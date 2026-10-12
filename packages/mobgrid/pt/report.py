"""Markdown report for the step 0 GTFS rebuilding calibration (section 5.6)."""

from __future__ import annotations

from pathlib import Path

from mobgrid.pt.calibrate import CalibrationRun, PatternEvaluation
from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.gtfs_rebuild import route_outcome


def _route_evaluations(
    evaluations: list[PatternEvaluation], network: str, route_id: str, date_key: str
) -> list[PatternEvaluation]:
    return [
        item
        for item in evaluations
        if item.network == network
        and item.route_id == route_id
        and item.date_key == date_key
    ]


def _known_cases_table(config: GtfsRebuildConfig, run: CalibrationRun) -> str:
    lines = [
        "| Case | Network | Route | Family | Opened | Expected 1 Jan 2022 | "
        "Obtained 2022 | Expected 1 Jan 2024 | Obtained 2024 | Match |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for case in config.known_cases:
        row_2022 = _route_evaluations(
            run.final_evaluations, case.network, case.route_id, "2022-01-01"
        )
        row_2024 = _route_evaluations(
            run.final_evaluations, case.network, case.route_id, "2024-01-01"
        )
        obtained_2022 = (
            route_outcome([item.result for item in row_2022]) if row_2022 else "n/a"
        )
        obtained_2024 = (
            route_outcome([item.result for item in row_2024]) if row_2024 else "n/a"
        )
        expected_2022 = case.expected_2022 or "(not scored)"
        expected_2024 = case.expected_2024 or "(not scored)"
        if case.expected_2022 is None and case.expected_2024 is None:
            match = "manual review"
        else:
            match = (
                "yes"
                if obtained_2022 == case.expected_2022
                and obtained_2024 == case.expected_2024
                else "NO"
            )
        lines.append(
            f"| {case.id} | {case.network} | {case.route_id} | {case.mode_family} | "
            f"{case.opened or '?'} | {expected_2022} | {obtained_2022} | "
            f"{expected_2024} | {obtained_2024} | {match} |"
        )
    return "\n".join(lines)


def _bus_family_note(run: CalibrationRun) -> str:
    """Flag the bus family's weak calibration fit, for manual judgement."""
    best_bus = max(
        (c for c in run.grid_result.grid if c.mode_family == "bus"),
        key=lambda c: (c.f1, c.accuracy),
    )
    if best_bus.f1 >= 0.3:
        return ""
    return f"""
> **Known limitation, bus family.** Even at its best grid point
> (r={best_bus.r_m:g} m, k={best_bus.k}, theta={best_bus.theta:g}), bus
> precision/recall/F1 are {best_bus.precision:.2f}/{best_bus.recall:.2f}/
> {best_bus.f1:.2f} over {best_bus.total} route-level cases: about half of
> all bus routes (almost all expected "kept") score below any reasonable
> theta. Section 5.6 names the likely cause directly: bus-stop mapping in
> OpenStreetMap is the least complete of the four families, and the dated
> 2022/2024 extracts appear to have materially sparser bus-stop coverage
> than needed, unrelated to real network changes. The recommended
> theta (bus) below is the grid optimum, but it is not a reliable
> threshold; please review before confirming it, for example by
> re-checking a sample of the "dropped" routes below by hand, before using
> this family's result for scenario triage.
"""



def _score_table(run: CalibrationRun) -> str:
    lines = [
        "| Family | r (m) | k | theta | n cases | accuracy | precision | recall | F1 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    ordered = sorted(
        run.grid_result.grid, key=lambda c: (c.mode_family, c.r_m, c.k, c.theta)
    )
    for counts in ordered:
        lines.append(
            f"| {counts.mode_family} | {counts.r_m:g} | {counts.k} | "
            f"{counts.theta:g} | {counts.total} | {counts.accuracy:.2f} | "
            f"{counts.precision:.2f} | {counts.recall:.2f} | {counts.f1:.2f} |"
        )
    return "\n".join(lines)


def _epci_line_list(
    run: CalibrationRun, config: GtfsRebuildConfig, epci_key: str, mode_family: str
) -> str:
    epci = config.test_epcis[epci_key]
    network = epci.network
    if network is None:
        return "_No network of its own (section 5.6)._"
    rows = [
        item
        for item in run.final_evaluations
        if item.network == network
        and item.mode_family == mode_family
        and item.result.outcome in ("dropped", "cut")
    ]
    if not rows:
        return "_No lines dropped or cut at either date._"
    lines = [
        "| Route | Pattern | Date | n | m | s | Outcome | Flagged interior |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in sorted(rows, key=lambda r: (r.route_id, r.date_key, r.pattern_id)):
        lines.append(
            f"| {item.route_id} | {item.pattern_id} | {item.date_key} | "
            f"{item.result.n} | {item.result.m} | {item.result.s:.2f} | "
            f"{item.result.outcome} | {item.result.flagged_interior} |"
        )
    return "\n".join(lines)


def _rail_manual_review(run: CalibrationRun) -> str:
    rows = [
        item
        for item in run.final_evaluations
        if item.mode_family == "rail" and item.result.outcome in ("dropped", "cut")
    ]
    if not rows:
        return "_No SNCF rail lines dropped or cut at either date (metro thresholds)._"
    lines = [
        "| Route | Pattern | Date | n | m | s | Outcome | Flagged interior |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in sorted(rows, key=lambda r: (r.route_id, r.date_key, r.pattern_id)):
        lines.append(
            f"| {item.route_id} | {item.pattern_id} | {item.date_key} | "
            f"{item.result.n} | {item.result.m} | {item.result.s:.2f} | "
            f"{item.result.outcome} | {item.result.flagged_interior} |"
        )
    return "\n".join(lines)


def _coverage_section(run: CalibrationRun, config: GtfsRebuildConfig) -> str:
    header_networks = sorted({
        network for counts in run.rural_epci_coverage.values() for network in counts
    })
    lines = [
        "| Test EPCI | " + " | ".join(header_networks) + " |",
        "|---|" + "---|" * len(header_networks),
    ]
    for epci_key in config.test_epcis:
        counts = run.rural_epci_coverage.get(epci_key, {})
        cells = " | ".join(
            f"{counts.get(network, 0)} patterns" for network in header_networks
        )
        lines.append(f"| {epci_key} | {cells} |")
    return "\n".join(lines)


def write_report(
    run: CalibrationRun, config: GtfsRebuildConfig, path: str | Path
) -> None:
    """Write the committed step 0 report (section 5.6 acceptance test)."""
    chosen = run.grid_result.chosen_theta
    text = f"""# Step 0: GTFS rebuilding test (section 5.6)

Calibration run on the reference date **{config.reference_date}**, against the
dated OSM extracts of **1 January 2022** and **1 January 2024**, for the five
test EPCIs and the metro/tram cases of section 5.6's calibration table.

## Recommended parameters

| Parameter | Value |
|---|---|
| r (matching radius) | {run.grid_result.chosen_r_m:g} m |
| k (cut run length) | {run.grid_result.chosen_k} |
| theta (bus) | {chosen.get("bus"):.2f} |
| theta (tram) | {chosen.get("tram"):.2f} |
| theta (metro) | {chosen.get("metro"):.2f} |
| theta (rail) | {chosen.get("rail"):.2f} (reuses the metro threshold; no rail case) |

Chosen as the (r, k) pair maximising the summed F1 of bus, tram and metro
against the known cases below, with theta optimised independently per mode
family at that (r, k). Written to `config/gtfs_rebuild.yaml` under `chosen`,
marked `TODO(confirm)` pending your review of this report.
{_bus_family_note(run)}
## Known cases: expected vs obtained

{_known_cases_table(config, run)}

The BHNS Part-Dieu - Sept-Chemins case ([TO CONFIRM: opening date], section
5.6) is reported for manual review only and is excluded from the score table.

## Score table (r, theta, k per mode family)

{_score_table(run)}

## Bus lines dropped or cut, by test EPCI

### Bordeaux Metropole

{_epci_line_list(run, config, "bordeaux_metropole", "bus")}

### Metropole de Lyon

{_epci_line_list(run, config, "metropole_de_lyon", "bus")}

### Sete Agglopole Mediterranee

{_epci_line_list(run, config, "sete_agglopole_mediterranee", "bus")}

## Rural EPCI spatial coverage (no network of their own)

Patterns of each regional/national network with at least one stop inside the
EPCI's 2026 polygon (section 5.6: "feed presence alone does not establish
coverage").

{_coverage_section(run, config)}

## Rail lines dropped or cut (manual review, metro thresholds)

No rail case is available in section 5.6's calibration table; SNCF patterns
reaching one of the five test EPCIs are scored with the metro theta and
listed here for manual review only (not included in the score table).

{_rail_manual_review(run)}
"""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
