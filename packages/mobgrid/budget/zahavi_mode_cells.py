"""Foundations for mode-user-day analyses, section 9.9.

The report and command-line interface are not yet implemented.
"""

from dataclasses import dataclass, fields
from itertools import combinations

import duckdb
import numpy as np

from mobgrid.budget import modes_cache, scope, variation
from mobgrid.budget import variation_report as vr
from mobgrid.budget import zahavi_groupings as groupings
from mobgrid.budget import zahavi_income as income_module
from mobgrid.budget import zahavi_modes as modes


@dataclass(frozen=True)
class ModeDays:
    """Mode-user-day totals: minutes, km and kJ above rest, section 9.9."""

    day: np.ndarray
    mode: np.ndarray
    household: np.ndarray
    weight: np.ndarray
    minutes: np.ndarray
    distance_km: np.ndarray
    trips: np.ndarray
    distance_trips: np.ndarray
    distance_minutes: np.ndarray
    energy_kj: np.ndarray


def _text(array: np.ndarray, name: str) -> np.ndarray:
    if np.any(np.equal(array, None)):  # noqa: E711
        raise ValueError(f"{name} contains missing identifiers")
    values = np.char.strip(array.astype(str))
    if np.any(values == ""):
        raise ValueError(f"{name} contains empty identifiers")
    return values


def aggregate_mode_days(
    *,
    day: np.ndarray,
    mode: np.ndarray,
    household: np.ndarray,
    weight: np.ndarray,
    minutes: np.ndarray,
    distance_km: np.ndarray,
    energy_kj: np.ndarray,
) -> ModeDays:
    """Aggregate trips to mode-user days, preserving missing km and energy.

    Durations are minutes, distances km, and modeled energies kJ above rest.
    Distance-known trip counts and minutes allow B2's selection term to
    remain separate. A missing trip energy makes its mode-day energy unknown.
    """
    columns = (day, mode, household, weight, minutes, distance_km, energy_kj)
    if (
        any(column.ndim != 1 for column in columns)
        or len({len(c) for c in columns}) != 1
    ):
        raise ValueError("Trip columns must be aligned one-dimensional arrays")
    if not len(day):
        raise ValueError("Trip columns must not be empty")
    day, mode, household = (
        _text(day, "day"),
        _text(mode, "mode"),
        _text(household, "household"),
    )
    weight, minutes, distance_km, energy_kj = (
        np.asarray(column, dtype=float)
        for column in (weight, minutes, distance_km, energy_kj)
    )
    if (
        np.any(~np.isfinite(weight))
        or np.any(weight <= 0)
        or np.any(~np.isfinite(minutes))
        or np.any(minutes < 0)
        or np.any(np.isinf(distance_km))
        or np.any(distance_km < 0)
        or np.any(np.isinf(energy_kj))
        or np.any(energy_kj < 0)
    ):
        raise ValueError("Invalid trip weights, minutes, distance or energy")
    _, day_first, day_inverse = np.unique(day, return_index=True, return_inverse=True)
    if np.any(weight != weight[day_first][day_inverse]):
        raise ValueError("A day has inconsistent trip weights")
    if np.any(household != household[day_first][day_inverse]):
        raise ValueError("A day has inconsistent household identifiers")
    keys, first, inverse = np.unique(
        np.column_stack((day, mode)), axis=0, return_index=True, return_inverse=True
    )
    count = len(keys)
    known_distance = np.isfinite(distance_km)
    known_energy = np.isfinite(energy_kj)
    energy = np.bincount(
        inverse, weights=np.where(known_energy, energy_kj, 0), minlength=count
    )
    energy[np.bincount(inverse, weights=~known_energy, minlength=count) > 0] = np.nan
    return ModeDays(
        day=keys[:, 0],
        mode=keys[:, 1],
        household=household[first],
        weight=weight[first],
        minutes=np.bincount(inverse, weights=minutes, minlength=count),
        distance_km=np.bincount(
            inverse, weights=np.where(known_distance, distance_km, 0), minlength=count
        ),
        trips=np.bincount(inverse, minlength=count),
        distance_trips=np.bincount(inverse, weights=known_distance, minlength=count),
        distance_minutes=np.bincount(
            inverse, weights=np.where(known_distance, minutes, 0), minlength=count
        ),
        energy_kj=energy,
    )


def reweight_to_target(
    target_cells: np.ndarray,
    target_weight: np.ndarray,
    source_cells: np.ndarray,
    source_weight: np.ndarray,
) -> np.ndarray:
    """Reweight source mode users to a fixed target joint mix, section 9.9.

    The result keeps the source's total weight. Cells are not merged; if a
    positive target cell has no source support, the estimate is unavailable.
    """
    for cell, weight in ((target_cells, target_weight), (source_cells, source_weight)):
        if (
            cell.ndim != 2
            or weight.ndim != 1
            or len(cell) != len(weight)
            or len(cell) == 0
            or cell.shape[1] == 0
            or not np.isfinite(weight).all()
            or np.any(weight < 0)
            or weight.sum() <= 0
        ):
            raise ValueError("Invalid joint cells or weights")
    if target_cells.shape[1] != source_cells.shape[1]:
        raise ValueError("Joint cells must have the same dimensions")
    target_cells = _text(target_cells, "target cell")
    source_cells = _text(source_cells, "source cell")
    _, inverse = np.unique(
        np.concatenate((target_cells, source_cells)), axis=0, return_inverse=True
    )
    target_index = inverse[: len(target_cells)]
    source_index = inverse[len(target_cells) :]
    size = int(inverse.max()) + 1
    target = np.bincount(target_index, weights=target_weight, minlength=size)
    source = np.bincount(source_index, weights=source_weight, minlength=size)
    if np.any((target > 0) & (source == 0)):
        raise ValueError("A target joint cell lacks source support")
    factors = np.divide(
        target / target.sum(),
        source / source.sum(),
        out=np.zeros(size),
        where=source > 0,
    )
    return source_weight * factors[source_index]


@dataclass(frozen=True)
class ModeCellSample:
    """One mode's user days and subgroup labels, section 9.9."""

    days: ModeDays
    labels: np.ndarray


@dataclass(frozen=True)
class ModeCellData:
    """Mode-user days and aligned subgroup attributes, section 9.9."""

    days: ModeDays
    attributes: dict[str, np.ndarray]


def read_mode_cell_data(
    cache: modes_cache.SurveyCache,
    selected: scope.Scope,
    *,
    income: dict[str, str],
    density: dict[str, str],
    vehicles: dict[str, str],
    household_type: dict[str, str],
) -> ModeCellData:
    """Read scoped cached trips and attach verified subgroup attributes."""
    with duckdb.connect() as con:
        trips = con.execute(
            """SELECT CAST(day_id AS VARCHAR) day_id, mode7,
                CAST(ident_men AS VARCHAR) household, pond_jour,
                duration_min, distance_km
            FROM read_parquet(?)""",
            [str(cache.trips(selected))],
        ).fetchnumpy()
        attributes = con.execute(
            """SELECT CAST(day_id AS VARCHAR) day_id,
                any_value(CAST(ident_ind AS VARCHAR)) person,
                any_value(CAST(ident_men AS VARCHAR)) household,
                coalesce(any_value(population_category), 'unknown') population,
                any_value(income_quintile) income,
                CASE WHEN bool_or(motive = 1.4 OR (motive >= 9 AND motive < 10))
                     THEN 'work_study'
                     WHEN count(*) FILTER (WHERE motive IS NULL) > 0 THEN 'unknown'
                     ELSE 'other' END day_purpose,
                count(DISTINCT coalesce(CAST(ident_ind AS VARCHAR), '')) persons,
                count(DISTINCT coalesce(CAST(ident_men AS VARCHAR), '')) households,
                count(DISTINCT coalesce(population_category, 'unknown')) populations,
                count(DISTINCT coalesce(income_quintile, '')) incomes
            FROM read_parquet(?) GROUP BY day_id ORDER BY CAST(day_id AS VARCHAR)""",
            [str(cache.trips(selected))],
        ).fetchnumpy()
    trips = {name: vr._plain_array(value) for name, value in trips.items()}
    attributes = {name: vr._plain_array(value) for name, value in attributes.items()}
    if any(
        np.any(attributes[column] != 1)
        for column in ("persons", "households", "populations", "incomes")
    ):
        raise ValueError("A day has inconsistent respondent attributes")
    days = aggregate_mode_days(
        day=trips["day_id"],
        mode=trips["mode7"],
        household=trips["household"],
        weight=trips["pond_jour"],
        minutes=trips["duration_min"],
        distance_km=trips["distance_km"],
        energy_kj=np.full(len(trips["day_id"]), np.nan),
    )
    day_ids = _text(attributes["day_id"], "day")
    indices = np.searchsorted(day_ids, days.day)
    if np.any(indices >= len(day_ids)) or np.any(day_ids[indices] != days.day):
        raise ValueError("Mode-user day missing from day attributes")
    person = _text(attributes["person"][indices], "person")
    household = _text(attributes["household"][indices], "household")
    if np.any(household != days.household):
        raise ValueError("Mode-user day household differs from day attributes")
    quintile = income_module._mapped_values(person, income, "Income")
    if np.any(quintile != _text(attributes["income"][indices], "income")):
        raise ValueError("Reconstructed income differs from scoped cache")
    return ModeCellData(
        days=days,
        attributes={
            "population": _text(attributes["population"][indices], "population"),
            "income": quintile,
            "density": income_module._mapped_values(
                person, density, "Residence density"
            ),
            "vehicles": income_module._mapped_values(household, vehicles, "Vehicles"),
            "household_type": income_module._mapped_values(
                household, household_type, "Household type"
            ),
            "day_purpose": _text(attributes["day_purpose"][indices], "day purpose"),
        },
    )


def _draw_weights(days: ModeDays, draws: modes.Draws) -> np.ndarray:
    """Return shared household draw weights after text normalization."""
    households = _text(np.asarray(draws.households), "draw household")
    if not np.array_equal(households, np.unique(households)):
        raise ValueError("Draw household identifiers must be unique and sorted text")
    indices = np.searchsorted(households, _text(days.household, "household"))
    if np.any(indices >= len(households)):
        raise ValueError("Mode-day household outside bootstrap universe")
    if np.any(households[indices] != _text(days.household, "household")):
        raise ValueError("Mode-day household outside bootstrap universe")
    if draws.multipliers.ndim != 2 or draws.multipliers.shape[1] != len(households):
        raise ValueError("Invalid household draw matrix")
    if np.any(~np.isfinite(draws.multipliers)) or np.any(draws.multipliers < 0):
        raise ValueError("Invalid household draw multipliers")
    return draws.multipliers[:, indices] * days.weight


def _mode_level(
    days: ModeDays, weights: np.ndarray, mask: np.ndarray
) -> tuple[float, float, float, float]:
    """Minutes/day, known km/day, km/h and distance-known time (section 9.9)."""
    weight = weights[mask]
    total = weight.sum()
    if total <= 0:
        return (np.nan, np.nan, np.nan, np.nan)
    minutes = float(np.dot(weight, days.minutes[mask]) / total)
    known_trips = float(np.dot(weight, days.distance_trips[mask]))
    km = (
        float(np.dot(weight, days.distance_km[mask]) / total)
        if known_trips > 0
        else np.nan
    )
    known_time = float(np.dot(weight, days.distance_minutes[mask]) / total)
    speed = 60 * km / known_time if known_time > 0 else np.nan
    return minutes, km, speed, known_time


def _gap_split(
    national: tuple[float, float, float, float],
    subgroup: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    """Split subgroup minus national minutes into distance, speed and selection."""
    time_a, distance_a, speed_a, known_a = national
    time_b, distance_b, speed_b, known_b = subgroup
    values = (
        time_a,
        time_b,
        distance_a,
        distance_b,
        speed_a,
        speed_b,
        known_a,
        known_b,
    )
    if not all(np.isfinite(value) and value > 0 for value in values):
        return (np.nan, np.nan, np.nan)
    log_change = np.log(time_b / time_a)
    scale = (time_b - time_a) / log_change if abs(log_change) > 1e-14 else time_a
    return (
        float(scale * np.log(distance_b / distance_a)),
        float(-scale * np.log(speed_b / speed_a)),
        float(scale * np.log((time_b / known_b) / (time_a / known_a))),
    )


def mode_cell_statistics(
    a: ModeCellSample,
    b: ModeCellSample,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    minimum_n: int,
    caution_n: int,
    margins: tuple[float, float],
) -> list[dict]:
    """Cell estimates versus the full mode distribution, section 9.9.

    Distances are known-distance km per user day; speed is the ratio of
    weighted known distance to weighted known-distance time, in km/h.
    The separate selection term prevents missing distance being called speed.
    """
    if minimum_n <= 0 or caution_n < minimum_n:
        raise ValueError("Invalid disclosure thresholds")
    if len(margins) != 2 or not all(0 < margin < 1 for margin in margins):
        raise ValueError("Equivalence margins must be between zero and one")
    if len(draws_a.multipliers) == 0 or len(draws_a.multipliers) != len(
        draws_b.multipliers
    ):
        raise ValueError("Both surveys need equal nonempty household draws")
    for sample in (a, b):
        if sample.labels.ndim != 1 or len(sample.labels) != len(sample.days.day):
            raise ValueError("Subgroup labels must match mode-user days")
    mode_names = np.union1d(a.days.mode, b.days.mode)
    if len(mode_names) != 1:
        raise ValueError("The samples must contain exactly one shared mode")
    labels_a = _text(a.labels, "subgroup")
    labels_b = _text(b.labels, "subgroup")
    weights_a = _draw_weights(a.days, draws_a)
    weights_b = _draw_weights(b.days, draws_b)
    rows = []
    for label in np.union1d(labels_a, labels_b):
        row: dict = {
            "scope": selected.id,
            "mode": str(mode_names[0]),
            "cell": str(label),
            "distance_source": "step11_speed_corrected",
            "comparison_status": (
                groupings.DAYTABLE_STATUS if selected.distance == "daytable" else ""
            ),
        }
        means = []
        replicate_means = []
        for year, sample, labels, rep_weights in (
            (2008, a, labels_a, weights_a),
            (2019, b, labels_b, weights_b),
        ):
            days = sample.days
            mask = labels == label
            count = int(mask.sum())
            visible = count >= minimum_n
            row[f"n_{year}"] = count
            row[f"caution_{year}"] = count < caution_n
            all_trips = float(np.dot(days.weight[mask], days.trips[mask]))
            known_trips = float(np.dot(days.weight[mask], days.distance_trips[mask]))
            share = known_trips / all_trips if all_trips > 0 else np.nan
            row[f"distance_trip_share_{year}"] = share if visible else np.nan
            row[f"distance_status_{year}"] = (
                "unavailable"
                if not visible or known_trips == 0
                else "incomplete"
                if known_trips < all_trips
                else "complete"
            )
            all_days = np.ones(len(days.day), dtype=bool)

            def calculate(weights: np.ndarray) -> np.ndarray:
                national = _mode_level(days, weights, all_days)
                level = _mode_level(days, weights, mask)
                subgroup = modes.Observations(
                    days.minutes[mask], weights[mask], days.household[mask]
                )
                full = modes.Observations(days.minutes, weights, days.household)
                ks = (
                    modes.weighted_ks(subgroup, full)
                    if weights[mask].sum() > 0
                    else np.nan
                )
                return np.array([*level[:3], ks, *_gap_split(national, level)])

            point = calculate(days.weight) if count else np.full(7, np.nan)
            replicas = (
                np.stack([calculate(weights) for weights in rep_weights])
                if count
                else np.full((len(rep_weights), 7), np.nan)
            )
            means.append(point[0])
            replicate_means.append(replicas[:, 0])
            for column, value, replicate in zip(
                (
                    "minutes",
                    "km",
                    "speed",
                    "ks",
                    "distance_gap",
                    "speed_gap",
                    "selection_gap",
                ),
                point,
                replicas.T,
                strict=True,
            ):
                row[f"{column}_{year}"] = float(value) if visible else np.nan
                low, high = (
                    groupings._percentile_interval(replicate, confidence=95)
                    if visible and np.isfinite(value)
                    else (np.nan, np.nan)
                )
                row[f"{column}_{year}_low"] = low
                row[f"{column}_{year}_high"] = high
        row.update(
            ratio=np.nan,
            ratio_low=np.nan,
            ratio_high=np.nan,
            verdict_15="",
            verdict_10="",
        )
        if (
            selected.distance != "daytable"
            and min(row["n_2008"], row["n_2019"]) >= minimum_n
            and means[0] > 0
            and means[1] > 0
        ):
            ratios = np.divide(
                replicate_means[1],
                replicate_means[0],
                out=np.full(len(replicate_means[0]), np.nan),
                where=replicate_means[0] > 0,
            )
            low, high = groupings._percentile_interval(ratios, confidence=90)
            row.update(ratio=means[1] / means[0], ratio_low=low, ratio_high=high)
            if np.isfinite(low) and np.isfinite(high):
                row["verdict_15"] = vr._equivalence_verdict((low, high), margins[0])
                row["verdict_10"] = vr._equivalence_verdict((low, high), margins[1])
        rows.append(row)
    return rows


def evaluate_mode_scope(
    a: ModeCellData,
    b: ModeCellData,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    merge_config: groupings.MergeConfig,
    minimum_n: int,
    caution_n: int,
    margins: tuple[float, float],
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """Evaluate every mode and requested subgroup in one scope, section 9.9."""
    recorded = {} if timings is None else timings
    with modes._timed(recorded, f"{selected.id} mode cells"):
        rows = []
        for mode_name in np.union1d(a.days.mode, b.days.mode):
            samples = []
            for data in (a, b):
                mask = data.days.mode == mode_name
                subset = ModeDays(
                    **{
                        field.name: getattr(data.days, field.name)[mask]
                        for field in fields(ModeDays)
                    }
                )
                samples.append(
                    ModeCellData(
                        subset,
                        {
                            name: values[mask]
                            for name, values in data.attributes.items()
                        },
                    )
                )
            for dimension in (
                "density",
                "population",
                "income",
                "vehicles",
                "household_type",
                "day_purpose",
            ):
                if any(dimension not in sample.attributes for sample in samples):
                    raise ValueError(f"Missing subgroup attribute {dimension}")
                raw = [sample.attributes[dimension].astype(str) for sample in samples]
                eligible = [
                    labels != "unknown"
                    if dimension == "population"
                    else np.ones(len(labels), dtype=bool)
                    for labels in raw
                ]
                matrices = [
                    np.column_stack((sample.days.mode[mask], labels[mask]))
                    for sample, labels, mask in zip(samples, raw, eligible, strict=True)
                ]
                if all(len(matrix) for matrix in matrices):
                    mapping = groupings.merge_cells(
                        matrices[0],
                        samples[0].days.day[eligible[0]],
                        matrices[1],
                        samples[1].days.day[eligible[1]],
                        dimensions=("mode", dimension),
                        config=merge_config,
                        minimum_n=minimum_n,
                    )
                    mapped = []
                    for labels in raw:
                        unique, inverse = np.unique(labels, return_inverse=True)
                        targets = [
                            mapping.get(
                                (str(mode_name), label), (str(mode_name), label)
                            )[1]
                            for label in unique
                        ]
                        mapped.append(np.asarray(targets)[inverse])
                else:
                    mapping = {}
                    mapped = raw
                estimates = mode_cell_statistics(
                    ModeCellSample(samples[0].days, mapped[0]),
                    ModeCellSample(samples[1].days, mapped[1]),
                    draws_a,
                    draws_b,
                    selected=selected,
                    minimum_n=minimum_n,
                    caution_n=caution_n,
                    margins=margins,
                )
                excluded = [
                    float(sample.days.weight[~mask].sum() / sample.days.weight.sum())
                    if len(sample.days.weight)
                    else np.nan
                    for sample, mask in zip(samples, eligible, strict=True)
                ]
                for row in estimates:
                    if dimension == "population" and row["cell"] == "unknown":
                        continue
                    row["grouping"] = dimension
                    row["merged_from"] = (
                        "+".join(
                            sorted(
                                source[1]
                                for source, target in mapping.items()
                                if target[1] == row["cell"]
                            )
                        )
                        or row["cell"]
                    )
                    row["excluded_population_share_2008"] = excluded[0]
                    row["excluded_population_share_2019"] = excluded[1]
                    rows.append(row)
        return rows


def _target_mean(
    target_codes: np.ndarray,
    target_weight: np.ndarray,
    source_codes: np.ndarray,
    source_weight: np.ndarray,
    source_minutes: np.ndarray,
    *,
    size: int,
    max_lost_share: float,
) -> tuple[float, float]:
    """Reweight the source to the target, reporting unsupported target mass."""
    target = np.bincount(target_codes, weights=target_weight, minlength=size)
    source = np.bincount(source_codes, weights=source_weight, minlength=size)
    if target.sum() <= 0 or source.sum() <= 0:
        return np.nan, np.nan
    target /= target.sum()
    common = source > 0
    lost = float(target[~common].sum())
    if lost >= max_lost_share or not common.any():
        return np.nan, lost
    target[~common] = 0
    target /= target.sum()
    factor = np.divide(target, source, out=np.zeros(size), where=common)
    reweighted = source_weight * factor[source_codes]
    return float(np.dot(reweighted, source_minutes) / reweighted.sum()), lost


def mode_reweighting(
    a: ModeCellData,
    b: ModeCellData,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    merge_config: groupings.MergeConfig,
    minimum_n: int,
    caution_n: int,
    max_lost_share: float,
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """Reweight 2019 mode users to the 2008 joint mix, section 9.9."""
    if minimum_n <= 0 or caution_n < minimum_n or not 0 < max_lost_share <= 1:
        raise ValueError("Invalid disclosure or support threshold")
    if len(draws_a.multipliers) == 0 or len(draws_a.multipliers) != len(
        draws_b.multipliers
    ):
        raise ValueError("Both surveys need equal nonempty household draws")
    dimensions = ("population", "density", "income")
    recorded = {} if timings is None else timings
    with modes._timed(recorded, f"{selected.id} mode reweighting"):
        rows = []
        for mode_name in np.union1d(a.days.mode, b.days.mode):
            prepared = []
            for data, draws in ((a, draws_a), (b, draws_b)):
                if any(name not in data.attributes for name in dimensions):
                    raise ValueError("Missing joint-reweighting attributes")
                mode_mask = data.days.mode == mode_name
                population = _text(data.attributes["population"], "population")
                income = _text(data.attributes["income"], "income")
                eligible = mode_mask & (population != "unknown") & (income != "unknown")
                days = ModeDays(
                    **{
                        field.name: getattr(data.days, field.name)[eligible]
                        for field in fields(ModeDays)
                    }
                )
                matrix = np.column_stack(
                    [
                        _text(data.attributes[name][eligible], name)
                        for name in dimensions
                    ]
                )
                if np.any(np.char.find(matrix, "|") >= 0):
                    raise ValueError("Joint labels cannot contain '|'")
                all_weight = data.days.weight[mode_mask].sum()
                excluded = (
                    float(data.days.weight[mode_mask & ~eligible].sum() / all_weight)
                    if all_weight > 0
                    else np.nan
                )
                prepared.append((days, matrix, _draw_weights(days, draws), excluded))
            (
                (days_a, matrix_a, weights_a, excluded_a),
                (days_b, matrix_b, weights_b, excluded_b),
            ) = prepared
            count_a, count_b = len(days_a.day), len(days_b.day)
            visible_a, visible_b = count_a >= minimum_n, count_b >= minimum_n
            row = {
                "scope": selected.id,
                "mode": str(mode_name),
                "n_2008": count_a,
                "n_2019": count_b,
                "caution_2008": count_a < caution_n,
                "caution_2019": count_b < caution_n,
                "excluded_share_2008": excluded_a,
                "excluded_share_2019": excluded_b,
                "mean_2008": np.nan,
                "mean_2019": np.nan,
                "ratio_before": np.nan,
                "ratio_before_low": np.nan,
                "ratio_before_high": np.nan,
                "ratio_after": np.nan,
                "ratio_after_low": np.nan,
                "ratio_after_high": np.nan,
                "lost_target_share": np.nan,
                "parent_fallback_share": np.nan,
                "fixed_2008_mean": np.nan,
                "status": "",
            }
            if count_a:
                row["mean_2008"] = (
                    float(np.average(days_a.minutes, weights=days_a.weight))
                    if visible_a
                    else np.nan
                )
            if count_b:
                row["mean_2019"] = (
                    float(np.average(days_b.minutes, weights=days_b.weight))
                    if visible_b
                    else np.nan
                )
            if selected.distance == "daytable":
                row["status"] = groupings.DAYTABLE_STATUS
                rows.append(row)
                continue
            if not (visible_a and visible_b):
                row["status"] = "insufficient mode-user days"
                rows.append(row)
                continue
            joint_config = groupings.MergeConfig(
                checkpoint_dir=merge_config.checkpoint_dir,
                dimensions={
                    name: rule
                    for name, rule in merge_config.dimensions.items()
                    if name == "density"
                },
            )
            mapping = groupings.merge_cells(
                matrix_a,
                days_a.day,
                matrix_b,
                days_b.day,
                dimensions=dimensions,
                config=joint_config,
                minimum_n=minimum_n,
            )
            combined = np.concatenate((matrix_a, matrix_b))
            original, inverse = np.unique(combined, axis=0, return_inverse=True)
            mapped = np.array(["|".join(mapping[tuple(cell)]) for cell in original])
            labels = mapped[inverse]
            labels_a, labels_b = labels[:count_a], labels[count_a:]
            unique_labels, codes = np.unique(labels, return_inverse=True)
            codes_a, codes_b = codes[:count_a], codes[count_a:]
            point, lost = _target_mean(
                codes_a,
                days_a.weight,
                codes_b,
                days_b.weight,
                days_b.minutes,
                size=len(unique_labels),
                max_lost_share=max_lost_share,
            )
            row["lost_target_share"] = lost
            observed_a = float(row["mean_2008"])
            observed_b = float(row["mean_2019"])
            if observed_a > 0 and observed_b > 0:
                row["ratio_before"] = observed_b / observed_a
                if np.isfinite(point):
                    row["ratio_after"] = point / observed_a
            if not np.isfinite(point):
                row["status"] = "insufficient common support for 2008 target"
            elif lost > 0:
                row["status"] = "2008 target rescaled to common support"
            parents_a, parents_b = matrix_a[:, 0], matrix_b[:, 0]
            missing = ~np.isin(labels_b, labels_a)
            row["parent_fallback_share"] = float(
                days_b.weight[missing].sum() / days_b.weight.sum()
            )
            if np.all(np.isin(parents_b[missing], parents_a)):
                fixed = groupings.fixed_cell_distribution(
                    groupings.CellSample(
                        days_a.minutes, days_a.weight, labels_a, parents_a
                    ),
                    groupings.CellSample(
                        days_b.minutes, days_b.weight, labels_b, parents_b
                    ),
                )
                row["fixed_2008_mean"] = float(
                    np.average(fixed.values, weights=fixed.weights)
                )
            else:
                row["status"] = (row["status"] + "; " if row["status"] else "") + (
                    "2008 parent distribution unavailable"
                )
            before, after = [], []
            for wa, wb in zip(weights_a, weights_b, strict=True):
                mean_a = (
                    float(np.average(days_a.minutes, weights=wa))
                    if wa.sum()
                    else np.nan
                )
                mean_b = (
                    float(np.average(days_b.minutes, weights=wb))
                    if wb.sum()
                    else np.nan
                )
                adjusted, _ = _target_mean(
                    codes_a,
                    wa,
                    codes_b,
                    wb,
                    days_b.minutes,
                    size=len(unique_labels),
                    max_lost_share=max_lost_share,
                )
                before.append(mean_b / mean_a if mean_a > 0 else np.nan)
                after.append(adjusted / mean_a if mean_a > 0 else np.nan)
            for name, point_name, replicates in (
                ("before", "ratio_before", before),
                ("after", "ratio_after", after),
            ):
                if np.isfinite(row[point_name]):
                    low, high = groupings._percentile_interval(
                        np.asarray(replicates), confidence=90
                    )
                    row[f"ratio_{name}_low"] = low
                    row[f"ratio_{name}_high"] = high
            rows.append(row)
        return rows


@dataclass(frozen=True)
class ModeTrips:
    """Scoped trips: durations in minutes and distances in km, section 9.9."""

    day: np.ndarray
    household: np.ndarray
    mode: np.ndarray
    weight: np.ndarray
    minutes: np.ndarray
    published_km: np.ndarray
    crow_fly_km: np.ndarray


def read_mode_trips(
    con: duckdb.DuckDBPyConnection,
    cache: modes_cache.SurveyCache,
    selected: scope.Scope,
) -> ModeTrips:
    """Join scoped cached trips to reconstructed published distance, section 9.9.

    ``trip_legs`` must have been reconstructed using the survey's step-11
    formulas. The Z1 cache's corrected distance is not the published distance.
    """
    rows = con.execute(
        """SELECT CAST(v.day_id AS VARCHAR) day_id,
            CAST(v.ident_men AS VARCHAR) household, v.mode7, v.pond_jour,
            v.duration_min, t.distance_km_declared, v.crow_fly_km,
            count(t.day_id) OVER (PARTITION BY v.day_id, v.num_dep) matches
        FROM read_parquet(?) v LEFT JOIN trip_legs t
          ON t.day_id = v.day_id AND t.num_dep = v.num_dep""",
        [str(cache.trips(selected))],
    ).fetchnumpy()
    rows = {name: vr._plain_array(value) for name, value in rows.items()}
    if np.any(rows["matches"] != 1):
        raise ValueError(
            "Scoped cached trip does not match exactly one reconstructed trip"
        )
    return ModeTrips(
        _text(rows["day_id"], "day"),
        _text(rows["household"], "household"),
        _text(rows["mode7"], "mode"),
        np.asarray(rows["pond_jour"], dtype=float),
        np.asarray(rows["duration_min"], dtype=float),
        np.asarray(rows["distance_km_declared"], dtype=float),
        np.asarray(rows["crow_fly_km"], dtype=float),
    )


def _mode_trip_days(
    trips: ModeTrips, mode_name: str, distance: np.ndarray
) -> ModeDays | None:
    mask = trips.mode == mode_name
    if not mask.any():
        return None
    km = np.asarray(distance[mask], dtype=float)
    km = np.where(np.isfinite(km) & (km >= 0), km, np.nan)
    return aggregate_mode_days(
        day=trips.day[mask],
        mode=trips.mode[mask],
        household=trips.household[mask],
        weight=trips.weight[mask],
        minutes=trips.minutes[mask],
        distance_km=km,
        energy_kj=np.full(int(mask.sum()), np.nan),
    )


def _person_days(days: ModeDays, weight: np.ndarray) -> variation.PersonDays:
    return variation.PersonDays(
        weight=weight,
        trips=days.trips,
        distance_km=days.distance_km,
        time_min=days.minutes,
        household=days.household,
        distance_trips=days.distance_trips,
        distance_time_min=days.distance_minutes,
    )


def mode_decompositions(
    a: ModeTrips,
    b: ModeTrips,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    minimum_n: int,
    caution_n: int,
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """B2 per mode-user day, with published and rounded crow-fly km."""
    if minimum_n <= 0 or caution_n < minimum_n:
        raise ValueError("Invalid disclosure thresholds")
    if not len(draws_a.multipliers) or len(draws_a.multipliers) != len(
        draws_b.multipliers
    ):
        raise ValueError("Both surveys need equal nonempty household draws")
    with modes._timed(
        {} if timings is None else timings, f"{selected.id} mode decomposition"
    ):
        rows = []
        for mode_name in np.union1d(a.mode, b.mode):
            for variant, distance_a, distance_b in (
                ("published", a.published_km, b.published_km),
                (
                    "rounded_crow_fly",
                    a.crow_fly_km,
                    vr._rounded_crow_fly_km(b.crow_fly_km),
                ),
            ):
                first = _mode_trip_days(a, str(mode_name), distance_a)
                second = _mode_trip_days(b, str(mode_name), distance_b)
                n_a = len(first.day) if first is not None else 0
                n_b = len(second.day) if second is not None else 0
                row = {
                    "scope": selected.id,
                    "mode": str(mode_name),
                    "variant": variant,
                    "n_2008": n_a,
                    "n_2019": n_b,
                    "caution_2008": n_a < caution_n,
                    "caution_2019": n_b < caution_n,
                    "status": "",
                    "distance_a_km": np.nan,
                    "distance_b_km": np.nan,
                    "trips_a": np.nan,
                    "trips_b": np.nan,
                    "speed_a_kmh": np.nan,
                    "speed_b_kmh": np.nan,
                    "distance_share_a": np.nan,
                    "distance_share_b": np.nan,
                }
                for name in ("delta", "trips", "distance", "speed", "selection"):
                    row[name] = row[f"{name}_low"] = row[f"{name}_high"] = np.nan
                if selected.distance == "daytable":
                    row["status"] = groupings.DAYTABLE_STATUS
                elif first is None or second is None or min(n_a, n_b) < minimum_n:
                    row["status"] = "insufficient mode-user days"
                else:
                    full_a = _person_days(first, first.weight)
                    full_b = _person_days(second, second.weight)
                    if not (
                        variation._has_positive_weighted_metrics(full_a)
                        and variation._has_positive_weighted_metrics(full_b)
                    ):
                        row["status"] = "insufficient distance or duration support"
                    else:
                        point = variation.decompose(full_a, full_b)
                        row["distance_a_km"] = point.distance_a_km
                        row["distance_b_km"] = point.distance_b_km
                        row["trips_a"] = point.trips_a
                        row["trips_b"] = point.trips_b
                        row["speed_a_kmh"] = 60 * point.speed_a_km_per_min
                        row["speed_b_kmh"] = 60 * point.speed_b_km_per_min
                        row["distance_share_a"] = point.distance_share_a
                        row["distance_share_b"] = point.distance_share_b
                        names = ("delta", "trips", "distance", "speed", "selection")
                        keys = (
                            "delta_min",
                            "trips_min",
                            "distance_min",
                            "speed_min",
                            "selection_min",
                        )
                        replications = np.full(
                            (len(draws_a.multipliers), len(keys)), np.nan
                        )
                        wa, wb = (
                            _draw_weights(first, draws_a),
                            _draw_weights(second, draws_b),
                        )
                        for index, (weights_a, weights_b) in enumerate(
                            zip(wa, wb, strict=True)
                        ):
                            sample_a = _person_days(first, weights_a)
                            sample_b = _person_days(second, weights_b)
                            if variation._has_positive_weighted_metrics(
                                sample_a
                            ) and variation._has_positive_weighted_metrics(sample_b):
                                result = variation.decompose(sample_a, sample_b)
                                replications[index] = [
                                    getattr(result, key) for key in keys
                                ]
                        for index, (name, key) in enumerate(
                            zip(names, keys, strict=True)
                        ):
                            row[name] = getattr(point, key)
                            low, high = groupings._percentile_interval(
                                replications[:, index], confidence=95
                            )
                            row[f"{name}_low"], row[f"{name}_high"] = low, high
                rows.append(row)
        return rows


def mode_rounding_bounds(
    a: ModeTrips,
    b: ModeTrips,
    *,
    selected: scope.Scope,
    config: variation.MeasurementConfig,
    minimum_n: int,
    caution_n: int,
    seed: int,
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """C4 row-a nearest/up extrema per mode-user day, in minutes."""
    if minimum_n <= 0 or caution_n < minimum_n:
        raise ValueError("Invalid disclosure thresholds")
    with modes._timed(
        {} if timings is None else timings, f"{selected.id} mode rounding"
    ):
        rows = []
        for mode_name in np.union1d(a.mode, b.mode):
            masks = (a.mode == mode_name, b.mode == mode_name)
            samples = [
                _mode_trip_days(trips, str(mode_name), trips.published_km)
                for trips in (a, b)
            ]
            n_a, n_b = (
                len(sample.day) if sample is not None else 0 for sample in samples
            )
            row = {
                "scope": selected.id,
                "mode": str(mode_name),
                "n_2008": n_a,
                "n_2019": n_b,
                "caution_2008": n_a < caution_n,
                "caution_2019": n_b < caution_n,
                "lower_min": np.nan,
                "upper_min": np.nan,
                "mean_min": np.nan,
                "unmatched_2008_trip_share": np.nan,
                "status": "",
            }
            if selected.distance == "daytable":
                row["status"] = groupings.DAYTABLE_STATUS
            elif samples[0] is None or samples[1] is None or min(n_a, n_b) < minimum_n:
                row["status"] = "insufficient mode-user days"
            else:
                frames = [
                    vr.SurveyFrames(
                        "",
                        {},
                        {
                            "mode7": trips.mode[mask],
                            "duration_min": trips.minutes[mask],
                            "pond_jour": trips.weight[mask],
                        },
                        {},
                    )
                    for trips, mask in zip((a, b), masks, strict=True)
                ]
                cells_a, _ = vr._rounding_cells(frames[0], config)
                cells_b, _ = vr._rounding_cells(frames[1], config)
                unmatched = ~np.isin(cells_a, cells_b)
                row["unmatched_2008_trip_share"] = float(
                    a.weight[masks[0]][unmatched].sum() / a.weight[masks[0]].sum()
                )
                if unmatched.any():
                    row["status"] = "bounds incomplete: 2019 rounding cells missing"
                changes = []
                for variant in ("nearest", "up"):
                    rng = np.random.default_rng(seed)
                    for _ in range(config.rounding_draws):
                        simulated = vr.simulate_rounding(
                            frames[0], frames[1], variant, config=config, rng=rng
                        )
                        changes.append(
                            float(
                                np.dot(
                                    a.weight[masks[0]], simulated - a.minutes[masks[0]]
                                )
                                / samples[0].weight.sum()
                            )
                        )
                row["lower_min"], row["upper_min"] = min(changes), max(changes)
                row["mean_min"] = float(np.mean(changes))
            rows.append(row)
        return rows


def read_mode_energy(
    con: duckdb.DuckDBPyConnection,
    cache: modes_cache.SurveyCache,
    selected: scope.Scope,
    *,
    rate: str,
) -> ModeDays:
    """Aggregate modeled trip energy by mode-user day, in kJ above rest."""
    if rate not in ("kh", "cp"):
        raise ValueError(f"Unsupported energy rate set: {rate}")
    rows = con.execute(
        f"""SELECT CAST(v.day_id AS VARCHAR) day_id,
            CAST(v.ident_men AS VARCHAR) household, v.mode7, v.pond_jour,
            v.duration_min, v.distance_km, t.energy_{rate}_kj AS energy_kj,
            count(t.day_id) OVER (PARTITION BY v.day_id, v.num_dep) matches
        FROM read_parquet(?) v LEFT JOIN trip_legs t
          ON t.day_id = v.day_id AND t.num_dep = v.num_dep""",
        [str(cache.trips(selected))],
    ).fetchnumpy()
    rows = {name: vr._plain_array(value) for name, value in rows.items()}
    if np.any(rows["matches"] != 1):
        raise ValueError("Scoped cached trip does not match exactly one energy trip")
    return aggregate_mode_days(
        day=rows["day_id"],
        mode=rows["mode7"],
        household=rows["household"],
        weight=rows["pond_jour"],
        minutes=rows["duration_min"],
        distance_km=rows["distance_km"],
        energy_kj=rows["energy_kj"],
    )


def _energy_samples(
    data: ModeDays, draws: modes.Draws
) -> dict[str, tuple[ModeDays, np.ndarray]]:
    result = {}
    for mode_name in np.unique(data.mode):
        mask = data.mode == mode_name
        subset = ModeDays(
            **{
                field.name: getattr(data, field.name)[mask]
                for field in fields(ModeDays)
            }
        )
        result[str(mode_name)] = (subset, _draw_weights(subset, draws))
    return result


def _collapse_ks(
    a: ModeDays, b: ModeDays, wa: np.ndarray, wb: np.ndarray
) -> tuple[float, float]:
    if wa.sum() <= 0 or wb.sum() <= 0:
        return np.nan, np.nan
    known_a, known_b = np.isfinite(a.energy_kj), np.isfinite(b.energy_kj)
    time_ks = modes.weighted_ks(
        modes.Observations(a.minutes, wa, a.household),
        modes.Observations(b.minutes, wb, b.household),
    )
    energy_ks = np.nan
    if wa[known_a].sum() > 0 and wb[known_b].sum() > 0:
        energy_ks = modes.weighted_ks(
            modes.Observations(a.energy_kj[known_a], wa[known_a], a.household[known_a]),
            modes.Observations(b.energy_kj[known_b], wb[known_b], b.household[known_b]),
        )
    return time_ks, energy_ks


def energy_collapse(
    a: ModeDays,
    b: ModeDays,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    rate: str,
    minimum_n: int,
    caution_n: int,
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """Compare within-year pairwise and cross-year mode distributions."""
    if rate not in ("kh", "cp") or minimum_n <= 0 or caution_n < minimum_n:
        raise ValueError("Invalid rate set or disclosure thresholds")
    if selected != scope.REFERENCE_SCOPE:
        raise ValueError("The energy collapse test uses the reference scope only")
    if not len(draws_a.multipliers) or len(draws_a.multipliers) != len(
        draws_b.multipliers
    ):
        raise ValueError("Both surveys need equal nonempty household draws")
    with modes._timed({} if timings is None else timings, f"{rate} energy collapse"):
        samples_a = _energy_samples(a, draws_a)
        samples_b = _energy_samples(b, draws_b)
        rows = []

        def intervals(
            row: dict,
            point: tuple[float, float],
            reps: np.ndarray,
            visible: tuple[bool, bool],
        ) -> None:
            for index, name in enumerate(("time", "energy")):
                if visible[index] and np.isfinite(point[index]):
                    row[f"{name}_ks"] = point[index]
                    low, high = groupings._percentile_interval(
                        reps[:, index], confidence=95
                    )
                    row[f"{name}_ks_low"] = low
                    row[f"{name}_ks_high"] = high

        for year, samples in ((2008, samples_a), (2019, samples_b)):
            point_pairs = []
            replicate_pairs = []
            for left, right in combinations(sorted(samples), 2):
                sa, wa = samples[left]
                sb, wb = samples[right]
                row = {
                    "kind": "within_year_pair",
                    "year": year,
                    "rate": rate,
                    "scope": selected.id,
                    "mode_a": left,
                    "mode_b": right,
                    "n_a": len(sa.day),
                    "n_b": len(sb.day),
                    "energy_n_a": int(np.isfinite(sa.energy_kj).sum()),
                    "energy_n_b": int(np.isfinite(sb.energy_kj).sum()),
                    "caution": min(len(sa.day), len(sb.day)) < caution_n,
                    "time_ks": np.nan,
                    "energy_ks": np.nan,
                    "time_ks_low": np.nan,
                    "time_ks_high": np.nan,
                    "energy_ks_low": np.nan,
                    "energy_ks_high": np.nan,
                    "status": "",
                }
                row["energy_caution"] = (
                    min(row["energy_n_a"], row["energy_n_b"]) < caution_n
                )
                point = _collapse_ks(sa, sb, sa.weight, sb.weight)
                reps = np.asarray(
                    [_collapse_ks(sa, sb, x, y) for x, y in zip(wa, wb, strict=True)]
                )
                if np.isfinite(point).all():
                    point_pairs.append(point)
                    replicate_pairs.append(reps)
                time_visible = min(len(sa.day), len(sb.day)) >= minimum_n
                energy_visible = min(row["energy_n_a"], row["energy_n_b"]) >= minimum_n
                intervals(row, point, reps, (time_visible, energy_visible))
                if not time_visible:
                    row["status"] = "small mode cell hidden"
                elif not energy_visible:
                    row["status"] = "mode energy unavailable or hidden"
                rows.append(row)
            summary = {
                "kind": "within_year_median",
                "year": year,
                "rate": rate,
                "scope": selected.id,
                "mode_a": "",
                "mode_b": "",
                "n_pairs": len(point_pairs),
                "time_ks": np.nan,
                "energy_ks": np.nan,
                "time_ks_low": np.nan,
                "time_ks_high": np.nan,
                "energy_ks_low": np.nan,
                "energy_ks_high": np.nan,
                "energy_minus_time": np.nan,
                "energy_minus_time_low": np.nan,
                "energy_minus_time_high": np.nan,
                "comparison": "",
                "comparison_basis": "pairs with known energy in both modes",
                "status": "",
            }
            if point_pairs:
                point = np.median(np.asarray(point_pairs), axis=0)
                rep_array = np.stack(replicate_pairs)
                complete = np.isfinite(rep_array).all(axis=(0, 2))
                medians = np.full((len(draws_a.multipliers), 2), np.nan)
                medians[complete] = np.median(rep_array[:, complete, :], axis=0)
                intervals(
                    summary, (float(point[0]), float(point[1])), medians, (True, True)
                )
                summary["energy_minus_time"] = float(point[1] - point[0])
                low, high = groupings._percentile_interval(
                    medians[:, 1] - medians[:, 0], confidence=95
                )
                summary["energy_minus_time_low"], summary["energy_minus_time_high"] = (
                    low,
                    high,
                )
                summary["comparison"] = (
                    "closer" if point[1] < point[0] else "not closer"
                )
            else:
                summary["status"] = "fewer than two modes with known energy"
            rows.append(summary)
        for mode_name in sorted(samples_a.keys() | samples_b.keys()):
            row = {
                "kind": "across_year_mode",
                "year": "",
                "rate": rate,
                "scope": selected.id,
                "mode_a": mode_name,
                "mode_b": mode_name,
                "time_ks": np.nan,
                "energy_ks": np.nan,
                "time_ks_low": np.nan,
                "time_ks_high": np.nan,
                "energy_ks_low": np.nan,
                "energy_ks_high": np.nan,
                "status": "",
            }
            if mode_name not in samples_a or mode_name not in samples_b:
                row["status"] = "mode unavailable in one year"
            else:
                sa, wa = samples_a[mode_name]
                sb, wb = samples_b[mode_name]
                row["n_a"], row["n_b"] = len(sa.day), len(sb.day)
                row["energy_n_a"] = int(np.isfinite(sa.energy_kj).sum())
                row["energy_n_b"] = int(np.isfinite(sb.energy_kj).sum())
                row["caution"] = min(len(sa.day), len(sb.day)) < caution_n
                row["energy_caution"] = (
                    min(row["energy_n_a"], row["energy_n_b"]) < caution_n
                )
                time_visible = min(len(sa.day), len(sb.day)) >= minimum_n
                energy_visible = min(row["energy_n_a"], row["energy_n_b"]) >= minimum_n
                point = _collapse_ks(sa, sb, sa.weight, sb.weight)
                reps = np.asarray(
                    [_collapse_ks(sa, sb, x, y) for x, y in zip(wa, wb, strict=True)]
                )
                intervals(row, point, reps, (time_visible, energy_visible))
                if not time_visible:
                    row["status"] = "small mode cell hidden"
                elif not energy_visible:
                    row["status"] = "mode energy unavailable or hidden"
            rows.append(row)
        return rows


@dataclass(frozen=True)
class EnergySurvey:
    """Reference-scope respondent and day energy in kJ above rest, section 9.9."""

    roster_household: np.ndarray
    roster_weight: np.ndarray
    roster_labels: dict[str, np.ndarray]
    day_id: np.ndarray
    day_household: np.ndarray
    day_weight: np.ndarray
    day_labels: dict[str, np.ndarray]
    day_mode: np.ndarray
    is_open: np.ndarray
    has_trips: np.ndarray
    energy_kj: np.ndarray
    mode_kj: dict[str, np.ndarray]
    mode_used: dict[str, np.ndarray]


def read_energy_survey(
    cache: modes_cache.SurveyCache,
    cached: income_module.CachedIncome,
    mode_days: ModeDays,
    *,
    rate: str,
) -> EnergySurvey:
    """Join cached weekday persons and day energy to reconstructed mode energy."""
    if rate not in ("kh", "cp"):
        raise ValueError(f"Unsupported energy rate set: {rate}")
    with duckdb.connect() as con:
        rows = con.execute(
            f"""SELECT CAST(b.day_id AS VARCHAR) day_id,
                trim(CAST(b.ident_ind AS VARCHAR)) person,
                trim(CAST(b.ident_men AS VARCHAR)) household, b.pond_jour AS weight,
                d.day_id IS NOT NULL has_trips,
                CASE WHEN d.day_id IS NULL THEN 0
                     ELSE d.total_energy_{rate}_kj END AS energy_kj,
                coalesce(d.day_mode_group, 'unknown') AS day_mode
            FROM read_parquet(?) b LEFT JOIN read_parquet(?) d ON d.day_id=b.day_id
            ORDER BY b.day_id""",
            [str(cache.day_base), str(cache.days(scope.REFERENCE_SCOPE))],
        ).fetchnumpy()
    rows = {name: vr._plain_array(value) for name, value in rows.items()}
    day_ids = _text(rows["day_id"], "day")
    persons = _text(rows["person"], "day person")
    households = _text(rows["household"], "day household")
    roster_person = _text(cached.people.person, "roster person")
    if len(day_ids) != len(np.unique(day_ids)) or len(roster_person) != len(
        np.unique(roster_person)
    ):
        raise ValueError("Duplicate day or roster person")
    if (
        not np.array_equal(persons, _text(cached.days.person, "cached day person"))
        or not np.array_equal(
            households, _text(cached.days.household, "cached day household")
        )
        or not np.allclose(rows["weight"], cached.days.weight)
        or not np.array_equal(rows["has_trips"], cached.days.has_trips)
    ):
        raise ValueError("Cached energy days do not match cached income days")
    order = np.argsort(roster_person)
    lookup = np.searchsorted(roster_person[order], persons)
    if np.any(lookup >= len(order)) or np.any(roster_person[order][lookup] != persons):
        raise ValueError("Day person missing from roster")
    person_index = order[lookup]
    if not np.array_equal(
        _text(cached.people.household, "roster household")[person_index], households
    ):
        raise ValueError("Day household differs from roster household")
    day_order = np.argsort(day_ids)
    mode_index = np.searchsorted(day_ids[day_order], mode_days.day)
    if np.any(mode_index >= len(day_ids)) or np.any(
        day_ids[day_order][mode_index] != mode_days.day
    ):
        raise ValueError("Mode energy day missing from day base")
    day_index = day_order[mode_index]
    if (
        not np.array_equal(households[day_index], mode_days.household)
        or not np.allclose(rows["weight"][day_index], mode_days.weight)
        or not np.array_equal(
            np.unique(day_index), np.flatnonzero(cached.days.has_trips)
        )
    ):
        raise ValueError("Mode energy records do not match cached travel days")
    mode_kj, mode_used = {}, {}
    for mode_name in np.unique(mode_days.mode):
        selected = mode_days.mode == mode_name
        indices = day_index[selected]
        mode_kj[str(mode_name)] = np.zeros(len(day_ids))
        mode_used[str(mode_name)] = np.zeros(len(day_ids), dtype=bool)
        mode_kj[str(mode_name)][indices] = mode_days.energy_kj[selected]
        mode_used[str(mode_name)][indices] = True
    labels = {
        "population": cached.population,
        "density": cached.density,
        "income": cached.people.income,
        "vehicles": cached.cars,
    }
    survey = EnergySurvey(
        roster_household=_text(cached.people.household, "roster household"),
        roster_weight=cached.people.weight,
        roster_labels=labels,
        day_id=day_ids,
        day_household=households,
        day_weight=cached.days.weight,
        day_labels={name: values[person_index] for name, values in labels.items()},
        day_mode=_text(rows["day_mode"], "day mode"),
        is_open=cached.days.is_open,
        has_trips=cached.days.has_trips,
        energy_kj=np.asarray(rows["energy_kj"], dtype=float),
        mode_kj=mode_kj,
        mode_used=mode_used,
    )
    _energy_survey_validate(survey)
    return survey


def _energy_survey_validate(data: EnergySurvey) -> None:
    """Validate energy inputs and the daily mode-to-total accounting identity."""
    n_people, n_days = len(data.roster_weight), len(data.day_weight)
    if not n_people or any(
        len(array) != n_people
        for array in (data.roster_household, *data.roster_labels.values())
    ):
        raise ValueError("Invalid energy respondent arrays")
    if any(
        len(array) != n_days
        for array in (
            data.day_id,
            data.day_household,
            data.day_mode,
            data.is_open,
            data.has_trips,
            data.energy_kj,
            *data.day_labels.values(),
            *data.mode_kj.values(),
            *data.mode_used.values(),
        )
    ):
        raise ValueError("Invalid energy day arrays")
    if set(data.mode_kj) != set(data.mode_used):
        raise ValueError("Mode energy and use labels differ")
    if data.is_open.dtype != np.dtype(bool) or data.has_trips.dtype != np.dtype(bool):
        raise ValueError("Open and travel-day indicators must be boolean")
    if (
        not np.isfinite(data.roster_weight).all()
        or not np.isfinite(data.day_weight).all()
        or np.any(data.roster_weight < 0)
        or np.any(data.day_weight < 0)
        or data.roster_weight.sum() <= 0
        or np.any(np.isinf(data.energy_kj))
        or np.any(data.energy_kj < 0)
    ):
        raise ValueError("Invalid energy weights or daily values")
    known = np.isfinite(data.energy_kj)
    if np.any(~data.has_trips & (~known | (data.energy_kj != 0))):
        raise ValueError("Days without scoped trips must have zero energy")
    total = np.zeros(n_days)
    for mode_name, values in data.mode_kj.items():
        used = data.mode_used[mode_name]
        if (
            used.dtype != np.dtype(bool)
            or np.any(np.isinf(values))
            or np.any(values < 0)
        ):
            raise ValueError("Invalid mode energy or use indicators")
        if np.any(~used & ((~np.isfinite(values)) | (values != 0))):
            raise ValueError("Non-users must have zero attributable energy")
        total += np.where(np.isfinite(values), values, 0)
    if not np.allclose(total[known], data.energy_kj[known], rtol=1e-8, atol=1e-8):
        raise ValueError("Mode energy does not sum to daily energy")


def _energy_draw_weights(
    household: np.ndarray, weight: np.ndarray, draws: modes.Draws
) -> np.ndarray:
    universe = _text(np.asarray(draws.households), "draw household")
    households = _text(household, "household")
    if not np.array_equal(universe, np.unique(universe)):
        raise ValueError("Draw households must be unique and sorted text")
    if draws.multipliers.ndim != 2 or draws.multipliers.shape[1] != len(universe):
        raise ValueError("Invalid household draw matrix")
    if np.any(~np.isfinite(draws.multipliers)) or np.any(draws.multipliers < 0):
        raise ValueError("Invalid household draw multipliers")
    indices = income_module._household_indices(households, universe)
    return draws.multipliers[:, indices] * weight


def _energy_metric(
    data: EnergySurvey,
    roster_mask: np.ndarray,
    day_mask: np.ndarray,
    values: np.ndarray,
    basis: str,
    roster_draws: np.ndarray,
    day_draws: np.ndarray,
) -> modes.Metric:
    """Weighted daily energy and aligned household replicates in kJ."""
    known = np.isfinite(data.energy_kj)
    travel = day_mask & ~data.is_open & data.has_trips & known
    excluded = day_mask & (data.is_open | (data.has_trips & ~known))
    numerators = np.where(travel, np.nan_to_num(values, nan=0.0), 0.0)
    numerator = float(np.dot(data.day_weight, numerators))
    rep_numerator = day_draws @ numerators
    if basis == "travel_day":
        denominator = float(data.day_weight[travel].sum())
        rep_denominator = day_draws @ travel.astype(float)
    elif basis == "person":
        denominator = float(
            data.roster_weight[roster_mask].sum() - data.day_weight[excluded].sum()
        )
        rep_denominator = roster_draws @ roster_mask.astype(
            float
        ) - day_draws @ excluded.astype(float)
    else:
        raise ValueError(f"Unknown energy basis {basis}")
    if denominator < 0:
        raise ValueError("Energy denominator after excluded days is negative")
    replicates = np.divide(
        rep_numerator,
        rep_denominator,
        out=np.full(len(rep_numerator), np.nan),
        where=rep_denominator > 0,
    )
    return modes.Metric(
        numerator / denominator if denominator > 0 else np.nan, replicates
    )


def energy_statistics(
    a: EnergySurvey,
    b: EnergySurvey,
    draws_a: modes.Draws,
    draws_b: modes.Draws,
    *,
    selected: scope.Scope,
    rate: str,
    minimum_n: int,
    caution_n: int,
    margins: tuple[float, float],
    merge_config: groupings.MergeConfig,
    timings: dict[str, float] | None = None,
) -> list[dict]:
    """Energy by group and attributable mode, with household intervals."""
    if selected != scope.REFERENCE_SCOPE or rate not in ("kh", "cp"):
        raise ValueError("Energy levels require the reference scope and known rate set")
    if minimum_n <= 0 or caution_n < minimum_n or not all(0 < m < 1 for m in margins):
        raise ValueError("Invalid energy thresholds or equivalence margins")
    if not len(draws_a.multipliers) or len(draws_a.multipliers) != len(
        draws_b.multipliers
    ):
        raise ValueError("Both surveys need equal nonempty household draws")
    for sample in (a, b):
        _energy_survey_validate(sample)
        for dimension in ("population", "density", "income", "vehicles"):
            if (
                dimension not in sample.day_labels
                or dimension not in sample.roster_labels
            ):
                raise ValueError(f"Missing energy grouping {dimension}")
    with modes._timed({} if timings is None else timings, f"{rate} grouped energy"):
        day_weights = [
            _energy_draw_weights(data.day_household, data.day_weight, draws)
            for data, draws in ((a, draws_a), (b, draws_b))
        ]
        roster_weights = [
            _energy_draw_weights(data.roster_household, data.roster_weight, draws)
            for data, draws in ((a, draws_a), (b, draws_b))
        ]
        rows = []
        for dimension in (
            "overall",
            "population",
            "density",
            "income",
            "vehicles",
            "day_mode_group",
            "mode",
        ):
            raw_day = []
            raw_roster = []
            for data in (a, b):
                if dimension == "overall":
                    raw_day.append(np.full(len(data.day_id), "all"))
                    raw_roster.append(np.full(len(data.roster_weight), "all"))
                elif dimension == "day_mode_group":
                    raw_day.append(_text(data.day_mode, "day mode"))
                    raw_roster.append(np.full(len(data.roster_weight), ""))
                elif dimension == "mode":
                    raw_day.append(np.full(len(data.day_id), ""))
                    raw_roster.append(np.full(len(data.roster_weight), "all"))
                else:
                    raw_day.append(_text(data.day_labels[dimension], dimension))
                    raw_roster.append(_text(data.roster_labels[dimension], dimension))
            mapping = {}
            if dimension in ("density", "income", "vehicles"):
                eligible = [
                    data.has_trips & ~data.is_open & np.isfinite(data.energy_kj)
                    for data in (a, b)
                ]
                matrices = [
                    np.column_stack((np.full(mask.sum(), "all"), labels[mask]))
                    for labels, mask in zip(raw_day, eligible, strict=True)
                ]
                if all(len(matrix) for matrix in matrices):
                    mapping = groupings.merge_cells(
                        matrices[0],
                        a.day_id[eligible[0]],
                        matrices[1],
                        b.day_id[eligible[1]],
                        dimensions=("all", dimension),
                        config=merge_config,
                        minimum_n=minimum_n,
                    )

            def mapped(labels: np.ndarray) -> np.ndarray:
                unique, inverse = np.unique(labels, return_inverse=True)
                targets = [
                    mapping.get(("all", label), ("all", label))[1] for label in unique
                ]
                return np.asarray(targets)[inverse]

            days_labels = [mapped(labels) for labels in raw_day]
            roster_labels = [mapped(labels) for labels in raw_roster]
            labels = (
                sorted(a.mode_kj.keys() | b.mode_kj.keys())
                if dimension == "mode"
                else np.union1d(days_labels[0], days_labels[1]).tolist()
            )
            for label in labels:
                if dimension == "population" and label == "unknown":
                    continue
                bases = ("person",) if dimension == "mode" else ("travel_day", "person")
                for basis in bases:
                    row = {
                        "scope": selected.id,
                        "rate": rate,
                        "grouping": dimension,
                        "cell": str(label),
                        "basis": basis,
                        "status": "",
                        "ratio": np.nan,
                        "ratio_low": np.nan,
                        "ratio_high": np.nan,
                        "verdict_15": "",
                        "verdict_10": "",
                    }
                    if dimension == "day_mode_group" and basis == "person":
                        row.update(
                            mean_2008=np.nan,
                            mean_2019=np.nan,
                            status="not defined: days without trips have no mode group",
                        )
                        rows.append(row)
                        continue
                    metrics = []
                    for index, (year, data) in enumerate(((2008, a), (2019, b))):
                        if dimension == "mode":
                            used = data.mode_used.get(
                                label, np.zeros(len(data.day_id), dtype=bool)
                            )
                            values = data.mode_kj.get(label, np.zeros(len(data.day_id)))
                            day_mask = np.ones(len(data.day_id), dtype=bool)
                            roster_mask = np.ones(len(data.roster_weight), dtype=bool)
                            count = int(
                                np.sum(used & ~data.is_open & np.isfinite(values))
                            )
                            unavailable = bool(
                                np.any(used & ~data.is_open & ~np.isfinite(values))
                            )
                        else:
                            day_mask = days_labels[index] == label
                            roster_mask = roster_labels[index] == label
                            values = data.energy_kj
                            count = int(
                                np.sum(
                                    day_mask
                                    & data.has_trips
                                    & ~data.is_open
                                    & np.isfinite(data.energy_kj)
                                )
                            )
                            unavailable = False
                        metric = _energy_metric(
                            data,
                            roster_mask,
                            day_mask,
                            values,
                            basis,
                            roster_weights[index],
                            day_weights[index],
                        )
                        metrics.append(metric)
                        visible = count >= minimum_n and not unavailable
                        row[f"n_{year}"] = count
                        row[f"caution_{year}"] = count < caution_n
                        row[f"mean_{year}"] = metric.value if visible else np.nan
                        low, high = (
                            groupings._percentile_interval(
                                metric.replicates, confidence=95
                            )
                            if visible and np.isfinite(metric.value)
                            else (np.nan, np.nan)
                        )
                        row[f"mean_{year}_low"], row[f"mean_{year}_high"] = low, high
                        if unavailable:
                            row["status"] = "mode energy unavailable"
                        elif count < minimum_n and not row["status"]:
                            row["status"] = "small cell hidden"
                    if (
                        np.isfinite(row["mean_2008"])
                        and row["mean_2008"] > 0
                        and np.isfinite(row["mean_2019"])
                    ):
                        ratios = np.divide(
                            metrics[1].replicates,
                            metrics[0].replicates,
                            out=np.full(len(metrics[0].replicates), np.nan),
                            where=metrics[0].replicates > 0,
                        )
                        low, high = groupings._percentile_interval(
                            ratios, confidence=90
                        )
                        row.update(
                            ratio=metrics[1].value / metrics[0].value,
                            ratio_low=low,
                            ratio_high=high,
                        )
                        if np.isfinite(low) and np.isfinite(high):
                            row["verdict_15"] = vr._equivalence_verdict(
                                (low, high), margins[0]
                            )
                            row["verdict_10"] = vr._equivalence_verdict(
                                (low, high), margins[1]
                            )
                    rows.append(row)
        return rows


if __name__ == "__main__":
    raise SystemExit("Mode-cell report is not implemented yet.")
