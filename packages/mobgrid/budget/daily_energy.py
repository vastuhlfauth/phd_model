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

#: Day-mode groups directly comparable with Koelbl & Helbing's six
#: reference modes, expanded per the updated section 9.9 point 3 (a
#: household/carpool passenger split); 'multimodal' and 'other' are kept
#: apart (section 9.9 point 3). The short/long train split (step 11
#: round 8) is merged back into a single 'train' group: train_long had
#: too few observations to be a meaningful separate group.
DAY_MODE_GROUPS = (
    "walking_only", "cycle", "car_driver", "car_passenger_household",
    "car_passenger_carpool", "urban_pt", "train",
)

#: The six groups of section 9.9's F8 robustness check ("For walk, bike,
#: driver, both passenger groups, urban PT and train short").
F8_ROBUSTNESS_GROUPS = (
    "walking_only", "cycle", "car_driver", "car_passenger_household",
    "car_passenger_carpool", "urban_pt", "train",
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
                count(*) AS trips_per_day,
                sum(duration_min) AS total_time_min,
                sum(energy_kh_kj) AS total_energy_kh_kj,
                sum(energy_cp_kj) AS total_energy_cp_kj,
                array_agg(DISTINCT mode_group)
                    FILTER (WHERE mode_group != 'walk') AS non_walk_modes,
                -- Home density: the trip departing from home (MORIDOM=1,
                -- section 9.9 point 3's "density class of the commune of
                -- residence"), else the day's first trip, by trip number.
                (array_agg(density_ori ORDER BY (moridom <> 1), num_dep))[1]
                    AS home_density
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
    con: duckdb.DuckDBPyConnection, *, by_age_band: bool = False,
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
    con: duckdb.DuckDBPyConnection, config: EnergyConfig, *, by_age_band: bool = False,
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
            speed_m_per_s, config.reference_mass_kg, 0.0, crr, config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        )
        results.append(
            P0Calibration(
                group=group, n=n, implied_flat_speed_kmh=speed_kmh, p0_w=p0_w
            )
        )
    return results


def bootstrap_mean_ci(
    household: np.ndarray, weight: np.ndarray, value: np.ndarray,
    *, n_reps: int = 200, seed: int = 0,
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
    time_ratio, time_cv, time_min_g, time_max_g = _ratio_and_cv(
        stat_time, group_labels
    )
    return RobustnessRow(
        variant=variant, scope=scope, statistic=statistic,
        energy_kh_ratio=kh_ratio, energy_kh_cv=kh_cv,
        energy_kh_min_group=kh_min, energy_kh_max_group=kh_max,
        energy_cp_ratio=cp_ratio, energy_cp_cv=cp_cv,
        energy_cp_min_group=cp_min, energy_cp_max_group=cp_max,
        time_ratio=time_ratio, time_cv=time_cv,
        time_min_group=time_min_g, time_max_group=time_max_g,
    )


