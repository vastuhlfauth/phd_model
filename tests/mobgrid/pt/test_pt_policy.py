"""Precedence tests for the national past-state policy (2026-10-15, point 7)."""

from __future__ import annotations

from mobgrid.pt.pt_policy import resolve_route_presence


def test_openings_override_wins_over_the_tram_automatic_rule() -> None:
    # The automatic rule would cut/drop the route, but the openings list
    # says it is present: the openings list wins outright.
    assert (
        resolve_route_presence(
            family_rule="automatic_osm",
            opening_removed=False,
            tram_rule_removed=True,
        )
        == "present"
    )


def test_openings_override_wins_even_the_other_way_round() -> None:
    # The automatic rule would keep the route, but the openings list says
    # it is absent: the openings list still wins.
    assert (
        resolve_route_presence(
            family_rule="automatic_osm",
            opening_removed=True,
            tram_rule_removed=False,
        )
        == "absent"
    )


def test_openings_override_applies_to_default_keep_families_too() -> None:
    # Metro/rail/bus/ferry have no automatic rule at all, but an openings
    # match still overrides the default keep.
    assert (
        resolve_route_presence(
            family_rule="default_keep_except_openings",
            opening_removed=True,
        )
        == "absent"
    )


def test_tram_automatic_rule_applies_only_without_an_openings_match() -> None:
    assert (
        resolve_route_presence(
            family_rule="automatic_osm",
            opening_removed=None,
            tram_rule_removed=True,
        )
        == "absent"
    )
    assert (
        resolve_route_presence(
            family_rule="automatic_osm",
            opening_removed=None,
            tram_rule_removed=False,
        )
        == "present"
    )


def test_tram_rule_is_never_consulted_for_a_default_keep_family() -> None:
    # Even if a caller mistakenly passes a tram-rule result for a family
    # whose policy does not use it, it must be ignored.
    assert (
        resolve_route_presence(
            family_rule="default_keep_except_openings",
            opening_removed=None,
            tram_rule_removed=True,
        )
        == "present"
    )


def test_default_keep_when_no_source_has_an_opinion() -> None:
    assert (
        resolve_route_presence(
            family_rule="automatic_osm",
            opening_removed=None,
            tram_rule_removed=None,
        )
        == "present"
    )
    assert (
        resolve_route_presence(
            family_rule="default_keep_except_openings",
            opening_removed=None,
        )
        == "present"
    )
