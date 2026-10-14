"""Unit tests for the DuckDB spatial precompute helpers (5.6 BHNS decision)."""

from __future__ import annotations

from pathlib import Path

import duckdb
from mobgrid.pt.relation_tables import _create_osm_views


def _write_opening_date_route_cache(
    connection: duckdb.DuckDBPyConnection, root: Path
) -> None:
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (1, 'T', 'Tram T', 'Network', 'Operator', 'tram')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT 1 AS relation_id, sequence, '' AS role, way_id,
                   'tram' AS railway, NULL::VARCHAR AS highway,
                   NULL::VARCHAR AS busway, NULL::VARCHAR AS lanes_bus,
                   NULL::VARCHAR AS construction, opening_date, start_date,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(x1, y1), ST_Point(x2, y2)
                   ])) AS geometry
            FROM VALUES
                -- in service: no lifecycle date at all
                (1, 10, NULL, NULL, -10.0, 0.0, 10.0, 0.0),
                -- a full ISO opening_date after the 2022-01-01 snapshot
                (2, 20, '2023-06-15', NULL, 90.0, 0.0, 110.0, 0.0),
                -- a bare future year in start_date
                (3, 30, NULL, '2024', 190.0, 0.0, 210.0, 0.0),
                -- an opening_date in the past (already in service)
                (4, 40, '2020-01-01', NULL, 290.0, 0.0, 310.0, 0.0)
            AS t(sequence, way_id, opening_date, start_date, x1, y1, x2, y2)
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


def test_ways_with_a_future_opening_or_start_date_are_not_in_service(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    root = tmp_path / "routes"
    _write_opening_date_route_cache(connection, root)

    _create_osm_views(connection, {"2022-01-01": root})

    rows = connection.execute(
        "SELECT way_id, in_service FROM calibration_relation_ways ORDER BY way_id"
    ).fetchall()
    assert rows == [
        (10, True),  # no date tag: in service
        (20, False),  # opening_date 2023-06-15 > 2022-01-01
        (30, False),  # start_date bare year 2024 > 2022
        (40, True),  # opening_date 2020-01-01 <= 2022-01-01
    ]


def test_opening_date_columns_absent_is_backward_compatible(tmp_path) -> None:
    """A cache predating the opening_date/start_date columns still works."""
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    root = tmp_path / "routes"
    root.mkdir(parents=True)
    connection.execute(
        """
        COPY (
            SELECT * FROM VALUES
                (1, 'T', 'Tram T', 'Network', 'Operator', 'tram')
            AS t(relation_id, ref, name, network, operator, route)
        ) TO ? (FORMAT PARQUET)
        """,
        [str(root / "relations.parquet")],
    )
    connection.execute(
        """
        COPY (
            SELECT 1 AS relation_id, 1::BIGINT AS sequence, '' AS role,
                   10 AS way_id, 'tram' AS railway,
                   NULL::VARCHAR AS highway, NULL::VARCHAR AS busway,
                   NULL::VARCHAR AS lanes_bus, NULL::VARCHAR AS construction,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   ST_AsWKB(ST_MakeLine([
                       ST_Point(-10.0, 0.0), ST_Point(10.0, 0.0)
                   ])) AS geometry
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

    _create_osm_views(connection, {"2022-01-01": root})

    rows = connection.execute(
        "SELECT way_id, in_service FROM calibration_relation_ways"
    ).fetchall()
    assert rows == [(10, True)]
