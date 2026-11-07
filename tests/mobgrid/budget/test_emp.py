"""Tests for the step 11 CLI (``python -m mobgrid.budget.emp``).

``test_cli_writes_figures_and_report_on_synthetic_data`` is isolated (no
network, no ``data/raw`` access): it runs the full command against the
tiny synthetic archive of ``conftest.py``. The one real-data check,
``test_real_emp_2019_mean_daily_energy_is_within_kh_order_of_magnitude``,
is gated by ``@pytest.mark.skipif`` (not ``@pytest.mark.pilot``, unlike
``.github/instructions/tests.instructions.md``'s convention) and skipped
only when the EMP 2019 archive has not been downloaded; it otherwise
runs as part of the default suite.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from mobgrid.budget import daily_energy, emp, emp2019, entd2008, scope

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"
_REAL_DATA_AVAILABLE = emp2019.DEFAULT_ZIP_PATH.is_file()


def test_time_day_reader_does_not_require_energy() -> None:
    """Section 9.9: time/trips use every in-scope day; energy retains its n."""
    import duckdb

    con = duckdb.connect()
    con.sql("""
        CREATE TABLE day_summary AS
        SELECT 'walking_only' AS day_mode_group, 'employed' AS population_category,
            'dense' AS home_density, 'q1' AS income_quintile,
            CAST(i AS VARCHAR) AS ident_men, 1 AS typejour,
            1.0 AS pond_jour, 10.0 AS total_time_min,
            CASE WHEN i < 10 THEN NULL ELSE 100.0 END AS total_energy_kh_kj,
            CASE WHEN i < 10 THEN NULL ELSE 90.0 END AS total_energy_cp_kj,
            2 AS trips_per_day
        FROM range(80) AS v(i)
    """)
    assert len(emp._day_rows(con, include_unknown_energy=True)["pond_jour"]) == 80
    assert len(emp._day_rows(con)["pond_jour"]) == 70
    con.close()


def test_scope_label_is_only_appended_to_report_title() -> None:
    """Section 9.9: same-scope section headings do not repeat scope words."""
    lines = ["# Report", "## Time", "### Energy", "**Scope:** reference"]
    assert emp._append_scope_to_headings(lines, "Reference") == [
        "# Report — Reference",
        "## Time",
        "### Energy",
        "**Scope:** reference",
    ]


def test_comparison_energy_ratios_exclude_masked_unknown_days() -> None:
    """Section 9.9: DuckDB NULL masks must not enter energy-known ratios."""
    household = np.array([f"M{i // 2}" for i in range(80)])
    weight = np.ones(80)
    known = np.arange(80) >= 10
    samples = []
    for scale in (1.0, 1.2):
        energy = np.arange(1.0, 81.0) * scale
        energy[~known] = 10000.0
        samples.append(
            {
                "ident_men": household,
                "pond_jour": weight,
                "population_category": np.full(80, "employed"),
                "energy": np.ma.array(energy, mask=~known),
            }
        )
    ratio, ci = daily_energy.bootstrap_ratio_ci(
        household[known],
        weight[known],
        samples[0]["energy"].compressed(),
        household[known],
        weight[known],
        samples[1]["energy"].compressed(),
    )
    assert emp._comparison_ratio_intervals(
        *samples, "population_category", "energy", n_reps=200, seed=0
    )["employed"] == (ratio, *ci)


@pytest.mark.parametrize("age_table", ["tcm_ind_kish", "q_tcm_individu"])
def test_age_eligibility_removes_children_and_missing_ages_in_every_scope(
    age_table: str,
) -> None:
    """Section 9.9: the age-6+ universe precedes all three scope switches."""
    import duckdb

    con = duckdb.connect()
    con.sql("""
        CREATE TABLE survey_all_respondents AS
        SELECT * FROM (VALUES ('young'), ('six'), ('adult'), ('missing'), ('unlinked'))
            AS v(IDENT_IND);
        CREATE TABLE survey_all_trips AS SELECT * FROM survey_all_respondents;
    """)
    con.sql(f"""
        CREATE TABLE {age_table} AS
        SELECT * FROM (VALUES ('young', 5), ('six', 6), ('adult', 35),
            ('missing', NULL)) AS v(IDENT_IND, AGE)
    """)
    scope.create_age_eligible_survey_views(con, age_table=age_table)
    assert con.sql("SELECT IDENT_IND FROM k_individu ORDER BY 1").fetchall() == [
        ("adult",),
        ("six",),
    ]
    assert con.sql("SELECT IDENT_IND FROM k_deploc ORDER BY 1").fetchall() == [
        ("adult",),
        ("six",),
    ]
    audit = scope.age_eligibility_summary(con)
    assert audit == {"respondents": 5, "eligible": 2, "under_6": 1, "missing_age": 2}
    con.close()


def test_person_ratio_matches_c7_and_figure_intervals() -> None:
    """Section 9.9: shared roster denominator and seed for person ratios."""
    from mobgrid.budget import variation_report

    results = []
    frames = []
    for year in range(2):
        households = np.array([f"M{i // 2}" for i in range(80)])
        weight = np.linspace(1.0, 2.0, 80)
        minutes = np.linspace(10.0, 90.0 + year * 10.0, 80)
        divisor = 1.0 if year == 0 else 5.0
        days = {
            "ident_men": households,
            "pond_jour": weight,
            "total_time_min": minutes,
            "population_category": np.full(80, "employed"),
        }
        persons = {
            "household": np.append(households, "immobile"),
            "weight": np.ones(81),
            "category": np.full(81, "employed"),
            "period_divisor": divisor,
        }
        results.append(
            {
                "_weekday_person_rows": persons,
                "_weekday_person_budget_days": days,
            }
        )
        sample = variation_report.PeriodBudgetSample(
            person_household=persons["household"],
            person_weight=persons["weight"],
            day_household=households,
            day_person=np.arange(80).astype(str),
            day_weight=weight,
            day_type=np.ones(80, dtype=int),
            trips=np.full(80, 2.0),
            total_time_min=minutes,
            time_trips=np.full(80, 2.0),
        )
        frames.append(
            variation_report.SurveyFrames(
                name=str(year),
                days={},
                trips={},
                aux={
                    "c7_data": dict.fromkeys(("reference", "sdes", "daytable"), sample)
                },
            )
        )
    row = next(
        row
        for row in emp._temporal_person_budget_rows(*results, n_reps=200, seed=0)
        if row.category == "employed"
    )
    c7 = next(
        row
        for row in variation_report._c7_comparison(*frames, n_reps=200, seed=0)
        if row["scope"] == "round-dest-local"
        and row["period"] == "weekday"
        and row["basis"] == "per person"
        and row["measure"] == "Minutes/day"
    )
    assert (row.ratio, row.ci) == c7["ratio"]
    assert emp._person_budget_ratio_intervals(*results, n_reps=200, seed=0)[
        "employed"
    ] == (row.ratio, *row.ci)


def test_cli_writes_figures_and_report_on_synthetic_data(
    tmp_path: Path, synthetic_emp_zip: Path
) -> None:
    out_dir = tmp_path / "step11_budget"
    exit_code = emp.main(
        [
            "--out",
            str(out_dir),
            "--data-path",
            str(synthetic_emp_zip),
            "--config",
            str(CONFIG_PATH),
            "--bootstrap-reps",
            "10",
        ]
    )

    assert exit_code == 0
    md_path = out_dir.with_suffix(".md")
    assert md_path.is_file()
    report = md_path.read_text(encoding="utf-8")
    png_files = sorted(out_dir.glob("*.png"))
    # F1, F1b, F1c, F2a, F2b, F3 x4 (incl. KH appendix), F4a/b, F5, F5b,
    # F6, F7, F8, F9 (motive), F10.
    assert len(png_files) == 18
    csv_files = sorted(out_dir.glob("*.csv"))
    assert {path.stem for path in csv_files} == {path.stem for path in png_files}
    for path in csv_files:
        with path.open(encoding="utf-8", newline="") as stream:
            assert next(csv.reader(stream)) == list(emp.figstyle.CSV_COLUMNS)
    with (out_dir / "f04a_mean_energy_by_mode.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert any(
        row["n"].isdigit() and int(row["n"]) < emp.MIN_CELL_N and not row["mean"]
        for row in rows
    )
    all_energy = next(
        row
        for row in rows
        if row["group"] == "All" and "computed mean (kh)" in row["subgroup"]
    )
    headline = re.search(
        r"Overall weighted mean daily energy: ([\d.]+) kJ \(kh\)", report
    )
    assert headline
    assert float(all_energy["mean"]) == pytest.approx(
        float(headline.group(1)), abs=0.05
    )
    assert any("f09_motive_energy" in p.name for p in png_files)
    assert any("f01b_trips_per_day_by_category" in p.name for p in png_files)
    assert any("f01c_minutes_per_trip_by_category" in p.name for p in png_files)
    assert any("f02a_time_density_overall" in p.name for p in png_files)
    assert any("f02b_time_density_by_category" in p.name for p in png_files)
    assert any("f05b_time_heatmaps" in p.name for p in png_files)
    assert any("f10_constancy" in p.name for p in png_files)

    assert "Round-trip days · destination purposes · local (≤ 80 km)" in report
    assert report.count(scope.REFERENCE_SCOPE.label) == 2
    assert "Mean daily energy and time by main-mode group" in report
    assert "Calibrated v0 and P0" in report
    assert "car_passenger_household" in report
    assert "F8 robustness" in report
    assert "Density classes" in report
    assert "Time budget: constancy across density classes" in report
    assert "Time budget: constancy across income quintiles" in report
    assert "Quintile shares and cut points" in report
    assert "Missing-income breakdown" in report
    assert "no code-side failure mode to report here" in report
    assert "Trips per day and minutes per trip" in report
    assert "Per-person budget, days without trips included" in report
    assert "Direct producer-weighted sum of selected-scope" in report
    assert "zero local trips is" in report
    assert "±15% verdict" in report
    assert "±10% verdict" in report


def test_figstyle_csv_preserves_suppressed_sample_size(tmp_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.set_ylabel("Mean daily time, minutes")
    path = tmp_path / "suppressed.png"
    values = {column: "" for column in emp.figstyle.CSV_COLUMNS}
    values.update(
        figure="suppressed",
        panel="time",
        scope="Reference",
        survey="EMP 2019",
        group="Employed",
        quantity="Mean daily time",
        unit="minutes",
        days="weekday",
        basis="per day with trips",
        n=49,
    )
    emp.figstyle.save_figure(fig, path, rows=[values])
    plt.close(fig)

    assert path.is_file()
    with path.with_suffix(".csv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["n"] == "49"
    assert all(
        not row[column]
        for column in (
            "mean",
            "ci_low",
            "ci_high",
            "median",
            "p25",
            "p75",
            "ratio",
            "ratio_ci_low",
            "ratio_ci_high",
        )
    )


def test_comparison_figures_export_headlines_and_bootstrap_ratios(
    tmp_path: Path,
) -> None:
    emp.figstyle.set_context(
        scope="Reference",
        survey="ENTD 2008 vs EMP 2019",
        days="weekday",
    )
    stats_2008 = [
        SimpleNamespace(
            group="walking_only",
            n=60,
            weighted_n=60.0,
            mean_time_min=60.0,
            p25_time_min=50.0,
            median_time_min=58.0,
            p75_time_min=65.0,
            mean_energy_kh_kj=100.0,
            mean_energy_kh_ci=(90.0, 110.0),
            p25_energy_kh_kj=80.0,
            median_energy_kh_kj=95.0,
            p75_energy_kh_kj=115.0,
            mean_energy_cp_kj=90.0,
            mean_energy_cp_ci=(80.0, 100.0),
            p25_energy_cp_kj=70.0,
            median_energy_cp_kj=85.0,
            p75_energy_cp_kj=105.0,
        )
    ]
    stats_2019 = [
        SimpleNamespace(
            group="walking_only",
            n=60,
            weighted_n=60.0,
            mean_time_min=72.0,
            p25_time_min=60.0,
            median_time_min=70.0,
            p75_time_min=80.0,
            mean_energy_kh_kj=120.0,
            mean_energy_kh_ci=(110.0, 130.0),
            p25_energy_kh_kj=100.0,
            median_energy_kh_kj=115.0,
            p75_energy_kh_kj=135.0,
            mean_energy_cp_kj=108.0,
            mean_energy_cp_ci=(98.0, 118.0),
            p25_energy_cp_kj=88.0,
            median_energy_cp_kj=103.0,
            p75_energy_cp_kj=123.0,
        )
    ]
    ratios = {
        ("walking_only", "kh"): (1.2, 1.1, 1.3),
        ("walking_only", "cp"): (1.2, 1.1, 1.3),
        ("walking_only", "time"): (1.2, 1.1, 1.3),
    }
    energy_path = emp._figure_compare_energy_time(
        stats_2008,
        stats_2019,
        (377.8, 411.5),
        (372.6, 402.7),
        (63.1, 68.4),
        tmp_path,
        time_stats_2008=[
            SimpleNamespace(
                group="walking_only",
                n=60,
                mean=60.0,
                mean_ci=(55.0, 65.0),
                p25=45.0,
                median=58.0,
                p75=70.0,
            )
        ],
        time_stats_2019=[
            SimpleNamespace(
                group="walking_only",
                n=60,
                mean=72.0,
                mean_ci=(67.0, 77.0),
                p25=55.0,
                median=70.0,
                p75=85.0,
            )
        ],
        ratio_intervals=ratios,
    )
    with energy_path.with_suffix(".csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    headline = next(
        row
        for row in rows
        if row["group"] == "All"
        and row["subgroup"] == "All (2008)"
        and "time" in row["quantity"].casefold()
    )
    assert float(headline["mean"]) == pytest.approx(63.1)
    time_row = next(
        row
        for row in rows
        if row["group"] == "Walking only"
        and row["subgroup"] == "2008"
        and "time" in row["quantity"].casefold()
    )
    assert float(time_row["p25"]) == pytest.approx(45.0)
    assert float(time_row["median"]) == pytest.approx(58.0)
    assert float(time_row["p75"]) == pytest.approx(70.0)
    energy_row = next(
        row
        for row in rows
        if row["group"] == "Walking only"
        and row["subgroup"] == "2008"
        and "kh" in row["quantity"].casefold()
    )
    assert float(energy_row["p25"]) == pytest.approx(80.0)
    assert float(energy_row["median"]) == pytest.approx(95.0)
    assert float(energy_row["p75"]) == pytest.approx(115.0)
    table_lines = emp._group_table_two_surveys(stats_2008, "2008", stats_2019, "2019")
    header = table_lines[0].strip("|").split("|")
    row = table_lines[2].strip("|").split("|")
    assert len(header) == len(row)
    table = dict(zip((cell.strip() for cell in header), (cell.strip() for cell in row)))
    assert table["p25 kh (2008)"] == "80.0"
    assert table["median kh (2008)"] == "95.0"
    assert table["p75 kh (2008)"] == "115.0"
    assert table["p25 time (2008)"] == "50.0"
    assert table["median time (2008)"] == "58.0"
    assert table["p75 time (2008)"] == "65.0"
    ratio_row = next(
        row
        for row in rows
        if row["group"] == "Walking only" and row["subgroup"] == "2019/2008"
    )
    assert float(ratio_row["ratio"]) == pytest.approx(1.2)
    assert float(ratio_row["ratio_ci_low"]) == pytest.approx(1.1)
    assert float(ratio_row["ratio_ci_high"]) == pytest.approx(1.3)

    time_stats_2008 = [
        SimpleNamespace(
            group="employed",
            n=60,
            mean=60.0,
            mean_ci=(55.0, 65.0),
            p25=45.0,
            median=58.0,
            p75=70.0,
        )
    ]
    time_stats_2019 = [
        SimpleNamespace(
            group="employed",
            n=60,
            mean=65.0,
            mean_ci=(60.0, 70.0),
            p25=55.0,
            median=63.0,
            p75=75.0,
        )
    ]
    budgets_2008 = [
        SimpleNamespace(group="employed", n=60, budget=50.0, budget_ci=(45.0, 55.0))
    ]
    budgets_2019 = [
        SimpleNamespace(group="employed", n=60, budget=55.0, budget_ci=(50.0, 60.0))
    ]
    category_path = emp._figure_compare_time_by_category(
        time_stats_2008,
        time_stats_2019,
        time_stats_2008,
        time_stats_2019,
        {row.group: row for row in budgets_2008},
        {row.group: row for row in budgets_2019},
        tmp_path,
        ratio_intervals={
            ("all", "employed"): (1.08, 1.02, 1.14),
            ("weekday", "employed"): (1.08, 1.02, 1.14),
            ("person", "employed"): (1.10, 1.03, 1.17),
        },
    )
    assert category_path.is_file()
    assert category_path.with_suffix(".csv").is_file()
    with category_path.with_suffix(".csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        category_rows = list(csv.DictReader(stream))
    category_row = next(
        row
        for row in category_rows
        if row["group"] == "Employed"
        and row["subgroup"] == "2008"
        and row["panel"] == "(A) All days, day with trips"
    )
    assert float(category_row["p25"]) == pytest.approx(45.0)
    assert float(category_row["median"]) == pytest.approx(58.0)
    assert float(category_row["p75"]) == pytest.approx(70.0)


#: The EMP 2019 base-case group table on the synthetic fixture (section
#: 9.9 point 1's refactor: ``emp2019.build_trip_legs`` split into
#: ``trips_norm`` + ``mobgrid.budget.trip_legs.build_trip_legs``), pinned
#: before the split (``bootstrap-reps=10``, ``seed=0``) so this test
#: fails if the refactor silently changes a single number. ``n``,
#: `weighted_n`` and every mean/median (kJ, minutes) are unaffected by
#: the split: it only moves *where* the SQL lives, not what it computes.
#: Re-pinned 22 October 2026 for the bike stop-term fix (costed at the
#: P0 flat speed, not the trip's own ride speed): only ``cycle``'s own
#: mean/median energy (and so the all-groups ``mean_kh``/``mean_cp``
#: below) changed, from 189.156/189.3728 kJ to 184.0764/184.2932 kJ.
#: Re-pinned 27 October 2026 for section 9.9's declared-legs decision:
#: ``trip_legs.build_trip_legs``'s default ``terminal_legs`` changed from
#: the section 9.4-9.7 defaults to ``'declared'`` (every fixture trip's
#: own `MTEMPSMAP`/`MTPSATTENT`, 5/2 min, both well below the former
#: density-class defaults), so every mode but ``walking_only`` (no
#: terminal legs of its own) shows a real, intentional drop.
_EXPECTED_BASE_CASE_GROUP_TABLE = {
    "car_driver": (1, 100.0, 25.0, 172.8, 176.12, 172.8, 176.12),
    "car_passenger_carpool": (1, 100.0, 25.0, 122.1, 103.5349, 122.1, 103.5349),
    "car_passenger_household": (1, 100.0, 25.0, 118.8, 100.2848, 118.8, 100.2848),
    "cycle": (2, 200.0, 15.0, 149.526, 150.068, 149.526, 150.068),
    "multimodal": (1, 100.0, 50.0, 308.3889, 285.0515, 308.3889, 285.0515),
    "train": (2, 200.0, 60.0, 193.4735, 172.6743, 147.3205, 126.5213),
    "urban_pt": (1, 100.0, 30.0, 156.5889, 136.0155, 156.5889, 136.0155),
    "walking_only": (1, 100.0, 20.0, 333.0, 254.19, 333.0, 254.19),
}


def test_refactor_preserves_emp2019_base_case_group_table(
    tmp_path: Path, synthetic_emp_zip: Path
) -> None:
    """Regression test (section 9.9 point 1): the main-mode-group table
    (point 3, section 9.9's base case, after fix 0) is bit-for-bit the
    same whether ``trip_legs`` is built as before (one EMP-2019-specific
    SQL blob) or as ``emp2019.build_trips_norm`` +
    ``trip_legs.build_trip_legs`` (shared with ENTD 2008)."""
    results = emp.run(
        tmp_path / "step11_budget",
        emp2019,
        synthetic_emp_zip,
        CONFIG_PATH,
        n_reps=10,
        seed=0,
    )
    actual = {
        s.group: (
            s.n,
            round(s.weighted_n, 3),
            round(s.mean_time_min, 4),
            round(s.mean_energy_kh_kj, 4),
            round(s.mean_energy_cp_kj, 4),
            round(s.median_energy_kh_kj, 4),
            round(s.median_energy_cp_kj, 4),
        )
        for s in results["mode_stats"]
    }
    assert actual == _EXPECTED_BASE_CASE_GROUP_TABLE
    assert results["n_days"] == 10
    assert round(results["mean_kh"], 4) == 189.7677
    assert round(results["mean_cp"], 4) == 170.0681


def test_cli_entd2008_survey_writes_report(
    tmp_path: Path, synthetic_entd2008_raw_dir: Path
) -> None:
    """``--survey entd2008`` runs the same pipeline and report/figure set
    as EMP 2019 (section 9.9, "Change between 2008 and 2019")."""
    out_dir = tmp_path / "step11_budget_entd2008"
    exit_code = emp.main(
        [
            "--out",
            str(out_dir),
            "--survey",
            "entd2008",
            "--data-path",
            str(synthetic_entd2008_raw_dir),
            "--config",
            str(CONFIG_PATH),
            "--bootstrap-reps",
            "10",
        ]
    )
    assert exit_code == 0
    assert {path.stem for path in out_dir.glob("*.csv")} == {
        path.stem for path in out_dir.glob("*.png")
    }
    md_path = out_dir.with_suffix(".md")
    report = md_path.read_text(encoding="utf-8")
    assert "ENTD 2008 re-estimation" in report
    assert "proxy" in report
    assert "`distcor`/`v2_mduree` fill rate" in report
    assert "Quintile shares and cut points" in report
    assert "Missing-income breakdown" in report
    assert "income_bracket_midpoint_eur` could not parse" in report


def test_cli_compare_writes_report_and_figure(
    tmp_path: Path,
    synthetic_emp_zip: Path,
    synthetic_entd2008_raw_dir: Path,
) -> None:
    """``--compare`` runs both surveys and writes the 2008-2019
    comparison report, without requiring the real data archives."""
    out_path = tmp_path / "step11_compare"
    exit_code = emp.main(
        [
            "--out",
            str(out_path),
            "--compare",
            "--emp2019-data-path",
            str(synthetic_emp_zip),
            "--entd2008-data-path",
            str(synthetic_entd2008_raw_dir),
            "--config",
            str(CONFIG_PATH),
            "--bootstrap-reps",
            # 3 replicates (step 12: "tests must be fast"): the compare
            # CLI runs the full pipeline three times (2008, 2019 grid,
            # 2019 proxy), so it dominates the suite's runtime.
            "3",
        ]
    )
    assert exit_code == 0
    md_path = out_path.with_suffix(".md")
    report = md_path.read_text(encoding="utf-8")
    assert "2008-2019 comparison" in report
    assert "Group table, 2008 vs 2019" in report
    assert "density grid vs proxy" in report.lower()
    assert "Robustness" in report
    assert "Weekday share of persons without trips" in report
    assert "Time budget: by population category" in report
    assert "Weekday-only comparison, 2008 vs 2019" in report
    assert "per person (days without trips included)" in report
    assert "Temporal equivalence, 2008 to 2019" in report
    assert "Ratio 2019/2008" in report
    assert "Within-survey equivalence: density proxy" in report
    assert "Within-survey equivalence: income quintile" in report


def test_scope_cli_defaults_to_reference_and_selects_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def fake_run(out_dir, survey, data_path, config_path, **kwargs):
        calls.append((out_dir, survey, kwargs["scope"].id))
        return {"figures": []}

    monkeypatch.setattr(emp, "run", fake_run)
    monkeypatch.setattr(emp, "write_markdown", lambda *args: None)

    assert emp.main(["--out", str(tmp_path / "report")]) == 0
    assert calls[-1][2] == "round-dest-local"

    assert (
        emp.main(
            [
                "--out",
                str(tmp_path / "report"),
                "--survey",
                "entd2008",
                "--scope",
                "alldays-allpurp-daytable",
            ]
        )
        == 0
    )
    assert calls[-1][1] is entd2008
    assert calls[-1][2] == "alldays-allpurp-daytable"


def test_scope_all_cli_runs_each_scope_in_separate_report_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def fake_run_compare(out_path, config_path, **kwargs):
        calls.append((out_path, kwargs["scope"].id))
        return out_path.with_suffix(".md")

    monkeypatch.setattr(emp, "run_compare", fake_run_compare)

    assert (
        emp.main(["--out", str(tmp_path / "compare"), "--compare", "--scope", "all"])
        == 0
    )

    assert [scope_id for _, scope_id in calls] == [s.id for s in scope.ALL_SCOPES]
    assert calls[0][0] == tmp_path / "scopes" / calls[0][1] / "compare"
    assert len({path for path, _ in calls}) == len(scope.ALL_SCOPES)


def test_weekday_person_table_uses_the_temporal_ratio_base() -> None:
    def results(respondent_weight: float, period_divisor: float) -> dict:
        household = np.array([f"h{i}" for i in range(60)])
        weight = np.full(60, respondent_weight)
        day_weight = np.full(60, 5.0)
        time = np.full(60, 10.0)
        categories = np.full(60, "employed")
        daily = {
            "ident_men": household,
            "pond_jour": day_weight,
            "total_time_min": time,
            "population_category": categories,
        }
        budget = daily_energy.PersonBudgetRow(
            group="overall",
            n=60,
            budget=float(np.sum(day_weight * time) / (np.sum(weight) * period_divisor)),
            budget_ci=(9.0, 11.0),
        )
        return {
            "weekday_days": daily,
            "_weekday_person_budget_days": daily,
            "_weekday_person_rows": {
                "category": categories,
                "household": household,
                "weight": weight,
                "period_divisor": period_divisor,
            },
            "person_budget_weekday_population": {
                "employed": budget,
                "overall": budget,
            },
        }

    results_2008 = results(5.0, 1.0)
    results_2019 = results(1.0, 5.0)
    ratio_rows = emp._temporal_person_budget_rows(
        results_2008, results_2019, n_reps=30, seed=3
    )
    overall_ratio = next(row for row in ratio_rows if row.category == "overall")
    report_lines = emp._format_weekday_comparison(
        results_2008, results_2019, n_reps=30, seed=3
    )
    table = "\n".join(report_lines).split(
        "### Daily time, per person (days without trips included)", 1
    )[1]
    overall_line = next(
        line for line in table.splitlines() if line.startswith("| overall |")
    )

    assert float(overall_line.split("|")[2].strip()) == pytest.approx(
        overall_ratio.estimate_2008
    )
    assert overall_ratio.estimate_2008 == pytest.approx(10.0)


def test_temporal_equivalence_uses_three_state_verdicts() -> None:
    rows = [
        emp.TemporalRatioRow("equiv", "-", 60, 60, 1.0, (0.95, 1.05)),
        emp.TemporalRatioRow("diff", "-", 60, 60, 1.2, (1.16, 1.24)),
        emp.TemporalRatioRow("uncertain", "-", 60, 60, 1.12, (1.11, 1.16)),
    ]

    lines = emp._format_temporal_ratio_table(
        rows, margin=0.15, secondary_margin=0.10, with_group=False
    )

    assert lines[2].endswith("| equivalent | equivalent |")
    assert lines[3].endswith("| different | different |")
    assert lines[4].endswith("| inconclusive | different |")


def test_daytable_temporal_comparison_reports_ratios_with_coverage_note(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section 9.9: observed coverage, not wording, permits day-table ratios."""
    monkeypatch.setattr(
        emp,
        "_format_temporal_equivalence",
        lambda *args, **kwargs: ["| Ratio 2019/2008 | 1.102 [1.082, 1.130] |"],
    )
    lines = emp._format_scope_temporal_comparison(
        scope.Scope.parse("alldays-allpurp-daytable"),
        {},
        {},
        n_reps=3,
        seed=0,
    )

    report = "\n".join(lines)
    assert "Ratio 2019/2008" in report
    assert scope.DAYTABLE_COVERAGE_NOTE in report


def test_run_compare_keeps_selected_scope_for_temporal_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    variation_config = SimpleNamespace(
        equivalence_margin=0.15,
        secondary_equivalence_margin=0.10,
    )
    results = {
        "variation_config": variation_config,
        "mode_stats": [],
        "population_stats": [],
        "density_constancy_summary": [],
        "density_equivalence": [],
        "income_equivalence": [],
        "robustness_rows": [],
        "declared_vs_modelled_walk_wait": [],
        "non_traveler_share_unweighted": 0.0,
        "non_traveler_share_weighted": 0.0,
        "non_traveler_n": 0,
        "n_respondents": 0,
        "age_eligibility": {
            "respondents": 0,
            "eligible": 0,
            "under_6": 0,
            "missing_age": 0,
        },
        "v0_overall": SimpleNamespace(speed_kmh=0.0, n=0),
        "p0_overall": SimpleNamespace(p0_w=0.0, implied_flat_speed_kmh=0.0, n=0),
        "mean_kh": 0.0,
        "mean_cp": 0.0,
        "mean_time_min": 0.0,
        "population_time_stats": [],
        "mode_time_stats": [],
        "population_time_stats_weekday": [],
        "person_budget_weekday_population": {},
        "all_days": {"typejour": np.array([], dtype=int)},
    }
    monkeypatch.setattr(emp, "run", lambda *args, **kwargs: results)
    monkeypatch.setattr(emp, "_group_table_two_surveys", lambda *args: [])
    monkeypatch.setattr(
        emp, "_format_equivalence_side_by_side", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(emp, "_format_weekday_comparison", lambda *args, **kwargs: [])
    monkeypatch.setattr(emp, "_format_temporal_equivalence", lambda *args, **kwargs: [])
    monkeypatch.setattr(emp, "_comparison_ratio_intervals", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        emp, "_person_budget_ratio_intervals", lambda *args, **kwargs: {}
    )
    monkeypatch.setattr(
        emp,
        "_figure_compare_energy_time",
        lambda *args, **kwargs: tmp_path / "compare_energy.png",
    )
    monkeypatch.setattr(
        emp,
        "_figure_compare_time_by_category",
        lambda *args, **kwargs: tmp_path / "compare_time.png",
    )
    selected_scope = scope.Scope.parse("alldays-allpurp-daytable")

    report_path = emp.run_compare(
        tmp_path / "comparison",
        scope=selected_scope,
    )

    report = report_path.read_text(encoding="utf-8")
    assert scope.DAYTABLE_COVERAGE_NOTE in report
    assert (
        "**Scope:** All days · all purposes · all trips in the day's trip table"
        in report
    )


def test_suppressed_person_budget_cell_keeps_true_n() -> None:
    rows = {
        ("unemployed", "q4"): daily_energy.PersonBudgetRow(
            group="unemployed||q4",
            n=12,
            budget=float("nan"),
            budget_ci=(float("nan"), float("nan")),
        )
    }

    lines = emp._format_person_budget_key_table(rows, ("q4",), "Income quintile")

    assert "| unemployed | q4 | 12 | - | - |" in lines


@pytest.mark.skipif(
    not _REAL_DATA_AVAILABLE,
    reason="EMP 2019 public data (data/raw/emp2019/emp2019-data.zip) is absent",
)
def test_real_emp_2019_mean_daily_energy_is_within_kh_order_of_magnitude(
    tmp_path: Path,
) -> None:
    """A loose sanity check on real data: the overall weighted mean daily
    energy should be the same order of magnitude as Koelbl & Helbing's
    (2003) ~615 kJ hypothesis, not a wildly different unit-conversion bug."""
    results = emp.run(tmp_path / "step11_budget", n_reps=20)
    assert 300.0 < results["mean_kh"] < 1200.0
    assert 300.0 < results["mean_cp"] < 1200.0
    assert results["n_days"] > 1000
