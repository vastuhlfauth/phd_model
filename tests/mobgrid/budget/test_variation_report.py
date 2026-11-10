"""Tests for the step-12 variation report (``mobgrid.budget.
variation_report``): Part A tables on tiny in-memory frames and CLI routing."""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import duckdb
import numpy as np
import pytest
from mobgrid.budget import figstyle, scope, variation_report
from mobgrid.budget.variation_report import SurveyFrames

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

N_REPS = 3
CLI_N_REPS = 1


def test_scope_cli_defaults_to_reference_and_scope_all_runs_eight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def fake_run(out_dir, config_path, **kwargs):
        calls.append((out_dir, kwargs["scope"].id))
        return {"figures": []}

    monkeypatch.setattr(variation_report, "run", fake_run)
    monkeypatch.setattr(variation_report, "write_markdown", lambda *args: None)

    assert (
        variation_report.main(
            [
                "--out",
                str(tmp_path / "step12"),
                "--entd2008-zoning-data-path",
                "zoning",
            ]
        )
        == 0
    )
    assert calls[-1][1] == "round-dest-local"

    calls.clear()
    assert (
        variation_report.main(
            [
                "--out",
                str(tmp_path / "step12"),
                "--entd2008-zoning-data-path",
                "zoning",
                "--scope",
                "all",
            ]
        )
        == 0
    )
    assert [scope_id for _, scope_id in calls] == [s.id for s in scope.ALL_SCOPES]
    assert calls[0][0] == tmp_path / "scopes" / calls[0][1] / "step12"
    assert len({path for path, _ in calls}) == len(scope.ALL_SCOPES)


@pytest.mark.parametrize("survey_name", ["EMP 2019", "ENTD 2008"])
@pytest.mark.parametrize("id_type", ["BIGINT", "VARCHAR"])
def test_scope_roster_categories_preserve_numeric_and_text_person_ids(
    survey_name: str, id_type: str
) -> None:
    """Section 9.9: roster and trip-day category weights must agree."""
    con = duckdb.connect()
    try:
        con.execute(f"""
            CREATE TABLE k_individu (
                IDENT_IND {id_type}, IDENT_MEN VARCHAR,
                pond_indC DOUBLE, PONDKI DOUBLE
            );
            INSERT INTO k_individu VALUES ('1', 'h1', 2.0, 2.0);
            CREATE TABLE tcm_ind_kish (
                IDENT_IND {id_type}, SITUA VARCHAR, AGE INTEGER
            );
            INSERT INTO tcm_ind_kish VALUES ('1', '3', 25);
            CREATE TABLE q_tcm_individu AS SELECT * FROM tcm_ind_kish;
        """)
        roster = variation_report._scope_person_weekday_rows(
            con, survey_name, sample_pct=None
        )
        assert roster == [("1", "h1", "other_inactive", 10.0)]
        bootstrap, negative_cells, _ = variation_report._bootstrap_scope_day_shares(
            roster,
            [("h1", "other_inactive", 5.0, *([0.0] * 13))],
            n_reps=3,
            seed=0,
        )
        assert bootstrap["other_inactive"]["point"]["no_trip_share"] == 0.5
        assert negative_cells == 0
    finally:
        con.close()


def test_scope_diagnostics_report_open_days_rule_drops_and_coverage() -> None:
    con = duckdb.connect()
    con.sql("""
        CREATE TABLE scope_input (
            day_id VARCHAR, num_dep INTEGER, origin_purpose VARCHAR,
            destination_purpose VARCHAR, destination_motive DOUBLE,
            motive DOUBLE, moridom DOUBLE, mode_group VARCHAR, mobloc INTEGER,
            departure_time TIME, arrival_time TIME
        )
    """)
    con.sql("""
        INSERT INTO scope_input VALUES
            ('sport', 1, '1.1', '7.6', 7.6, 7.6, 1, 'walk', 1,
                '08:00', '08:10'),
            ('sport', 2, '7.6', '1.1', 1.1, 7.6, NULL, 'walk', 1,
                '08:20', '08:30'),
            ('open', 1, '1.1', '9.1', 9.1, 9.1, 2, 'car_driver', 1,
                '09:00', '09:20'),
            ('nonlocal-study', 1, '1.1', '1.4', 1.4, 1.4, 1,
                'car_driver', 0, '10:00', '10:30')
    """)
    scope.create_scope_views(con, activity_stay_min=15)
    con.sql("""
        CREATE TABLE trip_legs AS
        SELECT day_id, num_dep, day_id || '-' || num_dep AS ident_dep,
            day_id AS ident_men, CASE day_id
                WHEN 'sport' THEN 2.0
                WHEN 'open' THEN 1.0
                ELSE 3.0
            END AS pond_jour,
            1 AS typejour, 35 AS age, 'employed' AS population_category,
            mode_group, mobloc, CASE
                WHEN day_id = 'sport' THEN 10.0
                WHEN day_id = 'open' THEN 20.0
                ELSE 30.0
            END AS duration_min, CASE
                WHEN day_id = 'sport' THEN 1.0
                WHEN day_id = 'open' THEN 2.0
                ELSE 10.0
            END AS distance_km,
            motive
        FROM scope_input
    """)
    con.sql("""
        CREATE TABLE vr_trip_ext AS
        SELECT ident_dep, CASE WHEN day_id = 'sport' THEN 0.8
            WHEN day_id = 'open' THEN 1.5 ELSE 9.0 END AS crow_fly_km
        FROM trip_legs
    """)
    con.sql("""
        CREATE TABLE k_individu (
            IDENT_IND VARCHAR, IDENT_MEN VARCHAR, PONDKI DOUBLE,
            V2_MOBILREF INTEGER
        )
    """)
    con.sql("""
        INSERT INTO k_individu VALUES
            ('sport', 'sport', 1.0, 2),
            ('open', 'open', 1.0, 2),
            ('nonlocal-study', 'nonlocal-study', 1.0, 2)
    """)
    con.sql("""
        CREATE TABLE q_tcm_individu (
            IDENT_IND VARCHAR, SITUA VARCHAR, AGE INTEGER
        )
    """)
    con.sql("""
        INSERT INTO q_tcm_individu VALUES
            ('sport', '1', 35), ('open', '1', 35),
            ('nonlocal-study', '1', 35)
    """)

    try:
        diagnostics = variation_report.scope_diagnostics(
            con, survey_name="ENTD 2008", sample_pct=None, n_reps=30, seed=2
        )
        con.sql("UPDATE q_tcm_individu SET SITUA = NULL")
        con.sql("UPDATE trip_legs SET population_category = 'unknown'")
        unknown = variation_report.scope_diagnostics(
            con, survey_name="ENTD 2008", sample_pct=None, n_reps=1, seed=2
        )
    finally:
        con.close()

    open_days = next(
        row
        for row in diagnostics["open_days"]
        if row["population_category"] == "overall"
    )
    assert open_days["last_not_home_share"] == pytest.approx(4 / 15)
    assert open_days["last_not_home_trip_share"] == pytest.approx(4 / 6)
    assert open_days["ends_study_childcare_share"] == pytest.approx(3 / 15)
    assert open_days["ends_study_childcare_trip_share"] == pytest.approx(3 / 6)
    assert open_days["tripday_share"] == pytest.approx(6 / 15)
    assert open_days["no_trip_share"] == pytest.approx(9 / 15)
    assert open_days["origin_moridom_agreement"] == pytest.approx(5 / 6)

    activity = next(
        row
        for row in diagnostics["activity"]
        if row["population_category"] == "overall" and row["mode_group"] == "walk"
    )
    assert activity["n_trips"] == 2
    assert activity["trips_per_day"] == pytest.approx(4 / 15)
    assert activity["mean_duration_min"] == pytest.approx(10.0)
    assert activity["mean_duration_min_ci95"] is not None
    assert activity["mean_crow_fly_km"] == pytest.approx(0.8)
    assert activity["stay_5_15_share"] == pytest.approx(1.0)
    assert activity["dropped_share_5"] == pytest.approx(0.0)
    assert activity["dropped_share_15"] == pytest.approx(1.0)
    assert activity["dropped_share_15_ci95"] is not None
    all_modes_activity = next(
        row
        for row in diagnostics["activity"]
        if row["population_category"] == "overall" and row["mode_group"] == "all modes"
    )
    assert all_modes_activity["dropped_share_15"] == pytest.approx(4 / 5)

    drops = {
        row["rule"]: row
        for row in diagnostics["rule_drops"]
        if row["population_category"] == "overall" and row["mode_group"] == "all modes"
    }
    assert drops["distance"]["trip_share"] == pytest.approx(3 / 8)
    assert drops["distance"]["trip_share_ci95"] is not None
    assert drops["distance"]["minute_share"] == pytest.approx(90 / 150)
    assert drops["distance"]["km_share"] == pytest.approx(30 / 36)
    assert drops["activity"]["trip_share"] == pytest.approx(4 / 8)
    assert drops["day"]["trip_share"] == pytest.approx(1 / 8)

    coverage = next(
        row
        for row in diagnostics["coverage"]
        if row["population_category"] == "overall"
    )
    assert coverage["n_respondents"] == 3
    for section in ("open_days", "activity", "rule_drops", "coverage"):
        assert not any(
            row["population_category"] == "unknown" for row in unknown[section]
        )
    assert coverage["days_with_nonlocal_share"] == pytest.approx(3 / 15)
    assert coverage["days_with_nonlocal_trip_share"] == pytest.approx(3 / 6)
    assert coverage["nonlocal_trips_per_day"] == pytest.approx(3 / 15)
    assert coverage["nonlocal_minutes_per_day"] == pytest.approx(90 / 15)
    assert coverage["nonlocal_km_per_day"] == pytest.approx(30 / 15)
    assert coverage["days_out_no_local_share"] == pytest.approx(3 / 15)
    assert coverage["days_out_no_local_trip_share"] == pytest.approx(3 / 6)
    assert diagnostics["partial_coverage"] is True
    assert diagnostics["away_reason_recorded"] is False
    rendered = "\n".join(
        variation_report._format_scope_diagnostics({"ENTD 2008": diagnostics})
    )
    assert "### Coverage of the day table" in rendered
    assert scope.DAYTABLE_COVERAGE_NOTE in rendered
    assert "95% CI" in rendered
    assert "person-weekdays / trip-days" in rendered
    assert "negative point-estimate population cells" in rendered
    assert "not recorded" in rendered


@pytest.mark.parametrize("category", ["unknown", "employed"])
@pytest.mark.parametrize("n", [49, 50])
def test_coverage_table_suppresses_small_respondent_cells(category, n) -> None:
    """Section 9.9: 50 respondents, not weighted days or trip counts."""
    metrics = (
        "days_with_nonlocal_share",
        "days_with_nonlocal_trip_share",
        "nonlocal_trips_per_day",
        "nonlocal_minutes_per_day",
        "nonlocal_km_per_day",
        "days_out_no_local_share",
        "days_out_no_local_trip_share",
    )
    row = {
        "population_category": category,
        "n_respondents": n,
        **dict.fromkeys(metrics, 0.123),
        **{f"{metric}_ci95": (0.1, 0.2) for metric in metrics},
    }
    diagnostics = {
        "open_days": [], "activity": [], "rule_drops": [], "coverage": [row],
        "negative_point_cells": 0, "negative_bootstrap_cell_draws": 0,
        "bootstrap_replicates": 1,
    }
    text = "\n".join(
        variation_report._format_scope_diagnostics({"EMP 2019": diagnostics})
    ).split("### Coverage of the day table")[1]
    lines = [line for line in text.splitlines() if line.startswith("| EMP 2019 |")]
    if category == "unknown" and n < 50:
        assert not lines
    else:
        assert len(lines) == 1
        assert f"| {n} |" in lines[0]
        assert ("12.3%" in lines[0]) == (n >= 50)


def test_scope_diagnostics_does_not_clip_negative_person_weekday_cells() -> None:
    diagnostics, negative_cells, negative_draws = (
        variation_report._bootstrap_scope_day_shares(
            [("person", "household", "employed", 5.0)],
            [("household", "employed", 6.0, *([0.0] * 13))],
            n_reps=3,
            seed=1,
        )
    )

    employed = diagnostics["employed"]
    assert employed["estimable"] is False
    assert np.isnan(employed["point"]["no_trip_share"])
    assert employed["ci95"]["tripday_share"] is None
    assert negative_cells == 1
    assert negative_draws == 3


def test_c7_reports_daytable_ratio_with_observed_coverage_note() -> None:
    report = "\n".join(
        variation_report._format_c7(
            [
                {
                    "scope": "alldays-allpurp-daytable",
                    "period": "weekday",
                    "basis": "per person",
                    "measure": "Minutes/day",
                    "n_2008": 100,
                    "estimate_2008": 100.0,
                    "n_2019": 100,
                    "estimate_2019": 102.0,
                    "ratio": (1.12, (1.11, 1.14)),
                }
            ],
            equivalence_margin=0.15,
            secondary_equivalence_margin=0.10,
        )
    )

    assert "alldays-allpurp-daytable" in report
    assert "1.120 [1.110, 1.140]" in report
    assert "| ±15% | ±10% |" in report
    assert "| equivalent | different |" in report
    assert scope.DAYTABLE_COVERAGE_NOTE in report


def test_return_legs_are_attributed_to_the_preceding_activity_mode() -> None:
    """Section 9.9: a car return dropped with a walk belongs in its column."""
    con = duckdb.connect()
    con.sql("""
        CREATE TABLE scope_diag_trips AS
        SELECT * FROM (VALUES
            ('employed', 'walk', TRUE, TRUE, FALSE, FALSE, 'car_driver'),
            ('employed', 'cycle', TRUE, TRUE, FALSE, FALSE, 'cycle'),
            ('employed', 'walk', TRUE, TRUE, TRUE, FALSE, 'walk'),
            ('retired', 'walk', TRUE, FALSE, FALSE, FALSE, 'walk'))
        AS v(population_category, prior_mode, return_home, prior_15,
            drop_distance, drop_group8, mode_group)
    """)
    counts = variation_report._scope_return_leg_counts(con)
    assert counts[("employed", "walk")] == 1
    assert counts[("employed", "cycle")] == 1
    assert counts[("employed", "all modes")] == 2
    assert counts[("overall", "all modes")] == 2
    con.close()


def test_compact_scope_tables_and_detail_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section 9.9: aggregate tables, retained detail, and scope heading placement."""
    import csv

    rules = []
    for category, mode, share in (
        ("overall", "all modes", 0.1),
        ("employed", "all modes", 0.2),
        ("employed", "walk", 0.8),
    ):
        for rule in (
            "distance",
            "group 8",
            "activity",
            "day",
            "activity_5",
            "activity_15",
            "activity_30",
        ):
            rules.append(
                {
                    "population_category": category,
                    "mode_group": mode,
                    "rule": rule,
                    "trips": 10.0,
                    "minutes": 20.0,
                    "km": 30.0,
                    "trip_share": share,
                    "minute_share": share,
                    "km_share": share,
                }
            )
    activities = [
        {
            "population_category": "overall",
            "mode_group": mode,
            "n_trips": n,
            "return_legs_dropped": returns,
            "trips_per_day": 0.1,
            "mean_duration_min": 10.0,
            "mean_crow_fly_km": 1.0,
            **dict.fromkeys(
                (
                    "stay_under_5_share",
                    "stay_5_15_share",
                    "stay_15_30_share",
                    "stay_30_plus_share",
                    "no_next_share",
                    "dropped_share_5",
                    "dropped_share_15",
                    "dropped_share_30",
                ),
                0.1,
            ),
        }
        for mode, n, returns in (
            ("walk", 2, 1),
            ("cycle", 2, 1),
            ("all modes", 4, 2),
            ("car_driver", 0, 0),
        )
    ]
    for row in [*rules, *activities]:
        row.update(
            {
                f"{key}_ci95": None
                for key, value in row.items()
                if isinstance(value, float)
            }
        )
    diagnostics = {
        "open_days": [],
        "activity": activities,
        "rule_drops": rules,
        "coverage": [],
        "negative_point_cells": 0,
        "negative_bootstrap_cell_draws": 0,
        "bootstrap_replicates": 200,
    }
    for name in ("_format_a1", "_format_a2", "_format_a3", "_format_a4", "_format_a5"):
        monkeypatch.setattr(variation_report, name, lambda results: [])
    results = {
        "scope": scope.REFERENCE_SCOPE,
        "n_reps": 200,
        "n_days_2008": 60,
        "n_days_2019": 60,
        "n_trips_2008": 120,
        "n_trips_2019": 120,
        "scope_diagnostics": {"ENTD 2008": diagnostics, "EMP 2019": diagnostics},
        "choices": [],
        "extra_sections": [
            [
                "## B2. Time",
                "### C5. Official-scope replication",
                "### C7. Budgets per person",
            ]
        ],
        "figures": [tmp_path / "synthetic.png"],
    }
    md_path = tmp_path / "report.md"
    variation_report.write_markdown(md_path, tmp_path, results)
    report = md_path.read_text(encoding="utf-8")
    assert report.splitlines()[0].endswith(scope.REFERENCE_SCOPE.label)
    assert "## B2. Time\n" in report
    assert "## Scope\n" in report
    assert "### C5. Official-scope replication — " + scope.SDES_SCOPE.label in report
    assert "### C7. Budgets per person — Scopes:" in report
    assert "\n*Scope:" not in report
    activity = report.split("### Walking/cycling as the activity")[1].split(
        "### What each rule removes"
    )[0]
    assert "| car_driver |" not in activity
    assert "Return legs dropped" in activity
    removals = report.split("### What each rule removes")[1].split(
        "### Coverage of the day table"
    )[0]
    assert removals.count("all modes and population categories") == 2
    assert "By population category (all modes)" in removals
    assert "activity_5" not in removals
    assert "80.0%" not in removals
    assert "10.0%" in removals and "20.0%" in removals
    csv_path = tmp_path / "report_scope_rules_round-dest-local.csv"
    assert csv_path.name in report
    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2 * len(rules)
    assert {row["scope"] for row in rows} == {"round-dest-local"}
    assert any(
        row["mode_group"] == "walk" and row["rule"] == "activity_30" for row in rows
    )


def _frames(days: dict, trips: dict, aux: dict | None = None) -> SurveyFrames:
    return SurveyFrames(
        name="synthetic",
        days={k: np.asarray(v) for k, v in days.items()},
        trips={k: np.asarray(v) for k, v in trips.items()},
        aux=aux or {},
    )


def _simple_frames(lags: list[float]) -> SurveyFrames:
    n = len(lags)
    days = {
        "pond_jour": [1.0] * n,
        "recall_lag": lags,
        "total_time_min": [30.0 + 10.0 * (lag or 0) for lag in lags],
        "trips_per_day": [2.0] * n,
        "total_distance_km": [5.0] * n,
        "population_category": ["employed"] * n,
        "home_density": ["dense"] * n,
        "ident_men": [f"M{i}" for i in range(n)],
        "described_weekday_name": ["lundi"] * n,
    }
    trips = {
        "pond_jour": [1.0] * (2 * n),
        "recall_lag": [lag for lag in lags for _ in range(2)],
        "duration_min": [4.0, 26.0] * n,
        "distance_km": [0.5, 4.5] * n,
    }
    return _frames(days, trips)


def test_recall_lag_table_counts_and_shares_by_lag() -> None:
    frames = _simple_frames([1.0, 1.0, 2.0, float("nan")])

    rows = variation_report.recall_lag_table(frames)

    by_label = {row.label: row for row in rows}
    assert by_label["1"].n_days == 2
    assert by_label["2"].n_days == 1
    # Weighted shares are over the days with a known lag only.
    assert by_label["1"].weighted_share == pytest.approx(2.0 / 3.0)
    assert by_label["2"].weighted_share == pytest.approx(1.0 / 3.0)
    # The all-days row includes the unknown-lag day.
    assert by_label["all days"].n_days == 4
    assert by_label["1"].trips_per_day == pytest.approx(2.0)
    assert by_label["1"].minutes_per_trip == pytest.approx(15.0)
    assert by_label["1"].time_per_day_min == pytest.approx(40.0)
    assert by_label["1"].share_trips_under_5_min == pytest.approx(0.5)
    assert by_label["1"].share_trips_under_1_km == pytest.approx(0.5)


def test_lag_regression_recovers_a_pure_lag_effect() -> None:
    # time = 40 at lag 1, 50 at lag 2: the lag-2 dummy should be +10.
    frames = _simple_frames([1.0, 1.0, 2.0, 2.0, 1.0, 2.0])

    coefficients = variation_report.lag_regression(
        frames, "total_time_min", n_reps=N_REPS, seed=0
    )

    by_lag = {c.lag: c for c in coefficients}
    assert by_lag[2].coefficient == pytest.approx(10.0)
    assert by_lag[2].n_days == 3
    assert np.isfinite(by_lag[2].ci).all()
    # Lags absent from the data get a 0 coefficient (empty dummy).
    assert by_lag[7].n_days == 0


@pytest.mark.parametrize("outcome", ["total_time_min", "trips_per_day"])
def test_lag_regression_controls_for_described_weekday(outcome: str) -> None:
    frames = _simple_frames([1.0] * 4 + [2.0] * 4)
    frames.days["described_weekday_name"] = np.array(
        [
            "lundi",
            "lundi",
            "lundi",
            "vendredi",
            "lundi",
            "vendredi",
            "vendredi",
            "vendredi",
        ]
    )
    frames.days[outcome] = np.where(
        frames.days["described_weekday_name"] == "vendredi", 90.0, 30.0
    ) + np.where(frames.days["recall_lag"] == 2, 10.0, 0.0)
    coefficients = variation_report.lag_regression(
        frames, outcome, n_reps=N_REPS, seed=0
    )
    assert coefficients[0].coefficient == pytest.approx(10.0)


def test_motive_crosswalk_flags_merged_and_one_survey_codes() -> None:
    frames_2008 = _frames(
        {},
        {},
        aux={
            "raw_motive_shares": {
                "destination": {"9.91": 0.6, "1.1": 0.3, "5.59": 0.1},
                "origin": {},
            }
        },
    )
    frames_2019 = _frames(
        {},
        {},
        aux={
            "raw_motive_shares": {
                "destination": {"9.1": 0.5, "1.1": 0.3, "9999": 0.2},
                "origin": {},
            }
        },
    )

    rows = variation_report.motive_crosswalk(frames_2008, frames_2019, "destination")

    by_entd = {row.entd_code: row for row in rows if row.entd_code}
    assert by_entd["9.91"].emp_code == "9.1"
    assert by_entd["9.91"].share_2008 == pytest.approx(0.6)
    assert by_entd["9.91"].share_2019 == pytest.approx(0.5)
    # 5.59 is outside the step-11 purpose conversion: unmapped.
    assert "unmapped" in by_entd["5.59"].flag
    # 9999 (refusal) exists in 2019; no ENTD code maps to it.
    only_2019 = [row for row in rows if row.flag == "2019 only"]
    assert any(row.emp_code == "9999" for row in only_2019)


def _b2_frames(scale: float, category: str = "employed") -> SurveyFrames:
    n = 60  # above the 50-respondent suppression threshold
    days = {
        "pond_jour": [1.0] * n,
        "trips_per_day": [2.0 * scale] * n,
        "total_distance_km": [6.0 * scale] * n,
        "distance_trips": [2.0 * scale] * n,
        "distance_time_min": [30.0 * scale + (i % 3) for i in range(n)],
        "total_time_min": [30.0 * scale + (i % 3) for i in range(n)],
        "population_category": [category] * n,
        "ident_men": [f"M{i // 2}" for i in range(n)],
    }
    return _frames(days, {})


def test_b2_decompositions_cover_overall_and_categories() -> None:
    frames_a = _b2_frames(1.0)
    frames_b = _b2_frames(1.2)

    rows = variation_report.b2_decompositions(
        frames_a,
        frames_b,
        n_reps=N_REPS,
        seed=0,
        include_time_ratio=True,
    )

    by_group = {row.group: row for row in rows}
    overall = by_group["overall"].result
    assert overall is not None
    point = overall.point
    assert point.delta_min == pytest.approx(
        point.trips_min + point.distance_min + point.speed_min
    )
    assert by_group["employed"].n_a == 60
    assert by_group["employed"].result is not None
    assert by_group["overall"].time_ratio == pytest.approx(37.0 / 31.0)
    assert by_group["overall"].time_ratio_ci90 is not None
    # A category absent from both surveys has no decomposition.
    assert by_group["retired"].result is None

    lines = variation_report._format_b2(
        rows,
        "2008",
        "2019",
        equivalence_margin=0.15,
        secondary_equivalence_margin=0.10,
    )
    text = "\n".join(lines)
    assert "B2. Trips x distance x speed" in text
    assert "Time ratio 2019/2008" in text
    assert "Equivalent at ±15%" in text
    assert "Equivalent at ±10%" in text
    assert "| overall | 60 | 60 |" in text
    employed_line = next(line for line in lines if line.startswith("| employed |"))
    assert len(employed_line.strip("|").split("|")) == 16
    assert "different" in employed_line
    # Absent categories keep their true n with dashes.
    assert "| retired | 0 | 0 | - | - | - | - | - | - |" in text


@pytest.mark.parametrize(
    ("ci", "expected"),
    [
        ((0.95, 1.05), "equivalent"),
        ((1.16, 1.20), "different"),
        ((1.05, 1.16), "inconclusive"),
    ],
)
def test_equivalence_verdict_is_three_state(
    ci: tuple[float, float], expected: str
) -> None:
    assert variation_report._equivalence_verdict(ci, 0.10) == expected


def test_density_grid_comparison_reports_temporal_equivalence() -> None:
    def frames(scale: float) -> SurveyFrames:
        n = 60
        day_ids = np.array([f"d{i}" for i in range(n)])
        days = {
            "day_id": day_ids,
            "pond_jour": np.ones(n),
            "total_time_min": np.full(n, 30.0 * scale),
            "population_category": np.full(n, "employed"),
            "home_density": np.full(n, "dense"),
            "ident_men": np.array([f"M{i // 2}" for i in range(n)]),
        }
        trips = {
            "day_id": day_ids,
            "pond_jour": np.ones(n),
            "duration_min": np.full(n, 30.0 * scale),
            "population_category": np.full(n, "employed"),
            "home_density": np.full(n, "dense"),
        }
        return _frames(days, trips)

    lines = variation_report._density_grid_comparison_lines(
        frames(1.0),
        frames(1.12),
        n_reps=N_REPS,
        seed=0,
        equivalence_margin=0.15,
        secondary_equivalence_margin=0.10,
    )
    text = "\n".join(lines)
    assert "Time ratio 2019/2008" in text
    assert "90% CI" in text
    employed_time = next(
        line
        for line in lines
        if line.startswith("| dense | employed | time/day (min) |")
    )
    assert employed_time.endswith(
        "| 1.120 | [1.120, 1.120] | equivalent | different |"
    ), employed_time


def test_b2_and_pair1_keep_days_with_no_known_distance() -> None:
    a, b = _b2_frames(1.0), _b2_frames(1.2)
    a.days["total_distance_km"][::2] = 0.0
    a.days["distance_trips"][::2] = 0.0
    a.days["distance_time_min"][::2] = 0.0
    b.days["recall_lag"] = np.ones(60)
    b.trips["recall_lag"] = np.array([])
    b.trips["pond_jour"] = np.array([])
    lag1 = variation_report.subset_frames(b, recall_lag=1)
    rows = variation_report.b2_decompositions(
        a, lag1, n_reps=N_REPS, seed=0, categories=()
    )
    result = rows[0].result
    assert result is not None
    assert result.point.time_a_min == pytest.approx(31.0)
    assert result.point.trips_a == pytest.approx(2.0)
    assert result.point.distance_a_km == pytest.approx(3.0)
    assert result.point.distance_share_a == pytest.approx(0.5)
    assert np.isfinite(result.speed_ci).all()
    assert "| overall | 60 | 60 | 31.0 |" in "\n".join(
        variation_report._format_b2(rows, "2008", "2019 (lag 1)")
    )


def _b1_frames(
    time_by_category: dict[str, float], shares: dict[str, int]
) -> SurveyFrames:
    categories = [c for c, n in shares.items() for _ in range(n)]
    days = {
        "pond_jour": [1.0] * len(categories),
        "population_category": categories,
        "total_time_min": [time_by_category[c] for c in categories],
        "age": [40.0] * len(categories),
        "sex": [1.0 if i % 2 else 2.0 for i in range(len(categories))],
        "home_density": ["dense"] * len(categories),
        "is_idf": [False] * len(categories),
        "cars_band": ["1"] * len(categories),
        "ident_men": [f"M{i // 2}" for i in range(len(categories))],
    }
    return _frames(days, {})


def test_b1_composition_identity_and_pure_composition_change() -> None:
    # Same behaviour per category in both groups; only the category mix
    # changes: the composition effect should carry the whole change.
    times = {"employed": 60.0, "retired": 30.0}
    frames_a = _b1_frames(times, {"employed": 40, "retired": 80})
    frames_b = _b1_frames(times, {"employed": 80, "retired": 40})

    row = variation_report.bootstrap_composition(
        frames_a, frames_b, "V1", n_reps=N_REPS, seed=0
    )

    point = row.point
    assert point.composition_min + point.behaviour_min == pytest.approx(
        point.mean_b_min - point.mean_a_min
    )
    assert point.behaviour_min == pytest.approx(0.0, abs=1e-9)
    assert point.composition_min == pytest.approx(point.mean_b_min - point.mean_a_min)
    assert np.isfinite(row.composition_ci).all()

    lines = variation_report._format_b1([row], "A", "B")
    assert any("| V1 |" in line for line in lines)


def test_composition_cells_merge_small_age_bands() -> None:
    n = 40
    days = {
        "pond_jour": [1.0] * n,
        "population_category": ["employed"] * n,
        "total_time_min": [30.0] * n,
        # Ages span two neighbouring bands: 25-34 has n=35, 35-44 n=5
        # (under the 30 threshold): the two bands must merge.
        "age": [30.0] * 35 + [40.0] * 5,
        "sex": [1.0] * n,
        "home_density": ["dense"] * n,
        "is_idf": [False] * n,
        "cars_band": ["1"] * n,
        "ident_men": [f"M{i}" for i in range(n)],
    }
    frames = _frames(days, {})

    cells_a, cells_b = variation_report.composition_pair_cells(frames, frames, "V1")

    assert len(set(cells_a)) == 1  # one merged cell, not two
    assert (cells_a == cells_b).all()


def _trip_frames(
    minutes_by_mode: dict[str, float],
    *,
    trips_per_day: int = 2,
    n_days: int = 60,
    km_per_min: float = 0.3,
) -> SurveyFrames:
    modes = list(minutes_by_mode)
    n_trips = n_days * trips_per_day
    mode7 = [modes[i % len(modes)] for i in range(n_trips)]
    duration = [minutes_by_mode[m] for m in mode7]
    days = {
        "pond_jour": [1.0] * n_days,
        "trips_per_day": [float(trips_per_day)] * n_days,
        "total_time_min": [sum(duration[:trips_per_day])] * n_days,
        "total_distance_km": [km_per_min * sum(duration[:trips_per_day])] * n_days,
        "distance_trips": [float(trips_per_day)] * n_days,
        "distance_time_min": [sum(duration[:trips_per_day])] * n_days,
        "population_category": ["employed"] * n_days,
        "ident_men": [f"M{i // 2}" for i in range(n_days)],
    }
    trips = {
        "pond_jour": [1.0] * n_trips,
        "ident_men": [f"M{(i // trips_per_day) // 2}" for i in range(n_trips)],
        "duration_min": duration,
        "distance_km": [km_per_min * d for d in duration],
        "mode7": mode7,
    }
    return _frames(days, trips)


def test_2019_2008_ratio_is_identical_in_b2_c7_comparison_and_csv(
    tmp_path: Path,
) -> None:
    """Section 9.9: one household interval, including energy-unknown days."""
    import csv

    from mobgrid.budget import daily_energy, emp

    a = _trip_frames({"walk": 15.0, "car_driver": 25.0}, n_days=80)
    b = _trip_frames({"walk": 18.0, "car_driver": 32.0}, n_days=80)
    for index, frames in enumerate((a, b)):
        frames.days["pond_jour"] = np.linspace(1.0, 3.0, 80)
        frames.days["total_time_min"] += np.arange(80) * (0.3 + index * 0.1)
        frames.days["typejour"] = np.ones(80, dtype=int)
        frames.days["day_mode_group"] = np.full(80, "multimodal")
        frames.days["home_density"] = np.full(80, "dense")
        frames.days["income_quintile"] = np.full(80, "q1")
        frames.days["total_energy_kh_kj"] = np.full(80, 100.0)
        frames.days["total_energy_cp_kj"] = np.full(80, 90.0)
        frames.days["total_energy_kh_kj"][:10] = np.nan
        frames.days["total_energy_cp_kj"][:10] = np.nan
        sample = variation_report.PeriodBudgetSample(
            person_household=np.append(frames.days["ident_men"], "immobile"),
            person_weight=np.ones(81),
            day_household=frames.days["ident_men"],
            day_person=np.arange(80).astype(str),
            day_weight=frames.days["pond_jour"],
            day_type=frames.days["typejour"],
            trips=frames.days["trips_per_day"],
            total_time_min=frames.days["total_time_min"],
            time_trips=frames.days["trips_per_day"],
        )
        frames.aux["c7_data"] = dict.fromkeys(("reference", "sdes", "daytable"), sample)
    b2 = variation_report.b2_decompositions(
        a, b, n_reps=200, seed=0, include_time_ratio=True, categories=()
    )[0]
    comparison = emp._temporal_day_ratio_rows(
        {"_weekday_days": a.days}, {"_weekday_days": b.days}, n_reps=200, seed=0
    )[-1]
    c7 = next(
        row
        for row in variation_report._c7_comparison(a, b, n_reps=200, seed=0)
        if row["scope"] == "round-dest-local"
        and row["period"] == "weekday"
        and row["basis"] == "per traveller"
        and row["measure"] == "Minutes/day"
    )
    expected = (b2.time_ratio, b2.time_ratio_ci90)
    assert (comparison.ratio, comparison.ci) == expected
    assert c7["ratio"] == expected
    daytable = next(
        row
        for row in variation_report._c7_comparison(a, b, n_reps=200, seed=0)
        if row["scope"] == "alldays-allpurp-daytable"
        and row["period"] == "weekday"
        and row["basis"] == "per traveller"
        and row["measure"] == "Minutes/day"
    )
    assert daytable["ratio"] == expected
    intervals = emp._comparison_ratio_intervals(
        a.days, b.days, "population_category", "total_time_min", n_reps=200, seed=0
    )
    assert intervals["employed"] == (expected[0], *expected[1])
    stats = [
        daily_energy.ScalarGroupStats(
            "employed", 80, 80.0, 50.0, (40.0, 60.0), 40.0, 50.0, 60.0
        )
    ]
    emp.figstyle.set_context(scope="Reference", survey="2008 vs 2019", days="weekday")
    path = emp._figure_compare_time_by_category(
        stats,
        stats,
        {},
        {},
        tmp_path,
        references_2008={
            "all": (50.0, 50.0),
            "weekday": (50.0, 50.0),
            "person": (None, None),
        },
        references_2019={
            "all": (50.0, 50.0),
            "weekday": (50.0, 50.0),
            "person": (None, None),
        },
        ratio_intervals={("weekday", "employed"): intervals["employed"]},
    )
    with path.with_suffix(".csv").open(encoding="utf-8", newline="") as stream:
        row = next(
            row
            for row in csv.DictReader(stream)
            if row["subgroup"] == "2019/2008" and row["ratio"]
        )
    assert tuple(
        float(row[key]) for key in ("ratio", "ratio_ci_low", "ratio_ci_high")
    ) == (expected[0], *expected[1])


def test_shift_share_identity_and_report_section() -> None:
    frames_a = _trip_frames({"walk": 15.0, "car_driver": 25.0})
    frames_b = _trip_frames({"walk": 18.0, "car_driver": 32.0})

    result = variation_report.shift_share_by(
        frames_a, frames_b, "mode7", n_reps=N_REPS, seed=0
    )

    point = result.point
    assert point.delta_min == pytest.approx(
        point.volume_min + point.mix_min + point.within_min + point.interaction_min
    )
    # Equal mode shares on both sides: the change is all within modes.
    assert point.mix_min == pytest.approx(0.0, abs=1e-9)
    assert point.within_min == pytest.approx(point.delta_min, abs=1e-9)
    by_mode = {term.group: term for term in point.terms}
    assert by_mode["walk"].minutes_per_trip_a == pytest.approx(15.0)
    assert by_mode["walk"].minutes_per_trip_b == pytest.approx(18.0)
    # Within each mode, the km/trip + speed split recovers the within term.
    for term in point.terms:
        assert term.within_km_min + term.within_speed_min == pytest.approx(
            term.within_min
        )

    lines = variation_report._format_shift_share(
        result,
        variation_report._group_counts(frames_a, "mode7"),
        variation_report._group_counts(frames_b, "mode7"),
        title="## B3. Mode shift-share, A -> B",
        group_name="mode",
        label_a="A",
        label_b="B",
        group_order=variation_report.MODE7_LABELS,
    )
    text = "\n".join(lines)
    assert "mode mix" in text
    assert "| walk | 60 | 60 |" in text


def test_b4_distance_band_shift_share_uses_band_labels() -> None:
    frames_a = _trip_frames({"walk": 10.0, "car_driver": 30.0}, km_per_min=0.3)
    frames_b = _trip_frames({"walk": 12.0, "car_driver": 36.0}, km_per_min=0.35)

    result = variation_report.shift_share_by(
        frames_a, frames_b, "distance_band", n_reps=N_REPS, seed=0
    )

    point = result.point
    assert point.delta_min == pytest.approx(
        point.volume_min + point.mix_min + point.within_min + point.interaction_min
    )
    groups = {term.group for term in point.terms}
    assert groups <= set(variation_report.DISTANCE_BAND_LABELS)


def test_missing_distances_do_not_poison_mode_decomposition() -> None:
    a = _trip_frames({"walk": 10.0, "car_driver": 30.0})
    b = _trip_frames({"walk": 12.0, "car_driver": 36.0})
    a.trips["distance_km"][::4] = np.nan
    b.trips["distance_km"][::6] = np.nan
    a.trips["duration_min"][0] = 70.0
    result = variation_report.shift_share_by(a, b, "mode7", n_reps=N_REPS, seed=0)
    for term in result.point.terms:
        assert np.isfinite([term.within_km_min, term.within_speed_min]).all()
        assert term.within_min == pytest.approx(
            term.within_km_min + term.within_speed_min + term.within_selection_min
        )
    walk = next(t for t in result.point.terms if t.group == "walk")
    assert walk.distance_share_a == pytest.approx(0.5)
    assert walk.distance_share_b == pytest.approx(2 / 3)
    assert walk.within_selection_min != pytest.approx(0.0)


def test_distance_bands_separate_missing_and_sort_figure_numerically() -> None:
    import matplotlib.pyplot as plt

    frames = _trip_frames({"walk": 10.0, "car_driver": 30.0})
    frames.trips["distance_km"][:5] = [np.nan, 0.5, 3.0, 15.0, 90.0]
    counts = variation_report._group_counts(frames, "distance_band")
    assert counts["unknown distance"] == 1
    assert counts[">=80 km"] == 1
    result = variation_report.shift_share_by(
        frames, frames, "distance_band", n_reps=N_REPS, seed=0
    )
    fig, ax = plt.subplots()
    variation_report._shift_share_panel(ax, result, "by distance band")
    labels = [t.get_text() for t in ax.get_xticklabels()]
    plt.close(fig)
    order = variation_report.DISTANCE_BAND_LABELS
    assert labels == [label for label in order if label in labels]


def test_frame_aggregation_keeps_missing_distance_days() -> None:
    """Section 9.9: N/T include all trips, L/v only distance-known trips."""
    with duckdb.connect() as con:
        con.sql("""
            CREATE TABLE trip_legs AS SELECT
                day_id, ident_dep, num_dep, distance_km, duration_min,
                day_id AS ident_ind, day_id AS ident_men,
                CASE WHEN day_id = 'a' THEN 1.0 ELSE 3.0 END AS pond_jour,
                'employed' AS population_category, 'dense' AS residence_density,
                'q1' AS income_quintile, 40 AS age, 'walk' AS mode_group,
                2 AS motive, 1 AS typejour, 1 AS mobloc
            FROM (VALUES ('a', 'd1', 1, 6.0, 10.0),
                         ('a', 'd2', 2, NULL, 30.0),
                         ('b', 'd3', 1, NULL, 20.0))
                v(day_id, ident_dep, num_dep, distance_km, duration_min);
            CREATE TABLE scope_trips AS SELECT day_id, num_dep,
                TRUE AS is_round, TRUE AS is_destination, 1 AS mobloc
                FROM trip_legs;
            CREATE VIEW vr_person AS SELECT DISTINCT ident_ind, 1 AS sex,
                1 AS recall_lag, 'lundi' AS described_weekday_name,
                'janvier' AS described_month_name, FALSE AS is_idf,
                '1' AS cars_band, '11' AS residence_aa_class FROM trip_legs;
            CREATE VIEW vr_trip_ext AS SELECT ident_dep,
                NULL::DOUBLE AS crow_fly_km, NULL::DOUBLE AS declared_km,
                0 AS vac_scol FROM trip_legs;
        """)
        variation_report._create_frames_tables(
            con,
            sample_pct=None,
            selected_scope=scope.Scope.parse("alldays-allpurp-daytable"),
        )
        frames = SurveyFrames(
            "synthetic",
            {
                k: variation_report._plain_array(v)
                for k, v in con.sql("SELECT * FROM vr_days ORDER BY day_id")
                .fetchnumpy()
                .items()
            },
            {},
            {},
        )
    days = variation_report.person_days_from_frames(frames)
    assert days.trips == pytest.approx([2.0, 1.0])
    assert days.time_min == pytest.approx([40.0, 20.0])
    assert days.distance_km == pytest.approx([6.0, 0.0])
    assert days.distance_trips == pytest.approx([1.0, 0.0])
    assert days.distance_time_min == pytest.approx([10.0, 0.0])


def test_b4_duration_tables_are_weighted_and_cover_both_years() -> None:
    frames = _frames(
        {},
        {
            "pond_jour": [1.0, 3.0, 1.0, 1.0],
            "duration_min": [10.0, 20.0, 30.0, 80.0],
            "distance_km": [90.0, 90.0, 90.0, np.nan],
            "mode7": ["train", "train", "train", "train"],
        },
    )
    rows = variation_report.distance_duration_table(frames)
    band = next(r for r in rows if r.label == ">=80 km" and r.mode == "all modes")
    assert band.n_trips == 3
    assert band.quartiles == pytest.approx((20.0, 20.0, 20.0))
    mode = next(r for r in rows if r.label == ">=80 km" and r.mode == "train")
    assert mode.quartiles == band.quartiles
    text = "\n".join(variation_report._format_b4_durations(frames, frames))
    assert "median min/trip 2008" in text
    assert "median min/trip 2019" in text
    assert "Q1 2008" in text and "Q3 2019" in text
    a = _frames({}, {k: np.tile(v, 60) for k, v in frames.trips.items()})
    b = _frames({}, {k: v.copy() for k, v in a.trips.items()})
    b.trips["duration_min"] += 10.0
    text = "\n".join(variation_report._format_b4_durations(a, b))
    assert "| >=80 km | 180 | 20.0 | 180 | 30.0 |" in text
    assert "| train | 180 | 20.0 | 20.0 | 20.0 | 180 | 30.0 | 30.0 | 30.0 |" in text


def test_waterfall_closes_with_zero_net_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    a = _b1_frames({"employed": 60.0, "retired": 30.0}, {"employed": 60, "retired": 60})
    b = _b1_frames({"employed": 50.0, "retired": 30.0}, {"employed": 90, "retired": 30})
    for frames in (a, b):
        frames.days["trips_per_day"] = np.full(120, 2.0)
        frames.days["total_distance_km"] = np.full(120, 6.0)
        frames.days["distance_trips"] = np.full(120, 2.0)
        frames.days["distance_time_min"] = frames.days["total_time_min"].copy()
    b2 = variation_report.b2_decompositions(a, b, n_reps=N_REPS, seed=0, categories=())
    b1 = variation_report.bootstrap_composition(a, b, "V2", n_reps=N_REPS, seed=0)
    assert b1.point.composition_min != 0
    figures = []
    savefig = Figure.savefig

    def capture(fig, *args, **kwargs):
        figures.append(fig)
        return savefig(fig, *args, **kwargs)

    monkeypatch.setattr(Figure, "savefig", capture)
    path = variation_report._figure_b7_waterfall(
        {"b2_rows": b2, "b1_rows": [b1]}, tmp_path
    )
    assert path is not None and path.is_file()
    bars = figures[0].axes[0].patches
    assert bars[0].get_height() == pytest.approx(45.0)
    assert sum(bar.get_height() for bar in bars[1:-1]) == pytest.approx(0.0)
    assert [bar.get_height() for bar in bars[2:6]] == pytest.approx(
        [
            b2[0].result.point.trips_min,
            b2[0].result.point.distance_min,
            b2[0].result.point.speed_min,
            b2[0].result.point.selection_min,
        ]
    )
    assert figures[0].axes[0].get_xticklabels()[1].get_text() == "composition (V2)"
    assert figures[0].axes[0].get_xticklabels()[-2].get_text() == (
        "non-additive residual"
    )
    assert "B7a" in figures[0].axes[0].get_title()
    fig = figures[0]
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    title_box = fig.axes[0].title.get_window_extent(canvas.get_renderer())
    assert fig.bbox.contains(title_box.x0, title_box.y0)
    assert fig.bbox.contains(title_box.x1, title_box.y1)
    assert "\n" in fig.axes[0].get_title()
    assert bars[-2].get_y() + bars[-2].get_height() == pytest.approx(
        bars[-1].get_height()
    )


def test_motive_group_label_maps_codes_and_unknown() -> None:
    assert variation_report.motive_group_label("2") == "shopping"
    assert variation_report.motive_group_label("9") == "professional"
    assert variation_report.motive_group_label("unknown") == "unknown"
    assert variation_report.motive_group_label(None) == "unknown"


def test_b5_tail_stats_median_trim_and_contributions() -> None:
    days = {
        "pond_jour": [1.0, 1.0, 1.0, 1.0],
        "total_time_min": [20.0, 40.0, 60.0, 200.0],
    }
    trips = {
        "pond_jour": [1.0, 1.0, 1.0],
        "duration_min": [30.0, 50.0, 120.0],
        "distance_km": [5.0, 25.0, 45.0],
    }
    frames = _frames(days, trips)

    stats = variation_report.b5_tail_stats(frames)

    assert stats.mean_min == pytest.approx(80.0)
    assert stats.median_min == pytest.approx(40.0)
    # Top 2.5% of weight trims 0.1 units of the 200-min day:
    # (20 + 40 + 60 + 0.9 x 200) / 3.9.
    assert stats.trimmed_2_5pct_min == pytest.approx((120.0 + 180.0) / 3.9)
    assert stats.over_180_min == pytest.approx(200.0 / 4.0)
    assert stats.trips_over_20km_min == pytest.approx((50.0 + 120.0) / 4.0)
    assert stats.trips_over_40km_min == pytest.approx(120.0 / 4.0)

    lines = variation_report._format_b5(stats, stats, "A", "B")
    text = "\n".join(lines)
    assert "B5. Tails" in text
    assert "| Median (min/day) | 40.0 | 40.0 | 0.0 |" in text


def test_subset_frames_filters_days_and_trips() -> None:
    frames = _trip_frames({"walk": 15.0, "car_driver": 25.0})
    frames.days["income_quintile"] = np.array(
        ["q1" if i % 2 else "q5" for i in range(len(frames.days["pond_jour"]))]
    )
    frames.trips["income_quintile"] = np.array(
        ["q1" if (i // 2) % 2 else "q5" for i in range(len(frames.trips["pond_jour"]))]
    )

    subset = variation_report.subset_frames(frames, income_quintile="q1")

    assert (subset.days["income_quintile"] == "q1").all()
    assert (subset.trips["income_quintile"] == "q1").all()
    assert len(subset.days["pond_jour"]) == 30


def test_comparison_pair_runs_b2_b3_b1_between_two_groups() -> None:
    frames_a = _b1_frames({"employed": 40.0}, {"employed": 60})
    frames_a.days["trips_per_day"] = np.full(60, 2.0)
    frames_a.days["total_distance_km"] = np.full(60, 8.0)
    frames_a.days["distance_trips"] = np.full(60, 2.0)
    frames_a.days["distance_time_min"] = np.full(60, 40.0)
    frames_a.trips = {
        "pond_jour": np.ones(120),
        "ident_men": np.repeat(frames_a.days["ident_men"], 2),
        "duration_min": np.full(120, 20.0),
        "distance_km": np.full(120, 4.0),
        "mode7": np.array(["walk", "car_driver"] * 60),
    }
    frames_b = _b1_frames({"employed": 50.0}, {"employed": 60})
    frames_b.days["trips_per_day"] = np.full(60, 2.0)
    frames_b.days["total_distance_km"] = np.full(60, 9.0)
    frames_b.days["distance_trips"] = np.full(60, 2.0)
    frames_b.days["distance_time_min"] = np.full(60, 50.0)
    frames_b.trips = {
        "pond_jour": np.ones(120),
        "ident_men": np.repeat(frames_b.days["ident_men"], 2),
        "duration_min": np.full(120, 25.0),
        "distance_km": np.full(120, 4.5),
        "mode7": np.array(["walk", "car_driver"] * 60),
    }

    pair = variation_report.comparison_pair(
        "employed", frames_a, frames_b, variants=("V1",), n_reps=N_REPS, seed=0
    )

    assert pair.b2.result is not None
    assert pair.b2.result.point.delta_min == pytest.approx(10.0)
    assert pair.b3 is not None
    assert pair.b3.point.delta_min == pytest.approx(10.0)
    assert len(pair.b1) == 1

    lines = variation_report._format_pair_results(
        [pair],
        title="## B6.2 test",
        intro="intro",
        label_a="A",
        label_b="B",
    )
    text = "\n".join(lines)
    assert "| employed | 60 | 60 |" in text
    assert "Mode shift-share aggregates" in text


def test_pair4_tables_suppress_small_cells() -> None:
    n = 120
    days = {
        "pond_jour": [1.0] * n,
        "population_category": ["employed"] * n,
        "total_time_min": [60.0 + (i % 5) for i in range(n)],
        "home_density": ["dense"] * (n // 2) + ["intermediate"] * (n // 2),
        "income_quintile": ["q1" if i % 2 else "q5" for i in range(n)],
        "is_idf": [i < 10 for i in range(n)],
        "ident_men": [f"M{i}" for i in range(n)],
    }
    frames = _frames(days, {})
    frames.name = "EMP 2019"

    lines = variation_report.pair4_tables(frames, "employed", n_reps=N_REPS, seed=0)
    text = "\n".join(lines)

    assert "### EMP 2019, employed" in text
    # 30 days per density x quintile cell: suppressed under 50.
    assert "n=30: -" in text
    # Île-de-France has only 10 employed days in total: suppressed.
    assert "n=0: -" in text or "n=5: -" in text
    # The other-regions q1/q5 cells have 55 each: shown.
    assert "n=55:" in text


def test_duration_rounding_table_counts_multiples() -> None:
    trips = {
        "pond_jour": [1.0] * 4,
        "duration_min": [5.0, 10.0, 12.0, 30.0],
        "mode7": ["walk"] * 4,
        "distance_km": [1.0] * 4,
    }
    frames = _frames({}, trips)

    rows = {r.mode: r for r in variation_report.duration_rounding_table(frames)}

    walk = rows["walk"]
    assert walk.n_trips == 4
    assert walk.share_mult_5 == pytest.approx(0.75)
    assert walk.share_mult_10 == pytest.approx(0.5)
    assert walk.share_mult_15 == pytest.approx(0.25)  # only the 30-min trip
    assert walk.share_mult_30 == pytest.approx(0.25)
    assert rows["all modes"].n_trips == 4
    assert rows["bike"].n_trips == 0


def test_calendar_mix_reads_french_month_and_weekday_names() -> None:
    days = {
        "pond_jour": [1.0, 1.0, 2.0],
        "described_month_name": ["janvier", "septembre", "septembre"],
        "described_weekday_name": ["lundi", "vendredi", "lundi"],
        "vac_scol": [0.0, 1.0, 0.0],
    }
    frames = _frames(days, {})

    mix = variation_report.calendar_mix(frames)

    assert mix.month_share[1] == pytest.approx(0.25)
    assert mix.month_share[9] == pytest.approx(0.75)
    assert mix.weekday_share[1] == pytest.approx(0.75)
    assert mix.weekday_share[5] == pytest.approx(0.25)
    assert mix.holiday_share == pytest.approx(0.25)
    assert mix.n_unknown_month == 0


def test_distance_band_table_shares_sum_to_one() -> None:
    frames = _frames(
        {},
        {
            "pond_jour": [1.0, 1.0, 2.0, 1.0],
            "duration_min": [10.0, 20.0, 30.0, 60.0],
            "distance_km": [0.5, 3.0, 15.0, 90.0],
        },
    )

    rows = variation_report.distance_band_table(frames)

    assert sum(row.share_trips for row in rows) == pytest.approx(1.0)
    assert sum(row.share_time for row in rows) == pytest.approx(1.0)
    by_label = {row.label: row for row in rows}
    assert by_label["0-1 km"].n_trips == 1
    assert by_label["2-5 km"].n_trips == 1
    assert by_label["10-20 km"].n_trips == 1
    assert by_label[">=80 km"].n_trips == 1
    assert by_label["10-20 km"].share_trips == pytest.approx(0.4)


def test_b7_figures_write_png_and_csv_sidecars(tmp_path: Path) -> None:
    point = SimpleNamespace(
        time_a_min=45.0,
        time_b_min=50.0,
        delta_min=5.0,
        trips_min=3.0,
        distance_min=1.0,
        speed_min=0.5,
        selection_min=0.5,
    )
    term = SimpleNamespace(
        group="walk",
        mix_min=0.5,
        within_min=1.0,
        interaction_min=0.25,
    )
    figures = [
        variation_report._figure_b7_waterfall(
            {
                "b2_rows": [SimpleNamespace(result=SimpleNamespace(point=point))],
                "b1_rows": [
                    SimpleNamespace(
                        variant="V2",
                        point=SimpleNamespace(composition_min=0.5),
                    )
                ],
            },
            tmp_path,
        ),
        variation_report._figure_b7_shift_share(
            {
                key: SimpleNamespace(point=SimpleNamespace(terms=(term,)))
                for key in ("b3_mode", "b4_motive", "b4_distance")
            },
            tmp_path,
        ),
        variation_report._figure_b7_recall_lag(
            {
                "lag_table": [
                    SimpleNamespace(
                        label="1",
                        time_per_day_min=55.0,
                        trips_per_day=2.0,
                        minutes_per_trip=27.5,
                    )
                ],
                "entd_overall": SimpleNamespace(
                    time_per_day_min=45.0,
                    trips_per_day=1.8,
                    minutes_per_trip=25.0,
                ),
            },
            tmp_path,
        ),
    ]

    for path in figures:
        assert path is not None and path.is_file()
        with path.with_suffix(".csv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            assert reader.fieldnames == list(figstyle.CSV_COLUMNS)
            assert next(reader, None) is not None


def test_cli_forwards_options_and_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI forwards options and writes its report without a costly data run."""
    calls = {}
    out_dir = tmp_path / "step12_variation"
    expected_figures = [
        out_dir / "waterfall.png",
        out_dir / "shift_share.png",
        out_dir / "recall_lag.png",
    ]

    def fake_run(path, config_path, **kwargs):
        path.mkdir(parents=True, exist_ok=True)
        calls["run"] = (path, config_path, kwargs)
        return {"figures": expected_figures}

    def fake_write_markdown(md_path, report_out_dir, results):
        calls["write_markdown"] = (md_path, report_out_dir, results)
        md_path.write_text("synthetic step-12 report", encoding="utf-8")

    monkeypatch.setattr(variation_report, "run", fake_run)
    monkeypatch.setattr(variation_report, "write_markdown", fake_write_markdown)
    exit_code = variation_report.main(
        [
            "--out",
            str(out_dir),
            "--scope",
            scope.REFERENCE_SCOPE.id,
            "--emp2019-data-path",
            str(tmp_path / "emp2019.zip"),
            "--entd2008-data-path",
            str(tmp_path / "entd2008"),
            "--entd2008-zoning-data-path",
            str(tmp_path / "entd2008_zoning"),
            "--config",
            str(CONFIG_PATH),
            "--bootstrap-reps",
            str(CLI_N_REPS),
            "--sample-households",
            "100",
        ]
    )

    assert exit_code == 0
    md_path = out_dir.with_suffix(".md")
    assert md_path.read_text(encoding="utf-8") == "synthetic step-12 report"
    run_path, config_path, kwargs = calls["run"]
    assert run_path == out_dir
    assert config_path == CONFIG_PATH
    assert kwargs == {
        "n_reps": CLI_N_REPS,
        "seed": 0,
        "emp2019_data_path": tmp_path / "emp2019.zip",
        "entd2008_data_path": tmp_path / "entd2008",
        "entd2008_zoning_data_path": tmp_path / "entd2008_zoning",
        "sample_pct": 100.0,
        "scope": scope.REFERENCE_SCOPE,
    }
    assert calls["write_markdown"] == (md_path, out_dir, {"figures": expected_figures})
    assert "3 figures" in capsys.readouterr().out


def _measurement_frames(durations: list[float]) -> SurveyFrames:
    n = len(durations)
    return _frames(
        {
            "day_id": [f"d{i}" for i in range(n)],
            "ident_men": [f"h{i // 2}" for i in range(n)],
            "pond_jour": [1.0] * n,
            "population_category": ["employed"] * n,
            "trips_per_day": [1.0] * n,
            "total_time_min": durations,
            "total_distance_km": [99.0] * n,
            "distance_trips": [1.0] * n,
            "distance_time_min": durations,
        },
        {
            "day_id": [f"d{i}" for i in range(n)],
            "ident_men": [f"h{i // 2}" for i in range(n)],
            "pond_jour": [1.0] * n,
            "population_category": ["employed"] * n,
            "duration_min": durations,
            "distance_km": [99.0] * n,
            "declared_km": [2.0] * n,
            "crow_fly_km": [0.5] * n,
            "mode7": ["walk"] * n,
            "motive_group": ["2"] * n,
        },
    )


def _measurement_config() -> variation_report.variation.MeasurementConfig:
    return variation_report.variation.load_variation_config(
        ROOT / "config" / "variation.yaml"
    ).measurement


def _ledger_frames(
    specs: list[tuple[str, str, float, list[float]]],
) -> SurveyFrames:
    """Section 9.9: each household repeats the full calendar/lag design."""
    days: dict[str, list] = {}
    trips: dict[str, list] = {}
    for household in range(60):
        for day, (month, weekday, lag, durations) in enumerate(specs):
            shared = {
                "day_id": f"{household}-{day}",
                "ident_men": f"h{household}",
                "pond_jour": 1.0,
                "population_category": "employed",
                "age": 35.0,
                "sex": 1.0,
                "home_density": "dense",
                "is_idf": False,
                "cars_band": "1",
                "described_month_name": month,
                "described_weekday_name": weekday,
                "recall_lag": lag,
            }
            for key, value in {
                **shared,
                "total_time_min": sum(durations),
                "trips_per_day": len(durations),
                "total_distance_km": len(durations) * 2.0,
                "distance_trips": len(durations),
                "distance_time_min": sum(durations),
            }.items():
                days.setdefault(key, []).append(value)
            for duration in durations:
                for key, value in {
                    **shared,
                    "duration_min": duration,
                    "distance_km": 2.0,
                    "crow_fly_km": 0.0 if duration < 5 else 1.0,
                    "mode7": "walk",
                    "motive_group": "2",
                }.items():
                    trips.setdefault(key, []).append(value)
    return _frames(days, trips)


def _ledger_inputs(*, trips_2019: int = 1) -> tuple[SurveyFrames, SurveyFrames, dict]:
    a = _ledger_frames(
        [("janvier", "lundi", 1.0, [2.0, 18.0])] * 3
        + [("février", "vendredi", 1.0, [2.0, 18.0])]
    )
    specs = [
        ("janvier", "lundi", 1.0, [20.0] * trips_2019),
        ("janvier", "vendredi", 2.0, [30.0] * trips_2019),
        ("février", "lundi", 4.0, [40.0] * trips_2019),
        ("février", "vendredi", float("nan"), [50.0] * trips_2019),
    ]
    b = _ledger_frames(specs)
    config = _measurement_config()
    ca = variation_report.common_distance_frames(a, "crow_fly_km")
    cb = variation_report.common_distance_frames(b, "crow_fly_km")
    results = {
        "lag_table": variation_report.recall_lag_table(b),
        "entd_overall": variation_report.survey_overall_row(a, "ENTD 2008"),
        "rounding_checks": {
            "changes": {
                "nearest": {"overall": [1.0, 2.0]},
                "up": {"overall": [3.0, 4.0]},
                "nearest_min5": {"overall": [999.0]},
            }
        },
        "motive_rates": variation_report.motive_rate_checks(
            a, b, config=config, n_reps=N_REPS, seed=0
        ),
        "b2_rows": variation_report.b2_decompositions(
            ca, cb, n_reps=N_REPS, seed=0, categories=()
        ),
        "b2_rows_corrected": variation_report.b2_decompositions(
            a, b, n_reps=N_REPS, seed=0, categories=()
        ),
        "b1_rows": [
            variation_report.bootstrap_composition(a, b, "V2", n_reps=N_REPS, seed=0)
        ],
    }
    results["b1_rows"] = [
        replace(
            results["b1_rows"][0],
            ledger_effect=np.array([2.0, 0.5, 1.0]),
            ledger_bounds=np.array([[1.0, 3.0], [0.2, 0.8], [0.5, 1.5]]),
        )
    ]
    return a, b, results


def test_measurement_ledger_reuses_results_and_preserves_effect_signs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C4: cached sections, ratio-of-totals, and signed short-trip restoration."""
    a, b, results = _ledger_inputs()

    def recomputation(*args, **kwargs):
        pytest.fail("C4 must reuse the existing section estimates")

    for name in (
        "rounding_checks",
        "recall_lag_table",
        "survey_overall_row",
        "motive_rate_checks",
        "b2_decompositions",
        "bootstrap_composition",
    ):
        monkeypatch.setattr(variation_report, name, recomputation)
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    rows = {row.key: row for row in ledger.rows}
    assert tuple(rows) == tuple("abdefg")
    assert ledger.observed == pytest.approx([15.0, -1.0, 25.0])
    np.testing.assert_allclose(rows["a"].bounds, [[1.0, 4.0], [0, 0], [0.5, 2.0]])
    assert rows["b"].effect == pytest.approx([10.0, 0.0, 10.0])
    assert rows["d"].effect == pytest.approx([0.0, 0.0, 0.0])
    assert "decomposition only" in rows["d"].note
    assert rows["e"].effect == pytest.approx([-2.0, -1.0, 16.5])
    assert rows["f"].effect == pytest.approx([7.5, 0.0, 7.5])
    assert rows["g"].effect == pytest.approx([2.0, 0.5, 1.0])
    np.testing.assert_allclose(
        ledger.residual_bounds,
        [[-4.5, -1.5], [0.0, 0.0], [-11.0, -9.5]],
        atol=1e-10,
    )
    np.testing.assert_allclose(
        ledger.residual_bounds_with_composition,
        [[-7.5, -2.5], [-0.8, -0.2], [-12.5, -10.0]],
        atol=1e-10,
    )
    text = "\n".join(variation_report._format_measurement_ledger(ledger))
    assert "### C4. Measurement ledger" in text
    assert "Residual change" in text
    assert "removing a, b, e, f" in text
    assert "also removing g, composition" in text
    assert "positive effect" in text
    assert "restoration" in text
    assert "100.0%" in text
    assert "intra-commune" in text
    assert "not a confidence interval" in text


def test_measurement_ledger_calendar_requires_joint_cell_support() -> None:
    """C4f: no pooling weekday/month margins or hiding unmatched target cells."""
    a, b, results = _ledger_inputs()
    a.days["described_month_name"][:] = "mars"
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    calendar = next(row for row in ledger.rows if row.key == "f")
    assert np.isnan(calendar.effect).all()
    assert "unmatched" in calendar.note.lower()
    assert np.isnan(ledger.residual_bounds).all()
    assert "unavailable" in "\n".join(
        variation_report._format_measurement_ledger(ledger)
    )


def test_measurement_ledger_suppresses_small_cells() -> None:
    a, b, results = _ledger_inputs()
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    from dataclasses import replace

    small = replace(
        ledger,
        n=49,
        rows=tuple(replace(row, n=49) for row in ledger.rows),
    )
    text = "\n".join(variation_report._format_measurement_ledger(small))
    assert "| a. Duration rounding | - | - | - | - | - | C1 |" in text
    assert "| Observed change | - | - | - |" in text
    assert "100.0%" not in text


def test_measurement_ledger_reports_zero_total_trip_change_share_as_undefined() -> None:
    a, b, results = _ledger_inputs(trips_2019=2)
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    assert ledger.observed[1] == 0.0
    assert "undefined (zero total trip change)" in "\n".join(ledger.diagnostics)


def test_measurement_ledger_uses_joint_calendar_not_separate_margins() -> None:
    a, b, results = _ledger_inputs()
    # Both samples now have 50/50 weekday and month margins. Only the
    # joint-cell mix differs: a has just Monday/Jan and Friday/Feb.
    a.days["described_month_name"] = np.tile(
        ["janvier", "janvier", "février", "février"], 60
    )
    a.days["described_weekday_name"] = np.tile(
        ["lundi", "lundi", "vendredi", "vendredi"], 60
    )
    # Make the middle cells contribute a different mean from the diagonal.
    b.days["total_time_min"] = np.tile([20.0, 100.0, 100.0, 50.0], 60)
    b.trips["duration_min"] = b.days["total_time_min"].copy()
    results["lag_table"] = variation_report.recall_lag_table(b)
    results["motive_rates"] = variation_report.motive_rate_checks(
        a, b, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    calendar = next(row for row in ledger.rows if row.key == "f")
    assert calendar.effect == pytest.approx([32.5, 0.0, 32.5])
    assert calendar.bounds[:, 0] == pytest.approx(calendar.effect)
    assert calendar.bounds[:, 1] == pytest.approx(calendar.effect)


def test_measurement_ledger_recall_uses_paired_household_draws() -> None:
    a, b, results = _ledger_inputs()
    b.days["recall_lag"][:] = 1.0
    b.trips["recall_lag"][:] = 1.0
    # Household-specific outcomes make unpaired resampling visibly incorrect.
    b.days["total_time_min"] += np.repeat(np.arange(60), 4)
    b.trips["duration_min"] = b.days["total_time_min"].copy()
    results["lag_table"] = variation_report.recall_lag_table(b)
    results["motive_rates"] = variation_report.motive_rate_checks(
        a, b, config=_measurement_config(), n_reps=20, seed=0
    )
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=20, seed=0
    )
    recall = next(row for row in ledger.rows if row.key == "b")
    assert recall.effect == pytest.approx(np.zeros(3), abs=1e-10)
    np.testing.assert_allclose(recall.bounds, np.zeros((3, 2)), atol=1e-10)


def test_ledger_minutes_per_trip_is_ratio_of_weighted_totals() -> None:
    frames = _ledger_frames(
        [
            ("janvier", "lundi", 1.0, [10.0]),
            ("janvier", "mardi", 1.0, [20.0, 20.0, 20.0]),
        ]
    )
    frames.days["pond_jour"][1::2] = 3.0
    frames.trips["pond_jour"] = np.tile([1.0, 3.0, 3.0, 3.0], 60)
    rates = variation_report.motive_rate_checks(
        frames, frames, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    point, reps = variation_report._ledger_metrics(rates, "b")
    assert point == pytest.approx([47.5, 2.5, 19.0])
    assert reps[:, 2] == pytest.approx(np.full(N_REPS, 19.0))


def test_b1_v2_collects_trip_effects_without_another_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    a = _b1_frames({"employed": 60.0, "retired": 30.0}, {"employed": 40, "retired": 80})
    b = _b1_frames({"employed": 60.0, "retired": 30.0}, {"employed": 80, "retired": 40})
    for frames in (a, b):
        frames.days["trips_per_day"] = np.where(
            frames.days["population_category"] == "employed", 3.0, 1.0
        )
    draws = []
    multipliers = variation_report.variation.household_multipliers

    def counting_draws(households, rng):
        draws.append(households)
        return multipliers(households, rng)

    monkeypatch.setattr(
        variation_report.variation, "household_multipliers", counting_draws
    )
    result = variation_report.bootstrap_composition(a, b, "V2", n_reps=N_REPS, seed=0)
    assert len(draws) == 2 * N_REPS
    assert result.ledger_effect == pytest.approx([10.0, 2 / 3, 150 / 7 - 24])
    assert result.ledger_bounds is not None
    assert result.ledger_bounds[0] == pytest.approx(result.composition_ci)


def test_measurement_ledger_does_not_invent_duration_when_no_2008_short_trips() -> None:
    a, b, results = _ledger_inputs()
    a.trips["duration_min"] = np.tile([5.0, 15.0], len(a.days["pond_jour"]))
    b.trips["duration_min"][:] = 2.0
    b.days["total_time_min"][:] = 2.0
    results["lag_table"] = variation_report.recall_lag_table(b)
    results["motive_rates"] = variation_report.motive_rate_checks(
        a, b, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    short = next(row for row in ledger.rows if row.key == "e")
    assert np.isnan(short.effect[0]) and np.isnan(short.effect[2])
    assert "unavailable" in short.note
    text = "\n".join(variation_report._format_measurement_ledger(ledger))
    assert "| Residual (removing a, b, e, f) | - | - | - |" in text
    assert "| Residual (also removing g, composition) | - | - | - |" in text
    assert "nan" not in text


def test_measurement_ledger_no_short_trips_requires_no_restoration() -> None:
    a, b, results = _ledger_inputs()
    a.trips["duration_min"] = np.tile([5.0, 15.0], len(a.days["pond_jour"]))
    results["motive_rates"] = variation_report.motive_rate_checks(
        a, b, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    short = next(row for row in ledger.rows if row.key == "e")
    assert short.effect == pytest.approx(np.zeros(3))
    np.testing.assert_allclose(short.bounds, np.zeros((3, 2)))
    assert short.km_effect == pytest.approx(np.zeros(2))
    np.testing.assert_allclose(short.km_bounds, np.zeros((2, 2)))


def test_measurement_ledger_km_column_restores_short_trips_at_2008_distance() -> None:
    """C4e km/trip: restoring 1 short trip/day with producer km 2.0 and
    crow-fly km 0.0 onto 2019's single 2-km (producer) / 1-km (crow-fly)
    trip leaves producer km/trip unchanged and halves crow-fly km/trip."""
    a, b, results = _ledger_inputs()
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    rows = {row.key: row for row in ledger.rows}
    assert all(row.km_effect is None for key, row in rows.items() if key != "e")
    assert rows["e"].km_effect == pytest.approx([0.0, 0.5])
    # Every synthetic household is identical, so the paired household
    # replicates equal the point effects exactly.
    np.testing.assert_allclose(
        rows["e"].km_bounds, [[0.0, 0.0], [0.5, 0.5]], atol=1e-12
    )
    text = "\n".join(variation_report._format_measurement_ledger(ledger))
    assert "Effect on km/trip change (producer; crow-fly)" in text
    e_line = next(line for line in text.splitlines() if line.startswith("| e."))
    assert "0.000 [0.000, 0.000]; 0.500 [0.500, 0.500]" in e_line
    a_line = next(line for line in text.splitlines() if line.startswith("| a."))
    assert "| - |" in a_line
    csv_rows = variation_report._ledger_km_csv_rows(ledger)
    assert [row["measure"] for row in csv_rows] == ["producer", "crow-fly"]
    assert csv_rows[1]["effect_km_per_trip"] == pytest.approx(0.5)
    suppressed = variation_report._ledger_km_csv_rows(
        replace(ledger, rows=tuple(replace(row, n=49) for row in ledger.rows))
    )
    assert suppressed[0]["n"] == 49
    assert suppressed[0]["effect_km_per_trip"] == ""


def test_measurement_ledger_does_not_leak_a_suppressed_recall_effect() -> None:
    from dataclasses import replace

    a, b, results = _ledger_inputs()
    ledger = variation_report.measurement_ledger(
        a, b, results, config=_measurement_config(), n_reps=N_REPS, seed=0
    )
    ledger = replace(
        ledger,
        rows=tuple(
            replace(row, n=49) if row.key == "b" else row for row in ledger.rows
        ),
    )
    text = "\n".join(variation_report._format_measurement_ledger(ledger))
    assert "| b. Recall lag | - | - | - | - | - | A1 |" in text
    assert "| Residual (removing a, b, e, f) | - | - | - |" in text
    assert "| Residual (also removing g, composition) | - | - | - |" in text


@pytest.mark.parametrize(
    ("variant", "expected"), [("nearest", 0.0), ("up", 5.0), ("nearest_min5", 5.0)]
)
def test_rounding_variants_keep_original_classes_and_never_refine(
    variant: str, expected: float
) -> None:
    """Section 9.9 / C1: fixed cells, increasing cumulative rounding levels."""
    config = _measurement_config()
    a = _measurement_frames([2.0, 3.0, 5.0, 30.0])
    b = _measurement_frames([5.0, 5.0, 5.0, 30.0])
    # Put 2-min and 5-min durations in the same class to exercise the floor.
    config = config.model_copy(update={"duration_upper_min": (10.0, 15.0, 30.0, 60.0)})
    result = variation_report.simulate_rounding(
        a, b, variant, config=config, rng=np.random.default_rng(7)
    )
    assert result[0] == expected
    assert result[2:] == pytest.approx([5.0, 30.0])
    assert np.all(
        variation_report.rounding_level(result, config.rounding_levels)
        >= variation_report.rounding_level(
            a.trips["duration_min"], config.rounding_levels
        )
    )
    assert a.trips["duration_min"] == pytest.approx([2.0, 3.0, 5.0, 30.0])


def test_rounding_uses_weighted_cumulative_gap_probability() -> None:
    config = _measurement_config()
    a = _measurement_frames([11.0, 12.0, 13.0, 10.0])
    b = _measurement_frames([10.0, 10.0, 11.0, 12.0])
    a.trips["pond_jour"] = np.array([1.0, 1.0, 2.0, 4.0])

    class FixedDraws:
        def random(self, size):
            return np.full(size, 0.1)

    # Weighted current share 1/2 already equals the target: no coarsening.
    result = variation_report.simulate_rounding(
        a, b, "nearest", config=config, rng=FixedDraws()
    )
    assert result == pytest.approx([11.0, 12.0, 13.0, 10.0])
    a.trips["pond_jour"] = np.ones(4)
    # p = (.5 - .25) / .75 = 1/3, hence all fixed .1 draws coarsen.
    result = variation_report.simulate_rounding(
        a, b, "nearest", config=config, rng=FixedDraws()
    )
    assert result == pytest.approx([10.0, 10.0, 15.0, 10.0])


def test_rounding_draws_report_daily_changes_and_achieved_shares() -> None:
    a = _measurement_frames([11.0] * 60)
    b = _measurement_frames([10.0] * 60)
    result = variation_report.rounding_checks(
        a, b, config=_measurement_config(), seed=4
    )
    nearest = result["changes"]["nearest"]["overall"]
    assert len(nearest) == 20
    assert nearest == pytest.approx([-1.0] * 20)
    assert result["changes"]["up"]["employed"] == pytest.approx([4.0] * 20)
    assert result["changes"]["nearest_min5"]["employed"] == pytest.approx([-1.0] * 20)
    assert result["shares"]["nearest"].shape == (20, 7, 6, 4)
    assert result["shares"]["nearest"][:, 0, 2, 1] == pytest.approx(np.ones(20))
    assert np.isnan(result["target"][1]).all()  # no bike cell: no fallback


def test_rounding_keeps_modes_and_original_duration_classes_separate() -> None:
    config = _measurement_config()
    a = _measurement_frames([11.0, 21.0, 31.0, 61.0, 11.0, 31.0])
    b = _measurement_frames([10.0, 20.0, 30.0, 60.0, 11.0])
    a.trips["mode7"] = np.array(["walk"] * 4 + ["bike", "car_driver"])
    b.trips["mode7"][-1] = "bike"
    result = variation_report.simulate_rounding(
        a, b, "nearest", config=config, rng=np.random.default_rng(1)
    )
    assert result == pytest.approx([10.0, 20.0, 30.0, 60.0, 11.0, 31.0])
    # 5, 10, 15, 30 and 60 belong to the next class, not the preceding one.
    boundaries = _measurement_frames([4.0, 5.0, 10.0, 15.0, 30.0, 60.0])
    codes, _ = variation_report._rounding_cells(boundaries, config)
    assert codes == pytest.approx(np.arange(6))


def test_rounding_draws_reach_partial_targets_and_are_reproducible() -> None:
    a = _measurement_frames([11.0] * 2000)
    b = _measurement_frames([10.0] * 1000 + [11.0] * 1000)
    config = _measurement_config()
    result = variation_report.rounding_checks(a, b, config=config, seed=18)
    repeated = variation_report.rounding_checks(a, b, config=config, seed=18)
    shares = result["shares"]["nearest"][:, 0, 2, 1]
    assert np.mean(shares) == pytest.approx(0.5, abs=0.02)
    assert np.ptp(shares) > 0
    assert np.mean(result["changes"]["nearest"]["overall"]) == pytest.approx(
        -0.5, abs=0.02
    )
    np.testing.assert_equal(result["shares"]["nearest"], repeated["shares"]["nearest"])


def test_common_distances_reaggregate_without_speed_or_producer_correction() -> None:
    frames = _measurement_frames([2.0, 20.0, 30.0])
    frames.trips["declared_km"] = np.array([300.0, np.nan, 0.0])
    frames.trips["crow_fly_km"] = np.array([0.2, 8.0, np.nan])
    declared = variation_report.common_distance_frames(frames, "declared_km")
    crow = variation_report.common_distance_frames(frames, "crow_fly_km")
    assert declared.days["total_distance_km"] == pytest.approx([300.0, 0.0, 0.0])
    assert declared.days["distance_trips"] == pytest.approx([1.0, 0.0, 1.0])
    assert declared.days["distance_time_min"] == pytest.approx([2.0, 0.0, 30.0])
    assert crow.days["total_distance_km"] == pytest.approx([0.2, 8.0, 0.0])
    assert crow.days["trips_per_day"] == pytest.approx([1.0, 1.0, 1.0])
    assert frames.days["total_distance_km"] == pytest.approx([99.0] * 3)
    # Day ids, not row ordering, determine aggregation.
    frames.trips = {k: v[::-1] for k, v in frames.trips.items()}
    reordered = variation_report.common_distance_frames(frames, "declared_km")
    assert reordered.days["total_distance_km"] == pytest.approx([300.0, 0.0, 0.0])
    decomposition = variation_report.b2_decompositions(
        declared, crow, categories=(), n_reps=N_REPS, seed=0
    )[0].result
    assert decomposition is not None
    assert decomposition.point.distance_a_km == pytest.approx(150.0)
    assert decomposition.point.distance_b_km == pytest.approx(4.1)
    assert decomposition.point.distance_share_a == pytest.approx(2 / 3)
    assert decomposition.point.trips_a == pytest.approx(1.0)


def test_motive_rates_include_zero_days_and_bootstrap_households() -> None:
    a = _measurement_frames([2.0, 5.0, 4.0, 8.0])
    b = _measurement_frames([2.0, 5.0, 4.0, 8.0])
    for frames in (a, b):
        frames.days["pond_jour"] = np.array([1.0, 1.0, 3.0, 3.0])
        frames.trips["motive_group"] = np.array(["2", "9", "2", "9"])
        frames.trips["crow_fly_km"] = np.array([0.2, np.nan, 0.5, 1.0])
    b.trips["motive_group"][:] = "2"
    rows = variation_report.motive_rate_checks(
        a, b, config=_measurement_config(), n_reps=20, seed=3
    )
    shopping = next(r for r in rows if r.group == "employed" and r.metric == "shopping")
    assert shopping.mean_a == pytest.approx(0.5)
    assert shopping.mean_b == pytest.approx(1.0)
    # Each household has one shopping day and one non-shopping day.
    assert shopping.ci_a == pytest.approx((0.5, 0.5))
    assert shopping.delta_ci == pytest.approx((0.5, 0.5))
    short = next(
        r
        for r in rows
        if r.group == "employed" and r.metric == "trips under 1 km (crow-fly)"
    )
    assert short.mean_a == pytest.approx(0.5)
    short_time = next(
        r for r in rows if r.group == "employed" and r.metric == "trips under 5 min"
    )
    assert short_time.mean_a == pytest.approx(0.5)
    absent = next(r for r in rows if r.group == "retired" and r.metric == "shopping")
    assert absent.n_a == 0 and np.isnan(absent.mean_a)


def test_measurement_loader_reads_exact_raw_distance_fields(
    synthetic_emp_zip: Path,
    synthetic_entd2008_raw_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for survey, path, declared, crow in (
        (variation_report.emp2019, synthetic_emp_zip, "MDISTTOT_decl", "dVO_ORIDES"),
        (
            variation_report.entd2008,
            synthetic_entd2008_raw_dir,
            "V2_MDISTTOT",
            "V2_DVO_LOC",
        ),
    ):
        build = survey.build_trip_legs

        def distinguish_raw_columns(con, config, **kwargs):
            build(con, config, **kwargs)
            con.sql(f"""
                CREATE TEMP TABLE measurement_raw AS
                SELECT * REPLACE (123.0 AS {declared}, 0.75 AS {crow})
                FROM k_deploc;
                CREATE OR REPLACE VIEW k_deploc AS SELECT * FROM measurement_raw;
            """)

        monkeypatch.setattr(survey, "build_trip_legs", distinguish_raw_columns)
        frames = variation_report.load_frames(survey, path, config_path=CONFIG_PATH)
        assert frames.trips["declared_km"] == pytest.approx(
            np.full(len(frames.trips["pond_jour"]), 123.0)
        )
        assert frames.trips["crow_fly_km"] == pytest.approx(
            np.full(len(frames.trips["pond_jour"]), 0.75)
        )


def test_c5_uses_full_roster_denominator_and_reports_published_gaps() -> None:
    def frames(name: str, person_weights: list[float], day_weight: float):
        data = {
            "household_p": np.array(["h1", "h2"]),
            "weight_p": np.array(person_weights),
            "household_t": np.array(["h1"]),
            "weight_t": np.array([day_weight]),
            "type_t": np.array([1]),
            "minutes": np.array([20.0]),
            "distance_km": np.array([8.0]),
            "zero_local_n_days": 1,
            "described_n_days": 2,
            "zero_local_weight": 3.0,
            "described_weight": 4.0,
            "n_people": 60,
        }
        return variation_report.SurveyFrames(
            name=name, days={}, trips={}, aux={"official_scope_data": data}
        )

    entd = variation_report._official_scope_estimates(
        frames("ENTD 2008", [5.0, 15.0], 5.0), n_reps=30, seed=1
    )
    emp = variation_report._official_scope_estimates(
        frames("EMP 2019", [1.0, 3.0], 1.0), n_reps=30, seed=2
    )

    assert entd["weekday"]["trips_per_person"]["estimate"] == pytest.approx(0.25)
    assert emp["weekday"]["trips_per_person"]["estimate"] == pytest.approx(0.05)
    assert emp["week"]["trips_per_person"]["estimate"] == pytest.approx(0.25)
    report = "\n".join(variation_report._format_official_scope(entd, emp))
    for reference in (
        "3.15",
        "3.04055",
        "20.36964",
        "8.72921",
        "19.7928",
        "20.69912",
        "8.970084",
    ):
        assert reference in report
    assert "Gap 2019" in report
    assert "zero-local-trip diagnostic" in report.lower()
    assert "75.00% by day weight" in report
    week_trip_row = next(
        line
        for line in report.splitlines()
        if line.startswith("| 7-day | trips_per_person |")
    )
    assert "trips/person/week" in week_trip_row
    assert "19.7928" in week_trip_row
    assert "-98.7" in week_trip_row


def test_c6_speed_uses_weighted_totals_and_crow_fly_zero_share() -> None:
    sample = variation_report.SpeedSample(
        household=np.array(["h1", "h2", "h3", "h4"]),
        weight=np.ones(4),
        duration_min=np.array([10.0, 50.0, 20.0, 30.0]),
        producer_km=np.array([1.0, 10.0, 8.0, 2.0]),
        crow_fly_km=np.array([1.0, 3.0, 3.0, 2.1]),
        mode=np.array(["car_driver"] * 4),
        density=np.array(["dense", "dense", "sparse", "very_sparse"]),
        residence_zone=np.array(["11", "12", "13", ""]),
    )
    selected = np.ones(4, dtype=bool)

    producer = variation_report._bootstrap_speed_estimate(
        sample, "producer", selected, n_reps=40, seed=4
    )
    crow = variation_report._bootstrap_speed_estimate(
        replace(sample, crow_fly_km=np.array([0.0, 3.0, 3.0, 2.1])),
        "crow-fly",
        selected,
        n_reps=40,
        seed=4,
    )

    assert producer.km_per_trip.estimate == pytest.approx(5.25)
    assert producer.speed_kmh.estimate == pytest.approx(60.0 * 21.0 / 110.0)
    assert producer.speed_kmh.estimate != pytest.approx(
        np.mean(60.0 * sample.producer_km / sample.duration_min)
    )
    assert np.isfinite(producer.speed_kmh.interval).all()
    with pytest.raises(ValueError, match="unknown speed distance measure"):
        variation_report._distance_measure_values(sample, "declared")
    assert crow.zero_km_share is not None
    assert crow.zero_km_share.estimate == pytest.approx(0.25)
    classified = replace(
        sample,
        density=np.array(
            ["dense", "dense", "sparse", "intermediate", "very_sparse", "dense"]
        ),
        residence_zone=np.array(["11", "12", "13", "20", "30", ""]),
    )
    assert variation_report._residence_classes(classified).tolist() == [
        "pôle",
        "pôle",
        "pôle",
        "couronne",
        "hors attraction",
        "INSEE density: dense",
    ]


def test_c6_crow_fly_distribution_excludes_zeros_and_lumps_over_5km() -> None:
    sample = variation_report.SpeedSample(
        household=np.array(["h"] * 6),
        weight=np.array([1.0, 1.0, 2.0, 1.0, 1.0, 1.0]),
        duration_min=np.full(6, 10.0),
        producer_km=np.full(6, 1.0),
        crow_fly_km=np.array([0.0, 0.3, 1.5, 4.99, 5.0, np.nan]),
        mode=np.array(["walk"] * 6),
        density=np.array(["dense"] * 6),
        residence_zone=np.array([""] * 6),
    )

    rows = variation_report.crow_fly_distribution_rows(sample, "ENTD 2008")

    by_band = {row["band"]: row for row in rows}
    assert [row["band"] for row in rows] == list(
        variation_report.CROW_FLY_BAND_LABELS
    )
    assert sum(row["share"] for row in rows) == pytest.approx(1.0)
    # The zero and NaN trips are excluded: total weight 5.
    assert by_band["0-0.5 km"]["share"] == pytest.approx(0.2)
    assert by_band["0-0.5 km"]["n"] == 1
    assert by_band["1.5-2 km"]["share"] == pytest.approx(0.4)
    assert by_band["4.5-5 km"]["share"] == pytest.approx(0.2)
    assert by_band[">=5 km"]["share"] == pytest.approx(0.2)

    lines = variation_report._format_c6_crow_fly_measure(
        rows + variation_report.crow_fly_distribution_rows(sample, "EMP 2019")
    )
    text = "\n".join(lines)
    assert "V2_DVO_LOC" in text and "dVO_ORIDES" in text
    assert "chefs-lieux" in text and "centroïdes" in text
    # Cells under 50 trips keep their true n and hide the share.
    band_line = next(line for line in lines if line.startswith("| 1.5-2 km"))
    assert band_line == "| 1.5-2 km | 1 | - | 1 | - |"


def test_c6_standardized_car_speed_holds_the_2008_cell_mix_constant() -> None:
    def sample(
        first_cell_n: int,
        second_cell_n: int,
        first_minutes: float,
        second_minutes: float,
    ) -> variation_report.SpeedSample:
        n = first_cell_n + second_cell_n
        return variation_report.SpeedSample(
            household=np.array([f"h{i}" for i in range(n)]),
            weight=np.ones(n),
            duration_min=np.array(
                [first_minutes] * first_cell_n + [second_minutes] * second_cell_n
            ),
            producer_km=np.array([3.0] * first_cell_n + [7.0] * second_cell_n),
            crow_fly_km=np.array([3.0] * first_cell_n + [7.0] * second_cell_n),
            mode=np.array(["car_driver"] * n),
            density=np.array(["dense"] * first_cell_n + ["sparse"] * second_cell_n),
            residence_zone=np.array(["11"] * n),
        )

    cells, n_2008, n_2019, speed_2008, speed_2019 = (
        variation_report._standardized_car_speed(
            sample(50, 50, 30.0, 70.0),
            sample(10, 90, 15.0, 21.0),
            n_reps=30,
            seed=8,
        )
    )

    assert cells == 2
    assert n_2008 == n_2019 == 100
    assert speed_2008.estimate == pytest.approx(6.0)
    assert speed_2019.estimate == pytest.approx(60.0 * 5.0 / 18.0)
    assert np.isfinite(speed_2019.interval).all()
    assert variation_report._ratio_metric(speed_2008, speed_2019) is not None


def _period_speed_sample(
    *,
    duration_before: float,
    duration_after: float,
    before_tag: str,
    after_tag: str,
    tag_field: str,
) -> variation_report.SpeedSample:
    """120 identical 15 km car-driver trips in one intermediate-density
    cell, half tagged before and half after (by month or by date)."""
    n, half = 120, 60
    tags = np.array([before_tag] * half + [after_tag] * half, dtype=object)
    blanks = np.array([""] * n, dtype=object)
    return variation_report.SpeedSample(
        household=np.array([f"h{i}" for i in range(n)]),
        weight=np.ones(n),
        duration_min=np.array([duration_before] * half + [duration_after] * half),
        producer_km=np.full(n, 15.0),
        crow_fly_km=np.full(n, 15.0),
        mode=np.array(["car_driver"] * n, dtype=object),
        density=np.array(["intermediate"] * n, dtype=object),
        residence_zone=blanks.copy(),
        month=tags if tag_field == "month" else blanks.copy(),
        date=tags if tag_field == "date" else blanks.copy(),
    )


def test_c6_speed_limit_check_standardizes_each_split_to_the_2008_mix() -> None:
    """3a: EMP before/after at the 2008 mix (90 vs 80 km/h), the ENTD
    season control (60 vs 50 km/h) and the ratio of ratios."""
    entd = _period_speed_sample(
        duration_before=15.0,
        duration_after=18.0,
        before_tag="2007-06-30",
        after_tag="2007-07-01",
        tag_field="date",
    )
    emp = _period_speed_sample(
        duration_before=10.0,
        duration_after=11.25,
        before_tag="mai",
        after_tag="octobre",
        tag_field="month",
    )
    # Two ambiguous avril trips must leave both periods.
    months = emp.month.copy()
    months[:2] = "avril"
    emp = replace(emp, month=months)

    rows = variation_report.speed_limit_check(entd, emp, n_reps=20, seed=0)

    main = "main: 10-80 km, intermediate/sparse/very sparse"
    by = {(row["check"], row["survey"]): row for row in rows}
    emp_row = by[(main, "EMP 2019")]
    assert emp_row["cells"] == 1
    assert (emp_row["n_before"], emp_row["n_after"]) == (58, 60)
    assert emp_row["speed_before"].estimate == pytest.approx(90.0)
    assert emp_row["speed_after"].estimate == pytest.approx(80.0)
    assert emp_row["ratio"].estimate == pytest.approx(8 / 9)
    entd_row = by[(main, "ENTD 2008 (season control)")]
    assert entd_row["speed_before"].estimate == pytest.approx(60.0)
    assert entd_row["speed_after"].estimate == pytest.approx(50.0)
    assert entd_row["ratio"].estimate == pytest.approx(5 / 6)
    ratio_of_ratios = by[(main, "ratio of ratios (EMP / ENTD)")]["ratio"]
    assert ratio_of_ratios.estimate == pytest.approx(16 / 15)
    # No 2-10 km dense trips: the placebo prints unavailable cells.
    placebo_row = by[("placebo: 2-10 km, dense", "EMP 2019")]
    assert placebo_row["cells"] == 0
    assert placebo_row["ratio"] is None

    lines = variation_report._format_c6_speed_limit(
        rows,
        {
            "share_before": 0.3,
            "share_ambiguous": 0.05,
            "n_before": 58,
            "n_after": 60,
            "n_ambiguous": 2,
        },
    )
    text = "\n".join(lines)
    assert "#### 80 km/h limit (1 July 2018)" in text
    assert "avril" in text
    assert "30.0%" in text
    placebo_line = next(
        line
        for line in lines
        if line.startswith("| placebo: 2-10 km, dense | EMP 2019")
    )
    assert placebo_line.endswith("| 0 | 0 | - | - | - |")
    csv_rows = variation_report._speed_limit_csv_rows(rows)
    by_csv = {(row["check"], row["split"]): row for row in csv_rows}
    assert by_csv[(main, "EMP 2019")]["ratio"] == pytest.approx(8 / 9)
    assert by_csv[("placebo: 2-10 km, dense", "EMP 2019")]["ratio"] == ""


def test_c6_recall_lag_speed_rows_split_emp_by_lag() -> None:
    """3b: the pooled standardized ratio, with EMP split by recall lag."""

    def sample(durations: list[float], lags: list[float] | None):
        n = len(durations)
        return variation_report.SpeedSample(
            household=np.array([f"h{i}" for i in range(n)]),
            weight=np.ones(n),
            duration_min=np.asarray(durations, dtype=float),
            producer_km=np.full(n, 15.0),
            crow_fly_km=np.full(n, 15.0),
            mode=np.array(["car_driver"] * n, dtype=object),
            density=np.array(["intermediate"] * n, dtype=object),
            residence_zone=np.array([""] * n, dtype=object),
            recall_lag=None if lags is None else np.asarray(lags, dtype=float),
        )

    entd = sample([15.0] * 120, None)  # 60 km/h
    emp = sample(
        [10.0] * 60 + [12.0] * 60 + [18.0] * 60 + [90.0] * 10,
        [1.0] * 60 + [2.0] * 30 + [3.0] * 30 + [5.0] * 60 + [float("nan")] * 10,
    )

    rows = variation_report.recall_lag_speed_rows(entd, emp, n_reps=20, seed=0)

    by_lag = {row["lag"]: row for row in rows}
    assert list(by_lag) == ["all days", "1 day", "2-3 days", "4-7 days"]
    assert by_lag["1 day"]["n_2019"] == 60
    assert by_lag["1 day"]["ratio"].estimate == pytest.approx(1.5)
    assert by_lag["2-3 days"]["ratio"].estimate == pytest.approx(1.25)
    assert by_lag["4-7 days"]["ratio"].estimate == pytest.approx(5 / 6)
    # The unknown-lag trips enter the all-days row only.
    assert by_lag["all days"]["n_2019"] == 190
    assert all(row["speed_2008"].estimate == pytest.approx(60.0) for row in rows)

    lines = variation_report._format_c6_recall_lag_speed(rows)
    assert lines[0] == "#### Recall lag and the standardized car-driver ratio"
    lag_line = next(line for line in lines if line.startswith("| 2-3 days"))
    assert "1.250" in lag_line
    csv_rows = variation_report._recall_lag_speed_csv_rows(rows)
    assert csv_rows[2]["emp_recall_lag"] == "2-3 days"
    assert csv_rows[2]["ratio"] == pytest.approx(1.25)
    with pytest.raises(ValueError, match="recall lags"):
        variation_report.recall_lag_speed_rows(entd, entd, n_reps=5, seed=0)


def test_c6_duration_bands_report_weighted_deciles_and_round_shares() -> None:
    """3c: deciles use the cumulative-weight rule and the round-minute
    shares count exact multiples (30 is also a multiple of 15)."""
    n = 5
    sample = variation_report.SpeedSample(
        household=np.array([f"h{i}" for i in range(n)]),
        weight=np.ones(n),
        duration_min=np.array([10.0, 15.0, 30.0, 7.0, 45.0]),
        producer_km=np.full(n, 3.0),
        crow_fly_km=np.full(n, 3.0),
        mode=np.array(["car_driver"] * 4 + ["walk"], dtype=object),
        density=np.array(["dense"] * n, dtype=object),
        residence_zone=np.array([""] * n, dtype=object),
    )

    rows = variation_report.duration_band_rows(sample, sample)

    car_2008 = next(
        row
        for row in rows
        if row["modes"] == "car driver"
        and row["survey"] == "ENTD 2008"
        and row["band"] == "2-5 km"
    )
    assert car_2008["n"] == 4
    assert car_2008["deciles"].tolist() == [
        7.0,
        7.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        30.0,
        30.0,
    ]
    assert car_2008["share_multiple_15"] == pytest.approx(0.5)
    assert car_2008["share_multiple_30"] == pytest.approx(0.25)
    all_2019 = next(
        row
        for row in rows
        if row["modes"] == "all modes"
        and row["survey"] == "EMP 2019"
        and row["band"] == "2-5 km"
    )
    assert all_2019["n"] == 5
    assert all_2019["share_multiple_15"] == pytest.approx(0.6)
    assert all_2019["share_multiple_30"] == pytest.approx(0.2)
    empty = next(row for row in rows if row["band"] == "40-80 km")
    assert empty["n"] == 0 and np.isnan(empty["deciles"]).all()

    lines = variation_report._format_c6_duration_bands(rows)
    assert lines[0] == "#### Trip durations within crow-fly bands"
    car_line = next(
        line for line in lines if line.startswith("| car driver | 2-5 km | ENTD 2008")
    )
    # Under 50 trips: the true n stays, every value is hidden.
    assert car_line == (
        "| car driver | 2-5 km | ENTD 2008 | 4 | - | - | - | - | - | - | - | "
        "- | - | - | - |"
    )
    csv_rows = variation_report._duration_band_csv_rows(rows)
    first = csv_rows[0]
    assert first["modes"] == "car driver" and first["band"] == "2-5 km"
    assert first["d50_min"] == ""  # suppressed below 50 trips
    assert list(first)[4:13] == [f"d{p}_min" for p in range(10, 100, 10)]


def test_c6_mode_mix_speed_isolates_the_mode_shift() -> None:
    """3d: with constant within-mode speeds, the mode x band x density
    standardization gives a flat ratio while the band x density one keeps
    the mode-shift speed gain."""

    def sample(n_walk: int, n_car: int) -> variation_report.SpeedSample:
        n = n_walk + n_car
        return variation_report.SpeedSample(
            household=np.array([f"h{i}" for i in range(n)]),
            weight=np.ones(n),
            duration_min=np.array([45.0] * n_walk + [6.0] * n_car),
            producer_km=np.full(n, 3.0),
            crow_fly_km=np.full(n, 3.0),
            mode=np.array(["walk"] * n_walk + ["car_driver"] * n_car, dtype=object),
            density=np.array(["dense"] * n, dtype=object),
            residence_zone=np.array([""] * n, dtype=object),
        )

    rows = variation_report.mode_mix_speed_rows(
        sample(50, 50), sample(20, 80), n_reps=20, seed=0
    )

    by = {row["comparison"]: row for row in rows}
    assert list(by) == [
        "as observed",
        "2008 mode x band x density mix",
        "2008 band x density mix",
        *(f"within {mode}" for mode in variation_report.MODE_MIX_MODES),
    ]
    observed_ratio = 2550.0 / 1380.0
    assert by["as observed"]["ratio"].estimate == pytest.approx(observed_ratio)
    assert by["as observed"]["speed_2008"].estimate == pytest.approx(60 * 300 / 2550)
    # Holding the 2008 mode mix removes the whole speed change ...
    assert by["2008 mode x band x density mix"]["ratio"].estimate == pytest.approx(1.0)
    assert by["2008 mode x band x density mix"]["cells"] == 2
    # ... while band x density cells alone let the mode shift act.
    assert by["2008 band x density mix"]["ratio"].estimate == pytest.approx(
        observed_ratio
    )
    assert by["2008 band x density mix"]["cells"] == 1
    assert by["within walk"]["ratio"].estimate == pytest.approx(1.0)
    assert by["within walk"]["speed_2008"].estimate == pytest.approx(4.0)
    assert by["within car_driver"]["ratio"].estimate == pytest.approx(1.0)
    assert by["within train"]["cells"] == 0
    assert by["within train"]["ratio"] is None

    lines = variation_report._format_c6_mode_mix_speed(rows)
    assert lines[0] == "#### All-mode speed with the mode mix held constant"
    train_line = next(line for line in lines if line.startswith("| within train"))
    assert train_line.endswith("| - | - | - |")
    csv_rows = variation_report._mode_mix_speed_csv_rows(rows)
    by_csv = {row["comparison"]: row for row in csv_rows}
    assert by_csv["as observed"]["ratio"] == pytest.approx(observed_ratio)
    # within walk has only 20 trips in 2019: suppressed in the CSV too.
    assert by_csv["within walk"]["ratio"] == ""


def test_c6_clock_time_rows_measure_minute_rounding_and_duration_gap() -> None:
    """3e: minute categories, the duration = arrival - departure share
    (overnight gaps mod 24 h) and the mean duration gap, by mode."""
    nan = float("nan")
    trips = {
        "pond_jour": [1.0] * 8,
        "mode7": ["car_driver"] * 7 + ["walk"],
        "departure_min": [480.0, 495.0, 510.0, 500.0, 503.0, nan, 1430.0, 600.0],
        "arrival_min": [510.0, 520.0, 540.0, nan, 523.0, 600.0, 10.0, 615.0],
        "duration_min": [30.0, 30.0, 25.0, 20.0, 20.0, 10.0, 20.0, 15.0],
    }
    frames = _frames({}, trips)

    minute_rows, gap_rows = variation_report.clock_time_rows(frames, frames)

    def pick(rows: list[dict], mode: str, endpoint: str | None = None) -> dict:
        return next(
            row
            for row in rows
            if row["survey"] == "EMP 2019"
            and row["mode"] == mode
            and (endpoint is None or row["endpoint"] == endpoint)
        )

    departure = pick(minute_rows, "car_driver", "departure")
    assert departure["n"] == 6
    assert departure["share_:00"] == pytest.approx(1 / 6)
    assert departure["share_:30"] == pytest.approx(1 / 6)
    assert departure["share_:15/:45"] == pytest.approx(1 / 6)
    assert departure["share_other multiple of 5"] == pytest.approx(2 / 6)
    assert departure["share_other"] == pytest.approx(1 / 6)
    arrival = pick(minute_rows, "car_driver", "arrival")
    assert arrival["n"] == 6
    assert arrival["share_:00"] == pytest.approx(2 / 6)
    assert arrival["share_:15/:45"] == 0.0
    assert pick(minute_rows, "All", "departure")["n"] == 7
    gap = pick(gap_rows, "car_driver")
    # The 23:50 -> 00:10 overnight trip counts as a 20-min gap.
    assert gap["n"] == 5
    assert gap["share_equal"] == pytest.approx(3 / 5)
    assert gap["mean_duration_minus_gap"] == pytest.approx(0.0)
    assert pick(gap_rows, "walk")["share_equal"] == pytest.approx(1.0)

    lines = variation_report._format_c6_clock_times(minute_rows, gap_rows)
    assert lines[0] == "#### Clock times behind the durations"
    departure_line = next(
        line
        for line in lines
        if line.startswith("| EMP 2019 | car_driver | departure")
    )
    # Under 50 trips: the true n stays, every share is hidden.
    assert departure_line == (
        "| EMP 2019 | car_driver | departure | 6 | - | - | - | - | - |"
    )
    minute_csv = variation_report._clock_minute_csv_rows(minute_rows)
    assert minute_csv[0]["share_00"] == ""  # suppressed below 50 trips
    assert list(minute_csv[0])[4:] == [
        "share_00",
        "share_30",
        "share_15_45",
        "share_other_multiple_5",
        "share_other",
    ]
    gap_csv = variation_report._clock_gap_csv_rows(gap_rows)
    assert gap_csv[0]["share_duration_equals_gap"] == ""


def test_c6_speed_limit_period_masks_and_day_share() -> None:
    months = np.array(
        ["mai", "Juin ", "octobre", "janvier", "avril", "nonsense"], dtype=object
    )
    before, after = variation_report._emp_period_masks(months)
    assert before.tolist() == [True, True, False, False, False, False]
    assert after.tolist() == [False, False, True, True, False, False]
    dates = np.array(["2007-06-30", "2007-07-01", ""], dtype=object)
    entd_before, entd_after = variation_report._entd_period_masks(dates)
    assert entd_before.tolist() == [True, False, False]
    assert entd_after.tolist() == [False, True, False]
    frames = _frames(
        {
            "pond_jour": [1.0, 1.0, 2.0, 4.0],
            "described_month_name": ["mai", "juin", "octobre", "avril"],
        },
        {"pond_jour": []},
    )
    share = variation_report.emp_day_share_before(frames)
    assert share["share_before"] == pytest.approx(0.5)
    assert share["share_ambiguous"] == pytest.approx(0.5)
    assert (share["n_before"], share["n_after"], share["n_ambiguous"]) == (2, 1, 1)


def test_c7_period_estimates_use_full_roster_and_traveller_days() -> None:
    sample = variation_report.PeriodBudgetSample(
        person_household=np.array(["h1", "h2"]),
        person_weight=np.array([1.0, 3.0]),
        day_household=np.array(["h1", "h1", "h2"]),
        day_person=np.array(["p1", "p2", "p3"]),
        day_weight=np.array([2.0, 2.0, 4.0]),
        day_type=np.array([1, 2, 1]),
        trips=np.array([2.0, 3.0, 1.0]),
        total_time_min=np.array([20.0, 60.0, 30.0]),
        time_trips=np.array([2.0, 3.0, 1.0]),
    )

    weekday = variation_report._period_budget_estimates(
        sample,
        day_types=(1,),
        person_period_divisor=5.0,
        n_reps=20,
        seed=3,
    )
    saturday = variation_report._period_budget_estimates(
        sample,
        day_types=(2,),
        person_period_divisor=1.0,
        n_reps=20,
        seed=3,
    )
    week = variation_report._period_budget_estimates(
        sample,
        day_types=(1, 2, 3),
        person_period_divisor=7.0,
        n_reps=20,
        seed=3,
    )

    assert weekday["per_person"]["trips_per_day"].estimate == pytest.approx(0.4)
    assert weekday["per_person"]["minutes_per_day"].estimate == pytest.approx(8.0)
    assert weekday["per_traveller"]["trips_per_day"].estimate == pytest.approx(8 / 6)
    assert weekday["per_traveller"]["minutes_per_day"].estimate == pytest.approx(
        160 / 6
    )
    assert saturday["per_person"]["trips_per_day"].estimate == pytest.approx(1.5)
    assert saturday["per_traveller"]["minutes_per_day"].estimate == pytest.approx(60.0)
    assert week["per_person"]["trips_per_day"].estimate == pytest.approx(0.5)
    assert week["per_person"]["minutes_per_day"].estimate == pytest.approx(10.0)
    assert weekday["per_person"]["minutes_per_trip"].estimate == pytest.approx(20.0)
    assert len(weekday["per_person"]["trips_per_day"].replicates) == 20


def test_c7_comparison_has_weekday_ratio_and_marks_entd_weekends_unavailable() -> None:
    def sample(name: str, day_weight: float, person_weight: float):
        people = np.array([f"{name}{i}" for i in range(60)])
        households = np.array([f"h{i}" for i in range(60)])
        return variation_report.PeriodBudgetSample(
            person_household=households,
            person_weight=np.full(60, person_weight),
            day_household=households,
            day_person=people,
            day_weight=np.full(60, day_weight),
            day_type=np.ones(60, dtype=int),
            trips=np.full(60, 2.0),
            total_time_min=np.full(60, 40.0),
            time_trips=np.full(60, 2.0),
        )

    sample_2008 = sample("a", 5.0, 5.0)
    sample_2019 = sample("b", 5.0, 1.0)
    frames_2008 = _frames(
        {},
        {},
        aux={
            "c7_data": {
                scope_id: sample_2008 for scope_id in ("sdes", "reference", "daytable")
            }
        },
    )
    frames_2019 = _frames(
        {},
        {},
        aux={
            "c7_data": {
                scope_id: sample_2019 for scope_id in ("sdes", "reference", "daytable")
            }
        },
    )

    rows = variation_report._c7_comparison(frames_2008, frames_2019, n_reps=30, seed=2)
    weekday = next(
        row
        for row in rows
        if row["scope"] == scope.SDES_SCOPE.id
        and row["period"] == "weekday"
        and row["basis"] == "per person"
        and row["measure"] == "Trips/day"
    )
    saturday = next(
        row
        for row in rows
        if row["scope"] == scope.SDES_SCOPE.id
        and row["period"] == "Saturday"
        and row["basis"] == "per person"
        and row["measure"] == "Trips/day"
    )
    assert weekday["estimate_2008"] == pytest.approx(2.0)
    assert weekday["estimate_2019"] == pytest.approx(2.0)
    assert weekday["ratio"] is not None
    assert weekday["ratio"][0] == pytest.approx(1.0)
    assert saturday["estimate_2008"] is None
    assert saturday["ratio"] is None


def test_emp_weekday_out_counts_require_complete_week() -> None:
    rows = [
        ("p1", "h1", 1.0, "weekday", 0.0),
        ("p1", "h1", 1.0, "weekday", 0.0),
        ("p1", "h1", 1.0, "weekday", 0.0),
        ("p1", "h1", 1.0, "weekday", 0.0),
        ("p1", "h1", 1.0, "weekday", 0.0),
        ("p1", "h1", 1.0, "saturday", 0.0),
        ("p2", "h2", 1.0, "weekday", 1.0),
        ("p2", "h2", 1.0, "weekday", 1.0),
        ("p2", "h2", 1.0, "weekday", 1.0),
        ("p2", "h2", 1.0, "weekday", 1.0),
        ("p2", "h2", 1.0, "weekday", 1.0),
        ("p3", "h3", 1.0, "weekday", 0.0),
        ("p3", "h3", 1.0, "weekday", 0.0),
        ("p3", "h3", 1.0, "weekday", 0.0),
        ("p3", "h3", 1.0, "weekday", 0.0),
    ]

    people, weekdays_out, weekdays_observed = variation_report._emp_weekday_out_counts(
        rows
    )
    by_person = {
        person: (int(out), int(observed))
        for person, out, observed in zip(people, weekdays_out, weekdays_observed)
    }

    assert by_person == {"p1": (5, 5), "p2": (0, 5), "p3": (4, 4)}
    selected_people, selected_out, selected_observed = (
        variation_report._emp_weekday_out_counts(
            rows, sampled_households=np.array(["h2"])
        )
    )
    assert selected_people.tolist() == ["p2"]
    assert selected_out.tolist() == [0]
    assert selected_observed.tolist() == [5]


def test_c8b_compares_weekday_time_with_frequency_times_time() -> None:
    n = 100
    people = np.array([f"p{i:03}" for i in range(n)])
    out_count = np.repeat([1.0, 3.0], n // 2)
    time = np.repeat([20.0, 30.0], n // 2)
    days = {
        "ident_ind": people,
        "pond_jour": np.ones(n),
        "total_time_min": time,
        "trips_per_day": np.full(n, 2.0),
        "total_distance_km": np.full(n, 4.0),
        "distance_trips": np.full(n, 2.0),
        "population_category": np.full(n, "employed"),
        "home_density": np.repeat(["dense", "sparse"], n // 2),
    }
    frames = _frames(days, {}, aux={})
    frames.aux["emp_weekday_out"] = (
        people,
        out_count.astype(int),
        np.full(n, 5, dtype=int),
    )

    summary = variation_report._c8b_summary(frames)

    assert summary["n_complete"] == 100
    assert summary["n_matched_days"] == 100
    assert summary["time_cv"] == pytest.approx(0.2)
    assert summary["weekly_time_cv"] == pytest.approx(70 / 110)
    assert summary["less_variable"] == "time/day"
    assert summary["n_cv_groups"] == 2
