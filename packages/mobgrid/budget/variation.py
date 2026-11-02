"""Step-12 travel-time variation analyses and their configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict, Field


class VariationConfig(BaseModel):
    """Equivalence margins for the step-12 report."""

    model_config = ConfigDict(extra="forbid")

    equivalence_margin: Annotated[float, Field(gt=0, lt=1)]
    secondary_equivalence_margin: Annotated[float, Field(gt=0, lt=1)]


def load_variation_config(path: str | Path) -> VariationConfig:
    """Load and validate the step-12 reporting parameters."""
    with Path(path).open(encoding="utf-8") as stream:
        return VariationConfig.model_validate(yaml.safe_load(stream))


@dataclass(frozen=True)
class PersonDays:
    """Weighted daily totals for a group of weekday person-days."""

    weight: np.ndarray
    trips: np.ndarray
    distance_km: np.ndarray
    time_min: np.ndarray
    household: np.ndarray | None = None


@dataclass(frozen=True)
class TripTimeDecomposition:
    """Weighted daily time and its trips, distance, and speed components,
    all in minutes."""

    time_a_min: float
    time_b_min: float
    delta_min: float
    trips_a: float
    trips_b: float
    distance_a_km: float
    distance_b_km: float
    speed_a_km_per_min: float
    speed_b_km_per_min: float
    trips_min: float
    distance_min: float
    speed_min: float


@dataclass(frozen=True)
class TripTimeDecompositionBootstrap:
    """Point decomposition and percentile 95% household-bootstrap intervals."""

    point: TripTimeDecomposition
    delta_ci: tuple[float, float]
    trips_ci: tuple[float, float]
    distance_ci: tuple[float, float]
    speed_ci: tuple[float, float]


def _weighted_metrics(days: PersonDays) -> tuple[float, float, float, float]:
    arrays = (days.weight, days.trips, days.distance_km, days.time_min)
    if len({len(array) for array in arrays}) != 1 or len(days.weight) == 0:
        raise ValueError("person-day arrays must have equal, non-zero lengths")
    weight = np.asarray(days.weight, dtype=float)
    trips = np.asarray(days.trips, dtype=float)
    distance = np.asarray(days.distance_km, dtype=float)
    time = np.asarray(days.time_min, dtype=float)
    if not all(np.isfinite(array).all() for array in (weight, trips, distance, time)):
        raise ValueError("person-day metrics must be finite")
    if np.any(weight < 0) or weight.sum() <= 0:
        raise ValueError("person-day weights must be non-negative and non-zero")
    if np.any(trips < 0) or np.any(distance < 0) or np.any(time < 0):
        raise ValueError(
            "person-day trip, distance, and time totals must be non-negative"
        )
    weighted_trips = float(np.sum(weight * trips))
    weighted_distance = float(np.sum(weight * distance))
    weighted_time = float(np.sum(weight * time))
    if min(weighted_trips, weighted_distance, weighted_time) <= 0:
        raise ValueError("groups must have positive weighted trips, distance, and time")
    total_weight = float(weight.sum())
    return (
        weighted_time / total_weight,
        weighted_trips / total_weight,
        weighted_distance / weighted_trips,
        weighted_distance / weighted_time,
    )


def decompose(a: PersonDays, b: PersonDays) -> TripTimeDecomposition:
    """Decompose the change in weighted daily time into trips, distance,
    and speed terms using ratios of weighted totals.

    The minutes are ``ΔT × Δln(component) / Δln(T)``. When ``Δln(T)``
    is zero, the logarithmic-mean limit is used; the components still
    sum exactly to the zero change.
    """
    time_a, trips_a, distance_a, speed_a = _weighted_metrics(a)
    time_b, trips_b, distance_b, speed_b = _weighted_metrics(b)
    log_delta_time = float(np.log(time_b / time_a))
    log_delta_trips = float(np.log(trips_b / trips_a))
    log_delta_distance = float(np.log(distance_b / distance_a))
    log_delta_speed = float(np.log(speed_b / speed_a))
    log_mean_time = (
        (time_b - time_a) / log_delta_time
        if not np.isclose(log_delta_time, 0.0, atol=1e-14)
        else time_a
    )
    return TripTimeDecomposition(
        time_a_min=time_a,
        time_b_min=time_b,
        delta_min=time_b - time_a,
        trips_a=trips_a,
        trips_b=trips_b,
        distance_a_km=distance_a,
        distance_b_km=distance_b,
        speed_a_km_per_min=speed_a,
        speed_b_km_per_min=speed_b,
        trips_min=log_mean_time * log_delta_trips,
        distance_min=log_mean_time * log_delta_distance,
        speed_min=-log_mean_time * log_delta_speed,
    )


def bootstrap_decompose(
    a: PersonDays,
    b: PersonDays,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> TripTimeDecompositionBootstrap:
    """Bootstrap the decomposition with independent household samples.

    Each survey draws its households independently with replacement.
    Intervals are percentile 95% CIs of the resulting minutes.
    """
    if n_reps <= 0:
        raise ValueError("n_reps must be positive")
    point = decompose(a, b)
    if a.household is None or b.household is None:
        raise ValueError("household identifiers are required for bootstrap")
    if len(a.household) != len(a.weight) or len(b.household) != len(b.weight):
        raise ValueError("household identifiers must match the person-day rows")

    households_a, codes_a = np.unique(a.household, return_inverse=True)
    households_b, codes_b = np.unique(b.household, return_inverse=True)
    if len(households_a) == 0 or len(households_b) == 0:
        raise ValueError("household identifiers are required for bootstrap")

    rng_a_seed, rng_b_seed = np.random.SeedSequence(seed).spawn(2)
    rng_a = np.random.default_rng(rng_a_seed)
    rng_b = np.random.default_rng(rng_b_seed)
    components = np.full((n_reps, 4), np.nan, dtype=float)
    for rep in range(n_reps):
        multiplicity_a = np.bincount(
            rng_a.integers(0, len(households_a), size=len(households_a)),
            minlength=len(households_a),
        )
        multiplicity_b = np.bincount(
            rng_b.integers(0, len(households_b), size=len(households_b)),
            minlength=len(households_b),
        )
        resampled_a = PersonDays(
            weight=a.weight * multiplicity_a[codes_a],
            trips=a.trips,
            distance_km=a.distance_km,
            time_min=a.time_min,
        )
        resampled_b = PersonDays(
            weight=b.weight * multiplicity_b[codes_b],
            trips=b.trips,
            distance_km=b.distance_km,
            time_min=b.time_min,
        )
        if not _has_positive_weighted_metrics(resampled_a):
            continue
        if not _has_positive_weighted_metrics(resampled_b):
            continue
        result = decompose(resampled_a, resampled_b)
        components[rep] = (
            result.delta_min,
            result.trips_min,
            result.distance_min,
            result.speed_min,
        )

    valid = components[np.isfinite(components).all(axis=1)]
    if len(valid) == 0:
        raise ValueError("household bootstrap produced no valid replicates")
    intervals = np.percentile(valid, [2.5, 97.5], axis=0)
    return TripTimeDecompositionBootstrap(
        point=point,
        delta_ci=(float(intervals[0, 0]), float(intervals[1, 0])),
        trips_ci=(float(intervals[0, 1]), float(intervals[1, 1])),
        distance_ci=(float(intervals[0, 2]), float(intervals[1, 2])),
        speed_ci=(float(intervals[0, 3]), float(intervals[1, 3])),
    )


def _has_positive_weighted_metrics(days: PersonDays) -> bool:
    weight = np.asarray(days.weight, dtype=float)
    return (
        float(weight.sum()) > 0
        and float(np.sum(weight * days.trips)) > 0
        and float(np.sum(weight * days.distance_km)) > 0
        and float(np.sum(weight * days.time_min)) > 0
    )
