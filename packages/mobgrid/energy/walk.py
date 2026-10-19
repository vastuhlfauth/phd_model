"""Walking energy calculations for section 9.3."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import exp
from typing import Literal

from mobgrid.energy.rates import GRAVITY_M_S2

#: v(0) normalisation of Tobler's (1993) hiking function, so that the
#: rescaled speed equals v0 at gradient 0 (section 9.3).
_TOBLER_FLAT_FACTOR = exp(-0.175)


def walking_speed_m_per_s(gradient: float, v0_m_per_s: float) -> float:
    """Tobler's (1993) hiking speed at gradient i, rescaled to v(0) = v0.

    ``gradient`` is signed: positive uphill, negative downhill, in the
    direction of travel (section 9.3).
    """
    return v0_m_per_s * exp(-3.5 * abs(gradient + 0.05)) / _TOBLER_FLAT_FACTOR


def net_cost_of_walking_j_per_kg_m(
    gradient: float, coefficients: Sequence[float]
) -> float:
    """Minetti et al. (2002) net cost of walking Cw(i), J/kg/m.

    ``coefficients`` are the six coefficients of the degree-5 polynomial in
    ``gradient``, from i^5 down to i^0 (section 9.3), evaluated by Horner's
    method.
    """
    total = 0.0
    for coefficient in coefficients:
        total = total * gradient + coefficient
    return total


def gradient_factor(gradient: float, coefficients: Sequence[float]) -> float:
    """Gradient factor g(i) = Cw(i) / Cw(0) (section 9.3)."""
    return net_cost_of_walking_j_per_kg_m(
        gradient, coefficients
    ) / net_cost_of_walking_j_per_kg_m(0.0, coefficients)


def walking_time_and_energy(
    segments: Iterable[tuple[float, float]],
    mass_kg: float,
    v0_kmh: float,
    c0_j_per_kg_m: float,
    coefficients: Sequence[float],
) -> tuple[float, float]:
    """Time (s) and energy above rest (kJ) of a walking leg (section 9.3).

    ``segments`` is a sequence of ``(length_m, gradient)`` pairs along the
    path, in the direction of travel; t = sum(L / v(i)),
    e = m * c0 * sum(L * g(i)). Reversing the path's direction negates
    every gradient and generally changes both t and e.
    """
    v0_m_per_s = v0_kmh * 1000.0 / 3600.0
    duration_s = 0.0
    work_j_per_kg = 0.0
    for length_m, gradient in segments:
        duration_s += length_m / walking_speed_m_per_s(gradient, v0_m_per_s)
        work_j_per_kg += length_m * gradient_factor(gradient, coefficients)
    energy_kj = mass_kg * c0_j_per_kg_m * work_j_per_kg / 1000.0
    return duration_s, energy_kj


def stair_time_and_energy(
    height_m: float,
    direction: Literal["up", "down"],
    mass_kg: float,
    up_speed_m_per_s: float,
    down_speed_m_per_s: float,
    up_efficiency: float,
    down_to_up_energy_ratio: float,
) -> tuple[float, float]:
    """Time (s) and energy above rest (kJ) of a stair leg (section 9.3).

    e_up = m*g*height/up_efficiency; e_down is about a third of e_up.
    Climbing 10 m at 70 kg costs about 22.9 kJ.
    """
    e_up_kj = mass_kg * GRAVITY_M_S2 * height_m / up_efficiency / 1000.0
    if direction == "up":
        return height_m / up_speed_m_per_s, e_up_kj
    return height_m / down_speed_m_per_s, e_up_kj * down_to_up_energy_ratio
