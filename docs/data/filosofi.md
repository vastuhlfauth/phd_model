# Filosofi

- **Source:** INSEE, Filosofi 2021, metropolitan, Martinique and La Réunion
  grid files. [Dataset and documentation](https://www.insee.fr/fr/statistiques/8735162).
- **Vintage(s):** income and household data for 2019 (temporal-test inputs)
  and 2021.
- **Local path:** `data/raw/filosofi/{2019,2021}/`.
- **CRS:** EPSG:3035, encoded by the cell identifiers.
- **Keys and joins:** `idcar_nat` links the natural-level table to
  `idcar_nat` on each 200 m row. `idcar_200m` and `idcar_1km` are INSPIRE
  cell identifiers. The 2021 `lcog_geo` field is a comma-separated list of
  the intersecting 2021 commune codes, ordered by intersection area
  (INSEE documentation).

## Files and row counts

The 2021 ZIP archives contain these CSV members:

| Scale | File/member | Rows |
|---|---|---:|
| Natural | `carreaux_nivNaturel_met.csv` | 145,197 |
| Natural | `carreaux_nivNaturel_mart.csv` | 620 |
| Natural | `carreaux_nivNaturel_reun.csv` | 824 |
| 200 m | `carreaux_200m_met.csv` | 2,298,582 |
| 200 m | `carreaux_200m_mart.csv` | 11,222 |
| 200 m | `carreaux_200m_reun.csv` | 14,773 |

The France totals across the three files are 146,641 natural-level rows and
2,324,577 200 m rows. ZIP sizes are 7,211,131 bytes (natural) and 91,614,618
bytes (200 m).

The 2019 archives are
`Filosofi2019_carreaux_nivNaturel_csv.zip` (6,282,711 bytes) and
`Filosofi2019_carreaux_200m_csv.zip` (61,770,743 bytes). Each contains a
nested `.7z`, which in turn contains the same `met`, `mart` and `reun` CSV
member names as the 2021 archive. The extracted 2019 metropolitan CSV schemas
have the same column names and DuckDB types as their 2021 equivalents; no
column differences were found.

The `lcog_geo` column uses different list formats: 2019 concatenates
five-character codes without separators, while 2021 separates them with
commas. Codes must be read as strings, including leading zeroes and Corsican
letters. In Gironde the corrected 2019 interpretation reaches 3,884 natural
cells, versus 3,870 using only the first code.

## Columns: natural-level CSV

`carreaux_nivNaturel_{met,mart,reun}.csv` (2021 and 2019):

| Column(s) | Type | Unit / meaning |
|---|---|---|
| `idcar_nat` | `VARCHAR` | Natural-level cell identifier; embeds CRS3035 resolution and grid corner |
| `tmaille` | `BIGINT` | Cell side length, metres |
| `ind`, `men`, `men_pauv`, `men_1ind`, `men_5ind`, `men_prop`, `men_fmp`, `ind_snv`, `men_surf`, `men_coll`, `men_mais`, `log_av45`, `log_45_70`, `log_70_90`, `log_ap90`, `log_inc`, `log_soc`, `ind_0_3`, `ind_4_5`, `ind_6_10`, `ind_11_17`, `ind_18_24`, `ind_25_39`, `ind_40_54`, `ind_55_64`, `ind_65_79`, `ind_80p`, `ind_inc` | `DOUBLE` | Filosofi population, household, dwelling and income aggregates; `ind` is individuals and `men` is households |

The side length and lower-left corner can be decoded from `idcar_nat` itself:
the identifier uses `CRS3035RES{metres}mN{northing}E{easting}`. `tmaille`
provides the same resolution explicitly. The 200 m file also provides the
natural-level identifier for every row: all 2,298,582 metropolitan rows have
`idcar_nat`, representing 145,197 distinct natural-level cells.

## Columns: 200 m CSV

`carreaux_200m_{met,mart,reun}.csv` (2021 and 2019):

| Column(s) | Type | Unit / meaning |
|---|---|---|
| `idcar_200m`, `idcar_1km`, `idcar_nat`, `lcog_geo` | `VARCHAR` | 200 m cell id, containing 1 km cell id, containing natural cell id, and intersecting commune code list |
| `i_est_200`, `i_est_1km` | `BIGINT` | Imputation indicators |
| `ind`, `men`, `men_pauv`, `men_1ind`, `men_5ind`, `men_prop`, `men_fmp`, `ind_snv`, `men_surf`, `men_coll`, `men_mais`, `log_av45`, `log_45_70`, `log_70_90`, `log_ap90`, `log_inc`, `log_soc`, `ind_0_3`, `ind_4_5`, `ind_6_10`, `ind_11_17`, `ind_18_24`, `ind_25_39`, `ind_40_54`, `ind_55_64`, `ind_65_79`, `ind_80p`, `ind_inc` | `DOUBLE` | Filosofi population, household, dwelling and income aggregates; `ind` is individuals and `men` is households |

INSEE defines `i_est_200 = 1` when the 200 m cell has an approximate imputed
value, and `0` otherwise. The imputation addresses cells below the
confidentiality threshold of 11 fiscal households. In metropolitan France,
1,809,025 rows have `i_est_200 = 1` and 489,557 have `i_est_200 = 0`
(78.7% imputed).

## Department-33 cells and checks

`lcog_geo` identifies every commune intersected by a 200 m cell, so
department-33 rows were selected when that list contained a `33xxx` commune
code. This yields 55,040 metropolitan 200 m cells, with 735,421.1 households
and 1,608,006.5 individuals. Of these, 41,052 are imputed and 13,988 are not.

Natural-level rows reached by those 200 m cells, by cell side:

| Side (m) | Cells | Households | Individuals |
|---:|---:|---:|---:|
| 200 | 1,067 | 119,859.0 | 233,018.0 |
| 1,000 | 1,870 | 425,601.6 | 941,060.5 |
| 2,000 | 846 | 107,823.6 | 251,142.5 |
| 4,000 | 125 | 31,458.8 | 76,422.0 |
| 8,000 | 40 | 25,538.7 | 56,871.0 |
| 16,000 | 5 | 35,500.6 | 71,393.5 |

At least 157 natural-level cells have 200 m records whose `lcog_geo` lists
both a department-33 commune and a commune outside department 33. Those
whole natural-level cells contain 19,450.2 households. This is a lower bound
on geometric straddlers: unpopulated 200 m subcells have no row in this file,
so this link-only test cannot prove that no additional natural-level square
crosses the boundary.

For all 145,197 metropolitan natural-level cells, the sums of 200 m
`ind` and `men` match their natural-level values. The maximum absolute
individual gap is 0; the maximum household gap is approximately
0.0000000015 (both are zero to six decimal places).

## Sample

First 20 metropolitan rows returned by DuckDB, limited to identifiers,
imputation flag, individuals and households:

### Natural-level

| `idcar_nat` | `tmaille` | `ind` | `men` |
|---|---:|---:|---:|
| `CRS3035RES1000mN2034000E4252000` | 1000 | 160.0 | 63.3 |
| `CRS3035RES1000mN2034000E4253000` | 1000 | 45.0 | 22.1 |
| `CRS3035RES1000mN2035000E4252000` | 1000 | 91.5 | 37.0 |
| `CRS3035RES1000mN2035000E4253000` | 1000 | 58.0 | 25.9 |
| `CRS3035RES1000mN2044000E4253000` | 1000 | 78.5 | 41.9 |
| `CRS3035RES1000mN2045000E4253000` | 1000 | 69.0 | 33.0 |
| `CRS3035RES1000mN2052000E4250000` | 1000 | 49.0 | 23.1 |
| `CRS3035RES1000mN2052000E4251000` | 1000 | 67.0 | 28.9 |
| `CRS3035RES1000mN2054000E4253000` | 1000 | 68.5 | 28.9 |
| `CRS3035RES1000mN2054000E4254000` | 1000 | 419.0 | 198.0 |
| `CRS3035RES1000mN2054000E4255000` | 1000 | 160.5 | 63.0 |
| `CRS3035RES1000mN2054000E4260000` | 1000 | 1,631.5 | 820.0 |
| `CRS3035RES1000mN2054000E4261000` | 1000 | 192.0 | 108.0 |
| `CRS3035RES1000mN2055000E4253000` | 1000 | 110.5 | 66.1 |
| `CRS3035RES1000mN2055000E4254000` | 1000 | 45.0 | 16.9 |
| `CRS3035RES1000mN2055000E4255000` | 1000 | 39.5 | 15.9 |
| `CRS3035RES1000mN2055000E4260000` | 1000 | 681.0 | 310.3 |
| `CRS3035RES1000mN2055000E4261000` | 1000 | 26.0 | 14.9 |
| `CRS3035RES1000mN2056000E4260000` | 1000 | 406.5 | 193.0 |
| `CRS3035RES1000mN2056000E4261000` | 1000 | 89.0 | 39.0 |

### 200 m

| `idcar_200m` | `idcar_nat` | `i_est_200` | `ind` | `men` |
|---|---|---:|---:|---:|
| `CRS3035RES200mN2029400E4259000` | `CRS3035RES32000mN2016000E4256000` | 1 | 2.0 | 0.9 |
| `CRS3035RES200mN2029400E4259200` | `CRS3035RES32000mN2016000E4256000` | 1 | 3.0 | 1.4 |
| `CRS3035RES200mN2029800E4252400` | `CRS3035RES8000mN2024000E4248000` | 1 | 1.0 | 0.6 |
| `CRS3035RES200mN2029800E4254200` | `CRS3035RES8000mN2024000E4248000` | 1 | 2.0 | 1.1 |
| `CRS3035RES200mN2030000E4254600` | `CRS3035RES8000mN2024000E4248000` | 1 | 1.0 | 0.6 |
| `CRS3035RES200mN2030200E4254200` | `CRS3035RES8000mN2024000E4248000` | 1 | 1.0 | 0.6 |
| `CRS3035RES200mN2030400E4253800` | `CRS3035RES8000mN2024000E4248000` | 1 | 2.0 | 0.8 |
| `CRS3035RES200mN2030400E4255200` | `CRS3035RES8000mN2024000E4248000` | 1 | 1.0 | 0.6 |
| `CRS3035RES200mN2030600E4252200` | `CRS3035RES8000mN2024000E4248000` | 1 | 2.0 | 0.8 |
| `CRS3035RES200mN2030600E4253400` | `CRS3035RES8000mN2024000E4248000` | 1 | 7.0 | 3.0 |
| `CRS3035RES200mN2030600E4253600` | `CRS3035RES8000mN2024000E4248000` | 1 | 2.0 | 0.8 |
| `CRS3035RES200mN2030600E4255200` | `CRS3035RES8000mN2024000E4248000` | 1 | 1.0 | 0.6 |
| `CRS3035RES200mN2030800E4252600` | `CRS3035RES8000mN2024000E4248000` | 1 | 4.0 | 1.7 |
| `CRS3035RES200mN2030800E4252800` | `CRS3035RES8000mN2024000E4248000` | 1 | 5.0 | 2.1 |
| `CRS3035RES200mN2030800E4253800` | `CRS3035RES8000mN2024000E4248000` | 1 | 3.0 | 1.3 |
| `CRS3035RES200mN2030800E4255000` | `CRS3035RES8000mN2024000E4248000` | 1 | 5.0 | 2.8 |
| `CRS3035RES200mN2031000E4252000` | `CRS3035RES8000mN2024000E4248000` | 1 | 2.0 | 0.8 |
| `CRS3035RES200mN2031000E4252400` | `CRS3035RES8000mN2024000E4248000` | 1 | 4.0 | 1.5 |
| `CRS3035RES200mN2031000E4253200` | `CRS3035RES8000mN2024000E4248000` | 1 | 7.0 | 3.0 |
| `CRS3035RES200mN2031000E4253400` | `CRS3035RES8000mN2024000E4248000` | 1 | 3.0 | 1.3 |
