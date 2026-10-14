"""Configuration and SQL helpers for OSM route-relation extraction."""

import duckdb
from mobgrid.pt.osm_route_extraction import (
    _invalidate_stale_ways_cache,
    configure_extraction_connection,
    memory_limit_gib,
    relation_members,
)


def test_memory_limit_is_sixty_percent_of_ram() -> None:
    assert memory_limit_gib(16 * 1024**3) == 9.6


def test_duckdb_extraction_uses_memory_limit_and_interim_temp(tmp_path) -> None:
    connection = duckdb.connect()
    settings = configure_extraction_connection(
        connection, tmp_path / "data" / "interim", total_memory_bytes=10 * 1024**3
    )
    assert settings.memory_limit == "6.0GiB"
    assert settings.temp_directory.is_dir()
    assert "interim" in settings.temp_directory.parts


def test_relation_members_preserve_types_roles_and_order() -> None:
    rows = relation_members(
        42,
        [100, 200, 300],
        ["way", "node", "way"],
        ["", "stop", "platform"],
    )
    assert [(row.member_type, row.member_id, row.role) for row in rows] == [
        ("way", 100, ""),
        ("node", 200, "stop"),
        ("way", 300, "platform"),
    ]


def test_invalidate_stale_ways_cache_deletes_missing_lifecycle_date_columns(
    tmp_path,
) -> None:
    connection = duckdb.connect()
    stale = tmp_path / "ways.parquet"
    connection.execute(
        """
        COPY (
            SELECT 1 AS relation_id, 1 AS sequence, '' AS role, 1 AS way_id,
                   'tram' AS railway, NULL::VARCHAR AS highway,
                   NULL::VARCHAR AS busway, NULL::VARCHAR AS lanes_bus,
                   NULL::VARCHAR AS construction, false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   NULL::BLOB AS geometry
        ) TO ? (FORMAT PARQUET)
        """,
        [str(stale)],
    )
    _invalidate_stale_ways_cache(connection, stale)
    assert not stale.is_file()


def test_invalidate_stale_ways_cache_keeps_up_to_date_file(tmp_path) -> None:
    connection = duckdb.connect()
    fresh = tmp_path / "ways.parquet"
    connection.execute(
        """
        COPY (
            SELECT 1 AS relation_id, 1 AS sequence, '' AS role, 1 AS way_id,
                   'tram' AS railway, NULL::VARCHAR AS highway,
                   NULL::VARCHAR AS busway, NULL::VARCHAR AS lanes_bus,
                   NULL::VARCHAR AS construction,
                   NULL::VARCHAR AS opening_date, NULL::VARCHAR AS start_date,
                   false AS lifecycle,
                   []::STRUCT(x DOUBLE, y DOUBLE)[] AS points,
                   NULL::BLOB AS geometry
        ) TO ? (FORMAT PARQUET)
        """,
        [str(fresh)],
    )
    _invalidate_stale_ways_cache(connection, fresh)
    assert fresh.is_file()

