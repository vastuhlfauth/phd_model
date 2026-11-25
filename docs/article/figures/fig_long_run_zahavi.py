"""Daily travel time, distance and door-to-door speed in France, 1982-2019 (article figure).

Reads france_local_series_time_distance_speed.csv (same folder) and writes
fig_long_run_time_distance_speed.{png,pdf,svg}. Scope of the series: residents
aged 6+, Monday-Friday, local trips (within 80 km of home), all purposes, per
person (people who did not travel count as zero). Speed = km per person-day
divided by hours per person-day, all modes, door to door.

    python fig_long_run_zahavi.py
"""

# ruff: noqa: E501  (long caption strings)

import csv
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
BLUE, NAVY = "#2a78d6", "#0d366b"

with open(
    HERE / "france_local_series_time_distance_speed.csv", newline="", encoding="utf-8"
) as f:
    rows = list(csv.DictReader(f))
years = [int(r["year"]) for r in rows]
series = {
    "min": [float(r["min_per_person_day"]) for r in rows],
    "km": [float(r["km_per_person_day"]) for r in rows],
    "kmh": [float(r["speed_kmh"]) for r in rows],
}
# Checks: speed = km / (minutes / 60), and minutes = trips x minutes per trip.
for r in rows:
    assert (
        abs(
            float(r["speed_kmh"])
            - float(r["km_per_person_day"]) / (float(r["min_per_person_day"]) / 60)
        )
        < 0.05
    ), r["year"]
    assert (
        abs(
            float(r["trips_per_person"]) * float(r["min_per_trip"])
            - float(r["min_per_person_day"])
        )
        < 0.1
    ), r["year"]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "text.color": INK,
        "axes.edgecolor": INK_2,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
    }
)


def style(ax, ymax):
    ax.set_ylim(0, ymax)
    ax.set_xlim(1977, 2024)
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.tick_params(length=0, pad=3)


fig, axes = plt.subplots(
    1, 4, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1, 1, 1, 1.35]}
)
panels = [
    ("min", "Minutes per person-day", "{:.1f}", 80),
    ("km", "Km per person-day", "{:.1f}", 35),
    ("kmh", "Door-to-door km/h", "{:.1f}", 35),
]
for ax, (key, title, fmt, ymax) in zip(axes[:3], panels, strict=True):
    ax.plot(
        years,
        series[key],
        color=BLUE,
        lw=1.8,
        marker="o",
        ms=4.5,
        mec="white",
        mew=1,
        zorder=3,
    )
    for x, y in zip(years, series[key], strict=True):
        ax.annotate(
            fmt.format(y),
            (x, y),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.5,
            color=INK,
        )
    ax.set_title(title, fontsize=8, loc="left", color=INK, pad=6)
    style(ax, ymax)

ax = axes[3]
lines = [
    ("min", "Minutes", INK, "-"),
    ("km", "Km", BLUE, "-"),
    ("kmh", "Km/h", NAVY, (0, (4, 2))),
]
for key, label, colour, ls in lines:
    idx = [100 * v / series[key][0] for v in series[key]]
    ax.plot(
        years,
        idx,
        color=colour,
        lw=1.6,
        ls=ls,
        marker="o",
        ms=3.5,
        mec="white",
        mew=0.8,
        zorder=3,
    )
    ax.annotate(
        f"{label} {idx[-1]:.0f}",
        (years[-1], idx[-1]),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        fontsize=6.5,
        color=colour,
    )
ax.axhline(100, color=INK_2, lw=0.6)
ax.set_title("Index, 1982 = 100", fontsize=8, loc="left", color=INK, pad=6)
style(ax, 170)
ax.set_ylim(80, 170)
ax.set_xlim(1977, 2033)

fig.text(
    0.01,
    0.01,
    "Residents aged 6+, Monday–Friday, local trips (within 80 km of home), all purposes; per person, non-travellers included. "
    "Speed = km ÷ hours,\nall modes, door to door. Published speeds: 18.9 (1982), 25.1 (1994), 27.0 km/h (2008). 2019: SDES table 2.2.1, "
    "3.04 trips × 20.4 min and × 8.73 km.\nSources: ENT 1981-82, ETC 1993-94, ENTD 2007-08 (UTP note on the ENTD 2008; INSEE); "
    "EMP 2018-19 (SDES). Collection methods differ between editions.",
    fontsize=5.8,
    color=INK_2,
    ha="left",
    va="bottom",
)
fig.tight_layout(rect=(0, 0.17, 1, 1), w_pad=1.4)
for ext in ("png", "pdf", "svg"):
    fig.savefig(
        HERE / f"fig_long_run_time_distance_speed.{ext}", dpi=300, facecolor="white"
    )
for i, y in enumerate(years):
    print(y, series["min"][i], series["km"][i], series["kmh"][i])
