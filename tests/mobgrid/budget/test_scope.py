"""Synthetic acceptance tests for the three-switch scope (section 9.9)."""

import duckdb
import pytest
from mobgrid.budget import scope


@pytest.fixture
def scoped_days() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.sql("""
        CREATE TABLE scope_input (
            day_id VARCHAR, num_dep INTEGER, origin_purpose VARCHAR,
            destination_purpose VARCHAR, destination_motive DOUBLE,
            motive DOUBLE, moridom INTEGER, mode_group VARCHAR,
            mobloc INTEGER, departure_time TIME, arrival_time TIME
        );
        INSERT INTO scope_input VALUES
          ('closed', 2, '9.1', '1.1', 1.1, 9.1, 2, 'car_driver', 0,
            '18:00', '18:30'),
          ('closed', 1, '1.1', '9.1', 9.1, 9.1, 1, 'car_driver', 1,
            '08:00', '08:30'),
          ('open', 1, '1.1', '9.1', 9.1, 9.1, 1, 'car_driver', 1,
            '08:00', '08:30'),
          ('study', 1, '1.1', '1.11', 1.4, 1.4, 1, 'walk', 1,
            '08:00', '08:30'),
          ('childcare', 1, '1.1', '1.12', 1.5, 1.5, 1, 'walk', 1,
            '08:00', '08:30'),
          ('fallback', 1, NULL, '1.2', 1.2, NULL, 1, 'walk', 1,
            '08:00', '08:30'),
          ('missing', 1, '1.1', NULL, NULL, NULL, 1, 'walk', 1,
            '08:00', '08:30'),
          ('holiday', 1, '1.1', '8.80', 8.1, 8.1, 1, 'car_driver', 1,
            '08:00', '08:30'),
          ('tennis', 1, '1.1', '7.6', 7.6, 7.6, 1, 'walk', 1,
            '08:00', '08:30'),
          ('tennis', 2, '7.6', '1.1', 1.1, 7.6, 2, 'walk', 1,
            '09:00', '09:30'),
          ('run', 1, '1.1', '7.6', 7.6, 7.6, 1, 'walk', 1,
            '08:00', '08:30'),
          ('run', 2, '7.6', '1.1', 1.1, 7.6, 2, 'walk', 1,
            '08:44', '09:00'),
          ('boundary', 1, '1.1', '7.76', 7.6, 7.6, 1, 'cycle', 1,
            '08:00', '08:30'),
          ('boundary', 2, '7.76', '1.1', 1.1, 7.6, 2, 'cycle', 1,
            '08:45', '09:00'),
          ('car_sport', 1, '1.1', '7.8', 7.8, 7.8, 1, 'car_driver', 1,
            '08:00', '08:30'),
          ('stroll', 1, '1.1', '7.77', 7.7, 7.7, 1, 'walk', 1,
            '08:00', '08:30'),
          ('stroll', 2, '7.77', '1.1', 1.1, 7.7, 2, 'car_driver', 1,
            '08:40', '09:00'),
          ('ride', 1, '1.1', '7.78', 7.8, 7.8, 1, 'cycle', 1,
            '08:00', '08:30'),
          ('no_next', 1, '1.1', '7.6', 7.6, 7.6, 1, 'walk', 1,
            '08:00', '08:30'),
          ('missing_origin', 1, NULL, '1.1', 1.1, NULL, 2, 'walk', 1,
            '08:00', '08:30'),
          ('midnight', 1, '1.1', '7.6', 7.6, 7.6, 1, 'walk', 1,
            '23:30', '23:55'),
          ('midnight', 2, '7.6', '1.1', 1.1, 7.6, 2, 'walk', 1,
            '00:05', '00:25');
    """)
    scope.create_scope_views(con, activity_stay_min=15)
    return con


def test_scope_ids_and_labels() -> None:
    assert len(scope.ALL_SCOPES) == 8
    selected = scope.Scope.parse("round-dest-local")
    assert selected.id == "round-dest-local"
    assert selected.label == "Round-trip days · destination purposes · local (≤ 80 km)"
    with pytest.raises(ValueError):
        scope.Scope.parse("round-needs-local")


def test_round_day_full_chain_and_raw_codes(
    scoped_days: duckdb.DuckDBPyConnection,
) -> None:
    rows = dict(scoped_days.sql("SELECT day_id, is_round FROM scope_days").fetchall())
    assert rows["closed"] is True
    assert rows["open"] is False
    assert rows["study"] is False
    assert rows["childcare"] is False
    assert rows["fallback"] is True
    assert rows["missing_origin"] is False
    assert rows["missing"] is False


def test_destination_rules_and_returns(scoped_days: duckdb.DuckDBPyConnection) -> None:
    rows = scoped_days.sql("""
        SELECT day_id, list(is_destination ORDER BY num_dep)
        FROM scope_trips GROUP BY day_id
    """).fetchall()
    flags = dict(rows)
    assert flags["holiday"] == [False]
    assert flags["tennis"] == [True, True]
    assert flags["run"] == [False, False]
    assert flags["boundary"] == [True, True]
    assert flags["car_sport"] == [True]
    assert flags["stroll"] == [False, False]
    assert flags["ride"] == [False]
    assert flags["no_next"] == [True]
    assert flags["midnight"] == [False, False]


def test_invalid_day_order_is_rejected() -> None:
    con = duckdb.connect()
    con.sql("CREATE TABLE scope_input (day_id VARCHAR, num_dep INTEGER)")
    con.sql("INSERT INTO scope_input VALUES ('day', 1), ('day', 1)")
    with pytest.raises(ValueError, match="unique"):
        scope.create_scope_views(con, activity_stay_min=15)


def test_independent_switches_use_full_day(
    scoped_days: duckdb.DuckDBPyConnection,
) -> None:
    selected = scope.Scope.parse("round-dest-local")
    rows = scoped_days.sql(
        f"SELECT day_id, num_dep FROM scope_trips WHERE {selected.where_sql}"
    ).fetchall()
    assert ("closed", 1) in rows
    assert ("closed", 2) not in rows
    assert not any(day == "open" for day, _ in rows)
    daytable = scope.Scope.parse("alldays-allpurp-daytable")
    rows = scoped_days.sql(
        f"SELECT day_id, num_dep FROM scope_trips WHERE {daytable.where_sql}"
    ).fetchall()
    assert ("closed", 2) in rows
    assert ("open", 1) in rows
