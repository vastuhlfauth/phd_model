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
    "_stages/nodes_in_bbox.parquet",
    "_stages/ways_candidates.parquet",
    "_stages/nodes_outside_bbox.parquet",
    "_stages/way_nodes_candidates.parquet",
    "_stages/control_nodes_candidates.parquet",
    "ways.parquet",
    "nodes.parquet",
)

_EXTRACTION_COLUMNS = {
    "_stages/nodes_in_bbox.parquet": {"node_id", "tags", "lat", "lon"},
    "_stages/ways_candidates.parquet": {"way_id", "tags", "refs"},
    "_stages/nodes_outside_bbox.parquet": {"node_id", "tags", "lat", "lon"},
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


def _prepare_area_polygon(
    connection: duckdb.DuckDBPyConnection,
    area: AreaGeometry,
    tolerance_m: float,
) -> None:
    """Cache one topology-preserving simplified area polygon in EPSG:3035."""
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE _osm_area AS
        SELECT ST_SimplifyPreserveTopology(
            ST_GeomFromWKB(from_hex(?)), ?
        ) AS geom
        """,
        [area.geometry_wkb.hex(), tolerance_m],
    )


def _build_ways_candidates_query(
    ways_source: str, config: NetworkConfig
) -> str:
    return f"""
        SELECT w.id AS way_id,
               {_tag_map_sql('w.tags', config.kept_tags)} AS tags,
               w.refs
        FROM {ways_source} w
        CROSS JOIN UNNEST(w.refs) AS ref(node_id)
        JOIN _osm_area_node_ids area_nodes USING (node_id)
        WHERE w.kind = 'way'
          AND (w.tags['highway'] IS NOT NULL
               OR w.tags['railway'] = 'platform'
               OR w.tags['public_transport'] = 'platform')
        QUALIFY row_number() OVER (
            PARTITION BY w.id ORDER BY ref.node_id
        ) = 1
    """


def _build_nodes_outside_bbox_query(
    nodes_source: str, ways_path: str, nodes_bbox_path: str
) -> str:
    return f"""
        WITH needed AS (
            SELECT DISTINCT unnest(refs) AS node_id
            FROM read_parquet('{ways_path}')
        )
        SELECT osm_node.id AS node_id, osm_node.tags,
               osm_node.lat, osm_node.lon
        FROM {nodes_source} osm_node
        JOIN needed ON needed.node_id = osm_node.id
        LEFT JOIN read_parquet('{nodes_bbox_path}') bbox_nodes
          ON bbox_nodes.node_id = osm_node.id
        WHERE osm_node.kind = 'node'
          AND bbox_nodes.node_id IS NULL
    """


def _build_kept_nodes_query(
    ways_path: str,
    nodes_bbox_path: str,
    nodes_outside_path: str,
    control_highways: tuple[str, ...],
) -> str:
    return f"""
        WITH way_node_ids AS (
            SELECT DISTINCT unnest(refs) AS node_id
            FROM read_parquet('{ways_path}')
        ),
        nodes_to_keep AS (
            SELECT n.node_id, n.tags, n.lat, n.lon
            FROM read_parquet('{nodes_bbox_path}') n
            JOIN way_node_ids USING (node_id)
            UNION ALL
            SELECT c.node_id, c.tags, c.lat, c.lon
            FROM read_parquet('{nodes_bbox_path}') c
            JOIN _osm_area_node_ids area_nodes USING (node_id)
            WHERE list_contains(
                {_sql_string_list(control_highways)}, c.tags['highway']
            )
            UNION ALL
            SELECT n.node_id, n.tags, n.lat, n.lon
            FROM read_parquet('{nodes_outside_path}') n
            JOIN way_node_ids USING (node_id)
        )
        SELECT node_id, any_value(tags) AS tags,
               any_value(lat) AS lat, any_value(lon) AS lon
        FROM nodes_to_keep
        GROUP BY node_id
    """


def _extraction_signature(
    pbf: Path, area: AreaGeometry, config: NetworkConfig
) -> str:
    payload = {
        "version": 3,
        "pbf": _file_signature(pbf),
        "area_wkb": hashlib.sha256(area.geometry_wkb).hexdigest(),
        "area_bounds": [area.west, area.south, area.east, area.north],
        "config": config.model_dump(
            mode="json", exclude={"car_speed", "bike_speed_table"}
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def extract_osm_pbf(
    connection: duckdb.DuckDBPyConnection,
    pbf_path: str | Path,
    cache_directory: str | Path,
    area: AreaGeometry,
    *,
    config: NetworkConfig,
) -> ExtractionSummary:
    """Read bbox nodes, matching ways, then their out-of-bounds nodes.

    A way is retained when it references a node covered by the simplified
    buffered area; all its nodes and in-area control nodes remain in the
    cache. Stages are resumable Parquet files under
    ``data/interim/osm/{state}/{area}``.
    """
    started = time.perf_counter()
    pbf = Path(pbf_path)
    if not pbf.is_file():
        raise FileNotFoundError(pbf)
    cache = Path(cache_directory)
    stages = cache / "_stages"
    stages.mkdir(parents=True, exist_ok=True)
    connection.execute("LOAD spatial")

    signature = _extraction_signature(pbf, area, config)
    _invalidate_stale_stages(connection, cache, signature)

    pbf_sql = _sql_path(pbf)
    _prepare_area_polygon(
        connection, area, config.area_simplify_tolerance_m
    )
    nodes_in_bbox = stages / "nodes_in_bbox.parquet"
    ways_candidates = stages / "ways_candidates.parquet"
    nodes_outside_bbox = stages / "nodes_outside_bbox.parquet"
    kept_ways = cache / "ways.parquet"
    kept_nodes = cache / "nodes.parquet"
    _stage_checked(
        connection,
        nodes_in_bbox,
        f"""
        SELECT id AS node_id, tags, lat, lon
        FROM ST_ReadOSM('{pbf_sql}')
        WHERE kind = 'node'
          AND lon BETWEEN {area.west!r} AND {area.east!r}
          AND lat BETWEEN {area.south!r} AND {area.north!r}
        """,
        _EXTRACTION_COLUMNS["_stages/nodes_in_bbox.parquet"],
    )
    nodes_bbox_path = _sql_path(nodes_in_bbox)
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_area_node_ids AS
        SELECT n.node_id
        FROM read_parquet('{nodes_bbox_path}') n
        CROSS JOIN _osm_area a
        WHERE ST_Covers(
            a.geom,
            ST_Transform(
                ST_Point(n.lon, n.lat),
                'EPSG:4326', 'EPSG:3035', true
            )
        )
    """)
    _stage_checked(
        connection,
        ways_candidates,
        _build_ways_candidates_query(
            f"ST_ReadOSM('{pbf_sql}')", config
        ),
        _EXTRACTION_COLUMNS["_stages/ways_candidates.parquet"],
    )

    ways_path = _sql_path(ways_candidates)
    _stage_checked(
        connection,
        kept_ways,
        f"SELECT way_id, tags, refs FROM read_parquet('{ways_path}')",
        _EXTRACTION_COLUMNS["ways.parquet"],
    )
    kept_ways_path = _sql_path(kept_ways)
    nodes_outside_path = _sql_path(nodes_outside_bbox)
    _stage_checked(
        connection,
        nodes_outside_bbox,
        _build_nodes_outside_bbox_query(
            f"ST_ReadOSM('{pbf_sql}')",
            kept_ways_path,
            nodes_bbox_path,
        ),
        _EXTRACTION_COLUMNS["_stages/nodes_outside_bbox.parquet"],
    )
    _stage_checked(
        connection,
        kept_nodes,
        _build_kept_nodes_query(
            kept_ways_path,
            nodes_bbox_path,
            nodes_outside_path,
            config.control_highways,
        ),
        _EXTRACTION_COLUMNS["nodes.parquet"],
    )
    connection.execute("DROP TABLE _osm_area")
    connection.execute("DROP TABLE _osm_area_node_ids")
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
