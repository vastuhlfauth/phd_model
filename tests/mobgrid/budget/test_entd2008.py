"""Unit tests for the ENTD 2008 trip-leg reconstruction (section 9.9's
"Change between 2008 and 2019", step 11).

Uses a tiny synthetic raw directory (``synthetic_entd2008_raw_dir``,
``conftest.py``), not the real ENTD 2008 data (isolated, no ``data/raw``
access, per ``.github/instructions/tests.instructions.md``).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from mobgrid.budget import entd2008, trip_legs
from mobgrid.energy.rates import load_energy_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "energy.yaml"


def test_mode_conversion_table_matches_documented_mapping() -> None:
    """Every 2008 `V2_MTP` code of `docs/data/entd2008.md`'s "Modes"
    table converts to its documented EMP 2019 `mtp` code."""
    expected = {
        "1.10": 1.1,
        "1.11": 1.1,
        "1.12": 1.1,
        "1.13": 1.1,
        "2.20": 2.1,
        "2.22": 2.3,
        "2.23": 2.3,
        "2.24": 2.3,
        "2.25": 2.3,
        "2.29": 2.3,
        "3.30": 3.1,
        "3.31": 3.1,
        "3.32": 3.2,
        "3.33": 3.3,
        "3.39": 3.4,
        "4.40": 4.1,
        "4.41": 4.1,
        "4.42": 4.1,
        "4.43": 4.1,
        "5.50": 5.1,
        "5.51": 5.2,
        "5.52": 5.3,
        "5.53": 5.4,
        "5.54": 5.5,
        "5.55": 5.6,
        "5.56": 5.7,
        "5.57": 5.8,
        "5.58": 5.9,
        "5.59": 5.1,
        "6.60": 6.1,
        "6.61": 6.1,
        "6.62": 6.3,
        "6.63": 6.3,
        "6.69": 6.3,
        "7.70": 7.1,
        "8.80": 8.1,
        "9.90": 9.1,
    }
    con = duckdb.connect()
    codes = sorted(expected)
    case_sql = trip_legs._case_sql("code", entd2008._MODE_CONVERSION)
    rows = con.sql(f"""
        SELECT code, ({case_sql}) AS mtp
        FROM (SELECT unnest({codes!r}) AS code)
    """).fetchall()
    actual = dict(rows)
    assert actual == expected


def test_purpose_conversion_table_matches_documented_mapping() -> None:
    """Every 2008 `V2_MMOTIFDES`/`V2_MMOTIFORI` code of
    `docs/data/entd2008.md`'s "Purposes" table converts to its
    documented EMP 2019 motive code."""
    expected = {
        "1.1": 1.1,
        "1.2": 1.2,
        "1.3": 1.3,
        "1.11": 1.4,
        "1.12": 1.5,
        "2.20": 2.1,
        "2.21": 2.2,
        "3.31": 3.1,
        "4.41": 4.1,
        "5.51": 5.1,
        "5.52": 5.2,
        "6.61": 6.1,
        "6.62": 6.2,
        "6.63": 6.3,
        "6.64": 6.4,
        "7.71": 7.1,
        "7.72": 7.2,
        "7.73": 7.3,
        "7.74": 7.4,
        "7.75": 7.5,
        "7.76": 7.6,
        "7.77": 7.7,
        "7.78": 7.8,
        "8.80": 8.1,
        "8.81": 8.2,
        "8.82": 8.3,
        "8.89": 8.4,
        "9.91": 9.1,
        "9.92": 9.2,
        "9.94": 9.3,
        "9.95": 9.4,
        "9.96": 9.5,
    }
    con = duckdb.connect()
    codes = sorted(expected)
    case_sql = trip_legs._case_sql("code", entd2008._PURPOSE_CONVERSION)
    rows = con.sql(f"""
        SELECT code, ({case_sql}) AS motive
        FROM (SELECT unnest({codes!r}) AS code)
    """).fetchall()
    actual = dict(rows)
    assert actual == expected


@pytest.fixture
def trips_norm(
    tmp_path: Path, synthetic_entd2008_raw_dir: Path
) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    csv_paths = entd2008.extract_tables(synthetic_entd2008_raw_dir, tmp_path / "csv")
    entd2008.register_views(con, csv_paths)
    entd2008.build_trips_norm(con)
    return con


def test_poids_jour_zero_rows_are_dropped(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    # Respondent 3's only trip has POIDS_JOUR = 0 (a weekday trip outside
    # the reference day): it must not appear in `trips_norm`.
    n = trips_norm.sql(
        "SELECT count(*) FROM trips_norm WHERE ident_ind = '3'"
    ).fetchone()[0]
    assert n == 0


def test_sequence_purpose_rule_return_trip_takes_outward_purpose(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    """Respondent 1's return trip (raw purpose 1.1, "retour au
    domicile") takes the purpose of the outward trip it closes (its own
    `V2_MMOTIFORI` = 9.91, "travail lieu habituel", converted to 9.1),
    not 1.1 itself (`docs/data/entd2008.md`'s `motive` row)."""
    outward_motive, return_motive = trips_norm.sql("""
        SELECT
            (SELECT motive FROM trips_norm WHERE ident_ind = '1' AND num_dep = 1),
            (SELECT motive FROM trips_norm WHERE ident_ind = '1' AND num_dep = 2)
    """).fetchone()
    assert outward_motive == pytest.approx(9.1)
    assert return_motive == pytest.approx(9.1)


def test_carpool_is_distinguished_by_companions(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    # Respondent 4: MACCOMPM = 0, MACCOMPHM = 3 -> carpool, once combined
    # with the shared mode classification in `trip_legs.build_trip_legs`.
    config = load_energy_config(CONFIG_PATH)
    trip_legs.build_trip_legs(trips_norm, config, density_source="proxy")
    mode_group = trips_norm.sql(
        "SELECT mode_group FROM trip_legs WHERE ident_ind = '4'"
    ).fetchone()[0]
    assert mode_group == "car_passenger_carpool"


def test_density_proxy_assigns_very_sparse_for_rural_trip_ends(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    config = load_energy_config(CONFIG_PATH)
    trip_legs.build_trip_legs(trips_norm, config, density_source="proxy")
    density_ori = trips_norm.sql(
        "SELECT density_ori FROM trip_legs WHERE ident_ind = '5'"
    ).fetchone()[0]
    assert density_ori == "very_sparse"


def test_distcor_and_v2_mduree_fill_rates(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    """Respondent 2 is the only kept row with `distcor`/`v2_mduree`
    filled (section 9.9's "Quirks"); the rest fall back to
    `V2_MDISTTOT`/`V2_DUREE`."""
    rates = entd2008.quirk_fill_rates(trips_norm)
    n_kept = trips_norm.sql(
        "SELECT count(*) FROM k_deploc WHERE POIDS_JOUR > 0"
    ).fetchone()[0]
    assert rates["distcor_fill_rate"] == pytest.approx(1 / n_kept)
    assert rates["v2_mduree_fill_rate"] == pytest.approx(1 / n_kept)
    # distcor (2.8) - V2_MDISTTOT (3.0) = -0.2; v2_mduree (14) - V2_DUREE
    # (15) = -1.0, respondent 2's only filled row.
    assert rates["distcor_mean_change_km"] == pytest.approx(-0.2)
    assert rates["v2_mduree_mean_change_min"] == pytest.approx(-1.0)
