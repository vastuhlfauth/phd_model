"""Elevation and gradient processing for sections 8.1 and 9.3."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Sequence

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
import pyarrow.parquet as pq
from common.config import load_pilot_config
from common.duckdb_io import open_connection, write_parquet
from numba import njit

from mobgrid.energy.rates import EnergyConfig, load_energy_config
from mobgrid.osm.active_costs import _grade_report_lines, _summarize_clipped_grades
from mobgrid.osm.config import NetworkConfig, load_network_config

FloatArray = npt.NDArray[np.float64]
logger = logging.getLogger(__name__)

_PROFILE_COLUMNS = (
    "node_elevations_m",
    "elevation_from_m",
    "elevation_to_m",
    "climb_m",
    "descent_m",
    "mean_grade",
)
_WAY_BATCH_SIZE = 25_000


@njit(cache=True)
def _profile_integral(
    positions: FloatArray, heights: FloatArray, areas: FloatArray, at: float
) -> float:
    if at <= positions[0]:
        next_index = 1
        while next_index < len(positions) and positions[next_index] == positions[0]:
            next_index += 1
        slope = (heights[next_index] - heights[0]) / (
            positions[next_index] - positions[0]
        )
        delta = at - positions[0]
        return heights[0] * delta + slope * delta * delta / 2
    if at >= positions[-1]:
        previous = len(positions) - 2
        while previous >= 0 and positions[previous] == positions[-1]:
            previous -= 1
        slope = (heights[-1] - heights[previous]) / (
            positions[-1] - positions[previous]
        )
        delta = at - positions[-1]
        return areas[-1] + heights[-1] * delta + slope * delta * delta / 2
    index = np.searchsorted(positions, at, side="right") - 1
    delta = at - positions[index]
    slope = (heights[index + 1] - heights[index]) / (
        positions[index + 1] - positions[index]
    )
    return areas[index] + heights[index] * delta + slope * delta * delta / 2


@njit(cache=True)
def _smooth_ways(
    way_ids: npt.NDArray[np.int64],
    positions: FloatArray,
    heights: FloatArray,
    window_m: float,
) -> FloatArray:
    result = heights.copy()
    start = 0
    while start < len(heights):
        if not np.isfinite(heights[start]):
            start += 1
            continue
        end = start + 1
        while (
            end < len(heights)
            and way_ids[end] == way_ids[start]
            and np.isfinite(heights[end])
        ):
            end += 1
        x = positions[start:end]
        z = heights[start:end]
        if len(x) > 1 and x[-1] > x[0]:
            area = np.zeros(len(x), dtype=np.float64)
            for index in range(1, len(x)):
                area[index] = area[index - 1] + (
                    (z[index - 1] + z[index]) * (x[index] - x[index - 1]) / 2
                )
            for index in range(len(x)):
                left = x[index] - window_m / 2
                right = x[index] + window_m / 2
                result[start + index] = (
                    _profile_integral(x, z, area, right)
                    - _profile_integral(x, z, area, left)
                ) / window_m
        start = end
    return result


def smooth_elevation_profile(
    distances_m: FloatArray, elevations_m: FloatArray, window_m: float
) -> FloatArray:
    """Average a piecewise-linear elevation profile over a distance window (8.1).

    Positions and elevations are metres. Endpoint slopes extend beyond each
    complete run so the averaging window preserves a uniform slope.
    """
    distances = np.asarray(distances_m, dtype=np.float64)
    elevations = np.asarray(elevations_m, dtype=np.float64)
    if (
        distances.ndim != 1 or elevations.ndim != 1
        or distances.shape != elevations.shape
        or not np.isfinite(distances).all()
        or np.any(np.diff(distances) < 0)
        or not np.isfinite(window_m) or window_m <= 0
    ):
        raise ValueError("profile needs ordered distances and a positive window")
    return _smooth_ways(
        np.zeros(len(distances), dtype=np.int64), distances, elevations, window_m
    )


@dataclass(frozen=True)
class _Grid:
    path: Path
    columns: int
    rows: int
    x_center: float
    y_center: float
    cellsize: float
    nodata: float


def _read_header(path: Path) -> _Grid:
    """Read ESRI ASCII grid geometry in Lambert-93 metres."""
    header: dict[str, float] = {}
    with path.open(encoding="ascii") as stream:
        for _ in range(6):
            fields = stream.readline().split()
            if len(fields) != 2:
                raise ValueError(f"invalid ASCII grid header in {path}")
            header[fields[0].lower()] = float(fields[1])
    try:
        columns = int(header["ncols"])
        rows = int(header["nrows"])
        cellsize = header["cellsize"]
        x_center = (
            header["xllcenter"]
            if "xllcenter" in header
            else header["xllcorner"] + cellsize / 2
        )
        y_center = (
            header["yllcenter"]
            if "yllcenter" in header
            else header["yllcorner"] + cellsize / 2
        )
        nodata = header["nodata_value"]
    except KeyError as exc:
        raise ValueError(f"missing ASCII grid header in {path}: {exc}") from exc
    if columns < 1 or rows < 1 or cellsize <= 0:
        raise ValueError(f"invalid ASCII grid dimensions in {path}")
    return _Grid(path, columns, rows, x_center, y_center, cellsize, nodata)


def sample_elevations(
    paths: Sequence[str | Path], x_m: FloatArray, y_m: FloatArray
) -> FloatArray:
    """Bilinearly sample Lambert-93 coordinates, returning metres or NaN (8.1).

    Interpolation uses cell centres and can cross aligned tile boundaries.
    A missing or no-data neighbour makes the sample NaN unless its weight is
    zero. Callers can pass chunks to limit memory use.
    """
    x = np.asarray(x_m, dtype=np.float64)
    y = np.asarray(y_m, dtype=np.float64)
    if x.ndim != 1 or x.shape != y.shape:
        raise ValueError("x and y must be equally sized one-dimensional arrays")
    if not paths:
        raise ValueError("no elevation grids supplied")
    grids = [_read_header(Path(path)) for path in paths]
    base = grids[0]
    for grid in grids[1:]:
        if not (
            grid.cellsize == base.cellsize
            and ((grid.x_center - base.x_center) / base.cellsize).is_integer()
            and ((grid.y_center - base.y_center) / base.cellsize).is_integer()
        ):
            raise ValueError(f"unaligned ASCII grid: {grid.path}")
    fx = (x - base.x_center) / base.cellsize
    fy = (y - base.y_center) / base.cellsize
    lower_x = np.floor(fx)
    lower_y = np.floor(fy)
    dx = fx - lower_x
    dy = fy - lower_y
    # CRS round-trips can move exact cell centers a fraction of a millimetre.
    dx[np.isclose(dx, 0, atol=1e-4, rtol=0)] = 0
    dx[np.isclose(dx, 1, atol=1e-4, rtol=0)] = 1
    dy[np.isclose(dy, 0, atol=1e-4, rtol=0)] = 0
    dy[np.isclose(dy, 1, atol=1e-4, rtol=0)] = 1
    values = np.full((len(x), 4), np.nan)
    xs = np.stack((lower_x, lower_x + 1, lower_x, lower_x + 1), axis=1)
    ys = np.stack((lower_y, lower_y, lower_y + 1, lower_y + 1), axis=1)
    for grid in grids:
        x_offset = round((grid.x_center - base.x_center) / base.cellsize)
        y_offset = round((grid.y_center - base.y_center) / base.cellsize)
        valid = (
            np.isfinite(xs) & np.isfinite(ys)
            & (xs >= x_offset) & (xs < x_offset + grid.columns)
            & (ys >= y_offset) & (ys < y_offset + grid.rows)
            & np.isnan(values)
        )
        row_indices, corners = np.nonzero(valid)
        if not len(row_indices):
            continue
        column = (xs[row_indices, corners] - x_offset).astype(np.int64)
        row = grid.rows - 1 - (
            ys[row_indices, corners] - y_offset
        ).astype(np.int64)
        sampled = _read_grid_samples(grid, row, column)
        sampled[sampled == grid.nodata] = np.nan
        values[row_indices, corners] = sampled
    weights = np.stack(
        ((1 - dx) * (1 - dy), dx * (1 - dy), (1 - dx) * dy, dx * dy),
        axis=1,
    )
    contributions = np.where(weights == 0, 0, values * weights)
    return np.sum(contributions, axis=1)


def nodes_without_tile(
    paths: Sequence[str | Path], x_m: FloatArray, y_m: FloatArray
) -> int:
    """Count coordinates outside every ASCII-grid cell footprint."""
    x = np.asarray(x_m, dtype=np.float64)
    y = np.asarray(y_m, dtype=np.float64)
    if x.ndim != 1 or x.shape != y.shape:
        raise ValueError("x and y must be equally sized one-dimensional arrays")
    if not paths:
        raise ValueError("no elevation grids supplied")
    covered = np.zeros(len(x), dtype=np.bool_)
    for path in paths:
        grid = _read_header(Path(path))
        covered |= (
            (x >= grid.x_center - grid.cellsize / 2)
            & (x < grid.x_center + (grid.columns - 0.5) * grid.cellsize)
            & (y >= grid.y_center - grid.cellsize / 2)
            & (y < grid.y_center + (grid.rows - 0.5) * grid.cellsize)
        )
    return int(np.count_nonzero(~covered))


def _file_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary.replace(path)


def _sample_nodes_with_checkpoint(
    nodes: Path,
    grids: Sequence[Path],
    node_ids: npt.NDArray[np.int64],
    x: FloatArray,
    y: FloatArray,
    cache_directory: Path | None,
) -> tuple[FloatArray, int]:
    """Sample nodes, reusing a complete raster checkpoint when inputs match."""
    signature = {
        "nodes": _file_signature(nodes),
        "grids": [_file_signature(path) for path in grids],
    }
    if cache_directory is not None:
        cache_directory.mkdir(parents=True, exist_ok=True)
        data_path = cache_directory / "sampled_nodes.parquet"
        metadata_path = cache_directory / "sampled_nodes.json"
        if data_path.is_file() and metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if (
                metadata["signature"] == signature
                and metadata["output"] == _file_signature(data_path)
            ):
                table = pq.read_table(data_path)
                cached_ids = table["node_id"].to_numpy(zero_copy_only=False)
                if not np.array_equal(cached_ids, node_ids):
                    raise ValueError(
                        "elevation sample checkpoint node ids do not match"
                    )
                logger.info("reusing node elevation checkpoint %s", data_path)
                return (
                    np.asarray(
                        table["elevation_m"].to_numpy(zero_copy_only=False),
                        dtype=np.float64,
                    ),
                    int(metadata["nodes_without_tile"]),
                )
    elevations = sample_elevations(grids, x, y)
    uncovered = nodes_without_tile(grids, x, y)
    if cache_directory is not None:
        temporary = data_path.with_name(data_path.stem + ".tmp.parquet")
        try:
            pq.write_table(pa.table({
                "node_id": pa.array(node_ids, type=pa.int64()),
                "elevation_m": pa.array(
                    elevations, mask=~np.isfinite(elevations), type=pa.float64()
                ),
            }), temporary)
            temporary.replace(data_path)
        finally:
            temporary.unlink(missing_ok=True)
        _write_json(metadata_path, {
            "signature": signature,
            "output": _file_signature(data_path),
            "nodes_without_tile": uncovered,
        })
    return elevations, uncovered


def _read_grid_samples(
    grid: _Grid, requested_rows: np.ndarray, requested_columns: np.ndarray
) -> FloatArray:
    """Read only requested ASCII-grid rows, keeping raster memory bounded."""
    sampled = np.full(len(requested_rows), np.nan, dtype=np.float64)
    order = np.argsort(requested_rows, kind="stable")
    sorted_rows = requested_rows[order]
    unique_rows, starts, counts = np.unique(
        sorted_rows, return_index=True, return_counts=True
    )
    with grid.path.open(encoding="ascii") as stream:
        for _ in range(6):
            stream.readline()
        current_row = 0
        for row_index, start, count in zip(
            unique_rows, starts, counts, strict=True
        ):
            while current_row < row_index:
                if not stream.readline():
                    raise ValueError(
                        f"ASCII grid data is truncated: {grid.path}"
                    )
                current_row += 1
            line = stream.readline()
            if not line:
                raise ValueError(f"ASCII grid data is truncated: {grid.path}")
            current_row += 1
            data = np.fromstring(line, sep=" ", dtype=np.float64)
            if len(data) != grid.columns:
                raise ValueError(
                    f"ASCII grid dimensions do not match data: {grid.path}"
                )
            request_indices = order[start : start + count]
            sampled[request_indices] = data[requested_columns[request_indices]]
    return sampled


@dataclass(frozen=True)
class ElevationProfile:
    """Directional edge elevation statistics in metres and dimensionless grade."""

    elevation_from_m: float | None
    elevation_to_m: float | None
    climb_m: float | None
    descent_m: float | None
    mean_grade: float | None


@dataclass(frozen=True)
class ElevationSummary:
    """Counts for one directed-edge elevation enrichment."""

    edge_count: int
    nodes_without_elevation: int
    nodes_without_tile: int
    edges_without_profile: int
    bridge_length_m: float = 0.0
    tunnel_length_m: float = 0.0
    climb_by_mode: dict[str, tuple[float, float]] = field(default_factory=dict)
    incomplete_by_mode: dict[str, int] = field(default_factory=dict)
    clipped_segments_by_class: dict[tuple[str, str], tuple[int, float]] = field(
        default_factory=dict
    )
    longest_clipped_edges: tuple[tuple[str, int, str, str, float, float], ...] = ()


def _smooth_way_elevations(
    connection: duckdb.DuckDBPyConnection, window_m: float, temporary_source: Path
) -> None:
    """Smooth complete runs in bounded batches, in metres (8.1)."""
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _osm_smoothed_elevations (
            way_id BIGINT, node_sequence BIGINT, elevation_m DOUBLE
        )
    """)
    write_parquet(connection, """
        SELECT way_id, node_sequence, distance_m, elevation_m
        FROM _osm_way_elevations ORDER BY way_id, node_sequence
    """, temporary_source)
    reader_connection = connection.cursor()
    reader = reader_connection.execute(
        f"SELECT * FROM read_parquet('{_sql_path(temporary_source)}') "
        "ORDER BY way_id, node_sequence"
    ).to_arrow_reader(batch_size=_WAY_BATCH_SIZE)
    pending: pa.Table | None = None

    def insert_batch(table: pa.Table) -> None:
        ids = np.asarray(table["way_id"].to_numpy(zero_copy_only=False), dtype=np.int64)
        positions = np.asarray(
            table["distance_m"].to_numpy(zero_copy_only=False), dtype=np.float64
        )
        heights = np.asarray(
            table["elevation_m"].to_numpy(zero_copy_only=False), dtype=np.float64
        )
        smoothed = _smooth_ways(ids, positions, heights, window_m)
        result = pa.table({
            "way_id": table["way_id"],
            "node_sequence": table["node_sequence"],
            "elevation_m": pa.array(smoothed, mask=~np.isfinite(smoothed)),
        })
        connection.register("_osm_smoothing_batch", result)
        try:
            connection.execute(
                "INSERT INTO _osm_smoothed_elevations "
                "SELECT * FROM _osm_smoothing_batch"
            )
        finally:
            connection.unregister("_osm_smoothing_batch")

    try:
        for batch in reader:
            table = pa.Table.from_batches([batch])
            if pending is not None:
                table = pa.concat_tables([pending, table])
            ids = np.asarray(
                table["way_id"].to_numpy(zero_copy_only=False), dtype=np.int64
            )
            split = int(np.searchsorted(ids, ids[-1], side="left"))
            if split:
                insert_batch(table.slice(0, split))
            pending = table.slice(split)
        if pending is not None and pending.num_rows:
            insert_batch(pending)
    finally:
        reader_connection.close()
        temporary_source.unlink(missing_ok=True)
    connection.execute("""
        ALTER TABLE _osm_way_elevations ADD COLUMN smoothed_elevation_m DOUBLE;
        UPDATE _osm_way_elevations AS w SET smoothed_elevation_m = s.elevation_m
        FROM _osm_smoothed_elevations s
        WHERE w.way_id = s.way_id AND w.node_sequence = s.node_sequence
    """)


def _prepare_way_elevations(
    connection: duckdb.DuckDBPyConnection,
    ways: Path,
    nodes: Path,
    edges: Path,
    smoothing_window_m: float,
    smoothing_source: Path,
) -> tuple[float, float]:
    """Interpolate bridge and tunnel profiles along full OSM ways (8.1)."""
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_way_elevations AS
        WITH points AS (
            SELECT w.way_id, ref.node_sequence, ref.node_id,
                   n.x, n.y, n.graph_node, s.elevation_m,
                   coalesce(lower(trim(w.tags['bridge'])) <> 'no', false) AS bridge,
                   coalesce(lower(trim(w.tags['tunnel'])) <> 'no', false) AS tunnel,
                   lag(n.x) OVER way_order AS previous_x,
                   lag(n.y) OVER way_order AS previous_y
            FROM read_parquet('{_sql_path(ways)}') w
            SEMI JOIN (
                SELECT DISTINCT way_id FROM read_parquet('{_sql_path(edges)}')
            ) e USING (way_id)
            CROSS JOIN UNNEST(w.refs) WITH ORDINALITY AS ref(node_id, node_sequence)
            LEFT JOIN read_parquet('{_sql_path(nodes)}') n USING (node_id)
            LEFT JOIN _osm_sampled_node_elevations s USING (node_id)
            WINDOW way_order AS (PARTITION BY w.way_id ORDER BY ref.node_sequence)
        ), distances AS (
            SELECT *, sum(
                CASE WHEN node_sequence = 1 THEN 0
                     ELSE sqrt(pow(x - previous_x, 2) + pow(y - previous_y, 2))
                END
            ) OVER way_order AS distance_m,
            count(*) OVER (PARTITION BY way_id) AS node_count,
            first(elevation_m) OVER whole_way AS start_m,
            last(elevation_m) OVER whole_way AS end_m
            FROM points
            WINDOW way_order AS (PARTITION BY way_id ORDER BY node_sequence),
                   whole_way AS (
                       PARTITION BY way_id ORDER BY node_sequence
                       ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                   )
        ), profiles AS (
            SELECT *, max(distance_m) OVER (PARTITION BY way_id) AS length_m,
                   count(x) OVER (PARTITION BY way_id) = node_count AS has_coordinates
            FROM distances
        )
        SELECT way_id, node_sequence, node_id, x, y, graph_node, distance_m,
               bridge, tunnel, length_m,
               CASE
                 WHEN NOT (bridge OR tunnel)
                      OR node_sequence = 1 OR node_sequence = node_count
                 THEN elevation_m
                 WHEN has_coordinates AND length_m > 0
                 THEN start_m + (end_m - start_m) * distance_m / length_m
               END AS elevation_m
        FROM profiles
    """)
    invalid = connection.execute("""
        SELECT count(*) FROM _osm_way_elevations
        WHERE x IS NULL OR y IS NULL OR graph_node IS NULL
    """).fetchone()[0]
    if invalid:
        raise ValueError(f"{invalid} way nodes lack coordinates or graph-node status")
    bridge, tunnel = connection.execute("""
        SELECT coalesce(sum(length_m) FILTER (WHERE bridge), 0),
               coalesce(sum(length_m) FILTER (WHERE tunnel), 0)
        FROM (
            SELECT way_id, first(bridge) AS bridge, first(tunnel) AS tunnel,
                   first(length_m) AS length_m,
                   count(elevation_m) = count(*) AS complete
            FROM _osm_way_elevations GROUP BY way_id
        )
        WHERE complete AND length_m > 0
    """).fetchone()
    _smooth_way_elevations(connection, smoothing_window_m, smoothing_source)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _osm_way_segment_elevations AS
        WITH numbered AS (
            SELECT *,
                   sum(CASE WHEN graph_node THEN 1 ELSE 0 END) OVER (
                       PARTITION BY way_id ORDER BY node_sequence
                   ) AS graph_count,
                   max(node_sequence) OVER (PARTITION BY way_id) AS last_sequence
            FROM _osm_way_elevations
        ), segment_points AS (
            SELECT *, graph_count - 1 AS segment_index
            FROM numbered WHERE NOT graph_node OR node_sequence < last_sequence
            UNION ALL
            SELECT *, graph_count - 2 AS segment_index
            FROM numbered WHERE graph_node AND graph_count > 1
        )
        SELECT *, row_number() OVER segment_order AS segment_ordinal,
               count(*) OVER (PARTITION BY way_id, segment_index) AS segment_count
        FROM segment_points
        WINDOW segment_order AS (
            PARTITION BY way_id, segment_index ORDER BY node_sequence
        )
    """)
    return float(bridge), float(tunnel)


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def enrich_edges_with_elevation(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    nodes_path: str | Path,
    elevation_paths: Sequence[str | Path],
    *,
    ways_path: str | Path,
    way_elevations_path: str | Path,
    network: NetworkConfig,
    energy: EnergyConfig,
    cache_directory: Path | None = None,
) -> ElevationSummary:
    """Add directional profiles to the edge table in EPSG:3035 metres (8.1)."""
    edges = Path(edges_path)
    nodes = Path(nodes_path)
    ways = Path(ways_path)
    way_elevations = Path(way_elevations_path)
    smoothing_window_m = network.elevation_smoothing_window_m
    if not np.isfinite(smoothing_window_m) or smoothing_window_m <= 0:
        raise ValueError("elevation smoothing window must be positive")
    if way_elevations.resolve() in (edges.resolve(), nodes.resolve(), ways.resolve()):
        raise ValueError("way elevation output must be separate from input tables")
    if not edges.is_file():
        raise FileNotFoundError(edges)
    if not nodes.is_file():
        raise FileNotFoundError(nodes)
    if not ways.is_file():
        raise FileNotFoundError(ways)
    grids = [Path(path) for path in elevation_paths]
    if not grids:
        raise ValueError("no BD ALTI ASCII grids supplied")
    missing_grids = [path for path in grids if not path.is_file()]
    if missing_grids:
        raise FileNotFoundError(missing_grids[0])

    connection.execute("LOAD spatial")
    node_table = connection.execute(f"""
        SELECT node_id,
               ST_X(ST_Transform(
                   ST_Point(x, y), 'EPSG:3035', 'EPSG:2154', true
               )) AS x,
               ST_Y(ST_Transform(
                   ST_Point(x, y), 'EPSG:3035', 'EPSG:2154', true
               )) AS y
        FROM read_parquet('{_sql_path(nodes)}')
        ORDER BY node_id
    """).to_arrow_table()
    node_ids = node_table.column("node_id").to_numpy(zero_copy_only=False)
    x = node_table.column("x").to_numpy(zero_copy_only=False)
    y = node_table.column("y").to_numpy(zero_copy_only=False)
    elevations, uncovered_nodes = _sample_nodes_with_checkpoint(
        nodes, grids, node_ids, x, y, cache_directory
    )
    sampled_nodes = pa.table(
        {
            "node_id": pa.array(node_ids, type=pa.int64()),
            "elevation_m": pa.array(
                elevations,
                mask=~np.isfinite(elevations),
                type=pa.float64(),
            ),
        }
    )
    connection.register("_osm_sampled_node_elevations", sampled_nodes)
    temporary = edges.with_name(edges.stem + ".elevation.tmp.parquet")
    temporary_nodes = nodes.with_name(nodes.stem + ".elevation.tmp.parquet")
    temporary_ways = way_elevations.with_name(
        way_elevations.stem + ".elevation.tmp.parquet"
    )
    smoothing_source = way_elevations.with_name(
        way_elevations.stem + ".smoothing.tmp.parquet"
    )
    way_elevations.parent.mkdir(parents=True, exist_ok=True)
    try:
        edge_source = _sql_path(edges)
        node_source = _sql_path(nodes)
        bridge_length, tunnel_length = _prepare_way_elevations(
            connection, ways, nodes, edges, smoothing_window_m, smoothing_source
        )
        mismatch = connection.execute(f"""
            SELECT count(*)
            FROM read_parquet('{edge_source}') e
            CROSS JOIN UNNEST(e.node_ids) WITH ORDINALITY AS ref(node_id, ordinal)
            LEFT JOIN _osm_way_segment_elevations p
              ON p.way_id = e.way_id
             AND p.segment_index = try_cast(split_part(e.edge_key, ':', 2) AS BIGINT)
             AND p.segment_ordinal = CASE WHEN e.is_forward THEN ref.ordinal
                 ELSE p.segment_count - ref.ordinal + 1 END
            WHERE p.node_id IS NULL OR p.node_id <> ref.node_id
               OR p.segment_count <> len(e.node_ids)
        """).fetchone()[0]
        if mismatch:
            raise ValueError(f"{mismatch} edge nodes do not match their way profiles")
        write_parquet(
            connection,
            "SELECT way_id, node_sequence, node_id, distance_m, "
            "elevation_m AS raw_elevation_m, smoothed_elevation_m AS elevation_m "
            "FROM _osm_way_elevations ORDER BY way_id, node_sequence",
            temporary_ways,
        )
        node_columns = [
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{node_source}')"
            ).fetchall()
            if row[0] != "elevation_m"
        ]
        node_projection = ", ".join(
            f"n.{_sql_identifier(column)}" for column in node_columns
        )
        write_parquet(
            connection,
            f"""
            SELECT {node_projection}, sampled.elevation_m
            FROM read_parquet('{node_source}') n
            LEFT JOIN _osm_sampled_node_elevations sampled USING (node_id)
            """,
            temporary_nodes,
        )
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _osm_edge_elevation_profiles AS
            WITH ordered_nodes AS (
                SELECT e.edge_key, edge_node.node_sequence,
                       n.x, n.y, p.smoothed_elevation_m AS elevation_m,
                       p.elevation_m AS raw_elevation_m,
                       lag(n.x) OVER edge_order AS previous_x,
                       lag(n.y) OVER edge_order AS previous_y,
                       lag(p.smoothed_elevation_m) OVER edge_order
                           AS previous_elevation_m,
                       lag(p.elevation_m) OVER edge_order
                           AS previous_raw_elevation_m
                FROM read_parquet('{edge_source}') e
                CROSS JOIN UNNEST(e.node_ids) WITH ORDINALITY
                    AS edge_node(node_id, node_sequence)
                JOIN read_parquet('{node_source}') n USING (node_id)
                JOIN _osm_way_segment_elevations p
                  ON p.way_id = e.way_id
                 AND p.segment_index = try_cast(
                     split_part(e.edge_key, ':', 2) AS BIGINT
                 )
                 AND p.segment_ordinal = CASE WHEN e.is_forward
                     THEN edge_node.node_sequence
                     ELSE p.segment_count - edge_node.node_sequence + 1 END
                WINDOW edge_order AS (
                    PARTITION BY e.edge_key ORDER BY edge_node.node_sequence
                )
            ),
            edge_stats AS (
                SELECT edge_key,
                       list(elevation_m ORDER BY node_sequence) AS node_elevations_m,
                       first(elevation_m ORDER BY node_sequence)
                           AS elevation_from_m,
                       last(elevation_m ORDER BY node_sequence)
                           AS elevation_to_m,
                       count(elevation_m) = count(*) AS has_complete_profile,
                       sum(
                           CASE WHEN node_sequence > 1
                                THEN sqrt(
                                    pow(x - previous_x, 2)
                                    + pow(y - previous_y, 2)
                                )
                           END
                       ) AS horizontal_length_m,
                       sum(greatest(elevation_m - previous_elevation_m, 0))
                           AS climb_m,
                       sum(greatest(
                           raw_elevation_m - previous_raw_elevation_m, 0
                       )) AS raw_climb_m,
                       sum(greatest(previous_elevation_m - elevation_m, 0))
                           AS descent_m
                FROM ordered_nodes
                GROUP BY edge_key
            )
            SELECT edge_key, node_elevations_m, elevation_from_m, elevation_to_m,
                   CASE WHEN has_complete_profile THEN climb_m END AS climb_m,
                   CASE WHEN has_complete_profile THEN raw_climb_m END AS raw_climb_m,
                   CASE WHEN has_complete_profile THEN descent_m END
                       AS descent_m,
                   CASE
                     WHEN has_complete_profile AND horizontal_length_m > 0
                     THEN (elevation_to_m - elevation_from_m)
                          / horizontal_length_m
                   END AS mean_grade
            FROM edge_stats
        """)
        climb_rows = connection.execute(f"""
                SELECT e.mode, coalesce(sum(p.raw_climb_m), 0),
                       coalesce(sum(p.climb_m), 0),
                       count(*) FILTER (WHERE p.climb_m IS NULL)
                FROM read_parquet('{edge_source}') e
                LEFT JOIN _osm_edge_elevation_profiles p USING (edge_key)
                GROUP BY e.mode ORDER BY e.mode
            """).fetchall()
        climb_by_mode = {
            mode: (float(before), float(after))
            for mode, before, after, _ in climb_rows
        }
        incomplete_by_mode = {
            mode: int(incomplete) for mode, _, _, incomplete in climb_rows
        }
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _osm_clipped_grades AS
            WITH points AS (
                SELECT e.edge_key, e.way_id, e.mode,
                       lower(trim(coalesce(e.highway, ''))) AS highway,
                       e.length_m AS edge_length_m, ref.node_sequence,
                       n.x, n.y,
                       list_extract(p.node_elevations_m, ref.node_sequence) AS z,
                       lag(n.x) OVER edge_order AS previous_x,
                       lag(n.y) OVER edge_order AS previous_y,
                       lag(list_extract(
                           p.node_elevations_m, ref.node_sequence
                       )) OVER edge_order AS previous_z
                FROM read_parquet('{edge_source}') e
                JOIN _osm_edge_elevation_profiles p USING (edge_key)
                CROSS JOIN UNNEST(e.node_ids) WITH ORDINALITY
                    AS ref(node_id, node_sequence)
                JOIN read_parquet('{node_source}') n USING (node_id)
                WHERE e.mode IN ('foot', 'bike') AND p.climb_m IS NOT NULL
                WINDOW edge_order AS (
                    PARTITION BY e.edge_key ORDER BY ref.node_sequence
                )
            ), segments AS (
                SELECT *, sqrt(pow(x - previous_x, 2) + pow(y - previous_y, 2))
                    AS horizontal
                FROM points WHERE node_sequence > 1
            ), graded AS (
                SELECT *, (z - previous_z) / nullif(horizontal, 0) AS grade,
                       horizontal * edge_length_m / nullif(
                           sum(horizontal) OVER (PARTITION BY edge_key), 0
                       ) AS segment_length_m
                FROM segments
            )
            SELECT edge_key, way_id, mode, highway, edge_length_m,
                   segment_length_m, grade
            FROM graded
            WHERE (mode = 'foot' AND highway <> 'steps' AND (grade < ? OR grade > ?))
               OR (mode = 'bike' AND (grade < ? OR grade > ?))
        """, [
            *energy.walking.gradient_valid_range,
            network.bike_speed_table.grade_min,
            network.bike_speed_table.grade_max,
        ])
        clipped_by_class, longest_clipped = _summarize_clipped_grades(
            connection, "_osm_clipped_grades",
            network.bike_speed_table.clipped_grade_report_limit,
        )
        columns = [
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{edge_source}')"
            ).fetchall()
            if row[0] not in _PROFILE_COLUMNS
        ]
        projection = ", ".join(f"e.{_sql_identifier(column)}" for column in columns)
        profiles = ", ".join(
            f"p.{_sql_identifier(column)}" for column in _PROFILE_COLUMNS
        )
        write_parquet(
            connection,
            f"""
            SELECT {projection}, {profiles}
            FROM read_parquet('{edge_source}') e
            LEFT JOIN _osm_edge_elevation_profiles p USING (edge_key)
            """,
            temporary,
        )
        temporary_ways.replace(way_elevations)
        temporary_nodes.replace(nodes)
        temporary.replace(edges)
        if cache_directory is not None:
            sample_metadata = cache_directory / "sampled_nodes.json"
            metadata = json.loads(sample_metadata.read_text(encoding="utf-8"))
            metadata["signature"]["nodes"] = _file_signature(nodes)
            _write_json(sample_metadata, metadata)
        edge_count, missing_profiles = connection.execute(
            f"""
            SELECT count(*),
                   count(*) FILTER (WHERE climb_m IS NULL OR descent_m IS NULL)
            FROM read_parquet('{_sql_path(edges)}')
            """
        ).fetchone()
    finally:
        connection.unregister("_osm_sampled_node_elevations")
        temporary.unlink(missing_ok=True)
        temporary_nodes.unlink(missing_ok=True)
        temporary_ways.unlink(missing_ok=True)
        smoothing_source.unlink(missing_ok=True)

    return ElevationSummary(
        int(edge_count),
        int(np.count_nonzero(~np.isfinite(elevations))),
        uncovered_nodes,
        int(missing_profiles),
        bridge_length,
        tunnel_length,
        climb_by_mode,
        incomplete_by_mode,
        clipped_by_class,
        longest_clipped,
    )


def write_elevation_report(
    summary: ElevationSummary,
    path: str | Path,
    *,
    state: int,
    area: str,
    tile_count: int,
) -> None:
    """Write the directed-edge elevation and no-coverage counts (8.1)."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    climb_lines = "\n".join(
        f"  - {mode}: {values[0]:,.1f} / {values[1]:,.1f}; "
        f"incomplete: {summary.incomplete_by_mode[mode]:,}"
        for mode, values in summary.climb_by_mode.items()
    )
    grade_lines = "\n".join(_grade_report_lines(
        summary.clipped_segments_by_class, summary.longest_clipped_edges
    ))
    destination.write_text(
        f"""# OSM elevation profiles ({state}, {area})

- BD ALTI ASCII tiles: {tile_count:,}
- Directed edge profiles: {summary.edge_count:,}
- Nodes with no covering tile: {summary.nodes_without_tile:,}
- Nodes with no valid elevation sample: {summary.nodes_without_elevation:,}
- Edges with incomplete elevation profiles: {summary.edges_without_profile:,}
- Bridge length interpolated: {summary.bridge_length_m:,.1f} m
- Tunnel length interpolated: {summary.tunnel_length_m:,.1f} m
- Directed climb by mode, before / after smoothing (m):
{climb_lines}
- Units: metres; mean grade is dimensionless.

## Grades to clip in active costs

{grade_lines}
""",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.elevation")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument(
        "--network-config", type=Path, default=Path("config/network.yaml")
    )
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    parser.add_argument(
        "--energy-config", type=Path, default=Path("config/energy.yaml")
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser


def _completion_signature(
    ways: Path,
    grids: Sequence[Path],
    edges: Path,
    nodes: Path,
    way_elevations: Path,
    report: Path,
    network: NetworkConfig,
    energy: EnergyConfig,
) -> dict[str, object]:
    """Fingerprint completed outputs, source files and relevant settings."""
    return {
        "version": 1,
        "ways": _file_signature(ways),
        "grids": [_file_signature(path) for path in grids],
        "edges": _file_signature(edges),
        "nodes": _file_signature(nodes),
        "way_elevations": _file_signature(way_elevations),
        "report": _file_signature(report),
        "window_m": network.elevation_smoothing_window_m,
        "walking_range": list(energy.walking.gradient_valid_range),
        "bike_range": [
            network.bike_speed_table.grade_min,
            network.bike_speed_table.grade_max,
        ],
        "report_limit": network.bike_speed_table.clipped_grade_report_limit,
    }


def main(argv: list[str] | None = None) -> int:
    """Sample BD ALTI and add elevation fields to the configured edge table."""
    args = _parser().parse_args(argv)
    network = load_network_config(args.network_config)
    energy = load_energy_config(args.energy_config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in network.states:
        raise ValueError(f"unsupported state {args.state}")
    root = args.pilot_config.resolve().parent.parent
    nodes_path = (
        root / pilot.paths["base"] / "network" / str(args.state) / args.area
        / "nodes.parquet"
    )
    edges_path = nodes_path.with_name("edges.parquet")
    tile_directory = root / pilot.paths["interim"] / "bdalti"
    ways_path = (
        root / pilot.paths["interim"] / "osm" / str(args.state) / args.area
        / "ways.parquet"
    )
    elevation_paths = sorted(tile_directory.rglob("*.asc"))
    if not elevation_paths:
        raise FileNotFoundError(
            f"no unpacked BD ALTI ASCII grids found under {tile_directory}"
        )
    report_path = args.report or Path(
        f"docs/data/step06_elevation_{args.area}_{args.state}.md"
    )
    way_elevations = nodes_path.with_name("way_elevations.parquet")
    cache_directory = ways_path.parent / "elevation"
    checkpoint = cache_directory / "completed.json"
    task = f"osm_elevation_{args.state}_{args.area}"
    log_path = args.log or root / "logs" / f"{date.today().isoformat()}_{task}.log"
    summary_path = (
        args.summary or root / "logs" / f"{date.today().isoformat()}_{task}_summary.md"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    started = time.perf_counter()
    try:
        required = (ways_path, edges_path, nodes_path, way_elevations, report_path)
        reused = False
        if checkpoint.is_file() and all(path.is_file() for path in required):
            previous = json.loads(checkpoint.read_text(encoding="utf-8"))
            reused = previous == _completion_signature(
                ways_path, elevation_paths, edges_path, nodes_path, way_elevations,
                report_path, network, energy,
            )
        if reused:
            logger.info("reusing completed elevation outputs")
        else:
            connection = open_connection()
            try:
                summary = enrich_edges_with_elevation(
                    connection, edges_path, nodes_path, elevation_paths,
                    ways_path=ways_path,
                    way_elevations_path=way_elevations,
                    network=network,
                    energy=energy,
                    cache_directory=cache_directory,
                )
            finally:
                connection.close()
            write_elevation_report(
                summary, report_path, state=args.state, area=args.area,
                tile_count=len(elevation_paths),
            )
            cache_directory.mkdir(parents=True, exist_ok=True)
            _write_json(
                checkpoint,
                _completion_signature(
                    ways_path, elevation_paths, edges_path, nodes_path,
                    way_elevations, report_path, network, energy,
                ),
            )
        elapsed = time.perf_counter() - started
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            f"# OSM elevation run summary\n\n"
            f"- Inputs: `{ways_path}`, `{nodes_path}`, `{edges_path}`, "
            f"{len(elevation_paths):,} tiles under `{tile_directory}`\n"
            f"- Outputs: `{edges_path}`, `{nodes_path}`, `{way_elevations}`, "
            f"`{report_path}`\n"
            f"- Status: {'reused completed outputs' if reused else 'completed'}\n"
            f"- Elapsed: {elapsed:.1f} seconds\n"
            f"- Warnings and counts: see coverage and profile counts below.\n\n"
            + report_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        logger.info("wrote elevation summary %s in %.1f seconds", summary_path, elapsed)
        return 0
    finally:
        if sys.exc_info()[0] is not None:
            logger.error("elevation job failed", exc_info=True)
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    raise SystemExit(main())


def edge_elevation_profile(
    segment_lengths_m: FloatArray, elevations_m: FloatArray
) -> ElevationProfile:
    """Summarise ordered segment elevations and horizontal lengths (8.1, 9.3)."""
    lengths = np.asarray(segment_lengths_m, dtype=np.float64)
    heights = np.asarray(elevations_m, dtype=np.float64)
    if (
        lengths.ndim != 1 or heights.ndim != 1
        or len(heights) != len(lengths) + 1 or not len(lengths)
        or not np.isfinite(lengths).all() or np.any(lengths <= 0)
    ):
        raise ValueError("edge requires positive segment lengths and n+1 elevations")
    start = float(heights[0]) if np.isfinite(heights[0]) else None
    end = float(heights[-1]) if np.isfinite(heights[-1]) else None
    if not np.isfinite(heights).all():
        return ElevationProfile(start, end, None, None, None)
    differences = np.diff(heights)
    return ElevationProfile(
        start,
        end,
        float(np.maximum(differences, 0).sum()),
        float(np.maximum(-differences, 0).sum()),
        float((heights[-1] - heights[0]) / lengths.sum()),
    )
