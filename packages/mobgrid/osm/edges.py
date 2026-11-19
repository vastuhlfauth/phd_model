"""Directed OSM edge construction and access rules for section 8.1."""

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
import numpy as np
import pyarrow as pa
from common.config import load_pilot_config
from common.duckdb_io import read_parquet, write_parquet
from common.grid import cell_id
from numba import njit

from mobgrid.osm.bike_infra import bike_infrastructure_sql, maxspeed_sql
from mobgrid.osm.config import Mode, NetworkConfig, load_network_config
from mobgrid.pt.osm_route_extraction import configure_extraction_connection

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


@dataclass(frozen=True)
class ConnectivitySummary:
    """Largest strongly connected component measures for one mode."""

    mode: str
    node_count: int
    edge_count: int
    largest_component_nodes: int
    largest_component_length_share: float | None


@njit(cache=True)
def _strongly_connected_components(
    indptr: np.ndarray,
    indices: np.ndarray,
    reverse_indptr: np.ndarray,
    reverse_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Iterative Kosaraju SCC labels over CSR arrays."""
    node_count = len(indptr) - 1
    visited = np.zeros(node_count, dtype=np.bool_)
    order = np.empty(node_count, dtype=np.int64)
    stack_nodes = np.empty(node_count, dtype=np.int64)
    stack_positions = np.empty(node_count, dtype=np.int64)
    order_count = 0

    for start in range(node_count):
        if visited[start]:
            continue
        top = 0
        stack_nodes[0] = start
        stack_positions[0] = indptr[start]
        visited[start] = True
        while top >= 0:
            node = stack_nodes[top]
            position = stack_positions[top]
            if position < indptr[node + 1]:
                neighbour = indices[position]
                stack_positions[top] = position + 1
                if not visited[neighbour]:
                    visited[neighbour] = True
                    top += 1
                    stack_nodes[top] = neighbour
                    stack_positions[top] = indptr[neighbour]
            else:
                order[order_count] = node
                order_count += 1
                top -= 1

    labels = np.full(node_count, -1, dtype=np.int64)
    component_sizes = np.zeros(node_count, dtype=np.int64)
    component_count = 0
    for order_position in range(node_count - 1, -1, -1):
        start = order[order_position]
        if labels[start] >= 0:
            continue
        top = 0
        stack_nodes[0] = start
        labels[start] = component_count
        size = 0
        while top >= 0:
            node = stack_nodes[top]
            top -= 1
            size += 1
            for position in range(reverse_indptr[node], reverse_indptr[node + 1]):
                neighbour = reverse_indices[position]
                if labels[neighbour] < 0:
                    labels[neighbour] = component_count
                    top += 1
                    stack_nodes[top] = neighbour
        component_sizes[component_count] = size
        component_count += 1
    return labels, component_sizes, component_count


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
                   tiles.tile_id
            FROM directions d
            JOIN read_parquet('{nodes_path}') n
              ON n.node_id = d.to_node_id
            JOIN _osm_segment_tiles tiles
              ON tiles.northing_m = floor(
                    ST_Y(ST_Centroid(d.geom)) / {tile_size}
                 ) * {tile_size}
             AND tiles.easting_m = floor(
                    ST_X(ST_Centroid(d.geom)) / {tile_size}
                 ) * {tile_size}
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


def _register_segment_tiles(
    connection: duckdb.DuckDBPyConnection, tile_size_m: int
) -> None:
    """Assign configured tile ids with the shared EPSG:3035 grid helper."""
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_segment_tile_origins AS
        SELECT DISTINCT
               (floor(ST_Y(ST_Centroid(geom)) / {tile_size_m})
                    * {tile_size_m})::BIGINT AS northing_m,
               (floor(ST_X(ST_Centroid(geom)) / {tile_size_m})
                    * {tile_size_m})::BIGINT AS easting_m
        FROM _osm_way_segments
    """)
    origins = connection.execute("""
        SELECT northing_m, easting_m
        FROM _osm_segment_tile_origins
        ORDER BY northing_m, easting_m
    """).fetchall()
    tile_map = pa.table(
        {
            "northing_m": pa.array([row[0] for row in origins], type=pa.int64()),
            "easting_m": pa.array([row[1] for row in origins], type=pa.int64()),
            "tile_id": pa.array(
                [
                    cell_id(int(northing), int(easting), tile_size_m)
                    for northing, easting in origins
                ],
                type=pa.int64(),
            ),
        }
    )
    connection.register("_osm_tile_id_map", tile_map)
    try:
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_segment_tiles AS
            SELECT * FROM _osm_tile_id_map
        """)
    finally:
        connection.unregister("_osm_tile_id_map")


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
    _register_segment_tiles(connection, config.tile_size_m)
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


def connectivity_summaries(
    connection: duckdb.DuckDBPyConnection, edges_path: str | Path
) -> tuple[ConnectivitySummary, ...]:
    """Compute largest-SCC node and directed-length shares per mode."""
    source = _sql_path(edges_path)
    summaries = []
    for mode in ("car", "bike", "foot"):
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _osm_scc_edges AS
            SELECT from_node_id, to_node_id, coalesce(length_m, 0)::DOUBLE AS length_m
            FROM read_parquet('{source}')
            WHERE mode = '{mode}'
        """)
        node_count = int(
            connection.execute("""
                SELECT count(*) FROM (
                    SELECT from_node_id AS node_id FROM _osm_scc_edges
                    UNION
                    SELECT to_node_id AS node_id FROM _osm_scc_edges
                )
            """).fetchone()[0]
        )
        indexed = connection.execute("""
            WITH node_ids AS (
                SELECT from_node_id AS node_id FROM _osm_scc_edges
                UNION
                SELECT to_node_id AS node_id FROM _osm_scc_edges
            ),
            node_index AS (
                SELECT node_id,
                       row_number() OVER (ORDER BY node_id) - 1 AS node_index
                FROM node_ids
            )
            SELECT source.node_index AS source_index,
                   target.node_index AS target_index, e.length_m
            FROM _osm_scc_edges e
            JOIN node_index source ON source.node_id = e.from_node_id
            JOIN node_index target ON target.node_id = e.to_node_id
            ORDER BY source_index, target_index
        """).to_arrow_table()
        source_indices = np.asarray(
            indexed["source_index"].to_numpy(zero_copy_only=False),
            dtype=np.int64,
        )
        target_indices = np.asarray(
            indexed["target_index"].to_numpy(zero_copy_only=False),
            dtype=np.int64,
        )
        lengths = np.asarray(
            indexed["length_m"].to_numpy(zero_copy_only=False),
            dtype=np.float64,
        )
        edge_count = len(source_indices)
        if node_count == 0:
            summaries.append(ConnectivitySummary(mode, 0, 0, 0, None))
            continue

        indptr = np.empty(node_count + 1, dtype=np.int64)
        indptr[0] = 0
        np.cumsum(
            np.bincount(source_indices, minlength=node_count),
            out=indptr[1:],
        )
        reverse_order = np.argsort(target_indices, kind="stable")
        reverse_sources = target_indices[reverse_order]
        reverse_indptr = np.empty(node_count + 1, dtype=np.int64)
        reverse_indptr[0] = 0
        np.cumsum(
            np.bincount(reverse_sources, minlength=node_count),
            out=reverse_indptr[1:],
        )
        labels, component_sizes, component_count = _strongly_connected_components(
            indptr,
            target_indices,
            reverse_indptr,
            source_indices[reverse_order],
        )
        largest_component = int(np.argmax(component_sizes[:component_count]))
        largest_nodes = int(component_sizes[largest_component])
        inside = (
            (labels[source_indices] == largest_component)
            & (labels[target_indices] == largest_component)
        )
        total_length = float(lengths.sum())
        largest_length_share = (
            float(lengths[inside].sum() / total_length)
            if total_length > 0
            else None
        )
        summaries.append(
            ConnectivitySummary(
                mode,
                node_count,
                edge_count,
                largest_nodes,
                largest_length_share,
            )
        )
    return tuple(summaries)


def _format_length(value: float | None) -> str:
    return "n/a" if value is None else f"{value:,.1f}"


def write_step06_report(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    report_path: str | Path,
    *,
    state: int,
    area: str,
) -> None:
    """Write the section 14.5 step-6 network and connectivity report."""
    source = _sql_path(edges_path)
    class_rows = connection.execute(f"""
        SELECT coalesce(highway, '(no highway)') AS highway, mode,
               count(*) AS edge_count, sum(length_m) AS length_m
        FROM read_parquet('{source}')
        GROUP BY highway, mode
        ORDER BY mode, highway
    """).fetchall()
    speed_rows = connection.execute(f"""
        SELECT coalesce(highway, '(no highway)') AS highway, mode,
               count(*) AS edge_count, count(maxspeed_kmh) AS speed_count,
               sum(length_m) AS length_m,
               sum(CASE WHEN maxspeed_kmh IS NOT NULL THEN length_m ELSE 0 END)
                   AS length_with_speed
        FROM read_parquet('{source}')
        GROUP BY highway, mode
        ORDER BY mode, highway
    """).fetchall()
    bike_rows = connection.execute(f"""
        SELECT coalesce(bike_infra, '(unclassified)') AS bike_infra,
               count(*) AS edge_count, sum(length_m) AS length_m
        FROM read_parquet('{source}')
        WHERE mode = 'bike'
        GROUP BY bike_infra
        ORDER BY bike_infra
    """).fetchall()
    length_checks = connection.execute(f"""
        SELECT count(*) FILTER (WHERE length_m = 0) AS zero_length,
               count(*) FILTER (WHERE length_m IS NULL) AS null_length
        FROM read_parquet('{source}')
    """).fetchone()
    connectivity = connectivity_summaries(connection, edges_path)

    lines = [
        f"# Step 6 OSM pilot ({state}, {area})",
        "",
        "Generated by `python -m mobgrid.osm.edges`; lengths are directed-edge",
        "lengths in metres in EPSG:3035. Access rows are duplicated by mode.",
        "",
        "## Edges and length by highway class and mode",
        "",
        "| Mode | Highway class | Directed edges | Length (m) |",
        "|---|---|---:|---:|",
    ]
    lines.extend(
        f"| {mode} | {highway} | {edge_count:,} | {_format_length(length)} |"
        for highway, mode, edge_count, length in class_rows
    )
    lines.extend(
        [
            "",
            "## Largest strongly connected component",
            "",
            "| Mode | Graph nodes | Nodes in largest SCC | Node share | "
            "Directed length share |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for stats in connectivity:
        node_share = (
            stats.largest_component_nodes / stats.node_count
            if stats.node_count
            else None
        )
        node_share_text = "n/a" if node_share is None else f"{node_share:.1%}"
        length_share_text = (
            "n/a"
            if stats.largest_component_length_share is None
            else f"{stats.largest_component_length_share:.1%}"
        )
        lines.append(
            f"| {stats.mode} | {stats.node_count:,} | "
            f"{stats.largest_component_nodes:,} | "
            f"{node_share_text} | {length_share_text} |"
        )
    lines.extend(
        [
            "",
            "## Length checks",
            "",
            f"- Zero-length directed edges: {length_checks[0]:,}",
            f"- Null-length directed edges: {length_checks[1]:,}",
            "",
            "## Maxspeed coverage by class and mode",
            "",
            "| Mode | Highway class | Directed edges | With maxspeed | "
            "Edge coverage | Length coverage |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for highway, mode, count, speed_count, length, speed_length in speed_rows:
        edge_coverage = speed_count / count if count else None
        length_coverage = (
            speed_length / length
            if length is not None and length > 0
            else None
        )
        lines.append(
            f"| {mode} | {highway} | {count:,} | {speed_count:,} | "
            f"{'n/a' if edge_coverage is None else f'{edge_coverage:.1%}'} | "
            f"{'n/a' if length_coverage is None else f'{length_coverage:.1%}'} |"
        )
    lines.extend(
        [
            "",
            "## Bike infrastructure length",
            "",
            "| Bike class | Directed bike edges | Length (m) |",
            "|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {bike_class} | {edge_count:,} | {_format_length(length)} |"
        for bike_class, edge_count, length in bike_rows
    )
    destination = Path(report_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def _artifact_path(task: str, suffix: str) -> Path:
    return Path("logs") / f"{date.today().isoformat()}_{task}{suffix}"


def _write_edge_summary(
    path: Path,
    *,
    elapsed_seconds: float,
    input_ways: Path,
    input_nodes: Path,
    result: EdgeBuildSummary,
    report_path: Path,
) -> None:
    text = f"""# OSM directed-edge build summary

- Inputs: `{input_ways}`, `{input_nodes}`
- Outputs: `{result.edges_path}`, `{result.nodes_path}`
- Report: `{report_path}`
- Elapsed: {elapsed_seconds:.1f} seconds
- Directed mode edges: {result.edge_count:,}
- Nodes: {result.node_count:,}
- Warnings: none
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.edges")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument("--config", type=Path, default=Path("config/network.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build edges, connectivity checks, and the requested Markdown report."""
    args = _parser().parse_args(argv)
    config = load_network_config(args.config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in config.states:
        raise ValueError(
            f"unsupported state {args.state}; configured: {sorted(config.states)}"
        )
    task = f"osm_edges_{args.state}_{args.area}"
    _configure_logging(args.log or _artifact_path(task, ".log"))
    input_directory = (
        Path(pilot.paths["interim"]) / "osm" / str(args.state) / args.area
    )
    output_directory = (
        Path(pilot.paths["base"]) / "network" / str(args.state) / args.area
    )
    report_path = args.report or (
        Path("docs/data/step06_osm_pilot.md")
        if args.state == 2021 and args.area == "pilot"
        else Path(f"docs/data/step06_osm_{args.area}_{args.state}.md")
    )
    ways_path = input_directory / "ways.parquet"
    nodes_path = input_directory / "nodes.parquet"
    started = time.perf_counter()
    connection = duckdb.connect()
    configure_extraction_connection(connection, pilot.paths["interim"])
    try:
        result = build_directed_edges(
            connection,
            ways_path,
            nodes_path,
            output_directory,
            config=config,
        )
        write_step06_report(
            connection,
            result.edges_path,
            report_path,
            state=args.state,
            area=args.area,
        )
    finally:
        connection.close()
    summary_path = args.summary or _artifact_path(task, "_summary.md")
    _write_edge_summary(
        summary_path,
        elapsed_seconds=time.perf_counter() - started,
        input_ways=ways_path,
        input_nodes=nodes_path,
        result=result,
        report_path=report_path,
    )
    logger.info(
        "wrote report %s and %s directed edges",
        report_path,
        result.edge_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
