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
| `proba_rprs` (2021, 2022), `rppo_rs` (2024) | Status of owner-occupied dwellings: 'RS' second home; `RP` (2022) or `RPPO` (2024) main residence; `AC` (2022) or `MR` (2024) recent transfer, a change of owner in the two years before the reference date; `NO` not owner-occupied; `PM` owned by a legal person. `proba_rprs` is Cerema's experimental estimate (main residence when the dwelling's address is the one where the owner receives the tax notice), `rppo_rs` the owners' declaration. In Gironde, 90,942 dwellings are 'RS' in 2022 and 57,883 in 2024; of the 2022 'RS' dwellings still present in 2024, 44% are 'RS' and 34% `RPPO`. Both fields classify only dwellings owned by a natural person and occupied by the owner: a dwelling held by a legal person, SCIs included (`PM`), let or vacant (`NO`) is never a second home. The census classes dwellings by their use, whoever owns them, and its second homes include furnished tourist lets; its published count (`P21_RSECOCC`) also adds occasional dwellings, used part of the year for work. The 2024 'RS' count is 67% of these census second homes and occasional dwellings of 2023, with the largest gaps in Bordeaux and the coastal resorts. A broader category, second homes plus the non-vacant dwellings neither owner-occupied nor let (`ccthp` other than 'P', 'L', 'V'), was tested and not adopted (decision of 27 November 2026): it brings the totals closer to the census but places second homes worse by commune (median commune ratio 239% against 185% in 2022, 184% against 118% in 2024), and its codes are unstable between vintages (`T` 18,067 then 6,411 dwellings in Gironde, `B` 1,184 then 11,157) | Occupied stock; share of second homes |
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
4. **Composition of households** (decision of 27 November 2026). Household counts come from step 3. Every other Filosofi count k is downscaled within each natural-level cell R as N_k(c) = N_k,Filosofi(R) × w_k(c) / Σ_{c' in R} w_k(c'), with one of four weights, set per variable in `config/origins.yaml`:
    - **Direct**, where the Fichiers fonciers count the same thing: owner households (`men_prop`) in proportion to owner-occupied main residences; households in houses and in flats (`men_mais`, `men_coll`) to main residences that are houses and flats; social housing (`log_soc`) to social main residences; dwellings by construction period (`log_av45`, `log_45_70`, `log_70_90`, `log_ap90`, `log_inc`) to main residences by period. Where the counterpart is zero in a whole natural-level cell, households are used.
    - **Within-cell regression**: w_k(c) = d(c) × exp(β·x(c)), where d(c) is the cell's main residences for household variables and its downscaled individuals for age groups and the standard of living. β comes from a Poisson model with one intercept per natural-level cell, N_k(c) ~ Poisson(exp(α_R + log d(c) + β·x(c))), fitted on INSEE's 200 m cells published without imputation (`i_est_200` = 0) in natural-level cells larger than 200 m that hold at least two such cells (about 12,700 cells in Gironde). The intercepts absorb each natural-level cell's level, so β describes only how a total splits among the 200 m cells, which is what the downscaling needs. Standard errors are scaled by the Pearson dispersion (1.0 to 2.4 for the counts in Gironde).
    - **Regression across natural-level cells**: the same weight, with β from a Poisson model fitted across natural-level cells and weighted by households. It mostly learns differences between large cells, and degrades some variables in sparse areas.
    - **Proportional**: w_k(c) = H(c); individuals of unknown age (`ind_inc`) in proportion to individuals.
    - **Explanatory variables** x(c), per 200 m cell from its main residences: shares of owner-occupiers (`ccthp` = 'P'), houses, social housing (`catpro2` = 'F1') and each construction period; share of second homes among dwellings (step 2); main residences in the cell; mean and standard deviation of `npiece_i` and `dnbniv`; median and standard deviation of `stoth` and `jannath`. They are standardised; a missing value takes the mean, with a missing indicator; variables without variance within natural-level cells in the training data are dropped. A construction year outside 1600 to the vintage year and a `dnbniv` of 80 or more are implausible and count as missing; `dniv` and `nbetagemax` (missing or zero for 43% of dwellings) are not used.
    - **Choice of the weight**: five-fold cross-validation, grouped by natural-level cell, scores the proportional weight and both regressions on the same held-out cells. Each regression variable keeps the weight with the lowest pooled median absolute relative error, the simpler one when two are within 0.5 points. A fit that fails, or gives a standardised coefficient above 10 in absolute value, falls back to proportional. Results in section 6.5.
    - The same models produce the 200 m grid of 2021 and the Filosofi-like grid of 2023 (step 7). Proportional downscaling is kept as the benchmark.
5. **Consistency.** Within each natural-level cell, iterative proportional fitting makes the age groups (with `ind_inc`) sum to each 200 m cell's individuals, and each age group to its Filosofi total; cells that do not converge are reported (fewer than 50 natural-level cells in Gironde). Optional integer rounding preserves totals.
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
- **Composition** (section 6.3, step 4): five-fold cross-validation grouped by natural-level cell, on INSEE's non-imputed 200 m cells, so that no held-out cell shares a natural-level cell with a training cell. The comparison with INSEE's 200 m product above is in-sample for the within-cell regression; the Eurostat comparison stays independent. Gironde, 2021, 12,921 held-out cells, pooled median absolute relative error:

  | Variable | Proportional | Across natural-level cells | Within cells | Weight kept |
  |---|---:|---:|---:|---|
  | Individuals (`ind`) | 12.7% | 10.5% | 9.9% | within |
  | Under 18 | 31.2% | 28.6% | 27.3% | within |
  | 65 and over | 32.1% | 25.3% | 24.3% | within |
  | Standard of living (`ind_snv`) | 16.8% | 13.5% | 10.7% | within |
  | Poor households (`men_pauv`) | 39.4% | 38.8% | 33.4% | within |
  | One-person households (`men_1ind`) | 29.6% | 24.4% | 24.3% | across (tie) |
  | Single-parent families (`men_fmp`) | 38.2% | 33.9% | 33.5% | across (tie) |
  | Five or more people (`men_5ind`) | 41.9% | 42.6% | fit failed in four folds | proportional |

  Each of the ten age groups keeps the within-cell regression (22% to 41%; the youngest groups, small counts per cell, stay near 40% whatever the weight). The direct weights, against INSEE's 200 m product in 1 km natural-level cells (median error by density class): owner households 6–8% against 14–36% with the proportional weight, households in houses 4–6% against 8–38%, social housing 0–7% against 64–68%. Against Eurostat 1 km, outside dense cells, individuals are within 2% of the reference and 65 and over within 1–5%, as with the proportional weight; dense cells hold 7.5% fewer individuals than Eurostat, the population outside fiscal households (section 6.2).
- **Temporal test of the 2023 model:** train on Filosofi 2019 with Fichiers fonciers 2021, predict 2021 from Fichiers fonciers 2022, and compare with Filosofi 2021.
- Car ownership: modelled totals against observed ones, aggregated to NUTS3 and to France.

## 6.6 Outputs

- `origins_200m(year, cell_id, individuals, households, household_size, dwellings_*, age_*, active, cars_0, cars_1, cars_2p, income_*, imputed, natural_cell_id)` and `origins_1km` (plus `residential_change` from the Eurostat grid), with the representative points; Parquet, EPSG:3035 cell ids.
