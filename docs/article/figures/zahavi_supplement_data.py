"""Data for the Zahavi supplement (items 2-4 of supplement_data_v1.md).

    python zahavi_supplement_data.py WORKBOOK.xlsx SCOPE_CUBE_ESTIMATES.csv OUTDIR

Reads the Zahavi workbook (Data and Chart long series sheets, cached formula
values) and docs/data/scope_cube/estimates.csv, and writes the CSVs:
s1_long_series_ranges, s1_time_speed_elasticity, s1_series_used,
s1_rows_used_and_excluded, s4_minute_changes_by_scope, s4_switch_effects_minutes.
"""

# ruff: noqa: E501  (long table cells)

import csv
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np
import openpyxl

FRANCE_2019_ID, FRANCE_2019_KM = 8, 26.54  # SDES table 2.2.1: 3.04055 x 8.72921
FLAGGED = {
    13: "Denmark 2001: workbook flags under-recording",
    40: "Latvia 2003: implausibly low",
    69: "Sweden 1994: under-reported after method switch",
    70: "Sweden 1995: under-reported after method switch",
    71: "Sweden 1995: under-reported after method switch",
}
COVID_LONG = {"Switzerland — MZMV": [2021], "Denmark — TU": [2021, 2022]}


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def long_series(wb, out):
    vals = [[c.value for c in r] for r in wb["Chart long series"].iter_rows()]
    names, rows = vals[3], []
    for j in range(0, 18, 3):
        pts = [
            (r[j], r[j + 1])
            for r in vals[5:]
            if len(r) > j + 1
            and isinstance(r[j], (int, float))
            and isinstance(r[j + 1], (int, float))
        ]
        ex = COVID_LONG.get(names[j], [])
        p = [(y, v) for y, v in pts if y not in ex]
        v = [x for _, x in p]
        mean = st.mean(v)
        rows.append([
            names[j], len(p), f"{p[0][0]:g}–{p[-1][0]:g}", round(min(v), 1),
            round(max(v), 1), round(max(v) - min(v), 1), round(max(v) / min(v), 3),
            round(mean, 1), round(100 * st.pstdev(v) / mean, 1),
            "; ".join(str(y) for y in ex) or "none",
        ])
    write(out / "s1_long_series_ranges.csv",
          ["series", "n_points", "years", "min_min_per_day", "max_min_per_day",
           "range_min", "max_over_min", "mean", "cv_pct", "excluded_covid_years"], rows)


def fixed_effects(d):
    d = [x for x in d if sum(z["series"] == x["series"] for z in d) >= 2]
    ser = sorted({x["series"] for x in d})
    y = np.log([x["minutes"] for x in d])
    xv = np.log([x["speed"] for x in d])
    yd, xd = y.copy(), xv.copy()
    for s in ser:
        idx = [i for i, x in enumerate(d) if x["series"] == s]
        yd[idx] -= y[idx].mean()
        xd[idx] -= xv[idx].mean()
    b = (xd @ yd) / (xd @ xd)
    res = yd - b * xd
    se = math.sqrt(res @ res / (len(d) - len(ser) - 1) / (xd @ xd))
    return b, se, d, ser


def cluster_bootstrap(d, draws=4000, seed=1):
    rng = np.random.default_rng(seed)
    ser = sorted({x["series"] for x in d})
    out = []
    for _ in range(draws):
        dd = []
        for k, s in enumerate(rng.choice(ser, len(ser), replace=True)):
            dd += [dict(x, series=f"{s}#{k}") for x in d if x["series"] == s]
        b = fixed_effects(dd)[0]
        if np.isfinite(b):
            out.append(b)
    return np.percentile(out, [2.5, 97.5])


def elasticity(wb, out):
    ws = wb["Data"]
    hdr = [c.value for c in ws[1]]
    rows = [dict(zip(hdr, [c.value for c in r])) for r in ws.iter_rows(min_row=2)]
    data, excluded = [], []
    for r in rows:
        if r["ID"] is None or r["Data type"] != "Travel survey":
            continue
        if r["Indicator"] != "Total daily travel time":
            continue
        m, s = r["Minutes per day"], r["Speed (km/h)"]
        if r["ID"] == FRANCE_2019_ID:
            s = FRANCE_2019_KM / (m / 60)
        if not isinstance(s, (int, float)):
            continue
        src = str(r["Source"])
        fam = "Eurostat" if src.startswith("Eurostat") else (
            "Vilhelmson" if "Vilhelmson" in src else "national")
        key, year = f"{r['Country']} ({fam})", r["Year (for plotting)"]
        if 2020 <= year <= 2022:
            excluded.append((r["ID"], key, year, "Covid years 2020-2022"))
        elif r["ID"] in FLAGGED:
            excluded.append((r["ID"], key, year, FLAGGED[r["ID"]]))
        else:
            data.append(dict(id=r["ID"], series=key, fam=fam, year=year, minutes=m,
                             speed=s, conf=r["Confidence"]))
    specs = {
        "All series (national, Eurostat and Vilhelmson families kept separate)": data,
        "National sources only": [x for x in data if x["fam"] == "national"],
        "National sources, confidence A only": [
            x for x in data if x["fam"] == "national" and x["conf"] == "A"],
    }
    res = []
    for name, d in specs.items():
        b, se, used, ser = fixed_effects(d)
        lo, hi = cluster_bootstrap(used)
        res.append([name, len(used), len(ser), round(b, 3), round(se, 3),
                    round(lo, 3), round(hi, 3), round(1 + b, 3)])
    write(out / "s1_time_speed_elasticity.csv",
          ["specification", "n_estimates", "n_series", "elasticity_time_wrt_speed",
           "ols_se", "cluster_bootstrap_95_low", "cluster_bootstrap_95_high",
           "implied_elasticity_distance_wrt_speed"], res)
    _, _, used, ser = fixed_effects(data)
    per = []
    for s in ser:
        pts = [x for x in used if x["series"] == s]
        slope = None
        if len(pts) >= 3:
            slope = round(float(np.polyfit(np.log([p["speed"] for p in pts]),
                                           np.log([p["minutes"] for p in pts]), 1)[0]), 3)
        yrs = sorted(p["year"] for p in pts)
        per.append([s, len(pts), f"{yrs[0]:g}–{yrs[-1]:g}",
                    round(min(p["speed"] for p in pts), 1), round(max(p["speed"] for p in pts), 1),
                    round(min(p["minutes"] for p in pts), 1), round(max(p["minutes"] for p in pts), 1),
                    slope])
    write(out / "s1_series_used.csv",
          ["series", "n", "years", "speed_min_kmh", "speed_max_kmh", "minutes_min",
           "minutes_max", "slope_log_minutes_on_log_speed (n>=3)"], per)
    used_ids = {x["id"] for x in used}
    listing = [[x["id"], x["series"], x["year"], round(x["minutes"], 1), round(x["speed"], 2),
                "used" if x["id"] in used_ids else "single point in its series"] for x in data]
    listing += [[e[0], e[1], e[2], "", "", "excluded: " + e[3]] for e in excluded]
    write(out / "s1_rows_used_and_excluded.csv",
          ["workbook_id", "series", "year", "minutes", "speed_kmh", "status"], listing)


def scope_changes(cube, out):
    rows = list(csv.DictReader(open(cube, encoding="utf-8")))
    lev = {(r["scope"], r["basis"], r["survey"][:4]): r for r in rows
           if r["category"] == "All" and r["indicator"] == "minutes_per_day"}
    order = ["round-dest-local", "round-dest-daytable", "round-allpurp-local",
             "round-allpurp-daytable", "alldays-dest-local", "alldays-dest-daytable",
             "alldays-allpurp-local", "alldays-allpurp-daytable"]
    res = []
    for s in order:
        for b, label in (("travel_day", "per day with trips"), ("person", "per person")):
            a, c = lev[(s, b, "ENTD")], lev[(s, b, "EMP ")]
            m8, l8, h8 = (float(a[k]) for k in ("mean", "ci_low", "ci_high"))
            m9, l9, h9 = (float(c[k]) for k in ("mean", "ci_low", "ci_high"))
            se = math.hypot((h8 - l8) / 3.92, (h9 - l9) / 3.92)
            d = m9 - m8
            res.append([s, label, a["n"], f"{m8:.1f} [{l8:.1f}, {h8:.1f}]", c["n"],
                        f"{m9:.1f} [{l9:.1f}, {h9:.1f}]", f"{d:+.1f}",
                        f"[{d - 1.96 * se:+.1f}, {d + 1.96 * se:+.1f}]"])
    write(out / "s4_minute_changes_by_scope.csv",
          ["scope", "basis", "n_2008", "2008_min_[95CI]", "n_2019", "2019_min_[95CI]",
           "change_min", "change_95CI_normal_approx"], res)
    names = {"alldays-dest-local": "days: round → alldays",
             "round-allpurp-local": "purposes: dest → allpurp",
             "round-dest-daytable": "distance: local → daytable"}
    res = []
    for s, lab in names.items():
        for b, label in (("travel_day", "per day with trips"), ("person", "per person")):
            d = {r["survey"][:4]: r for r in rows if r["scope"] == s and r["category"] == "All"
                 and r["indicator"] == "change_minutes_per_day" and r["basis"] == b}
            e, m = d["ENTD"], d["EMP "]

            def cell(r, k="mean", lo="ci_low", hi="ci_high", f="{:+.2f}"):
                return f"{f.format(float(r[k]))} [{f.format(float(r[lo]))}, {f.format(float(r[hi]))}]"

            res.append([lab, label, cell(e), cell(m),
                        f"{float(m['mean']) - float(e['mean']):+.2f}",
                        cell(m, "ratio", "ratio_ci_low", "ratio_ci_high", "{:+.4f}")])
    write(out / "s4_switch_effects_minutes.csv",
          ["switch_from_reference", "basis", "effect_on_2008_level_min_[95CI]",
           "effect_on_2019_level_min_[95CI]",
           "effect_on_change_min_(point; = 2019 effect - 2008 effect)",
           "effect_on_ratio_[90CI]"], res)


if __name__ == "__main__":
    workbook, cube, outdir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    outdir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.load_workbook(workbook, data_only=True)
    long_series(wb, outdir)
    elasticity(wb, outdir)
    scope_changes(cube, outdir)
