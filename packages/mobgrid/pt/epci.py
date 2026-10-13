"""EPCI polygons for the step 0 spatial coverage check (section 5.6)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa


def load_epci_polygons_3035(
    connection: duckdb.DuckDBPyConnection,
    contours_path: str | Path,
    sirens: list[str] | None = None,
) -> None:
    """Create a temp view ``epci_polygons(siren, geom, xmin, ymin, xmax, ymax)``.

    ``contours_path`` is a WGS84 commune contours GeoJSON carrying an
    ``epci`` SIREN column per commune (for example
    ``data/raw/contours/2026/communes-5m.geojson.gz``); member communes
    are unioned per EPCI and reprojected once to EPSG:3035, with their
    bounding box precomputed so ``pattern_ids_within_epci`` can cheaply
    reject points far from the polygon before the exact containment test.
    ``sirens`` restricts the union to the given EPCIs (needed ones only);
    ``None`` processes every EPCI nationally, which is much slower.
    """
    connection.execute("INSTALL spatial")
    connection.execute("LOAD spatial")
    siren_filter = "epci IS NOT NULL"
    if sirens is not None:
        id_list = ", ".join(f"'{siren}'" for siren in sirens)
        siren_filter = f"epci IN ({id_list})"
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE epci_polygons AS
        SELECT siren, geom,
               ST_XMin(geom) AS xmin, ST_YMin(geom) AS ymin,
               ST_XMax(geom) AS xmax, ST_YMax(geom) AS ymax
        FROM (
            SELECT epci AS siren,
                   ST_Transform(
                       ST_Union_Agg(geom), 'EPSG:4326', 'EPSG:3035', true
                   ) AS geom
            FROM st_read('{Path(contours_path).as_posix()}')
            WHERE {siren_filter}
            GROUP BY epci
        )
    """)


def pattern_ids_within_epci(
    connection: duckdb.DuckDBPyConnection, pattern_stops: pa.Table, siren: str
) -> set[str]:
    """Pattern ids with at least one stop inside the given EPCI's polygon.

    Requires ``load_epci_polygons_3035`` to have been called first, and
    ``pattern_stops`` to carry EPSG:3035 ``x``/``y`` columns (as produced
    by ``stop_tables.load_gtfs_patterns``). The bounding-box pre-filter is
    materialised into its own temp table first, so the exact (and much
    costlier) polygon containment test only runs on the few candidate
    stops, since the unioned EPCI polygon can carry tens of thousands of
    vertices at 5 m precision and a vectorised ``AND`` would otherwise
    still evaluate it for every stop.
    """
    connection.register("pattern_stops_for_epci", pattern_stops)
    try:
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE epci_bbox_candidates AS
            SELECT pattern_stops_for_epci.pattern_id,
                   pattern_stops_for_epci.x, pattern_stops_for_epci.y
            FROM pattern_stops_for_epci, epci_polygons
            WHERE epci_polygons.siren = ?
              AND pattern_stops_for_epci.x BETWEEN epci_polygons.xmin
                                                AND epci_polygons.xmax
              AND pattern_stops_for_epci.y BETWEEN epci_polygons.ymin
                                                AND epci_polygons.ymax
            """,
            [siren],
        )
        rows = connection.execute(
            """
            SELECT DISTINCT epci_bbox_candidates.pattern_id
            FROM epci_bbox_candidates, epci_polygons
            WHERE epci_polygons.siren = ?
              AND ST_Within(
                  ST_Point(epci_bbox_candidates.x, epci_bbox_candidates.y),
                  epci_polygons.geom
              )
            """,
            [siren],
        ).fetchall()
    finally:
        connection.unregister("pattern_stops_for_epci")
    return {row[0] for row in rows}


def filter_stops_to_contour_coverage(
    connection: duckdb.DuckDBPyConnection,
    pattern_stops: pa.Table,
    contours_path: str | Path,
) -> pa.Table:
    """Drop route stops outside metropolitan-France OSM coverage.

    The dated France extracts cover the commune contours used by the project.
    This filter prevents international rail stops from entering ``n``.
    """
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE osm_extract_coverage AS
        SELECT geom, ST_XMin(geom) AS xmin, ST_YMin(geom) AS ymin,
               ST_XMax(geom) AS xmax, ST_YMax(geom) AS ymax
        FROM (
            SELECT ST_Transform(
                ST_Union_Agg(geom), 'EPSG:4326', 'EPSG:3035', true
            ) AS geom
            FROM st_read('{Path(contours_path).as_posix()}')
        )
    """)
    connection.register("rail_stops_for_coverage", pattern_stops)
    try:
        return connection.sql("""
            SELECT rail_stops_for_coverage.*
            FROM rail_stops_for_coverage, osm_extract_coverage
            WHERE rail_stops_for_coverage.x BETWEEN osm_extract_coverage.xmin
                                                   AND osm_extract_coverage.xmax
              AND rail_stops_for_coverage.y BETWEEN osm_extract_coverage.ymin
                                                   AND osm_extract_coverage.ymax
              AND ST_Within(
                  ST_Point(rail_stops_for_coverage.x,
                           rail_stops_for_coverage.y),
                  osm_extract_coverage.geom
              )
            ORDER BY pattern_id, stop_sequence
        """).to_arrow_table()
    finally:
        connection.unregister("rail_stops_for_coverage")
