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

import pytest
from mobgrid.budget import emp, emp2019

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
    # F1, F2, F2b, F3 x4 (incl. KH appendix), F4a/b, F5, F6, F7, F8, F9 (motive).
    assert len(png_files) == 14
    assert any("f09_motive_energy" in p.name for p in png_files)
    assert any("f02_time_density_by_category" in p.name for p in png_files)
    assert any("f02b_time_heatmap_category_density" in p.name for p in png_files)

    md_path = out_dir.with_suffix(".md")
    assert md_path.is_file()
    report = md_path.read_text(encoding="utf-8")
    assert "Mean daily energy and time by main-mode group" in report
    assert "Calibrated v0 and P0" in report
    assert "car_passenger_household" in report
    assert "F8 robustness" in report
    assert "Density classes" in report
    assert "Time budget: constancy across density classes" in report


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
    "cycle": (1, 100.0, 15.0, 149.526, 150.068, 149.526, 150.068),
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
    assert results["n_days"] == 9
    assert round(results["mean_kh"], 4) == 194.239
    assert round(results["mean_cp"], 4) == 172.2904


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
            "10",
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
