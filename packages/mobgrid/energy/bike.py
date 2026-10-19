"""Cycling energy calculations for section 9.7."""

from __future__ import annotations

from math import atan, cos, sin

import numpy as np

from mobgrid.energy.rates import GRAVITY_M_S2


def solve_bike_speed_m_per_s(
    power_w: float,
    mass_kg: float,
    gradient: float,
    rolling_resistance: float,
    cda_m2: float,
    rho_air_kg_per_m3: float,
    drivetrain_efficiency: float,
    headwind_m_per_s: float = 0.0,
) -> float:
    """Speed solving the force balance of section 9.7, m/s.

    ``P_r . eta_d = v . [M.g.(Crr.cos(theta) + sin(theta))
    + 0.5.rho.CdA.(v + v_w)^2]`` (di Prampero et al. 1979; Martin et al.
    1998). ``gradient`` is the signed slope i = tan(theta) in the
    direction of travel, climbing positive; reversing the direction of
    travel negates it and generally changes the solved speed. ``mass_kg``
    is the combined rider and bike mass M. The cubic in v is solved for
    its smallest positive real root: with zero power on a steep enough
    descent (negative ``gradient``), gravity alone sets a coasting
    equilibrium speed, otherwise the root is 0.
    """
    if power_w < 0:
        raise ValueError("power must not be negative")
    theta = atan(gradient)
    weight_term = mass_kg * GRAVITY_M_S2 * (
        rolling_resistance * cos(theta) + sin(theta)
    )
    drag_coefficient = 0.5 * rho_air_kg_per_m3 * cda_m2
    available_power_w = power_w * drivetrain_efficiency
    # b.v^3 + 2.b.v_w.v^2 + (A + b.v_w^2).v - P = 0
    coefficients = [
        drag_coefficient,
        2.0 * drag_coefficient * headwind_m_per_s,
        weight_term + drag_coefficient * headwind_m_per_s**2,
        -available_power_w,
    ]
    roots = np.roots(coefficients)
    positive_real_roots = [
        root.real
        for root in roots
        if abs(root.imag) < 1e-6 and root.real > 1e-9
    ]
    if not positive_real_roots:
        return 0.0
    return min(positive_real_roots)


def select_ride_power_w(
    gradient: float, p0_w: float, k: float, p_max_w: float
) -> float:
    """Rider power P_r by slope regime (section 9.7).

    P_r = P_0 on the flat or climbing (i >= 0), capped at P_max;
    P_r = 0 on descents (i < 0), where the caller instead caps the solved
    speed at v_max,desc.
    """
    if gradient < 0:
        return 0.0
    return min(p0_w * (1.0 + k * gradient), p_max_w)


def rolling_work_j_per_kg(
    length_m: float, gradient: float, rolling_resistance: float
) -> float:
    """W_roll contribution of one pedalled edge, J/kg (section 9.7)."""
    theta = atan(gradient)
    return GRAVITY_M_S2 * rolling_resistance * cos(theta) * length_m


def climbing_work_j_per_kg(length_m: float, gradient: float) -> float:
    """W_climb contribution of one edge, J/kg; zero on descents (9.7)."""
    theta = atan(gradient)
    return GRAVITY_M_S2 * max(length_m * sin(theta), 0.0)


def drag_work_j(
    length_m: float,
    speed_m_per_s: float,
    rho_air_kg_per_m3: float,
    cda_m2: float,
) -> float:
    """W_drag contribution of one pedalled edge, J (section 9.7)."""
    return 0.5 * rho_air_kg_per_m3 * cda_m2 * speed_m_per_s**2 * length_m


def stop_energy_kj(
    speed_m_per_s: float, mass_total_kg: float, efficiency: float
) -> float:
    """Energy to regain speed after one stop, kJ (section 9.7).

    0.5 * M * v^2 / efficiency; about 3.5 kJ at 16 km/h for M = 85 kg.
    """
    return 0.5 * mass_total_kg * speed_m_per_s**2 / efficiency / 1000.0


def bike_ride_energy_kj(
    roll_work_j_per_kg: float,
    climb_work_j_per_kg: float,
    stops_work_j_per_kg: float,
    drag_work_j_total: float,
    mass_total_kg: float,
    efficiency: float,
    separated_infra_factor: float = 1.0,
) -> float:
    """Riding energy above rest, kJ (section 9.7).

    e = [M.(W_roll + W_climb + W_stops) + W_drag] / efficiency, multiplied
    by phi_sep (``separated_infra_factor``) on separated infrastructure.
    """
    total_j = (
        mass_total_kg
        * (roll_work_j_per_kg + climb_work_j_per_kg + stops_work_j_per_kg)
        + drag_work_j_total
    ) / efficiency
    return total_j * separated_infra_factor / 1000.0


def ebike_motor_power_w(
    rider_power_w: float, assist_factor: float, motor_cap_w: float
) -> float:
    """Motor power added by pedelec assistance (section 9.7).

    P_m = min(motor_cap_w, a . P_r); the EU pedelec speed cutoff is
    applied by ``solve_ebike_speed_m_per_s``, not here.
    """
    return min(motor_cap_w, assist_factor * rider_power_w)


def solve_ebike_speed_m_per_s(
    rider_power_w: float,
    mass_kg: float,
    gradient: float,
    rolling_resistance: float,
    cda_m2: float,
    rho_air_kg_per_m3: float,
    drivetrain_efficiency: float,
    assist_factor: float,
    motor_cap_w: float,
    speed_cap_kmh: float,
    headwind_m_per_s: float = 0.0,
) -> float:
    """E-bike speed with pedelec assistance below ``speed_cap_kmh`` (9.7).

    Below the EU pedelec speed cap the motor adds
    ``ebike_motor_power_w``; above it assistance cuts out, so the speed is
    governed at the cap whenever the rider alone could not reach it, and
    left unassisted whenever the rider alone already exceeds it. Rider
    metabolic energy still comes from ``rider_power_w`` only.
    """
    motor_power_w = ebike_motor_power_w(rider_power_w, assist_factor, motor_cap_w)
    assisted_speed = solve_bike_speed_m_per_s(
        rider_power_w + motor_power_w,
        mass_kg,
        gradient,
        rolling_resistance,
        cda_m2,
        rho_air_kg_per_m3,
        drivetrain_efficiency,
        headwind_m_per_s,
    )
    speed_cap_m_per_s = speed_cap_kmh * 1000.0 / 3600.0
    if assisted_speed <= speed_cap_m_per_s:
        return assisted_speed
    unassisted_speed = solve_bike_speed_m_per_s(
        rider_power_w,
        mass_kg,
        gradient,
        rolling_resistance,
        cda_m2,
        rho_air_kg_per_m3,
        drivetrain_efficiency,
        headwind_m_per_s,
    )
    return max(unassisted_speed, speed_cap_m_per_s)
