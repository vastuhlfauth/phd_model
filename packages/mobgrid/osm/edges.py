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
from acquire.manifest import load_manifest
from common.config import load_pilot_config
from common.duckdb_io import read_parquet, write_parquet
from common.grid import cell_id
from numba import njit

from mobgrid.osm.bike_infra import bike_infrastructure_sql, maxspeed_sql
from mobgrid.osm.config import Mode, NetworkConfig, load_network_config
from mobgrid.osm.geovelo_report import write_geovelo_report_section
from mobgrid.pt.osm_route_extraction import configure_extraction_connection

logger = logging.getLogger(__name__)

EDGE_COLUMNS = {
    "edge_key",
    "way_id",
    "from_node_id",
    "to_node_id",
    "is_forward",
    "mode",
    "node_ids",
    "length_m",
    "highway",
    "maxspeed_kmh",
    "oneway",
    "speed_context",
    "motorroad",
    "lanes",
    "car_access",
    "bike_access",
    "foot_access",
    "bike_infra",
    "surface",
    "tracktype",
    "smoothness",
    "busway",
    "lanes_bus",
    "lanes_psv",
    "signal_count",
    "stop_count",
    "give_way_count",
    "crossing_count",
    "mini_roundabout_count",
    "to_degree",
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
    denied = "[" + ", ".join(
        _sql_text(value.casefold()) for value in rule.denied
    ) + "]"

    def fully_denied(value: str) -> str:
        return (
            "NOT EXISTS ("
            f"SELECT 1 FROM UNNEST(string_split(lower({value}), ';')) "
            "AS access_value(value) "
            f"WHERE trim(access_value.value) <> '' AND NOT list_contains("
            f"{denied}, trim(access_value.value)))"
        )

    denied_list = fully_denied(access)
    excluded = ", ".join(_sql_text(value) for value in rule.excluded_highways)
    included = ", ".join(_sql_text(value) for value in rule.included_highways)
    mode_specific_access = [
        f"nullif(way_tags[{_sql_text(key)}], '')"
        for key in rule.precedence
        if key != "access"
    ]
    mode_specific_access_sql = (
        "coalesce(" + ", ".join(mode_specific_access) + ")"
        if mode_specific_access
        else "NULL"
    )
    mode_specific_highways = ", ".join(
        _sql_text(value) for value in rule.mode_specific_only_highways
    )
    explicit_mode_access = (
        f"({mode_specific_access_sql} IS NOT NULL AND "
        f"NOT ({fully_denied(mode_specific_access_sql)}))"
    )
    if rule.explicit_allowed_values:
        allowed_values = "[" + ", ".join(
            _sql_text(value.casefold())
            for value in rule.explicit_allowed_values
        ) + "]"
        explicit_mode_access += (
            " AND EXISTS ("
            "SELECT 1 FROM UNNEST(string_split("
            f"lower({mode_specific_access_sql}), ';')) "
            "AS mode_access_value(value) "
            "WHERE list_contains("
            f"{allowed_values}, trim(mode_access_value.value)))"
        )
    hard_highways = rule.hard_excluded_highways
    hard_exclusion = (
        "lower(way_tags['highway']) IN ("
        + ", ".join(_sql_text(value) for value in hard_highways)
        + ")"
        if hard_highways
        else "FALSE"
    )
    if mode in ("bike", "foot"):
        motorway_values = ", ".join(
            _sql_text(value) for value in ("motorway", "motorway_link")
        )
        hard_exclusion = (
            f"({hard_exclusion} OR "
            f"(lower(way_tags['highway']) IN ({motorway_values}) "
            "OR (lower(way_tags['highway']) = 'trunk' "
            "AND lower(way_tags['motorroad']) IN ('yes', 'true', '1'))))"
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
    specific_access_rule = (
        f"WHEN lower(way_tags['highway']) IN "
        f"({mode_specific_highways}) THEN ({explicit_mode_access}) "
        if mode_specific_highways
        else ""
    )
    missing_highway_guard = (
        "WHEN way_tags['highway'] IS NULL THEN FALSE "
        if mode != "foot"
        else ""
    )
    return (
        "CASE "
        "WHEN way_tags['highway'] IS NOT NULL AND "
        f"lower(way_tags['highway']) NOT IN "
        f"({', '.join(_sql_text(value) for value in config.known_highways)}) "
        "THEN FALSE "
        f"{missing_highway_guard}"
        f"WHEN {hard_exclusion} THEN FALSE "
        f"{specific_access_rule}"
        f"WHEN {access} IS NOT NULL AND {denied_list} THEN FALSE "
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
        "OR lower(way_tags['junction']) IN ('roundabout', 'circular') "
        "THEN 'yes' END)"
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
            {
                "version": 7,
                "inputs": inputs,
                "config": config.model_dump(
                    mode="json",
                    exclude={
                    "car_speed", "bike_speed_table", "elevation_smoothing_window_m",
                    "geovelo_report",
                    },
                ),
            },
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


def _build_points_sql(
    ways_path: str, nodes_path: str, config: NetworkConfig | None = None
) -> str:
    known = ""
    if config is not None:
        classes = ", ".join(_sql_text(value) for value in config.known_highways)
        known = (
            "WHERE w.tags['highway'] IS NULL "
            f"OR lower(w.tags['highway']) IN ({classes})"
        )
    return f"""
        CREATE OR REPLACE TEMP TABLE _osm_way_points AS
        SELECT w.way_id, ref.node_sequence, ref.node_id, n.lat, n.lon,
               ST_Transform(
                   ST_Point(n.lon, n.lat),
                   'EPSG:4326', 'EPSG:3035', true
               ) AS point
        FROM read_parquet('{ways_path}') w
        CROSS JOIN UNNEST(w.refs) WITH ORDINALITY
            AS ref(node_id, node_sequence)
        JOIN read_parquet('{nodes_path}') n USING (node_id)
        {known}
    """


def _build_segments_sql() -> str:
    return """
        CREATE OR REPLACE TEMP TABLE _osm_way_segments AS
        WITH numbered_points AS (
            SELECT p.*,
                   g.node_id IS NOT NULL AS is_graph_node,
                   sum(CASE WHEN g.node_id IS NOT NULL THEN 1 ELSE 0 END)
                       OVER (
                           PARTITION BY p.way_id
                           ORDER BY p.node_sequence
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                       ) AS graph_node_count,
                   max(p.node_sequence) OVER (
                       PARTITION BY p.way_id
                   ) AS last_sequence
            FROM _osm_way_points p
            LEFT JOIN _osm_graph_node_ids g USING (node_id)
        ),
        segment_points AS (
            SELECT *, graph_node_count - 1 AS segment_index
            FROM numbered_points
            WHERE NOT is_graph_node
               OR node_sequence < last_sequence
            UNION ALL
            SELECT *, graph_node_count - 2 AS segment_index
            FROM numbered_points
            WHERE is_graph_node AND graph_node_count > 1
        )
        SELECT way_id, segment_index,
               arg_min(node_id, node_sequence) AS from_node_id,
               arg_max(node_id, node_sequence) AS to_node_id,
               min(node_sequence) AS from_sequence,
               max(node_sequence) AS to_sequence,
               list(node_id ORDER BY node_sequence) AS node_ids,
               ST_Length_Spheroid(
                   ST_MakeLine(
                       list(ST_Point(lat, lon) ORDER BY node_sequence)
                   )
               ) AS length_m,
               ST_MakeLine(list(point ORDER BY node_sequence)) AS geom
        FROM segment_points
        GROUP BY way_id, segment_index
        HAVING count(*) > 1
    """


def _build_way_attributes_sql(config: NetworkConfig, ways_path: str) -> str:
    accesses = {
        mode: access_sql(mode, config) for mode in ("car", "bike", "foot")
    }
    directions = ", ".join(
        f"{direction_sql(mode, config).replace('is_forward', str(forward).upper())} "
        f"AS {mode}_{'forward' if forward else 'reverse'}"
        for mode in ("car", "bike", "foot")
        for forward in (True, False)
    )
    bike_classes = ", ".join(
        bike_infrastructure_sql("way_tags", str(forward).upper(), "bike_access", config)
        + " "
        f"AS bike_infra_{'forward' if forward else 'reverse'}"
        for forward in (True, False)
    )
    speed_context_cases = " ".join(
        f"WHEN {_sql_text(token.casefold())} THEN {_sql_text(context)}"
        for token, context in config.speed_context_values.items()
    )
    speed_context = "coalesce(" + ", ".join(
        "CASE lower(trim(way_tags["
        + _sql_text(tag)
        + f"])) {speed_context_cases} END"
        for tag in config.speed_context_tags
    ) + ")"
    return f"""
        CREATE OR REPLACE TEMP TABLE _way_attributes AS
        WITH ways AS (
            SELECT way_id, tags AS way_tags FROM read_parquet('{ways_path}')
        ),
        access AS (
            SELECT *,
                   {accesses["car"]} AS car_access,
                   {accesses["bike"]} AS bike_access,
                   {accesses["foot"]} AS foot_access
            FROM ways
        )
        SELECT way_id, car_access, bike_access, foot_access, {directions},
               {bike_classes}, {maxspeed_sql("way_tags", config)} AS maxspeed_kmh,
               {speed_context} AS speed_context,
               coalesce(lower(way_tags['motorroad']) IN ('yes', 'true', '1'), false)
                   AS motorroad,
               way_tags['highway'] AS highway, way_tags['oneway'] AS oneway,
               way_tags['lanes'] AS lanes, way_tags['surface'] AS surface,
               way_tags['tracktype'] AS tracktype, way_tags['smoothness'] AS smoothness,
               way_tags['busway'] AS busway, way_tags['lanes:bus'] AS lanes_bus,
               way_tags['lanes:psv'] AS lanes_psv
        FROM access
    """


def _build_control_tables(
    connection: duckdb.DuckDBPyConnection, nodes_path: str
) -> None:
    started = time.perf_counter()
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _control_nodes AS
        SELECT node_id,
               CASE WHEN lower(tags['highway']) = 'crossing'
                         AND lower(tags['crossing']) = 'traffic_signals'
                    THEN 'traffic_signals' ELSE lower(tags['highway']) END AS kind,
               lower(trim(tags['direction'])) AS direction,
               coalesce(nullif(lower(trim(tags['traffic_signals:direction'])), ''),
                        nullif(lower(trim(tags['direction'])), '')) AS signal_direction
        FROM read_parquet('{nodes_path}')
        WHERE lower(tags['highway']) IN
              ('traffic_signals', 'stop', 'give_way', 'crossing', 'mini_roundabout')
    """)
    _log_stage_elapsed("identify-control-nodes", started)
    started = time.perf_counter()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _control_counts AS
        WITH relevant AS (
            SELECT s.way_id, s.segment_index, d.is_forward, c.kind,
                   CASE WHEN c.kind = 'traffic_signals' THEN c.signal_direction
                        ELSE c.direction END AS direction
            FROM _control_nodes c
            JOIN _osm_way_points p USING (node_id)
            JOIN _osm_way_segments s
              ON s.way_id = p.way_id
             AND p.node_sequence BETWEEN s.from_sequence AND s.to_sequence
            CROSS JOIN (VALUES (true), (false)) d(is_forward)
            WHERE (d.is_forward AND p.node_sequence > s.from_sequence)
               OR (NOT d.is_forward AND p.node_sequence < s.to_sequence)
        )
        SELECT way_id, segment_index, is_forward,
               count(*) FILTER (WHERE kind = 'traffic_signals')::TINYINT
                   AS signal_count,
               count(*) FILTER (WHERE kind = 'stop')::TINYINT AS stop_count,
               count(*) FILTER (WHERE kind = 'give_way')::TINYINT AS give_way_count,
               count(*) FILTER (WHERE kind = 'crossing')::TINYINT AS crossing_count,
               count(*) FILTER (WHERE kind = 'mini_roundabout')::TINYINT
                   AS mini_roundabout_count
        FROM relevant
        WHERE direction IS NULL OR direction NOT IN ('forward', 'backward')
           OR (direction = 'forward' AND is_forward)
           OR (direction = 'backward' AND NOT is_forward)
        GROUP BY way_id, segment_index, is_forward
    """)
    _log_stage_elapsed("count-controls", started)


def _build_allowed_edges(connection: duckdb.DuckDBPyConnection) -> None:
    started = time.perf_counter()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _directions AS
        SELECT way_id, segment_index, from_node_id, to_node_id, true AS is_forward
        FROM _osm_way_segments
        UNION ALL
        SELECT way_id, segment_index, to_node_id, from_node_id, false AS is_forward
        FROM _osm_way_segments
    """)
    _log_stage_elapsed("expand-directions", started)
    started = time.perf_counter()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _allowed_edges AS
        SELECT d.*, m.mode
        FROM _directions d
        JOIN _way_attributes a USING (way_id)
        CROSS JOIN (VALUES ('car'), ('bike'), ('foot')) m(mode)
        WHERE (m.mode = 'car' AND a.car_access AND
               CASE WHEN d.is_forward THEN a.car_forward ELSE a.car_reverse END)
           OR (m.mode = 'bike' AND a.bike_access AND
               CASE WHEN d.is_forward THEN a.bike_forward ELSE a.bike_reverse END)
           OR (m.mode = 'foot' AND a.foot_access AND
               CASE WHEN d.is_forward THEN a.foot_forward ELSE a.foot_reverse END)
    """)
    _log_stage_elapsed("filter-allowed-edges", started)
    started = time.perf_counter()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _node_degrees AS
        WITH neighbours AS (
            SELECT mode, from_node_id AS node_id, to_node_id AS neighbour_id
            FROM _allowed_edges
            UNION ALL
            SELECT mode, to_node_id AS node_id, from_node_id AS neighbour_id
            FROM _allowed_edges
        )
        SELECT mode, node_id, count(DISTINCT neighbour_id) AS to_degree
        FROM neighbours GROUP BY mode, node_id
    """)
    _log_stage_elapsed("compute-node-degrees", started)


def _build_edges_query() -> str:
    return """
        SELECT concat(e.way_id, ':', e.segment_index, ':',
                      e.mode, ':', CASE WHEN e.is_forward THEN 'f' ELSE 'r' END)
                   AS edge_key,
               e.way_id, e.from_node_id, e.to_node_id, e.is_forward,
               e.mode, CASE WHEN e.is_forward THEN s.node_ids
                            ELSE list_reverse(s.node_ids) END AS node_ids,
               s.length_m, a.highway, a.maxspeed_kmh, a.oneway, a.speed_context,
               a.motorroad, a.lanes, a.car_access, a.bike_access, a.foot_access,
               CASE WHEN e.is_forward THEN a.bike_infra_forward
                    ELSE a.bike_infra_reverse END AS bike_infra,
               a.surface, a.tracktype, a.smoothness, a.busway, a.lanes_bus, a.lanes_psv,
               coalesce(c.signal_count, 0::TINYINT) AS signal_count,
               coalesce(c.stop_count, 0::TINYINT) AS stop_count,
               coalesce(c.give_way_count, 0::TINYINT) AS give_way_count,
               coalesce(c.crossing_count, 0::TINYINT) AS crossing_count,
               coalesce(c.mini_roundabout_count, 0::TINYINT) AS mini_roundabout_count,
               coalesce(d.to_degree, 0) AS to_degree,
               l.cell_1km_id, l.tile_id,
               ST_AsWKB(CASE WHEN e.is_forward THEN s.geom
                             ELSE ST_Reverse(s.geom) END) AS geometry_wkb
        FROM _allowed_edges e
        JOIN _osm_way_segments s USING (way_id, segment_index)
        JOIN _way_attributes a USING (way_id)
        JOIN _osm_segment_locations l USING (way_id, segment_index)
        LEFT JOIN _control_counts c USING (way_id, segment_index, is_forward)
        LEFT JOIN _node_degrees d
          ON d.mode = e.mode AND d.node_id = e.to_node_id
    """


def _register_segment_tiles(
    connection: duckdb.DuckDBPyConnection, tile_size_m: int
) -> None:
    """Assign configured tile ids with the shared EPSG:3035 grid helper."""
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _osm_segment_centroids AS
        SELECT way_id, segment_index, ST_Centroid(geom) AS centroid
        FROM _osm_way_segments
    """)
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_segment_tile_origins AS
        SELECT DISTINCT
               (floor(ST_Y(centroid) / {tile_size_m})
                    * {tile_size_m})::BIGINT AS northing_m,
               (floor(ST_X(centroid) / {tile_size_m})
                    * {tile_size_m})::BIGINT AS easting_m
        FROM _osm_segment_centroids
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
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_segment_locations AS
        SELECT c.way_id, c.segment_index,
               floor(ST_Y(c.centroid) / 1000)::BIGINT * 100000
                 + floor(ST_X(c.centroid) / 1000)::BIGINT AS cell_1km_id,
               t.tile_id
        FROM _osm_segment_centroids c
        JOIN _osm_segment_tiles t
          ON t.northing_m = floor(ST_Y(c.centroid) / {tile_size_m}) * {tile_size_m}
         AND t.easting_m = floor(ST_X(c.centroid) / {tile_size_m}) * {tile_size_m}
    """)


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


def _log_stage_elapsed(stage: str, started_at: float) -> None:
    logger.info(
        "edge-build stage %s elapsed %.3f seconds",
        stage,
        time.perf_counter() - started_at,
    )


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
    force: bool = False,
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
    if (
        not force and edges_path.is_file() and output_nodes_path.is_file()
        and metadata_path.is_file()
    ):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("signature") == signature
            and EDGE_COLUMNS <= _cache_schema(connection, edges_path)
            and NODE_COLUMNS <= _cache_schema(connection, output_nodes_path)
        ):
            logger.info("reusing cached directed edges in %s", output)
            return _summary_from_files(connection, edges_path, output_nodes_path)

    metadata_path.unlink(missing_ok=True)
    stage_started = time.perf_counter()
    connection.execute("LOAD spatial")
    _log_stage_elapsed("load-spatial", stage_started)
    ways_source = _sql_path(ways)
    nodes_source = _sql_path(nodes)
    stage_started = time.perf_counter()
    connection.execute(_build_points_sql(ways_source, nodes_source, config))
    _log_stage_elapsed("expand-way-nodes", stage_started)
    stage_started = time.perf_counter()
    connection.execute(_build_way_attributes_sql(config, ways_source))
    _log_stage_elapsed("compute-way-attributes", stage_started)
    stage_started = time.perf_counter()
    _build_graph_nodes(connection)
    _log_stage_elapsed("identify-graph-nodes", stage_started)
    stage_started = time.perf_counter()
    connection.execute(_build_segments_sql())
    _log_stage_elapsed("assign-segments", stage_started)
    stage_started = time.perf_counter()
    _register_segment_tiles(connection, config.tile_size_m)
    _log_stage_elapsed("assign-tiles", stage_started)
    _build_control_tables(connection, nodes_source)
    _build_allowed_edges(connection)
    stage_started = time.perf_counter()
    _write_parquet_atomic(
        connection,
        _build_edges_query(),
        edges_path,
    )
    _log_stage_elapsed("write-directed-edges", stage_started)
    stage_started = time.perf_counter()
    _write_parquet_atomic(
        connection,
        _build_nodes_query(nodes_source),
        output_nodes_path,
    )
    _log_stage_elapsed("write-graph-nodes", stage_started)
    stage_started = time.perf_counter()
    _write_metadata(metadata_path, signature)
    _log_stage_elapsed("write-cache-metadata", stage_started)
    stage_started = time.perf_counter()
    summary = _summary_from_files(connection, edges_path, output_nodes_path)
    _log_stage_elapsed("count-output-rows", stage_started)
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
    ways_path: str | Path,
    config: NetworkConfig,
) -> None:
    """Write the section 14.5 step-6 network and connectivity report."""
    source = _sql_path(edges_path)
    ways_source = _sql_path(ways_path)
    known = ", ".join(_sql_text(value) for value in config.known_highways)
    dropped_rows = connection.execute(f"""
        SELECT tags['highway'], count(DISTINCT way_id)
        FROM read_parquet('{ways_source}')
        WHERE tags['highway'] IS NOT NULL
          AND lower(tags['highway']) NOT IN ({known})
        GROUP BY tags['highway']
        ORDER BY tags['highway']
    """).fetchall()
    car_classes = ", ".join(
        _sql_text(value) for value in config.access_rules["car"].excluded_highways
    )
    tag_cases = " ".join(
        f"WHEN nullif(w.tags[{_sql_text(tag)}], '') IS NOT NULL "
        f"THEN {_sql_text(tag)}"
        for tag in config.access_rules["car"].precedence
    )
    tag_value = "coalesce(" + ", ".join(
        f"nullif(w.tags[{_sql_text(tag)}], '')"
        for tag in config.access_rules["car"].precedence
    ) + ")"
    car_rows = connection.execute(f"""
        SELECT e.highway, CASE {tag_cases} END AS access_tag,
               {tag_value} AS access_value, count(*), sum(e.length_m)
        FROM read_parquet('{source}') e
        JOIN read_parquet('{ways_source}') w USING (way_id)
        WHERE e.mode = 'car' AND lower(e.highway) IN ({car_classes})
        GROUP BY e.highway, access_tag, access_value
        ORDER BY e.highway, access_tag, access_value
    """).fetchall()
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
        "lengths are ellipsoidal metres computed from ordered OSM node "
        "latitude/longitude coordinates. Access rows are duplicated by mode.",
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
    lines.extend([
        "",
        "## Dropped highway values",
        "",
        "| Highway value | Ways |",
        "|---|---:|",
    ])
    lines.extend(f"| {highway} | {count:,} |" for highway, count in dropped_rows)
    lines.extend([
        "",
        "## Car access on non-road classes",
        "",
        "| Highway class | Access tag | Value | Directed edges | Length (m) |",
        "|---|---|---|---:|---:|",
    ])
    lines.extend(
        f"| {highway} | {tag or '(default)'} | {value or '(none)'} | "
        f"{count:,} | {_format_length(length)} |"
        for highway, tag, value, count, length in car_rows
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


def _configure_edge_connection(
    connection: duckdb.DuckDBPyConnection, interim_path: str
) -> None:
    configure_extraction_connection(connection, interim_path)
    connection.execute("SET preserve_insertion_order = false")


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
    parser.add_argument("--manifest", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--force", action="store_true", help="rebuild cached edges")
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
    connection_started = time.perf_counter()
    _configure_edge_connection(connection, pilot.paths["interim"])
    _log_stage_elapsed("configure-connection", connection_started)
    try:
        result = build_directed_edges(
            connection,
            ways_path,
            nodes_path,
            output_directory,
            config=config,
            force=args.force,
        )
        report_started = time.perf_counter()
        write_step06_report(
            connection,
            result.edges_path,
            report_path,
            state=args.state,
            area=args.area,
            ways_path=ways_path,
            config=config,
        )
        source_id = config.geovelo_report.source_ids_by_state.get(args.state)
        if args.area == "pilot" and source_id is not None:
            sources = {source.id: source for source in load_manifest(args.manifest)}
            geovelo_source = sources.get(source_id)
            contour_source = sources.get(config.contour_source_id)
            if geovelo_source is None:
                raise ValueError(f"Géovélo source {source_id!r} is not in the manifest")
            if contour_source is None:
                raise ValueError(
                    "contour source "
                    f"{config.contour_source_id!r} is not in the manifest"
                )
            write_geovelo_report_section(
                connection,
                report_path,
                ways_path=ways_path,
                nodes_path=nodes_path,
                edges_path=result.edges_path,
                geovelo_path=geovelo_source.local_path,
                contours_path=contour_source.local_path,
                department=pilot.department,
                source_id=source_id,
                config=config,
            )
        _log_stage_elapsed("connectivity-and-report", report_started)
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
