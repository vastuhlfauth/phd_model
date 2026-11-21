# Supplement data, first batch (19 November 2026)

This answers the writing chat's five "data still to produce" items. Every number comes from the v9 reports, the scope-cube CSV or the Zahavi workbook. The scripts that computed them read only those files.

## 1. France 2019 daily distance and door-to-door speed: confirmed

| Source | 2008 | 2019 |
|---|---|---|
| Published: SDES/UTP tables | 25.2 km/day, 27.0 km/h (UTP note) | 26.54 km/day, 25.71 km/h (SDES table 2.2.1: 3.04055 trips × 8.72921 km; 3.04055 × 20.36964 = 61.93 min) |
| Microdata: speed (step 12 C6, scope A: 6+, Mon–Fri, local, all purposes, producer distance, 95% CI) | 26.87 [26.25, 27.44] km/h | 25.61 [25.09, 26.06] km/h |
| Microdata: minutes per person (scope cube, `alldays-allpurp-local`, per person, 95% CI) | 56.41 [55.53, 57.75] | 61.93 [60.64, 63.42] |
| Microdata: daily km = minutes × speed / 60 (derived, no interval) | 25.26 | 26.44 |

- The published-table value and the microdata value differ by 0.4% in 2019.
- C6 speed uses trips with a known distance and a positive duration.
- Speed ratio 2019/2008 (C6): 0.95 [0.93, 0.98], 90% CI.
- **Wording:** "26.5 km per person-day at 25.7 km/h (SDES table 2.2.1; microdata replication 26.4 km and 25.6 [25.1, 26.1] km/h)."

## 2. Within-series range of daily time: `s1_long_series_ranges.csv`

Values from the workbook's "Chart long series" sheet:
- Swiss 2021 and Danish 2021–22 excluded as Covid-affected;
- England 2021–22 already absent from that sheet.

| Series | n | Years | Min–max (min/day) | Max/min | CV |
|---|---|---|---|---|---|
| France ENTD/EMP | 4 | 1982–2019 | 54.7–62.0 | 1.13 | 5.2% |
| England/GB NTS | 10 | 1965–2024 | 57.4–64.1 | 1.12 | 3.1% |
| Switzerland MZMV | 5 | 1994–2015 | 82.6–97.5 | 1.18 | 5.4% |
| Germany MiD | 4 | 2002–2023 | 76.0–85.0 | 1.12 | 4.3% |
| Netherlands CBS | 9 | 1985–2007 | 60.0–63.0 | 1.05 | 1.3% |
| Denmark TU | 4 | 2019–2025 | 55.2–58.0 | 1.05 | 2.0% |

- **Wording:** "within each series, the highest value is at most 18% above the lowest (5–13% for five of six), over spans of 6 to 59 years, while series means range from 57 to 91 minutes between countries."
- **Caveats to keep:** the series contain method breaks (Switzerland redefined waiting time; England moved from GB to England coverage, see item 5).

## 3. Within-series relation between daily time and speed: `s1_time_speed_elasticity.csv`

**Model:** log(minutes) = series fixed effect + b · log(door-to-door speed), on estimates with a distance.
- Zahavi predicts b ≈ 0: faster travel goes into distance, not saved time. Equivalently, the elasticity of distance with respect to speed is 1 + b ≈ 1.
- **Series:** one per country and source family (national, Eurostat harmonisation, Vilhelmson), so that scope changes between families don't drive the slope.
- **Interval:** 95% bootstrap resampling whole series (4,000 draws).

| Specification | Estimates | Series | b | 95% CI | Distance elasticity 1 + b |
|---|---|---|---|---|---|
| All families | 58 | 16 | 0.085 | [−0.34, 0.20] | 1.09 |
| National sources only | 45 | 10 | 0.109 | [−0.27, 0.31] | 1.11 |
| National, confidence A only | 43 | 9 | 0.104 | [−0.29, 0.27] | 1.10 |

**Exclusions** (`s1_rows_used_and_excluded.csv`):
- Covid years 2020–2022;
- the rows the workbook flags as under-recorded (Denmark 2001, Latvia 2003, Sweden 1994 and 1995);
- France 2019 uses the distance of item 1.

The two series with the largest speed ranges carry most of the information: France (19.1 → 26.9 km/h) and England/GB (16.9 → 30.2 km/h). Their own slopes are 0.15 and 0.12 (`s1_series_used.csv`).

**Wording:** "within national series, a 10% faster door-to-door speed goes with about 1% more daily travel time (elasticity 0.09, 95% CI −0.34 to 0.20, 58 estimates in 16 series): the gain is spent on distance."

## 4. Changes in minutes, with intervals: `s4_minute_changes_by_scope.csv`, `s4_switch_effects_minutes.csv`

**Change 2019 − 2008 for each scope**, per day with trips and per person:
- The interval is a normal approximation from the two surveys' independent 95% bootstrap intervals: SE = √(SE₂₀₀₈² + SE₂₀₁₉²), with SE = CI width / 3.92.
- Check: for the reference per day with trips it gives +5.2 [+3.4, +6.9]. The report's bootstrap interval is [+3.2, +6.9] (step 11 compare), so the approximation is close.

| Scope | Per day with trips | Per person |
|---|---|---|
| round-dest-local (reference) | +5.2 [+3.4, +6.9] | +5.1 [+3.4, +6.7] |
| alldays-allpurp-local (SDES) | +6.1 [+4.2, +8.0] | **+5.5 [+3.7, +7.3]** (56.4 → 61.9) |

The other six scopes are in the CSV.

**Switch effects in minutes** (from the reference, all residents):

| Switch | Effect on the change, per day with trips (min) | Effect on the ratio [90% CI] |
|---|---|---|
| Days: round → all days | −0.37 | −0.006 [−0.014, −0.000] |
| Purposes: dest → all purposes | +1.45 | +0.017 [+0.006, +0.028] |
| Distance: local → day table | −0.47 | −0.011 [−0.027, +0.003] |

- **Effect on the change** = the switch's effect on the 2019 level minus its effect on the 2008 level. Both level effects have paired 95% CIs in the CSV; their difference has no interval in the reports.
- Use the ratio column for inference.

## 5. NTS coverage

- **Survey coverage.** DfT, NTS 2024 notes and definitions: "From January 2013, the survey has covered England residents only", and trips within Great Britain by English residents are included.
- **Re-based series.** DfT's current table NTS0101 is titled "Trips, distance travelled and time taken: England, 1972 onwards". The time series has been re-based to England back to 1972; the 1965 survey predates it.
- **Reweighting.** The same notes say the 2002–2015 figures were reweighted after the 2016 experiment. They also say that combining 2020–2022 (telephone and knock-to-nudge modes) with other years "is not recommended".
- **Consequence for Figure S1:** the workbook mixes rows from different releases:
  - GB rows (1972/73, and 2000 and 2005 via Eurostat);
  - England rows (2002 onwards) from different DfT releases, some before the reweighting.
- **Fix:** rebuild the England series from one release of NTS0101, England 1972 onwards, time taken in hours per person per year → minutes per day. Keep 1965 as a separate, flagged point, and drop the Eurostat GB rows from the series.
- Download the ODS from the gov.uk page "NTS01: Average number of trips made and distance travelled" and attach it. The shell here cannot reach gov.uk files.

Sources:
- [NTS 2024 notes and definitions](https://www.gov.uk/government/statistics/national-travel-survey-2024/nts-2024-notes-and-definitions)
- [NTS01 tables (NTS0101)](https://www.gov.uk/government/statistical-data-sets/nts01-average-number-of-trips-made-and-distance-travelled)
- [NTS 2019 report](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/906276/national-travel-survey-2019.pdf)
