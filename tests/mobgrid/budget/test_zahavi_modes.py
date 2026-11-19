"""Synthetic acceptance tests for the Zahavi mode supplement."""

from pathlib import Path

import duckdb
import numpy as np
import pytest
from mobgrid.budget import modes_cache, scope
from mobgrid.budget import zahavi_modes as modes


def test_distribution_shared_bandwidth_and_weighted_ecdf() -> None:
    """Section 9.9: the two years share a bandwidth and use day weights."""
    first = modes.Observations(
        values=np.array([5.0, 10.0, 30.0]),
        weights=np.array([1.0, 2.0, 1.0]),
        household=np.array(["a", "b", "c"]),
    )
    second = modes.Observations(
        values=np.array([10.0, 20.0]),
        weights=np.array([1.0, 1.0]),
        household=np.array(["d", "e"]),
    )
    rows = modes.distribution_rows(
        {("trip", "walk"): first},
        {("trip", "walk"): second},
        trip_max=30,
        day_max=40,
        minimum_n=1,
    )
    a = next(row for row in rows if row["year"] == 2008 and row["minute"] == 10)
    b = next(row for row in rows if row["year"] == 2019 and row["minute"] == 10)
    assert a["ecdf"] == pytest.approx(0.75)
    assert b["ecdf"] == pytest.approx(0.5)
    assert a["bandwidth"] == b["bandwidth"]
    assert a["bandwidth"] > 0


def test_distributions_hide_small_cells() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0]),
        weights=np.array([1.0, 1.0]),
        household=np.array(["a", "b"]),
    )
    rows = modes.distribution_rows(
        {("trip", "walk"): sample},
        {("trip", "walk"): sample},
        trip_max=2,
        day_max=2,
        minimum_n=3,
    )
    assert all(row["n"] == 2 and row["ecdf"] is None for row in rows)


def test_read_samples_distinguishes_mode_use_and_day_group(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute("""
            COPY (SELECT * FROM (VALUES
              ('d1', 'h1', 2.0, 'walk', 5.0),
              ('d1', 'h1', 2.0, 'car_driver', 20.0),
              ('d1', 'h1', 2.0, 'car_driver', 10.0)
            ) t(day_id, ident_men, pond_jour, mode7, duration_min))
            TO ? (FORMAT PARQUET)
        """, [str(cache.trips(scope.REFERENCE_SCOPE))])
        con.execute("""
            COPY (SELECT 'h1' ident_men, 2.0 pond_jour,
                         'car_driver' day_mode_group, 35.0 total_time_min)
            TO ? (FORMAT PARQUET)
        """, [str(cache.days(scope.REFERENCE_SCOPE))])
    samples = modes.read_samples(cache, scope.REFERENCE_SCOPE)
    assert samples["trip", "car_driver"].values.tolist() == [20.0, 10.0]
    assert samples["mode_user_day", "car_driver"].values.tolist() == [30.0]
    assert samples["day_mode_group", "car_driver"].values.tolist() == [35.0]


def test_weighted_deciles_and_thresholds_against_brute_force() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 10.0, 30.0]),
        weights=np.array([1.0, 1.0, 1.0, 1.0]),
        household=np.array(["a", "b", "c", "d"]),
    )
    probabilities = np.arange(1, 10) / 10
    expected = np.interp(probabilities, [0.25, 0.75, 1.0], [5, 10, 30])
    assert modes.weighted_deciles(sample, probabilities) == pytest.approx(expected)
    assert modes.threshold_shares(sample, [10, 30]) == pytest.approx([0.75, 0.25])


def test_weighted_ks_is_zero_for_identical_samples() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 10.0, 30.0]),
        weights=np.array([1.0, 1.0, 1.0, 1.0]),
        household=np.array(["a", "b", "c", "d"]),
    )
    assert modes.weighted_ks(sample, sample) == pytest.approx(0.0)


def test_rounded_short_intercommunal_trip_stays_out_of_same_commune() -> None:
    bands = modes.crow_fly_bands(np.array([0.0, 0.4, 1.6, 2.0]), rounded=True)
    assert bands.tolist() == ["same commune", "under 2 km", "2-5 km", "2-5 km"]


def test_comparison_outputs_and_suppression() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 30.0]),
        weights=np.array([1.0, 2.0, 1.0]),
        household=np.array(["a", "b", "c"]),
    )
    draws = modes.make_draws(sample.household, n_reps=20, seed=7)
    inputs = {("trip", "walk"): sample}
    deciles, thresholds, ks = modes.comparison_rows(
        inputs, inputs, draws, draws, thresholds=[10], minimum_n=1
    )
    assert deciles[4]["shift"] == pytest.approx(0)
    assert deciles[4]["ci_low"] == pytest.approx(0)
    assert thresholds[0]["share_2008"] == pytest.approx(0.75)
    assert thresholds[0]["change_points"] == pytest.approx(0)
    assert ks[0]["D"] == pytest.approx(0)
    deciles, thresholds, ks = modes.comparison_rows(
        inputs, inputs, draws, draws, thresholds=[10], minimum_n=4
    )
    assert np.isnan(deciles[0]["interpolated_2008"])
    assert np.isnan(thresholds[0]["change_points"])
    assert np.isnan(ks[0]["D"])


def test_person_mode_minutes_sum_to_total_with_open_and_zero_days(
    tmp_path: Path,
) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute("""
            COPY (SELECT * FROM (VALUES
              ('h1', 10.0), ('h2', 10.0)
            ) t(ident_men, weight)) TO ? (FORMAT PARQUET)
        """, [str(cache.roster)])
        con.execute("""
            COPY (SELECT * FROM (VALUES
              ('d1', 'h1', 2.0, TRUE), ('d2', 'h1', 2.0, FALSE)
            ) t(day_id, ident_men, pond_jour, is_round)) TO ? (FORMAT PARQUET)
        """, [str(cache.day_base)])
        con.execute("""
            COPY (SELECT * FROM (VALUES
              ('d1', 'walk', 10.0), ('d1', 'car_driver', 20.0)
            ) t(day_id, mode7, duration_min)) TO ? (FORMAT PARQUET)
        """, [str(cache.trips(scope.REFERENCE_SCOPE))])
    draws = modes.make_draws(np.array(["h1", "h2"]), n_reps=20, seed=3)
    metrics = modes.person_mode_metrics(cache, scope.REFERENCE_SCOPE, draws)
    assert metrics["walk"].value == pytest.approx(20 / 18)
    assert metrics["car_driver"].value == pytest.approx(40 / 18)
    assert sum(metrics[mode].value for mode in modes.vr.MODE7_LABELS) == pytest.approx(
        metrics["All"].value
    )
    assert sum(metrics[mode].replicates for mode in modes.vr.MODE7_LABELS) == (
        pytest.approx(metrics["All"].replicates)
    )


def test_mode_shares_use_trip_and_minute_weights() -> None:
    samples = {
        ("trip", "walk"): modes.Observations(
            np.array([10.0, 20.0]), np.array([1.0, 2.0]), np.array(["a", "b"])
        ),
        ("trip", "car_driver"): modes.Observations(
            np.array([30.0]), np.array([1.0]), np.array(["c"])
        ),
    }
    trip_share, minute_share, n = modes.mode_shares(samples, "walk")
    assert n == 2
    assert trip_share == pytest.approx(3 / 4)
    assert minute_share == pytest.approx(50 / 80)
