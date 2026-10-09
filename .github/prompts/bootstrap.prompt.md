---
description: Create the repository skeleton (run once)
agent: agent
---

Read [the project instructions](../copilot-instructions.md), [the spec index](../../docs/spec/README.md) and [section 14](../../docs/spec/14_implementation.md).

Create the repository skeleton of section 14.2:

1. **`pyproject.toml` for uv,** Python 3.12, one workspace with the four packages `common`, `acquire`, `landgrid`, `mobgrid` under `packages/`.
   - Dependencies for now: duckdb, pyarrow, numpy, numba, pydantic, pyyaml, httpx, pytest, ruff.
   - Other packages are added later, by the step that needs them.
2. **Package folders and modules** as listed in section 14.2. Each module holds only a one-line docstring naming the spec section it will implement.
3. **`config/`:**
   - `base.yaml`;
   - `pilot.yaml`: département 33 (Gironde) with a 50 km halo, years 2021 and 2023, every path under `data/`;
   - `energy.yaml`, `landuse.yaml`, `sources.yaml`: comments only, each naming the spec section that will fill it.
4. **Configuration loader** in `common` with pydantic models for `base.yaml` and `pilot.yaml`, plus a test that rejects invalid values.
5. **Tests and repository files:**
   - `tests/` with one smoke test;
   - pytest and ruff configuration;
   - a `.gitignore` excluding `data/` and caches.

No data logic yet.

Run `uv sync`, `uv run ruff check .` and `uv run pytest -q`. Then fill in `docs/progress.md`: mark the skeleton as done and list anything you assumed.
