"""Section 9.3 walking-leg acceptance tests."""

from pathlib import Path

import pytest
from mobgrid.energy.rates import load_energy_config
from mobgrid.energy.walk import (
    gradient_factor,
    stair_time_and_energy,
    walking_speed_m_per_s,
    walking_time_and_energy,
)

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

MASS_KG = 70.0


@pytest.fixture
def config():
    return load_energy_config(CONFIG_PATH)


@pytest.fixture
def coefficients(config):
    return config.walking.gradient_polynomial_j_per_kg_m


@pytest.mark.parametrize(
    ("gradient", "expected"),
    [(0.05, 1.44), (0.10, 1.96), (-0.10, 0.45)],
)
def test_gradient_factor_reference_values(coefficients, gradient, expected) -> None:
    # Minetti et al. (2002) gradient factor checks (section 9.3).
    assert gradient_factor(gradient, coefficients) == pytest.approx(expected, abs=0.01)


def test_gradient_factor_is_one_on_the_flat(coefficients) -> None:
    assert gradient_factor(0.0, coefficients) == pytest.approx(1.0)


def test_walking_speed_equals_v0_on_the_flat() -> None:
    v0 = 4.8 * 1000.0 / 3600.0
    assert walking_speed_m_per_s(0.0, v0) == pytest.approx(v0)


def test_walking_speed_is_slower_up_and_down_steep_slopes() -> None:
    v0 = 4.8 * 1000.0 / 3600.0
    flat = walking_speed_m_per_s(0.0, v0)
    assert walking_speed_m_per_s(0.10, v0) < flat
    # Tobler's function peaks on a gentle -5% downhill slope, so a steep
    # downhill (well past that peak) is needed to be slower than flat.
    assert walking_speed_m_per_s(-0.20, v0) < flat


def test_walking_speed_peaks_on_a_gentle_downhill_slope() -> None:
    v0 = 4.8 * 1000.0 / 3600.0
    # v(i) depends on |i + 0.05|, so flat ground and a -10% slope give the
    # same speed, both slower than the -5% peak (section 9.3).
    assert walking_speed_m_per_s(0.0, v0) == pytest.approx(
        walking_speed_m_per_s(-0.10, v0)
    )
    assert walking_speed_m_per_s(-0.05, v0) > walking_speed_m_per_s(0.0, v0)


def test_flat_walking_energy_per_km_compendium(config, coefficients) -> None:
    # 1 km on the flat at 70 kg: 160 kJ with the Compendium (section 9.3).
    c0 = config.walking.c0_j_per_kg_m["compendium"]
    _, energy_kj = walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    assert energy_kj == pytest.approx(160.0, rel=0.01)


def test_flat_walking_energy_per_km_kh(config, coefficients) -> None:
    # 1 km on the flat at 70 kg: 211 kJ with KH (section 9.3).
    c0 = config.walking.c0_j_per_kg_m["kh"]
    _, energy_kj = walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    assert energy_kj == pytest.approx(211.0, rel=0.01)


def test_walking_leg_direction_changes_time_and_energy(config, coefficients) -> None:
    # Section 9.3/14.5 "per direction": reversing a sloped segment flips its
    # sign, so walking it forward and backward are not the same leg.
    c0 = config.walking.c0_j_per_kg_m["compendium"]
    forward_t, forward_e = walking_time_and_energy(
        [(100.0, 0.08)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    backward_t, backward_e = walking_time_and_energy(
        [(100.0, -0.08)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    assert forward_t != pytest.approx(backward_t)
    assert forward_e != pytest.approx(backward_e)
    # Climbing costs more energy than descending the same slope.
    assert forward_e > backward_e


def test_walking_time_and_energy_sum_segments(config, coefficients) -> None:
    c0 = config.walking.c0_j_per_kg_m["compendium"]
    one_segment = walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    two_segments = walking_time_and_energy(
        [(400.0, 0.0), (600.0, 0.0)], MASS_KG, config.walking.v0_kmh, c0, coefficients
    )
    assert two_segments[0] == pytest.approx(one_segment[0])
    assert two_segments[1] == pytest.approx(one_segment[1])


def test_stair_climb_10m_reference(config) -> None:
    # Climbing 10 m of stairs costs about 22.9 kJ at 70 kg (section 9.3).
    duration_s, energy_kj = stair_time_and_energy(
        10.0,
        "up",
        MASS_KG,
        config.stairs.up_speed_m_per_s,
        config.stairs.down_speed_m_per_s,
        config.stairs.up_efficiency,
        config.stairs.down_to_up_energy_ratio,
    )
    assert energy_kj == pytest.approx(22.9, rel=0.01)
    assert duration_s == pytest.approx(10.0 / 0.20)


def test_stair_descent_costs_about_a_third_of_the_climb(config) -> None:
    _, up_energy_kj = stair_time_and_energy(
        10.0,
        "up",
        MASS_KG,
        config.stairs.up_speed_m_per_s,
        config.stairs.down_speed_m_per_s,
        config.stairs.up_efficiency,
        config.stairs.down_to_up_energy_ratio,
    )
    down_duration_s, down_energy_kj = stair_time_and_energy(
        10.0,
        "down",
        MASS_KG,
        config.stairs.up_speed_m_per_s,
        config.stairs.down_speed_m_per_s,
        config.stairs.up_efficiency,
        config.stairs.down_to_up_energy_ratio,
    )
    assert down_energy_kj == pytest.approx(up_energy_kj / 3, rel=0.01)
    assert down_duration_s == pytest.approx(10.0 / 0.30)
