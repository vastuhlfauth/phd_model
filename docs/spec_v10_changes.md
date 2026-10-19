# Specification version 10 (16 October 2026, after the research meeting)

This archive holds every file of `docs/spec` changed since version 8, so it applies whether or not version 9 was already committed. Version 9 changes (rebuilt PT method, national acquisition) are described in `spec_v9_changes.md`; this note lists what the meeting added.

| Meeting outcome | Where | What changes |
|---|---|---|
| 1. Compare a grid graph with only the contiguous cells | 8.3, 8.4, 3, 10.3, 13, 14.5, 14.8, 15 | The neighbourhood is no longer fixed at 24: 8, 16 and 24 neighbours are built and compared in the pilot (runtime and error against OSRM). A table gives edges (4.4, 8.7 and 13 million) and the overstatement of straight trips (mean / maximum: 5.5% / 8.2% with 8 neighbours, 1.4% / 2.7% with 16 or 24). With 8 neighbours searches are about three times faster, the bias is mostly systematic and can be partly corrected, and the graph suits congestion best. |
| 2. Better "central" point of a cell | 4.2, 14.7, 14.5 (step 9) | The point is the network node of the cell that minimises the occupied-dwelling-weighted distance (a weighted 1-median), among nodes of local roads open to cars (1 km cells) or of the foot network (200 m cells), in the main component. Weights are dwellings occupied as main residences in the Fichiers fonciers; opportunities when there are none. Points are fixed on the baseline for all states and scenarios. |
| 3. Test other routing options (AequilibraE) | 14.6, 13, 12, 14.8 | AequilibraE 1.7 is added: benchmarked on the pilot against the compiled Dijkstra for skims (runtime, agreement, cutoffs, products of 10.2) and candidate engine for assignment. Full national skim matrices do not scale, which the benchmark must address. |
| 4. Scenarios without new local roads | 11.3, 11.4, 11.6, 11.8, 8.1, 8.4, 3, 5.5, 0 | Road scenarios edit the reduced network only: speed limits, capacities (new `road_capacity` edit), bike infrastructure shares, new trunk sections. `road_add`, `road_remove` and `car_to_bike` are removed. `urban_extension` copies the edge properties of neighbouring cells or of cells of the same type of development (new `development` parameter). Level 2 is now the trunk graph and the GTFS only. Grid edges carry a capacity from the start. |
| 5. Calibrate a BPR function on the reduced network | 12 (rewritten), 1, 9, 14.7, 14.8, 13, 15 | BPR on grid edges and trunk links, α and β per edge group; two definitions of grid-edge capacity to test (bottleneck of the path; screenline across the cell boundary) with a calibrated scale; peak-hour demand (MOBPRO car flows until the demand models exist); static user-equilibrium assignment within a period; calibration on Google peak times with an edge-level check from polylines. |

## Open points added

- Equilibrium within each period, or the out-of-equilibrium loop of version 9 (12).
- Peak-hour factor and share of non-commuting car trips for the provisional demand (12).

## Not changed

Figure 6 still shows "OSM edges" among level 2 edits; it should be redrawn with "trunk graph, GTFS".

## How to apply

From the repository root in PowerShell:

```
Expand-Archive -Path spec_v10.zip -DestinationPath . -Force
git add docs
git commit -m "Spec v10: meeting outcomes (neighbourhood, points, AequilibraE, scenarios, BPR)"
```
