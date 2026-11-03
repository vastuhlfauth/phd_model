"""Long-run weekday local mobility in France, 1994-2019 (published series).

Reads long_run_local_mobility.csv (same folder) and writes
fig_long_run_local_mobility.{png,pdf,svg}. Scope of the published series:
residents aged 6+, Monday-Friday, local trips (activities within 80 km of
home), all motives, per person (people who did not travel count as zero).
"""

from pathlib import Path

import csv

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3de"
SERIES = "#2a78d6"  # reference palette, categorical slot 1 (validated, light mode)

with open(HERE / "long_run_local_mobility.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
df = {
    "year": [int(r["year"]) for r in rows],
    "trips_per_person": [float(r["trips_per_person"]) for r in rows],
    "min_per_trip": [float(r["min_per_trip"]) for r in rows],
    "status": [r["status"] for r in rows],
}
df["min_per_person"] = [n * m for n, m in zip(df["trips_per_person"], df["min_per_trip"])]

panels = [
    ("trips_per_person", "Trips per person per day", "{:.2f}", 4.0),
    ("min_per_trip", "Minutes per trip", "{:.1f}", 24.0),
    ("min_per_person", "Minutes per person per day", "{:.0f}", 72.0),
]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "text.color": INK,
})

fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.7), dpi=300)
for ax, (col, title, fmt, ymax) in zip(axes, panels):
    ax.plot(df["year"], df[col], color=SERIES, lw=2, marker="o", ms=5,
            markeredgecolor="white", markeredgewidth=1.2, zorder=3)
    for x, y, status in zip(df["year"], df[col], df["status"]):
        label = fmt.format(y)
        ax.annotate(label, (x, y), xytext=(0, 7), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_title(title, fontsize=8.5, color=INK, loc="left", pad=6)
    ax.set_ylim(0, ymax)
    ax.set_xlim(1990, 2023)
    ax.set_xticks(df["year"])
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.tick_params(length=0, pad=4)

fig.text(0.01, 0.01,
         "Residents aged 6+, Monday-Friday, local trips (within 80 km of home), all motives; "
         "per person, non-travellers included.\nMinutes per person = trips x minutes per trip.\nSources: INSEE ETC 1994; SDES/INSEE ENTD 2008 "
         "and EMP 2019. Collection methods differ between editions.",
         fontsize=6.5, color=INK_2, ha="left", va="bottom")
fig.tight_layout(rect=(0, 0.19, 1, 1), w_pad=2.0)
for ext in ("png", "pdf", "svg"):
    fig.savefig(HERE / f"fig_long_run_local_mobility.{ext}", facecolor="white")
for i, year in enumerate(df["year"]):
    print(year, df["trips_per_person"][i], df["min_per_trip"][i],
          round(df["min_per_person"][i], 1), df["status"][i])
