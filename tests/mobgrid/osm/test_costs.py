"""Integration tests for the resumable section 8.1 cost stage."""

import json
from pathlib import Path
from shutil import copyfile

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from mobgrid.osm.config import load_network_config
from mobgrid.osm.edges import build_directed_edges

ROOT = Path(__file__).resolve().parents[3]


def test_cost_stage_recomputes_after_speed_change_without_rebuilding_edges(
    tmp_path, monkeypatch, capsys
):
    import mobgrid.osm.costs as costs
    import mobgrid.osm.elevation as elevation

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    for name in ("pilot.yaml", "network.yaml", "energy.yaml"):
        copyfile(ROOT / "config" / name, config_dir / name)
    interim = tmp_path / "data" / "interim" / "osm" / "2021" / "pilot"
    interim.mkdir(parents=True)
    base = tmp_path / "data" / "base" / "network" / "2021" / "pilot"
    grid_dir = tmp_path / "data" / "interim" / "bdalti"
    grid_dir.mkdir(parents=True)
    (grid_dir / "synthetic.asc").write_text("synthetic", encoding="ascii")
    connection = duckdb.connect()
    connection.execute(
        """
        COPY (SELECT 1::BIGINT AS way_id,
                     map {'highway': 'residential', 'zone:traffic': 'FR:urban'}
                         AS tags, [1, 2]::BIGINT[] AS refs)
        TO ? (FORMAT PARQUET)
    """,
        [str(interim / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (SELECT i::BIGINT AS node_id, map()::MAP(VARCHAR, VARCHAR) AS tags,
                     44.0 AS lat, 0.01 + i * 0.001 AS lon
              FROM range(1, 3) t(i))
        TO ? (FORMAT PARQUET)
    """,
        [str(interim / "nodes.parquet")],
    )
    network_path = config_dir / "network.yaml"
    energy_path = config_dir / "energy.yaml"
    network = load_network_config(network_path)
    build_directed_edges(
        connection,
        interim / "ways.parquet",
        interim / "nodes.parquet",
        base,
        config=network,
    )
    monkeypatch.setattr(
        elevation, "sample_elevations", lambda paths, x, y: np.zeros(len(x))
    )
    monkeypatch.setattr(elevation, "nodes_without_tile", lambda paths, x, y: 0)
    report = tmp_path / "step06.md"
    report.write_text("# Step 6\n", encoding="utf-8")
    args = [
        "--state",
        "2021",
        "--pilot-config",
        str(config_dir / "pilot.yaml"),
        "--network-config",
        str(network_path),
        "--energy-config",
        str(energy_path),
        "--report",
        str(report),
    ]
    assert costs.main(args) == 0
    elevation_report = tmp_path / "docs" / "data" / "step06_elevation_pilot.md"
    assert elevation_report.is_file()
    assert not elevation_report.with_name("step06_elevation_pilot_2021.md").exists()
    edges = base / "edges.parquet"
    output = base / "edge_costs.parquet"
    original_edges = edges.read_bytes()
    edge_mtime = edges.stat().st_mtime_ns
    before = pq.read_table(output)
    assert before.num_rows == pq.read_table(edges).num_rows
    assert len(set(before.column("edge_key").to_pylist())) == before.num_rows
    assert before.schema.field("walk_time_s").type == pa.float32()
    assert before.schema.field("length_m").type == pa.float32()
    assert "null elevation" in report.read_text(encoding="utf-8").lower()
    assert "urban" in report.read_text(encoding="utf-8").lower()
    assert "completed in" in capsys.readouterr().err

    old_report = elevation_report.with_name("step06_elevation_pilot_2021.md")
    copyfile(elevation_report, old_report)
    checkpoint = interim / "elevation" / "completed.json"
    previous = json.loads(checkpoint.read_text(encoding="utf-8"))
    previous["report"] = elevation._file_signature(old_report)
    checkpoint.write_text(json.dumps(previous), encoding="utf-8")
    with monkeypatch.context() as patch:
        def unexpected_elevation(*args, **kwargs):
            raise AssertionError("matching elevation checkpoint was not reused")

        patch.setattr(elevation, "enrich_edges_with_elevation", unexpected_elevation)
        assert costs.main(args) == 0
    assert json.loads(checkpoint.read_text(encoding="utf-8"))["report"] == (
        elevation._file_signature(elevation_report)
    )

    with monkeypatch.context() as patch:
        def unexpected_join(*args, **kwargs):
            raise AssertionError("completed output was recomputed")

        patch.setattr(costs, "_write_costs", unexpected_join)
        assert costs.main(args) == 0

    output.unlink()
    with monkeypatch.context() as patch:

        def unexpected(*args, **kwargs):
            raise AssertionError("completed cost substage was recomputed")

        patch.setattr(costs.speeds, "build_car_costs", unexpected)
        patch.setattr(costs, "enrich_active_edge_costs", unexpected)
        assert costs.main(args) == 0

    config = yaml.safe_load(energy_path.read_text(encoding="utf-8"))
    config["walking"]["v0_kmh"] *= 2
    energy_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    assert costs.main(args) == 0
    after = pq.read_table(output)
    before_walk = next(row for row in before.to_pylist() if row["walk_time_s"])
    after_walk = next(row for row in after.to_pylist() if row["walk_time_s"])
    assert after_walk["walk_time_s"] == pytest.approx(
        before_walk["walk_time_s"] / 2, rel=1e-6
    )
    assert edges.stat().st_mtime_ns == edge_mtime
    assert edges.read_bytes() == original_edges
    before_car = next(row for row in after.to_pylist() if row["car_time_s"])
    network_data = yaml.safe_load(network_path.read_text(encoding="utf-8"))
    network_data["car_speed"]["defaults_kmh_by_context"]["urban"] = 40
    network_path.write_text(yaml.safe_dump(network_data), encoding="utf-8")
    assert costs.main(args) == 0
    after_car = next(
        row for row in pq.read_table(output).to_pylist() if row["car_time_s"]
    )
    assert after_car["car_time_s"] == pytest.approx(
        before_car["car_time_s"] * 1.25, rel=1e-6
    )
    build_directed_edges(
        connection,
        interim / "ways.parquet",
        interim / "nodes.parquet",
        base,
        config=load_network_config(network_path),
    )
    assert edges.stat().st_mtime_ns == edge_mtime
    assert report.read_text(encoding="utf-8").count("## Edge costs") == 1
    build_directed_edges(
        connection,
        interim / "ways.parquet",
        interim / "nodes.parquet",
        base,
        config=load_network_config(network_path),
        force=True,
    )
    assert edges.stat().st_mtime_ns != edge_mtime
    import mobgrid.osm.edges as edge_module

    def fail_write(*args, **kwargs):
        raise RuntimeError("interrupted rebuild")

    with monkeypatch.context() as patch:
        patch.setattr(edge_module, "_write_parquet_atomic", fail_write)
        with pytest.raises(RuntimeError, match="interrupted rebuild"):
            build_directed_edges(
                connection,
                interim / "ways.parquet",
                interim / "nodes.parquet",
                base,
                config=load_network_config(network_path),
                force=True,
            )
    assert not (base / "_edges.json").exists()
    connection.close()


@pytest.mark.parametrize(
    ("car_keys", "active_keys"),
    [
        ([], ["walk"]),
        (["car", "extra"], ["walk"]),
        (["car"], ["walk", "extra"]),
        (["car", "car"], ["walk"]),
        (["walk"], ["car"]),
    ],
)
def test_cost_join_rejects_missing_extra_and_duplicate_keys(
    tmp_path, car_keys, active_keys
):
    from mobgrid.osm.costs import _write_costs

    edges = tmp_path / "edges.parquet"
    car = tmp_path / "car.parquet"
    active = tmp_path / "active.parquet"
    pq.write_table(
        pa.table({"edge_key": ["car", "walk"], "mode": ["car", "foot"]}), edges
    )
    pq.write_table(pa.table({"edge_key": pa.array(car_keys, type=pa.string())}), car)
    pq.write_table(
        pa.table({"edge_key": pa.array(active_keys, type=pa.string())}), active
    )
    connection = duckdb.connect()
    try:
        with pytest.raises(ValueError, match="edge|cost"):
            _write_costs(connection, edges, car, active, tmp_path / "out.parquet")
    finally:
        connection.close()


def test_cost_report_speeds_and_urban_share(tmp_path):
    from mobgrid.osm.costs import _write_report

    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "costs.parquet"
    report = tmp_path / "report.md"
    pq.write_table(
        pa.table(
            {
                "edge_key": ["a", "b", "c", "d"],
                "mode": ["car", "car", "foot", "bike"],
                "highway": ["residential"] * 4,
                "length_m": [100.0, 300.0, 100.0, 100.0],
                "climb_m": [0.0, 0.0, None, 0.0],
            }
        ),
        edges,
    )
    pq.write_table(
        pa.table(
            {
                "edge_key": ["a", "b", "c", "d"],
                "car_time_s": [10.0, 30.0, None, None],
                "walk_time_s": [None, None, None, None],
                "bike_time_s": [None, None, None, 20.0],
                "bike_zero_speed_segments": [None, None, None, 2],
                "is_urban": [True, False, None, None],
            }
        ),
        costs,
    )
    report.write_text("# Step 6\n\n## Other\n\nKept.\n", encoding="utf-8")
    connection = duckdb.connect()
    try:
        _write_report(connection, edges, costs, report)
        _write_report(connection, edges, costs, report)
    finally:
        connection.close()
    text = report.read_text(encoding="utf-8")
    assert "null elevation profiles: 1 of 4" in text
    assert "zero-speed bike segments: 2" in text.lower()
    assert "| residential | 36.00 | n/a | 18.00 | 25.0% |" in text
    assert text.count("## Edge costs") == 1
    assert "## Other\n\nKept." in text
