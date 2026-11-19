"""Income-supplement calculations for the daily budget (section 9.9)."""

import logging
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfileobj
from types import ModuleType

import duckdb
import numpy as np

from mobgrid.budget import daily_energy, trip_legs
from mobgrid.budget import variation_report as vr
from mobgrid.budget import zahavi_modes as modes
from mobgrid.budget.zahavi_modes import Draws, Metric

LOGGER = logging.getLogger(__name__)


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
    people: People, days: Days, draws: Draws
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
    for quintile in trip_legs.INCOME_QUINTILE_LABELS:
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
) -> list[dict]:
    """Report mean minutes and 2019/2008 ratios, section 9.9."""
    rows = []
    for basis in ("travel_day", "person"):
        for quintile in trip_legs.INCOME_QUINTILE_LABELS:
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
                if entry is None or (year == 2019 and quintile == "unknown"):
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
                valid = np.isfinite(a.replicates) & np.isfinite(b.replicates)
                valid &= a.replicates != 0
                if not valid.any():
                    LOGGER.warning("No valid ratio draws for %s / %s", basis, quintile)
                else:
                    ratio, (low, high) = daily_energy.bootstrap_replicate_ratio_ci(
                        a.value, a.replicates, b.value, b.replicates
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
