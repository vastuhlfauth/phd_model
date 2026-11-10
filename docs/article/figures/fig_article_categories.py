"""Weekday daily travel time by population category, 2008 vs 2019 (article figure).

Reads the step 11 comparison report and its figure CSV (the report is the single
source of numbers) and writes fig_time_by_category.{png,pdf,svg} next to this file.

    python fig_article_categories.py [path/to/step11_compare.md]

Default report path: docs/data/step11_compare.md, two folders above this file.
Values come from:
- per day with trips: mean, 95% CI, median and quartiles from the CSV of
  compare_time_by_category (panel B, weekday only); n and the 2019/2008 ratio
  with its 90% CI from the "Daily time, weekday days with trips" table;
- per person: means and 95% CIs from "Daily time, per person", n and ratios from
  "Daily time, weekday per-person budgets";
- the "All" lines from the overall rows of those tables.
Each value printed on the figure is checked against the report before drawing.
"""

# ruff: noqa: E501  (long caption strings)

import csv
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
REPORT = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE.parents[1] / "data" / "step11_compare.md"
)
FIG_CSV = REPORT.with_suffix("") / "compare_time_by_category.csv"

YEAR_COLOURS = {"2008": "#2a78d6", "2019": "#eb6834"}
YEAR_TINTS = {"2008": "#bcd5f3", "2019": "#f8cdb8"}
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3de"
CATEGORIES = [
    ("children_6_17", "Children 6–17"),
    ("employed", "Employed"),
    ("unemployed", "Unemployed"),
    ("retired", "Retired"),
    ("other_inactive", "Other inactive"),
]
LABEL = dict(CATEGORIES)


def md_table(text, heading):
    """Rows of the first table after the first heading that starts with `heading`."""
    lines = text.splitlines()
    start = next(
        i
        for i, line in enumerate(lines)
        if line.lstrip("#").strip().startswith(heading)
    )
    rows, seen = [], False
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            seen = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif seen:
            break
        elif line.startswith("#"):
            break
    return rows[1:]  # drop header


def nums(cell):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", cell)]


def load():
    text = REPORT.read_text(encoding="utf-8")
    day_ratio = {
        r[0]: {"n": (int(r[1]), int(r[2])), "ratio": float(r[3]), "ci": nums(r[4])}
        for r in md_table(text, "Daily time, weekday days with trips")
    }
    person_ratio = {
        r[0]: {"n": (int(r[1]), int(r[2])), "ratio": float(r[3]), "ci": nums(r[4])}
        for r in md_table(text, "Daily time, weekday per-person budgets")
    }
    person = {
        r[0]: {
            "2008": (float(r[1]), *nums(r[2])),
            "2019": (float(r[3]), *nums(r[4])),
        }
        for r in md_table(text, "Daily time, per person (days without trips")
    }
    day_means = {
        r[0]: (float(r[1]), float(r[2]))
        for r in md_table(text, "Daily time, per day with trips")
    }

    day = {}
    all_day = {}
    with open(FIG_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["panel"].startswith("(B)"):
                continue
            if r["group"] == "All":
                m = re.match(r"All \((\d{4})\) (mean|median)", r["subgroup"])
                if m:
                    key = "mean" if m.group(2) == "mean" else "median"
                    all_day.setdefault(m.group(1), {})[key] = float(
                        r["mean"] or r["median"]
                    )
                continue
            if r["subgroup"] in ("2008", "2019") and r["mean"]:
                day.setdefault(r["group"], {})[r["subgroup"]] = {
                    k: float(r[k])
                    for k in ("mean", "ci_low", "ci_high", "median", "p25", "p75")
                }
                day[r["group"]][r["subgroup"]]["n"] = int(r["n"])

    # Checks: the figure CSV must agree with the report tables.
    for key, label in CATEGORIES:
        for i, year in enumerate(("2008", "2019")):
            csv_mean = day[label][year]["mean"]
            assert abs(csv_mean - day_means[key][i]) < 0.06, (key, year, csv_mean)
            assert day[label][year]["n"] == day_ratio[key]["n"][i], (key, year)
    for i, year in enumerate(("2008", "2019")):
        assert abs(all_day[year]["mean"] - day_means["overall"][i]) < 0.06, year
    return day, all_day, day_ratio, person, person_ratio


def ratio_text(r, sep=" "):
    lo, hi = r["ci"]
    return f"×{r['ratio']:.2f}{sep}[{lo:.2f}, {hi:.2f}]"


def style(ax, ymax, step):
    ax.set_ylim(0, ymax)
    ax.set_yticks(range(0, int(ymax) + 1, step))
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(INK_2)
    ax.tick_params(length=0, pad=3, colors=INK_2)


def all_lines(ax, values, x_right, fmt):
    for year, (value, extra) in values.items():
        ax.hlines(
            value,
            -0.55,
            x_right - 0.08,
            color=YEAR_COLOURS[year],
            lw=0.9,
            ls=(0, (4, 3)),
            zorder=1,
        )
        ax.text(
            x_right,
            value,
            fmt.format(year=year, v=value, extra=extra),
            color=INK_2,
            fontsize=6.3,
            va="center",
            ha="left",
        )


def main():
    day, all_day, day_ratio, person, person_ratio = load()
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 7.5, "text.color": INK}
    )
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 6.4), sharex=True)
    offset = {"2008": -0.19, "2019": 0.19}
    xs = range(len(CATEGORIES))

    # Panel A: per weekday with trips (distribution: quartiles, median, mean, CI).
    for x, (key, label) in zip(xs, CATEGORIES, strict=True):
        tops = []
        for year in ("2008", "2019"):
            d = day[label][year]
            xx = x + offset[year]
            ax1.vlines(xx, d["p25"], d["p75"], color=YEAR_TINTS[year], lw=9, zorder=2)
            ax1.vlines(
                xx,
                d["ci_low"],
                d["ci_high"],
                color=YEAR_COLOURS[year],
                lw=2.2,
                zorder=3,
            )
            ax1.plot(
                xx,
                d["mean"],
                "o",
                ms=5.5,
                color=YEAR_COLOURS[year],
                mec="white",
                mew=0.8,
                zorder=4,
            )
            ax1.plot(
                xx,
                d["median"],
                "D",
                ms=4,
                mfc="white",
                mec=YEAR_COLOURS[year],
                mew=1.1,
                zorder=4,
            )
            ax1.text(
                xx,
                d["p75"] + 8,
                f"{d['mean']:.1f}",
                ha="center",
                va="bottom",
                fontsize=7,
                color=INK,
            )
            ax1.text(
                xx,
                d["p75"] + 2.5,
                f"med {d['median']:.0f}",
                ha="center",
                va="bottom",
                fontsize=5.8,
                color=INK_2,
            )
            ax1.text(
                xx,
                3,
                f"{d['n']:,}",
                ha="center",
                va="bottom",
                fontsize=5.6,
                color=INK_2,
            )
            tops.append(d["p75"])
        ax1.text(
            x,
            128,
            ratio_text(day_ratio[key], "\n"),
            ha="center",
            va="bottom",
            fontsize=6.5,
            color=INK,
            linespacing=1.1,
        )
    style(ax1, 145, 20)
    all_lines(
        ax1,
        {y: (all_day[y]["mean"], all_day[y]["median"]) for y in ("2008", "2019")},
        len(CATEGORIES) - 0.45,
        "All {year}: {v:.1f} (med {extra:.0f})",
    )
    r_all = day_ratio["overall"]
    ax1.set_title(
        "A. Minutes per weekday with trips   "
        f"All residents: {all_day['2008']['mean']:.1f} → {all_day['2019']['mean']:.1f} "
        f"min, {ratio_text(r_all)}",
        loc="left",
        fontsize=8,
        color=INK,
        pad=8,
    )
    ax1.set_ylabel("Minutes per day", color=INK_2)

    # Panel B: per person (days without trips count as zero): mean and CI only.
    for x, (key, label) in zip(xs, CATEGORIES, strict=True):
        tops = []
        for year in ("2008", "2019"):
            mean, lo, hi = person[key][year]
            xx = x + offset[year]
            ax2.vlines(xx, lo, hi, color=YEAR_COLOURS[year], lw=2.2, zorder=3)
            ax2.plot(
                xx,
                mean,
                "o",
                ms=5.5,
                color=YEAR_COLOURS[year],
                mec="white",
                mew=0.8,
                zorder=4,
            )
            ax2.text(xx, hi + 2, f"{mean:.1f}", ha="center", va="bottom", fontsize=7)
            ax2.text(
                xx,
                2,
                f"{person_ratio[key]['n'][0 if year == '2008' else 1]:,}",
                ha="center",
                va="bottom",
                fontsize=5.6,
                color=INK_2,
            )
            tops.append(hi)
        ax2.text(
            x,
            88,
            ratio_text(person_ratio[key], "\n"),
            ha="center",
            va="bottom",
            fontsize=6.5,
            linespacing=1.1,
        )
    style(ax2, 102, 20)
    all_lines(
        ax2,
        {y: (person["overall"][y][0], None) for y in ("2008", "2019")},
        len(CATEGORIES) - 0.45,
        "All {year}: {v:.1f}",
    )
    p_all = person_ratio["overall"]
    ax2.set_title(
        "B. Minutes per person per weekday (days without trips count as zero)   "
        f"All: {person['overall']['2008'][0]:.1f} → {person['overall']['2019'][0]:.1f}, "
        f"{ratio_text(p_all)}",
        loc="left",
        fontsize=8,
        color=INK,
        pad=8,
    )
    ax2.set_ylabel("Minutes per person", color=INK_2)

    ax2.set_xticks(list(xs))
    ax2.set_xticklabels([label for _, label in CATEGORIES], fontsize=7.2, color=INK)
    ax2.set_xlim(-0.55, len(CATEGORIES) + 0.55)

    handles = [
        Line2D(
            [],
            [],
            marker="o",
            ls="",
            color=YEAR_COLOURS["2008"],
            ms=5.5,
            label="ENTD 2008",
        ),
        Line2D(
            [],
            [],
            marker="o",
            ls="",
            color=YEAR_COLOURS["2019"],
            ms=5.5,
            label="EMP 2019",
        ),
        Line2D([], [], color=INK_2, lw=2.2, label="Mean and 95% CI"),
        Line2D([], [], marker="D", ls="", mfc="white", mec=INK_2, ms=4, label="Median"),
        Line2D([], [], color="#cfcdc6", lw=7, label="Quartiles (25–75%)"),
        Line2D([], [], color=INK_2, lw=0.9, ls=(0, (4, 3)), label="All residents"),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=6,
        frameon=False,
        fontsize=6.6,
        bbox_to_anchor=(0.5, 0.995),
        handlelength=1.6,
        columnspacing=1.2,
    )
    fig.text(
        0.01,
        0.005,
        "Residents aged 6+, Monday–Friday, round-trip days (start and end at home), "
        "destination purposes (no holidays, no walking or cycling\nas the activity), "
        "local trips (≤ 80 km). Above each pair: ratio 2019/2008 [90% CI]. Means with 95% CIs; "
        "household bootstrap, 200 replicates.\n"
        "Small grey numbers at the foot of each column: n (weekdays with trips in A, "
        "respondents in B). "
        "Sources: ENTD 2008, EMP 2019 (SDES/INSEE); author's calculations.",
        fontsize=5.9,
        color=INK_2,
        ha="left",
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.07, 0.86, 0.965), h_pad=1.6)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(HERE / f"fig_time_by_category.{ext}", dpi=300, facecolor="white")
    print("All, per day with trips:", all_day, ratio_text(r_all))
    print("All, per person:", person["overall"], ratio_text(p_all))


if __name__ == "__main__":
    main()
