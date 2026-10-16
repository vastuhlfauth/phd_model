"""Validated public-transport edit catalogue for section 11.4."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from mobgrid.pt.config import GtfsRebuildConfig


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


class OpeningDerivedChange(BaseModel):
    """One route's per-state edit instruction, auto-derived from a PT
    openings CSV row (2026-10-16 fix of the 2026-10-15 national policy).

    Built only from a high- or medium-confidence CSV row whose GTFS match
    is ``exact`` or ``stop-confirmed`` (section 5.6 point 4) -- see
    ``mobgrid.pt.pt_openings.apply_openings_matches``. Rows whose state is
    ``add`` (a line closed before 2026, with no 2026 GTFS counterpart at
    all) never reach this model -- they are excluded by
    ``apply_openings_matches`` itself and reported separately as a known
    gap (section 5.6 point 5).

    ``state_2022``/``state_2024`` alone are **not** an instruction:
    ``keep`` and ``modify`` mean the CSV has nothing to say about that
    state, so the route falls through to the tram automatic rule (for
    tram) or the default-keep policy (for every other family) -- only
    ``remove`` is an instruction, and what it does depends on
    ``change_type`` (``instruction_at``). This matters for real rows:
    Bordeaux trams A/C/E (restructurings, ``modify``/``modify``) must
    never be touched by this model at all; only a true ``new_line``,
    ``reopening`` or ``extension``/``new_station`` row paired with
    ``remove`` ever changes a route.
    """

    model_config = ConfigDict(extra="forbid")
    opening_id: str
    network: str
    route_id: str
    mode: str
    change_type: str
    line_2026: str | None = None
    section_from: str | None = None
    section_to: str | None = None
    match_confidence: Literal["exact", "stop-confirmed"]
    csv_confidence: Literal["high", "medium"]
    state_2022: Literal["keep", "remove", "modify"]
    state_2024: Literal["keep", "remove", "modify"]
    notes: str | None = None

    _STATE_DATES = {date(2022, 1, 1): "state_2022", date(2024, 1, 1): "state_2024"}
    # change_type values that give an instruction when paired with "remove"
    # (section 5.6 point 2); every other change_type (restructuring,
    # renaming, relocation, suspension, closure) gives no instruction here
    # even if its state happens to be "remove" -- see ``unhandled_remove_at``.
    _DROP_CHANGE_TYPES = frozenset(("new_line", "reopening"))
    _CUT_CHANGE_TYPES = frozenset(("extension",))
    _NEW_STATION_CHANGE_TYPES = frozenset(("new_station",))

    def _state_at(self, state_date: date) -> str:
        field_name = self._STATE_DATES.get(state_date)
        if field_name is None:
            raise ValueError(f"no PT openings state defined for {state_date}")
        return getattr(self, field_name)

    def instruction_at(
        self, state_date: date
    ) -> Literal["drop", "cut", "new_station"] | None:
        """The edit instruction active at ``state_date``, or ``None``.

        ``None`` covers both "no instruction" (state is ``keep``/
        ``modify``: fall through to the tram rule or default keep) and
        "state is ``remove`` but ``change_type`` is not recognised" (an
        unhandled case, logged via ``unhandled_remove_at`` rather than
        guessed -- the same conservative policy as an edit whose anchor
        stop cannot be located in the route's pattern).
        """
        if self._state_at(state_date) != "remove":
            return None
        if self.change_type in self._DROP_CHANGE_TYPES:
            return "drop"
        if self.change_type in self._CUT_CHANGE_TYPES:
            return "cut"
        if self.change_type in self._NEW_STATION_CHANGE_TYPES:
            return "new_station"
        return None

    def unhandled_remove_at(self, state_date: date) -> bool:
        """True when the state is ``remove`` but ``change_type`` is unrecognised.

        TODO(confirm): the CSV's ``suspension`` change_type can also pair
        with ``remove`` (a line temporarily out of service, 5 real rows as
        of 2026-10-15) but is deliberately left unhandled here pending a
        decision on whether a suspended line should count as dropped for
        that state; see ``docs/progress.md``.
        """
        return self._state_at(state_date) == "remove" and self.instruction_at(
            state_date
        ) is None

    def removed_at(self, state_date: date) -> bool:
        """Whether the route is wholly absent from the state at ``state_date``.

        Only a ``drop`` instruction (``new_line``/``reopening`` paired
        with ``remove``) removes the whole route; ``cut``/``new_station``
        modify it without removing it, and ``None`` leaves it to the tram
        rule or default keep (2026-10-16 fix: ``modify`` previously
        counted as removed, which would have deleted Bordeaux trams
        A/C/E/F -- restructurings on tracks that already existed --
        nationwide).
        """
        return self.instruction_at(state_date) == "drop"


class PtChangeCatalogue(BaseModel):
    """Confirmed edits plus a reviewed and an unreviewed candidate list.

    ``confirmed`` (manually reviewed) and ``from_openings`` (auto-applied
    from the PT openings CSV's exact/stop-confirmed, high/medium-confidence
    matches -- 2026-10-15 national policy) are the only lists a past-state
    build reads. ``to_review`` and ``not_applied`` are informational only
    (section 5.6 point 6): every other detected candidate route change is
    kept here with its evidence, for the record, but a past-state build
    never reads either list. ``rejected`` holds candidates a reviewer has
    confirmed are *not* real changes (for example a false positive from an
    OSM mapping gap); they are kept with their evidence and notes, and a
    rerun's ``to_review``/``not_applied`` regeneration excludes them so
    they are not re-surfaced every time.
    """

    model_config = ConfigDict(extra="forbid")
    confirmed: list[PtChange] = Field(default_factory=list)
    from_openings: list[OpeningDerivedChange] = Field(default_factory=list)
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
        network_resource_ids: Mapping[str, int],
        mode_split_network_resource_ids: Mapping[str, Mapping[str, int]] | None = None,
    ) -> set[tuple[int, str]]:
        """``(GTFS resource id, route_id)`` pairs wholly absent from a past state.

        ``state_date`` is one of the dated OSM extracts used to build that
        state (``2022-01-01`` for the 2021 state, ``2024-01-01`` for 2023).
        A route is removed only by a manually ``confirmed`` edit or a
        ``from_openings`` entry whose ``instruction_at(state_date)`` is
        ``drop`` (a ``new_line``/``reopening`` row paired with
        ``remove``) -- never by a ``cut``/``new_station`` instruction
        (the route still exists, only part of it does not -- see
        ``mobgrid.pt.route_edits`` for how those are resolved) nor by a
        ``keep``/``modify`` state (no instruction at all: falls through to
        the tram automatic rule or default keep). No family's own
        screening candidates (``to_review``/``not_applied``) ever feed
        into a built state either -- they are informational only (section
        5.6 point 6).

        ``confirmed`` entries name their network by its
        ``config/gtfs_rebuild.yaml`` ``networks:`` slug (for example
        ``tbm_bordeaux``); ``from_openings`` entries name it by the
        openings CSV's own free-text ``network`` column (for example
        ``"TBM (Bordeaux M\u00e9tropole)"``). ``network_resource_ids``
        resolves either string to the one GTFS resource id both describe
        (see ``build_network_resource_ids``), so the key returned here is
        always ``(resource id, route_id)`` -- never a mix of the two
        naming conventions for what may be the same physical network
        (2026-10-16 fix). ``mode_split_network_resource_ids`` additionally
        resolves the one network whose resource id depends on each row's
        own ``mode`` rather than a single value (section 5.6 point 5,
        ``"TER Occitanie (liO)"`` today); only ``from_openings`` entries
        carry a ``mode`` to resolve against, so it is never consulted for
        ``confirmed`` entries.

        Real example (2026-10-16 fix): Bordeaux tram F (route 164) has two
        ``from_openings`` entries -- NAQ-01 (``extension``, ``remove``/
        ``keep``) and NAQ-15 (``restructuring``, ``modify``/``modify``).
        Neither is a ``drop`` instruction (``extension`` gives ``cut``;
        ``restructuring`` is unrecognised, so ``modify`` gives ``None``
        regardless), so route 164 is never in ``removed_route_keys`` at
        either date -- it is a real route 164 is only *cut* at 2022, not
        removed, and both trams A/C/E (also ``restructuring``, also
        ``modify``/``modify``) are untouched at both dates. This replaces
        a 2026-10-15 bug where any non-``keep`` state (including
        ``modify``) counted as removed, which would have deleted these
        four Bordeaux trams -- restructurings on tracks that already
        existed -- nationwide.
        """

        def resolve(network: str, mode: str | None) -> int:
            if (
                mode_split_network_resource_ids is not None
                and network in mode_split_network_resource_ids
            ):
                by_mode = mode_split_network_resource_ids[network]
                if mode in by_mode:
                    return by_mode[mode]
                raise KeyError(
                    f"network {network!r} has a mode-split resource mapping "
                    f"but no entry for mode {mode!r}"
                )
            try:
                return network_resource_ids[network]
            except KeyError:
                raise KeyError(
                    f"no GTFS resource id configured for network {network!r}"
                ) from None

        removed = {
            (resolve(change.network, None), route_id)
            for change in self.changes_after(state_date)
            for route_id in change.route_ids
        }
        removed |= {
            (resolve(change.network, change.mode), change.route_id)
            for change in self.from_openings
            if change.removed_at(state_date)
        }
        return removed


def load_pt_changes(path: str | Path) -> PtChangeCatalogue:
    """Load the section 11-compatible PT change catalogue."""
    with Path(path).open(encoding="utf-8") as stream:
        return PtChangeCatalogue.model_validate(yaml.safe_load(stream))


def build_network_resource_ids(config: GtfsRebuildConfig) -> dict[str, int]:
    """Merge every network name this catalogue uses into one resource-id map.

    ``confirmed`` entries name a network by its ``config/gtfs_rebuild.yaml``
    ``networks:`` slug (for example ``tbm_bordeaux``); ``from_openings``
    entries name it by the openings CSV's own free-text ``network`` column
    (for example ``"TBM (Bordeaux M\u00e9tropole)"``). The two key sets are
    disjoint by construction (one is ``lower_snake_case``, the other free
    text copied from the CSV), so merging them into one dict is safe --
    feed the result to ``PtChangeCatalogue.removed_route_keys`` so it never
    mixes the two conventions (2026-10-16 fix).
    """
    resource_ids = {slug: ref.resource_id for slug, ref in config.networks.items()}
    if config.national_policy is not None:
        resource_ids.update(config.national_policy.openings_list.network_resource_ids)
    return resource_ids


def write_from_openings(
    pt_changes_path: str | Path, applied: tuple[OpeningDerivedChange, ...]
) -> None:
    """Merge auto-applied openings-list changes into ``pt_changes.yaml``.

    Replaces the whole ``from_openings`` list with ``applied``: unlike
    ``to_review``/``not_applied`` (regenerated but keyed by id so manual
    ``rejected`` decisions persist), the openings CSV's state columns
    describe a single ground truth per route, not evidence that
    accumulates across reruns, so a rerun's own proposals simply replace
    the previous ones. ``confirmed``/``to_review``/``not_applied``/
    ``rejected`` are left untouched.
    """
    path = Path(pt_changes_path)
    raw: dict = {}
    if path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw.setdefault("confirmed", [])
    raw.setdefault("to_review", [])
    raw.setdefault("not_applied", [])
    raw.setdefault("rejected", [])
    raw["from_openings"] = [
        change.model_dump(mode="json")
        for change in sorted(applied, key=lambda item: item.opening_id)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=False), encoding="utf-8"
    )
