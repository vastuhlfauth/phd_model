# Census dossier complet

- **Source:** INSEE census dossier complet, vintages 2021 and 2023.
- **2021 file:** `data/raw/census/2021/dossier_complet_31_12_2024.zip`,
  member `dossier_complet.csv`; 34,993 data rows. `CODGEO` is the commune
  code; the four housing columns below use this same source row count. The CSV
  header has no declared types.
- **2023 file:** `data/raw/census/2023/dossier_complet.parquet`;
  92,615,762 rows. `GEO` (`VARCHAR`) is the geography code and
  `GEO_OBJECT` (`VARCHAR`) identifies its type.

## Housing comparison fields and selectors

| Census year | Field or selector | Type | Meaning |
|---|---|---|---|
| 2021 | `CODGEO` | CSV type not declared | Commune code |
| 2021 | `P21_LOG` | CSV type not declared | Dwellings |
| 2021 | `P21_RP` | CSV type not declared | Main residences |
| 2021 | `P21_RSECOCC` | CSV type not declared | Second homes and occasional dwellings |
| 2021 | `P21_LOGVAC` | CSV type not declared | Vacant dwellings |
| 2023 | `GEO` | `VARCHAR` | Commune code when `GEO_OBJECT=COM` |
| 2023 | `GEO_OBJECT` | `VARCHAR` | Geography type |
| 2023 | `GEO_OBJECT=COM`, `TIME_PERIOD=2023`, `ID_TAB=LOG_T1`, `DS=DS_RP_SERIE_HISTORIQUE` | `VARCHAR` selectors | Commune historical housing table and reference period |
| 2023 | `TAB_MEASURE=DWELLINGS` | `OBS_VALUE` is `DOUBLE` | Dwellings (`P21_LOG` comparison) |
| 2023 | `TAB_MEASURE=DWELLINGS_OCS_DW_MAIN` | `OBS_VALUE` is `DOUBLE` | Main residences (`P21_RP` comparison) |
| 2023 | `TAB_MEASURE=DWELLINGS_OCS_DW_SEC_DW_OCC` | `OBS_VALUE` is `DOUBLE` | Second homes and occasional dwellings (`P21_RSECOCC` comparison) |
| 2023 | `TAB_MEASURE=DWELLINGS_OCS_DW_VAC` | `OBS_VALUE` is `DOUBLE` | Vacant dwellings (`P21_LOGVAC` comparison) |

The 2023 Parquet has no direct `P23_LOG`, `P23_RP`, `P23_RSECOCC`, or
`P23_LOGVAC` columns. Their equivalents are the four `TAB_MEASURE` selectors
above, with values in `OBS_VALUE`. The selector mapping is stored in
`config/origins.yaml`. For department 33, the selected 2023 observations
contain 534 communes per measure (2,136 records); the 2021 file has 535
commune rows for that department.

`LOG_T1` is the guide's historical "evolution of housing by category" table.
The same totals were returned by `LOG_T2` / `DS_RP_LOGEMENT_PRINC`; `LOG_T1`
is used because it is the documented historical series. Earlier periods for
these measures are 1968, 1975, 1982, 1990, 1999, 2007, 2012, and 2017.

## Metadata dimensions

The 2023 file has 25,453 distinct five-dimension combinations. The distinct
values and row counts for `GEO_OBJECT`, `TIME_PERIOD`, `ID_TAB`, `DS`, and
`TAB_MEASURE` are in [census_dossier_complet_dimensions.csv](./census_dossier_complet_dimensions.csv);
each dimension's counts reconcile to the 92,615,762 source rows.

## Department-33 selector check

For the 534 communes common to both releases, 2023 totals compared with the
2021 totals as follows:

| Measure | 2021 | 2023 | Change |
|---|---:|---:|---:|
| Dwellings | 913,405.85 | 944,356.43 | +3.39% |
| Main residences | 775,300.55 | 800,830.41 | +3.29% |
| Second homes and occasional dwellings | 81,657.32 | 86,844.69 | +6.35% |
| Vacant dwellings | 56,447.98 | 56,681.32 | +0.41% |

Three measures are within 3.4%; second homes are +6.35%, above a 5% check
threshold, and should be interpreted as a notable change rather than described
as within a few percent. The comparison uses the common-commune set; 2021 has
one additional department-33 commune row.
