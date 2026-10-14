"""Validated public-transport edit catalogue for section 11.4."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PtChange(BaseModel):
    """One confirmed or candidate source-network PT edit.

    ``type`` distinguishes a brand-new line (``pt_new_line``, fully absent
    before ``opened``) from an extension of an existing line
    (``pt_extend``, where only the extended portion is absent before
    ``opened`` -- the historical network-edit application, not yet
    implemented, is expected to trim rather than remove such routes).
    """

    model_config = ConfigDict(extra="forbid")
    id: str
    type: Literal["pt_new_line", "pt_extend"]
    network: str
    route_ids: list[str] = Field(min_length=1)
    opened: date | None = None
    description: str
    notes: str | None = None


class PtChangeCandidate(BaseModel):
    """A detected route outcome awaiting confirmation or rejection."""

    model_config = ConfigDict(extra="forbid")
    id: str
    network: str
    route_id: str
    outcomes_by_date: dict[str, Literal["dropped", "kept-renamed"]]
    match_pass: Literal["name", "geometry"] | None
    relation_ids: list[int] = Field(default_factory=list)
    relation_refs: list[str] = Field(default_factory=list)
    covered_share: float = Field(ge=0, le=1)
    trip_count: int = 0
    is_bhns: bool = False
    network_coverage_by_date: dict[str, float] = Field(default_factory=dict)
    notes: str | None = None


class PtChangeCatalogue(BaseModel):
    """Confirmed edits plus a reviewed and an unreviewed candidate list.

    Bus and ferry routes are never auto-applied: ``confirmed`` is the only
    list a past-state build reads by default. ``to_review`` is the top-50,
    high-confidence subset of detected changes (section 5.6 point 3);
    ``not_applied`` keeps every other candidate with its evidence, for the
    record, without ever feeding automatically into a state. ``rejected``
    holds candidates a reviewer has confirmed are *not* real changes (for
    example a false positive from an OSM mapping gap); they are kept with
    their evidence and notes, and a rerun's ``to_review``/``not_applied``
    regeneration excludes them so they are not re-surfaced every time.
    """

    model_config = ConfigDict(extra="forbid")
    confirmed: list[PtChange] = Field(default_factory=list)
    to_review: list[PtChangeCandidate] = Field(default_factory=list)
    not_applied: list[PtChangeCandidate] = Field(default_factory=list)
    rejected: list[PtChangeCandidate] = Field(default_factory=list)

    def changes_after(self, state_date: date) -> list[PtChange]:
        """Confirmed edits to subtract from a state predating their opening."""
        return [
            change
            for change in self.confirmed
            if change.opened is not None and change.opened > state_date
        ]

    def removed_route_keys(
        self,
        state_date: date,
        *,
        sensitivity: Literal[
            "confirmed", "confirmed_and_candidates"
        ] = "confirmed",
    ) -> set[tuple[str, str]]:
        """``(network, route_id)`` pairs absent from a past state.

        ``state_date`` is one of the dated OSM extracts used to build that
        state (``2022-01-01`` for the 2021 state, ``2024-01-01`` for 2023).
        ``sensitivity="confirmed"`` (default) only removes confirmed edits.
        ``sensitivity="confirmed_and_candidates"`` additionally removes every
        candidate route whose outcome on that date is ``dropped`` (from
        ``to_review`` and ``not_applied`` alike), for sensitivity testing of
        how much the uncertain bus/ferry candidates would change a state;
        ``kept-renamed`` candidates are not removed, since they describe a
        route kept on a different alignment, not an absent route.
        """
        removed = {
            (change.network, route_id)
            for change in self.changes_after(state_date)
            for route_id in change.route_ids
        }
        if sensitivity == "confirmed_and_candidates":
            date_key = state_date.isoformat()
            removed |= {
                (candidate.network, candidate.route_id)
                for candidate in (*self.to_review, *self.not_applied)
                if candidate.outcomes_by_date.get(date_key) == "dropped"
            }
        return removed


def load_pt_changes(path: str | Path) -> PtChangeCatalogue:
    """Load the section 11-compatible PT change catalogue."""
    with Path(path).open(encoding="utf-8") as stream:
        return PtChangeCatalogue.model_validate(yaml.safe_load(stream))
