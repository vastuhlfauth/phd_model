"""Unit tests for EPCI polygon loading and point-in-polygon matching (5.6)."""

from __future__ import annotations

import json

import duckdb
import pyarrow as pa
from mobgrid.pt.epci import (
    filter_stops_to_contour_coverage,
    load_epci_polygons_3035,
    pattern_ids_within_epci,
)

# A single square commune (0,0)-(1,1) degrees, belonging to EPCI "111111111",
# and a disjoint commune far away belonging to EPCI "222222222".
_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"code": "00001", "epci": "111111111"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
        },
        {
            "type": "Feature",
            "properties": {"code": "00002", "epci": "222222222"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]],
            },
        },
    ],
}


def _write_geojson(tmp_path) -> str:
    path = tmp_path / "communes.geojson"
    path.write_text(json.dumps(_GEOJSON), encoding="utf-8")
    return str(path)


def _write_invalid_geojson(tmp_path) -> str:
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"code": "00001", "epci": "111111111"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                        [[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]],
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"code": "00002", "epci": "222222222"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]
                    ],
                },
            },
        ],
    }
    path = tmp_path / "invalid-communes.geojson"
    path.write_text(json.dumps(geojson), encoding="utf-8")
    return str(path)


def test_load_epci_polygons_restricts_to_requested_sirens(tmp_path) -> None:
    connection = duckdb.connect()
    load_epci_polygons_3035(connection, _write_geojson(tmp_path), ["111111111"])
    rows = connection.execute("SELECT siren FROM epci_polygons").fetchall()
    sirens = {row[0] for row in rows}
    assert sirens == {"111111111"}


def test_pattern_ids_within_epci_matches_a_point_inside(tmp_path) -> None:
    connection = duckdb.connect()
    load_epci_polygons_3035(
        connection, _write_geojson(tmp_path), ["111111111", "222222222"]
    )
    # Project the test points through the same EPSG:4326 -> EPSG:3035
    # transform as the polygon, using a point clearly inside the first
    # commune's square and one clearly outside both.
    points = connection.execute("""
        SELECT ST_X(p) AS x, ST_Y(p) AS y FROM (
            SELECT ST_Transform(
                ST_Point(0.5, 0.5), 'EPSG:4326', 'EPSG:3035', true
            ) AS p
        )
    """).fetchone()
    outside = connection.execute("""
        SELECT ST_X(p) AS x, ST_Y(p) AS y FROM (
            SELECT ST_Transform(
                ST_Point(5.0, 5.0), 'EPSG:4326', 'EPSG:3035', true
            ) AS p
        )
    """).fetchone()
    pattern_stops = pa.table({
        "pattern_id": ["inside", "outside"],
        "x": [points[0], outside[0]],
        "y": [points[1], outside[1]],
    })
    matched = pattern_ids_within_epci(connection, pattern_stops, "111111111")
    assert matched == {"inside"}


def test_pattern_ids_within_epci_returns_empty_for_no_match(tmp_path) -> None:
    connection = duckdb.connect()
    load_epci_polygons_3035(connection, _write_geojson(tmp_path), ["222222222"])
    outside = connection.execute("""
        SELECT ST_X(p) AS x, ST_Y(p) AS y FROM (
            SELECT ST_Transform(
                ST_Point(0.5, 0.5), 'EPSG:4326', 'EPSG:3035', true
            ) AS p
        )
    """).fetchone()
    pattern_stops = pa.table({
        "pattern_id": ["far"], "x": [outside[0]], "y": [outside[1]]
    })
    assert pattern_ids_within_epci(connection, pattern_stops, "222222222") == set()


def test_filter_stops_repairs_invalid_contour_geometry(tmp_path) -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    inside = connection.execute("""
        SELECT ST_X(point), ST_Y(point)
        FROM (
            SELECT ST_Transform(
                ST_Point(0.5, 0.5), 'EPSG:4326', 'EPSG:3035', true
            ) AS point
        )
    """).fetchone()
    outside = connection.execute("""
        SELECT ST_X(point), ST_Y(point)
        FROM (
            SELECT ST_Transform(
                ST_Point(5.0, 5.0), 'EPSG:4326', 'EPSG:3035', true
            ) AS point
        )
    """).fetchone()
    pattern_stops = pa.table({
        "pattern_id": ["inside", "outside"],
        "stop_sequence": [1, 1],
        "x": [inside[0], outside[0]],
        "y": [inside[1], outside[1]],
    })

    filtered = filter_stops_to_contour_coverage(
        connection, pattern_stops, _write_invalid_geojson(tmp_path)
    )

    assert filtered.column("pattern_id").to_pylist() == ["inside"]
