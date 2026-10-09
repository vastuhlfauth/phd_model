# 13. Validation plan

- **Origins:** INSEE 200 m product and Eurostat 1 km grid; regression weights against simple downscaling (section 6.3); temporal test of the 2023 model; errors by density class and size of natural-level cell; car ownership against commune totals.
- **Jobs:** EPCI totals exact by construction; allocation tested at commune level by sector with INSEE EMP; Fichiers fonciers method against the Overture method.
- **Services:** counts match BPE in each group, in both nomenclatures (section 7.3).
- **Radiative accessibility:** extended-radiation parameter estimated on MOBPRO flows (jobs) and on the travel surveys (social).
- **PT rebuilding:** lines correctly kept, dropped or cut on the five test EPCIs and the metro cases (section 5.6).
- **Bike infrastructure:** OSM against the national cycle-infrastructure dataset (section 8.1).
- **Mode choice and flows:** MOBPRO 2021 and 2023, modes of commuting and commune-to-commune work flows.
- **Energy:** walking and cycling formulas against the reference rates of section 9.2; re-estimation of the daily budget on EMP 2019 and the EMC² surveys (section 9.9); sensitivity of mode shares to the rate set and the cycling convention.
- **Google Maps:** the existing pipeline (sections 12 and 14.4) on stratified samples per mode, with its metrics: bias, MAE, RMSE, mean and median absolute percentage error, 90th percentile of absolute error, correlation, by mode, departure time and bins of duration and distance. Car times are compared without the terminal legs of the model (Google gives driving time only); free-flow times are compared with `staticDuration`, congested times with `duration`. PT is recomputed at the exact departure time of each Google request, as the current PT script does.
- **Routing:** test areas (a dense metropolitan area, a rural département, a mountain or coastal area with barriers, a border area); reference full-network OSRM (car, bike, foot) and OTP or full RAPTOR (PT); a few thousand origins stratified by density and distance band; metrics: bias, median absolute error, share of pairs within ±2 and ±5 min, relative error by band, distance errors, rank correlation of accessibility.
- **Products:** opportunity curves and nearest destinations against brute-force sums and minima on a sample of origins.
- **PT engines:** numba RAPTOR against r5py; fast variant against per-origin range RAPTOR.
- **Engine:** back-test 2021 to 2023 and the checks of section 11.8.
- **Acceptance thresholds** agreed before the runs; a starting proposal is a median absolute error of 2 min or 5% in the mid band and a bias within ±2%.
