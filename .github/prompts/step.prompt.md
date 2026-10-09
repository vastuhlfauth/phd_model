---
description: Implement one step of the plan (section 14.5), tests first
agent: agent
argument-hint: step number from section 14.5, e.g. 3
---

Implement step ${input:step:step number from the table of section 14.5}.

1. **Read first:**
   - [the instructions](../copilot-instructions.md) and [docs/progress.md](../../docs/progress.md);
   - the row of this step in the table of [section 14.5](../../docs/spec/14_implementation.md);
   - only the spec files listed for this step in [the spec index](../../docs/spec/README.md);
   - the page in `docs/data/` of every dataset the step uses. If a page is missing, stop and ask me to run `/schema` for it.
2. **Plan.** Write a short plan: files, functions with signatures and units, tests. If the step touches more than one package or needs a new dependency, stop and wait for my approval.
3. **Tests first.**
   - Write the acceptance tests from the "Acceptance test" column, using the reference numbers of the spec.
   - Run them and check that they fail.
4. **Implement** until all tests pass.
   - Stay inside the package of this step.
   - Parameters go to `config/`, never into code.
   - Use DuckDB for tables and numba for graph code.
5. **Check.** Run `uv run ruff check . && uv run pytest -q` and fix every failure.
6. **Report in `docs/progress.md`:**
   - what was done;
   - the assumptions made;
   - the `[TO CONFIRM]` items used, with the value chosen;
   - open questions;
   - how to run the step on the pilot data.
