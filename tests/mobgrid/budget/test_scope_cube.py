"""Tests for the cross-scope cube (section 9.9's cross-scope comparison).

The unit tests build ``CubeSurvey`` inputs directly and check the weighted
formulas and the shared household draws. The end-to-end tests run the
report on synthetic surveys of 60 respondents (so the 50-respondent
suppression does not blank every cell), with no network or ``data/raw``
access.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pytest
from mobgrid.budget import daily_energy, scope_cube
from mobgrid.budget import scope as scope_module

# ---------------------------------------------------------------------------
# Synthetic surveys of 60 respondents, one two-trip weekday each.
# Respondent variations: i % 12 == 0 starts the day away from home (not a
# round-trip day); i % 7 == 0 returns on a > 80 km trip (out of the local
# scope); i % 9 == 0 walks a stroll out (purpose 7.7, out of the destination
# scope, with its return). Every respondent is an employed adult, so the
# reference scope keeps at least 50 travellers per survey.
# ---------------------------------------------------------------------------

_EMP_K_DEPLOC_HEADER = (
    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,mobloc,MORIDOM,"
    "DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,DENSITECOM_ORI,DENSITECOM_DES,"
    "MMOTIFDES,MOT_SEQ_COMPL,STATUTCOM_UU_ORI,STATUTCOM_UU_DES,MTEMPSMAP,"
    "MTPSATTENT,NEW_VAC_SCOL,dVO_ORIDES,MDISTTOT_decl,indic_dist_corr,MOTPREC,"
    "dist_ign,IDENT_SEQ,MORIHDEP,MDESHARR"
)

N_RESPONDENTS = 72
N_NOT_ROUND = 6


def _variations(i: int) -> tuple[bool, bool, bool]:
    return i % 12 == 0, i % 7 == 0, i % 9 == 0


def _emp_k_deploc_rows() -> list[str]:
    rows = []
    for i in range(1, N_RESPONDENTS + 1):
        not_round, far_return, stroll = _variations(i)
        out_origin = "9.1" if not_round else "1.1"
        if stroll:
            mode_out, dist_out, dur_out, motif_out = "1.1", 1.5, 20, "7.7"
        else:
            mode_out, dist_out, motif_out = "3.1", 5.0, "9.1"
            dur_out = 15 + (i % 5) * 5
        rows.append(
            f"D{i}A,M{i},{i},1,100.0,1,1,1,{dur_out},{dist_out},0,0,"
            f"{mode_out},1,1,{motif_out},{motif_out},C,C,5,2,0,"
            f"{0.8 * dist_out},{dist_out},0,{out_origin},{dist_out},"
            f"SEQ{i}A,08:00,08:30"
        )
        mobloc_back = 0 if far_return else 1
        dist_back = 90.0 if far_return else dist_out
        dur_back = 60 if far_return else 20 + (i % 3) * 5
        mode_back = "1.1" if stroll else "3.1"
        rows.append(
            f"D{i}B,M{i},{i},2,100.0,1,{mobloc_back},2,{dur_back},{dist_back},"
            f"0,0,{mode_back},1,1,1.1,1.1,C,C,5,2,0,{0.8 * dist_back},"
            f"{dist_back},0,{motif_out},{dist_back},SEQ{i}B,17:00,17:30"
        )
    return rows


_WEEKDAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi")


def write_cube_emp_zip(path: Path) -> None:
    people = range(1, N_RESPONDENTS + 1)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "5. k_deploc_public_V4.csv",
            "\n".join([_EMP_K_DEPLOC_HEADER, *_emp_k_deploc_rows()]),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join(
                ["IDENT_IND;AGE;AGE6;SITUA;SEXE"]
                + [f"{i};{30 + i % 20};30;1;{1 + i % 2}" for i in people]
            ),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join(
                [
                    "IDENT_IND;IDENT_MEN;pond_indC;MIMMOSEM;MDATE_jour;"
                    "MDATE_delai;IMMODEP_A;IMMODEP_B;IMMODEP_C;IMMODEP_D;"
                    "IMMODEP_E;IMMODEP_F;IMMODEP_G;MDATE_mois"
                ]
                + [
                    f"{i};M{i};100.0;2;{_WEEKDAYS[(i - 1) % 5]};{(i - 1) % 7 + 1};"
                    "0;0;0;0;0;0;0;janvier"
                    for i in people
                ]
            ),
        )
        archive.writestr(
            "tcm_ind_public_V3.csv",
            "ident_ind;ident_men\n" + "\n".join(f"{i};M{i}" for i in people),
        )
        archive.writestr(
            "q_menage_public_V3.csv",
            "IDENT_MEN;pond_menC;JNBVEH\n"
            + "\n".join(f"M{i};100.0;1" for i in people),
        )
        archive.writestr(
            "tcm_men_public_V3.csv",
            '"ident_men","TUU2017_RES","STATUTCOM_UU_RES","TYPE_UU_RES",'
            '"TAA2017_RES","CATCOM_AA_RES","DENSITECOM_RES","decile_rev_uc",'
            '"REG_res"\n'
            + "\n".join(
                f'"M{i}","7","C","2","3","11","1","{(i - 1) % 10 + 1}","Bretagne"'
                for i in people
            ),
        )


_ENTD_K_DEPLOC_HEADER = (
    "IDENT_DEP;IDENT_IND;IDENT_MEN;IDENT_JOUR;POIDS_JOUR;V2_TYPJOUR;V2_DLOCAL;"
    "NODEP;V2_MORIDOM;v2_mduree;V2_DUREE;distcor;V2_MDISTTOT;V2_MACCOMPM;"
    "V2_MACCOMPHM;V2_MTP;V2_MMOTIFDES;V2_MMOTIFORI;v2_moricom_UU2010;"
    "v2_mdescom_UU2010;V2_MTEMPSMAP;V2_MTPSATTENT;V2_VAC_SCOL;V2_DVO_LOC;"
    "V2_MORIHDEP;V2_MDESHARR"
)


def _entd_k_deploc_rows() -> list[str]:
    rows = []
    for i in range(1, N_RESPONDENTS + 1):
        not_round, far_return, stroll = _variations(i)
        moridom = 2 if not_round else 1
        origin_out = "9.91" if not_round else ""
        if stroll:
            mode_out, dist_out, dur_out, motif_out = "1.10", 1.5, 20, "7.77"
        else:
            mode_out, dist_out, motif_out = "3.30", 5.0, "9.91"
            dur_out = 20 + (i % 5) * 5
        rows.append(
            f"D{i}A;{i};M{i};J{i};100;1;1;1;{moridom};{dur_out};{dur_out};"
            f"{dist_out};{dist_out};0;0;"
            f"{mode_out};{motif_out};{origin_out};C;C;5;2;0;{0.8 * dist_out};;"
        )
        local_back = 0 if far_return else 1
        dist_back = 90.0 if far_return else dist_out
        dur_back = 60 if far_return else 25 + (i % 3) * 5
        mode_back = "1.10" if stroll else "3.30"
        rows.append(
            f"D{i}B;{i};M{i};J{i};100;1;{local_back};2;2;{dur_back};{dur_back};"
            f"{dist_back};{dist_back};0;0;"
            f"{mode_back};1.1;{motif_out};C;C;5;2;0;{0.8 * dist_back};;"
        )
    return rows


def write_cube_entd_dir(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    people = range(1, N_RESPONDENTS + 1)
    files = {
        "k_deploc.csv": [_ENTD_K_DEPLOC_HEADER, *_entd_k_deploc_rows()],
        "k_individu.csv": [
            "IDENT_IND;IDENT_MEN;PONDKI;V2_MOBILREF;MDATENQ2V;V2_DATESEMREF;RG",
            *[f"{i};M{i};100;1;20/09/2007;19/09/2007;52" for i in people],
        ],
        "q_tcm_individu.csv": [
            "IDENT_IND;AGE;AGE6;SITUA;SEXE",
            *[f"{i};{30 + i % 20};30;1;{1 + i % 2}" for i in people],
        ],
        "q_tcm_menage.csv": [
            "IDENT_MEN;TU99;numcom_UUCat;TrancheRevenuMensuel;NBUC",
            *[
                f"M{i};7;ville centre;De 1 500 \u20ac \u00e0 moins de "
                f"1 800 \u20ac;1.5"
                for i in people
            ],
        ],
    }
    for name, lines in files.items():
        (raw_dir / name).write_text("\n".join(lines), encoding="cp1252")


@pytest.fixture(scope="module")
def cube_report(tmp_path_factory: pytest.TempPathFactory) -> dict:
    base = tmp_path_factory.mktemp("scope_cube")
    emp_zip = base / "emp2019-data.zip"
    write_cube_emp_zip(emp_zip)
    entd_dir = base / "entd2008"
    write_cube_entd_dir(entd_dir)
    out_dir = base / "cube"
    results = scope_cube.run(
        out_dir,
        n_reps=16,
        seed=0,
        emp2019_data_path=emp_zip,
        entd2008_data_path=entd_dir,
    )
    md_path = out_dir.with_suffix(".md")
    scope_cube.write_markdown(md_path, out_dir, results)
    return {
        "results": results,
        "md_path": md_path,
        "out_dir": out_dir,
        "lookup": scope_cube._row_lookup(results["rows"]),
    }


# ---------------------------------------------------------------------------
# Unit tests on hand-built CubeSurvey inputs.
# ---------------------------------------------------------------------------


def _unit_frame(minutes_scale: float = 1.0) -> scope_cube.ScopeDayFrame:
    """Three trip-days: a kept travel day, a dropped (non-round) day, and a
    kept day whose trips are all filtered out by the trip switches."""
    return scope_cube.ScopeDayFrame(
        person=np.array(["p1", "p2", "p3"], dtype=object),
        household=np.array(["h1", "h2", "h3"], dtype=object),
        category=np.array(["employed", "employed", "retired"], dtype=object),
        weight=np.array([10.0, 10.0, 20.0]),
        kept=np.array([True, False, True]),
        trips=np.array([2.0, 1.0, 0.0]),
        minutes=np.array([30.0, 15.0, 0.0]) * minutes_scale,
        minute_trips=np.array([2.0, 1.0, 0.0]),
        producer_km=np.array([4.0, 2.0, 0.0]),
        producer_trips=np.array([2.0, 1.0, 0.0]),
        crow_km=np.array([3.0, 1.5, 0.0]),
        crow_trips=np.array([2.0, 1.0, 0.0]),
    )


def _unit_survey(
    name: str = "EMP 2019",
    minutes_scale: float = 1.0,
    scope_ids: tuple[str, ...] = ("round-dest-local",),
) -> scope_cube.CubeSurvey:
    return scope_cube.CubeSurvey(
        name=name,
        roster_person=np.array(["p1", "p2", "p3"], dtype=object),
        roster_household=np.array(["h1", "h2", "h3"], dtype=object),
        roster_category=np.array(
            ["employed", "employed", "retired"], dtype=object
        ),
        roster_weight=np.array([50.0, 50.0, 100.0]),
        frames={
            scope_id: _unit_frame(minutes_scale) for scope_id in scope_ids
        },
    )


def test_cell_estimates_match_hand_computed_weighted_totals() -> None:
    """Section 9.9 bases: U = 200, dropped day weight = 10, kept = 30,
    travel = 10; weighted trips = 20, minutes = 300, producer km = 40,
    crow-fly km = 30 (all over kept days)."""
    cells = scope_cube.survey_cells(_unit_survey(), n_reps=8, seed=0)
    cell = cells[("round-dest-local", "All")]
    expected = {
        "person_days_kept_share": 190.0 / 200.0,
        "trips_per_day": 2.0,
        "minutes_per_trip": 15.0,
        "km_per_trip_producer": 2.0,
        "km_per_trip_crow_fly": 1.5,
        "minutes_per_day_day": 10.0,
        "minutes_per_day_travel_day": 30.0,
        "minutes_per_day_person": 300.0 / 190.0,
    }
    for key, value in expected.items():
        assert cell.estimates[key] == pytest.approx(value), key
    assert cell.n_respondents == 1
    assert cell.n_trips == 2
    assert cell.quantiles["trips_per_day"] == (2.0, 2.0, 2.0)
    assert cell.quantiles["minutes_per_day_day"] == (0.0, 0.0, 30.0)
    employed = cells[("round-dest-local", "employed")]
    assert employed.estimates["person_days_kept_share"] == pytest.approx(0.9)
    retired = cells[("round-dest-local", "retired")]
    assert retired.estimates["person_days_kept_share"] == pytest.approx(1.0)
    assert np.isnan(retired.estimates["trips_per_day"])


def test_household_draws_are_shared_across_scopes() -> None:
    """One multiplier matrix per survey: identical frames give identical
    replicates in every scope (the paired-draw requirement of item 2)."""
    survey = _unit_survey(scope_ids=("round-dest-local", "alldays-dest-local"))
    cells = scope_cube.survey_cells(survey, n_reps=32, seed=7)
    for key in scope_cube._cell_metrics(np.zeros(len(scope_cube._COMPONENTS))):
        np.testing.assert_array_equal(
            cells[("round-dest-local", "All")].replicates[key],
            cells[("alldays-dest-local", "All")].replicates[key],
        )


def test_ratio_reuses_shared_replicate_ratio_ci() -> None:
    """Doubling every duration doubles the point ratio exactly, and the
    interval equals the shared ``bootstrap_replicate_ratio_ci``'s."""
    cells_2008 = scope_cube.survey_cells(
        _unit_survey("ENTD 2008"), n_reps=64, seed=1
    )
    cells_2019 = scope_cube.survey_cells(
        _unit_survey("EMP 2019", minutes_scale=2.0), n_reps=64, seed=2
    )
    cell_2008 = cells_2008[("round-dest-local", "All")]
    cell_2019 = cells_2019[("round-dest-local", "All")]
    key = "minutes_per_day_travel_day"
    ratio = scope_cube._ratio_with_ci(cell_2008, cell_2019, key)
    assert ratio is not None
    estimate, ci = ratio
    assert estimate == pytest.approx(2.0)
    expected = daily_energy.bootstrap_replicate_ratio_ci(
        cell_2008.estimates[key],
        cell_2008.replicates[key],
        cell_2019.estimates[key],
        cell_2019.replicates[key],
    )
    assert (estimate, ci) == expected


def test_core_rows_suppress_small_cells_and_keep_counts() -> None:
    """Cells under 50 respondents keep their true n and blank every value,
    including the ratio columns on the EMP 2019 row."""
    scope_ids = tuple(selected.id for selected in scope_module.ALL_SCOPES)
    cells_2008 = scope_cube.survey_cells(
        _unit_survey("ENTD 2008", scope_ids=scope_ids), n_reps=8, seed=1
    )
    cells_2019 = scope_cube.survey_cells(
        _unit_survey("EMP 2019", scope_ids=scope_ids), n_reps=8, seed=2
    )
    rows = scope_cube.core_rows(
        cells_2008,
        cells_2019,
        ["All", "employed", "retired"],
        equivalence_margin=0.15,
        secondary_equivalence_margin=0.10,
    )
    lookup = scope_cube._row_lookup(rows)
    row = lookup[
        ("round-dest-local", "EMP 2019", "All", "trips_per_day", "travel_day")
    ]
    assert row["n"] == 1
    assert row["mean"] == "" and row["median"] == ""
    assert row["ratio"] == "" and row["verdict_15"] == ""
    count_row = lookup[
        ("round-dest-local", "ENTD 2008", "All", "n_trips", "count")
    ]
    assert count_row["n"] == 2


# ---------------------------------------------------------------------------
# End-to-end on the synthetic 60-respondent surveys.
# ---------------------------------------------------------------------------


def test_report_covers_every_scope_and_counts_open_scope_trips(
    cube_report: dict,
) -> None:
    text = cube_report["md_path"].read_text(encoding="utf-8")
    for selected_scope in scope_module.ALL_SCOPES:
        assert f"| {selected_scope.id} |" in text
    assert "### Sample sizes" in text
    lookup = cube_report["lookup"]
    # The open scope keeps all 120 trips of each survey's 60 respondents.
    for survey in ("ENTD 2008", "EMP 2019"):
        key = ("alldays-allpurp-daytable", survey, "All", "n_trips", "count")
        assert lookup[key]["n"] == 2 * N_RESPONDENTS
        key = (
            "alldays-allpurp-daytable",
            survey,
            "All",
            "n_respondents",
            "count",
        )
        assert lookup[key]["n"] == N_RESPONDENTS


def test_day_switch_drops_person_days_only_under_round(
    cube_report: dict,
) -> None:
    """`alldays` keeps the full person-weekday universe; `round` drops the
    non-round days' weights (section 9.9's open-day rule)."""
    lookup = cube_report["lookup"]
    for survey in ("ENTD 2008", "EMP 2019"):
        alldays = lookup[
            (
                "alldays-allpurp-local",
                survey,
                "All",
                "person_days_kept_share",
                "person_days",
            )
        ]
        assert alldays["mean"] == pytest.approx(1.0)
        round_scope = lookup[
            (
                "round-dest-local",
                survey,
                "All",
                "person_days_kept_share",
                "person_days",
            )
        ]
        # N_NOT_ROUND respondents (i % 12 == 0) start the day away from
        # home; each described day carries 1/5 of its person-weekday weight.
        expected = 1.0 - N_NOT_ROUND / N_RESPONDENTS / 5.0
        assert round_scope["mean"] == pytest.approx(expected)


def test_report_shows_unsuppressed_values_and_ratios(cube_report: dict) -> None:
    lookup = cube_report["lookup"]
    row = lookup[
        ("round-dest-local", "EMP 2019", "All", "minutes_per_day", "day")
    ]
    assert row["n"] >= scope_cube.MIN_CELL_N
    assert row["mean"] != "" and row["ci_low"] != "" and row["median"] != ""
    assert row["ratio"] != "" and row["verdict_15"] in (
        "equivalent",
        "different",
        "inconclusive",
    )
    text = cube_report["md_path"].read_text(encoding="utf-8")
    spec = next(
        spec
        for spec in scope_cube.INDICATOR_SPECS
        if spec.indicator == "minutes_per_day" and spec.basis == "day"
    )
    assert scope_cube._mean_cell(row, spec) in text
