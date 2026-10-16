"""National past-state policy precedence (2026-10-15 decision, step 0).

The goal is a national model built with no manual review step. The
per-family OSM-calibrated automatic rule is retired for every mode family
except tram: metro, rail, bus and ferry (including BHNS/express bus, whose
own automatic cut rule is retired too) keep every 2026 route in both past
states by default, changed only by the PT openings list's auto-applied
matches (see ``mobgrid.pt.pt_openings.apply_openings_matches`` and
``mobgrid.pt.pt_changes.OpeningDerivedChange``). ``to_review``/`not_applied`
candidates are informational only; nothing here ever reads them. See
``docs/progress.md`` and ``config/gtfs_rebuild.yaml``'s ``national_policy``
for the full decision record.
"""

from __future__ import annotations

from typing import Literal

FamilyRule = Literal["automatic_osm", "default_keep_except_openings"]
RoutePresence = Literal["present", "absent"]


def resolve_route_presence(
    *,
    family_rule: FamilyRule,
    opening_removed: bool | None,
    tram_rule_removed: bool | None = None,
) -> RoutePresence:
    """Decide whether a 2026 route exists in one past state.

    Precedence, highest first (section 5.6 point 7):

    1. ``opening_removed`` -- not ``None`` only when a high/medium-
       confidence, exact/stop-confirmed PT-openings-CSV match concerns
       this route at this state date (``OpeningDerivedChange.removed_at``).
       Always wins outright, for every mode family.
    2. ``tram_rule_removed`` -- only consulted when ``family_rule`` is
       ``"automatic_osm"`` (tram today): the confirmed relation-based
       rule's cut/dropped outcome. Never consulted for a family whose
       policy is ``"default_keep_except_openings"``, even if a caller
       happens to pass a value for it.
    3. Otherwise the route is kept by default.
    """
    if opening_removed is not None:
        return "absent" if opening_removed else "present"
    if family_rule == "automatic_osm" and tram_rule_removed is not None:
        return "absent" if tram_rule_removed else "present"
    return "present"
