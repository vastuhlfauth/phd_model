"""Directed OSM edge construction and access rules for section 8.1."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
from common.duckdb_io import read_parquet, write_parquet

from mobgrid.osm.bike_infra import bike_infrastructure_sql, maxspeed_sql
from mobgrid.osm.config import Mode, NetworkConfig

logger = logging.getLogger(__name__)

EDGE_COLUMNS = {
    "way_id",
    "from_node_id",
    "to_node_id",
    "is_forward",
    "mode",
    "node_ids",
    "length_m",
    "highway",
    "maxspeed_kmh",
    "motorroad",
    "lanes",
    "car_access",
    "bike_access",
    "foot_access",
    "bike_infra",
    "surface",
    "smoothness",
    "busway",
    "lanes_bus",
    "lanes_psv",
    "signal_count",
    "junction_count",
    "cell_1km_id",
    "tile_id",
    "geometry_wkb",
}
NODE_COLUMNS = {"node_id", "x", "y", "tags", "graph_node"}


@dataclass(frozen=True)
class EdgeBuildSummary:
    """Persistent edge-build outputs and counts."""

    edges_path: str
    nodes_path: str
    edge_count: int
    node_count: int


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def access_sql(mode: Mode, config: NetworkConfig) -> str:
    """Build the DuckDB expression for the configured OSM access hierarchy."""
    rule = config.access_rules[mode]
    access = "coalesce(" + ", ".join(
        f"nullif(way_tags[{_sql_text(key)}], '')" for key in rule.precedence
    ) + ")"
    denied = ", ".join(_sql_text(value.casefold()) for value in rule.denied)
    excluded = ", ".join(_sql_text(value) for value in rule.excluded_highways)
    included = ", ".join(_sql_text(value) for value in rule.included_highways)
    hard_exclusion = "FALSE"
    if mode in ("bike", "foot"):
        motorway_values = ", ".join(
            _sql_text(value) for value in ("motorway", "motorway_link")
        )
        hard_exclusion = (
            f"(lower(way_tags['highway']) IN ({motorway_values}) "
            "OR (lower(way_tags['highway']) = 'trunk' "
            "AND lower(way_tags['motorroad']) IN ('yes', 'true', '1')))"
        )
    platform_default = (
        "WHEN way_tags['highway'] IS NULL "
        "THEN way_tags['railway'] = 'platform' "
        "OR way_tags['public_transport'] = 'platform'"
        if mode == "foot"
        else "WHEN way_tags['highway'] IS NULL THEN FALSE"
    )
    sidewalk_access = ""
    if mode == "foot":
        sidewalk_values = ", ".join(
            _sql_text(value.casefold()) for value in rule.sidewalk_values
        )
        sidewalk_access = (
            f"WHEN lower(way_tags['sidewalk']) IN ({sidewalk_values}) THEN TRUE "
        )
    included_access = (
        f"WHEN lower(way_tags['highway']) IN ({included}) THEN TRUE "
        if included
        else ""
    )
    return (
        "CASE "
        f"WHEN {hard_exclusion} THEN FALSE "
        f"WHEN lower({access}) IN ({denied}) THEN FALSE "
        f"WHEN {access} IS NOT NULL THEN TRUE "
        f"{included_access}{sidewalk_access}"
        f"{platform_default} "
        f"WHEN lower(way_tags['highway']) IN ({excluded}) THEN FALSE "
        f"ELSE {'TRUE' if rule.default_allowed else 'FALSE'} END"
    )


def _direction_result(value: str, forward: bool, config: NetworkConfig) -> str:
    yes = ", ".join(_sql_text(item) for item in config.oneway_yes)
    reverse = ", ".join(_sql_text(item) for item in config.oneway_reverse)
    return (
        f"CASE WHEN lower({value}) IN ({yes}) THEN "
        f"{'TRUE' if forward else 'FALSE'} "
        f"WHEN lower({value}) IN ({reverse}) THEN "
        f"{'FALSE' if forward else 'TRUE'} ELSE TRUE END"
    )


def direction_sql(mode: Mode, config: NetworkConfig) -> str:
    """Build the per-way direction predicate for the current edge direction."""
    if mode == "foot":
        return "TRUE"
    is_forward = "is_forward"
    general = (
        "coalesce(nullif(way_tags['oneway'], ''), "
        "CASE WHEN way_tags['highway'] = 'motorway' "
        "OR way_tags['junction'] = 'roundabout' THEN 'yes' END)"
    )
    general_forward = _direction_result(general, True, config)
    general_reverse = _direction_result(general, False, config)
    if mode == "car":
        return (
            f"CASE WHEN {is_forward} THEN {general_forward} "
            f"ELSE {general_reverse} END"
        )

    cycleway_oneway_tags = (
        "way_tags['cycleway:oneway']",
        "way_tags['cycleway:both:oneway']",
        "way_tags['cycleway:left:oneway']",
        "way_tags['cycleway:right:oneway']",
    )
    bike_oneway = "nullif(way_tags['oneway:bicycle'], '')"
    bike_specific_forward = _direction_result(bike_oneway, True, config)
    bike_specific_reverse = _direction_result(bike_oneway, False, config)
    no_values = ", ".join(_sql_text(item) for item in config.oneway_no)
    reverse_values = ", ".join(
        _sql_text(item) for item in config.oneway_reverse
    )
    cycleway_two_way = " OR ".join(
        f"lower({tag}) IN ({no_values})" for tag in cycleway_oneway_tags
    )
    cycleway_reverse = " OR ".join(
        f"lower({tag}) IN ({reverse_values})" for tag in cycleway_oneway_tags
    )
    opposite_tags = [
        "way_tags['cycleway']",
        "way_tags['cycleway:both']",
        "way_tags['cycleway:left']",
        "way_tags['cycleway:right']",
    ]
    opposite = " OR ".join(
        f"starts_with(lower(coalesce({tag}, '')), 'opposite')"
        for tag in opposite_tags
    )
    return f"""
        CASE
          WHEN {bike_oneway} IS NOT NULL THEN
            CASE WHEN {is_forward} THEN {bike_specific_forward}
                 ELSE {bike_specific_reverse} END
          WHEN {opposite} THEN TRUE
          WHEN {cycleway_two_way} THEN TRUE
          WHEN NOT {is_forward} AND ({cycleway_reverse}) THEN TRUE
          WHEN {is_forward} THEN {general_forward}
          ELSE {general_reverse}
        END
    """


def _write_parquet_atomic(
    connection: duckdb.DuckDBPyConnection, query: str, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp.parquet")
    write_parquet(connection, query, temporary)
    temporary.replace(destination)


def _input_signature(
    ways_path: str | Path, nodes_path: str | Path, config: NetworkConfig
) -> str:
    inputs = {}
    for candidate in (Path(ways_path), Path(nodes_path)):
        stat = candidate.stat()
        inputs[str(candidate.resolve())] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    return hashlib.sha256(
        json.dumps(
            {"version": 1, "inputs": inputs, "config": config.model_dump(mode="json")},
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _cache_schema(
    connection: duckdb.DuckDBPyConnection, path: Path
) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_path(path)}')"
        ).fetchall()
    }


def _build_points_sql(ways_path: str, nodes_path: str) -> str:
    return f"""
        CREATE OR REPLACE TEMP TABLE _osm_way_points AS
        SELECT w.way_id, w.tags AS way_tags, ref.node_sequence,
               ref.node_id, n.tags AS node_tags, n.lat, n.lon,
               ST_Transform(
                   ST_Point(n.lon, n.lat),
                   'EPSG:4326', 'EPSG:3035', true
               ) AS point
        FROM read_parquet('{ways_path}') w
        CROSS JOIN UNNEST(w.refs) WITH ORDINALITY
            AS ref(node_id, node_sequence)
        JOIN read_parquet('{nodes_path}') n USING (node_id)
    """


def _build_segments_sql() -> str:
    return """
        CREATE OR REPLACE TEMP TABLE _osm_way_segments AS
        WITH graph_way_nodes AS (
            SELECT p.*
            FROM _osm_way_points p
            JOIN _osm_graph_node_ids g USING (node_id)
        ),
        ranges AS (
            SELECT way_id, way_tags, node_id AS from_node_id,
                   node_sequence AS from_sequence,
                   lead(node_id) OVER (
                       PARTITION BY way_id ORDER BY node_sequence
                   ) AS to_node_id,
                   lead(node_sequence) OVER (
                       PARTITION BY way_id ORDER BY node_sequence
                   ) AS to_sequence
            FROM graph_way_nodes
        )
        SELECT r.way_id, r.way_tags, r.from_node_id, r.to_node_id,
               r.from_sequence, r.to_sequence,
               list(p.node_id ORDER BY p.node_sequence) AS node_ids,
               ST_MakeLine(list(p.point ORDER BY p.node_sequence)) AS geom
        FROM ranges r
        JOIN _osm_way_points p
          ON p.way_id = r.way_id
         AND p.node_sequence BETWEEN r.from_sequence AND r.to_sequence
        WHERE r.to_node_id IS NOT NULL
        GROUP BY r.way_id, r.way_tags, r.from_node_id, r.to_node_id,
                 r.from_sequence, r.to_sequence
    """


def _build_edges_query(config: NetworkConfig, nodes_path: str) -> str:
    accesses = {
        mode: access_sql(mode, config) for mode in ("car", "bike", "foot")
    }
    directions = {
        mode: direction_sql(mode, config) for mode in ("car", "bike", "foot")
    }
    mode_values = ", ".join(f"('{mode}')" for mode in ("car", "bike", "foot"))
    allowed_by_mode = " OR ".join(
        f"(mode = '{mode}' AND {accesses[mode]} AND {directions[mode]})"
        for mode in ("car", "bike", "foot")
    )
    bike_class = bike_infrastructure_sql(
        "way_tags", "is_forward", "bike_access", config
    )
    maxspeed = maxspeed_sql("way_tags", config)
    tile_size = config.tile_size_m
    return f"""
        WITH directions AS (
            SELECT way_id, way_tags, from_node_id, to_node_id,
                   node_ids, geom, true AS is_forward
            FROM _osm_way_segments
            UNION ALL
            SELECT way_id, way_tags, to_node_id AS from_node_id,
                   from_node_id AS to_node_id,
                   list_reverse(node_ids) AS node_ids,
                   ST_Reverse(geom) AS geom, false AS is_forward
            FROM _osm_way_segments
        ),
        attributes AS (
            SELECT d.*,
                   {accesses["car"]} AS car_access,
                   {accesses["bike"]} AS bike_access,
                   {accesses["foot"]} AS foot_access,
                   ST_Length(d.geom) AS length_m,
                   {maxspeed} AS maxspeed_kmh,
                   coalesce(
                       lower(d.way_tags['motorroad']) IN ('yes', 'true', '1'),
                       false
                   )
                       AS motorroad,
                   d.way_tags['highway'] AS highway,
                   d.way_tags['lanes'] AS lanes,
                   d.way_tags['surface'] AS surface,
                   d.way_tags['smoothness'] AS smoothness,
                   d.way_tags['busway'] AS busway,
                   d.way_tags['lanes:bus'] AS lanes_bus,
                   d.way_tags['lanes:psv'] AS lanes_psv,
                   CASE WHEN lower(n.tags['highway']) = 'traffic_signals'
                        THEN 1::TINYINT ELSE 0::TINYINT END AS signal_count,
                   CASE WHEN lower(n.tags['highway']) IN
                       ('stop', 'give_way', 'crossing', 'mini_roundabout')
                        THEN 1::TINYINT ELSE 0::TINYINT END AS junction_count,
                   floor(ST_Y(ST_Centroid(d.geom)) / 1000)::BIGINT
                       * 100000
                     + floor(ST_X(ST_Centroid(d.geom)) / 1000)::BIGINT
                       AS cell_1km_id,
                   floor(ST_Y(ST_Centroid(d.geom)) / {tile_size})::BIGINT
                       * 100000
                     + floor(ST_X(ST_Centroid(d.geom)) / {tile_size})::BIGINT
                       AS tile_id
            FROM directions d
            JOIN read_parquet('{nodes_path}') n
              ON n.node_id = d.to_node_id
        ),
        per_mode AS (
            SELECT attributes.*, mode
            FROM attributes
            CROSS JOIN (VALUES {mode_values}) AS modes(mode)
        )
        SELECT way_id, from_node_id, to_node_id, is_forward, mode, node_ids,
               length_m, highway, maxspeed_kmh, motorroad, lanes,
               car_access, bike_access, foot_access,
               {bike_class} AS bike_infra,
               surface, smoothness, busway, lanes_bus, lanes_psv,
               signal_count, junction_count, cell_1km_id, tile_id,
               ST_AsWKB(geom) AS geometry_wkb
        FROM per_mode
        WHERE {allowed_by_mode}
    """


def _build_graph_nodes(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _osm_graph_node_ids AS
        SELECT node_id
        FROM _osm_way_points
        GROUP BY node_id
        HAVING count(DISTINCT way_id) >= 2
        UNION
        SELECT p.node_id
        FROM _osm_way_points p
        JOIN (
            SELECT way_id, min(node_sequence) AS first_sequence,
                   max(node_sequence) AS last_sequence
            FROM _osm_way_points
            GROUP BY way_id
        ) ends USING (way_id)
        WHERE p.node_sequence IN (ends.first_sequence, ends.last_sequence)
    """)


def _build_nodes_query(nodes_path: str) -> str:
    return f"""
        WITH projected AS (
            SELECT node_id, tags,
                   ST_Transform(
                       ST_Point(lon, lat),
                       'EPSG:4326', 'EPSG:3035', true
                   ) AS point
            FROM read_parquet('{nodes_path}')
        )
        SELECT p.node_id, ST_X(p.point) AS x, ST_Y(p.point) AS y,
               p.tags, g.node_id IS NOT NULL AS graph_node
        FROM projected p
        LEFT JOIN _osm_graph_node_ids g USING (node_id)
    """


def _write_metadata(path: Path, signature: str) -> None:
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps({"signature": signature}, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _summary_from_files(
    connection: duckdb.DuckDBPyConnection,
    edges_path: Path,
    nodes_path: Path,
) -> EdgeBuildSummary:
    edge_count = int(
        read_parquet(connection, edges_path).aggregate("count(*)").fetchone()[0]
    )
    node_count = int(
        read_parquet(connection, nodes_path).aggregate("count(*)").fetchone()[0]
    )
    return EdgeBuildSummary(
        str(edges_path), str(nodes_path), edge_count, node_count
    )


def build_directed_edges(
    connection: duckdb.DuckDBPyConnection,
    ways_path: str | Path,
    nodes_path: str | Path,
    output_directory: str | Path,
    *,
    config: NetworkConfig,
) -> EdgeBuildSummary:
    """Split kept ways at graph nodes and write directed, mode-specific edges."""
    ways = Path(ways_path)
    nodes = Path(nodes_path)
    if not ways.is_file():
        raise FileNotFoundError(ways)
    if not nodes.is_file():
        raise FileNotFoundError(nodes)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    edges_path = output / "edges.parquet"
    output_nodes_path = output / "nodes.parquet"
    metadata_path = output / "_edges.json"
    signature = _input_signature(ways, nodes, config)
    if edges_path.is_file() and output_nodes_path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("signature") == signature
            and EDGE_COLUMNS <= _cache_schema(connection, edges_path)
            and NODE_COLUMNS <= _cache_schema(connection, output_nodes_path)
        ):
            logger.info("reusing cached directed edges in %s", output)
            return _summary_from_files(connection, edges_path, output_nodes_path)

    connection.execute("LOAD spatial")
    ways_source = _sql_path(ways)
    nodes_source = _sql_path(nodes)
    connection.execute(_build_points_sql(ways_source, nodes_source))
    _build_graph_nodes(connection)
    connection.execute(_build_segments_sql())
    _write_parquet_atomic(
        connection,
        _build_edges_query(config, nodes_source),
        edges_path,
    )
    _write_parquet_atomic(
        connection,
        _build_nodes_query(nodes_source),
        output_nodes_path,
    )
    _write_metadata(metadata_path, signature)
    summary = _summary_from_files(connection, edges_path, output_nodes_path)
    logger.info(
        "wrote %s directed mode edges and %s nodes to %s",
        summary.edge_count,
        summary.node_count,
        output,
    )
    return summary
