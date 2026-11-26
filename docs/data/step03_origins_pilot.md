# Step 3 origins pilot — commune checks

## Restricted Fichiers fonciers commune check

Status: census selectors are verified and the report subcommand is implemented.
No real FF build or report was run during coding. The commands below are the
only commands that may read the restricted partitions. All displayed aggregate
counts below 50 are suppressed as `<50`; no row-level FF output is included.

### Department 33 — 2022 FF / 2021 census

The 2021 census comparison fields are `P21_LOG`, `P21_RP`,
`P21_RSECOCC`, and `P21_LOGVAC`; each is a column in the 2021 CSV.
Department 33 has 535 census commune rows. FF results remain pending the real
build.

Report for 2022: median and decile ratios of Fichiers fonciers to
`P21_LOG`, `P21_RP`, `P21_RSECOCC`, and `P21_LOGVAC` for every commune of
department 33. Report the 33 total for each measure and the ten communes with
the largest second-home gaps.

### Department 33 — 2024 FF / 2023 census

The 2023 Parquet has no direct `P23_*` columns; the verified selectors and the
department-33 comparison against 2021 are recorded in
`docs/data/census_dossier_complet.md`. It uses `GEO_OBJECT=COM`,
`TIME_PERIOD=2023`, `ID_TAB=LOG_T1`, `DS=DS_RP_SERIE_HISTORIQUE`, and the four
housing measure identifiers in `TAB_MEASURE`. The selected dataset has 534
department-33 communes per measure. FF results remain pending the real build.

### Three residence interpretations

For main residences and second homes, compare:

1. Recent transfers counted as main residences, as configured;
2. Recent transfers left out of both categories;
3. Recent transfers split at the commune ratio of settled main residences to
   settled second homes among owner-occupied dwellings.

The report compares the configured, excluded, and proportionally split
interpretations. It ranks them by the mean of the main-residence and
second-home normalized absolute count errors; no conclusion is drawn from
synthetic fixtures.

### Other checks

- Compare social housing among FF main residences in 33 with Filosofi `log_soc`
  in the 200 m rows linked to 33 communes.
- Count dwellings whose `idcom` disagrees with the commune list of the 200 m
  cell's `lcog_geo`.
- Premises without coordinates, main residences outside natural-level cells,
  and cleaning-rule removals are reported by exact internal count in
  `data/interim/landgrid/ff_cells_{vintage}.json` and suppressed as needed in
  the aggregate-only report.

## Commands

From the project terminal with `.venv` active, these real-data builds may take
more than two minutes. They have not been run during coding.

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2022 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers --vintage 2024 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers report --vintage 2022 --department 33
python -m landgrid.origins.fichiers_fonciers report --vintage 2024 --department 33
```
