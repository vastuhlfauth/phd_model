---
applyTo: "packages/landgrid/**"
description: Rules for origins and opportunities (landgrid)
---

# landgrid: origins and opportunities

Spec: `docs/spec/06_origins.md` and `docs/spec/07_opportunities.md`; grids in `docs/spec/04_spatial_frame.md`.

## Totals and keys

- Every downscaling preserves its control totals exactly. Tests check that, for every variable, the sum over each zone equals the input total (relative tolerance 1e-9).
- One generic function implements O(c) = T(Z) × w(c) / Σ w over Z (section 7.1); all layers use it.
- Keys with a zero sum in a zone are an error to report, not something to divide by.

## Origins (section 6)

- **Fichiers fonciers:** use table `pb0010_local`, key `idlocal`, location `geomloc`. Variable names exactly as in `docs/data/fichiers_fonciers.md`.
- **Occupied dwelling, exactly:** `logh = 't' AND NOT (ccthp = 'V' AND rppo_rs = 'RS')`. Owner-occupier: `ccthp = 'P'`.
- **Households:** occupied dwellings scaled to Filosofi households within each natural-level cell. Dwellings outside every natural-level cell are dropped.
- **Regression weights** (section 6.3, step 4):
  - estimated across natural-level cells;
  - weight w_k(c) = H(c) × r̂_k(c);
  - simple proportional downscaling is kept as the benchmark;
  - the same models serve 2021 and 2023.
- **Car ownership** (section 6.4) needs accessibility products from `mobgrid`, so it comes after step 10.

## Jobs (section 7.2)

- **Totals:** INSEE EMP by EPCI and sector (simplified NACE classification).
- **Keys:** Fichiers fonciers premises with `cconac` (premises without it are dropped), weighted by `sprincp`.
- **Public sector:** OSM building footprints with the amenity and building tags of section 7.2; each building is counted once (one feature per site).
- **Comparison:** the Overture method, without population-in-reach scaling.
- **Construction:** three keys compared.
- **Abroad:** NUTS3 totals with Overture keys only.

## Services, nature, social (sections 7.3 to 7.5)

- **BPE:** groups and codes in both nomenclatures (2021, and 2023 onwards for BPE 2025), stored in `config/landuse.yaml`. B103 is excluded from food.
- **Nature:** parks of at least 2,500 m², rivers `water=river`, access points every 50 m along contours.
- **Social:** 200 m cells with more than 50 inhabitants and 1 km cells with more than 200; France only.
- **Destination flags:** one bit per type, in `destinations(year, scenario, res, cell_id, flags)`.

## Outputs

- The Parquet tables of sections 6.6 and 7.6, at 200 m and 1 km, one row per (year, scenario, cell, type).
