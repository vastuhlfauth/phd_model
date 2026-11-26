# 6. Base grids: origins

## 6.1 Target

One table per state with, for each 200 m cell of metropolitan France: individuals, households, household size, dwellings by type and occupation, age groups, active individuals and income indicators, with a flag for imputed values; aggregated to 1 km. The representative points used by the networks (section 4.2) come from these tables. Origins are in France only; residential change between 2020 and 2021 comes from the Eurostat 1 km grid.

**Population categories of the whole study.** Every result by person (daily travel time per mode and in total, mode use, accessibility) is given for five categories: children (under 18; 6–17 in travel surveys, which start at 6), employed, unemployed, retired, and other inactive (students aged 18 or more, homemakers, others). In each cell they come from the cell's age groups and the census commune tables of activity by age [TO CONFIRM: method of allocation to cells; whether students aged 18 or more stay in "other inactive"].

**Synthetic population.** Household types (single person, couple, couple with children, single parent, other), used by the mobility model of section 10.4, come from the synthetic population generated from the tables of this section (decision of 20 November 2026) [TO CONFIRM: method of the synthetic population].

## 6.2 Inputs

- **Filosofi 2021 at the natural level** ("premier niveau diffusable"): cells of variable size, from 200 m to 64 km, each with at least 11 households for confidentiality. It contains individuals, households, household size, equivalised disposable income (standard of living) and about 30 other variables (age groups, household types, owners, dwellings by type and period, social housing, poor households).
- **Eurostat 2021 census grid (1 km):** population and residential change between 2020 and 2021. Independent of the Fichiers fonciers, it validates the downscaling, and residential change is kept for later modelling.
- **Census commune data** for 2021 and 2023 (population, households, age groups, activity).
- **INSEE 200 m Filosofi including imputed values:** a benchmark for the redistribution.
- **Fichiers fonciers**, base `pb0010_local` of the Parquet release (premises located from the cadastral plan), millésimes 2022 and 2024, read for the study area and for every département whose communes share a natural-level cell with it (Charente-Maritime, Dordogne, Landes and Lot-et-Garonne around Gironde):

| Variable | Content | Use |
|---|---|---|
| `idlocal` | Premises identifier | Key of all joins |
| `X`, `Y` | Position of the premises from the cadastral plan, EPSG:3035 (the Parquet release has no `geomloc`; the BAN address point, at street level for 43% of premises in Gironde, is not used) | Assignment to 200 m cells |
| `dteloc` | Type of premises: house, apartment, commercial or industrial premises | Dwellings vs activity premises; houses vs apartments |
| `logh` | Dwelling indicator ('t' for a dwelling; the same premises as `dteloc` '1' or '2') | Dwelling stock |
| `ccthp` | Occupancy: 'P' owner-occupied, 'L' rented, 'V' vacant (the same dwellings as `loghvac` = 't' in 2022) | Occupied stock, hence households; owner-occupiers |
| `proba_rprs` (2021, 2022), `rppo_rs` (2024) | Status of owner-occupied dwellings: 'RS' second home; `RP` (2022) or `RPPO` (2024) main residence; `AC` (2022) or `MR` (2024) recent transfer, a change of owner in the two years before the reference date; `NO` not owner-occupied; `PM` owned by a legal person. `proba_rprs` is Cerema's experimental estimate (main residence when the dwelling's address is the one where the owner receives the tax notice), `rppo_rs` the owners' declaration. In Gironde, 90,942 dwellings are 'RS' in 2022 and 57,883 in 2024; of the 2022 'RS' dwellings still present in 2024, 44% are 'RS' and 34% `RPPO`. Both fields classify only dwellings owned by a natural person and occupied by the owner: a dwelling held by a legal person, SCIs included (`PM`), let or vacant (`NO`) is never a second home. The census classes dwellings by their use, whoever owns them, and its second homes include furnished tourist lets; its published count (`P21_RSECOCC`) also adds occasional dwellings, used part of the year for work. The 2024 'RS' count is 67% of these census second homes and occasional dwellings of 2023, with the largest gaps in Bordeaux and the coastal resorts. A broader category, second homes plus the non-vacant dwellings neither owner-occupied nor let (`ccthp` other than 'P', 'L', 'V'), is tested against the census [TO CONFIRM: after the test] | Occupied stock; share of second homes |
| `catpro2` | Owner category ('F1' social housing organisation) | Social housing |
| `npiece_i` | Number of rooms, INSEE definition | Household size model |
| `stoth` | Living surface | Household size model |
| `dnbniv` | Number of levels | Household size model; floor area of premises |
| `jannath` | Year of construction | Construction period |
| `sprincp` | Main surface of professional premises | Job allocation key (section 7.2) |
| `typeact` | Type of professional activity | Job allocation key |
| `cconac` | NAF code of the occupant of professional premises (quality rated 3 out of 5 by Cerema) | Sector of each premises |

## 6.3 Method: redistribution preserving INSEE totals

1. **Locate premises.** Each premises of `pb0010_local` is assigned to the 200 m cell that contains its `X`, `Y` point (EPSG:3035); premises without coordinates (0.14% of the dwellings of Gironde in 2022) are dropped and counted. Every natural-level cell reached by the study area is completed with the premises of the neighbouring départements, so that its dwellings are complete.
2. **Occupied stock.** A premises counts as an occupied dwelling when:

```text
logh = 't'  AND  ccthp ≠ 'V'  AND  RS ≠ 'RS'
RS = rppo_rs (2024)
RS = rppo_rs of the same idlocal in 2024 when it is 'RS' or 'RPPO', else proba_rprs   (2021, 2022)
null codes count as neither vacant nor second home; recent transfers (AC, MR) are main residences
```

The earlier expression, NOT (vacant AND second home), excluded almost no dwelling (correction of 25 November 2026). For 2021 and 2022, a dwelling with a settled owner-occupied status (`RS` or `RPPO`) in 2024 takes that declared status; recent transfers and dwellings not owner-occupied in 2024 keep their own estimate (decision of 26 November 2026). The 2024 status describes the dwelling two or three years later, but changes of owner in between appear as `MR` and keep the earlier estimate. In Gironde in 2022, 57,074 dwellings take the 2024 'RS', 382,335 the 2024 `RPPO`, and 508,681 keep `proba_rprs`.

Against census 2021, by commune (`data/interim/landgrid/ff_commune_comparison_2022.md`):

| 2022 classification | Main residences, total | Main residences, P10–P90 of commune ratios | Second homes, total | Second homes, median commune ratio |
|---|---:|---:|---:|---:|
| `proba_rprs` alone | 100.9% | 77.9–107.9% | 111.4% | 228.9% |
| with the 2024 status | 103.1% | 94.2–108.9% | 94.2% | 184.7% |

Main residences against Filosofi households, per natural-level cell wholly inside Gironde (first decile, median, ninth decile): 1 km cells 75.6%, 98.9%, 111.4% with `proba_rprs` alone, 93.4%, 101.3%, 113.1% with the 2024 status; 2 km cells 80.2%, 100.0%, 114.1% against 94.9%, 103.3%, 114.2%. Splitting recent transfers between main residences and second homes in each commune's ratio barely improves the fit (scenario error 20.8% against 21.7%), so they stay main residences.

3. **Households.** One occupied dwelling is one household. Within each natural-level cell R, households are scaled so that their total equals Filosofi: H(c) = H_Filosofi(R) × D(c) / Σ_{c' in R} D(c'), where D is the number of occupied dwellings.
4. **Weights from regressions.** Household counts come from the Fichiers fonciers (step 3); regressions supply the relative composition of households, so that the downscaling follows meso-scale patterns while the sums stay exactly those of Filosofi:
    - Regressions estimated across natural-level cells (natural-level cells of 200 m giving direct observations) predict, for each 200 m cell, relative household size and the shares of each category (young, elderly, active individuals and so on).
    - Explanatory variables, computed per cell from the Fichiers fonciers: share of owner-occupiers among main residences (`ccthp` = 'P'); share of second homes among dwellings (step 2); share of social housing (`catpro2` = 'F1'); mean and standard deviation of `npiece_i` and `dnbniv`; median and standard deviation of `stoth` and `jannath`. A construction year outside 1600 to the vintage year and a floor (`dniv`) of 80 or more are codes, not values, and count as missing; `nbetagemax`, missing or zero for 43% of dwellings, is not used.
    - For a category k, the weight of cell c is w_k(c) = H(c) × r̂_k(c), the households of the cell times the predicted relative value, and the category is downscaled within each natural-level cell R as N_k(c) = N_k,Filosofi(R) × w_k(c) / Σ_{c' in R} w_k(c').
    - The mean standard of living (disposable income per consumption unit) is tested with the same approach.
    - The same regressions produce the 200 m grid of 2021 and the Filosofi-like grid of 2023 (step 7). Simple proportional downscaling on households is kept as the benchmark.
5. **Consistency** within each 200 m cell (age groups summing to individuals, for example) with iterative proportional fitting; optional integer rounding that preserves totals.
6. **Gaps.** Occupied dwellings that fall outside every Filosofi natural-level cell are dropped, so that totals always equal INSEE's (fewer than 50 main residences in Gironde in 2022).
7. **Filosofi-like 2023.** The regressions of step 4, estimated on Filosofi 2021 with the Fichiers fonciers 2022, are applied to the Fichiers fonciers 2024 and scaled to the 2023 commune data (census population, households, age groups). Both vintages take second homes from the 2024 declared status where it is settled (step 2), so no rescaling between them is needed. The mean standard of living is tested in the same way; otherwise income is left to the economic model.

## 6.4 Car ownership

- **Source:** share of households with no car, one car, two or more cars, by commune, for 2022 (INSEE census, housing file, published by the Tableau de bord des mobilités durables on data.gouv.fr).
- **Model at commune scale:** the shares of the three classes are explained by accessibility (from the products of section 10, by mode) and income (Filosofi, deflated to constant euros), estimated on 2022 [TO CONFIRM: functional form, e.g. ordered or multinomial logit].
- **Downscaling:** the model is applied to each 200 m cell with the cell's own accessibility and income, and the results are scaled to the commune counts of 2022.
- **Other years and scenarios:** the same model gives car ownership for 2023 and for scenarios, so that it responds to accessibility and income.
- **Use:** fixed costs of car ownership in the monetary cost (section 9.10) and car availability in the mode-use model (section 10.4).

## 6.5 Validation

- Against INSEE's own 200 m product on cells published without imputation, and against the Eurostat 1 km grid, which does not use the Fichiers fonciers; errors reported by density class and size of the natural-level cell.
- **Housing stock by commune:** main residences, second homes and vacant dwellings from the Fichiers fonciers against the census (dossier complet, 2021 and 2023); results for the classification of second homes in step 2. Vacant dwellings exceed the census (133% in 2022, 150% in 2024: tax vacancy on 1 January includes short vacancies), and so do dwellings (104%, 103%), so main residences stay close (103% in both years). Social housing among main residences (`catpro2` = 'F1') is 103% of Filosofi `log_soc` in 2022 and 102% in 2024.
- Regression weights against the simple downscaling, on the same metrics.
- **Temporal test of the 2023 model:** train on Filosofi 2019 with Fichiers fonciers 2021, predict 2021 from Fichiers fonciers 2022, and compare with Filosofi 2021.
- Car ownership: modelled totals against observed ones, aggregated to NUTS3 and to France.

## 6.6 Outputs

- `origins_200m(year, cell_id, individuals, households, household_size, dwellings_*, age_*, active, cars_0, cars_1, cars_2p, income_*, imputed, natural_cell_id)` and `origins_1km` (plus `residential_change` from the Eurostat grid), with the representative points; Parquet, EPSG:3035 cell ids.
