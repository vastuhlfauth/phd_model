"""Section 9.9 re-estimation on EMP 2019 and ENTD 2008: CLI, figures and
report (step 11).

``python -m mobgrid.budget.emp --out docs/data/step11_budget`` extracts
the public EMP 2019 tables, rebuilds every respondent's surveyed day as
legs (``emp2019``, ``mobgrid.budget.trip_legs``), aggregates it to a
daily travel time/energy budget and runs the hypothesis test of steps
1-3 and 5 (``daily_energy``), plus the F8 robustness check added to
section 9.9. ``--survey entd2008`` runs the same pipeline on ENTD 2008
(``mobgrid.budget.entd2008``, section 9.9's "Change between 2008 and
2019"); ``--compare`` runs both and writes the 2008-2019 comparison
report instead. EMC² (step 4) and Ē_c (step 6) are out of scope.

Writes figures F1, F3 (Compendium + a KH appendix), F4-F8 to ``--out``
and a Markdown report to ``<out>.md``, mirroring ``mobgrid.energy.checks``.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mobgrid.budget import daily_energy, emp2019, entd2008, trip_legs
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
    activity_rate_kj_per_min,
    load_energy_config,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"
DEFAULT_OUT_DIR = ROOT / "docs" / "data" / "step11_budget"

#: `typejour`/`V2_TYPJOUR` day-type codes, both surveys (`docs/data/
#: entd2008.md`'s "1 weekday, 2 Saturday, 3 Sunday in both").
_DAY_TYPE_LABEL = {1: "weekdays", 2: "Saturdays", 3: "Sundays"}

#: Minimum weighted-day cell size below which a mean is left blank
#: (section 9.9's F4/F5: "with cells of fewer than 50 persons left blank").
MIN_CELL_N = 50

#: Section 9.7's flat-ground P0 reference (16 km/h, 70 kg), used by F8's
#: "P0 recalibrated (below) vs 52.5 W" robustness variant.
P0_REFERENCE_W = 52.5


def _compute_cycle_decomposition(
    con: duckdb.DuckDBPyConnection, config: EnergyConfig
) -> dict:
    """Point 3 (section 9.9, step 11 round 5): the post-fix decomposition
    of mean cycle-day energy into ride work, unloaded pedalling, stops,
    get/park and the walking trips of the same day (kJ and minutes,
    weighted by ``pond_jour``), plus the per-stop unit cost.

    Ride work, unloaded pedalling and stops are the same formula in both
    rate sets (section 9.7's mechanical/physiological terms); only
    get/park (a standing activity rate) and the day's walking legs (c0)
    differ by rate set. Every component is summed to one row per cycle
    day *before* being weighted (``pond_jour`` is a day weight, repeated
    on every leg of that day; weighting leg rows directly would count
    each day's weight once per leg). Restricted to needs-only legs
    (``emp2019.NEEDS_ONLY_WHERE_SQL``), matching the main "cycle" group's
    own, now needs-only-scoped ``total_energy_kh_kj``.
    """
    bike = config.bike
    mass = config.reference_mass_kg
    bike_total_mass = mass + bike.bike_mass_kg
    eff = bike.gross_muscular_efficiency
    p0_w = bike.power.p0_w
    unloaded_rate_kj_per_min = (
        bike.pedalling_unloaded_net_met * MET_MINUTE_KJ_PER_KG * mass
    )
    get_park_min_total = 2.0 * bike.get_park_min
    stops_per_km = bike.stops.stops_per_km
    standing_kh = activity_rate_kj_per_min(
        config.activity_rates["standing_relaxed"], "kh", mass
    )
    standing_cp = activity_rate_kj_per_min(
        config.activity_rates["standing_relaxed"], "compendium", mass
    )
    c0_kh = config.walking.c0_j_per_kg_m["kh"]
    c0_cp = config.walking.c0_j_per_kg_m["compendium"]

    rows = con.sql(f"""
        SELECT day_id, mode_group, distance_km, bike_ride_time_for_energy_s,
            duration_min, pond_jour
        FROM trip_legs
        WHERE day_id IN
            (SELECT day_id FROM day_summary WHERE day_mode_group = 'cycle')
            AND ({emp2019.NEEDS_ONLY_WHERE_SQL})
    """).fetchnumpy()
    cycle_mask = rows["mode_group"] == "cycle"
    walk_mask = rows["mode_group"] == "walk"

    ride_s = rows["bike_ride_time_for_energy_s"][cycle_mask]
    dist_km = rows["distance_km"][cycle_mask]
    speed_m_s = dist_km * 1000.0 / ride_s
    work_kj = p0_w / eff * ride_s / 1000.0
    unloaded_kj = unloaded_rate_kj_per_min * ride_s / 60.0
    n_stops = stops_per_km * dist_km
    stops_kj = 0.5 * bike_total_mass * speed_m_s**2 / eff / 1000.0 * n_stops

    walk_dist_km = rows["distance_km"][walk_mask]
    walk_kh_kj = mass * c0_kh * walk_dist_km
    walk_cp_kj = mass * c0_cp * walk_dist_km

    # One shared day_id -> day-index map (every row here belongs to a
    # cycle day, so a leg's day_id is always one of ``cycle_days``);
    # sums each component to one total per day (a day can have more than
    # one leg of the same mode) via bincount, not a Python-level loop.
    cycle_days, cycle_index = np.unique(rows["day_id"], return_inverse=True)
    n_days = len(cycle_days)
    weight_by_day = np.zeros(n_days)
    weight_by_day[cycle_index[cycle_mask]] = rows["pond_jour"][cycle_mask]
    total_weight = weight_by_day.sum()

    def _day_sum(mask: np.ndarray, values: np.ndarray) -> np.ndarray:
        return np.bincount(cycle_index[mask], weights=values, minlength=n_days)

    def _weighted_mean(mask: np.ndarray, values: np.ndarray) -> float:
        return float(np.sum(weight_by_day * _day_sum(mask, values)) / total_weight)

    mean_n_stops = _weighted_mean(cycle_mask, n_stops)
    mean_stops_kj = _weighted_mean(cycle_mask, stops_kj)

    return {
        "n_cycle_days": n_days,
        "ride_minutes": _weighted_mean(cycle_mask, ride_s) / 60.0,
        "ride_work_kj": _weighted_mean(cycle_mask, work_kj),
        "unloaded_kj": _weighted_mean(cycle_mask, unloaded_kj),
        "stops_kj": mean_stops_kj,
        "stops_per_km": stops_per_km,
        "mean_n_stops_per_day": mean_n_stops,
        "kj_per_stop": (
            mean_stops_kj / mean_n_stops if mean_n_stops > 0 else float("nan")
        ),
        "get_park_minutes": get_park_min_total,
        "get_park_kh_kj": standing_kh * get_park_min_total,
        "get_park_cp_kj": standing_cp * get_park_min_total,
        "walk_minutes": _weighted_mean(walk_mask, rows["duration_min"][walk_mask]),
        "walk_kh_kj": _weighted_mean(walk_mask, walk_kh_kj),
        "walk_cp_kj": _weighted_mean(walk_mask, walk_cp_kj),
    }


def _compute_motive_decomposition(
    con: duckdb.DuckDBPyConnection, mode_group: str
) -> list[tuple]:
    """Section 9.9 point 1 follow-up ("decompose energy per motive"): one
    row per ``MOT_SEQ_COMPL`` motive among ``mode_group``'s trips -- n,
    weighted n (`pond_jour`, trip-weighted, as elsewhere in this report),
    weighted energy (both rate sets) and mean distance/duration -- sorted
    by weighted energy, largest first."""
    return con.sql(f"""
        SELECT motive, count(*) AS n, sum(pond_jour) AS weighted_n,
            sum(pond_jour * energy_kh_kj) AS energy_kh_sum,
            sum(pond_jour * energy_cp_kj) AS energy_cp_sum,
            avg(distance_km) AS mean_distance_km, avg(duration_min) AS mean_duration_min
        FROM trip_legs
        WHERE mode_group = '{mode_group}' AND energy_kh_kj IS NOT NULL
        GROUP BY 1 ORDER BY energy_kh_sum DESC
    """).fetchall()


def _compute_motive_energy_matrix(
    con: duckdb.DuckDBPyConnection, *, where_sql: str = "TRUE"
) -> tuple[list[str], list[float], np.ndarray]:
    """(mode_groups, top_level_motives, matrix): weighted KH energy sum
    per (mode_group, top-level motive) cell, for the "energy by motive,
    all modes" figure (section 9.9 point 1 follow-up, generalising the
    cycling-only motive table to every mode). Top-level (``floor``) only
    -- a dozen or so sub-codes per mode would make an unreadable stacked
    bar legend. ``where_sql`` filters ``trip_legs`` directly (e.g.
    ``emp2019.NEEDS_ONLY_WHERE_SQL``, for the "final decomposition"
    panel): unlike every other needs-only query in this module, this one
    is never joined through ``day_summary``, so it needs its own filter."""
    rows = con.sql(f"""
        SELECT mode_group, floor(motive) AS top_motive,
            sum(pond_jour * energy_kh_kj) AS energy_kh_sum
        FROM trip_legs
        WHERE energy_kh_kj IS NOT NULL AND motive IS NOT NULL AND ({where_sql})
        GROUP BY 1, 2
    """).fetchall()
    mode_groups = sorted({row[0] for row in rows})
    top_motives = sorted({row[1] for row in rows})
    matrix = np.zeros((len(mode_groups), len(top_motives)))
    for mode_group, top_motive, energy_kh_sum in rows:
        matrix[mode_groups.index(mode_group), top_motives.index(top_motive)] = (
            energy_kh_sum
        )
    return mode_groups, top_motives, matrix


def _weighted_query(
    con: duckdb.DuckDBPyConnection, sql: str
) -> tuple[int, float, float, float]:
    """(n, weighted_n, weighted_mean_kh, weighted_mean_cp) of a query
    selecting (weight, energy_kh, energy_cp, time_min) rows."""
    rows = con.sql(sql).fetchnumpy()
    if len(rows["weight"]) == 0:
        return 0, 0.0, float("nan"), float("nan")
    mean_kh, _ = daily_energy.weighted_mean_variance(rows["weight"], rows["energy_kh"])
    mean_cp, _ = daily_energy.weighted_mean_variance(rows["weight"], rows["energy_cp"])
    return len(rows["weight"]), float(rows["weight"].sum()), mean_kh, mean_cp


def _day_rows(con: duckdb.DuckDBPyConnection) -> dict:
    """Fetch every classified-day column needed by the figures/report."""
    return con.sql(
        "SELECT day_mode_group, population_category, home_density, "
        "income_quintile, ident_men, typejour, "
        "pond_jour, total_time_min, total_energy_kh_kj, total_energy_cp_kj, "
        "trips_per_day FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()


def _group_stats(
    days: dict, group_column: str, *, n_reps: int, seed: int
) -> list[daily_energy.GroupStats]:
    return daily_energy.bootstrap_group_stats(
        days[group_column],
        days["ident_men"],
        days["pond_jour"],
        days["total_time_min"],
        days["total_energy_kh_kj"],
        days["total_energy_cp_kj"],
        n_reps=n_reps,
        seed=seed,
    )


def _category_density_stats(
    days: dict, *, n_reps: int, seed: int
) -> dict[tuple[str, str], daily_energy.GroupStats]:
    """Population category x density class, combined into one group key
    for `bootstrap_group_stats` (section 9.9, point 2a); keyed back out
    to ``(category, density)`` tuples."""
    return _category_by_key_stats(
        days, "home_density", n_reps=n_reps, seed=seed
    )


def _category_by_key_stats(
    days: dict, key_column: str, *, n_reps: int, seed: int
) -> dict[tuple[str, str], daily_energy.GroupStats]:
    """Population category x ``key_column`` (``home_density`` or
    ``income_quintile``), combined into one group key for
    `bootstrap_group_stats` (section 9.9 point 2a/3's income update);
    keyed back out to ``(category, key)`` tuples. Generalises
    ``_category_density_stats`` to any second grouping key."""
    combined = np.array(
        [
            f"{c}||{k}"
            for c, k in zip(days["population_category"], days[key_column], strict=False)
        ]
    )
    stats = daily_energy.bootstrap_group_stats(
        combined,
        days["ident_men"],
        days["pond_jour"],
        days["total_time_min"],
        days["total_energy_kh_kj"],
        days["total_energy_cp_kj"],
        n_reps=n_reps,
        seed=seed,
    )
    result = {}
    for s in stats:
        category, key = s.group.split("||", 1)
        result[(category, key)] = s
    return result


def _density_constancy_summary(
    category_density_stats: dict[tuple[str, str], daily_energy.GroupStats],
) -> list[tuple[str, float, float, float]]:
    """Section 9.9's constancy summary: within each population category,
    the dense/very_sparse ratio, the highest/lowest-density-class ratio
    and the coefficient of variation across classes, mean daily time
    (cells of fewer than `MIN_CELL_N` persons excluded)."""
    return _constancy_summary(
        category_density_stats, named_pair=("dense", "very_sparse")
    )


def _income_constancy_summary(
    category_income_stats: dict[tuple[str, str], daily_energy.GroupStats],
) -> list[tuple[str, float, float, float]]:
    """Section 9.9's income constancy summary: within each population
    category, the highest (q5) / lowest (q1) quintile ratio and the
    coefficient of variation across quintiles, mean daily time (cells of
    fewer than `MIN_CELL_N` persons excluded; `'unknown'` is not a
    quintile, so it is excluded from both)."""
    return _constancy_summary(category_income_stats, named_pair=("q5", "q1"))


def _constancy_summary(
    category_key_stats: dict[tuple[str, str], daily_energy.GroupStats],
    *,
    named_pair: tuple[str, str],
) -> list[tuple[str, float, float, float]]:
    """Generic constancy summary (section 9.9's density and income
    updates): within each population category, ``named_pair``'s ratio
    (e.g. dense/very_sparse, or q5/q1), the highest/lowest-key ratio and
    the coefficient of variation across keys, mean daily time (cells of
    fewer than `MIN_CELL_N` persons excluded). `'unknown'` keys (an
    unrecognised density code, or a missing/refused income) are excluded
    from the summary, as they are not part of the ordered scale."""
    rows = []
    for category in daily_energy.POPULATION_CATEGORIES:
        present = {
            key: s
            for (cat, key), s in category_key_stats.items()
            if cat == category and s.n >= MIN_CELL_N and key != "unknown"
        }
        if not present:
            rows.append((category, float("nan"), float("nan"), float("nan")))
            continue
        values = {key: s.mean_time_min for key, s in present.items()}
        named_ratio = (
            values[named_pair[0]] / values[named_pair[1]]
            if named_pair[0] in values and named_pair[1] in values
            else float("nan")
        )
        arr = np.array(list(values.values()))
        ratio = arr.max() / arr.min()
        cv = arr.std() / arr.mean()
        rows.append((category, named_ratio, ratio, cv))
    return rows


def _scalar_by_group(
    days: dict, group_column: str, value: np.ndarray, *, n_reps: int, seed: int
) -> list[daily_energy.ScalarGroupStats]:
    """Mean (with 95% bootstrap CI), median and n of ``value`` (e.g.
    ``total_time_min``, trips/day, minutes/trip) by ``days[group_column]``
    (section 9.9's time-parity update: "the same treatment energy
    already has"). Excludes the `'unknown'` group (population category
    or income), as elsewhere in this report."""
    mask = days[group_column] != "unknown"
    return daily_energy.bootstrap_scalar_group_stats(
        days[group_column][mask],
        days["ident_men"][mask],
        days["pond_jour"][mask],
        value[mask],
        n_reps=n_reps,
        seed=seed,
    )


def _scalar_by_combined_key(
    days: dict, key_column: str, value: np.ndarray, *, n_reps: int, seed: int
) -> dict[tuple[str, str], daily_energy.ScalarGroupStats]:
    """Population category x ``key_column`` (``home_density`` or
    ``income_quintile``), combined into one group key for
    ``bootstrap_scalar_group_stats``; keyed back out to ``(category,
    key)`` tuples (section 9.9's trips-per-day/minutes-per-trip and
    time-with-CI tables)."""
    combined = np.array(
        [
            f"{c}||{k}"
            for c, k in zip(days["population_category"], days[key_column], strict=False)
        ]
    )
    stats = daily_energy.bootstrap_scalar_group_stats(
        combined,
        days["ident_men"],
        days["pond_jour"],
        value,
        n_reps=n_reps,
        seed=seed,
    )
    result = {}
    for s in stats:
        category, key = s.group.split("||", 1)
        result[(category, key)] = s
    return result


def _build_base(
    con: duckdb.DuckDBPyConnection,
    survey,
    config: EnergyConfig,
    *,
    where_sql: str = "TRUE",
    density_source: str | None = None,
) -> None:
    survey.build_trip_legs(con, config, density_source=density_source)
    daily_energy.create_day_summary(con, where_sql=where_sql)


def run(
    out_dir: Path,
    survey=emp2019,
    data_path: Path | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    n_reps: int = 200,
    seed: int = 0,
    density_source: str | None = None,
) -> dict:
    """Run the full re-estimation; return every computed statistic and
    figure path, used by ``write_markdown`` and the test suite.

    Survey-agnostic (``survey`` is ``mobgrid.budget.emp2019`` or
    ``mobgrid.budget.entd2008``, both exposing the same
    ``extract_tables``/``register_views``/``build_trip_legs``/
    ``non_traveler_summary`` interface, section 9.9's "Change between
    2008 and 2019"): every table and figure below reads ``trip_legs``/
    ``day_summary``, built identically from either survey's own
    ``trips_norm``. ``density_source`` defaults to the survey's own
    ``DEFAULT_DENSITY_SOURCE`` ('grid' for EMP 2019, 'proxy' for ENTD
    2008, which has no density grid). Terminal legs use
    ``survey.build_trip_legs``'s own default (``'declared'``, section
    9.9's 27 October 2026 decision; see
    ``trip_legs.TERMINAL_LEGS_VARIANTS``) -- not yet a parameter of this
    function (step 11, part A: only ``trip_legs.build_trip_legs`` itself
    gained the new parameter; this report/figure pipeline is updated in
    part B).

    Section 9.9's scope (2026-10-20 project decision): every table and
    figure below is restricted to commuting/needs-fulfilment travel
    (``emp2019.NEEDS_ONLY_WHERE_SQL`` excludes sport/stroll/promenade-
    destination trips -- section 9.9 point 1 follow-up), the report's
    one base filter, not an optional variant. A separate, diagnostic
    pass on the full (unfiltered-by-motive) dataset provides the
    evidence for this scope decision (the motive breakdown, F9) and a
    few checks that must *not* be scoped to it (non-traveller share,
    data-quality corrections, children-as-car-drivers).
    """
    config = load_energy_config(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_path or survey.DEFAULT_DATA_PATH
    density_source = density_source or survey.DEFAULT_DENSITY_SOURCE

    con = duckdb.connect()
    # A custom (typically tmp-scoped) `data_path` gets its own, equally
    # tmp-scoped extraction directory: the default extraction directory
    # under `data/interim/` is cached across runs (resumable) *by file
    # name*, not by `data_path`, so reusing it for a different archive
    # (e.g. a test's synthetic one) would silently serve stale,
    # previously extracted CSVs instead.
    interim_dir = (
        None
        if data_path == survey.DEFAULT_DATA_PATH
        else data_path.parent / f"_interim_{survey.__name__.rsplit('.', 1)[-1]}_csv"
    )
    csv_paths = survey.extract_tables(data_path, interim_dir)
    survey.register_views(con, csv_paths)

    # ENTD 2008 only (section 9.9's "Quirks"): fill rate and mean change
    # of the undocumented `distcor`/`v2_mduree` correction columns.
    quirk_fill_rates = (
        survey.quirk_fill_rates(con) if hasattr(survey, "quirk_fill_rates") else None
    )

    _build_base(
        con,
        survey,
        config,
        where_sql=emp2019.NEEDS_ONLY_WHERE_SQL,
        density_source=density_source,
    )
    days = _day_rows(con)
    n_days_within_scope = con.sql("SELECT count(*) FROM day_summary").fetchone()[0]

    # Children as car drivers (round 4's point 4): the mtp code (already
    # harmonised to EMP 2019's, `trips_norm`) behind every
    # day_mode_group='car_driver' day of a children_6_17 respondent.
    # Computed here, against the still needs-only-scoped `day_summary`/
    # `trip_legs` (same scope as `mode_stats`'s table above, not the
    # later full, pre-exclusion `day_summary` rebuild used by the
    # motive-share diagnostics below): otherwise the two reported
    # figures silently differed (56/148 full-scope days vs. 50/140
    # needs-only, in the table).
    children_car_driver_mtp = con.sql(f"""
        SELECT mtp, count(*), min(age), max(age)
        FROM trip_legs
        WHERE mode_group = 'car_driver' AND population_category = 'children_6_17'
            AND ({emp2019.NEEDS_ONLY_WHERE_SQL})
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    children_car_driver_n = con.sql("""
        SELECT count(*) FROM day_summary
        WHERE day_mode_group = 'car_driver' AND population_category = 'children_6_17'
    """).fetchone()[0]

    # Sample flow (section 9.9, "Change between 2008 and 2019": persons
    # and days kept apart), replacing the old "Sample:" line's
    # `n_days + non_traveler_n` reconstruction of "respondents" (which
    # silently dropped every respondent who had a trip but whose day
    # fell out of scope, or ended with null energy, between "days with
    # trips" and `n_days` here). Days-with-trips/with-energy are read
    # off a full (pre-motive-scope) `day_summary` rebuild, then the view
    # is rebuilt back to the needs-only scope so every later
    # computation (this function's own, and the diagnostics below) sees
    # what it expects.
    n_respondents = survey.respondent_n(con)
    daily_energy.create_day_summary(con, where_sql="TRUE")
    n_days_with_trips = con.sql("SELECT count(*) FROM day_summary").fetchone()[0]
    n_days_with_energy = con.sql(
        "SELECT count(*) FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchone()[0]
    days_with_trips_by_type = con.sql(
        "SELECT typejour, count(*) FROM day_summary GROUP BY 1 ORDER BY 1"
    ).fetchall()
    daily_energy.create_day_summary(con, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL)

    mode_stats = _group_stats(days, "day_mode_group", n_reps=n_reps, seed=seed)
    population_stats = _group_stats(
        days, "population_category", n_reps=n_reps, seed=seed
    )
    density_stats = _group_stats(days, "home_density", n_reps=n_reps, seed=seed)
    category_density_stats = _category_density_stats(days, n_reps=n_reps, seed=seed)
    density_constancy_summary = _density_constancy_summary(category_density_stats)

    # Section 9.9's income update: household income per consumption
    # unit, in quintiles computed within this survey
    # (`trip_legs.weighted_quintile_view_sql`); the same category x key
    # table/constancy-summary machinery as density, plus a time-with-CI
    # column giving time the same treatment energy already has.
    income_stats = _group_stats(days, "income_quintile", n_reps=n_reps, seed=seed)
    category_income_stats = _category_by_key_stats(
        days, "income_quintile", n_reps=n_reps, seed=seed
    )
    income_constancy_summary = _income_constancy_summary(category_income_stats)
    category_density_time_ci = _scalar_by_combined_key(
        days, "home_density", days["total_time_min"], n_reps=n_reps, seed=seed
    )
    category_income_time_ci = _scalar_by_combined_key(
        days, "income_quintile", days["total_time_min"], n_reps=n_reps, seed=seed
    )

    mean_kh, var_kh = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_kh_kj"]
    )
    mean_cp, var_cp = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_cp_kj"]
    )
    gamma_kh = daily_energy.gamma_moments_fit(mean_kh, var_kh)
    gamma_cp = daily_energy.gamma_moments_fit(mean_cp, var_cp)
    # Overall (all groups combined) weighted mean daily time, alongside
    # `mean_kh`/`mean_cp` (used by `--compare`'s figure, section 9.9's
    # "Outputs of the re-estimation": global means next to the group
    # breakdown).
    mean_time_min = float(
        np.sum(days["pond_jour"] * days["total_time_min"]) / days["pond_jour"].sum()
    )

    by_group = {s.group: s for s in mode_stats}
    kh_means = [
        by_group[g].mean_energy_kh_kj
        for g in daily_energy.DAY_MODE_GROUPS
        if g in by_group
    ]
    cp_means = [
        by_group[g].mean_energy_cp_kj
        for g in daily_energy.DAY_MODE_GROUPS
        if g in by_group
    ]
    ratio_kh = max(kh_means) / min(kh_means) if kh_means else float("nan")
    ratio_cp = max(cp_means) / min(cp_means) if cp_means else float("nan")

    v0_overall = daily_energy.calibrate_v0_kmh(
        con, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL
    )[0]
    v0_by_age_band = daily_energy.calibrate_v0_kmh(
        con, by_age_band=True, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL
    )
    p0_overall = daily_energy.calibrate_p0(
        con, config, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL
    )[0]
    p0_by_age_band = daily_energy.calibrate_p0(
        con, config, by_age_band=True, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL
    )

    trips_mean, trips_ci = daily_energy.bootstrap_mean_ci(
        days["ident_men"],
        days["pond_jour"],
        days["trips_per_day"].astype(float),
        n_reps=n_reps,
        seed=seed,
    )
    trips_by_population = _trips_per_day_by_group(
        days, "population_category", n_reps=n_reps, seed=seed
    )
    trips_by_density = _trips_per_day_by_group(
        days, "home_density", n_reps=n_reps, seed=seed
    )
    # Section 9.9 point 2's trips-per-day/minutes-per-trip split: daily
    # time = trips/day x minutes/trip, so a constant daily time can come
    # from constant trips or from trips that compensate each other.
    # Scalar (mean+CI+median) versions of the marginals, for the new
    # tables (`trips_by_population`/`trips_by_density` above stay in
    # their original (group, n, mean, ci) tuple form, used only by the
    # F1 figure).
    minutes_per_trip = days["total_time_min"] / days["trips_per_day"]
    trips_per_day_float = days["trips_per_day"].astype(float)
    trips_by_density_scalar = _scalar_by_group(
        days, "home_density", trips_per_day_float, n_reps=n_reps, seed=seed
    )
    trips_by_income = _scalar_by_group(
        days, "income_quintile", trips_per_day_float, n_reps=n_reps, seed=seed
    )
    minutes_per_trip_by_population = _scalar_by_group(
        days, "population_category", minutes_per_trip, n_reps=n_reps, seed=seed
    )
    minutes_per_trip_by_density = _scalar_by_group(
        days, "home_density", minutes_per_trip, n_reps=n_reps, seed=seed
    )
    minutes_per_trip_by_income = _scalar_by_group(
        days, "income_quintile", minutes_per_trip, n_reps=n_reps, seed=seed
    )
    trips_by_category_density = _scalar_by_combined_key(
        days, "home_density", trips_per_day_float, n_reps=n_reps, seed=seed
    )
    trips_by_category_income = _scalar_by_combined_key(
        days, "income_quintile", trips_per_day_float, n_reps=n_reps, seed=seed
    )
    minutes_per_trip_by_category_density = _scalar_by_combined_key(
        days, "home_density", minutes_per_trip, n_reps=n_reps, seed=seed
    )
    minutes_per_trip_by_category_income = _scalar_by_combined_key(
        days, "income_quintile", minutes_per_trip, n_reps=n_reps, seed=seed
    )
    motive_by_population = _trips_by_group_and_motive(con, "population_category")
    motive_by_density = _trips_by_group_and_motive(con, "home_density")

    # Section 9.9 point 2's per-person budget: P(out) x T(out), days
    # without trips included, by population category and by category x
    # density/income. Weekday only in both surveys (comparable with
    # 2008); EMP 2019 also reports the all-week budget (its IMMODEP
    # questions cover the whole week; ENTD 2008's weekend eligibility is
    # unverified, so it stays weekday-only, per the user's instruction).
    person = _person_universe(survey, con, density_source)
    (
        person_budget_weekday_population,
        person_budget_weekday_category_density,
        person_budget_weekday_category_income,
    ) = _person_budget_tables(
        person,
        days,
        value=days["total_time_min"],
        day_types=("weekday",),
        day_type_weight=None,
        n_reps=n_reps,
        seed=seed,
    )
    if person["day_types"] == ("weekday", "saturday", "sunday"):
        (
            person_budget_all_week_population,
            person_budget_all_week_category_density,
            person_budget_all_week_category_income,
        ) = _person_budget_tables(
            person,
            days,
            value=days["total_time_min"],
            day_types=person["day_types"],
            day_type_weight=daily_energy.DAY_TYPE_WEIGHT,
            n_reps=n_reps,
            seed=seed,
        )
    else:
        person_budget_all_week_population = None
        person_budget_all_week_category_density = None
        person_budget_all_week_category_income = None

    # Car passengers: household vs carpool, and the walking trips of
    # passenger days (section 9.9, "Outputs of the re-estimation").
    passenger_trip_stats = {}
    for group in ("car_passenger_household", "car_passenger_carpool"):
        passenger_trip_stats[group] = _weighted_query(
            con,
            "SELECT pond_jour AS weight, energy_kh_kj AS energy_kh, "
            "energy_cp_kj AS energy_cp, duration_min AS time_min FROM trip_legs "
            f"WHERE mode_group = '{group}' AND ({emp2019.NEEDS_ONLY_WHERE_SQL})",
        )
    carpool_n, carpool_household_n, carpool_share = con.sql(f"""
        SELECT
            sum(CASE WHEN mode_group = 'car_passenger_carpool'
                THEN pond_jour ELSE 0 END),
            sum(CASE WHEN mode_group IN
                ('car_passenger_household', 'car_passenger_carpool')
                THEN pond_jour ELSE 0 END),
            sum(CASE WHEN mode_group = 'car_passenger_carpool'
                THEN pond_jour ELSE 0 END)
                / sum(CASE WHEN mode_group IN
                    ('car_passenger_household', 'car_passenger_carpool')
                    THEN pond_jour ELSE 0 END)
        FROM trip_legs WHERE ({emp2019.NEEDS_ONLY_WHERE_SQL})
    """).fetchone()
    walk_trips_by_day_group = dict(
        con.sql(f"""
        SELECT d.day_mode_group,
            sum(CASE WHEN t.mode_group = 'walk' THEN 1 ELSE 0 END) * 1.0
                / count(DISTINCT d.day_id)
        FROM day_summary d
        JOIN trip_legs t ON t.day_id = d.day_id
        WHERE d.day_mode_group IN
            ('car_driver', 'car_passenger_household', 'car_passenger_carpool')
            AND ({emp2019.NEEDS_ONLY_WHERE_SQL})
        GROUP BY d.day_mode_group
    """).fetchall()
    )

    # F8 robustness (section 9.9): re-run the pipeline under each
    # variant, always within the needs-only scope.
    robustness_rows, robustness_ci = _run_robustness(
        con,
        survey,
        config,
        n_reps=n_reps,
        seed=seed,
        base_where_sql=emp2019.NEEDS_ONLY_WHERE_SQL,
        density_source=density_source,
    )
    # Restore the needs-only base for the figures below.
    daily_energy.create_day_summary(con, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL)

    # Cycle group, weekdays only (kept from round 4's point 3), same
    # needs-only scope.
    daily_energy.create_day_summary(
        con, where_sql=f"({emp2019.NEEDS_ONLY_WHERE_SQL}) AND (typejour = 1)"
    )
    days_weekday = _day_rows(con)
    cycle_weekday_stats = next(
        (
            s
            for s in _group_stats(
                days_weekday, "day_mode_group", n_reps=n_reps, seed=seed
            )
            if s.group == "cycle"
        ),
        None,
    )
    daily_energy.create_day_summary(con, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL)

    cycle_decomposition = _compute_cycle_decomposition(con, config)

    f4_paths, f4_panels = _figure_f4_mean_by_mode(
        con, out_dir, n_reps=n_reps, seed=seed
    )
    figures = [
        _figure_f1_trips_per_day(
            days,
            trips_mean,
            trips_by_population,
            trips_by_density,
            motive_by_population,
            motive_by_density,
            out_dir,
        ),
        _figure_scalar_by_category_key(
            trips_by_category_density,
            trips_by_category_income,
            title="F1b. Trips per day by population category x density "
            "class / income quintile (95% CI, section 9.9 point 2)",
            ylabel="Mean trips per day",
            filename="f01b_trips_per_day_by_category.png",
            out_dir=out_dir,
        ),
        _figure_scalar_by_category_key(
            minutes_per_trip_by_category_density,
            minutes_per_trip_by_category_income,
            title="F1c. Minutes per trip by population category x density "
            "class / income quintile (95% CI, section 9.9 point 2)",
            ylabel="Mean minutes per trip",
            filename="f01c_minutes_per_trip_by_category.png",
            out_dir=out_dir,
        ),
        *_figure_f2_time_density_by_category(con, out_dir),
        *_figure_f3_energy_density(con, out_dir),
        *f4_paths,
        _figure_f5_heatmaps(con, out_dir),
        _figure_f5_time_heatmaps(con, out_dir),
        _figure_f6_v0_p0(v0_by_age_band, p0_by_age_band, config, out_dir),
        _figure_f7_passengers(passenger_trip_stats, walk_trips_by_day_group, out_dir),
        _figure_f8_robustness(robustness_ci, out_dir),
        _figure_f10_constancy(
            category_density_time_ci,
            category_income_time_ci,
            person_budget_weekday_category_density,
            person_budget_weekday_category_income,
            out_dir,
        ),
    ]

    # ---- Diagnostics: full, unfiltered-by-motive dataset -- the
    # evidence behind the needs-only scope above, plus checks that must
    # *not* be scoped to it. ----
    daily_energy.create_day_summary(con)

    # Section 9.9 point 1 follow-up: trip/energy share of the excluded,
    # non-needs motives, by main-mode group (justifies the scope
    # decision above), plus the all-modes energy-by-motive figure (F9).
    excluded_codes_sql = ", ".join(
        f"{code:g}" for code in emp2019.NEEDS_EXCLUDED_MOTIVE_CODES
    )
    excluded_trip_shares = con.sql(f"""
        SELECT d.day_mode_group,
            sum(t.pond_jour * (t.motive IN ({excluded_codes_sql}))::int)
                / sum(t.pond_jour) AS trip_share,
            count(*) FILTER (WHERE t.motive IN ({excluded_codes_sql})) AS n_excluded,
            count(*) AS n_total
        FROM trip_legs t JOIN day_summary d ON d.day_id = t.day_id
        WHERE d.total_energy_kh_kj IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    excluded_energy_shares = con.sql(f"""
        WITH excluded_leg_energy AS (
            SELECT day_id,
                sum(energy_kh_kj)
                    FILTER (WHERE motive IN ({excluded_codes_sql})) AS excluded_kh,
                sum(energy_cp_kj)
                    FILTER (WHERE motive IN ({excluded_codes_sql})) AS excluded_cp
            FROM trip_legs GROUP BY 1
        )
        SELECT d.day_mode_group,
            sum(d.pond_jour * coalesce(e.excluded_kh, 0))
                / sum(d.pond_jour * d.total_energy_kh_kj) AS excluded_energy_share_kh,
            sum(d.pond_jour * coalesce(e.excluded_cp, 0))
                / sum(d.pond_jour * d.total_energy_cp_kj) AS excluded_energy_share_cp
        FROM day_summary d LEFT JOIN excluded_leg_energy e ON e.day_id = d.day_id
        WHERE d.total_energy_kh_kj IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """).fetchall()

    motive_matrix_before = _compute_motive_energy_matrix(con)
    motive_matrix_after = _compute_motive_energy_matrix(
        con, where_sql=emp2019.NEEDS_ONLY_WHERE_SQL
    )
    figures.append(
        _figure_f9_motive_energy(motive_matrix_before, motive_matrix_after, out_dir)
    )

    # Point 2: data-quality correction counts (upper-bound speed flags,
    # corrected by mode's median speed, not dropped).
    quality_counts = con.sql("""
        SELECT mode_group,
            count(*) FILTER (WHERE speed_flagged_upper) AS n_corrected,
            count(*) AS n_total
        FROM trip_legs GROUP BY 1 ORDER BY 1
    """).fetchall()

    # Declared walking/waiting minutes (`MTEMPSMAP`/`MTPSATTENT`, ENTD
    # 2008's converted equivalents) against the modelled terminal-leg
    # minutes, by mode group (section 9.9, step 1's closing sentence,
    # and "Outputs of the re-estimation": "declared walking and waiting
    # times against the modelled terminal legs, by mode group"); a check
    # only -- neither is used to build the legs themselves. The modelled
    # walk is mode-specific, matching the energy formula (`trip_legs.
    # build_trip_legs`): car's walk-to/from-car only (`access_walk_ori/
    # des_min` is a PT/train-only concept, computed for every row
    # regardless of mode, but not part of car's own energy -- adding it
    # here used to double the car figure, 17.6-19.2 modelled minutes
    # against a 9/10-minute default cap).
    declared_vs_modelled_walk_wait = con.sql("""
        SELECT mode_group,
            avg(declared_walk_min) AS declared_walk_min,
            avg(declared_wait_min) AS declared_wait_min,
            avg(CASE
                WHEN mode_group IN
                    ('car_driver', 'car_passenger_household',
                     'car_passenger_carpool')
                    THEN coalesce(walk_to_car_min, 0) + coalesce(walk_from_car_min, 0)
                WHEN mode_group IN ('urban_pt', 'train')
                    THEN coalesce(access_walk_ori_min, 0)
                        + coalesce(access_walk_des_min, 0)
            END) AS modelled_walk_min,
            avg(wait_min) AS modelled_wait_min,
            count(*) AS n
        FROM trip_legs
        WHERE mode_group IN
            ('car_driver', 'car_passenger_household', 'car_passenger_carpool',
             'urban_pt', 'train')
        GROUP BY 1 ORDER BY 1
    """).fetchall()

    # Cycling energy by motive (section 9.9 point 1 follow-up, user note:
    # "7.6,7.7,7.8 might have large impact on bike"), full dataset.
    cycle_motive_decomposition = _compute_motive_decomposition(con, "cycle")

    non_traveler = survey.non_traveler_summary(con)
    # Weekday surveyed-day mix among travellers, now read directly from
    # `day_summary.typejour` (one row per day, no join needed), as a
    # *share* of the total (previously a raw `sum(pond_jour)` fed
    # straight into a `.1%` format, printing e.g. "2500207431.3%").
    traveler_day_type_weight = dict(
        con.sql("""
        SELECT typejour, sum(pond_jour) FROM day_summary
        WHERE total_energy_kh_kj IS NOT NULL GROUP BY typejour
    """).fetchall()
    )
    traveler_day_type_total = sum(traveler_day_type_weight.values())
    traveler_day_type_share = {
        day_type: weight / traveler_day_type_total
        for day_type, weight in traveler_day_type_weight.items()
    }

    return {
        "config": config,
        "survey_name": survey.SURVEY_NAME,
        "density_source": density_source,
        "n_days": len(days["day_mode_group"]),
        "mode_stats": mode_stats,
        "population_stats": population_stats,
        "density_stats": density_stats,
        "category_density_stats": category_density_stats,
        "density_constancy_summary": density_constancy_summary,
        "income_stats": income_stats,
        "category_income_stats": category_income_stats,
        "income_constancy_summary": income_constancy_summary,
        "category_density_time_ci": category_density_time_ci,
        "category_income_time_ci": category_income_time_ci,
        "trips_by_income": trips_by_income,
        "trips_by_density_scalar": trips_by_density_scalar,
        "minutes_per_trip_by_population": minutes_per_trip_by_population,
        "minutes_per_trip_by_density": minutes_per_trip_by_density,
        "minutes_per_trip_by_income": minutes_per_trip_by_income,
        "trips_by_category_density": trips_by_category_density,
        "trips_by_category_income": trips_by_category_income,
        "minutes_per_trip_by_category_density": minutes_per_trip_by_category_density,
        "minutes_per_trip_by_category_income": minutes_per_trip_by_category_income,
        "person_budget_weekday_population": person_budget_weekday_population,
        "person_budget_weekday_category_density": (
            person_budget_weekday_category_density
        ),
        "person_budget_weekday_category_income": (
            person_budget_weekday_category_income
        ),
        "person_budget_all_week_population": person_budget_all_week_population,
        "person_budget_all_week_category_density": (
            person_budget_all_week_category_density
        ),
        "person_budget_all_week_category_income": (
            person_budget_all_week_category_income
        ),
        "mean_kh": mean_kh,
        "mean_cp": mean_cp,
        "mean_time_min": mean_time_min,
        "gamma_kh": gamma_kh,
        "gamma_cp": gamma_cp,
        "ratio_kh": ratio_kh,
        "ratio_cp": ratio_cp,
        "v0_overall": v0_overall,
        "v0_by_age_band": v0_by_age_band,
        "p0_overall": p0_overall,
        "p0_by_age_band": p0_by_age_band,
        "trips_mean": trips_mean,
        "trips_ci": trips_ci,
        "passenger_trip_stats": passenger_trip_stats,
        "carpool_n": carpool_n,
        "carpool_household_n": carpool_household_n,
        "carpool_share": carpool_share,
        "walk_trips_by_day_group": walk_trips_by_day_group,
        "f4_panels": f4_panels,
        "robustness_rows": robustness_rows,
        "excluded_trip_shares": excluded_trip_shares,
        "excluded_energy_shares": excluded_energy_shares,
        "quality_counts": quality_counts,
        "declared_vs_modelled_walk_wait": declared_vs_modelled_walk_wait,
        "cycle_decomposition": cycle_decomposition,
        "cycle_motive_decomposition": cycle_motive_decomposition,
        "cycle_weekday_stats": cycle_weekday_stats,
        "children_car_driver_mtp": children_car_driver_mtp,
        "children_car_driver_n": children_car_driver_n,
        "quirk_fill_rates": quirk_fill_rates,
        "n_respondents": n_respondents,
        "n_days_with_trips": n_days_with_trips,
        "n_days_with_energy": n_days_with_energy,
        "n_days_within_scope": n_days_within_scope,
        "days_with_trips_by_type": days_with_trips_by_type,
        "non_traveler_n": non_traveler["n"],
        "non_traveler_share_weighted": non_traveler["share_weighted"],
        "non_traveler_share_unweighted": non_traveler["share_unweighted"],
        "non_traveler_mimmosem_match": non_traveler["mimmosem_match"],
        "traveler_day_type_share": traveler_day_type_share,
        # Weekday-only day arrays (section 9.9's 2008-2019 comparison,
        # comparable in both surveys): used by `run_compare`'s
        # `bootstrap_diff_ci` (ENTD 2008 describes only one weekday per
        # respondent; EMP 2019's `typejour` marks the same reference
        # weekday).
        "weekday_days": {
            key: days[key][days["typejour"] == 1]
            for key in ("ident_men", "pond_jour", "total_time_min",
                        "population_category", "trips_per_day")
        },
        "figures": figures,
    }


def _run_robustness(
    con: duckdb.DuckDBPyConnection,
    survey,
    config: EnergyConfig,
    *,
    n_reps: int,
    seed: int,
    base_where_sql: str = "TRUE",
    density_source: str | None = None,
) -> tuple[list[daily_energy.RobustnessRow], dict[str, list[daily_energy.GroupStats]]]:
    """F8: re-run the pipeline under each robustness variant (section 9.9).

    ``base_where_sql`` is ANDed into every variant's own ``day_summary``
    filter (the needs-only scope, for the whole sweep).
    Returns the compressed ratio/CV table (every variant, scope and
    statistic) and, for the base case and the two terminal-leg extremes,
    full bootstrap group stats for the figure ("group means +/- CI for
    the base case and the extremes").
    """
    rows: list[daily_energy.RobustnessRow] = []
    ci_stats: dict[str, list[daily_energy.GroupStats]] = {}

    def _day_rows_f8() -> dict:
        return con.sql(
            "SELECT day_mode_group, ident_men, pond_jour, total_time_min, "
            "total_energy_kh_kj, total_energy_cp_kj FROM day_summary "
            "WHERE total_energy_kh_kj IS NOT NULL"
        ).fetchnumpy()

    def _row(name: str, want_ci: bool) -> None:
        rows_data = _day_rows_f8()
        for scope, groups_of_interest in (
            ("full", daily_energy.F8_ROBUSTNESS_GROUPS),
            ("core", daily_energy.F8_CORE_ROBUSTNESS_GROUPS),
        ):
            for statistic in ("mean", "median"):
                rows.append(
                    daily_energy.robustness_row(
                        name,
                        rows_data["day_mode_group"],
                        rows_data["pond_jour"],
                        rows_data["total_time_min"],
                        rows_data["total_energy_kh_kj"],
                        rows_data["total_energy_cp_kj"],
                        scope=scope,
                        groups_of_interest=groups_of_interest,
                        statistic=statistic,
                    )
                )
        if want_ci:
            ci_stats[name] = daily_energy.bootstrap_group_stats(
                rows_data["day_mode_group"],
                rows_data["ident_men"],
                rows_data["pond_jour"],
                rows_data["total_time_min"],
                rows_data["total_energy_kh_kj"],
                rows_data["total_energy_cp_kj"],
                n_reps=n_reps,
                seed=seed,
            )

    def _summary(extra_where: str = "TRUE") -> None:
        daily_energy.create_day_summary(
            con, where_sql=f"({base_where_sql}) AND ({extra_where})"
        )

    # Terminal-legs variants (section 9.9, 27 October 2026 decision):
    # 'declared' (also the base case: every other table/figure in this
    # report uses it, since it is `trip_legs.build_trip_legs`'s own
    # default) and 'declared_plus1'. `terminal_scale`'s old x0.5/x1.5
    # sweep only has an effect under `terminal_legs='defaults'`
    # (`trip_legs.build_trip_legs`'s docstring), so those two rows pass
    # it explicitly -- otherwise they would silently duplicate the base
    # case under the new default.
    survey.build_trip_legs(con, config, density_source=density_source)
    _summary()
    _row("declared (base case)", want_ci=True)

    survey.build_trip_legs(
        con, config, terminal_legs="declared_plus1", density_source=density_source
    )
    _summary()
    _row("declared + 1 min (car/bike/urban PT)", want_ci=True)

    survey.build_trip_legs(
        con,
        config,
        terminal_legs="defaults",
        terminal_scale=0.5,
        density_source=density_source,
    )
    _summary()
    _row("former defaults, terminal legs x0.5", want_ci=True)

    survey.build_trip_legs(
        con,
        config,
        terminal_legs="defaults",
        terminal_scale=1.0,
        density_source=density_source,
    )
    _summary()
    _row("former defaults, terminal legs x1", want_ci=True)

    survey.build_trip_legs(
        con,
        config,
        terminal_legs="defaults",
        terminal_scale=1.5,
        density_source=density_source,
    )
    _summary()
    _row("former defaults, terminal legs x1.5", want_ci=True)

    # Weekdays-only and local-trips-only reuse the base (declared-legs)
    # trip legs, only `day_summary`'s own filter changes.
    survey.build_trip_legs(con, config, density_source=density_source)
    _summary("typejour = 1")
    _row("weekdays only", want_ci=False)
    _summary("mobloc = 1")
    _row("local trips only (MOBLOC=1)", want_ci=False)
    _summary()  # restore the (base_where_sql-filtered) unfiltered base

    survey.build_trip_legs(
        con, config, bike_p0_override_w=P0_REFERENCE_W, density_source=density_source
    )
    _summary()
    _row(f"P0 = {P0_REFERENCE_W:g} W (section 9.7 reference)", want_ci=False)

    # Restore `trip_legs` itself to the base case (declared legs,
    # calibrated P0): every variant above rebuilds `trip_legs` in place,
    # so without this the last variant's mutation (here, the P0=52.5 W
    # override) would silently leak into every `trip_legs`-reading
    # computation that runs after this sweep (F4-F9, the cycle
    # decomposition, etc.) -- the bug behind section 9.9's 2026-10-20
    # fix 0 (F4's "overall" cycle/multimodal means briefly disagreed with
    # the main group table because of exactly this).
    survey.build_trip_legs(con, config, density_source=density_source)
    _summary()

    return rows, ci_stats


def _trips_per_day_by_group(
    days: dict, group_col: str, *, n_reps: int, seed: int
) -> list[tuple[str, int, float, tuple[float, float]]]:
    """(group, n, mean trips/day, 95% CI) per distinct value of
    ``days[group_col]`` (section 9.9's F1: "means with CI by population
    category and density class")."""
    results = []
    for group in np.unique(days[group_col]):
        if group == "unknown":
            continue
        mask = days[group_col] == group
        n = int(mask.sum())
        if n == 0:
            continue
        mean, ci = daily_energy.bootstrap_mean_ci(
            days["ident_men"][mask],
            days["pond_jour"][mask],
            days["trips_per_day"][mask].astype(float),
            n_reps=n_reps,
            seed=seed,
        )
        results.append((str(group), n, mean, ci))
    return results


_DAY_TYPE_BY_TYPEJOUR = {1.0: "weekday", 2.0: "saturday", 3.0: "sunday"}


def _person_universe(
    survey, con: duckdb.DuckDBPyConnection, density_source: str
) -> dict:
    """The full respondent roster with its per-day-type immobility rows
    (section 9.9 point 2's per-person budget), each respondent's
    population category, residence density and income quintile joined
    on: EMP 2019's `person_day_type_rows` (weekday/Saturday/Sunday, from
    `IMMODEP_A`-`G`) or ENTD 2008's `person_weekday_rows` (weekday only,
    from `V2_MOBILREF`), whichever the survey module exposes."""
    if hasattr(survey, "person_day_type_rows"):
        rows = survey.person_day_type_rows(con)
        day_types = ("weekday", "saturday", "sunday")
    else:
        rows = survey.person_weekday_rows(con)
        day_types = ("weekday",)
    category_by_ident = survey.population_category_by_ident(con)
    density_by_ident = survey.residence_density_by_ident(con, density_source)
    income_by_ident = survey.income_quintile_by_ident(con)
    ident_ind = np.array([r[0] for r in rows])
    return {
        "day_types": day_types,
        "ident_men": np.array([r[1] for r in rows]),
        "weight": np.array([r[2] for r in rows], dtype=float),
        "day_type": np.array([r[3] for r in rows]),
        "immobile": np.array([r[4] for r in rows], dtype=float),
        "category": np.array(
            [category_by_ident.get(i, "unknown") for i in ident_ind]
        ),
        "density": np.array(
            [density_by_ident.get(i, "intermediate") for i in ident_ind]
        ),
        "income": np.array([income_by_ident.get(i, "unknown") for i in ident_ind]),
    }


def _person_budget_tables(
    person: dict,
    days: dict,
    *,
    value: np.ndarray,
    day_types: tuple[str, ...],
    day_type_weight: dict[str, float] | None,
    n_reps: int,
    seed: int,
) -> tuple[
    dict[str, daily_energy.PersonBudgetRow],
    dict[tuple[str, str], daily_energy.PersonBudgetRow],
    dict[tuple[str, str], daily_energy.PersonBudgetRow],
]:
    """Per-person budget (section 9.9 point 2) of ``value`` (a
    ``days``-length array, e.g. `total_time_min`): by population
    category alone, by category x density, and by category x income
    quintile. ``day_types``/``day_type_weight`` select weekday-only
    (both surveys) or all-week (EMP 2019 only, `daily_energy.
    DAY_TYPE_WEIGHT`)."""
    t_day_type = np.array(
        [_DAY_TYPE_BY_TYPEJOUR.get(t, "weekday") for t in days["typejour"]]
    )
    by_category = daily_energy.person_budget_by_group(
        person["category"],
        person["day_type"],
        person["ident_men"],
        person["weight"],
        person["immobile"],
        days["population_category"],
        t_day_type,
        days["ident_men"],
        days["pond_jour"],
        value,
        groups=list(daily_energy.POPULATION_CATEGORIES),
        day_types=day_types,
        day_type_weight=day_type_weight,
        min_cell_n=MIN_CELL_N,
        n_reps=n_reps,
        seed=seed,
    )

    def _combined(key_array_p: np.ndarray, key_array_t: np.ndarray, key_order):
        p_combined = np.array(
            [f"{c}||{k}" for c, k in zip(person["category"], key_array_p, strict=False)]
        )
        t_combined = np.array(
            [
                f"{c}||{k}"
                for c, k in zip(days["population_category"], key_array_t, strict=False)
            ]
        )
        groups = [
            f"{c}||{k}" for c in daily_energy.POPULATION_CATEGORIES for k in key_order
        ]
        raw = daily_energy.person_budget_by_group(
            p_combined,
            person["day_type"],
            person["ident_men"],
            person["weight"],
            person["immobile"],
            t_combined,
            t_day_type,
            days["ident_men"],
            days["pond_jour"],
            value,
            groups=groups,
            day_types=day_types,
            day_type_weight=day_type_weight,
            min_cell_n=MIN_CELL_N,
            n_reps=n_reps,
            seed=seed,
        )
        result = {}
        for label, row in raw.items():
            if label == "overall" or "||" not in label:
                continue
            category, key = label.split("||", 1)
            result[(category, key)] = row
        return result

    by_category_density = _combined(
        person["density"], days["home_density"], trip_legs.DENSITY_LABELS
    )
    by_category_income = _combined(
        person["income"], days["income_quintile"], ("q1", "q2", "q3", "q4", "q5")
    )
    return by_category, by_category_density, by_category_income


def _frequency_matrix(days: dict) -> tuple[list[str], list[str], np.ndarray]:
    """(rows, cols, matrix): weighted mean trips per day in each
    (population category, main-mode group) cell -- the same quantity as
    F1 panels (B)/(C), cross-tabulated instead of two separate bar
    charts -- with "overall" margins in both directions (row 0/col 0,
    mean trips/day ignoring the other axis). Excludes the 'unknown'
    population category, as elsewhere in this report."""
    categories = sorted({c for c in days["population_category"] if c != "unknown"})
    modes = sorted(set(days["day_mode_group"]))
    rows = ["overall", *categories]
    cols = ["overall", *modes]
    matrix = np.zeros((len(rows), len(cols)))
    for i, category in enumerate(rows):
        category_mask = (
            np.ones(len(days["pond_jour"]), dtype=bool)
            if category == "overall"
            else days["population_category"] == category
        )
        for j, mode in enumerate(cols):
            mode_mask = (
                np.ones(len(days["pond_jour"]), dtype=bool)
                if mode == "overall"
                else days["day_mode_group"] == mode
            )
            cell_mask = category_mask & mode_mask
            cell_weight = days["pond_jour"][cell_mask]
            matrix[i, j] = (
                float(
                    np.sum(cell_weight * days["trips_per_day"][cell_mask])
                    / cell_weight.sum()
                )
                if cell_weight.sum() > 0
                else np.nan
            )
    return rows, cols, matrix


def _trips_by_group_and_motive(
    con: duckdb.DuckDBPyConnection, group_col: str
) -> tuple[list[str], list[float], np.ndarray]:
    """(groups, top_motives, matrix): weighted mean trips per day of
    each top-level motive, by ``group_col`` (``population_category`` or
    ``home_density``) -- the per-motive decomposition of F1 panels
    (B)/(C): for a fixed group, summing the segments over
    ``top_motives`` reproduces that group's existing mean-trips/day bar
    height exactly. A missing/refused motive (kept, not excluded, by
    ``NEEDS_ONLY_WHERE_SQL``, since it cannot be classified) gets its
    own ``-1.0`` sentinel code, labelled "not recorded". Excludes the
    'unknown' population category, as elsewhere in this report."""
    denom = dict(
        con.sql(
            f"SELECT {group_col}, sum(pond_jour) FROM day_summary "
            f"WHERE {group_col} != 'unknown' GROUP BY 1"
        ).fetchall()
    )
    rows = con.sql(f"""
        SELECT d.{group_col} AS group_value, COALESCE(floor(t.motive), -1.0)
                AS top_motive,
            sum(t.pond_jour) AS weighted_n
        FROM trip_legs t
        JOIN day_summary d ON d.day_id = t.day_id
        WHERE d.{group_col} != 'unknown' AND ({emp2019.NEEDS_ONLY_WHERE_SQL})
        GROUP BY 1, 2
    """).fetchall()
    groups = sorted(denom)
    top_motives = sorted({row[1] for row in rows})
    matrix = np.zeros((len(groups), len(top_motives)))
    for group_value, top_motive, weighted_n in rows:
        if denom.get(group_value, 0.0) > 0:
            matrix[groups.index(group_value), top_motives.index(top_motive)] = (
                weighted_n / denom[group_value]
            )
    return groups, top_motives, matrix


def _figure_f1_trips_per_day(
    days: dict,
    trips_mean: float,
    trips_by_population: list[tuple[str, int, float, tuple[float, float]]],
    trips_by_density: list[tuple[str, int, float, tuple[float, float]]],
    motive_by_population: tuple[list[str], list[float], np.ndarray],
    motive_by_density: tuple[list[str], list[float], np.ndarray],
    out_dir: Path,
) -> Path:
    fig, ((ax_hist, ax_pop), (ax_density, ax_freq)) = plt.subplots(
        2, 2, figsize=(14, 11)
    )

    max_trips = int(days["trips_per_day"].max())
    bins = np.arange(0.5, max_trips + 1.5, 1)
    counts, _ = np.histogram(
        days["trips_per_day"], bins=bins, weights=days["pond_jour"]
    )
    pct = counts / days["pond_jour"].sum() * 100.0
    ax_hist.bar(bins[:-1] + 0.5, pct, width=0.9, color="tab:blue")
    ax_hist.axvline(trips_mean, color="black", linestyle="--")
    ax_hist.text(
        trips_mean,
        ax_hist.get_ylim()[1] * 0.95,
        f"mean={trips_mean:.2f}",
        ha="left",
        va="top",
    )
    ax_hist.set_xlabel("Trips per person and day (integer-centred bins)")
    ax_hist.set_ylabel("% of person-days")
    ax_hist.set_title("(A) Distribution")

    # One shared top-motive -> colour mapping across (B) and (C), as F9
    # does across its two panels.
    all_top_motives = sorted(set(motive_by_population[1]) | set(motive_by_density[1]))
    cmap = plt.get_cmap("tab20")
    colour_by_motive = {
        motive: ("lightgrey" if motive < 0 else cmap(i % 20))
        for i, motive in enumerate(all_top_motives)
    }

    for ax, cis, (groups, top_motives, matrix), title in (
        (
            ax_pop,
            trips_by_population,
            motive_by_population,
            "(B) By population category, stacked by motive",
        ),
        (
            ax_density,
            trips_by_density,
            motive_by_density,
            "(C) By density class, stacked by motive",
        ),
    ):
        ci_by_group = {row[0]: row for row in cis}
        x = np.arange(len(groups))
        bottom = np.zeros(len(groups))
        for j, top_motive in enumerate(top_motives):
            label = (
                "not recorded"
                if top_motive < 0
                else f"{top_motive:g} "
                f"{emp2019.TOP_LEVEL_MOTIVE_LABEL_BY_CODE.get(top_motive, '')}"
            )
            ax.bar(
                x,
                matrix[:, j],
                bottom=bottom,
                label=label,
                color=colour_by_motive[top_motive],
            )
            bottom += matrix[:, j]
        totals = [ci_by_group[g][2] for g in groups]
        lower = [ci_by_group[g][2] - ci_by_group[g][3][0] for g in groups]
        upper = [ci_by_group[g][3][1] - ci_by_group[g][2] for g in groups]
        ax.errorbar(
            x,
            totals,
            yerr=[lower, upper],
            fmt="none",
            ecolor="black",
            capsize=3,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(groups, rotation=30, ha="right")
        ax.set_ylabel("Mean trips per day")
        ax.set_title(title)
        ax.legend(fontsize=5, bbox_to_anchor=(1.02, 1), loc="upper left")

    freq_rows, freq_cols, freq_matrix = _frequency_matrix(days)
    image = ax_freq.imshow(freq_matrix, aspect="auto", cmap="viridis")
    ax_freq.set_xticks(range(len(freq_cols)))
    ax_freq.set_xticklabels(freq_cols, rotation=30, ha="right", fontsize=8)
    ax_freq.set_yticks(range(len(freq_rows)))
    ax_freq.set_yticklabels(freq_rows, fontsize=8)
    for i in range(freq_matrix.shape[0]):
        for j in range(freq_matrix.shape[1]):
            if not np.isnan(freq_matrix[i, j]):
                ax_freq.text(
                    j,
                    i,
                    f"{freq_matrix[i, j]:.1f}",
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="white",
                )
    ax_freq.set_title(
        "(D) Mean trips per day by population category x main-mode group\n"
        "(row/col 'overall' = marginal, weighted means, as in (B)/(C); a\n"
        "subgroup can exceed its row/column total if other subgroups pull\n"
        "the weighted average down -- not an error, see the report)",
        fontsize=8,
    )
    fig.colorbar(image, ax=ax_freq, label="Mean trips per day")

    fig.suptitle("F1. Trips per person and day (section 9.9, point 2)")
    fig.tight_layout()
    path = out_dir / "f01_trips_per_day.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_scalar_by_category_key(
    density_stats: dict[tuple[str, str], daily_energy.ScalarGroupStats],
    income_stats: dict[tuple[str, str], daily_energy.ScalarGroupStats],
    *,
    title: str,
    ylabel: str,
    filename: str,
    out_dir: Path,
) -> Path:
    """Two-panel bar chart (mean + 95% CI, n) by population category x
    density class / income quintile: the shared engine behind f01b
    (trips/day) and f01c (minutes/trip), section 9.9 point 2."""
    categories = list(daily_energy.POPULATION_CATEGORIES)
    fig, (ax_density, ax_income) = plt.subplots(1, 2, figsize=(14, 6))
    for ax, stats, key_order, key_title in (
        (ax_density, density_stats, trip_legs.DENSITY_LABELS, "density class"),
        (ax_income, income_stats, ("q1", "q2", "q3", "q4", "q5"), "income quintile"),
    ):
        width = 0.8 / len(categories)
        x = np.arange(len(key_order))
        for i, category in enumerate(categories):
            means, lowers, uppers = [], [], []
            for key in key_order:
                stat = stats.get((category, key))
                if stat is None or stat.n < MIN_CELL_N:
                    means.append(np.nan)
                    lowers.append(0.0)
                    uppers.append(0.0)
                    continue
                means.append(stat.mean)
                lowers.append(max(stat.mean - stat.mean_ci[0], 0.0))
                uppers.append(max(stat.mean_ci[1] - stat.mean, 0.0))
            ax.bar(
                x + i * width,
                means,
                width,
                yerr=[lowers, uppers],
                label=category,
                capsize=2,
            )
        ax.set_xticks(x + width * (len(categories) - 1) / 2)
        ax.set_xticklabels(key_order, rotation=30, ha="right")
        ax.set_xlabel(f"By {key_title}")
        ax.set_ylabel(ylabel)
    ax_density.legend(fontsize=6)
    fig.suptitle(title)
    fig.tight_layout()
    path = out_dir / filename
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f2_time_density_by_category(
    con: duckdb.DuckDBPyConnection, out_dir: Path
) -> list[Path]:
    """F2: weighted Gaussian kernel densities of daily travel time, by
    main-mode group, linear x-axis (daily time is far less heavy-tailed
    than energy, unlike F3's log scale); (A) stacked and weight-scaled,
    overall, (B) normalised and overlaid, one panel per population
    category -- the same treatment F3 gives energy (section 9.9's
    income update: "give time at least the same treatment as energy").
    Groups/panels with fewer than ``MIN_CELL_N`` days are left out."""
    day_groups = list(daily_energy.DAY_MODE_GROUPS) + ["multimodal", "other"]
    rows = con.sql("""
        SELECT day_mode_group, population_category, pond_jour, total_time_min
        FROM day_summary
        WHERE total_time_min IS NOT NULL AND population_category != 'unknown'
    """).fetchnumpy()
    bandwidth = daily_energy.weighted_gaussian_bandwidth(
        rows["pond_jour"], rows["total_time_min"], scale=1.5
    )
    grid = np.linspace(0, np.percentile(rows["total_time_min"], 99.5), 300)
    present_groups = [
        g for g in day_groups if (rows["day_mode_group"] == g).sum() >= MIN_CELL_N
    ]

    fig, (ax_stack, ax_norm) = plt.subplots(1, 2, figsize=(13, 5))
    cumulative = np.zeros_like(grid)
    total_weight = rows["pond_jour"].sum()
    for group in present_groups:
        mask = rows["day_mode_group"] == group
        sub_time, sub_weight = rows["total_time_min"][mask], rows["pond_jour"][mask]
        density = daily_energy.weighted_gaussian_kde(
            grid, sub_time, sub_weight, bandwidth
        )
        scaled = density * (sub_weight.sum() / total_weight)
        ax_stack.fill_between(
            grid, cumulative, cumulative + scaled, label=group, alpha=0.85
        )
        cumulative += scaled
        mean_min = float(np.sum(sub_weight * sub_time) / sub_weight.sum())
        ax_norm.plot(grid, density, label=group)
        ax_norm.axvline(mean_min, linestyle=":", linewidth=0.8, alpha=0.6)
    for ax in (ax_stack, ax_norm):
        ax.set_xlabel("Daily travel time, minutes")
    ax_stack.set_ylabel("Weighted density (stacked, group-scaled by its share)")
    ax_stack.set_title("(A) Stacked by main-mode group")
    ax_stack.legend(fontsize=6)
    ax_norm.set_ylabel("Density (each group normalised to 1)")
    ax_norm.set_title("(B) Normalised, overlaid; dotted lines mark group means")
    ax_norm.legend(fontsize=6)
    fig.suptitle("F2a. Daily travel time density, overall (section 9.9)")
    fig.tight_layout()
    path_a = out_dir / "f02a_time_density_overall.png"
    fig.savefig(path_a, dpi=110)
    plt.close(fig)

    categories = sorted(set(rows["population_category"]))
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, category in zip(axes.flat, categories, strict=False):
        category_mask = rows["population_category"] == category
        for group in present_groups:
            mask = category_mask & (rows["day_mode_group"] == group)
            if mask.sum() < MIN_CELL_N:
                continue
            density = daily_energy.weighted_gaussian_kde(
                grid, rows["total_time_min"][mask], rows["pond_jour"][mask], bandwidth
            )
            ax.plot(grid, density, label=group)
        ax.set_title(category, fontsize=9)
    for ax in axes.flat[len(categories) :]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=6, loc="upper right")
    fig.suptitle(
        "F2b. Daily travel time density by population category "
        "(normalised, section 9.9)"
    )
    fig.tight_layout()
    path_b = out_dir / "f02b_time_density_by_category.png"
    fig.savefig(path_b, dpi=110)
    plt.close(fig)
    return [path_a, path_b]


def _figure_f3_energy_density(
    con: duckdb.DuckDBPyConnection, out_dir: Path
) -> list[Path]:
    """F3: weighted Gaussian kernel densities on log(energy), log x-axis,
    one shared (widened) bandwidth, group means marked; (A) stacked and
    weight-scaled, (B) normalised and overlaid; one figure overall and
    one per population category (excluding 'unknown'), Compendium, with
    a KH appendix. Groups/panels with fewer than ``MIN_CELL_N`` trips are
    left out, as in F4/F5."""
    paths: list[Path] = []
    day_groups = list(daily_energy.DAY_MODE_GROUPS) + ["multimodal", "other"]
    #: Widens Silverman's rule-of-thumb bandwidth for a smoother curve
    #: over these modest per-group sample sizes (section 9.9's F3).
    bandwidth_scale = 1.5

    for rate_key, rate_label, rate_suffix in (
        ("cp", "Compendium", ""),
        ("kh", "KH", "_appendix_kh"),
    ):
        energy_column = f"total_energy_{rate_key}_kj"
        rows = con.sql(
            f"SELECT day_mode_group, population_category, pond_jour, "
            f"{energy_column} AS energy FROM day_summary "
            f"WHERE {energy_column} IS NOT NULL AND {energy_column} > 0 "
            "AND population_category != 'unknown'"
        ).fetchnumpy()
        log_energy = np.log(rows["energy"])
        bandwidth = daily_energy.weighted_gaussian_bandwidth(
            rows["pond_jour"], log_energy, scale=bandwidth_scale
        )
        grid_log = np.linspace(log_energy.min(), log_energy.max(), 300)
        grid_kj = np.exp(grid_log)
        present_groups = [
            g for g in day_groups if (rows["day_mode_group"] == g).sum() >= MIN_CELL_N
        ]

        fig, (ax_stack, ax_norm) = plt.subplots(1, 2, figsize=(13, 5))
        cumulative = np.zeros_like(grid_log)
        total_weight = rows["pond_jour"].sum()
        for group in present_groups:
            mask = rows["day_mode_group"] == group
            sub_log, sub_weight = log_energy[mask], rows["pond_jour"][mask]
            density = daily_energy.weighted_gaussian_kde(
                grid_log, sub_log, sub_weight, bandwidth
            )
            scaled = density * (sub_weight.sum() / total_weight)
            ax_stack.fill_between(
                grid_kj,
                cumulative,
                cumulative + scaled,
                label=group,
                alpha=0.85,
            )
            cumulative += scaled
            mean_kj = np.exp(np.average(sub_log, weights=sub_weight))
            ax_norm.plot(grid_kj, density, label=group)
            ax_norm.axvline(mean_kj, linestyle=":", linewidth=0.8, alpha=0.6)
        for ax in (ax_stack, ax_norm):
            ax.set_xscale("log")
            ax.axvline(daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--")
            ax.set_xlabel(f"Daily travel energy, kJ ({rate_label}, log scale)")
        ax_stack.set_ylabel("Weighted density (stacked, group-scaled by its share)")
        ax_stack.set_title("(A) Stacked by main-mode group")
        ax_stack.legend(fontsize=6)
        ax_norm.set_ylabel("Density (each group normalised to 1)")
        ax_norm.set_title("(B) Normalised, overlaid; dotted lines mark group means")
        ax_norm.legend(fontsize=6)
        fig.suptitle(
            f"F3. Daily travel energy density, overall ({rate_label}, section 9.9)"
        )
        fig.tight_layout()
        path = out_dir / f"f03a_energy_density_overall{rate_suffix}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        paths.append(path)

        categories = sorted(set(rows["population_category"]))
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        for ax, category in zip(axes.flat, categories, strict=False):
            category_mask = rows["population_category"] == category
            for group in present_groups:
                mask = category_mask & (rows["day_mode_group"] == group)
                if mask.sum() < MIN_CELL_N:
                    continue
                density = daily_energy.weighted_gaussian_kde(
                    grid_log, log_energy[mask], rows["pond_jour"][mask], bandwidth
                )
                ax.plot(grid_kj, density, label=group)
            ax.set_xscale("log")
            ax.axvline(
                daily_energy.KH_DAILY_ENERGY_KJ,
                color="grey",
                linestyle="--",
                linewidth=0.8,
            )
            ax.set_title(category, fontsize=9)
        for ax in axes.flat[len(categories) :]:
            ax.axis("off")
        axes.flat[0].legend(fontsize=6, loc="upper right")
        fig.suptitle(
            f"F3. Daily travel energy density by population category "
            f"({rate_label}, normalised, section 9.9)"
        )
        fig.tight_layout()
        path = out_dir / f"f03b_energy_density_by_category{rate_suffix}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        paths.append(path)

    return paths


def _bootstrap_stats_where(
    con: duckdb.DuckDBPyConnection, where_sql: str, *, n_reps: int, seed: int
) -> dict[str, daily_energy.GroupStats]:
    rows = con.sql(
        "SELECT day_mode_group, ident_men, pond_jour, total_time_min, "
        "total_energy_kh_kj, total_energy_cp_kj FROM day_summary "
        f"WHERE total_energy_kh_kj IS NOT NULL AND ({where_sql})"
    ).fetchnumpy()
    if len(rows["day_mode_group"]) == 0:
        return {}
    stats = daily_energy.bootstrap_group_stats(
        rows["day_mode_group"],
        rows["ident_men"],
        rows["pond_jour"],
        rows["total_time_min"],
        rows["total_energy_kh_kj"],
        rows["total_energy_cp_kj"],
        n_reps=n_reps,
        seed=seed,
    )
    return {s.group: s for s in stats}


def _bootstrap_scalar_time_stats_where(
    con: duckdb.DuckDBPyConnection, where_sql: str, *, n_reps: int, seed: int
) -> dict[str, daily_energy.ScalarGroupStats]:
    """Mean daily time with its 95% bootstrap CI, by main-mode group,
    within one panel's ``where_sql`` scope (F4b's time-parity update:
    "the same treatment energy already has")."""
    rows = con.sql(
        "SELECT day_mode_group, ident_men, pond_jour, total_time_min "
        f"FROM day_summary WHERE total_time_min IS NOT NULL AND ({where_sql})"
    ).fetchnumpy()
    if len(rows["day_mode_group"]) == 0:
        return {}
    stats = daily_energy.bootstrap_scalar_group_stats(
        rows["day_mode_group"],
        rows["ident_men"],
        rows["pond_jour"],
        rows["total_time_min"],
        n_reps=n_reps,
        seed=seed,
    )
    return {s.group: s for s in stats}


def _panel_overall_stats(
    con: duckdb.DuckDBPyConnection, where_sql: str
) -> tuple[float, float, float, float]:
    """This panel's own weighted mean and median daily energy (both rate
    sets), across every main-mode group combined (F4a's "computed mean"
    and "overall median" lines, distinct from Koelbl & Helbing's fixed
    615 kJ reference)."""
    rows = con.sql(
        "SELECT pond_jour, total_energy_kh_kj, total_energy_cp_kj FROM day_summary "
        f"WHERE total_energy_kh_kj IS NOT NULL AND ({where_sql})"
    ).fetchnumpy()
    if len(rows["pond_jour"]) == 0:
        return (float("nan"),) * 4
    mean_kh, _ = daily_energy.weighted_mean_variance(
        rows["pond_jour"], rows["total_energy_kh_kj"]
    )
    mean_cp, _ = daily_energy.weighted_mean_variance(
        rows["pond_jour"], rows["total_energy_cp_kj"]
    )
    median_kh = daily_energy._weighted_median(
        rows["total_energy_kh_kj"], rows["pond_jour"]
    )
    median_cp = daily_energy._weighted_median(
        rows["total_energy_cp_kj"], rows["pond_jour"]
    )
    return mean_kh, mean_cp, median_kh, median_cp


def _figure_f4_mean_by_mode(
    con: duckdb.DuckDBPyConnection,
    out_dir: Path,
    *,
    n_reps: int,
    seed: int,
) -> tuple[list[Path], list[tuple[str, dict[str, daily_energy.GroupStats]]]]:
    """F4: mean daily energy and time, 95% CI and n on the bars, overall
    and one panel per population category; blank when n < 50."""
    categories = [
        row[0]
        for row in con.sql(
            "SELECT DISTINCT population_category FROM day_summary "
            "WHERE population_category != 'unknown' ORDER BY 1"
        ).fetchall()
    ]
    groups = list(daily_energy.DAY_MODE_GROUPS) + ["multimodal", "other"]
    panel_where_sql = [("overall", "TRUE")] + [
        (category, f"population_category = '{category}'") for category in categories
    ]
    panels = [
        (label, _bootstrap_stats_where(con, where_sql, n_reps=n_reps, seed=seed))
        for label, where_sql in panel_where_sql
    ]
    panel_stats_overall = {
        label: _panel_overall_stats(con, where_sql)
        for label, where_sql in panel_where_sql
    }

    fig, axes = plt.subplots(2, 3, figsize=(19, 11))
    for ax, (label, stats) in zip(axes.flat, panels, strict=False):
        present = [g for g in groups if g in stats]
        x = np.arange(len(present))
        width = 0.35
        for offset, rate_key in zip((-width / 2, width / 2), ("kh", "cp"), strict=True):
            means, lowers, uppers, medians = [], [], [], []
            for group in present:
                stat = stats[group]
                if stat.n < MIN_CELL_N:
                    means.append(np.nan)
                    lowers.append(0.0)
                    uppers.append(0.0)
                    medians.append(np.nan)
                    continue
                mean = getattr(stat, f"mean_energy_{rate_key}_kj")
                ci = getattr(stat, f"mean_energy_{rate_key}_ci")
                means.append(mean)
                lowers.append(max(mean - ci[0], 0.0))
                uppers.append(max(ci[1] - mean, 0.0))
                medians.append(getattr(stat, f"median_energy_{rate_key}_kj"))
            ax.bar(
                x + offset,
                means,
                width,
                yerr=[lowers, uppers],
                label=rate_key,
                capsize=2,
            )
            ax.scatter(
                x + offset,
                medians,
                marker="D",
                color="black",
                s=14,
                zorder=3,
                label=f"{rate_key} median" if ax is axes.flat[0] else None,
            )
            for xi, mean in zip(x + offset, means, strict=True):
                if not np.isnan(mean):
                    ax.text(
                        xi,
                        mean,
                        f"{mean:.0f}",
                        ha="center",
                        va="bottom",
                        fontsize=6,
                    )
        for i, group in enumerate(present):
            ax.text(
                i,
                0,
                f"n={stats[group].n}",
                ha="center",
                va="bottom",
                fontsize=6,
                rotation=90,
            )
        # Reference lines use the y-axis transform (x in axes fraction,
        # y in data units) so their value labels stay inside the plot
        # regardless of how many mode groups a panel has.
        label_transform = ax.get_yaxis_transform()
        panel_mean_kh, panel_mean_cp, panel_median_kh, panel_median_cp = (
            panel_stats_overall[label]
        )
        for value, color, linestyle, text_va, show_legend in (
            (
                daily_energy.KH_DAILY_ENERGY_KJ,
                "grey",
                "--",
                "bottom",
                "Koelbl & Helbing 615 kJ",
            ),
            (panel_mean_kh, "tab:blue", "-.", "bottom", "computed mean (kh)"),
            (panel_mean_cp, "tab:orange", "-.", "top", "computed mean (cp)"),
            (panel_median_kh, "tab:blue", ":", "bottom", "overall median (kh)"),
            (panel_median_cp, "tab:orange", ":", "top", "overall median (cp)"),
        ):
            ax.axhline(
                value,
                color=color,
                linestyle=linestyle,
                linewidth=0.8,
                label=show_legend if ax is axes.flat[0] else None,
            )
            ax.text(
                0.98,
                value,
                f"{value:.0f}",
                transform=label_transform,
                color=color,
                fontsize=6,
                ha="right",
                va=text_va,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(present, rotation=45, ha="right", fontsize=7)
        ax.set_title(label, fontsize=9)
        ax.legend(fontsize=6)
    for ax in axes.flat[len(panels) :]:
        ax.axis("off")
    fig.suptitle(
        "F4a. Mean daily energy by main-mode group, 95% CI, n, median "
        "marker, mean bar values, and labelled reference lines (Koelbl & "
        "Helbing 615 kJ, this panel's own computed mean, overall median; "
        "section 9.9)"
    )
    fig.tight_layout()
    path_energy = out_dir / "f04a_mean_energy_by_mode.png"
    fig.savefig(path_energy, dpi=110)
    plt.close(fig)

    time_panels = [
        (
            label,
            _bootstrap_scalar_time_stats_where(
                con, where_sql, n_reps=n_reps, seed=seed
            ),
        )
        for label, where_sql in panel_where_sql
    ]
    fig, axes = plt.subplots(2, 3, figsize=(19, 11))
    for ax, (label, stats), (_, time_stats) in zip(
        axes.flat, panels, time_panels, strict=False
    ):
        present = [g for g in groups if g in stats]
        x = np.arange(len(present))
        means, lowers, uppers, medians = [], [], [], []
        for group in present:
            stat = time_stats.get(group)
            if stat is None or stat.n < MIN_CELL_N:
                means.append(np.nan)
                lowers.append(0.0)
                uppers.append(0.0)
                medians.append(np.nan)
                continue
            means.append(stat.mean)
            lowers.append(max(stat.mean - stat.mean_ci[0], 0.0))
            uppers.append(max(stat.mean_ci[1] - stat.mean, 0.0))
            medians.append(stat.median)
        ax.bar(x, means, yerr=[lowers, uppers], color="tab:gray", capsize=2)
        ax.scatter(
            x,
            medians,
            marker="D",
            color="black",
            s=14,
            zorder=3,
            label="median" if ax is axes.flat[0] else None,
        )
        for xi, mean in zip(x, means, strict=True):
            if not np.isnan(mean):
                ax.text(xi, mean, f"{mean:.0f}", ha="center", va="bottom", fontsize=6)
        for i, group in enumerate(present):
            ax.text(
                i,
                0,
                f"n={stats[group].n}",
                ha="center",
                va="bottom",
                fontsize=6,
                rotation=90,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(present, rotation=45, ha="right", fontsize=7)
        ax.set_title(label, fontsize=9)
        # Only the first panel's median marker carries a label (see
        # above): calling legend() on the others would warn "no artists
        # with labels found".
        if ax is axes.flat[0]:
            ax.legend(fontsize=6)
    for ax in axes.flat[len(panels) :]:
        ax.axis("off")
    fig.suptitle(
        "F4b. Mean daily travel time by main-mode group, 95% CI, n, "
        "median marker (section 9.9's income update: the same treatment "
        "energy already has)"
    )
    fig.tight_layout()
    path_time = out_dir / "f04b_mean_time_by_mode.png"
    fig.savefig(path_time, dpi=110)
    plt.close(fig)
    return [path_energy, path_time], panels


def _figure_f5_heatmaps(con: duckdb.DuckDBPyConnection, out_dir: Path) -> Path:
    """F5: heatmaps of mean energy (Compendium) by main-mode group x
    population category and x density class, with n; blank when n < 50."""
    groups = list(daily_energy.DAY_MODE_GROUPS) + ["multimodal", "other"]

    def _matrix(column: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
        rows = con.sql(f"""
            SELECT day_mode_group, {column} AS col2, count(*) AS n,
                sum(pond_jour * total_energy_cp_kj) / sum(pond_jour) AS mean_energy
            FROM day_summary WHERE total_energy_cp_kj IS NOT NULL
            GROUP BY 1, 2
        """).fetchall()
        values = sorted({row[1] for row in rows if row[1] != "unknown"})
        matrix = np.full((len(groups), len(values)), np.nan)
        n_matrix = np.zeros((len(groups), len(values)), dtype=int)
        for mode, value, n, mean_energy in rows:
            if mode not in groups or value not in values:
                continue
            i, j = groups.index(mode), values.index(value)
            n_matrix[i, j] = n
            if n >= MIN_CELL_N:
                matrix[i, j] = mean_energy
        return matrix, n_matrix, values

    fig, (ax_population, ax_density) = plt.subplots(1, 2, figsize=(15, 7))
    for ax, column, title in (
        (ax_population, "population_category", "(A) x population category"),
        (ax_density, "home_density", "(B) x density class"),
    ):
        matrix, n_matrix, values = _matrix(column)
        image = ax.imshow(matrix, aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels(values, rotation=30, ha="right")
        ax.set_yticks(range(len(groups)))
        ax.set_yticklabels(groups, fontsize=7)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if not np.isnan(matrix[i, j]):
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.0f}\n(n={n_matrix[i, j]})",
                        ha="center",
                        va="center",
                        fontsize=6,
                        color="white",
                    )
        ax.set_title(title, fontsize=10)
        fig.colorbar(image, ax=ax, label="Mean daily energy, kJ (Compendium)")
    fig.suptitle(
        "F5. Mean daily energy by main-mode group (n < 50 cells blank, section 9.9)"
    )
    fig.tight_layout()
    path = out_dir / "f05_heatmaps.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _heatmap_matrix(
    con: duckdb.DuckDBPyConnection,
    row_col: str,
    row_values: list[str],
    col_col: str,
    col_values: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    """Mean daily time (n, blank where n < 50) for a (``row_col``,
    ``col_col``) heatmap cell (section 9.9's income update: time
    heatmaps, mode x category, mode x density, category x density,
    category x income quintile)."""
    rows = con.sql(f"""
        SELECT {row_col} AS r, {col_col} AS c, count(*) AS n,
            sum(pond_jour * total_time_min) / sum(pond_jour) AS mean_time
        FROM day_summary WHERE total_time_min IS NOT NULL
            AND {row_col} != 'unknown' AND {col_col} != 'unknown'
        GROUP BY 1, 2
    """).fetchall()
    matrix = np.full((len(row_values), len(col_values)), np.nan)
    n_matrix = np.zeros((len(row_values), len(col_values)), dtype=int)
    for r, c, n, mean_time in rows:
        if r not in row_values or c not in col_values:
            continue
        i, j = row_values.index(r), col_values.index(c)
        n_matrix[i, j] = n
        if n >= MIN_CELL_N:
            matrix[i, j] = mean_time
    return matrix, n_matrix


def _draw_heatmap_panel(fig, ax, matrix, n_matrix, row_values, col_values, title):
    image = ax.imshow(matrix, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(col_values)))
    ax.set_xticklabels(col_values, rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_values)))
    ax.set_yticklabels(row_values, fontsize=7)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if not np.isnan(matrix[i, j]):
                ax.text(
                    j,
                    i,
                    f"{matrix[i, j]:.0f}\n(n={n_matrix[i, j]})",
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="white",
                )
    ax.set_title(title, fontsize=9)
    fig.colorbar(
        image, ax=ax, label="Mean daily travel time, minutes", fraction=0.046
    )


def _figure_f5_time_heatmaps(con: duckdb.DuckDBPyConnection, out_dir: Path) -> Path:
    """F5b: 4-panel heatmaps of mean daily travel time -- main-mode
    group x population category, mode x density class, population
    category x density class, category x income quintile -- with n;
    blank where n < 50 (section 9.9's income update: "give time the
    same treatment energy already has")."""
    groups = list(daily_energy.DAY_MODE_GROUPS) + ["multimodal", "other"]
    categories = list(daily_energy.POPULATION_CATEGORIES)
    densities = list(trip_legs.DENSITY_LABELS)
    incomes = ["q1", "q2", "q3", "q4", "q5"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    panels = (
        ("day_mode_group", groups, "population_category", categories,
         "(A) mode x population category"),
        ("day_mode_group", groups, "home_density", densities,
         "(B) mode x density class"),
        ("population_category", categories, "home_density", densities,
         "(C) category x density class"),
        ("population_category", categories, "income_quintile", incomes,
         "(D) category x income quintile"),
    )
    for ax, (row_col, row_values, col_col, col_values, title) in zip(
        axes.flat, panels, strict=True
    ):
        matrix, n_matrix = _heatmap_matrix(
            con, row_col, row_values, col_col, col_values
        )
        _draw_heatmap_panel(fig, ax, matrix, n_matrix, row_values, col_values, title)
    fig.suptitle(
        "F5b. Mean daily travel time, four cross-tabulations (n < 50 "
        "cells blank, section 9.9)"
    )
    fig.tight_layout()
    path = out_dir / "f05b_time_heatmaps.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f10_constancy(
    category_density_time_ci: dict[tuple[str, str], daily_energy.ScalarGroupStats],
    category_income_time_ci: dict[tuple[str, str], daily_energy.ScalarGroupStats],
    person_budget_category_density: dict[tuple[str, str], daily_energy.PersonBudgetRow],
    person_budget_category_income: dict[tuple[str, str], daily_energy.PersonBudgetRow],
    out_dir: Path,
) -> Path:
    """F10: one panel per population category, mean daily time with 95%
    CI by density class and by income quintile, per day with trips and
    per person (section 9.9's constancy test): is the budget the same
    across density classes and income classes within a category?"""
    densities = list(trip_legs.DENSITY_LABELS)
    incomes = ["q1", "q2", "q3", "q4", "q5"]
    categories = list(daily_energy.POPULATION_CATEGORIES)

    fig, axes = plt.subplots(2, 3, figsize=(19, 11))
    for ax, category in zip(axes.flat, categories, strict=False):
        all_xticks, all_xlabels = [], []
        x_start = 0
        for key_order, store, person_store, color, label in (
            (densities, category_density_time_ci, person_budget_category_density,
             "tab:blue", "density"),
            (incomes, category_income_time_ci, person_budget_category_income,
             "tab:orange", "income"),
        ):
            x = x_start + np.arange(len(key_order))
            all_xticks.extend(x.tolist())
            all_xlabels.extend(key_order)
            x_start = x[-1] + 2  # a one-slot gap between the two series
            means, lowers, uppers = [], [], []
            for key in key_order:
                stat = store.get((category, key))
                if stat is None or stat.n < MIN_CELL_N:
                    means.append(np.nan)
                    lowers.append(0.0)
                    uppers.append(0.0)
                    continue
                means.append(stat.mean)
                lowers.append(max(stat.mean - stat.mean_ci[0], 0.0))
                uppers.append(max(stat.mean_ci[1] - stat.mean, 0.0))
            ax.errorbar(
                x,
                means,
                yerr=[lowers, uppers],
                fmt="o",
                color=color,
                capsize=3,
                label=f"day with trips ({label})" if ax is axes.flat[0] else None,
            )
            person_means = []
            for key in key_order:
                row = person_store.get((category, key))
                person_means.append(
                    row.budget if row is not None and row.n >= MIN_CELL_N else np.nan
                )
            ax.plot(
                x,
                person_means,
                marker="x",
                linestyle="none",
                color=color,
                markersize=8,
                label=f"per person ({label})" if ax is axes.flat[0] else None,
            )
        ax.set_xticks(all_xticks)
        ax.set_xticklabels(all_xlabels, rotation=30, ha="right", fontsize=6)
        ax.set_title(category, fontsize=9)
        ax.set_ylabel("Mean daily time, minutes")
    for ax in axes.flat[len(categories) :]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=6, loc="upper right")
    fig.suptitle(
        "F10. Constancy: mean daily time by density class and income "
        "quintile, within each population category (circles = day with "
        "trips with 95% CI; crosses = per person, point estimate; "
        "section 9.9)"
    )
    fig.tight_layout()
    path = out_dir / "f10_constancy.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f6_v0_p0(
    v0_by_age_band: list[daily_energy.SpeedCalibration],
    p0_by_age_band: list[daily_energy.P0Calibration],
    config: EnergyConfig,
    out_dir: Path,
) -> Path:
    fig, (ax_v0, ax_p0) = plt.subplots(1, 2, figsize=(10, 5))
    bands = [stat.group for stat in v0_by_age_band]
    ax_v0.bar(bands, [stat.speed_kmh for stat in v0_by_age_band], color="tab:green")
    for i, stat in enumerate(v0_by_age_band):
        ax_v0.text(
            i, stat.speed_kmh, f"n={stat.n}", ha="center", va="bottom", fontsize=7
        )
    ax_v0.axhline(
        config.walking.v0_kmh, color="grey", linestyle="--", label="configured v0"
    )
    ax_v0.set_xlabel("AGE6 age band")
    ax_v0.set_ylabel("v0, km/h (weighted ratio estimator)")
    ax_v0.set_title("(A) Walking")
    ax_v0.legend()

    bands_p0 = [stat.group for stat in p0_by_age_band]
    ax_p0.bar(bands_p0, [stat.p0_w for stat in p0_by_age_band], color="tab:orange")
    for i, stat in enumerate(p0_by_age_band):
        ax_p0.text(i, stat.p0_w, f"n={stat.n}", ha="center", va="bottom", fontsize=7)
    ax_p0.set_xlabel("AGE6 age band")
    ax_p0.set_ylabel("P0, W (at the implied flat speed)")
    ax_p0.set_title("(B) Cycling")
    fig.suptitle("F6. Calibrated v0 and P0 by age band (section 9.9, step 1)")
    fig.tight_layout()
    path = out_dir / "f06_v0_p0.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f7_passengers(
    passenger_trip_stats: dict[str, tuple[int, float, float, float]],
    walk_trips_by_day_group: dict[str, float],
    out_dir: Path,
) -> Path:
    groups = ["car_passenger_household", "car_passenger_carpool"]
    fig, (ax_energy, ax_walk) = plt.subplots(1, 2, figsize=(11, 5))
    x = np.arange(len(groups))
    width = 0.35
    ax_energy.bar(
        x - width / 2,
        [passenger_trip_stats[g][2] for g in groups],
        width,
        label="kh",
    )
    ax_energy.bar(
        x + width / 2,
        [passenger_trip_stats[g][3] for g in groups],
        width,
        label="compendium",
    )
    ax_energy.set_xticks(x)
    ax_energy.set_xticklabels(["household", "carpool"])
    ax_energy.set_ylabel("Mean one-way trip energy, kJ")
    ax_energy.set_title("(A) Household vs carpool (trip level)")
    ax_energy.legend()

    walk_groups = ["car_driver", "car_passenger_household", "car_passenger_carpool"]
    walk_values = [walk_trips_by_day_group.get(g, float("nan")) for g in walk_groups]
    ax_walk.bar(range(len(walk_groups)), walk_values, color="tab:purple")
    ax_walk.set_xticks(range(len(walk_groups)))
    ax_walk.set_xticklabels(
        ["driver", "passenger\n(household)", "passenger\n(carpool)"]
    )
    ax_walk.set_ylabel("Mean walking trips per day")
    ax_walk.set_title("(B) Walking trips, driver vs passenger days")
    fig.suptitle(
        "F7. Car passengers (section 9.9); the carpool premium is the "
        "TODO(confirm)\ndefault of config.car.carpool_passenger (section 9.6)"
    )
    fig.tight_layout()
    path = out_dir / "f07_passengers.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f8_robustness(
    robustness_ci: dict[str, list[daily_energy.GroupStats]],
    out_dir: Path,
) -> Path:
    """F8: group means +/- 95% CI for the base case and the terminal-leg
    extremes (section 9.9's F8)."""
    variants = list(robustness_ci.keys())
    groups = list(daily_energy.F8_ROBUSTNESS_GROUPS)
    x = np.arange(len(groups))
    width = 0.8 / max(len(variants), 1)

    fig, (ax_energy, ax_time) = plt.subplots(1, 2, figsize=(15, 6))
    for i, variant in enumerate(variants):
        by_group = {stat.group: stat for stat in robustness_ci[variant]}
        offset = (i - (len(variants) - 1) / 2) * width
        means = [
            by_group[g].mean_energy_cp_kj if g in by_group else np.nan for g in groups
        ]
        lowers = [
            by_group[g].mean_energy_cp_kj - by_group[g].mean_energy_cp_ci[0]
            if g in by_group
            else 0.0
            for g in groups
        ]
        uppers = [
            by_group[g].mean_energy_cp_ci[1] - by_group[g].mean_energy_cp_kj
            if g in by_group
            else 0.0
            for g in groups
        ]
        ax_energy.bar(
            x + offset,
            means,
            width,
            yerr=[lowers, uppers],
            label=variant,
            capsize=2,
        )
        time_means = [
            by_group[g].mean_time_min if g in by_group else np.nan for g in groups
        ]
        ax_time.bar(x + offset, time_means, width, label=variant)

    ax_energy.set_xticks(x)
    ax_energy.set_xticklabels(groups, rotation=30, ha="right")
    ax_energy.set_ylabel("Mean daily energy, kJ (compendium)")
    ax_energy.set_title("(A) Energy")
    ax_energy.legend(fontsize=7)
    ax_time.set_xticks(x)
    ax_time.set_xticklabels(groups, rotation=30, ha="right")
    ax_time.set_ylabel("Mean daily time, minutes")
    ax_time.set_title("(B) Time")
    fig.suptitle(
        "F8. Robustness: group means +/- 95% CI, base case and\n"
        "terminal-leg extremes (section 9.9)"
    )
    fig.tight_layout()
    path = out_dir / "f08_robustness.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f9_motive_energy(
    before: tuple[list[str], list[float], np.ndarray],
    after: tuple[list[str], list[float], np.ndarray],
    out_dir: Path,
) -> Path:
    """F9: stacked bar of weighted KH energy by top-level motive, one bar
    per mode group, each normalised to 100% (section 9.9 point 1
    follow-up, "a graph with a stacked bar of energy values per
    motive"). (A) the full, pre-exclusion dataset (every motive,
    including `NEEDS_EXCLUDED_MOTIVE_CODES`): the evidence behind this
    report's needs-only scope. (B) the final, needs-only-scoped dataset
    ("the final decomposition"): motive 7 (leisure) shrinks to its
    remaining, non-excluded sub-codes (7.1-7.5) and motive 8
    (holidays/second home) disappears entirely, since every one of its
    sub-codes is excluded.
    """
    # One shared top-motive -> colour mapping across both panels (a
    # motive missing from one panel keeps the same colour it would have
    # had, so the two panels stay visually comparable).
    all_top_motives = sorted(set(before[1]) | set(after[1]))
    cmap = plt.get_cmap("tab10")
    colour_by_motive = {
        motive: cmap(i % 10) for i, motive in enumerate(all_top_motives)
    }

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    for ax, (mode_groups, top_motives, matrix), title in (
        (axes[0], before, "(A) Full dataset (evidence for the scope decision)"),
        (axes[1], after, "(B) Final decomposition (needs-only scope)"),
    ):
        totals = matrix.sum(axis=1, keepdims=True)
        shares = (
            np.divide(matrix, totals, out=np.zeros_like(matrix), where=totals > 0)
            * 100.0
        )
        x = np.arange(len(mode_groups))
        bottom = np.zeros(len(mode_groups))
        for j, top_motive in enumerate(top_motives):
            label = emp2019.TOP_LEVEL_MOTIVE_LABEL_BY_CODE.get(
                top_motive, f"code {top_motive:g}"
            )
            ax.bar(
                x,
                shares[:, j],
                bottom=bottom,
                label=f"{top_motive:g} {label}",
                color=colour_by_motive[top_motive],
            )
            bottom += shares[:, j]
        ax.set_xticks(x)
        ax.set_xticklabels(mode_groups, rotation=30, ha="right")
        ax.set_ylabel("Share of weighted energy, % (kh)")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=6, bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.suptitle(
        "F9. Energy by top-level motive, all modes (100% stacked, section 9.9 point 1)"
    )
    fig.tight_layout()
    path = out_dir / "f09_motive_energy.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _format_category_density_table(
    category_density_stats: dict[tuple[str, str], daily_energy.GroupStats],
    time_ci_stats: dict[tuple[str, str], daily_energy.ScalarGroupStats] | None = None,
) -> list[str]:
    """Population category x density class: mean daily time (n < 50
    blank), section 9.9's time-budget table (point 2a). ``time_ci_stats``
    (``_scalar_by_combined_key`` on ``total_time_min``) adds a 95% CI
    column, giving time the same mean+CI+median treatment energy already
    has (section 9.9's income update); omitted, the CI column is left
    out (backward compatible)."""
    return _format_category_key_table(
        category_density_stats,
        trip_legs.DENSITY_LABELS,
        "Density",
        time_ci_stats=time_ci_stats,
    )


def _format_category_key_table(
    category_key_stats: dict[tuple[str, str], daily_energy.GroupStats],
    key_order: tuple[str, ...],
    key_label: str,
    time_ci_stats: dict[tuple[str, str], daily_energy.ScalarGroupStats] | None = None,
) -> list[str]:
    """Population category x ``key_label`` (density or income quintile):
    mean daily time (n < 50 blank), with an optional 95% CI column
    (``time_ci_stats``, section 9.9's time-parity update). Generalises
    ``_format_category_density_table`` to any ordered key."""
    header = f"| Category | {key_label} | n | mean time (min)"
    sep = "|---|---|---|---"
    if time_ci_stats is not None:
        header += " | 95% CI"
        sep += "|---"
    header += " | median time (min) |"
    sep += "|---|"
    lines = [header, sep]
    for category in daily_energy.POPULATION_CATEGORIES:
        for key in key_order:
            stat = category_key_stats.get((category, key))
            if stat is None or stat.n < MIN_CELL_N:
                n = stat.n if stat else 0
                row = f"| {category} | {key} | {n} | -"
                if time_ci_stats is not None:
                    row += " | -"
                row += " | - |"
                lines.append(row)
                continue
            row = f"| {category} | {key} | {stat.n} | {stat.mean_time_min:.1f}"
            if time_ci_stats is not None:
                ci_stat = time_ci_stats.get((category, key))
                row += (
                    f" | [{ci_stat.mean_ci[0]:.1f}, {ci_stat.mean_ci[1]:.1f}]"
                    if ci_stat is not None
                    else " | -"
                )
            row += f" | {stat.median_time_min:.1f} |"
            lines.append(row)
    return lines


def _format_constancy_summary_table(
    rows: list[tuple[str, float, float, float]], named_label: str = "dense/very_sparse"
) -> list[str]:
    lines = [
        f"| Category | {named_label} | max/min | CV across classes |",
        "|---|---|---|---|",
    ]
    for category, named_ratio, max_min, cv in rows:
        nr = "-" if np.isnan(named_ratio) else f"{named_ratio:.2f}"
        mm = "-" if np.isnan(max_min) else f"{max_min:.2f}"
        cvs = "-" if np.isnan(cv) else f"{cv:.2f}"
        lines.append(f"| {category} | {nr} | {mm} | {cvs} |")
    return lines


def _format_scalar_group_table(
    stats: list[daily_energy.ScalarGroupStats], *, label: str, decimals: int = 2
) -> list[str]:
    """Generic mean+CI+median table for one arbitrary scalar
    (trips/day, minutes/trip, section 9.9 point 2): one row per group,
    n < 50 blank."""
    lines = [
        f"| Group | n | weighted n | mean {label} | 95% CI | median {label} |",
        "|---|---|---|---|---|---|",
    ]
    for stat in sorted(stats, key=lambda s: -s.weighted_n):
        if stat.n < MIN_CELL_N:
            lines.append(
                f"| {stat.group} | {stat.n} | {stat.weighted_n:,.0f} | - | - | - |"
            )
            continue
        lines.append(
            f"| {stat.group} | {stat.n} | {stat.weighted_n:,.0f} | "
            f"{stat.mean:.{decimals}f} | [{stat.mean_ci[0]:.{decimals}f}, "
            f"{stat.mean_ci[1]:.{decimals}f}] | {stat.median:.{decimals}f} |"
        )
    return lines


def _format_person_budget_table(
    rows: dict[str, daily_energy.PersonBudgetRow],
) -> list[str]:
    """Per-person budget (section 9.9 point 2) by population category:
    P(out), T|out, n, budget and its 95% CI (blank when there is no
    bootstrap, i.e. an all-week budget)."""
    lines = [
        "| Category | n | P(out) | T\\|out (min) | budget (min) | 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    order = [*daily_energy.POPULATION_CATEGORIES, "overall"]
    for category in order:
        row = rows.get(category)
        if row is None or row.n == 0:
            lines.append(f"| {category} | 0 | - | - | - | - |")
            continue
        ci = (
            f"[{row.budget_ci[0]:.1f}, {row.budget_ci[1]:.1f}]"
            if not np.isnan(row.budget_ci[0])
            else "-"
        )
        lines.append(
            f"| {category} | {row.n} | {row.p_out:.3f} | "
            f"{row.value_given_out:.1f} | {row.budget:.1f} | {ci} |"
        )
    return lines


def _format_person_budget_key_table(
    rows: dict[tuple[str, str], daily_energy.PersonBudgetRow],
    key_order: tuple[str, ...],
    key_label: str,
) -> list[str]:
    """Per-person budget by population category x key (density or
    income quintile, section 9.9 point 2): P(out), T|out, n, budget and
    its 95% CI."""
    lines = [
        f"| Category | {key_label} | n | P(out) | T\\|out (min) | "
        "budget (min) | 95% CI |",
        "|---|---|---|---|---|---|---|",
    ]
    for category in daily_energy.POPULATION_CATEGORIES:
        for key in key_order:
            row = rows.get((category, key))
            if row is None or row.n == 0:
                lines.append(f"| {category} | {key} | 0 | - | - | - | - |")
                continue
            ci = (
                f"[{row.budget_ci[0]:.1f}, {row.budget_ci[1]:.1f}]"
                if not np.isnan(row.budget_ci[0])
                else "-"
            )
            lines.append(
                f"| {category} | {key} | {row.n} | {row.p_out:.3f} | "
                f"{row.value_given_out:.1f} | {row.budget:.1f} | {ci} |"
            )
    return lines


def _format_scalar_category_key_table(
    category_key_stats: dict[tuple[str, str], daily_energy.ScalarGroupStats],
    key_order: tuple[str, ...],
    key_label: str,
    *,
    label: str,
    decimals: int = 2,
) -> list[str]:
    """Population category x key (density or income quintile): mean +
    95% CI + median of one arbitrary scalar (trips/day, minutes/trip),
    n < 50 blank."""
    lines = [
        f"| Category | {key_label} | n | mean {label} | 95% CI | median {label} |",
        "|---|---|---|---|---|---|",
    ]
    for category in daily_energy.POPULATION_CATEGORIES:
        for key in key_order:
            stat = category_key_stats.get((category, key))
            if stat is None or stat.n < MIN_CELL_N:
                n = stat.n if stat else 0
                lines.append(f"| {category} | {key} | {n} | - | - | - |")
                continue
            lines.append(
                f"| {category} | {key} | {stat.n} | {stat.mean:.{decimals}f} | "
                f"[{stat.mean_ci[0]:.{decimals}f}, {stat.mean_ci[1]:.{decimals}f}] | "
                f"{stat.median:.{decimals}f} |"
            )
    return lines


def _format_group_table(stats: list[daily_energy.GroupStats]) -> list[str]:
    lines = [
        "| Group | n | weighted n | mean time (min) | median time (min) | "
        "mean energy kh (kJ) | median energy kh (kJ) | 95% CI | "
        "mean energy compendium (kJ) | median energy compendium (kJ) | 95% CI |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for stat in sorted(stats, key=lambda s: -s.weighted_n):
        lines.append(
            f"| {stat.group} | {stat.n} | {stat.weighted_n:,.0f} | "
            f"{stat.mean_time_min:.1f} | {stat.median_time_min:.1f} | "
            f"{stat.mean_energy_kh_kj:.1f} | {stat.median_energy_kh_kj:.1f} | "
            f"[{stat.mean_energy_kh_ci[0]:.1f}, {stat.mean_energy_kh_ci[1]:.1f}] | "
            f"{stat.mean_energy_cp_kj:.1f} | {stat.median_energy_cp_kj:.1f} | "
            f"[{stat.mean_energy_cp_ci[0]:.1f}, {stat.mean_energy_cp_ci[1]:.1f}] |"
        )
    return lines


def _format_robustness_table(rows: list[daily_energy.RobustnessRow]) -> list[str]:
    lines = [
        "| Variant | Scope | Statistic | energy ratio (kh) | CV (kh) | "
        "min/max group (kh) | energy ratio (cp) | CV (cp) | min/max group (cp) | "
        "time ratio | time CV | min/max group (time) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.variant} | {row.scope} | {row.statistic} | "
            f"{row.energy_kh_ratio:.2f} | {row.energy_kh_cv:.2f} | "
            f"{row.energy_kh_min_group} / {row.energy_kh_max_group} | "
            f"{row.energy_cp_ratio:.2f} | {row.energy_cp_cv:.2f} | "
            f"{row.energy_cp_min_group} / {row.energy_cp_max_group} | "
            f"{row.time_ratio:.2f} | {row.time_cv:.2f} | "
            f"{row.time_min_group} / {row.time_max_group} |"
        )
    return lines


def _format_group_table_by_panel(
    panels: list[tuple[str, dict[str, daily_energy.GroupStats]]],
) -> list[str]:
    """Mean daily energy (both rate sets) and time, with 95% CI and n, for
    every main-mode group, overall and one sub-table per population
    category (F4's own data as a table)."""
    lines: list[str] = []
    for label, stats in panels:
        lines.append(f"### {label}")
        lines.append("")
        lines.extend(_format_group_table(list(stats.values())))
        lines.append("")
    return lines


def _format_motive_table(
    rows: list[tuple], *, mode_label: str = "cycling"
) -> list[str]:
    """Trip/energy share by `MOT_SEQ_COMPL` motive (section 9.9 point 1
    follow-up, "decompose energy per motive"), largest energy share
    first, plus a needs-excluded (`NEEDS_EXCLUDED_MOTIVE_CODES`)
    rollup row -- the evidence behind this report's needs-only scope."""
    total_weighted_n = sum(row[2] for row in rows)
    total_energy_kh = sum(row[3] for row in rows)
    total_energy_cp = sum(row[4] for row in rows)
    lines = [
        "| Motive | n | weighted n | trip share | energy share (kh) | "
        "energy share (cp) | mean distance (km) | mean duration (min) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    excluded_weighted_n = 0.0
    excluded_energy_kh = 0.0
    excluded_energy_cp = 0.0
    for motive, n, weighted_n, energy_kh, energy_cp, mean_dist, mean_dur in rows:
        label = (
            "missing/refused"
            if motive is None
            else emp2019.MOTIVE_LABEL_BY_CODE.get(motive, f"code {motive:g}")
        )
        lines.append(
            f"| {motive if motive is not None else '-'} {label} | {n} | "
            f"{weighted_n:,.0f} | {weighted_n / total_weighted_n:.1%} | "
            f"{energy_kh / total_energy_kh:.1%} | "
            f"{energy_cp / total_energy_cp:.1%} | {mean_dist:.2f} | {mean_dur:.1f} |"
        )
        if motive in emp2019.NEEDS_EXCLUDED_MOTIVE_CODES:
            excluded_weighted_n += weighted_n
            excluded_energy_kh += energy_kh
            excluded_energy_cp += energy_cp
    excluded_codes = ", ".join(f"{c:g}" for c in emp2019.NEEDS_EXCLUDED_MOTIVE_CODES)
    lines += [
        "",
        f"**Excluded from the main report's scope** (motives {excluded_codes}: "
        + ", ".join(
            emp2019.MOTIVE_LABEL_BY_CODE[c] for c in emp2019.NEEDS_EXCLUDED_MOTIVE_CODES
        )
        + f"), among {mode_label} trips: "
        f"{excluded_weighted_n / total_weighted_n:.1%} of weighted trips, "
        f"{excluded_energy_kh / total_energy_kh:.1%} of weighted energy (kh), "
        f"{excluded_energy_cp / total_energy_cp:.1%} (cp).",
    ]
    return lines


def write_markdown(md_path: Path, out_dir: Path, results: dict) -> None:
    """Write the section 9.9 re-estimation report (steps 1-3, 5, F8),
    for either survey (``results['survey_name']``, section 9.9's "Change
    between 2008 and 2019")."""
    config = results["config"]
    carpool = config.car.carpool_passenger
    walk_trips = results["walk_trips_by_day_group"]
    walk_driver = walk_trips.get("car_driver", float("nan"))
    walk_household = walk_trips.get("car_passenger_household", float("nan"))
    walk_carpool = walk_trips.get("car_passenger_carpool", float("nan"))
    survey_name = results["survey_name"]
    is_emp2019 = survey_name == emp2019.SURVEY_NAME
    if is_emp2019:
        variables_used_line = (
            "**Variables used** (K_DEPLOC unless noted): mode `mtp`; duration "
            "`DUREE`; distance `MDISTTOT_fin`; purpose `MMOTIFDES`/`MOTPREC` "
            "(read, not used by this step's formulas); companions "
            "`MACCOMPM`/`MACCOMPHM` (household vs carpool passenger split); day "
            "`TYPEJOUR`, `mobloc` (F8's local-trips variant); weights "
            "`POND_JOUR` (day) and `pond_indC` (K_INDIVIDU, individual); age "
            "band `AGE6` (TCM_IND_KISH); population category (section 6.1) from "
            "`SITUA` (TCM_IND_KISH) combined with `AGE` for the 6-17 children "
            "group; density of residence `TCM_MEN.DENSITECOM_RES`/"
            "`STATUTCOM_UU_RES` (27 October 2026 decision: the residence "
            "commune's own density, not a trip end's); non-traveller "
            "cross-check `MIMMOSEM` (K_INDIVIDU)."
        )
    else:
        variables_used_line = (
            "**Variables used** (`docs/data/entd2008.md`'s complete mapping, "
            "K_DEPLOC unless noted): mode `V2_MTP` (converted); duration "
            "`v2_mduree`/`V2_DUREE`; distance `distcor`/`V2_MDISTTOT`; purpose "
            "`V2_MMOTIFDES`/`V2_MMOTIFORI` (converted); companions "
            "`V2_MACCOMPM`/`V2_MACCOMPHM`; day `V2_TYPJOUR`, `mobloc` (from "
            "`V2_DLOCAL`); weights `POIDS_JOUR` (day) and `PONDKI` "
            "(K_INDIVIDU, individual); age band `AGE6` (Q_TCM_INDIVIDU); "
            "population category (section 6.1) from `SITUA` (Q_TCM_INDIVIDU) "
            "combined with `AGE` for the 6-17 children group; density: "
            "`Q_TCM_MENAGE.numcom_UUCat`/`TU99`, the residence commune's own "
            "density proxy (27 October 2026 decision; no density grid in "
            "ENTD 2008); non-traveller check `V2_MOBILREF` (K_INDIVIDU, "
            "reference weekday only)."
        )
    lines = [
        f"# Step 11 (`mobgrid/budget`): {survey_name} re-estimation (section 9.9)",
        "",
        "Generated by `python -m mobgrid.budget.emp`. Rebuilds section 9.9's "
        f"re-estimation steps 1-3 and 5 on the {survey_name} public tables, "
        "plus the F8 robustness check; terminal legs reuse sections 9.4-9.7's "
        "formulas and `config/energy.yaml`'s already-calibrated car/stairs/"
        "waiting/PT-ride defaults, plus provisional PT headway/station-height/"
        "access-walk defaults (TODO(confirm), `config.pt_ride`). EMC² (step "
        "4) and Ē_c (step 6) are out of scope. Same model parameters "
        "(`config/energy.yaml`) in both surveys: differences reflect "
        'behaviour, not the model (section 9.9, "Change between 2008 and '
        '2019"). Density: '
        f"`{results['density_source']}` "
        "(the INSEE grid, or section 9.9's urban-unit-status x "
        "residence-size proxy; ENTD 2008 always uses the proxy).",
        "",
        variables_used_line,
        "",
        '**Sample flow** (persons and days kept apart, section 9.9\'s '
        '"Change between 2008 and 2019"; one described day per respondent '
        "in EMP 2019, up to three in ENTD 2008, weekday/Saturday/Sunday):",
        "",
        "| Step | n |",
        "|---|---|",
        f"| Respondents | {results['n_respondents']:,} |",
        "| Days with trips"
        + (
            " ("
            + ", ".join(
                f"{count:,} {_DAY_TYPE_LABEL.get(day_type, f'type {day_type}')}"
                for day_type, count in results["days_with_trips_by_type"]
            )
            + ")"
            if not is_emp2019
            else ""
        )
        + f" | {results['n_days_with_trips']:,} |",
        f"| Days with energy | {results['n_days_with_energy']:,} |",
        f"| Days within scope | {results['n_days_within_scope']:,} |",
        f"| Days within scope with energy | {results['n_days']:,} |",
        "",
        f"{results['non_traveler_n']:,} of {results['n_respondents']:,} "
        "respondents report no trip "
        + ("that day" if is_emp2019 else "on the reference weekday")
        + f" ({results['non_traveler_share_unweighted']:.1%} unweighted, "
        f"{results['non_traveler_share_weighted']:.1%} by individual weight; "
        "reported apart per point 2).",
        "",
        "## Main-mode-of-the-day groups (point 3)",
        "",
        "walking only, bike, car driver, car passenger with a household "
        "driver, car passenger with a non-household driver (carpool), "
        "urban PT, train (short- and long-distance merged, step 11 round 8: "
        "train_long had too few observations to be a meaningful separate "
        "group), multimodal (two or more distinct non-walk modes in the day; "
        "driving and riding as a passenger count as two), other. "
        f"**'other' contains:** {emp2019.OTHER_MODE_DESCRIPTION}.",
        "",
        f"**Children as car drivers** ({results['children_car_driver_n']} "
        "children_6_17 car_driver days): the raw `mtp` code is "
        + ", ".join(
            f"{code:g} (n={n}, ages {age_min}-{age_max})"
            for code, n, age_min, age_max in results["children_car_driver_mtp"]
        )
        + '. Both codes are `mtp` category 3 "Automobile" (3.1 '
        '"Conducteur", 3.3 "Tantot conducteur tantot passager"), not a '
        "two-wheeler code (2.x): no two-wheeler reclassification applies. "
        '`mtp` 3.1 includes "voiturette" (a license-free microcar, legal '
        "from age 14 in France), plausible for the 14-17 share, but not "
        "for the many 6-13 year olds here; most likely EMP's own "
        "household/accompanying-trip coding records the car's use rather "
        "than confirming the child personally drove.",
        "",
        "## Density classes",
        "",
        "INSEE's own 4-level grid names and order: dense (1, densely "
        "populated communes), intermediate (2), sparse (3, peu denses), "
        "very_sparse (4, tres peu denses). EMP 2019's `emp2019._DENSITY_"
        "LABEL_BY_CODE` maps `DENSITECOM_ORI`/`_DES` directly (grid); both "
        "surveys' `trip_legs.density_proxy_case_sql` computes the same "
        "four labels from the urban-unit-status x residence-size proxy of "
        'section 9.9\'s "Change between 2008 and 2019" when '
        f"`density_source='proxy'` (this report: `{results['density_source']}`). "
        "`trip_legs._DENSITY_KEY_TRANSLATION` re-keys `config.car`/"
        "`config.pt_ride`'s existing density defaults (chosen for step 7 "
        "as `dense`/`urban`/`suburban`/`rural`) to these same INSEE names "
        "and order, checked against `data/raw/emp2019/emp2019-categories.pdf`'s "
        '"Degre de densite" table. `home_density` (every per-day/per-person '
        "table below) is the **residence** commune's own density "
        "(`trip_legs.residence_density`; 27 October 2026 decision), from "
        "`TCM_MEN.DENSITECOM_RES`/`STATUTCOM_UU_RES` (EMP 2019) or "
        "`Q_TCM_MENAGE.numcom_UUCat`/`TU99` (ENTD 2008, proxy only) -- not "
        "the density of the trip departing from home, which this "
        "replaces: that proxy was undefined for a day with no "
        "home-departing trip in scope, and was not a property of the "
        "person.",
        "",
        "## Time budget: constancy across density classes (point 3)",
        "",
        "The reference constant (section 9.9, 27 October 2026 decision): "
        "is mean daily travel time the same across density classes of "
        "residence, within each population category? Day with trips, "
        "needs scope. Cells of fewer than 50 persons blank. The 95% CI "
        "column (bootstrap over households) gives time the same "
        "treatment energy already has (section 9.9's income update).",
        "",
        *_format_category_density_table(
            results["category_density_stats"], results["category_density_time_ci"]
        ),
        "",
        "### Constancy summary",
        "",
        *_format_constancy_summary_table(results["density_constancy_summary"]),
        "",
        "## Time budget: constancy across income quintiles (section 9.9's "
        "income update)",
        "",
        "Household income per consumption unit (modified OECD scale), in "
        "quintiles computed within this survey with individual weights "
        "(`docs/data/entd2008.md`'s \"Income variables\"): is mean daily "
        "travel time the same across income quintiles, within each "
        "population category, as income is treated as density is? Day "
        "with trips, needs scope. `'unknown'` (missing/refused income) "
        "is its own class, excluded from the constancy summary (not an "
        "ordered quantile).",
        "",
        *_format_category_key_table(
            results["category_income_stats"],
            ("q1", "q2", "q3", "q4", "q5", "unknown"),
            "Income quintile",
            results["category_income_time_ci"],
        ),
        "",
        "### Constancy summary",
        "",
        *_format_constancy_summary_table(
            results["income_constancy_summary"], named_label="q5/q1"
        ),
        "",
        "## Trips per day and minutes per trip, by category, density and "
        "income quintile (section 9.9 point 2: daily time = trips/day x "
        "minutes/trip)",
        "",
        "### Trips per day",
        "",
        "#### By population category x density class",
        "",
        *_format_scalar_category_key_table(
            results["trips_by_category_density"],
            trip_legs.DENSITY_LABELS,
            "Density",
            label="trips/day",
        ),
        "",
        "#### By population category x income quintile",
        "",
        *_format_scalar_category_key_table(
            results["trips_by_category_income"],
            ("q1", "q2", "q3", "q4", "q5", "unknown"),
            "Income quintile",
            label="trips/day",
        ),
        "",
        "### Minutes per trip",
        "",
        "#### By population category x density class",
        "",
        *_format_scalar_category_key_table(
            results["minutes_per_trip_by_category_density"],
            trip_legs.DENSITY_LABELS,
            "Density",
            label="min/trip",
        ),
        "",
        "#### By population category x income quintile",
        "",
        *_format_scalar_category_key_table(
            results["minutes_per_trip_by_category_income"],
            ("q1", "q2", "q3", "q4", "q5", "unknown"),
            "Income quintile",
            label="min/trip",
        ),
        "",
        "#### By density class and by income quintile (marginals)",
        "",
        *_format_scalar_group_table(
            results["trips_by_density_scalar"], label="trips/day"
        ),
        "",
        *_format_scalar_group_table(results["trips_by_income"], label="trips/day"),
        "",
        *_format_scalar_group_table(
            results["minutes_per_trip_by_population"], label="min/trip"
        ),
        "",
        *_format_scalar_group_table(
            results["minutes_per_trip_by_density"], label="min/trip"
        ),
        "",
        *_format_scalar_group_table(
            results["minutes_per_trip_by_income"], label="min/trip"
        ),
        "",
        "## Per-person budget, days without trips included (section 9.9 "
        "point 2b)",
        "",
        "P(out on the weekday) x T(weekday|out), weekday only (comparable "
        "with ENTD 2008's own, unverified-weekend-eligibility budget); "
        + (
            "EMP 2019 additionally reports the all-week budget, Sigma_d "
            "w_d . P(out on day type d) . T(d|out), w_d = 5/7, 1/7, 1/7 "
            "(P from `IMMODEP_A`-`G`, T from the described days of each "
            "day type; point estimate only, no bootstrap CI)."
            if results["person_budget_all_week_population"] is not None
            else "ENTD 2008 reports the weekday budget only: its weekend "
            "eligibility is unverified (`docs/progress.md`)."
        ),
        "",
        "### By population category",
        "",
        "#### Weekday",
        "",
        *_format_person_budget_table(results["person_budget_weekday_population"]),
        "",
    ]
    if results["person_budget_all_week_population"] is not None:
        lines += [
            "#### All-week",
            "",
            *_format_person_budget_table(results["person_budget_all_week_population"]),
            "",
        ]
    lines += [
        "### By population category x density class (weekday budget)",
        "",
        *_format_person_budget_key_table(
            results["person_budget_weekday_category_density"],
            trip_legs.DENSITY_LABELS,
            "Density",
        ),
        "",
        "### By population category x income quintile (weekday budget)",
        "",
        *_format_person_budget_key_table(
            results["person_budget_weekday_category_income"],
            ("q1", "q2", "q3", "q4", "q5"),
            "Income quintile",
        ),
        "",
    ]
    if results["quirk_fill_rates"] is not None:
        rates = results["quirk_fill_rates"]
        lines += [
            "## Quirks: `distcor`/`v2_mduree` fill rate and mean change (section 9.9)",
            "",
            "`k_deploc`'s seven undocumented correction columns "
            '(`docs/data/entd2008.md`\'s "Quirks"); `distcor`/`v2_mduree` '
            "are used (when filled) by `trips_norm`, the other five are not.",
            "",
            f"- `distcor`: {rates['distcor_fill_rate']:.2%} filled, mean "
            f"change {rates['distcor_mean_change_km']:.2f} km "
            "(corrected - declared) where filled."
            if rates["distcor_mean_change_km"] is not None
            else f"- `distcor`: {rates['distcor_fill_rate']:.2%} filled.",
            f"- `v2_mduree`: {rates['v2_mduree_fill_rate']:.2%} filled, mean "
            f"change {rates['v2_mduree_mean_change_min']:.2f} min "
            "(corrected - declared) where filled."
            if rates["v2_mduree_mean_change_min"] is not None
            else f"- `v2_mduree`: {rates['v2_mduree_fill_rate']:.2%} filled "
            "(never filled in this release: `duration_min` always falls "
            "back to `V2_DUREE`).",
            "",
        ]
    lines += [
        "## Mean daily energy and time by main-mode group (point 3)",
        "",
        *_format_group_table(results["mode_stats"]),
        "",
        "## Section 9.9's scope: commuting and travel for needs fulfilment",
        "",
        "Every table and figure above and below is restricted to this "
        "scope (2026-10-20 project decision, not an optional variant): "
        "trips whose corrected motive (`motive`, `MOT_SEQ_COMPL`) is "
        'sport (7.6), a destination-less stroll (7.7, "se promener sans '
        'destination precise"), going to a place to walk/ride (7.8, a '
        "destination exists, but the movement itself is the point), or "
        "any top-level motive group 8 purpose (8.1-8.4: holidays, "
        "second/occasional residence, other private reasons -- none of "
        "them a needs-fulfilment destination) are excluded from every "
        "day's energy/time sums and from day classification; a day whose "
        "only trips were these becomes a non-traveller for this analysis. "
        "A missing/refused motive is kept, not excluded. See F9 and the "
        "table below for the evidence behind this decision, computed on "
        "the full, pre-exclusion dataset.",
        "",
        "| Group | excluded trip share | n excluded / n total | excluded "
        "share of day energy (kh) | excluded share of day energy (cp) |",
        "|---|---|---|---|---|",
    ]
    excluded_energy_by_group = {
        row[0]: (row[1], row[2]) for row in results["excluded_energy_shares"]
    }
    for mode, trip_share, n_excluded, n_total in results["excluded_trip_shares"]:
        energy_kh, energy_cp = excluded_energy_by_group.get(mode, (float("nan"),) * 2)
        lines.append(
            f"| {mode} | {trip_share:.1%} | {n_excluded:,} / {n_total:,} | "
            f"{energy_kh:.1%} | {energy_cp:.1%} |"
        )
    lines += [
        "",
        "## Data-quality correction: implausible door-to-door speeds",
        "",
        "Trips are corrected, not dropped (section 9.9, step 11 round 5): "
        "flagged above an upper speed bound only -- walk > "
        f"{emp2019.WALK_SPEED_UPPER_KMH:g} km/h, bike > "
        f"{emp2019.CYCLE_SPEED_UPPER_KMH:g} km/h, car (driver or passenger) > "
        f"{emp2019.CAR_SPEED_UPPER_KMH:g} km/h -- their declared distance is "
        "replaced by declared duration x the mode's own median speed "
        "(from its not-flagged trips). Cycling energy's main work term "
        'is time-based (round 4), but its "stops" sub-term still '
        "multiplies by distance and by the distance-derived ride speed "
        "squared (section 9.7), so a flagged bike trip's distance is "
        "corrected too, like walk and car (round 9).",
        "",
        *[
            f"- {mode}: {corrected:,} of {total:,} trips corrected"
            for mode, corrected, total in results["quality_counts"]
        ],
        "",
        "## Mean daily energy and time by main-mode group, overall and by "
        "population category (F4)",
        "",
        *_format_group_table_by_panel(results["f4_panels"]),
        "## By population category (section 6.1)",
        "",
        *_format_group_table(results["population_stats"]),
        "",
        "## By home density class",
        "",
        *_format_group_table(results["density_stats"]),
        "",
        "## Car passengers (F7)",
        "",
        f"- Carpool trips: {results['carpool_n']:,.0f} of "
        f"{results['carpool_household_n']:,.0f} weighted passenger trips "
        f"({results['carpool_share']:.1%} share).",
        "- Daily totals of both passenger groups: see "
        "`car_passenger_household`/`car_passenger_carpool` rows of the "
        "main-mode-group table above.",
        "- Mean walking trips per day: "
        f"driver {walk_driver:.2f}, household passenger {walk_household:.2f}, "
        f"carpool passenger {walk_carpool:.2f}.",
        "- **Carpool premium** (the extra origin-side walk/wait before the "
        "car, section 9.6): `config.car.carpool_passenger.walk_to_meeting_point_min` = "
        f"{carpool.walk_to_meeting_point_min:g} min, "
        f"`.wait_standing_min` = {carpool.wait_standing_min:g} min -- "
        "TODO(confirm), no survey or observed pickup pattern.",
        "",
        "## F8 robustness (time and energy; max/min ratio and CV of the "
        "group means, walk/bike/driver/both passenger groups/urban PT/"
        "train, over the terminal-legs variants: declared (base case), "
        "declared + 1 min, and the former section 9.4-9.7 defaults at "
        "x0.5/x1/x1.5, plus weekdays-only, local-trips-only and P0)",
        "",
        *_format_robustness_table(results["robustness_rows"]),
        "",
        "## Constancy test (point 3, 5): energy (Kolbl & Helbing's hypothesis)",
        "",
        f"- Overall weighted mean daily energy: {results['mean_kh']:.1f} kJ (kh), "
        f"{results['mean_cp']:.1f} kJ (compendium); Koelbl & Helbing's (2003) "
        f"hypothesis is {daily_energy.KH_DAILY_ENERGY_KJ:g} kJ.",
        "- Max/min ratio of the day-mode-group means "
        f"({', '.join(daily_energy.DAY_MODE_GROUPS)}): "
        f"{results['ratio_kh']:.2f} (kh), {results['ratio_cp']:.2f} (compendium).",
        "- Method-of-moments gamma fit (point 5): shape="
        f"{results['gamma_kh'][0]:.2f}, scale={results['gamma_kh'][1]:.1f} kJ (kh); "
        f"shape={results['gamma_cp'][0]:.2f}, scale={results['gamma_cp'][1]:.1f} kJ "
        "(compendium).",
        f"- Mean trips per person and day: {results['trips_mean']:.2f} "
        f"(95% CI [{results['trips_ci'][0]:.2f}, {results['trips_ci'][1]:.2f}]).",
        "",
        "## Calibrated v0 and P0 (step 1)",
        "",
        "- **v0 estimator:** the ratio of weighted sums of distance and "
        "duration, sum(POND_JOUR*distance)/sum(POND_JOUR*duration), not an "
        "average of per-trip speeds (avoids the bias of averaging a ratio).",
        f"- Overall v0: {results['v0_overall'].speed_kmh:.2f} km/h, n="
        f"{results['v0_overall'].n} (configured: {config.walking.v0_kmh:g} km/h).",
        "- **P0 estimator:** the trip's own terminal-leg walk (27 October "
        "2026 decision: `terminal_legs='declared'`, each trip's own "
        "`MTEMPSMAP`/`V2_MTEMPSMAP`, falling back to the section 9.4-9.7 "
        "defaults where missing) and the expected stop delays (section 9.7, "
        "Webster 1958) are subtracted from the declared duration at the "
        "naive speed before computing the ride speed; P0 is "
        "`bike.required_power_w` at the single ratio-estimated implied "
        "flat speed (not an average of per-trip, nonlinear P0 values). "
        "EMP 2019's own mode codes do not separate e-bikes from bicycles "
        '(`mtp` 2.1 includes "assistance electrique"), so they cannot be '
        "excluded or reported apart.",
        f"- Overall P0: {results['p0_overall'].p0_w:.1f} W at an implied flat "
        f"speed of {results['p0_overall'].implied_flat_speed_kmh:.2f} km/h, n="
        f"{results['p0_overall'].n} (configured `config.bike.power.p0_w` = "
        f"{config.bike.power.p0_w:g} W; section 9.7's reference: "
        f"{P0_REFERENCE_W:g} W at 16 km/h). `config/energy.yaml` is not "
        "changed by this calibration.",
        "",
        "| Age band (AGE6) | n walk | v0 (km/h) | n cycle | implied flat "
        "speed (km/h) | P0 (W) |",
        "|---|---|---|---|---|---|",
    ]
    p0_by_band = {stat.group: stat for stat in results["p0_by_age_band"]}
    for v0_stat in results["v0_by_age_band"]:
        p0_stat = p0_by_band.get(v0_stat.group)
        p0_text = (
            f"{p0_stat.n} | {p0_stat.implied_flat_speed_kmh:.2f} | {p0_stat.p0_w:.1f}"
            if p0_stat
            else "0 | - | -"
        )
        lines.append(
            f"| {v0_stat.group} | {v0_stat.n} | {v0_stat.speed_kmh:.2f} | {p0_text} |"
        )

    lines += [
        "",
        "## Declared vs modelled walk/wait minutes, by mode group (step 1)",
        "",
        "Unweighted trip-level means. Since the 27 October 2026 decision, "
        "the declared value *is* the model's terminal-leg walk/wait by "
        "default (`terminal_legs='declared'`, falling back to the "
        "modelled default where missing): \"modelled\" below is the "
        "section 9.4-9.7 default this report no longer uses by default, "
        "kept as the comparison point.",
        "",
        "| Mode group | n | declared walk (min) | modelled walk (min) | "
        "declared wait (min) | modelled wait (min) |",
        "|---|---|---|---|---|---|",
    ]
    for row in results["declared_vs_modelled_walk_wait"]:
        mode_group, declared_walk, declared_wait, modelled_walk, modelled_wait, n = row
        lines.append(
            f"| {mode_group} | {n} | "
            + (f"{declared_walk:.1f}" if declared_walk is not None else "-")
            + " | "
            + f"{modelled_walk:.1f} | "
            + (f"{declared_wait:.1f}" if declared_wait is not None else "-")
            + " | "
            + (f"{modelled_wait:.1f}" if modelled_wait is not None else "-")
            + " |"
        )

    cycle_all = next(s for s in results["mode_stats"] if s.group == "cycle")
    cycle_weekday = results["cycle_weekday_stats"]
    lines += [
        "",
        "## Cycle group, after the fix (point 3)",
        "",
        "Cycling energy's work term is now time-based at the single "
        f"calibrated P0 ({config.bike.power.p0_w:g} W, declared ride minutes "
        "x riding rate), not at each trip's own implied, per-trip power "
        "(section 9.9, step 11 third round: see `build_trip_legs`'s "
        "docstring for why the per-trip approach inflated energy).",
        "",
        "| Variant | n | mean energy kh (kJ) | median energy kh (kJ) | "
        "mean energy cp (kJ) | median energy cp (kJ) |",
        "|---|---|---|---|---|---|",
        f"| all days | {cycle_all.n} | {cycle_all.mean_energy_kh_kj:.1f} | "
        f"{cycle_all.median_energy_kh_kj:.1f} | {cycle_all.mean_energy_cp_kj:.1f} | "
        f"{cycle_all.median_energy_cp_kj:.1f} |",
    ]
    if cycle_weekday is not None:
        lines.append(
            f"| weekdays only | {cycle_weekday.n} | "
            f"{cycle_weekday.mean_energy_kh_kj:.1f} | "
            f"{cycle_weekday.median_energy_kh_kj:.1f} | "
            f"{cycle_weekday.mean_energy_cp_kj:.1f} | "
            f"{cycle_weekday.median_energy_cp_kj:.1f} |"
        )

    dec = results["cycle_decomposition"]
    lines += [
        "",
        "### Post-fix cycle-day decomposition (point 3)",
        "",
        "Ride work, unloaded pedalling and stops are the same formula in "
        "both rate sets (section 9.7's mechanical/physiological terms); "
        "only get/park (a standing activity rate) and the day's walking "
        "legs (c0) differ by rate set.",
        "",
        f"- Mean ride time: {dec['ride_minutes']:.1f} min; ride work: "
        f"{dec['ride_work_kj']:.1f} kJ; unloaded pedalling: "
        f"{dec['unloaded_kj']:.1f} kJ.",
        f"- Stops: {dec['stops_kj']:.1f} kJ/day, "
        f"{dec['mean_n_stops_per_day']:.2f} stops/day at "
        f"`config.bike.stops.stops_per_km` = {dec['stops_per_km']:g}/km; "
        f"{dec['kj_per_stop']:.2f} kJ/stop.",
        f"- Get/park: {dec['get_park_minutes']:g} min/day fixed, "
        f"{dec['get_park_kh_kj']:.1f} kJ (kh), {dec['get_park_cp_kj']:.1f} kJ (cp).",
        f"- Walking trips of the same day: {dec['walk_minutes']:.1f} min/day, "
        f"{dec['walk_kh_kj']:.1f} kJ (kh), {dec['walk_cp_kj']:.1f} kJ (cp).",
    ]

    lines += [
        "",
        "### Cycling energy by motive (point 1 follow-up)",
        "",
        "`MOT_SEQ_COMPL`, EMP's own chain-level, corrected trip purpose "
        '(unlike the raw `MMOTIFDES`); excludes "return home"/"return '
        'to residence" codes 1.1-1.3 (a return leg is recoded to the '
        "purpose of the outward leg it closes). Full, pre-exclusion "
        "dataset (unlike every other table in this report): this is the "
        "evidence behind the needs-only scope above, not itself scoped "
        "to it; see also F9 for the same breakdown, every mode, "
        "top-level motive only.",
        "",
        *_format_motive_table(results["cycle_motive_decomposition"]),
    ]

    lines += [
        "",
        "## Non-traveller immobility (point 2)",
        "",
    ]
    if is_emp2019:
        lines += [
            "Identified as: a Kish respondent with zero rows in K_DEPLOC for "
            "their described day. Cross-check: every one of these respondents "
            f"has K_INDIVIDU's `MIMMOSEM` (weekday immobility) = 1 "
            f"({results['non_traveler_mimmosem_match']:.0%} match); `MDATE_jour` "
            "is blank only for these same respondents, so EMP 2019's public "
            "release records no day-of-week for a fully immobile respondent -- "
            "a Saturday/Sunday non-traveller cannot be told apart from a "
            "weekday one in these tables. The surveyed-day mix among "
            "travellers is "
            + ", ".join(
                f"TYPEJOUR={day_type}: {share:.1%}"
                for day_type, share in sorted(
                    results["traveler_day_type_share"].items()
                )
            )
            + f" (weekday-dominated: {results['non_traveler_share_weighted']:.1%} "
            "overall immobility is a weekday-weighted figure, not comparable "
            "to all-week averages that include weekends, when immobility is "
            "known to be much higher).",
        ]
    else:
        lines += [
            "Identified as: `k_individu.V2_MOBILREF = 0` (not mobile) on the "
            "reference weekday, weighted by `PONDKI` "
            '(`docs/data/entd2008.md`\'s "Persons without trips"); weekend '
            "immobility (`V2_MIMMOSAM`/`V2_MIMMODIM`) is not used, matching "
            "EMP 2019, which identifies weekday non-travellers only. "
            "Weekday share of persons without trips: "
            f"{results['non_traveler_share_unweighted']:.1%} unweighted, "
            f"{results['non_traveler_share_weighted']:.1%} by individual "
            "weight.",
        ]
    lines += [
        "",
        "## Figures",
        "",
    ]
    for path in results["figures"]:
        try:
            relative = path.relative_to(md_path.parent)
        except ValueError:
            relative = path
        lines.append(f"![{path.stem}]({relative.as_posix()})")
        lines.append("")

    lines += [
        "## Modelling notes and simplifications",
        "",
        "- EMP 2019 gives no headway, station-depth or PT access-walk-"
        "distance data; `config.pt_ride.headway_min_am_peak`/"
        "`station_height_m`/`access_walk_m_by_density` are provisional "
        "TODO(confirm) defaults, used only by this step.",
        "- Car terminal legs always use the apartment-density default: the "
        "public tables give no house/apartment split (section 9.6's "
        "`s_house`).",
        "- `mode_group='other'` trips have no energy formula and "
        "contribute 0 kJ to a day's total; a day with only such trips is "
        "its own 'other' group, separate from 'multimodal'.",
        "- The day's home density is the residence commune's own density "
        "(`trip_legs.residence_density`, 27 October 2026 decision), not "
        "the origin density of the home-departure trip.",
        "- Bike get/park and stop-delay adjustment: unreliable (would "
        "consume over half, or all but under a minute, of a very short "
        "trip's declared duration) for a small share of cycling trips; "
        "these fall back to the naive whole-duration speed for both "
        "energy and the P0 estimator's ride-time denominator.",
        "- F3/F4/F5 use the full set of day-mode groups (including "
        "multimodal and other); F8's robustness check is restricted to "
        "the seven groups the task names (walk, bike, driver, both "
        "passenger groups, urban PT, train).",
        "- F8's figure shows bootstrap CIs for every terminal-legs "
        "variant with a CI (declared, declared + 1 min, former defaults "
        "x0.5/x1/x1.5), not every table variant (not weekdays-only, "
        "local-trips-only or the P0 reference, which have none).",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _group_table_two_surveys(
    stats_a: list[daily_energy.GroupStats],
    label_a: str,
    stats_b: list[daily_energy.GroupStats],
    label_b: str,
) -> list[str]:
    """Markdown table: n, mean/median energy (both rate sets, with 95%
    CI on the means) and mean time, two surveys/variants side by side,
    one row per group present in either."""
    by_a = {s.group: s for s in stats_a}
    by_b = {s.group: s for s in stats_b}
    groups = sorted(
        set(by_a) | set(by_b),
        key=lambda g: -(by_a[g].weighted_n if g in by_a else by_b[g].weighted_n),
    )
    lines = [
        f"| Group | n ({label_a}) | n ({label_b}) | mean time ({label_a}) | "
        f"mean time ({label_b}) | mean kh ({label_a}) [CI] | "
        f"mean kh ({label_b}) [CI] | median kh ({label_a}) | "
        f"median kh ({label_b}) | mean cp ({label_a}) [CI] | "
        f"mean cp ({label_b}) [CI] | median cp ({label_a}) | "
        f"median cp ({label_b}) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for group in groups:
        a, b = by_a.get(group), by_b.get(group)

        def _cell(stat, attr, fmt="{:.1f}"):
            return fmt.format(getattr(stat, attr)) if stat else "-"

        def _ci_cell(stat, attr):
            if not stat:
                return "-"
            lo, hi = getattr(stat, attr)
            return f"[{lo:.1f}, {hi:.1f}]"

        lines.append(
            f"| {group} | {a.n if a else 0} | {b.n if b else 0} | "
            f"{_cell(a, 'mean_time_min')} | {_cell(b, 'mean_time_min')} | "
            f"{_cell(a, 'mean_energy_kh_kj')} {_ci_cell(a, 'mean_energy_kh_ci')} | "
            f"{_cell(b, 'mean_energy_kh_kj')} {_ci_cell(b, 'mean_energy_kh_ci')} | "
            f"{_cell(a, 'median_energy_kh_kj')} | {_cell(b, 'median_energy_kh_kj')} | "
            f"{_cell(a, 'mean_energy_cp_kj')} {_ci_cell(a, 'mean_energy_cp_ci')} | "
            f"{_cell(b, 'mean_energy_cp_kj')} {_ci_cell(b, 'mean_energy_cp_ci')} | "
            f"{_cell(a, 'median_energy_cp_kj')} | {_cell(b, 'median_energy_cp_kj')} |"
        )
    return lines


def _format_weekday_comparison(
    results_2008: dict, results_2019: dict, *, n_reps: int, seed: int
) -> list[str]:
    """Section 9.9's weekday-only 2008-2019 comparison (per day with
    trips and per person), with a bootstrap difference interval: ENTD
    2008 describes only the reference weekday, so this is the one
    scope both surveys' per-person budgets are directly comparable on
    (the per-day-with-trips comparison elsewhere in this report mixes
    weekday/Saturday/Sunday)."""
    lines = [
        "## Weekday-only comparison, 2008 vs 2019 (density proxy in "
        "both; section 9.9's per-person budget is only defined on the "
        "weekday in both surveys)",
        "",
        "### Daily time, per day with trips",
        "",
        "| Category | 2008 (min) | 2019 (min) | 2019 - 2008 | 95% CI |",
        "|---|---|---|---|---|",
    ]
    wd_2008, wd_2019 = results_2008["weekday_days"], results_2019["weekday_days"]
    for category in (*daily_energy.POPULATION_CATEGORIES, None):
        label = category or "overall"
        mask_2008 = (
            wd_2008["population_category"] == category
            if category
            else np.ones(len(wd_2008["pond_jour"]), dtype=bool)
        )
        mask_2019 = (
            wd_2019["population_category"] == category
            if category
            else np.ones(len(wd_2019["pond_jour"]), dtype=bool)
        )
        n8, n9 = int(mask_2008.sum()), int(mask_2019.sum())
        if n8 < MIN_CELL_N or n9 < MIN_CELL_N:
            lines.append(f"| {label} | - | - | - | - |")
            continue
        mean_2008 = float(
            np.sum(
                wd_2008["pond_jour"][mask_2008]
                * wd_2008["total_time_min"][mask_2008]
            )
            / wd_2008["pond_jour"][mask_2008].sum()
        )
        mean_2019 = float(
            np.sum(
                wd_2019["pond_jour"][mask_2019]
                * wd_2019["total_time_min"][mask_2019]
            )
            / wd_2019["pond_jour"][mask_2019].sum()
        )
        diff, ci = daily_energy.bootstrap_diff_ci(
            wd_2008["ident_men"][mask_2008],
            wd_2008["pond_jour"][mask_2008],
            wd_2008["total_time_min"][mask_2008],
            wd_2019["ident_men"][mask_2019],
            wd_2019["pond_jour"][mask_2019],
            wd_2019["total_time_min"][mask_2019],
            n_reps=n_reps,
            seed=seed,
        )
        lines.append(
            f"| {label} | {mean_2008:.1f} | {mean_2019:.1f} | {diff:+.1f} | "
            f"[{ci[0]:+.1f}, {ci[1]:+.1f}] |"
        )
    lines += [
        "",
        "### Daily time, per person (days without trips included)",
        "",
        "P(out on the weekday) x T(weekday|out); the difference shown is "
        "between the two surveys' independent point budgets, without a "
        "joint bootstrap interval (each side's own 95% CI is shown "
        "instead, from its single-survey per-person budget table above).",
        "",
        "| Category | 2008 (min) | 2008 95% CI | 2019 (min) | 2019 95% CI "
        "| 2019 - 2008 |",
        "|---|---|---|---|---|---|",
    ]
    budgets_2008 = results_2008["person_budget_weekday_population"]
    budgets_2019 = results_2019["person_budget_weekday_population"]
    for category in (*daily_energy.POPULATION_CATEGORIES, "overall"):
        row8, row9 = budgets_2008.get(category), budgets_2019.get(category)
        if row8 is None or row9 is None or row8.n == 0 or row9.n == 0:
            lines.append(f"| {category} | - | - | - | - | - |")
            continue
        ci8 = (
            f"[{row8.budget_ci[0]:.1f}, {row8.budget_ci[1]:.1f}]"
            if not np.isnan(row8.budget_ci[0])
            else "-"
        )
        ci9 = (
            f"[{row9.budget_ci[0]:.1f}, {row9.budget_ci[1]:.1f}]"
            if not np.isnan(row9.budget_ci[0])
            else "-"
        )
        lines.append(
            f"| {category} | {row8.budget:.1f} | {ci8} | {row9.budget:.1f} | "
            f"{ci9} | {row9.budget - row8.budget:+.1f} |"
        )
    lines.append("")
    return lines


def run_compare(
    out_path: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    n_reps: int = 200,
    seed: int = 0,
    emp2019_data_path: Path | None = None,
    entd2008_data_path: Path | None = None,
) -> Path:
    """Section 9.9's "Change between 2008 and 2019": runs EMP 2019 (grid
    and proxy density) and ENTD 2008 (proxy, its only option), then
    writes ``<out_path>.md`` with the 2008-2019 and grid-vs-proxy
    comparisons. None of the three runs' own figures/reports are a
    deliverable of ``--compare`` itself (run the plain, single-survey
    CLI for those): they go to a temporary directory, discarded once
    this report is written; only the one comparison figure below is
    kept, under ``out_path``.
    """
    out_path.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        results_2019_proxy = run(
            Path(tmp) / "emp2019_proxy",
            emp2019,
            emp2019_data_path,
            config_path,
            n_reps=n_reps,
            seed=seed,
            density_source="proxy",
        )
        results_2019_grid = run(
            Path(tmp) / "emp2019_grid",
            emp2019,
            emp2019_data_path,
            config_path,
            n_reps=n_reps,
            seed=seed,
            density_source="grid",
        )
        results_2008 = run(
            Path(tmp) / "entd2008_proxy",
            entd2008,
            entd2008_data_path,
            config_path,
            n_reps=n_reps,
            seed=seed,
            density_source="proxy",
        )

    lines = [
        "# Step 11 (`mobgrid/budget`): 2008-2019 comparison (section 9.9)",
        "",
        "Generated by `python -m mobgrid.budget.emp --compare`. Same model "
        "parameters in both years (`config/energy.yaml`); EMP 2019 is run "
        "with both the INSEE density grid and section 9.9's urban-unit-"
        "status x residence-size proxy, ENTD 2008 with the proxy only (no "
        "density grid in ENTD 2008).",
        "",
        "## Group table, 2008 vs 2019 (density proxy in both)",
        "",
        *_group_table_two_surveys(
            results_2008["mode_stats"],
            "2008",
            results_2019_proxy["mode_stats"],
            "2019",
        ),
        "",
        "## Time budget: by population category, 2008 vs 2019 (density "
        "proxy in both, section 9.9's 27 October 2026 decision)",
        "",
        *_group_table_two_surveys(
            results_2008["population_stats"],
            "2008",
            results_2019_proxy["population_stats"],
            "2019",
        ),
        "",
        "### Constancy summary (density within category), both years",
        "",
        "| Category | dense/very_sparse 2008 | dense/very_sparse 2019 | "
        "max/min 2008 | max/min 2019 | CV 2008 | CV 2019 |",
        "|---|---|---|---|---|---|---|",
    ]
    constancy_2008 = {r[0]: r for r in results_2008["density_constancy_summary"]}
    constancy_2019 = {r[0]: r for r in results_2019_proxy["density_constancy_summary"]}
    for category in daily_energy.POPULATION_CATEGORIES:
        c8, c9 = constancy_2008.get(category), constancy_2019.get(category)

        def _fmt_constancy(row, idx):
            return "-" if row is None or np.isnan(row[idx]) else f"{row[idx]:.2f}"

        lines.append(
            f"| {category} | {_fmt_constancy(c8, 1)} | {_fmt_constancy(c9, 1)} | "
            f"{_fmt_constancy(c8, 2)} | {_fmt_constancy(c9, 2)} | "
            f"{_fmt_constancy(c8, 3)} | {_fmt_constancy(c9, 3)} |"
        )
    lines += [
        "",
        "## EMP 2019: density grid vs proxy, same groups",
        "",
        *_group_table_two_surveys(
            results_2019_grid["mode_stats"],
            "grid",
            results_2019_proxy["mode_stats"],
            "proxy",
        ),
        "",
        "## Robustness (F8 base case, core and full scope, means)",
        "",
        "| Scope | energy ratio (kh), 2008 | energy ratio (kh), 2019 | "
        "CV (kh), 2008 | CV (kh), 2019 | energy ratio (cp), 2008 | "
        "energy ratio (cp), 2019 |",
        "|---|---|---|---|---|---|---|",
    ]
    rows_2008 = {
        r.scope: r
        for r in results_2008["robustness_rows"]
        if r.variant == "declared (base case)" and r.statistic == "mean"
    }
    rows_2019 = {
        r.scope: r
        for r in results_2019_proxy["robustness_rows"]
        if r.variant == "declared (base case)" and r.statistic == "mean"
    }
    for scope in ("core", "full"):
        r8, r9 = rows_2008.get(scope), rows_2019.get(scope)
        lines.append(
            f"| {scope} | "
            + (f"{r8.energy_kh_ratio:.2f}" if r8 else "-")
            + " | "
            + (f"{r9.energy_kh_ratio:.2f}" if r9 else "-")
            + " | "
            + (f"{r8.energy_kh_cv:.2f}" if r8 else "-")
            + " | "
            + (f"{r9.energy_kh_cv:.2f}" if r9 else "-")
            + " | "
            + (f"{r8.energy_cp_ratio:.2f}" if r8 else "-")
            + " | "
            + (f"{r9.energy_cp_ratio:.2f}" if r9 else "-")
            + " |"
        )

    lines += [
        "",
        "## Declared vs modelled walk/wait minutes per trip, car driver, "
        "urban PT and train, both years",
        "",
        "| Mode group | n, 2008 | n, 2019 | declared walk, 2008 | "
        "declared walk, 2019 | modelled walk, 2008 | modelled walk, 2019 | "
        "declared wait, 2008 | declared wait, 2019 | modelled wait, 2008 | "
        "modelled wait, 2019 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    by_group_2008 = {
        row[0]: row for row in results_2008["declared_vs_modelled_walk_wait"]
    }
    by_group_2019 = {
        row[0]: row for row in results_2019_proxy["declared_vs_modelled_walk_wait"]
    }
    for group in ("car_driver", "urban_pt", "train"):
        row8, row9 = by_group_2008.get(group), by_group_2019.get(group)

        def _fmt(row, idx):
            return f"{row[idx]:.1f}" if row and row[idx] is not None else "-"

        lines.append(
            f"| {group} | {row8[5] if row8 else 0} | {row9[5] if row9 else 0} | "
            f"{_fmt(row8, 1)} | {_fmt(row9, 1)} | {_fmt(row8, 3)} | {_fmt(row9, 3)} | "
            f"{_fmt(row8, 2)} | {_fmt(row9, 2)} | {_fmt(row8, 4)} | {_fmt(row9, 4)} |"
        )

    lines += [
        "",
        "## Weekday share of persons without trips, both years",
        "",
        f"- 2008: {results_2008['non_traveler_share_unweighted']:.1%} unweighted, "
        f"{results_2008['non_traveler_share_weighted']:.1%} by individual weight "
        f"(n={results_2008['non_traveler_n']} of "
        f"{results_2008['n_respondents']:,} respondents)",
        f"- 2019: {results_2019_proxy['non_traveler_share_unweighted']:.1%} "
        f"unweighted, {results_2019_proxy['non_traveler_share_weighted']:.1%} by "
        f"individual weight (n={results_2019_proxy['non_traveler_n']} of "
        f"{results_2019_proxy['n_respondents']:,} respondents)",
        "",
        "## 2008-calibrated v0 and P0 (for information only; the model "
        "uses the same parameters in both years, section 9.9)",
        "",
        f"- v0: {results_2008['v0_overall'].speed_kmh:.2f} km/h, "
        f"n={results_2008['v0_overall'].n} "
        f"(2019: {results_2019_proxy['v0_overall'].speed_kmh:.2f} km/h, "
        f"n={results_2019_proxy['v0_overall'].n})",
        f"- P0: {results_2008['p0_overall'].p0_w:.1f} W at an implied flat "
        f"speed of {results_2008['p0_overall'].implied_flat_speed_kmh:.2f} km/h, "
        f"n={results_2008['p0_overall'].n} "
        f"(2019: {results_2019_proxy['p0_overall'].p0_w:.1f} W, "
        f"n={results_2019_proxy['p0_overall'].n})",
        "",
        "## Overall (all groups combined), both years",
        "",
        f"- Mean daily energy: 2008 {results_2008['mean_kh']:.1f} kJ (kh), "
        f"{results_2008['mean_cp']:.1f} kJ (cp); 2019 "
        f"{results_2019_proxy['mean_kh']:.1f} kJ (kh), "
        f"{results_2019_proxy['mean_cp']:.1f} kJ (cp).",
        f"- Mean daily time: 2008 {results_2008['mean_time_min']:.1f} min; "
        f"2019 {results_2019_proxy['mean_time_min']:.1f} min.",
        "",
        *_format_weekday_comparison(
            results_2008, results_2019_proxy, n_reps=n_reps, seed=seed
        ),
    ]

    figure_path = _figure_compare_energy_time(
        results_2008["mode_stats"],
        results_2019_proxy["mode_stats"],
        (results_2008["mean_kh"], results_2019_proxy["mean_kh"]),
        (results_2008["mean_cp"], results_2019_proxy["mean_cp"]),
        (results_2008["mean_time_min"], results_2019_proxy["mean_time_min"]),
        out_path,
    )
    time_by_category_path = _figure_compare_time_by_category(
        results_2008["population_stats"],
        results_2019_proxy["population_stats"],
        out_path,
    )
    lines += [
        "## Figures",
        "",
        f"![{time_by_category_path.stem}]"
        f"({time_by_category_path.relative_to(out_path.parent).as_posix()})",
        "",
        f"![{figure_path.stem}]({figure_path.relative_to(out_path.parent).as_posix()})",
        "",
    ]

    md_path = out_path.with_suffix(".md")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def _figure_compare_energy_time(
    stats_2008: list[daily_energy.GroupStats],
    stats_2019: list[daily_energy.GroupStats],
    overall_mean_energy_kh: tuple[float, float],
    overall_mean_energy_cp: tuple[float, float],
    overall_mean_time_min: tuple[float, float],
    out_dir: Path,
) -> Path:
    """One figure: mean daily energy (both rate sets) and time by group,
    2008 vs 2019, with CI (section 9.9's "Outputs of the re-estimation"
    comparison list), plus each year's own global mean (all groups
    combined, the ``overall_mean_*`` tuples, 2008 then 2019) as a
    labelled horizontal reference line on every panel, as F4a does for
    the single-survey report."""
    by_2008 = {s.group: s for s in stats_2008}
    by_2019 = {s.group: s for s in stats_2019}
    groups = [g for g in daily_energy.DAY_MODE_GROUPS if g in by_2008 or g in by_2019]
    x = np.arange(len(groups))
    width = 0.35

    fig, (ax_energy_kh, ax_energy_cp, ax_time) = plt.subplots(1, 3, figsize=(19, 6))
    for ax, rate_key in ((ax_energy_kh, "kh"), (ax_energy_cp, "cp")):
        for offset, by_year, label in (
            (-width / 2, by_2008, "2008"),
            (width / 2, by_2019, "2019"),
        ):
            means = [
                getattr(by_year[g], f"mean_energy_{rate_key}_kj")
                if g in by_year
                else np.nan
                for g in groups
            ]
            lowers = [
                getattr(by_year[g], f"mean_energy_{rate_key}_kj")
                - getattr(by_year[g], f"mean_energy_{rate_key}_ci")[0]
                if g in by_year
                else 0.0
                for g in groups
            ]
            uppers = [
                getattr(by_year[g], f"mean_energy_{rate_key}_ci")[1]
                - getattr(by_year[g], f"mean_energy_{rate_key}_kj")
                if g in by_year
                else 0.0
                for g in groups
            ]
            ax.bar(
                x + offset,
                means,
                width,
                yerr=[lowers, uppers],
                label=label,
                capsize=2,
            )
    for offset, by_year, label in (
        (-width / 2, by_2008, "2008"),
        (width / 2, by_2019, "2019"),
    ):
        times = [by_year[g].mean_time_min if g in by_year else np.nan for g in groups]
        ax_time.bar(x + offset, times, width, label=label)

    for ax, overall_values, unit in (
        (ax_energy_kh, overall_mean_energy_kh, "kJ"),
        (ax_energy_cp, overall_mean_energy_cp, "kJ"),
        (ax_time, overall_mean_time_min, "min"),
    ):
        label_transform = ax.get_yaxis_transform()
        for value, year, color, va in (
            (overall_values[0], "2008", "tab:blue", "bottom"),
            (overall_values[1], "2019", "tab:orange", "top"),
        ):
            ax.axhline(value, color=color, linestyle="--", linewidth=1.0)
            # Left-anchored (not right): a right-anchored label can
            # render into the neighbouring subplot's own white
            # background and look clipped there, since adjacent panels
            # share a narrow gap (``fig.tight_layout()`` does not widen
            # it for text added after the axes are built).
            ax.text(
                0.02,
                value,
                f"{year}: {value:.0f} {unit}",
                transform=label_transform,
                color=color,
                fontsize=8,
                ha="left",
                va=va,
            )

    ax_energy_kh.set_xticks(x)
    ax_energy_kh.set_xticklabels(groups, rotation=30, ha="right")
    ax_energy_kh.set_ylabel("Mean daily energy, kJ (KH)")
    ax_energy_kh.legend()
    ax_energy_cp.set_xticks(x)
    ax_energy_cp.set_xticklabels(groups, rotation=30, ha="right")
    ax_energy_cp.set_ylabel("Mean daily energy, kJ (compendium)")
    ax_energy_cp.legend()
    ax_time.set_xticks(x)
    ax_time.set_xticklabels(groups, rotation=30, ha="right")
    ax_time.set_ylabel("Mean daily time, minutes")
    ax_time.legend()
    fig.suptitle(
        "Mean daily energy (both rate sets) and time by main-mode group, "
        "2008 vs 2019 (density proxy in both, section 9.9); dashed lines "
        "are each year's own global mean, all groups combined"
    )
    fig.tight_layout()
    path = out_dir / "compare_energy_time.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_compare_time_by_category(
    stats_2008: list[daily_energy.GroupStats],
    stats_2019: list[daily_energy.GroupStats],
    out_dir: Path,
) -> Path:
    """Time by population category, 2008 vs 2019 (section 9.9, 27
    October 2026 decision: the time budget's own b_k, one value per
    category, is now the reference constant). Day with trips, needs
    scope, density proxy in both years."""
    by_2008 = {s.group: s for s in stats_2008}
    by_2019 = {s.group: s for s in stats_2019}
    categories = [
        c for c in daily_energy.POPULATION_CATEGORIES if c in by_2008 or c in by_2019
    ]
    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))
    for offset, by_year, label in (
        (-width / 2, by_2008, "2008"),
        (width / 2, by_2019, "2019"),
    ):
        means = [
            by_year[c].mean_time_min if c in by_year else np.nan for c in categories
        ]
        ns = [by_year[c].n if c in by_year else 0 for c in categories]
        bars = ax.bar(x + offset, means, width, label=label)
        for bar, n in zip(bars, ns, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"n={n}",
                ha="center",
                va="bottom",
                fontsize=6,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylabel("Mean daily travel time, minutes")
    ax.set_title(
        "Daily travel time by population category, 2008 vs 2019\n"
        "(day with trips, needs scope, density proxy in both, section 9.9)",
        fontsize=10,
    )
    ax.legend()
    fig.tight_layout()
    path = out_dir / "compare_time_by_category.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-estimate section 9.9's daily energy budget (EMP 2019 "
        "and ENTD 2008)."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--survey",
        choices=["emp2019", "entd2008"],
        default="emp2019",
    )
    parser.add_argument("--data-path", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--density",
        choices=["grid", "proxy"],
        default=None,
        help="Density source; defaults to the survey's own "
        "DEFAULT_DENSITY_SOURCE ('grid' for EMP 2019, 'proxy' for ENTD "
        "2008, which has no density grid and always uses it).",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run both surveys and write the 2008-2019 comparison report "
        "to <out>.md instead of a single-survey report.",
    )
    parser.add_argument(
        "--emp2019-data-path",
        type=Path,
        default=None,
        help="With --compare: EMP 2019 data path (default: emp2019.DEFAULT_DATA_PATH).",
    )
    parser.add_argument(
        "--entd2008-data-path",
        type=Path,
        default=None,
        help="With --compare: ENTD 2008 raw directory (default: "
        "entd2008.DEFAULT_DATA_PATH).",
    )
    args = parser.parse_args(argv)

    if args.compare:
        md_path = run_compare(
            args.out,
            args.config,
            n_reps=args.bootstrap_reps,
            seed=args.seed,
            emp2019_data_path=args.emp2019_data_path,
            entd2008_data_path=args.entd2008_data_path,
        )
        print(f"Wrote {md_path}")
        return 0

    survey = {"emp2019": emp2019, "entd2008": entd2008}[args.survey]
    results = run(
        args.out,
        survey,
        args.data_path,
        args.config,
        n_reps=args.bootstrap_reps,
        seed=args.seed,
        density_source=args.density,
    )
    md_path = args.out.with_suffix(".md")
    write_markdown(md_path, args.out, results)
    print(f"Wrote {len(results['figures'])} figures to {args.out} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
