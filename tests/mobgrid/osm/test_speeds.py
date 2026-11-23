from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.osm.config import load_network_config
from mobgrid.osm.speeds import build_car_costs, write_car_speed_report

ROOT = Path(__file__).parents[3]


def _write_edges(path, records):
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    geometry = [
        connection.execute(
            "SELECT ST_AsWKB(ST_GeomFromText(?))", [record["wkt"]]
        ).fetchone()[0]
        for record in records
    ]
    connection.close()
    pq.write_table(
        pa.table(
            {
                "edge_key": [record["edge_key"] for record in records],
                "mode": ["car"] * len(records),
                "length_m": [record["length_m"] for record in records],
                "geometry_wkb": geometry,
                "highway": [record["highway"] for record in records],
                "service": pa.array(
                    [record.get("service") for record in records], type=pa.string()
                ),
                "oneway": pa.array(
                    [record.get("oneway") for record in records], type=pa.string()
                ),
                "maxspeed_kmh": [record["maxspeed_kmh"] for record in records],
                "speed_context": [record["speed_context"] for record in records],
                "signal_count": [record.get("signal_count", 0) for record in records],
                "stop_count": [record.get("stop_count", 0) for record in records],
                "give_way_count": [
                    record.get("give_way_count", 0) for record in records
                ],
                "crossing_count": [
                    record.get("crossing_count", 0) for record in records
                ],
                "mini_roundabout_count": [
                    record.get("mini_roundabout_count", 0) for record in records
                ],
                "to_degree": [record.get("to_degree", 2) for record in records],
            }
        ),
        path,
    )


def _record(
    edge_key,
    wkt,
    *,
    length_m=100.0,
    highway="residential",
    maxspeed_kmh=None,
    speed_context="urban",
    **counts,
):
    return {
        "edge_key": edge_key,
        "wkt": wkt,
        "length_m": length_m,
        "highway": highway,
        "maxspeed_kmh": maxspeed_kmh,
        "speed_context": speed_context,
        **counts,
    }


def _config():
    return load_network_config(ROOT / "config" / "network.yaml")


def test_class_context_default_is_used_only_when_maxspeed_is_null(tmp_path):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "car_costs.parquet"
    _write_edges(
        edges,
        [
            _record("default", "LINESTRING (0 0, 100 0)"),
            _record(
                "rural_default",
                "LINESTRING (20000 0, 20100 0)",
                highway="trunk",
                speed_context="rural",
            ),
            _record(
                "tagged",
                "LINESTRING (10000 0, 10100 0)",
                maxspeed_kmh=30.0,
                speed_context="rural",
            ),
        ],
    )
    connection = duckdb.connect()
    try:
        summary = build_car_costs(connection, edges, costs, config=_config())
        rows = {
            row[0]: row[1:]
            for row in connection.execute(
                f"SELECT edge_key, time_s, is_urban, road_class, "
                f"speed_limit_bucket FROM read_parquet('{costs.as_posix()}')"
            ).fetchall()
        }
    finally:
        connection.close()

    assert rows["default"][0] == pytest.approx(7.2)
    assert rows["default"][1] is True
    assert rows["default"][2] == "residential"
    assert rows["default"][3]
    assert rows["rural_default"][0] == pytest.approx(100 * 3.6 / 80)
    assert rows["rural_default"][2] == "trunk"
    assert rows["rural_default"][3]
    assert rows["tagged"][0] == pytest.approx(12.0)
    assert rows["tagged"][1] is False
    assert rows["tagged"][2] == "residential"
    assert rows["tagged"][3]
    assert dict(summary.urban_length_share_by_class)["trunk"] == 0


def test_each_control_adds_one_delay_and_junction_delay_is_smaller(tmp_path):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "car_costs.parquet"
    _write_edges(
        edges,
        [
            _record("none", "LINESTRING (0 0, 100 0)"),
            _record(
                "controls",
                "LINESTRING (10000 0, 10100 0)",
                signal_count=1,
                stop_count=1,
                give_way_count=1,
                crossing_count=1,
                mini_roundabout_count=1,
            ),
            _record(
                "junction",
                "LINESTRING (20000 0, 20100 0)",
                to_degree=3,
            ),
        ],
    )
    config = _config()
    connection = duckdb.connect()
    try:
        build_car_costs(connection, edges, costs, config=config)
        rows = dict(
            connection.execute(
                f"SELECT edge_key, time_s FROM read_parquet('{costs.as_posix()}')"
            ).fetchall()
        )
    finally:
        connection.close()

    base = 100 * 3.6 / 50
    assert rows["controls"] - rows["none"] == pytest.approx(
        15 + 5 + 2 + 3
    )
    assert rows["junction"] - rows["none"] == pytest.approx(
        config.car_speed.delays.at_to_node_s
    )
    assert rows["none"] == pytest.approx(base)


def test_default_caps_and_directional_dual_carriageway(tmp_path):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "car_costs.parquet"
    records = [
        _record("parking", "LINESTRING (0 0, 100 0)", highway="service",
                service="parking_aisle"),
        _record("trunk", "LINESTRING (10000 0, 10100 0)",
                highway="trunk", speed_context="rural"),
        _record("dual", "LINESTRING (20000 0, 20100 0)",
                highway="primary", speed_context="rural", oneway="yes"),
        _record("home", "LINESTRING (30000 0, 30100 0)",
                speed_context="motorway"),
        _record("explicit", "LINESTRING (40000 0, 40100 0)",
                highway="service", maxspeed_kmh=40.0),
        _record("crossing", "LINESTRING (50000 0, 50100 0)", crossing_count=1),
        _record("signal", "LINESTRING (60000 0, 60100 0)", signal_count=1),
    ]
    _write_edges(edges, records)
    connection = duckdb.connect()
    try:
        build_car_costs(connection, edges, costs, config=_config())
        times = dict(connection.execute(
            "SELECT edge_key, time_s FROM read_parquet(?)", [str(costs)]
        ).fetchall())
    finally:
        connection.close()
    assert times["parking"] == pytest.approx(100 * 3.6 / 20)
    assert times["trunk"] == pytest.approx(100 * 3.6 / 80)
    assert times["dual"] == pytest.approx(100 * 3.6 / 110)
    assert times["home"] == pytest.approx(100 * 3.6 / 50)
    assert times["explicit"] == pytest.approx(100 * 3.6 / 40)
    assert times["crossing"] == pytest.approx(100 * 3.6 / 50)
    assert times["signal"] == pytest.approx(100 * 3.6 / 50 + 15)


@pytest.mark.parametrize(
    ("highway", "expected_speed"),
    [
        ("living_street", 20), ("service", 20), ("track", 20),
        ("residential", 50), ("footway", 20), ("path", 20),
        ("cycleway", 20), ("pedestrian", 20), ("bridleway", 20),
    ],
)
def test_default_caps_apply_in_all_contexts(tmp_path, highway, expected_speed):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "costs.parquet"
    _write_edges(edges, [
        _record("edge", "LINESTRING (0 0, 100 0)", highway=highway,
                speed_context="motorway")
    ])
    connection = duckdb.connect()
    try:
        build_car_costs(connection, edges, costs, config=_config())
        time_s = connection.execute(
            "SELECT time_s FROM read_parquet(?)", [str(costs)]
        ).fetchone()[0]
    finally:
        connection.close()
    assert time_s == pytest.approx(360 / expected_speed)


def test_class_realism_factor_scales_explicit_speed_limit(tmp_path):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "car_costs.parquet"
    _write_edges(
        edges,
        [
            _record(
                "tagged",
                "LINESTRING (0 0, 100 0)",
                maxspeed_kmh=30.0,
            ),
        ],
    )
    config = _config()
    factors = dict(config.car_speed.realism_factor_by_highway)
    factors["residential"] = 0.5
    car_speed = config.car_speed.model_copy(
        update={"realism_factor_by_highway": factors}
    )
    config = config.model_copy(update={"car_speed": car_speed})
    connection = duckdb.connect()
    try:
        build_car_costs(connection, edges, costs, config=config)
        time_s, bucket = connection.execute(
            f"""
            SELECT time_s, speed_limit_bucket
            FROM read_parquet('{costs.as_posix()}')
            """
        ).fetchone()
    finally:
        connection.close()

    assert time_s == pytest.approx(24.0)
    assert bucket == "le_30"


def test_density_threshold_maximises_label_agreement_and_reports_urban_share(
    tmp_path,
):
    edges = tmp_path / "edges.parquet"
    costs = tmp_path / "car_costs.parquet"
    report = tmp_path / "car_speeds.md"
    _write_edges(
        edges,
        [
            _record(
                "urban",
                "LINESTRING (0 0, 200 0)",
                length_m=200.0,
                speed_context="urban",
            ),
            _record(
                "rural",
                "LINESTRING (10000 0, 10100 0)",
                speed_context="rural",
            ),
            _record(
                "inferred",
                "LINESTRING (0 10, 100 10)",
                speed_context=None,
            ),
        ],
    )
    connection = duckdb.connect()
    try:
        summary = build_car_costs(connection, edges, costs, config=_config())
        inferred_urban = connection.execute(
            f"""
            SELECT is_urban
            FROM read_parquet('{costs.as_posix()}')
            WHERE edge_key = 'inferred'
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert summary.density_agreement == pytest.approx(1.0)
    assert 0.1 < summary.density_threshold_km <= 0.3
    assert inferred_urban is True
    shares = dict(summary.urban_length_share_by_class)
    assert shares["residential"] == pytest.approx(0.75)
    write_car_speed_report(summary, report, state=2021, area="pilot")
    contents = report.read_text(encoding="utf-8")
    assert "Length-weighted urban/rural label agreement: 100.0%" in contents
    assert "residential" in contents
    assert "75.0%" in contents
