"""Elevation and gradient processing for sections 8.1 and 9.3."""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
from common.config import load_pilot_config
from common.duckdb_io import open_connection, write_parquet

from mobgrid.osm.config import load_network_config

FloatArray = npt.NDArray[np.float64]
logger = logging.getLogger(__name__)

_PROFILE_COLUMNS = (
    "elevation_from_m",
    "elevation_to_m",
    "climb_m",
    "descent_m",
    "mean_grade",
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


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def enrich_edges_with_elevation(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    nodes_path: str | Path,
    elevation_paths: Sequence[str | Path],
) -> ElevationSummary:
    """Add directional profiles to the edge table in EPSG:3035 metres (8.1)."""
    edges = Path(edges_path)
    nodes = Path(nodes_path)
    if not edges.is_file():
        raise FileNotFoundError(edges)
    if not nodes.is_file():
        raise FileNotFoundError(nodes)
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
    elevations = sample_elevations(grids, x, y)
    uncovered_nodes = nodes_without_tile(grids, x, y)
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
    try:
        edge_source = _sql_path(edges)
        node_source = _sql_path(nodes)
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _osm_edge_elevation_profiles AS
            WITH ordered_nodes AS (
                SELECT e.edge_key, edge_node.node_sequence,
                       n.x, n.y, sampled.elevation_m,
                       lag(n.x) OVER edge_order AS previous_x,
                       lag(n.y) OVER edge_order AS previous_y,
                       lag(sampled.elevation_m) OVER edge_order
                           AS previous_elevation_m
                FROM read_parquet('{edge_source}') e
                CROSS JOIN UNNEST(e.node_ids) WITH ORDINALITY
                    AS edge_node(node_id, node_sequence)
                JOIN read_parquet('{node_source}') n USING (node_id)
                LEFT JOIN _osm_sampled_node_elevations sampled USING (node_id)
                WINDOW edge_order AS (
                    PARTITION BY e.edge_key ORDER BY edge_node.node_sequence
                )
            ),
            edge_stats AS (
                SELECT edge_key,
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
                       sum(greatest(previous_elevation_m - elevation_m, 0))
                           AS descent_m
                FROM ordered_nodes
                GROUP BY edge_key
            )
            SELECT edge_key, elevation_from_m, elevation_to_m,
                   CASE WHEN has_complete_profile THEN climb_m END AS climb_m,
                   CASE WHEN has_complete_profile THEN descent_m END
                       AS descent_m,
                   CASE
                     WHEN has_complete_profile AND horizontal_length_m > 0
                     THEN (elevation_to_m - elevation_from_m)
                          / horizontal_length_m
                   END AS mean_grade
            FROM edge_stats
        """)
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
        temporary.replace(edges)
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

    return ElevationSummary(
        int(edge_count),
        int(np.count_nonzero(~np.isfinite(elevations))),
        uncovered_nodes,
        int(missing_profiles),
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
    destination.write_text(
        f"""# OSM elevation profiles ({state}, {area})

- BD ALTI ASCII tiles: {tile_count:,}
- Directed edge profiles: {summary.edge_count:,}
- Nodes with no covering tile: {summary.nodes_without_tile:,}
- Nodes with no valid elevation sample: {summary.nodes_without_elevation:,}
- Edges with incomplete elevation profiles: {summary.edges_without_profile:,}
- Units: metres; mean grade is dimensionless.
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
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Sample BD ALTI and add elevation fields to the configured edge table."""
    args = _parser().parse_args(argv)
    network = load_network_config(args.network_config)
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
    elevation_paths = sorted(tile_directory.rglob("*.asc"))
    if not elevation_paths:
        raise FileNotFoundError(
            f"no unpacked BD ALTI ASCII grids found under {tile_directory}"
        )
    report_path = args.report or Path(
        f"docs/data/step06_elevation_{args.area}_{args.state}.md"
    )
    started = time.perf_counter()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    connection = open_connection()
    try:
        summary = enrich_edges_with_elevation(
            connection, edges_path, nodes_path, elevation_paths
        )
    finally:
        connection.close()
    write_elevation_report(
        summary,
        report_path,
        state=args.state,
        area=args.area,
        tile_count=len(elevation_paths),
    )
    logger.info(
        "wrote %s edge elevation profiles; %s nodes lack tile coverage "
        "(%.1f seconds)",
        summary.edge_count,
        summary.nodes_without_elevation,
        time.perf_counter() - started,
    )
    return 0


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
