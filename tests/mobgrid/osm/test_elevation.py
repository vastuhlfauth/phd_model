from pathlib import Path
from shutil import copyfile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.energy.rates import load_energy_config
from mobgrid.osm.active_costs import enrich_active_edge_costs
from mobgrid.osm.config import load_network_config
from mobgrid.osm.elevation import (
    ElevationSummary,
    edge_elevation_profile,
    enrich_edges_with_elevation,
    sample_elevations,
    smooth_elevation_profile,
    write_elevation_report,
)

ENERGY = load_energy_config("config/energy.yaml")
NETWORK = load_network_config("config/network.yaml")


def _monaco_elevation_run(tmp_path, monkeypatch, elevation_module):
    import duckdb

    fixtures = Path(__file__).parents[2] / "fixtures"
    edges = tmp_path / "edges.parquet"
    nodes = tmp_path / "nodes.parquet"
    ways = fixtures / "osm_monaco_ways.parquet"
    grid = tmp_path / "synthetic.asc"
    grid.write_text("synthetic", encoding="ascii")
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    copyfile(fixtures / "osm_monaco_baseline.parquet", edges)
    connection.execute("""
        CREATE TEMP TABLE test_nodes AS
            WITH endpoints AS (
                SELECT from_node_id AS node_id FROM read_parquet(?)
                UNION SELECT to_node_id AS node_id FROM read_parquet(?)
            ), projected AS (
                SELECT n.node_id, n.tags, n.lat, n.lon,
                       ST_Transform(ST_Point(n.lon, n.lat),
                                    'EPSG:4326', 'EPSG:3035', true) AS point,
                       e.node_id IS NOT NULL AS graph_node
                FROM read_parquet(?) n LEFT JOIN endpoints e USING (node_id)
            )
            SELECT node_id, tags, lat, lon, ST_X(point) AS x, ST_Y(point) AS y,
                   graph_node FROM projected
    """, [str(edges), str(edges), str(fixtures / "osm_monaco_nodes.parquet")])
    connection.execute("COPY test_nodes TO ? (FORMAT PARQUET)", [str(nodes)])
    monkeypatch.setattr(
        elevation_module, "sample_elevations",
        lambda paths, x, y: 30 + 40 * np.sin(x / 200) + 20 * np.cos(y / 150),
    )
    monkeypatch.setattr(
        elevation_module, "nodes_without_tile", lambda paths, x, y: 0
    )
    summary = elevation_module.enrich_edges_with_elevation(
        connection, edges, nodes, [grid], ways_path=ways,
        way_elevations_path=tmp_path / "way_elevations.parquet",
        network=NETWORK, energy=ENERGY,
    )
    connection.close()
    return edges, summary


def test_monaco_profiles_match_directed_baseline(tmp_path, monkeypatch):
    import mobgrid.osm.elevation as elevation

    fixtures = Path(__file__).parents[2] / "fixtures"
    edges, summary = _monaco_elevation_run(tmp_path, monkeypatch, elevation)
    columns = [
        "edge_key", "node_elevations_m", "elevation_from_m", "elevation_to_m",
        "climb_m", "descent_m", "mean_grade",
    ]
    actual = sorted(
        pq.read_table(edges, columns=columns).to_pylist(),
        key=lambda row: row["edge_key"],
    )
    expected = sorted(
        pq.read_table(fixtures / "osm_monaco_elevation_baseline.parquet").to_pylist(),
        key=lambda row: row["edge_key"],
    )
    assert len(actual) == len(expected)
    for result, baseline in zip(actual, expected, strict=True):
        assert result["edge_key"] == baseline["edge_key"]
        for column in columns[1:]:
            if baseline[column] is None:
                assert result[column] is None
            else:
                tolerance = 1e-9 if column == "mean_grade" else 0.001
                assert result[column] == pytest.approx(
                    baseline[column], abs=tolerance, rel=0
                )
    expected_clips = pq.read_table(
        fixtures / "osm_monaco_elevation_clipped_baseline.parquet"
    ).to_pylist()
    assert {
        (row["mode"], row["highway"]): row["count"] for row in expected_clips
    } == {
        key: value[0] for key, value in summary.clipped_segments_by_class.items()
    }


def _grid(path, x_corner, rows, y_corner=0):
    path.write_text(
        f"ncols {len(rows[0])}\nnrows {len(rows)}\n"
        f"xllcorner {x_corner}\nyllcorner {y_corner}\ncellsize 25\n"
        "NODATA_value -9999\n"
        + "\n".join(" ".join(str(value) for value in row) for row in rows)
        + "\n",
        encoding="ascii",
    )


def test_bilinear_interpolation_across_tiles_and_nodata(tmp_path):
    west = tmp_path / "west.asc"
    east = tmp_path / "east.asc"
    _grid(west, 0, [[10, 20], [0, 10]])
    _grid(east, 50, [[30, -9999], [20, 30]])

    elevations = sample_elevations(
        [west, east],
        np.array([25.0, 50.0, 62.5, 75.0, -100.0]),
        np.array([25.0, 25.0, 37.5, 37.5, 25.0]),
    )
    assert elevations[:3] == pytest.approx([10.0, 20.0, 30.0])
    assert np.isnan(elevations[3:]).all()


def test_directional_elevation_profile_and_missing_nodes():
    forward = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([10.0, 15.0, 12.0])
    )
    reverse = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([12.0, 15.0, 10.0])
    )
    assert forward.climb_m == pytest.approx(5.0)
    assert forward.descent_m == pytest.approx(3.0)
    assert reverse.climb_m == pytest.approx(forward.descent_m)
    assert reverse.descent_m == pytest.approx(forward.climb_m)
    assert forward.mean_grade == pytest.approx(0.01)
    assert reverse.mean_grade == pytest.approx(-0.01)
    missing = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([10.0, np.nan, 12.0])
    )
    assert missing.climb_m is None
    assert missing.mean_grade is None


def test_distance_weighted_smoothing_preserves_slopes_and_reduces_zigzag():
    distances = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])
    slope = distances * 0.1 + 10
    zigzag = np.array([0.0, 2.0, 0.0, 2.0, 0.0, 2.0])
    smoothed_slope = smooth_elevation_profile(distances, slope, 50.0)
    smoothed_zigzag = smooth_elevation_profile(distances, zigzag, 50.0)
    assert smoothed_slope == pytest.approx(slope)
    assert np.maximum(np.diff(smoothed_zigzag), 0).sum() < (
        np.maximum(np.diff(zigzag), 0).sum()
    )


def test_smoothing_weights_by_distance_not_node_density():
    sparse_distances = np.array([0.0, 20.0, 40.0])
    sparse_heights = np.array([0.0, 10.0, 0.0])
    dense_distances = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 40.0])
    dense_heights = np.array([0.0, 2.5, 5.0, 7.5, 10.0, 0.0])
    sparse = smooth_elevation_profile(sparse_distances, sparse_heights, 20.0)
    dense = smooth_elevation_profile(dense_distances, dense_heights, 20.0)
    assert dense[[0, 4, 5]] == pytest.approx(sparse)


def test_smoothing_does_not_fill_missing_elevations():
    distances = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    heights = np.array([0.0, 1.0, np.nan, 3.0, 4.0])
    actual = smooth_elevation_profile(distances, heights, 50.0)
    assert np.isnan(actual[2])
    assert actual[[0, 1, 3, 4]] == pytest.approx([0.0, 1.0, 3.0, 4.0])


def test_elevation_sampling_checkpoint_reuses_and_invalidates(tmp_path, monkeypatch):
    import mobgrid.osm.elevation as elevation

    nodes = tmp_path / "nodes.parquet"
    grid = tmp_path / "tile.asc"
    nodes.write_bytes(b"nodes")
    grid.write_bytes(b"raster")
    calls = []

    def sample(paths, x, y):
        calls.append(tuple(paths))
        return np.array([10.0, 20.0])

    monkeypatch.setattr(elevation, "sample_elevations", sample)
    monkeypatch.setattr(elevation, "nodes_without_tile", lambda paths, x, y: 1)
    args = (
        nodes, [grid], np.array([1, 2]), np.array([0.0, 1.0]),
        np.array([0.0, 1.0]), tmp_path / "cache",
    )
    first, uncovered = elevation._sample_nodes_with_checkpoint(*args)
    second, second_uncovered = elevation._sample_nodes_with_checkpoint(*args)
    assert first == pytest.approx([10, 20])
    assert second == pytest.approx(first)
    assert (uncovered, second_uncovered, len(calls)) == (1, 1, 1)
    grid.write_bytes(b"changed raster")
    elevation._sample_nodes_with_checkpoint(*args)
    assert len(calls) == 2


def test_elevation_command_resumes_completed_outputs(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    import mobgrid.osm.elevation as elevation

    pilot_config = tmp_path / "config" / "pilot.yaml"
    pilot_config.parent.mkdir()
    pilot_config.write_text("test", encoding="utf-8")
    network_dir = tmp_path / "data" / "base" / "network" / "2021" / "pilot"
    cache_dir = tmp_path / "data" / "interim" / "osm" / "2021" / "pilot"
    raster_dir = tmp_path / "data" / "interim" / "bdalti"
    for folder in (network_dir, cache_dir, raster_dir):
        folder.mkdir(parents=True)
    for path in (
        network_dir / "edges.parquet", network_dir / "nodes.parquet",
        cache_dir / "ways.parquet", raster_dir / "tile.asc",
    ):
        path.write_bytes(b"synthetic")
    pilot = SimpleNamespace(paths={"base": "data/base", "interim": "data/interim"})
    monkeypatch.setattr(elevation, "load_pilot_config", lambda path: pilot)
    monkeypatch.setattr(elevation, "load_network_config", lambda path: NETWORK)
    monkeypatch.setattr(elevation, "load_energy_config", lambda path: ENERGY)
    monkeypatch.setattr(elevation, "open_connection", lambda: SimpleNamespace(
        close=lambda: None
    ))
    calls = []

    def enrich(connection, edges, nodes, grids, **kwargs):
        calls.append(1)
        kwargs["way_elevations_path"].write_bytes(b"profiles")
        return ElevationSummary(1, 0, 0, 0)

    monkeypatch.setattr(elevation, "enrich_edges_with_elevation", enrich)
    args = [
        "--state", "2021", "--area", "pilot",
        "--pilot-config", str(pilot_config),
        "--report", str(tmp_path / "report.md"),
        "--log", str(tmp_path / "run.log"),
        "--summary", str(tmp_path / "summary.md"),
    ]
    assert elevation.main(args) == 0
    assert "wrote elevation summary" in capsys.readouterr().err
    assert elevation.main(args) == 0
    assert len(calls) == 1
    assert "reused" in (tmp_path / "summary.md").read_text(encoding="utf-8").lower()
    (raster_dir / "tile.asc").write_bytes(b"changed")
    assert elevation.main(args) == 0
    assert len(calls) == 2
    assert (tmp_path / "run.log").is_file()


def test_unaligned_grids_are_rejected(tmp_path):
    west = tmp_path / "west.asc"
    east = tmp_path / "east.asc"
    _grid(west, 0, [[10, 20], [0, 10]])
    _grid(east, 51, [[30, 40], [20, 30]])
    with pytest.raises(ValueError, match="unaligned ASCII grid"):
        sample_elevations([west, east], np.array([25.0]), np.array([25.0]))


def test_edge_elevation_profiles_keep_direction_and_report_uncovered_nodes(
    tmp_path, monkeypatch, caplog,
):
    import duckdb
    import mobgrid.osm.elevation as elevation

    caplog.set_level("INFO", logger=elevation.__name__)
    grid = tmp_path / "tile.asc"
    _grid(grid, 700000, [[10, 15, 12], [10, 15, 12]], y_corner=6600000)
    edges = tmp_path / "edges.parquet"
    nodes = tmp_path / "nodes.parquet"
    ways = tmp_path / "ways.parquet"
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    connection.register(
        "_test_lambert93",
        pa.table(
            {
                "x": [700012.5, 700037.5, 700062.5, 701000.0],
                "y": [6600012.5] * 4,
            }
        ),
    )
    coordinates = connection.execute("""
        SELECT ST_X(ST_Transform(
                   ST_Point(x, y), 'EPSG:2154', 'EPSG:3035', true
               )) AS x,
               ST_Y(ST_Transform(
                   ST_Point(x, y), 'EPSG:2154', 'EPSG:3035', true
               )) AS y
        FROM _test_lambert93
    """).fetchall()
    pq.write_table(
        pa.table(
            {
                "edge_key": ["10:0:foot:f", "10:0:foot:r", "11:0:foot:f"],
                "way_id": [10, 10, 11],
                "mode": ["foot", "foot", "bike"],
                "highway": ["residential"] * 3,
                "is_forward": [True, False, True],
                "node_ids": pa.array(
                    [[1, 2, 3], [3, 2, 1], [3, 4]],
                    type=pa.list_(pa.int64()),
                ),
                "length_m": [50.0, 50.0, 25.0],
            }
        ),
        edges,
    )
    pq.write_table(
        pa.table(
            {
                "node_id": [1, 2, 3, 4],
                "x": [row[0] for row in coordinates],
                "y": [row[1] for row in coordinates],
                "graph_node": [True, False, True, True],
            }
        ),
        nodes,
    )
    pq.write_table(pa.table({
        "way_id": [10, 11],
        "refs": [[1, 2, 3], [3, 4]],
        "tags": pa.array([{}, {}], type=pa.map_(pa.string(), pa.string())),
    }), ways)

    try:
        summary = enrich_edges_with_elevation(
            connection, edges, nodes, [grid], ways_path=ways,
            way_elevations_path=tmp_path / "way_elevations.parquet",
            network=NETWORK.model_copy(
                update={"elevation_smoothing_window_m": 0.00001}
            ),
            energy=ENERGY,
            cache_directory=tmp_path / "cache",
        )
        segment_count = connection.execute(
            "SELECT count(*) FROM _osm_segment_elevation_profiles"
        ).fetchone()[0]
        assert segment_count == 2
        assert "elevation profiles completed in" in caplog.text
        def unexpected_resample(*args):
            pytest.fail("completed node sampling should be reused")

        monkeypatch.setattr(elevation, "sample_elevations", unexpected_resample)
        repeated = enrich_edges_with_elevation(
            connection, edges, nodes, [grid], ways_path=ways,
            way_elevations_path=tmp_path / "way_elevations.parquet",
            network=NETWORK.model_copy(
                update={"elevation_smoothing_window_m": 0.00001}
            ),
            energy=ENERGY,
            cache_directory=tmp_path / "cache",
        )
        assert repeated == summary
        profiles = {
            row[0]: row[1:]
            for row in connection.execute(
                f"SELECT edge_key, climb_m, descent_m, mean_grade "
                f"FROM read_parquet('{edges.as_posix()}')"
            ).fetchall()
        }
        node_elevations = connection.execute(
            f"SELECT node_id, elevation_m FROM read_parquet('{nodes.as_posix()}') "
            "ORDER BY node_id"
        ).fetchall()
    finally:
        connection.close()

    assert profiles["10:0:foot:f"][:2] == pytest.approx((5.0, 3.0))
    assert profiles["10:0:foot:f"][2] == pytest.approx(0.04, abs=1e-4)
    assert profiles["10:0:foot:r"][:2] == pytest.approx((3.0, 5.0))
    assert profiles["10:0:foot:r"][2] == pytest.approx(-0.04, abs=1e-4)
    assert profiles["11:0:foot:f"] == (None, None, None)
    assert summary.nodes_without_elevation == 1
    assert summary.nodes_without_tile == 1
    assert [row[1] for row in node_elevations[:3]] == pytest.approx(
        [10.0, 15.0, 12.0]
    )
    assert node_elevations[3][1] is None


def test_elevation_report_distinguishes_uncovered_nodes_from_missing_samples(
    tmp_path,
):
    report = tmp_path / "elevation.md"

    write_elevation_report(
        ElevationSummary(
            3, 2, 1, 1,
            climb_by_mode={"bike": (100.0, 60.0), "car": (200.0, 120.0),
                           "foot": (300.0, 180.0)},
            incomplete_by_mode={"bike": 1, "car": 0, "foot": 0},
        ),
        report,
        state=2021,
        area="pilot",
        tile_count=2,
    )

    contents = report.read_text(encoding="utf-8")
    assert "Nodes with no covering tile: 1" in contents
    assert "Nodes with no valid elevation sample: 2" in contents
    assert "bike: 100.0 / 60.0; incomplete: 1" in contents
    assert "car: 200.0 / 120.0; incomplete: 0" in contents
    assert "foot: 300.0 / 180.0; incomplete: 0" in contents


@pytest.mark.parametrize("structure", ["bridge", "tunnel"])
def test_structure_profile_interpolates_between_portals_per_way(
    tmp_path, structure, monkeypatch
):
    import duckdb
    import mobgrid.osm.elevation as elevation

    monkeypatch.setattr(elevation, "_WAY_BATCH_SIZE", 2)

    grid = tmp_path / "tile.asc"
    _grid(grid, 700000, [[10, -20, 12], [10, -20, 12]], y_corner=6600000)
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    coordinates = connection.execute("""
        SELECT ST_X(p), ST_Y(p)
        FROM (
            SELECT ST_Transform(
                ST_Point(x, 6600012.5), 'EPSG:2154', 'EPSG:3035', true
            ) AS p
            FROM unnest([700012.5, 700037.5, 700062.5]) AS points(x)
        )
    """).fetchall()
    nodes = tmp_path / "nodes.parquet"
    ways = tmp_path / "ways.parquet"
    edges = tmp_path / "edges.parquet"
    profiles = tmp_path / "way_elevations.parquet"
    pq.write_table(pa.table({
        "node_id": [1, 2, 3],
        "x": [point[0] for point in coordinates],
        "y": [point[1] for point in coordinates],
        "graph_node": [True, True, True],
        "tags": pa.array([{}, {}, {}], type=pa.map_(pa.string(), pa.string())),
    }), nodes)
    pq.write_table(pa.table({
        "way_id": [10, 11],
        "refs": [[1, 2, 3], [1, 2, 3]],
        "tags": pa.array(
            [{structure: "yes"}, {structure: "no"}],
            type=pa.map_(pa.string(), pa.string()),
        ),
    }), ways)
    pq.write_table(pa.table({
        "edge_key": [
            "10:0:foot:f", "10:0:foot:r", "10:1:foot:f",
            "11:0:car:r", "11:0:bike:r", "11:0:foot:r",
        ],
        "way_id": [10, 10, 10, 11, 11, 11],
        "mode": ["foot", "foot", "foot", "car", "bike", "foot"],
        "highway": ["residential"] * 6,
        "is_forward": [True, False, True, False, False, False],
        "node_ids": [[1, 2], [2, 1], [2, 3], [2, 1], [2, 1], [2, 1]],
        "length_m": [25.0] * 6,
        "bike_infra": [None, None, None, None, "mixed_traffic", None],
        "surface": pa.array([None] * 6, type=pa.string()),
        "tracktype": pa.array([None] * 6, type=pa.string()),
        "signal_count": [0] * 6,
        "stop_count": [0] * 6,
        "give_way_count": [0] * 6,
        "crossing_count": [0] * 6,
        "to_degree": [2] * 6,
        "to_node_id": [2, 1, 3, 1, 1, 1],
    }), edges)
    try:
        summary = enrich_edges_with_elevation(
            connection, edges, nodes, [grid], ways_path=ways,
            way_elevations_path=profiles,
            network=NETWORK,
            energy=ENERGY,
        )
        values = connection.execute(
            "SELECT way_id, node_id, elevation_m, raw_elevation_m "
            "FROM read_parquet(?) "
            "ORDER BY way_id, node_sequence", [str(profiles)]
        ).fetchall()
        edge_profiles = connection.execute(
            "SELECT edge_key, node_elevations_m FROM read_parquet(?) "
            "ORDER BY edge_key", [str(edges)]
        ).fetchall()
        active_summary = enrich_active_edge_costs(
            connection, edges, nodes, tmp_path / "costs.parquet",
            energy=ENERGY, network=NETWORK,
        )
    finally:
        connection.close()

    assert [row[2] for row in values[:3]] == pytest.approx([10, 11, 12], abs=1e-3)
    assert values[4][3] == pytest.approx(-20, abs=1e-3)
    assert edge_profiles[0][1] == pytest.approx([10, 11], abs=1e-3)
    assert edge_profiles[1][1] == pytest.approx([11, 10], abs=1e-3)
    assert edge_profiles[3][1] == pytest.approx([values[4][2], values[3][2]])
    assert summary.climb_by_mode["car"][0] == pytest.approx(30, abs=1e-3)
    assert summary.climb_by_mode["bike"] == pytest.approx(summary.climb_by_mode["car"])
    assert summary.climb_by_mode["car"][1] < summary.climb_by_mode["car"][0]
    assert summary.clipped_segments_by_class[("bike", "residential")][0] == 1
    assert summary.clipped_segments_by_class[("foot", "residential")][0] == 1
    for key, counts in summary.clipped_segments_by_class.items():
        assert counts == pytest.approx(active_summary.clipped_segments_by_class[key])
    assert [row[0] for row in summary.longest_clipped_edges] == [
        row[0] for row in active_summary.longest_clipped_edges
    ]
    report = tmp_path / "report.md"
    write_elevation_report(summary, report, state=2021, area="pilot", tile_count=1)
    contents = report.read_text(encoding="utf-8")
    assert "11:0:bike:r" in contents
    assert "| 11 | bike | residential |" in contents
    assert getattr(summary, f"{structure}_length_m") == pytest.approx(50, abs=0.1)
    other = "tunnel" if structure == "bridge" else "bridge"
    assert getattr(summary, f"{other}_length_m") == 0
