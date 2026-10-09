# 10. Computing O-D costs and accessibility

## 10.1 Searches by mode

| Mode | Per-origin computation | Destinations | Stored O-D table |
|---|---|---|---|
| Walk | Search with 30-min cutoff from each 200 m cell on the foot graph | 200 m cells within reach | 200 m pairs, in full |
| Bike | Search with cutoff on the bike grid graph from each 1 km cell, plus terminal legs | 1 km cells within the bike cutoff | 1 km pairs |
| Car | Search with cutoff on the combined car graph, plus walking and parking legs | 1 km cells | 1 km pairs; optional bands beyond 30 km |
| PT | Range RAPTOR over 08:00–09:00 from each 200 m cell, started from stop areas within 20 min on foot; egress to 200 m cells | 200 m cells reached | Aggregated to 1 km pairs |

## 10.2 One search, three products

A search settles destination cells in increasing time. When it settles a flagged cell d with time t, distance x and energy e, it updates three products at once:

- **O-D table:** for cells holding jobs or social destinations, record (d, t, x, e) and, for PT, the components and route groups; the monetary cost follows (section 9.10).
- **Opportunity curves:** for each counted type k (jobs in total and by sector, population for social access), add the count O_k(d) to bin ⌊t/Δt⌋ of the time curve, bin ⌊x/Δx⌋ of the distance curve and bin ⌊e/Δe⌋ of the energy curve.
- **Nearest destinations:** for each service group, nature class and stop class held by d, record (d, t, x, e) until the number required by the group (one to five, section 7.3) plus two have been found; for a set of types (specialists), record the time at which the last type is first reached.

Accessibility measures are then computed afterwards, in DuckDB, from the curves: the opportunities within τ minutes, A, and the radiative accessibility, R:

```text
A_k(τ) = Σ_{b ≤ τ/Δt} H_k[b]
R_k(τ) = A_k(τ) / (m_k + A_k(τ))
```

- **Radiative accessibility.** In the radiation model (Simini et al. 2012), a trip leaving a cell with m_k opportunities of its own (its population, for social access) ends among the A_k(τ) opportunities closer than τ with probability A_k(τ) / (m_k + A_k(τ)), A being counted without the origin cell: the model's flows to destinations ranked by cost sum to this expression, so the curves give it exactly, up to one bin. It needs no distance-decay parameter and accounts for intervening opportunities. The extended radiation model (Yang et al. 2014) adds one parameter, calibrated on MOBPRO for jobs and on EMP 2019 and EMC² for social trips; it is computed from the same curves.
- **Bins:** Δt = 1 min, Δx = 250 m, Δe = 10 kJ; the error is at most one bin. Limits on time, distance and energy select different destinations, hence one curve per metric.
- **"Nearest" means nearest by time;** its distance and energy are those of the fastest path. The nearest by energy can be another cell (behind a hill); a second search with energy as weight can be added if needed.
- **This replaces the four-step process** (job grid, job O-D, service grid, services minus jobs): one flagged destination grid and one pass give all of it, and access to PT stops by walk or car is one more type.
- **Cost:** the search itself is unchanged; a settled flagged cell costs a few array updates. The curves also feed intervening-opportunity and radiation distribution models directly (Stouffer 1940; Simini et al. 2012).

> **Storage.** Opportunity curves with 7 counted types (6 job sectors [TO CONFIRM] and population) and 120 one-minute bins in 32-bit floats take about 15 GB per metric for the 200 m modes (2.3 million origins, walk and PT) and about 2.5 GB for the 1 km modes, before compression; cumulated curves are monotone and mostly empty at short costs, so they compress well. Nearest destinations (12 service groups plus nature and stop classes, one to five each plus two) are sized in the pilot.

## 10.3 Other rules

- **Time, distance and energy of the fastest path.** Searches minimise time; distance, energy, time per road class, climb and length on separated bike infrastructure are accumulated along the shortest-path tree as secondary weights, in the same compiled pass.
- **Intra-cell trips.** Walk and PT from the 200 m pairs; bike and car from the intra-cell network distance at mode speed, plus the terminal legs of section 9.
- **Outputs** are stored in long format, one row per scenario, mode, origin and destination: destination level (200 m, 1, 5 or 10 km), time (10 s units), distance (10 m units), energy (0.1 kJ units), all as 16-bit integers; for PT, the journey components and route groups; for bike, the two energy parts; for aggregates, min, max and spread of time. Files are Parquet, partitioned by scenario, mode and origin tile, and queried with DuckDB.

> **Performance expectation, to be confirmed in the pilot.** The 1 km grid graph has about 544,000 nodes and about 13 million directed edges with 24 neighbours. Cutoff searches touch hundreds of nodes (bike) to tens of thousands (car at 120 min), which a compiled Dijkstra handles in milliseconds to tens of milliseconds, so a national car run should take tens of minutes on a multi-core workstation. PT from 2.3 million 200 m origins dominates total time; the fast variant of section 8.6 and parallel tiles are the levers.
