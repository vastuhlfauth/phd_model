"""Section 9.9 re-estimation on EMP 2019: CLI, figures and report (step 11).

``python -m mobgrid.budget.emp --out docs/data/step11_budget`` extracts
the public EMP 2019 tables, rebuilds every respondent's surveyed day as
legs (``emp2019``), aggregates it to a daily travel time/energy budget
and runs the hypothesis test of steps 1-3 and 5 (``daily_energy``), plus
the F8 robustness check added to section 9.9. EMC² (step 4) and Ē_c
(step 6) are out of scope.

Writes figures F1, F3 (Compendium + a KH appendix), F4-F8 to ``--out``
and a Markdown report to ``<out>.md``, mirroring ``mobgrid.energy.checks``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mobgrid.budget import daily_energy, emp2019
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
    activity_rate_kj_per_min,
    load_energy_config,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"
DEFAULT_OUT_DIR = ROOT / "docs" / "data" / "step11_budget"

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
    each day's weight once per leg).
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

    rows = con.sql("""
        SELECT ident_ind, mode_group, distance_km, bike_ride_time_for_energy_s,
            duration_min, pond_jour
        FROM trip_legs
        WHERE ident_ind IN
            (SELECT ident_ind FROM day_summary WHERE day_mode_group = 'cycle')
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

    # One shared ident_ind -> day-index map (every row here belongs to a
    # cycle day, so a leg's ident_ind is always one of ``cycle_days``);
    # sums each component to one total per day (a day can have more than
    # one leg of the same mode) via bincount, not a Python-level loop.
    cycle_days, cycle_index = np.unique(rows["ident_ind"], return_inverse=True)
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
        "SELECT day_mode_group, population_category, home_density, ident_men, "
        "pond_jour, total_time_min, total_energy_kh_kj, total_energy_cp_kj, "
        "trips_per_day FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()


def _group_stats(
    days: dict, group_column: str, *, n_reps: int, seed: int
) -> list[daily_energy.GroupStats]:
    return daily_energy.bootstrap_group_stats(
        days[group_column], days["ident_men"], days["pond_jour"],
        days["total_time_min"], days["total_energy_kh_kj"],
        days["total_energy_cp_kj"], n_reps=n_reps, seed=seed,
    )


def _build_base(
    con: duckdb.DuckDBPyConnection, config: EnergyConfig
) -> None:
    emp2019.build_trip_legs(con, config)
    daily_energy.create_day_summary(con)
    daily_energy.create_non_travelers(con)


def _run_variant(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    out_dir: Path,
    *,
    where_sql_days: str,
    suffix: str,
    n_reps: int,
    seed: int,
) -> dict:
    """Compute every statistic and figure for one loop-trip variant
    (section 9.9, step 11 round 5): ``where_sql_days`` filters
    ``day_summary``'s candidate trip legs (``"TRUE"`` for every trip,
    ``"NOT is_loop_trip"`` to exclude leisure loops -- point 1's "with
    and without loop trips"), ``suffix`` names this variant's figures
    (``"_all"``/``"_noloops"``, point 6: "every figure twice")."""
    _build_base(con, config)
    daily_energy.create_day_summary(con, where_sql=where_sql_days)
    days = _day_rows(con)

    mode_stats = _group_stats(days, "day_mode_group", n_reps=n_reps, seed=seed)
    population_stats = _group_stats(
        days, "population_category", n_reps=n_reps, seed=seed
    )
    density_stats = _group_stats(days, "home_density", n_reps=n_reps, seed=seed)

    mean_kh, var_kh = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_kh_kj"]
    )
    mean_cp, var_cp = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_cp_kj"]
    )
    gamma_kh = daily_energy.gamma_moments_fit(mean_kh, var_kh)
    gamma_cp = daily_energy.gamma_moments_fit(mean_cp, var_cp)

    by_group = {s.group: s for s in mode_stats}
    kh_means = [
        by_group[g].mean_energy_kh_kj for g in daily_energy.DAY_MODE_GROUPS
        if g in by_group
    ]
    cp_means = [
        by_group[g].mean_energy_cp_kj for g in daily_energy.DAY_MODE_GROUPS
        if g in by_group
    ]
    ratio_kh = max(kh_means) / min(kh_means) if kh_means else float("nan")
    ratio_cp = max(cp_means) / min(cp_means) if cp_means else float("nan")

    v0_overall = daily_energy.calibrate_v0_kmh(con, where_sql=where_sql_days)[0]
    v0_by_age_band = daily_energy.calibrate_v0_kmh(
        con, by_age_band=True, where_sql=where_sql_days
    )
    p0_overall = daily_energy.calibrate_p0(con, config, where_sql=where_sql_days)[0]
    p0_by_age_band = daily_energy.calibrate_p0(
        con, config, by_age_band=True, where_sql=where_sql_days
    )

    trips_mean, trips_ci = daily_energy.bootstrap_mean_ci(
        days["ident_men"], days["pond_jour"], days["trips_per_day"].astype(float),
        n_reps=n_reps, seed=seed,
    )
    trips_by_population = _trips_per_day_by_group(
        days, "population_category", n_reps=n_reps, seed=seed
    )
    trips_by_density = _trips_per_day_by_group(
        days, "home_density", n_reps=n_reps, seed=seed
    )

    # Car passengers: household vs carpool, and the walking trips of
    # passenger days (section 9.9, "Outputs of the re-estimation").
    passenger_trip_stats = {}
    for group in ("car_passenger_household", "car_passenger_carpool"):
        passenger_trip_stats[group] = _weighted_query(
            con,
            "SELECT pond_jour AS weight, energy_kh_kj AS energy_kh, "
            "energy_cp_kj AS energy_cp, duration_min AS time_min FROM trip_legs "
            f"WHERE mode_group = '{group}' AND ({where_sql_days})",
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
        FROM trip_legs WHERE ({where_sql_days})
    """).fetchone()
    walk_trips_by_day_group = dict(con.sql(f"""
        SELECT d.day_mode_group,
            sum(CASE WHEN t.mode_group = 'walk' THEN 1 ELSE 0 END) * 1.0
                / count(DISTINCT d.ident_ind)
        FROM day_summary d
        JOIN trip_legs t ON t.ident_ind = d.ident_ind
        WHERE d.day_mode_group IN
            ('car_driver', 'car_passenger_household', 'car_passenger_carpool')
            AND ({where_sql_days})
        GROUP BY d.day_mode_group
    """).fetchall())

    # F8 robustness (section 9.9): re-run the pipeline under each variant,
    # scoped to this same loop-trip filter throughout.
    robustness_rows, robustness_ci = _run_robustness(
        con, config, n_reps=n_reps, seed=seed, base_where_sql=where_sql_days,
    )
    # Restore this variant's own base for the figures below.
    daily_energy.create_day_summary(con, where_sql=where_sql_days)

    f4_paths, f4_panels = _figure_f4_mean_by_mode(
        con, out_dir, n_reps=n_reps, seed=seed, suffix=suffix,
    )
    figures = [
        _figure_f1_trips_per_day(
            days, trips_mean, trips_by_population, trips_by_density, out_dir,
            suffix=suffix,
        ),
        *_figure_f3_energy_density(con, out_dir, suffix=suffix),
        *f4_paths,
        _figure_f5_heatmaps(con, out_dir, suffix=suffix),
        _figure_f6_v0_p0(
            v0_by_age_band, p0_by_age_band, config, out_dir, suffix=suffix,
        ),
        _figure_f7_passengers(
            passenger_trip_stats, walk_trips_by_day_group, out_dir, suffix=suffix,
        ),
        _figure_f8_robustness(robustness_ci, out_dir, suffix=suffix),
    ]

    return {
        "n_days": len(days["day_mode_group"]),
        "mode_stats": mode_stats,
        "population_stats": population_stats,
        "density_stats": density_stats,
        "mean_kh": mean_kh,
        "mean_cp": mean_cp,
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
        "figures": figures,
    }


def run(
    out_dir: Path,
    zip_path: Path = emp2019.DEFAULT_ZIP_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    n_reps: int = 200,
    seed: int = 0,
) -> dict:
    """Run the full re-estimation; return every computed statistic and
    figure path, used by ``write_markdown`` and the test suite.

    Every statistic and figure is computed twice (section 9.9, step 11
    round 5, point 6): ``"_all"`` (every trip) and ``"_noloops"``
    (leisure-loop trips -- EMP purpose 7.7, "se promener sans
    destination precise" -- excluded). The ``"_all"`` variant is this
    function's primary, top-level result (unchanged keys, for
    ``write_markdown`` and backward compatibility); ``"_noloops"``
    contributes its own figures and the point-1 group-table comparison.
    """
    config = load_energy_config(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path)
    emp2019.register_views(con, csv_paths)

    results_all = _run_variant(
        con, config, out_dir, where_sql_days="TRUE", suffix="_all",
        n_reps=n_reps, seed=seed,
    )
    results_noloops = _run_variant(
        con, config, out_dir, where_sql_days="NOT is_loop_trip", suffix="_noloops",
        n_reps=n_reps, seed=seed,
    )

    # Restore the unfiltered base for the diagnostics below (not part of
    # the all-vs-noloops figure duplication).
    _build_base(con, config)

    # Point 1: leisure-loop trip shares (of trips, and of day energy, by
    # main-mode group); grouped by the trip's own day's ``day_mode_group``
    # (walking_only/cycle/.../multimodal/other), matching every other
    # group table in this report, not the trip's own naive ``mode_group``
    # (e.g. 'walk', which is a different label set and can't be joined
    # against the energy-share query below).
    loop_trip_shares = con.sql("""
        SELECT d.day_mode_group,
            sum(t.pond_jour * t.is_loop_trip::int) / sum(t.pond_jour) AS trip_share,
            count(*) FILTER (WHERE t.is_loop_trip) AS n_loop, count(*) AS n_total
        FROM trip_legs t JOIN day_summary d ON d.ident_ind = t.ident_ind
        WHERE d.total_energy_kh_kj IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    loop_energy_shares = con.sql("""
        WITH loop_leg_energy AS (
            SELECT ident_ind,
                sum(energy_kh_kj) FILTER (WHERE is_loop_trip) AS loop_kh,
                sum(energy_cp_kj) FILTER (WHERE is_loop_trip) AS loop_cp
            FROM trip_legs GROUP BY 1
        )
        SELECT d.day_mode_group,
            sum(d.pond_jour * coalesce(l.loop_kh, 0))
                / sum(d.pond_jour * d.total_energy_kh_kj) AS loop_energy_share_kh,
            sum(d.pond_jour * coalesce(l.loop_cp, 0))
                / sum(d.pond_jour * d.total_energy_cp_kj) AS loop_energy_share_cp
        FROM day_summary d LEFT JOIN loop_leg_energy l ON l.ident_ind = d.ident_ind
        WHERE d.total_energy_kh_kj IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """).fetchall()

    # Point 2: data-quality correction counts (upper-bound speed flags,
    # corrected by mode's median speed, not dropped).
    quality_counts = con.sql("""
        SELECT mode_group,
            count(*) FILTER (WHERE speed_flagged_upper) AS n_corrected,
            count(*) AS n_total
        FROM trip_legs GROUP BY 1 ORDER BY 1
    """).fetchall()

    # Point 3: post-fix cycle-day decomposition.
    cycle_decomposition = _compute_cycle_decomposition(con, config)

    # Cycle group, weekdays only (kept from round 4's point 3).
    daily_energy.create_day_summary(con, where_sql="typejour = 1")
    days_weekday = _day_rows(con)
    cycle_weekday_stats = next(
        (
            s for s in _group_stats(
                days_weekday, "day_mode_group", n_reps=n_reps, seed=seed
            )
            if s.group == "cycle"
        ),
        None,
    )
    daily_energy.create_day_summary(con)  # restore the unfiltered base

    # Children as car drivers (round 4's point 4): the raw mtp code
    # behind every day_mode_group='car_driver' day of a children_6_17
    # respondent.
    children_car_driver_mtp = con.sql("""
        SELECT d.mtp, count(*), min(t.age), max(t.age)
        FROM trip_legs t
        JOIN k_deploc d ON d.IDENT_IND = t.ident_ind AND d.num_dep = t.num_dep
        WHERE t.mode_group = 'car_driver' AND t.population_category = 'children_6_17'
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    children_car_driver_n = con.sql("""
        SELECT count(*) FROM day_summary
        WHERE day_mode_group = 'car_driver' AND population_category = 'children_6_17'
    """).fetchone()[0]

    non_travelers = con.sql(
        "SELECT pond_ind, mimmosem FROM non_travelers"
    ).fetchnumpy()
    travelers_pond_ind = con.sql(
        "SELECT pond_ind FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()["pond_ind"]
    non_traveler_weight = non_travelers["pond_ind"].sum()
    non_traveler_share = non_traveler_weight / (
        non_traveler_weight + travelers_pond_ind.sum()
    )
    non_traveler_mimmosem_match = float(np.mean(non_travelers["mimmosem"] == 1))
    traveler_day_type_share = dict(con.sql("""
        SELECT any_value(t.typejour), sum(d.pond_jour)
        FROM day_summary d JOIN trip_legs t ON t.ident_ind = d.ident_ind
        GROUP BY d.ident_ind
    """).fetchall())

    results = dict(results_all)
    results.update({
        "config": config,
        "mode_stats_noloops": results_noloops["mode_stats"],
        "loop_trip_shares": loop_trip_shares,
        "loop_energy_shares": loop_energy_shares,
        "quality_counts": quality_counts,
        "cycle_decomposition": cycle_decomposition,
        "cycle_weekday_stats": cycle_weekday_stats,
        "children_car_driver_mtp": children_car_driver_mtp,
        "children_car_driver_n": children_car_driver_n,
        "non_traveler_n": len(non_travelers["pond_ind"]),
        "non_traveler_share": non_traveler_share,
        "non_traveler_mimmosem_match": non_traveler_mimmosem_match,
        "traveler_day_type_share": traveler_day_type_share,
        "figures": results_all["figures"] + results_noloops["figures"],
    })
    return results


def _run_robustness(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    *,
    n_reps: int,
    seed: int,
    base_where_sql: str = "TRUE",
) -> tuple[list[daily_energy.RobustnessRow], dict[str, list[daily_energy.GroupStats]]]:
    """F8: re-run the pipeline under each robustness variant (section 9.9).

    ``base_where_sql`` is ANDed into every variant's own ``day_summary``
    filter (e.g. excluding leisure-loop trips for the whole sweep).
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
                        name, rows_data["day_mode_group"], rows_data["pond_jour"],
                        rows_data["total_time_min"], rows_data["total_energy_kh_kj"],
                        rows_data["total_energy_cp_kj"],
                        scope=scope, groups_of_interest=groups_of_interest,
                        statistic=statistic,
                    )
                )
        if want_ci:
            ci_stats[name] = daily_energy.bootstrap_group_stats(
                rows_data["day_mode_group"], rows_data["ident_men"],
                rows_data["pond_jour"], rows_data["total_time_min"],
                rows_data["total_energy_kh_kj"], rows_data["total_energy_cp_kj"],
                n_reps=n_reps, seed=seed,
            )

    def _summary(extra_where: str = "TRUE") -> None:
        daily_energy.create_day_summary(
            con, where_sql=f"({base_where_sql}) AND ({extra_where})"
        )

    # Terminal-leg scale sweep (also provides the base case).
    emp2019.build_trip_legs(con, config, terminal_scale=0.5)
    _summary()
    _row("terminal legs x0.5", want_ci=True)

    emp2019.build_trip_legs(con, config, terminal_scale=1.0)
    _summary()
    _row("terminal legs x1 (base case)", want_ci=True)

    # Weekdays-only and local-trips-only reuse the base (x1.0) trip legs,
    # only `day_summary`'s own filter changes.
    _summary("typejour = 1")
    _row("weekdays only", want_ci=False)
    _summary("mobloc = 1")
    _row("local trips only (MOBLOC=1)", want_ci=False)
    _summary()  # restore the (base_where_sql-filtered) unfiltered base

    emp2019.build_trip_legs(con, config, terminal_scale=1.5)
    _summary()
    _row("terminal legs x1.5", want_ci=True)

    emp2019.build_trip_legs(con, config, bike_p0_override_w=P0_REFERENCE_W)
    _summary()
    _row(f"P0 = {P0_REFERENCE_W:g} W (section 9.7 reference)", want_ci=False)

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
            days["ident_men"][mask], days["pond_jour"][mask],
            days["trips_per_day"][mask].astype(float), n_reps=n_reps, seed=seed,
        )
        results.append((str(group), n, mean, ci))
    return results


def _figure_f1_trips_per_day(
    days: dict,
    trips_mean: float,
    trips_by_population: list[tuple[str, int, float, tuple[float, float]]],
    trips_by_density: list[tuple[str, int, float, tuple[float, float]]],
    out_dir: Path,
    *,
    suffix: str = "",
) -> Path:
    fig, (ax_hist, ax_pop, ax_density) = plt.subplots(1, 3, figsize=(17, 5))

    max_trips = int(days["trips_per_day"].max())
    bins = np.arange(0.5, max_trips + 1.5, 1)
    counts, _ = np.histogram(
        days["trips_per_day"], bins=bins, weights=days["pond_jour"]
    )
    pct = counts / days["pond_jour"].sum() * 100.0
    ax_hist.bar(bins[:-1] + 0.5, pct, width=0.9, color="tab:blue")
    ax_hist.axvline(trips_mean, color="black", linestyle="--")
    ax_hist.text(
        trips_mean, ax_hist.get_ylim()[1] * 0.95, f"mean={trips_mean:.2f}",
        ha="left", va="top",
    )
    ax_hist.set_xlabel("Trips per person and day (integer-centred bins)")
    ax_hist.set_ylabel("% of person-days")
    ax_hist.set_title("(A) Distribution")

    for ax, rows, title in (
        (ax_pop, trips_by_population, "(B) By population category"),
        (ax_density, trips_by_density, "(C) By density class"),
    ):
        labels = [row[0] for row in rows]
        means = [row[2] for row in rows]
        lower = [row[2] - row[3][0] for row in rows]
        upper = [row[3][1] - row[2] for row in rows]
        x = np.arange(len(labels))
        ax.bar(x, means, yerr=[lower, upper], capsize=3, color="tab:orange")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel("Mean trips per day")
        ax.set_title(title)

    fig.suptitle("F1. Trips per person and day (section 9.9, point 2)")
    fig.tight_layout()
    path = out_dir / f"f01_trips_per_day{suffix}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f3_energy_density(
    con: duckdb.DuckDBPyConnection, out_dir: Path, *, suffix: str = ""
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
        ("cp", "Compendium", ""), ("kh", "KH", "_appendix_kh"),
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
            g for g in day_groups
            if (rows["day_mode_group"] == g).sum() >= MIN_CELL_N
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
                grid_kj, cumulative, cumulative + scaled, label=group, alpha=0.85,
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
        path = out_dir / f"f03a_energy_density_overall{suffix}{rate_suffix}.png"
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
                daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--",
                linewidth=0.8,
            )
            ax.set_title(category, fontsize=9)
        for ax in axes.flat[len(categories):]:
            ax.axis("off")
        axes.flat[0].legend(fontsize=6, loc="upper right")
        fig.suptitle(
            f"F3. Daily travel energy density by population category "
            f"({rate_label}, normalised, section 9.9)"
        )
        fig.tight_layout()
        path = out_dir / f"f03b_energy_density_by_category{suffix}{rate_suffix}.png"
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
        rows["day_mode_group"], rows["ident_men"], rows["pond_jour"],
        rows["total_time_min"], rows["total_energy_kh_kj"],
        rows["total_energy_cp_kj"], n_reps=n_reps, seed=seed,
    )
    return {s.group: s for s in stats}


def _figure_f4_mean_by_mode(
    con: duckdb.DuckDBPyConnection, out_dir: Path, *, n_reps: int, seed: int,
    suffix: str = "",
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
    panels = [
        ("overall", _bootstrap_stats_where(con, "TRUE", n_reps=n_reps, seed=seed))
    ]
    panels += [
        (
            category,
            _bootstrap_stats_where(
                con, f"population_category = '{category}'", n_reps=n_reps, seed=seed
            ),
        )
        for category in categories
    ]

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
                x + offset, means, width, yerr=[lowers, uppers], label=rate_key,
                capsize=2,
            )
            ax.scatter(
                x + offset, medians, marker="D", color="black", s=14, zorder=3,
                label=f"{rate_key} median" if ax is axes.flat[0] else None,
            )
        for i, group in enumerate(present):
            ax.text(
                i, 0, f"n={stats[group].n}", ha="center", va="bottom", fontsize=6,
                rotation=90,
            )
        ax.axhline(
            daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--", linewidth=0.8
        )
        ax.set_xticks(x)
        ax.set_xticklabels(present, rotation=45, ha="right", fontsize=7)
        ax.set_title(label, fontsize=9)
        ax.legend(fontsize=6)
    for ax in axes.flat[len(panels):]:
        ax.axis("off")
    fig.suptitle(
        "F4a. Mean daily energy by main-mode group, 95% CI, n, median marker "
        "(section 9.9)"
    )
    fig.tight_layout()
    path_energy = out_dir / f"f04a_mean_energy_by_mode{suffix}.png"
    fig.savefig(path_energy, dpi=110)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(19, 11))
    for ax, (label, stats) in zip(axes.flat, panels, strict=False):
        present = [g for g in groups if g in stats]
        x = np.arange(len(present))
        means = [
            stats[group].mean_time_min if stats[group].n >= MIN_CELL_N else np.nan
            for group in present
        ]
        ax.bar(x, means, color="tab:gray")
        for i, group in enumerate(present):
            ax.text(
                i, 0, f"n={stats[group].n}", ha="center", va="bottom", fontsize=6,
                rotation=90,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(present, rotation=45, ha="right", fontsize=7)
        ax.set_title(label, fontsize=9)
    for ax in axes.flat[len(panels):]:
        ax.axis("off")
    fig.suptitle("F4b. Mean daily travel time by main-mode group, n (section 9.9)")
    fig.tight_layout()
    path_time = out_dir / f"f04b_mean_time_by_mode{suffix}.png"
    fig.savefig(path_time, dpi=110)
    plt.close(fig)
    return [path_energy, path_time], panels


def _figure_f5_heatmaps(
    con: duckdb.DuckDBPyConnection, out_dir: Path, *, suffix: str = ""
) -> Path:
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
                        j, i, f"{matrix[i, j]:.0f}\n(n={n_matrix[i, j]})",
                        ha="center", va="center", fontsize=6, color="white",
                    )
        ax.set_title(title, fontsize=10)
        fig.colorbar(image, ax=ax, label="Mean daily energy, kJ (Compendium)")
    fig.suptitle(
        "F5. Mean daily energy by main-mode group (n < 50 cells blank, section 9.9)"
    )
    fig.tight_layout()
    path = out_dir / f"f05_heatmaps{suffix}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f6_v0_p0(
    v0_by_age_band: list[daily_energy.SpeedCalibration],
    p0_by_age_band: list[daily_energy.P0Calibration],
    config: EnergyConfig,
    out_dir: Path,
    *,
    suffix: str = "",
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
    path = out_dir / f"f06_v0_p0{suffix}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f7_passengers(
    passenger_trip_stats: dict[str, tuple[int, float, float, float]],
    walk_trips_by_day_group: dict[str, float],
    out_dir: Path,
    *,
    suffix: str = "",
) -> Path:
    groups = ["car_passenger_household", "car_passenger_carpool"]
    fig, (ax_energy, ax_walk) = plt.subplots(1, 2, figsize=(11, 5))
    x = np.arange(len(groups))
    width = 0.35
    ax_energy.bar(
        x - width / 2, [passenger_trip_stats[g][2] for g in groups], width, label="kh",
    )
    ax_energy.bar(
        x + width / 2, [passenger_trip_stats[g][3] for g in groups], width,
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
    path = out_dir / f"f07_passengers{suffix}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_f8_robustness(
    robustness_ci: dict[str, list[daily_energy.GroupStats]], out_dir: Path,
    *, suffix: str = "",
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
            if g in by_group else 0.0
            for g in groups
        ]
        uppers = [
            by_group[g].mean_energy_cp_ci[1] - by_group[g].mean_energy_cp_kj
            if g in by_group else 0.0
            for g in groups
        ]
        ax_energy.bar(
            x + offset, means, width, yerr=[lowers, uppers], label=variant, capsize=2,
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
    path = out_dir / f"f08_robustness{suffix}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


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


def write_markdown(md_path: Path, out_dir: Path, results: dict) -> None:
    """Write the section 9.9 re-estimation report (steps 1-3, 5, F8)."""
    config = results["config"]
    carpool = config.car.carpool_passenger
    walk_trips = results["walk_trips_by_day_group"]
    walk_driver = walk_trips.get("car_driver", float("nan"))
    walk_household = walk_trips.get("car_passenger_household", float("nan"))
    walk_carpool = walk_trips.get("car_passenger_carpool", float("nan"))
    lines = [
        "# Step 11 (`mobgrid/budget`): EMP 2019 re-estimation (section 9.9)",
        "",
        "Generated by `python -m mobgrid.budget.emp`. Rebuilds section 9.9's "
        "re-estimation steps 1-3 and 5 on the EMP 2019 public tables, plus the "
        "F8 robustness check; terminal legs reuse sections 9.4-9.7's formulas "
        "and `config/energy.yaml`'s already-calibrated car/stairs/waiting/"
        "PT-ride defaults, plus provisional PT headway/station-height/"
        "access-walk defaults (TODO(confirm), `config.pt_ride`). EMC² (step "
        "4) and Ē_c (step 6) are out of scope.",
        "",
        "**Variables used** (K_DEPLOC unless noted): mode `mtp`; duration "
        "`DUREE`; distance `MDISTTOT_fin`; purpose `MMOTIFDES`/`MOTPREC` "
        "(read, not used by this step's formulas); companions "
        "`MACCOMPM`/`MACCOMPHM` (household vs carpool passenger split); day "
        "`TYPEJOUR`, `mobloc` (F8's local-trips variant); weights "
        "`POND_JOUR` (day) and `pond_indC` (K_INDIVIDU, individual); age "
        "band `AGE6` (TCM_IND_KISH); population category (section 6.1) from "
        "`SITUA` (TCM_IND_KISH) combined with `AGE` for the 6-17 children "
        "group; density of residence `DENSITECOM_ORI` of the home-departure "
        "trip (`MORIDOM`); non-traveller cross-check `MIMMOSEM` (K_INDIVIDU).",
        "",
        f"**Sample:** {results['n_days']:,} respondent-days with at least "
        "one classified trip "
        f"({results['non_traveler_n']} of "
        f"{results['n_days'] + results['non_traveler_n']} "
        f"respondents report no trip that day, {results['non_traveler_share']:.1%} "
        "by individual weight, reported apart per point 2).",
        "",
        "## Main-mode-of-the-day groups (point 3)",
        "",
        "walking only, bike, car driver, car passenger with a household "
        "driver, car passenger with a non-household driver (carpool), "
        "urban PT, train short (< 80 km), train long (>= 80 km), "
        "multimodal (two or more distinct non-walk modes in the day; "
        "driving and riding as a passenger count as two), other. "
        f"**'other' contains:** {emp2019.OTHER_MODE_DESCRIPTION}.",
        "",
        f"**Children as car drivers** ({results['children_car_driver_n']} "
        "children_6_17 car_driver days): the raw `mtp` code is "
        + ", ".join(
            f"{code:g} (n={n}, ages {age_min}-{age_max})"
            for code, n, age_min, age_max in results["children_car_driver_mtp"]
        )
        + ". Both codes are `mtp` category 3 \"Automobile\" (3.1 "
        "\"Conducteur\", 3.3 \"Tantot conducteur tantot passager\"), not a "
        "two-wheeler code (2.x): no two-wheeler reclassification applies. "
        "`mtp` 3.1 includes \"voiturette\" (a license-free microcar, legal "
        "from age 14 in France), plausible for the 14-17 share, but not "
        "for the many 6-13 year olds here; most likely EMP's own "
        "household/accompanying-trip coding records the car's use rather "
        "than confirming the child personally drove.",
        "",
        "## Density classes",
        "",
        "INSEE's own 4-level grid names and order: dense (1, densely "
        "populated communes), intermediate (2), sparse (3, peu denses), "
        "very_sparse (4, tres peu denses); `emp2019._DENSITY_LABEL_BY_CODE` "
        "maps `DENSITECOM_ORI`/`_DES` directly, and "
        "`emp2019._DENSITY_KEY_TRANSLATION` re-keys `config.car`/"
        "`config.pt_ride`'s existing density defaults (chosen for step 7 "
        "as `dense`/`urban`/`suburban`/`rural`) to these same INSEE names "
        "and order, checked against `data/raw/emp2019/emp2019-categories.pdf`'s "
        "\"Degre de densite\" table.",
        "",
        "## Mean daily energy and time by main-mode group (point 3)",
        "",
        *_format_group_table(results["mode_stats"]),
        "",
        "## Leisure loops (point 1): trips without a destination",
        "",
        "Identified by EMP's own purpose code `MMOTIFDES` = 7.7 (\"se "
        "promener sans destination precise\", stroll/ride/drive without a "
        "specific destination; code 7.8, \"go to a place for walking\", has "
        "a destination and does not count). EMP's public release has no "
        "commune-level origin field (destination only, disclosure "
        "control), so an exact origin=destination geometry check is not "
        "available; this purpose code is EMP's own operationalisation of "
        "the same concept.",
        "",
        "| Group | loop trip share | n loop / n total | loop share of day "
        "energy (kh) | loop share of day energy (cp) |",
        "|---|---|---|---|---|",
    ]
    loop_energy_by_group = {
        row[0]: (row[1], row[2]) for row in results["loop_energy_shares"]
    }
    for mode, trip_share, n_loop, n_total in results["loop_trip_shares"]:
        energy_kh, energy_cp = loop_energy_by_group.get(mode, (float("nan"),) * 2)
        lines.append(
            f"| {mode} | {trip_share:.1%} | {n_loop:,} / {n_total:,} | "
            f"{energy_kh:.1%} | {energy_cp:.1%} |"
        )
    lines += [
        "",
        "### Main-mode group table, loop trips excluded",
        "",
        *_format_group_table(results["mode_stats_noloops"]),
        "",
        "## Data-quality correction: implausible door-to-door speeds",
        "",
        "Trips are corrected, not dropped (section 9.9, step 11 round 5): "
        "flagged above an upper speed bound only -- walk > "
        f"{emp2019.WALK_SPEED_UPPER_KMH:g} km/h, bike > "
        f"{emp2019.CYCLE_SPEED_UPPER_KMH:g} km/h, car (driver or passenger) > "
        f"{emp2019.CAR_SPEED_UPPER_KMH:g} km/h -- their declared distance is "
        "replaced by declared duration x the mode's own median speed "
        "(from its not-flagged trips). Cycling energy is time-based "
        "(round 4), so only walk's and car's corrected distances feed the "
        "energy formulas; bike is flagged (reported) but not corrected.",
        "",
        *[f"- {mode}: {corrected:,} of {total:,} trips corrected"
          for mode, corrected, total in results["quality_counts"]],
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
        "## F8 robustness (max/min ratio and CV of the group means, "
        "walk/bike/driver/both passenger groups/urban PT/train short)",
        "",
        *_format_robustness_table(results["robustness_rows"]),
        "",
        "## Constancy test (point 3, 5)",
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
        "- **P0 estimator:** get/park bike (2 min total) and the expected "
        "stop delays (section 9.7, Webster 1958) are subtracted from the "
        "declared duration at the naive speed before computing the ride "
        "speed; P0 is `bike.required_power_w` at the single ratio-estimated "
        "implied flat speed (not an average of per-trip, nonlinear P0 "
        "values). EMP 2019's own mode codes do not separate e-bikes from "
        "bicycles (`mtp` 2.1 includes \"assistance electrique\"), so they "
        "cannot be excluded or reported apart.",
        f"- Overall P0: {results['p0_overall'].p0_w:.1f} W at an implied flat "
        f"speed of {results['p0_overall'].implied_flat_speed_kmh:.2f} km/h, n="
        f"{results['p0_overall'].n} (section 9.7's reference: "
        f"{P0_REFERENCE_W:g} W at 16 km/h).",
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
            if p0_stat else "0 | - | -"
        )
        lines.append(
            f"| {v0_stat.group} | {v0_stat.n} | {v0_stat.speed_kmh:.2f} | {p0_text} |"
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
        "## Non-traveller immobility (point 2)",
        "",
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
            for day_type, share in sorted(results["traveler_day_type_share"].items())
        )
        + f" (weekday-dominated: {results['non_traveler_share']:.1%} overall "
        "immobility is a weekday-weighted figure, not comparable to "
        "all-week averages that include weekends, when immobility is "
        "known to be much higher).",
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
        "- The day's home density is the origin density of its "
        "home-departure trip (`MORIDOM=1`), or the first trip by number "
        "if no such trip is recorded that day.",
        "- Bike get/park and stop-delay adjustment: unreliable (would "
        "consume over half, or all but under a minute, of a very short "
        "trip's declared duration) for a small share of cycling trips; "
        "these fall back to the naive whole-duration speed for both "
        "energy and the P0 estimator's ride-time denominator.",
        "- F3/F4/F5 use the full set of day-mode groups (including "
        "multimodal and other); F8's robustness check is restricted to "
        "the six groups the task names (walk, bike, driver, both "
        "passenger groups, urban PT, train short).",
        "- F8's figure shows bootstrap CIs for the base case and the "
        "terminal-legs x0.5/x1.5 extremes only (not every table variant), "
        "per the task's \"figure ... for the base case and the extremes\".",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-estimate section 9.9's daily energy budget on EMP 2019."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--data-zip", type=Path, default=emp2019.DEFAULT_ZIP_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    results = run(
        args.out, args.data_zip, args.config, n_reps=args.bootstrap_reps, seed=args.seed
    )
    md_path = args.out.with_suffix(".md")
    write_markdown(md_path, args.out, results)
    print(f"Wrote {len(results['figures'])} figures to {args.out} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
