"""Free-flow car speeds and edge delays for sections 8.1 and 8.4."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
import pyarrow.parquet as pq
from common.config import load_pilot_config
from common.duckdb_io import open_connection, write_parquet
from numba import njit

from mobgrid.osm.config import CarSpeedConfig, NetworkConfig, load_network_config

logger = logging.getLogger(__name__)

_DENSITY_TILE_CELLS = 512
_DENSITY_BATCH_SIZE = 65_536


@njit(cache=True)
def _rasterize_lines(
    x0: npt.NDArray[np.float64],
    y0: npt.NDArray[np.float64],
    x1: npt.NDArray[np.float64],
    y1: npt.NDArray[np.float64],
    cell_m: float,
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64], npt.NDArray[np.float64]]:
    """Split projected line segments into grid-cell lengths in metres (8.4)."""
    capacity = 0
    for i in range(len(x0)):
        capacity += (
            int(np.ceil(abs(x1[i] - x0[i]) / cell_m))
            + int(np.ceil(abs(y1[i] - y0[i]) / cell_m)) + 3
        )
    cells_x = np.empty(capacity, dtype=np.int64)
    cells_y = np.empty(capacity, dtype=np.int64)
    lengths = np.empty(capacity, dtype=np.float64)
    count = 0
    for i in range(len(x0)):
        dx = x1[i] - x0[i]
        dy = y1[i] - y0[i]
        length = np.hypot(dx, dy)
        if length == 0:
            continue
        cx = int(np.floor(x0[i] / cell_m))
        cy = int(np.floor(y0[i] / cell_m))
        if dx < 0 and x0[i] == cx * cell_m:
            cx -= 1
        if dy < 0 and y0[i] == cy * cell_m:
            cy -= 1
        start = 0.0
        while start < 1:
            tx = np.inf
            ty = np.inf
            if dx > 0:
                tx = ((cx + 1) * cell_m - x0[i]) / dx
            elif dx < 0:
                tx = (cx * cell_m - x0[i]) / dx
            if dy > 0:
                ty = ((cy + 1) * cell_m - y0[i]) / dy
            elif dy < 0:
                ty = (cy * cell_m - y0[i]) / dy
            end = min(tx, ty, 1.0)
            if end > start:
                cells_x[count] = cx
                cells_y[count] = cy
                lengths[count] = (end - start) * length
                count += 1
            if end >= 1:
                break
            if tx <= end:
                cx += 1 if dx > 0 else -1
            if ty <= end:
                cy += 1 if dy > 0 else -1
            start = end
    return cells_x[:count], cells_y[:count], lengths[:count]


def _tile_groups(
    x: npt.NDArray[np.int64], y: npt.NDArray[np.int64]
) -> dict[tuple[int, int], npt.NDArray[np.int64]]:
    """Group sparse grid-cell indices into bounded convolution tiles."""
    tx = np.floor_divide(x, _DENSITY_TILE_CELLS)
    ty = np.floor_divide(y, _DENSITY_TILE_CELLS)
    order = np.lexsort((tx, ty))
    if not len(order):
        return {}
    boundaries = np.flatnonzero(
        (tx[order[1:]] != tx[order[:-1]]) | (ty[order[1:]] != ty[order[:-1]])
    ) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries, [len(order)]))
    return {
        (int(tx[order[start]]), int(ty[order[start]])): order[start:end]
        for start, end in zip(starts, ends, strict=True)
    }


def _grid_density(
    connection: duckdb.DuckDBPyConnection,
    cell_m: float,
    radius_m: float,
    scratch: Path,
) -> None:
    """Rasterize undirected car length and convolve a centroid disc (8.4)."""
    started = time.perf_counter()
    logger.info("rasterizing undirected car segments")
    reader = connection.execute("""
        WITH points AS (
            SELECT s.way_id, s.segment_index, point.path[1] AS position,
                   ST_X(point.geom) AS x, ST_Y(point.geom) AS y
            FROM _car_segments s,
                 UNNEST(ST_Dump(ST_Points(s.geom))) AS u(point)
        ), lines AS (
            SELECT x, y,
                   lead(x) OVER segment_order AS next_x,
                   lead(y) OVER segment_order AS next_y
            FROM points
            WINDOW segment_order AS (
                PARTITION BY way_id, segment_index ORDER BY position
            )
        )
        SELECT x, y, next_x, next_y FROM lines WHERE next_x IS NOT NULL
    """).to_arrow_reader(batch_size=_DENSITY_BATCH_SIZE)
    try:
        schema = pa.schema([
            ("cell_x", pa.int64()), ("cell_y", pa.int64()),
            ("length_m", pa.float64()),
        ])
        with pq.ParquetWriter(scratch, schema) as writer:
            for batch in reader:
                arrays = [
                    np.asarray(batch.column(index).to_numpy(), dtype=np.float64)
                    for index in range(4)
                ]
                if not all(np.isfinite(array).all() for array in arrays):
                    raise ValueError(
                        "car road geometries contain non-finite coordinates"
                    )
                x, y, length = _rasterize_lines(*arrays, cell_m)
                writer.write_table(
                    pa.table({"cell_x": x, "cell_y": y, "length_m": length})
                )
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _car_density_cells AS
            SELECT cell_x, cell_y, sum(length_m) AS length_m
            FROM read_parquet('{_sql_path(scratch)}') GROUP BY cell_x, cell_y
        """)
    finally:
        scratch.unlink(missing_ok=True)
    logger.info(
        "car grid rasterization completed in %.2f s", time.perf_counter() - started
    )
    started = time.perf_counter()
    logger.info("convolving road length over the focal disc")
    cells = connection.execute(
        "SELECT cell_x, cell_y, length_m FROM _car_density_cells"
    ).to_arrow_table()
    targets = connection.execute(f"""
        SELECT DISTINCT
               CAST(floor(ST_X(edge_center) / {cell_m!r}) AS BIGINT) AS cell_x,
               CAST(floor(ST_Y(edge_center) / {cell_m!r}) AS BIGINT) AS cell_y
        FROM _car_edges
    """).to_arrow_table()
    cell_x = cells["cell_x"].to_numpy()
    cell_y = cells["cell_y"].to_numpy()
    lengths = cells["length_m"].to_numpy()
    target_x = targets["cell_x"].to_numpy()
    target_y = targets["cell_y"].to_numpy()
    cell_groups = _tile_groups(cell_x, cell_y)
    target_groups = _tile_groups(target_x, target_y)

    halo = int(np.ceil(radius_m / cell_m))
    offsets = np.arange(-halo, halo + 1)
    kernel = (
        (offsets[:, None] * cell_m) ** 2 + (offsets[None, :] * cell_m) ** 2
        <= radius_m ** 2
    ).astype(np.float64)
    width = _DENSITY_TILE_CELLS + 2 * halo
    shape = (width + 2 * halo, width + 2 * halo)
    kernel_fft = np.fft.rfft2(kernel, s=shape)
    densities = np.empty(len(target_x), dtype=np.float64)
    neighbours = (halo + _DENSITY_TILE_CELLS - 1) // _DENSITY_TILE_CELLS
    for (tile_x, tile_y), indices in target_groups.items():
        grid = np.zeros((width, width), dtype=np.float64)
        origin_x = tile_x * _DENSITY_TILE_CELLS - halo
        origin_y = tile_y * _DENSITY_TILE_CELLS - halo
        for other_y in range(tile_y - neighbours, tile_y + neighbours + 1):
            for other_x in range(tile_x - neighbours, tile_x + neighbours + 1):
                group = cell_groups.get((other_x, other_y))
                if group is None:
                    continue
                gx = cell_x[group] - origin_x
                gy = cell_y[group] - origin_y
                valid = (gx >= 0) & (gx < width) & (gy >= 0) & (gy < width)
                grid[gy[valid], gx[valid]] = lengths[group[valid]]
        result = np.fft.irfft2(np.fft.rfft2(grid, s=shape) * kernel_fft, s=shape)
        gx = target_x[indices] - tile_x * _DENSITY_TILE_CELLS + 2 * halo
        gy = target_y[indices] - tile_y * _DENSITY_TILE_CELLS + 2 * halo
        # Remove FFT round-off so equal focal sums remain equal during fitting.
        densities[indices] = np.maximum(np.round(result[gy, gx], 8), 0) / 1000
    connection.register("_car_density_results", pa.table({
        "cell_x": target_x, "cell_y": target_y, "road_density_km": densities,
    }))
    try:
        connection.execute(f"""
            CREATE OR REPLACE TEMP TABLE _car_edge_densities AS
            SELECT e.edge_key, d.road_density_km
            FROM _car_edges e JOIN _car_density_results d
              ON CAST(floor(ST_X(e.edge_center) / {cell_m!r}) AS BIGINT) = d.cell_x
             AND CAST(floor(ST_Y(e.edge_center) / {cell_m!r}) AS BIGINT) = d.cell_y
        """)
    finally:
        connection.unregister("_car_density_results")
    logger.info("focal convolution completed in %.2f s", time.perf_counter() - started)


@dataclass(frozen=True)
class CarCostSummary:
    """Fitted density threshold and length-weighted urban shares."""

    edge_count: int
    density_radius_m: float
    density_threshold_km: float
    density_agreement: float | None
    urban_length_share_by_class: tuple[tuple[str, float], ...]
    output_path: str
    density_grid_cell_m: float


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _file_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns
    }


def _default_speed_expression(config: CarSpeedConfig) -> str:
    context_cases = []
    for context, default_speed in config.defaults_kmh_by_context.items():
        class_cases = " ".join(
            f"WHEN {_sql_text(highway)} THEN {speed!r}"
            for highway, speed in config.class_overrides_kmh_by_context.get(
                context, {}
            ).items()
        )
        class_default = (
            f"CASE lower(coalesce(highway, 'default')) {class_cases} "
            f"ELSE {default_speed!r} END"
            if class_cases
            else repr(default_speed)
        )
        context_cases.append(
            f"WHEN resolved_context = {_sql_text(context)} "
            f"THEN ({class_default})"
        )
    base = "CASE " + " ".join(context_cases) + " END"
    oneway_cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {speed!r}"
        for highway, speed in config.rural_oneway_speed_kmh_by_highway.items()
    )
    base = (
        "CASE WHEN resolved_context = 'rural' AND lower(trim(oneway)) = 'yes' "
        f"THEN coalesce(CASE lower(highway) {oneway_cases} END, ({base})) "
        f"ELSE ({base}) END"
    )
    cap_cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {speed!r}"
        for highway, speed in config.default_caps_kmh_by_highway.items()
    )
    return (
        f"least(({base}), coalesce(CASE lower(highway) {cap_cases} END, "
        f"({base})))"
    )


def _realism_factor_expression(config: CarSpeedConfig) -> str:
    cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {factor!r}"
        for highway, factor in config.realism_factor_by_highway.items()
        if highway != "default"
    )
    return (
        f"CASE lower(coalesce(highway, 'default')) {cases} "
        f"ELSE {config.realism_factor_by_highway['default']!r} END"
    )


def _bucket_expression(
    config: CarSpeedConfig, speed_expression: str
) -> str:
    bounds = config.speed_limit_bucket_upper_bounds_kmh
    cases = []
    for index, upper_bound in enumerate(bounds):
        label = f"le_{upper_bound:g}" if index == 0 else (
            f"gt_{bounds[index - 1]:g}_le_{upper_bound:g}"
        )
        cases.append(
            f"WHEN {speed_expression} <= {upper_bound!r} "
            f"THEN {_sql_text(label)}"
        )
    return (
        "CASE " + " ".join(cases) + " ELSE "
        + _sql_text(f"gt_{bounds[-1]:g}") + " END"
    )


def _fit_density_threshold(
    connection: duckdb.DuckDBPyConnection,
    config: CarSpeedConfig,
) -> tuple[float, float | None]:
    """Fit the length-weighted urban/rural separator on tagged edges."""
    urban_length, rural_length = connection.execute("""
        SELECT sum(length_m) FILTER (WHERE speed_context = 'urban'),
               sum(length_m) FILTER (WHERE speed_context = 'rural')
        FROM _car_edges
    """).fetchone()
    if not urban_length or not rural_length:
        return config.urban_density.fallback_threshold_km, None

    threshold, agreement = connection.execute("""
        WITH density_groups AS (
            SELECT d.road_density_km,
                   sum(e.length_m) FILTER (
                       WHERE e.speed_context = 'urban'
                   ) AS urban_length_m,
                   sum(e.length_m) FILTER (
                       WHERE e.speed_context = 'rural'
                   ) AS rural_length_m
            FROM _car_edges e
            JOIN _car_edge_densities d USING (edge_key)
            WHERE e.speed_context IN ('urban', 'rural')
            GROUP BY d.road_density_km
        ),
        totals AS (
            SELECT sum(urban_length_m) AS urban_total_m,
                   sum(rural_length_m) AS rural_total_m,
                   sum(
                       coalesce(urban_length_m, 0)
                       + coalesce(rural_length_m, 0)
                   ) AS labelled_total_m,
                   max(road_density_km) AS maximum_density_km
            FROM density_groups
        ),
        running AS (
            SELECT *,
                   coalesce(
                       sum(urban_length_m) OVER (
                           ORDER BY road_density_km
                           ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                       ),
                       0
                   ) AS urban_below_m,
                   coalesce(
                       sum(rural_length_m) OVER (
                           ORDER BY road_density_km
                           ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                       ),
                       0
                   ) AS rural_below_m
            FROM density_groups
        ),
        candidates AS (
            SELECT road_density_km AS threshold_km,
                   urban_total_m - urban_below_m + rural_below_m
                       AS correctly_classified_m,
                   labelled_total_m
            FROM running
            CROSS JOIN totals
            UNION ALL
            SELECT maximum_density_km
                       + greatest(abs(maximum_density_km), 1) * 1e-12,
                   rural_total_m,
                   labelled_total_m
            FROM totals
        )
        SELECT threshold_km,
               max(correctly_classified_m / labelled_total_m) AS agreement
        FROM candidates
        GROUP BY threshold_km
        ORDER BY agreement DESC, threshold_km
        LIMIT 1
    """).fetchone()
    return float(threshold), float(agreement)


def _check_car_classes(
    connection: duckdb.DuckDBPyConnection,
    edges_path: Path,
    config: CarSpeedConfig,
) -> None:
    configured = set(config.realism_factor_by_highway)
    classes = {
        row[0]
        for row in connection.execute(
            f"""
            SELECT DISTINCT lower(highway)
            FROM read_parquet('{_sql_path(edges_path)}')
            WHERE mode = 'car' AND highway IS NOT NULL
            """
        ).fetchall()
    }
    missing = sorted(classes - configured)
    if missing:
        raise ValueError(
            "car highway classes lack realism factors in config/network.yaml: "
            + ", ".join(missing)
        )
    invalid_limits = connection.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{_sql_path(edges_path)}')
        WHERE mode = 'car' AND maxspeed_kmh <= 0
        """
    ).fetchone()[0]
    if invalid_limits:
        raise ValueError(
            f"{invalid_limits} car edges have a non-positive maxspeed_kmh"
        )


def build_car_costs(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    output_path: str | Path,
    *,
    config: NetworkConfig,
    cache_directory: Path | None = None,
) -> CarCostSummary:
    """Write per-directed-edge free-flow times and speed metadata (8.1, 8.4)."""
    edges = Path(edges_path)
    output = Path(output_path)
    if not edges.is_file():
        raise FileNotFoundError(edges)
    started = time.perf_counter()
    logger.info("validating and loading car edges")
    _check_car_classes(connection, edges, config.car_speed)
    output.parent.mkdir(parents=True, exist_ok=True)
    connection.execute("LOAD spatial")
    edge_source = _sql_path(edges)
    radius = config.car_speed.urban_density.radius_m
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _car_edges AS
        WITH geometries AS (
            SELECT edge_key, way_id, is_forward,
                   try_cast(split_part(edge_key, ':', 2) AS BIGINT) AS segment_index,
                   highway, maxspeed_kmh, speed_context, length_m, oneway,
                   signal_count, stop_count, give_way_count, crossing_count,
                   mini_roundabout_count, to_degree,
                   ST_GeomFromWKB(geometry_wkb) AS geom
            FROM read_parquet('{edge_source}')
            WHERE mode = 'car'
        )
        SELECT *, ST_Centroid(geom) AS edge_center
        FROM geometries
    """)
    invalid = connection.execute("""
        SELECT count(*) FROM _car_edges
        WHERE way_id IS NULL OR segment_index IS NULL OR is_forward IS NULL
           OR geom IS NULL OR edge_center IS NULL OR ST_NPoints(geom) < 2
    """).fetchone()[0]
    if invalid:
        raise ValueError(f"{invalid} car edges have invalid segment keys or geometry")
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _car_segments AS
        SELECT way_id, segment_index, first(geom ORDER BY is_forward DESC) AS geom
        FROM _car_edges GROUP BY way_id, segment_index
    """)
    logger.info("car edge loading completed in %.2f s", time.perf_counter() - started)
    started = time.perf_counter()
    logger.info("calculating car road density")
    signature = {
        "version": 1,
        "edges": _file_signature(edges),
        "cell_m": config.car_speed.urban_density.grid_cell_m,
        "radius_m": radius,
    }
    cached = False
    if cache_directory is not None:
        cache_directory.mkdir(parents=True, exist_ok=True)
        checkpoint = cache_directory / "density.parquet"
        metadata_path = cache_directory / "density.json"
        if checkpoint.is_file() and metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            cached = (
                metadata["signature"] == signature
                and metadata["output"] == _file_signature(checkpoint)
            )
        if cached:
            logger.info("reusing car density checkpoint %s", checkpoint)
            connection.execute(f"""
                CREATE OR REPLACE TEMP TABLE _car_edge_densities AS
                SELECT * FROM read_parquet('{_sql_path(checkpoint)}')
            """)
    if not cached:
        _grid_density(
            connection, config.car_speed.urban_density.grid_cell_m, radius,
            output.with_name(output.stem + ".density.tmp.parquet"),
        )
        if cache_directory is not None:
            temporary_checkpoint = checkpoint.with_name("density.tmp.parquet")
            temporary_metadata = metadata_path.with_suffix(".tmp.json")
            try:
                write_parquet(
                    connection, "SELECT * FROM _car_edge_densities",
                    temporary_checkpoint,
                )
                temporary_checkpoint.replace(checkpoint)
                temporary_metadata.write_text(
                    json.dumps({
                        "signature": signature,
                        "output": _file_signature(checkpoint),
                    }, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                temporary_metadata.replace(metadata_path)
            finally:
                temporary_checkpoint.unlink(missing_ok=True)
                temporary_metadata.unlink(missing_ok=True)
    logger.info(
        "density calculation completed in %.2f s", time.perf_counter() - started
    )
    started = time.perf_counter()
    logger.info("fitting density threshold")
    threshold, agreement = _fit_density_threshold(
        connection, config.car_speed
    )
    logger.info(
        "density threshold fit completed in %.2f s", time.perf_counter() - started
    )
    started = time.perf_counter()
    logger.info("calculating car costs")
    density_flag = f"d.road_density_km >= {threshold!r}"
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _car_edge_costs AS
        WITH classified AS (
            SELECT e.*, d.road_density_km,
                   CASE
                     WHEN e.speed_context = 'urban' THEN TRUE
                     WHEN e.speed_context = 'rural' THEN FALSE
                     ELSE {density_flag}
                   END AS is_urban,
                   CASE
                     WHEN e.speed_context IN (
                         'urban', 'rural', 'zone30', 'motorway'
                     ) THEN e.speed_context
                     WHEN {density_flag} THEN 'urban'
                     ELSE 'rural'
                   END AS resolved_context
            FROM _car_edges e
            JOIN _car_edge_densities d USING (edge_key)
        ),
        limits AS (
            SELECT *,
                   coalesce(
                       maxspeed_kmh,
                       {_default_speed_expression(config.car_speed)}
                   ) AS speed_limit_kmh,
                   {_realism_factor_expression(config.car_speed)}
                       AS realism_factor
            FROM classified
        ),
        timed AS (
            SELECT *,
                   speed_limit_kmh * realism_factor AS effective_speed_kmh,
                   length_m * 3.6
                       / (speed_limit_kmh * realism_factor)
                   + coalesce(signal_count, 0) * {config.car_speed.delays.signal_s!r}
                   + coalesce(stop_count, 0) * {config.car_speed.delays.stop_s!r}
                   + coalesce(give_way_count, 0)
                       * {config.car_speed.delays.give_way_s!r}
                   + coalesce(crossing_count, 0)
                       * {config.car_speed.delays.crossing_s!r}
                   + coalesce(mini_roundabout_count, 0)
                       * {config.car_speed.delays.mini_roundabout_s!r}
                   + CASE
                       WHEN to_degree >=
                            {config.car_speed.delays.degree_threshold}
                       THEN {config.car_speed.delays.at_to_node_s!r}
                       ELSE 0
                     END AS time_s
            FROM limits
        )
        SELECT edge_key, time_s, is_urban, highway AS road_class,
               {_bucket_expression(config.car_speed, "speed_limit_kmh")}
                   AS speed_limit_bucket
        FROM timed
    """)
    logger.info("car costs completed in %.2f s", time.perf_counter() - started)

    started = time.perf_counter()
    logger.info("writing car costs and calculating summary")
    temporary = output.with_name(output.stem + ".tmp.parquet")
    try:
        write_parquet(
            connection,
            "SELECT edge_key, time_s, is_urban, road_class, "
            "speed_limit_bucket FROM _car_edge_costs",
            temporary,
        )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    edge_count = int(
        connection.execute("SELECT count(*) FROM _car_edge_costs").fetchone()[0]
    )
    class_shares = connection.execute("""
        SELECT coalesce(costs.road_class, '(no highway)') AS road_class,
               coalesce(
                   sum(edges.length_m) FILTER (WHERE costs.is_urban)
                       / nullif(sum(edges.length_m), 0),
                   0
               )
                   AS urban_length_share
        FROM _car_edge_costs costs
        JOIN _car_edges edges USING (edge_key)
        GROUP BY road_class
        ORDER BY road_class
    """).fetchall()
    logger.info("car cost output completed in %.2f s", time.perf_counter() - started)
    return CarCostSummary(
        edge_count=edge_count,
        density_radius_m=radius,
        density_threshold_km=threshold,
        density_agreement=agreement,
        urban_length_share_by_class=tuple(
            (str(road_class), float(share))
            for road_class, share in class_shares
        ),
        output_path=str(output),
        density_grid_cell_m=config.car_speed.urban_density.grid_cell_m,
    )


def write_car_speed_report(
    summary: CarCostSummary,
    path: str | Path,
    *,
    state: int,
    area: str,
) -> None:
    """Report the fitted urban-density rule and urban length by class (8.4)."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    agreement = (
        "not estimable"
        if summary.density_agreement is None
        else f"{summary.density_agreement:.1%}"
    )
    lines = [
        f"# Car free-flow costs ({state}, {area})",
        "",
        f"- Directed car edges: {summary.edge_count:,}",
        "- Density metric: undirected car-road length per grid cell, summed "
        "over a cell-centred disc and sampled at each edge centroid.",
        f"- Density grid cell: {summary.density_grid_cell_m:g} m",
        f"- Density radius: {summary.density_radius_m:g} m",
        f"- {'Fitted' if summary.density_agreement is not None else 'Fallback'} "
        f"urban threshold: {summary.density_threshold_km:.6g} km of car roads",
        f"- Length-weighted urban/rural label agreement: {agreement}",
        "- Speed-limit bucket is based on the configured limit before realism "
        "factors.",
        "",
        "## Urban share of directed car length by road class",
        "",
        "| Road class | Urban length share |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {road_class} | {share:.1%} |"
        for road_class, share in summary.urban_length_share_by_class
    )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.speeds")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument(
        "--network-config", type=Path, default=Path("config/network.yaml")
    )
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build the car free-flow cost table and its diagnostic report."""
    args = _parser().parse_args(argv)
    config = load_network_config(args.network_config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in config.states:
        raise ValueError(f"unsupported state {args.state}")
    root = args.pilot_config.resolve().parent.parent
    network_directory = (
        root / pilot.paths["base"] / "network" / str(args.state) / args.area
    )
    edges_path = network_directory / "edges.parquet"
    output_path = network_directory / "car_costs.parquet"
    report_path = args.report or Path(
        f"docs/data/step06_car_speeds_{args.area}_{args.state}.md"
    )
    task = f"osm_speeds_{args.state}_{args.area}"
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
        connection = open_connection()
        try:
            summary = build_car_costs(
                connection, edges_path, output_path, config=config,
                cache_directory=(
                    root / pilot.paths["interim"] / "osm" / str(args.state)
                    / args.area / "speeds"
                ),
            )
        finally:
            connection.close()
        write_car_speed_report(
            summary, report_path, state=args.state, area=args.area
        )
        elapsed = time.perf_counter() - started
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            f"# OSM car speeds run summary\n\n"
            f"- Input: `{edges_path}`\n"
            f"- Outputs: `{output_path}`, `{report_path}`\n"
            f"- Elapsed: {elapsed:.1f} seconds\n"
            f"- Warnings and counts: see the report below.\n\n"
            + report_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        logger.info(
            "wrote %s directed car costs to %s; density threshold %.6g km in %.1f s",
            summary.edge_count,
            output_path,
            summary.density_threshold_km,
            elapsed,
        )
        return 0
    finally:
        if sys.exc_info()[0] is not None:
            logger.error("car speed job failed", exc_info=True)
        logger.removeHandler(handler)
        handler.close()
        logger.removeHandler(terminal)
        terminal.close()


if __name__ == "__main__":
    raise SystemExit(main())
