"""Section 9.2, 9.4, 9.5 and 9.6 leg-chain acceptance tests."""

from pathlib import Path

import pytest
from mobgrid.energy.legs import (
    Leg,
    car_drive_leg,
    car_passenger_leg,
    driving_rate_kj_per_min,
    expected_wait_s,
    pt_ride_leg,
    pt_ride_rate_kj_per_min,
    pt_standing_rate_kj_per_min,
    pt_standing_share,
    sedentary_leg,
    trip_time_and_energy,
    waiting_leg,
)
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"


@pytest.fixture
def config():
    return load_energy_config(CONFIG_PATH)


def test_trip_chains_sum_duration_and_energy() -> None:
    # T = sum(t), E = sum(e) (section 9.2).
    legs = [Leg(60.0, 1.0), Leg(120.0, 2.5), Leg(30.0, 0.5)]
    duration_s, energy_kj = trip_time_and_energy(legs)
    assert duration_s == pytest.approx(210.0)
    assert energy_kj == pytest.approx(4.0)


def test_sedentary_leg_matches_rate_times_duration() -> None:
    leg = sedentary_leg(600.0, 2.6)
    assert leg.duration_s == pytest.approx(600.0)
    assert leg.energy_kj == pytest.approx(26.0)


def test_expected_wait_random_arrivals_regime(config) -> None:
    # w = h/2 . (1 + CV^2) for headways up to the regime threshold (9.4).
    headway_s = 5 * 60.0
    cv = config.waiting.cv_defaults["bus_mixed_traffic"]
    wait_s = expected_wait_s(
        headway_s, cv, config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0,
    )
    assert wait_s == pytest.approx(headway_s / 2 * (1 + cv**2))


def test_expected_wait_falls_back_to_planned_beyond_threshold(config) -> None:
    headway_s = 20 * 60.0
    wait_s = expected_wait_s(
        headway_s, 0.15, config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0,
    )
    assert wait_s == pytest.approx(config.waiting.w_planned_min * 60.0)


def test_waiting_leg_uses_the_standing_relaxed_rate(config) -> None:
    rate = config.activity_rates["standing_relaxed"]
    relaxed_kj_per_min = rate.kh_kj_per_min
    leg = waiting_leg(
        5 * 60.0, 0.15, config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0, relaxed_kj_per_min,
    )
    expected_duration_s = expected_wait_s(
        5 * 60.0, 0.15, config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0,
    )
    assert leg.duration_s == pytest.approx(expected_duration_s)
    assert leg.energy_kj == pytest.approx(
        relaxed_kj_per_min * expected_duration_s / 60.0
    )


def test_pt_standing_share_is_zero_below_one_passenger_per_seat() -> None:
    assert pt_standing_share(0.5) == 0.0


def test_pt_standing_share_rises_with_load_factor() -> None:
    assert pt_standing_share(1.0) == 0.0
    assert pt_standing_share(2.0) == pytest.approx(0.5)
    assert pt_standing_share(4.0) == pytest.approx(0.75)


def test_pt_standing_share_rejects_non_positive_load_factor() -> None:
    with pytest.raises(ValueError):
        pt_standing_share(0.0)


def test_pt_ride_rate_at_capacity_is_all_sitting(config) -> None:
    rate = pt_ride_rate_kj_per_min(
        1.0, 4.0, config.pt_ride.r_sit_kj_per_min,
        config.pt_ride.r_relaxed_kj_per_min, config.pt_ride.r_restless_kj_per_min,
    )
    assert rate == pytest.approx(config.pt_ride.r_sit_kj_per_min)


def test_pt_ride_rate_at_crush_load_is_fully_restless(config) -> None:
    load_factor_max = config.pt_ride.load_factor_max["metro"]
    rate = pt_standing_rate_kj_per_min(
        load_factor_max, load_factor_max, config.pt_ride.r_relaxed_kj_per_min,
        config.pt_ride.r_restless_kj_per_min,
    )
    assert rate == pytest.approx(config.pt_ride.r_restless_kj_per_min)


def test_pt_ride_leg_combines_sitting_and_standing(config) -> None:
    leg = pt_ride_leg(
        600.0, 2.0, config.pt_ride.load_factor_max["metro"],
        config.pt_ride.r_sit_kj_per_min, config.pt_ride.r_relaxed_kj_per_min,
        config.pt_ride.r_restless_kj_per_min,
    )
    rate = pt_ride_rate_kj_per_min(
        2.0, config.pt_ride.load_factor_max["metro"],
        config.pt_ride.r_sit_kj_per_min, config.pt_ride.r_relaxed_kj_per_min,
        config.pt_ride.r_restless_kj_per_min,
    )
    assert leg.energy_kj == pytest.approx(rate * 10.0)


def test_driving_rate_free_flow_at_rho_one(config) -> None:
    rate = config.activity_rates["driving_free_flow"]
    free_flow = rate.kh_kj_per_min
    assert driving_rate_kj_per_min(
        1.0, config.car.congestion_rho_max, free_flow,
        config.car.r_congested_cap_kj_per_min,
    ) == pytest.approx(free_flow)


def test_driving_rate_caps_at_rho_max(config) -> None:
    rate = config.activity_rates["driving_free_flow"]
    free_flow = rate.kh_kj_per_min
    at_cap = driving_rate_kj_per_min(
        config.car.congestion_rho_max, config.car.congestion_rho_max, free_flow,
        config.car.r_congested_cap_kj_per_min,
    )
    beyond_cap = driving_rate_kj_per_min(
        config.car.congestion_rho_max * 2, config.car.congestion_rho_max,
        free_flow, config.car.r_congested_cap_kj_per_min,
    )
    assert at_cap == pytest.approx(config.car.r_congested_cap_kj_per_min)
    assert beyond_cap == pytest.approx(config.car.r_congested_cap_kj_per_min)


def test_car_drive_leg_matches_driving_rate(config) -> None:
    rate = config.activity_rates["driving_free_flow"]
    leg = car_drive_leg(
        600.0, 1.0, config.car.congestion_rho_max, rate.kh_kj_per_min,
        config.car.r_congested_cap_kj_per_min,
    )
    assert leg.energy_kj == pytest.approx(rate.kh_kj_per_min * 10.0)


def test_car_passenger_leg_uses_the_sitting_rate(config) -> None:
    sitting = config.activity_rates["sitting_vehicle"].kh_kj_per_min
    leg = car_passenger_leg(600.0, sitting)
    assert leg.energy_kj == pytest.approx(sitting * 10.0)
