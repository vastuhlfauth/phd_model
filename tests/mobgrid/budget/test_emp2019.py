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
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    activity_rate_kj_per_min,
    load_energy_config,
)

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
        11: "train",
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
    assert len(rows) == 12  # 11 single-trip persons (except 'other') + 1 multimodal leg
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


def test_income_quintile_is_ordered_by_decile_rev_uc(
    trip_legs: duckdb.DuckDBPyConnection,
) -> None:
    """EMP 2019 publishes no raw income bracket: `TCM_MEN.decile_rev_uc`
    is used directly as the continuous rank fed to
    `trip_legs.build_income_quintile_table` (section 9.9's "Income
    variables"). The synthetic fixture's `decile_rev_uc` runs 1..10
    across its 13 households (`conftest.py`): the lowest decile
    (ident_ind 1, M1) must rank at or below a higher decile (ident_ind
    8, M8, decile 8; ident_ind 10/M10 has the highest decile, 10, but no
    trip at all, so no `trip_legs` row to query)."""
    rows = dict(
        trip_legs.sql(
            "SELECT ident_ind, income_quintile FROM trip_legs "
            "WHERE ident_ind IN (1, 8)"
        ).fetchall()
    )
    order = {"q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5}
    assert rows[1] in order
    assert rows[8] in order
    assert order[rows[1]] <= order[rows[8]]


def test_missing_income_breakdown_distinguishes_no_match_from_null_decile() -> None:
    """28 October 2026's missing-income audit: a respondent whose
    household has no `TCM_MEN` row at all is a different failure mode
    (`n_no_household_match`) from one whose household is matched but
    has a blank `decile_rev_uc` (`n_null_decile`) -- this project's code
    does nothing beyond the plain lookup, so there is no third,
    code-side failure mode for EMP 2019."""
    con = duckdb.connect()
    con.sql("CREATE TABLE k_individu (IDENT_IND VARCHAR, pond_indC DOUBLE)")
    con.sql(
        "INSERT INTO k_individu VALUES "
        "('1', 100.0), ('2', 100.0), ('3', 100.0)"
    )
    con.sql("CREATE TABLE tcm_ind (ident_ind VARCHAR, ident_men VARCHAR)")
    con.sql(
        "INSERT INTO tcm_ind VALUES ('1', 'M1'), ('2', 'M2'), ('3', 'M3')"
    )
    con.sql("CREATE TABLE tcm_men (ident_men VARCHAR, decile_rev_uc INTEGER)")
    # M1: normal; M2: present but blank decile; M3: no row at all.
    con.sql("INSERT INTO tcm_men VALUES ('M1', 5), ('M2', NULL)")

    breakdown = emp2019.missing_income_breakdown(con)
    assert breakdown["n_total"] == 3
    assert breakdown["n_no_household_match"] == 1
    assert breakdown["n_null_decile"] == 1


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
            "\n".join(
                [
                    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,"
                    "mobloc,MORIDOM,DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,"
                    "DENSITECOM_ORI,DENSITECOM_DES,MMOTIFDES,MOT_SEQ_COMPL,"
                    "STATUTCOM_UU_ORI,STATUTCOM_UU_DES,MTEMPSMAP,MTPSATTENT",
                    "D1,M1,1,1,100.0,1,1,1,20,1.5,0,0,1.1,1,1,1.1,9999,C,C,5,2",
                    "D2,M2,2,1,100.0,1,1,1,20,1.5,0,0,1.1,1,1,1.1,9.1,C,C,5,2",
                ]
            ),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join(["IDENT_IND;AGE;AGE6;SITUA", "1;30;30;1", "2;30;30;1"]),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join(
                [
                    "IDENT_IND;pond_indC;MIMMOSEM",
                    "1;100.0;2",
                    "2;100.0;2",
                ]
            ),
        )
        archive.writestr("tcm_ind_public_V3.csv", "ident_ind;ident_men\n1;M1\n2;M2")
        archive.writestr(
            "q_menage_public_V3.csv",
            "\n".join(["IDENT_MEN;pond_menC", "M1;100.0", "M2;100.0"]),
        )
        archive.writestr(
            "tcm_men_public_V3.csv",
            "\n".join(
                [
                    '"ident_men","TUU2017_RES","STATUTCOM_UU_RES","DENSITECOM_RES","decile_rev_uc"',
                    '"M1","7","C","1","5"',
                    '"M2","7","C","1","5"',
                ]
            ),
        )
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path, tmp_path / "csv2")
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)
    motive = con.sql("SELECT motive FROM trip_legs WHERE ident_ind = 1").fetchone()[0]
    assert motive is None


def test_implausibly_fast_cycle_trip_has_its_distance_corrected(
    tmp_path: Path,
) -> None:
    """Round 9 fix: a flagged (> 35 km/h) cycling trip's declared
    distance is corrected like walk's and car's, not left as-is --
    cycling's "stops" energy sub-term otherwise still multiplies by the
    raw, implausible distance and by the resulting (also implausible)
    ride speed squared (section 9.7), inflating a single day's energy
    by orders of magnitude (an ENTD 2008 real-data case: a declared
    376 km/65 min cycling leg produced ~1.3M kJ for that one day).

    Two respondents cycle at a plausible 12 km/h (median); a third's
    declared distance implies 300 km/h, above `CYCLE_SPEED_UPPER_KMH`
    (35): its corrected distance must equal its declared duration times
    that 12 km/h median, not its declared (implausible) distance, and
    its energy must stay in the same order of magnitude as the two
    plausible trips, not orders of magnitude higher.
    """
    config = load_energy_config(CONFIG_PATH)
    zip_path = tmp_path / "emp2019-data.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "5. k_deploc_public_V4.csv",
            "\n".join(
                [
                    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,"
                    "mobloc,MORIDOM,DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,"
                    "DENSITECOM_ORI,DENSITECOM_DES,MMOTIFDES,MOT_SEQ_COMPL,"
                    "STATUTCOM_UU_ORI,STATUTCOM_UU_DES,MTEMPSMAP,MTPSATTENT",
                    # 4 km in 20 min = 12 km/h, not flagged (two respondents,
                    # for a clean median).
                    "D1,M1,1,1,100.0,1,1,1,20,4.0,0,0,2.1,1,1,1.1,9.1,C,C,5,2",
                    "D2,M2,2,1,100.0,1,1,1,20,4.0,0,0,2.1,1,1,1.1,9.1,C,C,5,2",
                    # 50 km in 10 min = 300 km/h, flagged (> 35 km/h).
                    "D3,M3,3,1,100.0,1,1,1,10,50.0,0,0,2.1,1,1,1.1,9.1,C,C,5,2",
                ]
            ),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join(
                [
                    "IDENT_IND;AGE;AGE6;SITUA",
                    "1;30;30;1",
                    "2;30;30;1",
                    "3;30;30;1",
                ]
            ),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join(
                [
                    "IDENT_IND;pond_indC;MIMMOSEM",
                    "1;100.0;2",
                    "2;100.0;2",
                    "3;100.0;2",
                ]
            ),
        )
        archive.writestr(
            "tcm_ind_public_V3.csv", "ident_ind;ident_men\n1;M1\n2;M2\n3;M3"
        )
        archive.writestr(
            "q_menage_public_V3.csv",
            "\n".join(
                [
                    "IDENT_MEN;pond_menC",
                    "M1;100.0",
                    "M2;100.0",
                    "M3;100.0",
                ]
            ),
        )
        archive.writestr(
            "tcm_men_public_V3.csv",
            "\n".join(
                [
                    '"ident_men","TUU2017_RES","STATUTCOM_UU_RES","DENSITECOM_RES","decile_rev_uc"',
                    '"M1","7","C","1","5"',
                    '"M2","7","C","1","5"',
                    '"M3","7","C","1","5"',
                ]
            ),
        )
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path, tmp_path / "csv3")
    emp2019.register_views(con, csv_paths)
    emp2019.build_trip_legs(con, config)

    flagged, distance_km, energy_cp = con.sql(
        "SELECT speed_flagged_upper, distance_km, energy_cp_kj "
        "FROM trip_legs WHERE ident_ind = 3"
    ).fetchone()
    assert flagged is True
    assert distance_km == pytest.approx(10.0 / 60.0 * 12.0)

    plausible_energy = con.sql(
        "SELECT energy_cp_kj FROM trip_legs WHERE ident_ind = 1"
    ).fetchone()[0]
    assert energy_cp < plausible_energy * 10


def test_stop_energy_per_stop_is_the_same_regardless_of_declared_speed(
    tmp_path: Path,
) -> None:
    """22 October 2026 decision: the "stops" sub-term is now costed at
    the flat speed the rider holds at the calibrated P0, not at the
    trip's own (declared-distance/ride-time) speed. So, even though an
    implausibly-fast-declared trip's corrected distance (and so its
    number of stops) differs from a normal trip's, its energy *per
    stop* must be identical -- unlike before this fix, when a trip's own
    (possibly still-differing, post-correction) ride speed set a
    different, trip-specific kJ/stop.

    Respondent 1 cycles normally (4 km/20 min = 12 km/h, not flagged).
    Respondent 2's declared speed is implausible (50 km/10 min =
    300 km/h, above `CYCLE_SPEED_UPPER_KMH`): its distance is corrected
    to 10 min x the (12 km/h) median of the not-flagged trips = 2 km, a
    different distance (and stop count) from respondent 1's, but its
    stop energy per stop must still equal respondent 1's.
    """
    config = load_energy_config(CONFIG_PATH)
    zip_path = tmp_path / "emp2019-data.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "5. k_deploc_public_V4.csv",
            "\n".join(
                [
                    "IDENT_DEP,IDENT_MEN,IDENT_IND,num_dep,POND_JOUR,TYPEJOUR,"
                    "mobloc,MORIDOM,DUREE,MDISTTOT_fin,MACCOMPM,MACCOMPHM,mtp,"
                    "DENSITECOM_ORI,DENSITECOM_DES,MMOTIFDES,MOT_SEQ_COMPL,"
                    "STATUTCOM_UU_ORI,STATUTCOM_UU_DES,MTEMPSMAP,MTPSATTENT",
                    # 4 km in 20 min = 12 km/h, not flagged.
                    "D1,M1,1,1,100.0,1,1,1,20,4.0,0,0,2.1,1,1,1.1,9.1,C,C,5,2",
                    # 50 km in 10 min = 300 km/h, flagged (> 35 km/h).
                    "D2,M2,2,1,100.0,1,1,1,10,50.0,0,0,2.1,1,1,1.1,9.1,C,C,5,2",
                ]
            ),
        )
        archive.writestr(
            "tcm_ind_kish_public_V3.csv",
            "\n".join(["IDENT_IND;AGE;AGE6;SITUA", "1;30;30;1", "2;30;30;1"]),
        )
        archive.writestr(
            "k_individu_public_V3.csv",
            "\n".join(["IDENT_IND;pond_indC;MIMMOSEM", "1;100.0;2", "2;100.0;2"]),
        )
        archive.writestr("tcm_ind_public_V3.csv", "ident_ind;ident_men\n1;M1\n2;M2")
        archive.writestr(
            "q_menage_public_V3.csv",
            "\n".join(["IDENT_MEN;pond_menC", "M1;100.0", "M2;100.0"]),
        )
        archive.writestr(
            "tcm_men_public_V3.csv",
            "\n".join(
                [
                    '"ident_men","TUU2017_RES","STATUTCOM_UU_RES","DENSITECOM_RES","decile_rev_uc"',
                    '"M1","7","C","1","5"',
                    '"M2","7","C","1","5"',
                ]
            ),
        )
    con = duckdb.connect()
    csv_paths = emp2019.extract_tables(zip_path, tmp_path / "csv_stops")
    emp2019.register_views(con, csv_paths)
    # `terminal_legs='defaults'`: this test is about the stop term's
    # speed-independence, not the 27 October 2026 declared-legs decision
    # (both trips here share the same declared `MTEMPSMAP`, which would
    # pass just as well, but the hand-computed `kj_per_stop` below checks
    # against the fixed `get_park_total_min` default explicitly).
    emp2019.build_trip_legs(con, config, terminal_legs="defaults")

    rows = con.sql(
        "SELECT ident_ind, distance_km, bike_ride_time_for_energy_s, "
        "speed_flagged_upper, energy_kh_kj FROM trip_legs ORDER BY ident_ind"
    ).fetchall()
    (ident1, dist1, ride1, flagged1, kh1), (ident2, dist2, ride2, flagged2, kh2) = rows
    assert (flagged1, flagged2) == (False, True)
    # The two trips' corrected distances (and so stop counts) genuinely
    # differ: this is not a trivial, already-equal case.
    assert dist1 != pytest.approx(dist2)

    bike = config.bike
    mass = config.reference_mass_kg
    standing_kh = activity_rate_kj_per_min(
        config.activity_rates["standing_relaxed"], "kh", mass
    )
    unloaded_rate_kj_per_min = (
        bike.pedalling_unloaded_net_met * MET_MINUTE_KJ_PER_KG * mass
    )
    get_park_total_min = 2.0 * bike.get_park_min

    def kj_per_stop(distance_km: float, ride_s: float, energy_kh: float) -> float:
        ride_work_kj = (
            bike.power.p0_w / bike.gross_muscular_efficiency * ride_s / 1000.0
        )
        unloaded_kj = unloaded_rate_kj_per_min * ride_s / 60.0
        get_park_kj = standing_kh * get_park_total_min
        stops_kj = energy_kh - ride_work_kj - unloaded_kj - get_park_kj
        n_stops = bike.stops.stops_per_km * distance_km
        return stops_kj / n_stops

    assert kj_per_stop(dist1, ride1, kh1) == pytest.approx(
        kj_per_stop(dist2, ride2, kh2), rel=1e-6
    )


def _make_person_budget_con() -> duckdb.DuckDBPyConnection:
    """A tiny, hand-built `k_individu`/`tcm_ind_kish`/`tcm_ind`/`tcm_men`
    set (section 9.9 point 2's per-person budget): respondent 1
    (interviewed Monday, delai 0, offset-1 = yesterday = Sunday) is
    mobile on 5 of 7 described days; respondent 2 has no interview date
    ("stayed home all week") and is immobile on every offset."""
    con = duckdb.connect()
    con.sql("""
        CREATE TABLE k_individu (
            IDENT_IND VARCHAR, IDENT_MEN VARCHAR, pond_indC DOUBLE,
            MIMMOSEM INTEGER, MDATE_jour VARCHAR, MDATE_delai VARCHAR,
            IMMODEP_A DOUBLE, IMMODEP_B DOUBLE, IMMODEP_C DOUBLE,
            IMMODEP_D DOUBLE, IMMODEP_E DOUBLE, IMMODEP_F DOUBLE,
            IMMODEP_G DOUBLE
        )
    """)
    con.sql("""
        INSERT INTO k_individu VALUES
            ('1', 'M1', 100.0, 2, 'lundi', '0', 0, 0, 0, 0, 0, 1, 1),
            ('2', 'M2', 100.0, 1, NULL, NULL, 1, 1, 1, 1, 1, 1, 1)
    """)
    con.sql("""
        CREATE TABLE tcm_ind_kish (IDENT_IND VARCHAR, AGE INTEGER,
            AGE6 VARCHAR, SITUA VARCHAR)
    """)
    con.sql("""
        INSERT INTO tcm_ind_kish VALUES
            ('1', 30, '30', '1'), ('2', 60, '60', '5')
    """)
    con.sql("CREATE TABLE tcm_ind (ident_ind VARCHAR, ident_men VARCHAR)")
    con.sql("INSERT INTO tcm_ind VALUES ('1', 'M1'), ('2', 'M2')")
    con.sql("""
        CREATE TABLE tcm_men (ident_men VARCHAR, TUU2017_RES VARCHAR,
            STATUTCOM_UU_RES VARCHAR, DENSITECOM_RES INTEGER,
            decile_rev_uc INTEGER)
    """)
    con.sql("""
        INSERT INTO tcm_men VALUES
            ('M1', '7', 'C', 1, 2), ('M2', '0', 'H', 4, 9)
    """)
    return con


def test_population_category_by_ident_covers_non_travellers() -> None:
    con = _make_person_budget_con()
    result = emp2019.population_category_by_ident(con)
    assert result == {"1": "employed", "2": "retired"}


def test_residence_density_by_ident_grid_and_proxy() -> None:
    con = _make_person_budget_con()
    grid = emp2019.residence_density_by_ident(con, "grid")
    assert grid == {"1": "dense", "2": "very_sparse"}
    proxy = emp2019.residence_density_by_ident(con, "proxy")
    assert proxy == {"1": "dense", "2": "very_sparse"}


def test_person_day_type_rows_assigns_offsets_by_interview_date() -> None:
    """Respondent 1, interviewed Monday with 0 days' delay (so the
    interview itself is Monday, day index 0): offset 1 ("yesterday") is
    Sunday, offsets 2-6 are Saturday back to Tuesday, offset 7 is
    Monday. Respondent 2 (no interview date) uses the fixed 5/1/1
    fallback split."""
    con = _make_person_budget_con()
    rows = emp2019.person_day_type_rows(con)
    by_person = {}
    for ident_ind, _ident_men, _pond, day_type, immobile in rows:
        by_person.setdefault(ident_ind, []).append((day_type, immobile))
    # Respondent 1: offsets A-G = (0,0,0,0,0,1,1); offset 1 = Sunday,
    # offset 7 = Monday (both weekday-adjacent via the 7-day wraparound).
    day_types_1 = [day_type for day_type, _ in by_person["1"]]
    assert day_types_1.count("sunday") == 1
    assert day_types_1.count("saturday") == 1
    assert day_types_1.count("weekday") == 5
    # Respondent 2: no interview date, fixed 5 weekday/1 Saturday/1
    # Sunday split, every offset immobile.
    day_types_2 = [day_type for day_type, _ in by_person["2"]]
    assert day_types_2.count("weekday") == 5
    assert day_types_2.count("saturday") == 1
    assert day_types_2.count("sunday") == 1
    assert all(immobile == 1.0 for _, immobile in by_person["2"])
