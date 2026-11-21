"""Elevation and gradient processing for sections 8.1 and 9.3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


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
        data = np.loadtxt(grid.path, skiprows=6, dtype=np.float64, ndmin=2)
        if data.shape != (grid.rows, grid.columns):
            raise ValueError(f"ASCII grid dimensions do not match data: {grid.path}")
        column = (xs[row_indices, corners] - x_offset).astype(np.int64)
        row = grid.rows - 1 - (
            ys[row_indices, corners] - y_offset
        ).astype(np.int64)
        sampled = data[row, column]
        sampled[sampled == grid.nodata] = np.nan
        values[row_indices, corners] = sampled
    weights = np.stack(
        ((1 - dx) * (1 - dy), dx * (1 - dy), (1 - dx) * dy, dx * dy),
        axis=1,
    )
    contributions = np.where(weights == 0, 0, values * weights)
    return np.sum(contributions, axis=1)


@dataclass(frozen=True)
class ElevationProfile:
    """Directional edge elevation statistics in metres and dimensionless grade."""

    elevation_from_m: float | None
    elevation_to_m: float | None
    climb_m: float | None
    descent_m: float | None
    mean_grade: float | None


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
