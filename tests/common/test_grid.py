"""Acceptance tests for grid identifiers and tiling (sections 4.1, 4.4)."""

import pytest
from common.grid import (
    NEIGHBOUR_OFFSETS,
    cell_id,
    cell_origin_m,
    child_cell_ids,
    inspire_code,
    parse_inspire_code,
    tile_bounds_m,
)


@pytest.mark.parametrize("resolution_m", [200, 1000])
def test_cell_ids_and_inspire_codes_round_trip(resolution_m: int) -> None:
    northing_m = 2_400_000
    easting_m = 4_000_000
    expected_code = f"CRS3035RES{resolution_m}mN2400000E4000000"
    expected_id = (
        1_200_020_000 if resolution_m == 200 else 240_004_000
    )

    identifier = cell_id(northing_m, easting_m, resolution_m)
    code = inspire_code(northing_m, easting_m, resolution_m)

    assert identifier == expected_id
    assert code == expected_code
    assert cell_origin_m(identifier, resolution_m) == (
        northing_m,
        easting_m,
    )
    assert parse_inspire_code(code) == (
        northing_m,
        easting_m,
        resolution_m,
    )


def test_one_kilometre_cell_has_25_two_hundred_metre_children() -> None:
    parent = cell_id(2_400_000, 4_000_000, 1000)
    children = child_cell_ids(parent, 1000, 200)

    assert len(children) == len(set(children)) == 25
    assert {
        cell_id(northing_m, easting_m, 1000)
        for northing_m, easting_m in (
            cell_origin_m(child, 200) for child in children
        )
    } == {parent}


def test_neighbour_stencil_has_24_distinct_offsets() -> None:
    assert len(NEIGHBOUR_OFFSETS) == 24
    assert len(set(NEIGHBOUR_OFFSETS)) == 24
    assert (0, 0) not in NEIGHBOUR_OFFSETS
    assert all(
        abs(north) <= 2 and abs(east) <= 2
        for north, east in NEIGHBOUR_OFFSETS
    )


def test_tile_bounds_include_configured_halo() -> None:
    assert tile_bounds_m(
        northing_m=2_401_234,
        easting_m=4_009_876,
        tile_size_m=50_000,
        halo_m=2_000,
    ) == (2_398_000, 3_998_000, 2_452_000, 4_052_000)


def test_cell_id_rejects_unencodable_easting_index() -> None:
    with pytest.raises(ValueError, match="easting"):
        cell_id(2_400_000, 20_000_000, 200)
