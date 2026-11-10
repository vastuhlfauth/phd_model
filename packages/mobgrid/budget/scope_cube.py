"""Cross-scope cube: section 9.9's core indicators for all eight scopes.

``python -m mobgrid.budget.scope_cube --out docs/data/scope_cube`` reuses the
step-11 survey loaders (``emp2019``/``entd2008`` extraction, ``trip_legs``)
and the section 9.9 scope chain (``scope.create_scope_views_from_trip_legs``),
and writes the cross-scope comparison of the spec ("the core indicators of
the eight scopes side by side, by population category, with the 2019/2008
ratio and the effect of flipping each switch from the reference").

Units: durations in minutes, distances in km, weights are the surveys' day
weights (`POND_JOUR`/`POIDS_JOUR`) and 5 x the individual weights
(`pond_indC`/`PONDKI`) for the person-weekday universe. Weekdays only.

Estimation bases, per scope x survey x population category:

- ``person_days``: the person-weekday universe (5 x individual weight);
  "kept" removes the described weekday trip-days that fail the day switch
  (non-round days under `round`), as section 9.9's open-day rule removes
  them from the per-person denominator.
- ``day``: described weekday trip-days kept by the day switch, a day with
  no in-scope trip counting zero.
- ``travel_day``: kept days with at least one in-scope trip.
- ``trip``: in-scope trips; per-trip quantities are ratios of weighted
  totals (day weight x value over day weight).
- ``person``: numerator over kept days, denominator the person-weekday
  universe minus the dropped days' weights (section 9.9's estimator).

Bootstrap: one set of 200 household draws per survey
(``variation.household_multipliers``), shared by every scope, category and
indicator, so switch effects use paired draws. Levels get percentile 95%
intervals; 2019/2008 ratios reuse ``daily_energy.bootstrap_replicate_ratio_ci``
(paired percentile 90% intervals) with verdicts at +-15% and +-10%
(``variation_report._equivalence_verdict``). Cells under
``variation_report.MIN_CELL_N`` (50) respondents keep their true n and hide
every value, in the report and in the CSV.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np

from mobgrid.budget import daily_energy, emp2019, entd2008, variation
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr
from mobgrid.energy.rates import EnergyConfig, load_energy_config

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"
DEFAULT_VARIATION_CONFIG_PATH = ROOT / "config" / "variation.yaml"
DEFAULT_OUT_DIR = ROOT / "docs" / "data" / "scope_cube"

MIN_CELL_N = vr.MIN_CELL_N
ALL_CATEGORY = "All"

#: Household-level component sums, in this order (one column each):
#: the person-weekday universe, then day-weight sums over described
#: weekday trip-days (dropped by the day switch, kept, kept with trips)
#: and weighted trip totals over kept days (trips, minutes and the
#: minute-known trip weight, producer km and crow-fly km with their
#: distance-known trip weights).
_COMPONENTS = (
    "universe",
    "dropped",
    "kept",
    "travel",
    "trips",
    "minutes",
    "minute_trips",
    "producer_km",
    "producer_trips",
    "crow_km",
    "crow_trips",
)


@dataclass(frozen=True)
class IndicatorSpec:
    """One cube indicator: estimate key, CSV naming and formatting."""

    key: str
    indicator: str
    basis: str
    label: str
    decimals: int
    is_share: bool = False
    has_quantiles: bool = False


INDICATOR_SPECS: tuple[IndicatorSpec, ...] = (
    IndicatorSpec(
        "person_days_kept_share",
        "person_days_kept_share",
        "person_days",
        "Share of person-days kept",
        1,
        is_share=True,
    ),
    IndicatorSpec(
        "trips_per_day",
        "trips_per_day",
        "travel_day",
        "Trips per day (days with trips)",
        2,
        has_quantiles=True,
    ),
    IndicatorSpec(
        "minutes_per_trip", "minutes_per_trip", "trip", "Minutes per trip", 1
    ),
    IndicatorSpec(
        "km_per_trip_producer",
        "km_per_trip_producer",
        "trip",
        "Km per trip (producer distance)",
        2,
    ),
    IndicatorSpec(
        "km_per_trip_crow_fly",
        "km_per_trip_crow_fly",
        "trip",
        "Km per trip (crow-fly distance)",
        2,
    ),
    IndicatorSpec(
        "minutes_per_day_day",
        "minutes_per_day",
        "day",
        "Minutes per day (described days)",
        1,
        has_quantiles=True,
    ),
    IndicatorSpec(
        "minutes_per_day_travel_day",
        "minutes_per_day",
        "travel_day",
        "Minutes per day (days with trips)",
        1,
        has_quantiles=True,
    ),
    IndicatorSpec(
        "minutes_per_day_person",
        "minutes_per_day",
        "person",
        "Minutes per day (per person)",
        1,
    ),
)

#: The three single-switch flips from the reference scope (section 9.9's
#: cross-scope comparison: "the effect of flipping each switch").
SWITCH_FLIPS: tuple[tuple[str, scope_module.Scope], ...] = tuple(
    (switch, scope_module.Scope(**{**vars(scope_module.REFERENCE_SCOPE), switch: off}))
    for switch, off in (
        ("days", "alldays"),
        ("purposes", "allpurp"),
        ("distance", "daytable"),
    )
)


@dataclass(frozen=True)
class ScopeDayFrame:
    """One scope's described weekday trip-days: identifiers, day weights,
    the day switch's kept flag, and per-day in-scope trip totals (trips,
    minutes, km) with the corresponding weighted trip counts."""

    person: np.ndarray
    household: np.ndarray
    category: np.ndarray
    weight: np.ndarray
    kept: np.ndarray
    trips: np.ndarray
    minutes: np.ndarray
    minute_trips: np.ndarray
    producer_km: np.ndarray
    producer_trips: np.ndarray
    crow_km: np.ndarray
    crow_trips: np.ndarray


@dataclass(frozen=True)
class CubeSurvey:
    """One survey's cube inputs: the person-weekday roster (5 x individual
    weight, section 9.9) and one ``ScopeDayFrame`` per scope id."""

    name: str
    roster_person: np.ndarray
    roster_household: np.ndarray
    roster_category: np.ndarray
    roster_weight: np.ndarray
    frames: dict[str, ScopeDayFrame]


@dataclass(frozen=True)
class CubeCell:
    """Point estimates, bootstrap replicates and weighted quantiles for
    one scope x survey x category."""

    n_respondents: int
    n_trips: int
    estimates: dict[str, float]
    replicates: dict[str, np.ndarray]
    quantiles: dict[str, tuple[float, float, float]]


def _scope_day_frame(
    con: duckdb.DuckDBPyConnection,
    selected_scope: scope_module.Scope,
    sample_pct: float | None,
) -> ScopeDayFrame:
    """Fetch one scope's weekday trip-day rows (joined in SQL, not Python)."""
    rows = con.sql(f"""
        SELECT b.ident_ind, b.ident_men, b.population_category, b.pond_jour,
            b.is_round,
            coalesce(s.trips, 0) AS trips,
            coalesce(s.minutes, 0.0) AS minutes,
            coalesce(s.minute_trips, 0.0) AS minute_trips,
            coalesce(s.producer_km, 0.0) AS producer_km,
            coalesce(s.producer_trips, 0.0) AS producer_trips,
            coalesce(s.crow_km, 0.0) AS crow_km,
            coalesce(s.crow_trips, 0.0) AS crow_trips
        FROM cube_day_base b
        LEFT JOIN (
            SELECT t.day_id,
                count(*) AS trips,
                coalesce(sum(t.duration_min) FILTER (
                    WHERE isfinite(t.duration_min)), 0.0) AS minutes,
                count(*) FILTER (WHERE isfinite(t.duration_min)) AS minute_trips,
                coalesce(sum(t.distance_km) FILTER (
                    WHERE isfinite(t.distance_km)), 0.0) AS producer_km,
                count(*) FILTER (WHERE isfinite(t.distance_km)) AS producer_trips,
                coalesce(sum(e.crow_fly_km) FILTER (
                    WHERE isfinite(e.crow_fly_km)), 0.0) AS crow_km,
                count(*) FILTER (WHERE isfinite(e.crow_fly_km)) AS crow_trips
            FROM trip_legs t
            LEFT JOIN vr_trip_ext e ON e.ident_dep = t.ident_dep
            WHERE t.typejour = 1 AND t.pond_jour > 0
                AND ({selected_scope.trip_filter_sql("t")})
            GROUP BY t.day_id
        ) s ON s.day_id = b.day_id
    """).fetchnumpy()
    rows = {name: vr._plain_array(values) for name, values in rows.items()}
    kept = (
        rows["is_round"].astype(bool)
        if selected_scope.days == "round"
        else np.ones(len(rows["is_round"]), dtype=bool)
    )
    return ScopeDayFrame(
        person=vr._text_values(rows["ident_ind"]),
        household=vr._text_values(rows["ident_men"]),
        category=vr._text_values(rows["population_category"]),
        weight=np.asarray(rows["pond_jour"], dtype=float),
        kept=kept,
        trips=np.asarray(rows["trips"], dtype=float),
        minutes=np.asarray(rows["minutes"], dtype=float),
        minute_trips=np.asarray(rows["minute_trips"], dtype=float),
        producer_km=np.asarray(rows["producer_km"], dtype=float),
        producer_trips=np.asarray(rows["producer_trips"], dtype=float),
        crow_km=np.asarray(rows["crow_km"], dtype=float),
        crow_trips=np.asarray(rows["crow_trips"], dtype=float),
    )


def load_cube_survey(
    survey,
    data_path: Path | None = None,
    config: EnergyConfig | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    sample_pct: float | None = None,
    activity_stay_min: float | None = None,
) -> CubeSurvey:
    """Load one survey once and extract all eight scopes' weekday frames.

    Reuses the step-11 loaders (``extract_tables``/``register_views``/
    ``build_trip_legs``), the section 9.9 scope chain and step 12's Kish
    person-weekday roster (``variation_report._scope_person_weekday_rows``).
    """
    config = config or load_energy_config(config_path)
    if activity_stay_min is None:
        activity_stay_min = variation.load_variation_config(
            DEFAULT_VARIATION_CONFIG_PATH
        ).scope.activity_stay_min
    data_path = data_path or survey.DEFAULT_DATA_PATH
    interim_dir = (
        None
        if data_path == survey.DEFAULT_DATA_PATH
        else data_path.parent / f"_interim_{survey.__name__.rsplit('.', 1)[-1]}_csv"
    )
    con = duckdb.connect()
    try:
        csv_paths = survey.extract_tables(data_path, interim_dir)
        survey.register_views(con, csv_paths)
        survey.build_trip_legs(
            con, config, density_source=survey.DEFAULT_DENSITY_SOURCE
        )
        scope_module.create_scope_views_from_trip_legs(
            con, activity_stay_min=activity_stay_min
        )
        vr._PERSON_EXT_BY_SURVEY[survey.SURVEY_NAME](con)
        roster = vr._scope_person_weekday_rows(con, survey.SURVEY_NAME, sample_pct)
        con.sql(f"""
            CREATE OR REPLACE TEMPORARY TABLE cube_day_base AS
            SELECT t.day_id,
                any_value(t.ident_ind) AS ident_ind,
                any_value(t.ident_men) AS ident_men,
                any_value(t.pond_jour) AS pond_jour,
                any_value(t.population_category) AS population_category,
                coalesce(any_value(d.is_round), FALSE) AS is_round
            FROM trip_legs t
            LEFT JOIN scope_days d ON d.day_id = t.day_id
            WHERE t.typejour = 1 AND t.pond_jour > 0
                AND ({vr._sample_sql(sample_pct, "t.ident_men")})
            GROUP BY t.day_id
        """)
        frames = {
            selected.id: _scope_day_frame(con, selected, sample_pct)
            for selected in scope_module.ALL_SCOPES
        }
    finally:
        con.close()
    return CubeSurvey(
        name=survey.SURVEY_NAME,
        roster_person=np.asarray([row[0] for row in roster], dtype=object),
        roster_household=np.asarray([row[1] for row in roster], dtype=object),
        roster_category=np.asarray([row[2] for row in roster], dtype=object),
        roster_weight=np.asarray([row[3] for row in roster], dtype=float),
        frames=frames,
    )


def multiplier_matrix(
    households: np.ndarray, *, n_reps: int, seed
) -> np.ndarray:
    """One (n_reps, households) household-bootstrap multiplicity matrix,
    from the shared ``variation.household_multipliers`` draw. One matrix
    per survey is reused by every scope, so switch effects are paired."""
    if n_reps <= 0:
        raise ValueError("n_reps must be positive")
    rng = np.random.default_rng(seed)
    return np.stack(
        [variation.household_multipliers(households, rng) for _ in range(n_reps)]
    ).astype(float)


def _cell_metrics(values: np.ndarray) -> dict[str, np.ndarray]:
    """Indicator values from component sums (last axis in ``_COMPONENTS``
    order); zero denominators give NaN."""
    columns = {name: np.asarray(values[..., i], dtype=float)
               for i, name in enumerate(_COMPONENTS)}
    person_universe = columns["universe"] - columns["dropped"]

    def div(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            out = numerator / denominator
        return np.where(denominator > 0, out, np.nan)

    return {
        "person_days_kept_share": div(person_universe, columns["universe"]),
        "trips_per_day": div(columns["trips"], columns["travel"]),
        "minutes_per_trip": div(columns["minutes"], columns["minute_trips"]),
        "km_per_trip_producer": div(
            columns["producer_km"], columns["producer_trips"]
        ),
        "km_per_trip_crow_fly": div(columns["crow_km"], columns["crow_trips"]),
        "minutes_per_day_day": div(columns["minutes"], columns["kept"]),
        "minutes_per_day_travel_day": div(columns["minutes"], columns["travel"]),
        "minutes_per_day_person": div(columns["minutes"], person_universe),
    }


def survey_cells(
    survey: CubeSurvey,
    *,
    n_reps: int = 200,
    seed=0,
    categories: list[str] | None = None,
) -> dict[tuple[str, str], CubeCell]:
    """Compute every (scope id, category) cell of one survey, with one
    shared set of household draws (paired across scopes and categories)."""
    households = np.unique(survey.roster_household)
    multipliers = multiplier_matrix(households, n_reps=n_reps, seed=seed)
    roster_index = np.searchsorted(households, survey.roster_household)
    if categories is None:
        categories = cube_categories(survey)
    cells: dict[tuple[str, str], CubeCell] = {}
    for scope_id, frame in survey.frames.items():
        if not np.isin(frame.household, households).all():
            raise ValueError(
                f"{survey.name}: trip-day households missing from the Kish "
                f"roster in scope {scope_id}"
            )
        day_index = np.searchsorted(households, frame.household)
        kept = frame.kept
        weight = frame.weight
        travel = kept & (frame.trips > 0)
        day_values = np.column_stack(
            [
                weight * ~kept,
                weight * kept,
                weight * travel,
                weight * frame.trips * kept,
                weight * frame.minutes * kept,
                weight * frame.minute_trips * kept,
                weight * frame.producer_km * kept,
                weight * frame.producer_trips * kept,
                weight * frame.crow_km * kept,
                weight * frame.crow_trips * kept,
            ]
        )
        for category in categories:
            roster_mask = (
                np.ones(len(survey.roster_category), dtype=bool)
                if category == ALL_CATEGORY
                else survey.roster_category == category
            )
            day_mask = (
                np.ones(len(frame.category), dtype=bool)
                if category == ALL_CATEGORY
                else frame.category == category
            )
            aggregates = np.zeros((len(households), len(_COMPONENTS)))
            np.add.at(
                aggregates[:, 0],
                roster_index[roster_mask],
                survey.roster_weight[roster_mask],
            )
            np.add.at(aggregates[:, 1:], day_index[day_mask], day_values[day_mask])
            totals = aggregates.sum(axis=0)
            point = _cell_metrics(totals)
            replicates = _cell_metrics(multipliers @ aggregates)
            traveller_mask = day_mask & travel
            kept_mask = day_mask & kept
            quantiles = {
                "trips_per_day": daily_energy._weighted_quantiles(
                    frame.trips[traveller_mask], weight[traveller_mask]
                ),
                "minutes_per_day_day": daily_energy._weighted_quantiles(
                    frame.minutes[kept_mask], weight[kept_mask]
                ),
                "minutes_per_day_travel_day": daily_energy._weighted_quantiles(
                    frame.minutes[traveller_mask], weight[traveller_mask]
                ),
            }
            cells[(scope_id, category)] = CubeCell(
                n_respondents=len(np.unique(frame.person[traveller_mask])),
                n_trips=int(frame.trips[day_mask & kept].sum()),
                estimates={key: float(value) for key, value in point.items()},
                replicates=replicates,
                quantiles=quantiles,
            )
    return cells


def cube_categories(*surveys: CubeSurvey) -> list[str]:
    """``All`` first, then the surveys' population categories, sorted."""
    names: set[str] = set()
    for survey in surveys:
        names.update(survey.roster_category.tolist())
        for frame in survey.frames.values():
            names.update(frame.category.tolist())
    return [ALL_CATEGORY, *sorted(names)]


def _level_ci(replicates: np.ndarray) -> tuple[float, float]:
    """Percentile 95% interval over the finite bootstrap replicates."""
    finite = replicates[np.isfinite(replicates)]
    if len(finite) == 0:
        return (float("nan"), float("nan"))
    low, high = np.percentile(finite, [2.5, 97.5])
    return (float(low), float(high))


def _ratio_with_ci(
    cell_2008: CubeCell, cell_2019: CubeCell, key: str
) -> tuple[float, tuple[float, float]] | None:
    """2019/2008 ratio with its paired percentile 90% household interval,
    through the shared ``daily_energy.bootstrap_replicate_ratio_ci``."""
    point_2008 = cell_2008.estimates[key]
    point_2019 = cell_2019.estimates[key]
    if not (
        np.isfinite(point_2008)
        and np.isfinite(point_2019)
        and point_2008 > 0
        and point_2019 > 0
    ):
        return None
    try:
        return daily_energy.bootstrap_replicate_ratio_ci(
            point_2008,
            cell_2008.replicates[key],
            point_2019,
            cell_2019.replicates[key],
        )
    except ValueError:
        return None


def _blank_row(
    selected_scope: scope_module.Scope, survey: str, category: str
) -> dict:
    return {
        "scope": selected_scope.id,
        "days_switch": selected_scope.days,
        "purposes_switch": selected_scope.purposes,
        "distance_switch": selected_scope.distance,
        "survey": survey,
        "category": category,
        "indicator": "",
        "basis": "",
        "n": "",
        "mean": "",
        "ci_low": "",
        "ci_high": "",
        "median": "",
        "p25": "",
        "p75": "",
        "ratio": "",
        "ratio_ci_low": "",
        "ratio_ci_high": "",
        "verdict_15": "",
        "verdict_10": "",
    }


def _set_if_finite(row: dict, **values: float) -> None:
    """Fill numeric row fields, leaving non-finite values empty."""
    for key, value in values.items():
        if np.isfinite(value):
            row[key] = float(value)


def core_rows(
    cells_2008: dict[tuple[str, str], CubeCell],
    cells_2019: dict[tuple[str, str], CubeCell],
    categories: list[str],
    *,
    equivalence_margin: float,
    secondary_equivalence_margin: float,
) -> list[dict]:
    """Item-1 tidy rows: one row per estimate (scope x survey x category x
    indicator x basis). 2019/2008 ratio columns sit on the EMP 2019 row;
    cells under ``MIN_CELL_N`` respondents keep n and blank the values."""
    rows: list[dict] = []
    for selected_scope in scope_module.ALL_SCOPES:
        for category in categories:
            cell_by_survey = {
                "ENTD 2008": cells_2008[(selected_scope.id, category)],
                "EMP 2019": cells_2019[(selected_scope.id, category)],
            }
            for survey, cell in cell_by_survey.items():
                for indicator, count in (
                    ("n_respondents", cell.n_respondents),
                    ("n_trips", cell.n_trips),
                ):
                    row = _blank_row(selected_scope, survey, category)
                    row.update(indicator=indicator, basis="count", n=count)
                    rows.append(row)
            for spec in INDICATOR_SPECS:
                ratio = _ratio_with_ci(
                    cell_by_survey["ENTD 2008"], cell_by_survey["EMP 2019"], spec.key
                )
                ratio_n = min(
                    cell_by_survey["ENTD 2008"].n_respondents,
                    cell_by_survey["EMP 2019"].n_respondents,
                )
                for survey, cell in cell_by_survey.items():
                    row = _blank_row(selected_scope, survey, category)
                    row.update(
                        indicator=spec.indicator,
                        basis=spec.basis,
                        n=cell.n_respondents,
                    )
                    if cell.n_respondents >= MIN_CELL_N:
                        low, high = _level_ci(cell.replicates[spec.key])
                        _set_if_finite(
                            row,
                            mean=cell.estimates[spec.key],
                            ci_low=low,
                            ci_high=high,
                        )
                        if spec.has_quantiles:
                            p25, median, p75 = cell.quantiles[spec.key]
                            _set_if_finite(row, median=median, p25=p25, p75=p75)
                    if (
                        survey == "EMP 2019"
                        and ratio is not None
                        and ratio_n >= MIN_CELL_N
                    ):
                        estimate, ci = ratio
                        row.update(
                            ratio=estimate,
                            ratio_ci_low=ci[0],
                            ratio_ci_high=ci[1],
                            verdict_15=vr._equivalence_verdict(
                                ci, equivalence_margin
                            ),
                            verdict_10=vr._equivalence_verdict(
                                ci, secondary_equivalence_margin
                            ),
                        )
                    rows.append(row)
    return rows


def run(
    out_dir: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    variation_config_path: Path = DEFAULT_VARIATION_CONFIG_PATH,
    n_reps: int = 200,
    seed: int = 0,
    emp2019_data_path: Path | None = None,
    entd2008_data_path: Path | None = None,
    sample_pct: float | None = None,
) -> dict:
    """Compute the cube and its tidy rows; returns the results dict
    consumed by ``write_markdown`` and the tests."""
    out_dir.mkdir(parents=True, exist_ok=True)
    config = load_energy_config(config_path)
    variation_config = variation.load_variation_config(variation_config_path)
    stay_min = variation_config.scope.activity_stay_min
    survey_2008 = load_cube_survey(
        entd2008,
        entd2008_data_path,
        config,
        sample_pct=sample_pct,
        activity_stay_min=stay_min,
    )
    survey_2019 = load_cube_survey(
        emp2019,
        emp2019_data_path,
        config,
        sample_pct=sample_pct,
        activity_stay_min=stay_min,
    )
    seed_2008, seed_2019 = np.random.SeedSequence(seed).spawn(2)
    categories = cube_categories(survey_2008, survey_2019)
    cells_2008 = survey_cells(
        survey_2008, n_reps=n_reps, seed=seed_2008, categories=categories
    )
    cells_2019 = survey_cells(
        survey_2019, n_reps=n_reps, seed=seed_2019, categories=categories
    )
    rows = core_rows(
        cells_2008,
        cells_2019,
        categories,
        equivalence_margin=variation_config.equivalence_margin,
        secondary_equivalence_margin=variation_config.secondary_equivalence_margin,
    )
    return {
        "rows": rows,
        "categories": categories,
        "n_reps": n_reps,
        "seed": seed,
        "sample_pct": sample_pct,
        "equivalence_margin": variation_config.equivalence_margin,
        "secondary_equivalence_margin": variation_config.secondary_equivalence_margin,
    }


def _row_lookup(rows: list[dict]) -> dict[tuple, dict]:
    return {
        (row["scope"], row["survey"], row["category"], row["indicator"], row["basis"]):
            row
        for row in rows
    }


def _value_formatter(spec: IndicatorSpec):
    if spec.is_share:
        return vr._pct
    return lambda value: vr._num(value, spec.decimals)


def _fmt(value, formatter) -> str:
    return "-" if value == "" else formatter(value)


def _mean_cell(row: dict, spec: IndicatorSpec) -> str:
    if row["mean"] == "":
        return "-"
    fmt = _value_formatter(spec)
    return (
        f"{fmt(row['mean'])} "
        f"[{_fmt(row['ci_low'], fmt)}, {_fmt(row['ci_high'], fmt)}]"
    )


def _quantile_cell(row: dict, spec: IndicatorSpec) -> str:
    if row["median"] == "":
        return "-"
    fmt = _value_formatter(spec)
    return (
        f"{fmt(row['median'])} "
        f"({_fmt(row['p25'], fmt)}-{_fmt(row['p75'], fmt)})"
    )


def _ratio_cells(row: dict) -> tuple[str, str, str]:
    if row["ratio"] == "":
        return ("-", "-", "-")
    ci = f"{vr._num(row['ratio'], 3)} [{vr._num(row['ratio_ci_low'], 3)}, " \
        f"{vr._num(row['ratio_ci_high'], 3)}]"
    return (ci, row["verdict_15"], row["verdict_10"])


def _format_count_table(rows: list[dict], categories: list[str]) -> list[str]:
    lookup = _row_lookup(rows)
    lines = [
        "### Sample sizes",
        "",
        "Unweighted respondents with at least one in-scope weekday trip, "
        "and unweighted in-scope weekday trips.",
        "",
        "| Scope | Category | n resp. 2008 | n trips 2008 | "
        "n resp. 2019 | n trips 2019 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for selected_scope in scope_module.ALL_SCOPES:
        for category in categories:
            cells = [
                lookup[(selected_scope.id, survey, category, indicator, "count")]["n"]
                for survey in ("ENTD 2008", "EMP 2019")
                for indicator in ("n_respondents", "n_trips")
            ]
            lines.append(
                f"| {selected_scope.id} | {category} | "
                + " | ".join(str(cell) for cell in cells)
                + " |"
            )
    return lines


def _format_indicator_table(
    rows: list[dict], categories: list[str], spec: IndicatorSpec
) -> list[str]:
    lookup = _row_lookup(rows)
    quantile_cols = (
        " 2008 median (p25-p75) |" if spec.has_quantiles else ""
    )
    quantile_cols_2019 = (
        " 2019 median (p25-p75) |" if spec.has_quantiles else ""
    )
    header = (
        f"| Scope | Category | n 2008 | 2008 mean [95% CI] |{quantile_cols}"
        f" n 2019 | 2019 mean [95% CI] |{quantile_cols_2019}"
        " 2019/2008 [90% CI] | ±15% | ±10% |"
    )
    separators = "|---|---|---:|---:|" + (
        "---:|" if spec.has_quantiles else ""
    ) + "---:|---:|" + ("---:|" if spec.has_quantiles else "") + "---|---|---|"
    lines = [f"### {spec.label}", "", header, separators]
    for selected_scope in scope_module.ALL_SCOPES:
        for category in categories:
            row_2008 = lookup[
                (selected_scope.id, "ENTD 2008", category, spec.indicator, spec.basis)
            ]
            row_2019 = lookup[
                (selected_scope.id, "EMP 2019", category, spec.indicator, spec.basis)
            ]
            cells = [str(row_2008["n"]), _mean_cell(row_2008, spec)]
            if spec.has_quantiles:
                cells.append(_quantile_cell(row_2008, spec))
            cells += [str(row_2019["n"]), _mean_cell(row_2019, spec)]
            if spec.has_quantiles:
                cells.append(_quantile_cell(row_2019, spec))
            cells += list(_ratio_cells(row_2019))
            lines.append(
                f"| {selected_scope.id} | {category} | " + " | ".join(cells) + " |"
            )
    return lines


def write_markdown(md_path: Path, out_dir: Path, results: dict) -> None:
    """Write the scope-cube report, one table per indicator."""
    rows = results["rows"]
    categories = results["categories"]
    lines = [
        "# Scope cube: core indicators across the eight scopes",
        "",
        "Generated by `python -m mobgrid.budget.scope_cube`. Weekday "
        "described days of ENTD 2008 and EMP 2019, section 9.9's three "
        f"scope switches (reference `{scope_module.REFERENCE_SCOPE.id}`: "
        f"{scope_module.REFERENCE_SCOPE.label}). Household-bootstrap "
        f"percentile intervals ({results['n_reps']} replicates, one shared "
        "set of draws per survey across every scope): 95% for levels, 90% "
        "for 2019/2008 ratios, with equivalence verdicts at "
        f"±{results['equivalence_margin']:.0%} and "
        f"±{results['secondary_equivalence_margin']:.0%}. Cells of fewer "
        f"than {MIN_CELL_N} respondents print their true n with `-` for "
        "the values."
        + (
            f" Household sample: {results['sample_pct']:g}% (smoke run)."
            if results.get("sample_pct")
            else ""
        ),
        "",
        "Bases: *person-days* is the person-weekday universe (5 × the "
        "individual weight), from which the day switch's dropped trip-days "
        "are removed, as in section 9.9's open-day rule; *described days* "
        "are the kept weekday trip-days, counting zero when every trip of "
        "the day is out of scope; *days with trips* keep at least one "
        "in-scope trip; per-trip quantities are ratios of weighted totals; "
        "*per person* divides the kept days' totals by the person-weekday "
        "universe minus the dropped days' weights. Trips per day and "
        "the 2019/2008 ratio columns come from the same weighted totals "
        "and paired replicates as the CSV. "
        + scope_module.DAYTABLE_COVERAGE_NOTE
        + " 2008 `daytable` levels and ratios carry that caveat.",
        "",
        "## 1. Core indicators",
        "",
        *_format_count_table(rows, categories),
    ]
    for spec in INDICATOR_SPECS:
        lines += ["", *_format_indicator_table(rows, categories, spec)]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-scope cube of section 9.9's core indicators "
        "(all eight scopes, both surveys)."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--variation-config", type=Path, default=DEFAULT_VARIATION_CONFIG_PATH
    )
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--emp2019-data-path", type=Path, default=None)
    parser.add_argument("--entd2008-data-path", type=Path, default=None)
    parser.add_argument(
        "--sample-households",
        type=float,
        default=None,
        help="Keep only this percentage of households per survey "
        "(stable hash), for smoke runs.",
    )
    args = parser.parse_args(argv)
    results = run(
        args.out,
        args.config,
        variation_config_path=args.variation_config,
        n_reps=args.bootstrap_reps,
        seed=args.seed,
        emp2019_data_path=args.emp2019_data_path,
        entd2008_data_path=args.entd2008_data_path,
        sample_pct=args.sample_households,
    )
    md_path = args.out.with_suffix(".md")
    write_markdown(md_path, args.out, results)
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
