"""Markdown reporting for the relation-based GTFS rebuild calibration."""

from __future__ import annotations

from pathlib import Path

import yaml

from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import (
    GridPoint,
    RelationCalibrationRun,
    RouteRun,
    network_relation_coverage,
)

_INERT_OUTCOME_FAMILIES = frozenset(("bus", "ferry"))


def _recommended(run: RelationCalibrationRun) -> str:
    lines = [
        "| Family | r (m) | k | theta | geometry share | Known correct | "
        "Known F1 | False-change rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for family, point in sorted(run.chosen.items()):
        score = point.score
        # Bus/ferry no longer cut or use theta to decide their outcome
        # (2026-10-15 decision): both are shown as not applicable rather
        # than the grid's arbitrary tie-break value.
        inert = family in _INERT_OUTCOME_FAMILIES
        k_cell = "n/a" if inert else str(point.k)
        theta_cell = "n/a" if inert else f"{point.theta:.1f}"
        lines.append(
            f"| {family} | {point.r_m} | {k_cell} | {theta_cell} | "
            f"{point.geometry_share:.1f} | {score.known_correct}/"
            f"{score.known_total} | {score.f1:.2f} | "
            f"{score.false_change_rate:.2%} |"
        )
    return "\n".join(lines)


def _score_table(grid: list[GridPoint]) -> str:
    lines = [
        "| Family | r | k | theta | geometry share | Known n | Known exact | "
        "Precision | Recall | F1 | Presumed unchanged n | False-change rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for point in sorted(
        grid,
        key=lambda item: (
            item.mode_family,
            item.r_m,
            item.k,
            item.theta,
            item.geometry_share,
        ),
    ):
        score = point.score
        exact = score.known_correct / score.known_total if score.known_total else 0
        lines.append(
            f"| {point.mode_family} | {point.r_m} | {point.k} | "
            f"{point.theta:.1f} | {point.geometry_share:.1f} | "
            f"{score.known_total} | {exact:.2f} | {score.precision:.2f} | "
            f"{score.recall:.2f} | {score.f1:.2f} | "
            f"{score.presumed_unchanged_total} | "
            f"{score.false_change_rate:.2%} |"
        )
    return "\n".join(lines)


def _known_cases(config: GtfsRebuildConfig, run: RelationCalibrationRun) -> str:
    lines = [
        "| Case | Route | Family | 2022 expected / obtained | "
        "2024 expected / obtained | Pass and relations |",
        "|---|---|---|---|---|---|",
    ]
    for case in config.known_cases:
        cells = []
        evidence = []
        for date_key, expected in (
            ("2022-01-01", case.expected_2022),
            ("2024-01-01", case.expected_2024),
        ):
            route = next(
                (
                    item
                    for item in run.final_routes
                    if item.network == case.network
                    and item.date_key == date_key
                    and case.route_id
                    in {item.pattern.route_id, item.pattern.short_name}
                ),
                None,
            )
            cells.append(
                f"{expected or 'review'} / "
                f"{route.result.outcome if route else 'n/a'}"
            )
            if route:
                evidence.append(
                    f"{date_key[:4]}: {route.result.match_pass or 'none'} "
                    f"{', '.join(route.result.relation_refs) or '-'} "
                    f"({route.result.covered_share:.0%})"
                )
        lines.append(
            f"| {case.id} | {case.route_id} | {case.mode_family} | "
            f"{cells[0]} | {cells[1]} | {'; '.join(evidence)} |"
        )
    return "\n".join(lines)


def _changed_routes(routes: list[RouteRun]) -> str:
    selected = [
        route
        for route in routes
        if route.result.outcome
        in ("dropped", "cut", "kept-renamed", "not-testable")
    ]
    if not selected:
        return "_No routes in a review outcome._"
    lines = [
        "| Network | Route | Date | Family | Outcome | Pass | Relation ids / refs | "
        "Covered share |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for route in sorted(
        selected,
        key=lambda item: (item.network, item.pattern.route_id, item.date_key),
    ):
        result = route.result
        relations = ", ".join(
            f"{relation_id}:{ref}"
            for relation_id, ref in zip(
                result.relation_ids,
                (*result.relation_refs, *("" for _ in result.relation_ids)),
            )
        )
        lines.append(
            f"| {route.network} | {route.pattern.route_id} | {route.date_key} | "
            f"{route.pattern.mode} | {result.outcome} | "
            f"{result.match_pass or '-'} | {relations or '-'} | "
            f"{result.covered_share:.0%} |"
        )
    return "\n".join(lines)


def _epci_sections(
    run: RelationCalibrationRun, config: GtfsRebuildConfig
) -> str:
    sections = []
    for epci in config.test_epcis:
        route_keys = run.epci_routes.get(epci, set())
        routes = [
            route
            for route in run.final_routes
            if (route.network, route.pattern.route_id) in route_keys
        ]
        sections.append(f"### {epci}\n\n{_changed_routes(routes)}")
    return "\n\n".join(sections)


def _flagged_networks(run: RelationCalibrationRun) -> str:
    if not run.flagged_networks:
        return "_None._"
    return "\n".join(
        f"- {date_key}: `{network}`"
        for date_key, network in sorted(run.flagged_networks)
    )


def _rail_review(run: RelationCalibrationRun) -> str:
    rail = [
        route
        for route in run.final_routes
        if route.pattern.mode == "rail"
        and route.result.outcome
        in ("dropped", "cut", "kept-renamed", "not-testable")
    ]
    checks = "\n".join(
        f"- SNCF route `{route_id}`: classified `{mode}`"
        for route_id, mode in sorted(run.rail_route_modes.items())
    ) or "- Requested SNCF route ids were not present in the selected feed."
    return f"{checks}\n\n{_changed_routes(rail)}"


def _bus_coverage_table(run: RelationCalibrationRun) -> str:
    coverage = network_relation_coverage(run)
    if not coverage:
        return "_No bus/ferry route evaluated._"
    lines = [
        "| Network | Date | Matched routes | Total routes | Coverage |",
        "|---|---|---:|---:|---:|",
    ]
    counts: dict[tuple[str, str], list[int]] = {}
    for route in run.final_routes:
        if route.pattern.mode not in ("bus", "ferry"):
            continue
        key = (route.network, route.date_key)
        matched, total = counts.setdefault(key, [0, 0])
        total += 1
        if route.match.relation_ids:
            matched += 1
        counts[key] = [matched, total]
    for (network, date_key), (matched, total) in sorted(counts.items()):
        share = matched / total if total else 0.0
        lines.append(
            f"| {network} | {date_key} | {matched} | {total} | {share:.0%} |"
        )
    return "\n".join(lines)


def _bhns_classification(run: RelationCalibrationRun) -> str:
    seen: dict[tuple[str, str], RouteRun] = {}
    for route in run.final_routes:
        if route.pattern.mode == "bus" and route.pattern.is_bhns:
            key = (route.network, route.pattern.route_id)
            if key not in seen or (
                route.result.covered_share > seen[key].result.covered_share
            ):
                seen[key] = route
    if not seen:
        return "_No route matched the BHNS/express keywords._"
    lines = [
        "| Network | Route | Short name | Long name | Share of stops on bus "
        "infrastructure |",
        "|---|---|---|---|---:|",
    ]
    for (network, route_id), route in sorted(seen.items()):
        lines.append(
            f"| {network} | {route_id} | {route.pattern.short_name or '-'} | "
            f"{route.pattern.long_name or '-'} | "
            f"{route.result.covered_share:.0%} |"
        )
    return "\n".join(lines)


def _candidate_review_section(pt_changes_path: str | Path) -> str:
    path = Path(pt_changes_path)
    if not path.is_file():
        return "_No calibration has written `config/pt_changes.yaml` yet._"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    to_review = raw.get("to_review", [])
    not_applied = raw.get("not_applied", [])
    lines = [f"Full evidence for every candidate is in `{path}`.", ""]
    lines.append(
        f"### To review ({len(to_review)} candidates: every BHNS/express "
        "bus/ferry route, plus every bus/ferry route dropped under the "
        "fixed name/geometry-share rule, with no cap; rail keeps its own "
        "90%-coverage gate and top-30-by-trips cap, ranked by trips)"
    )
    if to_review:
        lines.append(
            "\n| Network | Route | BHNS | Trips | Pass | Outcomes by date | "
            "Covered share |"
        )
        lines.append("|---|---|---|---:|---|---|---:|")
        for candidate in to_review:
            outcomes = ", ".join(
                f"{date}: {outcome}"
                for date, outcome in candidate["outcomes_by_date"].items()
            )
            lines.append(
                f"| {candidate['network']} | {candidate['route_id']} | "
                f"{'yes' if candidate.get('is_bhns') else 'no'} | "
                f"{candidate.get('trip_count', 0)} | "
                f"{candidate['match_pass'] or '-'} | {outcomes} | "
                f"{candidate['covered_share']:.0%} |"
            )
    else:
        lines.append("\n_None eligible._")
    lines.append(
        f"\n### Not applied ({len(not_applied)} candidates kept as evidence, "
        "never auto-applied)"
    )
    by_network: dict[str, int] = {}
    for candidate in not_applied:
        by_network[candidate["network"]] = by_network.get(candidate["network"], 0) + 1
    if by_network:
        lines.append("")
        lines.extend(
            f"- `{network}`: {count}" for network, count in sorted(by_network.items())
        )
    else:
        lines.append("\n_None._")
    return "\n".join(lines)


def write_report(
    run: RelationCalibrationRun,
    config: GtfsRebuildConfig,
    path: str | Path,
    *,
    pt_changes_path: str | Path = "config/pt_changes.yaml",
) -> None:
    """Write all calibration evidence required by section 5.6."""
    text = f"""# Step 0: GTFS rebuilding test (section 5.6)

This implementation replaces the stop-only test with **name matching followed
by geometry matching**, then spatially verifies the matched relation portions.
Results come from each route's most-travelled pattern on
**{config.reference_date}**.

## Bus and ferry policy (2026-10-15 decision)

Every 2026 bus and ferry route is kept in both past states by default; only
`confirmed` entries of `config/pt_changes.yaml` are ever applied. BHNS/express
routes are the one exception: they are identified by name or description
(`Express`, `BHNS`, `Liane(s)`, `Chronobus`) and verified like a tram, cut at
uncovered ends before `theta`, using dedicated bus infrastructure in OSM
(`highway=busway`/`bus_guideway`, `busway=*`, `lanes:bus=*`, not under
construction or proposed) instead of the regular kept/dropped rule. Every
other bus/ferry route uses a fixed, non-calibrated outcome rule instead of
`theta`: a name match covering at least 50% of stops is `kept`; a name match
below 30% is treated as a homonym (a coincidental ref/name match, not the
same line) and discarded in favour of the geometry pass; a geometry match
reaching 50% is `kept-renamed`; otherwise the route is `dropped`. Ferry
coverage is checked against a relation's member stops and piers only, never
its ways, within a fixed 200 m regardless of the calibrated `r_m`. All other
detected bus/ferry changes are candidates for manual review only (see below).

## Recommended parameters

The ranking maximises exact known-case outcomes, then known-case F1, then
minimises the false-change rate among presumed-unchanged routes. Rail reuses
metro parameters because section 5.6 has no labelled rail case; ferry reuses
bus parameters and is never cut.

{_recommended(run)}

Values are written to `config/gtfs_rebuild.yaml` as `TODO(confirm)`.

## Known cases: expected versus obtained

{_known_cases(config, run)}

## Complete calibration score table

Known-case precision, recall and F1 exclude `not-testable` routes. The
false-change rate is the share of other test-area routes presumed unchanged
that were incorrectly cut or dropped; `kept-renamed` is not a false change.

{_score_table(run.grid)}

## Bus and ferry OSM relation coverage, by network and date

Share of each network's main patterns that found any OSM relation by name or
geometry. Recorded for every candidate as context; it no longer gates
bus/ferry review eligibility (2026-10-15 decision -- see the policy above),
but rail's own review list still requires at least 90%.

{_bus_coverage_table(run)}

## BHNS/express bus classification

{_bhns_classification(run)}

## Candidate route changes for manual review

{_candidate_review_section(pt_changes_path)}

## Routes requiring review, by test EPCI

{_epci_sections(run, config)}

## Networks below 50% OSM relation coverage

Every route in these network/date combinations is retained as `not-testable`.

{_flagged_networks(run)}

## Rail manual review

Stops outside the configured OSM coverage are excluded from n. Routes 7601
and 951-953 must remain buses when their GTFS `route_type` is 3.

{_rail_review(run)}
"""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
