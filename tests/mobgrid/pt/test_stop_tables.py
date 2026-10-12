"""Unit tests for OSM tag classification and GTFS pattern extraction (5.6)."""

from datetime import date

import duckdb
import pytest
from mobgrid.pt.stop_tables import (
    _LIFECYCLE_EXCLUSION_SQL,
    _MODE_FAMILY_CASE_SQL,
    _PT_TAG_FILTER_SQL,
    _mode_family_from_route_type,
    load_gtfs_patterns,
)


def _classify(
    connection: duckdb.DuckDBPyConnection, tags: dict[str, str]
) -> str | None:
    keys = list(tags.keys())
    values = list(tags.values())
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE one_tag AS SELECT map(?, ?) AS tags",
        [keys, values],
    )
    matches = connection.execute(
        f"SELECT {_PT_TAG_FILTER_SQL} AND {_LIFECYCLE_EXCLUSION_SQL} FROM one_tag"
    ).fetchone()[0]
    if not matches:
        return None
    return connection.execute(
        f"SELECT {_MODE_FAMILY_CASE_SQL} FROM one_tag"
    ).fetchone()[0]


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ({"highway": "bus_stop"}, "bus"),
        ({"amenity": "bus_station"}, "bus"),
        ({"public_transport": "platform", "bus": "yes"}, "bus"),
        ({"railway": "tram_stop"}, "tram"),
        ({"public_transport": "station", "station": "subway"}, "metro"),
        ({"railway": "station", "station": "subway"}, "metro"),
        ({"railway": "station"}, "rail"),
        ({"railway": "halt"}, "rail"),
        ({"public_transport": "platform", "light_rail": "yes"}, "tram"),
    ],
)
def test_mode_family_classification(tags: dict[str, str], expected: str) -> None:
    connection = duckdb.connect()
    assert _classify(connection, tags) == expected


@pytest.mark.parametrize(
    "tags",
    [
        {"construction:highway": "bus_stop", "highway": "construction"},
        {"disused:railway": "station"},
        {"railway": "construction"},
        {"proposed:public_transport": "platform"},
        {"abandoned:amenity": "bus_station"},
    ],
)
def test_lifecycle_prefixed_objects_are_excluded(tags: dict[str, str]) -> None:
    connection = duckdb.connect()
    assert _classify(connection, tags) is None


def test_untagged_mode_is_excluded() -> None:
    # A bare public_transport=platform with no mode-specific tag cannot be
    # classified into bus/tram/metro/rail and is dropped (known limitation).
    connection = duckdb.connect()
    assert _classify(connection, {"public_transport": "platform"}) is None


@pytest.mark.parametrize(
    ("route_type", "expected"),
    [
        (0, "tram"),
        (1, "metro"),
        (2, "rail"),
        (3, "bus"),
        (11, "bus"),
        (700, "bus"),
        (702, "bus"),
        (900, "tram"),
        (109, "rail"),
        (99999, None),
    ],
)
def test_mode_family_from_route_type(route_type: int, expected: str | None) -> None:
    assert _mode_family_from_route_type(route_type) == expected


def test_mode_family_from_route_type_handles_none() -> None:
    assert _mode_family_from_route_type(None) is None


def _write_gtfs_fixture(directory) -> None:
    (directory / "routes.txt").write_text(
        "route_id,route_type\nR1,3\nR2,0\n", encoding="utf-8"
    )
    (directory / "trips.txt").write_text(
        "route_id,service_id,trip_id,direction_id\n"
        "R1,S,T1,0\nR1,S,T2,0\nR2,S,T3,1\n",
        encoding="utf-8",
    )
    (directory / "stop_times.txt").write_text(
        "trip_id,stop_id,stop_sequence\n"
        "T1,A,1\nT1,B,2\nT1,C,3\n"
        "T2,A,1\nT2,B,2\n"
        "T3,D,1\nT3,E,2\n",
        encoding="utf-8",
    )
    (directory / "stops.txt").write_text(
        "stop_id,stop_lat,stop_lon\n"
        "A,45.0,3.0\nB,45.01,3.01\nC,45.02,3.02\nD,48.8,2.3\nE,48.81,2.31\n",
        encoding="utf-8",
    )
    (directory / "calendar.txt").write_text(
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
        "start_date,end_date\n"
        "S,1,1,1,1,1,1,1,20261001,20261231\n",
        encoding="utf-8",
    )


def test_load_gtfs_patterns_groups_distinct_stop_sequences(tmp_path) -> None:
    _write_gtfs_fixture(tmp_path)
    connection = duckdb.connect()
    table = load_gtfs_patterns(connection, tmp_path, date(2026, 10, 13))
    route_ids = set(table.column("route_id").to_pylist())
    mode_families = dict(
        zip(
            table.column("route_id").to_pylist(),
            table.column("mode_family").to_pylist(),
            strict=True,
        )
    )
    assert route_ids == {"R1", "R2"}
    assert mode_families["R1"] == "bus"
    assert mode_families["R2"] == "tram"
    # R1 has two distinct stop sequences (T1: A-B-C, T2: A-B): two patterns.
    pattern_ids = {
        pid
        for pid, route in zip(
            table.column("pattern_id").to_pylist(), table.column("route_id").to_pylist()
        )
        if route == "R1"
    }
    assert len(pattern_ids) == 2


def test_load_gtfs_patterns_restricts_to_route_ids(tmp_path) -> None:
    _write_gtfs_fixture(tmp_path)
    connection = duckdb.connect()
    table = load_gtfs_patterns(
        connection, tmp_path, date(2026, 10, 13), route_ids=["R2"]
    )
    assert set(table.column("route_id").to_pylist()) == {"R2"}
