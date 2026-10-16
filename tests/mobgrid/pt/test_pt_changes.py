"""PT change catalogue acceptance tests (section 11.4)."""

from datetime import date
from pathlib import Path

import yaml
from mobgrid.pt.config import load_gtfs_rebuild_config
from mobgrid.pt.pt_changes import (
    OpeningDerivedChange,
    PtChange,
    PtChangeCandidate,
    PtChangeCatalogue,
    build_network_resource_ids,
    load_pt_changes,
    write_from_openings,
)

ROOT = Path(__file__).resolve().parents[3]

# All tests here use a single network ("net") for both confirmed (slug
# convention) and from_openings (CSV free-text convention) entries, so one
# fixed resource id stands in for whatever real GTFS resource id a config
# would resolve it to.
_NETWORK_RESOURCE_IDS = {"net": 1}


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


def _opening_change(
    opening_id: str,
    route_id: str,
    change_type: str,
    state_2022: str,
    state_2024: str,
    **kwargs,
) -> OpeningDerivedChange:
    return OpeningDerivedChange(
        opening_id=opening_id,
        network="net",
        route_id=route_id,
        mode="tram",
        change_type=change_type,
        match_confidence="exact",
        csv_confidence="high",
        state_2022=state_2022,
        state_2024=state_2024,
        **kwargs,
    )


def test_removed_route_keys_equals_confirmed_plus_openings_drops_only() -> None:
    """2026-10-15/16 national policy: the routes a past state subtracts
    are exactly the confirmed edits plus the openings list's own `drop`
    instructions -- `to_review`/`not_applied` never change this result,
    even when a candidate names the very same route an openings-list row
    drops.

    Real case: TCL Lyon's `TB12` is both `candidate_tcl_lyon_TB12` (old
    automatic OSM screening, `kept-renamed`, informational only) and
    `ARA-08` (openings-list `new_line`, `state_2022`/`state_2024` both
    `remove` -- a real drop). The candidate changes nothing.
    """
    catalogue = load_pt_changes(ROOT / "config" / "pt_changes.yaml")
    config = load_gtfs_rebuild_config(ROOT / "config" / "gtfs_rebuild.yaml")
    network_resource_ids = build_network_resource_ids(config)
    mode_split_resource_ids = (
        config.national_policy.openings_list.mode_split_network_resource_ids
    )

    def _resolve(network: str, mode: str | None) -> int:
        if network in mode_split_resource_ids:
            return mode_split_resource_ids[network][mode]
        return network_resource_ids[network]

    for state_date in (date(2022, 1, 1), date(2024, 1, 1)):
        expected = {
            (_resolve(change.network, None), route_id)
            for change in catalogue.changes_after(state_date)
            for route_id in change.route_ids
        }
        expected |= {
            (_resolve(change.network, change.mode), change.route_id)
            for change in catalogue.from_openings
            if change.removed_at(state_date)
        }
        removed = catalogue.removed_route_keys(
            state_date,
            network_resource_ids=network_resource_ids,
            mode_split_network_resource_ids=mode_split_resource_ids,
        )
        assert removed == expected

    confirmed_route_ids = {
        route_id
        for change in catalogue.changes_after(date(2024, 1, 1))
        for route_id in change.route_ids
    }
    assert confirmed_route_ids == {"901", "911", "912", "A"}

    # TB12: a real openings-list drop that also happens to be a
    # screening candidate for the same network/route.
    tcl_resource_id = network_resource_ids["TCL (SYTRAL Mobilités)"]
    assert any(
        candidate.network == "tcl_lyon" and candidate.route_id == "TB12"
        for candidate in (*catalogue.to_review, *catalogue.not_applied)
    )
    removed_2022 = catalogue.removed_route_keys(
        date(2022, 1, 1),
        network_resource_ids=network_resource_ids,
        mode_split_network_resource_ids=mode_split_resource_ids,
    )
    assert (tcl_resource_id, "TB12") in removed_2022

    # Emptying to_review/not_applied must not change the result at all --
    # they are read-only/informational, never consulted by
    # removed_route_keys (section 5.6 point 6).
    catalogue_without_candidates = catalogue.model_copy(
        update={"to_review": [], "not_applied": []}
    )
    removed_2022_without_candidates = catalogue_without_candidates.removed_route_keys(
        date(2022, 1, 1),
        network_resource_ids=network_resource_ids,
        mode_split_network_resource_ids=mode_split_resource_ids,
    )
    assert removed_2022_without_candidates == removed_2022




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
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {(1, "1")}


def test_removed_route_keys_never_reads_to_review_or_not_applied() -> None:
    # 2026-10-15 national policy point 6: to_review/not_applied are
    # informational only; the former "confirmed_and_candidates" sensitivity
    # option that used to read them (dropping candidate route "2" too) is
    # removed -- only the confirmed route "1" is ever subtracted.
    catalogue = _catalogue()
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {(1, "1")}


def test_new_line_remove_drops_the_route() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[_opening_change("O1", "5", "new_line", "remove", "keep")]
    )
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {(1, "5")}
    assert catalogue.removed_route_keys(
        date(2024, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == set()


def test_reopening_remove_drops_the_route() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[_opening_change("O1", "5", "reopening", "remove", "remove")]
    )
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {(1, "5")}
    assert catalogue.removed_route_keys(
        date(2024, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {(1, "5")}


def test_keep_and_modify_states_never_remove_a_route() -> None:
    # 2026-10-16 fix of the 2026-10-15 bug: "modify" is not an instruction
    # (section 5.6 point 1) -- an extension/new_station/new_line/reopening
    # row whose state is "keep" or "modify" must never remove anything.
    for change_type in ("new_line", "reopening", "extension", "new_station"):
        for state in ("keep", "modify"):
            catalogue = PtChangeCatalogue(
                from_openings=[
                    _opening_change("O1", "5", change_type, state, state)
                ]
            )
            assert catalogue.removed_route_keys(
                date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
            ) == set()
            assert catalogue.removed_route_keys(
                date(2024, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
            ) == set()


def test_extension_remove_cuts_rather_than_drops() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[_opening_change("O1", "5", "extension", "remove", "keep")]
    )
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == set()
    assert catalogue.removed_route_keys(
        date(2024, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == set()
    change = catalogue.from_openings[0]
    assert change.instruction_at(date(2022, 1, 1)) == "cut"
    assert change.instruction_at(date(2024, 1, 1)) is None


def test_new_station_remove_never_drops_the_route() -> None:
    catalogue = PtChangeCatalogue(
        from_openings=[_opening_change("O1", "5", "new_station", "remove", "remove")]
    )
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == set()
    change = catalogue.from_openings[0]
    assert change.instruction_at(date(2022, 1, 1)) == "new_station"


def test_unrecognised_change_type_with_remove_is_logged_not_guessed() -> None:
    change = _opening_change("O1", "5", "suspension", "keep", "remove")
    assert change.instruction_at(date(2022, 1, 1)) is None
    assert change.unhandled_remove_at(date(2022, 1, 1)) is False
    assert change.instruction_at(date(2024, 1, 1)) is None
    assert change.unhandled_remove_at(date(2024, 1, 1)) is True
    # removed_route_keys must not be affected by an unhandled remove.
    catalogue = PtChangeCatalogue(from_openings=[change])
    assert catalogue.removed_route_keys(
        date(2024, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == set()


def test_metro_14_two_extensions_combine_without_ever_dropping_the_route() -> None:
    # Real case: IDF-11 (extension, north) and IDF-12 (extension, south),
    # both remove/remove -- section 5.6 point 3, replacing the OR rule.
    catalogue = PtChangeCatalogue(
        from_openings=[
            _opening_change("IDF-11", "M14", "extension", "remove", "remove"),
            _opening_change("IDF-12", "M14", "extension", "remove", "remove"),
        ]
    )
    for state_date in (date(2022, 1, 1), date(2024, 1, 1)):
        assert catalogue.removed_route_keys(
            state_date, network_resource_ids=_NETWORK_RESOURCE_IDS
        ) == set()
        for change in catalogue.from_openings:
            assert change.instruction_at(state_date) == "cut"


def test_opening_derived_change_instruction_at_rejects_an_unknown_state_date() -> None:
    change = _opening_change("O1", "5", "new_line", "keep", "keep")
    try:
        change.instruction_at(date(2023, 6, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("expected a ValueError for an unknown state date")


def test_removed_route_keys_counts_same_route_once_from_both_conventions() -> None:
    # The real-world case this guards against: a route confirmed by a
    # config slug (e.g. "tbm_bordeaux") and the same physical route named
    # by the openings CSV's own free-text network string (e.g. "TBM
    # (Bordeaux M\u00e9tropole)") must resolve to one (resource id,
    # route_id) key, not two -- both strings describe GTFS resource 5
    # here (2026-10-16 fix).
    catalogue = PtChangeCatalogue(
        confirmed=[
            PtChange(
                id="x",
                type="pt_new_line",
                network="slug_x",
                route_ids=["77"],
                opened=date(2026, 1, 1),
                description="d",
            )
        ],
        from_openings=[
            OpeningDerivedChange(
                opening_id="O1",
                network="X Network (Operator)",
                route_id="77",
                mode="tram",
                change_type="new_line",
                match_confidence="exact",
                csv_confidence="high",
                state_2022="remove",
                state_2024="remove",
            )
        ],
    )
    removed = catalogue.removed_route_keys(
        date(2022, 1, 1),
        network_resource_ids={"slug_x": 5, "X Network (Operator)": 5},
    )
    assert removed == {(5, "77")}


def test_write_from_openings_merges_and_leaves_other_lists_untouched(
    tmp_path,
) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "confirmed": [
                    {
                        "id": "x",
                        "type": "pt_new_line",
                        "network": "net",
                        "route_ids": ["1"],
                        "opened": "2026-01-01",
                        "description": "d",
                    }
                ],
                "to_review": [],
                "not_applied": [],
                "rejected": [],
            }
        ),
        encoding="utf-8",
    )
    applied = (_opening_change("O1", "5", "new_line", "remove", "keep"),)
    write_from_openings(path, applied)

    catalogue = load_pt_changes(path)
    assert len(catalogue.confirmed) == 1
    assert [change.opening_id for change in catalogue.from_openings] == ["O1"]
    assert catalogue.removed_route_keys(
        date(2022, 1, 1), network_resource_ids=_NETWORK_RESOURCE_IDS
    ) == {
        (1, "1"),
        (1, "5"),
    }


def test_write_from_openings_treats_an_empty_file_as_an_empty_mapping(
    tmp_path,
) -> None:
    # A freshly touched or truncated file: yaml.safe_load returns None, not
    # {} -- write_from_openings must not crash on raw.setdefault(...).
    path = tmp_path / "pt_changes.yaml"
    path.write_text("   \n", encoding="utf-8")

    applied = (_opening_change("O1", "5", "new_line", "remove", "keep"),)
    write_from_openings(path, applied)

    catalogue = load_pt_changes(path)
    assert catalogue.confirmed == []
    assert catalogue.to_review == []
    assert catalogue.not_applied == []
    assert catalogue.rejected == []
    assert [change.opening_id for change in catalogue.from_openings] == ["O1"]

