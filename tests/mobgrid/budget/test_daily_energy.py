"""Unit tests for the day-level aggregation and hypothesis test
(section 9.9, step 11).

Uses the synthetic archive (``synthetic_emp_zip``, ``conftest.py``) for the
DuckDB aggregation, and plain numpy arrays for the statistics helpers.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pytest
from mobgrid.budget import daily_energy, emp2019
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"


@pytest.fixture
def day_summary(tmp_path: Path, synthetic_emp_zip: Path) -> duckdb.DuckDBPyConnection:
    config = load_energy_config(CONFIG_PATH)
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(synthetic_emp_zip, tmp_path / "csv")
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)
    daily_energy.create_day_summary(con)
    daily_energy.create_non_travelers(con)
    return con


def test_single_trip_days_are_classified_by_their_only_mode(
    day_summary: duckdb.DuckDBPyConnection,
) -> None:
    rows = dict(
        day_summary.sql(
            "SELECT ident_ind, day_mode_group FROM day_summary "
            "WHERE ident_ind IN (1, 2, 3, 6, 7, 11)"
        ).fetchall()
    )
    assert rows == {
        1: "walking_only",
        2: "cycle",
        3: "car_driver",
        6: "urban_pt",
        7: "train",
        11: "train",
    }


def test_two_non_walk_modes_in_one_day_are_multimodal(
    day_summary: duckdb.DuckDBPyConnection,
) -> None:
    group = day_summary.sql(
        "SELECT day_mode_group FROM day_summary WHERE ident_ind = 9"
    ).fetchone()[0]
    assert group == "multimodal"


def test_car_passenger_household_and_carpool_are_distinct_day_groups(
    day_summary: duckdb.DuckDBPyConnection,
) -> None:
    rows = dict(
        day_summary.sql(
            "SELECT ident_ind, day_mode_group FROM day_summary "
            "WHERE ident_ind IN (4, 5)"
        ).fetchall()
    )
    assert rows == {4: "car_passenger_household", 5: "car_passenger_carpool"}


def test_other_only_day_is_its_own_group_not_multimodal(
    day_summary: duckdb.DuckDBPyConnection,
) -> None:
    group = day_summary.sql(
        "SELECT day_mode_group FROM day_summary WHERE ident_ind = 8"
    ).fetchone()[0]
    assert group == "other"


def test_respondent_with_no_trip_is_a_non_traveler(
    day_summary: duckdb.DuckDBPyConnection,
) -> None:
    assert day_summary.sql(
        "SELECT count(*) FROM day_summary WHERE ident_ind = 10"
    ).fetchone()[0] == 0
    assert day_summary.sql(
        "SELECT count(*) FROM non_travelers WHERE ident_ind = 10"
    ).fetchone()[0] == 1


def test_gamma_moments_fit_recovers_mean_and_variance() -> None:
    mean, variance = 600.0, 200.0**2
    shape, scale = daily_energy.gamma_moments_fit(mean, variance)
    assert shape * scale == pytest.approx(mean)
    assert shape * scale**2 == pytest.approx(variance)


def test_gamma_moments_fit_rejects_non_positive_inputs() -> None:
    with pytest.raises(ValueError):
        daily_energy.gamma_moments_fit(0.0, 1.0)
    with pytest.raises(ValueError):
        daily_energy.gamma_moments_fit(1.0, 0.0)


def test_weighted_mean_variance_matches_equal_weight_numpy() -> None:
    values = np.array([100.0, 200.0, 300.0, 400.0])
    weights = np.ones_like(values)
    mean, variance = daily_energy.weighted_mean_variance(weights, values)
    assert mean == pytest.approx(values.mean())
    assert variance == pytest.approx(values.var())


def test_bootstrap_group_stats_point_estimate_matches_direct_computation() -> None:
    group = np.array(["a", "a", "b", "b"])
    household = np.array([1, 2, 3, 4])
    weight = np.array([1.0, 1.0, 1.0, 1.0])
    time_min = np.array([10.0, 20.0, 30.0, 40.0])
    energy_kh = np.array([100.0, 200.0, 300.0, 400.0])
    energy_cp = np.array([90.0, 180.0, 270.0, 360.0])

    stats = daily_energy.bootstrap_group_stats(
        group, household, weight, time_min, energy_kh, energy_cp, n_reps=50, seed=1,
    )
    by_group = {s.group: s for s in stats}

    assert by_group["a"].mean_energy_kh_kj == pytest.approx(150.0)
    assert by_group["b"].mean_energy_kh_kj == pytest.approx(350.0)
    assert by_group["a"].n == 2
    assert by_group["a"].weighted_n == pytest.approx(2.0)
    # Equal weights, 2 rows per group: the weighted median is the lower
    # of the two values (cumulative weight reaches half there first).
    assert by_group["a"].median_energy_kh_kj == pytest.approx(100.0)
    assert by_group["b"].median_energy_kh_kj == pytest.approx(300.0)
    assert by_group["a"].median_time_min == pytest.approx(10.0)
    # The CI must bracket the point estimate it is centred on.
    assert by_group["a"].mean_energy_kh_ci[0] <= by_group["a"].mean_energy_kh_kj
    assert by_group["a"].mean_energy_kh_ci[1] >= by_group["a"].mean_energy_kh_kj


def test_bootstrap_mean_ci_matches_direct_weighted_mean() -> None:
    household = np.array([1, 2, 3, 4])
    weight = np.array([1.0, 1.0, 1.0, 1.0])
    value = np.array([2.0, 4.0, 6.0, 8.0])
    mean, ci = daily_energy.bootstrap_mean_ci(
        household, weight, value, n_reps=50, seed=2
    )
    assert mean == pytest.approx(5.0)
    assert ci[0] <= mean <= ci[1]


def test_weighted_gaussian_kde_integrates_to_one() -> None:
    rng = np.random.default_rng(0)
    samples = rng.normal(size=2000)
    weights = np.ones_like(samples)
    bandwidth = daily_energy.weighted_gaussian_bandwidth(weights, samples)
    grid = np.linspace(samples.min() - 1, samples.max() + 1, 500)
    density = daily_energy.weighted_gaussian_kde(grid, samples, weights, bandwidth)
    integral = np.trapezoid(density, grid)
    assert integral == pytest.approx(1.0, abs=0.02)


def test_robustness_row_ratio_and_cv() -> None:
    group = np.array(["walking_only", "walking_only", "cycle", "cycle"])
    weight = np.ones(4)
    time_min = np.array([10.0, 10.0, 20.0, 20.0])
    energy_kh = np.array([100.0, 100.0, 200.0, 200.0])
    energy_cp = np.array([90.0, 90.0, 180.0, 180.0])
    row = daily_energy.robustness_row(
        "test", group, weight, time_min, energy_kh, energy_cp
    )
    assert row.scope == "full"
    assert row.statistic == "mean"
    assert row.energy_kh_ratio == pytest.approx(2.0)
    assert row.energy_cp_ratio == pytest.approx(2.0)
    assert row.time_ratio == pytest.approx(2.0)
    assert row.energy_kh_min_group == "walking_only"
    assert row.energy_kh_max_group == "cycle"
    assert row.energy_cp_min_group == "walking_only"
    assert row.energy_cp_max_group == "cycle"
    assert row.time_min_group == "walking_only"
    assert row.time_max_group == "cycle"


def test_robustness_row_median_statistic() -> None:
    # Median of {100, 300} is 100 (lower value), of {200, 600} is 200.
    group = np.array(["walking_only", "walking_only", "cycle", "cycle"])
    weight = np.ones(4)
    time_min = np.array([10.0, 10.0, 20.0, 20.0])
    energy_kh = np.array([100.0, 300.0, 200.0, 600.0])
    energy_cp = np.array([90.0, 270.0, 180.0, 540.0])
    row = daily_energy.robustness_row(
        "test", group, weight, time_min, energy_kh, energy_cp, statistic="median",
    )
    assert row.statistic == "median"
    assert row.energy_kh_ratio == pytest.approx(2.0)
    assert row.energy_kh_min_group == "walking_only"
    assert row.energy_kh_max_group == "cycle"


def test_robustness_row_core_scope_restricts_groups() -> None:
    group = np.array(["walking_only", "walking_only", "cycle", "cycle"])
    weight = np.ones(4)
    time_min = np.array([10.0, 10.0, 20.0, 20.0])
    energy_kh = np.array([100.0, 100.0, 200.0, 200.0])
    energy_cp = np.array([90.0, 90.0, 180.0, 180.0])
    row = daily_energy.robustness_row(
        "test", group, weight, time_min, energy_kh, energy_cp,
        scope="core", groups_of_interest=("walking_only",),
    )
    assert row.scope == "core"
    # Only one group left: ratio/CV of a single value are 1.0/0.0.
    assert row.energy_kh_ratio == pytest.approx(1.0)
    assert row.energy_kh_cv == pytest.approx(0.0)
    assert row.energy_kh_min_group == row.energy_kh_max_group == "walking_only"

