"""Daily travel-time distributions by mode, section 9.9."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np

from mobgrid.budget import daily_energy, modes_cache
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Observations:
    """Durations in minutes, their day weights and household identifiers."""

    values: np.ndarray
    weights: np.ndarray
    household: np.ndarray


def _read_observations(
    con: duckdb.DuckDBPyConnection, query: str, path: Path
) -> dict[str, Observations]:
    rows = con.execute(query, [str(path)]).fetchnumpy()
    rows = {key: vr._plain_array(value) for key, value in rows.items()}
    labels = vr._text_values(rows["group_name"])
    values = np.asarray(rows["value"], dtype=float)
    weights = np.asarray(rows["weight"], dtype=float)
    household = vr._text_values(rows["household"])
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0) & (values >= 0)
    if not valid.all():
        LOGGER.warning(
            "Excluded %d rows with invalid duration or weight", (~valid).sum()
        )
    return {
        str(group): Observations(values[mask], weights[mask], household[mask])
        for group in np.unique(labels[valid])
        if (mask := valid & (labels == group)).any()
    }


def read_samples(
    cache: modes_cache.SurveyCache, selected: scope_module.Scope
) -> dict[tuple[str, str], Observations]:
    """Read cached scoped weekday trips and days without rebuilding legs."""
    with duckdb.connect() as con:
        trips = _read_observations(
            con,
            """SELECT mode7 AS group_name, duration_min AS value,
                      pond_jour AS weight, ident_men AS household
               FROM read_parquet(?)""",
            cache.trips(selected),
        )
        users = _read_observations(
            con,
            """SELECT mode7 AS group_name, sum(duration_min) AS value,
                      any_value(pond_jour) AS weight,
                      any_value(ident_men) AS household
               FROM read_parquet(?) GROUP BY day_id, mode7""",
            cache.trips(selected),
        )
        days = _read_observations(
            con,
            """SELECT day_mode_group AS group_name, total_time_min AS value,
                      pond_jour AS weight, ident_men AS household
               FROM read_parquet(?)""",
            cache.days(selected),
        )
    return {
        **{("trip", key): value for key, value in trips.items()},
        **{("mode_user_day", key): value for key, value in users.items()},
        **{("day_mode_group", key): value for key, value in days.items()},
    }


def distribution_rows(
    sample_2008: dict[tuple[str, str], Observations],
    sample_2019: dict[tuple[str, str], Observations],
    *,
    trip_max: int,
    day_max: int,
    minimum_n: int,
    selected: scope_module.Scope = scope_module.REFERENCE_SCOPE,
) -> list[dict]:
    """Weighted ECDF and pooled-bandwidth KDE on a one-minute grid."""
    rows: list[dict] = []
    empty = Observations(np.array([]), np.array([]), np.array([]))
    for kind, group in sorted(sample_2008.keys() | sample_2019.keys()):
        samples = (sample_2008.get((kind, group), empty),
                   sample_2019.get((kind, group), empty))
        available = [sample for sample in samples if len(sample.values)]
        if not available:
            continue
        pooled_values = np.concatenate([sample.values for sample in available])
        pooled_weights = np.concatenate([
            sample.weights / sample.weights.sum() for sample in available
        ])
        bandwidth = daily_energy.weighted_gaussian_bandwidth(
            pooled_weights, pooled_values
        )
        if not np.isfinite(bandwidth) or bandwidth <= 0:
            LOGGER.warning("%s %s: KDE bandwidth is not positive", kind, group)
            bandwidth = float("nan")
        grid = np.arange((trip_max if kind == "trip" else day_max) + 1, dtype=float)
        for year, sample in zip((2008, 2019), samples, strict=True):
            n = len(sample.values)
            if n >= minimum_n:
                order = np.argsort(sample.values, kind="stable")
                cumulative = np.r_[0.0, np.cumsum(sample.weights[order])]
                index = np.searchsorted(sample.values[order], grid, side="right")
                ecdf = cumulative[index] / cumulative[-1]
                kde = (
                    daily_energy.weighted_gaussian_kde(
                        grid, sample.values, sample.weights, bandwidth
                    )
                    if np.isfinite(bandwidth)
                    else np.full(len(grid), np.nan)
                )
            for index, minute in enumerate(grid):
                rows.append({
                    "scope": selected.id, "kind": kind, "mode": group,
                    "year": year, "minute": int(minute), "n": n,
                    "bandwidth": float(bandwidth) if n >= minimum_n else None,
                    "ecdf": float(ecdf[index]) if n >= minimum_n else None,
                    "kde": float(kde[index]) if n >= minimum_n else None,
                })
    return rows
