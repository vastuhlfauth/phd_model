"""Study-area construction and resumable OSM extraction for section 8.1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pyarrow as pa
from common.duckdb_io import read_parquet, write_parquet


@dataclass(frozen=True)
class AreaGeometry:
    """Buffered study area in EPSG:3035 and its WGS84 reading bounds."""

    geometry_wkb: bytes
    west: float
    south: float
    east: float
    north: float


def _sql_path(path: str | Path) -> str:
    """Return a quoted-safe DuckDB path using forward slashes."""
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_area(
    connection: duckdb.DuckDBPyConnection,
    contours_path: str | Path,
    *,
    area: str,
    department: str,
    halo_km: float,
) -> AreaGeometry:
    """Dissolve commune contours, buffer in EPSG:3035, and return a WGS84 bbox.

    ``pilot`` selects the configured department; ``national`` selects
    metropolitan France excluding Corsica, then includes the configured halo
    abroad (sections 4.3 and 4.4).
    """
    if area == "pilot":
        where = f"departement = {_sql_text(department)}"
    elif area == "national":
        where = "length(departement) <= 2 AND departement NOT IN ('2A', '2B')"
    else:
        raise ValueError(f"unsupported area {area!r}; expected 'pilot' or 'national'")
    if halo_km <= 0:
        raise ValueError("halo_km must be positive")

    connection.execute("LOAD spatial")
    contours = _sql_path(contours_path)
    row = connection.execute(
        f"""
        WITH communes AS (
            SELECT ST_MakeValid(geom) AS geom
            FROM ST_Read('{contours}')
            WHERE {where}
        ),
        dissolved AS (
            SELECT ST_Union_Agg(geom) AS geom
            FROM communes
        ),
        buffered AS (
            SELECT ST_Buffer(
                ST_Transform(geom, 'EPSG:4326', 'EPSG:3035', true),
                ?
            ) AS geom
            FROM dissolved
            WHERE geom IS NOT NULL
        ),
        wgs84 AS (
            SELECT geom,
                   ST_Envelope(
                       ST_Transform(geom, 'EPSG:3035', 'EPSG:4326', true)
                   ) AS bbox
            FROM buffered
        )
        SELECT ST_AsWKB(geom),
               ST_XMin(bbox), ST_YMin(bbox), ST_XMax(bbox), ST_YMax(bbox)
        FROM wgs84
        """,
        [halo_km * 1000],
    ).fetchone()
    if row is None or row[0] is None:
        raise ValueError(f"no commune contours found for area {area!r}")
    return AreaGeometry(bytes(row[0]), *(float(value) for value in row[1:]))


def write_area_cache(
    connection: duckdb.DuckDBPyConnection,
    path: str | Path,
    area: AreaGeometry,
) -> None:
    """Atomically cache area WKB and WGS84 read bounds as Parquet."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp.parquet")
    connection.register(
        "_area_cache",
        pa.table(
            {
                "geometry_wkb": pa.array([area.geometry_wkb], type=pa.binary()),
                "west": [area.west],
                "south": [area.south],
                "east": [area.east],
                "north": [area.north],
            }
        ),
    )
    try:
        write_parquet(connection, "SELECT * FROM _area_cache", temporary)
    finally:
        connection.unregister("_area_cache")
    temporary.replace(destination)


def read_area_cache(
    connection: duckdb.DuckDBPyConnection, path: str | Path
) -> AreaGeometry:
    """Load cached area WKB and bounds using the shared Parquet reader."""
    row = read_parquet(connection, path).fetchone()
    if row is None:
        raise ValueError(f"area cache is empty: {path}")
    return AreaGeometry(
        bytes(row[0]),
        float(row[1]),
        float(row[2]),
        float(row[3]),
        float(row[4]),
    )
