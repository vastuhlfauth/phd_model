"""Temporal census growth helpers for the approved section-6.3 exception."""

from __future__ import annotations

import math
from collections.abc import Mapping


def projected_growth_factor(
    start_value: float,
    end_value: float,
    *,
    observed_years: float,
    projected_years: float,
) -> float:
    """Project a census growth factor across years using geometric growth."""
    values = (start_value, end_value, observed_years, projected_years)
    if (
        not all(math.isfinite(value) for value in values)
        or start_value <= 0
        or end_value < 0
        or observed_years <= 0
        or projected_years <= 0
    ):
        raise ValueError("invalid growth inputs")
    if end_value == 0:
        return 0.0
    exponent = projected_years / observed_years
    factor = math.exp((math.log(end_value) - math.log(start_value)) * exponent)
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("projected growth factor is not finite and positive")
    return factor


def rescale_age_margins(
    age_margins: Mapping[str, float],
    *,
    individual_total: float,
) -> tuple[dict[str, float], float]:
    """Rescale census age margins to grown individuals before age IPF (6.3)."""
    if (
        not math.isfinite(individual_total)
        or individual_total < 0
        or not age_margins
        or any(
            not name or not math.isfinite(value) or value < 0
            for name, value in age_margins.items()
        )
    ):
        raise ValueError("invalid age margin inputs")
    age_total = math.fsum(age_margins.values())
    if age_total == 0:
        if individual_total == 0:
            return dict(age_margins), 1.0
        raise ValueError("positive individuals have no age margin support")
    adjustment = individual_total / age_total
    return (
        {name: value * adjustment for name, value in age_margins.items()},
        adjustment,
    )
