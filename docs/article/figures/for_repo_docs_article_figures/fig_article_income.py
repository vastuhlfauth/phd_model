"""Daily travel time by household income quintile, 2008 vs 2019 (article figure).

Reads the CSVs written by `python -m mobgrid.budget.zahavi_income` and draws
fig_time_by_income.{png,pdf,svg}: levels by quintile, raw and reweighted to a
common income x density x vehicle distribution, per weekday with trips (A) and
per person (B), with the 2019/2008 ratios and the Q5/Q1 gaps.

    python fig_article_income.py [path/to/docs/data/step12_income]

Default input folder: docs/data/step12_income, two folders above this file.
Scope: round-dest-local only (the reference scope).
"""

# ruff: noqa: E501  (long caption strings)

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
DATA = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE.parents[1] / "data" / "step12_income"
)
SCOPE = "round-dest-local"
YEAR = {"2008": "#2a78d6", "2019": "#eb6834"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
QUINTILES = [
    ("q1", "Q1\n(poorest)"),
    ("q2", "Q2"),
    ("q3", "Q3"),
    ("q4", "Q4"),
    ("q5", "Q5\n(richest)"),
]

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


def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["scope"] == SCOPE]


def f(x):
    return float(x)


def load():
    raw = {(r["basis"], r["quintile"]): r for r in read("levels.csv")}
    rew_rows = read("reweighted.csv")
    rew = {(r["basis"], r["quintile"]): r for r in rew_rows if r["row_type"] == "level"}
    rew_gap = {
        r["basis"]: r
        for r in rew_rows
        if r["row_type"] == "gap" and r["gap"] == "ratio"
    }
    gaps = {r["basis"]: r for r in read("gaps.csv") if r["gap"] == "ratio"}
    reg = {(r["year"], r["model"], r["term"]): r for r in read("regression.csv")}
    return raw, rew, rew_gap, gaps, reg


def style(ax, lo, hi):
    ax.set_ylim(lo, hi)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.tick_params(length=0, pad=3)


def panel(ax, basis, raw, rew, title, lo, hi):
    offsets = {
        ("2008", "raw"): -0.24,
        ("2008", "rew"): -0.1,
        ("2019", "raw"): 0.1,
        ("2019", "rew"): 0.24,
    }
    for x, (q, _) in enumerate(QUINTILES):
        for year in ("2008", "2019"):
            for kind, src in (("raw", raw), ("rew", rew)):
                r = src[(basis, q)]
                xx = x + offsets[(year, kind)]
                m = f(r[f"mean_{year}"])
                ax.vlines(
                    xx,
                    f(r[f"ci_{year}_low"]),
                    f(r[f"ci_{year}_high"]),
                    color=YEAR[year],
                    lw=2.0 if kind == "raw" else 1.0,
                    zorder=2,
                )
                if kind == "raw":
                    ax.plot(
                        xx,
                        m,
                        "o",
                        ms=5.5,
                        color=YEAR[year],
                        mec="white",
                        mew=0.8,
                        zorder=3,
                    )
                    ax.text(
                        xx,
                        f(r[f"ci_{year}_high"]) + 0.6,
                        f"{m:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=6.0,
                    )
                else:
                    ax.plot(
                        xx, m, "D", ms=4, mfc="white", mec=YEAR[year], mew=1.1, zorder=3
                    )
        r = raw[(basis, q)]
        ax.text(
            x,
            hi - 1.0,
            f"×{f(r['ratio']):.2f}\n[{f(r['ratio_ci_low']):.2f}, {f(r['ratio_ci_high']):.2f}]",
            ha="center",
            va="top",
            fontsize=5.9,
            linespacing=1.1,
        )
        ax.text(
            x,
            lo + 0.6,
            f"{int(r['n_2008']):,}\n{int(r['n_2019']):,}",
            ha="center",
            va="bottom",
            fontsize=5.5,
            color=INK_2,
            linespacing=1.05,
        )
    ax.set_title(title, loc="left", fontsize=8, color=INK, pad=6)
    ax.set_xticks(range(len(QUINTILES)), [lab for _, lab in QUINTILES], fontsize=7)
    ax.set_xlim(-0.55, len(QUINTILES) - 0.45)
    style(ax, lo, hi)


def main():
    raw, rew, rew_gap, gaps, reg = load()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.9), sharey=False)

    def gap_text(basis):
        g, w = gaps[basis], rew_gap[basis]
        return (
            f"Q5/Q1: {f(g['value_2008']):.3f} → {f(g['value_2019']):.3f} raw, "
            f"{f(w['value_2008']):.3f} → {f(w['value_2019']):.3f} reweighted"
        )

    panel(
        ax1,
        "travel_day",
        raw,
        rew,
        "A. Minutes per weekday with trips\n" + gap_text("travel_day"),
        40,
        92,
    )
    panel(
        ax2,
        "person",
        raw,
        rew,
        "B. Minutes per person (no-trip days = 0)\n" + gap_text("person"),
        30,
        82,
    )
    ax1.set_ylabel("Minutes per day", color=INK_2)
    m2 = {y: reg[(y, "M2", "income:q5")] for y in ("2008", "2019")}
    inter = reg[("pooled", "pooled", "survey:2019*income:q5")]
    handles = [
        Line2D(
            [], [], marker="o", ls="", color=YEAR["2008"], ms=5.5, label="ENTD 2008"
        ),
        Line2D([], [], marker="o", ls="", color=YEAR["2019"], ms=5.5, label="EMP 2019"),
        Line2D(
            [], [], marker="o", ls="-", color=INK_2, ms=5, lw=2, label="Raw, 95% CI"
        ),
        Line2D(
            [],
            [],
            marker="D",
            ls="-",
            color=INK_2,
            mfc="white",
            ms=4,
            lw=1,
            label="Reweighted, 95% CI",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=4,
        frameon=False,
        fontsize=6.8,
        bbox_to_anchor=(0.5, 1.0),
    )
    fig.text(
        0.01,
        0.005,
        "Quintiles of household income per consumption unit, relative within each year (ENTD: bracket midpoints; EMP: INSEE imputed decile). "
        "Above each quintile: ratio 2019/2008\n[90% CI], raw. Reweighted: each year reweighted to the pooled income × density (urban-unit proxy) × "
        "household vehicles (0, 1, 2+) distribution. Regression on log minutes\nper day with trips with population category, weekday, density "
        f"and vehicles: Q5 vs Q1 +{f(m2['2008']['percent']):.1f}% [{f(m2['2008']['ci_low']):.1f}, {f(m2['2008']['ci_high']):.1f}] in 2008, "
        f"+{f(m2['2019']['percent']):.1f}% [{f(m2['2019']['ci_low']):.1f}, {f(m2['2019']['ci_high']):.1f}] in 2019; "
        f"change {f(inter['percent']):+.1f}% [{f(inter['ci_low']):.1f}, {f(inter['ci_high']):.1f}].\n"
        "Residents aged 6+, Monday–Friday, round-trip days, destination purposes, local trips (≤ 80 km). Household bootstrap, 200 draws.\n"
        "Grey numbers at the foot: n 2008 (top) and 2019, weekdays with trips (A) or respondents (B). Sources: ENTD 2008, EMP 2019 (SDES/INSEE); author's calculations.",
        fontsize=5.6,
        color=INK_2,
        ha="left",
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.15, 1, 0.95), w_pad=1.5)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(HERE / f"fig_time_by_income.{ext}", dpi=300, facecolor="white")
    print(gap_text("travel_day"))
    print(gap_text("person"))


if __name__ == "__main__":
    main()
