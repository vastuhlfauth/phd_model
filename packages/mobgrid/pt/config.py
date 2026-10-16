"""Validated configuration for the GTFS rebuilding test (section 5.6 / step 0)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

ModeFamily = Literal["bus", "tram", "metro", "rail", "ferry"]
PatternOutcome = Literal[
    "kept", "kept-renamed", "dropped", "cut", "not-testable"
]


class CalibrationGrid(BaseModel):
    """Candidate parameter values searched in the calibration (section 5.6)."""

    model_config = ConfigDict(extra="forbid")
    r_m: list[int] = Field(min_length=1)
    theta: list[float] = Field(min_length=1)
    k: list[int] = Field(min_length=1)
    geometry_share: list[float] = Field(min_length=1)


class ChosenFamilyParameters(BaseModel):
    """Parameters retained for one mode family; null until confirmed."""

    model_config = ConfigDict(extra="forbid")
    r_m: int | None = None
    k: int | None = None
    geometry_share: float | None = None
    theta: float | None = None


FamilyPolicyRule = Literal["automatic_osm", "default_keep_except_openings"]
OpeningRowConfidence = Literal["high", "medium", "low"]
OpeningMatchConfidence = Literal["exact", "stop-confirmed", "ambiguous", "none"]
PolicySource = Literal["openings_list", "tram_automatic_rule", "default_keep"]


class FamilyPolicy(BaseModel):
    """One mode family's national past-state policy (2026-10-15 decision)."""

    model_config = ConfigDict(extra="forbid")
    rule: FamilyPolicyRule
    notes: str | None = None


class OpeningsListPolicy(BaseModel):
    """How the PT openings CSV feeds automatic past-state changes.

    ``network_resource_ids`` maps a CSV ``network`` column string to the
    one GTFS resource id that covers it, resolved against
    ``config/gtfs_inventory.csv`` (dataset title, AOM/EPCI, agency names)
    -- used by ``mobgrid.pt map-and-apply-all`` to map every configured
    network in one batch run. ``mode_split_network_resource_ids`` covers
    the one network needing a per-row resolution instead of a single
    resource: ``"TER Occitanie (liO)"`` resolves by each row's own
    ``mode`` (rail rows against SNCF's resource; bus/coach rows against
    liO's own resource -- section 5.6 point 5), since its rows describe
    both TER rail services and liO interurban coach lines sharing one
    brand. ``unresolved_networks`` lists a CSV network string with no
    resource id found at all, each with the reason, rather than guessing
    one (section 5.6 point 5 -- "If one cannot be resolved, log it as a
    gap").
    """

    model_config = ConfigDict(extra="forbid")
    source_csv: str
    mapping_csv: str
    include_row_confidence: list[OpeningRowConfidence] = Field(min_length=1)
    apply_match_confidence: list[OpeningMatchConfidence] = Field(min_length=1)
    known_gap_state: Literal["add"] = "add"
    network_resource_ids: dict[str, int] = Field(default_factory=dict)
    mode_split_network_resource_ids: dict[str, dict[str, int]] = Field(
        default_factory=dict
    )
    unresolved_networks: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class NationalPolicy(BaseModel):
    """The national no-manual-review past-state policy (2026-10-15 decision).

    Replaces the per-family calibrated-threshold approach for every family
    except tram: metro, rail, bus and ferry (including BHNS/express bus,
    which no longer has its own automatic cut rule either) keep every 2026
    route in both past states by default, changed only by a high- or
    medium-confidence, exact- or stop-confirmed-matched row of the PT
    openings CSV (``openings_list``). ``precedence`` lists, highest first,
    the sources consulted to decide one route's presence in one state: the
    openings list always wins; the automatic OSM rule (tram only, today)
    is consulted next when no openings-list match applies; otherwise the
    route is kept by default. ``to_review_is_informational`` records that
    no family's own screening candidates ever gate or feed this decision
    (section 5.6 point 6) -- see ``mobgrid.pt.pt_policy.resolve_route_presence``.
    """

    model_config = ConfigDict(extra="forbid")
    decision_date: date
    precedence: list[PolicySource] = Field(min_length=1)
    families: dict[ModeFamily, FamilyPolicy]
    openings_list: OpeningsListPolicy
    to_review_is_informational: bool = True
    notes: str | None = None


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
    osm_route_cache_root: str
    calibration: CalibrationGrid
    chosen: dict[ModeFamily, ChosenFamilyParameters]
    national_policy: NationalPolicy | None = None
    networks: dict[str, NetworkRef]
    test_epcis: dict[str, EpciRef]
    manual_review_networks: list[str] = Field(default_factory=list)
    known_cases: list[KnownCase]


def load_gtfs_rebuild_config(path: str | Path) -> GtfsRebuildConfig:
    """Load and validate ``config/gtfs_rebuild.yaml``."""
    with Path(path).open(encoding="utf-8") as stream:
        return GtfsRebuildConfig.model_validate(yaml.safe_load(stream))
