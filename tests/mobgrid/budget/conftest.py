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

#: K_DEPLOC columns actually read by ``emp2019.build_trip_legs``.
_K_DEPLOC_HEADER = (
    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,mobloc,MORIDOM,"
    "DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,DENSITECOM_ORI,DENSITECOM_DES"
)

# One trip per mode_group branch (ident_ind 1-8, single trip each, density
# 1="dense"), plus a two-trip multimodal day (ident_ind 9: car then metro)
# and a tenth respondent (ident_ind 10) with no trip at all. ident_ind 7's
# 120 km trip is "train_long" (>= 80 km); a second, short train trip
# (ident_ind 11) covers "train_short".
_K_DEPLOC_ROWS = [
    "D1,M1,1,1,100.0,1,1,1,20,1.5,NA,NA,1.1,1,1",  # walk
    "D2,M2,2,1,100.0,1,1,1,15,3.0,NA,NA,2.1,1,1",  # cycle
    "D3,M3,3,1,100.0,1,1,1,25,5.0,NA,NA,3.1,1,1",  # car_driver
    "D4,M4,4,1,100.0,1,1,1,25,5.0,2,0,3.2,1,1",  # car_passenger_household
    "D5,M5,5,1,100.0,1,1,1,25,5.0,0,3,3.2,1,1",  # car_passenger_carpool
    "D6,M6,6,1,100.0,1,1,1,30,4.0,NA,NA,5.7,2,2",  # urban_pt (metro)
    "D7,M7,7,1,100.0,1,0,1,90,120.0,NA,NA,6.1,3,3",  # train_long (TGV, 120 km)
    "D8,M8,8,1,100.0,1,1,1,20,2.0,NA,NA,8.1,1,1",  # other (boat)
    "D9,M9,9,1,100.0,1,1,1,20,3.0,NA,NA,3.1,1,1",  # multimodal day, leg 1 (car)
    "D10,M9,9,2,100.0,1,1,0,30,4.0,NA,NA,5.7,2,2",  # multimodal day, leg 2 (metro)
    "D11,M11,11,1,100.0,1,1,1,30,20.0,NA,NA,5.9,2,2",  # train_short (TER, 20 km)
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
]

_K_INDIVIDU_HEADER = "IDENT_IND;pond_indC;MIMMOSEM"
_K_INDIVIDU_ROWS = [
    f"{i};100.0;{'1' if i == 10 else '2'}" for i in range(1, 12)
]

_Q_MENAGE_HEADER = "IDENT_MEN;pond_menC"
_Q_MENAGE_ROWS = [f"M{i};100.0" for i in range(1, 12)]


def write_synthetic_emp_zip(path: Path) -> None:
    """Write a tiny EMP 2019 archive with the five public tables'
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
            "ident_ind;ident_men\n"
            + "\n".join(f"{i};M{i}" for i in range(1, 12)),
        )
        archive.writestr(
            "q_menage_public_V3.csv", "\n".join([_Q_MENAGE_HEADER, *_Q_MENAGE_ROWS])
        )


@pytest.fixture
def synthetic_emp_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "emp2019-data.zip"
    write_synthetic_emp_zip(zip_path)
    return zip_path
