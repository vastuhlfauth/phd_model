"""Section 9.9 re-estimation on EMP 2019: CLI, figures and report (step 11).

``python -m mobgrid.budget.emp --out docs/data/step11_budget`` extracts
the public EMP 2019 tables (K_DEPLOC, TCM_IND_KISH, K_INDIVIDU, Q_MENAGE;
no `TCM_IND` columns are needed by this step's formulas), rebuilds every
respondent's surveyed day as legs (``emp2019``), aggregates it to a daily
travel time/energy budget and runs the hypothesis test of steps 1-3 and 5
(``daily_energy``). Section 9.9's EMC² cross-check (step 4) and the
definition of Ē_c for 1 km cells (step 6) are out of scope.

The command writes seven PNG figures to ``--out`` and a Markdown report
to ``<out>.md`` alongside it, mirroring ``mobgrid.energy.checks``.
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
from mobgrid.energy.rates import EnergyConfig, load_energy_config

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"
DEFAULT_OUT_DIR = ROOT / "docs" / "data" / "step11_budget"

#: Day-level groups directly comparable with Koelbl & Helbing's (2003) six
#: reference modes (section 9.9 point 3); 'multimodal' and 'other' are
#: kept apart in the figures and tables, as the spec requires.
KH_COMPARABLE_GROUPS = (
    "walking_only", "cycle", "car_driver", "car_passenger", "urban_pt", "train",
)


def _weighted_query(
    con: duckdb.DuckDBPyConnection, sql: str
) -> tuple[int, float, float, float]:
    """(n, weighted_n, weighted_mean_kh, weighted_mean_cp) of a query
    selecting (weight, energy_kh, energy_cp, time_min) rows, used for the
    one-off passenger/walk cross-tabulations outside the main groupings."""
    rows = con.sql(sql).fetchnumpy()
    if len(rows["weight"]) == 0:
        return 0, 0.0, float("nan"), float("nan")
    mean_kh, _ = daily_energy.weighted_mean_variance(rows["weight"], rows["energy_kh"])
    mean_cp, _ = daily_energy.weighted_mean_variance(rows["weight"], rows["energy_cp"])
    return len(rows["weight"]), float(rows["weight"].sum()), mean_kh, mean_cp


def run(
    out_dir: Path,
    zip_path: Path = emp2019.DEFAULT_ZIP_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    n_reps: int = 200,
    seed: int = 0,
) -> dict:
    """Run the full re-estimation; return every computed statistic and
    figure path, used by ``write_markdown`` and the test suite."""
    config = load_energy_config(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path)
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)
    daily_energy.create_day_summary(con)
    daily_energy.create_non_travelers(con)

    days = con.sql(
        "SELECT day_mode_group, age_activity_group, home_density, ident_men, "
        "pond_jour, total_time_min, total_energy_kh_kj, total_energy_cp_kj, "
        "trips_per_day FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()

    def _stats(group_column: str) -> list[daily_energy.GroupStats]:
        return daily_energy.bootstrap_group_stats(
            days[group_column], days["ident_men"], days["pond_jour"],
            days["total_time_min"], days["total_energy_kh_kj"],
            days["total_energy_cp_kj"], n_reps=n_reps, seed=seed,
        )

    mode_stats = _stats("day_mode_group")
    age_activity_stats = _stats("age_activity_group")
    density_stats = _stats("home_density")

    mean_kh, var_kh = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_kh_kj"]
    )
    mean_cp, var_cp = daily_energy.weighted_mean_variance(
        days["pond_jour"], days["total_energy_cp_kj"]
    )
    gamma_kh = daily_energy.gamma_moments_fit(mean_kh, var_kh)
    gamma_cp = daily_energy.gamma_moments_fit(mean_cp, var_cp)

    kh_comparable = {
        s.group: s for s in mode_stats if s.group in KH_COMPARABLE_GROUPS
    }
    kh_means = [s.mean_energy_kh_kj for s in kh_comparable.values()]
    cp_means = [s.mean_energy_cp_kj for s in kh_comparable.values()]
    ratio_kh = max(kh_means) / min(kh_means) if kh_means else float("nan")
    ratio_cp = max(cp_means) / min(cp_means) if cp_means else float("nan")

    v0_by_age_band = daily_energy.calibrate_by_age_band(
        con, "walk", "implied_speed_kmh"
    )
    p0_by_age_band = daily_energy.calibrate_by_age_band(
        con, "cycle", "p0_calibrated_w"
    )
    v0_overall = con.sql(
        "SELECT avg(implied_speed_kmh) FROM trip_legs WHERE mode_group='walk' "
        "AND implied_speed_kmh IS NOT NULL"
    ).fetchone()[0]
    p0_overall = con.sql(
        "SELECT avg(p0_calibrated_w) FROM trip_legs WHERE mode_group='cycle' "
        "AND p0_calibrated_w IS NOT NULL"
    ).fetchone()[0]

    # Car passengers: household vs carpool (trip level), and the walking
    # trips of passenger days (section 9.9, "Outputs of the re-estimation").
    passenger_trip_stats = {}
    for group in ("car_passenger_household", "car_passenger_carpool"):
        n, wn, mkh, mcp = _weighted_query(
            con,
            "SELECT pond_jour AS weight, energy_kh_kj AS energy_kh, "
            "energy_cp_kj AS energy_cp, duration_min AS time_min FROM trip_legs "
            f"WHERE mode_group = '{group}'",
        )
        passenger_trip_stats[group] = (n, wn, mkh, mcp)
    passenger_walk_stats = _weighted_query(
        con,
        "SELECT t.pond_jour AS weight, t.energy_kh_kj AS energy_kh, "
        "t.energy_cp_kj AS energy_cp, t.duration_min AS time_min "
        "FROM trip_legs t JOIN day_summary d USING (ident_ind) "
        "WHERE t.mode_group = 'walk' AND d.day_mode_group = 'car_passenger'",
    )
    passenger_walk_n, passenger_walk_wn, passenger_walk_kh, passenger_walk_cp = (
        passenger_walk_stats
    )

    non_travelers = con.sql("SELECT pond_ind FROM non_travelers").fetchnumpy()
    # The weight compared here is the per-respondent individual weight
    # (`pond_indC`), available for both travellers and non-travellers,
    # not `POND_JOUR` (day weight, travellers only).
    travelers_pond_ind = con.sql(
        "SELECT pond_ind FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()["pond_ind"]
    non_traveler_weight = non_travelers["pond_ind"].sum()
    non_traveler_share = non_traveler_weight / (
        non_traveler_weight + travelers_pond_ind.sum()
    )

    figures = [
        _figure_trips_per_day(days, out_dir),
        _figure_daily_time(days, out_dir),
        _figure_daily_energy_histogram(days, config, out_dir),
        _figure_mean_by_mode(mode_stats, out_dir),
        _figure_mean_by_age_density(age_activity_stats, density_stats, out_dir),
        _figure_v0_p0(v0_by_age_band, p0_by_age_band, config, out_dir),
        _figure_passengers(passenger_trip_stats, out_dir),
    ]

    return {
        "config": config,
        "n_days": len(days["day_mode_group"]),
        "mode_stats": mode_stats,
        "age_activity_stats": age_activity_stats,
        "density_stats": density_stats,
        "mean_kh": mean_kh,
        "mean_cp": mean_cp,
        "gamma_kh": gamma_kh,
        "gamma_cp": gamma_cp,
        "ratio_kh": ratio_kh,
        "ratio_cp": ratio_cp,
        "v0_by_age_band": v0_by_age_band,
        "p0_by_age_band": p0_by_age_band,
        "v0_overall": v0_overall,
        "p0_overall": p0_overall,
        "passenger_trip_stats": passenger_trip_stats,
        "passenger_walk": (
            passenger_walk_n, passenger_walk_wn, passenger_walk_kh, passenger_walk_cp
        ),
        "non_traveler_n": len(non_travelers["pond_ind"]),
        "non_traveler_share": non_traveler_share,
        "trips_per_day_mean": float(
            np.average(days["trips_per_day"], weights=days["pond_jour"])
        ),
        "figures": figures,
    }


def _figure_trips_per_day(days: dict, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    max_trips = int(days["trips_per_day"].max())
    ax.hist(
        days["trips_per_day"], bins=np.arange(0.5, max_trips + 1.5, 1),
        weights=days["pond_jour"], color="tab:blue",
    )
    ax.set_xlabel("Trips per person and day")
    ax.set_ylabel("Weighted persons")
    ax.set_title("F1. Trips per person and day (section 9.9, point 2)")
    fig.tight_layout()
    path = out_dir / "f01_trips_per_day.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_daily_time(days: dict, out_dir: Path) -> Path:
    groups = KH_COMPARABLE_GROUPS + ("multimodal", "other")
    data = [
        days["total_time_min"][days["day_mode_group"] == group]
        for group in groups
        if (days["day_mode_group"] == group).any()
    ]
    labels = [g for g in groups if (days["day_mode_group"] == g).any()]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=labels, showfliers=False)
    ax.set_ylabel("Daily travel time, minutes")
    ax.set_title(
        "F2. Daily travel time by main-mode group (unweighted distributions,\n"
        "section 9.9 point 3)"
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    path = out_dir / "f02_daily_time.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_daily_energy_histogram(
    days: dict, config: EnergyConfig, out_dir: Path
) -> Path:
    groups = KH_COMPARABLE_GROUPS + ("multimodal", "other")
    rate_key = "kh" if config.rate_set == "kh" else "cp"
    energy = days[f"total_energy_{rate_key}_kj"]
    fig, (ax_stack, ax_norm) = plt.subplots(1, 2, figsize=(12, 5))
    bins = np.linspace(0, np.nanpercentile(energy, 99), 40)
    stacked_data = [energy[days["day_mode_group"] == g] for g in groups]
    stacked_weights = [days["pond_jour"][days["day_mode_group"] == g] for g in groups]
    ax_stack.hist(
        stacked_data, bins=bins, weights=stacked_weights, stacked=True, label=groups,
    )
    ax_stack.axvline(daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--")
    ax_stack.set_xlabel(f"Daily travel energy, kJ ({config.rate_set})")
    ax_stack.set_ylabel("Weighted persons")
    ax_stack.set_title("(A) Stacked by main-mode group")
    ax_stack.legend(fontsize=7)

    for group in groups:
        values = energy[days["day_mode_group"] == group]
        if len(values) < 5:
            continue
        weights = days["pond_jour"][days["day_mode_group"] == group]
        ax_norm.hist(
            values, bins=bins, weights=weights, density=True, histtype="step",
            label=group,
        )
    ax_norm.axvline(daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--")
    ax_norm.set_xlabel(f"Daily travel energy, kJ ({config.rate_set})")
    ax_norm.set_ylabel("Density")
    ax_norm.set_title("(B) Normalised, overlaid")
    ax_norm.legend(fontsize=7)

    fig.suptitle(
        "F3. Daily travel energy: the Koelbl & Helbing (2003) constancy "
        "test (section 9.9 point 3, 5)"
    )
    fig.tight_layout()
    path = out_dir / "f03_daily_energy_histogram.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_mean_by_mode(mode_stats: list, out_dir: Path) -> Path:
    groups = KH_COMPARABLE_GROUPS + ("multimodal", "other")
    by_group = {s.group: s for s in mode_stats}
    present = [g for g in groups if g in by_group]
    x = np.arange(len(present))
    width = 0.35
    fig, (ax_e, ax_t) = plt.subplots(1, 2, figsize=(12, 5))
    rate_sets = (("kh", "kh"), ("compendium", "cp"))
    for offset, (rate_set, rate_key) in zip(
        (-width / 2, width / 2), rate_sets, strict=True
    ):
        means = [getattr(by_group[g], f"mean_energy_{rate_key}_kj") for g in present]
        ci = [getattr(by_group[g], f"mean_energy_{rate_key}_ci") for g in present]
        lower = [m - c[0] for m, c in zip(means, ci, strict=True)]
        upper = [c[1] - m for m, c in zip(means, ci, strict=True)]
        ax_e.bar(
            x + offset, means, width, yerr=[lower, upper], label=rate_set, capsize=3
        )
    ax_e.axhline(daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--")
    ax_e.set_xticks(x)
    ax_e.set_xticklabels(present, rotation=30, ha="right")
    ax_e.set_ylabel("Mean daily travel energy, kJ")
    ax_e.set_title("(A) Energy, 95% bootstrap CI")
    ax_e.legend()

    times = [by_group[g].mean_time_min for g in present]
    ax_t.bar(x, times, color="tab:gray")
    ax_t.set_xticks(x)
    ax_t.set_xticklabels(present, rotation=30, ha="right")
    ax_t.set_ylabel("Mean daily travel time, minutes")
    ax_t.set_title("(B) Time")
    fig.suptitle("F4. Mean daily energy and time by main-mode group (section 9.9)")
    fig.tight_layout()
    path = out_dir / "f04_mean_by_mode.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_mean_by_age_density(
    age_stats: list, density_stats: list, out_dir: Path
) -> Path:
    fig, (ax_age, ax_density) = plt.subplots(1, 2, figsize=(12, 5))
    for ax, stats, title in (
        (ax_age, age_stats, "(A) By age-activity group"),
        (ax_density, density_stats, "(B) By home density class"),
    ):
        groups = [s.group for s in stats]
        x = np.arange(len(groups))
        width = 0.35
        ax.bar(x - width / 2, [s.mean_energy_kh_kj for s in stats], width, label="kh")
        ax.bar(
            x + width / 2, [s.mean_energy_cp_kj for s in stats], width,
            label="compendium",
        )
        ax.axhline(daily_energy.KH_DAILY_ENERGY_KJ, color="grey", linestyle="--")
        ax.set_xticks(x)
        ax.set_xticklabels(groups, rotation=30, ha="right")
        ax.set_ylabel("Mean daily travel energy, kJ")
        ax.set_title(title)
        ax.legend()
    fig.suptitle("F5. Mean daily travel energy, both rate sets (section 9.9 point 3)")
    fig.tight_layout()
    path = out_dir / "f05_mean_by_age_density.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_v0_p0(
    v0_stats: list, p0_stats: list, config: EnergyConfig, out_dir: Path
) -> Path:
    fig, (ax_v0, ax_p0) = plt.subplots(1, 2, figsize=(10, 5))
    ax_v0.bar(
        [s.age_band for s in v0_stats], [s.mean_value for s in v0_stats],
        color="tab:green",
    )
    ax_v0.axhline(
        config.walking.v0_kmh, color="grey", linestyle="--", label="configured v0"
    )
    ax_v0.set_xlabel("AGE6 age band")
    ax_v0.set_ylabel("Calibrated v0, km/h")
    ax_v0.set_title("(A) Walking: declared distance/duration")
    ax_v0.legend()

    ax_p0.bar(
        [s.age_band for s in p0_stats], [s.mean_value for s in p0_stats],
        color="tab:orange",
    )
    ax_p0.set_xlabel("AGE6 age band")
    ax_p0.set_ylabel("Calibrated P0, W")
    ax_p0.set_title("(B) Cycling: flat-ground required power")
    fig.suptitle("F6. Calibrated v0 and P0 by age band (section 9.9, step 1)")
    fig.tight_layout()
    path = out_dir / "f06_v0_p0.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _figure_passengers(passenger_trip_stats: dict, out_dir: Path) -> Path:
    groups = ["car_passenger_household", "car_passenger_carpool"]
    x = np.arange(len(groups))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 4.5))
    kh_means = [passenger_trip_stats[g][2] for g in groups]
    cp_means = [passenger_trip_stats[g][3] for g in groups]
    ax.bar(x - width / 2, kh_means, width, label="kh")
    ax.bar(x + width / 2, cp_means, width, label="compendium")
    ax.set_xticks(x)
    ax.set_xticklabels(["household", "carpool"])
    ax.set_ylabel("Mean one-way trip energy, kJ")
    ax.set_title(
        "F7. Car passengers: household vs carpool trips\n"
        "(section 9.9, companions-based split)"
    )
    ax.legend()
    fig.tight_layout()
    path = out_dir / "f07_passengers.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _format_group_table(stats: list) -> list[str]:
    lines = [
        "| Group | n | weighted n | mean time (min) | mean energy kh (kJ) | 95% CI | "
        "mean energy compendium (kJ) | 95% CI |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(stats, key=lambda s: -s.weighted_n):
        lines.append(
            f"| {s.group} | {s.n} | {s.weighted_n:,.0f} | {s.mean_time_min:.1f} | "
            f"{s.mean_energy_kh_kj:.1f} | [{s.mean_energy_kh_ci[0]:.1f}, "
            f"{s.mean_energy_kh_ci[1]:.1f}] | {s.mean_energy_cp_kj:.1f} | "
            f"[{s.mean_energy_cp_ci[0]:.1f}, {s.mean_energy_cp_ci[1]:.1f}] |"
        )
    return lines


def write_markdown(md_path: Path, out_dir: Path, results: dict) -> None:
    """Write the section 9.9 re-estimation report (steps 1-3, 5)."""
    lines = [
        "# Step 11 (`mobgrid/budget`): EMP 2019 re-estimation (section 9.9)",
        "",
        "Generated by `python -m mobgrid.budget.emp`. Rebuilds section 9.9's "
        "re-estimation steps 1-3 and 5 on the EMP 2019 public tables "
        "(`K_DEPLOC`, `TCM_IND_KISH`, `K_INDIVIDU`, `Q_MENAGE`); terminal "
        "legs reuse sections 9.4-9.7's formulas and `config/energy.yaml`'s "
        "already-calibrated car/stairs/waiting/PT-ride defaults, plus new "
        "provisional PT headway/station-height/access-walk defaults "
        "(TODO(confirm), `config.pt_ride`). EMC² (step 4) and Ē_c (step 6) "
        "are out of scope.",
        "",
        "**Variables used** (K_DEPLOC unless noted): mode `mtp`; duration "
        "`DUREE`; distance `MDISTTOT_fin`; purpose `MMOTIFDES`/`MOTPREC` "
        "(read, not yet used by this step's formulas); companions "
        "`MACCOMPM`/`MACCOMPHM` (household vs carpool passenger split); day "
        "`TYPEJOUR`; weights `POND_JOUR` (day) and `pond_indC` (K_INDIVIDU, "
        "individual); age band `AGE6` (TCM_IND_KISH); activity `SITUA` "
        "(TCM_IND_KISH, combined with `AGE` for the 6-17 children group); "
        "density of residence `DENSITECOM_ORI` of the home-departure trip "
        "(`MORIDOM`).",
        "",
        f"**Sample:** {results['n_days']:,} respondent-days with at least "
        "one classified trip "
        f"({results['non_traveler_n']} of "
        f"{results['n_days'] + results['non_traveler_n']} "
        f"respondents report no trip that day, {results['non_traveler_share']:.1%} "
        "by individual weight, reported apart per point 2).",
        "",
        "## Mean daily energy and time by main-mode group (point 3)",
        "",
        *_format_group_table(results["mode_stats"]),
        "",
        "## By age-activity group",
        "",
        *_format_group_table(results["age_activity_stats"]),
        "",
        "## By home density class",
        "",
        *_format_group_table(results["density_stats"]),
        "",
        "## Car passengers: household vs carpool (trip level)",
        "",
        "| Group | n | weighted n | mean one-way energy kh (kJ) | "
        "mean one-way energy compendium (kJ) |",
        "|---|---|---|---|---|",
    ]
    for group, (n, wn, mkh, mcp) in results["passenger_trip_stats"].items():
        lines.append(f"| {group} | {n} | {wn:,.0f} | {mkh:.1f} | {mcp:.1f} |")
    walk_n, walk_wn, walk_kh, walk_cp = results["passenger_walk"]
    lines += [
        f"| walking trips of car_passenger days | {walk_n} | {walk_wn:,.0f} | "
        f"{walk_kh:.1f} | {walk_cp:.1f} |",
        "",
        "## Constancy test (point 3, 5)",
        "",
        f"- Overall weighted mean daily energy: {results['mean_kh']:.1f} kJ (kh), "
        f"{results['mean_cp']:.1f} kJ (compendium); Koelbl & Helbing's (2003) "
        f"hypothesis is {daily_energy.KH_DAILY_ENERGY_KJ:g} kJ.",
        "- Max/min ratio of the six KH-comparable group means "
        f"(walking_only, cycle, car_driver, car_passenger, urban_pt, train): "
        f"{results['ratio_kh']:.2f} (kh), {results['ratio_cp']:.2f} (compendium).",
        "- Method-of-moments gamma fit (point 5): shape="
        f"{results['gamma_kh'][0]:.2f}, scale={results['gamma_kh'][1]:.1f} kJ (kh); "
        f"shape={results['gamma_cp'][0]:.2f}, scale={results['gamma_cp'][1]:.1f} kJ "
        "(compendium).",
        f"- Mean trips per person and day: {results['trips_per_day_mean']:.2f}.",
        "",
        "## Calibrated v0 and P0 (step 1)",
        "",
        f"- Overall v0: {results['v0_overall']:.2f} km/h (configured: "
        f"{results['config'].walking.v0_kmh:g} km/h).",
        f"- Overall P0: {results['p0_overall']:.1f} W (section 9.7's flat-ground "
        "reference: ~52.5 W at 16 km/h).",
        "",
        "| Age band (AGE6) | n walk | v0 (km/h) | n cycle | P0 (W) |",
        "|---|---|---|---|---|",
    ]
    p0_by_band = {s.age_band: s for s in results["p0_by_age_band"]}
    for v0_stat in results["v0_by_age_band"]:
        p0_stat = p0_by_band.get(v0_stat.age_band)
        p0_text = f"{p0_stat.n} | {p0_stat.mean_value:.1f}" if p0_stat else "0 | -"
        lines.append(
            f"| {v0_stat.age_band} | {v0_stat.n} | {v0_stat.mean_value:.2f} | "
            f"{p0_text} |"
        )

    lines += ["", "## Figures", ""]
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
        "- EMP 2019 gives no headway, station-depth or PT access-walk-distance "
        "data; `config.pt_ride.headway_min_am_peak`/`station_height_m`/"
        "`access_walk_m_by_density` are new, provisional TODO(confirm) "
        "defaults (section 9.3's station table, section 9.4's frequency "
        "formula), used only by this step.",
        "- Car terminal legs always use the apartment-density default "
        "(`config.car.walk_to_car.apartment_min_by_density`): the public "
        "tables give no house/apartment split (section 9.6's `s_house`).",
        "- `mode_group='other'` trips (taxi, specialised/school transport, "
        "plane, boat, unclassified) have no energy formula and contribute "
        "0 kJ to a day's total; a day with only such trips is its own "
        "'other' group, separate from 'multimodal'.",
        "- The day's home density is the origin density of its "
        "home-departure trip (`MORIDOM=1`), or the first trip by number "
        "if no such trip is recorded that day.",
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
