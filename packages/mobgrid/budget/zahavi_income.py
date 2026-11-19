"""Income-supplement calculations for the daily budget (section 9.9)."""

import argparse
import hashlib
import json
import logging
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from shutil import copyfileobj
from types import ModuleType

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
    trip_legs,
)
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr
from mobgrid.budget import zahavi_modes as modes
from mobgrid.budget.zahavi_modes import Draws, Metric

LOGGER = logging.getLogger(__name__)


class IncomeConfig(BaseModel):
    """Input and disclosure settings for the income supplement."""

    model_config = ConfigDict(extra="forbid")

    entd_cars: Path
    caution_cell_n: int = Field(gt=0)
    checkpoint_dir: Path


@dataclass(frozen=True)
class People:
    """Full weekday roster, with weekday-universe weights (section 9.9)."""

    person: np.ndarray
    household: np.ndarray
    income: np.ndarray
    weight: np.ndarray


@dataclass(frozen=True)
class Days:
    """Described weekday records and scoped durations in minutes (section 9.9)."""

    person: np.ndarray
    household: np.ndarray
    income: np.ndarray
    weight: np.ndarray
    minutes: np.ndarray
    is_open: np.ndarray
    has_trips: np.ndarray


@dataclass(frozen=True)
class CachedIncome:
    """Scoped data joined to respondent attributes, section 9.9."""

    people: People
    days: Days
    population: np.ndarray
    density: np.ndarray
    cars: np.ndarray
    weekday: np.ndarray


def _mapped_values(keys: np.ndarray, mapping: dict[str, str], label: str) -> np.ndarray:
    missing = set(keys) - mapping.keys()
    if missing:
        raise ValueError(f"{label} missing for {len(missing)} identifiers")
    return np.array([mapping[key] for key in keys])


def read_cached_income(
    cache: modes_cache.SurveyCache,
    selected: scope_module.Scope,
    *,
    income: dict[str, str],
    density: dict[str, str],
    cars: dict[str, str],
) -> CachedIncome:
    """Join the full roster and described days to cached scoped results."""
    with duckdb.connect() as con:
        p = con.execute(
            """SELECT trim(CAST(ident_ind AS VARCHAR)) AS person,
                      trim(CAST(ident_men AS VARCHAR)) AS household,
                      population_category, weight
               FROM read_parquet(?) ORDER BY person""",
            [str(cache.roster)],
        ).fetchnumpy()
        d = con.execute(
            """WITH weekday AS (
                SELECT day_id, any_value(described_weekday_name) AS weekday
                FROM read_parquet(?) GROUP BY day_id
            )
            SELECT trim(CAST(b.ident_ind AS VARCHAR)) AS person,
                   trim(CAST(b.ident_men AS VARCHAR)) AS household,
                   b.pond_jour AS weight, b.is_round,
                   d.day_id IS NOT NULL AS has_trips,
                   CASE WHEN d.day_id IS NULL THEN 0
                        ELSE d.total_time_min END AS minutes,
                   d.income_quintile AS cached_income, w.weekday
            FROM read_parquet(?) b
            LEFT JOIN read_parquet(?) d ON d.day_id = b.day_id
            LEFT JOIN weekday w ON w.day_id = b.day_id
            ORDER BY b.day_id""",
            [
                str(cache.trips(selected)),
                str(cache.day_base),
                str(cache.days(selected)),
            ],
        ).fetchnumpy()
    p = {key: vr._plain_array(value) for key, value in p.items()}
    d = {
        key: (
            value.filled("")
            if key in {"weekday", "cached_income"}
            and isinstance(value, np.ma.MaskedArray)
            else vr._plain_array(value)
        )
        for key, value in d.items()
    }
    person = vr._text_values(p["person"])
    household = vr._text_values(p["household"])
    people = People(
        person,
        household,
        _mapped_values(person, income, "Income"),
        np.asarray(p["weight"], dtype=float),
    )
    day_person = vr._text_values(d["person"])
    day_income = _mapped_values(day_person, income, "Day income")
    has_trips = np.asarray(d["has_trips"], dtype=bool)
    cached_income = vr._text_values(d["cached_income"])
    if np.any(day_income[has_trips] != cached_income[has_trips]):
        raise ValueError("Reconstructed income differs from scoped cache")
    weekday = vr._text_values(d["weekday"])
    if np.any(has_trips & (weekday == "")):
        LOGGER.warning(
            "%d travel days have missing weekday",
            np.sum(has_trips & (weekday == "")),
        )
        weekday[has_trips & (weekday == "")] = "unknown"
    days = Days(
        day_person,
        vr._text_values(d["household"]),
        day_income,
        np.asarray(d["weight"], dtype=float),
        np.asarray(d["minutes"], dtype=float),
        ~np.asarray(d["is_round"], dtype=bool)
        if selected.days == "round"
        else np.zeros(len(day_person), dtype=bool),
        has_trips,
    )
    return CachedIncome(
        people,
        days,
        vr._text_values(p["population_category"]),
        _mapped_values(person, density, "Residence density"),
        _mapped_values(household, cars, "Household car count"),
        weekday,
    )


def _household_indices(households: np.ndarray, universe: np.ndarray) -> np.ndarray:
    indices = np.searchsorted(universe, households)
    if np.any(indices >= len(universe)) or np.any(universe[indices] != households):
        raise ValueError("Household outside bootstrap universe")
    return indices


def _component_metric(
    numerator: np.ndarray, denominator: np.ndarray, multipliers: np.ndarray
) -> Metric:
    total = denominator.sum()
    value = float(numerator.sum() / total) if total > 0 else float("nan")
    draw_denominator = multipliers @ denominator
    replicates = np.divide(
        multipliers @ numerator,
        draw_denominator,
        out=np.full(len(multipliers), np.nan),
        where=draw_denominator > 0,
    )
    return Metric(value, replicates)


def income_metrics(
    people: People,
    days: Days,
    draws: Draws,
    *,
    groups: tuple[str, ...] = trip_legs.INCOME_QUINTILE_LABELS,
) -> dict[tuple[str, str], tuple[int, Metric]]:
    """Estimate minutes per travel day and per person with paired draws, section 9.9."""
    if not (
        len(people.person)
        == len(people.household)
        == len(people.income)
        == len(people.weight)
        and len(days.person)
        == len(days.household)
        == len(days.income)
        == len(days.weight)
        == len(days.minutes)
        == len(days.is_open)
        == len(days.has_trips)
    ):
        raise ValueError("Income sample arrays must have matching lengths")
    if (
        not np.isfinite(people.weight).all()
        or np.any(people.weight <= 0)
        or not np.isfinite(days.weight).all()
        or np.any(days.weight <= 0)
        or not np.isfinite(days.minutes).all()
        or np.any(days.minutes < 0)
        or days.is_open.dtype != np.dtype(bool)
        or days.has_trips.dtype != np.dtype(bool)
        or np.any((~days.is_open) & (~days.has_trips) & (days.minutes != 0))
    ):
        raise ValueError("Invalid income sample weights or day values")
    order = np.argsort(people.person)
    roster = people.person[order]
    if len(np.unique(roster)) != len(roster):
        raise ValueError("Duplicate respondent in income roster")
    idx = np.searchsorted(roster, days.person)
    if np.any(idx >= len(roster)) or np.any(roster[idx] != days.person):
        raise ValueError("Day respondent outside income roster")
    if np.any(people.household[order][idx] != days.household) or np.any(
        people.income[order][idx] != days.income
    ):
        raise ValueError("Day attributes disagree with income roster")
    ph = _household_indices(people.household, draws.households)
    dh = _household_indices(days.household, draws.households)
    if draws.multipliers.ndim != 2 or draws.multipliers.shape[1] != len(
        draws.households
    ):
        raise ValueError("Invalid bootstrap multiplier matrix")
    n_households = len(draws.households)
    result: dict[tuple[str, str], tuple[int, Metric]] = {}
    for quintile in groups:
        p = people.income == quintile
        d = days.income == quintile
        travel = d & ~days.is_open & days.has_trips
        opened = d & days.is_open
        numerator = np.bincount(
            dh[travel],
            weights=days.weight[travel] * days.minutes[travel],
            minlength=n_households,
        )
        travel_weight = np.bincount(
            dh[travel], weights=days.weight[travel], minlength=n_households
        )
        roster_weight = np.bincount(
            ph[p], weights=people.weight[p], minlength=n_households
        )
        open_weight = np.bincount(
            dh[opened], weights=days.weight[opened], minlength=n_households
        )
        result["travel_day", quintile] = (
            len(np.unique(days.person[travel])),
            _component_metric(numerator, travel_weight, draws.multipliers),
        )
        result["person", quintile] = (
            int(p.sum()),
            _component_metric(
                numerator, roster_weight - open_weight, draws.multipliers
            ),
        )
    return result


def level_rows(
    metrics_a: dict[tuple[str, str], tuple[int, Metric]],
    metrics_b: dict[tuple[str, str], tuple[int, Metric]],
    *,
    minimum_n: int,
    margins: tuple[float, float],
    groups: tuple[str, ...] = trip_legs.INCOME_QUINTILE_LABELS,
) -> list[dict]:
    """Report mean minutes and 2019/2008 ratios, section 9.9."""
    rows = []
    for basis in ("travel_day", "person"):
        for quintile in groups:
            row: dict = {
                "basis": basis,
                "quintile": quintile,
                "n_2008": 0,
                "n_2019": 0,
                "mean_2008": np.nan,
                "mean_2019": np.nan,
                "ci_2008_low": np.nan,
                "ci_2008_high": np.nan,
                "ci_2019_low": np.nan,
                "ci_2019_high": np.nan,
                "ratio": np.nan,
                "ratio_ci_low": np.nan,
                "ratio_ci_high": np.nan,
                "verdict_15": "",
                "verdict_10": "",
            }
            estimates = []
            for year, source in ((2008, metrics_a), (2019, metrics_b)):
                entry = source.get((basis, quintile))
                if entry is None or (
                    year == 2019 and quintile.split("|", 1)[0] == "unknown"
                ):
                    estimates.append(None)
                    continue
                n, metric = entry
                row[f"n_{year}"] = n
                estimates.append(metric if n >= minimum_n else None)
                if n >= minimum_n:
                    row[f"mean_{year}"] = metric.value
                    low, high = modes._interval(metric.replicates)
                    row[f"ci_{year}_low"], row[f"ci_{year}_high"] = low, high
            a, b = estimates
            if a is not None and b is not None and a.value > 0 and b.value > 0:
                if a.replicates.shape != b.replicates.shape:
                    raise ValueError("Ratio replicate arrays must have matching shapes")
                row["ratio"] = b.value / a.value
                valid = np.isfinite(a.replicates) & np.isfinite(b.replicates)
                valid &= a.replicates > 0
                ratio_draws = np.divide(
                    b.replicates,
                    a.replicates,
                    out=np.full_like(a.replicates, np.nan, dtype=float),
                    where=valid,
                )
                if np.isfinite(modes._interval(ratio_draws)[0]):
                    ratio, (low, high) = daily_energy.bootstrap_replicate_ratio_ci(
                        a.value, a.replicates[valid], b.value, b.replicates[valid]
                    )
                    row.update(
                        ratio=ratio,
                        ratio_ci_low=low,
                        ratio_ci_high=high,
                        verdict_15=vr._equivalence_verdict((low, high), margins[0]),
                        verdict_10=vr._equivalence_verdict((low, high), margins[1]),
                    )
            rows.append(row)
    return rows


def density_rows(
    a: CachedIncome,
    b: CachedIncome,
    draws_a: Draws,
    draws_b: Draws,
    *,
    minimum_n: int,
    caution_n: int,
    margins: tuple[float, float],
) -> list[dict]:
    """Income-by-proxy-density levels and ratios, section 9.9."""
    densities = sorted(set(a.density) | set(b.density))
    groups = tuple(
        f"{quintile}|{density}"
        for quintile in trip_legs.INCOME_QUINTILE_LABELS
        for density in densities
    )
    results = []
    for sample, draws in ((a, draws_a), (b, draws_b)):
        if len(sample.density) != len(sample.people.person):
            raise ValueError("Density and respondent lengths differ")
        order = np.argsort(sample.people.person)
        roster = sample.people.person[order]
        indices = np.searchsorted(roster, sample.days.person)
        if np.any(indices >= len(roster)) or np.any(
            roster[indices] != sample.days.person
        ):
            raise ValueError("Day respondent outside density roster")
        day_density = sample.density[order][indices]
        person_group = np.char.add(
            np.char.add(sample.people.income.astype(str), "|"),
            sample.density.astype(str),
        )
        day_group = np.char.add(
            np.char.add(sample.days.income.astype(str), "|"), day_density.astype(str)
        )
        results.append(
            income_metrics(
                replace(sample.people, income=person_group),
                replace(sample.days, income=day_group),
                draws,
                groups=groups,
            )
        )
    rows = level_rows(
        results[0], results[1], minimum_n=minimum_n, margins=margins, groups=groups
    )
    for row in rows:
        row["quintile"], row["density"] = row["quintile"].split("|", 1)
        counts = [row["n_2008"]]
        if row["quintile"] != "unknown":
            counts.append(row["n_2019"])
        row["small_cell"] = min(counts) < caution_n
    return rows


def load_entd_household_cars(source: Path, scratch: Path) -> dict[str, str]:
    """Load ENTD household car-count bands from CP1252, section 9.9."""
    scratch.mkdir(parents=True, exist_ok=True)
    encoded = scratch / source.name
    with (
        source.open(encoding="cp1252") as inp,
        encoded.open("w", encoding="utf-8", newline="") as out,
    ):
        copyfileobj(inp, out)
    with duckdb.connect() as con:
        con.execute(
            """CREATE TEMP TABLE cars AS SELECT
                trim(idENT_MEN) AS ident_men, V1_JNBVEH AS count_text
            FROM read_csv(?, delim=';', nullstr='',
                types={'idENT_MEN': 'VARCHAR', 'V1_JNBVEH': 'VARCHAR'})""",
            [str(encoded)],
        )
        return _cars_from_view(con)


def emp_household_cars(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Read EMP 2019 household car-count bands, section 9.9."""
    con.execute(
        """CREATE OR REPLACE TEMP VIEW cars AS SELECT
            trim(CAST(IDENT_MEN AS VARCHAR)) AS ident_men,
            CAST(JNBVEH AS VARCHAR) AS count_text FROM q_menage"""
    )
    return _cars_from_view(con)


def _cars_from_view(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    duplicates = con.execute(
        """SELECT ident_men FROM cars GROUP BY ident_men
               HAVING ident_men IS NULL OR ident_men = '' OR count(*) > 1 LIMIT 1"""
    ).fetchone()
    if duplicates:
        raise ValueError(f"Duplicate or empty household ID: {duplicates[0]!r}")
    invalid = con.execute(
        """SELECT count_text FROM cars WHERE count_text IS NOT NULL AND
               (NOT regexp_full_match(trim(count_text), '[0-9]+') OR
                TRY_CAST(count_text AS INTEGER) IS NULL) LIMIT 1"""
    ).fetchone()
    if invalid:
        raise ValueError(f"Invalid household car count: {invalid[0]!r}")
    rows = con.execute(
        """SELECT ident_men, CASE
                WHEN count_text IS NULL THEN 'unknown'
                WHEN CAST(count_text AS INTEGER) = 0 THEN '0'
                WHEN CAST(count_text AS INTEGER) = 1 THEN '1'
                ELSE '2+' END
               FROM cars"""
    ).fetchall()
    return dict(rows)


def income_by_person(
    con: duckdb.DuckDBPyConnection, survey: ModuleType
) -> dict[str, str]:
    """Rebuild the survey's existing individual-weighted income classes, section 9.9."""
    survey.build_respondent_income(con)
    rows = con.execute(
        "SELECT ident_ind, income_quintile FROM respondent_income"
    ).fetchall()
    result: dict[str, str] = {}
    for ident, quintile in rows:
        if ident is None or quintile not in {"q1", "q2", "q3", "q4", "q5", "unknown"}:
            raise ValueError("Invalid respondent income row")
        key = str(ident).strip()
        if not key or key in result:
            raise ValueError(f"Duplicate or empty respondent identifier: {key!r}")
        result[key] = quintile
    return result


def respondent_attributes(
    con: duckdb.DuckDBPyConnection, survey: ModuleType
) -> tuple[dict[str, str], dict[str, str]]:
    """Reuse survey income assignments and the common residence proxy."""
    income = income_by_person(con, survey)
    if survey is emp2019 and "unknown" in income.values():
        raise ValueError("EMP 2019 contains unexpected missing imputed income")
    raw_density = survey.residence_density_by_ident(con, "proxy")
    density: dict[str, str] = {}
    for ident, value in raw_density.items():
        key = str(ident).strip()
        if not key or key in density or value is None:
            raise ValueError(f"Invalid residence density for respondent {key!r}")
        density[key] = str(value)
    return income, density


def extract_attributes(
    survey: ModuleType,
    source: Path,
    scratch: Path,
    *,
    entd_cars: Path | None = None,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Extract survey attributes in temporary storage without modifying caches."""
    if survey not in (emp2019, entd2008):
        raise ValueError(f"Unsupported survey: {survey.__name__}")
    if survey is entd2008 and entd_cars is None:
        raise ValueError("ENTD household car source is required")
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        temp_path = Path(temporary)
        paths = survey.extract_tables(source, temp_path / "tables")
        with duckdb.connect() as con:
            survey.register_views(con, paths)
            income, density = respondent_attributes(con, survey)
            if survey is emp2019:
                cars = emp_household_cars(con)
            else:
                if entd_cars is None:
                    raise ValueError("ENTD household car source is required")
                cars = load_entd_household_cars(entd_cars, temp_path / "cars")
    return income, density, cars


def unknown_income_shares(
    respondent_income: np.ndarray, day_income: np.ndarray, day_weight: np.ndarray
) -> tuple[float, float]:
    """Return unknown-income respondent and described-day-weight shares, section 9.9."""
    if len(day_income) != len(day_weight):
        raise ValueError("Day income and weight lengths differ")
    if not len(respondent_income):
        raise ValueError("Empty respondent roster")
    if not np.all(np.isfinite(day_weight)) or np.any(day_weight < 0):
        raise ValueError("Invalid day weights")
    if day_weight.sum() <= 0:
        raise ValueError("No positive day weight")
    return (
        float(np.mean(respondent_income == "unknown")),
        float(day_weight[day_income == "unknown"].sum() / day_weight.sum()),
    )


def gap_change(q1_a: Metric, q5_a: Metric, q1_b: Metric, q5_b: Metric) -> Metric:
    """Change in Q5 minus Q1, in minutes; draw indices remain paired (section 9.9)."""
    shapes = {metric.replicates.shape for metric in (q1_a, q5_a, q1_b, q5_b)}
    if len(shapes) != 1 or q1_a.replicates.ndim != 1:
        raise ValueError("Bootstrap replicate arrays must have matching shapes")
    return Metric(
        (q5_b.value - q1_b.value) - (q5_a.value - q1_a.value),
        (q5_b.replicates - q1_b.replicates) - (q5_a.replicates - q1_a.replicates),
    )


def gap_rows(
    metrics_a: dict[tuple[str, str], tuple[int, Metric]],
    metrics_b: dict[tuple[str, str], tuple[int, Metric]],
    *,
    minimum_n: int,
) -> list[dict]:
    """Report within-year income gaps and paired changes, section 9.9."""
    rows = []
    for basis in ("travel_day", "person"):
        for kind in ("difference", "ratio"):
            row: dict = {"basis": basis, "gap": kind}
            values: list[Metric | None] = []
            for year, source in ((2008, metrics_a), (2019, metrics_b)):
                q1, q5 = source.get((basis, "q1")), source.get((basis, "q5"))
                metric = None
                if (
                    q1 is not None
                    and q5 is not None
                    and min(q1[0], q5[0]) >= minimum_n
                    and q1[1].replicates.shape == q5[1].replicates.shape
                ):
                    if kind == "difference":
                        metric = Metric(
                            q5[1].value - q1[1].value,
                            q5[1].replicates - q1[1].replicates,
                        )
                    elif q1[1].value > 0:
                        with np.errstate(divide="ignore", invalid="ignore"):
                            metric = Metric(
                                q5[1].value / q1[1].value,
                                q5[1].replicates / q1[1].replicates,
                            )
                values.append(metric)
                row[f"value_{year}"] = metric.value if metric else np.nan
                low, high = (
                    modes._interval(metric.replicates) if metric else (np.nan, np.nan)
                )
                row[f"ci_{year}_low"], row[f"ci_{year}_high"] = low, high
            a, b = values
            row["change"] = row["change_ci_low"] = row["change_ci_high"] = np.nan
            if a is not None and b is not None:
                if a.replicates.shape != b.replicates.shape:
                    raise ValueError("Gap replicate arrays must have matching shapes")
                row["change"] = b.value - a.value
                row["change_ci_low"], row["change_ci_high"] = modes._interval(
                    b.replicates - a.replicates
                )
            rows.append(row)
    return rows


def collapse_joint_cells(
    cells_a: np.ndarray,
    cells_b: np.ndarray,
    *,
    supported_a: np.ndarray | None = None,
    supported_b: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, str]]]:
    """Collapse unsupported density/car cells within quintiles, section 9.9.

    Pool car categories within a density class when necessary. If a
    density class is absent from one year, pool density and cars within
    that quintile. A quintile missing in one year cannot be compared.
    """
    for cells in (cells_a, cells_b):
        if cells.ndim != 2 or cells.shape[1] != 3 or len(cells) == 0:
            raise ValueError("Joint cells must be a nonempty three-column array")
        if np.any(cells == "") or np.any(np.char.find(cells.astype(str), "|") >= 0):
            raise ValueError("Invalid joint-cell labels")
    if supported_a is None:
        supported_a = np.ones(len(cells_a), dtype=bool)
    if supported_b is None:
        supported_b = np.ones(len(cells_b), dtype=bool)
    if supported_a.shape != (len(cells_a),) or supported_b.shape != (len(cells_b),):
        raise ValueError("Joint-cell support masks must match the input rows")
    all_cells = {
        tuple(row)
        for row in np.unique(np.concatenate((cells_a, cells_b)).astype(str), axis=0)
    }
    unique_a = {
        tuple(row) for row in np.unique(cells_a[supported_a].astype(str), axis=0)
    }
    unique_b = {
        tuple(row) for row in np.unique(cells_b[supported_b].astype(str), axis=0)
    }
    quintiles_a = {cell[0] for cell in unique_a}
    quintiles_b = {cell[0] for cell in unique_b}
    if quintiles_a != quintiles_b:
        raise ValueError("A quintile lacks common survey support")
    mapping: dict[tuple[str, ...], str] = {}
    for quintile in sorted(quintiles_a):
        a = {cell for cell in unique_a if cell[0] == quintile}
        b = {cell for cell in unique_b if cell[0] == quintile}
        all_q = {cell for cell in all_cells if cell[0] == quintile}
        density_a = {cell[1] for cell in a}
        density_b = {cell[1] for cell in b}
        if density_a != density_b or density_a != {cell[1] for cell in all_q}:
            mapping.update({cell: f"{quintile}|all|all" for cell in all_q})
            continue
        for density in sorted(density_a):
            aa = {cell for cell in a if cell[1] == density}
            bb = {cell for cell in b if cell[1] == density}
            all_d = {cell for cell in all_q if cell[1] == density}
            if aa != bb or aa != all_d:
                mapping.update({cell: f"{quintile}|{density}|all" for cell in all_d})
            else:
                mapping.update({cell: "|".join(cell) for cell in aa})
    if any(cell not in mapping for cell in all_cells):
        raise ValueError("A quintile lacks positive survey support")
    combined = np.concatenate((cells_a, cells_b)).astype(str)
    unique, inverse = np.unique(combined, axis=0, return_inverse=True)
    mapped = np.array([mapping[tuple(row)] for row in unique])[inverse]
    collapsed = sorted(
        ("|".join(cell), target)
        for cell, target in mapping.items()
        if "|".join(cell) != target
    )
    return mapped[: len(cells_a)], mapped[len(cells_a) :], collapsed


def pooled_reweight(
    cells_a: np.ndarray,
    weights_a: np.ndarray,
    cells_b: np.ndarray,
    weights_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Standardise each survey to the mean joint-cell distribution, section 9.9.

    Cell codes must be shared non-negative integers. Cells with no support in
    either year must be collapsed before calling this function.
    """
    for cells, weights in ((cells_a, weights_a), (cells_b, weights_b)):
        if (
            cells.ndim != 1
            or weights.ndim != 1
            or len(cells) != len(weights)
            or not len(cells)
            or not np.issubdtype(cells.dtype, np.integer)
            or np.any(cells < 0)
            or not np.all(np.isfinite(weights))
            or np.any(weights < 0)
            or weights.sum() <= 0
        ):
            raise ValueError("Invalid joint cells or weights")
    size = int(max(cells_a.max(), cells_b.max())) + 1
    totals_a = np.bincount(cells_a, weights=weights_a, minlength=size)
    totals_b = np.bincount(cells_b, weights=weights_b, minlength=size)
    shares_a = totals_a / totals_a.sum()
    shares_b = totals_b / totals_b.sum()
    if np.any((shares_a == 0) != (shares_b == 0)):
        raise ValueError("Joint cells lack common support; collapse them first")
    target = (shares_a + shares_b) / 2
    factor_a = np.divide(
        target, shares_a, out=np.zeros_like(target), where=shares_a > 0
    )
    factor_b = np.divide(
        target, shares_b, out=np.zeros_like(target), where=shares_b > 0
    )
    return weights_a * factor_a[cells_a], weights_b * factor_b[cells_b], target


def reweighted_metrics(
    a: CachedIncome,
    b: CachedIncome,
    draws_a: Draws,
    draws_b: Draws,
) -> tuple[
    dict[tuple[str, str], tuple[int, Metric]],
    dict[tuple[str, str], tuple[int, Metric]],
    list[tuple[str, str, str]],
]:
    """Re-estimate minutes under pooled joint mixes with shared draws, section 9.9."""
    if len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("Both surveys require the same number of bootstrap draws")
    outputs: list[dict[tuple[str, str], tuple[int, Metric]]] = [{}, {}]
    collapsed_rows: list[tuple[str, str, str]] = []
    quintiles = tuple(x for x in trip_legs.INCOME_QUINTILE_LABELS if x != "unknown")
    for basis in ("travel_day", "person"):
        prepared = []
        for sample, draws in ((a, draws_a), (b, draws_b)):
            people, days = sample.people, sample.days
            order = np.argsort(people.person)
            roster = people.person[order]
            idx = np.searchsorted(roster, days.person)
            if np.any(idx >= len(roster)) or np.any(roster[idx] != days.person):
                raise ValueError("Day respondent outside reweighting roster")
            day_index = order[idx]
            known_p = np.isin(people.income, quintiles)
            known_d = np.isin(days.income, quintiles)
            travel = known_d & ~days.is_open & days.has_trips
            opened = known_d & days.is_open
            pcells = np.column_stack((people.income, sample.density, sample.cars))
            dcells = pcells[day_index]
            support = pcells[known_p] if basis == "person" else dcells[travel]
            if basis == "person":
                effective_weight = people.weight.copy()
                np.add.at(effective_weight, day_index[opened], -days.weight[opened])
                _, inverse = np.unique(support, axis=0, return_inverse=True)
                totals = np.bincount(inverse, weights=effective_weight[known_p])
                if np.any(totals < 0):
                    raise ValueError("A person cell has negative net day weight")
                supported = totals[inverse] > 0
            else:
                supported = np.ones(len(support), dtype=bool)
            prepared.append(
                (
                    sample,
                    draws,
                    known_p,
                    travel,
                    opened,
                    pcells,
                    dcells,
                    support,
                    supported,
                )
            )
        mapped_a, mapped_b, collapsed = collapse_joint_cells(
            prepared[0][7],
            prepared[1][7],
            supported_a=prepared[0][8],
            supported_b=prepared[1][8],
        )
        collapsed_rows.extend((basis, src, dest) for src, dest in collapsed)
        labels = np.unique(np.concatenate((mapped_a, mapped_b)))
        joint_codes = []
        for prepared_sample, mapped in zip(prepared, (mapped_a, mapped_b), strict=True):
            sample, draws, known_p, travel, opened, pcells, dcells, support, _ = (
                prepared_sample
            )
            original, inverse = np.unique(support, axis=0, return_inverse=True)
            target_by_original = np.empty(len(original), dtype=object)
            target_by_original[inverse] = mapped
            mapping = {
                tuple(cell): target
                for cell, target in zip(original, target_by_original, strict=True)
            }
            if basis == "person":
                person_labels = np.array(
                    [mapping[tuple(row)] for row in pcells[known_p]]
                )
                day_labels = np.array(
                    [mapping[tuple(row)] for row in dcells[travel | opened]]
                )
                person_codes = np.searchsorted(labels, person_labels)
                day_codes = np.searchsorted(labels, day_labels)
            else:
                person_codes = np.array([], dtype=int)
                day_codes = np.searchsorted(labels, mapped)
            ph = _household_indices(sample.people.household, draws.households)
            dh = _household_indices(sample.days.household, draws.households)
            joint_codes.append((person_codes, day_codes, ph, dh))
        groups = np.array([label.split("|", 1)[0] for label in labels])
        values = [
            {q: np.full(len(draws_a.multipliers) + 1, np.nan) for q in quintiles}
            for _ in range(2)
        ]
        invalid = 0
        for rep in range(-1, len(draws_a.multipliers)):
            components = []
            for item, codes in zip(prepared, joint_codes, strict=True):
                sample, draws, known_p, travel, opened, _, _, _, _ = item
                pcodes, dcodes, ph, dh = codes
                mult = (
                    np.ones(len(draws.households))
                    if rep < 0
                    else draws.multipliers[rep]
                )
                day_mask = travel | opened if basis == "person" else travel
                day_weight = sample.days.weight[day_mask] * mult[dh[day_mask]]
                numerator = np.bincount(
                    dcodes,
                    weights=day_weight
                    * np.where(
                        sample.days.is_open[day_mask], 0, sample.days.minutes[day_mask]
                    ),
                    minlength=len(labels),
                )
                if basis == "person":
                    denominator = np.bincount(
                        pcodes,
                        weights=sample.people.weight[known_p] * mult[ph[known_p]],
                        minlength=len(labels),
                    ) - np.bincount(
                        dcodes,
                        weights=day_weight * sample.days.is_open[day_mask],
                        minlength=len(labels),
                    )
                else:
                    denominator = np.bincount(
                        dcodes, weights=day_weight, minlength=len(labels)
                    )
                components.append((numerator, denominator))
            denominator_a, denominator_b = components[0][1], components[1][1]
            if (
                np.any(denominator_a < 0)
                or np.any(denominator_b < 0)
                or denominator_a.sum() <= 0
                or denominator_b.sum() <= 0
                or np.any((denominator_a == 0) != (denominator_b == 0))
            ):
                if rep < 0:
                    raise ValueError(
                        "Collapsed cells do not have positive common support"
                    )
                invalid += 1
                continue
            shares = [
                denominator_a / denominator_a.sum(),
                denominator_b / denominator_b.sum(),
            ]
            target = (shares[0] + shares[1]) / 2
            for year in range(2):
                factors = np.divide(
                    target,
                    shares[year],
                    out=np.zeros_like(target),
                    where=shares[year] > 0,
                )
                numerator, denominator = components[year]
                for quintile in quintiles:
                    mask = groups == quintile
                    total = np.sum(denominator[mask] * factors[mask])
                    if total > 0:
                        values[year][quintile][rep + 1] = (
                            np.sum(numerator[mask] * factors[mask]) / total
                        )
        if invalid:
            LOGGER.warning("%s: %d reweighting draws lack support", basis, invalid)
        for year, item in enumerate(prepared):
            sample, _, known_p, travel, _, _, _, _, _ = item
            for quintile in quintiles:
                n = (
                    int(np.sum(known_p & (sample.people.income == quintile)))
                    if basis == "person"
                    else len(
                        np.unique(
                            sample.days.person[
                                travel & (sample.days.income == quintile)
                            ]
                        )
                    )
                )
                outputs[year][basis, quintile] = (
                    n,
                    Metric(values[year][quintile][0], values[year][quintile][1:]),
                )
    return outputs[0], outputs[1], collapsed_rows


def weighted_least_squares(
    design: np.ndarray, outcome: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    """Fit day-weighted least squares for log minutes, section 9.9."""
    if (
        design.ndim != 2
        or outcome.ndim != 1
        or weights.ndim != 1
        or len(design) != len(outcome)
        or len(outcome) != len(weights)
        or not np.all(np.isfinite(design))
        or not np.all(np.isfinite(outcome))
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
    ):
        raise ValueError("Invalid weighted regression inputs")
    root = np.sqrt(weights)
    coefficients, _, rank, _ = np.linalg.lstsq(
        design * root[:, None], outcome * root, rcond=None
    )
    if rank != design.shape[1]:
        raise ValueError("Weighted regression design is rank deficient")
    return coefficients


def regression_design(
    *,
    income: np.ndarray,
    population: np.ndarray,
    weekday: np.ndarray,
    density: np.ndarray | None = None,
    cars: np.ndarray | None = None,
    survey: np.ndarray | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Build reference-coded WLS predictors for section 9.9's income models."""
    variables = [income, population, weekday]
    variables += [x for x in (density, cars, survey) if x is not None]
    if not len(income) or any(x.ndim != 1 or len(x) != len(income) for x in variables):
        raise ValueError("Regression predictors must be nonempty matching arrays")
    if any(np.any(x == "") for x in variables) or not np.any(income == "q1"):
        raise ValueError("Regression requires nonblank predictors and Q1")
    names = ["intercept"]
    columns = [np.ones(len(income), dtype=float)]
    income_levels = [str(x) for x in np.unique(income) if x != "q1"]
    for level in income_levels:
        names.append(f"income:{level}")
        columns.append((income == level).astype(float))
    for name, predictor in (
        ("population", population),
        ("weekday", weekday),
        ("density", density),
        ("cars", cars),
    ):
        if predictor is None:
            continue
        levels = np.unique(predictor)
        for level in levels[1:]:
            names.append(f"{name}:{level}")
            columns.append((predictor == level).astype(float))
    if survey is not None:
        if set(np.unique(survey)) != {"2008", "2019"}:
            raise ValueError("Pooled regression requires both survey years")
        is_2019 = survey == "2019"
        names.append("survey:2019")
        columns.append(is_2019.astype(float))
        for level in income_levels:
            if np.any(is_2019 & (income == level)):
                names.append(f"survey:2019*income:{level}")
                columns.append((is_2019 & (income == level)).astype(float))
    return np.column_stack(columns), names


def bootstrap_wls(
    design: np.ndarray,
    outcome: np.ndarray,
    weights: np.ndarray,
    households: np.ndarray,
    draws: Draws,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit WLS and shared household-bootstrap coefficients, section 9.9."""
    if len(households) != len(weights):
        raise ValueError("Regression households and weights differ in length")
    point = weighted_least_squares(design, outcome, weights)
    indices = _household_indices(households, draws.households)
    if (
        draws.multipliers.ndim != 2
        or draws.multipliers.shape[1] != len(draws.households)
        or np.any(draws.multipliers < 0)
    ):
        raise ValueError("Invalid bootstrap multiplier matrix")
    replicates = np.full((len(draws.multipliers), design.shape[1]), np.nan)
    invalid = 0
    for rep, multiplier in enumerate(draws.multipliers):
        root = np.sqrt(weights * multiplier[indices])
        coef, _, rank, _ = np.linalg.lstsq(
            design * root[:, None], outcome * root, rcond=None
        )
        if rank == design.shape[1]:
            replicates[rep] = coef
        else:
            invalid += 1
    if invalid:
        LOGGER.warning("%d bootstrap regression draws are rank deficient", invalid)
    return point, replicates


def regression_effects(
    design: np.ndarray,
    names: list[str],
    outcome: np.ndarray,
    weights: np.ndarray,
    households: np.ndarray,
    draws: Draws,
) -> list[dict]:
    """Return income and interaction coefficients as percentage effects."""
    if len(names) != design.shape[1] or len(set(names)) != len(names):
        raise ValueError("Regression column names must be distinct and match design")
    point, replicates = bootstrap_wls(design, outcome, weights, households, draws)
    rows = []
    for column, term in enumerate(names):
        if not (term.startswith("income:") or term.startswith("survey:2019*income:")):
            continue
        with np.errstate(over="ignore", invalid="ignore"):
            effect = float(100 * np.expm1(point[column]))
            samples = 100 * np.expm1(replicates[:, column])
        if not np.isfinite(effect):
            LOGGER.warning("Nonfinite regression effect for %s", term)
        low, high = modes._interval(samples)
        rows.append({"term": term, "percent": effect, "ci_low": low, "ci_high": high})
    return rows


def _regression_sample(sample: CachedIncome) -> dict[str, np.ndarray]:
    people, days = sample.people, sample.days
    order = np.argsort(people.person)
    roster = people.person[order]
    indices = np.searchsorted(roster, days.person)
    if np.any(indices >= len(roster)) or np.any(roster[indices] != days.person):
        raise ValueError("Regression day respondent outside roster")
    person_index = order[indices]
    valid = (
        days.has_trips & ~days.is_open & np.isfinite(days.minutes) & (days.minutes > 0)
    )
    excluded = days.has_trips & ~days.is_open & ~valid
    if excluded.any():
        LOGGER.warning(
            "Excluded %d travel days with nonpositive or invalid minutes from log WLS",
            int(excluded.sum()),
        )
    return {
        "person": days.person[valid],
        "household": days.household[valid],
        "income": days.income[valid],
        "population": sample.population[person_index][valid],
        "density": sample.density[person_index][valid],
        "cars": sample.cars[person_index][valid],
        "weekday": sample.weekday[valid],
        "weight": days.weight[valid],
        "outcome": np.log(days.minutes[valid]),
    }


def regression_rows(
    a: CachedIncome,
    b: CachedIncome,
    draws_a: Draws,
    draws_b: Draws,
    *,
    minimum_n: int,
) -> list[dict]:
    """Fit M0, M1, M2 and pooled interaction WLS with shared household draws."""
    if len(draws_a.multipliers) != len(draws_b.multipliers):
        raise ValueError("Both surveys require the same number of bootstrap draws")
    samples = [_regression_sample(a), _regression_sample(b)]
    counts = [
        {
            q: len(np.unique(sample["person"][sample["income"] == q]))
            for q in trip_legs.INCOME_QUINTILE_LABELS
        }
        for sample in samples
    ]
    pooled = {key: np.concatenate([s[key] for s in samples]) for key in samples[0]}
    pooled["household"] = np.concatenate(
        [
            np.char.add("2008|", samples[0]["household"].astype(str)),
            np.char.add("2019|", samples[1]["household"].astype(str)),
        ]
    )
    pooled["survey"] = np.concatenate(
        [
            np.full(len(samples[0]["income"]), "2008"),
            np.full(len(samples[1]["income"]), "2019"),
        ]
    )
    pooled_draws = Draws(
        np.concatenate(
            [
                np.char.add("2008|", draws_a.households.astype(str)),
                np.char.add("2019|", draws_b.households.astype(str)),
            ]
        ),
        np.concatenate([draws_a.multipliers, draws_b.multipliers], axis=1),
        draws_a.seed,
    )
    rows = []
    jobs = [
        (str(year), model, sample, draws, level)
        for year, sample, draws in (
            (2008, samples[0], draws_a),
            (2019, samples[1], draws_b),
        )
        for model, level in (("M0", 0), ("M1", 1), ("M2", 2))
    ]
    jobs.append(("pooled", "pooled", pooled, pooled_draws, 2))
    for year, model, sample, draws, level in jobs:
        design, names = regression_design(
            income=sample["income"],
            population=sample["population"],
            weekday=sample["weekday"],
            density=sample["density"] if level >= 1 else None,
            cars=sample["cars"] if level >= 2 else None,
            survey=sample.get("survey"),
        )
        effects = regression_effects(
            design,
            names,
            sample["outcome"],
            sample["weight"],
            sample["household"],
            draws,
        )
        effects.insert(
            0, {"term": "income:q1", "percent": 0.0, "ci_low": 0.0, "ci_high": 0.0}
        )
        for effect in effects:
            quintile = effect["term"].rsplit(":", 1)[-1]
            year_indices = (
                (0, 1) if year == "pooled" else ((0,) if year == "2008" else (1,))
            )
            ns = [min(counts[i]["q1"], counts[i][quintile]) for i in year_indices]
            if min(ns) < minimum_n:
                effect["percent"] = effect["ci_low"] = effect["ci_high"] = np.nan
            effect.update(
                year=year,
                model=model,
                n_2008=counts[0].get(quintile, 0) if year != "2019" else 0,
                n_2019=counts[1].get(quintile, 0) if year != "2008" else 0,
            )
            rows.append(effect)
    return rows


def _conclusion_rows(
    levels: list[dict],
    gaps: list[dict],
    adjusted_gaps: list[dict],
    regressions: list[dict],
) -> list[dict]:
    result = []
    for basis in ("travel_day", "person"):
        raw = next(
            row for row in gaps if row["basis"] == basis and row["gap"] == "ratio"
        )
        adjusted = next(
            row
            for row in adjusted_gaps
            if row["basis"] == basis and row["gap"] == "ratio"
        )
        for quintile in trip_legs.INCOME_QUINTILE_LABELS[:5]:
            level = next(
                row
                for row in levels
                if row["basis"] == basis and row["quintile"] == quintile
            )
            row: dict = {
                "basis": basis,
                "quintile": quintile,
                "ratio": level["ratio"],
                "verdict_15": level["verdict_15"],
            }
            for year in (2008, 2019):
                row[f"raw_q5_q1_{year}"] = raw[f"value_{year}"]
                row[f"reweighted_q5_q1_{year}"] = adjusted[f"value_{year}"]
                m2 = next(
                    (
                        item
                        for item in regressions
                        if item["year"] == str(year)
                        and item["model"] == "M2"
                        and item["term"] == "income:q5"
                    ),
                    None,
                )
                row[f"m2_q5_q1_{year}"] = (
                    1 + m2["percent"] / 100 if m2 is not None else np.nan
                )
            result.append(row)
    return result


def _gradient_statement(regressions: list[dict]) -> str:
    directions = []
    for year in ("2008", "2019"):
        item = next(
            (
                row
                for row in regressions
                if row["year"] == year
                and row["model"] == "M2"
                and row["term"] == "income:q5"
            ),
            None,
        )
        if (
            item is None
            or not np.isfinite(item["ci_low"])
            or not np.isfinite(item["ci_high"])
        ):
            return "The controlled gradient is unavailable in at least one year."
        if item["ci_low"] > 0:
            directions.append("positive")
        elif item["ci_high"] < 0:
            directions.append("negative")
        else:
            return "The controlled gradient is inconclusive in at least one year."
    if directions[0] != directions[1]:
        return "The controlled income gradient changes direction between years."
    return (
        f"The {directions[0]} income gradient survives density and car controls "
        "in both years."
    )


def run_report(
    out: Path,
    cache_a: modes_cache.SurveyCache,
    cache_b: modes_cache.SurveyCache,
    attributes_a: tuple[dict[str, str], dict[str, str], dict[str, str]],
    attributes_b: tuple[dict[str, str], dict[str, str], dict[str, str]],
    draws_a: Draws,
    draws_b: Draws,
    *,
    selected_scopes: list[scope_module.Scope],
    minimum_n: int,
    caution_n: int,
    margins: tuple[float, float],
    checkpoint_dir: Path | None = None,
    warning_messages: list[str] | None = None,
) -> dict[str, float]:
    """Write the cached income supplement and five CSVs, section 9.9."""
    if minimum_n <= 0 or caution_n < minimum_n or not selected_scopes:
        raise ValueError("Invalid disclosure thresholds or empty scope list")
    out.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    all_levels: list[dict] = []
    all_gaps: list[dict] = []
    all_reweighted: list[dict] = []
    all_regressions: list[dict] = []
    all_density: list[dict] = []
    report = [
        "# Daily travel time by household income",
        "",
        "Weekdays, residents aged 6+; quintiles are relative within each year. "
        "ENTD uses bracket midpoint per consumption unit; EMP uses INSEE's imputed "
        "income decile re-cut under individual weights.",
        "",
        "ENTD unknown income remains a separate sixth group; 2019 has no equivalent. "
        "Residence density is the urban-unit-status × size proxy in both years. "
        "Cars are grouped 0, 1, 2+; their exact survey coverage needs verification.",
        "",
        "Levels and gaps use 95% household-bootstrap intervals; cross-year ratios "
        "use 90% intervals. Individual survey household draws are independent, "
        "and shared across scopes and statistics. Per-person estimates include "
        "zero-trip people and subtract open-day weights.",
        "",
        "Reweighting excludes unknown income and targets the average of each "
        "survey's joint income × density × cars distribution, separately for "
        "each estimation basis. Unsupported cells pool cars within density, "
        "then pool density and cars within the quintile. A draw without "
        "common support is invalid.",
        "",
        "M0 includes income, population category and weekday; M1 adds density; "
        "M2 adds cars. The pooled M2 model adds survey × quintile interactions. "
        "WLS models log travel-day minutes, so M2 Q5/Q1 is a conditional "
        "geometric ratio, not the arithmetic-mean gap. Nonpositive times are "
        "excluded. Regression confidence intervals are household-bootstrap 95%.",
        "",
        f"Cells under {minimum_n} respondents are hidden; density cells under "
        f"{caution_n} are flagged. Intervals need at least 95% valid draws.",
        "",
    ]
    for selected in selected_scopes:
        checkpoint = checkpoint_dir / f"{selected.id}.json" if checkpoint_dir else None
        if checkpoint is not None and checkpoint.is_file():
            LOGGER.info("%s: resuming completed scope", selected.id)
            result = json.loads(checkpoint.read_text(encoding="utf-8"))
            if result["scope"] != selected.id:
                raise ValueError(f"Checkpoint scope mismatch: {checkpoint}")
            for warning in result["warnings"]:
                LOGGER.warning("%s (resumed %s)", warning, selected.id)
        else:
            warning_start = len(warning_messages) if warning_messages is not None else 0
            with modes._timed(timings, f"{selected.id} read"):
                samples = [
                    read_cached_income(
                        cache,
                        selected,
                        income=attrs[0],
                        density=attrs[1],
                        cars=attrs[2],
                    )
                    for cache, attrs in (
                        (cache_a, attributes_a),
                        (cache_b, attributes_b),
                    )
                ]
            with modes._timed(timings, f"{selected.id} levels and gaps"):
                ma = income_metrics(samples[0].people, samples[0].days, draws_a)
                mb = income_metrics(samples[1].people, samples[1].days, draws_b)
                levels = level_rows(ma, mb, minimum_n=minimum_n, margins=margins)
                gaps = gap_rows(ma, mb, minimum_n=minimum_n)
                density = density_rows(
                    samples[0],
                    samples[1],
                    draws_a,
                    draws_b,
                    minimum_n=minimum_n,
                    caution_n=caution_n,
                    margins=margins,
                )
            with modes._timed(timings, f"{selected.id} reweighting"):
                ra, rb, collapsed = reweighted_metrics(
                    samples[0], samples[1], draws_a, draws_b
                )
                reweighted = level_rows(ra, rb, minimum_n=minimum_n, margins=margins)
                reweighted_gaps = gap_rows(ra, rb, minimum_n=minimum_n)
            with modes._timed(timings, f"{selected.id} regression"):
                regressions = regression_rows(
                    samples[0], samples[1], draws_a, draws_b, minimum_n=minimum_n
                )
            day_mask = ~samples[0].days.is_open
            respondent_share, day_share = unknown_income_shares(
                samples[0].people.income,
                samples[0].days.income[day_mask],
                samples[0].days.weight[day_mask],
            )
            result = {
                "scope": selected.id,
                "levels": levels,
                "gaps": gaps,
                "density": density,
                "reweighted": reweighted,
                "reweighted_gaps": reweighted_gaps,
                "regressions": regressions,
                "collapsed": collapsed,
                "respondent_share": respondent_share,
                "day_share": day_share,
                "unknown_n": int(np.sum(samples[0].people.income == "unknown")),
                "warnings": (
                    warning_messages[warning_start:]
                    if warning_messages is not None
                    else []
                ),
            }
            if checkpoint is not None:
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                encoded = json.dumps(result, ensure_ascii=False)
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=checkpoint.parent, delete=False
                ) as stream:
                    temporary = Path(stream.name)
                try:
                    temporary.write_text(encoded, encoding="utf-8")
                    temporary.replace(checkpoint)
                finally:
                    temporary.unlink(missing_ok=True)
        levels = result["levels"]
        gaps = result["gaps"]
        density = result["density"]
        reweighted = result["reweighted"]
        reweighted_gaps = result["reweighted_gaps"]
        regressions = result["regressions"]
        collapsed = result["collapsed"]
        respondent_share = result["respondent_share"]
        day_share = result["day_share"]
        unknown_n = result["unknown_n"]
        for collection in (
            levels,
            gaps,
            reweighted,
            reweighted_gaps,
            regressions,
            density,
        ):
            for row in collection:
                row["scope"] = selected.id
        all_levels.extend(levels)
        all_gaps.extend(gaps)
        all_reweighted.extend({"row_type": "level", **row} for row in reweighted)
        all_reweighted.extend({"row_type": "gap", **row} for row in reweighted_gaps)
        all_reweighted.extend(
            {
                "scope": selected.id,
                "row_type": "collapse",
                "basis": basis,
                "original_cell": original,
                "collapsed_cell": target,
            }
            for basis, original, target in collapsed
        )
        all_regressions.extend(regressions)
        all_density.extend(density)
        report.extend([f"## {selected.label} (`{selected.id}`)", ""])
        if unknown_n == 0 or unknown_n >= minimum_n:
            report.append(
                f"ENTD unknown income: {100 * respondent_share:.2f}% of respondents "
                f"and {100 * day_share:.2f}% of kept described-day weight. "
                "EMP income is imputed; no equivalent unknown group."
            )
        else:
            report.append(
                "ENTD unknown-income shares suppressed for a small cell; "
                "EMP has no equivalent unknown group."
            )
        report.append("")
        report.extend(
            modes._markdown_table(
                "Levels and 2019/2008 ratios",
                selected,
                levels,
                (
                    "basis",
                    "quintile",
                    "n_2008",
                    "mean_2008",
                    "ci_2008_low",
                    "ci_2008_high",
                    "n_2019",
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
        )
        report.extend(
            modes._markdown_table(
                "Income gaps and their changes",
                selected,
                gaps,
                (
                    "basis",
                    "gap",
                    "value_2008",
                    "ci_2008_low",
                    "ci_2008_high",
                    "value_2019",
                    "ci_2019_low",
                    "ci_2019_high",
                    "change",
                    "change_ci_low",
                    "change_ci_high",
                ),
            )
        )
        report.extend(
            modes._markdown_table(
                "Reweighted levels and ratios",
                selected,
                reweighted,
                (
                    "basis",
                    "quintile",
                    "n_2008",
                    "mean_2008",
                    "ci_2008_low",
                    "ci_2008_high",
                    "n_2019",
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
        )
        report.extend(
            modes._markdown_table(
                "Reweighted gaps",
                selected,
                reweighted_gaps,
                (
                    "basis",
                    "gap",
                    "value_2008",
                    "ci_2008_low",
                    "ci_2008_high",
                    "value_2019",
                    "ci_2019_low",
                    "ci_2019_high",
                    "change",
                    "change_ci_low",
                    "change_ci_high",
                ),
            )
        )
        report.extend(["### Collapsed joint cells", ""])
        report.extend(
            [
                f"- {basis}: `{original}` → `{target}`."
                for basis, original, target in collapsed
            ]
            or ["- None."]
        )
        report.append("")
        report.extend(
            modes._markdown_table(
                "Weighted regressions",
                selected,
                regressions,
                (
                    "year",
                    "model",
                    "term",
                    "n_2008",
                    "n_2019",
                    "percent",
                    "ci_low",
                    "ci_high",
                ),
            )
        )
        report.extend(
            modes._markdown_table(
                "Quintile × density",
                selected,
                density,
                (
                    "basis",
                    "quintile",
                    "density",
                    "small_cell",
                    "n_2008",
                    "mean_2008",
                    "ci_2008_low",
                    "ci_2008_high",
                    "n_2019",
                    "mean_2019",
                    "ci_2019_low",
                    "ci_2019_high",
                    "ratio",
                    "ratio_ci_low",
                    "ratio_ci_high",
                ),
            )
        )
        conclusion = _conclusion_rows(levels, gaps, reweighted_gaps, regressions)
        report.extend(
            modes._markdown_table(
                "Conclusion grid",
                selected,
                conclusion,
                (
                    "basis",
                    "quintile",
                    "ratio",
                    "verdict_15",
                    "raw_q5_q1_2008",
                    "raw_q5_q1_2019",
                    "reweighted_q5_q1_2008",
                    "reweighted_q5_q1_2019",
                    "m2_q5_q1_2008",
                    "m2_q5_q1_2019",
                ),
            )
        )
        report.extend([_gradient_statement(regressions), ""])
    for name, rows in (
        ("levels.csv", all_levels),
        ("gaps.csv", all_gaps),
        ("reweighted.csv", all_reweighted),
        ("regression.csv", all_regressions),
        ("quintile_density.csv", all_density),
    ):
        modes._csv_rows(out / name, rows, ("scope",))
    out.with_suffix(".md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return timings


def read_signed_cache(
    survey: ModuleType,
    data_path: Path,
    cache_dir: Path,
    *,
    activity_stay_min: float,
    config_path: Path,
) -> modes_cache.SurveyCache:
    """Read an existing Z1 cache, never building or modifying it."""
    signature = modes_cache.input_signature(
        survey, data_path, activity_stay_min, config_path
    )
    cache = modes_cache.SurveyCache(
        cache_dir / survey.__name__.rsplit(".", 1)[-1] / signature
    )
    modes_cache._verify_cache(cache, signature)
    return cache


def checkpoint_directory(
    base: Path, caches: list[modes_cache.SurveyCache], inputs: tuple[Path, ...]
) -> Path:
    """Key completed scopes by verified caches, code and report inputs."""
    digest = hashlib.sha256()
    for cache in caches:
        digest.update(str(cache.root.resolve()).encode("utf-8"))
    for path in inputs:
        digest.update(str(path.resolve()).encode("utf-8"))
        modes_cache._hash_file(digest.update, path)
    return base / digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    """Run the income supplement on existing Z1 caches, section 9.9."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--income-config", type=Path, default=vr.ROOT / "config" / "zahavi_income.yaml"
    )
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
    with args.income_config.open(encoding="utf-8") as stream:
        income_config = IncomeConfig.model_validate(yaml.safe_load(stream))
    with args.modes_config.open(encoding="utf-8") as stream:
        config = modes.ReportConfig.model_validate(yaml.safe_load(stream))
    variation_config = vr.variation.load_variation_config(args.variation_config)
    scopes = (
        list(scope_module.ALL_SCOPES)
        if args.scope == "all"
        else [scope_module.Scope.parse(args.scope)]
    )
    cache_dir = vr.ROOT / config.cache_dir
    logs_dir = vr.ROOT / config.logs_dir
    car_path = vr.ROOT / income_config.entd_cars
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    log_path = logs_dir / f"{stamp}_zahavi_income.log"
    summary_path = logs_dir / f"{stamp}_zahavi_income_summary.md"
    counter = modes._WarningCounter()
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
        with modes._timed(timings, "load existing caches"):
            caches = [
                read_signed_cache(
                    survey,
                    source,
                    cache_dir,
                    activity_stay_min=variation_config.scope.activity_stay_min,
                    config_path=args.config,
                )
                for survey, source in (
                    (entd2008, args.entd2008_data_path),
                    (emp2019, args.emp2019_data_path),
                )
            ]
        with modes._timed(timings, "extract respondent attributes"):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                attrs_a = extract_attributes(
                    entd2008, args.entd2008_data_path, root / "entd", entd_cars=car_path
                )
                attrs_b = extract_attributes(
                    emp2019, args.emp2019_data_path, root / "emp"
                )
        with modes._timed(timings, "shared household draws"):
            seed_a, seed_b = np.random.SeedSequence(config.seed).spawn(2)
            draws_a = modes.make_draws(
                modes._roster_households(caches[0]),
                n_reps=config.bootstrap_reps,
                seed=seed_a,
            )
            draws_b = modes.make_draws(
                modes._roster_households(caches[1]),
                n_reps=config.bootstrap_reps,
                seed=seed_b,
            )
        for year, cache in ((2008, caches[0]), (2019, caches[1])):
            roster, days, trips = modes._sample_counts(
                cache, scope_module.REFERENCE_SCOPE
            )
            counts.append(
                f"{year}: {roster} roster persons, {days} days, {trips} trips."
            )
        if modes.__file__ is None or scope_cube.__file__ is None:
            raise RuntimeError("Cannot identify shared modules for checkpointing")
        checkpoint = checkpoint_directory(
            vr.ROOT / income_config.checkpoint_dir,
            caches,
            (
                Path(__file__),
                Path(modes.__file__),
                Path(scope_cube.__file__),
                args.income_config,
                args.modes_config,
                args.variation_config,
                car_path,
            ),
        )
        timings.update(
            run_report(
                args.out,
                caches[0],
                caches[1],
                attrs_a,
                attrs_b,
                draws_a,
                draws_b,
                selected_scopes=scopes,
                minimum_n=config.minimum_cell_n,
                caution_n=income_config.caution_cell_n,
                margins=(
                    variation_config.equivalence_margin,
                    variation_config.secondary_equivalence_margin,
                ),
                checkpoint_dir=checkpoint,
                warning_messages=counter.messages,
            )
        )
        success = True
    finally:
        if not success:
            LOGGER.error("Income report failed; see traceback and log.")
        lines = [
            "# Zahavi income report summary",
            "",
            f"Status: {'completed' if success else 'failed'}.",
            f"Input surveys: {args.entd2008_data_path}; {args.emp2019_data_path}.",
            f"ENTD household cars: {car_path}.",
            f"Scopes: {', '.join(selected.id for selected in scopes)}.",
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
