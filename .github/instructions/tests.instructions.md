---
applyTo: "tests/**"
description: Rules for tests
---

# Tests

## Structure and fixtures

- One test module per source module, in the same structure as `packages/`.
- Fixtures in `tests/fixtures/` are small: synthetic, or pilot extracts under 10 MB.

## What to test

- **Acceptance tests** come from the table of section 14.5.
- Use the reference numbers of the spec with explicit tolerances (see `.github/instructions/mobgrid.instructions.md`).
- **Downscaling tests** always check that zone totals are preserved.

## Rules

- **Deterministic:** fixed seeds, no dependence on the current date.
- **Isolated:** no network, and no access to `data/raw/` in unit tests.
- **Pilot data:** tests that need pilot data are marked `@pytest.mark.pilot` and skipped when the data are absent.
