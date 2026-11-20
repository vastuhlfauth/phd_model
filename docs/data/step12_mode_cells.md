# Daily time and energy by mode

ENTD 2008 and EMP 2019, weighted weekday estimates, section 9.9.
Cells under 50 days are hidden; under 100 are flagged. Hidden cells remain in national and median computations.
All eight scopes are included. Day-table cross-year results are suppressed because coverage is not comparable.
Subgroup distances use the speed-corrected cache; decomposition uses published distance or 2019 rounded crow-fly distance. Selection terms and rounding bounds are reported separately.
Reweighting targets 2008 category × density × income; support loss and parent fallback are reported in the CSV.
Energy is kJ above rest, from step 11, reference scope only. Other-only days and open days are excluded from energy denominators; non-users have zero attributable energy. Day-mode per-person energy is undefined. Mixed-mode days sum known energies.

## Detailed tables

- [mode_cells](step12_mode_cells/mode_cells.csv)
- [reweighted](step12_mode_cells/reweighted.csv)
- [decomposition](step12_mode_cells/decomposition.csv)
- [rounding](step12_mode_cells/rounding.csv)
- [energy](step12_mode_cells/energy.csv)
- [collapse](step12_mode_cells/collapse.csv)

## Mode, subgroup and composition

## Round-trip days · destination purposes · local (≤ 80 km)

### Subgroup mode-user days

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 80 | 58 | True | True | 42.807 | 47.427 | 8.046 | 8.141 | 11.278 | 10.299 | 1.108 | 0.820 | 1.405 | inconclusive | inconclusive | 0.155 | 0.211 | 7.923 | -3.076 | 0.000 | 3.846 | 4.279 | 0.000 |  |
| bike | density | intermediate | 152 | 114 | False | False | 39.069 | 42.766 | 6.970 | 8.658 | 10.704 | 12.147 | 1.095 | 0.894 | 1.296 | inconclusive | inconclusive | 0.109 | 0.100 | 2.035 | -0.927 | 0.000 | 6.172 | -2.708 | 0.000 |  |
| bike | density | sparse+very_sparse | 169 | 81 | False | True | 34.048 | 28.057 | 5.419 | 5.148 | 9.549 | 11.010 | 0.824 | 0.609 | 1.152 | inconclusive | inconclusive | 0.180 | 0.193 | -7.153 | 3.241 | 0.000 | -12.320 | 1.074 | 0.000 |  |
| bike | population | children_6_17 | 67 | 28 | True | True | 27.357 | - | 4.706 | - | 10.322 | - | - | - | - |  |  | 0.189 | - | -11.001 | 0.397 | 0.000 | - | - | - |  |
| bike | population | employed | 178 | 128 | False | False | 46.665 | 41.898 | 8.141 | 8.700 | 10.467 | 12.459 | 0.898 | 0.726 | 1.106 | inconclusive | inconclusive | 0.145 | 0.091 | 8.775 | -0.071 | 0.000 | 6.307 | -3.711 | 0.000 |  |
| bike | population | other_inactive | 34 | 16 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | population | retired | 105 | 64 | False | True | 36.415 | 38.751 | 5.781 | 7.056 | 9.525 | 10.925 | 1.064 | 0.782 | 1.454 | inconclusive | inconclusive | 0.106 | 0.065 | -4.989 | 3.443 | 0.000 | -2.110 | 1.558 | 0.000 |  |
| bike | population | unemployed | 17 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | income | q1+q2+q3 | 217 | 137 | False | False | 39.355 | 38.160 | 6.486 | 6.607 | 9.888 | 10.388 | 0.970 | 0.790 | 1.178 | inconclusive | inconclusive | 0.050 | 0.077 | -0.740 | 2.134 | 0.000 | -4.643 | 3.500 | 0.000 |  |
| bike | income | q4 | 74 | 50 | True | True | 36.761 | 36.992 | 7.974 | 7.642 | 13.014 | 12.394 | 1.006 | 0.736 | 1.424 | inconclusive | inconclusive | 0.098 | 0.109 | 7.000 | -8.200 | 0.000 | 0.978 | -3.288 | 0.000 |  |
| bike | income | q5 | 110 | 66 | False | True | 34.854 | 44.478 | 5.805 | 9.175 | 9.994 | 12.377 | 1.276 | 1.013 | 1.612 | inconclusive | inconclusive | 0.107 | 0.114 | -4.730 | 1.623 | 0.000 | 8.723 | -3.548 | 0.000 |  |
| bike | vehicles | 0 | 96 | 55 | True | True | 41.514 | 51.784 | 7.468 | 7.839 | 10.794 | 9.082 | 1.247 | 0.942 | 1.601 | inconclusive | inconclusive | 0.144 | 0.168 | 4.841 | -1.288 | 0.000 | 2.313 | 10.168 | 0.000 |  |
| bike | vehicles | 1 | 149 | 98 | False | True | 42.953 | 40.413 | 7.616 | 8.442 | 10.639 | 12.533 | 0.941 | 0.773 | 1.214 | inconclusive | inconclusive | 0.123 | 0.061 | 5.719 | -0.727 | 0.000 | 4.991 | -3.880 | 0.000 |  |
| bike | vehicles | 2+ | 156 | 97 | False | True | 31.560 | 32.105 | 5.247 | 6.471 | 9.975 | 12.093 | 1.017 | 0.806 | 1.261 | inconclusive | inconclusive | 0.135 | 0.108 | -8.010 | 1.610 | 0.000 | -5.004 | -2.193 | 0.000 |  |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | couple | 119 | 73 | False | True | 35.623 | 34.911 | 5.644 | 7.013 | 9.507 | 12.053 | 0.980 | 0.773 | 1.240 | inconclusive | inconclusive | 0.121 | 0.081 | -5.816 | 3.478 | 0.000 | -2.231 | -2.161 | 0.000 |  |
| bike | household_type | couple_with_children | 134 | 76 | False | True | 37.358 | 37.345 | 6.648 | 7.486 | 10.677 | 12.027 | 1.000 | 0.781 | 1.223 | inconclusive | inconclusive | 0.052 | 0.050 | 0.207 | -0.810 | 0.000 | 0.193 | -2.151 | 0.000 |  |
| bike | household_type | other | 11 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_parent | 29 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_person | 108 | 73 | False | True | 44.340 | 45.581 | 8.351 | 7.933 | 11.300 | 10.442 | 1.028 | 0.855 | 1.286 | inconclusive | inconclusive | 0.240 | 0.131 | 9.591 | -3.212 | 0.000 | 2.672 | 3.607 | 0.000 |  |
| bike | day_purpose | other | 204 | 123 | False | False | 35.471 | 37.730 | 5.705 | 6.894 | 9.650 | 10.964 | 1.064 | 0.840 | 1.327 | inconclusive | inconclusive | 0.057 | 0.083 | -5.410 | 2.920 | 0.000 | -2.976 | 1.403 | 0.000 |  |
| bike | day_purpose | work_study | 197 | 130 | False | False | 40.667 | 40.720 | 7.596 | 7.947 | 11.207 | 11.710 | 1.001 | 0.837 | 1.228 | inconclusive | inconclusive | 0.061 | 0.074 | 5.456 | -2.750 | 0.000 | 2.596 | -1.178 | 0.000 |  |
| car_driver | density | dense | 629 | 429 | False | False | 61.670 | 67.371 | 28.548 | 27.779 | 27.775 | 24.739 | 1.092 | 0.997 | 1.189 | inconclusive | inconclusive | 0.056 | 0.070 | -14.813 | 16.187 | 0.000 | -20.208 | 23.301 | 0.000 |  |
| car_driver | density | intermediate | 3137 | 2411 | False | False | 60.336 | 64.853 | 31.635 | 33.162 | 31.459 | 30.680 | 1.075 | 1.033 | 1.124 | equivalent | inconclusive | 0.011 | 0.013 | -8.460 | 8.499 | 0.000 | -8.389 | 8.965 | 0.000 |  |
| car_driver | density | sparse | 1204 | 1012 | False | False | 58.260 | 60.093 | 37.757 | 39.695 | 38.885 | 39.633 | 1.031 | 0.943 | 1.114 | equivalent | inconclusive | 0.052 | 0.048 | 2.173 | -4.209 | 0.000 | 3.102 | -7.286 | 0.000 |  |
| car_driver | density | very_sparse | 3366 | 1721 | False | False | 61.114 | 65.662 | 44.508 | 46.812 | 43.697 | 42.775 | 1.074 | 1.019 | 1.125 | equivalent | inconclusive | 0.028 | 0.031 | 12.211 | -11.393 | 0.000 | 13.956 | -12.571 | 0.000 |  |
| car_driver | population | children_6_17 | 77 | 41 | True | True | 44.534 | - | 25.745 | - | 34.686 | - | - | - | - |  |  | 0.195 | - | -18.012 | 2.250 | 0.000 | - | - | - |  |
| car_driver | population | employed | 5223 | 3054 | False | False | 64.261 | 69.445 | 39.968 | 42.953 | 37.318 | 37.111 | 1.081 | 1.042 | 1.120 | equivalent | inconclusive | 0.046 | 0.075 | 5.826 | -1.860 | 0.000 | 8.606 | -3.439 | 0.000 |  |
| car_driver | population | other_inactive | 599 | 287 | False | False | 54.233 | 60.981 | 29.774 | 34.090 | 32.939 | 33.541 | 1.124 | 1.000 | 1.272 | inconclusive | inconclusive | 0.088 | 0.083 | -11.493 | 5.431 | 0.000 | -6.407 | 3.111 | 0.000 |  |
| car_driver | population | retired | 2118 | 1924 | False | False | 51.932 | 52.856 | 28.790 | 26.773 | 33.263 | 30.391 | 1.018 | 0.959 | 1.078 | equivalent | equivalent | 0.106 | 0.162 | -13.132 | 4.769 | 0.000 | -20.080 | 8.658 | 0.000 |  |
| car_driver | population | unemployed | 319 | 263 | False | False | 56.883 | 62.378 | 34.166 | 32.248 | 36.038 | 31.018 | 1.097 | 0.963 | 1.230 | inconclusive | inconclusive | 0.049 | 0.063 | -3.707 | 0.294 | 0.000 | -9.997 | 8.098 | 0.000 |  |
| car_driver | income | q1 | 976 | 625 | False | False | 53.368 | 59.740 | 31.179 | 32.467 | 35.053 | 32.608 | 1.119 | 1.022 | 1.236 | inconclusive | inconclusive | 0.093 | 0.077 | -8.786 | 1.857 | 0.000 | -9.366 | 4.828 | 0.000 |  |
| car_driver | income | q2 | 1321 | 1041 | False | False | 56.555 | 58.423 | 34.327 | 33.999 | 36.418 | 34.917 | 1.033 | 0.973 | 1.109 | equivalent | inconclusive | 0.045 | 0.055 | -3.421 | -0.320 | 0.000 | -6.437 | 0.582 | 0.000 |  |
| car_driver | income | q3 | 1730 | 1173 | False | False | 58.137 | 62.558 | 34.839 | 37.951 | 35.955 | 36.400 | 1.076 | 0.992 | 1.144 | equivalent | inconclusive | 0.035 | 0.040 | -2.592 | 0.434 | 0.000 | 0.316 | -2.036 | 0.000 |  |
| car_driver | income | q4 | 1854 | 1338 | False | False | 62.622 | 67.118 | 39.189 | 39.845 | 37.548 | 35.619 | 1.072 | 1.015 | 1.135 | equivalent | inconclusive | 0.040 | 0.036 | 4.541 | -2.215 | 0.000 | 3.525 | -0.684 | 0.000 |  |
| car_driver | income | q5 | 2455 | 1396 | False | False | 66.667 | 69.890 | 39.590 | 41.138 | 35.631 | 35.317 | 1.048 | 0.996 | 1.104 | equivalent | inconclusive | 0.086 | 0.068 | 5.332 | 1.039 | 0.000 | 5.739 | -0.127 | 0.000 |  |
| car_driver | vehicles | 0 | 56 | 56 | True | True | 67.306 | 64.400 | 40.737 | 33.813 | 36.315 | 31.502 | 0.957 | 0.673 | 1.389 | inconclusive | inconclusive | 0.175 | 0.136 | 7.178 | -0.168 | 0.000 | -7.109 | 7.232 | 0.000 |  |
| car_driver | vehicles | 1 | 3279 | 2500 | False | False | 58.485 | 60.810 | 32.312 | 31.701 | 33.150 | 31.279 | 1.040 | 0.994 | 1.098 | equivalent | equivalent | 0.059 | 0.038 | -7.070 | 5.259 | 0.000 | -10.940 | 7.474 | 0.000 |  |
| car_driver | vehicles | 2+ | 5001 | 3010 | False | False | 61.335 | 66.487 | 38.880 | 41.658 | 38.033 | 37.594 | 1.084 | 1.047 | 1.124 | equivalent | inconclusive | 0.037 | 0.027 | 4.011 | -2.972 | 0.000 | 6.418 | -4.208 | 0.000 |  |
| car_driver | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_driver | household_type | couple | 2875 | 1953 | False | False | 57.712 | 58.592 | 34.179 | 33.672 | 35.534 | 34.481 | 1.015 | 0.962 | 1.075 | equivalent | equivalent | 0.050 | 0.082 | -3.711 | 1.126 | 0.000 | -7.038 | 1.353 | 0.000 |  |
| car_driver | household_type | couple_with_children | 3140 | 1589 | False | False | 63.588 | 70.014 | 39.511 | 43.309 | 37.282 | 37.115 | 1.101 | 1.058 | 1.157 | inconclusive | inconclusive | 0.046 | 0.071 | 5.082 | -1.790 | 0.000 | 9.197 | -3.459 | 0.000 |  |
| car_driver | household_type | other | 170 | 86 | False | True | 56.830 | 58.346 | 34.459 | 31.606 | 36.381 | 32.502 | 1.027 | 0.861 | 1.215 | inconclusive | inconclusive | 0.078 | 0.125 | -3.205 | -0.260 | 0.000 | -10.903 | 4.972 | 0.000 |  |
| car_driver | household_type | single_parent | 520 | 340 | False | False | 54.418 | 64.414 | 29.656 | 35.608 | 32.698 | 33.168 | 1.184 | 1.074 | 1.310 | inconclusive | inconclusive | 0.059 | 0.037 | -11.739 | 5.862 | 0.000 | -3.781 | 3.918 | 0.000 |  |
| car_driver | household_type | single_person | 1631 | 1605 | False | False | 57.121 | 59.785 | 33.151 | 32.131 | 34.822 | 32.246 | 1.047 | 0.993 | 1.117 | equivalent | inconclusive | 0.053 | 0.060 | -5.484 | 2.309 | 0.000 | -10.014 | 5.522 | 0.000 |  |
| car_driver | day_purpose | other | 3992 | 3051 | False | False | 53.349 | 56.406 | 30.919 | 30.608 | 34.773 | 32.558 | 1.057 | 1.009 | 1.108 | equivalent | inconclusive | 0.095 | 0.118 | -9.259 | 2.313 | 0.000 | -12.658 | 4.786 | 0.000 |  |
| car_driver | day_purpose | work_study | 4344 | 2522 | False | False | 65.871 | 70.907 | 40.796 | 43.789 | 37.159 | 37.053 | 1.076 | 1.041 | 1.117 | equivalent | inconclusive | 0.077 | 0.099 | 7.191 | -1.615 | 0.000 | 9.999 | -3.370 | 0.000 |  |
| car_passenger | density | dense | 184 | 160 | False | False | 38.875 | 47.481 | 17.189 | 17.889 | 26.530 | 22.606 | 1.221 | 1.007 | 1.501 | inconclusive | inconclusive | 0.062 | 0.113 | -12.169 | 10.885 | 0.000 | -14.450 | 16.609 | 0.000 |  |
| car_passenger | density | intermediate | 794 | 767 | False | False | 38.536 | 44.101 | 19.320 | 20.942 | 30.080 | 28.492 | 1.144 | 1.032 | 1.249 | inconclusive | inconclusive | 0.029 | 0.035 | -7.519 | 5.896 | 0.000 | -6.879 | 5.658 | 0.000 |  |
| car_passenger | density | sparse | 281 | 288 | False | False | 40.562 | 43.231 | 25.519 | 26.119 | 37.748 | 36.250 | 1.066 | 0.899 | 1.248 | inconclusive | inconclusive | 0.060 | 0.055 | 3.519 | -3.116 | 0.000 | 2.967 | -5.058 | 0.000 |  |
| car_passenger | density | very_sparse | 766 | 413 | False | False | 42.870 | 48.801 | 30.355 | 32.765 | 42.485 | 40.284 | 1.138 | 1.018 | 1.258 | inconclusive | inconclusive | 0.075 | 0.065 | 10.820 | -8.109 | 0.000 | 13.817 | -10.337 | 0.000 |  |
| car_passenger | population | children_6_17 | 612 | 442 | False | False | 31.331 | 35.726 | 16.592 | 17.197 | 31.774 | 28.881 | 1.140 | 1.023 | 1.248 | inconclusive | inconclusive | 0.123 | 0.126 | -12.209 | 3.381 | 0.000 | -14.154 | 4.558 | 0.000 |  |
| car_passenger | population | employed | 566 | 319 | False | False | 43.605 | 52.121 | 25.745 | 31.343 | 35.425 | 36.081 | 1.195 | 1.059 | 1.348 | inconclusive | inconclusive | 0.072 | 0.091 | 4.019 | -0.572 | 0.000 | 12.130 | -5.330 | 0.000 |  |
| car_passenger | population | other_inactive | 236 | 181 | False | False | 49.386 | 50.454 | 26.302 | 24.966 | 31.955 | 29.690 | 1.022 | 0.837 | 1.276 | inconclusive | inconclusive | 0.149 | 0.075 | 5.238 | 3.989 | 0.000 | 1.047 | 4.085 | 0.000 |  |
| car_passenger | population | retired | 527 | 612 | False | False | 52.027 | 56.472 | 35.162 | 33.209 | 40.550 | 35.283 | 1.085 | 0.948 | 1.210 | inconclusive | inconclusive | 0.149 | 0.167 | 18.688 | -6.821 | 0.000 | 15.572 | -4.421 | 0.000 |  |
| car_passenger | population | unemployed | 83 | 72 | True | True | 49.086 | 44.592 | 31.388 | 23.006 | 38.366 | 30.955 | 0.908 | 0.731 | 1.124 | inconclusive | inconclusive | 0.206 | 0.128 | 13.083 | -4.156 | 0.000 | -2.691 | 1.962 | 0.000 |  |
| car_passenger | income | q1 | 358 | 309 | False | False | 39.423 | 44.792 | 21.004 | 20.989 | 31.967 | 28.116 | 1.136 | 0.974 | 1.273 | inconclusive | inconclusive | 0.054 | 0.042 | -4.279 | 3.542 | 0.000 | -6.831 | 6.301 | 0.000 |  |
| car_passenger | income | q2 | 410 | 373 | False | False | 36.036 | 45.976 | 20.949 | 26.189 | 34.879 | 34.177 | 1.276 | 1.124 | 1.430 | inconclusive | different | 0.084 | 0.046 | -4.193 | 0.070 | 0.000 | 3.182 | -2.527 | 0.000 |  |
| car_passenger | income | q3 | 416 | 332 | False | False | 45.805 | 45.816 | 27.452 | 26.441 | 35.960 | 34.627 | 1.000 | 0.867 | 1.165 | inconclusive | inconclusive | 0.101 | 0.050 | 6.876 | -1.230 | 0.000 | 3.614 | -3.119 | 0.000 |  |
| car_passenger | income | q4 | 389 | 330 | False | False | 37.972 | 44.111 | 22.725 | 22.961 | 35.907 | 31.231 | 1.162 | 1.045 | 1.301 | inconclusive | inconclusive | 0.046 | 0.025 | -1.125 | -1.062 | 0.000 | -2.765 | 1.555 | 0.000 |  |
| car_passenger | income | q5 | 452 | 284 | False | False | 42.444 | 45.905 | 25.077 | 25.423 | 35.450 | 33.228 | 1.082 | 0.958 | 1.199 | inconclusive | inconclusive | 0.050 | 0.037 | 2.878 | -0.593 | 0.000 | 1.825 | -1.241 | 0.000 |  |
| car_passenger | vehicles | 0 | 253 | 248 | False | False | 39.391 | 44.908 | 19.709 | 20.611 | 30.021 | 27.537 | 1.140 | 0.972 | 1.336 | inconclusive | inconclusive | 0.064 | 0.071 | -6.808 | 6.040 | 0.000 | -7.662 | 7.248 | 0.000 |  |
| car_passenger | vehicles | 1 | 730 | 617 | False | False | 41.589 | 45.786 | 23.112 | 23.121 | 33.343 | 30.299 | 1.101 | 0.992 | 1.220 | inconclusive | inconclusive | 0.059 | 0.026 | -0.486 | 1.916 | 0.000 | -2.500 | 2.965 | 0.000 |  |
| car_passenger | vehicles | 2+ | 1042 | 760 | False | False | 39.332 | 45.043 | 24.147 | 25.897 | 36.835 | 34.496 | 1.145 | 1.056 | 1.249 | inconclusive | inconclusive | 0.043 | 0.020 | 1.268 | -2.095 | 0.000 | 2.642 | -2.921 | 0.000 |  |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_passenger | household_type | couple | 589 | 552 | False | False | 52.363 | 56.104 | 33.975 | 33.389 | 38.931 | 35.707 | 1.071 | 0.960 | 1.197 | inconclusive | inconclusive | 0.153 | 0.165 | 17.173 | -4.969 | 0.000 | 15.792 | -5.010 | 0.000 |  |
| car_passenger | household_type | couple_with_children | 893 | 559 | False | False | 36.229 | 40.766 | 20.242 | 21.345 | 33.523 | 31.416 | 1.125 | 1.032 | 1.240 | inconclusive | inconclusive | 0.051 | 0.065 | -5.514 | 1.584 | 0.000 | -5.798 | 1.243 | 0.000 |  |
| car_passenger | household_type | other | 64 | 37 | True | True | 42.974 | - | 28.092 | - | 39.221 | - | - | - | - |  |  | 0.059 | - | 7.614 | -4.798 | 0.000 | - | - | - |  |
| car_passenger | household_type | single_parent | 158 | 147 | False | False | 40.096 | 40.243 | 20.513 | 18.448 | 30.695 | 27.506 | 1.004 | 0.840 | 1.214 | inconclusive | inconclusive | 0.050 | 0.056 | -5.265 | 5.202 | 0.000 | -11.993 | 6.914 | 0.000 |  |
| car_passenger | household_type | single_person | 321 | 333 | False | False | 36.489 | 48.423 | 20.196 | 24.846 | 33.210 | 30.786 | 1.327 | 1.146 | 1.549 | inconclusive | different | 0.081 | 0.058 | -5.619 | 1.949 | 0.000 | 0.799 | 2.302 | 0.000 |  |
| car_passenger | day_purpose | other | 1106 | 1083 | False | False | 48.437 | 54.089 | 30.538 | 31.753 | 37.829 | 35.223 | 1.117 | 1.028 | 1.215 | inconclusive | inconclusive | 0.115 | 0.113 | 11.782 | -3.504 | 0.000 | 13.006 | -4.238 | 0.000 |  |
| car_passenger | day_purpose | work_study | 919 | 545 | False | False | 33.171 | 35.678 | 17.352 | 16.367 | 31.387 | 27.524 | 1.076 | 0.977 | 1.181 | inconclusive | inconclusive | 0.097 | 0.124 | -10.912 | 3.924 | 0.000 | -16.137 | 6.494 | 0.000 |  |
| other | density | dense+intermediate | 258 | 168 | False | False | 57.518 | 55.091 | 23.350 | 22.798 | 24.362 | 24.829 | 0.958 | 0.815 | 1.128 | inconclusive | inconclusive | 0.036 | 0.065 | -4.531 | 3.346 | -0.269 | -12.602 | 8.286 | 0.000 |  |
| other | density | sparse+very_sparse | 357 | 152 | False | False | 60.052 | 63.843 | 26.642 | 34.186 | 26.835 | 32.128 | 1.063 | 0.923 | 1.247 | inconclusive | inconclusive | 0.027 | 0.067 | 3.218 | -2.335 | 0.196 | 11.391 | -6.956 | 0.000 |  |
| other | population | children_6_17 | 266 | 86 | False | True | 57.484 | 57.204 | 21.667 | 19.108 | 22.615 | 20.042 | 0.995 | 0.829 | 1.184 | inconclusive | inconclusive | 0.048 | 0.082 | -8.887 | 7.677 | -0.278 | -23.131 | 20.928 | 0.000 |  |
| other | population | employed | 246 | 140 | False | False | 64.140 | 61.104 | 32.634 | 33.670 | 30.934 | 33.062 | 0.953 | 0.805 | 1.174 | inconclusive | inconclusive | 0.107 | 0.049 | 15.806 | -11.159 | 0.520 | 10.225 | -8.528 | 0.000 |  |
| other | population | other_inactive | 36 | 24 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | population | retired | 57 | 61 | True | True | 50.196 | 59.719 | 21.753 | 33.881 | 26.038 | 34.040 | 1.190 | 0.850 | 1.739 | inconclusive | inconclusive | 0.185 | 0.121 | -8.098 | -0.496 | -0.183 | 10.481 | -10.168 | 0.000 |  |
| other | population | unemployed | 10 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | income | q1 | 105 | 58 | False | True | 59.277 | 67.488 | 26.602 | 37.891 | 26.926 | 33.687 | 1.139 | 0.897 | 1.476 | inconclusive | inconclusive | 0.039 | 0.190 | 3.108 | -2.520 | -0.283 | 18.236 | -10.155 | 0.000 |  |
| other | income | q2 | 149 | 71 | False | True | 64.678 | 45.961 | 25.082 | 19.147 | 23.524 | 24.996 | 0.711 | 0.579 | 0.891 | inconclusive | different | 0.090 | 0.124 | -0.386 | 5.712 | 0.380 | -20.683 | 7.237 | 0.000 |  |
| other | income | q3 | 101 | 65 | False | True | 58.513 | 64.607 | 23.041 | 29.511 | 23.701 | 27.407 | 1.104 | 0.907 | 1.448 | inconclusive | inconclusive | 0.084 | 0.101 | -5.353 | 4.990 | -0.097 | 2.347 | 2.853 | 0.000 |  |
| other | income | q4 | 121 | 52 | False | True | 51.693 | 49.615 | 26.315 | 22.436 | 30.709 | 27.132 | 0.960 | 0.771 | 1.184 | inconclusive | inconclusive | 0.147 | 0.193 | 2.306 | -9.618 | 0.033 | -12.842 | 3.049 | 0.000 |  |
| other | income | q5 | 139 | 74 | False | True | 59.068 | 66.518 | 24.829 | 32.001 | 25.283 | 28.866 | 1.126 | 0.907 | 1.471 | inconclusive | inconclusive | 0.043 | 0.076 | -0.968 | 1.200 | -0.137 | 7.477 | -0.367 | 0.000 |  |
| other | vehicles | 0 | 88 | 59 | True | True | 50.950 | 55.073 | 17.535 | 26.654 | 20.650 | 29.039 | 1.081 | 0.836 | 1.406 | inconclusive | inconclusive | 0.146 | 0.057 | -19.980 | 12.221 | -0.262 | -3.658 | -0.676 | 0.000 |  |
| other | vehicles | 1 | 198 | 114 | False | False | 59.832 | 56.312 | 27.300 | 24.466 | 27.417 | 26.068 | 0.941 | 0.805 | 1.128 | inconclusive | inconclusive | 0.048 | 0.046 | 4.662 | -3.606 | -0.197 | -8.655 | 5.560 | 0.000 |  |
| other | vehicles | 2+ | 329 | 147 | False | False | 59.928 | 62.754 | 25.442 | 31.881 | 25.663 | 30.482 | 1.047 | 0.884 | 1.258 | inconclusive | inconclusive | 0.024 | 0.034 | 0.475 | 0.322 | 0.158 | 7.029 | -3.682 | 0.000 |  |
| other | household_type | couple | 79 | 83 | True | True | 52.437 | 58.843 | 27.417 | 30.546 | 31.514 | 31.147 | 1.122 | 0.882 | 1.509 | inconclusive | inconclusive | 0.201 | 0.051 | 4.605 | -11.127 | -0.013 | 4.278 | -4.841 | 0.000 |  |
| other | household_type | couple_with_children | 355 | 123 | False | False | 63.484 | 59.286 | 27.338 | 26.413 | 25.997 | 26.731 | 0.934 | 0.787 | 1.100 | inconclusive | inconclusive | 0.067 | 0.050 | 4.887 | -0.460 | 0.084 | -4.336 | 4.214 | 0.000 |  |
| other | household_type | other | 19 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | household_type | single_parent | 59 | 36 | True | True | 55.753 | - | 19.895 | - | 21.411 | - | - | - | - |  |  | 0.119 | - | -13.645 | 10.700 | -0.274 | - | - | - |  |
| other | household_type | single_person | 103 | 72 | False | True | 47.258 | 63.958 | 18.258 | 41.565 | 23.180 | 38.993 | 1.353 | 0.992 | 1.801 | inconclusive | inconclusive | 0.237 | 0.138 | -17.130 | 5.669 | -0.253 | 23.451 | -18.900 | 0.000 |  |
| other | day_purpose | other | 107 | 108 | False | False | 46.638 | 60.615 | 19.527 | 33.259 | 25.135 | 32.922 | 1.300 | 1.033 | 1.780 | inconclusive | inconclusive | 0.180 | 0.098 | -13.488 | 1.377 | -0.223 | 9.448 | -8.240 | 0.000 |  |
| other | day_purpose | work_study | 508 | 212 | False | False | 61.237 | 59.063 | 26.288 | 27.034 | 25.896 | 27.463 | 0.965 | 0.849 | 1.085 | inconclusive | inconclusive | 0.033 | 0.028 | 2.447 | -0.218 | 0.036 | -2.951 | 2.606 | 0.000 |  |
| train | density | dense+intermediate+sparse+very_sparse | 559 | 241 | False | False | 117.436 | 127.094 | 44.800 | 53.135 | 23.348 | 25.085 | 1.082 | 0.984 | 1.179 | inconclusive | inconclusive | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 |  |
| train | population | children_6_17 | 27 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | employed | 422 | 168 | False | False | 121.005 | 128.888 | 47.408 | 56.083 | 23.575 | 26.108 | 1.065 | 0.950 | 1.181 | inconclusive | inconclusive | 0.051 | 0.032 | 6.744 | -1.149 | -2.026 | 6.912 | -5.117 | 0.000 |  |
| train | population | other_inactive | 46 | 25 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | retired | 46 | 23 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | unemployed | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | income | q1+q2+q3+q4 | 308 | 154 | False | False | 116.785 | 128.223 | 45.265 | 50.606 | 23.450 | 23.680 | 1.098 | 0.976 | 1.234 | inconclusive | inconclusive | 0.016 | 0.040 | 1.208 | -0.510 | -1.349 | -6.225 | 7.354 | 0.000 |  |
| train | income | q5 | 251 | 87 | False | True | 118.502 | 124.631 | 44.039 | 58.651 | 23.179 | 28.236 | 1.052 | 0.921 | 1.189 | inconclusive | inconclusive | 0.026 | 0.088 | -2.023 | 0.860 | 2.229 | 12.430 | -14.892 | 0.000 |  |
| train | vehicles | 0 | 176 | 77 | False | True | 109.999 | 136.143 | 32.264 | 46.852 | 17.598 | 20.648 | 1.238 | 1.003 | 1.432 | inconclusive | inconclusive | 0.106 | 0.130 | -37.317 | 32.139 | -2.258 | -16.558 | 25.607 | 0.000 |  |
| train | vehicles | 1 | 239 | 94 | False | True | 121.496 | 122.022 | 47.756 | 53.726 | 24.313 | 26.418 | 1.004 | 0.880 | 1.154 | inconclusive | inconclusive | 0.052 | 0.084 | 7.632 | -4.835 | 1.264 | 1.378 | -6.450 | 0.000 |  |
| train | vehicles | 2+ | 144 | 67 | False | True | 117.057 | 117.698 | 50.440 | 52.927 | 26.321 | 26.981 | 1.005 | 0.836 | 1.229 | inconclusive | inconclusive | 0.062 | 0.083 | 13.903 | -14.050 | -0.231 | -0.479 | -8.916 | 0.000 |  |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | couple | 123 | 47 | False | True | 124.742 | - | 51.327 | - | 24.688 | - | - | - | - |  |  | 0.079 | - | 16.465 | -6.754 | -2.405 | - | - | - |  |
| train | household_type | couple_with_children | 198 | 84 | False | True | 111.559 | 114.134 | 41.273 | 48.171 | 23.143 | 25.323 | 1.023 | 0.865 | 1.195 | inconclusive | inconclusive | 0.058 | 0.079 | -9.387 | 1.010 | 2.501 | -11.818 | -1.141 | 0.000 |  |
| train | household_type | other | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | single_parent | 58 | 31 | True | True | 124.322 | - | 43.724 | - | 21.102 | - | - | - | - |  |  | 0.121 | - | -2.938 | 12.225 | -2.401 | - | - | - |  |
| train | household_type | single_person | 162 | 72 | False | True | 117.900 | 129.122 | 48.174 | 49.894 | 24.516 | 23.185 | 1.095 | 0.969 | 1.225 | inconclusive | inconclusive | 0.038 | 0.065 | 8.543 | -5.741 | -2.338 | -8.063 | 10.091 | 0.000 |  |
| train | day_purpose | other | 98 | 49 | True | True | 108.131 | - | 38.880 | - | 21.574 | - | - | - | - |  |  | 0.125 | - | -15.975 | 8.910 | -2.239 | - | - | - |  |
| train | day_purpose | work_study | 461 | 192 | False | False | 119.173 | 125.849 | 45.905 | 53.627 | 23.656 | 25.567 | 1.056 | 0.941 | 1.158 | inconclusive | inconclusive | 0.023 | 0.029 | 2.883 | -1.548 | 0.403 | 1.166 | -2.410 | 0.000 |  |
| urban_pt | density | dense | 676 | 364 | False | False | 70.955 | 73.028 | 12.808 | 10.293 | 10.831 | 8.457 | 1.029 | 0.929 | 1.116 | equivalent | inconclusive | 0.033 | 0.044 | -15.284 | 14.097 | 0.000 | -23.798 | 21.827 | 0.000 |  |
| urban_pt | density | intermediate | 633 | 467 | False | False | 73.696 | 78.523 | 16.776 | 15.390 | 13.658 | 11.759 | 1.066 | 0.964 | 1.165 | inconclusive | inconclusive | 0.026 | 0.048 | 4.101 | -2.547 | 0.000 | 6.193 | -2.668 | 0.000 |  |
| urban_pt | density | sparse+very_sparse | 88 | 84 | True | True | 68.453 | 66.659 | 25.176 | 21.616 | 22.067 | 19.457 | 0.974 | 0.770 | 1.277 | inconclusive | inconclusive | 0.140 | 0.126 | 32.482 | -36.171 | 0.000 | 29.745 | -38.084 | 0.000 |  |
| urban_pt | population | children_6_17 | 138 | 175 | False | False | 63.486 | 69.345 | 17.943 | 16.390 | 16.958 | 14.182 | 1.092 | 0.865 | 1.335 | inconclusive | inconclusive | 0.159 | 0.107 | 8.365 | -17.021 | 0.000 | 10.365 | -16.018 | 0.000 |  |
| urban_pt | population | employed | 705 | 340 | False | False | 74.492 | 74.635 | 14.557 | 13.662 | 11.725 | 10.983 | 1.002 | 0.918 | 1.083 | equivalent | equivalent | 0.055 | 0.047 | -6.280 | 8.630 | 0.000 | -2.874 | 2.511 | 0.000 |  |
| urban_pt | population | other_inactive | 222 | 142 | False | False | 77.776 | 81.663 | 18.562 | 13.529 | 14.319 | 9.940 | 1.050 | 0.915 | 1.188 | inconclusive | inconclusive | 0.125 | 0.115 | 11.793 | -6.158 | 0.000 | -3.770 | 10.435 | 0.000 |  |
| urban_pt | population | retired | 259 | 177 | False | False | 65.878 | 75.186 | 13.232 | 11.671 | 12.052 | 9.313 | 1.141 | 1.026 | 1.282 | inconclusive | inconclusive | 0.100 | 0.066 | -12.485 | 6.221 | 0.000 | -14.713 | 14.901 | 0.000 |  |
| urban_pt | population | unemployed | 73 | 79 | True | True | 80.208 | 82.916 | 14.807 | 14.003 | 11.076 | 10.133 | 1.034 | 0.760 | 1.389 | inconclusive | inconclusive | 0.115 | 0.109 | -5.223 | 13.289 | 0.000 | -1.082 | 9.001 | 0.000 |  |
| urban_pt | income | q1 | 293 | 287 | False | False | 79.079 | 78.455 | 20.311 | 13.161 | 15.411 | 10.065 | 0.992 | 0.864 | 1.149 | equivalent | inconclusive | 0.080 | 0.046 | 18.698 | -11.760 | 0.000 | -5.810 | 9.267 | 0.000 |  |
| urban_pt | income | q2 | 233 | 159 | False | False | 73.412 | 79.398 | 14.748 | 14.341 | 12.053 | 10.838 | 1.082 | 0.951 | 1.237 | inconclusive | inconclusive | 0.066 | 0.085 | -5.285 | 6.556 | 0.000 | 0.783 | 3.617 | 0.000 |  |
| urban_pt | income | q3 | 230 | 148 | False | False | 75.992 | 76.082 | 14.525 | 16.359 | 11.468 | 12.901 | 1.001 | 0.878 | 1.136 | equivalent | inconclusive | 0.097 | 0.043 | -6.504 | 10.355 | 0.000 | 10.708 | -9.624 | 0.000 |  |
| urban_pt | income | q4 | 249 | 132 | False | False | 63.176 | 66.302 | 14.646 | 13.688 | 13.910 | 12.387 | 1.049 | 0.909 | 1.226 | inconclusive | inconclusive | 0.112 | 0.092 | -5.372 | -3.594 | 0.000 | -2.572 | -6.124 | 0.000 |  |
| urban_pt | income | q5 | 392 | 189 | False | False | 66.961 | 71.426 | 13.181 | 14.103 | 11.811 | 11.847 | 1.067 | 0.963 | 1.167 | inconclusive | inconclusive | 0.068 | 0.048 | -12.855 | 7.675 | 0.000 | -0.486 | -3.086 | 0.000 |  |
| urban_pt | vehicles | 0 | 710 | 466 | False | False | 79.473 | 79.470 | 17.096 | 12.158 | 12.907 | 9.179 | 1.000 | 0.907 | 1.110 | equivalent | inconclusive | 0.089 | 0.067 | 5.693 | 1.639 | 0.000 | -11.972 | 16.444 | 0.000 |  |
| urban_pt | vehicles | 1 | 453 | 279 | False | False | 68.180 | 67.311 | 13.339 | 12.236 | 11.738 | 10.907 | 0.987 | 0.897 | 1.083 | equivalent | inconclusive | 0.057 | 0.091 | -12.137 | 8.175 | 0.000 | -10.566 | 2.879 | 0.000 |  |
| urban_pt | vehicles | 2+ | 234 | 165 | False | False | 65.166 | 77.675 | 17.639 | 20.088 | 16.240 | 15.517 | 1.192 | 1.024 | 1.383 | inconclusive | inconclusive | 0.113 | 0.071 | 7.298 | -14.274 | 0.000 | 26.495 | -23.818 | 0.000 |  |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | couple | 259 | 123 | False | False | 69.945 | 71.296 | 14.591 | 13.097 | 12.516 | 11.022 | 1.019 | 0.914 | 1.174 | inconclusive | inconclusive | 0.033 | 0.099 | -5.917 | 3.720 | 0.000 | -5.896 | 2.193 | 0.000 |  |
| urban_pt | household_type | couple_with_children | 365 | 261 | False | False | 71.258 | 75.135 | 14.997 | 17.002 | 12.627 | 13.577 | 1.054 | 0.952 | 1.170 | inconclusive | inconclusive | 0.038 | 0.031 | -4.006 | 3.122 | 0.000 | 13.535 | -13.398 | 0.000 |  |
| urban_pt | household_type | other | 32 | 37 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | single_parent | 152 | 130 | False | False | 76.767 | 68.163 | 22.629 | 11.884 | 17.687 | 10.460 | 0.888 | 0.726 | 1.066 | inconclusive | inconclusive | 0.069 | 0.125 | 26.463 | -21.838 | 0.000 | -12.721 | 5.886 | 0.000 |  |
| urban_pt | household_type | single_person | 589 | 364 | False | False | 73.021 | 76.192 | 15.233 | 11.526 | 12.517 | 9.076 | 1.043 | 0.946 | 1.134 | equivalent | inconclusive | 0.073 | 0.024 | -2.921 | 3.801 | 0.000 | -15.755 | 16.948 | 0.000 |  |
| urban_pt | day_purpose | other | 517 | 409 | False | False | 69.175 | 75.925 | 17.522 | 12.115 | 15.198 | 9.574 | 1.098 | 0.959 | 1.247 | inconclusive | inconclusive | 0.120 | 0.038 | 7.045 | -10.013 | 0.000 | -11.963 | 12.890 | 0.000 |  |
| urban_pt | day_purpose | work_study | 880 | 506 | False | False | 73.563 | 74.535 | 15.062 | 15.235 | 12.285 | 12.264 | 1.013 | 0.946 | 1.088 | equivalent | equivalent | 0.057 | 0.019 | -3.756 | 5.178 | 0.000 | 5.280 | -5.743 | 0.000 |  |
| walk | density | dense | 951 | 603 | False | False | 34.127 | 37.979 | 2.101 | 2.134 | 3.723 | 3.372 | 1.113 | 1.012 | 1.226 | inconclusive | inconclusive | 0.086 | 0.131 | 4.182 | -0.542 | 0.186 | 5.753 | 0.328 | 0.000 |  |
| walk | density | intermediate | 1704 | 1253 | False | False | 31.293 | 32.099 | 1.898 | 1.813 | 3.640 | 3.390 | 1.026 | 0.949 | 1.099 | equivalent | equivalent | 0.030 | 0.023 | 0.879 | 0.181 | -0.069 | 0.070 | 0.131 | 0.000 |  |
| walk | density | sparse | 409 | 289 | False | False | 27.896 | 28.984 | 1.697 | 1.696 | 3.649 | 3.511 | 1.039 | 0.887 | 1.180 | inconclusive | inconclusive | 0.051 | 0.112 | -2.435 | 0.095 | -0.065 | -1.972 | -0.942 | 0.000 |  |
| walk | density | very_sparse | 572 | 262 | False | False | 20.408 | 18.458 | 1.224 | 1.068 | 3.599 | 3.471 | 0.904 | 0.802 | 1.018 | inconclusive | inconclusive | 0.189 | 0.267 | -10.267 | 0.429 | -0.056 | -12.956 | -0.483 | 0.000 |  |
| walk | population | children_6_17 | 462 | 339 | False | False | 29.108 | 29.246 | 1.760 | 1.561 | 3.627 | 3.202 | 1.005 | 0.891 | 1.110 | equivalent | inconclusive | 0.025 | 0.055 | -1.402 | 0.275 | -0.066 | -4.519 | 1.867 | 0.000 |  |
| walk | population | employed | 1355 | 785 | False | False | 27.862 | 28.399 | 1.783 | 1.747 | 3.866 | 3.691 | 1.019 | 0.933 | 1.107 | equivalent | inconclusive | 0.075 | 0.067 | -0.996 | -1.585 | 0.142 | -1.060 | -2.439 | 0.000 |  |
| walk | population | other_inactive | 468 | 266 | False | False | 32.801 | 39.924 | 2.110 | 2.303 | 3.860 | 3.460 | 1.217 | 1.078 | 1.386 | inconclusive | inconclusive | 0.061 | 0.158 | 4.238 | -1.667 | -0.070 | 8.619 | -0.592 | 0.000 |  |
| walk | population | retired | 1135 | 851 | False | False | 32.143 | 34.619 | 1.758 | 1.865 | 3.282 | 3.233 | 1.077 | 0.984 | 1.149 | equivalent | inconclusive | 0.087 | 0.065 | -1.504 | 3.416 | -0.070 | 1.008 | 1.713 | 0.000 |  |
| walk | population | unemployed | 216 | 164 | False | False | 38.233 | 40.095 | 2.390 | 2.236 | 3.750 | 3.346 | 1.049 | 0.836 | 1.316 | inconclusive | inconclusive | 0.149 | 0.084 | 8.826 | -0.818 | -0.076 | 7.589 | 0.607 | 0.000 |  |
| walk | income | q1 | 828 | 596 | False | False | 34.987 | 35.339 | 2.124 | 1.989 | 3.668 | 3.377 | 1.010 | 0.915 | 1.120 | equivalent | inconclusive | 0.080 | 0.085 | 4.588 | -0.061 | 0.159 | 3.175 | 0.266 | 0.000 |  |
| walk | income | q2 | 632 | 455 | False | False | 28.571 | 33.299 | 1.751 | 1.903 | 3.678 | 3.429 | 1.165 | 1.035 | 1.302 | inconclusive | inconclusive | 0.032 | 0.048 | -1.530 | -0.134 | -0.066 | 1.648 | -0.247 | 0.000 |  |
| walk | income | q3 | 642 | 394 | False | False | 28.256 | 28.213 | 1.678 | 1.597 | 3.564 | 3.397 | 0.998 | 0.894 | 1.128 | equivalent | inconclusive | 0.055 | 0.074 | -2.766 | 0.786 | -0.065 | -3.742 | 0.057 | 0.000 |  |
| walk | income | q4 | 632 | 449 | False | False | 28.690 | 31.021 | 1.777 | 1.794 | 3.716 | 3.471 | 1.081 | 0.945 | 1.225 | inconclusive | inconclusive | 0.075 | 0.052 | -1.108 | -0.437 | -0.066 | -0.262 | -0.615 | 0.000 |  |
| walk | income | q5 | 902 | 513 | False | False | 28.644 | 29.863 | 1.749 | 1.673 | 3.664 | 3.361 | 1.043 | 0.934 | 1.154 | inconclusive | inconclusive | 0.059 | 0.056 | -1.571 | -0.021 | -0.066 | -2.421 | 0.387 | 0.000 |  |
| walk | vehicles | 0 | 1173 | 774 | False | False | 37.249 | 38.037 | 2.272 | 2.060 | 3.659 | 3.250 | 1.021 | 0.956 | 1.116 | equivalent | inconclusive | 0.151 | 0.104 | 7.003 | 0.020 | -0.075 | 4.528 | 1.612 | 0.000 |  |
| walk | vehicles | 1 | 1525 | 999 | False | False | 29.209 | 32.969 | 1.773 | 1.871 | 3.641 | 3.405 | 1.129 | 1.040 | 1.223 | inconclusive | inconclusive | 0.026 | 0.028 | -1.188 | 0.161 | -0.066 | 1.084 | -0.013 | 0.000 |  |
| walk | vehicles | 2+ | 938 | 627 | False | False | 26.191 | 24.851 | 1.600 | 1.492 | 3.698 | 3.602 | 0.949 | 0.842 | 1.050 | inconclusive | inconclusive | 0.090 | 0.115 | -4.010 | -0.284 | 0.184 | -5.447 | -1.599 | 0.000 |  |
| walk | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | household_type | couple | 852 | 560 | False | False | 30.098 | 31.569 | 1.772 | 1.839 | 3.532 | 3.495 | 1.049 | 0.954 | 1.166 | inconclusive | inconclusive | 0.020 | 0.036 | -1.219 | 1.083 | -0.067 | 0.511 | -0.840 | 0.000 |  |
| walk | household_type | couple_with_children | 1079 | 662 | False | False | 28.697 | 28.726 | 1.775 | 1.665 | 3.731 | 3.477 | 1.001 | 0.911 | 1.073 | equivalent | equivalent | 0.051 | 0.045 | -1.139 | -0.554 | 0.088 | -2.525 | -0.647 | 0.000 |  |
| walk | household_type | other | 82 | 46 | True | True | 28.797 | - | 1.833 | - | 3.820 | - | - | - | - |  |  | 0.075 | - | -0.185 | -1.253 | -0.066 | - | - | - |  |
| walk | household_type | single_parent | 343 | 239 | False | False | 31.881 | 32.772 | 1.932 | 1.792 | 3.636 | 3.282 | 1.028 | 0.873 | 1.218 | inconclusive | inconclusive | 0.050 | 0.048 | 1.436 | 0.213 | -0.069 | -0.306 | 1.180 | 0.000 |  |
| walk | household_type | single_person | 1280 | 900 | False | False | 33.493 | 38.047 | 2.030 | 2.079 | 3.637 | 3.279 | 1.136 | 1.062 | 1.238 | inconclusive | inconclusive | 0.083 | 0.105 | 3.048 | 0.214 | -0.071 | 4.843 | 1.306 | 0.000 |  |
| walk | day_purpose | other | 2168 | 1515 | False | False | 30.703 | 35.286 | 1.823 | 1.942 | 3.563 | 3.301 | 1.149 | 1.076 | 1.217 | inconclusive | inconclusive | 0.017 | 0.053 | -0.360 | 0.830 | -0.068 | 2.365 | 1.023 | 0.000 |  |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | day_purpose | work_study | 1468 | 891 | False | False | 29.846 | 28.309 | 1.869 | 1.669 | 3.776 | 3.537 | 0.948 | 0.881 | 1.032 | equivalent | inconclusive | 0.020 | 0.056 | 0.396 | -0.929 | 0.078 | -2.434 | -1.155 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Mode-user composition

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 401 | 253 | 1.035 | - | 0.019 | 0.000 | insufficient common support for 2008 target |
| car_driver | 8336 | 5569 | 1.066 | 1.073 | 0.000 | 0.000 |  |
| car_passenger | 2024 | 1626 | 1.128 | 1.109 | 0.000 | 0.000 |  |
| other | 615 | 320 | 1.007 | - | 0.012 | 0.000 | insufficient common support for 2008 target |
| train | 559 | 240 | 1.083 | 1.074 | 0.010 | 0.006 | 2008 target rescaled to common support |
| urban_pt | 1397 | 913 | 1.039 | 1.045 | 0.000 | 0.000 |  |
| walk | 3636 | 2405 | 1.053 | 1.044 | 0.000 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Per-mode decomposition

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | 1.342 | 1.593 | 1.558 | -1.809 | -0.000 |  |
| bike | rounded_crow_fly | 1.342 | 1.593 | 10.177 | -10.428 | 0.000 |  |
| car_driver | published | 3.982 | -3.274 | 5.196 | 2.060 | -0.000 |  |
| car_driver | rounded_crow_fly | 3.982 | -3.274 | 5.383 | 1.873 | -0.000 |  |
| car_passenger | published | 5.162 | -1.385 | 3.202 | 3.346 | -0.000 |  |
| car_passenger | rounded_crow_fly | 5.162 | -1.385 | 4.199 | 2.349 | -0.000 |  |
| other | published | 0.435 | -5.481 | 11.962 | -6.295 | 0.250 |  |
| other | rounded_crow_fly | 0.435 | -5.481 | 13.850 | -7.933 | 0.000 |  |
| train | published | 9.658 | -4.959 | 24.363 | -8.765 | -0.981 |  |
| train | rounded_crow_fly | 9.658 | -4.959 | 17.871 | -3.254 | -0.000 |  |
| urban_pt | published | 2.857 | -2.284 | -5.859 | 11.000 | 0.000 |  |
| urban_pt | rounded_crow_fly | 2.857 | -2.284 | -1.607 | 6.748 | 0.000 |  |
| walk | published | 1.597 | -0.854 | 2.602 | -0.125 | -0.026 |  |
| walk | rounded_crow_fly | 1.597 | -0.854 | -1.388 | 3.839 | -0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Duration-rounding bounds

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | 0.007 | 1.081 | 0.000 |  |
| car_driver | 0.005 | 3.114 | 0.000 |  |
| car_passenger | -0.089 | 1.458 | 0.000 |  |
| other | -0.096 | 1.791 | 0.000 |  |
| train | -0.265 | 2.248 | 0.000 |  |
| urban_pt | -0.033 | 0.895 | 0.000 |  |
| walk | -0.108 | 0.646 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


## Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km)

### Subgroup mode-user days

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 81 | 58 | True | True | 42.800 | 47.427 | 8.044 | 8.141 | 11.276 | 10.299 | - | - | - |  |  | 0.153 | 0.211 | 7.844 | -3.095 | 0.000 | 3.846 | 4.279 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | intermediate | 153 | 114 | False | False | 39.319 | 42.766 | 7.006 | 8.658 | 10.691 | 12.147 | - | - | - |  |  | 0.109 | 0.100 | 2.172 | -0.905 | 0.000 | 6.172 | -2.708 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | sparse+very_sparse | 170 | 81 | False | True | 34.026 | 28.057 | 5.416 | 5.148 | 9.550 | 11.010 | - | - | - |  |  | 0.179 | 0.193 | -7.246 | 3.221 | 0.000 | -12.320 | 1.074 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | children_6_17 | 67 | 28 | True | True | 27.357 | - | 4.706 | - | 10.322 | - | - | - | - |  |  | 0.190 | - | -11.075 | 0.381 | 0.000 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | employed | 181 | 128 | False | False | 46.788 | 41.898 | 8.153 | 8.700 | 10.455 | 12.459 | - | - | - |  |  | 0.146 | 0.091 | 8.781 | -0.044 | 0.000 | 6.307 | -3.711 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | other_inactive | 34 | 16 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | retired | 105 | 64 | False | True | 36.415 | 38.751 | 5.781 | 7.056 | 9.525 | 10.925 | - | - | - |  |  | 0.107 | 0.065 | -5.064 | 3.428 | 0.000 | -2.110 | 1.558 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | unemployed | 17 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q1+q2+q3 | 218 | 137 | False | False | 39.323 | 38.160 | 6.481 | 6.607 | 9.888 | 10.388 | - | - | - |  |  | 0.049 | 0.077 | -0.845 | 2.117 | 0.000 | -4.643 | 3.500 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q4 | 76 | 50 | True | True | 37.371 | 36.992 | 8.038 | 7.642 | 12.906 | 12.394 | - | - | - |  |  | 0.086 | 0.109 | 7.300 | -7.980 | 0.000 | 0.978 | -3.288 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q5 | 110 | 66 | False | True | 34.854 | 44.478 | 5.805 | 9.175 | 9.994 | 12.377 | - | - | - |  |  | 0.109 | 0.114 | -4.803 | 1.606 | 0.000 | 8.723 | -3.548 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 0 | 97 | 55 | True | True | 41.508 | 51.784 | 7.467 | 7.839 | 10.793 | 9.082 | - | - | - |  |  | 0.142 | 0.168 | 4.762 | -1.305 | 0.000 | 2.313 | 10.168 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 1 | 149 | 98 | False | True | 42.953 | 40.413 | 7.616 | 8.442 | 10.639 | 12.533 | - | - | - |  |  | 0.121 | 0.061 | 5.650 | -0.748 | 0.000 | 4.991 | -3.880 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 2+ | 158 | 97 | False | True | 31.859 | 32.105 | 5.294 | 6.471 | 9.971 | 12.093 | - | - | - |  |  | 0.131 | 0.108 | -7.809 | 1.616 | 0.000 | -5.004 | -2.193 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple | 119 | 73 | False | True | 35.623 | 34.911 | 5.644 | 7.013 | 9.507 | 12.053 | - | - | - |  |  | 0.122 | 0.081 | -5.892 | 3.463 | 0.000 | -2.231 | -2.161 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple_with_children | 136 | 76 | False | True | 37.542 | 37.345 | 6.672 | 7.486 | 10.664 | 12.027 | - | - | - |  |  | 0.050 | 0.050 | 0.276 | -0.785 | 0.000 | 0.193 | -2.151 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | other | 11 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_parent | 29 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_person | 109 | 73 | False | True | 44.330 | 45.581 | 8.347 | 7.933 | 11.298 | 10.442 | - | - | - |  |  | 0.238 | 0.131 | 9.509 | -3.230 | 0.000 | 2.672 | 3.607 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | other | 204 | 123 | False | False | 35.480 | 37.730 | 5.704 | 6.894 | 9.645 | 10.964 | - | - | - |  |  | 0.059 | 0.083 | -5.496 | 2.925 | 0.000 | -2.976 | 1.403 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | work_study | 200 | 130 | False | False | 40.807 | 40.720 | 7.610 | 7.947 | 11.189 | 11.710 | - | - | - |  |  | 0.064 | 0.074 | 5.470 | -2.714 | 0.000 | 2.596 | -1.178 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | dense | 640 | 433 | False | False | 63.627 | 78.162 | 31.083 | 41.952 | 29.311 | 32.204 | - | - | - |  |  | 0.054 | 0.069 | -15.441 | 16.080 | -0.069 | 0.721 | 10.194 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | intermediate | 3166 | 2426 | False | False | 62.782 | 66.551 | 34.751 | 35.291 | 33.213 | 31.817 | - | - | - |  |  | 0.008 | 0.015 | -8.321 | 8.110 | -0.065 | -10.902 | 10.206 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | sparse | 1224 | 1018 | False | False | 61.954 | 61.988 | 41.789 | 42.134 | 40.488 | 40.783 | - | - | - |  |  | 0.046 | 0.047 | 3.262 | -4.324 | -0.042 | 0.921 | -6.181 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | very_sparse | 3402 | 1743 | False | False | 63.974 | 69.050 | 47.682 | 51.007 | 44.865 | 44.321 | - | - | - |  |  | 0.027 | 0.032 | 11.693 | -10.914 | 0.137 | 13.995 | -12.192 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | children_6_17 | 77 | 42 | True | True | 44.534 | - | 25.745 | - | 34.686 | - | - | - | - |  |  | 0.205 | - | -23.019 | 4.554 | -0.058 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | employed | 5299 | 3087 | False | False | 67.941 | 72.513 | 44.360 | 47.001 | 39.233 | 38.891 | - | - | - |  |  | 0.049 | 0.075 | 7.325 | -2.468 | 0.026 | 8.632 | -3.367 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | other_inactive | 602 | 289 | False | False | 55.617 | 62.591 | 31.088 | 35.867 | 33.538 | 34.382 | - | - | - |  |  | 0.092 | 0.089 | -14.437 | 7.061 | -0.065 | -9.524 | 4.868 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | retired | 2134 | 1934 | False | False | 52.779 | 55.349 | 29.845 | 29.862 | 33.933 | 32.371 | - | - | - |  |  | 0.113 | 0.161 | -16.431 | 6.207 | -0.055 | -20.165 | 8.267 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | unemployed | 320 | 264 | False | False | 57.178 | 63.571 | 34.350 | 33.684 | 36.045 | 31.792 | - | - | - |  |  | 0.062 | 0.061 | -8.641 | 2.827 | -0.066 | -13.704 | 10.028 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q1 | 981 | 633 | False | False | 54.328 | 61.765 | 32.243 | 34.344 | 35.615 | 33.363 | - | - | - |  |  | 0.101 | 0.079 | -12.135 | 3.461 | -0.056 | -12.259 | 6.776 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q2 | 1328 | 1044 | False | False | 58.850 | 59.682 | 37.028 | 35.777 | 37.803 | 35.968 | - | - | - |  |  | 0.048 | 0.059 | -4.191 | -0.034 | 0.016 | -9.463 | 1.897 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q3 | 1745 | 1184 | False | False | 60.274 | 69.314 | 37.432 | 46.411 | 37.262 | 40.174 | - | - | - |  |  | 0.037 | 0.032 | -3.571 | 0.855 | -0.068 | 7.575 | -5.508 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q4 | 1877 | 1343 | False | False | 65.064 | 68.196 | 42.364 | 41.330 | 39.131 | 36.363 | - | - | - |  |  | 0.039 | 0.036 | 4.219 | -2.247 | 0.034 | -0.339 | 1.288 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q5 | 2501 | 1416 | False | False | 71.503 | 73.124 | 45.090 | 45.463 | 37.900 | 37.303 | - | - | - |  |  | 0.095 | 0.068 | 8.614 | -0.210 | 0.041 | 6.335 | -0.458 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 0 | 57 | 58 | True | True | 72.873 | 63.992 | 46.639 | 34.397 | 38.400 | 32.251 | - | - | - |  |  | 0.187 | 0.143 | 10.991 | -1.102 | -0.074 | -12.375 | 9.119 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 1 | 3319 | 2516 | False | False | 60.849 | 63.804 | 35.400 | 35.018 | 34.912 | 32.930 | - | - | - |  |  | 0.060 | 0.038 | -7.045 | 4.894 | -0.058 | -11.184 | 7.741 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 2+ | 5056 | 3039 | False | False | 64.314 | 69.492 | 42.230 | 45.764 | 39.463 | 39.513 | - | - | - |  |  | 0.038 | 0.027 | 3.992 | -2.772 | 0.036 | 6.625 | -4.380 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple | 2900 | 1970 | False | False | 59.251 | 61.677 | 35.949 | 37.784 | 36.406 | 36.756 | - | - | - |  |  | 0.053 | 0.079 | -6.013 | 2.267 | -0.061 | -6.102 | 0.531 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple_with_children | 3179 | 1599 | False | False | 67.300 | 73.281 | 43.860 | 47.527 | 39.163 | 38.913 | - | - | - |  |  | 0.048 | 0.070 | 6.552 | -2.339 | 0.028 | 9.459 | -3.425 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | other | 170 | 88 | False | True | 57.482 | 64.006 | 34.802 | 35.789 | 36.357 | 33.549 | - | - | - |  |  | 0.088 | 0.121 | -7.876 | 2.316 | -0.016 | -9.773 | 6.531 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_parent | 525 | 342 | False | False | 55.999 | 65.544 | 31.272 | 36.966 | 33.621 | 33.839 | - | - | - |  |  | 0.062 | 0.037 | -14.135 | 6.937 | 0.138 | -7.741 | 6.038 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_person | 1658 | 1621 | False | False | 59.982 | 62.365 | 37.060 | 35.341 | 37.085 | 34.000 | - | - | - |  |  | 0.049 | 0.061 | -4.177 | 1.145 | -0.044 | -10.464 | 5.583 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | other | 3994 | 3070 | False | False | 55.105 | 59.221 | 32.579 | 33.940 | 35.529 | 34.387 | - | - | - |  |  | 0.096 | 0.116 | -11.609 | 3.627 | 0.029 | -12.756 | 4.729 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | work_study | 4438 | 2550 | False | False | 69.236 | 73.984 | 45.168 | 47.914 | 39.174 | 38.857 | - | - | - |  |  | 0.075 | 0.097 | 8.588 | -2.391 | -0.020 | 10.077 | -3.340 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | dense | 192 | 164 | False | False | 41.972 | 50.311 | 21.816 | 22.143 | 31.186 | 26.408 | - | - | - |  |  | 0.071 | 0.111 | -6.814 | 6.686 | -0.201 | -9.391 | 12.520 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | intermediate | 812 | 779 | False | False | 40.926 | 45.926 | 21.708 | 23.213 | 32.079 | 30.326 | - | - | - |  |  | 0.029 | 0.038 | -6.934 | 5.428 | 0.132 | -6.775 | 5.519 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | sparse | 287 | 294 | False | False | 42.355 | 45.384 | 27.517 | 28.750 | 39.203 | 38.009 | - | - | - |  |  | 0.061 | 0.056 | 2.982 | -2.967 | 0.040 | 3.166 | -4.963 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | very_sparse | 776 | 418 | False | False | 44.580 | 50.100 | 31.934 | 34.614 | 43.020 | 41.454 | - | - | - |  |  | 0.077 | 0.067 | 9.525 | -7.080 | -0.166 | 12.352 | -9.435 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | children_6_17 | 616 | 445 | False | False | 32.045 | 36.245 | 17.098 | 17.674 | 32.039 | 29.257 | - | - | - |  |  | 0.126 | 0.125 | -14.974 | 4.865 | -0.146 | -17.343 | 6.405 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | employed | 587 | 329 | False | False | 47.295 | 54.988 | 29.933 | 35.422 | 38.099 | 38.650 | - | - | - |  |  | 0.076 | 0.095 | 6.920 | -1.859 | -0.067 | 14.127 | -6.321 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | other_inactive | 241 | 182 | False | False | 49.971 | 51.333 | 26.891 | 26.111 | 32.288 | 30.520 | - | - | - |  |  | 0.145 | 0.074 | 2.184 | 5.705 | -0.219 | -1.372 | 5.523 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | retired | 538 | 622 | False | False | 56.146 | 59.166 | 39.966 | 36.635 | 43.310 | 37.152 | - | - | - |  |  | 0.152 | 0.164 | 21.694 | -8.299 | 0.450 | 16.455 | -4.471 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | unemployed | 84 | 75 | True | True | 50.316 | 52.816 | 31.826 | 35.040 | 38.415 | 39.807 | - | - | - |  |  | 0.205 | 0.112 | 9.975 | -2.300 | 0.341 | 13.299 | -7.665 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q1 | 363 | 313 | False | False | 40.882 | 46.102 | 23.005 | 22.543 | 33.762 | 29.340 | - | - | - |  |  | 0.055 | 0.043 | -4.519 | 3.298 | -0.198 | -8.153 | 7.072 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q2 | 416 | 377 | False | False | 37.680 | 47.998 | 22.578 | 29.052 | 35.951 | 36.317 | - | - | - |  |  | 0.090 | 0.045 | -5.089 | 0.659 | -0.190 | 3.753 | -2.937 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q3 | 427 | 339 | False | False | 48.329 | 48.474 | 30.804 | 29.633 | 38.286 | 36.679 | - | - | - |  |  | 0.099 | 0.047 | 8.293 | -2.101 | -0.164 | 4.718 | -3.426 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q4 | 395 | 335 | False | False | 39.373 | 45.063 | 24.201 | 24.206 | 37.014 | 32.229 | - | - | - |  |  | 0.050 | 0.025 | -2.366 | -0.516 | -0.045 | -4.780 | 2.661 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q5 | 466 | 291 | False | False | 46.284 | 48.326 | 27.950 | 28.769 | 36.996 | 35.719 | - | - | - |  |  | 0.063 | 0.038 | 3.810 | -0.538 | 0.711 | 3.298 | -2.154 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 0 | 260 | 249 | False | False | 42.282 | 45.520 | 23.656 | 21.605 | 33.569 | 28.478 | - | - | - |  |  | 0.058 | 0.070 | -3.415 | 3.597 | -0.201 | -10.071 | 8.409 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 1 | 743 | 632 | False | False | 43.435 | 48.561 | 25.392 | 26.964 | 35.116 | 33.316 | - | - | - |  |  | 0.056 | 0.025 | -0.425 | 1.715 | -0.155 | 0.204 | 1.174 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 2+ | 1064 | 771 | False | False | 41.559 | 46.411 | 26.124 | 27.499 | 38.019 | 35.550 | - | - | - |  |  | 0.041 | 0.021 | 0.776 | -1.654 | 0.137 | 1.119 | -1.890 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple | 608 | 564 | False | False | 56.095 | 59.178 | 38.217 | 37.360 | 41.409 | 37.879 | - | - | - |  |  | 0.156 | 0.163 | 19.497 | -6.102 | 0.399 | 17.494 | -5.498 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple_with_children | 903 | 566 | False | False | 37.426 | 42.160 | 21.266 | 23.116 | 34.130 | 32.898 | - | - | - |  |  | 0.055 | 0.068 | -7.455 | 2.726 | -0.145 | -6.680 | 1.659 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | other | 64 | 37 | True | True | 42.974 | - | 28.092 | - | 39.221 | - | - | - | - |  |  | 0.058 | - | 3.886 | -3.009 | -0.203 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_parent | 164 | 149 | False | False | 45.401 | 41.821 | 27.217 | 20.660 | 35.968 | 29.641 | - | - | - |  |  | 0.058 | 0.056 | 2.607 | 0.702 | -0.209 | -11.647 | 6.286 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_person | 328 | 339 | False | False | 38.329 | 50.408 | 21.995 | 27.797 | 34.755 | 33.087 | - | - | - |  |  | 0.076 | 0.054 | -6.184 | 2.027 | 0.185 | 1.692 | 1.533 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | other | 1128 | 1100 | False | False | 50.913 | 56.590 | 33.211 | 34.920 | 39.410 | 37.024 | - | - | - |  |  | 0.114 | 0.112 | 12.016 | -3.503 | 0.099 | 13.598 | -4.191 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | work_study | 939 | 555 | False | False | 34.993 | 36.765 | 19.224 | 17.914 | 33.033 | 29.235 | - | - | - |  |  | 0.097 | 0.124 | -11.104 | 3.897 | -0.102 | -16.899 | 6.482 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | dense+intermediate | 263 | 173 | False | False | 58.972 | 57.879 | 25.381 | 26.850 | 26.540 | 27.834 | - | - | - |  |  | 0.032 | 0.066 | -2.899 | 1.324 | 0.599 | -21.360 | 14.819 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | sparse+very_sparse | 362 | 156 | False | False | 60.682 | 71.164 | 27.602 | 49.675 | 27.566 | 41.882 | - | - | - |  |  | 0.024 | 0.068 | 2.120 | -0.946 | -0.440 | 17.991 | -11.247 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | children_6_17 | 266 | 87 | False | True | 57.484 | 60.970 | 21.667 | 33.503 | 22.615 | 32.970 | - | - | - |  |  | 0.050 | 0.075 | -12.151 | 10.702 | -1.015 | -8.039 | 4.589 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | employed | 254 | 145 | False | False | 66.543 | 67.949 | 36.331 | 42.426 | 34.259 | 37.463 | - | - | - |  |  | 0.107 | 0.040 | 19.583 | -14.726 | 1.738 | 7.138 | -3.609 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | other_inactive | 36 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | retired | 59 | 62 | True | True | 52.760 | 61.721 | 23.864 | 36.281 | 27.642 | 35.270 | - | - | - |  |  | 0.178 | 0.126 | -6.212 | -1.037 | 0.061 | -3.064 | 0.365 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | unemployed | 10 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q1 | 105 | 61 | False | True | 59.277 | 69.513 | 26.602 | 40.729 | 26.926 | 35.155 | - | - | - |  |  | 0.037 | 0.182 | -0.106 | 0.466 | -1.031 | 4.487 | 0.606 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q2 | 150 | 73 | False | True | 65.180 | 47.909 | 25.340 | 21.384 | 23.610 | 26.781 | - | - | - |  |  | 0.089 | 0.131 | -3.149 | 8.705 | -0.324 | -32.186 | 15.675 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q3 | 103 | 66 | False | True | 59.217 | 71.301 | 23.668 | 52.401 | 24.164 | 44.096 | - | - | - |  |  | 0.084 | 0.096 | -7.069 | 6.913 | -0.575 | 21.631 | -14.750 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q4 | 123 | 55 | False | True | 52.282 | 57.735 | 28.302 | 34.034 | 32.652 | 35.369 | - | - | - |  |  | 0.149 | 0.163 | 3.372 | -10.366 | -0.672 | -6.867 | 0.182 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q5 | 144 | 74 | False | True | 62.824 | 73.325 | 30.106 | 39.489 | 30.866 | 32.313 | - | - | - |  |  | 0.040 | 0.076 | 7.485 | -7.903 | 3.294 | 2.485 | 6.420 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 0 | 88 | 61 | True | True | 50.950 | 58.477 | 17.535 | 30.438 | 20.650 | 31.231 | - | - | - |  |  | 0.152 | 0.058 | -23.156 | 15.115 | -0.956 | -13.765 | 7.822 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 1 | 202 | 117 | False | False | 61.652 | 59.674 | 28.958 | 28.668 | 28.766 | 28.824 | - | - | - |  |  | 0.049 | 0.039 | 5.052 | -3.544 | 0.196 | -17.620 | 12.875 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 2+ | 335 | 151 | False | False | 60.575 | 69.320 | 26.948 | 46.938 | 27.178 | 40.627 | - | - | - |  |  | 0.025 | 0.031 | 0.672 | -0.090 | 0.044 | 13.965 | -9.065 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple | 80 | 84 | True | True | 55.481 | 59.731 | 27.146 | 32.091 | 31.514 | 32.236 | - | - | - |  |  | 0.199 | 0.046 | 1.065 | -8.626 | 3.094 | -10.629 | 5.940 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple_with_children | 361 | 126 | False | False | 64.071 | 65.059 | 29.224 | 39.745 | 27.742 | 36.654 | - | - | - |  |  | 0.067 | 0.045 | 5.718 | -1.366 | -0.229 | 2.757 | -2.118 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | other | 21 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_parent | 59 | 36 | True | True | 56.029 | - | 19.980 | - | 21.473 | - | - | - | - |  |  | 0.121 | - | -16.697 | 13.570 | -0.793 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_person | 104 | 77 | False | True | 48.897 | 80.074 | 19.912 | 60.901 | 24.434 | 45.634 | - | - | - |  |  | 0.236 | 0.147 | -15.805 | 5.691 | -0.938 | 33.776 | -18.122 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | other | 111 | 112 | False | False | 48.126 | 68.781 | 23.199 | 57.951 | 29.131 | 50.553 | - | - | - |  |  | 0.175 | 0.094 | -7.462 | -3.815 | -0.545 | 27.942 | -23.581 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | work_study | 514 | 217 | False | False | 62.129 | 63.156 | 27.286 | 32.329 | 26.849 | 30.714 | - | - | - |  |  | 0.032 | 0.027 | 1.441 | 0.652 | 0.089 | -10.457 | 9.192 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | density | dense+intermediate+sparse+very_sparse | 588 | 257 | False | False | 132.785 | 134.044 | 67.283 | 65.036 | 34.235 | 29.111 | - | - | - |  |  | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | children_6_17 | 28 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | employed | 447 | 179 | False | False | 140.876 | 135.649 | 68.906 | 68.085 | 33.356 | 30.115 | - | - | - |  |  | 0.052 | 0.031 | 3.261 | 3.558 | 1.273 | 6.177 | -4.572 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | other_inactive | 48 | 27 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | retired | 47 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | unemployed | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q1+q2+q3+q4 | 323 | 164 | False | False | 133.953 | 136.045 | 68.562 | 62.088 | 35.694 | 27.383 | - | - | - |  |  | 0.020 | 0.038 | 2.511 | -5.566 | 4.224 | -6.264 | 8.266 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q5 | 265 | 93 | False | True | 130.753 | 129.609 | 65.061 | 71.569 | 31.851 | 33.131 | - | - | - |  |  | 0.035 | 0.083 | -4.425 | 9.510 | -7.116 | 12.617 | -17.052 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 0 | 178 | 80 | False | True | 112.298 | 143.072 | 31.751 | 56.392 | 17.598 | 23.649 | - | - | - |  |  | 0.144 | 0.129 | -91.813 | 81.355 | -10.029 | -19.754 | 28.783 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 1 | 256 | 102 | False | False | 135.764 | 131.147 | 77.865 | 68.087 | 39.430 | 31.150 | - | - | - |  |  | 0.066 | 0.069 | 19.612 | -18.967 | 2.334 | 6.078 | -8.975 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 2+ | 154 | 72 | False | True | 143.109 | 122.604 | 75.947 | 63.981 | 36.683 | 31.311 | - | - | - |  |  | 0.048 | 0.082 | 16.701 | -9.522 | 3.145 | -2.099 | -9.341 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple | 128 | 48 | False | True | 139.293 | - | 67.610 | - | 30.994 | - | - | - | - |  |  | 0.083 | - | 0.659 | 13.528 | -7.678 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple_with_children | 210 | 86 | False | True | 131.434 | 115.690 | 68.743 | 50.571 | 38.002 | 26.227 | - | - | - |  |  | 0.047 | 0.087 | 2.835 | -13.790 | 9.604 | -31.357 | 13.003 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | other | 18 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_parent | 60 | 32 | True | True | 135.311 | - | 73.774 | - | 32.713 | - | - | - | - |  |  | 0.133 | - | 12.345 | 6.097 | -15.915 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_person | 172 | 83 | False | True | 127.876 | 149.940 | 63.946 | 87.735 | 32.440 | 35.108 | - | - | - |  |  | 0.062 | 0.109 | -6.630 | 7.019 | -5.298 | 42.465 | -26.569 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | other | 101 | 55 | False | True | 112.905 | 153.467 | 51.793 | 84.649 | 27.899 | 33.094 | - | - | - |  |  | 0.170 | 0.180 | -32.073 | 25.089 | -12.895 | 37.831 | -18.408 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | work_study | 487 | 202 | False | False | 136.101 | 130.507 | 69.868 | 61.465 | 35.225 | 28.258 | - | - | - |  |  | 0.028 | 0.033 | 5.067 | -3.831 | 2.080 | -7.470 | 3.933 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | dense | 679 | 364 | False | False | 71.703 | 73.028 | 13.903 | 10.293 | 11.634 | 8.457 | - | - | - |  |  | 0.035 | 0.045 | -21.592 | 19.320 | 0.000 | -26.503 | 24.129 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | intermediate | 636 | 471 | False | False | 75.127 | 79.174 | 19.082 | 16.228 | 15.240 | 12.298 | - | - | - |  |  | 0.026 | 0.049 | 1.506 | -0.353 | 0.000 | 7.586 | -3.814 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | sparse+very_sparse | 95 | 85 | True | True | 77.743 | 67.265 | 38.194 | 22.369 | 29.478 | 19.953 | - | - | - |  |  | 0.137 | 0.126 | 54.164 | -50.395 | 0.000 | 29.863 | -38.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | children_6_17 | 140 | 175 | False | False | 66.801 | 69.345 | 22.708 | 16.390 | 20.396 | 14.182 | - | - | - |  |  | 0.150 | 0.108 | 13.657 | -20.831 | 0.000 | 7.819 | -13.875 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | employed | 710 | 343 | False | False | 74.835 | 75.465 | 15.748 | 14.748 | 12.626 | 11.725 | - | - | - |  |  | 0.049 | 0.049 | -12.784 | 13.645 | 0.000 | 0.187 | -0.124 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | other_inactive | 223 | 142 | False | False | 77.610 | 81.663 | 18.513 | 13.529 | 14.312 | 9.940 | - | - | - |  |  | 0.117 | 0.114 | -0.765 | 4.400 | 0.000 | -6.574 | 12.834 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | retired | 264 | 179 | False | False | 74.796 | 76.062 | 24.915 | 12.703 | 19.987 | 10.020 | - | - | - |  |  | 0.081 | 0.064 | 21.345 | -20.523 | 0.000 | -11.115 | 11.775 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | unemployed | 73 | 79 | True | True | 81.359 | 82.916 | 14.996 | 14.003 | 11.059 | 10.133 | - | - | - |  |  | 0.096 | 0.109 | -17.130 | 24.515 | 0.000 | -3.901 | 11.415 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q1 | 295 | 287 | False | False | 81.441 | 78.455 | 23.972 | 13.161 | 17.661 | 10.065 | - | - | - |  |  | 0.082 | 0.044 | 19.284 | -11.817 | 0.000 | -8.563 | 11.617 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q2 | 235 | 161 | False | False | 74.839 | 81.301 | 17.816 | 16.890 | 14.284 | 12.464 | - | - | - |  |  | 0.066 | 0.088 | -3.604 | 4.468 | 0.000 | 10.815 | -4.916 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q3 | 232 | 150 | False | False | 77.985 | 76.540 | 15.751 | 16.862 | 12.119 | 13.218 | - | - | - |  |  | 0.097 | 0.043 | -13.037 | 17.047 | 0.000 | 10.365 | -9.227 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q4 | 255 | 132 | False | False | 66.553 | 66.302 | 19.700 | 13.688 | 17.760 | 12.387 | - | - | - |  |  | 0.106 | 0.093 | 3.655 | -11.077 | 0.000 | -5.097 | -4.002 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q5 | 393 | 190 | False | False | 66.779 | 71.422 | 13.438 | 14.097 | 12.074 | 11.843 | - | - | - |  |  | 0.076 | 0.047 | -23.235 | 16.040 | 0.000 | -3.129 | -0.851 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 0 | 711 | 466 | False | False | 79.789 | 79.470 | 17.958 | 12.158 | 13.504 | 9.179 | - | - | - |  |  | 0.090 | 0.067 | -3.111 | 8.925 | 0.000 | -14.759 | 18.827 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 1 | 461 | 283 | False | False | 71.670 | 68.574 | 18.411 | 13.789 | 15.413 | 12.065 | - | - | - |  |  | 0.050 | 0.087 | -1.136 | -1.168 | 0.000 | -4.656 | -2.172 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 2+ | 238 | 166 | False | False | 67.248 | 77.657 | 20.497 | 20.069 | 18.288 | 15.506 | - | - | - |  |  | 0.117 | 0.071 | 6.472 | -13.199 | 0.000 | 23.768 | -21.513 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple | 262 | 124 | False | False | 72.223 | 71.289 | 17.660 | 13.092 | 14.671 | 11.018 | - | - | - |  |  | 0.037 | 0.098 | -4.183 | 2.432 | 0.000 | -8.552 | 4.439 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple_with_children | 369 | 262 | False | False | 73.655 | 75.723 | 18.708 | 17.762 | 15.240 | 14.074 | - | - | - |  |  | 0.040 | 0.031 | 0.031 | -0.350 | 0.000 | 14.239 | -13.918 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | other | 33 | 37 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_parent | 154 | 130 | False | False | 76.493 | 68.163 | 22.523 | 11.884 | 17.667 | 10.460 | - | - | - |  |  | 0.066 | 0.127 | 13.993 | -11.474 | 0.000 | -15.308 | 8.069 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_person | 592 | 367 | False | False | 75.003 | 76.935 | 18.506 | 12.430 | 14.804 | 9.694 | - | - | - |  |  | 0.076 | 0.024 | -0.779 | 1.808 | 0.000 | -12.830 | 14.363 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | other | 523 | 411 | False | False | 72.216 | 76.643 | 21.624 | 12.729 | 17.967 | 9.965 | - | - | - |  |  | 0.118 | 0.035 | 10.619 | -12.378 | 0.000 | -11.001 | 12.241 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | work_study | 887 | 509 | False | False | 74.817 | 74.790 | 17.299 | 15.688 | 13.873 | 12.586 | - | - | - |  |  | 0.057 | 0.017 | -5.794 | 6.637 | 0.000 | 4.830 | -5.442 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | dense | 956 | 603 | False | False | 34.129 | 38.038 | 2.101 | 2.139 | 3.723 | 3.374 | - | - | - |  |  | 0.086 | 0.131 | 4.195 | -0.540 | 0.186 | 5.860 | 0.298 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | intermediate | 1706 | 1258 | False | False | 31.288 | 32.052 | 1.898 | 1.811 | 3.640 | 3.390 | - | - | - |  |  | 0.031 | 0.021 | 0.885 | 0.183 | -0.069 | 0.054 | 0.119 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | sparse | 409 | 290 | False | False | 27.896 | 28.992 | 1.697 | 1.691 | 3.649 | 3.499 | - | - | - |  |  | 0.051 | 0.107 | -2.425 | 0.097 | -0.065 | -2.040 | -0.847 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | very_sparse | 575 | 264 | False | False | 20.386 | 18.467 | 1.224 | 1.067 | 3.603 | 3.465 | - | - | - |  |  | 0.186 | 0.263 | -10.253 | 0.406 | -0.056 | -12.967 | -0.445 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | children_6_17 | 462 | 341 | False | False | 29.108 | 29.241 | 1.760 | 1.557 | 3.627 | 3.196 | - | - | - |  |  | 0.025 | 0.055 | -1.393 | 0.278 | -0.066 | -4.558 | 1.920 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | employed | 1363 | 790 | False | False | 27.847 | 28.342 | 1.782 | 1.744 | 3.866 | 3.691 | - | - | - |  |  | 0.074 | 0.068 | -1.000 | -1.582 | 0.141 | -1.091 | -2.445 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | other_inactive | 469 | 266 | False | False | 32.786 | 39.924 | 2.109 | 2.303 | 3.860 | 3.460 | - | - | - |  |  | 0.061 | 0.158 | 4.234 | -1.666 | -0.070 | 8.644 | -0.599 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | retired | 1136 | 851 | False | False | 32.127 | 34.682 | 1.757 | 1.870 | 3.282 | 3.235 | - | - | - |  |  | 0.086 | 0.065 | -1.507 | 3.415 | -0.069 | 1.125 | 1.679 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | unemployed | 216 | 165 | False | False | 38.233 | 39.931 | 2.390 | 2.229 | 3.750 | 3.349 | - | - | - |  |  | 0.149 | 0.083 | 8.835 | -0.814 | -0.076 | 7.481 | 0.571 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q1 | 829 | 596 | False | False | 34.978 | 35.339 | 2.123 | 1.989 | 3.668 | 3.377 | - | - | - |  |  | 0.081 | 0.086 | 4.591 | -0.060 | 0.159 | 3.201 | 0.259 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q2 | 633 | 457 | False | False | 28.571 | 33.236 | 1.751 | 1.900 | 3.678 | 3.430 | - | - | - |  |  | 0.031 | 0.048 | -1.520 | -0.132 | -0.065 | 1.619 | -0.262 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q3 | 643 | 395 | False | False | 28.249 | 28.295 | 1.678 | 1.604 | 3.564 | 3.402 | - | - | - |  |  | 0.054 | 0.075 | -2.763 | 0.789 | -0.065 | -3.593 | 0.009 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q4 | 635 | 450 | False | False | 28.722 | 31.015 | 1.779 | 1.790 | 3.716 | 3.463 | - | - | - |  |  | 0.074 | 0.050 | -1.062 | -0.439 | -0.066 | -0.314 | -0.549 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q5 | 906 | 517 | False | False | 28.569 | 29.785 | 1.745 | 1.668 | 3.664 | 3.360 | - | - | - |  |  | 0.061 | 0.058 | -1.630 | -0.024 | -0.065 | -2.482 | 0.388 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 0 | 1173 | 774 | False | False | 37.249 | 38.037 | 2.272 | 2.060 | 3.659 | 3.250 | - | - | - |  |  | 0.151 | 0.104 | 7.012 | 0.023 | -0.075 | 4.554 | 1.605 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 1 | 1532 | 1004 | False | False | 29.204 | 32.954 | 1.773 | 1.870 | 3.642 | 3.404 | - | - | - |  |  | 0.026 | 0.029 | -1.179 | 0.161 | -0.066 | 1.085 | -0.010 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 2+ | 941 | 630 | False | False | 26.171 | 24.824 | 1.599 | 1.490 | 3.699 | 3.601 | - | - | - |  |  | 0.090 | 0.114 | -4.015 | -0.286 | 0.183 | -5.462 | -1.593 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple | 854 | 562 | False | False | 30.088 | 31.512 | 1.771 | 1.836 | 3.532 | 3.496 | - | - | - |  |  | 0.020 | 0.037 | -1.219 | 1.086 | -0.067 | 0.486 | -0.852 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple_with_children | 1081 | 664 | False | False | 28.680 | 28.710 | 1.774 | 1.664 | 3.731 | 3.477 | - | - | - |  |  | 0.051 | 0.045 | -1.144 | -0.553 | 0.088 | -2.521 | -0.648 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | other | 82 | 46 | True | True | 28.797 | - | 1.833 | - | 3.820 | - | - | - | - |  |  | 0.075 | - | -0.175 | -1.250 | -0.066 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_parent | 344 | 240 | False | False | 31.866 | 32.751 | 1.932 | 1.786 | 3.637 | 3.273 | - | - | - |  |  | 0.050 | 0.048 | 1.438 | 0.210 | -0.069 | -0.389 | 1.262 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_person | 1285 | 903 | False | False | 33.485 | 38.052 | 2.030 | 2.081 | 3.637 | 3.282 | - | - | - |  |  | 0.083 | 0.104 | 3.054 | 0.213 | -0.071 | 4.908 | 1.265 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | other | 2168 | 1517 | False | False | 30.705 | 35.328 | 1.823 | 1.943 | 3.563 | 3.300 | - | - | - |  |  | 0.018 | 0.053 | -0.348 | 0.832 | -0.068 | 2.419 | 1.029 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | work_study | 1478 | 897 | False | False | 29.819 | 28.248 | 1.868 | 1.665 | 3.776 | 3.537 | - | - | - |  |  | 0.020 | 0.056 | 0.381 | -0.929 | 0.078 | -2.474 | -1.157 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Mode-user composition

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 404 | 253 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | 8432 | 5616 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | 2066 | 1653 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | 625 | 329 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | 588 | 256 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | 1410 | 918 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | 3646 | 2413 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Per-mode decomposition

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Duration-rounding bounds

Scope: Round-trip days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`round-dest-daytable`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

## Round-trip days · all purposes · local (≤ 80 km)

### Subgroup mode-user days

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 83 | 59 | True | True | 42.077 | 48.313 | 7.849 | 8.245 | 11.192 | 10.239 | 1.148 | 0.833 | 1.501 | inconclusive | inconclusive | 0.066 | 0.138 | 3.844 | -4.314 | 0.000 | -3.469 | 1.051 | 0.000 |  |
| bike | density | intermediate | 178 | 130 | False | False | 41.081 | 46.922 | 7.081 | 9.542 | 10.341 | 12.201 | 1.142 | 0.939 | 1.354 | inconclusive | inconclusive | 0.082 | 0.079 | -0.510 | -0.956 | 0.000 | 3.712 | -7.520 | 0.000 |  |
| bike | density | sparse | 86 | 52 | True | True | 45.067 | 43.716 | 7.426 | 6.790 | 9.886 | 9.319 | 0.970 | 0.634 | 1.540 | inconclusive | inconclusive | 0.107 | 0.152 | 1.550 | 0.970 | 0.000 | -12.453 | 5.439 | 0.000 |  |
| bike | density | very_sparse | 146 | 50 | False | True | 43.433 | 77.669 | 6.351 | 10.595 | 8.773 | 8.185 | 1.788 | 1.034 | 2.509 | inconclusive | inconclusive | 0.170 | 0.201 | -5.200 | 6.086 | 0.000 | 11.433 | 15.506 | 0.000 |  |
| bike | population | children_6_17 | 93 | 37 | True | True | 28.853 | - | 4.650 | - | 9.669 | - | - | - | - |  |  | 0.214 | - | -15.257 | 1.564 | 0.000 | - | - | - |  |
| bike | population | employed | 197 | 135 | False | False | 50.654 | 46.890 | 8.656 | 9.439 | 10.253 | 12.078 | 0.926 | 0.767 | 1.120 | inconclusive | inconclusive | 0.123 | 0.072 | 8.770 | -0.663 | 0.000 | 3.184 | -7.024 | 0.000 |  |
| bike | population | other_inactive | 38 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | population | retired | 146 | 82 | False | True | 53.694 | 49.292 | 8.500 | 8.906 | 9.498 | 10.840 | 0.918 | 0.721 | 1.162 | inconclusive | inconclusive | 0.116 | 0.041 | 8.168 | 2.979 | 0.000 | 0.355 | -1.793 | 0.000 |  |
| bike | population | unemployed | 19 | 20 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | income | q1 | 94 | 50 | True | True | 47.973 | 56.440 | 8.183 | 7.871 | 10.235 | 8.367 | 1.176 | 0.752 | 1.811 | inconclusive | inconclusive | 0.169 | 0.096 | 5.991 | -0.565 | 0.000 | -6.233 | 11.943 | 0.000 |  |
| bike | income | q2 | 90 | 55 | True | True | 41.162 | 56.287 | 6.399 | 8.498 | 9.328 | 9.058 | 1.367 | 0.942 | 1.995 | inconclusive | inconclusive | 0.064 | 0.124 | -4.743 | 3.358 | 0.000 | -2.129 | 7.687 | 0.000 |  |
| bike | income | q3 | 95 | 58 | True | True | 40.652 | 52.842 | 6.656 | 10.115 | 9.824 | 11.486 | 1.300 | 1.016 | 1.666 | inconclusive | inconclusive | 0.095 | 0.116 | -3.078 | 1.183 | 0.000 | 6.961 | -4.850 | 0.000 |  |
| bike | income | q4 | 91 | 53 | True | True | 38.939 | 37.875 | 7.612 | 7.790 | 11.729 | 12.341 | 0.973 | 0.682 | 1.390 | inconclusive | inconclusive | 0.131 | 0.147 | 2.450 | -6.058 | 0.000 | -5.576 | -7.279 | 0.000 |  |
| bike | income | q5 | 123 | 75 | False | True | 44.175 | 52.359 | 6.968 | 10.085 | 9.465 | 11.557 | 1.185 | 0.943 | 1.516 | inconclusive | inconclusive | 0.062 | 0.118 | -1.221 | 2.849 | 0.000 | 6.774 | -5.146 | 0.000 |  |
| bike | vehicles | 0 | 104 | 60 | False | True | 40.221 | 52.410 | 7.315 | 8.236 | 10.912 | 9.429 | 1.303 | 0.980 | 1.756 | inconclusive | inconclusive | 0.087 | 0.120 | 0.843 | -3.169 | 0.000 | -3.663 | 5.343 | 0.000 |  |
| bike | vehicles | 1 | 183 | 112 | False | False | 48.395 | 50.185 | 8.275 | 9.840 | 10.260 | 11.765 | 1.037 | 0.847 | 1.318 | inconclusive | inconclusive | 0.125 | 0.072 | 6.527 | -0.680 | 0.000 | 5.394 | -5.939 | 0.000 |  |
| bike | vehicles | 2+ | 206 | 116 | False | False | 39.095 | 50.565 | 6.260 | 8.358 | 9.607 | 9.918 | 1.293 | 0.959 | 1.677 | inconclusive | inconclusive | 0.110 | 0.100 | -5.526 | 2.073 | 0.000 | -2.853 | 2.688 | 0.000 |  |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | couple | 153 | 89 | False | True | 49.845 | 44.515 | 7.902 | 8.390 | 9.512 | 11.309 | 0.893 | 0.708 | 1.099 | inconclusive | inconclusive | 0.104 | 0.047 | 4.498 | 2.800 | 0.000 | -2.497 | -3.718 | 0.000 |  |
| bike | household_type | couple_with_children | 167 | 85 | False | True | 39.080 | 51.202 | 6.723 | 8.807 | 10.322 | 10.321 | 1.310 | 0.984 | 1.670 | inconclusive | inconclusive | 0.074 | 0.066 | -2.612 | -0.855 | 0.000 | -0.205 | 0.677 | 0.000 |  |
| bike | household_type | other | 12 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_parent | 36 | 30 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_person | 125 | 81 | False | True | 48.176 | 52.111 | 8.731 | 9.490 | 10.874 | 10.927 | 1.082 | 0.905 | 1.369 | inconclusive | inconclusive | 0.259 | 0.112 | 8.942 | -3.312 | 0.000 | 3.632 | -2.251 | 0.000 |  |
| bike | day_purpose | other | 279 | 155 | False | False | 43.496 | 58.046 | 6.862 | 9.317 | 9.466 | 9.630 | 1.335 | 1.041 | 1.659 | inconclusive | inconclusive | 0.039 | 0.068 | -1.872 | 2.821 | 0.000 | 2.836 | 4.481 | 0.000 |  |
| bike | day_purpose | work_study | 214 | 136 | False | False | 41.207 | 42.833 | 7.598 | 8.331 | 11.064 | 11.670 | 1.039 | 0.861 | 1.263 | inconclusive | inconclusive | 0.055 | 0.074 | 2.445 | -3.785 | 0.000 | -2.782 | -5.116 | 0.000 |  |
| car_driver | density | dense | 637 | 431 | False | False | 62.006 | 68.077 | 28.662 | 28.144 | 27.735 | 24.805 | 1.098 | 1.004 | 1.187 | inconclusive | inconclusive | 0.053 | 0.064 | -16.299 | 16.610 | -0.032 | -22.698 | 23.510 | 0.000 |  |
| car_driver | density | intermediate | 3150 | 2415 | False | False | 62.517 | 67.318 | 33.104 | 34.436 | 31.772 | 30.692 | 1.077 | 1.033 | 1.132 | equivalent | inconclusive | 0.018 | 0.015 | -7.417 | 8.237 | -0.030 | -8.994 | 9.046 | 0.000 |  |
| car_driver | density | sparse | 1216 | 1015 | False | False | 59.546 | 64.012 | 38.524 | 41.877 | 38.818 | 39.253 | 1.075 | 0.979 | 1.157 | inconclusive | inconclusive | 0.060 | 0.042 | 1.955 | -4.105 | -0.032 | 4.069 | -7.323 | 0.000 |  |
| car_driver | density | very_sparse | 3406 | 1728 | False | False | 61.912 | 69.478 | 44.879 | 48.845 | 43.565 | 42.181 | 1.122 | 1.066 | 1.180 | inconclusive | inconclusive | 0.022 | 0.030 | 11.432 | -11.317 | 0.070 | 14.760 | -12.547 | 0.000 |  |
| car_driver | population | children_6_17 | 78 | 42 | True | True | 44.658 | - | 25.715 | - | 34.549 | - | - | - | - |  |  | 0.201 | - | -19.615 | 2.574 | -0.027 | - | - | - |  |
| car_driver | population | employed | 5238 | 3061 | False | False | 66.256 | 73.891 | 41.254 | 45.323 | 37.386 | 36.803 | 1.115 | 1.079 | 1.159 | inconclusive | inconclusive | 0.051 | 0.082 | 6.442 | -1.927 | 0.014 | 9.950 | -3.323 | 0.000 |  |
| car_driver | population | other_inactive | 607 | 290 | False | False | 54.087 | 60.748 | 29.726 | 33.967 | 32.975 | 33.549 | 1.123 | 1.002 | 1.271 | inconclusive | inconclusive | 0.100 | 0.099 | -13.127 | 5.518 | -0.030 | -9.423 | 2.906 | 0.000 |  |
| car_driver | population | retired | 2163 | 1929 | False | False | 52.501 | 53.291 | 29.092 | 27.034 | 33.247 | 30.438 | 1.015 | 0.962 | 1.072 | equivalent | equivalent | 0.110 | 0.169 | -14.167 | 4.970 | -0.030 | -22.541 | 8.567 | 0.000 |  |
| car_driver | population | unemployed | 323 | 263 | False | False | 57.880 | 63.841 | 34.906 | 33.031 | 36.185 | 31.044 | 1.103 | 0.959 | 1.252 | inconclusive | inconclusive | 0.055 | 0.076 | -3.967 | 0.152 | -0.031 | -11.488 | 8.064 | 0.000 |  |
| car_driver | income | q1 | 990 | 625 | False | False | 53.531 | 61.500 | 31.239 | 33.421 | 35.014 | 32.606 | 1.149 | 1.051 | 1.256 | inconclusive | inconclusive | 0.103 | 0.077 | -10.204 | 2.039 | -0.030 | -10.524 | 4.759 | 0.000 |  |
| car_driver | income | q2 | 1334 | 1045 | False | False | 57.650 | 60.875 | 34.836 | 35.382 | 36.272 | 34.874 | 1.056 | 0.985 | 1.135 | equivalent | inconclusive | 0.047 | 0.060 | -4.080 | 0.008 | -0.004 | -6.821 | 0.430 | 0.000 |  |
| car_driver | income | q3 | 1741 | 1179 | False | False | 60.375 | 64.976 | 35.991 | 39.211 | 35.768 | 36.208 | 1.076 | 0.990 | 1.151 | inconclusive | inconclusive | 0.025 | 0.036 | -2.183 | 0.863 | -0.032 | -0.251 | -2.038 | 0.000 |  |
| car_driver | income | q4 | 1866 | 1340 | False | False | 63.780 | 70.309 | 39.989 | 41.501 | 37.686 | 35.416 | 1.102 | 1.042 | 1.163 | inconclusive | inconclusive | 0.041 | 0.036 | 4.365 | -2.391 | 0.080 | 3.643 | -0.600 | 0.000 |  |
| car_driver | income | q5 | 2478 | 1400 | False | False | 68.584 | 74.229 | 41.147 | 43.465 | 36.000 | 35.134 | 1.082 | 1.029 | 1.141 | equivalent | inconclusive | 0.083 | 0.074 | 6.386 | 0.499 | -0.028 | 7.014 | -0.050 | 0.000 |  |
| car_driver | vehicles | 0 | 57 | 58 | True | True | 66.308 | 66.250 | 40.116 | 34.553 | 36.299 | 31.293 | 0.999 | 0.690 | 1.407 | inconclusive | inconclusive | 0.162 | 0.170 | 4.655 | -0.040 | -0.033 | -8.695 | 7.680 | 0.000 |  |
| car_driver | vehicles | 1 | 3299 | 2501 | False | False | 59.739 | 63.705 | 33.061 | 33.257 | 33.205 | 31.323 | 1.066 | 1.017 | 1.122 | equivalent | inconclusive | 0.053 | 0.041 | -7.329 | 5.373 | -0.032 | -11.031 | 7.470 | 0.000 |  |
| car_driver | vehicles | 2+ | 5053 | 3021 | False | False | 62.900 | 69.549 | 39.891 | 43.298 | 38.083 | 37.353 | 1.106 | 1.068 | 1.148 | equivalent | inconclusive | 0.034 | 0.028 | 4.182 | -3.028 | 0.019 | 6.523 | -4.239 | 0.000 |  |
| car_driver | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_driver | household_type | couple | 2913 | 1958 | False | False | 59.338 | 60.573 | 35.448 | 34.774 | 35.847 | 34.445 | 1.021 | 0.964 | 1.075 | equivalent | equivalent | 0.051 | 0.083 | -3.084 | 0.722 | -0.026 | -7.911 | 1.219 | 0.000 |  |
| car_driver | household_type | couple_with_children | 3155 | 1594 | False | False | 65.158 | 74.142 | 40.349 | 45.480 | 37.161 | 36.805 | 1.138 | 1.087 | 1.191 | inconclusive | inconclusive | 0.046 | 0.074 | 4.981 | -1.527 | -0.022 | 10.210 | -3.334 | 0.000 |  |
| car_driver | household_type | other | 170 | 87 | False | True | 58.143 | 59.158 | 34.855 | 32.007 | 36.472 | 32.462 | 1.017 | 0.855 | 1.224 | inconclusive | inconclusive | 0.085 | 0.123 | -4.064 | -0.321 | 0.801 | -13.054 | 4.947 | 0.000 |  |
| car_driver | household_type | single_parent | 523 | 341 | False | False | 55.259 | 67.084 | 30.372 | 37.045 | 32.978 | 33.133 | 1.214 | 1.099 | 1.338 | inconclusive | inconclusive | 0.068 | 0.034 | -12.009 | 5.572 | -0.030 | -4.071 | 3.890 | 0.000 |  |
| car_driver | household_type | single_person | 1648 | 1609 | False | False | 57.967 | 61.973 | 33.770 | 33.319 | 34.955 | 32.258 | 1.069 | 1.012 | 1.138 | equivalent | inconclusive | 0.055 | 0.062 | -5.950 | 2.221 | -0.031 | -10.761 | 5.468 | 0.000 |  |
| car_driver | day_purpose | other | 4055 | 3053 | False | False | 53.678 | 56.463 | 31.088 | 30.681 | 34.749 | 32.603 | 1.052 | 1.004 | 1.102 | equivalent | inconclusive | 0.102 | 0.130 | -10.497 | 2.479 | -0.030 | -15.371 | 4.569 | 0.000 |  |
| car_driver | day_purpose | work_study | 4354 | 2536 | False | False | 68.282 | 76.314 | 42.363 | 46.630 | 37.256 | 36.661 | 1.118 | 1.078 | 1.166 | inconclusive | inconclusive | 0.083 | 0.109 | 8.264 | -1.730 | 0.022 | 12.152 | -3.103 | 0.000 |  |
| car_passenger | density | dense | 189 | 161 | False | False | 39.844 | 47.659 | 17.962 | 18.077 | 27.049 | 22.759 | 1.196 | 0.979 | 1.487 | inconclusive | inconclusive | 0.061 | 0.108 | -11.491 | 10.631 | 0.000 | -14.651 | 16.638 | 0.000 |  |
| car_passenger | density | intermediate | 798 | 770 | False | False | 38.840 | 44.450 | 19.504 | 21.164 | 30.130 | 28.568 | 1.144 | 1.031 | 1.250 | inconclusive | inconclusive | 0.031 | 0.035 | -8.072 | 6.208 | 0.000 | -7.046 | 5.824 | 0.000 |  |
| car_passenger | density | sparse | 288 | 290 | False | False | 41.392 | 43.974 | 26.734 | 26.977 | 38.752 | 36.808 | 1.062 | 0.894 | 1.236 | inconclusive | inconclusive | 0.062 | 0.051 | 4.610 | -3.922 | 0.000 | 3.867 | -5.566 | 0.000 |  |
| car_passenger | density | very_sparse | 779 | 414 | False | False | 43.439 | 48.890 | 30.741 | 32.866 | 42.461 | 40.335 | 1.125 | 1.009 | 1.245 | inconclusive | inconclusive | 0.073 | 0.064 | 10.597 | -7.862 | 0.000 | 13.412 | -10.194 | 0.000 |  |
| car_passenger | population | children_6_17 | 614 | 443 | False | False | 31.721 | 35.819 | 16.862 | 17.282 | 31.895 | 28.950 | 1.129 | 1.017 | 1.236 | inconclusive | inconclusive | 0.122 | 0.129 | -12.556 | 3.573 | 0.000 | -14.556 | 4.703 | 0.000 |  |
| car_passenger | population | employed | 577 | 320 | False | False | 44.270 | 52.426 | 26.213 | 31.515 | 35.528 | 36.068 | 1.184 | 1.055 | 1.338 | inconclusive | inconclusive | 0.073 | 0.088 | 3.934 | -0.368 | 0.000 | 11.841 | -5.087 | 0.000 |  |
| car_passenger | population | other_inactive | 239 | 181 | False | False | 49.400 | 50.589 | 26.332 | 25.116 | 31.982 | 29.788 | 1.024 | 0.837 | 1.279 | inconclusive | inconclusive | 0.141 | 0.074 | 4.364 | 4.333 | 0.000 | 0.713 | 4.204 | 0.000 |  |
| car_passenger | population | retired | 540 | 617 | False | False | 53.041 | 57.535 | 36.557 | 34.262 | 41.353 | 35.730 | 1.085 | 0.959 | 1.207 | inconclusive | inconclusive | 0.148 | 0.171 | 19.817 | -7.480 | 0.000 | 16.716 | -4.853 | 0.000 |  |
| car_passenger | population | unemployed | 83 | 72 | True | True | 49.086 | 44.592 | 31.388 | 23.006 | 38.366 | 30.955 | 0.908 | 0.731 | 1.124 | inconclusive | inconclusive | 0.203 | 0.126 | 12.212 | -3.829 | 0.000 | -3.291 | 2.211 | 0.000 |  |
| car_passenger | income | q1 | 366 | 311 | False | False | 40.060 | 44.667 | 22.260 | 20.947 | 33.340 | 28.137 | 1.115 | 0.958 | 1.261 | inconclusive | inconclusive | 0.053 | 0.045 | -2.860 | 2.216 | 0.000 | -7.529 | 6.524 | 0.000 |  |
| car_passenger | income | q2 | 415 | 376 | False | False | 36.036 | 46.245 | 20.928 | 26.405 | 34.846 | 34.258 | 1.283 | 1.128 | 1.435 | inconclusive | different | 0.091 | 0.044 | -5.078 | 0.410 | 0.000 | 2.981 | -2.408 | 0.000 |  |
| car_passenger | income | q3 | 420 | 332 | False | False | 46.250 | 46.020 | 27.833 | 26.578 | 36.109 | 34.652 | 0.995 | 0.862 | 1.163 | inconclusive | inconclusive | 0.103 | 0.049 | 6.627 | -1.081 | 0.000 | 3.274 | -2.926 | 0.000 |  |
| car_passenger | income | q4 | 395 | 331 | False | False | 39.197 | 44.744 | 23.492 | 23.692 | 35.959 | 31.770 | 1.142 | 1.027 | 1.280 | inconclusive | inconclusive | 0.038 | 0.024 | -0.677 | -0.829 | 0.000 | -1.969 | 1.041 | 0.000 |  |
| car_passenger | income | q5 | 458 | 285 | False | False | 42.982 | 46.795 | 25.404 | 26.085 | 35.463 | 33.446 | 1.089 | 0.968 | 1.205 | inconclusive | inconclusive | 0.049 | 0.046 | 2.565 | -0.287 | 0.000 | 2.436 | -1.313 | 0.000 |  |
| car_passenger | vehicles | 0 | 256 | 249 | False | False | 39.931 | 45.043 | 19.958 | 20.931 | 29.988 | 27.882 | 1.128 | 0.944 | 1.335 | inconclusive | inconclusive | 0.076 | 0.071 | -7.257 | 6.484 | 0.000 | -7.594 | 6.965 | 0.000 |  |
| car_passenger | vehicles | 1 | 740 | 620 | False | False | 41.997 | 46.196 | 23.468 | 23.589 | 33.529 | 30.638 | 1.100 | 0.991 | 1.216 | inconclusive | inconclusive | 0.060 | 0.027 | -0.742 | 2.036 | 0.000 | -2.200 | 2.723 | 0.000 |  |
| car_passenger | vehicles | 2+ | 1058 | 763 | False | False | 39.973 | 45.384 | 24.798 | 26.119 | 37.222 | 34.531 | 1.135 | 1.048 | 1.239 | inconclusive | inconclusive | 0.041 | 0.018 | 1.499 | -2.230 | 0.000 | 2.458 | -2.746 | 0.000 |  |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_passenger | household_type | couple | 605 | 557 | False | False | 52.858 | 56.951 | 34.367 | 34.240 | 39.011 | 36.074 | 1.077 | 0.968 | 1.205 | inconclusive | inconclusive | 0.155 | 0.171 | 16.908 | -4.754 | 0.000 | 16.595 | -5.316 | 0.000 |  |
| car_passenger | household_type | couple_with_children | 896 | 559 | False | False | 36.638 | 40.977 | 20.518 | 21.480 | 33.602 | 31.451 | 1.118 | 1.029 | 1.228 | inconclusive | inconclusive | 0.050 | 0.067 | -5.884 | 1.818 | 0.000 | -6.128 | 1.432 | 0.000 |  |
| car_passenger | household_type | other | 66 | 37 | True | True | 44.919 | - | 32.103 | - | 42.882 | - | - | - | - |  |  | 0.090 | - | 12.634 | -8.419 | 0.000 | - | - | - |  |
| car_passenger | household_type | single_parent | 160 | 148 | False | False | 39.990 | 40.066 | 20.544 | 18.394 | 30.824 | 27.546 | 1.002 | 0.834 | 1.213 | inconclusive | inconclusive | 0.040 | 0.061 | -6.095 | 5.380 | 0.000 | -12.698 | 7.092 | 0.000 |  |
| car_passenger | household_type | single_person | 327 | 334 | False | False | 37.696 | 48.953 | 20.901 | 25.349 | 33.267 | 31.069 | 1.299 | 1.124 | 1.512 | inconclusive | different | 0.086 | 0.056 | -5.243 | 2.236 | 0.000 | 1.137 | 2.143 | 0.000 |  |
| car_passenger | day_purpose | other | 1129 | 1090 | False | False | 48.978 | 54.682 | 31.143 | 32.309 | 38.151 | 35.451 | 1.116 | 1.033 | 1.213 | inconclusive | inconclusive | 0.113 | 0.113 | 11.848 | -3.574 | 0.000 | 13.345 | -4.335 | 0.000 |  |
| car_passenger | day_purpose | work_study | 925 | 545 | False | False | 33.611 | 35.706 | 17.679 | 16.381 | 31.560 | 27.526 | 1.062 | 0.964 | 1.170 | inconclusive | inconclusive | 0.097 | 0.125 | -11.159 | 4.065 | 0.000 | -16.702 | 6.736 | 0.000 |  |
| other | density | dense+intermediate | 259 | 171 | False | False | 57.970 | 59.088 | 23.610 | 24.252 | 24.441 | 24.627 | 1.019 | 0.866 | 1.197 | inconclusive | inconclusive | 0.038 | 0.061 | -4.456 | 3.436 | -0.268 | -14.831 | 9.765 | 0.000 |  |
| other | density | sparse+very_sparse | 363 | 156 | False | False | 60.213 | 69.343 | 26.856 | 37.619 | 26.976 | 32.550 | 1.152 | 0.990 | 1.334 | inconclusive | inconclusive | 0.028 | 0.062 | 3.153 | -2.394 | 0.196 | 13.221 | -8.032 | 0.000 |  |
| other | population | children_6_17 | 266 | 86 | False | True | 57.767 | 57.204 | 21.881 | 19.108 | 22.727 | 20.042 | 0.990 | 0.823 | 1.178 | inconclusive | inconclusive | 0.050 | 0.088 | -8.898 | 7.683 | -0.277 | -29.046 | 22.096 | 0.000 |  |
| other | population | employed | 247 | 146 | False | False | 64.872 | 71.107 | 33.119 | 38.724 | 31.033 | 32.675 | 1.096 | 0.929 | 1.291 | inconclusive | inconclusive | 0.112 | 0.063 | 16.275 | -11.176 | 0.514 | 15.348 | -8.395 | 0.000 |  |
| other | population | other_inactive | 36 | 24 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | population | retired | 62 | 62 | True | True | 49.089 | 60.312 | 21.161 | 33.752 | 25.899 | 33.577 | 1.229 | 0.869 | 1.803 | inconclusive | inconclusive | 0.217 | 0.128 | -10.022 | 0.035 | -0.182 | 5.580 | -9.423 | 0.000 |  |
| other | population | unemployed | 11 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | income | q1 | 109 | 59 | False | True | 58.529 | 69.367 | 26.275 | 38.322 | 26.935 | 33.147 | 1.185 | 0.940 | 1.519 | inconclusive | inconclusive | 0.039 | 0.169 | 1.820 | -2.272 | -0.279 | 14.459 | -9.247 | 0.000 |  |
| other | income | q2 | 149 | 71 | False | True | 64.798 | 50.723 | 25.168 | 20.531 | 23.560 | 24.287 | 0.783 | 0.642 | 0.982 | inconclusive | inconclusive | 0.091 | 0.121 | -0.751 | 5.908 | 0.383 | -23.292 | 9.861 | 0.000 |  |
| other | income | q3 | 102 | 68 | False | True | 58.373 | 76.245 | 22.971 | 37.670 | 23.686 | 29.644 | 1.306 | 1.000 | 1.692 | inconclusive | inconclusive | 0.086 | 0.144 | -6.084 | 5.293 | -0.094 | 13.972 | -1.881 | 0.000 |  |
| other | income | q4 | 122 | 53 | False | True | 52.366 | 51.530 | 26.813 | 23.058 | 30.884 | 26.848 | 0.984 | 0.809 | 1.217 | inconclusive | inconclusive | 0.130 | 0.218 | 2.853 | -9.776 | 0.032 | -16.784 | 4.159 | 0.000 |  |
| other | income | q5 | 140 | 76 | False | True | 61.145 | 67.873 | 26.121 | 32.046 | 25.693 | 28.329 | 1.110 | 0.895 | 1.441 | inconclusive | inconclusive | 0.039 | 0.051 | 1.508 | 0.520 | -0.141 | 2.498 | 1.220 | 0.000 |  |
| other | vehicles | 0 | 89 | 61 | True | True | 52.981 | 57.302 | 18.736 | 27.853 | 21.218 | 29.164 | 1.082 | 0.851 | 1.400 | inconclusive | inconclusive | 0.134 | 0.099 | -17.224 | 11.212 | -0.265 | -6.211 | -0.641 | 0.000 |  |
| other | vehicles | 1 | 201 | 115 | False | False | 59.620 | 60.558 | 27.168 | 26.252 | 27.381 | 26.010 | 1.016 | 0.865 | 1.211 | inconclusive | inconclusive | 0.045 | 0.060 | 3.825 | -3.269 | -0.195 | -10.073 | 6.477 | 0.000 |  |
| other | vehicles | 2+ | 332 | 151 | False | False | 60.191 | 68.426 | 25.716 | 35.077 | 25.825 | 30.758 | 1.137 | 0.974 | 1.360 | inconclusive | inconclusive | 0.027 | 0.035 | 0.563 | 0.211 | 0.159 | 8.496 | -4.225 | 0.000 |  |
| other | household_type | couple | 83 | 86 | True | True | 51.681 | 66.768 | 26.921 | 33.563 | 31.395 | 30.161 | 1.292 | 1.003 | 1.731 | inconclusive | inconclusive | 0.204 | 0.045 | 3.058 | -10.621 | -0.014 | 5.504 | -2.890 | 0.000 |  |
| other | household_type | couple_with_children | 356 | 126 | False | False | 63.730 | 63.171 | 27.531 | 29.119 | 26.079 | 27.658 | 0.991 | 0.847 | 1.173 | inconclusive | inconclusive | 0.068 | 0.041 | 4.771 | -0.385 | 0.086 | -3.688 | 2.704 | 0.000 |  |
| other | household_type | other | 19 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | household_type | single_parent | 60 | 36 | True | True | 55.576 | - | 19.878 | - | 21.460 | - | - | - | - |  |  | 0.122 | - | -14.239 | 10.828 | -0.272 | - | - | - |  |
| other | household_type | single_person | 104 | 73 | False | True | 50.340 | 67.110 | 20.260 | 43.603 | 24.148 | 38.983 | 1.333 | 0.992 | 1.800 | inconclusive | inconclusive | 0.221 | 0.111 | -12.524 | 3.864 | -0.259 | 22.692 | -19.736 | 0.000 |  |
| other | day_purpose | other | 113 | 108 | False | False | 46.500 | 61.099 | 19.747 | 33.439 | 25.494 | 32.838 | 1.314 | 1.041 | 1.764 | inconclusive | inconclusive | 0.172 | 0.123 | -13.401 | 0.864 | -0.222 | 5.034 | -8.090 | 0.000 |  |
| other | day_purpose | work_study | 509 | 219 | False | False | 61.680 | 64.989 | 26.562 | 30.151 | 25.977 | 27.837 | 1.054 | 0.935 | 1.196 | inconclusive | inconclusive | 0.033 | 0.033 | 2.527 | -0.141 | 0.037 | -1.493 | 2.326 | 0.000 |  |
| train | density | dense+intermediate+sparse+very_sparse | 563 | 241 | False | False | 117.541 | 127.483 | 44.873 | 53.323 | 23.363 | 25.096 | 1.085 | 0.983 | 1.179 | inconclusive | inconclusive | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 |  |
| train | population | children_6_17 | 27 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | employed | 423 | 168 | False | False | 120.904 | 129.159 | 47.440 | 56.162 | 23.610 | 26.090 | 1.068 | 0.958 | 1.189 | inconclusive | inconclusive | 0.049 | 0.032 | 6.631 | -1.253 | -2.015 | 6.656 | -4.980 | 0.000 |  |
| train | population | other_inactive | 47 | 25 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | retired | 48 | 23 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | unemployed | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | income | q1+q2+q3+q4 | 310 | 154 | False | False | 117.074 | 128.223 | 45.345 | 50.606 | 23.433 | 23.680 | 1.095 | 0.975 | 1.231 | inconclusive | inconclusive | 0.016 | 0.047 | 1.226 | -0.348 | -1.345 | -6.685 | 7.425 | 0.000 |  |
| train | income | q5 | 253 | 87 | False | True | 118.301 | 125.870 | 44.104 | 59.247 | 23.248 | 28.242 | 1.064 | 0.935 | 1.200 | inconclusive | inconclusive | 0.027 | 0.103 | -2.038 | 0.585 | 2.214 | 13.346 | -14.960 | 0.000 |  |
| train | vehicles | 0 | 177 | 77 | False | True | 110.293 | 136.143 | 32.367 | 46.852 | 17.608 | 20.648 | 1.234 | 0.999 | 1.431 | inconclusive | inconclusive | 0.107 | 0.130 | -37.203 | 32.206 | -2.251 | -17.048 | 25.708 | 0.000 |  |
| train | vehicles | 1 | 242 | 94 | False | True | 121.329 | 122.022 | 47.782 | 53.726 | 24.356 | 26.418 | 1.006 | 0.881 | 1.152 | inconclusive | inconclusive | 0.052 | 0.087 | 7.500 | -4.968 | 1.256 | 0.941 | -6.402 | 0.000 |  |
| train | vehicles | 2+ | 144 | 67 | False | True | 117.430 | 118.908 | 50.579 | 53.510 | 26.308 | 27.001 | 1.013 | 0.845 | 1.242 | inconclusive | inconclusive | 0.062 | 0.087 | 14.061 | -13.945 | -0.227 | 0.432 | -9.007 | 0.000 |  |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | couple | 124 | 47 | False | True | 125.899 | - | 51.688 | - | 24.633 | - | - | - | - |  |  | 0.081 | - | 17.202 | -6.439 | -2.405 | - | - | - |  |
| train | household_type | couple_with_children | 199 | 84 | False | True | 111.173 | 114.491 | 41.230 | 48.274 | 23.198 | 25.299 | 1.030 | 0.871 | 1.196 | inconclusive | inconclusive | 0.064 | 0.079 | -9.681 | 0.811 | 2.503 | -12.023 | -0.970 | 0.000 |  |
| train | household_type | other | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | single_parent | 58 | 31 | True | True | 124.503 | - | 43.930 | - | 21.170 | - | - | - | - |  |  | 0.120 | - | -2.572 | 11.927 | -2.391 | - | - | - |  |
| train | household_type | single_person | 164 | 72 | False | True | 118.368 | 129.122 | 48.218 | 49.894 | 24.442 | 23.185 | 1.091 | 0.968 | 1.215 | inconclusive | inconclusive | 0.039 | 0.065 | 8.480 | -5.321 | -2.331 | -8.527 | 10.166 | 0.000 |  |
| train | day_purpose | other | 101 | 49 | False | True | 109.972 | - | 39.476 | - | 21.538 | - | - | - | - |  |  | 0.117 | - | -14.574 | 9.253 | -2.248 | - | - | - |  |
| train | day_purpose | work_study | 462 | 192 | False | False | 118.964 | 125.849 | 45.889 | 53.627 | 23.688 | 25.567 | 1.058 | 0.944 | 1.163 | inconclusive | inconclusive | 0.022 | 0.032 | 2.646 | -1.634 | 0.411 | 0.721 | -2.355 | 0.000 |  |
| urban_pt | density | dense | 678 | 364 | False | False | 71.410 | 74.194 | 12.895 | 10.479 | 10.835 | 8.474 | 1.039 | 0.941 | 1.136 | equivalent | inconclusive | 0.032 | 0.047 | -15.457 | 14.194 | 0.000 | -23.461 | 21.994 | 0.000 |  |
| urban_pt | density | intermediate | 635 | 470 | False | False | 74.372 | 78.950 | 16.938 | 15.515 | 13.665 | 11.791 | 1.062 | 0.965 | 1.158 | inconclusive | inconclusive | 0.026 | 0.050 | 4.273 | -2.574 | 0.000 | 6.132 | -2.842 | 0.000 |  |
| urban_pt | density | sparse+very_sparse | 89 | 84 | True | True | 68.487 | 66.659 | 25.192 | 21.616 | 22.070 | 19.457 | 0.973 | 0.770 | 1.272 | inconclusive | inconclusive | 0.142 | 0.130 | 32.113 | -36.299 | 0.000 | 29.206 | -38.207 | 0.000 |  |
| urban_pt | population | children_6_17 | 139 | 175 | False | False | 63.796 | 69.771 | 18.027 | 16.442 | 16.954 | 14.139 | 1.094 | 0.865 | 1.345 | inconclusive | inconclusive | 0.162 | 0.111 | 8.206 | -17.083 | 0.000 | 9.982 | -15.871 | 0.000 |  |
| urban_pt | population | employed | 707 | 342 | False | False | 74.776 | 75.827 | 14.616 | 13.946 | 11.728 | 11.035 | 1.014 | 0.929 | 1.091 | equivalent | equivalent | 0.056 | 0.052 | -6.585 | 8.688 | 0.000 | -2.066 | 2.233 | 0.000 |  |
| urban_pt | population | other_inactive | 222 | 142 | False | False | 78.064 | 81.663 | 18.608 | 13.529 | 14.302 | 9.940 | 1.046 | 0.915 | 1.187 | inconclusive | inconclusive | 0.122 | 0.107 | 11.463 | -6.071 | 0.000 | -4.531 | 10.533 | 0.000 |  |
| urban_pt | population | retired | 261 | 178 | False | False | 68.490 | 75.933 | 13.874 | 11.792 | 12.154 | 9.318 | 1.109 | 0.997 | 1.245 | inconclusive | inconclusive | 0.091 | 0.060 | -9.977 | 5.794 | 0.000 | -14.784 | 15.056 | 0.000 |  |
| urban_pt | population | unemployed | 73 | 79 | True | True | 80.314 | 83.220 | 14.828 | 14.058 | 11.077 | 10.135 | 1.036 | 0.758 | 1.393 | inconclusive | inconclusive | 0.118 | 0.106 | -5.726 | 13.367 | 0.000 | -1.532 | 9.091 | 0.000 |  |
| urban_pt | income | q1 | 293 | 288 | False | False | 79.658 | 79.392 | 20.428 | 13.287 | 15.387 | 10.042 | 0.997 | 0.865 | 1.151 | inconclusive | inconclusive | 0.080 | 0.043 | 18.686 | -11.701 | 0.000 | -5.866 | 9.598 | 0.000 |  |
| urban_pt | income | q2 | 233 | 160 | False | False | 73.878 | 80.736 | 14.840 | 14.767 | 12.052 | 10.974 | 1.093 | 0.960 | 1.245 | inconclusive | inconclusive | 0.068 | 0.094 | -5.429 | 6.633 | 0.000 | 2.340 | 2.736 | 0.000 |  |
| urban_pt | income | q3 | 233 | 149 | False | False | 76.001 | 76.734 | 14.567 | 16.463 | 11.500 | 12.873 | 1.010 | 0.885 | 1.139 | equivalent | inconclusive | 0.095 | 0.043 | -6.889 | 10.217 | 0.000 | 10.566 | -9.492 | 0.000 |  |
| urban_pt | income | q4 | 250 | 132 | False | False | 63.901 | 66.376 | 14.777 | 13.702 | 13.875 | 12.386 | 1.039 | 0.905 | 1.221 | inconclusive | inconclusive | 0.109 | 0.100 | -5.344 | -3.429 | 0.000 | -3.188 | -6.096 | 0.000 |  |
| urban_pt | income | q5 | 393 | 189 | False | False | 67.724 | 71.547 | 13.422 | 14.122 | 11.892 | 11.843 | 1.056 | 0.954 | 1.160 | inconclusive | inconclusive | 0.066 | 0.051 | -12.244 | 7.295 | 0.000 | -1.084 | -3.029 | 0.000 |  |
| urban_pt | vehicles | 0 | 711 | 467 | False | False | 79.953 | 80.119 | 17.180 | 12.253 | 12.893 | 9.176 | 1.002 | 0.907 | 1.115 | equivalent | inconclusive | 0.088 | 0.062 | 5.516 | 1.764 | 0.000 | -12.205 | 16.663 | 0.000 |  |
| urban_pt | vehicles | 1 | 454 | 280 | False | False | 68.826 | 68.209 | 13.471 | 12.393 | 11.744 | 10.902 | 0.991 | 0.906 | 1.080 | equivalent | equivalent | 0.056 | 0.081 | -12.087 | 8.240 | 0.000 | -10.445 | 2.994 | 0.000 |  |
| urban_pt | vehicles | 2+ | 237 | 166 | False | False | 65.635 | 78.077 | 17.815 | 20.260 | 16.286 | 15.569 | 1.190 | 1.026 | 1.381 | inconclusive | inconclusive | 0.116 | 0.068 | 7.505 | -14.543 | 0.000 | 26.607 | -24.191 | 0.000 |  |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | couple | 261 | 124 | False | False | 71.158 | 71.713 | 14.947 | 13.427 | 12.603 | 11.234 | 1.008 | 0.904 | 1.149 | equivalent | inconclusive | 0.030 | 0.093 | -4.812 | 3.298 | 0.000 | -4.806 | 0.859 | 0.000 |  |
| urban_pt | household_type | couple_with_children | 367 | 261 | False | False | 71.412 | 75.977 | 15.045 | 17.133 | 12.641 | 13.530 | 1.064 | 0.960 | 1.181 | inconclusive | inconclusive | 0.041 | 0.030 | -4.349 | 3.089 | 0.000 | 13.536 | -13.220 | 0.000 |  |
| urban_pt | household_type | other | 32 | 37 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | single_parent | 152 | 130 | False | False | 77.300 | 68.587 | 22.736 | 11.945 | 17.648 | 10.449 | 0.887 | 0.722 | 1.073 | inconclusive | inconclusive | 0.057 | 0.132 | 26.427 | -21.799 | 0.000 | -13.130 | 6.057 | 0.000 |  |
| urban_pt | household_type | single_person | 590 | 366 | False | False | 73.902 | 77.052 | 15.373 | 11.683 | 12.481 | 9.098 | 1.043 | 0.954 | 1.139 | equivalent | inconclusive | 0.078 | 0.023 | -2.843 | 4.072 | 0.000 | -15.602 | 16.993 | 0.000 |  |
| urban_pt | day_purpose | other | 519 | 410 | False | False | 70.516 | 76.577 | 17.816 | 12.211 | 15.159 | 9.567 | 1.086 | 0.948 | 1.230 | inconclusive | inconclusive | 0.114 | 0.040 | 7.782 | -9.939 | 0.000 | -12.190 | 13.107 | 0.000 |  |
| urban_pt | day_purpose | work_study | 883 | 508 | False | False | 73.708 | 75.203 | 15.101 | 15.389 | 12.293 | 12.278 | 1.020 | 0.951 | 1.095 | equivalent | equivalent | 0.055 | 0.020 | -4.147 | 5.182 | 0.000 | 5.371 | -5.828 | 0.000 |  |
| walk | density | dense | 1027 | 662 | False | False | 39.653 | 45.027 | 2.351 | 2.445 | 3.580 | 3.258 | 1.136 | 1.026 | 1.265 | inconclusive | inconclusive | 0.077 | 0.095 | 3.137 | -1.174 | 0.187 | 3.886 | 1.324 | 0.000 |  |
| walk | density | intermediate | 1918 | 1449 | False | False | 38.092 | 39.288 | 2.223 | 2.225 | 3.501 | 3.398 | 1.031 | 0.958 | 1.104 | equivalent | inconclusive | 0.024 | 0.019 | 0.951 | -0.302 | -0.060 | -0.097 | -0.431 | 0.000 |  |
| walk | density | sparse | 497 | 367 | False | False | 35.285 | 38.763 | 2.014 | 2.184 | 3.424 | 3.381 | 1.099 | 0.944 | 1.255 | inconclusive | inconclusive | 0.056 | 0.072 | -2.672 | 0.512 | -0.058 | -0.830 | -0.223 | 0.000 |  |
| walk | density | very_sparse | 782 | 378 | False | False | 34.169 | 32.354 | 1.820 | 1.856 | 3.196 | 3.442 | 0.947 | 0.845 | 1.072 | inconclusive | inconclusive | 0.122 | 0.151 | -6.248 | 2.972 | -0.057 | -6.613 | -0.849 | 0.000 |  |
| walk | population | children_6_17 | 490 | 370 | False | False | 33.084 | 31.277 | 1.932 | 1.688 | 3.504 | 3.239 | 0.945 | 0.832 | 1.075 | inconclusive | inconclusive | 0.058 | 0.118 | -4.052 | -0.310 | -0.056 | -9.857 | 1.317 | 0.000 |  |
| walk | population | employed | 1501 | 894 | False | False | 31.264 | 33.140 | 1.983 | 2.034 | 3.829 | 3.683 | 1.060 | 0.977 | 1.137 | equivalent | inconclusive | 0.094 | 0.071 | -3.039 | -3.343 | 0.143 | -3.357 | -3.319 | 0.000 |  |
| walk | population | other_inactive | 530 | 311 | False | False | 40.243 | 48.553 | 2.520 | 2.756 | 3.758 | 3.406 | 1.206 | 1.077 | 1.358 | inconclusive | inconclusive | 0.062 | 0.140 | 5.865 | -3.062 | -0.061 | 9.311 | -0.574 | 0.000 |  |
| walk | population | retired | 1457 | 1091 | False | False | 46.808 | 49.833 | 2.348 | 2.613 | 3.010 | 3.146 | 1.065 | 0.988 | 1.158 | inconclusive | inconclusive | 0.113 | 0.119 | 3.370 | 6.002 | -0.066 | 7.058 | 2.958 | 0.000 |  |
| walk | population | unemployed | 246 | 188 | False | False | 44.909 | 50.284 | 2.679 | 2.833 | 3.579 | 3.380 | 1.120 | 0.907 | 1.387 | inconclusive | inconclusive | 0.126 | 0.088 | 8.705 | -1.233 | -0.065 | 10.714 | -0.246 | 0.000 |  |
| walk | income | q1 | 949 | 692 | False | False | 42.443 | 41.938 | 2.428 | 2.301 | 3.451 | 3.293 | 0.988 | 0.893 | 1.092 | equivalent | inconclusive | 0.066 | 0.067 | 4.539 | 0.256 | 0.145 | 1.278 | 0.844 | 0.000 |  |
| walk | income | q2 | 740 | 569 | False | False | 34.766 | 42.073 | 2.048 | 2.383 | 3.535 | 3.399 | 1.210 | 1.089 | 1.348 | inconclusive | inconclusive | 0.045 | 0.052 | -2.042 | -0.638 | -0.057 | 2.710 | -0.454 | 0.000 |  |
| walk | income | q3 | 763 | 487 | False | False | 36.908 | 41.129 | 2.084 | 2.297 | 3.389 | 3.351 | 1.114 | 0.986 | 1.253 | inconclusive | inconclusive | 0.030 | 0.025 | -1.450 | 0.914 | -0.059 | 1.183 | 0.130 | 0.000 |  |
| walk | income | q4 | 736 | 517 | False | False | 35.280 | 37.071 | 2.074 | 2.113 | 3.527 | 3.419 | 1.051 | 0.938 | 1.187 | inconclusive | inconclusive | 0.055 | 0.058 | -1.602 | -0.562 | -0.058 | -2.089 | -0.657 | 0.000 |  |
| walk | income | q5 | 1036 | 591 | False | False | 35.965 | 36.175 | 2.082 | 2.037 | 3.474 | 3.379 | 1.006 | 0.912 | 1.099 | equivalent | equivalent | 0.048 | 0.054 | -1.472 | -0.008 | -0.058 | -3.444 | -0.196 | 0.000 |  |
| walk | vehicles | 0 | 1277 | 868 | False | False | 42.466 | 45.366 | 2.486 | 2.363 | 3.513 | 3.125 | 1.068 | 0.977 | 1.184 | inconclusive | inconclusive | 0.111 | 0.078 | 5.479 | -0.453 | -0.063 | 2.447 | 3.103 | 0.000 |  |
| walk | vehicles | 1 | 1778 | 1193 | False | False | 37.967 | 40.671 | 2.151 | 2.270 | 3.400 | 3.348 | 1.071 | 0.986 | 1.147 | equivalent | inconclusive | 0.016 | 0.026 | -0.280 | 0.805 | -0.060 | 0.699 | 0.156 | 0.000 |  |
| walk | vehicles | 2+ | 1169 | 786 | False | False | 32.868 | 34.128 | 1.939 | 2.067 | 3.561 | 3.634 | 1.038 | 0.943 | 1.140 | equivalent | inconclusive | 0.070 | 0.083 | -3.910 | -0.879 | 0.154 | -2.814 | -2.874 | 0.000 |  |
| walk | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | household_type | couple | 1122 | 729 | False | False | 44.246 | 44.945 | 2.369 | 2.510 | 3.213 | 3.351 | 1.016 | 0.922 | 1.131 | equivalent | inconclusive | 0.079 | 0.070 | 3.636 | 3.172 | -0.065 | 4.992 | 0.137 | 0.000 |  |
| walk | household_type | couple_with_children | 1195 | 742 | False | False | 33.115 | 33.404 | 2.002 | 1.971 | 3.642 | 3.541 | 1.009 | 0.924 | 1.097 | equivalent | equivalent | 0.056 | 0.080 | -2.806 | -1.673 | 0.091 | -4.515 | -1.897 | 0.000 |  |
| walk | household_type | other | 97 | 51 | True | True | 35.618 | 43.804 | 2.180 | 2.427 | 3.672 | 3.324 | 1.230 | 0.946 | 1.570 | inconclusive | inconclusive | 0.092 | 0.171 | 0.210 | -2.036 | -0.058 | 3.518 | 0.470 | 0.000 |  |
| walk | household_type | single_parent | 373 | 268 | False | False | 35.707 | 36.760 | 2.085 | 1.968 | 3.504 | 3.213 | 1.029 | 0.854 | 1.247 | inconclusive | inconclusive | 0.071 | 0.051 | -1.409 | -0.329 | -0.058 | -4.791 | 1.734 | 0.000 |  |
| walk | household_type | single_person | 1437 | 1066 | False | False | 40.429 | 48.206 | 2.335 | 2.572 | 3.465 | 3.201 | 1.192 | 1.112 | 1.299 | inconclusive | different | 0.070 | 0.111 | 2.895 | 0.093 | -0.062 | 6.250 | 2.140 | 0.000 |  |
| walk | day_purpose | other | 2671 | 1909 | False | False | 42.220 | 47.597 | 2.326 | 2.601 | 3.306 | 3.279 | 1.127 | 1.070 | 1.208 | inconclusive | inconclusive | 0.057 | 0.095 | 2.818 | 1.963 | -0.063 | 6.701 | 1.080 | 0.000 |  |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | day_purpose | work_study | 1553 | 946 | False | False | 31.275 | 29.882 | 1.958 | 1.757 | 3.772 | 3.528 | 0.955 | 0.884 | 1.031 | equivalent | inconclusive | 0.075 | 0.121 | -3.492 | -2.833 | 0.097 | -8.264 | -1.671 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Mode-user composition

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 493 | 291 | 1.192 | 1.240 | 0.006 | 0.001 | 2008 target rescaled to common support |
| car_driver | 8409 | 5585 | 1.090 | 1.098 | 0.000 | 0.000 |  |
| car_passenger | 2053 | 1633 | 1.121 | 1.102 | 0.000 | 0.000 |  |
| other | 622 | 327 | 1.083 | - | 0.013 | 0.000 | insufficient common support for 2008 target |
| train | 563 | 240 | 1.085 | 1.078 | 0.010 | 0.006 | 2008 target rescaled to common support |
| urban_pt | 1402 | 916 | 1.041 | 1.047 | 0.000 | 0.000 |  |
| walk | 4224 | 2854 | 1.062 | 1.058 | 0.000 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Per-mode decomposition

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | 8.183 | 2.778 | 5.411 | -0.005 | 0.000 |  |
| bike | rounded_crow_fly | 8.183 | 2.778 | 10.551 | -5.146 | 0.000 |  |
| car_driver | published | 5.539 | -3.432 | 6.511 | 2.489 | -0.029 |  |
| car_driver | rounded_crow_fly | 5.539 | -3.432 | 6.575 | 2.396 | 0.000 |  |
| car_passenger | published | 4.968 | -1.562 | 3.040 | 3.490 | -0.000 |  |
| car_passenger | rounded_crow_fly | 4.968 | -1.562 | 3.856 | 2.675 | -0.000 |  |
| other | published | 4.896 | -5.114 | 16.386 | -6.631 | 0.255 |  |
| other | rounded_crow_fly | 4.896 | -5.114 | 17.235 | -7.225 | -0.000 |  |
| train | published | 9.943 | -4.929 | 24.614 | -8.761 | -0.982 |  |
| train | rounded_crow_fly | 9.943 | -4.929 | 18.183 | -3.311 | 0.000 |  |
| urban_pt | published | 2.987 | -2.484 | -5.595 | 11.066 | 0.000 |  |
| urban_pt | rounded_crow_fly | 2.987 | -2.484 | -1.383 | 6.854 | -0.000 |  |
| walk | published | 2.314 | -0.503 | 5.186 | -2.355 | -0.015 |  |
| walk | rounded_crow_fly | 2.314 | -0.503 | -2.993 | 5.810 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Duration-rounding bounds

Scope: Round-trip days · all purposes · local (≤ 80 km) (`round-allpurp-local`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | 0.176 | 1.717 | 0.000 |  |
| car_driver | -0.045 | 3.008 | 0.000 |  |
| car_passenger | -0.038 | 1.476 | 0.000 |  |
| other | -0.241 | 2.231 | 0.000 |  |
| train | -0.258 | 2.053 | 0.000 |  |
| urban_pt | -0.044 | 0.941 | 0.000 |  |
| walk | -0.003 | 1.407 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


## Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km)

### Subgroup mode-user days

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 84 | 60 | True | True | 42.071 | 49.702 | 7.847 | 8.504 | 11.191 | 10.265 | - | - | - |  |  | 0.064 | 0.142 | 3.548 | -4.355 | 0.000 | -2.265 | 0.956 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | intermediate | 180 | 130 | False | False | 41.936 | 46.922 | 7.212 | 9.542 | 10.319 | 12.201 | - | - | - |  |  | 0.082 | 0.078 | -0.036 | -0.906 | 0.000 | 3.435 | -7.524 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | sparse | 87 | 52 | True | True | 44.951 | 43.716 | 7.406 | 6.790 | 9.886 | 9.319 | - | - | - |  |  | 0.104 | 0.154 | 1.129 | 0.944 | 0.000 | -12.766 | 5.471 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | very_sparse | 146 | 50 | False | True | 43.433 | 77.669 | 6.351 | 10.595 | 8.773 | 8.185 | - | - | - |  |  | 0.171 | 0.199 | -5.524 | 6.080 | 0.000 | 11.091 | 15.567 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | children_6_17 | 93 | 37 | True | True | 28.853 | - | 4.650 | - | 9.669 | - | - | - | - |  |  | 0.216 | - | -15.570 | 1.546 | 0.000 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | employed | 200 | 136 | False | False | 50.717 | 47.469 | 8.660 | 9.540 | 10.246 | 12.058 | - | - | - |  |  | 0.123 | 0.072 | 8.504 | -0.665 | 0.000 | 3.447 | -6.989 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | other_inactive | 38 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | retired | 147 | 82 | False | True | 54.928 | 49.292 | 8.695 | 8.906 | 9.498 | 10.840 | - | - | - |  |  | 0.119 | 0.039 | 9.056 | 2.994 | 0.000 | 0.062 | -1.780 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | unemployed | 19 | 20 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q1 | 94 | 51 | True | True | 47.973 | 57.780 | 8.183 | 8.144 | 10.235 | 8.457 | - | - | - |  |  | 0.166 | 0.089 | 5.694 | -0.599 | 0.000 | -4.791 | 11.560 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q2 | 90 | 55 | True | True | 41.162 | 56.287 | 6.399 | 8.498 | 9.328 | 9.058 | - | - | - |  |  | 0.066 | 0.122 | -5.058 | 3.342 | 0.000 | -2.449 | 7.726 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q3 | 96 | 58 | True | True | 40.562 | 52.842 | 6.641 | 10.115 | 9.824 | 11.486 | - | - | - |  |  | 0.095 | 0.115 | -3.474 | 1.158 | 0.000 | 6.676 | -4.845 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q4 | 93 | 53 | True | True | 39.341 | 37.875 | 7.662 | 7.790 | 11.685 | 12.341 | - | - | - |  |  | 0.124 | 0.147 | 2.449 | -5.986 | 0.000 | -5.851 | -7.285 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q5 | 124 | 75 | False | True | 45.667 | 52.359 | 7.204 | 10.085 | 9.466 | 11.557 | - | - | - |  |  | 0.062 | 0.116 | -0.085 | 2.874 | 0.000 | 6.490 | -5.142 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 0 | 105 | 61 | False | True | 40.216 | 53.695 | 7.313 | 8.485 | 10.911 | 9.481 | - | - | - |  |  | 0.085 | 0.122 | 0.543 | -3.205 | 0.000 | -2.470 | 5.154 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 1 | 183 | 112 | False | False | 48.395 | 50.185 | 8.275 | 9.840 | 10.260 | 11.765 | - | - | - |  |  | 0.122 | 0.071 | 6.231 | -0.714 | 0.000 | 5.112 | -5.938 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 2+ | 209 | 116 | False | False | 39.861 | 50.565 | 6.382 | 8.358 | 9.606 | 9.918 | - | - | - |  |  | 0.106 | 0.101 | -5.090 | 2.074 | 0.000 | -3.159 | 2.712 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple | 154 | 89 | False | True | 51.052 | 44.515 | 8.092 | 8.390 | 9.511 | 11.309 | - | - | - |  |  | 0.106 | 0.050 | 5.356 | 2.818 | 0.000 | -2.784 | -3.712 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple_with_children | 169 | 85 | False | True | 39.211 | 51.202 | 6.741 | 8.807 | 10.316 | 10.321 | - | - | - |  |  | 0.074 | 0.067 | -2.802 | -0.864 | 0.000 | -0.505 | 0.697 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | other | 12 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_parent | 36 | 30 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_person | 126 | 82 | False | True | 48.165 | 53.973 | 8.728 | 9.828 | 10.873 | 10.926 | - | - | - |  |  | 0.257 | 0.116 | 8.638 | -3.351 | 0.000 | 5.237 | -2.275 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | other | 280 | 156 | False | False | 43.984 | 58.552 | 6.937 | 9.415 | 9.463 | 9.647 | - | - | - |  |  | 0.040 | 0.070 | -1.725 | 2.831 | 0.000 | 3.106 | 4.435 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | work_study | 217 | 136 | False | False | 41.331 | 42.833 | 7.611 | 8.331 | 11.049 | 11.670 | - | - | - |  |  | 0.057 | 0.076 | 2.232 | -3.778 | 0.000 | -3.064 | -5.114 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | dense | 649 | 436 | False | False | 64.124 | 78.939 | 31.482 | 42.473 | 29.457 | 32.283 | - | - | - |  |  | 0.051 | 0.063 | -16.545 | 16.193 | -0.100 | -1.826 | 9.847 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | intermediate | 3180 | 2430 | False | False | 65.127 | 69.458 | 36.480 | 36.804 | 33.612 | 31.793 | - | - | - |  |  | 0.013 | 0.016 | -7.117 | 7.762 | -0.094 | -11.766 | 10.305 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | sparse | 1236 | 1021 | False | False | 63.218 | 66.655 | 42.555 | 44.778 | 40.405 | 40.308 | - | - | - |  |  | 0.057 | 0.042 | 2.829 | -4.114 | -0.073 | 1.958 | -6.221 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | very_sparse | 3442 | 1750 | False | False | 64.805 | 74.077 | 48.092 | 53.678 | 44.737 | 43.478 | - | - | - |  |  | 0.021 | 0.031 | 10.777 | -10.755 | 0.206 | 15.205 | -12.046 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | children_6_17 | 78 | 43 | True | True | 44.658 | - | 25.715 | - | 34.549 | - | - | - | - |  |  | 0.212 | - | -24.813 | 4.978 | -0.084 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | employed | 5314 | 3094 | False | False | 70.008 | 78.017 | 45.785 | 49.957 | 39.323 | 38.420 | - | - | - |  |  | 0.054 | 0.081 | 7.898 | -2.506 | 0.039 | 10.262 | -3.163 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | other_inactive | 610 | 292 | False | False | 55.459 | 62.347 | 31.029 | 35.733 | 33.569 | 34.387 | - | - | - |  |  | 0.103 | 0.105 | -16.269 | 7.245 | -0.093 | -13.121 | 4.550 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | retired | 2180 | 1940 | False | False | 53.472 | 55.825 | 30.322 | 30.191 | 34.029 | 32.448 | - | - | - |  |  | 0.117 | 0.169 | -17.340 | 6.318 | -0.083 | -23.067 | 7.973 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | unemployed | 325 | 264 | False | False | 58.729 | 65.031 | 35.727 | 34.466 | 36.500 | 31.799 | - | - | - |  |  | 0.065 | 0.076 | -8.046 | 2.294 | -0.096 | -15.848 | 9.961 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q1 | 995 | 633 | False | False | 54.476 | 63.818 | 32.286 | 35.444 | 35.565 | 33.323 | - | - | - |  |  | 0.111 | 0.080 | -13.770 | 3.753 | -0.084 | -13.818 | 6.718 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q2 | 1341 | 1048 | False | False | 59.917 | 62.117 | 37.511 | 37.147 | 37.629 | 35.881 | - | - | - |  |  | 0.049 | 0.065 | -5.095 | 0.422 | 0.012 | -10.519 | 1.717 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q3 | 1757 | 1190 | False | False | 62.563 | 72.666 | 38.662 | 48.149 | 37.078 | 39.756 | - | - | - |  |  | 0.027 | 0.028 | -3.284 | 1.369 | -0.099 | 7.253 | -5.506 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q4 | 1889 | 1345 | False | False | 66.455 | 71.909 | 43.507 | 43.288 | 39.411 | 36.119 | - | - | - |  |  | 0.041 | 0.033 | 4.350 | -2.587 | 0.114 | -0.383 | 1.374 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q5 | 2525 | 1421 | False | False | 73.529 | 78.803 | 46.863 | 48.592 | 38.306 | 36.997 | - | - | - |  |  | 0.092 | 0.075 | 9.703 | -0.762 | 0.011 | 8.242 | -0.358 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 0 | 59 | 60 | True | True | 72.048 | 72.578 | 46.235 | 38.470 | 38.504 | 31.804 | - | - | - |  |  | 0.175 | 0.176 | 8.682 | -1.105 | -0.106 | -8.851 | 10.510 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 1 | 3339 | 2517 | False | False | 62.126 | 67.028 | 36.209 | 36.787 | 34.975 | 32.930 | - | - | - |  |  | 0.054 | 0.043 | -7.425 | 5.062 | -0.089 | -11.592 | 7.702 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 2+ | 5109 | 3051 | False | False | 66.005 | 73.366 | 43.435 | 47.856 | 39.578 | 39.137 | - | - | - |  |  | 0.035 | 0.029 | 4.227 | -2.854 | 0.055 | 6.849 | -4.401 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple | 2939 | 1976 | False | False | 60.927 | 64.228 | 37.297 | 39.273 | 36.736 | 36.688 | - | - | - |  |  | 0.054 | 0.080 | -5.496 | 1.933 | -0.086 | -6.935 | 0.244 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple_with_children | 3194 | 1604 | False | False | 68.961 | 78.337 | 44.854 | 50.195 | 39.090 | 38.446 | - | - | - |  |  | 0.048 | 0.073 | 6.467 | -2.090 | 0.007 | 10.638 | -3.219 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | other | 170 | 89 | False | True | 58.794 | 64.789 | 35.198 | 36.173 | 36.447 | 33.499 | - | - | - |  |  | 0.095 | 0.119 | -8.970 | 2.385 | 0.802 | -12.541 | 6.411 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_parent | 528 | 343 | False | False | 57.040 | 68.198 | 32.353 | 38.392 | 34.146 | 33.777 | - | - | - |  |  | 0.069 | 0.033 | -13.956 | 6.310 | 0.108 | -8.721 | 6.001 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_person | 1676 | 1625 | False | False | 60.988 | 65.255 | 37.876 | 36.888 | 37.277 | 33.917 | - | - | - |  |  | 0.051 | 0.064 | -4.531 | 1.016 | -0.074 | -11.253 | 5.589 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | other | 4059 | 3073 | False | False | 55.555 | 59.304 | 32.926 | 34.053 | 35.616 | 34.453 | - | - | - |  |  | 0.103 | 0.129 | -12.724 | 3.703 | -0.000 | -15.931 | 4.316 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | work_study | 4448 | 2564 | False | False | 71.692 | 80.617 | 46.851 | 51.428 | 39.272 | 38.275 | - | - | - |  |  | 0.081 | 0.108 | 9.561 | -2.447 | 0.000 | 12.630 | -2.931 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | dense | 199 | 165 | False | False | 42.893 | 50.956 | 22.555 | 22.956 | 31.550 | 27.030 | - | - | - |  |  | 0.067 | 0.111 | -6.433 | 6.644 | -0.212 | -8.613 | 11.870 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | intermediate | 817 | 782 | False | False | 41.322 | 46.285 | 21.960 | 23.435 | 32.160 | 30.379 | - | - | - |  |  | 0.031 | 0.037 | -7.440 | 5.715 | 0.152 | -7.237 | 5.823 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | sparse | 294 | 295 | False | False | 43.142 | 46.702 | 28.681 | 30.154 | 40.107 | 38.740 | - | - | - |  |  | 0.063 | 0.055 | 3.884 | -3.660 | 0.023 | 4.630 | -5.626 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | very_sparse | 790 | 419 | False | False | 45.228 | 50.185 | 32.451 | 34.711 | 43.090 | 41.500 | - | - | - |  |  | 0.071 | 0.066 | 9.419 | -6.908 | -0.178 | 11.686 | -9.200 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | children_6_17 | 618 | 446 | False | False | 32.428 | 36.336 | 17.363 | 17.758 | 32.151 | 29.322 | - | - | - |  |  | 0.127 | 0.128 | -15.402 | 5.090 | -0.155 | -18.016 | 6.654 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | employed | 600 | 330 | False | False | 48.019 | 55.511 | 30.525 | 35.886 | 38.262 | 38.789 | - | - | - |  |  | 0.078 | 0.095 | 6.929 | -1.725 | -0.080 | 14.016 | -6.204 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | other_inactive | 245 | 182 | False | False | 50.012 | 51.467 | 26.964 | 26.260 | 32.349 | 30.614 | - | - | - |  |  | 0.138 | 0.072 | 1.325 | 6.021 | -0.230 | -1.991 | 5.760 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | retired | 551 | 626 | False | False | 57.130 | 60.848 | 41.231 | 38.238 | 43.949 | 37.706 | - | - | - |  |  | 0.153 | 0.169 | 22.515 | -8.770 | 0.490 | 18.125 | -4.976 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | unemployed | 85 | 75 | True | True | 51.374 | 52.816 | 32.915 | 35.040 | 38.900 | 39.807 | - | - | - |  |  | 0.202 | 0.110 | 10.718 | -2.563 | 0.324 | 12.466 | -7.349 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q1 | 372 | 315 | False | False | 41.506 | 46.234 | 24.240 | 22.806 | 35.041 | 29.596 | - | - | - |  |  | 0.054 | 0.044 | -3.289 | 2.108 | -0.209 | -8.511 | 7.047 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q2 | 422 | 380 | False | False | 37.675 | 48.259 | 22.562 | 29.258 | 35.932 | 36.376 | - | - | - |  |  | 0.095 | 0.043 | -6.021 | 1.000 | -0.199 | 3.259 | -2.698 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q3 | 431 | 339 | False | False | 48.756 | 48.675 | 31.166 | 29.768 | 38.396 | 36.694 | - | - | - |  |  | 0.102 | 0.048 | 7.935 | -1.898 | -0.175 | 4.105 | -3.129 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q4 | 401 | 335 | False | False | 40.575 | 46.284 | 24.946 | 25.482 | 37.019 | 33.034 | - | - | - |  |  | 0.042 | 0.027 | -2.053 | -0.207 | -0.060 | -3.301 | 1.887 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q5 | 474 | 292 | False | False | 47.219 | 49.193 | 28.701 | 29.411 | 37.280 | 35.872 | - | - | - |  |  | 0.063 | 0.049 | 4.097 | -0.539 | 0.766 | 3.542 | -2.048 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 0 | 263 | 250 | False | False | 42.742 | 46.227 | 23.808 | 22.685 | 33.421 | 29.443 | - | - | - |  |  | 0.070 | 0.076 | -4.106 | 4.165 | -0.212 | -8.760 | 7.288 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 1 | 756 | 634 | False | False | 43.931 | 49.297 | 25.846 | 27.721 | 35.340 | 33.740 | - | - | - |  |  | 0.057 | 0.026 | -0.598 | 1.800 | -0.166 | 0.677 | 0.921 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 2+ | 1081 | 774 | False | False | 42.242 | 46.746 | 26.821 | 27.716 | 38.416 | 35.575 | - | - | - |  |  | 0.039 | 0.020 | 0.989 | -1.788 | 0.146 | 0.651 | -1.603 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple | 626 | 568 | False | False | 56.797 | 60.533 | 38.808 | 38.677 | 41.561 | 38.337 | - | - | - |  |  | 0.159 | 0.167 | 19.447 | -5.976 | 0.431 | 18.690 | -5.856 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple_with_children | 906 | 566 | False | False | 37.848 | 42.369 | 21.562 | 23.250 | 34.218 | 32.925 | - | - | - |  |  | 0.056 | 0.070 | -7.863 | 2.972 | -0.156 | -7.284 | 1.954 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | other | 66 | 37 | True | True | 44.919 | - | 32.103 | - | 42.882 | - | - | - | - |  |  | 0.078 | - | 8.913 | -6.672 | -0.217 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_parent | 166 | 150 | False | False | 45.195 | 41.634 | 27.118 | 20.588 | 36.002 | 29.670 | - | - | - |  |  | 0.040 | 0.058 | 1.509 | 1.009 | -0.218 | -12.644 | 6.580 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_person | 336 | 340 | False | False | 39.557 | 51.535 | 22.780 | 29.012 | 34.862 | 33.778 | - | - | - |  |  | 0.079 | 0.063 | -5.771 | 2.269 | 0.164 | 2.950 | 0.886 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | other | 1154 | 1106 | False | False | 51.562 | 57.506 | 33.928 | 35.799 | 39.767 | 37.351 | - | - | - |  |  | 0.114 | 0.113 | 12.165 | -3.606 | 0.108 | 14.145 | -4.337 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | work_study | 946 | 555 | False | False | 35.427 | 36.793 | 19.550 | 17.927 | 33.179 | 29.235 | - | - | - |  |  | 0.098 | 0.126 | -11.438 | 4.082 | -0.112 | -17.724 | 6.818 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | dense+intermediate | 264 | 176 | False | False | 60.904 | 62.473 | 25.628 | 28.724 | 26.592 | 27.587 | - | - | - |  |  | 0.034 | 0.062 | -2.922 | 1.474 | 1.474 | -22.734 | 15.853 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | sparse+very_sparse | 368 | 160 | False | False | 60.858 | 76.424 | 27.832 | 52.735 | 27.712 | 41.402 | - | - | - |  |  | 0.025 | 0.064 | 2.101 | -1.039 | -1.082 | 19.106 | -12.036 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | children_6_17 | 266 | 87 | False | True | 57.767 | 60.970 | 21.881 | 33.503 | 22.727 | 32.970 | - | - | - |  |  | 0.057 | 0.096 | -12.220 | 10.751 | -1.641 | -12.449 | 4.065 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | employed | 255 | 151 | False | False | 69.161 | 78.243 | 36.785 | 47.597 | 34.301 | 36.500 | - | - | - |  |  | 0.122 | 0.071 | 20.351 | -14.958 | 2.890 | 11.781 | -2.892 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | other_inactive | 36 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | retired | 64 | 63 | True | True | 51.734 | 62.279 | 23.396 | 36.116 | 27.617 | 34.794 | - | - | - |  |  | 0.205 | 0.133 | -7.815 | -0.766 | -0.563 | -7.642 | 0.567 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | unemployed | 11 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q1 | 109 | 62 | False | True | 58.529 | 73.229 | 26.275 | 42.455 | 26.935 | 34.786 | - | - | - |  |  | 0.045 | 0.162 | -1.377 | 0.680 | -1.652 | 3.243 | 0.632 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q2 | 150 | 73 | False | True | 65.300 | 52.627 | 25.425 | 22.755 | 23.646 | 25.944 | - | - | - |  |  | 0.089 | 0.128 | -3.526 | 8.931 | -0.983 | -35.040 | 18.312 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q3 | 104 | 69 | False | True | 59.075 | 82.474 | 23.595 | 59.569 | 24.148 | 43.337 | - | - | - |  |  | 0.091 | 0.138 | -7.833 | 7.233 | -1.203 | 29.092 | -15.972 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q4 | 124 | 56 | False | True | 52.953 | 59.482 | 28.794 | 34.533 | 32.797 | 34.834 | - | - | - |  |  | 0.133 | 0.188 | 3.893 | -10.542 | -1.276 | -10.353 | 0.482 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q5 | 145 | 76 | False | True | 68.822 | 74.545 | 31.420 | 39.386 | 31.120 | 31.701 | - | - | - |  |  | 0.064 | 0.058 | 10.089 | -8.616 | 6.472 | -2.125 | 7.316 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 0 | 89 | 63 | True | True | 52.981 | 60.551 | 18.736 | 31.487 | 21.218 | 31.200 | - | - | - |  |  | 0.139 | 0.102 | -20.530 | 14.207 | -1.573 | -16.433 | 7.630 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 1 | 205 | 118 | False | False | 61.425 | 63.847 | 28.812 | 30.390 | 28.724 | 28.559 | - | - | - |  |  | 0.044 | 0.050 | 4.228 | -3.235 | -0.445 | -19.226 | 13.719 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 2+ | 338 | 155 | False | False | 61.980 | 75.433 | 27.238 | 50.261 | 27.340 | 39.978 | - | - | - |  |  | 0.028 | 0.037 | 0.795 | -0.217 | 0.525 | 15.503 | -9.424 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple | 84 | 87 | True | True | 54.756 | 67.541 | 26.791 | 35.031 | 31.478 | 31.120 | - | - | - |  |  | 0.202 | 0.052 | -0.208 | -8.344 | 2.431 | -10.041 | 8.229 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple_with_children | 362 | 129 | False | False | 65.288 | 69.400 | 29.415 | 42.576 | 27.815 | 36.809 | - | - | - |  |  | 0.067 | 0.037 | 5.664 | -1.310 | 0.056 | 3.353 | -3.307 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | other | 21 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_parent | 60 | 36 | True | True | 55.850 | - | 19.962 | - | 21.523 | - | - | - | - |  |  | 0.129 | - | -17.371 | 13.747 | -1.404 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_person | 105 | 78 | False | True | 51.921 | 82.925 | 21.865 | 62.665 | 25.267 | 45.341 | - | - | - |  |  | 0.220 | 0.121 | -11.638 | 4.239 | -1.557 | 33.021 | -19.450 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | other | 117 | 112 | False | False | 48.013 | 69.366 | 23.379 | 58.479 | 29.420 | 50.583 | - | - | - |  |  | 0.167 | 0.118 | -7.576 | -4.165 | -1.124 | 25.366 | -25.354 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | work_study | 515 | 224 | False | False | 63.331 | 69.350 | 27.557 | 35.589 | 26.921 | 30.790 | - | - | - |  |  | 0.032 | 0.033 | 1.526 | 0.739 | 0.188 | -9.079 | 9.076 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | density | dense+intermediate+sparse+very_sparse | 594 | 258 | False | False | 133.001 | 134.677 | 67.166 | 65.343 | 34.204 | 29.111 | - | - | - |  |  | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | children_6_17 | 28 | 18 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | employed | 450 | 179 | False | False | 140.857 | 135.908 | 68.728 | 68.159 | 33.371 | 30.091 | - | - | - |  |  | 0.052 | 0.032 | 3.147 | 3.378 | 1.331 | 5.708 | -4.478 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | other_inactive | 49 | 27 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | retired | 49 | 26 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | unemployed | 18 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q1+q2+q3+q4 | 327 | 165 | False | False | 134.336 | 136.409 | 68.424 | 62.296 | 35.635 | 27.401 | - | - | - |  |  | 0.021 | 0.043 | 2.482 | -5.477 | 4.330 | -6.474 | 8.206 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q5 | 267 | 93 | False | True | 130.685 | 130.810 | 64.983 | 72.147 | 31.868 | 33.093 | - | - | - |  |  | 0.037 | 0.097 | -4.356 | 9.327 | -7.287 | 13.148 | -17.015 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 0 | 180 | 80 | False | True | 112.602 | 143.072 | 31.922 | 56.392 | 17.641 | 23.649 | - | - | - |  |  | 0.147 | 0.130 | -91.137 | 81.125 | -10.387 | -20.455 | 28.850 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 1 | 259 | 102 | False | False | 135.545 | 131.147 | 77.722 | 68.087 | 39.399 | 31.150 | - | - | - |  |  | 0.064 | 0.075 | 19.601 | -18.983 | 1.927 | 5.466 | -8.996 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 2+ | 155 | 73 | False | True | 143.987 | 124.754 | 75.634 | 64.952 | 36.645 | 31.238 | - | - | - |  |  | 0.053 | 0.083 | 16.436 | -9.539 | 4.089 | -0.780 | -9.143 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple | 130 | 48 | False | True | 140.790 | - | 67.241 | - | 30.864 | - | - | - | - |  |  | 0.081 | - | 0.153 | 14.065 | -6.428 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple_with_children | 211 | 86 | False | True | 131.157 | 116.042 | 68.593 | 50.672 | 38.032 | 26.200 | - | - | - |  |  | 0.052 | 0.086 | 2.777 | -14.010 | 9.390 | -31.818 | 13.183 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | other | 18 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_parent | 60 | 33 | True | True | 135.467 | - | 73.951 | - | 32.754 | - | - | - | - |  |  | 0.130 | - | 12.918 | 5.818 | -16.269 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_person | 175 | 83 | False | True | 128.283 | 149.940 | 63.998 | 87.735 | 32.344 | 35.108 | - | - | - |  |  | 0.063 | 0.106 | -6.310 | 7.307 | -5.715 | 41.893 | -26.630 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | other | 106 | 56 | False | True | 116.103 | 156.836 | 51.729 | 85.952 | 27.737 | 32.882 | - | - | - |  |  | 0.150 | 0.202 | -32.477 | 26.066 | -10.486 | 39.880 | -17.720 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | work_study | 488 | 202 | False | False | 135.877 | 130.507 | 69.794 | 61.465 | 35.241 | 28.258 | - | - | - |  |  | 0.026 | 0.038 | 5.160 | -4.015 | 1.732 | -8.113 | 3.942 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | dense | 681 | 364 | False | False | 72.204 | 74.194 | 13.995 | 10.479 | 11.630 | 8.474 | - | - | - |  |  | 0.033 | 0.046 | -22.000 | 19.618 | 0.000 | -26.167 | 24.298 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | intermediate | 638 | 474 | False | False | 75.798 | 79.597 | 19.239 | 16.351 | 15.229 | 12.325 | - | - | - |  |  | 0.026 | 0.051 | 1.387 | -0.175 | 0.000 | 7.517 | -3.982 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | sparse+very_sparse | 96 | 85 | True | True | 78.501 | 67.265 | 38.896 | 22.369 | 29.729 | 19.953 | - | - | - |  |  | 0.138 | 0.129 | 55.283 | -51.367 | 0.000 | 29.347 | -38.144 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | children_6_17 | 141 | 175 | False | False | 67.097 | 69.771 | 22.780 | 16.442 | 20.370 | 14.139 | - | - | - |  |  | 0.154 | 0.112 | 13.261 | -20.749 | 0.000 | 7.445 | -13.735 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | employed | 712 | 345 | False | False | 75.162 | 76.647 | 15.812 | 15.027 | 12.623 | 11.763 | - | - | - |  |  | 0.051 | 0.053 | -13.307 | 13.883 | 0.000 | 0.929 | -0.344 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | other_inactive | 223 | 142 | False | False | 77.897 | 81.663 | 18.558 | 13.529 | 14.294 | 9.940 | - | - | - |  |  | 0.115 | 0.106 | -1.341 | 4.652 | 0.000 | -7.316 | 12.917 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | retired | 266 | 180 | False | False | 77.887 | 76.804 | 26.060 | 12.821 | 20.075 | 10.016 | - | - | - |  |  | 0.074 | 0.059 | 24.537 | -21.236 | 0.000 | -11.201 | 11.943 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | unemployed | 73 | 79 | True | True | 81.464 | 83.220 | 15.017 | 14.058 | 11.061 | 10.135 | - | - | - |  |  | 0.099 | 0.105 | -17.879 | 24.757 | 0.000 | -4.336 | 11.494 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q1 | 295 | 288 | False | False | 82.010 | 79.392 | 24.087 | 13.287 | 17.623 | 10.042 | - | - | - |  |  | 0.082 | 0.041 | 19.026 | -11.602 | 0.000 | -8.616 | 11.946 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q2 | 235 | 162 | False | False | 75.300 | 82.621 | 17.908 | 17.305 | 14.269 | 12.567 | - | - | - |  |  | 0.069 | 0.098 | -3.993 | 4.707 | 0.000 | 12.158 | -5.599 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q3 | 235 | 151 | False | False | 78.463 | 77.188 | 16.253 | 16.964 | 12.429 | 13.186 | - | - | - |  |  | 0.095 | 0.043 | -11.492 | 15.370 | 0.000 | 10.223 | -9.097 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q4 | 256 | 132 | False | False | 67.366 | 66.376 | 19.840 | 13.702 | 17.670 | 12.386 | - | - | - |  |  | 0.102 | 0.101 | 3.487 | -10.707 | 0.000 | -5.699 | -3.987 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q5 | 394 | 190 | False | False | 67.535 | 71.543 | 13.676 | 14.116 | 12.150 | 11.839 | - | - | - |  |  | 0.075 | 0.051 | -22.922 | 15.871 | 0.000 | -3.713 | -0.806 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 0 | 712 | 467 | False | False | 80.266 | 80.119 | 18.041 | 12.253 | 13.486 | 9.176 | - | - | - |  |  | 0.089 | 0.061 | -3.548 | 9.229 | 0.000 | -14.984 | 19.041 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 1 | 462 | 284 | False | False | 72.353 | 69.464 | 18.541 | 13.942 | 15.376 | 12.042 | - | - | - |  |  | 0.048 | 0.078 | -1.359 | -0.873 | 0.000 | -4.565 | -2.033 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 2+ | 241 | 167 | False | False | 68.008 | 78.058 | 20.957 | 20.241 | 18.490 | 15.558 | - | - | - |  |  | 0.120 | 0.068 | 7.409 | -13.986 | 0.000 | 23.891 | -21.894 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple | 264 | 125 | False | False | 73.400 | 71.704 | 17.994 | 13.420 | 14.709 | 11.229 | - | - | - |  |  | 0.036 | 0.091 | -3.587 | 2.401 | 0.000 | -7.456 | 3.099 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple_with_children | 371 | 262 | False | False | 73.804 | 76.562 | 18.750 | 17.892 | 15.243 | 14.022 | - | - | - |  |  | 0.042 | 0.030 | -0.541 | -0.241 | 0.000 | 14.249 | -13.749 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | other | 33 | 37 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_parent | 154 | 130 | False | False | 77.024 | 68.587 | 22.629 | 11.945 | 17.628 | 10.449 | - | - | - |  |  | 0.054 | 0.133 | 13.700 | -11.262 | 0.000 | -15.708 | 8.233 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_person | 593 | 369 | False | False | 75.964 | 77.788 | 18.654 | 12.582 | 14.734 | 9.705 | - | - | - |  |  | 0.083 | 0.023 | -0.935 | 2.314 | 0.000 | -12.721 | 14.447 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | other | 525 | 412 | False | False | 73.748 | 77.298 | 22.115 | 12.824 | 17.992 | 9.955 | - | - | - |  |  | 0.113 | 0.036 | 11.699 | -12.537 | 0.000 | -11.218 | 12.454 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | work_study | 890 | 511 | False | False | 74.988 | 75.453 | 17.340 | 15.840 | 13.874 | 12.596 | - | - | - |  |  | 0.054 | 0.018 | -6.395 | 6.797 | 0.000 | 4.916 | -5.525 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | dense | 1032 | 662 | False | False | 39.659 | 45.080 | 2.351 | 2.449 | 3.580 | 3.260 | - | - | - |  |  | 0.076 | 0.096 | 3.101 | -1.179 | 0.187 | 3.879 | 1.295 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | intermediate | 1920 | 1455 | False | False | 38.177 | 39.484 | 2.226 | 2.236 | 3.499 | 3.398 | - | - | - |  |  | 0.025 | 0.019 | 0.980 | -0.294 | -0.060 | 0.014 | -0.437 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | sparse | 498 | 368 | False | False | 35.315 | 38.711 | 2.015 | 2.177 | 3.424 | 3.374 | - | - | - |  |  | 0.057 | 0.070 | -2.688 | 0.510 | -0.057 | -1.038 | -0.157 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | very_sparse | 787 | 380 | False | False | 34.203 | 32.296 | 1.824 | 1.851 | 3.199 | 3.439 | - | - | - |  |  | 0.120 | 0.150 | -6.223 | 2.932 | -0.057 | -6.780 | -0.830 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | children_6_17 | 490 | 372 | False | False | 33.084 | 31.265 | 1.932 | 1.685 | 3.504 | 3.233 | - | - | - |  |  | 0.059 | 0.119 | -4.093 | -0.318 | -0.056 | -10.015 | 1.373 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | employed | 1510 | 899 | False | False | 31.280 | 33.349 | 1.984 | 2.046 | 3.827 | 3.680 | - | - | - |  |  | 0.095 | 0.071 | -3.070 | -3.343 | 0.143 | -3.241 | -3.316 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | other_inactive | 531 | 311 | False | False | 40.216 | 48.553 | 2.519 | 2.756 | 3.758 | 3.406 | - | - | - |  |  | 0.061 | 0.140 | 5.803 | -3.076 | -0.061 | 9.229 | -0.582 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | retired | 1459 | 1092 | False | False | 46.987 | 49.987 | 2.357 | 2.622 | 3.010 | 3.148 | - | - | - |  |  | 0.116 | 0.120 | 3.489 | 6.014 | -0.066 | 7.147 | 2.934 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | unemployed | 247 | 189 | False | False | 44.982 | 50.117 | 2.682 | 2.825 | 3.577 | 3.382 | - | - | - |  |  | 0.125 | 0.086 | 8.723 | -1.227 | -0.065 | 10.487 | -0.277 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q1 | 950 | 693 | False | False | 42.429 | 42.061 | 2.428 | 2.308 | 3.451 | 3.292 | - | - | - |  |  | 0.066 | 0.067 | 4.490 | 0.244 | 0.145 | 1.309 | 0.845 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q2 | 741 | 571 | False | False | 34.778 | 42.009 | 2.048 | 2.380 | 3.534 | 3.400 | - | - | - |  |  | 0.045 | 0.052 | -2.077 | -0.638 | -0.057 | 2.572 | -0.470 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q3 | 765 | 488 | False | False | 36.917 | 41.434 | 2.085 | 2.313 | 3.388 | 3.349 | - | - | - |  |  | 0.030 | 0.026 | -1.486 | 0.911 | -0.059 | 1.380 | 0.147 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q4 | 740 | 518 | False | False | 35.358 | 37.036 | 2.079 | 2.107 | 3.528 | 3.414 | - | - | - |  |  | 0.055 | 0.059 | -1.557 | -0.579 | -0.057 | -2.271 | -0.600 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q5 | 1041 | 595 | False | False | 36.161 | 36.329 | 2.091 | 2.048 | 3.469 | 3.383 | - | - | - |  |  | 0.046 | 0.055 | -1.364 | 0.033 | -0.058 | -3.333 | -0.245 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 0 | 1277 | 868 | False | False | 42.466 | 45.366 | 2.486 | 2.363 | 3.513 | 3.125 | - | - | - |  |  | 0.110 | 0.078 | 5.440 | -0.462 | -0.063 | 2.361 | 3.099 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 1 | 1786 | 1199 | False | False | 37.977 | 40.801 | 2.152 | 2.275 | 3.400 | 3.346 | - | - | - |  |  | 0.016 | 0.026 | -0.310 | 0.796 | -0.060 | 0.713 | 0.182 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 2+ | 1174 | 789 | False | False | 33.026 | 34.246 | 1.947 | 2.075 | 3.557 | 3.635 | - | - | - |  |  | 0.068 | 0.083 | -3.824 | -0.854 | 0.153 | -2.763 | -2.898 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple | 1126 | 731 | False | False | 44.456 | 45.101 | 2.379 | 2.521 | 3.211 | 3.354 | - | - | - |  |  | 0.082 | 0.071 | 3.768 | 3.202 | -0.065 | 5.111 | 0.084 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple_with_children | 1197 | 744 | False | False | 33.107 | 33.387 | 2.001 | 1.970 | 3.642 | 3.540 | - | - | - |  |  | 0.057 | 0.081 | -2.848 | -1.687 | 0.091 | -4.620 | -1.900 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | other | 98 | 51 | True | True | 35.711 | 43.804 | 2.183 | 2.427 | 3.667 | 3.324 | - | - | - |  |  | 0.094 | 0.170 | 0.222 | -2.003 | -0.058 | 3.434 | 0.463 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_parent | 374 | 269 | False | False | 35.686 | 36.714 | 2.085 | 1.962 | 3.505 | 3.206 | - | - | - |  |  | 0.072 | 0.051 | -1.462 | -0.345 | -0.058 | -5.002 | 1.810 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_person | 1442 | 1070 | False | False | 40.445 | 48.529 | 2.335 | 2.589 | 3.465 | 3.201 | - | - | - |  |  | 0.069 | 0.111 | 2.871 | 0.085 | -0.061 | 6.476 | 2.146 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | other | 2672 | 1911 | False | False | 42.436 | 47.751 | 2.337 | 2.608 | 3.304 | 3.277 | - | - | - |  |  | 0.059 | 0.095 | 2.965 | 1.984 | -0.063 | 6.740 | 1.105 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | work_study | 1565 | 953 | False | False | 31.177 | 29.947 | 1.952 | 1.762 | 3.772 | 3.530 | - | - | - |  |  | 0.077 | 0.121 | -3.630 | -2.840 | 0.096 | -8.259 | -1.700 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Mode-user composition

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 497 | 292 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | 8507 | 5633 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | 2099 | 1659 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | 632 | 336 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | 594 | 257 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | 1415 | 921 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | 4237 | 2863 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Per-mode decomposition

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Duration-rounding bounds

Scope: Round-trip days · all purposes · all trips in the day's trip table (incl. > 80 km) (`round-allpurp-daytable`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

## All days · destination purposes · local (≤ 80 km)

### Subgroup mode-user days

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 86 | 63 | True | True | 43.884 | 45.992 | 8.137 | 7.847 | 11.126 | 10.237 | 1.048 | 0.798 | 1.357 | inconclusive | inconclusive | 0.141 | 0.182 | 8.014 | -2.715 | 0.000 | 2.800 | 4.116 | 0.000 |  |
| bike | density | intermediate | 164 | 120 | False | False | 39.880 | 42.059 | 7.092 | 8.424 | 10.670 | 12.018 | 1.055 | 0.875 | 1.236 | inconclusive | inconclusive | 0.103 | 0.092 | 2.240 | -0.945 | 0.000 | 5.555 | -2.571 | 0.000 |  |
| bike | density | sparse+very_sparse | 172 | 83 | False | True | 34.171 | 29.255 | 5.451 | 5.351 | 9.572 | 10.974 | 0.856 | 0.628 | 1.213 | inconclusive | inconclusive | 0.173 | 0.175 | -7.485 | 3.071 | 0.000 | -10.751 | 0.931 | 0.000 |  |
| bike | population | children_6_17 | 69 | 31 | True | True | 27.752 | - | 4.765 | - | 10.301 | - | - | - | - |  |  | 0.178 | - | -11.196 | 0.364 | 0.000 | - | - | - |  |
| bike | population | employed | 193 | 136 | False | False | 47.403 | 40.790 | 8.210 | 8.478 | 10.391 | 12.470 | 0.860 | 0.701 | 1.063 | inconclusive | inconclusive | 0.152 | 0.075 | 8.717 | 0.101 | 0.000 | 5.722 | -4.006 | 0.000 |  |
| bike | population | other_inactive | 36 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | population | retired | 105 | 65 | False | True | 36.415 | 38.315 | 5.781 | 6.982 | 9.525 | 10.934 | 1.052 | 0.782 | 1.439 | inconclusive | inconclusive | 0.111 | 0.072 | -5.520 | 3.350 | 0.000 | -1.964 | 1.204 | 0.000 |  |
| bike | population | unemployed | 19 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | income | q1+q2 | 150 | 93 | False | True | 41.518 | 38.766 | 6.677 | 6.340 | 9.649 | 9.813 | 0.934 | 0.730 | 1.204 | inconclusive | inconclusive | 0.090 | 0.096 | -0.129 | 3.062 | 0.000 | -5.729 | 5.421 | 0.000 |  |
| bike | income | q3 | 77 | 52 | True | True | 37.794 | 37.809 | 6.409 | 7.025 | 10.174 | 11.148 | 1.000 | 0.804 | 1.233 | inconclusive | inconclusive | 0.108 | 0.098 | -1.688 | 0.897 | 0.000 | -1.717 | 0.451 | 0.000 |  |
| bike | income | q4 | 77 | 51 | True | True | 37.012 | 36.783 | 7.920 | 7.616 | 12.839 | 12.424 | 0.994 | 0.729 | 1.403 | inconclusive | inconclusive | 0.115 | 0.107 | 6.331 | -7.904 | 0.000 | 1.372 | -3.663 | 0.000 |  |
| bike | income | q5 | 118 | 70 | False | True | 34.713 | 42.990 | 5.920 | 8.881 | 10.233 | 12.394 | 1.238 | 0.998 | 1.545 | inconclusive | inconclusive | 0.115 | 0.091 | -4.521 | 0.649 | 0.000 | 7.780 | -3.864 | 0.000 |  |
| bike | vehicles | 0 | 99 | 56 | True | True | 41.794 | 51.751 | 7.594 | 7.874 | 10.901 | 9.129 | 1.238 | 0.941 | 1.591 | inconclusive | inconclusive | 0.133 | 0.173 | 5.040 | -1.831 | 0.000 | 3.132 | 9.544 | 0.000 |  |
| bike | vehicles | 1 | 160 | 107 | False | False | 44.493 | 39.341 | 7.771 | 8.004 | 10.480 | 12.207 | 0.884 | 0.737 | 1.087 | inconclusive | inconclusive | 0.128 | 0.048 | 6.162 | -0.255 | 0.000 | 3.363 | -3.096 | 0.000 |  |
| bike | vehicles | 2+ | 163 | 100 | False | False | 31.112 | 32.631 | 5.176 | 6.546 | 9.983 | 12.037 | 1.049 | 0.825 | 1.294 | inconclusive | inconclusive | 0.150 | 0.104 | -8.948 | 1.475 | 0.000 | -4.121 | -2.322 | 0.000 |  |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | couple | 121 | 75 | False | True | 35.588 | 34.464 | 5.718 | 6.903 | 9.640 | 12.018 | 0.968 | 0.754 | 1.228 | inconclusive | inconclusive | 0.122 | 0.090 | -5.866 | 2.870 | 0.000 | -2.283 | -2.328 | 0.000 |  |
| bike | household_type | couple_with_children | 145 | 81 | False | True | 38.616 | 37.725 | 6.751 | 7.435 | 10.489 | 11.825 | 0.977 | 0.779 | 1.202 | inconclusive | inconclusive | 0.035 | 0.042 | 0.302 | -0.270 | 0.000 | 0.462 | -1.811 | 0.000 |  |
| bike | household_type | other | 12 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_parent | 32 | 27 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_person | 112 | 78 | False | True | 44.135 | 43.853 | 8.353 | 7.705 | 11.355 | 10.542 | 0.994 | 0.824 | 1.239 | inconclusive | inconclusive | 0.221 | 0.111 | 9.116 | -3.566 | 0.000 | 1.977 | 2.802 | 0.000 |  |
| bike | day_purpose | other | 208 | 127 | False | False | 35.423 | 38.370 | 5.719 | 6.931 | 9.686 | 10.838 | 1.083 | 0.849 | 1.336 | inconclusive | inconclusive | 0.067 | 0.071 | -5.848 | 2.685 | 0.000 | -2.251 | 1.547 | 0.000 |  |
| bike | day_purpose | work_study | 214 | 139 | False | False | 41.726 | 39.710 | 7.671 | 7.720 | 11.031 | 11.665 | 0.952 | 0.800 | 1.160 | inconclusive | inconclusive | 0.066 | 0.064 | 5.443 | -2.302 | 0.000 | 1.957 | -1.322 | 0.000 |  |
| car_driver | density | dense | 679 | 454 | False | False | 62.200 | 68.102 | 29.056 | 28.387 | 28.028 | 25.010 | 1.095 | 1.003 | 1.184 | inconclusive | inconclusive | 0.057 | 0.072 | -14.476 | 16.007 | 0.000 | -19.590 | 23.237 | 0.000 |  |
| car_driver | density | intermediate | 3330 | 2508 | False | False | 60.402 | 64.900 | 31.569 | 33.606 | 31.359 | 31.069 | 1.074 | 1.031 | 1.121 | equivalent | inconclusive | 0.009 | 0.014 | -9.242 | 8.975 | 0.000 | -8.206 | 8.652 | 0.000 |  |
| car_driver | density | sparse | 1286 | 1040 | False | False | 58.939 | 60.518 | 38.487 | 40.160 | 39.179 | 39.816 | 1.027 | 0.944 | 1.105 | equivalent | inconclusive | 0.047 | 0.047 | 2.718 | -4.449 | 0.000 | 3.203 | -7.139 | 0.000 |  |
| car_driver | density | very_sparse | 3539 | 1783 | False | False | 61.707 | 65.664 | 45.235 | 47.018 | 43.983 | 42.962 | 1.064 | 1.000 | 1.118 | equivalent | inconclusive | 0.027 | 0.027 | 12.666 | -11.629 | 0.000 | 13.592 | -12.383 | 0.000 |  |
| car_driver | population | children_6_17 | 80 | 44 | True | True | 43.614 | - | 25.194 | - | 34.659 | - | - | - | - |  |  | 0.212 | - | -19.546 | 2.491 | 0.000 | - | - | - |  |
| car_driver | population | employed | 5586 | 3189 | False | False | 64.525 | 69.306 | 40.368 | 43.070 | 37.537 | 37.287 | 1.074 | 1.034 | 1.112 | equivalent | inconclusive | 0.044 | 0.072 | 5.831 | -1.975 | 0.000 | 8.105 | -3.253 | 0.000 |  |
| car_driver | population | other_inactive | 649 | 305 | False | False | 55.359 | 63.333 | 30.591 | 36.819 | 33.156 | 34.881 | 1.144 | 1.009 | 1.296 | inconclusive | inconclusive | 0.074 | 0.065 | -10.676 | 5.364 | 0.000 | -2.274 | 1.152 | 0.000 |  |
| car_driver | population | retired | 2191 | 1968 | False | False | 52.267 | 53.153 | 28.827 | 27.121 | 33.092 | 30.615 | 1.017 | 0.967 | 1.073 | equivalent | equivalent | 0.107 | 0.159 | -13.728 | 5.325 | 0.000 | -20.006 | 8.705 | 0.000 |  |
| car_driver | population | unemployed | 328 | 275 | False | False | 56.950 | 63.049 | 34.312 | 33.236 | 36.150 | 31.629 | 1.107 | 0.973 | 1.240 | inconclusive | inconclusive | 0.053 | 0.051 | -4.077 | 0.358 | 0.000 | -8.795 | 7.389 | 0.000 |  |
| car_driver | income | q1 | 1035 | 648 | False | False | 52.823 | 59.797 | 30.978 | 32.994 | 35.186 | 33.107 | 1.132 | 1.035 | 1.235 | inconclusive | inconclusive | 0.102 | 0.074 | -9.722 | 1.875 | 0.000 | -9.020 | 4.362 | 0.000 |  |
| car_driver | income | q2 | 1388 | 1071 | False | False | 57.500 | 58.759 | 34.365 | 34.582 | 35.859 | 35.313 | 1.022 | 0.961 | 1.095 | equivalent | equivalent | 0.036 | 0.052 | -4.006 | 0.836 | 0.000 | -6.049 | 0.353 | 0.000 |  |
| car_driver | income | q3 | 1825 | 1219 | False | False | 58.783 | 63.457 | 35.253 | 38.813 | 35.983 | 36.698 | 1.080 | 0.993 | 1.141 | equivalent | inconclusive | 0.034 | 0.037 | -2.526 | 0.639 | 0.000 | 1.097 | -2.095 | 0.000 |  |
| car_driver | income | q4 | 1987 | 1403 | False | False | 63.389 | 67.138 | 40.243 | 40.126 | 38.092 | 35.860 | 1.059 | 1.007 | 1.126 | equivalent | inconclusive | 0.040 | 0.033 | 5.588 | -2.868 | 0.000 | 3.318 | -0.635 | 0.000 |  |
| car_driver | income | q5 | 2599 | 1444 | False | False | 66.439 | 69.446 | 39.811 | 40.929 | 35.953 | 35.362 | 1.045 | 0.994 | 1.103 | equivalent | inconclusive | 0.083 | 0.064 | 5.036 | 0.734 | 0.000 | 4.702 | 0.290 | 0.000 |  |
| car_driver | vehicles | 0 | 62 | 58 | True | True | 65.832 | 63.669 | 40.073 | 33.589 | 36.523 | 31.653 | 0.967 | 0.659 | 1.386 | inconclusive | inconclusive | 0.166 | 0.146 | 5.427 | -0.265 | 0.000 | -8.161 | 7.376 | 0.000 |  |
| car_driver | vehicles | 1 | 3491 | 2607 | False | False | 59.214 | 61.229 | 32.998 | 32.335 | 33.436 | 31.686 | 1.034 | 0.989 | 1.086 | equivalent | equivalent | 0.054 | 0.035 | -6.497 | 5.041 | 0.000 | -10.394 | 7.169 | 0.000 |  |
| car_driver | vehicles | 2+ | 5281 | 3113 | False | False | 61.509 | 66.526 | 39.078 | 41.904 | 38.120 | 37.794 | 1.082 | 1.046 | 1.123 | equivalent | inconclusive | 0.035 | 0.025 | 3.709 | -2.870 | 0.000 | 6.142 | -4.071 | 0.000 |  |
| car_driver | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_driver | household_type | couple | 2987 | 1995 | False | False | 57.975 | 58.424 | 34.309 | 33.538 | 35.507 | 34.443 | 1.008 | 0.955 | 1.058 | equivalent | equivalent | 0.050 | 0.083 | -4.118 | 1.424 | 0.000 | -7.913 | 1.883 | 0.000 |  |
| car_driver | household_type | couple_with_children | 3315 | 1659 | False | False | 63.637 | 69.934 | 39.544 | 43.568 | 37.284 | 37.379 | 1.099 | 1.057 | 1.151 | inconclusive | inconclusive | 0.044 | 0.070 | 4.509 | -1.542 | 0.000 | 8.914 | -3.434 | 0.000 |  |
| car_driver | household_type | other | 181 | 88 | False | True | 56.316 | 58.975 | 34.582 | 31.924 | 36.845 | 32.479 | 1.047 | 0.882 | 1.246 | inconclusive | inconclusive | 0.084 | 0.112 | -3.596 | -0.758 | 0.000 | -10.992 | 5.512 | 0.000 |  |
| car_driver | household_type | single_parent | 553 | 357 | False | False | 57.181 | 65.609 | 33.307 | 37.284 | 34.949 | 34.096 | 1.147 | 0.998 | 1.285 | inconclusive | inconclusive | 0.055 | 0.037 | -5.837 | 2.349 | 0.000 | -1.498 | 2.652 | 0.000 |  |
| car_driver | household_type | single_person | 1798 | 1686 | False | False | 58.118 | 60.471 | 33.956 | 33.022 | 35.056 | 32.765 | 1.040 | 0.989 | 1.108 | equivalent | inconclusive | 0.050 | 0.056 | -4.737 | 2.185 | 0.000 | -9.018 | 5.034 | 0.000 |  |
| car_driver | day_purpose | other | 4170 | 3158 | False | False | 53.755 | 56.864 | 31.207 | 31.242 | 34.832 | 32.965 | 1.058 | 1.012 | 1.110 | equivalent | inconclusive | 0.094 | 0.115 | -9.384 | 2.469 | 0.000 | -12.106 | 4.515 | 0.000 |  |
| car_driver | day_purpose | work_study | 4664 | 2627 | False | False | 66.076 | 70.870 | 41.131 | 43.993 | 37.349 | 37.245 | 1.073 | 1.038 | 1.112 | equivalent | inconclusive | 0.073 | 0.097 | 7.087 | -1.681 | 0.000 | 9.630 | -3.215 | 0.000 |  |
| car_passenger | density | dense | 209 | 174 | False | False | 41.472 | 48.316 | 20.088 | 20.059 | 29.062 | 24.909 | 1.165 | 0.946 | 1.476 | inconclusive | inconclusive | 0.065 | 0.116 | -7.004 | 7.976 | 0.000 | -10.281 | 13.220 | 0.000 |  |
| car_passenger | density | intermediate | 848 | 806 | False | False | 38.325 | 44.431 | 19.368 | 21.498 | 30.321 | 29.031 | 1.159 | 1.047 | 1.260 | inconclusive | inconclusive | 0.032 | 0.035 | -8.173 | 5.998 | 0.000 | -6.746 | 5.800 | 0.000 |  |
| car_passenger | density | sparse | 304 | 297 | False | False | 40.762 | 42.918 | 26.121 | 26.418 | 38.448 | 36.933 | 1.053 | 0.900 | 1.230 | inconclusive | inconclusive | 0.055 | 0.057 | 3.726 | -3.464 | 0.000 | 2.465 | -4.924 | 0.000 |  |
| car_passenger | density | very_sparse | 807 | 441 | False | False | 43.475 | 48.104 | 30.561 | 32.590 | 42.177 | 40.650 | 1.106 | 1.002 | 1.224 | inconclusive | inconclusive | 0.076 | 0.048 | 10.438 | -7.463 | 0.000 | 12.421 | -9.694 | 0.000 |  |
| car_passenger | population | children_6_17 | 647 | 490 | False | False | 31.539 | 36.751 | 17.015 | 18.681 | 32.370 | 30.500 | 1.165 | 1.061 | 1.266 | inconclusive | inconclusive | 0.118 | 0.110 | -12.073 | 3.112 | 0.000 | -11.892 | 3.266 | 0.000 |  |
| car_passenger | population | employed | 625 | 332 | False | False | 44.029 | 52.243 | 26.154 | 32.181 | 35.641 | 36.960 | 1.187 | 1.060 | 1.337 | inconclusive | inconclusive | 0.064 | 0.088 | 3.927 | -0.398 | 0.000 | 12.338 | -5.472 | 0.000 |  |
| car_passenger | population | other_inactive | 255 | 186 | False | False | 51.445 | 49.964 | 28.023 | 24.999 | 32.683 | 30.021 | 0.971 | 0.781 | 1.223 | inconclusive | inconclusive | 0.144 | 0.072 | 7.413 | 3.532 | 0.000 | 0.031 | 4.556 | 0.000 |  |
| car_passenger | population | retired | 551 | 628 | False | False | 51.731 | 56.270 | 35.267 | 33.167 | 40.904 | 35.366 | 1.088 | 0.957 | 1.209 | inconclusive | inconclusive | 0.147 | 0.156 | 17.984 | -6.753 | 0.000 | 14.346 | -3.453 | 0.000 |  |
| car_passenger | population | unemployed | 89 | 80 | True | True | 48.403 | 44.589 | 30.559 | 22.551 | 37.881 | 30.345 | 0.921 | 0.764 | 1.148 | inconclusive | inconclusive | 0.198 | 0.121 | 11.024 | -3.120 | 0.000 | -4.607 | 3.819 | 0.000 |  |
| car_passenger | income | q1 | 387 | 336 | False | False | 39.854 | 44.833 | 22.213 | 21.730 | 33.442 | 29.081 | 1.125 | 0.977 | 1.248 | inconclusive | inconclusive | 0.049 | 0.046 | -2.826 | 2.180 | 0.000 | -6.292 | 5.748 | 0.000 |  |
| car_passenger | income | q2 | 435 | 389 | False | False | 36.396 | 46.556 | 21.338 | 27.073 | 35.176 | 34.890 | 1.279 | 1.117 | 1.427 | inconclusive | different | 0.080 | 0.040 | -4.246 | 0.142 | 0.000 | 3.692 | -2.512 | 0.000 |  |
| car_passenger | income | q3 | 439 | 351 | False | False | 46.198 | 45.631 | 27.867 | 27.089 | 36.192 | 35.619 | 0.988 | 0.851 | 1.145 | equivalent | inconclusive | 0.102 | 0.040 | 6.771 | -1.073 | 0.000 | 3.683 | -3.429 | 0.000 |  |
| car_passenger | income | q4 | 424 | 346 | False | False | 37.177 | 43.778 | 22.139 | 23.121 | 35.730 | 31.689 | 1.178 | 1.056 | 1.319 | inconclusive | inconclusive | 0.052 | 0.026 | -2.860 | -0.462 | 0.000 | -3.452 | 1.853 | 0.000 |  |
| car_passenger | income | q5 | 483 | 296 | False | False | 44.313 | 46.120 | 26.344 | 25.841 | 35.670 | 33.618 | 1.041 | 0.918 | 1.189 | inconclusive | inconclusive | 0.050 | 0.039 | 4.247 | -0.434 | 0.000 | 1.545 | -0.801 | 0.000 |  |
| car_passenger | vehicles | 0 | 280 | 258 | False | False | 40.369 | 45.179 | 21.346 | 20.580 | 31.727 | 27.331 | 1.119 | 0.942 | 1.314 | inconclusive | inconclusive | 0.058 | 0.076 | -4.453 | 4.323 | 0.000 | -8.779 | 8.581 | 0.000 |  |
| car_passenger | vehicles | 1 | 785 | 648 | False | False | 42.263 | 45.665 | 23.900 | 23.471 | 33.930 | 30.839 | 1.080 | 0.974 | 1.194 | inconclusive | inconclusive | 0.066 | 0.029 | 0.118 | 1.646 | 0.000 | -2.842 | 3.130 | 0.000 |  |
| car_passenger | vehicles | 2+ | 1103 | 809 | False | False | 39.334 | 45.201 | 24.201 | 26.626 | 36.916 | 35.344 | 1.149 | 1.052 | 1.256 | inconclusive | inconclusive | 0.046 | 0.017 | 0.614 | -1.779 | 0.000 | 2.885 | -3.061 | 0.000 |  |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_passenger | household_type | couple | 616 | 567 | False | False | 53.159 | 55.985 | 35.101 | 33.648 | 39.618 | 36.061 | 1.053 | 0.946 | 1.173 | inconclusive | inconclusive | 0.154 | 0.154 | 18.021 | -5.362 | 0.000 | 15.036 | -4.427 | 0.000 |  |
| car_passenger | household_type | couple_with_children | 946 | 604 | False | False | 36.549 | 41.055 | 20.491 | 22.165 | 33.639 | 32.394 | 1.123 | 1.032 | 1.234 | inconclusive | inconclusive | 0.051 | 0.059 | -5.813 | 1.862 | 0.000 | -5.168 | 0.845 | 0.000 |  |
| car_passenger | household_type | other | 65 | 38 | True | True | 42.368 | - | 27.642 | - | 39.145 | - | - | - | - |  |  | 0.057 | - | 6.144 | -4.276 | 0.000 | - | - | - |  |
| car_passenger | household_type | single_parent | 178 | 161 | False | False | 39.870 | 41.079 | 21.402 | 19.862 | 32.208 | 29.011 | 1.030 | 0.841 | 1.208 | inconclusive | inconclusive | 0.048 | 0.052 | -4.321 | 3.691 | 0.000 | -9.907 | 5.610 | 0.000 |  |
| car_passenger | household_type | single_person | 363 | 348 | False | False | 37.385 | 48.303 | 20.957 | 24.950 | 33.634 | 30.991 | 1.292 | 1.123 | 1.466 | inconclusive | different | 0.077 | 0.060 | -5.004 | 1.889 | 0.000 | -0.062 | 2.989 | 0.000 |  |
| car_passenger | day_purpose | other | 1186 | 1149 | False | False | 48.542 | 53.634 | 30.928 | 31.927 | 38.228 | 35.717 | 1.105 | 1.022 | 1.190 | inconclusive | inconclusive | 0.114 | 0.108 | 11.572 | -3.530 | 0.000 | 12.113 | -3.856 | 0.000 |  |
| car_passenger | day_purpose | work_study | 982 | 569 | False | False | 33.701 | 35.986 | 17.832 | 17.086 | 31.748 | 28.487 | 1.068 | 0.976 | 1.170 | inconclusive | inconclusive | 0.096 | 0.123 | -10.729 | 3.930 | 0.000 | -15.388 | 5.998 | 0.000 |  |
| other | density | dense | 85 | 52 | True | True | 60.217 | 51.357 | 24.622 | 18.342 | 24.533 | 21.429 | 0.853 | 0.680 | 1.114 | inconclusive | inconclusive | 0.104 | 0.137 | -1.426 | 3.676 | -0.272 | -25.078 | 17.391 | 0.000 |  |
| other | density | intermediate | 193 | 139 | False | False | 55.453 | 56.117 | 22.668 | 25.955 | 24.532 | 27.751 | 1.012 | 0.830 | 1.229 | inconclusive | inconclusive | 0.057 | 0.079 | -6.066 | 3.530 | -0.250 | -6.211 | 3.284 | 0.000 |  |
| other | density | sparse+very_sparse | 372 | 164 | False | False | 59.580 | 63.558 | 26.852 | 34.276 | 27.253 | 32.357 | 1.067 | 0.924 | 1.244 | inconclusive | inconclusive | 0.031 | 0.073 | 3.688 | -2.538 | 0.191 | 10.429 | -5.914 | 0.000 |  |
| other | population | children_6_17 | 273 | 89 | False | True | 57.194 | 57.720 | 21.790 | 19.737 | 22.859 | 20.517 | 1.009 | 0.842 | 1.203 | inconclusive | inconclusive | 0.042 | 0.079 | -8.442 | 7.662 | -0.265 | -22.287 | 20.963 | 0.000 |  |
| other | population | employed | 267 | 151 | False | False | 62.516 | 60.065 | 32.104 | 33.135 | 31.196 | 33.099 | 0.961 | 0.815 | 1.178 | inconclusive | inconclusive | 0.093 | 0.062 | 14.561 | -10.754 | 0.471 | 8.119 | -7.098 | 0.000 |  |
| other | population | other_inactive | 40 | 30 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | population | retired | 59 | 73 | True | True | 48.920 | 57.626 | 21.229 | 34.270 | 26.074 | 35.682 | 1.178 | 0.847 | 1.720 | inconclusive | inconclusive | 0.191 | 0.117 | -9.211 | 0.062 | -0.171 | 9.916 | -11.335 | 0.000 |  |
| other | population | unemployed | 11 | 12 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | income | q1 | 108 | 71 | False | True | 58.264 | 68.068 | 26.133 | 36.851 | 26.912 | 32.483 | 1.168 | 0.932 | 1.474 | inconclusive | inconclusive | 0.036 | 0.209 | 2.067 | -1.775 | -0.268 | 15.394 | -6.370 | 0.000 |  |
| other | income | q2 | 156 | 78 | False | True | 63.364 | 45.028 | 25.080 | 19.725 | 24.002 | 26.284 | 0.711 | 0.581 | 0.875 | inconclusive | different | 0.101 | 0.145 | -0.342 | 5.101 | 0.365 | -19.777 | 5.760 | 0.000 |  |
| other | income | q3 | 112 | 68 | False | True | 58.867 | 63.621 | 22.910 | 29.103 | 23.418 | 27.446 | 1.081 | 0.891 | 1.441 | inconclusive | inconclusive | 0.075 | 0.092 | -5.629 | 6.359 | -0.102 | 0.403 | 4.174 | 0.000 |  |
| other | income | q4 | 127 | 58 | False | True | 51.469 | 51.449 | 26.953 | 26.425 | 31.584 | 30.817 | 1.000 | 0.786 | 1.217 | inconclusive | inconclusive | 0.122 | 0.147 | 3.636 | -10.439 | 0.033 | -4.962 | -2.633 | 0.000 |  |
| other | income | q5 | 147 | 80 | False | True | 57.627 | 64.694 | 24.923 | 31.510 | 26.011 | 29.223 | 1.123 | 0.906 | 1.442 | inconclusive | inconclusive | 0.046 | 0.055 | -0.691 | 0.208 | -0.129 | 5.319 | 0.331 | 0.000 |  |
| other | vehicles | 0 | 100 | 68 | False | True | 48.590 | 56.266 | 16.712 | 26.574 | 20.636 | 28.338 | 1.158 | 0.890 | 1.484 | inconclusive | inconclusive | 0.165 | 0.064 | -21.926 | 12.521 | -0.245 | -4.861 | 2.082 | 0.000 |  |
| other | vehicles | 1 | 211 | 127 | False | False | 58.920 | 54.407 | 28.002 | 24.257 | 28.554 | 26.751 | 0.923 | 0.793 | 1.083 | inconclusive | inconclusive | 0.051 | 0.045 | 6.125 | -5.255 | -0.190 | -9.952 | 5.315 | 0.000 |  |
| other | vehicles | 2+ | 339 | 160 | False | False | 59.735 | 63.159 | 25.186 | 32.949 | 25.484 | 31.301 | 1.057 | 0.894 | 1.262 | inconclusive | inconclusive | 0.033 | 0.031 | -0.084 | 1.418 | 0.162 | 7.984 | -3.869 | 0.000 |  |
| other | household_type | couple | 85 | 86 | True | True | 51.629 | 58.813 | 26.829 | 31.636 | 31.317 | 32.274 | 1.139 | 0.912 | 1.516 | inconclusive | inconclusive | 0.196 | 0.050 | 3.389 | -9.989 | -0.010 | 5.305 | -5.535 | 0.000 |  |
| other | household_type | couple_with_children | 366 | 132 | False | False | 62.724 | 60.237 | 27.268 | 27.824 | 26.240 | 27.715 | 0.960 | 0.805 | 1.115 | inconclusive | inconclusive | 0.066 | 0.029 | 4.714 | -0.314 | 0.084 | -2.288 | 3.481 | 0.000 |  |
| other | household_type | other | 20 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | household_type | single_parent | 64 | 43 | True | True | 56.189 | - | 20.960 | - | 22.382 | - | - | - | - |  |  | 0.092 | - | -10.589 | 8.802 | -0.263 | - | - | - |  |
| other | household_type | single_person | 115 | 87 | False | True | 45.843 | 63.836 | 18.716 | 39.796 | 24.496 | 37.405 | 1.392 | 1.049 | 1.863 | inconclusive | inconclusive | 0.220 | 0.132 | -15.452 | 3.293 | -0.238 | 19.621 | -14.829 | 0.000 |  |
| other | day_purpose | other | 116 | 126 | False | False | 44.530 | 60.204 | 18.952 | 35.291 | 25.549 | 35.172 | 1.352 | 1.096 | 1.780 | inconclusive | inconclusive | 0.197 | 0.080 | -14.597 | 1.097 | -0.209 | 11.887 | -10.728 | 0.000 |  |
| other | day_purpose | work_study | 534 | 229 | False | False | 60.966 | 58.679 | 26.469 | 26.906 | 26.185 | 27.512 | 0.962 | 0.848 | 1.080 | inconclusive | inconclusive | 0.039 | 0.025 | 2.876 | -0.185 | 0.036 | -4.233 | 3.868 | 0.000 |  |
| train | density | dense+intermediate+sparse+very_sparse | 603 | 253 | False | False | 116.414 | 125.735 | 45.279 | 52.812 | 23.782 | 25.201 | 1.080 | 0.985 | 1.182 | inconclusive | inconclusive | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 |  |
| train | population | children_6_17 | 27 | 18 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | employed | 452 | 176 | False | False | 118.976 | 128.078 | 46.517 | 56.056 | 23.524 | 26.260 | 1.076 | 0.964 | 1.189 | inconclusive | inconclusive | 0.043 | 0.034 | 3.174 | 1.285 | -1.897 | 7.566 | -5.223 | 0.000 |  |
| train | population | other_inactive | 56 | 26 | True | True | 120.195 | - | 48.447 | - | 24.184 | - | - | - | - |  |  | 0.115 | - | 8.000 | -1.985 | -2.234 | - | - | - |  |
| train | population | retired | 50 | 23 | True | True | 123.104 | - | 49.427 | - | 24.090 | - | - | - | - |  |  | 0.101 | - | 10.495 | -1.544 | -2.261 | - | - | - |  |
| train | population | unemployed | 18 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | income | q1+q2+q3+q4 | 336 | 163 | False | False | 116.648 | 126.244 | 46.655 | 49.828 | 24.186 | 23.682 | 1.082 | 0.967 | 1.218 | inconclusive | inconclusive | 0.019 | 0.037 | 3.488 | -1.964 | -1.290 | -7.327 | 7.836 | 0.000 |  |
| train | income | q5 | 267 | 90 | False | True | 116.024 | 124.566 | 42.982 | 59.669 | 23.082 | 28.741 | 1.074 | 0.945 | 1.208 | inconclusive | inconclusive | 0.032 | 0.084 | -6.052 | 3.469 | 2.192 | 15.278 | -16.448 | 0.000 |  |
| train | vehicles | 0 | 196 | 80 | False | True | 107.666 | 131.267 | 32.936 | 45.824 | 18.355 | 20.945 | 1.219 | 1.004 | 1.428 | inconclusive | inconclusive | 0.111 | 0.110 | -35.641 | 29.007 | -2.115 | -18.235 | 23.766 | 0.000 |  |
| train | vehicles | 1 | 256 | 101 | False | False | 121.245 | 121.701 | 48.771 | 53.558 | 24.843 | 26.405 | 1.004 | 0.877 | 1.126 | equivalent | inconclusive | 0.055 | 0.083 | 8.826 | -5.186 | 1.191 | 1.736 | -5.771 | 0.000 |  |
| train | vehicles | 2+ | 151 | 69 | False | True | 116.129 | 117.713 | 50.290 | 53.408 | 26.435 | 27.223 | 1.014 | 0.852 | 1.226 | inconclusive | inconclusive | 0.055 | 0.092 | 12.203 | -12.298 | -0.190 | 1.365 | -9.388 | 0.000 |  |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | couple | 129 | 50 | False | True | 122.535 | 139.921 | 50.167 | 74.985 | 24.565 | 32.155 | 1.142 | 0.958 | 1.365 | inconclusive | inconclusive | 0.066 | 0.108 | 12.244 | -3.868 | -2.256 | 46.519 | -32.333 | 0.000 |  |
| train | household_type | couple_with_children | 206 | 86 | False | True | 110.842 | 114.399 | 41.351 | 48.395 | 23.315 | 25.382 | 1.032 | 0.875 | 1.204 | inconclusive | inconclusive | 0.051 | 0.075 | -10.309 | 2.254 | 2.483 | -10.480 | -0.856 | 0.000 |  |
| train | household_type | other | 18 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | single_parent | 64 | 33 | True | True | 129.215 | - | 51.272 | - | 23.808 | - | - | - | - |  |  | 0.146 | - | 15.252 | -0.134 | -2.317 | - | - | - |  |
| train | household_type | single_person | 186 | 76 | False | True | 112.826 | 128.249 | 46.984 | 50.739 | 24.986 | 23.738 | 1.137 | 1.007 | 1.261 | inconclusive | inconclusive | 0.045 | 0.063 | 4.237 | -5.661 | -2.164 | -5.085 | 7.599 | 0.000 |  |
| train | day_purpose | other | 109 | 53 | False | True | 110.541 | 130.976 | 44.148 | 49.042 | 23.963 | 22.466 | 1.185 | 0.997 | 1.383 | inconclusive | inconclusive | 0.114 | 0.148 | -2.869 | -0.861 | -2.142 | -9.504 | 14.745 | 0.000 |  |
| train | day_purpose | work_study | 494 | 200 | False | False | 117.555 | 124.805 | 45.499 | 53.481 | 23.748 | 25.711 | 1.062 | 0.951 | 1.170 | inconclusive | inconclusive | 0.022 | 0.026 | 0.566 | 0.167 | 0.408 | 1.577 | -2.507 | 0.000 |  |
| urban_pt | density | dense | 722 | 378 | False | False | 71.400 | 73.642 | 12.993 | 10.397 | 10.919 | 8.471 | 1.031 | 0.935 | 1.129 | equivalent | inconclusive | 0.031 | 0.047 | -14.329 | 13.622 | 0.000 | -23.891 | 22.576 | 0.000 |  |
| urban_pt | density | intermediate | 659 | 489 | False | False | 73.402 | 77.912 | 16.655 | 15.222 | 13.614 | 11.722 | 1.061 | 0.974 | 1.157 | inconclusive | inconclusive | 0.026 | 0.044 | 3.533 | -2.238 | 0.000 | 4.561 | -1.606 | 0.000 |  |
| urban_pt | density | sparse+very_sparse | 94 | 92 | True | True | 67.818 | 67.215 | 25.519 | 22.679 | 22.577 | 20.244 | 0.991 | 0.790 | 1.280 | inconclusive | inconclusive | 0.147 | 0.112 | 33.243 | -37.532 | 0.000 | 32.554 | -40.295 | 0.000 |  |
| urban_pt | population | children_6_17 | 143 | 181 | False | False | 65.620 | 69.503 | 18.360 | 16.979 | 16.788 | 14.658 | 1.059 | 0.847 | 1.295 | inconclusive | inconclusive | 0.144 | 0.104 | 10.052 | -16.538 | 0.000 | 12.199 | -17.652 | 0.000 |  |
| urban_pt | population | employed | 748 | 360 | False | False | 73.873 | 74.692 | 14.388 | 13.858 | 11.686 | 11.132 | 1.011 | 0.932 | 1.097 | equivalent | equivalent | 0.052 | 0.040 | -7.133 | 8.899 | 0.000 | -2.557 | 2.293 | 0.000 |  |
| urban_pt | population | other_inactive | 241 | 152 | False | False | 76.273 | 80.432 | 18.550 | 13.187 | 14.592 | 9.837 | 1.055 | 0.918 | 1.187 | inconclusive | inconclusive | 0.108 | 0.086 | 11.597 | -7.431 | 0.000 | -6.511 | 11.986 | 0.000 |  |
| urban_pt | population | retired | 265 | 179 | False | False | 66.214 | 74.940 | 13.221 | 11.618 | 11.980 | 9.302 | 1.132 | 1.019 | 1.260 | inconclusive | inconclusive | 0.099 | 0.070 | -12.603 | 6.711 | 0.000 | -15.776 | 15.760 | 0.000 |  |
| urban_pt | population | unemployed | 78 | 85 | True | True | 79.745 | 83.012 | 14.556 | 13.755 | 10.952 | 9.942 | 1.041 | 0.769 | 1.374 | inconclusive | inconclusive | 0.104 | 0.120 | -6.533 | 14.171 | 0.000 | -3.286 | 11.342 | 0.000 |  |
| urban_pt | income | q1 | 311 | 299 | False | False | 78.031 | 78.574 | 19.920 | 13.216 | 15.317 | 10.092 | 1.007 | 0.881 | 1.171 | inconclusive | inconclusive | 0.069 | 0.056 | 17.077 | -11.152 | 0.000 | -6.261 | 9.879 | 0.000 |  |
| urban_pt | income | q2 | 239 | 167 | False | False | 74.862 | 78.861 | 15.549 | 14.143 | 12.462 | 10.760 | 1.053 | 0.917 | 1.207 | inconclusive | inconclusive | 0.067 | 0.085 | -1.481 | 4.237 | 0.000 | -1.062 | 4.966 | 0.000 |  |
| urban_pt | income | q3 | 243 | 160 | False | False | 75.538 | 74.868 | 14.419 | 16.856 | 11.453 | 13.509 | 0.991 | 0.877 | 1.118 | equivalent | inconclusive | 0.095 | 0.058 | -7.054 | 10.485 | 0.000 | 12.114 | -12.202 | 0.000 |  |
| urban_pt | income | q4 | 266 | 140 | False | False | 63.709 | 67.699 | 14.556 | 14.025 | 13.708 | 12.430 | 1.063 | 0.932 | 1.236 | inconclusive | inconclusive | 0.097 | 0.071 | -5.841 | -2.556 | 0.000 | -1.584 | -5.673 | 0.000 |  |
| urban_pt | income | q5 | 416 | 193 | False | False | 66.378 | 71.460 | 12.952 | 14.090 | 11.707 | 11.831 | 1.077 | 0.971 | 1.184 | inconclusive | inconclusive | 0.075 | 0.046 | -14.042 | 8.313 | 0.000 | -1.283 | -2.213 | 0.000 |  |
| urban_pt | vehicles | 0 | 749 | 485 | False | False | 78.780 | 79.644 | 16.806 | 12.241 | 12.800 | 9.222 | 1.011 | 0.923 | 1.113 | equivalent | inconclusive | 0.088 | 0.074 | 4.344 | 2.329 | 0.000 | -12.230 | 16.917 | 0.000 |  |
| urban_pt | vehicles | 1 | 483 | 293 | False | False | 67.730 | 67.399 | 13.438 | 12.250 | 11.904 | 10.905 | 0.995 | 0.912 | 1.083 | equivalent | equivalent | 0.058 | 0.092 | -11.606 | 7.229 | 0.000 | -11.202 | 3.645 | 0.000 |  |
| urban_pt | vehicles | 2+ | 243 | 176 | False | False | 66.983 | 77.104 | 18.091 | 20.370 | 16.205 | 15.851 | 1.151 | 0.996 | 1.331 | inconclusive | inconclusive | 0.106 | 0.061 | 9.125 | -14.249 | 0.000 | 26.687 | -24.539 | 0.000 |  |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | couple | 269 | 129 | False | False | 68.892 | 71.363 | 14.237 | 13.379 | 12.399 | 11.249 | 1.036 | 0.930 | 1.180 | inconclusive | inconclusive | 0.049 | 0.092 | -7.633 | 4.419 | 0.000 | -5.071 | 1.477 | 0.000 |  |
| urban_pt | household_type | couple_with_children | 377 | 272 | False | False | 72.266 | 74.997 | 15.457 | 17.185 | 12.833 | 13.748 | 1.038 | 0.941 | 1.152 | inconclusive | inconclusive | 0.033 | 0.032 | -1.881 | 2.041 | 0.000 | 13.570 | -13.530 | 0.000 |  |
| urban_pt | household_type | other | 35 | 40 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | single_parent | 157 | 137 | False | False | 76.114 | 68.057 | 22.130 | 11.955 | 17.444 | 10.540 | 0.894 | 0.728 | 1.066 | inconclusive | inconclusive | 0.068 | 0.122 | 24.657 | -20.650 | 0.000 | -12.996 | 6.097 | 0.000 |  |
| urban_pt | household_type | single_person | 637 | 381 | False | False | 72.390 | 76.855 | 15.007 | 11.734 | 12.439 | 9.160 | 1.062 | 0.974 | 1.148 | equivalent | inconclusive | 0.066 | 0.033 | -4.015 | 4.298 | 0.000 | -15.222 | 17.121 | 0.000 |  |
| urban_pt | day_purpose | other | 542 | 422 | False | False | 69.038 | 75.457 | 17.331 | 12.586 | 15.062 | 10.008 | 1.093 | 0.963 | 1.234 | inconclusive | inconclusive | 0.112 | 0.035 | 6.237 | -9.305 | 0.000 | -9.809 | 10.310 | 0.000 |  |
| urban_pt | day_purpose | work_study | 933 | 537 | False | False | 73.561 | 74.709 | 15.170 | 15.203 | 12.374 | 12.210 | 1.016 | 0.949 | 1.086 | equivalent | equivalent | 0.053 | 0.017 | -3.262 | 4.717 | 0.000 | 4.377 | -4.624 | 0.000 |  |
| walk | density | dense | 996 | 625 | False | False | 33.851 | 37.424 | 2.089 | 2.101 | 3.732 | 3.368 | 1.106 | 1.009 | 1.221 | inconclusive | inconclusive | 0.084 | 0.132 | 3.883 | -0.644 | 0.182 | 5.524 | 0.459 | 0.000 |  |
| walk | density | intermediate | 1775 | 1298 | False | False | 31.623 | 31.571 | 1.923 | 1.792 | 3.649 | 3.405 | 0.998 | 0.925 | 1.069 | equivalent | equivalent | 0.034 | 0.020 | 1.188 | 0.073 | -0.066 | 0.055 | 0.075 | 0.000 |  |
| walk | density | sparse | 427 | 302 | False | False | 27.489 | 28.762 | 1.666 | 1.682 | 3.637 | 3.508 | 1.046 | 0.894 | 1.182 | inconclusive | inconclusive | 0.060 | 0.108 | -3.040 | 0.163 | -0.061 | -1.858 | -0.821 | 0.000 |  |
| walk | density | very_sparse | 611 | 278 | False | False | 21.701 | 19.185 | 1.266 | 1.123 | 3.499 | 3.513 | 0.884 | 0.788 | 1.007 | inconclusive | inconclusive | 0.183 | 0.247 | -9.817 | 1.145 | -0.055 | -11.540 | -0.716 | 0.000 |  |
| walk | population | children_6_17 | 478 | 361 | False | False | 29.095 | 28.566 | 1.759 | 1.537 | 3.627 | 3.228 | 0.982 | 0.870 | 1.085 | equivalent | inconclusive | 0.027 | 0.055 | -1.523 | 0.253 | -0.063 | -4.548 | 1.674 | 0.000 |  |
| walk | population | employed | 1433 | 814 | False | False | 28.022 | 28.071 | 1.790 | 1.731 | 3.858 | 3.699 | 1.002 | 0.913 | 1.083 | equivalent | equivalent | 0.076 | 0.062 | -0.986 | -1.554 | 0.135 | -0.980 | -2.389 | 0.000 |  |
| walk | population | other_inactive | 498 | 279 | False | False | 33.157 | 38.844 | 2.140 | 2.244 | 3.873 | 3.466 | 1.172 | 1.042 | 1.316 | inconclusive | inconclusive | 0.071 | 0.152 | 4.611 | -1.815 | -0.067 | 7.941 | -0.537 | 0.000 |  |
| walk | population | retired | 1168 | 878 | False | False | 32.285 | 34.249 | 1.751 | 1.849 | 3.254 | 3.238 | 1.061 | 0.968 | 1.133 | equivalent | inconclusive | 0.084 | 0.066 | -1.740 | 3.663 | -0.066 | 1.082 | 1.727 | 0.000 |  |
| walk | population | unemployed | 232 | 169 | False | False | 38.178 | 40.487 | 2.394 | 2.255 | 3.763 | 3.342 | 1.060 | 0.838 | 1.312 | inconclusive | inconclusive | 0.143 | 0.098 | 8.788 | -0.965 | -0.072 | 8.286 | 0.761 | 0.000 |  |
| walk | income | q1 | 871 | 622 | False | False | 35.530 | 35.019 | 2.144 | 1.976 | 3.644 | 3.385 | 0.986 | 0.896 | 1.087 | equivalent | inconclusive | 0.080 | 0.083 | 4.831 | 0.121 | 0.150 | 3.302 | 0.276 | 0.000 |  |
| walk | income | q2 | 662 | 470 | False | False | 28.463 | 32.465 | 1.751 | 1.856 | 3.691 | 3.430 | 1.141 | 1.014 | 1.273 | inconclusive | inconclusive | 0.029 | 0.045 | -1.633 | -0.270 | -0.062 | 1.183 | -0.158 | 0.000 |  |
| walk | income | q3 | 670 | 409 | False | False | 27.695 | 28.036 | 1.653 | 1.598 | 3.581 | 3.421 | 1.012 | 0.905 | 1.134 | equivalent | inconclusive | 0.062 | 0.066 | -3.291 | 0.619 | -0.062 | -3.342 | -0.063 | 0.000 |  |
| walk | income | q4 | 663 | 473 | False | False | 28.858 | 30.538 | 1.787 | 1.773 | 3.715 | 3.483 | 1.058 | 0.923 | 1.178 | inconclusive | inconclusive | 0.077 | 0.050 | -1.050 | -0.458 | -0.063 | -0.277 | -0.626 | 0.000 |  |
| walk | income | q5 | 943 | 529 | False | False | 29.006 | 29.406 | 1.769 | 1.651 | 3.658 | 3.369 | 1.014 | 0.910 | 1.131 | equivalent | inconclusive | 0.056 | 0.056 | -1.353 | -0.006 | -0.063 | -2.429 | 0.395 | 0.000 |  |
| walk | vehicles | 0 | 1221 | 799 | False | False | 37.034 | 37.707 | 2.263 | 2.050 | 3.666 | 3.262 | 1.018 | 0.954 | 1.110 | equivalent | inconclusive | 0.147 | 0.109 | 6.750 | -0.073 | -0.071 | 4.703 | 1.564 | 0.000 |  |
| walk | vehicles | 1 | 1599 | 1037 | False | False | 29.344 | 32.510 | 1.786 | 1.849 | 3.652 | 3.412 | 1.108 | 1.027 | 1.188 | inconclusive | inconclusive | 0.027 | 0.025 | -1.063 | 0.043 | -0.063 | 1.052 | 0.017 | 0.000 |  |
| walk | vehicles | 2+ | 989 | 660 | False | False | 26.706 | 24.596 | 1.615 | 1.478 | 3.657 | 3.606 | 0.921 | 0.822 | 1.006 | inconclusive | inconclusive | 0.083 | 0.113 | -3.893 | 0.002 | 0.169 | -5.312 | -1.533 | 0.000 |  |
| walk | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | household_type | couple | 883 | 575 | False | False | 30.825 | 31.130 | 1.797 | 1.818 | 3.498 | 3.504 | 1.010 | 0.918 | 1.117 | equivalent | inconclusive | 0.021 | 0.033 | -0.902 | 1.363 | -0.065 | 0.508 | -0.819 | 0.000 |  |
| walk | household_type | couple_with_children | 1123 | 693 | False | False | 28.990 | 28.376 | 1.796 | 1.651 | 3.735 | 3.491 | 0.979 | 0.896 | 1.050 | equivalent | inconclusive | 0.044 | 0.044 | -0.898 | -0.625 | 0.084 | -2.396 | -0.668 | 0.000 |  |
| walk | household_type | other | 85 | 47 | True | True | 28.555 | - | 1.821 | - | 3.827 | - | - | - | - |  |  | 0.065 | - | -0.478 | -1.332 | -0.063 | - | - | - |  |
| walk | household_type | single_parent | 360 | 248 | False | False | 31.744 | 32.050 | 1.926 | 1.761 | 3.641 | 3.297 | 1.010 | 0.863 | 1.194 | inconclusive | inconclusive | 0.047 | 0.044 | 1.236 | 0.146 | -0.066 | -0.494 | 1.104 | 0.000 |  |
| walk | household_type | single_person | 1358 | 940 | False | False | 32.825 | 37.636 | 1.992 | 2.058 | 3.641 | 3.281 | 1.147 | 1.071 | 1.243 | inconclusive | inconclusive | 0.068 | 0.105 | 2.316 | 0.147 | -0.067 | 4.838 | 1.358 | 0.000 |  |
| walk | day_purpose | other | 2243 | 1564 | False | False | 30.753 | 34.970 | 1.822 | 1.925 | 3.555 | 3.303 | 1.137 | 1.066 | 1.205 | inconclusive | inconclusive | 0.017 | 0.057 | -0.484 | 0.873 | -0.065 | 2.441 | 1.089 | 0.000 |  |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | day_purpose | work_study | 1566 | 938 | False | False | 30.071 | 27.820 | 1.883 | 1.648 | 3.774 | 3.554 | 0.925 | 0.855 | 0.999 | equivalent | inconclusive | 0.019 | 0.058 | 0.518 | -0.947 | 0.072 | -2.426 | -1.194 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Mode-user composition

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 422 | 266 | 1.013 | - | 0.019 | 0.000 | insufficient common support for 2008 target |
| car_driver | 8834 | 5781 | 1.062 | 1.069 | 0.000 | 0.000 |  |
| car_passenger | 2167 | 1716 | 1.120 | 1.113 | 0.000 | 0.000 |  |
| other | 650 | 355 | 1.014 | 0.996 | 0.008 | 0.000 | 2008 target rescaled to common support |
| train | 603 | 252 | 1.080 | 1.072 | 0.001 | 0.000 | 2008 target rescaled to common support |
| urban_pt | 1475 | 957 | 1.039 | 1.042 | 0.000 | 0.001 |  |
| walk | 3809 | 2501 | 1.033 | 1.025 | 0.000 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Per-mode decomposition

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | 0.490 | 1.002 | 1.210 | -1.722 | 0.000 |  |
| bike | rounded_crow_fly | 0.490 | 1.002 | 9.542 | -10.055 | 0.000 |  |
| car_driver | published | 3.785 | -3.493 | 5.408 | 1.870 | 0.000 |  |
| car_driver | rounded_crow_fly | 3.785 | -3.493 | 5.312 | 1.966 | 0.000 |  |
| car_passenger | published | 4.877 | -1.358 | 3.193 | 3.042 | 0.000 |  |
| car_passenger | rounded_crow_fly | 4.877 | -1.358 | 3.960 | 2.275 | 0.000 |  |
| other | published | 0.805 | -4.623 | 12.119 | -6.933 | 0.242 |  |
| other | rounded_crow_fly | 0.805 | -4.623 | 14.436 | -9.008 | 0.000 |  |
| train | published | 9.321 | -5.521 | 22.779 | -7.017 | -0.919 |  |
| train | rounded_crow_fly | 9.321 | -5.521 | 15.977 | -1.135 | 0.000 |  |
| urban_pt | published | 2.850 | -2.018 | -5.415 | 10.282 | -0.000 |  |
| urban_pt | rounded_crow_fly | 2.850 | -2.018 | 0.331 | 4.537 | -0.000 |  |
| walk | published | 1.012 | -1.052 | 2.685 | -0.597 | -0.024 |  |
| walk | rounded_crow_fly | 1.012 | -1.052 | -0.868 | 2.932 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Duration-rounding bounds

Scope: All days · destination purposes · local (≤ 80 km) (`alldays-dest-local`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | -0.037 | 0.928 | 0.000 |  |
| car_driver | 0.010 | 3.120 | 0.000 |  |
| car_passenger | -0.056 | 1.329 | 0.000 |  |
| other | -0.201 | 1.623 | 0.000 |  |
| train | -0.173 | 2.042 | 0.000 |  |
| urban_pt | -0.019 | 0.621 | 0.000 |  |
| walk | -0.080 | 0.656 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


## All days · destination purposes · all trips in the day's trip table (incl. > 80 km)

### Subgroup mode-user days

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 87 | 63 | True | True | 43.876 | 45.992 | 8.135 | 7.847 | 11.124 | 10.237 | - | - | - |  |  | 0.139 | 0.181 | 7.876 | -3.276 | 0.000 | 2.620 | 4.228 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | intermediate | 165 | 122 | False | False | 40.107 | 42.193 | 7.125 | 8.488 | 10.659 | 12.070 | - | - | - |  |  | 0.102 | 0.092 | 2.264 | -1.433 | 0.000 | 5.698 | -2.649 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | sparse+very_sparse | 176 | 83 | False | True | 35.823 | 29.255 | 5.513 | 5.351 | 9.234 | 10.974 | - | - | - |  |  | 0.168 | 0.175 | -7.481 | 4.028 | 0.000 | -10.907 | 1.018 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | children_6_17 | 69 | 31 | True | True | 27.752 | - | 4.765 | - | 10.301 | - | - | - | - |  |  | 0.181 | - | -11.457 | -0.066 | 0.000 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | employed | 196 | 136 | False | False | 47.506 | 40.790 | 8.220 | 8.478 | 10.382 | 12.470 | - | - | - |  |  | 0.151 | 0.074 | 8.653 | -0.423 | 0.000 | 5.555 | -3.908 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | other_inactive | 37 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | retired | 106 | 67 | False | True | 36.628 | 38.716 | 5.791 | 7.167 | 9.486 | 11.108 | - | - | - |  |  | 0.111 | 0.070 | -5.702 | 3.053 | 0.000 | -1.125 | 0.697 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | unemployed | 20 | 17 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q1+q2 | 151 | 93 | False | True | 42.866 | 38.766 | 6.723 | 6.340 | 9.411 | 9.813 | - | - | - |  |  | 0.090 | 0.098 | -0.038 | 3.628 | 0.000 | -5.901 | 5.525 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q3 | 78 | 52 | True | True | 37.715 | 37.809 | 6.393 | 7.025 | 10.171 | 11.148 | - | - | - |  |  | 0.108 | 0.098 | -1.975 | 0.413 | 0.000 | -1.883 | 0.549 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q4 | 80 | 51 | True | True | 37.781 | 36.783 | 7.984 | 7.616 | 12.680 | 12.424 | - | - | - |  |  | 0.104 | 0.108 | 6.586 | -8.081 | 0.000 | 1.210 | -3.570 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q5 | 119 | 72 | False | True | 34.706 | 43.248 | 5.918 | 9.002 | 10.231 | 12.490 | - | - | - |  |  | 0.118 | 0.096 | -4.750 | 0.180 | 0.000 | 8.194 | -4.089 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 0 | 100 | 56 | False | True | 41.788 | 51.751 | 7.592 | 7.874 | 10.900 | 9.129 | - | - | - |  |  | 0.130 | 0.172 | 4.883 | -2.371 | 0.000 | 2.941 | 9.666 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 1 | 161 | 108 | False | False | 44.583 | 39.505 | 7.773 | 8.083 | 10.461 | 12.276 | - | - | - |  |  | 0.125 | 0.048 | 6.038 | -0.730 | 0.000 | 3.590 | -3.229 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 2+ | 167 | 101 | False | False | 32.872 | 32.677 | 5.280 | 6.555 | 9.638 | 12.036 | - | - | - |  |  | 0.142 | 0.103 | -8.727 | 2.324 | 0.000 | -4.232 | -2.234 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple | 123 | 76 | False | True | 35.775 | 34.543 | 5.724 | 6.919 | 9.600 | 12.018 | - | - | - |  |  | 0.122 | 0.092 | -6.067 | 2.567 | 0.000 | -2.362 | -2.238 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple_with_children | 148 | 81 | False | True | 39.870 | 37.725 | 6.810 | 7.435 | 10.248 | 11.825 | - | - | - |  |  | 0.032 | 0.043 | 0.467 | 0.127 | 0.000 | 0.297 | -1.715 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | other | 12 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_parent | 32 | 27 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_person | 113 | 79 | False | True | 44.126 | 44.202 | 8.350 | 7.887 | 11.353 | 10.706 | - | - | - |  |  | 0.218 | 0.113 | 8.984 | -4.135 | 0.000 | 2.781 | 2.277 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | other | 210 | 128 | False | False | 36.693 | 38.666 | 5.766 | 7.020 | 9.429 | 10.894 | - | - | - |  |  | 0.068 | 0.066 | -5.866 | 3.283 | 0.000 | -1.929 | 1.452 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | work_study | 218 | 140 | False | False | 41.822 | 39.571 | 7.679 | 7.697 | 11.017 | 11.671 | - | - | - |  |  | 0.067 | 0.059 | 5.350 | -2.804 | 0.000 | 1.670 | -1.242 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | dense | 703 | 467 | False | False | 66.443 | 85.688 | 34.040 | 49.939 | 30.805 | 34.968 | - | - | - |  |  | 0.056 | 0.079 | -14.567 | 15.623 | 0.036 | 8.689 | 7.273 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | intermediate | 3406 | 2553 | False | False | 64.786 | 68.816 | 37.371 | 38.428 | 34.617 | 33.505 | - | - | - |  |  | 0.008 | 0.016 | -8.309 | 7.836 | -0.093 | -10.378 | 9.468 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | sparse | 1317 | 1055 | False | False | 64.212 | 63.076 | 44.680 | 43.489 | 41.765 | 41.368 | - | - | - |  |  | 0.040 | 0.045 | 3.300 | -4.360 | -0.080 | -1.732 | -4.919 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | very_sparse | 3620 | 1824 | False | False | 66.560 | 71.242 | 50.634 | 53.891 | 45.835 | 45.386 | - | - | - |  |  | 0.025 | 0.029 | 11.610 | -10.572 | 0.170 | 13.276 | -11.759 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | children_6_17 | 80 | 48 | True | True | 43.614 | - | 25.194 | - | 34.659 | - | - | - | - |  |  | 0.223 | - | -28.059 | 6.408 | -0.087 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | employed | 5735 | 3259 | False | False | 70.388 | 74.372 | 47.430 | 49.388 | 40.519 | 39.844 | - | - | - |  |  | 0.048 | 0.071 | 7.507 | -2.511 | 0.040 | 7.282 | -2.636 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | other_inactive | 659 | 311 | False | False | 58.841 | 65.892 | 34.631 | 40.076 | 35.313 | 36.493 | - | - | - |  |  | 0.079 | 0.070 | -12.647 | 6.236 | -0.100 | -7.309 | 3.475 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | retired | 2234 | 1997 | False | False | 54.044 | 57.921 | 31.290 | 32.834 | 34.744 | 34.013 | - | - | - |  |  | 0.115 | 0.158 | -18.170 | 6.950 | -0.088 | -19.546 | 7.741 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | unemployed | 338 | 280 | False | False | 59.874 | 71.197 | 37.871 | 43.952 | 37.951 | 37.040 | - | - | - |  |  | 0.065 | 0.045 | -7.158 | 1.781 | -0.101 | -1.092 | 2.563 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q1 | 1046 | 661 | False | False | 54.703 | 62.582 | 33.403 | 36.106 | 36.642 | 34.616 | - | - | - |  |  | 0.112 | 0.076 | -14.366 | 3.806 | -0.089 | -14.020 | 6.876 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q2 | 1402 | 1080 | False | False | 61.019 | 62.079 | 38.949 | 38.464 | 38.345 | 37.176 | - | - | - |  |  | 0.040 | 0.054 | -5.454 | 1.146 | -0.025 | -9.800 | 2.153 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q3 | 1857 | 1241 | False | False | 62.693 | 73.583 | 40.129 | 51.735 | 38.406 | 42.185 | - | - | - |  |  | 0.036 | 0.029 | -3.615 | 1.060 | -0.103 | 10.569 | -6.712 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q4 | 2039 | 1427 | False | False | 67.953 | 71.480 | 45.920 | 44.947 | 40.622 | 37.729 | - | - | - |  |  | 0.040 | 0.035 | 5.219 | -2.635 | 0.018 | 0.487 | 1.267 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q5 | 2702 | 1490 | False | False | 74.057 | 73.911 | 48.628 | 46.888 | 39.533 | 38.063 | - | - | - |  |  | 0.094 | 0.061 | 9.440 | -0.861 | 0.126 | 3.529 | 0.656 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 0 | 65 | 61 | True | True | 84.911 | 63.796 | 72.607 | 34.937 | 51.306 | 32.858 | - | - | - |  |  | 0.262 | 0.152 | 40.077 | -20.397 | -0.121 | -16.349 | 10.419 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 1 | 3580 | 2653 | False | False | 62.790 | 66.626 | 37.622 | 38.895 | 35.955 | 35.027 | - | - | - |  |  | 0.055 | 0.035 | -7.752 | 5.285 | -0.094 | -9.388 | 6.288 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 2+ | 5401 | 3178 | False | False | 66.670 | 71.806 | 45.045 | 48.436 | 40.641 | 40.472 | - | - | - |  |  | 0.035 | 0.025 | 3.900 | -2.640 | 0.059 | 5.778 | -3.697 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | unknown | 0 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple | 3054 | 2037 | False | False | 61.406 | 63.564 | 38.605 | 39.947 | 37.724 | 37.707 | - | - | - |  |  | 0.052 | 0.080 | -6.032 | 2.183 | -0.097 | -7.395 | 1.233 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple_with_children | 3389 | 1687 | False | False | 69.316 | 75.408 | 46.259 | 50.126 | 40.131 | 39.884 | - | - | - |  |  | 0.045 | 0.068 | 5.767 | -1.844 | 0.041 | 8.410 | -2.727 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | other | 182 | 91 | False | True | 58.781 | 74.914 | 36.063 | 50.099 | 37.098 | 40.125 | - | - | - |  |  | 0.099 | 0.104 | -10.128 | 3.175 | 0.382 | 8.343 | -3.154 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_parent | 560 | 360 | False | False | 59.590 | 67.740 | 36.260 | 39.904 | 36.617 | 35.345 | - | - | - |  |  | 0.059 | 0.034 | -9.855 | 4.011 | 0.083 | -7.706 | 5.720 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_person | 1861 | 1724 | False | False | 63.349 | 65.631 | 41.062 | 39.874 | 38.904 | 36.453 | - | - | - |  |  | 0.042 | 0.055 | -2.156 | 0.236 | -0.083 | -7.636 | 3.541 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | other | 4232 | 3222 | False | False | 58.101 | 63.011 | 36.070 | 38.269 | 37.359 | 36.440 | - | - | - |  |  | 0.092 | 0.109 | -10.057 | 2.725 | 0.081 | -10.210 | 3.495 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | work_study | 4814 | 2677 | False | False | 70.831 | 75.444 | 47.290 | 50.063 | 40.091 | 39.815 | - | - | - |  |  | 0.069 | 0.092 | 7.330 | -1.796 | -0.055 | 8.321 | -2.602 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | dense | 230 | 191 | False | False | 49.173 | 60.165 | 29.819 | 36.419 | 36.807 | 36.319 | - | - | - |  |  | 0.076 | 0.138 | 1.289 | 2.702 | 0.247 | 7.240 | 1.695 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | intermediate | 889 | 842 | False | False | 42.026 | 50.344 | 23.412 | 27.790 | 33.695 | 33.120 | - | - | - |  |  | 0.035 | 0.037 | -9.323 | 6.336 | 0.077 | -7.117 | 6.231 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | sparse | 318 | 310 | False | False | 44.558 | 46.756 | 30.818 | 31.166 | 41.702 | 39.994 | - | - | - |  |  | 0.057 | 0.066 | 2.701 | -3.016 | -0.062 | -1.248 | -3.226 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | very_sparse | 850 | 465 | False | False | 48.351 | 52.793 | 36.315 | 38.928 | 45.198 | 44.242 | - | - | - |  |  | 0.081 | 0.048 | 10.467 | -6.896 | -0.155 | 10.240 | -8.677 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | children_6_17 | 659 | 500 | False | False | 33.257 | 38.069 | 19.094 | 20.356 | 34.473 | 32.082 | - | - | - |  |  | 0.124 | 0.115 | -16.234 | 4.772 | -0.216 | -20.011 | 6.850 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | employed | 687 | 365 | False | False | 50.838 | 65.543 | 33.783 | 47.275 | 40.166 | 43.277 | - | - | - |  |  | 0.067 | 0.113 | 7.281 | -1.430 | 0.052 | 22.724 | -8.410 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | other_inactive | 267 | 190 | False | False | 55.061 | 51.738 | 32.549 | 26.887 | 35.571 | 31.180 | - | - | - |  |  | 0.139 | 0.063 | 5.731 | 4.565 | -0.170 | -8.916 | 9.424 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | retired | 578 | 660 | False | False | 57.588 | 63.141 | 41.687 | 42.310 | 44.082 | 40.205 | - | - | - |  |  | 0.146 | 0.144 | 18.486 | -6.268 | 0.435 | 15.965 | -4.054 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | unemployed | 95 | 91 | True | True | 60.652 | 62.542 | 49.705 | 44.008 | 49.595 | 42.220 | - | - | - |  |  | 0.207 | 0.104 | 28.212 | -12.616 | 0.122 | 18.118 | -6.806 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q1 | 401 | 349 | False | False | 42.470 | 51.390 | 25.242 | 28.091 | 35.750 | 32.797 | - | - | - |  |  | 0.047 | 0.046 | -6.082 | 3.783 | -0.167 | -6.638 | 6.798 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q2 | 450 | 397 | False | False | 39.621 | 51.418 | 24.433 | 33.006 | 37.000 | 38.515 | - | - | - |  |  | 0.087 | 0.036 | -7.254 | 2.205 | -0.266 | 1.636 | -1.448 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q3 | 470 | 372 | False | False | 50.652 | 50.811 | 33.508 | 32.573 | 39.732 | 38.464 | - | - | - |  |  | 0.097 | 0.038 | 6.877 | -0.908 | -0.252 | 0.952 | -1.371 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q4 | 442 | 366 | False | False | 40.532 | 48.074 | 26.615 | 29.412 | 39.606 | 36.708 | - | - | - |  |  | 0.056 | 0.026 | -3.682 | -0.677 | -0.045 | -4.141 | 0.985 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q5 | 524 | 324 | False | False | 53.101 | 55.283 | 36.537 | 37.809 | 42.250 | 41.035 | - | - | - |  |  | 0.065 | 0.048 | 11.278 | -3.935 | 0.824 | 8.928 | -4.876 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 0 | 298 | 270 | False | False | 45.171 | 56.497 | 27.200 | 34.696 | 36.163 | 36.847 | - | - | - |  |  | 0.047 | 0.078 | -2.907 | 3.384 | -0.242 | 4.402 | 0.865 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 1 | 829 | 680 | False | False | 45.968 | 50.263 | 28.321 | 29.572 | 37.123 | 35.301 | - | - | - |  |  | 0.062 | 0.029 | -1.096 | 2.222 | -0.093 | -3.958 | 2.991 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 2+ | 1160 | 855 | False | False | 44.211 | 51.183 | 29.777 | 33.273 | 40.762 | 39.005 | - | - | - |  |  | 0.043 | 0.015 | 1.159 | -1.988 | 0.105 | 2.045 | -2.092 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple | 658 | 606 | False | False | 60.177 | 63.622 | 43.225 | 43.446 | 43.721 | 40.973 | - | - | - |  |  | 0.160 | 0.144 | 20.807 | -5.985 | 0.420 | 17.545 | -5.152 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple_with_children | 978 | 631 | False | False | 39.663 | 45.464 | 24.467 | 27.745 | 37.080 | 36.616 | - | - | - |  |  | 0.057 | 0.059 | -7.198 | 2.115 | -0.189 | -6.845 | 1.079 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | other | 66 | 39 | True | True | 42.349 | - | 27.621 | - | 39.133 | - | - | - | - |  |  | 0.069 | - | -2.145 | -0.167 | -0.274 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_parent | 190 | 164 | False | False | 45.801 | 49.396 | 28.384 | 27.252 | 37.203 | 33.102 | - | - | - |  |  | 0.054 | 0.046 | -0.993 | 2.121 | -0.261 | -8.034 | 6.200 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_person | 395 | 368 | False | False | 43.760 | 53.934 | 26.568 | 31.212 | 37.045 | 34.723 | - | - | - |  |  | 0.065 | 0.049 | -3.904 | 2.262 | 0.467 | -1.262 | 3.966 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | other | 1262 | 1223 | False | False | 54.887 | 62.555 | 38.690 | 42.482 | 42.606 | 40.747 | - | - | - |  |  | 0.117 | 0.110 | 14.320 | -4.420 | 0.053 | 16.119 | -4.794 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | work_study | 1025 | 585 | False | False | 36.264 | 37.579 | 20.581 | 19.300 | 34.218 | 30.815 | - | - | - |  |  | 0.102 | 0.133 | -13.888 | 5.273 | -0.056 | -22.234 | 8.583 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | dense | 93 | 54 | True | True | 77.609 | 49.569 | 34.049 | 17.783 | 30.824 | 21.525 | - | - | - |  |  | 0.124 | 0.168 | 9.589 | -2.800 | 6.286 | -81.926 | 59.058 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | intermediate | 207 | 152 | False | False | 59.688 | 72.944 | 24.370 | 81.851 | 26.826 | 67.326 | - | - | - |  |  | 0.062 | 0.064 | -12.362 | 6.174 | 1.342 | 12.183 | -11.675 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | sparse | 76 | 52 | True | True | 50.262 | 76.441 | 26.765 | 76.730 | 34.120 | 60.227 | - | - | - |  |  | 0.187 | 0.157 | -6.018 | -8.056 | -0.198 | 7.665 | -3.661 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | very_sparse | 311 | 120 | False | False | 70.940 | 79.668 | 34.355 | 71.871 | 30.025 | 54.128 | - | - | - |  |  | 0.085 | 0.066 | 9.765 | -0.896 | -2.463 | 2.856 | 4.376 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | children_6_17 | 275 | 91 | False | True | 58.796 | 66.819 | 22.637 | 53.520 | 23.464 | 48.058 | - | - | - |  |  | 0.056 | 0.074 | -16.816 | 14.378 | -3.299 | -17.901 | 12.284 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | employed | 294 | 167 | False | False | 76.194 | 80.778 | 43.296 | 94.587 | 38.647 | 70.257 | - | - | - |  |  | 0.107 | 0.052 | 26.366 | -18.650 | 3.944 | 23.895 | -15.554 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | other_inactive | 42 | 32 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | retired | 65 | 75 | True | True | 55.655 | 59.482 | 22.085 | 36.401 | 27.180 | 36.718 | - | - | - |  |  | 0.161 | 0.116 | -17.851 | 5.178 | 3.794 | -42.256 | 29.302 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | unemployed | 11 | 12 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q1 | 110 | 75 | False | True | 61.295 | 68.877 | 28.144 | 38.690 | 28.124 | 33.704 | - | - | - |  |  | 0.039 | 0.171 | -3.470 | 3.283 | -3.052 | -41.093 | 37.533 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q2 | 158 | 81 | False | True | 63.965 | 49.052 | 25.305 | 23.834 | 24.082 | 29.153 | - | - | - |  |  | 0.095 | 0.153 | -10.374 | 13.321 | -3.515 | -63.958 | 40.574 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q3 | 115 | 70 | False | True | 59.734 | 78.587 | 23.474 | 82.356 | 23.743 | 62.878 | - | - | - |  |  | 0.078 | 0.083 | -14.693 | 13.757 | -3.864 | 13.113 | -6.963 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q4 | 135 | 63 | False | True | 62.761 | 69.017 | 38.216 | 40.553 | 40.302 | 35.255 | - | - | - |  |  | 0.112 | 0.129 | 15.960 | -19.577 | 1.845 | -37.808 | 34.389 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q5 | 169 | 89 | False | True | 76.525 | 92.525 | 35.243 | 145.434 | 34.542 | 94.310 | - | - | - |  |  | 0.063 | 0.091 | 11.945 | -10.790 | 10.836 | 60.932 | -40.843 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 0 | 101 | 70 | False | True | 50.785 | 59.386 | 16.594 | 30.066 | 20.636 | 30.377 | - | - | - |  |  | 0.178 | 0.079 | -33.481 | 20.760 | -1.027 | -54.783 | 41.733 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 1 | 225 | 134 | False | False | 70.288 | 64.128 | 36.755 | 73.996 | 34.342 | 69.233 | - | - | - |  |  | 0.055 | 0.066 | 14.269 | -9.941 | 1.427 | 4.550 | -12.858 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 2+ | 361 | 174 | False | False | 63.614 | 80.957 | 27.919 | 73.291 | 27.895 | 54.319 | - | - | - |  |  | 0.032 | 0.049 | -4.047 | 3.868 | -0.740 | 4.378 | 4.142 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple | 93 | 90 | True | True | 64.830 | 67.866 | 34.918 | 65.061 | 35.488 | 57.519 | - | - | - |  |  | 0.173 | 0.052 | 10.383 | -11.668 | 1.581 | -4.346 | -0.224 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple_with_children | 382 | 142 | False | False | 65.728 | 76.320 | 28.599 | 64.261 | 27.935 | 50.519 | - | - | - |  |  | 0.062 | 0.031 | -2.547 | 3.837 | -0.095 | -5.528 | 9.413 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | other | 22 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_parent | 67 | 43 | True | True | 62.158 | - | 25.722 | - | 25.309 | - | - | - | - |  |  | 0.098 | - | -9.193 | 9.985 | -3.168 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_person | 123 | 95 | False | True | 70.616 | 86.432 | 43.431 | 166.921 | 41.695 | 115.874 | - | - | - |  |  | 0.197 | 0.114 | 25.574 | -23.067 | 3.576 | 69.739 | -55.742 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | other | 127 | 139 | False | False | 49.818 | 95.013 | 21.733 | 124.522 | 29.228 | 78.634 | - | - | - |  |  | 0.183 | 0.092 | -17.833 | 0.778 | 2.340 | 48.862 | -26.285 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | work_study | 560 | 239 | False | False | 67.460 | 64.458 | 31.332 | 49.679 | 29.687 | 46.243 | - | - | - |  |  | 0.036 | 0.032 | 3.442 | -0.125 | -0.390 | -22.679 | 14.701 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | density | dense+intermediate+sparse+very_sparse | 681 | 288 | False | False | 144.056 | 139.324 | 75.423 | 83.323 | 38.310 | 35.883 | - | - | - |  |  | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | children_6_17 | 31 | 18 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | employed | 504 | 201 | False | False | 149.511 | 143.246 | 74.643 | 94.032 | 36.441 | 39.386 | - | - | - |  |  | 0.046 | 0.037 | -1.528 | 7.342 | -0.359 | 17.082 | -13.161 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | other_inactive | 63 | 30 | True | True | 131.427 | - | 70.718 | - | 34.194 | - | - | - | - |  |  | 0.121 | - | -8.867 | 15.645 | -19.406 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | retired | 59 | 29 | True | True | 174.885 | - | 56.043 | - | 31.533 | - | - | - | - |  |  | 0.123 | - | -47.213 | 30.948 | 47.094 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | unemployed | 24 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q1+q2+q3 | 238 | 128 | False | False | 136.028 | 134.578 | 63.239 | 65.998 | 34.829 | 29.424 | - | - | - |  |  | 0.052 | 0.074 | -24.667 | 13.340 | 3.300 | -31.921 | 27.175 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q4 | 138 | 51 | False | True | 150.230 | 141.512 | 94.094 | 72.106 | 44.332 | 30.572 | - | - | - |  |  | 0.114 | 0.132 | 32.540 | -21.476 | -4.889 | -20.302 | 22.490 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q5 | 305 | 109 | False | False | 149.474 | 145.710 | 78.567 | 116.445 | 38.282 | 47.949 | - | - | - |  |  | 0.049 | 0.087 | 5.993 | 0.108 | -0.683 | 47.692 | -41.305 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 0 | 206 | 87 | False | True | 112.198 | 141.076 | 37.049 | 73.424 | 21.135 | 31.227 | - | - | - |  |  | 0.184 | 0.092 | -90.612 | 75.815 | -17.060 | -17.732 | 19.484 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 1 | 295 | 118 | False | False | 147.067 | 139.747 | 92.777 | 86.604 | 44.559 | 37.183 | - | - | - |  |  | 0.060 | 0.067 | 30.141 | -21.993 | -5.137 | 5.390 | -4.966 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 2+ | 180 | 80 | False | True | 162.163 | 129.695 | 75.579 | 84.364 | 38.864 | 39.029 | - | - | - |  |  | 0.078 | 0.085 | 0.316 | -2.193 | 19.984 | 1.670 | -11.299 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple | 147 | 56 | False | True | 151.787 | 157.394 | 78.569 | 128.268 | 36.642 | 48.897 | - | - | - |  |  | 0.094 | 0.099 | 6.043 | 6.584 | -4.895 | 63.923 | -45.853 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple_with_children | 232 | 92 | False | True | 138.766 | 121.674 | 74.891 | 64.237 | 41.753 | 31.677 | - | - | - |  |  | 0.049 | 0.090 | -1.001 | -12.166 | 7.878 | -33.897 | 16.247 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | other | 19 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_parent | 70 | 35 | True | True | 145.216 | - | 75.386 | - | 34.816 | - | - | - | - |  |  | 0.105 | - | -0.071 | 13.835 | -12.603 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_person | 213 | 96 | False | True | 152.425 | 157.275 | 77.801 | 115.754 | 37.240 | 44.160 | - | - | - |  |  | 0.056 | 0.135 | 4.600 | 4.202 | -0.432 | 48.694 | -30.742 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | other | 136 | 64 | False | True | 149.987 | 157.207 | 87.414 | 103.272 | 46.778 | 39.415 | - | - | - |  |  | 0.101 | 0.152 | 21.688 | -29.354 | 13.597 | 31.785 | -13.902 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | work_study | 545 | 224 | False | False | 142.797 | 135.974 | 72.880 | 79.586 | 36.624 | 35.118 | - | - | - |  |  | 0.021 | 0.029 | -4.920 | 6.457 | -2.796 | -6.316 | 2.966 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | dense | 730 | 381 | False | False | 72.555 | 74.066 | 14.622 | 10.726 | 12.092 | 8.689 | - | - | - |  |  | 0.031 | 0.045 | -20.706 | 19.179 | 0.000 | -28.558 | 24.480 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | intermediate | 667 | 503 | False | False | 74.697 | 79.719 | 18.829 | 16.817 | 15.125 | 12.657 | - | - | - |  |  | 0.024 | 0.041 | -2.198 | 2.813 | 0.000 | 5.876 | -4.301 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | sparse+very_sparse | 110 | 99 | False | True | 77.644 | 83.622 | 44.053 | 24.754 | 34.043 | 17.761 | - | - | - |  |  | 0.142 | 0.094 | 62.230 | -58.668 | 0.000 | 37.275 | -31.797 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | children_6_17 | 146 | 185 | False | False | 69.989 | 70.556 | 24.169 | 18.289 | 20.720 | 15.553 | - | - | - |  |  | 0.131 | 0.103 | 15.853 | -19.946 | 0.000 | 11.762 | -19.350 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | employed | 764 | 371 | False | False | 73.959 | 77.179 | 15.534 | 15.846 | 12.602 | 12.319 | - | - | - |  |  | 0.044 | 0.039 | -16.429 | 16.306 | 0.000 | 1.163 | -2.128 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | other_inactive | 243 | 155 | False | False | 76.213 | 91.132 | 18.562 | 13.471 | 14.613 | 8.869 | - | - | - |  |  | 0.104 | 0.091 | -3.294 | 5.426 | 0.000 | -12.452 | 25.440 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | retired | 275 | 184 | False | False | 75.668 | 75.806 | 29.641 | 12.900 | 23.503 | 10.210 | - | - | - |  |  | 0.080 | 0.077 | 31.761 | -30.175 | 0.000 | -14.680 | 12.342 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | unemployed | 79 | 86 | True | True | 80.631 | 82.933 | 14.692 | 13.716 | 10.933 | 9.923 | - | - | - |  |  | 0.106 | 0.116 | -21.463 | 28.013 | 0.000 | -10.418 | 15.208 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q1 | 314 | 301 | False | False | 80.260 | 78.647 | 23.398 | 13.411 | 17.492 | 10.231 | - | - | - |  |  | 0.071 | 0.047 | 14.478 | -8.299 | 0.000 | -11.909 | 12.413 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q2 | 243 | 173 | False | False | 76.210 | 92.092 | 18.522 | 17.064 | 14.582 | 11.118 | - | - | - |  |  | 0.065 | 0.097 | -3.458 | 5.587 | 0.000 | 7.560 | 6.388 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q3 | 250 | 164 | False | False | 78.476 | 78.679 | 17.247 | 19.420 | 13.187 | 14.809 | - | - | - |  |  | 0.095 | 0.045 | -8.946 | 13.340 | 0.000 | 17.119 | -16.584 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q4 | 276 | 144 | False | False | 67.123 | 68.178 | 19.539 | 15.026 | 17.466 | 13.223 | - | - | - |  |  | 0.090 | 0.076 | 0.527 | -7.485 | 0.000 | -2.791 | -7.175 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q5 | 424 | 201 | False | False | 66.590 | 71.830 | 16.296 | 14.466 | 14.684 | 12.084 | - | - | - |  |  | 0.083 | 0.051 | -12.228 | 4.736 | 0.000 | -5.706 | -0.608 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 0 | 752 | 487 | False | False | 79.045 | 79.696 | 17.621 | 12.386 | 13.375 | 9.325 | - | - | - |  |  | 0.089 | 0.066 | -7.338 | 12.301 | 0.000 | -18.261 | 19.813 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 1 | 500 | 302 | False | False | 71.572 | 75.110 | 18.955 | 14.141 | 15.891 | 11.296 | - | - | - |  |  | 0.049 | 0.083 | -1.666 | -0.844 | 0.000 | -7.578 | 4.544 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 2+ | 255 | 188 | False | False | 69.303 | 79.400 | 23.286 | 22.240 | 20.160 | 16.806 | - | - | - |  |  | 0.110 | 0.058 | 13.106 | -17.885 | 0.000 | 27.881 | -26.625 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | unknown | 0 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple | 277 | 136 | False | False | 71.191 | 72.139 | 20.627 | 14.152 | 17.385 | 11.771 | - | - | - |  |  | 0.045 | 0.091 | 4.479 | -7.369 | 0.000 | -7.367 | 1.362 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple_with_children | 386 | 281 | False | False | 75.193 | 81.428 | 19.676 | 18.962 | 15.700 | 13.972 | - | - | - |  |  | 0.035 | 0.029 | 1.078 | 0.033 | 0.000 | 15.516 | -12.232 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | other | 38 | 40 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_parent | 160 | 139 | False | False | 75.876 | 68.989 | 22.005 | 12.596 | 17.401 | 10.955 | - | - | - |  |  | 0.067 | 0.123 | 9.471 | -7.677 | 0.000 | -15.764 | 6.610 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_person | 646 | 387 | False | False | 74.292 | 77.737 | 18.168 | 13.095 | 14.673 | 10.107 | - | - | - |  |  | 0.069 | 0.027 | -4.844 | 5.054 | 0.000 | -13.695 | 13.288 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | other | 559 | 437 | False | False | 72.100 | 82.945 | 22.881 | 14.829 | 19.041 | 10.727 | - | - | - |  |  | 0.109 | 0.032 | 12.084 | -14.065 | 0.000 | -4.137 | 8.938 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | work_study | 948 | 546 | False | False | 75.031 | 75.737 | 17.723 | 16.003 | 14.172 | 12.677 | - | - | - |  |  | 0.052 | 0.016 | -6.718 | 7.667 | 0.000 | 1.907 | -4.314 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | dense | 1012 | 630 | False | False | 33.966 | 37.458 | 2.093 | 2.105 | 3.725 | 3.372 | - | - | - |  |  | 0.084 | 0.133 | 3.944 | -0.612 | 0.180 | 5.569 | 0.393 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | intermediate | 1784 | 1322 | False | False | 31.570 | 31.577 | 1.920 | 1.795 | 3.650 | 3.410 | - | - | - |  |  | 0.032 | 0.017 | 1.135 | 0.048 | -0.065 | 0.077 | 0.004 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | sparse | 429 | 304 | False | False | 27.630 | 28.759 | 1.672 | 1.676 | 3.630 | 3.497 | - | - | - |  |  | 0.060 | 0.106 | -2.962 | 0.199 | -0.061 | -1.985 | -0.752 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | very_sparse | 625 | 287 | False | False | 21.839 | 20.012 | 1.274 | 1.143 | 3.500 | 3.428 | - | - | - |  |  | 0.177 | 0.230 | -9.682 | 1.122 | -0.054 | -11.352 | -0.131 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | children_6_17 | 481 | 366 | False | False | 29.237 | 28.520 | 1.768 | 1.532 | 3.629 | 3.223 | - | - | - |  |  | 0.026 | 0.057 | -1.369 | 0.216 | -0.063 | -4.676 | 1.700 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | employed | 1457 | 832 | False | False | 27.970 | 28.102 | 1.782 | 1.736 | 3.849 | 3.706 | - | - | - |  |  | 0.077 | 0.067 | -1.108 | -1.509 | 0.133 | -0.924 | -2.469 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | other_inactive | 501 | 284 | False | False | 33.135 | 38.669 | 2.139 | 2.215 | 3.873 | 3.437 | - | - | - |  |  | 0.069 | 0.156 | 4.587 | -1.838 | -0.067 | 7.444 | -0.270 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | retired | 1177 | 888 | False | False | 32.359 | 34.647 | 1.754 | 1.868 | 3.253 | 3.234 | - | - | - |  |  | 0.085 | 0.068 | -1.690 | 3.661 | -0.066 | 1.396 | 1.756 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | unemployed | 234 | 171 | False | False | 38.206 | 40.286 | 2.396 | 2.246 | 3.763 | 3.344 | - | - | - |  |  | 0.143 | 0.095 | 8.813 | -0.988 | -0.072 | 8.090 | 0.700 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q1 | 874 | 624 | False | False | 35.512 | 34.964 | 2.142 | 1.974 | 3.644 | 3.387 | - | - | - |  |  | 0.080 | 0.083 | 4.804 | 0.104 | 0.150 | 3.234 | 0.234 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q2 | 669 | 480 | False | False | 28.532 | 32.398 | 1.754 | 1.842 | 3.689 | 3.411 | - | - | - |  |  | 0.029 | 0.045 | -1.591 | -0.268 | -0.062 | 0.905 | -0.002 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q3 | 677 | 415 | False | False | 27.793 | 27.962 | 1.656 | 1.600 | 3.575 | 3.434 | - | - | - |  |  | 0.063 | 0.071 | -3.245 | 0.645 | -0.061 | -3.332 | -0.201 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q4 | 672 | 478 | False | False | 29.110 | 30.558 | 1.798 | 1.771 | 3.706 | 3.478 | - | - | - |  |  | 0.073 | 0.051 | -0.874 | -0.407 | -0.063 | -0.335 | -0.603 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q5 | 958 | 546 | False | False | 28.803 | 29.906 | 1.757 | 1.679 | 3.661 | 3.368 | - | - | - |  |  | 0.060 | 0.051 | -1.542 | -0.046 | -0.062 | -1.972 | 0.383 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 0 | 1224 | 803 | False | False | 37.018 | 37.718 | 2.261 | 2.052 | 3.665 | 3.264 | - | - | - |  |  | 0.148 | 0.108 | 6.723 | -0.088 | -0.071 | 4.702 | 1.520 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 1 | 1623 | 1052 | False | False | 29.440 | 32.572 | 1.790 | 1.848 | 3.648 | 3.403 | - | - | - |  |  | 0.027 | 0.023 | -1.008 | 0.058 | -0.063 | 1.009 | 0.068 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 2+ | 1003 | 680 | False | False | 26.701 | 24.838 | 1.614 | 1.491 | 3.656 | 3.601 | - | - | - |  |  | 0.083 | 0.107 | -3.912 | -0.009 | 0.167 | -5.133 | -1.525 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | unknown | 0 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple | 893 | 591 | False | False | 30.674 | 31.341 | 1.790 | 1.832 | 3.501 | 3.507 | - | - | - |  |  | 0.017 | 0.031 | -1.035 | 1.320 | -0.064 | 0.724 | -0.878 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple_with_children | 1134 | 706 | False | False | 29.047 | 28.386 | 1.796 | 1.651 | 3.728 | 3.490 | - | - | - |  |  | 0.044 | 0.044 | -0.905 | -0.585 | 0.083 | -2.417 | -0.692 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | other | 87 | 48 | True | True | 29.109 | - | 1.868 | - | 3.850 | - | - | - | - |  |  | 0.080 | - | 0.263 | -1.545 | -0.063 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_parent | 362 | 251 | False | False | 31.736 | 31.938 | 1.926 | 1.746 | 3.642 | 3.280 | - | - | - |  |  | 0.047 | 0.044 | 1.230 | 0.117 | -0.065 | -0.797 | 1.240 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_person | 1374 | 947 | False | False | 32.891 | 37.921 | 1.993 | 2.070 | 3.636 | 3.276 | - | - | - |  |  | 0.068 | 0.104 | 2.340 | 0.164 | -0.067 | 5.031 | 1.395 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | other | 2263 | 1589 | False | False | 30.886 | 35.094 | 1.828 | 1.931 | 3.550 | 3.301 | - | - | - |  |  | 0.018 | 0.058 | -0.397 | 0.894 | -0.065 | 2.513 | 1.086 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | work_study | 1587 | 953 | False | False | 29.977 | 27.819 | 1.878 | 1.646 | 3.775 | 3.550 | - | - | - |  |  | 0.020 | 0.059 | 0.424 | -0.973 | 0.072 | -2.488 | -1.189 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Mode-user composition

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 428 | 268 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | 9046 | 5895 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | 2286 | 1806 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | 687 | 377 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | 681 | 287 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | 1507 | 981 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | 3850 | 2541 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Per-mode decomposition

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Duration-rounding bounds

Scope: All days · destination purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-dest-daytable`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

## All days · all purposes · local (≤ 80 km)

### Subgroup mode-user days

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 90 | 65 | True | True | 43.384 | 46.484 | 7.983 | 7.890 | 11.041 | 10.184 | 1.071 | 0.787 | 1.388 | inconclusive | inconclusive | 0.059 | 0.108 | 4.154 | -3.859 | 0.000 | -4.813 | 1.218 | 0.000 |  |
| bike | density | intermediate | 192 | 137 | False | False | 41.795 | 46.227 | 7.214 | 9.352 | 10.356 | 12.139 | 1.106 | 0.925 | 1.303 | inconclusive | inconclusive | 0.073 | 0.074 | -0.225 | -1.069 | 0.000 | 3.386 | -7.238 | 0.000 |  |
| bike | density | sparse | 88 | 54 | True | True | 45.153 | 44.740 | 7.432 | 7.010 | 9.875 | 9.401 | 0.991 | 0.688 | 1.493 | inconclusive | inconclusive | 0.096 | 0.129 | 1.081 | 0.983 | 0.000 | -10.320 | 4.980 | 0.000 |  |
| bike | density | very_sparse | 150 | 50 | False | True | 43.374 | 77.669 | 6.353 | 10.595 | 8.788 | 8.185 | 1.791 | 1.036 | 2.510 | inconclusive | inconclusive | 0.163 | 0.207 | -5.724 | 6.009 | 0.000 | 12.266 | 15.324 | 0.000 |  |
| bike | population | children_6_17 | 96 | 40 | True | True | 29.569 | - | 4.761 | - | 9.660 | - | - | - | - |  |  | 0.203 | - | -15.111 | 1.591 | 0.000 | - | - | - |  |
| bike | population | employed | 213 | 143 | False | False | 51.383 | 45.657 | 8.753 | 9.201 | 10.221 | 12.092 | 0.889 | 0.745 | 1.066 | inconclusive | inconclusive | 0.134 | 0.058 | 8.867 | -0.573 | 0.000 | 2.587 | -7.010 | 0.000 |  |
| bike | population | other_inactive | 40 | 19 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | population | retired | 150 | 84 | False | True | 53.277 | 49.073 | 8.432 | 8.957 | 9.496 | 10.951 | 0.921 | 0.727 | 1.167 | inconclusive | inconclusive | 0.106 | 0.048 | 7.237 | 2.951 | 0.000 | 1.346 | -2.352 | 0.000 |  |
| bike | population | unemployed | 21 | 20 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | income | q1 | 99 | 51 | True | True | 49.475 | 55.956 | 8.323 | 7.810 | 10.093 | 8.374 | 1.131 | 0.720 | 1.725 | inconclusive | inconclusive | 0.185 | 0.100 | 6.365 | 0.021 | 0.000 | -5.821 | 11.698 | 0.000 |  |
| bike | income | q2 | 95 | 58 | True | True | 40.823 | 56.446 | 6.341 | 8.545 | 9.319 | 9.083 | 1.383 | 0.977 | 1.977 | inconclusive | inconclusive | 0.074 | 0.141 | -5.632 | 3.366 | 0.000 | -1.059 | 7.426 | 0.000 |  |
| bike | income | q3 | 98 | 63 | True | True | 41.084 | 51.034 | 6.675 | 9.566 | 9.748 | 11.246 | 1.242 | 0.967 | 1.575 | inconclusive | inconclusive | 0.079 | 0.115 | -3.490 | 1.485 | 0.000 | 4.697 | -3.743 | 0.000 |  |
| bike | income | q4 | 95 | 54 | True | True | 39.733 | 37.666 | 7.703 | 7.764 | 11.632 | 12.369 | 0.948 | 0.676 | 1.313 | inconclusive | inconclusive | 0.112 | 0.143 | 2.497 | -5.854 | 0.000 | -5.043 | -7.371 | 0.000 |  |
| bike | income | q5 | 133 | 80 | False | True | 44.264 | 50.907 | 7.153 | 9.893 | 9.695 | 11.660 | 1.150 | 0.923 | 1.486 | inconclusive | inconclusive | 0.065 | 0.099 | -0.602 | 1.777 | 0.000 | 6.388 | -5.560 | 0.000 |  |
| bike | vehicles | 0 | 107 | 61 | False | True | 40.486 | 52.377 | 7.428 | 8.266 | 11.009 | 9.469 | 1.294 | 0.978 | 1.751 | inconclusive | inconclusive | 0.079 | 0.127 | 1.005 | -3.609 | 0.000 | -2.719 | 5.018 | 0.000 |  |
| bike | vehicles | 1 | 197 | 123 | False | False | 49.581 | 48.485 | 8.397 | 9.392 | 10.161 | 11.622 | 0.978 | 0.803 | 1.233 | inconclusive | inconclusive | 0.127 | 0.060 | 6.782 | -0.290 | 0.000 | 3.673 | -5.268 | 0.000 |  |
| bike | vehicles | 2+ | 216 | 119 | False | False | 38.873 | 50.554 | 6.236 | 8.384 | 9.626 | 9.951 | 1.301 | 0.977 | 1.668 | inconclusive | inconclusive | 0.120 | 0.095 | -6.177 | 1.960 | 0.000 | -1.959 | 2.434 | 0.000 |  |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | couple | 158 | 91 | False | True | 49.418 | 43.978 | 7.894 | 8.275 | 9.584 | 11.290 | 0.890 | 0.709 | 1.116 | inconclusive | inconclusive | 0.091 | 0.046 | 3.916 | 2.412 | 0.000 | -2.444 | -3.658 | 0.000 |  |
| bike | household_type | couple_with_children | 179 | 90 | False | True | 40.268 | 50.921 | 6.840 | 8.708 | 10.192 | 10.261 | 1.265 | 0.955 | 1.600 | inconclusive | inconclusive | 0.060 | 0.059 | -2.437 | -0.385 | 0.000 | -0.050 | 0.891 | 0.000 |  |
| bike | household_type | other | 13 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_parent | 39 | 31 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| bike | household_type | single_person | 131 | 88 | False | True | 48.077 | 49.917 | 8.748 | 9.256 | 10.918 | 11.126 | 1.038 | 0.886 | 1.295 | inconclusive | inconclusive | 0.243 | 0.082 | 8.543 | -3.556 | 0.000 | 3.001 | -3.164 | 0.000 |  |
| bike | day_purpose | other | 289 | 161 | False | False | 43.420 | 57.775 | 6.862 | 9.290 | 9.483 | 9.648 | 1.331 | 1.050 | 1.637 | inconclusive | inconclusive | 0.046 | 0.073 | -2.387 | 2.717 | 0.000 | 3.428 | 4.268 | 0.000 |  |
| bike | day_purpose | work_study | 231 | 145 | False | False | 42.658 | 41.784 | 7.761 | 8.099 | 10.916 | 11.630 | 0.980 | 0.823 | 1.160 | inconclusive | inconclusive | 0.060 | 0.079 | 2.908 | -3.339 | 0.000 | -3.367 | -4.928 | 0.000 |  |
| car_driver | density | dense | 692 | 457 | False | False | 62.322 | 69.102 | 29.146 | 29.044 | 28.060 | 25.219 | 1.109 | 1.015 | 1.196 | inconclusive | inconclusive | 0.053 | 0.065 | -16.053 | 16.307 | -0.030 | -21.553 | 23.148 | 0.000 |  |
| car_driver | density | intermediate | 3350 | 2513 | False | False | 62.567 | 67.592 | 33.062 | 35.021 | 31.707 | 31.088 | 1.080 | 1.039 | 1.130 | equivalent | inconclusive | 0.017 | 0.014 | -8.226 | 8.722 | -0.028 | -8.675 | 8.760 | 0.000 |  |
| car_driver | density | sparse | 1302 | 1044 | False | False | 60.286 | 64.302 | 39.381 | 42.272 | 39.194 | 39.443 | 1.067 | 0.969 | 1.152 | inconclusive | inconclusive | 0.054 | 0.041 | 2.627 | -4.410 | -0.030 | 3.936 | -7.141 | 0.000 |  |
| car_driver | density | very_sparse | 3582 | 1791 | False | False | 62.540 | 69.373 | 45.663 | 49.050 | 43.877 | 42.423 | 1.109 | 1.051 | 1.171 | inconclusive | inconclusive | 0.022 | 0.026 | 11.899 | -11.524 | 0.067 | 14.267 | -12.401 | 0.000 |  |
| car_driver | population | children_6_17 | 81 | 46 | True | True | 43.738 | - | 25.166 | - | 34.523 | - | - | - | - |  |  | 0.217 | - | -21.207 | 2.872 | -0.026 | - | - | - |  |
| car_driver | population | employed | 5612 | 3197 | False | False | 66.478 | 73.784 | 41.684 | 45.464 | 37.648 | 36.970 | 1.110 | 1.073 | 1.150 | inconclusive | inconclusive | 0.048 | 0.077 | 6.412 | -2.046 | 0.013 | 9.357 | -3.080 | 0.000 |  |
| car_driver | population | other_inactive | 658 | 308 | False | False | 55.357 | 63.339 | 30.690 | 36.981 | 33.264 | 35.031 | 1.144 | 1.019 | 1.305 | inconclusive | inconclusive | 0.084 | 0.080 | -12.108 | 5.396 | -0.029 | -4.838 | 0.671 | 0.000 |  |
| car_driver | population | retired | 2243 | 1975 | False | False | 52.887 | 53.697 | 29.189 | 27.498 | 33.115 | 30.726 | 1.015 | 0.963 | 1.068 | equivalent | equivalent | 0.108 | 0.168 | -14.719 | 5.535 | -0.028 | -22.341 | 8.531 | 0.000 |  |
| car_driver | population | unemployed | 332 | 275 | False | False | 57.945 | 64.452 | 35.058 | 33.987 | 36.301 | 31.640 | 1.112 | 0.968 | 1.256 | inconclusive | inconclusive | 0.055 | 0.064 | -4.401 | 0.277 | -0.029 | -10.448 | 7.394 | 0.000 |  |
| car_driver | income | q1 | 1050 | 649 | False | False | 53.135 | 61.562 | 31.128 | 33.993 | 35.150 | 33.131 | 1.159 | 1.063 | 1.261 | inconclusive | inconclusive | 0.109 | 0.072 | -11.054 | 2.118 | -0.028 | -10.203 | 4.257 | 0.000 |  |
| car_driver | income | q2 | 1401 | 1075 | False | False | 58.613 | 61.182 | 34.910 | 35.972 | 35.751 | 35.277 | 1.044 | 0.977 | 1.111 | equivalent | inconclusive | 0.038 | 0.057 | -4.680 | 1.199 | -0.004 | -6.534 | 0.209 | 0.000 |  |
| car_driver | income | q3 | 1842 | 1226 | False | False | 60.927 | 65.962 | 36.388 | 40.170 | 35.835 | 36.539 | 1.083 | 0.999 | 1.153 | inconclusive | inconclusive | 0.025 | 0.032 | -2.220 | 1.078 | -0.030 | 0.583 | -2.128 | 0.000 |  |
| car_driver | income | q4 | 2001 | 1406 | False | False | 64.488 | 70.292 | 41.064 | 41.774 | 38.269 | 35.657 | 1.090 | 1.035 | 1.158 | inconclusive | inconclusive | 0.039 | 0.032 | 5.365 | -3.049 | 0.074 | 3.299 | -0.514 | 0.000 |  |
| car_driver | income | q5 | 2632 | 1449 | False | False | 68.377 | 74.033 | 41.466 | 43.448 | 36.389 | 35.213 | 1.083 | 1.028 | 1.146 | equivalent | inconclusive | 0.081 | 0.070 | 6.163 | 0.142 | -0.026 | 6.166 | 0.360 | 0.000 |  |
| car_driver | vehicles | 0 | 63 | 60 | True | True | 64.954 | 65.523 | 39.520 | 34.328 | 36.506 | 31.434 | 1.009 | 0.695 | 1.442 | inconclusive | inconclusive | 0.154 | 0.180 | 2.951 | -0.064 | -0.031 | -9.872 | 7.888 | 0.000 |  |
| car_driver | vehicles | 1 | 3522 | 2610 | False | False | 60.395 | 64.389 | 33.808 | 34.071 | 33.587 | 31.748 | 1.066 | 1.018 | 1.123 | equivalent | inconclusive | 0.050 | 0.037 | -6.715 | 5.041 | -0.030 | -10.282 | 7.164 | 0.000 |  |
| car_driver | vehicles | 2+ | 5341 | 3126 | False | False | 63.120 | 69.529 | 40.134 | 43.549 | 38.180 | 37.580 | 1.102 | 1.063 | 1.145 | equivalent | inconclusive | 0.032 | 0.026 | 3.874 | -2.871 | 0.019 | 6.132 | -4.110 | 0.000 |  |
| car_driver | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_driver | household_type | couple | 3029 | 2001 | False | False | 59.605 | 60.598 | 35.574 | 34.787 | 35.813 | 34.443 | 1.017 | 0.959 | 1.068 | equivalent | equivalent | 0.051 | 0.083 | -3.574 | 1.105 | -0.025 | -8.648 | 1.739 | 0.000 |  |
| car_driver | household_type | couple_with_children | 3337 | 1664 | False | False | 65.143 | 73.958 | 40.399 | 45.703 | 37.216 | 37.078 | 1.135 | 1.091 | 1.183 | inconclusive | inconclusive | 0.044 | 0.071 | 4.354 | -1.290 | -0.020 | 9.740 | -3.289 | 0.000 |  |
| car_driver | household_type | other | 181 | 89 | False | True | 57.804 | 59.763 | 35.089 | 32.313 | 36.908 | 32.441 | 1.034 | 0.872 | 1.244 | inconclusive | inconclusive | 0.090 | 0.112 | -4.343 | -0.718 | 0.766 | -13.277 | 5.533 | 0.000 |  |
| car_driver | household_type | single_parent | 556 | 360 | False | False | 58.083 | 69.092 | 34.079 | 39.338 | 35.204 | 34.162 | 1.190 | 1.053 | 1.339 | inconclusive | inconclusive | 0.063 | 0.037 | -6.106 | 2.120 | -0.029 | -0.832 | 2.417 | 0.000 |  |
| car_driver | household_type | single_person | 1823 | 1691 | False | False | 59.133 | 62.542 | 34.836 | 34.147 | 35.347 | 32.759 | 1.058 | 1.007 | 1.123 | equivalent | inconclusive | 0.048 | 0.060 | -4.830 | 1.894 | -0.030 | -9.990 | 5.025 | 0.000 |  |
| car_driver | day_purpose | other | 4247 | 3163 | False | False | 54.187 | 57.086 | 31.495 | 31.441 | 34.873 | 33.046 | 1.054 | 1.008 | 1.104 | equivalent | inconclusive | 0.097 | 0.126 | -10.480 | 2.597 | -0.028 | -14.683 | 4.262 | 0.000 |  |
| car_driver | day_purpose | work_study | 4679 | 2642 | False | False | 68.372 | 76.273 | 42.667 | 46.869 | 37.472 | 36.869 | 1.116 | 1.078 | 1.162 | inconclusive | inconclusive | 0.077 | 0.106 | 8.023 | -1.770 | 0.020 | 11.701 | -2.935 | 0.000 |  |
| car_passenger | density | dense | 215 | 175 | False | False | 42.335 | 48.684 | 20.825 | 20.330 | 29.515 | 25.055 | 1.150 | 0.927 | 1.431 | inconclusive | inconclusive | 0.058 | 0.115 | -6.995 | 7.902 | -0.008 | -10.450 | 13.329 | 0.000 |  |
| car_passenger | density | intermediate | 860 | 811 | False | False | 38.833 | 44.766 | 19.799 | 21.708 | 30.591 | 29.095 | 1.153 | 1.039 | 1.250 | inconclusive | inconclusive | 0.037 | 0.036 | -8.728 | 6.132 | -0.008 | -7.048 | 6.009 | 0.000 |  |
| car_passenger | density | sparse | 311 | 299 | False | False | 43.107 | 43.804 | 28.052 | 27.411 | 39.082 | 37.545 | 1.016 | 0.878 | 1.207 | inconclusive | inconclusive | 0.054 | 0.050 | 5.531 | -3.893 | 0.032 | 3.476 | -5.476 | 0.000 |  |
| car_passenger | density | very_sparse | 822 | 443 | False | False | 44.092 | 48.370 | 31.062 | 32.841 | 42.269 | 40.737 | 1.097 | 0.994 | 1.213 | inconclusive | inconclusive | 0.071 | 0.048 | 9.953 | -7.289 | -0.008 | 12.161 | -9.596 | 0.000 |  |
| car_passenger | population | children_6_17 | 651 | 492 | False | False | 31.929 | 36.938 | 17.273 | 18.859 | 32.459 | 30.633 | 1.157 | 1.059 | 1.256 | inconclusive | inconclusive | 0.122 | 0.112 | -12.913 | 3.413 | -0.007 | -12.214 | 3.347 | 0.000 |  |
| car_passenger | population | employed | 637 | 334 | False | False | 46.070 | 52.540 | 27.345 | 32.306 | 35.637 | 36.893 | 1.140 | 1.014 | 1.282 | inconclusive | inconclusive | 0.071 | 0.085 | 4.606 | 0.008 | 0.020 | 11.877 | -5.143 | 0.000 |  |
| car_passenger | population | other_inactive | 261 | 186 | False | False | 51.330 | 50.095 | 28.651 | 25.145 | 33.491 | 30.117 | 0.976 | 0.791 | 1.219 | inconclusive | inconclusive | 0.141 | 0.069 | 7.024 | 2.878 | -0.009 | -0.416 | 4.705 | 0.000 |  |
| car_passenger | population | retired | 569 | 634 | False | False | 52.763 | 57.553 | 36.756 | 34.392 | 41.797 | 35.854 | 1.091 | 0.966 | 1.204 | inconclusive | inconclusive | 0.143 | 0.161 | 18.801 | -7.466 | -0.009 | 15.667 | -3.920 | 0.000 |  |
| car_passenger | population | unemployed | 89 | 80 | True | True | 48.403 | 44.589 | 30.559 | 22.551 | 37.881 | 30.345 | 0.921 | 0.764 | 1.148 | inconclusive | inconclusive | 0.192 | 0.118 | 9.705 | -2.730 | -0.009 | -5.313 | 4.097 | 0.000 |  |
| car_passenger | income | q1 | 397 | 338 | False | False | 40.642 | 44.838 | 23.617 | 21.767 | 34.866 | 29.127 | 1.103 | 0.961 | 1.229 | inconclusive | inconclusive | 0.047 | 0.047 | -1.691 | 0.904 | -0.008 | -6.932 | 5.964 | 0.000 |  |
| car_passenger | income | q2 | 442 | 394 | False | False | 36.415 | 46.896 | 21.368 | 27.371 | 35.208 | 35.019 | 1.288 | 1.135 | 1.438 | inconclusive | different | 0.090 | 0.040 | -5.491 | 0.477 | -0.007 | 3.529 | -2.438 | 0.000 |  |
| car_passenger | income | q3 | 443 | 352 | False | False | 46.634 | 45.832 | 28.236 | 27.231 | 36.329 | 35.649 | 0.983 | 0.847 | 1.143 | inconclusive | inconclusive | 0.098 | 0.041 | 6.045 | -0.838 | -0.008 | 3.253 | -3.227 | 0.000 |  |
| car_passenger | income | q4 | 434 | 347 | False | False | 39.727 | 44.426 | 23.653 | 23.823 | 35.756 | 32.175 | 1.118 | 1.006 | 1.272 | inconclusive | inconclusive | 0.040 | 0.026 | -1.609 | -0.129 | 0.029 | -2.827 | 1.448 | 0.000 |  |
| car_passenger | income | q5 | 492 | 297 | False | False | 45.265 | 47.217 | 27.085 | 26.679 | 35.902 | 33.902 | 1.043 | 0.928 | 1.192 | inconclusive | inconclusive | 0.054 | 0.051 | 4.151 | -0.313 | -0.008 | 2.351 | -0.939 | 0.000 |  |
| car_passenger | vehicles | 0 | 285 | 260 | False | False | 40.954 | 45.383 | 21.956 | 20.902 | 32.167 | 27.634 | 1.108 | 0.941 | 1.298 | inconclusive | inconclusive | 0.064 | 0.076 | -4.702 | 4.228 | -0.008 | -8.822 | 8.400 | 0.000 |  |
| car_passenger | vehicles | 1 | 797 | 653 | False | False | 42.794 | 46.023 | 24.344 | 23.909 | 34.132 | 31.170 | 1.075 | 0.973 | 1.189 | inconclusive | inconclusive | 0.064 | 0.029 | -0.459 | 1.825 | -0.008 | -2.714 | 2.931 | 0.000 |  |
| car_passenger | vehicles | 2+ | 1126 | 812 | False | False | 40.612 | 45.711 | 25.242 | 26.992 | 37.306 | 35.429 | 1.126 | 1.034 | 1.227 | inconclusive | inconclusive | 0.042 | 0.014 | 1.039 | -1.870 | 0.007 | 2.846 | -2.940 | 0.000 |  |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| car_passenger | household_type | couple | 638 | 573 | False | False | 53.857 | 57.025 | 35.854 | 34.646 | 39.944 | 36.453 | 1.059 | 0.954 | 1.176 | inconclusive | inconclusive | 0.155 | 0.159 | 17.827 | -5.397 | -0.009 | 15.969 | -4.750 | 0.000 |  |
| car_passenger | household_type | couple_with_children | 952 | 605 | False | False | 37.374 | 41.363 | 21.028 | 22.379 | 33.759 | 32.461 | 1.107 | 1.020 | 1.209 | inconclusive | inconclusive | 0.051 | 0.059 | -6.193 | 2.138 | -0.008 | -5.454 | 1.012 | 0.000 |  |
| car_passenger | household_type | other | 67 | 38 | True | True | 45.997 | - | 31.877 | - | 41.753 | - | - | - | - |  |  | 0.101 | - | 11.299 | -6.910 | 0.171 | - | - | - |  |
| car_passenger | household_type | single_parent | 180 | 163 | False | False | 39.782 | 40.817 | 21.414 | 19.773 | 32.297 | 29.066 | 1.026 | 0.839 | 1.209 | inconclusive | inconclusive | 0.050 | 0.056 | -5.649 | 4.003 | -0.008 | -10.773 | 5.785 | 0.000 |  |
| car_passenger | household_type | single_person | 371 | 349 | False | False | 38.592 | 48.886 | 21.790 | 25.470 | 33.878 | 31.261 | 1.267 | 1.094 | 1.441 | inconclusive | inconclusive | 0.084 | 0.057 | -4.868 | 2.031 | -0.008 | 0.197 | 2.883 | 0.000 |  |
| car_passenger | day_purpose | other | 1218 | 1159 | False | False | 49.006 | 54.351 | 31.569 | 32.577 | 38.651 | 35.963 | 1.109 | 1.027 | 1.195 | inconclusive | inconclusive | 0.107 | 0.109 | 11.234 | -3.655 | -0.009 | 12.503 | -3.957 | 0.000 |  |
| car_passenger | day_purpose | work_study | 990 | 569 | False | False | 34.907 | 36.013 | 18.609 | 17.099 | 31.999 | 28.488 | 1.032 | 0.938 | 1.138 | equivalent | inconclusive | 0.092 | 0.125 | -10.644 | 4.106 | 0.009 | -16.054 | 6.262 | 0.000 |  |
| other | density | dense | 85 | 54 | True | True | 62.537 | 53.312 | 25.960 | 18.824 | 24.907 | 21.185 | 0.852 | 0.672 | 1.112 | inconclusive | inconclusive | 0.123 | 0.151 | 0.676 | 3.489 | -0.275 | -29.286 | 19.203 | 0.000 |  |
| other | density | intermediate | 194 | 140 | False | False | 55.361 | 60.364 | 22.612 | 27.582 | 24.511 | 27.415 | 1.090 | 0.889 | 1.319 | inconclusive | inconclusive | 0.068 | 0.064 | -7.233 | 4.195 | -0.248 | -7.493 | 4.461 | 0.000 |  |
| other | density | sparse+very_sparse | 378 | 168 | False | False | 59.971 | 68.681 | 27.455 | 37.468 | 27.681 | 32.732 | 1.145 | 0.981 | 1.307 | inconclusive | inconclusive | 0.036 | 0.070 | 3.982 | -2.847 | 0.189 | 12.226 | -6.940 | 0.000 |  |
| other | population | children_6_17 | 273 | 89 | False | True | 57.468 | 57.720 | 21.998 | 19.737 | 22.967 | 20.517 | 1.004 | 0.836 | 1.197 | inconclusive | inconclusive | 0.044 | 0.077 | -8.967 | 8.052 | -0.264 | -27.580 | 21.904 | 0.000 |  |
| other | population | employed | 268 | 157 | False | False | 63.579 | 69.503 | 33.212 | 37.904 | 31.724 | 32.721 | 1.093 | 0.936 | 1.284 | inconclusive | inconclusive | 0.097 | 0.059 | 15.729 | -11.260 | 0.464 | 13.067 | -6.960 | 0.000 |  |
| other | population | other_inactive | 40 | 30 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | population | retired | 64 | 74 | True | True | 47.926 | 58.200 | 20.689 | 34.145 | 25.936 | 35.201 | 1.214 | 0.867 | 1.759 | inconclusive | inconclusive | 0.221 | 0.123 | -11.461 | 0.909 | -0.170 | 5.612 | -10.808 | 0.000 |  |
| other | population | unemployed | 12 | 12 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | income | q1 | 112 | 72 | False | True | 57.554 | 69.773 | 25.823 | 37.281 | 26.921 | 32.059 | 1.212 | 0.965 | 1.528 | inconclusive | inconclusive | 0.041 | 0.189 | 0.342 | -1.171 | -0.264 | 11.991 | -5.614 | 0.000 |  |
| other | income | q2 | 156 | 78 | False | True | 63.478 | 49.566 | 25.162 | 21.044 | 24.036 | 25.474 | 0.781 | 0.653 | 0.970 | inconclusive | inconclusive | 0.101 | 0.141 | -1.225 | 5.686 | 0.369 | -22.010 | 8.180 | 0.000 |  |
| other | income | q3 | 113 | 71 | False | True | 58.738 | 75.066 | 22.847 | 37.116 | 23.404 | 29.666 | 1.278 | 0.993 | 1.647 | inconclusive | inconclusive | 0.064 | 0.137 | -6.842 | 7.032 | -0.099 | 12.140 | -0.470 | 0.000 |  |
| other | income | q4 | 128 | 59 | False | True | 52.821 | 53.017 | 28.635 | 26.911 | 32.692 | 30.456 | 1.004 | 0.797 | 1.230 | inconclusive | inconclusive | 0.106 | 0.170 | 6.083 | -11.938 | 0.029 | -8.459 | -1.919 | 0.000 |  |
| other | income | q5 | 148 | 82 | False | True | 59.572 | 65.990 | 26.132 | 31.560 | 26.380 | 28.696 | 1.108 | 0.883 | 1.422 | inconclusive | inconclusive | 0.032 | 0.045 | 1.051 | 0.008 | -0.133 | 0.883 | 1.711 | 0.000 |  |
| other | vehicles | 0 | 101 | 70 | False | True | 50.426 | 58.572 | 17.793 | 27.779 | 21.171 | 28.456 | 1.162 | 0.893 | 1.490 | inconclusive | inconclusive | 0.158 | 0.081 | -19.956 | 11.982 | -0.247 | -6.948 | 2.124 | 0.000 |  |
| other | vehicles | 1 | 214 | 128 | False | False | 59.119 | 58.333 | 28.536 | 25.902 | 29.000 | 26.643 | 0.987 | 0.836 | 1.171 | inconclusive | inconclusive | 0.048 | 0.047 | 6.228 | -5.568 | -0.188 | -11.188 | 6.125 | 0.000 |  |
| other | vehicles | 2+ | 342 | 164 | False | False | 59.995 | 68.243 | 25.456 | 35.798 | 25.644 | 31.474 | 1.137 | 0.970 | 1.353 | inconclusive | inconclusive | 0.032 | 0.033 | -0.500 | 1.686 | 0.163 | 9.187 | -4.340 | 0.000 |  |
| other | household_type | couple | 89 | 89 | True | True | 50.928 | 66.522 | 26.371 | 34.540 | 31.204 | 31.154 | 1.306 | 1.028 | 1.737 | inconclusive | inconclusive | 0.203 | 0.051 | 1.469 | -9.178 | -0.010 | 6.746 | -3.619 | 0.000 |  |
| other | household_type | couple_with_children | 367 | 135 | False | False | 63.165 | 63.797 | 27.802 | 30.289 | 26.566 | 28.486 | 1.010 | 0.868 | 1.185 | inconclusive | inconclusive | 0.068 | 0.020 | 4.853 | -0.421 | 0.085 | -1.747 | 2.149 | 0.000 |  |
| other | household_type | other | 20 | 7 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| other | household_type | single_parent | 65 | 43 | True | True | 56.026 | - | 20.939 | - | 22.424 | - | - | - | - |  |  | 0.094 | - | -11.682 | 9.321 | -0.260 | - | - | - |  |
| other | household_type | single_person | 116 | 88 | False | True | 48.579 | 66.880 | 20.469 | 41.684 | 25.281 | 37.396 | 1.377 | 1.064 | 1.803 | inconclusive | inconclusive | 0.211 | 0.107 | -12.107 | 2.282 | -0.243 | 19.007 | -15.522 | 0.000 |  |
| other | day_purpose | other | 122 | 126 | False | False | 44.469 | 60.736 | 19.166 | 35.511 | 25.872 | 35.081 | 1.366 | 1.134 | 1.776 | inconclusive | different | 0.194 | 0.102 | -14.974 | 1.003 | -0.208 | 8.166 | -10.826 | 0.000 |  |
| other | day_purpose | work_study | 535 | 236 | False | False | 61.552 | 64.200 | 27.005 | 29.808 | 26.460 | 27.858 | 1.043 | 0.927 | 1.182 | inconclusive | inconclusive | 0.040 | 0.031 | 3.042 | -0.173 | 0.036 | -2.773 | 3.578 | 0.000 |  |
| train | density | dense+intermediate+sparse+very_sparse | 610 | 253 | False | False | 116.692 | 126.103 | 45.332 | 52.989 | 23.748 | 25.212 | 1.081 | 0.983 | 1.181 | inconclusive | inconclusive | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 |  |
| train | population | children_6_17 | 27 | 18 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | population | employed | 453 | 176 | False | False | 119.035 | 128.338 | 46.636 | 56.131 | 23.572 | 26.242 | 1.078 | 0.970 | 1.193 | inconclusive | inconclusive | 0.040 | 0.034 | 3.342 | 0.878 | -1.877 | 7.329 | -5.094 | 0.000 |  |
| train | population | other_inactive | 59 | 26 | True | True | 119.765 | - | 47.623 | - | 23.858 | - | - | - | - |  |  | 0.116 | - | 5.828 | -0.547 | -2.208 | - | - | - |  |
| train | population | retired | 53 | 23 | True | True | 127.639 | - | 49.984 | - | 23.496 | - | - | - | - |  |  | 0.117 | - | 11.927 | 1.301 | -2.281 | - | - | - |  |
| train | population | unemployed | 18 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | income | q1+q2+q3+q4 | 340 | 163 | False | False | 116.854 | 126.244 | 46.607 | 49.828 | 24.117 | 23.682 | 1.080 | 0.966 | 1.215 | inconclusive | inconclusive | 0.020 | 0.043 | 3.239 | -1.800 | -1.278 | -7.760 | 7.901 | 0.000 |  |
| train | income | q5 | 270 | 90 | False | True | 116.421 | 125.778 | 43.203 | 60.253 | 23.111 | 28.743 | 1.080 | 0.951 | 1.216 | inconclusive | inconclusive | 0.033 | 0.099 | -5.606 | 3.167 | 2.168 | 16.179 | -16.504 | 0.000 |  |
| train | vehicles | 0 | 198 | 80 | False | True | 108.039 | 131.267 | 32.923 | 45.824 | 18.284 | 20.945 | 1.215 | 0.998 | 1.423 | inconclusive | inconclusive | 0.108 | 0.110 | -35.920 | 29.365 | -2.098 | -18.692 | 23.856 | 0.000 |  |
| train | vehicles | 1 | 261 | 101 | False | False | 121.206 | 121.701 | 48.726 | 53.558 | 24.820 | 26.405 | 1.004 | 0.874 | 1.130 | equivalent | inconclusive | 0.055 | 0.086 | 8.587 | -5.251 | 1.179 | 1.324 | -5.726 | 0.000 |  |
| train | vehicles | 2+ | 151 | 69 | False | True | 116.852 | 118.897 | 50.633 | 53.978 | 26.448 | 27.239 | 1.017 | 0.863 | 1.243 | inconclusive | inconclusive | 0.056 | 0.099 | 12.915 | -12.575 | -0.180 | 2.265 | -9.471 | 0.000 |  |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | couple | 130 | 50 | False | True | 123.639 | 141.169 | 50.513 | 75.787 | 24.513 | 32.211 | 1.142 | 0.962 | 1.357 | inconclusive | inconclusive | 0.070 | 0.118 | 13.002 | -3.811 | -2.244 | 47.771 | -32.705 | 0.000 |  |
| train | household_type | couple_with_children | 207 | 86 | False | True | 110.682 | 114.748 | 41.431 | 48.495 | 23.390 | 25.357 | 1.037 | 0.882 | 1.205 | inconclusive | inconclusive | 0.055 | 0.075 | -10.226 | 1.725 | 2.492 | -10.663 | -0.691 | 0.000 |  |
| train | household_type | other | 18 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| train | household_type | single_parent | 65 | 33 | True | True | 130.361 | - | 51.371 | - | 23.644 | - | - | - | - |  |  | 0.149 | - | 15.432 | 0.542 | -2.305 | - | - | - |  |
| train | household_type | single_person | 190 | 76 | False | True | 113.097 | 128.249 | 46.576 | 50.739 | 24.709 | 23.738 | 1.134 | 1.004 | 1.258 | inconclusive | inconclusive | 0.051 | 0.063 | 3.110 | -4.559 | -2.146 | -5.518 | 7.664 | 0.000 |  |
| train | day_purpose | other | 114 | 53 | False | True | 112.655 | 133.415 | 44.519 | 50.217 | 23.711 | 22.584 | 1.184 | 1.014 | 1.376 | inconclusive | inconclusive | 0.098 | 0.165 | -2.075 | 0.181 | -2.142 | -6.971 | 14.282 | 0.000 |  |
| train | day_purpose | work_study | 496 | 200 | False | False | 117.491 | 124.805 | 45.493 | 53.481 | 23.755 | 25.711 | 1.062 | 0.951 | 1.172 | inconclusive | inconclusive | 0.019 | 0.029 | 0.415 | -0.036 | 0.420 | 1.159 | -2.457 | 0.000 |  |
| urban_pt | density | dense | 724 | 378 | False | False | 71.828 | 74.887 | 13.075 | 10.599 | 10.922 | 8.492 | 1.043 | 0.950 | 1.140 | equivalent | inconclusive | 0.032 | 0.048 | -15.498 | 14.599 | 0.000 | -24.065 | 23.208 | 0.000 |  |
| urban_pt | density | intermediate | 664 | 494 | False | False | 74.195 | 78.528 | 16.980 | 15.563 | 13.731 | 11.891 | 1.058 | 0.972 | 1.147 | equivalent | inconclusive | 0.023 | 0.046 | 3.446 | -1.978 | 0.000 | 4.981 | -2.196 | 0.000 |  |
| urban_pt | density | sparse+very_sparse | 96 | 92 | True | True | 68.427 | 67.215 | 26.843 | 22.679 | 23.537 | 20.244 | 0.982 | 0.790 | 1.256 | inconclusive | inconclusive | 0.140 | 0.116 | 35.620 | -39.921 | 0.000 | 31.494 | -40.022 | 0.000 |  |
| urban_pt | population | children_6_17 | 145 | 181 | False | False | 66.173 | 70.048 | 19.054 | 17.059 | 17.277 | 14.612 | 1.059 | 0.845 | 1.264 | inconclusive | inconclusive | 0.143 | 0.109 | 11.254 | -17.808 | 0.000 | 11.395 | -17.090 | 0.000 |  |
| urban_pt | population | employed | 752 | 363 | False | False | 74.042 | 75.871 | 14.627 | 14.195 | 11.853 | 11.226 | 1.025 | 0.948 | 1.105 | equivalent | inconclusive | 0.050 | 0.044 | -7.504 | 8.819 | 0.000 | -2.078 | 2.205 | 0.000 |  |
| urban_pt | population | other_inactive | 242 | 153 | False | False | 76.485 | 80.924 | 18.592 | 13.692 | 14.585 | 10.152 | 1.058 | 0.925 | 1.193 | inconclusive | inconclusive | 0.105 | 0.082 | 10.263 | -6.506 | 0.000 | -4.972 | 10.153 | 0.000 |  |
| urban_pt | population | retired | 267 | 180 | False | False | 68.761 | 75.817 | 13.847 | 11.752 | 12.083 | 9.300 | 1.103 | 0.992 | 1.235 | inconclusive | inconclusive | 0.090 | 0.063 | -11.108 | 7.142 | 0.000 | -16.389 | 16.463 | 0.000 |  |
| urban_pt | population | unemployed | 78 | 85 | True | True | 82.289 | 83.273 | 14.755 | 13.802 | 10.759 | 9.944 | 1.012 | 0.751 | 1.366 | inconclusive | inconclusive | 0.110 | 0.116 | -7.240 | 16.801 | 0.000 | -4.411 | 11.940 | 0.000 |  |
| urban_pt | income | q1 | 312 | 301 | False | False | 78.538 | 79.767 | 20.028 | 13.635 | 15.301 | 10.256 | 1.016 | 0.888 | 1.174 | inconclusive | inconclusive | 0.069 | 0.053 | 16.027 | -10.216 | 0.000 | -5.257 | 9.281 | 0.000 |  |
| urban_pt | income | q2 | 239 | 168 | False | False | 75.310 | 80.162 | 15.638 | 14.539 | 12.459 | 10.882 | 1.064 | 0.930 | 1.217 | inconclusive | inconclusive | 0.067 | 0.089 | -2.624 | 5.207 | 0.000 | -0.270 | 4.689 | 0.000 |  |
| urban_pt | income | q3 | 248 | 162 | False | False | 75.482 | 75.573 | 15.924 | 17.065 | 12.657 | 13.549 | 1.001 | 0.888 | 1.121 | equivalent | inconclusive | 0.095 | 0.060 | -1.284 | 4.039 | 0.000 | 11.859 | -12.029 | 0.000 |  |
| urban_pt | income | q4 | 267 | 140 | False | False | 64.397 | 68.026 | 14.680 | 14.095 | 13.677 | 12.432 | 1.056 | 0.923 | 1.233 | inconclusive | inconclusive | 0.094 | 0.074 | -6.756 | -1.574 | 0.000 | -2.474 | -5.243 | 0.000 |  |
| urban_pt | income | q5 | 418 | 193 | False | False | 67.756 | 71.579 | 13.238 | 14.109 | 11.723 | 11.827 | 1.056 | 0.949 | 1.161 | inconclusive | inconclusive | 0.074 | 0.050 | -14.186 | 9.215 | 0.000 | -2.464 | -1.701 | 0.000 |  |
| urban_pt | vehicles | 0 | 751 | 488 | False | False | 79.212 | 80.633 | 16.888 | 12.646 | 12.792 | 9.410 | 1.018 | 0.926 | 1.126 | equivalent | inconclusive | 0.084 | 0.070 | 3.150 | 3.335 | 0.000 | -11.173 | 16.063 | 0.000 |  |
| urban_pt | vehicles | 1 | 485 | 294 | False | False | 68.281 | 68.248 | 13.791 | 12.398 | 12.118 | 10.900 | 1.000 | 0.915 | 1.086 | equivalent | equivalent | 0.059 | 0.086 | -11.357 | 6.910 | 0.000 | -11.706 | 4.210 | 0.000 |  |
| urban_pt | vehicles | 2+ | 248 | 177 | False | False | 68.170 | 77.478 | 18.864 | 20.529 | 16.603 | 15.898 | 1.137 | 0.988 | 1.303 | inconclusive | inconclusive | 0.106 | 0.058 | 10.714 | -15.271 | 0.000 | 26.164 | -24.430 | 0.000 |  |
| urban_pt | vehicles | unknown | 0 | 5 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | couple | 272 | 130 | False | False | 69.997 | 71.750 | 14.581 | 13.684 | 12.498 | 11.443 | 1.025 | 0.920 | 1.165 | inconclusive | inconclusive | 0.046 | 0.087 | -7.523 | 4.792 | 0.000 | -4.724 | 0.730 | 0.000 |  |
| urban_pt | household_type | couple_with_children | 380 | 273 | False | False | 72.815 | 75.928 | 15.851 | 17.378 | 13.061 | 13.732 | 1.043 | 0.952 | 1.153 | inconclusive | inconclusive | 0.036 | 0.033 | -1.594 | 1.681 | 0.000 | 13.263 | -13.079 | 0.000 |  |
| urban_pt | household_type | other | 35 | 40 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| urban_pt | household_type | single_parent | 158 | 137 | False | False | 76.307 | 68.458 | 22.650 | 12.013 | 17.810 | 10.528 | 0.897 | 0.736 | 1.070 | inconclusive | inconclusive | 0.060 | 0.128 | 24.961 | -21.382 | 0.000 | -14.001 | 6.715 | 0.000 |  |
| urban_pt | household_type | single_person | 639 | 384 | False | False | 73.174 | 78.193 | 15.145 | 12.341 | 12.418 | 9.469 | 1.069 | 0.982 | 1.161 | inconclusive | inconclusive | 0.068 | 0.033 | -4.923 | 5.370 | 0.000 | -12.884 | 15.333 | 0.000 |  |
| urban_pt | day_purpose | other | 546 | 424 | False | False | 70.380 | 76.398 | 18.233 | 12.953 | 15.544 | 10.173 | 1.086 | 0.960 | 1.219 | inconclusive | inconclusive | 0.101 | 0.036 | 8.449 | -10.797 | 0.000 | -9.051 | 9.705 | 0.000 |  |
| urban_pt | day_purpose | work_study | 938 | 540 | False | False | 73.858 | 75.421 | 15.224 | 15.396 | 12.368 | 12.248 | 1.021 | 0.953 | 1.092 | equivalent | equivalent | 0.049 | 0.018 | -4.562 | 5.692 | 0.000 | 4.066 | -4.388 | 0.000 |  |
| walk | density | dense | 1080 | 691 | False | False | 39.658 | 44.495 | 2.352 | 2.408 | 3.580 | 3.247 | 1.122 | 1.015 | 1.251 | inconclusive | inconclusive | 0.075 | 0.098 | 3.130 | -1.162 | 0.181 | 3.697 | 1.388 | 0.000 |  |
| walk | density | intermediate | 2005 | 1502 | False | False | 38.167 | 38.948 | 2.235 | 2.198 | 3.513 | 3.387 | 1.020 | 0.946 | 1.093 | equivalent | equivalent | 0.026 | 0.017 | 1.140 | -0.425 | -0.057 | -0.113 | -0.349 | 0.000 |  |
| walk | density | sparse | 519 | 383 | False | False | 34.970 | 38.434 | 1.993 | 2.172 | 3.420 | 3.391 | 1.099 | 0.953 | 1.233 | inconclusive | inconclusive | 0.063 | 0.064 | -3.047 | 0.563 | -0.055 | -0.581 | -0.395 | 0.000 |  |
| walk | density | very_sparse | 837 | 399 | False | False | 34.459 | 32.172 | 1.823 | 1.856 | 3.174 | 3.461 | 0.934 | 0.832 | 1.058 | inconclusive | inconclusive | 0.123 | 0.143 | -6.242 | 3.245 | -0.054 | -6.145 | -1.093 | 0.000 |  |
| walk | population | children_6_17 | 515 | 394 | False | False | 33.191 | 30.644 | 1.935 | 1.665 | 3.497 | 3.261 | 0.923 | 0.816 | 1.049 | inconclusive | inconclusive | 0.058 | 0.119 | -4.025 | -0.241 | -0.053 | -9.778 | 1.012 | 0.000 |  |
| walk | population | employed | 1596 | 930 | False | False | 31.382 | 32.980 | 1.988 | 2.018 | 3.823 | 3.671 | 1.051 | 0.966 | 1.125 | equivalent | inconclusive | 0.094 | 0.068 | -2.974 | -3.289 | 0.135 | -3.196 | -3.234 | 0.000 |  |
| walk | population | other_inactive | 562 | 327 | False | False | 40.247 | 48.314 | 2.532 | 2.682 | 3.774 | 3.330 | 1.200 | 1.072 | 1.347 | inconclusive | inconclusive | 0.067 | 0.143 | 6.025 | -3.228 | -0.059 | 8.560 | 0.344 | 0.000 |  |
| walk | population | retired | 1505 | 1127 | False | False | 46.879 | 49.339 | 2.341 | 2.598 | 2.996 | 3.159 | 1.052 | 0.972 | 1.147 | equivalent | inconclusive | 0.113 | 0.119 | 3.222 | 6.211 | -0.064 | 7.247 | 2.682 | 0.000 |  |
| walk | population | unemployed | 263 | 195 | False | False | 44.536 | 50.503 | 2.668 | 2.826 | 3.595 | 3.358 | 1.134 | 0.921 | 1.389 | inconclusive | inconclusive | 0.119 | 0.094 | 8.492 | -1.403 | -0.062 | 11.109 | -0.015 | 0.000 |  |
| walk | income | q1 | 998 | 721 | False | False | 42.833 | 41.889 | 2.443 | 2.287 | 3.439 | 3.276 | 0.978 | 0.893 | 1.084 | equivalent | inconclusive | 0.068 | 0.065 | 4.782 | 0.403 | 0.138 | 1.486 | 0.993 | 0.000 |  |
| walk | income | q2 | 779 | 590 | False | False | 34.489 | 41.304 | 2.037 | 2.326 | 3.544 | 3.379 | 1.198 | 1.079 | 1.319 | inconclusive | inconclusive | 0.046 | 0.050 | -2.240 | -0.726 | -0.054 | 2.163 | -0.269 | 0.000 |  |
| walk | income | q3 | 799 | 507 | False | False | 36.057 | 40.816 | 2.046 | 2.293 | 3.404 | 3.371 | 1.132 | 1.005 | 1.270 | inconclusive | inconclusive | 0.039 | 0.022 | -2.139 | 0.742 | -0.056 | 1.575 | -0.169 | 0.000 |  |
| walk | income | q4 | 777 | 547 | False | False | 35.372 | 36.693 | 2.082 | 2.089 | 3.531 | 3.415 | 1.037 | 0.927 | 1.160 | inconclusive | inconclusive | 0.057 | 0.059 | -1.486 | -0.597 | -0.055 | -2.058 | -0.659 | 0.000 |  |
| walk | income | q5 | 1088 | 610 | False | False | 36.465 | 35.556 | 2.108 | 2.006 | 3.469 | 3.385 | 0.975 | 0.878 | 1.073 | equivalent | inconclusive | 0.042 | 0.057 | -1.035 | 0.046 | -0.056 | -3.537 | -0.316 | 0.000 |  |
| walk | vehicles | 0 | 1328 | 898 | False | False | 42.270 | 45.207 | 2.477 | 2.350 | 3.516 | 3.119 | 1.069 | 0.983 | 1.181 | inconclusive | inconclusive | 0.109 | 0.080 | 5.306 | -0.486 | -0.060 | 2.690 | 3.107 | 0.000 |  |
| walk | vehicles | 1 | 1875 | 1244 | False | False | 38.055 | 40.457 | 2.163 | 2.251 | 3.410 | 3.339 | 1.063 | 0.986 | 1.140 | equivalent | inconclusive | 0.016 | 0.027 | -0.096 | 0.698 | -0.057 | 0.830 | 0.218 | 0.000 |  |
| walk | vehicles | 2+ | 1238 | 824 | False | False | 33.048 | 33.454 | 1.939 | 2.026 | 3.540 | 3.634 | 1.012 | 0.929 | 1.114 | equivalent | inconclusive | 0.068 | 0.088 | -3.935 | -0.670 | 0.143 | -3.069 | -2.887 | 0.000 |  |
| walk | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | household_type | couple | 1161 | 751 | False | False | 44.475 | 44.488 | 2.378 | 2.482 | 3.207 | 3.347 | 1.000 | 0.912 | 1.104 | equivalent | inconclusive | 0.080 | 0.070 | 3.768 | 3.259 | -0.062 | 4.959 | 0.120 | 0.000 |  |
| walk | household_type | couple_with_children | 1253 | 776 | False | False | 33.353 | 33.052 | 2.015 | 1.948 | 3.640 | 3.535 | 0.991 | 0.913 | 1.087 | equivalent | equivalent | 0.052 | 0.080 | -2.585 | -1.657 | 0.086 | -4.484 | -1.874 | 0.000 |  |
| walk | household_type | other | 100 | 52 | False | True | 35.786 | 42.780 | 2.197 | 2.370 | 3.684 | 3.323 | 1.195 | 0.937 | 1.505 | inconclusive | inconclusive | 0.089 | 0.148 | 0.485 | -2.153 | -0.055 | 2.961 | 0.410 | 0.000 |  |
| walk | household_type | single_parent | 394 | 279 | False | False | 35.649 | 36.064 | 2.091 | 1.944 | 3.520 | 3.235 | 1.012 | 0.846 | 1.214 | inconclusive | inconclusive | 0.075 | 0.057 | -1.318 | -0.487 | -0.055 | -4.744 | 1.398 | 0.000 |  |
| walk | household_type | single_person | 1533 | 1117 | False | False | 39.751 | 48.204 | 2.295 | 2.557 | 3.464 | 3.183 | 1.213 | 1.135 | 1.309 | inconclusive | different | 0.057 | 0.109 | 2.192 | 0.107 | -0.058 | 6.471 | 2.324 | 0.000 |  |
| walk | day_purpose | other | 2776 | 1977 | False | False | 42.220 | 47.398 | 2.323 | 2.582 | 3.302 | 3.268 | 1.123 | 1.066 | 1.199 | inconclusive | inconclusive | 0.056 | 0.098 | 2.749 | 2.022 | -0.060 | 6.831 | 1.157 | 0.000 |  |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - |  |
| walk | day_purpose | work_study | 1665 | 997 | False | False | 31.467 | 29.503 | 1.969 | 1.737 | 3.771 | 3.532 | 0.938 | 0.871 | 1.004 | equivalent | inconclusive | 0.072 | 0.121 | -3.308 | -2.824 | 0.090 | -8.165 | -1.742 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Mode-user composition

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 520 | 306 | 1.162 | 1.193 | 0.007 | 0.001 | 2008 target rescaled to common support |
| car_driver | 8926 | 5801 | 1.087 | 1.096 | 0.000 | 0.000 |  |
| car_passenger | 2207 | 1726 | 1.105 | 1.097 | 0.000 | 0.000 |  |
| other | 657 | 362 | 1.081 | 1.045 | 0.008 | 0.000 | 2008 target rescaled to common support |
| train | 610 | 252 | 1.081 | 1.073 | 0.001 | 0.000 | 2008 target rescaled to common support |
| urban_pt | 1484 | 962 | 1.041 | 1.045 | 0.000 | 0.001 |  |
| walk | 4441 | 2973 | 1.051 | 1.047 | 0.000 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Per-mode decomposition

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | 6.990 | 2.043 | 5.017 | -0.070 | -0.000 |  |
| bike | rounded_crow_fly | 6.990 | 2.043 | 9.829 | -4.883 | -0.000 |  |
| car_driver | published | 5.409 | -3.611 | 6.716 | 2.331 | -0.028 |  |
| car_driver | rounded_crow_fly | 5.409 | -3.611 | 6.476 | 2.544 | -0.000 |  |
| car_passenger | published | 4.369 | -1.461 | 2.579 | 3.246 | 0.005 |  |
| car_passenger | rounded_crow_fly | 4.369 | -1.461 | 3.425 | 2.406 | -0.000 |  |
| other | published | 4.749 | -4.354 | 15.593 | -6.738 | 0.246 |  |
| other | rounded_crow_fly | 4.749 | -4.354 | 16.834 | -7.732 | 0.000 |  |
| train | published | 9.411 | -5.375 | 22.958 | -7.260 | -0.911 |  |
| train | rounded_crow_fly | 9.411 | -5.375 | 16.205 | -1.418 | 0.000 |  |
| urban_pt | published | 3.016 | -2.045 | -5.736 | 10.797 | -0.000 |  |
| urban_pt | rounded_crow_fly | 3.016 | -2.045 | -0.327 | 5.388 | -0.000 |  |
| walk | published | 1.900 | -0.771 | 5.253 | -2.568 | -0.014 |  |
| walk | rounded_crow_fly | 1.900 | -0.771 | -2.416 | 5.088 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Duration-rounding bounds

Scope: All days · all purposes · local (≤ 80 km) (`alldays-allpurp-local`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | 0.238 | 1.742 | 0.000 |  |
| car_driver | -0.040 | 2.875 | 0.000 |  |
| car_passenger | -0.042 | 1.447 | 0.000 |  |
| other | -0.168 | 1.906 | 0.000 |  |
| train | -0.203 | 2.393 | 0.000 |  |
| urban_pt | -0.013 | 0.591 | 0.000 |  |
| walk | -0.007 | 1.449 | 0.000 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


## All days · all purposes · all trips in the day's trip table (incl. > 80 km)

### Subgroup mode-user days

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| mode | grouping | cell | n_2008 | n_2019 | caution_2008 | caution_2019 | minutes_2008 | minutes_2019 | km_2008 | km_2019 | speed_2008 | speed_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | ks_2008 | ks_2019 | distance_gap_2008 | speed_gap_2008 | selection_gap_2008 | distance_gap_2019 | speed_gap_2019 | selection_gap_2019 | comparison_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bike | density | dense | 91 | 66 | True | True | 43.377 | 47.805 | 7.981 | 8.136 | 11.039 | 10.211 | - | - | - |  |  | 0.056 | 0.112 | 3.728 | -4.291 | 0.000 | -3.809 | 1.207 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | intermediate | 196 | 139 | False | False | 42.705 | 46.312 | 7.343 | 9.400 | 10.316 | 12.179 | - | - | - |  |  | 0.073 | 0.073 | 0.088 | -1.323 | 0.000 | 3.233 | -7.327 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | sparse | 90 | 54 | True | True | 47.114 | 44.740 | 7.479 | 7.010 | 9.525 | 9.401 | - | - | - |  |  | 0.098 | 0.129 | 0.932 | 2.242 | 0.000 | -10.763 | 5.096 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | density | very_sparse | 154 | 51 | False | True | 43.600 | 77.734 | 6.429 | 10.591 | 8.848 | 8.175 | - | - | - |  |  | 0.162 | 0.209 | -5.724 | 5.384 | 0.000 | 11.740 | 15.587 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | children_6_17 | 96 | 40 | True | True | 29.569 | - | 4.761 | - | 9.660 | - | - | - | - |  |  | 0.208 | - | -15.647 | 1.276 | 0.000 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | employed | 219 | 145 | False | False | 51.464 | 46.138 | 8.747 | 9.283 | 10.197 | 12.072 | - | - | - |  |  | 0.131 | 0.058 | 8.425 | -0.901 | 0.000 | 2.619 | -6.888 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | other_inactive | 41 | 19 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | retired | 153 | 86 | False | True | 54.676 | 49.657 | 8.680 | 9.123 | 9.526 | 11.023 | - | - | - |  |  | 0.112 | 0.044 | 8.320 | 2.416 | 0.000 | 1.848 | -2.598 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | population | unemployed | 22 | 20 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q1 | 99 | 52 | True | True | 49.475 | 57.288 | 8.323 | 8.081 | 10.093 | 8.463 | - | - | - |  |  | 0.180 | 0.093 | 5.940 | -0.406 | 0.000 | -4.538 | 11.419 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q2 | 96 | 58 | True | True | 43.042 | 56.446 | 6.421 | 8.545 | 8.950 | 9.083 | - | - | - |  |  | 0.074 | 0.139 | -5.747 | 4.849 | 0.000 | -1.521 | 7.561 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q3 | 100 | 63 | False | True | 41.192 | 51.034 | 6.737 | 9.566 | 9.813 | 11.246 | - | - | - |  |  | 0.081 | 0.114 | -3.577 | 0.829 | 0.000 | 4.277 | -3.649 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q4 | 99 | 55 | True | True | 40.437 | 37.575 | 7.764 | 7.744 | 11.520 | 12.365 | - | - | - |  |  | 0.105 | 0.140 | 2.440 | -5.943 | 0.000 | -5.546 | -7.285 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | income | q5 | 137 | 82 | False | True | 45.600 | 51.393 | 7.354 | 10.027 | 9.676 | 11.706 | - | - | - |  |  | 0.064 | 0.102 | 0.161 | 1.499 | 0.000 | 6.687 | -5.701 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 0 | 108 | 62 | False | True | 40.481 | 53.657 | 7.427 | 8.513 | 11.008 | 9.520 | - | - | - |  |  | 0.078 | 0.127 | 0.566 | -4.026 | 0.000 | -1.678 | 4.928 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 1 | 199 | 125 | False | False | 49.742 | 48.677 | 8.404 | 9.453 | 10.137 | 11.652 | - | - | - |  |  | 0.123 | 0.060 | 6.409 | -0.607 | 0.000 | 3.590 | -5.320 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | 2+ | 224 | 120 | False | False | 40.721 | 50.536 | 6.422 | 8.386 | 9.462 | 9.957 | - | - | - |  |  | 0.113 | 0.095 | -5.584 | 2.365 | 0.000 | -2.387 | 2.516 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple | 164 | 92 | False | True | 50.813 | 43.985 | 8.126 | 8.280 | 9.595 | 11.294 | - | - | - |  |  | 0.097 | 0.048 | 4.891 | 1.982 | 0.000 | -2.831 | -3.591 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | couple_with_children | 183 | 90 | False | True | 41.268 | 50.921 | 6.886 | 8.708 | 10.012 | 10.261 | - | - | - |  |  | 0.060 | 0.061 | -2.647 | -0.025 | 0.000 | -0.485 | 1.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | other | 13 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_parent | 39 | 31 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | household_type | single_person | 132 | 91 | False | True | 48.066 | 52.051 | 8.745 | 9.713 | 10.917 | 11.197 | - | - | - |  |  | 0.239 | 0.092 | 8.130 | -4.005 | 0.000 | 5.103 | -3.458 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | other | 296 | 163 | False | False | 44.859 | 58.649 | 6.992 | 9.472 | 9.352 | 9.690 | - | - | - |  |  | 0.045 | 0.076 | -2.082 | 3.000 | 0.000 | 4.052 | 4.191 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | day_purpose | work_study | 235 | 147 | False | False | 42.737 | 41.580 | 7.767 | 8.065 | 10.905 | 11.637 | - | - | - |  |  | 0.059 | 0.082 | 2.525 | -3.728 | 0.000 | -3.961 | -4.865 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | dense | 723 | 471 | False | False | 69.066 | 87.593 | 36.857 | 51.163 | 32.434 | 35.046 | - | - | - |  |  | 0.053 | 0.070 | -12.500 | 13.418 | 0.677 | 6.327 | 7.298 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | intermediate | 3441 | 2565 | False | False | 67.648 | 72.265 | 39.767 | 40.566 | 35.279 | 33.681 | - | - | - |  |  | 0.013 | 0.017 | -7.237 | 7.600 | -0.186 | -11.230 | 9.526 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | sparse | 1336 | 1059 | False | False | 65.823 | 67.696 | 45.984 | 46.191 | 41.931 | 40.940 | - | - | - |  |  | 0.053 | 0.039 | 2.542 | -4.016 | -0.173 | -1.679 | -4.593 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | density | very_sparse | 3672 | 1835 | False | False | 67.815 | 77.219 | 51.602 | 57.812 | 45.905 | 44.921 | - | - | - |  |  | 0.019 | 0.028 | 10.376 | -10.201 | 0.169 | 15.168 | -11.918 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | children_6_17 | 82 | 50 | True | True | 43.398 | 72.108 | 24.959 | 52.737 | 34.507 | 43.882 | - | - | - |  |  | 0.235 | 0.171 | -31.255 | 7.344 | -0.161 | 7.947 | -9.807 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | employed | 5773 | 3272 | False | False | 73.006 | 80.524 | 49.573 | 53.099 | 40.908 | 39.566 | - | - | - |  |  | 0.052 | 0.076 | 7.952 | -2.496 | 0.078 | 8.928 | -2.373 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | other_inactive | 670 | 314 | False | False | 59.255 | 65.882 | 34.907 | 40.216 | 35.346 | 36.625 | - | - | - |  |  | 0.089 | 0.085 | -15.025 | 6.997 | -0.187 | -11.333 | 3.247 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | retired | 2303 | 2010 | False | False | 55.617 | 58.972 | 32.889 | 33.846 | 35.486 | 34.436 | - | - | - |  |  | 0.115 | 0.165 | -18.223 | 6.543 | -0.173 | -22.153 | 7.156 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | population | unemployed | 344 | 280 | False | False | 62.063 | 72.577 | 40.162 | 44.691 | 38.828 | 36.947 | - | - | - |  |  | 0.064 | 0.059 | -6.294 | 1.077 | -0.191 | -4.157 | 2.766 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q1 | 1061 | 662 | False | False | 55.140 | 64.610 | 33.593 | 37.232 | 36.558 | 34.575 | - | - | - |  |  | 0.120 | 0.075 | -16.854 | 4.696 | -0.173 | -16.559 | 7.201 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q2 | 1419 | 1087 | False | False | 62.317 | 66.490 | 39.725 | 41.897 | 38.308 | 37.808 | - | - | - |  |  | 0.042 | 0.059 | -7.017 | 1.953 | -0.090 | -8.510 | 1.031 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q3 | 1884 | 1251 | False | False | 65.356 | 77.220 | 42.033 | 53.926 | 38.588 | 41.900 | - | - | - |  |  | 0.027 | 0.023 | -3.434 | 1.515 | -0.196 | 9.909 | -6.657 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q4 | 2063 | 1431 | False | False | 70.322 | 75.553 | 48.065 | 47.492 | 41.314 | 37.716 | - | - | - |  |  | 0.039 | 0.031 | 5.675 | -3.129 | 0.306 | 0.303 | 1.281 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | income | q5 | 2745 | 1499 | False | False | 76.915 | 79.815 | 51.608 | 50.220 | 40.392 | 37.753 | - | - | - |  |  | 0.092 | 0.068 | 11.067 | -1.648 | 0.025 | 4.604 | 1.242 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 0 | 67 | 63 | True | True | 83.943 | 72.168 | 71.629 | 38.878 | 51.198 | 32.323 | - | - | - |  |  | 0.248 | 0.186 | 36.296 | -19.601 | -0.223 | -14.327 | 12.527 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 1 | 3622 | 2659 | False | False | 64.268 | 70.423 | 38.848 | 41.167 | 36.273 | 35.074 | - | - | - |  |  | 0.050 | 0.037 | -8.594 | 5.577 | -0.186 | -10.024 | 6.478 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | 2+ | 5483 | 3199 | False | False | 69.227 | 76.269 | 47.240 | 51.331 | 41.134 | 40.381 | - | - | - |  |  | 0.032 | 0.026 | 4.447 | -2.806 | 0.115 | 6.142 | -3.842 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | vehicles | unknown | 0 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple | 3112 | 2048 | False | False | 64.095 | 66.941 | 41.349 | 42.405 | 38.713 | 38.008 | - | - | - |  |  | 0.052 | 0.079 | -4.479 | 1.288 | -0.184 | -7.691 | 0.664 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | couple_with_children | 3421 | 1694 | False | False | 71.418 | 81.009 | 47.755 | 53.427 | 40.288 | 39.571 | - | - | - |  |  | 0.044 | 0.068 | 5.271 | -1.408 | 0.085 | 9.432 | -2.392 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | other | 182 | 92 | False | True | 60.492 | 75.640 | 36.768 | 50.436 | 37.217 | 40.008 | - | - | - |  |  | 0.107 | 0.106 | -11.858 | 3.772 | 1.108 | 4.802 | -3.130 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_parent | 563 | 363 | False | False | 60.668 | 71.185 | 37.357 | 41.926 | 37.052 | 35.339 | - | - | - |  |  | 0.067 | 0.032 | -10.859 | 4.061 | -0.005 | -8.751 | 5.968 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | household_type | single_person | 1894 | 1733 | False | False | 64.992 | 68.688 | 42.649 | 41.864 | 39.386 | 36.569 | - | - | - |  |  | 0.041 | 0.058 | -2.460 | 0.156 | -0.175 | -8.703 | 3.423 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | other | 4341 | 3238 | False | False | 59.974 | 64.195 | 38.080 | 39.479 | 38.299 | 36.899 | - | - | - |  |  | 0.096 | 0.119 | -9.578 | 1.932 | 0.149 | -12.466 | 2.692 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | day_purpose | work_study | 4831 | 2692 | False | False | 73.246 | 82.280 | 49.028 | 53.952 | 40.221 | 39.342 | - | - | - |  |  | 0.074 | 0.101 | 7.188 | -1.309 | -0.103 | 10.270 | -1.958 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | dense | 242 | 193 | False | False | 52.431 | 62.591 | 35.504 | 39.098 | 41.047 | 37.480 | - | - | - |  |  | 0.081 | 0.143 | 5.752 | -0.750 | 0.196 | 7.901 | 1.590 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | intermediate | 906 | 853 | False | False | 43.805 | 51.626 | 25.604 | 29.352 | 35.362 | 34.113 | - | - | - |  |  | 0.039 | 0.038 | -9.615 | 6.098 | 0.090 | -7.845 | 6.371 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | sparse | 328 | 313 | False | False | 47.178 | 51.724 | 33.159 | 36.722 | 42.398 | 42.599 | - | - | - |  |  | 0.056 | 0.059 | 2.229 | -2.240 | -0.043 | 3.889 | -5.266 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | density | very_sparse | 870 | 467 | False | False | 50.818 | 53.079 | 38.655 | 39.167 | 45.765 | 44.274 | - | - | - |  |  | 0.069 | 0.042 | 9.828 | -6.070 | -0.172 | 7.360 | -7.381 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | children_6_17 | 668 | 504 | False | False | 35.223 | 39.873 | 21.437 | 22.258 | 36.542 | 33.494 | - | - | - |  |  | 0.128 | 0.118 | -15.922 | 4.142 | -0.229 | -19.691 | 6.463 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | employed | 706 | 371 | False | False | 53.522 | 67.213 | 35.756 | 49.662 | 40.383 | 44.333 | - | - | - |  |  | 0.080 | 0.113 | 6.169 | 0.063 | 0.058 | 22.518 | -8.405 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | other_inactive | 276 | 191 | False | False | 59.287 | 53.503 | 39.241 | 29.353 | 39.815 | 32.918 | - | - | - |  |  | 0.133 | 0.059 | 11.434 | 0.818 | -0.198 | -7.983 | 8.387 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | retired | 599 | 667 | False | False | 59.017 | 65.768 | 43.911 | 44.892 | 45.331 | 40.955 | - | - | - |  |  | 0.144 | 0.150 | 17.356 | -6.049 | 0.478 | 16.287 | -3.620 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | population | unemployed | 96 | 91 | True | True | 61.530 | 62.542 | 50.586 | 44.008 | 49.748 | 42.220 | - | - | - |  |  | 0.199 | 0.100 | 25.388 | -11.209 | 0.118 | 14.723 | -5.281 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q1 | 414 | 352 | False | False | 45.275 | 52.458 | 28.567 | 29.567 | 37.944 | 33.818 | - | - | - |  |  | 0.046 | 0.047 | -4.710 | 2.939 | -0.186 | -7.522 | 6.880 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q2 | 459 | 405 | False | False | 39.893 | 52.254 | 24.947 | 34.179 | 37.521 | 39.246 | - | - | - |  |  | 0.100 | 0.035 | -10.315 | 3.249 | -0.273 | 0.128 | -0.975 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q3 | 477 | 374 | False | False | 52.090 | 51.599 | 35.199 | 33.527 | 40.584 | 38.986 | - | - | - |  |  | 0.097 | 0.039 | 5.305 | -0.184 | -0.264 | -0.880 | -0.621 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q4 | 456 | 369 | False | False | 43.747 | 50.508 | 29.303 | 32.256 | 40.414 | 38.318 | - | - | - |  |  | 0.042 | 0.028 | -3.474 | 0.022 | -0.033 | -2.873 | 0.281 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | income | q5 | 540 | 326 | False | False | 57.482 | 60.079 | 42.276 | 42.478 | 45.112 | 42.422 | - | - | - |  |  | 0.075 | 0.060 | 15.141 | -5.715 | 0.823 | 12.423 | -5.444 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 0 | 304 | 275 | False | False | 46.269 | 60.347 | 28.810 | 40.616 | 37.393 | 40.382 | - | - | - |  |  | 0.054 | 0.084 | -4.365 | 3.655 | -0.253 | 9.912 | -2.664 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 1 | 853 | 685 | False | False | 48.324 | 51.347 | 31.313 | 30.871 | 39.033 | 36.073 | - | - | - |  |  | 0.060 | 0.031 | -0.481 | 1.684 | -0.111 | -5.189 | 3.436 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | 2+ | 1189 | 863 | False | False | 46.674 | 53.290 | 32.327 | 35.411 | 41.925 | 39.870 | - | - | - |  |  | 0.040 | 0.013 | 1.023 | -1.701 | 0.119 | 2.012 | -1.823 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple | 688 | 613 | False | False | 62.699 | 65.799 | 46.279 | 45.610 | 44.920 | 41.591 | - | - | - |  |  | 0.159 | 0.148 | 20.780 | -5.745 | 0.432 | 17.230 | -4.532 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | couple_with_children | 988 | 636 | False | False | 41.413 | 47.326 | 26.486 | 29.753 | 38.441 | 37.721 | - | - | - |  |  | 0.056 | 0.059 | -7.855 | 2.237 | -0.202 | -6.834 | 1.060 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | other | 68 | 39 | True | True | 45.951 | - | 31.824 | - | 41.724 | - | - | - | - |  |  | 0.075 | - | 0.286 | -1.464 | -0.102 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_parent | 194 | 166 | False | False | 49.388 | 49.054 | 31.926 | 27.086 | 38.805 | 33.129 | - | - | - |  |  | 0.038 | 0.057 | 0.451 | 1.986 | -0.280 | -11.751 | 7.705 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | household_type | single_person | 408 | 372 | False | False | 46.149 | 58.904 | 29.479 | 38.080 | 38.927 | 38.789 | - | - | - |  |  | 0.070 | 0.058 | -3.287 | 1.772 | 0.432 | 6.183 | -0.379 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | other | 1312 | 1240 | False | False | 57.987 | 65.698 | 42.866 | 46.039 | 44.673 | 42.046 | - | - | - |  |  | 0.117 | 0.113 | 15.936 | -5.227 | 0.046 | 17.771 | -5.172 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | day_purpose | work_study | 1034 | 586 | False | False | 37.595 | 37.741 | 21.561 | 19.536 | 34.586 | 31.058 | - | - | - |  |  | 0.105 | 0.138 | -16.184 | 6.597 | -0.051 | -25.053 | 9.694 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | dense | 97 | 59 | True | True | 84.766 | 77.010 | 34.006 | 130.830 | 30.942 | 101.932 | - | - | - |  |  | 0.151 | 0.147 | 8.290 | -1.315 | 9.075 | 13.557 | -19.351 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | intermediate | 219 | 155 | False | False | 68.532 | 82.975 | 25.788 | 143.218 | 28.885 | 103.563 | - | - | - |  |  | 0.060 | 0.052 | -11.543 | 3.542 | 7.817 | 21.568 | -21.397 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | sparse | 77 | 53 | True | True | 51.844 | 88.002 | 28.719 | 84.164 | 35.409 | 57.384 | - | - | - |  |  | 0.172 | 0.144 | -3.626 | -9.106 | -4.141 | -23.171 | 28.369 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | density | very_sparse | 319 | 124 | False | False | 71.349 | 82.611 | 34.364 | 73.380 | 29.937 | 53.295 | - | - | - |  |  | 0.068 | 0.045 | 8.325 | 1.108 | -6.802 | -33.788 | 33.594 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | children_6_17 | 277 | 92 | False | True | 60.446 | 68.728 | 22.720 | 60.778 | 23.567 | 53.059 | - | - | - |  |  | 0.067 | 0.106 | -19.016 | 16.450 | -5.705 | -45.098 | 31.022 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | employed | 304 | 177 | False | False | 83.286 | 98.995 | 44.969 | 163.779 | 39.898 | 99.265 | - | - | - |  |  | 0.123 | 0.086 | 29.387 | -20.565 | 5.747 | 35.751 | -19.561 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | other_inactive | 44 | 32 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | retired | 74 | 76 | True | True | 63.803 | 60.021 | 23.979 | 36.249 | 30.431 | 36.236 | - | - | - |  |  | 0.180 | 0.125 | -15.959 | -0.035 | 11.080 | -78.858 | 56.074 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | population | unemployed | 13 | 13 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q1 | 114 | 76 | False | True | 60.539 | 72.069 | 27.801 | 40.189 | 28.125 | 33.459 | - | - | - |  |  | 0.059 | 0.144 | -6.005 | 5.052 | -7.224 | -78.130 | 67.394 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q2 | 159 | 82 | False | True | 64.856 | 64.904 | 25.216 | 67.721 | 24.116 | 62.604 | - | - | - |  |  | 0.094 | 0.133 | -12.728 | 15.493 | -6.626 | -35.920 | 18.020 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q3 | 118 | 74 | False | True | 59.981 | 96.153 | 23.382 | 186.870 | 23.729 | 116.609 | - | - | - |  |  | 0.093 | 0.123 | -17.101 | 15.948 | -7.583 | 47.000 | -33.652 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q4 | 139 | 68 | False | True | 68.488 | 85.339 | 40.107 | 102.849 | 41.864 | 72.310 | - | - | - |  |  | 0.094 | 0.136 | 18.758 | -21.919 | 2.932 | -5.961 | 8.496 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | income | q5 | 182 | 91 | False | True | 93.307 | 93.226 | 37.983 | 143.596 | 36.793 | 92.418 | - | - | - |  |  | 0.106 | 0.056 | 17.606 | -15.305 | 22.289 | 23.107 | -12.685 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 0 | 105 | 74 | False | True | 58.748 | 87.144 | 17.113 | 130.768 | 21.171 | 90.036 | - | - | - |  |  | 0.155 | 0.064 | -36.782 | 23.042 | 3.770 | 14.380 | -10.039 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 1 | 233 | 136 | False | False | 71.649 | 69.935 | 38.856 | 89.192 | 36.394 | 76.521 | - | - | - |  |  | 0.047 | 0.069 | 16.963 | -12.596 | -1.435 | -16.257 | 3.388 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | vehicles | 2+ | 374 | 181 | False | False | 68.869 | 91.019 | 27.963 | 121.185 | 27.914 | 79.885 | - | - | - |  |  | 0.029 | 0.045 | -6.002 | 5.901 | 0.253 | 8.089 | 0.125 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple | 103 | 95 | False | True | 74.925 | 82.498 | 33.347 | 98.190 | 35.404 | 71.413 | - | - | - |  |  | 0.166 | 0.053 | 6.377 | -10.904 | 10.736 | -9.692 | 9.386 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | couple_with_children | 388 | 147 | False | False | 69.478 | 83.779 | 28.936 | 108.914 | 28.137 | 78.001 | - | - | - |  |  | 0.062 | 0.021 | -3.665 | 5.378 | -0.952 | -1.133 | 2.108 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | other | 22 | 8 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_parent | 68 | 44 | True | True | 61.966 | - | 25.676 | - | 25.341 | - | - | - | - |  |  | 0.114 | - | -11.266 | 11.914 | -7.399 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | household_type | single_person | 131 | 97 | False | True | 77.525 | 94.610 | 50.079 | 190.764 | 47.486 | 120.979 | - | - | - |  |  | 0.170 | 0.089 | 36.186 | -32.537 | 5.160 | 48.439 | -36.634 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | other | 150 | 145 | False | False | 67.219 | 117.458 | 24.469 | 268.841 | 33.840 | 137.330 | - | - | - |  |  | 0.148 | 0.127 | -15.002 | -7.254 | 20.758 | 88.215 | -53.562 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | day_purpose | work_study | 562 | 246 | False | False | 69.042 | 70.076 | 31.824 | 52.214 | 29.909 | 44.706 | - | - | - |  |  | 0.032 | 0.047 | 2.899 | 1.154 | -3.727 | -57.108 | 44.380 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | density | dense+intermediate+sparse+very_sparse | 703 | 295 | False | False | 146.139 | 143.278 | 80.006 | 92.105 | 40.373 | 38.570 | - | - | - |  |  | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.000 | -0.000 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | children_6_17 | 33 | 19 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | employed | 516 | 204 | False | False | 151.236 | 146.820 | 79.713 | 103.209 | 38.709 | 42.178 | - | - | - |  |  | 0.043 | 0.038 | -0.546 | 6.259 | -0.615 | 16.511 | -12.968 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | other_inactive | 65 | 30 | True | True | 132.239 | - | 70.063 | - | 33.613 | - | - | - | - |  |  | 0.134 | - | -18.457 | 25.487 | -20.930 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | retired | 65 | 32 | True | True | 176.813 | - | 58.591 | - | 31.918 | - | - | - | - |  |  | 0.113 | - | -50.151 | 37.831 | 42.994 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | population | unemployed | 24 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q1+q2+q3 | 247 | 130 | False | False | 137.123 | 134.999 | 66.116 | 66.603 | 36.225 | 29.601 | - | - | - |  |  | 0.051 | 0.081 | -26.999 | 15.349 | 2.634 | -45.093 | 36.815 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q4 | 141 | 54 | False | True | 153.245 | 157.039 | 97.748 | 111.716 | 45.239 | 42.683 | - | - | - |  |  | 0.107 | 0.139 | 29.976 | -17.030 | -5.840 | 28.965 | -15.203 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | income | q5 | 315 | 111 | False | False | 152.078 | 148.942 | 85.533 | 121.870 | 41.620 | 49.094 | - | - | - |  |  | 0.048 | 0.096 | 9.958 | -4.534 | 0.515 | 40.910 | -35.245 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 0 | 215 | 89 | False | True | 114.344 | 149.896 | 42.518 | 97.978 | 24.180 | 39.218 | - | - | - |  |  | 0.179 | 0.107 | -81.927 | 66.437 | -16.305 | 9.060 | -2.442 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 1 | 305 | 119 | False | False | 150.164 | 139.724 | 99.500 | 87.032 | 47.282 | 37.373 | - | - | - |  |  | 0.058 | 0.072 | 32.302 | -23.399 | -4.878 | -8.015 | 4.462 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | 2+ | 183 | 84 | False | True | 162.997 | 135.394 | 76.061 | 91.936 | 39.058 | 40.742 | - | - | - |  |  | 0.077 | 0.085 | -7.809 | 5.116 | 19.552 | -0.255 | -7.628 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | vehicles | unknown | 0 | 3 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple | 152 | 58 | False | True | 154.969 | 172.812 | 92.371 | 168.857 | 43.034 | 58.627 | - | - | - |  |  | 0.089 | 0.115 | 21.630 | -9.607 | -3.193 | 95.515 | -65.981 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | couple_with_children | 236 | 93 | False | True | 139.726 | 123.017 | 76.918 | 65.535 | 42.942 | 31.964 | - | - | - |  |  | 0.050 | 0.095 | -5.626 | -8.815 | 8.028 | -45.227 | 24.967 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | other | 20 | 9 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_parent | 71 | 36 | True | True | 146.035 | - | 75.344 | - | 34.558 | - | - | - | - |  |  | 0.100 | - | -8.771 | 22.720 | -14.053 | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | household_type | single_person | 224 | 99 | False | True | 154.292 | 159.351 | 78.682 | 120.795 | 37.529 | 45.482 | - | - | - |  |  | 0.050 | 0.128 | -2.506 | 10.970 | -0.311 | 40.993 | -24.919 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | other | 153 | 71 | False | True | 158.859 | 177.777 | 96.767 | 151.239 | 50.143 | 51.044 | - | - | - |  |  | 0.111 | 0.191 | 28.988 | -33.030 | 16.761 | 79.304 | -44.805 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | day_purpose | work_study | 550 | 224 | False | False | 143.267 | 135.974 | 76.222 | 79.586 | 38.238 | 35.118 | - | - | - |  |  | 0.025 | 0.040 | -7.011 | 7.864 | -3.724 | -20.394 | 13.090 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | dense | 733 | 381 | False | False | 73.073 | 75.306 | 14.840 | 10.927 | 12.185 | 8.706 | - | - | - |  |  | 0.031 | 0.046 | -21.791 | 20.008 | 0.000 | -33.621 | 28.888 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | intermediate | 673 | 509 | False | False | 75.621 | 80.296 | 19.348 | 17.154 | 15.351 | 12.818 | - | - | - |  |  | 0.025 | 0.043 | -2.209 | 2.974 | 0.000 | 1.440 | -1.183 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | density | sparse+very_sparse | 112 | 100 | False | False | 78.621 | 92.302 | 45.408 | 32.252 | 34.653 | 20.965 | - | - | - |  |  | 0.138 | 0.096 | 63.201 | -59.435 | 0.000 | 55.857 | -43.594 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | children_6_17 | 148 | 185 | False | False | 70.472 | 74.010 | 24.772 | 20.579 | 21.091 | 16.684 | - | - | - |  |  | 0.131 | 0.109 | 15.820 | -20.203 | 0.000 | 15.398 | -21.427 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | employed | 769 | 375 | False | False | 74.335 | 78.298 | 16.011 | 16.185 | 12.923 | 12.403 | - | - | - |  |  | 0.043 | 0.043 | -16.312 | 15.792 | 0.000 | -3.179 | 1.438 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | other_inactive | 244 | 156 | False | False | 76.424 | 91.549 | 18.603 | 13.959 | 14.605 | 9.149 | - | - | - |  |  | 0.100 | 0.085 | -5.187 | 6.756 | 0.000 | -16.114 | 27.624 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | retired | 278 | 186 | False | False | 78.807 | 79.983 | 31.161 | 16.709 | 23.724 | 12.534 | - | - | - |  |  | 0.071 | 0.059 | 34.353 | -30.402 | 0.000 | -0.666 | 0.609 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | population | unemployed | 79 | 86 | True | True | 83.160 | 83.193 | 14.891 | 13.763 | 10.744 | 9.926 | - | - | - |  |  | 0.109 | 0.110 | -22.986 | 31.290 | 0.000 | -16.509 | 19.664 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q1 | 315 | 303 | False | False | 80.754 | 79.837 | 23.498 | 13.828 | 17.459 | 10.392 | - | - | - |  |  | 0.069 | 0.044 | 12.831 | -6.933 | 0.000 | -15.795 | 15.593 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q2 | 244 | 174 | False | False | 76.762 | 93.303 | 18.852 | 17.435 | 14.736 | 11.212 | - | - | - |  |  | 0.064 | 0.099 | -4.192 | 6.099 | 0.000 | 2.959 | 10.305 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q3 | 255 | 166 | False | False | 78.750 | 79.321 | 19.024 | 19.593 | 14.495 | 14.821 | - | - | - |  |  | 0.089 | 0.048 | -3.548 | 7.444 | 0.000 | 12.024 | -12.742 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q4 | 278 | 144 | False | False | 68.295 | 74.148 | 20.221 | 19.376 | 17.765 | 15.679 | - | - | - |  |  | 0.082 | 0.080 | 1.057 | -7.617 | 0.000 | 10.770 | -16.661 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | income | q5 | 426 | 203 | False | False | 67.929 | 73.682 | 16.563 | 16.434 | 14.630 | 13.382 | - | - | - |  |  | 0.083 | 0.054 | -13.178 | 6.252 | 0.000 | -1.915 | -4.442 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 0 | 755 | 490 | False | False | 79.522 | 80.683 | 17.833 | 12.790 | 13.455 | 9.511 | - | - | - |  |  | 0.085 | 0.060 | -8.555 | 13.222 | 0.000 | -22.150 | 22.793 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 1 | 503 | 303 | False | False | 72.332 | 75.916 | 19.543 | 14.281 | 16.211 | 11.287 | - | - | - |  |  | 0.048 | 0.079 | -1.419 | -1.104 | 0.000 | -12.892 | 8.769 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | 2+ | 260 | 191 | False | False | 70.713 | 84.033 | 24.247 | 26.114 | 20.574 | 18.646 | - | - | - |  |  | 0.111 | 0.055 | 14.289 | -18.431 | 0.000 | 35.943 | -31.948 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | vehicles | unknown | 0 | 6 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple | 280 | 139 | False | False | 72.241 | 75.434 | 20.924 | 17.732 | 17.379 | 14.104 | - | - | - |  |  | 0.043 | 0.080 | 3.601 | -6.216 | 0.000 | 3.971 | -8.576 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | couple_with_children | 389 | 282 | False | False | 75.710 | 84.128 | 20.033 | 20.523 | 15.876 | 14.637 | - | - | - |  |  | 0.035 | 0.032 | 0.412 | 0.443 | 0.000 | 16.191 | -12.102 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | other | 38 | 40 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_parent | 161 | 139 | False | False | 76.072 | 69.383 | 22.524 | 12.653 | 17.766 | 10.942 | - | - | - |  |  | 0.057 | 0.130 | 9.257 | -8.041 | 0.000 | -21.360 | 10.704 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | household_type | single_person | 650 | 390 | False | False | 75.524 | 79.053 | 18.985 | 13.683 | 15.082 | 10.385 | - | - | - |  |  | 0.074 | 0.026 | -3.631 | 4.300 | 0.000 | -16.557 | 15.571 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | other | 564 | 441 | False | False | 73.627 | 87.207 | 24.016 | 18.161 | 19.571 | 12.495 | - | - | - |  |  | 0.100 | 0.036 | 13.868 | -15.096 | 0.000 | 6.267 | 0.901 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | day_purpose | work_study | 954 | 549 | False | False | 75.453 | 76.431 | 17.935 | 16.188 | 14.262 | 12.708 | - | - | - |  |  | 0.048 | 0.018 | -7.905 | 8.502 | 0.000 | -3.127 | -0.480 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | dense | 1097 | 701 | False | False | 39.754 | 44.828 | 2.354 | 2.426 | 3.577 | 3.247 | - | - | - |  |  | 0.073 | 0.098 | 2.986 | -1.267 | 0.187 | 3.514 | 1.406 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | intermediate | 2022 | 1532 | False | False | 38.504 | 39.600 | 2.243 | 2.241 | 3.495 | 3.396 | - | - | - |  |  | 0.025 | 0.015 | 1.086 | -0.362 | -0.068 | 0.152 | -0.460 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | sparse | 522 | 387 | False | False | 35.102 | 38.193 | 1.999 | 2.153 | 3.416 | 3.383 | - | - | - |  |  | 0.064 | 0.067 | -3.169 | 0.489 | -0.065 | -1.415 | -0.300 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | density | very_sparse | 862 | 411 | False | False | 35.477 | 33.525 | 1.873 | 1.911 | 3.172 | 3.420 | - | - | - |  |  | 0.117 | 0.135 | -5.562 | 3.204 | -0.013 | -5.703 | -0.680 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | children_6_17 | 519 | 404 | False | False | 33.472 | 31.088 | 1.952 | 1.679 | 3.500 | 3.241 | - | - | - |  |  | 0.057 | 0.121 | -3.942 | -0.390 | -0.044 | -10.062 | 1.243 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | employed | 1628 | 951 | False | False | 31.833 | 33.606 | 1.996 | 2.057 | 3.782 | 3.673 | - | - | - |  |  | 0.095 | 0.068 | -3.070 | -3.067 | 0.122 | -3.005 | -3.297 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | other_inactive | 567 | 334 | False | False | 40.397 | 48.208 | 2.542 | 2.669 | 3.775 | 3.322 | - | - | - |  |  | 0.066 | 0.145 | 6.003 | -3.383 | -0.070 | 7.833 | 0.467 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | retired | 1523 | 1143 | False | False | 47.338 | 50.289 | 2.359 | 2.657 | 2.992 | 3.170 | - | - | - |  |  | 0.116 | 0.122 | 3.355 | 6.186 | -0.051 | 7.805 | 2.576 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | population | unemployed | 266 | 197 | False | False | 44.618 | 50.292 | 2.672 | 2.816 | 3.594 | 3.360 | - | - | - |  |  | 0.119 | 0.089 | 8.375 | -1.532 | -0.074 | 10.421 | -0.037 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q1 | 1002 | 725 | False | False | 42.823 | 41.949 | 2.442 | 2.291 | 3.439 | 3.277 | - | - | - |  |  | 0.067 | 0.062 | 4.579 | 0.270 | 0.127 | 1.055 | 0.986 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q2 | 787 | 600 | False | False | 34.785 | 41.092 | 2.049 | 2.306 | 3.534 | 3.367 | - | - | - |  |  | 0.046 | 0.046 | -2.248 | -0.749 | -0.065 | 1.308 | -0.124 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q3 | 808 | 516 | False | False | 36.232 | 41.563 | 2.055 | 2.323 | 3.402 | 3.354 | - | - | - |  |  | 0.041 | 0.023 | -2.196 | 0.647 | -0.066 | 1.615 | 0.040 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q4 | 792 | 560 | False | False | 35.851 | 37.349 | 2.109 | 2.124 | 3.529 | 3.413 | - | - | - |  |  | 0.054 | 0.055 | -1.227 | -0.704 | -0.066 | -1.923 | -0.636 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | income | q5 | 1114 | 630 | False | False | 37.437 | 37.063 | 2.129 | 2.108 | 3.418 | 3.412 | - | - | - |  |  | 0.042 | 0.052 | -0.895 | 0.488 | -0.004 | -2.219 | -0.626 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 0 | 1332 | 903 | False | False | 42.253 | 45.175 | 2.476 | 2.349 | 3.516 | 3.120 | - | - | - |  |  | 0.109 | 0.077 | 5.092 | -0.615 | -0.072 | 2.160 | 3.108 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 1 | 1905 | 1265 | False | False | 38.189 | 40.780 | 2.167 | 2.264 | 3.405 | 3.331 | - | - | - |  |  | 0.017 | 0.025 | -0.229 | 0.628 | -0.058 | 0.554 | 0.318 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | 2+ | 1266 | 853 | False | False | 34.004 | 34.779 | 1.975 | 2.102 | 3.506 | 3.627 | - | - | - |  |  | 0.064 | 0.081 | -3.548 | -0.447 | 0.152 | -2.245 | -2.884 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | vehicles | unknown | 0 | 10 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple | 1179 | 773 | False | False | 44.775 | 45.734 | 2.391 | 2.571 | 3.206 | 3.374 | - | - | - |  |  | 0.080 | 0.076 | 3.799 | 3.174 | -0.046 | 6.036 | -0.209 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | couple_with_children | 1271 | 794 | False | False | 33.804 | 33.406 | 2.028 | 1.961 | 3.614 | 3.522 | - | - | - |  |  | 0.053 | 0.080 | -2.595 | -1.535 | 0.086 | -4.751 | -1.751 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | other | 103 | 53 | False | True | 36.712 | 42.079 | 2.269 | 2.327 | 3.708 | 3.319 | - | - | - |  |  | 0.103 | 0.126 | 1.492 | -2.561 | -0.067 | 1.701 | 0.471 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_parent | 397 | 282 | False | False | 35.772 | 35.903 | 2.093 | 1.928 | 3.511 | 3.222 | - | - | - |  |  | 0.076 | 0.062 | -1.499 | -0.511 | -0.066 | -5.562 | 1.558 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | household_type | single_person | 1553 | 1129 | False | False | 39.904 | 48.884 | 2.299 | 2.590 | 3.458 | 3.179 | - | - | - |  |  | 0.057 | 0.108 | 2.073 | 0.052 | -0.069 | 6.567 | 2.410 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | other | 2815 | 2017 | False | False | 42.965 | 48.189 | 2.352 | 2.627 | 3.286 | 3.271 | - | - | - |  |  | 0.060 | 0.099 | 3.067 | 2.104 | -0.053 | 7.137 | 1.145 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | unknown | 0 | 1 | True | True | - | - | - | - | - | - | - | - | - |  |  | - | - | - | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | day_purpose | work_study | 1688 | 1013 | False | False | 31.314 | 29.595 | 1.960 | 1.742 | 3.771 | 3.531 | - | - | - |  |  | 0.076 | 0.123 | -3.664 | -2.950 | 0.079 | -8.569 | -1.744 | 0.000 | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Mode-user composition

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| mode | n_2008 | n_2019 | ratio_before | ratio_after | lost_target_share | parent_fallback_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | 531 | 310 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | 9172 | 5926 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | 2345 | 1824 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | 712 | 390 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | 703 | 294 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | 1518 | 988 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | 4503 | 3029 | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Per-mode decomposition

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| mode | variant | delta | trips | distance | speed | selection | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bike | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| bike | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | published | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | rounded_crow_fly | - | - | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).

### Duration-rounding bounds

Scope: All days · all purposes · all trips in the day's trip table (incl. > 80 km) (`alldays-allpurp-daytable`), Monday–Friday.

| mode | lower_min | upper_min | unmatched_2008_trip_share | status |
| --- | --- | --- | --- | --- |
| bike | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_driver | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| car_passenger | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| other | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| train | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| urban_pt | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |
| walk | - | - | - | ENTD 2008 day-table coverage beyond 80 km not established; not compared |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.
The ENTD 2008 documentation does not guarantee coverage beyond 80 km; observed coverage is similar (Scope section).


## Reference-scope energy

### Unsupported-energy coverage

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| rate | unknown_energy_days_2008 | unknown_energy_days_2019 | unknown_energy_weight_share_2008 | unknown_energy_weight_share_2019 |
| --- | --- | --- | --- | --- |
| kh | 366 | 175 | 0.036 | 0.021 |
| cp | 366 | 175 | 0.036 | 0.021 |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Energy per travel day and per person

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| rate | grouping | cell | basis | n_2008 | n_2019 | mean_2008 | mean_2019 | ratio | ratio_low | ratio_high | verdict_15 | verdict_10 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kh | overall | all | travel_day | 13640 | 9243 | 386.942 | 415.539 | 1.074 | 1.045 | 1.104 | equivalent | inconclusive |  |
| kh | overall | all | person | 13640 | 9243 | 312.658 | 341.998 | 1.094 | 1.060 | 1.125 | equivalent | inconclusive |  |
| kh | population | children_6_17 | travel_day | 1091 | 820 | 319.181 | 314.461 | 0.985 | 0.898 | 1.084 | equivalent | inconclusive |  |
| kh | population | children_6_17 | person | 1091 | 820 | 277.733 | 272.272 | 0.980 | 0.891 | 1.102 | equivalent | inconclusive |  |
| kh | population | employed | travel_day | 7052 | 3977 | 407.318 | 452.542 | 1.111 | 1.072 | 1.150 | inconclusive | inconclusive |  |
| kh | population | employed | person | 7052 | 3977 | 363.455 | 414.096 | 1.139 | 1.089 | 1.187 | inconclusive | inconclusive |  |
| kh | population | other_inactive | travel_day | 1305 | 760 | 450.645 | 459.358 | 1.019 | 0.926 | 1.122 | equivalent | inconclusive |  |
| kh | population | other_inactive | person | 1305 | 760 | 336.101 | 352.651 | 1.049 | 0.955 | 1.177 | inconclusive | inconclusive |  |
| kh | population | retired | travel_day | 3600 | 3178 | 344.023 | 372.621 | 1.083 | 1.032 | 1.135 | equivalent | inconclusive |  |
| kh | population | retired | person | 3600 | 3178 | 224.862 | 255.129 | 1.135 | 1.068 | 1.204 | inconclusive | inconclusive |  |
| kh | population | unemployed | travel_day | 591 | 498 | 467.089 | 513.150 | 1.099 | 0.954 | 1.283 | inconclusive | inconclusive |  |
| kh | population | unemployed | person | 591 | 498 | 356.748 | 401.671 | 1.126 | 0.961 | 1.305 | inconclusive | inconclusive |  |
| kh | density | dense | travel_day | 1958 | 1271 | 523.587 | 554.230 | 1.059 | 1.002 | 1.123 | equivalent | inconclusive |  |
| kh | density | dense | person | 1958 | 1271 | 452.157 | 485.122 | 1.073 | 1.003 | 1.154 | inconclusive | inconclusive |  |
| kh | density | intermediate | travel_day | 5622 | 4265 | 412.667 | 443.411 | 1.075 | 1.031 | 1.115 | equivalent | inconclusive |  |
| kh | density | intermediate | person | 5622 | 4265 | 343.054 | 367.842 | 1.072 | 1.018 | 1.116 | equivalent | inconclusive |  |
| kh | density | sparse | travel_day | 1741 | 1497 | 336.976 | 329.037 | 0.976 | 0.901 | 1.044 | equivalent | equivalent |  |
| kh | density | sparse | person | 1741 | 1497 | 267.266 | 260.074 | 0.973 | 0.880 | 1.057 | equivalent | inconclusive |  |
| kh | density | very_sparse | travel_day | 4319 | 2210 | 289.621 | 329.068 | 1.136 | 1.078 | 1.210 | inconclusive | inconclusive |  |
| kh | density | very_sparse | person | 4319 | 2210 | 216.638 | 264.410 | 1.221 | 1.150 | 1.303 | different | different |  |
| kh | income | q1 | travel_day | 2186 | 1591 | 423.083 | 435.408 | 1.029 | 0.962 | 1.111 | equivalent | inconclusive |  |
| kh | income | q1 | person | 2186 | 1591 | 311.090 | 331.762 | 1.066 | 0.990 | 1.168 | inconclusive | inconclusive |  |
| kh | income | q2 | travel_day | 2277 | 1799 | 356.952 | 396.408 | 1.111 | 1.042 | 1.182 | inconclusive | inconclusive |  |
| kh | income | q2 | person | 2277 | 1799 | 282.115 | 316.308 | 1.121 | 1.043 | 1.207 | inconclusive | inconclusive |  |
| kh | income | q3 | travel_day | 2683 | 1813 | 359.834 | 385.684 | 1.072 | 1.012 | 1.134 | equivalent | inconclusive |  |
| kh | income | q3 | person | 2683 | 1813 | 291.214 | 311.187 | 1.069 | 0.998 | 1.142 | equivalent | inconclusive |  |
| kh | income | q4 | travel_day | 2799 | 1968 | 376.969 | 410.427 | 1.089 | 1.021 | 1.143 | equivalent | inconclusive |  |
| kh | income | q4 | person | 2799 | 1968 | 321.692 | 355.468 | 1.105 | 1.025 | 1.175 | inconclusive | inconclusive |  |
| kh | income | q5 | travel_day | 3695 | 2072 | 419.347 | 447.657 | 1.068 | 1.015 | 1.119 | equivalent | inconclusive |  |
| kh | income | q5 | person | 3695 | 2072 | 357.825 | 395.516 | 1.105 | 1.044 | 1.178 | inconclusive | inconclusive |  |
| kh | vehicles | 0 | travel_day | 1976 | 1351 | 569.803 | 584.825 | 1.026 | 0.971 | 1.096 | equivalent | equivalent |  |
| kh | vehicles | 0 | person | 1976 | 1351 | 405.488 | 413.663 | 1.020 | 0.943 | 1.106 | equivalent | inconclusive |  |
| kh | vehicles | 1 | travel_day | 5258 | 3864 | 398.917 | 409.296 | 1.026 | 0.979 | 1.075 | equivalent | equivalent |  |
| kh | vehicles | 1 | person | 5258 | 3864 | 315.869 | 331.585 | 1.050 | 0.991 | 1.103 | equivalent | inconclusive |  |
| kh | vehicles | 2+ | travel_day | 6406 | 4005 | 335.168 | 374.218 | 1.117 | 1.066 | 1.157 | inconclusive | inconclusive |  |
| kh | vehicles | 2+ | person | 6406 | 4005 | 284.312 | 326.294 | 1.148 | 1.092 | 1.197 | inconclusive | inconclusive |  |
| kh | vehicles | unknown | travel_day | 0 | 23 | - | - | - | - | - |  |  | small cell hidden |
| kh | vehicles | unknown | person | 0 | 23 | - | - | - | - | - |  |  | small cell hidden |
| kh | day_mode_group | car_driver | travel_day | 7632 | 5132 | 332.761 | 370.198 | 1.113 | 1.076 | 1.150 | inconclusive | inconclusive |  |
| kh | day_mode_group | car_driver | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | car_passenger_carpool | travel_day | 361 | 364 | 272.271 | 244.635 | 0.898 | 0.699 | 1.108 | inconclusive | inconclusive |  |
| kh | day_mode_group | car_passenger_carpool | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | car_passenger_household | travel_day | 887 | 781 | 188.469 | 211.748 | 1.124 | 0.950 | 1.291 | inconclusive | inconclusive |  |
| kh | day_mode_group | car_passenger_household | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | cycle | travel_day | 265 | 154 | 622.820 | 707.133 | 1.135 | 0.952 | 1.356 | inconclusive | inconclusive |  |
| kh | day_mode_group | cycle | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | multimodal | travel_day | 1188 | 741 | 440.235 | 487.183 | 1.107 | 1.031 | 1.192 | inconclusive | inconclusive |  |
| kh | day_mode_group | multimodal | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | other | travel_day | 50 | 23 | 279.278 | - | - | - | - |  |  | small cell hidden |
| kh | day_mode_group | other | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | train | travel_day | 382 | 150 | 777.270 | 826.133 | 1.063 | 0.945 | 1.216 | inconclusive | inconclusive |  |
| kh | day_mode_group | train | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | unknown | travel_day | 0 | 0 | - | - | - | - | - |  |  | small cell hidden |
| kh | day_mode_group | unknown | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | urban_pt | travel_day | 1044 | 700 | 613.212 | 624.536 | 1.018 | 0.954 | 1.091 | equivalent | equivalent |  |
| kh | day_mode_group | urban_pt | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | day_mode_group | walking_only | travel_day | 1831 | 1198 | 491.258 | 473.240 | 0.963 | 0.904 | 1.024 | equivalent | equivalent |  |
| kh | day_mode_group | walking_only | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| kh | mode | bike | person | 401 | 253 | 13.885 | 14.123 | 1.017 | 0.816 | 1.263 | inconclusive | inconclusive |  |
| kh | mode | car_driver | person | 8336 | 5573 | 140.514 | 151.929 | 1.081 | 1.036 | 1.120 | equivalent | inconclusive |  |
| kh | mode | car_passenger | person | 2025 | 1628 | 15.624 | 18.555 | 1.188 | 1.047 | 1.337 | inconclusive | inconclusive |  |
| kh | mode | other | person | 0 | 0 | - | - | - | - | - |  |  | mode energy unavailable |
| kh | mode | train | person | 559 | 241 | 15.552 | 19.424 | 1.249 | 1.013 | 1.487 | inconclusive | inconclusive |  |
| kh | mode | urban_pt | person | 1397 | 915 | 32.746 | 44.185 | 1.349 | 1.190 | 1.522 | different | different |  |
| kh | mode | walk | person | 3635 | 2407 | - | 93.781 | - | - | - |  |  | mode energy unavailable |
| cp | overall | all | travel_day | 13640 | 9243 | 381.154 | 406.352 | 1.066 | 1.041 | 1.092 | equivalent | equivalent |  |
| cp | overall | all | person | 13640 | 9243 | 307.980 | 334.437 | 1.086 | 1.056 | 1.116 | equivalent | inconclusive |  |
| cp | population | children_6_17 | travel_day | 1091 | 820 | 267.489 | 263.212 | 0.984 | 0.905 | 1.078 | equivalent | equivalent |  |
| cp | population | children_6_17 | person | 1091 | 820 | 232.754 | 227.899 | 0.979 | 0.894 | 1.094 | equivalent | inconclusive |  |
| cp | population | employed | travel_day | 7052 | 3977 | 425.964 | 468.991 | 1.101 | 1.065 | 1.135 | equivalent | inconclusive |  |
| cp | population | employed | person | 7052 | 3977 | 380.093 | 429.148 | 1.129 | 1.081 | 1.171 | inconclusive | inconclusive |  |
| cp | population | other_inactive | travel_day | 1305 | 760 | 409.721 | 415.741 | 1.015 | 0.933 | 1.102 | equivalent | inconclusive |  |
| cp | population | other_inactive | person | 1305 | 760 | 305.579 | 319.166 | 1.044 | 0.951 | 1.169 | inconclusive | inconclusive |  |
| cp | population | retired | travel_day | 3600 | 3178 | 336.122 | 358.917 | 1.068 | 1.024 | 1.116 | equivalent | inconclusive |  |
| cp | population | retired | person | 3600 | 3178 | 219.698 | 245.747 | 1.119 | 1.054 | 1.185 | inconclusive | inconclusive |  |
| cp | population | unemployed | travel_day | 591 | 498 | 428.925 | 478.005 | 1.114 | 0.985 | 1.279 | inconclusive | inconclusive |  |
| cp | population | unemployed | person | 591 | 498 | 327.600 | 374.161 | 1.142 | 0.983 | 1.319 | inconclusive | inconclusive |  |
| cp | density | dense | travel_day | 1958 | 1271 | 463.323 | 487.002 | 1.051 | 0.995 | 1.110 | equivalent | inconclusive |  |
| cp | density | dense | person | 1958 | 1271 | 400.114 | 426.277 | 1.065 | 1.001 | 1.140 | equivalent | inconclusive |  |
| cp | density | intermediate | travel_day | 5622 | 4265 | 396.787 | 426.149 | 1.074 | 1.033 | 1.111 | equivalent | inconclusive |  |
| cp | density | intermediate | person | 5622 | 4265 | 329.853 | 353.522 | 1.072 | 1.020 | 1.114 | equivalent | inconclusive |  |
| cp | density | sparse | travel_day | 1741 | 1497 | 346.654 | 341.531 | 0.985 | 0.910 | 1.051 | equivalent | equivalent |  |
| cp | density | sparse | person | 1741 | 1497 | 274.942 | 269.950 | 0.982 | 0.890 | 1.059 | equivalent | inconclusive |  |
| cp | density | very_sparse | travel_day | 4319 | 2210 | 325.610 | 361.175 | 1.109 | 1.059 | 1.172 | inconclusive | inconclusive |  |
| cp | density | very_sparse | person | 4319 | 2210 | 243.558 | 290.209 | 1.192 | 1.123 | 1.263 | inconclusive | different |  |
| cp | income | q1 | travel_day | 2186 | 1591 | 383.553 | 393.070 | 1.025 | 0.973 | 1.102 | equivalent | inconclusive |  |
| cp | income | q1 | person | 2186 | 1591 | 282.024 | 299.502 | 1.062 | 0.991 | 1.151 | inconclusive | inconclusive |  |
| cp | income | q2 | travel_day | 2277 | 1799 | 349.617 | 382.016 | 1.093 | 1.026 | 1.154 | inconclusive | inconclusive |  |
| cp | income | q2 | person | 2277 | 1799 | 276.318 | 304.823 | 1.103 | 1.031 | 1.185 | inconclusive | inconclusive |  |
| cp | income | q3 | travel_day | 2683 | 1813 | 363.156 | 388.871 | 1.071 | 1.014 | 1.126 | equivalent | inconclusive |  |
| cp | income | q3 | person | 2683 | 1813 | 293.903 | 313.758 | 1.068 | 0.996 | 1.136 | equivalent | inconclusive |  |
| cp | income | q4 | travel_day | 2799 | 1968 | 381.854 | 415.282 | 1.088 | 1.032 | 1.139 | equivalent | inconclusive |  |
| cp | income | q4 | person | 2799 | 1968 | 325.861 | 359.672 | 1.104 | 1.029 | 1.167 | inconclusive | inconclusive |  |
| cp | income | q5 | travel_day | 3695 | 2072 | 425.171 | 447.276 | 1.052 | 1.007 | 1.099 | equivalent | equivalent |  |
| cp | income | q5 | person | 3695 | 2072 | 362.794 | 395.179 | 1.089 | 1.032 | 1.161 | inconclusive | inconclusive |  |
| cp | vehicles | 0 | travel_day | 1976 | 1351 | 467.203 | 482.101 | 1.032 | 0.975 | 1.105 | equivalent | inconclusive |  |
| cp | vehicles | 0 | person | 1976 | 1351 | 332.476 | 341.004 | 1.026 | 0.948 | 1.115 | equivalent | inconclusive |  |
| cp | vehicles | 1 | travel_day | 5258 | 3864 | 386.078 | 393.940 | 1.020 | 0.979 | 1.062 | equivalent | equivalent |  |
| cp | vehicles | 1 | person | 5258 | 3864 | 305.703 | 319.145 | 1.044 | 0.992 | 1.094 | equivalent | equivalent |  |
| cp | vehicles | 2+ | travel_day | 6406 | 4005 | 357.347 | 394.979 | 1.105 | 1.063 | 1.142 | equivalent | inconclusive |  |
| cp | vehicles | 2+ | person | 6406 | 4005 | 303.126 | 344.396 | 1.136 | 1.085 | 1.182 | inconclusive | inconclusive |  |
| cp | vehicles | unknown | travel_day | 0 | 23 | - | - | - | - | - |  |  | small cell hidden |
| cp | vehicles | unknown | person | 0 | 23 | - | - | - | - | - |  |  | small cell hidden |
| cp | day_mode_group | car_driver | travel_day | 7632 | 5132 | 383.219 | 420.185 | 1.096 | 1.066 | 1.134 | equivalent | inconclusive |  |
| cp | day_mode_group | car_driver | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | car_passenger_carpool | travel_day | 361 | 364 | 229.203 | 211.288 | 0.922 | 0.732 | 1.119 | inconclusive | inconclusive |  |
| cp | day_mode_group | car_passenger_carpool | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | car_passenger_household | travel_day | 887 | 781 | 162.761 | 182.614 | 1.122 | 0.963 | 1.274 | inconclusive | inconclusive |  |
| cp | day_mode_group | car_passenger_household | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | cycle | travel_day | 265 | 154 | 605.125 | 688.461 | 1.138 | 0.953 | 1.358 | inconclusive | inconclusive |  |
| cp | day_mode_group | cycle | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | multimodal | travel_day | 1188 | 741 | 423.052 | 458.816 | 1.085 | 1.015 | 1.163 | inconclusive | inconclusive |  |
| cp | day_mode_group | multimodal | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | other | travel_day | 50 | 23 | 213.182 | - | - | - | - |  |  | small cell hidden |
| cp | day_mode_group | other | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | train | travel_day | 382 | 150 | 655.411 | 701.296 | 1.070 | 0.957 | 1.219 | inconclusive | inconclusive |  |
| cp | day_mode_group | train | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | unknown | travel_day | 0 | 0 | - | - | - | - | - |  |  | small cell hidden |
| cp | day_mode_group | unknown | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | urban_pt | travel_day | 1044 | 700 | 505.186 | 513.947 | 1.017 | 0.955 | 1.088 | equivalent | equivalent |  |
| cp | day_mode_group | urban_pt | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | day_mode_group | walking_only | travel_day | 1831 | 1198 | 374.993 | 361.240 | 0.963 | 0.904 | 1.024 | equivalent | equivalent |  |
| cp | day_mode_group | walking_only | person | - | - | - | - | - | - | - |  |  | not defined: days without trips have no mode group |
| cp | mode | bike | person | 401 | 253 | 13.890 | 14.126 | 1.017 | 0.816 | 1.262 | inconclusive | inconclusive |  |
| cp | mode | car_driver | person | 8336 | 5573 | 166.594 | 177.838 | 1.067 | 1.027 | 1.106 | equivalent | inconclusive |  |
| cp | mode | car_passenger | person | 2025 | 1628 | 14.623 | 17.307 | 1.183 | 1.058 | 1.310 | inconclusive | inconclusive |  |
| cp | mode | other | person | 0 | 0 | - | - | - | - | - |  |  | mode energy unavailable |
| cp | mode | train | person | 559 | 241 | 13.302 | 16.607 | 1.248 | 1.020 | 1.487 | inconclusive | inconclusive |  |
| cp | mode | urban_pt | person | 1397 | 915 | 27.560 | 36.973 | 1.342 | 1.186 | 1.511 | different | different |  |
| cp | mode | walk | person | 3635 | 2407 | - | 71.587 | - | - | - |  |  | mode energy unavailable |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.



## Collapse test

### Median pairwise KS

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| year | rate | n_pairs | time_ks | time_ks_low | time_ks_high | energy_ks | energy_ks_low | energy_ks_high | comparison | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2008 | kh | 15 | 0.384 | 0.360 | 0.427 | 0.368 | 0.340 | 0.448 | closer |  |
| 2019 | kh | 15 | 0.389 | 0.370 | 0.430 | 0.327 | 0.280 | 0.444 | closer |  |
| 2008 | cp | 15 | 0.384 | 0.360 | 0.427 | 0.395 | 0.353 | 0.441 | not closer |  |
| 2019 | cp | 15 | 0.389 | 0.370 | 0.430 | 0.355 | 0.296 | 0.431 | closer |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


### Pairwise and cross-year KS

Scope: Round-trip days · destination purposes · local (≤ 80 km) (`round-dest-local`), Monday–Friday.

| kind | year | rate | mode_a | mode_b | time_ks | time_ks_low | time_ks_high | energy_ks | energy_ks_low | energy_ks_high | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| within_year_pair | 2008 | kh | bike | car_driver | 0.287 | 0.215 | 0.372 | 0.345 | 0.290 | 0.397 |  |
| within_year_pair | 2008 | kh | bike | car_passenger | 0.042 | 0.045 | 0.133 | 0.701 | 0.661 | 0.762 |  |
| within_year_pair | 2008 | kh | bike | other | 0.276 | 0.203 | 0.378 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | bike | train | 0.675 | 0.602 | 0.748 | 0.347 | 0.253 | 0.440 |  |
| within_year_pair | 2008 | kh | bike | urban_pt | 0.419 | 0.359 | 0.514 | 0.146 | 0.103 | 0.235 |  |
| within_year_pair | 2008 | kh | bike | walk | 0.158 | 0.106 | 0.223 | 0.242 | 0.178 | 0.300 |  |
| within_year_pair | 2008 | kh | car_driver | car_passenger | 0.260 | 0.226 | 0.300 | 0.560 | 0.532 | 0.588 |  |
| within_year_pair | 2008 | kh | car_driver | other | 0.041 | 0.034 | 0.101 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | car_driver | train | 0.495 | 0.442 | 0.559 | 0.556 | 0.512 | 0.606 |  |
| within_year_pair | 2008 | kh | car_driver | urban_pt | 0.145 | 0.120 | 0.196 | 0.227 | 0.190 | 0.273 |  |
| within_year_pair | 2008 | kh | car_driver | walk | 0.372 | 0.351 | 0.401 | 0.175 | 0.151 | 0.207 |  |
| within_year_pair | 2008 | kh | car_passenger | other | 0.248 | 0.195 | 0.323 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | car_passenger | train | 0.652 | 0.614 | 0.706 | 0.871 | 0.849 | 0.903 |  |
| within_year_pair | 2008 | kh | car_passenger | urban_pt | 0.384 | 0.348 | 0.439 | 0.684 | 0.651 | 0.726 |  |
| within_year_pair | 2008 | kh | car_passenger | walk | 0.174 | 0.128 | 0.216 | 0.651 | 0.618 | 0.679 |  |
| within_year_pair | 2008 | kh | other | train | 0.484 | 0.433 | 0.567 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | other | urban_pt | 0.159 | 0.106 | 0.239 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | other | walk | 0.386 | 0.336 | 0.441 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | kh | train | urban_pt | 0.397 | 0.346 | 0.476 | 0.368 | 0.319 | 0.438 |  |
| within_year_pair | 2008 | kh | train | walk | 0.746 | 0.716 | 0.784 | 0.417 | 0.388 | 0.467 |  |
| within_year_pair | 2008 | kh | urban_pt | walk | 0.504 | 0.478 | 0.557 | 0.153 | 0.114 | 0.190 |  |
| within_year_pair | 2019 | kh | bike | car_driver | 0.306 | 0.243 | 0.386 | 0.236 | 0.181 | 0.333 |  |
| within_year_pair | 2019 | kh | bike | car_passenger | 0.074 | 0.048 | 0.174 | 0.673 | 0.643 | 0.727 |  |
| within_year_pair | 2019 | kh | bike | other | 0.259 | 0.182 | 0.379 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | bike | train | 0.664 | 0.569 | 0.756 | 0.327 | 0.231 | 0.444 |  |
| within_year_pair | 2019 | kh | bike | urban_pt | 0.461 | 0.390 | 0.544 | 0.130 | 0.090 | 0.202 |  |
| within_year_pair | 2019 | kh | bike | walk | 0.139 | 0.085 | 0.219 | 0.220 | 0.195 | 0.272 |  |
| within_year_pair | 2019 | kh | car_driver | car_passenger | 0.247 | 0.219 | 0.286 | 0.542 | 0.513 | 0.571 |  |
| within_year_pair | 2019 | kh | car_driver | other | 0.108 | 0.062 | 0.172 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | car_driver | train | 0.467 | 0.396 | 0.547 | 0.520 | 0.449 | 0.597 |  |
| within_year_pair | 2019 | kh | car_driver | urban_pt | 0.157 | 0.120 | 0.196 | 0.242 | 0.201 | 0.290 |  |
| within_year_pair | 2019 | kh | car_driver | walk | 0.389 | 0.371 | 0.415 | 0.139 | 0.112 | 0.165 |  |
| within_year_pair | 2019 | kh | car_passenger | other | 0.195 | 0.145 | 0.284 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | car_passenger | train | 0.616 | 0.529 | 0.685 | 0.801 | 0.771 | 0.866 |  |
| within_year_pair | 2019 | kh | car_passenger | urban_pt | 0.400 | 0.369 | 0.443 | 0.642 | 0.610 | 0.681 |  |
| within_year_pair | 2019 | kh | car_passenger | walk | 0.177 | 0.144 | 0.218 | 0.516 | 0.487 | 0.552 |  |
| within_year_pair | 2019 | kh | other | train | 0.538 | 0.449 | 0.623 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | other | urban_pt | 0.253 | 0.185 | 0.328 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | other | walk | 0.366 | 0.312 | 0.441 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | kh | train | urban_pt | 0.389 | 0.310 | 0.467 | 0.309 | 0.234 | 0.400 |  |
| within_year_pair | 2019 | kh | train | walk | 0.705 | 0.625 | 0.775 | 0.469 | 0.395 | 0.543 |  |
| within_year_pair | 2019 | kh | urban_pt | walk | 0.543 | 0.509 | 0.585 | 0.207 | 0.171 | 0.258 |  |
| across_year_mode |  | kh | bike | bike | 0.061 | 0.058 | 0.168 | 0.098 | 0.077 | 0.197 |  |
| across_year_mode |  | kh | car_driver | car_driver | 0.052 | 0.037 | 0.074 | 0.061 | 0.048 | 0.086 |  |
| across_year_mode |  | kh | car_passenger | car_passenger | 0.064 | 0.041 | 0.098 | 0.063 | 0.044 | 0.111 |  |
| across_year_mode |  | kh | other | other | 0.062 | 0.047 | 0.157 | - | - | - | mode energy unavailable or hidden |
| across_year_mode |  | kh | train | train | 0.089 | 0.067 | 0.185 | 0.086 | 0.082 | 0.169 |  |
| across_year_mode |  | kh | urban_pt | urban_pt | 0.073 | 0.042 | 0.133 | 0.111 | 0.064 | 0.172 |  |
| across_year_mode |  | kh | walk | walk | 0.028 | 0.021 | 0.059 | 0.082 | 0.063 | 0.117 |  |
| within_year_pair | 2008 | cp | bike | car_driver | 0.287 | 0.215 | 0.372 | 0.231 | 0.192 | 0.297 |  |
| within_year_pair | 2008 | cp | bike | car_passenger | 0.042 | 0.045 | 0.133 | 0.714 | 0.670 | 0.767 |  |
| within_year_pair | 2008 | cp | bike | other | 0.276 | 0.203 | 0.378 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | bike | train | 0.675 | 0.602 | 0.748 | 0.266 | 0.185 | 0.365 |  |
| within_year_pair | 2008 | cp | bike | urban_pt | 0.419 | 0.359 | 0.514 | 0.243 | 0.193 | 0.319 |  |
| within_year_pair | 2008 | cp | bike | walk | 0.158 | 0.106 | 0.223 | 0.356 | 0.295 | 0.413 |  |
| within_year_pair | 2008 | cp | car_driver | car_passenger | 0.260 | 0.226 | 0.300 | 0.632 | 0.609 | 0.661 |  |
| within_year_pair | 2008 | cp | car_driver | other | 0.041 | 0.034 | 0.101 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | car_driver | train | 0.495 | 0.442 | 0.559 | 0.399 | 0.358 | 0.451 |  |
| within_year_pair | 2008 | cp | car_driver | urban_pt | 0.145 | 0.120 | 0.196 | 0.078 | 0.054 | 0.120 |  |
| within_year_pair | 2008 | cp | car_driver | walk | 0.372 | 0.351 | 0.401 | 0.169 | 0.144 | 0.196 |  |
| within_year_pair | 2008 | cp | car_passenger | other | 0.248 | 0.195 | 0.323 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | car_passenger | train | 0.652 | 0.614 | 0.706 | 0.862 | 0.836 | 0.893 |  |
| within_year_pair | 2008 | cp | car_passenger | urban_pt | 0.384 | 0.348 | 0.439 | 0.671 | 0.638 | 0.714 |  |
| within_year_pair | 2008 | cp | car_passenger | walk | 0.174 | 0.128 | 0.216 | 0.563 | 0.529 | 0.599 |  |
| within_year_pair | 2008 | cp | other | train | 0.484 | 0.433 | 0.567 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | other | urban_pt | 0.159 | 0.106 | 0.239 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | other | walk | 0.386 | 0.336 | 0.441 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2008 | cp | train | urban_pt | 0.397 | 0.346 | 0.476 | 0.395 | 0.344 | 0.453 |  |
| within_year_pair | 2008 | cp | train | walk | 0.746 | 0.716 | 0.784 | 0.490 | 0.447 | 0.536 |  |
| within_year_pair | 2008 | cp | urban_pt | walk | 0.504 | 0.478 | 0.557 | 0.184 | 0.161 | 0.234 |  |
| within_year_pair | 2019 | cp | bike | car_driver | 0.306 | 0.243 | 0.386 | 0.168 | 0.115 | 0.257 |  |
| within_year_pair | 2019 | cp | bike | car_passenger | 0.074 | 0.048 | 0.174 | 0.680 | 0.649 | 0.747 |  |
| within_year_pair | 2019 | cp | bike | other | 0.259 | 0.182 | 0.379 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | bike | train | 0.664 | 0.569 | 0.756 | 0.267 | 0.171 | 0.389 |  |
| within_year_pair | 2019 | cp | bike | urban_pt | 0.461 | 0.390 | 0.544 | 0.200 | 0.135 | 0.269 |  |
| within_year_pair | 2019 | cp | bike | walk | 0.139 | 0.085 | 0.219 | 0.303 | 0.252 | 0.387 |  |
| within_year_pair | 2019 | cp | car_driver | car_passenger | 0.247 | 0.219 | 0.286 | 0.613 | 0.589 | 0.641 |  |
| within_year_pair | 2019 | cp | car_driver | other | 0.108 | 0.062 | 0.172 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | car_driver | train | 0.467 | 0.396 | 0.547 | 0.379 | 0.302 | 0.452 |  |
| within_year_pair | 2019 | cp | car_driver | urban_pt | 0.157 | 0.120 | 0.196 | 0.067 | 0.047 | 0.116 |  |
| within_year_pair | 2019 | cp | car_driver | walk | 0.389 | 0.371 | 0.415 | 0.209 | 0.187 | 0.239 |  |
| within_year_pair | 2019 | cp | car_passenger | other | 0.195 | 0.145 | 0.284 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | car_passenger | train | 0.616 | 0.529 | 0.685 | 0.789 | 0.756 | 0.857 |  |
| within_year_pair | 2019 | cp | car_passenger | urban_pt | 0.400 | 0.369 | 0.443 | 0.625 | 0.593 | 0.667 |  |
| within_year_pair | 2019 | cp | car_passenger | walk | 0.177 | 0.144 | 0.218 | 0.465 | 0.432 | 0.500 |  |
| within_year_pair | 2019 | cp | other | train | 0.538 | 0.449 | 0.623 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | other | urban_pt | 0.253 | 0.185 | 0.328 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | other | walk | 0.366 | 0.312 | 0.441 | - | - | - | mode energy unavailable or hidden |
| within_year_pair | 2019 | cp | train | urban_pt | 0.389 | 0.310 | 0.467 | 0.355 | 0.268 | 0.438 |  |
| within_year_pair | 2019 | cp | train | walk | 0.705 | 0.625 | 0.775 | 0.535 | 0.450 | 0.608 |  |
| within_year_pair | 2019 | cp | urban_pt | walk | 0.543 | 0.509 | 0.585 | 0.249 | 0.221 | 0.304 |  |
| across_year_mode |  | cp | bike | bike | 0.061 | 0.058 | 0.168 | 0.098 | 0.078 | 0.197 |  |
| across_year_mode |  | cp | car_driver | car_driver | 0.052 | 0.037 | 0.074 | 0.057 | 0.043 | 0.083 |  |
| across_year_mode |  | cp | car_passenger | car_passenger | 0.064 | 0.041 | 0.098 | 0.066 | 0.045 | 0.110 |  |
| across_year_mode |  | cp | other | other | 0.062 | 0.047 | 0.157 | - | - | - | mode energy unavailable or hidden |
| across_year_mode |  | cp | train | train | 0.089 | 0.067 | 0.185 | 0.075 | 0.078 | 0.174 |  |
| across_year_mode |  | cp | urban_pt | urban_pt | 0.073 | 0.042 | 0.133 | 0.115 | 0.068 | 0.177 |  |
| across_year_mode |  | cp | walk | walk | 0.028 | 0.021 | 0.059 | 0.082 | 0.063 | 0.117 |  |

n is the unweighted count shown in each row; sources: ENTD 2008 and EMP 2019 cached scoped weekday tables, section 9.9.


