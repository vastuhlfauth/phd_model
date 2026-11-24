from types import SimpleNamespace

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from mobgrid.graph.build import build_graphs, main, write_graph_report
from mobgrid.graph.csr import load_graph


def _pilot_inputs(tmp_path):
    edges = []
    costs = []
    edge_number = 0
    for mode in ("car", "bike", "foot"):
        for source, target in ((1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3)):
            edge_number += 1
            edge_key = f"{mode}-{edge_number}"
            edges.append(
                {
                    "edge_key": edge_key,
                    "mode": mode,
                    "from_node_id": source,
                    "to_node_id": target,
                    "way_id": 1,
                    "highway": "residential",
                    "length_m": 10.0,
                    "climb_m": 1.0,
                }
            )
            costs.append(
                {
                    "edge_key": edge_key,
                    "length_m": 10.0,
                    "car_time_s": 1.0,
                    "walk_time_s": 2.0,
                    "walk_energy_kj": 3.0,
                    "bike_time_s": 1.5,
                    "bike_energy_kj": 1.39,
                    "bike_energy_per_kg_kj_per_kg": 0.01,
                    "bike_energy_drag_kj": 0.2,
                    "bike_pedalling_energy_kj": 0.3,
                    "climb_m": 1.0,
                    "separated_length_m": 4.0,
                    "is_urban": True,
                    "speed_limit_bucket": "30-50",
                }
            )
    edges_path = tmp_path / "edges.parquet"
    costs_path = tmp_path / "edge_costs.parquet"
    nodes_path = tmp_path / "nodes.parquet"
    pq.write_table(pa.Table.from_pylist(edges), edges_path)
    pq.write_table(pa.Table.from_pylist(costs), costs_path)
    pq.write_table(
        pa.table(
            {
                "node_id": pa.array([1, 2, 3, 4], type=pa.int64()),
                "tags": pa.array(
                    [[], [], [("highway", "traffic_signals")], []],
                    type=pa.map_(pa.string(), pa.string()),
                ),
            }
        ),
        nodes_path,
    )
    return edges_path, costs_path, nodes_path


def test_build_graphs_saves_each_mode_and_kept_nodes(tmp_path):
    edges_path, costs_path, nodes_path = _pilot_inputs(tmp_path)
    output = tmp_path / "graph"
    with duckdb.connect() as connection:
        result = build_graphs(
            connection,
            edges_path,
            costs_path,
            nodes_path,
            output,
            reference_mass_kg=74.0,
            bike_mass_kg=15.0,
            car_energy_kj_per_s=0.1,
        )

    assert [summary.mode for summary in result.modes] == ["car", "bike", "foot"]
    for summary in result.modes:
        assert (output / f"{summary.mode}.npz").is_file()
        assert (summary.nodes_before_contraction, summary.edges_before_contraction) == (
            4,
            6,
        )
        assert (summary.nodes_after_contraction, summary.edges_after_contraction) == (
            3,
            4,
        )
        graph = load_graph(output / f"{summary.mode}.npz")
        np.testing.assert_array_equal(graph.node_ids, [1, 3, 4])
        assert graph.indices.dtype == np.int32
        assert graph.indptr.dtype == np.int64

    bike = load_graph(output / "bike.npz")
    np.testing.assert_allclose(bike.weights["time_s"], [3.0, 3.0, 1.5, 1.5])
    np.testing.assert_allclose(bike.weights["energy_kj"], [2.78, 2.78, 1.39, 1.39])
    assert bike.weights["separated_length_m"].sum() == 24.0
    np.testing.assert_allclose(
        bike.weights["bike_energy_per_kg_kj_per_kg"].sum(),
        0.06,
    )
    car = load_graph(output / "car.npz")
    assert car.weights["time_s:road_class:residential"].sum() == 6.0
    assert car.weights["time_s:speed_limit_bucket:30-50"].sum() == 6.0


def test_graph_report_replaces_previous_graph_section(tmp_path):
    edges_path, costs_path, nodes_path = _pilot_inputs(tmp_path)
    report = tmp_path / "step06_osm_pilot.md"
    report.write_text("# Pilot\n\n## Existing section\n\nKeep me.\n", encoding="utf-8")
    with duckdb.connect() as connection:
        result = build_graphs(
            connection,
            edges_path,
            costs_path,
            nodes_path,
            tmp_path / "graph",
            reference_mass_kg=74.0,
            bike_mass_kg=15.0,
            car_energy_kj_per_s=0.1,
        )

    write_graph_report(report, result, state=2021, area="pilot")
    write_graph_report(report, result, state=2021, area="pilot")

    text = report.read_text(encoding="utf-8")
    assert "Keep me." in text
    assert text.count("## Graph build") == 1
    assert "| car | 4 | 6 | 3 | 4 |" in text
    assert "Memory" in text
    assert "contraction" in text


def test_build_cli_uses_configured_base_and_updates_pilot_report(
    tmp_path,
    monkeypatch,
    capsys,
):
    root = tmp_path
    pilot_config = root / "config" / "pilot.yaml"
    energy_config = root / "config" / "energy.yaml"
    pilot_config.parent.mkdir()
    pilot_config.write_text("synthetic: true\n", encoding="utf-8")
    energy_config.write_text("synthetic: true\n", encoding="utf-8")
    pilot = SimpleNamespace(years=(2021,), paths={"base": "data/base"})
    energy = SimpleNamespace(
        reference_mass_kg=74.0,
        bike=SimpleNamespace(bike_mass_kg=15.0),
        rate_set="compendium",
        activity_rates={"driving_free_flow": SimpleNamespace(compendium_net_met=1.0)},
    )
    monkeypatch.setattr("mobgrid.graph.build.load_pilot_config", lambda _: pilot)
    monkeypatch.setattr("mobgrid.graph.build.load_energy_config", lambda _: energy)
    base = root / "data" / "base" / "network" / "2021" / "pilot"
    base.mkdir(parents=True)
    _pilot_inputs(base)
    report = root / "docs" / "data" / "step06_osm_pilot.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Synthetic pilot\n", encoding="utf-8")

    assert (
        main(
            [
                "--state",
                "2021",
                "--area",
                "pilot",
                "--pilot-config",
                str(pilot_config),
                "--energy-config",
                str(energy_config),
            ]
        )
        == 0
    )

    assert (base / "graph" / "car.npz").is_file()
    assert "## Graph build" in report.read_text(encoding="utf-8")
    assert "Wrote " in capsys.readouterr().out
