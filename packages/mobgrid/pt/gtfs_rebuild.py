"""Stop matching, scoring and cutting for the GTFS rebuilding test (section 5.6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import duckdb
import numpy as np
import pyarrow as pa

PatternOutcome = Literal["kept", "dropped", "cut"]


def match_stops(
    connection: duckdb.DuckDBPyConnection,
    gtfs_pattern_stops: pa.Table,
    osm_stops: duckdb.DuckDBPyRelation,
    r_m: float,
) -> pa.Table:
    """Flag each GTFS pattern stop matched by a compatible OSM stop within r_m.

    Section 5.6 point 2: "a stop is matched if an OSM stop of a compatible
    mode lies within a distance r of it"; compatible means the same
    ``mode_family``. ``gtfs_pattern_stops`` and ``osm_stops`` must both
    carry EPSG:3035 ``x``/``y`` columns.
    """
    connection.register("gtfs_pattern_stops", gtfs_pattern_stops)
    connection.register("osm_stops", osm_stops)
    r_squared = r_m * r_m
    result = connection.sql(f"""
        SELECT g.*, EXISTS (
            SELECT 1 FROM osm_stops o
            WHERE o.mode_family = g.mode_family
              AND (o.x - g.x) * (o.x - g.x) + (o.y - g.y) * (o.y - g.y) <= {r_squared}
        ) AS matched
        FROM gtfs_pattern_stops g
    """).to_arrow_table()
    connection.unregister("gtfs_pattern_stops")
    connection.unregister("osm_stops")
    return result


@dataclass(frozen=True)
class PatternMatch:
    """One scored pattern's ordered match flags, before cutting (section 5.6)."""

    pattern_id: str
    route_id: str
    direction_id: str
    mode_family: str
    matched: tuple[bool, ...]


def patterns_from_matches(matched_table: pa.Table) -> list[PatternMatch]:
    """Group a matched-stops table into ordered per-pattern match sequences.

    Assumes rows are already ordered by ``stop_sequence`` within each
    pattern (as produced by ``stop_tables.load_gtfs_patterns``).
    """
    pattern_ids = matched_table.column("pattern_id").to_pylist()
    route_ids = matched_table.column("route_id").to_pylist()
    direction_ids = matched_table.column("direction_id").to_pylist()
    mode_families = matched_table.column("mode_family").to_pylist()
    matched = matched_table.column("matched").to_pylist()
    groups: dict[str, list[bool]] = {}
    meta: dict[str, tuple[str, str, str]] = {}
    for pattern_id, route_id, direction_id, mode_family, flag in zip(
        pattern_ids, route_ids, direction_ids, mode_families, matched, strict=True
    ):
        groups.setdefault(pattern_id, []).append(bool(flag))
        meta[pattern_id] = (route_id, direction_id, mode_family)
    return [
        PatternMatch(pattern_id, *meta[pattern_id], tuple(flags))
        for pattern_id, flags in groups.items()
    ]


@dataclass(frozen=True)
class PatternResult:
    """Score, cut and outcome of one pattern (section 5.6 points 3-5)."""

    pattern_id: str
    route_id: str
    direction_id: str
    mode_family: str
    n: int
    m: int
    s: float
    outcome: PatternOutcome
    start_index: int
    end_index: int
    flagged_interior: bool


def rebuild_pattern(match: PatternMatch, theta: float, k: int) -> PatternResult:
    """Score, drop or cut one pattern (section 5.6 points 3 to 5).

    A pattern is dropped entirely when its matched share ``s = m / n`` is
    below ``theta``. Otherwise, a run of at least ``k`` consecutive
    unmatched stops at either end is trimmed (the pattern ends at the last
    matched stop); isolated interior gaps are kept, and an interior run of
    at least ``k`` unmatched stops is kept but flagged for manual review.
    """
    flags = np.asarray(match.matched, dtype=bool)
    n = len(flags)
    m = int(flags.sum())
    s = m / n if n else 0.0
    if n == 0 or s < theta:
        return PatternResult(
            match.pattern_id,
            match.route_id,
            match.direction_id,
            match.mode_family,
            n,
            m,
            s,
            "dropped",
            0,
            max(n - 1, 0),
            False,
        )
    leading = 0
    while leading < n and not flags[leading]:
        leading += 1
    trailing = 0
    while trailing < n and not flags[n - 1 - trailing]:
        trailing += 1
    start = leading if leading >= k else 0
    end = (n - 1 - trailing) if trailing >= k else n - 1
    if start > end:
        return PatternResult(
            match.pattern_id,
            match.route_id,
            match.direction_id,
            match.mode_family,
            n,
            m,
            s,
            "dropped",
            0,
            n - 1,
            False,
        )
    flagged = False
    run = 0
    for index in range(start, end + 1):
        if flags[index]:
            run = 0
        else:
            run += 1
            if run >= k:
                flagged = True
    outcome: PatternOutcome = "kept" if start == 0 and end == n - 1 else "cut"
    return PatternResult(
        match.pattern_id,
        match.route_id,
        match.direction_id,
        match.mode_family,
        n,
        m,
        s,
        outcome,
        start,
        end,
        flagged,
    )


def rebuild_patterns(
    matches: list[PatternMatch], theta_by_family: dict[str, float], k: int
) -> list[PatternResult]:
    """Apply ``rebuild_pattern`` to every pattern, using its mode family's theta."""
    return [
        rebuild_pattern(match, theta_by_family[match.mode_family], k)
        for match in matches
    ]


def route_outcome(results: list[PatternResult]) -> PatternOutcome:
    """Worst-case outcome across a route's patterns (dropped > cut > kept)."""
    outcomes = {result.outcome for result in results}
    if "dropped" in outcomes:
        return "dropped"
    if "cut" in outcomes:
        return "cut"
    return "kept"

