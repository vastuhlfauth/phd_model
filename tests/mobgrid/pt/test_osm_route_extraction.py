"""Configuration and SQL helpers for OSM route-relation extraction."""

import duckdb
from mobgrid.pt.osm_route_extraction import (
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

