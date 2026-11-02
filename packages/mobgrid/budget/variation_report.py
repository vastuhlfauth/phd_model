"""Step-12 travel-time variation report (Parts A and B).

``python -m mobgrid.budget.variation_report --out docs/data/step12_variation``
re-runs the step-11 loaders (``mobgrid.budget.emp2019``/``entd2008``,
``trip_legs``) unchanged, extracts weekday person-days with trips in the
needs scope with their day weights, and writes the step-12 report: the
survey-method checks of Part A (recall lag, motive crosswalk, distances,
durations, calendar) and the decompositions of Part B (composition,
trips x distance x speed, mode/motive/distance shift-shares, tails, the
comparison pairs and their figures). Step-11 outputs are not touched.

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
)

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
    """One survey's step-12 extraction: weekday, needs-scope person-days
    with trips (``days``) and their trips (``trips``), as numpy column
    dicts, plus the in-SQL Part A diagnostics (``aux``)."""

    name: str
    days: dict[str, np.ndarray]
    trips: dict[str, np.ndarray]
    aux: dict


def _sample_sql(sample_pct: float | None) -> str:
    if sample_pct is None:
        return "TRUE"
    return f"(hash(CAST(ident_men AS VARCHAR)) % 100) < {float(sample_pct):g}"


def _create_person_ext_emp2019(con: duckdb.DuckDBPyConnection) -> None:
    """EMP 2019 person-level extras: sex, recall lag (`MDATE_delai`, 1-7
    days between the described day and the interview), the described
    day's weekday/month (`MDATE_jour`/`MDATE_mois`, French names),
    Île-de-France residence (`REG_res`), household cars (`JNBVEH`)."""
    con.sql("""
        CREATE OR REPLACE VIEW vr_person AS
        SELECT
            i.IDENT_IND AS ident_ind,
            TRY_CAST(k.SEXE AS INTEGER) AS sex,
            TRY_CAST(i.MDATE_delai AS INTEGER) AS recall_lag,
            CAST(i.MDATE_jour AS VARCHAR) AS described_weekday_name,
            CAST(i.MDATE_mois AS VARCHAR) AS described_month_name,
            coalesce(CAST(m.REG_res AS VARCHAR) = 'Ile-de-France', FALSE)
                AS is_idf,
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
            TRY_CAST(dVO_ORIDES AS DOUBLE) AS crow_fly_km,
            TRY_CAST(NEW_VAC_SCOL AS INTEGER) AS vac_scol
        FROM k_deploc
    """)


def _create_person_ext_entd2008(con: duckdb.DuckDBPyConnection) -> None:
    """ENTD 2008 person-level extras: sex, recall lag in calendar days
    between the reference weekday described (`V2_DATESEMREF`) and the
    second visit (`MDATENQ2V`, when trips are collected), the reference
    day's weekday/month, Île-de-France residence (`RG` = 11). Household
    cars are not in the four public tables used by step 11 (no
    `JNBVEH` equivalent): `cars_band` is 'unknown' throughout."""
    con.sql("""
        CREATE OR REPLACE VIEW vr_person AS
        WITH dates AS (
            SELECT IDENT_IND,
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
            'unknown' AS cars_band
        FROM dates d
        LEFT JOIN q_tcm_individu q ON q.IDENT_IND = d.IDENT_IND
    """)
    con.sql("""
        CREATE OR REPLACE VIEW vr_trip_ext AS
        SELECT IDENT_DEP AS ident_dep,
            TRY_CAST(V2_DVO_LOC AS DOUBLE) AS crow_fly_km,
            TRY_CAST(V2_VAC_SCOL AS INTEGER) AS vac_scol
        FROM k_deploc
    """)


_PERSON_EXT_BY_SURVEY = {
    "EMP 2019": _create_person_ext_emp2019,
    "ENTD 2008": _create_person_ext_entd2008,
}


def _create_frames_tables(
    con: duckdb.DuckDBPyConnection, *, sample_pct: float | None
) -> None:
    """Materialise ``vr_trips``/``vr_days``: weekday (typejour = 1),
    needs-scope trips with a positive day weight, and their person-days,
    with the step-12 extra columns."""
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
            e.crow_fly_km, e.vac_scol,
            p.sex, p.recall_lag, p.described_weekday_name,
            p.described_month_name, p.is_idf, p.cars_band
        FROM trip_legs t
        LEFT JOIN vr_person p ON p.ident_ind = t.ident_ind
        LEFT JOIN vr_trip_ext e ON e.ident_dep = t.ident_dep
        WHERE t.typejour = 1 AND t.pond_jour > 0
            AND ({trip_legs.NEEDS_ONLY_WHERE_SQL})
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
            sum(distance_km) AS total_distance_km
        FROM vr_trips
        GROUP BY day_id
    """)


def _needs_scope_removal(con: duckdb.DuckDBPyConnection) -> dict:
    """A2's scope check: the weighted share of weekday trips and of
    weekday time removed by the needs scope."""
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
    sample_pct: float | None = None,
) -> SurveyFrames:
    """Build one survey's step-12 frames, reusing the step-11 loaders
    unchanged (``survey.extract_tables``/``register_views``/
    ``build_trip_legs``)."""
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
        survey.build_trip_legs(con, config, density_source=density_source)
        _PERSON_EXT_BY_SURVEY[survey.SURVEY_NAME](con)
        _create_frames_tables(con, sample_pct=sample_pct)
        days = con.sql("SELECT * FROM vr_days").fetchnumpy()
        trips = con.sql("SELECT * FROM vr_trips").fetchnumpy()
        motive_shares, distance_doc = _AUX_BY_SURVEY[survey.SURVEY_NAME]
        aux = {
            "needs_scope_removal": _needs_scope_removal(con),
            "raw_motive_shares": motive_shares(con),
            "distance_doc": distance_doc(con),
        }
    finally:
        con.close()
    days = {k: _plain_array(v) for k, v in days.items()}
    trips = {k: _plain_array(v) for k, v in trips.items()}
    return SurveyFrames(name=survey.SURVEY_NAME, days=days, trips=trips, aux=aux)


def _plain_array(column: np.ndarray) -> np.ndarray:
    """Convert a DuckDB masked array to a plain array (NaN/None fill)."""
    if isinstance(column, np.ma.MaskedArray):
        if column.dtype.kind in "fiu":
            return column.astype(float).filled(np.nan)
        return column.filled(None)
    return column


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
    population-category x density-class fixed effects, weekday days."""
    days = frames.days
    lag = days["recall_lag"].astype(float)
    keep = np.isfinite(lag) & (lag >= 1) & (lag <= 7)
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
    design = np.ones((len(y), 1 + len(lag_levels) + len(stratum_levels)))
    for j, level in enumerate(lag_levels):
        design[:, 1 + j] = lag == level
    for j, level in enumerate(stratum_levels):
        design[:, 1 + len(lag_levels) + j] = strata == level

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
    """Band index (into ``DISTANCE_BAND_LABELS``) of each trip distance."""
    return np.searchsorted(
        np.asarray(DISTANCE_BAND_UPPER_KM[:-1]), distance_km, side="right"
    )


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
        "population-category x density-class controls, household-bootstrap "
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
    lines += [
        "### Needs scope",
        "",
        "Weighted share of weekday trips and time removed by the needs "
        "scope (motives 7.6-7.8 and 8.x):",
        "",
        "| Survey | Trips removed | Time removed |",
        "|---|---|---|",
        f"| ENTD 2008 | {_pct(removal_2008['share_trips_removed'])} | "
        f"{_pct(removal_2008['share_time_removed'])} |",
        f"| EMP 2019 | {_pct(removal_2019['share_trips_removed'])} | "
        f"{_pct(removal_2019['share_time_removed'])} |",
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
        "analysis: weekday person-days with at least one trip, needs "
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
    ]
    for extra in results.get("extra_sections", []):
        lines += ["", *extra]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


#: Standing "Choices made" entries (prompt: "If a variable is missing or
#: ambiguous, choose, write the choice in the report under 'Choices
#: made', and continue").
BASE_CHOICES = [
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
    "The motive crosswalk reports raw code shares before the needs "
    "scope and before the return-trip motive reassignment, so both "
    "surveys' code inventories are visible.",
    "Distance bands use step 11's corrected distances "
    "(`trip_legs.distance_km`): the speed-plausibility correction "
    "replaces implausible declared distances, as in every step-11 "
    "table.",
]


def run(
    out_dir: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    n_reps: int = 200,
    seed: int = 0,
    emp2019_data_path: Path | None = None,
    entd2008_data_path: Path | None = None,
    sample_pct: float | None = None,
) -> dict:
    """Compute every step-12 statistic and figure; returns the results
    dict consumed by ``write_markdown`` and the tests."""
    out_dir.mkdir(parents=True, exist_ok=True)
    config = load_energy_config(config_path)
    frames_2008 = load_frames(
        entd2008,
        entd2008_data_path,
        config,
        density_source="proxy",
        sample_pct=sample_pct,
    )
    frames_2019 = load_frames(
        emp2019,
        emp2019_data_path,
        config,
        density_source="proxy",
        sample_pct=sample_pct,
    )
    frames_2019_grid = load_frames(
        emp2019,
        emp2019_data_path,
        config,
        density_source="grid",
        sample_pct=sample_pct,
    )
    results: dict = {
        "n_reps": n_reps,
        "seed": seed,
        "sample_pct": sample_pct,
        "choices": list(BASE_CHOICES),
        "n_days_2008": len(frames_2008.days["pond_jour"]),
        "n_trips_2008": len(frames_2008.trips["pond_jour"]),
        "n_days_2019": len(frames_2019.days["pond_jour"]),
        "n_trips_2019": len(frames_2019.trips["pond_jour"]),
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
        # A3
        "distance_doc_2008": frames_2008.aux["distance_doc"],
        "distance_doc_2019": frames_2019.aux["distance_doc"],
        "distance_bands_2008": distance_band_table(frames_2008),
        "distance_bands_2019": distance_band_table(frames_2019),
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
    )


@dataclass(frozen=True)
class B2Row:
    """One B2 row: the trips x km x speed split of the daily-time change
    for one group of person-days (overall or one category)."""

    group: str
    n_a: int
    n_b: int
    result: variation.TripTimeDecompositionBootstrap | None


def b2_decompositions(
    frames_a: SurveyFrames,
    frames_b: SurveyFrames,
    *,
    n_reps: int,
    seed: int,
) -> list[B2Row]:
    """B2 (``T = N . L / v``) overall and by population category, with
    independent household-bootstrap CIs; a degenerate group (no days or
    zero totals on either side) yields ``result=None``."""
    rows = []
    categories = [None, *daily_energy.POPULATION_CATEGORIES]
    for category in categories:
        if category is None:
            mask_a = np.ones(len(frames_a.days["pond_jour"]), dtype=bool)
            mask_b = np.ones(len(frames_b.days["pond_jour"]), dtype=bool)
            label = "overall"
        else:
            mask_a = frames_a.days["population_category"] == category
            mask_b = frames_b.days["population_category"] == category
            label = category
        result = None
        if mask_a.any() and mask_b.any():
            try:
                result = variation.bootstrap_decompose(
                    person_days_from_frames(frames_a, mask_a),
                    person_days_from_frames(frames_b, mask_b),
                    n_reps=n_reps,
                    seed=seed,
                )
            except ValueError:
                result = None
        rows.append(
            B2Row(
                group=label,
                n_a=int(mask_a.sum()),
                n_b=int(mask_b.sum()),
                result=result,
            )
        )
    return rows


def _ci_cell(value: float, ci: tuple[float, float], decimals: int = 1) -> str:
    return f"{_num(value, decimals)} [{_num(ci[0], decimals)}, {_num(ci[1], decimals)}]"


def _format_b2(rows: list[B2Row], label_a: str, label_b: str) -> list[str]:
    lines = [
        f"## B2. Trips x distance x speed, {label_a} -> {label_b}",
        "",
        "T = N . L / v (trips per day, km per trip, km per minute), "
        "ratios of weighted totals; Δln T = Δln N + Δln L - Δln v, each "
        "term expressed in minutes as ΔT x (term / Δln T). Distances are "
        "step 11's corrected distances. Household-bootstrap 95% CIs, "
        "surveys resampled independently.",
        "",
        f"| Group | n {label_a} | n {label_b} | T {label_a} | T {label_b} "
        "| Δ (min) [CI] | trips (min) [CI] | km/trip (min) [CI] | "
        "speed (min) [CI] |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        if row.result is None or min(row.n_a, row.n_b) < MIN_CELL_N:
            lines.append(
                f"| {row.group} | {row.n_a} | {row.n_b} | - | - | - | - | - | - |"
            )
            continue
        point = row.result.point
        lines.append(
            f"| {row.group} | {row.n_a} | {row.n_b} | "
            f"{_num(point.time_a_min)} | {_num(point.time_b_min)} | "
            f"{_ci_cell(point.delta_min, row.result.delta_ci)} | "
            f"{_ci_cell(point.trips_min, row.result.trips_ci)} | "
            f"{_ci_cell(point.distance_min, row.result.distance_ci)} | "
            f"{_ci_cell(point.speed_min, row.result.speed_ci)} |"
        )
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
        "interaction (min) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                f"| {group} | {n_a} | {n_b} | - | - | - | - | - | - | - | - | - |"
            )
            continue
        lines.append(
            f"| {group} | {n_a} | {n_b} | {_pct(term.share_a)} | "
            f"{_pct(term.share_b)} | {_num(term.minutes_per_trip_a)} | "
            f"{_num(term.minutes_per_trip_b)} | {_num(term.mix_min, 2)} | "
            f"{_num(term.within_min, 2)} | {_num(term.within_km_min, 2)} | "
            f"{_num(term.within_speed_min, 2)} | {_num(term.interaction_min, 2)} |"
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
#: bands. 'residence' is home_density x Île-de-France (the caller picks
#: proxy- or grid-density frames); 'cars' is the household 0/1/2+ band.
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
    bootstrap 95% CIs."""

    variant: str
    point: variation.Composition
    composition_ci: tuple[float, float]
    behaviour_ci: tuple[float, float]
    note: str = ""


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
    seed_a, seed_b = np.random.SeedSequence(seed).spawn(2)
    rng_a, rng_b = np.random.default_rng(seed_a), np.random.default_rng(seed_b)
    reps = np.full((len(range(n_reps)), 2), np.nan)
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
            note="density proxy x Île-de-France",
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
    results["b2_rows"] = b2_decompositions(
        frames_2008, frames_2019, n_reps=n_reps, seed=seed
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
    motive_order = tuple([*MOTIVE_GROUP_LABELS.values(), "unknown"])
    results["extra_sections"] += [
        _format_b1(results["b1_rows"], "2008", "2019"),
        _format_b2(results["b2_rows"], "2008", "2019"),
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
            within_label="within bands (a speed effect)",
            intro=(
                "Same shift-share by trip distance band (A3's bands). "
                "Within a distance band, km per trip is nearly fixed, so "
                "the within-band term is a speed effect. "
                "Household-bootstrap 95% CIs."
            ),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Step-12 travel-time variation report (Parts A and B)."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--emp2019-data-path", type=Path, default=None)
    parser.add_argument("--entd2008-data-path", type=Path, default=None)
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
        sample_pct=args.sample_households,
    )
    md_path = args.out.with_suffix(".md")
    write_markdown(md_path, args.out, results)
    print(f"Wrote {md_path} and {len(results['figures'])} figures to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
