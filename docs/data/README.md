# Data pages

One page per dataset, written with `/schema` before any step uses the dataset. Agents read these pages instead of guessing column names. Raw data live in `data/raw/{source}/{vintage}/` (not committed); the download list is in [download_checklist.md](download_checklist.md).

## Index

| Dataset | Page | Vintages | Used by step |
|---|---|---|---|
| GTFS acquisition inventory | [gtfs.md](gtfs.md) | Configured snapshot; service dates checked independently | 2, 0 |
| Commune contours | [commune_contours.md](commune_contours.md) | 2021 | 6 |
| BD ALTI 25 m elevation grids | [bdalti.md](bdalti.md) | Departmental editions in the manifest | 6 |
| OSM directed edges and car costs | [osm_edges.md](osm_edges.md) | 2022 and 2024 extracts | 6 |
| Géovélo cycle infrastructure | [geovelo.md](geovelo.md) | July 2022 | 6 |
| EMP 2019 public tables | [emp2019.md](emp2019.md) | Fieldwork 2018-2019; public release December 2021, updated November 2024 | 11 |
| Fichiers fonciers | [fichiers_fonciers.md](fichiers_fonciers.md) | 2022 (pilot 33); schema comparison 2021 and 2024 | 3 |
| Filosofi grids | [filosofi.md](filosofi.md) | 2019 and 2021 | 3 |
| Eurostat census grid | [eurostat_grid.md](eurostat_grid.md) | 2021, 1 km | 3 |
| Census dossier complet | [census_dossier_complet.md](census_dossier_complet.md) | 2021 and 2023, communes and larger geographies | 3 |

## Template for a dataset page

```markdown
# {Dataset name}

- **Source:** provider, URL, licence
- **Vintage(s):** …, reference date
- **Local path:** data/raw/{source}/{vintage}/
- **Files:** name, format, size, row count
- **CRS:** … (or none)
- **Keys and joins:** which column joins with which dataset

## Columns: {file}

| Column | Type | Unit | Meaning | Example |
|---|---|---|---|---|

## Quirks

- missing values, special codes, separators, encodings, known errors

## Sample

20 rows, as returned by DuckDB.
```
