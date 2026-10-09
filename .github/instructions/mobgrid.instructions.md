---
applyTo: "packages/mobgrid/**"
description: Rules for networks, energy, O-D costs and scenarios (mobgrid)
---

# mobgrid: networks, energy, O-D costs

Spec: `docs/spec/08_networks.md`, `docs/spec/09_trip_legs_energy.md`, `docs/spec/10_od_accessibility.md`, `docs/spec/11_scenario_engine.md`.

## Graphs and searches

- **Graphs** are CSR numpy arrays (`indptr`, `indices`, weights): float32 weights, int32 or int64 ids. They are built with DuckDB and passed through Arrow.
- **Searches:**
  - written in numba (`@njit(cache=True)`);
  - bounded multi-source Dijkstra with a cutoff and initial offsets;
  - the search minimises time;
  - along the fastest path it accumulates the secondary weights: distance, the two parts of bike energy, time per road class, climb, length on separated bike infrastructure.
- **Reusable workspace:** no allocation inside a search; generation stamps instead of resetting arrays.
- **Three products per search** (section 10.2):
  - the O-D table, for job and social destinations;
  - the opportunity curves (Δt = 1 min, Δx = 250 m, Δe = 10 kJ);
  - the nearest destinations: the k of each group plus 2.
- **Grid graph:** 24 neighbours (the 5 × 5 block). The stray check uses the cells crossed by the straight segment.
- **Car trunk:** a node-based layer (motorways and `trunk` + `motorroad=yes`), attached to 1 km cells through connectors.
- **PT:** stop areas are network elements; access and egress on foot from 200 m cells within 20 min; window 08:00–09:00.

## Energy (section 9)

- Formulas exactly as in section 9, with body mass as a parameter.
- Bike energy is stored as a per-kg part and a drag part.
- Rates come from the rate set chosen in `config/energy.yaml` (KH or Compendium).

## Reference numbers for tests

70 kg unless stated.

**Units and walking**

| Quantity | Expected |
|---|---|
| 1 net MET-minute | 0.0732 × m kJ: 5.13 kJ at 70 kg, 5.42 kJ at 74 kg |
| Walking on the flat, Compendium | c0 = 2.29 J/kg/m, so 160 kJ per km |
| Walking on the flat, KH | 211 kJ per km |
| Minetti gradient factor g | 1.44 at +5%, 1.96 at +10%, 0.45 at −10% |
| Climbing 10 m of stairs | 22.9 kJ (0.20 m/s, efficiency 0.30); descending ≈ one third |

**Bike** (16 km/h on the flat, M = 85 kg, C_rr = 0.006, C_dA = 0.55 m², ρ = 1.2 kg/m³, η_d = 0.976)

| Quantity | Expected |
|---|---|
| Mechanical power | ≈ 52.5 W |
| Metabolic energy at ε = 0.24 | ≈ 13.1 kJ/min |
| +10 kg at the same power, on the flat | speed −2.4% |
| +10 kg at 100 W, on a 5% climb | speed −9.8% |
| One stop from 16 km/h | ½·M·v²/ε ≈ 3.50 kJ |

**PT and accessibility**

| Quantity | Expected |
|---|---|
| Wait for headway h, random arrivals | h/2 · (1 + CV²) |
| Radiative accessibility | A / (m + A) |

**Searches**

- Dijkstra gives the same distances as `scipy.sparse.csgraph.dijkstra` on random graphs.
- The products equal brute-force sums and minima.

## Scenarios (section 11)

- **Network edits** go to source tables (OSM edge table, GTFS) or to stored time components (level 1); never edit outputs, except level 3 sensitivity runs.
- **Triage thresholds:** full run above 30% of affected origins; 2 min per added stop on a reopened line; 2% gap for interpolation bounds.
