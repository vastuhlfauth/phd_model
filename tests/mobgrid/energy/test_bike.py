"""Section 9.7 bike-leg acceptance tests."""

from pathlib import Path

import pytest
from mobgrid.energy.bike import (
    bike_ride_energy_kj,
    climbing_work_j_per_kg,
    drag_work_j,
    ebike_motor_power_w,
    rolling_work_j_per_kg,
    select_ride_power_w,
    solve_bike_speed_m_per_s,
    solve_ebike_speed_m_per_s,
    stop_energy_kj,
)
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

# Consistency check of section 9.7: 16 km/h on the flat, M = 85 kg.
RIDER_SPEED_M_S = 16.0 / 3.6
RIDER_MASS_KG = 85.0


@pytest.fixture
def config():
    return load_energy_config(CONFIG_PATH)


@pytest.fixture
def crr(config):
    return config.bike.surface_crr["asphalt_concrete_paved_default"]


def _required_power_w(config, crr, mass_kg, gradient, speed_m_s):
    """Power needed to hold ``speed_m_s`` on ``gradient``, from the formula
    itself (inverting the force balance) -- not a separate implementation."""
    # Binary search for the power giving the target speed, since the only
    # solver exposed goes power -> speed (section 14.7 "per edge and
    # direction"); confirms the reference check by round trip instead of
    # re-deriving the closed form.
    low, high = 0.0, 1000.0
    for _ in range(100):
        mid = (low + high) / 2
        v = solve_bike_speed_m_per_s(
            mid, mass_kg, gradient, crr, config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        )
        if v < speed_m_s:
            low = mid
        else:
            high = mid
    return high


def test_mechanical_power_for_16kmh_flat_matches_reference(config, crr) -> None:
    # ~52.5 W of rider power at 16 km/h on the flat, M = 85 kg (section 9.7).
    power_w = _required_power_w(config, crr, RIDER_MASS_KG, 0.0, RIDER_SPEED_M_S)
    assert power_w == pytest.approx(52.5, rel=0.02)


def test_metabolic_rate_at_reference_power_matches_kh_and_compendium(
    config, crr
) -> None:
    power_w = _required_power_w(config, crr, RIDER_MASS_KG, 0.0, RIDER_SPEED_M_S)
    rate_kj_per_min = power_w / config.bike.gross_muscular_efficiency * 60 / 1000
    # Consistent with KH (14.7 kJ/min at 12 km/h) and the Compendium
    # leisure value (4.0 MET): about 13.1 kJ/min (section 9.7).
    assert rate_kj_per_min == pytest.approx(13.1, rel=0.02)


def test_solver_round_trips_a_known_speed(config, crr) -> None:
    power_w = _required_power_w(config, crr, RIDER_MASS_KG, 0.0, RIDER_SPEED_M_S)
    speed = solve_bike_speed_m_per_s(
        power_w, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert speed == pytest.approx(RIDER_SPEED_M_S, rel=0.01)


def test_mass_effect_on_speed_flat(config, crr) -> None:
    # +10 kg at the same power on the flat: speed -2.4% (section 9.7).
    power_w = _required_power_w(config, crr, RIDER_MASS_KG, 0.0, RIDER_SPEED_M_S)
    base = solve_bike_speed_m_per_s(
        power_w, 85.0, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    heavier = solve_bike_speed_m_per_s(
        power_w, 95.0, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert (heavier / base - 1) * 100 == pytest.approx(-2.4, abs=0.2)


def test_mass_effect_on_speed_climb(config, crr) -> None:
    # +10 kg at 100 W on a 5% climb: speed -9.8% (section 9.7).
    base = solve_bike_speed_m_per_s(
        100.0, 85.0, 0.05, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    heavier = solve_bike_speed_m_per_s(
        100.0, 95.0, 0.05, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert (heavier / base - 1) * 100 == pytest.approx(-9.8, abs=0.5)


def test_one_stop_energy_reference(config) -> None:
    # One stop from 16 km/h: 0.5 x M x v^2 / epsilon = 3.50 kJ (section 9.7).
    energy_kj = stop_energy_kj(
        RIDER_SPEED_M_S, RIDER_MASS_KG, config.bike.gross_muscular_efficiency
    )
    assert energy_kj == pytest.approx(3.50, rel=0.01)


def test_solve_bike_speed_rejects_negative_power(config, crr) -> None:
    with pytest.raises(ValueError):
        solve_bike_speed_m_per_s(
            -1.0, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        )


def test_zero_power_on_the_flat_gives_zero_speed(config, crr) -> None:
    speed = solve_bike_speed_m_per_s(
        0.0, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert speed == pytest.approx(0.0)


def test_zero_power_on_a_steep_descent_gives_a_coasting_speed(config, crr) -> None:
    # On a descent (i < 0) the rider applies P_r = 0; gravity still sets a
    # positive equilibrium speed when it exceeds rolling resistance.
    speed = solve_bike_speed_m_per_s(
        0.0, RIDER_MASS_KG, -0.08, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert speed > 0.0


def test_select_ride_power_on_the_flat_is_p0() -> None:
    assert select_ride_power_w(0.0, p0_w=100.0, k=2.0, p_max_w=300.0) == 100.0


def test_select_ride_power_is_capped_on_climbs() -> None:
    assert select_ride_power_w(0.5, p0_w=100.0, k=2.0, p_max_w=150.0) == 150.0


def test_select_ride_power_is_zero_on_descents() -> None:
    assert select_ride_power_w(-0.05, p0_w=100.0, k=2.0, p_max_w=300.0) == 0.0


def test_ride_energy_components_direction_asymmetry() -> None:
    # Same edge, opposite directions: climbing work is positive one way and
    # zero the other (section 9.7, 14.7 "per edge and direction").
    length_m, gradient = 100.0, 0.05
    forward_climb = climbing_work_j_per_kg(length_m, gradient)
    backward_climb = climbing_work_j_per_kg(length_m, -gradient)
    assert forward_climb > 0.0
    assert backward_climb == pytest.approx(0.0)


def test_bike_ride_energy_matches_manual_sum(config, crr) -> None:
    length_m, gradient, speed = 1000.0, 0.02, 16.0 / 3.6
    roll = rolling_work_j_per_kg(length_m, gradient, crr)
    climb = climbing_work_j_per_kg(length_m, gradient)
    drag = drag_work_j(
        length_m, speed, config.bike.rho_air_kg_per_m3, config.bike.cda_m2
    )
    mass_total = RIDER_MASS_KG + config.bike.bike_mass_kg
    efficiency = config.bike.gross_muscular_efficiency
    energy_kj = bike_ride_energy_kj(roll, climb, 0.0, drag, mass_total, efficiency)
    expected_kj = (mass_total * (roll + climb) + drag) / efficiency / 1000.0
    assert energy_kj == pytest.approx(expected_kj)


def test_separated_infrastructure_reduces_riding_energy(config, crr) -> None:
    length_m, gradient, speed = 1000.0, 0.0, 16.0 / 3.6
    roll = rolling_work_j_per_kg(length_m, gradient, crr)
    drag = drag_work_j(
        length_m, speed, config.bike.rho_air_kg_per_m3, config.bike.cda_m2
    )
    mass_total = RIDER_MASS_KG + config.bike.bike_mass_kg
    efficiency = config.bike.gross_muscular_efficiency
    mixed_traffic = bike_ride_energy_kj(
        roll, 0.0, 0.0, drag, mass_total, efficiency, 1.0
    )
    separated = bike_ride_energy_kj(
        roll, 0.0, 0.0, drag, mass_total, efficiency, config.bike.separated_infra_factor
    )
    assert separated < mixed_traffic


def test_ebike_motor_power_capped(config) -> None:
    ebike = config.bike.ebike
    assist = ebike.assist_factor_by_level[ebike.default_level]
    motor_power = ebike_motor_power_w(1000.0, assist, ebike.motor_power_cap_w)
    assert motor_power == pytest.approx(ebike.motor_power_cap_w)


def test_ebike_assist_increases_speed_below_cap(config, crr) -> None:
    ebike = config.bike.ebike
    # The gentlest assist level keeps the assisted speed under the cap, so
    # the comparison is not confounded by the governor.
    assist = ebike.assist_factor_by_level["eco"]
    mass = RIDER_MASS_KG + config.bike.ebike_mass_kg
    unassisted = solve_bike_speed_m_per_s(
        80.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assisted = solve_ebike_speed_m_per_s(
        80.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        assist, ebike.motor_power_cap_w, ebike.speed_cap_kmh,
    )
    assert unassisted < assisted < ebike.speed_cap_kmh * 1000.0 / 3600.0


def test_ebike_speed_is_governed_at_the_pedelec_cap(config, crr) -> None:
    ebike = config.bike.ebike
    # At the default assist level, 100 W of rider power alone stays well
    # under 25 km/h, but with assistance the raw solved speed would exceed
    # it: assistance cuts out above the cap (EU pedelec rules, 9.7), so the
    # result is governed exactly at the cap, not left unbounded.
    assist = ebike.assist_factor_by_level[ebike.default_level]
    mass = RIDER_MASS_KG + config.bike.ebike_mass_kg
    unassisted = solve_bike_speed_m_per_s(
        100.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert unassisted < ebike.speed_cap_kmh * 1000.0 / 3600.0
    speed = solve_ebike_speed_m_per_s(
        100.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        assist, ebike.motor_power_cap_w, ebike.speed_cap_kmh,
    )
    assert speed == pytest.approx(ebike.speed_cap_kmh * 1000.0 / 3600.0, rel=0.01)
