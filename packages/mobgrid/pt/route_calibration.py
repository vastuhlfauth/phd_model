"""Calibration metrics for relation-based historical GTFS rebuilding."""

from __future__ import annotations

from dataclasses import dataclass

from mobgrid.pt.route_relations import RouteOutcome


@dataclass(frozen=True)
class RouteEvaluation:
    """Expected and obtained route-level outcome at one OSM date."""

    route_id: str
    mode_family: str
    expected: RouteOutcome
    obtained: RouteOutcome
    known_case: bool


@dataclass(frozen=True)
class FamilyScore:
    """Known-case detection metrics and presumed-unchanged false changes."""

    mode_family: str
    known_total: int
    known_correct: int
    precision: float
    recall: float
    f1: float
    presumed_unchanged_total: int
    false_change_rate: float


def score_family(
    evaluations: list[RouteEvaluation], mode_family: str
) -> FamilyScore:
    """Score known changes separately from presumed-unchanged routes."""
    rows = [
        row
        for row in evaluations
        if row.mode_family == mode_family and row.obtained != "not-testable"
    ]
    known = [row for row in rows if row.known_case]
    presumed = [row for row in rows if not row.known_case]
    true_positive = sum(
        row.expected != "kept"
        and row.obtained in ("cut", "dropped", "kept-renamed")
        for row in known
    )
    false_positive = sum(
        row.expected == "kept"
        and row.obtained in ("cut", "dropped", "kept-renamed")
        for row in known
    )
    false_negative = sum(
        row.expected != "kept"
        and row.obtained not in ("cut", "dropped", "kept-renamed")
        for row in known
    )
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = (
        true_positive / precision_denominator if precision_denominator else 1.0
    )
    recall = true_positive / recall_denominator if recall_denominator else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    false_changes = sum(
        row.obtained in ("cut", "dropped") for row in presumed
    )
    false_change_rate = false_changes / len(presumed) if presumed else 0.0
    return FamilyScore(
        mode_family,
        len(known),
        sum(row.expected == row.obtained for row in known),
        precision,
        recall,
        f1,
        len(presumed),
        false_change_rate,
    )
