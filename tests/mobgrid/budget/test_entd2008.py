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


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        (None, None),
        ("", None),
        ("Moins de 400 € (moins de 2 600 F)", 200.0),
        ("De 400 € à moins de 600 € (de 2 600 F à moins de 3 900 F)", 500.0),
        (
            "De 1 200 € à moins de 1 500 € (de 7 900 F à moins de 9 800 F)",
            1350.0,
        ),
        ("10 000 € ou plus (65 600 F ou plus)", 15000.0),
    ],
)
def test_income_bracket_midpoint_eur(label: str | None, expected: float | None) -> None:
    """`TrancheRevenuMensuel`'s bracket midpoint (section 9.9's "Income
    variables"): interior brackets average their two bounds, the bottom
    open bracket is half its upper bound, the top open bracket is 1.5
    times its lower bound."""
    result = entd2008.income_bracket_midpoint_eur(label)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected)


def test_respondent_income_quintiles_every_household_with_a_bracket(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    """Every household of the synthetic fixture has a `TrancheRevenuMensuel`
    bracket except M7 (blank, the non-traveller): its respondent gets
    `'unknown'`; the other six, quintiled by `NBUC`-adjusted income, get
    one of `'q1'`..`'q5'` (section 9.9's "Income variables")."""
    rows = dict(
        trips_norm.sql("SELECT ident_ind, income_quintile FROM respondent_income")
        .fetchall()
    )
    assert rows["7"] == "unknown"
    for ident_ind in ("1", "2", "3", "4", "5", "6", "8"):
        assert rows[ident_ind] in ("q1", "q2", "q3", "q4", "q5")
    # M1 (the smallest bracket, "Moins de 400") must rank at or below M8
    # (the top bracket, "10 000 ou plus"): quintile labels are ordered.
    order = {"q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5}
    assert order[rows["1"]] <= order[rows["8"]]


def test_income_quintile_column_on_trip_legs(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    config = load_energy_config(CONFIG_PATH)
    trip_legs.build_trip_legs(trips_norm, config, density_source="proxy")
    income_quintile = trips_norm.sql(
        "SELECT income_quintile FROM trip_legs WHERE ident_ind = '7'"
    ).fetchone()
    # Respondent 7 has no trip (the non-traveller), so no trip_legs row.
    assert income_quintile is None
    income_quintile = trips_norm.sql(
        "SELECT income_quintile FROM trip_legs WHERE ident_ind = '1'"
    ).fetchone()[0]
    assert income_quintile in trip_legs.INCOME_QUINTILE_LABELS


def test_missing_income_breakdown_distinguishes_every_failure_mode() -> None:
    """28 October 2026's missing-income audit: a producer-side gap (no
    `Q_TCM_MENAGE` row at all, or a blank bracket) is a different
    failure mode from this project's own code (an unparseable bracket
    label, or a missing/zero `NBUC` making the division `NULL`)."""
    con = duckdb.connect()
    con.sql(
        "CREATE TABLE k_individu "
        "(IDENT_IND VARCHAR, idENT_MEN VARCHAR, PONDKI DOUBLE)"
    )
    con.sql(
        "INSERT INTO k_individu VALUES "
        "('1', 'M1', 100.0), ('2', 'M2', 100.0), ('3', 'M3', 100.0), "
        "('4', 'M4', 100.0), ('5', 'M5', 100.0)"
    )
    con.sql(
        "CREATE TABLE q_tcm_menage "
        "(IDENT_MEN VARCHAR, TrancheRevenuMensuel VARCHAR, NBUC DOUBLE)"
    )
    con.sql("""
        INSERT INTO q_tcm_menage VALUES
            ('M1', 'De 1 200 € à moins de 1 500 €', 2.0),
            ('M2', NULL, 2.0),
            ('M3', 'not a parseable label', 2.0),
            ('M4', 'De 1 200 € à moins de 1 500 €', 0.0)
    """)
    # M5: no row in q_tcm_menage at all.

    breakdown = entd2008.missing_income_breakdown(con)
    assert breakdown["n_total"] == 5
    assert breakdown["n_no_household_match"] == 1
    assert breakdown["n_null_bracket"] == 1
    assert breakdown["n_unparseable_bracket"] == 1
    assert breakdown["n_null_nbuc"] == 1


def test_population_category_by_ident_covers_non_traveller(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    """Respondent 7 (`SITUA` 5, retired) has no trip at all, but must
    still get a population category (section 9.9 point 2's per-person
    budget groups non-travellers too)."""
    result = entd2008.population_category_by_ident(trips_norm)
    assert result["7"] == "retired"
    assert result["1"] == "employed"


def test_residence_density_by_ident_matches_proxy(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    result = entd2008.residence_density_by_ident(trips_norm, "proxy")
    # M5 (respondent 5): rural trip end and residence (commune rurale).
    assert result["5"] == "very_sparse"
    # M1 (respondent 1): city centre, large residence size (TU99 = 7).
    assert result["1"] == "dense"


def test_residence_density_by_ident_rejects_grid(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    with pytest.raises(ValueError, match="no density grid"):
        entd2008.residence_density_by_ident(trips_norm, "grid")


def test_person_weekday_rows_flags_non_traveller_as_immobile(
    trips_norm: duckdb.DuckDBPyConnection,
) -> None:
    weekday_rows = entd2008.person_weekday_rows(trips_norm)
    rows = {
        ident_ind: (day_type, immobile)
        for ident_ind, _ident_men, _pond, day_type, immobile in weekday_rows
    }
    assert rows["7"] == ("weekday", 1.0)
    assert rows["1"] == ("weekday", 0.0)


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
