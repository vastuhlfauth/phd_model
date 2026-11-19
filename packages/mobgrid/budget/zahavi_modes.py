"""Daily travel-time distributions by mode, section 9.9."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import duckdb
import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict, Field

from mobgrid.budget import (
    daily_energy,
    emp2019,
    entd2008,
    modes_cache,
    scope_cube,
    variation,
)
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr

LOGGER = logging.getLogger(__name__)


class ReportConfig(BaseModel):
    """Validated mode-report grids, bootstrap, paths and reference values."""

    model_config = ConfigDict(extra="forbid")

    trip_grid_max_min: int = Field(gt=0)
    day_grid_max_min: int = Field(gt=0)
    minimum_cell_n: int = Field(gt=0)
    thresholds_min: list[float] = Field(min_length=1)
    bootstrap_reps: int = Field(gt=0)
    seed: int = Field(ge=0)
    cache_dir: Path
    b3_report: Path
    logs_dir: Path
    reference_2008_min: float
    reference_2019_min: float
    reference_tolerance_min: float = Field(gt=0)


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
        samples = (
            sample_2008.get((kind, group), empty),
            sample_2019.get((kind, group), empty),
        )
        available = [sample for sample in samples if len(sample.values)]
        bandwidth = float("nan")
        if available:
            pooled_values = np.concatenate([sample.values for sample in available])
            pooled_weights = np.concatenate(
                [sample.weights / sample.weights.sum() for sample in available]
            )
            bandwidth = daily_energy.weighted_gaussian_bandwidth(
                pooled_weights, pooled_values
            )
        if available and (not np.isfinite(bandwidth) or bandwidth <= 0):
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
                rows.append(
                    {
                        "scope": selected.id,
                        "kind": kind,
                        "mode": group,
                        "year": year,
                        "minute": int(minute),
                        "n": n,
                        "bandwidth": float(bandwidth) if n >= minimum_n else None,
                        "ecdf": float(ecdf[index]) if n >= minimum_n else None,
                        "kde": float(kde[index]) if n >= minimum_n else None,
                    }
                )
    return rows


def weighted_deciles(sample: Observations, probabilities: np.ndarray) -> np.ndarray:
    """Interpolate weighted cumulative support points, in minutes."""
    valid = (
        np.isfinite(sample.values) & np.isfinite(sample.weights) & (sample.weights > 0)
    )
    if not valid.any():
        return np.full(len(probabilities), np.nan)
    values, inverse = np.unique(sample.values[valid], return_inverse=True)
    weights = np.bincount(inverse, weights=sample.weights[valid])
    cumulative = np.cumsum(weights) / weights.sum()
    return np.interp(probabilities, cumulative, values)


def threshold_shares(sample: Observations, thresholds: list[float]) -> np.ndarray:
    """Weighted shares of trips with duration at or above each threshold."""
    total = sample.weights.sum()
    if total <= 0:
        return np.full(len(thresholds), np.nan)
    return np.asarray(
        [
            np.sum(sample.weights[sample.values >= threshold]) / total
            for threshold in thresholds
        ]
    )


def weighted_ks(a: Observations, b: Observations) -> float:
    """Weighted two-sample KS distance, with no p-value."""
    if a.weights.sum() <= 0 or b.weights.sum() <= 0:
        return float("nan")
    points = np.union1d(a.values, b.values)

    def cdf(sample: Observations) -> np.ndarray:
        order = np.argsort(sample.values, kind="stable")
        cumulative = np.r_[0.0, np.cumsum(sample.weights[order])]
        indices = np.searchsorted(sample.values[order], points, side="right")
        return cumulative[indices] / cumulative[-1]

    return float(np.max(np.abs(cdf(a) - cdf(b))))


def crow_fly_bands(distance: np.ndarray, *, rounded: bool) -> np.ndarray:
    """Assign B4b crow-fly bands, preserving the observed same-commune flag."""
    km = vr._rounded_crow_fly_km(distance) if rounded else distance
    index = vr.distance_band_index(km)
    labels = np.asarray(vr.DISTANCE_BAND_LABELS, dtype=object)[index]
    labels[(km < 2) & (distance > 0)] = "under 2 km"
    labels[distance == 0] = "same commune"
    return labels


def read_band_samples(
    cache: modes_cache.SurveyCache,
    selected: scope_module.Scope,
    *,
    rounded: bool,
) -> dict[tuple[str, str], Observations]:
    """Read published or rounded crow-fly trip bands from the cache."""
    with duckdb.connect() as con:
        raw = con.execute(
            """SELECT mode7, duration_min, pond_jour, ident_men, crow_fly_km
               FROM read_parquet(?)""",
            [str(cache.trips(selected))],
        ).fetchnumpy()
    raw = {name: vr._plain_array(value) for name, value in raw.items()}
    km = np.asarray(raw["crow_fly_km"], dtype=float)
    values = np.asarray(raw["duration_min"], dtype=float)
    weights = np.asarray(raw["pond_jour"], dtype=float)
    mode = vr._text_values(raw["mode7"])
    household = vr._text_values(raw["ident_men"])
    valid = (
        np.isfinite(km)
        & (km >= 0)
        & np.isfinite(values)
        & (values >= 0)
        & np.isfinite(weights)
        & (weights > 0)
    )
    labels = crow_fly_bands(km, rounded=rounded)
    wanted = ("same commune", "under 2 km", *vr.SPEED_BAND_LABELS)
    return {
        (str(group), band): Observations(
            values[valid & (mode == group) & (labels == band)],
            weights[valid & (mode == group) & (labels == band)],
            household[valid & (mode == group) & (labels == band)],
        )
        for group in vr.MODE7_LABELS
        for band in wanted
    }


@dataclass(frozen=True)
class Draws:
    """One survey's shared household bootstrap draws."""

    households: np.ndarray
    multipliers: np.ndarray
    seed: int | np.random.SeedSequence

    def weights(self, sample: Observations, replicate: int) -> np.ndarray:
        codes = np.searchsorted(self.households, sample.household)
        if np.any(codes >= len(self.households)) or np.any(
            self.households[codes] != sample.household
        ):
            raise ValueError("bootstrap observations include households outside roster")
        return sample.weights * self.multipliers[replicate, codes]


def make_draws(
    household: np.ndarray, *, n_reps: int, seed: int | np.random.SeedSequence
) -> Draws:
    """Draw households once for all scopes and mode statistics, section 9.9."""
    universe = np.unique(household)
    return Draws(
        universe, scope_cube.multiplier_matrix(universe, n_reps=n_reps, seed=seed), seed
    )


def _interval(values: np.ndarray) -> tuple[float, float]:
    valid = values[np.isfinite(values)]
    if len(valid) < np.ceil(0.95 * len(values)):
        LOGGER.warning(
            "Only %d of %d bootstrap draws are valid", len(valid), len(values)
        )
        return float("nan"), float("nan")
    low, high = np.percentile(valid, [2.5, 97.5])
    return float(low), float(high)


def comparison_rows(
    samples_a: dict[tuple[str, str], Observations],
    samples_b: dict[tuple[str, str], Observations],
    draws_a: Draws,
    draws_b: Draws,
    *,
    thresholds: list[float],
    minimum_n: int,
    selected: scope_module.Scope = scope_module.REFERENCE_SCOPE,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Weighted deciles, threshold changes and KS with paired draws."""
    if len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("the two surveys must have the same number of draws")
    probabilities = np.arange(1, 10) / 10
    empty = Observations(np.array([]), np.array([]), np.array([]))
    deciles, shares, distances = [], [], []
    for kind, group in sorted(samples_a.keys() | samples_b.keys()):
        a = samples_a.get((kind, group), empty)
        b = samples_b.get((kind, group), empty)
        n_a, n_b = len(a.values), len(b.values)
        base = {
            "scope": selected.id,
            "kind": kind,
            "mode": group,
            "n_2008": n_a,
            "n_2019": n_b,
        }
        qa = weighted_deciles(a, probabilities)
        qb = weighted_deciles(b, probabilities)
        step_a = vr._weighted_quantile_values(a.values, a.weights, tuple(probabilities))
        step_b = vr._weighted_quantile_values(b.values, b.weights, tuple(probabilities))
        ta = threshold_shares(a, thresholds)
        tb = threshold_shares(b, thresholds)
        n_reps = len(draws_a.multipliers)
        qdiff = np.full((n_reps, len(probabilities)), np.nan)
        tdiff = np.full((n_reps, len(thresholds)), np.nan)
        ks_reps = np.full(n_reps, np.nan)
        if min(n_a, n_b) >= minimum_n:
            support = np.union1d(a.values, b.values)
            support_a = np.searchsorted(support, a.values)
            support_b = np.searchsorted(support, b.values)
            cutoff = np.searchsorted(support, thresholds, side="left")

            def bootstrap_summary(
                weights: np.ndarray, index: np.ndarray
            ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
                grouped = np.bincount(index, weights=weights, minlength=len(support))
                total = grouped.sum()
                if total <= 0:
                    return (
                        np.full(len(probabilities), np.nan),
                        np.full(len(thresholds), np.nan),
                        np.full(len(support), np.nan),
                    )
                cumulative = np.cumsum(grouped) / total
                nonzero = grouped > 0
                quantiles = np.interp(
                    probabilities, cumulative[nonzero], support[nonzero]
                )
                before = np.r_[0.0, cumulative][cutoff]
                return quantiles, 1 - before, cumulative

            for rep in range(n_reps):
                q_a, t_a, cdf_a = bootstrap_summary(draws_a.weights(a, rep), support_a)
                q_b, t_b, cdf_b = bootstrap_summary(draws_b.weights(b, rep), support_b)
                qdiff[rep] = q_b - q_a
                tdiff[rep] = t_b - t_a
                ks_reps[rep] = np.max(np.abs(cdf_a - cdf_b))
        for idx, probability in enumerate(probabilities):
            low, high = (
                _interval(qdiff[:, idx])
                if min(n_a, n_b) >= minimum_n
                else (np.nan, np.nan)
            )
            deciles.append(
                {
                    **base,
                    "decile": int(round(probability * 10)),
                    "interpolated_2008": qa[idx] if n_a >= minimum_n else np.nan,
                    "interpolated_2019": qb[idx] if n_b >= minimum_n else np.nan,
                    "step_2008": step_a[idx] if n_a >= minimum_n else np.nan,
                    "step_2019": step_b[idx] if n_b >= minimum_n else np.nan,
                    "shift": qb[idx] - qa[idx]
                    if min(n_a, n_b) >= minimum_n
                    else np.nan,
                    "ci_low": low,
                    "ci_high": high,
                }
            )
        if kind == "trip":
            for idx, threshold in enumerate(thresholds):
                low, high = (
                    _interval(tdiff[:, idx])
                    if min(n_a, n_b) >= minimum_n
                    else (np.nan, np.nan)
                )
                shares.append(
                    {
                        **base,
                        "threshold_min": threshold,
                        "share_2008": ta[idx] if n_a >= minimum_n else np.nan,
                        "share_2019": tb[idx] if n_b >= minimum_n else np.nan,
                        "change_points": (
                            100 * (tb[idx] - ta[idx])
                            if min(n_a, n_b) >= minimum_n
                            else np.nan
                        ),
                        "ci_low_points": 100 * low,
                        "ci_high_points": 100 * high,
                    }
                )
        low, high = (
            _interval(ks_reps) if min(n_a, n_b) >= minimum_n else (np.nan, np.nan)
        )
        distances.append(
            {
                **base,
                "D": weighted_ks(a, b) if min(n_a, n_b) >= minimum_n else np.nan,
                "ci_low": low,
                "ci_high": high,
            }
        )
    return deciles, shares, distances


def band_decile_rows(
    samples_a: dict[tuple[str, str], Observations],
    samples_b: dict[tuple[str, str], Observations],
    draws_a: Draws,
    draws_b: Draws,
    *,
    minimum_n: int,
    variant: str,
    selected: scope_module.Scope = scope_module.REFERENCE_SCOPE,
) -> list[dict]:
    """Interpolate trip-duration deciles by mode and crow-fly band."""

    def keyed(samples: dict[tuple[str, str], Observations]) -> dict:
        return {
            ("band", f"{mode}|{band}"): sample
            for (mode, band), sample in samples.items()
        }

    deciles, _, _ = comparison_rows(
        keyed(samples_a),
        keyed(samples_b),
        draws_a,
        draws_b,
        thresholds=[],
        minimum_n=minimum_n,
        selected=selected,
    )
    for row in deciles:
        row["mode"], row["band"] = row["mode"].split("|", 1)
        row["distance_variant"] = variant
        del row["kind"]
    return deciles


@dataclass(frozen=True)
class Metric:
    """Weighted estimate and its household replicates."""

    value: float
    replicates: np.ndarray


def person_mode_metrics(
    cache: modes_cache.SurveyCache,
    selected: scope_module.Scope,
    draws: Draws,
) -> dict[str, Metric]:
    """Per-person mode minutes, including zero days, section 9.9."""
    columns = ", ".join(
        f"coalesce(sum(t.duration_min) FILTER (WHERE t.mode7 = '{mode}'), 0) AS {mode}"
        for mode in vr.MODE7_LABELS
    )
    with duckdb.connect() as con:
        people = con.execute(
            "SELECT ident_men, weight FROM read_parquet(?)", [str(cache.roster)]
        ).fetchnumpy()
        days = con.execute(
            f"""
            SELECT b.day_id, b.ident_men, b.pond_jour, b.is_round, {columns}
            FROM read_parquet(?) b
            LEFT JOIN read_parquet(?) t ON b.day_id = t.day_id
            GROUP BY b.day_id, b.ident_men, b.pond_jour, b.is_round
            """,
            [str(cache.day_base), str(cache.trips(selected))],
        ).fetchnumpy()
    people = {k: vr._plain_array(v) for k, v in people.items()}
    days = {k: vr._plain_array(v) for k, v in days.items()}
    open_days = (
        ~np.asarray(days["is_round"], dtype=bool)
        if selected.days == "round"
        else np.zeros(len(days["is_round"]), dtype=bool)
    )
    values = {mode: np.asarray(days[mode], dtype=float) for mode in vr.MODE7_LABELS}
    values["All"] = np.sum(np.stack(list(values.values())), axis=0)
    results = {}
    for mode, duration in values.items():
        point, reps = daily_energy.bootstrap_person_value_replicates(
            vr._text_values(people["ident_men"]),
            np.asarray(people["weight"], dtype=float),
            vr._text_values(days["ident_men"]),
            np.asarray(days["pond_jour"], dtype=float),
            duration,
            open_days=open_days,
            n_reps=len(draws.multipliers),
            seed=draws.seed,
            household_universe=draws.households,
        )
        results[mode] = Metric(point, reps)
    return results


def mean_metric(sample: Observations, draws: Draws) -> Metric:
    """Day-weighted mean and the shared household replicates, minutes."""
    if not len(sample.values):
        return Metric(float("nan"), np.full(len(draws.multipliers), np.nan))
    point = float(np.sum(sample.values * sample.weights) / np.sum(sample.weights))
    reps = np.full(len(draws.multipliers), np.nan)
    for rep in range(len(reps)):
        weights = draws.weights(sample, rep)
        if weights.sum() > 0:
            reps[rep] = np.sum(weights * sample.values) / weights.sum()
    return Metric(point, reps)


def mode_shares(
    samples: dict[tuple[str, str], Observations], mode: str
) -> tuple[float, float, int]:
    """Weighted shares of trips and minutes attributable to a trip mode."""
    trips = {
        group: sample for (kind, group), sample in samples.items() if kind == "trip"
    }
    if mode not in trips:
        return float("nan"), float("nan"), 0
    total_weight = sum(float(sample.weights.sum()) for sample in trips.values())
    total_minutes = sum(
        float(np.sum(sample.weights * sample.values)) for sample in trips.values()
    )
    sample = trips[mode]
    if total_weight <= 0:
        return float("nan"), float("nan"), len(sample.values)
    return (
        float(sample.weights.sum() / total_weight),
        float(np.sum(sample.weights * sample.values) / total_minutes)
        if total_minutes > 0
        else float("nan"),
        len(sample.values),
    )


def stability_rows(
    samples_a: dict[tuple[str, str], Observations],
    samples_b: dict[tuple[str, str], Observations],
    person_a: dict[str, Metric],
    person_b: dict[str, Metric],
    draws_a: Draws,
    draws_b: Draws,
    *,
    minimum_n: int,
    margin: float,
    secondary_margin: float,
    selected: scope_module.Scope = scope_module.REFERENCE_SCOPE,
) -> list[dict]:
    """Means and equivalence comparisons of three mode-budget estimands."""
    empty = Observations(np.array([]), np.array([]), np.array([]))
    rows = []
    keys = sorted(
        {key for key in samples_a.keys() | samples_b.keys() if key[0] != "trip"}
        | {("per_person", mode) for mode in vr.MODE7_LABELS}
    )
    for kind, group in keys:
        sample_kind = "mode_user_day" if kind == "per_person" else kind
        a = samples_a.get((sample_kind, group), empty)
        b = samples_b.get((sample_kind, group), empty)
        n_a, n_b = len(a.values), len(b.values)
        ma = person_a[group] if kind == "per_person" else mean_metric(a, draws_a)
        mb = person_b[group] if kind == "per_person" else mean_metric(b, draws_b)
        la, ha = _interval(ma.replicates) if n_a >= minimum_n else (np.nan, np.nan)
        lb, hb = _interval(mb.replicates) if n_b >= minimum_n else (np.nan, np.nan)
        ratio = low = high = np.nan
        verdict = secondary_verdict = ""
        if (
            min(n_a, n_b) >= minimum_n
            and np.isfinite(ma.value)
            and np.isfinite(mb.value)
            and ma.value > 0
            and mb.value > 0
        ):
            ratio, (low, high) = daily_energy.bootstrap_replicate_ratio_ci(
                ma.value, ma.replicates, mb.value, mb.replicates
            )
            verdict = vr._equivalence_verdict((low, high), margin)
            secondary_verdict = vr._equivalence_verdict((low, high), secondary_margin)
        row = {
            "scope": selected.id,
            "kind": kind,
            "mode": group,
            "n_2008": n_a,
            "n_2019": n_b,
            "mean_2008": ma.value if n_a >= minimum_n else np.nan,
            "mean_2019": mb.value if n_b >= minimum_n else np.nan,
            "ci_2008_low": la,
            "ci_2008_high": ha,
            "ci_2019_low": lb,
            "ci_2019_high": hb,
            "ratio": ratio,
            "ratio_ci_low": low,
            "ratio_ci_high": high,
            "verdict_15": verdict,
            "verdict_10": secondary_verdict,
        }
        if kind == "per_person":
            trip_a, minutes_a, trip_n_a = mode_shares(samples_a, group)
            trip_b, minutes_b, trip_n_b = mode_shares(samples_b, group)
            enough_a, enough_b = trip_n_a >= minimum_n, trip_n_b >= minimum_n
            row.update(
                {
                    "trip_n_2008": trip_n_a,
                    "trip_n_2019": trip_n_b,
                    "trip_share_2008": trip_a if enough_a else np.nan,
                    "trip_share_2019": trip_b if enough_b else np.nan,
                    "trip_share_change_points": (
                        100 * (trip_b - trip_a) if enough_a and enough_b else np.nan
                    ),
                    "minute_share_2008": minutes_a if enough_a else np.nan,
                    "minute_share_2019": minutes_b if enough_b else np.nan,
                    "minute_share_change_points": (
                        100 * (minutes_b - minutes_a)
                        if enough_a and enough_b
                        else np.nan
                    ),
                }
            )
        rows.append(row)
    return rows


def b3_source_counts(report: Path) -> dict[str, tuple[int, int]]:
    """Read B3's published trip counts without rebuilding its point terms."""
    text = report.read_text(encoding="utf-8")
    marker = "## B3. Mode shift-share, 2008 -> 2019"
    if marker not in text:
        raise ValueError(f"B3 section is missing: {report}")
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    counts = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if line.startswith("|") and cells[0] in vr.MODE7_LABELS:
            if len(cells) != 15:
                raise ValueError(f"unrecognised B3 mode row: {line}")
            counts[cells[0]] = (int(cells[1]), int(cells[2]))
    return counts


def _b3_sample(
    cache: modes_cache.SurveyCache, selected: scope_module.Scope
) -> variation.TripSample:
    with duckdb.connect() as con:
        days = con.execute(
            "SELECT pond_jour, ident_men FROM read_parquet(?)",
            [str(cache.days(selected))],
        ).fetchnumpy()
        trips = con.execute(
            """SELECT pond_jour, ident_men, duration_min, distance_km, mode7
               FROM read_parquet(?)""",
            [str(cache.trips(selected))],
        ).fetchnumpy()
    days = {key: vr._plain_array(value) for key, value in days.items()}
    trips = {key: vr._plain_array(value) for key, value in trips.items()}
    return vr.trip_sample_from_frames(
        vr.SurveyFrames("cached", days, trips, {}), vr._text_values(trips["mode7"])
    )


def b3_missing_intervals(
    a: variation.TripSample,
    b: variation.TripSample,
    draws_a: Draws,
    draws_b: Draws,
    *,
    minimum_n: int,
) -> dict[str, dict[str, tuple[float, float]]]:
    """Bootstrap only B3's missing per-mode intervals using its own estimator."""
    counts_a = {mode: int(np.sum(a.trip_group == mode)) for mode in vr.MODE7_LABELS}
    counts_b = {mode: int(np.sum(b.trip_group == mode)) for mode in vr.MODE7_LABELS}
    groups = [
        mode
        for mode in vr.MODE7_LABELS
        if min(counts_a[mode], counts_b[mode]) >= minimum_n
    ]
    fields = {
        "mix": "mix_min",
        "within": "within_min",
        "km_per_trip": "within_km_min",
        "speed": "within_speed_min",
        "selection": "within_selection_min",
        "interaction": "interaction_min",
    }
    n_reps = len(draws_a.multipliers)
    if n_reps != len(draws_b.multipliers):
        raise ValueError("the two surveys must have the same number of draws")
    estimates = {
        mode: {name: np.full(n_reps, np.nan) for name in fields} for mode in groups
    }
    _, day_a = daily_energy._bootstrap_household_codes(
        a.day_household, draws_a.households
    )
    _, trip_a = daily_energy._bootstrap_household_codes(
        a.trip_household, draws_a.households
    )
    _, day_b = daily_energy._bootstrap_household_codes(
        b.day_household, draws_b.households
    )
    _, trip_b = daily_energy._bootstrap_household_codes(
        b.trip_household, draws_b.households
    )
    for rep in range(n_reps):
        ga = a.to_groups(
            draws_a.multipliers[rep, day_a], draws_a.multipliers[rep, trip_a]
        )
        gb = b.to_groups(
            draws_b.multipliers[rep, day_b], draws_b.multipliers[rep, trip_b]
        )
        if (
            min(
                ga.day_weight_total,
                gb.day_weight_total,
                ga.weight.sum(),
                gb.weight.sum(),
            )
            <= 0
        ):
            continue
        result = variation.shift_share(ga, gb)
        terms = {term.group: term for term in result.terms}
        for mode in groups:
            if (
                mode not in terms
                or ga.weight[ga.group == mode].sum() <= 0
                or gb.weight[gb.group == mode].sum() <= 0
            ):
                continue
            for name, attr in fields.items():
                estimates[mode][name][rep] = getattr(terms[mode], attr)
    return {
        mode: {name: _interval(values) for name, values in metrics.items()}
        for mode, metrics in estimates.items()
    }


def b3_excerpt(
    report: Path,
    *,
    minimum_n: int,
    new_intervals: dict[str, dict[str, tuple[float, float]]] | None = None,
) -> str:
    """Quote B3 without recomputing its decomposition, section 9.9."""
    text = report.read_text(encoding="utf-8")
    if f"`{scope_module.REFERENCE_SCOPE.id}`" not in text.split("## ", 1)[0]:
        raise ValueError(f"B3 source is not the reference scope: {report}")
    marker = "## B3. Mode shift-share, 2008 -> 2019"
    if marker not in text:
        raise ValueError(f"B3 section is missing: {report}")
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    lines = []
    fractions = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if line.startswith("|") and cells[0] in vr.MODE7_LABELS:
            if len(cells) != 15:
                raise ValueError(f"unrecognised B3 mode row: {line}")
            n_a, n_b = int(cells[1]), int(cells[2])
            if min(n_a, n_b) < minimum_n:
                cells[3:] = ["-"] * 12
                line = "| " + " | ".join(cells) + " |"
            else:
                try:
                    within, km, speed = (float(cells[i]) for i in (8, 9, 10))
                except ValueError as exc:
                    raise ValueError(f"invalid B3 mode terms: {line}") from exc
                if within:
                    fractions.append(
                        f"| {cells[0]} | {n_a} | {n_b} | {km / within:.1%} | "
                        f"{speed / within:.1%} |"
                    )
                else:
                    fractions.append(f"| {cells[0]} | {n_a} | {n_b} | - | - |")
        lines.append(line)
    if not any("trips volume" in line for line in lines):
        raise ValueError(f"B3 aggregate table is missing: {report}")
    ci_note = (
        "B3's aggregate intervals are quoted above. Its per-mode intervals "
        "were not published; the table below adds 95% intervals from the "
        "existing B3 estimator using the shared household draws."
        if new_intervals
        else "B3's aggregate intervals are quoted above. Its per-mode terms have "
        "no confidence intervals in the source; those intervals are unavailable."
    )
    interval_lines = []
    if new_intervals:
        counts = b3_source_counts(report)
        fields = ("mix", "within", "km_per_trip", "speed", "selection", "interaction")
        interval_lines = [
            "| Mode | n 2008 | n 2019 | " + " | ".join(fields) + " |",
            "|---|---:|---:|" + "---|" * len(fields),
            *[
                "| "
                + mode
                + " | "
                + str(counts[mode][0])
                + " | "
                + str(counts[mode][1])
                + " | "
                + " | ".join(
                    f"[{low:.2f}, {high:.2f}]"
                    if np.isfinite(low) and np.isfinite(high)
                    else "-"
                    for low, high in (metrics[field] for field in fields)
                )
                + " |"
                for mode, metrics in new_intervals.items()
            ],
            "",
        ]
    return "\n".join(
        [
            "## B3: quoted mode decomposition",
            *lines,
            "",
            ci_note,
            "",
            *interval_lines,
            "",
            "Shares below divide B3's rounded km and speed terms by its rounded "
            "within-mode term; they are signed and approximate, can exceed 100%, "
            "and exclude the separately reported selection residual.",
            "",
            "| Mode | n 2008 | n 2019 | km/trip / within | speed / within |",
            "|---|---:|---:|---:|---:|",
            *fractions,
        ]
    )


@contextmanager
def _timed(timings: dict[str, float], stage: str) -> Generator[None]:
    start = time.monotonic()
    LOGGER.info("%s: started", stage)
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        timings[stage] = timings.get(stage, 0.0) + elapsed
        LOGGER.info("%s: ended after %.2f s", stage, elapsed)


def _roster_households(cache: modes_cache.SurveyCache) -> np.ndarray:
    with duckdb.connect() as con:
        rows = con.execute(
            "SELECT ident_men FROM read_parquet(?)", [str(cache.roster)]
        ).fetchnumpy()
    return vr._text_values(vr._plain_array(rows["ident_men"]))


def _include_empty_samples(samples: dict[tuple[str, str], Observations]) -> None:
    empty = Observations(np.array([]), np.array([]), np.array([]))
    for mode in vr.MODE7_LABELS:
        samples.setdefault(("trip", mode), empty)
        samples.setdefault(("mode_user_day", mode), empty)
    for mode in (*daily_energy.DAY_MODE_GROUPS, "multimodal", "other"):
        samples.setdefault(("day_mode_group", mode), empty)


def _sample_counts(
    cache: modes_cache.SurveyCache, selected: scope_module.Scope
) -> tuple[int, int, int]:
    with duckdb.connect() as con:
        counts = []
        for path in (cache.roster, cache.day_base, cache.trips(selected)):
            row = con.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(path)]
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Could not count cache rows: {path}")
            counts.append(int(row[0]))
    return counts[0], counts[1], counts[2]


def _csv_rows(path: Path, rows: list[dict], required: tuple[str, ...]) -> None:
    keys = list(dict.fromkeys([*required, *(key for row in rows for key in row)]))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        ""
                        if value is None
                        or (
                            isinstance(value, (float, np.floating))
                            and not np.isfinite(value)
                        )
                        else scope_cube._csv_value(value)
                    )
                    for key, value in row.items()
                }
            )


def _cell(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, (float, np.floating)):
        return f"{value:.3f}" if np.isfinite(value) else "-"
    return str(value).replace("|", "\\|")


def _markdown_table(
    title: str, selected: scope_module.Scope, rows: list[dict], fields: tuple[str, ...]
) -> list[str]:
    lines = [
        f"### {title}",
        "",
        f"Scope: {selected.label} (`{selected.id}`), Monday–Friday.",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_cell(row.get(field)) for field in fields) + " |"
        for row in rows
    )
    lines.extend(
        [
            "",
            "n is the unweighted count shown in each row; sources: ENTD 2008 and "
            "EMP 2019 cached scoped weekday tables, section 9.9.",
            scope_module.DAYTABLE_COVERAGE_NOTE
            if selected.distance == "daytable"
            else "",
            "",
        ]
    )
    return lines


def run_report(
    out_dir: Path,
    cache_2008: modes_cache.SurveyCache,
    cache_2019: modes_cache.SurveyCache,
    config: ReportConfig,
    *,
    selected_scopes: list[scope_module.Scope],
    equivalence_margin: float,
    secondary_margin: float,
) -> dict[str, float]:
    """Write all mode tables from cached data, section 9.9."""
    out_dir.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    with _timed(timings, "shared household draws"):
        seed_a, seed_b = np.random.SeedSequence(config.seed).spawn(2)
        draws_a = make_draws(
            _roster_households(cache_2008), n_reps=config.bootstrap_reps, seed=seed_a
        )
        draws_b = make_draws(
            _roster_households(cache_2019), n_reps=config.bootstrap_reps, seed=seed_b
        )
    distributions: list[dict] = []
    deciles: list[dict] = []
    thresholds: list[dict] = []
    ks: list[dict] = []
    bands: list[dict] = []
    stability: list[dict] = []
    references: list[str] = []
    b3_intervals: dict[str, dict[str, tuple[float, float]]] | None = None
    for selected in selected_scopes:
        with _timed(timings, "read scoped samples"):
            samples_a = read_samples(cache_2008, selected)
            samples_b = read_samples(cache_2019, selected)
            _include_empty_samples(samples_a)
            _include_empty_samples(samples_b)
        with _timed(timings, "distributions"):
            distributions.extend(
                distribution_rows(
                    samples_a,
                    samples_b,
                    trip_max=config.trip_grid_max_min,
                    day_max=config.day_grid_max_min,
                    minimum_n=config.minimum_cell_n,
                    selected=selected,
                )
            )
        with _timed(timings, "distribution comparisons"):
            q, t, k = comparison_rows(
                samples_a,
                samples_b,
                draws_a,
                draws_b,
                thresholds=config.thresholds_min,
                minimum_n=config.minimum_cell_n,
                selected=selected,
            )
            deciles.extend(q)
            thresholds.extend(t)
            ks.extend(k)
        with _timed(timings, "crow-fly band comparisons"):
            band_a = read_band_samples(cache_2008, selected, rounded=False)
            for variant, rounded in (("published", False), ("emp_rounded_km", True)):
                band_b = read_band_samples(cache_2019, selected, rounded=rounded)
                bands.extend(
                    band_decile_rows(
                        band_a,
                        band_b,
                        draws_a,
                        draws_b,
                        minimum_n=config.minimum_cell_n,
                        variant=variant,
                        selected=selected,
                    )
                )
        if selected == scope_module.REFERENCE_SCOPE:
            with _timed(timings, "stability"):
                person_a = person_mode_metrics(cache_2008, selected, draws_a)
                person_b = person_mode_metrics(cache_2019, selected, draws_b)
                stability.extend(
                    stability_rows(
                        samples_a,
                        samples_b,
                        person_a,
                        person_b,
                        draws_a,
                        draws_b,
                        minimum_n=config.minimum_cell_n,
                        margin=equivalence_margin,
                        secondary_margin=secondary_margin,
                        selected=selected,
                    )
                )
                for year, person, expected in (
                    (2008, person_a, config.reference_2008_min),
                    (2019, person_b, config.reference_2019_min),
                ):
                    actual = person["All"].value
                    match = abs(actual - expected) <= config.reference_tolerance_min
                    message = (
                        f"{year}: {actual:.3f} min/person; published scope-cube "
                        f"reference {expected:.1f} min; "
                        f"{'matches' if match else 'DIFFERS'}."
                    )
                    references.append(message)
                    if not match:
                        LOGGER.warning(message)
            with _timed(timings, "missing B3 mode intervals"):
                source_counts = b3_source_counts(config.b3_report)
                if source_counts:
                    b3_a = _b3_sample(cache_2008, selected)
                    b3_b = _b3_sample(cache_2019, selected)
                    actual_counts = {
                        mode: (
                            int(np.sum(b3_a.trip_group == mode)),
                            int(np.sum(b3_b.trip_group == mode)),
                        )
                        for mode in vr.MODE7_LABELS
                    }
                    if any(
                        actual_counts[mode] != count
                        for mode, count in source_counts.items()
                    ):
                        LOGGER.warning(
                            "B3 source trip counts differ from the cache; "
                            "new per-mode intervals are unavailable."
                        )
                    else:
                        b3_intervals = b3_missing_intervals(
                            b3_a,
                            b3_b,
                            draws_a,
                            draws_b,
                            minimum_n=config.minimum_cell_n,
                        )
                else:
                    LOGGER.warning(
                        "B3 source has no mode rows; intervals are unavailable."
                    )
    datasets = {
        "distributions.csv": (
            distributions,
            ("scope", "kind", "mode", "year", "minute"),
        ),
        "deciles.csv": (deciles, ("scope", "kind", "mode", "decile")),
        "thresholds.csv": (thresholds, ("scope", "kind", "mode", "threshold_min")),
        "ks.csv": (ks, ("scope", "kind", "mode")),
        "band_deciles.csv": (
            bands,
            ("scope", "distance_variant", "mode", "band", "decile"),
        ),
        "stability.csv": (stability, ("scope", "kind", "mode")),
    }
    with _timed(timings, "write outputs"):
        for filename, (rows, required) in datasets.items():
            _csv_rows(out_dir / filename, rows, required)
        lines = [
            "# Daily travel time by mode: Zahavi supplement",
            "",
            "Monday–Friday. ENTD 2008 and EMP 2019; section 9.9. "
            f"{config.bootstrap_reps} independent household draws per survey "
            "are shared across scopes and statistics. Cells under "
            f"{config.minimum_cell_n} observations are suppressed.",
            "",
            "Deciles linearly interpolate cumulative weights at distinct duration "
            "support points; step deciles are also shown. KS is a weighted distance, "
            "not a significance test. Threshold changes are percentage points.",
            "",
            "Per-person values include days without trips as zero; open days are "
            "removed from numerator and denominator for round-trip scopes. "
            "Day-mode groups include walking plus the single non-walking mode; "
            "they are not the same estimand as mode-user days.",
            "",
            *references,
            "",
            "KDE bandwidths are pooled by mode and kind, with each survey given "
            "equal total weight; Gaussian densities are not boundary corrected. "
            "The complete minute grids are in `step12_modes/distributions.csv`.",
            "",
        ]
        for selected in selected_scopes:

            def scoped(rows: list[dict]) -> list[dict]:
                return [row for row in rows if row["scope"] == selected.id]

            count_rows = [row for row in scoped(distributions) if row["minute"] == 0]
            lines += _markdown_table(
                "Distribution samples",
                selected,
                count_rows,
                ("kind", "mode", "year", "n", "bandwidth"),
            )
            lines += _markdown_table(
                "Deciles",
                selected,
                scoped(deciles),
                (
                    "kind",
                    "mode",
                    "n_2008",
                    "n_2019",
                    "decile",
                    "interpolated_2008",
                    "interpolated_2019",
                    "step_2008",
                    "step_2019",
                    "shift",
                    "ci_low",
                    "ci_high",
                ),
            )
            lines += _markdown_table(
                "Trip thresholds",
                selected,
                scoped(thresholds),
                (
                    "mode",
                    "n_2008",
                    "n_2019",
                    "threshold_min",
                    "share_2008",
                    "share_2019",
                    "change_points",
                    "ci_low_points",
                    "ci_high_points",
                ),
            )
            lines += _markdown_table(
                "Weighted KS distances",
                selected,
                scoped(ks),
                ("kind", "mode", "n_2008", "n_2019", "D", "ci_low", "ci_high"),
            )
            lines += _markdown_table(
                "Crow-fly band deciles",
                selected,
                scoped(bands),
                (
                    "distance_variant",
                    "mode",
                    "band",
                    "n_2008",
                    "n_2019",
                    "decile",
                    "interpolated_2008",
                    "interpolated_2019",
                    "shift",
                    "ci_low",
                    "ci_high",
                ),
            )
            if selected == scope_module.REFERENCE_SCOPE:
                lines += _markdown_table(
                    "Mode stability",
                    selected,
                    stability,
                    (
                        "kind",
                        "mode",
                        "n_2008",
                        "n_2019",
                        "mean_2008",
                        "ci_2008_low",
                        "ci_2008_high",
                        "mean_2019",
                        "ci_2019_low",
                        "ci_2019_high",
                        "ratio",
                        "ratio_ci_low",
                        "ratio_ci_high",
                        "verdict_15",
                        "verdict_10",
                    ),
                )
                lines += _markdown_table(
                    "Mode shares",
                    selected,
                    [row for row in stability if row["kind"] == "per_person"],
                    (
                        "mode",
                        "trip_n_2008",
                        "trip_n_2019",
                        "trip_share_2008",
                        "trip_share_2019",
                        "trip_share_change_points",
                        "minute_share_2008",
                        "minute_share_2019",
                        "minute_share_change_points",
                    ),
                )
                lines += [
                    f"Scope: {selected.label} (`{selected.id}`), Monday–Friday.",
                    "",
                    b3_excerpt(
                        config.b3_report,
                        minimum_n=config.minimum_cell_n,
                        new_intervals=b3_intervals,
                    ),
                    "",
                    f"Source: {config.b3_report}; sample counts are in B3's table. "
                    "This previously generated source is not recomputed; verify its "
                    "freshness against the input surveys.",
                    "",
                ]
        out_dir.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    return timings


class _WarningCounter(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def main(argv: list[str] | None = None) -> int:
    """CLI for cached mode reports, section 9.9."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--modes-config", type=Path, default=vr.ROOT / "config" / "zahavi_modes.yaml"
    )
    parser.add_argument("--config", type=Path, default=vr.DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--variation-config",
        type=Path,
        default=scope_cube.DEFAULT_VARIATION_CONFIG_PATH,
    )
    parser.add_argument("--scope", default="all")
    parser.add_argument(
        "--emp2019-data-path", type=Path, default=emp2019.DEFAULT_DATA_PATH
    )
    parser.add_argument(
        "--entd2008-data-path", type=Path, default=entd2008.DEFAULT_DATA_PATH
    )
    args = parser.parse_args(argv)
    with args.modes_config.open(encoding="utf-8") as stream:
        config = ReportConfig.model_validate(yaml.safe_load(stream))
    config = config.model_copy(
        update={
            "cache_dir": vr.ROOT / config.cache_dir,
            "b3_report": vr.ROOT / config.b3_report,
            "logs_dir": vr.ROOT / config.logs_dir,
        }
    )
    variation_config = variation.load_variation_config(args.variation_config)
    selected_scopes = (
        list(scope_module.ALL_SCOPES)
        if args.scope == "all"
        else [scope_module.Scope.parse(args.scope)]
    )
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    log_path = config.logs_dir / f"{stamp}_zahavi_modes.log"
    summary_path = config.logs_dir / f"{stamp}_zahavi_modes_summary.md"
    counter = _WarningCounter()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    old_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    for handler in (file_handler, stream_handler, counter):
        root_logger.addHandler(handler)
    timings: dict[str, float] = {}
    counts: list[str] = []
    success = False
    try:
        with _timed(timings, "load 2008 cache"):
            cache_a = modes_cache.load_survey(
                entd2008,
                args.entd2008_data_path,
                config.cache_dir,
                activity_stay_min=variation_config.scope.activity_stay_min,
                config_path=args.config,
            )
        with _timed(timings, "load 2019 cache"):
            cache_b = modes_cache.load_survey(
                emp2019,
                args.emp2019_data_path,
                config.cache_dir,
                activity_stay_min=variation_config.scope.activity_stay_min,
                config_path=args.config,
            )
        with _timed(timings, "count reference samples"):
            for label, cache in (("ENTD 2008", cache_a), ("EMP 2019", cache_b)):
                roster, days, trips = _sample_counts(
                    cache, scope_module.REFERENCE_SCOPE
                )
                counts.append(
                    f"{label}: {roster} roster persons, {days} described weekdays, "
                    f"{trips} reference-scope trips."
                )
        timings.update(
            run_report(
                args.out,
                cache_a,
                cache_b,
                config,
                selected_scopes=selected_scopes,
                equivalence_margin=variation_config.equivalence_margin,
                secondary_margin=variation_config.secondary_equivalence_margin,
            )
        )
        success = True
    finally:
        if not success:
            LOGGER.error("Mode report failed; see traceback and log.")
        lines = [
            "# Zahavi mode report summary",
            "",
            f"Status: {'completed' if success else 'failed'}.",
            f"Input surveys: {args.entd2008_data_path}; {args.emp2019_data_path}.",
            f"Scopes: {', '.join(selected.id for selected in selected_scopes)}.",
            f"Household draws per survey: {config.bootstrap_reps}.",
            *counts,
            f"Output: {args.out}; report: {args.out.with_suffix('.md')}.",
            "",
            "## Stage timings (seconds)",
            *[f"- {stage}: {seconds:.2f}" for stage, seconds in timings.items()],
            "",
            "## Warnings",
            *([f"- {message}" for message in counter.messages] or ["- None."]),
        ]
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        for handler in (file_handler, stream_handler, counter):
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(old_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
