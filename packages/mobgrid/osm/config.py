"""Network extraction and edge-access configuration for section 8.1."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

Mode = Literal["car", "bike", "foot"]
SpeedContext = Literal["urban", "rural", "zone30", "motorway"]
PositiveSpeed = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
BikeClass = Literal[
    "separated_track_path",
    "painted_lane",
    "bus_lane",
    "low_speed",
    "mixed_traffic",
]


class AccessRule(BaseModel):
    """OSM access precedence and defaults for one travel mode."""

    model_config = ConfigDict(extra="forbid")

    precedence: tuple[str, ...]
    denied: tuple[str, ...]
    hard_excluded_highways: tuple[str, ...] = ()
    excluded_highways: tuple[str, ...]
    mode_specific_only_highways: tuple[str, ...] = ()
    explicit_allowed_values: tuple[str, ...] = ()
    included_highways: tuple[str, ...] = ()
    sidewalk_values: tuple[str, ...] = ()
    default_allowed: bool


class UrbanDensityConfig(BaseModel):
    """Road-density fallback for untagged car-speed context."""

    model_config = ConfigDict(extra="forbid")

    radius_m: float = Field(gt=0)
    fallback_threshold_km: float = Field(ge=0)
    fit_strategy: Literal["max_length_weighted_agreement"]


class CarDelayConfig(BaseModel):
    """Free-flow control and junction delay parameters."""

    model_config = ConfigDict(extra="forbid")

    signal_s: float = Field(ge=0)
    stop_s: float = Field(ge=0)
    give_way_s: float = Field(ge=0)
    mini_roundabout_s: float = Field(ge=0)
    crossing_s: float = Field(ge=0)
    at_to_node_s: float = Field(ge=0)
    degree_threshold: int = Field(gt=0)


class CarSpeedConfig(BaseModel):
    """Configured defaults, class factors, density rule and delay parameters."""

    model_config = ConfigDict(extra="forbid")

    defaults_kmh_by_context: dict[SpeedContext, PositiveSpeed]
    class_overrides_kmh_by_context: dict[
        SpeedContext, dict[str, PositiveSpeed]
    ]
    default_caps_kmh_by_highway: dict[str, PositiveSpeed]
    rural_oneway_speed_kmh_by_highway: dict[str, PositiveSpeed]
    realism_factor_by_highway: dict[str, PositiveSpeed]
    speed_limit_bucket_upper_bounds_kmh: tuple[PositiveSpeed, ...]
    urban_density: UrbanDensityConfig
    delays: CarDelayConfig

    @field_validator("speed_limit_bucket_upper_bounds_kmh")
    @classmethod
    def validate_speed_buckets(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if not value or any(bound <= 0 for bound in value):
            raise ValueError("speed buckets must contain positive upper bounds")
        if tuple(sorted(set(value))) != value:
            raise ValueError("speed bucket upper bounds must increase strictly")
        return value


class BikeSpeedTableConfig(BaseModel):
    """Provisional interpolation grid, tolerances and bike speed caps (9.7)."""

    model_config = ConfigDict(extra="forbid")

    grade_min: float
    grade_max: float
    grade_step: float = Field(gt=0, allow_inf_nan=False)
    clipped_grade_report_limit: int = Field(gt=0)
    speed_tolerance_kmh: float = Field(gt=0, allow_inf_nan=False)
    energy_relative_tolerance: float = Field(gt=0, allow_inf_nan=False)
    class_cap_kmh: dict[str, PositiveSpeed]
    highway_cap_kmh: dict[str, PositiveSpeed]


class BikeEdgeCostConfig(BaseModel):
    """Provisional bicycle stop probabilities and OSM surface mapping."""

    model_config = ConfigDict(extra="forbid")

    stop_sign_probability: float = Field(ge=0, le=1)
    give_way_probability: float = Field(ge=0, le=1)
    uncontrolled_junction_probability_by_class: dict[BikeClass, Probability]
    crossing_probability_by_class: dict[BikeClass, Probability]
    surface_aliases: dict[str, str]
    surface_by_tracktype: dict[str, str]
    surface_default_by_highway: dict[str, str]


class NetworkConfig(BaseModel):
    """Validated OSM extraction and tiling parameters."""

    model_config = ConfigDict(extra="forbid")

    states: dict[int, str]
    contour_source_id: str
    kept_tags: tuple[str, ...]
    area_simplify_tolerance_m: float = Field(gt=0)
    elevation_smoothing_window_m: float = Field(gt=0, allow_inf_nan=False)
    known_highways: tuple[str, ...]
    access_rules: dict[Mode, AccessRule]
    oneway_yes: tuple[str, ...]
    oneway_no: tuple[str, ...]
    oneway_reverse: tuple[str, ...]
    control_highways: tuple[str, ...]
    signal_highways: tuple[str, ...]
    maxspeed_tokens_kmh: dict[str, float | None]
    speed_context_tags: tuple[str, ...]
    speed_context_values: dict[
        str, Literal["urban", "rural", "zone30", "motorway"]
    ]
    car_speed: CarSpeedConfig
    mph_to_kmh: float = Field(gt=0)
    busway_values: tuple[str, ...]
    bike_classes: dict[BikeClass, tuple[str, ...]]
    bike_speed_table: BikeSpeedTableConfig
    bike_edge_costs: BikeEdgeCostConfig
    tile_size_m: int = Field(gt=0)


def load_network_config(path: str | Path) -> NetworkConfig:
    """Load and validate ``config/network.yaml``."""
    with Path(path).open(encoding="utf-8") as stream:
        return NetworkConfig.model_validate(yaml.safe_load(stream))
