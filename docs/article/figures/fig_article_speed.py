"""Speed and time-decomposition figures for the article, read from the step 12 report.

    python fig_article_speed.py [path/to/step12_variation.md]

Default report path: docs/data/step12_variation.md, two folders above this file.
Writes, next to this file (png, pdf, svg):
- fig_speed_class: km per trip, minutes per trip and km/h by residence class,
  1994 (published), 2008 and 2019 (SDES scope, producer distances; C6);
- fig_time_decomposition: where the extra minutes per day come from, by crow-fly
  distance band, with 2019 distances as published and rounded to whole km as in
  2008 (B4b crow-fly and the whole-kilometre sensitivity);
- fig_speed_checks: the car-driver speed ratio 2019/2008 at constant distance and
  density under each check, and the 80 km/h before/after test (C6);
- fig_car_speed_bands: car-driver speed ratio by crow-fly band and density (C6).
Every number printed comes from the report's tables.
"""

# ruff: noqa: E501  (long caption strings)

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
REPORT = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE.parents[1] / "data" / "step12_variation.md"
)

C2008, C2019, C1994 = "#2a78d6", "#eb6834", "#52514e"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
LIGHT = "#c9c7c0"
ORDINAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # dense -> very sparse
NUM = r"-?\d+(?:\.\d+)?"
FOOT = "Sources: ENTD 2008, EMP 2019 (SDES/INSEE), ETC 1994 (INSEE); author's calculations."


def tables_after(text: str, title: str) -> list[list[list[str]]]:
    """All Markdown tables between the heading starting with `title` and the next heading."""
    lines = text.splitlines()
    start = next(
        i for i, ln in enumerate(lines) if ln.lstrip("#").strip().startswith(title)
    )
    tables, rows = [], []
    for ln in lines[start + 1 :]:
        if ln.startswith("#"):
            break
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif rows:
            tables.append(rows)
            rows = []
    if rows:
        tables.append(rows)
    return tables


def est(cell: str) -> tuple[float, float, float] | None:
    """'0.91 [0.89, 0.94]' -> (0.91, 0.89, 0.94); a lone number -> (x, nan, nan); '-' -> None."""
    nums = [float(x) for x in re.findall(NUM, cell)]
    if not nums:
        return None
    if len(nums) >= 3:
        return nums[0], nums[1], nums[2]
    return nums[0], float("nan"), float("nan")


def col(header: list[str], start: str) -> int:
    return next(i for i, h in enumerate(header) if h.startswith(start))


def base_style(ax, grid_axis="x"):
    ax.grid(axis=grid_axis, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(INK_2)
    ax.tick_params(length=0, colors=INK_2, labelsize=7)


def save(fig, name):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig_speed_class(text):
    table = tables_after(text, "Speed by residence class")[0]
    h = table[0]
    classes = [
        ("All", "All residents"),
        ("pôle", "Urban core (pôle)"),
        ("couronne", "Commuter belt (couronne)"),
        ("hors attraction", "Outside urban areas"),
    ]
    rows = {
        r[h.index("Residence class")]: r
        for r in table[1:]
        if r[h.index("Scope")] == "A" and r[h.index("Distance")] == "producer"
    }
    panels = [
        ("km per trip", "km/trip", 0, "{:.1f}"),
        ("minutes per trip", "min/trip", 1, "{:.1f}"),
        ("km/h (door to door)", "km/h", 2, "{:.1f}"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.1), sharey=True)
    for ax, (title, key, k94, fmt) in zip(axes, panels, strict=True):
        i08 = col(h, f"2008 {key}")
        i19 = col(h, f"2019 {key}")
        iratio = col(h, "speed ratio" if key == "km/h" else f"{key} ratio")
        xmax = 0
        for y, (cls, _) in enumerate(classes):
            r = rows[cls]
            pub = [float(x) for x in re.findall(NUM, r[-1])]
            yy = len(classes) - 1 - y
            v94 = pub[k94]
            ax.plot(v94, yy + 0.25, "D", ms=4, mfc="white", mec=C1994, mew=1.1)
            ax.text(
                v94,
                yy + 0.25,
                "  " + fmt.format(v94),
                va="center",
                fontsize=6,
                color=INK_2,
            )
            for off, idx, colour in ((0.0, i08, C2008), (-0.25, i19, C2019)):
                m, lo, hi = est(r[idx])
                ax.hlines(yy + off, lo, hi, color=colour, lw=1.8)
                ax.plot(m, yy + off, "o", ms=4.5, color=colour, mec="white", mew=0.6)
                ax.text(
                    hi,
                    yy + off,
                    "  " + fmt.format(m),
                    va="center",
                    fontsize=6.3,
                    color=INK,
                )
                xmax = max(xmax, hi, v94)
            ratio = est(r[iratio])
            ax.text(
                0.0,
                yy - 0.47,
                f"2019/2008 ×{ratio[0]:.2f} [{ratio[1]:.2f}, {ratio[2]:.2f}]",
                fontsize=5.8,
                color=INK_2,
                va="center",
                transform=ax.get_yaxis_transform(),
            )
        ax.set_xlim(0, xmax * 1.32)
        ax.set_title(title, fontsize=8, loc="left", color=INK)
        base_style(ax)
    axes[0].set_yticks(range(len(classes)))
    axes[0].set_yticklabels([lab for _, lab in classes][::-1], fontsize=7, color=INK)
    axes[0].set_ylim(-0.75, len(classes) - 0.45)
    handles = [
        Line2D(
            [],
            [],
            marker="D",
            ls="",
            mfc="white",
            mec=C1994,
            ms=4,
            label="1994 (published)",
        ),
        Line2D([], [], marker="o", color=C2008, ms=4.5, label="ENTD 2008"),
        Line2D([], [], marker="o", color=C2019, ms=4.5, label="EMP 2019"),
    ]
    fig.legend(
        handles=handles,
        loc="upper left",
        ncol=3,
        frameon=False,
        fontsize=6.8,
        bbox_to_anchor=(0.005, 0.95),
    )
    fig.suptitle(
        "Trip length, duration and speed by place of residence, 1994–2008–2019",
        x=0.01,
        ha="left",
        fontsize=8.5,
        color=INK,
        y=0.985,
    )
    fig.text(
        0.01,
        0.01,
        "Residents aged 6+, Monday–Friday, local trips (≤ 80 km), all purposes (SDES scope); producer distances "
        "(2008: corrected declared; 2019: consolidated).\nMeans of weighted totals with 95% CIs; ratios with 90% CIs; "
        "household bootstrap. 1994: published INSEE values, the survey's own measures.\n"
        + FOOT,
        fontsize=5.6,
        color=INK_2,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.1, 1, 0.9), w_pad=0.8)
    save(fig, "fig_speed_class")


# ---------------------------------------------------------------------------
def fig_time_decomposition(text):
    t_terms, t_bands = tables_after(text, "crow-fly: B4b distance-band shift-share")[:2]
    terms = {r[0]: est(r[1]) + (est(r[2]) or (0, 0)) for r in t_terms[1:]}
    terms = {
        k: (v[0], *est(r[2])[:2])
        for k, v, r in ((r[0], est(r[1]), r) for r in t_terms[1:])
    }
    hb = t_bands[0]
    bands = {r[0]: r for r in t_bands[1:]}
    i_within, i_km, i_speed = (
        col(hb, "within (min)"),
        col(hb, "of which km/trip"),
        col(hb, "of which speed"),
    )

    def num(cell):
        v = est(cell)
        return 0.0 if v is None else v[0]

    same_commune = num(bands["0-1 km"][i_within])
    km_cur = sum(num(r[i_km]) for b, r in bands.items() if b != "0-1 km")
    sp_cur = sum(num(r[i_speed]) for b, r in bands.items() if b != "0-1 km")
    mix_cur = terms["band mix"][0]

    wk_ratio, wk_bands = tables_after(text, "Whole-kilometre crow-fly sensitivity")[:2]
    hw = wk_bands[0]
    mix_r = sum(num(r[col(hw, "Mix rounded")]) for r in wk_bands[1:])
    km_r = sum(num(r[col(hw, "Km rounded")]) for r in wk_bands[1:])
    sp_r = sum(num(r[col(hw, "Speed rounded")]) for r in wk_bands[1:])
    mix_c2 = sum(num(r[col(hw, "Mix current")]) for r in wk_bands[1:])
    assert abs(mix_c2 - mix_cur) < 0.06, (mix_c2, mix_cur)

    volume = terms["trips volume"][0]
    inter = terms["interaction"][0]
    total = terms["ΔT"][0]
    rows = [
        ("Fewer trips per day", volume, volume),
        ("More trips in longer distance bands", mix_cur, mix_r),
        ("Longer trips within the same band", km_cur, km_r),
        ("Slower trips within the same band", sp_cur, sp_r),
        (
            "Same-commune trips take longer\n(no distance: length or speed?)",
            same_commune,
            same_commune,
        ),
        ("Interaction", inter, inter),
    ]
    sum_cur = sum(r[1] for r in rows)
    sum_r = sum(r[2] for r in rows)
    rows.append(("Total change, minutes per day with trips", total, total))

    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    n = len(rows)
    for i, (label, cur, rnd) in enumerate(rows):
        y = n - 1 - i
        bold = i == n - 1
        ax.barh(y + 0.18, cur, height=0.32, color=LIGHT, zorder=2)
        ax.barh(y - 0.18, rnd, height=0.32, color=INK_2 if not bold else INK, zorder=2)
        for yy, v in ((y + 0.18, cur), (y - 0.18, rnd)):
            ax.text(
                v + (0.12 if v >= 0 else -0.12),
                yy,
                f"{v:+.1f}",
                va="center",
                ha="left" if v >= 0 else "right",
                fontsize=6.6,
                color=INK,
            )
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=7, color=INK)
    ax.set_xlabel(
        "Contribution to the 2008 → 2019 change (minutes per day with trips)",
        fontsize=7,
        color=INK_2,
    )
    lo = min(min(r[1], r[2]) for r in rows)
    hi = max(max(r[1], r[2]) for r in rows)
    ax.set_xlim(lo - 1.2, hi + 1.4)
    base_style(ax)
    handles = [
        plt.Rectangle(
            (0, 0),
            1,
            1,
            color=LIGHT,
            label="2019 crow-fly distances as published (continuous)",
        ),
        plt.Rectangle(
            (0, 0),
            1,
            1,
            color=INK_2,
            label="2019 distances rounded to whole km, as in 2008",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=False,
        fontsize=6.6,
        bbox_to_anchor=(1.0, 1.0),
    )
    ax.set_title(
        f"Where the extra {total:.1f} minutes per day with trips come from",
        loc="left",
        fontsize=8.5,
        color=INK,
    )
    fig.text(
        0.01,
        0.01,
        "Residents 6+, weekdays with trips; round-trip days, destination purposes, local trips (≤ 80 km). "
        "Shift-share by crow-fly distance band;\n"
        f"components sum to {sum_cur:+.1f} (published) and {sum_r:+.1f} (rounded) "
        f"against {total:+.1f} observed. ENTD 2008 crow-fly distances are whole kilometres between commune town halls;\n"
        "rounding EMP 2019 the same way removes the apparent lengthening within bands. "
        + FOOT,
        fontsize=5.6,
        color=INK_2,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    save(fig, "fig_time_decomposition")
    return {
        "published": (volume, mix_cur, km_cur, sp_cur, same_commune, inter),
        "rounded": (volume, mix_r, km_r, sp_r, same_commune, inter),
    }


# ---------------------------------------------------------------------------
def fig_speed_checks(text):
    pooled = tables_after(text, "Car-driver speed pooled at the 2008 trip mix")[0]
    recall = tables_after(text, "Recall lag and the standardized car-driver ratio")[0]
    clock = tables_after(text, "Speed by clock-time rounding")[0]
    whole = tables_after(text, "Whole-kilometre crow-fly sensitivity")[0]
    modes = tables_after(text, "All-mode speed with the mode mix held constant")[0]
    limit = tables_after(text, "80 km/h limit (1 July 2018)")[0]

    def last(table, pred, colname):
        h = table[0]
        r = next(r for r in table[1:] if pred(r))
        return est(r[col(h, colname)]), r

    departure = tables_after(text, "Car-driver speed by departure time")[0]
    tours = tables_after(text, "Simple vs chained trips")[0]

    def three(table, first, cols=("ratio", "ratio ci low", "ratio ci high")):
        h = table[0]
        r = next(r for r in table[1:] if r[0] == first)
        vals = []
        for c in cols:
            cell = r[h.index(c)]
            vals.append(float(cell) if re.fullmatch(NUM, cell) else float("nan"))
        return tuple(vals)

    left = [("Car drivers", None, None)]
    # Reference: the standardised ratio as printed with three decimals (recall-lag
    # table, all days); the pooled table rounds the same estimate to two.
    v, _ = last(recall, lambda r: r[0] == "all days", "2019/2008 ratio")
    v_pooled, _ = last(pooled, lambda r: True, "2019/2008 ratio")
    assert abs(v[0] - v_pooled[0]) < 0.006, (v, v_pooled)
    left.append(("All weekday car-driver trips (reference)", v, "ref"))
    try:
        ledger = tables_after(text, "C4. Measurement ledger")[0]
        hl_ = ledger[0]
        row_h = next(r for r in ledger[1:] if r[0].startswith("h."))
        with_rounds = float(
            re.findall(NUM, row_h[col(hl_, "Car-driver speed ratio")])[0]
        )
        left.append(
            (
                "Professional rounds kept (2019 includes stop time)",
                (with_rounds, float("nan"), float("nan")),
                None,
            )
        )
    except (StopIteration, IndexError):
        pass
    for lag, lab in (
        ("1 day", "Day described the next day"),
        ("2-3 days", "Described 2–3 days later"),
        ("4-7 days", "Described 4–7 days later"),
    ):
        v, _ = last(recall, lambda r, lag=lag: r[0] == lag, "2019/2008 ratio")
        left.append((lab, v, None))
    for sub, lab in (
        ("departure round", "Departure time at :00 or :30"),
        ("departure not round", "Departure time not at :00 or :30"),
        ("both endpoints not round", "Neither time at :00 or :30"),
        ("both endpoints precise", "Both times off 5-min marks"),
    ):
        v, _ = last(
            clock,
            lambda r, sub=sub: r[0] == "car_driver" and r[1] == sub,
            "Speed ratio",
        )
        left.append((lab, v, None))
    v, _ = last(whole, lambda r: r[0] == "rounded", "Speed ratio")
    left.append(("2019 distances rounded to whole km", v, None))
    v, _ = last(tours, lambda r: r[0] == "2 trips", "Ratio")
    left.append(("Simple home-based tours (2 trips)", v, None))
    left.append(("Car drivers by time of day", None, None))
    for period, lab in (
        ("Morning peak (07:00–09:29)", "Morning peak, 07:00–09:29"),
        ("Evening peak (16:30–19:29)", "Evening peak, 16:30–19:29"),
        ("Other hours", "Other hours"),
        ("Usual workplace: either peak", "Commutes in either peak"),
    ):
        left.append((lab, three(departure, period), None))
    left.append(("Other modes", None, None))
    for m, lab in (
        ("car_passenger", "Car passengers"),
        ("train", "Train"),
        ("urban_pt", "Urban public transport"),
        ("bike", "Bike"),
        ("walk", "Walking"),
    ):
        v, _ = last(modes, lambda r, m=m: r[0] == f"within {m}", "2019/2008 ratio")
        left.append((lab, v, None))
    left.append(("All modes", None, None))
    for key, lab in (
        ("as observed", "As observed"),
        ("2008 band x density mix", "At 2008 distance × density mix"),
        ("2008 mode x band x density mix", "Also at 2008 mode mix"),
    ):
        v, _ = last(modes, lambda r, key=key: r[0] == key, "2019/2008 ratio")
        left.append((lab, v, None))

    right = [("80 km/h limit", None, None)]
    hl = limit[0]
    for r in limit[1:]:
        check = (
            "Car, 10–80 km, outside dense areas"
            if r[0].startswith("main")
            else "Placebo: car, 2–10 km, dense"
        )
        lab = {
            "EMP 2019": "EMP 2019 (limit from 1 July 2018)",
            "ENTD 2008 (season control)": "ENTD 2008, same calendar split",
            "ratio of ratios (EMP / ENTD)": "Difference (EMP ÷ ENTD)",
        }[r[1]]
        if r[1] == "EMP 2019":
            right.append((check, None, None))
        right.append(
            (
                lab,
                est(r[col(hl, "after/before ratio")]),
                "ref" if r[1].startswith("ratio") else None,
            )
        )

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7.0, 8.6), gridspec_kw={"height_ratios": [len(left), len(right)]}
    )
    for ax, items, xlim in ((ax1, left, (0.80, 1.22)), (ax2, right, (0.80, 1.22))):
        n = len(items)
        for i, (lab, v, flag) in enumerate(items):
            y = n - 1 - i
            if v is None:
                ax.text(
                    -0.01,
                    y,
                    lab,
                    fontsize=7,
                    color=INK,
                    va="center",
                    ha="right",
                    fontweight="bold",
                    transform=ax.get_yaxis_transform(),
                )
                continue
            m, lo, hi = v
            if lo == lo and hi - lo < 0.001:  # degenerate interval: show the point only
                lo = hi = float("nan")
            colour = INK if flag == "ref" else INK_2
            if lo == lo:  # not nan
                ax.hlines(y, lo, hi, color=colour, lw=1.6)
            ax.plot(m, y, "o", ms=4.5, color=colour, mec="white", mew=0.6)
            ci = f" [{lo:.3f}, {hi:.3f}]" if lo == lo else ""
            ax.text(
                1.02,
                y,
                f"{m:.3f}{ci}",
                fontsize=6.4,
                color=INK,
                va="center",
                ha="left",
                transform=ax.get_yaxis_transform(),
            )
        ax.axvline(1.0, color=INK_2, lw=0.8, ls=(0, (3, 2)))
        ax.set_yticks([n - 1 - i for i, it in enumerate(items) if it[1] is not None])
        ax.set_yticklabels(
            [it[0] for it in items if it[1] is not None], fontsize=6.8, color=INK
        )
        ax.set_ylim(-0.7, n - 0.3)
        ax.set_xlim(*xlim)
        ax.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2])
        base_style(ax)
    ax1.set_xlabel("Speed ratio 2019/2008 [90% CI]", fontsize=7, color=INK_2)
    ax2.set_xlabel(
        "Speed ratio, days from 1 July / days before [90% CI]", fontsize=7, color=INK_2
    )
    ref_ratio = next(v for lab, v, flag in left if flag == "ref")[0]
    fig.suptitle(
        f"Car speed at constant distance fell by about {round((1 - ref_ratio) * 100)}%, whatever the check",
        x=0.01,
        ha="left",
        fontsize=8.5,
        color=INK,
        y=0.995,
    )
    fig.text(
        0.01,
        0.005,
        "Residents 6+, weekdays, round-trip days, destination purposes, local trips; door-to-door speed on crow-fly distance, "
        "2–80 km,\nstandardised to the 2008 trip mix of distance band × residence density. 80 km/h test: car-driver trips "
        "of 10–80 km by residents of\nintermediate, sparse or very sparse areas; EMP April days excluded (year unknown). "
        "Household bootstrap.\nNo interval shown: fewer than 95% valid draws, or a degenerate interval (2008 mode mix).\n"
        + FOOT,
        fontsize=5.6,
        color=INK_2,
        va="bottom",
    )
    fig.tight_layout(rect=(0.0, 0.07, 0.80, 0.975), h_pad=2.0)
    save(fig, "fig_speed_checks")


# ---------------------------------------------------------------------------
def fig_car_speed_bands(text):
    table = tables_after(text, "Car-driver speed by crow-fly band and INSEE density")[0]
    pooled = tables_after(text, "Car-driver speed pooled at the 2008 trip mix")[0]
    ref = est(pooled[1][col(pooled[0], "2019/2008 ratio")])
    h = table[0]
    bands = ["2-5 km", "5-10 km", "10-20 km", "20-40 km", "40-80 km"]
    dens = [
        ("dense", "Dense"),
        ("intermediate", "Intermediate"),
        ("sparse", "Sparse"),
        ("very_sparse", "Very sparse"),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    offs = [-0.27, -0.09, 0.09, 0.27]
    for bi, band in enumerate(bands):
        for (dk, _), off, colour in zip(dens, offs, ORDINAL, strict=True):
            r = next(r for r in table[1:] if r[0] == band and r[1] == dk)
            v = est(r[col(h, "2019/2008 speed ratio")])
            if v is None:
                ax.text(
                    bi + off,
                    0.66,
                    "n<50",
                    fontsize=5.2,
                    color=INK_2,
                    ha="center",
                    rotation=90,
                )
                continue
            m, lo, hi = v
            ax.vlines(bi + off, lo, hi, color=colour, lw=1.6)
            ax.plot(bi + off, m, "o", ms=4.5, color=colour, mec="white", mew=0.6)
            ax.text(
                bi + off,
                hi + 0.012,
                f"{m:.2f}",
                fontsize=5.6,
                color=INK,
                ha="center",
                va="bottom",
            )
    ax.axhline(1.0, color=INK_2, lw=0.8)
    ax.hlines(ref[0], -0.6, len(bands) - 0.55, color=INK, lw=0.9, ls=(0, (4, 3)))
    ax.text(
        len(bands) - 0.5,
        ref[0],
        f"  pooled at 2008 mix: {ref[0]:.2f} [{ref[1]:.2f}, {ref[2]:.2f}]",
        fontsize=6.2,
        color=INK,
        va="center",
        ha="left",
    )
    ax.set_xticks(range(len(bands)))
    ax.set_xticklabels([b.replace("-", "–") for b in bands], fontsize=7, color=INK)
    ax.set_xlabel("Crow-fly distance band", fontsize=7, color=INK_2)
    ax.set_ylabel("Car-driver speed 2019/2008", fontsize=7, color=INK_2)
    ax.set_xlim(-0.6, len(bands) + 1.2)
    ax.set_ylim(0.62, 1.32)
    base_style(ax, grid_axis="y")
    handles = [
        Line2D([], [], marker="o", ls="", color=c, ms=4.5, label=lab)
        for (_, lab), c in zip(dens, ORDINAL, strict=True)
    ]
    ax.legend(
        handles=handles,
        title="Residence density",
        title_fontsize=6.6,
        fontsize=6.6,
        frameon=False,
        loc="upper right",
    )
    ax.set_title(
        "Car-driver door-to-door speed, 2019 relative to 2008, by distance and density",
        loc="left",
        fontsize=8.5,
        color=INK,
    )
    fig.text(
        0.01,
        0.01,
        "Residents 6+, weekdays, round-trip days, destination purposes, local trips; speed = total crow-fly km / total minutes.\n"
        "Ratios with 90% CIs, household bootstrap; cells under 50 trips hidden. "
        + FOOT,
        fontsize=5.6,
        color=INK_2,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, "fig_car_speed_bands")


def main():
    text = REPORT.read_text(encoding="utf-8")
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    fig_speed_class(text)
    parts = fig_time_decomposition(text)
    fig_speed_checks(text)
    fig_car_speed_bands(text)
    labels = (
        "volume",
        "band mix",
        "within km",
        "within speed",
        "same commune",
        "interaction",
    )
    for k, v in parts.items():
        print(
            k,
            ", ".join(f"{a} {b:+.2f}" for a, b in zip(labels, v, strict=True)),
            f"= {sum(v):+.2f}",
        )


if __name__ == "__main__":
    main()
