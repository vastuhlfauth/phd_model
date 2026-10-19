"""Section 9.7 bike-leg acceptance tests."""

from pathlib import Path

import pytest
from mobgrid.energy.bike import (
    bike_ride_energy_kj,
    climbing_work_j_per_kg,
    drag_work_j,
    ebike_motor_power_w,
    ebike_ride_speed_and_power,
    ebike_rider_share,
    required_power_w,
    ride_speed_and_power,
    rolling_work_j_per_kg,
    select_ride_power_w,
    solve_bike_speed_m_per_s,
    stop_energy_kj,
    stop_time_s,
    unloaded_pedalling_energy_kj,
)
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

# Consistency check of section 9.7: 16 km/h on the flat, M = 85 kg.
RIDER_SPEED_M_S = 16.0 / 3.6
RIDER_MASS_KG = 85.0
# Rider's own body mass (excludes the bike), for the unloaded pedalling
# cost, which is charged on the rider alone (section 9.7).
RIDER_BODY_MASS_KG = 70.0


@pytest.fixture
def config():
    return load_energy_config(CONFIG_PATH)


@pytest.fixture
def crr(config):
    return config.bike.surface_crr["asphalt_concrete_paved_default"]


def test_required_power_matches_reference_at_16kmh_flat(config, crr) -> None:
    # ~52.5 W of rider power at 16 km/h on the flat, M = 85 kg (section 9.7).
    power_w = required_power_w(
        RIDER_SPEED_M_S, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert power_w == pytest.approx(52.5, rel=0.02)


def test_metabolic_rate_at_reference_power_matches_kh_and_compendium(
    config, crr
) -> None:
    power_w = required_power_w(
        RIDER_SPEED_M_S, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    work_rate_kj_per_min = power_w / config.bike.gross_muscular_efficiency * 60 / 1000
    time_s = 1000.0 / RIDER_SPEED_M_S
    unloaded_kj = unloaded_pedalling_energy_kj(
        time_s, RIDER_BODY_MASS_KG, config.bike.pedalling_unloaded_net_met
    )
    rate_kj_per_min = work_rate_kj_per_min + unloaded_kj / (time_s / 60.0)
    # Consistent with KH (14.7 kJ/min at 12 km/h) and the Compendium
    # leisure value (4.0 MET), plus the unloaded pedalling cost: about
    # 18.2 kJ/min (section 9.7).
    assert rate_kj_per_min == pytest.approx(18.2, rel=0.02)


def test_required_power_round_trips_through_the_solver(config, crr) -> None:
    power_w = required_power_w(
        RIDER_SPEED_M_S, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    speed = solve_bike_speed_m_per_s(
        power_w, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert speed == pytest.approx(RIDER_SPEED_M_S, rel=0.01)


def test_mass_effect_on_speed_flat(config, crr) -> None:
    # +10 kg at the same power on the flat: speed -2.4% (section 9.7).
    power_w = required_power_w(
        RIDER_SPEED_M_S, RIDER_MASS_KG, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
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


def test_one_stop_energy_scales_with_rider_share(config) -> None:
    full = stop_energy_kj(
        RIDER_SPEED_M_S, RIDER_MASS_KG, config.bike.gross_muscular_efficiency
    )
    half = stop_energy_kj(
        RIDER_SPEED_M_S, RIDER_MASS_KG, config.bike.gross_muscular_efficiency,
        rider_share=0.5,
    )
    assert half == pytest.approx(full / 2.0)


def test_stop_time_matches_formula(config) -> None:
    stops = config.bike.stops
    duration_s = stop_time_s(
        RIDER_SPEED_M_S, stops.deceleration_m_per_s2, stops.acceleration_m_per_s2,
        stops.signal_cycle_s, stops.red_time_s,
    )
    expected_s = (
        RIDER_SPEED_M_S / stops.deceleration_m_per_s2
        + stops.red_time_s**2 / (2.0 * stops.signal_cycle_s)
        + RIDER_SPEED_M_S / stops.acceleration_m_per_s2
    )
    assert duration_s == pytest.approx(expected_s)


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
    # On a descent (i < 0) with no power, gravity still sets a positive
    # equilibrium speed when it exceeds rolling resistance.
    speed = solve_bike_speed_m_per_s(
        0.0, RIDER_MASS_KG, -0.08, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert speed > 0.0


def test_select_ride_power_on_the_flat_is_p0() -> None:
    assert select_ride_power_w(0.0, p0_w=100.0, k=2.0, p_max_w=300.0) == 100.0


def test_select_ride_power_is_capped_on_climbs() -> None:
    assert select_ride_power_w(0.5, p0_w=100.0, k=2.0, p_max_w=150.0) == 150.0


def test_select_ride_power_is_reduced_but_not_zero_on_a_gentle_descent() -> None:
    # Section 9.7: P_r = clamp(P0.(1+k.i), 0, Pmax) on every grade, so a
    # gentle descent still has positive rider power (previously a bug
    # zeroed power -- and so speed -- immediately past i = 0).
    power = select_ride_power_w(-0.003, p0_w=100.0, k=37.0, p_max_w=300.0)
    assert 0.0 < power < 100.0


def test_select_ride_power_is_zero_past_the_descent_cutoff() -> None:
    # i <= -1/k: clamp(P0.(1+k.i), 0, Pmax) reaches 0.
    assert select_ride_power_w(-1.0, p0_w=100.0, k=2.0, p_max_w=300.0) == 0.0


def test_ride_speed_and_power_has_no_zero_speed_plateau(config, crr) -> None:
    # The bug: speed was 0 for grades in about (-0.7%, 0%) under the old
    # "P_r = 0 on every descent" rule. Scan -10% to +10% and require a
    # strictly positive, non-increasing speed throughout (section 9.7).
    p0_w, k, p_max_w = 52.5, 37.0, 200.0
    v_max_descent_m_per_s = 30.0 / 3.6
    mass_total = RIDER_MASS_KG
    previous_speed = None
    grade = -0.10
    while grade <= 0.10 + 1e-9:
        speed, power = ride_speed_and_power(
            grade, p0_w, k, p_max_w, mass_total, crr, config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
            v_max_descent_m_per_s,
        )
        assert speed > 0.0, f"zero speed at grade={grade}"
        assert power >= 0.0
        if previous_speed is not None:
            assert speed <= previous_speed + 1e-9, f"speed increased at grade={grade}"
        previous_speed = speed
        grade += 0.005


def test_ride_speed_and_power_caps_a_steep_descent(config, crr) -> None:
    v_max_descent_m_per_s = 30.0 / 3.6
    speed, power = ride_speed_and_power(
        -0.15, 52.5, 37.0, 200.0, RIDER_MASS_KG, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        v_max_descent_m_per_s,
    )
    assert speed == pytest.approx(v_max_descent_m_per_s)
    # The power that exactly holds the capped speed is well under what
    # free coasting would otherwise reach; never negative (braking, not
    # negative pedalling, absorbs the rest).
    assert 0.0 <= power


def test_ride_energy_components_direction_asymmetry() -> None:
    # Same edge, opposite directions: the signed climb term flips sign
    # (section 9.7; 14.7 "per edge and direction").
    length_m, gradient = 100.0, 0.05
    forward_climb = climbing_work_j_per_kg(length_m, gradient)
    backward_climb = climbing_work_j_per_kg(length_m, -gradient)
    assert forward_climb > 0.0
    assert backward_climb == pytest.approx(-forward_climb)


def test_unloaded_pedalling_energy_scales_with_mass_and_time() -> None:
    # e = m . u_ped . t_ped (section 9.7); 1 net MET = 0.0732 kJ/kg/min.
    kj = unloaded_pedalling_energy_kj(60.0, 70.0, 1.0)
    assert kj == pytest.approx(0.0732 * 70.0)
    assert unloaded_pedalling_energy_kj(120.0, 70.0, 1.0) == pytest.approx(kj * 2.0)
    assert unloaded_pedalling_energy_kj(60.0, 0.0, 1.0) == 0.0


def test_bike_ride_energy_adds_unloaded_pedalling_cost(config, crr) -> None:
    length_m, gradient, speed = 1000.0, 0.02, 16.0 / 3.6
    roll = rolling_work_j_per_kg(length_m, gradient, crr)
    climb = climbing_work_j_per_kg(length_m, gradient)
    drag = drag_work_j(
        length_m, speed, config.bike.rho_air_kg_per_m3, config.bike.cda_m2
    )
    mass_total = RIDER_BODY_MASS_KG + config.bike.bike_mass_kg
    efficiency = config.bike.gross_muscular_efficiency
    pedalled_time_s = length_m / speed
    work_only = bike_ride_energy_kj(roll, climb, 0.0, drag, mass_total, efficiency)
    with_unloaded = bike_ride_energy_kj(
        roll, climb, 0.0, drag, mass_total, efficiency,
        rider_mass_kg=RIDER_BODY_MASS_KG, pedalled_time_s=pedalled_time_s,
        unloaded_net_met_per_min=config.bike.pedalling_unloaded_net_met,
    )
    expected_unloaded = unloaded_pedalling_energy_kj(
        pedalled_time_s, RIDER_BODY_MASS_KG, config.bike.pedalling_unloaded_net_met
    )
    assert with_unloaded == pytest.approx(work_only + expected_unloaded)


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


def test_bike_ride_energy_scales_with_rider_share(config, crr) -> None:
    length_m, gradient, speed = 1000.0, 0.02, 16.0 / 3.6
    roll = rolling_work_j_per_kg(length_m, gradient, crr)
    climb = climbing_work_j_per_kg(length_m, gradient)
    drag = drag_work_j(
        length_m, speed, config.bike.rho_air_kg_per_m3, config.bike.cda_m2
    )
    mass_total = RIDER_MASS_KG + config.bike.ebike_mass_kg
    efficiency = config.bike.gross_muscular_efficiency
    full = bike_ride_energy_kj(roll, climb, 0.0, drag, mass_total, efficiency)
    half = bike_ride_energy_kj(
        roll, climb, 0.0, drag, mass_total, efficiency, rider_share=0.5
    )
    assert half == pytest.approx(full / 2.0)


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


def test_ebike_rider_share_is_one_without_a_motor() -> None:
    assert ebike_rider_share(80.0, 0.0) == pytest.approx(1.0)
    assert ebike_rider_share(0.0, 0.0) == pytest.approx(1.0)


def test_ebike_rider_share_falls_with_more_motor_power() -> None:
    assert ebike_rider_share(80.0, 80.0) == pytest.approx(0.5)
    assert ebike_rider_share(80.0, 240.0) == pytest.approx(0.25)


def test_ebike_assist_increases_speed_below_cap(config, crr) -> None:
    ebike = config.bike.ebike
    # The gentlest assist level keeps the assisted speed under the cap, so
    # the comparison is not confounded by the governor.
    assist = ebike.assist_factor_by_level["eco"]
    mass = RIDER_MASS_KG + config.bike.ebike_mass_kg
    speed_cap_m_per_s = ebike.speed_cap_kmh * 1000.0 / 3600.0
    v_max_descent_m_per_s = speed_cap_m_per_s
    unassisted = solve_bike_speed_m_per_s(
        80.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assisted, rider_power, motor_power = ebike_ride_speed_and_power(
        0.0, 80.0, 0.0, 80.0, mass, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency, assist,
        ebike.motor_power_cap_w, speed_cap_m_per_s, v_max_descent_m_per_s,
    )
    assert unassisted < assisted < speed_cap_m_per_s
    assert rider_power == pytest.approx(80.0)
    assert motor_power > 0.0


def test_ebike_speed_is_governed_at_the_pedelec_cap(config, crr) -> None:
    ebike = config.bike.ebike
    # At the default assist level, 100 W of rider power alone stays well
    # under 25 km/h, but with assistance the raw solved speed would exceed
    # it: assistance cuts out above the cap (EU pedelec rules, 9.7), so the
    # result is governed exactly at the cap, not left unbounded.
    assist = ebike.assist_factor_by_level[ebike.default_level]
    mass = RIDER_MASS_KG + config.bike.ebike_mass_kg
    speed_cap_m_per_s = ebike.speed_cap_kmh * 1000.0 / 3600.0
    v_max_descent_m_per_s = speed_cap_m_per_s
    unassisted = solve_bike_speed_m_per_s(
        100.0, mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    assert unassisted < speed_cap_m_per_s
    speed, rider_power, motor_power = ebike_ride_speed_and_power(
        0.0, 100.0, 0.0, 100.0, mass, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency, assist,
        ebike.motor_power_cap_w, speed_cap_m_per_s, v_max_descent_m_per_s,
    )
    assert speed == pytest.approx(speed_cap_m_per_s, rel=0.01)
    # The motor backs off partially to hold the cap (not to zero): less
    # than its full uncapped assistance, but still positive here, since
    # the rider alone could not reach the cap.
    full_motor_power = ebike_motor_power_w(100.0, assist, ebike.motor_power_cap_w)
    assert 0.0 < motor_power < full_motor_power


def test_ebike_ride_caps_a_steep_descent_reducing_rider_first(config, crr) -> None:
    ebike = config.bike.ebike
    assist = ebike.assist_factor_by_level[ebike.default_level]
    mass = RIDER_MASS_KG + config.bike.ebike_mass_kg
    speed_cap_m_per_s = ebike.speed_cap_kmh * 1000.0 / 3600.0
    v_max_descent_m_per_s = 30.0 / 3.6
    speed, rider_power, motor_power = ebike_ride_speed_and_power(
        -0.15, 52.5, 37.0, 200.0, mass, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency, assist,
        ebike.motor_power_cap_w, speed_cap_m_per_s, v_max_descent_m_per_s,
    )
    assert speed == pytest.approx(v_max_descent_m_per_s)
    assert motor_power == pytest.approx(0.0)
    assert rider_power >= 0.0
