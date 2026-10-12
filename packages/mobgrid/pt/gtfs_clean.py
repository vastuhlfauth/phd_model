"""Exact-date GTFS service selection shared by the rebuild test (section 5.6)."""

from __future__ import annotations

from datetime import date

import duckdb


def select_active_services(
    connection: duckdb.DuckDBPyConnection, reference_date: date
) -> None:
    """Create a temp view ``active_services(service_id)`` for one exact date.

    A service is active when its day-of-week flag and date range in
    ``calendar`` cover ``reference_date``, minus ``calendar_dates``
    removals, plus ``calendar_dates`` additions for that date (section
    14.4: day-of-week flag, date range, additions and removals; not "any
    weekday whose range overlaps", and removals are not ignored). Requires
    the ``trips`` view, and optionally ``calendar``/``calendar_dates``, to
    already be registered on ``connection``.
    """
    has_calendar = connection.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = 'calendar'"
    ).fetchone()[0]
    has_exceptions = connection.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_name = 'calendar_dates'"
    ).fetchone()[0]
    weekday_column = (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )[reference_date.weekday()]
    reference = reference_date.isoformat()
    reference_compact = reference_date.strftime("%Y%m%d")
    if has_calendar:
        connection.execute(f"""
            CREATE OR REPLACE TEMP VIEW regular_services AS
            SELECT service_id FROM calendar
            WHERE {weekday_column} = '1'
              AND strptime(start_date, '%Y%m%d') <= DATE '{reference}'
              AND strptime(end_date, '%Y%m%d') >= DATE '{reference}'
        """)
    else:
        connection.execute(
            "CREATE OR REPLACE TEMP VIEW regular_services AS "
            "SELECT NULL::VARCHAR AS service_id WHERE false"
        )
    if has_exceptions:
        connection.execute(f"""
            CREATE OR REPLACE TEMP VIEW added_services AS
            SELECT DISTINCT service_id FROM calendar_dates
            WHERE date = '{reference_compact}' AND exception_type = '1'
        """)
        connection.execute(f"""
            CREATE OR REPLACE TEMP VIEW removed_services AS
            SELECT DISTINCT service_id FROM calendar_dates
            WHERE date = '{reference_compact}' AND exception_type = '2'
        """)
    else:
        connection.execute(
            "CREATE OR REPLACE TEMP VIEW added_services AS "
            "SELECT NULL::VARCHAR AS service_id WHERE false"
        )
        connection.execute(
            "CREATE OR REPLACE TEMP VIEW removed_services AS "
            "SELECT NULL::VARCHAR AS service_id WHERE false"
        )
    connection.execute("""
        CREATE OR REPLACE TEMP VIEW active_services AS
        SELECT service_id FROM regular_services
        WHERE service_id NOT IN (SELECT service_id FROM removed_services)
        UNION
        SELECT service_id FROM added_services
    """)
