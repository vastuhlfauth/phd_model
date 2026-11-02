"""A tiny synthetic EMP 2019 archive, covering every ``mode_group`` branch
of ``mobgrid.budget.emp2019.build_trip_legs`` (walk, cycle, car driver,
car passenger household/carpool, urban PT, train, other) and both a
single-mode and a multimodal day; no network or ``data/raw`` access (see
``.github/instructions/tests.instructions.md``).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

#: K_DEPLOC columns actually read by ``emp2019.build_trips_norm``. Every
#: row below uses the same STATUTCOM_UU/MTEMPSMAP/MTPSATTENT values
#: (section 9.9's density proxy and declared walk/wait minutes are not
#: exercised by these mode-classification tests; `test_entd2008.py` and
#: the density-proxy tests cover them directly).
_K_DEPLOC_HEADER = (
    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,mobloc,MORIDOM,"
    "DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,DENSITECOM_ORI,DENSITECOM_DES,"
    "MMOTIFDES,MOT_SEQ_COMPL,STATUTCOM_UU_ORI,STATUTCOM_UU_DES,MTEMPSMAP,"
    "MTPSATTENT"
)
_UU = "C,C,5,2"  # STATUTCOM_UU_ORI, STATUTCOM_UU_DES, MTEMPSMAP, MTPSATTENT

# One trip per mode_group branch (ident_ind 1-8, single trip each, density
# 1="dense"), plus a two-trip multimodal day (ident_ind 9: car then metro)
# and a tenth respondent (ident_ind 10) with no trip at all. ident_ind 7's
# 120 km trip and a second, short train trip (ident_ind 11) both cover
# "train" (the short/long split is merged, step 11 round 8). ident_ind 1's
# walk is a leisure loop (MMOTIFDES 7.7, "se promener sans destination
# precise"); every other trip is a generic purpose (1.1, "retour au
# domicile"). ident_ind 2's cycle trip has MOT_SEQ_COMPL 7.6 ("sport"),
# covering the motive decomposition's needs-excluded rollup (round 8: this
# trip is also excluded from the main, needs-only-scoped day_summary, so
# ident_ind 2 has no day_mode_group='cycle' row there -- by design).
# ident_ind 12 (walk) and 13 (cycle) have a needs-only-scoped purpose
# (9.1), so v0/P0 calibration (``daily_energy.calibrate_v0_kmh``/
# ``calibrate_p0``, needs-only scoped like every other step 11 query)
# has at least one trip of each mode to calibrate from.
_K_DEPLOC_ROWS = [
    f"D1,M1,1,1,100.0,1,1,1,20,1.5,NA,NA,1.1,1,1,7.7,7.7,{_UU}",  # walk (loop trip)
    f"D2,M2,2,1,100.0,1,1,1,15,3.0,NA,NA,2.1,1,1,1.1,7.6,{_UU}",  # cycle (sport)
    f"D3,M3,3,1,100.0,1,1,1,25,5.0,NA,NA,3.1,1,1,1.1,9.1,{_UU}",  # car_driver
    # car_passenger_household
    f"D4,M4,4,1,100.0,1,1,1,25,5.0,2,0,3.2,1,1,1.1,9.1,{_UU}",
    # car_passenger_carpool
    f"D5,M5,5,1,100.0,1,1,1,25,5.0,0,3,3.2,1,1,1.1,9.1,{_UU}",
    f"D6,M6,6,1,100.0,1,1,1,30,4.0,NA,NA,5.7,2,2,1.1,9.1,{_UU}",  # urban_pt (metro)
    # train (TGV, 120 km)
    f"D7,M7,7,1,100.0,1,0,1,90,120.0,NA,NA,6.1,3,3,1.1,9.1,{_UU}",
    f"D8,M8,8,1,100.0,1,1,1,20,2.0,NA,NA,8.1,1,1,1.1,9.1,{_UU}",  # other (boat)
    # multimodal day, leg 1 (car)
    f"D9,M9,9,1,100.0,1,1,1,20,3.0,NA,NA,3.1,1,1,1.1,9.1,{_UU}",
    # multimodal day, leg 2 (metro)
    f"D10,M9,9,2,100.0,1,1,0,30,4.0,NA,NA,5.7,2,2,1.1,9.1,{_UU}",
    # train (TER, 20 km)
    f"D11,M11,11,1,100.0,1,1,1,30,20.0,NA,NA,5.9,2,2,1.1,9.1,{_UU}",
    f"D12,M12,12,1,100.0,1,1,1,20,1.5,NA,NA,1.1,1,1,9.1,9.1,{_UU}",  # walk, needs-only
    f"D13,M13,13,1,100.0,1,1,1,15,3.0,NA,NA,2.1,1,1,9.1,9.1,{_UU}",  # cycle, needs-only
]

_TCM_IND_KISH_HEADER = "IDENT_IND;AGE;AGE6;SITUA"
_TCM_IND_KISH_ROWS = [
    "1;30;30;1",
    "2;40;40;1",
    "3;35;30;1",
    "4;36;30;1",
    "5;37;30;1",
    "6;45;40;1",
    "7;50;50;5",
    "8;60;60;5",
    "9;10;00;",  # child, blank SITUA
    "10;70;60;5",  # a tenth respondent with no trip at all
    "11;25;15;3",  # student, folds into other_inactive (section 6.1)
    "12;33;30;1",
    "13;34;30;1",
]

#: `IDENT_MEN`/`MDATE_jour`/`MDATE_delai`/`IMMODEP_A`-`G` (section 9.9
#: point 2's per-person budget): every respondent has no interview date
#: (blank `MDATE_jour`/`MDATE_delai`, the fixed 5 weekday/1 Saturday/1
#: Sunday fallback split), immobile on every offset for ident_ind 10
#: (the non-traveller) and mobile for everyone else.
_K_INDIVIDU_HEADER = (
    "IDENT_IND;IDENT_MEN;pond_indC;MIMMOSEM;MDATE_jour;MDATE_delai;"
    "IMMODEP_A;IMMODEP_B;IMMODEP_C;IMMODEP_D;IMMODEP_E;IMMODEP_F;IMMODEP_G"
)
_K_INDIVIDU_ROWS = [
    f"{i};M{i};100.0;{'1' if i == 10 else '2'};;;"
    f"{'1;1;1;1;1;1;1' if i == 10 else '0;0;0;0;0;0;0'}"
    for i in range(1, 14)
]

_Q_MENAGE_HEADER = "IDENT_MEN;pond_menC"
_Q_MENAGE_ROWS = [f"M{i};100.0" for i in range(1, 14)]

#: TCM_MEN's `TUU2017_RES` (section 9.9's density proxy) and
#: `STATUTCOM_UU_RES`/`DENSITECOM_RES` (the residence density itself,
#: 27 October 2026 decision: `home_density` reads this, not a trip
#: end's), added to EMP 2019's loaded tables; '7'/'C'/'1' for every
#: household, consistent with every trip's 'C' (city centre) status
#: above giving 'dense' under the proxy, and '1' being 'dense' under
#: the grid. Comma-quoted, like the real `tcm_men_public_V3.csv`
#: (unlike every other EMP 2019 table besides `k_deploc`, which is
#: semicolon-separated).
#: `decile_rev_uc` (income variables, section 9.9): varied 1-10 across
#: the 13 households, so the weighted-quintile computation
#: (``emp2019.build_respondent_income``) has a real spread to cut.
_TCM_MEN_HEADER = (
    '"ident_men","TUU2017_RES","STATUTCOM_UU_RES","DENSITECOM_RES","decile_rev_uc"'
)
_TCM_MEN_ROWS = [f'"M{i}","7","C","1","{((i - 1) % 10) + 1}"' for i in range(1, 14)]


def write_synthetic_emp_zip(path: Path) -> None:
    """Write a tiny EMP 2019 archive with the six public tables'
    zip member names, to ``path``."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "5. k_deploc_public_V4.csv",
            "\n".join([_K_DEPLOC_HEADER, *_K_DEPLOC_ROWS]),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join([_TCM_IND_KISH_HEADER, *_TCM_IND_KISH_ROWS]),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join([_K_INDIVIDU_HEADER, *_K_INDIVIDU_ROWS]),
        )
        archive.writestr(
            "tcm_ind_public_V3.csv",
            "ident_ind;ident_men\n" + "\n".join(f"{i};M{i}" for i in range(1, 14)),
        )
        archive.writestr(
            "q_menage_public_V3.csv", "\n".join([_Q_MENAGE_HEADER, *_Q_MENAGE_ROWS])
        )
        archive.writestr(
            "tcm_men_public_V3.csv", "\n".join([_TCM_MEN_HEADER, *_TCM_MEN_ROWS])
        )


@pytest.fixture
def synthetic_emp_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "emp2019-data.zip"
    write_synthetic_emp_zip(zip_path)
    return zip_path


#: A tiny synthetic ENTD 2008 raw directory, covering the mode and
#: purpose conversion tables, the sequence-purpose rule (return trips
#: take the outward trip's purpose, via `V2_MMOTIFORI`), `POIDS_JOUR > 0`
#: filtering and the density proxy (`docs/data/entd2008.md`).
_ENTD_K_DEPLOC_HEADER = (
    "IDENT_DEP;IDENT_IND;IDENT_MEN;IDENT_JOUR;POIDS_JOUR;V2_TYPJOUR;V2_DLOCAL;"
    "NODEP;V2_MORIDOM;v2_mduree;V2_DUREE;distcor;V2_MDISTTOT;V2_MACCOMPM;"
    "V2_MACCOMPHM;V2_MTP;V2_MMOTIFDES;V2_MMOTIFORI;v2_moricom_UU2010;"
    "v2_mdescom_UU2010;V2_MTEMPSMAP;V2_MTPSATTENT"
)
_ENTD_K_DEPLOC_ROWS = [
    # Respondent 1, weekday, two trips: out to work (walk), back home
    # (walk) -- the return trip's raw purpose is 1.1 ("retour au
    # domicile"), converted to 1.1 (an excluded-return code), so its
    # `motive` is overridden by its own `V2_MMOTIFORI` (9.91, "travail
    # lieu habituel", converted to 9.1): the sequence-purpose rule.
    # Declared duration/distance fall back to V2_DUREE/V2_MDISTTOT
    # (v2_mduree/distcor blank).
    "D1;1;M1;J1;100;1;1;1;1;;20;;1.5;;;1.10;9.91;;C;C;5;2",
    "D2;1;M1;J1;100;1;1;2;2;;20;;1.5;;;1.10;1.1;9.91;C;C;5;2",
    # Respondent 2, Saturday, one cycling trip, sport (7.76 -> 7.6,
    # excluded from the needs-only scope); distcor/v2_mduree filled
    # (different from the V2_DUREE/V2_MDISTTOT fallback, for the
    # fill-rate/mean-change report).
    "D3;2;M2;J2;200;2;1;1;1;14;15;2.8;3.0;;;2.20;7.76;;C;C;7;0",
    # Respondent 3: POIDS_JOUR = 0 (weekday trip outside the reference
    # day, `docs/data/entd2008.md`'s "Keys, days and weights"): dropped.
    "D4;3;M3;J3;0;1;1;1;1;;25;;5.0;;;3.30;9.91;;C;C;7;0",
    # Respondent 4: car passenger, carpool (MACCOMPHM > 0, MACCOMPM = 0).
    "D5;4;M4;J4;150;1;1;1;1;;25;;5.0;0;3;3.32;9.91;;C;C;7;0",
    # Respondent 5: urban bus, rural trip end (uu_status 'R' -> always
    # 'very_sparse' under the proxy, whatever the residence size).
    "D6;5;M5;J5;120;1;1;1;1;;30;;4.0;;;5.50;9.91;;R;R;10;5",
    # Respondent 6: TGV, suburb trip end, medium residence size (tuu_res
    # '5' -> 'intermediate' under the proxy).
    "D7;6;M6;J6;180;1;0;1;1;;90;;120.0;;;6.60;9.91;;B;B;15;5",
    # Respondent 8: a second, needs-only-scoped cycling trip (purpose
    # 9.91, unlike respondent 2's sport trip), so P0 calibration
    # (``daily_energy.calibrate_p0``, needs-only scoped) has a cycle
    # trip to calibrate from.
    "D8;8;M8;J8;100;1;1;1;1;;15;;3.0;;;2.20;9.91;;C;C;7;0",
]

_ENTD_K_INDIVIDU_HEADER = "IDENT_IND;IDENT_MEN;PONDKI;V2_MOBILREF"
_ENTD_K_INDIVIDU_ROWS = [
    "1;M1;100;1",
    "2;M2;200;1",
    "3;M3;100;1",
    "4;M4;150;1",
    "5;M5;120;1",
    "6;M6;180;1",
    # Respondent 7: no k_deploc row at all, `V2_MOBILREF = 0` (not
    # mobile on the reference weekday): a non-traveller.
    "7;M7;140;0",
    "8;M8;100;1",
]

_ENTD_Q_TCM_INDIVIDU_HEADER = "IDENT_IND;AGE;AGE6;SITUA"
_ENTD_Q_TCM_INDIVIDU_ROWS = [
    "1;35;30;1",
    "2;40;40;1",
    "3;45;40;1",
    "4;50;50;5",
    "5;30;30;1",
    "6;33;30;1",
    "7;60;60;5",
    "8;31;30;1",
]

#: `TrancheRevenuMensuel`/`NBUC` (income variables, section 9.9): varied
#: across the 8 households, so ``entd2008.build_respondent_income`` has
#: a real bracket-midpoint/consumption-unit spread to quintile; M7 (the
#: non-traveller) gets a blank bracket, covering the missing/refused
#: ('unknown') path.
_ENTD_Q_TCM_MENAGE_HEADER = "IDENT_MEN;TU99;numcom_UUCat;TrancheRevenuMensuel;NBUC"
_ENTD_Q_TCM_MENAGE_ROWS = [
    "M1;7;ville centre;Moins de 400 €;1.0",
    "M2;7;ville centre;De 800 € à moins de 1 000 €;1.5",
    "M3;7;ville centre;De 1 500 € à moins de 1 800 €;2.0",
    "M4;7;ville centre;De 2 500 € à moins de 3 000 €;2.5",
    "M5;0;commune rurale;De 3 000 € à moins de 4 000 €;1.5",
    "M6;5;banlieue;De 4 000 € à moins de 6 000 €;2.0",
    "M7;7;ville centre;;1.0",
    "M8;7;ville centre;10 000 € ou plus;1.0",
]


def write_synthetic_entd2008_csvs(raw_dir: Path) -> None:
    """Write the four tiny ENTD 2008 public CSVs (cp1252, `;`-delimited,
    as the real archive) to ``raw_dir``."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "k_deploc.csv": [_ENTD_K_DEPLOC_HEADER, *_ENTD_K_DEPLOC_ROWS],
        "k_individu.csv": [_ENTD_K_INDIVIDU_HEADER, *_ENTD_K_INDIVIDU_ROWS],
        "q_tcm_individu.csv": [
            _ENTD_Q_TCM_INDIVIDU_HEADER,
            *_ENTD_Q_TCM_INDIVIDU_ROWS,
        ],
        "q_tcm_menage.csv": [_ENTD_Q_TCM_MENAGE_HEADER, *_ENTD_Q_TCM_MENAGE_ROWS],
    }
    for name, lines in files.items():
        (raw_dir / name).write_text("\n".join(lines), encoding="cp1252")


@pytest.fixture
def synthetic_entd2008_raw_dir(tmp_path: Path) -> Path:
    raw_dir = tmp_path / "entd2008_raw"
    write_synthetic_entd2008_csvs(raw_dir)
    return raw_dir
