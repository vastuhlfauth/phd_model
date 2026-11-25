"""Article figures from the step 12 report (docs/data/step12_variation.md).

Usage: python fig_article_step12.py [path/to/step12_variation.md]
Writes, next to this script:
  fig_ratio_2008_2019.{png,pdf,svg}       2019/2008 daily-time ratios (B2, B6.5)
  fig_measurement_bridge.{png,pdf,svg}    observed change, measurement rows and the
                                          report's residual ranges (C4, B2)
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
    """Observed change, the measurement rows of the ledger, and the report's residual ranges.

    Rounding (row a) is a pair of bounds, not an estimate, so it is drawn as a bar
    without a point. The residuals are the report's own ranges ("Residual change"
    table): after rows a, b, e, f, then also after g (composition). They are
    sensitivity ranges, drawn as bars without a point.
    """
    led = section(text, "C4. Measurement ledger")
    names = {
        "a.": "Duration rounding (bounds)",
        "b.": "Recall lag (EMP)",
        "e.": "Short trips missing in 2019",
        "f.": "Calendar mix",
        "g.": "Population composition",
    }
    bounds_col = next(
        i for i, h in enumerate(led[0]) if h.startswith("Interval or bounds")
    )
    effects = {}
    for r in led[1:]:
        key = r[0][:2]
        if key not in names:
            continue
        groups = [interval(g) for g in r[bounds_col].split(";")]
        points = []
        for k, cell in enumerate(r[1:4]):
            nums = [float(x) for x in re.findall(NUM, cell)]
            lo, hi = groups[k]
            is_bounds = len(nums) != 1  # row a prints "[lo, hi]" in the effect cell
            points.append((None if is_bounds else nums[0], lo, hi))
        effects[key] = points
    res = section(text, "Residual change")
    observed = [float(x) for x in res[1][1:4]]
    resid_abef = [interval(c) for c in res[2][1:4]]
    resid_g = [interval(c) for c in res[3][1:4]]
    assert res[2][0].startswith("Residual (removing a, b, e, f)"), res[2][0]
    assert res[3][0].startswith("Residual (also removing g"), res[3][0]
    b2 = section(text, "B2. Trips x distance x speed")
    head = b2[0]
    t_ci = interval(b2[1][head.index("Δ (min) [CI]")].split("[", 1)[1])

    rows = [("Observed change 2008 → 2019", "obs", None)]
    rows += [(f"minus {names[k]}", "eff", k) for k in ("a.", "b.", "e.", "f.")]
    rows += [("= Residual after measurement rows a, b, e, f", "res", resid_abef)]
    rows += [(f"minus {names['g.']}", "eff", "g.")]
    rows += [("= Residual, also without composition", "res", resid_g)]

    titles = ["Daily time (min/day)", "Trips per day", "Minutes per trip"]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.6), sharey=True)
    for k, ax in enumerate(axes):
        ax.axvline(0, color=INK_2, lw=0.8)
        fmt = "{:+.2f}" if k == 1 else "{:+.1f}"
        span = []
        for y, (_, kind, ref) in enumerate(rows):
            if kind == "obs":
                m = observed[k]
                lo, hi = t_ci if k == 0 else (m, m)
                col, marker = INK, "D"
                label = fmt.format(m)
            elif kind == "eff":
                m, lo, hi = effects[ref][k]
                col, marker = SERIES, "o"
                label = (
                    fmt.format(m)
                    if m is not None
                    else f"[{fmt.format(lo)}, {fmt.format(hi)}]"
                )
            else:
                lo, hi = ref[k]
                m, col, marker = None, INK, None
                label = f"[{fmt.format(lo)}, {fmt.format(hi)}]"
            span += [lo, hi] + ([m] if m is not None else [])
            if hi > lo:
                ax.plot(
                    [lo, hi],
                    [y, y],
                    color=col,
                    lw=5 if kind == "res" else 2,
                    solid_capstyle="butt" if kind == "res" else "round",
                    alpha=0.55 if kind == "res" else 1,
                )
            if m is not None:
                ax.plot(m, y, marker, ms=5.5, color=col, markeredgewidth=0, zorder=3)
            ax.annotate(
                label,
                (max(hi, m if m is not None else hi), y),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=6.3,
                color=INK,
            )
        ax.set_title(titles[k], fontsize=8.5, loc="left", color=INK)
        style(ax)
        lo_all, hi_all = min(span), max(span)
        width = hi_all - lo_all
        ax.set_xlim(lo_all - 0.12 * width, hi_all + 0.95 * width)
    axes[0].set_yticks(range(len(rows)), [r[0] for r in rows])
    axes[0].set_ylim(len(rows) - 0.5, -0.5)
    fig.text(
        0.01,
        0.01,
        "Effects are on the measured 2008–2019 change (positive = raises the measured 2019 value). Observed: point and"
        " 95% CI (daily time, B2).\n"
        "Rounding: bounds from simulation (nearest vs round-up), not an estimate. Other rows: point and 95% household-bootstrap CI.\n"
        "Residuals (wide bars): the report's sensitivity ranges, observed change minus the extreme combinations of the rows"
        " removed; not CIs.\nThe short-trip row treats the whole fall in trips under 5 min as measurement (an upper bound)."
        " Residents 6+, weekdays with trips;\nround-trip days, destination purposes, local trips (≤ 80 km); harmonised"
        " motives. Sources: ENTD 2008, EMP 2019; author's calculations.",
        fontsize=6.0,
        color=INK_2,
    )
    fig.tight_layout(rect=(0, 0.2, 0.99, 1), w_pad=0.8)
    save(fig, "fig_measurement_bridge")
    for t, o, r1, r2 in zip(titles, observed, resid_abef, resid_g):
        print(f"{t}: observed {o:+.3f}; residual a,b,e,f {r1}; also g {r2}")


if __name__ == "__main__":
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REPORT
    txt = report.read_text(encoding="utf-8")
    ratio_figure(txt)
    bridge_figure(txt)
