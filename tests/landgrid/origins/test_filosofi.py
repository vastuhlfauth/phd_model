"""Acceptance tests for Filosofi natural-level helpers (section 6)."""

from landgrid.origins.filosofi import (
    decode_natural_cell,
    derived_departments,
    natural_cell_200m_codes,
    natural_cell_contains_200m,
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
