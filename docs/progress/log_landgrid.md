# Landgrid origins

## 2026-11-25 — Step 3 data pages (in progress)

- Added Fichiers fonciers, Filosofi and Eurostat grid pages; indexed all three.
- Fichiers fonciers 2022 department-33 Parquet reads directly in DuckDB:
  1,766,607 rows; `idlocal` is unique.
- The 2022 schema has no `geomloc` or `rppo_rs`; no aliases were inferred.
  Section 6.3's four occupancy/residence groups cannot be computed.
- Filosofi 2021 totals: 2,324,577 200 m rows and 146,641 natural-level rows
  across metropolitan France, Martinique and La Réunion.
- The department-33 Filosofi subset uses official `lcog_geo` commune
  intersections. 200 m sums reconcile to natural-level values in every
  metropolitan natural cell (maximum household gap about 1.5e-9).
- Natural-level cells with linked populated 200 m records in both department
  33 and another department: at least 157; 19,450.2 whole-cell households.
- Eurostat grid IDs round-trip for all 4,595,919 grid-coded rows. 6,992
  linked 1 km cells total 1,656,946 population; this is not a clipped or
  independently boundary-validated total.
- A direct DuckDB read of the full 2021 commune geometry exceeded 60 seconds
  and was stopped. No raw data changed and no package code was added.
- Before implementation, resolve the missing Fichiers fonciers fields and
  obtain exact geometric straddler / Eurostat boundary counts if needed.
