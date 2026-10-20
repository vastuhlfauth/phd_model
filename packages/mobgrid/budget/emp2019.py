"""EMP 2019 trip-leg reconstruction for section 9.9 (step 11).

Builds ``trips_norm`` -- one row per EMP 2019 trip, with the columns of
``docs/data/entd2008.md``'s "Columns of the normalised trip view, by
survey" table -- from the public EMP 2019 tables; the shared, survey-
agnostic energy computation (``mobgrid.budget.trip_legs``) takes it from
there. Section 9.9's re-estimation step 1: "the main mode, the declared
duration (DUREE), the distance (MDISTTOT_fin), the purpose and the
companions, with the weight POND_JOUR"; terminal legs take the defaults
of sections 9.4 to 9.7 by density class of the trip ends, and the
vehicle leg takes the rest of the declared duration.

EMP 2019 gives no headway, station-depth or PT access-distance data, so
these (``config.pt_ride.headway_min_am_peak``/``station_height_m``/
``access_walk_m_by_density``) are new, provisional, TODO(confirm) values
in ``config/energy.yaml``, in the spirit of section 9.3's own station
table; everything else (car terminal legs, activity rates, PT ride
crowding) reuses the values already calibrated for step 7.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import duckdb
import numpy as np

from mobgrid.budget import trip_legs
from mobgrid.budget.trip_legs import (  # noqa: F401 -- re-exported, shared constants
    CAR_SPEED_UPPER_KMH,
    CYCLE_SPEED_UPPER_KMH,
    MOTIVE_LABEL_BY_CODE,
    NEEDS_EXCLUDED_MOTIVE_CODES,
    NEEDS_ONLY_WHERE_SQL,
    OTHER_MODE_DESCRIPTION,
    TOP_LEVEL_MOTIVE_LABEL_BY_CODE,
    WALK_SPEED_UPPER_KMH,
)
from mobgrid.budget.trip_legs import (
    build_trip_legs as _shared_build_trip_legs,
)
from mobgrid.energy.rates import EnergyConfig

#: Repository root, three levels above this file (packages/mobgrid/budget).
ROOT = Path(__file__).resolve().parents[3]

#: Survey identity, used by `emp.py`'s CLI dispatch and report text.
SURVEY_NAME = "EMP 2019"

#: No density grid work is needed for EMP 2019 by default: it is the one
#: survey with a real INSEE density grid (`DENSITECOM_ORI`/`_DES`).
DEFAULT_DENSITY_SOURCE = "grid"

#: Default location of the EMP 2019 public data archive (`config/sources.yaml`
#: source id `emp2019-data`).
DEFAULT_ZIP_PATH = ROOT / "data" / "raw" / "emp2019" / "emp2019-data.zip"

#: Generic alias used by `emp.py`'s survey-agnostic ``run()`` (ENTD 2008's
#: equivalent is a raw directory, not an archive; both survey modules
#: expose this same name).
DEFAULT_DATA_PATH = DEFAULT_ZIP_PATH

#: Zip member name -> extracted CSV file name, for the six public tables
#: section 9.9 names (K_DEPLOC, TCM_IND, TCM_IND_KISH, K_INDIVIDU, Q_MENAGE,
#: TCM_MEN -- added for `TUU2017_RES`, section 9.9's density proxy).
ZIP_MEMBERS = {
    "5. k_deploc_public_V4.csv": "k_deploc.csv",
    "k_individu_public_V3.csv": "k_individu.csv",
    "tcm_ind_public_V3.csv": "tcm_ind.csv",
    "tcm_ind_kish_public_V3.csv": "tcm_ind_kish.csv",
    "q_menage_public_V3.csv": "q_menage.csv",
    "tcm_men_public_V3.csv": "tcm_men.csv",
}

#: k_deploc and tcm_men use a comma-quoted dialect; the other tables are
#: semicolon-separated, unquoted.
_COMMA_QUOTED_NAMES = ("k_deploc.csv", "tcm_men.csv")

#: `mode_group = 'other'` day-mode-group contents and the shared motive
#: constants are now defined once in `trip_legs` (re-exported above, for
#: `emp.py`'s existing `emp2019.X` references).

#: `tcm_ind_kish_public`'s `SITUA` ("Situation principale vis-a-vis du
#: travail") codes, mapped to section 6.1's five population categories
#: (children 6-17, employed, unemployed, retired, other inactive).
#: Codes 1/2 = employed or paid trainee; 4 = unemployed; 5 = retired;
#: 3/6/7/8 = student/homemaker/other/unspecified inactive, all folded
#: into "other_inactive" (section 6.1: "students aged 18 or more,
#: homemakers, others").
_POPULATION_CATEGORY_BY_SITUA = {
    "1": "employed",
    "2": "employed",
    "3": "other_inactive",
    "4": "unemployed",
    "5": "retired",
    "6": "other_inactive",
    "7": "other_inactive",
    "8": "other_inactive",
}

#: EMP's 4-level `DENSITECOM_ORI`/`DENSITECOM_DES` codes (section 9.9
#: point 3: "the four levels of the INSEE density grid"), in the INSEE
#: grid's own order and names (`emp2019-categories.pdf`, "Degre de
#: densite"): 1 = densely populated, 2 = intermediate density, 3 =
#: sparsely populated ("peu denses"), 4 = very sparsely populated
#: ("tres peu denses").
_DENSITY_LABEL_BY_CODE = {
    1: "dense",
    2: "intermediate",
    3: "sparse",
    4: "very_sparse",
}

#: `STATUTCOM_UU_ORI`/`_DES` codes (section 9.9's density proxy): city
#: centre, suburb (banlieue), isolated town; `H` ("hors unite urbaine")
#: is read as `R` (rural, `docs/data/entd2008.md`'s trips_norm mapping),
#: matching ENTD 2008's own 'R' code. TODO(confirm): the disclosure-
#: masked '8'/'9' stray codes seen in the public release, and a blank
#: status, are left NULL (not mapped to any of the four): no documented
#: meaning is given for them, and `trip_legs.density_proxy_case_sql`
#: already falls back to 'intermediate' for an unmapped status, the
#: same default the grid itself uses for a stray code.
_UU_STATUS_BY_CODE = {
    "C": "C",
    "B": "B",
    "I": "I",
    "H": "R",
}


def extract_tables(
    zip_path: Path = DEFAULT_ZIP_PATH, out_dir: Path | None = None
) -> dict[str, Path]:
    """Extract the six public tables to UTF-8 CSVs, resumable.

    The archive's CSVs are Windows-1252 encoded (French accents), which
    DuckDB's CSV reader does not accept; each file is decoded once and
    re-written as UTF-8 under ``out_dir`` (default
    ``data/interim/emp2019/csv``). Already-extracted files are kept.
    """
    if out_dir is None:
        out_dir = ROOT / "data" / "interim" / "emp2019" / "csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member, dest_name in ZIP_MEMBERS.items():
            dest_path = out_dir / dest_name
            if not dest_path.exists():
                text = archive.read(member).decode("cp1252")
                dest_path.write_text(text, encoding="utf-8")
            paths[dest_name] = dest_path
    return paths


def register_views(con: duckdb.DuckDBPyConnection, csv_paths: dict[str, Path]) -> None:
    """Register the extracted CSVs as DuckDB views."""
    for name, path in csv_paths.items():
        view_name = name.removesuffix(".csv")
        posix_path = path.as_posix()
        if name in _COMMA_QUOTED_NAMES:
            con.sql(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv("
                f"'{posix_path}', delim=',', quote='\"', escape='\"', "
                "nullstr='NA', strict_mode=false)"
            )
        else:
            con.sql(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv("
                f"'{posix_path}', delim=';', nullstr='NA', strict_mode=false)"
            )


def build_trips_norm(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``trips_norm`` view from EMP 2019's raw tables: the
    survey-specific half of the trip-leg reconstruction
    (``docs/data/entd2008.md``'s "Columns of the normalised trip view,
    by survey"). ``mobgrid.budget.trip_legs.build_trip_legs`` reads this
    view onward, shared with ENTD 2008.
    """
    population_category_sql = trip_legs._case_sql(
        "k.SITUA",
        _POPULATION_CATEGORY_BY_SITUA,
        default="'unknown'",
        quote_values=True,
    )
    density_ori_sql = (
        "CASE d.DENSITECOM_ORI\n    "
        + "\n    ".join(
            f"WHEN {code} THEN '{label}'"
            for code, label in _DENSITY_LABEL_BY_CODE.items()
        )
        + "\n    ELSE 'intermediate'\nEND"
    )
    density_des_sql = (
        "CASE d.DENSITECOM_DES\n    "
        + "\n    ".join(
            f"WHEN {code} THEN '{label}'"
            for code, label in _DENSITY_LABEL_BY_CODE.items()
        )
        + "\n    ELSE 'intermediate'\nEND"
    )
    uu_status_ori_sql = trip_legs._case_sql(
        "d.STATUTCOM_UU_ORI",
        _UU_STATUS_BY_CODE,
        quote_values=True,
    )
    uu_status_des_sql = trip_legs._case_sql(
        "d.STATUTCOM_UU_DES",
        _UU_STATUS_BY_CODE,
        quote_values=True,
    )

    con.sql(f"""
        CREATE OR REPLACE VIEW trips_norm AS
        SELECT
            d.IDENT_DEP AS ident_dep,
            d.IDENT_IND AS ident_ind,
            d.IDENT_MEN AS ident_men,
            -- EMP 2019 describes one surveyed day per respondent: the
            -- day grouping key is the person id itself.
            d.IDENT_IND AS day_id,
            d.POND_JOUR AS pond_jour,
            d.TYPEJOUR AS typejour,
            d.mobloc AS mobloc,
            d.num_dep AS num_dep,
            d.MORIDOM AS moridom,
            d.DUREE AS duration_min,
            d.MDISTTOT_fin AS distance_km_declared,
            d.MACCOMPM AS maccompm,
            d.MACCOMPHM AS maccomphm,
            d.mtp AS mtp,
            -- Trips without a real destination (section 9.9's "leisure
            -- loops"): EMP's own purpose code 7.7 "se promener sans
            -- destination precise" (stroll, no specific destination);
            -- code 7.8 ("go to a place for walking") has a destination
            -- and does not count.
            d.MMOTIFDES = {trip_legs._dbl(7.7)} AS is_loop_trip,
            -- EMP's own "corrected, detailed motive of the sequence"
            -- (MOT_SEQ_COMPL): unlike the raw, trip-level MMOTIFDES
            -- used by `is_loop_trip` above, this is chain-level and
            -- excludes "return home"/"return to residence" codes
            -- (1.1-1.3).
            CASE WHEN d.MOT_SEQ_COMPL = {trip_legs._dbl(9999.0)} THEN NULL
                ELSE d.MOT_SEQ_COMPL
            END AS motive,
            ({uu_status_ori_sql}) AS uu_status_ori,
            ({uu_status_des_sql}) AS uu_status_des,
            CAST(m.TUU2017_RES AS VARCHAR) AS tuu_res,
            ({density_ori_sql}) AS density_ori_grid,
            ({density_des_sql}) AS density_des_grid,
            k.AGE AS age,
            k.AGE6 AS age_band,
            -- Section 6.1's five population categories: children under
            -- 18 (6-17 in this travel survey), employed, unemployed,
            -- retired, other inactive (students 18+, homemakers, others).
            CASE
                WHEN k.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                ELSE {population_category_sql}
            END AS population_category,
            d.MTEMPSMAP AS declared_walk_min,
            d.MTPSATTENT AS declared_wait_min,
            i.pond_indC AS pond_ind
        FROM k_deploc d
        JOIN tcm_ind_kish k ON k.IDENT_IND = d.IDENT_IND
        JOIN k_individu i ON i.IDENT_IND = d.IDENT_IND
        LEFT JOIN tcm_men m ON m.ident_men = d.IDENT_MEN
    """)


def build_trip_legs(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    *,
    terminal_scale: float = 1.0,
    bike_p0_override_w: float | None = None,
    density_source: str | None = None,
) -> None:
    """Build ``trips_norm`` from EMP 2019's raw tables, then ``trip_legs``
    from it (``trip_legs.build_trip_legs``, shared with ENTD 2008).
    ``density_source`` defaults to ``DEFAULT_DENSITY_SOURCE`` ('grid').
    """
    build_trips_norm(con)
    _shared_build_trip_legs(
        con,
        config,
        terminal_scale=terminal_scale,
        bike_p0_override_w=bike_p0_override_w,
        density_source=density_source or DEFAULT_DENSITY_SOURCE,
    )


def create_non_travelers(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``non_travelers`` view: Kish respondents with no trip
    recorded on their surveyed day (section 9.9 point 2, "persons without
    trips are reported apart")."""
    population_case = trip_legs._case_sql(
        "k.SITUA",
        _POPULATION_CATEGORY_BY_SITUA,
        default="'unknown'",
        quote_values=True,
    )
    con.sql(f"""
        CREATE OR REPLACE VIEW non_travelers AS
        SELECT
            k.IDENT_IND AS ident_ind,
            i.pond_indC AS pond_ind,
            k.AGE6 AS age_band,
            CASE WHEN k.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                 ELSE {population_case} END AS population_category,
            -- Immobility is "no trip on the described day"; `MIMMOSEM`
            -- (K_INDIVIDU) is an independent weekday-immobility flag that
            -- matches this exactly for every respondent in this release
            -- (see the step 11 report): EMP 2019's public tables record
            -- no day-of-week for a fully immobile respondent (`MDATE_jour`
            -- is blank), so a Saturday/Sunday non-traveller cannot be
            -- told apart from a weekday one here.
            i.MIMMOSEM AS mimmosem
        FROM tcm_ind_kish k
        JOIN k_individu i ON i.IDENT_IND = k.IDENT_IND
        WHERE NOT EXISTS (
            SELECT 1 FROM trip_legs t WHERE t.ident_ind = k.IDENT_IND
        )
    """)


def non_traveler_summary(con: duckdb.DuckDBPyConnection) -> dict:
    """Section 9.9 point 2's "persons without trips" summary: weighted
    non-traveller share plus the EMP-specific `MIMMOSEM` cross-check
    (``emp.py``'s "Non-traveller immobility" section)."""
    create_non_travelers(con)
    non_travelers = con.sql("SELECT pond_ind, mimmosem FROM non_travelers").fetchnumpy()
    travelers_pond_ind = con.sql(
        "SELECT pond_ind FROM day_summary WHERE total_energy_kh_kj IS NOT NULL"
    ).fetchnumpy()["pond_ind"]
    non_traveler_weight = float(non_travelers["pond_ind"].sum())
    non_traveler_share = non_traveler_weight / (
        non_traveler_weight + float(travelers_pond_ind.sum())
    )
    mimmosem_match = float(np.mean(non_travelers["mimmosem"] == 1))
    return {
        "n": int(len(non_travelers["pond_ind"])),
        "share": non_traveler_share,
        "mimmosem_match": mimmosem_match,
    }
