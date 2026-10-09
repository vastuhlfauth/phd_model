"""Grid-cell identifiers and tiling helpers for sections 4.1 and 4.4."""

from __future__ import annotations

import re
from math import floor, isfinite

_CELL_ID_BASE = 100_000
_INSPIRE_PATTERN = re.compile(
    r"^CRS3035RES(?P<resolution>\d+)mN(?P<northing>\d+)E(?P<easting>\d+)$"
)

NEIGHBOUR_OFFSETS: tuple[tuple[int, int], ...] = tuple(
    (northing, easting)
    for northing in range(-2, 3)
    for easting in range(-2, 3)
    if (northing, easting) != (0, 0)
)


def _grid_index(coordinate_m: int | float, resolution_m: int) -> int:
    if isinstance(coordinate_m, bool) or not isinstance(coordinate_m, (int, float)):
        raise ValueError("grid coordinates must be finite numbers")
    if not isfinite(coordinate_m) or coordinate_m < 0:
        raise ValueError("EPSG:3035 coordinates must be finite and non-negative")
    if isinstance(resolution_m, bool) or not isinstance(resolution_m, int):
        raise ValueError("resolution must be a positive integer")
    if resolution_m <= 0:
        raise ValueError("resolution must be a positive integer")
    return floor(coordinate_m / resolution_m)


def _cell_id_from_indices(northing_index: int, easting_index: int) -> int:
    if not 0 <= easting_index < _CELL_ID_BASE:
        raise ValueError("easting index must be less than 100000 for unique cell ids")
    return northing_index * _CELL_ID_BASE + easting_index


def cell_id(northing_m: int | float, easting_m: int | float, resolution_m: int) -> int:
    """Return the integer id for a coordinate in metres (section 14.3)."""
    northing_index = _grid_index(northing_m, resolution_m)
    easting_index = _grid_index(easting_m, resolution_m)
    return _cell_id_from_indices(northing_index, easting_index)


def cell_origin_m(cell_id: int, resolution_m: int) -> tuple[int, int]:
    """Decode a cell id to its south-west grid corner in metres."""
    _grid_index(0, resolution_m)
    if isinstance(cell_id, bool) or not isinstance(cell_id, int) or cell_id < 0:
        raise ValueError("cell id must be a non-negative integer")
    northing_index, easting_index = divmod(cell_id, _CELL_ID_BASE)
    return northing_index * resolution_m, easting_index * resolution_m


def inspire_code(
    northing_m: int | float, easting_m: int | float, resolution_m: int
) -> str:
    """Return the INSPIRE cell code for a point in metres (section 4.1)."""
    northing_index = _grid_index(northing_m, resolution_m)
    easting_index = _grid_index(easting_m, resolution_m)
    _cell_id_from_indices(northing_index, easting_index)
    northing_origin = northing_index * resolution_m
    easting_origin = easting_index * resolution_m
    return (
        f"CRS3035RES{resolution_m}mN{northing_origin}E{easting_origin}"
    )


def parse_inspire_code(code: str) -> tuple[int, int, int]:
    """Parse an INSPIRE cell code to (northing, easting, resolution) metres."""
    match = _INSPIRE_PATTERN.fullmatch(code)
    if match is None:
        raise ValueError(f"invalid EPSG:3035 INSPIRE cell code: {code!r}")
    resolution_m = int(match.group("resolution"))
    northing_m = int(match.group("northing"))
    easting_m = int(match.group("easting"))
    if _grid_index(northing_m, resolution_m) * resolution_m != northing_m:
        raise ValueError("northing in INSPIRE code is not grid-aligned")
    if _grid_index(easting_m, resolution_m) * resolution_m != easting_m:
        raise ValueError("easting in INSPIRE code is not grid-aligned")
    _cell_id_from_indices(
        northing_m // resolution_m,
        easting_m // resolution_m,
    )
    return northing_m, easting_m, resolution_m


def child_cell_ids(
    parent_cell_id: int, parent_resolution_m: int, child_resolution_m: int
) -> tuple[int, ...]:
    """Return the nested child ids, ordered northing then easting (section 4.1)."""
    if parent_resolution_m <= 0 or child_resolution_m <= 0:
        raise ValueError("grid resolutions must be positive")
    if parent_resolution_m <= child_resolution_m:
        raise ValueError("parent resolution must exceed child resolution")
    if parent_resolution_m % child_resolution_m:
        raise ValueError("child resolution must divide parent resolution")

    northing_m, easting_m = cell_origin_m(parent_cell_id, parent_resolution_m)
    child_count = parent_resolution_m // child_resolution_m
    return tuple(
        cell_id(
            northing_m + northing_offset * child_resolution_m,
            easting_m + easting_offset * child_resolution_m,
            child_resolution_m,
        )
        for northing_offset in range(child_count)
        for easting_offset in range(child_count)
    )


def tile_bounds_m(
    northing_m: int | float,
    easting_m: int | float,
    tile_size_m: int,
    halo_m: int = 0,
) -> tuple[int, int, int, int]:
    """Return half-open (north_min, east_min, north_max, east_max) tile bounds."""
    if isinstance(tile_size_m, bool) or not isinstance(tile_size_m, int):
        raise ValueError("tile size must be a positive integer")
    if tile_size_m <= 0:
        raise ValueError("tile size must be a positive integer")
    if isinstance(halo_m, bool) or not isinstance(halo_m, int) or halo_m < 0:
        raise ValueError("tile halo must be a non-negative integer")
    northing_index = _grid_index(northing_m, 1)
    easting_index = _grid_index(easting_m, 1)
    northing_min = (northing_index // tile_size_m) * tile_size_m - halo_m
    easting_min = (easting_index // tile_size_m) * tile_size_m - halo_m
    return (
        northing_min,
        easting_min,
        northing_min + tile_size_m + 2 * halo_m,
        easting_min + tile_size_m + 2 * halo_m,
    )
