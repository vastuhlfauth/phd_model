# 2. What the literature says

## 2.1 Gridded network representations

**Raster friction surfaces.** Weiss et al. (2018) map travel time to cities worldwide at about 1 km: each pixel gets a movement speed in a friction surface, and a least-cost-path algorithm computes travel times. This is the reference raster approach.

**Economics precedent closest to this project.** Fajgelbaum & Schaal (2020) discretise European road networks, France included, into cells whose nodes connect to up to 8 neighbours. Each link's attributes come from the cheapest path on the real road network, and a link is dropped when that path runs mostly (over 50%) through other cells. They snap each node to the nearest national road in the cell. Their French grid is coarse (1-degree cells, 74 in total). Allen & Arkolakis (2014) compute trade costs on a continuous surface with the Fast Marching Method, which avoids directional bias.

**Known biases of grids:**

- **Raster vs network.** Delamater et al. (2012) found that the raster method flagged more people as having poor access and was more sensitive to speed settings, while the network method was more sensitive to how population was assigned.
- **Directional (metrication) error.** Lattice paths can only move in fixed directions. On a 4-connected raster, paths are about 41% longer than straight lines; 16-connected rasters cut this to about 2.7% (van Bemmelen et al. 1993). By the same geometry, 8-connected grids overstate by up to about 8%.
- **"Cracks".** Rasterising narrow features opens false shortcuts across barriers (Rothley 2005): crossing motorways or rivers without an interchange or bridge, or joining a motorway in any cell.
- **Level of detail.** Bovy & Jansen (1983) found that network detail has a consistent but diminishing effect on assignment results.

## 2.2 Locality and exact compression

- **Transit node routing** (Bast et al. 2007). A locality filter decides whether a query is local; long-distance queries go through a small set of access nodes. The grid-based variant defines each cell's access nodes using a 5×5 inner and 9×9 outer block, so "local" extends well beyond the immediate 3×3 ring.
- **Highway dimension** (Abraham et al. 2010) formalises why a few access points per area suffice for long trips, but a single centroid does not.
- **Customizable route planning / Multi-Level Dijkstra** (Delling et al. 2017; the MLD mode of OSRM). Each cell is replaced by shortcuts between its boundary vertices, giving a distance-preserving overlay: exact only if boundary nodes are kept.
- **PHAST** (Delling et al. 2013) computes one-to-all trees on contraction hierarchies fast enough to make all-pairs shortest paths on a continental road network a matter of days on a four-core machine.

## 2.3 Adaptive zoning

Hagen-Zanker & Jin (2012, 2015) let destination zones grow with distance from each origin. On the Chicago benchmark, at a computing time similar to halving the zone count, adaptive zoning reduced travel-time bias from 10% to 0.64% and link-volume RMSE from 221 to 33 vehicles. In their assignment application the gain is in computing time; in this project the routing cost is unchanged and the gain is in storage (section 4.5).

## 2.4 Accessibility and large-scale public transport

- **Accessibility measures.** Hansen (1959) defines accessibility as opportunities weighted by a decreasing function of travel cost. Geurs & van Wee (2004) review the families used in evaluation: cumulative opportunities within a threshold, gravity measures, nearest facility, utility-based measures; this project uses cumulative, radiative and nearest-facility measures. All except the utility-based ones are sums or minima over destinations, which a search can compute as it reaches them.
- **Ranked opportunities.** Intervening-opportunity models (Stouffer 1940) and the radiation model (Simini et al. 2012) use the number of opportunities closer than each destination, which is the cumulative opportunity curve of section 10.2. The radiation model has no parameter; its extended version adds one, to calibrate on observed flows (Yang et al. 2014).
- The European Commission computes road performance for all 2 million inhabited 1 km² cells in the EU and EFTA, counting population within a 120 km radius (Dijkstra et al. 2019), and the same grid for rail with near-complete timetables (Poelman et al. 2020).
- The Helsinki Region Travel Time Matrix covers 13,231 cells of 250 m for walk, bike, PT and car (Tenkanen & Toivonen 2020).
- Exact PT routing at continental scale still requires simplifications or heavy preprocessing (Bast et al. 2016). RAPTOR (Delling et al. 2015) needs no preprocessing, which matters for scenarios. ULTRA (Baum et al. 2023) adds a small set of transfer shortcuts that are provably sufficient for unrestricted walking.
- R5, through r5r (Pereira et al. 2021) or r5py in Python, computes travel-time matrices over departure windows; r5r reports a 1,227 × 1,227 matrix with a 120-minute window in under a minute on a laptop.
- **Departure-time sampling.** A 15-minute resolution balances precision and computing time (Stępniak et al. 2019). Regular-interval sampling can create spatially clustered errors that a constrained random-walk sampling avoids (Owen & Murphy 2019).
- PT times are heavily affected by spatial and temporal aggregation, much more than car times (Kuehnel & Ziemke).

## 2.5 Scenario design: edit the network or edit the outputs?

- **Fast network edits are established practice.** Conway, Byrd & van der Linden (2017) build transit modifications in a map interface and recompute accessibility quickly on commodity cloud infrastructure with R5, including variability over departure times. Scenario editing at network level and interactive recomputation are compatible.
- **Edits on a discretised graph.** Fajgelbaum & Schaal (2020) run their counterfactuals by changing infrastructure on the links of their cell graph, not on the raw road network. This is level 1 in this proposal.
- **A link's effect depends on the whole network.** Allen & Arkolakis (2022) derive analytical expressions linking link-level infrastructure to bilateral transport costs and link traffic, and find highly variable returns across links of the US highway and Seattle road networks. A direct edit of the O-D output cannot reproduce this propagation, and the effects of several projects do not add up.
- **Stylised cost shocks.** Quantitative spatial models often change bilateral costs directly (review in Redding & Rossi-Hansberg 2017). This is useful for sensitivity analysis but is not tied to a physical project.
- **Demand side: pivot-point.** Daly, Fox & Tuinenga (2005) recommend forecasting changes relative to observed base demand rather than absolute values. Applied here: scenario cost changes can be applied to observed flows (INSEE MOBPRO) rather than to modelled base flows.

## 2.6 Bodily energy of travel

Section 9 turns this literature into formulas; the main sources by theme:

- **Reference rates.** The Compendium of Physical Activities (Ainsworth et al. 2011; Herrmann et al. 2024) gives METs for walking, cycling, e-cycling, driving and riding. Kölbl & Helbing (2003) use ergonomic tables of oxygen consumption (Spitzer, Hettinger & Kaminsky 1982) that give energy above rest in kJ per minute for sitting, standing, walking, cycling and driving. Byrne et al. (2005) show that the conventional resting value behind the MET (3.5 mL O2/kg/min) overstates measured resting rates for many adults, which limits the precision of any MET-to-kJ conversion.
- **Walking.** Minetti et al. (2002) measure the net energy cost of walking from −45% to +45% gradient (minimum 1.64 J/kg/m at 1 m/s on level ground) and fit a fifth-order polynomial in the gradient. Pandolf, Givoni & Goldman (1977) predict metabolic rate from body mass, carried load, speed and grade. Ludlow & Weyand (2016) compare predictive equations for level walking; Weyand et al. (2010) show that the mass-specific cost of walking depends on stature. Tobler (1993) relates walking speed to slope.
- **Cycling.** Di Prampero et al. (1979) write the equation of motion of a cyclist; Martin et al. (1998) validate a power model combining rolling resistance, drag, gravity and kinetic energy, with mass explicit. Ettema & Lorås (2009) review cycling efficiency (gross efficiency around 20–25%). Wilson & Schmidt (2020) is the reference text on bicycle physics. Parkin & Rotheram (2010) measure commuter cyclists' speeds on gradients and their accelerations, the inputs for speed and stop costs.
- **E-bikes.** Gojanovic et al. (2011), Langford et al. (2017) and the review by Bourne et al. (2018) find that assisted cycling remains moderate-intensity activity, lower than conventional cycling at the same speed.
- **Travel time and energy budgets.** Zahavi & Talvitie (1980) and Marchetti (1994) propose a roughly constant daily travel time budget; Schafer & Victor (2000) use it to project world mobility. Mokhtarian & Chen (2004), Metz (2008) and Ahmed & Stopher (2014) review the evidence and find averages fairly stable but strong variation across individuals and contexts. Kölbl & Helbing (2003) find that mean daily travel time differs by mode, but that daily travel energy is roughly constant, about 615 kJ per person and day (UK National Travel Surveys 1972–1998).
- **Effort and comfort in choices.** Slopes reduce walking and cycling (Rodríguez & Joo 2004; Parkin, Wardman & Page 2008; review in Heinen, van Wee & Maat 2010). Cyclists' route choices value separated infrastructure and avoid climbs and signals (Menghini et al. 2010; Hood, Sall & Charlton 2011; Broach, Dill & Gliebe 2012).
- **Waiting, crowding and stress.** Mean waiting time grows with headway irregularity (random incidence: Larson & Odoni 1981; London measurements: Holroyd & Scraggs 1966). Crowding is valued as a strong penalty (Wardman & Whelan 2011; Li & Hensher 2011; Haywood, Koning & Monchambert 2017). Commuting stress rises with duration, unpredictability and congestion (Hennessy & Wiesenthal 1997; Evans & Wener 2006; Wener & Evans 2011; Legrain, Eluru & El-Geneidy 2015). Searching for parking adds time in dense areas (Shoup 2006).

## 2.7 Downscaling population and opportunities

- **Dasymetric mapping** redistributes counts from source zones to finer units using ancillary data while preserving zone totals (Eicher & Brewer 2001; Mennis 2003). Dwellings are the most direct ancillary data for population, premises for jobs.
- **Service thresholds.** Each type of service tends to appear above a minimum population in its catchment (Berry & Garrison 1958), which supports a presence model for projecting services.
- **POI-based job allocation.** The existing Monte Carlo study on Gironde compares allocation configurations against census jobs by sector at commune and EPCI level; it is the reference against which the Fichiers fonciers method is compared (section 7.2).

## 2.8 Take-aways for this project

- Grids are defensible where a traveller can enter anywhere; limited-access networks need explicit nodes.
- Exactness matters most for short trips; storage precision can fall with distance, but accessibility must be computed before any aggregation.
- Edit the network (at grid-edge or source level), not the outputs, for physical projects; validate changes, not only levels.
- Baseline and scenarios must share one engine.
- Energy must be built leg by leg along paths, because slopes and walking legs dominate its variation; a daily budget only holds if every leg of the day is counted.
- Origins and opportunities should preserve official totals and put local information in the allocation keys.
