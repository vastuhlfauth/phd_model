# 12. Congestion extension (later phase)

- **Out of equilibrium.** Congestion at period t sets speeds at period t+1: car O-D flows from the demand models at t are assigned on the combined car graph, link speeds for t+1 come from a speed-flow model, and the new costs feed the demand models at t+1. No fixed point is sought; speeds are smoothed between periods.

```text
v_l(t+1) = f( q_l(t), class_l, lanes_l, context_l ; θ )
```

- **Models to test:** volume-delay functions of the BPR type (Bureau of Public Roads 1964) and Akçelik (1991), against regressions estimated on Google Maps travel times by road section and time of day, with daily flows, class, lanes and urban context as explanatory variables (panel of sections).
- **Data: the existing Google pipeline.** The current scripts (section 14.4) query the Google Routes API (`computeRoutes`) between the representative points of 200 m cells, for a sample stratified by modelled duration (100 O-D pairs per mode by default), at fixed departure times (07:00 and 08:20 on a Wednesday), with traffic-aware routing for cars. They request only the duration and distance of each route. For the congestion phase three more fields are needed: `staticDuration` (the duration without traffic), whose ratio to `duration` gives the congestion index of the route; the route `polyline`, to split routes into road sections; and, for cars, the traffic on the polyline (`extraComputations: TRAFFIC_ON_POLYLINE`), which marks each interval as normal, slow or jammed [TO CONFIRM: pricing tier of these fields].
- **Data:** Google Maps travel times are obtained between addresses. They are matched to the model by locating each address in its 200 m and 1 km cells and adding the model's terminal legs, and by splitting routes into road sections, from their polylines, for the section-level regressions. Traffic counts [TO CONFIRM: national and departmental count data]. The terms of the Google Maps Platform on storing results must be checked before collecting data.
- **Effects:** driving time; driving energy through the congestion penalty of section 9.6; parking search; buses in mixed traffic; bike stops (section 9.8).
- **Capacities:** every car grid edge keeps a capacity derived from the lanes and class of the roads on its path; trunk links keep theirs directly. Assignment is network-exact on the trunk layer and approximate on the grid.
- **Cost:** congestion changes link times everywhere, so each period needs one national car run (tens of minutes), or path-fixed updates with the bounds of section 11.5 between full runs.
