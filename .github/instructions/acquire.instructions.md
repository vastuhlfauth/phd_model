---
applyTo: "packages/acquire/**"
description: Rules for data acquisition (manifest, downloads, conversion)
---

# acquire: data acquisition

Spec: `docs/spec/05_data_acquisition.md`; links in `docs/data/download_checklist.md`.

## Manifest

- Every source is described once in `config/sources.yaml`: provider, version or release, URL or API query, licence, expected checksum, download date and local path.

## Downloads

- Downloads are idempotent (skipped when the checksum matches), resumable and logged.
- They write to `data/raw/{source}/{vintage}/`.
- **Restricted sources** (Fichiers fonciers, EMC² surveys) are never downloaded; only their local path and vintage are registered.
- **Overture extracts** are archived locally, because releases stay online for only 60 days.
- **Overture queries** use the schema of release 2026-09-23.0 or later: `taxonomy.*` or `basic_category`, not `categories`.

## Conversion and secrets

- Raw files are never modified.
- A separate conversion step writes Parquet in EPSG:3035, with cell ids, to `data/interim/`.
- API keys (for example `GOOGLE_MAPS_API_KEY`) come from environment variables only.

## Tests

- Tests mock the network: no real download in tests.
