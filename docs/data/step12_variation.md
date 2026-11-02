# Step 12: what explains the variation of daily travel time

This report is generated (together with its figures, under
`docs/data/step12_variation/`) by:

```
uv run python -m mobgrid.budget.variation_report --out docs/data/step12_variation
```

It has not been generated on the real data yet (step-12 rule: no full
real-data runs inside the agent session). A 2% household smoke run
(`--sample-households 2`) validated the full pipeline end to end:
Parts A1-A5 (recall lag, motive crosswalk, distances, duration
rounding, calendar) and B1-B7 (composition V1-V3, trips x km x speed,
mode/motive/distance shift-shares, tails, comparison pairs 1-4,
figures). Run the command above to replace this placeholder with the
full report.
