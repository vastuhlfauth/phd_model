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


# ---------------------------------------------------------------------------
# Step-12 Part B primitives (shift-share, composition, tails), all pure
# numpy so the household bootstrap can rerun them on resampled weights.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TripGroups:
    """Trip-level rows of one group of person-days: one entry per trip,
    with its day weight (minutes and km per trip are weighted by it)."""

    weight: np.ndarray  # day weight repeated on each trip
    minutes: np.ndarray
    km: np.ndarray
    group: np.ndarray  # mode / motive / distance-band label per trip
    #: weighted count of person-days (denominator of trips per day);
    #: scalar because the trip rows alone cannot recover it.
    day_weight_total: float


@dataclass(frozen=True)
class ShiftShareTerm:
    """One group's shift-share contribution, minutes per day (B3/B4)."""

    group: str
    share_a: float
    share_b: float
    minutes_per_trip_a: float
    minutes_per_trip_b: float
    mix_min: float
    within_min: float
    interaction_min: float
    #: `within_min` split into km-per-trip and speed parts (B3's "within
    #: each mode, split the minutes per trip into km per trip and speed,
    #: as in B2"); NaN when the group is absent from either side.
    within_km_min: float
    within_speed_min: float


@dataclass(frozen=True)
class ShiftShare:
    """B3/B4 shift-share of the change in daily time, minutes per day.

    ``delta_min = volume_min + sum(mix + within + interaction)`` exactly:
    ``ΔT = (N_B - N_A)·M_A + N_B·(M_B - M_A)`` with ``M_B - M_A`` split
    group by group (mix, within, interaction).
    """

    time_a_min: float
    time_b_min: float
    delta_min: float
    trips_a: float
    trips_b: float
    minutes_per_trip_a: float
    minutes_per_trip_b: float
    volume_min: float
    terms: tuple[ShiftShareTerm, ...]

    @property
    def mix_min(self) -> float:
        return float(sum(t.mix_min for t in self.terms))

    @property
    def within_min(self) -> float:
        return float(sum(t.within_min for t in self.terms))

    @property
    def interaction_min(self) -> float:
        return float(sum(t.interaction_min for t in self.terms))


def _group_trip_stats(
    trips: TripGroups, groups: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-group (share of trips, minutes per trip, km per trip),
    weighted; share 0 and NaN minutes/km for an absent group."""
    shares = np.zeros(len(groups))
    minutes = np.full(len(groups), np.nan)
    km = np.full(len(groups), np.nan)
    total_w = float(trips.weight.sum())
    for i, group in enumerate(groups):
        mask = trips.group == group
        w = float(trips.weight[mask].sum())
        if w > 0 and total_w > 0:
            shares[i] = w / total_w
            minutes[i] = float(np.sum(trips.weight[mask] * trips.minutes[mask])) / w
            km[i] = float(np.sum(trips.weight[mask] * trips.km[mask])) / w
    return shares, minutes, km


def shift_share(a: TripGroups, b: TripGroups) -> ShiftShare:
    """B3/B4 shift-share of the daily-time change between two groups of
    person-days, by trip group (mode, motive or distance band), minutes.

    Ratios of weighted totals throughout: N = weighted trips per day,
    M = weighted minutes per trip, s_m/m_m per group. A group absent
    from one side takes that side's overall M as its ``m`` (its share is
    0 there, so the identity is unchanged; the convention only affects
    how its minutes split between mix and interaction).
    """
    groups = sorted(set(a.group) | set(b.group))
    s_a, m_a, km_a = _group_trip_stats(a, groups)
    s_b, m_b, km_b = _group_trip_stats(b, groups)
    n_a = float(a.weight.sum()) / a.day_weight_total
    n_b = float(b.weight.sum()) / b.day_weight_total
    big_m_a = float(np.sum(a.weight * a.minutes)) / float(a.weight.sum())
    big_m_b = float(np.sum(b.weight * b.minutes)) / float(b.weight.sum())
    time_a = n_a * big_m_a
    time_b = n_b * big_m_b
    m_a_filled = np.where(np.isnan(m_a), big_m_a, m_a)
    m_b_filled = np.where(np.isnan(m_b), big_m_b, m_b)

    terms = []
    for i, group in enumerate(groups):
        mix = (s_b[i] - s_a[i]) * m_a_filled[i] * n_b
        within = s_a[i] * (m_b_filled[i] - m_a_filled[i]) * n_b
        interaction = (s_b[i] - s_a[i]) * (m_b_filled[i] - m_a_filled[i]) * n_b
        # B2-style log split of the within-group minutes-per-trip change
        # into km per trip and speed: m = L / v, so
        # Δln m = Δln L - Δln v, scaled to the group's within minutes.
        within_km = within_speed = float("nan")
        if (
            np.isfinite(m_a[i])
            and np.isfinite(m_b[i])
            and min(m_a[i], m_b[i]) > 0
            and np.isfinite(km_a[i])
            and np.isfinite(km_b[i])
            and min(km_a[i], km_b[i]) > 0
        ):
            log_m = float(np.log(m_b[i] / m_a[i]))
            log_km = float(np.log(km_b[i] / km_a[i]))
            log_speed = log_km - log_m  # v = L/m
            log_mean = (
                (m_b[i] - m_a[i]) / log_m
                if not np.isclose(log_m, 0.0, atol=1e-14)
                else float(m_a[i])
            )
            within_km = s_a[i] * n_b * log_mean * log_km
            within_speed = -s_a[i] * n_b * log_mean * log_speed
        terms.append(
            ShiftShareTerm(
                group=group,
                share_a=float(s_a[i]),
                share_b=float(s_b[i]),
                minutes_per_trip_a=float(m_a[i]),
                minutes_per_trip_b=float(m_b[i]),
                mix_min=float(mix),
                within_min=float(within),
                interaction_min=float(interaction),
                within_km_min=within_km,
                within_speed_min=within_speed,
            )
        )
    return ShiftShare(
        time_a_min=time_a,
        time_b_min=time_b,
        delta_min=time_b - time_a,
        trips_a=n_a,
        trips_b=n_b,
        minutes_per_trip_a=big_m_a,
        minutes_per_trip_b=big_m_b,
        volume_min=(n_b - n_a) * big_m_a,
        terms=tuple(terms),
    )


@dataclass(frozen=True)
class Composition:
    """B1 composition/behaviour split of the daily-time change, minutes."""

    mean_a_min: float
    mean_b_min: float
    counterfactual_a_min: float
    composition_min: float
    behaviour_min: float
    n_cells: int
    #: share of group B's weight in cells with no group-A observation,
    #: renormalised away before the counterfactual is taken.
    unmatched_b_weight_share: float


def composition_reweight(
    cell_a: np.ndarray,
    weight_a: np.ndarray,
    time_a: np.ndarray,
    cell_b: np.ndarray,
    weight_b: np.ndarray,
    time_b: np.ndarray,
) -> Composition:
    """Re-weight group A to group B's population structure, cell by cell
    (B1): counterfactual mean of A = Σ_c share_B(c) · mean_A(c), over the
    cells present in both groups (share_B renormalised over them).

    - composition effect = counterfactual mean of A − mean of A;
    - behaviour effect = mean of B − counterfactual mean of A.
    """
    if len(cell_a) == 0 or len(cell_b) == 0:
        raise ValueError("both groups need at least one person-day")
    mean_a = float(np.sum(weight_a * time_a) / np.sum(weight_a))
    mean_b = float(np.sum(weight_b * time_b) / np.sum(weight_b))
    cells_a: dict[str, float] = {}
    sums_a: dict[str, float] = {}
    for cell, w, t in zip(cell_a, weight_a, time_a, strict=True):
        cells_a[cell] = cells_a.get(cell, 0.0) + float(w)
        sums_a[cell] = sums_a.get(cell, 0.0) + float(w) * float(t)
    weights_b: dict[str, float] = {}
    for cell, w in zip(cell_b, weight_b, strict=True):
        weights_b[cell] = weights_b.get(cell, 0.0) + float(w)
    total_b = sum(weights_b.values())
    matched = {c: w for c, w in weights_b.items() if cells_a.get(c, 0.0) > 0}
    matched_total = sum(matched.values())
    if matched_total <= 0:
        raise ValueError("no population cell is present in both groups")
    counterfactual = sum(
        (w / matched_total) * (sums_a[c] / cells_a[c]) for c, w in matched.items()
    )
    return Composition(
        mean_a_min=mean_a,
        mean_b_min=mean_b,
        counterfactual_a_min=float(counterfactual),
        composition_min=float(counterfactual) - mean_a,
        behaviour_min=mean_b - float(counterfactual),
        n_cells=len(matched),
        unmatched_b_weight_share=1.0 - matched_total / total_b if total_b else 0.0,
    )


def merge_age_bands(
    age_idx_a: np.ndarray,
    stratum_a: np.ndarray,
    age_idx_b: np.ndarray,
    stratum_b: np.ndarray,
    *,
    n_bands: int,
    min_n: int = 30,
) -> dict[tuple[str, int], int]:
    """Merge neighbouring age bands within each stratum until every
    (stratum, merged band) cell has at least ``min_n`` respondents in
    *both* groups (B1: "when a cell has fewer than 30 respondents in
    either group, merge it with the neighbouring age band").

    Scans bands in ascending order, accumulating a run of bands until
    both groups reach ``min_n``; a trailing short run merges backward
    into the previous merged cell. Returns a mapping
    ``(stratum, age band index) -> merged band index`` (the first band
    of the run), identical for both groups.
    """
    strata = sorted(set(stratum_a) | set(stratum_b))
    counts_a = {(s, i): 0 for s in strata for i in range(n_bands)}
    counts_b = dict(counts_a)
    for idx, stratum in zip(age_idx_a, stratum_a, strict=True):
        counts_a[(stratum, int(idx))] += 1
    for idx, stratum in zip(age_idx_b, stratum_b, strict=True):
        counts_b[(stratum, int(idx))] += 1
    mapping: dict[tuple[str, int], int] = {}
    for stratum in strata:
        run_start = 0
        run_a = run_b = 0
        starts: list[int] = []
        for i in range(n_bands):
            run_a += counts_a[(stratum, i)]
            run_b += counts_b[(stratum, i)]
            mapping[(stratum, i)] = run_start
            if run_a >= min_n and run_b >= min_n:
                starts.append(run_start)
                run_start = i + 1
                run_a = run_b = 0
        if run_start < n_bands and (run_a > 0 or run_b > 0):
            # Trailing short run: fold into the previous merged cell.
            target = starts[-1] if starts else 0
            for i in range(run_start, n_bands):
                mapping[(stratum, i)] = target
    return mapping


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted median: the first value whose cumulative weight reaches
    half the total."""
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    cutoff = 0.5 * cumulative[-1]
    return float(values[order][np.searchsorted(cumulative, cutoff)])


def trimmed_mean(values: np.ndarray, weights: np.ndarray, top_share: float) -> float:
    """Weighted mean after removing the top ``top_share`` of weight by
    value (B5's trimmed means)."""
    order = np.argsort(values, kind="stable")
    v, w = values[order], weights[order].astype(float)
    cumulative = np.cumsum(w)
    total = cumulative[-1]
    keep = total * (1.0 - top_share)
    w_kept = np.where(cumulative <= keep, w, np.maximum(0.0, keep - (cumulative - w)))
    return float(np.sum(w_kept * v) / np.sum(w_kept))


def mean_above_threshold(
    values: np.ndarray, weights: np.ndarray, threshold: float
) -> float:
    """Weighted mean, per unit of weight, of the part of ``values``
    above ``threshold`` cases: Σ w·v·1(v > t) / Σ w (B5's "contribution
    of person-days above 180 min" -- their minutes per person-day)."""
    mask = values > threshold
    return float(np.sum(weights[mask] * values[mask]) / np.sum(weights))


def weighted_mean_ci(
    values: np.ndarray,
    weights: np.ndarray,
    households: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> tuple[float, tuple[float, float]]:
    """Weighted mean with a percentile 95% household-bootstrap CI."""
    mean = float(np.sum(weights * values) / np.sum(weights))
    unique, codes = np.unique(households, return_inverse=True)
    rng = np.random.default_rng(seed)
    reps = np.empty(n_reps)
    for rep in range(n_reps):
        multiplicity = np.bincount(
            rng.integers(0, len(unique), size=len(unique)), minlength=len(unique)
        )
        w = weights * multiplicity[codes]
        total = w.sum()
        reps[rep] = np.sum(w * values) / total if total > 0 else np.nan
    valid = reps[np.isfinite(reps)]
    if len(valid) == 0:
        return mean, (float("nan"), float("nan"))
    low, high = np.percentile(valid, [2.5, 97.5])
    return mean, (float(low), float(high))


def household_multipliers(
    households: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """One bootstrap multiplicity per row, resampling households with
    replacement (shared helper for the Part B bootstrap loops)."""
    unique, codes = np.unique(households, return_inverse=True)
    multiplicity = np.bincount(
        rng.integers(0, len(unique), size=len(unique)), minlength=len(unique)
    )
    return multiplicity[codes]


@dataclass(frozen=True)
class TripSample:
    """One group of person-days with their trips, for the household
    bootstrap: day rows carry the day weights (the trips-per-day
    denominator), trip rows the per-trip metrics."""

    day_weight: np.ndarray
    day_household: np.ndarray
    trip_weight: np.ndarray
    trip_household: np.ndarray
    trip_minutes: np.ndarray
    trip_km: np.ndarray
    trip_group: np.ndarray

    def to_groups(
        self,
        day_multiplier: np.ndarray | None = None,
        trip_multiplier: np.ndarray | None = None,
    ) -> TripGroups:
        day_weight = (
            self.day_weight
            if day_multiplier is None
            else self.day_weight * day_multiplier
        )
        trip_weight = (
            self.trip_weight
            if trip_multiplier is None
            else self.trip_weight * trip_multiplier
        )
        return TripGroups(
            weight=trip_weight,
            minutes=self.trip_minutes,
            km=self.trip_km,
            group=self.trip_group,
            day_weight_total=float(day_weight.sum()),
        )


@dataclass(frozen=True)
class ShiftShareBootstrap:
    """Point shift-share and percentile 95% household-bootstrap CIs on
    its aggregate terms."""

    point: ShiftShare
    delta_ci: tuple[float, float]
    volume_ci: tuple[float, float]
    mix_ci: tuple[float, float]
    within_ci: tuple[float, float]
    interaction_ci: tuple[float, float]


def bootstrap_shift_share(
    a: TripSample,
    b: TripSample,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> ShiftShareBootstrap:
    """``shift_share`` with independent household bootstraps of each
    group (a household's multiplicity applies to its days and trips)."""
    point = shift_share(a.to_groups(), b.to_groups())
    seed_a, seed_b = np.random.SeedSequence(seed).spawn(2)
    rng_a, rng_b = np.random.default_rng(seed_a), np.random.default_rng(seed_b)
    components = np.full((n_reps, 5), np.nan)
    for rep in range(n_reps):
        resampled = []
        for sample, rng in ((a, rng_a), (b, rng_b)):
            unique, day_codes = np.unique(sample.day_household, return_inverse=True)
            multiplicity = np.bincount(
                rng.integers(0, len(unique), size=len(unique)),
                minlength=len(unique),
            )
            trip_codes = np.searchsorted(unique, sample.trip_household)
            resampled.append(
                sample.to_groups(multiplicity[day_codes], multiplicity[trip_codes])
            )
        groups_a, groups_b = resampled
        if (
            groups_a.day_weight_total <= 0
            or groups_b.day_weight_total <= 0
            or groups_a.weight.sum() <= 0
            or groups_b.weight.sum() <= 0
        ):
            continue
        result = shift_share(groups_a, groups_b)
        components[rep] = (
            result.delta_min,
            result.volume_min,
            result.mix_min,
            result.within_min,
            result.interaction_min,
        )
    valid = components[np.isfinite(components).all(axis=1)]
    if len(valid) == 0:
        raise ValueError("household bootstrap produced no valid replicates")
    intervals = np.percentile(valid, [2.5, 97.5], axis=0)

    def _ci(column: int) -> tuple[float, float]:
        return (float(intervals[0, column]), float(intervals[1, column]))

    return ShiftShareBootstrap(
        point=point,
        delta_ci=_ci(0),
        volume_ci=_ci(1),
        mix_ci=_ci(2),
        within_ci=_ci(3),
        interaction_ci=_ci(4),
    )
