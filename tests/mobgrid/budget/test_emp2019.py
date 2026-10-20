"""Unit tests for the EMP 2019 trip-leg reconstruction (section 9.9, step 11).

Uses a tiny synthetic archive (``synthetic_emp_zip``, ``conftest.py``), not
the real EMP 2019 data (isolated, no ``data/raw`` access).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import duckdb
import pytest
from mobgrid.budget import emp2019
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"


@pytest.fixture
def trip_legs(tmp_path: Path, synthetic_emp_zip: Path) -> duckdb.DuckDBPyRelation:
    config = load_energy_config(CONFIG_PATH)
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(synthetic_emp_zip, tmp_path / "csv")
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)
    return con


def _mode_group(con: duckdb.DuckDBPyConnection, ident_ind: int) -> str:
    return con.sql(
        f"SELECT mode_group FROM trip_legs WHERE ident_ind = {ident_ind} "
        "ORDER BY num_dep LIMIT 1"
    ).fetchone()[0]


def test_every_mode_group_is_classified(trip_legs: duckdb.DuckDBPyConnection) -> None:
    expected = {
        1: "walk",
        2: "cycle",
        3: "car_driver",
        4: "car_passenger_household",
        5: "car_passenger_carpool",
        6: "urban_pt",
        7: "train_long",
        8: "other",
        11: "train_short",
    }
    for ident_ind, mode_group in expected.items():
        assert _mode_group(trip_legs, ident_ind) == mode_group


def test_classified_trips_have_positive_energy_in_both_rate_sets(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    rows = trip_legs.sql(
        "SELECT ident_ind, energy_kh_kj, energy_cp_kj FROM trip_legs "
        "WHERE mode_group != 'other'"
    ).fetchall()
    assert len(rows) == 10  # 9 single-trip persons (except 'other') + 1 multimodal leg
    for _, energy_kh, energy_cp in rows:
        assert energy_kh > 0
        assert energy_cp > 0


def test_other_mode_group_has_no_energy_formula(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    row = trip_legs.sql(
        "SELECT energy_kh_kj, energy_cp_kj FROM trip_legs WHERE ident_ind = 8"
    ).fetchone()
    assert row == (None, None)


def test_walking_and_cycling_calibrate_v0_and_p0(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    walk_speed, cycle_power = trip_legs.sql(
        "SELECT "
        "(SELECT implied_speed_kmh FROM trip_legs WHERE ident_ind = 1), "
        "(SELECT p0_calibrated_w FROM trip_legs WHERE ident_ind = 2)"
    ).fetchone()
    # ident_ind 1: 1.5 km in 20 min = 4.5 km/h.
    assert walk_speed == pytest.approx(4.5, rel=1e-6)
    assert cycle_power > 0


def test_carpool_is_distinguished_from_household_passenger_by_companions(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    # Same duration/distance/density for ident_ind 4 (household) and 5
    # (carpool); only the companions differ, so their energy must differ.
    household_kh, carpool_kh = trip_legs.sql(
        "SELECT "
        "(SELECT energy_kh_kj FROM trip_legs WHERE ident_ind = 4), "
        "(SELECT energy_kh_kj FROM trip_legs WHERE ident_ind = 5)"
    ).fetchone()
    assert household_kh != pytest.approx(carpool_kh)


def test_motive_column_reads_mot_seq_compl(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    # ident_ind 2's cycle trip has MOT_SEQ_COMPL 7.6 ("sport").
    motive = trip_legs.sql(
        "SELECT motive FROM trip_legs WHERE ident_ind = 2"
    ).fetchone()[0]
    assert motive == pytest.approx(7.6)


def test_motive_is_null_for_the_refusal_code(tmp_path: Path) -> None:
    """A tiny, two-row k_deploc (so DuckDB's CSV type inference sees more
    than one value per column, avoiding single-row inference quirks
    unrelated to this test): one trip with MOT_SEQ_COMPL 9999 (the
    refusal code), the other with a normal motive, confirming only the
    former reads back as NULL."""
    config = load_energy_config(CONFIG_PATH)
    zip_path = tmp_path / "emp2019-data.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "5. k_deploc_public_V4.csv",
            "\n".join([
                "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,"
                "mobloc,MORIDOM,DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,"
                "DENSITECOM_ORI,DENSITECOM_DES,MMOTIFDES,MOT_SEQ_COMPL",
                "D1,M1,1,1,100.0,1,1,1,20,1.5,0,0,1.1,1,1,1.1,9999",
                "D2,M2,2,1,100.0,1,1,1,20,1.5,0,0,1.1,1,1,1.1,9.1",
            ]),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join(["IDENT_IND;AGE;AGE6;SITUA", "1;30;30;1", "2;30;30;1"]),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join([
                "IDENT_IND;pond_indC;MIMMOSEM", "1;100.0;2", "2;100.0;2",
            ]),
        )
        archive.writestr(
            "tcm_ind_public_V3.csv", "ident_ind;ident_men\n1;M1\n2;M2"
        )
        archive.writestr(
            "q_menage_public_V3.csv",
            "\n".join(["IDENT_MEN;pond_menC", "M1;100.0", "M2;100.0"]),
        )
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path, tmp_path / "csv2")
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)
    motive = con.sql("SELECT motive FROM trip_legs WHERE ident_ind = 1").fetchone()[0]
    assert motive is None
