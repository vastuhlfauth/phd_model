# 13. Validation plan

- **Origins:** INSEE 200 m product and Eurostat 1 km grid; regression weights against simple downscaling (section 6.3); temporal test of the 2023 model; errors by density class and size of natural-level cell; car ownership against commune totals.
- **Jobs:** EPCI totals exact by construction; allocation tested at commune level by sector with INSEE EMP; Fichiers fonciers method against the Overture method.
- **Services:** counts match BPE in each group, in both nomenclatures (section 7.3).
- **Radiative accessibility:** extended-radiation parameter estimated on MOBPRO flows (jobs) and on the travel surveys (social).
- **PT rebuilding (section 5.6):** the tram rule on the known cases (12 of 12 right, no false change among routes presumed unchanged); the openings list checked at every run, each row in exactly one category, residuals and known gaps listed; the PT back-test of 2021 to 2023 limited to openings and extensions.
- **Bike infrastructure:** OSM against the national cycle-infrastructure dataset (section 8.1).
- **Mode choice and flows:** MOBPRO 2021 and 2023, modes of commuting and commune-to-commune work flows.
- **Time budget:** constancy of daily travel time per population category across density classes and between ENTD 2008 and EMP 2019, per day with trips and per person, then within urban areas with the EMC² surveys (section 9.9).
- **Energy:** walking and cycling formulas against the reference rates of section 9.2; daily energy re-estimated in parallel on the same surveys, with declared walking and waiting times and after correction of implausible declared speeds (section 9.9); sensitivity of mode shares to the rate set and the cycling convention.
- **Google Maps:** the existing pipeline (sections 12 and 14.4) on stratified samples per mode, with its metrics: bias, MAE, RMSE, mean and median absolute percentage error, 90th percentile of absolute error, correlation, by mode, departure time and bins of duration and distance. Car times are compared without the terminal legs of the model (Google gives driving time only); free-flow times are compared with `staticDuration`, congested times with `duration`. PT is recomputed at the exact departure time of each Google request, as the current PT script does.
- **Routing:** the 8-, 16- and 24-neighbour grid graphs (section 8.3), with and without the through node, each with its runtime; test areas (a dense metropolitan area, a rural département, a mountain or coastal area with barriers, a border area); reference full-network OSRM (car, bike, foot) and OTP or full RAPTOR (PT); a few thousand origins stratified by density and distance band; metrics: bias, median absolute error, share of pairs within ±2 and ±5 min, relative error by band, distance errors, rank correlation of accessibility.
- **Products:** opportunity curves and nearest destinations against brute-force sums and minima on a sample of origins.
- **Engines:** numba RAPTOR against r5py; fast variant against per-origin range RAPTOR; the compiled Dijkstra against AequilibraE skimming on the pilot (runtime, agreement, whether cutoffs and the three products of section 10.2 can be obtained).
- **Congestion (later):** calibrated BPR functions against Google peak times by distance band and edge group; edge-level check from the route polylines; traffic counts where available.
- **Engine:** back-test 2021 to 2023 and the checks of section 11.8.
- **Acceptance thresholds** agreed before the runs; a starting proposal is a median absolute error of 2 min or 5% in the mid band and a bias within ±2%.
