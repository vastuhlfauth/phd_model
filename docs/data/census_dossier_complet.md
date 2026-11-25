# Census dossier complet

- **Source:** INSEE, census dossier complet for 2021 and 2023.
- **Join key:** `CODGEO` in the 2021 CSV; `GEO` in the 2023 Parquet, with
  `GEO_OBJECT` identifying the geography type.
- **2021 file:** `data/raw/census/2021/dossier_complet_31_12_2024.zip`,
  member `dossier_complet.csv`; 34,993 data rows.
- **2023 file:** `data/raw/census/2023/dossier_complet.parquet`;
  92,615,762 data rows across the dossier-complet table.

## Housing comparison fields

| Census year | Column | Type | Meaning |
|---|---|---|---|
| 2021 | `CODGEO` | CSV type not declared | Commune code |
| 2021 | `P21_LOG` | CSV type not declared | Dwellings |
| 2021 | `P21_RP` | CSV type not declared | Main residences |
| 2021 | `P21_RSECOCC` | CSV type not declared | Second homes |
| 2021 | `P21_LOGVAC` | CSV type not declared | Vacant dwellings |
| 2023 | `GEO` | `VARCHAR` | Geographic code |
| 2023 | `GEO_OBJECT` | `VARCHAR` | Geography type |
| 2023 | `P23_LOG` | absent | No direct column in this release |
| 2023 | `P23_RP` | absent | No direct column in this release |
| 2023 | `P23_RSECOCC` | absent | No direct column in this release |
| 2023 | `P23_LOGVAC` | absent | No direct column in this release |

The 2021 CSV header contains `CODGEO` and all four requested 2021 housing
columns. The CSV header does not declare field types.

The 2023 Parquet is a long-form table; its schema has `GEO` (`VARCHAR`),
`GEO_OBJECT` (`VARCHAR`), `TIME_PERIOD` (`VARCHAR`), `ID_TAB` (`VARCHAR`),
`DS` (`VARCHAR`), `TAB_MEASURE` (`VARCHAR`), and `OBS_VALUE` (`DOUBLE`).
The guide describes `GEO` as the geographic code, with `GEO_OBJECT` giving
the geography type; table/dimension fields identify an observation and
`OBS_VALUE` holds its value. Thus the four `P23_*` names have no one-column
replacement: report extraction must select the corresponding observations
from `OBS_VALUE` using the table and measure identifiers.

No census observation values are reproduced here.
