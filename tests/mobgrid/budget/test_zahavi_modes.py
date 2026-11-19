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
