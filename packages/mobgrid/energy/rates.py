"""Energy rate configuration for section 9."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

#: Standard gravity, m/s^2 (sections 9.3, 9.7).
GRAVITY_M_S2 = 9.81

#: Energy of one net MET-minute per kilogram of body mass, kJ: 0.0175
#: kcal/kg x 4.184 kJ/kcal (section 9.1).
MET_MINUTE_KJ_PER_KG = 0.0732

#: Seconds per minute, converting the stored second-based durations to the
#: minute-based rates of section 9.2.
SECONDS_PER_MINUTE = 60.0

#: The two rate sets of section 9.1, chosen in configuration.
RateSet = Literal["kh", "compendium"]


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` to ``[low, high]`` (sections 9.5, 9.6)."""
    return min(max(value, low), high)


class ActivityRate(BaseModel):
    """One row of the section 9.2 reference-rate table.

    ``kh_kj_per_min`` is Koelbl & Helbing's absolute rate for a reference
    adult; ``compendium_net_met`` is the matching Compendium 2024 code's
    gross MET value minus 1 (net MET). A null field means section 9.2's
    table gives no value for that rate set.
    """

    model_config = ConfigDict(extra="forbid")
    kh_kj_per_min: float | None = None
    compendium_net_met: float | None = None


class WalkingRateConfig(BaseModel):
    """Walking speed and cost parameters (section 9.3)."""

    model_config = ConfigDict(extra="forbid")
    v0_kmh: float = Field(gt=0)
    c0_j_per_kg_m: dict[Literal["compendium", "kh"], float]
    gradient_polynomial_j_per_kg_m: list[float] = Field(min_length=6, max_length=6)
    gradient_valid_range: tuple[float, float]


class StairsConfig(BaseModel):
    """Stairs and level-change parameters (section 9.3)."""

    model_config = ConfigDict(extra="forbid")
    up_speed_m_per_s: float = Field(gt=0)
    down_speed_m_per_s: float = Field(gt=0)
    up_efficiency: float = Field(gt=0, le=1)
    down_to_up_energy_ratio: float = Field(gt=0)
    level_change_height_m: dict[str, tuple[float, float]]
    escalator_depth_threshold_m: float = Field(ge=0)


class WaitingConfig(BaseModel):
    """Waiting and transfer parameters (section 9.4)."""

    model_config = ConfigDict(extra="forbid")
    w_planned_min: float = Field(ge=0)
    headway_regime_threshold_min: float = Field(gt=0)
    cv_defaults: dict[str, float]


class PtRideConfig(BaseModel):
    """Public transport ride energy parameters (section 9.5).

    ``headway_min_am_peak``, ``station_height_m`` and
    ``access_walk_m_by_density`` are provisional, used only by the
    section 9.9 re-estimation (step 11: ``mobgrid.budget.emp``), which
    has no headway, station-depth or access-distance data of its own
    (TODO(confirm), section 9.9).
    """

    model_config = ConfigDict(extra="forbid")
    r_sit_kj_per_min: float = Field(gt=0)
    r_relaxed_kj_per_min: float = Field(gt=0)
    r_restless_kj_per_min: float = Field(gt=0)
    load_factor_max: dict[str, float]
    standing_share_am_peak: dict[str, float]
    headway_min_am_peak: dict[str, float]
    station_height_m: dict[str, float]
    access_walk_m_by_density: dict[str, float]


class WalkToCarConfig(BaseModel):
    """Walk-to-car time parameters (section 9.6)."""

    model_config = ConfigDict(extra="forbid")
    house_min: float = Field(ge=0)
    apartment_min_by_density: dict[str, float]


class CarpoolPassengerConfig(BaseModel):
    """Carpool passenger origin legs (section 9.6); provisional, not yet
    confirmed against any survey or observed pickup pattern."""

    model_config = ConfigDict(extra="forbid")
    walk_to_meeting_point_min: float = Field(ge=0)
    wait_standing_min: float = Field(ge=0)


class CarConfig(BaseModel):
    """Car leg parameters (section 9.6)."""

    model_config = ConfigDict(extra="forbid")
    r_congested_cap_kj_per_min: float = Field(gt=0)
    congestion_rho_max: float = Field(gt=1)
    walk_to_car: WalkToCarConfig
    parking_search_min_by_density: dict[str, float]
    walk_from_car_min_by_density: dict[str, float]
    carpool_passenger: CarpoolPassengerConfig


class BikePowerConfig(BaseModel):
    """Force-balance power-selection parameters; null until calibrated
    against observed commuter speeds on gradients (section 9.7)."""

    model_config = ConfigDict(extra="forbid")
    p0_w: float | None = None
    k: float | None = None
    p_max_w: float | None = None
    v_max_descent_kmh: float | None = None


class EbikeConfig(BaseModel):
    """E-bike pedelec assistance parameters (section 9.7)."""

    model_config = ConfigDict(extra="forbid")
    motor_power_cap_w: float = Field(gt=0)
    speed_cap_kmh: float = Field(gt=0)
    assist_factor_by_level: dict[str, float]
    default_level: str
    effort_factor_by_level: dict[str, float]


class StopsConfig(BaseModel):
    """Bike stop time parameters (section 9.7); not yet calibrated against
    observed signal timings or braking/acceleration rates.

    ``stops_per_km`` is provisional, used only by the section 9.9
    re-estimation (step 11)."""

    model_config = ConfigDict(extra="forbid")
    deceleration_m_per_s2: float = Field(gt=0)
    acceleration_m_per_s2: float = Field(gt=0)
    signal_cycle_s: float = Field(gt=0)
    red_time_s: float = Field(ge=0)
    stops_per_km: float = Field(ge=0)


class BikeConfig(BaseModel):
    """Bike leg parameters (section 9.7).

    ``get_park_min`` is used by step 11's re-estimation to recover
    ride-only time from a trip's declared duration. ``pedalling_unloaded_net_met``
    is the unloaded pedalling cost, in net MET-minutes per pedalled
    minute, charged on the rider's own mass regardless of mechanical
    power (ACSM leg-cycling equation; Swain 2000)."""

    model_config = ConfigDict(extra="forbid")
    bike_mass_kg: float = Field(gt=0)
    ebike_mass_kg: float = Field(gt=0)
    drivetrain_efficiency: float = Field(gt=0, le=1)
    gross_muscular_efficiency: float = Field(gt=0, le=1)
    rho_air_kg_per_m3: float = Field(gt=0)
    cda_m2: float = Field(gt=0)
    separated_infra_factor: float = Field(gt=0, le=1)
    get_park_min: float = Field(ge=0)
    pedalling_unloaded_net_met: float = Field(gt=0)
    surface_crr: dict[str, float]
    power: BikePowerConfig
    ebike: EbikeConfig
    stops: StopsConfig


class EnergyConfig(BaseModel):
    """Full configuration for ``config/energy.yaml`` (section 9)."""

    model_config = ConfigDict(extra="forbid")
    reference_mass_kg: float = Field(gt=0)
    rate_set: RateSet
    activity_rates: dict[str, ActivityRate]
    walking: WalkingRateConfig
    stairs: StairsConfig
    waiting: WaitingConfig
    pt_ride: PtRideConfig
    car: CarConfig
    bike: BikeConfig


def load_energy_config(path: str | Path) -> EnergyConfig:
    """Load and validate ``config/energy.yaml``."""
    with Path(path).open(encoding="utf-8") as stream:
        return EnergyConfig.model_validate(yaml.safe_load(stream))


def activity_rate_kj_per_min(
    rate: ActivityRate, rate_set: RateSet, mass_kg: float
) -> float:
    """Rate of one section 9.2 activity, kJ above rest per minute.

    KH rates are absolute, for a reference adult (section 9.1), and do not
    scale with ``mass_kg``; Compendium rates are net MET-minutes, which
    scale with body mass through ``MET_MINUTE_KJ_PER_KG``.
    """
    if rate_set == "kh":
        if rate.kh_kj_per_min is None:
            raise ValueError("no KH rate is given for this activity")
        return rate.kh_kj_per_min
    if rate.compendium_net_met is None:
        raise ValueError("no Compendium rate is given for this activity")
    return rate.compendium_net_met * MET_MINUTE_KJ_PER_KG * mass_kg


def sedentary_energy_kj(rate_kj_per_min: float, duration_s: float) -> float:
    """Energy of a sedentary, standing or driving leg, e = r x t (9.2)."""
    return rate_kj_per_min * duration_s / SECONDS_PER_MINUTE
