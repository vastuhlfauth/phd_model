# 6. Base grids: origins

## 6.1 Target

One table per state with, for each 200 m cell of metropolitan France: individuals, households, household size, dwellings by type and occupation, age groups, active individuals and income indicators, with a flag for imputed values; aggregated to 1 km. The representative points used by the networks (section 4.2) come from these tables. Origins are in France only; residential change between 2020 and 2021 comes from the Eurostat 1 km grid.

## 6.2 Inputs

- **Filosofi 2021 at the natural level** ("premier niveau diffusable"): cells of variable size, from 200 m to 64 km, each with at least 11 households for confidentiality. It contains individuals, households, household size, equivalised disposable income (standard of living) and about 30 other variables (age groups, household types, owners, dwellings by type and period, social housing, poor households).
- **Eurostat 2021 census grid (1 km):** population and residential change between 2020 and 2021. Independent of the Fichiers fonciers, it validates the downscaling, and residential change is kept for later modelling.
- **Census commune data** for 2021 and 2023 (population, households, age groups, activity).
- **INSEE 200 m Filosofi including imputed values:** a benchmark for the redistribution.
- **Fichiers fonciers**, base `pb0010_local` (premises located at building points, not parcels), millésimes 2022 and 2024:

| Variable | Content | Use |
|---|---|---|
| `idlocal` | Premises identifier | Key of all joins |
| `geomloc` | Location of the premises at its building | Assignment to 200 m cells |
| `dteloc` | Type of premises: house, apartment, commercial or industrial premises | Dwellings vs activity premises; houses vs apartments |
| `logh` | Dwelling indicator ('t' for a dwelling) | Dwelling stock |
| `ccthp` | Occupancy ('V' for vacant) | Occupied stock, hence households |
| `rppo_rs` | Main or secondary residence ('RS' for secondary) | Occupied stock |
| `catpro2` | Owner category | Social housing |
| `npiece_i` | Number of rooms, INSEE definition | Household size model |
| `stoth` | Living surface | Household size model |
| `dnbniv` | Number of levels | Household size model; floor area of premises |
| `jannath` | Year of construction | Construction period |
| `sprincp` | Main surface of professional premises | Job allocation key (section 7.2) |
| `typeact` | Type of professional activity | Job allocation key |
| `cconac` | NAF code of the occupant of professional premises (quality rated 3 out of 5 by Cerema) | Sector of each premises |

## 6.3 Method: redistribution preserving INSEE totals

1. **Locate premises.** Each premises of `pb0010_local` is placed at its building point (`geomloc`) and assigned to its 200 m cell.
2. **Occupied stock.** A premises counts as an occupied dwelling when:

```text
logh = 't'  AND  NOT (ccthp = 'V'  AND  rppo_rs = 'RS')
```

3. **Households.** One occupied dwelling is one household. Within each natural-level cell R, households are scaled so that their total equals Filosofi: H(c) = H_Filosofi(R) × D(c) / Σ_{c' in R} D(c'), where D is the number of occupied dwellings.
4. **Weights from regressions.** Household counts come from the Fichiers fonciers (step 3); regressions supply the relative composition of households, so that the downscaling follows meso-scale patterns while the sums stay exactly those of Filosofi:
    - Regressions estimated across natural-level cells (natural-level cells of 200 m giving direct observations) predict, for each 200 m cell, relative household size and the shares of each category (young, elderly, active individuals and so on).
    - Explanatory variables, computed per cell from the Fichiers fonciers: share of owner-occupiers (`ccthp` = 'P'); share of second homes (`rppo_rs` = 'RS'); mean and standard deviation of `npiece_i` and `dnbniv`; median and standard deviation of `stoth` and `jannath`.
    - For a category k, the weight of cell c is w_k(c) = H(c) × r̂_k(c), the households of the cell times the predicted relative value, and the category is downscaled within each natural-level cell R as N_k(c) = N_k,Filosofi(R) × w_k(c) / Σ_{c' in R} w_k(c').
    - The mean standard of living (disposable income per consumption unit) is tested with the same approach.
    - The same regressions produce the 200 m grid of 2021 and the Filosofi-like grid of 2023 (step 7). Simple proportional downscaling on households is kept as the benchmark.
5. **Consistency** within each 200 m cell (age groups summing to individuals, for example) with iterative proportional fitting; optional integer rounding that preserves totals.
6. **Gaps.** Occupied dwellings that fall outside every Filosofi natural-level cell are dropped, so that totals always equal INSEE's.
7. **Filosofi-like 2023.** The regressions of step 4, estimated on Filosofi 2021 with the Fichiers fonciers 2022, are applied to the Fichiers fonciers 2024 and scaled to the 2023 commune data (census population, households, age groups). The mean standard of living is tested in the same way; otherwise income is left to the economic model.

## 6.4 Car ownership

- **Source:** share of households with no car, one car, two or more cars, by commune, for 2022 (INSEE census, housing file, published by the Tableau de bord des mobilités durables on data.gouv.fr).
- **Model at commune scale:** the shares of the three classes are explained by accessibility (from the products of section 10, by mode) and income (Filosofi, deflated to constant euros), estimated on 2022 [TO CONFIRM: functional form, e.g. ordered or multinomial logit].
- **Downscaling:** the model is applied to each 200 m cell with the cell's own accessibility and income, and the results are scaled to the commune counts of 2022.
- **Other years and scenarios:** the same model gives car ownership for 2023 and for scenarios, so that it responds to accessibility and income.
- **Use:** fixed costs of car ownership in the monetary cost (section 9.10) and car availability in the mode-choice model.

## 6.5 Validation

- Against INSEE's own 200 m product on cells published without imputation, and against the Eurostat 1 km grid, which does not use the Fichiers fonciers; errors reported by density class and size of the natural-level cell.
- Regression weights against the simple downscaling, on the same metrics.
- **Temporal test of the 2023 model:** train on Filosofi 2019 with Fichiers fonciers 2021, predict 2021 from Fichiers fonciers 2022, and compare with Filosofi 2021.
- Car ownership: modelled totals against observed ones, aggregated to NUTS3 and to France.

## 6.6 Outputs

- `origins_200m(year, cell_id, individuals, households, household_size, dwellings_*, age_*, active, cars_0, cars_1, cars_2p, income_*, imputed, natural_cell_id)` and `origins_1km` (plus `residential_change` from the Eurostat grid), with the representative points; Parquet, EPSG:3035 cell ids.
