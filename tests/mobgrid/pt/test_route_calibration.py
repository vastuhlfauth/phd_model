"""Scoring rules for the relation-based GTFS rebuild calibration."""

from mobgrid.pt.route_calibration import RouteEvaluation, score_family


def test_scores_known_cases_and_false_change_rate_separately() -> None:
    evaluations = [
        RouteEvaluation("known-new", "bus", "dropped", "dropped", True),
        RouteEvaluation("known-cut", "bus", "cut", "kept", True),
        RouteEvaluation("old-1", "bus", "kept", "kept", False),
        RouteEvaluation("old-2", "bus", "kept", "cut", False),
        RouteEvaluation("unknown", "bus", "not-testable", "not-testable", False),
    ]
    score = score_family(evaluations, "bus")
    assert score.known_total == 2
    assert score.precision == 1.0
    assert score.recall == 0.5
    assert score.f1 == 2 / 3
    assert score.presumed_unchanged_total == 2
    assert score.false_change_rate == 0.5


def test_kept_renamed_is_not_a_false_change() -> None:
    evaluations = [
        RouteEvaluation("renamed", "tram", "kept", "kept-renamed", False)
    ]
    assert score_family(evaluations, "tram").false_change_rate == 0.0


def test_kept_renamed_is_a_detected_known_rename() -> None:
    evaluations = [
        RouteEvaluation(
            "known-rename", "tram", "kept-renamed", "kept-renamed", True
        )
    ]
    score = score_family(evaluations, "tram")
    assert score.recall == 1.0
    assert score.known_correct == 1
