# 10. Computing O-D costs and accessibility

## 10.1 Searches by mode

| Mode | Per-origin computation | Destinations | Stored O-D table |
|---|---|---|---|
| Walk | Search with 45-min cutoff from each 200 m cell on the foot graph | 200 m cells within reach | 200 m pairs, in full |
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

> **Performance expectation, to be confirmed in the pilot.** The 1 km grid graph has about 544,000 nodes and about 13 million directed edges with 24 neighbours (4.4 million with 8, section 8.3). Cutoff searches touch hundreds of nodes (bike) to tens of thousands (car at 120 min), which a compiled Dijkstra handles in milliseconds to tens of milliseconds, so a national car run should take tens of minutes on a multi-core workstation. PT from 2.3 million 200 m origins dominates total time; the fast variant of section 8.6 and parallel tiles are the levers.

## 10.4 Mobility model: mode use, time per mode and destinations

The mobility model turns the persons of section 6 and the products of section 10.2 into daily mobility per cell: which modes people use, how long they spend in each and where they go. It rests on the per-mode constant of section 9.9 (decision of 20 November 2026): each mode m has one national distribution f_m of minutes per user day, and people and places differ through the modes they use and how far their activities are. Total daily time is an output, not a constraint. The unit is a weekday of a resident aged 6 or more, under the reference scope of section 9.9 (local round trips made to do something at a destination). Saturday and Sunday get their own f_m and their own mode-use model in a later version (decision of 20 November 2026); the first version covers weekdays.

```text
1. mode use        P(g | category, income, household type, vehicles, accessibility of c)
2. required time   r_m(c, k, g) = Σ_p n_p,m,k,g · 2 · t̄_p,m(c)
3. allocation      the group (c, k, g) holds the slice [a, b] of the national ranking of r_m
                   V ~ U[a, b],   U = Φ(ρ_m · Φ⁻¹(V) + √(1 − ρ_m²) · ε),   ε ~ N(0, 1)
                   t_m = δ_m · F_m⁻¹(U)
4. destinations    P_m(d | p, c) ∝ P_rad(d | p, c) · exp(−β · t_m(c, d)),
                   β such that the day's trips in m take the group's mean allocated time
```

**1. Mode use: day patterns.** A weekday is described by its pattern g, the set of modes used, grouped as the day-mode groups of section 9.9: walking only, bike, car driver, car passenger with a household driver, car passenger with a driver from another household, urban PT, train, multimodal and other modes, plus days without trips. Multimodal days are split by their main combinations (e.g. walking + urban PT + train) in a later version (decision of 20 November 2026); the first version keeps one multimodal group. The probability of each pattern depends on:

- equipment: household cars (section 6.4), driving licence, PT pass and bike [TO CONFIRM: licence, pass and bike are not known per cell; they are modelled from the surveys by category, income and household type, or enter only through those variables];
- the household's income quintile (section 6), household type (single person, couple, couple with children, single parent, other), from the synthetic population of section 6.1 (decision of 20 November 2026), and the person's population category (section 6.1);
- accessibility by each mode and opportunity type, from the products of section 10.2, measured in either of two ways (decision of 20 November 2026): the time to the 1st, 2nd and 3rd nearest opportunities (nearest destinations), or the opportunities reachable within 15, 30 and 45 minutes (opportunity curves); the estimation compares the two.

The model is a multinomial logit, nested only if the tests call for it (decision of 20 November 2026). It is estimated on EMP 2019 and re-estimated on ENTD 2008 with the variables both surveys share, for the transfer test (validation, below). Density classes are not used: neither mode use nor time depends on them in the model (decision of 20 November 2026); they remain a test dimension only. Accessibility effects need each respondent's residence, which the public EMP 2019 and ENTD 2008 tables do not give. They are estimated where the residence is known: the EMC² surveys (14 EPCIs, fine zones), the census commuting file MOBPRO (commune of residence and commuting mode, all of France), and EMP 2019 with its residence commune if restricted access (CASD) is obtained [TO CONFIRM: estimation sources, and how the accessibility terms are combined with the national person and household terms]. Accessibility also acts through household cars, whose commune model rests on accessibility (section 6.4). Until accessibility terms are estimated, mode use responds to network scenarios only through household cars. Mode use carries more of the differences between people than any population grouping: in EMP 2019 the day-mode group explains 16% of the variance of daily minutes, population category 4%, and income, density, household vehicles and household type under 1% each (section 9.9).

**2. Required time per mode.** For persons of category k in cell c on days of pattern g, the time their activities require in mode m is r_m(c, k, g) in the block above, where:

- n_p,m,k,g is the number of trips per weekday for purpose p (work, education, shopping and services, nature, social, other) made in m by persons of category k on days of pattern g (EMP 2019 and EMC², reference scope);
- t̄_p,m(c) is the one-way door-to-door time by m from c for purpose p. For services and nature it is the time to the nearest destinations of each type, in the number required by section 7.3. For work, education, social and other purposes it is the mean time of the radiation model's destination probabilities (section 10.2; extended radiation calibrated on MOBPRO for work);
- 2 counts the return; a tour with several stops is counted once, under its main purpose.

A purpose with no destination within the search cutoff of m (section 10.1) is not counted in r_m [TO CONFIRM: rule for purposes out of a mode's reach]. In sparse cells fewer purposes lie within walking reach, which is how the model should reproduce the fall of walking time with density (section 9.9). The ranking key is time: the distance to the destinations that meet the needs, covered at the mode's speeds. Areas that are farther but faster then rank like near and slow ones, as the surveys show for motorised modes (decision of 20 November 2026).

**3. Allocation within f_m.** Persons are grouped by cell, category and pattern. For each mode of the pattern, the groups are ranked nationally by r_m, each weighted by its persons, so that group (c, k, g) holds the slice [a, b] of the weighted ranking, between 0 and 1. Its persons take times in f_m as in the block above:

- V, the latent rank, is uniform on the group's slice;
- ε is the individual part of daily time, which geography does not explain;
- ρ_m sets how far the required time orders persons within f_m. With ρ_m = 1 each group takes the slice of f_m between its quantiles a and b; with ρ_m = 0 every group takes the whole f_m.

Over the whole population V is uniform, hence U too, so f_m (scaled by δ_m) is reproduced exactly whatever ρ_m. Group means are computed by quadrature, without simulation. ρ_m is calibrated on the EMC² surveys, whose finer zones let each respondent's required time be computed and set against the declared time; failing that, on time per user day by population category in EMP 2019, leaving density and the other groupings for validation [TO CONFIRM: calibration of ρ_m].

Ranks are always national, also when a scenario touches one area: the other areas keep their required times, so a local change moves local persons within f_m and leaves f_m whole. A multimodal day takes one allocation per mode it uses (f_m pools every user day of m, single-mode or multimodal); its total is their sum.

**4. Destinations.** Trips for services and nature go to the nearest destinations of each type. Trips for work, education, social and other purposes go to destinations drawn from the opportunity curves by the radiation model, tilted so that the day's trips in m take the group's mean allocated time.

- β is solved, not estimated: the tilted probabilities are the closest to the radiation model's that meet the time constraint (entropy maximisation, Wilson 1967). β = 0 when the allocated time equals the required time, β > 0 when it is shorter, β < 0 when it is longer.
- If the allocated time is shorter than the nearest destinations require, the nearest are kept and the excess is reported (decision of 20 November 2026).
- For work and education, the tilt acts on the cell's flows, which stand for job and residence choices made over years (Levinson & Kumar 1994), not on daily choices.
- The extended radiation parameter is calibrated on MOBPRO with the tilt in place, iterating between the two until both settle (decision of 20 November 2026).

The O-D flows by mode and purpose follow; car flows feed the congestion loop (section 12).

**Outputs** per cell, by population category and pattern, weighted by persons:

- minutes, km, energy (section 9) and monetary cost (section 9.10) per mode;
- total daily time, T(c) = Σ_k p_k(c) · Σ_g P(g | c, k) · Σ_{m ∈ g} t̄_m(c, k, g), where t̄_m is the group's mean allocated time;
- the shares of patterns and of persons using each mode, and mode shares of trips, km and time;
- O-D flows by mode and purpose;
- the daily time per population category, b_k, kept to validate the model against the surveys.

**Travel outside the scope.** The model covers the reference scope only: in 2019, 57.0 of the 61.9 minutes per person and weekday of the published indicators (52.0 of 56.4 in 2008). The rest (days that do not close at home, holidays and second or occasional residences, walking or cycling as the activity itself, professional rounds) is added at its observed level per population category, unchanged across scenarios, whenever totals are compared with published figures (decision of 20 November 2026).

**Drift.** δ_m scales f_m; its default is 1, so time per user stays at its 2019 level. The 2008–2019 change sets the order of magnitude for sensitivity runs: car driver 1.066 [1.039, 1.101] in 11 years, mostly longer and slower commuting trips that the literature and macro speed data do not explain; car passenger 1.129, train 1.082, walk 1.053, urban PT 1.040 (section 9.9). With δ_m = 1 the model misses about 7% of the mean daily time per person over 11 years (53.5 against 57.0 min in the survey counterfactual), and scenarios beyond a few years state that error [TO CONFIRM: δ_m as a yearly trend in long-horizon runs, or only as a sensitivity]. f_m is a medium-run constant. From 1982 to 2008, motorisation moved many trips from walking to the car while total daily time rose by only 3% (published aggregates of the national surveys); with fixed f_m, each point of person-days moving from walking-only days (36.6 min in 2008) to car-driver days (63.6 min) adds about 0.27 min per person. Either per-mode times adjusted over those decades, or other changes offset the shift; the earlier surveys are available only as published aggregates, so this cannot be tested (section 15).

**Scenario behaviour.**

| Scenario | What the model does | What stays fixed |
|---|---|---|
| A mode gets faster (road, PT line, cycle track) | Required times fall where it gets faster. A uniform speed-up leaves ranks unchanged: users keep their time and go farther. A local one moves the area's users down the national ranking: with ρ_m above 0, part of the saving is kept as time and the rest goes into farther destinations. Mode use shifts through accessibility | f_m |
| New users of a mode (a new PT line, households giving up a car) | They take that mode's distribution: an urban PT user day lasts 75 min, a car-driver day 64 (2019), so total daily time rises when drivers move to PT. This total-time effect of a modal shift is the model's least tested output (section 15) | f_m of each mode |
| Opportunities move away (jobs concentrate, a service closes) | Required times rise for those affected; they move up within f_m and others move down; destinations are redrawn within the allocated time | The national f_m: a general move away shortens the chosen destinations rather than lengthening days, unless δ_m is set (2008–2019: car drivers' time per user day rose by 6.6%) |
| Time per user drifts (sensitivity) | δ_m ≠ 1 scales the mode's times and, through the tilt, its distances | — |

**Validation** (section 13):

- cross-section, EMP 2019: time, km and speed per mode user day by density class (the INSEE density grid of the residence commune, given in the public tables; each model cell takes its commune's class), population category, income quintile, household vehicles, household type and day purpose (`docs/data/step12_mode_cells.md`), in particular the flat profile of motorised modes and the falling profile of walking across density; b_k per category;
- over time: the model run on the 2021 state with ENTD 2008's f_m and EMP 2019's mode use; its error against EMP 2019 should stay near the 7% of the survey counterfactual;
- transfer: the mode-use model estimated on ENTD 2008 predicts EMP 2019's patterns, with the variables both surveys share;
- commuting: modes and commune-to-commune flows of MOBPRO 2021 and 2023, and the back-test of 2021 to 2023 (section 11).
