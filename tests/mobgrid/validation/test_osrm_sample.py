from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from mobgrid.graph.csr import csr_from_indexed_edges, save_graph
from mobgrid.validation.osrm import load_query_settings
from mobgrid.validation.osrm_sample import (
    SampleSettings,
    classify_origins,
    generate_sample,
    interior_mask,
    sample_mode,
)
from shapely import LineString, Point, box, to_wkb


def test_pilot_sampling_configuration_has_requested_sizes_and_bands():
    settings = load_query_settings(
        Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
    )
    sample = settings.sampling
    assert sample is not None
    assert sample.count_by_mode == {"car": 1500, "bike": 500, "foot": 500}
    assert sample.band_edges_m == [0, 2000, 5000, 10000, 20000, 40000, 80000]
    assert sample.bike_max_m == 20000
    assert sample.boundary_margin_m == 10000
    assert sample.context_radius_m == 500


def test_origin_context_nearest_geometry_ties_and_rural_fallback():
    points = np.array([Point(1, 5), Point(0, 5), Point(1000, 5)], dtype=object)
    edges = np.array(
        [LineString([(0, 0), (0, 10)]), LineString([(2, 0), (2, 10)])],
        dtype=object,
    )
    contexts, methods = classify_origins(
        points,
        edges,
        np.array(["z", "a"]),
        np.array([True, False]),
        np.array([True, False]),
        max_distance_m=500,
    )
    assert contexts.tolist() == ["rural", "urban", "rural"]
    assert methods.tolist() == ["density", "tagged", "beyond"]


def test_foot_sample_obeys_cutoff_and_is_reproducible():
    node_ids = np.arange(6, dtype=np.int64)
    source = np.repeat(node_ids, len(node_ids))
    target = np.tile(node_ids, len(node_ids))
    keep = source != target
    source, target = source[keep], target[keep]
    weights = np.where(np.abs(source - target) == 1, 10, 100).astype(np.float32)
    graph = csr_from_indexed_edges(
        "foot",
        node_ids,
        source,
        target,
        {"time_s": weights},
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    xy = np.column_stack((node_ids * 1000, np.zeros(len(node_ids))))
    contexts = np.array(["urban", "urban", "urban", "rural", "rural", "rural"])
    kwargs = dict(
        graph=graph,
        coordinates=xy,
        contexts=contexts,
        methods=np.array(["tagged"] * len(node_ids)),
        inside=np.ones(len(node_ids), dtype=bool),
        bands_m=[(0, 1500), (1500, 3000)],
        count=8,
        cutoff_s=10,
        resolution_s=1,
        long_car_min_m=20_000,
        attempts_per_stratum=100,
    )
    first, unavailable = sample_mode(**kwargs, rng=np.random.default_rng(42))
    second, _ = sample_mode(**kwargs, rng=np.random.default_rng(42))
    assert first == second
    assert len(first) == 8
    assert all(
        abs(row["origin_index"] - row["destination_index"]) == 1 for row in first
    )
    assert set(unavailable) == {(1500, 3000, "urban"), (1500, 3000, "rural")}


def test_long_car_pairs_keep_both_endpoints_inside():
    ids = np.arange(4, dtype=np.int64)
    graph = csr_from_indexed_edges(
        "car",
        ids,
        ids[:-1],
        ids[1:],
        {"time_s": np.ones(3, dtype=np.float32)},
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    rows, _ = sample_mode(
        graph=graph,
        coordinates=np.column_stack((ids * 21_000, np.zeros(4))),
        contexts=np.array(["urban", "rural", "urban", "rural"]),
        methods=np.array(["tagged"] * 4),
        inside=np.array([False, True, True, False]),
        bands_m=[(20_000, 40_000)],
        count=2,
        cutoff_s=100,
        resolution_s=1,
        long_car_min_m=20_000,
        attempts_per_stratum=50,
        rng=np.random.default_rng(42),
    )
    assert {(row["origin_index"], row["destination_index"]) for row in rows} == {
        (1, 2),
        (2, 1),
    }


def test_interior_mask_checks_exact_boundary_distance():
    area = box(0, 0, 100, 100)
    points = np.array([Point(10, 50), Point(9.9, 50), Point(50, 50)], dtype=object)
    assert interior_mask(area, points, 10).tolist() == [True, False, True]


def test_sample_pipeline_writes_wgs84_pairs_and_reuses_checkpoints(tmp_path):
    nodes = np.arange(6, dtype=np.int64)
    x = 4_000_000 + nodes * 1000
    y = np.full(6, 3_000_000)
    graph_directory = tmp_path / "graphs"
    graph_directory.mkdir()
    sources = np.repeat(nodes, len(nodes))
    targets = np.tile(nodes, len(nodes))
    keep = sources != targets
    for mode in ("car", "bike", "foot"):
        graph = csr_from_indexed_edges(
            mode,
            nodes,
            sources[keep],
            targets[keep],
            {"time_s": np.full(keep.sum(), 10, dtype=np.float32)},
            reference_mass_kg=74,
            bike_mass_kg=15,
        )
        save_graph(graph, graph_directory / f"{mode}.npz")
    pq.write_table(
        pa.table({"node_id": nodes, "x": x, "y": y}), tmp_path / "nodes.parquet"
    )
    geometries = [
        to_wkb(LineString([(int(xx), int(yy) - 100), (int(xx), int(yy) + 100)]))
        for xx, yy in zip(x, y, strict=True)
    ]
    keys = [f"edge-{i}" for i in nodes]
    pq.write_table(
        pa.table(
            {
                "edge_key": keys,
                "mode": ["car"] * 6,
                "speed_context": ["urban"] * 3 + ["rural"] * 3,
                "geometry_wkb": geometries,
            }
        ),
        tmp_path / "edges.parquet",
    )
    pq.write_table(
        pa.table({"edge_key": keys, "is_urban": [True] * 3 + [False] * 3}),
        tmp_path / "costs.parquet",
    )
    pq.write_table(
        pa.table(
            {"geometry_wkb": [to_wkb(box(3_990_000, 2_990_000, 4_020_000, 3_010_000))]}
        ),
        tmp_path / "area.parquet",
    )
    search_config = tmp_path / "search.yaml"
    search_config.write_text(
        "queue: dial\ndial_resolution_s: 1\ntime_bin_s: 60\n"
        "distance_bin_m: 250\nenergy_bin_kj: 10\nnearest_extra: 2\n"
        "benchmark_seed: 42\nbenchmark_log_directory: logs\n"
        "cutoff_s_by_mode: {car: 100, bike: 100, foot: 100}\n",
        encoding="utf-8",
    )
    settings = SampleSettings(
        graph_directory=graph_directory,
        edges_path=tmp_path / "edges.parquet",
        edge_costs_path=tmp_path / "costs.parquet",
        nodes_path=tmp_path / "nodes.parquet",
        area_path=tmp_path / "area.parquet",
        search_config=search_config,
        seed=42,
        count_by_mode={"car": 4, "bike": 4, "foot": 4},
        band_edges_m=[0, 1500, 3000],
        bike_max_m=3000,
        long_car_min_m=1500,
        boundary_margin_m=100,
        context_radius_m=500,
        attempts_per_stratum=100,
    )
    sample_path = tmp_path / "pairs.parquet"
    generate_sample(settings, sample_path, tmp_path / "logs", "2026-01-01")
    pairs = pq.read_table(sample_path).to_pylist()
    assert len(pairs) == 12
    assert {row["mode"] for row in pairs} == {"car", "bike", "foot"}
    assert len({row["pair_id"] for row in pairs}) == 12
    assert all(-180 < row["origin_lon"] < 180 for row in pairs)
    assert all(row["context_method"] == "tagged" for row in pairs)
    checkpoints = sorted(tmp_path.glob("sample_*.json"))
    assert len(checkpoints) == 3
    before = [path.stat().st_mtime_ns for path in checkpoints]
    generate_sample(settings, sample_path, tmp_path / "logs", "2026-01-01")
    assert [path.stat().st_mtime_ns for path in checkpoints] == before
    assert pq.read_table(sample_path).to_pylist() == pairs
