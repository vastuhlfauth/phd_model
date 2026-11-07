"""Day-level aggregation and the section 9.9 hypothesis test (step 11).

Sums ``trip_legs`` to one row per described day (point 2), groups days by
main mode, population category (section 6.1) and home density (point 3),
fits a gamma-like distribution of daily travel energy and compares its
mean with Koelbl & Helbing's (2003) ~615 kJ (point 5), and calibrates v0
and P0 from the walking and cycling trips (step 1's closing sentence).
Section 9.9's EMC² cross-check (point 4) and the definition of Ē_c for
1 km cells (point 6) are out of scope for this step. Survey-agnostic
(``trip_legs.day_id`` is EMP 2019's `IDENT_IND` or ENTD 2008's
`IDENT_JOUR`, `docs/data/entd2008.md`): each survey builds its own
``non_travelers``-equivalent summary (``emp2019.non_traveler_summary``,
``entd2008.non_traveler_summary``), since the two surveys identify
non-travellers differently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import duckdb
import numpy as np

from mobgrid.energy import bike
from mobgrid.energy.rates import EnergyConfig

#: Koelbl & Helbing's (2003) UK National Travel Survey hypothesis: about
#: 615 kJ of daily travel energy per person and day (section 9.9).
KH_DAILY_ENERGY_KJ = 615.0

#: Section 6.1's five population categories, in the order the time
#: budget's b_k is reported (section 9.9, 27 October 2026 decision:
#: "one budget b_k is defined for each population category").
POPULATION_CATEGORIES = (
    "children_6_17",
    "employed",
    "unemployed",
    "retired",
    "other_inactive",
)

#: Day-mode groups directly comparable with Koelbl & Helbing's six
#: reference modes, expanded per the updated section 9.9 point 3 (a
#: household/carpool passenger split); 'multimodal' and 'other' are kept
#: apart (section 9.9 point 3). The short/long train split (step 11
#: round 8) is merged back into a single 'train' group: train_long had
#: too few observations to be a meaningful separate group.
DAY_MODE_GROUPS = (
    "walking_only",
    "cycle",
    "car_driver",
    "car_passenger_household",
    "car_passenger_carpool",
    "urban_pt",
    "train",
)

#: The seven groups of section 9.9's F8 robustness check ("For walk, bike,
#: driver, both passenger groups, urban PT and train short").
F8_ROBUSTNESS_GROUPS = (
    "walking_only",
    "cycle",
    "car_driver",
    "car_passenger_household",
    "car_passenger_carpool",
    "urban_pt",
    "train",
)

#: The four "core" groups of F8's core/full comparison: walk, car driver,
#: urban PT, train (no bike or either passenger group).
F8_CORE_ROBUSTNESS_GROUPS = ("walking_only", "car_driver", "urban_pt", "train")


def create_day_summary(
    con: duckdb.DuckDBPyConnection, *, where_sql: str = "TRUE"
) -> None:
    """Create the ``day_summary`` view: one row per described day
    (``trip_legs.day_id``: EMP 2019's `IDENT_IND`, one day per person;
    ENTD 2008's `IDENT_JOUR`, up to three days per person) with at least
    one trip matching ``where_sql`` (applied to ``trip_legs``; used by
    the F8 robustness check's "weekdays only" and "local trips only"
    variants, section 9.9).

    ``day_mode_group`` is 'walking_only' (every matching trip of the day
    is a walk), the single non-walk mode used (``trip_legs.mode_group``,
    now already split into household/carpool passenger and short/long
    train), or 'multimodal' (two or more distinct non-walk modes in the
    same day -- driving and riding as a passenger count as two, section
    9.9 point 3).
    """
    con.sql(f"""
        CREATE OR REPLACE VIEW day_summary AS
        WITH candidate AS (
            SELECT * FROM trip_legs WHERE {where_sql}
        ),
        per_day AS (
            SELECT
                day_id,
                any_value(ident_ind) AS ident_ind,
                any_value(ident_men) AS ident_men,
                any_value(pond_jour) AS pond_jour,
                any_value(pond_ind) AS pond_ind,
                any_value(typejour) AS typejour,
                any_value(age_band) AS age_band,
                any_value(population_category) AS population_category,
                -- Household income quintile (section 9.9's income
                -- update): constant per person, like `home_density`,
                -- so a day groups by it even if that day's own trips
                -- don't all carry it identically (they do, but the
                -- aggregation is the same `any_value` pattern).
                any_value(income_quintile) AS income_quintile,
                count(*) AS trips_per_day,
                sum(duration_min) AS total_time_min,
                sum(energy_kh_kj) AS total_energy_kh_kj,
                sum(energy_cp_kj) AS total_energy_cp_kj,
                array_agg(DISTINCT mode_group)
                    FILTER (WHERE mode_group != 'walk') AS non_walk_modes,
                -- Home density (27 October 2026 decision, section 9.9):
                -- the residence commune's own density
                -- (`trip_legs.residence_density`), constant per person
                -- regardless of which trip ends up in `candidate`'s
                -- scope -- not the density of the trip departing from
                -- home (MORIDOM=1), which this replaces: that proxy was
                -- undefined for a day with no home-departing trip in
                -- scope, and is not even a property of the person.
                any_value(residence_density) AS home_density
            FROM candidate
            GROUP BY day_id
        )
        SELECT *,
            CASE
                WHEN non_walk_modes IS NULL OR len(non_walk_modes) = 0
                    THEN 'walking_only'
                WHEN len(non_walk_modes) = 1 THEN non_walk_modes[1]
                ELSE 'multimodal'
            END AS day_mode_group
        FROM per_day
    """)


@dataclass(frozen=True)
class GroupStats:
    """Weighted sample size, mean and median energy/time for one group,
    both rate sets, with a bootstrap 95% confidence interval on the
    energy means."""

    group: str
    n: int
    weighted_n: float
    mean_time_min: float
    median_time_min: float
    mean_energy_kh_kj: float
    mean_energy_kh_ci: tuple[float, float]
    median_energy_kh_kj: float
    mean_energy_cp_kj: float
    mean_energy_cp_ci: tuple[float, float]
    median_energy_cp_kj: float


def _weighted_group_means(
    group_codes: np.ndarray, n_groups: int, weights: np.ndarray, values: np.ndarray
) -> np.ndarray:
    """Per group (0..n_groups-1), sum(weight*value)/sum(weight); NaN where
    a group has zero weight in this (possibly resampled) set of rows."""
    weighted_sum = np.bincount(
        group_codes, weights=weights * values, minlength=n_groups
    )
    weight_sum = np.bincount(group_codes, weights=weights, minlength=n_groups)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(weight_sum > 0, weighted_sum / weight_sum, np.nan)


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted median: the value at which the cumulative weight first
    reaches half the total weight."""
    if len(values) == 0 or weights.sum() <= 0:
        return float("nan")
    order = np.argsort(values)
    sorted_values = values[order]
    cum_weight = np.cumsum(weights[order])
    half = cum_weight[-1] / 2.0
    idx = int(np.searchsorted(cum_weight, half))
    idx = min(idx, len(sorted_values) - 1)
    return float(sorted_values[idx])


def _weighted_group_medians(
    group_codes: np.ndarray, n_groups: int, weights: np.ndarray, values: np.ndarray
) -> np.ndarray:
    """Per group (0..n_groups-1), the weighted median of ``values``; a
    per-group loop, not a per-row one (``n_groups`` is small, a dozen at
    most)."""
    medians = np.full(n_groups, np.nan)
    for i in range(n_groups):
        mask = group_codes == i
        if mask.any():
            medians[i] = _weighted_median(values[mask], weights[mask])
    return medians


def bootstrap_group_stats(
    group: np.ndarray,
    household: np.ndarray,
    weight: np.ndarray,
    time_min: np.ndarray,
    energy_kh: np.ndarray,
    energy_cp: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> list[GroupStats]:
    """Weighted group means, with a 95% bootstrap confidence interval on
    the two energy means, resampled over households (section 9.9's
    "Outputs of the re-estimation": "weighted, with 95% confidence
    intervals by bootstrap over households, both rate sets"), plus the
    (non-bootstrapped) weighted median of each.
    """
    groups, group_codes = np.unique(group, return_inverse=True)
    n_groups = len(groups)
    households, household_codes = np.unique(household, return_inverse=True)
    n_households = len(households)

    point_time = _weighted_group_means(group_codes, n_groups, weight, time_min)
    point_kh = _weighted_group_means(group_codes, n_groups, weight, energy_kh)
    point_cp = _weighted_group_means(group_codes, n_groups, weight, energy_cp)
    median_time = _weighted_group_medians(group_codes, n_groups, weight, time_min)
    median_kh = _weighted_group_medians(group_codes, n_groups, weight, energy_kh)
    median_cp = _weighted_group_medians(group_codes, n_groups, weight, energy_cp)

    rng = np.random.default_rng(seed)
    rep_kh = np.empty((n_reps, n_groups))
    rep_cp = np.empty((n_reps, n_groups))
    for rep in range(n_reps):
        sample = rng.integers(0, n_households, size=n_households)
        multiplicity = np.bincount(sample, minlength=n_households)
        rep_weight = weight * multiplicity[household_codes]
        rep_kh[rep] = _weighted_group_means(
            group_codes, n_groups, rep_weight, energy_kh
        )
        rep_cp[rep] = _weighted_group_means(
            group_codes, n_groups, rep_weight, energy_cp
        )

    ci_kh = np.nanpercentile(rep_kh, [2.5, 97.5], axis=0)
    ci_cp = np.nanpercentile(rep_cp, [2.5, 97.5], axis=0)
    n_by_group = np.bincount(group_codes, minlength=n_groups)
    weighted_n_by_group = np.bincount(group_codes, weights=weight, minlength=n_groups)

    return [
        GroupStats(
            group=groups[i],
            n=int(n_by_group[i]),
            weighted_n=float(weighted_n_by_group[i]),
            mean_time_min=float(point_time[i]),
            median_time_min=float(median_time[i]),
            mean_energy_kh_kj=float(point_kh[i]),
            mean_energy_kh_ci=(float(ci_kh[0, i]), float(ci_kh[1, i])),
            median_energy_kh_kj=float(median_kh[i]),
            mean_energy_cp_kj=float(point_cp[i]),
            mean_energy_cp_ci=(float(ci_cp[0, i]), float(ci_cp[1, i])),
            median_energy_cp_kj=float(median_cp[i]),
        )
        for i in range(n_groups)
    ]


@dataclass(frozen=True)
class ScalarGroupStats:
    """Weighted sample size, mean (with a 95% bootstrap CI over
    households) and median of one arbitrary scalar, by group: the
    shared engine behind every daily-time/trips-per-day/minutes-per-trip
    table of section 9.9's income update (point 2/3), giving time the
    same mean+CI+median treatment ``GroupStats`` already gives energy,
    without changing ``GroupStats`` itself."""

    group: str
    n: int
    weighted_n: float
    mean: float
    mean_ci: tuple[float, float]
    median: float


@dataclass(frozen=True)
class EquivalenceStats:
    """Ratio of a subgroup's weighted mean to its category mean, with a
    percentile 90% household-bootstrap interval and TOST verdicts."""

    category: str
    group: str
    n: int
    ratio: float
    ci90: tuple[float, float]
    equivalent_15: bool | None
    equivalent_10: bool | None


def _weighted_mean_bootstrap_replicates(
    household: np.ndarray,
    weight: np.ndarray,
    value: np.ndarray,
    *,
    n_reps: int,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray]:
    """Point estimate and household-bootstrap replicates of a weighted
    ratio of totals."""
    if not (len(household) == len(weight) == len(value)) or len(weight) == 0:
        raise ValueError("bootstrap inputs must have equal, non-zero lengths")
    if not np.isfinite(weight).all() or np.any(weight < 0) or weight.sum() <= 0:
        raise ValueError("bootstrap weights must be finite, non-negative, and non-zero")
    if not np.isfinite(value).all():
        raise ValueError("bootstrap values must be finite")
    households, household_codes = np.unique(household, return_inverse=True)
    if len(households) == 0:
        raise ValueError("bootstrap requires at least one household")
    point = float(np.sum(weight * value) / weight.sum())
    reps = np.empty(n_reps, dtype=float)
    for rep in range(n_reps):
        multiplicity = np.bincount(
            rng.integers(0, len(households), size=len(households)),
            minlength=len(households),
        )
        rep_weight = weight * multiplicity[household_codes]
        reps[rep] = (
            float(np.sum(rep_weight * value) / rep_weight.sum())
            if rep_weight.sum() > 0
            else np.nan
        )
    return point, reps


def bootstrap_replicate_ratio_ci(
    point_a: float,
    reps_a: np.ndarray,
    point_b: float,
    reps_b: np.ndarray,
) -> tuple[float, tuple[float, float]]:
    """Ratio B/A and its paired percentile 90% interval from two already
    bootstrapped samples; replicate ``b`` is paired only after each
    sample has been resampled independently."""
    if len(reps_a) == 0 or len(reps_a) != len(reps_b):
        raise ValueError("ratio bootstrap samples must have equal, non-zero lengths")
    if point_a <= 0 or point_b <= 0:
        raise ValueError("ratio point estimates must be positive")
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = np.asarray(reps_b, dtype=float) / np.asarray(reps_a, dtype=float)
    ratios = ratios[np.isfinite(ratios)]
    if len(ratios) == 0:
        raise ValueError("ratio bootstrap has no finite paired replicates")
    ci = np.nanpercentile(ratios, [5.0, 95.0])
    return point_b / point_a, (float(ci[0]), float(ci[1]))


def bootstrap_ratio_ci(
    household_a: np.ndarray,
    weight_a: np.ndarray,
    value_a: np.ndarray,
    household_b: np.ndarray,
    weight_b: np.ndarray,
    value_b: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
    denominator_a: tuple[np.ndarray, np.ndarray] | None = None,
    denominator_b: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[float, tuple[float, float]]:
    """Section 9.9 survey ratio B/A and its 90% percentile household CI.

    By default each survey estimates a weighted day mean. Explicit
    household/weight denominators support minutes/trip and per-person
    budgets (period scaling must already be in those weights). Both surveys
    always use independent streams spawned from the same report seed.
    """
    if n_reps <= 0:
        raise ValueError("n_reps must be positive")
    seed_a, seed_b = np.random.SeedSequence(seed).spawn(2)

    def estimate(
        household: np.ndarray,
        weight: np.ndarray,
        value: np.ndarray,
        denominator: tuple[np.ndarray, np.ndarray] | None,
        survey_seed: np.random.SeedSequence,
    ) -> tuple[float, np.ndarray]:
        if denominator is None:
            return _weighted_mean_bootstrap_replicates(
                household,
                weight,
                value,
                n_reps=n_reps,
                rng=np.random.default_rng(survey_seed),
            )
        denominator_household, denominator_weight = denominator
        return bootstrap_person_value_replicates(
            denominator_household,
            denominator_weight,
            household,
            weight,
            value,
            n_reps=n_reps,
            seed=survey_seed,
        )

    point_a, reps_a = estimate(household_a, weight_a, value_a, denominator_a, seed_a)
    point_b, reps_b = estimate(household_b, weight_b, value_b, denominator_b, seed_b)
    return bootstrap_replicate_ratio_ci(point_a, reps_a, point_b, reps_b)


def bootstrap_equivalence_by_group(
    group: np.ndarray,
    category: np.ndarray,
    household: np.ndarray,
    weight: np.ndarray,
    value: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
    margin: float,
    secondary_margin: float,
    min_cell_n: int = 50,
) -> list[EquivalenceStats]:
    """Compare each subgroup's mean with its category mean (section 9.9).

    Each replicate resamples households once, preserving the covariance
    between subgroup and category means. Intervals are percentile 90%
    intervals of their ratio, which gives the TOST equivalence decision.
    """
    arrays = (group, category, household, weight, value)
    if len({len(array) for array in arrays}) != 1 or len(weight) == 0:
        raise ValueError("equivalence inputs must have equal, non-zero lengths")
    if n_reps <= 0 or min_cell_n < 1:
        raise ValueError("n_reps and min_cell_n must be positive")
    for candidate in (margin, secondary_margin):
        if not 0 < candidate < 1:
            raise ValueError("equivalence margins must be between zero and one")
    if not np.isfinite(weight).all() or np.any(weight < 0) or weight.sum() <= 0:
        raise ValueError(
            "equivalence weights must be finite, non-negative, and non-zero"
        )
    if not np.isfinite(value).all():
        raise ValueError("equivalence values must be finite")

    group = np.asarray(group, dtype=str)
    category = np.asarray(category, dtype=str)
    household = np.asarray(household)
    weight = np.asarray(weight, dtype=float)
    value = np.asarray(value, dtype=float)
    categories, category_codes = np.unique(category, return_inverse=True)
    pair_labels = np.char.add(
        np.char.add(category, "\x1f"),
        group,
    )
    pairs, pair_codes = np.unique(pair_labels, return_inverse=True)
    pair_categories = np.array([label.split("\x1f", 1)[0] for label in pairs])
    category_index = {label: i for i, label in enumerate(categories)}
    pair_category_codes = np.array([category_index[label] for label in pair_categories])
    households, household_codes = np.unique(household, return_inverse=True)

    point_category = _weighted_group_means(
        category_codes, len(categories), weight, value
    )
    point_pair = _weighted_group_means(pair_codes, len(pairs), weight, value)
    point_ratios = point_pair / point_category[pair_category_codes]
    rep_ratios = np.full((n_reps, len(pairs)), np.nan, dtype=float)
    rng = np.random.default_rng(seed)
    for rep in range(n_reps):
        multiplicity = np.bincount(
            rng.integers(0, len(households), size=len(households)),
            minlength=len(households),
        )
        rep_weight = weight * multiplicity[household_codes]
        category_means = _weighted_group_means(
            category_codes, len(categories), rep_weight, value
        )
        pair_means = _weighted_group_means(pair_codes, len(pairs), rep_weight, value)
        with np.errstate(divide="ignore", invalid="ignore"):
            rep_ratios[rep] = pair_means / category_means[pair_category_codes]

    counts = np.bincount(pair_codes, minlength=len(pairs))
    result = []
    for index, label in enumerate(pairs):
        cat, key = label.split("\x1f", 1)
        if counts[index] < min_cell_n or not np.isfinite(point_ratios[index]):
            ci = (float("nan"), float("nan"))
            verdict_15 = verdict_10 = None
        else:
            finite = rep_ratios[:, index]
            finite = finite[np.isfinite(finite)]
            if len(finite) == 0:
                raise ValueError(f"no finite bootstrap ratios for {cat!r} / {key!r}")
            bounds = np.nanpercentile(finite, [5.0, 95.0])
            ci = (float(bounds[0]), float(bounds[1]))
            verdict_15 = ci[0] >= 1 - margin and ci[1] <= 1 + margin
            verdict_10 = ci[0] >= 1 - secondary_margin and ci[1] <= 1 + secondary_margin
        result.append(
            EquivalenceStats(
                category=cat,
                group=key,
                n=int(counts[index]),
                ratio=float(point_ratios[index]),
                ci90=ci,
                equivalent_15=verdict_15,
                equivalent_10=verdict_10,
            )
        )
    return result


def bootstrap_scalar_group_stats(
    group: np.ndarray,
    household: np.ndarray,
    weight: np.ndarray,
    value: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> list[ScalarGroupStats]:
    """Weighted mean (95% bootstrap CI over households) and median of
    ``value`` by ``group`` (section 9.9: "mean, median and CI wherever
    energy has them"). Reuses ``bootstrap_group_stats``'s own
    group-mean/median/resampling helpers, generalised to one value
    instead of three (time + two energies)."""
    groups, group_codes = np.unique(group, return_inverse=True)
    n_groups = len(groups)
    households, household_codes = np.unique(household, return_inverse=True)
    n_households = len(households)

    point = _weighted_group_means(group_codes, n_groups, weight, value)
    median = _weighted_group_medians(group_codes, n_groups, weight, value)

    rng = np.random.default_rng(seed)
    rep = np.empty((n_reps, n_groups))
    for r in range(n_reps):
        sample = rng.integers(0, n_households, size=n_households)
        multiplicity = np.bincount(sample, minlength=n_households)
        rep_weight = weight * multiplicity[household_codes]
        rep[r] = _weighted_group_means(group_codes, n_groups, rep_weight, value)
    ci = np.nanpercentile(rep, [2.5, 97.5], axis=0)
    n_by_group = np.bincount(group_codes, minlength=n_groups)
    weighted_n_by_group = np.bincount(group_codes, weights=weight, minlength=n_groups)

    return [
        ScalarGroupStats(
            group=groups[i],
            n=int(n_by_group[i]),
            weighted_n=float(weighted_n_by_group[i]),
            mean=float(point[i]),
            mean_ci=(float(ci[0, i]), float(ci[1, i])),
            median=float(median[i]),
        )
        for i in range(n_groups)
    ]


def gamma_moments_fit(mean: float, variance: float) -> tuple[float, float]:
    """Method-of-moments gamma fit (shape, scale): shape = mean^2/var,
    scale = var/mean (section 9.9 point 5, "gamma-like, as in Koelbl &
    Helbing"). No MLE (``scipy.stats.gamma.fit``) dependency is added for
    this single check; the moment estimator is exact for a true gamma and
    a standard first approximation otherwise."""
    if mean <= 0 or variance <= 0:
        raise ValueError("mean and variance must be positive")
    shape = mean**2 / variance
    scale = variance / mean
    return shape, scale


def weighted_mean_variance(
    weight: np.ndarray, value: np.ndarray
) -> tuple[float, float]:
    """Weighted mean and (population) variance of ``value``."""
    total_weight = weight.sum()
    mean = float(np.sum(weight * value) / total_weight)
    variance = float(np.sum(weight * (value - mean) ** 2) / total_weight)
    return mean, variance


@dataclass(frozen=True)
class SpeedCalibration:
    """A ratio-of-weighted-sums speed estimate (section 9.9, step 1):
    v = sum(weight*distance) / sum(weight*duration), for one age band or
    overall, with the unweighted trip count ``n``."""

    group: str
    n: int
    speed_kmh: float


def calibrate_v0_kmh(
    con: duckdb.DuckDBPyConnection,
    *,
    by_age_band: bool = False,
    where_sql: str = "TRUE",
) -> list[SpeedCalibration]:
    """v0, the ratio of weighted sums of distance and duration (section
    9.9, step 1: "Walking and cycling trips calibrate v0 ... by age
    band"), overall or by age band, from walking trips. ``where_sql`` is
    an extra filter on ``trip_legs`` (e.g. excluding leisure-loop trips)."""
    group_sql = "age_band" if by_age_band else "'overall'"
    rows = con.sql(f"""
        SELECT {group_sql} AS grp, count(*),
            sum(pond_jour * distance_km) / sum(pond_jour * duration_min / 60.0)
        FROM trip_legs
        WHERE mode_group = 'walk' AND duration_min > 0 AND ({where_sql})
        GROUP BY {group_sql}
        ORDER BY grp
    """).fetchall()
    return [SpeedCalibration(group=row[0], n=row[1], speed_kmh=row[2]) for row in rows]


@dataclass(frozen=True)
class P0Calibration:
    """P0 and its implied flat speed (section 9.9, step 1), from the
    ratio of weighted sums of distance and ride-only time (get/park and
    expected stops subtracted; ``emp2019.build_trip_legs``)."""

    group: str
    n: int
    implied_flat_speed_kmh: float
    p0_w: float


def calibrate_p0(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    *,
    by_age_band: bool = False,
    where_sql: str = "TRUE",
) -> list[P0Calibration]:
    """P0, from the implied flat speed = ratio of weighted sums of
    distance and ride-only time (section 9.9, step 1), overall or by age
    band. Reuses ``bike.required_power_w`` (section 9.7) at that one
    speed, rather than averaging a nonlinear per-trip P0 over trips.
    ``where_sql`` is an extra filter on ``trip_legs`` (e.g. excluding
    leisure-loop trips).

    EMP 2019's own mode codes (`mtp` 2.1) do not separate e-bikes from
    bicycles ("y compris a assistance electrique"), so they cannot be
    excluded or reported apart here (section 9.9, step 1).
    """
    group_sql = "age_band" if by_age_band else "'overall'"
    rows = con.sql(f"""
        SELECT {group_sql} AS grp, count(*),
            sum(pond_jour * distance_km)
                / (sum(pond_jour * bike_ride_time_for_energy_s) / 3600.0)
        FROM trip_legs
        WHERE mode_group = 'cycle' AND ({where_sql})
        GROUP BY {group_sql}
        ORDER BY grp
    """).fetchall()
    crr = config.bike.surface_crr["asphalt_concrete_paved_default"]
    results = []
    for group, n, speed_kmh in rows:
        speed_m_per_s = speed_kmh * 1000.0 / 3600.0
        p0_w = bike.required_power_w(
            speed_m_per_s,
            config.reference_mass_kg,
            0.0,
            crr,
            config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3,
            config.bike.drivetrain_efficiency,
        )
        results.append(
            P0Calibration(group=group, n=n, implied_flat_speed_kmh=speed_kmh, p0_w=p0_w)
        )
    return results


def bootstrap_mean_ci(
    household: np.ndarray,
    weight: np.ndarray,
    value: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> tuple[float, tuple[float, float]]:
    """Weighted mean of ``value`` and its 95% bootstrap CI, resampled
    over households (section 9.9, "95% confidence intervals by bootstrap
    over households"); used for trips-per-person-and-day (point 2/F1)."""
    households, household_codes = np.unique(household, return_inverse=True)
    n_households = len(households)
    point_mean = float(np.sum(weight * value) / weight.sum())

    rng = np.random.default_rng(seed)
    reps = np.empty(n_reps)
    for rep in range(n_reps):
        sample = rng.integers(0, n_households, size=n_households)
        multiplicity = np.bincount(sample, minlength=n_households)
        rep_weight = weight * multiplicity[household_codes]
        reps[rep] = np.sum(rep_weight * value) / rep_weight.sum()
    ci = np.percentile(reps, [2.5, 97.5])
    return point_mean, (float(ci[0]), float(ci[1]))


def bootstrap_diff_ci(
    household_a: np.ndarray,
    weight_a: np.ndarray,
    value_a: np.ndarray,
    household_b: np.ndarray,
    weight_b: np.ndarray,
    value_b: np.ndarray,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> tuple[float, tuple[float, float]]:
    """Point difference ``mean(b) - mean(a)`` and its 95% bootstrap CI,
    independent household resamples in each survey added rep-by-rep
    (section 9.9's "Weights and confidence intervals": "the 2008-2019
    difference gets its interval from the two surveys' replicates"),
    used for the weekday-only 2008-2019 comparison (per day with trips
    and per person)."""
    point = float(
        np.sum(weight_b * value_b) / weight_b.sum()
        - np.sum(weight_a * value_a) / weight_a.sum()
    )
    households_a, codes_a = np.unique(household_a, return_inverse=True)
    households_b, codes_b = np.unique(household_b, return_inverse=True)
    rng = np.random.default_rng(seed)
    reps = np.empty(n_reps)
    for rep in range(n_reps):
        mult_a = np.bincount(
            rng.integers(0, len(households_a), size=len(households_a)),
            minlength=len(households_a),
        )
        mult_b = np.bincount(
            rng.integers(0, len(households_b), size=len(households_b)),
            minlength=len(households_b),
        )
        rw_a = weight_a * mult_a[codes_a]
        rw_b = weight_b * mult_b[codes_b]
        reps[rep] = (
            np.sum(rw_b * value_b) / rw_b.sum() - np.sum(rw_a * value_a) / rw_a.sum()
        )
    ci = np.percentile(reps, [2.5, 97.5])
    return point, (float(ci[0]), float(ci[1]))


def weighted_gaussian_bandwidth(
    weight: np.ndarray, value: np.ndarray, *, scale: float = 1.0
) -> float:
    """Silverman's (1986) rule-of-thumb bandwidth on a weighted sample,
    used as one shared bandwidth across every group's density (section
    9.9's F3, "same bandwidth for all groups"). ``scale`` widens
    (``> 1.0``) or narrows (``< 1.0``) the Silverman bandwidth, e.g. for
    a smoother density over modest per-group sample sizes."""
    mean, variance = weighted_mean_variance(weight, value)
    std = math.sqrt(variance)
    effective_n = weight.sum() ** 2 / np.sum(weight**2)
    return scale * 0.9 * std * effective_n ** (-1.0 / 5.0)


def weighted_gaussian_kde(
    x_eval: np.ndarray, samples: np.ndarray, weights: np.ndarray, bandwidth: float
) -> np.ndarray:
    """Weighted Gaussian kernel density estimate of ``samples`` at
    ``x_eval`` (section 9.9's F3), fully vectorised (no `scipy`
    dependency: a Gaussian KDE is a direct, O(len(x_eval)*len(samples))
    sum, well within the project's "no Python loops over large arrays"
    rule for the few hundred grid points x tens of thousands of trips
    used here).
    """
    diffs = (x_eval[:, None] - samples[None, :]) / bandwidth
    kernel = np.exp(-0.5 * diffs**2) / math.sqrt(2.0 * math.pi)
    return (kernel * weights[None, :]).sum(axis=1) / (bandwidth * weights.sum())


@dataclass(frozen=True)
class RobustnessRow:
    """One F8 robustness variant, for one ``scope`` (``"full"``,
    ``F8_ROBUSTNESS_GROUPS``, or ``"core"``, ``F8_CORE_ROBUSTNESS_GROUPS``)
    and one ``statistic`` (``"mean"`` or ``"median"``): the max/min ratio
    and coefficient of variation of that scope's groups' chosen
    statistic, energy (both rate sets) and time (section 9.9's F8), with
    the names of the min/max groups."""

    variant: str
    scope: str
    statistic: str
    energy_kh_ratio: float
    energy_kh_cv: float
    energy_kh_min_group: str
    energy_kh_max_group: str
    energy_cp_ratio: float
    energy_cp_cv: float
    energy_cp_min_group: str
    energy_cp_max_group: str
    time_ratio: float
    time_cv: float
    time_min_group: str
    time_max_group: str


def _ratio_and_cv(
    values: np.ndarray, labels: np.ndarray
) -> tuple[float, float, str, str]:
    """max/min ratio and coefficient of variation (std/mean) of an array
    of group means, with the names of the min/max groups."""
    finite_mask = np.isfinite(values)
    finite = values[finite_mask]
    finite_labels = labels[finite_mask]
    if len(finite) == 0:
        return float("nan"), float("nan"), "", ""
    ratio = float(finite.max() / finite.min())
    cv = float(finite.std() / finite.mean())
    min_group = str(finite_labels[finite.argmin()])
    max_group = str(finite_labels[finite.argmax()])
    return ratio, cv, min_group, max_group


def robustness_row(
    variant: str,
    day_mode_group: np.ndarray,
    weight: np.ndarray,
    time_min: np.ndarray,
    energy_kh: np.ndarray,
    energy_cp: np.ndarray,
    *,
    scope: str = "full",
    groups_of_interest: tuple[str, ...] = F8_ROBUSTNESS_GROUPS,
    statistic: str = "mean",
) -> RobustnessRow:
    """One F8 table row: ratio and CV of ``groups_of_interest``' means or
    medians under one robustness variant (section 9.9's F8); ``scope``
    names this set of groups in the row (``"full"`` or ``"core"``),
    ``statistic`` the chosen per-group value (``"mean"`` or
    ``"median"``)."""
    if statistic not in ("mean", "median"):
        raise ValueError(f"unknown statistic: {statistic!r}")
    group_stat_fn = (
        _weighted_group_means if statistic == "mean" else _weighted_group_medians
    )
    groups, group_codes = np.unique(day_mode_group, return_inverse=True)
    n_groups = len(groups)
    mask = np.isin(groups, groups_of_interest)
    group_labels = groups[mask]
    stat_kh = group_stat_fn(group_codes, n_groups, weight, energy_kh)[mask]
    stat_cp = group_stat_fn(group_codes, n_groups, weight, energy_cp)[mask]
    stat_time = group_stat_fn(group_codes, n_groups, weight, time_min)[mask]
    kh_ratio, kh_cv, kh_min, kh_max = _ratio_and_cv(stat_kh, group_labels)
    cp_ratio, cp_cv, cp_min, cp_max = _ratio_and_cv(stat_cp, group_labels)
    time_ratio, time_cv, time_min_g, time_max_g = _ratio_and_cv(stat_time, group_labels)
    return RobustnessRow(
        variant=variant,
        scope=scope,
        statistic=statistic,
        energy_kh_ratio=kh_ratio,
        energy_kh_cv=kh_cv,
        energy_kh_min_group=kh_min,
        energy_kh_max_group=kh_max,
        energy_cp_ratio=cp_ratio,
        energy_cp_cv=cp_cv,
        energy_cp_min_group=cp_min,
        energy_cp_max_group=cp_max,
        time_ratio=time_ratio,
        time_cv=time_cv,
        time_min_group=time_min_g,
        time_max_group=time_max_g,
    )


@dataclass(frozen=True)
class PersonBudgetRow:
    """Direct producer-weighted per-person value and household-bootstrap CI."""

    group: str
    n: int
    budget: float
    budget_ci: tuple[float, float]


@dataclass(frozen=True)
class ZeroLocalTripDaySummary:
    """Weighted zero-local-trip share among described weekday out-days."""

    n_described_days: int
    n_zero_local_days: int
    weighted_days: float
    weighted_zero_local_days: float
    share: float


def zero_local_trip_day_summary(
    con: duckdb.DuckDBPyConnection, *, where_sql: str = "typejour = 1"
) -> ZeroLocalTripDaySummary:
    """Summarize described days with trips but no local trip (section 9.9).

    The weighted share uses one ``pond_jour`` per described day. ``where_sql``
    filters trip rows before grouping and defaults to weekdays.
    """
    row = con.sql(f"""
        WITH described_days AS (
            SELECT day_id,
                any_value(pond_jour) AS day_weight,
                count(*) FILTER (WHERE mobloc = 1) AS local_trips
            FROM trip_legs
            WHERE ({where_sql}) AND pond_jour > 0
            GROUP BY day_id
        )
        SELECT count(*) AS n_days,
            count(*) FILTER (WHERE local_trips = 0) AS n_zero_local_days,
            sum(day_weight) AS weighted_days,
            sum(day_weight) FILTER (WHERE local_trips = 0)
                AS weighted_zero_local_days
        FROM described_days
    """).fetchone()
    n_days, n_zero, weighted_days, weighted_zero = row
    if not n_days or weighted_days is None or weighted_days <= 0:
        raise ValueError("zero-local-trip diagnostic requires described weekdays")
    weighted_zero = float(weighted_zero or 0.0)
    return ZeroLocalTripDaySummary(
        n_described_days=int(n_days),
        n_zero_local_days=int(n_zero),
        weighted_days=float(weighted_days),
        weighted_zero_local_days=weighted_zero,
        share=weighted_zero / float(weighted_days),
    )


def bootstrap_person_value_replicates(
    household_p: np.ndarray,
    weight_p: np.ndarray,
    household_t: np.ndarray,
    weight_t: np.ndarray,
    value_t: np.ndarray,
    *,
    person_weight_scale: float = 1.0,
    period_divisor: float = 1.0,
    open_days: np.ndarray | None = None,
    n_reps: int = 200,
    seed: int | np.random.SeedSequence = 0,
) -> tuple[float, np.ndarray]:
    """Direct producer-weighted per-person value and household replicates.

    The numerator is ``sum(weight_t * value_t)``. The denominator is the
    full respondent weight, multiplied by the producer's denominator scale
    and the number of days represented by the period. A household draw is
    applied to both samples. Open days are excluded from the numerator and
    their day weights are subtracted from the denominator (section 9.9).
    Respondents without trips remain in the denominator.
    """
    if len(household_p) != len(weight_p):
        raise ValueError("person-budget inputs must have equal lengths")
    if len(household_t) != len(weight_t) or len(weight_t) != len(value_t):
        raise ValueError("trip-day inputs must have equal lengths")
    if open_days is None:
        open_days = np.zeros(len(weight_t), dtype=bool)
    elif len(open_days) != len(weight_t) or open_days.dtype != np.dtype(bool):
        raise ValueError("open_days must be a boolean array matching trip-day inputs")
    if len(weight_p) == 0 or n_reps < 0:
        raise ValueError(
            "person-budget bootstrap requires people and non-negative reps"
        )
    if (
        not np.isfinite(weight_p).all()
        or not np.isfinite(weight_t).all()
        or np.any(weight_p < 0)
        or np.any(weight_t < 0)
        or weight_p.sum() <= 0
        or not np.isfinite(person_weight_scale)
        or person_weight_scale <= 0
        or not np.isfinite(period_divisor)
        or period_divisor <= 0
    ):
        raise ValueError("person-budget weights and scales must be finite and positive")
    if not np.isfinite(value_t).all() or np.any(value_t < 0):
        raise ValueError("person-budget values must be finite and non-negative")

    denominator = np.sum(weight_p) * person_weight_scale * period_divisor - np.sum(
        weight_t[open_days]
    )
    if denominator <= 0:
        raise ValueError("person-budget denominator after open days must be positive")
    point = float(np.sum(weight_t[~open_days] * value_t[~open_days]) / denominator)
    households = np.unique(np.concatenate([household_p, household_t]))
    hh_index = {household: i for i, household in enumerate(households)}
    idx_p = np.array([hh_index[household] for household in household_p])
    idx_t = np.array([hh_index[household] for household in household_t])
    rng = np.random.default_rng(seed)
    reps = np.empty(n_reps)
    for rep in range(n_reps):
        multiplicity = np.bincount(
            rng.integers(0, len(households), size=len(households)),
            minlength=len(households),
        )
        denominator = np.sum(
            weight_p * multiplicity[idx_p]
        ) * person_weight_scale * period_divisor - np.sum(
            weight_t[open_days] * multiplicity[idx_t[open_days]]
        )
        numerator = np.sum(
            weight_t[~open_days] * value_t[~open_days] * multiplicity[idx_t[~open_days]]
        )
        reps[rep] = numerator / denominator if denominator > 0 else np.nan
    return point, reps


def person_budget_by_group(
    p_group: np.ndarray,
    p_household: np.ndarray,
    p_weight: np.ndarray,
    t_group: np.ndarray,
    t_day_type: np.ndarray,
    t_household: np.ndarray,
    t_weight: np.ndarray,
    t_value: np.ndarray,
    *,
    groups: list[str],
    day_types: tuple[str, ...] = ("weekday",),
    person_weight_scale: float = 1.0,
    period_divisor: float = 1.0,
    t_is_open: np.ndarray | None = None,
    min_cell_n: int = 50,
    n_reps: int = 200,
    seed: int = 0,
) -> dict[str, PersonBudgetRow]:
    """Estimate direct producer-weighted per-person values by group.

    Person inputs contain one row per respondent. Trip-day inputs contain
    local day summaries; their weighted values are summed over ``day_types``
    and divided by the full group roster weight and ``period_divisor``.
    Cells are suppressed using respondent counts, and household bootstrap
    multiplicities are shared by both inputs.
    """
    if len(p_group) != len(p_household) or len(p_group) != len(p_weight):
        raise ValueError("person-budget person inputs must have equal lengths")
    if not (
        len(t_group)
        == len(t_day_type)
        == len(t_household)
        == len(t_weight)
        == len(t_value)
    ):
        raise ValueError("person-budget trip-day inputs must have equal lengths")
    if min_cell_n < 1 or n_reps < 0:
        raise ValueError("min_cell_n must be positive and n_reps non-negative")
    if not day_types:
        raise ValueError("person-budget day_types must not be empty")
    if t_is_open is not None and (
        len(t_is_open) != len(t_weight) or t_is_open.dtype != np.dtype(bool)
    ):
        raise ValueError("t_is_open must be a boolean array matching trip-day inputs")

    results: dict[str, PersonBudgetRow] = {}
    for group in (*groups, None):
        label = group or "overall"
        mask_p_all = (
            p_group == group if group is not None else np.ones(len(p_group), bool)
        )
        mask_t_all = (
            t_group == group if group is not None else np.ones(len(t_group), bool)
        )
        n = int(mask_p_all.sum())
        if n < min_cell_n or n == 0:
            results[label] = PersonBudgetRow(
                group=label,
                n=n,
                budget=float("nan"),
                budget_ci=(float("nan"), float("nan")),
            )
            continue

        mask_t = mask_t_all & np.isin(t_day_type, day_types)
        point, reps = bootstrap_person_value_replicates(
            p_household[mask_p_all],
            p_weight[mask_p_all],
            t_household[mask_t],
            t_weight[mask_t],
            t_value[mask_t],
            person_weight_scale=person_weight_scale,
            period_divisor=period_divisor,
            open_days=t_is_open[mask_t] if t_is_open is not None else None,
            n_reps=n_reps,
            seed=seed,
        )
        finite_reps = reps[np.isfinite(reps)]
        if len(finite_reps):
            low, high = np.percentile(finite_reps, [2.5, 97.5])
            ci = (float(low), float(high))
        else:
            ci = (float("nan"), float("nan"))
        results[label] = PersonBudgetRow(
            group=label,
            n=n,
            budget=point,
            budget_ci=ci,
        )
    return results
