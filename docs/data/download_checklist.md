# Download checklist

Store everything in `data/raw/{source}/{vintage}/` and never edit it there. Step 2 (`acquire`) automates these downloads later; until then, download by hand and tick the box. Restricted sources stay manual.

**Pilot:** Gironde (département 33) plus a 50 km halo (parts of Charente-Maritime, Charente, Dordogne, Lot-et-Garonne, Landes).

## A. Already available

- [ ] Fichiers fonciers 2022 and 2024 (and 2021), Cerema convention → `data/raw/fichiers_fonciers/{ff2021,ff2022,ff2024}/`
- [ ] BPE 2021 → `data/raw/bpe/INSEE_bpe21-ensemble-xy-csv/`
- [ ] BPE lists of equipment types 2021 (PDF) → `data/raw/bpe/nomenclature/`
- [ ] Eurostat 2021 census grid, 1 km → `data/raw/eurostat_grid/Eurostat_Census-GRID_2021_V3/`

## B. Pilot downloads

| ✓ | # | Dataset | Vintage | Where | Save to |
|---|---|---|---|---|---|
| [ ] | 1 | OpenStreetMap, France | 2022-01-01 and 2024-01-01 | `https://download.geofabrik.de/europe/france-220101.osm.pbf` and `france-240101.osm.pbf` (with `.md5`), about 4 GB each; clip to Gironde plus halo for the pilot | `data/raw/osm/{220101,240101}/` |
| [ ] | 2 | GTFS feeds covering Gironde: TBM (Bordeaux Métropole), regional coaches of Nouvelle-Aquitaine, TER | Current (2026) | `https://transport.data.gouv.fr/api/datasets` (search by network), docs at `/swaggerui` | `data/raw/gtfs/2026-10/{dataset_id}/` |
| [ ] | 3 | Filosofi 2021, natural level | 2021 | `https://www.insee.fr/fr/statistiques/fichier/8735108/Filosofi2021_carreaux_nivNaturel_csv.zip` | `data/raw/filosofi/2021/` |
| [ ] | 4 | Filosofi 2021, 200 m cells with imputed values (benchmark) | 2021 | INSEE page of the Filosofi 2021 gridded data (check where the 200 m file is published) | `data/raw/filosofi/2021/` |
| [ ] | 5 | Census commune data | 2021 and 2023 | `https://www.insee.fr/fr/statistiques/5359146` | `data/raw/census/{2021,2023}/` |
| [ ] | 6 | Employment at place of work (EMP) | 2021 and 2023 | 2021: `https://www.insee.fr/fr/statistiques/8202930?sommaire=8205947`; 2023: `https://www.insee.fr/fr/statistiques/9004561` | `data/raw/emp/{2021,2023}/` |
| [ ] | 7 | Home-to-work flows (MOBPRO) | 2021 and 2023 | 2021: `https://www.insee.fr/fr/statistiques/8205896?sommaire=8205966`; 2023: `https://www.insee.fr/fr/statistiques/9004795?sommaire=9004842` | `data/raw/mobpro/{2021,2023}/` |
| [ ] | 8 | BPE 2025 (for the 2023 state) | 2025 | `https://www.insee.fr/fr/statistiques/8217525?sommaire=8217537` | `data/raw/bpe/2025/` |
| [ ] | 9 | Communes to EPCI table | 2026 | `https://www.insee.fr/fr/information/7671844` | `data/raw/cog/2026/` |
| [ ] | 10 | Communes table de passage | Since 2003 | `https://www.insee.fr/fr/information/7671867` | `data/raw/cog/passage/` |
| [ ] | 11 | Commune contours | 2021, 2023, 2026 | `https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2021/geojson/`; `https://etalab-datasets.geo.data.gouv.fr/2023/geojson/`; `https://etalab-datasets.geo.data.gouv.fr/2026/geojson/` | `data/raw/contours/{2021,2023,2026}/` |
| [ ] | 12 | Elevation BD ALTI, 25 m: Gironde and neighbouring départements | Latest | `https://www.data.gouv.fr/datasets/bd-alti-r-1` | `data/raw/bdalti/25m/` |
| [ ] | 13 | Cycle infrastructure (Géovélo) | Earliest file (mid-2022) and January 2024 | `https://transport.data.gouv.fr/datasets/amenagements-cyclables-france-metropolitaine` | `data/raw/geovelo/{2022-xx,2024-01}/` |
| [ ] | 14 | Overture places, Gironde plus halo bounding box | Current release (archive it: releases stay online 60 days) | `s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*`, read with DuckDB | `data/raw/overture/{release}/` |
| [ ] | 15 | National travel survey EMP 2019, public tables | 2018–2019 | `https://www.statistiques.developpement-durable.gouv.fr/resultats-detailles-de-lenquete-mobilite-des-personnes-de-2019` (also `https://www.data.gouv.fr/datasets/6285e9adf8a6866bbd8bddb9`) | `data/raw/emp2019/` |
| [ ] | 16 | EMC² Gironde | 2021 | Cerema (restricted) | `data/raw/emc2/gironde_2021/` |
| [ ] | 17 | Households by number of cars | 2022 | `https://www.data.gouv.fr/datasets/part-des-menages-selon-le-nombre-de-voiture-a-disposition` | `data/raw/cars/2022/` |

## C. National run (later)

| ✓ | Dataset | Notes |
|---|---|---|
| [ ] | OSM for the neighbouring countries (BE, LU, DE, CH, IT, MC, ES, AD), 2022-01-01 and 2024-01-01 | Country or sub-region dated extracts, as in `legacy/00_download_neighbor_pbf.py` |
| [ ] | All French GTFS feeds and border feeds | transport.data.gouv.fr API; foreign portals |
| [ ] | Fichiers fonciers, all départements | Cerema |
| [ ] | BD ALTI 25 m, all départements | data.gouv.fr |
| [ ] | NUTS 2024 boundaries | `https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics` |
| [ ] | Eurostat NUTS3 employment `nama_10r_3empers`, 2021 and 2023 | `https://ec.europa.eu/eurostat/databrowser/view/nama_10r_3empers/default/table?lang=en` |
| [ ] | Eurostat national employment `lfsi_emp_a`, 2021 and 2023 | `https://ec.europa.eu/eurostat/databrowser/view/lfsi_emp_a/default/table?lang=en` |
| [ ] | Overture places for France and foreign NUTS3 | Same S3 path; archive the release |
| [ ] | The other 13 EMC² surveys | Cerema; list in section 5.4 of the spec |
