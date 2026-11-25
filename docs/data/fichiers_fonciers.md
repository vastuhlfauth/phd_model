# Fichiers fonciers

- **Source:** Cerema Fichiers fonciers; restricted data under the Cerema
  convention. Do not redistribute row-level values.
- **Vintages:** 2022 for the pilot (département 33); 2021 and 2024 inspected
  for layout comparison.
- **Local path:** `data/raw/fichiers_fonciers/ff2022/`.
- **Files (2022):** 96 Parquet files under `pb0010_local` (9,991,660,416
  bytes) and 99 under `pb40_pevprincipale` (2,385,574,979 bytes), total
  12,377,235,395 bytes. The partition file name is `part-01.parquet` under
  `ccodep=<department>/`; the department-33 `pb0010_local` file is
  257,491,086 bytes and its `pb40_pevprincipale` file is 57,520,502 bytes.
  No archives are present.
- **CRS:** No `geomloc` field exists in the 2022 `pb0010_local` schema, so its
  storage format, CRS, null share and share outside département 33 cannot be
  measured. `X`, `Y` and `ban_geom` are present but are not substituted for
  `geomloc`.
- **Keys and joins:** `idlocal` identifies premises. It is non-null and unique
  in the department-33 `pb0010_local` partition (1,766,607 rows).

## Schema: `pb0010_local`, 2022, département 33

DuckDB reads the Parquet partition directly. It has 126 columns and 1,766,607
rows. The grouped schema below gives every column and its DuckDB type.

| DuckDB type | Columns |
|---|---|
| `VARCHAR` | `idlocal`, `idbat`, `idpar`, `idtup`, `idsec`, `idvoie`, `idprocpte`, `idcom`, `idcomtxt`, `ccodir`, `ccocom`, `invar`, `ccopre`, `ccosec`, `dnupla`, `dnubat`, `descc`, `dniv`, `dpor`, `ccoriv`, `ccovoi`, `dnvoiri`, `dindic`, `ccocif`, `dvoilib`, `cleinvar`, `ccpper`, `gpdl`, `ctpdl`, `dnupro`, `jdatat`, `jdatatv`, `dnufnl`, `ccoeva`, `ccoevatxt`, `dteloc`, `dteloctxt`, `logh`, `loghmais`, `loghappt`, `gtauom`, `dcomrd`, `ccoplc`, `ccoplctxt`, `cconlc`, `cconlctxt`, `cc48lc`, `top48a`, `dnatlc`, `ccthp`, `proba_rprs`, `typeact`, `loghvac`, `loghvac2a`, `loghvac5a`, `loghvacdeb`, `cchpr`, `jannat`, `dnbniv`, `hlmsem`, `loghlls`, `postel`, `dnatcg`, `jdatcgl`, `gimtom`, `cbtabt`, `jdbabt`, `jrtabt`, `cconac`, `cconactxt`, `toprev`, `catpro2`, `catpro2txt`, `catpro3`, `catpropro2`, `catproges2`, `locprop`, `locproptxt`, `source_geo`, `vecteur`, `ban_id`, `ban_type`, `ban_cp`, `ban_geom`, `reg` |
| `INTEGER` | `jdatatan`, `dvltrt`, `dloy48a`, `nbetagemax`, `nbnivssol`, `fburx`, `ccoifp`, `jannath`, `janbilmin`, `npevph`, `stoth`, `stotdsueic`, `npevd`, `stotd`, `npevp`, `sprincp`, `ssecp`, `ssecncp`, `sparkp`, `sparkncp`, `npevtot`, `slocal`, `npiece_soc`, `npiece_ff`, `npiece_i`, `npiece_p2`, `nbannexe`, `nbgarpark`, `nbagrement`, `nbterrasse`, `nbpiscine`, `ndroit`, `ndroitindi`, `ndroitpro`, `ndroitges`, `dis_ban_ff`, `idpk` |
| `BIGINT` | `ccodep` |
| `DOUBLE` | `ban_score`, `X`, `Y` |

## Section 6.2 variables: presence and nulls

Null shares are for all 1,766,607 rows in the department-33 partition. Counts
below 50 are shown as `<50`, as required for these restricted data.

| Spec variable | Meaning / unit | 2022 field | Type | Null count (share) |
|---|---|---|---|---:|
| `idlocal` | Premises identifier | present | `VARCHAR` | `<50` (0.0000%) |
| `geomloc` | Premises point; assignment to 200 m cells | **absent** | — | — |
| `dteloc` | Premises type code | present | `VARCHAR` | `<50` (0.0000%) |
| `logh` | Dwelling indicator | present | `VARCHAR` | 818,517 (46.3327%) |
| `ccthp` | Occupancy code | present | `VARCHAR` | 821,888 (46.5235%) |
| `rppo_rs` | Main/secondary-residence code | **absent** | — | — |
| `catpro2` | Owner category code | present | `VARCHAR` | `<50` (0.0000%) |
| `npiece_i` | Number of rooms, count | present | `INTEGER` | `<50` (0.0000%) |
| `stoth` | Living surface, m² | present | `INTEGER` | `<50` (0.0000%) |
| `dnbniv` | Number of levels, count | present | `VARCHAR` | `<50` (0.0000%) |
| `jannath` | Construction year, year | present | `INTEGER` | `<50` (0.0000%) |
| `sprincp` | Main professional-premises surface, m² | present | `INTEGER` | `<50` (0.0000%) |
| `typeact` | Professional activity code | present | `VARCHAR` | 1,681,816 (95.2003%) |
| `cconac` | Occupant NAF code | present | `VARCHAR` | 1,712,218 (96.9213%) |

`logh` has `t` for 948,090 rows; the other 818,517 rows are null (there is no
explicit non-dwelling code in this partition). `ccthp` contains the codes
`B`, `D`, `G`, `L`, `N`, `P`, `R`, `T`, `V`, `X` and nulls. The `P` and `V`
codes mentioned in section 6 are present.

## Counts by value

Counts under 50 are suppressed to `<50`. Null is shown explicitly.

- `dteloc`: `1` 563,829; `2` 384,261; `3` 724,877; `4` 93,640.
- `logh`: `t` 948,090; null 818,517.
- `ccthp`: null 821,888; `B` 83; `D` 9,592; `G` 12,093; `L` 351,147;
  `N` 65; `P` 488,850; `R` 122; `T` 6,603; `V` 76,122; `X` `<50`.
- `rppo_rs`: not present; no value counts are available. `proba_rprs` is a
  different field name and has not been treated as a substitute.
- `typeact`: null 1,681,816; `ATE1` 4,283; `ATE2` 2,539; `ATE3` 70;
  `BUR1` 16,350; `BUR2` 7,094; `BUR3` 781; `CLI1` 146; `CLI2` 595;
  `CLI3` 2,735; `CLI4` 119; `DEP1` 657; `DEP2` 8,663; `DEP3` 2,295;
  `DEP4` 1,632; `DEP5` 186; `ENS1` 513; `ENS2` 319; `EXC1` 207;
  `HOT1` 94; `HOT2` 1,004; `HOT3` 222; `HOT4` 565; `HOT5` 5,874;
  `IND1` 180; `IND2` `<50`; `MAG1` 19,572; `MAG2` 1,263; `MAG3` 2,102;
  `MAG4` 1,737; `MAG5` 232; `MAG6` 361; `MAG7` 516; `SPE1` 267;
  `SPE2` 570; `SPE3` 348; `SPE4` 130; `SPE5` 82; `SPE6` 125; `SPE7` 350.
- `catpro2`:

```text
99=52; A1=7108; A1 G1=<50; A1 L1=<50; A1 M1=<50; A1 X1=99; A1 Z1=<50; A1 Z2=<50; A1 Z2 X1=<50; A2=172; A2 M1=<50; A2 M1 X1=<50; A2 X1=<50; A3=<50; A4=<50; A5=<50; E1=<50; E2=<50; E2 M1=<50; E2 X1=<50; E3=<50; E3 M1=<50
F1=207489; F1 F6=<50; F1 F7=<50; F1 G1=141; F1 G2=51; F1 M1=160; F1 M2=79; F1 R4=<50; F1 S1=83; F1 S2=284; F1 X1=1495; F2=255; F4=<50; F4 R5=<50; F5=<50; F5 M1=<50; F5 X1=<50; F6=4038; F6 F7=<50; F6 F7 X1=<50; F6 G1=<50; F6 G2=<50; F6 G2 M1=<50; F6 M1=<50; F6 R5=<50; F6 X1=<50; F6 Z1=<50; F7=23744; F7 A1=<50; F7 A1 M1=<50; F7 A5=143; F7 G1=580; F7 G1 G2=123; F7 G1 M1=<50; F7 G1 X1=<50; F7 G2=434; F7 G2 M1=<50; F7 L1=<50; F7 L4=<50; F7 M1=98; F7 R4=<50; F7 S1=<50; F7 X1=167; F7 Z1=<50; F7 Z2=<50
G1=121569; G1 G2=193; G1 G2 M1=<50; G1 L1=<50; G1 L3=<50; G1 M1=180; G1 M1 X1=<50; G1 S1=2818; G1 S2=<50; G1 X1=1905; G1 Z1=<50; G1 Z2=84; G2=4310; G2 L1=<50; G2 M1=696; G2 X1=151; G2 Z2=<50; L1=1133; L1 L2=<50; L1 X1=<50; L2=413; L2 M1=<50; L2 M1 X1=<50; L2 X1=<50; L3=<50; L3 X1=<50; L4=98; M1=7711; M1 X1=361; M2=972
P1=2132; P1 A2=251; P1 A3=<50; P1 E1=369; P1 E2=<50; P1 E3=<50; P1 F1=1249; P1 F1 S2=380; P1 F7=<50; P1 G1=<50; P1 L4=<50; P1 M1=89; P1 M2=<50; P1 P2=118; P1 P3=<50; P1 P5=<50; P1 R1=<50; P1 R2=<50; P1 R3=136; P1 R4=<50; P1 S1=<50; P1 S2=1661; P1 X1=<50; P1 Z1=<50; P1 Z4=<50; P2=664; P2 A1=<50; P2 F1=50; P2 P4=<50; P3=1115; P3 F1=973; P3 M1=59; P3 M2=93; P3 P4=<50; P3 P5=<50; P3 P5 M1=<50; P3 S2 M1=<50
P4=3285; P4 F1=176; P4 F2=<50; P4 F6=<50; P4 F7=<50; P4 G1=<50; P4 L1=<50; P4 L3=<50; P4 M1=97; P4 M2=<50; P4 P5=<50; P4 P5 F7=<50; P4 R5=<50; P4 S1=<50; P4 X1=<50; P4 Z2=<50; P5=10892; P5 A1=<50; P5 E1=<50; P5 E2=<50; P5 E3=<50; P5 F1=5304; P5 F6=<50; P5 F7=<50; P5 G1=167; P5 L2=<50; P5 L4=<50; P5 M1=189; P5 M2=<50; P5 R5=<50; P5 R6=<50; P5 R7=<50; P5 S1=<50; P5 S2=<50; P5 X1=<50; P5 Z2=<50
R0=174; R0 X1=<50; R1=110; R2=393; R2 M1=<50; R3=<50; R4=65; R4 G1=<50; R4 M1=<50; R4 Z2=<50; R5=5427; R6=150; R6 G1=<50; R7=321; S1=703; S1 L1=<50; S1 L2=<50; S1 M1=<50; S1 M1 X1=<50; S1 X1=<50; S2=1266; S2 L2=<50; S2 M1=<50; S2 M1 X1=<50; S2 X1=<50; X1=1335573; Z1=566; Z1 M1=131; Z1 X1=<50; Z2=1665; Z2 M1=<50; Z2 X1=<50; Z3=<50; Z4=<50
```

## Occupied-dwelling groups requested by section 6.3

The four combinations of `ccthp = 'V'`/not `V` and `rppo_rs = 'RS'`/not
`RS`, among `logh = 't'`, are **not computable from this 2022 table**:
`rppo_rs` is absent. No replacement field or vintage was used.

## 2021 and 2024 layout comparison

From partition names and DuckDB schemas only: 2021 has 94
`pb0010_local/ccodep=*/part-01.parquet` files and no `pb40_pevprincipale`
folder; its department-33 `pb0010_local` schema has 123 columns. 2024 has 96
files in each of `pb0010_local` and `pb40_pevprincipale`; its `pb0010_local`
schema has 132 columns. The 2021-only `pb0010_local` fields include
`actvac`, `actvac2a`, `actvac5a`, `habitat`, and `proba_rprs`; 2024-only
fields include `rppo_rs`, `typeloc`, BAN/RNB fields, `assieft`, `codique`,
and `nbnivssol`. Neither inspected schema has `geomloc`.

## Quirks

- Counts are aggregate-only. No sample rows or row-level values are included.
- Section 6.2's 2022 `geomloc` and `rppo_rs` are absent in the source schema.
  In particular, section 6.3's occupied-stock expression cannot be applied
  as written to the 2022 table. `proba_rprs` is not assumed to be equivalent
  to `rppo_rs`.

## Sample

Omitted: this restricted dataset is documented with schema and aggregate
counts only.

## Step 3b aggregate checks (2026-11-25)

These are aggregate-only checks on the restricted département-33 partitions.
Counts below 50 are suppressed as `<50`; no row-level values are reported.
The 2022 dwelling selector gives 948,090 rows for both `logh = 't'` and
`dteloc IN ('1', '2')`, with no mismatches.

### Location

| 2022 dwelling measure | Result |
|---|---:|
| `X` null | 1,328 (0.1401%) |
| `Y` null | 1,328 (0.1401%) |
| `ban_geom` null | 1,182 (0.1247%) |
| `X` range | 3,428,908.1–3,556,146.4 |
| `Y` range | 2,399,826.2–2,559,302.7 |
| `ban_geom` coordinate range (EPSG:2154) | X 362,530.4–487,500.9; Y 6,350,200.6–6,504,676.7 |
| `ban_score`, median / p90 / p99 | 0.56 / 0.65 / 0.70 |
| `dis_ban_ff`, median / p90 / p99 | 38 / 250 / 2,127.21 m |

`X` and `Y` ranges and the match to the standard 200 m EPSG:3035 grid support
EPSG:3035. `ban_geom` is EWKB with SRID 2154. Among the 945,580 dwellings
with both points, after transforming the BAN point to EPSG:3035, 339,786
(35.9341%) fall in a different 200 m cell. The transformed point-distance
median, p90 and p99 (38.05, 250.21 and 2,131.35 m) closely track
`dis_ban_ff`.

The 200 m cell derived from `X` and `Y` has a Filosofi row for 934,260 of the
948,090 dwellings (98.5413%); 12,502 coordinate-bearing dwellings have no
matching row, and 1,328 have no coordinates. The exact share outside the
département-33 bounding box was not calculated: the full local commune
geometry read previously exceeded the one-minute limit.

Counts by location fields are for all 1,766,607 premises:

| Field | Value counts |
|---|---|
| `source_geo` | `BD Parcellaire 2008` `<50`; `BD Parcellaire 2010` `<50`; `BD Parcellaire 2012` `<50`; `BD Parcellaire 2014` `<50`; `BD Parcellaire 2015` 59; `N` 2,972; `PCI DGFiP 2017-07-06` `<50`; `PCI DGFiP 2018-04-03` `<50`; `PCI DGFiP 2018-10-01` `<50`; `PCI DGFiP 2019-01-01` `<50`; `PCI DGFiP 2019-04-01` `<50`; `PCI DGFiP 2020-07-01` `<50`; `PCI DGFiP 2021-04-01` `<50`; `PCI DGFiP 2021-07-01` `<50`; `PCI DGFiP 2021-10-01` `<50`; `PCI DGFiP 2022-04-01` 7,758; `PCI DGFiP 2022-07-01` 1,195; `PCI DGFiP 2022-10-01` 1,754,553 |
| `vecteur` | `I` `<50`; `N` 2,972; `V` 1,763,624 |
| `ban_type` | null 2,098; `housenumber` 980,054; `locality` 23,022; `municipality` 1,037; `street` 760,396 |

`ban_score` and `dis_ban_ff` percentiles are over dwellings with a non-null
value. No Cerema documentation was found under
`data/raw/fichiers_fonciers/`; meanings for `source_geo` and `vecteur` are
therefore not inferred.

### Dwelling occupancy and residence codes

2022 counts among 948,090 dwellings:

| Field | Value counts |
|---|---|
| `proba_rprs` | `AC` 46,796; `INCONNU` 11,589; `NO` 253,447; `PM` 206,295; `RP` 339,021; `RS` 90,942 |
| `ccthp` | null 16,562; `B` 82; `G` 12,072; `L` 349,447; `N` `<50`; `P` 488,534; `T` 6,498; `V` 74,847; `X` `<50` |
| `loghvac` | null 873,243; `t` 74,847 |

2022 `proba_rprs` cross-tabs (rows are `proba_rprs`; omitted combinations
have no rows):

| `proba_rprs` | `ccthp` counts |
|---|---|
| `AC` | `P` 46,796 |
| `INCONNU` | null 11,585; `P` `<50` |
| `NO` | `B` 72; `G` 8,484; `L` 192,965; `N` `<50`; `T` 4,135; `V` 47,764; `X` `<50` |
| `PM` | null 4,977; `B` `<50`; `G` 3,588; `L` 156,482; `N` `<50`; `P` 11,771; `T` 2,363; `V` 27,083; `X` `<50` |
| `RP` | `P` 339,021 |
| `RS` | `P` 90,942 |

| `proba_rprs` | `loghvac` counts |
|---|---|
| `AC` | null 46,796 |
| `INCONNU` | null 11,589 |
| `NO` | null 205,683; `t` 47,764 |
| `PM` | null 179,212; `t` 27,083 |
| `RP` | null 339,021 |
| `RS` | null 90,942 |

For `ccthp = 'V'`, `loghvac` is `t` for all 74,847 dwellings; conversely,
every dwelling with `loghvac = 't'` has `ccthp = 'V'`.

2024 dwelling counts:

| Field | Value counts |
|---|---|
| `ccthp` | null 14,344; `B` 2,364; `G` 16,635; `L` 342,970; `P` 504,057; `T` 2,121; `V` 85,058; `X` `<50`; there is no `S` |
| `rppo_rs` | `INCONNU` 9,440; `MR` 49,629; `NO` 449,174; `PM` 15,223; `RPPO` 386,226; `RS` 57,883 |

2024 cross-tab of `ccthp` by `rppo_rs`:

| `ccthp` | `rppo_rs` counts |
|---|---|
| null | `INCONNU` 9,432; `PM` 4,912 |
| `B` | `NO` 2,364 |
| `G` | `NO` 16,635 |
| `L` | `NO` 342,970 |
| `P` | `INCONNU` `<50`; `MR` 49,629; `PM` 10,311; `RPPO` 386,226; `RS` 57,883 |
| `T` | `NO` 2,121 |
| `V` | `NO` 85,058 |
| `X` | `NO` `<50` |

There are 941,139 `idlocal` joins where both vintages classify the premises as
a dwelling. The 2022 `proba_rprs` by 2024 `rppo_rs` cross-tab is:

| 2022 `proba_rprs` | 2024 `rppo_rs` counts |
|---|---|
| `AC` | `INCONNU` `<50`; `MR` 3,117; `NO` 5,487; `PM` `<50`; `RPPO` 32,420; `RS` 5,450 |
| `INCONNU` | `INCONNU` `<50`; `MR` 620; `NO` 4,798; `PM` `<50`; `RPPO` 5,033; `RS` 958 |
| `NO` | `MR` 8,133; `NO` 220,104; `PM` `<50`; `RPPO` 16,751; `RS` 5,636 |
| `PM` | `MR` 2,706; `NO` 190,615; `PM` 10,174; `RPPO` 182; `RS` `<50` |
| `RP` | `MR` 24,187; `NO` 12,188; `PM` `<50`; `RPPO` 296,898; `RS` 4,969 |
| `RS` | `INCONNU` `<50`; `MR` 10,012; `NO` 9,487; `PM` `<50`; `RPPO` 31,051; `RS` 40,025 |

No local Cerema codebook was found for `ccthp` or `proba_rprs`. These code
counts do not establish meanings or equivalence between `proba_rprs` and
`rppo_rs`.

### Candidate main residences and Filosofi households

For this check only, null vacancy/residence values are treated as neither
vacant nor secondary. The candidate is a dwelling that is neither marked
vacant nor `proba_rprs = 'RS'`. Both vacancy definitions (`loghvac = 't'`
and `ccthp = 'V'`) select exactly the same rows, so each produces 782,301
candidate main residences. This is a comparison, not a decision to substitute
fields in section 6.

Filosofi has 55,040 department-33 200 m rows and 735,421.1 households
(`men`), selected by `lcog_geo`. Of the 782,301 candidate main residences,
774,603 fall in a 200 m Filosofi row whose `lcog_geo` includes department 33.
The all-dwelling candidate total is 106.37% of that household benchmark; the
matched-cell total is 105.33%.

Natural-level assignment decodes the resolution and corner in `idcar_nat`;
for 934,260 points with a Filosofi 200 m row, all direct natural-cell IDs
agree with the 200 m file's `idcar_nat`. Of 781,111 candidate main residences
with coordinates, fewer than 50 fall outside every natural-level cell
(0.0056%). Separately, 1,190 candidate main residences have missing `X` or
`Y` and cannot be assigned spatially.

For natural-level cells whose 200 m rows all list only department-33
communes, ratios are candidate main residences divided by Filosofi `men`.
Each entry is a ratio; counts under 50 are suppressed.

| Cell side (m) | Cells | P10 | P20 | P30 | P40 | Median | P60 | P70 | P80 | P90 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 1,067 | 0.948 | 0.992 | 1.021 | 1.048 | 1.071 | 1.108 | 1.165 | 1.250 | 1.407 |
| 1,000 | 1,826 | 0.758 | 0.866 | 0.927 | 0.965 | 0.991 | 1.006 | 1.032 | 1.063 | 1.120 |
| 2,000 | 755 | 0.802 | 0.892 | 0.955 | 0.981 | 1.002 | 1.027 | 1.054 | 1.089 | 1.146 |
| 4,000 | 112 | 0.875 | 0.926 | 0.967 | 0.993 | 1.006 | 1.023 | 1.060 | 1.103 | 1.161 |
| 8,000 | `<50` | 0.831 | 0.949 | 1.000 | 1.042 | 1.061 | 1.069 | 1.080 | 1.138 | 1.684 |
| 16,000 | `<50` | 1.069 | 1.111 | 1.153 | 1.195 | 1.237 | 1.271 | 1.305 | 1.339 | 1.373 |

The ten communes with the largest 2022 `proba_rprs = 'RS'` share among
dwellings are Dardenac (55.6%), Fontet (54.4%), Cauvignac (54.2%), Giscos
(53.0%), Balizac (53.0%), Vendays-Montalivet (51.0%), Tayac (50.6%),
Saint-Philippe-du-Seignal (47.8%), Lerm-et-Musset (46.8%) and Lacanau
(46.5%).

### Social housing

Among 2022 dwellings, strict `catpro2 = 'F1'` counts 111,881; any `catpro2`
value containing `F1` counts 118,658. The sum of Filosofi `log_soc` across
department-33 200 m rows is 99,906.6. In the natural-level cells whose
200 m rows all list only department-33 communes, the corresponding strict
and combined counts are 111,102 and 117,858, against `log_soc` total
99,546.4.

The ratio universe comprises 3,796 fully department-33 natural cells; 2,723
have zero `log_soc`, leaving 1,073 positive-denominator cells for the ratios.
Cells with zero `log_soc` have no defined ratio and are excluded. Each table
gives P10 through P90.

**Strict `F1`:**

| Cell side (m) | Cells | P10 | P20 | P30 | P40 | Median | P60 | P70 | P80 | P90 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 347 | 0.857 | 1.000 | 1.000 | 1.053 | 1.077 | 1.118 | 1.187 | 1.328 | 1.913 |
| 1,000 | 563 | 0.836 | 1.000 | 1.022 | 1.049 | 1.068 | 1.091 | 1.117 | 1.186 | 1.333 |
| 2,000 | 115 | 0.732 | 0.998 | 1.000 | 1.000 | 1.036 | 1.070 | 1.109 | 1.145 | 1.250 |
| 4,000 | `<50` | 0.946 | 1.000 | 1.034 | 1.077 | 1.106 | 1.127 | 1.149 | 1.200 | 1.258 |
| 8,000 | `<50` | 0.582 | 0.849 | 1.000 | 1.002 | 1.013 | 1.040 | 1.071 | 1.096 | 1.181 |
| 16,000 | `<50` | 1.012 | 1.023 | 1.035 | 1.047 | 1.058 | 1.059 | 1.060 | 1.062 | 1.063 |

**Combined codes containing `F1`:**

| Cell side (m) | Cells | P10 | P20 | P30 | P40 | Median | P60 | P70 | P80 | P90 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 347 | 1.000 | 1.000 | 1.040 | 1.071 | 1.100 | 1.153 | 1.228 | 1.402 | 2.000 |
| 1,000 | 563 | 1.000 | 1.023 | 1.051 | 1.071 | 1.091 | 1.112 | 1.162 | 1.250 | 1.429 |
| 2,000 | 115 | 1.000 | 1.000 | 1.000 | 1.037 | 1.071 | 1.113 | 1.143 | 1.216 | 1.307 |
| 4,000 | `<50` | 1.000 | 1.035 | 1.053 | 1.095 | 1.111 | 1.127 | 1.149 | 1.200 | 1.258 |
| 8,000 | `<50` | 1.001 | 1.035 | 1.055 | 1.072 | 1.097 | 1.125 | 1.151 | 1.171 | 1.349 |
| 16,000 | `<50` | 1.087 | 1.091 | 1.094 | 1.098 | 1.102 | 1.121 | 1.140 | 1.159 | 1.178 |

### Cleaning and neighboring departments

| 2022 dwelling check | Rows |
|---|---:|
| `stoth < 0` | `<50` |
| `jannath` outside 1600–2022 | 11,820 |
| `dniv >= 80` | 622 |
| `nbetagemax <= 0` or null | 403,812 |
| null `npiece_i` | `<50` |
| null `dnbniv` | `<50` |

The departments represented in `lcog_geo` for natural cells reached by
department 33 are 17, 24, 33, 40 and 47. The 2022 `pb0010_local` partitions
for neighboring departments 17, 24, 40 and 47 all exist.
