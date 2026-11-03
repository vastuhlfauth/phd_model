"""Acceptance tests for the step-12 travel-time decomposition."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from mobgrid.budget.variation import (
    PersonDays,
    bootstrap_decompose,
    decompose,
    load_variation_config,
)

ROOT = Path(__file__).resolve().parents[3]


def _person_days(
    weight: list[float],
    trips: list[float],
    distance_km: list[float],
    time_min: list[float],
    household: list[str] | None = None,
) -> PersonDays:
    return PersonDays(
        weight=np.asarray(weight),
        trips=np.asarray(trips),
        distance_km=np.asarray(distance_km),
        time_min=np.asarray(time_min),
        household=None if household is None else np.asarray(household),
    )


def test_log_decomposition_returns_minutes_and_sums_exactly() -> None:
    group_a = _person_days([1.0, 3.0], [1.0, 2.0], [2.0, 8.0], [20.0, 40.0])
    group_b = _person_days([2.0, 1.0], [2.0, 3.0], [6.0, 12.0], [32.0, 45.0])

    result = decompose(group_a, group_b)

    assert result.time_a_min == pytest.approx(35.0)
    assert result.time_b_min == pytest.approx(109.0 / 3.0)
    assert result.delta_min == pytest.approx(result.time_b_min - result.time_a_min)
    assert (result.trips_min + result.distance_min + result.speed_min) == pytest.approx(
        result.delta_min
    )


def test_log_decomposition_exposes_the_weighted_total_identities() -> None:
    group_a = _person_days([1.0, 1.0], [1.0, 2.0], [1.0, 4.0], [10.0, 20.0])
    group_b = _person_days([1.0, 2.0], [2.0, 3.0], [4.0, 12.0], [20.0, 30.0])

    result = decompose(group_a, group_b)

    assert result.time_a_min == pytest.approx(
        result.trips_a * result.distance_a_km / result.speed_a_km_per_min
    )
    assert result.time_b_min == pytest.approx(
        result.trips_b * result.distance_b_km / result.speed_b_km_per_min
    )
    assert (result.trips_min + result.distance_min + result.speed_min) == pytest.approx(
        result.delta_min
    )


def test_log_decomposition_rejects_empty_or_nonpositive_metrics() -> None:
    empty = _person_days([], [], [], [])
    valid = _person_days([1.0], [1.0], [1.0], [10.0])

    with pytest.raises(ValueError):
        decompose(empty, valid)

    zero_distance = _person_days([1.0], [1.0], [0.0], [10.0])
    with pytest.raises(ValueError):
        decompose(zero_distance, valid)


def test_log_decomposition_bootstraps_independent_households() -> None:
    group_a = _person_days(
        [1.0, 1.0, 2.0, 2.0],
        [1.0, 2.0, 1.0, 3.0],
        [2.0, 5.0, 3.0, 9.0],
        [20.0, 35.0, 24.0, 54.0],
        ["a", "a", "b", "b"],
    )
    group_b = _person_days(
        [1.0, 2.0, 1.0, 2.0],
        [2.0, 3.0, 2.0, 4.0],
        [4.0, 9.0, 6.0, 12.0],
        [28.0, 50.0, 36.0, 60.0],
        ["c", "c", "d", "d"],
    )

    result = bootstrap_decompose(group_a, group_b, n_reps=40, seed=7)
    repeated = bootstrap_decompose(group_a, group_b, n_reps=40, seed=7)

    assert result == repeated
    assert result.point.delta_min == pytest.approx(
        result.point.trips_min + result.point.distance_min + result.point.speed_min
    )
    assert result.delta_ci[0] <= result.point.delta_min <= result.delta_ci[1]
    for interval in (
        result.trips_ci,
        result.distance_ci,
        result.speed_ci,
    ):
        assert len(interval) == 2
        assert np.isfinite(interval).all()


def test_log_decomposition_bootstrap_requires_household_ids() -> None:
    group = _person_days([1.0], [1.0], [1.0], [10.0])

    with pytest.raises(ValueError, match="household"):
        bootstrap_decompose(group, group, n_reps=10)


def test_distance_complete_metrics_keep_all_trip_time_and_bootstrap() -> None:
    """Section 9.9: missing distances must not remove trips or their time."""
    a = PersonDays(
        weight=np.array([1.0, 3.0]),
        trips=np.array([2.0, 2.0]),
        distance_km=np.array([6.0, 0.0]),
        time_min=np.array([40.0, 20.0]),
        household=np.array(["a", "b"]),
        distance_trips=np.array([1.0, 0.0]),
        distance_time_min=np.array([10.0, 0.0]),
    )
    b = PersonDays(
        weight=np.ones(2),
        trips=np.full(2, 2.0),
        distance_km=np.full(2, 12.0),
        time_min=np.full(2, 60.0),
        household=np.array(["c", "d"]),
        distance_trips=np.ones(2),
        distance_time_min=np.full(2, 20.0),
    )
    result = bootstrap_decompose(a, b, n_reps=12, seed=7)
    point = result.point
    assert point.time_a_min == pytest.approx(25.0)
    assert point.trips_a == pytest.approx(2.0)
    assert point.distance_a_km == pytest.approx(6.0)
    assert point.speed_a_km_per_min == pytest.approx(0.6)
    assert point.distance_share_a == pytest.approx(1 / 8)
    assert point.distance_share_b == pytest.approx(0.5)
    assert point.delta_min == pytest.approx(
        point.trips_min + point.distance_min + point.speed_min + point.selection_min
    )
    assert np.isfinite(result.selection_ci).all()


def test_variation_config_has_the_requested_equivalence_margins() -> None:
    config = load_variation_config(ROOT / "config" / "variation.yaml")

    assert config.equivalence_margin == pytest.approx(0.15)
    assert config.secondary_equivalence_margin == pytest.approx(0.10)
    assert config.measurement.rounding_draws == 20
    assert config.measurement.rounding_levels == (1, 5, 15, 30)


def test_variation_config_rejects_invalid_margins(tmp_path: Path) -> None:
    path = tmp_path / "variation.yaml"
    path.write_text(
        "equivalence_margin: 1.0\nsecondary_equivalence_margin: 0.1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_variation_config(path)
