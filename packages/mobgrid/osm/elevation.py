"""Elevation and gradient processing for sections 8.1 and 9.3."""

from __future__ import annotations

import argparse
import binascii
import json
import logging
import struct
import sys
import time
import zlib
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


@dataclass(frozen=True)
class TileClimb:
    """Complete directed car-edge climb and length within one 10 km tile."""

    tile_id: int
    easting_m: int
    northing_m: int
    climb_m: float
    edge_length_m: float
    incomplete_edges: int

    @property
    def climb_per_km(self) -> float | None:
        if self.edge_length_m <= 0:
            return None
        return self.climb_m * 1000 / self.edge_length_m


@dataclass(frozen=True)
class ElevationSensitivity:
    """Directed car climb per kilometre under alternative smoothing windows."""

    windows_m: tuple[float, ...]
    pilot_climb_per_km: dict[float, float | None]
    tiles_by_window: dict[float, tuple[TileClimb, ...]]
    reference_zones: dict[str, dict[float, float | None]]


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
        CREATE OR REPLACE TEMP TABLE _osm_way_elevations AS
        SELECT w.*, s.elevation_m AS smoothed_elevation_m
        FROM _osm_way_elevations w
        LEFT JOIN _osm_smoothed_elevations s
          ON w.way_id = s.way_id AND w.node_sequence = s.node_sequence
    """)


def _prepare_way_elevations(
    connection: duckdb.DuckDBPyConnection,
    ways: Path,
    edges: Path,
    smoothing_window_m: float,
    smoothing_source: Path,
) -> tuple[float, float]:
    """Interpolate bridge and tunnel profiles along full OSM ways (8.1)."""
    started = time.perf_counter()
    logger.info("building way elevation profiles")
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
            LEFT JOIN _osm_nodes n USING (node_id)
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
    logger.info(
        "way elevation profiles completed in %.2f s", time.perf_counter() - started
    )
    started = time.perf_counter()
    logger.info("smoothing way elevations")
    _smooth_way_elevations(connection, smoothing_window_m, smoothing_source)
    logger.info("way smoothing completed in %.2f s", time.perf_counter() - started)
    started = time.perf_counter()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _osm_way_segment_elevations AS
        WITH numbered AS (
            SELECT *,
                   sum(CASE WHEN graph_node THEN 1 ELSE 0 END) OVER (
                       PARTITION BY way_id ORDER BY node_sequence
                   ) AS graph_count,
                   max(node_sequence) OVER (
                       PARTITION BY way_id
                   ) AS last_sequence
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
    logger.info("way segmentation completed in %.2f s", time.perf_counter() - started)
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

    started = time.perf_counter()
    logger.info("loading and projecting elevation nodes")
    connection.execute("LOAD spatial")
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _osm_nodes AS
        SELECT node_id, x, y, graph_node FROM read_parquet('{_sql_path(nodes)}')
    """)
    node_table = connection.execute("""
        SELECT node_id,
               ST_X(ST_Transform(
                   ST_Point(x, y), 'EPSG:3035', 'EPSG:2154', true
               )) AS x,
               ST_Y(ST_Transform(
                   ST_Point(x, y), 'EPSG:3035', 'EPSG:2154', true
               )) AS y
        FROM _osm_nodes
        ORDER BY node_id
    """).to_arrow_table()
    node_ids = node_table.column("node_id").to_numpy(zero_copy_only=False)
    x = node_table.column("x").to_numpy(zero_copy_only=False)
    y = node_table.column("y").to_numpy(zero_copy_only=False)
    logger.info("node projection completed in %.2f s", time.perf_counter() - started)
    started = time.perf_counter()
    logger.info("sampling node elevations")
    elevations, uncovered_nodes = _sample_nodes_with_checkpoint(
        nodes, grids, node_ids, x, y, cache_directory
    )
    logger.info("elevation sampling completed in %.2f s", time.perf_counter() - started)
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
            connection, ways, edges, smoothing_window_m, smoothing_source
        )
        started = time.perf_counter()
        logger.info("writing way and node elevation outputs")
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _osm_profile_edges AS
            SELECT edge_key, way_id, is_forward, node_ids, mode, highway, length_m,
                   try_cast(split_part(edge_key, ':', 2) AS BIGINT) AS segment_index
            FROM read_parquet('{edge_source}')
        """)
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
        logger.info(
            "way and node output completed in %.2f s", time.perf_counter() - started
        )
        started = time.perf_counter()
        logger.info("building segment and directed elevation profiles")
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_segment_profile_points AS
            SELECT way_id, segment_index, segment_ordinal, node_id,
                   smoothed_elevation_m AS elevation_m,
                   elevation_m AS raw_elevation_m,
                   sqrt(pow(x - lag(x) OVER segment_order, 2)
                      + pow(y - lag(y) OVER segment_order, 2)) AS horizontal,
                   smoothed_elevation_m
                       - lag(smoothed_elevation_m) OVER segment_order AS delta,
                   elevation_m - lag(elevation_m) OVER segment_order AS raw_delta
            FROM _osm_way_segment_elevations
            WINDOW segment_order AS (
                PARTITION BY way_id, segment_index ORDER BY segment_ordinal
            )
        """)
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_segment_elevation_profiles AS
            WITH stats AS (
                SELECT way_id, segment_index,
                       list(node_id ORDER BY segment_ordinal) AS node_ids,
                       list(elevation_m ORDER BY segment_ordinal) AS node_elevations_m,
                       first(elevation_m ORDER BY segment_ordinal) AS elevation_from_m,
                       last(elevation_m ORDER BY segment_ordinal) AS elevation_to_m,
                       count(elevation_m) = count(*) AS complete,
                       sum(horizontal) AS horizontal_length_m,
                       sum(greatest(delta, 0)) AS climb_m,
                       sum(greatest(-delta, 0)) AS descent_m,
                       sum(greatest(raw_delta, 0)) AS raw_climb_m,
                       sum(greatest(-raw_delta, 0)) AS raw_descent_m
                FROM _osm_segment_profile_points
                GROUP BY way_id, segment_index
            )
            SELECT way_id, segment_index, node_ids, node_elevations_m,
                   elevation_from_m, elevation_to_m, horizontal_length_m,
                   CASE WHEN complete THEN climb_m END AS climb_m,
                   CASE WHEN complete THEN descent_m END AS descent_m,
                   CASE WHEN complete THEN raw_climb_m END AS raw_climb_m,
                   CASE WHEN complete THEN raw_descent_m END AS raw_descent_m,
                   CASE WHEN complete AND horizontal_length_m > 0
                        THEN (elevation_to_m - elevation_from_m) / horizontal_length_m
                   END AS mean_grade
            FROM stats
        """)
        mismatch = connection.execute("""
            SELECT count(*) FROM _osm_profile_edges e
            LEFT JOIN _osm_segment_elevation_profiles p USING (way_id, segment_index)
            WHERE p.node_ids IS NULL OR e.node_ids IS DISTINCT FROM
                CASE WHEN e.is_forward THEN p.node_ids ELSE list_reverse(p.node_ids) END
        """).fetchone()[0]
        if mismatch:
            raise ValueError(f"{mismatch} edge nodes do not match their way profiles")
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_edge_elevation_profiles AS
            SELECT e.edge_key,
                   CASE WHEN e.is_forward THEN p.node_elevations_m
                        ELSE list_reverse(p.node_elevations_m) END AS node_elevations_m,
                   CASE WHEN e.is_forward THEN p.elevation_from_m
                        ELSE p.elevation_to_m END AS elevation_from_m,
                   CASE WHEN e.is_forward THEN p.elevation_to_m
                        ELSE p.elevation_from_m END AS elevation_to_m,
                   CASE WHEN e.is_forward THEN p.climb_m
                        ELSE p.descent_m END AS climb_m,
                   CASE WHEN e.is_forward THEN p.descent_m
                        ELSE p.climb_m END AS descent_m,
                   CASE WHEN e.is_forward THEN p.raw_climb_m
                        ELSE p.raw_descent_m END AS raw_climb_m,
                   CASE WHEN e.is_forward THEN p.mean_grade
                        ELSE -p.mean_grade END AS mean_grade
            FROM _osm_profile_edges e
            LEFT JOIN _osm_segment_elevation_profiles p USING (way_id, segment_index)
        """)
        logger.info(
            "elevation profiles completed in %.2f s", time.perf_counter() - started
        )
        started = time.perf_counter()
        logger.info("summarizing elevation climbs and clipped grades")
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
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_segment_clipped_grades AS
            SELECT way_id, segment_index, horizontal,
                   delta / nullif(horizontal, 0) AS grade
            FROM _osm_segment_profile_points
            WHERE segment_ordinal > 1 AND horizontal > 0
              AND (delta / horizontal < greatest(?, -?, ?, -?)
                   OR delta / horizontal > least(?, -?, ?, -?))
        """, [
            energy.walking.gradient_valid_range[0],
            energy.walking.gradient_valid_range[1],
            network.bike_speed_table.grade_min,
            network.bike_speed_table.grade_max,
            energy.walking.gradient_valid_range[1],
            energy.walking.gradient_valid_range[0],
            network.bike_speed_table.grade_max,
            network.bike_speed_table.grade_min,
        ])
        connection.execute("""
            CREATE OR REPLACE TEMP TABLE _osm_clipped_grades AS
            WITH graded AS (
                SELECT e.edge_key, e.way_id, e.mode,
                       lower(trim(coalesce(e.highway, ''))) AS highway,
                       e.length_m AS edge_length_m,
                       s.horizontal * e.length_m / nullif(p.horizontal_length_m, 0)
                           AS segment_length_m,
                       CASE WHEN e.is_forward THEN s.grade ELSE -s.grade END AS grade
                FROM _osm_profile_edges e
                JOIN _osm_segment_elevation_profiles p USING (way_id, segment_index)
                JOIN _osm_segment_clipped_grades s USING (way_id, segment_index)
                WHERE e.mode IN ('foot', 'bike') AND p.climb_m IS NOT NULL
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
        logger.info(
            "elevation diagnostics completed in %.2f s", time.perf_counter() - started
        )
        started = time.perf_counter()
        logger.info("writing directed elevation profiles")
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
        logger.info(
            "elevation output completed in %.2f s", time.perf_counter() - started
        )
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


def _compute_elevation_sensitivity(
    connection: duckdb.DuckDBPyConnection,
    edges_path: Path,
    nodes_path: Path,
    way_elevations_path: Path,
    windows_m: tuple[float, ...],
    *,
    flat_tiles: tuple[int, ...],
    hilly_tiles: tuple[int, ...],
) -> ElevationSensitivity:
    """Measure car climb in metres per kilometre without changing profiles (8.1)."""
    edges_source = _sql_path(edges_path)
    nodes_source = _sql_path(nodes_path)
    profiles_source = _sql_path(way_elevations_path)
    smoothing_source = way_elevations_path.with_name(
        way_elevations_path.stem + ".sensitivity.tmp.parquet"
    )
    tiles_by_window: dict[float, tuple[TileClimb, ...]] = {}
    pilot_climb_per_km: dict[float, float | None] = {}
    try:
        for window_m in windows_m:
            connection.execute(f"""
                CREATE OR REPLACE TEMP TABLE _osm_way_elevations AS
                SELECT p.way_id, p.node_sequence, p.node_id, p.distance_m,
                       n.graph_node, p.raw_elevation_m AS elevation_m
                FROM read_parquet('{profiles_source}') p
                JOIN read_parquet('{nodes_source}') n USING (node_id)
            """)
            if window_m == 0:
                connection.execute("""
                    CREATE OR REPLACE TEMP TABLE _osm_way_elevations AS
                    SELECT *, elevation_m AS smoothed_elevation_m
                    FROM _osm_way_elevations
                """)
            else:
                _smooth_way_elevations(connection, window_m, smoothing_source)

            connection.execute("""
                CREATE OR REPLACE TEMP TABLE _osm_sensitivity_segments AS
                WITH numbered AS (
                    SELECT *,
                           sum(CASE WHEN graph_node THEN 1 ELSE 0 END) OVER (
                               PARTITION BY way_id ORDER BY node_sequence
                           ) AS graph_count,
                           max(node_sequence) OVER (
                               PARTITION BY way_id
                           ) AS last_sequence
                    FROM _osm_way_elevations
                ), segment_points AS (
                    SELECT *, graph_count - 1 AS segment_index
                    FROM numbered
                    WHERE NOT graph_node OR node_sequence < last_sequence
                    UNION ALL
                    SELECT *, graph_count - 2 AS segment_index
                    FROM numbered
                    WHERE graph_node AND graph_count > 1
                ), deltas AS (
                    SELECT *,
                           smoothed_elevation_m - lag(smoothed_elevation_m) OVER (
                               PARTITION BY way_id, segment_index
                               ORDER BY node_sequence
                           ) AS delta
                    FROM segment_points
                )
                SELECT way_id, segment_index,
                       CASE WHEN count(smoothed_elevation_m) = count(*)
                            THEN sum(greatest(delta, 0)) END AS climb_m,
                       CASE WHEN count(smoothed_elevation_m) = count(*)
                            THEN sum(greatest(-delta, 0)) END AS descent_m
                FROM deltas
                GROUP BY way_id, segment_index
            """)
            connection.execute(f"""
                CREATE OR REPLACE TEMP TABLE _osm_sensitivity_edge_rows AS
                WITH car_edges AS (
                    SELECT edge_key, way_id,
                           try_cast(split_part(edge_key, ':', 2) AS BIGINT)
                               AS segment_index,
                           is_forward, length_m,
                           list_extract(node_ids, 1) AS from_node_id,
                           list_extract(node_ids, -1) AS to_node_id
                    FROM read_parquet('{edges_source}')
                    WHERE mode = 'car'
                ), located AS (
                    SELECT e.*,
                           (n1.x + n2.x) / 2 AS midpoint_x,
                           (n1.y + n2.y) / 2 AS midpoint_y,
                           CASE WHEN e.is_forward THEN s.climb_m
                                ELSE s.descent_m END AS climb_m
                    FROM car_edges e
                    LEFT JOIN read_parquet('{nodes_source}') n1
                      ON e.from_node_id = n1.node_id
                    LEFT JOIN read_parquet('{nodes_source}') n2
                      ON e.to_node_id = n2.node_id
                    LEFT JOIN _osm_sensitivity_segments s
                      USING (way_id, segment_index)
                )
                SELECT *,
                       CAST(floor(midpoint_y / 10000) AS BIGINT) * 100000
                         + CAST(floor(midpoint_x / 10000) AS BIGINT) AS tile_id,
                       CAST(floor(midpoint_x / 10000) AS BIGINT) * 10000
                         AS tile_easting_m,
                       CAST(floor(midpoint_y / 10000) AS BIGINT) * 10000
                         AS tile_northing_m
                FROM located
            """)
            invalid_edges = connection.execute("""
                SELECT count(*) FROM _osm_sensitivity_edge_rows
                WHERE length_m IS NULL OR length_m <= 0
                   OR midpoint_x IS NULL OR midpoint_y IS NULL OR tile_id IS NULL
            """).fetchone()[0]
            if invalid_edges:
                raise ValueError(
                    f"{invalid_edges} car edges lack valid length or tile coordinates"
                )
            tile_rows = connection.execute("""
                SELECT tile_id, tile_easting_m, tile_northing_m,
                       coalesce(sum(climb_m), 0),
                       coalesce(sum(length_m) FILTER (WHERE climb_m IS NOT NULL), 0),
                       count(*) FILTER (WHERE climb_m IS NULL)
                FROM _osm_sensitivity_edge_rows
                GROUP BY tile_id, tile_easting_m, tile_northing_m
                ORDER BY tile_id
            """).fetchall()
            tiles = tuple(
                TileClimb(
                    int(tile_id), int(easting), int(northing),
                    float(climb), float(length), int(incomplete),
                )
                for tile_id, easting, northing, climb, length, incomplete in tile_rows
            )
            total_climb = sum(tile.climb_m for tile in tiles)
            total_length = sum(tile.edge_length_m for tile in tiles)
            pilot_climb_per_km[window_m] = (
                total_climb * 1000 / total_length if total_length > 0 else None
            )
            tiles_by_window[window_m] = tiles

        known_tiles = {tile.tile_id for tile in tiles_by_window[windows_m[0]]}
        missing_tiles = (set(flat_tiles) | set(hilly_tiles)) - known_tiles
        if missing_tiles:
            raise ValueError(
                "reference tile ids are absent from car edges: "
                + ", ".join(str(tile_id) for tile_id in sorted(missing_tiles))
            )
        reference_zones: dict[str, dict[float, float | None]] = {}
        for name, selected_ids in (
            ("flat", flat_tiles), ("hilly", hilly_tiles)
        ):
            if not selected_ids:
                continue
            reference_zones[name] = {}
            for window_m, tiles in tiles_by_window.items():
                selected = [tile for tile in tiles if tile.tile_id in selected_ids]
                length = sum(tile.edge_length_m for tile in selected)
                climb = sum(tile.climb_m for tile in selected)
                reference_zones[name][window_m] = (
                    climb * 1000 / length if length > 0 else None
                )
    finally:
        smoothing_source.unlink(missing_ok=True)
    return ElevationSensitivity(
        windows_m, pilot_climb_per_km, tiles_by_window, reference_zones
    )


def _write_tile_map(path: Path, tiles: tuple[TileClimb, ...]) -> None:
    """Write a north-up PNG tile map; tile ids and coordinates are in the report."""
    if not tiles:
        raise ValueError("cannot map an empty tile set")
    cell_pixels = 20
    eastings = [tile.easting_m // 10000 for tile in tiles]
    northings = [tile.northing_m // 10000 for tile in tiles]
    min_easting, max_easting = min(eastings), max(eastings)
    min_northing, max_northing = min(northings), max(northings)
    columns = max_easting - min_easting + 1
    rows = max_northing - min_northing + 1
    width, height = columns * cell_pixels, rows * cell_pixels
    values = [tile.climb_per_km for tile in tiles if tile.climb_per_km is not None]
    low, high = min(values, default=0.0), max(values, default=0.0)
    pixels = bytearray([255] * width * height * 3)
    for tile in tiles:
        value = tile.climb_per_km
        if value is None:
            color = (150, 150, 150)
        else:
            fraction = 0.0 if high == low else (value - low) / (high - low)
            color = (
                int(40 + 215 * fraction),
                int(175 - 125 * fraction),
                int(70 - 30 * fraction),
            )
        column = tile.easting_m // 10000 - min_easting
        row = max_northing - tile.northing_m // 10000
        for dy in range(cell_pixels):
            for dx in range(cell_pixels):
                if dx in (0, cell_pixels - 1) or dy in (0, cell_pixels - 1):
                    pixel = (35, 35, 35)
                else:
                    pixel = color
                offset = ((row * cell_pixels + dy) * width
                          + column * cell_pixels + dx) * 3
                pixels[offset : offset + 3] = bytes(pixel)
    scanlines = b"".join(
        b"\x00" + pixels[row * width * 3 : (row + 1) * width * 3]
        for row in range(height)
    )

    def chunk(name: bytes, data: bytes) -> bytes:
        payload = name + data
        return (
            struct.pack(">I", len(data)) + payload
            + struct.pack(">I", binascii.crc32(payload) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines))
        + chunk(b"IEND", b"")
    )


def _append_sensitivity_report(
    report_path: Path,
    map_path: Path,
    sensitivity: ElevationSensitivity,
) -> None:
    """Replace the optional sensitivity section and map link in the report."""
    marker = "\n## Smoothing sensitivity\n"
    existing = report_path.read_text(encoding="utf-8")
    if marker in existing:
        existing = existing.split(marker, 1)[0].rstrip() + "\n"
    windows = sensitivity.windows_m
    headers = " | ".join(f"{window:g} m" for window in windows)
    pilot_values = " | ".join(
        "NA" if sensitivity.pilot_climb_per_km[window] is None
        else f"{sensitivity.pilot_climb_per_km[window]:.2f}"
        for window in windows
    )
    lines = [
        "## Smoothing sensitivity",
        "",
        "Car climb per kilometre of complete directed car-edge length; "
        "climb is in metres and distance in kilometres.",
        "",
        f"![Climb per km by 10 km tile at 50 m]({map_path.name})",
        "",
        "Map tiles are 10 km squares in EPSG:3035, north-up. Each edge is "
        "assigned by its endpoint midpoint. Tile id is "
        "`floor(northing / 10000) * 100000 + floor(easting / 10000)`. Color runs "
        "from green (flattest) to red (hilliest); tile ids and lower-left "
        "coordinates are listed below.",
        "",
        f"| Scope | {headers} |",
        "|---|" + "|".join("---:" for _ in windows) + "|",
        f"| Whole pilot | {pilot_values} |",
    ]
    for name in ("flat", "hilly"):
        zone = sensitivity.reference_zones.get(name)
        if zone is None:
            continue
        values = " | ".join(
            "NA" if zone[window] is None else f"{zone[window]:.2f}"
            for window in windows
        )
        lines.append(f"| {name.title()} reference zone | {values} |")
    lines.extend([
        "",
        "### By 10 km tile",
        "",
        f"| Tile id | Easting (m) | Northing (m) | Complete edge km | "
        f"Incomplete edges | {headers} |",
        "|---:|---:|---:|---:|---:|" + "|".join("---:" for _ in windows) + "|",
    ])
    tile_values: dict[int, dict[float, TileClimb]] = {}
    for window, tiles in sensitivity.tiles_by_window.items():
        for tile in tiles:
            tile_values.setdefault(tile.tile_id, {})[window] = tile
    for tile_id in sorted(tile_values):
        tile_by_window = tile_values[tile_id]
        first = tile_by_window[windows[0]]
        climb_values = " | ".join(
            "NA" if tile_by_window[window].climb_per_km is None
            else f"{tile_by_window[window].climb_per_km:.2f}"
            for window in windows
        )
        lines.append(
            f"| {tile_id} | {first.easting_m} | {first.northing_m} | "
            f"{first.edge_length_m / 1000:.2f} | {first.incomplete_edges} | "
            f"{climb_values} |"
        )
    ranked = sensitivity.tiles_by_window.get(50.0, ())
    for title, ordered in (
        ("10 flattest tiles at 50 m", sorted(
            (tile for tile in ranked if tile.climb_per_km is not None),
            key=lambda tile: (tile.climb_per_km, tile.tile_id),
        )[:10]),
        ("10 hilliest tiles at 50 m", sorted(
            (tile for tile in ranked if tile.climb_per_km is not None),
            key=lambda tile: (-tile.climb_per_km, tile.tile_id),
        )[:10]),
    ):
        lines.extend(["", f"### {title}", "",
                      "| Tile id | Easting (m) | Northing (m) | Climb (m/km) |",
                      "|---:|---:|---:|---:|"])
        lines.extend(
            f"| {tile.tile_id} | {tile.easting_m} | {tile.northing_m} | "
            f"{tile.climb_per_km:.2f} |"
            for tile in ordered
        )
    _write_tile_map(map_path, ranked)
    report_path.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")


def _parse_smoothing_windows(value: str) -> tuple[float, ...]:
    try:
        windows = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "smoothing windows must be comma-separated numbers"
        ) from exc
    if (
        not windows or any(not np.isfinite(window) or window < 0 for window in windows)
        or len(set(windows)) != len(windows)
    ):
        raise argparse.ArgumentTypeError(
            "smoothing windows must be distinct, finite, non-negative numbers"
        )
    if 50.0 not in windows:
        raise argparse.ArgumentTypeError(
            "smoothing windows must include 50 m for the tile map and rankings"
        )
    return windows


def _parse_tile_ids(value: str) -> tuple[int, ...]:
    try:
        tile_ids = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "tile ids must be comma-separated integers"
        ) from exc
    if not tile_ids or len(set(tile_ids)) != len(tile_ids):
        raise argparse.ArgumentTypeError("tile ids must be non-empty and distinct")
    return tile_ids


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
    parser.add_argument(
        "--smoothing-windows", type=_parse_smoothing_windows,
        help="report-only climb sensitivity windows in metres (must include 50)",
    )
    parser.add_argument(
        "--flat-tiles", type=_parse_tile_ids,
        help="comma-separated tile ids for the flat reference zone",
    )
    parser.add_argument(
        "--hilly-tiles", type=_parse_tile_ids,
        help="comma-separated tile ids for the hilly reference zone",
    )
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
        "version": 2,
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
    if bool(args.flat_tiles) != bool(args.hilly_tiles):
        raise ValueError("--flat-tiles and --hilly-tiles must be supplied together")
    if (args.flat_tiles or args.hilly_tiles) and args.smoothing_windows is None:
        raise ValueError("reference tiles require --smoothing-windows")
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
    report_path = args.report or root / "docs" / "data" / (
        "step06_elevation_pilot.md"
        if args.state == 2021 and args.area == "pilot"
        else f"step06_elevation_{args.area}_{args.state}.md"
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
    terminal = logging.StreamHandler()
    terminal.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(terminal)
    logger.setLevel(logging.INFO)
    started = time.perf_counter()
    try:
        required = (ways_path, edges_path, nodes_path, way_elevations, report_path)
        reused = False
        if checkpoint.is_file() and all(path.is_file() for path in required):
            previous = json.loads(checkpoint.read_text(encoding="utf-8"))
            current = _completion_signature(
                ways_path, elevation_paths, edges_path, nodes_path, way_elevations,
                report_path, network, energy,
            )
            reused = previous == current
            old_report = root / "docs" / "data" / "step06_elevation_pilot_2021.md"
            if (
                not reused and args.report is None
                and args.state == 2021 and args.area == "pilot"
                and old_report.is_file()
                and previous == {**current, "report": _file_signature(old_report)}
                and old_report.read_bytes() == report_path.read_bytes()
            ):
                _write_json(checkpoint, current)
                reused = True
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
        if args.smoothing_windows is not None:
            connection = open_connection()
            try:
                sensitivity = _compute_elevation_sensitivity(
                    connection,
                    edges_path,
                    nodes_path,
                    way_elevations,
                    args.smoothing_windows,
                    flat_tiles=args.flat_tiles or (),
                    hilly_tiles=args.hilly_tiles or (),
                )
            finally:
                connection.close()
            map_path = report_path.with_name(
                report_path.stem + "_climb_per_km_50m.png"
            )
            _append_sensitivity_report(report_path, map_path, sensitivity)
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
        logger.removeHandler(terminal)
        terminal.close()


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
