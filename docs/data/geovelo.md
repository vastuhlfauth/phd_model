# Géovélo cycle infrastructure

- **Source:** Geovelo; `geovelo-2022` in `config/sources.yaml`.
- **Vintage:** 18 July 2022; used as the 2021 validation source.
- **Local path:** `data/raw/geovelo/2022-07/geovelo-2022.geojson`.
- **Format:** GeoJSON, approximately 198 MB in the configured manifest.
- **CRS:** WGS 84 (EPSG:4326); the step 6 report transforms and clips line
  geometries to the 2021 commune contours in EPSG:3035.
- **Licence:** consult the source resource; it is not recorded in the manifest.

## Fields used by the step 6 report

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `OGC_FID` | int64 | none | Feature identifier supplied by DuckDB's GeoJSON reader |
| `ame_d` | string, nullable | none | Right-side facility classification |
| `ame_g` | string, nullable | none | Left-side facility classification |
| `geom` | geometry, EPSG:4326 | degrees | Facility line geometry |

Other source fields are retained by the reader but are not used in this
comparison. Amenagement values are normalized for case and surrounding
whitespace before mapping; unrecognized non-empty values are excluded from
family totals and counted by the report.

## Sample

| `ame_d` | `ame_g` | `geom` |
|---|---|---|
| `BANDE CYCLABLE` | `BANDE CYCLABLE` | LineString |

The report uses only features intersecting the configured pilot department.
Each mapped amenagement side contributes the clipped geometry length once;
two separated-facility fields on one feature count once.
