"""Markdown reporting for the relation-based GTFS rebuild calibration."""

from __future__ import annotations

from pathlib import Path

from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import GridPoint, RelationCalibrationRun, RouteRun


def _recommended(run: RelationCalibrationRun) -> str:
    lines = [
        "| Family | r (m) | k | theta | geometry share | Known correct | "
        "Known F1 | False-change rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for family, point in sorted(run.chosen.items()):
        score = point.score
        lines.append(
            f"| {family} | {point.r_m} | {point.k} | {point.theta:.1f} | "
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


def write_report(
    run: RelationCalibrationRun,
    config: GtfsRebuildConfig,
    path: str | Path,
) -> None:
    """Write all calibration evidence required by section 5.6."""
    text = f"""# Step 0: GTFS rebuilding test (section 5.6)

This implementation replaces the stop-only test with **name matching followed
by geometry matching**, then spatially verifies the matched relation portions.
Results come from each route's most-travelled pattern on
**{config.reference_date}**.

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
