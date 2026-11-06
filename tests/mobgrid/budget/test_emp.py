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

from pathlib import Path

import numpy as np
import pytest
from mobgrid.budget import daily_energy, emp, emp2019, entd2008, scope

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"
_REAL_DATA_AVAILABLE = emp2019.DEFAULT_ZIP_PATH.is_file()


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
    png_files = sorted(out_dir.glob("*.png"))
    # F1, F1b, F1c, F2a, F2b, F3 x4 (incl. KH appendix), F4a/b, F5, F5b,
    # F6, F7, F8, F9 (motive), F10.
    assert len(png_files) == 18
    assert any("f09_motive_energy" in p.name for p in png_files)
    assert any("f01b_trips_per_day_by_category" in p.name for p in png_files)
    assert any("f01c_minutes_per_trip_by_category" in p.name for p in png_files)
    assert any("f02a_time_density_overall" in p.name for p in png_files)
    assert any("f02b_time_density_by_category" in p.name for p in png_files)
    assert any("f05b_time_heatmaps" in p.name for p in png_files)
    assert any("f10_constancy" in p.name for p in png_files)

    md_path = out_dir.with_suffix(".md")
    assert md_path.is_file()
    report = md_path.read_text(encoding="utf-8")
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
    assert (out_path / "compare_energy_time.png").is_file()
    assert (out_path / "compare_time_by_category.png").is_file()
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

    assert emp.main(
        ["--out", str(tmp_path / "report"), "--survey", "entd2008",
         "--scope", "alldays-allpurp-daytable"]
    ) == 0
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

    assert emp.main(
        ["--out", str(tmp_path / "compare"), "--compare", "--scope", "all"]
    ) == 0

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
            budget=float(
                np.sum(day_weight * time) / (np.sum(weight) * period_divisor)
            ),
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
