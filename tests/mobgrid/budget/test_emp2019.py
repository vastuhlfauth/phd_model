"""Unit tests for the EMP 2019 trip-leg reconstruction (section 9.9, step 11).

Uses a tiny synthetic archive (``synthetic_emp_zip``, ``conftest.py``), not
the real EMP 2019 data (isolated, no ``data/raw`` access).
"""

from __future__ import annotations

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
        7: "train",
        8: "other",
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
    assert len(rows) == 9  # 8 single-trip persons (except 'other') + 1 multimodal leg
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
