"""Filosofi natural-level helpers for section 6."""

from __future__ import annotations

import re
from collections.abc import Iterable

_INSPIRE_NATURAL = re.compile(
    r"^CRS3035RES(?P<resolution>\d+)mN(?P<northing>\d+)E(?P<easting>\d+)$"
)


def decode_natural_cell(code: str) -> tuple[int, int, int]:
    """Decode an INSPIRE natural-level code to corner northing/easting/size."""
    match = _INSPIRE_NATURAL.fullmatch(code)
    if match is None:
        raise ValueError(f"invalid natural-level INSPIRE code: {code!r}")
    northing = int(match.group("northing"))
    easting = int(match.group("easting"))
    resolution = int(match.group("resolution"))
    if northing % resolution or easting % resolution:
        raise ValueError("natural-level corner is not resolution-aligned")
    return northing, easting, resolution


def natural_cell_200m_codes(code: str) -> list[str]:
    """Return the INSPIRE 200 m codes contained by a natural-level cell."""
    northing, easting, resolution = decode_natural_cell(code)
    if resolution % 200:
        raise ValueError("natural-level resolution must contain 200 m cells")
    result: list[str] = []
    for north in range(northing, northing + resolution, 200):
        for east in range(easting, easting + resolution, 200):
            result.append(f"CRS3035RES200mN{north}E{east}")
    return result


def natural_cell_contains_200m(natural_code: str, cell_200m_code: str) -> bool:
    """Test whether an INSPIRE 200 m code is contained in a natural cell."""
    natural_northing, natural_easting, resolution = decode_natural_cell(natural_code)
    match = _INSPIRE_NATURAL.fullmatch(cell_200m_code)
    if match is None or int(match.group("resolution")) != 200:
        return False
    northing = int(match.group("northing"))
    easting = int(match.group("easting"))
    return (
        natural_northing <= northing < natural_northing + resolution
        and natural_easting <= easting < natural_easting + resolution
    )


def derived_departments(lcog_geo_values: Iterable[str]) -> set[str]:
    """Derive commune départements from comma-separated lcog_geo lists."""
    departments: set[str] = set()
    for value in lcog_geo_values:
        if not value:
            continue
        for commune in str(value).split(","):
            code = commune.strip()
            if len(code) >= 5 and code[:2].upper() in {"2A", "2B"}:
                departments.add(code[:2].upper())
            elif len(code) >= 5:
                departments.add(code[:2])
    return departments
