"""PT change catalogue acceptance tests (section 11.4)."""

from datetime import date
from pathlib import Path

from mobgrid.pt.pt_changes import (
    PtChange,
    PtChangeCandidate,
    PtChangeCatalogue,
    load_pt_changes,
)

ROOT = Path(__file__).resolve().parents[3]


def _catalogue() -> PtChangeCatalogue:
    return PtChangeCatalogue(
        confirmed=[
            PtChange(
                id="x",
                type="pt_new_line",
                network="net",
                route_ids=["1"],
                opened=date(2026, 1, 1),
                description="d",
            )
        ],
        to_review=[
            PtChangeCandidate(
                id="c1",
                network="net",
                route_id="2",
                outcomes_by_date={"2022-01-01": "dropped"},
                match_pass="name",
                covered_share=0.5,
            )
        ],
        not_applied=[
            PtChangeCandidate(
                id="c2",
                network="net",
                route_id="3",
                outcomes_by_date={"2022-01-01": "kept-renamed"},
                match_pass="geometry",
                covered_share=0.9,
            )
        ],
    )


def test_only_confirmed_changes_are_subtracted_from_past_state() -> None:
    catalogue = load_pt_changes(ROOT / "config" / "pt_changes.yaml")
    route_ids = {
        route_id
        for change in catalogue.changes_after(date(2024, 1, 1))
        for route_id in change.route_ids
    }
    assert route_ids == {"901", "911", "912", "A"}
    candidate_route_ids = {
        candidate.route_id
        for candidate in (*catalogue.to_review, *catalogue.not_applied)
    }
    assert route_ids.isdisjoint(candidate_route_ids)


def test_pt_change_notes_defaults_to_none_and_is_optional() -> None:
    assert PtChange(
        id="x",
        type="pt_extend",
        network="net",
        route_ids=["1"],
        description="d",
    ).notes is None
    assert PtChange(
        id="y",
        type="pt_extend",
        network="net",
        route_ids=["1"],
        description="d",
        notes="a data-gap note",
    ).notes == "a data-gap note"


def test_removed_route_keys_default_only_subtracts_confirmed() -> None:
    catalogue = _catalogue()
    assert catalogue.removed_route_keys(date(2022, 1, 1)) == {("net", "1")}


def test_removed_route_keys_candidates_sensitivity_adds_dropped_candidates() -> None:
    catalogue = _catalogue()
    removed = catalogue.removed_route_keys(
        date(2022, 1, 1), sensitivity="confirmed_and_candidates"
    )
    assert removed == {("net", "1"), ("net", "2")}


def test_rejected_candidates_are_never_removed_by_either_sensitivity() -> None:
    catalogue = PtChangeCatalogue(
        rejected=[
            PtChangeCandidate(
                id="c4",
                network="net",
                route_id="4",
                outcomes_by_date={"2022-01-01": "dropped"},
                match_pass="name",
                covered_share=0.5,
                notes="reviewer confirmed false positive",
            )
        ]
    )
    for sensitivity in ("confirmed", "confirmed_and_candidates"):
        assert catalogue.removed_route_keys(
            date(2022, 1, 1), sensitivity=sensitivity
        ) == set()
