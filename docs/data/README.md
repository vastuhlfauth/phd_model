# Data pages

One page per dataset, written with `/schema` before any step uses the dataset. Agents read these pages instead of guessing column names. Raw data live in `data/raw/{source}/{vintage}/` (not committed); the download list is in [download_checklist.md](download_checklist.md).

## Index

| Dataset | Page | Vintages | Used by step |
|---|---|---|---|
| GTFS acquisition inventory | [gtfs.md](gtfs.md) | Configured snapshot; service dates checked independently | 2, 0 |
| EMP 2019 public tables | [emp2019.md](emp2019.md) | Fieldwork 2018-2019; public release December 2021, updated November 2024 | 11 |

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
