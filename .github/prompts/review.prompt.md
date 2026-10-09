---
description: Review the current branch against the spec (no changes)
agent: agent
argument-hint: step number, e.g. 3
---

Review the changes of this branch (`git diff main...HEAD`) for step ${input:step:step number}. Compare them with the spec files listed for this step in [the spec index](../../docs/spec/README.md) and with [the instructions](../copilot-instructions.md).

**Do not modify any file.**

Report, most important first, with file and line:

1. Departures from the spec: formulas, units, thresholds, outputs, names.
2. Missing or weak tests: acceptance tests of section 14.5, reference numbers, preservation of totals.
3. Performance problems:
   - Python loops over large arrays;
   - pandas in hot paths;
   - whole files loaded into memory;
   - allocations inside searches.
4. Paths, years, thresholds or keys hard-coded instead of being in `config/`.
5. Anything that will break or become too slow at national scale.

End with a short verdict: merge, or fix first.
