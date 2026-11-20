# Daily travel time by household income

Weekdays, residents aged 6+; quintiles are relative within each year. ENTD uses bracket midpoint per consumption unit; EMP uses INSEE's imputed income decile re-cut under individual weights.

Residence density is the urban-unit-status × size proxy in both years. Household vehicles use the broad in-use definition (cars + VUL + camper vans), grouped 0, 1 and 2+.

### Household vehicle definitions

ENTD 2008 `Q_MENAGE.V1_JNBVEH + V1_JNBCCVUL` counts passenger cars, vans and camper vans in use. `JNBVEH`: « De combien de voitures particulières votre ménage dispose-t-il au total ? » `JNBCCVUL`: « De combien de camping-cars, fourgonnettes, ou véhicules utilitaires légers votre ménage dispose-t-il au total ? » Out-of-use vehicles are excluded by the questionnaire instructions. [ENTD questionnaire](https://www.statistiques.developpement-durable.gouv.fr/media/2309/download?inline).

EMP 2019 `Q_MENAGE.JNBVEH` includes cars, VUL and camper vans, including vehicles out of use (`JNBVHS = 1`). When public out-of-use counts are present, subtract `JNBVPHS + JNBCCHS + JNBVULHS`. `JNBVEH`: « De combien de voitures particulières, de véhicules utilitaires légers ou de camping-cars votre ménage dispose-t-il au total ? » A zero total remains zero; `JNBVHS` is not asked in that case. [EMP questionnaire](https://www.statistiques.developpement-durable.gouv.fr/sites/default/files/2022-07/questionnaire_emp2019.pdf).

## Household shares by vehicle class

Weighted by the household weights (`PONDV1` in ENTD; `pond_menC` in EMP). `n` is the unweighted number of households. Sources: ENTD `Q_MENAGE` and EMP `Q_MENAGE_public`; counts use the definitions above.

| Year | Class | n households | Share (%) |
|---:|:---|---:|---:|
| 2008 | 0 | 3297 | 19.09 |
| 2008 | 1 | 7872 | 44.66 |
| 2008 | 2+ | 9009 | 36.24 |
| 2008 | unknown | 0 | 0.00 |
| 2019 | 0 | 2255 | 19.95 |
| 2019 | 1 | 5722 | 44.91 |
| 2019 | 2+ | 5810 | 34.87 |
| 2019 | unknown | 38 | 0.28 |



Levels and gaps use 95% household-bootstrap intervals; cross-year ratios use 90% intervals. Individual survey household draws are independent, and shared across scopes and statistics. Per-person estimates include zero-trip people and subtract open-day weights.

Reweighting excludes unknown income and targets the average of each survey's joint income × density × vehicle-class distribution, separately for each estimation basis. Only cells with respondents in at least one year enter the joint grid. Within quintile, sparse cells pool 1 with 2+ at the same density, then sparse with very sparse at the same vehicle class. Remaining small cells merge with the closest cell, preferring the same density, then the same vehicle class, then the closest supported cell across both dimensions. The displayed destination is the retained label. Whole-quintile pooling is a last resort for cells with no common support. Still-small cells make that quintile unavailable. Bootstrap targets are rescaled over common support only when lost share is below 1%; each draw is recorded in reweighted.csv.

M0 includes income, population category and weekday; M1 adds density; M2 adds vehicle class. The pooled M2 model adds survey × quintile interactions. WLS models log travel-day minutes, so M2 Q5/Q1 is a conditional geometric ratio, not the arithmetic-mean gap. Nonpositive times are excluded. Regression confidence intervals are household-bootstrap 95%.

Cells under 50 respondents are hidden; density cells under 100 are flagged. Intervals need at least 95% valid draws.

## Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 596 |
| regression_M0 | 2019 | 13 | 0 | 0 | 502 |
| regression_M1 | 2008 | 16 | 0 | 0 | 596 |
| regression_M1 | 2019 | 16 | 0 | 0 | 502 |
| regression_M2 | 2008 | 18 | 0 | 0 | 596 |
| regression_M2 | 2019 | 18 | 0 | 0 | 502 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 23 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1779 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1290 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2256 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1628 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2430 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1635 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 502 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 14 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 47 | 0 | 0 | 70 |
| reweight_travel_day | 2019 | 47 | 0 | 0 | 50 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Levels and 2019/2008 ratios

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2256 | 59.795 | 57.273 | 62.225 | 1628 | 65.036 | 62.214 | 67.625 | 1.088 | 1.025 | 1.146 | equivalent | inconclusive |
| travel_day | q2 | 2369 | 60.292 | 57.766 | 63.048 | 1843 | 64.596 | 61.787 | 67.795 | 1.071 | 1.013 | 1.129 | equivalent | inconclusive |
| travel_day | q3 | 2743 | 62.480 | 59.943 | 65.347 | 1850 | 68.756 | 66.109 | 71.320 | 1.100 | 1.055 | 1.154 | inconclusive | inconclusive |
| travel_day | q4 | 2871 | 64.746 | 62.247 | 67.477 | 1990 | 69.645 | 67.019 | 72.431 | 1.076 | 1.021 | 1.125 | equivalent | inconclusive |
| travel_day | q5 | 3767 | 71.457 | 68.878 | 73.740 | 2107 | 76.301 | 73.483 | 78.676 | 1.068 | 1.020 | 1.111 | equivalent | inconclusive |
| person | q1 | 3359 | 44.527 | 42.284 | 46.704 | 2504 | 49.860 | 47.337 | 53.052 | 1.120 | 1.048 | 1.196 | inconclusive | inconclusive |
| person | q2 | 3159 | 48.101 | 45.678 | 50.230 | 2662 | 51.784 | 48.999 | 54.960 | 1.077 | 1.004 | 1.149 | equivalent | inconclusive |
| person | q3 | 3615 | 50.861 | 48.664 | 53.503 | 2742 | 55.771 | 53.008 | 59.135 | 1.097 | 1.032 | 1.164 | inconclusive | inconclusive |
| person | q4 | 3657 | 55.533 | 53.281 | 58.246 | 2885 | 60.422 | 57.380 | 63.387 | 1.088 | 1.018 | 1.151 | inconclusive | inconclusive |
| person | q5 | 4752 | 61.192 | 58.754 | 63.370 | 3032 | 67.546 | 64.195 | 70.958 | 1.104 | 1.052 | 1.166 | inconclusive | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Income gaps and their changes

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 11.663 | 7.524 | 15.378 | 11.265 | 7.018 | 14.901 | -0.398 | -6.766 | 4.923 |
| travel_day | ratio | 1.195 | 1.123 | 1.259 | 1.173 | 1.103 | 1.236 | -0.022 | -0.134 | 0.074 |
| person | difference | 16.665 | 13.098 | 19.841 | 17.685 | 13.331 | 22.260 | 1.020 | -4.680 | 6.699 |
| person | ratio | 1.374 | 1.285 | 1.466 | 1.355 | 1.257 | 1.462 | -0.020 | -0.159 | 0.125 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted levels and ratios

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2256 | 60.072 | 57.634 | 62.815 | 1628 | 64.514 | 61.796 | 67.150 | 1.074 | 1.008 | 1.131 | equivalent | inconclusive |
| travel_day | q2 | 2369 | 59.953 | 57.318 | 62.685 | 1843 | 64.853 | 62.023 | 68.126 | 1.082 | 1.030 | 1.138 | equivalent | inconclusive |
| travel_day | q3 | 2743 | 62.466 | 59.959 | 65.267 | 1850 | 68.818 | 66.210 | 71.484 | 1.102 | 1.056 | 1.158 | inconclusive | inconclusive |
| travel_day | q4 | 2871 | 64.756 | 62.149 | 67.488 | 1990 | 69.751 | 67.118 | 72.410 | 1.077 | 1.023 | 1.128 | equivalent | inconclusive |
| travel_day | q5 | 3767 | 71.555 | 69.084 | 73.836 | 2107 | 76.469 | 73.827 | 78.893 | 1.069 | 1.023 | 1.115 | equivalent | inconclusive |
| person | q1 | 3359 | 45.329 | 42.954 | 47.742 | 2504 | 49.094 | 46.674 | 52.325 | 1.083 | 1.007 | 1.158 | inconclusive | inconclusive |
| person | q2 | 3159 | 47.706 | 45.415 | 50.080 | 2662 | 52.006 | 48.842 | 54.964 | 1.090 | 1.013 | 1.172 | inconclusive | inconclusive |
| person | q3 | 3615 | 50.820 | 48.617 | 53.387 | 2742 | 55.830 | 53.243 | 59.242 | 1.099 | 1.030 | 1.167 | inconclusive | inconclusive |
| person | q4 | 3657 | 55.526 | 53.181 | 58.285 | 2885 | 60.745 | 57.646 | 63.844 | 1.094 | 1.026 | 1.155 | inconclusive | inconclusive |
| person | q5 | 4752 | 61.435 | 58.975 | 63.635 | 3032 | 67.431 | 64.139 | 70.884 | 1.098 | 1.048 | 1.161 | inconclusive | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted gaps

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 11.483 | 7.308 | 14.889 | 11.955 | 7.812 | 15.528 | 0.472 | -5.573 | 5.944 |
| travel_day | ratio | 1.191 | 1.117 | 1.255 | 1.185 | 1.118 | 1.255 | -0.006 | -0.109 | 0.104 |
| person | difference | 16.106 | 12.241 | 19.201 | 18.337 | 13.807 | 22.870 | 2.231 | -3.445 | 7.947 |
| person | ratio | 1.355 | 1.257 | 1.447 | 1.374 | 1.267 | 1.498 | 0.018 | -0.121 | 0.172 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Collapsed joint cells

- travel_day: 38.84% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.52% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|dense|0` → `q4|dense|1`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2256 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2369 | 0 | -0.164 | -6.850 | 5.539 |
| 2008 | M0 | income:q3 | 2743 | 0 | 3.113 | -4.040 | 9.588 |
| 2008 | M0 | income:q4 | 2871 | 0 | 4.861 | -2.055 | 12.600 |
| 2008 | M0 | income:q5 | 3767 | 0 | 16.064 | 8.636 | 23.159 |
| 2008 | M1 | income:q1 | 2256 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2369 | 0 | 0.083 | -6.231 | 5.775 |
| 2008 | M1 | income:q3 | 2743 | 0 | 3.631 | -3.274 | 10.042 |
| 2008 | M1 | income:q4 | 2871 | 0 | 5.502 | -1.702 | 13.207 |
| 2008 | M1 | income:q5 | 3767 | 0 | 15.398 | 7.892 | 22.305 |
| 2008 | M2 | income:q1 | 2256 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2369 | 0 | 0.506 | -6.266 | 6.205 |
| 2008 | M2 | income:q3 | 2743 | 0 | 4.226 | -2.379 | 10.763 |
| 2008 | M2 | income:q4 | 2871 | 0 | 5.959 | -0.857 | 13.764 |
| 2008 | M2 | income:q5 | 3767 | 0 | 16.065 | 8.482 | 23.565 |
| 2019 | M0 | income:q1 | 0 | 1628 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1843 | 1.965 | -4.749 | 8.933 |
| 2019 | M0 | income:q3 | 0 | 1850 | 6.120 | -0.491 | 13.156 |
| 2019 | M0 | income:q4 | 0 | 1990 | 8.403 | 1.613 | 14.749 |
| 2019 | M0 | income:q5 | 0 | 2107 | 17.571 | 10.325 | 25.652 |
| 2019 | M1 | income:q1 | 0 | 1628 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1843 | 3.893 | -2.746 | 10.401 |
| 2019 | M1 | income:q3 | 0 | 1850 | 8.003 | 1.608 | 15.286 |
| 2019 | M1 | income:q4 | 0 | 1990 | 9.814 | 2.679 | 16.542 |
| 2019 | M1 | income:q5 | 0 | 2107 | 17.136 | 9.837 | 25.582 |
| 2019 | M2 | income:q1 | 0 | 1628 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1843 | 3.904 | -2.657 | 11.167 |
| 2019 | M2 | income:q3 | 0 | 1850 | 7.781 | 1.756 | 15.201 |
| 2019 | M2 | income:q4 | 0 | 1990 | 9.303 | 2.699 | 15.676 |
| 2019 | M2 | income:q5 | 0 | 2107 | 16.491 | 9.268 | 25.981 |
| pooled | pooled | income:q1 | 2256 | 1628 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2369 | 1843 | 0.598 | -6.497 | 6.473 |
| pooled | pooled | income:q3 | 2743 | 1850 | 4.263 | -3.141 | 11.082 |
| pooled | pooled | income:q4 | 2871 | 1990 | 5.716 | -1.302 | 13.618 |
| pooled | pooled | income:q5 | 3767 | 2107 | 15.543 | 8.234 | 22.685 |
| pooled | pooled | survey:2019*income:q2 | 2369 | 1843 | 2.778 | -5.654 | 13.382 |
| pooled | pooled | survey:2019*income:q3 | 2743 | 1850 | 3.149 | -4.049 | 14.864 |
| pooled | pooled | survey:2019*income:q4 | 2871 | 1990 | 3.344 | -5.988 | 13.873 |
| pooled | pooled | survey:2019*income:q5 | 3767 | 2107 | 1.184 | -8.214 | 11.981 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Quintile × density

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 366 | 64.779 | 58.405 | 72.332 | 330 | 69.992 | 64.814 | 75.228 | 1.080 | 0.967 | 1.208 |
| travel_day | q1 | intermediate | False | 846 | 61.734 | 57.654 | 67.293 | 791 | 66.755 | 61.684 | 72.537 | 1.081 | 0.983 | 1.188 |
| travel_day | q1 | sparse | False | 285 | 55.410 | 49.508 | 62.409 | 232 | 57.913 | 50.248 | 65.245 | 1.045 | 0.877 | 1.216 |
| travel_day | q1 | very_sparse | False | 759 | 55.365 | 51.498 | 59.158 | 275 | 60.438 | 53.115 | 67.811 | 1.092 | 0.961 | 1.235 |
| travel_day | q2 | dense | False | 266 | 69.717 | 59.593 | 80.036 | 192 | 74.630 | 65.803 | 83.263 | 1.070 | 0.928 | 1.262 |
| travel_day | q2 | intermediate | False | 867 | 60.470 | 56.533 | 63.925 | 828 | 67.741 | 63.460 | 73.026 | 1.120 | 1.039 | 1.216 |
| travel_day | q2 | sparse | False | 313 | 50.250 | 45.075 | 55.639 | 329 | 54.321 | 49.218 | 59.729 | 1.081 | 0.975 | 1.225 |
| travel_day | q2 | very_sparse | False | 923 | 61.262 | 56.830 | 65.518 | 494 | 63.405 | 58.002 | 69.371 | 1.035 | 0.944 | 1.139 |
| travel_day | q3 | dense | False | 328 | 65.944 | 59.649 | 71.650 | 187 | 72.902 | 66.362 | 79.825 | 1.106 | 1.001 | 1.238 |
| travel_day | q3 | intermediate | False | 1030 | 63.246 | 59.538 | 66.851 | 806 | 71.586 | 67.239 | 77.225 | 1.132 | 1.053 | 1.216 |
| travel_day | q3 | sparse | False | 377 | 60.058 | 53.268 | 71.511 | 303 | 64.281 | 57.804 | 70.081 | 1.070 | 0.898 | 1.229 |
| travel_day | q3 | very_sparse | False | 1008 | 61.372 | 57.914 | 66.279 | 554 | 65.841 | 60.888 | 70.697 | 1.073 | 0.990 | 1.171 |
| travel_day | q4 | dense | False | 358 | 59.936 | 55.583 | 65.939 | 242 | 73.561 | 68.179 | 80.660 | 1.227 | 1.091 | 1.363 |
| travel_day | q4 | intermediate | False | 1182 | 67.305 | 63.398 | 71.957 | 883 | 71.611 | 67.287 | 76.021 | 1.064 | 0.977 | 1.143 |
| travel_day | q4 | sparse | False | 394 | 61.909 | 54.591 | 69.484 | 350 | 60.855 | 54.491 | 67.389 | 0.983 | 0.848 | 1.143 |
| travel_day | q4 | very_sparse | False | 937 | 64.955 | 61.579 | 68.333 | 515 | 71.584 | 67.286 | 75.900 | 1.102 | 1.025 | 1.176 |
| travel_day | q5 | dense | False | 678 | 73.377 | 67.635 | 79.012 | 339 | 74.538 | 69.545 | 79.675 | 1.016 | 0.934 | 1.106 |
| travel_day | q5 | intermediate | False | 1801 | 74.020 | 70.511 | 77.788 | 1036 | 79.749 | 76.310 | 83.511 | 1.077 | 1.020 | 1.143 |
| travel_day | q5 | sparse | False | 410 | 62.765 | 57.113 | 67.825 | 311 | 69.505 | 61.124 | 76.680 | 1.107 | 0.971 | 1.260 |
| travel_day | q5 | very_sparse | False | 878 | 69.725 | 64.753 | 75.193 | 421 | 74.720 | 68.303 | 81.149 | 1.072 | 0.973 | 1.185 |
| person | q1 | dense | False | 473 | 55.803 | 49.455 | 63.011 | 476 | 60.930 | 54.683 | 67.215 | 1.092 | 0.954 | 1.236 |
| person | q1 | intermediate | False | 1159 | 47.626 | 43.708 | 51.923 | 1197 | 52.095 | 47.324 | 57.587 | 1.094 | 0.984 | 1.219 |
| person | q1 | sparse | False | 435 | 39.838 | 33.691 | 47.221 | 385 | 40.534 | 33.993 | 47.766 | 1.017 | 0.832 | 1.221 |
| person | q1 | very_sparse | False | 1292 | 35.912 | 32.689 | 38.701 | 446 | 41.344 | 35.397 | 47.525 | 1.151 | 0.981 | 1.391 |
| person | q2 | dense | False | 331 | 62.295 | 52.433 | 71.630 | 293 | 57.506 | 47.918 | 66.693 | 0.923 | 0.792 | 1.112 |
| person | q2 | intermediate | False | 1131 | 48.691 | 45.523 | 52.125 | 1191 | 55.231 | 50.722 | 60.821 | 1.134 | 1.034 | 1.241 |
| person | q2 | sparse | False | 427 | 38.361 | 32.359 | 43.294 | 456 | 43.007 | 37.682 | 48.747 | 1.121 | 0.968 | 1.336 |
| person | q2 | very_sparse | False | 1270 | 47.157 | 42.681 | 51.016 | 722 | 50.565 | 44.851 | 56.337 | 1.072 | 0.958 | 1.197 |
| person | q3 | dense | False | 418 | 54.160 | 47.533 | 59.344 | 284 | 56.803 | 47.821 | 67.305 | 1.049 | 0.868 | 1.247 |
| person | q3 | intermediate | False | 1298 | 53.315 | 49.616 | 57.469 | 1190 | 58.914 | 54.217 | 64.321 | 1.105 | 1.013 | 1.212 |
| person | q3 | sparse | False | 495 | 48.157 | 42.112 | 58.336 | 459 | 50.383 | 44.404 | 56.756 | 1.046 | 0.851 | 1.249 |
| person | q3 | very_sparse | False | 1404 | 47.631 | 44.623 | 51.638 | 809 | 54.376 | 48.523 | 59.674 | 1.142 | 1.042 | 1.272 |
| person | q4 | dense | False | 449 | 53.428 | 48.787 | 58.813 | 348 | 71.637 | 63.676 | 80.150 | 1.341 | 1.157 | 1.490 |
| person | q4 | intermediate | False | 1479 | 57.598 | 54.218 | 61.499 | 1291 | 61.695 | 57.138 | 66.669 | 1.071 | 0.973 | 1.163 |
| person | q4 | sparse | False | 497 | 55.722 | 49.488 | 63.058 | 514 | 50.099 | 43.065 | 57.170 | 0.899 | 0.760 | 1.056 |
| person | q4 | very_sparse | False | 1232 | 52.931 | 49.110 | 56.954 | 732 | 61.846 | 56.443 | 67.697 | 1.168 | 1.050 | 1.283 |
| person | q5 | dense | False | 860 | 63.598 | 58.021 | 70.177 | 497 | 69.454 | 62.844 | 77.000 | 1.092 | 0.984 | 1.215 |
| person | q5 | intermediate | False | 2201 | 66.173 | 62.554 | 69.396 | 1478 | 70.349 | 65.822 | 75.291 | 1.063 | 0.987 | 1.138 |
| person | q5 | sparse | False | 542 | 50.025 | 44.919 | 55.195 | 452 | 61.526 | 52.635 | 70.215 | 1.230 | 1.043 | 1.414 |
| person | q5 | very_sparse | False | 1149 | 55.965 | 51.789 | 60.998 | 605 | 62.864 | 56.099 | 69.176 | 1.123 | 1.002 | 1.260 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Conclusion grid

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.088 | equivalent | 1.195 | 1.173 | 1.191 | 1.185 | 1.161 | 1.165 |
| travel_day | q2 | 1.071 | equivalent | 1.195 | 1.173 | 1.191 | 1.185 | 1.161 | 1.165 |
| travel_day | q3 | 1.100 | inconclusive | 1.195 | 1.173 | 1.191 | 1.185 | 1.161 | 1.165 |
| travel_day | q4 | 1.076 | equivalent | 1.195 | 1.173 | 1.191 | 1.185 | 1.161 | 1.165 |
| travel_day | q5 | 1.068 | equivalent | 1.195 | 1.173 | 1.191 | 1.185 | 1.161 | 1.165 |
| person | q1 | 1.120 | inconclusive | 1.374 | 1.355 | 1.355 | 1.374 | 1.161 | 1.165 |
| person | q2 | 1.077 | equivalent | 1.374 | 1.355 | 1.355 | 1.374 | 1.161 | 1.165 |
| person | q3 | 1.097 | inconclusive | 1.374 | 1.355 | 1.355 | 1.374 | 1.161 | 1.165 |
| person | q4 | 1.088 | inconclusive | 1.374 | 1.355 | 1.355 | 1.374 | 1.161 | 1.165 |
| person | q5 | 1.104 | inconclusive | 1.374 | 1.355 | 1.355 | 1.374 | 1.161 | 1.165 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


The positive income gradient survives density and car controls in both years.

## Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 597 |
| regression_M0 | 2019 | 13 | 0 | 0 | 505 |
| regression_M1 | 2008 | 16 | 0 | 0 | 597 |
| regression_M1 | 2019 | 16 | 0 | 0 | 505 |
| regression_M2 | 2008 | 18 | 0 | 0 | 597 |
| regression_M2 | 2019 | 18 | 0 | 0 | 505 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 23 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1805 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1301 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2264 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1641 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2450 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1650 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 505 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 14 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 47 | 0 | 0 | 71 |
| reweight_travel_day | 2019 | 47 | 0 | 0 | 50 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Levels and 2019/2008 ratios

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2264 | 61.133 | 58.301 | 64.076 | 1641 | 66.400 | 63.412 | 69.288 | 1.086 | 1.021 | 1.147 | equivalent | inconclusive |
| travel_day | q2 | 2382 | 62.718 | 59.638 | 66.474 | 1851 | 66.154 | 63.138 | 70.123 | 1.055 | 0.999 | 1.118 | equivalent | inconclusive |
| travel_day | q3 | 2766 | 65.414 | 62.694 | 69.031 | 1873 | 74.535 | 70.112 | 79.164 | 1.139 | 1.069 | 1.198 | inconclusive | inconclusive |
| travel_day | q4 | 2910 | 67.881 | 64.415 | 70.707 | 2003 | 70.938 | 68.265 | 73.943 | 1.045 | 0.989 | 1.092 | equivalent | equivalent |
| travel_day | q5 | 3827 | 76.698 | 73.553 | 79.622 | 2136 | 79.266 | 76.303 | 81.682 | 1.033 | 0.986 | 1.080 | equivalent | equivalent |
| person | q1 | 3359 | 45.627 | 43.174 | 48.082 | 2504 | 51.159 | 48.552 | 54.328 | 1.121 | 1.040 | 1.198 | inconclusive | inconclusive |
| person | q2 | 3159 | 50.613 | 48.059 | 53.812 | 2662 | 53.251 | 50.169 | 56.744 | 1.052 | 0.980 | 1.131 | equivalent | inconclusive |
| person | q3 | 3615 | 53.825 | 51.374 | 57.406 | 2742 | 61.190 | 57.025 | 65.675 | 1.137 | 1.056 | 1.238 | inconclusive | inconclusive |
| person | q4 | 3657 | 58.891 | 56.158 | 61.739 | 2885 | 62.058 | 58.845 | 65.076 | 1.054 | 0.993 | 1.120 | equivalent | inconclusive |
| person | q5 | 4752 | 66.842 | 64.141 | 69.945 | 3032 | 70.899 | 67.532 | 74.436 | 1.061 | 1.002 | 1.116 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Income gaps and their changes

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 15.564 | 10.825 | 18.991 | 12.866 | 8.637 | 16.853 | -2.698 | -8.481 | 3.529 |
| travel_day | ratio | 1.255 | 1.170 | 1.322 | 1.194 | 1.124 | 1.266 | -0.061 | -0.155 | 0.052 |
| person | difference | 21.215 | 17.305 | 24.586 | 19.740 | 15.120 | 24.406 | -1.475 | -7.815 | 4.812 |
| person | ratio | 1.465 | 1.363 | 1.556 | 1.386 | 1.285 | 1.500 | -0.079 | -0.235 | 0.082 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted levels and ratios

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2264 | 61.310 | 58.556 | 64.168 | 1641 | 65.949 | 62.992 | 68.866 | 1.076 | 1.009 | 1.133 | equivalent | inconclusive |
| travel_day | q2 | 2382 | 62.417 | 59.451 | 66.141 | 1851 | 66.387 | 63.212 | 69.906 | 1.064 | 1.004 | 1.124 | equivalent | inconclusive |
| travel_day | q3 | 2766 | 65.430 | 62.758 | 69.015 | 1873 | 74.822 | 70.131 | 79.145 | 1.144 | 1.072 | 1.208 | inconclusive | inconclusive |
| travel_day | q4 | 2910 | 67.841 | 64.506 | 70.854 | 2003 | 71.051 | 68.431 | 74.189 | 1.047 | 0.991 | 1.094 | equivalent | equivalent |
| travel_day | q5 | 3827 | 76.758 | 73.840 | 79.709 | 2136 | 79.523 | 76.594 | 82.010 | 1.036 | 0.992 | 1.085 | equivalent | equivalent |
| person | q1 | 3359 | 46.389 | 43.765 | 49.060 | 2504 | 50.440 | 47.796 | 53.417 | 1.087 | 1.011 | 1.163 | inconclusive | inconclusive |
| person | q2 | 3159 | 50.211 | 47.439 | 53.343 | 2662 | 53.475 | 50.154 | 56.707 | 1.065 | 0.990 | 1.140 | equivalent | inconclusive |
| person | q3 | 3615 | 53.786 | 51.290 | 57.268 | 2742 | 61.467 | 57.243 | 66.007 | 1.143 | 1.059 | 1.241 | inconclusive | inconclusive |
| person | q4 | 3657 | 58.839 | 55.983 | 61.751 | 2885 | 62.366 | 59.237 | 65.474 | 1.060 | 0.995 | 1.125 | equivalent | inconclusive |
| person | q5 | 4752 | 67.042 | 64.345 | 70.153 | 3032 | 70.913 | 67.366 | 74.441 | 1.058 | 1.004 | 1.113 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted gaps

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 15.448 | 10.928 | 18.785 | 13.574 | 9.668 | 17.518 | -1.874 | -7.214 | 4.369 |
| travel_day | ratio | 1.252 | 1.169 | 1.314 | 1.206 | 1.140 | 1.275 | -0.046 | -0.143 | 0.062 |
| person | difference | 20.653 | 16.849 | 23.993 | 20.472 | 15.712 | 25.129 | -0.180 | -6.374 | 6.310 |
| person | ratio | 1.445 | 1.346 | 1.540 | 1.406 | 1.299 | 1.522 | -0.039 | -0.191 | 0.110 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Collapsed joint cells

- travel_day: 38.82% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.52% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|dense|0` → `q4|dense|1`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2264 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2382 | 0 | 0.423 | -6.730 | 6.262 |
| 2008 | M0 | income:q3 | 2766 | 0 | 4.147 | -2.912 | 10.816 |
| 2008 | M0 | income:q4 | 2910 | 0 | 5.317 | -1.914 | 13.261 |
| 2008 | M0 | income:q5 | 3827 | 0 | 20.204 | 12.583 | 27.365 |
| 2008 | M1 | income:q1 | 2264 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2382 | 0 | 0.649 | -6.385 | 6.607 |
| 2008 | M1 | income:q3 | 2766 | 0 | 4.628 | -2.168 | 11.164 |
| 2008 | M1 | income:q4 | 2910 | 0 | 5.860 | -1.589 | 13.892 |
| 2008 | M1 | income:q5 | 3827 | 0 | 19.622 | 12.066 | 26.751 |
| 2008 | M2 | income:q1 | 2264 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2382 | 0 | 0.936 | -6.643 | 6.962 |
| 2008 | M2 | income:q3 | 2766 | 0 | 5.017 | -1.781 | 11.563 |
| 2008 | M2 | income:q4 | 2910 | 0 | 6.096 | -1.203 | 13.843 |
| 2008 | M2 | income:q5 | 3827 | 0 | 20.017 | 12.529 | 27.859 |
| 2019 | M0 | income:q1 | 0 | 1641 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1851 | 1.967 | -4.243 | 8.918 |
| 2019 | M0 | income:q3 | 0 | 1873 | 8.600 | 1.475 | 16.370 |
| 2019 | M0 | income:q4 | 0 | 2003 | 8.483 | 1.301 | 14.852 |
| 2019 | M0 | income:q5 | 0 | 2136 | 18.509 | 11.414 | 26.731 |
| 2019 | M1 | income:q1 | 0 | 1641 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1851 | 3.872 | -2.784 | 10.434 |
| 2019 | M1 | income:q3 | 0 | 1873 | 10.459 | 3.530 | 18.991 |
| 2019 | M1 | income:q4 | 0 | 2003 | 9.916 | 2.333 | 16.901 |
| 2019 | M1 | income:q5 | 0 | 2136 | 18.075 | 10.696 | 26.628 |
| 2019 | M2 | income:q1 | 0 | 1641 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1851 | 3.727 | -2.917 | 10.669 |
| 2019 | M2 | income:q3 | 0 | 1873 | 10.003 | 3.211 | 17.673 |
| 2019 | M2 | income:q4 | 0 | 2003 | 9.161 | 1.948 | 16.173 |
| 2019 | M2 | income:q5 | 0 | 2136 | 17.190 | 9.189 | 25.063 |
| pooled | pooled | income:q1 | 2264 | 1641 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2382 | 1851 | 1.281 | -5.944 | 7.323 |
| pooled | pooled | income:q3 | 2766 | 1873 | 5.460 | -2.054 | 12.012 |
| pooled | pooled | income:q4 | 2910 | 2003 | 6.416 | -1.154 | 14.339 |
| pooled | pooled | income:q5 | 3827 | 2136 | 20.012 | 11.912 | 27.024 |
| pooled | pooled | survey:2019*income:q2 | 2382 | 1851 | 1.699 | -6.796 | 13.660 |
| pooled | pooled | survey:2019*income:q3 | 2766 | 1873 | 3.767 | -3.778 | 15.685 |
| pooled | pooled | survey:2019*income:q4 | 2910 | 2003 | 2.177 | -6.617 | 12.600 |
| pooled | pooled | survey:2019*income:q5 | 3827 | 2136 | -2.383 | -10.849 | 8.017 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Quintile × density

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 366 | 64.784 | 58.405 | 72.332 | 331 | 71.416 | 65.555 | 77.043 | 1.102 | 0.983 | 1.232 |
| travel_day | q1 | intermediate | False | 850 | 62.469 | 58.303 | 68.098 | 798 | 67.981 | 62.597 | 74.027 | 1.088 | 0.990 | 1.194 |
| travel_day | q1 | sparse | False | 285 | 58.244 | 50.491 | 67.474 | 234 | 58.328 | 50.380 | 65.783 | 1.001 | 0.830 | 1.176 |
| travel_day | q1 | very_sparse | False | 763 | 57.819 | 53.308 | 62.189 | 278 | 63.390 | 55.174 | 70.378 | 1.096 | 0.971 | 1.232 |
| travel_day | q2 | dense | False | 267 | 69.696 | 59.594 | 80.035 | 193 | 75.565 | 65.934 | 85.117 | 1.084 | 0.931 | 1.280 |
| travel_day | q2 | intermediate | False | 873 | 64.149 | 59.290 | 69.809 | 832 | 69.999 | 65.057 | 75.567 | 1.091 | 1.007 | 1.199 |
| travel_day | q2 | sparse | False | 314 | 50.704 | 45.502 | 56.362 | 330 | 54.583 | 49.560 | 60.066 | 1.077 | 0.974 | 1.218 |
| travel_day | q2 | very_sparse | False | 928 | 63.980 | 58.519 | 69.979 | 496 | 64.934 | 58.896 | 71.999 | 1.015 | 0.907 | 1.125 |
| travel_day | q3 | dense | False | 331 | 69.613 | 62.436 | 77.598 | 190 | 98.414 | 70.070 | 133.282 | 1.414 | 1.016 | 1.877 |
| travel_day | q3 | intermediate | False | 1036 | 65.023 | 60.886 | 69.684 | 814 | 73.780 | 69.713 | 78.872 | 1.135 | 1.060 | 1.219 |
| travel_day | q3 | sparse | False | 382 | 66.676 | 57.824 | 78.734 | 308 | 68.655 | 61.828 | 75.717 | 1.030 | 0.865 | 1.194 |
| travel_day | q3 | very_sparse | False | 1017 | 63.301 | 59.501 | 67.500 | 561 | 70.482 | 64.917 | 76.850 | 1.113 | 1.029 | 1.228 |
| travel_day | q4 | dense | False | 363 | 61.918 | 57.194 | 67.408 | 243 | 73.717 | 68.437 | 80.664 | 1.191 | 1.060 | 1.317 |
| travel_day | q4 | intermediate | False | 1196 | 71.290 | 65.877 | 76.566 | 889 | 73.116 | 68.522 | 78.000 | 1.026 | 0.936 | 1.121 |
| travel_day | q4 | sparse | False | 399 | 63.131 | 55.768 | 70.488 | 354 | 62.234 | 56.262 | 69.017 | 0.986 | 0.852 | 1.157 |
| travel_day | q4 | very_sparse | False | 952 | 68.681 | 64.719 | 72.982 | 517 | 73.175 | 68.427 | 77.460 | 1.065 | 0.978 | 1.143 |
| travel_day | q5 | dense | False | 689 | 79.656 | 72.476 | 87.805 | 344 | 76.843 | 71.242 | 82.374 | 0.965 | 0.868 | 1.078 |
| travel_day | q5 | intermediate | False | 1816 | 78.712 | 74.081 | 83.217 | 1046 | 81.513 | 77.723 | 85.468 | 1.036 | 0.977 | 1.101 |
| travel_day | q5 | sparse | False | 425 | 70.544 | 64.651 | 76.446 | 313 | 72.403 | 64.593 | 81.528 | 1.026 | 0.910 | 1.166 |
| travel_day | q5 | very_sparse | False | 897 | 73.572 | 67.956 | 78.965 | 433 | 82.195 | 75.117 | 90.836 | 1.117 | 1.011 | 1.233 |
| person | q1 | dense | False | 473 | 55.807 | 49.455 | 63.023 | 476 | 62.288 | 55.905 | 68.390 | 1.116 | 0.976 | 1.273 |
| person | q1 | intermediate | False | 1159 | 48.339 | 44.251 | 52.520 | 1197 | 53.360 | 48.706 | 58.637 | 1.104 | 0.989 | 1.225 |
| person | q1 | sparse | False | 435 | 41.876 | 34.784 | 51.188 | 385 | 40.943 | 34.280 | 48.216 | 0.978 | 0.794 | 1.220 |
| person | q1 | very_sparse | False | 1292 | 37.660 | 34.393 | 40.881 | 446 | 43.757 | 37.436 | 50.970 | 1.162 | 1.005 | 1.376 |
| person | q2 | dense | False | 331 | 62.441 | 52.796 | 71.752 | 293 | 58.440 | 47.918 | 67.630 | 0.936 | 0.795 | 1.135 |
| person | q2 | intermediate | False | 1131 | 52.496 | 48.026 | 57.550 | 1191 | 57.421 | 52.326 | 63.087 | 1.094 | 0.988 | 1.217 |
| person | q2 | sparse | False | 427 | 38.817 | 33.043 | 43.832 | 456 | 43.256 | 37.928 | 48.769 | 1.114 | 0.967 | 1.314 |
| person | q2 | very_sparse | False | 1270 | 49.902 | 45.312 | 55.027 | 722 | 51.947 | 46.022 | 57.324 | 1.041 | 0.917 | 1.171 |
| person | q3 | dense | False | 418 | 58.426 | 51.370 | 65.236 | 284 | 79.052 | 55.009 | 109.152 | 1.353 | 0.961 | 1.833 |
| person | q3 | intermediate | False | 1298 | 55.033 | 51.305 | 59.430 | 1190 | 61.175 | 56.463 | 66.833 | 1.112 | 1.010 | 1.216 |
| person | q3 | sparse | False | 495 | 54.698 | 47.153 | 66.382 | 459 | 54.385 | 47.979 | 62.147 | 0.994 | 0.827 | 1.185 |
| person | q3 | very_sparse | False | 1404 | 49.550 | 45.968 | 53.628 | 809 | 58.971 | 53.297 | 65.529 | 1.190 | 1.078 | 1.341 |
| person | q4 | dense | False | 449 | 55.671 | 50.834 | 61.866 | 348 | 71.845 | 64.195 | 80.360 | 1.291 | 1.119 | 1.455 |
| person | q4 | intermediate | False | 1479 | 61.797 | 56.850 | 66.128 | 1291 | 63.595 | 58.855 | 68.505 | 1.029 | 0.931 | 1.134 |
| person | q4 | sparse | False | 497 | 57.318 | 50.577 | 64.631 | 514 | 52.008 | 44.575 | 58.856 | 0.907 | 0.773 | 1.078 |
| person | q4 | very_sparse | False | 1232 | 56.673 | 52.890 | 60.454 | 732 | 63.476 | 57.475 | 69.099 | 1.120 | 1.019 | 1.231 |
| person | q5 | dense | False | 860 | 69.658 | 62.578 | 77.834 | 497 | 72.315 | 66.073 | 79.707 | 1.038 | 0.940 | 1.179 |
| person | q5 | intermediate | False | 2201 | 71.109 | 66.582 | 75.181 | 1478 | 72.402 | 68.184 | 77.271 | 1.018 | 0.941 | 1.096 |
| person | q5 | sparse | False | 542 | 58.594 | 52.602 | 65.136 | 452 | 64.355 | 55.559 | 73.583 | 1.098 | 0.941 | 1.262 |
| person | q5 | very_sparse | False | 1149 | 60.571 | 54.805 | 65.938 | 605 | 71.077 | 63.213 | 79.899 | 1.173 | 1.034 | 1.316 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Conclusion grid

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.086 | equivalent | 1.255 | 1.194 | 1.252 | 1.206 | 1.200 | 1.172 |
| travel_day | q2 | 1.055 | equivalent | 1.255 | 1.194 | 1.252 | 1.206 | 1.200 | 1.172 |
| travel_day | q3 | 1.139 | inconclusive | 1.255 | 1.194 | 1.252 | 1.206 | 1.200 | 1.172 |
| travel_day | q4 | 1.045 | equivalent | 1.255 | 1.194 | 1.252 | 1.206 | 1.200 | 1.172 |
| travel_day | q5 | 1.033 | equivalent | 1.255 | 1.194 | 1.252 | 1.206 | 1.200 | 1.172 |
| person | q1 | 1.121 | inconclusive | 1.465 | 1.386 | 1.445 | 1.406 | 1.200 | 1.172 |
| person | q2 | 1.052 | equivalent | 1.465 | 1.386 | 1.445 | 1.406 | 1.200 | 1.172 |
| person | q3 | 1.137 | inconclusive | 1.465 | 1.386 | 1.445 | 1.406 | 1.200 | 1.172 |
| person | q4 | 1.054 | equivalent | 1.465 | 1.386 | 1.445 | 1.406 | 1.200 | 1.172 |
| person | q5 | 1.061 | equivalent | 1.465 | 1.386 | 1.445 | 1.406 | 1.200 | 1.172 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

The positive income gradient survives density and car controls in both years.

## Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 614 |
| regression_M0 | 2019 | 13 | 0 | 0 | 516 |
| regression_M1 | 2008 | 16 | 0 | 0 | 614 |
| regression_M1 | 2019 | 16 | 0 | 0 | 516 |
| regression_M2 | 2008 | 18 | 0 | 0 | 614 |
| regression_M2 | 2019 | 18 | 0 | 0 | 516 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 24 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1836 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1323 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2352 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1692 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2510 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1685 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 516 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 14 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 47 | 0 | 0 | 73 |
| reweight_travel_day | 2019 | 47 | 0 | 0 | 52 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Levels and 2019/2008 ratios

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2352 | 63.384 | 60.463 | 66.657 | 1692 | 69.332 | 66.316 | 72.154 | 1.094 | 1.030 | 1.148 | equivalent | inconclusive |
| travel_day | q2 | 2438 | 63.213 | 60.434 | 66.267 | 1902 | 69.956 | 66.930 | 73.728 | 1.107 | 1.050 | 1.168 | inconclusive | inconclusive |
| travel_day | q3 | 2812 | 66.627 | 63.311 | 70.109 | 1896 | 75.178 | 72.198 | 78.256 | 1.128 | 1.069 | 1.187 | inconclusive | inconclusive |
| travel_day | q4 | 2922 | 68.327 | 65.869 | 70.896 | 2015 | 73.808 | 70.709 | 76.528 | 1.080 | 1.025 | 1.131 | equivalent | inconclusive |
| travel_day | q5 | 3818 | 75.883 | 72.935 | 78.538 | 2133 | 82.022 | 79.750 | 84.800 | 1.081 | 1.038 | 1.128 | equivalent | inconclusive |
| person | q1 | 3359 | 49.321 | 46.855 | 51.847 | 2504 | 55.020 | 52.194 | 57.754 | 1.116 | 1.044 | 1.180 | inconclusive | inconclusive |
| person | q2 | 3159 | 51.583 | 49.189 | 53.864 | 2662 | 57.931 | 54.489 | 61.159 | 1.123 | 1.056 | 1.202 | inconclusive | inconclusive |
| person | q3 | 3615 | 55.360 | 52.669 | 58.670 | 2742 | 62.434 | 59.064 | 65.870 | 1.128 | 1.057 | 1.194 | inconclusive | inconclusive |
| person | q4 | 3657 | 59.406 | 57.080 | 61.886 | 2885 | 64.757 | 61.135 | 68.004 | 1.090 | 1.019 | 1.158 | inconclusive | inconclusive |
| person | q5 | 4752 | 65.887 | 63.353 | 68.315 | 3032 | 73.266 | 70.341 | 76.499 | 1.112 | 1.065 | 1.175 | inconclusive | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Income gaps and their changes

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 12.499 | 7.636 | 16.178 | 12.690 | 9.025 | 16.616 | 0.191 | -5.259 | 6.126 |
| travel_day | ratio | 1.197 | 1.115 | 1.264 | 1.183 | 1.127 | 1.247 | -0.014 | -0.105 | 0.089 |
| person | difference | 16.566 | 12.630 | 19.860 | 18.246 | 14.195 | 23.074 | 1.680 | -3.857 | 8.813 |
| person | ratio | 1.336 | 1.251 | 1.417 | 1.332 | 1.252 | 1.437 | -0.004 | -0.113 | 0.154 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted levels and ratios

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2352 | 63.748 | 60.890 | 67.194 | 1692 | 68.856 | 65.821 | 71.557 | 1.080 | 1.019 | 1.135 | equivalent | inconclusive |
| travel_day | q2 | 2438 | 62.914 | 60.130 | 65.854 | 1902 | 70.128 | 66.905 | 73.596 | 1.115 | 1.062 | 1.175 | inconclusive | inconclusive |
| travel_day | q3 | 2812 | 66.661 | 63.445 | 70.084 | 1896 | 75.170 | 72.245 | 78.042 | 1.128 | 1.070 | 1.184 | inconclusive | inconclusive |
| travel_day | q4 | 2922 | 68.312 | 65.854 | 70.839 | 2015 | 73.953 | 70.887 | 76.741 | 1.083 | 1.029 | 1.135 | equivalent | inconclusive |
| travel_day | q5 | 3818 | 76.036 | 73.172 | 78.795 | 2133 | 82.192 | 79.734 | 84.961 | 1.081 | 1.038 | 1.128 | equivalent | inconclusive |
| person | q1 | 3359 | 50.169 | 47.621 | 52.933 | 2504 | 54.401 | 51.691 | 57.299 | 1.084 | 1.018 | 1.149 | equivalent | inconclusive |
| person | q2 | 3159 | 51.196 | 48.855 | 53.525 | 2662 | 58.046 | 54.540 | 61.291 | 1.134 | 1.065 | 1.212 | inconclusive | inconclusive |
| person | q3 | 3615 | 55.325 | 52.705 | 58.719 | 2742 | 62.483 | 59.115 | 65.948 | 1.129 | 1.056 | 1.193 | inconclusive | inconclusive |
| person | q4 | 3657 | 59.425 | 56.910 | 62.119 | 2885 | 65.096 | 61.553 | 68.503 | 1.095 | 1.025 | 1.161 | inconclusive | inconclusive |
| person | q5 | 4752 | 66.169 | 63.732 | 68.530 | 3032 | 73.138 | 70.279 | 76.422 | 1.105 | 1.059 | 1.170 | inconclusive | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted gaps

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 12.289 | 7.724 | 15.876 | 13.336 | 9.698 | 17.133 | 1.047 | -4.343 | 7.691 |
| travel_day | ratio | 1.193 | 1.115 | 1.261 | 1.194 | 1.137 | 1.259 | 0.001 | -0.087 | 0.115 |
| person | difference | 16.000 | 11.936 | 19.464 | 18.738 | 15.242 | 23.649 | 2.737 | -2.403 | 9.381 |
| person | ratio | 1.319 | 1.229 | 1.403 | 1.344 | 1.261 | 1.453 | 0.026 | -0.078 | 0.176 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Collapsed joint cells

- travel_day: 39.03% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.52% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|dense|0` → `q4|dense|1`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2352 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2438 | 0 | 0.252 | -7.025 | 6.914 |
| 2008 | M0 | income:q3 | 2812 | 0 | 4.758 | -2.254 | 12.429 |
| 2008 | M0 | income:q4 | 2922 | 0 | 6.500 | -1.073 | 15.355 |
| 2008 | M0 | income:q5 | 3818 | 0 | 17.373 | 8.276 | 24.392 |
| 2008 | M1 | income:q1 | 2352 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2438 | 0 | 0.329 | -6.684 | 7.315 |
| 2008 | M1 | income:q3 | 2812 | 0 | 5.129 | -2.271 | 12.624 |
| 2008 | M1 | income:q4 | 2922 | 0 | 6.969 | -0.660 | 15.779 |
| 2008 | M1 | income:q5 | 3818 | 0 | 16.533 | 7.425 | 23.588 |
| 2008 | M2 | income:q1 | 2352 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2438 | 0 | 0.455 | -5.771 | 7.210 |
| 2008 | M2 | income:q3 | 2812 | 0 | 5.283 | -2.059 | 11.979 |
| 2008 | M2 | income:q4 | 2922 | 0 | 6.965 | -0.455 | 14.470 |
| 2008 | M2 | income:q5 | 3818 | 0 | 16.600 | 8.190 | 24.085 |
| 2019 | M0 | income:q1 | 0 | 1692 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1902 | 1.956 | -4.391 | 9.769 |
| 2019 | M0 | income:q3 | 0 | 1896 | 7.360 | 0.804 | 15.008 |
| 2019 | M0 | income:q4 | 0 | 2015 | 5.663 | -1.106 | 12.223 |
| 2019 | M0 | income:q5 | 0 | 2133 | 18.022 | 10.671 | 26.428 |
| 2019 | M1 | income:q1 | 0 | 1692 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1902 | 3.518 | -2.825 | 11.157 |
| 2019 | M1 | income:q3 | 0 | 1896 | 8.818 | 2.757 | 16.942 |
| 2019 | M1 | income:q4 | 0 | 2015 | 6.776 | 0.437 | 13.672 |
| 2019 | M1 | income:q5 | 0 | 2133 | 17.565 | 10.527 | 26.613 |
| 2019 | M2 | income:q1 | 0 | 1692 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1902 | 3.553 | -2.467 | 11.833 |
| 2019 | M2 | income:q3 | 0 | 1896 | 8.591 | 2.451 | 16.713 |
| 2019 | M2 | income:q4 | 0 | 2015 | 6.241 | -0.083 | 12.784 |
| 2019 | M2 | income:q5 | 0 | 2133 | 16.866 | 10.056 | 25.067 |
| pooled | pooled | income:q1 | 2352 | 1692 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2438 | 1902 | 0.543 | -6.198 | 7.056 |
| pooled | pooled | income:q3 | 2812 | 1896 | 5.322 | -1.989 | 12.780 |
| pooled | pooled | income:q4 | 2922 | 2015 | 6.469 | -0.927 | 14.639 |
| pooled | pooled | income:q5 | 3818 | 2133 | 16.158 | 7.212 | 23.075 |
| pooled | pooled | survey:2019*income:q2 | 2438 | 1902 | 2.466 | -6.196 | 13.933 |
| pooled | pooled | survey:2019*income:q3 | 2812 | 1896 | 2.929 | -4.845 | 13.664 |
| pooled | pooled | survey:2019*income:q4 | 2922 | 2015 | -0.276 | -9.480 | 10.758 |
| pooled | pooled | survey:2019*income:q5 | 3818 | 2133 | 0.991 | -8.465 | 13.742 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Quintile × density

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 381 | 68.640 | 61.311 | 77.435 | 341 | 74.732 | 68.774 | 81.599 | 1.089 | 0.958 | 1.226 |
| travel_day | q1 | intermediate | False | 864 | 66.587 | 62.035 | 71.744 | 821 | 69.619 | 64.771 | 75.496 | 1.046 | 0.955 | 1.159 |
| travel_day | q1 | sparse | False | 305 | 57.846 | 49.887 | 65.934 | 242 | 64.039 | 55.063 | 71.770 | 1.107 | 0.928 | 1.281 |
| travel_day | q1 | very_sparse | False | 802 | 57.554 | 53.639 | 61.447 | 288 | 67.099 | 57.978 | 76.289 | 1.166 | 1.019 | 1.334 |
| travel_day | q2 | dense | False | 271 | 72.107 | 62.355 | 82.825 | 199 | 81.408 | 72.664 | 90.508 | 1.129 | 0.981 | 1.334 |
| travel_day | q2 | intermediate | False | 888 | 63.221 | 59.153 | 66.733 | 854 | 71.903 | 67.288 | 77.056 | 1.137 | 1.054 | 1.218 |
| travel_day | q2 | sparse | False | 321 | 54.030 | 48.933 | 60.163 | 338 | 62.830 | 57.091 | 69.757 | 1.163 | 1.042 | 1.339 |
| travel_day | q2 | very_sparse | False | 958 | 64.197 | 59.598 | 68.438 | 511 | 67.890 | 62.541 | 73.878 | 1.058 | 0.971 | 1.166 |
| travel_day | q3 | dense | False | 334 | 67.362 | 60.868 | 73.987 | 194 | 79.346 | 71.709 | 86.466 | 1.178 | 1.064 | 1.321 |
| travel_day | q3 | intermediate | False | 1043 | 68.315 | 63.110 | 74.434 | 824 | 78.481 | 74.073 | 83.504 | 1.149 | 1.050 | 1.246 |
| travel_day | q3 | sparse | False | 391 | 64.972 | 57.477 | 76.552 | 309 | 68.252 | 61.216 | 75.367 | 1.050 | 0.866 | 1.195 |
| travel_day | q3 | very_sparse | False | 1044 | 64.762 | 61.144 | 69.128 | 569 | 73.180 | 68.352 | 78.102 | 1.130 | 1.040 | 1.230 |
| travel_day | q4 | dense | False | 368 | 65.371 | 59.173 | 72.679 | 245 | 77.604 | 70.520 | 86.174 | 1.187 | 1.057 | 1.332 |
| travel_day | q4 | intermediate | False | 1195 | 70.203 | 66.461 | 74.688 | 893 | 74.705 | 70.028 | 79.451 | 1.064 | 0.987 | 1.135 |
| travel_day | q4 | sparse | False | 399 | 65.426 | 57.946 | 73.538 | 358 | 66.405 | 58.351 | 74.304 | 1.015 | 0.873 | 1.168 |
| travel_day | q4 | very_sparse | False | 960 | 68.861 | 65.539 | 72.727 | 519 | 76.804 | 71.812 | 80.851 | 1.115 | 1.036 | 1.197 |
| travel_day | q5 | dense | False | 686 | 77.364 | 71.772 | 83.123 | 344 | 76.504 | 71.599 | 81.274 | 0.989 | 0.917 | 1.079 |
| travel_day | q5 | intermediate | False | 1821 | 79.283 | 75.078 | 83.586 | 1046 | 85.495 | 81.684 | 89.292 | 1.078 | 1.019 | 1.144 |
| travel_day | q5 | sparse | False | 420 | 65.688 | 59.332 | 71.836 | 316 | 76.829 | 68.931 | 83.612 | 1.170 | 1.039 | 1.301 |
| travel_day | q5 | very_sparse | False | 891 | 73.867 | 69.292 | 79.458 | 427 | 83.531 | 75.735 | 92.308 | 1.131 | 1.028 | 1.246 |
| person | q1 | dense | False | 473 | 61.053 | 53.971 | 68.458 | 476 | 66.894 | 60.556 | 73.785 | 1.096 | 0.950 | 1.264 |
| person | q1 | intermediate | False | 1159 | 52.447 | 48.412 | 56.612 | 1197 | 55.804 | 51.284 | 61.505 | 1.064 | 0.960 | 1.187 |
| person | q1 | sparse | False | 435 | 45.797 | 39.695 | 53.195 | 385 | 47.088 | 39.689 | 54.573 | 1.028 | 0.834 | 1.212 |
| person | q1 | very_sparse | False | 1292 | 39.583 | 36.182 | 42.497 | 446 | 48.402 | 40.189 | 55.848 | 1.223 | 1.037 | 1.454 |
| person | q2 | dense | False | 331 | 65.205 | 55.310 | 74.362 | 293 | 65.398 | 54.942 | 75.864 | 1.003 | 0.845 | 1.223 |
| person | q2 | intermediate | False | 1131 | 51.779 | 48.403 | 55.189 | 1191 | 60.291 | 55.233 | 66.347 | 1.164 | 1.061 | 1.266 |
| person | q2 | sparse | False | 427 | 41.922 | 36.042 | 47.288 | 456 | 52.057 | 44.814 | 59.053 | 1.242 | 1.071 | 1.465 |
| person | q2 | very_sparse | False | 1270 | 51.357 | 46.565 | 55.210 | 722 | 55.588 | 49.454 | 61.025 | 1.082 | 0.970 | 1.205 |
| person | q3 | dense | False | 418 | 57.129 | 50.892 | 62.562 | 284 | 65.017 | 54.726 | 73.808 | 1.138 | 0.969 | 1.321 |
| person | q3 | intermediate | False | 1298 | 58.101 | 53.894 | 63.958 | 1190 | 65.876 | 60.884 | 71.321 | 1.134 | 1.022 | 1.252 |
| person | q3 | sparse | False | 495 | 53.608 | 47.312 | 64.808 | 459 | 54.323 | 47.463 | 62.244 | 1.013 | 0.822 | 1.207 |
| person | q3 | very_sparse | False | 1404 | 51.716 | 48.313 | 55.551 | 809 | 61.960 | 55.851 | 67.550 | 1.198 | 1.090 | 1.333 |
| person | q4 | dense | False | 449 | 59.883 | 53.559 | 67.896 | 348 | 76.462 | 66.997 | 88.559 | 1.277 | 1.105 | 1.461 |
| person | q4 | intermediate | False | 1479 | 60.689 | 57.195 | 64.851 | 1291 | 64.948 | 59.574 | 70.274 | 1.070 | 0.974 | 1.155 |
| person | q4 | sparse | False | 497 | 59.310 | 53.179 | 66.506 | 514 | 55.883 | 47.738 | 63.798 | 0.942 | 0.789 | 1.093 |
| person | q4 | very_sparse | False | 1232 | 57.122 | 53.757 | 61.546 | 732 | 66.669 | 61.010 | 73.042 | 1.167 | 1.055 | 1.274 |
| person | q5 | dense | False | 860 | 67.575 | 62.094 | 73.928 | 497 | 71.833 | 65.610 | 79.583 | 1.063 | 0.964 | 1.184 |
| person | q5 | intermediate | False | 2201 | 71.336 | 67.040 | 75.373 | 1478 | 75.937 | 71.306 | 81.180 | 1.064 | 0.988 | 1.146 |
| person | q5 | sparse | False | 542 | 54.917 | 49.491 | 60.750 | 452 | 68.835 | 60.109 | 76.411 | 1.253 | 1.070 | 1.409 |
| person | q5 | very_sparse | False | 1149 | 59.968 | 54.849 | 65.196 | 605 | 71.282 | 62.939 | 81.241 | 1.189 | 1.067 | 1.347 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Conclusion grid

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.094 | equivalent | 1.197 | 1.183 | 1.193 | 1.194 | 1.166 | 1.169 |
| travel_day | q2 | 1.107 | inconclusive | 1.197 | 1.183 | 1.193 | 1.194 | 1.166 | 1.169 |
| travel_day | q3 | 1.128 | inconclusive | 1.197 | 1.183 | 1.193 | 1.194 | 1.166 | 1.169 |
| travel_day | q4 | 1.080 | equivalent | 1.197 | 1.183 | 1.193 | 1.194 | 1.166 | 1.169 |
| travel_day | q5 | 1.081 | equivalent | 1.197 | 1.183 | 1.193 | 1.194 | 1.166 | 1.169 |
| person | q1 | 1.116 | inconclusive | 1.336 | 1.332 | 1.319 | 1.344 | 1.166 | 1.169 |
| person | q2 | 1.123 | inconclusive | 1.336 | 1.332 | 1.319 | 1.344 | 1.166 | 1.169 |
| person | q3 | 1.128 | inconclusive | 1.336 | 1.332 | 1.319 | 1.344 | 1.166 | 1.169 |
| person | q4 | 1.090 | inconclusive | 1.336 | 1.332 | 1.319 | 1.344 | 1.166 | 1.169 |
| person | q5 | 1.112 | inconclusive | 1.336 | 1.332 | 1.319 | 1.344 | 1.166 | 1.169 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


The positive income gradient survives density and car controls in both years.

## Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 617 |
| regression_M0 | 2019 | 13 | 0 | 0 | 519 |
| regression_M1 | 2008 | 16 | 0 | 0 | 617 |
| regression_M1 | 2019 | 16 | 0 | 0 | 519 |
| regression_M2 | 2008 | 18 | 0 | 0 | 617 |
| regression_M2 | 2019 | 18 | 0 | 0 | 519 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 24 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1862 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1334 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2358 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1704 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2530 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1700 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 519 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 14 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 47 | 0 | 0 | 74 |
| reweight_travel_day | 2019 | 47 | 0 | 0 | 52 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Levels and 2019/2008 ratios

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2358 | 64.703 | 61.510 | 68.170 | 1704 | 71.035 | 67.905 | 73.619 | 1.098 | 1.031 | 1.154 | inconclusive | inconclusive |
| travel_day | q2 | 2450 | 65.802 | 62.491 | 69.601 | 1910 | 71.446 | 68.089 | 75.653 | 1.086 | 1.029 | 1.152 | inconclusive | inconclusive |
| travel_day | q3 | 2836 | 69.559 | 66.015 | 73.666 | 1919 | 81.574 | 77.201 | 86.767 | 1.173 | 1.104 | 1.246 | inconclusive | different |
| travel_day | q4 | 2960 | 71.589 | 68.431 | 74.515 | 2027 | 75.514 | 72.619 | 78.605 | 1.055 | 1.005 | 1.107 | equivalent | inconclusive |
| travel_day | q5 | 3881 | 81.487 | 78.393 | 84.844 | 2162 | 85.853 | 83.073 | 89.041 | 1.054 | 1.001 | 1.102 | equivalent | inconclusive |
| person | q1 | 3359 | 50.424 | 47.545 | 53.180 | 2504 | 56.626 | 53.735 | 59.654 | 1.123 | 1.046 | 1.193 | inconclusive | inconclusive |
| person | q2 | 3159 | 54.144 | 51.445 | 57.430 | 2662 | 59.400 | 55.856 | 63.452 | 1.097 | 1.023 | 1.172 | inconclusive | inconclusive |
| person | q3 | 3615 | 58.413 | 55.703 | 62.495 | 2742 | 68.546 | 64.026 | 73.731 | 1.173 | 1.079 | 1.268 | inconclusive | inconclusive |
| person | q4 | 3657 | 62.927 | 59.855 | 65.633 | 2885 | 66.756 | 63.305 | 70.290 | 1.061 | 0.996 | 1.129 | equivalent | inconclusive |
| person | q5 | 4752 | 72.037 | 69.022 | 75.211 | 3032 | 77.482 | 74.025 | 81.398 | 1.076 | 1.021 | 1.137 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Income gaps and their changes

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 16.784 | 11.620 | 20.578 | 14.818 | 11.457 | 19.413 | -1.965 | -7.624 | 4.697 |
| travel_day | ratio | 1.259 | 1.172 | 1.330 | 1.209 | 1.156 | 1.276 | -0.051 | -0.149 | 0.067 |
| person | difference | 21.613 | 17.658 | 25.097 | 20.856 | 16.659 | 25.931 | -0.757 | -6.651 | 6.538 |
| person | ratio | 1.429 | 1.331 | 1.513 | 1.368 | 1.283 | 1.474 | -0.060 | -0.199 | 0.097 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted levels and ratios

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2358 | 64.970 | 61.933 | 68.519 | 1704 | 70.576 | 67.438 | 73.360 | 1.086 | 1.015 | 1.142 | equivalent | inconclusive |
| travel_day | q2 | 2450 | 65.532 | 62.353 | 69.376 | 1910 | 71.602 | 68.136 | 75.476 | 1.093 | 1.036 | 1.157 | inconclusive | inconclusive |
| travel_day | q3 | 2836 | 69.606 | 65.959 | 73.609 | 1919 | 81.744 | 77.386 | 86.727 | 1.174 | 1.105 | 1.242 | inconclusive | different |
| travel_day | q4 | 2960 | 71.521 | 68.273 | 74.443 | 2027 | 75.655 | 72.814 | 78.753 | 1.058 | 1.010 | 1.108 | equivalent | inconclusive |
| travel_day | q5 | 3881 | 81.600 | 78.713 | 84.965 | 2162 | 86.087 | 83.240 | 89.329 | 1.055 | 1.006 | 1.101 | equivalent | inconclusive |
| person | q1 | 3359 | 51.232 | 48.413 | 54.061 | 2504 | 56.017 | 53.417 | 59.103 | 1.093 | 1.019 | 1.156 | inconclusive | inconclusive |
| person | q2 | 3159 | 53.749 | 51.181 | 56.916 | 2662 | 59.517 | 55.718 | 63.464 | 1.107 | 1.033 | 1.180 | inconclusive | inconclusive |
| person | q3 | 3615 | 58.379 | 55.576 | 62.365 | 2742 | 68.804 | 64.150 | 73.565 | 1.179 | 1.088 | 1.275 | inconclusive | inconclusive |
| person | q4 | 3657 | 62.901 | 59.786 | 65.672 | 2885 | 67.072 | 63.605 | 70.482 | 1.066 | 1.002 | 1.130 | equivalent | inconclusive |
| person | q5 | 4752 | 72.283 | 69.239 | 75.410 | 3032 | 77.479 | 74.051 | 81.496 | 1.072 | 1.018 | 1.132 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted gaps

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 16.630 | 11.692 | 20.287 | 15.510 | 12.167 | 19.692 | -1.120 | -6.994 | 5.514 |
| travel_day | ratio | 1.256 | 1.171 | 1.322 | 1.220 | 1.167 | 1.287 | -0.036 | -0.127 | 0.072 |
| person | difference | 21.051 | 16.822 | 24.562 | 21.462 | 17.321 | 26.707 | 0.411 | -5.124 | 7.964 |
| person | ratio | 1.411 | 1.317 | 1.497 | 1.383 | 1.294 | 1.493 | -0.028 | -0.155 | 0.132 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Collapsed joint cells

- travel_day: 39.01% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.52% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|dense|0` → `q4|dense|1`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2358 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2450 | 0 | 1.326 | -6.631 | 7.873 |
| 2008 | M0 | income:q3 | 2836 | 0 | 5.717 | -1.926 | 13.479 |
| 2008 | M0 | income:q4 | 2960 | 0 | 6.876 | -0.794 | 16.102 |
| 2008 | M0 | income:q5 | 3881 | 0 | 21.603 | 12.293 | 29.574 |
| 2008 | M1 | income:q1 | 2358 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2450 | 0 | 1.366 | -6.247 | 8.484 |
| 2008 | M1 | income:q3 | 2836 | 0 | 6.066 | -1.739 | 13.720 |
| 2008 | M1 | income:q4 | 2960 | 0 | 7.270 | -0.687 | 16.676 |
| 2008 | M1 | income:q5 | 3881 | 0 | 20.877 | 11.344 | 28.296 |
| 2008 | M2 | income:q1 | 2358 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2450 | 0 | 1.350 | -6.377 | 7.554 |
| 2008 | M2 | income:q3 | 2836 | 0 | 6.014 | -1.703 | 12.958 |
| 2008 | M2 | income:q4 | 2960 | 0 | 7.074 | -0.817 | 14.788 |
| 2008 | M2 | income:q5 | 3881 | 0 | 20.683 | 12.704 | 28.567 |
| 2019 | M0 | income:q1 | 0 | 1704 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1910 | 1.476 | -4.965 | 9.802 |
| 2019 | M0 | income:q3 | 0 | 1919 | 9.782 | 2.567 | 18.328 |
| 2019 | M0 | income:q4 | 0 | 2027 | 5.519 | -1.459 | 12.178 |
| 2019 | M0 | income:q5 | 0 | 2162 | 18.959 | 11.058 | 27.475 |
| 2019 | M1 | income:q1 | 0 | 1704 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1910 | 2.967 | -3.940 | 11.188 |
| 2019 | M1 | income:q3 | 0 | 1919 | 11.153 | 3.759 | 19.704 |
| 2019 | M1 | income:q4 | 0 | 2027 | 6.619 | -0.658 | 13.527 |
| 2019 | M1 | income:q5 | 0 | 2162 | 18.506 | 11.205 | 26.723 |
| 2019 | M2 | income:q1 | 0 | 1704 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1910 | 2.841 | -3.835 | 11.553 |
| 2019 | M2 | income:q3 | 0 | 1919 | 10.676 | 3.393 | 19.450 |
| 2019 | M2 | income:q4 | 0 | 2027 | 5.816 | -1.130 | 12.878 |
| 2019 | M2 | income:q5 | 0 | 2162 | 17.525 | 10.208 | 26.334 |
| pooled | pooled | income:q1 | 2358 | 1704 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2450 | 1910 | 1.639 | -6.427 | 8.942 |
| pooled | pooled | income:q3 | 2836 | 1919 | 6.385 | -1.048 | 14.395 |
| pooled | pooled | income:q4 | 2960 | 2027 | 7.048 | -0.608 | 14.910 |
| pooled | pooled | income:q5 | 3881 | 2162 | 20.691 | 11.660 | 28.704 |
| pooled | pooled | survey:2019*income:q2 | 2450 | 1910 | 0.478 | -8.804 | 12.342 |
| pooled | pooled | survey:2019*income:q3 | 2836 | 1919 | 3.601 | -4.197 | 15.393 |
| pooled | pooled | survey:2019*income:q4 | 2960 | 2027 | -1.494 | -10.612 | 9.326 |
| pooled | pooled | survey:2019*income:q5 | 3881 | 2162 | -2.577 | -11.135 | 8.023 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Quintile × density

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 381 | 68.672 | 61.321 | 77.499 | 342 | 76.685 | 70.724 | 83.597 | 1.117 | 0.986 | 1.253 |
| travel_day | q1 | intermediate | False | 868 | 67.293 | 62.727 | 72.507 | 827 | 71.392 | 66.351 | 77.149 | 1.061 | 0.967 | 1.175 |
| travel_day | q1 | sparse | False | 305 | 60.419 | 52.028 | 69.785 | 244 | 64.418 | 55.337 | 72.095 | 1.066 | 0.895 | 1.259 |
| travel_day | q1 | very_sparse | False | 804 | 60.033 | 55.739 | 64.418 | 291 | 69.844 | 60.849 | 78.944 | 1.163 | 1.019 | 1.336 |
| travel_day | q2 | dense | False | 272 | 72.138 | 62.350 | 82.690 | 200 | 82.281 | 73.498 | 91.850 | 1.141 | 0.988 | 1.350 |
| travel_day | q2 | intermediate | False | 894 | 66.917 | 62.482 | 72.634 | 858 | 74.080 | 68.639 | 80.178 | 1.107 | 1.013 | 1.207 |
| travel_day | q2 | sparse | False | 322 | 54.466 | 49.258 | 60.677 | 339 | 63.073 | 57.204 | 69.814 | 1.158 | 1.035 | 1.336 |
| travel_day | q2 | very_sparse | False | 962 | 67.432 | 61.694 | 73.879 | 513 | 69.365 | 63.403 | 76.084 | 1.029 | 0.929 | 1.136 |
| travel_day | q3 | dense | False | 338 | 70.943 | 63.388 | 78.297 | 197 | 103.458 | 77.149 | 136.218 | 1.458 | 1.086 | 1.899 |
| travel_day | q3 | intermediate | False | 1049 | 70.056 | 64.935 | 75.984 | 832 | 81.162 | 76.423 | 87.005 | 1.159 | 1.069 | 1.265 |
| travel_day | q3 | sparse | False | 396 | 71.300 | 61.887 | 84.512 | 314 | 72.519 | 64.781 | 81.450 | 1.017 | 0.847 | 1.182 |
| travel_day | q3 | very_sparse | False | 1053 | 66.959 | 62.790 | 71.271 | 576 | 79.735 | 73.589 | 86.279 | 1.191 | 1.096 | 1.314 |
| travel_day | q4 | dense | False | 373 | 67.348 | 60.482 | 74.785 | 246 | 77.755 | 70.553 | 86.261 | 1.155 | 1.023 | 1.301 |
| travel_day | q4 | intermediate | False | 1209 | 74.370 | 68.987 | 79.956 | 899 | 76.751 | 71.928 | 81.486 | 1.032 | 0.954 | 1.117 |
| travel_day | q4 | sparse | False | 404 | 66.806 | 59.506 | 75.147 | 361 | 68.611 | 61.703 | 77.052 | 1.027 | 0.884 | 1.196 |
| travel_day | q4 | very_sparse | False | 974 | 72.667 | 68.533 | 77.447 | 521 | 78.367 | 73.179 | 82.732 | 1.078 | 1.000 | 1.154 |
| travel_day | q5 | dense | False | 697 | 83.776 | 76.120 | 91.721 | 349 | 78.981 | 73.624 | 85.012 | 0.943 | 0.868 | 1.038 |
| travel_day | q5 | intermediate | False | 1839 | 84.739 | 79.671 | 90.019 | 1056 | 87.363 | 83.570 | 90.939 | 1.031 | 0.971 | 1.095 |
| travel_day | q5 | sparse | False | 435 | 73.006 | 66.072 | 80.588 | 318 | 81.829 | 73.055 | 91.693 | 1.121 | 0.987 | 1.266 |
| travel_day | q5 | very_sparse | False | 910 | 77.870 | 72.185 | 83.301 | 439 | 93.732 | 84.699 | 103.395 | 1.204 | 1.088 | 1.340 |
| person | q1 | dense | False | 473 | 61.081 | 53.993 | 68.459 | 476 | 68.771 | 61.683 | 76.409 | 1.126 | 0.977 | 1.302 |
| person | q1 | intermediate | False | 1159 | 53.159 | 48.876 | 57.613 | 1197 | 57.515 | 52.458 | 62.903 | 1.082 | 0.978 | 1.200 |
| person | q1 | sparse | False | 435 | 47.834 | 40.227 | 55.776 | 385 | 47.497 | 40.524 | 55.214 | 0.993 | 0.805 | 1.194 |
| person | q1 | very_sparse | False | 1292 | 41.331 | 37.586 | 44.204 | 446 | 50.815 | 42.396 | 57.904 | 1.229 | 1.045 | 1.422 |
| person | q2 | dense | False | 331 | 65.404 | 55.459 | 74.565 | 293 | 66.332 | 55.257 | 79.435 | 1.014 | 0.855 | 1.251 |
| person | q2 | intermediate | False | 1131 | 55.685 | 50.857 | 60.811 | 1191 | 62.485 | 57.462 | 68.901 | 1.122 | 1.006 | 1.234 |
| person | q2 | sparse | False | 427 | 42.378 | 36.442 | 48.038 | 456 | 52.305 | 45.091 | 59.423 | 1.234 | 1.068 | 1.456 |
| person | q2 | very_sparse | False | 1270 | 54.102 | 49.206 | 59.524 | 722 | 56.970 | 50.455 | 62.339 | 1.053 | 0.925 | 1.187 |
| person | q3 | dense | False | 418 | 61.469 | 54.855 | 68.669 | 284 | 87.266 | 62.616 | 115.152 | 1.420 | 1.033 | 1.866 |
| person | q3 | intermediate | False | 1298 | 59.818 | 55.531 | 65.672 | 1190 | 68.626 | 62.940 | 74.949 | 1.147 | 1.032 | 1.256 |
| person | q3 | sparse | False | 495 | 60.148 | 52.268 | 72.287 | 459 | 58.324 | 51.125 | 67.877 | 0.970 | 0.793 | 1.149 |
| person | q3 | very_sparse | False | 1404 | 53.917 | 50.245 | 57.721 | 809 | 68.372 | 61.702 | 75.549 | 1.268 | 1.136 | 1.403 |
| person | q4 | dense | False | 449 | 62.212 | 55.944 | 69.573 | 348 | 76.671 | 67.549 | 89.092 | 1.232 | 1.055 | 1.418 |
| person | q4 | intermediate | False | 1479 | 65.114 | 60.032 | 69.696 | 1291 | 67.360 | 61.657 | 72.485 | 1.034 | 0.947 | 1.135 |
| person | q4 | sparse | False | 497 | 61.086 | 54.594 | 68.995 | 514 | 58.415 | 50.374 | 66.915 | 0.956 | 0.816 | 1.127 |
| person | q4 | very_sparse | False | 1232 | 60.943 | 56.690 | 65.404 | 732 | 68.299 | 61.980 | 74.010 | 1.121 | 1.016 | 1.215 |
| person | q5 | dense | False | 860 | 73.825 | 66.987 | 82.020 | 497 | 74.913 | 68.580 | 83.003 | 1.015 | 0.917 | 1.150 |
| person | q5 | intermediate | False | 2201 | 77.149 | 71.913 | 81.930 | 1478 | 78.128 | 73.562 | 83.026 | 1.013 | 0.937 | 1.083 |
| person | q5 | sparse | False | 542 | 63.485 | 57.790 | 70.377 | 452 | 73.611 | 64.277 | 85.655 | 1.159 | 0.983 | 1.346 |
| person | q5 | very_sparse | False | 1149 | 64.832 | 59.184 | 69.753 | 605 | 82.181 | 73.637 | 93.105 | 1.268 | 1.131 | 1.437 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Conclusion grid

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.098 | inconclusive | 1.259 | 1.209 | 1.256 | 1.220 | 1.207 | 1.175 |
| travel_day | q2 | 1.086 | inconclusive | 1.259 | 1.209 | 1.256 | 1.220 | 1.207 | 1.175 |
| travel_day | q3 | 1.173 | inconclusive | 1.259 | 1.209 | 1.256 | 1.220 | 1.207 | 1.175 |
| travel_day | q4 | 1.055 | equivalent | 1.259 | 1.209 | 1.256 | 1.220 | 1.207 | 1.175 |
| travel_day | q5 | 1.054 | equivalent | 1.259 | 1.209 | 1.256 | 1.220 | 1.207 | 1.175 |
| person | q1 | 1.123 | inconclusive | 1.429 | 1.368 | 1.411 | 1.383 | 1.207 | 1.175 |
| person | q2 | 1.097 | inconclusive | 1.429 | 1.368 | 1.411 | 1.383 | 1.207 | 1.175 |
| person | q3 | 1.173 | inconclusive | 1.429 | 1.368 | 1.411 | 1.383 | 1.207 | 1.175 |
| person | q4 | 1.061 | equivalent | 1.429 | 1.368 | 1.411 | 1.383 | 1.207 | 1.175 |
| person | q5 | 1.076 | equivalent | 1.429 | 1.368 | 1.411 | 1.383 | 1.207 | 1.175 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

The positive income gradient survives density and car controls in both years.

## All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 624 |
| regression_M0 | 2019 | 13 | 0 | 0 | 531 |
| regression_M1 | 2008 | 16 | 0 | 0 | 624 |
| regression_M1 | 2019 | 16 | 0 | 0 | 531 |
| regression_M2 | 2008 | 18 | 0 | 0 | 624 |
| regression_M2 | 2019 | 18 | 0 | 0 | 531 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 23 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1897 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1360 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2380 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1714 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2565 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1704 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 531 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 13 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 47 | 0 | 0 | 75 |
| reweight_travel_day | 2019 | 47 | 0 | 0 | 50 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Levels and 2019/2008 ratios

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2380 | 60.287 | 57.948 | 62.814 | 1714 | 64.999 | 62.016 | 67.477 | 1.078 | 1.019 | 1.134 | equivalent | inconclusive |
| travel_day | q2 | 2481 | 60.878 | 58.214 | 63.785 | 1910 | 64.822 | 62.064 | 68.278 | 1.065 | 1.007 | 1.122 | equivalent | inconclusive |
| travel_day | q3 | 2891 | 62.795 | 60.228 | 65.643 | 1930 | 69.445 | 66.964 | 71.896 | 1.106 | 1.055 | 1.157 | inconclusive | inconclusive |
| travel_day | q4 | 3057 | 65.250 | 62.774 | 68.135 | 2091 | 69.649 | 67.003 | 72.295 | 1.067 | 1.016 | 1.118 | equivalent | inconclusive |
| travel_day | q5 | 3986 | 71.251 | 68.687 | 73.509 | 2190 | 75.379 | 72.759 | 77.867 | 1.058 | 1.013 | 1.104 | equivalent | inconclusive |
| person | q1 | 3359 | 45.117 | 42.870 | 47.435 | 2504 | 49.941 | 47.364 | 53.079 | 1.107 | 1.039 | 1.182 | inconclusive | inconclusive |
| person | q2 | 3159 | 48.564 | 45.956 | 51.000 | 2662 | 51.384 | 48.655 | 54.320 | 1.058 | 0.985 | 1.125 | equivalent | inconclusive |
| person | q3 | 3615 | 50.978 | 48.710 | 53.425 | 2742 | 55.980 | 53.495 | 58.714 | 1.098 | 1.034 | 1.160 | inconclusive | inconclusive |
| person | q4 | 3657 | 55.666 | 53.545 | 57.936 | 2885 | 59.170 | 56.125 | 62.113 | 1.063 | 1.002 | 1.125 | equivalent | inconclusive |
| person | q5 | 4752 | 59.754 | 57.415 | 62.163 | 3032 | 65.246 | 61.968 | 68.480 | 1.092 | 1.040 | 1.149 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Income gaps and their changes

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 10.965 | 6.939 | 14.427 | 10.380 | 6.379 | 14.042 | -0.585 | -6.416 | 4.891 |
| travel_day | ratio | 1.182 | 1.111 | 1.244 | 1.160 | 1.095 | 1.225 | -0.022 | -0.123 | 0.071 |
| person | difference | 14.637 | 11.106 | 17.753 | 15.304 | 11.261 | 19.827 | 0.667 | -4.486 | 6.168 |
| person | ratio | 1.324 | 1.238 | 1.406 | 1.306 | 1.221 | 1.409 | -0.018 | -0.141 | 0.114 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted levels and ratios

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2380 | 60.583 | 58.352 | 63.350 | 1714 | 64.535 | 61.728 | 67.178 | 1.065 | 1.005 | 1.118 | equivalent | inconclusive |
| travel_day | q2 | 2481 | 60.608 | 58.108 | 63.367 | 1910 | 65.029 | 62.386 | 68.217 | 1.073 | 1.017 | 1.126 | equivalent | inconclusive |
| travel_day | q3 | 2891 | 62.788 | 60.252 | 65.682 | 1930 | 69.481 | 67.007 | 71.916 | 1.107 | 1.054 | 1.161 | inconclusive | inconclusive |
| travel_day | q4 | 3057 | 65.276 | 62.831 | 68.156 | 2091 | 69.683 | 67.093 | 72.565 | 1.068 | 1.019 | 1.119 | equivalent | inconclusive |
| travel_day | q5 | 3986 | 71.339 | 68.868 | 73.600 | 2190 | 75.538 | 73.026 | 78.084 | 1.059 | 1.013 | 1.100 | equivalent | inconclusive |
| person | q1 | 3359 | 45.923 | 43.628 | 48.236 | 2504 | 49.233 | 46.733 | 52.359 | 1.072 | 1.002 | 1.146 | equivalent | inconclusive |
| person | q2 | 3159 | 48.262 | 45.864 | 50.851 | 2662 | 51.549 | 48.704 | 54.324 | 1.068 | 0.998 | 1.136 | equivalent | inconclusive |
| person | q3 | 3615 | 50.952 | 48.816 | 53.365 | 2742 | 56.000 | 53.697 | 58.733 | 1.099 | 1.034 | 1.160 | inconclusive | inconclusive |
| person | q4 | 3657 | 55.651 | 53.465 | 57.946 | 2885 | 59.312 | 56.251 | 62.417 | 1.066 | 1.004 | 1.129 | equivalent | inconclusive |
| person | q5 | 4752 | 59.952 | 57.746 | 62.201 | 3032 | 65.170 | 62.045 | 68.272 | 1.087 | 1.035 | 1.145 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted gaps

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 10.757 | 6.641 | 13.920 | 11.002 | 6.904 | 14.593 | 0.246 | -5.619 | 5.763 |
| travel_day | ratio | 1.178 | 1.105 | 1.236 | 1.170 | 1.105 | 1.237 | -0.007 | -0.108 | 0.094 |
| person | difference | 14.029 | 10.352 | 17.113 | 15.938 | 11.736 | 20.499 | 1.909 | -3.192 | 7.422 |
| person | ratio | 1.305 | 1.216 | 1.389 | 1.324 | 1.231 | 1.435 | 0.018 | -0.100 | 0.152 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Collapsed joint cells

- travel_day: 38.91% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.55% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|dense|0` → `q4|dense|1`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2380 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2481 | 0 | 0.462 | -5.956 | 5.658 |
| 2008 | M0 | income:q3 | 2891 | 0 | 2.213 | -4.203 | 8.048 |
| 2008 | M0 | income:q4 | 3057 | 0 | 4.814 | -1.615 | 11.820 |
| 2008 | M0 | income:q5 | 3986 | 0 | 14.723 | 7.629 | 21.536 |
| 2008 | M1 | income:q1 | 2380 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2481 | 0 | 0.700 | -5.395 | 6.181 |
| 2008 | M1 | income:q3 | 2891 | 0 | 2.625 | -3.719 | 8.749 |
| 2008 | M1 | income:q4 | 3057 | 0 | 5.437 | -1.135 | 12.814 |
| 2008 | M1 | income:q5 | 3986 | 0 | 14.034 | 6.829 | 20.739 |
| 2008 | M2 | income:q1 | 2380 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2481 | 0 | 1.160 | -5.502 | 6.465 |
| 2008 | M2 | income:q3 | 2891 | 0 | 3.233 | -2.923 | 9.227 |
| 2008 | M2 | income:q4 | 3057 | 0 | 5.976 | -0.752 | 12.952 |
| 2008 | M2 | income:q5 | 3986 | 0 | 14.757 | 7.722 | 21.914 |
| 2019 | M0 | income:q1 | 0 | 1714 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1910 | 3.138 | -3.298 | 9.224 |
| 2019 | M0 | income:q3 | 0 | 1930 | 8.103 | 1.571 | 14.644 |
| 2019 | M0 | income:q4 | 0 | 2091 | 9.392 | 2.459 | 15.848 |
| 2019 | M0 | income:q5 | 0 | 2190 | 17.146 | 10.134 | 25.220 |
| 2019 | M1 | income:q1 | 0 | 1714 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1910 | 4.940 | -1.947 | 11.473 |
| 2019 | M1 | income:q3 | 0 | 1930 | 9.952 | 3.694 | 16.613 |
| 2019 | M1 | income:q4 | 0 | 2091 | 10.652 | 3.326 | 17.501 |
| 2019 | M1 | income:q5 | 0 | 2190 | 16.575 | 9.637 | 25.039 |
| 2019 | M2 | income:q1 | 0 | 1714 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1910 | 4.952 | -2.183 | 11.545 |
| 2019 | M2 | income:q3 | 0 | 1930 | 9.653 | 3.501 | 17.356 |
| 2019 | M2 | income:q4 | 0 | 2091 | 10.027 | 3.141 | 16.991 |
| 2019 | M2 | income:q5 | 0 | 2190 | 15.820 | 9.049 | 24.607 |
| pooled | pooled | income:q1 | 2380 | 1714 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2481 | 1910 | 1.319 | -5.638 | 7.170 |
| pooled | pooled | income:q3 | 2891 | 1930 | 3.328 | -3.668 | 10.083 |
| pooled | pooled | income:q4 | 3057 | 2091 | 5.777 | -0.928 | 13.166 |
| pooled | pooled | income:q5 | 3986 | 2190 | 14.332 | 6.664 | 21.532 |
| pooled | pooled | survey:2019*income:q2 | 2481 | 1910 | 2.897 | -4.448 | 14.171 |
| pooled | pooled | survey:2019*income:q3 | 2891 | 1930 | 5.692 | -2.222 | 17.995 |
| pooled | pooled | survey:2019*income:q4 | 3057 | 2091 | 3.805 | -5.419 | 14.770 |
| pooled | pooled | survey:2019*income:q5 | 3986 | 2190 | 1.488 | -7.221 | 11.817 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Quintile × density

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 391 | 64.871 | 58.411 | 72.375 | 344 | 69.606 | 64.443 | 75.403 | 1.073 | 0.959 | 1.192 |
| travel_day | q1 | intermediate | False | 889 | 62.567 | 58.264 | 67.868 | 828 | 66.791 | 62.241 | 72.614 | 1.068 | 0.976 | 1.168 |
| travel_day | q1 | sparse | False | 304 | 55.343 | 49.389 | 62.606 | 247 | 57.767 | 50.659 | 64.826 | 1.044 | 0.884 | 1.205 |
| travel_day | q1 | very_sparse | False | 796 | 55.991 | 52.361 | 60.046 | 295 | 61.176 | 54.189 | 67.971 | 1.093 | 0.974 | 1.222 |
| travel_day | q2 | dense | False | 277 | 71.626 | 60.394 | 81.944 | 203 | 75.120 | 66.335 | 82.797 | 1.049 | 0.905 | 1.235 |
| travel_day | q2 | intermediate | False | 908 | 60.904 | 57.268 | 64.844 | 858 | 67.790 | 63.901 | 72.830 | 1.113 | 1.034 | 1.196 |
| travel_day | q2 | sparse | False | 335 | 51.550 | 46.484 | 56.347 | 334 | 54.544 | 49.621 | 59.581 | 1.058 | 0.958 | 1.185 |
| travel_day | q2 | very_sparse | False | 961 | 61.387 | 57.216 | 65.939 | 515 | 63.560 | 58.444 | 69.262 | 1.035 | 0.945 | 1.140 |
| travel_day | q3 | dense | False | 352 | 65.698 | 59.430 | 71.434 | 197 | 74.547 | 67.600 | 81.457 | 1.135 | 1.032 | 1.266 |
| travel_day | q3 | intermediate | False | 1080 | 63.005 | 59.688 | 67.125 | 845 | 71.704 | 67.552 | 76.381 | 1.138 | 1.054 | 1.222 |
| travel_day | q3 | sparse | False | 401 | 60.352 | 54.100 | 71.926 | 316 | 65.756 | 59.063 | 71.164 | 1.090 | 0.913 | 1.231 |
| travel_day | q3 | very_sparse | False | 1058 | 62.820 | 58.795 | 67.896 | 572 | 66.515 | 61.636 | 71.288 | 1.059 | 0.978 | 1.163 |
| travel_day | q4 | dense | False | 386 | 61.798 | 56.648 | 67.052 | 258 | 73.594 | 67.832 | 80.856 | 1.191 | 1.063 | 1.306 |
| travel_day | q4 | intermediate | False | 1257 | 67.145 | 63.087 | 71.642 | 931 | 72.259 | 68.228 | 76.357 | 1.076 | 0.996 | 1.155 |
| travel_day | q4 | sparse | False | 425 | 61.682 | 55.206 | 68.911 | 360 | 60.436 | 54.162 | 67.127 | 0.980 | 0.854 | 1.133 |
| travel_day | q4 | very_sparse | False | 989 | 66.632 | 62.417 | 71.708 | 542 | 70.385 | 66.107 | 74.574 | 1.056 | 0.978 | 1.134 |
| travel_day | q5 | dense | False | 727 | 73.402 | 67.842 | 79.691 | 358 | 74.439 | 69.667 | 79.258 | 1.014 | 0.935 | 1.108 |
| travel_day | q5 | intermediate | False | 1902 | 73.285 | 69.821 | 76.641 | 1076 | 78.534 | 75.046 | 82.303 | 1.072 | 1.016 | 1.138 |
| travel_day | q5 | sparse | False | 432 | 63.951 | 58.300 | 68.982 | 318 | 68.314 | 60.490 | 75.773 | 1.068 | 0.937 | 1.202 |
| travel_day | q5 | very_sparse | False | 925 | 69.562 | 64.269 | 75.328 | 438 | 73.832 | 67.832 | 80.096 | 1.061 | 0.956 | 1.164 |
| person | q1 | dense | False | 473 | 55.547 | 49.322 | 62.295 | 476 | 60.613 | 53.953 | 67.324 | 1.091 | 0.958 | 1.242 |
| person | q1 | intermediate | False | 1159 | 48.447 | 44.535 | 52.847 | 1197 | 51.846 | 47.345 | 56.922 | 1.070 | 0.956 | 1.189 |
| person | q1 | sparse | False | 435 | 40.280 | 34.262 | 47.654 | 385 | 41.002 | 34.489 | 47.893 | 1.018 | 0.840 | 1.219 |
| person | q1 | very_sparse | False | 1292 | 36.694 | 33.379 | 39.984 | 446 | 42.712 | 36.936 | 48.892 | 1.164 | 0.989 | 1.364 |
| person | q2 | dense | False | 331 | 63.709 | 53.732 | 72.875 | 293 | 57.204 | 49.620 | 65.735 | 0.898 | 0.756 | 1.070 |
| person | q2 | intermediate | False | 1131 | 48.930 | 45.378 | 52.758 | 1191 | 54.511 | 49.993 | 59.604 | 1.114 | 1.016 | 1.216 |
| person | q2 | sparse | False | 427 | 39.790 | 34.339 | 44.354 | 456 | 42.824 | 37.783 | 48.343 | 1.076 | 0.941 | 1.259 |
| person | q2 | very_sparse | False | 1270 | 47.241 | 42.973 | 50.968 | 722 | 50.292 | 44.795 | 55.176 | 1.065 | 0.965 | 1.180 |
| person | q3 | dense | False | 418 | 53.200 | 46.699 | 58.365 | 284 | 56.891 | 48.001 | 66.896 | 1.069 | 0.893 | 1.251 |
| person | q3 | intermediate | False | 1298 | 53.184 | 50.198 | 57.540 | 1190 | 58.947 | 53.960 | 63.727 | 1.108 | 1.017 | 1.205 |
| person | q3 | sparse | False | 495 | 48.410 | 42.646 | 57.979 | 459 | 51.406 | 45.205 | 57.387 | 1.062 | 0.868 | 1.228 |
| person | q3 | very_sparse | False | 1404 | 48.462 | 44.866 | 52.400 | 809 | 54.303 | 49.167 | 59.621 | 1.121 | 1.014 | 1.239 |
| person | q4 | dense | False | 449 | 54.289 | 49.168 | 60.058 | 348 | 66.262 | 59.205 | 73.848 | 1.221 | 1.070 | 1.394 |
| person | q4 | intermediate | False | 1479 | 57.285 | 53.905 | 61.145 | 1291 | 61.479 | 56.301 | 66.380 | 1.073 | 0.970 | 1.174 |
| person | q4 | sparse | False | 497 | 55.097 | 48.946 | 61.609 | 514 | 49.016 | 42.163 | 55.467 | 0.890 | 0.760 | 1.039 |
| person | q4 | very_sparse | False | 1232 | 54.072 | 49.860 | 59.427 | 732 | 60.117 | 55.154 | 66.035 | 1.112 | 1.004 | 1.239 |
| person | q5 | dense | False | 860 | 61.607 | 56.602 | 68.420 | 497 | 68.100 | 61.578 | 74.825 | 1.105 | 1.006 | 1.227 |
| person | q5 | intermediate | False | 2201 | 63.763 | 60.035 | 67.302 | 1478 | 67.732 | 63.593 | 72.183 | 1.062 | 0.986 | 1.143 |
| person | q5 | sparse | False | 542 | 50.884 | 45.907 | 55.969 | 452 | 58.568 | 49.914 | 66.520 | 1.151 | 0.972 | 1.322 |
| person | q5 | very_sparse | False | 1149 | 55.206 | 50.097 | 59.792 | 605 | 61.021 | 54.720 | 66.853 | 1.105 | 0.980 | 1.232 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Conclusion grid

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.078 | equivalent | 1.182 | 1.160 | 1.178 | 1.170 | 1.148 | 1.158 |
| travel_day | q2 | 1.065 | equivalent | 1.182 | 1.160 | 1.178 | 1.170 | 1.148 | 1.158 |
| travel_day | q3 | 1.106 | inconclusive | 1.182 | 1.160 | 1.178 | 1.170 | 1.148 | 1.158 |
| travel_day | q4 | 1.067 | equivalent | 1.182 | 1.160 | 1.178 | 1.170 | 1.148 | 1.158 |
| travel_day | q5 | 1.058 | equivalent | 1.182 | 1.160 | 1.178 | 1.170 | 1.148 | 1.158 |
| person | q1 | 1.107 | inconclusive | 1.324 | 1.306 | 1.305 | 1.324 | 1.148 | 1.158 |
| person | q2 | 1.058 | equivalent | 1.324 | 1.306 | 1.305 | 1.324 | 1.148 | 1.158 |
| person | q3 | 1.098 | inconclusive | 1.324 | 1.306 | 1.305 | 1.324 | 1.148 | 1.158 |
| person | q4 | 1.063 | equivalent | 1.324 | 1.306 | 1.305 | 1.324 | 1.148 | 1.158 |
| person | q5 | 1.092 | equivalent | 1.324 | 1.306 | 1.305 | 1.324 | 1.148 | 1.158 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


The positive income gradient survives density and car controls in both years.

## All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 639 |
| regression_M0 | 2019 | 13 | 0 | 0 | 546 |
| regression_M1 | 2008 | 16 | 0 | 0 | 639 |
| regression_M1 | 2019 | 16 | 0 | 0 | 546 |
| regression_M2 | 2008 | 18 | 0 | 0 | 639 |
| regression_M2 | 2019 | 18 | 0 | 0 | 546 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 24 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1944 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1400 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2406 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1743 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 11 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2625 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1735 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 546 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 13 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 48 | 0 | 0 | 76 |
| reweight_travel_day | 2019 | 48 | 0 | 0 | 50 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Levels and 2019/2008 ratios

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2406 | 62.665 | 60.112 | 65.839 | 1743 | 67.662 | 64.128 | 70.957 | 1.080 | 1.005 | 1.143 | equivalent | inconclusive |
| travel_day | q2 | 2515 | 64.726 | 61.846 | 68.599 | 1940 | 69.318 | 65.576 | 73.746 | 1.071 | 1.004 | 1.140 | equivalent | inconclusive |
| travel_day | q3 | 2954 | 67.893 | 64.825 | 71.667 | 1981 | 78.509 | 74.021 | 83.263 | 1.156 | 1.084 | 1.222 | inconclusive | inconclusive |
| travel_day | q4 | 3143 | 70.934 | 67.408 | 74.125 | 2142 | 73.963 | 71.124 | 77.108 | 1.043 | 0.992 | 1.100 | equivalent | equivalent |
| travel_day | q5 | 4150 | 81.714 | 78.075 | 85.245 | 2283 | 82.857 | 79.727 | 85.470 | 1.014 | 0.970 | 1.059 | equivalent | equivalent |
| person | q1 | 3359 | 47.305 | 44.790 | 49.618 | 2504 | 52.775 | 49.878 | 56.280 | 1.116 | 1.034 | 1.204 | inconclusive | inconclusive |
| person | q2 | 3159 | 52.647 | 49.846 | 56.040 | 2662 | 56.137 | 52.257 | 60.073 | 1.066 | 0.982 | 1.142 | equivalent | inconclusive |
| person | q3 | 3615 | 56.256 | 53.270 | 60.103 | 2742 | 64.943 | 60.468 | 69.508 | 1.154 | 1.074 | 1.246 | inconclusive | inconclusive |
| person | q4 | 3657 | 61.929 | 58.759 | 64.940 | 2885 | 64.829 | 61.475 | 68.114 | 1.047 | 0.989 | 1.106 | equivalent | inconclusive |
| person | q5 | 4752 | 71.450 | 68.213 | 75.078 | 3032 | 74.438 | 70.812 | 77.778 | 1.042 | 0.982 | 1.090 | equivalent | equivalent |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Income gaps and their changes

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 19.048 | 14.738 | 22.965 | 15.196 | 10.252 | 19.223 | -3.853 | -10.739 | 2.774 |
| travel_day | ratio | 1.304 | 1.226 | 1.378 | 1.225 | 1.148 | 1.295 | -0.079 | -0.195 | 0.036 |
| person | difference | 24.145 | 19.660 | 28.353 | 21.663 | 16.924 | 25.948 | -2.482 | -9.802 | 4.057 |
| person | ratio | 1.510 | 1.405 | 1.621 | 1.410 | 1.305 | 1.510 | -0.100 | -0.277 | 0.059 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted levels and ratios

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2406 | 62.827 | 60.168 | 65.812 | 1743 | 67.194 | 63.751 | 70.290 | 1.069 | 0.998 | 1.130 | equivalent | inconclusive |
| travel_day | q2 | 2515 | 64.554 | 61.776 | 68.391 | 1940 | 69.484 | 65.828 | 73.980 | 1.076 | 1.009 | 1.139 | equivalent | inconclusive |
| travel_day | q3 | 2954 | 67.930 | 64.905 | 71.695 | 1981 | 78.862 | 74.150 | 83.702 | 1.161 | 1.082 | 1.234 | inconclusive | inconclusive |
| travel_day | q4 | 3143 | 70.809 | 67.233 | 73.921 | 2142 | 74.022 | 71.339 | 77.115 | 1.045 | 0.993 | 1.102 | equivalent | inconclusive |
| travel_day | q5 | 4150 | 81.661 | 78.264 | 85.090 | 2283 | 83.150 | 79.778 | 85.814 | 1.018 | 0.975 | 1.063 | equivalent | equivalent |
| person | q1 | 3359 | 48.079 | 45.439 | 50.610 | 2504 | 52.011 | 49.008 | 55.227 | 1.082 | 1.001 | 1.161 | inconclusive | inconclusive |
| person | q2 | 3159 | 52.399 | 49.524 | 55.645 | 2662 | 56.331 | 52.389 | 60.101 | 1.075 | 0.985 | 1.149 | equivalent | inconclusive |
| person | q3 | 3615 | 56.200 | 53.300 | 59.872 | 2742 | 65.312 | 60.700 | 69.997 | 1.162 | 1.077 | 1.259 | inconclusive | inconclusive |
| person | q4 | 3657 | 61.824 | 58.635 | 64.861 | 2885 | 65.012 | 61.614 | 68.296 | 1.052 | 0.994 | 1.111 | equivalent | inconclusive |
| person | q5 | 4752 | 71.511 | 68.338 | 75.111 | 3032 | 74.475 | 70.805 | 77.968 | 1.041 | 0.982 | 1.091 | equivalent | equivalent |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted gaps

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 18.834 | 14.471 | 22.769 | 15.956 | 11.049 | 20.098 | -2.878 | -9.673 | 3.959 |
| travel_day | ratio | 1.300 | 1.221 | 1.374 | 1.237 | 1.160 | 1.309 | -0.062 | -0.180 | 0.055 |
| person | difference | 23.432 | 19.220 | 27.526 | 22.465 | 17.527 | 27.114 | -0.967 | -8.409 | 5.600 |
| person | ratio | 1.487 | 1.380 | 1.592 | 1.432 | 1.323 | 1.540 | -0.055 | -0.237 | 0.104 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Collapsed joint cells

- travel_day: 36.82% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.55% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2406 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2515 | 0 | 1.491 | -5.973 | 7.180 |
| 2008 | M0 | income:q3 | 2954 | 0 | 4.049 | -2.716 | 10.043 |
| 2008 | M0 | income:q4 | 3143 | 0 | 6.415 | -0.640 | 13.444 |
| 2008 | M0 | income:q5 | 4150 | 0 | 21.863 | 14.262 | 29.570 |
| 2008 | M1 | income:q1 | 2406 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2515 | 0 | 1.674 | -5.760 | 7.607 |
| 2008 | M1 | income:q3 | 2954 | 0 | 4.436 | -2.375 | 10.716 |
| 2008 | M1 | income:q4 | 3143 | 0 | 6.996 | -0.400 | 14.313 |
| 2008 | M1 | income:q5 | 4150 | 0 | 21.278 | 13.748 | 28.668 |
| 2008 | M2 | income:q1 | 2406 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2515 | 0 | 1.936 | -5.414 | 8.053 |
| 2008 | M2 | income:q3 | 2954 | 0 | 4.774 | -1.923 | 11.081 |
| 2008 | M2 | income:q4 | 3143 | 0 | 7.223 | 0.170 | 14.324 |
| 2008 | M2 | income:q5 | 4150 | 0 | 21.627 | 13.739 | 29.148 |
| 2019 | M0 | income:q1 | 0 | 1743 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1940 | 3.850 | -3.553 | 10.351 |
| 2019 | M0 | income:q3 | 0 | 1981 | 11.452 | 4.446 | 19.213 |
| 2019 | M0 | income:q4 | 0 | 2142 | 10.356 | 3.287 | 16.396 |
| 2019 | M0 | income:q5 | 0 | 2283 | 20.505 | 12.761 | 28.303 |
| 2019 | M1 | income:q1 | 0 | 1743 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1940 | 5.581 | -1.651 | 12.474 |
| 2019 | M1 | income:q3 | 0 | 1981 | 13.220 | 6.257 | 21.359 |
| 2019 | M1 | income:q4 | 0 | 2142 | 11.544 | 4.175 | 18.083 |
| 2019 | M1 | income:q5 | 0 | 2283 | 19.957 | 12.203 | 28.150 |
| 2019 | M2 | income:q1 | 0 | 1743 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1940 | 5.351 | -2.132 | 11.848 |
| 2019 | M2 | income:q3 | 0 | 1981 | 12.541 | 5.942 | 20.643 |
| 2019 | M2 | income:q4 | 0 | 2142 | 10.497 | 3.177 | 17.616 |
| 2019 | M2 | income:q5 | 0 | 2283 | 18.756 | 10.245 | 26.796 |
| pooled | pooled | income:q1 | 2406 | 1743 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2515 | 1940 | 2.262 | -5.435 | 8.252 |
| pooled | pooled | income:q3 | 2954 | 1981 | 5.138 | -1.369 | 11.066 |
| pooled | pooled | income:q4 | 3143 | 2142 | 7.505 | -0.014 | 15.073 |
| pooled | pooled | income:q5 | 4150 | 2283 | 21.610 | 13.637 | 28.841 |
| pooled | pooled | survey:2019*income:q2 | 2515 | 1940 | 2.214 | -6.514 | 13.200 |
| pooled | pooled | survey:2019*income:q3 | 2954 | 1981 | 6.351 | -1.107 | 19.932 |
| pooled | pooled | survey:2019*income:q4 | 3143 | 2142 | 2.317 | -6.497 | 13.001 |
| pooled | pooled | survey:2019*income:q5 | 4150 | 2283 | -2.482 | -11.533 | 7.367 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Quintile × density

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 395 | 66.460 | 60.201 | 73.903 | 348 | 71.330 | 65.546 | 77.564 | 1.073 | 0.966 | 1.208 |
| travel_day | q1 | intermediate | False | 897 | 63.732 | 59.618 | 68.947 | 844 | 70.151 | 64.449 | 77.645 | 1.101 | 0.994 | 1.218 |
| travel_day | q1 | sparse | False | 306 | 59.690 | 52.031 | 68.998 | 250 | 58.603 | 51.526 | 65.481 | 0.982 | 0.826 | 1.130 |
| travel_day | q1 | very_sparse | False | 808 | 59.902 | 55.981 | 64.532 | 301 | 64.927 | 58.195 | 71.734 | 1.084 | 0.950 | 1.213 |
| travel_day | q2 | dense | False | 280 | 71.732 | 60.462 | 81.952 | 207 | 77.823 | 68.190 | 86.686 | 1.085 | 0.938 | 1.285 |
| travel_day | q2 | intermediate | False | 923 | 66.063 | 61.272 | 72.190 | 874 | 72.075 | 66.834 | 77.596 | 1.091 | 1.003 | 1.199 |
| travel_day | q2 | sparse | False | 337 | 54.198 | 48.925 | 59.796 | 336 | 60.883 | 50.926 | 72.604 | 1.123 | 0.937 | 1.334 |
| travel_day | q2 | very_sparse | False | 975 | 65.565 | 60.474 | 71.955 | 523 | 67.596 | 61.052 | 74.251 | 1.031 | 0.916 | 1.144 |
| travel_day | q3 | dense | False | 360 | 73.069 | 64.745 | 81.846 | 207 | 107.868 | 81.721 | 141.761 | 1.476 | 1.121 | 1.877 |
| travel_day | q3 | intermediate | False | 1096 | 66.624 | 62.749 | 71.183 | 858 | 77.193 | 72.911 | 82.282 | 1.159 | 1.075 | 1.253 |
| travel_day | q3 | sparse | False | 410 | 67.907 | 58.956 | 80.853 | 324 | 70.616 | 63.492 | 77.908 | 1.040 | 0.869 | 1.184 |
| travel_day | q3 | very_sparse | False | 1088 | 67.558 | 62.504 | 72.686 | 592 | 74.606 | 68.620 | 82.514 | 1.104 | 0.998 | 1.230 |
| travel_day | q4 | dense | False | 395 | 64.855 | 59.279 | 71.340 | 268 | 81.061 | 71.804 | 93.416 | 1.250 | 1.070 | 1.417 |
| travel_day | q4 | intermediate | False | 1286 | 72.535 | 67.166 | 77.792 | 953 | 76.093 | 71.275 | 80.686 | 1.049 | 0.963 | 1.147 |
| travel_day | q4 | sparse | False | 438 | 65.496 | 58.654 | 73.372 | 369 | 63.295 | 57.119 | 71.612 | 0.966 | 0.832 | 1.120 |
| travel_day | q4 | very_sparse | False | 1024 | 75.678 | 68.567 | 84.050 | 552 | 74.841 | 69.664 | 80.417 | 0.989 | 0.896 | 1.096 |
| travel_day | q5 | dense | False | 763 | 85.523 | 77.454 | 94.208 | 370 | 78.877 | 73.164 | 85.336 | 0.922 | 0.831 | 1.021 |
| travel_day | q5 | intermediate | False | 1961 | 82.496 | 77.951 | 87.394 | 1118 | 85.343 | 80.939 | 89.925 | 1.035 | 0.967 | 1.099 |
| travel_day | q5 | sparse | False | 453 | 74.226 | 66.740 | 82.078 | 331 | 75.222 | 65.610 | 84.264 | 1.013 | 0.867 | 1.142 |
| travel_day | q5 | very_sparse | False | 973 | 82.129 | 74.303 | 90.424 | 464 | 87.627 | 79.907 | 97.110 | 1.067 | 0.960 | 1.198 |
| person | q1 | dense | False | 473 | 57.620 | 50.981 | 64.680 | 476 | 62.513 | 55.859 | 69.707 | 1.085 | 0.958 | 1.244 |
| person | q1 | intermediate | False | 1159 | 49.777 | 45.511 | 54.225 | 1197 | 55.582 | 50.277 | 62.273 | 1.117 | 0.999 | 1.246 |
| person | q1 | sparse | False | 435 | 43.615 | 36.817 | 52.870 | 385 | 41.913 | 35.351 | 49.003 | 0.961 | 0.791 | 1.185 |
| person | q1 | very_sparse | False | 1292 | 39.634 | 35.913 | 43.267 | 446 | 46.132 | 40.518 | 52.924 | 1.164 | 1.014 | 1.357 |
| person | q2 | dense | False | 331 | 64.024 | 54.097 | 73.375 | 293 | 60.811 | 51.436 | 69.155 | 0.950 | 0.796 | 1.154 |
| person | q2 | intermediate | False | 1131 | 54.650 | 50.722 | 59.887 | 1191 | 59.389 | 53.987 | 64.684 | 1.087 | 0.975 | 1.201 |
| person | q2 | sparse | False | 427 | 42.048 | 36.295 | 47.082 | 456 | 48.386 | 38.556 | 58.153 | 1.151 | 0.934 | 1.386 |
| person | q2 | very_sparse | False | 1270 | 51.469 | 47.036 | 56.854 | 722 | 54.648 | 48.205 | 60.754 | 1.062 | 0.937 | 1.186 |
| person | q3 | dense | False | 418 | 61.826 | 53.989 | 70.657 | 284 | 87.461 | 61.637 | 114.935 | 1.415 | 1.040 | 1.885 |
| person | q3 | intermediate | False | 1298 | 56.731 | 53.027 | 61.240 | 1190 | 64.513 | 59.537 | 70.562 | 1.137 | 1.037 | 1.255 |
| person | q3 | sparse | False | 495 | 56.083 | 48.256 | 68.177 | 459 | 56.053 | 49.166 | 63.385 | 0.999 | 0.819 | 1.171 |
| person | q3 | very_sparse | False | 1404 | 53.322 | 48.758 | 58.041 | 809 | 63.059 | 56.017 | 71.169 | 1.183 | 1.053 | 1.344 |
| person | q4 | dense | False | 449 | 58.442 | 53.223 | 65.069 | 348 | 77.887 | 68.284 | 91.535 | 1.333 | 1.145 | 1.569 |
| person | q4 | intermediate | False | 1479 | 63.050 | 58.077 | 67.917 | 1291 | 66.604 | 61.429 | 72.179 | 1.056 | 0.963 | 1.160 |
| person | q4 | sparse | False | 497 | 59.979 | 53.686 | 67.741 | 514 | 52.638 | 45.818 | 59.532 | 0.878 | 0.753 | 1.028 |
| person | q4 | very_sparse | False | 1232 | 63.158 | 56.479 | 70.262 | 732 | 65.273 | 59.117 | 71.858 | 1.033 | 0.925 | 1.171 |
| person | q5 | dense | False | 860 | 74.714 | 67.042 | 83.654 | 497 | 74.346 | 67.384 | 81.260 | 0.995 | 0.901 | 1.122 |
| person | q5 | intermediate | False | 2201 | 74.507 | 69.740 | 79.311 | 1478 | 76.284 | 71.724 | 81.502 | 1.024 | 0.949 | 1.100 |
| person | q5 | sparse | False | 542 | 62.182 | 56.076 | 70.020 | 452 | 66.746 | 57.878 | 75.016 | 1.073 | 0.906 | 1.213 |
| person | q5 | very_sparse | False | 1149 | 68.352 | 61.018 | 76.023 | 605 | 76.404 | 68.438 | 85.223 | 1.118 | 0.979 | 1.279 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Conclusion grid

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.080 | equivalent | 1.304 | 1.225 | 1.300 | 1.237 | 1.216 | 1.188 |
| travel_day | q2 | 1.071 | equivalent | 1.304 | 1.225 | 1.300 | 1.237 | 1.216 | 1.188 |
| travel_day | q3 | 1.156 | inconclusive | 1.304 | 1.225 | 1.300 | 1.237 | 1.216 | 1.188 |
| travel_day | q4 | 1.043 | equivalent | 1.304 | 1.225 | 1.300 | 1.237 | 1.216 | 1.188 |
| travel_day | q5 | 1.014 | equivalent | 1.304 | 1.225 | 1.300 | 1.237 | 1.216 | 1.188 |
| person | q1 | 1.116 | inconclusive | 1.510 | 1.410 | 1.487 | 1.432 | 1.216 | 1.188 |
| person | q2 | 1.066 | equivalent | 1.510 | 1.410 | 1.487 | 1.432 | 1.216 | 1.188 |
| person | q3 | 1.154 | inconclusive | 1.510 | 1.410 | 1.487 | 1.432 | 1.216 | 1.188 |
| person | q4 | 1.047 | equivalent | 1.510 | 1.410 | 1.487 | 1.432 | 1.216 | 1.188 |
| person | q5 | 1.042 | equivalent | 1.510 | 1.410 | 1.487 | 1.432 | 1.216 | 1.188 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

The positive income gradient survives density and car controls in both years.

## All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 642 |
| regression_M0 | 2019 | 13 | 0 | 0 | 545 |
| regression_M1 | 2008 | 16 | 0 | 0 | 642 |
| regression_M1 | 2019 | 16 | 0 | 0 | 545 |
| regression_M2 | 2008 | 18 | 0 | 0 | 642 |
| regression_M2 | 2019 | 18 | 0 | 0 | 545 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 24 |
| regression_input_density | 2008 | 4 | 0 | 0 | 1960 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1395 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2481 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1781 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 10 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2650 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1759 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 545 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 13 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 48 | 0 | 0 | 78 |
| reweight_travel_day | 2019 | 48 | 0 | 0 | 50 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Levels and 2019/2008 ratios

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2481 | 63.963 | 61.198 | 67.002 | 1781 | 69.423 | 66.424 | 72.103 | 1.085 | 1.024 | 1.136 | equivalent | inconclusive |
| travel_day | q2 | 2558 | 63.741 | 61.004 | 66.796 | 1973 | 70.188 | 67.188 | 73.906 | 1.101 | 1.044 | 1.162 | inconclusive | inconclusive |
| travel_day | q3 | 2967 | 66.989 | 64.143 | 70.482 | 1980 | 75.854 | 72.891 | 78.625 | 1.132 | 1.075 | 1.179 | inconclusive | inconclusive |
| travel_day | q4 | 3114 | 69.147 | 66.781 | 71.772 | 2120 | 73.747 | 70.830 | 76.664 | 1.067 | 1.020 | 1.118 | equivalent | inconclusive |
| travel_day | q5 | 4048 | 75.962 | 73.152 | 78.578 | 2217 | 81.178 | 78.638 | 83.737 | 1.069 | 1.025 | 1.115 | equivalent | inconclusive |
| person | q1 | 3359 | 49.971 | 47.656 | 52.478 | 2504 | 55.206 | 52.248 | 58.083 | 1.105 | 1.038 | 1.172 | inconclusive | inconclusive |
| person | q2 | 3159 | 52.051 | 49.417 | 54.530 | 2662 | 57.508 | 54.386 | 60.548 | 1.105 | 1.037 | 1.174 | inconclusive | inconclusive |
| person | q3 | 3615 | 55.549 | 52.886 | 58.712 | 2742 | 62.604 | 59.706 | 65.839 | 1.127 | 1.052 | 1.194 | inconclusive | inconclusive |
| person | q4 | 3657 | 59.786 | 57.479 | 62.284 | 2885 | 63.465 | 60.103 | 67.275 | 1.062 | 0.996 | 1.126 | equivalent | inconclusive |
| person | q5 | 4752 | 64.679 | 62.196 | 67.022 | 3032 | 70.891 | 68.007 | 74.001 | 1.096 | 1.051 | 1.153 | inconclusive | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Income gaps and their changes

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 11.998 | 7.112 | 15.764 | 11.756 | 8.243 | 15.757 | -0.242 | -5.720 | 5.693 |
| travel_day | ratio | 1.188 | 1.106 | 1.252 | 1.169 | 1.115 | 1.234 | -0.018 | -0.106 | 0.086 |
| person | difference | 14.708 | 10.652 | 18.064 | 15.685 | 11.506 | 20.308 | 0.977 | -3.991 | 6.929 |
| person | ratio | 1.294 | 1.207 | 1.376 | 1.284 | 1.205 | 1.386 | -0.010 | -0.117 | 0.118 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted levels and ratios

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2481 | 64.335 | 61.606 | 67.488 | 1781 | 68.981 | 66.021 | 71.710 | 1.072 | 1.011 | 1.123 | equivalent | inconclusive |
| travel_day | q2 | 2558 | 63.492 | 60.715 | 66.511 | 1973 | 70.342 | 66.838 | 73.700 | 1.108 | 1.051 | 1.168 | inconclusive | inconclusive |
| travel_day | q3 | 2967 | 67.045 | 64.159 | 70.591 | 1980 | 75.825 | 73.002 | 78.568 | 1.131 | 1.074 | 1.179 | inconclusive | inconclusive |
| travel_day | q4 | 3114 | 69.138 | 66.623 | 71.686 | 2120 | 73.879 | 70.899 | 76.697 | 1.069 | 1.020 | 1.122 | equivalent | inconclusive |
| travel_day | q5 | 4048 | 76.075 | 73.364 | 78.610 | 2217 | 81.348 | 78.883 | 83.792 | 1.069 | 1.026 | 1.115 | equivalent | inconclusive |
| person | q1 | 3359 | 50.807 | 48.544 | 53.592 | 2504 | 54.625 | 51.637 | 57.553 | 1.075 | 1.005 | 1.138 | equivalent | inconclusive |
| person | q2 | 3159 | 51.752 | 49.111 | 54.226 | 2662 | 57.579 | 54.248 | 60.796 | 1.113 | 1.044 | 1.180 | inconclusive | inconclusive |
| person | q3 | 3615 | 55.538 | 53.002 | 58.661 | 2742 | 62.614 | 59.767 | 66.043 | 1.127 | 1.053 | 1.193 | inconclusive | inconclusive |
| person | q4 | 3657 | 59.804 | 57.397 | 62.383 | 2885 | 63.620 | 60.314 | 67.605 | 1.064 | 0.998 | 1.130 | equivalent | inconclusive |
| person | q5 | 4752 | 64.898 | 62.355 | 67.280 | 3032 | 70.799 | 67.955 | 73.921 | 1.091 | 1.045 | 1.150 | equivalent | inconclusive |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Reweighted gaps

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 11.740 | 7.119 | 15.286 | 12.367 | 8.771 | 16.467 | 0.627 | -4.511 | 6.737 |
| travel_day | ratio | 1.182 | 1.106 | 1.245 | 1.179 | 1.123 | 1.246 | -0.003 | -0.084 | 0.097 |
| person | difference | 14.090 | 10.032 | 17.489 | 16.173 | 12.326 | 21.071 | 2.083 | -2.484 | 8.268 |
| person | ratio | 1.277 | 1.190 | 1.358 | 1.296 | 1.221 | 1.395 | 0.019 | -0.077 | 0.161 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Collapsed joint cells

- travel_day: 37.14% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.55% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2481 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2558 | 0 | 0.503 | -6.424 | 7.686 |
| 2008 | M0 | income:q3 | 2967 | 0 | 3.931 | -2.611 | 11.579 |
| 2008 | M0 | income:q4 | 3114 | 0 | 6.478 | -0.262 | 14.734 |
| 2008 | M0 | income:q5 | 4048 | 0 | 16.179 | 7.789 | 23.021 |
| 2008 | M1 | income:q1 | 2481 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2558 | 0 | 0.602 | -6.285 | 8.160 |
| 2008 | M1 | income:q3 | 2967 | 0 | 4.219 | -2.657 | 11.580 |
| 2008 | M1 | income:q4 | 3114 | 0 | 6.957 | 0.357 | 14.995 |
| 2008 | M1 | income:q5 | 4048 | 0 | 15.331 | 6.678 | 22.143 |
| 2008 | M2 | income:q1 | 2481 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2558 | 0 | 0.732 | -5.652 | 7.128 |
| 2008 | M2 | income:q3 | 2967 | 0 | 4.371 | -3.048 | 11.624 |
| 2008 | M2 | income:q4 | 3114 | 0 | 7.014 | 0.139 | 14.414 |
| 2008 | M2 | income:q5 | 4048 | 0 | 15.441 | 7.601 | 22.451 |
| 2019 | M0 | income:q1 | 0 | 1781 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 1973 | 3.204 | -3.413 | 11.313 |
| 2019 | M0 | income:q3 | 0 | 1980 | 9.371 | 3.202 | 17.736 |
| 2019 | M0 | income:q4 | 0 | 2120 | 6.448 | 0.050 | 13.337 |
| 2019 | M0 | income:q5 | 0 | 2217 | 17.427 | 10.358 | 25.299 |
| 2019 | M1 | income:q1 | 0 | 1781 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 1973 | 4.716 | -1.991 | 12.728 |
| 2019 | M1 | income:q3 | 0 | 1980 | 10.864 | 4.790 | 19.226 |
| 2019 | M1 | income:q4 | 0 | 2120 | 7.472 | 0.888 | 14.629 |
| 2019 | M1 | income:q5 | 0 | 2217 | 16.865 | 10.036 | 25.050 |
| 2019 | M2 | income:q1 | 0 | 1781 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 1973 | 4.779 | -1.453 | 12.971 |
| 2019 | M2 | income:q3 | 0 | 1980 | 10.617 | 4.337 | 19.110 |
| 2019 | M2 | income:q4 | 0 | 2120 | 6.901 | 0.618 | 14.331 |
| 2019 | M2 | income:q5 | 0 | 2217 | 16.142 | 8.993 | 24.441 |
| pooled | pooled | income:q1 | 2481 | 1781 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2558 | 1973 | 0.906 | -5.786 | 7.956 |
| pooled | pooled | income:q3 | 2967 | 1980 | 4.466 | -2.431 | 11.694 |
| pooled | pooled | income:q4 | 3114 | 2120 | 6.568 | -0.290 | 15.039 |
| pooled | pooled | income:q5 | 4048 | 2217 | 15.102 | 6.733 | 21.794 |
| pooled | pooled | survey:2019*income:q2 | 2558 | 1973 | 3.092 | -4.731 | 14.036 |
| pooled | pooled | survey:2019*income:q3 | 2967 | 1980 | 5.507 | -2.582 | 16.076 |
| pooled | pooled | survey:2019*income:q4 | 3114 | 2120 | 0.065 | -8.434 | 11.305 |
| pooled | pooled | survey:2019*income:q5 | 4048 | 2217 | 1.093 | -7.622 | 11.196 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Quintile × density

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 406 | 68.960 | 61.828 | 77.562 | 356 | 74.177 | 68.298 | 81.717 | 1.076 | 0.957 | 1.204 |
| travel_day | q1 | intermediate | False | 910 | 67.482 | 62.880 | 72.148 | 860 | 70.169 | 65.811 | 75.899 | 1.040 | 0.949 | 1.153 |
| travel_day | q1 | sparse | False | 324 | 57.843 | 50.141 | 65.242 | 257 | 63.579 | 55.249 | 70.688 | 1.099 | 0.918 | 1.258 |
| travel_day | q1 | very_sparse | False | 841 | 58.256 | 54.681 | 61.839 | 308 | 67.428 | 58.730 | 75.952 | 1.157 | 1.015 | 1.309 |
| travel_day | q2 | dense | False | 283 | 74.071 | 63.021 | 84.876 | 210 | 82.718 | 74.009 | 91.737 | 1.117 | 0.957 | 1.325 |
| travel_day | q2 | intermediate | False | 930 | 63.607 | 59.917 | 67.652 | 885 | 71.893 | 67.396 | 76.897 | 1.130 | 1.051 | 1.210 |
| travel_day | q2 | sparse | False | 345 | 55.201 | 49.530 | 60.815 | 345 | 63.035 | 57.234 | 70.041 | 1.142 | 1.020 | 1.311 |
| travel_day | q2 | very_sparse | False | 1000 | 64.238 | 59.684 | 68.569 | 533 | 67.915 | 62.761 | 73.368 | 1.057 | 0.971 | 1.163 |
| travel_day | q3 | dense | False | 358 | 67.613 | 61.436 | 74.036 | 204 | 80.956 | 73.417 | 88.586 | 1.197 | 1.088 | 1.338 |
| travel_day | q3 | intermediate | False | 1095 | 68.033 | 63.812 | 74.281 | 865 | 78.767 | 73.878 | 83.268 | 1.158 | 1.062 | 1.248 |
| travel_day | q3 | sparse | False | 417 | 65.293 | 58.459 | 77.125 | 323 | 69.572 | 62.148 | 76.106 | 1.066 | 0.885 | 1.209 |
| travel_day | q3 | very_sparse | False | 1097 | 66.207 | 61.909 | 70.930 | 588 | 73.682 | 68.466 | 78.972 | 1.113 | 1.034 | 1.219 |
| travel_day | q4 | dense | False | 396 | 67.097 | 60.024 | 73.966 | 262 | 77.787 | 70.916 | 86.692 | 1.159 | 1.034 | 1.298 |
| travel_day | q4 | intermediate | False | 1273 | 70.008 | 66.052 | 74.452 | 941 | 75.548 | 71.135 | 80.236 | 1.079 | 0.999 | 1.155 |
| travel_day | q4 | sparse | False | 431 | 67.041 | 59.696 | 73.937 | 369 | 65.809 | 58.021 | 74.263 | 0.982 | 0.861 | 1.119 |
| travel_day | q4 | very_sparse | False | 1014 | 70.416 | 65.902 | 75.593 | 548 | 74.999 | 70.099 | 79.575 | 1.065 | 0.982 | 1.154 |
| travel_day | q5 | dense | False | 737 | 78.297 | 72.083 | 84.379 | 363 | 76.759 | 71.878 | 81.717 | 0.980 | 0.898 | 1.072 |
| travel_day | q5 | intermediate | False | 1930 | 78.586 | 74.743 | 82.405 | 1087 | 84.421 | 80.422 | 88.211 | 1.074 | 1.015 | 1.139 |
| travel_day | q5 | sparse | False | 443 | 66.757 | 60.502 | 73.184 | 323 | 75.426 | 67.749 | 82.265 | 1.130 | 0.999 | 1.254 |
| travel_day | q5 | very_sparse | False | 938 | 74.317 | 69.200 | 80.491 | 444 | 82.475 | 75.217 | 90.488 | 1.110 | 1.014 | 1.228 |
| person | q1 | dense | False | 473 | 60.904 | 54.597 | 68.230 | 476 | 66.473 | 59.966 | 73.303 | 1.091 | 0.952 | 1.254 |
| person | q1 | intermediate | False | 1159 | 53.372 | 49.581 | 57.830 | 1197 | 56.021 | 51.510 | 61.320 | 1.050 | 0.947 | 1.165 |
| person | q1 | sparse | False | 435 | 46.131 | 40.229 | 53.155 | 385 | 47.276 | 40.498 | 54.379 | 1.025 | 0.842 | 1.203 |
| person | q1 | very_sparse | False | 1292 | 40.439 | 36.904 | 43.989 | 446 | 49.425 | 41.242 | 56.953 | 1.222 | 1.055 | 1.428 |
| person | q2 | dense | False | 331 | 66.721 | 56.505 | 76.238 | 293 | 65.442 | 55.672 | 77.410 | 0.981 | 0.839 | 1.194 |
| person | q2 | intermediate | False | 1131 | 51.981 | 48.559 | 55.704 | 1191 | 59.488 | 54.581 | 64.957 | 1.144 | 1.039 | 1.235 |
| person | q2 | sparse | False | 427 | 43.390 | 37.649 | 48.584 | 456 | 51.962 | 44.912 | 59.556 | 1.198 | 1.042 | 1.407 |
| person | q2 | very_sparse | False | 1270 | 51.459 | 46.884 | 55.347 | 722 | 55.184 | 49.341 | 60.472 | 1.072 | 0.970 | 1.186 |
| person | q3 | dense | False | 418 | 56.429 | 50.139 | 61.591 | 284 | 64.854 | 54.539 | 73.924 | 1.149 | 0.953 | 1.325 |
| person | q3 | intermediate | False | 1298 | 57.966 | 53.709 | 63.807 | 1190 | 66.009 | 60.840 | 71.061 | 1.139 | 1.024 | 1.245 |
| person | q3 | sparse | False | 495 | 53.874 | 48.034 | 64.554 | 459 | 55.392 | 48.272 | 63.191 | 1.028 | 0.838 | 1.205 |
| person | q3 | very_sparse | False | 1404 | 52.709 | 48.760 | 56.860 | 809 | 61.652 | 55.552 | 67.001 | 1.170 | 1.064 | 1.296 |
| person | q4 | dense | False | 449 | 60.479 | 53.852 | 67.469 | 348 | 70.903 | 62.552 | 81.286 | 1.172 | 1.011 | 1.344 |
| person | q4 | intermediate | False | 1479 | 60.351 | 56.892 | 64.449 | 1291 | 64.827 | 59.407 | 69.826 | 1.074 | 0.976 | 1.165 |
| person | q4 | sparse | False | 497 | 60.307 | 53.441 | 66.655 | 514 | 54.672 | 46.922 | 62.193 | 0.907 | 0.770 | 1.068 |
| person | q4 | very_sparse | False | 1232 | 58.148 | 53.921 | 62.873 | 732 | 64.818 | 59.345 | 70.566 | 1.115 | 1.014 | 1.225 |
| person | q5 | dense | False | 860 | 66.259 | 60.737 | 72.971 | 497 | 70.741 | 64.809 | 77.525 | 1.068 | 0.984 | 1.193 |
| person | q5 | intermediate | False | 2201 | 69.053 | 64.740 | 72.711 | 1478 | 73.321 | 68.864 | 77.537 | 1.062 | 0.986 | 1.136 |
| person | q5 | sparse | False | 542 | 55.605 | 50.525 | 61.157 | 452 | 65.427 | 57.177 | 73.019 | 1.177 | 1.005 | 1.341 |
| person | q5 | very_sparse | False | 1149 | 59.621 | 54.439 | 65.402 | 605 | 69.098 | 60.785 | 78.235 | 1.159 | 1.040 | 1.299 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Conclusion grid

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.085 | equivalent | 1.188 | 1.169 | 1.182 | 1.179 | 1.154 | 1.161 |
| travel_day | q2 | 1.101 | inconclusive | 1.188 | 1.169 | 1.182 | 1.179 | 1.154 | 1.161 |
| travel_day | q3 | 1.132 | inconclusive | 1.188 | 1.169 | 1.182 | 1.179 | 1.154 | 1.161 |
| travel_day | q4 | 1.067 | equivalent | 1.188 | 1.169 | 1.182 | 1.179 | 1.154 | 1.161 |
| travel_day | q5 | 1.069 | equivalent | 1.188 | 1.169 | 1.182 | 1.179 | 1.154 | 1.161 |
| person | q1 | 1.105 | inconclusive | 1.294 | 1.284 | 1.277 | 1.296 | 1.154 | 1.161 |
| person | q2 | 1.105 | inconclusive | 1.294 | 1.284 | 1.277 | 1.296 | 1.154 | 1.161 |
| person | q3 | 1.127 | inconclusive | 1.294 | 1.284 | 1.277 | 1.296 | 1.154 | 1.161 |
| person | q4 | 1.062 | equivalent | 1.294 | 1.284 | 1.277 | 1.296 | 1.154 | 1.161 |
| person | q5 | 1.096 | inconclusive | 1.294 | 1.284 | 1.277 | 1.296 | 1.154 | 1.161 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


The positive income gradient survives density and car controls in both years.

## All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`)

ENTD 2008 income is complete in this file: the released income bracket and consumption-unit count are populated. The dictionary and released fields do not establish whether income brackets were imputed upstream (see [ENTD income audit](./entd2008.md#income-imputation-audit-step-12)).

### Weighted income quintile shares

Shares use the full weekday respondent roster and individual weights; `n` is unweighted. Ties in income can produce unequal shares.

| Year | Quintile | n | Share (%) |
|---:|:---|---:|---:|
| 2008 | q1 | 3359 | 20.00 |
| 2008 | q2 | 3159 | 20.00 |
| 2008 | q3 | 3615 | 20.00 |
| 2008 | q4 | 3657 | 19.99 |
| 2008 | q5 | 4752 | 20.02 |
| 2019 | q1 | 2504 | 20.00 |
| 2019 | q2 | 2662 | 20.00 |
| 2019 | q3 | 2742 | 19.99 |
| 2019 | q4 | 2885 | 20.01 |
| 2019 | q5 | 3032 | 20.00 |

### Support audit (details in support.csv)

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| group | year | terms_or_cells | empty_in_draws | max_empty_draws | min_respondents |
| --- | --- | --- | --- | --- | --- |
| regression_M0 | 2008 | 13 | 0 | 0 | 660 |
| regression_M0 | 2019 | 13 | 0 | 0 | 561 |
| regression_M1 | 2008 | 16 | 0 | 0 | 660 |
| regression_M1 | 2019 | 16 | 0 | 0 | 561 |
| regression_M2 | 2008 | 18 | 0 | 0 | 660 |
| regression_M2 | 2019 | 18 | 0 | 0 | 561 |
| regression_input_cars | 2008 | 4 | 1 | 200 | 0 |
| regression_input_cars | 2019 | 4 | 0 | 0 | 25 |
| regression_input_density | 2008 | 4 | 0 | 0 | 2012 |
| regression_input_density | 2019 | 4 | 0 | 0 | 1442 |
| regression_input_income | 2008 | 5 | 0 | 0 | 2509 |
| regression_input_income | 2019 | 5 | 0 | 0 | 1809 |
| regression_input_population | 2008 | 6 | 1 | 79 | 1 |
| regression_input_population | 2019 | 6 | 0 | 0 | 11 |
| regression_input_weekday | 2008 | 5 | 0 | 0 | 2720 |
| regression_input_weekday | 2019 | 5 | 0 | 0 | 1799 |
| regression_pooled | 2008 | 23 | 5 | 200 | 0 |
| regression_pooled | 2019 | 23 | 0 | 0 | 561 |
| reweight_input_person | 2008 | 77 | 17 | 200 | 0 |
| reweight_input_person | 2019 | 77 | 18 | 92 | 1 |
| reweight_input_travel_day | 2008 | 73 | 13 | 200 | 0 |
| reweight_input_travel_day | 2019 | 73 | 16 | 92 | 1 |
| reweight_person | 2008 | 52 | 0 | 0 | 68 |
| reweight_person | 2019 | 52 | 0 | 0 | 56 |
| reweight_travel_day | 2008 | 48 | 0 | 0 | 80 |
| reweight_travel_day | 2019 | 48 | 0 | 0 | 54 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Levels and 2019/2008 ratios

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2509 | 66.714 | 63.796 | 70.236 | 1809 | 72.532 | 69.182 | 75.962 | 1.087 | 1.018 | 1.152 | inconclusive | inconclusive |
| travel_day | q2 | 2597 | 68.019 | 64.720 | 72.069 | 2010 | 76.009 | 71.935 | 80.607 | 1.117 | 1.053 | 1.187 | inconclusive | inconclusive |
| travel_day | q3 | 3044 | 72.595 | 69.144 | 77.200 | 2037 | 86.134 | 81.680 | 91.085 | 1.186 | 1.114 | 1.253 | inconclusive | different |
| travel_day | q4 | 3212 | 76.248 | 72.686 | 79.233 | 2184 | 80.647 | 77.436 | 84.061 | 1.058 | 1.008 | 1.112 | equivalent | inconclusive |
| travel_day | q5 | 4243 | 88.847 | 85.259 | 92.322 | 2316 | 90.608 | 87.391 | 94.803 | 1.020 | 0.975 | 1.075 | equivalent | equivalent |
| person | q1 | 3359 | 52.595 | 50.148 | 55.481 | 2504 | 58.493 | 55.188 | 61.794 | 1.112 | 1.038 | 1.182 | inconclusive | inconclusive |
| person | q2 | 3159 | 56.549 | 53.664 | 59.991 | 2662 | 63.855 | 59.515 | 68.181 | 1.129 | 1.044 | 1.213 | inconclusive | inconclusive |
| person | q3 | 3615 | 61.605 | 58.639 | 66.219 | 2742 | 73.199 | 68.579 | 78.540 | 1.188 | 1.100 | 1.281 | inconclusive | different |
| person | q4 | 3657 | 67.603 | 63.990 | 70.775 | 2885 | 71.998 | 68.197 | 75.584 | 1.065 | 1.003 | 1.132 | equivalent | inconclusive |
| person | q5 | 4752 | 79.298 | 75.845 | 83.289 | 3032 | 82.317 | 78.524 | 87.091 | 1.038 | 0.979 | 1.091 | equivalent | equivalent |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Income gaps and their changes

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 22.134 | 17.511 | 26.578 | 18.076 | 13.367 | 22.568 | -4.057 | -11.307 | 2.884 |
| travel_day | ratio | 1.332 | 1.254 | 1.418 | 1.249 | 1.178 | 1.319 | -0.083 | -0.198 | 0.040 |
| person | difference | 26.703 | 22.209 | 31.062 | 23.825 | 18.926 | 29.325 | -2.879 | -9.444 | 4.827 |
| person | ratio | 1.508 | 1.408 | 1.612 | 1.407 | 1.307 | 1.519 | -0.100 | -0.249 | 0.061 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted levels and ratios

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | quintile | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high | verdict_15 | verdict_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 2509 | 66.890 | 64.133 | 70.269 | 1809 | 72.044 | 68.776 | 75.306 | 1.077 | 1.011 | 1.139 | equivalent | inconclusive |
| travel_day | q2 | 2597 | 67.859 | 64.769 | 71.885 | 2010 | 76.276 | 72.452 | 80.949 | 1.124 | 1.058 | 1.189 | inconclusive | inconclusive |
| travel_day | q3 | 3044 | 72.691 | 69.409 | 77.082 | 2037 | 86.406 | 82.158 | 91.740 | 1.189 | 1.111 | 1.262 | inconclusive | different |
| travel_day | q4 | 3212 | 76.148 | 72.660 | 79.178 | 2184 | 80.795 | 77.315 | 84.280 | 1.061 | 1.013 | 1.119 | equivalent | inconclusive |
| travel_day | q5 | 4243 | 88.798 | 85.633 | 92.322 | 2316 | 90.892 | 87.627 | 95.027 | 1.024 | 0.979 | 1.076 | equivalent | equivalent |
| person | q1 | 3359 | 53.340 | 50.832 | 56.356 | 2504 | 57.820 | 54.537 | 61.247 | 1.084 | 1.011 | 1.151 | inconclusive | inconclusive |
| person | q2 | 3159 | 56.302 | 53.441 | 59.562 | 2662 | 64.059 | 59.858 | 68.453 | 1.138 | 1.051 | 1.231 | inconclusive | inconclusive |
| person | q3 | 3615 | 61.571 | 58.458 | 66.007 | 2742 | 73.555 | 68.872 | 79.134 | 1.195 | 1.108 | 1.294 | inconclusive | different |
| person | q4 | 3657 | 67.557 | 63.992 | 70.678 | 2885 | 72.283 | 68.385 | 75.703 | 1.070 | 1.003 | 1.140 | equivalent | inconclusive |
| person | q5 | 4752 | 79.362 | 76.066 | 83.257 | 3032 | 82.355 | 78.506 | 87.332 | 1.038 | 0.981 | 1.090 | equivalent | equivalent |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Reweighted gaps

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | gap | value_2008 | ci_2008_low | ci_2008_high | value_2019 | ci_2019_low | ci_2019_high | change | change_ci_low | change_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | difference | 21.909 | 17.329 | 26.352 | 18.848 | 14.247 | 23.516 | -3.061 | -10.128 | 4.105 |
| travel_day | ratio | 1.328 | 1.250 | 1.409 | 1.262 | 1.192 | 1.334 | -0.066 | -0.184 | 0.056 |
| person | difference | 26.022 | 21.334 | 30.299 | 24.535 | 19.534 | 29.901 | -1.487 | -7.969 | 6.202 |
| person | ratio | 1.488 | 1.385 | 1.589 | 1.424 | 1.326 | 1.535 | -0.064 | -0.210 | 0.114 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Collapsed joint cells

- travel_day: 36.95% of the full-sample pooled target is in cells that combine two or more original cells.
- person: 37.55% of the full-sample pooled target is in cells that combine two or more original cells.

- travel_day: `q1|dense|1` → `q1|dense|1+`.
- travel_day: `q1|dense|2+` → `q1|dense|1+`.
- travel_day: `q1|dense|unknown` → `q1|dense|0`.
- travel_day: `q1|intermediate|unknown` → `q1|intermediate|1`.
- travel_day: `q1|sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|sparse|1` → `q1|sparse|1+`.
- travel_day: `q1|sparse|2+` → `q1|sparse|1+`.
- travel_day: `q1|sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|0` → `q1|sparse+very_sparse|0`.
- travel_day: `q1|very_sparse|unknown` → `q1|sparse+very_sparse|0`.
- travel_day: `q2|dense|1` → `q2|dense|1+`.
- travel_day: `q2|dense|2+` → `q2|dense|1+`.
- travel_day: `q2|dense|unknown` → `q2|dense|1+`.
- travel_day: `q2|intermediate|unknown` → `q2|intermediate|1`.
- travel_day: `q2|sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|0` → `q2|sparse+very_sparse|0`.
- travel_day: `q2|very_sparse|unknown` → `q2|sparse+very_sparse|0`.
- travel_day: `q3|dense|1` → `q3|dense|1+`.
- travel_day: `q3|dense|2+` → `q3|dense|1+`.
- travel_day: `q3|dense|unknown` → `q3|dense|1+`.
- travel_day: `q3|intermediate|unknown` → `q3|intermediate|1`.
- travel_day: `q3|sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|0` → `q3|intermediate|0`.
- travel_day: `q3|very_sparse|unknown` → `q3|very_sparse|2+`.
- travel_day: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- travel_day: `q4|sparse|0` → `q4|intermediate|0`.
- travel_day: `q4|sparse|unknown` → `q4|sparse|2+`.
- travel_day: `q4|very_sparse|0` → `q4|intermediate|0`.
- travel_day: `q5|sparse|0` → `q5|intermediate|0`.
- travel_day: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q1|dense|1` → `q1|dense|1+`.
- person: `q1|dense|2+` → `q1|dense|1+`.
- person: `q1|dense|unknown` → `q1|dense|0`.
- person: `q1|intermediate|unknown` → `q1|intermediate|0`.
- person: `q1|sparse|unknown` → `q1|very_sparse|1`.
- person: `q1|very_sparse|unknown` → `q1|very_sparse|1`.
- person: `q2|dense|1` → `q2|dense|1+`.
- person: `q2|dense|2+` → `q2|dense|1+`.
- person: `q2|dense|unknown` → `q2|dense|1+`.
- person: `q2|intermediate|unknown` → `q2|intermediate|1`.
- person: `q2|sparse|unknown` → `q2|very_sparse|2+`.
- person: `q2|very_sparse|unknown` → `q2|very_sparse|2+`.
- person: `q3|dense|1` → `q3|dense|1+`.
- person: `q3|dense|2+` → `q3|dense|1+`.
- person: `q3|dense|unknown` → `q3|dense|1+`.
- person: `q3|intermediate|unknown` → `q3|intermediate|1`.
- person: `q3|sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|0` → `q3|sparse+very_sparse|0`.
- person: `q3|very_sparse|unknown` → `q3|sparse+very_sparse|0`.
- person: `q4|intermediate|unknown` → `q4|intermediate|2+`.
- person: `q4|sparse|0` → `q4|intermediate|0`.
- person: `q4|sparse|unknown` → `q4|intermediate|0`.
- person: `q4|very_sparse|0` → `q4|intermediate|0`.
- person: `q4|very_sparse|unknown` → `q4|intermediate|0`.
- person: `q5|intermediate|unknown` → `q5|intermediate|2+`.
- person: `q5|sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|0` → `q5|intermediate|0`.
- person: `q5|very_sparse|unknown` → `q5|very_sparse|2+`.

### Cells still below minimum support

- None.

- travel_day: 200/200 draws retained; maximum lost target share 0.000%.
- person: 200/200 draws retained; maximum lost target share 0.000%.

### Merged regression levels

- population: `unknown` → `unknown+other_inactive`.
- population: `other_inactive` → `unknown+other_inactive`.
- cars: `unknown` → `unknown+0`.
- cars: `0` → `unknown+0`.

### Weighted regressions

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| year | model | term | n_2008 | n_2019 | percent | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | M0 | income:q1 | 2509 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M0 | income:q2 | 2597 | 0 | 2.021 | -5.470 | 8.635 |
| 2008 | M0 | income:q3 | 3044 | 0 | 5.870 | -0.952 | 13.608 |
| 2008 | M0 | income:q4 | 3212 | 0 | 8.839 | 1.450 | 17.423 |
| 2008 | M0 | income:q5 | 4243 | 0 | 24.632 | 15.984 | 31.810 |
| 2008 | M1 | income:q1 | 2509 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M1 | income:q2 | 2597 | 0 | 2.067 | -5.646 | 9.006 |
| 2008 | M1 | income:q3 | 3044 | 0 | 6.163 | -0.786 | 14.013 |
| 2008 | M1 | income:q4 | 3212 | 0 | 9.318 | 2.031 | 17.950 |
| 2008 | M1 | income:q5 | 4243 | 0 | 23.838 | 14.870 | 30.853 |
| 2008 | M2 | income:q1 | 2509 | 0 | 0.000 | 0.000 | 0.000 |
| 2008 | M2 | income:q2 | 2597 | 0 | 1.972 | -5.674 | 7.993 |
| 2008 | M2 | income:q3 | 3044 | 0 | 6.005 | -1.001 | 13.176 |
| 2008 | M2 | income:q4 | 3212 | 0 | 9.048 | 1.896 | 16.251 |
| 2008 | M2 | income:q5 | 4243 | 0 | 23.523 | 15.748 | 31.218 |
| 2019 | M0 | income:q1 | 0 | 1809 | 0.000 | 0.000 | 0.000 |
| 2019 | M0 | income:q2 | 0 | 2010 | 4.090 | -2.848 | 12.236 |
| 2019 | M0 | income:q3 | 0 | 2037 | 12.903 | 5.858 | 22.100 |
| 2019 | M0 | income:q4 | 0 | 2184 | 8.573 | 1.198 | 15.528 |
| 2019 | M0 | income:q5 | 0 | 2316 | 21.313 | 13.653 | 29.294 |
| 2019 | M1 | income:q1 | 0 | 1809 | 0.000 | 0.000 | 0.000 |
| 2019 | M1 | income:q2 | 0 | 2010 | 5.572 | -1.082 | 13.589 |
| 2019 | M1 | income:q3 | 0 | 2037 | 14.373 | 7.231 | 23.820 |
| 2019 | M1 | income:q4 | 0 | 2184 | 9.573 | 2.063 | 16.458 |
| 2019 | M1 | income:q5 | 0 | 2316 | 20.789 | 13.466 | 28.750 |
| 2019 | M2 | income:q1 | 0 | 1809 | 0.000 | 0.000 | 0.000 |
| 2019 | M2 | income:q2 | 0 | 2010 | 5.420 | -1.143 | 13.119 |
| 2019 | M2 | income:q3 | 0 | 2037 | 13.736 | 6.563 | 23.990 |
| 2019 | M2 | income:q4 | 0 | 2184 | 8.522 | 1.624 | 16.620 |
| 2019 | M2 | income:q5 | 0 | 2316 | 19.537 | 11.455 | 28.023 |
| pooled | pooled | income:q1 | 2509 | 1809 | 0.000 | 0.000 | 0.000 |
| pooled | pooled | income:q2 | 2597 | 2010 | 2.259 | -5.444 | 9.051 |
| pooled | pooled | income:q3 | 3044 | 2037 | 6.287 | -0.959 | 13.262 |
| pooled | pooled | income:q4 | 3212 | 2184 | 8.924 | 1.406 | 17.141 |
| pooled | pooled | income:q5 | 4243 | 2316 | 23.477 | 14.878 | 30.939 |
| pooled | pooled | survey:2019*income:q2 | 2597 | 2010 | 2.224 | -7.519 | 13.107 |
| pooled | pooled | survey:2019*income:q3 | 3044 | 2037 | 6.439 | -2.229 | 18.274 |
| pooled | pooled | survey:2019*income:q4 | 3212 | 2184 | -0.759 | -9.668 | 10.106 |
| pooled | pooled | survey:2019*income:q5 | 4243 | 2316 | -3.213 | -12.455 | 5.919 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Quintile × density

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | quintile | density | small_cell | n_2008 | mean_2008 | ci_2008_low | ci_2008_high | n_2019 | mean_2019 | ci_2019_low | ci_2019_high | ratio | ratio_ci_low | ratio_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | dense | False | 410 | 70.477 | 63.476 | 80.000 | 360 | 76.526 | 70.290 | 84.160 | 1.086 | 0.961 | 1.219 |
| travel_day | q1 | intermediate | False | 920 | 68.846 | 64.265 | 73.613 | 875 | 74.314 | 68.749 | 81.271 | 1.079 | 0.977 | 1.190 |
| travel_day | q1 | sparse | False | 326 | 61.803 | 53.705 | 70.610 | 260 | 64.335 | 56.005 | 71.540 | 1.041 | 0.884 | 1.185 |
| travel_day | q1 | very_sparse | False | 853 | 63.647 | 58.751 | 68.750 | 314 | 70.939 | 61.699 | 78.936 | 1.115 | 0.968 | 1.264 |
| travel_day | q2 | dense | False | 288 | 75.277 | 64.058 | 86.440 | 215 | 91.753 | 76.255 | 105.984 | 1.219 | 1.014 | 1.482 |
| travel_day | q2 | intermediate | False | 946 | 68.767 | 63.750 | 74.755 | 906 | 76.450 | 70.799 | 82.279 | 1.112 | 1.022 | 1.214 |
| travel_day | q2 | sparse | False | 348 | 58.155 | 52.287 | 64.066 | 347 | 68.979 | 58.467 | 80.987 | 1.186 | 1.000 | 1.382 |
| travel_day | q2 | very_sparse | False | 1015 | 69.260 | 64.126 | 75.614 | 542 | 74.454 | 67.067 | 82.551 | 1.075 | 0.963 | 1.193 |
| travel_day | q3 | dense | False | 368 | 75.018 | 67.074 | 83.552 | 215 | 113.762 | 87.702 | 145.366 | 1.516 | 1.184 | 1.932 |
| travel_day | q3 | intermediate | False | 1116 | 72.090 | 67.145 | 78.554 | 881 | 85.685 | 80.038 | 92.004 | 1.189 | 1.091 | 1.303 |
| travel_day | q3 | sparse | False | 428 | 73.370 | 64.275 | 86.270 | 332 | 74.090 | 66.726 | 81.391 | 1.010 | 0.831 | 1.143 |
| travel_day | q3 | very_sparse | False | 1132 | 71.760 | 66.712 | 77.357 | 609 | 84.194 | 76.271 | 93.260 | 1.173 | 1.057 | 1.310 |
| travel_day | q4 | dense | False | 408 | 71.930 | 65.296 | 81.153 | 276 | 90.192 | 78.709 | 104.741 | 1.254 | 1.082 | 1.436 |
| travel_day | q4 | intermediate | False | 1309 | 77.741 | 72.828 | 83.474 | 968 | 81.274 | 76.525 | 86.187 | 1.045 | 0.964 | 1.137 |
| travel_day | q4 | sparse | False | 444 | 70.943 | 63.694 | 79.144 | 381 | 70.822 | 64.067 | 79.864 | 0.998 | 0.878 | 1.150 |
| travel_day | q4 | very_sparse | False | 1051 | 80.179 | 73.123 | 88.284 | 559 | 82.303 | 75.381 | 88.236 | 1.026 | 0.915 | 1.141 |
| travel_day | q5 | dense | False | 781 | 94.496 | 85.846 | 103.174 | 376 | 82.295 | 76.465 | 88.765 | 0.871 | 0.788 | 0.972 |
| travel_day | q5 | intermediate | False | 2006 | 90.887 | 85.947 | 97.010 | 1131 | 92.055 | 87.686 | 96.759 | 1.013 | 0.944 | 1.074 |
| travel_day | q5 | sparse | False | 466 | 76.561 | 69.911 | 84.094 | 338 | 88.394 | 76.529 | 100.840 | 1.155 | 1.003 | 1.325 |
| travel_day | q5 | very_sparse | False | 990 | 88.300 | 80.432 | 97.304 | 471 | 98.599 | 89.169 | 109.034 | 1.117 | 1.006 | 1.277 |
| person | q1 | dense | False | 473 | 63.000 | 55.481 | 70.296 | 476 | 68.919 | 61.317 | 77.536 | 1.094 | 0.956 | 1.258 |
| person | q1 | intermediate | False | 1159 | 54.986 | 50.797 | 59.417 | 1197 | 60.492 | 54.924 | 67.329 | 1.100 | 0.984 | 1.220 |
| person | q1 | sparse | False | 435 | 49.466 | 42.838 | 57.242 | 385 | 48.187 | 41.518 | 55.510 | 0.974 | 0.796 | 1.131 |
| person | q1 | very_sparse | False | 1292 | 44.619 | 40.327 | 48.587 | 446 | 52.874 | 44.866 | 59.952 | 1.185 | 0.994 | 1.368 |
| person | q2 | dense | False | 331 | 68.449 | 57.980 | 78.244 | 293 | 75.664 | 60.193 | 92.300 | 1.105 | 0.903 | 1.426 |
| person | q2 | intermediate | False | 1131 | 57.856 | 53.675 | 63.246 | 1191 | 65.021 | 59.826 | 71.104 | 1.124 | 1.009 | 1.246 |
| person | q2 | sparse | False | 427 | 46.128 | 39.620 | 51.580 | 456 | 57.523 | 47.914 | 67.091 | 1.247 | 1.026 | 1.478 |
| person | q2 | very_sparse | False | 1270 | 56.053 | 50.770 | 61.708 | 722 | 62.013 | 54.192 | 69.023 | 1.106 | 0.963 | 1.242 |
| person | q3 | dense | False | 418 | 65.738 | 59.007 | 74.232 | 284 | 96.969 | 71.882 | 123.609 | 1.475 | 1.130 | 1.899 |
| person | q3 | intermediate | False | 1298 | 62.101 | 57.643 | 67.837 | 1190 | 73.250 | 66.729 | 80.065 | 1.180 | 1.066 | 1.307 |
| person | q3 | sparse | False | 495 | 62.409 | 54.218 | 74.569 | 459 | 60.452 | 53.486 | 68.963 | 0.969 | 0.790 | 1.112 |
| person | q3 | very_sparse | False | 1404 | 58.613 | 54.161 | 63.292 | 809 | 72.917 | 64.971 | 82.142 | 1.244 | 1.105 | 1.412 |
| person | q4 | dense | False | 449 | 66.833 | 60.822 | 75.482 | 348 | 89.085 | 76.788 | 104.438 | 1.333 | 1.112 | 1.541 |
| person | q4 | intermediate | False | 1479 | 68.542 | 63.667 | 73.278 | 1291 | 72.057 | 66.432 | 78.098 | 1.051 | 0.960 | 1.155 |
| person | q4 | sparse | False | 497 | 65.416 | 58.970 | 73.123 | 514 | 60.777 | 53.235 | 69.378 | 0.929 | 0.802 | 1.089 |
| person | q4 | very_sparse | False | 1232 | 68.045 | 61.679 | 75.089 | 732 | 72.596 | 64.964 | 80.308 | 1.067 | 0.938 | 1.210 |
| person | q5 | dense | False | 860 | 84.314 | 75.621 | 93.364 | 497 | 78.299 | 71.349 | 86.708 | 0.929 | 0.837 | 1.051 |
| person | q5 | intermediate | False | 2201 | 83.381 | 78.345 | 88.914 | 1478 | 82.947 | 78.032 | 88.542 | 0.995 | 0.915 | 1.071 |
| person | q5 | sparse | False | 542 | 67.096 | 61.599 | 74.038 | 452 | 80.064 | 67.463 | 94.504 | 1.193 | 1.009 | 1.403 |
| person | q5 | very_sparse | False | 1149 | 74.405 | 66.490 | 82.758 | 605 | 87.170 | 78.355 | 98.742 | 1.172 | 1.037 | 1.342 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Conclusion grid

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| basis | quintile | ratio | verdict_15 | raw_q5_q1_2008 | raw_q5_q1_2019 | reweighted_q5_q1_2008 | reweighted_q5_q1_2019 | m2_q5_q1_2008 | m2_q5_q1_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| travel_day | q1 | 1.087 | inconclusive | 1.332 | 1.249 | 1.328 | 1.262 | 1.235 | 1.195 |
| travel_day | q2 | 1.117 | inconclusive | 1.332 | 1.249 | 1.328 | 1.262 | 1.235 | 1.195 |
| travel_day | q3 | 1.186 | inconclusive | 1.332 | 1.249 | 1.328 | 1.262 | 1.235 | 1.195 |
| travel_day | q4 | 1.058 | equivalent | 1.332 | 1.249 | 1.328 | 1.262 | 1.235 | 1.195 |
| travel_day | q5 | 1.020 | equivalent | 1.332 | 1.249 | 1.328 | 1.262 | 1.235 | 1.195 |
| person | q1 | 1.112 | inconclusive | 1.508 | 1.407 | 1.488 | 1.424 | 1.235 | 1.195 |
| person | q2 | 1.129 | inconclusive | 1.508 | 1.407 | 1.488 | 1.424 | 1.235 | 1.195 |
| person | q3 | 1.188 | inconclusive | 1.508 | 1.407 | 1.488 | 1.424 | 1.235 | 1.195 |
| person | q4 | 1.065 | equivalent | 1.508 | 1.407 | 1.488 | 1.424 | 1.235 | 1.195 |
| person | q5 | 1.038 | equivalent | 1.508 | 1.407 | 1.488 | 1.424 | 1.235 | 1.195 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

The positive income gradient survives density and car controls in both years.

