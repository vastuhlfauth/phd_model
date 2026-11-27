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
The build also writes `ff_natural_{vintage}.parquet`, with covariates
aggregated directly from dwellings at the natural level. The 200 m and natural
outputs include main-residence house and flat counts, construction-period
counts and shares, and the density and dwelling characteristics used by the
experimental composition method. Rebuilding invalidates older cached cells.

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

The broader category is the adopted second-home count plus disjoint extra
dwellings that are non-vacant and neither owner-occupied (`ccthp=P`) nor let
(`ccthp=L`). Report both variants, including and excluding null `ccthp`, with
the same commune totals, ratios, and ten largest gaps as second homes. The
extra-dwelling counts by `ccthp` and `proba_rprs` are in the report. Broad
main residences are compared with `P21_RP` by commune and with Filosofi 2021
households by fully contained natural-level cell.

### Department 33 — 2024 FF / 2023 census

The 2023 Parquet has no direct `P23_*` columns; the verified selectors and the
department-33 comparison against 2021 are recorded in
`docs/data/census_dossier_complet.md`. It uses `GEO_OBJECT=COM`,
`TIME_PERIOD=2023`, `ID_TAB=LOG_T1`, `DS=DS_RP_SERIE_HISTORIQUE`, and the four
housing measure identifiers in `TAB_MEASURE`. The selected dataset has 534
department-33 communes per measure. FF results remain pending the real build.

Use the same broader-category and main-residence comparisons as for 2022,
with `DWELLINGS_OCS_DW_SEC_DW_OCC` as the census second-home-and-occasional
measure and `rppo_rs` for extra-dwelling code counts.

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

## Section 6.5 — 2021 downscaling validation

The 2021 Filosofi natural-level counts are distributed to 200 m cells using
the adopted 2022 hybrid Fichiers fonciers main-residence counts. If a natural
cell has no main-residence weight, use all dwellings, then Filosofi 200 m
households; natural cells already at 200 m are copied. The output is
`data/interim/landgrid/origins_2021_200m.parquet`, with each cell's natural
cell id, natural-cell size, downscaled variables and selected fallback.

The INSEE 200 m comparison uses only `i_est_200 = 0` records in natural cells
larger than 200 m. It reports mean absolute error, median absolute relative
error, and the share within the configured ±20% tolerance for households,
individuals, under-18s (`ind_0_3` through `ind_11_17`) and people aged 65+
(`ind_65_79` plus `ind_80p`), by natural-cell size and Eurostat density class.
Density is Eurostat population divided by `LAND_SURFACE` in km² when positive;
otherwise the 1 km² cell area is used. Classes are under 300, 300 to under
1,500, and 1,500 or more people per km². The report counts 200 m validation
cells without a matching Eurostat row, with null or negative population, and
with null, zero, or negative land surface; reasons may overlap. Unmatched
cells and cells with unavailable population retain their 200 m error
statistics in separate density classes. The median relative error excludes
zero-reference cells; the tolerance share includes them, counting only exact
zero predictions as within tolerance.

The naive baseline equally splits each natural-cell total among 200 m cells
with at least one main residence, assigning zero to the other cells; if none
qualify, all subcells receive zero. The Eurostat comparison sums downscaled
individuals to 1 km cells wholly covered by the department-33 boundary and
reports totals and median absolute relative error by Eurostat density class.
Zero Eurostat reference populations are excluded from relative-error medians.
Cells with null or negative Eurostat populations are excluded from the 1 km
Eurostat comparison.
Reports contain aggregate totals and error statistics only; every displayed
count or population total below 50 is `<50`. The report and downscaled
products remain under `data/interim/landgrid/`.

### Experimental composition

The separate composition product keeps the proportional product unchanged.
Direct FF counterparts weight owner households, house/flat households, social
housing and construction periods; a zero natural-cell counterpart falls back
to downscaled households. The report counts those fallbacks.

For each remaining variable, the configured `fixed_methods` entry takes
precedence over the cross-validation choice file. If the file or a variable
choice is absent, `default_method` applies; a missing file logs a warning.
The experimental `within` fit uses all eligible non-imputed 200 m training
cells in the reached natural cells, with natural-cell fixed effects.
Within-group constant and linearly dependent features are dropped and recorded.
Natural-cell and within-cell covariates use household-weighted training
standardisation and mean imputation with missing indicators. Individuals are
allocated first; predicted individuals are the exposure for age and `ind_snv`.

Age IPF includes `ind_inc` when present. Its tolerance and iteration limit
are configured. If age and individual margins disagree or IPF does not
converge, the composition command fails without publishing a new composition
product. The interim IPF failure Parquet identifies the natural cells and
reasons; its report displays only suppressed aggregate counts. Fitted model
coefficients and standard errors are written to the interim composition report
and model JSON; within-model standard errors are dispersion-corrected.

The section-6.5 report compares composition, proportional and equal split on
the same non-imputed 200 m cells, including the requested household, housing
and income variables. At 1 km, it compares age 65+ directly with Eurostat.
Under-11 (`ind_0_3`, `ind_4_5`, `ind_6_10`) and under-18 (also `ind_11_17`)
ratios to Eurostat under-15 are informational, not validation errors.
Eurostat's negative age codes are excluded.
Within-model INSEE comparisons are in-sample; use the grouped cross-validation
report for held-out errors. Eurostat comparisons remain independent.

Builds resume FF departments and composition models from interim checkpoints;
validation caches aggregate metrics there. The commands below log to dated
files and write summaries under `logs/`. Restricted tables, models, detailed
failure identifiers and temporary extracts stay under `data/interim/landgrid/`.
No real-data build or validation was run during implementation.
The configured bound of 80 on `dnbniv` is a plausibility check; `dniv` is not
used. The section 6.3 wording still needs correction.

## Commands

For the composition experiment, run in order:

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2022
python -m landgrid.origins.crossval
python -m landgrid.origins.composition
python -m landgrid.origins.validation
```

The composition command rebuilds the proportional benchmark if its FF
signature is stale. For the other existing checks:

```powershell
python -m landgrid.origins.fichiers_fonciers --vintage 2021
python -m landgrid.origins.fichiers_fonciers --vintage 2022
python -m landgrid.origins.fichiers_fonciers --vintage 2024
python -m landgrid.origins.fichiers_fonciers report --vintage 2022 --department 33
python -m landgrid.origins.fichiers_fonciers report --vintage 2024 --department 33
python -m landgrid.origins.downscale
```
