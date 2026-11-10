"""Article figures from the step 12 report (docs/data/step12_variation.md).

Usage: python fig_article_step12.py [path/to/step12_variation.md]
Writes, next to this script:
  fig_ratio_2008_2019.{png,pdf,svg}       2019/2008 daily-time ratios (B2, B6.5)
  fig_measurement_bridge.{png,pdf,svg}    observed change -> measurement-corrected
                                          behavioural change (C4, B2)
Only aggregate tables of the report are read; nothing else is needed.
"""

# ruff: noqa: E501  (long caption strings)

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DEFAULT_REPORT = HERE.parents[1] / "data" / "step12_variation.md"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
SERIES = "#2a78d6"  # reference palette slot 1 (validated, light mode)
BAND_15, BAND_10 = "#eef4fc", "#dbe8f9"
NUM = r"-?\d+(?:\.\d+)?"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "text.color": INK,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK_2,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
    }
)


def section(text: str, title: str) -> list[list[str]]:
    """Rows (cells) of the first Markdown table after a heading starting with `title`."""
    lines = text.splitlines()
    start = next(
        i for i, ln in enumerate(lines) if ln.lstrip("#").strip().startswith(title)
    )
    rows, in_table = [], False
    for ln in lines[start + 1 :]:
        if ln.startswith("|"):
            in_table = True
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif in_table:
            break
    return rows


def interval(cell: str) -> tuple[float, float]:
    lo, hi = re.findall(NUM, cell)[:2]
    return float(lo), float(hi)


def save(fig, name: str) -> None:
    for ext in ("png", "pdf", "svg"):
        fig.savefig(HERE / f"{name}.{ext}", facecolor="white", dpi=300)


def style(ax) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


LABELS = {
    "overall": "All residents",
    "children_6_17": "Children 6-17",
    "employed": "Employed",
    "unemployed": "Unemployed",
    "retired": "Retired",
    "other_inactive": "Other inactive",
    "dense": "Dense",
    "intermediate": "Intermediate",
    "sparse": "Sparse",
    "very_sparse": "Very sparse",
}


def ratio_figure(text: str) -> None:
    b2 = section(text, "B2. Trips x distance x speed")
    head = b2[0]
    i_r, i_ci, i_15 = (
        head.index("Time ratio 2019/2008"),
        head.index("90% CI"),
        head.index("Equivalent at ±15%"),
    )
    rows = [
        (LABELS[r[0]], float(r[i_r]), interval(r[i_ci]), r[i_15])
        for r in b2[1:]
        if r[0] in LABELS
    ]
    b65 = section(text, "B6.5. 2008 -> 2019 by INSEE density grid")
    h = b65[0]
    j_r, j_ci, j_15 = (
        h.index("Time ratio 2019/2008"),
        h.index("90% CI"),
        h.index("Equivalent at ±15%"),
    )
    dens = [
        (LABELS[r[0]] + " areas", float(r[j_r]), interval(r[j_ci]), r[j_15])
        for r in b65[1:]
        if r[1] == "all categories" and r[2].startswith("time")
    ]
    groups = [("By population category", rows), ("By density of residence", dens)]

    labels, ys, y = [], [], 0.0
    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.axvspan(0.85, 1.15, color=BAND_15, zorder=0)
    ax.axvspan(0.90, 1.10, color=BAND_10, zorder=0)
    ax.axvline(1.0, color=INK_2, lw=0.8, zorder=1)
    for gname, items in groups:
        ax.text(
            0.705, y, gname, fontsize=8, color=INK_2, fontweight="bold", va="center"
        )
        y += 1
        for lab, r, (lo, hi), verdict in items:
            filled = verdict == "equivalent"
            ax.plot(
                [lo, hi], [y, y], color=SERIES, lw=2, solid_capstyle="round", zorder=3
            )
            ax.plot(
                r,
                y,
                "o",
                ms=6,
                color=SERIES if filled else "white",
                markeredgecolor=SERIES,
                markeredgewidth=1.5,
                zorder=4,
            )
            ax.text(
                1.42,
                y,
                f"{r:.3f} [{lo:.3f}, {hi:.3f}]  {verdict}",
                fontsize=7,
                color=INK,
                va="center",
            )
            labels.append(lab)
            ys.append(y)
            y += 1
        y += 0.4
    ax.set_yticks(ys, labels)
    ax.set_ylim(y - 0.6, -0.8)
    ax.set_xlim(0.70, 1.40)
    ax.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2, 1.3])
    ax.set_xlabel(
        "Daily travel time per weekday with trips, ratio 2019 / 2008 (90% CI)"
    )
    style(ax)
    ax.text(
        1.42,
        -0.8,
        "Ratio [90% CI], verdict at ±15%",
        fontsize=7,
        color=INK_2,
        va="center",
    )
    fig.text(
        0.01,
        0.01,
        "Shaded: ±10% (dark) and ±15% (light) equivalence margins. Filled dot: interval inside ±15%"
        " (equivalent);\nopen dot: inconclusive. Residents 6+, weekdays with trips; round-trip days,"
        " destination purposes, local trips (≤ 80 km);\nharmonised motives, day weights;"
        " household bootstrap. Sources: ENTD 2008, EMP 2019.",
        fontsize=6.5,
        color=INK_2,
    )
    fig.tight_layout(rect=(0, 0.10, 0.80, 1))
    save(fig, "fig_ratio_2008_2019")


def bridge_figure(text: str) -> None:
    led = section(text, "C4. Measurement ledger")
    keep = {
        "a.": "Duration rounding",
        "b.": "Recall lag (EMP)",
        "e.": "Short trips missing in 2019",
        "f.": "Calendar mix",
        "g.": "Population composition",
    }
    effects = []
    for r in led[1:]:
        key = r[0][:2]
        if key not in keep:
            continue
        groups = [interval(g) for g in r[4].split(";")]
        points = []
        for k, cell in enumerate(r[1:4]):
            nums = [float(x) for x in re.findall(NUM, cell)]
            lo, hi = groups[k]
            points.append((nums[0] if len(nums) == 1 else (lo + hi) / 2, lo, hi))
        effects.append((keep[key], points))
    obs = section(text, "Residual change")[1]
    observed = [float(x) for x in obs[1:4]]
    b2 = section(text, "B2. Trips x distance x speed")
    head = b2[0]
    t_ci = interval(b2[1][head.index("Δ (min) [CI]")].split("[", 1)[1])

    # Behavioural, measurement-corrected change = observed - sum(effects); ranges combine extremes.
    resid = []
    for k in range(3):
        mid = observed[k] - sum(p[k][0] for _, p in effects)
        lo = observed[k] - sum(p[k][2] for _, p in effects)
        hi = observed[k] - sum(p[k][1] for _, p in effects)
        resid.append((mid, lo, hi))

    titles = ["Daily time (min/day)", "Trips per day", "Minutes per trip"]
    rows = (
        ["Observed change 2008 to 2019"]
        + [f"minus: {n}" for n, _ in effects]
        + ["= Behavioural change, measurement-corrected"]
    )
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.3), sharey=True)
    for k, ax in enumerate(axes):
        ax.axvline(0, color=INK_2, lw=0.8)
        vals = [(observed[k], *(t_ci if k == 0 else (observed[k], observed[k])))]
        vals += [p[k] for _, p in effects]
        vals += [resid[k]]
        for y, (m, lo, hi) in enumerate(vals):
            result = y in (0, len(vals) - 1)
            col = INK if result else SERIES
            if hi > lo:
                ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
            ax.plot(
                m,
                y,
                "D" if result else "o",
                ms=5.5,
                color=col,
                markeredgewidth=0,
                zorder=3,
            )
            fmt = "{:+.2f}" if k == 1 else "{:+.1f}"
            ax.annotate(
                fmt.format(m),
                (max(m, hi), y),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=6.5,
                color=INK,
            )
        ax.set_title(titles[k], fontsize=8.5, loc="left", color=INK)
        style(ax)
        lo_all = min(v[1] for v in vals)
        hi_all = max(v[2] for v in vals)
        pad = 0.25 * (hi_all - lo_all)
        ax.set_xlim(lo_all - 0.15 * pad, hi_all + pad)
    axes[0].set_yticks(range(len(rows)), rows)
    axes[0].set_ylim(len(rows) - 0.5, -0.5)
    fig.text(
        0.01,
        0.01,
        "Effects are on the measured 2008-2019 change (positive = raises the measured 2019 value);"
        " the corrected change removes them.\n"
        "Observed CI shown for daily time only (B2). Rounding: bounds from simulation (nearest vs"
        " round-up); other rows: 95% household-bootstrap CIs.\n"
        "The corrected range combines the extremes of all rows. The short-trip row assumes the whole"
        " fall in trips under 5 min is measurement (an upper bound).\n"
        "Residents 6+, weekdays with trips; round-trip days, destination purposes, local trips"
        " (≤ 80 km); harmonised motives. Sources: ENTD 2008, EMP 2019.",
        fontsize=6.3,
        color=INK_2,
    )
    fig.tight_layout(rect=(0, 0.17, 1, 1), w_pad=1.2)
    save(fig, "fig_measurement_bridge")
    for t, (m, lo, hi), o in zip(titles, resid, observed):
        print(f"{t}: observed {o:+.3f} -> corrected {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")


if __name__ == "__main__":
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REPORT
    txt = report.read_text(encoding="utf-8")
    ratio_figure(txt)
    bridge_figure(txt)
