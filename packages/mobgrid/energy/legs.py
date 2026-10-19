"""Trip-leg energy calculations for section 9."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from mobgrid.energy.rates import clamp, sedentary_energy_kj


@dataclass(frozen=True)
class Leg:
    """One leg of a trip: duration (s) and energy above rest (kJ), 9.2."""

    duration_s: float
    energy_kj: float


def trip_time_and_energy(legs: Iterable[Leg]) -> tuple[float, float]:
    """Chain a trip's legs: T = sum(t), E = sum(e) (section 9.2)."""
    duration_s = 0.0
    energy_kj = 0.0
    for leg in legs:
        duration_s += leg.duration_s
        energy_kj += leg.energy_kj
    return duration_s, energy_kj


def sedentary_leg(duration_s: float, rate_kj_per_min: float) -> Leg:
    """A sitting, standing or driving leg, e = r x t (section 9.2)."""
    return Leg(duration_s, sedentary_energy_kj(rate_kj_per_min, duration_s))


def expected_wait_s(
    headway_s: float,
    coefficient_of_variation: float,
    regime_threshold_s: float,
    planned_wait_s: float,
) -> float:
    """Expected wait w for a headway h (section 9.4).

    w = h/2 . (1 + CV^2) for headways up to the regime threshold (random
    arrivals; Larson & Odoni 1981; Holroyd & Scraggs 1966); w = w_planned
    beyond it, when passengers time their arrival.
    """
    if headway_s <= regime_threshold_s:
        return headway_s / 2.0 * (1.0 + coefficient_of_variation**2)
    return planned_wait_s


def waiting_leg(
    headway_s: float,
    coefficient_of_variation: float,
    regime_threshold_s: float,
    planned_wait_s: float,
    standing_relaxed_rate_kj_per_min: float,
) -> Leg:
    """A wait leg, at the standing-relaxed rate (section 9.4)."""
    duration_s = expected_wait_s(
        headway_s, coefficient_of_variation, regime_threshold_s, planned_wait_s
    )
    return sedentary_leg(duration_s, standing_relaxed_rate_kj_per_min)


def pt_standing_share(load_factor: float) -> float:
    """Share of riders standing, p_s = max(0, 1 - 1/LF) (section 9.5)."""
    if load_factor <= 0:
        raise ValueError("load factor must be positive")
    return max(0.0, 1.0 - 1.0 / load_factor)


def pt_standing_rate_kj_per_min(
    load_factor: float,
    load_factor_max: float,
    relaxed_rate_kj_per_min: float,
    restless_rate_kj_per_min: float,
) -> float:
    """Standing rate, interpolated up to the crush load LF_max (9.5)."""
    if load_factor_max <= 1:
        raise ValueError("load factor max must exceed 1")
    crowding = clamp((load_factor - 1.0) / (load_factor_max - 1.0), 0.0, 1.0)
    return relaxed_rate_kj_per_min + (
        restless_rate_kj_per_min - relaxed_rate_kj_per_min
    ) * crowding


def pt_ride_rate_kj_per_min(
    load_factor: float,
    load_factor_max: float,
    sit_rate_kj_per_min: float,
    relaxed_rate_kj_per_min: float,
    restless_rate_kj_per_min: float,
) -> float:
    """Mixed sitting/standing rate of a PT ride leg (section 9.5)."""
    standing_share = pt_standing_share(load_factor)
    standing_rate = pt_standing_rate_kj_per_min(
        load_factor, load_factor_max, relaxed_rate_kj_per_min, restless_rate_kj_per_min
    )
    return (1.0 - standing_share) * sit_rate_kj_per_min + standing_share * standing_rate


def pt_ride_leg(
    duration_s: float,
    load_factor: float,
    load_factor_max: float,
    sit_rate_kj_per_min: float,
    relaxed_rate_kj_per_min: float,
    restless_rate_kj_per_min: float,
) -> Leg:
    """A public transport ride leg (section 9.5)."""
    rate = pt_ride_rate_kj_per_min(
        load_factor,
        load_factor_max,
        sit_rate_kj_per_min,
        relaxed_rate_kj_per_min,
        restless_rate_kj_per_min,
    )
    return sedentary_leg(duration_s, rate)


def driving_rate_kj_per_min(
    rho: float,
    rho_max: float,
    free_flow_rate_kj_per_min: float,
    congested_cap_kj_per_min: float,
) -> float:
    """Driving rate, rising with congestion rho (section 9.6).

    rho is the ratio of congested to free-flow time on the path.
    """
    if rho_max <= 1:
        raise ValueError("rho_max must exceed 1")
    congestion = clamp((rho - 1.0) / (rho_max - 1.0), 0.0, 1.0)
    return free_flow_rate_kj_per_min + (
        congested_cap_kj_per_min - free_flow_rate_kj_per_min
    ) * congestion


def car_drive_leg(
    duration_s: float,
    rho: float,
    rho_max: float,
    free_flow_rate_kj_per_min: float,
    congested_cap_kj_per_min: float,
) -> Leg:
    """A car driving leg (section 9.6)."""
    rate = driving_rate_kj_per_min(
        rho, rho_max, free_flow_rate_kj_per_min, congested_cap_kj_per_min
    )
    return sedentary_leg(duration_s, rate)


def car_passenger_leg(duration_s: float, sitting_rate_kj_per_min: float) -> Leg:
    """A seated car-passenger leg (section 9.6)."""
    return sedentary_leg(duration_s, sitting_rate_kj_per_min)
