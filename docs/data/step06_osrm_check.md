# Step 6: OSRM routing check

OSRM responses use current server data; the model graphs are from 2021.
Response dates (UTC): 2026-11-24T17:31:34.057791+00:00 to 2026-11-24T21:08:43.922668+00:00.
Server data versions: not provided.
This is the full-network baseline, not the grid-variant or accessibility rank-correlation validation.

Errors are model minus OSRM; relative error is the mean signed time difference divided by OSRM time. Time shares include the stated boundary.
NoRoute, NoSegment and pairs snapped beyond the configured limit are excluded from metrics and calibration. Eligible routes not reached within the Dial cutoff are excluded from metrics.

| Mode | Band (km) | Context | Matched | Cutoff | NoRoute | NoSegment | Over snap limit | Bias (min) | Median abs (min) | Within 2 min | Within 5 min | Relative error | Distance bias (m) | Median abs distance (m) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bike | 0-2 | rural | 59 | 0 | 0 | 0 | 4 | 1.33 | 1.35 | 62.7% | 91.5% | 17.1% | -27 | 1 |
| bike | 0-2 | urban | 59 | 0 | 0 | 0 | 4 | 0.99 | 1.07 | 76.3% | 93.2% | 17.7% | 7 | 16 |
| bike | 2-5 | rural | 52 | 1 | 0 | 0 | 10 | 4.51 | 4.62 | 15.4% | 55.8% | 22.1% | -71 | 5 |
| bike | 2-5 | urban | 59 | 0 | 0 | 0 | 4 | 4.01 | 3.65 | 22.0% | 71.2% | 23.0% | -153 | 57 |
| bike | 5-10 | rural | 41 | 9 | 0 | 0 | 12 | 7.98 | 8.45 | 4.9% | 19.5% | 20.5% | -228 | 26 |
| bike | 5-10 | urban | 50 | 9 | 0 | 0 | 3 | 8.52 | 8.62 | 0.0% | 8.0% | 25.4% | -326 | 224 |
| bike | 10-20 | rural | 2 | 50 | 0 | 0 | 10 | 19.09 | 19.09 | 0.0% | 0.0% | 74.5% | -180 | 180 |
| bike | 10-20 | urban | 1 | 55 | 1 | 0 | 5 | 18.78 | 18.78 | 0.0% | 0.0% | 51.6% | -3520 | 3520 |
| car | 0-2 | rural | 122 | 0 | 0 | 0 | 3 | -1.59 | 1.27 | 63.9% | 97.5% | -36.2% | -81 | 2 |
| car | 0-2 | urban | 122 | 0 | 0 | 0 | 3 | -0.28 | 0.45 | 89.3% | 99.2% | -6.1% | -25 | 17 |
| car | 2-5 | rural | 124 | 0 | 0 | 0 | 1 | -2.93 | 2.82 | 35.5% | 84.7% | -29.9% | -241 | 155 |
| car | 2-5 | urban | 120 | 0 | 0 | 0 | 5 | -0.50 | 1.23 | 70.8% | 95.8% | -5.0% | 37 | 170 |
| car | 5-10 | rural | 120 | 0 | 0 | 0 | 5 | -4.37 | 4.33 | 21.7% | 58.3% | -27.0% | -405 | 526 |
| car | 5-10 | urban | 124 | 0 | 0 | 0 | 1 | -1.38 | 2.11 | 46.0% | 83.1% | -8.4% | 79 | 283 |
| car | 10-20 | rural | 122 | 0 | 0 | 0 | 3 | -6.29 | 6.34 | 7.4% | 36.9% | -23.4% | 20 | 985 |
| car | 10-20 | urban | 120 | 2 | 0 | 0 | 3 | -2.59 | 2.77 | 35.0% | 74.2% | -9.6% | 1305 | 676 |
| car | 20-40 | rural | 115 | 5 | 0 | 0 | 5 | -9.66 | 8.99 | 0.0% | 18.3% | -21.1% | -1324 | 1608 |
| car | 20-40 | urban | 121 | 2 | 0 | 0 | 2 | -6.02 | 5.39 | 14.9% | 46.3% | -13.3% | 316 | 1263 |
| car | 40-80 | rural | 110 | 10 | 0 | 0 | 5 | -13.49 | 13.24 | 0.9% | 2.7% | -18.1% | 84 | 2203 |
| car | 40-80 | urban | 114 | 8 | 0 | 0 | 3 | -10.77 | 10.40 | 4.4% | 12.3% | -15.1% | 553 | 1745 |
| foot | 0-2 | rural | 121 | 0 | 0 | 0 | 4 | -1.45 | 1.66 | 59.5% | 89.3% | -4.6% | 34 | 1 |
| foot | 0-2 | urban | 118 | 0 | 0 | 0 | 7 | -1.52 | 1.57 | 66.9% | 96.6% | -6.1% | -37 | 15 |
| foot | 2-5 | rural | 119 | 0 | 0 | 0 | 6 | -3.81 | 2.91 | 23.5% | 76.5% | -8.5% | -74 | 7 |
| foot | 2-5 | urban | 120 | 0 | 0 | 0 | 5 | -3.21 | 2.82 | 15.8% | 82.5% | -7.5% | -80 | 51 |

## OSRM unreachable pairs

Our route time is in seconds; not reached means outside the Dial cutoff.

| Pair ID | Mode | Band (km) | Context | Outcome | Origin (lon, lat) | Destination (lon, lat) | Our time (s) |
|---|---|---|---|---|---|---|---:|
| bike-000107 | bike | 10-20 | urban | NoRoute | -0.5913103999999995, 44.875772895272085 | -0.4353764999999954, 44.9902189953154 | not reached |

## OSRM snapping distances

Limit: 25 m at either endpoint. Distribution pools both endpoints of all successful routes, including over-limit pairs.

| Mode | Successful pairs | Over limit | Endpoint distances | Minimum (m) | Median (m) | P90 (m) | Maximum (m) |
|---|---:|---:|---:|---:|---:|---:|---:|
| car | 1500 | 39 | 3000 | 0.00 | 0.00 | 0.75 | 637.53 |
| bike | 499 | 52 | 998 | 0.00 | 0.00 | 2.05 | 1319.87 |
| foot | 500 | 22 | 1000 | 0.00 | 0.00 | 1.01 | 710.35 |

## Origin context provenance

- car: 1495 distinct origins; tagged: 0.5%, density: 99.5%, beyond: 0.0%.
- bike: 500 distinct origins; tagged: 0.4%, density: 95.8%, beyond: 3.8%.
- foot: 499 distinct origins; tagged: 0.6%, density: 96.2%, beyond: 3.2%.

## Car calibration

Failed: car calibration pairs exceed the provisional Dial cutoff

Sample: data\interim\osrm\pairs.parquet.
Responses: data\interim\osrm\responses.
