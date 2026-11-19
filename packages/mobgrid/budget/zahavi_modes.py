"""Daily travel-time distributions by mode, section 9.9."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np

from mobgrid.budget import daily_energy, modes_cache, scope_cube
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
    return np.asarray([
        np.sum(sample.weights[sample.values >= threshold]) / total
        for threshold in thresholds
    ])


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
        np.isfinite(km) & (km >= 0) & np.isfinite(values) & (values >= 0)
        & np.isfinite(weights) & (weights > 0)
    )
    labels = crow_fly_bands(km, rounded=rounded)
    wanted = ("same commune", "under 2 km", *vr.SPEED_BAND_LABELS)
    return {
        (str(group), band): Observations(values[mask], weights[mask], household[mask])
        for group in vr.MODE7_LABELS for band in wanted
        if (mask := valid & (mode == group) & (labels == band)).any()
    }


@dataclass(frozen=True)
class Draws:
    """One survey's shared household bootstrap draws."""

    households: np.ndarray
    multipliers: np.ndarray
    seed: int | np.random.SeedSequence

    def weights(self, sample: Observations, replicate: int) -> np.ndarray:
        _, codes = daily_energy._bootstrap_household_codes(
            sample.household, self.households
        )
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
        base = {"scope": selected.id, "kind": kind, "mode": group,
                "n_2008": n_a, "n_2019": n_b}
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
            for rep in range(n_reps):
                aa = Observations(a.values, draws_a.weights(a, rep), a.household)
                bb = Observations(b.values, draws_b.weights(b, rep), b.household)
                qdiff[rep] = weighted_deciles(bb, probabilities) - weighted_deciles(
                    aa, probabilities
                )
                tdiff[rep] = threshold_shares(bb, thresholds) - threshold_shares(
                    aa, thresholds
                )
                ks_reps[rep] = weighted_ks(aa, bb)
        for idx, probability in enumerate(probabilities):
            low, high = _interval(qdiff[:, idx]) if min(n_a, n_b) >= minimum_n else (
                np.nan, np.nan
            )
            deciles.append({
                **base, "decile": int(round(probability * 10)),
                "interpolated_2008": qa[idx] if n_a >= minimum_n else np.nan,
                "interpolated_2019": qb[idx] if n_b >= minimum_n else np.nan,
                "step_2008": step_a[idx] if n_a >= minimum_n else np.nan,
                "step_2019": step_b[idx] if n_b >= minimum_n else np.nan,
                "shift": qb[idx] - qa[idx] if min(n_a, n_b) >= minimum_n else np.nan,
                "ci_low": low, "ci_high": high,
            })
        if kind == "trip":
            for idx, threshold in enumerate(thresholds):
                low, high = (
                    _interval(tdiff[:, idx])
                    if min(n_a, n_b) >= minimum_n else (np.nan, np.nan)
                )
                shares.append({
                    **base, "threshold_min": threshold,
                    "share_2008": ta[idx] if n_a >= minimum_n else np.nan,
                    "share_2019": tb[idx] if n_b >= minimum_n else np.nan,
                    "change_points": (
                        100 * (tb[idx] - ta[idx]) if min(n_a, n_b) >= minimum_n
                        else np.nan
                    ),
                    "ci_low_points": 100 * low, "ci_high_points": 100 * high,
                })
        low, high = (
            _interval(ks_reps) if min(n_a, n_b) >= minimum_n else (np.nan, np.nan)
        )
        distances.append({
            **base, "D": weighted_ks(a, b) if min(n_a, n_b) >= minimum_n else np.nan,
            "ci_low": low, "ci_high": high,
        })
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
        return {("band", f"{mode}|{band}"): sample
                for (mode, band), sample in samples.items()}

    deciles, _, _ = comparison_rows(
        keyed(samples_a), keyed(samples_b), draws_a, draws_b,
        thresholds=[], minimum_n=minimum_n, selected=selected,
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
    return (
        float(sample.weights.sum() / total_weight),
        float(np.sum(sample.weights * sample.values) / total_minutes)
        if total_minutes > 0 else float("nan"),
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
            and np.isfinite(ma.value) and np.isfinite(mb.value)
            and ma.value > 0 and mb.value > 0
        ):
            ratio, (low, high) = daily_energy.bootstrap_replicate_ratio_ci(
                ma.value, ma.replicates, mb.value, mb.replicates
            )
            verdict = vr._equivalence_verdict((low, high), margin)
            secondary_verdict = vr._equivalence_verdict((low, high), secondary_margin)
        row = {
            "scope": selected.id, "kind": kind, "mode": group,
            "n_2008": n_a, "n_2019": n_b,
            "mean_2008": ma.value if n_a >= minimum_n else np.nan,
            "mean_2019": mb.value if n_b >= minimum_n else np.nan,
            "ci_2008_low": la, "ci_2008_high": ha,
            "ci_2019_low": lb, "ci_2019_high": hb,
            "ratio": ratio, "ratio_ci_low": low, "ratio_ci_high": high,
            "verdict_15": verdict, "verdict_10": secondary_verdict,
        }
        if kind == "per_person":
            trip_a, minutes_a, trip_n_a = mode_shares(samples_a, group)
            trip_b, minutes_b, trip_n_b = mode_shares(samples_b, group)
            enough_a, enough_b = trip_n_a >= minimum_n, trip_n_b >= minimum_n
            row.update({
                "trip_n_2008": trip_n_a, "trip_n_2019": trip_n_b,
                "trip_share_2008": trip_a if enough_a else np.nan,
                "trip_share_2019": trip_b if enough_b else np.nan,
                "trip_share_change_points": (
                    100 * (trip_b - trip_a) if enough_a and enough_b else np.nan
                ),
                "minute_share_2008": minutes_a if enough_a else np.nan,
                "minute_share_2019": minutes_b if enough_b else np.nan,
                "minute_share_change_points": (
                    100 * (minutes_b - minutes_a) if enough_a and enough_b else np.nan
                ),
            })
        rows.append(row)
    return rows


def b3_excerpt(report: Path, *, minimum_n: int) -> str:
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
    return "\n".join([
        "## B3: quoted mode decomposition",
        *lines,
        "",
        "B3's aggregate intervals are quoted above. Its per-mode terms have "
        "no confidence intervals in the source; those intervals are unavailable "
        "without additional bootstrap calculations.",
        "",
        "Shares below divide B3's rounded km and speed terms by its rounded "
        "within-mode term; they are signed and approximate, can exceed 100%, "
        "and exclude the separately reported selection residual.",
        "",
        "| Mode | n 2008 | n 2019 | km/trip / within | speed / within |",
        "|---|---:|---:|---:|---:|",
        *fractions,
    ])
