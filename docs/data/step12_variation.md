# Step 12: travel-time variation

## Status

This is an implementation handoff, not a completed statistical report.
The full real-data reports were not run, as required by the step-12
prompt.

### Part C: equivalence summaries

The step-11 report path now includes household-bootstrap 90% intervals
for subgroup-to-category time ratios, with verdicts at the configured
±15% and ±10% margins. The 2008-to-2019 comparison uses independent
household bootstrap streams paired by replicate for the temporal ratios.
Suppressed per-person cells retain their true respondent count and show
`-` for values below the 50-respondent threshold.

The `--compare` report includes temporal ratios for weekday daily time
with trips (overall and by category), weekday per-person budgets, and
weekday daily time by category × density proxy. It also shows the
within-survey density and income equivalence summaries side by side.

### Part B2

The generic weighted log decomposition of daily time into trips, distance
and speed is implemented in `mobgrid.budget.variation`. A household
bootstrap computes independent survey replicates and 95% percentile
intervals for the total change and each component. This helper is
synthetic-tested, but is not yet connected to the report's category and
overall tables.

### Remaining Parts A and B

Recall-lag regressions, motive and distance diagnostics, duration and
calendar tables, composition reweighting, mode/motive/distance
shift-shares, tail analyses, the requested comparison pairs, and their
figures have not been implemented. No result or figure for these
analyses is claimed here.

### Part D

The EMC² and Île-de-France EGT source directories were not found in
`data/raw/`; see [emc2_inventory.md](./emc2_inventory.md). No field names,
counts, or mappings are inferred.

## Validation and next steps

Synthetic tests cover the equivalence bootstrap, temporal-ratio helper,
suppression behavior, and weighted log decomposition and bootstrap.
The full step-12 report remains incomplete: Parts A/B still require
implementation and integration, and the EMC²/EGT inventory requires the source files.
No real-data report command is provided until that report pipeline
exists.
