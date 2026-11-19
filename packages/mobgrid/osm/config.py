"""Network extraction and edge-access configuration for section 8.1."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["car", "bike", "foot"]


class AccessRule(BaseModel):
    """OSM access precedence and defaults for one travel mode."""

    model_config = ConfigDict(extra="forbid")

    precedence: tuple[str, ...]
    denied: tuple[str, ...]
    hard_excluded_highways: tuple[str, ...] = ()
    excluded_highways: tuple[str, ...]
    included_highways: tuple[str, ...] = ()
    sidewalk_values: tuple[str, ...] = ()
    default_allowed: bool


class NetworkConfig(BaseModel):
    """Validated OSM extraction and tiling parameters."""

    model_config = ConfigDict(extra="forbid")

    states: dict[int, str]
    contour_source_id: str
    kept_tags: tuple[str, ...]
    area_simplify_tolerance_m: float = Field(gt=0)
    unusable_highways: tuple[str, ...]
    access_rules: dict[Mode, AccessRule]
    oneway_yes: tuple[str, ...]
    oneway_no: tuple[str, ...]
    oneway_reverse: tuple[str, ...]
    control_highways: tuple[str, ...]
    signal_highways: tuple[str, ...]
    maxspeed_tokens_kmh: dict[str, float | None]
    mph_to_kmh: float = Field(gt=0)
    busway_values: tuple[str, ...]
    bike_classes: dict[
        Literal[
            "separated_track_path",
            "painted_lane",
            "bus_lane",
            "low_speed",
            "mixed_traffic",
        ],
        tuple[str, ...],
    ]
    tile_size_m: int = Field(gt=0)


def load_network_config(path: str | Path) -> NetworkConfig:
    """Load and validate ``config/network.yaml``."""
    with Path(path).open(encoding="utf-8") as stream:
        return NetworkConfig.model_validate(yaml.safe_load(stream))
