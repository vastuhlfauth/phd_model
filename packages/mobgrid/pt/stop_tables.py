"""Public transport stop tables for section 8.6 and the rebuild test (5.6)."""

from __future__ import annotations

import csv
import shutil
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath

import duckdb
import pyarrow as pa

from mobgrid.pt.gtfs_clean import select_active_services

_GTFS_TABLE_NAMES = (
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "calendar.txt",
    "calendar_dates.txt",
)


def extract_gtfs_tables(zip_path: str | Path, destination: str | Path) -> None:
    """Extract only the GTFS metadata CSVs needed by ``load_gtfs_patterns``."""
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        members = {
            PurePosixPath(info.filename).name: info.filename
            for info in archive.infolist()
            if not info.is_dir()
        }
        for name in _GTFS_TABLE_NAMES:
            if name not in members:
                continue
            target_path = destination_path / name
            if target_path.is_file():
                continue
            temporary_path = target_path.with_suffix(".tmp")
            with (
                archive.open(members[name]) as source,
                temporary_path.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
            temporary_path.replace(target_path)


def _filter_rows_by_column(
    path: Path, column: str, keep_values: set[str], collect_column: str | None = None
) -> set[str]:
    """Rewrite a CSV in place, keeping only rows whose ``column`` matches.

    Streams row by row (never loads the file in memory), so a national
    feed's multi-gigabyte ``stop_times.txt`` is never fully parsed when
    only a handful of routes are needed (section 5.6's metro cases).
    Returns the set of values seen in ``collect_column`` (``column`` by
    default) among the kept rows.
    """
    filtered_path = path.with_suffix(".filtered.txt")
    seen: set[str] = set()
    with (
        path.open(newline="", encoding="utf-8-sig") as source,
        filtered_path.open("w", newline="", encoding="utf-8") as target,
    ):
        reader = csv.reader(source)
        header = next(reader)
        index = header.index(column)
        collect_index = header.index(collect_column or column)
        writer = csv.writer(target)
        writer.writerow(header)
        for row in reader:
            if row[index] in keep_values:
                writer.writerow(row)
                seen.add(row[collect_index])
    filtered_path.replace(path)
    return seen


def restrict_gtfs_tables_to_routes(
    gtfs_tables_dir: str | Path, route_ids: list[str]
) -> None:
    """Pre-filter ``trips.txt``/``stop_times.txt`` to the given route ids.

    Streams the filter in Python before DuckDB ever reads the files, so a
    national feed is not fully parsed just to keep a handful of metro
    routes (section 5.6's "Metros" calibration on IDFM/STAR Rennes).
    """
    directory = Path(gtfs_tables_dir)
    trips_path = directory / "trips.txt"
    if not trips_path.is_file():
        return
    trip_ids = _filter_rows_by_column(
        trips_path, "route_id", set(route_ids), collect_column="trip_id"
    )
    stop_times_path = directory / "stop_times.txt"
    if stop_times_path.is_file():
        _filter_rows_by_column(stop_times_path, "trip_id", trip_ids)


_LIFECYCLE_EXCLUSION_SQL = """
    len(list_filter(map_keys(tags), key ->
        starts_with(key, 'construction:') OR starts_with(key, 'proposed:')
        OR starts_with(key, 'disused:') OR starts_with(key, 'abandoned:')
    )) = 0
    AND coalesce(tags['railway'], '') != 'construction'
"""

_PT_TAG_FILTER_SQL = """
    (
        coalesce(tags['public_transport'], '')
            IN ('platform', 'stop_position', 'station')
        OR coalesce(tags['highway'], '') = 'bus_stop'
        OR coalesce(tags['railway'], '') IN ('station', 'halt', 'tram_stop', 'stop')
        OR coalesce(tags['amenity'], '') = 'bus_station'
    )
"""

_MODE_FAMILY_CASE_SQL = """
    CASE
        WHEN coalesce(tags['railway'], '') IN ('station', 'halt')
             AND coalesce(tags['station'], '') = 'subway' THEN 'metro'
        WHEN coalesce(tags['railway'], '') IN ('station', 'halt') THEN 'rail'
        WHEN coalesce(tags['railway'], '') IN ('tram_stop', 'stop') THEN 'tram'
        WHEN coalesce(tags['station'], '') = 'subway'
             OR coalesce(tags['subway'], '') = 'yes' THEN 'metro'
        WHEN coalesce(tags['light_rail'], '') = 'yes' THEN 'tram'
        WHEN coalesce(tags['highway'], '') = 'bus_stop'
             OR coalesce(tags['amenity'], '') = 'bus_station'
             OR coalesce(tags['bus'], '') = 'yes'
             OR coalesce(tags['trolleybus'], '') = 'yes' THEN 'bus'
        WHEN coalesce(tags['train'], '') = 'yes' THEN 'rail'
        ELSE NULL
    END
"""


def extract_osm_pt_stops(
    connection: duckdb.DuckDBPyConnection,
    pbf_path: str | Path,
    bboxes: list[tuple[float, float, float, float]] | None = None,
) -> duckdb.DuckDBPyRelation:
    """Public-transport stops of a dated OSM extract, projected to EPSG:3035.

    Implements section 5.6 point 1: nodes and ways tagged
    ``public_transport=platform|stop_position|station``,
    ``highway=bus_stop``, ``railway=station|halt|tram_stop|stop`` or
    ``amenity=bus_station``, excluding lifecycle-prefixed tags and
    ``railway=construction``. Ways use the centroid of their referenced
    nodes. Each stop carries a ``mode_family`` of bus, tram, metro or rail;
    stops with no identifiable mode are dropped. Columns: ``id`` (BIGINT),
    ``kind`` (node/way), ``mode_family``, ``x``, ``y`` (EPSG:3035 metres).

    ``bboxes`` is an optional list of ``(west, south, east, north)`` WGS84
    degree boxes; when given, only nodes inside at least one box are read
    (including for way centroids), which keeps a national extract fast when
    only a few local networks are needed. ``None`` scans the whole extract.
    Reads the PBF in three passes (coordinates for way centroids, matching
    ways, and matching nodes), the first two materialised to lean temp
    tables (no ``tags`` column on the much larger node-coordinates pass)
    so later steps never re-parse it and never carry a MAP per node.
    """
    connection.execute("INSTALL spatial")
    connection.execute("LOAD spatial")
    path = Path(pbf_path).as_posix()
    bbox_filter = "true"
    if bboxes is not None:
        bbox_filter = " OR ".join(
            f"(lon BETWEEN {west} AND {east} AND lat BETWEEN {south} AND {north})"
            for west, south, east, north in bboxes
        )
        if not bbox_filter:
            bbox_filter = "false"
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE osm_node_coords AS
        SELECT id, lon, lat
        FROM ST_ReadOSM('{path}')
        WHERE kind = 'node' AND ({bbox_filter})
    """)
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE osm_pt_ways AS
        SELECT id, refs, {_MODE_FAMILY_CASE_SQL} AS mode_family
        FROM ST_ReadOSM('{path}')
        WHERE kind = 'way' AND {_PT_TAG_FILTER_SQL} AND {_LIFECYCLE_EXCLUSION_SQL}
    """)
    connection.execute(f"""
        CREATE OR REPLACE TEMP VIEW osm_node_stops AS
        SELECT id, 'node' AS kind, {_MODE_FAMILY_CASE_SQL} AS mode_family, lon, lat
        FROM ST_ReadOSM('{path}')
        WHERE kind = 'node' AND ({bbox_filter})
          AND {_PT_TAG_FILTER_SQL} AND {_LIFECYCLE_EXCLUSION_SQL}
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP VIEW osm_way_stops AS
        SELECT way.id, 'way' AS kind, any_value(way.mode_family) AS mode_family,
               avg(node.lon) AS lon, avg(node.lat) AS lat
        FROM osm_pt_ways AS way, UNNEST(way.refs) AS ref(node_id)
        JOIN osm_node_coords AS node ON node.id = ref.node_id
        GROUP BY way.id
    """)
    return connection.sql("""
        SELECT id, kind, mode_family,
               ST_X(ST_Transform(
                   ST_Point(lon, lat), 'EPSG:4326', 'EPSG:3035', true)) AS x,
               ST_Y(ST_Transform(
                   ST_Point(lon, lat), 'EPSG:4326', 'EPSG:3035', true)) AS y
        FROM (SELECT * FROM osm_node_stops UNION ALL SELECT * FROM osm_way_stops)
        WHERE mode_family IS NOT NULL
    """)


def write_osm_pt_stops_cache(
    connection: duckdb.DuckDBPyConnection,
    pbf_path: str | Path,
    cache_path: str | Path,
    bboxes: list[tuple[float, float, float, float]] | None = None,
) -> None:
    """Extract once and cache OSM public-transport stops as Parquet."""
    relation = extract_osm_pt_stops(connection, pbf_path, bboxes)
    destination = Path(cache_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    relation.write_parquet(str(destination))


def read_osm_pt_stops_cache(
    connection: duckdb.DuckDBPyConnection, cache_path: str | Path
) -> duckdb.DuckDBPyRelation:
    """Read previously cached OSM public-transport stops; never reads a PBF."""
    return connection.read_parquet(str(cache_path))


_ROUTE_TYPE_FAMILY: dict[int, str] = {
    0: "tram",
    1: "metro",
    2: "rail",
    3: "bus",
    4: "ferry",
    5: "tram",  # cable tram
    6: "metro",  # aerial lift: grouped with metro-like fixed guideway.
    7: "metro",  # funicular
    11: "bus",  # trolleybus
    12: "metro",  # monorail
}


def _mode_family_from_route_type(route_type: int | None) -> str | None:
    """Map a GTFS ``route_type`` to a rebuild mode family (section 5.6)."""
    if route_type is None:
        return None
    if route_type in _ROUTE_TYPE_FAMILY:
        return _ROUTE_TYPE_FAMILY[route_type]
    if 100 <= route_type <= 117 or 400 <= route_type <= 405:
        return "rail"
    if 200 <= route_type <= 209:
        return "bus"
    if 700 <= route_type <= 716:
        return "bus"
    if 900 <= route_type <= 906:
        return "tram"
    if 1000 <= route_type <= 1021:
        return "ferry"
    if 1300 <= route_type <= 1307:
        return "metro"
    if 1400 <= route_type <= 1402:
        return "metro"
    return None


def _transport_mode_from_route_type(route_type: int | None) -> str | None:
    """Map GTFS route type to the exact mode used for OSM relation matching."""
    return _mode_family_from_route_type(route_type)


def register_mode_family_udf(connection: duckdb.DuckDBPyConnection) -> None:
    """Register ``gtfs_mode_family(route_type)``, once per connection."""
    existing = connection.execute(
        "SELECT count(*) FROM duckdb_functions() "
        "WHERE function_name = 'gtfs_mode_family'"
    ).fetchone()[0]
    if existing:
        return
    connection.create_function(
        "gtfs_mode_family", _mode_family_from_route_type, [int], str
    )


def load_gtfs_patterns(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: str | Path,
    reference_date: date,
    *,
    route_ids: list[str] | None = None,
) -> pa.Table:
    """Patterns (route, direction, distinct ordered stop sequence) active on one date.

    Reads GTFS metadata CSVs already extracted to ``gtfs_tables_dir`` (see
    ``extract_gtfs_tables`` above). One row per
    (pattern_id, stop_sequence) in EPSG:3035, with the pattern's
    ``mode_family`` from its GTFS ``route_type``. ``route_ids`` restricts to
    a subset of routes and, for a national/regional feed, pre-filters
    ``trips.txt``/``stop_times.txt`` on disk first (``restrict_gtfs_tables_
    to_routes``) so a multi-gigabyte file is never fully parsed by DuckDB.
    """
    directory = Path(gtfs_tables_dir)
    if route_ids is not None:
        restrict_gtfs_tables_to_routes(directory, route_ids)
    connection.execute("INSTALL spatial")
    connection.execute("LOAD spatial")
    register_mode_family_udf(connection)
    for name in (
        "agency", "routes", "trips", "stops", "stop_times", "calendar",
        "calendar_dates",
    ):
        path = directory / f"{name}.txt"
        if path.is_file():
            connection.read_csv(
                str(path), header=True, all_varchar=True, delimiter=","
            ).create_view(name)
    route_columns = {
        row[0] for row in connection.execute("DESCRIBE routes").fetchall()
    }
    agency_columns = {
        row[0] for row in connection.execute("DESCRIBE agency").fetchall()
    }
    agency_id = (
        "routes.agency_id"
        if "agency_id" in route_columns
        else "NULL"
    )
    short_name = (
        "routes.route_short_name"
        if "route_short_name" in route_columns
        else "CAST(NULL AS VARCHAR)"
    )
    long_name = (
        "routes.route_long_name"
        if "route_long_name" in route_columns
        else "CAST(NULL AS VARCHAR)"
    )
    description = (
        "routes.route_desc"
        if "route_desc" in route_columns
        else "CAST(NULL AS VARCHAR)"
    )
    agency_join = (
        f"LEFT JOIN agency ON {agency_id} = agency.agency_id"
        if "agency_id" in agency_columns and "agency_id" in route_columns
        else "LEFT JOIN agency ON true"
    )
    select_active_services(connection, reference_date)
    route_filter = ""
    if route_ids is not None:
        id_list = ", ".join(f"'{route_id}'" for route_id in route_ids)
        route_filter = f"AND trips.route_id IN ({id_list})"
    return connection.sql(f"""
        WITH active_trips AS (
            SELECT trips.trip_id, trips.route_id,
                   coalesce(trips.direction_id, '0') AS direction_id
            FROM trips
            JOIN active_services USING (service_id)
            WHERE true {route_filter}
        ),
        trip_stop_sequences AS (
            SELECT active_trips.trip_id, active_trips.route_id,
                   active_trips.direction_id,
                   list(stop_times.stop_id ORDER BY
                        CAST(stop_times.stop_sequence AS INTEGER)) AS stop_sequence
            FROM active_trips
            JOIN stop_times USING (trip_id)
            GROUP BY active_trips.trip_id, active_trips.route_id,
                     active_trips.direction_id
        ),
        trip_stop_sequences_hashed AS (
            SELECT *, hash(stop_sequence) AS sequence_hash
            FROM trip_stop_sequences
        ),
        patterns AS (
            SELECT route_id, direction_id, sequence_hash,
                   any_value(stop_sequence) AS stop_sequence,
                   route_id || ':' || direction_id || ':' || sequence_hash
                       AS pattern_id,
                   count(*) AS trip_count
            FROM trip_stop_sequences_hashed
            GROUP BY route_id, direction_id, sequence_hash
        )
        SELECT patterns.pattern_id, patterns.route_id, patterns.direction_id,
               gtfs_mode_family(TRY_CAST(routes.route_type AS INTEGER)) AS mode_family,
               gtfs_mode_family(TRY_CAST(routes.route_type AS INTEGER))
                   AS transport_mode,
               {short_name} AS route_short_name,
               {long_name} AS route_long_name,
               {description} AS route_desc,
               agency.agency_name,
               patterns.trip_count,
               CAST(ordinal AS INTEGER) AS stop_sequence,
               stops.stop_id,
               CAST(stops.stop_lon AS DOUBLE) AS lon,
               CAST(stops.stop_lat AS DOUBLE) AS lat,
               ST_X(ST_Transform(
                   ST_Point(
                       CAST(stops.stop_lon AS DOUBLE), CAST(stops.stop_lat AS DOUBLE)
                   ),
                   'EPSG:4326', 'EPSG:3035', true)) AS x,
               ST_Y(ST_Transform(
                   ST_Point(
                       CAST(stops.stop_lon AS DOUBLE), CAST(stops.stop_lat AS DOUBLE)
                   ),
                   'EPSG:4326', 'EPSG:3035', true)) AS y
        FROM patterns,
             UNNEST(patterns.stop_sequence) WITH ORDINALITY AS u(stop_id, ordinal)
        JOIN stops ON stops.stop_id = u.stop_id
        JOIN routes ON routes.route_id = patterns.route_id
        {agency_join}
        ORDER BY patterns.pattern_id, ordinal
    """).to_arrow_table()
