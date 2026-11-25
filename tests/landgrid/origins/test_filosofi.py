"""Acceptance tests for Filosofi natural-level helpers (section 6)."""

import pytest
from landgrid.origins.filosofi import (
    build_natural_cell_lookup,
    decode_natural_cell,
    derived_departments,
    natural_cell_200m_codes,
    natural_cell_contains_200m,
    natural_cell_for_200m_cell,
)


def test_decode_and_containment_of_natural_level_cell() -> None:
    code = "CRS3035RES1000mN2400000E4000000"

    northing, easting, resolution = decode_natural_cell(code)

    assert (northing, easting, resolution) == (2_400_000, 4_000_000, 1_000)
    contained = natural_cell_200m_codes(code)
    assert len(contained) == 25
    assert "CRS3035RES200mN2400000E4000000" in contained
    assert "CRS3035RES200mN2400800E4000800" in contained
    assert natural_cell_contains_200m(
        code,
        "CRS3035RES200mN2400800E4000800",
    )


def test_derived_departments_from_lcog_geo() -> None:
    lcog_geo = [
        "33063,40088",
        "33000,24001",
        "17300",
        "47001,33063",
        "2A001",
    ]

    assert derived_departments(lcog_geo) == {"17", "24", "33", "2A", "40", "47"}


def test_natural_cell_is_decoded_without_a_200m_filosofi_row() -> None:
    natural_code = "CRS3035RES1000mN2400000E4000000"
    lookup = build_natural_cell_lookup([natural_code])

    assert (
        natural_cell_for_200m_cell(
            "CRS3035RES200mN2400200E4000200",
            lookup,
        )
        == natural_code
    )


def test_natural_cell_lookup_rejects_multiple_matching_resolutions() -> None:
    lookup = build_natural_cell_lookup(
        [
            "CRS3035RES1000mN2400000E4000000",
            "CRS3035RES2000mN2400000E4000000",
        ]
    )

    with pytest.raises(ValueError, match="multiple natural-level cells"):
        natural_cell_for_200m_cell(
            "CRS3035RES200mN2400200E4000200",
            lookup,
        )
