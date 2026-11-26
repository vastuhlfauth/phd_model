# Step 3 origins pilot — commune checks

## Restricted Fichiers fonciers commune check

Status: census selectors are verified and the report subcommand is implemented.
No real FF build or report was run during coding. The commands below are the
only commands that may read the restricted partitions. All displayed aggregate
counts below 50 are suppressed as `<50`; no row-level FF output is included.

### Adopted hybrid comparison

The default for 2021 and 2022 is `hybrid_2024`; 2024 remains `own`. Join each
2021 or 2022 partition to the same department's 2024 partition by `idlocal`;
2024 `RS` and `RPPO` override the earlier second-home status, while all other
or missing statuses fall back to that vintage's `proba_rprs`. Vacancy uses
the earlier vintage's `ccthp`. An earlier-vintage recent-transfer indicator
is counted only if the hybrid rule leaves the dwelling a main residence.
The hybrid is adopted under section 6.3, based on the 2022 comparison.

The comparison reports both classifications' housing totals, commune ratios,
transfer scenarios, and separately ranked top gaps. It counts all dwellings in
the department's three hybrid branches, including unlocated dwellings.
Natural-cell ratios use whole natural squares covered by the dissolved 2021
commune contours in EPSG:3035 and exclude zero-household cells. This geometric
test is stricter than the `lcog_geo` populated-cell approximation.

The five pilot départements took 2 to 4 seconds each. Build products and
diagnostics stay under `data/interim/landgrid/`.

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2022 --department 17 --department 24 --department 33 --department 40 --department 47 --second-home-source own --output data\interim\landgrid\own_2022_comparison
python -m landgrid.origins.fichiers_fonciers --vintage 2022 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers report --vintage 2022 --department 33 --compare-own data\interim\landgrid\own_2022_comparison --compare-hybrid data\interim\landgrid
```

The own comparison build uses a separate output and does not overwrite the
adopted hybrid. The comparison report is
`data/interim/landgrid/ff_commune_comparison_2022.md`.

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

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2021 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers --vintage 2022 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers --vintage 2024 --department 17 --department 24 --department 33 --department 40 --department 47
python -m landgrid.origins.fichiers_fonciers report --vintage 2022 --department 33
python -m landgrid.origins.fichiers_fonciers report --vintage 2024 --department 33
```
