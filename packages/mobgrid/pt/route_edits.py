"""Resolve PT-openings ``cut``/``new_station`` edits against a route pattern.

Section 5.6 point 2 (2026-10-16 fix): what a ``remove``-state openings row
does depends on its ``change_type``. ``new_line``/``reopening`` drop a
route outright (handled by ``PtChangeCatalogue.removed_route_keys``, never
reaching this module). ``extension`` cuts a route at its old terminus
(``section_from``), keeping the stops up to it and dropping the stops
toward the new terminus (``section_to``); trips keep their 2026 times on
the remaining section. ``new_station`` removes only the one new stop named
in ``section_from``. Several such rows on the same route combine (point
3): this module narrows a kept index range and a set of excluded single
stops across every edit active for one ``(network, route_id)`` at one
state date, rather than resolving each row in isolation.

An edit whose anchor stop(s) cannot be located in the route's main pattern
is skipped and logged (``EditOutcome.unresolved_opening_ids``) -- "log it
and keep the route whole" applies *per edit*, not to the combined result:
other, resolvable edits on the same route still apply (point 2's last
bullet; see ``resolve_route_edits``'s docstring for the metro 14 case,
where a north and a south extension cut both ends independently).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from mobgrid.pt.pt_changes import PtChangeCatalogue
from mobgrid.pt.pt_text import normalise_text


@dataclass(frozen=True)
class RouteEditSpec:
    """One active ``cut``/``new_station`` edit for one route at one state."""

    opening_id: str
    kind: str  # "cut" | "new_station"
    anchor_from: str
    anchor_to: str | None = None


@dataclass(frozen=True)
class EditOutcome:
    """Result of applying a route's combined edits to its main pattern."""

    original_stop_count: int
    kept_stop_count: int
    applied_opening_ids: tuple[str, ...]
    unresolved_opening_ids: tuple[str, ...]


def collect_edit_specs(
    catalogue: PtChangeCatalogue, state_date: date
) -> dict[tuple[str, str], list[RouteEditSpec]]:
    """Active ``cut``/``new_station`` edits per ``(network, route_id)``.

    Only entries whose ``instruction_at(state_date)`` is ``cut`` or
    ``new_station`` are collected: a ``drop`` instruction removes the
    whole route (``removed_route_keys``, not here), and ``None`` (no
    instruction -- ``keep``/``modify`` state, or an unrecognised
    ``change_type`` paired with ``remove``) contributes nothing.
    """
    collected: dict[tuple[str, str], list[RouteEditSpec]] = {}
    for change in catalogue.from_openings:
        instruction = change.instruction_at(state_date)
        if instruction not in ("cut", "new_station"):
            continue
        key = (change.network, change.route_id)
        collected.setdefault(key, []).append(
            RouteEditSpec(
                change.opening_id,
                instruction,
                change.section_from or "",
                change.section_to,
            )
        )
    return collected


def _find_stop_index(stop_names: Sequence[str], query: str) -> int | None:
    """First index whose normalised name contains, or is contained by, ``query``.

    Bidirectional containment handles both real-world directions seen in
    the openings CSV: a CSV place name with extra context the GTFS stop
    name lacks (``"Carrefour des Quatre Chemins (Mérignac)"`` vs the real
    stop ``"Quatre Chemins"``), and the reverse.
    """
    needle = normalise_text(query)
    if not needle:
        return None
    for index, name in enumerate(stop_names):
        haystack = normalise_text(name)
        if haystack and (needle in haystack or haystack in needle):
            return index
    return None


def resolve_route_edits(
    stop_names: Sequence[str], edits: Sequence[RouteEditSpec]
) -> EditOutcome:
    """Apply a route's combined ``cut``/``new_station`` edits to its pattern.

    A ``cut`` narrows the kept index range ``[lo, hi]`` toward
    ``anchor_from`` (the old terminus), away from ``anchor_to`` (located on
    the other side); several cuts combine by narrowing the same range
    further. The real motivating case is metro 14: a north extension
    (cut toward the north end) and a south extension (cut toward the south
    end) are independent edits that together trim *both* ends of one
    route, never dropping it. A ``new_station`` edit excludes a single
    index from the retained range. An edit whose anchor(s) cannot be
    located is skipped (recorded in ``unresolved_opening_ids``) and never
    narrows or excludes anything; the other edits still apply.
    """
    lo, hi = 0, len(stop_names) - 1
    excluded: set[int] = set()
    applied: list[str] = []
    unresolved: list[str] = []
    for edit in edits:
        idx_from = _find_stop_index(stop_names, edit.anchor_from)
        if edit.kind == "new_station":
            if idx_from is None:
                unresolved.append(edit.opening_id)
                continue
            excluded.add(idx_from)
            applied.append(edit.opening_id)
            continue
        idx_to = (
            _find_stop_index(stop_names, edit.anchor_to) if edit.anchor_to else None
        )
        if idx_from is None or idx_to is None:
            unresolved.append(edit.opening_id)
            continue
        if idx_to > idx_from:
            hi = min(hi, idx_from)
        else:
            lo = max(lo, idx_from)
        applied.append(edit.opening_id)
    kept = (
        sum(1 for index in range(lo, hi + 1) if index not in excluded)
        if hi >= lo
        else 0
    )
    return EditOutcome(len(stop_names), kept, tuple(applied), tuple(unresolved))
