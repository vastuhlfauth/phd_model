"""Day-level aggregation and the section 9.9 hypothesis test (step 11).

Sums ``emp2019.trip_legs`` to one row per respondent (point 2), groups
days by main mode, age-activity and home density (point 3), fits a
gamma-like distribution of daily travel energy and compares its mean
with Koelbl & Helbing's (2003) ~615 kJ (point 5), and calibrates v0 and
P0 from the walking and cycling trips (step 1's closing sentence).
Section 9.9's EMC² cross-check (point 4) and the definition of Ē_c for
1 km cells (point 6) are out of scope for this step.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np

from mobgrid.budget.emp2019 import _ACTIVITY_BY_SITUA, _case_sql

#: Koelbl & Helbing's (2003) UK National Travel Survey hypothesis: about
#: 615 kJ of daily travel energy per person and day (section 9.9).
KH_DAILY_ENERGY_KJ = 615.0

#: Day-level groups of section 9.9 point 3: the one mode used besides
#: walking. `trip_legs.mode_group`'s two passenger sub-groups collapse
#: into one here (the household/carpool split is its own report item).
_DAY_MODE_CANDIDATE_SQL = """
    CASE mode_group
        WHEN 'car_passenger_household' THEN 'car_passenger'
        WHEN 'car_passenger_carpool' THEN 'car_passenger'
        ELSE mode_group
    END
"""


def create_day_summary(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``day_summary`` view: one row per EMP 2019 respondent.

    ``day_mode_group`` is 'walking_only' (every trip of the day is a
    walk), the single non-walk mode used (bike, car_driver, car_passenger,
    urban_pt, train or other), or 'multimodal' (more than one non-walk
    mode in the same day; section 9.9 point 3).
    """
    con.sql(f"""
        CREATE OR REPLACE VIEW day_summary AS
        WITH candidate AS (
            SELECT *, {_DAY_MODE_CANDIDATE_SQL} AS day_mode_candidate
            FROM trip_legs
        ),
        per_person AS (
            SELECT
                ident_ind,
                any_value(ident_men) AS ident_men,
                any_value(pond_jour) AS pond_jour,
                any_value(pond_ind) AS pond_ind,
                any_value(age_band) AS age_band,
                any_value(age_activity_group) AS age_activity_group,
                count(*) AS trips_per_day,
                sum(duration_min) AS total_time_min,
                sum(energy_kh_kj) AS total_energy_kh_kj,
                sum(energy_cp_kj) AS total_energy_cp_kj,
                array_agg(DISTINCT day_mode_candidate)
                    FILTER (WHERE day_mode_candidate != 'walk') AS non_walk_modes,
                -- Home density: the trip departing from home (MORIDOM=1,
                -- section 9.9 point 3's "density class ... of residence"),
                -- else the day's first trip, by trip number.
                (array_agg(density_ori ORDER BY (moridom <> 1), num_dep))[1]
                    AS home_density
            FROM candidate
            GROUP BY ident_ind
        )
        SELECT *,
            CASE
                WHEN non_walk_modes IS NULL OR len(non_walk_modes) = 0
                    THEN 'walking_only'
                WHEN len(non_walk_modes) = 1 THEN non_walk_modes[1]
                ELSE 'multimodal'
            END AS day_mode_group
        FROM per_person
    """)


def create_non_travelers(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``non_travelers`` view: Kish respondents with no trip
    recorded on their surveyed day (section 9.9 point 2, "persons without
    trips are reported apart")."""
    activity_case = _case_sql(
        "k.SITUA", _ACTIVITY_BY_SITUA, default="'unknown'", quote_values=True
    )
    con.sql(f"""
        CREATE OR REPLACE VIEW non_travelers AS
        SELECT
            k.IDENT_IND AS ident_ind,
            i.pond_indC AS pond_ind,
            k.AGE6 AS age_band,
            CASE WHEN k.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                 ELSE {activity_case} END AS age_activity_group
        FROM tcm_ind_kish k
        JOIN k_individu i ON i.IDENT_IND = k.IDENT_IND
        WHERE NOT EXISTS (
            SELECT 1 FROM trip_legs t WHERE t.ident_ind = k.IDENT_IND
        )
    """)


@dataclass(frozen=True)
class GroupStats:
    """Weighted sample size and mean energy/time for one group, both rate
    sets, with a bootstrap 95% confidence interval on the energy means."""

    group: str
    n: int
    weighted_n: float
    mean_time_min: float
    mean_energy_kh_kj: float
    mean_energy_kh_ci: tuple[float, float]
    mean_energy_cp_kj: float
    mean_energy_cp_ci: tuple[float, float]


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
    intervals by bootstrap over households, both rate sets").
    """
    groups, group_codes = np.unique(group, return_inverse=True)
    n_groups = len(groups)
    households, household_codes = np.unique(household, return_inverse=True)
    n_households = len(households)

    point_time = _weighted_group_means(group_codes, n_groups, weight, time_min)
    point_kh = _weighted_group_means(group_codes, n_groups, weight, energy_kh)
    point_cp = _weighted_group_means(group_codes, n_groups, weight, energy_cp)

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
            mean_energy_kh_kj=float(point_kh[i]),
            mean_energy_kh_ci=(float(ci_kh[0, i]), float(ci_kh[1, i])),
            mean_energy_cp_kj=float(point_cp[i]),
            mean_energy_cp_ci=(float(ci_cp[0, i]), float(ci_cp[1, i])),
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
class CalibrationStats:
    """Calibrated v0 (walking) or P0 (cycling) for one age band (section
    9.9, step 1's closing sentence)."""

    age_band: str
    n: int
    mean_value: float


def calibrate_by_age_band(
    con: duckdb.DuckDBPyConnection, mode_group: str, value_column: str
) -> list[CalibrationStats]:
    """Mean implied v0 (km/h, ``mode_group='walk'``) or P0 (W,
    ``mode_group='cycle'``) by age band, from declared distance over
    duration (section 9.9, step 1)."""
    rows = con.sql(f"""
        SELECT age_band, count(*), avg({value_column})
        FROM trip_legs
        WHERE mode_group = '{mode_group}' AND {value_column} IS NOT NULL
        GROUP BY age_band
        ORDER BY age_band
    """).fetchall()
    return [
        CalibrationStats(age_band=row[0], n=row[1], mean_value=row[2])
        for row in rows
    ]

