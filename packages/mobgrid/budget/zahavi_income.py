"""Income-supplement calculations for the daily budget (section 9.9)."""

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from shutil import copyfileobj
from types import ModuleType

import duckdb
import numpy as np

from mobgrid.budget import daily_energy, modes_cache, trip_legs
from mobgrid.budget import scope as scope_module
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
    cells_a: np.ndarray, cells_b: np.ndarray
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
    unique_a = {tuple(row) for row in np.unique(cells_a.astype(str), axis=0)}
    unique_b = {tuple(row) for row in np.unique(cells_b.astype(str), axis=0)}
    quintiles_a = {cell[0] for cell in unique_a}
    quintiles_b = {cell[0] for cell in unique_b}
    if quintiles_a != quintiles_b:
        raise ValueError("A quintile lacks common survey support")
    mapping: dict[tuple[str, ...], str] = {}
    for quintile in sorted(quintiles_a):
        a = {cell for cell in unique_a if cell[0] == quintile}
        b = {cell for cell in unique_b if cell[0] == quintile}
        density_a = {cell[1] for cell in a}
        density_b = {cell[1] for cell in b}
        if density_a != density_b:
            mapping.update({cell: f"{quintile}|all|all" for cell in a | b})
            continue
        for density in sorted(density_a):
            aa = {cell for cell in a if cell[1] == density}
            bb = {cell for cell in b if cell[1] == density}
            if aa != bb:
                mapping.update({cell: f"{quintile}|{density}|all" for cell in aa | bb})
            else:
                mapping.update({cell: "|".join(cell) for cell in aa})
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
            prepared.append(
                (sample, draws, known_p, travel, opened, pcells, dcells, support)
            )
        mapped_a, mapped_b, collapsed = collapse_joint_cells(
            prepared[0][7], prepared[1][7]
        )
        collapsed_rows.extend((basis, src, dest) for src, dest in collapsed)
        labels = np.unique(np.concatenate((mapped_a, mapped_b)))
        joint_codes = []
        for prepared_sample, mapped in zip(prepared, (mapped_a, mapped_b), strict=True):
            sample, draws, known_p, travel, opened, pcells, dcells, support = (
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
                sample, draws, known_p, travel, opened, _, _, _ = item
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
            sample, _, known_p, travel, _, _, _, _ = item
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
