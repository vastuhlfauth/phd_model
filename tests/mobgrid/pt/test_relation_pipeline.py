"""End-to-end synthetic tests for relation calibration orchestration."""

from pathlib import Path

import duckdb
import pyarrow as pa
from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import (
    GridPoint,
    RelationCalibrationRun,
    RouteRun,
    _rank,
    calibrate_relations,
    evaluate_networks,
    network_relation_coverage,
)
from mobgrid.pt.relation_tables import (
    evaluate_cached_grid_point,
    precompute_relation_tables,
)
from mobgrid.pt.route_calibration import FamilyScore
from mobgrid.pt.route_relations import (
    OSMRelation,
    OSMWay,
    RelationMatch,
    RoutePattern,
    RouteResult,
)


def _pattern(route_id: str, x: float) -> RoutePattern:
    return RoutePattern(
        route_id,
        route_id,
        route_id,
        route_id,
        "bus",
        "Operator",
        10,
        ((x, 0.0), (x + 10, 0.0)),
    )


def _config() -> GtfsRebuildConfig:
    return GtfsRebuildConfig.model_validate(
        {
            "reference_date": "2026-10-13",
            "osm_lifecycle_prefixes": ["construction"],
            "osm_source_ids": {"2022-01-01": "osm"},
            "osm_cache_root": "unused",
            "osm_route_cache_root": "unused",
            "calibration": {
                "r_m": [25],
                "theta": [0.5],
                "k": [2],
                "geometry_share": [0.5],
            },
            "chosen": {
                family: {
                    "r_m": None,
                    "theta": None,
                    "k": None,
                    "geometry_share": None,
                }
                for family in ("bus", "tram", "metro", "rail", "ferry")
            },
            "networks": {},
            "test_epcis": {},
            "known_cases": [],
        }
    )


def test_network_below_half_relations_retains_every_route_not_testable() -> None:
    patterns = {
        "network": [
            _pattern("A", 0),
            _pattern("B", 5_000),
            _pattern("C", 10_000),
        ]
    }
    relation = OSMRelation(
        1,
        "A",
        "A",
        None,
        "Operator",
        "bus",
        (),
        (OSMWay(((-10, 0), (20, 0)), highway="service"),),
    )
    runs, flagged = evaluate_networks(
        patterns,
        {"2022-01-01": [relation]},
        _config(),
        r_m=25,
        k=2,
        theta=0.5,
        geometry_share=0.5,
    )
    assert {run.result.outcome for run in runs} == {"not-testable"}
    assert flagged == {("2022-01-01", "network")}


def _pattern_table() -> pa.Table:
    return pa.table(
        {
            "pattern_id": ["p-a", "p-a", "p-t", "p-t"],
            "route_id": ["A", "A", "T", "T"],
            "direction_id": ["0", "0", "0", "0"],
            "mode_family": ["bus", "bus", "tram", "tram"],
            "transport_mode": ["bus", "bus", "tram", "tram"],
            "route_short_name": ["A", "A", "T", "T"],
            "route_long_name": ["Alpha", "Alpha", "Tram T", "Tram T"],
            "agency_name": ["Operator", "Operator", "Operator", "Operator"],
            "trip_count": [10, 10, 10, 10],
            "stop_sequence": [1, 2, 1, 2],
            "stop_id": ["a1", "a2", "t1", "t2"],
            "lon": [0.0, 0.0, 0.0, 0.0],
            "lat": [0.0, 0.0, 0.0, 0.0],
            "x": [0.0, 10.0, 0.0, 10.0],
            "y": [0.0, 0.0, 20.0, 20.0],
        }
    )


def _write_route_cache(connection: duckdb.DuckDBPyConnection, root: Path) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (1, 'A', 'Alpha line', 'Network', 'Operator', 'bus'),
                (2, 'A', 'Wrong mode', 'Network', 'Operator', 'tram'),
                (3, 'X', 'Renamed', 'Network', 'Operator', 'bus'),
                (4, 'T', 'Tram T', 'Network', 'Operator', 'tram'),
                (5, 'FAR', 'Far', 'Network', 'Operator', 'bus')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, 1::BIGINT AS sequence, '' AS role,
                   relation_id * 10 AS way_id, railway, highway,
                   NULL::VARCHAR AS busway, NULL::VARCHAR AS lanes_bus,
                   construction, false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, y1), ST_Point(x2, y2)
                   ])) AS geometry
            FROM VALUES
                (1, NULL, 'service', NULL, -10.0, 0.0, 20.0, 0.0),
                (2, 'tram', NULL, NULL, -10.0, 0.0, 20.0, 0.0),
                (3, NULL, 'service', NULL, -10.0, 5.0, 20.0, 5.0),
                (4, 'tram', NULL, 'yes', -10.0, 20.0, 20.0, 20.0),
                (5, NULL, 'service', NULL, 100000.0, 0.0, 100010.0, 0.0)
            AS t(relation_id, railway, highway, construction, x1, y1, x2, y2)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT NULL::BIGINT AS relation_id, NULL::BIGINT AS sequence,
                   NULL::VARCHAR AS role, NULL::BIGINT AS node_id,
                   NULL::VARCHAR AS public_transport,
                   NULL::VARCHAR AS railway, NULL::VARCHAR AS highway,
                   NULL::DOUBLE AS x, NULL::DOUBLE AS y,
                   NULL::BLOB AS geometry
            WHERE false
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_duckdb_precompute_writes_local_distance_and_name_tables(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_route_cache(connection, route_cache)

    summary = precompute_relation_tables(
        connection,
        {"network": _pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=100,
    )

    distances = connection.execute(
        "SELECT pattern_id, relation_id, in_service, min(distance_m) "
        "FROM read_parquet(?) WHERE NOT is_fallback "
        "GROUP BY ALL ORDER BY pattern_id, relation_id, in_service",
        [str(summary.distances_path)],
    ).fetchall()
    names = connection.execute(
        "SELECT pattern_id, relation_id FROM read_parquet(?) "
        "ORDER BY pattern_id, relation_id",
        [str(summary.names_path)],
    ).fetchall()
    assert distances == [
        ("p-a", 1, True, 0.0),
        ("p-a", 3, True, 5.0),
        ("p-t", 2, True, 20.0),
        ("p-t", 4, False, 0.0),
    ]
    assert names == [("p-a", 1), ("p-t", 4)]


def test_cached_grid_evaluation_uses_no_geometry(tmp_path) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=100,
    )

    runs, flagged = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=25,
        k=2,
        theta=0.5,
        geometry_share=0.5,
    )

    assert flagged == set()
    assert [(run.pattern.route_id, run.result.outcome) for run in runs] == [
        ("A", "kept")
    ]

    decimal_runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=25,
        k=2,
        theta=0.6,
        geometry_share=0.3,
    )
    assert [run.pattern.route_id for run in decimal_runs] == ["A"]


def test_parameter_ranking_prefers_exact_known_cases_before_false_changes() -> None:
    exact = GridPoint(
        "bus",
        100,
        2,
        0.7,
        0.5,
        FamilyScore("bus", 2, 2, 1.0, 1.0, 1.0, 10, 0.2),
    )
    low_false_changes = GridPoint(
        "bus",
        25,
        1,
        0.5,
        0.3,
        FamilyScore("bus", 2, 1, 1.0, 0.5, 2 / 3, 10, 0.0),
    )
    assert _rank(exact) > _rank(low_false_changes)


def _bhns_pattern_table() -> pa.Table:
    # "Express X" (BHNS by name) and "Y" (a regular bus) share the same
    # five-stop geometry and the same matched relation/ways, so only the
    # BHNS classification differs between them.
    stops_x = [0.0, 10.0, 20.0, 30.0, 40.0]
    return pa.table(
        {
            "pattern_id": ["p-x"] * 5 + ["p-y"] * 5,
            "route_id": ["X"] * 5 + ["Y"] * 5,
            "direction_id": ["0"] * 10,
            "mode_family": ["bus"] * 10,
            "transport_mode": ["bus"] * 10,
            "route_short_name": ["X"] * 5 + ["Y"] * 5,
            "route_long_name": ["Express X"] * 5 + ["Line Y"] * 5,
            "agency_name": ["Operator"] * 10,
            "trip_count": [10] * 10,
            "stop_sequence": [1, 2, 3, 4, 5] * 2,
            "stop_id": [f"x{i}" for i in range(5)] + [f"y{i}" for i in range(5)],
            "lon": [0.0] * 10,
            "lat": [0.0] * 10,
            "x": stops_x + stops_x,
            "y": [0.0] * 10,
        }
    )


def _write_bhns_route_cache(connection: duckdb.DuckDBPyConnection, root: Path) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (1, 'X', 'Express X', 'Network', 'Operator', 'bus'),
                (2, 'Y', 'Line Y', 'Network', 'Operator', 'bus')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, sequence, '' AS role, way_id,
                   NULL::VARCHAR AS railway, highway, busway, lanes_bus,
                   NULL::VARCHAR AS construction, false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, y1), ST_Point(x2, y2)
                   ])) AS geometry
            FROM VALUES
                -- dedicated busway, covers only the middle three stops
                (1, 1, 11, 'service', 'lane', NULL, 9.0, 0.0, 31.0, 0.0),
                -- plain residential way, covers every stop
                (1, 2, 12, 'residential', NULL, NULL, -10.0, 0.0, 50.0, 0.0),
                (2, 1, 21, 'service', 'lane', NULL, 9.0, 0.0, 31.0, 0.0),
                (2, 2, 22, 'residential', NULL, NULL, -10.0, 0.0, 50.0, 0.0)
            AS t(relation_id, sequence, way_id, highway, busway, lanes_bus,
                 x1, y1, x2, y2)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT NULL::BIGINT AS relation_id, NULL::BIGINT AS sequence,
                   NULL::VARCHAR AS role, NULL::BIGINT AS node_id,
                   NULL::VARCHAR AS public_transport,
                   NULL::VARCHAR AS railway, NULL::VARCHAR AS highway,
                   NULL::DOUBLE AS x, NULL::DOUBLE AS y,
                   NULL::BLOB AS geometry
            WHERE false
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_bhns_route_is_cut_like_a_tram_while_a_regular_bus_is_not(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_bhns_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _bhns_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=5,
    )

    runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=5,
        k=1,
        theta=0.5,
        geometry_share=0.5,
    )

    outcomes = {run.pattern.route_id: run for run in runs}
    assert outcomes["X"].pattern.is_bhns
    assert outcomes["X"].result.outcome == "cut"
    assert outcomes["X"].result.start_index == 1
    assert outcomes["X"].result.end_index == 3
    assert not outcomes["Y"].pattern.is_bhns
    assert outcomes["Y"].result.outcome == "kept"
    assert outcomes["Y"].result.start_index == 0
    assert outcomes["Y"].result.end_index == 4


def _any_relation_pattern_table() -> pa.Table:
    return pa.table(
        {
            "pattern_id": ["p-f"] * 2,
            "route_id": ["F"] * 2,
            "direction_id": ["0"] * 2,
            "mode_family": ["tram"] * 2,
            "transport_mode": ["tram"] * 2,
            "route_short_name": ["A"] * 2,
            "route_long_name": ["Tram A"] * 2,
            "agency_name": ["Operator"] * 2,
            "trip_count": [10, 10],
            "stop_sequence": [1, 2],
            "stop_id": ["f1", "f2"],
            "lon": [0.0, 0.0],
            "lat": [0.0, 0.0],
            "x": [0.0, 10.0],
            "y": [0.0, 0.0],
        }
    )


def _write_any_relation_route_cache(
    connection: duckdb.DuckDBPyConnection, root: Path
) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (1, 'A', 'Tram A', 'Network', 'Operator', 'tram'),
                (2, 'B', 'Tram B', 'Network', 'Operator', 'tram')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, 1::BIGINT AS sequence, '' AS role,
                   relation_id * 10 AS way_id, 'tram' AS railway,
                   NULL::VARCHAR AS highway, NULL::VARCHAR AS busway,
                   NULL::VARCHAR AS lanes_bus, NULL::VARCHAR AS construction,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, y1), ST_Point(x2, y2)
                   ])) AS geometry
            FROM VALUES
                -- matched by name (ref "A"), but its own track is 500 m away
                (1, -500.0, 0.0, -490.0, 0.0),
                -- never matched (ref "B"), but its track covers F's stops
                (2, -10.0, 0.0, 20.0, 0.0)
            AS t(relation_id, x1, y1, x2, y2)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT NULL::BIGINT AS relation_id, NULL::BIGINT AS sequence,
                   NULL::VARCHAR AS role, NULL::BIGINT AS node_id,
                   NULL::VARCHAR AS public_transport,
                   NULL::VARCHAR AS railway, NULL::VARCHAR AS highway,
                   NULL::DOUBLE AS x, NULL::DOUBLE AS y,
                   NULL::BLOB AS geometry
            WHERE false
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_fixed_guideway_coverage_uses_any_same_mode_relations_track(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_any_relation_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _any_relation_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=25,
    )

    runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="tram",
        r_m=25,
        k=2,
        theta=0.5,
        geometry_share=0.5,
    )

    assert len(runs) == 1
    result = runs[0].result
    # Identity still comes from the matched relation (name pass, ref "A"),
    # but coverage comes from relation "B"'s track, within 25 m of both
    # stops, even though "B" was never selected as a match.
    assert result.match_pass == "name"
    assert result.relation_refs == ("A",)
    assert result.outcome == "kept"
    assert result.covered_share == 1.0


def _route_run(
    network: str, date_key: str, route_id: str, relation_ids: tuple[int, ...]
) -> RouteRun:
    pattern = RoutePattern(route_id, route_id, route_id, route_id, "bus", "Op", 1, ())
    match = RelationMatch(
        "name" if relation_ids else None, relation_ids, (), 1.0 if relation_ids else 0.0
    )
    result = RouteResult(
        route_id, "kept", match.pass_name, relation_ids, (), 1, 1, 1.0, 0, 0
    )
    return RouteRun(network, date_key, pattern, match, result, "kept", False, None)


def test_network_relation_coverage_is_the_matched_share_per_network_date() -> None:
    run = RelationCalibrationRun(
        final_routes=[
            _route_run("net", "2022-01-01", "A", (1,)),
            _route_run("net", "2022-01-01", "B", ()),
            _route_run("net", "2022-01-01", "C", (2,)),
            _route_run("net", "2024-01-01", "A", ()),
        ]
    )
    coverage = network_relation_coverage(run)
    assert coverage[("net", "2022-01-01")] == 2 / 3
    assert coverage[("net", "2024-01-01")] == 0.0


def _metro_rail_pattern_table() -> pa.Table:
    return pa.table(
        {
            "pattern_id": ["p-m", "p-m", "p-r", "p-r"],
            "route_id": ["M", "M", "R", "R"],
            "direction_id": ["0", "0", "0", "0"],
            "mode_family": ["metro", "metro", "rail", "rail"],
            "transport_mode": ["metro", "metro", "rail", "rail"],
            "route_short_name": ["M", "M", "R", "R"],
            "route_long_name": ["Metro M", "Metro M", "Rail R", "Rail R"],
            "agency_name": ["Operator"] * 4,
            "trip_count": [10, 10, 10, 10],
            "stop_sequence": [1, 2, 1, 2],
            "stop_id": ["m1", "m2", "r1", "r2"],
            "lon": [0.0] * 4,
            "lat": [0.0] * 4,
            "x": [0.0, 10.0, 0.0, 1000.0],
            "y": [0.0, 0.0, 0.0, 0.0],
        }
    )


def _write_metro_rail_route_cache(
    connection: duckdb.DuckDBPyConnection, root: Path
) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (10, 'M', 'Metro M', 'Network', 'Operator', 'subway'),
                (20, 'R', 'Rail R', 'Network', 'Operator', 'train')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, 1::BIGINT AS sequence, '' AS role,
                   relation_id * 10 AS way_id, railway,
                   NULL::VARCHAR AS highway, NULL::VARCHAR AS busway,
                   NULL::VARCHAR AS lanes_bus, NULL::VARCHAR AS construction,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, y1), ST_Point(x2, y2)
                   ])) AS geometry
            FROM VALUES
                -- fully covers both metro stops (x=0 and x=10)
                (10, 'subway', -10.0, 0.0, 20.0, 0.0),
                -- within the 1 km candidate window but far outside r=25 m,
                -- so it still matches by name yet covers neither rail stop
                (20, 'rail', 500.0, 0.0, 510.0, 0.0)
            AS t(relation_id, railway, x1, y1, x2, y2)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT NULL::BIGINT AS relation_id, NULL::BIGINT AS sequence,
                   NULL::VARCHAR AS role, NULL::BIGINT AS node_id,
                   NULL::VARCHAR AS public_transport,
                   NULL::VARCHAR AS railway, NULL::VARCHAR AS highway,
                   NULL::DOUBLE AS x, NULL::DOUBLE AS y,
                   NULL::BLOB AS geometry
            WHERE false
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_rail_chosen_score_is_computed_on_rail_routes_not_aliased_from_metro(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_metro_rail_route_cache(connection, route_cache)
    precompute = precompute_relation_tables(
        connection,
        {"network": _metro_rail_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=25,
    )

    _, chosen, _ = calibrate_relations(connection, precompute, _config())

    assert chosen["rail"].mode_family == "rail"
    assert chosen["metro"].mode_family == "metro"
    assert chosen["rail"].score is not chosen["metro"].score
    # Metro's single route is fully covered; rail's is dropped (its second
    # stop, 1 km away, is far outside the matched relation's track).
    assert chosen["metro"].score.false_change_rate == 0.0
    assert chosen["rail"].score.false_change_rate == 1.0
    assert chosen["metro"].score.presumed_unchanged_total == 1
    assert chosen["rail"].score.presumed_unchanged_total == 1


def _bus_homonym_pattern_table() -> pa.Table:
    # Route "Z": 4 equally-spaced stops, so the weak name match below
    # covers exactly 1/4 = 0.25 (a homonym, < 0.3). Route "M": 3 stops, so
    # its weak name match covers exactly 1/3 = 0.333 (not a homonym, but
    # below the 0.5 "kept" bar -- the ambiguous zone of section 5.6 point 2).
    stops_z = [0.0, 10.0, 20.0, 30.0]
    stops_m = [0.0, 10.0, 20.0]
    return pa.table(
        {
            "pattern_id": ["p-z"] * 4 + ["p-m"] * 3,
            "route_id": ["Z"] * 4 + ["M"] * 3,
            "direction_id": ["0"] * 7,
            "mode_family": ["bus"] * 7,
            "transport_mode": ["bus"] * 7,
            "route_short_name": ["Z"] * 4 + ["M"] * 3,
            "route_long_name": ["Zed"] * 4 + ["Mu"] * 3,
            "agency_name": ["Operator"] * 7,
            "trip_count": [10] * 7,
            "stop_sequence": [1, 2, 3, 4, 1, 2, 3],
            "stop_id": [f"z{i}" for i in range(4)] + [f"m{i}" for i in range(3)],
            "lon": [0.0] * 7,
            "lat": [0.0] * 7,
            "x": stops_z + stops_m,
            "y": [0.0] * 7,
        }
    )


def _write_bus_homonym_route_cache(
    connection: duckdb.DuckDBPyConnection, root: Path
) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                -- ref "Z" is a homonym: its own way covers only 1 of 4 stops
                (1, 'Z', 'Not the real Z', 'Network', 'Operator', 'bus'),
                -- unmatched by name, but its way covers every "Z" stop
                (2, 'W', 'Renamed Z', 'Network', 'Operator', 'bus'),
                -- ref "M" covers 1 of 3 stops: not a homonym (>= 0.3), but
                -- short of "kept" (< 0.5); no geometry fallback should run
                (3, 'M', 'Weak M', 'Network', 'Operator', 'bus'),
                -- unmatched by name; would fully cover "M" if it were ever
                -- considered, which it must not be in the 0.3-0.5 zone
                (4, 'N', 'Renamed M', 'Network', 'Operator', 'bus')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, 1::BIGINT AS sequence, '' AS role,
                   relation_id * 10 AS way_id, NULL::VARCHAR AS railway,
                   'service' AS highway, NULL::VARCHAR AS busway,
                   NULL::VARCHAR AS lanes_bus, NULL::VARCHAR AS construction,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, 0.0), ST_Point(x2, 0.0)
                   ])) AS geometry
            FROM VALUES
                (1, -1.0, 1.0),
                (2, -5.0, 35.0),
                (3, -1.0, 1.0),
                (4, -5.0, 25.0)
            AS t(relation_id, x1, x2)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT NULL::BIGINT AS relation_id, NULL::BIGINT AS sequence,
                   NULL::VARCHAR AS role, NULL::BIGINT AS node_id,
                   NULL::VARCHAR AS public_transport,
                   NULL::VARCHAR AS railway, NULL::VARCHAR AS highway,
                   NULL::DOUBLE AS x, NULL::DOUBLE AS y,
                   NULL::BLOB AS geometry
            WHERE false
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_bus_homonym_name_match_falls_back_to_geometry(tmp_path) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_bus_homonym_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _bus_homonym_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=2,
    )

    runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=2,
        k=1,
        theta=0.9,
        geometry_share=0.5,
    )

    result = {run.pattern.route_id: run.result for run in runs}["Z"]
    assert result.match_pass == "geometry"
    assert result.relation_ids == (2,)
    assert result.covered_share == 1.0
    assert result.outcome == "kept-renamed"


def test_bus_name_match_in_the_ambiguous_zone_is_dropped_without_geometry_rescue(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_bus_homonym_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _bus_homonym_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=2,
    )

    runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=2,
        k=1,
        theta=0.9,
        geometry_share=0.5,
    )

    result = {run.pattern.route_id: run.result for run in runs}["M"]
    # Not a homonym (0.333 >= 0.3), but below the 0.5 "kept" bar: dropped,
    # not rescued by relation "N" even though it would fully cover "M".
    assert result.match_pass == "name"
    assert result.relation_ids == (3,)
    assert abs(result.covered_share - 1 / 3) < 1e-9
    assert result.outcome == "dropped"


def _ferry_pattern_table() -> pa.Table:
    return pa.table(
        {
            "pattern_id": ["p-ferry"] * 2,
            "route_id": ["F"] * 2,
            "direction_id": ["0"] * 2,
            "mode_family": ["ferry"] * 2,
            "transport_mode": ["ferry"] * 2,
            "route_short_name": ["F"] * 2,
            "route_long_name": ["Ferry F"] * 2,
            "agency_name": ["Operator"] * 2,
            "trip_count": [10, 10],
            "stop_sequence": [1, 2],
            "stop_id": ["f1", "f2"],
            "lon": [0.0, 0.0],
            "lat": [0.0, 0.0],
            "x": [0.0, 1000.0],
            "y": [0.0, 0.0],
        }
    )


def _write_ferry_route_cache(
    connection: duckdb.DuckDBPyConnection, root: Path
) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                -- name-matched: its own way runs straight through both
                -- stops (a decoy -- must be ignored), its member piers are
                -- 150 m away, within the fixed 200 m ferry radius
                (1, 'F', 'Ferry F', 'Network', 'Operator', 'ferry'),
                -- never name-matched: also has a decoy way straight
                -- through both stops, but its piers are 5 km away, well
                -- outside 200 m, so it must never be picked as a match
                (2, 'G', 'Ferry G', 'Network', 'Operator', 'ferry')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, 1::BIGINT AS sequence, '' AS role,
                   relation_id * 10 AS way_id, NULL::VARCHAR AS railway,
                   NULL::VARCHAR AS highway, NULL::VARCHAR AS busway,
                   NULL::VARCHAR AS lanes_bus, NULL::VARCHAR AS construction,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(0.0, 0.0), ST_Point(1000.0, 0.0)
                   ])) AS geometry
            FROM VALUES (1), (2) AS t(relation_id)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "ways.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT relation_id, sequence, '' AS role, node_id,
                   'platform' AS public_transport, NULL::VARCHAR AS railway,
                   NULL::VARCHAR AS highway, x, y,
                   ST_AsWKB(ST_Point(x, y)) AS geometry
            FROM VALUES
                (1, 1, 1, 0.0, 150.0),
                (1, 2, 2, 1000.0, 150.0),
                (2, 1, 3, 0.0, 5000.0),
                (2, 2, 4, 1000.0, 5000.0)
            AS t(relation_id, sequence, node_id, x, y)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "stops.parquet")],
    )
    (root / "_SUCCESS.json").write_text("{}", encoding="utf-8")


def test_ferry_coverage_uses_member_piers_not_ways_within_a_fixed_200m(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    route_cache = tmp_path / "routes"
    _write_ferry_route_cache(connection, route_cache)
    summary = precompute_relation_tables(
        connection,
        {"network": _ferry_pattern_table()},
        {"2022-01-01": route_cache},
        {},
        tmp_path / "precompute",
        _config(),
        max_r_m=25,
    )

    distances = connection.execute(
        "SELECT relation_id, min(distance_m) FROM read_parquet(?) "
        "WHERE NOT is_fallback GROUP BY relation_id ORDER BY relation_id",
        [str(summary.distances_path)],
    ).fetchall()
    # Neither relation's 0 m decoy way survives into the cached distances:
    # relation 1 shows its 150 m pier distance, relation 2 (piers 5 km
    # away) is absent entirely, not the 0 m its decoy way would give.
    assert distances == [(1, 150.0)]

    runs, _ = evaluate_cached_grid_point(
        connection,
        summary,
        _config(),
        family="bus",
        r_m=25,
        k=1,
        theta=0.9,
        geometry_share=0.3,
    )

    result = runs[0].result
    # r_m=25 is far smaller than the 150 m pier distance: ferry coverage
    # uses the fixed 200 m radius regardless of the calibrated r_m.
    assert result.match_pass == "name"
    assert result.relation_ids == (1,)
    assert result.covered_share == 1.0
    assert result.outcome == "kept"
