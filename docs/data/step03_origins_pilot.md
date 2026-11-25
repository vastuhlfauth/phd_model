# Step 3 origins pilot — commune checks

## Restricted Fichiers fonciers commune check

Status: pilot builds and census ratios were not run during coding. The real-data
commands below are the only commands that may read the restricted partitions.
All aggregate counts below 50 must be displayed as `<50`; no row-level output is
included here.

### Department 33 — 2022 FF / 2021 census

| Measure | Vintages side by side |
|---|---|
| Dwellings | Pending build 2022 |
| Main residences | Pending build 2022 |
| Second homes | Pending build 2022 |
| Vacant dwellings | Pending build 2022 |

Report for 2022: median and decile ratios of Fichiers fonciers to
`P21_LOG`, `P21_RP`, `P21_RSECOCC`, and `P21_LOGVAC` for every commune of
department 33. Report the 33 total for each measure and the ten communes with
the largest second-home gaps.

### Department 33 — 2024 FF / 2023 census

The local 2023 dossier-complet Parquet has no direct `P23_*` columns. It is
long-form: `GEO` and `GEO_OBJECT` identify geography, while `ID_TAB`, `DS`,
`TAB_MEASURE`, and `TIME_PERIOD` identify each measure in `OBS_VALUE`. The
exact selectors for the four housing measures have not been verified, so no
2023 census comparison or ratios are reported yet. Do not infer selectors
from the 2021 field names.

| Measure | Vintages side by side |
|---|---|
| Dwellings | Pending build 2024 |
| Main residences | Pending build 2024 |
| Second homes | Pending build 2024 |
| Vacant dwellings | Pending build 2024 |

### Three residence interpretations

For main residences and second homes, compare:

1. Recent transfers counted as main residences, as configured;
2. Recent transfers left out of both categories;
3. Recent transfers split at the commune ratio of settled main residences to
   settled second homes among owner-occupied dwellings.

The closest interpretation to the census is to be stated after the two real
builds. No conclusion was drawn from synthetic tests.

### Other checks

- Compare social housing among FF main residences in 33 with Filosofi `log_soc`
  in the 200 m rows linked to 33 communes.
- Count dwellings whose `idcom` disagrees with the commune list of the 200 m
  cell's `lcog_geo`.
- Premises without coordinates, main residences outside natural-level cells,
  and cleaning-rule removals are reported by exact internal count in
  `data/interim/landgrid/ff_cells_{vintage}.json` and aggregate-only in the
  public report.

## Commands

From the project terminal with `.venv` active, these real-data builds may take
more than two minutes. They have not been run during coding.

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2022 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers --vintage 2024 --department 17 --department 24 --department 33 --department 40 --department 47
```
