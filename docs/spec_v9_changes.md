# Specification version 9 (16 October 2026): changes from version 8

Eight files of `docs/spec` change; the others and the figures are unchanged.

| File | Changes |
|---|---|
| `00_summary.md` | Version 9 header and "Changes in version 9" note; the "two states" decision now says that PT of both states is rebuilt from the 2026 timetables. |
| `05_data_acquisition.md` | **5.6 rewritten.** The stop-matching rule of v8 is replaced by the method actually built and run: precedence openings list > tram rule > default keep; the national openings list (content, mapping to GTFS routes, what each type of change does, results of the national run with the 120 rows in six categories); the OSM route-relation rule for trams (identity by name then geometry, coverage by any in-service track, cut then θ, parameters, known cases, calibration results by family and why only trams are applied); the edits file and its use in the state builder; limits. **5.1:** verification by checksum or size, failed files do not stop a batch, restricted files registered only, national coverage from the start. **5.3:** Filosofi 2019 added; OSM dated extracts checked by size (no `.md5`); Overture release 2026-09-23.1; GTFS snapshot of October 2026; new row for the openings list; Géovélo's earliest file (18 July 2022) stands for 2021. **5.4:** new notes on the GTFS inventory (producer resources, archive fallback, 552 resources, 536 passing checks, coverage of the 1,127 AOMs, networks published only on data.gouv.fr) and on Geofabrik dated extracts; Overture national box. |
| `08_networks.md` | **8.1:** Géovélo files for 2021 and 2023 decided. **8.6:** producer feeds; new rule "one copy per agency" (an agency's copy in a regional aggregate is dropped when it has its own feed); past states built from the precedence and edits of 5.6; reference day 13 October 2026; open point on feeds whose calendars have expired. |
| `11_scenario_engine.md` | **11.2:** the planned entries of the openings list give the dated PT events of a reference scenario. |
| `13_validation.md` | PT rebuilding: tram rule on known cases, openings list checked at each run, back-test limited to openings. |
| `14_implementation.md` | **14.2:** `pt` package contents. **14.3:** long-job policy and `docs/progress.md` added to the agent conventions. **14.4:** dated extracts checked by size; agencies repeated in aggregates. **14.5:** status (steps 0, 1, 2 merged); step 0 row describes the method built. **14.6, 14.7:** route-relation matching and route edits replace stop matching. **14.8:** phase 0 items marked done. |
| `15_risks.md` | Rebuilt PT supply: depends on the completeness of the openings list outside trams; OSM relations too incomplete for buses and rail. |
| `README.md` | Version 9; step status pointer; new "PT build" row in the later steps. |

## Open points added or closed

- Closed: Géovélo version for 2021 (the 18 July 2022 file stands for it); the `.md5` claim of 5.3.
- Added: whether to rebuild the 8 lines closed before 2026 from their OSM relations (5.6.4); rule for feeds whose calendars expired before the reference day (8.6, already in `docs/progress.md`).

## How to apply

From the repository root in PowerShell:

```
Expand-Archive -Path spec_v9.zip -DestinationPath . -Force
git diff --stat docs/spec
git add docs/spec
git commit -m "Spec v9: rebuilt PT method, national acquisition, status"
```

No coding agent is needed. At the next step, tell the agent that the specification is now version 9 and that section 5.6 replaces the stop-matching text it may remember.
