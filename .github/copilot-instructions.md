# Project instructions

## What this project is

A Python pipeline that builds, for metropolitan France:

- **`landgrid`**: origins (population, households, dwellings at 200 m) and opportunities (jobs, services, nature, social) per cell, year and scenario;
- **`mobgrid`**: multimodal O-D costs and accessibility (time, distance, bodily energy, monetary cost) for walk, bike, car and public transport (PT).

It covers two states (2021 and 2023) and scenarios. The full specification is in `docs/spec/`; start with `docs/spec/README.md`. **The spec is the source of truth.** When code and spec disagree, or the spec is unclear, stop and ask before writing code.

## Where things are

- `docs/spec/`: the specification, one file per section (cite as "section 9.3").
- `docs/data/`: one page per dataset (columns, types, units, samples). Read it before using a dataset. **Never guess a column name.**
- `docs/progress.md`: what is done, decisions, assumptions, open points. Read it first; update it at the end of every task.
- `config/`: every parameter, in YAML, validated with pydantic. No parameter, path, year or threshold in code.
- `data/`: raw and derived data, never committed. `data/raw/` is read-only.
- `legacy/`: previous scripts, for reference only. Do not import them.

## Conventions

- **Coordinates:** EPSG:3035 (metres) everywhere. Other systems only when reading inputs or writing maps.
- **Cell ids:** `(N // res) * 100_000 + (E // res)`, with the resolution (200 or 1000) stored alongside. INSPIRE codes `CRS3035RES{res}mN{N}E{E}` for joins with INSEE files. 25 cells of 200 m in each 1 km cell.
- **Units:**
  - time in seconds, stored in 10 s units;
  - distance in metres, stored in 10 m units;
  - energy in kJ above rest for the reference mass in `config/energy.yaml` (74 kg), stored in 0.1 kJ units;
  - net MET-minutes are derived.
- **States and geography:** 2021 and 2023. Physical stocks are dated 1 January of the following year. Communes and EPCI use the 2026 geography, NUTS the 2024 version.
- **Storage:** Parquet, partitioned by scenario, mode and tile. Integer and float32 types.

## Stack

- Python 3.12 with `uv`.
- DuckDB (spatial, httpfs) for all table work.
- pyarrow and Parquet for storage.
- numpy and numba for graph searches on CSR arrays.
- pydantic and PyYAML for configuration.
- pytest and ruff.

Rules for speed:

- No pandas or geopandas in hot paths (allowed for small reports and plots).
- No Python loops over large arrays or tables.
- Read large files lazily with DuckDB. Never load a national file in memory in a test.

## How to work

1. **One task at a time:** one step of the table in section 14.5, or one explicit request. Do not start other steps.
2. **Plan first** when a task touches more than one package or needs a new dependency; wait for approval.
3. **Tests first:** write the acceptance tests with the reference numbers of the spec, check that they fail, then implement until they pass.
4. **Keep functions small and typed,** with docstrings that state units and the spec section they implement.
5. **`[TO CONFIRM: …]` items:** use the value in `config/`, mark it with a `TODO(confirm)` comment, and list it in `docs/progress.md`. Never invent a value silently.
6. **Before finishing,** run `uv run ruff check . && uv run pytest -q` and fix every failure.
7. **Finish** by updating `docs/progress.md`: what was done, assumptions, open points.

## Do not

- Do not edit `data/raw/`, `docs/spec/` or `legacy/`.
- Do not hard-code paths, URLs, years, thresholds or API keys. Keys come from environment variables.
- Do not add a dependency without saying why.
- Do not commit to `main`. Work on the branch of the step.
