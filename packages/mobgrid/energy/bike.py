"""Cycling energy calculations for section 9.7."""

from __future__ import annotations

from math import atan, cos, sin

import numpy as np

from mobgrid.energy.rates import GRAVITY_M_S2, clamp


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


def required_power_w(
    speed_m_per_s: float,
    mass_kg: float,
    gradient: float,
    rolling_resistance: float,
    cda_m2: float,
    rho_air_kg_per_m3: float,
    drivetrain_efficiency: float,
    headwind_m_per_s: float = 0.0,
) -> float:
    """Power needed to hold ``speed_m_per_s`` on ``gradient`` (section 9.7).

    The forward evaluation of the same force balance solved by
    ``solve_bike_speed_m_per_s``; used to find the (possibly reduced,
    never negative in practice since braking needs no power) power that
    exactly holds a capped descent speed.
    """
    theta = atan(gradient)
    weight_term = mass_kg * GRAVITY_M_S2 * (
        rolling_resistance * cos(theta) + sin(theta)
    )
    drag_coefficient = 0.5 * rho_air_kg_per_m3 * cda_m2
    relative_speed = speed_m_per_s + headwind_m_per_s
    mechanical_power_w = speed_m_per_s * (
        weight_term + drag_coefficient * relative_speed**2
    )
    return mechanical_power_w / drivetrain_efficiency


def select_ride_power_w(
    gradient: float, p0_w: float, k: float, p_max_w: float
) -> float:
    """Rider power P_r by slope, on every grade (section 9.7).

    P_r = clamp(P_0 . (1 + k.i), 0, P_max), climbs and descents alike:
    a gentle descent still has the rider pedalling at reduced power, down
    to zero once i <= -1/k. ``ride_speed_and_power`` separately caps the
    resulting speed (and reduces power to match) on steeper descents.
    """
    return clamp(p0_w * (1.0 + k * gradient), 0.0, p_max_w)


def rolling_work_j_per_kg(
    length_m: float, gradient: float, rolling_resistance: float
) -> float:
    """W_roll contribution of one pedalled edge, J/kg (section 9.7)."""
    theta = atan(gradient)
    return GRAVITY_M_S2 * rolling_resistance * cos(theta) * length_m


def climbing_work_j_per_kg(length_m: float, gradient: float) -> float:
    """W_climb contribution of one pedalled edge, J/kg (section 9.7).

    Signed: negative on a descent still being pedalled (gradient < 0 but
    P_r > 0 under the clamp formula above), so the rider's total
    mechanical work, and hence s_r = P_r/(P_r+P_m), matches the force
    balance that actually set the speed.
    """
    theta = atan(gradient)
    return GRAVITY_M_S2 * length_m * sin(theta)


def drag_work_j(
    length_m: float,
    speed_m_per_s: float,
    rho_air_kg_per_m3: float,
    cda_m2: float,
) -> float:
    """W_drag contribution of one pedalled edge, J (section 9.7)."""
    return 0.5 * rho_air_kg_per_m3 * cda_m2 * speed_m_per_s**2 * length_m


def stop_energy_kj(
    speed_m_per_s: float,
    mass_total_kg: float,
    efficiency: float,
    rider_share: float = 1.0,
) -> float:
    """Rider's energy to regain speed after one stop, kJ (section 9.7).

    0.5 * M * v^2 * s_r / efficiency; about 3.5 kJ at 16 km/h for
    M = 85 kg, s_r = 1 (an unassisted bike). ``rider_share`` is
    s_r = P_r/(P_r+P_m) (section 9.7): on an e-bike, part of the
    kinetic energy regained after a stop comes from the motor.
    """
    return 0.5 * mass_total_kg * speed_m_per_s**2 * rider_share / efficiency / 1000.0


def stop_time_s(
    speed_m_per_s: float,
    deceleration_m_per_s2: float,
    acceleration_m_per_s2: float,
    signal_cycle_s: float,
    red_time_s: float,
) -> float:
    """Time lost to one stop: deceleration + wait + acceleration (9.7).

    The expected wait for a random arrival at a signal of cycle C and red
    time R is R^2/(2C) (Webster 1958).
    """
    deceleration_time_s = speed_m_per_s / deceleration_m_per_s2
    acceleration_time_s = speed_m_per_s / acceleration_m_per_s2
    expected_wait_s = red_time_s**2 / (2.0 * signal_cycle_s)
    return deceleration_time_s + expected_wait_s + acceleration_time_s


def bike_ride_energy_kj(
    roll_work_j_per_kg: float,
    climb_work_j_per_kg: float,
    stops_work_j_per_kg: float,
    drag_work_j_total: float,
    mass_total_kg: float,
    efficiency: float,
    separated_infra_factor: float = 1.0,
    rider_share: float = 1.0,
) -> float:
    """Rider's riding energy above rest, kJ (section 9.7).

    e = s_r . [M.(W_roll + W_climb + W_stops) + W_drag] / efficiency,
    multiplied by phi_sep (``separated_infra_factor``) on separated
    infrastructure. ``rider_share`` is s_r = P_r/(P_r+P_m) (1.0 for an
    unassisted bike, where the rider supplies all propulsive power).
    """
    total_j = (
        mass_total_kg
        * (roll_work_j_per_kg + climb_work_j_per_kg + stops_work_j_per_kg)
        + drag_work_j_total
    ) / efficiency
    return total_j * separated_infra_factor * rider_share / 1000.0


def ride_speed_and_power(
    gradient: float,
    p0_w: float,
    k: float,
    p_max_w: float,
    mass_total_kg: float,
    rolling_resistance: float,
    cda_m2: float,
    rho_air_kg_per_m3: float,
    drivetrain_efficiency: float,
    v_max_descent_m_per_s: float,
    class_cap_m_per_s: float | None = None,
    headwind_m_per_s: float = 0.0,
) -> tuple[float, float]:
    """Speed and rider power on one edge, by direction (section 9.7).

    P_r = ``select_ride_power_w`` on every grade; if the resulting speed
    would exceed v_max,desc or a (not yet modelled) infrastructure-class
    cap, speed is capped there and P_r reduced to the power that exactly
    holds the cap (braking absorbs any excess mechanically, at no
    metabolic cost, so the reduced P_r is never negative). Returns
    ``(speed_m_per_s, rider_power_w)``.
    """
    power_w = select_ride_power_w(gradient, p0_w, k, p_max_w)
    speed_m_per_s = solve_bike_speed_m_per_s(
        power_w, mass_total_kg, gradient, rolling_resistance, cda_m2,
        rho_air_kg_per_m3, drivetrain_efficiency, headwind_m_per_s,
    )
    cap_m_per_s = v_max_descent_m_per_s
    if class_cap_m_per_s is not None:
        cap_m_per_s = min(cap_m_per_s, class_cap_m_per_s)
    if speed_m_per_s > cap_m_per_s:
        speed_m_per_s = cap_m_per_s
        power_w = max(
            required_power_w(
                speed_m_per_s, mass_total_kg, gradient, rolling_resistance,
                cda_m2, rho_air_kg_per_m3, drivetrain_efficiency, headwind_m_per_s,
            ),
            0.0,
        )
    return speed_m_per_s, power_w


def ebike_rider_share(rider_power_w: float, motor_power_w: float) -> float:
    """s_r = P_r / (P_r + P_m), the rider's share of propulsive power (9.7).

    1.0 when there is no motor power (an unassisted bike, or a fully
    braked/coasting descent where neither rider nor motor propels).
    """
    total_power_w = rider_power_w + motor_power_w
    if total_power_w <= 0.0:
        return 1.0
    return rider_power_w / total_power_w


def ebike_motor_power_w(
    rider_power_w: float, assist_factor: float, motor_cap_w: float
) -> float:
    """Motor power added by pedelec assistance (section 9.7).

    P_m = min(motor_cap_w, a . P_r); the EU pedelec speed cutoff is
    applied by ``ebike_ride_speed_and_power``, not here.
    """
    return min(motor_cap_w, assist_factor * rider_power_w)


def ebike_ride_speed_and_power(
    gradient: float,
    p0_w: float,
    k: float,
    p_max_w: float,
    mass_total_kg: float,
    rolling_resistance: float,
    cda_m2: float,
    rho_air_kg_per_m3: float,
    drivetrain_efficiency: float,
    assist_factor: float,
    motor_cap_w: float,
    pedelec_speed_cap_m_per_s: float,
    v_max_descent_m_per_s: float,
    class_cap_m_per_s: float | None = None,
    headwind_m_per_s: float = 0.0,
) -> tuple[float, float, float]:
    """E-bike speed, rider power and motor power on one edge (9.7).

    Extends ``ride_speed_and_power`` with pedelec assistance
    (``ebike_motor_power_w``) below the EU speed cap, cutting out above
    it; descents are capped exactly as for a plain bike, with the
    reduction applied to the rider first (the motor is assumed to cut
    out, like coasting/regen braking, before the rider stops pedalling).
    Returns ``(speed_m_per_s, rider_power_w, motor_power_w)``.
    """
    rider_power_w = select_ride_power_w(gradient, p0_w, k, p_max_w)
    motor_power_w = ebike_motor_power_w(rider_power_w, assist_factor, motor_cap_w)
    speed_m_per_s = solve_bike_speed_m_per_s(
        rider_power_w + motor_power_w, mass_total_kg, gradient, rolling_resistance,
        cda_m2, rho_air_kg_per_m3, drivetrain_efficiency, headwind_m_per_s,
    )
    if speed_m_per_s > pedelec_speed_cap_m_per_s:
        unassisted_speed_m_per_s = solve_bike_speed_m_per_s(
            rider_power_w, mass_total_kg, gradient, rolling_resistance, cda_m2,
            rho_air_kg_per_m3, drivetrain_efficiency, headwind_m_per_s,
        )
        if unassisted_speed_m_per_s >= pedelec_speed_cap_m_per_s:
            # The rider alone already exceeds the cap; assistance is moot.
            motor_power_w = 0.0
            speed_m_per_s = unassisted_speed_m_per_s
        else:
            # Governed exactly at the cap: the motor's assistance backs
            # off to hold it, not the rider's own power (EU pedelec
            # rules, section 9.7).
            speed_m_per_s = pedelec_speed_cap_m_per_s
            required_total_w = max(
                required_power_w(
                    speed_m_per_s, mass_total_kg, gradient, rolling_resistance,
                    cda_m2, rho_air_kg_per_m3, drivetrain_efficiency,
                    headwind_m_per_s,
                ),
                0.0,
            )
            motor_power_w = max(required_total_w - rider_power_w, 0.0)

    cap_m_per_s = v_max_descent_m_per_s
    if class_cap_m_per_s is not None:
        cap_m_per_s = min(cap_m_per_s, class_cap_m_per_s)
    if speed_m_per_s > cap_m_per_s:
        speed_m_per_s = cap_m_per_s
        required_total_w = max(
            required_power_w(
                speed_m_per_s, mass_total_kg, gradient, rolling_resistance,
                cda_m2, rho_air_kg_per_m3, drivetrain_efficiency, headwind_m_per_s,
            ),
            0.0,
        )
        rider_power_w = min(rider_power_w, required_total_w)
        motor_power_w = max(required_total_w - rider_power_w, 0.0)

    return speed_m_per_s, rider_power_w, motor_power_w
