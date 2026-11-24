# OSM elevation profiles (2021, pilot)

- BD ALTI ASCII tiles: 171
- Directed edge profiles: 4,461,184
- Nodes with no covering tile: 0
- Nodes with no valid elevation sample: 0
- Edges with incomplete elevation profiles: 0
- Bridge length interpolated: 237,531.1 m
- Tunnel length interpolated: 27,258.9 m
- Directed climb by mode, before / after smoothing (m):
  - bike: 2,649,646.9 / 2,457,019.4; incomplete: 0
  - car: 1,658,708.6 / 1,553,050.4; incomplete: 0
  - foot: 2,724,799.9 / 2,521,525.6; incomplete: 0
- Units: metres; mean grade is dimensionless.

## Grades to clip in active costs

Lengths are metres; grades are the original signed segment grades.
Classes are OSM highway classes, separated by directed travel mode.

| Mode | Highway class | Segments | Length (m) |
|---|---|---:|---:|
| bike | bridleway | 2 | 163.1 |
| bike | cycleway | 8 | 94.4 |
| bike | footway | 64 | 951.0 |
| bike | living_street | 14 | 53.8 |
| bike | path | 3528 | 58393.2 |
| bike | pedestrian | 73 | 723.4 |
| bike | primary | 42 | 435.4 |
| bike | primary_link | 2 | 40.9 |
| bike | residential | 411 | 6246.2 |
| bike | secondary | 54 | 469.4 |
| bike | service | 733 | 11255.2 |
| bike | steps | 10 | 145.9 |
| bike | tertiary | 93 | 1091.8 |
| bike | track | 2886 | 61132.8 |
| bike | trunk | 1 | 21.3 |
| bike | trunk_link | 1 | 22.8 |
| bike | unclassified | 470 | 7717.4 |
| foot | footway | 30 | 244.8 |
| foot | path | 38 | 493.9 |
| foot | primary | 4 | 15.3 |
| foot | residential | 2 | 16.2 |
| foot | secondary | 10 | 49.7 |
| foot | tertiary | 2 | 23.7 |
| foot | track | 2 | 16.3 |
| foot | unclassified | 6 | 46.2 |

| Edge key | Way id | Mode | Highway class | Edge length (m) | Grade |
|---|---:|---|---|---:|---:|
| 771858457:2:bike:f | 771858457 | bike | track | 2557.9 | 0.222 |
| 771858457:2:bike:r | 771858457 | bike | track | 2557.9 | -0.222 |
| 991208914:1:bike:f | 991208914 | bike | path | 2482.5 | -0.287 |
| 991208914:1:bike:r | 991208914 | bike | path | 2482.5 | 0.287 |
| 592373467:0:bike:f | 592373467 | bike | path | 2156.7 | -0.202 |
| 592373467:0:bike:r | 592373467 | bike | path | 2156.7 | 0.202 |
| 664474660:0:bike:f | 664474660 | bike | path | 2147.0 | -0.247 |
| 664474660:0:bike:r | 664474660 | bike | path | 2147.0 | 0.247 |
| 786590545:0:bike:f | 786590545 | bike | path | 1898.9 | 0.260 |
| 786590545:0:bike:r | 786590545 | bike | path | 1898.9 | -0.260 |
| 144015837:0:bike:f | 144015837 | bike | track | 1776.1 | -0.234 |
| 144015837:0:bike:r | 144015837 | bike | track | 1776.1 | 0.234 |
| 848197138:2:bike:f | 848197138 | bike | track | 1774.9 | -0.211 |
| 848197138:2:bike:r | 848197138 | bike | track | 1774.9 | 0.211 |
| 585706298:0:bike:f | 585706298 | bike | track | 1724.6 | 0.278 |
| 585706298:0:bike:r | 585706298 | bike | track | 1724.6 | -0.278 |
| 549564600:0:bike:f | 549564600 | bike | path | 1693.7 | -0.201 |
| 549564600:0:bike:r | 549564600 | bike | path | 1693.7 | 0.201 |
| 318261931:0:bike:f | 318261931 | bike | path | 1693.2 | -0.276 |
| 318261931:0:bike:r | 318261931 | bike | path | 1693.2 | 0.276 |
