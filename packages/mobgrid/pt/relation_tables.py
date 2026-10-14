"""DuckDB spatial precompute and geometry-free GTFS relation calibration."""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pyarrow as pa

from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.route_relations import (
    RelationMatch,
    RoutePattern,
    RouteResult,
    classify_bhns,
)

_CACHE_VERSION = 3
_FIXED_MODES = frozenset(("tram", "metro", "rail"))
_MODE_SQL = """
CASE route
    WHEN 'bus' THEN 'bus'
    WHEN 'trolleybus' THEN 'bus'
    WHEN 'coach' THEN 'bus'
    WHEN 'tram' THEN 'tram'
    WHEN 'light_rail' THEN 'tram'
    WHEN 'subway' THEN 'metro'
    WHEN 'monorail' THEN 'metro'
    WHEN 'train' THEN 'rail'
    WHEN 'ferry' THEN 'ferry'
END
"""


@dataclass(frozen=True)
class PrecomputeSummary:
    """Paths and timings for the persistent scalar calibration tables."""

    cache_directory: Path
    patterns_path: Path
    distances_path: Path
    names_path: Path
    dates: tuple[str, ...]
    elapsed_seconds: float
    pattern_count: int
    candidate_relation_count: int
    distance_count: int
    name_count: int


@dataclass(frozen=True)
class CachedRouteRun:
    """One route/date result produced without access to OSM geometry."""

    network: str
    date_key: str
    pattern: RoutePattern
    match: RelationMatch
    result: RouteResult
    expected: str
    known_case: bool
    case_id: str | None


def _sql_path(path: str | Path) -> str:
    return Path(path).as_posix().replace("'", "''")


def _sql_literal(value: str) -> str:
    return value.replace("'", "''")


def _normalise_text(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value).encode(
        "ascii", "ignore"
    ).decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())


def _normalise_ref(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode(
        "ascii", "ignore"
    ).decode("ascii")
    text = re.sub(r"^\s*(?:ligne|line)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[tml]\s*[-.:]?\s*(?=[a-z0-9])", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def _copy_atomic(
    connection: duckdb.DuckDBPyConnection, query: str, path: Path
) -> None:
    temporary = path.with_suffix(".tmp.parquet")
    connection.execute(
        f"COPY ({query}) TO '{_sql_path(temporary)}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    temporary.replace(path)


def _register_pattern_input(
    connection: duckdb.DuckDBPyConnection,
    tables: dict[str, pa.Table],
) -> None:
    combined = []
    for network, table in tables.items():
        combined.append(
            table.append_column(
                "network", pa.array([network] * table.num_rows, pa.string())
            )
        )
    if not combined:
        raise ValueError("no GTFS pattern tables to calibrate")
    input_table = pa.concat_tables(combined, promote_options="default")
    connection.register("calibration_pattern_input", input_table)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE calibration_patterns AS
        WITH pattern_rank AS (
            SELECT network, route_id, pattern_id,
                   row_number() OVER (
                       PARTITION BY network, route_id
                       ORDER BY trip_count DESC, pattern_id
                   ) AS rank
            FROM calibration_pattern_input
            GROUP BY network, route_id, pattern_id, trip_count
        )
        SELECT input.*
        FROM calibration_pattern_input input
        JOIN pattern_rank USING (network, route_id, pattern_id)
        WHERE rank = 1
    """)
    connection.unregister("calibration_pattern_input")
    pattern_columns = {
        row[0]
        for row in connection.execute(
            "DESCRIBE SELECT * FROM calibration_patterns"
        ).fetchall()
    }
    description_sql = (
        "route_desc" if "route_desc" in pattern_columns else "CAST(NULL AS VARCHAR)"
    )
    connection.create_function(
        "calibration_classify_bhns",
        classify_bhns,
        [str, str, str],
        bool,
        null_handling="special",
    )
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE calibration_patterns AS
        SELECT *, calibration_classify_bhns(
            route_short_name, route_long_name, {description_sql}
        ) AS is_bhns
        FROM calibration_patterns
    """)



def _future_dated_sql(has_opening_date: bool, has_start_date: bool) -> str:
    """Build a `ways.*` boolean: value tagged as opening after the snapshot.

    Handles both full ISO dates and bare years (OSM `opening_date`/
    `start_date` are free text); defensive no-op (``false``) when the
    source cache predates these columns, so older caches keep working.
    """
    checks = []
    for column in ("opening_date", "start_date"):
        if (column == "opening_date" and not has_opening_date) or (
            column == "start_date" and not has_start_date
        ):
            continue
        checks.append(f"""
            (try_cast(ways.{column} AS DATE) IS NOT NULL
                 AND try_cast(ways.{column} AS DATE) > CAST(ways.date_key AS DATE))
            OR (regexp_matches(ways.{column}, '^[0-9]{{4}}')
                 AND CAST(regexp_extract(ways.{column}, '^([0-9]{{4}})', 1)
                          AS INTEGER) > year(CAST(ways.date_key AS DATE)))
        """)
    if not checks:
        return "false"
    return " OR ".join(f"({check})" for check in checks)


def _create_osm_views(
    connection: duckdb.DuckDBPyConnection,
    route_cache_directories: dict[str, Path],
) -> None:
    relations = []
    ways = []
    stops = []
    for date_key, root in sorted(route_cache_directories.items()):
        date = date_key.replace("'", "''")
        relations.append(
            f"SELECT '{date}' AS date_key, * FROM "
            f"read_parquet('{_sql_path(root / 'relations.parquet')}')"
        )
        ways.append(
            f"SELECT '{date}' AS date_key, * FROM "
            f"read_parquet('{_sql_path(root / 'ways.parquet')}')"
        )
        stops.append(
            f"SELECT '{date}' AS date_key, * FROM "
            f"read_parquet('{_sql_path(root / 'stops.parquet')}')"
        )
    connection.execute(
        "CREATE OR REPLACE TEMP VIEW calibration_osm_relations AS "
        + " UNION ALL ".join(relations)
    )
    connection.execute(
        "CREATE OR REPLACE TEMP VIEW calibration_osm_ways_raw AS "
        + " UNION ALL ".join(ways)
    )
    connection.execute(
        "CREATE OR REPLACE TEMP VIEW calibration_osm_stops AS "
        + " UNION ALL ".join(stops)
    )
    ways_columns = {
        row[0]
        for row in connection.execute(
            "DESCRIBE SELECT * FROM calibration_osm_ways_raw"
        ).fetchall()
    }
    future_dated_sql = _future_dated_sql(
        "opening_date" in ways_columns, "start_date" in ways_columns
    )
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE calibration_relation_ways AS
        SELECT ways.date_key, ways.relation_id, relations.ref,
               relations.name, relations.network, relations.operator,
               {_MODE_SQL} AS mode, ways.way_id,
               ST_GeomFromWKB(ways.geometry) AS geom,
               ST_XMin(ST_GeomFromWKB(ways.geometry)) AS xmin,
               ST_YMin(ST_GeomFromWKB(ways.geometry)) AS ymin,
               ST_XMax(ST_GeomFromWKB(ways.geometry)) AS xmax,
               ST_YMax(ST_GeomFromWKB(ways.geometry)) AS ymax,
               CASE
                   WHEN {_MODE_SQL} NOT IN ('tram', 'metro', 'rail') THEN true
                   WHEN ways.lifecycle OR ways.construction IS NOT NULL THEN false
                   WHEN {future_dated_sql} THEN false
                   WHEN {_MODE_SQL} = 'tram'
                       THEN ways.railway IN ('tram', 'light_rail')
                   WHEN {_MODE_SQL} = 'metro' THEN ways.railway = 'subway'
                   WHEN {_MODE_SQL} = 'rail' THEN ways.railway = 'rail'
                   ELSE false
               END AS in_service,
               CASE
                   WHEN ways.lifecycle OR ways.construction IS NOT NULL THEN false
                   WHEN {future_dated_sql} THEN false
                   WHEN ways.highway IN ('busway', 'bus_guideway') THEN true
                   WHEN ways.busway IS NOT NULL THEN true
                   WHEN ways.lanes_bus IS NOT NULL THEN true
                   ELSE false
               END AS bus_lane_in_service
        FROM calibration_osm_ways_raw ways
        JOIN calibration_osm_relations relations
          USING (date_key, relation_id)
        WHERE ways.geometry IS NOT NULL
    """)


def _create_candidates(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE calibration_relation_bounds AS
        SELECT date_key, relation_id, any_value(ref) AS ref,
               any_value(name) AS name, any_value(network) AS relation_network,
               any_value(operator) AS operator, any_value(mode) AS mode,
               min(xmin) AS xmin, min(ymin) AS ymin,
               max(xmax) AS xmax, max(ymax) AS ymax
        FROM calibration_relation_ways
        GROUP BY date_key, relation_id
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE calibration_candidates AS
        SELECT DISTINCT patterns.network, patterns.pattern_id, patterns.route_id,
               relations.date_key, relations.relation_id, relations.ref,
               relations.name, relations.relation_network, relations.operator,
               relations.mode
        FROM calibration_patterns patterns
        JOIN calibration_relation_bounds relations
          ON relations.mode = patterns.transport_mode
         AND patterns.x BETWEEN relations.xmin - 1000
                            AND relations.xmax + 1000
         AND patterns.y BETWEEN relations.ymin - 1000
                            AND relations.ymax + 1000
    """)


def _write_names(
    connection: duckdb.DuckDBPyConnection, destination: Path
) -> None:
    connection.create_function(
        "calibration_normalise_ref",
        _normalise_ref,
        [str],
        str,
        null_handling="special",
    )
    connection.create_function(
        "calibration_normalise_text",
        _normalise_text,
        [str],
        str,
        null_handling="special",
    )
    _copy_atomic(
        connection,
        """
        WITH metadata AS (
            SELECT network, pattern_id,
                   any_value(route_short_name) AS short_name,
                   any_value(route_long_name) AS long_name,
                   any_value(agency_name) AS agency_name
            FROM calibration_patterns
            GROUP BY network, pattern_id
        )
        SELECT candidates.date_key, candidates.network,
               candidates.pattern_id, candidates.relation_id,
               candidates.ref AS relation_ref,
               CASE WHEN calibration_normalise_text(metadata.agency_name) != ''
                          AND (
                            (
                              calibration_normalise_text(
                                candidates.relation_network
                              ) != ''
                              AND (contains(
                              calibration_normalise_text(metadata.agency_name),
                              calibration_normalise_text(
                                candidates.relation_network
                              )
                            )
                            OR contains(
                              calibration_normalise_text(
                                candidates.relation_network
                              ),
                              calibration_normalise_text(metadata.agency_name)
                            )))
                            OR (
                              calibration_normalise_text(candidates.operator) != ''
                              AND (contains(
                              calibration_normalise_text(metadata.agency_name),
                              calibration_normalise_text(candidates.operator)
                            )
                            OR contains(
                              calibration_normalise_text(candidates.operator),
                              calibration_normalise_text(metadata.agency_name)
                            )))
                          )
                    THEN 1 ELSE 0 END AS affiliation_score
        FROM calibration_candidates candidates
        JOIN metadata USING (network, pattern_id)
        WHERE (
            calibration_normalise_ref(metadata.short_name) != ''
            AND calibration_normalise_ref(metadata.short_name)
                = calibration_normalise_ref(candidates.ref)
        ) OR (
            calibration_normalise_text(metadata.long_name) != ''
            AND calibration_normalise_text(metadata.long_name)
                = calibration_normalise_text(candidates.name)
        )
        """,
        destination,
    )


def _distance_query(max_r_m: int, include_fallback: bool) -> str:
    relation_distances = f"""
        WITH way_distances AS (
            SELECT candidates.date_key, candidates.network,
                   candidates.pattern_id, patterns.stop_sequence,
                   candidates.relation_id,
                   candidates.ref AS relation_ref,
                   CASE
                       WHEN patterns.transport_mode IN ('tram', 'metro', 'rail')
                           THEN ways.in_service
                       WHEN patterns.transport_mode = 'bus' AND patterns.is_bhns
                           THEN ways.bus_lane_in_service
                       ELSE true
                   END AS in_service,
                   ST_Distance(ST_Point(patterns.x, patterns.y), ways.geom)
                       AS distance_m,
                   false AS is_fallback
            FROM calibration_patterns patterns
            JOIN calibration_candidates candidates
              USING (network, pattern_id)
            JOIN calibration_relation_ways ways
              USING (date_key, relation_id)
            WHERE ways.xmax >= patterns.x - {max_r_m}
              AND ways.xmin <= patterns.x + {max_r_m}
              AND ways.ymax >= patterns.y - {max_r_m}
              AND ways.ymin <= patterns.y + {max_r_m}
        ),
        member_stop_distances AS (
            SELECT candidates.date_key, candidates.network,
                   candidates.pattern_id, patterns.stop_sequence,
                   candidates.relation_id,
                   candidates.ref AS relation_ref, true AS in_service,
                   sqrt(pow(patterns.x - stops.x, 2)
                        + pow(patterns.y - stops.y, 2)) AS distance_m,
                   false AS is_fallback
            FROM calibration_patterns patterns
            JOIN calibration_candidates candidates
              USING (network, pattern_id)
            JOIN calibration_osm_stops stops
              USING (date_key, relation_id)
            WHERE (candidates.mode = 'ferry'
                   OR (candidates.mode = 'bus' AND NOT patterns.is_bhns))
              AND stops.x BETWEEN patterns.x - {max_r_m}
                              AND patterns.x + {max_r_m}
              AND stops.y BETWEEN patterns.y - {max_r_m}
                              AND patterns.y + {max_r_m}
        ),
        relation_rows AS (
            SELECT * FROM way_distances WHERE distance_m <= {max_r_m}
            UNION ALL
            SELECT * FROM member_stop_distances WHERE distance_m <= {max_r_m}
        )
        SELECT date_key, network, pattern_id, stop_sequence,
               relation_id, relation_ref, in_service,
               min(distance_m) AS distance_m, is_fallback
        FROM relation_rows
        GROUP BY ALL
    """
    if not include_fallback:
        return relation_distances
    return f"""
        WITH relation_result AS ({relation_distances}),
        candidate_service_ways AS (
            SELECT DISTINCT candidates.date_key, candidates.relation_id,
                   candidates.mode, ways.geom, ways.xmin, ways.ymin,
                   ways.xmax, ways.ymax
            FROM calibration_candidates candidates
            JOIN calibration_relation_ways ways
              USING (date_key, relation_id)
            WHERE candidates.mode IN ('tram', 'metro', 'rail')
              AND ways.in_service
        ),
        qualified_osm_stops AS (
            SELECT DISTINCT stops.date_key, stops.mode_family,
                   stops.id, stops.kind, stops.x, stops.y
            FROM calibration_fallback_stops stops
            JOIN candidate_service_ways ways
              ON ways.date_key = stops.date_key
             AND ways.mode = stops.mode_family
             AND ways.xmax >= stops.x - {max_r_m}
             AND ways.xmin <= stops.x + {max_r_m}
             AND ways.ymax >= stops.y - {max_r_m}
             AND ways.ymin <= stops.y + {max_r_m}
             AND ST_Distance(ST_Point(stops.x, stops.y), ways.geom)
                 <= {max_r_m}
        ),
        fallback_rows AS (
            SELECT dates.date_key, patterns.network, patterns.pattern_id,
                   patterns.stop_sequence, NULL::BIGINT AS relation_id,
                   NULL::VARCHAR AS relation_ref, true AS in_service,
                   min(sqrt(pow(patterns.x - stops.x, 2)
                            + pow(patterns.y - stops.y, 2))) AS distance_m,
                   true AS is_fallback
            FROM calibration_patterns patterns
            CROSS JOIN (SELECT DISTINCT date_key
                        FROM calibration_osm_relations) dates
            JOIN qualified_osm_stops stops
              ON stops.date_key = dates.date_key
             AND stops.mode_family = patterns.transport_mode
             AND stops.x BETWEEN patterns.x - {max_r_m}
                             AND patterns.x + {max_r_m}
             AND stops.y BETWEEN patterns.y - {max_r_m}
                             AND patterns.y + {max_r_m}
            WHERE patterns.transport_mode IN ('tram', 'metro', 'rail')
            GROUP BY dates.date_key, patterns.network, patterns.pattern_id,
                     patterns.stop_sequence
        )
        SELECT * FROM relation_result
        UNION ALL
        SELECT * FROM fallback_rows WHERE distance_m <= {max_r_m}
    """


def _create_fallback_view(
    connection: duckdb.DuckDBPyConnection,
    stop_cache_paths: dict[str, Path],
) -> bool:
    if not stop_cache_paths:
        return False
    sources = [
        f"SELECT '{_sql_literal(date)}' AS date_key, * "
        f"FROM read_parquet('{_sql_path(path)}')"
        for date, path in sorted(stop_cache_paths.items())
        if path.is_file()
    ]
    if not sources:
        return False
    connection.execute(
        "CREATE OR REPLACE TEMP VIEW calibration_fallback_stops AS "
        + " UNION ALL ".join(sources)
    )
    return True


def precompute_relation_tables(
    connection: duckdb.DuckDBPyConnection,
    pattern_tables: dict[str, pa.Table],
    route_cache_directories: dict[str, Path],
    stop_cache_paths: dict[str, Path],
    output_directory: str | Path,
    config: GtfsRebuildConfig,
    *,
    max_r_m: int,
) -> PrecomputeSummary:
    """Write reduced patterns, spatial distances and name candidates once."""
    del config
    started = time.perf_counter()
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    patterns_path = output / "patterns.parquet"
    distances_path = output / "relation_distances.parquet"
    names_path = output / "name_matches.parquet"
    signature_payload = {
        "version": _CACHE_VERSION,
        "max_r_m": max_r_m,
        "patterns": {
            network: (
                table.num_rows,
                sorted(set(table.column("pattern_id").to_pylist())),
            )
            for network, table in sorted(pattern_tables.items())
        },
        "route_caches": {
            date: {
                name: (
                    (root / f"{name}.parquet").stat().st_size,
                    (root / f"{name}.parquet").stat().st_mtime_ns,
                )
                for name in ("relations", "ways", "stops")
            }
            for date, root in sorted(route_cache_directories.items())
        },
        "stop_caches": {
            date: (path.stat().st_size, path.stat().st_mtime_ns)
            for date, path in sorted(stop_cache_paths.items())
            if path.is_file()
        },
    }
    signature = hashlib.sha256(
        json.dumps(signature_payload, sort_keys=True).encode()
    ).hexdigest()
    metadata_path = output / "precompute.json"
    if (
        metadata_path.is_file()
        and patterns_path.is_file()
        and distances_path.is_file()
        and names_path.is_file()
    ):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("signature") == signature:
            return load_precompute_summary(output)

    connection.execute("LOAD spatial")
    _register_pattern_input(connection, pattern_tables)
    _create_osm_views(connection, route_cache_directories)
    _create_candidates(connection)
    _copy_atomic(connection, "SELECT * FROM calibration_patterns", patterns_path)
    _write_names(connection, names_path)
    include_fallback = _create_fallback_view(connection, stop_cache_paths)
    _copy_atomic(
        connection,
        _distance_query(max_r_m, include_fallback),
        distances_path,
    )

    counts = {
        "patterns": connection.execute(
            "SELECT count(DISTINCT network || ':' || pattern_id) "
            "FROM calibration_patterns"
        ).fetchone()[0],
        "candidates": connection.execute(
            "SELECT count(*) FROM calibration_candidates"
        ).fetchone()[0],
        "distances": connection.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(distances_path)]
        ).fetchone()[0],
        "names": connection.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(names_path)]
        ).fetchone()[0],
    }
    dates = tuple(sorted(route_cache_directories))
    metadata = {
        "version": _CACHE_VERSION,
        "signature": signature,
        "dates": dates,
        "max_r_m": max_r_m,
        "pattern_count": counts["patterns"],
        "candidate_relation_count": counts["candidates"],
        "distance_count": counts["distances"],
        "name_count": counts["names"],
    }
    (output / "precompute.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return PrecomputeSummary(
        output,
        patterns_path,
        distances_path,
        names_path,
        dates,
        time.perf_counter() - started,
        counts["patterns"],
        counts["candidates"],
        counts["distances"],
        counts["names"],
    )


def load_precompute_summary(directory: str | Path) -> PrecomputeSummary:
    """Load an existing table-precompute cache."""
    root = Path(directory)
    metadata = json.loads((root / "precompute.json").read_text(encoding="utf-8"))
    if metadata["version"] != _CACHE_VERSION:
        raise ValueError("calibration precompute cache version changed")
    return PrecomputeSummary(
        root,
        root / "patterns.parquet",
        root / "relation_distances.parquet",
        root / "name_matches.parquet",
        tuple(metadata["dates"]),
        0.0,
        metadata["pattern_count"],
        metadata["candidate_relation_count"],
        metadata["distance_count"],
        metadata["name_count"],
    )


def _expected(
    config: GtfsRebuildConfig,
    network: str,
    route_id: str,
    short_name: str | None,
    date_key: str,
) -> tuple[str, bool, str | None]:
    for case in config.known_cases:
        if case.network == network and case.route_id in {route_id, short_name}:
            expected = (
                case.expected_2022
                if date_key == "2022-01-01"
                else case.expected_2024
            )
            if expected is None:
                return "kept", False, case.id
            return expected, True, case.id
    return "kept", False, None


def _pattern_lookup(
    connection: duckdb.DuckDBPyConnection, path: Path
) -> dict[tuple[str, str], RoutePattern]:
    rows = connection.execute(
        """
        SELECT network, pattern_id, any_value(route_id),
               any_value(route_short_name), any_value(route_long_name),
               any_value(transport_mode), any_value(agency_name),
               any_value(trip_count), any_value(is_bhns),
               list(struct_pack(x := x, y := y) ORDER BY stop_sequence)
        FROM read_parquet(?)
        GROUP BY network, pattern_id
        """,
        [str(path)],
    ).fetchall()
    return {
        (network, pattern_id): RoutePattern(
            pattern_id,
            route_id,
            short_name,
            long_name,
            mode,
            agency_name,
            trip_count,
            tuple((float(point["x"]), float(point["y"])) for point in stops),
            is_bhns=bool(is_bhns),
        )
        for (
            network,
            pattern_id,
            route_id,
            short_name,
            long_name,
            mode,
            agency_name,
            trip_count,
            is_bhns,
            stops,
        ) in rows
    }


def _values_sql(values: list[int | float]) -> str:
    return ", ".join(f"({value})" for value in values)


def _bulk_evaluation_sql(
    summary: PrecomputeSummary,
    dates: tuple[str, ...],
    r_values: list[int],
    k_values: list[int],
    theta_values: list[float],
    geometry_values: list[float],
) -> str:
    date_values = ", ".join(f"('{_sql_literal(date)}')" for date in dates)
    return f"""
        WITH
        dates(date_key) AS (VALUES {date_values}),
        radii(r_m) AS (VALUES {_values_sql(r_values)}),
        geometries(geometry_share) AS (VALUES {_values_sql(geometry_values)}),
        ks(k) AS (VALUES {_values_sql(k_values)}),
        thetas(theta) AS (VALUES {_values_sql(theta_values)}),
        match_params AS (
            SELECT r_m, geometry_share FROM radii CROSS JOIN geometries
        ),
        grid_params AS (
            SELECT r_m, geometry_share, k, theta
            FROM match_params CROSS JOIN ks CROSS JOIN thetas
        ),
        patterns AS (
            SELECT *, row_number() OVER (
                PARTITION BY network, pattern_id ORDER BY stop_sequence
            ) AS ordinal
            FROM read_parquet('{_sql_path(summary.patterns_path)}')
        ),
        pattern_meta AS (
            SELECT network, pattern_id, any_value(route_id) AS route_id,
                   any_value(transport_mode) AS mode,
                   any_value(is_bhns) AS is_bhns, count(*) AS stop_count
            FROM patterns GROUP BY network, pattern_id
        ),
        names AS (
            SELECT *, max(affiliation_score) OVER (
                PARTITION BY date_key, network, pattern_id
            ) AS best_affiliation
            FROM read_parquet('{_sql_path(summary.names_path)}')
        ),
        selected_names_base AS (
            SELECT date_key, network, pattern_id, relation_id, relation_ref
            FROM names WHERE affiliation_score = best_affiliation
        ),
        selected_names AS (
            SELECT params.r_m, params.geometry_share, names.*,
                   'name' AS match_pass
            FROM match_params params CROSS JOIN selected_names_base names
        ),
        relation_coverage AS (
            SELECT radii.r_m, distances.date_key, distances.network,
                   distances.pattern_id, distances.relation_id,
                   any_value(distances.relation_ref) AS relation_ref,
                   count(DISTINCT distances.stop_sequence)
                       FILTER (WHERE distances.in_service
                                      AND distances.distance_m <= radii.r_m)
                       / any_value(meta.stop_count)::DOUBLE AS covered_share
            FROM read_parquet('{_sql_path(summary.distances_path)}') distances
            JOIN pattern_meta meta USING (network, pattern_id)
            CROSS JOIN radii
            WHERE NOT distances.is_fallback
            GROUP BY radii.r_m, distances.date_key, distances.network,
                     distances.pattern_id, distances.relation_id
        ),
        geometry_ranked AS (
            SELECT coverage.*, geometries.geometry_share,
                   max(covered_share) OVER (
                       PARTITION BY coverage.r_m, geometries.geometry_share,
                                    date_key, network, pattern_id
                   ) AS best_share
            FROM relation_coverage coverage CROSS JOIN geometries
            WHERE coverage.covered_share >= geometries.geometry_share
              AND NOT EXISTS (
                  SELECT 1 FROM selected_names_base names
                  WHERE names.date_key = coverage.date_key
                    AND names.network = coverage.network
                    AND names.pattern_id = coverage.pattern_id
              )
        ),
        selected_geometry AS (
            SELECT r_m, geometry_share, date_key, network, pattern_id,
                   relation_id, relation_ref, 'geometry' AS match_pass
            FROM geometry_ranked WHERE covered_share = best_share
        ),
        matches AS (
            SELECT * FROM selected_names
            UNION ALL
            SELECT * FROM selected_geometry
        ),
        matched_routes AS (
            SELECT DISTINCT r_m, geometry_share, date_key, network, pattern_id
            FROM matches
        ),
        network_status AS (
            SELECT params.r_m, params.geometry_share, dates.date_key,
                   meta.network, count(*) AS total_routes,
                   count(matched.pattern_id) AS matched_routes,
                   count(matched.pattern_id) * 2 >= count(*) AS testable
            FROM match_params params CROSS JOIN dates CROSS JOIN pattern_meta meta
            LEFT JOIN matched_routes matched
              ON matched.r_m = params.r_m
             AND matched.geometry_share = params.geometry_share
             AND matched.date_key = dates.date_key
             AND matched.network = meta.network
             AND matched.pattern_id = meta.pattern_id
            GROUP BY params.r_m, params.geometry_share,
                     dates.date_key, meta.network
        ),
        match_meta AS (
            SELECT r_m, geometry_share, date_key, network, pattern_id,
                   any_value(match_pass) AS match_pass,
                   list(DISTINCT relation_id ORDER BY relation_id)
                       AS relation_ids,
                   list(DISTINCT relation_ref ORDER BY relation_ref)
                       FILTER (WHERE relation_ref IS NOT NULL) AS relation_refs
            FROM matches
            GROUP BY r_m, geometry_share, date_key, network, pattern_id
        ),
        matched_covered AS (
            SELECT DISTINCT matches.r_m, matches.geometry_share,
                   patterns.network, patterns.pattern_id,
                   patterns.stop_sequence, matches.date_key
            FROM patterns
            JOIN matches USING (network, pattern_id)
            JOIN read_parquet('{_sql_path(summary.distances_path)}') distances
              ON distances.date_key = matches.date_key
             AND distances.network = matches.network
             AND distances.pattern_id = matches.pattern_id
             AND distances.stop_sequence = patterns.stop_sequence
             AND distances.relation_id = matches.relation_id
             AND NOT distances.is_fallback
             AND distances.in_service
             AND distances.distance_m <= matches.r_m
        ),
        track_covered AS (
            -- Relations give identity (via `matches`); tracks give
            -- coverage. A tram/metro/rail stop counts as covered if it
            -- sits within r of ANY in-service same-mode relation's way,
            -- not only the one(s) selected as this route's identity match
            -- (2026-10-14 decision).
            SELECT DISTINCT params.r_m, params.geometry_share,
                   patterns.network, patterns.pattern_id,
                   patterns.stop_sequence, dates.date_key
            FROM patterns CROSS JOIN dates CROSS JOIN match_params params
            JOIN read_parquet('{_sql_path(summary.distances_path)}') distances
              ON distances.date_key = dates.date_key
             AND distances.network = patterns.network
             AND distances.pattern_id = patterns.pattern_id
             AND distances.stop_sequence = patterns.stop_sequence
             AND NOT distances.is_fallback
             AND distances.in_service
             AND distances.distance_m <= params.r_m
            WHERE patterns.transport_mode IN ('tram', 'metro', 'rail')
        ),
        fallback_covered AS (
            SELECT DISTINCT params.r_m, params.geometry_share,
                   patterns.network, patterns.pattern_id,
                   patterns.stop_sequence, dates.date_key
            FROM patterns CROSS JOIN dates CROSS JOIN match_params params
            JOIN read_parquet('{_sql_path(summary.distances_path)}') distances
              ON distances.date_key = dates.date_key
             AND distances.network = patterns.network
             AND distances.pattern_id = patterns.pattern_id
             AND distances.stop_sequence = patterns.stop_sequence
             AND distances.is_fallback
             AND distances.distance_m <= params.r_m
            WHERE patterns.transport_mode IN ('tram', 'metro', 'rail')
              AND NOT EXISTS (
                  SELECT 1 FROM matches
                  WHERE matches.r_m = params.r_m
                    AND matches.geometry_share = params.geometry_share
                    AND matches.date_key = dates.date_key
                    AND matches.network = patterns.network
                    AND matches.pattern_id = patterns.pattern_id
              )
        ),
        flags AS (
            SELECT params.r_m, params.geometry_share, dates.date_key,
                   patterns.network, patterns.pattern_id, patterns.route_id,
                   patterns.transport_mode AS mode, patterns.is_bhns,
                   patterns.ordinal,
                   CASE
                       WHEN patterns.transport_mode IN ('tram', 'metro', 'rail')
                           THEN track.pattern_id IS NOT NULL
                                OR fallback.pattern_id IS NOT NULL
                       ELSE matched.pattern_id IS NOT NULL
                   END AS covered
            FROM patterns CROSS JOIN dates CROSS JOIN match_params params
            LEFT JOIN matched_covered matched
              ON matched.r_m = params.r_m
             AND matched.geometry_share = params.geometry_share
             AND matched.date_key = dates.date_key
             AND matched.network = patterns.network
             AND matched.pattern_id = patterns.pattern_id
             AND matched.stop_sequence = patterns.stop_sequence
            LEFT JOIN track_covered track
              ON track.r_m = params.r_m
             AND track.geometry_share = params.geometry_share
             AND track.date_key = dates.date_key
             AND track.network = patterns.network
             AND track.pattern_id = patterns.pattern_id
             AND track.stop_sequence = patterns.stop_sequence
            LEFT JOIN fallback_covered fallback
              ON fallback.r_m = params.r_m
             AND fallback.geometry_share = params.geometry_share
             AND fallback.date_key = dates.date_key
             AND fallback.network = patterns.network
             AND fallback.pattern_id = patterns.pattern_id
             AND fallback.stop_sequence = patterns.stop_sequence
        ),
        stats AS (
            SELECT r_m, geometry_share, date_key, network, pattern_id,
                   any_value(route_id) AS route_id, any_value(mode) AS mode,
                   any_value(is_bhns) AS is_bhns,
                   count(*) AS n, count(*) FILTER (WHERE covered) AS covered,
                   min(ordinal) FILTER (WHERE covered) AS first_covered,
                   max(ordinal) FILTER (WHERE covered) AS last_covered
            FROM flags
            GROUP BY r_m, geometry_share, date_key, network, pattern_id
        ),
        bounds AS (
            SELECT stats.*,
                   (mode IN ('tram', 'metro', 'rail')
                        OR (mode = 'bus' AND is_bhns)) AS fixed_guideway_like,
                   ks.k,
                   CASE WHEN (mode IN ('tram', 'metro', 'rail')
                                  OR (mode = 'bus' AND is_bhns))
                              AND coalesce(first_covered - 1, n) >= ks.k
                        THEN coalesce(first_covered, n + 1) ELSE 1 END AS start_idx,
                   CASE WHEN (mode IN ('tram', 'metro', 'rail')
                                  OR (mode = 'bus' AND is_bhns))
                              AND coalesce(n - last_covered, n) >= ks.k
                        THEN coalesce(last_covered, 0) ELSE n END AS end_idx
            FROM stats CROSS JOIN ks
        ),
        remaining AS (
            SELECT bounds.r_m, bounds.geometry_share, bounds.k,
                   bounds.date_key, bounds.network, bounds.pattern_id,
                   any_value(bounds.route_id) AS route_id,
                   any_value(bounds.mode) AS mode,
                   any_value(bounds.fixed_guideway_like) AS fixed_guideway_like,
                   any_value(bounds.n) AS original_n,
                   any_value(bounds.start_idx) AS start_idx,
                   any_value(bounds.end_idx) AS end_idx,
                   count(flags.ordinal) AS remaining_n,
                   count(flags.ordinal) FILTER (WHERE flags.covered)
                       AS remaining_covered
            FROM bounds
            LEFT JOIN flags
              ON flags.r_m = bounds.r_m
             AND flags.geometry_share = bounds.geometry_share
             AND flags.date_key = bounds.date_key
             AND flags.network = bounds.network
             AND flags.pattern_id = bounds.pattern_id
             AND flags.ordinal BETWEEN bounds.start_idx AND bounds.end_idx
            GROUP BY bounds.r_m, bounds.geometry_share, bounds.k,
                     bounds.date_key, bounds.network, bounds.pattern_id
        )
        SELECT remaining.r_m, remaining.geometry_share, remaining.k,
               thetas.theta, remaining.date_key, remaining.network,
               remaining.pattern_id, remaining.route_id, remaining.mode,
               match_meta.match_pass, match_meta.relation_ids,
               match_meta.relation_refs,
               CASE WHEN remaining.remaining_n > 0
                    THEN remaining.remaining_covered
                         / remaining.remaining_n::DOUBLE
                    ELSE 0.0 END AS covered_share,
               remaining.remaining_n, remaining.remaining_covered,
               remaining.start_idx - 1 AS start_index,
               greatest(remaining.end_idx - 1, 0) AS end_index,
               CASE
                   WHEN NOT network_status.testable THEN 'not-testable'
                   WHEN NOT remaining.fixed_guideway_like
                     THEN CASE
                       WHEN remaining.remaining_n > 0
                         AND remaining.remaining_covered
                             / remaining.remaining_n::DOUBLE >= thetas.theta
                       THEN CASE WHEN match_meta.match_pass = 'geometry'
                                 THEN 'kept-renamed' ELSE 'kept' END
                       ELSE 'dropped' END
                   WHEN remaining.remaining_n < 2
                     OR remaining.remaining_covered
                        / remaining.remaining_n::DOUBLE < thetas.theta
                     THEN 'dropped'
                   WHEN remaining.start_idx > 1
                     OR remaining.end_idx < remaining.original_n THEN 'cut'
                   WHEN match_meta.match_pass = 'geometry' THEN 'kept-renamed'
                   ELSE 'kept'
               END AS outcome
        FROM remaining CROSS JOIN thetas
        JOIN network_status
          ON network_status.r_m = remaining.r_m
         AND network_status.geometry_share = remaining.geometry_share
         AND network_status.date_key = remaining.date_key
         AND network_status.network = remaining.network
        LEFT JOIN match_meta
          ON match_meta.r_m = remaining.r_m
         AND match_meta.geometry_share = remaining.geometry_share
         AND match_meta.date_key = remaining.date_key
         AND match_meta.network = remaining.network
         AND match_meta.pattern_id = remaining.pattern_id
        ORDER BY remaining.r_m, remaining.geometry_share, remaining.k,
                 thetas.theta, remaining.date_key, remaining.network,
                 remaining.pattern_id
    """


def evaluate_cached_grid(
    connection: duckdb.DuckDBPyConnection,
    summary: PrecomputeSummary,
    config: GtfsRebuildConfig,
    *,
    r_values: list[int],
    k_values: list[int],
    theta_values: list[float],
    geometry_values: list[float],
) -> dict[
    tuple[str, int, int, float, float],
    tuple[list[CachedRouteRun], set[tuple[str, str]]],
]:
    """Evaluate many grid points in one geometry-free DuckDB query."""
    patterns = _pattern_lookup(connection, summary.patterns_path)
    rows = connection.execute(
        _bulk_evaluation_sql(
            summary,
            summary.dates,
            r_values,
            k_values,
            theta_values,
            geometry_values,
        )
    ).fetchall()
    evaluations: dict[
        tuple[str, int, int, float, float],
        tuple[list[CachedRouteRun], set[tuple[str, str]]],
    ] = {}
    for row in rows:
        (
            r_m,
            geometry_share,
            k,
            theta,
            date_key,
            network,
            pattern_id,
            route_id,
            mode,
            match_pass,
            relation_ids,
            relation_refs,
            covered_share,
            n,
            covered,
            start_index,
            end_index,
            outcome,
        ) = row
        family = "bus" if mode == "ferry" else mode
        key = (
            family,
            int(r_m),
            int(k),
            float(theta),
            float(geometry_share),
        )
        runs, flagged = evaluations.setdefault(key, ([], set()))
        pattern = patterns[(network, pattern_id)]
        ids = tuple(relation_ids or ())
        refs = tuple(relation_refs or ())
        expected, known, case_id = _expected(
            config, network, route_id, pattern.short_name, date_key
        )
        runs.append(
            CachedRouteRun(
                network,
                date_key,
                pattern,
                RelationMatch(match_pass, ids, refs, covered_share),
                RouteResult(
                    route_id,
                    outcome,
                    match_pass,
                    ids,
                    refs,
                    n,
                    covered,
                    covered_share,
                    start_index,
                    end_index,
                ),
                expected,
                known,
                case_id,
            )
        )
        if outcome == "not-testable":
            flagged.add((date_key, network))
    return evaluations


def evaluate_cached_grid_point(
    connection: duckdb.DuckDBPyConnection,
    summary: PrecomputeSummary,
    config: GtfsRebuildConfig,
    *,
    family: str,
    r_m: int,
    k: int,
    theta: float,
    geometry_share: float,
) -> tuple[list[CachedRouteRun], set[tuple[str, str]]]:
    """Evaluate one grid point using only cached scalar Parquet columns."""
    evaluations = evaluate_cached_grid(
        connection,
        summary,
        config,
        r_values=[r_m],
        k_values=[k],
        theta_values=[theta],
        geometry_values=[geometry_share],
    )
    return evaluations.get((family, r_m, k, theta, geometry_share), ([], set()))
