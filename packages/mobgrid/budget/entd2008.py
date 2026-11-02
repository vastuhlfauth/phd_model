"""ENTD 2008 trip-leg reconstruction for section 9.9's 2008-2019
comparison (step 11).

Builds ``trips_norm`` -- the same normalised trip view as EMP 2019,
``docs/data/entd2008.md``'s "Columns of the normalised trip view, by
survey" -- from ENTD 2008's four public tables, converting its own mode
and purpose codes to EMP 2019's; the shared, survey-agnostic energy
computation (``mobgrid.budget.trip_legs``) takes it from there
unchanged, so the two surveys' re-estimations differ only in behaviour,
not in the model (section 9.9, "Change between 2008 and 2019").

Full variable and code mapping: ``docs/data/entd2008.md``. Do not read
the raw CSVs or the archive's own PDFs for variables or codes beyond
that page -- it is the complete, authoritative source for this module.
"""

from __future__ import annotations

import re
from pathlib import Path

import duckdb

from mobgrid.budget import trip_legs

#: Repository root, three levels above this file (packages/mobgrid/budget).
ROOT = Path(__file__).resolve().parents[3]

#: Survey identity, used by `emp.py`'s CLI dispatch and report text.
SURVEY_NAME = "ENTD 2008"

#: ENTD 2008 has no density grid (section 9.9, "Quirks": "There is no
#: density grid in ENTD 2008"): the urban-unit-status x residence-size
#: proxy is the only option.
DEFAULT_DENSITY_SOURCE = "proxy"

#: Location of the four public ENTD 2008 CSVs (`docs/data/entd2008.md`).
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "entd2008"

#: Generic alias used by `emp.py`'s survey-agnostic ``run()`` (EMP 2019's
#: equivalent is a zip archive; both survey modules expose this same name).
DEFAULT_DATA_PATH = DEFAULT_RAW_DIR

#: Raw file name -> DuckDB view name.
RAW_FILES = {
    "k_deploc.csv": "k_deploc",
    "k_individu.csv": "k_individu",
    "q_tcm_individu.csv": "q_tcm_individu",
    "q_tcm_menage.csv": "q_tcm_menage",
}

#: Code columns read as VARCHAR, by raw file (`docs/data/entd2008.md`'s
#: "Format": two-decimal codes such as `5.50` must not be read as
#: numbers, and `1.1` (going home) must stay distinct from `1.11`
#: (studying)).
_CODE_COLUMN_TYPES = {
    "k_deploc.csv": {
        "IDENT_DEP": "VARCHAR",
        "IDENT_IND": "VARCHAR",
        "IDENT_MEN": "VARCHAR",
        "IDENT_JOUR": "VARCHAR",
        "V2_MTP": "VARCHAR",
        "V2_MMOTIFDES": "VARCHAR",
        "V2_MMOTIFORI": "VARCHAR",
        "V2_TYPJOUR": "VARCHAR",
        "V2_MORIDOM": "VARCHAR",
        "v2_moricom_UU2010": "VARCHAR",
        "v2_mdescom_UU2010": "VARCHAR",
    },
    "k_individu.csv": {
        "IDENT_IND": "VARCHAR",
        "IDENT_MEN": "VARCHAR",
    },
    "q_tcm_individu.csv": {
        "IDENT_IND": "VARCHAR",
        "SITUA": "VARCHAR",
        "AGE6": "VARCHAR",
    },
    "q_tcm_menage.csv": {
        "IDENT_MEN": "VARCHAR",
        "TU99": "VARCHAR",
        "numcom_UUCat": "VARCHAR",
    },
}

#: `V2_MTP` (2008) -> EMP 2019's harmonised `mtp` code
#: (`docs/data/entd2008.md`'s "Modes" table). Any other/missing code
#: (e.g. the walk sub-codes beyond `1.13`, or the 9999 refusal) is left
#: unmapped (NULL), which `trip_legs.build_trip_legs` already treats as
#: `mode_group = 'other'`, matching EMP 2019's own missing/refused mtp
#: handling.
_MODE_CONVERSION = {
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

#: `V2_MMOTIFDES`/`V2_MMOTIFORI` (2008) -> EMP 2019's motive code
#: (`docs/data/entd2008.md`'s "Purposes" table). Any other/missing code
#: (e.g. the "return home"/residence codes 1.1-1.3, already identical
#: between the two surveys, or an unlisted sub-code) is passed through
#: unmapped (NULL for an unlisted code; 1.1/1.2/1.3 are both the input
#: and the output, so they are listed too, for clarity).
_PURPOSE_CONVERSION = {
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

#: `SITUA` (2008) -> section 6.1's five population categories (same
#: mapping as EMP 2019's `tcm_ind_kish.SITUA`, `emp2019.py`'s
#: `_POPULATION_CATEGORY_BY_SITUA`; code 8 is an EMP 2019-only addition,
#: `docs/data/entd2008.md`: "3, 6, 7 (2019 also 8) other inactive").
_POPULATION_CATEGORY_BY_SITUA = {
    "1": "employed",
    "2": "employed",
    "3": "other_inactive",
    "4": "unemployed",
    "5": "retired",
    "6": "other_inactive",
    "7": "other_inactive",
}

#: `q_tcm_menage.numcom_UUCat` (the residence commune's own urban-unit
#: category, "Zonage de 1999") -> the same 4-code status
#: `STATUTCOM_UU_ORI`/`_DES`/`_RES` use (27 October 2026 decision:
#: residence density, not a trip end's, for `home_density`). Verified
#: against the real file: exactly these 4 French labels, no stray codes.
_UU_STATUS_BY_UUCAT = {
    "ville centre": "C",
    "banlieue": "B",
    "ville isolée": "I",
    "commune rurale": "R",
}

#: Matches a run of digits, possibly with interior whitespace (regular
#: or non-breaking space, the thousands separator of `TrancheRevenuMensuel`'s
#: bracket labels, e.g. "1 200").
_BRACKET_NUMBER_RE = re.compile(r"\d[\d\s]*\d|\d")


def income_bracket_midpoint_eur(label: str | None) -> float | None:
    """`Q_TCM_MENAGE.TrancheRevenuMensuel`'s free-text bracket label
    (section 9.9's "Income variables") to its midpoint in euros: an
    interior bracket's midpoint is the average of its two bounds; the
    bottom open bracket ("Moins de ... €") is read at half its upper
    bound; the top open bracket ("... € ou plus") at 1.5 times its lower
    bound (spec 9.9). The franc-equivalent parenthetical is ignored (the
    bounds are read from the text before the first `(`). Returns
    ``None`` for a missing or unparsable label.
    """
    if not label:
        return None
    head = label.split("(")[0]
    numbers = [
        int(re.sub(r"\s", "", token)) for token in _BRACKET_NUMBER_RE.findall(head)
    ]
    if not numbers:
        return None
    if "plus" in head:
        return 1.5 * numbers[0]
    if len(numbers) == 1:
        return numbers[0] / 2.0
    return sum(numbers[:2]) / 2.0


def build_respondent_income(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``respondent_income`` table (``ident_ind`` ->
    ``income_quintile``): household income per consumption unit, from
    `TrancheRevenuMensuel`'s bracket midpoint (``income_bracket_midpoint_eur``,
    registered here as a DuckDB scalar function) divided by `NBUC` (the
    household's own modified-OECD consumption-unit count, already
    matching this project's formula exactly, `docs/data/entd2008.md`'s
    "Income variables"), re-cut into quintiles by
    ``trip_legs.build_income_quintile_table`` (28 October 2026 decision:
    equal-sized quintiles). The universe is every ``K_INDIVIDU``
    respondent with ``PONDKI`` (the "persons actually analysed", 18,632
    rows in the real release -- not a trip-day-filtered subset).
    """
    _register_income_bracket_udf(con)
    base_sql = """
        SELECT i.IDENT_IND AS ident_ind,
            income_bracket_midpoint_eur(m.TrancheRevenuMensuel)
                / nullif(m.NBUC, 0) AS income_value,
            i.PONDKI AS weight
        FROM k_individu i
        LEFT JOIN q_tcm_menage m ON m.IDENT_MEN = i.idENT_MEN
    """
    trip_legs.build_income_quintile_table(con, base_sql)


def _register_income_bracket_udf(con: duckdb.DuckDBPyConnection) -> None:
    """Register ``income_bracket_midpoint_eur`` as a DuckDB scalar
    function, idempotently: DuckDB has no "CREATE OR REPLACE FUNCTION",
    so a second registration on the same connection (`build_trip_legs`/
    `build_respondent_income`/`missing_income_breakdown` can each be
    called more than once per connection, e.g. the F8 robustness sweep)
    is a harmless no-op here, not an error."""
    try:
        con.create_function(
            "income_bracket_midpoint_eur",
            income_bracket_midpoint_eur,
            [str],
            float,
            null_handling="special",
        )
    except duckdb.NotImplementedException:
        pass


def missing_income_breakdown(con: duckdb.DuckDBPyConnection) -> dict:
    """28 October 2026's missing-income audit (section 9.9's income
    update, point 2: "check whether income is truly never missing, was
    imputed by the producer, or is being dropped by our code"): counts
    *why* a respondent's ``income_value`` is ``NULL`` (if any are), each
    a separate failure mode along `build_respondent_income`'s own join/
    parse/divide chain -- a producer-side gap (no `Q_TCM_MENAGE` row, or
    a blank bracket) is not the same thing as this project's own
    `income_bracket_midpoint_eur` failing to parse a non-blank label, or
    a zero/missing `NBUC` making the division ``NULL``."""
    _register_income_bracket_udf(con)
    row = con.sql("""
        SELECT count(*) AS n_total,
            count(*) FILTER (WHERE m.IDENT_MEN IS NULL) AS n_no_household_match,
            count(*) FILTER (
                WHERE m.IDENT_MEN IS NOT NULL
                    AND (m.TrancheRevenuMensuel IS NULL OR m.TrancheRevenuMensuel = '')
            ) AS n_null_bracket,
            count(*) FILTER (
                WHERE m.TrancheRevenuMensuel IS NOT NULL
                    AND m.TrancheRevenuMensuel != ''
                    AND income_bracket_midpoint_eur(m.TrancheRevenuMensuel) IS NULL
            ) AS n_unparseable_bracket,
            count(*) FILTER (
                WHERE income_bracket_midpoint_eur(m.TrancheRevenuMensuel) IS NOT NULL
                    AND (m.NBUC IS NULL OR m.NBUC = 0)
            ) AS n_null_nbuc
        FROM k_individu i
        LEFT JOIN q_tcm_menage m ON m.IDENT_MEN = i.idENT_MEN
    """).fetchone()
    return {
        "n_total": row[0],
        "n_no_household_match": row[1],
        "n_null_bracket": row[2],
        "n_unparseable_bracket": row[3],
        "n_null_nbuc": row[4],
    }


def extract_tables(
    raw_dir: Path = DEFAULT_RAW_DIR, out_dir: Path | None = None
) -> dict[str, Path]:
    """Re-encode the four public tables from Windows-1252 to UTF-8,
    resumable (`docs/data/entd2008.md`'s "Format": "re-encoded once to
    UTF-8 under data/interim/entd2008/csv, as for EMP 2019")."""
    if out_dir is None:
        out_dir = ROOT / "data" / "interim" / "entd2008" / "csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name in RAW_FILES:
        dest_path = out_dir / name
        if not dest_path.exists():
            text = (raw_dir / name).read_text(encoding="cp1252")
            dest_path.write_text(text, encoding="utf-8")
        paths[name] = dest_path
    return paths


def register_views(con: duckdb.DuckDBPyConnection, csv_paths: dict[str, Path]) -> None:
    """Register the four extracted CSVs as DuckDB views, `;`-delimited,
    with every code column forced to VARCHAR (`docs/data/entd2008.md`'s
    "Format")."""
    for name, path in csv_paths.items():
        view_name = RAW_FILES[name]
        posix_path = path.as_posix()
        types = _CODE_COLUMN_TYPES.get(name, {})
        types_sql = ", ".join(f"'{col}': '{t}'" for col, t in types.items())
        con.sql(
            f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv("
            f"'{posix_path}', delim=';', nullstr='', strict_mode=false, "
            f"types={{{types_sql}}})"
        )


def build_trips_norm(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``trips_norm`` view from ENTD 2008's raw tables: the
    survey-specific half of the trip-leg reconstruction, converting mode
    and purpose codes to EMP 2019's (``docs/data/entd2008.md``'s
    "Columns of the normalised trip view, by survey").
    ``mobgrid.budget.trip_legs.build_trip_legs`` reads this view onward,
    shared with EMP 2019.

    Keeps only rows with ``POIDS_JOUR > 0`` (the day weight; weekday
    trips outside the reference day are weighted 0 and dropped,
    `docs/data/entd2008.md`'s "Keys, days and weights").
    """
    mtp_sql = trip_legs._case_sql("d.V2_MTP", _MODE_CONVERSION)
    motifdes_sql = trip_legs._case_sql("d.V2_MMOTIFDES", _PURPOSE_CONVERSION)
    motifori_sql = trip_legs._case_sql("d.V2_MMOTIFORI", _PURPOSE_CONVERSION)
    population_category_sql = trip_legs._case_sql(
        "q.SITUA",
        _POPULATION_CATEGORY_BY_SITUA,
        default="'unknown'",
        quote_values=True,
    )
    uu_status_res_sql = trip_legs._case_sql(
        "m.numcom_UUCat",
        _UU_STATUS_BY_UUCAT,
        quote_values=True,
    )
    build_respondent_income(con)

    con.sql(f"""
        CREATE OR REPLACE VIEW trips_norm AS
        WITH motives AS (
            SELECT
                d.*,
                ({motifdes_sql}) AS motifdes_converted,
                ({motifori_sql}) AS motifori_converted
            FROM k_deploc d
        )
        SELECT
            d.IDENT_DEP AS ident_dep,
            d.IDENT_IND AS ident_ind,
            d.IDENT_MEN AS ident_men,
            -- Each respondent describes up to three days (reference
            -- weekday, Saturday, Sunday): the day grouping key is the
            -- described day, not the person (`docs/data/entd2008.md`'s
            -- "Keys, days and weights").
            d.IDENT_JOUR AS day_id,
            d.POIDS_JOUR AS pond_jour,
            CAST(d.V2_TYPJOUR AS DOUBLE) AS typejour,
            (CAST(d.V2_DLOCAL AS DOUBLE) <> 0)::INT AS mobloc,
            d.NODEP AS num_dep,
            CAST(d.V2_MORIDOM AS DOUBLE) AS moridom,
            coalesce(try_cast(d.v2_mduree AS DOUBLE), d.V2_DUREE) AS duration_min,
            coalesce(try_cast(d.distcor AS DOUBLE), d.V2_MDISTTOT)
                AS distance_km_declared,
            d.V2_MACCOMPM AS maccompm,
            d.V2_MACCOMPHM AS maccomphm,
            ({mtp_sql}) AS mtp,
            d.motifdes_converted = {trip_legs._dbl(7.7)} AS is_loop_trip,
            -- Return trips take the purpose of the outward trip they
            -- close (`docs/data/entd2008.md`'s `motive` row).
            CASE WHEN d.motifdes_converted IN (1.1, 1.2, 1.3)
                THEN d.motifori_converted
                ELSE d.motifdes_converted
            END AS motive,
            nullif(d.v2_moricom_UU2010, '') AS uu_status_ori,
            nullif(d.v2_mdescom_UU2010, '') AS uu_status_des,
            ({uu_status_res_sql}) AS uu_status_res,
            m.TU99 AS tuu_res,
            CAST(NULL AS VARCHAR) AS density_ori_grid,
            CAST(NULL AS VARCHAR) AS density_des_grid,
            CAST(NULL AS VARCHAR) AS density_res_grid,
            q.AGE AS age,
            q.AGE6 AS age_band,
            CASE
                WHEN q.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                ELSE {population_category_sql}
            END AS population_category,
            d.V2_MTEMPSMAP AS declared_walk_min,
            d.V2_MTPSATTENT AS declared_wait_min,
            i.PONDKI AS pond_ind,
            coalesce(ri.income_quintile, 'unknown') AS income_quintile
        FROM motives d
        JOIN q_tcm_individu q ON q.IDENT_IND = d.IDENT_IND
        JOIN k_individu i ON i.IDENT_IND = d.IDENT_IND
        LEFT JOIN q_tcm_menage m ON m.IDENT_MEN = d.IDENT_MEN
        LEFT JOIN respondent_income ri ON ri.ident_ind = d.IDENT_IND
        WHERE d.POIDS_JOUR > 0
    """)


def build_trip_legs(
    con: duckdb.DuckDBPyConnection,
    config,
    *,
    terminal_scale: float = 1.0,
    bike_p0_override_w: float | None = None,
    density_source: str | None = None,
    terminal_legs: str = "declared",
) -> None:
    """Build ``trips_norm`` from ENTD 2008's raw tables, then
    ``trip_legs`` from it (``trip_legs.build_trip_legs``, shared with
    EMP 2019). ``density_source`` defaults to ``DEFAULT_DENSITY_SOURCE``
    ('proxy'): ENTD 2008 has no density grid, so 'grid' always raises.
    ``terminal_legs`` is ``trip_legs.build_trip_legs``'s own parameter
    (section 9.9's 27 October 2026 decision; see
    ``trip_legs.TERMINAL_LEGS_VARIANTS``), passed straight through.
    """
    build_trips_norm(con)
    trip_legs.build_trip_legs(
        con,
        config,
        terminal_scale=terminal_scale,
        bike_p0_override_w=bike_p0_override_w,
        density_source=density_source or DEFAULT_DENSITY_SOURCE,
        terminal_legs=terminal_legs,
    )


def quirk_fill_rates(con: duckdb.DuckDBPyConnection) -> dict:
    """Section 9.9's "Quirks": fill rate and mean change of `k_deploc`'s
    seven undocumented correction columns' two used by `trips_norm`
    (`distcor`, `v2_mduree`), on rows with ``POIDS_JOUR > 0`` (the
    ``trips_norm`` scope). `try_cast` (not `CAST`): a column that is
    empty for every row of a release (seen for `v2_mduree`) is read back
    by DuckDB as VARCHAR, not DOUBLE, since there are no numeric
    samples to infer a type from.
    """
    row = con.sql("""
        SELECT
            count(try_cast(distcor AS DOUBLE)) * 1.0 / count(*)
                AS distcor_fill_rate,
            avg(try_cast(distcor AS DOUBLE) - V2_MDISTTOT)
                FILTER (WHERE try_cast(distcor AS DOUBLE) IS NOT NULL)
                AS distcor_mean_change_km,
            count(try_cast(v2_mduree AS DOUBLE)) * 1.0 / count(*)
                AS v2_mduree_fill_rate,
            avg(try_cast(v2_mduree AS DOUBLE) - V2_DUREE)
                FILTER (WHERE try_cast(v2_mduree AS DOUBLE) IS NOT NULL)
                AS v2_mduree_mean_change_min
        FROM k_deploc WHERE POIDS_JOUR > 0
    """).fetchone()
    return {
        "distcor_fill_rate": row[0],
        "distcor_mean_change_km": row[1],
        "v2_mduree_fill_rate": row[2],
        "v2_mduree_mean_change_min": row[3],
    }


def respondent_n(con: duckdb.DuckDBPyConnection) -> int:
    """The selected-respondent roster size (section 9.9, "Change between
    2008 and 2019": persons and days kept apart). One row per selected
    (Kish) respondent, up to three described days each (`k_individu`,
    "Donnees mobilite quotidienne, mobilite du Kish" -- not
    `q_tcm_individu`'s 49,283 rows, which cover every household member,
    selected or not, and are used only for ages/occupations)."""
    return con.sql("SELECT count(*) FROM k_individu").fetchone()[0]


def non_traveler_summary(con: duckdb.DuckDBPyConnection) -> dict:
    """Section 9.9's "Persons without trips", 2008: `k_individu`'s
    `V2_MOBILREF = 0` (not mobile) on the reference weekday, weighted by
    `PONDKI` (the person weight); weighted and unweighted shares are
    both over the full respondent roster (``respondent_n``), not the
    narrower within-scope-with-energy traveller count the share used to
    be computed against. Weekend immobility (`V2_MIMMOSAM`, `V2_MIMMODIM`)
    is not needed for the comparison, since EMP 2019 identifies weekday
    non-travellers only.
    """
    n_respondents = respondent_n(con)
    total_weight = con.sql("SELECT sum(PONDKI) FROM k_individu").fetchone()[0]
    non_traveler_weight = (
        con.sql("SELECT sum(PONDKI) FROM k_individu WHERE V2_MOBILREF = 0").fetchone()[
            0
        ]
        or 0.0
    )
    non_traveler_n = con.sql(
        "SELECT count(*) FROM k_individu WHERE V2_MOBILREF = 0"
    ).fetchone()[0]
    return {
        "n": int(non_traveler_n),
        "n_respondents": n_respondents,
        "share_weighted": float(non_traveler_weight) / float(total_weight),
        "share_unweighted": non_traveler_n / n_respondents,
        "mimmosem_match": None,
    }


def population_category_by_ident(con: duckdb.DuckDBPyConnection) -> dict:
    """``population_category`` for every ENTD 2008 respondent
    (`k_individu` joined to `q_tcm_individu` for age/situation), the same
    section 6.1 mapping ``build_trips_norm`` uses -- needed for the
    per-person budget (section 9.9 point 2), which groups non-travellers
    (`V2_MOBILREF = 0`) too."""
    case_sql = trip_legs._case_sql(
        "q.SITUA",
        _POPULATION_CATEGORY_BY_SITUA,
        default="'unknown'",
        quote_values=True,
    )
    rows = con.sql(f"""
        SELECT i.IDENT_IND,
            CASE WHEN q.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                 ELSE {case_sql} END
        FROM k_individu i JOIN q_tcm_individu q ON q.IDENT_IND = i.IDENT_IND
    """).fetchall()
    return dict(rows)


def residence_density_by_ident(
    con: duckdb.DuckDBPyConnection, density_source: str
) -> dict:
    """Residence density for every ENTD 2008 respondent (`k_individu`
    joined to `q_tcm_menage` through `IDENT_MEN`), proxy only (no density
    grid in ENTD 2008, so ``density_source='grid'`` is not offered;
    section 9.9 point 2's per-person budget)."""
    if density_source != "proxy":
        raise ValueError("ENTD 2008 has no density grid: use density_source='proxy'")
    uu_status_res_sql = trip_legs._case_sql(
        "m.numcom_UUCat", _UU_STATUS_BY_UUCAT, quote_values=True
    )
    rows = con.sql(f"""
        WITH base AS (
            SELECT i.IDENT_IND AS ident_ind,
                ({uu_status_res_sql}) AS uu_status_res,
                m.TU99 AS tuu_res
            FROM k_individu i
            JOIN q_tcm_menage m ON m.IDENT_MEN = i.idENT_MEN
        )
        SELECT ident_ind,
            ({trip_legs.density_proxy_case_sql("uu_status_res", "tuu_res")})
        FROM base
    """).fetchall()
    return dict(rows)


def income_quintile_by_ident(con: duckdb.DuckDBPyConnection) -> dict:
    """``income_quintile`` for every ENTD 2008 respondent, from
    ``respondent_income`` (built by ``build_respondent_income``, already
    covering the full `k_individu` roster): section 9.9 point 2's
    per-person budget needs the income quintile of non-travellers too."""
    return dict(
        con.sql("SELECT ident_ind, income_quintile FROM respondent_income").fetchall()
    )


def person_weekday_rows(con: duckdb.DuckDBPyConnection) -> list[tuple]:
    """One row per respondent, the reference weekday only (ENTD 2008's
    weekend eligibility is unverified, section 9.9 point 2): ``(ident_ind,
    ident_men, pond_ind, day_type, immobile)``, ``day_type`` always
    `'weekday'`, ``immobile`` from `V2_MOBILREF = 0` (`k_individu`,
    weighted by `PONDKI`, as ``non_traveler_summary``)."""
    rows = con.sql("""
        SELECT IDENT_IND, idENT_MEN, PONDKI, V2_MOBILREF FROM k_individu
    """).fetchall()
    return [
        (ident_ind, ident_men, float(pondki), "weekday", float(mobilref == 0))
        for ident_ind, ident_men, pondki, mobilref in rows
    ]
