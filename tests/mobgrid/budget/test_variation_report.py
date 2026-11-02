"""Tests for the step-12 variation report (``mobgrid.budget.
variation_report``): Part A tables on tiny in-memory frames, and the
end-to-end CLI on the synthetic archives (3 bootstrap replicates, so
every test stays well under 10 s)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from mobgrid.budget import variation_report
from mobgrid.budget.variation_report import SurveyFrames

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"

N_REPS = 3


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
        "total_time_min": [30.0 * scale + (i % 3) for i in range(n)],
        "population_category": [category] * n,
        "ident_men": [f"M{i // 2}" for i in range(n)],
    }
    return _frames(days, {})


def test_b2_decompositions_cover_overall_and_categories() -> None:
    frames_a = _b2_frames(1.0)
    frames_b = _b2_frames(1.2)

    rows = variation_report.b2_decompositions(frames_a, frames_b, n_reps=N_REPS, seed=0)

    by_group = {row.group: row for row in rows}
    overall = by_group["overall"].result
    assert overall is not None
    point = overall.point
    assert point.delta_min == pytest.approx(
        point.trips_min + point.distance_min + point.speed_min
    )
    assert by_group["employed"].n_a == 60
    assert by_group["employed"].result is not None
    # A category absent from both surveys has no decomposition.
    assert by_group["retired"].result is None

    lines = variation_report._format_b2(rows, "2008", "2019")
    text = "\n".join(lines)
    assert "B2. Trips x distance x speed" in text
    assert "| overall | 60 | 60 |" in text
    # Absent categories keep their true n with dashes.
    assert "| retired | 0 | 0 | - | - | - | - | - | - |" in text


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


def test_cli_writes_report_on_synthetic_data(
    tmp_path: Path, synthetic_emp_zip: Path, synthetic_entd2008_raw_dir: Path
) -> None:
    out_dir = tmp_path / "step12_variation"
    exit_code = variation_report.main(
        [
            "--out",
            str(out_dir),
            "--emp2019-data-path",
            str(synthetic_emp_zip),
            "--entd2008-data-path",
            str(synthetic_entd2008_raw_dir),
            "--config",
            str(CONFIG_PATH),
            "--bootstrap-reps",
            str(N_REPS),
        ]
    )

    assert exit_code == 0
    md_path = out_dir.with_suffix(".md")
    report = md_path.read_text(encoding="utf-8")
    assert "Choices made" in report
    assert "A1. Recall lag" in report
    assert "A2. Motive crosswalk" in report
    assert "A3. Distances" in report
    assert "ENTD 2008" in report and "EMP 2019, lag 1" in report
    assert "80-km check" in report
