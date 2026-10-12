"""Unit tests for exact-date GTFS service selection (section 5.6 / 14.4)."""

from datetime import date

import duckdb
from mobgrid.pt.gtfs_clean import select_active_services


def _active(connection: duckdb.DuckDBPyConnection) -> set[str]:
    rows = connection.execute("SELECT service_id FROM active_services").fetchall()
    return {row[0] for row in rows}


def _connection_with_calendar() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute("""
        CREATE TABLE calendar (
            service_id VARCHAR, monday VARCHAR, tuesday VARCHAR,
            wednesday VARCHAR, thursday VARCHAR, friday VARCHAR,
            saturday VARCHAR, sunday VARCHAR,
            start_date VARCHAR, end_date VARCHAR
        )
    """)
    connection.execute("""
        INSERT INTO calendar VALUES
            ('WEEKDAY', '1','1','1','1','1','0','0', '20261001', '20261231'),
            ('WEEKEND', '0','0','0','0','0','1','1', '20261001', '20261231'),
            ('EXPIRED', '1','1','1','1','1','1','1', '20260101', '20260601')
    """)
    connection.execute("""
        CREATE TABLE calendar_dates (
            service_id VARCHAR, date VARCHAR, exception_type VARCHAR
        )
    """)
    connection.execute("""
        INSERT INTO calendar_dates VALUES
            ('WEEKDAY', '20261013', '2'),
            ('ADDED_ONLY', '20261013', '1')
    """)
    return connection


def test_keeps_regular_service_active_on_the_exact_weekday() -> None:
    # 2026-10-13 is a Tuesday; WEEKEND must not be selected.
    connection = _connection_with_calendar()
    select_active_services(connection, date(2026, 10, 13))
    active = _active(connection)
    assert "WEEKEND" not in active
    assert "EXPIRED" not in active


def test_removal_in_calendar_dates_excludes_the_regular_service() -> None:
    connection = _connection_with_calendar()
    select_active_services(connection, date(2026, 10, 13))
    active = _active(connection)
    assert "WEEKDAY" not in active  # removed by calendar_dates exception_type=2


def test_addition_in_calendar_dates_includes_a_service_with_no_calendar_row() -> None:
    connection = _connection_with_calendar()
    select_active_services(connection, date(2026, 10, 13))
    active = _active(connection)
    assert "ADDED_ONLY" in active


def test_date_outside_the_calendar_range_is_not_active() -> None:
    connection = _connection_with_calendar()
    select_active_services(connection, date(2026, 9, 1))  # before start_date
    active = _active(connection)
    assert "WEEKDAY" not in active


def test_works_without_calendar_dates_table() -> None:
    connection = duckdb.connect()
    connection.execute("""
        CREATE TABLE calendar (
            service_id VARCHAR, monday VARCHAR, tuesday VARCHAR,
            wednesday VARCHAR, thursday VARCHAR, friday VARCHAR,
            saturday VARCHAR, sunday VARCHAR,
            start_date VARCHAR, end_date VARCHAR
        )
    """)
    connection.execute(
        "INSERT INTO calendar VALUES "
        "('S', '1','1','1','1','1','0','0', '20261001', '20261231')"
    )
    select_active_services(connection, date(2026, 10, 13))
    assert _active(connection) == {"S"}
