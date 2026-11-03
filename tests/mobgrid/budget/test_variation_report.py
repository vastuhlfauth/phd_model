"""Tests for the step-12 variation report (``mobgrid.budget.
variation_report``): Part A tables on tiny in-memory frames, and the
end-to-end CLI on the synthetic archives (3 bootstrap replicates, so
every test stays well under 10 s)."""

from __future__ import annotations

from pathlib import Path

import duckdb
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
    # Absent categories keep their true n with dashes.
    assert "| retired | 0 | 0 | - | - | - | - | - | - |" in text


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
    assert employed_time.endswith("| 1.120 | [1.120, 1.120] | yes | no |"), (
        employed_time
    )


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


def test_frame_aggregation_keeps_missing_distance_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section 9.9: N/T include all trips, L/v only distance-known trips."""
    monkeypatch.setattr(variation_report.trip_legs, "NEEDS_ONLY_WHERE_SQL", "TRUE")
    with duckdb.connect() as con:
        con.sql("""
            CREATE TABLE trip_legs AS SELECT
                day_id, ident_dep, distance_km, duration_min,
                day_id AS ident_ind, day_id AS ident_men,
                CASE WHEN day_id = 'a' THEN 1.0 ELSE 3.0 END AS pond_jour,
                'employed' AS population_category, 'dense' AS residence_density,
                'q1' AS income_quintile, 40 AS age, 'walk' AS mode_group,
                2 AS motive, 1 AS typejour
            FROM (VALUES ('a', 'd1', 6.0, 10.0), ('a', 'd2', NULL, 30.0),
                         ('b', 'd3', NULL, 20.0))
                v(day_id, ident_dep, distance_km, duration_min);
            CREATE VIEW vr_person AS SELECT DISTINCT ident_ind, 1 AS sex,
                1 AS recall_lag, 'lundi' AS described_weekday_name,
                'janvier' AS described_month_name, FALSE AS is_idf,
                '1' AS cars_band FROM trip_legs;
            CREATE VIEW vr_trip_ext AS SELECT ident_dep,
                NULL::DOUBLE AS crow_fly_km, NULL::DOUBLE AS declared_km,
                0 AS vac_scol FROM trip_legs;
        """)
        variation_report._create_frames_tables(con, sample_pct=None)
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


def test_cli_writes_report_on_synthetic_data(
    tmp_path: Path,
    synthetic_emp_zip: Path,
    synthetic_entd2008_raw_dir: Path,
    synthetic_entd2008_zoning_dir: Path,
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
            "--entd2008-zoning-data-path",
            str(synthetic_entd2008_zoning_dir),
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
    assert "B6.4. Density and income together" in report
    assert "## Figures" in report
    assert "described-day weekday" in report
    assert "arrival minus departure" in report
    assert "distance-known trips" in report
    assert "median min/trip 2008" in report
    assert "raw crow-fly distances (`V2_DVO_LOC` for ENTD 2008" in report
    assert "B2 sensitivity: corrected distances" in report
    assert "MDISTTOT_fin" in report
    assert "Time ratio 2019/2008" in report
    assert "Equivalent at ±15%" in report
    assert "Equivalent at ±10%" in report
    assert "## C. Measurement checks" in report
    assert "C1. Rounding bounds" in report
    assert "20 draws" in report
    assert "Simulated 2008 share" in report
    assert "C2. Common distance measures" in report
    assert "No speed correction" in report
    c2 = report.split("### C2. Common distance measures", 1)[1].split(
        "### C3. Trips by motive", 1
    )[0]
    assert "dVO_ORIDES" in c2
    assert "declared" not in c2
    assert "C3. Trips by motive" in report
    assert "motive coding, not behaviour" in report
    assert "C3 sensitivity: EMP 2019 producer sequence motive" in report
    assert "MOT_SEQ_COMPL" in report
    assert "trips under 1 km (crow-fly)" in report
    assert "B6.5. 2008 -> 2019 by INSEE density grid" in report
    assert (out_dir / "fig_b7a_waterfall.png").is_file()
    assert (out_dir / "fig_b7b_shift_share.png").is_file()
    assert (out_dir / "fig_b7c_recall_lag.png").is_file()


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
