"""Section 9.2 reference-rate acceptance tests."""

from pathlib import Path

import pytest
from mobgrid.energy.rates import (
    ActivityRate,
    EnergyConfig,
    load_energy_config,
    sedentary_energy_kj,
)
from mobgrid.energy.rates import activity_rate_kj_per_min as rate_kj_per_min

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

# Reference mass of the numerical examples in section 9.2.
MASS_KG = 70.0


def _config() -> EnergyConfig:
    return load_energy_config(CONFIG_PATH)


def test_config_loads_and_validates() -> None:
    config = _config()
    assert config.reference_mass_kg > 0
    assert config.rate_set in ("kh", "compendium")
    # Bike power parameters are unconfirmed placeholders (section 9.7).
    assert config.bike.power.p0_w is None


@pytest.mark.parametrize(
    ("activity", "kh_expected"),
    [
        ("sitting_vehicle", 1.5),
        ("standing_relaxed", 2.6),
        ("standing_restless", 6.7),
        ("driving_free_flow", 4.2),
        ("driving_congested_cap", 8.0),
    ],
)
def test_kh_rate_is_absolute_for_a_reference_adult(
    activity: str, kh_expected: float
) -> None:
    rate = _config().activity_rates[activity]
    # KH rates (section 9.1: "for a reference adult") do not scale with mass.
    assert rate_kj_per_min(rate, "kh", MASS_KG) == pytest.approx(kh_expected)
    assert rate_kj_per_min(rate, "kh", 2 * MASS_KG) == pytest.approx(kh_expected)


@pytest.mark.parametrize(
    ("activity", "compendium_expected_at_70kg"),
    [
        ("sitting_vehicle", 1.5),
        ("standing_relaxed", 2.6),
        ("driving_free_flow", 5.1),
    ],
)
def test_compendium_rate_matches_section_9_2(
    activity: str, compendium_expected_at_70kg: float
) -> None:
    rate = _config().activity_rates[activity]
    value = rate_kj_per_min(rate, "compendium", MASS_KG)
    # Section 9.2's own figures are rounded to one decimal place.
    assert value == pytest.approx(compendium_expected_at_70kg, rel=0.03)


def test_compendium_rate_scales_with_mass() -> None:
    rate = _config().activity_rates["sitting_vehicle"]
    at_70 = rate_kj_per_min(rate, "compendium", 70.0)
    at_140 = rate_kj_per_min(rate, "compendium", 140.0)
    assert at_140 == pytest.approx(2 * at_70)


def test_missing_rate_raises_instead_of_guessing() -> None:
    # standing_restless has no Compendium equivalent (section 9.2).
    rate = _config().activity_rates["standing_restless"]
    with pytest.raises(ValueError):
        rate_kj_per_min(rate, "compendium", MASS_KG)


def test_missing_kh_rate_raises() -> None:
    rate = ActivityRate(kh_kj_per_min=None, compendium_net_met=1.0)
    with pytest.raises(ValueError):
        rate_kj_per_min(rate, "kh", MASS_KG)


def test_sedentary_energy_is_rate_times_duration() -> None:
    # e = r x t (section 9.2): 2.6 kJ/min for 10 min = 26 kJ.
    assert sedentary_energy_kj(2.6, 600.0) == pytest.approx(26.0)
