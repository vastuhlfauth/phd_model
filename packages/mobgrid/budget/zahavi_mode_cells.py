"""Foundations for mode-user-day analyses, section 9.9.

The report and command-line interface are not yet implemented.
"""

from dataclasses import dataclass, fields

import duckdb
import numpy as np

from mobgrid.budget import modes_cache, scope
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
        _text(day, "day"), _text(mode, "mode"), _text(household, "household")
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
    _, day_first, day_inverse = np.unique(
        day, return_index=True, return_inverse=True
    )
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
        target / target.sum(), source / source.sum(),
        out=np.zeros(size), where=source > 0,
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
        day=trips["day_id"], mode=trips["mode7"], household=trips["household"],
        weight=trips["pond_jour"], minutes=trips["duration_min"],
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
        if known_trips > 0 else np.nan
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
        time_a, time_b, distance_a, distance_b, speed_a, speed_b, known_a, known_b
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
                "unavailable" if not visible or known_trips == 0 else
                "incomplete" if known_trips < all_trips else "complete"
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
                    if weights[mask].sum() > 0 else np.nan
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
                ("minutes", "km", "speed", "ks", "distance_gap", "speed_gap",
                 "selection_gap"),
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
        row.update(ratio=np.nan, ratio_low=np.nan, ratio_high=np.nan,
                   verdict_15="", verdict_10="")
        if (
            selected.distance != "daytable"
            and min(row["n_2008"], row["n_2019"]) >= minimum_n
            and means[0] > 0
            and means[1] > 0
        ):
            ratios = np.divide(
                replicate_means[1], replicate_means[0],
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
                    **{field.name: getattr(data.days, field.name)[mask]
                       for field in fields(ModeDays)}
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
                "density", "population", "income", "vehicles",
                "household_type", "day_purpose",
            ):
                if any(dimension not in sample.attributes for sample in samples):
                    raise ValueError(f"Missing subgroup attribute {dimension}")
                raw = [sample.attributes[dimension].astype(str) for sample in samples]
                eligible = [
                    labels != "unknown" if dimension == "population"
                    else np.ones(len(labels), dtype=bool)
                    for labels in raw
                ]
                matrices = [
                    np.column_stack((sample.days.mode[mask], labels[mask]))
                    for sample, labels, mask in zip(samples, raw, eligible, strict=True)
                ]
                if all(len(matrix) for matrix in matrices):
                    mapping = groupings.merge_cells(
                        matrices[0], samples[0].days.day[eligible[0]],
                        matrices[1], samples[1].days.day[eligible[1]],
                        dimensions=("mode", dimension), config=merge_config,
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
                    draws_a, draws_b, selected=selected, minimum_n=minimum_n,
                    caution_n=caution_n, margins=margins,
                )
                excluded = [
                    float(sample.days.weight[~mask].sum() / sample.days.weight.sum())
                    if len(sample.days.weight) else np.nan
                    for sample, mask in zip(samples, eligible, strict=True)
                ]
                for row in estimates:
                    if dimension == "population" and row["cell"] == "unknown":
                        continue
                    row["grouping"] = dimension
                    row["merged_from"] = "+".join(
                        sorted(
                            source[1] for source, target in mapping.items()
                            if target[1] == row["cell"]
                        )
                    ) or row["cell"]
                    row["excluded_population_share_2008"] = excluded[0]
                    row["excluded_population_share_2019"] = excluded[1]
                    rows.append(row)
        return rows


if __name__ == "__main__":
    raise SystemExit("Mode-cell report is not implemented yet.")
