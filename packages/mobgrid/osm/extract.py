"""Study-area construction and resumable OSM extraction for section 8.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import pyarrow as pa
from acquire.manifest import SourceFile, load_manifest
from common.config import load_pilot_config
from common.duckdb_io import open_connection, read_parquet, write_parquet

from mobgrid.osm.config import NetworkConfig, load_network_config
from mobgrid.pt.osm_route_extraction import (
    _stage,
    configure_extraction_connection,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AreaGeometry:
    """Buffered study area in EPSG:3035 and its WGS84 reading bounds."""

    geometry_wkb: bytes
    west: float
    south: float
    east: float
    north: float


@dataclass(frozen=True)
class ExtractionSummary:
    """Counts and timings for one cached OSM extraction."""

    pbf_path: str
    output_directory: str
    elapsed_seconds: float
    pbf_bytes: int
    way_count: int
    node_count: int
    warnings: tuple[str, ...] = ()


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


def _file_signature(path: str | Path) -> dict[str, int | str]:
    candidate = Path(path)
    stat = candidate.stat()
    return {
        "path": str(candidate.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary.replace(path)


def _area_signature(
    contours_path: str | Path,
    area: str,
    department: str,
    halo_km: float,
) -> str:
    payload = {
        "version": 1,
        "contours": _file_signature(contours_path),
        "area": area,
        "department": department,
        "halo_km": halo_km,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _load_or_build_area(
    connection: duckdb.DuckDBPyConnection,
    cache_directory: Path,
    contours_path: str | Path,
    *,
    area_name: str,
    department: str,
    halo_km: float,
) -> AreaGeometry:
    area_path = cache_directory / "area.parquet"
    metadata_path = cache_directory / "area.json"
    signature = _area_signature(contours_path, area_name, department, halo_km)
    if area_path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        columns = {
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{_sql_path(area_path)}')"
            ).fetchall()
        }
        if metadata.get("signature") == signature and {
            "geometry_wkb", "west", "south", "east", "north"
        } <= columns:
            logger.info("reusing cached study area %s", area_path)
            return read_area_cache(connection, area_path)
        logger.info("study-area cache is stale; rebuilding %s", area_path)
        area_path.unlink()
    study_area = build_area(
        connection,
        contours_path,
        area=area_name,
        department=department,
        halo_km=halo_km,
    )
    write_area_cache(connection, area_path, study_area)
    _write_json(metadata_path, {"signature": signature})
    return study_area


def _sql_string_list(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(_sql_text(value) for value in values) + "]"


def _tag_map_sql(tag_expression: str, kept_tags: tuple[str, ...]) -> str:
    return (
        "map_from_entries(list_filter(map_entries("
        f"{tag_expression}), entry -> list_contains("
        f"{_sql_string_list(kept_tags)}, entry.key)))"
    )


_EXTRACTION_FILES = (
    "_stages/ways_candidates.parquet",
    "_stages/way_nodes_candidates.parquet",
    "_stages/control_nodes_candidates.parquet",
    "ways.parquet",
    "nodes.parquet",
)

_EXTRACTION_COLUMNS = {
    "_stages/ways_candidates.parquet": {"way_id", "tags", "refs"},
    "_stages/way_nodes_candidates.parquet": {"node_id", "tags", "lat", "lon"},
    "_stages/control_nodes_candidates.parquet": {"node_id", "tags", "lat", "lon"},
    "ways.parquet": {"way_id", "tags", "refs"},
    "nodes.parquet": {"node_id", "tags", "lat", "lon"},
}


def _invalidate_stale_stages(
    connection: duckdb.DuckDBPyConnection,
    cache_directory: Path,
    signature: str,
) -> None:
    metadata_path = cache_directory / "extraction.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("signature") == signature:
            return
        logger.info("OSM extraction inputs changed; invalidating cached stages")
    for relative_path in _EXTRACTION_FILES:
        path = cache_directory / relative_path
        if not path.is_file():
            continue
        columns = {
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{_sql_path(path)}')"
            ).fetchall()
        }
        if not _EXTRACTION_COLUMNS[relative_path] <= columns:
            logger.info("OSM stage schema is stale; rebuilding %s", path)
        path.unlink()
    _write_json(metadata_path, {"signature": signature})


def _stage_checked(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    query: str,
    required_columns: set[str],
) -> None:
    if path.is_file():
        columns = {
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{_sql_path(path)}')"
            ).fetchall()
        }
        if required_columns <= columns:
            logger.info("reusing OSM stage %s", path.name)
            return
        logger.info("OSM stage schema is stale; rebuilding %s", path)
        path.unlink()
    _stage(connection, path, query)


def extract_osm_pbf(
    connection: duckdb.DuckDBPyConnection,
    pbf_path: str | Path,
    cache_directory: str | Path,
    area: AreaGeometry,
    *,
    config: NetworkConfig,
) -> ExtractionSummary:
    """Read ways, their nodes, and traffic-control nodes in three PBF passes.

    A way is retained when any referenced node lies in the buffered area;
    all references for each retained way remain in the cache. Stages are
    resumable Parquet files under ``data/interim/osm/{state}/{area}``.
    """
    started = time.perf_counter()
    pbf = Path(pbf_path)
    if not pbf.is_file():
        raise FileNotFoundError(pbf)
    cache = Path(cache_directory)
    stages = cache / "_stages"
    stages.mkdir(parents=True, exist_ok=True)
    connection.execute("LOAD spatial")

    signature_payload = {
        "version": 2,
        "pbf": _file_signature(pbf),
        "area_wkb": hashlib.sha256(area.geometry_wkb).hexdigest(),
        "area_bounds": [area.west, area.south, area.east, area.north],
        "config": config.model_dump(mode="json"),
    }
    signature = hashlib.sha256(
        json.dumps(signature_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    _invalidate_stale_stages(connection, cache, signature)

    pbf_sql = _sql_path(pbf)
    ways_candidates = stages / "ways_candidates.parquet"
    way_nodes_candidates = stages / "way_nodes_candidates.parquet"
    control_nodes_candidates = stages / "control_nodes_candidates.parquet"
    kept_ways = cache / "ways.parquet"
    kept_nodes = cache / "nodes.parquet"
    _stage_checked(
        connection,
        ways_candidates,
        f"""
        SELECT id AS way_id, {_tag_map_sql('tags', config.kept_tags)} AS tags,
               refs
        FROM ST_ReadOSM('{pbf_sql}')
        WHERE kind = 'way'
          AND (tags['highway'] IS NOT NULL
               OR tags['railway'] = 'platform'
               OR tags['public_transport'] = 'platform')
        """,
        _EXTRACTION_COLUMNS["_stages/ways_candidates.parquet"],
    )
    ways_path = _sql_path(ways_candidates)
    _stage_checked(
        connection,
        way_nodes_candidates,
        f"""
        WITH needed AS (
            SELECT DISTINCT unnest(refs) AS node_id
            FROM read_parquet('{ways_path}')
        )
        SELECT id AS node_id, tags, lat, lon
        FROM ST_ReadOSM('{pbf_sql}')
        WHERE kind = 'node'
          AND id IN (SELECT node_id FROM needed)
        """,
        _EXTRACTION_COLUMNS["_stages/way_nodes_candidates.parquet"],
    )
    _stage_checked(
        connection,
        control_nodes_candidates,
        f"""
        SELECT id AS node_id, tags, lat, lon
        FROM ST_ReadOSM('{pbf_sql}')
        WHERE kind = 'node'
          AND tags['highway'] IN (
              {", ".join(_sql_text(v) for v in config.control_highways)}
          )
          AND lon BETWEEN {area.west!r} AND {area.east!r}
          AND lat BETWEEN {area.south!r} AND {area.north!r}
        """,
        _EXTRACTION_COLUMNS["_stages/control_nodes_candidates.parquet"],
    )

    area_literal = "from_hex('" + area.geometry_wkb.hex() + "')"
    nodes_path = _sql_path(way_nodes_candidates)
    control_path = _sql_path(control_nodes_candidates)
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _osm_area AS
        SELECT ST_GeomFromWKB({area_literal}) AS geom
        """
    )
    _stage_checked(
        connection,
        kept_ways,
        f"""
        SELECT w.way_id, w.tags, w.refs
        FROM read_parquet('{ways_path}') w
        WHERE EXISTS (
            SELECT 1
            FROM UNNEST(w.refs) AS ref(node_id)
            JOIN read_parquet('{nodes_path}') n USING (node_id)
            CROSS JOIN _osm_area a
            WHERE n.lon BETWEEN {area.west!r} AND {area.east!r}
              AND n.lat BETWEEN {area.south!r} AND {area.north!r}
              AND ST_Covers(
                a.geom,
                ST_Transform(
                    ST_Point(n.lon, n.lat),
                    'EPSG:4326', 'EPSG:3035', true
                )
            )
        )
        """,
        _EXTRACTION_COLUMNS["ways.parquet"],
    )
    kept_ways_path = _sql_path(kept_ways)
    _stage_checked(
        connection,
        kept_nodes,
        f"""
        WITH way_node_ids AS (
            SELECT DISTINCT unnest(refs) AS node_id
            FROM read_parquet('{kept_ways_path}')
        ),
        nodes_to_keep AS (
            SELECT n.node_id, n.tags, n.lat, n.lon
            FROM read_parquet('{nodes_path}') n
            JOIN way_node_ids USING (node_id)
            UNION ALL
            SELECT c.node_id, c.tags, c.lat, c.lon
            FROM read_parquet('{control_path}') c
            CROSS JOIN _osm_area a
            WHERE c.lon BETWEEN {area.west!r} AND {area.east!r}
              AND c.lat BETWEEN {area.south!r} AND {area.north!r}
              AND ST_Covers(
                a.geom,
                ST_Transform(
                    ST_Point(c.lon, c.lat),
                    'EPSG:4326', 'EPSG:3035', true
                )
            )
        )
        SELECT node_id, any_value(tags) AS tags,
               any_value(lat) AS lat, any_value(lon) AS lon
        FROM nodes_to_keep
        GROUP BY node_id
        """,
        _EXTRACTION_COLUMNS["nodes.parquet"],
    )
    connection.execute("DROP TABLE _osm_area")
    way_count = int(
        connection.execute(
            f"SELECT count(*) FROM read_parquet('{_sql_path(kept_ways)}')"
        ).fetchone()[0]
    )
    node_count = int(
        connection.execute(
            f"SELECT count(*) FROM read_parquet('{_sql_path(kept_nodes)}')"
        ).fetchone()[0]
    )
    summary = ExtractionSummary(
        str(pbf),
        str(cache),
        time.perf_counter() - started,
        pbf.stat().st_size,
        way_count,
        node_count,
    )
    _write_json(
        cache / "_SUCCESS.json",
        {
            "pbf_path": str(pbf.resolve()),
            "pbf_bytes": summary.pbf_bytes,
            "way_count": way_count,
            "node_count": node_count,
            "elapsed_seconds": summary.elapsed_seconds,
        },
    )
    return summary


def _source_path(manifest: list[SourceFile], source_id: str) -> Path:
    """Resolve a manifest id relative to the project root."""
    for source in manifest:
        if source.id == source_id:
            path = Path(source.local_path)
            if not path.is_file():
                raise FileNotFoundError(path)
            return path
    raise KeyError(f"source id {source_id!r} is not in the acquisition manifest")


def _configure_logging(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(path, encoding="utf-8"),
        ],
    )


def _write_extraction_summary(summary: ExtractionSummary, path: Path) -> None:
    text = f"""# OSM extraction summary

- Input: `{summary.pbf_path}`
- Input size: {summary.pbf_bytes:,} bytes
- Output: `{summary.output_directory}`
- Elapsed: {summary.elapsed_seconds:.1f} seconds
- Kept ways: {summary.way_count:,}
- Nodes, including traffic-control points: {summary.node_count:,}
- Warnings: {", ".join(summary.warnings) if summary.warnings else "none"}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact_path(task: str, suffix: str) -> Path:
    return Path("logs") / f"{date.today().isoformat()}_{task}{suffix}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.extract")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument("--config", type=Path, default=Path("config/network.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument("--manifest", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Extract one configured state/area without running a national job."""
    args = _parser().parse_args(argv)
    config = load_network_config(args.config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in config.states:
        raise ValueError(
            f"unsupported state {args.state}; configured: {sorted(config.states)}"
        )
    task = f"osm_extract_{args.state}_{args.area}"
    _configure_logging(args.log or _artifact_path(task, ".log"))
    sources = load_manifest(args.manifest)
    pbf_path = _source_path(sources, config.states[args.state])
    contours_path = _source_path(sources, config.contour_source_id)
    cache = Path(pilot.paths["interim"]) / "osm" / str(args.state) / args.area
    cache.mkdir(parents=True, exist_ok=True)
    connection = open_connection()
    configure_extraction_connection(connection, pilot.paths["interim"])
    area = _load_or_build_area(
        connection,
        cache,
        contours_path,
        area_name=args.area,
        department=pilot.department,
        halo_km=pilot.halo_km,
    )
    summary = extract_osm_pbf(
        connection,
        pbf_path,
        cache,
        area,
        config=config,
    )
    summary_path = args.summary or _artifact_path(task, "_summary.md")
    _write_extraction_summary(summary, summary_path)
    logger.info(
        "extracted %s ways and %s nodes in %.1f seconds",
        summary.way_count,
        summary.node_count,
        summary.elapsed_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
