"""Resumable DuckDB extraction of public-transport OSM route relations."""

from __future__ import annotations

import ctypes
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)
_ROUTE_TYPES = (
    "bus",
    "trolleybus",
    "coach",
    "tram",
    "subway",
    "light_rail",
    "train",
    "monorail",
    "ferry",
)


@dataclass(frozen=True)
class ExtractionSettings:
    """DuckDB resource settings used by a national extraction."""

    memory_limit: str
    temp_directory: Path


@dataclass(frozen=True)
class RelationMember:
    """One ordered OSM relation member."""

    relation_id: int
    sequence: int
    member_id: int
    member_type: str
    role: str


@dataclass(frozen=True)
class ExtractionSummary:
    """Persistent summary of one dated extraction run."""

    input_path: str
    output_path: str
    elapsed_seconds: float
    peak_memory_bytes: int | None
    input_bytes: int
    relation_count: int
    way_count: int
    stop_count: int
    warnings: tuple[str, ...]


def memory_limit_gib(total_memory_bytes: int) -> float:
    """Return 60% of physical RAM in GiB."""
    return round(total_memory_bytes * 0.6 / 1024**3, 1)


def _physical_memory_bytes() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if os.name == "nt" and ctypes.windll.kernel32.GlobalMemoryStatusEx(
        ctypes.byref(status)
    ):
        return int(status.total_physical)
    return 8 * 1024**3


def configure_extraction_connection(
    connection: duckdb.DuckDBPyConnection,
    interim_root: str | Path,
    *,
    total_memory_bytes: int | None = None,
) -> ExtractionSettings:
    """Set the extraction memory cap and disk-spill directory."""
    total_memory = total_memory_bytes or _physical_memory_bytes()
    memory_limit = f"{memory_limit_gib(total_memory):.1f}GiB"
    temp_directory = Path(interim_root) / "osm_pt_routes" / "_duckdb_temp"
    temp_directory.mkdir(parents=True, exist_ok=True)
    escaped_temp = str(temp_directory).replace("'", "''")
    connection.execute(f"SET memory_limit = '{memory_limit}'")
    connection.execute(f"SET temp_directory = '{escaped_temp}'")
    return ExtractionSettings(memory_limit, temp_directory)


def relation_members(
    relation_id: int,
    refs: list[int],
    ref_types: list[str],
    ref_roles: list[str],
) -> list[RelationMember]:
    """Zip ST_ReadOSM relation arrays without losing order, type, or role."""
    if not (len(refs) == len(ref_types) == len(ref_roles)):
        raise ValueError("OSM relation member arrays have different lengths")
    return [
        RelationMember(relation_id, index, member_id, member_type, role)
        for index, (member_id, member_type, role) in enumerate(
            zip(refs, ref_types, ref_roles, strict=True), start=1
        )
    ]


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _copy_sql(query: str, path: Path) -> str:
    return (
        f"COPY ({query}) TO '{_sql_path(path)}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD)"
    )


def _stage(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    query: str,
) -> None:
    if path.is_file():
        logger.info("checkpoint exists, skipping %s", path.name)
        return
    temporary = path.with_suffix(".tmp.parquet")
    connection.execute(_copy_sql(query, temporary))
    temporary.replace(path)


_WAYS_REQUIRED_COLUMNS = frozenset((
    "relation_id", "sequence", "role", "way_id", "railway", "highway",
    "busway", "lanes_bus", "construction", "opening_date", "start_date",
    "lifecycle", "points", "geometry",
))


def _invalidate_stale_ways_cache(
    connection: duckdb.DuckDBPyConnection, path: Path
) -> None:
    """Delete a cached ``ways.parquet`` missing newly required columns.

    Keeps ``ways_raw.parquet``/``nodes_raw.parquet``/``members.parquet``
    (the expensive PBF-scan stages) untouched, so a schema upgrade such as
    adding bus-infrastructure tag columns only redoes the cheap final join,
    not the national PBF scan.
    """
    if not path.is_file():
        return
    existing = {
        row[0]
        for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_path(path)}')"
        ).fetchall()
    }
    if not _WAYS_REQUIRED_COLUMNS <= existing:
        logger.info(
            "ways.parquet schema is stale (missing %s), rebuilding from "
            "cached stages: %s",
            _WAYS_REQUIRED_COLUMNS - existing,
            path,
        )
        path.unlink()


def _route_filter_sql() -> str:
    route_types = ", ".join(f"'{route_type}'" for route_type in _ROUTE_TYPES)
    return (
        "kind = 'relation' AND tags['type'] = 'route' "
        f"AND tags['route'] IN ({route_types})"
    )


def extract_osm_pt_routes(
    pbf_path: str | Path,
    output_directory: str | Path,
    *,
    summary_path: str | Path | None = None,
) -> ExtractionSummary:
    """Extract all PT route relations in three filtered PBF passes.

    The PBF is scanned for route relations, their member ways, and the nodes
    needed by those members. Every completed Parquet stage is reused on rerun.
    Geometries are EPSG:3035 WKB.
    """
    started = time.perf_counter()
    source = Path(pbf_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    stages = output / "_stages"
    stages.mkdir(exist_ok=True)
    connection = duckdb.connect()
    configure_extraction_connection(connection, output.parents[1])
    connection.execute("LOAD spatial")
    pbf = _sql_path(source)
    relations_raw = stages / "relations_raw.parquet"
    members = output / "members.parquet"
    ways_raw = stages / "ways_raw.parquet"
    nodes_raw = stages / "nodes_raw.parquet"

    _stage(
        connection,
        relations_raw,
        "SELECT id, tags, refs, ref_types, ref_roles "
        f"FROM ST_ReadOSM('{pbf}') WHERE {_route_filter_sql()}",
    )
    relations_source = _sql_path(relations_raw)
    _stage(
        connection,
        members,
        """
        SELECT id AS relation_id, ordinal AS sequence,
               list_extract(refs, ordinal) AS member_id,
               list_extract(ref_types, ordinal) AS member_type,
               coalesce(list_extract(ref_roles, ordinal), '') AS role
        FROM read_parquet('{relations}')
        CROSS JOIN UNNEST(generate_series(1, len(refs))) AS member(ordinal)
        """.format(relations=relations_source),
    )
    members_source = _sql_path(members)
    _stage(
        connection,
        ways_raw,
        "SELECT id, tags, refs FROM ST_ReadOSM("
        f"'{pbf}') WHERE kind = 'way' AND id IN "
        f"(SELECT member_id FROM read_parquet('{members_source}') "
        "WHERE member_type = 'way')",
    )
    ways_source = _sql_path(ways_raw)
    _stage(
        connection,
        nodes_raw,
        "WITH needed AS ("
        f"SELECT member_id AS id FROM read_parquet('{members_source}') "
        "WHERE member_type = 'node' UNION "
        f"SELECT unnest(refs) AS id FROM read_parquet('{ways_source}')) "
        f"SELECT id, tags, lat, lon FROM ST_ReadOSM('{pbf}') "
        "WHERE kind = 'node' AND id IN (SELECT id FROM needed)",
    )
    nodes_source = _sql_path(nodes_raw)
    _stage(
        connection,
        output / "relations.parquet",
        "SELECT id AS relation_id, tags['ref'] AS ref, tags['name'] AS name, "
        "tags['network'] AS network, tags['operator'] AS operator, "
        f"tags['route'] AS route FROM read_parquet('{relations_source}')",
    )
    _invalidate_stale_ways_cache(connection, output / "ways.parquet")
    _stage(
        connection,
        output / "ways.parquet",
        """
        WITH points AS (
            SELECT m.relation_id, m.sequence, m.role, w.id AS way_id, w.tags,
                   ordinal AS node_sequence,
                   ST_Transform(ST_Point(n.lon, n.lat),
                                'EPSG:4326', 'EPSG:3035', true) AS point
            FROM read_parquet('{members}') m
            JOIN read_parquet('{ways}') w ON w.id = m.member_id
            CROSS JOIN UNNEST(w.refs) WITH ORDINALITY AS ref(node_id, ordinal)
            JOIN read_parquet('{nodes}') n ON n.id = ref.node_id
            WHERE m.member_type = 'way'
        )
        SELECT relation_id, sequence, role, way_id,
               any_value(tags['railway']) AS railway,
               any_value(tags['highway']) AS highway,
               any_value(tags['busway']) AS busway,
               any_value(tags['lanes:bus']) AS lanes_bus,
               any_value(tags['construction']) AS construction,
               any_value(tags['opening_date']) AS opening_date,
               any_value(tags['start_date']) AS start_date,
               bool_or(len(list_filter(map_keys(tags), key ->
                   starts_with(key, 'construction:')
                   OR starts_with(key, 'proposed:')
                   OR starts_with(key, 'disused:')
                   OR starts_with(key, 'abandoned:'))) > 0) AS lifecycle,
               list(struct_pack(x := ST_X(point), y := ST_Y(point))
                    ORDER BY node_sequence) AS points,
               ST_AsWKB(ST_MakeLine(list(point ORDER BY node_sequence))) AS geometry
        FROM points
        GROUP BY relation_id, sequence, role, way_id
        """.format(members=members_source, ways=ways_source, nodes=nodes_source),
    )
    _stage(
        connection,
        output / "stops.parquet",
        """
        SELECT m.relation_id, m.sequence, m.role, n.id AS node_id,
               n.tags['public_transport'] AS public_transport,
               n.tags['railway'] AS railway, n.tags['highway'] AS highway,
               ST_X(ST_Transform(ST_Point(n.lon, n.lat),
                   'EPSG:4326', 'EPSG:3035', true)) AS x,
               ST_Y(ST_Transform(ST_Point(n.lon, n.lat),
                   'EPSG:4326', 'EPSG:3035', true)) AS y,
               ST_AsWKB(ST_Transform(ST_Point(n.lon, n.lat),
                   'EPSG:4326', 'EPSG:3035', true)) AS geometry
        FROM read_parquet('{members}') m
        JOIN read_parquet('{nodes}') n ON n.id = m.member_id
        WHERE m.member_type = 'node'
          AND (m.role IN ('stop', 'platform', 'stop_entry_only',
                          'stop_exit_only', 'platform_entry_only',
                          'platform_exit_only')
               OR n.tags['public_transport'] IN ('stop_position', 'platform'))
        """.format(members=members_source, nodes=nodes_source),
    )
    counts = {}
    for name in ("relations", "ways", "stops"):
        parquet = _sql_path(output / f"{name}.parquet")
        counts[name] = connection.execute(
            f"SELECT count(*) FROM read_parquet('{parquet}')"
        ).fetchone()[0]
    summary = ExtractionSummary(
        str(source),
        str(output),
        time.perf_counter() - started,
        process_peak_memory_bytes(),
        source.stat().st_size,
        counts["relations"],
        counts["ways"],
        counts["stops"],
        (),
    )
    if summary_path is not None:
        write_extraction_summary(summary, summary_path)
    (output / "_SUCCESS.json").write_text(
        json.dumps(asdict(summary), indent=2), encoding="utf-8"
    )
    return summary


def process_peak_memory_bytes() -> int | None:
    """Return peak working-set bytes for the current process on Windows."""
    if os.name != "nt":
        return None

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = ctypes.c_void_p
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemoryCounters),
        ctypes.c_ulong,
    ]
    if get_process_memory_info(
        get_current_process(), ctypes.byref(counters), counters.cb
    ):
        return int(counters.peak_working_set_size)
    return None


def write_extraction_summary(
    summary: ExtractionSummary, path: str | Path
) -> None:
    """Write the required long-job Markdown summary."""
    peak = (
        f"{summary.peak_memory_bytes / 1024**3:.2f} GiB"
        if summary.peak_memory_bytes is not None
        else "not available"
    )
    text = f"""# OSM PT route extraction summary

- Input: `{summary.input_path}` ({summary.input_bytes:,} bytes)
- Output: `{summary.output_path}`
- Elapsed: {summary.elapsed_seconds:.1f} seconds
- Peak process memory: {peak}
- Relations: {summary.relation_count:,}
- Member ways: {summary.way_count:,}
- Member stops/platforms: {summary.stop_count:,}
- Warnings: {", ".join(summary.warnings) if summary.warnings else "none"}
"""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def estimate_run(
    smoke: ExtractionSummary, target_input_bytes: int
) -> tuple[float, int | None]:
    """Scale runtime and a conservative memory upper bound by input size."""
    scale = target_input_bytes / smoke.input_bytes
    peak = (
        int(smoke.peak_memory_bytes * scale)
        if smoke.peak_memory_bytes is not None
        else None
    )
    return smoke.elapsed_seconds * scale, peak
