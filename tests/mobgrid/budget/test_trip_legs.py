"""Unit tests for the shared trip-leg energy computation
(``mobgrid.budget.trip_legs``), survey-agnostic: section 9.9's density
proxy (the urban-unit-status x residence-size table of "Change between
2008 and 2019") and the 27 October 2026 declared-legs decision
(``terminal_legs``).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from mobgrid.budget import trip_legs
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"


@pytest.mark.parametrize(
    ("uu_status", "tuu_res", "expected"),
    [
        # City centre (C): sparse / intermediate / dense, by residence size.
        ("C", "0", "sparse"),
        ("C", "3", "sparse"),
        ("C", "4", "intermediate"),
        ("C", "6", "intermediate"),
        ("C", "7", "dense"),
        ("C", "8", "dense"),
        # Suburb (B): sparse / intermediate / intermediate.
        ("B", "0", "sparse"),
        ("B", "3", "sparse"),
        ("B", "4", "intermediate"),
        ("B", "6", "intermediate"),
        ("B", "7", "intermediate"),
        ("B", "8", "intermediate"),
        # Isolated town (I): always sparse.
        ("I", "0", "sparse"),
        ("I", "4", "sparse"),
        ("I", "8", "sparse"),
        # Rural, outside urban units (R): always very_sparse.
        ("R", "0", "very_sparse"),
        ("R", "4", "very_sparse"),
        ("R", "8", "very_sparse"),
        # Unmapped/missing status or size: the grid's own stray-code
        # fallback, 'intermediate'.
        (None, "7", "intermediate"),
        ("C", None, "intermediate"),
        ("H", "7", "intermediate"),
    ],
)
def test_density_proxy_table_matches_section_9_9(
    uu_status: str | None, tuu_res: str | None, expected: str
) -> None:
    def _sql_literal(value: str | None) -> str:
        return "NULL::VARCHAR" if value is None else f"{value!r}::VARCHAR"

    con = duckdb.connect()
    case_sql = trip_legs.density_proxy_case_sql("uu_status", "tuu_res")
    row = con.sql(f"""
        SELECT ({case_sql}) FROM (
            SELECT {_sql_literal(uu_status)} AS uu_status,
                {_sql_literal(tuu_res)} AS tuu_res
        )
    """).fetchone()
    assert row[0] == expected


#: A tiny, hand-built ``trips_norm`` (not a real survey's, unlike
#: ``conftest.py``'s synthetic EMP 2019 zip): one trip per
#: `terminal_legs`-affected mode group, all in a 'dense' cell
#: (`density_ori_grid`/`density_des_grid`, so ``density_source='grid'``
#: needs no proxy inputs). `ident_ind` 1/2 are both car drivers (2's
#: `declared_walk_min` is missing, to test the default fallback); 3 is a
#: cyclist; 4 is urban PT (`mtp` 5.7, metro -- a vehicle with a
#: configured headway); 5 is a train (`mtp` 6.3, intercites, also a
#: configured headway) -- `'declared_plus1'`'s one excluded mode.
def _make_trips_norm(con: duckdb.DuckDBPyConnection) -> None:
    con.sql("""
        CREATE TABLE trips_norm (
            ident_dep VARCHAR, ident_ind VARCHAR, ident_men VARCHAR,
            day_id VARCHAR, pond_jour DOUBLE, pond_ind DOUBLE,
            typejour INTEGER, mobloc INTEGER, num_dep INTEGER,
            moridom INTEGER, duration_min DOUBLE, distance_km_declared DOUBLE,
            maccompm DOUBLE, maccomphm DOUBLE, mtp DOUBLE, motive DOUBLE,
            is_loop_trip BOOLEAN, age INTEGER, age_band VARCHAR,
            population_category VARCHAR, declared_walk_min DOUBLE,
            declared_wait_min DOUBLE, uu_status_ori VARCHAR,
            uu_status_des VARCHAR, uu_status_res VARCHAR, tuu_res VARCHAR,
            density_ori_grid VARCHAR, density_des_grid VARCHAR,
            density_res_grid VARCHAR
        )
    """)
    con.sql("""
        INSERT INTO trips_norm VALUES
            ('D1', '1', 'M1', '1', 100.0, 100.0, 1, 1, 1, 1, 30.0, 5.0,
             NULL, NULL, 3.1, 9.1, FALSE, 30, '30', 'employed',
             3.0, NULL, 'C', 'C', 'C', '7', 'dense', 'dense', 'dense'),
            ('D2', '2', 'M2', '2', 100.0, 100.0, 1, 1, 1, 1, 30.0, 5.0,
             NULL, NULL, 3.1, 9.1, FALSE, 30, '30', 'employed',
             NULL, NULL, 'C', 'C', 'C', '7', 'dense', 'dense', 'dense'),
            ('D3', '3', 'M3', '3', 100.0, 100.0, 1, 1, 1, 1, 20.0, 3.0,
             NULL, NULL, 2.1, 9.1, FALSE, 30, '30', 'employed',
             2.5, NULL, 'C', 'C', 'C', '7', 'dense', 'dense', 'dense'),
            ('D4', '4', 'M4', '4', 100.0, 100.0, 1, 1, 1, 1, 30.0, 4.0,
             NULL, NULL, 5.7, 9.1, FALSE, 30, '30', 'employed',
             4.0, 3.0, 'C', 'C', 'C', '7', 'dense', 'dense', 'dense'),
            ('D5', '5', 'M5', '5', 100.0, 100.0, 1, 1, 1, 1, 90.0, 120.0,
             NULL, NULL, 6.3, 9.1, FALSE, 30, '30', 'employed',
             6.0, 5.0, 'C', 'C', 'C', '7', 'dense', 'dense', 'dense')
    """)


def _row(con: duckdb.DuckDBPyConnection, ident_ind: str) -> dict:
    columns = (
        "used_walk_min, used_wait_min, declared_walk_min, declared_wait_min, "
        "walk_to_car_min, walk_from_car_min, access_walk_ori_min, "
        "access_walk_des_min, wait_min"
    )
    row = con.sql(
        f"SELECT {columns} FROM trip_legs WHERE ident_ind = '{ident_ind}'"
    ).fetchone()
    return dict(zip(columns.split(", "), row, strict=False))


@pytest.fixture
def config():
    return load_energy_config(CONFIG_PATH)


def test_terminal_legs_declared_uses_declared_values(config) -> None:
    """``'declared'`` (the default): each trip's own declared walking/
    waiting minutes replace the car/carpool/PT/bike terminal-leg
    defaults (section 9.9, 27 October 2026 decision)."""
    con = duckdb.connect()
    _make_trips_norm(con)
    trip_legs.build_trip_legs(con, config, density_source="grid")

    car = _row(con, "1")
    assert car["used_walk_min"] == pytest.approx(3.0)
    assert car["used_wait_min"] is None  # car has no PT wait

    cycle = _row(con, "3")
    assert cycle["used_walk_min"] == pytest.approx(2.5)

    urban_pt = _row(con, "4")
    assert urban_pt["used_walk_min"] == pytest.approx(4.0)
    assert urban_pt["used_wait_min"] == pytest.approx(3.0)

    train = _row(con, "5")
    assert train["used_walk_min"] == pytest.approx(6.0)
    assert train["used_wait_min"] == pytest.approx(5.0)


def test_terminal_legs_declared_falls_back_to_default_when_missing(config) -> None:
    """A trip with no declared walking minutes (`ident_ind` 2) keeps the
    section 9.4-9.7 default, under every `terminal_legs` variant."""
    con = duckdb.connect()
    _make_trips_norm(con)
    for variant in trip_legs.TERMINAL_LEGS_VARIANTS:
        trip_legs.build_trip_legs(
            con, config, density_source="grid", terminal_legs=variant
        )
        row = _row(con, "2")
        expected_default = row["walk_to_car_min"] + row["walk_from_car_min"]
        extra = 1.0 if variant == "declared_plus1" else 0.0
        assert row["used_walk_min"] == pytest.approx(expected_default + extra), variant


def test_terminal_legs_declared_plus1_excludes_train(config) -> None:
    """``'declared_plus1'`` adds 1 min of walking to car, bike and urban
    PT trips, but not train (section 9.9, 27 October 2026 decision)."""
    con = duckdb.connect()
    _make_trips_norm(con)
    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="declared_plus1"
    )
    assert _row(con, "1")["used_walk_min"] == pytest.approx(4.0)  # car: 3.0 + 1
    assert _row(con, "3")["used_walk_min"] == pytest.approx(3.5)  # cycle: 2.5 + 1
    assert _row(con, "4")["used_walk_min"] == pytest.approx(5.0)  # urban_pt: 4.0 + 1
    assert _row(con, "5")["used_walk_min"] == pytest.approx(6.0)  # train: unchanged
    # Waiting is never bumped by `'declared_plus1'` (only walking is).
    assert _row(con, "4")["used_wait_min"] == pytest.approx(3.0)
    assert _row(con, "5")["used_wait_min"] == pytest.approx(5.0)


def test_terminal_legs_defaults_ignores_declared_values(config) -> None:
    """``'defaults'`` keeps the section 9.4-9.7 density/vehicle defaults,
    whatever each trip's own declared values are (the pre-27 October
    2026 model, still available for the F8 robustness sweep)."""
    con = duckdb.connect()
    _make_trips_norm(con)
    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="defaults"
    )

    car = _row(con, "1")
    assert car["used_walk_min"] == pytest.approx(
        car["walk_to_car_min"] + car["walk_from_car_min"]
    )
    cycle = _row(con, "3")
    assert cycle["used_walk_min"] == pytest.approx(2.0 * config.bike.get_park_min)
    urban_pt = _row(con, "4")
    assert urban_pt["used_walk_min"] == pytest.approx(
        urban_pt["access_walk_ori_min"] + urban_pt["access_walk_des_min"]
    )
    assert urban_pt["used_wait_min"] == pytest.approx(urban_pt["wait_min"])


def test_terminal_scale_only_affects_defaults_variant(config) -> None:
    """`terminal_scale` keeps its old x0.5/x1.5 robustness-sweep role
    only under `terminal_legs='defaults'`; a declared quantity is not
    scaled (section 9.9, 27 October 2026 decision)."""
    con = duckdb.connect()
    _make_trips_norm(con)

    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="declared", terminal_scale=0.5
    )
    declared_half = _row(con, "1")["used_walk_min"]
    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="declared", terminal_scale=1.0
    )
    declared_full = _row(con, "1")["used_walk_min"]
    assert declared_half == pytest.approx(declared_full)

    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="defaults", terminal_scale=0.5
    )
    energy_half = con.sql(
        "SELECT energy_kh_kj FROM trip_legs WHERE ident_ind = '1'"
    ).fetchone()[0]
    trip_legs.build_trip_legs(
        con, config, density_source="grid", terminal_legs="defaults", terminal_scale=1.0
    )
    energy_full = con.sql(
        "SELECT energy_kh_kj FROM trip_legs WHERE ident_ind = '1'"
    ).fetchone()[0]
    assert energy_half != pytest.approx(energy_full)


def test_unknown_terminal_legs_raises(config) -> None:
    con = duckdb.connect()
    _make_trips_norm(con)
    with pytest.raises(ValueError, match="terminal_legs"):
        trip_legs.build_trip_legs(con, config, terminal_legs="not_a_variant")
