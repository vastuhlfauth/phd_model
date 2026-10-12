"""Validated configuration for the GTFS rebuilding test (section 5.6 / step 0)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

ModeFamily = Literal["bus", "tram", "metro", "rail"]
PatternOutcome = Literal["kept", "dropped", "cut"]


class CalibrationGrid(BaseModel):
    """Candidate parameter values searched in the calibration (section 5.6)."""

    model_config = ConfigDict(extra="forbid")
    r_m: list[int] = Field(min_length=1)
    theta: list[float] = Field(min_length=1)
    k: list[int] = Field(min_length=1)


class ChosenParameters(BaseModel):
    """Parameters retained after calibration; null until confirmed."""

    model_config = ConfigDict(extra="forbid")
    r_m: int | None = None
    k: int | None = None
    theta: dict[ModeFamily, float | None] = Field(default_factory=dict)


class NetworkRef(BaseModel):
    """One configured GTFS resource, resolved to a local path at run time."""

    model_config = ConfigDict(extra="forbid")
    resource_id: int
    notes: str | None = None


class EpciRef(BaseModel):
    """A test EPCI's 2026 SIREN code and optional own GTFS network."""

    model_config = ConfigDict(extra="forbid")
    siren: str = Field(pattern=r"^\d{9}$")
    network: str | None = None
    notes: str | None = None


class KnownCase(BaseModel):
    """One known change of section 5.6's calibration table."""

    model_config = ConfigDict(extra="forbid")
    id: str
    network: str
    route_id: str
    mode_family: ModeFamily
    epci: str | None = None
    opened: date | None = None
    expected_2022: PatternOutcome | None = None
    expected_2024: PatternOutcome | None = None
    notes: str | None = None


class GtfsRebuildConfig(BaseModel):
    """Full configuration for the step 0 GTFS rebuilding test."""

    model_config = ConfigDict(extra="forbid")
    reference_date: date
    osm_lifecycle_prefixes: list[str] = Field(min_length=1)
    osm_source_ids: dict[str, str]
    osm_cache_root: str
    calibration: CalibrationGrid
    chosen: ChosenParameters
    networks: dict[str, NetworkRef]
    test_epcis: dict[str, EpciRef]
    manual_review_networks: list[str] = Field(default_factory=list)
    known_cases: list[KnownCase]


def load_gtfs_rebuild_config(path: str | Path) -> GtfsRebuildConfig:
    """Load and validate ``config/gtfs_rebuild.yaml``."""
    with Path(path).open(encoding="utf-8") as stream:
        return GtfsRebuildConfig.model_validate(yaml.safe_load(stream))
