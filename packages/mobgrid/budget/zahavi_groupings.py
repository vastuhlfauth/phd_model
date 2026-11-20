"""Grouping comparisons of daily travel time, section 9.9."""

import logging
from dataclasses import dataclass
from itertools import product
from typing import Self

import duckdb
import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator

from mobgrid.budget import modes_cache
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr
from mobgrid.budget import zahavi_income as income_module
from mobgrid.budget import zahavi_modes as modes

LOGGER = logging.getLogger(__name__)

DAYTABLE_STATUS = (
    "ENTD 2008 day-table coverage beyond 80 km not established; not compared"
)


class OrderedDimension(BaseModel):
    """Ordered levels and preferred neighbouring pairs."""

    model_config = ConfigDict(extra="forbid")

    levels: list[str]
    preferred: list[tuple[str, str]]

    @model_validator(mode="after")
    def validate_neighbours(self) -> Self:
        if len(set(self.levels)) != len(self.levels) or not self.levels:
            raise ValueError("Ordered dimension levels must be unique and nonempty")
        for left, right in self.preferred:
            if left not in self.levels or right not in self.levels:
                raise ValueError("Preferred neighbour is not a configured level")
            if abs(self.levels.index(left) - self.levels.index(right)) != 1:
                raise ValueError("Preferred neighbours must be adjacent")
        return self


class MergeConfig(BaseModel):
    """Configured ordered dimensions; unlisted dimensions never merge."""

    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, OrderedDimension]


@dataclass(frozen=True)
class CellSample:
    """Daily minutes, survey weights, cell and parent labels, section 9.9."""

    values: np.ndarray
    weights: np.ndarray
    cells: np.ndarray
    parents: np.ndarray


@dataclass(frozen=True)
class FixedDistribution:
    """2008 minutes reweighted to 2019 cells and fallback weight share."""

    values: np.ndarray
    weights: np.ndarray
    fallback_share: float


@dataclass(frozen=True)
class GroupingDays:
    """Scoped travel days, survey weights and grouping attributes, section 9.9."""

    person: np.ndarray
    household: np.ndarray
    weights: np.ndarray
    minutes: np.ndarray
    attributes: dict[str, np.ndarray]


@dataclass(frozen=True)
class PreparedGrouping:
    """Fixed partition and its full-sample merge audit, section 9.9."""

    a: GroupingDays
    b: GroupingDays
    cells_a: np.ndarray
    cells_b: np.ndarray
    parents_a: np.ndarray
    parents_b: np.ndarray
    excluded_share_2008: float
    excluded_share_2019: float
    merges: list[tuple[str, str]]


@dataclass(frozen=True)
class GroupingResult:
    """Prepared partition, cell rows and statistics, section 9.9."""

    partition: PreparedGrouping
    cells: list[dict]
    summary: dict


@dataclass(frozen=True)
class PersonModeData:
    """Weekday person base, open days, and mode minutes, section 9.9."""

    roster_household: np.ndarray
    roster_weight: np.ndarray
    day_household: np.ndarray
    day_weight: np.ndarray
    is_open: np.ndarray
    minutes: np.ndarray
    used: np.ndarray
    modes: tuple[str, ...]


def read_person_modes(
    cache: modes_cache.SurveyCache, selected: scope_module.Scope
) -> PersonModeData:
    """Read the section 9.9 person base and scoped weekday mode minutes."""
    columns = ", ".join(
        f"coalesce(sum(t.duration_min) FILTER (WHERE t.mode7 = '{mode}'), 0) "
        f"AS minutes_{mode}, "
        f"count(*) FILTER (WHERE t.mode7 = '{mode}') > 0 AS used_{mode}"
        for mode in vr.MODE7_LABELS
    )
    labels = ", ".join(f"'{mode}'" for mode in vr.MODE7_LABELS)
    with duckdb.connect() as con:
        roster = con.execute(
            "SELECT ident_men, weight FROM read_parquet(?)", [str(cache.roster)]
        ).fetchnumpy()
        days = con.execute(
            f"""SELECT b.day_id, b.ident_men, b.pond_jour, b.is_round,
                count(*) FILTER (WHERE t.day_id IS NOT NULL AND
                    (t.mode7 IS NULL OR t.mode7 NOT IN ({labels}) OR
                     t.duration_min IS NULL OR NOT isfinite(t.duration_min) OR
                     t.duration_min < 0)) AS invalid_trips,
                {columns}
            FROM read_parquet(?) b LEFT JOIN read_parquet(?) t ON b.day_id = t.day_id
            GROUP BY b.day_id, b.ident_men, b.pond_jour, b.is_round
            ORDER BY b.day_id""",
            [str(cache.day_base), str(cache.trips(selected))],
        ).fetchnumpy()
    roster = {key: vr._plain_array(value) for key, value in roster.items()}
    days = {key: vr._plain_array(value) for key, value in days.items()}
    if np.any(days["invalid_trips"]):
        raise ValueError("Scoped cache contains invalid trip modes or minutes")
    is_open = (
        ~np.asarray(days["is_round"], dtype=bool)
        if selected.days == "round"
        else np.zeros(len(days["is_round"]), dtype=bool)
    )
    minutes = np.column_stack(
        [np.asarray(days[f"minutes_{mode}"], dtype=float) for mode in vr.MODE7_LABELS]
    )
    used = np.column_stack(
        [np.asarray(days[f"used_{mode}"], dtype=bool) for mode in vr.MODE7_LABELS]
    )
    if np.any(used[is_open]):
        raise ValueError("Scoped cache includes trips on an excluded open day")
    return PersonModeData(
        vr._text_values(roster["ident_men"]),
        np.asarray(roster["weight"], dtype=float),
        vr._text_values(days["ident_men"]),
        np.asarray(days["pond_jour"], dtype=float),
        is_open,
        minutes,
        used,
        vr.MODE7_LABELS,
    )


def _person_mode_values(
    data: PersonModeData, roster_weight: np.ndarray, day_weight: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float]:
    """Use shares and minutes per user day against the kept-person base."""
    denominator = float(roster_weight.sum() - day_weight[data.is_open].sum())
    if denominator <= 0:
        raise ValueError("The kept-person denominator is not positive")
    weights = day_weight * ~data.is_open
    users = weights @ data.used
    minutes = weights @ data.minutes
    return (
        users / denominator,
        np.divide(
            minutes, users, out=np.full(len(data.modes), np.nan), where=users > 0
        ),
        denominator,
    )


def _person_mode_distribution(
    a: PersonModeData,
    b: PersonModeData,
    denominator_b: float,
) -> tuple[modes.Observations, modes.Observations]:
    """Map weighted within-mode 2019 user ranks to 2008 minutes, section 9.9."""
    kept_a = ~a.is_open
    kept_b = ~b.is_open
    predicted = np.zeros(len(b.day_weight))
    for mode in range(len(a.modes)):
        source = kept_a & a.used[:, mode] & (a.day_weight > 0)
        target = kept_b & b.used[:, mode] & (b.day_weight > 0)
        if not target.any():
            continue
        if not source.any():
            raise ValueError(f"No 2008 user-day support for mode {a.modes[mode]}")
        source_values = a.minutes[source, mode]
        source_weights = a.day_weight[source]
        source_order = np.argsort(source_values, kind="stable")
        source_cdf = np.cumsum(source_weights[source_order]) / source_weights.sum()
        target_indices = np.flatnonzero(target)
        order = np.argsort(b.minutes[target, mode], kind="stable")
        ordered_indices = target_indices[order]
        target_weights = b.day_weight[ordered_indices]
        ranks = (np.cumsum(target_weights) - target_weights / 2) / target_weights.sum()
        indices = np.searchsorted(source_cdf, ranks, side="left")
        predicted[ordered_indices] += source_values[source_order[indices]]
    travelled = kept_b & np.any(b.used, axis=1)
    remainder = denominator_b - b.day_weight[travelled].sum()
    if remainder < 0:
        raise ValueError("2019 travel-day weights exceed the kept-person denominator")
    weights = np.r_[b.day_weight[travelled], remainder]
    household = np.concatenate((b.day_household[travelled], np.array([""])))
    return (
        modes.Observations(np.r_[predicted[travelled], 0.0], weights, household),
        modes.Observations(
            np.r_[b.minutes[travelled].sum(axis=1), 0.0], weights, household
        ),
    )


def person_mode_statistics(
    a: PersonModeData,
    b: PersonModeData,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    compare: bool,
    minimum_n: int,
) -> dict:
    """Person-day mode use, minutes, decomposition and distributions, section 9.9."""
    if a.modes != b.modes or minimum_n <= 0:
        raise ValueError("Mode labels must match and threshold must be positive")
    if len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("Household draw counts must match")
    for data in (a, b):
        n = len(data.day_weight)
        if (
            data.minutes.shape != (n, len(data.modes))
            or data.used.shape != data.minutes.shape
            or len(data.day_household) != n
            or len(data.is_open) != n
            or len(data.roster_household) != len(data.roster_weight)
            or not np.all(np.isfinite(data.minutes))
            or not np.all(np.isfinite(data.day_weight))
            or not np.all(np.isfinite(data.roster_weight))
            or np.any(data.minutes < 0)
            or np.any(data.day_weight < 0)
            or np.any(data.roster_weight < 0)
            or np.any((data.minutes > 0) & ~data.used)
        ):
            raise ValueError("Invalid per-person mode data")
    ua, ta, _ = _person_mode_values(a, a.roster_weight, a.day_weight)
    ub, tb, denom_b = _person_mode_values(b, b.roster_weight, b.day_weight)
    rows = []
    for index, name in enumerate(a.modes):
        count_a = int(np.sum(a.used[:, index] & ~a.is_open))
        count_b = int(np.sum(b.used[:, index] & ~b.is_open))
        rows.append(
            {
                "mode": name,
                "n_2008": count_a,
                "n_2019": count_b,
                "use_2008": ua[index] if count_a >= minimum_n else np.nan,
                "use_2019": ub[index] if count_b >= minimum_n else np.nan,
                "user_minutes_2008": ta[index] if count_a >= minimum_n else np.nan,
                "user_minutes_2019": tb[index] if count_b >= minimum_n else np.nan,
            }
        )
    result = {
        "rows": rows,
        "observed_2008": float(np.nansum(ua * ta)),
        "observed_2019": float(np.nansum(ub * tb)),
        "predicted_2019": np.nan,
        "use_effect": np.nan,
        "use_effect_low": np.nan,
        "use_effect_high": np.nan,
        "time_effect": np.nan,
        "time_effect_low": np.nan,
        "time_effect_high": np.nan,
        "ks_d": np.nan,
        "predicted_deciles": np.full(9, np.nan),
        "observed_deciles": np.full(9, np.nan),
    }
    if not compare:
        return result
    if not np.all(np.isfinite(ta)) or not np.all(np.isfinite(tb)):
        LOGGER.warning("Per-mode comparison unavailable: a mode has no user days")
        return result
    result["predicted_2019"] = float(np.dot(ub, ta))
    result["use_effect"] = float(np.dot(ub - ua, ta))
    result["time_effect"] = float(np.dot(ub, tb - ta))
    predicted, observed = _person_mode_distribution(a, b, denom_b)
    result["ks_d"] = modes.weighted_ks(predicted, observed)
    result["predicted_deciles"] = modes.weighted_deciles(
        predicted, np.arange(1, 10) / 10
    )
    result["observed_deciles"] = modes.weighted_deciles(observed, np.arange(1, 10) / 10)
    use_effect = np.full(len(draws_a.multipliers), np.nan)
    time_effect = np.full(len(draws_a.multipliers), np.nan)
    indices = [
        (
            income_module._household_indices(data.roster_household, draws.households),
            income_module._household_indices(data.day_household, draws.households),
        )
        for data, draws in ((a, draws_a), (b, draws_b))
    ]
    for rep in range(len(use_effect)):
        values = []
        for data, draws, (roster_idx, day_idx) in zip(
            (a, b), (draws_a, draws_b), indices, strict=True
        ):
            rw = data.roster_weight * draws.multipliers[rep, roster_idx]
            dw = data.day_weight * draws.multipliers[rep, day_idx]
            if rw.sum() - dw[data.is_open].sum() <= 0:
                break
            values.append(_person_mode_values(data, rw, dw))
        if len(values) != 2:
            continue
        rep_ua, rep_ta, _ = values[0]
        rep_ub, rep_tb, _ = values[1]
        if np.all(np.isfinite(rep_ta)) and np.all(np.isfinite(rep_tb)):
            use_effect[rep] = np.dot(rep_ub - rep_ua, rep_ta)
            time_effect[rep] = np.dot(rep_ub, rep_tb - rep_ta)
    result["use_effect_low"], result["use_effect_high"] = _percentile_interval(
        use_effect, confidence=95
    )
    result["time_effect_low"], result["time_effect_high"] = _percentile_interval(
        time_effect, confidence=95
    )
    return result


def read_grouping_days(
    cache: modes_cache.SurveyCache,
    selected: scope_module.Scope,
    *,
    income: dict[str, str],
    density: dict[str, str],
    vehicles: dict[str, str],
    household_type: dict[str, str] | None = None,
) -> GroupingDays:
    """Read cached scoped weekdays with trips; minutes are per day, section 9.9."""
    with duckdb.connect() as con:
        rows = con.execute(
            """WITH purpose AS (
                SELECT day_id,
                    bool_or(motive = 1.4 OR (motive >= 9 AND motive < 10)) AS work,
                    count(*) FILTER (WHERE motive IS NULL) AS missing
                FROM read_parquet(?) GROUP BY day_id
            )
            SELECT trim(CAST(d.ident_ind AS VARCHAR)) AS person,
                trim(CAST(d.ident_men AS VARCHAR)) AS household,
                d.pond_jour AS weight, d.total_time_min AS minutes,
                coalesce(CAST(d.age_band AS VARCHAR), 'unknown') AS age_band,
                coalesce(d.population_category, 'unknown') AS population,
                d.income_quintile AS income,
                coalesce(d.day_mode_group, 'unknown') AS day_mode_group,
                p.day_id IS NULL AS missing_trips,
                CASE WHEN p.work THEN 'work_study'
                     WHEN p.missing > 0 THEN 'unknown'
                     ELSE 'other' END AS day_purpose
            FROM read_parquet(?) d LEFT JOIN purpose p ON p.day_id = d.day_id
            ORDER BY d.day_id""",
            [str(cache.trips(selected)), str(cache.days(selected))],
        ).fetchnumpy()
    rows = {key: vr._plain_array(value) for key, value in rows.items()}
    if np.any(rows["missing_trips"]):
        raise ValueError(
            f"{np.sum(rows['missing_trips'])} days have missing scoped trips"
        )
    person = vr._text_values(rows["person"])
    household = vr._text_values(rows["household"])
    quintile = income_module._mapped_values(person, income, "Income")
    if np.any(quintile != vr._text_values(rows["income"])):
        raise ValueError("Reconstructed income differs from scoped cache")
    attributes = {
        "population": vr._text_values(rows["population"]),
        "age_band": vr._text_values(rows["age_band"]),
        "density": income_module._mapped_values(person, density, "Residence density"),
        "income": quintile,
        "vehicles": income_module._mapped_values(household, vehicles, "Vehicles"),
        "day_purpose": vr._text_values(rows["day_purpose"]),
        "day_mode_group": vr._text_values(rows["day_mode_group"]),
    }
    if household_type is not None:
        attributes["household_type"] = income_module._mapped_values(
            household, household_type, "Household type"
        )
    return GroupingDays(
        person,
        household,
        np.asarray(rows["weight"], dtype=float),
        np.asarray(rows["minutes"], dtype=float),
        attributes,
    )


def grouping_catalog(*, household_type_available: bool) -> dict[str, tuple[str, ...]]:
    """Requested travel-day partitions, section 9.9."""
    catalog = {
        "none": (),
        "category": ("population",),
        "age_band": ("age_band",),
        "density": ("density",),
        "income": ("income",),
        "vehicles": ("vehicles",),
        "day_purpose": ("day_purpose",),
        "day_mode_group": ("day_mode_group",),
        "day_mode_group_x_density": ("day_mode_group", "density"),
        "day_mode_group_x_category": ("day_mode_group", "population"),
        "day_mode_group_x_income": ("day_mode_group", "income"),
        "day_mode_group_x_vehicles": ("day_mode_group", "vehicles"),
        "category_x_density_x_income": ("population", "density", "income"),
    }
    if household_type_available:
        catalog["household_type"] = ("household_type",)
    return catalog


def prepare_grouping(
    a: GroupingDays,
    b: GroupingDays,
    dimensions: tuple[str, ...],
    *,
    config: MergeConfig,
    minimum_n: int,
) -> PreparedGrouping:
    """Build a partition with full-sample ordered merges, section 9.9."""
    samples = []
    excluded = []
    matrices = []
    for sample in (a, b):
        if any(name not in sample.attributes for name in dimensions):
            raise ValueError(f"Missing grouping attributes for {dimensions}")
        if any(
            len(sample.attributes[name]) != len(sample.person) for name in dimensions
        ):
            raise ValueError("Grouping attributes must match the travel-day rows")
        keep = np.ones(len(sample.person), dtype=bool)
        if "population" in dimensions:
            keep &= sample.attributes["population"] != "unknown"
        total = sample.weights.sum()
        if total <= 0 or not keep.any():
            raise ValueError("Grouping has no positive retained survey support")
        excluded.append(float(sample.weights[~keep].sum() / total))
        filtered = GroupingDays(
            sample.person[keep],
            sample.household[keep],
            sample.weights[keep],
            sample.minutes[keep],
            {name: values[keep] for name, values in sample.attributes.items()},
        )
        samples.append(filtered)
        matrix = (
            np.column_stack(
                [filtered.attributes[name].astype(str) for name in dimensions]
            )
            if dimensions
            else np.full((len(filtered.person), 1), "all")
        )
        if np.any(matrix == "") or np.any(np.char.find(matrix, "|") >= 0):
            raise ValueError("Grouping labels must be nonempty and cannot contain '|'")
        matrices.append(matrix)
    mapping = merge_cells(
        matrices[0],
        samples[0].person,
        matrices[1],
        samples[1].person,
        dimensions=dimensions if dimensions else ("all",),
        config=config,
        minimum_n=minimum_n,
    )
    labels = []
    parents = []
    for matrix in matrices:
        unique, inverse = np.unique(matrix, axis=0, return_inverse=True)
        targets = [mapping[tuple(row)] for row in unique]
        labels.append(np.array(["|".join(target) for target in targets])[inverse])
        parents.append(
            np.array(
                [target[0] if len(dimensions) > 1 else "all" for target in targets]
            )[inverse]
        )
    merges = sorted(
        ("|".join(original), "|".join(target))
        for original, target in mapping.items()
        if original != target
    )
    return PreparedGrouping(
        samples[0],
        samples[1],
        labels[0],
        labels[1],
        parents[0],
        parents[1],
        excluded[0],
        excluded[1],
        merges,
    )


def _percentile_interval(values: np.ndarray, *, confidence: int) -> tuple[float, float]:
    valid = values[np.isfinite(values)]
    if not len(values) or len(valid) < np.ceil(0.95 * len(values)):
        LOGGER.warning(
            "Only %d of %d bootstrap draws are valid", len(valid), len(values)
        )
        return float("nan"), float("nan")
    tail = (100 - confidence) / 2
    low, high = np.percentile(valid, [tail, 100 - tail])
    return float(low), float(high)


def grouping_statistics(
    a: GroupingDays,
    b: GroupingDays,
    cells_a: np.ndarray,
    cells_b: np.ndarray,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    minimum_n: int,
    margins: tuple[float, float],
    compare: bool,
) -> tuple[list[dict], dict]:
    """Cell levels, eta-squared and pooled temporal stability, section 9.9."""
    if minimum_n <= 0 or len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("Invalid threshold or mismatched household draws")
    labels = np.union1d(cells_a, cells_b)
    if not len(labels):
        raise ValueError("Grouping has no observations")
    estimates = []
    for sample, cells, draws in ((a, cells_a, draws_a), (b, cells_b, draws_b)):
        if (
            cells.ndim != 1
            or len(cells) != len(sample.person)
            or len(cells) != len(sample.household)
            or len(cells) != len(sample.weights)
            or len(cells) != len(sample.minutes)
            or not len(cells)
            or not np.all(np.isfinite(sample.minutes))
            or not np.all(np.isfinite(sample.weights))
            or np.any(sample.weights <= 0)
        ):
            raise ValueError("Invalid grouped travel-day observations")
        codes = np.searchsorted(labels, cells)
        counts = np.array(
            [
                len(np.unique(sample.person[codes == index]))
                for index in range(len(labels))
            ]
        )
        observation = modes.Observations(
            sample.minutes, sample.weights, sample.household
        )

        def weighted_means(weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            totals = np.bincount(codes, weights=weights, minlength=len(labels))
            sums = np.bincount(
                codes, weights=weights * sample.minutes, minlength=len(labels)
            )
            means = np.divide(
                sums, totals, out=np.full(len(labels), np.nan), where=totals > 0
            )
            return means, totals

        means, totals = weighted_means(sample.weights)
        rep_means = np.full((len(draws.multipliers), len(labels)), np.nan)
        eta_draws = np.full(len(draws.multipliers), np.nan)
        for rep in range(len(draws.multipliers)):
            weights = draws.weights(observation, rep)
            rep_means[rep], _ = weighted_means(weights)
            if weights.sum() > 0:
                eta_draws[rep] = weighted_eta_squared(sample.minutes, weights, cells)
        eta = weighted_eta_squared(sample.minutes, sample.weights, cells)
        eta_low, eta_high = _percentile_interval(eta_draws, confidence=95)
        estimates.append(
            (counts, means, totals / totals.sum(), rep_means, eta, eta_low, eta_high)
        )

    counts_a, means_a, shares_a, reps_a, eta_a, eta_a_low, eta_a_high = estimates[0]
    counts_b, means_b, shares_b, reps_b, eta_b, eta_b_low, eta_b_high = estimates[1]
    rows = []
    pooled = (shares_a + shares_b) / 2
    logs = np.full(len(labels), np.nan)
    equivalent_10 = np.zeros(len(labels), dtype=bool)
    equivalent_15 = np.zeros(len(labels), dtype=bool)
    for index, label in enumerate(labels):
        valid_level_a = counts_a[index] >= minimum_n
        valid_level_b = counts_b[index] >= minimum_n
        ratio = low = high = np.nan
        verdict_10 = verdict_15 = ""
        if compare and means_a[index] > 0 and means_b[index] > 0:
            ratio = means_b[index] / means_a[index]
            logs[index] = abs(np.log(ratio))
            replicates = np.divide(
                reps_b[:, index],
                reps_a[:, index],
                out=np.full(len(reps_a), np.nan),
                where=reps_a[:, index] > 0,
            )
            low, high = _percentile_interval(replicates, confidence=90)
            if np.isfinite(low) and np.isfinite(high):
                verdict_15 = vr._equivalence_verdict((low, high), margins[0])
                verdict_10 = vr._equivalence_verdict((low, high), margins[1])
                equivalent_10[index] = verdict_10 == "equivalent"
                equivalent_15[index] = verdict_15 == "equivalent"
        visible = valid_level_a and valid_level_b
        rows.append(
            {
                "cell": str(label),
                "n_2008": int(counts_a[index]),
                "n_2019": int(counts_b[index]),
                "mean_2008": means_a[index] if valid_level_a else np.nan,
                "mean_2019": means_b[index] if valid_level_b else np.nan,
                "share_2008": shares_a[index] if valid_level_a else np.nan,
                "share_2019": shares_b[index] if valid_level_b else np.nan,
                "ratio": ratio if visible else np.nan,
                "ratio_ci_low": low if visible else np.nan,
                "ratio_ci_high": high if visible else np.nan,
                "verdict_10": verdict_10 if visible else "",
                "verdict_15": verdict_15 if visible else "",
            }
        )
    complete = compare and np.all(np.isfinite(logs))
    if compare and not complete:
        LOGGER.warning(
            "Temporal log-ratio statistics have cells without positive means"
        )
    summary = {
        "eta2_2008": eta_a,
        "eta2_2008_low": eta_a_low,
        "eta2_2008_high": eta_a_high,
        "eta2_2019": eta_b,
        "eta2_2019_low": eta_b_low,
        "eta2_2019_high": eta_b_high,
        "mean_abs_log_ratio": float(np.dot(pooled, logs)) if complete else np.nan,
        "max_abs_log_ratio": float(np.max(logs)) if complete else np.nan,
        "equivalent_10_share": float(np.dot(pooled, equivalent_10))
        if compare
        else np.nan,
        "equivalent_15_share": float(np.dot(pooled, equivalent_15))
        if compare
        else np.nan,
        "n_cells": len(labels),
    }
    return rows, summary


def evaluate_groupings(
    a: GroupingDays,
    b: GroupingDays,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope_module.Scope,
    config: MergeConfig,
    minimum_n: int,
    margins: tuple[float, float],
    timings: dict[str, float],
) -> dict[str, GroupingResult]:
    """Evaluate every available grouping on one scope, section 9.9."""
    has_type = "household_type" in a.attributes and "household_type" in b.attributes
    if ("household_type" in a.attributes) != ("household_type" in b.attributes):
        LOGGER.warning("Household type is unavailable for one survey")
    results = {}
    for name, dimensions in grouping_catalog(household_type_available=has_type).items():
        with modes._timed(timings, f"{selected.id} {name} cells"):
            partition = prepare_grouping(
                a, b, dimensions, config=config, minimum_n=minimum_n
            )
            cells, summary = grouping_statistics(
                partition.a,
                partition.b,
                partition.cells_a,
                partition.cells_b,
                draws_a,
                draws_b,
                minimum_n=minimum_n,
                margins=margins,
                compare=selected.distance != "daytable",
            )
        status = DAYTABLE_STATUS if selected.distance == "daytable" else ""
        summary.update(
            scope=selected.id,
            grouping=name,
            status=status,
            excluded_share_2008=partition.excluded_share_2008,
            excluded_share_2019=partition.excluded_share_2019,
        )
        for row in cells:
            row.update(scope=selected.id, grouping=name, status=status)
        results[name] = GroupingResult(partition, cells, summary)
    return results


def summary_rows(
    summaries: list[dict], counterfactuals: dict[tuple[str, str], dict]
) -> list[dict]:
    """Sort scope-by-grouping summaries by ratio distance from one, section 9.9."""
    scope_order = {item.id: index for index, item in enumerate(scope_module.ALL_SCOPES)}
    rows = []
    seen = set()
    for summary in summaries:
        scope_id = summary["scope"]
        grouping = summary["grouping"]
        key = (scope_id, grouping)
        if scope_id not in scope_order or key in seen or key not in counterfactuals:
            raise ValueError(f"Invalid, duplicate or unmatched grouping summary {key}")
        seen.add(key)
        counter = counterfactuals[key]
        compare = scope_module.Scope.parse(scope_id).distance != "daytable"
        row = {
            "scope": scope_id,
            "grouping": grouping,
            "eta2_2008": summary["eta2_2008"],
            "eta2_2019": summary["eta2_2019"],
            "mean_abs_log_ratio": summary["mean_abs_log_ratio"] if compare else np.nan,
            "equivalent_10_share": summary["equivalent_10_share"]
            if compare
            else np.nan,
            "observed_over_predicted": counter["observed_over_predicted"]
            if compare
            else np.nan,
            "ratio_low": counter["ratio_low"] if compare else np.nan,
            "ratio_high": counter["ratio_high"] if compare else np.nan,
            "ks_d": counter["ks_d"] if compare else np.nan,
            "n_cells": summary["n_cells"],
            "status": "" if compare else DAYTABLE_STATUS,
        }
        rows.append(row)
    if seen != set(counterfactuals):
        raise ValueError("Counterfactuals include unmatched grouping summaries")

    def sort_key(row: dict) -> tuple[int, float, str]:
        ratio = row["observed_over_predicted"]
        distance = abs(ratio - 1) if np.isfinite(ratio) else float("inf")
        return scope_order[row["scope"]], distance, row["grouping"]

    return sorted(rows, key=sort_key)


def fixed_cell_distribution(a: CellSample, b: CellSample) -> FixedDistribution:
    """Build the 2019-share mixture of 2008 daily minutes, section 9.9."""
    for sample in (a, b):
        if not len(sample.values) or any(
            len(column) != len(sample.values)
            for column in (sample.weights, sample.cells, sample.parents)
        ):
            raise ValueError("Cell sample arrays must be nonempty and aligned")
        if (
            not np.all(np.isfinite(sample.values))
            or not np.all(np.isfinite(sample.weights))
            or np.any(sample.weights < 0)
            or sample.weights.sum() <= 0
        ):
            raise ValueError("Cell samples require finite values and positive weight")
        for cell in np.unique(sample.cells):
            if len(np.unique(sample.parents[sample.cells == cell])) != 1:
                raise ValueError(f"Cell {cell!r} has more than one parent")
    weights = np.zeros(len(a.values), dtype=float)
    fallback = 0.0
    total_b = b.weights.sum()
    for cell in np.unique(b.cells):
        target = b.cells == cell
        share = float(b.weights[target].sum() / total_b)
        if share == 0:
            continue
        source = a.cells == cell
        parent = b.parents[target][0]
        if source.any() and np.any(a.parents[source] != parent):
            raise ValueError(f"Cell {cell!r} has inconsistent parents across years")
        if not source.any():
            source = a.parents == parent
            fallback += share
        elif a.weights[source].sum() <= 0:
            raise ValueError(f"No 2008 bootstrap support for cell {cell!r}")
        source_weight = a.weights[source].sum()
        if source_weight <= 0:
            raise ValueError(f"No 2008 support for cell {cell!r} or parent {parent!r}")
        weights[source] += share * a.weights[source] / source_weight
    return FixedDistribution(a.values, weights, fallback)


def counterfactual_statistics(
    partition: PreparedGrouping,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    compare: bool,
) -> dict:
    """Fixed-cell mean and distribution of daily minutes, section 9.9."""
    a, b = partition.a, partition.b
    observation_a = modes.Observations(a.minutes, a.weights, a.household)
    observation_b = modes.Observations(b.minutes, b.weights, b.household)
    observed = float(np.average(b.minutes, weights=b.weights))
    result = {
        "observed_2019": observed,
        "predicted_2019": np.nan,
        "observed_over_predicted": np.nan,
        "ratio_low": np.nan,
        "ratio_high": np.nan,
        "mix_term": np.nan,
        "fallback_share": np.nan,
        "ks_d": np.nan,
        "ks_low": np.nan,
        "ks_high": np.nan,
        "predicted_deciles": np.full(9, np.nan),
        "observed_deciles": np.full(9, np.nan),
    }
    if not compare:
        return result
    if len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("Household draw counts must match")
    source = CellSample(a.minutes, a.weights, partition.cells_a, partition.parents_a)
    target = CellSample(b.minutes, b.weights, partition.cells_b, partition.parents_b)
    prediction = fixed_cell_distribution(source, target)
    predicted = float(np.average(prediction.values, weights=prediction.weights))
    if predicted <= 0:
        raise ValueError("The fixed-cell predicted mean must be positive")
    predicted_sample = modes.Observations(
        prediction.values, prediction.weights, a.household
    )
    probabilities = np.arange(1, 10) / 10
    result.update(
        predicted_2019=predicted,
        observed_over_predicted=observed / predicted,
        mix_term=predicted - float(np.average(a.minutes, weights=a.weights)),
        fallback_share=prediction.fallback_share,
        ks_d=modes.weighted_ks(predicted_sample, observation_b),
        predicted_deciles=modes.weighted_deciles(predicted_sample, probabilities),
        observed_deciles=modes.weighted_deciles(observation_b, probabilities),
    )
    support_masks = []
    for cell in np.unique(target.cells):
        target_mask = target.cells == cell
        source_mask = source.cells == cell
        if not source_mask.any():
            source_mask = source.parents == target.parents[target_mask][0]
        support_masks.append((source_mask, target_mask))
    ratios = np.full(len(draws_a.multipliers), np.nan)
    distances = np.full(len(draws_a.multipliers), np.nan)
    for rep in range(len(ratios)):
        weights_a = draws_a.weights(observation_a, rep)
        weights_b = draws_b.weights(observation_b, rep)
        if weights_a.sum() <= 0 or weights_b.sum() <= 0:
            continue
        if any(
            weights_b[t].sum() > 0 and weights_a[s].sum() <= 0 for s, t in support_masks
        ):
            continue
        draw_prediction = fixed_cell_distribution(
            CellSample(a.minutes, weights_a, partition.cells_a, partition.parents_a),
            CellSample(b.minutes, weights_b, partition.cells_b, partition.parents_b),
        )
        draw_mean = float(
            np.average(draw_prediction.values, weights=draw_prediction.weights)
        )
        if draw_mean <= 0:
            continue
        ratios[rep] = np.average(b.minutes, weights=weights_b) / draw_mean
        distances[rep] = modes.weighted_ks(
            modes.Observations(
                draw_prediction.values, draw_prediction.weights, a.household
            ),
            modes.Observations(b.minutes, weights_b, b.household),
        )
    result["ratio_low"], result["ratio_high"] = _percentile_interval(
        ratios, confidence=90
    )
    result["ks_low"], result["ks_high"] = _percentile_interval(distances, confidence=95)
    return result


def merge_cells(
    cells_a: np.ndarray,
    people_a: np.ndarray,
    cells_b: np.ndarray,
    people_b: np.ndarray,
    *,
    dimensions: tuple[str, ...],
    config: MergeConfig,
    minimum_n: int,
) -> dict[tuple[str, ...], tuple[str, ...]]:
    """Fix ordered-secondary merges on full-sample respondent counts, section 9.9."""
    for cells, people in ((cells_a, people_a), (cells_b, people_b)):
        if (
            cells.ndim != 2
            or cells.shape[1] != len(dimensions)
            or len(cells) != len(people)
        ):
            raise ValueError("Cells and respondent identifiers must match dimensions")
    if minimum_n <= 0 or not len(dimensions) or not len(cells_a) or not len(cells_b):
        raise ValueError(
            "A positive threshold and nonempty survey samples are required"
        )
    original = [
        tuple(row)
        for row in np.unique(np.concatenate((cells_a, cells_b)).astype(str), axis=0)
    ]
    members = {cell: [set(), set()] for cell in original}
    for year, (cells, people) in enumerate(((cells_a, people_a), (cells_b, people_b))):
        for cell in original:
            mask = np.all(cells.astype(str) == cell, axis=1)
            members[cell][year].update(np.unique(people[mask]).astype(str))
    clusters = {cell: frozenset([cell]) for cell in original}

    def counts(cluster: frozenset[tuple[str, ...]]) -> int:
        return min(
            len(set().union(*(members[cell][year] for cell in cluster)))
            for year in (0, 1)
        )

    while True:
        groups = set(clusters.values())
        choice = None
        for cluster in sorted(groups, key=lambda group: (counts(group), sorted(group))):
            if counts(cluster) >= minimum_n:
                break
            for axis, dimension in enumerate(dimensions):
                if axis == 0 or dimension not in config.dimensions:
                    continue
                rule = config.dimensions[dimension]
                candidates = []
                for other in groups - {cluster}:
                    projections = (
                        {
                            tuple(row[i] for i in range(len(dimensions)) if i != axis)
                            for row in group
                        }
                        for group in (cluster, other)
                    )
                    left_projection, right_projection = projections
                    if left_projection != right_projection:
                        continue
                    left = {row[axis] for row in cluster}
                    right = {row[axis] for row in other}
                    pairs = [
                        (a, b)
                        for a, b in product(left, right)
                        if a in rule.levels
                        and b in rule.levels
                        and abs(rule.levels.index(a) - rule.levels.index(b)) == 1
                    ]
                    if not pairs:
                        continue
                    preferred = min(
                        (
                            i
                            for i, pair in enumerate(rule.preferred)
                            if pair in pairs or pair[::-1] in pairs
                        ),
                        default=len(rule.preferred),
                    )
                    candidates.append((preferred, -counts(other), sorted(other), other))
                if candidates:
                    other = min(candidates, key=lambda item: item[:3])[3]
                    choice = cluster | other
                    break
            if choice is not None:
                break
        if choice is None:
            break
        for cell in choice:
            clusters[cell] = choice
    result = {}
    for cell, cluster in clusters.items():
        result[cell] = tuple(
            "+".join(sorted({row[i] for row in cluster}))
            for i in range(len(dimensions))
        )
    return result


def weighted_eta_squared(
    values: np.ndarray, weights: np.ndarray, cells: np.ndarray
) -> float:
    """Weighted between-cell variance share for daily minutes, section 9.9."""
    if len(values) != len(weights) or len(values) != len(cells) or not len(values):
        raise ValueError("Values, weights and cell labels must be nonempty and aligned")
    if (
        not np.all(np.isfinite(values))
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
    ):
        raise ValueError("Values and nonnegative weights must be finite")
    if weights.sum() <= 0:
        raise ValueError("Total weight must be positive")
    _, codes = np.unique(cells, return_inverse=True)
    cell_weight = np.bincount(codes, weights=weights)
    cell_sum = np.bincount(codes, weights=weights * values)
    mean = np.sum(weights * values) / np.sum(weights)
    total = np.sum(weights * (values - mean) ** 2)
    if total == 0:
        LOGGER.warning("Weighted eta-squared is undefined for zero total variance")
        return float("nan")
    means = np.divide(
        cell_sum, cell_weight, out=np.zeros_like(cell_sum), where=cell_weight > 0
    )
    return float(np.sum(cell_weight * (means - mean) ** 2) / total)


if __name__ == "__main__":
    raise NotImplementedError("The grouping report and CLI have not been implemented")
