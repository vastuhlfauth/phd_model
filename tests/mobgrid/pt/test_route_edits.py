"""Tests for cut/new_station edit resolution (section 5.6 point 2/3)."""

from __future__ import annotations

from datetime import date

from mobgrid.pt.pt_changes import OpeningDerivedChange, PtChangeCatalogue
from mobgrid.pt.route_edits import (
    EditOutcome,
    RouteEditSpec,
    collect_edit_specs,
    resolve_route_edits,
)

# A stylised corridor (origin -> terminus), long enough to exercise both
# cut directions and a new_station removal.
_STOPS = [
    "Origin",
    "Stop 1",
    "Stop 2",
    "Old Terminus",
    "New Stop A",
    "New Stop B",
    "New Terminus",
]


def test_cut_keeps_stops_up_to_the_old_terminus_when_new_terminus_is_after() -> None:
    edit = RouteEditSpec("O1", "cut", "Old Terminus", "New Terminus")
    outcome = resolve_route_edits(_STOPS, [edit])
    assert outcome == EditOutcome(7, 4, ("O1",), ())


def test_cut_direction_is_symmetric_when_the_pattern_is_reversed() -> None:
    reversed_stops = list(reversed(_STOPS))
    edit = RouteEditSpec("O1", "cut", "Old Terminus", "New Terminus")
    outcome = resolve_route_edits(reversed_stops, [edit])
    # Same 4 stops kept (Origin..Old Terminus), regardless of direction.
    assert outcome.kept_stop_count == 4


def test_new_station_removes_only_the_one_named_stop() -> None:
    edit = RouteEditSpec("O1", "new_station", "Stop 1")
    outcome = resolve_route_edits(_STOPS, [edit])
    assert outcome == EditOutcome(7, 6, ("O1",), ())


def test_unresolved_anchor_is_logged_and_keeps_the_route_whole() -> None:
    edit = RouteEditSpec("O1", "cut", "Nonexistent Place", "Also Nonexistent")
    outcome = resolve_route_edits(_STOPS, [edit])
    assert outcome.kept_stop_count == len(_STOPS)
    assert outcome.applied_opening_ids == ()
    assert outcome.unresolved_opening_ids == ("O1",)


def test_one_unresolved_edit_does_not_block_another_resolvable_edit() -> None:
    edits = [
        RouteEditSpec("O1", "cut", "Old Terminus", "New Terminus"),
        RouteEditSpec("O2", "new_station", "Nonexistent Stop"),
    ]
    outcome = resolve_route_edits(_STOPS, edits)
    assert outcome.applied_opening_ids == ("O1",)
    assert outcome.unresolved_opening_ids == ("O2",)
    assert outcome.kept_stop_count == 4  # the valid cut still applies


def test_metro_14_two_extensions_cut_both_ends_without_dropping() -> None:
    # Real case (section 5.6 point 3, IDF-11 north + IDF-12 south): two
    # independent extension rows combine to trim both ends of one route.
    stops = [
        "Saint-Denis Pleyel",  # new, north
        "Mairie de Saint-Ouen",  # old north terminus
        "Saint-Lazare",
        "Chatelet",
        "Olympiades",  # old south terminus
        "Villejuif-Gustave Roussy",  # new, south
        "Aeroport d'Orly",  # new, south
    ]
    north_cut = RouteEditSpec(
        "IDF-11", "cut", "Mairie de Saint-Ouen", "Saint-Denis Pleyel"
    )
    south_cut = RouteEditSpec("IDF-12", "cut", "Olympiades", "Aeroport d'Orly")
    outcome = resolve_route_edits(stops, [north_cut, south_cut])
    assert outcome.applied_opening_ids == ("IDF-11", "IDF-12")
    assert outcome.unresolved_opening_ids == ()
    # Only "Mairie de Saint-Ouen".."Olympiades" (indices 1..4) remain.
    assert outcome.kept_stop_count == 4


def test_collect_edit_specs_ignores_drop_and_no_instruction_entries() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[
            OpeningDerivedChange(
                opening_id="O1",
                network="net",
                route_id="A",
                mode="rail",
                change_type="new_line",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="remove",
                state_2024="remove",
            ),
            OpeningDerivedChange(
                opening_id="O2",
                network="net",
                route_id="B",
                mode="rail",
                change_type="extension",
                section_from="Old End",
                section_to="New End",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="remove",
                state_2024="keep",
            ),
            OpeningDerivedChange(
                opening_id="O3",
                network="net",
                route_id="C",
                mode="rail",
                change_type="restructuring",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="modify",
                state_2024="modify",
            ),
        ]
    )
    specs = collect_edit_specs(catalogue, date(2022, 1, 1))
    assert set(specs) == {("net", "B")}
    assert specs[("net", "B")][0].kind == "cut"
    assert specs[("net", "B")][0].anchor_from == "Old End"


def test_collect_edit_specs_combines_several_edits_on_the_same_route() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[
            OpeningDerivedChange(
                opening_id="IDF-11",
                network="net",
                route_id="M14",
                mode="metro",
                change_type="extension",
                section_from="Mairie de Saint-Ouen",
                section_to="Saint-Denis Pleyel",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="remove",
                state_2024="remove",
            ),
            OpeningDerivedChange(
                opening_id="IDF-12",
                network="net",
                route_id="M14",
                mode="metro",
                change_type="extension",
                section_from="Olympiades",
                section_to="Aeroport d'Orly",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="remove",
                state_2024="remove",
            ),
        ]
    )
    specs = collect_edit_specs(catalogue, date(2022, 1, 1))
    assert len(specs[("net", "M14")]) == 2
