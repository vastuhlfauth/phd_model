# EMC² and Île-de-France EGT inventory (step 12, Part D)

Inventory of the 13 EMC² surveys and the Île-de-France EGT 2018-2020
delivered by ADISP under `data/raw/emc2/`. Read-only scan: headers,
dictionaries and counts, no processing. The raw root is ignored by Git
(`.gitignore`, line 1: `/data/`); nothing from the raw folder is
committed. All numbers below are aggregate counts over whole surveys or
fieldwork periods; no displayed cell is below 50 respondents.

Every "verified" statement below was checked directly against the files
with DuckDB (headers, value ranges, joins). Variable labels quoted in
French come from the supplied dictionaries.

## Files and formats

Each EMC² survey is one ADISP `lil-XXXX` delivery with four parallel
data folders (`.csv`, `.dta`, `.sas7bdat`, `.sav`) holding the same
tables, plus a `Doc` folder. CSV layout (semicolon-separated):

- `Csv/Fichiers_Originaux/{survey}_ori_{men,pers,depl,traj}.csv`
  (original survey-specific variables; Aix-Marseille also has an
  `ori_opi` opinion table, 4,865 rows, face-to-face only);
- `Csv/Fichiers_Standard/{survey}_std_{men,pers,depl,traj}.csv`
  (Cerema standard V16: households, persons, trips, legs).

`Doc` always contains: the original variable dictionary
(`Dessin*dico*.xls[x]`, readable), the standard V16 dictionary
(`Dico_Dessin_StandardV16_Corrige.xls`, identical across surveys; old
`.xls`, not readable with the current toolchain — see Blockers), the
questionnaire, a `Note_calcul_distances` (odt) describing how distances
were computed, and `SIG` shapefiles: `ZF` (fine zones), `DTIR` (sampling
sectors) and `GT` (traffic generators).

The EGT (`lil-1581`) has one folder per format (CSV/SAS/SPSS/STATA) with
7 tables (`01_Menage`, `02_Individu`, `03_Deplacement`, `04_Trajet`,
`05_Voiture`, `06_Drm`, `07_Velo`) and a `Documentation` folder:
variable dictionary (`Dictionnaire EGT 2018-2020 ... avec poids.xlsx`),
notice, questionnaire, and value-label files
(`LABELS/modalites_labels_variables_lil-1581.txt` plus per-format label
scripts). No zoning geometry is supplied for the EGT.

## Counts

Rows counted in the standard CSV tables (EGT: delivered tables).
"Described" = persons with a described day (`PENQ = 1`; EGT `ENQ = 1`,
of whom 616 reported zero trips).

| Survey (ADISP id) | Households | Persons | Described | Trips | Legs |
|---|---:|---:|---:|---:|---:|
| Aix-Marseille-Provence 2020 (lil-1556) | 17,510 | 37,557 | 25,530 | 84,469 | 63,068 |
| Sables d'Olonne 2021 (lil-1559) | 1,380 | 2,620 | 1,560 | 5,342 | 3,950 |
| Gironde 2021 (lil-1633) | 8,020 | 16,109 | 11,814 | 40,594 | 32,504 |
| Grand Reims 2021 (lil-1560) | 4,051 | 8,061 | 5,892 | 22,190 | 14,525 |
| Grande Région Angevine 2022 (lil-1561) | 5,854 | 12,800 | 8,094 | 26,975 | 20,209 |
| Grande région grenobloise 2020 (lil-1554) | 7,339 | 15,423 | 12,453 | 44,600 | 33,278 |
| Indre-et-Loire 2019 (lil-1631) | 6,383 | 13,446 | 8,736 | 33,388 | 25,265 |
| Lannion-Trégor 2022 (lil-1562) | 1,236 | 2,543 | 1,466 | 5,584 | 4,255 |
| Loire Sud – Pilat 2021 (lil-1634) | 6,188 | 12,657 | 9,625 | 32,886 | 24,937 |
| Métropole Savoie 2022 (lil-1636) | 3,207 | 6,605 | 4,532 | 17,260 | 12,746 |
| Nord Est Thionvillois 2019 (lil-1630) | 830 | 2,011 | 1,092 | 4,846 | 3,676 |
| Valenciennois 2019 (lil-1632) | 4,170 | 9,662 | 6,714 | 23,138 | 17,405 |
| Vendée 2020 (lil-1555) | 6,630 | 14,548 | 8,111 | 29,797 | 24,028 |
| Île-de-France EGT 2018-2020 (lil-1581) | 4,766 | 10,470 | 9,350 | 35,656 | 62,398 |

EGT side tables: 4,862 cars, 431 motorised two-wheelers, 3,828 bikes.

## Fieldwork dates and described days by period

The EMC² standard person table dates the **described day** (`AN`,
`MOIS`, `DATE`, weekday `JOUR`, 1 = Monday). The interview date is only
in the original household table (`MDAT`, `JENQ`). Verified on
Aix-Marseille: the interview is the day after the described day for
98.9% of described persons (lag 2–6 days for the rest, postponed
interviews). The EGT household table dates the described day (`JOUR`,
`MOIS`, `ANNEE`; `JOURSEM` matches that date's weekday, verified).
Described days are weekdays (Mon–Fri) only, in every survey.

Reference periods:

| Period | Dates |
|---|---|
| Before lockdown 1 | before 17 Mar 2020 |
| Lockdown 1 | 17 Mar – 10 May 2020 |
| Between lockdowns 1 and 2 | 11 May – 29 Oct 2020 |
| Lockdown 2 | 30 Oct – 14 Dec 2020 |
| Curfews | 15 Dec 2020 – 2 Apr 2021 |
| Lockdown 3 | 3 Apr – 2 May 2021 |
| Curfew | 3 May – 19 Jun 2021 |
| After restrictions | from 20 Jun 2021 |

Described days per survey (counts of described persons). **No survey
has described days during lockdowns 1–3 or the curfew periods**:
fieldwork was suspended, so only three periods occur.

| Survey | Described-day range | Before lockdown 1 | Between lockdowns 1–2 | After restrictions |
|---|---|---:|---:|---:|
| Aix-Marseille-Provence 2020 | 2019-11-04 → 2020-10-16 | 20,041 | 5,489 | – |
| Sables d'Olonne 2021 | 2021-09-21 → 2021-12-09 | – | – | 1,560 |
| Gironde 2021 | 2021-09-13 → 2021-12-17 | – | – | 11,814 |
| Grand Reims 2021 | 2021-09-06 → 2021-12-10 | – | – | 5,892 |
| Grande Région Angevine 2022 | 2021-09-13 → 2022-01-12 | – | – | 8,094 |
| Grande région grenobloise 2020 | 2019-11-12 → 2020-10-16 | 9,273 | 3,180 | – |
| Indre-et-Loire 2019 | 2019-01-07 → 2019-05-06 | 8,736 | – | – |
| Lannion-Trégor 2022 | 2022-02-21 → 2022-04-29 | – | – | 1,466 |
| Loire Sud – Pilat 2021 | 2019-12-09 → 2021-12-10 | 6,578 | – | 3,047 |
| Métropole Savoie 2022 | 2022-02-28 → 2022-05-23 | – | – | 4,532 |
| Nord Est Thionvillois 2019 | 2019-04-01 → 2019-06-14 | 1,092 | – | – |
| Valenciennois 2019 | 2018-11-05 → 2019-02-07 | 6,714 | – | – |
| Vendée 2020 | 2020-01-27 → 2020-10-16 | 3,404 | 4,707 | – |
| Île-de-France EGT | 2018-01-22 → 2020-03-13 | 9,350 | – | – |

### Sampling sector × period

Summary of the crosstab of sampling sector (`STP`) × period over
described days (full crosstabs would show many cells under 50
respondents and are therefore not printed):

| Survey | Sectors | Sectors in >1 period | Mean / max days between a sector's first and last described day |
|---|---:|---:|---|
| Aix-Marseille-Provence 2020 | 160 | 156 | 337 / 347 |
| Sables d'Olonne 2021 | 9 | 0 | 74 / 79 |
| Gironde 2021 | 50 | 0 | 94 / 95 |
| Grand Reims 2021 | 32 | 0 | 94 / 95 |
| Grande Région Angevine 2022 | 47 | 0 | 118 / 121 |
| Grande région grenobloise 2020 | 89 | 89 | 337 / 339 |
| Indre-et-Loire 2019 | 54 | 0 | 114 / 119 |
| Lannion-Trégor 2022 | 9 | 0 | 67 / 67 |
| Loire Sud – Pilat 2021 | 70 | 70 | 728 / 732 |
| Métropole Savoie 2022 | 28 | 0 | 80 / 84 |
| Nord Est Thionvillois 2019 | 6 | 0 | 74 / 74 |
| Valenciennois 2019 | 41 | 0 | 92 / 94 |
| Vendée 2020 | 47 | 47 | 263 / 263 |

Sectors are **not** surveyed one after another: each sector's described
days span nearly the whole fieldwork window. Where fieldwork crossed
COVID restrictions (Aix-Marseille, Grenoble, Vendée around lockdown 1;
Loire Sud with a 2019 wave and a late-2021 wave), (almost) every sector
appears in both periods. A within-survey before/after test can
therefore compare the same sectors across periods in those four
surveys; the others are single-period.

## Survey design

**EMC² (Cerema standard V16).**

- **Described day:** the day before the interview (verified, above);
  weekdays only. Interviews run Tuesday–Saturday (`MDAT`/`JENQ` in the
  original household table).
- **Interview modes:** `METH` in `std_men` (1 = face-to-face, 2 =
  telephone); person-level `PMET` in `std_pers`. Mixed except Sables
  d'Olonne, Lannion-Trégor, Nord Est Thionvillois and Vendée (telephone
  only). Face-to-face interviews cover every household member aged 5+
  (observed ≈ 2.0 surveyed per household ≈ the count of members 5+);
  telephone interviews cover a subset (observed 1.1–1.3 per household),
  so household-complete analyses are face-to-face only.
- **Ages:** 5+ (observed minimum age 5 among described persons in all
  surveys).
- **Weights:** `COE0` (household, `std_men`); `COE1` and `COEP`
  (person, `std_pers`). The exact definition of `COE1` vs `COEP` is in
  the V16 dictionary (`.xls`, unread — see Blockers). There is no
  separate day weight, as every surveyed person describes exactly one
  day; the person weight plays the role of step 11's `POND_JOUR`.
- **Zoning:** fine zone (`ZFM`/`ZFP`/`ZFD`/`ZFT`) and sampling sector
  (`STM`/`STP`/`STD`/`STT`, "DTIR") in every standard table; `GD*`/`GT*`
  aggregate zones. Geometry supplied as shapefiles (`ZF`, `DTIR`, `GT`);
  Sables d'Olonne ships `.dbf` attribute tables without `.shp` geometry.
- **Home commune code:** not in the data tables, but the `ZF` SIG table
  maps every fine zone to its INSEE commune (field name varies:
  `CODE_COM`/`DEPCOM` in Aix-Marseille, `NUM_COM` in Gironde,
  `INSEE`/`INSEE_COM` elsewhere; verified per survey). So the INSEE
  density grid can be attached via fine zone → commune.

**Île-de-France EGT 2018-2020 (IDFM, non-Cerema variable set).**

- **Described day:** the day before the interview ("la veille",
  per the individual table labels, e.g. `MNPMOB`, `DEPL`); weekdays
  only; fieldwork 22 Jan 2018 – 13 Mar 2020, stopped by lockdown 1.
- **Interview modes:** `TYPE_QUEST`: CAPI face-to-face (4,087
  households, all members 5+, observed ≈ 2.1 surveyed per household) and
  CATI telephone (679 households; one randomly drawn member, `KISH` = 1,
  855 persons, plus 641 CATI persons with `KISH` = 0).
- **Ages:** 5+ (`POIDSI` defined for surveyed persons 5+ only; observed
  minimum 5).
- **Weights:** `POIDSM` (household), `POIDSI` (individual, also carried
  on trips); no day weight.
- **Zoning:** no fine zone and no sampling sector. Residence: INSEE
  commune (`RESINSEE`), département (`RESDEP`), couronne (`RESCOUR`),
  and coordinates rounded to 3 decimals (~70–110 m: `RESLNG`,
  `RESLAT`). Trips carry origin/destination commune (`ORINSEE`,
  `DESTINSEE`) and rounded coordinates. The INSEE density grid can be
  attached via the commune code directly.

## Variable availability for the step-11 analyses

| Step-11 input | EMC² standard (verified header + ori dictionary) | EGT (verified header + labels file) |
|---|---|---|
| Age, sex | `P4`, `P2` (`std_pers`) | `AGE`, `SEXE` |
| Occupation status | `P7` "occupation principale" (+ `PCSC`/`PCSD` CSP) | `OCCP` (+ `CS8`, `CS24L`) |
| Household income | **absent** (not collected in EMC²; no "revenu" entry in the dictionaries) | `REVENU`, 10 brackets + refusal (−1) / don't-know (−2); 90 + 686 + 11 households without a usable bracket |
| Cars | household vehicle block in `std_men` (`M6`–`M13*`); per-car details | `NB_VD` (cars at disposal), `NB_VEH`; `05_Voiture` table |
| Bikes | `M20` "nombre de vélos à disposition" (ori) / bike block `M15*`–`M20*` (std) | `NB_VELO`, `NB_VAE`; `07_Velo` table |
| Driving licence | `P5` "possession du permis de conduire voiture" | `PERMVP` |
| Mobility difficulty | `PL1` "difficultés de déplacement" (ori pers; FAF only in some surveys) | `GENE` "gêne ressentie lors des déplacements" |
| Trip motive | `D2A` (origin), `D5A` (destination), V16 codes 01–91 | `ORMOT`/`DESTMOT` (detailed), `ORMOT_H9`/`DESTMOT_H9` (9 groups), `MOTIF_COMBINE` |
| Trip mode | `MODP` (V16 two-digit codes; legs: `T3`) | `MODP_H6`/`H7`/`H12`; legs: `MOYEN` |
| Declared duration | `D9` (minutes; = arrival `D8` − departure `D4`, ori `D8C`) | `DUREE` (minutes; `ORHOR`/`DESTHOR` HHMM) |
| Distance | `D11` crow-fly m, `D12` network m (computed, see below) | `DPORTEE` crow-fly km only; **no network distance** |
| Departure time | `D4` (HHMM) | `ORHOR` (HHMM) |
| Escort / accompaniment | `D2B`/`D5B` "motif de la personne accompagnée"; motive codes 61–64 | escort motives inside `ORMOT`/`DESTMOT`; `NBCO_1`/`NBCO_2` accompanying counts |
| School holidays flag | **absent** (derive from the calendar) | **absent** (derive from the calendar) |

**EMC² distances are computed, not declared.** Per the
`Note_calcul_distances` (verified for Aix-Marseille): crow-fly distance
(`D11`, ori `DOIB`) plus a network distance (`D12`, ori `DIST`, and
within-perimeter `DISP`) computed afterwards in TransCad on a BDTOPO
network, between fine-zone centroids (building-weighted barycentres),
peak or off-peak speeds chosen by the trip's departure hour; walk legs
carry their own distances (`TDMO`/`TDMD`). This matches EMP 2019's
imputed-distance logic better than ENTD 2008's declared distances, but
the method (zone centroids) differs from both.

## Differences from the Cerema standard

- The 13 EMC² surveys all follow standard V16 (same `std_*` schemas,
  same dictionary file); original tables differ by survey (extra local
  questions, e.g. Aix-Marseille's opinion table).
- The **EGT does not use the Cerema standard tables or names** (IDFM
  variable set, 7 tables; no `std_*` files, no ZF/DTIR zoning, no
  standard weights). It is nonetheless a previous-day, weekday,
  all-members-5+ (CAPI) trip survey, so the same unit of analysis can
  be built.
- EGT extras absent from EMC²: household income, exact coordinates
  (rounded), per-vehicle/bike tables, 7-day activity and remote-work
  questions.
- EMC² extras absent from EGT: network distances, legs with walk
  distances (EGT legs `04_Trajet` describe PT legs, car/bike legs with
  stations), fine-zone geometry.

## Proposed mapping to the step-11 variables

- **Unit:** described weekday person-days: EMC² `std_pers` with
  `PENQ = 1`; EGT `02_Individu` with `ENQ = 1`. Day weight: EMC² person
  weight (`COEP`, to confirm against `COE1` in the V16 dictionary); EGT
  `POIDSI`.
- **Households:** EMC² `ECH` × `ZFM` (sampling id within survey; the
  bootstrap resamples households within each survey); EGT `IDCEREMA`.
- **Population categories:** EMC² `P7` → employed (1–2), children 6–17
  (scolaire codes, age 6–17), unemployed, retired, other inactive;
  EGT `OCCP` equivalently. Age bands from `P4`/`AGE`, sex `P2`/`SEXE`.
- **Residence and density:** EMC² fine zone → INSEE commune via the
  `ZF` SIG table → INSEE density grid; EGT `RESINSEE` → density grid;
  Île-de-France flag: constant 0 for the 13 EMC² territories, 1 for the
  EGT.
- **Cars (0/1/2+):** EMC² `std_men` vehicle count; EGT `NB_VD`.
- **Income quintiles:** EGT only, from `REVENU` brackets (bracket
  midpoints / consumption units from household composition, as for
  ENTD 2008); impossible for EMC².
- **Trips, needs scope and modes:** EMC² `std_depl` motives
  `D2A`/`D5A` mapped to the harmonised motive groups (extend the step-12
  A2 crosswalk with the V16 codes); mode `MODP` → walk / bike / car
  driver / car passenger / urban PT / train / other; duration `D9`;
  distance `D12` (network) with `D11` as the crow-fly check; local
  scope: trips within 80 km of home as in step 11. EGT: motives
  `ORMOT`/`DESTMOT`, modes `MODP_H12` → the same groups (car driver vs
  passenger via trip-leg `UVP`/`VPASS_COVOIT`), duration `DUREE`.
- **Speed-plausibility correction:** EMC² can reuse step 11's rule with
  `D12`/`D9`. EGT has only crow-fly `DPORTEE`: the correction must be
  re-derived for crow-fly distances or skipped (flag the choice).

### Blockers

1. **No household income in EMC²**: income-quintile analyses are
   impossible outside Île-de-France.
2. **Standard V16 dictionary unread**: `Dico_Dessin_StandardV16_
   Corrige.xls` (old `.xls`) is not readable with the project's current
   toolchain (DuckDB spatial/GDAL lacks the XLS driver; no xlrd). The
   `COE1` vs `COEP` definition and exact `P7`/`MODP`/motive code labels
   must be confirmed from it (one manual export to CSV/XLSX, or add
   `xlrd` as a dev dependency).
3. **EGT distances are crow-fly only** (`DPORTEE`), so the step-11
   speed correction and the distance decompositions need an EGT-specific
   convention.
4. **No described days under lockdowns/curfews** anywhere: COVID-period
   contrasts reduce to before vs between lockdowns (Aix-Marseille,
   Grenoble, Vendée), before vs after restrictions (Loire Sud), and
   2019-like vs post-2021 across surveys.
5. **Sables d'Olonne SIG has `.dbf` without `.shp`**: the fine-zone →
   commune attribute join still works, but there is no geometry.
6. **EGT CATI households** interview a single Kish-drawn member:
   household-level composition effects need CAPI-only or weight checks.
7. **Territorial coverage**: EMC² perimeters are survey-specific (not
   national); any pooling with ENTD/EMP must treat them as separate
   strata with their own weights.
