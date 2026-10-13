"""Validated public-transport edit catalogue for section 11.4."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PtChange(BaseModel):
    """One confirmed or candidate source-network PT edit."""

    model_config = ConfigDict(extra="forbid")
    id: str
    type: Literal["pt_new_line", "pt_extend"]
    network: str
    route_ids: list[str] = Field(min_length=1)
    opened: date | None = None
    description: str


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


class PtChangeCatalogue(BaseModel):
    """Confirmed edits and review-only candidates."""

    model_config = ConfigDict(extra="forbid")
    confirmed: list[PtChange] = Field(default_factory=list)
    candidates: list[PtChangeCandidate] = Field(default_factory=list)

    def changes_after(self, state_date: date) -> list[PtChange]:
        """Confirmed edits to subtract from a state predating their opening."""
        return [
            change
            for change in self.confirmed
            if change.opened is not None and change.opened > state_date
        ]


def load_pt_changes(path: str | Path) -> PtChangeCatalogue:
    """Load the section 11-compatible PT change catalogue."""
    with Path(path).open(encoding="utf-8") as stream:
        return PtChangeCatalogue.model_validate(yaml.safe_load(stream))
