"""Unit tests for stop scoring and cutting (section 5.6 points 3 to 5)."""

from mobgrid.pt.gtfs_rebuild import (
    PatternMatch,
    rebuild_pattern,
    rebuild_patterns,
    route_outcome,
)


def _match(flags: tuple[bool, ...], mode_family: str = "bus") -> PatternMatch:
    return PatternMatch("p1", "R1", "0", mode_family, flags)


def test_pattern_dropped_below_theta() -> None:
    # share s = 1/5 = 0.2, below theta = 0.5: whole pattern dropped.
    result = rebuild_pattern(_match((True, False, False, False, False)), theta=0.5, k=2)
    assert result.outcome == "dropped"
    assert result.n == 5
    assert result.m == 1
    assert result.s == 0.2


def test_pattern_kept_when_fully_matched() -> None:
    result = rebuild_pattern(_match((True, True, True, True)), theta=0.5, k=2)
    assert result.outcome == "kept"
    assert (result.start_index, result.end_index) == (0, 3)
    assert not result.flagged_interior


def test_trailing_extension_is_cut() -> None:
    # Share 4/6 = 0.667 stays above theta; the last two stops are a new
    # extension (k=2) and are trimmed, the pattern ends at the last match.
    flags = (True, True, True, True, False, False)
    result = rebuild_pattern(_match(flags), theta=0.5, k=2)
    assert result.outcome == "cut"
    assert (result.start_index, result.end_index) == (0, 3)
    assert not result.flagged_interior


def test_leading_extension_is_cut() -> None:
    flags = (False, False, True, True, True, True)
    result = rebuild_pattern(_match(flags), theta=0.5, k=2)
    assert result.outcome == "cut"
    assert (result.start_index, result.end_index) == (2, 5)


def test_isolated_interior_gap_is_kept_without_flag() -> None:
    # A single unmatched stop inside the pattern (run length 1 < k=2) is
    # kept, per section 5.6: "more often gaps in OSM than new stations".
    flags = (True, True, False, True, True)
    result = rebuild_pattern(_match(flags), theta=0.5, k=2)
    assert result.outcome == "kept"
    assert (result.start_index, result.end_index) == (0, 4)
    assert not result.flagged_interior


def test_long_interior_run_is_kept_but_flagged() -> None:
    # A long interior unmatched run (>= k) is a possible new branch and is
    # listed for review, but the stops are not removed from the pattern.
    flags = (True, True, False, False, True, True)
    result = rebuild_pattern(_match(flags), theta=0.5, k=2)
    assert result.outcome == "kept"
    assert (result.start_index, result.end_index) == (0, 5)
    assert result.flagged_interior


def test_both_ends_cut_leaves_isolated_interior_gap_intact() -> None:
    flags = (False, False, True, False, True, True, False, False)
    result = rebuild_pattern(_match(flags), theta=0.1, k=2)
    assert result.outcome == "cut"
    assert (result.start_index, result.end_index) == (2, 5)
    assert not result.flagged_interior


def test_all_unmatched_pattern_is_dropped_via_trim_guard() -> None:
    # No match anywhere: share is 0 and (even with theta=0) trimming both
    # ends would cross; the defensive guard reports "dropped".
    flags = (False, False, False, False, False)
    result = rebuild_pattern(_match(flags), theta=0.0, k=2)
    assert result.outcome == "dropped"


def test_rebuild_patterns_uses_mode_family_theta() -> None:
    matches = [
        _match((True, True, False, False), mode_family="bus"),
        _match((True, True, False, False), mode_family="tram"),
    ]
    results = rebuild_patterns(matches, {"bus": 0.4, "tram": 0.6}, k=2)
    by_family = {result.mode_family: result for result in results}
    assert by_family["bus"].outcome == "cut"  # s=0.5 >= 0.4
    assert by_family["tram"].outcome == "dropped"  # s=0.5 < 0.6


def test_route_outcome_is_worst_case_across_patterns() -> None:
    kept = rebuild_pattern(_match((True, True, True)), theta=0.5, k=1)
    cut = rebuild_pattern(_match((True, True, False, False)), theta=0.1, k=1)
    dropped = rebuild_pattern(_match((False, False, True)), theta=0.5, k=1)
    assert route_outcome([kept]) == "kept"
    assert route_outcome([kept, cut]) == "cut"
    assert route_outcome([kept, cut, dropped]) == "dropped"
