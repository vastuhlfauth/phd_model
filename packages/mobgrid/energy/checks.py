"""Visual and tabular checks for the section 9 leg formulas (step 7).

``python -m mobgrid.energy.checks --out docs/data/step7_energy`` writes ten
PNG figures to ``--out`` and a Markdown report (check table and embedded
figures) to ``<out>_checks.md`` alongside it. No external data is read; the
whole run takes seconds.

Every figure is built from the *public* functions of ``rates``, ``walk``,
``bike`` and ``legs`` only (never a private reimplementation of a formula),
so the figures also exercise the package's API. A few scenario numbers
(bike power profiles, terminal-leg times, PT/car cruise speeds, trips per
day) have no single value in the spec; they are gathered in
``build_provisional`` below, used only for these figures -- they are never
written to ``config/energy.yaml``, which keeps its ``null``/``TODO(confirm)``
placeholders (section 9.7; see ``docs/progress.md``).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mobgrid.energy import bike, legs, walk
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
    activity_rate_kj_per_min,
    load_energy_config,
    sedentary_energy_kj,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"

#: Reference adult mass of the numerical examples of section 9.1/9.2, used
#: throughout these figures unless a check explicitly needs another value.
MASS_KG = 70.0

#: Kolbl & Helbing's (2003) UK National Travel Survey mean daily time by
#: mode, minutes (section 9.9).
KH_MEAN_DAILY_TIME_MIN = {
    "walk": 40.0,
    "cycle": 42.0,
    "bus": 67.0,
    "driver": 75.0,
    "passenger": 59.0,
    "train": 153.0,
}

#: Kolbl & Helbing's (2003) hypothesis: roughly 615 kJ of daily travel
#: energy per person and day, for people who travel (section 9.9).
KH_DAILY_ENERGY_KJ = 615.0

_SURFACE_KEY = "asphalt_concrete_paved_default"


def _required_power_w(
    speed_kmh: float,
    mass_kg: float,
    config: EnergyConfig,
    gradient: float = 0.0,
) -> float:
    """Rider power (public solver, bisection) holding ``speed_kmh`` (9.7).

    Used only to derive the "set A" provisional power profile below from
    its own defining consistency check (16 km/h flat, 70+15 kg); the
    figures that plot speed and energy call ``bike.solve_bike_speed_m_per_s``
    directly, in the forward (power -> speed) direction described in 14.7.
    """
    crr = config.bike.surface_crr[_SURFACE_KEY]
    target = speed_kmh * 1000.0 / 3600.0
    low, high = 0.0, 1000.0
    for _ in range(60):
        mid = (low + high) / 2.0
        speed = bike.solve_bike_speed_m_per_s(
            mid, mass_kg, gradient, crr, config.bike.cda_m2,
            config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
        )
        if speed < target:
            low = mid
        else:
            high = mid
    return high


def build_provisional(config: EnergyConfig) -> dict:
    """Scenario values for these figures only (see the module docstring)."""
    rider_and_bike_mass = MASS_KG + config.bike.bike_mass_kg
    p0_a = _required_power_w(16.0, rider_and_bike_mass, config)
    p0_b, p_max_b = 150.0, 250.0
    k_b = (p_max_b / p0_b - 1.0) / 0.05
    return {
        "bike_power": {
            # Set A, "calm": the 9.7 consistency check (~52.5 W at 16 km/h,
            # 70+15 kg); k=37 gives ~150 W at +5% as stated in section 9.7.
            "A": {"p0_w": p0_a, "k": 37.0, "p_max_w": 200.0},
            # Set B, "Parkin & Rotheram 2010 commuter": P0=150 W, k set so
            # P_max=250 W is reached at +5%.
            "B": {"p0_w": p0_b, "k": k_b, "p_max_w": p_max_b},
        },
        "v_max_descent_kmh": 30.0,
        "terminal": {
            "s_house": 0.3,
            "t_house_min": 0.5,
            "t_apartment_min": 2.0,
            "parking_search_min": 2.0,
            "walk_from_car_min": 2.0,
            "bike_get_park_min": 1.0,
            "bike_stops_per_km": 2.0,
            # Not given by the task; an illustrative PT access/egress walk.
            "pt_access_walk_m": 400.0,
        },
        "bus": {"headway_min": 10.0, "cv": 0.45, "ride_speed_kmh": 18.0},
        "metro": {
            "headway_min": 4.0, "cv": 0.15, "ride_speed_kmh": 30.0,
            "station_depth_m": 15.0,
        },
        "car": {"urban_speed_kmh": 30.0, "rho_values": (1.0, 1.5)},
        "trips_per_day": {"n": 3, "whiskers": (2, 4)},
    }


@dataclass
class CheckRow:
    """One row of the Markdown check table."""

    quantity: str
    expected: str
    computed: str
    tolerance: str
    status: Literal["PASS", "FAIL", "COMPARE"]


def _add_check(
    rows: list[CheckRow],
    quantity: str,
    expected_text: str,
    expected_value: float,
    computed_value: float,
    *,
    rel_tol: float | None = None,
    abs_tol: float | None = None,
    unit: str = "",
) -> None:
    if rel_tol is not None:
        ok = math.isclose(computed_value, expected_value, rel_tol=rel_tol)
        tol_text = f"+/-{rel_tol:.0%}"
    else:
        assert abs_tol is not None
        ok = abs(computed_value - expected_value) <= abs_tol
        tol_text = f"+/-{abs_tol:g}{unit}"
    rows.append(
        CheckRow(
            quantity, expected_text, f"{computed_value:.3f}{unit}", tol_text,
            "PASS" if ok else "FAIL",
        )
    )


def _add_compare(
    rows: list[CheckRow], quantity: str, expected_text: str, computed_text: str
) -> None:
    rows.append(CheckRow(quantity, expected_text, computed_text, "-", "COMPARE"))


def _implied_load_factor(standing_share: float) -> float:
    """Load factor consistent with a given standing share (section 9.5).

    Inverts ``legs.pt_standing_share``: LF = 1 / (1 - p_s). Used only to
    turn the "first phase, without load data" standing shares of section
    9.5 into a load factor, so the crowding-aware
    ``legs.pt_ride_rate_kj_per_min`` can still be used for a single
    illustrative rate.
    """
    return 1.0 / (1.0 - min(standing_share, 0.999_999))


def _bike_power(gradient: float, power_set: dict) -> float:
    return bike.select_ride_power_w(
        gradient, power_set["p0_w"], power_set["k"], power_set["p_max_w"]
    )


def _bike_speed_m_per_s(
    gradient: float,
    power_w: float,
    mass_total_kg: float,
    config: EnergyConfig,
    v_max_descent_kmh: float,
) -> float:
    """Bike speed at ``gradient``, capped at ``v_max_descent_kmh`` downhill."""
    crr = config.bike.surface_crr[_SURFACE_KEY]
    speed = bike.solve_bike_speed_m_per_s(
        power_w, mass_total_kg, gradient, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
    )
    if gradient < 0:
        speed = min(speed, v_max_descent_kmh * 1000.0 / 3600.0)
    return speed


def _rider_metabolic_kj(power_w: float, efficiency: float, duration_s: float) -> float:
    """Rider-only metabolic energy, kJ: P_r/efficiency . t (section 9.7).

    Correct for both a plain bike (where the rider supplies all propulsive
    power) and an e-bike (where ``power_w`` is the rider's own share only,
    "rider energy from P_r only"): going faster on the same rider power
    (because the motor adds the rest) simply means less *time* is spent,
    not more effort.
    """
    rate_kj_per_min = power_w / efficiency * 60.0 / 1000.0
    return sedentary_energy_kj(rate_kj_per_min, duration_s)


# --------------------------------------------------------------------- F1 --


def figure_1_leg_rates(
    config: EnergyConfig, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Section 9.2 reference-rate table: KH vs Compendium, at 70 kg."""
    activities = [
        "sitting_vehicle",
        "standing_relaxed",
        "standing_restless",
        "driving_free_flow",
        "driving_congested_cap",
    ]
    kh_values = []
    compendium_values = []
    rows: list[CheckRow] = []
    kh_expected = {
        "sitting_vehicle": 1.5,
        "standing_relaxed": 2.6,
        "standing_restless": 6.7,
        "driving_free_flow": 4.2,
        "driving_congested_cap": 8.0,
    }
    compendium_expected = {
        "sitting_vehicle": 1.5,
        "standing_relaxed": 2.6,
        "driving_free_flow": 5.1,
    }
    for activity in activities:
        rate = config.activity_rates[activity]
        kh_value = activity_rate_kj_per_min(rate, "kh", MASS_KG)
        kh_values.append(kh_value)
        _add_check(
            rows, f"9.2 rate, {activity} (KH)", f"{kh_expected[activity]} (9.2)",
            kh_expected[activity], kh_value, abs_tol=0.01, unit=" kJ/min",
        )
        if rate.compendium_net_met is not None:
            compendium_value = activity_rate_kj_per_min(rate, "compendium", MASS_KG)
            compendium_values.append(compendium_value)
            if activity in compendium_expected:
                _add_check(
                    rows, f"9.2 rate, {activity} (Compendium)",
                    f"{compendium_expected[activity]} (9.2)",
                    compendium_expected[activity], compendium_value,
                    rel_tol=0.03, unit=" kJ/min",
                )
        else:
            compendium_values.append(float("nan"))

    x = np.arange(len(activities))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, kh_values, width, label="KH (Spitzer et al. 1982)")
    ax.bar(x + width / 2, compendium_values, width, label="Compendium 2024")
    for index, value in enumerate(compendium_values):
        if math.isnan(value):
            ax.text(
                index + width / 2, 0.15, "n/a", ha="center", va="bottom", fontsize=8,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [a.replace("_", "\n") for a in activities], fontsize=8,
    )
    ax.set_ylabel("Rate above rest, kJ/min")
    ax.set_title(
        f"F1. Section 9.2 reference activity rates, {MASS_KG:g} kg\n"
        "KH values are absolute (do not scale with mass); Compendium values "
        "are net MET-minutes, mass-scaled"
    )
    ax.legend()
    fig.tight_layout()
    path = out_dir / "f01_leg_rates.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F2 --


def figure_2_walking(
    config: EnergyConfig, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Walking speed, gradient factor, energy per km and stairs (9.3)."""
    rows: list[CheckRow] = []
    coefficients = config.walking.gradient_polynomial_j_per_kg_m
    v0_kmh = config.walking.v0_kmh
    v0_m_per_s = v0_kmh * 1000.0 / 3600.0
    grades = np.linspace(-0.30, 0.30, 121)

    speeds_kmh = [
        walk.walking_speed_m_per_s(float(g), v0_m_per_s) * 3.6 for g in grades
    ]
    g_factors = [walk.gradient_factor(float(g), coefficients) for g in grades]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    ax = axes[0, 0]
    ax.plot(grades * 100, speeds_kmh)
    ax.set_xlabel("Grade, %")
    ax.set_ylabel("Speed, km/h")
    ax.set_title(f"Tobler walking speed, v0 = {v0_kmh:g} km/h (mass-independent)")

    ax = axes[0, 1]
    ax.plot(grades * 100, g_factors)
    marks = [(0.05, 1.44), (0.10, 1.96), (-0.10, 0.45)]
    for grade, expected in marks:
        computed = walk.gradient_factor(grade, coefficients)
        ax.scatter([grade * 100], [computed], color="red", zorder=3)
        ax.annotate(
            f"{computed:.2f}", (grade * 100, computed),
            textcoords="offset points", xytext=(5, 5), fontsize=8,
        )
        _add_check(
            rows, f"gradient factor g({grade:+.0%})", f"{expected} (9.3)",
            expected, computed, abs_tol=0.01,
        )
    ax.set_xlabel("Grade, %")
    ax.set_ylabel("g(i) = Cw(i)/Cw(0)")
    ax.set_title("Minetti et al. (2002) gradient factor")

    ax = axes[1, 0]
    for mass_kg, style in [(55.0, "--"), (70.0, "-"), (90.0, ":")]:
        c0 = config.walking.c0_j_per_kg_m["compendium"]
        energies = [
            walk.walking_time_and_energy(
                [(1000.0, float(g))], mass_kg, v0_kmh, c0, coefficients
            )[1]
            for g in grades
        ]
        ax.plot(grades * 100, energies, style, label=f"{mass_kg:g} kg, Compendium")
    c0_kh = config.walking.c0_j_per_kg_m["kh"]
    energies_kh = [
        walk.walking_time_and_energy(
            [(1000.0, float(g))], MASS_KG, v0_kmh, c0_kh, coefficients
        )[1]
        for g in grades
    ]
    ax.plot(grades * 100, energies_kh, "-.", color="black", label="70 kg, KH")
    ax.set_xlabel("Grade, %")
    ax.set_ylabel("Energy per km, kJ")
    ax.set_title("Walking energy per km, by mass and rate set")
    ax.legend(fontsize=7)

    flat_compendium = walk.walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, v0_kmh, config.walking.c0_j_per_kg_m["compendium"],
        coefficients,
    )[1]
    _add_check(
        rows, "1 km flat walk, 70 kg (Compendium)", "160 kJ (9.3)", 160.0,
        flat_compendium, rel_tol=0.02, unit=" kJ",
    )
    flat_kh = walk.walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, v0_kmh, c0_kh, coefficients
    )[1]
    _add_check(
        rows, "1 km flat walk, 70 kg (KH)", "211 kJ (9.3)", 211.0, flat_kh,
        rel_tol=0.01, unit=" kJ",
    )

    ax = axes[1, 1]
    up_t, up_e = walk.stair_time_and_energy(
        10.0, "up", MASS_KG, config.stairs.up_speed_m_per_s,
        config.stairs.down_speed_m_per_s, config.stairs.up_efficiency,
        config.stairs.down_to_up_energy_ratio,
    )
    down_t, down_e = walk.stair_time_and_energy(
        10.0, "down", MASS_KG, config.stairs.up_speed_m_per_s,
        config.stairs.down_speed_m_per_s, config.stairs.up_efficiency,
        config.stairs.down_to_up_energy_ratio,
    )
    ax.bar(["up (10 m)", "down (10 m)"], [up_e, down_e], color=["tab:red", "tab:blue"])
    for index, (value, duration) in enumerate([(up_e, up_t), (down_e, down_t)]):
        ax.text(
            index, value, f"{value:.1f} kJ\n{duration:.0f} s", ha="center",
            va="bottom", fontsize=8,
        )
    ax.set_ylabel("Energy above rest, kJ")
    ax.set_title("Stairs, 70 kg (section 9.3)")
    _add_check(
        rows, "stairs up, 10 m, 70 kg", "~22.9 kJ (9.3)", 22.9, up_e, rel_tol=0.03,
        unit=" kJ",
    )

    fig.suptitle(
        f"F2. Walking: speed, gradient factor, energy per km and stairs "
        f"({config.rate_set} rate set shown by default)"
    )
    fig.tight_layout()
    path = out_dir / "f02_walking.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F3 --


def figure_3_bike(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Bike speed and rider energy per km vs grade, sets A/B and e-bike (9.7)."""
    rows: list[CheckRow] = []
    crr = config.bike.surface_crr[_SURFACE_KEY]
    eff = config.bike.gross_muscular_efficiency
    eta_d = config.bike.drivetrain_efficiency
    bike_mass = MASS_KG + config.bike.bike_mass_kg
    ebike_mass = MASS_KG + config.bike.ebike_mass_kg
    v_max_desc = provisional["v_max_descent_kmh"]
    grades = np.linspace(-0.08, 0.10, 91)
    length_m = 1000.0

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax_speed, ax_energy = axes

    for name, power_set, mass_total, style in [
        ("Bike, set A (calm)", provisional["bike_power"]["A"], bike_mass, "-"),
        (
            "Bike, set B (Parkin & Rotheram)", provisional["bike_power"]["B"],
            bike_mass, "--",
        ),
    ]:
        speeds, energies = [], []
        for grade in grades:
            power = _bike_power(float(grade), power_set)
            speed = _bike_speed_m_per_s(
                float(grade), power, mass_total, config, v_max_desc
            )
            speeds.append(speed * 3.6)
            time_s = length_m / speed if speed > 0 else float("inf")
            energies.append(_rider_metabolic_kj(power, eff, time_s))
        ax_speed.plot(grades * 100, speeds, linestyle=style, label=name)
        ax_energy.plot(grades * 100, energies, linestyle=style, label=name)

    for level, style in [
        ("eco", ":"), ("tour", "-."), ("sport", "--"), ("turbo", "-"),
    ]:
        assist = config.bike.ebike.assist_factor_by_level[level]
        speeds, energies = [], []
        for grade in grades:
            power_set = provisional["bike_power"]["A"]
            rider_power = _bike_power(float(grade), power_set)
            speed = bike.solve_ebike_speed_m_per_s(
                rider_power, ebike_mass, float(grade), crr, config.bike.cda_m2,
                config.bike.rho_air_kg_per_m3, eta_d, assist,
                config.bike.ebike.motor_power_cap_w, config.bike.ebike.speed_cap_kmh,
            )
            if grade < 0:
                speed = min(speed, v_max_desc * 1000.0 / 3600.0)
            speeds.append(speed * 3.6)
            time_s = length_m / speed if speed > 0 else float("inf")
            energies.append(_rider_metabolic_kj(rider_power, eff, time_s))
        ax_speed.plot(
            grades * 100, speeds, linestyle=style, alpha=0.8,
            label=f"E-bike A, {level}",
        )
        ax_energy.plot(
            grades * 100, energies, linestyle=style, alpha=0.8,
            label=f"E-bike A, {level}",
        )

    # +10 kg effect at the reference consistency check (set A, flat).
    power_flat = _bike_power(0.0, provisional["bike_power"]["A"])
    base_speed = _bike_speed_m_per_s(0.0, power_flat, bike_mass, config, v_max_desc)
    heavier_speed = _bike_speed_m_per_s(
        0.0, power_flat, bike_mass + 10.0, config, v_max_desc
    )
    speed_change_pct = (heavier_speed / base_speed - 1.0) * 100.0
    _add_check(
        rows, "bike speed change, +10 kg, flat, set A", "-2.4% (9.7)", -2.4,
        speed_change_pct, abs_tol=0.3, unit="%",
    )
    climb_power = 100.0
    base_climb_speed = _bike_speed_m_per_s(
        0.05, climb_power, bike_mass, config, v_max_desc
    )
    heavier_climb_speed = _bike_speed_m_per_s(
        0.05, climb_power, bike_mass + 10.0, config, v_max_desc
    )
    climb_change_pct = (heavier_climb_speed / base_climb_speed - 1.0) * 100.0
    _add_check(
        rows, "bike speed change, +10 kg, 5% climb, 100 W", "-9.8% (9.7)", -9.8,
        climb_change_pct, abs_tol=0.5, unit="%",
    )

    ax_speed.axhline(25.0, color="grey", linestyle=":", linewidth=1)
    ax_speed.annotate(
        "25 km/h EU pedelec cutoff", (grades.min() * 100, 25.5), fontsize=7,
    )
    ax_speed.annotate(
        f"+10 kg, flat: {speed_change_pct:+.1f}%", (0, base_speed * 3.6),
        textcoords="offset points", xytext=(10, -15), fontsize=7,
    )
    ax_speed.set_xlabel("Grade, %")
    ax_speed.set_ylabel("Speed, km/h")
    ax_speed.legend(fontsize=6)
    ax_speed.set_title(
        f"Speed, M = {bike_mass:g} kg (bike) / {ebike_mass:g} kg (e-bike)"
    )

    ax_energy.set_xlabel("Grade, %")
    ax_energy.set_ylabel("Rider metabolic energy per km, kJ")
    ax_energy.legend(fontsize=6)
    ax_energy.set_title(f"Energy per km, efficiency = {eff:g}")

    power_16 = _required_power_w(16.0, bike_mass, config)
    _add_check(
        rows, "mechanical power, 16 km/h flat, M=85 kg", "~52.5 W (9.7)", 52.5,
        power_16, rel_tol=0.02, unit=" W",
    )
    rate_16 = power_16 / eff * 60.0 / 1000.0
    _add_check(
        rows, "metabolic rate, 16 km/h flat, M=85 kg", "~13.1 kJ/min (9.7)", 13.1,
        rate_16, rel_tol=0.02, unit=" kJ/min",
    )
    speed_check = bike.solve_bike_speed_m_per_s(
        power_16, bike_mass, 0.0, crr, config.bike.cda_m2,
        config.bike.rho_air_kg_per_m3, eta_d,
    )
    stop_energy = bike.stop_energy_kj(speed_check, bike_mass, eff)
    _add_check(
        rows, "one-stop energy, 16 km/h, M=85 kg", "~3.50 kJ (9.7)", 3.50,
        stop_energy, rel_tol=0.02, unit=" kJ",
    )

    # COMPARE: the model keeps rider power fixed across assist levels, so
    # its metabolic rate does not fall with more assistance, unlike the
    # Compendium's own without/light/high-support figures (section 9.7).
    def _net_met_kj_per_min(gross_met: float) -> float:
        return (gross_met - 1.0) * MET_MINUTE_KJ_PER_KG * MASS_KG

    _add_compare(
        rows, "e-bike rider rate vs Compendium light support (tour)",
        f"{_net_met_kj_per_min(6.0):.1f} kJ/min (light, 6.0 MET) / "
        f"{_net_met_kj_per_min(6.8):.1f} kJ/min (unassisted, 6.8 MET), 9.7",
        f"{rate_16:.1f} kJ/min (model: same at every assist level)",
    )
    _add_compare(
        rows, "e-bike rider rate vs Compendium high support (sport)",
        f"{_net_met_kj_per_min(4.0):.1f} kJ/min (high, 4.0 MET) / "
        f"{_net_met_kj_per_min(6.8):.1f} kJ/min (unassisted, 6.8 MET), 9.7",
        f"{rate_16:.1f} kJ/min (model: same at every assist level)",
    )

    set_b_speed_kmh = _bike_speed_m_per_s(
        0.0, provisional["bike_power"]["B"]["p0_w"], bike_mass, config, v_max_desc
    ) * 3.6
    _add_compare(
        rows, "set B flat speed vs Parkin & Rotheram (2010)",
        "~22 km/h (85th percentile commuter)", f"{set_b_speed_kmh:.1f} km/h",
    )

    fig.suptitle(
        "F3. Bike and e-bike: speed and rider metabolic energy per km vs "
        "grade, 70 kg rider (M = rider + bike/e-bike mass)"
    )
    fig.tight_layout()
    path = out_dir / "f03_bike_speed_energy.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F4 --


def figure_4_bike_energy_split(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Bike energy split (roll, climb, stops, drag) for 5 km (9.7).

    E-bike bars show the same roll/climb/stops/drag split, computed at the
    e-bike's own (faster) speed and divided by the same efficiency, as if
    the rider alone supplied all of it; in reality the motor supplies part
    of it, so the rider's own metabolic cost is lower (see F3's rider-only
    curves, which do split the motor and rider power correctly).
    """
    rows: list[CheckRow] = []
    crr = config.bike.surface_crr[_SURFACE_KEY]
    eff = config.bike.gross_muscular_efficiency
    eta_d = config.bike.drivetrain_efficiency
    rho_air = config.bike.rho_air_kg_per_m3
    cda = config.bike.cda_m2
    bike_mass = MASS_KG + config.bike.bike_mass_kg
    ebike_mass = MASS_KG + config.bike.ebike_mass_kg
    v_max_desc = provisional["v_max_descent_kmh"]
    length_m = 5000.0
    stops_per_km = provisional["terminal"]["bike_stops_per_km"]
    tour_assist = config.bike.ebike.assist_factor_by_level["tour"]

    scenarios = [
        ("flat, no stops", 0.0, 0.0),
        ("flat, 10 stops", 0.0, stops_per_km * length_m / 1000.0),
        ("+50 m climb", 50.0 / length_m, 0.0),
    ]

    def _split(power_w, mass_total, speed, n_stops):
        roll = bike.rolling_work_j_per_kg(length_m, grade, crr)
        climb = bike.climbing_work_j_per_kg(length_m, grade)
        drag = bike.drag_work_j(length_m, speed, rho_air, cda)
        roll_kj = bike.bike_ride_energy_kj(roll, 0.0, 0.0, 0.0, mass_total, eff)
        climb_kj = bike.bike_ride_energy_kj(0.0, climb, 0.0, 0.0, mass_total, eff)
        drag_kj = bike.bike_ride_energy_kj(0.0, 0.0, 0.0, drag, mass_total, eff)
        stops_kj = n_stops * bike.stop_energy_kj(speed, mass_total, eff)
        return roll_kj, climb_kj, stops_kj, drag_kj

    labels, components = [], {"roll": [], "climb": [], "stops": [], "drag": []}
    for scenario_name, grade, n_stops in scenarios:
        power = _bike_power(grade, provisional["bike_power"]["A"])
        speed = _bike_speed_m_per_s(grade, power, bike_mass, config, v_max_desc)
        roll_kj, climb_kj, stops_kj, drag_kj = _split(power, bike_mass, speed, n_stops)
        labels.append(f"Bike\n{scenario_name}")
        components["roll"].append(roll_kj)
        components["climb"].append(climb_kj)
        components["stops"].append(stops_kj)
        components["drag"].append(drag_kj)

        rider_power = power
        ebike_speed = bike.solve_ebike_speed_m_per_s(
            rider_power, ebike_mass, grade, crr, cda, rho_air, eta_d, tour_assist,
            config.bike.ebike.motor_power_cap_w, config.bike.ebike.speed_cap_kmh,
        )
        if grade < 0:
            ebike_speed = min(ebike_speed, v_max_desc * 1000.0 / 3600.0)
        roll_kj, climb_kj, stops_kj, drag_kj = _split(
            rider_power, ebike_mass, ebike_speed, n_stops
        )
        labels.append(f"E-bike tour\n{scenario_name}")
        components["roll"].append(roll_kj)
        components["climb"].append(climb_kj)
        components["stops"].append(stops_kj)
        components["drag"].append(drag_kj)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    bottom = np.zeros(len(labels))
    for key, color in [
        ("roll", "tab:brown"), ("climb", "tab:green"), ("stops", "tab:orange"),
        ("drag", "tab:blue"),
    ]:
        values = np.array(components[key])
        ax.bar(x, values, bottom=bottom, label=key, color=color)
        bottom += values
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Rider metabolic energy, kJ (as if unassisted)")
    ax.legend()
    ax.set_title(
        "F4. Bike energy split for 5 km, bike vs e-bike (tour), 70 kg rider\n"
        "E-bike bars overstate the rider's real cost (motor supplies part "
        "of the drag/roll/climb work); see F3 for the rider-only split"
    )
    fig.tight_layout()
    path = out_dir / "f04_bike_energy_split.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F5 --


def figure_5_pt_and_car_rates(
    config: EnergyConfig, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """r_ride vs load factor by vehicle type; r_drive vs rho (9.5, 9.6)."""
    rows: list[CheckRow] = []
    r_sit = config.pt_ride.r_sit_kj_per_min
    r_relaxed = config.pt_ride.r_relaxed_kj_per_min
    r_restless = config.pt_ride.r_restless_kj_per_min

    fig, (ax_pt, ax_car) = plt.subplots(1, 2, figsize=(12, 5))

    for vehicle, lf_max in config.pt_ride.load_factor_max.items():
        load_factors = np.linspace(0.5, lf_max + 0.5, 60)
        rates = [
            legs.pt_ride_rate_kj_per_min(
                float(lf), lf_max, r_sit, r_relaxed, r_restless
            )
            for lf in load_factors
        ]
        ax_pt.plot(load_factors, rates, label=f"{vehicle} (LF_max={lf_max:g})")
    ax_pt.axhline(r_sit, color="grey", linestyle=":", linewidth=1)
    ax_pt.set_xlabel("Load factor LF (passengers per seat)")
    ax_pt.set_ylabel("r_ride, kJ/min above rest")
    ax_pt.set_title(
        "r_ride vs load factor, by vehicle type\n"
        "r_sit/r_relaxed/r_restless pinned to KH (9.5), not switched by rate set"
    )
    ax_pt.legend(fontsize=6)

    r_stand_at_one = legs.pt_standing_rate_kj_per_min(1.0, 4.0, r_relaxed, r_restless)
    _add_check(
        rows, "r_stand at LF=1", "2.6 kJ/min (9.5)", 2.6, r_stand_at_one,
        abs_tol=0.01, unit=" kJ/min",
    )
    metro_lf_max = config.pt_ride.load_factor_max["metro"]
    r_stand_at_crush = legs.pt_standing_rate_kj_per_min(
        metro_lf_max, metro_lf_max, r_relaxed, r_restless
    )
    _add_check(
        rows, "r_stand at LF=LF_max (metro)", "6.7 kJ/min (9.5)", 6.7,
        r_stand_at_crush, abs_tol=0.01, unit=" kJ/min",
    )

    rho_max = config.car.congestion_rho_max
    rhos = np.linspace(1.0, rho_max * 1.5, 60)
    for rate_set in ("kh", "compendium"):
        free_flow = activity_rate_kj_per_min(
            config.activity_rates["driving_free_flow"], rate_set, MASS_KG
        )
        drive_rates = [
            legs.driving_rate_kj_per_min(
                float(rho), rho_max, free_flow, config.car.r_congested_cap_kj_per_min
            )
            for rho in rhos
        ]
        ax_car.plot(rhos, drive_rates, label=f"{rate_set}, 70 kg")
    ax_car.axvline(rho_max, color="grey", linestyle=":", linewidth=1)
    ax_car.set_xlabel("rho = congested time / free-flow time")
    ax_car.set_ylabel("r_drive, kJ/min above rest")
    ax_car.set_title("r_drive vs congestion, both rate sets")
    ax_car.legend()

    r_drive_at_cap = legs.driving_rate_kj_per_min(
        rho_max, rho_max,
        activity_rate_kj_per_min(
            config.activity_rates["driving_free_flow"], "kh", MASS_KG
        ),
        config.car.r_congested_cap_kj_per_min,
    )
    _add_check(
        rows, "r_drive at rho >= rho_max", "8.0 kJ/min (9.6)", 8.0, r_drive_at_cap,
        abs_tol=0.01, unit=" kJ/min",
    )

    wait_s = legs.expected_wait_s(
        10 * 60.0, 0.45, config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0,
    )
    _add_check(
        rows, "wait, h=10 min, CV=0.45", "6.0 min (9.4)", 6.0, wait_s / 60.0,
        abs_tol=0.05, unit=" min",
    )

    fig.suptitle("F5. Ride and driving rates by crowding and congestion")
    fig.tight_layout()
    path = out_dir / "f05_pt_and_car_rates.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F6 --


def figure_6_energy_landscape(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Energy per km vs energy per minute, log-log, with iso-speed lines.

    "Wait" has no distance of its own; it is drawn as a horizontal
    reference line at its rate instead of a point.
    """
    rows: list[CheckRow] = []
    eff = config.bike.gross_muscular_efficiency
    bike_mass = MASS_KG + config.bike.bike_mass_kg
    ebike_mass = MASS_KG + config.bike.ebike_mass_kg
    v_max_desc = provisional["v_max_descent_kmh"]
    r_sit = config.pt_ride.r_sit_kj_per_min
    r_relaxed = config.pt_ride.r_relaxed_kj_per_min
    r_restless = config.pt_ride.r_restless_kj_per_min
    bus_speed = provisional["bus"]["ride_speed_kmh"]
    car_speed = provisional["car"]["urban_speed_kmh"]

    points: dict[str, tuple[float, float]] = {}

    walk_t, walk_e = walk.walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, config.walking.v0_kmh,
        config.walking.c0_j_per_kg_m["compendium"],
        config.walking.gradient_polynomial_j_per_kg_m,
    )
    points["walk"] = (walk_e, walk_e / (walk_t / 60.0))

    for label, power_set in [("bike A", provisional["bike_power"]["A"]),
                              ("bike B", provisional["bike_power"]["B"])]:
        power = _bike_power(0.0, power_set)
        speed = _bike_speed_m_per_s(0.0, power, bike_mass, config, v_max_desc)
        rate = power / eff * 60.0 / 1000.0
        points[label] = (rate * (1000.0 / speed) / 60.0, rate)

    rider_power = _bike_power(0.0, provisional["bike_power"]["A"])
    assist = config.bike.ebike.assist_factor_by_level["tour"]
    ebike_speed = bike.solve_ebike_speed_m_per_s(
        rider_power, ebike_mass, 0.0, config.bike.surface_crr[_SURFACE_KEY],
        config.bike.cda_m2, config.bike.rho_air_kg_per_m3,
        config.bike.drivetrain_efficiency, assist,
        config.bike.ebike.motor_power_cap_w, config.bike.ebike.speed_cap_kmh,
    )
    ebike_rate = rider_power / eff * 60.0 / 1000.0
    points["e-bike tour"] = (ebike_rate * (1000.0 / ebike_speed) / 60.0, ebike_rate)

    bus_lf_max = config.pt_ride.load_factor_max["urban_bus"]
    points["PT seated"] = (r_sit * 60.0 / bus_speed, r_sit)
    rate_standing = legs.pt_ride_rate_kj_per_min(
        2.0, bus_lf_max, r_sit, r_relaxed, r_restless
    )
    points["PT standing"] = (rate_standing * 60.0 / bus_speed, rate_standing)
    points["PT crowded standing"] = (r_restless * 60.0 / bus_speed, r_restless)

    r_free = activity_rate_kj_per_min(
        config.activity_rates["driving_free_flow"], config.rate_set, MASS_KG
    )
    points["car driver, free"] = (r_free * 60.0 / car_speed, r_free)
    r_congested = legs.driving_rate_kj_per_min(
        config.car.congestion_rho_max, config.car.congestion_rho_max, r_free,
        config.car.r_congested_cap_kj_per_min,
    )
    points["car driver, congested"] = (r_congested * 60.0 / car_speed, r_congested)
    points["car passenger"] = (r_sit * 60.0 / car_speed, r_sit)

    fig, ax = plt.subplots(figsize=(8, 7))
    for label, (x, y) in points.items():
        ax.scatter([x], [y])
        ax.annotate(
            label, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=7,
        )
    ax.axhline(r_relaxed, color="grey", linestyle="--", linewidth=1)
    ax.annotate(
        "wait (stationary, no km)",
        (ax.get_xlim()[0] if ax.get_xlim()[0] > 0 else 1, r_relaxed),
        fontsize=7, va="bottom",
    )

    all_x = [p[0] for p in points.values()]
    x_range = np.array([min(all_x) * 0.5, max(all_x) * 2.0])
    for speed_kmh in (4.8, 16.0, 18.0, 25.0, 30.0):
        y_line = x_range * speed_kmh / 60.0
        ax.plot(x_range, y_line, color="grey", linestyle=":", linewidth=0.7)
        ax.annotate(
            f"{speed_kmh:g} km/h", (x_range[-1], y_line[-1]), fontsize=6, color="grey",
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Energy per km, kJ (log)")
    ax.set_ylabel("Energy per minute, kJ/min (log)")
    ax.set_title(
        f"F6. Energy landscape on the flat, 70 kg, {config.rate_set} rate set\n"
        "Diagonals are iso-speed lines (slope 1 in log-log)"
    )
    fig.tight_layout()
    path = out_dir / "f06_energy_landscape.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# ------------------------------------------------------- chain builders --

#: Leg (name, duration_s, energy_kj) triples make up a door-to-door chain.
ChainLeg = tuple[str, float, float]

CHAIN_MODES = (
    "walk", "bike", "ebike_tour", "bus", "metro", "car_driver", "car_passenger",
)


def _short_walk_leg(
    minutes: float, mass_kg: float, config: EnergyConfig
) -> tuple[float, float]:
    """A short flat walk of a given duration (walk-to-car, parking, etc).

    Section 9.6 gives these as times, not distances; the walking formula
    is applied to the flat-ground distance that time implies at v0, so
    the same public ``walk.walking_time_and_energy`` computes it exactly.
    """
    v0_m_per_s = config.walking.v0_kmh * 1000.0 / 3600.0
    length_m = minutes * 60.0 * v0_m_per_s
    duration_s, energy_kj = walk.walking_time_and_energy(
        [(length_m, 0.0)], mass_kg, config.walking.v0_kmh,
        config.walking.c0_j_per_kg_m["compendium"],
        config.walking.gradient_polynomial_j_per_kg_m,
    )
    return duration_s, energy_kj


def _pt_access_legs(
    mode: Literal["bus", "metro"], config: EnergyConfig, provisional: dict
) -> list[ChainLeg]:
    """Access walk, stairs/escalator (metro) and wait, one way (9.3-9.5)."""
    params = provisional[mode]
    access_m = provisional["terminal"]["pt_access_walk_m"]
    walk_leg_s, walk_leg_kj = walk.walking_time_and_energy(
        [(access_m, 0.0)], MASS_KG, config.walking.v0_kmh,
        config.walking.c0_j_per_kg_m["compendium"],
        config.walking.gradient_polynomial_j_per_kg_m,
    )
    chain_legs: list[ChainLeg] = [("walk to stop", walk_leg_s, walk_leg_kj)]
    if mode == "metro":
        depth = params["station_depth_m"]
        duration_s, stair_energy_kj = walk.stair_time_and_energy(
            depth, "down", MASS_KG, config.stairs.up_speed_m_per_s,
            config.stairs.down_speed_m_per_s, config.stairs.up_efficiency,
            config.stairs.down_to_up_energy_ratio,
        )
        if depth > config.stairs.escalator_depth_threshold_m:
            # Escalators and lifts are taken at the standing rate (9.3).
            energy_kj = sedentary_energy_kj(
                config.pt_ride.r_relaxed_kj_per_min, duration_s
            )
        else:
            energy_kj = stair_energy_kj
        chain_legs.append(("level change (down)", duration_s, energy_kj))
    r_relaxed = config.pt_ride.r_relaxed_kj_per_min
    wait_leg = legs.waiting_leg(
        params["headway_min"] * 60.0, params["cv"],
        config.waiting.headway_regime_threshold_min * 60.0,
        config.waiting.w_planned_min * 60.0, r_relaxed,
    )
    chain_legs.append(("wait", wait_leg.duration_s, wait_leg.energy_kj))
    return chain_legs


def build_chain(
    mode: str, distance_km: float, config: EnergyConfig, provisional: dict
) -> list[ChainLeg]:
    """One one-way door-to-door chain's legs (name, duration_s, energy_kj).

    A documented, illustrative composition of ``rates``/``walk``/``bike``/
    ``legs`` public functions over ``provisional``'s scenario parameters;
    not itself part of the tested production formulas.
    """
    length_m = distance_km * 1000.0
    terminal = provisional["terminal"]
    chain_legs: list[ChainLeg] = []

    if mode == "walk":
        duration_s, energy_kj = walk.walking_time_and_energy(
            [(length_m, 0.0)], MASS_KG, config.walking.v0_kmh,
            config.walking.c0_j_per_kg_m["compendium"],
            config.walking.gradient_polynomial_j_per_kg_m,
        )
        chain_legs.append(("walk", duration_s, energy_kj))

    elif mode in ("bike", "ebike_tour"):
        crr = config.bike.surface_crr[_SURFACE_KEY]
        eff = config.bike.gross_muscular_efficiency
        v_max_desc = provisional["v_max_descent_kmh"]
        get_park_s = terminal["bike_get_park_min"] * 60.0
        get_park_kj = sedentary_energy_kj(
            config.activity_rates["standing_relaxed"].kh_kj_per_min, get_park_s
        )
        chain_legs.append(("get bike", get_park_s, get_park_kj))
        power = _bike_power(0.0, provisional["bike_power"]["A"])
        n_stops = terminal["bike_stops_per_km"] * distance_km
        if mode == "bike":
            mass_total = MASS_KG + config.bike.bike_mass_kg
            speed = _bike_speed_m_per_s(0.0, power, mass_total, config, v_max_desc)
        else:
            mass_total = MASS_KG + config.bike.ebike_mass_kg
            assist = config.bike.ebike.assist_factor_by_level["tour"]
            speed = bike.solve_ebike_speed_m_per_s(
                power, mass_total, 0.0, crr, config.bike.cda_m2,
                config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
                assist, config.bike.ebike.motor_power_cap_w,
                config.bike.ebike.speed_cap_kmh,
            )
        ride_s = length_m / speed
        ride_kj = _rider_metabolic_kj(power, eff, ride_s)
        stops_kj = n_stops * bike.stop_energy_kj(speed, mass_total, eff)
        chain_legs.append(("ride", ride_s, ride_kj + stops_kj))
        chain_legs.append(("park bike", get_park_s, get_park_kj))

    elif mode in ("bus", "metro"):
        chain_legs.extend(_pt_access_legs(mode, config, provisional))
        params = provisional[mode]
        access_km = 2.0 * terminal["pt_access_walk_m"] / 1000.0
        ride_km = max(distance_km - access_km, 0.1)
        ride_s = ride_km / params["ride_speed_kmh"] * 3600.0
        standing_share = {
            "bus": config.pt_ride.standing_share_am_peak["urban_bus"],
            "metro": config.pt_ride.standing_share_am_peak["metro"],
        }[mode]
        lf_max = config.pt_ride.load_factor_max[
            "urban_bus" if mode == "bus" else "metro"
        ]
        load_factor = _implied_load_factor(standing_share)
        ride_leg = legs.pt_ride_leg(
            ride_s, load_factor, lf_max, config.pt_ride.r_sit_kj_per_min,
            config.pt_ride.r_relaxed_kj_per_min, config.pt_ride.r_restless_kj_per_min,
        )
        chain_legs.append(("ride", ride_leg.duration_s, ride_leg.energy_kj))
        if mode == "metro":
            duration_s, stair_energy_kj = walk.stair_time_and_energy(
                params["station_depth_m"], "up", MASS_KG,
                config.stairs.up_speed_m_per_s, config.stairs.down_speed_m_per_s,
                config.stairs.up_efficiency, config.stairs.down_to_up_energy_ratio,
            )
            if params["station_depth_m"] > config.stairs.escalator_depth_threshold_m:
                energy_kj = sedentary_energy_kj(
                    config.pt_ride.r_relaxed_kj_per_min, duration_s
                )
            else:
                energy_kj = stair_energy_kj
            chain_legs.append(("level change (up)", duration_s, energy_kj))
        egress_walk_s, egress_walk_kj = walk.walking_time_and_energy(
            [(terminal["pt_access_walk_m"], 0.0)], MASS_KG, config.walking.v0_kmh,
            config.walking.c0_j_per_kg_m["compendium"],
            config.walking.gradient_polynomial_j_per_kg_m,
        )
        chain_legs.append(("walk from stop", egress_walk_s, egress_walk_kj))

    elif mode in ("car_driver", "car_passenger"):
        to_car_min = (
            terminal["s_house"] * terminal["t_house_min"]
            + (1.0 - terminal["s_house"]) * terminal["t_apartment_min"]
        )
        to_car_s, to_car_kj = _short_walk_leg(to_car_min, MASS_KG, config)
        chain_legs.append(("walk to car", to_car_s, to_car_kj))
        speed_kmh = provisional["car"]["urban_speed_kmh"]
        drive_s = length_m / (speed_kmh * 1000.0 / 3600.0)
        if mode == "car_driver":
            free_flow = activity_rate_kj_per_min(
                config.activity_rates["driving_free_flow"], config.rate_set, MASS_KG
            )
            drive_leg = legs.car_drive_leg(
                drive_s, 1.0, config.car.congestion_rho_max, free_flow,
                config.car.r_congested_cap_kj_per_min,
            )
        else:
            sitting = activity_rate_kj_per_min(
                config.activity_rates["sitting_vehicle"], config.rate_set, MASS_KG
            )
            drive_leg = legs.car_passenger_leg(drive_s, sitting)
        chain_legs.append(("drive", drive_leg.duration_s, drive_leg.energy_kj))
        parking_s = terminal["parking_search_min"] * 60.0
        parking_rate = activity_rate_kj_per_min(
            config.activity_rates["driving_free_flow"], config.rate_set, MASS_KG
        )
        chain_legs.append(
            ("parking search", parking_s, sedentary_energy_kj(parking_rate, parking_s))
        )
        from_car_s, from_car_kj = _short_walk_leg(
            terminal["walk_from_car_min"], MASS_KG, config
        )
        chain_legs.append(("walk from car", from_car_s, from_car_kj))

    else:
        raise ValueError(f"unknown chain mode: {mode!r}")

    return chain_legs


_MODE_LABELS = {
    "walk": "Walk", "bike": "Bike", "ebike_tour": "E-bike (tour)", "bus": "Bus",
    "metro": "Metro", "car_driver": "Car driver", "car_passenger": "Car passenger",
}


def _chain_totals(
    mode: str, distance_km: float, config: EnergyConfig, provisional: dict
) -> tuple[float, float]:
    chain = build_chain(mode, distance_km, config, provisional)
    return sum(leg[1] for leg in chain), sum(leg[2] for leg in chain)


def _affine_fit(
    mode: str, config: EnergyConfig, provisional: dict, d1_km: float = 1.0,
    d2_km: float = 2.0,
) -> tuple[float, float, float, float]:
    """Fixed terminal part and per-km slope of a chain's time and energy.

    Every chain built by ``build_chain`` is exactly affine in distance (a
    fixed terminal/access part plus a distance-proportional ride part), so
    two points determine the line exactly; used by F8(b)'s iso-energy /
    iso-time reachable distance.
    """
    t1, e1 = _chain_totals(mode, d1_km, config, provisional)
    t2, e2 = _chain_totals(mode, d2_km, config, provisional)
    time_slope = (t2 - t1) / (d2_km - d1_km)
    time_intercept = t1 - time_slope * d1_km
    energy_slope = (e2 - e1) / (d2_km - d1_km)
    energy_intercept = e1 - energy_slope * d1_km
    return time_intercept, time_slope, energy_intercept, energy_slope


# --------------------------------------------------------------------- F7 --


def figure_7_chains(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Door-to-door chains of 2, 5 and 10 km: stacked time and energy."""
    rows: list[CheckRow] = []
    distances = (2.0, 5.0, 10.0)
    chains = {
        (mode, distance): build_chain(mode, distance, config, provisional)
        for mode in CHAIN_MODES
        for distance in distances
    }
    leg_names = sorted({leg[0] for chain in chains.values() for leg in chain})
    palette = plt.get_cmap("tab20")
    colors = {
        name: palette(i / max(len(leg_names) - 1, 1))
        for i, name in enumerate(leg_names)
    }

    fig, axes = plt.subplots(2, len(distances), figsize=(14, 8), sharex=True)
    for col, distance in enumerate(distances):
        for row, (quantity_index, scale, ylabel) in enumerate(
            [(1, 1.0 / 60.0, "Time, min"), (2, 1.0, "Energy, kJ")]
        ):
            ax = axes[row, col]
            bottoms = np.zeros(len(CHAIN_MODES))
            seen_labels = set()
            max_legs = max(len(chains[(m, distance)]) for m in CHAIN_MODES)
            for leg_index in range(max_legs):
                values = []
                color_list = []
                label_list = []
                for mode in CHAIN_MODES:
                    chain = chains[(mode, distance)]
                    if leg_index < len(chain):
                        name, duration_s, energy_kj = chain[leg_index]
                        value = (
                            duration_s if quantity_index == 1 else energy_kj
                        ) * scale
                    else:
                        name, value = None, 0.0
                    values.append(value)
                    color_list.append(colors.get(name, "lightgrey"))
                    label_list.append(name)
                for mode_index, (value, color, name) in enumerate(
                    zip(values, color_list, label_list, strict=True)
                ):
                    label = name if name not in seen_labels else None
                    ax.bar(
                        mode_index, value, bottom=bottoms[mode_index], color=color,
                        label=label,
                    )
                    if name is not None:
                        seen_labels.add(name)
                bottoms += np.array(values)
            ax.set_xticks(range(len(CHAIN_MODES)))
            ax.set_xticklabels(
                [_MODE_LABELS[m] for m in CHAIN_MODES], rotation=45, ha="right",
                fontsize=7,
            )
            ax.set_ylabel(ylabel)
            if row == 0:
                ax.set_title(f"{distance:g} km")
            if row == 0 and col == len(distances) - 1:
                ax.legend(fontsize=6, bbox_to_anchor=(1.02, 1.0), loc="upper left")

    fig.suptitle(
        f"F7. Door-to-door chains, stacked by leg, 70 kg, {config.rate_set} rate set"
    )
    fig.tight_layout()
    path = out_dir / "f07_chains.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F8 --


def figure_8_iso_energy(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Iso-energy: how far E = 615 kJ (and E/n per trip) goes, per mode."""
    rows: list[CheckRow] = []
    time_cap_s = 3.0 * 3600.0
    eff = config.bike.gross_muscular_efficiency
    bike_mass = MASS_KG + config.bike.bike_mass_kg
    ebike_mass = MASS_KG + config.bike.ebike_mass_kg
    v_max_desc = provisional["v_max_descent_kmh"]

    # (a) minutes and km that 615 kJ buys in each main-mode leg on the flat.
    main_mode_rates_kmh: list[tuple[str, float, float]] = []
    v0_kmh = config.walking.v0_kmh
    walk_rate = (
        walk.walking_time_and_energy(
            [(1000.0, 0.0)], MASS_KG, v0_kmh,
            config.walking.c0_j_per_kg_m["compendium"],
            config.walking.gradient_polynomial_j_per_kg_m,
        )[1]
        * (v0_kmh / 60.0)
    )  # kJ/min on the flat at v0
    main_mode_rates_kmh.append(("Walk", walk_rate, v0_kmh))

    power_a = _bike_power(0.0, provisional["bike_power"]["A"])
    bike_speed = _bike_speed_m_per_s(0.0, power_a, bike_mass, config, v_max_desc)
    bike_rate = power_a / eff * 60.0 / 1000.0
    main_mode_rates_kmh.append(("Bike A", bike_rate, bike_speed * 3.6))

    assist = config.bike.ebike.assist_factor_by_level["tour"]
    ebike_speed = bike.solve_ebike_speed_m_per_s(
        power_a, ebike_mass, 0.0, config.bike.surface_crr[_SURFACE_KEY],
        config.bike.cda_m2, config.bike.rho_air_kg_per_m3,
        config.bike.drivetrain_efficiency, assist,
        config.bike.ebike.motor_power_cap_w, config.bike.ebike.speed_cap_kmh,
    )
    main_mode_rates_kmh.append(("E-bike tour", bike_rate, ebike_speed * 3.6))

    r_free = activity_rate_kj_per_min(
        config.activity_rates["driving_free_flow"], config.rate_set, MASS_KG
    )
    car_speed = provisional["car"]["urban_speed_kmh"]
    main_mode_rates_kmh.append(("Car driver", r_free, car_speed))
    r_sit = activity_rate_kj_per_min(
        config.activity_rates["sitting_vehicle"], config.rate_set, MASS_KG
    )
    main_mode_rates_kmh.append(("Car passenger", r_sit, car_speed))
    bus_speed = provisional["bus"]["ride_speed_kmh"]
    main_mode_rates_kmh.append(
        ("Bus ride", config.pt_ride.r_sit_kj_per_min, bus_speed)
    )
    metro_speed = provisional["metro"]["ride_speed_kmh"]
    main_mode_rates_kmh.append(
        ("Metro ride", config.pt_ride.r_sit_kj_per_min, metro_speed)
    )

    labels_a, minutes_a, km_a, capped_a = [], [], [], []
    for label, rate_kj_per_min, speed_kmh in main_mode_rates_kmh:
        minutes = KH_DAILY_ENERGY_KJ / rate_kj_per_min
        cap = minutes > 180.0
        minutes = min(minutes, 180.0)
        labels_a.append(label)
        minutes_a.append(minutes)
        km_a.append(minutes * speed_kmh / 60.0)
        capped_a.append(cap)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5))
    x = np.arange(len(labels_a))
    bars = ax_a.bar(
        x, minutes_a, color=["tab:red" if c else "tab:blue" for c in capped_a]
    )
    for index, (bar, km, cap) in enumerate(zip(bars, km_a, capped_a, strict=True)):
        suffix = " (capped)" if cap else ""
        ax_a.text(
            index, bar.get_height(), f"{km:.1f} km{suffix}", ha="center", va="bottom",
            fontsize=7,
        )
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels_a, rotation=30, ha="right", fontsize=8)
    ax_a.set_ylabel("Minutes bought by 615 kJ (capped at 180 min)")
    ax_a.set_title("(a) Minutes and km that E = 615 kJ buys, main-mode leg")

    # (b) door-to-door distance reachable per mode with E/n per one-way trip.
    n = provisional["trips_per_day"]["n"]
    budget_kj = KH_DAILY_ENERGY_KJ / n
    labels_b, distances_b, capped_b = [], [], []
    for mode in CHAIN_MODES:
        t0, t_slope, e0, e_slope = _affine_fit(mode, config, provisional)
        distance_energy = (
            (budget_kj - e0) / e_slope if e_slope > 0 else float("inf")
        )
        distance_time = (
            (time_cap_s - t0) / t_slope if t_slope > 0 else float("inf")
        )
        distance = max(min(distance_energy, distance_time), 0.0)
        labels_b.append(_MODE_LABELS[mode])
        distances_b.append(distance)
        capped_b.append(distance_time < distance_energy)

    x = np.arange(len(labels_b))
    colors_b = ["tab:red" if c else "tab:blue" for c in capped_b]
    bars = ax_b.bar(x, distances_b, color=colors_b)
    for index, (bar, cap) in enumerate(zip(bars, capped_b, strict=True)):
        if cap:
            ax_b.text(
                index, bar.get_height(), "time-capped", ha="center", va="bottom",
                fontsize=7,
            )
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(labels_b, rotation=30, ha="right", fontsize=8)
    ax_b.set_ylabel(f"One-way distance, km (n={n} trips/day, 3 h time cap)")
    ax_b.set_title(f"(b) Door-to-door distance for E/n = {budget_kj:.0f} kJ")

    fig.suptitle(
        "F8. Iso-energy: how far 615 kJ of daily travel energy goes "
        f"(illustrative; {config.rate_set} rate set)"
    )
    fig.tight_layout()
    path = out_dir / "f08_iso_energy.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# --------------------------------------------------------------------- F9 --

#: Kolbl & Helbing's six daily-budget modes mapped to a chain builder mode
#: and its main ("ride"/"drive") leg name; walk has no separate main leg,
#: since the whole trip is the main mode (section 9.9).
_F9_MODE_CHAIN = {
    "walk": ("walk", None),
    "cycle": ("bike", "ride"),
    "bus": ("bus", "ride"),
    "driver": ("car_driver", "drive"),
    "passenger": ("car_passenger", "drive"),
    "train": ("metro", "ride"),  # terminal legs only; see module docstring
}


def _f9_walk_rate_kj_per_min(config: EnergyConfig, rate_set: str) -> float:
    c0 = config.walking.c0_j_per_kg_m[rate_set]
    v0_kmh = config.walking.v0_kmh
    per_km_kj = walk.walking_time_and_energy(
        [(1000.0, 0.0)], MASS_KG, v0_kmh, c0,
        config.walking.gradient_polynomial_j_per_kg_m,
    )[1]
    return per_km_kj * v0_kmh / 60.0


def _f9_main_rate_kj_per_min(
    mode_key: str, config: EnergyConfig, provisional: dict, rate_set: str
) -> float:
    if mode_key == "walk":
        return _f9_walk_rate_kj_per_min(config, rate_set)
    if mode_key == "cycle":
        power_a = _bike_power(0.0, provisional["bike_power"]["A"])
        return power_a / config.bike.gross_muscular_efficiency * 60.0 / 1000.0
    if mode_key in ("bus", "train"):
        # PT ride rates are pinned to KH regardless of rate_set (section 9.5).
        return config.pt_ride.r_sit_kj_per_min
    if mode_key == "driver":
        return activity_rate_kj_per_min(
            config.activity_rates["driving_free_flow"], rate_set, MASS_KG
        )
    if mode_key == "passenger":
        return activity_rate_kj_per_min(
            config.activity_rates["sitting_vehicle"], rate_set, MASS_KG
        )
    raise ValueError(mode_key)


def _f9_terminal_per_trip(
    mode_key: str, config: EnergyConfig, provisional: dict
) -> tuple[float, float]:
    """One trip's fixed terminal time (s) and energy (kJ), section 9.9(B)."""
    chain_mode, main_name = _F9_MODE_CHAIN[mode_key]
    if main_name is None:
        return 0.0, 0.0
    chain = build_chain(chain_mode, 5.0, config, provisional)
    terminal_time = sum(leg[1] for leg in chain if leg[0] != main_name)
    terminal_energy = sum(leg[2] for leg in chain if leg[0] != main_name)
    return terminal_time, terminal_energy


def _f9_a_energy_kj(
    mode_key: str, config: EnergyConfig, provisional: dict, rate_set: str
) -> float:
    rate = _f9_main_rate_kj_per_min(mode_key, config, provisional, rate_set)
    return KH_MEAN_DAILY_TIME_MIN[mode_key] * rate


def _f9_b_energy_kj(
    mode_key: str, n: int, config: EnergyConfig, provisional: dict, rate_set: str
) -> float:
    terminal_time_s, terminal_energy_kj = _f9_terminal_per_trip(
        mode_key, config, provisional
    )
    total_time_s = KH_MEAN_DAILY_TIME_MIN[mode_key] * 60.0
    remaining_s = max(total_time_s - n * terminal_time_s, 0.0)
    rate = _f9_main_rate_kj_per_min(mode_key, config, provisional, rate_set)
    return n * terminal_energy_kj + remaining_s / 60.0 * rate


def figure_9_daily_budget(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Daily budget at Kolbl & Helbing's mean daily times (section 9.9)."""
    rows: list[CheckRow] = []
    modes = list(KH_MEAN_DAILY_TIME_MIN)
    n = provisional["trips_per_day"]["n"]
    n_low, n_high = provisional["trips_per_day"]["whiskers"]
    rate_sets = ("kh", "compendium")

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    width = 0.35
    x = np.arange(len(modes))
    for offset, rate_set in zip((-width / 2, width / 2), rate_sets, strict=True):
        values_a = [
            _f9_a_energy_kj(mode, config, provisional, rate_set) for mode in modes
        ]
        ax_a.bar(x + offset, values_a, width, label=rate_set)

        centers, lows, highs = [], [], []
        for mode in modes:
            values = [
                _f9_b_energy_kj(mode, n_i, config, provisional, rate_set)
                for n_i in (n_low, n, n_high)
            ]
            centers.append(values[1])
            lows.append(min(values))
            highs.append(max(values))
        centers_arr = np.array(centers)
        errors = np.array(
            [centers_arr - np.array(lows), np.array(highs) - centers_arr]
        )
        ax_b.bar(x + offset, centers, width, label=rate_set)
        ax_b.errorbar(
            x + offset, centers, yerr=errors, fmt="none", ecolor="black", capsize=3,
        )

    for ax, title in [
        (ax_a, "(A) Whole mean time at the main-mode rate"),
        (
            ax_b,
            f"(B) Same time, n={n} trips' terminal legs "
            f"(whiskers n={n_low}/{n_high})",
        ),
    ]:
        ax.axhline(KH_DAILY_ENERGY_KJ, color="grey", linestyle="--", linewidth=1)
        ax.axhspan(
            KH_DAILY_ENERGY_KJ * 0.8, KH_DAILY_ENERGY_KJ * 1.2, color="grey",
            alpha=0.15,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(modes, rotation=30, ha="right")
        ax.set_ylabel("Daily travel energy, kJ")
        ax.set_title(title)
        ax.legend()

    fig.suptitle(
        "F9. Daily energy budget at Kolbl & Helbing's (2003) mean daily "
        "times; dashed line/band = 615 kJ +/-20%"
    )
    fig.tight_layout()
    path = out_dir / "f09_daily_budget.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)

    walk_kj = _f9_a_energy_kj("walk", config, provisional, "compendium")
    net_met_minutes = KH_DAILY_ENERGY_KJ / (MET_MINUTE_KJ_PER_KG * MASS_KG)
    _add_check(
        rows, "615 kJ in net MET-minutes, 70 kg", "~120 net MET-min (9.9)", 120.0,
        net_met_minutes, rel_tol=0.03, unit=" net MET-min",
    )
    _add_check(
        rows, "F9-A walking day (Compendium)", "~510 kJ (9.9)", 510.0, walk_kj,
        rel_tol=0.05, unit=" kJ",
    )
    driver_kj = _f9_a_energy_kj("driver", config, provisional, "compendium")
    _add_check(
        rows, "F9-A driving only (Compendium)", "~385 kJ (9.9)", 385.0, driver_kj,
        rel_tol=0.05, unit=" kJ",
    )
    passenger_kj = _f9_a_energy_kj("passenger", config, provisional, "compendium")
    _add_check(
        rows, "F9-A car passenger sitting only (Compendium)", "~90 kJ (9.9)", 90.0,
        passenger_kj, rel_tol=0.05, unit=" kJ",
    )
    for mode in modes:
        value = _f9_b_energy_kj(mode, n, config, provisional, config.rate_set)
        _add_compare(
            rows, f"F9-B total, {mode} (n={n}, {config.rate_set})", "~615 kJ (9.9)",
            f"{value:.0f} kJ",
        )

    return rows, path


# -------------------------------------------------------------------- F10 --


def figure_10_mass_sensitivity(
    config: EnergyConfig, provisional: dict, out_dir: Path
) -> tuple[list[CheckRow], Path]:
    """Energy of a 5 km trip vs body mass, 50-110 kg (walk/bike/e-bike/car)."""
    rows: list[CheckRow] = []
    masses = np.linspace(50.0, 110.0, 61)
    length_m = 5000.0
    eff = config.bike.gross_muscular_efficiency
    crr = config.bike.surface_crr[_SURFACE_KEY]
    v_max_desc = provisional["v_max_descent_kmh"]
    car_speed = provisional["car"]["urban_speed_kmh"]

    fig, ax = plt.subplots(figsize=(9, 6))
    for rate_set, style in [("kh", "--"), ("compendium", "-")]:
        c0 = config.walking.c0_j_per_kg_m[rate_set]
        walk_energies = [
            walk.walking_time_and_energy(
                [(length_m, 0.0)], float(m), config.walking.v0_kmh, c0,
                config.walking.gradient_polynomial_j_per_kg_m,
            )[1]
            for m in masses
        ]
        ax.plot(
            masses, walk_energies, linestyle=style, color="tab:green",
            label=f"Walk ({rate_set})",
        )

        power_a = provisional["bike_power"]["A"]
        bike_energies = []
        for m in masses:
            power = _bike_power(0.0, power_a)
            mass_total = float(m) + config.bike.bike_mass_kg
            speed = _bike_speed_m_per_s(0.0, power, mass_total, config, v_max_desc)
            bike_energies.append(_rider_metabolic_kj(power, eff, length_m / speed))
        ax.plot(
            masses, bike_energies, linestyle=style, color="tab:blue",
            label=f"Bike A ({rate_set})",
        )

        assist = config.bike.ebike.assist_factor_by_level["tour"]
        ebike_energies = []
        for m in masses:
            power = _bike_power(0.0, power_a)
            mass_total = float(m) + config.bike.ebike_mass_kg
            speed = bike.solve_ebike_speed_m_per_s(
                power, mass_total, 0.0, crr, config.bike.cda_m2,
                config.bike.rho_air_kg_per_m3, config.bike.drivetrain_efficiency,
                assist, config.bike.ebike.motor_power_cap_w,
                config.bike.ebike.speed_cap_kmh,
            )
            ebike_energies.append(_rider_metabolic_kj(power, eff, length_m / speed))
        ax.plot(
            masses, ebike_energies, linestyle=style, color="tab:orange",
            label=f"E-bike tour ({rate_set})",
        )

        drive_s = length_m / (car_speed * 1000.0 / 3600.0)
        car_energies = [
            sedentary_energy_kj(
                activity_rate_kj_per_min(
                    config.activity_rates["driving_free_flow"], rate_set, float(m)
                ),
                drive_s,
            )
            for m in masses
        ]
        ax.plot(
            masses, car_energies, linestyle=style, color="tab:red",
            label=f"Car driver ({rate_set})",
        )

    ax.axvline(config.reference_mass_kg, color="grey", linestyle=":", linewidth=1)
    ax.annotate(
        f"{config.reference_mass_kg:g} kg",
        (config.reference_mass_kg, ax.get_ylim()[1]),
        fontsize=8, ha="center", va="top",
    )
    ax.set_xlabel("Body mass, kg")
    ax.set_ylabel("Energy of a 5 km trip, kJ")
    ax.set_title(
        "F10. Energy of a 5 km trip vs body mass, KH (dashed) vs Compendium "
        "(solid)\nCar driver's Compendium rate scales with mass (net MET); "
        "its KH rate is a reference-adult constant"
    )
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    path = out_dir / "f10_mass_sensitivity.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return rows, path


# ------------------------------------------------------------- reporting --

FIGURE_FUNCTIONS = (
    ("F1", lambda cfg, prov, out: figure_1_leg_rates(cfg, out)),
    ("F2", lambda cfg, prov, out: figure_2_walking(cfg, out)),
    ("F3", figure_3_bike),
    ("F4", figure_4_bike_energy_split),
    ("F5", lambda cfg, prov, out: figure_5_pt_and_car_rates(cfg, out)),
    ("F6", figure_6_energy_landscape),
    ("F7", figure_7_chains),
    ("F8", figure_8_iso_energy),
    ("F9", figure_9_daily_budget),
    ("F10", figure_10_mass_sensitivity),
)


def run(
    out_dir: Path, config_path: Path = DEFAULT_CONFIG_PATH
) -> tuple[list[CheckRow], list[Path], EnergyConfig, dict]:
    """Generate all ten figures; return the check rows and figure paths."""
    config = load_energy_config(config_path)
    provisional = build_provisional(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[CheckRow] = []
    all_paths: list[Path] = []
    for _, figure_function in FIGURE_FUNCTIONS:
        rows, path = figure_function(config, provisional, out_dir)
        all_rows.extend(rows)
        all_paths.append(path)
    return all_rows, all_paths, config, provisional


def write_markdown(
    md_path: Path,
    out_dir: Path,
    rows: list[CheckRow],
    paths: list[Path],
    config: EnergyConfig,
    provisional: dict,
) -> None:
    """Write the check table and embedded figures (section 9 step 7)."""
    fail_count = sum(1 for row in rows if row.status == "FAIL")
    pass_count = sum(1 for row in rows if row.status == "PASS")
    compare_count = sum(1 for row in rows if row.status == "COMPARE")
    lines = [
        "# Step 7 (`mobgrid/energy`): leg formula checks (section 9)",
        "",
        "Generated by `python -m mobgrid.energy.checks`. No external data; "
        f"mass = {MASS_KG:g} kg (section 9.1 convention) unless a figure "
        "states otherwise; `config/energy.yaml` rate set = "
        f"`{config.rate_set}`.",
        "",
        f"**Check summary: {pass_count} PASS, {fail_count} FAIL, "
        f"{compare_count} COMPARE.**",
        "",
        "## Check table",
        "",
        "| Quantity | Expected (spec section) | Computed | Tolerance | Status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.quantity} | {row.expected} | {row.computed} | "
            f"{row.tolerance} | {row.status} |"
        )

    lines += [
        "",
        "## Figures",
        "",
    ]
    for path in paths:
        try:
            relative = path.relative_to(md_path.parent)
        except ValueError:
            relative = path
        lines.append(f"![{path.stem}]({relative.as_posix()})")
        lines.append("")

    lines += [
        "## Provisional values used only in these figures",
        "",
        "`config/energy.yaml` keeps every `null`/`TODO(confirm)` placeholder "
        "unchanged; the scenario numbers below (`checks.build_provisional`) "
        "are used only to draw these figures.",
        "",
        f"- Bike set A (\"calm\", 9.7 consistency check): P0 = "
        f"{provisional['bike_power']['A']['p0_w']:.1f} W, k = "
        f"{provisional['bike_power']['A']['k']:g}, Pmax = "
        f"{provisional['bike_power']['A']['p_max_w']:g} W",
        "- Bike set B (Parkin & Rotheram 2010 commuter): P0 = "
        f"{provisional['bike_power']['B']['p0_w']:g} W, k = "
        f"{provisional['bike_power']['B']['k']:.2f}, Pmax = "
        f"{provisional['bike_power']['B']['p_max_w']:g} W",
        f"- Both sets: v_max,desc = {provisional['v_max_descent_kmh']:g} km/h",
        "- Urban terminal legs: s_house="
        f"{provisional['terminal']['s_house']:g}, t_house="
        f"{provisional['terminal']['t_house_min']:g} min, t_apartment="
        f"{provisional['terminal']['t_apartment_min']:g} min, parking "
        f"search={provisional['terminal']['parking_search_min']:g} min, "
        "walk from car="
        f"{provisional['terminal']['walk_from_car_min']:g} min, get/park "
        f"bike={provisional['terminal']['bike_get_park_min']:g} min each, "
        f"{provisional['terminal']['bike_stops_per_km']:g} bike stops/km",
        "- PT access/egress walk (illustrative, not in the task's list): "
        f"{provisional['terminal']['pt_access_walk_m']:g} m each way",
        f"- Bus: h={provisional['bus']['headway_min']:g} min, "
        f"CV={provisional['bus']['cv']:g}, ride="
        f"{provisional['bus']['ride_speed_kmh']:g} km/h",
        f"- Metro: h={provisional['metro']['headway_min']:g} min, "
        f"CV={provisional['metro']['cv']:g}, ride="
        f"{provisional['metro']['ride_speed_kmh']:g} km/h, station depth="
        f"{provisional['metro']['station_depth_m']:g} m (escalator, >10 m)",
        f"- Car: {provisional['car']['urban_speed_kmh']:g} km/h urban; "
        f"rho in {list(provisional['car']['rho_values'])}",
        f"- Trips per day: n={provisional['trips_per_day']['n']}, "
        f"whiskers n={list(provisional['trips_per_day']['whiskers'])}",
        "",
        "## Modelling notes and simplifications",
        "",
        "- F3/F4/F6/F7/F8/F9/F10's e-bike rider metabolic energy uses "
        "bike set A's rider power profile plus the configured pedelec "
        "assist factor and motor cap (section 9.7): rider effort does not "
        "fall with more assistance in this model, only speed rises (F3's "
        "COMPARE rows against the Compendium's light/high-support MET "
        "values make this gap explicit).",
        "- F4's e-bike roll/climb/stops/drag split is computed at the "
        "e-bike's own (faster) speed and divided by the same efficiency, "
        "as if the rider alone supplied it; the real rider cost is lower "
        "(see F3's correct rider-only split).",
        "- F7/F8/F9's PT legs use an illustrative access/egress walk "
        f"({provisional['terminal']['pt_access_walk_m']:g} m each way), not "
        "given by the task, and an implied load factor "
        "(`1/(1-standing_share)`) from section 9.5's first-phase standing "
        "shares, so the crowding-aware PT ride formula can still be used.",
        "- F9-B's \"train\" mode reuses the metro chain's terminal legs "
        "(access walk, escalator, wait) as a stand-in, with its own "
        "seated main-mode rate, since section 9 gives no separate rail "
        "access/wait model (per the task's \"Train: metro terminal legs\").",
        "- Bike/car stop and parking-search durations are not modelled "
        "with a time cost beyond the distance/speed-implied ride time "
        "(section 9.7's stop-time formula needs signal-timing data not "
        "configured here); only their energy is counted.",
        "- F8(b) and the chains solve for distance/time exactly from each "
        "chain's two-point affine fit (`_affine_fit`), since every chain "
        "built by `build_chain` is exactly linear in distance.",
    ]

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mobgrid.energy.checks",
        description=__doc__.splitlines()[0] if __doc__ else "",
    )
    parser.add_argument(
        "--out", required=True, type=Path,
        help="Directory to write the 10 PNG figures to",
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH,
        help="Path to config/energy.yaml",
    )
    args = parser.parse_args(argv)

    out_dir: Path = args.out
    rows, paths, config, provisional = run(out_dir, args.config)
    md_path = out_dir.parent / f"{out_dir.name}_checks.md"
    write_markdown(md_path, out_dir, rows, paths, config, provisional)

    fail_count = sum(1 for row in rows if row.status == "FAIL")
    print(f"Wrote {len(paths)} figures to {out_dir}")
    print(f"Wrote check table to {md_path}")
    print(
        f"{sum(1 for r in rows if r.status == 'PASS')} PASS, {fail_count} FAIL, "
        f"{sum(1 for r in rows if r.status == 'COMPARE')} COMPARE"
    )
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

