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
