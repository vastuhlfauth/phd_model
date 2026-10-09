# 7. Opportunities: jobs, services, nature, social

## 7.1 One rule for every layer: control totals times allocation keys

For a cell c, a sector or type k, a year t and a scenario s, the opportunity count is the control total of the cell's zone Z multiplied by the cell's share of the allocation key within that zone:

```text
O(c,k,t,s) = T(Z(c),k,t,s) × w(c,k,t,s) / Σ_{c' in Z} w(c',k,t,s)
```

Macro-economic dynamics enter through the totals T (for example sector growth by EPCI); local changes enter through the keys w (new premises, a business park, a new hospital). Opportunities are stored at 200 m and aggregated to 1 km. The `landgrid` module is independent of the networks: a macro scenario reruns only these tables, in seconds to minutes.

**One destination grid with flags.** Every 200 m cell, and every 1 km cell, carries one flag per opportunity type: jobs, each service group, each nature class, social, PT stop classes. A cell can hold jobs, services, both or none; it is a destination if any flag is set, and each search reaches it once whatever the number of types (section 10).

**How each type is measured** (section 10.2):

| Type | Measure | Stored per origin and mode |
|---|---|---|
| Jobs (total and by sector) | Radiative accessibility; time, distance, energy and monetary cost of each O-D pair, for the distribution model and modal shares | Opportunity curves; O-D table |
| Social (population) | Radiative accessibility, calibrated on surveys; time, distance, energy and monetary cost of each O-D pair | Opportunity curves; O-D table |
| Services (BPE groups of section 7.3) | First one, or first k, in reach; time to reach all types of a set | Time, distance and energy of the k nearest |
| Nature (each class) | First one in reach | Same |
| PT stops (for walk and car) | First one in reach, by class of stop | Same |

## 7.2 Jobs

- **Control totals:** INSEE EMP (employment at place of work) by EPCI and sector, in INSEE's simplified sector classification (aggregated NACE), 2021 and 2023. Jobs are downscaled from EPCI to 200 m and validated at commune level with the same source: the same data at two scales.
- **Main key: Fichiers fonciers premises.** The sector of each professional premises comes from `cconac` (NAF code of the occupant, aggregated to INSEE's simplified classification); its weight is its main surface `sprincp`; `typeact` refines the type of activity. Within an EPCI and a sector only shares matter, so a constant density of jobs per m² cancels out; densities that vary by type of premises can be calibrated. Premises without `cconac` are dropped.
- **Public sector** (administration, education, health, social work): premises of public bodies are largely exempt from property tax and poorly described in the Fichiers fonciers. Keys come from OSM building footprints, times levels where tagged:
    - Amenities: `school`, `college`, `university`, `kindergarten`, `hospital`, `clinic`, `townhall`, `courthouse`, `police`, `fire_station`, `prison`, `post_office`, `post_depot`, `library`, `research_institute`, `social_facility`, `social_centre`, `community_centre`, `arts_centre`, `baby_hatch`, `ranger_station`, `animal_shelter`; and `office=government`.
    - Buildings: `building=civic`, `college`, `fire_station`, `government`, `hospital`, `kindergarten`, `museum`, `public`, `school`, `train_station`, `university`.
    - `landuse=education` and `landuse=institutional` are not used, to avoid counting the same site twice.
- **One feature per site.** OSM maps an amenity as a node, a node on a way or on a building outline, or an area that may coincide with the building (dual tagging). Surfaces always come from building footprints: a building takes the type of its own tags, or of the amenity area it lies in, or of the amenity node it contains or carries on its outline; each building is counted once. An amenity with no building footprint gets a default surface by type [TO CONFIRM: default surfaces].
- **Comparison method: Overture POIs** mapped to NACE, as in the existing Monte Carlo study (best configuration on Gironde), without the population-in-reach scaling. The two methods are scored on the same commune-level validation.
- **Agriculture:** OSM land use (area times annual work units per hectare) as a comparison only.
- **Construction:** three keys compared: (a) Fichiers fonciers premises with a construction NAF code; (b) population, in cells with more than 200 inhabitants (existing rule); (c) OSM construction sites: `building=construction`, `highway=construction`, `landuse=construction`, `railway=construction`. Construction sites are temporary, so (c) depends on the date of the OSM extract.
- **Not used:** population-in-reach scaling (possibly later); Sirene (multi-site firms booking staff at one establishment, registered offices, coarse size bands); Flores (replaced by EMP).
- **Abroad:** NUTS3 totals (Eurostat `nama_10r_3empers`) allocated with the Overture method.
- **Dynamics:** economic planning scenarios (continued metropolisation, decentralisation) defined as trajectories of totals by EPCI and sector, to be provided; keys change with new premises between millésimes and with scenario projects.

## 7.3 Services

- **Source:** BPE 2021 (baseline) and BPE 2025 (for the 2023 state), geolocated per equipment; location quality is not a concern (errors below 100 m). INSEE revised the nomenclature in 2023, so each group below is defined in both nomenclatures, from INSEE's lists of equipment types for 2021 and 2025.
- **Measure:** set per group: the nearest, the k nearest, or the time needed to reach every type of a set. Two more destinations than required are kept to handle closures (section 11).

Groups retained:

| Group | Measure | BPE 2021 codes | BPE 2025 codes (2023 nomenclature) |
|---|---|---|---|
| Primary school | Nearest | C1: C101, C102, C104, C105 | C1: C107, C108, C109 |
| Lower secondary | Nearest | C2: C201 | Same |
| Upper secondary | Nearest | C3: C301 to C305 | Same |
| University | Nearest | C5: C501 to C505, C509 | Same |
| Childcare | Nearest | D502 | Same |
| Large food stores | Nearest | B1: B101 hypermarket, B102 supermarket | B1: B104, B105 (wider scope: department stores, multi-stores) |
| Convenience stores | Nearest | B201 | Same |
| Employment agency | Nearest | A122 (Pôle emploi) | A122 (France Travail) |
| General practitioner | Three nearest | D201 | D265 |
| Specialists | Time until all four are reached | D207 psychiatry, D208 ophthalmology, D210 paediatrics, D221 dentist | D269, D270, D272, D277 |
| Sports | Three nearest among the four types | F101 pool, F103 tennis, F107 athletics, F109 fitness trail | Same |
| Restaurants | Five nearest | A504 | Same |

**Note on B1.** The prefix B1 also contains B103, DIY superstores, in both nomenclatures; for food, B103 is excluded. For the back-test, both vintages are mapped to these common groups, so that changes of nomenclature are not read as openings or closures.

- **Dynamics:** scenarios open or close services; a presence model based on thresholds of population in the catchment (Berry & Garrison 1958), estimated on BPE, can project them under population or macro scenarios.

## 7.4 Nature

- **Sources:** OSM forests and woods (`landuse=forest`, `natural=wood`), parks (`leisure=park`, at least 2,500 m², i.e. 50 m × 50 m), protected areas (`boundary=protected_area`, `boundary=national_park`), sea beaches (`natural=beach` near `natural=coastline`, as in the current scripts) and rivers (`water=river`) instead of all water bodies.
- **Access points:** where the walk, bike or car network crosses or meets the polygon boundary, plus OSM entrances, plus points every 50 m along the contour. Destinations are the cells containing access points. Access starts at the edge, not at the centroid, which can lie kilometres from any entrance.
- **Measure:** the first one in reach for each class, without weighting by size.
- **Dynamics:** mostly static; scenarios can add or remove areas (new park, greening).

## 7.5 Social opportunities

- **Purpose:** visits to family and friends, measured as population within reach.
- **Destinations:** 200 m cells with more than 50 inhabitants (walk and PT) and 1 km cells with more than 200 inhabitants (bike and car), from the origin tables; France only.
- **Measure:** radiative accessibility from the opportunity curves (section 10.2), calibrated on surveys (EMP 2019, EMC²); time, distance, energy and monetary cost of each O-D pair in the O-D table, for modal shares.
- **Dynamics:** follows the population of each state and scenario.

## 7.6 Outputs and use

- `jobs(year, scenario, cell_id, sector, jobs)`, `services(year, scenario, cell_id, group, count)`, `nature(year, scenario, cell_id, class, access_points)`, `social(year, scenario, cell_id, population)` at 200 m and 1 km, and `destinations(year, scenario, res, cell_id, flags)` with one bit per type.
- The economic model uses them as destination sizes; `mobgrid` uses the flags to decide which cells to record and the counts to fill the opportunity curves.
