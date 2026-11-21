# Daily travel time by grouping

Weekdays, residents aged 6+; survey day weights and shared household draws. Density is the common residence proxy; vehicles are harmonised in-use household vehicles. Income is the within-survey quintile. Work/study days include a scoped trip for work or study.

Nominal categories are never merged. Ordered secondary categories are merged on full-sample respondent counts in both years and held fixed in every draw. Cells below the threshold are hidden in cell tables but retained in all aggregate calculations.

Ratios are observed 2019 divided by predicted 2019; their intervals are 90%, eta-squared, KS and decomposition intervals are 95%. Intervals require at least 95% valid household draws. Missing 2008 cells use their primary parent; the fallback share is reported.

The person-mode distribution maps weighted mid-ranks within each 2019 mode to 2008 weighted empirical mode-user durations, preserving the 2019 mode combinations; ties retain day order. Its discretised mean can differ from the analytical fixed-mode mean.

## Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`)

### Grouping summary

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| day_mode_group_x_income | 0.154 | 0.169 | 0.086 | 0.000 | 1.068 | 1.047 | 1.089 | 0.048 | 34 |
| day_mode_group_x_category | 0.175 | 0.199 | 0.081 | 0.000 | 1.070 | 1.047 | 1.092 | 0.050 | 45 |
| day_mode_group_x_vehicles | 0.149 | 0.176 | - | 0.279 | 1.070 | 1.048 | 1.091 | 0.049 | 29 |
| day_mode_group | 0.145 | 0.158 | 0.070 | 0.169 | 1.070 | 1.049 | 1.093 | 0.049 | 9 |
| day_mode_group_x_density | 0.150 | 0.164 | 0.075 | 0.033 | 1.071 | 1.049 | 1.094 | 0.049 | 25 |
| income | 0.007 | 0.007 | 0.077 | 0.000 | 1.080 | 1.056 | 1.101 | 0.054 | 5 |
| vehicles | 0.001 | 0.006 | - | 0.389 | 1.080 | 1.055 | 1.101 | 0.054 | 4 |
| density | 0.004 | 0.007 | 0.077 | 0.000 | 1.080 | 1.056 | 1.102 | 0.054 | 4 |
| none | 0.000 | 0.000 | 0.078 | 0.000 | 1.081 | 1.057 | 1.101 | 0.054 | 1 |
| category_x_density_x_income | 0.051 | 0.057 | 0.103 | 0.024 | 1.082 | 1.057 | 1.107 | 0.056 | 60 |
| household_type | 0.001 | 0.002 | 0.079 | 0.000 | 1.083 | 1.059 | 1.104 | 0.054 | 5 |
| day_purpose | 0.020 | 0.015 | - | 0.543 | 1.085 | 1.061 | 1.106 | 0.056 | 3 |
| category | 0.033 | 0.041 | 0.082 | 0.000 | 1.088 | 1.064 | 1.110 | 0.058 | 5 |
| age_band | 0.041 | 0.050 | 0.092 | 0.000 | 1.099 | 1.076 | 1.121 | 0.065 | 6 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 14006 | 9418 | 63.879 | 69.038 | 1.000 | 1.000 | 1.081 | 1.057 | 1.101 | inconclusive | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.078 | 0.000 | 1.000 | 0.078 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.879 | 1.081 | 1.057 | 1.101 | 0.000 | 0.000 | 0.054 | 0.041 | 0.072 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.019 | 19.207 |
| 2 | 24.790 | 29.837 |
| 3 | 34.187 | 34.987 |
| 4 | 41.919 | 44.816 |
| 5 | 54.166 | 59.128 |
| 6 | 61.174 | 69.258 |
| 7 | 75.116 | 84.308 |
| 8 | 94.292 | 104.154 |
| 9 | 121.874 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1253 | 861 | 50.737 | 53.394 | 0.171 | 0.165 | 1.052 | 0.971 | 1.118 | inconclusive | equivalent |
| employed | 7197 | 4045 | 71.941 | 78.191 | 0.497 | 0.471 | 1.087 | 1.057 | 1.118 | inconclusive | equivalent |
| other_inactive | 1324 | 778 | 65.329 | 74.157 | 0.093 | 0.084 | 1.135 | 1.050 | 1.231 | inconclusive | inconclusive |
| retired | 3635 | 3222 | 54.360 | 58.697 | 0.200 | 0.229 | 1.080 | 1.034 | 1.122 | inconclusive | equivalent |
| unemployed | 596 | 502 | 64.134 | 72.944 | 0.040 | 0.051 | 1.137 | 1.011 | 1.282 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.033 | 0.025 | 0.043 | 0.041 | 0.031 | 0.052 | 0.082 | 0.000 | 0.866 | 0.129 | 0.000 | 0.001 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.030 | 63.464 | 1.088 | 1.064 | 1.110 | -0.417 | 0.000 | 0.058 | 0.043 | 0.076 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.930 | 19.206 |
| 2 | 24.673 | 29.837 |
| 3 | 33.980 | 34.980 |
| 4 | 40.547 | 44.813 |
| 5 | 54.009 | 59.127 |
| 6 | 59.999 | 69.256 |
| 7 | 74.865 | 84.302 |
| 8 | 94.079 | 104.150 |
| 9 | 120.953 | 134.642 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 996 | 655 | 44.482 | 46.216 | 0.129 | 0.128 | 1.039 | 0.949 | 1.127 | inconclusive | equivalent |
| 15 | 2023 | 1165 | 71.304 | 78.119 | 0.212 | 0.173 | 1.096 | 1.043 | 1.152 | inconclusive | inconclusive |
| 30 | 2115 | 1083 | 71.114 | 77.986 | 0.167 | 0.140 | 1.097 | 1.037 | 1.141 | inconclusive | equivalent |
| 40 | 2353 | 1223 | 70.948 | 78.906 | 0.159 | 0.159 | 1.112 | 1.060 | 1.169 | inconclusive | inconclusive |
| 50 | 2760 | 1606 | 67.867 | 74.377 | 0.135 | 0.139 | 1.096 | 1.040 | 1.158 | inconclusive | inconclusive |
| 60 | 3759 | 3686 | 54.091 | 60.580 | 0.198 | 0.262 | 1.120 | 1.068 | 1.164 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.041 | 0.030 | 0.052 | 0.050 | 0.042 | 0.063 | 0.092 | 0.000 | 0.282 | 0.113 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 62.811 | 1.099 | 1.076 | 1.121 | -1.068 | 0.000 | 0.065 | 0.049 | 0.082 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.012 | 19.207 |
| 2 | 24.401 | 29.837 |
| 3 | 31.186 | 34.987 |
| 4 | 39.877 | 44.816 |
| 5 | 51.631 | 59.128 |
| 6 | 59.975 | 69.258 |
| 7 | 74.604 | 84.308 |
| 8 | 91.360 | 104.154 |
| 9 | 120.074 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 1996 | 1290 | 67.141 | 72.964 | 0.142 | 0.149 | 1.087 | 1.031 | 1.142 | inconclusive | equivalent |
| intermediate | 5726 | 4344 | 65.757 | 71.719 | 0.446 | 0.460 | 1.091 | 1.055 | 1.124 | inconclusive | equivalent |
| sparse | 1779 | 1525 | 58.362 | 61.213 | 0.171 | 0.186 | 1.049 | 0.964 | 1.113 | inconclusive | equivalent |
| very_sparse | 4505 | 2259 | 62.388 | 67.271 | 0.241 | 0.205 | 1.078 | 1.038 | 1.127 | inconclusive | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.004 | 0.001 | 0.009 | 0.007 | 0.004 | 0.013 | 0.077 | 0.000 | 1.000 | 0.087 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.896 | 1.080 | 1.056 | 1.102 | 0.017 | 0.000 | 0.054 | 0.041 | 0.073 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.017 | 19.207 |
| 2 | 24.785 | 29.837 |
| 3 | 34.183 | 34.987 |
| 4 | 41.864 | 44.816 |
| 5 | 54.156 | 59.128 |
| 6 | 61.109 | 69.258 |
| 7 | 75.076 | 84.308 |
| 8 | 94.324 | 104.154 |
| 9 | 121.934 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2256 | 1628 | 59.795 | 65.036 | 0.186 | 0.188 | 1.088 | 1.025 | 1.146 | inconclusive | equivalent |
| q2 | 2369 | 1843 | 60.292 | 64.596 | 0.198 | 0.196 | 1.071 | 1.013 | 1.129 | inconclusive | equivalent |
| q3 | 2743 | 1850 | 62.480 | 68.756 | 0.200 | 0.196 | 1.100 | 1.055 | 1.154 | inconclusive | inconclusive |
| q4 | 2871 | 1990 | 64.746 | 69.645 | 0.209 | 0.206 | 1.076 | 1.021 | 1.125 | inconclusive | equivalent |
| q5 | 3767 | 2107 | 71.457 | 76.301 | 0.207 | 0.214 | 1.068 | 1.020 | 1.111 | inconclusive | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.007 | 0.004 | 0.013 | 0.007 | 0.004 | 0.012 | 0.077 | 0.000 | 0.802 | 0.096 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.933 | 1.080 | 1.056 | 1.101 | 0.054 | 0.000 | 0.054 | 0.040 | 0.071 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.020 | 19.207 |
| 2 | 24.796 | 29.837 |
| 3 | 34.197 | 34.987 |
| 4 | 42.047 | 44.816 |
| 5 | 54.187 | 59.128 |
| 6 | 61.334 | 69.258 |
| 7 | 75.487 | 84.308 |
| 8 | 94.322 | 104.154 |
| 9 | 122.175 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2030 | 1390 | 67.511 | 73.682 | 0.115 | 0.125 | 1.091 | 1.020 | 1.170 | inconclusive | inconclusive |
| 1 | 5385 | 3934 | 62.947 | 65.367 | 0.387 | 0.391 | 1.038 | 1.004 | 1.074 | equivalent | equivalent |
| 2+ | 6591 | 4071 | 63.763 | 70.547 | 0.498 | 0.481 | 1.106 | 1.069 | 1.137 | inconclusive | equivalent |
| unknown | 0 | 23 | - | - | - | - | - | - | - |  |  |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.003 | 0.006 | 0.002 | 0.022 | - | 0.389 | 0.879 | - | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.914 | 1.080 | 1.055 | 1.101 | 0.034 | 0.002 | 0.054 | 0.041 | 0.072 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.016 | 19.207 |
| 2 | 24.766 | 29.837 |
| 3 | 34.159 | 34.987 |
| 4 | 41.851 | 44.816 |
| 5 | 54.164 | 59.128 |
| 6 | 61.174 | 69.258 |
| 7 | 75.399 | 84.308 |
| 8 | 94.333 | 104.154 |
| 9 | 122.408 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 6918 | 5415 | 56.106 | 62.369 | 0.449 | 0.465 | 1.112 | 1.072 | 1.150 | inconclusive | equivalent |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7088 | 4002 | 70.225 | 74.843 | 0.551 | 0.535 | 1.066 | 1.034 | 1.097 | equivalent | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.020 | 0.015 | 0.027 | 0.015 | 0.010 | 0.022 | - | 0.543 | 1.000 | - | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.655 | 1.085 | 1.061 | 1.106 | -0.224 | 0.000 | 0.056 | 0.043 | 0.074 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.004 | 19.207 |
| 2 | 24.717 | 29.837 |
| 3 | 34.086 | 34.987 |
| 4 | 41.266 | 44.816 |
| 5 | 54.076 | 59.128 |
| 6 | 60.534 | 69.258 |
| 7 | 74.933 | 84.308 |
| 8 | 94.187 | 104.154 |
| 9 | 121.466 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 7632 | 5132 | 63.570 | 68.447 | 0.511 | 0.502 | 1.077 | 1.051 | 1.107 | inconclusive | equivalent |
| car_passenger_carpool | 361 | 364 | 53.757 | 59.518 | 0.024 | 0.024 | 1.107 | 0.963 | 1.257 | inconclusive | inconclusive |
| car_passenger_household | 887 | 781 | 48.169 | 53.544 | 0.083 | 0.094 | 1.112 | 1.023 | 1.202 | inconclusive | inconclusive |
| cycle | 265 | 154 | 45.428 | 51.509 | 0.021 | 0.019 | 1.134 | 0.950 | 1.347 | inconclusive | inconclusive |
| multimodal | 1188 | 741 | 94.177 | 98.198 | 0.094 | 0.094 | 1.043 | 0.985 | 1.093 | equivalent | equivalent |
| other | 415 | 198 | 65.819 | 71.027 | 0.039 | 0.025 | 1.079 | 0.966 | 1.226 | inconclusive | inconclusive |
| train | 382 | 150 | 127.946 | 145.819 | 0.020 | 0.021 | 1.140 | 1.012 | 1.261 | inconclusive | inconclusive |
| urban_pt | 1044 | 700 | 91.048 | 93.173 | 0.065 | 0.086 | 1.023 | 0.962 | 1.091 | equivalent | equivalent |
| walking_only | 1832 | 1198 | 36.593 | 38.643 | 0.142 | 0.136 | 1.056 | 0.990 | 1.121 | inconclusive | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.145 | 0.119 | 0.174 | 0.158 | 0.142 | 0.179 | 0.070 | 0.169 | 0.815 | 0.131 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 64.494 | 1.070 | 1.049 | 1.093 | 0.614 | 0.000 | 0.049 | 0.035 | 0.067 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.049 | 19.207 |
| 2 | 24.938 | 29.837 |
| 3 | 34.376 | 34.987 |
| 4 | 43.637 | 44.816 |
| 5 | 54.360 | 59.128 |
| 6 | 62.521 | 69.258 |
| 7 | 77.397 | 84.308 |
| 8 | 94.663 | 104.154 |
| 9 | 124.180 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 527 | 378 | 67.802 | 75.132 | 0.042 | 0.041 | 1.108 | 1.021 | 1.201 | inconclusive | inconclusive |
| car_driver\|intermediate | 2851 | 2208 | 64.370 | 70.346 | 0.215 | 0.216 | 1.093 | 1.050 | 1.139 | inconclusive | equivalent |
| car_driver\|sparse | 1125 | 944 | 60.960 | 62.701 | 0.098 | 0.108 | 1.029 | 0.936 | 1.113 | inconclusive | equivalent |
| car_driver\|very_sparse | 3129 | 1602 | 62.978 | 68.014 | 0.156 | 0.137 | 1.080 | 1.027 | 1.137 | inconclusive | equivalent |
| car_passenger_carpool\|dense+intermediate | 192 | 225 | 54.991 | 62.180 | 0.013 | 0.014 | 1.131 | 0.963 | 1.294 | inconclusive | inconclusive |
| car_passenger_carpool\|sparse | 52 | 61 | 55.491 | 52.370 | 0.006 | 0.006 | 0.944 | 0.645 | 1.266 | inconclusive | inconclusive |
| car_passenger_carpool\|very_sparse | 117 | 78 | 48.190 | 60.589 | 0.005 | 0.005 | 1.257 | 0.982 | 1.606 | inconclusive | inconclusive |
| car_passenger_household\|dense | 67 | 58 | 48.282 | 67.070 | 0.007 | 0.008 | 1.389 | 1.103 | 1.744 | different | inconclusive |
| car_passenger_household\|intermediate | 321 | 360 | 48.544 | 53.652 | 0.035 | 0.044 | 1.105 | 0.961 | 1.227 | inconclusive | inconclusive |
| car_passenger_household\|sparse | 128 | 159 | 42.517 | 49.793 | 0.016 | 0.021 | 1.171 | 0.957 | 1.460 | inconclusive | inconclusive |
| car_passenger_household\|very_sparse | 371 | 204 | 51.176 | 52.154 | 0.025 | 0.022 | 1.019 | 0.898 | 1.150 | inconclusive | equivalent |
| cycle\|dense+intermediate+sparse+very_sparse | 265 | 154 | 45.428 | 51.509 | 0.021 | 0.019 | 1.134 | 0.950 | 1.347 | inconclusive | inconclusive |
| multimodal\|dense | 188 | 108 | 105.494 | 103.070 | 0.013 | 0.012 | 0.977 | 0.818 | 1.113 | inconclusive | inconclusive |
| multimodal\|intermediate | 520 | 355 | 98.111 | 102.052 | 0.045 | 0.048 | 1.040 | 0.949 | 1.118 | inconclusive | equivalent |
| multimodal\|sparse | 123 | 101 | 80.306 | 90.458 | 0.014 | 0.014 | 1.126 | 0.954 | 1.318 | inconclusive | inconclusive |
| multimodal\|very_sparse | 357 | 177 | 88.676 | 91.207 | 0.023 | 0.019 | 1.029 | 0.907 | 1.166 | inconclusive | inconclusive |
| other\|dense+intermediate | 178 | 114 | 63.050 | 68.708 | 0.017 | 0.013 | 1.090 | 0.922 | 1.275 | inconclusive | inconclusive |
| other\|sparse+very_sparse | 237 | 84 | 67.955 | 73.775 | 0.022 | 0.011 | 1.086 | 0.917 | 1.302 | inconclusive | inconclusive |
| train\|dense+intermediate+sparse+very_sparse | 382 | 150 | 127.946 | 145.819 | 0.020 | 0.021 | 1.140 | 1.012 | 1.261 | inconclusive | inconclusive |
| urban_pt\|dense | 550 | 302 | 89.562 | 89.647 | 0.029 | 0.037 | 1.001 | 0.928 | 1.091 | equivalent | equivalent |
| urban_pt\|intermediate+sparse+very_sparse | 494 | 398 | 92.265 | 95.874 | 0.036 | 0.049 | 1.039 | 0.949 | 1.126 | inconclusive | equivalent |
| walking_only\|dense | 475 | 313 | 39.747 | 44.526 | 0.038 | 0.037 | 1.120 | 0.993 | 1.269 | inconclusive | inconclusive |
| walking_only\|intermediate | 899 | 624 | 36.824 | 39.007 | 0.072 | 0.068 | 1.059 | 0.962 | 1.156 | inconclusive | inconclusive |
| walking_only\|sparse | 214 | 168 | 36.315 | 34.629 | 0.021 | 0.022 | 0.954 | 0.797 | 1.117 | inconclusive | inconclusive |
| walking_only\|very_sparse | 244 | 93 | 24.561 | 22.195 | 0.011 | 0.009 | 0.904 | 0.759 | 1.113 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.150 | 0.125 | 0.182 | 0.164 | 0.150 | 0.190 | 0.075 | 0.033 | 0.611 | 0.329 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|intermediate | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|sparse | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|very_sparse | cycle\|dense+intermediate+sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|intermediate | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|intermediate+sparse+very_sparse |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 64.471 | 1.071 | 1.049 | 1.094 | 0.591 | 0.000 | 0.049 | 0.036 | 0.067 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.042 | 19.207 |
| 2 | 24.902 | 29.837 |
| 3 | 34.340 | 34.987 |
| 4 | 43.350 | 44.816 |
| 5 | 54.321 | 59.128 |
| 6 | 62.399 | 69.258 |
| 7 | 77.229 | 84.308 |
| 8 | 94.672 | 104.154 |
| 9 | 124.172 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 60 | 34 | 51.753 | - | 0.009 | - | - | - | - |  |  |
| car_driver\|employed | 4784 | 2793 | 67.549 | 73.456 | 0.337 | 0.319 | 1.087 | 1.052 | 1.126 | inconclusive | equivalent |
| car_driver\|other_inactive | 541 | 263 | 58.240 | 65.075 | 0.035 | 0.026 | 1.117 | 0.985 | 1.289 | inconclusive | inconclusive |
| car_driver\|retired | 1959 | 1798 | 54.813 | 57.483 | 0.112 | 0.126 | 1.049 | 0.993 | 1.109 | inconclusive | equivalent |
| car_driver\|unemployed | 288 | 240 | 59.681 | 66.606 | 0.018 | 0.024 | 1.116 | 0.972 | 1.261 | inconclusive | inconclusive |
| car_passenger_carpool\|children_6_17 | 17 | 19 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 102 | 59 | 54.595 | 73.276 | 0.009 | 0.004 | 1.342 | 1.055 | 1.640 | inconclusive | inconclusive |
| car_passenger_carpool\|other_inactive | 58 | 50 | 60.679 | 63.685 | 0.003 | 0.004 | 1.050 | 0.768 | 1.434 | inconclusive | inconclusive |
| car_passenger_carpool\|retired | 161 | 209 | 52.467 | 57.974 | 0.008 | 0.010 | 1.105 | 0.878 | 1.336 | inconclusive | inconclusive |
| car_passenger_carpool\|unemployed | 22 | 25 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 387 | 293 | 39.646 | 45.102 | 0.050 | 0.053 | 1.138 | 1.006 | 1.248 | inconclusive | inconclusive |
| car_passenger_household\|employed | 142 | 82 | 60.530 | 69.996 | 0.010 | 0.008 | 1.156 | 0.941 | 1.453 | inconclusive | inconclusive |
| car_passenger_household\|other_inactive | 103 | 81 | 70.608 | 66.479 | 0.007 | 0.008 | 0.942 | 0.733 | 1.228 | inconclusive | inconclusive |
| car_passenger_household\|retired | 230 | 303 | 57.734 | 63.126 | 0.015 | 0.022 | 1.093 | 0.961 | 1.272 | inconclusive | inconclusive |
| car_passenger_household\|unemployed | 25 | 22 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 42 | 17 | - | - | - | - | - | - | - |  |  |
| cycle\|employed | 117 | 74 | 59.117 | 55.194 | 0.008 | 0.010 | 0.934 | 0.756 | 1.175 | inconclusive | inconclusive |
| cycle\|other_inactive | 25 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 70 | 39 | 36.268 | - | 0.004 | - | - | - | - |  |  |
| cycle\|unemployed | 11 | 9 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 219 | 139 | 67.309 | 67.975 | 0.028 | 0.024 | 1.010 | 0.869 | 1.155 | inconclusive | inconclusive |
| multimodal\|employed | 608 | 351 | 107.238 | 111.597 | 0.045 | 0.044 | 1.041 | 0.971 | 1.115 | inconclusive | equivalent |
| multimodal\|other_inactive | 105 | 58 | 101.415 | 109.753 | 0.008 | 0.009 | 1.082 | 0.916 | 1.246 | inconclusive | inconclusive |
| multimodal\|retired | 201 | 153 | 102.808 | 100.410 | 0.009 | 0.011 | 0.977 | 0.856 | 1.097 | inconclusive | equivalent |
| multimodal\|unemployed | 55 | 40 | 99.918 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 176 | 47 | 67.926 | - | 0.020 | - | - | - | - |  |  |
| other\|employed | 165 | 80 | 65.838 | 73.673 | 0.013 | 0.012 | 1.119 | 0.937 | 1.443 | inconclusive | inconclusive |
| other\|other_inactive | 25 | 20 | - | - | - | - | - | - | - |  |  |
| other\|retired | 44 | 46 | - | - | - | - | - | - | - |  |  |
| other\|unemployed | 5 | 5 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 13 | - | - | - | - | - | - | - |  |  |
| train\|employed | 286 | 103 | 133.524 | 156.100 | 0.013 | 0.012 | 1.169 | 1.048 | 1.308 | inconclusive | inconclusive |
| train\|other_inactive | 33 | 15 | - | - | - | - | - | - | - |  |  |
| train\|retired | 34 | 13 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 5 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 89 | 118 | 87.585 | 85.601 | 0.012 | 0.022 | 0.977 | 0.776 | 1.247 | inconclusive | inconclusive |
| urban_pt\|employed | 511 | 250 | 93.063 | 96.119 | 0.029 | 0.030 | 1.033 | 0.956 | 1.115 | inconclusive | equivalent |
| urban_pt\|other_inactive | 176 | 120 | 91.653 | 97.106 | 0.013 | 0.016 | 1.059 | 0.941 | 1.219 | inconclusive | inconclusive |
| urban_pt\|retired | 216 | 147 | 80.578 | 92.290 | 0.009 | 0.011 | 1.145 | 1.024 | 1.285 | inconclusive | inconclusive |
| urban_pt\|unemployed | 52 | 63 | 115.256 | 97.582 | 0.003 | 0.007 | 0.847 | 0.628 | 1.192 | inconclusive | inconclusive |
| walking_only\|children_6_17 | 244 | 181 | 34.661 | 33.322 | 0.041 | 0.041 | 0.961 | 0.843 | 1.122 | inconclusive | inconclusive |
| walking_only\|employed | 482 | 253 | 39.356 | 41.248 | 0.033 | 0.030 | 1.048 | 0.926 | 1.177 | inconclusive | inconclusive |
| walking_only\|other_inactive | 258 | 156 | 35.887 | 46.548 | 0.019 | 0.015 | 1.297 | 1.132 | 1.525 | different | inconclusive |
| walking_only\|retired | 720 | 514 | 34.752 | 37.674 | 0.039 | 0.042 | 1.084 | 0.975 | 1.183 | inconclusive | inconclusive |
| walking_only\|unemployed | 128 | 93 | 43.564 | 45.803 | 0.010 | 0.008 | 1.051 | 0.773 | 1.396 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.175 | 0.147 | 0.210 | 0.199 | 0.180 | 0.240 | 0.081 | 0.000 | 0.546 | 0.686 | 0.000 | 0.001 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.030 | 64.542 | 1.070 | 1.047 | 1.092 | 0.662 | 0.000 | 0.050 | 0.036 | 0.068 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.046 | 19.206 |
| 2 | 24.936 | 29.837 |
| 3 | 34.312 | 34.980 |
| 4 | 43.260 | 44.813 |
| 5 | 54.318 | 59.127 |
| 6 | 61.882 | 69.256 |
| 7 | 77.094 | 84.302 |
| 8 | 94.692 | 104.150 |
| 9 | 124.372 | 134.642 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 897 | 581 | 57.168 | 63.506 | 0.067 | 0.060 | 1.111 | 1.022 | 1.234 | inconclusive | inconclusive |
| car_driver\|q2 | 1220 | 965 | 58.550 | 61.778 | 0.092 | 0.096 | 1.055 | 0.989 | 1.122 | inconclusive | equivalent |
| car_driver\|q3 | 1602 | 1093 | 61.599 | 66.354 | 0.113 | 0.108 | 1.077 | 0.995 | 1.147 | inconclusive | equivalent |
| car_driver\|q4 | 1691 | 1218 | 66.289 | 71.631 | 0.115 | 0.118 | 1.081 | 1.025 | 1.142 | inconclusive | equivalent |
| car_driver\|q5 | 2222 | 1275 | 70.001 | 75.031 | 0.125 | 0.120 | 1.072 | 1.023 | 1.131 | inconclusive | equivalent |
| car_passenger_carpool\|q1 | 102 | 109 | 51.996 | 60.081 | 0.006 | 0.008 | 1.155 | 0.950 | 1.413 | inconclusive | inconclusive |
| car_passenger_carpool\|q2 | 82 | 98 | 44.360 | 52.634 | 0.006 | 0.005 | 1.187 | 0.925 | 1.459 | inconclusive | inconclusive |
| car_passenger_carpool\|q3 | 70 | 67 | 54.597 | 56.980 | 0.005 | 0.004 | 1.044 | 0.732 | 1.500 | inconclusive | inconclusive |
| car_passenger_carpool\|q4+q5 | 107 | 90 | 62.456 | 65.897 | 0.007 | 0.007 | 1.055 | 0.836 | 1.323 | inconclusive | inconclusive |
| car_passenger_household\|q1 | 135 | 127 | 55.516 | 50.310 | 0.013 | 0.019 | 0.906 | 0.711 | 1.087 | inconclusive | inconclusive |
| car_passenger_household\|q2 | 182 | 176 | 44.497 | 55.760 | 0.019 | 0.022 | 1.253 | 1.059 | 1.471 | inconclusive | inconclusive |
| car_passenger_household\|q3 | 194 | 162 | 51.808 | 54.428 | 0.018 | 0.019 | 1.051 | 0.876 | 1.252 | inconclusive | inconclusive |
| car_passenger_household\|q4 | 183 | 173 | 42.318 | 51.912 | 0.020 | 0.020 | 1.227 | 1.032 | 1.452 | inconclusive | inconclusive |
| car_passenger_household\|q5 | 193 | 143 | 49.966 | 55.443 | 0.012 | 0.014 | 1.110 | 0.935 | 1.300 | inconclusive | inconclusive |
| cycle\|q1+q2+q3+q4+q5 | 265 | 154 | 45.428 | 51.509 | 0.021 | 0.019 | 1.134 | 0.950 | 1.347 | inconclusive | inconclusive |
| multimodal\|q1 | 164 | 107 | 83.421 | 106.742 | 0.015 | 0.015 | 1.280 | 1.093 | 1.452 | inconclusive | inconclusive |
| multimodal\|q2 | 200 | 130 | 97.928 | 86.126 | 0.021 | 0.017 | 0.879 | 0.770 | 0.999 | inconclusive | inconclusive |
| multimodal\|q3 | 215 | 147 | 93.392 | 91.363 | 0.018 | 0.020 | 0.978 | 0.876 | 1.102 | inconclusive | equivalent |
| multimodal\|q4 | 240 | 166 | 91.622 | 95.703 | 0.020 | 0.020 | 1.045 | 0.886 | 1.191 | inconclusive | inconclusive |
| multimodal\|q5 | 369 | 191 | 102.123 | 109.952 | 0.019 | 0.022 | 1.077 | 0.964 | 1.186 | inconclusive | inconclusive |
| other\|q1+q2+q3 | 242 | 129 | 66.412 | 69.097 | 0.025 | 0.016 | 1.040 | 0.919 | 1.195 | inconclusive | inconclusive |
| other\|q4+q5 | 173 | 69 | 64.736 | 74.840 | 0.014 | 0.008 | 1.156 | 0.934 | 1.443 | inconclusive | inconclusive |
| train\|q1+q2+q3+q4 | 216 | 99 | 127.014 | 156.503 | 0.012 | 0.015 | 1.232 | 1.079 | 1.406 | inconclusive | inconclusive |
| train\|q5 | 166 | 51 | 129.507 | 120.357 | 0.007 | 0.006 | 0.929 | 0.839 | 1.051 | inconclusive | inconclusive |
| urban_pt\|q1 | 240 | 241 | 97.800 | 91.099 | 0.019 | 0.029 | 0.931 | 0.806 | 1.062 | inconclusive | inconclusive |
| urban_pt\|q2 | 171 | 129 | 91.992 | 92.760 | 0.013 | 0.016 | 1.008 | 0.882 | 1.166 | inconclusive | inconclusive |
| urban_pt\|q3 | 173 | 107 | 90.479 | 97.051 | 0.010 | 0.014 | 1.073 | 0.955 | 1.198 | inconclusive | inconclusive |
| urban_pt\|q4 | 191 | 93 | 79.285 | 92.554 | 0.013 | 0.011 | 1.167 | 1.031 | 1.362 | inconclusive | inconclusive |
| urban_pt\|q5 | 269 | 130 | 92.532 | 94.272 | 0.011 | 0.016 | 1.019 | 0.927 | 1.102 | inconclusive | equivalent |
| walking_only\|q1 | 548 | 372 | 38.921 | 40.437 | 0.049 | 0.046 | 1.039 | 0.933 | 1.177 | inconclusive | inconclusive |
| walking_only\|q2 | 327 | 232 | 33.461 | 40.149 | 0.030 | 0.026 | 1.200 | 1.045 | 1.393 | inconclusive | inconclusive |
| walking_only\|q3 | 322 | 181 | 35.351 | 33.264 | 0.022 | 0.018 | 0.941 | 0.824 | 1.104 | inconclusive | inconclusive |
| walking_only\|q4 | 295 | 210 | 37.744 | 35.967 | 0.022 | 0.023 | 0.953 | 0.813 | 1.083 | inconclusive | inconclusive |
| walking_only\|q5 | 340 | 203 | 35.603 | 40.452 | 0.019 | 0.023 | 1.136 | 0.987 | 1.311 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.154 | 0.129 | 0.187 | 0.169 | 0.154 | 0.195 | 0.086 | 0.000 | 0.476 | 0.247 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q2 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q3 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q4 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q5 | cycle\|q1+q2+q3+q4+q5 |
| other\|q1 | other\|q1+q2+q3 |
| other\|q2 | other\|q1+q2+q3 |
| other\|q3 | other\|q1+q2+q3 |
| other\|q4 | other\|q4+q5 |
| other\|q5 | other\|q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 64.658 | 1.068 | 1.047 | 1.089 | 0.778 | 0.000 | 0.048 | 0.033 | 0.065 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.051 | 19.207 |
| 2 | 24.985 | 29.837 |
| 3 | 34.400 | 34.987 |
| 4 | 43.883 | 44.816 |
| 5 | 54.398 | 59.128 |
| 6 | 62.702 | 69.258 |
| 7 | 77.891 | 84.308 |
| 8 | 94.797 | 104.154 |
| 9 | 124.278 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3072 | 2390 | 63.233 | 65.029 | 0.197 | 0.200 | 1.028 | 0.978 | 1.084 | equivalent | equivalent |
| car_driver\|2+ | 4560 | 2736 | 63.782 | 70.753 | 0.314 | 0.302 | 1.109 | 1.074 | 1.149 | inconclusive | equivalent |
| car_driver\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 160 | 191 | 46.067 | 54.309 | 0.009 | 0.009 | 1.179 | 1.012 | 1.387 | inconclusive | inconclusive |
| car_passenger_carpool\|1 | 128 | 118 | 62.756 | 66.063 | 0.007 | 0.008 | 1.053 | 0.802 | 1.319 | inconclusive | inconclusive |
| car_passenger_carpool\|2+ | 73 | 54 | 54.305 | 58.575 | 0.008 | 0.007 | 1.079 | 0.843 | 1.348 | inconclusive | inconclusive |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 364 | 357 | 52.688 | 52.279 | 0.035 | 0.044 | 0.992 | 0.877 | 1.117 | inconclusive | equivalent |
| car_passenger_household\|2+ | 523 | 422 | 44.890 | 54.721 | 0.048 | 0.050 | 1.219 | 1.109 | 1.351 | different | inconclusive |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0+1+2+ | 265 | 152 | 45.428 | 51.573 | 0.021 | 0.019 | 1.135 | 0.951 | 1.349 | inconclusive | inconclusive |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 133 | 76 | 108.412 | 132.528 | 0.008 | 0.007 | 1.222 | 1.062 | 1.381 | inconclusive | inconclusive |
| multimodal\|1 | 414 | 261 | 94.010 | 99.363 | 0.034 | 0.031 | 1.057 | 0.966 | 1.159 | inconclusive | inconclusive |
| multimodal\|2+ | 641 | 403 | 92.159 | 93.020 | 0.052 | 0.055 | 1.009 | 0.929 | 1.093 | equivalent | equivalent |
| multimodal\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| other\|0+1 | 216 | 126 | 63.924 | 70.163 | 0.019 | 0.015 | 1.098 | 0.940 | 1.253 | inconclusive | inconclusive |
| other\|2+ | 199 | 72 | 67.601 | 72.260 | 0.020 | 0.010 | 1.069 | 0.891 | 1.308 | inconclusive | inconclusive |
| train\|0 | 125 | 50 | 134.027 | 169.047 | 0.005 | 0.006 | 1.261 | 1.048 | 1.453 | inconclusive | inconclusive |
| train\|1+2+ | 257 | 97 | 125.994 | 130.696 | 0.015 | 0.015 | 1.037 | 0.923 | 1.150 | inconclusive | inconclusive |
| train\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 600 | 405 | 97.294 | 93.416 | 0.031 | 0.041 | 0.960 | 0.864 | 1.063 | inconclusive | equivalent |
| urban_pt\|1 | 323 | 201 | 84.388 | 85.012 | 0.024 | 0.028 | 1.007 | 0.933 | 1.096 | equivalent | equivalent |
| urban_pt\|2+ | 121 | 89 | 87.529 | 106.499 | 0.010 | 0.016 | 1.217 | 1.071 | 1.388 | inconclusive | inconclusive |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 789 | 508 | 40.069 | 42.568 | 0.046 | 0.047 | 1.062 | 0.984 | 1.169 | inconclusive | inconclusive |
| walking_only\|1 | 733 | 475 | 34.801 | 40.061 | 0.064 | 0.059 | 1.151 | 1.040 | 1.271 | inconclusive | inconclusive |
| walking_only\|2+ | 310 | 212 | 35.118 | 29.017 | 0.032 | 0.028 | 0.826 | 0.695 | 0.939 | inconclusive | inconclusive |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.149 | 0.122 | 0.179 | 0.176 | 0.156 | 0.213 | - | 0.279 | 0.662 | - | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| cycle\|0 | cycle\|0+1+2+ |
| cycle\|1 | cycle\|0+1+2+ |
| cycle\|2+ | cycle\|0+1+2+ |
| other\|0 | other\|0+1 |
| other\|1 | other\|0+1 |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 64.541 | 1.070 | 1.048 | 1.091 | 0.662 | 0.002 | 0.049 | 0.035 | 0.067 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.057 | 19.207 |
| 2 | 24.953 | 29.837 |
| 3 | 34.371 | 34.987 |
| 4 | 43.682 | 44.816 |
| 5 | 54.367 | 59.128 |
| 6 | 62.535 | 69.258 |
| 7 | 77.512 | 84.308 |
| 8 | 94.689 | 104.154 |
| 9 | 124.214 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 202 | 118 | 49.283 | 56.565 | 0.020 | 0.021 | 1.148 | 0.936 | 1.366 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q1 | 123 | 176 | 57.710 | 58.563 | 0.026 | 0.037 | 1.015 | 0.806 | 1.238 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q2 | 136 | 111 | 47.260 | 53.426 | 0.025 | 0.022 | 1.130 | 0.972 | 1.334 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q3 | 104 | 80 | 49.486 | 53.893 | 0.015 | 0.015 | 1.089 | 0.861 | 1.335 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q4 | 128 | 89 | 46.963 | 52.875 | 0.019 | 0.017 | 1.126 | 0.908 | 1.376 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q1 | 119 | 57 | 46.023 | 48.746 | 0.016 | 0.012 | 1.059 | 0.800 | 1.360 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q2 | 171 | 73 | 58.335 | 43.221 | 0.018 | 0.014 | 0.741 | 0.617 | 0.891 | different | inconclusive |
| children_6_17\|sparse+very_sparse\|q3 | 135 | 85 | 52.169 | 54.267 | 0.016 | 0.015 | 1.040 | 0.848 | 1.274 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q4 | 135 | 72 | 47.034 | 47.371 | 0.016 | 0.012 | 1.007 | 0.843 | 1.188 | inconclusive | inconclusive |
| employed\|dense\|q1 | 86 | 67 | 83.904 | 78.948 | 0.009 | 0.008 | 0.941 | 0.757 | 1.137 | inconclusive | inconclusive |
| employed\|dense\|q2 | 110 | 74 | 80.561 | 82.133 | 0.010 | 0.009 | 1.020 | 0.814 | 1.250 | inconclusive | inconclusive |
| employed\|dense\|q3 | 195 | 87 | 75.777 | 75.898 | 0.015 | 0.009 | 1.002 | 0.885 | 1.139 | inconclusive | equivalent |
| employed\|dense\|q4 | 225 | 124 | 64.684 | 79.476 | 0.016 | 0.016 | 1.229 | 1.086 | 1.389 | inconclusive | inconclusive |
| employed\|dense\|q5 | 430 | 197 | 81.320 | 81.023 | 0.022 | 0.027 | 0.996 | 0.916 | 1.097 | equivalent | equivalent |
| employed\|intermediate\|q1 | 207 | 185 | 75.098 | 71.331 | 0.018 | 0.027 | 0.950 | 0.819 | 1.120 | inconclusive | inconclusive |
| employed\|intermediate\|q2 | 392 | 299 | 69.367 | 76.095 | 0.038 | 0.034 | 1.097 | 0.984 | 1.249 | inconclusive | inconclusive |
| employed\|intermediate\|q3 | 540 | 368 | 68.600 | 84.113 | 0.047 | 0.043 | 1.226 | 1.122 | 1.348 | different | inconclusive |
| employed\|intermediate\|q4 | 724 | 415 | 74.489 | 77.474 | 0.053 | 0.045 | 1.040 | 0.948 | 1.144 | inconclusive | equivalent |
| employed\|intermediate\|q5 | 1066 | 568 | 84.129 | 88.001 | 0.061 | 0.064 | 1.046 | 0.982 | 1.133 | inconclusive | equivalent |
| employed\|sparse+very_sparse\|q1 | 315 | 133 | 63.165 | 67.003 | 0.024 | 0.019 | 1.061 | 0.922 | 1.206 | inconclusive | inconclusive |
| employed\|sparse\|q2 | 145 | 99 | 51.994 | 58.571 | 0.014 | 0.014 | 1.127 | 0.941 | 1.338 | inconclusive | inconclusive |
| employed\|sparse\|q3 | 181 | 132 | 68.315 | 69.606 | 0.017 | 0.018 | 1.019 | 0.764 | 1.274 | inconclusive | inconclusive |
| employed\|sparse\|q4 | 224 | 170 | 71.787 | 75.209 | 0.024 | 0.022 | 1.048 | 0.875 | 1.271 | inconclusive | inconclusive |
| employed\|sparse\|q5 | 226 | 162 | 70.947 | 75.260 | 0.017 | 0.018 | 1.061 | 0.933 | 1.216 | inconclusive | inconclusive |
| employed\|very_sparse\|q2 | 444 | 197 | 63.291 | 79.264 | 0.028 | 0.023 | 1.252 | 1.101 | 1.443 | different | inconclusive |
| employed\|very_sparse\|q3 | 539 | 265 | 65.508 | 73.015 | 0.028 | 0.028 | 1.115 | 0.991 | 1.251 | inconclusive | inconclusive |
| employed\|very_sparse\|q4 | 631 | 264 | 68.341 | 82.629 | 0.035 | 0.024 | 1.209 | 1.102 | 1.304 | different | inconclusive |
| employed\|very_sparse\|q5 | 517 | 239 | 76.770 | 81.746 | 0.022 | 0.021 | 1.065 | 0.941 | 1.215 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 176 | 101 | 65.612 | 78.100 | 0.010 | 0.012 | 1.190 | 1.015 | 1.433 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 144 | 65 | 70.305 | 80.508 | 0.010 | 0.009 | 1.145 | 0.916 | 1.423 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 213 | 54 | 65.472 | 79.941 | 0.011 | 0.008 | 1.221 | 0.904 | 1.563 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate\|q2 | 155 | 130 | 64.943 | 79.085 | 0.013 | 0.013 | 1.218 | 1.037 | 1.453 | inconclusive | inconclusive |
| other_inactive\|dense\|q1 | 160 | 102 | 63.751 | 75.476 | 0.010 | 0.010 | 1.184 | 1.015 | 1.417 | inconclusive | inconclusive |
| other_inactive\|intermediate\|q1 | 211 | 185 | 63.571 | 68.386 | 0.019 | 0.016 | 1.076 | 0.898 | 1.281 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q1 | 154 | 82 | 69.143 | 62.592 | 0.011 | 0.009 | 0.905 | 0.660 | 1.242 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q2 | 111 | 59 | 60.427 | 68.217 | 0.008 | 0.007 | 1.129 | 0.883 | 1.458 | inconclusive | inconclusive |
| retired\|dense+intermediate\|q1 | 277 | 196 | 51.624 | 55.482 | 0.020 | 0.013 | 1.075 | 0.904 | 1.268 | inconclusive | inconclusive |
| retired\|dense\|q2 | 54 | 62 | 70.042 | 58.573 | 0.003 | 0.004 | 0.836 | 0.622 | 1.139 | inconclusive | inconclusive |
| retired\|dense\|q3 | 80 | 66 | 47.038 | 67.454 | 0.004 | 0.005 | 1.434 | 1.051 | 1.983 | inconclusive | inconclusive |
| retired\|dense\|q4 | 80 | 88 | 46.977 | 66.378 | 0.005 | 0.007 | 1.413 | 1.102 | 1.727 | different | inconclusive |
| retired\|dense\|q5 | 169 | 111 | 66.385 | 72.996 | 0.008 | 0.009 | 1.100 | 0.930 | 1.294 | inconclusive | inconclusive |
| retired\|intermediate\|q2 | 205 | 290 | 49.633 | 62.157 | 0.014 | 0.019 | 1.252 | 1.050 | 1.460 | inconclusive | inconclusive |
| retired\|intermediate\|q3 | 306 | 289 | 57.138 | 52.807 | 0.022 | 0.021 | 0.924 | 0.816 | 1.067 | inconclusive | inconclusive |
| retired\|intermediate\|q4 | 249 | 336 | 63.465 | 64.706 | 0.014 | 0.025 | 1.020 | 0.885 | 1.205 | inconclusive | inconclusive |
| retired\|intermediate\|q5 | 504 | 371 | 56.407 | 66.615 | 0.025 | 0.025 | 1.181 | 1.039 | 1.339 | inconclusive | inconclusive |
| retired\|sparse\|q1 | 84 | 71 | 34.378 | 53.236 | 0.007 | 0.005 | 1.549 | 1.189 | 2.002 | different | different |
| retired\|sparse\|q2 | 90 | 157 | 43.476 | 47.663 | 0.008 | 0.015 | 1.096 | 0.867 | 1.497 | inconclusive | inconclusive |
| retired\|sparse\|q3 | 106 | 117 | 47.094 | 59.524 | 0.009 | 0.010 | 1.264 | 0.951 | 1.623 | inconclusive | inconclusive |
| retired\|sparse\|q4 | 97 | 132 | 49.009 | 47.311 | 0.006 | 0.011 | 0.965 | 0.779 | 1.149 | inconclusive | inconclusive |
| retired\|sparse\|q5 | 120 | 114 | 58.688 | 57.858 | 0.008 | 0.009 | 0.986 | 0.798 | 1.211 | inconclusive | inconclusive |
| retired\|very_sparse\|q1 | 279 | 91 | 44.001 | 43.411 | 0.009 | 0.006 | 0.987 | 0.827 | 1.207 | inconclusive | inconclusive |
| retired\|very_sparse\|q2 | 235 | 202 | 55.501 | 48.919 | 0.011 | 0.012 | 0.881 | 0.764 | 1.049 | inconclusive | inconclusive |
| retired\|very_sparse\|q3 | 287 | 196 | 56.747 | 56.017 | 0.013 | 0.012 | 0.987 | 0.856 | 1.154 | inconclusive | inconclusive |
| retired\|very_sparse\|q4 | 163 | 186 | 58.771 | 58.965 | 0.006 | 0.012 | 1.003 | 0.847 | 1.185 | inconclusive | inconclusive |
| retired\|very_sparse\|q5 | 250 | 147 | 65.695 | 65.990 | 0.009 | 0.008 | 1.004 | 0.862 | 1.203 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 121 | 89 | 70.137 | 67.859 | 0.009 | 0.010 | 0.968 | 0.738 | 1.230 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 94 | 64 | 70.129 | 74.875 | 0.006 | 0.007 | 1.068 | 0.823 | 1.323 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 140 | 70 | 66.753 | 68.922 | 0.008 | 0.008 | 1.032 | 0.815 | 1.283 | inconclusive | inconclusive |
| unemployed\|dense+intermediate\|q1 | 148 | 207 | 54.899 | 79.353 | 0.013 | 0.019 | 1.445 | 1.174 | 1.786 | different | different |
| unemployed\|sparse+very_sparse\|q1 | 93 | 72 | 65.899 | 66.517 | 0.005 | 0.007 | 1.009 | 0.741 | 1.361 | inconclusive | inconclusive |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.051 | 0.047 | 0.071 | 0.057 | 0.054 | 0.079 | 0.103 | 0.024 | 0.148 | 0.437 | 0.000 | 0.001 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.030 | 63.773 | 1.082 | 1.057 | 1.107 | -0.107 | 0.000 | 0.056 | 0.041 | 0.074 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.006 | 19.206 |
| 2 | 24.751 | 29.837 |
| 3 | 34.085 | 34.980 |
| 4 | 40.724 | 44.813 |
| 5 | 54.018 | 59.127 |
| 6 | 60.552 | 69.256 |
| 7 | 75.106 | 84.302 |
| 8 | 94.326 | 104.150 |
| 9 | 121.851 | 134.642 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: cell levels

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4176 | 2885 | 61.504 | 65.182 | 0.245 | 0.247 | 1.060 | 1.018 | 1.106 | inconclusive | equivalent |
| couple_with_children | 5007 | 2704 | 65.685 | 71.101 | 0.492 | 0.446 | 1.082 | 1.047 | 1.113 | inconclusive | equivalent |
| other | 330 | 194 | 63.227 | 72.125 | 0.037 | 0.032 | 1.141 | 0.999 | 1.292 | inconclusive | inconclusive |
| single_parent | 1052 | 751 | 63.443 | 70.166 | 0.084 | 0.110 | 1.106 | 1.017 | 1.186 | inconclusive | inconclusive |
| single_person | 3441 | 2884 | 62.151 | 67.861 | 0.143 | 0.165 | 1.092 | 1.047 | 1.148 | inconclusive | equivalent |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: stability and explained variance

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.006 | 0.002 | 0.001 | 0.006 | 0.079 | 0.000 | 0.869 | 0.132 | 0.000 | 0.000 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed full-sample merges

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.038 | 63.746 | 1.083 | 1.059 | 1.104 | -0.134 | 0.000 | 0.054 | 0.041 | 0.072 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.012 | 19.207 |
| 2 | 24.732 | 29.837 |
| 3 | 34.089 | 34.987 |
| 4 | 41.386 | 44.816 |
| 5 | 54.122 | 59.128 |
| 6 | 61.023 | 69.258 |
| 7 | 74.987 | 84.308 |
| 8 | 94.178 | 104.154 |
| 9 | 121.519 | 134.639 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person mode use and user-day minutes

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 3636 | 2407 | 0.224 | 0.229 | 30.301 | 31.898 |
| bike | 401 | 253 | 0.026 | 0.026 | 37.961 | 39.303 |
| car_driver | 8336 | 5573 | 0.456 | 0.455 | 60.296 | 64.277 |
| car_passenger | 2025 | 1628 | 0.141 | 0.149 | 40.159 | 45.321 |
| urban_pt | 1397 | 915 | 0.075 | 0.096 | 72.142 | 74.998 |
| train | 559 | 241 | 0.023 | 0.028 | 117.436 | 127.094 |
| other | 615 | 320 | 0.049 | 0.034 | 58.972 | 59.407 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode model

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 51.975 | 57.032 | 53.496 | 1.521 | 0.295 | 2.772 | 3.535 | 2.130 | 4.847 | 0.031 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode deciles

Scope: Round-trip days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 0.000 | 0.000 |
| 2 | 9.167 | 9.898 |
| 3 | 19.807 | 19.990 |
| 4 | 29.901 | 33.658 |
| 5 | 41.066 | 44.660 |
| 6 | 54.991 | 59.358 |
| 7 | 69.342 | 74.232 |
| 8 | 89.827 | 94.054 |
| 9 | 119.221 | 124.799 |

n: 2008 14006, 2019 9418 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

## Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`)

### Grouping summary

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | 0.040 | 0.041 | - | - | - | - | - | - | 6 |
| category | 0.037 | 0.035 | - | - | - | - | - | - | 5 |
| category_x_density_x_income | 0.055 | 0.052 | - | - | - | - | - | - | 60 |
| day_mode_group | 0.147 | 0.133 | - | - | - | - | - | - | 9 |
| day_mode_group_x_category | 0.179 | 0.170 | - | - | - | - | - | - | 45 |
| day_mode_group_x_density | 0.152 | 0.141 | - | - | - | - | - | - | 25 |
| day_mode_group_x_income | 0.157 | 0.142 | - | - | - | - | - | - | 34 |
| day_mode_group_x_vehicles | 0.150 | 0.146 | - | - | - | - | - | - | 30 |
| day_purpose | 0.022 | 0.011 | - | - | - | - | - | - | 3 |
| density | 0.002 | 0.006 | - | - | - | - | - | - | 4 |
| household_type | 0.002 | 0.002 | - | - | - | - | - | - | 5 |
| income | 0.010 | 0.007 | - | - | - | - | - | - | 5 |
| none | 0.000 | 0.000 | - | - | - | - | - | - | 1 |
| vehicles | 0.000 | 0.004 | - | - | - | - | - | - | 4 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 14149 | 9504 | 66.958 | 71.647 | 1.000 | 1.000 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1256 | 865 | 51.828 | 54.865 | 0.169 | 0.165 | - | - | - |  |  |
| employed | 7300 | 4094 | 76.727 | 81.557 | 0.500 | 0.472 | - | - | - |  |  |
| other_inactive | 1330 | 783 | 66.324 | 75.529 | 0.092 | 0.084 | - | - | - |  |  |
| retired | 3665 | 3247 | 56.105 | 61.117 | 0.199 | 0.229 | - | - | - |  |  |
| unemployed | 597 | 505 | 64.574 | 74.899 | 0.040 | 0.051 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.037 | 0.028 | 0.046 | 0.035 | 0.027 | 0.045 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.640 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 999 | 659 | 45.880 | 47.967 | 0.129 | 0.128 | - | - | - |  |  |
| 15 | 2038 | 1171 | 73.293 | 78.911 | 0.212 | 0.172 | - | - | - |  |  |
| 30 | 2137 | 1089 | 76.445 | 82.289 | 0.168 | 0.140 | - | - | - |  |  |
| 40 | 2386 | 1239 | 76.491 | 81.664 | 0.160 | 0.159 | - | - | - |  |  |
| 50 | 2797 | 1634 | 70.310 | 79.312 | 0.135 | 0.140 | - | - | - |  |  |
| 60 | 3792 | 3712 | 55.791 | 62.536 | 0.197 | 0.262 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.040 | 0.031 | 0.050 | 0.041 | 0.032 | 0.053 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2016 | 1301 | 69.704 | 77.758 | 0.142 | 0.149 | - | - | - |  |  |
| intermediate | 5771 | 4379 | 68.824 | 73.500 | 0.446 | 0.460 | - | - | - |  |  |
| sparse | 1805 | 1539 | 62.163 | 63.082 | 0.172 | 0.186 | - | - | - |  |  |
| very_sparse | 4557 | 2285 | 65.303 | 70.823 | 0.241 | 0.206 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.002 | 0.001 | 0.007 | 0.006 | 0.003 | 0.012 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2264 | 1641 | 61.133 | 66.400 | 0.184 | 0.188 | - | - | - |  |  |
| q2 | 2382 | 1851 | 62.718 | 66.154 | 0.198 | 0.195 | - | - | - |  |  |
| q3 | 2766 | 1873 | 65.414 | 74.535 | 0.200 | 0.197 | - | - | - |  |  |
| q4 | 2910 | 2003 | 67.881 | 70.938 | 0.209 | 0.207 | - | - | - |  |  |
| q5 | 3827 | 2136 | 76.698 | 79.266 | 0.208 | 0.214 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.010 | 0.006 | 0.016 | 0.007 | 0.005 | 0.012 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2039 | 1397 | 68.361 | 74.436 | 0.115 | 0.125 | - | - | - |  |  |
| 1 | 5442 | 3969 | 66.243 | 68.354 | 0.387 | 0.391 | - | - | - |  |  |
| 2+ | 6668 | 4115 | 67.191 | 73.345 | 0.498 | 0.482 | - | - | - |  |  |
| unknown | 0 | 23 | - | - | - | - | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.002 | 0.004 | 0.001 | 0.015 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 6939 | 5457 | 57.931 | 64.967 | 0.445 | 0.465 | - | - | - |  |  |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7210 | 4046 | 74.184 | 77.450 | 0.555 | 0.535 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.022 | 0.016 | 0.028 | 0.011 | 0.006 | 0.017 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 7701 | 5166 | 66.477 | 71.589 | 0.510 | 0.502 | - | - | - |  |  |
| car_passenger_carpool | 373 | 369 | 56.902 | 62.338 | 0.024 | 0.024 | - | - | - |  |  |
| car_passenger_household | 891 | 791 | 49.358 | 55.418 | 0.082 | 0.095 | - | - | - |  |  |
| cycle | 263 | 152 | 45.467 | 51.864 | 0.021 | 0.018 | - | - | - |  |  |
| multimodal | 1231 | 761 | 100.862 | 101.721 | 0.097 | 0.095 | - | - | - |  |  |
| other | 421 | 203 | 66.872 | 74.830 | 0.039 | 0.025 | - | - | - |  |  |
| train | 398 | 162 | 142.096 | 155.665 | 0.022 | 0.021 | - | - | - |  |  |
| urban_pt | 1047 | 703 | 93.237 | 93.477 | 0.065 | 0.085 | - | - | - |  |  |
| walking_only | 1824 | 1197 | 36.674 | 38.637 | 0.140 | 0.134 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.147 | 0.123 | 0.173 | 0.133 | 0.112 | 0.162 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 533 | 379 | 69.797 | 86.858 | 0.041 | 0.041 | - | - | - |  |  |
| car_driver\|intermediate | 2866 | 2217 | 66.947 | 72.152 | 0.214 | 0.216 | - | - | - |  |  |
| car_driver\|sparse | 1142 | 950 | 64.979 | 64.716 | 0.099 | 0.108 | - | - | - |  |  |
| car_driver\|very_sparse | 3160 | 1620 | 65.905 | 71.566 | 0.156 | 0.137 | - | - | - |  |  |
| car_passenger_carpool\|dense+intermediate | 199 | 228 | 58.786 | 63.792 | 0.014 | 0.014 | - | - | - |  |  |
| car_passenger_carpool\|sparse | 54 | 64 | 57.182 | 60.163 | 0.006 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|very_sparse | 120 | 77 | 51.369 | 60.858 | 0.005 | 0.005 | - | - | - |  |  |
| car_passenger_household\|dense | 67 | 59 | 49.552 | 69.596 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|intermediate | 322 | 366 | 49.410 | 56.294 | 0.035 | 0.044 | - | - | - |  |  |
| car_passenger_household\|sparse | 130 | 161 | 44.202 | 51.210 | 0.016 | 0.021 | - | - | - |  |  |
| car_passenger_household\|very_sparse | 372 | 205 | 52.528 | 52.656 | 0.024 | 0.022 | - | - | - |  |  |
| cycle\|dense+intermediate+sparse+very_sparse | 263 | 152 | 45.467 | 51.864 | 0.021 | 0.018 | - | - | - |  |  |
| multimodal\|dense | 197 | 112 | 117.642 | 108.469 | 0.013 | 0.013 | - | - | - |  |  |
| multimodal\|intermediate | 540 | 364 | 103.984 | 104.894 | 0.046 | 0.048 | - | - | - |  |  |
| multimodal\|sparse | 127 | 102 | 86.881 | 90.748 | 0.015 | 0.014 | - | - | - |  |  |
| multimodal\|very_sparse | 367 | 183 | 93.732 | 97.475 | 0.023 | 0.020 | - | - | - |  |  |
| other\|dense+intermediate | 180 | 116 | 64.344 | 69.852 | 0.017 | 0.014 | - | - | - |  |  |
| other\|sparse+very_sparse | 241 | 87 | 68.821 | 80.707 | 0.022 | 0.011 | - | - | - |  |  |
| train\|dense+intermediate+sparse+very_sparse | 398 | 162 | 142.096 | 155.665 | 0.022 | 0.021 | - | - | - |  |  |
| urban_pt\|dense | 548 | 301 | 89.485 | 89.907 | 0.029 | 0.037 | - | - | - |  |  |
| urban_pt\|intermediate+sparse+very_sparse | 499 | 402 | 96.225 | 96.183 | 0.036 | 0.048 | - | - | - |  |  |
| walking_only\|dense | 472 | 312 | 39.803 | 44.523 | 0.038 | 0.036 | - | - | - |  |  |
| walking_only\|intermediate | 895 | 624 | 36.943 | 39.010 | 0.071 | 0.067 | - | - | - |  |  |
| walking_only\|sparse | 213 | 168 | 36.427 | 34.629 | 0.020 | 0.022 | - | - | - |  |  |
| walking_only\|very_sparse | 244 | 93 | 24.483 | 22.195 | 0.011 | 0.009 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.152 | 0.130 | 0.181 | 0.141 | 0.124 | 0.170 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|intermediate | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|sparse | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|very_sparse | cycle\|dense+intermediate+sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|intermediate | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|intermediate+sparse+very_sparse |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 60 | 35 | 51.753 | - | 0.009 | - | - | - | - |  |  |
| car_driver\|employed | 4838 | 2816 | 71.497 | 76.716 | 0.337 | 0.320 | - | - | - |  |  |
| car_driver\|other_inactive | 541 | 263 | 59.458 | 67.144 | 0.035 | 0.025 | - | - | - |  |  |
| car_driver\|retired | 1974 | 1808 | 55.712 | 60.123 | 0.111 | 0.127 | - | - | - |  |  |
| car_driver\|unemployed | 288 | 240 | 59.681 | 67.154 | 0.018 | 0.024 | - | - | - |  |  |
| car_passenger_carpool\|children_6_17 | 18 | 19 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 106 | 60 | 56.052 | 80.669 | 0.009 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|other_inactive | 58 | 50 | 60.679 | 63.685 | 0.003 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|retired | 167 | 213 | 58.954 | 61.267 | 0.008 | 0.010 | - | - | - |  |  |
| car_passenger_carpool\|unemployed | 23 | 25 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 386 | 294 | 40.239 | 45.714 | 0.049 | 0.053 | - | - | - |  |  |
| car_passenger_household\|employed | 143 | 85 | 64.020 | 72.458 | 0.010 | 0.008 | - | - | - |  |  |
| car_passenger_household\|other_inactive | 106 | 81 | 72.361 | 66.479 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|retired | 232 | 307 | 58.857 | 65.410 | 0.015 | 0.022 | - | - | - |  |  |
| car_passenger_household\|unemployed | 24 | 24 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 42 | 16 | - | - | - | - | - | - | - |  |  |
| cycle\|employed | 115 | 73 | 59.304 | 55.349 | 0.008 | 0.010 | - | - | - |  |  |
| cycle\|other_inactive | 25 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 70 | 39 | 36.268 | - | 0.004 | - | - | - | - |  |  |
| cycle\|unemployed | 11 | 9 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 223 | 141 | 69.337 | 68.349 | 0.028 | 0.024 | - | - | - |  |  |
| multimodal\|employed | 638 | 364 | 117.270 | 117.360 | 0.047 | 0.045 | - | - | - |  |  |
| multimodal\|other_inactive | 108 | 60 | 102.297 | 112.528 | 0.008 | 0.009 | - | - | - |  |  |
| multimodal\|retired | 206 | 155 | 110.323 | 101.810 | 0.009 | 0.011 | - | - | - |  |  |
| multimodal\|unemployed | 56 | 41 | 101.492 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 176 | 48 | 67.926 | - | 0.020 | - | - | - | - |  |  |
| other\|employed | 170 | 81 | 68.440 | 75.463 | 0.013 | 0.012 | - | - | - |  |  |
| other\|other_inactive | 25 | 22 | - | - | - | - | - | - | - |  |  |
| other\|retired | 45 | 47 | - | - | - | - | - | - | - |  |  |
| other\|unemployed | 5 | 5 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 13 | - | - | - | - | - | - | - |  |  |
| train\|employed | 300 | 111 | 152.492 | 165.644 | 0.015 | 0.013 | - | - | - |  |  |
| train\|other_inactive | 35 | 16 | - | - | - | - | - | - | - |  |  |
| train\|retired | 34 | 16 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 5 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 89 | 118 | 92.709 | 85.601 | 0.012 | 0.022 | - | - | - |  |  |
| urban_pt\|employed | 511 | 251 | 93.657 | 96.645 | 0.028 | 0.030 | - | - | - |  |  |
| urban_pt\|other_inactive | 176 | 120 | 91.526 | 97.106 | 0.013 | 0.015 | - | - | - |  |  |
| urban_pt\|retired | 219 | 149 | 87.473 | 93.280 | 0.009 | 0.011 | - | - | - |  |  |
| urban_pt\|unemployed | 52 | 63 | 117.149 | 97.582 | 0.003 | 0.007 | - | - | - |  |  |
| walking_only\|children_6_17 | 243 | 181 | 34.703 | 33.322 | 0.040 | 0.040 | - | - | - |  |  |
| walking_only\|employed | 479 | 253 | 39.418 | 41.248 | 0.033 | 0.030 | - | - | - |  |  |
| walking_only\|other_inactive | 256 | 156 | 35.887 | 46.548 | 0.018 | 0.015 | - | - | - |  |  |
| walking_only\|retired | 718 | 513 | 34.930 | 37.650 | 0.038 | 0.041 | - | - | - |  |  |
| walking_only\|unemployed | 128 | 93 | 43.564 | 45.803 | 0.010 | 0.008 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.179 | 0.157 | 0.212 | 0.170 | 0.148 | 0.210 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.640 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 899 | 587 | 58.032 | 65.794 | 0.066 | 0.060 | - | - | - |  |  |
| car_driver\|q2 | 1224 | 965 | 61.015 | 62.959 | 0.092 | 0.096 | - | - | - |  |  |
| car_driver\|q3 | 1611 | 1103 | 63.961 | 73.708 | 0.112 | 0.108 | - | - | - |  |  |
| car_driver\|q4 | 1712 | 1220 | 68.815 | 72.689 | 0.115 | 0.117 | - | - | - |  |  |
| car_driver\|q5 | 2255 | 1291 | 75.090 | 78.364 | 0.125 | 0.120 | - | - | - |  |  |
| car_passenger_carpool\|q1 | 104 | 110 | 53.059 | 59.459 | 0.006 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|q2 | 85 | 98 | 48.591 | 52.634 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q3 | 74 | 70 | 61.103 | 66.167 | 0.006 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|q4+q5 | 110 | 91 | 63.872 | 70.957 | 0.007 | 0.007 | - | - | - |  |  |
| car_passenger_household\|q1 | 135 | 129 | 53.458 | 51.261 | 0.013 | 0.019 | - | - | - |  |  |
| car_passenger_household\|q2 | 179 | 177 | 44.493 | 58.033 | 0.019 | 0.022 | - | - | - |  |  |
| car_passenger_household\|q3 | 195 | 163 | 53.428 | 57.001 | 0.018 | 0.019 | - | - | - |  |  |
| car_passenger_household\|q4 | 184 | 175 | 43.441 | 53.182 | 0.020 | 0.020 | - | - | - |  |  |
| car_passenger_household\|q5 | 198 | 147 | 55.569 | 57.834 | 0.013 | 0.015 | - | - | - |  |  |
| cycle\|q1+q2+q3+q4+q5 | 263 | 152 | 45.467 | 51.864 | 0.021 | 0.018 | - | - | - |  |  |
| multimodal\|q1 | 168 | 111 | 88.073 | 111.248 | 0.015 | 0.015 | - | - | - |  |  |
| multimodal\|q2 | 206 | 134 | 100.102 | 91.899 | 0.021 | 0.017 | - | - | - |  |  |
| multimodal\|q3 | 225 | 150 | 104.174 | 91.450 | 0.020 | 0.020 | - | - | - |  |  |
| multimodal\|q4 | 247 | 169 | 96.289 | 98.436 | 0.021 | 0.020 | - | - | - |  |  |
| multimodal\|q5 | 385 | 197 | 112.669 | 114.838 | 0.020 | 0.023 | - | - | - |  |  |
| other\|q1+q2 | 176 | 93 | 68.283 | 64.742 | 0.019 | 0.011 | - | - | - |  |  |
| other\|q3+q4+q5 | 245 | 110 | 65.600 | 82.355 | 0.021 | 0.014 | - | - | - |  |  |
| train\|q1+q2 | 81 | 50 | 143.562 | 148.931 | 0.006 | 0.008 | - | - | - |  |  |
| train\|q3+q4+q5 | 317 | 112 | 141.516 | 159.569 | 0.015 | 0.014 | - | - | - |  |  |
| urban_pt\|q1 | 241 | 240 | 101.044 | 91.448 | 0.019 | 0.028 | - | - | - |  |  |
| urban_pt\|q2 | 172 | 130 | 93.803 | 93.247 | 0.013 | 0.016 | - | - | - |  |  |
| urban_pt\|q3 | 172 | 109 | 90.733 | 97.674 | 0.009 | 0.014 | - | - | - |  |  |
| urban_pt\|q4 | 194 | 93 | 83.681 | 92.554 | 0.013 | 0.011 | - | - | - |  |  |
| urban_pt\|q5 | 268 | 131 | 92.254 | 94.192 | 0.010 | 0.016 | - | - | - |  |  |
| walking_only\|q1 | 544 | 372 | 39.002 | 40.437 | 0.048 | 0.045 | - | - | - |  |  |
| walking_only\|q2 | 327 | 232 | 33.461 | 40.149 | 0.030 | 0.025 | - | - | - |  |  |
| walking_only\|q3 | 321 | 180 | 35.396 | 33.157 | 0.022 | 0.018 | - | - | - |  |  |
| walking_only\|q4 | 295 | 210 | 37.744 | 35.967 | 0.022 | 0.023 | - | - | - |  |  |
| walking_only\|q5 | 337 | 203 | 35.996 | 40.461 | 0.019 | 0.023 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.157 | 0.135 | 0.185 | 0.142 | 0.125 | 0.176 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q2 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q3 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q4 | cycle\|q1+q2+q3+q4+q5 |
| cycle\|q5 | cycle\|q1+q2+q3+q4+q5 |
| other\|q1 | other\|q1+q2 |
| other\|q2 | other\|q1+q2 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2 |
| train\|q2 | train\|q1+q2 |
| train\|q3 | train\|q3+q4+q5 |
| train\|q4 | train\|q3+q4+q5 |
| train\|q5 | train\|q3+q4+q5 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3103 | 2399 | 65.870 | 68.072 | 0.197 | 0.199 | - | - | - |  |  |
| car_driver\|2+ | 4598 | 2761 | 66.859 | 73.953 | 0.313 | 0.302 | - | - | - |  |  |
| car_driver\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 165 | 192 | 48.328 | 55.192 | 0.009 | 0.009 | - | - | - |  |  |
| car_passenger_carpool\|1 | 132 | 122 | 68.329 | 69.751 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|2+ | 76 | 54 | 56.094 | 62.504 | 0.008 | 0.007 | - | - | - |  |  |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 363 | 363 | 52.586 | 54.740 | 0.034 | 0.044 | - | - | - |  |  |
| car_passenger_household\|2+ | 528 | 426 | 47.080 | 56.099 | 0.048 | 0.050 | - | - | - |  |  |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0+1+2+ | 263 | 150 | 45.467 | 51.931 | 0.021 | 0.018 | - | - | - |  |  |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 136 | 77 | 113.430 | 133.865 | 0.008 | 0.007 | - | - | - |  |  |
| multimodal\|1 | 432 | 270 | 102.854 | 105.311 | 0.035 | 0.031 | - | - | - |  |  |
| multimodal\|2+ | 663 | 413 | 97.707 | 95.480 | 0.054 | 0.056 | - | - | - |  |  |
| multimodal\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| other\|0 | 70 | 50 | 57.624 | 75.465 | 0.005 | 0.003 | - | - | - |  |  |
| other\|1 | 149 | 79 | 68.643 | 71.471 | 0.014 | 0.011 | - | - | - |  |  |
| other\|2+ | 202 | 74 | 68.050 | 78.165 | 0.020 | 0.011 | - | - | - |  |  |
| train\|0 | 127 | 52 | 137.628 | 177.296 | 0.005 | 0.006 | - | - | - |  |  |
| train\|1+2+ | 271 | 107 | 143.403 | 142.053 | 0.017 | 0.015 | - | - | - |  |  |
| train\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 601 | 405 | 97.587 | 93.416 | 0.031 | 0.041 | - | - | - |  |  |
| urban_pt\|1 | 324 | 203 | 88.592 | 85.924 | 0.024 | 0.028 | - | - | - |  |  |
| urban_pt\|2+ | 122 | 90 | 90.865 | 106.367 | 0.010 | 0.016 | - | - | - |  |  |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 788 | 508 | 40.059 | 42.568 | 0.046 | 0.047 | - | - | - |  |  |
| walking_only\|1 | 727 | 474 | 34.863 | 40.051 | 0.062 | 0.059 | - | - | - |  |  |
| walking_only\|2+ | 309 | 212 | 35.337 | 29.017 | 0.032 | 0.028 | - | - | - |  |  |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.150 | 0.125 | 0.177 | 0.146 | 0.125 | 0.188 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| cycle\|0 | cycle\|0+1+2+ |
| cycle\|1 | cycle\|0+1+2+ |
| cycle\|2+ | cycle\|0+1+2+ |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 203 | 119 | 49.660 | 57.844 | 0.021 | 0.021 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q1 | 123 | 176 | 57.710 | 58.563 | 0.026 | 0.037 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q2 | 136 | 111 | 47.488 | 53.426 | 0.025 | 0.022 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q3 | 104 | 80 | 49.486 | 62.654 | 0.015 | 0.015 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q4 | 128 | 90 | 47.080 | 54.249 | 0.019 | 0.017 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q1 | 119 | 57 | 51.394 | 48.746 | 0.016 | 0.012 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q2 | 172 | 73 | 59.342 | 43.221 | 0.018 | 0.014 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q3 | 136 | 86 | 52.896 | 58.146 | 0.015 | 0.015 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q4 | 135 | 73 | 50.532 | 47.661 | 0.016 | 0.012 | - | - | - |  |  |
| employed\|dense\|q1 | 86 | 67 | 83.904 | 83.688 | 0.009 | 0.008 | - | - | - |  |  |
| employed\|dense\|q2 | 110 | 74 | 80.573 | 82.133 | 0.009 | 0.009 | - | - | - |  |  |
| employed\|dense\|q3 | 197 | 89 | 77.519 | 111.425 | 0.015 | 0.010 | - | - | - |  |  |
| employed\|dense\|q4 | 230 | 125 | 67.754 | 79.746 | 0.016 | 0.016 | - | - | - |  |  |
| employed\|dense\|q5 | 441 | 200 | 91.344 | 83.826 | 0.022 | 0.027 | - | - | - |  |  |
| employed\|intermediate\|q1 | 209 | 187 | 75.378 | 71.898 | 0.018 | 0.027 | - | - | - |  |  |
| employed\|intermediate\|q2 | 394 | 299 | 75.423 | 77.971 | 0.038 | 0.034 | - | - | - |  |  |
| employed\|intermediate\|q3 | 544 | 373 | 71.797 | 87.007 | 0.047 | 0.043 | - | - | - |  |  |
| employed\|intermediate\|q4 | 734 | 420 | 80.276 | 79.332 | 0.053 | 0.046 | - | - | - |  |  |
| employed\|intermediate\|q5 | 1076 | 577 | 90.704 | 90.491 | 0.061 | 0.064 | - | - | - |  |  |
| employed\|sparse+very_sparse\|q1 | 316 | 135 | 66.774 | 70.447 | 0.024 | 0.019 | - | - | - |  |  |
| employed\|sparse\|q2 | 146 | 99 | 52.997 | 58.571 | 0.014 | 0.014 | - | - | - |  |  |
| employed\|sparse\|q3 | 184 | 132 | 81.410 | 69.606 | 0.017 | 0.018 | - | - | - |  |  |
| employed\|sparse\|q4 | 228 | 172 | 73.212 | 77.388 | 0.024 | 0.022 | - | - | - |  |  |
| employed\|sparse\|q5 | 239 | 163 | 83.936 | 77.196 | 0.018 | 0.018 | - | - | - |  |  |
| employed\|very_sparse\|q2 | 447 | 197 | 67.299 | 81.062 | 0.029 | 0.023 | - | - | - |  |  |
| employed\|very_sparse\|q3 | 545 | 270 | 68.124 | 79.271 | 0.028 | 0.029 | - | - | - |  |  |
| employed\|very_sparse\|q4 | 644 | 266 | 71.813 | 85.312 | 0.035 | 0.024 | - | - | - |  |  |
| employed\|very_sparse\|q5 | 530 | 249 | 81.047 | 92.269 | 0.022 | 0.022 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 177 | 102 | 65.735 | 81.891 | 0.010 | 0.012 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 145 | 65 | 72.151 | 80.508 | 0.010 | 0.009 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 214 | 54 | 66.705 | 79.941 | 0.011 | 0.008 | - | - | - |  |  |
| other_inactive\|dense+intermediate\|q2 | 156 | 131 | 66.133 | 80.376 | 0.013 | 0.013 | - | - | - |  |  |
| other_inactive\|dense\|q1 | 160 | 103 | 63.766 | 76.873 | 0.010 | 0.010 | - | - | - |  |  |
| other_inactive\|intermediate\|q1 | 212 | 186 | 64.746 | 70.100 | 0.019 | 0.016 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q1 | 155 | 82 | 69.287 | 62.592 | 0.011 | 0.009 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q2 | 111 | 60 | 62.606 | 69.695 | 0.008 | 0.007 | - | - | - |  |  |
| retired\|dense+intermediate\|q1 | 278 | 199 | 52.837 | 60.597 | 0.020 | 0.013 | - | - | - |  |  |
| retired\|dense\|q2 | 54 | 62 | 70.042 | 58.573 | 0.003 | 0.004 | - | - | - |  |  |
| retired\|dense\|q3 | 81 | 67 | 61.777 | 77.232 | 0.004 | 0.005 | - | - | - |  |  |
| retired\|dense\|q4 | 80 | 88 | 46.977 | 66.378 | 0.005 | 0.007 | - | - | - |  |  |
| retired\|dense\|q5 | 169 | 111 | 66.385 | 72.996 | 0.008 | 0.009 | - | - | - |  |  |
| retired\|intermediate\|q2 | 208 | 293 | 53.061 | 66.790 | 0.014 | 0.020 | - | - | - |  |  |
| retired\|intermediate\|q3 | 307 | 292 | 57.180 | 55.674 | 0.022 | 0.021 | - | - | - |  |  |
| retired\|intermediate\|q4 | 253 | 336 | 66.322 | 64.706 | 0.014 | 0.024 | - | - | - |  |  |
| retired\|intermediate\|q5 | 508 | 372 | 59.474 | 67.445 | 0.025 | 0.025 | - | - | - |  |  |
| retired\|sparse\|q1 | 84 | 73 | 34.378 | 55.767 | 0.007 | 0.005 | - | - | - |  |  |
| retired\|sparse\|q2 | 90 | 157 | 43.476 | 47.663 | 0.007 | 0.014 | - | - | - |  |  |
| retired\|sparse\|q3 | 108 | 121 | 48.253 | 70.878 | 0.009 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q4 | 97 | 133 | 49.009 | 48.166 | 0.006 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q5 | 122 | 115 | 59.456 | 64.697 | 0.008 | 0.009 | - | - | - |  |  |
| retired\|very_sparse\|q1 | 281 | 92 | 45.615 | 44.932 | 0.009 | 0.006 | - | - | - |  |  |
| retired\|very_sparse\|q2 | 236 | 204 | 56.040 | 51.879 | 0.010 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q3 | 289 | 197 | 58.228 | 56.903 | 0.013 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q4 | 165 | 186 | 59.683 | 59.259 | 0.006 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q5 | 255 | 149 | 69.351 | 66.050 | 0.009 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 122 | 90 | 70.058 | 72.609 | 0.009 | 0.010 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 94 | 64 | 70.129 | 74.875 | 0.006 | 0.007 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 140 | 71 | 68.013 | 74.567 | 0.008 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate\|q1 | 148 | 208 | 55.497 | 79.582 | 0.012 | 0.018 | - | - | - |  |  |
| unemployed\|sparse+very_sparse\|q1 | 93 | 72 | 65.899 | 66.517 | 0.005 | 0.007 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.055 | 0.050 | 0.074 | 0.052 | 0.049 | 0.079 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.640 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: cell levels

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4213 | 2915 | 64.014 | 67.824 | 0.244 | 0.247 | - | - | - |  |  |
| couple_with_children | 5060 | 2722 | 69.425 | 73.647 | 0.493 | 0.446 | - | - | - |  |  |
| other | 332 | 196 | 63.958 | 75.459 | 0.036 | 0.032 | - | - | - |  |  |
| single_parent | 1062 | 755 | 66.127 | 71.755 | 0.084 | 0.110 | - | - | - |  |  |
| single_person | 3482 | 2916 | 64.729 | 71.150 | 0.143 | 0.165 | - | - | - |  |  |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: stability and explained variance

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.002 | 0.001 | 0.006 | 0.002 | 0.001 | 0.005 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed full-sample merges

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71.647 | - | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person mode use and user-day minutes

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 3646 | 2415 | 0.224 | 0.230 | 30.288 | 31.879 |
| bike | 404 | 253 | 0.026 | 0.026 | 38.051 | 39.303 |
| car_driver | 8432 | 5620 | 0.462 | 0.459 | 63.058 | 67.247 |
| car_passenger | 2067 | 1655 | 0.144 | 0.151 | 42.301 | 47.182 |
| urban_pt | 1410 | 920 | 0.076 | 0.096 | 73.974 | 75.402 |
| train | 588 | 257 | 0.026 | 0.029 | 132.785 | 134.044 |
| other | 625 | 329 | 0.050 | 0.035 | 59.948 | 64.420 |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode model

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 55.075 | 59.663 | - | - | - | - | - | - | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode deciles

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14149, 2019 9504 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

## Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`)

### Grouping summary

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| day_mode_group_x_category | 0.151 | 0.161 | 0.104 | 0.117 | 1.087 | 1.060 | 1.110 | 0.054 | 45 |
| day_mode_group_x_income | 0.133 | 0.128 | 0.108 | 0.000 | 1.088 | 1.062 | 1.111 | 0.053 | 35 |
| day_mode_group_x_vehicles | 0.126 | 0.134 | - | 0.000 | 1.090 | 1.066 | 1.114 | 0.054 | 31 |
| day_mode_group | 0.124 | 0.117 | 0.093 | 0.169 | 1.091 | 1.066 | 1.114 | 0.054 | 9 |
| day_mode_group_x_density | 0.128 | 0.120 | 0.097 | 0.074 | 1.091 | 1.067 | 1.114 | 0.055 | 26 |
| category_x_density_x_income | 0.041 | 0.051 | 0.116 | 0.024 | 1.097 | 1.068 | 1.120 | 0.058 | 60 |
| density | 0.004 | 0.004 | 0.093 | 0.000 | 1.097 | 1.069 | 1.121 | 0.058 | 4 |
| income | 0.008 | 0.007 | 0.093 | 0.000 | 1.097 | 1.069 | 1.120 | 0.058 | 5 |
| vehicles | 0.000 | 0.005 | - | 0.390 | 1.097 | 1.069 | 1.120 | 0.058 | 4 |
| none | 0.000 | 0.000 | 0.093 | 0.000 | 1.098 | 1.070 | 1.121 | 0.058 | 1 |
| household_type | 0.000 | 0.001 | 0.095 | 0.249 | 1.100 | 1.073 | 1.121 | 0.059 | 5 |
| day_purpose | 0.011 | 0.010 | - | 0.000 | 1.100 | 1.072 | 1.124 | 0.059 | 3 |
| category | 0.023 | 0.037 | 0.094 | 0.000 | 1.102 | 1.075 | 1.127 | 0.061 | 5 |
| age_band | 0.028 | 0.045 | 0.099 | 0.128 | 1.110 | 1.084 | 1.135 | 0.066 | 6 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 14342 | 9638 | 67.587 | 74.196 | 1.000 | 1.000 | 1.098 | 1.070 | 1.121 | inconclusive | equivalent |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.093 | 0.000 | 1.000 | 0.093 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.587 | 1.098 | 1.070 | 1.121 | 0.000 | 0.000 | 0.058 | 0.045 | 0.079 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.148 | 19.384 |
| 2 | 28.017 | 29.886 |
| 3 | 35.911 | 39.897 |
| 4 | 44.667 | 49.482 |
| 5 | 56.945 | 59.634 |
| 6 | 64.880 | 74.191 |
| 7 | 79.755 | 89.442 |
| 8 | 99.553 | 109.614 |
| 9 | 129.540 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1265 | 877 | 53.671 | 56.114 | 0.168 | 0.165 | 1.046 | 0.953 | 1.117 | inconclusive | equivalent |
| employed | 7243 | 4075 | 74.658 | 83.739 | 0.489 | 0.464 | 1.122 | 1.090 | 1.159 | inconclusive | inconclusive |
| other_inactive | 1357 | 803 | 68.408 | 77.980 | 0.092 | 0.085 | 1.140 | 1.054 | 1.234 | inconclusive | inconclusive |
| retired | 3862 | 3357 | 61.911 | 65.766 | 0.209 | 0.234 | 1.062 | 1.019 | 1.108 | inconclusive | equivalent |
| unemployed | 614 | 516 | 67.404 | 78.043 | 0.041 | 0.052 | 1.158 | 1.028 | 1.304 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.023 | 0.017 | 0.032 | 0.037 | 0.029 | 0.049 | 0.094 | 0.000 | 0.388 | 0.147 | 0.000 | 0.001 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 67.307 | 1.102 | 1.075 | 1.127 | -0.281 | 0.000 | 0.061 | 0.048 | 0.084 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.124 | 19.383 |
| 2 | 27.427 | 29.886 |
| 3 | 34.951 | 39.897 |
| 4 | 44.553 | 49.480 |
| 5 | 55.894 | 59.633 |
| 6 | 64.757 | 74.189 |
| 7 | 79.676 | 89.438 |
| 8 | 99.475 | 109.613 |
| 9 | 129.428 | 146.234 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1005 | 669 | 48.009 | 48.236 | 0.128 | 0.127 | 1.005 | 0.908 | 1.091 | equivalent | equivalent |
| 15 | 2034 | 1176 | 73.877 | 81.809 | 0.209 | 0.171 | 1.107 | 1.047 | 1.166 | inconclusive | inconclusive |
| 30 | 2134 | 1096 | 73.163 | 82.818 | 0.166 | 0.139 | 1.132 | 1.072 | 1.185 | inconclusive | inconclusive |
| 40 | 2373 | 1235 | 73.528 | 84.623 | 0.156 | 0.156 | 1.151 | 1.093 | 1.205 | inconclusive | inconclusive |
| 50 | 2809 | 1629 | 71.832 | 80.826 | 0.135 | 0.138 | 1.125 | 1.060 | 1.191 | inconclusive | inconclusive |
| 60 | 3987 | 3833 | 61.578 | 67.668 | 0.206 | 0.268 | 1.099 | 1.056 | 1.143 | inconclusive | equivalent |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.028 | 0.020 | 0.038 | 0.045 | 0.037 | 0.058 | 0.099 | 0.128 | 0.364 | 0.141 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 66.856 | 1.110 | 1.084 | 1.135 | -0.730 | 0.000 | 0.066 | 0.053 | 0.087 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.084 | 19.384 |
| 2 | 26.004 | 29.886 |
| 3 | 34.641 | 39.897 |
| 4 | 44.348 | 49.482 |
| 5 | 54.856 | 59.634 |
| 6 | 64.557 | 74.191 |
| 7 | 79.523 | 89.442 |
| 8 | 99.354 | 109.614 |
| 9 | 129.419 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2040 | 1323 | 70.611 | 77.279 | 0.142 | 0.149 | 1.094 | 1.033 | 1.160 | inconclusive | inconclusive |
| intermediate | 5811 | 4438 | 69.935 | 76.228 | 0.442 | 0.459 | 1.090 | 1.055 | 1.126 | inconclusive | equivalent |
| sparse | 1836 | 1563 | 61.881 | 67.436 | 0.173 | 0.187 | 1.090 | 1.004 | 1.153 | inconclusive | inconclusive |
| very_sparse | 4655 | 2314 | 65.619 | 73.587 | 0.243 | 0.205 | 1.121 | 1.076 | 1.170 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.004 | 0.001 | 0.008 | 0.004 | 0.001 | 0.008 | 0.093 | 0.000 | 0.450 | 0.115 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.642 | 1.097 | 1.069 | 1.121 | 0.055 | 0.000 | 0.058 | 0.045 | 0.081 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.146 | 19.384 |
| 2 | 27.959 | 29.886 |
| 3 | 35.899 | 39.897 |
| 4 | 44.667 | 49.482 |
| 5 | 56.900 | 59.634 |
| 6 | 64.894 | 74.191 |
| 7 | 79.770 | 89.442 |
| 8 | 99.581 | 109.614 |
| 9 | 129.572 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2352 | 1692 | 63.384 | 69.332 | 0.190 | 0.191 | 1.094 | 1.030 | 1.148 | inconclusive | equivalent |
| q2 | 2438 | 1902 | 63.213 | 69.956 | 0.198 | 0.198 | 1.107 | 1.050 | 1.168 | inconclusive | inconclusive |
| q3 | 2812 | 1896 | 66.627 | 75.178 | 0.200 | 0.196 | 1.128 | 1.069 | 1.187 | inconclusive | inconclusive |
| q4 | 2922 | 2015 | 68.327 | 73.808 | 0.207 | 0.204 | 1.080 | 1.025 | 1.131 | inconclusive | equivalent |
| q5 | 3818 | 2133 | 75.883 | 82.022 | 0.205 | 0.211 | 1.081 | 1.038 | 1.128 | inconclusive | equivalent |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.008 | 0.004 | 0.014 | 0.007 | 0.004 | 0.012 | 0.093 | 0.000 | 0.604 | 0.121 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.634 | 1.097 | 1.069 | 1.120 | 0.048 | 0.000 | 0.058 | 0.045 | 0.079 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.148 | 19.384 |
| 2 | 28.037 | 29.886 |
| 3 | 35.991 | 39.897 |
| 4 | 44.679 | 49.482 |
| 5 | 57.069 | 59.634 |
| 6 | 64.899 | 74.191 |
| 7 | 79.771 | 89.442 |
| 8 | 99.571 | 109.614 |
| 9 | 129.571 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2117 | 1462 | 70.140 | 78.400 | 0.119 | 0.128 | 1.118 | 1.034 | 1.205 | inconclusive | inconclusive |
| 1 | 5512 | 4024 | 67.355 | 70.462 | 0.388 | 0.392 | 1.046 | 1.006 | 1.086 | equivalent | equivalent |
| 2+ | 6713 | 4128 | 67.153 | 75.866 | 0.493 | 0.477 | 1.130 | 1.092 | 1.163 | inconclusive | inconclusive |
| unknown | 0 | 24 | - | - | - | - | - | - | - |  |  |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.003 | 0.005 | 0.002 | 0.018 | - | 0.390 | 0.390 | - | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.617 | 1.097 | 1.069 | 1.120 | 0.030 | 0.002 | 0.058 | 0.045 | 0.079 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.142 | 19.384 |
| 2 | 27.882 | 29.886 |
| 3 | 35.693 | 39.897 |
| 4 | 44.656 | 49.482 |
| 5 | 56.904 | 59.634 |
| 6 | 64.881 | 74.191 |
| 7 | 79.769 | 89.442 |
| 8 | 99.574 | 109.614 |
| 9 | 129.591 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7250 | 5623 | 61.779 | 68.499 | 0.462 | 0.475 | 1.109 | 1.071 | 1.150 | inconclusive | equivalent |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7092 | 4014 | 72.564 | 79.357 | 0.538 | 0.525 | 1.094 | 1.059 | 1.126 | inconclusive | equivalent |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.011 | 0.006 | 0.015 | 0.010 | 0.005 | 0.015 | - | 0.000 | 1.000 | - | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.438 | 1.100 | 1.072 | 1.124 | -0.148 | 0.000 | 0.059 | 0.046 | 0.081 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.134 | 19.384 |
| 2 | 27.689 | 29.886 |
| 3 | 35.224 | 39.897 |
| 4 | 44.605 | 49.482 |
| 5 | 56.414 | 59.634 |
| 6 | 64.823 | 74.191 |
| 7 | 79.714 | 89.442 |
| 8 | 99.512 | 109.614 |
| 9 | 129.499 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 7648 | 5126 | 66.702 | 73.563 | 0.502 | 0.491 | 1.103 | 1.070 | 1.140 | inconclusive | equivalent |
| car_passenger_carpool | 361 | 365 | 56.045 | 63.233 | 0.023 | 0.023 | 1.128 | 0.984 | 1.273 | inconclusive | inconclusive |
| car_passenger_household | 880 | 780 | 51.595 | 57.055 | 0.080 | 0.092 | 1.106 | 1.017 | 1.207 | inconclusive | inconclusive |
| cycle | 297 | 175 | 53.636 | 72.120 | 0.025 | 0.022 | 1.345 | 1.114 | 1.663 | different | inconclusive |
| multimodal | 1272 | 771 | 99.051 | 103.595 | 0.097 | 0.095 | 1.046 | 0.980 | 1.097 | equivalent | equivalent |
| other | 412 | 198 | 67.362 | 76.961 | 0.038 | 0.024 | 1.142 | 1.018 | 1.295 | inconclusive | inconclusive |
| train | 382 | 149 | 129.560 | 147.247 | 0.019 | 0.020 | 1.137 | 1.013 | 1.251 | inconclusive | inconclusive |
| urban_pt | 1043 | 695 | 95.532 | 95.896 | 0.064 | 0.083 | 1.004 | 0.940 | 1.066 | equivalent | equivalent |
| walking_only | 2047 | 1379 | 43.335 | 47.903 | 0.152 | 0.149 | 1.105 | 1.040 | 1.173 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.124 | 0.099 | 0.152 | 0.117 | 0.103 | 0.139 | 0.093 | 0.169 | 0.666 | 0.296 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.023 | 1.091 | 1.066 | 1.114 | 0.437 | 0.000 | 0.054 | 0.044 | 0.076 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.164 | 19.384 |
| 2 | 28.434 | 29.886 |
| 3 | 36.869 | 39.897 |
| 4 | 44.792 | 49.482 |
| 5 | 57.919 | 59.634 |
| 6 | 65.405 | 74.191 |
| 7 | 79.884 | 89.442 |
| 8 | 99.724 | 109.614 |
| 9 | 129.770 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 534 | 378 | 71.743 | 77.727 | 0.041 | 0.040 | 1.083 | 1.002 | 1.179 | inconclusive | inconclusive |
| car_driver\|intermediate | 2849 | 2204 | 68.173 | 74.877 | 0.211 | 0.211 | 1.098 | 1.051 | 1.151 | inconclusive | inconclusive |
| car_driver\|sparse | 1129 | 946 | 63.512 | 69.038 | 0.097 | 0.106 | 1.087 | 0.991 | 1.175 | inconclusive | inconclusive |
| car_driver\|very_sparse | 3136 | 1598 | 65.338 | 73.849 | 0.153 | 0.134 | 1.130 | 1.072 | 1.187 | inconclusive | inconclusive |
| car_passenger_carpool\|dense+intermediate | 192 | 226 | 58.305 | 64.067 | 0.013 | 0.013 | 1.099 | 0.926 | 1.263 | inconclusive | inconclusive |
| car_passenger_carpool\|sparse | 52 | 61 | 57.299 | 57.794 | 0.006 | 0.006 | 1.009 | 0.671 | 1.344 | inconclusive | inconclusive |
| car_passenger_carpool\|very_sparse | 117 | 78 | 48.250 | 67.539 | 0.005 | 0.005 | 1.400 | 1.104 | 1.832 | different | inconclusive |
| car_passenger_household\|dense | 69 | 58 | 52.695 | 67.656 | 0.007 | 0.008 | 1.284 | 1.010 | 1.579 | inconclusive | inconclusive |
| car_passenger_household\|intermediate | 318 | 361 | 51.125 | 57.326 | 0.034 | 0.043 | 1.121 | 0.981 | 1.254 | inconclusive | inconclusive |
| car_passenger_household\|sparse | 128 | 159 | 45.213 | 54.732 | 0.015 | 0.020 | 1.211 | 0.986 | 1.587 | inconclusive | inconclusive |
| car_passenger_household\|very_sparse | 365 | 202 | 55.957 | 54.996 | 0.024 | 0.021 | 0.983 | 0.867 | 1.121 | inconclusive | equivalent |
| cycle\|dense+intermediate | 165 | 122 | 54.061 | 71.577 | 0.015 | 0.015 | 1.324 | 1.084 | 1.635 | inconclusive | inconclusive |
| cycle\|sparse+very_sparse | 132 | 53 | 52.935 | 73.353 | 0.009 | 0.007 | 1.386 | 0.848 | 2.083 | inconclusive | inconclusive |
| multimodal\|dense | 190 | 112 | 111.999 | 106.651 | 0.012 | 0.012 | 0.952 | 0.812 | 1.091 | inconclusive | inconclusive |
| multimodal\|intermediate | 544 | 366 | 102.704 | 106.151 | 0.045 | 0.048 | 1.034 | 0.941 | 1.118 | inconclusive | equivalent |
| multimodal\|sparse | 135 | 104 | 86.547 | 99.987 | 0.015 | 0.014 | 1.155 | 0.959 | 1.341 | inconclusive | inconclusive |
| multimodal\|very_sparse | 403 | 189 | 93.384 | 98.122 | 0.024 | 0.020 | 1.051 | 0.932 | 1.164 | inconclusive | inconclusive |
| other\|dense+intermediate | 178 | 114 | 64.091 | 76.057 | 0.017 | 0.013 | 1.187 | 0.971 | 1.400 | inconclusive | inconclusive |
| other\|sparse+very_sparse | 234 | 84 | 69.937 | 78.031 | 0.021 | 0.011 | 1.116 | 0.944 | 1.325 | inconclusive | inconclusive |
| train\|dense+intermediate+sparse+very_sparse | 382 | 149 | 129.560 | 147.247 | 0.019 | 0.020 | 1.137 | 1.013 | 1.251 | inconclusive | inconclusive |
| urban_pt\|dense | 550 | 300 | 92.247 | 93.009 | 0.029 | 0.036 | 1.008 | 0.927 | 1.099 | equivalent | equivalent |
| urban_pt\|intermediate+sparse+very_sparse | 493 | 395 | 98.226 | 98.121 | 0.035 | 0.047 | 0.999 | 0.924 | 1.084 | equivalent | equivalent |
| walking_only\|dense | 503 | 344 | 44.039 | 54.663 | 0.039 | 0.039 | 1.241 | 1.087 | 1.400 | inconclusive | inconclusive |
| walking_only\|intermediate | 958 | 702 | 43.238 | 47.038 | 0.073 | 0.072 | 1.088 | 1.000 | 1.194 | inconclusive | inconclusive |
| walking_only\|sparse | 250 | 196 | 44.157 | 43.123 | 0.025 | 0.025 | 0.977 | 0.792 | 1.120 | inconclusive | inconclusive |
| walking_only\|very_sparse | 336 | 137 | 40.701 | 41.221 | 0.015 | 0.013 | 1.013 | 0.842 | 1.266 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.128 | 0.103 | 0.160 | 0.120 | 0.108 | 0.146 | 0.097 | 0.074 | 0.143 | 0.336 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate |
| cycle\|intermediate | cycle\|dense+intermediate |
| cycle\|sparse | cycle\|sparse+very_sparse |
| cycle\|very_sparse | cycle\|sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|intermediate | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|intermediate+sparse+very_sparse |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.013 | 1.091 | 1.067 | 1.114 | 0.427 | 0.000 | 0.055 | 0.044 | 0.077 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.160 | 19.384 |
| 2 | 28.276 | 29.886 |
| 3 | 36.542 | 39.897 |
| 4 | 44.760 | 49.482 |
| 5 | 57.638 | 59.634 |
| 6 | 65.245 | 74.191 |
| 7 | 79.866 | 89.442 |
| 8 | 99.712 | 109.614 |
| 9 | 129.795 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 58 | 34 | 59.548 | - | 0.009 | - | - | - | - |  |  |
| car_driver\|employed | 4776 | 2787 | 70.075 | 79.385 | 0.330 | 0.312 | 1.133 | 1.095 | 1.180 | inconclusive | inconclusive |
| car_driver\|other_inactive | 545 | 264 | 59.399 | 66.916 | 0.034 | 0.025 | 1.127 | 0.987 | 1.293 | inconclusive | inconclusive |
| car_driver\|retired | 1978 | 1797 | 59.737 | 61.825 | 0.111 | 0.124 | 1.035 | 0.976 | 1.093 | equivalent | equivalent |
| car_driver\|unemployed | 291 | 240 | 65.077 | 70.079 | 0.018 | 0.024 | 1.077 | 0.937 | 1.234 | inconclusive | inconclusive |
| car_passenger_carpool\|children_6_17 | 17 | 19 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 102 | 59 | 55.660 | 74.190 | 0.008 | 0.004 | 1.333 | 1.038 | 1.634 | inconclusive | inconclusive |
| car_passenger_carpool\|other_inactive | 57 | 50 | 61.753 | 64.510 | 0.003 | 0.004 | 1.045 | 0.775 | 1.431 | inconclusive | inconclusive |
| car_passenger_carpool\|retired | 162 | 210 | 57.329 | 65.354 | 0.008 | 0.009 | 1.140 | 0.924 | 1.370 | inconclusive | inconclusive |
| car_passenger_carpool\|unemployed | 22 | 25 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 374 | 292 | 41.270 | 47.030 | 0.047 | 0.052 | 1.140 | 1.008 | 1.260 | inconclusive | inconclusive |
| car_passenger_household\|employed | 142 | 81 | 60.827 | 71.446 | 0.010 | 0.008 | 1.175 | 0.965 | 1.479 | inconclusive | inconclusive |
| car_passenger_household\|other_inactive | 105 | 80 | 76.828 | 79.145 | 0.007 | 0.008 | 1.030 | 0.740 | 1.412 | inconclusive | inconclusive |
| car_passenger_household\|retired | 234 | 305 | 66.380 | 68.215 | 0.015 | 0.021 | 1.028 | 0.904 | 1.166 | inconclusive | inconclusive |
| car_passenger_household\|unemployed | 25 | 22 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 50 | 21 | 39.391 | - | 0.008 | - | - | - | - |  |  |
| cycle\|employed | 120 | 77 | 62.797 | 62.667 | 0.008 | 0.010 | 0.998 | 0.816 | 1.245 | inconclusive | inconclusive |
| cycle\|other_inactive | 25 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 90 | 50 | 58.554 | 79.495 | 0.005 | 0.004 | 1.358 | 0.927 | 1.902 | inconclusive | inconclusive |
| cycle\|unemployed | 12 | 12 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 238 | 144 | 70.136 | 72.226 | 0.029 | 0.024 | 1.030 | 0.878 | 1.163 | inconclusive | inconclusive |
| multimodal\|employed | 636 | 366 | 112.845 | 117.539 | 0.045 | 0.045 | 1.042 | 0.959 | 1.129 | inconclusive | equivalent |
| multimodal\|other_inactive | 110 | 60 | 102.691 | 117.309 | 0.008 | 0.009 | 1.142 | 0.946 | 1.293 | inconclusive | inconclusive |
| multimodal\|retired | 232 | 161 | 115.568 | 105.933 | 0.010 | 0.012 | 0.917 | 0.812 | 1.018 | inconclusive | inconclusive |
| multimodal\|unemployed | 56 | 40 | 105.795 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 173 | 47 | 69.081 | - | 0.020 | - | - | - | - |  |  |
| other\|employed | 162 | 80 | 68.108 | 85.328 | 0.013 | 0.012 | 1.253 | 1.025 | 1.536 | inconclusive | inconclusive |
| other\|other_inactive | 25 | 20 | - | - | - | - | - | - | - |  |  |
| other\|retired | 47 | 46 | - | - | - | - | - | - | - |  |  |
| other\|unemployed | 5 | 5 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 13 | - | - | - | - | - | - | - |  |  |
| train\|employed | 285 | 102 | 134.297 | 157.781 | 0.013 | 0.012 | 1.175 | 1.058 | 1.303 | inconclusive | inconclusive |
| train\|other_inactive | 34 | 15 | - | - | - | - | - | - | - |  |  |
| train\|retired | 34 | 13 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 5 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 89 | 115 | 93.249 | 88.053 | 0.012 | 0.021 | 0.944 | 0.743 | 1.173 | inconclusive | inconclusive |
| urban_pt\|employed | 511 | 248 | 95.249 | 98.734 | 0.028 | 0.029 | 1.037 | 0.961 | 1.117 | inconclusive | equivalent |
| urban_pt\|other_inactive | 176 | 119 | 95.499 | 98.271 | 0.013 | 0.015 | 1.029 | 0.925 | 1.168 | inconclusive | inconclusive |
| urban_pt\|retired | 215 | 148 | 93.116 | 96.910 | 0.009 | 0.011 | 1.041 | 0.917 | 1.163 | inconclusive | inconclusive |
| urban_pt\|unemployed | 52 | 63 | 115.425 | 102.036 | 0.003 | 0.006 | 0.884 | 0.657 | 1.217 | inconclusive | inconclusive |
| walking_only\|children_6_17 | 247 | 192 | 37.376 | 34.763 | 0.039 | 0.042 | 0.930 | 0.804 | 1.095 | inconclusive | inconclusive |
| walking_only\|employed | 509 | 275 | 43.169 | 47.187 | 0.034 | 0.031 | 1.093 | 0.978 | 1.219 | inconclusive | inconclusive |
| walking_only\|other_inactive | 280 | 180 | 43.909 | 55.673 | 0.020 | 0.017 | 1.268 | 1.095 | 1.466 | inconclusive | inconclusive |
| walking_only\|retired | 870 | 627 | 47.960 | 54.705 | 0.047 | 0.050 | 1.141 | 1.032 | 1.250 | inconclusive | inconclusive |
| walking_only\|unemployed | 141 | 104 | 44.029 | 58.350 | 0.012 | 0.009 | 1.325 | 0.997 | 1.755 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.151 | 0.124 | 0.191 | 0.161 | 0.145 | 0.196 | 0.104 | 0.117 | 0.191 | 0.780 | 0.000 | 0.001 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 68.271 | 1.087 | 1.060 | 1.110 | 0.683 | 0.000 | 0.054 | 0.042 | 0.076 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.171 | 19.383 |
| 2 | 28.585 | 29.886 |
| 3 | 36.750 | 39.897 |
| 4 | 44.793 | 49.480 |
| 5 | 57.938 | 59.633 |
| 6 | 65.473 | 74.189 |
| 7 | 79.920 | 89.438 |
| 8 | 99.808 | 109.613 |
| 9 | 129.969 | 146.234 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 902 | 580 | 58.789 | 67.826 | 0.066 | 0.059 | 1.154 | 1.053 | 1.267 | inconclusive | inconclusive |
| car_driver\|q2 | 1222 | 965 | 61.314 | 66.504 | 0.091 | 0.094 | 1.085 | 1.011 | 1.158 | inconclusive | inconclusive |
| car_driver\|q3 | 1603 | 1092 | 65.167 | 70.591 | 0.110 | 0.105 | 1.083 | 1.005 | 1.154 | inconclusive | inconclusive |
| car_driver\|q4 | 1691 | 1218 | 68.999 | 76.936 | 0.112 | 0.115 | 1.115 | 1.059 | 1.176 | inconclusive | inconclusive |
| car_driver\|q5 | 2230 | 1271 | 74.206 | 81.471 | 0.123 | 0.117 | 1.098 | 1.040 | 1.156 | inconclusive | inconclusive |
| car_passenger_carpool\|q1 | 103 | 110 | 55.162 | 62.067 | 0.006 | 0.008 | 1.125 | 0.934 | 1.365 | inconclusive | inconclusive |
| car_passenger_carpool\|q2 | 81 | 98 | 46.402 | 55.521 | 0.006 | 0.005 | 1.197 | 0.954 | 1.468 | inconclusive | inconclusive |
| car_passenger_carpool\|q3 | 69 | 67 | 55.530 | 60.542 | 0.005 | 0.004 | 1.090 | 0.758 | 1.584 | inconclusive | inconclusive |
| car_passenger_carpool\|q4+q5 | 108 | 90 | 65.277 | 72.371 | 0.007 | 0.007 | 1.109 | 0.889 | 1.390 | inconclusive | inconclusive |
| car_passenger_household\|q1 | 136 | 128 | 62.338 | 52.050 | 0.013 | 0.018 | 0.835 | 0.657 | 1.008 | inconclusive | inconclusive |
| car_passenger_household\|q2 | 180 | 177 | 45.436 | 60.148 | 0.019 | 0.021 | 1.324 | 1.076 | 1.644 | inconclusive | inconclusive |
| car_passenger_household\|q3 | 193 | 161 | 54.388 | 61.011 | 0.018 | 0.019 | 1.122 | 0.937 | 1.365 | inconclusive | inconclusive |
| car_passenger_household\|q4 | 179 | 172 | 45.875 | 52.353 | 0.019 | 0.019 | 1.141 | 0.958 | 1.352 | inconclusive | inconclusive |
| car_passenger_household\|q5 | 192 | 142 | 54.367 | 60.137 | 0.012 | 0.014 | 1.106 | 0.927 | 1.301 | inconclusive | inconclusive |
| cycle\|q1+q2 | 121 | 74 | 54.482 | 81.680 | 0.010 | 0.010 | 1.499 | 1.083 | 2.068 | inconclusive | inconclusive |
| cycle\|q3+q4+q5 | 176 | 101 | 53.026 | 64.529 | 0.014 | 0.012 | 1.217 | 1.022 | 1.508 | inconclusive | inconclusive |
| multimodal\|q1 | 179 | 109 | 86.893 | 108.396 | 0.016 | 0.015 | 1.247 | 1.079 | 1.428 | inconclusive | inconclusive |
| multimodal\|q2 | 218 | 136 | 99.096 | 89.201 | 0.021 | 0.017 | 0.900 | 0.788 | 1.012 | inconclusive | inconclusive |
| multimodal\|q3 | 229 | 156 | 103.004 | 103.569 | 0.019 | 0.021 | 1.005 | 0.854 | 1.162 | inconclusive | inconclusive |
| multimodal\|q4 | 258 | 169 | 99.470 | 100.677 | 0.021 | 0.019 | 1.012 | 0.874 | 1.147 | inconclusive | equivalent |
| multimodal\|q5 | 388 | 201 | 104.589 | 113.798 | 0.020 | 0.023 | 1.088 | 0.986 | 1.202 | inconclusive | inconclusive |
| other\|q1+q2 | 171 | 91 | 69.271 | 70.479 | 0.018 | 0.011 | 1.017 | 0.857 | 1.216 | inconclusive | inconclusive |
| other\|q3+q4+q5 | 241 | 107 | 65.628 | 82.045 | 0.020 | 0.014 | 1.250 | 1.092 | 1.473 | inconclusive | inconclusive |
| train\|q1+q2+q3+q4 | 217 | 98 | 128.008 | 156.696 | 0.012 | 0.014 | 1.224 | 1.074 | 1.394 | inconclusive | inconclusive |
| train\|q5 | 165 | 51 | 132.170 | 124.948 | 0.007 | 0.006 | 0.945 | 0.845 | 1.071 | inconclusive | inconclusive |
| urban_pt\|q1 | 239 | 241 | 104.139 | 94.034 | 0.019 | 0.028 | 0.903 | 0.770 | 1.052 | inconclusive | inconclusive |
| urban_pt\|q2 | 171 | 128 | 96.336 | 96.507 | 0.013 | 0.015 | 1.002 | 0.889 | 1.152 | inconclusive | inconclusive |
| urban_pt\|q3 | 174 | 104 | 93.358 | 101.339 | 0.009 | 0.014 | 1.085 | 0.967 | 1.209 | inconclusive | inconclusive |
| urban_pt\|q4 | 192 | 93 | 81.830 | 94.347 | 0.013 | 0.010 | 1.153 | 1.020 | 1.334 | inconclusive | inconclusive |
| urban_pt\|q5 | 267 | 129 | 97.725 | 94.975 | 0.010 | 0.016 | 0.972 | 0.872 | 1.069 | inconclusive | equivalent |
| walking_only\|q1 | 616 | 427 | 45.711 | 48.122 | 0.053 | 0.049 | 1.053 | 0.934 | 1.208 | inconclusive | inconclusive |
| walking_only\|q2 | 373 | 281 | 39.876 | 49.952 | 0.032 | 0.030 | 1.253 | 1.104 | 1.437 | different | inconclusive |
| walking_only\|q3 | 367 | 217 | 43.787 | 50.984 | 0.024 | 0.022 | 1.164 | 1.015 | 1.361 | inconclusive | inconclusive |
| walking_only\|q4 | 327 | 230 | 42.394 | 42.080 | 0.022 | 0.025 | 0.993 | 0.842 | 1.145 | inconclusive | inconclusive |
| walking_only\|q5 | 364 | 224 | 43.065 | 48.084 | 0.020 | 0.024 | 1.117 | 0.974 | 1.281 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.133 | 0.110 | 0.167 | 0.128 | 0.116 | 0.154 | 0.108 | 0.000 | 0.033 | 0.405 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2 |
| cycle\|q2 | cycle\|q1+q2 |
| cycle\|q3 | cycle\|q3+q4+q5 |
| cycle\|q4 | cycle\|q3+q4+q5 |
| cycle\|q5 | cycle\|q3+q4+q5 |
| other\|q1 | other\|q1+q2 |
| other\|q2 | other\|q1+q2 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.222 | 1.088 | 1.062 | 1.111 | 0.635 | 0.000 | 0.053 | 0.041 | 0.074 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.169 | 19.384 |
| 2 | 28.622 | 29.886 |
| 3 | 37.037 | 39.897 |
| 4 | 44.832 | 49.482 |
| 5 | 58.179 | 59.634 |
| 6 | 65.959 | 74.191 |
| 7 | 79.950 | 89.442 |
| 8 | 99.825 | 109.614 |
| 9 | 129.896 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3074 | 2387 | 66.542 | 70.444 | 0.193 | 0.196 | 1.059 | 1.005 | 1.117 | inconclusive | equivalent |
| car_driver\|2+ | 4574 | 2732 | 66.802 | 75.653 | 0.309 | 0.295 | 1.133 | 1.094 | 1.180 | inconclusive | inconclusive |
| car_driver\|unknown | 0 | 7 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 162 | 191 | 50.287 | 60.656 | 0.008 | 0.009 | 1.206 | 0.990 | 1.410 | inconclusive | inconclusive |
| car_passenger_carpool\|1 | 126 | 119 | 65.151 | 70.101 | 0.007 | 0.008 | 1.076 | 0.829 | 1.364 | inconclusive | inconclusive |
| car_passenger_carpool\|2+ | 73 | 54 | 54.554 | 58.842 | 0.008 | 0.007 | 1.079 | 0.849 | 1.363 | inconclusive | inconclusive |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 366 | 357 | 57.154 | 55.290 | 0.034 | 0.043 | 0.967 | 0.845 | 1.114 | inconclusive | inconclusive |
| car_passenger_household\|2+ | 514 | 421 | 47.467 | 58.681 | 0.046 | 0.049 | 1.236 | 1.120 | 1.371 | different | inconclusive |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0 | 89 | 53 | 51.239 | 74.922 | 0.006 | 0.007 | 1.462 | 1.040 | 2.053 | inconclusive | inconclusive |
| cycle\|1 | 119 | 68 | 56.799 | 65.321 | 0.009 | 0.008 | 1.150 | 0.903 | 1.531 | inconclusive | inconclusive |
| cycle\|2+ | 89 | 52 | 52.103 | 78.458 | 0.009 | 0.006 | 1.506 | 0.994 | 2.106 | inconclusive | inconclusive |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 134 | 79 | 110.794 | 135.922 | 0.008 | 0.008 | 1.227 | 1.051 | 1.380 | inconclusive | inconclusive |
| multimodal\|1 | 443 | 270 | 102.220 | 103.561 | 0.034 | 0.031 | 1.013 | 0.898 | 1.125 | inconclusive | equivalent |
| multimodal\|2+ | 695 | 420 | 95.394 | 99.197 | 0.054 | 0.056 | 1.040 | 0.958 | 1.114 | inconclusive | equivalent |
| multimodal\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| other\|0+1 | 217 | 127 | 65.056 | 76.912 | 0.019 | 0.014 | 1.182 | 0.996 | 1.377 | inconclusive | inconclusive |
| other\|2+ | 195 | 71 | 69.591 | 77.033 | 0.019 | 0.010 | 1.107 | 0.928 | 1.358 | inconclusive | inconclusive |
| train\|0 | 126 | 50 | 134.762 | 169.047 | 0.005 | 0.005 | 1.254 | 1.042 | 1.437 | inconclusive | inconclusive |
| train\|1+2+ | 256 | 97 | 127.879 | 132.609 | 0.015 | 0.014 | 1.037 | 0.926 | 1.155 | inconclusive | inconclusive |
| train\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 600 | 404 | 99.555 | 96.120 | 0.031 | 0.040 | 0.966 | 0.872 | 1.062 | inconclusive | equivalent |
| urban_pt\|1 | 321 | 199 | 92.413 | 87.245 | 0.023 | 0.027 | 0.944 | 0.861 | 1.039 | inconclusive | equivalent |
| urban_pt\|2+ | 122 | 87 | 90.519 | 110.337 | 0.010 | 0.015 | 1.219 | 1.060 | 1.391 | inconclusive | inconclusive |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 863 | 572 | 45.850 | 50.962 | 0.050 | 0.051 | 1.111 | 0.995 | 1.238 | inconclusive | inconclusive |
| walking_only\|1 | 821 | 553 | 42.361 | 49.274 | 0.069 | 0.066 | 1.163 | 1.042 | 1.264 | inconclusive | inconclusive |
| walking_only\|2+ | 363 | 251 | 41.506 | 40.119 | 0.032 | 0.032 | 0.967 | 0.825 | 1.138 | inconclusive | inconclusive |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.126 | 0.102 | 0.158 | 0.134 | 0.114 | 0.167 | - | 0.000 | 0.343 | - | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| other\|0 | other\|0+1 |
| other\|1 | other\|0+1 |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.043 | 1.090 | 1.066 | 1.114 | 0.457 | 0.002 | 0.054 | 0.044 | 0.077 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.171 | 19.384 |
| 2 | 28.481 | 29.886 |
| 3 | 36.835 | 39.897 |
| 4 | 44.792 | 49.482 |
| 5 | 57.966 | 59.634 |
| 6 | 65.459 | 74.191 |
| 7 | 79.893 | 89.442 |
| 8 | 99.728 | 109.614 |
| 9 | 129.756 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 202 | 119 | 50.395 | 58.855 | 0.020 | 0.021 | 1.168 | 0.954 | 1.419 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q1 | 124 | 183 | 63.618 | 59.257 | 0.026 | 0.037 | 0.931 | 0.738 | 1.129 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q2 | 138 | 113 | 47.684 | 55.539 | 0.025 | 0.022 | 1.165 | 1.013 | 1.347 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q3 | 106 | 80 | 49.220 | 61.814 | 0.015 | 0.015 | 1.256 | 1.018 | 1.552 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q4 | 128 | 90 | 49.752 | 52.945 | 0.018 | 0.017 | 1.064 | 0.844 | 1.285 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q1 | 122 | 60 | 51.034 | 57.758 | 0.016 | 0.013 | 1.132 | 0.756 | 1.552 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q2 | 173 | 74 | 60.814 | 48.318 | 0.018 | 0.014 | 0.795 | 0.639 | 0.973 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q3 | 136 | 85 | 56.663 | 56.335 | 0.015 | 0.015 | 0.994 | 0.815 | 1.218 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q4 | 136 | 73 | 51.569 | 47.307 | 0.016 | 0.012 | 0.917 | 0.755 | 1.093 | inconclusive | inconclusive |
| employed\|dense\|q1 | 88 | 68 | 85.907 | 85.647 | 0.009 | 0.008 | 0.997 | 0.816 | 1.202 | inconclusive | inconclusive |
| employed\|dense\|q2 | 110 | 74 | 81.321 | 87.131 | 0.009 | 0.009 | 1.071 | 0.869 | 1.309 | inconclusive | inconclusive |
| employed\|dense\|q3 | 196 | 88 | 78.073 | 79.100 | 0.015 | 0.009 | 1.013 | 0.892 | 1.139 | inconclusive | equivalent |
| employed\|dense\|q4 | 227 | 125 | 66.350 | 82.961 | 0.016 | 0.016 | 1.250 | 1.101 | 1.413 | different | inconclusive |
| employed\|dense\|q5 | 433 | 198 | 83.539 | 83.104 | 0.022 | 0.026 | 0.995 | 0.914 | 1.093 | equivalent | equivalent |
| employed\|intermediate\|q1 | 208 | 187 | 77.535 | 75.252 | 0.018 | 0.026 | 0.971 | 0.831 | 1.151 | inconclusive | inconclusive |
| employed\|intermediate\|q2 | 393 | 302 | 71.522 | 79.528 | 0.037 | 0.034 | 1.112 | 0.997 | 1.255 | inconclusive | inconclusive |
| employed\|intermediate\|q3 | 542 | 369 | 73.853 | 89.422 | 0.046 | 0.042 | 1.211 | 1.076 | 1.355 | inconclusive | inconclusive |
| employed\|intermediate\|q4 | 725 | 416 | 76.813 | 80.680 | 0.052 | 0.045 | 1.050 | 0.963 | 1.150 | inconclusive | equivalent |
| employed\|intermediate\|q5 | 1070 | 570 | 88.182 | 93.852 | 0.060 | 0.062 | 1.064 | 0.990 | 1.153 | inconclusive | inconclusive |
| employed\|sparse+very_sparse\|q1 | 320 | 135 | 63.117 | 71.169 | 0.024 | 0.019 | 1.128 | 0.980 | 1.283 | inconclusive | inconclusive |
| employed\|sparse\|q2 | 146 | 101 | 56.664 | 69.955 | 0.014 | 0.014 | 1.235 | 1.047 | 1.472 | inconclusive | inconclusive |
| employed\|sparse\|q3 | 183 | 133 | 73.982 | 75.187 | 0.017 | 0.018 | 1.016 | 0.752 | 1.280 | inconclusive | inconclusive |
| employed\|sparse\|q4 | 225 | 172 | 74.173 | 83.820 | 0.023 | 0.022 | 1.130 | 0.917 | 1.365 | inconclusive | inconclusive |
| employed\|sparse\|q5 | 227 | 164 | 72.634 | 82.097 | 0.017 | 0.018 | 1.130 | 0.988 | 1.289 | inconclusive | inconclusive |
| employed\|very_sparse\|q2 | 448 | 199 | 64.559 | 85.144 | 0.028 | 0.022 | 1.319 | 1.152 | 1.515 | different | different |
| employed\|very_sparse\|q3 | 544 | 270 | 67.309 | 82.438 | 0.028 | 0.028 | 1.225 | 1.092 | 1.365 | inconclusive | inconclusive |
| employed\|very_sparse\|q4 | 637 | 264 | 70.970 | 89.703 | 0.034 | 0.023 | 1.264 | 1.144 | 1.378 | different | inconclusive |
| employed\|very_sparse\|q5 | 521 | 240 | 79.733 | 90.548 | 0.021 | 0.021 | 1.136 | 1.010 | 1.296 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 179 | 106 | 66.673 | 84.773 | 0.010 | 0.013 | 1.271 | 1.079 | 1.529 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 147 | 67 | 75.042 | 82.017 | 0.010 | 0.009 | 1.093 | 0.878 | 1.344 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 220 | 55 | 69.713 | 80.414 | 0.011 | 0.008 | 1.153 | 0.858 | 1.505 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate\|q2 | 157 | 133 | 68.326 | 81.686 | 0.013 | 0.014 | 1.196 | 1.014 | 1.421 | inconclusive | inconclusive |
| other_inactive\|dense\|q1 | 164 | 104 | 67.361 | 81.242 | 0.010 | 0.010 | 1.206 | 1.041 | 1.413 | inconclusive | inconclusive |
| other_inactive\|intermediate\|q1 | 212 | 193 | 67.917 | 70.719 | 0.019 | 0.016 | 1.041 | 0.862 | 1.229 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q1 | 162 | 83 | 68.790 | 67.466 | 0.011 | 0.008 | 0.981 | 0.705 | 1.319 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q2 | 116 | 62 | 63.016 | 75.081 | 0.008 | 0.007 | 1.191 | 0.902 | 1.599 | inconclusive | inconclusive |
| retired\|dense+intermediate\|q1 | 295 | 213 | 59.636 | 62.610 | 0.021 | 0.014 | 1.050 | 0.908 | 1.252 | inconclusive | inconclusive |
| retired\|dense\|q2 | 57 | 68 | 75.400 | 78.796 | 0.003 | 0.005 | 1.045 | 0.692 | 1.528 | inconclusive | inconclusive |
| retired\|dense\|q3 | 83 | 70 | 54.832 | 78.732 | 0.004 | 0.006 | 1.436 | 1.104 | 1.923 | different | inconclusive |
| retired\|dense\|q4 | 86 | 90 | 67.583 | 74.621 | 0.005 | 0.007 | 1.104 | 0.789 | 1.562 | inconclusive | inconclusive |
| retired\|dense\|q5 | 174 | 115 | 75.545 | 75.438 | 0.008 | 0.009 | 0.999 | 0.822 | 1.200 | inconclusive | inconclusive |
| retired\|intermediate\|q2 | 221 | 308 | 58.429 | 68.976 | 0.014 | 0.020 | 1.181 | 0.999 | 1.363 | inconclusive | inconclusive |
| retired\|intermediate\|q3 | 316 | 301 | 64.439 | 63.328 | 0.022 | 0.021 | 0.983 | 0.866 | 1.154 | inconclusive | inconclusive |
| retired\|intermediate\|q4 | 260 | 343 | 68.050 | 69.908 | 0.015 | 0.025 | 1.027 | 0.905 | 1.183 | inconclusive | inconclusive |
| retired\|intermediate\|q5 | 515 | 377 | 65.321 | 73.459 | 0.025 | 0.025 | 1.125 | 1.000 | 1.258 | inconclusive | inconclusive |
| retired\|sparse\|q1 | 95 | 79 | 44.915 | 68.596 | 0.007 | 0.006 | 1.527 | 1.170 | 1.928 | different | different |
| retired\|sparse\|q2 | 97 | 162 | 48.928 | 52.934 | 0.008 | 0.015 | 1.082 | 0.884 | 1.478 | inconclusive | inconclusive |
| retired\|sparse\|q3 | 117 | 122 | 53.113 | 63.318 | 0.010 | 0.011 | 1.192 | 0.945 | 1.486 | inconclusive | inconclusive |
| retired\|sparse\|q4 | 101 | 136 | 56.563 | 50.518 | 0.006 | 0.011 | 0.893 | 0.746 | 1.096 | inconclusive | inconclusive |
| retired\|sparse\|q5 | 129 | 117 | 64.713 | 67.727 | 0.009 | 0.009 | 1.047 | 0.817 | 1.293 | inconclusive | inconclusive |
| retired\|very_sparse\|q1 | 311 | 96 | 51.124 | 50.482 | 0.011 | 0.006 | 0.987 | 0.828 | 1.203 | inconclusive | inconclusive |
| retired\|very_sparse\|q2 | 258 | 214 | 61.110 | 55.491 | 0.011 | 0.012 | 0.908 | 0.799 | 1.076 | inconclusive | inconclusive |
| retired\|very_sparse\|q3 | 314 | 204 | 63.903 | 60.981 | 0.014 | 0.012 | 0.954 | 0.845 | 1.106 | inconclusive | inconclusive |
| retired\|very_sparse\|q4 | 177 | 190 | 66.695 | 64.101 | 0.007 | 0.012 | 0.961 | 0.820 | 1.114 | inconclusive | inconclusive |
| retired\|very_sparse\|q5 | 256 | 152 | 73.676 | 76.660 | 0.009 | 0.008 | 1.041 | 0.876 | 1.206 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 124 | 91 | 75.101 | 72.001 | 0.009 | 0.010 | 0.959 | 0.737 | 1.251 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 96 | 68 | 73.266 | 79.889 | 0.006 | 0.007 | 1.090 | 0.845 | 1.347 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 143 | 70 | 74.849 | 78.437 | 0.008 | 0.008 | 1.048 | 0.841 | 1.287 | inconclusive | inconclusive |
| unemployed\|dense+intermediate\|q1 | 154 | 211 | 58.336 | 83.515 | 0.013 | 0.019 | 1.432 | 1.148 | 1.712 | different | inconclusive |
| unemployed\|sparse+very_sparse\|q1 | 97 | 76 | 59.699 | 70.214 | 0.006 | 0.007 | 1.176 | 0.783 | 1.735 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.041 | 0.038 | 0.060 | 0.051 | 0.049 | 0.072 | 0.116 | 0.024 | 0.084 | 0.423 | 0.000 | 0.001 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 67.658 | 1.097 | 1.068 | 1.120 | 0.070 | 0.000 | 0.058 | 0.045 | 0.080 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.134 | 19.383 |
| 2 | 27.713 | 29.886 |
| 3 | 35.268 | 39.897 |
| 4 | 44.556 | 49.480 |
| 5 | 56.123 | 59.633 |
| 6 | 64.917 | 74.189 |
| 7 | 79.842 | 89.438 |
| 8 | 99.645 | 109.613 |
| 9 | 129.623 | 146.234 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: cell levels

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4332 | 2968 | 67.994 | 71.404 | 0.248 | 0.249 | 1.050 | 1.007 | 1.096 | equivalent | equivalent |
| couple_with_children | 5060 | 2737 | 68.306 | 75.744 | 0.487 | 0.443 | 1.109 | 1.073 | 1.142 | inconclusive | equivalent |
| other | 336 | 198 | 66.892 | 76.950 | 0.036 | 0.032 | 1.150 | 1.020 | 1.306 | inconclusive | inconclusive |
| single_parent | 1067 | 767 | 65.348 | 73.621 | 0.084 | 0.110 | 1.127 | 1.025 | 1.216 | inconclusive | inconclusive |
| single_person | 3547 | 2968 | 65.942 | 74.108 | 0.144 | 0.166 | 1.124 | 1.076 | 1.174 | inconclusive | inconclusive |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: stability and explained variance

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.003 | 0.001 | 0.000 | 0.004 | 0.095 | 0.249 | 0.713 | 0.140 | 0.000 | 0.000 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed full-sample merges

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.465 | 1.100 | 1.073 | 1.121 | -0.122 | 0.000 | 0.059 | 0.046 | 0.080 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.135 | 19.384 |
| 2 | 27.640 | 29.886 |
| 3 | 35.016 | 39.897 |
| 4 | 44.601 | 49.482 |
| 5 | 56.480 | 59.634 |
| 6 | 64.858 | 74.191 |
| 7 | 79.734 | 89.442 |
| 8 | 99.495 | 109.614 |
| 9 | 129.543 | 146.206 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person mode use and user-day minutes

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 4224 | 2856 | 0.254 | 0.267 | 37.502 | 39.816 |
| bike | 493 | 291 | 0.032 | 0.030 | 42.547 | 50.730 |
| car_driver | 8409 | 5589 | 0.460 | 0.456 | 61.727 | 67.265 |
| car_passenger | 2054 | 1635 | 0.142 | 0.149 | 40.704 | 45.672 |
| urban_pt | 1402 | 918 | 0.076 | 0.096 | 72.673 | 75.660 |
| train | 563 | 241 | 0.023 | 0.028 | 117.541 | 127.483 |
| other | 622 | 327 | 0.049 | 0.035 | 59.259 | 64.155 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode model

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 56.243 | 62.640 | 57.780 | 1.536 | 0.357 | 2.899 | 4.861 | 3.313 | 6.323 | 0.036 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode deciles

Scope: Round-trip days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 0.000 | 0.000 |
| 2 | 9.904 | 11.054 |
| 3 | 24.325 | 24.972 |
| 4 | 34.737 | 39.863 |
| 5 | 45.393 | 49.675 |
| 6 | 59.552 | 61.659 |
| 7 | 74.501 | 79.690 |
| 8 | 94.206 | 99.891 |
| 9 | 124.182 | 134.889 |

n: 2008 14342, 2019 9638 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

## Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`)

### Grouping summary

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | 0.029 | 0.039 | - | - | - | - | - | - | 6 |
| category | 0.028 | 0.033 | - | - | - | - | - | - | 5 |
| category_x_density_x_income | 0.046 | 0.048 | - | - | - | - | - | - | 60 |
| day_mode_group | 0.128 | 0.102 | - | - | - | - | - | - | 9 |
| day_mode_group_x_category | 0.159 | 0.141 | - | - | - | - | - | - | 45 |
| day_mode_group_x_density | 0.132 | 0.106 | - | - | - | - | - | - | 26 |
| day_mode_group_x_income | 0.139 | 0.112 | - | - | - | - | - | - | 35 |
| day_mode_group_x_vehicles | 0.129 | 0.114 | - | - | - | - | - | - | 32 |
| day_purpose | 0.012 | 0.008 | - | - | - | - | - | - | 3 |
| density | 0.003 | 0.004 | - | - | - | - | - | - | 4 |
| household_type | 0.001 | 0.001 | - | - | - | - | - | - | 5 |
| income | 0.011 | 0.008 | - | - | - | - | - | - | 5 |
| none | 0.000 | 0.000 | - | - | - | - | - | - | 1 |
| vehicles | 0.000 | 0.003 | - | - | - | - | - | - | 4 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 14485 | 9722 | 70.790 | 77.245 | 1.000 | 1.000 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1268 | 881 | 54.743 | 57.743 | 0.167 | 0.164 | - | - | - |  |  |
| employed | 7344 | 4123 | 79.690 | 87.999 | 0.492 | 0.465 | - | - | - |  |  |
| other_inactive | 1363 | 808 | 69.376 | 79.293 | 0.092 | 0.085 | - | - | - |  |  |
| retired | 3892 | 3381 | 63.781 | 68.232 | 0.208 | 0.234 | - | - | - |  |  |
| unemployed | 617 | 519 | 68.267 | 79.923 | 0.041 | 0.051 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.028 | 0.021 | 0.037 | 0.033 | 0.025 | 0.044 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.241 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1008 | 673 | 49.378 | 49.945 | 0.127 | 0.127 | - | - | - |  |  |
| 15 | 2049 | 1182 | 76.043 | 82.984 | 0.208 | 0.170 | - | - | - |  |  |
| 30 | 2154 | 1102 | 78.704 | 87.786 | 0.166 | 0.139 | - | - | - |  |  |
| 40 | 2405 | 1251 | 79.204 | 88.793 | 0.158 | 0.157 | - | - | - |  |  |
| 50 | 2847 | 1656 | 74.473 | 85.874 | 0.135 | 0.139 | - | - | - |  |  |
| 60 | 4022 | 3858 | 63.436 | 69.814 | 0.206 | 0.267 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.029 | 0.022 | 0.039 | 0.039 | 0.031 | 0.051 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2061 | 1334 | 73.190 | 82.133 | 0.142 | 0.149 | - | - | - |  |  |
| intermediate | 5859 | 4472 | 73.201 | 78.324 | 0.442 | 0.458 | - | - | - |  |  |
| sparse | 1862 | 1576 | 65.538 | 69.811 | 0.174 | 0.187 | - | - | - |  |  |
| very_sparse | 4703 | 2340 | 68.767 | 78.056 | 0.242 | 0.206 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.003 | 0.001 | 0.007 | 0.004 | 0.001 | 0.008 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2358 | 1704 | 64.703 | 71.035 | 0.188 | 0.190 | - | - | - |  |  |
| q2 | 2450 | 1910 | 65.802 | 71.446 | 0.197 | 0.197 | - | - | - |  |  |
| q3 | 2836 | 1919 | 69.559 | 81.574 | 0.200 | 0.197 | - | - | - |  |  |
| q4 | 2960 | 2027 | 71.589 | 75.514 | 0.207 | 0.204 | - | - | - |  |  |
| q5 | 3881 | 2162 | 81.487 | 85.853 | 0.207 | 0.212 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.011 | 0.007 | 0.018 | 0.008 | 0.005 | 0.013 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2126 | 1469 | 70.985 | 79.558 | 0.118 | 0.128 | - | - | - |  |  |
| 1 | 5569 | 4057 | 70.688 | 73.672 | 0.388 | 0.392 | - | - | - |  |  |
| 2+ | 6790 | 4172 | 70.823 | 79.305 | 0.494 | 0.478 | - | - | - |  |  |
| unknown | 0 | 24 | - | - | - | - | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.002 | 0.003 | 0.001 | 0.013 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7271 | 5663 | 63.822 | 71.197 | 0.456 | 0.475 | - | - | - |  |  |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7214 | 4058 | 76.637 | 82.710 | 0.544 | 0.525 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.012 | 0.008 | 0.018 | 0.008 | 0.004 | 0.013 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 7717 | 5161 | 69.709 | 77.348 | 0.501 | 0.491 | - | - | - |  |  |
| car_passenger_carpool | 373 | 368 | 59.489 | 66.439 | 0.024 | 0.024 | - | - | - |  |  |
| car_passenger_household | 885 | 790 | 52.918 | 58.902 | 0.080 | 0.092 | - | - | - |  |  |
| cycle | 296 | 173 | 54.092 | 72.612 | 0.024 | 0.021 | - | - | - |  |  |
| multimodal | 1318 | 792 | 106.364 | 108.545 | 0.100 | 0.096 | - | - | - |  |  |
| other | 417 | 203 | 68.427 | 80.644 | 0.038 | 0.025 | - | - | - |  |  |
| train | 397 | 161 | 142.818 | 157.093 | 0.021 | 0.021 | - | - | - |  |  |
| urban_pt | 1046 | 698 | 97.699 | 96.555 | 0.064 | 0.083 | - | - | - |  |  |
| walking_only | 2036 | 1376 | 43.580 | 47.902 | 0.149 | 0.148 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.128 | 0.102 | 0.153 | 0.102 | 0.086 | 0.124 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 540 | 380 | 73.933 | 89.549 | 0.041 | 0.040 | - | - | - |  |  |
| car_driver\|intermediate | 2865 | 2213 | 70.921 | 76.958 | 0.209 | 0.211 | - | - | - |  |  |
| car_driver\|sparse | 1146 | 952 | 67.415 | 71.848 | 0.097 | 0.106 | - | - | - |  |  |
| car_driver\|very_sparse | 3166 | 1616 | 68.390 | 78.662 | 0.154 | 0.134 | - | - | - |  |  |
| car_passenger_carpool\|dense+intermediate | 200 | 228 | 62.338 | 67.009 | 0.013 | 0.013 | - | - | - |  |  |
| car_passenger_carpool\|sparse | 54 | 63 | 58.968 | 64.039 | 0.006 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|very_sparse | 119 | 77 | 52.169 | 67.854 | 0.005 | 0.004 | - | - | - |  |  |
| car_passenger_household\|dense | 69 | 59 | 53.919 | 70.173 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|intermediate | 319 | 367 | 52.452 | 59.923 | 0.034 | 0.043 | - | - | - |  |  |
| car_passenger_household\|sparse | 130 | 161 | 47.054 | 56.073 | 0.015 | 0.020 | - | - | - |  |  |
| car_passenger_household\|very_sparse | 367 | 203 | 57.035 | 55.518 | 0.024 | 0.021 | - | - | - |  |  |
| cycle\|dense+intermediate | 164 | 121 | 54.791 | 71.756 | 0.015 | 0.015 | - | - | - |  |  |
| cycle\|sparse+very_sparse | 132 | 52 | 52.935 | 74.585 | 0.009 | 0.006 | - | - | - |  |  |
| multimodal\|dense | 200 | 117 | 123.976 | 113.302 | 0.013 | 0.013 | - | - | - |  |  |
| multimodal\|intermediate | 564 | 375 | 109.414 | 110.183 | 0.046 | 0.048 | - | - | - |  |  |
| multimodal\|sparse | 139 | 105 | 92.954 | 102.437 | 0.015 | 0.014 | - | - | - |  |  |
| multimodal\|very_sparse | 415 | 195 | 99.713 | 105.936 | 0.025 | 0.020 | - | - | - |  |  |
| other\|dense+intermediate | 180 | 116 | 65.381 | 77.065 | 0.017 | 0.013 | - | - | - |  |  |
| other\|sparse+very_sparse | 237 | 87 | 70.824 | 84.869 | 0.021 | 0.011 | - | - | - |  |  |
| train\|dense+intermediate+sparse+very_sparse | 397 | 161 | 142.818 | 157.093 | 0.021 | 0.021 | - | - | - |  |  |
| urban_pt\|dense | 548 | 299 | 92.197 | 93.297 | 0.028 | 0.036 | - | - | - |  |  |
| urban_pt\|intermediate+sparse+very_sparse | 498 | 399 | 102.082 | 99.038 | 0.035 | 0.047 | - | - | - |  |  |
| walking_only\|dense | 500 | 342 | 44.111 | 54.665 | 0.038 | 0.039 | - | - | - |  |  |
| walking_only\|intermediate | 954 | 701 | 43.390 | 47.053 | 0.072 | 0.072 | - | - | - |  |  |
| walking_only\|sparse | 249 | 196 | 44.365 | 43.123 | 0.024 | 0.025 | - | - | - |  |  |
| walking_only\|very_sparse | 333 | 137 | 41.816 | 41.221 | 0.015 | 0.013 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.132 | 0.108 | 0.161 | 0.106 | 0.095 | 0.130 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate |
| cycle\|intermediate | cycle\|dense+intermediate |
| cycle\|sparse | cycle\|sparse+very_sparse |
| cycle\|very_sparse | cycle\|sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|intermediate | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|intermediate+sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|intermediate+sparse+very_sparse |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 58 | 35 | 59.548 | - | 0.008 | - | - | - | - |  |  |
| car_driver\|employed | 4829 | 2810 | 74.120 | 83.645 | 0.331 | 0.312 | - | - | - |  |  |
| car_driver\|other_inactive | 545 | 264 | 60.608 | 68.984 | 0.034 | 0.025 | - | - | - |  |  |
| car_driver\|retired | 1993 | 1808 | 60.744 | 64.491 | 0.111 | 0.124 | - | - | - |  |  |
| car_driver\|unemployed | 292 | 240 | 65.718 | 70.642 | 0.018 | 0.023 | - | - | - |  |  |
| car_passenger_carpool\|children_6_17 | 18 | 19 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 105 | 59 | 57.134 | 82.370 | 0.009 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|other_inactive | 57 | 50 | 61.753 | 64.510 | 0.003 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|retired | 168 | 213 | 63.930 | 69.324 | 0.008 | 0.010 | - | - | - |  |  |
| car_passenger_carpool\|unemployed | 24 | 25 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 373 | 293 | 41.601 | 47.633 | 0.047 | 0.052 | - | - | - |  |  |
| car_passenger_household\|employed | 144 | 84 | 64.814 | 73.918 | 0.010 | 0.008 | - | - | - |  |  |
| car_passenger_household\|other_inactive | 108 | 80 | 78.485 | 79.145 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|retired | 236 | 309 | 68.528 | 70.414 | 0.015 | 0.022 | - | - | - |  |  |
| car_passenger_household\|unemployed | 24 | 24 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 50 | 20 | 39.391 | - | 0.008 | - | - | - | - |  |  |
| cycle\|employed | 118 | 76 | 63.001 | 62.865 | 0.008 | 0.010 | - | - | - |  |  |
| cycle\|other_inactive | 25 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 91 | 50 | 60.324 | 79.495 | 0.005 | 0.004 | - | - | - |  |  |
| cycle\|unemployed | 12 | 12 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 242 | 146 | 72.427 | 73.899 | 0.029 | 0.024 | - | - | - |  |  |
| multimodal\|employed | 668 | 380 | 124.067 | 124.947 | 0.048 | 0.046 | - | - | - |  |  |
| multimodal\|other_inactive | 113 | 62 | 103.623 | 119.883 | 0.008 | 0.009 | - | - | - |  |  |
| multimodal\|retired | 238 | 163 | 122.947 | 109.930 | 0.010 | 0.012 | - | - | - |  |  |
| multimodal\|unemployed | 57 | 41 | 107.344 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 173 | 48 | 69.081 | - | 0.019 | - | - | - | - |  |  |
| other\|employed | 167 | 81 | 70.724 | 86.915 | 0.013 | 0.012 | - | - | - |  |  |
| other\|other_inactive | 25 | 22 | - | - | - | - | - | - | - |  |  |
| other\|retired | 47 | 47 | - | - | - | - | - | - | - |  |  |
| other\|unemployed | 5 | 5 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 13 | - | - | - | - | - | - | - |  |  |
| train\|employed | 298 | 110 | 152.168 | 167.351 | 0.015 | 0.013 | - | - | - |  |  |
| train\|other_inactive | 36 | 16 | - | - | - | - | - | - | - |  |  |
| train\|retired | 34 | 16 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 5 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 89 | 115 | 98.212 | 88.053 | 0.012 | 0.021 | - | - | - |  |  |
| urban_pt\|employed | 511 | 249 | 95.864 | 100.266 | 0.027 | 0.029 | - | - | - |  |  |
| urban_pt\|other_inactive | 176 | 119 | 95.355 | 98.271 | 0.012 | 0.015 | - | - | - |  |  |
| urban_pt\|retired | 218 | 150 | 99.733 | 97.880 | 0.009 | 0.011 | - | - | - |  |  |
| urban_pt\|unemployed | 52 | 63 | 117.318 | 102.036 | 0.003 | 0.006 | - | - | - |  |  |
| walking_only\|children_6_17 | 246 | 192 | 37.445 | 34.763 | 0.038 | 0.041 | - | - | - |  |  |
| walking_only\|employed | 504 | 274 | 43.805 | 47.129 | 0.033 | 0.031 | - | - | - |  |  |
| walking_only\|other_inactive | 278 | 180 | 43.965 | 55.673 | 0.019 | 0.017 | - | - | - |  |  |
| walking_only\|retired | 867 | 625 | 48.198 | 54.768 | 0.046 | 0.049 | - | - | - |  |  |
| walking_only\|unemployed | 141 | 104 | 44.029 | 58.350 | 0.012 | 0.009 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.159 | 0.135 | 0.191 | 0.141 | 0.126 | 0.173 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.241 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 904 | 586 | 59.642 | 70.448 | 0.065 | 0.059 | - | - | - |  |  |
| car_driver\|q2 | 1225 | 965 | 63.813 | 67.165 | 0.090 | 0.094 | - | - | - |  |  |
| car_driver\|q3 | 1613 | 1102 | 67.522 | 79.011 | 0.110 | 0.106 | - | - | - |  |  |
| car_driver\|q4 | 1712 | 1220 | 71.829 | 78.580 | 0.112 | 0.115 | - | - | - |  |  |
| car_driver\|q5 | 2263 | 1288 | 79.398 | 86.203 | 0.123 | 0.118 | - | - | - |  |  |
| car_passenger_carpool\|q1 | 104 | 110 | 56.802 | 63.754 | 0.006 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|q2 | 84 | 98 | 50.546 | 55.521 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q3 | 73 | 70 | 62.013 | 69.557 | 0.005 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|q4+q5 | 112 | 90 | 67.382 | 76.356 | 0.007 | 0.007 | - | - | - |  |  |
| car_passenger_household\|q1 | 136 | 130 | 60.364 | 52.984 | 0.013 | 0.018 | - | - | - |  |  |
| car_passenger_household\|q2 | 177 | 178 | 45.439 | 62.431 | 0.018 | 0.021 | - | - | - |  |  |
| car_passenger_household\|q3 | 194 | 162 | 56.034 | 63.592 | 0.017 | 0.019 | - | - | - |  |  |
| car_passenger_household\|q4 | 180 | 174 | 46.496 | 53.619 | 0.019 | 0.020 | - | - | - |  |  |
| car_passenger_household\|q5 | 198 | 146 | 61.458 | 62.442 | 0.013 | 0.014 | - | - | - |  |  |
| cycle\|q1+q2 | 121 | 73 | 54.482 | 82.039 | 0.010 | 0.009 | - | - | - |  |  |
| cycle\|q3+q4+q5 | 175 | 100 | 53.810 | 65.107 | 0.014 | 0.012 | - | - | - |  |  |
| multimodal\|q1 | 184 | 114 | 92.642 | 114.832 | 0.016 | 0.015 | - | - | - |  |  |
| multimodal\|q2 | 225 | 140 | 101.686 | 97.497 | 0.022 | 0.017 | - | - | - |  |  |
| multimodal\|q3 | 239 | 159 | 113.697 | 105.057 | 0.020 | 0.021 | - | - | - |  |  |
| multimodal\|q4 | 265 | 172 | 104.379 | 104.895 | 0.021 | 0.020 | - | - | - |  |  |
| multimodal\|q5 | 405 | 207 | 116.766 | 119.026 | 0.021 | 0.023 | - | - | - |  |  |
| other\|q1+q2 | 172 | 94 | 69.570 | 72.464 | 0.018 | 0.011 | - | - | - |  |  |
| other\|q3+q4+q5 | 245 | 109 | 67.394 | 86.942 | 0.020 | 0.014 | - | - | - |  |  |
| train\|q1+q2+q3+q4 | 224 | 106 | 143.936 | 167.730 | 0.013 | 0.015 | - | - | - |  |  |
| train\|q5 | 173 | 55 | 140.841 | 131.636 | 0.008 | 0.006 | - | - | - |  |  |
| urban_pt\|q1 | 240 | 240 | 107.246 | 94.414 | 0.019 | 0.028 | - | - | - |  |  |
| urban_pt\|q2 | 172 | 129 | 98.115 | 96.989 | 0.013 | 0.015 | - | - | - |  |  |
| urban_pt\|q3 | 173 | 106 | 93.653 | 102.916 | 0.009 | 0.014 | - | - | - |  |  |
| urban_pt\|q4 | 195 | 93 | 86.166 | 94.347 | 0.013 | 0.010 | - | - | - |  |  |
| urban_pt\|q5 | 266 | 130 | 97.611 | 95.890 | 0.010 | 0.016 | - | - | - |  |  |
| walking_only\|q1 | 611 | 426 | 45.834 | 48.141 | 0.052 | 0.049 | - | - | - |  |  |
| walking_only\|q2 | 372 | 281 | 40.422 | 49.952 | 0.031 | 0.030 | - | - | - |  |  |
| walking_only\|q3 | 366 | 216 | 43.849 | 51.029 | 0.024 | 0.021 | - | - | - |  |  |
| walking_only\|q4 | 326 | 230 | 42.373 | 42.080 | 0.022 | 0.024 | - | - | - |  |  |
| walking_only\|q5 | 361 | 223 | 43.636 | 48.017 | 0.019 | 0.023 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.139 | 0.115 | 0.167 | 0.112 | 0.099 | 0.142 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2 |
| cycle\|q2 | cycle\|q1+q2 |
| cycle\|q3 | cycle\|q3+q4+q5 |
| cycle\|q4 | cycle\|q3+q4+q5 |
| cycle\|q5 | cycle\|q3+q4+q5 |
| other\|q1 | other\|q1+q2 |
| other\|q2 | other\|q1+q2 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3105 | 2396 | 69.234 | 73.782 | 0.193 | 0.195 | - | - | - |  |  |
| car_driver\|2+ | 4612 | 2758 | 70.007 | 79.728 | 0.308 | 0.295 | - | - | - |  |  |
| car_driver\|unknown | 0 | 7 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 167 | 191 | 52.763 | 61.715 | 0.009 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|1 | 131 | 122 | 71.303 | 74.871 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|2+ | 75 | 54 | 56.384 | 62.767 | 0.008 | 0.007 | - | - | - |  |  |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 365 | 363 | 56.802 | 57.711 | 0.033 | 0.043 | - | - | - |  |  |
| car_passenger_household\|2+ | 520 | 425 | 50.115 | 60.046 | 0.046 | 0.049 | - | - | - |  |  |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0 | 88 | 53 | 51.312 | 74.922 | 0.006 | 0.007 | - | - | - |  |  |
| cycle\|1 | 118 | 68 | 56.884 | 65.321 | 0.009 | 0.008 | - | - | - |  |  |
| cycle\|2+ | 90 | 50 | 53.186 | 80.395 | 0.009 | 0.006 | - | - | - |  |  |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 137 | 81 | 115.813 | 138.948 | 0.008 | 0.008 | - | - | - |  |  |
| multimodal\|1 | 462 | 279 | 110.826 | 111.760 | 0.036 | 0.032 | - | - | - |  |  |
| multimodal\|2+ | 719 | 430 | 102.203 | 102.579 | 0.056 | 0.056 | - | - | - |  |  |
| multimodal\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| other\|0 | 71 | 50 | 60.917 | 81.662 | 0.005 | 0.003 | - | - | - |  |  |
| other\|1 | 149 | 80 | 68.965 | 78.301 | 0.014 | 0.011 | - | - | - |  |  |
| other\|2+ | 197 | 73 | 70.063 | 82.866 | 0.019 | 0.010 | - | - | - |  |  |
| train\|0 | 128 | 52 | 138.325 | 177.296 | 0.005 | 0.005 | - | - | - |  |  |
| train\|1+2+ | 269 | 107 | 144.145 | 143.862 | 0.016 | 0.015 | - | - | - |  |  |
| train\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 601 | 404 | 99.836 | 96.120 | 0.030 | 0.040 | - | - | - |  |  |
| urban_pt\|1 | 322 | 201 | 96.499 | 88.656 | 0.023 | 0.027 | - | - | - |  |  |
| urban_pt\|2+ | 123 | 88 | 93.911 | 111.210 | 0.010 | 0.015 | - | - | - |  |  |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 861 | 572 | 45.835 | 50.962 | 0.050 | 0.051 | - | - | - |  |  |
| walking_only\|1 | 814 | 551 | 42.779 | 49.303 | 0.067 | 0.065 | - | - | - |  |  |
| walking_only\|2+ | 361 | 250 | 41.748 | 40.054 | 0.032 | 0.032 | - | - | - |  |  |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.129 | 0.104 | 0.158 | 0.114 | 0.097 | 0.143 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 203 | 120 | 50.751 | 60.126 | 0.020 | 0.021 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q1 | 124 | 183 | 63.618 | 59.257 | 0.025 | 0.037 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q2 | 138 | 113 | 47.910 | 55.539 | 0.024 | 0.022 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q3 | 106 | 80 | 49.220 | 70.575 | 0.015 | 0.015 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q4 | 128 | 91 | 49.869 | 54.305 | 0.018 | 0.017 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q1 | 122 | 60 | 56.273 | 57.758 | 0.016 | 0.012 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q2 | 174 | 74 | 61.798 | 48.318 | 0.018 | 0.014 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q3 | 137 | 86 | 57.365 | 62.391 | 0.015 | 0.015 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q4 | 136 | 74 | 55.062 | 47.597 | 0.016 | 0.012 | - | - | - |  |  |
| employed\|dense\|q1 | 88 | 68 | 85.907 | 92.951 | 0.008 | 0.008 | - | - | - |  |  |
| employed\|dense\|q2 | 110 | 74 | 81.490 | 87.131 | 0.009 | 0.009 | - | - | - |  |  |
| employed\|dense\|q3 | 198 | 90 | 79.782 | 114.169 | 0.015 | 0.010 | - | - | - |  |  |
| employed\|dense\|q4 | 232 | 126 | 69.493 | 83.226 | 0.016 | 0.016 | - | - | - |  |  |
| employed\|dense\|q5 | 444 | 200 | 93.831 | 86.027 | 0.022 | 0.026 | - | - | - |  |  |
| employed\|intermediate\|q1 | 210 | 189 | 77.796 | 77.132 | 0.018 | 0.026 | - | - | - |  |  |
| employed\|intermediate\|q2 | 395 | 302 | 77.784 | 81.385 | 0.038 | 0.034 | - | - | - |  |  |
| employed\|intermediate\|q3 | 546 | 374 | 77.008 | 93.406 | 0.046 | 0.042 | - | - | - |  |  |
| employed\|intermediate\|q4 | 735 | 421 | 82.965 | 83.660 | 0.052 | 0.045 | - | - | - |  |  |
| employed\|intermediate\|q5 | 1080 | 579 | 95.406 | 96.535 | 0.060 | 0.063 | - | - | - |  |  |
| employed\|sparse+very_sparse\|q1 | 320 | 137 | 66.809 | 74.536 | 0.024 | 0.019 | - | - | - |  |  |
| employed\|sparse\|q2 | 147 | 101 | 57.636 | 69.955 | 0.014 | 0.014 | - | - | - |  |  |
| employed\|sparse\|q3 | 186 | 133 | 86.797 | 75.187 | 0.017 | 0.018 | - | - | - |  |  |
| employed\|sparse\|q4 | 229 | 174 | 75.819 | 86.589 | 0.023 | 0.022 | - | - | - |  |  |
| employed\|sparse\|q5 | 240 | 165 | 85.065 | 88.035 | 0.018 | 0.018 | - | - | - |  |  |
| employed\|very_sparse\|q2 | 450 | 199 | 69.834 | 86.930 | 0.028 | 0.022 | - | - | - |  |  |
| employed\|very_sparse\|q3 | 550 | 275 | 69.896 | 91.292 | 0.028 | 0.029 | - | - | - |  |  |
| employed\|very_sparse\|q4 | 649 | 266 | 74.674 | 92.333 | 0.034 | 0.023 | - | - | - |  |  |
| employed\|very_sparse\|q5 | 535 | 250 | 84.168 | 105.488 | 0.022 | 0.022 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 180 | 107 | 66.792 | 88.317 | 0.010 | 0.013 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 148 | 67 | 76.809 | 82.017 | 0.010 | 0.009 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 221 | 55 | 70.910 | 80.414 | 0.011 | 0.008 | - | - | - |  |  |
| other_inactive\|dense+intermediate\|q2 | 158 | 134 | 69.475 | 82.896 | 0.013 | 0.013 | - | - | - |  |  |
| other_inactive\|dense\|q1 | 164 | 105 | 67.462 | 82.571 | 0.010 | 0.010 | - | - | - |  |  |
| other_inactive\|intermediate\|q1 | 213 | 194 | 69.064 | 72.388 | 0.019 | 0.016 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q1 | 163 | 83 | 68.926 | 67.466 | 0.011 | 0.008 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q2 | 116 | 63 | 65.136 | 76.430 | 0.008 | 0.007 | - | - | - |  |  |
| retired\|dense+intermediate\|q1 | 296 | 215 | 60.755 | 68.642 | 0.021 | 0.014 | - | - | - |  |  |
| retired\|dense\|q2 | 57 | 68 | 75.400 | 78.796 | 0.003 | 0.005 | - | - | - |  |  |
| retired\|dense\|q3 | 84 | 71 | 68.822 | 87.534 | 0.004 | 0.006 | - | - | - |  |  |
| retired\|dense\|q4 | 86 | 90 | 67.583 | 74.621 | 0.005 | 0.007 | - | - | - |  |  |
| retired\|dense\|q5 | 174 | 116 | 75.545 | 76.044 | 0.008 | 0.009 | - | - | - |  |  |
| retired\|intermediate\|q2 | 224 | 311 | 61.467 | 73.212 | 0.015 | 0.020 | - | - | - |  |  |
| retired\|intermediate\|q3 | 317 | 304 | 64.477 | 65.969 | 0.022 | 0.021 | - | - | - |  |  |
| retired\|intermediate\|q4 | 264 | 343 | 70.751 | 69.908 | 0.015 | 0.024 | - | - | - |  |  |
| retired\|intermediate\|q5 | 521 | 378 | 69.922 | 74.248 | 0.025 | 0.024 | - | - | - |  |  |
| retired\|sparse\|q1 | 95 | 81 | 44.915 | 70.500 | 0.007 | 0.006 | - | - | - |  |  |
| retired\|sparse\|q2 | 97 | 162 | 48.928 | 52.934 | 0.008 | 0.015 | - | - | - |  |  |
| retired\|sparse\|q3 | 119 | 126 | 54.118 | 74.067 | 0.010 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q4 | 101 | 136 | 56.563 | 53.272 | 0.006 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q5 | 131 | 118 | 65.334 | 74.266 | 0.009 | 0.009 | - | - | - |  |  |
| retired\|very_sparse\|q1 | 312 | 97 | 52.720 | 51.872 | 0.011 | 0.006 | - | - | - |  |  |
| retired\|very_sparse\|q2 | 259 | 216 | 61.588 | 58.200 | 0.011 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q3 | 316 | 205 | 65.863 | 61.797 | 0.014 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q4 | 179 | 190 | 67.479 | 64.390 | 0.007 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q5 | 260 | 154 | 77.695 | 76.649 | 0.009 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 125 | 92 | 74.987 | 76.662 | 0.009 | 0.010 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 97 | 68 | 75.231 | 79.889 | 0.006 | 0.007 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 144 | 71 | 76.959 | 83.955 | 0.008 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate\|q1 | 154 | 212 | 58.917 | 83.727 | 0.013 | 0.019 | - | - | - |  |  |
| unemployed\|sparse+very_sparse\|q1 | 97 | 76 | 59.699 | 70.214 | 0.006 | 0.007 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.046 | 0.044 | 0.065 | 0.048 | 0.047 | 0.074 | - | - | - | - | 0.000 | 0.001 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.241 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: cell levels

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4371 | 2998 | 70.622 | 74.441 | 0.248 | 0.250 | - | - | - |  |  |
| couple_with_children | 5111 | 2755 | 72.230 | 78.783 | 0.487 | 0.442 | - | - | - |  |  |
| other | 338 | 200 | 67.854 | 80.210 | 0.036 | 0.032 | - | - | - |  |  |
| single_parent | 1077 | 771 | 68.036 | 75.450 | 0.084 | 0.110 | - | - | - |  |  |
| single_person | 3588 | 2998 | 68.560 | 77.974 | 0.145 | 0.167 | - | - | - |  |  |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: stability and explained variance

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.004 | 0.001 | 0.000 | 0.003 | - | - | - | - | 0.000 | 0.000 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed full-sample merges

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 77.245 | - | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person mode use and user-day minutes

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 4237 | 2865 | 0.255 | 0.267 | 37.551 | 39.907 |
| bike | 497 | 292 | 0.032 | 0.030 | 42.878 | 51.011 |
| car_driver | 8507 | 5637 | 0.466 | 0.460 | 64.577 | 70.918 |
| car_passenger | 2100 | 1661 | 0.145 | 0.151 | 42.895 | 47.698 |
| urban_pt | 1415 | 923 | 0.077 | 0.096 | 74.586 | 76.062 |
| train | 594 | 258 | 0.026 | 0.029 | 133.001 | 134.677 |
| other | 632 | 336 | 0.050 | 0.035 | 60.878 | 69.354 |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode model

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 59.502 | 65.716 | - | - | - | - | - | - | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode deciles

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 14485, 2019 9722 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

## All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`)

### Grouping summary

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| day_mode_group_x_income | 0.150 | 0.168 | 0.081 | 0.000 | 1.061 | 1.039 | 1.082 | 0.043 | 35 |
| day_mode_group_x_vehicles | 0.144 | 0.177 | - | 0.278 | 1.063 | 1.041 | 1.085 | 0.044 | 30 |
| day_mode_group | 0.141 | 0.159 | 0.063 | 0.309 | 1.064 | 1.041 | 1.086 | 0.045 | 9 |
| day_mode_group_x_density | 0.145 | 0.165 | 0.073 | 0.033 | 1.064 | 1.040 | 1.085 | 0.045 | 26 |
| day_mode_group_x_category | 0.171 | 0.197 | 0.083 | 0.000 | 1.065 | 1.044 | 1.087 | 0.047 | 45 |
| income | 0.006 | 0.006 | 0.072 | 0.000 | 1.074 | 1.049 | 1.095 | 0.050 | 5 |
| vehicles | 0.001 | 0.006 | - | 0.389 | 1.074 | 1.049 | 1.096 | 0.050 | 4 |
| density | 0.003 | 0.007 | 0.071 | 0.000 | 1.074 | 1.050 | 1.097 | 0.050 | 4 |
| none | 0.000 | 0.000 | 0.072 | 1.000 | 1.075 | 1.049 | 1.096 | 0.051 | 1 |
| household_type | 0.001 | 0.002 | 0.073 | 0.242 | 1.076 | 1.052 | 1.098 | 0.050 | 5 |
| category_x_density_x_income | 0.048 | 0.057 | 0.100 | 0.000 | 1.079 | 1.053 | 1.102 | 0.053 | 60 |
| day_purpose | 0.020 | 0.014 | - | 0.544 | 1.079 | 1.055 | 1.102 | 0.053 | 3 |
| category | 0.033 | 0.041 | 0.079 | 0.000 | 1.084 | 1.059 | 1.107 | 0.056 | 5 |
| age_band | 0.041 | 0.050 | 0.088 | 0.000 | 1.093 | 1.068 | 1.115 | 0.061 | 6 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 14795 | 9835 | 64.224 | 69.011 | 1.000 | 1.000 | 1.075 | 1.049 | 1.096 | equivalent | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.072 | 1.000 | 1.000 | 0.072 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.224 | 1.075 | 1.049 | 1.096 | 0.000 | 0.000 | 0.051 | 0.038 | 0.069 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.729 | 19.158 |
| 2 | 24.716 | 29.835 |
| 3 | 34.109 | 34.930 |
| 4 | 41.719 | 44.811 |
| 5 | 54.184 | 59.118 |
| 6 | 61.997 | 69.262 |
| 7 | 77.095 | 84.366 |
| 8 | 94.476 | 104.190 |
| 9 | 124.200 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1307 | 925 | 50.608 | 53.509 | 0.169 | 0.170 | 1.057 | 0.978 | 1.124 | inconclusive | equivalent |
| employed | 7686 | 4233 | 72.109 | 77.880 | 0.502 | 0.468 | 1.080 | 1.054 | 1.110 | inconclusive | equivalent |
| other_inactive | 1419 | 818 | 66.700 | 75.251 | 0.094 | 0.086 | 1.128 | 1.044 | 1.222 | inconclusive | inconclusive |
| retired | 3758 | 3318 | 54.582 | 58.487 | 0.195 | 0.224 | 1.072 | 1.026 | 1.113 | inconclusive | equivalent |
| unemployed | 624 | 531 | 64.195 | 74.540 | 0.039 | 0.052 | 1.161 | 1.029 | 1.288 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.033 | 0.025 | 0.041 | 0.041 | 0.032 | 0.052 | 0.079 | 0.000 | 0.864 | 0.149 | 0.000 | 0.001 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.003 | 63.660 | 1.084 | 1.059 | 1.107 | -0.564 | 0.000 | 0.056 | 0.041 | 0.073 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.213 | 19.157 |
| 2 | 24.570 | 29.834 |
| 3 | 33.250 | 34.924 |
| 4 | 39.986 | 44.808 |
| 5 | 53.758 | 59.117 |
| 6 | 60.287 | 69.260 |
| 7 | 74.979 | 84.361 |
| 8 | 94.169 | 104.187 |
| 9 | 123.256 | 134.646 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1033 | 691 | 44.155 | 46.423 | 0.128 | 0.128 | 1.051 | 0.965 | 1.129 | inconclusive | equivalent |
| 15 | 2230 | 1267 | 71.785 | 78.503 | 0.218 | 0.183 | 1.094 | 1.039 | 1.150 | inconclusive | equivalent |
| 30 | 2247 | 1139 | 72.128 | 78.335 | 0.169 | 0.140 | 1.086 | 1.029 | 1.131 | inconclusive | equivalent |
| 40 | 2504 | 1282 | 70.766 | 77.666 | 0.159 | 0.157 | 1.098 | 1.048 | 1.151 | inconclusive | inconclusive |
| 50 | 2890 | 1666 | 67.403 | 74.318 | 0.133 | 0.138 | 1.103 | 1.047 | 1.168 | inconclusive | inconclusive |
| 60 | 3891 | 3790 | 54.449 | 60.238 | 0.193 | 0.255 | 1.106 | 1.057 | 1.150 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.041 | 0.030 | 0.051 | 0.050 | 0.041 | 0.062 | 0.088 | 0.000 | 0.482 | 0.101 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 63.114 | 1.093 | 1.068 | 1.115 | -1.109 | 0.000 | 0.061 | 0.047 | 0.078 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 17.261 | 19.158 |
| 2 | 24.345 | 29.835 |
| 3 | 30.592 | 34.930 |
| 4 | 39.858 | 44.811 |
| 5 | 51.757 | 59.118 |
| 6 | 59.983 | 69.262 |
| 7 | 74.763 | 84.366 |
| 8 | 92.887 | 104.190 |
| 9 | 122.247 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2133 | 1360 | 67.811 | 73.146 | 0.142 | 0.148 | 1.079 | 1.024 | 1.135 | inconclusive | equivalent |
| intermediate | 6036 | 4538 | 65.746 | 71.628 | 0.446 | 0.460 | 1.089 | 1.053 | 1.123 | inconclusive | equivalent |
| sparse | 1897 | 1575 | 58.790 | 61.248 | 0.173 | 0.184 | 1.042 | 0.958 | 1.105 | inconclusive | equivalent |
| very_sparse | 4729 | 2362 | 63.193 | 67.147 | 0.240 | 0.208 | 1.063 | 1.025 | 1.110 | inconclusive | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.003 | 0.001 | 0.008 | 0.007 | 0.004 | 0.013 | 0.071 | 0.000 | 1.000 | 0.086 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.241 | 1.074 | 1.050 | 1.097 | 0.018 | 0.000 | 0.050 | 0.037 | 0.070 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.726 | 19.158 |
| 2 | 24.715 | 29.835 |
| 3 | 34.113 | 34.930 |
| 4 | 41.713 | 44.811 |
| 5 | 54.181 | 59.118 |
| 6 | 61.999 | 69.262 |
| 7 | 77.122 | 84.366 |
| 8 | 94.503 | 104.190 |
| 9 | 124.196 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2380 | 1714 | 60.287 | 64.999 | 0.185 | 0.188 | 1.078 | 1.019 | 1.134 | inconclusive | equivalent |
| q2 | 2481 | 1910 | 60.878 | 64.822 | 0.197 | 0.194 | 1.065 | 1.007 | 1.122 | inconclusive | equivalent |
| q3 | 2891 | 1930 | 62.795 | 69.445 | 0.200 | 0.197 | 1.106 | 1.055 | 1.157 | inconclusive | inconclusive |
| q4 | 3057 | 2091 | 65.250 | 69.649 | 0.211 | 0.208 | 1.067 | 1.016 | 1.118 | inconclusive | equivalent |
| q5 | 3986 | 2190 | 71.251 | 75.379 | 0.207 | 0.212 | 1.058 | 1.013 | 1.104 | inconclusive | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.006 | 0.003 | 0.011 | 0.006 | 0.003 | 0.010 | 0.072 | 0.000 | 0.801 | 0.101 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.255 | 1.074 | 1.049 | 1.095 | 0.031 | 0.000 | 0.050 | 0.038 | 0.069 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.723 | 19.158 |
| 2 | 24.719 | 29.835 |
| 3 | 34.114 | 34.930 |
| 4 | 41.792 | 44.811 |
| 5 | 54.198 | 59.118 |
| 6 | 62.087 | 69.262 |
| 7 | 77.194 | 84.366 |
| 8 | 94.494 | 104.190 |
| 9 | 124.220 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2146 | 1448 | 67.325 | 73.906 | 0.115 | 0.124 | 1.098 | 1.025 | 1.173 | inconclusive | inconclusive |
| 1 | 5702 | 4119 | 63.607 | 65.392 | 0.388 | 0.390 | 1.028 | 0.997 | 1.066 | equivalent | equivalent |
| 2+ | 6947 | 4245 | 63.988 | 70.417 | 0.498 | 0.484 | 1.100 | 1.059 | 1.131 | inconclusive | equivalent |
| unknown | 0 | 23 | - | - | - | - | - | - | - |  |  |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.003 | 0.006 | 0.002 | 0.021 | - | 0.389 | 0.879 | - | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.254 | 1.074 | 1.049 | 1.096 | 0.031 | 0.002 | 0.050 | 0.038 | 0.069 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.697 | 19.158 |
| 2 | 24.698 | 29.835 |
| 3 | 34.088 | 34.930 |
| 4 | 41.681 | 44.811 |
| 5 | 54.186 | 59.118 |
| 6 | 62.005 | 69.262 |
| 7 | 77.210 | 84.366 |
| 8 | 94.509 | 104.190 |
| 9 | 124.248 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7241 | 5644 | 56.352 | 62.561 | 0.446 | 0.465 | 1.110 | 1.071 | 1.146 | inconclusive | equivalent |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7554 | 4190 | 70.554 | 74.625 | 0.554 | 0.535 | 1.058 | 1.027 | 1.086 | equivalent | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.020 | 0.014 | 0.027 | 0.014 | 0.009 | 0.021 | - | 0.544 | 1.000 | - | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 63.945 | 1.079 | 1.055 | 1.102 | -0.278 | 0.000 | 0.053 | 0.041 | 0.072 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.405 | 19.158 |
| 2 | 24.627 | 29.835 |
| 3 | 33.902 | 34.930 |
| 4 | 40.961 | 44.811 |
| 5 | 54.071 | 59.118 |
| 6 | 61.834 | 69.262 |
| 7 | 76.152 | 84.366 |
| 8 | 94.343 | 104.190 |
| 9 | 124.088 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 8069 | 5325 | 63.945 | 68.505 | 0.512 | 0.497 | 1.071 | 1.042 | 1.102 | inconclusive | equivalent |
| car_passenger_carpool | 402 | 382 | 53.641 | 59.402 | 0.025 | 0.024 | 1.107 | 0.957 | 1.263 | inconclusive | inconclusive |
| car_passenger_household | 933 | 821 | 47.974 | 53.924 | 0.083 | 0.096 | 1.124 | 1.033 | 1.213 | inconclusive | inconclusive |
| cycle | 274 | 161 | 48.262 | 51.043 | 0.021 | 0.019 | 1.058 | 0.888 | 1.260 | inconclusive | inconclusive |
| multimodal | 1278 | 788 | 95.138 | 98.233 | 0.095 | 0.097 | 1.033 | 0.977 | 1.084 | equivalent | equivalent |
| other | 439 | 224 | 64.596 | 70.109 | 0.040 | 0.026 | 1.085 | 0.964 | 1.233 | inconclusive | inconclusive |
| train | 412 | 159 | 126.151 | 144.717 | 0.020 | 0.021 | 1.147 | 1.020 | 1.276 | inconclusive | inconclusive |
| urban_pt | 1096 | 729 | 91.148 | 92.645 | 0.064 | 0.086 | 1.016 | 0.953 | 1.082 | equivalent | equivalent |
| walking_only | 1892 | 1246 | 36.722 | 37.832 | 0.140 | 0.135 | 1.030 | 0.971 | 1.088 | equivalent | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.141 | 0.117 | 0.166 | 0.159 | 0.143 | 0.179 | 0.063 | 0.309 | 0.814 | 0.137 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.878 | 1.064 | 1.041 | 1.086 | 0.655 | 0.000 | 0.045 | 0.033 | 0.062 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.010 | 19.158 |
| 2 | 24.864 | 29.835 |
| 3 | 34.309 | 34.930 |
| 4 | 43.598 | 44.811 |
| 5 | 54.400 | 59.118 |
| 6 | 63.844 | 69.262 |
| 7 | 78.876 | 84.366 |
| 8 | 94.852 | 104.190 |
| 9 | 124.611 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 564 | 402 | 68.039 | 75.764 | 0.041 | 0.040 | 1.114 | 1.020 | 1.199 | inconclusive | inconclusive |
| car_driver\|intermediate | 3025 | 2292 | 64.472 | 70.114 | 0.216 | 0.214 | 1.088 | 1.041 | 1.133 | inconclusive | equivalent |
| car_driver\|sparse | 1198 | 970 | 61.662 | 63.160 | 0.100 | 0.107 | 1.024 | 0.934 | 1.112 | inconclusive | equivalent |
| car_driver\|very_sparse | 3282 | 1661 | 63.584 | 68.003 | 0.155 | 0.136 | 1.069 | 1.009 | 1.122 | inconclusive | equivalent |
| car_passenger_carpool\|dense+intermediate | 221 | 236 | 53.941 | 62.392 | 0.014 | 0.014 | 1.157 | 0.981 | 1.339 | inconclusive | inconclusive |
| car_passenger_carpool\|sparse | 57 | 62 | 56.249 | 51.841 | 0.006 | 0.006 | 0.922 | 0.638 | 1.229 | inconclusive | inconclusive |
| car_passenger_carpool\|very_sparse | 124 | 84 | 49.352 | 59.710 | 0.005 | 0.005 | 1.210 | 0.969 | 1.558 | inconclusive | inconclusive |
| car_passenger_household\|dense | 73 | 66 | 47.721 | 66.883 | 0.007 | 0.008 | 1.402 | 1.131 | 1.714 | different | inconclusive |
| car_passenger_household\|intermediate | 334 | 376 | 48.481 | 53.951 | 0.035 | 0.044 | 1.113 | 0.961 | 1.245 | inconclusive | inconclusive |
| car_passenger_household\|sparse | 139 | 163 | 42.254 | 49.415 | 0.016 | 0.021 | 1.169 | 0.973 | 1.446 | inconclusive | inconclusive |
| car_passenger_household\|very_sparse | 387 | 216 | 51.134 | 53.274 | 0.024 | 0.023 | 1.042 | 0.923 | 1.167 | inconclusive | inconclusive |
| cycle\|dense+intermediate+sparse+very_sparse | 274 | 161 | 48.262 | 51.043 | 0.021 | 0.019 | 1.058 | 0.888 | 1.260 | inconclusive | inconclusive |
| multimodal\|dense | 211 | 114 | 109.197 | 103.449 | 0.013 | 0.012 | 0.947 | 0.813 | 1.071 | inconclusive | inconclusive |
| multimodal\|intermediate | 552 | 381 | 97.730 | 102.910 | 0.045 | 0.050 | 1.053 | 0.970 | 1.133 | inconclusive | equivalent |
| multimodal\|sparse | 135 | 105 | 80.725 | 90.198 | 0.014 | 0.014 | 1.117 | 0.957 | 1.296 | inconclusive | inconclusive |
| multimodal\|very_sparse | 380 | 188 | 91.317 | 89.180 | 0.023 | 0.020 | 0.977 | 0.852 | 1.119 | inconclusive | equivalent |
| other\|dense+intermediate | 193 | 131 | 61.257 | 67.656 | 0.018 | 0.014 | 1.104 | 0.937 | 1.308 | inconclusive | inconclusive |
| other\|sparse+very_sparse | 246 | 93 | 67.320 | 73.020 | 0.022 | 0.012 | 1.085 | 0.918 | 1.290 | inconclusive | inconclusive |
| train\|dense+intermediate+sparse+very_sparse | 412 | 159 | 126.151 | 144.717 | 0.020 | 0.021 | 1.147 | 1.020 | 1.276 | inconclusive | inconclusive |
| urban_pt\|dense | 583 | 314 | 90.074 | 89.973 | 0.029 | 0.037 | 0.999 | 0.916 | 1.090 | equivalent | equivalent |
| urban_pt\|intermediate | 463 | 358 | 92.397 | 95.196 | 0.031 | 0.040 | 1.030 | 0.936 | 1.128 | inconclusive | equivalent |
| urban_pt\|sparse+very_sparse | 50 | 57 | 89.567 | 92.276 | 0.004 | 0.008 | 1.030 | 0.828 | 1.265 | inconclusive | inconclusive |
| walking_only\|dense | 489 | 323 | 39.534 | 43.852 | 0.037 | 0.036 | 1.109 | 0.980 | 1.257 | inconclusive | inconclusive |
| walking_only\|intermediate | 919 | 648 | 36.882 | 38.234 | 0.071 | 0.067 | 1.037 | 0.950 | 1.123 | inconclusive | equivalent |
| walking_only\|sparse | 224 | 177 | 36.246 | 34.142 | 0.020 | 0.022 | 0.942 | 0.785 | 1.078 | inconclusive | inconclusive |
| walking_only\|very_sparse | 260 | 98 | 27.638 | 21.107 | 0.012 | 0.010 | 0.764 | 0.611 | 0.959 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.145 | 0.122 | 0.174 | 0.165 | 0.151 | 0.188 | 0.073 | 0.033 | 0.671 | 0.338 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|intermediate | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|sparse | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|very_sparse | cycle\|dense+intermediate+sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|sparse+very_sparse |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.852 | 1.064 | 1.040 | 1.085 | 0.628 | 0.000 | 0.045 | 0.034 | 0.062 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.006 | 19.158 |
| 2 | 24.835 | 29.835 |
| 3 | 34.279 | 34.930 |
| 4 | 43.396 | 44.811 |
| 5 | 54.375 | 59.118 |
| 6 | 63.780 | 69.262 |
| 7 | 78.801 | 84.366 |
| 8 | 94.862 | 104.190 |
| 9 | 124.602 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 63 | 37 | 50.435 | - | 0.009 | - | - | - | - |  |  |
| car_driver\|employed | 5107 | 2915 | 67.777 | 73.302 | 0.340 | 0.317 | 1.082 | 1.044 | 1.119 | inconclusive | equivalent |
| car_driver\|other_inactive | 577 | 278 | 59.655 | 66.020 | 0.036 | 0.027 | 1.107 | 0.969 | 1.249 | inconclusive | inconclusive |
| car_driver\|retired | 2027 | 1839 | 55.187 | 57.704 | 0.110 | 0.123 | 1.046 | 0.989 | 1.102 | inconclusive | equivalent |
| car_driver\|unemployed | 295 | 252 | 59.881 | 67.163 | 0.017 | 0.024 | 1.122 | 0.980 | 1.270 | inconclusive | inconclusive |
| car_passenger_carpool\|children_6_17 | 24 | 23 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 118 | 63 | 54.201 | 72.848 | 0.009 | 0.005 | 1.344 | 1.077 | 1.634 | inconclusive | inconclusive |
| car_passenger_carpool\|other_inactive | 62 | 52 | 61.158 | 63.321 | 0.003 | 0.004 | 1.035 | 0.772 | 1.401 | inconclusive | inconclusive |
| car_passenger_carpool\|retired | 171 | 212 | 52.704 | 57.462 | 0.008 | 0.009 | 1.090 | 0.865 | 1.329 | inconclusive | inconclusive |
| car_passenger_carpool\|unemployed | 26 | 30 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 407 | 318 | 39.321 | 46.411 | 0.049 | 0.056 | 1.180 | 1.056 | 1.285 | inconclusive | inconclusive |
| car_passenger_household\|employed | 154 | 85 | 60.529 | 70.049 | 0.010 | 0.008 | 1.157 | 0.949 | 1.450 | inconclusive | inconclusive |
| car_passenger_household\|other_inactive | 108 | 82 | 70.807 | 65.625 | 0.007 | 0.008 | 0.927 | 0.720 | 1.205 | inconclusive | inconclusive |
| car_passenger_household\|retired | 238 | 313 | 57.570 | 62.963 | 0.015 | 0.021 | 1.094 | 0.963 | 1.267 | inconclusive | inconclusive |
| car_passenger_household\|unemployed | 26 | 23 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 43 | 18 | - | - | - | - | - | - | - |  |  |
| cycle\|employed | 124 | 79 | 65.250 | 53.757 | 0.008 | 0.010 | 0.824 | 0.653 | 1.031 | inconclusive | inconclusive |
| cycle\|other_inactive | 25 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 70 | 40 | 36.268 | - | 0.004 | - | - | - | - |  |  |
| cycle\|unemployed | 12 | 9 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 227 | 158 | 66.568 | 67.501 | 0.027 | 0.026 | 1.014 | 0.866 | 1.156 | inconclusive | inconclusive |
| multimodal\|employed | 664 | 366 | 107.770 | 111.005 | 0.046 | 0.044 | 1.030 | 0.962 | 1.100 | inconclusive | equivalent |
| multimodal\|other_inactive | 123 | 63 | 108.176 | 117.000 | 0.009 | 0.010 | 1.082 | 0.915 | 1.267 | inconclusive | inconclusive |
| multimodal\|retired | 207 | 156 | 102.510 | 100.266 | 0.009 | 0.011 | 0.978 | 0.863 | 1.097 | inconclusive | equivalent |
| multimodal\|unemployed | 57 | 45 | 99.030 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 181 | 47 | 67.644 | - | 0.020 | - | - | - | - |  |  |
| other\|employed | 178 | 89 | 63.404 | 72.127 | 0.014 | 0.012 | 1.138 | 0.943 | 1.464 | inconclusive | inconclusive |
| other\|other_inactive | 28 | 24 | - | - | - | - | - | - | - |  |  |
| other\|retired | 46 | 58 | - | 69.270 | - | 0.003 | - | - | - |  |  |
| other\|unemployed | 6 | 6 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 14 | - | - | - | - | - | - | - |  |  |
| train\|employed | 306 | 109 | 130.255 | 153.747 | 0.013 | 0.012 | 1.180 | 1.059 | 1.314 | inconclusive | inconclusive |
| train\|other_inactive | 39 | 16 | - | - | - | - | - | - | - |  |  |
| train\|retired | 38 | 13 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 6 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 93 | 120 | 90.981 | 86.225 | 0.012 | 0.022 | 0.948 | 0.749 | 1.204 | inconclusive | inconclusive |
| urban_pt\|employed | 537 | 266 | 92.485 | 95.223 | 0.028 | 0.031 | 1.030 | 0.956 | 1.111 | inconclusive | equivalent |
| urban_pt\|other_inactive | 189 | 128 | 90.360 | 95.136 | 0.013 | 0.017 | 1.053 | 0.939 | 1.192 | inconclusive | inconclusive |
| urban_pt\|retired | 220 | 149 | 80.608 | 91.866 | 0.009 | 0.010 | 1.140 | 1.022 | 1.273 | inconclusive | inconclusive |
| urban_pt\|unemployed | 57 | 64 | 112.979 | 96.999 | 0.003 | 0.006 | 0.859 | 0.644 | 1.186 | inconclusive | inconclusive |
| walking_only\|children_6_17 | 250 | 190 | 34.729 | 32.025 | 0.040 | 0.041 | 0.922 | 0.807 | 1.063 | inconclusive | inconclusive |
| walking_only\|employed | 498 | 261 | 39.207 | 40.746 | 0.032 | 0.029 | 1.039 | 0.914 | 1.179 | inconclusive | inconclusive |
| walking_only\|other_inactive | 268 | 160 | 36.154 | 45.631 | 0.019 | 0.015 | 1.262 | 1.102 | 1.460 | different | inconclusive |
| walking_only\|retired | 741 | 538 | 35.050 | 37.052 | 0.038 | 0.041 | 1.057 | 0.945 | 1.147 | inconclusive | equivalent |
| walking_only\|unemployed | 135 | 96 | 43.928 | 46.602 | 0.010 | 0.008 | 1.061 | 0.799 | 1.398 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.171 | 0.145 | 0.202 | 0.197 | 0.181 | 0.233 | 0.083 | 0.000 | 0.569 | 0.612 | 0.000 | 0.001 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.003 | 64.793 | 1.065 | 1.044 | 1.087 | 0.569 | 0.000 | 0.047 | 0.034 | 0.065 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.003 | 19.157 |
| 2 | 24.843 | 29.834 |
| 3 | 34.214 | 34.924 |
| 4 | 42.976 | 44.808 |
| 5 | 54.313 | 59.117 |
| 6 | 62.404 | 69.260 |
| 7 | 78.100 | 84.361 |
| 8 | 94.810 | 104.187 |
| 9 | 124.683 | 134.646 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 944 | 603 | 56.587 | 63.421 | 0.066 | 0.059 | 1.121 | 1.030 | 1.237 | inconclusive | inconclusive |
| car_driver\|q2 | 1282 | 992 | 59.662 | 62.036 | 0.093 | 0.094 | 1.040 | 0.974 | 1.103 | inconclusive | equivalent |
| car_driver\|q3 | 1685 | 1133 | 62.166 | 67.440 | 0.113 | 0.108 | 1.085 | 0.998 | 1.153 | inconclusive | inconclusive |
| car_driver\|q4 | 1809 | 1278 | 66.914 | 71.136 | 0.116 | 0.118 | 1.063 | 1.009 | 1.127 | inconclusive | equivalent |
| car_driver\|q5 | 2349 | 1319 | 69.871 | 74.564 | 0.125 | 0.118 | 1.067 | 1.016 | 1.124 | inconclusive | equivalent |
| car_passenger_carpool\|q1 | 114 | 117 | 52.706 | 59.945 | 0.006 | 0.008 | 1.137 | 0.925 | 1.420 | inconclusive | inconclusive |
| car_passenger_carpool\|q2 | 88 | 99 | 44.605 | 52.436 | 0.006 | 0.005 | 1.176 | 0.918 | 1.446 | inconclusive | inconclusive |
| car_passenger_carpool\|q3 | 79 | 69 | 56.113 | 56.070 | 0.005 | 0.004 | 0.999 | 0.707 | 1.406 | inconclusive | inconclusive |
| car_passenger_carpool\|q4+q5 | 121 | 97 | 59.698 | 65.662 | 0.007 | 0.007 | 1.100 | 0.875 | 1.384 | inconclusive | inconclusive |
| car_passenger_household\|q1 | 142 | 138 | 55.349 | 49.989 | 0.014 | 0.019 | 0.903 | 0.721 | 1.067 | inconclusive | inconclusive |
| car_passenger_household\|q2 | 192 | 185 | 44.356 | 56.819 | 0.019 | 0.022 | 1.281 | 1.069 | 1.479 | inconclusive | inconclusive |
| car_passenger_household\|q3 | 198 | 171 | 52.268 | 54.636 | 0.017 | 0.020 | 1.045 | 0.876 | 1.239 | inconclusive | inconclusive |
| car_passenger_household\|q4 | 198 | 180 | 42.070 | 52.189 | 0.020 | 0.020 | 1.241 | 1.061 | 1.446 | inconclusive | inconclusive |
| car_passenger_household\|q5 | 203 | 147 | 48.994 | 56.247 | 0.012 | 0.014 | 1.148 | 0.960 | 1.334 | inconclusive | inconclusive |
| cycle\|q1+q2 | 108 | 67 | 52.101 | 49.962 | 0.009 | 0.008 | 0.959 | 0.666 | 1.337 | inconclusive | inconclusive |
| cycle\|q3+q4+q5 | 166 | 94 | 45.362 | 51.802 | 0.012 | 0.011 | 1.142 | 0.999 | 1.348 | inconclusive | inconclusive |
| multimodal\|q1 | 180 | 117 | 85.689 | 106.661 | 0.016 | 0.015 | 1.245 | 1.074 | 1.403 | inconclusive | inconclusive |
| multimodal\|q2 | 210 | 137 | 97.475 | 86.489 | 0.021 | 0.017 | 0.887 | 0.782 | 1.008 | inconclusive | inconclusive |
| multimodal\|q3 | 233 | 160 | 94.280 | 92.988 | 0.019 | 0.022 | 0.986 | 0.879 | 1.091 | inconclusive | equivalent |
| multimodal\|q4 | 261 | 175 | 91.729 | 96.998 | 0.021 | 0.021 | 1.057 | 0.908 | 1.207 | inconclusive | inconclusive |
| multimodal\|q5 | 394 | 199 | 104.908 | 107.433 | 0.019 | 0.022 | 1.024 | 0.930 | 1.136 | inconclusive | equivalent |
| other\|q1+q2 | 184 | 105 | 66.482 | 64.195 | 0.019 | 0.011 | 0.966 | 0.816 | 1.142 | inconclusive | inconclusive |
| other\|q3+q4+q5 | 255 | 119 | 62.924 | 74.737 | 0.021 | 0.014 | 1.188 | 1.018 | 1.401 | inconclusive | inconclusive |
| train\|q1+q2+q3+q4 | 235 | 106 | 126.221 | 154.920 | 0.013 | 0.015 | 1.227 | 1.083 | 1.392 | inconclusive | inconclusive |
| train\|q5 | 177 | 53 | 126.035 | 119.376 | 0.007 | 0.006 | 0.947 | 0.850 | 1.070 | inconclusive | inconclusive |
| urban_pt\|q1 | 253 | 249 | 96.820 | 91.317 | 0.019 | 0.029 | 0.943 | 0.824 | 1.071 | inconclusive | inconclusive |
| urban_pt\|q2 | 176 | 136 | 94.604 | 90.924 | 0.013 | 0.017 | 0.961 | 0.833 | 1.122 | inconclusive | inconclusive |
| urban_pt\|q3 | 181 | 112 | 90.074 | 95.315 | 0.009 | 0.014 | 1.058 | 0.947 | 1.194 | inconclusive | inconclusive |
| urban_pt\|q4 | 202 | 99 | 79.371 | 93.218 | 0.013 | 0.011 | 1.174 | 1.047 | 1.339 | inconclusive | inconclusive |
| urban_pt\|q5 | 284 | 133 | 91.776 | 94.024 | 0.010 | 0.016 | 1.024 | 0.935 | 1.109 | inconclusive | equivalent |
| walking_only\|q1 | 566 | 389 | 39.597 | 39.765 | 0.048 | 0.045 | 1.004 | 0.900 | 1.128 | inconclusive | equivalent |
| walking_only\|q2 | 337 | 238 | 33.419 | 39.180 | 0.029 | 0.025 | 1.172 | 1.003 | 1.351 | inconclusive | inconclusive |
| walking_only\|q3 | 333 | 186 | 34.040 | 32.804 | 0.023 | 0.018 | 0.964 | 0.835 | 1.127 | inconclusive | inconclusive |
| walking_only\|q4 | 302 | 219 | 38.324 | 35.330 | 0.021 | 0.023 | 0.922 | 0.791 | 1.046 | inconclusive | inconclusive |
| walking_only\|q5 | 354 | 214 | 35.919 | 39.058 | 0.019 | 0.023 | 1.087 | 0.948 | 1.249 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.150 | 0.127 | 0.178 | 0.168 | 0.154 | 0.194 | 0.081 | 0.000 | 0.432 | 0.248 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2 |
| cycle\|q2 | cycle\|q1+q2 |
| cycle\|q3 | cycle\|q3+q4+q5 |
| cycle\|q4 | cycle\|q3+q4+q5 |
| cycle\|q5 | cycle\|q3+q4+q5 |
| other\|q1 | other\|q1+q2 |
| other\|q2 | other\|q1+q2 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 65.058 | 1.061 | 1.039 | 1.082 | 0.835 | 0.000 | 0.043 | 0.031 | 0.061 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.012 | 19.158 |
| 2 | 24.921 | 29.835 |
| 3 | 34.344 | 34.930 |
| 4 | 43.919 | 44.811 |
| 5 | 54.447 | 59.118 |
| 6 | 64.804 | 69.262 |
| 7 | 79.051 | 84.366 |
| 8 | 94.981 | 104.190 |
| 9 | 124.702 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3260 | 2490 | 63.888 | 65.343 | 0.197 | 0.198 | 1.023 | 0.972 | 1.079 | equivalent | equivalent |
| car_driver\|2+ | 4809 | 2829 | 63.981 | 70.641 | 0.315 | 0.299 | 1.104 | 1.069 | 1.150 | inconclusive | equivalent |
| car_driver\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 177 | 198 | 48.271 | 54.451 | 0.009 | 0.009 | 1.128 | 0.956 | 1.326 | inconclusive | inconclusive |
| car_passenger_carpool\|1 | 143 | 127 | 61.837 | 64.262 | 0.007 | 0.008 | 1.039 | 0.813 | 1.292 | inconclusive | inconclusive |
| car_passenger_carpool\|2+ | 82 | 56 | 52.440 | 59.623 | 0.008 | 0.007 | 1.137 | 0.910 | 1.420 | inconclusive | inconclusive |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 383 | 368 | 53.003 | 52.050 | 0.035 | 0.043 | 0.982 | 0.863 | 1.100 | inconclusive | equivalent |
| car_passenger_household\|2+ | 550 | 451 | 44.236 | 55.527 | 0.047 | 0.053 | 1.255 | 1.140 | 1.385 | different | inconclusive |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0+1+2+ | 274 | 159 | 48.262 | 51.102 | 0.021 | 0.018 | 1.059 | 0.890 | 1.264 | inconclusive | inconclusive |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 145 | 78 | 109.202 | 133.909 | 0.008 | 0.008 | 1.226 | 1.068 | 1.380 | inconclusive | inconclusive |
| multimodal\|1 | 456 | 284 | 95.894 | 99.444 | 0.035 | 0.032 | 1.037 | 0.950 | 1.137 | inconclusive | equivalent |
| multimodal\|2+ | 677 | 425 | 92.497 | 92.768 | 0.053 | 0.057 | 1.003 | 0.921 | 1.089 | equivalent | equivalent |
| multimodal\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| other\|0 | 79 | 57 | 54.647 | 71.824 | 0.006 | 0.004 | 1.314 | 0.957 | 1.677 | inconclusive | inconclusive |
| other\|1 | 156 | 85 | 64.491 | 68.909 | 0.015 | 0.011 | 1.069 | 0.913 | 1.258 | inconclusive | inconclusive |
| other\|2+ | 204 | 82 | 67.515 | 70.747 | 0.019 | 0.011 | 1.048 | 0.877 | 1.279 | inconclusive | inconclusive |
| train\|0 | 140 | 52 | 129.183 | 167.402 | 0.005 | 0.005 | 1.296 | 1.070 | 1.480 | inconclusive | inconclusive |
| train\|1+2+ | 272 | 104 | 125.137 | 130.345 | 0.015 | 0.015 | 1.042 | 0.931 | 1.156 | inconclusive | inconclusive |
| train\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 630 | 422 | 96.418 | 93.504 | 0.031 | 0.041 | 0.970 | 0.878 | 1.072 | inconclusive | equivalent |
| urban_pt\|1 | 337 | 207 | 84.148 | 83.848 | 0.023 | 0.028 | 0.996 | 0.927 | 1.082 | equivalent | equivalent |
| urban_pt\|2+ | 129 | 95 | 91.377 | 104.834 | 0.010 | 0.017 | 1.147 | 1.004 | 1.300 | inconclusive | inconclusive |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 810 | 524 | 40.008 | 42.142 | 0.045 | 0.046 | 1.053 | 0.976 | 1.158 | inconclusive | inconclusive |
| walking_only\|1 | 756 | 498 | 34.557 | 39.202 | 0.062 | 0.059 | 1.134 | 1.026 | 1.246 | inconclusive | inconclusive |
| walking_only\|2+ | 326 | 221 | 36.310 | 28.063 | 0.033 | 0.029 | 0.773 | 0.653 | 0.875 | different | inconclusive |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.144 | 0.120 | 0.171 | 0.177 | 0.155 | 0.212 | - | 0.278 | 0.693 | - | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| cycle\|0 | cycle\|0+1+2+ |
| cycle\|1 | cycle\|0+1+2+ |
| cycle\|2+ | cycle\|0+1+2+ |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.923 | 1.063 | 1.041 | 1.085 | 0.700 | 0.002 | 0.044 | 0.032 | 0.062 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.018 | 19.158 |
| 2 | 24.876 | 29.835 |
| 3 | 34.302 | 34.930 |
| 4 | 43.640 | 44.811 |
| 5 | 54.409 | 59.118 |
| 6 | 63.880 | 69.262 |
| 7 | 79.005 | 84.366 |
| 8 | 94.877 | 104.190 |
| 9 | 124.646 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 209 | 125 | 49.277 | 55.187 | 0.020 | 0.022 | 1.120 | 0.911 | 1.327 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q1 | 127 | 182 | 57.427 | 58.352 | 0.025 | 0.036 | 1.016 | 0.814 | 1.230 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q2 | 143 | 118 | 48.939 | 53.571 | 0.025 | 0.022 | 1.095 | 0.935 | 1.286 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q3 | 107 | 84 | 48.697 | 54.424 | 0.015 | 0.015 | 1.118 | 0.879 | 1.368 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q4 | 133 | 97 | 46.348 | 54.052 | 0.018 | 0.018 | 1.166 | 0.946 | 1.406 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q1 | 124 | 67 | 46.625 | 50.737 | 0.016 | 0.013 | 1.088 | 0.831 | 1.342 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q2 | 179 | 81 | 57.961 | 45.610 | 0.018 | 0.015 | 0.787 | 0.657 | 0.946 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q3 | 143 | 93 | 51.283 | 54.783 | 0.015 | 0.016 | 1.068 | 0.870 | 1.289 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q4 | 142 | 78 | 45.933 | 45.754 | 0.016 | 0.013 | 0.996 | 0.823 | 1.187 | inconclusive | inconclusive |
| employed\|dense\|q1 | 88 | 68 | 83.792 | 81.842 | 0.008 | 0.008 | 0.977 | 0.794 | 1.184 | inconclusive | inconclusive |
| employed\|dense\|q2 | 115 | 75 | 80.514 | 83.033 | 0.009 | 0.009 | 1.031 | 0.830 | 1.262 | inconclusive | inconclusive |
| employed\|dense\|q3 | 213 | 90 | 75.237 | 77.305 | 0.015 | 0.009 | 1.027 | 0.898 | 1.153 | inconclusive | inconclusive |
| employed\|dense\|q4 | 245 | 135 | 66.663 | 78.945 | 0.016 | 0.016 | 1.184 | 1.037 | 1.345 | inconclusive | inconclusive |
| employed\|dense\|q5 | 461 | 205 | 82.108 | 80.698 | 0.022 | 0.026 | 0.983 | 0.885 | 1.082 | inconclusive | equivalent |
| employed\|intermediate\|q1 | 221 | 197 | 75.980 | 71.175 | 0.018 | 0.027 | 0.937 | 0.802 | 1.115 | inconclusive | inconclusive |
| employed\|intermediate\|q2 | 412 | 308 | 70.133 | 75.902 | 0.038 | 0.033 | 1.082 | 0.974 | 1.222 | inconclusive | inconclusive |
| employed\|intermediate\|q3 | 570 | 391 | 67.486 | 82.990 | 0.046 | 0.044 | 1.230 | 1.130 | 1.355 | different | inconclusive |
| employed\|intermediate\|q4 | 777 | 445 | 74.485 | 76.802 | 0.053 | 0.046 | 1.031 | 0.943 | 1.126 | inconclusive | equivalent |
| employed\|intermediate\|q5 | 1142 | 590 | 82.570 | 86.963 | 0.062 | 0.063 | 1.053 | 0.989 | 1.139 | inconclusive | equivalent |
| employed\|sparse+very_sparse\|q1 | 339 | 136 | 62.794 | 67.657 | 0.024 | 0.019 | 1.077 | 0.932 | 1.218 | inconclusive | inconclusive |
| employed\|sparse\|q2 | 156 | 99 | 54.892 | 58.571 | 0.015 | 0.013 | 1.067 | 0.901 | 1.253 | inconclusive | inconclusive |
| employed\|sparse\|q3 | 196 | 141 | 67.626 | 72.107 | 0.017 | 0.019 | 1.066 | 0.810 | 1.316 | inconclusive | inconclusive |
| employed\|sparse\|q4 | 250 | 174 | 71.503 | 75.379 | 0.025 | 0.022 | 1.054 | 0.882 | 1.240 | inconclusive | inconclusive |
| employed\|sparse\|q5 | 245 | 167 | 71.895 | 73.265 | 0.017 | 0.018 | 1.019 | 0.892 | 1.172 | inconclusive | inconclusive |
| employed\|very_sparse\|q2 | 462 | 209 | 63.679 | 78.493 | 0.028 | 0.023 | 1.233 | 1.081 | 1.411 | inconclusive | inconclusive |
| employed\|very_sparse\|q3 | 574 | 272 | 68.435 | 72.896 | 0.029 | 0.028 | 1.065 | 0.948 | 1.185 | inconclusive | inconclusive |
| employed\|very_sparse\|q4 | 669 | 281 | 70.724 | 82.382 | 0.035 | 0.024 | 1.165 | 1.053 | 1.272 | inconclusive | inconclusive |
| employed\|very_sparse\|q5 | 551 | 250 | 75.027 | 80.168 | 0.022 | 0.021 | 1.069 | 0.942 | 1.205 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 194 | 110 | 68.183 | 80.263 | 0.011 | 0.013 | 1.177 | 0.986 | 1.403 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 150 | 68 | 70.086 | 89.786 | 0.010 | 0.009 | 1.281 | 1.001 | 1.571 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 224 | 56 | 68.084 | 80.123 | 0.012 | 0.008 | 1.177 | 0.817 | 1.542 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate\|q2 | 165 | 136 | 66.098 | 78.899 | 0.013 | 0.014 | 1.194 | 1.022 | 1.412 | inconclusive | inconclusive |
| other_inactive\|dense\|q1 | 180 | 107 | 64.468 | 72.560 | 0.010 | 0.010 | 1.126 | 0.973 | 1.354 | inconclusive | inconclusive |
| other_inactive\|intermediate\|q1 | 224 | 193 | 65.722 | 68.994 | 0.019 | 0.016 | 1.050 | 0.879 | 1.240 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q1 | 164 | 88 | 69.914 | 62.419 | 0.011 | 0.009 | 0.893 | 0.647 | 1.218 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q2 | 118 | 60 | 60.447 | 68.307 | 0.008 | 0.007 | 1.130 | 0.901 | 1.449 | inconclusive | inconclusive |
| retired\|dense+intermediate\|q1 | 282 | 205 | 51.396 | 54.375 | 0.019 | 0.013 | 1.058 | 0.898 | 1.241 | inconclusive | inconclusive |
| retired\|dense\|q2 | 55 | 67 | 70.002 | 58.518 | 0.003 | 0.004 | 0.836 | 0.615 | 1.134 | inconclusive | inconclusive |
| retired\|dense\|q3 | 82 | 69 | 47.301 | 69.843 | 0.004 | 0.005 | 1.477 | 1.101 | 2.039 | different | inconclusive |
| retired\|dense\|q4 | 85 | 91 | 49.227 | 65.494 | 0.005 | 0.007 | 1.330 | 1.043 | 1.647 | inconclusive | inconclusive |
| retired\|dense\|q5 | 183 | 120 | 66.296 | 73.042 | 0.009 | 0.009 | 1.102 | 0.922 | 1.282 | inconclusive | inconclusive |
| retired\|intermediate\|q2 | 211 | 300 | 49.768 | 61.783 | 0.014 | 0.019 | 1.241 | 1.053 | 1.438 | inconclusive | inconclusive |
| retired\|intermediate\|q3 | 314 | 295 | 57.566 | 52.334 | 0.021 | 0.020 | 0.909 | 0.802 | 1.048 | inconclusive | inconclusive |
| retired\|intermediate\|q4 | 262 | 344 | 62.806 | 64.553 | 0.014 | 0.024 | 1.028 | 0.898 | 1.204 | inconclusive | inconclusive |
| retired\|intermediate\|q5 | 519 | 382 | 56.214 | 66.422 | 0.024 | 0.024 | 1.182 | 1.046 | 1.336 | inconclusive | inconclusive |
| retired\|sparse\|q1 | 90 | 77 | 34.381 | 52.421 | 0.007 | 0.005 | 1.525 | 1.187 | 1.966 | different | different |
| retired\|sparse\|q2 | 95 | 158 | 43.476 | 48.273 | 0.007 | 0.014 | 1.110 | 0.879 | 1.488 | inconclusive | inconclusive |
| retired\|sparse\|q3 | 110 | 118 | 50.156 | 60.118 | 0.009 | 0.010 | 1.199 | 0.904 | 1.574 | inconclusive | inconclusive |
| retired\|sparse\|q4 | 98 | 136 | 49.140 | 46.680 | 0.006 | 0.011 | 0.950 | 0.761 | 1.143 | inconclusive | inconclusive |
| retired\|sparse\|q5 | 121 | 116 | 59.486 | 57.113 | 0.008 | 0.009 | 0.960 | 0.787 | 1.167 | inconclusive | inconclusive |
| retired\|very_sparse\|q1 | 287 | 94 | 46.330 | 43.222 | 0.009 | 0.005 | 0.933 | 0.759 | 1.143 | inconclusive | inconclusive |
| retired\|very_sparse\|q2 | 243 | 204 | 54.941 | 48.665 | 0.010 | 0.011 | 0.886 | 0.762 | 1.053 | inconclusive | inconclusive |
| retired\|very_sparse\|q3 | 291 | 198 | 56.455 | 55.766 | 0.012 | 0.011 | 0.988 | 0.852 | 1.151 | inconclusive | inconclusive |
| retired\|very_sparse\|q4 | 173 | 191 | 58.714 | 57.744 | 0.006 | 0.012 | 0.983 | 0.835 | 1.146 | inconclusive | inconclusive |
| retired\|very_sparse\|q5 | 257 | 153 | 65.429 | 65.870 | 0.008 | 0.008 | 1.007 | 0.871 | 1.203 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 127 | 94 | 70.372 | 70.406 | 0.008 | 0.010 | 1.000 | 0.778 | 1.252 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 97 | 69 | 68.739 | 82.120 | 0.006 | 0.007 | 1.195 | 0.930 | 1.472 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 146 | 72 | 67.624 | 69.542 | 0.008 | 0.008 | 1.028 | 0.834 | 1.260 | inconclusive | inconclusive |
| unemployed\|dense+intermediate\|q1 | 158 | 217 | 55.593 | 79.559 | 0.012 | 0.018 | 1.431 | 1.164 | 1.743 | different | different |
| unemployed\|sparse+very_sparse\|q1 | 96 | 79 | 64.702 | 66.075 | 0.005 | 0.007 | 1.021 | 0.761 | 1.352 | inconclusive | inconclusive |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.048 | 0.044 | 0.066 | 0.057 | 0.054 | 0.079 | 0.100 | 0.000 | 0.136 | 0.422 | 0.000 | 0.001 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.003 | 63.978 | 1.079 | 1.053 | 1.102 | -0.246 | 0.000 | 0.053 | 0.039 | 0.073 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.368 | 19.157 |
| 2 | 24.649 | 29.834 |
| 3 | 33.857 | 34.924 |
| 4 | 40.823 | 44.808 |
| 5 | 54.003 | 59.117 |
| 6 | 61.800 | 69.260 |
| 7 | 76.645 | 84.361 |
| 8 | 94.429 | 104.187 |
| 9 | 124.082 | 134.646 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: cell levels

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4339 | 2963 | 61.923 | 64.932 | 0.242 | 0.242 | 1.049 | 1.005 | 1.092 | equivalent | equivalent |
| couple_with_children | 5263 | 2842 | 65.865 | 70.889 | 0.489 | 0.449 | 1.076 | 1.040 | 1.106 | inconclusive | equivalent |
| other | 347 | 202 | 62.606 | 73.048 | 0.036 | 0.033 | 1.167 | 1.022 | 1.299 | inconclusive | inconclusive |
| single_parent | 1119 | 794 | 64.517 | 70.313 | 0.086 | 0.111 | 1.090 | 0.995 | 1.174 | inconclusive | inconclusive |
| single_person | 3727 | 3034 | 62.757 | 68.197 | 0.146 | 0.165 | 1.087 | 1.043 | 1.141 | inconclusive | equivalent |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: stability and explained variance

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.005 | 0.002 | 0.001 | 0.006 | 0.073 | 0.242 | 0.867 | 0.154 | 0.000 | 0.000 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed full-sample merges

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69.011 | 64.142 | 1.076 | 1.052 | 1.098 | -0.081 | 0.000 | 0.050 | 0.040 | 0.069 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 18.675 | 19.158 |
| 2 | 24.676 | 29.835 |
| 3 | 34.033 | 34.930 |
| 4 | 41.278 | 44.811 |
| 5 | 54.147 | 59.118 |
| 6 | 61.976 | 69.262 |
| 7 | 76.962 | 84.366 |
| 8 | 94.389 | 104.190 |
| 9 | 124.179 | 134.643 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person mode use and user-day minutes

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 3809 | 2503 | 0.221 | 0.226 | 30.428 | 31.440 |
| bike | 422 | 266 | 0.026 | 0.026 | 38.585 | 39.075 |
| car_driver | 8834 | 5785 | 0.455 | 0.445 | 60.670 | 64.455 |
| car_passenger | 2168 | 1718 | 0.142 | 0.150 | 40.500 | 45.377 |
| urban_pt | 1475 | 959 | 0.074 | 0.096 | 72.107 | 74.956 |
| train | 603 | 253 | 0.023 | 0.028 | 116.414 | 125.735 |
| other | 650 | 355 | 0.049 | 0.035 | 58.239 | 59.044 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode model

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 52.017 | 56.345 | 53.128 | 1.111 | -0.083 | 2.464 | 3.217 | 1.867 | 4.487 | 0.031 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode deciles

Scope: All days · destination purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 0.000 | 0.000 |
| 2 | 7.617 | 9.850 |
| 3 | 19.615 | 19.809 |
| 4 | 29.949 | 29.991 |
| 5 | 39.956 | 44.454 |
| 6 | 54.719 | 59.266 |
| 7 | 69.217 | 74.086 |
| 8 | 89.833 | 93.155 |
| 9 | 119.300 | 124.658 |

n: 2008 14795, 2019 9835 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

## All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`)

### Grouping summary

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | 0.037 | 0.036 | - | - | - | - | - | - | 6 |
| category | 0.034 | 0.032 | - | - | - | - | - | - | 5 |
| category_x_density_x_income | 0.050 | 0.050 | - | - | - | - | - | - | 60 |
| day_mode_group | 0.134 | 0.116 | - | - | - | - | - | - | 9 |
| day_mode_group_x_category | 0.166 | 0.151 | - | - | - | - | - | - | 45 |
| day_mode_group_x_density | 0.137 | 0.127 | - | - | - | - | - | - | 27 |
| day_mode_group_x_income | 0.145 | 0.127 | - | - | - | - | - | - | 36 |
| day_mode_group_x_vehicles | 0.137 | 0.126 | - | - | - | - | - | - | 32 |
| day_purpose | 0.015 | 0.005 | - | - | - | - | - | - | 3 |
| density | 0.002 | 0.005 | - | - | - | - | - | - | 4 |
| household_type | 0.001 | 0.002 | - | - | - | - | - | - | 5 |
| income | 0.012 | 0.007 | - | - | - | - | - | - | 5 |
| none | 0.000 | 0.000 | - | - | - | - | - | - | 1 |
| vehicles | 0.000 | 0.003 | - | - | - | - | - | - | 4 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 15168 | 10089 | 69.878 | 74.696 | 1.000 | 1.000 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1324 | 943 | 52.697 | 56.392 | 0.168 | 0.168 | - | - | - |  |  |
| employed | 7918 | 4362 | 80.161 | 84.912 | 0.505 | 0.471 | - | - | - |  |  |
| other_inactive | 1443 | 838 | 69.945 | 79.915 | 0.093 | 0.086 | - | - | - |  |  |
| retired | 3843 | 3389 | 58.069 | 63.273 | 0.194 | 0.223 | - | - | - |  |  |
| unemployed | 639 | 546 | 69.219 | 81.431 | 0.039 | 0.052 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.034 | 0.026 | 0.042 | 0.032 | 0.025 | 0.041 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.677 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1046 | 705 | 46.303 | 49.781 | 0.126 | 0.127 | - | - | - |  |  |
| 15 | 2283 | 1297 | 76.718 | 82.201 | 0.218 | 0.182 | - | - | - |  |  |
| 30 | 2302 | 1169 | 81.902 | 87.861 | 0.170 | 0.141 | - | - | - |  |  |
| 40 | 2573 | 1324 | 77.915 | 83.594 | 0.159 | 0.158 | - | - | - |  |  |
| 50 | 2980 | 1726 | 73.397 | 82.295 | 0.134 | 0.138 | - | - | - |  |  |
| 60 | 3984 | 3868 | 57.838 | 64.813 | 0.192 | 0.254 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.037 | 0.030 | 0.047 | 0.036 | 0.029 | 0.048 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2193 | 1400 | 73.152 | 81.395 | 0.142 | 0.150 | - | - | - |  |  |
| intermediate | 6163 | 4647 | 70.914 | 76.455 | 0.445 | 0.459 | - | - | - |  |  |
| sparse | 1944 | 1610 | 64.530 | 65.659 | 0.173 | 0.183 | - | - | - |  |  |
| very_sparse | 4868 | 2432 | 69.875 | 73.940 | 0.240 | 0.208 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.002 | 0.001 | 0.005 | 0.005 | 0.003 | 0.011 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2406 | 1743 | 62.665 | 67.662 | 0.182 | 0.186 | - | - | - |  |  |
| q2 | 2515 | 1940 | 64.726 | 69.318 | 0.196 | 0.193 | - | - | - |  |  |
| q3 | 2954 | 1981 | 67.893 | 78.509 | 0.200 | 0.197 | - | - | - |  |  |
| q4 | 3143 | 2142 | 70.934 | 73.963 | 0.211 | 0.209 | - | - | - |  |  |
| q5 | 4150 | 2283 | 81.714 | 82.857 | 0.211 | 0.214 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.012 | 0.008 | 0.017 | 0.007 | 0.004 | 0.012 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2176 | 1473 | 69.425 | 76.230 | 0.114 | 0.123 | - | - | - |  |  |
| 1 | 5854 | 4212 | 69.228 | 71.478 | 0.388 | 0.389 | - | - | - |  |  |
| 2+ | 7138 | 4380 | 70.489 | 76.656 | 0.498 | 0.486 | - | - | - |  |  |
| unknown | 0 | 24 | - | - | - | - | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.001 | 0.003 | 0.001 | 0.012 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7397 | 5806 | 61.313 | 69.921 | 0.442 | 0.469 | - | - | - |  |  |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7771 | 4282 | 76.661 | 78.917 | 0.558 | 0.531 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.015 | 0.010 | 0.021 | 0.005 | 0.002 | 0.009 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 8218 | 5415 | 68.799 | 74.241 | 0.508 | 0.493 | - | - | - |  |  |
| car_passenger_carpool | 436 | 405 | 61.285 | 66.674 | 0.026 | 0.026 | - | - | - |  |  |
| car_passenger_household | 960 | 862 | 51.961 | 61.312 | 0.082 | 0.098 | - | - | - |  |  |
| cycle | 273 | 158 | 49.140 | 51.565 | 0.021 | 0.018 | - | - | - |  |  |
| multimodal | 1383 | 833 | 108.569 | 106.278 | 0.100 | 0.098 | - | - | - |  |  |
| other | 457 | 237 | 68.596 | 79.906 | 0.040 | 0.027 | - | - | - |  |  |
| train | 450 | 184 | 148.746 | 159.380 | 0.023 | 0.022 | - | - | - |  |  |
| urban_pt | 1105 | 744 | 93.669 | 96.694 | 0.064 | 0.086 | - | - | - |  |  |
| walking_only | 1886 | 1251 | 36.867 | 37.904 | 0.136 | 0.132 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.134 | 0.110 | 0.155 | 0.116 | 0.099 | 0.138 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 578 | 411 | 72.697 | 94.812 | 0.041 | 0.041 | - | - | - |  |  |
| car_driver\|intermediate | 3072 | 2324 | 68.999 | 74.516 | 0.214 | 0.212 | - | - | - |  |  |
| car_driver\|sparse | 1223 | 984 | 67.334 | 65.843 | 0.099 | 0.105 | - | - | - |  |  |
| car_driver\|very_sparse | 3345 | 1696 | 68.425 | 74.055 | 0.154 | 0.135 | - | - | - |  |  |
| car_passenger_carpool\|dense | 50 | 60 | 81.068 | 89.416 | 0.003 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|intermediate | 193 | 189 | 58.528 | 65.221 | 0.012 | 0.011 | - | - | - |  |  |
| car_passenger_carpool\|sparse | 58 | 68 | 58.529 | 59.899 | 0.006 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|very_sparse | 135 | 88 | 58.050 | 58.908 | 0.005 | 0.005 | - | - | - |  |  |
| car_passenger_household\|dense | 75 | 73 | 52.641 | 78.637 | 0.007 | 0.009 | - | - | - |  |  |
| car_passenger_household\|intermediate | 343 | 394 | 50.612 | 62.134 | 0.035 | 0.045 | - | - | - |  |  |
| car_passenger_household\|sparse | 144 | 167 | 47.489 | 52.981 | 0.016 | 0.021 | - | - | - |  |  |
| car_passenger_household\|very_sparse | 398 | 228 | 56.721 | 60.164 | 0.024 | 0.023 | - | - | - |  |  |
| cycle\|dense+intermediate+sparse+very_sparse | 273 | 158 | 49.140 | 51.565 | 0.021 | 0.018 | - | - | - |  |  |
| multimodal\|dense | 233 | 121 | 126.469 | 110.475 | 0.014 | 0.013 | - | - | - |  |  |
| multimodal\|intermediate | 590 | 403 | 107.967 | 109.740 | 0.046 | 0.051 | - | - | - |  |  |
| multimodal\|sparse | 147 | 109 | 90.785 | 96.750 | 0.015 | 0.014 | - | - | - |  |  |
| multimodal\|very_sparse | 413 | 200 | 110.436 | 101.825 | 0.025 | 0.021 | - | - | - |  |  |
| other\|dense+intermediate | 205 | 141 | 67.876 | 80.686 | 0.018 | 0.015 | - | - | - |  |  |
| other\|sparse+very_sparse | 252 | 96 | 69.198 | 78.905 | 0.022 | 0.012 | - | - | - |  |  |
| train\|dense+intermediate+sparse+very_sparse | 450 | 184 | 148.746 | 159.380 | 0.023 | 0.022 | - | - | - |  |  |
| urban_pt\|dense | 581 | 316 | 90.798 | 90.727 | 0.029 | 0.036 | - | - | - |  |  |
| urban_pt\|intermediate | 468 | 367 | 94.255 | 97.490 | 0.030 | 0.041 | - | - | - |  |  |
| urban_pt\|sparse+very_sparse | 56 | 61 | 107.425 | 117.382 | 0.005 | 0.009 | - | - | - |  |  |
| walking_only\|dense | 488 | 322 | 39.682 | 43.974 | 0.036 | 0.035 | - | - | - |  |  |
| walking_only\|intermediate | 915 | 654 | 36.941 | 38.307 | 0.069 | 0.066 | - | - | - |  |  |
| walking_only\|sparse | 223 | 177 | 36.752 | 34.142 | 0.020 | 0.022 | - | - | - |  |  |
| walking_only\|very_sparse | 260 | 98 | 27.544 | 21.742 | 0.011 | 0.010 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.137 | 0.116 | 0.162 | 0.127 | 0.114 | 0.150 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| cycle\|dense | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|intermediate | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|sparse | cycle\|dense+intermediate+sparse+very_sparse |
| cycle\|very_sparse | cycle\|dense+intermediate+sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|sparse+very_sparse |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 63 | 41 | 50.435 | - | 0.009 | - | - | - | - |  |  |
| car_driver\|employed | 5208 | 2967 | 73.959 | 78.850 | 0.339 | 0.314 | - | - | - |  |  |
| car_driver\|other_inactive | 583 | 282 | 63.228 | 69.362 | 0.035 | 0.026 | - | - | - |  |  |
| car_driver\|retired | 2062 | 1865 | 56.952 | 62.787 | 0.108 | 0.123 | - | - | - |  |  |
| car_driver\|unemployed | 302 | 256 | 62.435 | 75.467 | 0.017 | 0.024 | - | - | - |  |  |
| car_passenger_carpool\|children_6_17 | 28 | 24 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 130 | 72 | 63.166 | 93.197 | 0.009 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|other_inactive | 65 | 53 | 62.218 | 61.832 | 0.004 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|retired | 184 | 222 | 61.051 | 63.435 | 0.008 | 0.010 | - | - | - |  |  |
| car_passenger_carpool\|unemployed | 28 | 32 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 409 | 323 | 40.883 | 47.796 | 0.049 | 0.055 | - | - | - |  |  |
| car_passenger_household\|employed | 167 | 96 | 69.627 | 95.917 | 0.011 | 0.010 | - | - | - |  |  |
| car_passenger_household\|other_inactive | 114 | 84 | 79.429 | 68.126 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|retired | 243 | 329 | 59.112 | 71.587 | 0.014 | 0.022 | - | - | - |  |  |
| car_passenger_household\|unemployed | 27 | 30 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 43 | 17 | - | - | - | - | - | - | - |  |  |
| cycle\|employed | 121 | 77 | 65.478 | 54.271 | 0.008 | 0.009 | - | - | - |  |  |
| cycle\|other_inactive | 26 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 70 | 40 | 36.268 | - | 0.004 | - | - | - | - |  |  |
| cycle\|unemployed | 13 | 9 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 233 | 163 | 70.042 | 72.266 | 0.027 | 0.026 | - | - | - |  |  |
| multimodal\|employed | 735 | 394 | 125.773 | 123.940 | 0.050 | 0.046 | - | - | - |  |  |
| multimodal\|other_inactive | 130 | 65 | 111.150 | 119.343 | 0.009 | 0.009 | - | - | - |  |  |
| multimodal\|retired | 223 | 164 | 124.814 | 101.953 | 0.010 | 0.011 | - | - | - |  |  |
| multimodal\|unemployed | 62 | 47 | 108.862 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 182 | 48 | 68.537 | - | 0.020 | - | - | - | - |  |  |
| other\|employed | 189 | 96 | 71.506 | 85.427 | 0.014 | 0.013 | - | - | - |  |  |
| other\|other_inactive | 29 | 26 | - | - | - | - | - | - | - |  |  |
| other\|retired | 51 | 60 | 63.010 | 71.786 | 0.003 | 0.003 | - | - | - |  |  |
| other\|unemployed | 6 | 6 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 21 | 14 | - | - | - | - | - | - | - |  |  |
| train\|employed | 332 | 125 | 158.341 | 167.333 | 0.016 | 0.014 | - | - | - |  |  |
| train\|other_inactive | 44 | 19 | - | - | - | - | - | - | - |  |  |
| train\|retired | 41 | 19 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 12 | 6 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 94 | 122 | 97.320 | 87.480 | 0.012 | 0.022 | - | - | - |  |  |
| urban_pt\|employed | 541 | 272 | 92.916 | 98.489 | 0.027 | 0.031 | - | - | - |  |  |
| urban_pt\|other_inactive | 187 | 131 | 90.546 | 107.841 | 0.013 | 0.017 | - | - | - |  |  |
| urban_pt\|retired | 226 | 153 | 88.396 | 92.521 | 0.009 | 0.010 | - | - | - |  |  |
| urban_pt\|unemployed | 57 | 64 | 114.743 | 96.999 | 0.003 | 0.006 | - | - | - |  |  |
| walking_only\|children_6_17 | 251 | 191 | 34.871 | 32.003 | 0.039 | 0.040 | - | - | - |  |  |
| walking_only\|employed | 495 | 263 | 39.269 | 40.748 | 0.032 | 0.029 | - | - | - |  |  |
| walking_only\|other_inactive | 265 | 163 | 36.214 | 45.374 | 0.018 | 0.015 | - | - | - |  |  |
| walking_only\|retired | 743 | 537 | 35.379 | 37.306 | 0.037 | 0.040 | - | - | - |  |  |
| walking_only\|unemployed | 132 | 96 | 43.895 | 46.602 | 0.010 | 0.008 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.166 | 0.143 | 0.193 | 0.151 | 0.135 | 0.181 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.677 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 952 | 614 | 58.474 | 66.527 | 0.064 | 0.059 | - | - | - |  |  |
| car_driver\|q2 | 1290 | 998 | 63.529 | 65.423 | 0.092 | 0.093 | - | - | - |  |  |
| car_driver\|q3 | 1703 | 1153 | 65.972 | 78.483 | 0.111 | 0.107 | - | - | - |  |  |
| car_driver\|q4 | 1854 | 1295 | 71.748 | 75.948 | 0.115 | 0.116 | - | - | - |  |  |
| car_driver\|q5 | 2419 | 1355 | 77.802 | 79.484 | 0.125 | 0.118 | - | - | - |  |  |
| car_passenger_carpool\|q1 | 123 | 122 | 56.314 | 63.380 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|q2 | 95 | 99 | 54.113 | 52.436 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q3 | 87 | 81 | 68.819 | 72.848 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q4+q5 | 131 | 103 | 65.773 | 75.492 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|q1 | 143 | 143 | 54.733 | 59.045 | 0.013 | 0.020 | - | - | - |  |  |
| car_passenger_household\|q2 | 188 | 189 | 44.949 | 63.752 | 0.019 | 0.022 | - | - | - |  |  |
| car_passenger_household\|q3 | 206 | 176 | 54.257 | 59.253 | 0.017 | 0.020 | - | - | - |  |  |
| car_passenger_household\|q4 | 203 | 190 | 46.881 | 56.633 | 0.020 | 0.021 | - | - | - |  |  |
| car_passenger_household\|q5 | 220 | 164 | 63.329 | 69.956 | 0.014 | 0.015 | - | - | - |  |  |
| cycle\|q1+q2+q3 | 159 | 97 | 50.663 | 51.496 | 0.013 | 0.010 | - | - | - |  |  |
| cycle\|q4+q5 | 114 | 61 | 46.461 | 51.658 | 0.007 | 0.008 | - | - | - |  |  |
| multimodal\|q1 | 187 | 123 | 93.542 | 110.690 | 0.016 | 0.016 | - | - | - |  |  |
| multimodal\|q2 | 222 | 142 | 101.850 | 92.210 | 0.021 | 0.017 | - | - | - |  |  |
| multimodal\|q3 | 255 | 165 | 111.094 | 98.398 | 0.020 | 0.022 | - | - | - |  |  |
| multimodal\|q4 | 279 | 184 | 102.201 | 100.372 | 0.022 | 0.021 | - | - | - |  |  |
| multimodal\|q5 | 440 | 219 | 129.936 | 125.907 | 0.022 | 0.023 | - | - | - |  |  |
| other\|q1 | 76 | 51 | 70.778 | 69.499 | 0.009 | 0.006 | - | - | - |  |  |
| other\|q2 | 111 | 59 | 64.048 | 64.989 | 0.010 | 0.006 | - | - | - |  |  |
| other\|q3+q4+q5 | 270 | 127 | 69.734 | 89.397 | 0.021 | 0.015 | - | - | - |  |  |
| train\|q1+q2+q3+q4 | 255 | 119 | 149.681 | 168.653 | 0.014 | 0.015 | - | - | - |  |  |
| train\|q5 | 195 | 65 | 147.196 | 138.156 | 0.009 | 0.007 | - | - | - |  |  |
| urban_pt\|q1 | 253 | 249 | 100.158 | 91.738 | 0.019 | 0.028 | - | - | - |  |  |
| urban_pt\|q2 | 178 | 141 | 96.165 | 105.127 | 0.013 | 0.017 | - | - | - |  |  |
| urban_pt\|q3 | 183 | 115 | 92.467 | 100.286 | 0.009 | 0.014 | - | - | - |  |  |
| urban_pt\|q4 | 205 | 101 | 83.598 | 93.951 | 0.013 | 0.011 | - | - | - |  |  |
| urban_pt\|q5 | 286 | 138 | 92.112 | 95.009 | 0.010 | 0.016 | - | - | - |  |  |
| walking_only\|q1 | 560 | 388 | 39.656 | 39.798 | 0.046 | 0.044 | - | - | - |  |  |
| walking_only\|q2 | 338 | 244 | 33.402 | 39.073 | 0.028 | 0.025 | - | - | - |  |  |
| walking_only\|q3 | 333 | 186 | 34.389 | 32.687 | 0.022 | 0.018 | - | - | - |  |  |
| walking_only\|q4 | 303 | 220 | 38.433 | 35.349 | 0.021 | 0.023 | - | - | - |  |  |
| walking_only\|q5 | 352 | 213 | 36.366 | 39.588 | 0.019 | 0.022 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.145 | 0.124 | 0.169 | 0.127 | 0.112 | 0.154 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2+q3 |
| cycle\|q2 | cycle\|q1+q2+q3 |
| cycle\|q3 | cycle\|q1+q2+q3 |
| cycle\|q4 | cycle\|q4+q5 |
| cycle\|q5 | cycle\|q4+q5 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0 | 55 | 51 | 92.480 | 73.702 | 0.004 | 0.004 | - | - | - |  |  |
| car_driver\|1 | 3271 | 2473 | 67.543 | 70.933 | 0.192 | 0.192 | - | - | - |  |  |
| car_driver\|2+ | 4892 | 2885 | 69.250 | 76.437 | 0.312 | 0.297 | - | - | - |  |  |
| car_driver\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 193 | 207 | 53.636 | 65.458 | 0.010 | 0.009 | - | - | - |  |  |
| car_passenger_carpool\|1 | 156 | 136 | 74.081 | 68.761 | 0.008 | 0.009 | - | - | - |  |  |
| car_passenger_carpool\|2+ | 87 | 61 | 58.163 | 65.692 | 0.008 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 389 | 384 | 53.935 | 58.377 | 0.034 | 0.044 | - | - | - |  |  |
| car_passenger_household\|2+ | 571 | 476 | 50.549 | 63.775 | 0.048 | 0.054 | - | - | - |  |  |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0+1+2+ | 273 | 156 | 49.140 | 51.628 | 0.021 | 0.018 | - | - | - |  |  |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 150 | 80 | 116.798 | 135.123 | 0.008 | 0.008 | - | - | - |  |  |
| multimodal\|1 | 502 | 303 | 114.042 | 111.473 | 0.037 | 0.033 | - | - | - |  |  |
| multimodal\|2+ | 731 | 449 | 103.774 | 99.560 | 0.056 | 0.058 | - | - | - |  |  |
| multimodal\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| other\|0 | 79 | 59 | 54.647 | 75.423 | 0.005 | 0.004 | - | - | - |  |  |
| other\|1 | 162 | 88 | 71.631 | 71.562 | 0.015 | 0.011 | - | - | - |  |  |
| other\|2+ | 216 | 90 | 70.185 | 88.858 | 0.019 | 0.012 | - | - | - |  |  |
| train\|0 | 148 | 58 | 133.365 | 178.261 | 0.005 | 0.006 | - | - | - |  |  |
| train\|1 | 195 | 73 | 145.996 | 154.209 | 0.011 | 0.009 | - | - | - |  |  |
| train\|2+ | 107 | 50 | 165.780 | 137.384 | 0.007 | 0.007 | - | - | - |  |  |
| train\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 632 | 423 | 96.685 | 93.559 | 0.030 | 0.040 | - | - | - |  |  |
| urban_pt\|1 | 341 | 213 | 89.246 | 93.600 | 0.023 | 0.028 | - | - | - |  |  |
| urban_pt\|2+ | 132 | 102 | 94.943 | 108.467 | 0.010 | 0.017 | - | - | - |  |  |
| urban_pt\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 809 | 525 | 40.006 | 42.309 | 0.044 | 0.045 | - | - | - |  |  |
| walking_only\|1 | 753 | 498 | 34.802 | 39.219 | 0.060 | 0.058 | - | - | - |  |  |
| walking_only\|2+ | 324 | 225 | 36.446 | 28.291 | 0.032 | 0.029 | - | - | - |  |  |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.137 | 0.115 | 0.164 | 0.126 | 0.109 | 0.155 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| cycle\|0 | cycle\|0+1+2+ |
| cycle\|1 | cycle\|0+1+2+ |
| cycle\|2+ | cycle\|0+1+2+ |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 215 | 128 | 52.141 | 56.911 | 0.021 | 0.022 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q1 | 129 | 182 | 58.458 | 58.352 | 0.025 | 0.035 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q2 | 143 | 120 | 49.157 | 54.556 | 0.024 | 0.022 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q3 | 108 | 84 | 50.423 | 62.838 | 0.015 | 0.015 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q4 | 134 | 101 | 46.500 | 57.276 | 0.018 | 0.018 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q1 | 124 | 68 | 53.982 | 53.030 | 0.015 | 0.013 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q2 | 182 | 83 | 59.954 | 47.861 | 0.018 | 0.015 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q3 | 145 | 97 | 51.804 | 65.144 | 0.015 | 0.016 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q4 | 144 | 80 | 50.473 | 47.156 | 0.016 | 0.013 | - | - | - |  |  |
| employed\|dense\|q1 | 88 | 68 | 83.792 | 86.438 | 0.008 | 0.008 | - | - | - |  |  |
| employed\|dense\|q2 | 116 | 76 | 80.530 | 86.709 | 0.009 | 0.009 | - | - | - |  |  |
| employed\|dense\|q3 | 216 | 96 | 80.396 | 114.678 | 0.015 | 0.010 | - | - | - |  |  |
| employed\|dense\|q4 | 253 | 142 | 71.629 | 91.621 | 0.016 | 0.017 | - | - | - |  |  |
| employed\|dense\|q5 | 490 | 212 | 99.856 | 85.201 | 0.023 | 0.026 | - | - | - |  |  |
| employed\|intermediate\|q1 | 223 | 201 | 76.234 | 77.200 | 0.018 | 0.027 | - | - | - |  |  |
| employed\|intermediate\|q2 | 419 | 312 | 78.738 | 80.400 | 0.039 | 0.033 | - | - | - |  |  |
| employed\|intermediate\|q3 | 579 | 399 | 73.363 | 92.134 | 0.046 | 0.044 | - | - | - |  |  |
| employed\|intermediate\|q4 | 795 | 459 | 82.217 | 81.365 | 0.053 | 0.047 | - | - | - |  |  |
| employed\|intermediate\|q5 | 1182 | 619 | 93.211 | 95.444 | 0.063 | 0.064 | - | - | - |  |  |
| employed\|sparse+very_sparse\|q1 | 342 | 139 | 66.895 | 71.172 | 0.024 | 0.019 | - | - | - |  |  |
| employed\|sparse\|q2 | 157 | 99 | 57.323 | 58.571 | 0.015 | 0.013 | - | - | - |  |  |
| employed\|sparse\|q3 | 202 | 141 | 81.929 | 72.107 | 0.018 | 0.018 | - | - | - |  |  |
| employed\|sparse\|q4 | 259 | 180 | 74.556 | 79.060 | 0.025 | 0.022 | - | - | - |  |  |
| employed\|sparse\|q5 | 264 | 174 | 88.589 | 82.826 | 0.019 | 0.018 | - | - | - |  |  |
| employed\|very_sparse\|q2 | 468 | 210 | 68.496 | 83.340 | 0.028 | 0.022 | - | - | - |  |  |
| employed\|very_sparse\|q3 | 593 | 283 | 75.528 | 80.988 | 0.029 | 0.028 | - | - | - |  |  |
| employed\|very_sparse\|q4 | 691 | 286 | 80.970 | 85.381 | 0.036 | 0.024 | - | - | - |  |  |
| employed\|very_sparse\|q5 | 581 | 266 | 89.069 | 94.988 | 0.022 | 0.022 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 198 | 113 | 70.859 | 84.559 | 0.011 | 0.013 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 152 | 70 | 73.162 | 95.402 | 0.010 | 0.009 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 232 | 57 | 76.681 | 80.332 | 0.012 | 0.008 | - | - | - |  |  |
| other_inactive\|dense+intermediate\|q2 | 168 | 141 | 68.590 | 79.463 | 0.014 | 0.014 | - | - | - |  |  |
| other_inactive\|dense\|q1 | 183 | 110 | 67.736 | 74.349 | 0.010 | 0.010 | - | - | - |  |  |
| other_inactive\|intermediate\|q1 | 226 | 196 | 66.952 | 71.631 | 0.019 | 0.016 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q1 | 166 | 88 | 72.479 | 62.419 | 0.011 | 0.009 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q2 | 118 | 63 | 63.751 | 99.488 | 0.008 | 0.007 | - | - | - |  |  |
| retired\|dense+intermediate\|q1 | 285 | 211 | 53.075 | 61.483 | 0.019 | 0.013 | - | - | - |  |  |
| retired\|dense\|q2 | 55 | 68 | 70.002 | 59.376 | 0.003 | 0.004 | - | - | - |  |  |
| retired\|dense\|q3 | 85 | 72 | 66.008 | 78.397 | 0.004 | 0.005 | - | - | - |  |  |
| retired\|dense\|q4 | 85 | 93 | 49.227 | 65.513 | 0.005 | 0.007 | - | - | - |  |  |
| retired\|dense\|q5 | 187 | 123 | 69.795 | 77.853 | 0.009 | 0.010 | - | - | - |  |  |
| retired\|intermediate\|q2 | 216 | 304 | 53.047 | 66.549 | 0.014 | 0.019 | - | - | - |  |  |
| retired\|intermediate\|q3 | 318 | 299 | 58.642 | 55.625 | 0.021 | 0.020 | - | - | - |  |  |
| retired\|intermediate\|q4 | 270 | 347 | 65.928 | 67.697 | 0.014 | 0.024 | - | - | - |  |  |
| retired\|intermediate\|q5 | 531 | 392 | 65.470 | 72.867 | 0.024 | 0.024 | - | - | - |  |  |
| retired\|sparse\|q1 | 91 | 79 | 35.148 | 54.809 | 0.007 | 0.005 | - | - | - |  |  |
| retired\|sparse\|q2 | 95 | 158 | 43.476 | 48.273 | 0.007 | 0.014 | - | - | - |  |  |
| retired\|sparse\|q3 | 113 | 124 | 52.008 | 72.439 | 0.009 | 0.010 | - | - | - |  |  |
| retired\|sparse\|q4 | 98 | 137 | 50.367 | 47.521 | 0.006 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q5 | 123 | 122 | 60.234 | 63.417 | 0.008 | 0.009 | - | - | - |  |  |
| retired\|very_sparse\|q1 | 292 | 96 | 47.742 | 45.055 | 0.009 | 0.005 | - | - | - |  |  |
| retired\|very_sparse\|q2 | 248 | 207 | 59.764 | 53.560 | 0.010 | 0.011 | - | - | - |  |  |
| retired\|very_sparse\|q3 | 298 | 202 | 58.451 | 58.813 | 0.012 | 0.011 | - | - | - |  |  |
| retired\|very_sparse\|q4 | 185 | 195 | 62.876 | 63.704 | 0.006 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q5 | 268 | 160 | 71.365 | 78.983 | 0.008 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 130 | 97 | 75.164 | 81.422 | 0.008 | 0.011 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 99 | 71 | 69.485 | 104.420 | 0.006 | 0.007 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 153 | 77 | 78.609 | 75.617 | 0.008 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate\|q1 | 158 | 221 | 57.760 | 80.323 | 0.012 | 0.018 | - | - | - |  |  |
| unemployed\|sparse+very_sparse\|q1 | 99 | 80 | 71.731 | 67.286 | 0.005 | 0.007 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.050 | 0.047 | 0.066 | 0.050 | 0.049 | 0.075 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| retired\|dense\|q1 | retired\|dense+intermediate\|q1 |
| retired\|intermediate\|q1 | retired\|dense+intermediate\|q1 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.677 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: cell levels

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4454 | 3056 | 67.191 | 70.673 | 0.241 | 0.242 | - | - | - |  |  |
| couple_with_children | 5382 | 2911 | 71.852 | 76.801 | 0.490 | 0.449 | - | - | - |  |  |
| other | 354 | 208 | 64.290 | 80.719 | 0.036 | 0.033 | - | - | - |  |  |
| single_parent | 1140 | 803 | 68.821 | 73.751 | 0.086 | 0.110 | - | - | - |  |  |
| single_person | 3838 | 3111 | 69.696 | 74.306 | 0.147 | 0.166 | - | - | - |  |  |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: stability and explained variance

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 0.000 | 0.004 | 0.002 | 0.001 | 0.005 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed full-sample merges

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.696 | - | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person mode use and user-day minutes

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 3850 | 2543 | 0.222 | 0.230 | 30.454 | 31.495 |
| bike | 428 | 268 | 0.026 | 0.026 | 39.276 | 39.143 |
| car_driver | 9046 | 5899 | 0.466 | 0.455 | 65.352 | 69.726 |
| car_passenger | 2287 | 1808 | 0.148 | 0.157 | 44.935 | 51.230 |
| urban_pt | 1507 | 983 | 0.076 | 0.098 | 74.082 | 78.144 |
| train | 681 | 288 | 0.029 | 0.030 | 144.056 | 139.324 |
| other | 687 | 378 | 0.050 | 0.038 | 64.533 | 72.436 |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode model

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 57.920 | 62.624 | - | - | - | - | - | - | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode deciles

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15168, 2019 10089 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

## All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`)

### Grouping summary

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| day_mode_group_x_income | 0.131 | 0.130 | 0.102 | 0.000 | 1.079 | 1.055 | 1.102 | 0.048 | 35 |
| day_mode_group_x_category | 0.150 | 0.162 | 0.104 | 0.115 | 1.081 | 1.057 | 1.102 | 0.050 | 45 |
| day_mode_group_x_vehicles | 0.124 | 0.136 | - | 0.091 | 1.083 | 1.059 | 1.107 | 0.049 | 32 |
| day_mode_group | 0.121 | 0.120 | 0.085 | 0.172 | 1.083 | 1.059 | 1.107 | 0.049 | 9 |
| day_mode_group_x_density | 0.125 | 0.124 | 0.092 | 0.035 | 1.083 | 1.059 | 1.106 | 0.049 | 27 |
| density | 0.003 | 0.004 | 0.085 | 0.000 | 1.089 | 1.061 | 1.114 | 0.053 | 4 |
| vehicles | 0.000 | 0.005 | - | 0.390 | 1.090 | 1.063 | 1.112 | 0.053 | 4 |
| income | 0.007 | 0.006 | 0.086 | 0.000 | 1.090 | 1.062 | 1.110 | 0.053 | 5 |
| none | 0.000 | 0.000 | 0.086 | 0.000 | 1.090 | 1.063 | 1.113 | 0.053 | 1 |
| household_type | 0.000 | 0.001 | 0.087 | 0.245 | 1.091 | 1.065 | 1.113 | 0.053 | 5 |
| category_x_density_x_income | 0.039 | 0.051 | 0.112 | 0.000 | 1.091 | 1.063 | 1.114 | 0.054 | 61 |
| day_purpose | 0.011 | 0.009 | - | 0.000 | 1.093 | 1.066 | 1.115 | 0.055 | 3 |
| category | 0.024 | 0.037 | 0.089 | 0.000 | 1.097 | 1.070 | 1.119 | 0.057 | 5 |
| age_band | 0.030 | 0.045 | 0.094 | 0.127 | 1.103 | 1.077 | 1.125 | 0.061 | 6 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 15168 | 10071 | 68.074 | 74.196 | 1.000 | 1.000 | 1.090 | 1.063 | 1.113 | inconclusive | equivalent |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.086 | 0.000 | 1.000 | 0.086 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.074 | 1.090 | 1.063 | 1.113 | 0.000 | 0.000 | 0.053 | 0.041 | 0.076 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### none: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.128 | 19.345 |
| 2 | 27.949 | 29.884 |
| 3 | 35.688 | 39.895 |
| 4 | 44.705 | 49.471 |
| 5 | 57.660 | 59.620 |
| 6 | 65.981 | 74.192 |
| 7 | 79.960 | 89.454 |
| 8 | 99.944 | 109.655 |
| 9 | 129.931 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1326 | 945 | 53.695 | 56.144 | 0.167 | 0.170 | 1.046 | 0.956 | 1.114 | inconclusive | equivalent |
| employed | 7741 | 4265 | 75.042 | 83.489 | 0.494 | 0.462 | 1.113 | 1.082 | 1.148 | inconclusive | equivalent |
| other_inactive | 1452 | 846 | 70.238 | 79.524 | 0.094 | 0.087 | 1.132 | 1.047 | 1.226 | inconclusive | inconclusive |
| retired | 4006 | 3460 | 62.078 | 65.572 | 0.204 | 0.229 | 1.056 | 1.018 | 1.101 | inconclusive | equivalent |
| unemployed | 642 | 545 | 67.675 | 79.602 | 0.040 | 0.052 | 1.176 | 1.047 | 1.315 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.024 | 0.017 | 0.032 | 0.037 | 0.029 | 0.050 | 0.089 | 0.000 | 0.863 | 0.162 | 0.000 | 0.001 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 67.643 | 1.097 | 1.070 | 1.119 | -0.433 | 0.000 | 0.057 | 0.044 | 0.079 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.095 | 19.344 |
| 2 | 27.122 | 29.884 |
| 3 | 34.884 | 39.895 |
| 4 | 44.551 | 49.470 |
| 5 | 56.202 | 59.619 |
| 6 | 64.977 | 74.190 |
| 7 | 79.829 | 89.451 |
| 8 | 99.916 | 109.655 |
| 9 | 129.718 | 146.478 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1049 | 708 | 47.696 | 48.422 | 0.126 | 0.127 | 1.015 | 0.926 | 1.094 | equivalent | equivalent |
| 15 | 2242 | 1282 | 75.003 | 82.496 | 0.214 | 0.182 | 1.100 | 1.041 | 1.159 | inconclusive | inconclusive |
| 30 | 2269 | 1152 | 74.243 | 83.393 | 0.168 | 0.138 | 1.123 | 1.069 | 1.171 | inconclusive | inconclusive |
| 40 | 2524 | 1294 | 73.445 | 83.274 | 0.156 | 0.155 | 1.134 | 1.081 | 1.190 | inconclusive | inconclusive |
| 50 | 2945 | 1691 | 71.633 | 80.727 | 0.134 | 0.137 | 1.127 | 1.064 | 1.194 | inconclusive | inconclusive |
| 60 | 4139 | 3944 | 61.835 | 67.328 | 0.202 | 0.261 | 1.089 | 1.048 | 1.135 | inconclusive | equivalent |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.030 | 0.022 | 0.039 | 0.045 | 0.037 | 0.057 | 0.094 | 0.127 | 0.358 | 0.126 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.278 | 1.103 | 1.077 | 1.125 | -0.796 | 0.000 | 0.061 | 0.049 | 0.082 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### age_band: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.065 | 19.345 |
| 2 | 25.936 | 29.884 |
| 3 | 34.623 | 39.895 |
| 4 | 44.381 | 49.471 |
| 5 | 54.924 | 59.620 |
| 6 | 64.946 | 74.192 |
| 7 | 79.707 | 89.454 |
| 8 | 99.898 | 109.655 |
| 9 | 129.721 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2180 | 1395 | 71.636 | 77.666 | 0.141 | 0.149 | 1.084 | 1.026 | 1.147 | inconclusive | equivalent |
| intermediate | 6138 | 4638 | 69.932 | 76.334 | 0.441 | 0.458 | 1.092 | 1.054 | 1.128 | inconclusive | equivalent |
| sparse | 1960 | 1617 | 62.719 | 67.283 | 0.175 | 0.186 | 1.073 | 0.990 | 1.133 | inconclusive | equivalent |
| very_sparse | 4890 | 2421 | 66.483 | 73.180 | 0.242 | 0.208 | 1.101 | 1.058 | 1.153 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.003 | 0.001 | 0.008 | 0.004 | 0.002 | 0.009 | 0.085 | 0.000 | 0.775 | 0.096 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.129 | 1.089 | 1.061 | 1.114 | 0.055 | 0.000 | 0.053 | 0.041 | 0.076 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### density: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.129 | 19.345 |
| 2 | 27.936 | 29.884 |
| 3 | 35.728 | 39.895 |
| 4 | 44.711 | 49.471 |
| 5 | 57.678 | 59.620 |
| 6 | 66.117 | 74.192 |
| 7 | 79.977 | 89.454 |
| 8 | 99.948 | 109.655 |
| 9 | 129.946 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2481 | 1781 | 63.963 | 69.423 | 0.189 | 0.190 | 1.085 | 1.024 | 1.136 | inconclusive | equivalent |
| q2 | 2558 | 1973 | 63.741 | 70.188 | 0.197 | 0.196 | 1.101 | 1.044 | 1.162 | inconclusive | inconclusive |
| q3 | 2967 | 1980 | 66.989 | 75.854 | 0.200 | 0.198 | 1.132 | 1.075 | 1.179 | inconclusive | inconclusive |
| q4 | 3114 | 2120 | 69.147 | 73.747 | 0.209 | 0.206 | 1.067 | 1.020 | 1.118 | inconclusive | equivalent |
| q5 | 4048 | 2217 | 75.962 | 81.178 | 0.206 | 0.209 | 1.069 | 1.025 | 1.115 | inconclusive | equivalent |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.007 | 0.004 | 0.013 | 0.006 | 0.003 | 0.011 | 0.086 | 0.000 | 0.604 | 0.124 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.097 | 1.090 | 1.062 | 1.110 | 0.023 | 0.000 | 0.053 | 0.040 | 0.076 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### income: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.128 | 19.345 |
| 2 | 27.951 | 29.884 |
| 3 | 35.718 | 39.895 |
| 4 | 44.711 | 49.471 |
| 5 | 57.721 | 59.620 |
| 6 | 66.050 | 74.192 |
| 7 | 79.968 | 89.454 |
| 8 | 99.946 | 109.655 |
| 9 | 129.946 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2235 | 1524 | 70.105 | 78.895 | 0.118 | 0.127 | 1.125 | 1.045 | 1.207 | inconclusive | inconclusive |
| 1 | 5847 | 4216 | 68.118 | 70.694 | 0.388 | 0.391 | 1.038 | 1.001 | 1.074 | equivalent | equivalent |
| 2+ | 7086 | 4307 | 67.553 | 75.547 | 0.493 | 0.480 | 1.118 | 1.078 | 1.149 | inconclusive | equivalent |
| unknown | 0 | 24 | - | - | - | - | - | - | - |  |  |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.002 | 0.005 | 0.001 | 0.017 | - | 0.390 | 0.876 | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.100 | 1.090 | 1.063 | 1.112 | 0.026 | 0.002 | 0.053 | 0.041 | 0.075 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### vehicles: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.123 | 19.345 |
| 2 | 27.836 | 29.884 |
| 3 | 35.528 | 39.895 |
| 4 | 44.699 | 49.471 |
| 5 | 57.654 | 59.620 |
| 6 | 66.016 | 74.192 |
| 7 | 79.973 | 89.454 |
| 8 | 99.948 | 109.655 |
| 9 | 129.966 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7610 | 5868 | 62.076 | 68.721 | 0.458 | 0.475 | 1.107 | 1.067 | 1.150 | inconclusive | equivalent |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7558 | 4202 | 73.143 | 79.161 | 0.542 | 0.524 | 1.082 | 1.051 | 1.113 | inconclusive | equivalent |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.011 | 0.007 | 0.015 | 0.009 | 0.005 | 0.014 | - | 0.000 | 1.000 | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.880 | 1.093 | 1.066 | 1.115 | -0.194 | 0.000 | 0.055 | 0.042 | 0.078 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_purpose: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.110 | 19.345 |
| 2 | 27.511 | 29.884 |
| 3 | 34.979 | 39.895 |
| 4 | 44.626 | 49.471 |
| 5 | 56.976 | 59.620 |
| 6 | 65.039 | 74.192 |
| 7 | 79.907 | 89.454 |
| 8 | 99.933 | 109.655 |
| 9 | 129.868 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 8099 | 5321 | 67.057 | 73.578 | 0.503 | 0.486 | 1.097 | 1.067 | 1.134 | inconclusive | equivalent |
| car_passenger_carpool | 404 | 384 | 56.419 | 62.891 | 0.024 | 0.024 | 1.115 | 0.978 | 1.253 | inconclusive | inconclusive |
| car_passenger_household | 931 | 822 | 51.652 | 57.301 | 0.080 | 0.094 | 1.109 | 1.021 | 1.201 | inconclusive | inconclusive |
| cycle | 310 | 183 | 55.855 | 70.918 | 0.025 | 0.021 | 1.270 | 1.064 | 1.537 | inconclusive | inconclusive |
| multimodal | 1373 | 820 | 100.347 | 104.252 | 0.099 | 0.097 | 1.039 | 0.978 | 1.098 | equivalent | equivalent |
| other | 434 | 223 | 66.200 | 75.853 | 0.038 | 0.025 | 1.146 | 1.015 | 1.293 | inconclusive | inconclusive |
| train | 412 | 158 | 128.070 | 146.062 | 0.019 | 0.020 | 1.140 | 1.016 | 1.263 | inconclusive | inconclusive |
| urban_pt | 1095 | 726 | 96.054 | 96.143 | 0.063 | 0.084 | 1.001 | 0.939 | 1.067 | equivalent | equivalent |
| walking_only | 2110 | 1434 | 43.466 | 46.942 | 0.148 | 0.148 | 1.080 | 1.014 | 1.150 | inconclusive | equivalent |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.121 | 0.098 | 0.148 | 0.120 | 0.106 | 0.140 | 0.085 | 0.172 | 0.815 | 0.239 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.513 | 1.083 | 1.059 | 1.107 | 0.439 | 0.000 | 0.049 | 0.039 | 0.071 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.138 | 19.345 |
| 2 | 28.335 | 29.884 |
| 3 | 36.638 | 39.895 |
| 4 | 44.833 | 49.471 |
| 5 | 58.429 | 59.620 |
| 6 | 67.039 | 74.192 |
| 7 | 81.455 | 89.454 |
| 8 | 99.978 | 109.655 |
| 9 | 131.924 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 574 | 403 | 71.808 | 78.769 | 0.041 | 0.039 | 1.097 | 1.009 | 1.192 | inconclusive | inconclusive |
| car_driver\|intermediate | 3029 | 2288 | 68.190 | 74.638 | 0.211 | 0.210 | 1.095 | 1.047 | 1.148 | inconclusive | equivalent |
| car_driver\|sparse | 1205 | 973 | 64.329 | 69.293 | 0.098 | 0.105 | 1.077 | 0.984 | 1.164 | inconclusive | inconclusive |
| car_driver\|very_sparse | 3291 | 1657 | 65.960 | 73.739 | 0.152 | 0.133 | 1.118 | 1.058 | 1.178 | inconclusive | inconclusive |
| car_passenger_carpool\|dense+intermediate | 223 | 238 | 58.114 | 64.081 | 0.014 | 0.013 | 1.103 | 0.958 | 1.273 | inconclusive | inconclusive |
| car_passenger_carpool\|sparse | 57 | 62 | 57.884 | 57.257 | 0.006 | 0.005 | 0.989 | 0.676 | 1.311 | inconclusive | inconclusive |
| car_passenger_carpool\|very_sparse | 124 | 84 | 49.402 | 65.977 | 0.005 | 0.005 | 1.336 | 1.079 | 1.707 | inconclusive | inconclusive |
| car_passenger_household\|dense | 76 | 66 | 53.011 | 67.991 | 0.007 | 0.008 | 1.283 | 1.007 | 1.577 | inconclusive | inconclusive |
| car_passenger_household\|intermediate | 334 | 378 | 51.210 | 57.458 | 0.034 | 0.043 | 1.122 | 0.968 | 1.257 | inconclusive | inconclusive |
| car_passenger_household\|sparse | 138 | 163 | 45.026 | 54.441 | 0.015 | 0.020 | 1.209 | 0.988 | 1.576 | inconclusive | inconclusive |
| car_passenger_household\|very_sparse | 383 | 215 | 56.211 | 55.724 | 0.024 | 0.022 | 0.991 | 0.877 | 1.113 | inconclusive | equivalent |
| cycle\|dense+intermediate | 174 | 128 | 57.590 | 69.940 | 0.015 | 0.015 | 1.214 | 0.998 | 1.467 | inconclusive | inconclusive |
| cycle\|sparse+very_sparse | 136 | 55 | 52.990 | 73.099 | 0.009 | 0.007 | 1.379 | 0.841 | 2.035 | inconclusive | inconclusive |
| multimodal\|dense | 217 | 118 | 115.789 | 106.883 | 0.013 | 0.012 | 0.923 | 0.796 | 1.040 | inconclusive | inconclusive |
| multimodal\|intermediate | 580 | 393 | 102.086 | 108.481 | 0.045 | 0.050 | 1.063 | 0.963 | 1.149 | inconclusive | equivalent |
| multimodal\|sparse | 149 | 108 | 89.678 | 99.337 | 0.016 | 0.014 | 1.108 | 0.931 | 1.292 | inconclusive | inconclusive |
| multimodal\|very_sparse | 427 | 201 | 95.945 | 95.956 | 0.025 | 0.021 | 1.000 | 0.872 | 1.124 | inconclusive | equivalent |
| other\|dense+intermediate | 193 | 131 | 62.209 | 74.528 | 0.017 | 0.014 | 1.198 | 0.989 | 1.423 | inconclusive | inconclusive |
| other\|sparse+very_sparse | 241 | 92 | 69.581 | 77.436 | 0.021 | 0.011 | 1.113 | 0.954 | 1.313 | inconclusive | inconclusive |
| train\|dense+intermediate+sparse+very_sparse | 412 | 158 | 128.070 | 146.062 | 0.019 | 0.020 | 1.140 | 1.016 | 1.263 | inconclusive | inconclusive |
| urban_pt\|dense | 581 | 312 | 93.568 | 94.171 | 0.029 | 0.036 | 1.006 | 0.921 | 1.103 | inconclusive | equivalent |
| urban_pt\|intermediate | 463 | 358 | 99.241 | 98.417 | 0.030 | 0.039 | 0.992 | 0.908 | 1.087 | equivalent | equivalent |
| urban_pt\|sparse+very_sparse | 51 | 56 | 90.316 | 93.956 | 0.004 | 0.008 | 1.040 | 0.849 | 1.269 | inconclusive | inconclusive |
| walking_only\|dense | 515 | 354 | 44.020 | 53.800 | 0.037 | 0.038 | 1.222 | 1.066 | 1.374 | inconclusive | inconclusive |
| walking_only\|intermediate | 977 | 727 | 43.179 | 46.205 | 0.071 | 0.071 | 1.070 | 0.987 | 1.167 | inconclusive | inconclusive |
| walking_only\|sparse | 262 | 208 | 44.407 | 42.574 | 0.024 | 0.025 | 0.959 | 0.780 | 1.091 | inconclusive | inconclusive |
| walking_only\|very_sparse | 356 | 145 | 42.022 | 39.312 | 0.016 | 0.013 | 0.936 | 0.784 | 1.160 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.125 | 0.103 | 0.157 | 0.124 | 0.112 | 0.148 | 0.092 | 0.035 | 0.371 | 0.322 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|dense | car_passenger_carpool\|dense+intermediate |
| car_passenger_carpool\|intermediate | car_passenger_carpool\|dense+intermediate |
| cycle\|dense | cycle\|dense+intermediate |
| cycle\|intermediate | cycle\|dense+intermediate |
| cycle\|sparse | cycle\|sparse+very_sparse |
| cycle\|very_sparse | cycle\|sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|sparse+very_sparse |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.482 | 1.083 | 1.059 | 1.106 | 0.408 | 0.000 | 0.049 | 0.040 | 0.070 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_density: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.136 | 19.345 |
| 2 | 28.182 | 29.884 |
| 3 | 36.320 | 39.895 |
| 4 | 44.807 | 49.471 |
| 5 | 58.271 | 59.620 |
| 6 | 66.928 | 74.192 |
| 7 | 81.341 | 89.454 |
| 8 | 99.975 | 109.655 |
| 9 | 131.949 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 61 | 38 | 57.931 | - | 0.008 | - | - | - | - |  |  |
| car_driver\|employed | 5105 | 2909 | 70.331 | 79.106 | 0.333 | 0.309 | 1.125 | 1.090 | 1.170 | inconclusive | inconclusive |
| car_driver\|other_inactive | 582 | 279 | 60.789 | 67.974 | 0.035 | 0.026 | 1.118 | 0.993 | 1.266 | inconclusive | inconclusive |
| car_driver\|retired | 2053 | 1839 | 60.080 | 62.117 | 0.109 | 0.121 | 1.034 | 0.976 | 1.089 | equivalent | equivalent |
| car_driver\|unemployed | 298 | 252 | 65.193 | 70.855 | 0.017 | 0.024 | 1.087 | 0.954 | 1.237 | inconclusive | inconclusive |
| car_passenger_carpool\|children_6_17 | 24 | 23 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 118 | 64 | 56.264 | 73.124 | 0.009 | 0.005 | 1.300 | 1.041 | 1.575 | inconclusive | inconclusive |
| car_passenger_carpool\|other_inactive | 61 | 52 | 62.174 | 64.133 | 0.003 | 0.004 | 1.032 | 0.764 | 1.390 | inconclusive | inconclusive |
| car_passenger_carpool\|retired | 174 | 213 | 57.635 | 64.759 | 0.008 | 0.009 | 1.124 | 0.915 | 1.330 | inconclusive | inconclusive |
| car_passenger_carpool\|unemployed | 26 | 30 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 395 | 318 | 40.795 | 48.240 | 0.047 | 0.054 | 1.182 | 1.048 | 1.303 | inconclusive | inconclusive |
| car_passenger_household\|employed | 153 | 84 | 61.488 | 71.446 | 0.010 | 0.008 | 1.162 | 0.952 | 1.441 | inconclusive | inconclusive |
| car_passenger_household\|other_inactive | 113 | 81 | 78.719 | 78.110 | 0.007 | 0.008 | 0.992 | 0.717 | 1.327 | inconclusive | inconclusive |
| car_passenger_household\|retired | 244 | 316 | 65.919 | 68.137 | 0.015 | 0.021 | 1.034 | 0.916 | 1.170 | inconclusive | inconclusive |
| car_passenger_household\|unemployed | 26 | 23 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 52 | 22 | 40.483 | - | 0.008 | - | - | - | - |  |  |
| cycle\|employed | 127 | 82 | 68.469 | 61.040 | 0.008 | 0.010 | 0.891 | 0.731 | 1.094 | inconclusive | inconclusive |
| cycle\|other_inactive | 25 | 16 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 93 | 51 | 58.000 | 78.333 | 0.005 | 0.004 | 1.351 | 0.888 | 1.896 | inconclusive | inconclusive |
| cycle\|unemployed | 13 | 12 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 247 | 163 | 69.413 | 71.367 | 0.029 | 0.026 | 1.028 | 0.880 | 1.160 | inconclusive | inconclusive |
| multimodal\|employed | 699 | 382 | 114.027 | 118.569 | 0.047 | 0.044 | 1.040 | 0.963 | 1.125 | inconclusive | equivalent |
| multimodal\|other_inactive | 130 | 65 | 110.512 | 123.600 | 0.009 | 0.009 | 1.118 | 0.931 | 1.309 | inconclusive | inconclusive |
| multimodal\|retired | 239 | 165 | 115.013 | 106.426 | 0.010 | 0.011 | 0.925 | 0.819 | 1.024 | inconclusive | inconclusive |
| multimodal\|unemployed | 58 | 45 | 104.776 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 178 | 47 | 68.757 | - | 0.019 | - | - | - | - |  |  |
| other\|employed | 173 | 88 | 65.888 | 83.398 | 0.013 | 0.012 | 1.266 | 1.016 | 1.542 | inconclusive | inconclusive |
| other\|other_inactive | 28 | 24 | - | - | - | - | - | - | - |  |  |
| other\|retired | 49 | 58 | - | 70.966 | - | 0.003 | - | - | - |  |  |
| other\|unemployed | 6 | 6 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 19 | 14 | - | - | - | - | - | - | - |  |  |
| train\|employed | 304 | 108 | 131.366 | 155.310 | 0.013 | 0.012 | 1.182 | 1.068 | 1.314 | inconclusive | inconclusive |
| train\|other_inactive | 40 | 16 | - | - | - | - | - | - | - |  |  |
| train\|retired | 39 | 13 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 10 | 6 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 94 | 117 | 98.018 | 88.885 | 0.012 | 0.021 | 0.907 | 0.721 | 1.109 | inconclusive | inconclusive |
| urban_pt\|employed | 537 | 265 | 94.603 | 97.838 | 0.028 | 0.030 | 1.034 | 0.962 | 1.113 | inconclusive | equivalent |
| urban_pt\|other_inactive | 188 | 128 | 94.445 | 100.128 | 0.013 | 0.016 | 1.060 | 0.936 | 1.189 | inconclusive | inconclusive |
| urban_pt\|retired | 219 | 150 | 93.074 | 96.669 | 0.008 | 0.010 | 1.039 | 0.914 | 1.157 | inconclusive | inconclusive |
| urban_pt\|unemployed | 57 | 64 | 117.406 | 101.306 | 0.003 | 0.006 | 0.863 | 0.657 | 1.175 | inconclusive | inconclusive |
| walking_only\|children_6_17 | 256 | 203 | 37.373 | 33.607 | 0.038 | 0.043 | 0.899 | 0.783 | 1.062 | inconclusive | inconclusive |
| walking_only\|employed | 525 | 283 | 43.230 | 46.620 | 0.033 | 0.031 | 1.078 | 0.960 | 1.198 | inconclusive | inconclusive |
| walking_only\|other_inactive | 285 | 185 | 43.980 | 54.693 | 0.019 | 0.017 | 1.244 | 1.070 | 1.441 | inconclusive | inconclusive |
| walking_only\|retired | 896 | 655 | 48.328 | 53.841 | 0.046 | 0.049 | 1.114 | 1.011 | 1.227 | inconclusive | inconclusive |
| walking_only\|unemployed | 148 | 107 | 44.328 | 58.799 | 0.012 | 0.009 | 1.326 | 1.005 | 1.753 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.150 | 0.125 | 0.186 | 0.162 | 0.149 | 0.193 | 0.104 | 0.115 | 0.203 | 0.752 | 0.000 | 0.001 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 68.608 | 1.081 | 1.057 | 1.102 | 0.532 | 0.000 | 0.050 | 0.040 | 0.071 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_category: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.138 | 19.344 |
| 2 | 28.311 | 29.884 |
| 3 | 36.123 | 39.895 |
| 4 | 44.790 | 49.470 |
| 5 | 58.184 | 59.619 |
| 6 | 66.717 | 74.190 |
| 7 | 81.374 | 89.451 |
| 8 | 99.983 | 109.655 |
| 9 | 132.574 | 146.478 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 950 | 603 | 58.354 | 67.800 | 0.065 | 0.058 | 1.162 | 1.060 | 1.274 | inconclusive | inconclusive |
| car_driver\|q2 | 1284 | 992 | 62.379 | 66.788 | 0.091 | 0.092 | 1.071 | 0.997 | 1.143 | inconclusive | equivalent |
| car_driver\|q3 | 1692 | 1132 | 65.618 | 71.615 | 0.111 | 0.105 | 1.091 | 1.009 | 1.156 | inconclusive | inconclusive |
| car_driver\|q4 | 1810 | 1279 | 69.689 | 76.332 | 0.113 | 0.115 | 1.095 | 1.037 | 1.159 | inconclusive | inconclusive |
| car_driver\|q5 | 2363 | 1315 | 73.993 | 80.947 | 0.123 | 0.116 | 1.094 | 1.036 | 1.154 | inconclusive | inconclusive |
| car_passenger_carpool\|q1 | 116 | 118 | 55.534 | 61.913 | 0.006 | 0.008 | 1.115 | 0.923 | 1.339 | inconclusive | inconclusive |
| car_passenger_carpool\|q2 | 87 | 100 | 46.561 | 55.047 | 0.006 | 0.005 | 1.182 | 0.951 | 1.410 | inconclusive | inconclusive |
| car_passenger_carpool\|q3 | 78 | 69 | 57.024 | 59.518 | 0.005 | 0.004 | 1.044 | 0.734 | 1.506 | inconclusive | inconclusive |
| car_passenger_carpool\|q4+q5 | 123 | 97 | 64.489 | 71.599 | 0.007 | 0.007 | 1.110 | 0.901 | 1.376 | inconclusive | inconclusive |
| car_passenger_household\|q1 | 143 | 139 | 62.828 | 51.583 | 0.013 | 0.019 | 0.821 | 0.654 | 0.975 | inconclusive | inconclusive |
| car_passenger_household\|q2 | 192 | 187 | 45.217 | 61.075 | 0.019 | 0.022 | 1.351 | 1.106 | 1.653 | different | inconclusive |
| car_passenger_household\|q3 | 197 | 171 | 55.016 | 60.737 | 0.017 | 0.019 | 1.104 | 0.927 | 1.311 | inconclusive | inconclusive |
| car_passenger_household\|q4 | 195 | 179 | 46.093 | 52.854 | 0.019 | 0.020 | 1.147 | 0.967 | 1.339 | inconclusive | inconclusive |
| car_passenger_household\|q5 | 204 | 146 | 53.514 | 60.756 | 0.012 | 0.014 | 1.135 | 0.963 | 1.335 | inconclusive | inconclusive |
| cycle\|q1+q2 | 127 | 77 | 58.387 | 80.805 | 0.010 | 0.010 | 1.384 | 1.018 | 1.939 | inconclusive | inconclusive |
| cycle\|q3+q4+q5 | 183 | 106 | 53.980 | 63.008 | 0.014 | 0.012 | 1.167 | 0.986 | 1.417 | inconclusive | inconclusive |
| multimodal\|q1 | 197 | 119 | 88.288 | 108.482 | 0.017 | 0.015 | 1.229 | 1.068 | 1.383 | inconclusive | inconclusive |
| multimodal\|q2 | 228 | 143 | 98.969 | 89.762 | 0.021 | 0.017 | 0.907 | 0.796 | 1.016 | inconclusive | inconclusive |
| multimodal\|q3 | 248 | 170 | 103.763 | 105.234 | 0.019 | 0.022 | 1.014 | 0.873 | 1.168 | inconclusive | inconclusive |
| multimodal\|q4 | 282 | 178 | 100.848 | 102.338 | 0.022 | 0.021 | 1.015 | 0.847 | 1.164 | inconclusive | inconclusive |
| multimodal\|q5 | 418 | 210 | 108.008 | 113.022 | 0.020 | 0.023 | 1.046 | 0.952 | 1.164 | inconclusive | inconclusive |
| other\|q1+q2 | 180 | 106 | 67.693 | 71.409 | 0.018 | 0.011 | 1.055 | 0.889 | 1.252 | inconclusive | inconclusive |
| other\|q3+q4+q5 | 254 | 117 | 64.848 | 79.456 | 0.020 | 0.014 | 1.225 | 1.066 | 1.440 | inconclusive | inconclusive |
| train\|q1+q2+q3+q4 | 236 | 105 | 127.158 | 155.086 | 0.012 | 0.014 | 1.220 | 1.076 | 1.378 | inconclusive | inconclusive |
| train\|q5 | 176 | 53 | 129.622 | 123.854 | 0.007 | 0.006 | 0.956 | 0.850 | 1.077 | inconclusive | inconclusive |
| urban_pt\|q1 | 252 | 250 | 103.077 | 95.563 | 0.018 | 0.028 | 0.927 | 0.800 | 1.068 | inconclusive | inconclusive |
| urban_pt\|q2 | 176 | 135 | 98.735 | 95.974 | 0.013 | 0.016 | 0.972 | 0.852 | 1.110 | inconclusive | equivalent |
| urban_pt\|q3 | 183 | 110 | 92.982 | 99.584 | 0.009 | 0.014 | 1.071 | 0.954 | 1.199 | inconclusive | inconclusive |
| urban_pt\|q4 | 202 | 99 | 81.753 | 95.377 | 0.012 | 0.011 | 1.167 | 1.036 | 1.321 | inconclusive | inconclusive |
| urban_pt\|q5 | 282 | 132 | 100.169 | 94.820 | 0.010 | 0.015 | 0.947 | 0.847 | 1.041 | inconclusive | inconclusive |
| walking_only\|q1 | 634 | 444 | 46.435 | 47.347 | 0.052 | 0.049 | 1.020 | 0.903 | 1.161 | inconclusive | inconclusive |
| walking_only\|q2 | 387 | 289 | 39.946 | 48.896 | 0.031 | 0.030 | 1.224 | 1.091 | 1.417 | inconclusive | inconclusive |
| walking_only\|q3 | 377 | 224 | 42.395 | 50.591 | 0.024 | 0.021 | 1.193 | 1.020 | 1.387 | inconclusive | inconclusive |
| walking_only\|q4 | 335 | 242 | 42.879 | 41.293 | 0.021 | 0.025 | 0.963 | 0.817 | 1.109 | inconclusive | inconclusive |
| walking_only\|q5 | 377 | 235 | 43.202 | 46.274 | 0.020 | 0.024 | 1.071 | 0.937 | 1.226 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.131 | 0.108 | 0.163 | 0.130 | 0.117 | 0.155 | 0.102 | 0.000 | 0.106 | 0.325 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2 |
| cycle\|q2 | cycle\|q1+q2 |
| cycle\|q3 | cycle\|q3+q4+q5 |
| cycle\|q4 | cycle\|q3+q4+q5 |
| cycle\|q5 | cycle\|q3+q4+q5 |
| other\|q1 | other\|q1+q2 |
| other\|q2 | other\|q1+q2 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.740 | 1.079 | 1.055 | 1.102 | 0.666 | 0.000 | 0.048 | 0.038 | 0.069 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_income: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.143 | 19.345 |
| 2 | 28.573 | 29.884 |
| 3 | 36.911 | 39.895 |
| 4 | 44.882 | 49.471 |
| 5 | 58.727 | 59.620 |
| 6 | 67.335 | 74.192 |
| 7 | 82.426 | 89.454 |
| 8 | 99.998 | 109.655 |
| 9 | 132.933 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0+1 | 3270 | 2488 | 67.156 | 70.828 | 0.194 | 0.194 | 1.055 | 1.006 | 1.112 | inconclusive | equivalent |
| car_driver\|2+ | 4829 | 2826 | 66.994 | 75.423 | 0.309 | 0.292 | 1.126 | 1.088 | 1.173 | inconclusive | inconclusive |
| car_driver\|unknown | 0 | 7 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 180 | 199 | 52.191 | 60.485 | 0.009 | 0.009 | 1.159 | 0.966 | 1.330 | inconclusive | inconclusive |
| car_passenger_carpool\|1 | 142 | 128 | 64.934 | 68.005 | 0.007 | 0.008 | 1.047 | 0.825 | 1.299 | inconclusive | inconclusive |
| car_passenger_carpool\|2+ | 82 | 56 | 53.750 | 59.880 | 0.008 | 0.007 | 1.114 | 0.890 | 1.375 | inconclusive | inconclusive |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 386 | 370 | 57.618 | 54.898 | 0.035 | 0.042 | 0.953 | 0.828 | 1.090 | inconclusive | inconclusive |
| car_passenger_household\|2+ | 545 | 450 | 47.160 | 59.354 | 0.046 | 0.051 | 1.259 | 1.142 | 1.394 | different | inconclusive |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0 | 92 | 54 | 51.437 | 74.777 | 0.006 | 0.007 | 1.454 | 1.036 | 2.031 | inconclusive | inconclusive |
| cycle\|1 | 126 | 74 | 61.618 | 62.390 | 0.010 | 0.008 | 1.013 | 0.790 | 1.307 | inconclusive | inconclusive |
| cycle\|2+ | 92 | 53 | 52.475 | 78.716 | 0.009 | 0.006 | 1.500 | 1.008 | 2.068 | inconclusive | inconclusive |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 147 | 81 | 111.840 | 136.979 | 0.008 | 0.008 | 1.225 | 1.069 | 1.372 | inconclusive | inconclusive |
| multimodal\|1 | 490 | 294 | 103.333 | 106.155 | 0.036 | 0.032 | 1.027 | 0.920 | 1.136 | inconclusive | equivalent |
| multimodal\|2+ | 736 | 443 | 96.738 | 98.673 | 0.055 | 0.057 | 1.020 | 0.933 | 1.095 | equivalent | equivalent |
| multimodal\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| other\|0 | 80 | 57 | 57.656 | 77.956 | 0.005 | 0.004 | 1.352 | 1.050 | 1.739 | inconclusive | inconclusive |
| other\|1 | 154 | 86 | 65.188 | 75.577 | 0.014 | 0.011 | 1.159 | 0.947 | 1.386 | inconclusive | inconclusive |
| other\|2+ | 200 | 80 | 69.493 | 75.437 | 0.018 | 0.011 | 1.086 | 0.913 | 1.327 | inconclusive | inconclusive |
| train\|0 | 141 | 52 | 129.883 | 167.402 | 0.005 | 0.005 | 1.289 | 1.068 | 1.471 | inconclusive | inconclusive |
| train\|1+2+ | 271 | 104 | 127.457 | 132.144 | 0.015 | 0.015 | 1.037 | 0.927 | 1.156 | inconclusive | inconclusive |
| train\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 630 | 423 | 98.702 | 97.363 | 0.030 | 0.040 | 0.986 | 0.900 | 1.084 | equivalent | equivalent |
| urban_pt\|1 | 335 | 205 | 92.934 | 86.948 | 0.023 | 0.027 | 0.936 | 0.861 | 1.032 | inconclusive | equivalent |
| urban_pt\|2+ | 130 | 93 | 95.320 | 108.287 | 0.010 | 0.016 | 1.136 | 0.999 | 1.284 | inconclusive | inconclusive |
| urban_pt\|unknown | 0 | 5 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 883 | 589 | 45.834 | 50.453 | 0.048 | 0.050 | 1.101 | 0.983 | 1.224 | inconclusive | inconclusive |
| walking_only\|1 | 847 | 578 | 42.309 | 48.271 | 0.067 | 0.065 | 1.141 | 1.024 | 1.246 | inconclusive | inconclusive |
| walking_only\|2+ | 380 | 264 | 42.326 | 38.893 | 0.033 | 0.033 | 0.919 | 0.787 | 1.071 | inconclusive | inconclusive |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.124 | 0.101 | 0.153 | 0.136 | 0.116 | 0.166 | - | 0.091 | 0.344 | - | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_driver\|0 | car_driver\|0+1 |
| car_driver\|1 | car_driver\|0+1 |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |
| train\|1 | train\|1+2+ |
| train\|2+ | train\|1+2+ |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 68.533 | 1.083 | 1.059 | 1.107 | 0.459 | 0.002 | 0.049 | 0.039 | 0.071 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.144 | 19.345 |
| 2 | 28.362 | 29.884 |
| 3 | 36.565 | 39.895 |
| 4 | 44.831 | 49.471 |
| 5 | 58.471 | 59.620 |
| 6 | 67.068 | 74.192 |
| 7 | 81.573 | 89.454 |
| 8 | 99.979 | 109.655 |
| 9 | 131.740 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 210 | 126 | 51.402 | 57.308 | 0.020 | 0.021 | 1.115 | 0.903 | 1.319 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q1 | 128 | 190 | 63.365 | 59.078 | 0.025 | 0.037 | 0.932 | 0.740 | 1.113 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q2 | 145 | 120 | 49.448 | 55.768 | 0.025 | 0.022 | 1.128 | 0.959 | 1.323 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q3 | 109 | 84 | 48.476 | 62.031 | 0.015 | 0.015 | 1.280 | 1.004 | 1.582 | inconclusive | inconclusive |
| children_6_17\|dense+intermediate\|q4 | 133 | 98 | 49.056 | 54.422 | 0.018 | 0.018 | 1.109 | 0.875 | 1.322 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q1 | 128 | 70 | 51.479 | 58.747 | 0.016 | 0.014 | 1.141 | 0.793 | 1.493 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q2 | 183 | 83 | 60.465 | 50.386 | 0.018 | 0.015 | 0.833 | 0.681 | 1.019 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q3 | 146 | 93 | 56.207 | 56.948 | 0.015 | 0.016 | 1.013 | 0.843 | 1.212 | inconclusive | inconclusive |
| children_6_17\|sparse+very_sparse\|q4 | 144 | 81 | 50.459 | 45.576 | 0.016 | 0.013 | 0.903 | 0.749 | 1.065 | inconclusive | inconclusive |
| employed\|dense\|q1 | 90 | 69 | 85.876 | 88.288 | 0.008 | 0.008 | 1.028 | 0.842 | 1.268 | inconclusive | inconclusive |
| employed\|dense\|q2 | 115 | 75 | 81.263 | 87.926 | 0.009 | 0.008 | 1.082 | 0.889 | 1.321 | inconclusive | inconclusive |
| employed\|dense\|q3 | 214 | 91 | 77.480 | 80.372 | 0.015 | 0.009 | 1.037 | 0.911 | 1.155 | inconclusive | inconclusive |
| employed\|dense\|q4 | 247 | 136 | 68.261 | 82.253 | 0.016 | 0.016 | 1.205 | 1.044 | 1.365 | inconclusive | inconclusive |
| employed\|dense\|q5 | 465 | 206 | 84.783 | 82.844 | 0.022 | 0.025 | 0.977 | 0.885 | 1.083 | inconclusive | equivalent |
| employed\|intermediate\|q1 | 222 | 199 | 78.326 | 75.014 | 0.018 | 0.026 | 0.958 | 0.820 | 1.144 | inconclusive | inconclusive |
| employed\|intermediate\|q2 | 413 | 312 | 72.187 | 79.139 | 0.037 | 0.033 | 1.096 | 0.973 | 1.231 | inconclusive | inconclusive |
| employed\|intermediate\|q3 | 573 | 392 | 72.870 | 89.063 | 0.046 | 0.043 | 1.222 | 1.093 | 1.361 | inconclusive | inconclusive |
| employed\|intermediate\|q4 | 778 | 446 | 76.760 | 80.583 | 0.052 | 0.045 | 1.050 | 0.966 | 1.140 | inconclusive | equivalent |
| employed\|intermediate\|q5 | 1149 | 593 | 86.757 | 93.166 | 0.061 | 0.062 | 1.074 | 1.010 | 1.164 | inconclusive | inconclusive |
| employed\|sparse+very_sparse\|q1 | 344 | 138 | 62.761 | 71.722 | 0.024 | 0.019 | 1.143 | 0.995 | 1.294 | inconclusive | inconclusive |
| employed\|sparse\|q2 | 158 | 101 | 59.565 | 69.955 | 0.015 | 0.013 | 1.174 | 1.019 | 1.395 | inconclusive | inconclusive |
| employed\|sparse\|q3 | 199 | 142 | 73.315 | 77.277 | 0.017 | 0.019 | 1.054 | 0.781 | 1.308 | inconclusive | inconclusive |
| employed\|sparse\|q4 | 251 | 176 | 77.086 | 83.777 | 0.025 | 0.022 | 1.087 | 0.898 | 1.282 | inconclusive | inconclusive |
| employed\|sparse\|q5 | 246 | 169 | 73.575 | 79.780 | 0.018 | 0.018 | 1.084 | 0.943 | 1.245 | inconclusive | inconclusive |
| employed\|very_sparse\|q2 | 466 | 211 | 64.914 | 84.540 | 0.028 | 0.023 | 1.302 | 1.143 | 1.490 | different | inconclusive |
| employed\|very_sparse\|q3 | 580 | 277 | 70.263 | 82.279 | 0.028 | 0.028 | 1.171 | 1.034 | 1.304 | inconclusive | inconclusive |
| employed\|very_sparse\|q4 | 676 | 281 | 73.336 | 89.055 | 0.035 | 0.024 | 1.214 | 1.088 | 1.340 | inconclusive | inconclusive |
| employed\|very_sparse\|q5 | 555 | 251 | 78.342 | 88.530 | 0.021 | 0.021 | 1.130 | 1.008 | 1.289 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 197 | 115 | 70.196 | 86.703 | 0.011 | 0.013 | 1.235 | 1.041 | 1.490 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 153 | 70 | 75.124 | 91.028 | 0.009 | 0.009 | 1.212 | 0.938 | 1.495 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 231 | 57 | 73.698 | 80.577 | 0.012 | 0.008 | 1.093 | 0.768 | 1.407 | inconclusive | inconclusive |
| other_inactive\|dense+intermediate\|q2 | 167 | 139 | 69.447 | 83.042 | 0.013 | 0.014 | 1.196 | 1.025 | 1.382 | inconclusive | inconclusive |
| other_inactive\|dense\|q1 | 184 | 110 | 68.724 | 77.897 | 0.010 | 0.010 | 1.133 | 0.989 | 1.306 | inconclusive | inconclusive |
| other_inactive\|intermediate\|q1 | 225 | 202 | 70.542 | 73.616 | 0.019 | 0.016 | 1.044 | 0.865 | 1.223 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q1 | 172 | 89 | 69.662 | 66.847 | 0.011 | 0.009 | 0.960 | 0.693 | 1.274 | inconclusive | inconclusive |
| other_inactive\|sparse+very_sparse\|q2 | 123 | 64 | 62.937 | 74.583 | 0.008 | 0.007 | 1.185 | 0.914 | 1.566 | inconclusive | inconclusive |
| retired\|dense\|q1 | 69 | 50 | 60.558 | 68.439 | 0.004 | 0.003 | 1.130 | 0.838 | 1.533 | inconclusive | inconclusive |
| retired\|dense\|q2 | 59 | 73 | 76.457 | 78.336 | 0.003 | 0.005 | 1.025 | 0.686 | 1.497 | inconclusive | inconclusive |
| retired\|dense\|q3 | 85 | 73 | 55.020 | 81.560 | 0.004 | 0.006 | 1.482 | 1.155 | 1.990 | different | different |
| retired\|dense\|q4 | 91 | 94 | 68.556 | 74.201 | 0.005 | 0.007 | 1.082 | 0.789 | 1.509 | inconclusive | inconclusive |
| retired\|dense\|q5 | 189 | 124 | 75.032 | 76.924 | 0.009 | 0.010 | 1.025 | 0.847 | 1.229 | inconclusive | inconclusive |
| retired\|intermediate\|q1 | 234 | 172 | 59.354 | 60.006 | 0.017 | 0.011 | 1.011 | 0.861 | 1.210 | inconclusive | inconclusive |
| retired\|intermediate\|q2 | 228 | 318 | 58.247 | 68.485 | 0.015 | 0.020 | 1.176 | 1.005 | 1.340 | inconclusive | inconclusive |
| retired\|intermediate\|q3 | 325 | 309 | 64.829 | 62.804 | 0.021 | 0.021 | 0.969 | 0.843 | 1.136 | inconclusive | inconclusive |
| retired\|intermediate\|q4 | 276 | 351 | 67.569 | 69.640 | 0.015 | 0.024 | 1.031 | 0.912 | 1.177 | inconclusive | inconclusive |
| retired\|intermediate\|q5 | 534 | 388 | 65.075 | 73.210 | 0.024 | 0.024 | 1.125 | 0.999 | 1.252 | inconclusive | inconclusive |
| retired\|sparse\|q1 | 101 | 85 | 45.122 | 67.093 | 0.007 | 0.006 | 1.487 | 1.151 | 1.865 | different | different |
| retired\|sparse\|q2 | 103 | 164 | 48.417 | 53.416 | 0.008 | 0.014 | 1.103 | 0.897 | 1.504 | inconclusive | inconclusive |
| retired\|sparse\|q3 | 122 | 124 | 56.007 | 63.709 | 0.009 | 0.010 | 1.138 | 0.895 | 1.411 | inconclusive | inconclusive |
| retired\|sparse\|q4 | 102 | 141 | 56.663 | 49.933 | 0.006 | 0.011 | 0.881 | 0.734 | 1.077 | inconclusive | inconclusive |
| retired\|sparse\|q5 | 131 | 119 | 65.331 | 66.859 | 0.008 | 0.009 | 1.023 | 0.803 | 1.249 | inconclusive | inconclusive |
| retired\|very_sparse\|q1 | 320 | 99 | 53.408 | 50.175 | 0.011 | 0.006 | 0.939 | 0.768 | 1.150 | inconclusive | inconclusive |
| retired\|very_sparse\|q2 | 268 | 216 | 60.433 | 55.192 | 0.011 | 0.012 | 0.913 | 0.803 | 1.078 | inconclusive | inconclusive |
| retired\|very_sparse\|q3 | 318 | 207 | 63.582 | 60.649 | 0.013 | 0.012 | 0.954 | 0.848 | 1.104 | inconclusive | inconclusive |
| retired\|very_sparse\|q4 | 188 | 195 | 66.321 | 62.718 | 0.007 | 0.012 | 0.946 | 0.810 | 1.096 | inconclusive | inconclusive |
| retired\|very_sparse\|q5 | 263 | 158 | 73.225 | 76.885 | 0.008 | 0.008 | 1.050 | 0.892 | 1.211 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 130 | 96 | 75.183 | 74.727 | 0.008 | 0.010 | 0.994 | 0.792 | 1.265 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 99 | 73 | 71.785 | 86.076 | 0.006 | 0.008 | 1.199 | 0.966 | 1.486 | inconclusive | inconclusive |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 149 | 72 | 77.097 | 78.822 | 0.008 | 0.008 | 1.022 | 0.810 | 1.247 | inconclusive | inconclusive |
| unemployed\|dense+intermediate\|q1 | 164 | 221 | 58.897 | 84.129 | 0.013 | 0.018 | 1.428 | 1.167 | 1.700 | different | different |
| unemployed\|sparse+very_sparse\|q1 | 100 | 83 | 58.850 | 69.576 | 0.006 | 0.008 | 1.182 | 0.808 | 1.734 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.039 | 0.036 | 0.057 | 0.051 | 0.049 | 0.072 | 0.112 | 0.000 | 0.072 | 0.397 | 0.000 | 0.001 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.191 | 67.988 | 1.091 | 1.063 | 1.114 | -0.088 | 0.000 | 0.054 | 0.042 | 0.077 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### category_x_density_x_income: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.105 | 19.344 |
| 2 | 27.455 | 29.884 |
| 3 | 34.975 | 39.895 |
| 4 | 44.576 | 49.470 |
| 5 | 56.619 | 59.619 |
| 6 | 65.824 | 74.190 |
| 7 | 80.063 | 89.451 |
| 8 | 99.949 | 109.655 |
| 9 | 129.894 | 146.478 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: cell levels

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4505 | 3052 | 68.397 | 71.255 | 0.245 | 0.244 | 1.042 | 1.000 | 1.086 | equivalent | equivalent |
| couple_with_children | 5328 | 2878 | 68.658 | 75.435 | 0.485 | 0.445 | 1.099 | 1.058 | 1.130 | inconclusive | equivalent |
| other | 353 | 206 | 66.848 | 77.587 | 0.036 | 0.032 | 1.161 | 1.025 | 1.308 | inconclusive | inconclusive |
| single_parent | 1136 | 812 | 66.720 | 74.106 | 0.087 | 0.112 | 1.111 | 1.006 | 1.201 | inconclusive | inconclusive |
| single_person | 3846 | 3123 | 66.714 | 74.598 | 0.148 | 0.167 | 1.118 | 1.073 | 1.165 | inconclusive | inconclusive |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: stability and explained variance

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.003 | 0.001 | 0.000 | 0.003 | 0.087 | 0.245 | 0.710 | 0.149 | 0.000 | 0.000 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed full-sample merges

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 74.196 | 67.996 | 1.091 | 1.065 | 1.113 | -0.078 | 0.000 | 0.053 | 0.042 | 0.076 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### household_type: fixed-cell deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 19.119 | 19.345 |
| 2 | 27.671 | 29.884 |
| 3 | 34.998 | 39.895 |
| 4 | 44.652 | 49.471 |
| 5 | 57.243 | 59.620 |
| 6 | 65.707 | 74.192 |
| 7 | 79.946 | 89.454 |
| 8 | 99.936 | 109.655 |
| 9 | 129.948 | 146.461 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person mode use and user-day minutes

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 4441 | 2975 | 0.251 | 0.263 | 37.509 | 39.410 |
| bike | 520 | 306 | 0.032 | 0.029 | 43.089 | 50.079 |
| car_driver | 8926 | 5805 | 0.460 | 0.447 | 62.098 | 67.507 |
| car_passenger | 2208 | 1728 | 0.144 | 0.150 | 41.436 | 45.805 |
| urban_pt | 1484 | 964 | 0.075 | 0.096 | 72.728 | 75.743 |
| train | 610 | 253 | 0.023 | 0.028 | 116.692 | 126.103 |
| other | 657 | 362 | 0.049 | 0.036 | 58.647 | 63.396 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode model

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 56.409 | 61.935 | 57.435 | 1.026 | -0.252 | 2.314 | 4.500 | 2.989 | 5.905 | 0.034 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

### Per-person fixed-mode deciles

Scope: All days · all purposes · local (≤ 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | 0.000 | 0.000 |
| 2 | 9.545 | 9.720 |
| 3 | 23.390 | 24.564 |
| 4 | 34.362 | 39.834 |
| 5 | 44.789 | 49.497 |
| 6 | 59.888 | 59.931 |
| 7 | 74.449 | 79.556 |
| 8 | 94.034 | 99.781 |
| 9 | 124.414 | 134.822 |

n: 2008 15168, 2019 10071 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

## All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`)

### Grouping summary

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | equivalent_10_share | observed_over_predicted | ratio_low | ratio_high | ks_d | n_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | 0.027 | 0.032 | - | - | - | - | - | - | 6 |
| category | 0.025 | 0.029 | - | - | - | - | - | - | 5 |
| category_x_density_x_income | 0.043 | 0.045 | - | - | - | - | - | - | 61 |
| day_mode_group | 0.113 | 0.092 | - | - | - | - | - | - | 9 |
| day_mode_group_x_category | 0.144 | 0.127 | - | - | - | - | - | - | 45 |
| day_mode_group_x_density | 0.117 | 0.100 | - | - | - | - | - | - | 28 |
| day_mode_group_x_income | 0.127 | 0.102 | - | - | - | - | - | - | 36 |
| day_mode_group_x_vehicles | 0.116 | 0.103 | - | - | - | - | - | - | 34 |
| day_purpose | 0.006 | 0.002 | - | - | - | - | - | - | 3 |
| density | 0.002 | 0.004 | - | - | - | - | - | - | 4 |
| household_type | 0.000 | 0.001 | - | - | - | - | - | - | 5 |
| income | 0.014 | 0.008 | - | - | - | - | - | - | 5 |
| none | 0.000 | 0.000 | - | - | - | - | - | - | 1 |
| vehicles | 0.000 | 0.003 | - | - | - | - | - | - | 4 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 15605 | 10356 | 74.788 | 81.408 | 1.000 | 1.000 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### none: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17 | 1352 | 968 | 56.954 | 60.798 | 0.166 | 0.169 | - | - | - |  |  |
| employed | 7995 | 4407 | 84.334 | 92.639 | 0.497 | 0.465 | - | - | - |  |  |
| other_inactive | 1483 | 867 | 74.484 | 84.436 | 0.093 | 0.087 | - | - | - |  |  |
| retired | 4114 | 3542 | 66.460 | 71.324 | 0.203 | 0.228 | - | - | - |  |  |
| unemployed | 660 | 561 | 73.290 | 86.874 | 0.040 | 0.052 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.025 | 0.019 | 0.031 | 0.029 | 0.021 | 0.040 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.393 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 1068 | 725 | 50.726 | 53.708 | 0.126 | 0.127 | - | - | - |  |  |
| 15 | 2304 | 1317 | 81.294 | 87.333 | 0.214 | 0.181 | - | - | - |  |  |
| 30 | 2328 | 1186 | 84.708 | 95.289 | 0.169 | 0.139 | - | - | - |  |  |
| 40 | 2599 | 1338 | 81.604 | 91.257 | 0.157 | 0.156 | - | - | - |  |  |
| 50 | 3048 | 1757 | 79.072 | 90.295 | 0.134 | 0.137 | - | - | - |  |  |
| 60 | 4258 | 4033 | 66.377 | 72.745 | 0.201 | 0.260 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.027 | 0.021 | 0.035 | 0.032 | 0.025 | 0.045 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### age_band: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | 2255 | 1442 | 78.553 | 88.212 | 0.142 | 0.150 | - | - | - |  |  |
| intermediate | 6297 | 4761 | 76.423 | 82.191 | 0.441 | 0.457 | - | - | - |  |  |
| sparse | 2012 | 1658 | 68.494 | 73.116 | 0.175 | 0.185 | - | - | - |  |  |
| very_sparse | 5041 | 2495 | 74.148 | 82.134 | 0.242 | 0.208 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.002 | 0.001 | 0.005 | 0.004 | 0.001 | 0.009 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### density: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | 2509 | 1809 | 66.714 | 72.532 | 0.186 | 0.188 | - | - | - |  |  |
| q2 | 2597 | 2010 | 68.019 | 76.009 | 0.196 | 0.195 | - | - | - |  |  |
| q3 | 3044 | 2037 | 72.595 | 86.134 | 0.200 | 0.198 | - | - | - |  |  |
| q4 | 3212 | 2184 | 76.248 | 80.647 | 0.209 | 0.208 | - | - | - |  |  |
| q5 | 4243 | 2316 | 88.847 | 90.608 | 0.210 | 0.211 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.014 | 0.009 | 0.020 | 0.008 | 0.005 | 0.013 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### income: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2273 | 1555 | 72.727 | 83.577 | 0.118 | 0.127 | - | - | - |  |  |
| 1 | 6020 | 4314 | 74.559 | 77.295 | 0.388 | 0.389 | - | - | - |  |  |
| 2+ | 7312 | 4462 | 75.460 | 83.933 | 0.494 | 0.482 | - | - | - |  |  |
| unknown | 0 | 25 | - | - | - | - | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.002 | 0.003 | 0.001 | 0.010 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### vehicles: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| other | 7830 | 6061 | 69.033 | 78.274 | 0.455 | 0.481 | - | - | - |  |  |
| unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| work_study | 7775 | 4294 | 79.599 | 84.311 | 0.545 | 0.519 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.006 | 0.003 | 0.010 | 0.002 | 0.000 | 0.005 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_purpose: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver | 8267 | 5418 | 72.712 | 80.613 | 0.500 | 0.481 | - | - | - |  |  |
| car_passenger_carpool | 442 | 408 | 66.671 | 73.192 | 0.026 | 0.025 | - | - | - |  |  |
| car_passenger_household | 961 | 867 | 57.369 | 66.333 | 0.080 | 0.096 | - | - | - |  |  |
| cycle | 310 | 179 | 56.954 | 71.830 | 0.024 | 0.020 | - | - | - |  |  |
| multimodal | 1499 | 871 | 115.292 | 114.535 | 0.104 | 0.099 | - | - | - |  |  |
| other | 463 | 241 | 75.114 | 94.620 | 0.038 | 0.027 | - | - | - |  |  |
| train | 456 | 189 | 152.576 | 165.735 | 0.023 | 0.022 | - | - | - |  |  |
| urban_pt | 1103 | 742 | 98.538 | 102.088 | 0.062 | 0.083 | - | - | - |  |  |
| walking_only | 2104 | 1441 | 44.025 | 47.064 | 0.143 | 0.146 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.113 | 0.094 | 0.133 | 0.092 | 0.079 | 0.108 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|dense | 592 | 412 | 79.229 | 99.208 | 0.041 | 0.040 | - | - | - |  |  |
| car_driver\|intermediate | 3082 | 2325 | 73.519 | 79.840 | 0.209 | 0.207 | - | - | - |  |  |
| car_driver\|sparse | 1233 | 987 | 70.210 | 72.860 | 0.098 | 0.103 | - | - | - |  |  |
| car_driver\|very_sparse | 3360 | 1694 | 71.447 | 82.193 | 0.151 | 0.132 | - | - | - |  |  |
| car_passenger_carpool\|dense | 53 | 61 | 88.487 | 96.151 | 0.003 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|intermediate | 194 | 191 | 64.408 | 71.633 | 0.012 | 0.010 | - | - | - |  |  |
| car_passenger_carpool\|sparse | 60 | 68 | 61.279 | 66.912 | 0.006 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|very_sparse | 135 | 88 | 63.813 | 64.801 | 0.005 | 0.005 | - | - | - |  |  |
| car_passenger_household\|dense | 79 | 73 | 58.759 | 81.871 | 0.007 | 0.009 | - | - | - |  |  |
| car_passenger_household\|intermediate | 345 | 399 | 55.332 | 66.547 | 0.034 | 0.044 | - | - | - |  |  |
| car_passenger_household\|sparse | 143 | 168 | 50.451 | 63.098 | 0.015 | 0.020 | - | - | - |  |  |
| car_passenger_household\|very_sparse | 394 | 227 | 64.457 | 62.583 | 0.023 | 0.023 | - | - | - |  |  |
| cycle\|dense+intermediate | 172 | 125 | 58.290 | 70.740 | 0.015 | 0.014 | - | - | - |  |  |
| cycle\|sparse+very_sparse | 138 | 54 | 54.765 | 74.268 | 0.009 | 0.006 | - | - | - |  |  |
| multimodal\|dense | 244 | 127 | 136.079 | 115.159 | 0.014 | 0.013 | - | - | - |  |  |
| multimodal\|intermediate | 628 | 418 | 114.186 | 117.657 | 0.047 | 0.051 | - | - | - |  |  |
| multimodal\|sparse | 162 | 112 | 99.114 | 107.545 | 0.016 | 0.014 | - | - | - |  |  |
| multimodal\|very_sparse | 465 | 214 | 116.054 | 111.416 | 0.027 | 0.022 | - | - | - |  |  |
| other\|dense+intermediate | 215 | 145 | 78.569 | 101.331 | 0.018 | 0.015 | - | - | - |  |  |
| other\|sparse+very_sparse | 248 | 96 | 72.088 | 85.654 | 0.020 | 0.011 | - | - | - |  |  |
| train\|dense+intermediate+sparse+very_sparse | 456 | 189 | 152.576 | 165.735 | 0.023 | 0.022 | - | - | - |  |  |
| urban_pt\|dense | 579 | 314 | 94.429 | 94.938 | 0.028 | 0.035 | - | - | - |  |  |
| urban_pt\|intermediate | 467 | 367 | 100.961 | 101.414 | 0.030 | 0.039 | - | - | - |  |  |
| urban_pt\|sparse+very_sparse | 57 | 61 | 107.372 | 134.242 | 0.005 | 0.009 | - | - | - |  |  |
| walking_only\|dense | 513 | 354 | 44.087 | 53.970 | 0.036 | 0.037 | - | - | - |  |  |
| walking_only\|intermediate | 975 | 731 | 43.872 | 46.455 | 0.069 | 0.070 | - | - | - |  |  |
| walking_only\|sparse | 261 | 210 | 44.947 | 42.163 | 0.023 | 0.025 | - | - | - |  |  |
| walking_only\|very_sparse | 355 | 146 | 43.137 | 40.129 | 0.015 | 0.013 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.117 | 0.100 | 0.141 | 0.100 | 0.090 | 0.119 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| cycle\|dense | cycle\|dense+intermediate |
| cycle\|intermediate | cycle\|dense+intermediate |
| cycle\|sparse | cycle\|sparse+very_sparse |
| cycle\|very_sparse | cycle\|sparse+very_sparse |
| other\|dense | other\|dense+intermediate |
| other\|intermediate | other\|dense+intermediate |
| other\|sparse | other\|sparse+very_sparse |
| other\|very_sparse | other\|sparse+very_sparse |
| train\|dense | train\|dense+intermediate+sparse+very_sparse |
| train\|intermediate | train\|dense+intermediate+sparse+very_sparse |
| train\|sparse | train\|dense+intermediate+sparse+very_sparse |
| train\|very_sparse | train\|dense+intermediate+sparse+very_sparse |
| urban_pt\|sparse | urban_pt\|sparse+very_sparse |
| urban_pt\|very_sparse | urban_pt\|sparse+very_sparse |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_density: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|children_6_17 | 62 | 42 | 57.348 | - | 0.008 | - | - | - | - |  |  |
| car_driver\|employed | 5208 | 2963 | 77.308 | 86.332 | 0.331 | 0.306 | - | - | - |  |  |
| car_driver\|other_inactive | 590 | 282 | 65.050 | 71.439 | 0.035 | 0.025 | - | - | - |  |  |
| car_driver\|retired | 2101 | 1871 | 62.889 | 68.118 | 0.108 | 0.120 | - | - | - |  |  |
| car_driver\|unemployed | 306 | 256 | 68.747 | 79.113 | 0.017 | 0.023 | - | - | - |  |  |
| car_passenger_carpool\|children_6_17 | 29 | 24 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|employed | 130 | 74 | 65.636 | 98.452 | 0.009 | 0.006 | - | - | - |  |  |
| car_passenger_carpool\|other_inactive | 66 | 54 | 74.860 | 71.649 | 0.004 | 0.004 | - | - | - |  |  |
| car_passenger_carpool\|retired | 187 | 222 | 66.122 | 71.137 | 0.008 | 0.009 | - | - | - |  |  |
| car_passenger_carpool\|unemployed | 29 | 32 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|children_6_17 | 399 | 325 | 43.791 | 52.009 | 0.047 | 0.054 | - | - | - |  |  |
| car_passenger_household\|employed | 167 | 95 | 73.368 | 98.056 | 0.010 | 0.010 | - | - | - |  |  |
| car_passenger_household\|other_inactive | 118 | 83 | 90.572 | 80.496 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|retired | 250 | 334 | 68.856 | 78.304 | 0.014 | 0.022 | - | - | - |  |  |
| car_passenger_household\|unemployed | 27 | 30 | - | - | - | - | - | - | - |  |  |
| cycle\|children_6_17 | 52 | 21 | 40.483 | - | 0.008 | - | - | - | - |  |  |
| cycle\|employed | 124 | 80 | 68.710 | 61.640 | 0.008 | 0.010 | - | - | - |  |  |
| cycle\|other_inactive | 26 | 15 | - | - | - | - | - | - | - |  |  |
| cycle\|retired | 94 | 51 | 59.749 | 78.333 | 0.005 | 0.004 | - | - | - |  |  |
| cycle\|unemployed | 14 | 12 | - | - | - | - | - | - | - |  |  |
| multimodal\|children_6_17 | 255 | 168 | 74.062 | 78.593 | 0.029 | 0.026 | - | - | - |  |  |
| multimodal\|employed | 784 | 415 | 134.124 | 133.946 | 0.051 | 0.046 | - | - | - |  |  |
| multimodal\|other_inactive | 137 | 68 | 114.046 | 125.601 | 0.009 | 0.009 | - | - | - |  |  |
| multimodal\|retired | 259 | 173 | 137.271 | 111.151 | 0.011 | 0.011 | - | - | - |  |  |
| multimodal\|unemployed | 64 | 47 | 116.841 | - | 0.004 | - | - | - | - |  |  |
| other\|children_6_17 | 179 | 49 | 72.540 | - | 0.019 | - | - | - | - |  |  |
| other\|employed | 192 | 98 | 80.722 | 109.283 | 0.013 | 0.013 | - | - | - |  |  |
| other\|other_inactive | 30 | 26 | - | - | - | - | - | - | - |  |  |
| other\|retired | 56 | 60 | 76.645 | 73.438 | 0.003 | 0.003 | - | - | - |  |  |
| other\|unemployed | 6 | 7 | - | - | - | - | - | - | - |  |  |
| train\|children_6_17 | 23 | 14 | - | - | - | - | - | - | - |  |  |
| train\|employed | 331 | 127 | 161.382 | 174.022 | 0.015 | 0.013 | - | - | - |  |  |
| train\|other_inactive | 45 | 19 | - | - | - | - | - | - | - |  |  |
| train\|retired | 45 | 22 | - | - | - | - | - | - | - |  |  |
| train\|unemployed | 12 | 6 | - | - | - | - | - | - | - |  |  |
| urban_pt\|children_6_17 | 95 | 119 | 103.984 | 94.581 | 0.012 | 0.021 | - | - | - |  |  |
| urban_pt\|employed | 538 | 271 | 94.993 | 102.089 | 0.027 | 0.030 | - | - | - |  |  |
| urban_pt\|other_inactive | 187 | 131 | 94.352 | 112.655 | 0.012 | 0.016 | - | - | - |  |  |
| urban_pt\|retired | 226 | 155 | 101.199 | 101.107 | 0.008 | 0.010 | - | - | - |  |  |
| urban_pt\|unemployed | 57 | 64 | 119.169 | 101.306 | 0.003 | 0.006 | - | - | - |  |  |
| walking_only\|children_6_17 | 258 | 206 | 37.568 | 33.500 | 0.037 | 0.042 | - | - | - |  |  |
| walking_only\|employed | 521 | 284 | 44.991 | 47.249 | 0.032 | 0.030 | - | - | - |  |  |
| walking_only\|other_inactive | 284 | 189 | 44.050 | 54.397 | 0.018 | 0.017 | - | - | - |  |  |
| walking_only\|retired | 896 | 654 | 48.719 | 54.166 | 0.044 | 0.047 | - | - | - |  |  |
| walking_only\|unemployed | 145 | 107 | 44.304 | 58.799 | 0.011 | 0.009 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.144 | 0.123 | 0.170 | 0.127 | 0.113 | 0.151 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.393 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_category: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|q1 | 958 | 613 | 60.408 | 71.163 | 0.064 | 0.057 | - | - | - |  |  |
| car_driver\|q2 | 1295 | 1001 | 66.497 | 71.817 | 0.091 | 0.091 | - | - | - |  |  |
| car_driver\|q3 | 1719 | 1155 | 69.985 | 84.006 | 0.109 | 0.104 | - | - | - |  |  |
| car_driver\|q4 | 1860 | 1295 | 76.162 | 82.176 | 0.113 | 0.113 | - | - | - |  |  |
| car_driver\|q5 | 2435 | 1354 | 82.886 | 87.635 | 0.123 | 0.115 | - | - | - |  |  |
| car_passenger_carpool\|q1 | 125 | 123 | 60.594 | 71.681 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|q2 | 95 | 100 | 60.352 | 55.047 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q3 | 87 | 82 | 70.233 | 78.119 | 0.006 | 0.005 | - | - | - |  |  |
| car_passenger_carpool\|q4+q5 | 135 | 103 | 74.797 | 83.770 | 0.007 | 0.008 | - | - | - |  |  |
| car_passenger_household\|q1 | 145 | 144 | 66.526 | 60.487 | 0.013 | 0.019 | - | - | - |  |  |
| car_passenger_household\|q2 | 188 | 194 | 45.813 | 68.785 | 0.018 | 0.022 | - | - | - |  |  |
| car_passenger_household\|q3 | 205 | 176 | 58.625 | 66.384 | 0.017 | 0.019 | - | - | - |  |  |
| car_passenger_household\|q4 | 203 | 190 | 51.596 | 58.903 | 0.019 | 0.021 | - | - | - |  |  |
| car_passenger_household\|q5 | 220 | 163 | 71.068 | 80.599 | 0.013 | 0.015 | - | - | - |  |  |
| cycle\|q1+q2 | 128 | 75 | 59.945 | 81.676 | 0.010 | 0.009 | - | - | - |  |  |
| cycle\|q3+q4+q5 | 182 | 104 | 54.727 | 63.929 | 0.014 | 0.011 | - | - | - |  |  |
| multimodal\|q1 | 204 | 127 | 96.985 | 114.284 | 0.017 | 0.015 | - | - | - |  |  |
| multimodal\|q2 | 241 | 148 | 103.631 | 97.863 | 0.021 | 0.017 | - | - | - |  |  |
| multimodal\|q3 | 274 | 175 | 120.539 | 113.235 | 0.021 | 0.022 | - | - | - |  |  |
| multimodal\|q4 | 306 | 189 | 111.823 | 108.223 | 0.023 | 0.021 | - | - | - |  |  |
| multimodal\|q5 | 474 | 232 | 138.304 | 133.268 | 0.023 | 0.024 | - | - | - |  |  |
| other\|q1 | 74 | 52 | 71.899 | 76.090 | 0.009 | 0.006 | - | - | - |  |  |
| other\|q2 | 110 | 60 | 66.497 | 88.015 | 0.009 | 0.006 | - | - | - |  |  |
| other\|q3+q4+q5 | 279 | 129 | 80.431 | 104.293 | 0.020 | 0.015 | - | - | - |  |  |
| train\|q1+q2+q3+q4 | 259 | 122 | 151.022 | 174.397 | 0.014 | 0.015 | - | - | - |  |  |
| train\|q5 | 197 | 67 | 155.189 | 145.853 | 0.008 | 0.007 | - | - | - |  |  |
| urban_pt\|q1 | 253 | 250 | 106.084 | 96.016 | 0.018 | 0.027 | - | - | - |  |  |
| urban_pt\|q2 | 179 | 140 | 100.795 | 110.000 | 0.013 | 0.016 | - | - | - |  |  |
| urban_pt\|q3 | 184 | 113 | 95.206 | 105.346 | 0.009 | 0.014 | - | - | - |  |  |
| urban_pt\|q4 | 204 | 101 | 85.987 | 104.697 | 0.012 | 0.011 | - | - | - |  |  |
| urban_pt\|q5 | 283 | 138 | 100.388 | 99.561 | 0.010 | 0.016 | - | - | - |  |  |
| walking_only\|q1 | 628 | 442 | 46.559 | 47.435 | 0.050 | 0.047 | - | - | - |  |  |
| walking_only\|q2 | 385 | 295 | 40.330 | 48.546 | 0.030 | 0.029 | - | - | - |  |  |
| walking_only\|q3 | 377 | 224 | 42.728 | 50.159 | 0.023 | 0.021 | - | - | - |  |  |
| walking_only\|q4 | 333 | 247 | 43.235 | 42.057 | 0.021 | 0.025 | - | - | - |  |  |
| walking_only\|q5 | 381 | 233 | 45.636 | 46.965 | 0.019 | 0.023 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.127 | 0.109 | 0.149 | 0.102 | 0.091 | 0.124 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_carpool\|q4 | car_passenger_carpool\|q4+q5 |
| car_passenger_carpool\|q5 | car_passenger_carpool\|q4+q5 |
| cycle\|q1 | cycle\|q1+q2 |
| cycle\|q2 | cycle\|q1+q2 |
| cycle\|q3 | cycle\|q3+q4+q5 |
| cycle\|q4 | cycle\|q3+q4+q5 |
| cycle\|q5 | cycle\|q3+q4+q5 |
| other\|q3 | other\|q3+q4+q5 |
| other\|q4 | other\|q3+q4+q5 |
| other\|q5 | other\|q3+q4+q5 |
| train\|q1 | train\|q1+q2+q3+q4 |
| train\|q2 | train\|q1+q2+q3+q4 |
| train\|q3 | train\|q1+q2+q3+q4 |
| train\|q4 | train\|q1+q2+q3+q4 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_income: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| car_driver\|0 | 57 | 51 | 91.667 | 84.892 | 0.004 | 0.004 | - | - | - |  |  |
| car_driver\|1 | 3282 | 2472 | 71.230 | 76.967 | 0.189 | 0.187 | - | - | - |  |  |
| car_driver\|2+ | 4928 | 2888 | 73.361 | 82.940 | 0.307 | 0.289 | - | - | - |  |  |
| car_driver\|unknown | 0 | 7 | - | - | - | - | - | - | - |  |  |
| car_passenger_carpool\|0 | 197 | 209 | 58.635 | 75.824 | 0.010 | 0.009 | - | - | - |  |  |
| car_passenger_carpool\|1 | 159 | 137 | 79.948 | 75.431 | 0.008 | 0.008 | - | - | - |  |  |
| car_passenger_carpool\|2+ | 86 | 61 | 63.555 | 67.408 | 0.008 | 0.007 | - | - | - |  |  |
| car_passenger_carpool\|unknown | 0 | 1 | - | - | - | - | - | - | - |  |  |
| car_passenger_household\|0+1 | 395 | 387 | 60.133 | 61.729 | 0.034 | 0.043 | - | - | - |  |  |
| car_passenger_household\|2+ | 566 | 478 | 55.350 | 70.166 | 0.046 | 0.053 | - | - | - |  |  |
| car_passenger_household\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| cycle\|0 | 91 | 54 | 51.509 | 74.777 | 0.006 | 0.006 | - | - | - |  |  |
| cycle\|1 | 125 | 72 | 61.707 | 63.351 | 0.010 | 0.008 | - | - | - |  |  |
| cycle\|2+ | 94 | 51 | 55.394 | 80.583 | 0.009 | 0.006 | - | - | - |  |  |
| cycle\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| multimodal\|0 | 154 | 84 | 120.271 | 139.730 | 0.008 | 0.008 | - | - | - |  |  |
| multimodal\|1 | 544 | 315 | 122.667 | 120.046 | 0.038 | 0.033 | - | - | - |  |  |
| multimodal\|2+ | 801 | 470 | 109.746 | 108.029 | 0.058 | 0.058 | - | - | - |  |  |
| multimodal\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| other\|0 | 83 | 61 | 64.797 | 111.770 | 0.006 | 0.004 | - | - | - |  |  |
| other\|1 | 163 | 90 | 75.116 | 81.215 | 0.014 | 0.011 | - | - | - |  |  |
| other\|2+ | 217 | 90 | 78.172 | 101.396 | 0.019 | 0.012 | - | - | - |  |  |
| train\|0 | 153 | 60 | 135.110 | 189.780 | 0.005 | 0.006 | - | - | - |  |  |
| train\|1 | 198 | 74 | 153.005 | 154.173 | 0.011 | 0.009 | - | - | - |  |  |
| train\|2+ | 105 | 53 | 166.667 | 147.553 | 0.006 | 0.007 | - | - | - |  |  |
| train\|unknown | 0 | 2 | - | - | - | - | - | - | - |  |  |
| urban_pt\|0 | 631 | 424 | 99.179 | 97.412 | 0.029 | 0.039 | - | - | - |  |  |
| urban_pt\|1 | 339 | 211 | 97.589 | 97.123 | 0.023 | 0.027 | - | - | - |  |  |
| urban_pt\|2+ | 133 | 101 | 98.838 | 120.703 | 0.010 | 0.017 | - | - | - |  |  |
| urban_pt\|unknown | 0 | 6 | - | - | - | - | - | - | - |  |  |
| walking_only\|0 | 880 | 589 | 45.753 | 50.613 | 0.047 | 0.048 | - | - | - |  |  |
| walking_only\|1 | 842 | 579 | 42.896 | 48.344 | 0.065 | 0.064 | - | - | - |  |  |
| walking_only\|2+ | 382 | 270 | 43.756 | 39.330 | 0.032 | 0.033 | - | - | - |  |  |
| walking_only\|unknown | 0 | 3 | - | - | - | - | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.116 | 0.096 | 0.139 | 0.103 | 0.090 | 0.125 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| car_passenger_household\|0 | car_passenger_household\|0+1 |
| car_passenger_household\|1 | car_passenger_household\|0+1 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### day_mode_group_x_vehicles: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| children_6_17\|dense+intermediate+sparse+very_sparse\|q5 | 219 | 130 | 57.550 | 64.427 | 0.021 | 0.021 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q1 | 131 | 190 | 64.674 | 59.078 | 0.025 | 0.035 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q2 | 145 | 123 | 49.664 | 57.035 | 0.024 | 0.022 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q3 | 110 | 84 | 50.145 | 70.445 | 0.015 | 0.014 | - | - | - |  |  |
| children_6_17\|dense+intermediate\|q4 | 136 | 104 | 51.973 | 59.831 | 0.018 | 0.018 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q1 | 130 | 71 | 62.725 | 60.808 | 0.016 | 0.013 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q2 | 186 | 85 | 62.953 | 52.452 | 0.018 | 0.015 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q3 | 149 | 98 | 56.860 | 70.752 | 0.015 | 0.016 | - | - | - |  |  |
| children_6_17\|sparse+very_sparse\|q4 | 146 | 83 | 54.927 | 54.056 | 0.016 | 0.013 | - | - | - |  |  |
| employed\|dense\|q1 | 90 | 69 | 85.876 | 95.374 | 0.008 | 0.008 | - | - | - |  |  |
| employed\|dense\|q2 | 117 | 77 | 82.723 | 105.815 | 0.009 | 0.009 | - | - | - |  |  |
| employed\|dense\|q3 | 218 | 98 | 82.969 | 117.994 | 0.015 | 0.010 | - | - | - |  |  |
| employed\|dense\|q4 | 257 | 145 | 75.850 | 100.735 | 0.016 | 0.017 | - | - | - |  |  |
| employed\|dense\|q5 | 497 | 212 | 107.093 | 87.413 | 0.023 | 0.025 | - | - | - |  |  |
| employed\|intermediate\|q1 | 224 | 203 | 78.563 | 82.074 | 0.018 | 0.027 | - | - | - |  |  |
| employed\|intermediate\|q2 | 420 | 318 | 80.956 | 84.457 | 0.038 | 0.033 | - | - | - |  |  |
| employed\|intermediate\|q3 | 583 | 402 | 78.817 | 100.819 | 0.045 | 0.043 | - | - | - |  |  |
| employed\|intermediate\|q4 | 799 | 460 | 86.766 | 86.759 | 0.052 | 0.046 | - | - | - |  |  |
| employed\|intermediate\|q5 | 1193 | 623 | 100.459 | 102.343 | 0.062 | 0.063 | - | - | - |  |  |
| employed\|sparse+very_sparse\|q1 | 346 | 141 | 66.930 | 75.131 | 0.024 | 0.018 | - | - | - |  |  |
| employed\|sparse\|q2 | 159 | 101 | 61.959 | 69.955 | 0.014 | 0.013 | - | - | - |  |  |
| employed\|sparse\|q3 | 207 | 142 | 88.581 | 77.939 | 0.017 | 0.018 | - | - | - |  |  |
| employed\|sparse\|q4 | 260 | 185 | 80.341 | 90.752 | 0.025 | 0.022 | - | - | - |  |  |
| employed\|sparse\|q5 | 267 | 176 | 89.751 | 93.066 | 0.019 | 0.018 | - | - | - |  |  |
| employed\|very_sparse\|q2 | 472 | 213 | 71.463 | 95.114 | 0.027 | 0.022 | - | - | - |  |  |
| employed\|very_sparse\|q3 | 601 | 288 | 78.081 | 92.660 | 0.028 | 0.028 | - | - | - |  |  |
| employed\|very_sparse\|q4 | 697 | 287 | 83.910 | 93.186 | 0.035 | 0.024 | - | - | - |  |  |
| employed\|very_sparse\|q5 | 588 | 267 | 93.456 | 107.274 | 0.022 | 0.022 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q3 | 203 | 118 | 76.212 | 91.067 | 0.011 | 0.013 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q4 | 155 | 73 | 78.082 | 96.186 | 0.009 | 0.009 | - | - | - |  |  |
| other_inactive\|dense+intermediate+sparse+very_sparse\|q5 | 242 | 58 | 85.828 | 80.779 | 0.012 | 0.008 | - | - | - |  |  |
| other_inactive\|dense+intermediate\|q2 | 171 | 144 | 72.576 | 83.479 | 0.013 | 0.014 | - | - | - |  |  |
| other_inactive\|dense\|q1 | 187 | 113 | 71.852 | 80.099 | 0.010 | 0.010 | - | - | - |  |  |
| other_inactive\|intermediate\|q1 | 228 | 205 | 72.390 | 78.278 | 0.019 | 0.016 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q1 | 174 | 89 | 72.087 | 66.847 | 0.011 | 0.009 | - | - | - |  |  |
| other_inactive\|sparse+very_sparse\|q2 | 123 | 67 | 66.154 | 103.011 | 0.008 | 0.008 | - | - | - |  |  |
| retired\|dense\|q1 | 70 | 50 | 62.924 | 68.439 | 0.004 | 0.003 | - | - | - |  |  |
| retired\|dense\|q2 | 59 | 74 | 77.719 | 78.969 | 0.003 | 0.004 | - | - | - |  |  |
| retired\|dense\|q3 | 88 | 76 | 72.757 | 92.709 | 0.004 | 0.006 | - | - | - |  |  |
| retired\|dense\|q4 | 91 | 97 | 68.556 | 76.365 | 0.005 | 0.007 | - | - | - |  |  |
| retired\|dense\|q5 | 195 | 129 | 78.495 | 85.192 | 0.009 | 0.010 | - | - | - |  |  |
| retired\|intermediate\|q1 | 236 | 177 | 60.638 | 69.774 | 0.016 | 0.011 | - | - | - |  |  |
| retired\|intermediate\|q2 | 234 | 324 | 61.389 | 73.128 | 0.015 | 0.020 | - | - | - |  |  |
| retired\|intermediate\|q3 | 332 | 314 | 66.197 | 66.409 | 0.021 | 0.020 | - | - | - |  |  |
| retired\|intermediate\|q4 | 287 | 357 | 74.066 | 75.597 | 0.014 | 0.024 | - | - | - |  |  |
| retired\|intermediate\|q5 | 554 | 399 | 77.254 | 81.434 | 0.025 | 0.024 | - | - | - |  |  |
| retired\|sparse\|q1 | 102 | 87 | 45.694 | 68.919 | 0.007 | 0.006 | - | - | - |  |  |
| retired\|sparse\|q2 | 104 | 164 | 50.086 | 53.416 | 0.008 | 0.014 | - | - | - |  |  |
| retired\|sparse\|q3 | 125 | 130 | 57.623 | 75.190 | 0.009 | 0.010 | - | - | - |  |  |
| retired\|sparse\|q4 | 102 | 141 | 57.850 | 52.592 | 0.006 | 0.011 | - | - | - |  |  |
| retired\|sparse\|q5 | 133 | 126 | 65.936 | 76.857 | 0.008 | 0.009 | - | - | - |  |  |
| retired\|very_sparse\|q1 | 324 | 101 | 54.847 | 51.962 | 0.010 | 0.006 | - | - | - |  |  |
| retired\|very_sparse\|q2 | 274 | 219 | 64.697 | 59.684 | 0.011 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q3 | 326 | 212 | 66.477 | 63.718 | 0.013 | 0.011 | - | - | - |  |  |
| retired\|very_sparse\|q4 | 203 | 199 | 74.925 | 68.555 | 0.007 | 0.012 | - | - | - |  |  |
| retired\|very_sparse\|q5 | 275 | 166 | 82.534 | 89.465 | 0.008 | 0.009 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q2 | 133 | 99 | 79.747 | 85.433 | 0.008 | 0.010 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q3 | 102 | 75 | 75.347 | 106.896 | 0.006 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 | 158 | 78 | 89.839 | 88.881 | 0.008 | 0.008 | - | - | - |  |  |
| unemployed\|dense+intermediate\|q1 | 164 | 225 | 61.003 | 84.842 | 0.012 | 0.018 | - | - | - |  |  |
| unemployed\|sparse+very_sparse\|q1 | 103 | 84 | 64.664 | 70.717 | 0.006 | 0.007 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.043 | 0.040 | 0.059 | 0.045 | 0.044 | 0.070 | - | - | - | - | 0.000 | 0.001 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |
| children_6_17\|dense\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|dense\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|dense\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|dense\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|dense\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|intermediate\|q1 | children_6_17\|dense+intermediate\|q1 |
| children_6_17\|intermediate\|q2 | children_6_17\|dense+intermediate\|q2 |
| children_6_17\|intermediate\|q3 | children_6_17\|dense+intermediate\|q3 |
| children_6_17\|intermediate\|q4 | children_6_17\|dense+intermediate\|q4 |
| children_6_17\|intermediate\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| children_6_17\|very_sparse\|q1 | children_6_17\|sparse+very_sparse\|q1 |
| children_6_17\|very_sparse\|q2 | children_6_17\|sparse+very_sparse\|q2 |
| children_6_17\|very_sparse\|q3 | children_6_17\|sparse+very_sparse\|q3 |
| children_6_17\|very_sparse\|q4 | children_6_17\|sparse+very_sparse\|q4 |
| children_6_17\|very_sparse\|q5 | children_6_17\|dense+intermediate+sparse+very_sparse\|q5 |
| employed\|sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| employed\|very_sparse\|q1 | employed\|sparse+very_sparse\|q1 |
| other_inactive\|dense\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|dense\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|dense\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|dense\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|intermediate\|q2 | other_inactive\|dense+intermediate\|q2 |
| other_inactive\|intermediate\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|intermediate\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|intermediate\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| other_inactive\|very_sparse\|q1 | other_inactive\|sparse+very_sparse\|q1 |
| other_inactive\|very_sparse\|q2 | other_inactive\|sparse+very_sparse\|q2 |
| other_inactive\|very_sparse\|q3 | other_inactive\|dense+intermediate+sparse+very_sparse\|q3 |
| other_inactive\|very_sparse\|q4 | other_inactive\|dense+intermediate+sparse+very_sparse\|q4 |
| other_inactive\|very_sparse\|q5 | other_inactive\|dense+intermediate+sparse+very_sparse\|q5 |
| unemployed\|dense\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|dense\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|dense\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|dense\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|dense\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q1 | unemployed\|dense+intermediate\|q1 |
| unemployed\|intermediate\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|intermediate\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|intermediate\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|intermediate\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q1 | unemployed\|sparse+very_sparse\|q1 |
| unemployed\|very_sparse\|q2 | unemployed\|dense+intermediate+sparse+very_sparse\|q2 |
| unemployed\|very_sparse\|q3 | unemployed\|dense+intermediate+sparse+very_sparse\|q3 |
| unemployed\|very_sparse\|q4 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |
| unemployed\|very_sparse\|q5 | unemployed\|dense+intermediate+sparse+very_sparse\|q4+q5 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.393 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### category_x_density_x_income: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: cell levels

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| cell | n_2008 | n_2019 | mean_2008 | mean_2019 | share_2008 | share_2019 | ratio | ratio_ci_low | ratio_ci_high | verdict_10 | verdict_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| couple | 4647 | 3159 | 75.157 | 78.929 | 0.245 | 0.245 | - | - | - |  |  |
| couple_with_children | 5466 | 2956 | 75.610 | 82.963 | 0.485 | 0.445 | - | - | - |  |  |
| other | 361 | 212 | 69.595 | 85.025 | 0.036 | 0.033 | - | - | - |  |  |
| single_parent | 1159 | 822 | 71.747 | 78.503 | 0.086 | 0.111 | - | - | - |  |  |
| single_person | 3972 | 3207 | 74.503 | 82.120 | 0.149 | 0.167 | - | - | - |  |  |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: stability and explained variance

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| eta2_2008 | eta2_2008_low | eta2_2008_high | eta2_2019 | eta2_2019_low | eta2_2019_high | mean_abs_log_ratio | equivalent_10_share | equivalent_15_share | max_abs_log_ratio | excluded_share_2008 | excluded_share_2019 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.000 | 0.003 | 0.001 | 0.000 | 0.003 | - | - | - | - | 0.000 | 0.000 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed full-sample merges

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| original | merged |
| --- | --- |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| observed_2019 | predicted_2019 | observed_over_predicted | ratio_low | ratio_high | mix_term | fallback_share | ks_d | ks_low | ks_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 81.408 | - | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### household_type: fixed-cell deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; days with scoped trips.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person mode use and user-day minutes

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| mode | n_2008 | n_2019 | use_2008 | use_2019 | user_minutes_2008 | user_minutes_2019 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 4503 | 3031 | 0.253 | 0.268 | 37.848 | 39.908 |
| bike | 531 | 310 | 0.032 | 0.030 | 43.940 | 50.406 |
| car_driver | 9172 | 5930 | 0.472 | 0.457 | 67.471 | 73.968 |
| car_passenger | 2346 | 1826 | 0.151 | 0.159 | 47.232 | 53.100 |
| urban_pt | 1518 | 990 | 0.077 | 0.099 | 74.855 | 80.039 |
| train | 703 | 295 | 0.029 | 0.031 | 146.139 | 143.278 |
| other | 712 | 391 | 0.051 | 0.039 | 68.717 | 82.804 |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode model

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| observed_2008 | observed_2019 | predicted_2019 | use_effect | use_effect_low | use_effect_high | time_effect | time_effect_low | time_effect_high | ks_d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 63.533 | 69.973 | - | - | - | - | - | - | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

### Per-person fixed-mode deciles

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km), Monday-Friday; per person, zero-trip days included and open days removed.

| decile | predicted | observed |
| --- | --- | --- |
| 1 | - | - |
| 2 | - | - |
| 3 | - | - |
| 4 | - | - |
| 5 | - | - |
| 6 | - | - |
| 7 | - | - |
| 8 | - | - |
| 9 | - | - |

n: 2008 15605, 2019 10356 travel days; cell n is respondents. Sources: ENTD 2008 and EMP 2019 weekday survey caches, section 9.9.

ENTD 2008 day-table coverage beyond 80 km not established; not compared

## Cross-scope comparison

Scope: the combinations listed below, Monday-Friday, days with trips.

| scope | grouping | eta2_2008 | eta2_2019 | mean_abs_log_ratio | ratio | ratio_low | ratio_high | status |
|---|---|---|---|---|---|---|---|---|
| round-dest-local | day_mode_group_x_income | 0.154 | 0.169 | 0.086 | 1.068 | 1.047 | 1.089 |  |
| round-dest-local | day_mode_group_x_category | 0.175 | 0.199 | 0.081 | 1.070 | 1.047 | 1.092 |  |
| round-dest-local | day_mode_group_x_vehicles | 0.149 | 0.176 | - | 1.070 | 1.048 | 1.091 |  |
| round-dest-local | day_mode_group | 0.145 | 0.158 | 0.070 | 1.070 | 1.049 | 1.093 |  |
| round-dest-local | day_mode_group_x_density | 0.150 | 0.164 | 0.075 | 1.071 | 1.049 | 1.094 |  |
| round-dest-local | income | 0.007 | 0.007 | 0.077 | 1.080 | 1.056 | 1.101 |  |
| round-dest-local | vehicles | 0.001 | 0.006 | - | 1.080 | 1.055 | 1.101 |  |
| round-dest-local | density | 0.004 | 0.007 | 0.077 | 1.080 | 1.056 | 1.102 |  |
| round-dest-local | none | 0.000 | 0.000 | 0.078 | 1.081 | 1.057 | 1.101 |  |
| round-dest-local | category_x_density_x_income | 0.051 | 0.057 | 0.103 | 1.082 | 1.057 | 1.107 |  |
| round-dest-local | household_type | 0.001 | 0.002 | 0.079 | 1.083 | 1.059 | 1.104 |  |
| round-dest-local | day_purpose | 0.020 | 0.015 | - | 1.085 | 1.061 | 1.106 |  |
| round-dest-local | category | 0.033 | 0.041 | 0.082 | 1.088 | 1.064 | 1.110 |  |
| round-dest-local | age_band | 0.041 | 0.050 | 0.092 | 1.099 | 1.076 | 1.121 |  |
| round-dest-daytable | age_band | 0.040 | 0.041 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | category | 0.037 | 0.035 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | category_x_density_x_income | 0.055 | 0.052 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_mode_group | 0.147 | 0.133 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_mode_group_x_category | 0.179 | 0.170 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_mode_group_x_density | 0.152 | 0.141 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_mode_group_x_income | 0.157 | 0.142 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_mode_group_x_vehicles | 0.150 | 0.146 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | day_purpose | 0.022 | 0.011 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | density | 0.002 | 0.006 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | household_type | 0.002 | 0.002 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | income | 0.010 | 0.007 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | none | 0.000 | 0.000 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-dest-daytable | vehicles | 0.000 | 0.004 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-local | day_mode_group_x_category | 0.151 | 0.161 | 0.104 | 1.087 | 1.060 | 1.110 |  |
| round-allpurp-local | day_mode_group_x_income | 0.133 | 0.128 | 0.108 | 1.088 | 1.062 | 1.111 |  |
| round-allpurp-local | day_mode_group_x_vehicles | 0.126 | 0.134 | - | 1.090 | 1.066 | 1.114 |  |
| round-allpurp-local | day_mode_group | 0.124 | 0.117 | 0.093 | 1.091 | 1.066 | 1.114 |  |
| round-allpurp-local | day_mode_group_x_density | 0.128 | 0.120 | 0.097 | 1.091 | 1.067 | 1.114 |  |
| round-allpurp-local | category_x_density_x_income | 0.041 | 0.051 | 0.116 | 1.097 | 1.068 | 1.120 |  |
| round-allpurp-local | density | 0.004 | 0.004 | 0.093 | 1.097 | 1.069 | 1.121 |  |
| round-allpurp-local | income | 0.008 | 0.007 | 0.093 | 1.097 | 1.069 | 1.120 |  |
| round-allpurp-local | vehicles | 0.000 | 0.005 | - | 1.097 | 1.069 | 1.120 |  |
| round-allpurp-local | none | 0.000 | 0.000 | 0.093 | 1.098 | 1.070 | 1.121 |  |
| round-allpurp-local | household_type | 0.000 | 0.001 | 0.095 | 1.100 | 1.073 | 1.121 |  |
| round-allpurp-local | day_purpose | 0.011 | 0.010 | - | 1.100 | 1.072 | 1.124 |  |
| round-allpurp-local | category | 0.023 | 0.037 | 0.094 | 1.102 | 1.075 | 1.127 |  |
| round-allpurp-local | age_band | 0.028 | 0.045 | 0.099 | 1.110 | 1.084 | 1.135 |  |
| round-allpurp-daytable | age_band | 0.029 | 0.039 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | category | 0.028 | 0.033 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | category_x_density_x_income | 0.046 | 0.048 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_mode_group | 0.128 | 0.102 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_mode_group_x_category | 0.159 | 0.141 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_mode_group_x_density | 0.132 | 0.106 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_mode_group_x_income | 0.139 | 0.112 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_mode_group_x_vehicles | 0.129 | 0.114 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | day_purpose | 0.012 | 0.008 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | density | 0.003 | 0.004 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | household_type | 0.001 | 0.001 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | income | 0.011 | 0.008 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | none | 0.000 | 0.000 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| round-allpurp-daytable | vehicles | 0.000 | 0.003 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-local | day_mode_group_x_income | 0.150 | 0.168 | 0.081 | 1.061 | 1.039 | 1.082 |  |
| alldays-dest-local | day_mode_group_x_vehicles | 0.144 | 0.177 | - | 1.063 | 1.041 | 1.085 |  |
| alldays-dest-local | day_mode_group | 0.141 | 0.159 | 0.063 | 1.064 | 1.041 | 1.086 |  |
| alldays-dest-local | day_mode_group_x_density | 0.145 | 0.165 | 0.073 | 1.064 | 1.040 | 1.085 |  |
| alldays-dest-local | day_mode_group_x_category | 0.171 | 0.197 | 0.083 | 1.065 | 1.044 | 1.087 |  |
| alldays-dest-local | income | 0.006 | 0.006 | 0.072 | 1.074 | 1.049 | 1.095 |  |
| alldays-dest-local | vehicles | 0.001 | 0.006 | - | 1.074 | 1.049 | 1.096 |  |
| alldays-dest-local | density | 0.003 | 0.007 | 0.071 | 1.074 | 1.050 | 1.097 |  |
| alldays-dest-local | none | 0.000 | 0.000 | 0.072 | 1.075 | 1.049 | 1.096 |  |
| alldays-dest-local | household_type | 0.001 | 0.002 | 0.073 | 1.076 | 1.052 | 1.098 |  |
| alldays-dest-local | category_x_density_x_income | 0.048 | 0.057 | 0.100 | 1.079 | 1.053 | 1.102 |  |
| alldays-dest-local | day_purpose | 0.020 | 0.014 | - | 1.079 | 1.055 | 1.102 |  |
| alldays-dest-local | category | 0.033 | 0.041 | 0.079 | 1.084 | 1.059 | 1.107 |  |
| alldays-dest-local | age_band | 0.041 | 0.050 | 0.088 | 1.093 | 1.068 | 1.115 |  |
| alldays-dest-daytable | age_band | 0.037 | 0.036 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | category | 0.034 | 0.032 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | category_x_density_x_income | 0.050 | 0.050 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_mode_group | 0.134 | 0.116 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_mode_group_x_category | 0.166 | 0.151 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_mode_group_x_density | 0.137 | 0.127 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_mode_group_x_income | 0.145 | 0.127 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_mode_group_x_vehicles | 0.137 | 0.126 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | day_purpose | 0.015 | 0.005 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | density | 0.002 | 0.005 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | household_type | 0.001 | 0.002 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | income | 0.012 | 0.007 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | none | 0.000 | 0.000 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-dest-daytable | vehicles | 0.000 | 0.003 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-local | day_mode_group_x_income | 0.131 | 0.130 | 0.102 | 1.079 | 1.055 | 1.102 |  |
| alldays-allpurp-local | day_mode_group_x_category | 0.150 | 0.162 | 0.104 | 1.081 | 1.057 | 1.102 |  |
| alldays-allpurp-local | day_mode_group_x_vehicles | 0.124 | 0.136 | - | 1.083 | 1.059 | 1.107 |  |
| alldays-allpurp-local | day_mode_group | 0.121 | 0.120 | 0.085 | 1.083 | 1.059 | 1.107 |  |
| alldays-allpurp-local | day_mode_group_x_density | 0.125 | 0.124 | 0.092 | 1.083 | 1.059 | 1.106 |  |
| alldays-allpurp-local | density | 0.003 | 0.004 | 0.085 | 1.089 | 1.061 | 1.114 |  |
| alldays-allpurp-local | vehicles | 0.000 | 0.005 | - | 1.090 | 1.063 | 1.112 |  |
| alldays-allpurp-local | income | 0.007 | 0.006 | 0.086 | 1.090 | 1.062 | 1.110 |  |
| alldays-allpurp-local | none | 0.000 | 0.000 | 0.086 | 1.090 | 1.063 | 1.113 |  |
| alldays-allpurp-local | household_type | 0.000 | 0.001 | 0.087 | 1.091 | 1.065 | 1.113 |  |
| alldays-allpurp-local | category_x_density_x_income | 0.039 | 0.051 | 0.112 | 1.091 | 1.063 | 1.114 |  |
| alldays-allpurp-local | day_purpose | 0.011 | 0.009 | - | 1.093 | 1.066 | 1.115 |  |
| alldays-allpurp-local | category | 0.024 | 0.037 | 0.089 | 1.097 | 1.070 | 1.119 |  |
| alldays-allpurp-local | age_band | 0.030 | 0.045 | 0.094 | 1.103 | 1.077 | 1.125 |  |
| alldays-allpurp-daytable | age_band | 0.027 | 0.032 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | category | 0.025 | 0.029 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | category_x_density_x_income | 0.043 | 0.045 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_mode_group | 0.113 | 0.092 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_mode_group_x_category | 0.144 | 0.127 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_mode_group_x_density | 0.117 | 0.100 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_mode_group_x_income | 0.127 | 0.102 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_mode_group_x_vehicles | 0.116 | 0.103 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | day_purpose | 0.006 | 0.002 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | density | 0.002 | 0.004 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | household_type | 0.000 | 0.001 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | income | 0.014 | 0.008 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | none | 0.000 | 0.000 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| alldays-allpurp-daytable | vehicles | 0.000 | 0.003 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n: see the per-scope tables above. Sources: ENTD 2008 and EMP 2019.
