---
description: Document a raw dataset in docs/data before any step uses it
agent: agent
argument-hint: dataset folder name under data/raw, e.g. filosofi
---

Document the dataset in `data/raw/${input:dataset:folder name under data/raw}`. Do not modify the data.

1. List the files, including the content of any zip archive.
2. For each table file, use DuckDB to get the schema, the row count and 20 sample rows, without loading the whole file into memory:
   - CSV: `read_csv`;
   - Parquet: `read_parquet`;
   - GeoPackage, Shapefile or GeoJSON: `ST_Read`;
   - OSM PBF: `ST_ReadOSM`, limited to a few thousand rows.
3. Write `docs/data/${input:dataset}.md` with the template of [docs/data/README.md](../../docs/data/README.md):
   - source and vintage, files, row counts;
   - for each column: name, type, unit, meaning, example;
   - keys and joins with other datasets, CRS;
   - quirks: missing values, special codes, encodings, separators.
4. Add one line for the dataset in the index of `docs/data/README.md`.
