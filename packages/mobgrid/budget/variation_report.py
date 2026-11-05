"""Step-12 travel-time variation report (Parts A, B and C).

``python -m mobgrid.budget.variation_report --out docs/data/step12_variation
--entd2008-zoning-data-path data/raw/entd2008/ENTD2008_avec_zonages_EMP``
reuses the step-11 survey loaders and ``trip_legs`` reconstruction, with a
harmonised return-home motive rule and optional ENTD 2008 zoning supplement,
extracts weekday person-days with trips in the needs scope with their day
weights, and writes the step-12 report: the
survey-method checks of Part A (recall lag, motive crosswalk, distances,
durations, calendar) and the decompositions of Part B (composition,
trips x distance x speed, mode/motive/distance shift-shares, tails, the
comparison pairs and their figures), and Part C measurement checks
(rounding bounds, common distances, trips by motive, the measurement
ledger, official-scope replication and door-to-door speed checks).
Step-11 outputs are not touched.

Bootstrap intervals resample households within each survey,
independently (``--bootstrap-reps``, default 200). ``--sample-households
PCT`` keeps a stable hash-based percentage of households per survey, for
smoke runs only.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mobgrid.budget import (
    daily_energy,
    emp2019,
    entd2008,
    trip_legs,
    variation,
)
from mobgrid.energy.rates import EnergyConfig, load_energy_config

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = ROOT / "config" / "energy.yaml"
DEFAULT_OUT_DIR = ROOT / "docs" / "data" / "step12_variation"

#: Suppression threshold, as in the step-11 reports (section 9.9's
#: "cells of fewer than 50 persons left blank").
MIN_CELL_N = 50

#: B1's age bands (lower bound inclusive); 75+ is open-ended.
AGE_BAND_LOWER = (6, 11, 15, 18, 25, 35, 45, 55, 65, 75)
AGE_BAND_LABELS = (
    "6-10",
    "11-14",
    "15-17",
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55-64",
    "65-74",
    "75+",
)

#: A3/B4's distance bands, km (lower bound inclusive, upper exclusive).
DISTANCE_BAND_UPPER_KM = (1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0, float("inf"))
DISTANCE_BAND_LABELS = (
    "0-1 km",
    "1-2 km",
    "2-5 km",
    "5-10 km",
    "10-20 km",
    "20-40 km",
    "40-80 km",
    ">=80 km",
    "unknown distance",
)

SPEED_BAND_LABELS = ("2-5 km", "5-10 km", "10-20 km", "20-40 km", "40-80 km")
SPEED_BAND_UPPER_KM = (5.0, 10.0, 20.0, 40.0)
DENSITY_GRID_LABELS = ("dense", "intermediate", "sparse", "very_sparse")
RESIDENCE_CLASS_LABELS = (
    "pôle",
    "couronne",
    "hors attraction",
)
RESIDENCE_CLASS_BY_AAV_CODE = {
    "11": "pôle",
    "12": "pôle",
    "13": "pôle",
    "20": "couronne",
    "30": "hors attraction",
}
RESIDENCE_ZONING_VARIABLES = (
    "TUU2017_RES",
    "STATUTCOM_UU_RES",
    "TYPE_UU_RES",
    "TAA2017_RES",
    "CATCOM_AA_RES",
    "DENSITECOM_RES",
)
HISTORICAL_1994_VALUES = {
    "pôle": (6.1, 17.7, 20.7),
    "couronne": (9.88, 17.60, 33.7),
    "hors attraction": (9.0, 15.6, 34.6),
    "All": (7.3, 17.3, 25.3),
}

#: B3's trip mode groups (step 11's trip-level mapping, with the two
#: passenger types merged into "car_passenger").
MODE7_LABELS = (
    "walk",
    "bike",
    "car_driver",
    "car_passenger",
    "urban_pt",
    "train",
    "other",
)

#: B4's harmonised motive groups: the top-level (integer) motive code of
#: the step-11 harmonised nomenclature (`trip_legs.
#: TOP_LEVEL_MOTIVE_LABEL_BY_CODE`); group 8 and the non-needs part of 7
#: are outside the needs scope by construction.
MOTIVE_GROUP_LABELS = {
    1: "home/study/childcare",
    2: "shopping",
    3: "medical/personal care",
    4: "administrative errand",
    5: "visits",
    6: "accompany/pick up",
    7: "leisure (needs scope)",
    8: "holidays/second home",
    9: "professional",
}

_FRENCH_WEEKDAY_NUM = {
    "lundi": 1,
    "mardi": 2,
    "mercredi": 3,
    "jeudi": 4,
    "vendredi": 5,
    "samedi": 6,
    "dimanche": 7,
}
_FRENCH_MONTH_NUM = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}
WEEKDAY_LABELS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri"}


@dataclass
class SurveyFrames:
    """One survey's step-12 extraction: weekday person-days and trips,
    plus the all-trips sensitivity and in-SQL Part A diagnostics."""

    name: str
    days: dict[str, np.ndarray]
    trips: dict[str, np.ndarray]
    aux: dict
    all_trips: SurveyFrames | None = None


@dataclass(frozen=True)
class SpeedSample:
    """C6 trip-level inputs; distances are km and durations are minutes."""

    household: np.ndarray
    weight: np.ndarray
    duration_min: np.ndarray
    producer_km: np.ndarray
    declared_km: np.ndarray
    crow_fly_km: np.ndarray
    mode: np.ndarray
    density: np.ndarray
    residence_zone: np.ndarray


def _sample_sql(sample_pct: float | None) -> str:
    if sample_pct is None:
        return "TRUE"
    return f"(hash(CAST(ident_men AS VARCHAR)) % 100) < {float(sample_pct):g}"


def _has_column(con: duckdb.DuckDBPyConnection, table: str, column: str) -> bool:
    return bool(
        con.execute(
            """
            SELECT count(*) > 0
            FROM information_schema.columns
            WHERE lower(table_name) = lower(?) AND lower(column_name) = lower(?)
            """,
            [table, column],
        ).fetchone()[0]
    )


def _create_person_ext_emp2019(con: duckdb.DuckDBPyConnection) -> None:
    """EMP 2019 person-level extras: sex, recall lag (`MDATE_delai`, 1-7
    days between the described day and the interview), the described
    day's weekday/month (`MDATE_jour`/`MDATE_mois`, French names),
    Île-de-France residence (`REG_res`), household cars (`JNBVEH`)."""
    residence_class_sql = (
        "TRY_CAST(m.CATCOM_AA_RES AS VARCHAR)"
        if _has_column(con, "tcm_men", "CATCOM_AA_RES")
        else "CAST(NULL AS VARCHAR)"
    )
    con.sql(f"""
        CREATE OR REPLACE VIEW vr_person AS
        SELECT
            i.IDENT_IND AS ident_ind,
            TRY_CAST(k.SEXE AS INTEGER) AS sex,
            TRY_CAST(i.MDATE_delai AS INTEGER) AS recall_lag,
            CAST(i.MDATE_jour AS VARCHAR) AS described_weekday_name,
            CAST(i.MDATE_mois AS VARCHAR) AS described_month_name,
            coalesce(CAST(m.REG_res AS VARCHAR) = 'Ile-de-France', FALSE)
                AS is_idf,
            {residence_class_sql} AS residence_aa_class,
            CASE
                WHEN TRY_CAST(q.JNBVEH AS INTEGER) >= 2 THEN '2+'
                WHEN TRY_CAST(q.JNBVEH AS INTEGER) = 1 THEN '1'
                WHEN TRY_CAST(q.JNBVEH AS INTEGER) = 0 THEN '0'
                ELSE 'unknown'
            END AS cars_band
        FROM k_individu i
        LEFT JOIN tcm_ind t ON t.ident_ind = i.IDENT_IND
        LEFT JOIN tcm_ind_kish k ON k.ident_ind = i.IDENT_IND
        LEFT JOIN tcm_men m ON m.ident_men = t.ident_men
        LEFT JOIN q_menage q ON q.IDENT_MEN = t.ident_men
    """)
    # Trip-level extras: crow-fly distance and the school-holiday flag.
    con.sql("""
        CREATE OR REPLACE VIEW vr_trip_ext AS
        SELECT IDENT_DEP AS ident_dep,
            TRY_CAST(MDISTTOT_decl AS DOUBLE) AS declared_km,
            TRY_CAST(dVO_ORIDES AS DOUBLE) AS crow_fly_km,
            TRY_CAST(NEW_VAC_SCOL AS INTEGER) AS vac_scol,
            TRY_CAST(mobloc AS INTEGER) = 1 AS is_local
        FROM k_deploc
    """)


def _create_person_ext_entd2008(con: duckdb.DuckDBPyConnection) -> None:
    """ENTD 2008 person-level extras: sex, recall lag in calendar days
    between the reference weekday described (`V2_DATESEMREF`) and the
    second visit (`MDATENQ2V`, when trips are collected), the reference
    day's weekday/month, Île-de-France residence (`RG` = 11). Household
    cars are not in the four public tables used by step 11 (no
    `JNBVEH` equivalent): `cars_band` is 'unknown' throughout."""
    has_residence_class = _has_column(con, "q_tcm_men_zon20", "CATCOM_AA_RES")
    residence_class_sql = (
        "TRY_CAST(z.CATCOM_AA_RES AS VARCHAR)"
        if has_residence_class
        else "CAST(NULL AS VARCHAR)"
    )
    residence_zone_join = (
        "LEFT JOIN q_tcm_men_zon20 z ON z.IDENT_MEN = d.IDENT_MEN"
        if has_residence_class
        else ""
    )
    con.sql(f"""
        CREATE OR REPLACE VIEW vr_person AS
        WITH dates AS (
            SELECT IDENT_IND, IDENT_MEN,
                coalesce(
                    TRY_CAST(V2_DATESEMREF AS DATE),
                    TRY_CAST(try_strptime(CAST(V2_DATESEMREF AS VARCHAR),
                        '%d/%m/%Y') AS DATE)
                ) AS ref_date,
                coalesce(
                    TRY_CAST(MDATENQ2V AS DATE),
                    TRY_CAST(try_strptime(CAST(MDATENQ2V AS VARCHAR),
                        '%d/%m/%Y') AS DATE)
                ) AS visit2_date,
                CAST(RG AS VARCHAR) AS rg
            FROM k_individu
        )
        SELECT
            d.IDENT_IND AS ident_ind,
            TRY_CAST(q.SEXE AS INTEGER) AS sex,
            CASE WHEN d.ref_date IS NOT NULL AND d.visit2_date IS NOT NULL
                THEN date_diff('day', d.ref_date, d.visit2_date)
            END AS recall_lag,
            CASE isodow(d.ref_date)
                WHEN 1 THEN 'lundi' WHEN 2 THEN 'mardi' WHEN 3 THEN 'mercredi'
                WHEN 4 THEN 'jeudi' WHEN 5 THEN 'vendredi' WHEN 6 THEN 'samedi'
                WHEN 7 THEN 'dimanche'
            END AS described_weekday_name,
            CASE month(d.ref_date)
                WHEN 1 THEN 'janvier' WHEN 2 THEN 'février' WHEN 3 THEN 'mars'
                WHEN 4 THEN 'avril' WHEN 5 THEN 'mai' WHEN 6 THEN 'juin'
                WHEN 7 THEN 'juillet' WHEN 8 THEN 'août'
                WHEN 9 THEN 'septembre' WHEN 10 THEN 'octobre'
                WHEN 11 THEN 'novembre' WHEN 12 THEN 'décembre'
            END AS described_month_name,
            coalesce(d.rg = '11', FALSE) AS is_idf,
            {residence_class_sql} AS residence_aa_class,
            'unknown' AS cars_band
        FROM dates d
        LEFT JOIN q_tcm_individu q ON q.IDENT_IND = d.IDENT_IND
        {residence_zone_join}
    """)
    con.sql("""
        CREATE OR REPLACE VIEW vr_trip_ext AS
        SELECT IDENT_DEP AS ident_dep,
            TRY_CAST(V2_MDISTTOT AS DOUBLE) AS declared_km,
            TRY_CAST(V2_DVO_LOC AS DOUBLE) AS crow_fly_km,
            TRY_CAST(V2_VAC_SCOL AS INTEGER) AS vac_scol,
            TRY_CAST(V2_DLOCAL AS INTEGER) <> 0 AS is_local
        FROM k_deploc
    """)


_PERSON_EXT_BY_SURVEY = {
    "EMP 2019": _create_person_ext_emp2019,
    "ENTD 2008": _create_person_ext_entd2008,
}


def _create_frames_tables(
    con: duckdb.DuckDBPyConnection,
    *,
    sample_pct: float | None,
    scope: str = "needs",
) -> None:
    """Materialise weekday trip/day tables for the needs or all-trips scope."""
    if scope == "needs":
        scope_sql = trip_legs.NEEDS_ONLY_WHERE_SQL
    elif scope == "all":
        scope_sql = "TRUE"
    else:
        raise ValueError(f"unknown variation-report scope: {scope!r}")
    mode7_sql = """
        CASE t.mode_group
            WHEN 'cycle' THEN 'bike'
            WHEN 'car_passenger_household' THEN 'car_passenger'
            WHEN 'car_passenger_carpool' THEN 'car_passenger'
            ELSE t.mode_group
        END
    """
    motive_group_sql = "CAST(TRY_CAST(floor(t.motive) AS INTEGER) AS VARCHAR)"
    con.sql(f"""
        CREATE OR REPLACE TABLE vr_trips AS
        SELECT
            t.day_id, t.ident_ind, t.ident_men, t.pond_jour,
            t.population_category,
            t.residence_density AS home_density,
            t.income_quintile,
            t.age, t.duration_min, t.distance_km,
            ({mode7_sql}) AS mode7,
            coalesce({motive_group_sql}, 'unknown') AS motive_group,
            e.declared_km, e.crow_fly_km, e.vac_scol,
            p.sex, p.recall_lag, p.described_weekday_name,
            p.described_month_name, p.is_idf, p.cars_band,
            p.residence_aa_class
        FROM trip_legs t
        LEFT JOIN vr_person p ON p.ident_ind = t.ident_ind
        LEFT JOIN vr_trip_ext e ON e.ident_dep = t.ident_dep
        WHERE t.typejour = 1 AND t.pond_jour > 0
            AND ({scope_sql})
            AND ({_sample_sql(sample_pct)})
    """)
    con.sql("""
        CREATE OR REPLACE TABLE vr_days AS
        SELECT
            day_id,
            any_value(ident_ind) AS ident_ind,
            any_value(ident_men) AS ident_men,
            any_value(pond_jour) AS pond_jour,
            any_value(population_category) AS population_category,
            any_value(home_density) AS home_density,
            any_value(income_quintile) AS income_quintile,
            any_value(age) AS age,
            any_value(sex) AS sex,
            any_value(recall_lag) AS recall_lag,
            any_value(described_weekday_name) AS described_weekday_name,
            any_value(described_month_name) AS described_month_name,
            any_value(is_idf) AS is_idf,
            any_value(cars_band) AS cars_band,
            max(coalesce(vac_scol, 0)) AS vac_scol,
            count(*) AS trips_per_day,
            sum(duration_min) AS total_time_min,
            coalesce(sum(distance_km) FILTER (
                WHERE isfinite(distance_km)), 0) AS total_distance_km,
            count(*) FILTER (WHERE isfinite(distance_km)) AS distance_trips,
            coalesce(sum(duration_min) FILTER (
                WHERE isfinite(distance_km)), 0) AS distance_time_min
        FROM vr_trips
        GROUP BY day_id
    """)


def _needs_scope_removal(con: duckdb.DuckDBPyConnection) -> dict:
    """A2's scope check: the weighted share of weekday trips and time
    excluded from the local-needs reference scope."""
    row = con.sql(f"""
        SELECT
            sum(pond_jour) FILTER (
                WHERE NOT ({trip_legs.NEEDS_ONLY_WHERE_SQL})
            ) / sum(pond_jour),
            sum(pond_jour * duration_min) FILTER (
                WHERE NOT ({trip_legs.NEEDS_ONLY_WHERE_SQL})
            ) / sum(pond_jour * duration_min)
        FROM trip_legs
        WHERE typejour = 1 AND pond_jour > 0
    """).fetchone()
    return {
        "share_trips_removed": float(row[0] or 0.0),
        "share_time_removed": float(row[1] or 0.0),
    }


def _local_scope_removal(con: duckdb.DuckDBPyConnection) -> dict[str, float | int]:
    """Weighted non-local need trips and minutes removed per prior-scope day."""
    row = con.sql(f"""
        WITH old_scope_days AS (
            SELECT day_id, any_value(pond_jour) AS weight,
                count(*) FILTER (WHERE mobloc IS DISTINCT FROM 1)
                    AS removed_trips,
                coalesce(sum(duration_min) FILTER (
                    WHERE mobloc IS DISTINCT FROM 1
                ), 0) AS removed_minutes
            FROM trip_legs
            WHERE typejour = 1 AND pond_jour > 0
                AND ({trip_legs.NEEDS_MOTIVE_WHERE_SQL})
            GROUP BY day_id
        )
        SELECT count(*), sum(weight),
            sum(weight * removed_trips) / nullif(sum(weight), 0),
            sum(weight * removed_minutes) / nullif(sum(weight), 0)
        FROM old_scope_days
    """).fetchone()
    return {
        "n_days": int(row[0] or 0),
        "weighted_days": float(row[1] or 0.0),
        "trips_per_day_removed": float(row[2] or 0.0),
        "minutes_per_day_removed": float(row[3] or 0.0),
    }


def _raw_motive_shares_emp2019(con: duckdb.DuckDBPyConnection) -> dict:
    """Weighted weekday shares of EMP 2019's raw destination
    (`MMOTIFDES`) and origin (`MOTPREC`) motive codes."""
    out = {}
    for key, col in (("destination", "MMOTIFDES"), ("origin", "MOTPREC")):
        rows = con.sql(f"""
            SELECT CAST({col} AS VARCHAR) AS code,
                sum(POND_JOUR) / sum(sum(POND_JOUR)) OVER () AS share
            FROM k_deploc
            WHERE TYPEJOUR = 1 AND POND_JOUR > 0 AND {col} IS NOT NULL
            GROUP BY 1
        """).fetchall()
        out[key] = {code: float(share) for code, share in rows}
    return out


def _raw_motive_shares_entd2008(con: duckdb.DuckDBPyConnection) -> dict:
    """Weighted weekday shares of ENTD 2008's raw `V2_` destination and
    origin motive codes."""
    out = {}
    for key, col in (("destination", "V2_MMOTIFDES"), ("origin", "V2_MMOTIFORI")):
        rows = con.sql(f"""
            SELECT CAST({col} AS VARCHAR) AS code,
                sum(TRY_CAST(POIDS_JOUR AS DOUBLE))
                    / sum(sum(TRY_CAST(POIDS_JOUR AS DOUBLE))) OVER () AS share
            FROM k_deploc
            WHERE TRY_CAST(V2_TYPJOUR AS INTEGER) = 1
                AND TRY_CAST(POIDS_JOUR AS DOUBLE) > 0
                AND {col} IS NOT NULL AND CAST({col} AS VARCHAR) != ''
            GROUP BY 1
        """).fetchall()
        out[key] = {code: float(share) for code, share in rows}
    return out


def _distance_doc_emp2019(con: duckdb.DuckDBPyConnection) -> dict:
    """A3's distance provenance on EMP 2019: fill rates of the declared
    (`MDISTTOT_decl`), final (`MDISTTOT_fin`), crow-fly (`dVO_ORIDES`)
    and IGN route (`dist_ign`) distances, the producer-corrected share
    (`indic_dist_corr`), and the 80-km check on local weekday trips."""
    row = con.sql("""
        SELECT count(*),
            count(MDISTTOT_decl), count(MDISTTOT_fin),
            count(dVO_ORIDES), count(dist_ign),
            sum(CASE WHEN TRY_CAST(indic_dist_corr AS INTEGER) = 1
                THEN 1 ELSE 0 END),
            sum(CASE WHEN mobloc = 1
                AND TRY_CAST(dVO_ORIDES AS DOUBLE) > 80 THEN 1 ELSE 0 END),
            max(TRY_CAST(dVO_ORIDES AS DOUBLE)) FILTER (WHERE mobloc = 1),
            max(TRY_CAST(MDISTTOT_fin AS DOUBLE)) FILTER (WHERE mobloc = 1),
            count(*) FILTER (WHERE mobloc = 1)
        FROM k_deploc
        WHERE POND_JOUR > 0
    """).fetchone()
    return {
        "n_trips": row[0],
        "n_declared": row[1],
        "n_final": row[2],
        "n_crow_fly": row[3],
        "n_route": row[4],
        "n_producer_corrected": int(row[5] or 0),
        "n_local_crow_fly_over_80": int(row[6] or 0),
        "max_local_crow_fly_km": float(row[7]) if row[7] is not None else None,
        "max_local_route_km": float(row[8]) if row[8] is not None else None,
        "n_local": row[9],
    }


def _distance_doc_entd2008(con: duckdb.DuckDBPyConnection) -> dict:
    """A3's distance provenance on ENTD 2008: fill rates of the declared
    (`V2_MDISTTOT`), corrected (`distcor`) and local crow-fly
    (`V2_DVO_LOC`) distances, and the 80-km check on local trips."""
    row = con.sql("""
        SELECT count(*),
            count(TRY_CAST(V2_MDISTTOT AS DOUBLE)),
            count(TRY_CAST(distcor AS DOUBLE)),
            count(TRY_CAST(V2_DVO_LOC AS DOUBLE)),
            sum(CASE WHEN TRY_CAST(V2_DLOCAL AS INTEGER) = 1
                AND TRY_CAST(V2_DVO_LOC AS DOUBLE) > 80 THEN 1 ELSE 0 END),
            max(TRY_CAST(V2_DVO_LOC AS DOUBLE))
                FILTER (WHERE TRY_CAST(V2_DLOCAL AS INTEGER) = 1),
            max(coalesce(
                    TRY_CAST(distcor AS DOUBLE), TRY_CAST(V2_MDISTTOT AS DOUBLE)
                ))
                FILTER (WHERE TRY_CAST(V2_DLOCAL AS INTEGER) = 1),
            count(*) FILTER (WHERE TRY_CAST(V2_DLOCAL AS INTEGER) = 1)
        FROM k_deploc
        WHERE TRY_CAST(POIDS_JOUR AS DOUBLE) > 0
    """).fetchone()
    return {
        "n_trips": row[0],
        "n_declared": row[1],
        "n_corrected": row[2],
        "n_crow_fly": row[3],
        "n_local_crow_fly_over_80": int(row[4] or 0),
        "max_local_crow_fly_km": float(row[5]) if row[5] is not None else None,
        "max_local_route_km": float(row[6]) if row[6] is not None else None,
        "n_local": row[7],
    }


_AUX_BY_SURVEY = {
    "EMP 2019": (_raw_motive_shares_emp2019, _distance_doc_emp2019),
    "ENTD 2008": (_raw_motive_shares_entd2008, _distance_doc_entd2008),
}


def load_frames(
    survey,
    data_path: Path | None = None,
    config: EnergyConfig | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    density_source: str | None = None,
    zoning_data_path: Path | None = None,
    sample_pct: float | None = None,
) -> SurveyFrames:
    """Build one survey's step-12 frames with explicit motive/density inputs."""
    config = config or load_energy_config(config_path)
    data_path = data_path or survey.DEFAULT_DATA_PATH
    density_source = density_source or survey.DEFAULT_DENSITY_SOURCE
    interim_dir = (
        None
        if data_path == survey.DEFAULT_DATA_PATH
        else data_path.parent / f"_interim_{survey.__name__.rsplit('.', 1)[-1]}_csv"
    )
    con = duckdb.connect()
    try:
        csv_paths = survey.extract_tables(data_path, interim_dir)
        survey.register_views(con, csv_paths)
        if zoning_data_path is not None:
            if survey is not entd2008:
                raise ValueError("zoning_data_path is only supported for ENTD 2008")
            zoning_out_dir = (
                interim_dir / "zon20"
                if interim_dir is not None
                else ROOT / "data" / "interim" / "entd2008" / "zon20"
            )
            zoning_csv_paths = survey.extract_zoning_tables(
                zoning_data_path, zoning_out_dir
            )
            survey.register_zoning_views(con, zoning_csv_paths)
        if survey is entd2008 and density_source == "grid":
            if zoning_data_path is None:
                raise ValueError(
                    "ENTD 2008 density_source='grid' requires zoning_data_path"
                )
            survey.build_trip_legs(con, config, density_source=density_source)
        elif survey is emp2019:
            survey.build_trip_legs(
                con,
                config,
                density_source=density_source,
            )
        else:
            survey.build_trip_legs(con, config, density_source=density_source)
        _PERSON_EXT_BY_SURVEY[survey.SURVEY_NAME](con)
        _create_frames_tables(con, sample_pct=sample_pct)
        days = con.sql("SELECT * FROM vr_days").fetchnumpy()
        trips = con.sql("SELECT * FROM vr_trips").fetchnumpy()
        _create_frames_tables(con, sample_pct=sample_pct, scope="all")
        all_days = con.sql("SELECT * FROM vr_days").fetchnumpy()
        all_trips = con.sql("SELECT * FROM vr_trips").fetchnumpy()
        official_data = _official_scope_data(con, survey, sample_pct)
        motive_shares, distance_doc = _AUX_BY_SURVEY[survey.SURVEY_NAME]
        aux = {
            "needs_scope_removal": _needs_scope_removal(con),
            "local_scope_removal": _local_scope_removal(con),
            "raw_motive_shares": motive_shares(con),
            "distance_doc": distance_doc(con),
            "official_scope_data": official_data,
        }
        if survey is emp2019:
            aux["sequence_motive_summary"] = emp2019.sequence_motive_summary(
                con, sample_pct=sample_pct
            )
    finally:
        con.close()
    days = {k: _plain_array(v) for k, v in days.items()}
    trips = {k: _plain_array(v) for k, v in trips.items()}
    all_trips_frames = SurveyFrames(
        name=survey.SURVEY_NAME,
        days={k: _plain_array(v) for k, v in all_days.items()},
        trips={k: _plain_array(v) for k, v in all_trips.items()},
        aux={},
    )
    return SurveyFrames(
        name=survey.SURVEY_NAME,
        days=days,
        trips=trips,
        aux=aux,
        all_trips=all_trips_frames,
    )


def _official_scope_data(
    con: duckdb.DuckDBPyConnection, survey, sample_pct: float | None
) -> dict[str, np.ndarray]:
    """Extract age-6+ local trips and full person/day denominators."""
    if survey is emp2019:
        person_rows = emp2019.person_estimator_rows(con)
        age_rows = con.sql(
            "SELECT IDENT_IND, TRY_CAST(AGE AS INTEGER) FROM tcm_ind_kish"
        ).fetchall()
        sampled = con.sql(f"""
            SELECT i.IDENT_IND
            FROM k_individu i
            JOIN tcm_ind t ON t.ident_ind = i.IDENT_IND
            WHERE {_sample_sql(sample_pct)}
        """).fetchall()
    else:
        person_rows = entd2008.person_estimator_rows(con)
        age_rows = con.sql(
            "SELECT i.IDENT_IND, TRY_CAST(q.AGE AS INTEGER) "
            "FROM k_individu i JOIN q_tcm_individu q ON q.IDENT_IND = i.IDENT_IND"
        ).fetchall()
        sampled = con.sql(
            f"SELECT IDENT_IND FROM k_individu WHERE {_sample_sql(sample_pct)}"
        ).fetchall()
    ages = {str(person_id): age for person_id, age in age_rows}
    sampled_ids = {str(row[0]) for row in sampled}
    eligible_people = [
        row
        for row in person_rows
        if str(row[0]) in sampled_ids
        and ages.get(str(row[0])) is not None
        and ages[str(row[0])] >= 6
    ]
    type_filter = "t.typejour = 1" if survey is entd2008 else "t.typejour IN (1, 2, 3)"
    trips = con.sql(f"""
        SELECT t.ident_men, t.pond_jour, t.typejour,
            t.duration_min, t.distance_km, t.age, t.residence_density,
            t.mode_group, e.declared_km, e.crow_fly_km, p.residence_aa_class
        FROM trip_legs t
        LEFT JOIN vr_trip_ext e ON e.ident_dep = t.ident_dep
        LEFT JOIN vr_person p ON p.ident_ind = t.ident_ind
        WHERE {type_filter} AND t.pond_jour > 0 AND t.age >= 6
            AND t.mobloc = 1 AND ({_sample_sql(sample_pct)})
    """).fetchall()
    described_days = con.sql(f"""
        SELECT t.day_id, any_value(t.ident_men) AS ident_men,
            any_value(t.pond_jour) AS pond_jour,
            count(*) FILTER (WHERE t.mobloc = 1) AS local_trips
        FROM trip_legs t
        WHERE t.typejour = 1 AND t.pond_jour > 0 AND t.age >= 6
            AND ({_sample_sql(sample_pct)})
        GROUP BY t.day_id
    """).fetchall()
    if not eligible_people or not trips or not described_days:
        raise ValueError(
            f"{survey.SURVEY_NAME} official-scope sample is empty "
            f"(people={len(eligible_people)}, local-trips={len(trips)}, "
            f"described-weekdays={len(described_days)})"
        )
    zero_local_days = [row for row in described_days if row[3] == 0]
    return {
        "household_p": np.asarray([str(row[1]) for row in eligible_people]),
        "weight_p": np.asarray([float(row[2]) for row in eligible_people]),
        "household_t": np.asarray([str(row[0]) for row in trips]),
        "weight_t": np.asarray([float(row[1]) for row in trips]),
        "type_t": np.asarray([int(row[2]) for row in trips]),
        "minutes": np.asarray(
            [np.nan if row[3] is None else float(row[3]) for row in trips]
        ),
        "distance_km": np.asarray(
            [np.nan if row[4] is None else float(row[4]) for row in trips]
        ),
        "age_t": np.asarray([int(row[5]) for row in trips]),
        "density_t": np.asarray([row[6] for row in trips], dtype=object),
        "mode_t": np.asarray([row[7] for row in trips], dtype=object),
        "declared_km": np.asarray(
            [np.nan if row[8] is None else float(row[8]) for row in trips]
        ),
        "crow_fly_km": np.asarray(
            [np.nan if row[9] is None else float(row[9]) for row in trips]
        ),
        "residence_aa_class": np.asarray([row[10] for row in trips], dtype=object),
        "zero_local_n_days": len(zero_local_days),
        "described_n_days": len(described_days),
        "zero_local_weight": float(sum(float(row[2]) for row in zero_local_days)),
        "described_weight": float(sum(float(row[2]) for row in described_days)),
        "n_people": len(eligible_people),
    }


def _official_scope_estimates(
    frames: SurveyFrames, *, n_reps: int, seed: int
) -> dict[str, dict]:
    """C5 direct producer-weighted local-trip estimates and CIs."""
    data = frames.aux["official_scope_data"]

    def interval(values: np.ndarray) -> tuple[float, float]:
        finite = values[np.isfinite(values)]
        if len(finite) == 0:
            return float("nan"), float("nan")
        low, high = np.percentile(finite, [2.5, 97.5])
        return float(low), float(high)

    weekday = data["type_t"] == 1
    periods = {"weekday": (weekday, 5.0 if frames.name == "EMP 2019" else 1.0)}
    if frames.name == "EMP 2019":
        periods["week"] = (np.ones(len(weekday), dtype=bool), 1.0)
    results = {"n": int(data["n_people"])}
    for period, (mask, divisor) in periods.items():
        household = data["household_t"][mask]
        weight = data["weight_t"][mask]
        ones = np.ones(len(weight))
        trip_mean, trip_reps = daily_energy.bootstrap_person_value_replicates(
            data["household_p"],
            data["weight_p"],
            household,
            weight,
            ones,
            period_divisor=divisor,
            n_reps=n_reps,
            seed=seed,
        )
        time_mask = mask & np.isfinite(data["minutes"])
        minutes_per_trip, minutes_ci = daily_energy.bootstrap_mean_ci(
            data["household_t"][time_mask],
            data["weight_t"][time_mask],
            data["minutes"][time_mask],
            n_reps=n_reps,
            seed=seed,
        )
        distance_mask = mask & np.isfinite(data["distance_km"])
        km_per_trip, km_ci = daily_energy.bootstrap_mean_ci(
            data["household_t"][distance_mask],
            data["weight_t"][distance_mask],
            data["distance_km"][distance_mask],
            n_reps=n_reps,
            seed=seed,
        )
        results[period] = {
            "trips_per_person": {
                "estimate": trip_mean,
                "ci": interval(trip_reps),
            },
            "minutes_per_trip": {
                "estimate": minutes_per_trip,
                "ci": minutes_ci,
            },
            "km_per_trip": {"estimate": km_per_trip, "ci": km_ci},
        }
    described_weight = float(data["described_weight"])
    results["zero_local_trip_days"] = {
        "share": (
            float(data["zero_local_weight"]) / described_weight
            if described_weight > 0
            else float("nan")
        ),
        "n_zero": int(data["zero_local_n_days"]),
        "n_described": int(data["described_n_days"]),
        "weighted_zero": float(data["zero_local_weight"]),
        "weighted_described": described_weight,
    }
    return results


def _format_official_scope(results_2008: dict, results_2019: dict) -> list[str]:
    published = (
        ("Weekday", "weekday", "trips_per_person", "trips/person", 3.15, 3.04055),
        ("Weekday", "weekday", "minutes_per_trip", "min/trip", 17.9, 20.36964),
        ("Weekday", "weekday", "km_per_trip", "km/trip", None, 8.72921),
        ("7-day", "week", "trips_per_person", "trips/person/week", None, 19.7928),
        ("7-day", "week", "minutes_per_trip", "min/trip", None, 20.69912),
        ("7-day", "week", "km_per_trip", "km/trip", None, 8.970084),
    )
    lines = [
        "### C5. Official-scope replication",
        "",
        "Residents aged 6+, all motives, local trips (`mobloc = 1`). "
        "Per-person trip counts are direct producer-weighted sums over the "
        "full respondent roster: EMP 2019 divides weekday totals by 5 and "
        "reports the 7-day total as a weekly value; ENTD 2008 uses "
        "`POIDS_JOUR` over all Kish reference weekdays. Minutes and "
        "kilometres per trip use "
        "household-bootstrap 95% CIs; kilometre estimates use trips with "
        "known distance.",
        "",
        "| Period | Indicator | Unit | n 2008 | 2008 [95% CI] | "
        "SDES 2008 | Gap 2008 | n 2019 | 2019 [95% CI] | SDES 2019 | "
        "Gap 2019 |",
        "|---|---|---|---:|---|---:|---:|---:|---|---:|---:|",
    ]
    for period, period_key, metric, unit, reference_2008, reference_2019 in published:
        value_2008 = results_2008.get(period_key)
        value_2019 = results_2019.get(period_key)
        metric_2008 = value_2008.get(metric) if value_2008 else None
        metric_2019 = value_2019.get(metric) if value_2019 else None
        estimate_2008 = (
            _ci_cell(metric_2008["estimate"], metric_2008["ci"]) if metric_2008 else "-"
        )
        estimate_2019 = (
            _ci_cell(metric_2019["estimate"], metric_2019["ci"]) if metric_2019 else "-"
        )
        gap_2008 = (
            100.0 * (metric_2008["estimate"] / reference_2008 - 1.0)
            if metric_2008 and reference_2008 is not None
            else None
        )
        gap_2019 = (
            100.0 * (metric_2019["estimate"] / reference_2019 - 1.0)
            if metric_2019 and reference_2019 is not None
            else None
        )
        gap_cell_2008 = (
            _suppress(results_2008["n"], _num(gap_2008))
            if gap_2008 is not None
            else "-"
        )
        gap_cell_2019 = (
            _suppress(results_2019["n"], _num(gap_2019))
            if gap_2019 is not None
            else "-"
        )
        lines.append(
            f"| {period} | {metric} | {unit} | "
            f"{results_2008['n'] if metric_2008 else '-'} | "
            f"{_suppress(results_2008['n'], estimate_2008) if metric_2008 else '-'} | "
            f"{reference_2008 if reference_2008 is not None else '-'} | "
            f"{gap_cell_2008} | "
            f"{results_2019['n'] if metric_2019 else '-'} | "
            f"{_suppress(results_2019['n'], estimate_2019) if metric_2019 else '-'} | "
            f"{reference_2019 if reference_2019 is not None else '-'} | "
            f"{gap_cell_2019} |"
        )
    lines += [
        "",
        "**Zero-local-trip diagnostic (weekday described out-days, age 6+):**",
    ]
    for label, results in (("ENTD 2008", results_2008), ("EMP 2019", results_2019)):
        diagnostic = results["zero_local_trip_days"]
        lines.append(
            f"- {label}: {diagnostic['share']:.2%} by day weight "
            f"({diagnostic['n_zero']}/{diagnostic['n_described']} days; "
            f"{diagnostic['weighted_zero']:,.0f}/"
            f"{diagnostic['weighted_described']:,.0f} weighted days)."
        )
    return lines


def _plain_array(column: np.ndarray) -> np.ndarray:
    """Convert a DuckDB masked array to a plain array (NaN/None fill)."""
    if isinstance(column, np.ma.MaskedArray):
        if column.dtype.kind in "fiu":
            return column.astype(float).filled(np.nan)
        return column.filled(None)
    return column


# ---------------------------------------------------------------------------
# Part C6: door-to-door speed
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeedMetric:
    estimate: float
    interval: tuple[float, float]
    replicates: np.ndarray


@dataclass(frozen=True)
class SpeedEstimate:
    n_trips: int
    km_per_trip: SpeedMetric
    minutes_per_trip: SpeedMetric
    speed_kmh: SpeedMetric
    zero_km_share: SpeedMetric | None
    rescaled_n: int
    dropped_n: int


def _text_values(values: np.ndarray) -> np.ndarray:
    return np.asarray(
        ["" if value is None else str(value).strip() for value in values],
        dtype=object,
    )


def _speed_sample(frames: SurveyFrames, scope: str) -> SpeedSample:
    """Get C6 weekday trips, preserving the existing survey scope definitions."""
    if scope == "A":
        data = frames.aux["official_scope_data"]
        weekday = data["type_t"] == 1
        return SpeedSample(
            household=data["household_t"][weekday].astype(str),
            weight=data["weight_t"][weekday].astype(float),
            duration_min=data["minutes"][weekday].astype(float),
            producer_km=data["distance_km"][weekday].astype(float),
            declared_km=data["declared_km"][weekday].astype(float),
            crow_fly_km=data["crow_fly_km"][weekday].astype(float),
            mode=_text_values(data["mode_t"][weekday]),
            density=_text_values(data["density_t"][weekday]),
            residence_zone=_text_values(data["residence_aa_class"][weekday]),
        )
    if scope != "B":
        raise ValueError(f"unknown speed scope: {scope!r}")
    trips = frames.trips
    return SpeedSample(
        household=trips["ident_men"].astype(str),
        weight=trips["pond_jour"].astype(float),
        duration_min=trips["duration_min"].astype(float),
        producer_km=trips["distance_km"].astype(float),
        declared_km=trips["declared_km"].astype(float),
        crow_fly_km=trips["crow_fly_km"].astype(float),
        mode=_text_values(trips["mode7"]),
        density=_text_values(trips["home_density"]),
        residence_zone=_text_values(trips["residence_aa_class"]),
    )


def _distance_measure_values(
    sample: SpeedSample, measure: str, selected: np.ndarray
) -> tuple[np.ndarray, int, int]:
    """Return distance km and declared-distance cleaning counts for C6."""
    if measure == "producer":
        return sample.producer_km, 0, 0
    if measure == "crow-fly":
        return sample.crow_fly_km, 0, 0
    if measure != "declared":
        raise ValueError(f"unknown speed distance measure: {measure!r}")
    distance = sample.declared_km.copy()
    crow = sample.crow_fly_km
    finite_pair = np.isfinite(distance) & np.isfinite(crow)
    rescaled = finite_pair & (crow > 0) & (distance > 100.0 * crow)
    distance[rescaled] /= 1000.0
    dropped = (
        selected
        & np.isfinite(distance)
        & np.isfinite(crow)
        & (crow > 2.0)
        & ((distance < 0.5 * crow) | (distance > 10.0 * crow))
    )
    distance[dropped] = np.nan
    return distance, int(np.sum(rescaled & selected)), int(np.sum(dropped))


def _metric_interval(
    estimate: float, replicates: np.ndarray, *, percentiles: tuple[float, float]
) -> SpeedMetric:
    finite = replicates[np.isfinite(replicates)]
    interval = (float("nan"), float("nan"))
    if len(finite):
        bounds = np.percentile(finite, percentiles)
        interval = (float(bounds[0]), float(bounds[1]))
    return SpeedMetric(estimate, interval, replicates)


def _empty_speed_metric(n_reps: int) -> SpeedMetric:
    return SpeedMetric(
        float("nan"),
        (float("nan"), float("nan")),
        np.full(n_reps, np.nan),
    )


def _bootstrap_speed_estimate(
    sample: SpeedSample,
    measure: str,
    selected: np.ndarray,
    *,
    n_reps: int,
    seed: int,
) -> SpeedEstimate:
    """Ratio-of-weighted-totals speed and household-bootstrap CIs (C6)."""
    if n_reps < 1:
        raise ValueError("n_reps must be positive")
    selected = np.asarray(selected, dtype=bool)
    if len(selected) != len(sample.weight):
        raise ValueError("speed selection mask length must match trip arrays")
    distance, rescaled_n, dropped_n = _distance_measure_values(
        sample, measure, selected
    )
    valid = (
        selected
        & np.isfinite(sample.weight)
        & (sample.weight > 0)
        & np.isfinite(sample.duration_min)
        & (sample.duration_min > 0)
        & np.isfinite(distance)
        & (distance >= 0)
    )
    n_trips = int(np.sum(valid))
    if n_trips == 0:
        empty = _empty_speed_metric(n_reps)
        return SpeedEstimate(
            0,
            empty,
            empty,
            empty,
            empty if measure == "crow-fly" else None,
            rescaled_n,
            dropped_n,
        )

    household = sample.household[valid].astype(str)
    weight = sample.weight[valid]
    duration = sample.duration_min[valid]
    km = distance[valid]
    total_weight = float(np.sum(weight))
    total_time = float(np.sum(weight * duration))
    if total_weight <= 0 or total_time <= 0:
        raise ValueError("speed estimates require positive weighted trips and time")
    point_km = float(np.sum(weight * km) / total_weight)
    point_minutes = float(total_time / total_weight)
    point_speed = float(60.0 * np.sum(weight * km) / total_time)
    point_zero = (
        float(np.sum(weight * (km == 0)) / total_weight)
        if measure == "crow-fly"
        else None
    )

    reps_km = np.full(n_reps, np.nan)
    reps_minutes = np.full(n_reps, np.nan)
    reps_speed = np.full(n_reps, np.nan)
    reps_zero = np.full(n_reps, np.nan) if measure == "crow-fly" else None
    rng = np.random.default_rng(seed)
    for rep in range(n_reps):
        multiplier = variation.household_multipliers(household, rng)
        rep_weight = weight * multiplier
        rep_total = float(np.sum(rep_weight))
        rep_time = float(np.sum(rep_weight * duration))
        if rep_total <= 0 or rep_time <= 0:
            continue
        rep_distance = float(np.sum(rep_weight * km))
        reps_km[rep] = rep_distance / rep_total
        reps_minutes[rep] = rep_time / rep_total
        reps_speed[rep] = 60.0 * rep_distance / rep_time
        if reps_zero is not None:
            reps_zero[rep] = float(np.sum(rep_weight * (km == 0)) / rep_total)

    return SpeedEstimate(
        n_trips,
        _metric_interval(point_km, reps_km, percentiles=(2.5, 97.5)),
        _metric_interval(point_minutes, reps_minutes, percentiles=(2.5, 97.5)),
        _metric_interval(point_speed, reps_speed, percentiles=(2.5, 97.5)),
        (
            _metric_interval(point_zero, reps_zero, percentiles=(2.5, 97.5))
            if reps_zero is not None and point_zero is not None
            else None
        ),
        rescaled_n,
        dropped_n,
    )


def _ratio_metric(metric_a: SpeedMetric, metric_b: SpeedMetric) -> SpeedMetric | None:
    """Independent-survey 2019/2008 ratio and percentile 90% interval."""
    if (
        not np.isfinite(metric_a.estimate)
        or not np.isfinite(metric_b.estimate)
        or metric_a.estimate <= 0
        or metric_b.estimate <= 0
        or len(metric_a.replicates) == 0
        or len(metric_a.replicates) != len(metric_b.replicates)
    ):
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = metric_b.replicates / metric_a.replicates
    finite = ratios[np.isfinite(ratios) & (ratios > 0)]
    if len(finite) == 0:
        return None
    return SpeedMetric(
        metric_b.estimate / metric_a.estimate,
        tuple(float(v) for v in np.percentile(finite, [5.0, 95.0])),
        ratios,
    )


def _residence_classes(sample: SpeedSample) -> np.ndarray:
    """Map shared AAV residence codes, using the INSEE grid for unknowns."""
    density = np.asarray(
        [
            value
            if value in DENSITY_GRID_LABELS
            else {
                "1": "dense",
                "2": "intermediate",
                "3": "sparse",
                "4": "very_sparse",
            }.get(value, "unknown")
            for value in sample.density
        ],
        dtype=object,
    )
    return np.asarray(
        [
            RESIDENCE_CLASS_BY_AAV_CODE.get(
                str(code), f"INSEE density: {grid}" if grid != "unknown" else "unknown"
            )
            for code, grid in zip(sample.residence_zone, density, strict=True)
        ],
        dtype=object,
    )


def _speed_band_index(distance_km: np.ndarray) -> np.ndarray:
    valid = np.isfinite(distance_km) & (distance_km >= 2.0) & (distance_km <= 80.0)
    result = np.full(len(distance_km), -1, dtype=int)
    result[valid] = np.searchsorted(
        SPEED_BAND_UPPER_KM, distance_km[valid], side="right"
    )
    return result


def _density_index(values: np.ndarray) -> np.ndarray:
    as_text = _text_values(values)
    code_map = {str(i + 1): i for i in range(len(DENSITY_GRID_LABELS))}
    result = np.full(len(as_text), -1, dtype=int)
    for index, value in enumerate(as_text):
        if value in DENSITY_GRID_LABELS:
            result[index] = DENSITY_GRID_LABELS.index(value)
        elif value in code_map:
            result[index] = code_map[value]
    return result


def _standardization_input(sample: SpeedSample) -> dict[str, np.ndarray]:
    bands = _speed_band_index(sample.crow_fly_km)
    density = _density_index(sample.density)
    cells = bands * len(DENSITY_GRID_LABELS) + density
    valid = (
        (bands >= 0)
        & (density >= 0)
        & (sample.mode == "car_driver")
        & np.isfinite(sample.weight)
        & (sample.weight > 0)
        & np.isfinite(sample.duration_min)
        & (sample.duration_min > 0)
        & np.isfinite(sample.crow_fly_km)
        & (sample.crow_fly_km >= 0)
    )
    return {
        "household": sample.household[valid].astype(str),
        "weight": sample.weight[valid],
        "duration": sample.duration_min[valid],
        "distance": sample.crow_fly_km[valid],
        "cell": cells[valid],
    }


def _standardized_speed_value(
    sample: dict[str, np.ndarray],
    multiplier: np.ndarray,
    common_cells: np.ndarray,
    mix: np.ndarray,
) -> float:
    weight = sample["weight"] * multiplier
    active_cells = common_cells[mix[common_cells] > 0]
    if len(active_cells) == 0:
        return float("nan")
    distance_mean = np.zeros(len(SPEED_BAND_LABELS) * len(DENSITY_GRID_LABELS))
    time_mean = np.zeros_like(distance_mean)
    for cell in active_cells:
        selected = sample["cell"] == cell
        total = float(np.sum(weight[selected]))
        if total <= 0:
            return float("nan")
        distance_mean[cell] = float(
            np.sum(weight[selected] * sample["distance"][selected]) / total
        )
        time_mean[cell] = float(
            np.sum(weight[selected] * sample["duration"][selected]) / total
        )
    weighted_distance = float(np.sum(mix[active_cells] * distance_mean[active_cells]))
    weighted_time = float(np.sum(mix[active_cells] * time_mean[active_cells]))
    return (
        60.0 * weighted_distance / weighted_time if weighted_time > 0 else float("nan")
    )


def _standardized_car_speed(
    sample_2008: SpeedSample,
    sample_2019: SpeedSample,
    *,
    n_reps: int,
    seed: int,
) -> tuple[int, int, int, SpeedMetric, SpeedMetric]:
    """Reweight crow-fly car speeds to the 2008 band x density trip mix."""
    data_a = _standardization_input(sample_2008)
    data_b = _standardization_input(sample_2019)
    n_cells = len(SPEED_BAND_LABELS) * len(DENSITY_GRID_LABELS)
    weight_a = np.bincount(data_a["cell"], weights=data_a["weight"], minlength=n_cells)
    weight_b = np.bincount(data_b["cell"], weights=data_b["weight"], minlength=n_cells)
    common_cells = np.flatnonzero((weight_a > 0) & (weight_b > 0))
    empty = _empty_speed_metric(n_reps)
    if len(common_cells) == 0:
        return 0, 0, 0, empty, empty

    n_a = int(np.sum(np.isin(data_a["cell"], common_cells)))
    n_b = int(np.sum(np.isin(data_b["cell"], common_cells)))
    cell_weight_a = np.bincount(
        data_a["cell"], weights=data_a["weight"], minlength=n_cells
    )
    point_mix = cell_weight_a / np.sum(cell_weight_a[common_cells])
    point_a = _standardized_speed_value(
        data_a, np.ones(len(data_a["weight"])), common_cells, point_mix
    )
    point_b = _standardized_speed_value(
        data_b, np.ones(len(data_b["weight"])), common_cells, point_mix
    )
    reps_a = np.full(n_reps, np.nan)
    reps_b = np.full(n_reps, np.nan)
    rng_a, rng_b = (
        np.random.default_rng(child) for child in np.random.SeedSequence(seed).spawn(2)
    )
    for rep in range(n_reps):
        multiplier_a = variation.household_multipliers(data_a["household"], rng_a)
        multiplier_b = variation.household_multipliers(data_b["household"], rng_b)
        cell_weight_a = np.bincount(
            data_a["cell"],
            weights=data_a["weight"] * multiplier_a,
            minlength=n_cells,
        )
        mix_total = float(np.sum(cell_weight_a[common_cells]))
        if mix_total <= 0:
            continue
        mix = cell_weight_a / mix_total
        reps_a[rep] = _standardized_speed_value(data_a, multiplier_a, common_cells, mix)
        reps_b[rep] = _standardized_speed_value(data_b, multiplier_b, common_cells, mix)
    return (
        len(common_cells),
        n_a,
        n_b,
        _metric_interval(point_a, reps_a, percentiles=(2.5, 97.5)),
        _metric_interval(point_b, reps_b, percentiles=(2.5, 97.5)),
    )


def _metric_cell(metric: SpeedMetric, n_trips: int, decimals: int = 2) -> str:
    if (
        n_trips < MIN_CELL_N
        or not np.isfinite(metric.estimate)
        or not np.isfinite(metric.interval).all()
    ):
        return "-"
    return (
        f"{_num(metric.estimate, decimals)} "
        f"[{_num(metric.interval[0], decimals)}, "
        f"{_num(metric.interval[1], decimals)}]"
    )


def _ratio_cell(
    metric_a: SpeedMetric,
    metric_b: SpeedMetric,
    n_a: int,
    n_b: int,
    decimals: int = 2,
) -> str:
    ratio = _ratio_metric(metric_a, metric_b)
    return "-" if ratio is None else _metric_cell(ratio, min(n_a, n_b), decimals)


def _speed_report_sample(
    sample: SpeedSample,
    measure: str,
    selected: np.ndarray,
    *,
    n_reps: int,
    seed: int,
) -> SpeedEstimate:
    return _bootstrap_speed_estimate(
        sample,
        measure,
        selected,
        n_reps=n_reps,
        seed=seed,
    )


def _format_c6_overall(
    samples: dict[str, tuple[SpeedSample, SpeedSample]],
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    lines = [
        "#### Overall speed and distance",
        "",
        "| Scope | Distance measure | n 2008 | n 2019 | 2008 km/trip [95% CI] | "
        "2019 km/trip [95% CI] | km/trip ratio 2019/2008 [90% CI] | "
        "2008 km/h [95% CI] | 2019 km/h [95% CI] | "
        "speed ratio 2019/2008 [90% CI] | Rescaled declared 2008 | "
        "Dropped declared 2008 | Rescaled declared 2019 | "
        "Dropped declared 2019 |",
        "|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for scope_index, (scope, pair) in enumerate(samples.items()):
        selected_a = np.ones(len(pair[0].weight), dtype=bool)
        selected_b = np.ones(len(pair[1].weight), dtype=bool)
        for measure_index, measure in enumerate(("producer", "declared", "crow-fly")):
            offset = seed + scope_index * 100 + measure_index * 10
            a = _speed_report_sample(
                pair[0], measure, selected_a, n_reps=n_reps, seed=offset
            )
            b = _speed_report_sample(
                pair[1], measure, selected_b, n_reps=n_reps, seed=offset + 1
            )
            lines.append(
                f"| {scope} | {measure} | {a.n_trips} | {b.n_trips} | "
                f"{_metric_cell(a.km_per_trip, a.n_trips)} | "
                f"{_metric_cell(b.km_per_trip, b.n_trips)} | "
                f"{_ratio_cell(a.km_per_trip, b.km_per_trip, a.n_trips, b.n_trips)} | "
                f"{_metric_cell(a.speed_kmh, a.n_trips)} | "
                f"{_metric_cell(b.speed_kmh, b.n_trips)} | "
                f"{_ratio_cell(a.speed_kmh, b.speed_kmh, a.n_trips, b.n_trips)} | "
                f"{a.rescaled_n} | {a.dropped_n} | "
                f"{b.rescaled_n} | {b.dropped_n} |"
            )
    lines += [
        "",
        "The declared-distance counts are unweighted trip counts in the "
        "selected scope. Crow-fly distance treats zero as a valid distance; "
        "producer distance is ENTD `distcor` (otherwise `V2_MDISTTOT`) and "
        "EMP `MDISTTOT_fin`, with the existing step-11 correction.",
    ]
    return lines


def _format_c6_residence(
    samples: dict[str, tuple[SpeedSample, SpeedSample]],
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    class_values = {
        scope: (_residence_classes(pair[0]), _residence_classes(pair[1]))
        for scope, pair in samples.items()
    }
    fallback_labels = sorted(
        {
            str(label)
            for pair in class_values.values()
            for values in pair
            for label in values
            if str(label).startswith("INSEE density:")
        }
    )
    classes = [*RESIDENCE_CLASS_LABELS, *fallback_labels]
    lines = [
        "#### Speed by residence class",
        "",
        "The 1994 values are the survey's own published measures (scope A) "
        "and are repeated as a reference across the distance-measure rows; "
        "they are not a common-distance sensitivity estimate.",
        "",
        "| Scope | Residence class | Distance | n 2008 | n 2019 | "
        "2008 km/trip [95% CI] | "
        "2019 km/trip [95% CI] | km/trip ratio [90% CI] | "
        "2008 min/trip [95% CI] | 2019 min/trip [95% CI] | "
        "min/trip ratio [90% CI] | 2008 km/h [95% CI] | "
        "2019 km/h [95% CI] | speed ratio [90% CI] | "
        "1994 published (km/trip; min/trip; km/h) |",
        "|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for scope_index, (scope, pair) in enumerate(samples.items()):
        classes_a, classes_b = class_values[scope]
        groups = [("All", None), *((label, label) for label in classes)]
        for group_index, (label, class_value) in enumerate(groups):
            mask_a = (
                np.ones(len(classes_a), dtype=bool)
                if class_value is None
                else classes_a == class_value
            )
            mask_b = (
                np.ones(len(classes_b), dtype=bool)
                if class_value is None
                else classes_b == class_value
            )
            for measure_index, measure in enumerate(
                ("producer", "declared", "crow-fly")
            ):
                offset = (
                    seed
                    + 1000
                    + scope_index * 1000
                    + group_index * 30
                    + measure_index * 2
                )
                a = _speed_report_sample(
                    pair[0], measure, mask_a, n_reps=n_reps, seed=offset
                )
                b = _speed_report_sample(
                    pair[1], measure, mask_b, n_reps=n_reps, seed=offset + 1
                )
                historical = HISTORICAL_1994_VALUES.get(label)
                historical_cell = (
                    " / ".join(f"{value:.1f}" for value in historical)
                    if scope == "A" and historical is not None
                    else "-"
                )
                km_ratio = _ratio_cell(
                    a.km_per_trip, b.km_per_trip, a.n_trips, b.n_trips
                )
                minutes_ratio = _ratio_cell(
                    a.minutes_per_trip,
                    b.minutes_per_trip,
                    a.n_trips,
                    b.n_trips,
                )
                speed_ratio = _ratio_cell(
                    a.speed_kmh, b.speed_kmh, a.n_trips, b.n_trips
                )
                lines.append(
                    f"| {scope} | {label} | {measure} | {a.n_trips} | "
                    f"{b.n_trips} | "
                    f"{_metric_cell(a.km_per_trip, a.n_trips)} | "
                    f"{_metric_cell(b.km_per_trip, b.n_trips)} | "
                    f"{km_ratio} | "
                    f"{_metric_cell(a.minutes_per_trip, a.n_trips)} | "
                    f"{_metric_cell(b.minutes_per_trip, b.n_trips)} | "
                    f"{minutes_ratio} | "
                    f"{_metric_cell(a.speed_kmh, a.n_trips)} | "
                    f"{_metric_cell(b.speed_kmh, b.n_trips)} | "
                    f"{speed_ratio} | "
                    f"{historical_cell} |"
                )
    return lines


def _format_c6_zero_share(
    samples: dict[str, tuple[SpeedSample, SpeedSample]],
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    lines = [
        "#### Same-commune trips (crow-fly = 0 km)",
        "",
        "| Scope | n 2008 | 2008 share [95% CI] | n 2019 | "
        "2019 share [95% CI] | 2019/2008 share ratio [90% CI] |",
        "|---|---:|---|---:|---|---|",
    ]
    for scope_index, (scope, pair) in enumerate(samples.items()):
        estimates = [
            _speed_report_sample(
                sample,
                "crow-fly",
                np.ones(len(sample.weight), dtype=bool),
                n_reps=n_reps,
                seed=seed + scope_index * 10 + year_index,
            )
            for year_index, sample in enumerate(pair)
        ]
        a, b = estimates
        if a.zero_km_share is None or b.zero_km_share is None:
            raise ValueError("crow-fly estimates must include zero-distance shares")
        lines.append(
            f"| {scope} | {a.n_trips} | "
            f"{_metric_cell(a.zero_km_share, a.n_trips, 3)} | "
            f"{b.n_trips} | "
            f"{_metric_cell(b.zero_km_share, b.n_trips, 3)} | "
            f"{_ratio_cell(a.zero_km_share, b.zero_km_share, a.n_trips, b.n_trips)} |"
        )
    return lines


def _format_c6_mode_bands(
    sample_a: SpeedSample,
    sample_b: SpeedSample,
    *,
    mode: str,
    by_density: bool,
    n_reps: int,
    seed: int,
) -> list[str]:
    title = (
        "Car-driver speed by crow-fly band and INSEE density"
        if by_density
        else f"{'Urban PT' if mode == 'urban_pt' else 'Walking'} speed by crow-fly band"
    )
    groups = tuple(DENSITY_GRID_LABELS) if by_density else (None,)
    density_a = _density_index(sample_a.density)
    density_b = _density_index(sample_b.density)
    band_a = _speed_band_index(sample_a.crow_fly_km)
    band_b = _speed_band_index(sample_b.crow_fly_km)
    lines = [
        f"#### {title}",
        "",
        "| Band | Density | n 2008 | 2008 km/h [95% CI] | "
        "n 2019 | 2019 km/h [95% CI] | 2019/2008 speed ratio [90% CI] |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for band_index, band_label in enumerate(SPEED_BAND_LABELS):
        for density_index, density_label in enumerate(groups):
            selected_a = (band_a == band_index) & (sample_a.mode == mode)
            selected_b = (band_b == band_index) & (sample_b.mode == mode)
            if by_density:
                selected_a &= density_a == density_index
                selected_b &= density_b == density_index
            offset = seed + band_index * 10 + density_index
            a = _speed_report_sample(
                sample_a, "crow-fly", selected_a, n_reps=n_reps, seed=offset
            )
            b = _speed_report_sample(
                sample_b, "crow-fly", selected_b, n_reps=n_reps, seed=offset + 1
            )
            lines.append(
                f"| {band_label} | {density_label or '-'} | {a.n_trips} | "
                f"{_metric_cell(a.speed_kmh, a.n_trips)} | {b.n_trips} | "
                f"{_metric_cell(b.speed_kmh, b.n_trips)} | "
                f"{_ratio_cell(a.speed_kmh, b.speed_kmh, a.n_trips, b.n_trips)} |"
            )
    return lines


def _format_c6_standardized(
    sample_a: SpeedSample,
    sample_b: SpeedSample,
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    common_cells, n_a, n_b, speed_a, speed_b = _standardized_car_speed(
        sample_a, sample_b, n_reps=n_reps, seed=seed
    )
    ratio = _ratio_metric(speed_a, speed_b)
    ratio_cell = "-" if ratio is None else _metric_cell(ratio, min(n_a, n_b))
    change = (
        "-"
        if ratio is None or min(n_a, n_b) < MIN_CELL_N
        else (
            f"{100 * (ratio.estimate - 1):.1f}% "
            f"[{100 * (ratio.interval[0] - 1):.1f}%, "
            f"{100 * (ratio.interval[1] - 1):.1f}%]"
        )
    )
    return [
        "#### Car-driver speed pooled at the 2008 trip mix",
        "",
        "Crow-fly car-driver trips in 2–80 km bands are standardized over "
        "the band × density cells observed in both years. Each cell's mean "
        "distance and minutes are reweighted to the 2008 weighted trip mix; "
        "the reported speed remains a ratio of those weighted totals.",
        "",
        "| Common cells | n 2008 | Standardized 2008 km/h [95% CI] | "
        "n 2019 | Standardized 2019 km/h [95% CI] | "
        "2019/2008 ratio [90% CI] | Change [90% CI] |",
        "|---:|---:|---|---:|---|---|---|",
        f"| {common_cells} | {n_a} | {_metric_cell(speed_a, n_a)} | "
        f"{n_b} | {_metric_cell(speed_b, n_b)} | {ratio_cell} | {change} |",
    ]


def _format_c6(
    frames_2008: SurveyFrames,
    frames_2019: SurveyFrames,
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    """Render C6 speed estimates from the existing trip scopes and weights."""
    samples = {
        "A": (_speed_sample(frames_2008, "A"), _speed_sample(frames_2019, "A")),
        "B": (_speed_sample(frames_2008, "B"), _speed_sample(frames_2019, "B")),
    }
    lines = [
        "### C6. Door-to-door speed",
        "",
        "Speed is total weighted distance (km) divided by total weighted "
        "duration (minutes), multiplied by 60; it is not the mean of trip "
        "speeds. The household bootstrap is independent by survey. Scope A "
        "is ages 6+, Monday–Friday, local trips, all motives (SDES); scope B "
        "is the existing step-12 weekday needs scope. Estimates use trip "
        "weights; distance-specific metrics use trips with valid distance "
        "and positive duration. 2008/2019 ratios use 90% bootstrap intervals; "
        "year estimates use 95% intervals. Cells with fewer than 50 trips "
        "suppress estimates. Declared distances over 100 times crow-fly "
        "(with positive crow-fly) are rescaled from metres, then values "
        "outside 0.5–10 times crow-fly are dropped when crow-fly exceeds 2 km.",
        "",
        *_format_c6_overall(samples, n_reps=n_reps, seed=seed),
        "",
        *_format_c6_zero_share(samples, n_reps=n_reps, seed=seed + 500),
        "",
        *_format_c6_residence(samples, n_reps=n_reps, seed=seed),
        "",
        *_format_c6_mode_bands(
            samples["B"][0],
            samples["B"][1],
            mode="car_driver",
            by_density=True,
            n_reps=n_reps,
            seed=seed + 10_000,
        ),
        "",
        *_format_c6_mode_bands(
            samples["B"][0],
            samples["B"][1],
            mode="urban_pt",
            by_density=False,
            n_reps=n_reps,
            seed=seed + 20_000,
        ),
        "",
        *_format_c6_mode_bands(
            samples["B"][0],
            samples["B"][1],
            mode="walk",
            by_density=False,
            n_reps=n_reps,
            seed=seed + 30_000,
        ),
        "",
        *_format_c6_standardized(
            samples["B"][0],
            samples["B"][1],
            n_reps=n_reps,
            seed=seed + 40_000,
        ),
    ]
    return lines


# ---------------------------------------------------------------------------
# Part A1: recall lag (EMP 2019)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LagRow:
    """One recall-lag row of A1's table (weighted, weekday days)."""

    label: str
    n_days: int
    weighted_share: float
    trips_per_day: float
    minutes_per_trip: float
    time_per_day_min: float
    share_trips_under_5_min: float
    share_trips_under_1_km: float


def _day_metrics(
    days: dict[str, np.ndarray],
    trips: dict[str, np.ndarray],
    day_mask: np.ndarray,
    trip_mask: np.ndarray,
    label: str,
    *,
    total_day_weight: float | None = None,
) -> LagRow:
    w_days = days["pond_jour"][day_mask].astype(float)
    w_trips = trips["pond_jour"][trip_mask].astype(float)
    day_weight = float(w_days.sum())
    trip_weight = float(w_trips.sum())
    time = float(np.sum(w_days * days["total_time_min"][day_mask]))
    duration = trips["duration_min"][trip_mask].astype(float)
    distance = trips["distance_km"][trip_mask].astype(float)
    return LagRow(
        label=label,
        n_days=int(day_mask.sum()),
        weighted_share=(
            day_weight / total_day_weight if total_day_weight else float("nan")
        ),
        trips_per_day=trip_weight / day_weight if day_weight else float("nan"),
        minutes_per_trip=(
            float(np.sum(w_trips * duration)) / trip_weight
            if trip_weight
            else float("nan")
        ),
        time_per_day_min=time / day_weight if day_weight else float("nan"),
        share_trips_under_5_min=(
            float(w_trips[duration < 5.0].sum()) / trip_weight
            if trip_weight
            else float("nan")
        ),
        share_trips_under_1_km=(
            float(w_trips[distance < 1.0].sum()) / trip_weight
            if trip_weight
            else float("nan")
        ),
    )


def recall_lag_table(frames: SurveyFrames) -> list[LagRow]:
    """A1's table: one row per recall lag (1-7 days), weekday described
    days, plus an "all lags" row; days with no recorded lag are only in
    the "all lags" row."""
    days, trips = frames.days, frames.trips
    lag_days = days["recall_lag"].astype(float)
    lag_trips = trips["recall_lag"].astype(float)
    known = np.isfinite(lag_days) & (lag_days >= 1) & (lag_days <= 7)
    total_weight = float(days["pond_jour"][known].astype(float).sum())
    rows = []
    for lag in range(1, 8):
        rows.append(
            _day_metrics(
                days,
                trips,
                lag_days == lag,
                lag_trips == lag,
                str(lag),
                total_day_weight=total_weight,
            )
        )
    rows.append(
        _day_metrics(
            days,
            trips,
            np.ones(len(lag_days), dtype=bool),
            np.ones(len(lag_trips), dtype=bool),
            "all days",
        )
    )
    return rows


def survey_overall_row(frames: SurveyFrames, label: str) -> LagRow:
    """One overall row (all weekday days) for A1's ENTD 2008 comparator."""
    return _day_metrics(
        frames.days,
        frames.trips,
        np.ones(len(frames.days["pond_jour"]), dtype=bool),
        np.ones(len(frames.trips["pond_jour"]), dtype=bool),
        label,
    )


@dataclass(frozen=True)
class LagCoefficient:
    """One recall-lag dummy's WLS coefficient (lag 1 is the reference),
    with a percentile 95% household-bootstrap CI."""

    lag: int
    coefficient: float
    ci: tuple[float, float]
    n_days: int


def lag_regression(
    frames: SurveyFrames,
    outcome: str,
    *,
    n_reps: int = 200,
    seed: int = 0,
) -> list[LagCoefficient]:
    """A1's weighted regression of ``outcome`` (``'total_time_min'`` or
    ``'trips_per_day'``) on recall-lag dummies (reference lag 1) with
    population-category x density-class and described-day weekday fixed
    effects (section 9.9), weekday days."""
    days = frames.days
    lag = days["recall_lag"].astype(float)
    weekday = days["described_weekday_name"].astype(str)
    keep = (
        np.isfinite(lag)
        & (lag >= 1)
        & (lag <= 7)
        & np.isin(weekday, tuple(_FRENCH_WEEKDAY_NUM)[:5])
    )
    weekday = weekday[keep]
    lag = lag[keep].astype(int)
    y = days[outcome][keep].astype(float)
    w = days["pond_jour"][keep].astype(float)
    strata = np.array(
        [
            f"{c}||{d}"
            for c, d in zip(
                days["population_category"][keep],
                days["home_density"][keep],
                strict=True,
            )
        ]
    )
    households = days["ident_men"][keep]

    lag_levels = list(range(2, 8))
    stratum_levels = sorted(set(strata))[1:]  # first stratum absorbed
    weekday_levels = [
        name for name in tuple(_FRENCH_WEEKDAY_NUM)[:5] if name in weekday
    ][1:]
    design = np.ones(
        (len(y), 1 + len(lag_levels) + len(stratum_levels) + len(weekday_levels))
    )
    for j, level in enumerate(lag_levels):
        design[:, 1 + j] = lag == level
    for j, level in enumerate(stratum_levels):
        design[:, 1 + len(lag_levels) + j] = strata == level
    for j, level in enumerate(weekday_levels):
        design[:, 1 + len(lag_levels) + len(stratum_levels) + j] = weekday == level

    def _fit(weights: np.ndarray) -> np.ndarray:
        sw = np.sqrt(weights)
        beta, *_ = np.linalg.lstsq(design * sw[:, None], y * sw, rcond=None)
        return beta[1 : 1 + len(lag_levels)]

    point = _fit(w)
    rng = np.random.default_rng(seed)
    reps = np.full((n_reps, len(lag_levels)), np.nan)
    for rep in range(n_reps):
        multiplicity = variation.household_multipliers(households, rng)
        weights = w * multiplicity
        if weights.sum() <= 0:
            continue
        try:
            reps[rep] = _fit(weights)
        except np.linalg.LinAlgError:  # pragma: no cover - degenerate resample
            continue
    valid = reps[np.isfinite(reps).all(axis=1)]
    out = []
    for j, level in enumerate(lag_levels):
        if len(valid):
            low, high = np.percentile(valid[:, j], [2.5, 97.5])
        else:  # pragma: no cover - no valid replicate
            low = high = float("nan")
        out.append(
            LagCoefficient(
                lag=level,
                coefficient=float(point[j]),
                ci=(float(low), float(high)),
                n_days=int((lag == level).sum()),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Part A2: motive crosswalk
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrosswalkRow:
    """One code of A2's motive crosswalk (destination or origin side)."""

    entd_code: str | None
    emp_code: str | None
    label: str
    share_2008: float
    share_2019: float
    flag: str


def _emp_motive_label(code: str | None) -> str:
    if code is None:
        return "-"
    try:
        return trip_legs.MOTIVE_LABEL_BY_CODE.get(float(code), "-")
    except ValueError:
        return "-"


def motive_crosswalk(
    frames_2008: SurveyFrames, frames_2019: SurveyFrames, side: str
) -> list[CrosswalkRow]:
    """A2's code-by-code crosswalk between ENTD 2008's `V2_` motive codes
    and EMP 2019's, on one trip ``side`` ('destination' or 'origin'),
    with each code's weighted weekday trip share in its own survey.

    The mapping itself is step 11's (`entd2008._PURPOSE_CONVERSION`,
    `docs/data/entd2008.md`'s "Purposes" table). Flags: `2008 only`
    (ENTD code with no 2019 occurrence of its mapped code), `2019 only`
    (EMP code no ENTD code maps to), `unmapped` (ENTD code outside the
    step-11 conversion, converted to NULL), `merged` (several ENTD codes
    map to this one EMP code).
    """
    shares_2008 = frames_2008.aux["raw_motive_shares"][side]
    shares_2019 = frames_2019.aux["raw_motive_shares"][side]
    conversion = entd2008._PURPOSE_CONVERSION
    emp_share_total: dict[str, float] = {}
    for code, share in shares_2019.items():
        emp_share_total[code] = emp_share_total.get(code, 0.0) + share
    targets_by_emp: dict[str, list[str]] = {}
    for entd_code, emp_code in conversion.items():
        targets_by_emp.setdefault(f"{emp_code:g}", []).append(entd_code)

    rows = []
    for entd_code in sorted(
        set(shares_2008) | set(conversion), key=lambda c: (len(c), c)
    ):
        emp_code = conversion.get(entd_code)
        emp_key = f"{emp_code:g}" if emp_code is not None else None
        share_2019 = emp_share_total.get(emp_key, 0.0) if emp_key else 0.0
        if emp_code is None:
            flag = "unmapped (-> NULL motive)"
        elif len(targets_by_emp.get(emp_key, [])) > 1:
            flag = "merged with " + ", ".join(
                c for c in targets_by_emp[emp_key] if c != entd_code
            )
        elif share_2019 == 0.0:
            flag = "2008 only"
        else:
            flag = ""
        rows.append(
            CrosswalkRow(
                entd_code=entd_code,
                emp_code=emp_key,
                label=_emp_motive_label(emp_key),
                share_2008=shares_2008.get(entd_code, 0.0),
                share_2019=share_2019,
                flag=flag,
            )
        )
    mapped_emp_codes = set(targets_by_emp)
    for emp_key in sorted(set(shares_2019) - mapped_emp_codes, key=float):
        rows.append(
            CrosswalkRow(
                entd_code=None,
                emp_code=emp_key,
                label=_emp_motive_label(emp_key),
                share_2008=0.0,
                share_2019=shares_2019[emp_key],
                flag="2019 only",
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Part A3: distances
# ---------------------------------------------------------------------------


def distance_band_index(distance_km: np.ndarray) -> np.ndarray:
    """Band index, with non-finite distances separate (section 9.9)."""
    band = np.searchsorted(
        np.asarray(DISTANCE_BAND_UPPER_KM[:-1]), distance_km, side="right"
    )
    return np.where(np.isfinite(distance_km), band, len(DISTANCE_BAND_LABELS) - 1)


@dataclass(frozen=True)
class DistanceBandRow:
    label: str
    n_trips: int
    share_trips: float
    share_time: float


def distance_band_table(frames: SurveyFrames) -> list[DistanceBandRow]:
    """A3's distribution of weekday trip distances by band: weighted
    share of trips and of time (step-11 corrected distances)."""
    trips = frames.trips
    w = trips["pond_jour"].astype(float)
    time = trips["duration_min"].astype(float)
    band = distance_band_index(trips["distance_km"].astype(float))
    total_w = float(w.sum())
    total_time = float(np.sum(w * time))
    rows = []
    for i, label in enumerate(DISTANCE_BAND_LABELS):
        mask = band == i
        rows.append(
            DistanceBandRow(
                label=label,
                n_trips=int(mask.sum()),
                share_trips=float(w[mask].sum()) / total_w if total_w else 0.0,
                share_time=(
                    float(np.sum(w[mask] * time[mask])) / total_time
                    if total_time
                    else 0.0
                ),
            )
        )
    return rows


@dataclass(frozen=True)
class DistanceDurationRow:
    """Weighted duration quartiles in minutes (section 9.9)."""

    label: str
    mode: str
    n_trips: int
    quartiles: tuple[float, float, float]


def distance_duration_table(frames: SurveyFrames) -> list[DistanceDurationRow]:
    """B4b: duration by band, and by mode in >=80 km (section 9.9)."""
    trips = frames.trips
    bands = distance_band_index(trips["distance_km"].astype(float))
    rows = []
    for i, label in enumerate(DISTANCE_BAND_LABELS):
        modes = ("all modes", *MODE7_LABELS) if label == ">=80 km" else ("all modes",)
        for mode in modes:
            mask = bands == i
            if mode != "all modes":
                mask &= trips["mode7"] == mode
            time = trips["duration_min"][mask].astype(float)
            weight = trips["pond_jour"][mask].astype(float)
            quartiles = (float("nan"),) * 3
            if len(time):
                order = np.argsort(time, kind="stable")
                cumulative = np.cumsum(weight[order])
                indices = np.searchsorted(
                    cumulative, cumulative[-1] * np.array([0.25, 0.5, 0.75])
                )
                q1, median, q3 = time[order][indices]
                quartiles = (float(q1), float(median), float(q3))
            rows.append(DistanceDurationRow(label, mode, int(mask.sum()), quartiles))
    return rows


def _format_b4_durations(a: SurveyFrames, b: SurveyFrames) -> list[str]:
    rows_a = {(r.label, r.mode): r for r in distance_duration_table(a)}
    rows_b = {(r.label, r.mode): r for r in distance_duration_table(b)}
    lines = [
        "### B4b. Trip-duration distributions",
        "",
        "Day-weighted quantiles: first duration reaching 25%, 50% or 75% "
        "of cumulative trip weight; minutes. Unknown distances stay separate. "
        f"Cells below {MIN_CELL_N} trips are suppressed.",
        "",
        "| Band | n 2008 | median min/trip 2008 | n 2019 | median min/trip 2019 |",
        "|---|---|---|---|---|",
    ]
    for label in DISTANCE_BAND_LABELS:
        ra, rb = rows_a[label, "all modes"], rows_b[label, "all modes"]
        lines.append(
            f"| {label} | {ra.n_trips} | "
            f"{_suppress(ra.n_trips, _num(ra.quartiles[1]))} | "
            f"{rb.n_trips} | {_suppress(rb.n_trips, _num(rb.quartiles[1]))} |"
        )
    lines += [
        "",
        "Duration quartiles by mode, >=80 km band:",
        "",
        "| Mode | n 2008 | Q1 2008 | Median 2008 | Q3 2008 | "
        "n 2019 | Q1 2019 | Median 2019 | Q3 2019 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for mode in MODE7_LABELS:
        cells = []
        for rows in (rows_a, rows_b):
            row = rows[">=80 km", mode]
            cells.append(str(row.n_trips))
            cells.extend(_suppress(row.n_trips, _num(q)) for q in row.quartiles)
        lines.append(f"| {mode} | " + " | ".join(cells) + " |")
    return lines


# ---------------------------------------------------------------------------
# Part A4: duration rounding; Part A5: calendar
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoundingRow:
    """A4: weighted share of declared trip durations that are multiples
    of 5/10/15/30 min, for one mode."""

    mode: str
    n_trips: int
    share_mult_5: float
    share_mult_10: float
    share_mult_15: float
    share_mult_30: float


def duration_rounding_table(frames: SurveyFrames) -> list[RoundingRow]:
    """A4's table: declared-duration rounding by mode (weekday trips,
    needs scope, day weights), plus an all-modes row."""
    trips = frames.trips
    w = trips["pond_jour"].astype(float)
    duration = trips["duration_min"].astype(float)
    mode = trips["mode7"].astype(str)

    def _row(label: str, mask: np.ndarray) -> RoundingRow:
        weight = float(w[mask].sum())

        def _share(multiple: float) -> float:
            if weight == 0:
                return float("nan")
            hits = np.isclose(np.mod(duration[mask], multiple), 0.0) | np.isclose(
                np.mod(duration[mask], multiple), multiple
            )
            return float(w[mask][hits].sum()) / weight

        return RoundingRow(
            label, int(mask.sum()), _share(5), _share(10), _share(15), _share(30)
        )

    rows = [_row(m, mode == m) for m in MODE7_LABELS]
    rows.append(_row("all modes", np.ones(len(w), dtype=bool)))
    return rows


@dataclass(frozen=True)
class CalendarMix:
    """A5: weighted month/weekday mix of described days, and the
    school-holiday share where flagged."""

    month_share: dict[int, float]
    weekday_share: dict[int, float]
    holiday_share: float
    n_unknown_month: int


def calendar_mix(frames: SurveyFrames) -> CalendarMix:
    """A5's calendar mix of weekday described days (day weights)."""
    days = frames.days
    w = days["pond_jour"].astype(float)
    months = np.array(
        [
            _FRENCH_MONTH_NUM.get(str(name).strip().lower(), 0)
            for name in days["described_month_name"]
        ]
    )
    weekdays = np.array(
        [
            _FRENCH_WEEKDAY_NUM.get(str(name).strip().lower(), 0)
            for name in days["described_weekday_name"]
        ]
    )
    known_month_weight = float(w[months > 0].sum())
    known_weekday_weight = float(w[weekdays > 0].sum())
    month_share = {
        month: float(w[months == month].sum()) / known_month_weight
        if known_month_weight
        else float("nan")
        for month in range(1, 13)
    }
    weekday_share = {
        weekday: float(w[weekdays == weekday].sum()) / known_weekday_weight
        if known_weekday_weight
        else float("nan")
        for weekday in range(1, 6)
    }
    vac = days["vac_scol"].astype(float)
    return CalendarMix(
        month_share=month_share,
        weekday_share=weekday_share,
        holiday_share=float(np.sum(w * (vac == 1))) / float(w.sum()),
        n_unknown_month=int((months == 0).sum()),
    )


MONTH_LABELS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


def _format_a4(results: dict) -> list[str]:
    lines = [
        "## A4. Survey-duration construction and rounding",
        "",
        "**EMP 2019:** the loader uses the published `K_DEPLOC.DUREE` "
        "(minutes). **ENTD 2008:** it uses `v2_mduree` where numeric, "
        "otherwise `V2_DUREE` (minutes). Neither loader recomputes "
        "arrival minus departure time. The local dictionaries label "
        "`DUREE`/`V2_DUREE` as trip duration but do not establish whether "
        "the producer obtained it from an independent duration declaration "
        "or from declared arrival/departure times. Producer-side construction "
        "remains unverified; rounding here must not be interpreted as proof "
        "of independently declared durations.",
        "",
        "Weighted share of published survey trip durations that are exact "
        "multiples of 5, 10, 15 and 30 minutes, by year and trip mode "
        "(weekday trips, needs scope).",
        "",
        "| Mode | n 2008 | x5 | x10 | x15 | x30 | n 2019 | x5 | x10 | x15 | x30 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    rows_2008 = {r.mode: r for r in results["rounding_2008"]}
    rows_2019 = {r.mode: r for r in results["rounding_2019"]}
    for mode in [*MODE7_LABELS, "all modes"]:
        r8, r9 = rows_2008[mode], rows_2019[mode]

        def _cells(row: RoundingRow) -> str:
            if row.n_trips < MIN_CELL_N:
                return f"{row.n_trips} | - | - | - | -"
            return (
                f"{row.n_trips} | {_pct(row.share_mult_5)} | "
                f"{_pct(row.share_mult_10)} | {_pct(row.share_mult_15)} | "
                f"{_pct(row.share_mult_30)}"
            )

        lines.append(f"| {mode} | {_cells(r8)} | {_cells(r9)} |")
    return lines


def _format_a5(results: dict) -> list[str]:
    mix_2008: CalendarMix = results["calendar_2008"]
    mix_2019: CalendarMix = results["calendar_2019"]
    lines = [
        "## A5. Calendar of described days",
        "",
        "Weighted month and weekday mix of the weekday described days "
        "with trips, by year, and the school-holiday share (`V2_VAC_SCOL`"
        " / `NEW_VAC_SCOL`).",
        "",
        "| Month | " + " | ".join(MONTH_LABELS.values()) + " |",
        "|---" * 13 + "|",
        "| 2008 | "
        + " | ".join(_pct(mix_2008.month_share[m]) for m in range(1, 13))
        + " |",
        "| 2019 | "
        + " | ".join(_pct(mix_2019.month_share[m]) for m in range(1, 13))
        + " |",
        "",
        "| Weekday | Mon | Tue | Wed | Thu | Fri |",
        "|---|---|---|---|---|---|",
        "| 2008 | "
        + " | ".join(_pct(mix_2008.weekday_share[d]) for d in range(1, 6))
        + " |",
        "| 2019 | "
        + " | ".join(_pct(mix_2019.weekday_share[d]) for d in range(1, 6))
        + " |",
        "",
        f"School-holiday share of described days: "
        f"{_pct(mix_2008.holiday_share)} in 2008, "
        f"{_pct(mix_2019.holiday_share)} in 2019 (days with at least one "
        "trip flagged as school holiday). Days with an unknown described "
        f"month: {mix_2008.n_unknown_month} in 2008, "
        f"{mix_2019.n_unknown_month} in 2019.",
    ]
    return lines


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _pct(value: float) -> str:
    return "-" if not np.isfinite(value) else f"{100.0 * value:.1f}%"


def _num(value: float, decimals: int = 1) -> str:
    return "-" if value is None or not np.isfinite(value) else f"{value:.{decimals}f}"


def _suppress(n: int, text: str) -> str:
    """Step-11 suppression: keep the true n, blank the value below
    ``MIN_CELL_N`` respondents."""
    return text if n >= MIN_CELL_N else "-"


def _equivalence_verdict(ci: tuple[float, float], margin: float) -> str:
    """Classify a 90% interval against a symmetric equivalence margin."""
    lower, upper = 1.0 - margin, 1.0 + margin
    if ci[0] >= lower and ci[1] <= upper:
        return "equivalent"
    if ci[1] < lower or ci[0] > upper:
        return "different"
    return "inconclusive"


def _lag_row_cells(row: LagRow) -> str:
    n = row.n_days
    return (
        f"| {row.label} | {n} | {_suppress(n, _pct(row.weighted_share))} | "
        f"{_suppress(n, _num(row.trips_per_day, 2))} | "
        f"{_suppress(n, _num(row.minutes_per_trip))} | "
        f"{_suppress(n, _num(row.time_per_day_min))} | "
        f"{_suppress(n, _pct(row.share_trips_under_5_min))} | "
        f"{_suppress(n, _pct(row.share_trips_under_1_km))} |"
    )


def _format_a1(results: dict) -> list[str]:
    lines = [
        "## A1. Recall lag (EMP 2019)",
        "",
        "EMP 2019 describes a day drawn from the 7 days before the visit "
        "(`MDATE_delai`, days between the described day and the "
        "interview); ENTD 2008 describes the last weekday before the "
        "second visit (`MDATENQ2V` - `V2_DATESEMREF`: lag 1 except after "
        "a weekend, where the calendar lag is 3). Weekday described days "
        "with trips, needs scope, day weights.",
        "",
        "| Lag (days) | n | Weighted share | Trips/day | Min/trip | "
        "Time/day (min) | Trips < 5 min | Trips < 1 km |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in results["lag_table"]:
        lines.append(_lag_row_cells(row))
    lines += [
        "",
        "EMP 2019 at lag 1 next to ENTD 2008 (all weekday days):",
        "",
        "| Survey | n | Trips/day | Min/trip | Time/day (min) | "
        "Trips < 5 min | Trips < 1 km |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, row in (
        ("EMP 2019, lag 1", results["lag_table"][0]),
        ("EMP 2019, all lags", results["lag_table"][-1]),
        ("ENTD 2008", results["entd_overall"]),
    ):
        n = row.n_days
        lines.append(
            f"| {label} | {n} | {_suppress(n, _num(row.trips_per_day, 2))} | "
            f"{_suppress(n, _num(row.minutes_per_trip))} | "
            f"{_suppress(n, _num(row.time_per_day_min))} | "
            f"{_suppress(n, _pct(row.share_trips_under_5_min))} | "
            f"{_suppress(n, _pct(row.share_trips_under_1_km))} |"
        )
    lines += [
        "",
        "Weighted regression on lag dummies (reference lag 1), with "
        "population-category x density-class controls and described-day weekday "
        "dummies (first observed weekday as reference; unknown weekdays excluded), "
        "household-bootstrap "
        "95% CIs:",
        "",
        "| Lag | Δ time/day (min) | 95% CI | Δ trips/day | 95% CI | n |",
        "|---|---|---|---|---|---|",
    ]
    time_by_lag = {c.lag: c for c in results["lag_regression_time"]}
    trips_by_lag = {c.lag: c for c in results["lag_regression_trips"]}
    for lag in range(2, 8):
        t, tr = time_by_lag[lag], trips_by_lag[lag]
        lines.append(
            f"| {lag} | {_num(t.coefficient)} | "
            f"[{_num(t.ci[0])}, {_num(t.ci[1])}] | "
            f"{_num(tr.coefficient, 2)} | "
            f"[{_num(tr.ci[0], 2)}, {_num(tr.ci[1], 2)}] | {t.n_days} |"
        )
    return lines


def _format_a2(results: dict) -> list[str]:
    lines = [
        "## A2. Motive crosswalk",
        "",
        "Step 11's code-by-code conversion "
        "(`docs/data/entd2008.md`'s \"Purposes\" table), with each code's "
        "weighted share of weekday trips in its own survey. Shares are of "
        "raw trip codes before the needs scope; `return home` codes are "
        "re-assigned to the outward motive downstream, as in step 11.",
        "",
    ]
    for side in ("destination", "origin"):
        lines += [
            f"### {side.capitalize()} motives",
            "",
            "| ENTD 2008 code | share 2008 | EMP 2019 code | label | "
            "share 2019 | flag |",
            "|---|---|---|---|---|---|",
        ]
        for row in results["crosswalk"][side]:
            lines.append(
                f"| {row.entd_code or '-'} | {_pct(row.share_2008)} | "
                f"{row.emp_code or '-'} | {row.label} | "
                f"{_pct(row.share_2019)} | {row.flag} |"
            )
        lines.append("")
    removal_2008 = results["needs_removal_2008"]
    removal_2019 = results["needs_removal_2019"]
    local_2008 = results["local_scope_removal_2008"]
    local_2019 = results["local_scope_removal_2019"]
    lines += [
        "### Needs scope",
        "",
        "Weighted share of weekday trips and time excluded from the reference "
        "scope (non-local trips and motives 7.6-7.8 and 8.x):",
        "",
        "| Survey | Trips removed | Time removed |",
        "|---|---|---|",
        f"| ENTD 2008 | {_pct(removal_2008['share_trips_removed'])} | "
        f"{_pct(removal_2008['share_time_removed'])} |",
        f"| EMP 2019 | {_pct(removal_2019['share_trips_removed'])} | "
        f"{_pct(removal_2019['share_time_removed'])} |",
        "",
        "The local-trip rule's additional removal relative to the former "
        "motive-only scope, averaged over that scope's weekday person-days "
        "with trips (including days with no local trips):",
        "",
        "| Survey | Days | Non-local needs trips/day removed | "
        "Non-local needs min/day removed |",
        "|---|---:|---:|---:|",
        f"| ENTD 2008 | {local_2008['n_days']} | "
        f"{_num(local_2008['trips_per_day_removed'], 2)} | "
        f"{_num(local_2008['minutes_per_day_removed'])} |",
        f"| EMP 2019 | {local_2019['n_days']} | "
        f"{_num(local_2019['trips_per_day_removed'], 2)} | "
        f"{_num(local_2019['minutes_per_day_removed'])} |",
    ]
    return lines


def _format_a3(results: dict) -> list[str]:
    doc_2019 = results["distance_doc_2019"]
    doc_2008 = results["distance_doc_2008"]
    lines = [
        "## A3. Distances",
        "",
        "**How each survey's distance was produced.** ENTD 2008: "
        "`V2_MDISTTOT` is the respondent's declared distance; the "
        "producer's undocumented correction `distcor` (filled for "
        f"{_pct(doc_2008['n_corrected'] / doc_2008['n_trips'])} of weekday "
        "trips) replaces it where present (step 11's rule); `V2_DVO_LOC` "
        "is a computed crow-fly distance for local trips "
        f"({_pct(doc_2008['n_crow_fly'] / doc_2008['n_trips'])} filled). "
        "EMP 2019: `MDISTTOT_decl` is declared "
        f"({_pct(doc_2019['n_declared'] / doc_2019['n_trips'])} filled), "
        "`MDISTTOT_fin` is the producer's consolidated distance (100% "
        "filled; producer-corrected against the declared value for "
        f"{_pct(doc_2019['n_producer_corrected'] / doc_2019['n_trips'])} "
        "of trips, `indic_dist_corr`), `dVO_ORIDES` is a computed "
        "crow-fly distance and `dist_ign` an IGN route distance "
        f"({_pct(doc_2019['n_route'] / doc_2019['n_trips'])} filled). The "
        "measurement therefore changed between 2008 (declared, with a "
        "partial correction) and 2019 (declared, consolidated by the "
        "producer against geocoded route distances). Both surveys then "
        "receive step 11's speed-plausibility correction; the bands "
        "below use the corrected distances.",
        "",
        "| Band | n 2008 | trips 2008 | time 2008 | n 2019 | trips 2019 | time 2019 |",
        "|---|---|---|---|---|---|---|",
    ]
    bands_2008 = {r.label: r for r in results["distance_bands_2008"]}
    bands_2019 = {r.label: r for r in results["distance_bands_2019"]}
    for label in DISTANCE_BAND_LABELS:
        b8, b9 = bands_2008[label], bands_2019[label]
        lines.append(
            f"| {label} | {b8.n_trips} | "
            f"{_suppress(b8.n_trips, _pct(b8.share_trips))} | "
            f"{_suppress(b8.n_trips, _pct(b8.share_time))} | {b9.n_trips} | "
            f"{_suppress(b9.n_trips, _pct(b9.share_trips))} | "
            f"{_suppress(b9.n_trips, _pct(b9.share_time))} |"
        )
    lines += [
        "",
        "**80-km check.** Local-trip tables and the crow-fly distance "
        "from home: ENTD 2008 local weekday trips (`V2_DLOCAL` = 1) have "
        f"{doc_2008['n_local_crow_fly_over_80']} of {doc_2008['n_local']} "
        "trips with a crow-fly O-D distance above 80 km (max "
        f"{_num(doc_2008['max_local_crow_fly_km'])} km; max route "
        f"distance {_num(doc_2008['max_local_route_km'])} km). EMP 2019 "
        "local weekday trips (`mobloc` = 1) have "
        f"{doc_2019['n_local_crow_fly_over_80']} of {doc_2019['n_local']} "
        "with a crow-fly O-D distance above 80 km (max "
        f"{_num(doc_2019['max_local_crow_fly_km'])} km; max route "
        f"distance {_num(doc_2019['max_local_route_km'])} km). The 80-km "
        "rule is defined on the distance between home and the trip ends, "
        "not on the O-D crow-fly distance itself, so a small overshoot "
        "of the O-D distance is expected; both tables are consistent "
        "with an 80-km-from-home scope.",
    ]
    return lines


def write_markdown(md_path: Path, out_dir: Path, results: dict) -> None:
    """Write the step-12 report."""
    lines = [
        "# Step 12: what explains the variation of daily travel time",
        "",
        "Generated by `python -m mobgrid.budget.variation_report`. Unit of "
        "analysis: weekday person-days with at least one local trip in the "
        "needs "
        "scope, day weights (`POND_JOUR`/`POIDS_JOUR`), as in step 11. "
        "Bootstrap intervals resample households within each survey, "
        f"independently ({results['n_reps']} replicates). Cells of fewer "
        f"than {MIN_CELL_N} respondents print their true n with `-` for "
        "the values.",
        "",
        f"Sample: ENTD 2008, {results['n_days_2008']} weekday days with "
        f"trips ({results['n_trips_2008']} trips); EMP 2019, "
        f"{results['n_days_2019']} days ({results['n_trips_2019']} "
        "trips)."
        + (
            f" Household sample: {results['sample_pct']:g}% (smoke run)."
            if results.get("sample_pct")
            else ""
        ),
        "",
        "## Choices made",
        "",
        *[f"- {choice}" for choice in results["choices"]],
        "",
        *_format_a1(results),
        "",
        *_format_a2(results),
        "",
        *_format_a3(results),
        "",
        *_format_a4(results),
        "",
        *_format_a5(results),
    ]
    for extra in results.get("extra_sections", []):
        lines += ["", *extra]
    if results.get("figures"):
        lines += ["", "## Figures", ""]
        for path in results["figures"]:
            try:
                relative = path.relative_to(md_path.parent)
            except ValueError:
                relative = path
            lines.append(f"![{path.stem}]({relative.as_posix()})")
            lines.append("")
            if path.stem == "fig_b7a_waterfall":
                lines += [
                    "B7a allocates the behavioural remainder proportionally "
                    "to B2's terms; it is not a sequential composition-adjusted "
                    "decomposition. The distance-selection term keeps all-trip "
                    "time separate from distance-known-trip time. At zero net "
                    "change, proportional allocation is undefined: B2 terms "
                    "are retained and an explicit allocation residual closes "
                    "the composition offset.",
                    "",
                ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


#: Standing "Choices made" entries (prompt: "If a variable is missing or
#: ambiguous, choose, write the choice in the report under 'Choices
#: made', and continue").
BASE_CHOICES = [
    "The reference needs scope includes local trips only (`mobloc = 1`; "
    "ENTD 2008 `V2_DLOCAL = 1`). Non-local needs trips are excluded; the "
    "all-trips sensitivity in B2 keeps them and every motive.",
    "ENTD 2008's recall lag uses the second visit (`MDATENQ2V`, when "
    "trips are collected) minus the described reference weekday "
    "(`V2_DATESEMREF`); the first visit (`DATENQ`) precedes the "
    "described day.",
    "EMP 2019 days with a missing `MDATE_delai` (about 3% of "
    "respondents) are excluded from the lag-specific rows and "
    "regressions, kept everywhere else.",
    "Household cars are not in ENTD 2008's four public step-11 tables: "
    "B1's V3 variant falls back to V2 for the 2008 -> 2019 pair and is "
    "computed fully within EMP 2019 pairs (`JNBVEH`).",
    "Both surveys use the harmonised trip-motive rule: returns home or to "
    "a residence (codes 1.1-1.3) take the trip's origin motive. Per SDES's "
    "November 2024 note, EMP 2019's `MOT_SEQ_COMPL` is the dominant activity "
    "of a sequence and is reported only once per unique `IDENT_SEQ`, not "
    "used as a trip motive.",
    "Residence density uses the INSEE grid in both years (ENTD 2008's "
    "2020-zoning SDES supplement, EMP 2019's published grid). The SDES "
    "tables contain no commune codes, so C2 crow-fly distances are not "
    "recomputed.",
    "The motive crosswalk reports raw code shares before the needs "
    "scope and before the return-trip motive reassignment, so both "
    "surveys' code inventories are visible.",
    "EMP 2019 declared distances have unit/coding errors and are excluded "
    "from the 2008 -> 2019 distance comparison.",
    "C6 residence classes use the shared 2020-zoning fields "
    f"({', '.join(RESIDENCE_ZONING_VARIABLES)}) in EMP's `TCM_MEN` and "
    "ENTD's `Q_TCM_MEN_ENTD08_zon20_public.csv`. `CATCOM_AA_RES` uses "
    "INSEE's CATEAAV2020 classes: 11 = commune-centre, 12 = other commune "
    "of the main pole, 13 = commune of a secondary pole, 20 = commune of "
    "the crown, and 30 = commune outside city attraction. Codes 11/12/13 "
    "are grouped as pôle, 20 as couronne, and 30 as hors attraction; "
    "unmatched codes fall back to the INSEE residence-density grid. "
    "The 1994 classes come from the older urban-area zoning, while the "
    "2008 and 2019 classes come from the 2020 attraction-area zoning, so "
    "the 1994 comparison is approximate. CATEAAV2020 has no multipolarised "
    "class; the 1994 couronne and multipolarisée values are merged using "
    "trip weights, and secondary-pole communes (13) are counted as pôle. "
    "Car-driver density bands use the residence grid class "
    "(`DENSITECOM_RES`), not a trip-end class.",
    "Distance bands use step 11's corrected distances "
    "(`trip_legs.distance_km`): the speed-plausibility correction "
    "replaces implausible declared distances, as in every step-11 "
    "table.",
    "Missing distances form a separate unknown-distance band. N and T "
    "include all trips; L and v use distance-known trips. Coverage is "
    "day-weighted at trip level, and the selection residual is explicit "
    "rather than attributed to speed.",
    "The waterfall figure shows B1 V2's composition effect, then the "
    "behavioural remainder split in proportion to B2's trips / km per "
    "trip / speed / selection terms (the decompositions are not nested). "
    "At zero total change, an explicit allocation residual closes the plot.",
]


def run(
    out_dir: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    n_reps: int = 200,
    seed: int = 0,
    emp2019_data_path: Path | None = None,
    entd2008_data_path: Path | None = None,
    entd2008_zoning_data_path: Path | None = None,
    sample_pct: float | None = None,
) -> dict:
    """Compute every step-12 statistic and figure; returns the results
    dict consumed by ``write_markdown`` and the tests."""
    out_dir.mkdir(parents=True, exist_ok=True)
    config = load_energy_config(config_path)
    if entd2008_zoning_data_path is None:
        raise ValueError(
            "ENTD 2008's 2020-zoning data path is required for the grid comparison"
        )
    frames_2008 = load_frames(
        entd2008,
        entd2008_data_path,
        config,
        density_source="grid",
        zoning_data_path=entd2008_zoning_data_path,
        sample_pct=sample_pct,
    )
    frames_2019 = load_frames(
        emp2019,
        emp2019_data_path,
        config,
        density_source="grid",
        sample_pct=sample_pct,
    )
    frames_2019_grid = frames_2019
    variation_config = variation.load_variation_config(
        ROOT / "config" / "variation.yaml"
    )
    results: dict = {
        "n_reps": n_reps,
        "seed": seed,
        "sample_pct": sample_pct,
        "equivalence_margin": variation_config.equivalence_margin,
        "secondary_equivalence_margin": (variation_config.secondary_equivalence_margin),
        "choices": list(BASE_CHOICES),
        "n_days_2008": len(frames_2008.days["pond_jour"]),
        "n_trips_2008": len(frames_2008.trips["pond_jour"]),
        "n_days_2019": len(frames_2019.days["pond_jour"]),
        "n_trips_2019": len(frames_2019.trips["pond_jour"]),
        "official_scope_2008": _official_scope_estimates(
            frames_2008, n_reps=n_reps, seed=seed
        ),
        "official_scope_2019": _official_scope_estimates(
            frames_2019, n_reps=n_reps, seed=seed
        ),
        # A1
        "lag_table": recall_lag_table(frames_2019),
        "entd_overall": survey_overall_row(frames_2008, "ENTD 2008"),
        "lag_regression_time": lag_regression(
            frames_2019, "total_time_min", n_reps=n_reps, seed=seed
        ),
        "lag_regression_trips": lag_regression(
            frames_2019, "trips_per_day", n_reps=n_reps, seed=seed
        ),
        # A2
        "crosswalk": {
            side: motive_crosswalk(frames_2008, frames_2019, side)
            for side in ("destination", "origin")
        },
        "needs_removal_2008": frames_2008.aux["needs_scope_removal"],
        "needs_removal_2019": frames_2019.aux["needs_scope_removal"],
        "local_scope_removal_2008": frames_2008.aux["local_scope_removal"],
        "local_scope_removal_2019": frames_2019.aux["local_scope_removal"],
        # A3
        "distance_doc_2008": frames_2008.aux["distance_doc"],
        "distance_doc_2019": frames_2019.aux["distance_doc"],
        "distance_bands_2008": distance_band_table(frames_2008),
        "distance_bands_2019": distance_band_table(frames_2019),
        # A4 and A5
        "rounding_2008": duration_rounding_table(frames_2008),
        "rounding_2019": duration_rounding_table(frames_2019),
        "calendar_2008": calendar_mix(frames_2008),
        "calendar_2019": calendar_mix(frames_2019),
        "extra_sections": [],
        "figures": [],
    }
    _run_part_b(
        results,
        frames_2008,
        frames_2019,
        frames_2019_grid,
        out_dir,
        n_reps=n_reps,
        seed=seed,
    )
    results["extra_sections"].append(
        measurement_checks(
            frames_2008,
            frames_2019,
            config=variation_config.measurement,
            n_reps=n_reps,
            seed=seed,
            results=results,
        )
    )
    results["measurement_ledger"] = measurement_ledger(
        frames_2008,
        frames_2019,
        results,
        config=variation_config.measurement,
        n_reps=n_reps,
        seed=seed,
    )
    results["extra_sections"].append(
        _format_measurement_ledger(results["measurement_ledger"])
    )
    results["extra_sections"].append(
        _format_official_scope(
            results["official_scope_2008"], results["official_scope_2019"]
        )
    )
    results["extra_sections"].append(
        _format_c6(
            frames_2008,
            frames_2019,
            n_reps=n_reps,
            seed=seed,
        )
    )
    return results


# ---------------------------------------------------------------------------
# Part B helpers: frames -> variation primitives
# ---------------------------------------------------------------------------


def person_days_from_frames(
    frames: SurveyFrames, mask: np.ndarray | None = None
) -> variation.PersonDays:
    """``variation.PersonDays`` of (a mask of) one survey's person-days."""
    days = frames.days
    sel = np.ones(len(days["pond_jour"]), dtype=bool) if mask is None else mask
    return variation.PersonDays(
        weight=days["pond_jour"][sel].astype(float),
        trips=days["trips_per_day"][sel].astype(float),
        distance_km=days["total_distance_km"][sel].astype(float),
        time_min=days["total_time_min"][sel].astype(float),
        household=days["ident_men"][sel],
        distance_trips=days["distance_trips"][sel].astype(float),
        distance_time_min=days["distance_time_min"][sel].astype(float),
    )


@dataclass(frozen=True)
class B2Row:
    """One B2 row: the trips x km x speed split of the daily-time change
    for one group of person-days (overall or one category)."""

    group: str
    n_a: int
    n_b: int
    result: variation.TripTimeDecompositionBootstrap | None
    unavailable_reason: str | None = None
    time_ratio: float | None = None
    time_ratio_ci90: tuple[float, float] | None = None


def subset_frames(frames: SurveyFrames, **conditions: object) -> SurveyFrames:
    """A new ``SurveyFrames`` restricted to the person-days (and their
    trips) matching ``conditions`` on the shared day/trip columns, e.g.
    ``population_category='employed'``, ``home_density='dense'``,
    ``income_quintile='q1'``, ``is_idf=True`` or ``recall_lag=1``."""

    def _mask(table: dict[str, np.ndarray]) -> np.ndarray:
        mask = np.ones(len(table["pond_jour"]), dtype=bool)
        for column, value in conditions.items():
            if isinstance(value, bool):
                mask &= table[column].astype(bool) == value
            elif isinstance(value, (int, float)):
                mask &= table[column].astype(float) == float(value)
            else:
                mask &= table[column].astype(str) == str(value)
        return mask

    day_mask = _mask(frames.days)
    trip_mask = _mask(frames.trips)
    return SurveyFrames(
        name=frames.name,
        days={k: v[day_mask] for k, v in frames.days.items()},
        trips={k: v[trip_mask] for k, v in frames.trips.items()},
        aux=frames.aux,
    )


def b2_decompositions(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    *,
    n_reps: int,
    seed: int,
    categories: tuple[str, ...] | None = None,
    include_time_ratio: bool = False,
) -> list[B2Row]:
    """B2 (``T = N . L / v``) overall and by population category, with
    independent household-bootstrap CIs; a degenerate group (no days or
    zero totals on either side) yields ``result=None``. ``categories=()``
    keeps the overall row only."""
    rows = []
    if categories is None:
        categories = daily_energy.POPULATION_CATEGORIES
    for category in (None, *categories):
        if category is None:
            mask_a = np.ones(len(frames_a.days["pond_jour"]), dtype=bool)
            mask_b = np.ones(len(frames_b.days["pond_jour"]), dtype=bool)
            label = "overall"
        else:
            mask_a = frames_a.days["population_category"] == category
            mask_b = frames_b.days["population_category"] == category
            label = category
        result = None
        unavailable_reason = "no person-days in one or both groups"
        if mask_a.any() and mask_b.any():
            try:
                result = variation.bootstrap_decompose(
                    person_days_from_frames(frames_a, mask_a),
                    person_days_from_frames(frames_b, mask_b),
                    n_reps=n_reps,
                    seed=seed,
                )
            except ValueError as exc:
                unavailable_reason = str(exc)
        time_ratio = None
        time_ratio_ci90 = None
        if (
            include_time_ratio
            and result is not None
            and min(int(mask_a.sum()), int(mask_b.sum())) >= MIN_CELL_N
        ):
            ratio = _time_ratio_ci(
                frames_a,
                frames_b,
                mask_a,
                mask_b,
                n_reps=n_reps,
                seed=seed,
            )
            if ratio is not None:
                time_ratio, time_ratio_ci90 = ratio
        rows.append(
            B2Row(
                group=label,
                n_a=int(mask_a.sum()),
                n_b=int(mask_b.sum()),
                result=result,
                unavailable_reason=unavailable_reason if result is None else None,
                time_ratio=time_ratio,
                time_ratio_ci90=time_ratio_ci90,
            )
        )
    return rows


def _time_ratio_ci(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    *,
    n_reps: int,
    seed: int,
) -> tuple[float, tuple[float, float]] | None:
    """Return the 2019/2008 daily-time ratio and 90% household-bootstrap CI."""
    days_a, days_b = frames_a.days, frames_b.days
    if min(int(mask_a.sum()), int(mask_b.sum())) < MIN_CELL_N:
        return None
    weight_a = days_a["pond_jour"][mask_a].astype(float)
    weight_b = days_b["pond_jour"][mask_b].astype(float)
    time_a = days_a["total_time_min"][mask_a].astype(float)
    time_b = days_b["total_time_min"][mask_b].astype(float)
    if (
        np.average(time_a, weights=weight_a) <= 0
        or np.average(time_b, weights=weight_b) <= 0
    ):
        return None
    return daily_energy.bootstrap_ratio_ci(
        days_a["ident_men"][mask_a],
        weight_a,
        time_a,
        days_b["ident_men"][mask_b],
        weight_b,
        time_b,
        n_reps=n_reps,
        seed=seed,
    )


def _ci_cell(
    value: float, ci: tuple[float, float] | np.ndarray, decimals: int = 1
) -> str:
    return f"{_num(value, decimals)} [{_num(ci[0], decimals)}, {_num(ci[1], decimals)}]"


def _format_b2(
    rows: list[B2Row],
    label_a: str,
    label_b: str,
    title: str | None = None,
    *,
    distance_description: str = "step 11's corrected distances",
    equivalence_margin: float | None = None,
    secondary_equivalence_margin: float | None = None,
) -> list[str]:
    equivalence_columns = equivalence_margin is not None
    if equivalence_columns != (secondary_equivalence_margin is not None):
        raise ValueError("both equivalence margins must be provided together")
    if equivalence_columns:
        assert equivalence_margin is not None
        assert secondary_equivalence_margin is not None
    lines = [
        title or f"## B2. Trips x distance x speed, {label_a} -> {label_b}",
        "",
        "N and T use all trips. L and v use distance-known trips only "
        "(km per trip and km per minute, ratios of weighted totals); "
        "coverage is their weighted share of all trips. "
        "T = N . L / v . R, where R = (T/N)/(L/v) is the "
        "all-trip/known-distance mean-duration ratio. "
        "Δln T = Δln N + Δln L - Δln v + Δln R, each "
        "term expressed in minutes as ΔT x (term / Δln T). Distances are "
        f"{distance_description}. Household-bootstrap 95% CIs, "
        "surveys resampled independently.",
        "",
        f"| Group | n {label_a} | n {label_b} | T {label_a} | T {label_b} "
        "| Δ (min) [CI] | trips (min) [CI] | km/trip (min) [CI] | "
        "speed (min) [CI] | selection R (min) [CI] | "
        f"distance-known share {label_a} | distance-known share {label_b} |",
    ]
    if equivalence_columns:
        lines[2] += (
            " Daily-time ratios are 2019/2008 with 90% household-bootstrap "
            "CIs; equivalence requires the full interval inside the margin."
        )
        lines[4] = lines[4][:-1] + (
            f" | Time ratio {label_b}/{label_a} | 90% CI | "
            f"Equivalent at ±{equivalence_margin:.0%} | "
            f"Equivalent at ±{secondary_equivalence_margin:.0%} |"
        )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
        + ("---|---|---|---|" if equivalence_columns else "")
    )
    for row in rows:
        if row.result is None or min(row.n_a, row.n_b) < MIN_CELL_N:
            cells = [
                row.group,
                str(row.n_a),
                str(row.n_b),
                *("-" for _ in range(9)),
            ]
            if equivalence_columns:
                cells.extend("-" for _ in range(4))
            lines.append("| " + " | ".join(cells) + " |")
            continue
        point = row.result.point
        cells = [
            row.group,
            str(row.n_a),
            str(row.n_b),
            _num(point.time_a_min),
            _num(point.time_b_min),
            _ci_cell(point.delta_min, row.result.delta_ci),
            _ci_cell(point.trips_min, row.result.trips_ci),
            _ci_cell(point.distance_min, row.result.distance_ci),
            _ci_cell(point.speed_min, row.result.speed_ci),
            _ci_cell(point.selection_min, row.result.selection_ci),
            _pct(point.distance_share_a),
            _pct(point.distance_share_b),
        ]
        if equivalence_columns:
            if row.time_ratio is None or row.time_ratio_ci90 is None:
                cells.extend(("-", "-", "-", "-"))
            else:
                ci = row.time_ratio_ci90
                cells.extend(
                    (
                        f"{row.time_ratio:.3f}",
                        f"[{ci[0]:.3f}, {ci[1]:.3f}]",
                        _equivalence_verdict(ci, equivalence_margin),
                        _equivalence_verdict(ci, secondary_equivalence_margin),
                    )
                )
        lines.append("| " + " | ".join(cells) + " |")
    unavailable = [row for row in rows if row.result is None]
    if unavailable:
        lines += ["", "Unavailable decompositions (not zero effects):"]
        lines += [f"- {row.group}: {row.unavailable_reason}." for row in unavailable]
    return lines


def trip_sample_from_frames(
    frames: SurveyFrames,
    group_labels: np.ndarray,
    day_mask: np.ndarray | None = None,
    trip_mask: np.ndarray | None = None,
) -> variation.TripSample:
    """``variation.TripSample`` of (a mask of) one survey's person-days
    and trips; ``group_labels`` is one label per (unmasked) trip row."""
    days, trips = frames.days, frames.trips
    dsel = np.ones(len(days["pond_jour"]), dtype=bool) if day_mask is None else day_mask
    tsel = (
        np.ones(len(trips["pond_jour"]), dtype=bool) if trip_mask is None else trip_mask
    )
    return variation.TripSample(
        day_weight=days["pond_jour"][dsel].astype(float),
        day_household=days["ident_men"][dsel],
        trip_weight=trips["pond_jour"][tsel].astype(float),
        trip_household=trips["ident_men"][tsel],
        trip_minutes=trips["duration_min"][tsel].astype(float),
        trip_km=trips["distance_km"][tsel].astype(float),
        trip_group=np.asarray(group_labels)[tsel],
    )


def shift_share_by(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    column: str,
    *,
    day_mask_a: np.ndarray | None = None,
    trip_mask_a: np.ndarray | None = None,
    day_mask_b: np.ndarray | None = None,
    trip_mask_b: np.ndarray | None = None,
    n_reps: int,
    seed: int,
) -> variation.ShiftShareBootstrap:
    """B3/B4 shift-share between two surveys (or two groups) by a trip
    grouping ``column`` ('mode7', 'motive_group' or 'distance_band')."""

    def _labels(frames: SurveyFrames) -> np.ndarray:
        if column == "distance_band":
            return np.asarray(DISTANCE_BAND_LABELS)[
                distance_band_index(frames.trips["distance_km"].astype(float))
            ]
        if column == "motive_group":
            return np.array([motive_group_label(code) for code in frames.trips[column]])
        return frames.trips[column].astype(str)

    return variation.bootstrap_shift_share(
        trip_sample_from_frames(frames_a, _labels(frames_a), day_mask_a, trip_mask_a),
        trip_sample_from_frames(frames_b, _labels(frames_b), day_mask_b, trip_mask_b),
        n_reps=n_reps,
        seed=seed,
    )


def motive_group_label(code) -> str:
    """Name of a harmonised top-level motive group code ('1'-'9'), or
    'unknown' for a missing/unparsed motive."""
    try:
        return MOTIVE_GROUP_LABELS.get(int(str(code)), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _group_counts(
    frames: SurveyFrames, column: str, trip_mask: np.ndarray | None = None
) -> dict[str, int]:
    if column == "distance_band":
        labels = np.asarray(DISTANCE_BAND_LABELS)[
            distance_band_index(frames.trips["distance_km"].astype(float))
        ]
    elif column == "motive_group":
        labels = np.array([motive_group_label(code) for code in frames.trips[column]])
    else:
        labels = frames.trips[column].astype(str)
    if trip_mask is not None:
        labels = labels[trip_mask]
    values, counts = np.unique(labels, return_counts=True)
    return dict(zip(values.tolist(), counts.tolist(), strict=True))


def _format_shift_share(
    result: variation.ShiftShareBootstrap,
    counts_a: dict[str, int],
    counts_b: dict[str, int],
    *,
    title: str,
    group_name: str,
    label_a: str,
    label_b: str,
    group_order: tuple[str, ...] | None = None,
    within_label: str = "within",
    intro: str = "",
) -> list[str]:
    """One shift-share section: the aggregate identity with CIs, then the
    per-group terms (suppressed below `MIN_CELL_N` trips)."""
    point = result.point
    lines = [
        title,
        "",
        intro
        or (
            "ΔT = (N_B - N_A) . M_A + N_B . (M_B - M_A); the second term "
            "splits into mode mix Σ (s_B - s_A) . m_A, within Σ s_A . "
            "(m_B - m_A) and interaction Σ (s_B - s_A) . (m_B - m_A), all "
            "scaled by N_B into minutes per day. Household-bootstrap 95% "
            "CIs."
        ),
        "N, T and mean durations use all trips. Km/trip and speed use "
        "distance-known trips only; their weighted shares are shown. "
        "The within selection residual separates changes in the "
        "all-trip/known-distance mean-duration ratio from speed. "
        "A group with no usable distances has no km/speed split.",
        "",
        "| Term | Minutes/day | 95% CI |",
        "|---|---|---|",
        f"| ΔT | {_num(point.delta_min)} | "
        f"[{_num(result.delta_ci[0])}, {_num(result.delta_ci[1])}] |",
        f"| trips volume | {_num(point.volume_min)} | "
        f"[{_num(result.volume_ci[0])}, {_num(result.volume_ci[1])}] |",
        f"| {group_name} mix | {_num(point.mix_min)} | "
        f"[{_num(result.mix_ci[0])}, {_num(result.mix_ci[1])}] |",
        f"| {within_label} | {_num(point.within_min)} | "
        f"[{_num(result.within_ci[0])}, {_num(result.within_ci[1])}] |",
        f"| interaction | {_num(point.interaction_min)} | "
        f"[{_num(result.interaction_ci[0])}, {_num(result.interaction_ci[1])}] |",
        "",
        f"Trips per day: {_num(point.trips_a, 2)} ({label_a}) -> "
        f"{_num(point.trips_b, 2)} ({label_b}); minutes per trip: "
        f"{_num(point.minutes_per_trip_a)} -> {_num(point.minutes_per_trip_b)}.",
        "",
        f"| {group_name} | n {label_a} | n {label_b} | share {label_a} | "
        f"share {label_b} | min/trip {label_a} | min/trip {label_b} | "
        "mix (min) | within (min) | of which km/trip | of which speed | "
        "interaction (min) | "
        f"distance-known share {label_a} | distance-known share {label_b} | "
        "within selection (min) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    terms = {term.group: term for term in point.terms}
    order = group_order or tuple(sorted(terms))
    for group in order:
        term = terms.get(group)
        if term is None:
            continue
        n_a = counts_a.get(group, 0)
        n_b = counts_b.get(group, 0)
        if min(n_a, n_b) < MIN_CELL_N:
            lines.append(
                f"| {group} | {n_a} | {n_b} | "
                "- | - | - | - | - | - | - | - | - | - | - | - |"
            )
            continue
        lines.append(
            f"| {group} | {n_a} | {n_b} | {_pct(term.share_a)} | "
            f"{_pct(term.share_b)} | {_num(term.minutes_per_trip_a)} | "
            f"{_num(term.minutes_per_trip_b)} | {_num(term.mix_min, 2)} | "
            f"{_num(term.within_min, 2)} | {_num(term.within_km_min, 2)} | "
            f"{_num(term.within_speed_min, 2)} | {_num(term.interaction_min, 2)} | "
            f"{_pct(term.distance_share_a)} | {_pct(term.distance_share_b)} | "
            f"{_num(term.within_selection_min, 2)} |"
        )
    return lines


def age_band_index(age: np.ndarray) -> np.ndarray:
    """B1 age-band index (into ``AGE_BAND_LABELS``) of each age."""
    return np.clip(
        np.searchsorted(np.asarray(AGE_BAND_LOWER[1:]), age, side="right"),
        0,
        len(AGE_BAND_LABELS) - 1,
    )


#: B1's composition variants: the stratum parts crossed with the age
#: bands. 'residence' is home_density x Île-de-France; 'cars' is the
#: household 0/1/2+ band.
B1_VARIANTS = {
    "V1": ("sex", "category"),
    "V2": ("sex", "category", "residence"),
    "V3": ("sex", "category", "residence", "cars"),
}


def _b1_strata(frames: SurveyFrames, parts: tuple[str, ...]) -> np.ndarray:
    days = frames.days
    columns = []
    for part in parts:
        if part == "sex":
            sex = days["sex"].astype(float)
            columns.append(np.where(np.isfinite(sex), sex.astype(int).astype(str), "u"))
        elif part == "category":
            columns.append(days["population_category"].astype(str))
        elif part == "residence":
            idf = np.where(days["is_idf"].astype(bool), "idf", "rest")
            columns.append(
                np.char.add(np.char.add(days["home_density"].astype(str), "|"), idf)
            )
        elif part == "cars":
            columns.append(days["cars_band"].astype(str))
        else:  # pragma: no cover - fixed variant definitions
            raise ValueError(f"unknown B1 part: {part}")
    out = columns[0]
    for column in columns[1:]:
        out = np.char.add(np.char.add(out, "||"), column)
    return out


def composition_pair_cells(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    variant: str,
    *,
    min_n: int = 30,
) -> tuple[np.ndarray, np.ndarray]:
    """Cell labels of B1's ``variant`` for both groups: stratum x age
    band, with neighbouring age bands merged (jointly for both groups)
    wherever a cell has fewer than ``min_n`` respondents in either."""
    parts = B1_VARIANTS[variant]
    strata_a = _b1_strata(frames_a, parts)
    strata_b = _b1_strata(frames_b, parts)
    age_a = age_band_index(frames_a.days["age"].astype(float))
    age_b = age_band_index(frames_b.days["age"].astype(float))
    mapping = variation.merge_age_bands(
        age_a, strata_a, age_b, strata_b, n_bands=len(AGE_BAND_LABELS), min_n=min_n
    )
    cells_a = np.array(
        [
            f"{stratum}||age{mapping[(stratum, int(idx))]}"
            for stratum, idx in zip(strata_a, age_a, strict=True)
        ]
    )
    cells_b = np.array(
        [
            f"{stratum}||age{mapping[(stratum, int(idx))]}"
            for stratum, idx in zip(strata_b, age_b, strict=True)
        ]
    )
    return cells_a, cells_b


@dataclass(frozen=True)
class B1Row:
    """One B1 variant's composition/behaviour split with household-
    bootstrap 95% CIs; optional ledger vectors are minutes/day,
    trips/day and minutes/trip effects and their 95% bounds."""

    variant: str
    point: variation.Composition
    composition_ci: tuple[float, float]
    behaviour_ci: tuple[float, float]
    note: str = ""
    ledger_effect: np.ndarray | None = None
    ledger_bounds: np.ndarray | None = None


def bootstrap_composition(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    variant: str,
    *,
    n_reps: int,
    seed: int,
    note: str = "",
    label: str | None = None,
) -> B1Row:
    """B1's re-weighting for one variant: the point split and household-
    bootstrap CIs (cells fixed at the point sample's merged definition).
    ``label`` renames the reported variant (the 2008 -> 2019 pair's V3
    falls back to V2's cells but is still reported as V3)."""
    cells_a, cells_b = composition_pair_cells(frames_a, frames_b, variant)
    weight_a = frames_a.days["pond_jour"].astype(float)
    weight_b = frames_b.days["pond_jour"].astype(float)
    time_a = frames_a.days["total_time_min"].astype(float)
    time_b = frames_b.days["total_time_min"].astype(float)
    point = variation.composition_reweight(
        cells_a, weight_a, time_a, cells_b, weight_b, time_b
    )
    include_rates = (
        variant == "V2"
        and "trips_per_day" in frames_a.days
        and "trips_per_day" in frames_b.days
    )

    def rate_effects(
        time_split: variation.Composition, wa: np.ndarray, wb: np.ndarray
    ) -> tuple[float, float]:
        trips_split = variation.composition_reweight(
            cells_a,
            wa,
            frames_a.days["trips_per_day"],
            cells_b,
            wb,
            frames_b.days["trips_per_day"],
        )
        return (
            trips_split.composition_min,
            time_split.counterfactual_a_min / trips_split.counterfactual_a_min
            - time_split.mean_a_min / trips_split.mean_a_min,
        )

    ledger_effect = (
        np.array([point.composition_min, *rate_effects(point, weight_a, weight_b)])
        if include_rates
        else None
    )
    seed_a, seed_b = np.random.SeedSequence(seed).spawn(2)
    rng_a, rng_b = np.random.default_rng(seed_a), np.random.default_rng(seed_b)
    reps = np.full((len(range(n_reps)), 2), np.nan)
    rate_reps = np.full((n_reps, 2), np.nan)
    for rep in range(n_reps):
        w_a = weight_a * variation.household_multipliers(
            frames_a.days["ident_men"], rng_a
        )
        w_b = weight_b * variation.household_multipliers(
            frames_b.days["ident_men"], rng_b
        )
        if w_a.sum() <= 0 or w_b.sum() <= 0:
            continue
        try:
            result = variation.composition_reweight(
                cells_a, w_a, time_a, cells_b, w_b, time_b
            )
        except ValueError:
            continue
        reps[rep] = (result.composition_min, result.behaviour_min)
        if include_rates:
            rate_reps[rep] = rate_effects(result, w_a, w_b)
    valid = reps[np.isfinite(reps).all(axis=1)]
    if len(valid) == 0:
        raise ValueError("household bootstrap produced no valid replicates")
    intervals = np.percentile(valid, [2.5, 97.5], axis=0)
    return B1Row(
        variant=label or variant,
        point=point,
        composition_ci=(float(intervals[0, 0]), float(intervals[1, 0])),
        behaviour_ci=(float(intervals[0, 1]), float(intervals[1, 1])),
        note=note,
        ledger_effect=ledger_effect,
        ledger_bounds=(
            np.vstack(
                [
                    intervals[:, 0],
                    _ledger_interval(rate_reps[:, 0]),
                    _ledger_interval(rate_reps[:, 1]),
                ]
            )
            if include_rates
            else None
        ),
    )


def _format_b1(rows: list[B1Row], label_a: str, label_b: str) -> list[str]:
    lines = [
        f"## B1. Composition, {label_a} -> {label_b}",
        "",
        f"Group {label_a} re-weighted to group {label_b}'s population "
        "structure, cell by cell. V1: age band x sex x category; V2: V1 x "
        "residence (density x Île-de-France vs other regions); V3: V2 x "
        "household cars (0/1/2+). Age bands with fewer than 30 "
        "respondents in either group are merged with the neighbouring "
        "band. Composition = counterfactual mean of A - mean of A; "
        "behaviour = mean of B - counterfactual. Household-bootstrap 95% "
        "CIs; the composition + behaviour identity holds exactly for "
        "each variant.",
        "",
        f"| Variant | Cells | Unmatched {label_b} weight | Mean {label_a} | "
        f"Counterfactual {label_a} | Mean {label_b} | Composition (min) "
        "[CI] | Behaviour (min) [CI] | Note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        point = row.point
        lines.append(
            f"| {row.variant} | {point.n_cells} | "
            f"{_pct(point.unmatched_b_weight_share)} | "
            f"{_num(point.mean_a_min)} | {_num(point.counterfactual_a_min)} | "
            f"{_num(point.mean_b_min)} | "
            f"{_ci_cell(point.composition_min, row.composition_ci)} | "
            f"{_ci_cell(point.behaviour_min, row.behaviour_ci)} | "
            f"{row.note} |"
        )
    return lines


@dataclass(frozen=True)
class B5Stats:
    """One survey's B5 tail statistics (weighted, minutes per person-day
    with trips)."""

    mean_min: float
    median_min: float
    trimmed_1pct_min: float
    trimmed_2_5pct_min: float
    over_180_min: float
    trips_over_20km_min: float
    trips_over_40km_min: float


def b5_tail_stats(frames: SurveyFrames) -> B5Stats:
    """B5's tail statistics for one survey: the weighted median, the
    top-1%/top-2.5%-trimmed means, the minutes per person-day held in
    days above 180 min, and in trips above 20 and 40 km."""
    days, trips = frames.days, frames.trips
    w = days["pond_jour"].astype(float)
    time = days["total_time_min"].astype(float)
    tw = trips["pond_jour"].astype(float)
    t_min = trips["duration_min"].astype(float)
    t_km = trips["distance_km"].astype(float)
    day_weight = float(w.sum())

    def _trip_minutes_over(km: float) -> float:
        mask = t_km > km
        return float(np.sum(tw[mask] * t_min[mask])) / day_weight

    return B5Stats(
        mean_min=float(np.sum(w * time)) / day_weight,
        median_min=variation.weighted_median(time, w),
        trimmed_1pct_min=variation.trimmed_mean(time, w, 0.01),
        trimmed_2_5pct_min=variation.trimmed_mean(time, w, 0.025),
        over_180_min=variation.mean_above_threshold(time, w, 180.0),
        trips_over_20km_min=_trip_minutes_over(20.0),
        trips_over_40km_min=_trip_minutes_over(40.0),
    )


def _format_b5(
    stats_a: B5Stats, stats_b: B5Stats, label_a: str, label_b: str
) -> list[str]:
    lines = [
        f"## B5. Tails, {label_a} -> {label_b}",
        "",
        "Weighted statistics of daily time on days with trips: the "
        "median, means trimmed of the top 1% / 2.5% of daily-time weight, "
        "and the minutes per person-day held in days above 180 min and in "
        "trips above 20 and 40 km (step-11 corrected distances).",
        "",
        f"| Statistic | {label_a} | {label_b} | Δ (min) |",
        "|---|---|---|---|",
    ]
    rows = [
        ("Mean (min/day)", "mean_min"),
        ("Median (min/day)", "median_min"),
        ("Trimmed mean, top 1% removed", "trimmed_1pct_min"),
        ("Trimmed mean, top 2.5% removed", "trimmed_2_5pct_min"),
        ("Minutes in days > 180 min", "over_180_min"),
        ("Minutes in trips > 20 km", "trips_over_20km_min"),
        ("Minutes in trips > 40 km", "trips_over_40km_min"),
    ]
    for label, attr in rows:
        a = getattr(stats_a, attr)
        b = getattr(stats_b, attr)
        lines.append(f"| {label} | {_num(a)} | {_num(b)} | {_num(b - a)} |")
    return lines


@dataclass(frozen=True)
class PairResult:
    """One B6 sub-pair (one row of the pair tables): the B2 split, the
    B3 aggregate terms and the B1 variants between groups A and B."""

    label: str
    n_a: int
    n_b: int
    b2: B2Row
    b3: variation.ShiftShareBootstrap | None
    b1: list[B1Row]


def comparison_pair(
    label: str,
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    *,
    variants: tuple[str, ...] = ("V1", "V2", "V3"),
    n_reps: int,
    seed: int,
) -> PairResult:
    """Run B2, B3 (mode) and B1 (``variants``) between two groups of
    person-days (B6's pairs 2 and 3); degenerate pieces are skipped."""
    b2 = b2_decompositions(frames_a, frames_b, n_reps=n_reps, seed=seed, categories=())[
        0
    ]
    try:
        b3 = shift_share_by(frames_a, frames_b, "mode7", n_reps=n_reps, seed=seed)
    except (ValueError, ZeroDivisionError):
        b3 = None
    b1 = []
    for variant in variants:
        try:
            b1.append(
                bootstrap_composition(
                    frames_a, frames_b, variant, n_reps=n_reps, seed=seed
                )
            )
        except (ValueError, ZeroDivisionError):
            continue
    return PairResult(
        label=label,
        n_a=len(frames_a.days["pond_jour"]),
        n_b=len(frames_b.days["pond_jour"]),
        b2=b2,
        b3=b3,
        b1=b1,
    )


def _format_pair_results(
    pairs: list[PairResult],
    *,
    title: str,
    intro: str,
    label_a: str,
    label_b: str,
) -> list[str]:
    lines = [
        title,
        "",
        intro,
        "",
    ]
    rows = [
        B2Row(
            pair.label, pair.n_a, pair.n_b, pair.b2.result, pair.b2.unavailable_reason
        )
        for pair in pairs
    ]
    lines += _format_b2(
        rows,
        label_a,
        label_b,
        title="Decomposition (B2, minutes, household-bootstrap 95% CIs):",
    )
    lines += [
        "",
        "Mode shift-share aggregates (B3, minutes):",
        "",
        "| Group | volume [CI] | mode mix [CI] | within modes [CI] | "
        "interaction [CI] |",
        "|---|---|---|---|---|",
    ]
    for pair in pairs:
        if pair.b3 is None or min(pair.n_a, pair.n_b) < MIN_CELL_N:
            lines.append(f"| {pair.label} | - | - | - | - |")
            continue
        point = pair.b3.point
        lines.append(
            f"| {pair.label} | {_ci_cell(point.volume_min, pair.b3.volume_ci)} | "
            f"{_ci_cell(point.mix_min, pair.b3.mix_ci)} | "
            f"{_ci_cell(point.within_min, pair.b3.within_ci)} | "
            f"{_ci_cell(point.interaction_min, pair.b3.interaction_ci)} |"
        )
    lines += [
        "",
        "Composition (B1, minutes; residence uses the INSEE density grid "
        "in both surveys):",
        "",
        "| Group | Variant | Cells | Composition [CI] | Behaviour [CI] |",
        "|---|---|---|---|---|",
    ]
    for pair in pairs:
        for row in pair.b1:
            if min(pair.n_a, pair.n_b) < MIN_CELL_N:
                lines.append(f"| {pair.label} | {row.variant} | - | - | - |")
                continue
            lines.append(
                f"| {pair.label} | {row.variant} | {row.point.n_cells} | "
                f"{_ci_cell(row.point.composition_min, row.composition_ci)} | "
                f"{_ci_cell(row.point.behaviour_min, row.behaviour_ci)} |"
            )
    return lines


def _cell_time_ci(
    frames: SurveyFrames,
    mask: np.ndarray,
    *,
    n_reps: int,
    seed: int,
) -> tuple[int, float, tuple[float, float]]:
    n = int(mask.sum())
    if n == 0:
        return 0, float("nan"), (float("nan"), float("nan"))
    mean, ci = variation.weighted_mean_ci(
        frames.days["total_time_min"][mask].astype(float),
        frames.days["pond_jour"][mask].astype(float),
        frames.days["ident_men"][mask],
        n_reps=n_reps,
        seed=seed,
    )
    return n, mean, ci


def pair4_tables(
    frames: SurveyFrames,
    category: str,
    *,
    n_reps: int,
    seed: int,
) -> list[str]:
    """B6 pair 4: time per day with trips by density class x income
    quintile (n, mean, 95% CI), and Île-de-France vs the other regions
    by income quintile, for one survey and category."""
    days = frames.days
    base = days["population_category"].astype(str) == category
    quintiles = ("q1", "q2", "q3", "q4", "q5")
    densities = [
        d for d in trip_legs.DENSITY_LABELS if (days["home_density"] == d).any()
    ]
    lines = [
        f"### {frames.name}, {category}",
        "",
        "| Density \\ income | " + " | ".join(quintiles) + " |",
        "|---" * (len(quintiles) + 1) + "|",
    ]
    for density in densities:
        cells = []
        for quintile in quintiles:
            mask = (
                base
                & (days["home_density"].astype(str) == density)
                & (days["income_quintile"].astype(str) == quintile)
            )
            n, mean, ci = _cell_time_ci(frames, mask, n_reps=n_reps, seed=seed)
            if n < MIN_CELL_N:
                cells.append(f"n={n}: -")
            else:
                cells.append(f"n={n}: {_num(mean)} [{_num(ci[0])}, {_num(ci[1])}]")
        lines.append(f"| {density} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "| Île-de-France \\ income | " + " | ".join(quintiles) + " |",
        "|---" * (len(quintiles) + 1) + "|",
    ]
    for is_idf, label in ((True, "Île-de-France"), (False, "other regions")):
        cells = []
        for quintile in quintiles:
            mask = (
                base
                & (days["is_idf"].astype(bool) == is_idf)
                & (days["income_quintile"].astype(str) == quintile)
            )
            n, mean, ci = _cell_time_ci(frames, mask, n_reps=n_reps, seed=seed)
            if n < MIN_CELL_N:
                cells.append(f"n={n}: -")
            else:
                cells.append(f"n={n}: {_num(mean)} [{_num(ci[0])}, {_num(ci[1])}]")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def _figure_b7_waterfall(results: dict, out_dir: Path) -> Path | None:
    """B7's waterfall: composition (B1 V2), unscaled B2 terms, and residual."""
    b2 = results["b2_rows"][0].result
    b1_v2 = next((r for r in results["b1_rows"] if r.variant == "V2"), None)
    if b2 is None or b1_v2 is None:
        return None
    point = b2.point
    delta = point.delta_min
    composition = b1_v2.point.composition_min
    b2_terms = np.array(
        [point.trips_min, point.distance_min, point.speed_min, point.selection_min]
    )
    steps = [
        ("composition (V2)", composition),
        ("trips", float(b2_terms[0])),
        ("km per trip", float(b2_terms[1])),
        ("time per crow-fly km", float(b2_terms[2])),
        ("distance selection", float(b2_terms[3])),
    ]
    residual = delta - composition - float(b2_terms.sum())
    if not np.isclose(residual, 0.0, atol=1e-10):
        steps.append(("non-additive residual", residual))
    fig, ax = plt.subplots(figsize=(7, 4))
    level = point.time_a_min
    positions = np.arange(len(steps) + 2)
    ax.bar(0, point.time_a_min, color="0.6")
    ax.text(0, point.time_a_min, f"{point.time_a_min:.1f}", ha="center", va="bottom")
    for i, (label, value) in enumerate(steps, start=1):
        color = "#2a9d8f" if value >= 0 else "#e76f51"
        ax.bar(i, value, bottom=level, color=color)
        ax.text(
            i,
            level + max(value, 0),
            f"{value:+.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
        level += value
    ax.bar(len(steps) + 1, point.time_b_min, color="0.4")
    ax.text(
        len(steps) + 1,
        point.time_b_min,
        f"{point.time_b_min:.1f}",
        ha="center",
        va="bottom",
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        ["2008", *[label for label, _ in steps], "2019"], fontsize=8, rotation=20
    )
    ax.set_ylabel("Daily time with trips (min)")
    ax.set_title(
        "B7a. 2008 -> 2019 daily-time change (crow-fly distances): "
        "composition and unscaled B2 terms"
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path = out_dir / "fig_b7a_waterfall.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _shift_share_panel(ax, result: variation.ShiftShareBootstrap, title: str) -> None:
    terms = result.point.terms
    if all(t.group in DISTANCE_BAND_LABELS for t in terms):
        terms = tuple(sorted(terms, key=lambda t: DISTANCE_BAND_LABELS.index(t.group)))
    groups = [t.group for t in terms]
    x = np.arange(len(groups))
    width = 0.27
    ax.bar(x - width, [t.mix_min for t in terms], width, label="mix")
    ax.bar(x, [t.within_min for t in terms], width, label="within")
    ax.bar(x + width, [t.interaction_min for t in terms], width, label="interaction")
    ax.axhline(0.0, color="0.5", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, rotation=45, ha="right", fontsize=7)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)


def _figure_b7_shift_share(results: dict, out_dir: Path) -> Path:
    """B7's shift-share bars by mode, motive and distance band (minutes
    per day, 2008 -> 2019)."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    _shift_share_panel(axes[0], results["b3_mode"], "by mode")
    _shift_share_panel(axes[1], results["b4_motive"], "by motive")
    _shift_share_panel(axes[2], results["b4_distance"], "by distance band")
    axes[0].set_ylabel("Minutes per day")
    axes[0].legend(fontsize=8)
    fig.suptitle("B7b. Shift-share of the 2008 -> 2019 daily-time change")
    fig.tight_layout()
    path = out_dir / "fig_b7b_shift_share.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _figure_b7_recall_lag(results: dict, out_dir: Path) -> Path:
    """B7's recall-lag figure: time per day, trips per day and minutes
    per trip by EMP 2019 recall lag, with the ENTD 2008 level as a
    reference line."""
    rows = [row for row in results["lag_table"] if row.label.isdigit()]
    lags = [int(row.label) for row in rows]
    entd = results["entd_overall"]
    panels = (
        ("time_per_day_min", "Time per day (min)"),
        ("trips_per_day", "Trips per day"),
        ("minutes_per_trip", "Minutes per trip"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, (attr, label) in zip(axes, panels, strict=True):
        values = [getattr(row, attr) for row in rows]
        ax.plot(lags, values, marker="o", label="EMP 2019 by lag")
        ax.axhline(
            getattr(entd, attr), color="#e76f51", linestyle="--", label="ENTD 2008"
        )
        ax.set_xlabel("Recall lag (days)")
        ax.set_title(label, fontsize=9)
        ax.tick_params(labelsize=8)
    axes[0].legend(fontsize=7)
    fig.suptitle("B7c. EMP 2019 by recall lag vs ENTD 2008 (weekday days)")
    fig.tight_layout()
    path = out_dir / "fig_b7c_recall_lag.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _density_grid_comparison_lines(
    frames_2008: SurveyFrames,
    frames_2019: SurveyFrames,
    *,
    n_reps: int,
    seed: int,
    equivalence_margin: float,
    secondary_equivalence_margin: float,
) -> list[str]:
    """Compare trips/day and time/day within each shared residence grid class."""
    lines = [
        "## B6.5. 2008 -> 2019 by INSEE density grid",
        "",
        "Weekday person-days with needs-scope trips, by residence density grid "
        "class and population category. Measures are trips/day and minutes/day; "
        "n is the number of person-days. Differences use household-bootstrap "
        "95% CIs; daily-time ratios use 90% CIs. Equivalence is established "
        "only when the full ratio interval is within the margin. "
        "Households are resampled independently. "
        "ENTD 2008 classes come from the SDES 2020-zoning supplement.",
        "",
        "| Density grid class | Population category | Measure | n 2008 | "
        "2008 [95% CI] | n 2019 | 2019 [95% CI] | Difference 2019 - "
        "2008 [95% CI] | Time ratio 2019/2008 | 90% CI | "
        f"Equivalent at ±{equivalence_margin:.0%} | "
        f"Equivalent at ±{secondary_equivalence_margin:.0%} |",
        "|---|---|---|---:|---|---:|---|---|---:|---|---|---|",
    ]
    for density in trip_legs.DENSITY_LABELS:
        subset_2008 = subset_frames(frames_2008, home_density=density)
        subset_2019 = subset_frames(frames_2019, home_density=density)
        measures = {
            "trips/day": (
                np.ones(len(subset_2008.trips["pond_jour"])),
                np.ones(len(subset_2019.trips["pond_jour"])),
            ),
            "time/day (min)": (
                subset_2008.trips["duration_min"].astype(float),
                subset_2019.trips["duration_min"].astype(float),
            ),
        }
        rows = _daily_rate_rows(
            subset_2008,
            subset_2019,
            measures,
            n_reps=n_reps,
            seed=seed,
        )
        for row in rows:
            category = "all categories" if row.group == "overall" else row.group
            delta_ci = _ci_cell(row.mean_b - row.mean_a, row.delta_ci, 2)
            ratio_cell = ci_cell = verdict_cell = verdict_secondary_cell = "-"
            if row.metric == "time/day (min)":
                mask_a = np.ones(len(subset_2008.days["pond_jour"]), dtype=bool)
                mask_b = np.ones(len(subset_2019.days["pond_jour"]), dtype=bool)
                if row.group != "overall":
                    mask_a &= subset_2008.days["population_category"] == row.group
                    mask_b &= subset_2019.days["population_category"] == row.group
                ratio = _time_ratio_ci(
                    subset_2008,
                    subset_2019,
                    mask_a,
                    mask_b,
                    n_reps=n_reps,
                    seed=seed,
                )
                if ratio is not None:
                    ratio_value, ratio_ci = ratio
                    ratio_cell = f"{ratio_value:.3f}"
                    ci_cell = f"[{ratio_ci[0]:.3f}, {ratio_ci[1]:.3f}]"
                    verdict_cell = _equivalence_verdict(ratio_ci, equivalence_margin)
                    verdict_secondary_cell = _equivalence_verdict(
                        ratio_ci, secondary_equivalence_margin
                    )
            lines.append(
                f"| {density} | {category} | {row.metric} | {row.n_a} | "
                f"{_suppress(row.n_a, _ci_cell(row.mean_a, row.ci_a, 2))} | "
                f"{row.n_b} | "
                f"{_suppress(row.n_b, _ci_cell(row.mean_b, row.ci_b, 2))} | "
                f"{_suppress(min(row.n_a, row.n_b), delta_ci)} | "
                f"{_suppress(min(row.n_a, row.n_b), ratio_cell)} | "
                f"{_suppress(min(row.n_a, row.n_b), ci_cell)} | "
                f"{_suppress(min(row.n_a, row.n_b), verdict_cell)} | "
                f"{_suppress(min(row.n_a, row.n_b), verdict_secondary_cell)} |"
            )
    return lines


def _run_part_b(
    results: dict,
    frames_2008: SurveyFrames,
    frames_2019: SurveyFrames,
    frames_2019_grid: SurveyFrames,
    out_dir: Path,
    *,
    n_reps: int,
    seed: int,
) -> None:
    """Part B decompositions and figures; extended one item at a time
    (B2, B3, B1, B4, B5, B6, B7). Sections are appended in report order
    (B1 first), whatever the implementation order."""
    results["b1_rows"] = [
        bootstrap_composition(frames_2008, frames_2019, "V1", n_reps=n_reps, seed=seed),
        bootstrap_composition(
            frames_2008,
            frames_2019,
            "V2",
            n_reps=n_reps,
            seed=seed,
            note="INSEE density grid x Île-de-France",
        ),
        bootstrap_composition(
            frames_2008,
            frames_2019,
            "V2",
            n_reps=n_reps,
            seed=seed,
            label="V3",
            note="falls back to V2: no household-car count in ENTD "
            "2008's step-11 tables (see Choices made)",
        ),
    ]
    frames_2008_crow = common_distance_frames(frames_2008, "crow_fly_km")
    frames_2019_crow = common_distance_frames(frames_2019, "crow_fly_km")
    results["b2_rows"] = b2_decompositions(
        frames_2008_crow,
        frames_2019_crow,
        n_reps=n_reps,
        seed=seed,
        include_time_ratio=True,
    )
    all_2008 = frames_2008.all_trips
    all_2019 = frames_2019.all_trips
    if all_2008 is None or all_2019 is None:
        raise ValueError("all-trips sensitivity frames were not loaded")
    all_crow_2008 = common_distance_frames(all_2008, "crow_fly_km")
    all_crow_2019 = common_distance_frames(all_2019, "crow_fly_km")
    all_trip_rows = b2_decompositions(
        all_crow_2008,
        all_crow_2019,
        n_reps=n_reps,
        seed=seed,
        categories=(),
        include_time_ratio=True,
    )
    results["b2_all_trips_row"] = B2Row(
        group="All trips (all motives and distances)",
        n_a=all_trip_rows[0].n_a,
        n_b=all_trip_rows[0].n_b,
        result=all_trip_rows[0].result,
        unavailable_reason=all_trip_rows[0].unavailable_reason,
        time_ratio=all_trip_rows[0].time_ratio,
        time_ratio_ci90=all_trip_rows[0].time_ratio_ci90,
    )
    results["b2_rows_corrected"] = b2_decompositions(
        frames_2008,
        frames_2019,
        n_reps=n_reps,
        seed=seed,
        include_time_ratio=True,
    )
    results["b3_mode"] = shift_share_by(
        frames_2008, frames_2019, "mode7", n_reps=n_reps, seed=seed
    )
    results["b4_motive"] = shift_share_by(
        frames_2008, frames_2019, "motive_group", n_reps=n_reps, seed=seed
    )
    results["b4_distance"] = shift_share_by(
        frames_2008, frames_2019, "distance_band", n_reps=n_reps, seed=seed
    )
    results["b5_2008"] = b5_tail_stats(frames_2008)
    results["b5_2019"] = b5_tail_stats(frames_2019)
    # B6 pair 1 variant: EMP 2019 restricted to recall lag 1 (A1).
    results["b2_rows_lag1"] = b2_decompositions(
        frames_2008_crow,
        common_distance_frames(subset_frames(frames_2019, recall_lag=1), "crow_fly_km"),
        n_reps=n_reps,
        seed=seed,
        include_time_ratio=True,
    )
    # B6 pair 2: within EMP 2019 (INSEE density grid), dense vs
    # intermediate, within category: A = intermediate, B = dense, so
    # Δ = dense - intermediate.
    results["pair2"] = [
        comparison_pair(
            category,
            subset_frames(
                frames_2019_grid,
                population_category=category,
                home_density="intermediate",
            ),
            subset_frames(
                frames_2019_grid, population_category=category, home_density="dense"
            ),
            n_reps=n_reps,
            seed=seed,
        )
        for category in ("employed", "retired", "children_6_17")
    ]
    # B6 pair 3: within EMP 2019, income q1 vs q5: A = q1, B = q5.
    results["pair3"] = [
        comparison_pair(
            category,
            subset_frames(
                frames_2019_grid, population_category=category, income_quintile="q1"
            ),
            subset_frames(
                frames_2019_grid, population_category=category, income_quintile="q5"
            ),
            n_reps=n_reps,
            seed=seed,
        )
        for category in ("employed", "retired")
    ]
    # B6 pair 4: density x income tables, employed and retired, both
    # surveys, using the shared INSEE density grid.
    pair4_lines = [
        "## B6.4. Density and income together",
        "",
        "Time per day with trips (min) by density class x income "
        "quintile, and Île-de-France vs the other regions by income "
        "quintile (n, weighted mean, household-bootstrap 95% CI; cells "
        f"under {MIN_CELL_N} respondents print n with `-`). The question "
        "is whether the income gradient survives within density classes, "
        "or is the density/Île-de-France gradient in disguise. Both years "
        "use the INSEE density grid.",
        "",
    ]
    for frames in (frames_2008, frames_2019_grid):
        for category in ("employed", "retired"):
            pair4_lines += pair4_tables(frames, category, n_reps=n_reps, seed=seed)
            pair4_lines.append("")
    pair4_lines += _density_grid_comparison_lines(
        frames_2008,
        frames_2019_grid,
        n_reps=n_reps,
        seed=seed,
        equivalence_margin=results["equivalence_margin"],
        secondary_equivalence_margin=results["secondary_equivalence_margin"],
    )
    results["pair4_lines"] = pair4_lines
    motive_order = tuple([*MOTIVE_GROUP_LABELS.values(), "unknown"])
    results["extra_sections"] += [
        _format_b1(results["b1_rows"], "2008", "2019"),
        _format_b2(
            [*results["b2_rows"], results["b2_all_trips_row"]],
            "2008",
            "2019",
            distance_description=(
                "raw crow-fly distances (`V2_DVO_LOC` for ENTD 2008; "
                "`dVO_ORIDES` for EMP 2019), with no speed correction"
            ),
            equivalence_margin=results["equivalence_margin"],
            secondary_equivalence_margin=results["secondary_equivalence_margin"],
        ),
        _format_b2(
            results["b2_rows_corrected"],
            "2008",
            "2019",
            title="### B2 sensitivity: corrected distances",
            distance_description=(
                "ENTD 2008's step-11 corrected/fallback distance "
                "(`distcor`, otherwise `V2_MDISTTOT`, with plausibility "
                "correction) and EMP 2019's step-11 corrected distance "
                "from `MDISTTOT_fin`"
            ),
            equivalence_margin=results["equivalence_margin"],
            secondary_equivalence_margin=results["secondary_equivalence_margin"],
        ),
        _format_shift_share(
            results["b3_mode"],
            _group_counts(frames_2008, "mode7"),
            _group_counts(frames_2019, "mode7"),
            title="## B3. Mode shift-share, 2008 -> 2019",
            group_name="mode",
            label_a="2008",
            label_b="2019",
            group_order=MODE7_LABELS,
        ),
        _format_shift_share(
            results["b4_motive"],
            _group_counts(frames_2008, "motive_group"),
            _group_counts(frames_2019, "motive_group"),
            title="## B4a. Motive shift-share, 2008 -> 2019",
            group_name="motive",
            label_a="2008",
            label_b="2019",
            group_order=motive_order,
        ),
        _format_shift_share(
            results["b4_distance"],
            _group_counts(frames_2008, "distance_band"),
            _group_counts(frames_2019, "distance_band"),
            title="## B4b. Distance-band shift-share, 2008 -> 2019",
            group_name="band",
            label_a="2008",
            label_b="2019",
            group_order=DISTANCE_BAND_LABELS,
            within_label="within bands",
            intro=(
                "Same shift-share by trip distance band (A3's bands). "
                "The within-band change can reflect both distance and speed, "
                "especially in the open-ended >=80 km band. "
                "Household-bootstrap 95% CIs."
            ),
        ),
        _format_b4_durations(frames_2008, frames_2019),
        _format_b5(results["b5_2008"], results["b5_2019"], "2008", "2019"),
        _format_b2(
            results["b2_rows_lag1"],
            "2008",
            "2019 (lag 1)",
            title="## B6.1. Pair 1 variant: 2008 -> 2019 with EMP 2019 "
            "restricted to recall lag 1",
            distance_description=(
                "raw crow-fly distances (`V2_DVO_LOC` for ENTD 2008; "
                "`dVO_ORIDES` for EMP 2019), with no speed correction"
            ),
            equivalence_margin=results["equivalence_margin"],
            secondary_equivalence_margin=results["secondary_equivalence_margin"],
        ),
        _format_pair_results(
            results["pair2"],
            title="## B6.2. EMP 2019, dense vs intermediate, within category",
            intro="A = intermediate density, B = dense (INSEE density "
            "grid), so Δ = dense - intermediate, within each population "
            "category.",
            label_a="interm.",
            label_b="dense",
        ),
        _format_pair_results(
            results["pair3"],
            title="## B6.3. EMP 2019, income q1 vs q5, within category",
            intro="A = income quintile q1, B = q5, so Δ = q5 - q1, within "
            "each population category (INSEE density grid for the "
            "composition variants).",
            label_a="q1",
            label_b="q5",
        ),
        results["pair4_lines"],
    ]
    waterfall = _figure_b7_waterfall(results, out_dir)
    results["figures"] = [
        path
        for path in (
            waterfall,
            _figure_b7_shift_share(results, out_dir),
            _figure_b7_recall_lag(results, out_dir),
        )
        if path is not None
    ]


def _trip_day_index(frames: SurveyFrames) -> np.ndarray:
    """Map trip rows to their person-day rows (section 9.9)."""
    days = frames.days["day_id"].astype(str)
    if len(np.unique(days)) != len(days):
        raise ValueError("measurement checks require unique person-day ids")
    order = np.argsort(days)
    trip_days = frames.trips["day_id"].astype(str)
    positions = np.searchsorted(days[order], trip_days)
    if np.any(positions >= len(days)):
        raise ValueError("trip has no matching person-day")
    indices = order[positions]
    if np.any(days[indices] != trip_days):
        raise ValueError("trip has no matching person-day")
    return indices


def common_distance_frames(frames: SurveyFrames, column: str) -> SurveyFrames:
    """Reaggregate a raw distance column, keeping all weekday days/trips.

    Neither producer-corrected distances nor speed corrections are used.
    Missing/invalid raw distances stay unknown, never imputed.
    """
    distance = frames.trips[column].astype(float)
    known = np.isfinite(distance) & (distance >= 0)
    distance = np.where(known, distance, np.nan)
    indices = _trip_day_index(frames)
    n = len(frames.days["pond_jour"])
    days = dict(frames.days)
    days["total_distance_km"] = np.bincount(
        indices, weights=np.where(known, distance, 0), minlength=n
    )
    days["distance_trips"] = np.bincount(indices, weights=known, minlength=n)
    days["distance_time_min"] = np.bincount(
        indices,
        weights=np.where(known, frames.trips["duration_min"], 0),
        minlength=n,
    )
    return SurveyFrames(
        frames.name, days, {**frames.trips, "distance_km": distance}, frames.aux
    )


def rounding_level(durations: np.ndarray, levels: tuple[int, ...]) -> np.ndarray:
    """C1: largest rounding multiple in minutes, including zero (section 9.9)."""
    if not np.isfinite(durations).all() or np.any(durations < 0):
        raise ValueError("rounding requires finite, non-negative durations")
    result = np.full(len(durations), levels[0], dtype=int)
    for level in levels[1:]:
        result[np.isclose(np.remainder(durations, level), 0, atol=1e-8)] = level
    return result


def _rounding_cells(
    frames: SurveyFrames, config: variation.MeasurementConfig
) -> tuple[np.ndarray, tuple[int, int, int]]:
    classes = np.searchsorted(
        config.duration_upper_min, frames.trips["duration_min"], side="right"
    )
    n_classes = len(config.duration_upper_min) + 1
    modes = frames.trips["mode7"].astype(str)
    codes = np.full(len(modes), -1, dtype=int)
    for i, mode in enumerate(MODE7_LABELS):
        codes[modes == mode] = i
    if np.any(codes < 0):
        raise ValueError("unrecognised mode in rounding cells")
    return (
        codes * n_classes + classes,
        (len(MODE7_LABELS), n_classes, len(config.rounding_levels)),
    )


def _rounding_shares(
    frames: SurveyFrames,
    durations: np.ndarray,
    config: variation.MeasurementConfig,
) -> np.ndarray:
    cells, shape = _rounding_cells(frames, config)
    n_cells = shape[0] * shape[1]
    weight = frames.trips["pond_jour"].astype(float)
    totals = np.bincount(cells, weights=weight, minlength=n_cells)
    levels = rounding_level(durations, config.rounding_levels)
    shares = np.full((n_cells, shape[2]), np.nan)
    for j, level in enumerate(config.rounding_levels):
        numerator = np.bincount(
            cells, weights=weight * (levels >= level), minlength=n_cells
        )
        np.divide(numerator, totals, out=shares[:, j], where=totals > 0)
    return shares.reshape(shape)


def simulate_rounding(
    a: SurveyFrames,
    b: SurveyFrames,
    variant: str,
    *,
    config: variation.MeasurementConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """C1: one coarsening draw on 2008 minutes, targeting 2019 (section 9.9).

    Both surveys' cells use their original durations. At each increasing
    level, p = (target - current share) / eligible share, clipped to [0, 1].
    Existing coarser durations are never refined; ties round upward.
    """
    if variant not in ("nearest", "up", "nearest_min5"):
        raise ValueError(f"unknown rounding variant: {variant}")
    durations = a.trips["duration_min"].astype(float).copy()
    levels = rounding_level(durations, config.rounding_levels)
    cells, shape = _rounding_cells(a, config)
    targets = _rounding_shares(
        b, b.trips["duration_min"].astype(float), config
    ).reshape(-1, shape[2])
    weights = a.trips["pond_jour"].astype(float)
    for cell in np.unique(cells):
        indices = np.flatnonzero(cells == cell)
        total = weights[indices].sum()
        if total <= 0 or not np.isfinite(targets[cell]).all():
            continue
        for j, level in enumerate(config.rounding_levels[1:], start=1):
            current = float(weights[indices][levels[indices] >= level].sum() / total)
            gap = targets[cell, j] - current
            if gap <= 0:
                continue
            eligible = indices[levels[indices] < level]
            scaled = durations[eligible] / level
            rounded = level * (
                np.ceil(scaled) if variant == "up" else np.floor(scaled + 0.5)
            )
            if variant == "nearest_min5":
                rounded = np.maximum(rounded, config.minimum_duration_min)
            new_levels = rounding_level(rounded, config.rounding_levels)
            can_coarsen = new_levels >= level
            eligible = eligible[can_coarsen]
            rounded = rounded[can_coarsen]
            new_levels = new_levels[can_coarsen]
            eligible_share = weights[eligible].sum() / total
            if eligible_share <= 0:
                continue
            selected = rng.random(len(eligible)) < min(1.0, gap / eligible_share)
            durations[eligible[selected]] = rounded[selected]
            levels[eligible[selected]] = new_levels[selected]
    return durations


def rounding_checks(
    a: SurveyFrames,
    b: SurveyFrames,
    *,
    config: variation.MeasurementConfig,
    seed: int,
) -> dict:
    """C1: draw distributions of change in minutes/day and cell shares."""
    indices = _trip_day_index(a)
    changes, shares = {}, {}
    groups = ("overall", *daily_energy.POPULATION_CATEGORIES)
    for variant in ("nearest", "up", "nearest_min5"):
        changes[variant] = {group: [] for group in groups}
        simulated_shares = []
        rng = np.random.default_rng(seed)
        for _ in range(config.rounding_draws):
            durations = simulate_rounding(a, b, variant, config=config, rng=rng)
            delta = np.bincount(
                indices,
                weights=durations - a.trips["duration_min"],
                minlength=len(a.days["pond_jour"]),
            )
            simulated_shares.append(_rounding_shares(a, durations, config))
            for group in groups:
                mask = (
                    np.ones(len(delta), dtype=bool)
                    if group == "overall"
                    else a.days["population_category"] == group
                )
                value = (
                    float(np.average(delta[mask], weights=a.days["pond_jour"][mask]))
                    if mask.any()
                    else float("nan")
                )
                changes[variant][group].append(value)
        shares[variant] = np.asarray(simulated_shares)
    return {
        "changes": changes,
        "shares": shares,
        "target": _rounding_shares(b, b.trips["duration_min"].astype(float), config),
    }


@dataclass(frozen=True)
class DailyRateRow:
    """C2/C3 means and independent-household 95% CIs, per day with trips."""

    group: str
    metric: str
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float
    ci_a: tuple[float, float]
    ci_b: tuple[float, float]
    delta_ci: tuple[float, float]
    replicates_a: np.ndarray | None = None
    replicates_b: np.ndarray | None = None


def _daily_rate_rows(
    a: SurveyFrames,
    b: SurveyFrames,
    measures: dict[str, tuple[np.ndarray, np.ndarray]],
    *,
    n_reps: int,
    seed: int,
) -> list[DailyRateRow]:
    """Aggregate trip quantities to days, retaining zeros (section 9.9)."""
    if n_reps <= 0:
        raise ValueError("n_reps must be positive")
    matrices = []
    for survey, frames in enumerate((a, b)):
        indices = _trip_day_index(frames)
        matrices.append(
            np.column_stack(
                [
                    np.bincount(
                        indices,
                        weights=values[survey],
                        minlength=len(frames.days["pond_jour"]),
                    )
                    for values in measures.values()
                ]
            )
        )
    rows = []
    for group in ("overall", *daily_energy.POPULATION_CATEGORIES):
        means, replicates, counts = [], [], []
        for frames, matrix, rng_seed in zip(
            (a, b), matrices, np.random.SeedSequence(seed).spawn(2), strict=True
        ):
            mask = (
                np.ones(len(matrix), dtype=bool)
                if group == "overall"
                else frames.days["population_category"] == group
            )
            counts.append(int(mask.sum()))
            weight = frames.days["pond_jour"][mask].astype(float)
            values = matrix[mask]
            means.append(
                np.average(values, axis=0, weights=weight)
                if mask.any()
                else np.full(len(measures), np.nan)
            )
            reps = np.full((n_reps, len(measures)), np.nan)
            if mask.any():
                rng = np.random.default_rng(rng_seed)
                for rep in range(n_reps):
                    w = weight * variation.household_multipliers(
                        frames.days["ident_men"][mask], rng
                    )
                    if w.sum() > 0:
                        reps[rep] = np.average(values, axis=0, weights=w)
            replicates.append(reps)

        def interval(values: np.ndarray) -> tuple[float, float]:
            valid = values[np.isfinite(values)]
            if not len(valid):
                return float("nan"), float("nan")
            lo, hi = np.percentile(valid, [2.5, 97.5])
            return float(lo), float(hi)

        for i, metric in enumerate(measures):
            rows.append(
                DailyRateRow(
                    group,
                    metric,
                    *counts,
                    float(means[0][i]),
                    float(means[1][i]),
                    interval(replicates[0][:, i]),
                    interval(replicates[1][:, i]),
                    interval(replicates[1][:, i] - replicates[0][:, i]),
                    replicates[0][:, i],
                    replicates[1][:, i],
                )
            )
    return rows


def motive_rate_checks(
    a: SurveyFrames,
    b: SurveyFrames,
    *,
    config: variation.MeasurementConfig,
    n_reps: int,
    seed: int,
) -> list[DailyRateRow]:
    """C3: motive and short-trip counts per category-day (section 9.9)."""
    measures = {
        motive_group_label(code): (
            a.trips["motive_group"].astype(str) == str(code),
            b.trips["motive_group"].astype(str) == str(code),
        )
        for code in MOTIVE_GROUP_LABELS
    }
    known_codes = np.array([str(code) for code in MOTIVE_GROUP_LABELS])
    measures["unknown motive"] = tuple(
        ~np.isin(frames.trips["motive_group"].astype(str), known_codes)
        for frames in (a, b)
    )
    measures[f"trips under {config.short_duration_min:g} min"] = tuple(
        frames.trips["duration_min"] < config.short_duration_min for frames in (a, b)
    )
    measures[f"trips under {config.short_distance_km:g} km (crow-fly)"] = tuple(
        np.isfinite(frames.trips["crow_fly_km"])
        & (frames.trips["crow_fly_km"] >= 0)
        & (frames.trips["crow_fly_km"] < config.short_distance_km)
        for frames in (a, b)
    )
    measures["intra-commune trips (crow-fly = 0)"] = tuple(
        frames.trips["crow_fly_km"] == 0 for frames in (a, b)
    )
    measures["total trips"] = tuple(
        np.ones(len(frames.trips["pond_jour"])) for frames in (a, b)
    )
    measures["total minutes"] = tuple(
        frames.trips["duration_min"].astype(float) for frames in (a, b)
    )
    measures["short-trip minutes"] = tuple(
        np.where(
            frames.trips["duration_min"] < config.short_duration_min,
            frames.trips["duration_min"],
            0.0,
        )
        for frames in (a, b)
    )
    return _daily_rate_rows(a, b, measures, n_reps=n_reps, seed=seed)


def _format_daily_rates(rows: list[DailyRateRow], unit: str) -> list[str]:
    lines = [
        f"| Category | Measure ({unit}) | n 2008 | 2008 [95% CI] | "
        "n 2019 | 2019 [95% CI] | Difference 2019 - 2008 [95% CI] |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        delta = row.mean_b - row.mean_a
        lines.append(
            f"| {row.group} | {row.metric} | {row.n_a} | "
            f"{_suppress(row.n_a, _ci_cell(row.mean_a, row.ci_a, 2))} | "
            f"{row.n_b} | {_suppress(row.n_b, _ci_cell(row.mean_b, row.ci_b, 2))} | "
            f"{_suppress(min(row.n_a, row.n_b), _ci_cell(delta, row.delta_ci, 2))} |"
        )
    return lines


def _format_sequence_motive_summary(
    summary: tuple[list[tuple[float | None, int, int]], int],
) -> list[str]:
    """Render EMP's unweighted `MOT_SEQ_COMPL` option at sequence level."""
    rows, missing_id_rows = summary
    lines = [
        "### C3 option: EMP 2019 sequence activity (`MOT_SEQ_COMPL`)",
        "",
        "Unweighted counts; each `IDENT_SEQ` is counted once. "
        "`MOT_SEQ_COMPL` is the dominant activity of a sequence between "
        "home, usual workplace and place of study (SDES, November 2024), "
        "not a trip motive. Cells with fewer than 50 respondents are "
        "suppressed.",
        "",
        "| Sequence activity | Unique sequences | Respondents |",
        "|---|---:|---:|",
    ]
    for motive, sequence_count, respondent_count in rows:
        label = (
            "missing/refused"
            if motive is None
            else emp2019.MOTIVE_LABEL_BY_CODE.get(motive, f"code {motive:g}")
        )
        lines.append(
            f"| {label} | "
            f"{_suppress(respondent_count, f'{sequence_count:,}')} | "
            f"{_suppress(respondent_count, f'{respondent_count:,}')} |"
        )
    if not rows:
        lines.append("| No sequences with an `IDENT_SEQ` | 0 | 0 |")
    if missing_id_rows:
        lines += [
            "",
            f"{missing_id_rows:,} trip rows without `IDENT_SEQ` are excluded "
            "from this sequence-level summary.",
        ]
    return lines


def measurement_checks(
    a: SurveyFrames,
    b: SurveyFrames,
    *,
    config: variation.MeasurementConfig,
    n_reps: int,
    seed: int,
    results: dict | None = None,
) -> list[str]:
    """Render section C, reusing B2/B4b and household bootstrap (section 9.9)."""
    rounding = rounding_checks(a, b, config=config, seed=seed)
    rates = motive_rate_checks(a, b, config=config, n_reps=n_reps, seed=seed)
    if results is not None:
        results["rounding_checks"] = rounding
        results["motive_rates"] = rates
    hidden_rates = {"total trips", "total minutes", "short-trip minutes"}
    lines = [
        "## C. Measurement checks",
        "",
        "Weekday person-days with needs-scope trips, day weights; the same "
        "denominator as B2. Section 9.9. Small-cell suppression is unchanged.",
        "",
        "### C1. Rounding bounds",
        "",
        f"{config.rounding_draws} draws per variant; change = simulated minus "
        "observed ENTD 2008 minutes per day with trips. The mean and full "
        "simulation range are sensitivity bounds, not confidence intervals. "
        "Levels are 1, 5, 15 and 30 min, assigned by the largest multiple "
        "each duration is (zero is a multiple of 30). Nearest ties round upward. "
        "The minimum variant clips newly rounded values to 5 min; unchanged "
        "short trips are not floored.",
        "",
        "Cells are mode x original duration class in each survey. The 2008 "
        "classes remain fixed after rounding. At each level, finest first, "
        "p = max(0, target share - current share) / eligible share, capped at 1. "
        "Only trips that can attain that level are eligible; no duration is "
        "made finer. Targets below existing shares do not undo rounding. "
        "Empty 2019 cells leave 2008 unchanged (no pooled fallback). Achieved "
        "shares can exceed targets or vary stochastically; they are shown below.",
        "",
        "| Variant | Category | n 2008 | Mean change min/day | Range |",
        "|---|---|---|---|---|",
    ]
    for variant, groups in rounding["changes"].items():
        for group, values in groups.items():
            n = (
                len(a.days["pond_jour"])
                if group == "overall"
                else int(np.sum(a.days["population_category"] == group))
            )
            lines.append(
                f"| {variant} | {group} | {n} | "
                f"{_suppress(n, _num(float(np.mean(values)), 2))} | "
                f"{_suppress(n, f'[{_num(min(values), 2)}, {_num(max(values), 2)}]')} |"
            )
    lines += [
        "",
        "Cumulative day-weighted trip shares at or above each level. "
        "Simulated shares are mean [min, max] across draws, within original "
        "2008 cells; 2019 shares use original 2019 cells.",
        "",
        "| Variant | Mode | Original duration class | Level (min) | n 2008 | "
        "Simulated 2008 share | n 2019 | 2019 share |",
        "|---|---|---|---|---|---|---|---|",
    ]
    codes_a, shape = _rounding_cells(a, config)
    codes_b, _ = _rounding_cells(b, config)
    counts_a = np.bincount(codes_a, minlength=shape[0] * shape[1]).reshape(shape[:2])
    counts_b = np.bincount(codes_b, minlength=shape[0] * shape[1]).reshape(shape[:2])
    class_labels = ("<5", "5-9", "10-14", "15-29", "30-59", "60+")
    for variant, shares in rounding["shares"].items():
        for i, mode in enumerate(MODE7_LABELS):
            for j, label in enumerate(class_labels):
                for k, level in enumerate(config.rounding_levels):
                    values = shares[:, i, j, k]
                    simulated = (
                        f"{_pct(float(np.mean(values)))} "
                        f"[{_pct(float(np.min(values)))}, "
                        f"{_pct(float(np.max(values)))}]"
                    )
                    target = _pct(rounding["target"][i, j, k])
                    lines.append(
                        f"| {variant} | {mode} | {label} min | {level} | "
                        f"{counts_a[i, j]} | {_suppress(counts_a[i, j], simulated)} | "
                        f"{counts_b[i, j]} | "
                        f"{_suppress(counts_b[i, j], target)} |"
                    )
    lines += [
        "",
        "### C2. Common distance measures",
        "",
        "No speed correction in either year. Crow-fly uses `V2_DVO_LOC` "
        "and `dVO_ORIDES`; neither falls back to another measure. "
        "Missing, non-finite or negative distances remain unknown. N and T "
        "retain all trips/days. Km/person-day sums known km over all days with "
        "trips (a lower bound when distances are missing); B2 coverage and "
        "the unknown-distance band expose this limitation. CIs resample "
        "households independently in the two surveys.",
        "",
    ]
    for column, label in (("crow_fly_km", "crow-fly"),):
        ca, cb = common_distance_frames(a, column), common_distance_frames(b, column)
        lines += _format_b2(
            results["b2_rows"]
            if results is not None
            else b2_decompositions(ca, cb, n_reps=n_reps, seed=seed),
            "2008",
            "2019",
            title=f"#### {label}: B2",
            distance_description=f"raw {label} distances, no speed correction",
        )
        lines += [
            "",
            *_format_daily_rates(
                _daily_rate_rows(
                    ca,
                    cb,
                    {
                        "km per person-day": (
                            np.nan_to_num(ca.trips["distance_km"], nan=0.0),
                            np.nan_to_num(cb.trips["distance_km"], nan=0.0),
                        )
                    },
                    n_reps=n_reps,
                    seed=seed,
                ),
                "km/day with trips",
            ),
        ]
        lines += [
            "",
            *_format_shift_share(
                shift_share_by(ca, cb, "distance_band", n_reps=n_reps, seed=seed),
                _group_counts(ca, "distance_band"),
                _group_counts(cb, "distance_band"),
                title=f"#### {label}: B4b distance-band shift-share",
                group_name="band",
                label_a="2008",
                label_b="2019",
                group_order=DISTANCE_BAND_LABELS,
                within_label="within bands",
                intro=f"Raw {label} bands; no speed correction. "
                "Household-bootstrap 95% CIs.",
            ),
        ]
        durations = _format_b4_durations(ca, cb)
        durations[0] = f"#### {label}: B4b trip-duration distributions"
        lines += ["", *durations]
    lines += [
        "",
        "### C3. Trips by motive: harmonised return-home rule",
        "",
        "EMP 2019's raw destination motive is replaced by its raw origin motive "
        "for returns to home or a residence (codes 1.1-1.3), matching ENTD "
        "2008's rule. This reassigned motive drives both needs scope and motive "
        "groups. Each category denominator includes days with zero trips for "
        "that motive. n counts all category person-days, not just motive users. "
        "Short-trip rows use strict < thresholds; missing crow-fly distances "
        "are not short trips. Thus short-distance rates are lower bounds if "
        "crow-fly distances are missing. Household-bootstrap 95% CIs for each "
        "year and the difference, with independent survey resamples.",
        "Unemployed and other-inactive respondents' “professional” and "
        "“home/study” changes reflect motive coding, not behaviour.",
        "",
        *_format_daily_rates(
            [row for row in rates if row.metric not in hidden_rates],
            "trips/day with trips",
        ),
    ]
    sequence_summary = b.aux.get("sequence_motive_summary")
    if sequence_summary is None:
        raise ValueError("C3 requires the EMP 2019 sequence-level motive summary")
    lines += ["", *_format_sequence_motive_summary(sequence_summary)]
    return lines


@dataclass(frozen=True)
class MeasurementLedgerRow:
    """C4 effects on minutes/day, trips/day and minutes/trip (section 9.9)."""

    key: str
    label: str
    effect: np.ndarray
    bounds: np.ndarray
    source: str
    n: int
    note: str = ""


@dataclass(frozen=True)
class MeasurementLedger:
    """C4 estimates and a sensitivity envelope, not a joint confidence interval."""

    rows: tuple[MeasurementLedgerRow, ...]
    observed: np.ndarray
    residual_bounds: np.ndarray
    residual_bounds_with_composition: np.ndarray
    n: int
    diagnostics: tuple[str, ...]


def _ledger_interval(values: np.ndarray) -> np.ndarray:
    """Percentile 95% interval from existing finite household replicates."""
    valid = values[np.isfinite(values)]
    return np.percentile(valid, [2.5, 97.5]) if len(valid) else np.full(2, np.nan)


def _ledger_metrics(
    rates: list[DailyRateRow], side: str, summary: LagRow | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Reuse C3 totals and their joint replicates; minutes/trip is T/N."""
    overall = {row.metric: row for row in rates if row.group == "overall"}
    time, trips = overall["total minutes"], overall["total trips"]
    t, n = getattr(time, f"mean_{side}"), getattr(trips, f"mean_{side}")
    rt = getattr(time, f"replicates_{side}")
    rn = getattr(trips, f"replicates_{side}")
    if rt is None or rn is None:
        raise ValueError("C4 requires the cached C3 household replicates")
    ratio = np.divide(rt, rn, out=np.full_like(rt, np.nan), where=rn > 0)
    point = (
        np.array(
            [summary.time_per_day_min, summary.trips_per_day, summary.minutes_per_trip]
        )
        if summary is not None
        else np.array([t, n, t / n])
    )
    return point, np.column_stack([rt, rn, ratio])


def _calendar_cells(frames: SurveyFrames) -> np.ndarray:
    """A5 weekday x month cells, retaining missing components explicitly."""
    days = frames.days
    weekdays = np.zeros(len(days["pond_jour"]), dtype=int)
    months = np.zeros_like(weekdays)
    weekday_names = np.char.lower(
        np.char.strip(days["described_weekday_name"].astype(str))
    )
    month_names = np.char.lower(np.char.strip(days["described_month_name"].astype(str)))
    for label, code in _FRENCH_WEEKDAY_NUM.items():
        weekdays[weekday_names == label] = code
    for label, code in _FRENCH_MONTH_NUM.items():
        months[month_names == label] = code
    return weekdays * (len(_FRENCH_MONTH_NUM) + 1) + months


def _calendar_and_recall_effects(
    a: SurveyFrames,
    b: SurveyFrames,
    results: dict,
    b_reps: np.ndarray,
    *,
    n_reps: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str, int]:
    """C4b/f: new paired contrasts on the existing household-bootstrap draws."""
    if n_reps <= 0 or len(b_reps) != n_reps:
        raise ValueError("C4 must use the same positive replicate count as C3")
    lag_rows = results["lag_table"]
    all_days = lag_rows[-1]
    observed = np.array(
        [
            all_days.time_per_day_min,
            all_days.trips_per_day,
            all_days.minutes_per_trip,
        ]
    )
    early = [row for row in lag_rows if row.label in ("1", "2", "3")]
    early_n = sum(row.n_days for row in early)
    known_early = [row for row in early if row.n_days > 0]
    early_means = np.full(3, np.nan)
    if known_early:
        mix = np.array([row.weighted_share for row in known_early])
        t = np.average([row.time_per_day_min for row in known_early], weights=mix)
        n = np.average([row.trips_per_day for row in known_early], weights=mix)
        early_means = np.array([t, n, t / n])
    early_mask = np.isfinite(b.days["recall_lag"]) & (
        (b.days["recall_lag"] >= 1) & (b.days["recall_lag"] <= 3)
    )
    codes_a, codes_b = _calendar_cells(a), _calendar_cells(b)
    n_cells = (len(_FRENCH_WEEKDAY_NUM) + 1) * (len(_FRENCH_MONTH_NUM) + 1)
    values = np.column_stack([b.days["total_time_min"], b.days["trips_per_day"]])
    weight_a = a.days["pond_jour"].astype(float)
    weight_b = b.days["pond_jour"].astype(float)

    def calendar_means(wa: np.ndarray, wb: np.ndarray) -> np.ndarray:
        target = np.bincount(codes_a, weights=wa, minlength=n_cells)
        source = np.bincount(codes_b, weights=wb, minlength=n_cells)
        if wa.sum() <= 0 or np.any((target > 0) & (source <= 0)):
            return np.full(3, np.nan)
        factors = np.divide(target, source, out=np.zeros(n_cells), where=source > 0)
        weights = wb * factors[codes_b]
        t, n = np.average(values, axis=0, weights=weights)
        return np.array([t, n, t / n])

    calendar = observed - calendar_means(weight_a, weight_b)
    target = np.bincount(codes_a, weights=weight_a, minlength=n_cells)
    source = np.bincount(codes_b, weights=weight_b, minlength=n_cells)
    unmatched = float(target[source <= 0].sum() / target.sum())
    note = (
        "Observed minus EMP reweighted to the ENTD weekday x month mix. "
        "Missing weekday/month components remain explicit cells. "
        f"Unmatched target weight: {_pct(unmatched)}."
    )
    if unmatched > 0:
        note += " Calendar effect unavailable; no pooling or renormalisation."
    recall_reps = np.full_like(b_reps, np.nan)
    calendar_reps = np.full_like(b_reps, np.nan)
    seed_a, seed_b = np.random.SeedSequence(seed).spawn(2)
    rng_a, rng_b = np.random.default_rng(seed_a), np.random.default_rng(seed_b)
    for rep in range(n_reps):
        wa = weight_a * variation.household_multipliers(a.days["ident_men"], rng_a)
        wb = weight_b * variation.household_multipliers(b.days["ident_men"], rng_b)
        if wb[early_mask].sum() > 0:
            t, n = np.average(values[early_mask], axis=0, weights=wb[early_mask])
            recall_reps[rep] = b_reps[rep] - np.array([t, n, t / n])
        calendar_reps[rep] = b_reps[rep] - calendar_means(wa, wb)
    if unmatched > 0:
        calendar_reps[:] = np.nan
    valid_calendar_reps = int(np.isfinite(calendar_reps).all(axis=1).sum())
    note += f" Valid calendar replicates: {valid_calendar_reps}/{n_reps}."
    return (
        observed - early_means,
        np.array([_ledger_interval(col) for col in recall_reps.T]),
        calendar,
        np.array([_ledger_interval(col) for col in calendar_reps.T]),
        note,
        early_n,
    )


def measurement_ledger(
    a: SurveyFrames,
    b: SurveyFrames,
    results: dict,
    *,
    config: variation.MeasurementConfig,
    n_reps: int,
    seed: int,
) -> MeasurementLedger:
    """C4 measurement effects and extreme-bound residuals (section 9.9).

    Existing C1/A1/B1/B2/C3 estimates are consumed, never rerun. Short-trip
    restoration is negated to express measurement bias; calendar effects
    likewise use observed minus reweighted EMP. Effects need not be additive.
    """
    rates = results["motive_rates"]
    point_a, reps_a = _ledger_metrics(rates, "a", results["entd_overall"])
    point_b, reps_b = _ledger_metrics(rates, "b", results["lag_table"][-1])
    n = min(len(a.days["pond_jour"]), len(b.days["pond_jour"]))
    observed = point_b - point_a
    changes = results["rounding_checks"]["changes"]
    draws = np.array([*changes["nearest"]["overall"], *changes["up"]["overall"]])
    rounding_bounds = np.array(
        [
            [draws.min(), draws.max()],
            [0.0, 0.0],
            [draws.min() / point_a[1], draws.max() / point_a[1]],
        ]
    )
    rows = [
        MeasurementLedgerRow(
            "a",
            "Duration rounding",
            np.array([draws.mean(), 0.0, draws.mean() / point_a[1]]),
            rounding_bounds,
            "C1",
            n,
            "Nearest and round-up draw extrema; minutes/trip divides by "
            "2008 trips/day. Bounds, not a confidence interval.",
        )
    ]
    recall, recall_bounds, calendar, calendar_bounds, calendar_note, early_n = (
        _calendar_and_recall_effects(a, b, results, reps_b, n_reps=n_reps, seed=seed)
    )
    rows.append(
        MeasurementLedgerRow(
            "b",
            "Recall lag",
            recall,
            recall_bounds,
            "A1",
            min(n, early_n),
            "EMP all days minus lag 1-3 days; missing lag stays in all days. "
            "Paired household-bootstrap 95% CIs."
            + (" No lag 1-3 days: unavailable." if not early_n else ""),
        )
    )
    crow = results["b2_rows"][0].result
    corrected = results["b2_rows_corrected"][0].result
    distance_note = "Changes the decomposition only, not the totals."
    if crow is None or corrected is None:
        distance_note += " The km/trip-term contrast is unavailable."
    else:
        distance_bounds = (
            np.asarray(corrected.distance_ci) - np.asarray(crow.distance_ci)[::-1]
        )
        distance_note += (
            " Corrected minus crow-fly km/trip term: "
            + _ci_cell(
                corrected.point.distance_min - crow.point.distance_min,
                distance_bounds,
                2,
            )
            + " min/day (marginal-CI envelope, not a contrast CI)."
        )
    rows.append(
        MeasurementLedgerRow(
            "d",
            "Distance measurement",
            np.zeros(3),
            np.zeros((3, 2)),
            "B2 sensitivity / B2",
            n,
            distance_note,
        )
    )
    overall = {row.metric: row for row in rates if row.group == "overall"}
    short = overall[f"trips under {config.short_duration_min:g} min"]
    short_time = overall["short-trip minutes"]
    assert short.replicates_a is not None and short.replicates_b is not None
    assert short_time.replicates_a is not None
    deficit = short.mean_a - short.mean_b
    mean_short = short_time.mean_a / short.mean_a if short.mean_a > 0 else np.nan
    restored_time = deficit * mean_short if deficit != 0 else 0.0
    restored_trips = point_b[1] + deficit
    restoration = np.array(
        [
            restored_time,
            deficit,
            (point_b[0] + restored_time) / restored_trips - point_b[2]
            if restored_trips > 0
            else np.nan,
        ]
    )
    deficit_reps = short.replicates_a - short.replicates_b
    mean_short_reps = np.divide(
        short_time.replicates_a,
        short.replicates_a,
        out=np.full(n_reps, np.nan),
        where=short.replicates_a > 0,
    )
    added_time = np.where(deficit_reps != 0, deficit_reps * mean_short_reps, 0.0)
    adjusted_ratio = np.divide(
        reps_b[:, 0] + added_time,
        reps_b[:, 1] + deficit_reps,
        out=np.full(n_reps, np.nan),
        where=reps_b[:, 1] + deficit_reps > 0,
    )
    short_effect_reps = -np.column_stack(
        [added_time, deficit_reps, adjusted_ratio - reps_b[:, 2]]
    )
    short_bounds = np.array([_ledger_interval(col) for col in short_effect_reps.T])
    short_days = np.bincount(
        _trip_day_index(a),
        weights=a.trips["duration_min"] < config.short_duration_min,
        minlength=len(a.days["pond_jour"]),
    )
    short_n = (
        min(n, int(np.sum(short_days > 0))) if short.mean_a > 0 or deficit != 0 else n
    )
    rows.append(
        MeasurementLedgerRow(
            "e",
            "Short trips missing in 2019",
            -restoration,
            short_bounds,
            "C3 / C4",
            short_n,
            "Bias = observed minus restored EMP; restoration adds the "
            f"2008-minus-2019 rate of trips under {config.short_duration_min:g} "
            "min at their 2008 mean duration. Household-bootstrap 95% CIs."
            f" Restoration (adjusted minus observed): {restoration[0]:+.3f} "
            f"min/day, {restoration[1]:+.3f} trips/day, "
            f"{restoration[2]:+.3f} min/trip."
            + (
                " No 2008 short trips: time/mean-duration effects unavailable."
                if short.mean_a <= 0 and deficit != 0
                else ""
            ),
        )
    )
    rows.append(
        MeasurementLedgerRow(
            "f",
            "Calendar",
            calendar,
            calendar_bounds,
            "A5 / C4",
            n,
            calendar_note + " Household-bootstrap 95% CIs.",
        )
    )
    composition = next(row for row in results["b1_rows"] if row.variant == "V2")
    if composition.ledger_effect is None or composition.ledger_bounds is None:
        raise ValueError("C4 requires B1 V2 time/trip composition estimates")
    rows.append(
        MeasurementLedgerRow(
            "g",
            "Composition (not a measurement effect)",
            composition.ledger_effect,
            composition.ledger_bounds,
            "B1 V2",
            n,
            "2008 reweighted to 2019 structure using the existing V2 cells "
            "and household draws. Household-bootstrap 95% CIs; excluded "
            "from the residual.",
        )
    )
    residual_effects = {row.key: row.bounds for row in rows if row.key in "abefg"}
    residual_bounds = (
        observed[:, None]
        - np.sum([residual_effects[key] for key in "abef"], axis=0)[:, ::-1]
    )
    residual_bounds_with_composition = (
        observed[:, None]
        - np.sum([residual_effects[key] for key in "abefg"], axis=0)[:, ::-1]
    )
    diagnostics = []
    delta_trips = observed[1]
    delta_trip_reps = reps_b[:, 1] - reps_a[:, 1]
    for metric in (
        f"trips under {config.short_duration_min:g} min",
        "intra-commune trips (crow-fly = 0)",
    ):
        rate = overall[metric]
        assert rate.replicates_a is not None and rate.replicates_b is not None
        delta_reps = rate.replicates_b - rate.replicates_a
        share_reps = np.divide(
            delta_reps,
            delta_trip_reps,
            out=np.full(n_reps, np.nan),
            where=delta_trip_reps != 0,
        )
        share = (
            _pct((rate.mean_b - rate.mean_a) / delta_trips)
            if delta_trips != 0
            else "undefined (zero total trip change)"
        )
        share_bounds = _ledger_interval(share_reps)
        diagnostics.append(
            f"{metric}: 2019 - 2008 = "
            f"{_ci_cell(rate.mean_b - rate.mean_a, rate.delta_ci, 3)} trips/day; "
            f"share of total trip change = {share} "
            f"[{_pct(share_bounds[0])}, {_pct(share_bounds[1])}] (95% CIs)."
        )
    diagnostics += [
        "Forgotten trips lower measured time "
        "and raise mean duration when the missing trips are shorter. "
        "The table reports the opposite signs (measurement bias).",
        "Intra-commune is the zero-crow-fly convention, not a commune-code "
        "join; missing/negative crow-fly distances do not count as zero. "
        "The short-duration and intra-commune diagnostics overlap and are "
        "not added together.",
    ]
    return MeasurementLedger(
        tuple(rows),
        observed,
        residual_bounds,
        residual_bounds_with_composition,
        n,
        tuple(diagnostics),
    )


def _format_measurement_ledger(ledger: MeasurementLedger) -> list[str]:
    """Render C4 with existing suppression and explicitly non-additive bounds."""
    lines = [
        "### C4. Measurement ledger",
        "",
        "Weekday person-days with needs-scope trips, day weights (section 9.9). "
        "T = minutes/day, N = trips/day, M = weighted total minutes/trips "
        "(not an average of person-day ratios). Brackets below are ordered "
        "T; N; M. Unavailable estimates print `-`.",
        "",
        "| Difference | Effect on time change (min/day) | "
        "Effect on trips/day change | Effect on min/trip change | "
        "Interval or bounds (T; N; M) | Source section |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in ledger.rows:
        cells = [
            _suppress(
                row.n,
                f"[{_num(low, 3)}, {_num(high, 3)}]"
                if row.key == "a" and index != 1
                else _num(value, 3),
            )
            for index, (value, (low, high)) in enumerate(
                zip(row.effect, row.bounds, strict=True)
            )
        ]
        bounds = "; ".join(
            f"[{_num(low, 3)}, {_num(high, 3)}]" for low, high in row.bounds
        )
        lines.append(
            f"| {row.key}. {row.label} | "
            + " | ".join(cells)
            + f" | {_suppress(row.n, bounds)} | {row.source} |"
        )
    lines += [
        "",
        "A positive effect means the difference raises the measured 2019 value "
        "(and hence the 2008 -> 2019 change). Row e reports measurement bias, "
        "not the opposite-signed restoration. Row f likewise reports observed "
        "minus calendar-reweighted EMP, not the correction.",
        "",
    ]
    for row in ledger.rows:
        if row.n >= MIN_CELL_N:
            lines.append(f"- {row.key}: {row.note}")
        elif not np.isfinite(row.effect).all():
            lines.append(
                f"- {row.key}: unavailable (missing or suppressed reference sample)."
            )
    if ledger.n >= MIN_CELL_N:
        lines += ["", *[f"- {note}" for note in ledger.diagnostics]]
    residual_n = min(ledger.n, *(row.n for row in ledger.rows if row.key in "abef"))
    composition_residual_n = min(
        residual_n, next(row.n for row in ledger.rows if row.key == "g")
    )
    lines += [
        "",
        "#### Residual change",
        "",
        "| Quantity | Time (min/day) | Trips/day | Minutes/trip |",
        "|---|---:|---:|---:|",
        "| Observed change | "
        + " | ".join(_suppress(ledger.n, _num(v, 3)) for v in ledger.observed)
        + " |",
        "| Residual (removing a, b, e, f) | "
        + " | ".join(
            _suppress(residual_n, f"[{_num(lo, 3)}, {_num(hi, 3)}]")
            for lo, hi in ledger.residual_bounds
        )
        + " |",
        "| Residual (also removing g, composition) | "
        + " | ".join(
            _suppress(composition_residual_n, f"[{_num(lo, 3)}, {_num(hi, 3)}]")
            for lo, hi in ledger.residual_bounds_with_composition
        )
        + " |",
        "",
        "Both residual ranges exclude c (motive processing), since the main "
        "comparison already uses the harmonised motive rule. The first removes "
        "a, b, e and f; the second also removes g (composition). Each range is "
        "observed change minus the highest/lowest combinations of the selected "
        "effect bounds. These are sensitivity ranges, not a confidence interval: CIs "
        "are not added across rows, and overlapping checks are not an "
        "identified causal decomposition. Distance is excluded. Missing "
        "required effects make the corresponding residual unavailable.",
    ]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Step-12 travel-time variation report (Parts A, B and C)."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--emp2019-data-path", type=Path, default=None)
    parser.add_argument("--entd2008-data-path", type=Path, default=None)
    parser.add_argument(
        "--entd2008-zoning-data-path",
        type=Path,
        required=True,
        help="SDES ENTD 2008 tables enriched with 2020 zoning variables",
    )
    parser.add_argument(
        "--sample-households",
        type=float,
        default=None,
        help="Keep only this percentage of households per survey "
        "(stable hash), for smoke runs.",
    )
    args = parser.parse_args(argv)
    results = run(
        args.out,
        args.config,
        n_reps=args.bootstrap_reps,
        seed=args.seed,
        emp2019_data_path=args.emp2019_data_path,
        entd2008_data_path=args.entd2008_data_path,
        entd2008_zoning_data_path=args.entd2008_zoning_data_path,
        sample_pct=args.sample_households,
    )
    md_path = args.out.with_suffix(".md")
    write_markdown(md_path, args.out, results)
    print(f"Wrote {md_path} and {len(results['figures'])} figures to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
