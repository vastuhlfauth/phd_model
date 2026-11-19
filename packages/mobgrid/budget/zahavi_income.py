"""Income-supplement calculations for the daily budget (section 9.9)."""

from pathlib import Path
from shutil import copyfileobj
from types import ModuleType

import duckdb
import numpy as np

from mobgrid.budget.zahavi_modes import Metric


def load_entd_household_cars(source: Path, scratch: Path) -> dict[str, str]:
    """Load ENTD household car-count bands from CP1252, section 9.9."""
    scratch.mkdir(parents=True, exist_ok=True)
    encoded = scratch / source.name
    with source.open(encoding="cp1252") as inp, encoded.open(
        "w", encoding="utf-8", newline=""
    ) as out:
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
        (q5_b.replicates - q1_b.replicates)
        - (q5_a.replicates - q1_a.replicates),
    )


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
