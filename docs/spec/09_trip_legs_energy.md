# 9. Trip legs: time and bodily energy

## 9.1 Unit and conventions

- **Energy above rest,** in kJ for a reference adult of mass m, the mean body mass of adults in France: about 74 kg (men about 81 kg, women about 67 kg in the Esteban study 2014–2016 of Santé publique France, weighted by the adult sex ratio). Energy is also reported in net MET-minutes: one net MET-minute is 0.0175 kcal/kg × 4.184 kJ/kcal × m = 0.0732 × m kJ, i.e. 5.42 kJ at 74 kg and 5.13 kJ at 70 kg. The numerical examples of this section use 70 kg, the convention of the literature.
- **Two sets of rates, chosen in configuration:** **KH**, the ergonomic values used by Kölbl & Helbing (2003), from Spitzer, Hettinger & Kaminsky (1982), in kJ per minute above rest; and **Compendium** (Ainsworth et al. 2011; Herrmann et al. 2024), in METs. Daily energy in section 9.9 is computed with both sets.
- **Body mass is explicit.** Walking costs are proportional to m; cycling separates mass-proportional work from drag; sedentary rates are per kilogram in the Compendium and for a reference adult in KH.
- **Physical quantities only.** Outputs are time and energy. Perceived penalties (for transfers, crowding, discomfort) belong to the mode-choice model; where crowding or congestion changes the body's energy use, the rates below change.

## 9.2 A trip is a chain of legs

Every trip is built from legs (Figure 4). Its time and energy are sums over legs: T = Σ t, E = Σ e. Sedentary and standing legs have e = r × t with a rate r; walking and cycling legs use physical models along the path. The same formulas serve the O-D computation, the scenario engine and the re-estimation of the daily budget on EMP 2019 (section 9.9). Modes are compared at equal distance and at equal door-to-door time: for a given time, the distance reached (faster modes contract space) and the energy spent, which crowding and congestion raise per minute.

![Figure 4. Trips as chains of legs, with the time and energy model of each leg; red dots mark the legs where congestion or crowding act (section 9.8).](figures/fig4_trip_legs.png)

_Figure 4. Trips as chains of legs, with the time and energy model of each leg; red dots mark the legs where congestion or crowding act (section 9.8)._

The legs use these reference rates, in kJ per minute above rest for 70 kg; Compendium values are given with their 2024 code:

| Activity | KH (Spitzer et al. 1982) | Compendium 2024: code, MET → kJ/min | Used for |
|---|---|---|---|
| Sitting in a vehicle | 1.5 | 16016 riding in a bus or train, 1.3 → 1.5 (16015 car, same) | Seated PT ride, car passenger |
| Standing, relaxed | 2.6 | 07041 standing, fidgeting, 1.5 → 2.6 (07040 quietly, 1.3) | Waits; standing ride without crowding |
| Standing, restless | 6.7 | — | Crowded standing ride (upper bound) |
| Car driving, clear roads | 4.2 | 16010 driving, 2.0 → 5.1 | Driving, free flow |
| Car driving, test drive | 8.0 (5.9–12.6) | — | Cap of the congestion penalty |
| Car driving, city rush hour | 13.4 | — | Upper bound only |
| Walking to or from a car or bus | — | 17161, 2.5 (estimated) → 7.7 | Check of short terminal walks |
| Walking, flat, 4 km/h | 14.1 | 17170 (2.5 mph), 3.0 → 10.3 | Walking formula, KH or Compendium level |
| Walking, flat, 5 km/h | 18.0 | 16060 walking for transportation (2.8–3.2 mph), 3.5 → 12.8 | Same |
| Climbing stairs | — | 17131 general, 6.8 → 29.7; 17133 slow, 4.5 → 17.9 | Check of the stairs formula |
| Descending stairs | — | 17070, 3.5 → 12.8 | Same |
| Cycling, flat, 12 km/h | 14.7 | 01010 under 10 mph, 4.0 → 15.4 | Check of the cycling physics |

## 9.3 Walking legs

Access and egress to stops, transfers, walking trips, and walks to and from cars and bikes all use the same formulas, applied segment by segment along the path (gradient i, length L):

```text
v(i)  = v0 · exp(−3.5·|i + 0.05|) / exp(−0.175)
t     = Σ L / v(i)
e     = m · c0 · Σ L · g(i)
g(i)  = Cw(i) / Cw(0)
Cw(i) = 280.5 i^5 − 58.7 i^4 − 76.8 i^3 + 51.9 i^2 + 19.6 i + 2.5    (J/kg/m)
```

The speed is Tobler's (1993) hiking function rescaled so that v(0) = v0; Cw is the net cost of walking measured by Minetti et al. (2002).

- **Parameters:** v0 = 4.8 km/h. The walking trips of the surveys give much lower speeds, declared distance over declared duration: 3.38 km/h in EMP 2019 (7,707 trips) and 3.63 km/h in ENTD 2008 (20,348 trips). These are door-to-door speeds, with crossings and stops on the way, and short durations are declared rounded to 5 or 10 min, so they are reported and not adopted [TO CONFIRM: keep 4.8 km/h for the walking legs of the O-D computation, or adopt a door-to-door value; v0 sets walking times only, since walking energy is counted per metre]. c0 is the net cost per kilogram and metre on the flat: 2.29 J/kg/m with the Compendium (3.5 MET at 4.8 km/h) or 3.0 J/kg/m with KH (14.1 kJ/min at 4 km/h for 70 kg). Minetti et al. measured a minimum of 1.64 J/kg/m at 1 m/s on a treadmill. For 70 kg and 1 km on the flat: 160 kJ (Compendium) or 211 kJ (KH).
- **Gradient factor:** g = 1.44 at +5%, 1.96 at +10%, 0.45 at −10%; the polynomial is valid from −45% to +45%.
- **The m·g·h term is already inside.** The extra cost of climbing, Cw(i) − Cw(0), equals the vertical work g·i divided by an apparent efficiency of about 0.45 at +5% and 0.34 at +30%. Since e is multiplied by m, climbing energy is proportional to body mass, as m·g·Δh is; adding m·g·Δh separately would count it twice.
- **Stairs and level changes** (stations, footbridges, underpasses). Proposed values, consistent with the Compendium:

```text
t_up   = Δh / 0.20 m/s      e_up   = m·g·Δh / 0.30
t_down = Δh / 0.30 m/s      e_down ≈ e_up / 3
```

Climbing at 0.20 m/s with an efficiency of 0.30 is about 6.4 MET, close to the Compendium's general stair climbing (17131, 6.8 MET); descending at 0.30 m/s at the Compendium's 3.5 MET (17070) costs about a third of climbing. Climbing 10 m costs about 23 kJ for 70 kg, as much as 140 m of flat walking. Escalators and lifts are taken at the standing rate; escalators are assumed in stations deeper than 10 m. OSM levels are rarely complete, so height differences come from the type of station:

| Place | Height difference | Note |
|---|---|---|
| Bus stop; tram or metro stop at street level | 0 |  |
| Rail platform change by underpass | 4 m down, then 4 m up |  |
| Rail platform change by footbridge | 7 m up, then 7 m down | Clearance above electrified tracks |
| Shallow underground station (older metro lines) | 6 m |  |
| Deep underground station (RER, newer metro lines) | 15 m | Escalators |
| Very deep station (e.g. Grand Paris Express) | 25 m | Escalators and lifts |

The heights are checked on a sample of stations.

- **Later:** carried loads for shopping trips (Pandolf, Givoni & Goldman 1977); walking speed in crowded stations (Fruin 1971).

## 9.4 Waiting and transfers

- **Time from timetables.** Range RAPTOR includes the initial wait in the median over the departure window, and transfer waits in each journey. A minimum transfer time applies: 2 min within a stop area, 3–5 min for rail.
- **Frequency-based approximation,** used when a scenario changes headways before timetables are regenerated:

```text
w = (h / 2) · (1 + CV²)      headways up to about 10–12 min: random arrivals
w = w_planned                longer headways: passengers time their arrival
```

h is the mean headway and CV the coefficient of variation of headways (Larson & Odoni 1981; Holroyd & Scraggs 1966). CV is zero in a timetable and positive when service is irregular: this is the reliability penalty. The limit between the two regimes is 10–12 min and w_planned = 4 min.

- **Without real-time data,** CV takes default values by mode and right of way, read from the headway-adherence levels of service of the TCQSM (Kittelson & Associates et al. 2003): A up to 0.21, B 0.22–0.30, C 0.31–0.39, D 0.40–0.52, E 0.53–0.74. Proposed: metro and rail 0.15 (A), tram on reserved track 0.25 (B), bus on bus lanes 0.35 (C), bus in mixed traffic 0.45 (D), bus in congested centres 0.60 (E). With the congestion module, the CV of buses in mixed traffic rises with the congestion index of their route.
- **Checks on EMP 2019.** EMP records door-to-door trip durations but not waits or headways, so it cannot test the CV values directly. It can test them together: modelled PT door-to-door times, which include the waits, are compared with declared PT trip durations by mode and density class; a systematic gap points to the waits, w_planned or the CV defaults.
- **Energy:** e = r_wait × w, with r_wait at the standing-relaxed rate (KH 2.6 kJ/min; Compendium 07041).
- **Transfer legs** combine a walking leg on the foot network, the level change between platforms, and the wait for the next departure.

## 9.5 Riding public transport

- **Time:** from the timetable; scenario edits change it. Later: dwell times grow with boardings and alightings (TCQSM 2013), and buses in mixed traffic follow car congestion except on bus lanes.
- **Energy:** a mix of sitting and standing that depends on the load factor LF (passengers per seat):

```text
r_ride  = (1 − p_s) · r_sit + p_s · r_stand(LF)
p_s     = max(0, 1 − 1/LF)                 share of riders standing
r_stand = r_relaxed + (r_restless − r_relaxed) · clamp((LF − 1)/(LF_max − 1), 0, 1)
```

with r_sit = 1.5, r_relaxed = 2.6 and r_restless = 6.7 kJ/min (KH), and LF_max the crush load per seat, by vehicle type (below). Kölbl & Helbing note that sitting and standing in a moving vehicle cost more than at rest because of balancing. No separate vehicle factor is needed: the Compendium already rates riding a bus or train (16016) at 1.3 MET against 1.0 for sitting quietly (07021), and the dynamic part, crowding, comes from the load factor, which follows the flows of the model.

Proposed crush loads per seat (seats plus standing room at about 4 passengers per m², divided by seats) [TO CONFIRM: against operators' vehicle data]:

| Vehicle | LF_max |
|---|---|
| Metro | 4.0 |
| Tram | 4.0 |
| Urban bus (standard or articulated) | 3.0 |
| RER and suburban trains (Transilien) | 2.5 |
| TER | 1.8 |
| Intercités | 1.3 |
| Interurban coach | 1.2 |
| TGV, long-distance coach | 1.1 |

- **First phase, without load data:** standing shares for 08:00–09:00: metro 0.5, tram 0.4, urban bus 0.3, TER 0.15, TGV 0. **Later:** LF from PT flows assigned with the stored route groups, so crowding raises energy (restless standing) and, at crush load, waiting (denied boarding).
- **Service quality in scenarios:** better frequency reduces waits; more capacity or seats lowers the standing share and its rate; closer stops shorten egress. All three change time and energy through these formulas.

## 9.6 Car legs

- **Walk to and from the car:** t_w minutes per car trip in total, split equally between the two ends, calibrated on the walking time declared for car trips in EMP 2019 (`MTEMPSMAP`), by density class and by parking type at the destination (`MSTATION`) (decision of 27 October 2026). Drivers declare 1.0 to 1.7 min per trip in total, and most declare none (58% to 75% of trips): about 1 min after parking at a private space, 1 to 2 min in the street and about 3 min in a paid car park, private spaces being 57% to 66% of destinations in sparse areas against 39% in dense areas. The former defaults, 0.5 to 4 min to the car (t_house, and t_apt by density with the share of houses s_house) and 0.5 to 5 min from it, gave 1.5 to 9 min per trip: about four times the declared values, and graded by assumption. Proposed per trip: dense 1.7, intermediate 1.1, sparse 1.2 and very sparse 1.2 min, with 1 min more as a sensitivity for unreported short walks [TO CONFIRM: final values from the calibration table of section 9.9]. Kölbl & Helbing explain the daily energy of car passengers by such walks; French respondents declare little of them. Energy from the walking formula.
- **Drive:** time from the car graph (free flow now, congested later). Energy at the driving rate, which rises with congestion:

```text
r_drive = r_free + (r_cong − r_free) · clamp((ρ − 1)/(ρ_max − 1), 0, 1)
ρ       = congested time / free-flow time on the path
```

with r_free = 4.2 (KH) or 5.1 kJ/min (Compendium), r_cong = 8.0 kJ/min (the test-drive value of KH; the rush-hour value of 13.4 is only an upper bound) and ρ_max = 2. Passengers sit (1.5 kJ/min).

- **Parking search** at the destination: t_ps by density class of the destination cell: about 0 in rural areas, 0.5 min suburban, 2 min urban, 5 min in dense centres (Shoup 2006), later a function of parking supply and occupancy; energy at the driving rate for the driver and at the sitting rate for passengers.
- **Passengers,** two cases. A household passenger has the driver's walks and sits during the parking search. A carpool passenger, travelling with a driver from another household, also walks to a meeting point and waits there standing [TO CONFIRM: about 5 min walking and 3 min waiting per trip; carpool passengers declare 1 to 2 min of walking per trip in EMP 2019 and ENTD 2008, and waiting is not asked for car trips; the two cases are separated by the trip's companions, `MACCOMPM` and `MACCOMPHM`].

## 9.7 Bike legs

- **Get the bike and park it:** fixed times, about 1 min each, more for apartment buildings, at the standing or walking rate. Shared bikes later (walk to and from the dock).
- **Ride:** on each edge of slope i = tan θ, the speed v solves the force balance (di Prampero et al. 1979; Martin et al. 1998):

```text
P_r · η_d = v · [ M·g·(C_rr·cos θ + sin θ) + ½·ρ_air·C_dA·(v + v_w)² ]
M = m + m_bike,   η_d ≈ 0.976 (drivetrain)
P_r = clamp( P_0·(1 + k·i), 0, P_max )     on every grade
v  ≤ v_max,desc on descents and ≤ the cap of the infrastructure class;
     at a cap, P_r is the power that holds it
```

The rider pushes harder on climbs, eases off on descents and freewheels below i = −1/k. A rule of no pedalling on every descent would stop riders on gentle slopes, where gravity does not overcome rolling resistance (below about 0.6% with C_rr = 0.006); the checks of step 7 showed it. P_0, k and P_max are calibrated on observed speeds. P_0 is the power that holds, on the flat, the mean ride speed of the bike trips of a survey: the weighted sum of declared distances divided by the weighted sum of ride times, a ride time being the declared duration minus the times to get and park the bike (2 × 1 min) and the expected stop delays. When so little time remains that the ride would exceed 45 km/h, the whole declared duration is taken as ride time instead; the trip stays in the calibration, and its energy uses the same ride time. EMP 2019 gives 13.55 km/h and P_0 = 34.8 W (727 of its 1,023 bike trips, the others being out of the scope of section 9.9). EMP 2019 does not separate e-bikes from bicycles (its bicycle code includes electric assistance), so they cannot be set apart; ENTD 2008, when e-bikes were still rare, gives a close value, 34.0 W at 13.39 km/h (2,146 trips), which suggests that they move the 2019 value little. Provisional values for the other parameters: k = 37, P_max = 200 W, v_max,desc = 30 km/h; the checks of step 7 used P_0 = 52.5 W (16 km/h) [TO CONFIRM: k and P_max; Parkin & Rotheram (2010) measured about 150 W on the flat and 250 W on climbs for UK commuters with an 85th-percentile speed of 22 km/h, a fitter population than the KH and Compendium references, so their ratio of climbing to flat power is the more transferable result].

- **Stops** at signals and junctions, with a probability by infrastructure class: time = deceleration + expected wait + acceleration (for a random arrival at a signal of cycle C and red time R, the expected wait is R²/(2C); Webster 1958); energy ½·M·v²/ε to regain speed, about 3.5 kJ at 16 km/h for M = 85 kg.
- **Energy:**

```text
e = m · u_ped · t_ped + [ M · (W_roll + W_climb + W_stops) + W_drag ] / ε
u_ped   = 1 net MET = 0.0732 kJ/kg/min    unloaded pedalling, per pedalled minute (P_r > 0)
W_roll  = Σ s_r·g·C_rr·cos θ·L        (per kg, pedalled edges: P_r > 0)
W_climb = Σ s_r·g·Δh                  (per kg, pedalled edges, signed: the m·g·h term)
W_stops = Σ s_r·½·v²                  (per kg, per stop)
W_drag  = Σ s_r·½·ρ_air·C_dA·v²·L     (pedalled edges)
s_r     = P_r / (P_r + P_m)           rider's share of the work; 1 without assistance
```

with ε ≈ 0.24, the gross muscular efficiency (Ettema & Lorås 2009). The first term is the cost of moving the legs without load: about 1 MET above rest in the leg-cycling equation of the American College of Sports Medicine (3.5 mL O₂ per kg and minute; Swain 2000). Without it, the work term alone underestimates slow riding, where the external power is small: at the EMP 2019 calibration (about 35 W, 13.5 km/h) it gives about 9 kJ/min, against 14.7 kJ/min measured at 12 km/h (KH) and 15.4 for the Compendium's slowest cycling; with the unloaded term, about 14 kJ/min at 74 kg. Δh is signed on pedalled edges, so on a gentle descent where the rider still pedals, gravity reduces the rider's work; freewheeling edges cost nothing. Storing the per-kilogram part and the drag part separately lets energy be recomputed for any body or bike mass without new searches; speeds are computed at the reference mass.

- **Calmer riding on separated infrastructure.** On separated tracks and paths the riding energy is multiplied by φ_sep = 0.97, with 0.90–1.00 as the sensitivity range. The evidence points to a small effect: Fitch, Sharpnack & Handy (2020) measure heart-rate variability of cyclists on five urban roads and find clear differences for only one of them; in a cycling simulator, Guo et al. (2022) find no difference in mean heart rate between mixed traffic, a bike lane and a protected lane, but about half as many abrupt heart-rate increases on the two lanes. The main physical gain of separated infrastructure, fewer stops, is modelled directly.
- **Defaults:** C_rr by surface (table below); C_dA = 0.55 m² (upright position); ρ_air = 1.2 kg/m³; no wind; m = reference mass, m_bike = 15 kg.

Rolling resistance for city-bike tyres, by OSM `surface`:

| OSM surface | C_rr |
|---|---|
| asphalt, concrete, paved; missing tag on paved roads (default) | 0.006 |
| concrete:plates, concrete:lanes | 0.007 |
| paving_stones | 0.008 |
| compacted | 0.010 |
| fine_gravel | 0.012 |
| sett, cobblestone, unhewn_cobblestone | 0.015 |
| gravel, pebblestone, unpaved, ground, dirt, earth | 0.020 |
| grass, sand | 0.030, or not routable |

- **Effect of mass on speed.** On the flat, mass only enters rolling resistance: 10 kg more slows a rider by about 2% at 16 km/h. On a 5% climb it slows them by about 10%.
- **Consistency.** With these defaults, riding at 15–16 km/h on the flat needs about 50 W of mechanical power: about 13 kJ/min of work at 24% efficiency plus 5 kJ/min of unloaded pedalling, about 18 kJ/min above rest at 70 kg. At 12 km/h (about 30 W) the rate is about 12 kJ/min, close to KH (14.7 kJ/min) and to the Compendium leisure value (4.0 MET, 15.4 kJ/min). The Compendium commuting value (6.8 MET, about 30 kJ/min) is kept only as an upper bound for sensitivity tests.
- **E-bike:** the motor adds P_m = min(250 W, a·P_r) below 25 km/h and nothing above (EU pedelec rules); m_bike about 23 kg; rider energy from P_r only, through s_r on every edge and stop, plus the unloaded pedalling cost. The rider keeps the power function of a non-assisted cyclist, so assistance turns into speed: on the flat the rider's rate per minute equals the cyclist's (a ratio of 1.0 in the checks of step 7), whereas the Compendium gives net ratios of about 0.86 with light and 0.52 with high support [TO CONFIRM: an effort factor f_e per support level multiplying P_r, 1.0 by default, tested at the Compendium ratios]. The assistance factor a follows manufacturers' support levels, for example Bosch Performance Line (model year 2021): eco 0.55, tour 1.2, sport 2.0, turbo 3.0, with tour as default. The Compendium's light support (6.0 MET) corresponds to eco or tour, its high support (4.0 MET) to sport or turbo. Results are checked against the Compendium (6.8, 6.0 and 4.0 MET without, with light and with high support) and Gojanovic et al. (2011), Langford et al. (2017).

## 9.8 Where congestion and crowding act

| Penalty | Legs | Effect on time | Effect on energy | Data | Phase |
|---|---|---|---|---|---|
| Road congestion | Drive | Congested link speeds | Driving rate rises with ρ | Google Maps; traffic counts | Congestion (section 12) |
| Parking pressure | Parking search; walk from car | Search and walking times | Driving and walking rates | Density now; parking supply later | Defaults now |
| Buses in traffic | PT ride | Follow car speeds, except on bus lanes | — | OSM bus lanes; congested speeds | Congestion |
| Irregular headways | Wait | Factor (1 + CV²) | Standing rate | Default CV by mode and right of way (TCQSM bands); later linked to congestion | Defaults now |
| Vehicle crowding | PT ride; wait | Dwell times; denied boarding | Standing share; restless standing | PT loads from the flow model | Defaults now |
| Station crowding | Transfers | Walking speed (Fruin 1971) | Walking | Station loads from the PT assignment of the model | Later |
| Bike traffic and signals | Bike ride; stops | Stops; speed caps on busy tracks | Stop energy | — | Later |

Congestion comes from BPR functions on the reduced car network (section 12); crowding is a loop in which loads at period t set penalties at period t+1.

## 9.9 Daily travel time budget per cell

**The constant.** The model's reference constant is the daily travel time budget: the time a person spends travelling in a day. A long literature finds it roughly stable across places and periods while speeds, distances and modes change (Zahavi & Talvitie 1980; Marchetti 1994; Schafer & Victor 2000); reviews find the averages fairly stable but individuals and contexts varying widely (Mokhtarian & Chen 2004; Metz 2008; Ahmed & Stopher 2014) [TO CONFIRM: literature to extend, in geography and anthropology]. The budget is a property of persons, not of modes: the mode used on a day is itself chosen within the budget, so days using different modes are expected to differ in time. One budget b_k is defined for each population category k of section 6.1, since the categories travel for different lengths of time (in EMP 2019, on days with trips: employed persons 84 min, retired persons 60 min, children 54 min); the budget of a cell is the population-weighted sum (decision of 27 October 2026).

**Why time and not energy.** Until 27 October 2026 the reference was the daily energy budget of Kölbl & Helbing (2003). Re-estimated with each trip's declared walking and waiting times (below), energy is no more stable than time:

| Ratio between extremes | Daily time | Energy, former default walks | Energy, declared walks |
|---|---|---|---|
| Density classes, dense ÷ very sparse (2019 / 2008) | 1.08 / 1.08 | 1.31 / 1.43 (Compendium) | 1.27 / 1.35 (Compendium) |
| Main-mode groups, highest ÷ lowest | 4.2 / 4.3 | 1.6 to 2.2 | 4.0 to 4.3 |
| 2019 ÷ 2008 (density proxy) | 1.08 | 1.02 | 1.09 to 1.10 |

The near-equality of energy across modes, and its stability between 2008 and 2019, came from the default walks to and from the car: about four times longer than declared, and graded by density class (section 9.6). With declared walks, energy follows time at each mode's intensity per minute. Trips per day on days with trips are also flat across density classes (3.3 in EMP 2019, 3.5 in ENTD 2008). Energy is still computed, in parallel (below).

**Use in the model.**

```text
B(c) = Σ_k p_k(c) · b_k
T(c) = Σ_p n_p(c) · Σ_mode s_p,mode(c) · 2 · t̄_p,mode(c)        T(c) = B(c)
```

where p_k(c) is the share of the cell's residents in category k (section 6.1) and b_k the budget of category k, in minutes per person and day, days without trips included (if daily time also differs by income within categories, b_k,q by income quintile q, with p_k,q(c) from the household incomes of section 6); n_p is the number of trips per person and day for purpose p (work, education, shopping and services, nature, social, other; rates from EMP 2019 and the EMC² surveys), s the mode shares and t̄ the expected one-way door-to-door time for that purpose from the O-D products (work: flow-weighted over job destinations; services and nature: nearest of each type; social: population-weighted); 2 counts the return, and a tour with several stops is counted once, under its main purpose. The budget constrains mode choice and the reach of destinations: faster modes and closer opportunities let the same time cover more activities or longer distances. The cell's daily energy E(c) is assembled in the same way from the one-way energies ē; it is an output, not a constraint.

**What is tested.** For each population category: is mean daily travel time the same across density classes of residence, across household income classes, and in 2008 and 2019, while modes, distances and speeds differ? Income is treated as density is: as a dimension along which the budget of a category should not change. The test compares means and distributions of daily time across density classes, income classes and years within each category, not the spread between individuals, which is wide. It is run per day with trips (the reference, comparable in both surveys) and per person, days without trips included (the unit of b_k), for travel for needs (the reference scope) and for all trips (a variant). Trips per day are tested in the same way, and daily time is split into trips per day × minutes per trip, to see whether a constant time comes from constant trips or from trips that compensate each other.

**Scope: travel for needs (reference) and all trips (variant).** The reference budget concerns travel to fulfil needs (work, study, shopping, services, visits, accompanying someone, leisure at a destination), not movement for its own sake. Trips whose purpose is sport, a stroll without destination, going to a place to walk or ride, holidays, a second or occasional residence or other private reasons are left out of the day's time and energy (decision of 20 October 2026). For return trips the purpose is that of the outward trip they close. In EMP 2019 these trips are a quarter of the trips of walking days and 30% of those of cycling days, and carry half of the energy of cycling days; in ENTD 2008, 19% and 25% of the trips, and 43% of the energy of cycling days. The variant keeps all trips, as most of the time-budget literature does.

**Re-estimation on EMP 2019 and the EMC² surveys:**

1. Rebuild each respondent's survey day as legs. `K_DEPLOC` gives, for each trip, the main mode, the declared duration (`DUREE`), the distance (`MDISTTOT_fin`), the purpose and the companions, with the weight `POND_jour`. Time comes from the declared durations and needs no model. For energy, the terminal legs take the trip's own declared walking and waiting minutes (decision of 27 October 2026): `MTEMPSMAP` ("Au cours de ce déplacement, combien de temps en tout avez-vous marché ?", asked for every trip not made entirely on foot, walking in car parks included) replaces the walks to and from the car, the carpool walk to the meeting point, the PT access walks and the bike get/park time; `MTPSATTENT` (total waiting time, asked for public transport, taxi and train trips) replaces the PT and train waits. The vehicle leg takes the rest of the declared duration. Where a declared value is missing (0.3% to 3% of trips, by mode), the defaults of sections 9.4 to 9.7 apply. Variants: declared walking plus 1 min per car, bike and urban PT trip, for unreported short walks (58% to 75% of car trips declare none); and the former defaults (×0.5, ×1, ×1.5). Walking and cycling trips calibrate v0 and P_0 (declared distance over duration, by age band; sections 9.3 and 9.7).
   - **Legs without paths.** Survey trips have no path, so every leg is on the flat. Walking energy follows the distance (section 9.3), declared walking minutes being converted to metres at v0; waiting, riding and driving energy follow time, at their rates. A bike trip is ridden at P_0 for its ride time, at P_0/ε + m·u_ped per unit of time, plus 2 stops per km. Each stop costs ½·M·v²/ε at the flat speed the rider holds at P_0 (13.55 km/h), not at the trip's own speed (decision of 22 October 2026): declared distances and durations make the trip's speed noisy, and the stop energy grows with its square. With each trip's own speed, the 6% of EMP 2019 bike trips faster than 25 km/h gave 37% of the stop energy, and the stop term carried 11.5% of the energy of cycling days (10.2% in ENTD 2008); at the P_0 speed it carries 6.3% (6.4%). The infrastructure is unknown, so φ_sep is not applied. Other modes (powered two-wheelers, taxi, plane, boat, unspecified) are too diverse for one rate and carry about 2% of trips in both surveys, so they are given no energy; their time counts in the budget. Days with only such trips (234 in EMP 2019, 221 within the scope) are left out of the energy statistics only.
   - **Implausible speeds.** A trip whose declared speed, distance over duration, exceeds 7 km/h on foot, 35 km/h by bike or 130 km/h by car (driver or passenger) has a wrong distance or duration. It stays in the sample: its duration is kept and its distance is replaced by the duration times the median speed of the same mode's trips that are not flagged. Bike trips are corrected like walking and car trips (decision of 20 October 2026): the number of stops follows the distance. Left uncorrected, three ENTD 2008 bike trips declared at about 360 km in 65 to 90 min raised the 2008 mean energy over all days from 533 to 625 kJ (KH). Corrected trips: walking 1,569 of 10,180 in EMP 2019 and 467 of 27,429 in ENTD 2008, a share nine times higher in 2019 [TO CONFIRM: how `MDISTTOT_fin` is computed for short walks]; car 0 of 29,990 and 413 of 85,302; bike 0 of 1,023 and 25 of 3,266. Durations are not checked for any mode [TO CONFIRM: a duration check for every mode, which matters more now that time is the reference].
2. Sum the day's travel time, trips and energy (both rate sets) over all trips of the described day, and compute them per day with trips and per person. The two surveys choose the described day differently:
   - **EMP 2019** draws the described day among the days of the previous week on which the respondent went out: the last weekday out, and Saturday or Sunday if they went out on it. Every described day therefore has trips. Respondents who stayed home all week (`MIMMOSEM` = 1) describe no day and have no date; they are 455 of 13,825 respondents, 2.6% by individual weight. Days without going out are those ticked in `IMMODEP`, one flag per day from J−1 to J−7 (`IMMODEP_A` to `IMMODEP_G` in `K_INDIVIDU`, with a summary flag `IMMODEP_FLAG`). The budget per person is Σ_d w_d · P(out on day type d) · T(d | out), over weekdays, Saturdays and Sundays (w_d = 5/7, 1/7, 1/7), P from `IMMODEP` with individual weights and T from the described days of that type with day weights; respondents who stayed home all week count zero.
   - **ENTD 2008** describes, for one selected person per household (18,632 respondents, `K_INDIVIDU`), the weekday before the visit whatever happened on it, and one or both weekend days. A weekday without trips counts zero: 2,945 of the 18,632 weekdays (15.8% unweighted; `V2_MOBILREF` = 0). The household members file (`Q_TCM_INDIVIDU`, 49,283 persons) is used for ages and occupations only, never as a count of respondents. Weekend days without trips are flagged (`V2_MIMMOSAM`, `V2_MIMMODIM`) [TO CONFIRM: which respondents were asked about each weekend day]. For comparison, local household surveys of 2009–2017 give 12.6% of persons without trips on a weekday, outside Île-de-France (Cerema's unified base; Observatoire des territoires 2023).

   The shares of persons without trips in the two surveys measure different things and are not compared; budgets per person are compared, since each survey's rule gives a per-person figure.
3. Test the hypothesis: daily travel time and trips per day by population category (section 6.1: children 6–17, employed, unemployed, retired, other inactive) × density class of the commune of residence (the four levels of the INSEE density grid, in the public tables), and population category × income quintile of the household, per day with trips and per person. Income is the household's income per consumption unit (modified OECD scale: 1 for the first adult, 0.5 for each other person aged 14 or more, 0.3 for each child under 14), in quintiles computed within each survey, so that 2008 and 2019 compare positions in the distribution, not euros [TO CONFIRM: income variables of EMP 2019 and ENTD 2008, and whether they are brackets; a bracket is taken at its midpoint, the open top bracket at 1.5 times its lower bound]. Then, to describe how the budget is spent, time and energy by main-mode group of the day, grouped as in Kölbl & Helbing by the one mode used besides walking: walking only, bike, car driver, car passenger with a household driver, car passenger with a driver from another household (carpool, formal or informal), urban PT and train (short and long train days merged, long-train days being too few); multimodal days (two or more modes besides walking, driving and riding as a passenger counting as two) and days with other modes form two more groups. Comparisons of energy across ages use net MET-minutes, so that body mass does not drive them [TO CONFIRM: Youth Compendium (Butte et al. 2018) for children].
4. Use the EMC² surveys of 14 EPCIs, which locate residents at a finer zoning, to test the variation of the budget within urban areas (centre, suburbs, periphery).
5. Fit the distribution of daily travel time for each category (and of daily energy), and compare the levels with the literature's values.
6. Define b_k for each population category from the estimates, and test whether age structure, household size, income or density class still matter within categories; density enters only if it remains significant [decision after estimation].

**Energy, in parallel.** Daily energy is computed for every day with both rate sets, from the same legs. It serves to explain the differences in time between modes: a mode with a higher energy per minute may be used for less time. Kölbl & Helbing's hypothesis, that daily energy is the same for every main-mode group, is tested and reported as a secondary result. Their figures and this project's model compare as follows:

| Point | Kölbl & Helbing | This project | Consequence |
|---|---|---|---|
| Units | kJ/min above rest; sitting 1.5 equals 0.3 MET above rest at 70 kg | kJ above rest; net MET-minutes | Compatible: sitting matches the Compendium's 1.3 MET; 615 kJ ≈ 120 net MET-min |
| Reading of their table 1 | Walking 14.1 (4 km/h) and 18.0 (5 km/h); cycling 14.7 (12 km/h) | — | 18.0 is walking at 5 km/h, not cycling (the table loses its alignment when copied) |
| Walking rate | 14.1–18.0 kJ/min | Compendium 10–13 kJ/min | KH about a third higher; rate set chosen in section 9.1 |
| Cycling rate | 14.7 kJ/min at 12 km/h | Physics with unloaded pedalling about 14 kJ/min at 13.5 km/h (EMP 2019 calibration, 74 kg); Compendium commuting about 30 | Physics consistent; the Compendium commuting value is only an upper bound |
| Rates per mode | Ē divided by mean daily time: walk 15.4, cycle 14.6, bus 9.2, driver 8.2, passenger 10.4, train 4.0 kJ/min | Declared walks, Compendium, EMP 2019: walking only 9.4, bike 12.3, urban PT 5.6, car driver 6.1, household passenger 2.9, train 4.7 kJ/min | Their passenger and driver rates require long walks around car trips, which French respondents do not declare |
| Precision | — | MET-to-kJ conversion about ±20% (Byrne et al. 2005) | Levels are compared with care; patterns across groups and years matter more |

**Change between 2008 and 2019 (ENTD 2008).** The same reconstruction is run on ENTD 2008, its codes mapped to those of EMP 2019 (`docs/data/entd2008.md`): `V2_MTEMPSMAP`, `V2_MTPSATTENT` and `V2_MSTATION` for the declared walking, waiting and parking. Days are counted per described day with their own weights (weekday, Saturday, Sunday): up to three days per person, against one in EMP 2019, so counts of days and of persons are kept apart. Sample flow: 18,632 respondents; 36,927 described days with trips (15,687 weekdays, 11,670 Saturdays, 9,570 Sundays); 36,253 with energy (674 days with only other modes); 33,643 within the scope (3,284 days whose trips were all out of scope); 33,012 within the scope with energy. In EMP 2019: 13,825 respondents; 13,370 days with trips; 13,136 with energy; 12,195 within the scope; 11,974 within the scope with energy. Trips with a zero day weight (`POIDS_JOUR`) are dropped; durations are the declared `V2_DUREE`, since the corrected duration `v2_mduree` is never filled; distances are the corrected `distcor` where it is filled (0.23% of trips) and the declared distance otherwise. The model is the same in both years (rates, P_0 = 34.8 W, terminal-leg rules), so differences come from behaviour; the P_0 calibrated on ENTD 2008 (34.0 W) is reported for information only. The question: did each category's daily travel time stay the same while modes, distances and speeds changed? The 4-level density grid does not exist in ENTD 2008, so the comparison uses, in both years, a proxy available in both surveys: the urban-unit status of each trip end crossed with the size of the residence's urban unit. EMP 2019 is also run with this proxy, to measure its effect against the grid. With declared terminal legs, density no longer enters the reconstruction, so the proxy only changes how residents are classified.

| Trip-end status | Residence unit: rural or under 20,000 (size class 0–3) | 20,000 to 199,999 (4–6) | 200,000 or more, Paris (7–8) |
|---|---|---|---|
| City centre | sparse | intermediate | dense |
| Suburb | sparse | intermediate | intermediate |
| Isolated town | sparse | sparse | sparse |
| Rural, outside urban units | very sparse | very sparse | very sparse |

**Weights and confidence intervals.** Statistics over days use the day weight (`POND_jour` in EMP 2019, `POIDS_JOUR` in ENTD 2008); statistics over persons, such as shares of days out and budgets per person, use the individual weight (`pond_indC`, `PONDKI`). The 95% confidence intervals of means (time, trips and energy) are percentile intervals over 200 bootstrap replicates: households are drawn with replacement, and each keeps its weights, multiplied by the number of times it is drawn. Differences between 2008 and 2019 get their interval from the two surveys' replicates. Medians are given without intervals.

**Outputs of the re-estimation** (weighted; reference: days with trips, travel for needs, declared terminal legs):

- sample flows of both surveys, persons and days kept apart;
- daily travel time by population category × density class, per day with trips and per person: mean with interval, median and distribution (weighted densities); cells of fewer than 50 persons left blank;
- the constancy summary: within each category, the ratio of the highest to the lowest density class and the coefficient of variation across classes, and the difference between 2008 and 2019 with its interval;
- the same by population category × income quintile, with its constancy summary;
- trips per day and minutes per trip, per day with trips and per person, by category, by density class and by income quintile;
- mode shares by category × density class: how the budget is spent;
- daily time and energy by main-mode group, overall, by category, by density class and by income quintile, with means, medians and intervals; energy per minute by group; the test of Kölbl & Helbing's energy hypothesis, with the ratio and coefficient of variation of the group means (seven single-mode groups; core set: walking only, car driver, urban PT, train);
- variants: all trips; declared walks plus 1 min; former default terminal legs (×0.5, ×1, ×1.5); weekdays only; local trips only; P_0;
- declared walking and waiting minutes by mode group × density class, and for car trips by parking type at the destination (`MSTATION`) × density class: the calibration table of section 9.6;
- calibrated v0 and P_0; trips corrected for implausible speeds, by mode; trips left out of scope, by group, with their share of trips, time and energy;
- for ENTD 2008, the same outputs, the fill rates of `distcor` and `v2_mduree`, and a comparison of 2008 and 2019 with the density proxy in both years.

## 9.10 Monetary cost

Each mode has a fixed cost per year and, for the car, a cost per km that includes fuel, maintenance and tyres. The variable part is computed from the stored distances without new searches; the fixed part enters the mode-choice model per household.

| Mode | Fixed cost | Cost per km or per trip |
|---|---|---|
| Car | Middle bracket of the official mileage scale (barème kilométrique 2025), by fiscal power: 1,065 € (3 CV) to 1,515 € (7 CV and more) per year, e.g. 1,395 € for 5 CV; applied per car to the cell's households with 0, 1 or 2+ cars (section 6.4) | 0.316 € (3 CV) to 0.394 € (7 CV and more) per km, e.g. 0.357 € for 5 CV; +20% for electric cars |
| PT | Monthly pass of the network serving the origin; employers reimburse half of commuting passes in France [TO CONFIRM: fares by network] | Single fare when no pass is held [TO CONFIRM: fares by network] |
| Bike, e-bike | Purchase cost, annualised [TO CONFIRM: prices and lifetimes; the average price of all bikes sold in France was about 2,000 € in 2024, pulled up by e-bikes] | 0 |
| Walk | 0 | 0 |

The mileage scale is the tax allowance for the use of a private car; its middle bracket (5,001 to 20,000 km per year) has the form a × d + b, which reads directly as a cost per km a and a fixed cost b. The fiscal power of the car fleet by cell is set by default to 5 CV [TO CONFIRM: fleet composition]. Tolls and parking charges can be added later.

## 9.11 Computation along paths

- Energy is one more weight on every directed edge, as distance is. Uphill and downhill differ, so each direction of a road has its own value.
- Searches minimise time; energy is summed along the resulting fastest path in the same pass. Grid edges carry the energy of their underlying paths, so national searches never touch OSM again. Bike energy is carried in its two parts.
- PT energy is assembled from its legs: walking legs from the walk layer, level changes at transfers, waits and rides from their rates.
- Option for the bike mode: a least-effort path, as cyclists avoid climbs; compare with the fastest path in the pilot.

## 9.12 Open choices

- Level of the time budget: per population category (decision of 27 October 2026); whether age structure, household size, income or density still matter within categories, and the tolerance used to call it constant (section 9.9).
- Rate set (KH or Compendium).
- Rider power on slopes and speed caps, to calibrate on observed speeds.
- Walking speed v0: 4.8 km/h, or the door-to-door speeds of the surveys (3.4 to 3.6 km/h; section 9.3).
- Plausibility checks for the declared durations of every mode, and for public transport and train distances (section 9.9).
- Defaults for stairs, standing shares, parking times and the congestion and crowding coefficients, all tested for sensitivity of mode shares.
