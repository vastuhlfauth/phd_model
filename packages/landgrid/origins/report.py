"""Aggregate-only census validation reports for section 6.5."""

from __future__ import annotations

import argparse
import json
import logging
import math
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pyarrow as pa
from common.duckdb_io import open_connection

from landgrid.origins.fichiers_fonciers import (
    CensusVintageConfig,
    OriginsConfig,
    _pilot_department,
    _quoted_identifier,
    load_origins_config,
)

LOGGER = logging.getLogger(__name__)

MEASURES = ("dwellings", "main_residences", "second_homes", "vacant")
SCENARIOS = ("configured", "exclude_recent", "split_recent")
SCENARIO_LABELS = {
    "configured": "Recent transfers counted as main residences",
    "exclude_recent": "Recent transfers excluded from both categories",
    "split_recent": "Recent transfers split by settled owner-occupied ratio",
}
MEASURE_LABELS = {
    "dwellings": "Dwellings",
    "main_residences": "Main residences",
    "second_homes": "Second homes",
    "vacant": "Vacant dwellings",
}


@dataclass(frozen=True)
class ReportSummary:
    matched_communes: int
    census_only_communes: int
    ff_only_communes: int
    totals: dict[str, tuple[float | None, float | None]]
    statistics: list[dict[str, Any]]
    scenario_nmae: dict[str, float | None]
    top_second_home_gaps: list[dict[str, Any]]


def _extract_zip_member(archive: Path, member: str, target: Path) -> None:
    """Stream one configured public CSV member into a temporary file."""
    with zipfile.ZipFile(archive) as zipped:
        if member not in zipped.namelist():
            raise FileNotFoundError(f"{member!r} is missing from {archive}")
        with zipped.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)


def _census_csv_table(
    connection: duckdb.DuckDBPyConnection,
    config: CensusVintageConfig,
    department: str,
) -> pa.Table:
    """Select section-6.5 census columns as dwelling counts."""
    if not config.member:
        raise ValueError("the 2021 census ZIP member is not configured")
    archive = Path(config.path)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with tempfile.TemporaryDirectory(prefix="census_2021_") as directory:
        csv_path = Path(directory) / "dossier_complet.csv"
        _extract_zip_member(archive, config.member, csv_path)
        geo = _quoted_identifier(config.geography_column)
        select_fields = [
            f"trim(CAST({geo} AS VARCHAR)) AS commune_code",
        ]
        for measure in MEASURES:
            column = _quoted_identifier(config.measures[measure])
            value = f"replace(trim(CAST({column} AS VARCHAR)), ',', '.')"
            select_fields.append(
                f"TRY_CAST(NULLIF({value}, '') AS DOUBLE) "
                f"AS {_quoted_identifier(measure)}"
            )
        delimiter = config.delimiter or ";"
        table = connection.execute(
            f"""
            SELECT {", ".join(select_fields)}
            FROM read_csv(?, delim={_sql_string(delimiter)},
                          header=true, all_varchar=true)
            WHERE left(trim(CAST({geo} AS VARCHAR)), length(?)) = ?
            ORDER BY commune_code
            """,
            [str(csv_path), department, department],
        ).to_arrow_table()
    return table


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _census_parquet_table(
    connection: duckdb.DuckDBPyConnection,
    config: CensusVintageConfig,
    department: str,
) -> pa.Table:
    """Select section-6.5 long-form observations as dwelling counts."""
    required = {
        "geography_type_column": config.geography_type_column,
        "time_period_column": config.time_period_column,
        "table_column": config.table_column,
        "dataset_column": config.dataset_column,
        "measure_column": config.measure_column,
        "geography_type": config.geography_type,
        "time_period": config.time_period,
        "table_id": config.table_id,
        "dataset_id": config.dataset_id,
    }
    missing = [key for key, value in required.items() if value is None]
    if missing:
        raise ValueError("incomplete long-form census selectors: " + ", ".join(missing))
    source = Path(config.path)
    if not source.is_file():
        raise FileNotFoundError(source)

    geo = _quoted_identifier(config.geography_column)
    geo_type = _quoted_identifier(config.geography_type_column or "")
    period = _quoted_identifier(config.time_period_column or "")
    table_id = _quoted_identifier(config.table_column or "")
    dataset = _quoted_identifier(config.dataset_column or "")
    measure = _quoted_identifier(config.measure_column or "")
    value_columns = [
        f"MAX(TRY_CAST(observation_value AS DOUBLE)) "
        f"FILTER (WHERE measure = ?) AS {_quoted_identifier(name)}"
        for name in MEASURES
    ]
    measure_placeholders = ", ".join("?" for _ in MEASURES)
    query = f"""
        WITH selected AS (
            SELECT
                regexp_extract(
                    CAST({geo} AS VARCHAR), '([0-9A-Z]{{5}})$', 1
                )
                    AS commune_code,
                CAST({measure} AS VARCHAR) AS measure,
                "OBS_VALUE" AS observation_value
            FROM read_parquet(?)
            WHERE {geo_type} = ?
                AND {period} = ?
                AND {table_id} = ?
                AND {dataset} = ?
                AND {measure} IN ({measure_placeholders})
                AND regexp_extract(
                    CAST({geo} AS VARCHAR), '([0-9A-Z]{{5}})$', 1
                ) LIKE ?
        )
        SELECT commune_code,
            count(*) AS selected_rows,
            count(DISTINCT measure) AS distinct_measures,
            {", ".join(value_columns)}
        FROM selected
        WHERE commune_code <> ''
        GROUP BY commune_code
        ORDER BY commune_code
    """
    parameters: list[object] = [
        str(source),
        config.geography_type,
        config.time_period,
        config.table_id,
        config.dataset_id,
        *[config.measures[name] for name in MEASURES],
        f"{department}%",
        *[config.measures[name] for name in MEASURES],
    ]
    table = connection.execute(query, parameters).to_arrow_table()
    if table.num_rows == 0:
        raise ValueError(
            f"no 2023 census housing observations found for department {department}"
        )
    if any(
        row["selected_rows"] != len(MEASURES)
        or row["distinct_measures"] != len(MEASURES)
        for row in table.select(["selected_rows", "distinct_measures"]).to_pylist()
    ):
        raise ValueError(
            "2023 census selectors must yield one row per commune and measure"
        )
    return table.drop(["selected_rows", "distinct_measures"])


def load_census_department(
    connection: duckdb.DuckDBPyConnection,
    census_vintage: int,
    department: str,
    config: OriginsConfig,
) -> pa.Table:
    """Load section-6.5 commune housing totals for one department."""
    try:
        census_config = config.census[census_vintage]
    except KeyError as error:
        raise ValueError(f"unsupported census vintage: {census_vintage}") from error
    if set(census_config.measures) != set(MEASURES):
        raise ValueError(f"census vintage {census_vintage} must configure {MEASURES}")
    if census_config.format == "zip_csv":
        table = _census_csv_table(connection, census_config, department)
    elif census_config.format == "parquet":
        table = _census_parquet_table(connection, census_config, department)
    else:
        raise ValueError(f"unsupported census format: {census_config.format}")
    if table.num_rows == 0:
        raise ValueError(f"no census commune rows found for department {department}")
    codes = table["commune_code"].to_pylist()
    if len(codes) != len(set(codes)):
        raise ValueError("census source contains duplicate commune codes")
    if any(table[name].null_count for name in MEASURES):
        raise ValueError("census housing measure is null for a selected commune")
    return table


def _ff_communes_table(
    connection: duckdb.DuckDBPyConnection,
    vintage: int,
    department: str,
    output_directory: Path,
    config: OriginsConfig,
) -> tuple[pa.Table, Path]:
    """Read the pre-aggregated FF dwelling counts for one department."""
    path = output_directory / config.report.ff_communes_pattern.format(vintage=vintage)
    if not path.is_file():
        raise FileNotFoundError(
            f"missing commune aggregation {path}; build this FF vintage first"
        )
    table = connection.execute(
        """
        SELECT * FROM read_parquet(?)
        WHERE left(commune_code, length(?)) = ?
        ORDER BY commune_code
        """,
        [str(path), department, department],
    ).to_arrow_table()
    if table.num_rows == 0:
        raise ValueError(
            f"no Fichiers fonciers commune rows found for department {department}"
        )
    return table, path


def calculate_report_summary(
    census: pa.Table,
    ff_communes: pa.Table,
    quantiles: tuple[float, ...],
    top_count: int,
) -> ReportSummary:
    """Compare section-6.5 dwelling counts without materializing row output."""
    if not quantiles or any(not 0 <= value <= 1 for value in quantiles):
        raise ValueError("report quantiles must be between zero and one")
    if top_count < 0:
        raise ValueError("top second-home gap count cannot be negative")
    connection = duckdb.connect()
    try:
        connection.register("_census_input", census)
        connection.register("_ff_communes_input", ff_communes)
        connection.execute(
            """
            CREATE TEMP TABLE _comparison AS
            SELECT coalesce(c.commune_code, f.commune_code) AS commune_code,
                c.commune_code IS NOT NULL AS in_census,
                f.commune_code IS NOT NULL AS in_ff,
                c.dwellings AS census_dwellings,
                f.dwellings AS ff_dwellings,
                c.main_residences AS census_main_residences,
                f.main_residences AS ff_main_residences,
                c.second_homes AS census_second_homes,
                f.second_homes AS ff_second_homes,
                c.vacant AS census_vacant,
                f.vacant AS ff_vacant,
                f.recent_transfers AS ff_recent_transfers,
                f.owner_occupied_main_residences
                    AS ff_owner_occupied_main_residences,
                f.owner_occupied_second_homes
                    AS ff_owner_occupied_second_homes,
                f.owner_occupied_recent_transfers
                    AS ff_owner_occupied_recent_transfers
            FROM _census_input AS c
            FULL OUTER JOIN _ff_communes_input AS f USING (commune_code)
            """
        )
        connection.execute(
            """
            CREATE TEMP TABLE _metric_rows AS
            WITH scenario_values AS (
                SELECT *,
                    (ff_owner_occupied_main_residences
                     - ff_owner_occupied_recent_transfers)
                    / NULLIF(
                        ff_owner_occupied_main_residences
                        - ff_owner_occupied_recent_transfers
                        + ff_owner_occupied_second_homes,
                        0
                    ) AS settled_owner_main_share
                FROM _comparison
            )
            SELECT commune_code, 'configured' AS scenario,
                'dwellings' AS metric, census_dwellings AS census_value,
                ff_dwellings AS ff_value FROM scenario_values
            UNION ALL
            SELECT commune_code, 'configured', 'main_residences',
                census_main_residences, ff_main_residences
                FROM scenario_values
            UNION ALL
            SELECT commune_code, 'configured', 'second_homes',
                census_second_homes, ff_second_homes
                FROM scenario_values
            UNION ALL
            SELECT commune_code, 'configured', 'vacant',
                census_vacant, ff_vacant FROM scenario_values
            UNION ALL
            SELECT commune_code, 'exclude_recent', 'main_residences',
                census_main_residences,
                ff_main_residences - ff_recent_transfers
                FROM scenario_values
            UNION ALL
            SELECT commune_code, 'exclude_recent', 'second_homes',
                census_second_homes, ff_second_homes FROM scenario_values
            UNION ALL
            SELECT commune_code, 'split_recent', 'main_residences',
                census_main_residences,
                ff_main_residences - ff_recent_transfers
                    + ff_recent_transfers * settled_owner_main_share
                FROM scenario_values
            UNION ALL
            SELECT commune_code, 'split_recent', 'second_homes',
                census_second_homes, ff_second_homes
                    + ff_recent_transfers * (1 - settled_owner_main_share)
                FROM scenario_values
            """
        )
        matches = connection.execute(
            """
            SELECT count(*) FILTER (WHERE in_census AND in_ff),
                count(*) FILTER (WHERE in_census AND NOT in_ff),
                count(*) FILTER (WHERE NOT in_census AND in_ff)
            FROM _comparison
            """
        ).fetchone()
        if matches is None:
            raise RuntimeError("failed to count matched communes")
        matched, census_only, ff_only = (int(value) for value in matches)

        totals: dict[str, tuple[float | None, float | None]] = {}
        for measure in MEASURES:
            census_total = connection.execute(
                f"SELECT sum({_quoted_identifier(measure)}) FROM _census_input"
            ).fetchone()[0]
            ff_total = connection.execute(
                f"SELECT sum({_quoted_identifier(measure)}) FROM _ff_communes_input"
            ).fetchone()[0]
            totals[measure] = (
                None if census_total is None else float(census_total),
                None if ff_total is None else float(ff_total),
            )

        quantile_names = [f"q{int(round(quantile * 100))}" for quantile in quantiles]
        quantile_sql = ", ".join(
            f"quantile_cont(ratio, ?) FILTER (WHERE ratio IS NOT NULL) AS {name}"
            for name in quantile_names
        )
        statistics = (
            connection.execute(
                f"""
            WITH ratios AS (
                SELECT *,
                    ff_value / NULLIF(census_value, 0) AS ratio
                FROM _metric_rows
            )
            SELECT scenario, metric,
                count(*) FILTER (WHERE ratio IS NOT NULL) AS ratio_communes,
                sum(census_value) FILTER (
                    WHERE census_value IS NOT NULL AND ff_value IS NOT NULL
                ) AS matched_census_total,
                sum(ff_value) FILTER (
                    WHERE census_value IS NOT NULL AND ff_value IS NOT NULL
                ) AS matched_ff_total,
                sum(ff_value) FILTER (
                    WHERE census_value IS NOT NULL AND ff_value IS NOT NULL
                ) / NULLIF(sum(census_value) FILTER (
                    WHERE census_value IS NOT NULL AND ff_value IS NOT NULL
                ), 0) AS total_ratio,
                {quantile_sql}
            FROM ratios
            GROUP BY scenario, metric
            ORDER BY scenario, metric
            """,
                list(quantiles),
            )
            .to_arrow_table()
            .to_pylist()
        )

        scenario_nmae = connection.execute(
            """
            WITH by_measure AS (
                SELECT scenario, metric,
                    sum(abs(ff_value - census_value))
                        / NULLIF(sum(census_value), 0) AS normalized_error
                FROM _metric_rows
                WHERE scenario IN ('configured', 'exclude_recent', 'split_recent')
                    AND metric IN ('main_residences', 'second_homes')
                    AND census_value IS NOT NULL AND ff_value IS NOT NULL
                GROUP BY scenario, metric
            )
            SELECT scenario, avg(normalized_error)
            FROM by_measure
            GROUP BY scenario
            """
        ).fetchall()
        nmae_by_scenario = {
            str(scenario): None if value is None else float(value)
            for scenario, value in scenario_nmae
        }
        top_gaps = (
            connection.execute(
                """
            SELECT commune_code, census_second_homes, ff_second_homes,
                ff_second_homes - census_second_homes AS signed_gap
            FROM _comparison
            WHERE census_second_homes IS NOT NULL
                AND ff_second_homes IS NOT NULL
            ORDER BY abs(ff_second_homes - census_second_homes) DESC,
                commune_code
            LIMIT ?
            """,
                [top_count],
            )
            .to_arrow_table()
            .to_pylist()
        )
        return ReportSummary(
            matched_communes=matched,
            census_only_communes=census_only,
            ff_only_communes=ff_only,
            totals=totals,
            statistics=statistics,
            scenario_nmae={
                scenario: nmae_by_scenario.get(scenario) for scenario in SCENARIOS
            },
            top_second_home_gaps=top_gaps,
        )
    finally:
        connection.close()


def _extract_filosofi_200m(
    archive: Path,
    directory: Path,
) -> Path:
    """Extract the metropolitan 200 m CSV for section-6.5 validation."""
    with zipfile.ZipFile(archive) as zipped:
        member = next(
            (
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_200m_met.csv")
            ),
            None,
        )
        if member is None:
            raise FileNotFoundError(f"metropolitan 200 m CSV is missing from {archive}")
        target = directory / "filosofi_200m.csv"
        with zipped.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return target


def calculate_natural_cell_ratios(
    connection: duckdb.DuckDBPyConnection,
    natural: pa.Table | Path,
    own: pa.Table | Path,
    hybrid: pa.Table | Path,
    quantiles: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
) -> list[dict[str, Any]]:
    """Compare main dwellings with households in fully contained cells, section 6.5."""
    if not quantiles or any(not 0 <= q <= 1 for q in quantiles):
        raise ValueError("cell ratio quantiles must be between zero and one")
    registered = []
    sources = []
    for name, value in (("natural", natural), ("own", own), ("hybrid", hybrid)):
        if isinstance(value, pa.Table):
            relation = f"_comparison_{name}"
            connection.register(relation, value)
            registered.append(relation)
        else:
            reader = "read_csv_auto" if name == "natural" else "read_parquet"
            relation = f"{reader}({_sql_string(str(value))})"
        sources.append(relation)
    try:
        rows = (
            connection.execute(
                f"""
            WITH natural_input AS (
                SELECT idcar_nat, CAST(tmaille AS BIGINT) AS size_m,
                    CAST(men AS DOUBLE) AS households,
                    CAST(regexp_extract(idcar_nat, 'mN([0-9]+)E', 1) AS BIGINT) AS n,
                    CAST(regexp_extract(idcar_nat, 'E([0-9]+)$', 1) AS BIGINT) AS e
                FROM {sources[0]}
            ),
            own AS (
                SELECT natural_cell_id, sum(main_residences) AS main
                FROM {sources[1]} GROUP BY natural_cell_id
            ),
            hybrid AS (
                SELECT natural_cell_id, sum(main_residences) AS main
                FROM {sources[2]} GROUP BY natural_cell_id
            ),
            ratios AS (
                SELECT n.size_m, coalesce(o.main, 0) / n.households AS own_ratio,
                    coalesce(h.main, 0) / n.households AS hybrid_ratio
                FROM natural_input n
                LEFT JOIN own o ON n.idcar_nat = o.natural_cell_id
                LEFT JOIN hybrid h ON n.idcar_nat = h.natural_cell_id
                CROSS JOIN department_boundary b
                WHERE n.households > 0
                    AND n.e >= ST_XMin(b.geom)
                    AND n.n >= ST_YMin(b.geom)
                    AND n.e + n.size_m <= ST_XMax(b.geom)
                    AND n.n + n.size_m <= ST_YMax(b.geom)
                    AND ST_Covers(b.geom, ST_MakeEnvelope(
                        n.e, n.n, n.e + n.size_m, n.n + n.size_m
                    ))
            )
            SELECT size_m, count(*) AS cells,
                quantile_cont(own_ratio, ?::DOUBLE[]) AS own,
                quantile_cont(hybrid_ratio, ?::DOUBLE[]) AS hybrid
            FROM ratios GROUP BY size_m ORDER BY size_m
            """,
                [list(quantiles), list(quantiles)],
            )
            .to_arrow_table()
            .to_pylist()
        )
    finally:
        for relation in registered:
            connection.unregister(relation)
    return rows


def _load_department_boundary(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    department: str,
) -> None:
    """Dissolve 2021 commune contours in EPSG:3035 for section 6.5."""
    if not path.is_file():
        raise FileNotFoundError(path)
    connection.execute("LOAD spatial")
    connection.execute(
        f"""
        CREATE TEMP TABLE department_boundary AS
        SELECT ST_Transform(ST_Union_Agg(ST_MakeValid(geom)),
                            'EPSG:4326', 'EPSG:3035', true) AS geom,
            count(geom) AS commune_count
        FROM ST_Read({_sql_string(str(path))})
        WHERE departement = ?
        """,
        [department],
    )
    if connection.execute(
        "SELECT geom IS NULL OR commune_count = 0 FROM department_boundary"
    ).fetchone()[0]:
        raise ValueError(f"no commune contours for department {department}")


def _extract_filosofi_natural(archive: Path, directory: Path) -> Path:
    with zipfile.ZipFile(archive) as zipped:
        member = next(
            (
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_nivNaturel_met.csv")
            ),
            None,
        )
        if member is None:
            raise FileNotFoundError(
                f"metropolitan natural CSV is missing from {archive}"
            )
        target = directory / "filosofi_natural.csv"
        with zipped.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return target


def render_comparison_report(
    summaries: dict[str, ReportSummary],
    cell_rows: list[dict[str, Any]],
    branch_counts: dict[str, int],
    department: str,
    config: OriginsConfig,
) -> str:
    """Render the experimental section-6.5 comparison with suppressed counts."""
    threshold = config.report.count_suppression_threshold
    quantiles = config.report.ratio_quantiles
    keys = [f"q{int(round(q * 100))}" for q in quantiles]
    headers = [f"P{int(round(q * 100))}" if q != 0.5 else "Median" for q in quantiles]
    labels = ("own", "hybrid_2024")
    lines = [
        "# 2022 second-home classification comparison",
        "",
        f"- Department `{department}`; 2021 census.",
        "- `hybrid_2024` is adopted by section 6.3; `own` is retained "
        "for comparison.",
        "- Hybrid uses settled 2024 RS/RPPO, otherwise 2022 proba_rprs; "
        "vacancy and recent-transfer indicators use 2022.",
        "- Ratios and scenario comparisons use matched communes only.",
        "",
        "## Housing totals and commune ratios",
        "",
        "| Measure | Classification | Census total | FF total | Matched census | "
        f"Matched FF | Total ratio | {' | '.join(headers)} |",
        "|---|---|" + "|".join("---:" for _ in range(5 + len(headers))) + "|",
    ]
    for measure in MEASURES:
        for label in labels:
            summary = summaries[label]
            row = next(
                item
                for item in summary.statistics
                if item["scenario"] == "configured" and item["metric"] == measure
            )
            census, ff = summary.totals[measure]
            values = [
                _format_count(census, threshold),
                _format_count(ff, threshold),
                _format_count(row["matched_census_total"], threshold),
                _format_count(row["matched_ff_total"], threshold),
                _format_ratio(row["total_ratio"]),
                *[_format_ratio(row[key]) for key in keys],
            ]
            lines.append(
                f"| {MEASURE_LABELS[measure]} | {label} | " + " | ".join(values) + " |"
            )
    lines.extend(
        [
            "",
            "## Recent-transfer interpretations",
            "",
            "The split uses the settled owner-occupied main/second-home ratio. "
            "Scenario error is the mean normalized absolute error of main and "
            "second homes.",
            "",
            "| Interpretation | Measure | Classification | Matched FF | "
            "Matched census | "
            f"Total ratio | {' | '.join(headers)} | Scenario error |",
            "|---|---|---|" + "|".join("---:" for _ in range(4 + len(headers))) + "|",
        ]
    )
    for scenario in SCENARIOS:
        for measure in ("main_residences", "second_homes"):
            for label in labels:
                summary = summaries[label]
                row = next(
                    item
                    for item in summary.statistics
                    if item["scenario"] == scenario and item["metric"] == measure
                )
                values = [
                    _format_count(row["matched_ff_total"], threshold),
                    _format_count(row["matched_census_total"], threshold),
                    _format_ratio(row["total_ratio"]),
                    *[_format_ratio(row[key]) for key in keys],
                    _format_ratio(summary.scenario_nmae[scenario]),
                ]
                lines.append(
                    f"| {SCENARIO_LABELS[scenario]} | {MEASURE_LABELS[measure]} | "
                    f"{label} | " + " | ".join(values) + " |"
                )
    lines.extend(
        [
            "",
            "## Largest second-home gaps",
            "",
            "Each classification is ranked separately by absolute gap.",
            "",
            "| Rank | Own commune | Census | Own FF | Own gap | "
            "Hybrid commune | Census | Hybrid FF | Hybrid gap |",
            "|---:|---|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    own_gaps = summaries["own"].top_second_home_gaps
    hybrid_gaps = summaries["hybrid_2024"].top_second_home_gaps
    for rank in range(max(len(own_gaps), len(hybrid_gaps))):
        values = []
        for gaps in (own_gaps, hybrid_gaps):
            if rank >= len(gaps):
                values.extend(["n/a"] * 4)
                continue
            row = gaps[rank]
            values.append(row["commune_code"])
            values.extend(
                _format_count(row[key], threshold)
                for key in ("census_second_homes", "ff_second_homes", "signed_gap")
            )
        lines.append(f"| {rank + 1} | " + " | ".join(values) + " |")
    cell_headers = [
        "Median" if q == 0.5 else f"P{int(round(q * 100))}"
        for q in config.report.cell_ratio_quantiles
    ]
    lines.extend(
        [
            "",
            "## Main residences / Filosofi households by natural cell size",
            "",
            "Natural squares must be completely covered by the dissolved 2021 "
            "department boundary in EPSG:3035; zero-household cells are excluded.",
            "",
            f"| Size (m) | Cells | Classification | {' | '.join(cell_headers)} |",
            "|---:|---:|---|" + "|".join("---:" for _ in cell_headers) + "|",
        ]
    )
    for row in cell_rows:
        for label, key in (("own", "own"), ("hybrid_2024", "hybrid")):
            values = " | ".join(_format_ratio(value) for value in row[key])
            lines.append(
                f"| {row['size_m']} | {_format_count(row['cells'], threshold)} | "
                f"{label} | {values} |"
            )
    lines.extend(
        [
            "",
            "## Hybrid rule branches",
            "",
            "All 2022 dwellings in the department partition, "
            "including unlocated dwellings.",
            "",
            "| Branch | Count |",
            "|---|---:|",
        ]
    )
    for key in ("hybrid_settled_rs", "hybrid_settled_rppo", "hybrid_fallback"):
        lines.append(
            f"| {key.replace('_', ' ')} | "
            f"{_format_count(branch_counts[key], threshold)} |"
        )
    lines.extend(
        ["", f"Counts below {threshold} are suppressed as `<{threshold}`.", ""]
    )
    return "\n".join(lines)


def build_comparison_report(
    department: str,
    own_directory: str | Path,
    hybrid_directory: str | Path,
    *,
    config_path: str | Path = "config/origins.yaml",
    output: str | Path | None = None,
) -> Path:
    """Build the aggregate 2022 experimental comparison for section 6.5."""
    config = load_origins_config(config_path)
    vintage = 2022
    directories = {"own": Path(own_directory), "hybrid_2024": Path(hybrid_directory)}
    if directories["own"].resolve() == directories["hybrid_2024"].resolve():
        raise ValueError("own and hybrid inputs must be separate directories")
    metadata = {}
    for label, directory in directories.items():
        path = directory / config.report.metadata_pattern.format(vintage=vintage)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("second_home_source") != label:
            raise ValueError(f"{path} does not identify a {label} build")
        metadata[label] = data
    if metadata["own"].get("departments") != metadata["hybrid_2024"].get(
        "departments"
    ) or department not in metadata["own"].get("departments", []):
        raise ValueError(
            "build departments must match and include the report department"
        )
    branch_counts = (
        metadata["hybrid_2024"].get("department_diagnostics", {}).get(department, {})
    )
    branch_keys = ("hybrid_settled_rs", "hybrid_settled_rppo", "hybrid_fallback")
    if any(type(branch_counts.get(key)) is not int for key in branch_keys):
        raise ValueError("hybrid metadata is missing department branch counts")
    connection = open_connection()
    try:
        census = load_census_department(connection, 2021, department, config)
        summaries = {}
        for label, directory in directories.items():
            communes, _ = _ff_communes_table(
                connection, vintage, department, directory, config
            )
            summaries[label] = calculate_report_summary(
                census,
                communes,
                config.report.ratio_quantiles,
                config.report.top_second_home_gaps,
            )
        _load_department_boundary(
            connection, Path(config.report.contours_2021), department
        )
        with tempfile.TemporaryDirectory(prefix="filosofi_natural_report_") as folder:
            natural = _extract_filosofi_natural(
                Path(config.filosofi_natural_archive), Path(folder)
            )
            cells = calculate_natural_cell_ratios(
                connection,
                natural,
                directories["own"]
                / config.report.ff_cells_pattern.format(vintage=vintage),
                directories["hybrid_2024"]
                / config.report.ff_cells_pattern.format(vintage=vintage),
                config.report.cell_ratio_quantiles,
            )
    finally:
        connection.close()
    report_path = Path(output or config.report.output_directory) / (
        config.report.comparison_report_pattern.format(vintage=vintage)
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_suffix(".tmp.md")
    temporary.write_text(
        render_comparison_report(summaries, cells, branch_counts, department, config),
        encoding="utf-8",
    )
    temporary.replace(report_path)
    return report_path


def _social_housing_totals(
    connection: duckdb.DuckDBPyConnection,
    vintage: int,
    department: str,
    output_directory: Path,
    config: OriginsConfig,
) -> tuple[float | None, float | None]:
    """Sum FF and Filosofi social-housing counts for section 6.5."""
    cell_path = output_directory / config.report.ff_cells_pattern.format(
        vintage=vintage
    )
    if not cell_path.is_file():
        raise FileNotFoundError(
            f"missing cell aggregation {cell_path}; build this FF vintage first"
        )
    archive = Path(config.filosofi_200m_archive)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with tempfile.TemporaryDirectory(prefix="filosofi_report_") as directory:
        csv_path = _extract_filosofi_200m(archive, Path(directory))
        result = connection.execute(
            """
            SELECT
                sum(coalesce(ff.social_housing_main_residences, 0)),
                sum(TRY_CAST(f.log_soc AS DOUBLE))
            FROM read_csv_auto(?, header=true) AS f
            LEFT JOIN read_parquet(?) AS ff
              ON f.idcar_200m =
                'CRS3035RES200mN'
                || CAST(CAST(floor(ff.cell_id / 100000) * 200 AS BIGINT)
                    AS VARCHAR)
                || 'E'
                || CAST(CAST((ff.cell_id % 100000) * 200 AS BIGINT)
                    AS VARCHAR)
            WHERE EXISTS (
                SELECT 1
                FROM UNNEST(string_split(CAST(f.lcog_geo AS VARCHAR), ','))
                    AS commune(code)
                WHERE left(trim(commune.code), length(?)) = ?
            )
            """,
            [str(csv_path), str(cell_path), department, department],
        ).fetchone()
    if result is None:
        return None, None
    return (
        None if result[0] is None else float(result[0]),
        None if result[1] is None else float(result[1]),
    )


def _format_count(value: float | int | None, threshold: int) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    if abs(float(value)) < threshold:
        return f"<{threshold}"
    return f"{float(value):,.1f}"


def _format_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value:.1%}"


def _census_selector_text(
    config: CensusVintageConfig,
) -> str:
    if config.format == "zip_csv":
        return ", ".join(
            f"{name}=`{column}`"
            for name, column in (
                ("dwellings", config.measures["dwellings"]),
                ("main residences", config.measures["main_residences"]),
                ("second homes", config.measures["second_homes"]),
                ("vacant dwellings", config.measures["vacant"]),
            )
        )
    measures = ", ".join(f"{name}=`{config.measures[name]}`" for name in MEASURES)
    return (
        f"`{config.geography_type_column}={config.geography_type}`, "
        f"`{config.time_period_column}={config.time_period}`, "
        f"`{config.table_column}={config.table_id}`, "
        f"`{config.dataset_column}={config.dataset_id}`; "
        f"`{config.measure_column}`: {measures}"
    )


def render_commune_report(
    summary: ReportSummary,
    vintage: int,
    census_vintage: int,
    department: str,
    census_config: CensusVintageConfig,
    quantiles: tuple[float, ...],
    diagnostics: dict[str, int],
    social_totals: tuple[float | None, float | None],
    suppression_threshold: int,
) -> str:
    """Render section-6.5 aggregate counts with configured suppression."""
    quantile_keys = [f"q{int(round(quantile * 100))}" for quantile in quantiles]
    quantile_headers = [
        "Median" if quantile == 0.5 else f"P{int(round(quantile * 100))}"
        for quantile in quantiles
    ]
    lines = [
        f"# Fichiers fonciers commune report — {vintage}",
        "",
        f"- Department: `{department}`",
        f"- Census comparison: `{census_vintage}`",
        f"- Census selectors: {_census_selector_text(census_config)}",
        (
            "- Commune coverage: "
            f"{_format_count(summary.matched_communes, suppression_threshold)} "
            "matched; "
            f"{_format_count(summary.census_only_communes, suppression_threshold)} "
            "census-only; "
            f"{_format_count(summary.ff_only_communes, suppression_threshold)} "
            "FF-only."
        ),
        "- Ratios and scenario comparisons use matched communes only.",
        "",
        "## Housing totals and commune ratios",
        "",
        "| Measure | Census total | FF total | Matched census | Matched FF | "
        f"Total ratio | {' | '.join(quantile_headers)} |",
        "|---|" + "|".join("---:" for _ in range(5 + len(quantile_keys))) + "|",
    ]
    baseline_stats = {
        row["metric"]: row
        for row in summary.statistics
        if row["scenario"] == "configured"
    }
    for measure in MEASURES:
        row = baseline_stats.get(measure, {})
        census_total, ff_total = summary.totals[measure]
        quantile_values = " | ".join(
            _format_ratio(row.get(name)) for name in quantile_keys
        )
        matched_census = _format_count(
            row.get("matched_census_total"), suppression_threshold
        )
        matched_ff = _format_count(row.get("matched_ff_total"), suppression_threshold)
        lines.append(
            f"| {MEASURE_LABELS[measure]} | "
            f"{_format_count(census_total, suppression_threshold)} | "
            f"{_format_count(ff_total, suppression_threshold)} | "
            f"{matched_census} | {matched_ff} | "
            f"{_format_ratio(row.get('total_ratio'))} | "
            f"{quantile_values} |"
        )
    lines.extend(
        [
            "",
            "## Recent-transfer interpretations",
            "",
            "The split uses the commune share of settled owner-occupied main "
            "residences among settled owner-occupied main residences and "
            "second homes. The ranking metric is the mean of the main- and "
            "second-home normalized absolute count errors.",
            "",
            "| Interpretation | Measure | Matched FF | Matched census | "
            f"Total ratio | {' | '.join(quantile_headers)} | Scenario error |",
            "|---|---|" + "|".join("---:" for _ in range(4 + len(quantile_keys))) + "|",
        ]
    )
    for scenario in SCENARIOS:
        for measure in ("main_residences", "second_homes"):
            row = next(
                (
                    item
                    for item in summary.statistics
                    if item["scenario"] == scenario and item["metric"] == measure
                ),
                {},
            )
            quantile_values = " | ".join(
                _format_ratio(row.get(name)) for name in quantile_keys
            )
            ff_value = _format_count(row.get("matched_ff_total"), suppression_threshold)
            census_value = _format_count(
                row.get("matched_census_total"), suppression_threshold
            )
            lines.append(
                f"| {SCENARIO_LABELS[scenario]} | "
                f"{MEASURE_LABELS[measure]} | "
                f"{ff_value} | {census_value} | "
                f"{_format_ratio(row.get('total_ratio'))} | "
                f"{quantile_values} | "
                f"{_format_ratio(summary.scenario_nmae[scenario])} |"
            )
    available_errors = {
        scenario: error
        for scenario, error in summary.scenario_nmae.items()
        if error is not None
    }
    if available_errors:
        closest = min(
            available_errors,
            key=lambda scenario: (
                available_errors[scenario]
                if available_errors[scenario] is not None
                else math.inf
            ),
        )
        lines.extend(
            [
                "",
                f"Closest under the stated error metric: "
                f"{SCENARIO_LABELS[closest]} "
                f"({_format_ratio(available_errors[closest])}).",
            ]
        )

    lines.extend(
        [
            "",
            f"## Largest {len(summary.top_second_home_gaps)} second-home gaps",
            "",
            "| Commune | Census second homes | FF second homes | FF minus census |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summary.top_second_home_gaps:
        lines.append(
            "| {code} | {census} | {ff} | {gap} |".format(
                code=row["commune_code"],
                census=_format_count(row["census_second_homes"], suppression_threshold),
                ff=_format_count(row["ff_second_homes"], suppression_threshold),
                gap=_format_count(row["signed_gap"], suppression_threshold),
            )
        )

    ff_social, filosofi_social = social_totals
    social_ratio = (
        None
        if (
            ff_social is None
            or filosofi_social in (None, 0)
            or abs(ff_social) < suppression_threshold
            or abs(filosofi_social) < suppression_threshold
        )
        else ff_social / filosofi_social
    )
    lines.extend(
        [
            "",
            "## Social housing and build diagnostics",
            "",
            f"- FF social main residences: "
            f"{_format_count(ff_social, suppression_threshold)}",
            f"- Filosofi `log_soc`: "
            f"{_format_count(filosofi_social, suppression_threshold)}",
            f"- FF / Filosofi ratio: {_format_ratio(social_ratio)}",
            "",
            "| Diagnostic | Count |",
            "|---|---:|",
        ]
    )
    for name, value in sorted(diagnostics.items()):
        lines.append(
            f"| {name.replace('_', ' ')} | "
            f"{_format_count(value, suppression_threshold)} |"
        )
    lines.extend(
        [
            "",
            f"Counts with absolute value below {suppression_threshold} are "
            "suppressed as `<"
            f"{suppression_threshold}`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_commune_report(
    vintage: int,
    department: str,
    *,
    config_path: str | Path = "config/origins.yaml",
    output: str | Path | None = None,
) -> Path:
    """Build an aggregate-only section-6.5 report from completed FF outputs."""
    config = load_origins_config(config_path)
    try:
        census_vintage = config.report.ff_vintage_to_census[vintage]
    except KeyError as error:
        raise ValueError(
            f"no census vintage configured for FF vintage {vintage}"
        ) from error
    census_config = config.census[census_vintage]
    output_directory = Path(output or config.report.output_directory)
    connection = open_connection()
    try:
        census = load_census_department(
            connection,
            census_vintage,
            department,
            config,
        )
        ff_communes, _ = _ff_communes_table(
            connection,
            vintage,
            department,
            output_directory,
            config,
        )
        summary = calculate_report_summary(
            census,
            ff_communes,
            config.report.ratio_quantiles,
            config.report.top_second_home_gaps,
        )
        diagnostics_path = output_directory / (
            config.report.metadata_pattern.format(vintage=vintage)
        )
        if not diagnostics_path.is_file():
            raise FileNotFoundError(f"missing build metadata {diagnostics_path}")
        metadata = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError(f"invalid build metadata in {diagnostics_path}")
        diagnostics = metadata.get("diagnostics")
        if not isinstance(diagnostics, dict) or any(
            not isinstance(name, str) or type(value) is not int
            for name, value in diagnostics.items()
        ):
            raise ValueError(f"invalid diagnostics in {diagnostics_path}")
        social_totals = _social_housing_totals(
            connection,
            vintage,
            department,
            output_directory,
            config,
        )
    finally:
        connection.close()

    report_path = output_directory / config.report.report_pattern.format(
        vintage=vintage
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_commune_report(
        summary,
        vintage,
        census_vintage,
        department,
        census_config,
        config.report.ratio_quantiles,
        diagnostics,
        social_totals,
        config.report.count_suppression_threshold,
    )
    temporary = report_path.with_suffix(".tmp.md")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(report_path)
    LOGGER.info("Wrote aggregate-only report to %s", report_path)
    return report_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the commune validation report."""
    parser = argparse.ArgumentParser(
        description="Report commune-level Fichiers fonciers validation"
    )
    parser.add_argument("--vintage", type=int, required=True)
    parser.add_argument("--department")
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare-hybrid", type=Path)
    parser.add_argument("--compare-own", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    department = args.department or _pilot_department(args.pilot_config)
    if args.compare_hybrid:
        if args.vintage != 2022:
            parser.error("--compare-hybrid requires vintage 2022")
        config = load_origins_config(args.config)
        report_path = build_comparison_report(
            department,
            args.compare_own or args.output or config.report.output_directory,
            args.compare_hybrid,
            config_path=args.config,
            output=args.output,
        )
    else:
        if args.compare_own:
            parser.error("--compare-own requires --compare-hybrid")
        report_path = build_commune_report(
            args.vintage,
            department,
            config_path=args.config,
            output=args.output,
        )
    print(json.dumps({"report": str(report_path)}, indent=2))
    return 0
