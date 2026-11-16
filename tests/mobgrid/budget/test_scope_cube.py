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
        "emp_zip": emp_zip,
        "entd_dir": entd_dir,
        "results": results,
        "md_path": md_path,
        "out_dir": out_dir,
        "lookup": scope_cube._row_lookup(results["rows"]),
    }


def test_reference_person_value_matches_c7_extraction(cube_report: dict) -> None:
    """Section 9.9: actual scope loaders retain open-day denominator weights."""
    import duckdb
    from mobgrid.budget import emp2019, entd2008, variation_report
    from mobgrid.energy.rates import load_energy_config

    for survey, path in (
        (emp2019, cube_report["emp_zip"]), (entd2008, cube_report["entd_dir"])
    ):
        with duckdb.connect() as con:
            paths = survey.extract_tables(path, path.parent / survey.SURVEY_NAME)
            survey.register_views(con, paths)
            survey.build_trip_legs(
                con, load_energy_config(scope_cube.DEFAULT_CONFIG_PATH),
                density_source=survey.DEFAULT_DENSITY_SOURCE,
            )
            scope_module.create_scope_views_from_trip_legs(con, activity_stay_min=15)
            sample = variation_report._c7_scope_data(
                con, survey, scope_module.REFERENCE_SCOPE, None
            )
            assert sample.is_open.any()
            estimate = variation_report._period_budget_estimates(
                sample, day_types=(1,),
                person_period_divisor=5.0 if survey is emp2019 else 1.0,
                n_reps=16, seed=0,
            )["per_person"]["minutes_per_day"]
        row = cube_report["lookup"][(
            "round-dest-local", survey.SURVEY_NAME, "All", "minutes_per_day", "person"
        )]
        assert row["mean"] == pytest.approx(estimate.estimate)
        assert row["n"] == N_RESPONDENTS


def test_reference_comparison_report_matches_cube(
    cube_report: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Section 9.9: actual survey report retains open days in denominator."""
    from mobgrid.budget import emp, emp2019, entd2008

    monkeypatch.setattr(
        emp.daily_energy, "calibrate_v0_kmh", lambda *args, **kwargs: [5.0]
    )
    monkeypatch.setattr(
        emp.daily_energy, "calibrate_p0", lambda *args, **kwargs: [30.0]
    )
    reports = [
        emp.run(
            tmp_path / survey.__name__.rsplit(".", 1)[-1],
            survey=survey, data_path=path, n_reps=16, seed=0, make_figures=False,
        )
        for survey, path in (
            (entd2008, cube_report["entd_dir"]),
            (emp2019, cube_report["emp_zip"]),
        )
    ]
    comparison = emp._temporal_person_budget_rows(*reports, n_reps=16, seed=0)[-1]
    for survey, expected in (
        ("ENTD 2008", comparison.estimate_2008),
        ("EMP 2019", comparison.estimate_2019),
    ):
        row = cube_report["lookup"][(
            "round-dest-local", survey, "All", "minutes_per_day", "person"
        )]
        assert row["mean"] == pytest.approx(expected)
        if survey == "EMP 2019":
            assert row["ratio"] == pytest.approx(comparison.ratio)
            assert (row["ratio_ci_low"], row["ratio_ci_high"]) == pytest.approx(
                comparison.ci
            )


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


def test_reference_time_ratio_ci_matches_b2_c7_and_comparison() -> None:
    """Section 9.9: nontravellers remain in every estimator's draw universe."""
    from mobgrid.budget import emp
    from mobgrid.budget import variation_report as vr

    frames, results, cells = [], [], []
    for year, child in enumerate(np.random.SeedSequence(8).spawn(2)):
        n = 100
        households = np.array([f"h{i:03}" for i in range(n)])
        minutes = np.linspace(20, 90 + year * 20, n)
        weight = np.linspace(1, 2, n)
        kept = np.arange(n) % 9 != 0
        trips = np.where(np.arange(n) < 80, 2.0, 0.0)
        minutes[trips == 0] = 0
        frame = scope_cube.ScopeDayFrame(
            person=households, household=households, category=np.full(n, "employed"),
            weight=weight, kept=kept, trips=trips, minutes=minutes,
            minute_trips=trips, producer_km=trips * 5, producer_trips=trips,
            crow_km=trips * 4, crow_trips=trips,
        )
        cube = scope_cube.CubeSurvey(
            name=("ENTD 2008", "EMP 2019")[year],
            roster_person=households, roster_household=households,
            roster_category=frame.category, roster_weight=weight * 5,
            frames={"round-dest-local": frame},
        )
        cells.append(scope_cube.survey_cells(
            cube, n_reps=40, seed=child
        )[("round-dest-local", "All")])
        selected = kept & (trips > 0)
        days = {
            "ident_ind": households[selected], "ident_men": households[selected],
            "pond_jour": weight[selected], "total_time_min": minutes[selected],
            "population_category": frame.category[selected],
            "trips_per_day": trips[selected],
            "total_distance_km": trips[selected] * 5,
            "distance_trips": trips[selected],
            "distance_time_min": minutes[selected],
        }
        sample = vr.PeriodBudgetSample(
            person_household=households, person_weight=weight * (5 if year == 0 else 1),
            day_household=households, day_person=households, day_weight=weight,
            day_type=np.ones(n, dtype=int), trips=trips, total_time_min=minutes,
            time_trips=trips, is_open=~kept,
        )
        frames.append(vr.SurveyFrames(
            str(year), days, {}, {"c7_data": dict.fromkeys(
                ("reference", "sdes", "daytable"), sample
            ), "household_universe": households}
        ))
        results.append({"_weekday_days": days, "_weekday_person_rows": {
            "household": households,
        }})
    expected = scope_cube._ratio_with_ci(*cells, "minutes_per_day_travel_day")
    b2 = vr.b2_decompositions(
        *frames, n_reps=40, seed=8, include_time_ratio=True, categories=()
    )[0]
    c7 = next(row for row in vr._c7_comparison(*frames, n_reps=40, seed=8)
              if row["scope"] == "round-dest-local" and row["period"] == "weekday"
              and row["basis"] == "per traveller" and row["measure"] == "Minutes/day")
    comparison = emp._temporal_day_ratio_rows(
        *results, n_reps=40, seed=8
    )[-1]
    for ratio, ci in (
        (b2.time_ratio, b2.time_ratio_ci90), c7["ratio"],
        (comparison.ratio, comparison.ci),
    ):
        assert ratio == pytest.approx(expected[0], abs=1e-14)
        assert ci == pytest.approx(expected[1], abs=1e-14)


# ---------------------------------------------------------------------------
# Switch effects (item 2).
# ---------------------------------------------------------------------------


def test_switch_effects_are_zero_with_degenerate_cis_on_identical_scopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With identical frames in every scope, the paired draws make every
    level and ratio change exactly zero with a [0, 0] interval -- an
    unpaired bootstrap would give nonzero interval width."""
    monkeypatch.setattr(scope_cube, "MIN_CELL_N", 1)
    scope_ids = tuple(selected.id for selected in scope_module.ALL_SCOPES)
    cells_2008 = scope_cube.survey_cells(
        _unit_survey("ENTD 2008", scope_ids=scope_ids), n_reps=32, seed=1
    )
    cells_2019 = scope_cube.survey_cells(
        _unit_survey("EMP 2019", minutes_scale=2.0, scope_ids=scope_ids),
        n_reps=32,
        seed=2,
    )
    rows = scope_cube.switch_rows(cells_2008, cells_2019)
    lookup = scope_cube._row_lookup(rows)
    for _, flipped_scope in scope_cube.SWITCH_FLIPS:
        for survey in ("ENTD 2008", "EMP 2019"):
            row = lookup[
                (
                    flipped_scope.id,
                    survey,
                    "All",
                    "change_minutes_per_day",
                    "travel_day",
                )
            ]
            assert row["mean"] == pytest.approx(0.0)
            assert row["ci_low"] == pytest.approx(0.0)
            assert row["ci_high"] == pytest.approx(0.0)
        ratio_row = lookup[
            (
                flipped_scope.id,
                "EMP 2019",
                "All",
                "change_minutes_per_day",
                "travel_day",
            )
        ]
        assert ratio_row["ratio"] == pytest.approx(0.0)
        assert ratio_row["ratio_ci_low"] == pytest.approx(0.0)
        assert ratio_row["ratio_ci_high"] == pytest.approx(0.0)


def test_switch_effect_rows_match_item1_levels_and_appear_in_report(
    cube_report: dict,
) -> None:
    """Each change equals the difference of the item-1 levels, the ratio
    change equals the difference of the item-1 ratios, and the report has
    one switch-effect table per flip."""
    lookup = cube_report["lookup"]
    text = cube_report["md_path"].read_text(encoding="utf-8")
    assert "## 2. Switch effects from the reference scope" in text
    reference_id = scope_module.REFERENCE_SCOPE.id
    for _, flipped_scope in scope_cube.SWITCH_FLIPS:
        for survey in ("ENTD 2008", "EMP 2019"):
            change = lookup[
                (
                    flipped_scope.id,
                    survey,
                    "All",
                    "change_minutes_per_day",
                    "day",
                )
            ]
            reference = lookup[
                (reference_id, survey, "All", "minutes_per_day", "day")
            ]
            flipped = lookup[
                (flipped_scope.id, survey, "All", "minutes_per_day", "day")
            ]
            assert change["mean"] == pytest.approx(
                flipped["mean"] - reference["mean"]
            )
        ratio_change = lookup[
            (flipped_scope.id, "EMP 2019", "All", "change_minutes_per_day", "day")
        ]
        reference_ratio = lookup[
            (reference_id, "EMP 2019", "All", "minutes_per_day", "day")
        ]
        flipped_ratio = lookup[
            (flipped_scope.id, "EMP 2019", "All", "minutes_per_day", "day")
        ]
        assert ratio_change["ratio"] == pytest.approx(
            flipped_ratio["ratio"] - reference_ratio["ratio"]
        )
    # Flipping the distance switch brings the > 80 km returns back in, so
    # producer km per trip rises in both surveys.
    distance_scope = next(
        flipped
        for switch, flipped in scope_cube.SWITCH_FLIPS
        if switch == "distance"
    )
    for survey in ("ENTD 2008", "EMP 2019"):
        row = lookup[
            (
                distance_scope.id,
                survey,
                "All",
                "change_km_per_trip_producer",
                "trip",
            )
        ]
        assert row["mean"] > 0


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


# ---------------------------------------------------------------------------
# Tidy CSV (item 3).
# ---------------------------------------------------------------------------


def _read_csv_rows(csv_path: Path) -> list[dict]:
    import csv

    with csv_path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _csv_row(rows: list[dict], **conditions: str) -> dict:
    matches = [
        row
        for row in rows
        if all(row[key] == value for key, value in conditions.items())
    ]
    assert len(matches) == 1, (conditions, len(matches))
    return matches[0]


def _parsed(row: dict) -> dict:
    """CSV strings back to the report writer's row values."""
    parsed = dict(row)
    for key in (
        "mean",
        "ci_low",
        "ci_high",
        "median",
        "p25",
        "p75",
        "ratio",
        "ratio_ci_low",
        "ratio_ci_high",
    ):
        if parsed[key] != "":
            parsed[key] = float(parsed[key])
    return parsed


def _table_line(text: str, heading: str, scope: str, category: str) -> str:
    lines = text.splitlines()
    start = lines.index(heading)
    prefix = f"| {scope} | {category} |"
    for line in lines[start + 1 :]:
        if line.startswith("### ") or line.startswith("## "):
            break
        if line.startswith(prefix):
            return line
    raise AssertionError(f"no row {prefix!r} under {heading!r}")


def test_csv_has_required_columns_and_all_cube_rows(cube_report: dict) -> None:
    csv_path = cube_report["results"]["csv_path"]
    assert csv_path == cube_report["out_dir"] / "estimates.csv"
    rows = _read_csv_rows(csv_path)
    assert list(rows[0].keys()) == list(scope_cube.CSV_COLUMNS)
    scopes = {row["scope"] for row in rows}
    assert scopes == {selected.id for selected in scope_module.ALL_SCOPES}
    # Switch columns always carry the scope's own settings.
    row = _csv_row(
        rows,
        scope="round-dest-daytable",
        survey="EMP 2019",
        category="All",
        indicator="change_minutes_per_day",
        basis="day",
    )
    assert (
        row["days_switch"],
        row["purposes_switch"],
        row["distance_switch"],
    ) == ("round", "dest", "daytable")


def test_csv_rows_equal_report_table_cells(cube_report: dict) -> None:
    """A few CSV rows, formatted with the report's own cell formatters,
    equal the report's table cells (the CSV is built from the table rows)."""
    text = cube_report["md_path"].read_text(encoding="utf-8")
    rows = _read_csv_rows(cube_report["results"]["csv_path"])
    spec = next(
        spec
        for spec in scope_cube.INDICATOR_SPECS
        if spec.indicator == "minutes_per_day" and spec.basis == "day"
    )
    for scope_id in ("round-dest-local", "alldays-allpurp-daytable"):
        row_2019 = _parsed(
            _csv_row(
                rows,
                scope=scope_id,
                survey="EMP 2019",
                category="All",
                indicator="minutes_per_day",
                basis="day",
            )
        )
        line = _table_line(text, f"### {spec.label}", scope_id, "All")
        assert scope_cube._mean_cell(row_2019, spec) in line
        assert scope_cube._quantile_cell(row_2019, spec) in line
        ratio_cell, verdict_15, verdict_10 = scope_cube._ratio_cells(row_2019)
        assert ratio_cell in line
        assert f" {verdict_15} |" in line and f" {verdict_10} |" in line
    # Per-trip ratio-of-totals table.
    trip_spec = next(
        spec
        for spec in scope_cube.INDICATOR_SPECS
        if spec.key == "minutes_per_trip"
    )
    trip_row = _parsed(
        _csv_row(
            rows,
            scope="round-dest-local",
            survey="ENTD 2008",
            category="All",
            indicator="minutes_per_trip",
            basis="trip",
        )
    )
    line = _table_line(
        text, f"### {trip_spec.label}", "round-dest-local", "All"
    )
    assert scope_cube._mean_cell(trip_row, trip_spec) in line
    # A switch-effect cell.
    change_row = _parsed(
        _csv_row(
            rows,
            scope="round-dest-daytable",
            survey="EMP 2019",
            category="All",
            indicator="change_km_per_trip_producer",
            basis="trip",
        )
    )
    km_spec = next(
        spec
        for spec in scope_cube.INDICATOR_SPECS
        if spec.key == "km_per_trip_producer"
    )
    heading = "### Distance: `local` → `daytable` (`round-dest-daytable`)"
    lines = text.splitlines()
    start = lines.index(heading)
    switch_line = next(
        line
        for line in lines[start + 1 :]
        if line.startswith(f"| {km_spec.label} |")
    )
    assert scope_cube._delta_cell(change_row, km_spec) in switch_line
    assert scope_cube._ratio_delta_cell(change_row) in switch_line
