"""Section 6.5 validation for the 2021 Filosofi downscaling."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
from common.duckdb_io import open_connection

from landgrid.origins.fichiers_fonciers import (
    _pilot_department,
    load_origins_config,
)
from landgrid.origins.report import _load_department_boundary

LOGGER = logging.getLogger(__name__)


def _sql_string(value: str) -> str:
    """Escape a filesystem path for a DuckDB relation expression."""
    return "'" + value.replace("'", "''") + "'"


def _source_relation(
    connection: duckdb.DuckDBPyConnection,
    name: str,
    source: pa.Table | Path,
) -> tuple[str, bool]:
    """Register an Arrow table or return a lazy CSV or Parquet reader."""
    if isinstance(source, pa.Table):
        connection.register(name, source)
        return name, True
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(path)
    reader = "read_parquet" if path.suffix.casefold() == ".parquet" else "read_csv_auto"
    return f"{reader}({_sql_string(str(path.resolve()))})", False


def _columns(
    connection: duckdb.DuckDBPyConnection,
    relation: str,
) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    }


def calculate_validation_metrics(
    connection: duckdb.DuckDBPyConnection,
    downscaled: pa.Table | Path,
    filosofi_200m: pa.Table | Path,
    ff_cells: pa.Table | Path,
    eurostat: pa.Table | Path,
    *,
    department: str,
    cell_resolution_m: int,
    eurostat_resolution_m: int,
    density_thresholds_population_km2: tuple[int, int],
    within_tolerance_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Calculate aggregate-only 200 m and 1 km checks for section 6.5."""
    if cell_resolution_m <= 0 or eurostat_resolution_m <= 0:
        raise ValueError("validation cell resolutions must be positive")
    if (
        len(density_thresholds_population_km2) != 2
        or density_thresholds_population_km2[0] <= 0
        or density_thresholds_population_km2[0]
        >= density_thresholds_population_km2[1]
    ):
        raise ValueError("density thresholds must be two increasing positive values")
    if not 0 <= within_tolerance_fraction <= 1:
        raise ValueError("within-cell tolerance must be between zero and one")
    sources = []
    registered = []
    for name, value in (
        ("downscaled", downscaled),
        ("filosofi_200m", filosofi_200m),
        ("ff_cells", ff_cells),
        ("eurostat", eurostat),
    ):
        relation, was_registered = _source_relation(
            connection, f"_validation_{name}_input", value
        )
        sources.append(relation)
        if was_registered:
            registered.append(f"_validation_{name}_input")

    downscaled_relation, insee_relation, ff_relation, eurostat_relation = sources
    try:
        required_columns = (
            (
                downscaled_relation,
                {
                    "cell_id",
                    "natural_cell_id",
                    "natural_cell_size_m",
                    "ind",
                    "men",
                    "ind_0_3",
                    "ind_4_5",
                    "ind_6_10",
                    "ind_11_17",
                    "ind_65_79",
                    "ind_80p",
                },
            ),
            (
                insee_relation,
                {
                    "idcar_200m",
                    "idcar_1km",
                    "idcar_nat",
                    "lcog_geo",
                    "i_est_200",
                    "ind",
                    "men",
                    "ind_0_3",
                    "ind_4_5",
                    "ind_6_10",
                    "ind_11_17",
                    "ind_65_79",
                    "ind_80p",
                },
            ),
            (ff_relation, {"cell_id", "main_residences"}),
            (eurostat_relation, {"GRD_ID", "T", "LAND_SURFACE"}),
        )
        for relation, required in required_columns:
            missing = required - _columns(connection, relation)
            if missing:
                raise ValueError(
                    "validation input lacks required columns: "
                    + ", ".join(sorted(missing))
                )

        northing = (
            f"CAST(floor(cell_id / 100000) AS BIGINT) * {cell_resolution_m}"
        )
        easting = f"(cell_id % 100000) * {cell_resolution_m}"
        cell_code = (
            f"'CRS3035RES{cell_resolution_m}mN' || CAST({northing} AS VARCHAR) "
            f"|| 'E' || CAST({easting} AS VARCHAR)"
        )
        first_density_label = f"<{density_thresholds_population_km2[0]}"
        second_density_label = (
            f"{density_thresholds_population_km2[0]}-"
            f"<{density_thresholds_population_km2[1]}"
        )
        third_density_label = f">={density_thresholds_population_km2[1]}"
        density_expression = f"""
            CASE
                WHEN CAST(T AS DOUBLE) / LAND_SURFACE
                    < {density_thresholds_population_km2[0]}
                    THEN '{first_density_label}'
                WHEN CAST(T AS DOUBLE) / LAND_SURFACE
                    < {density_thresholds_population_km2[1]}
                    THEN '{second_density_label}'
                ELSE '{third_density_label}'
            END
        """
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_eurostat AS
            SELECT GRD_ID, CAST(T AS DOUBLE) AS population,
                CAST(LAND_SURFACE AS DOUBLE) AS land_surface,
                {density_expression} AS density_class
            FROM {eurostat_relation}
            WHERE T >= 0 AND LAND_SURFACE > 0
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_downscaled AS
            SELECT *, {cell_code} AS cell_code,
                {northing} AS northing_m, {easting} AS easting_m
            FROM {downscaled_relation}
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_ff AS
            SELECT cell_id, sum(main_residences) AS main_residences
            FROM {ff_relation}
            GROUP BY cell_id
            """
        )
        missing_predictions = connection.execute(
            f"""
            SELECT count(*)
            FROM {insee_relation} i
            LEFT JOIN _validation_downscaled d
              ON d.cell_code = i.idcar_200m
            WHERE i.i_est_200 = 0
                AND CAST(regexp_extract(
                    i.idcar_nat, 'RES([0-9]+)mN', 1
                ) AS BIGINT) > {cell_resolution_m}
                AND EXISTS (
                    SELECT 1
                    FROM UNNEST(string_split(
                        CAST(i.lcog_geo AS VARCHAR), ','
                    )) AS commune(code)
                    WHERE left(trim(commune.code), length(?)) = ?
                )
                AND d.cell_id IS NULL
            """,
            [department, department],
        ).fetchone()[0]
        if missing_predictions:
            raise ValueError(
                "non-imputed INSEE cells in the validation scope are missing "
                "from the downscaled output"
            )
        missing_density = connection.execute(
            f"""
            SELECT count(*)
            FROM {insee_relation} i
            JOIN _validation_downscaled d
              ON d.cell_code = i.idcar_200m
            LEFT JOIN _validation_eurostat e ON e.GRD_ID = i.idcar_1km
            WHERE i.i_est_200 = 0
                AND d.natural_cell_size_m > {cell_resolution_m}
                AND EXISTS (
                    SELECT 1
                    FROM UNNEST(string_split(
                        CAST(i.lcog_geo AS VARCHAR), ','
                    )) AS commune(code)
                    WHERE left(trim(commune.code), length(?)) = ?
                )
                AND e.GRD_ID IS NULL
            """,
            [department, department],
        ).fetchone()[0]
        if missing_density:
            raise ValueError(
                "Eurostat 1 km population or land surface is missing for "
                "non-imputed INSEE validation cells"
            )

        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _validation_natural_totals AS
            SELECT natural_cell_id,
                sum(ind) AS individuals,
                sum(men) AS households,
                sum(ind_0_3 + ind_4_5 + ind_6_10 + ind_11_17) AS under_18,
                sum(ind_65_79 + ind_80p) AS age_65_plus
            FROM _validation_downscaled
            GROUP BY natural_cell_id
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _validation_main_cells AS
            SELECT d.natural_cell_id,
                count(*) FILTER (
                    WHERE coalesce(f.main_residences, 0) > 0
                ) AS occupied_cell_count
            FROM _validation_downscaled d
            LEFT JOIN _validation_ff f USING (cell_id)
            GROUP BY d.natural_cell_id
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_200m AS
            SELECT i.idcar_200m, d.natural_cell_id,
                d.natural_cell_size_m, e.density_class,
                d.ind AS predicted_individuals, i.ind AS reference_individuals,
                d.men AS predicted_households, i.men AS reference_households,
                d.ind_0_3 + d.ind_4_5 + d.ind_6_10 + d.ind_11_17
                    AS predicted_under_18,
                i.ind_0_3 + i.ind_4_5 + i.ind_6_10 + i.ind_11_17
                    AS reference_under_18,
                d.ind_65_79 + d.ind_80p AS predicted_age_65_plus,
                i.ind_65_79 + i.ind_80p AS reference_age_65_plus,
                coalesce(f.main_residences, 0) AS main_residences,
                n.individuals AS natural_individuals,
                n.households AS natural_households,
                n.under_18 AS natural_under_18,
                n.age_65_plus AS natural_age_65_plus,
                m.occupied_cell_count
            FROM {insee_relation} i
            JOIN _validation_downscaled d
              ON d.cell_code = i.idcar_200m
            JOIN _validation_eurostat e ON e.GRD_ID = i.idcar_1km
            JOIN _validation_natural_totals n
              ON n.natural_cell_id = d.natural_cell_id
            JOIN _validation_main_cells m
              ON m.natural_cell_id = d.natural_cell_id
            LEFT JOIN _validation_ff f USING (cell_id)
            WHERE i.i_est_200 = 0
                AND d.natural_cell_size_m > {cell_resolution_m}
                AND EXISTS (
                    SELECT 1
                    FROM UNNEST(string_split(
                        CAST(i.lcog_geo AS VARCHAR), ','
                    )) AS commune(code)
                    WHERE left(trim(commune.code), length(?)) = ?
                )
            """,
            [department, department],
        )

        value_rows = []
        variable_fields = (
            (
                "individuals",
                "predicted_individuals",
                "reference_individuals",
                "natural_individuals",
            ),
            (
                "households",
                "predicted_households",
                "reference_households",
                "natural_households",
            ),
            (
                "under_18",
                "predicted_under_18",
                "reference_under_18",
                "natural_under_18",
            ),
            (
                "age_65_plus",
                "predicted_age_65_plus",
                "reference_age_65_plus",
                "natural_age_65_plus",
            ),
        )
        for variable, prediction, reference, natural_total in variable_fields:
            value_rows.extend(
                (
                    f"""SELECT 'proportional' AS method, '{variable}' AS variable,
                        natural_cell_size_m, density_class,
                        {prediction} AS predicted, {reference} AS reference
                    FROM _validation_200m""",
                    f"""SELECT 'equal_split' AS method, '{variable}' AS variable,
                        natural_cell_size_m, density_class,
                        CASE
                            WHEN occupied_cell_count > 0 AND main_residences > 0
                                THEN {natural_total} / occupied_cell_count
                            ELSE 0.0
                        END AS predicted,
                        {reference} AS reference
                    FROM _validation_200m""",
                )
            )
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _validation_values AS
            """
            + "\nUNION ALL\n".join(value_rows)
        )
        metrics_200m = (
            connection.execute(
                f"""
                SELECT method, variable, natural_cell_size_m, density_class,
                    count(*) AS cell_count,
                    sum(CASE WHEN reference > 0 THEN 1 ELSE 0 END)
                        AS positive_reference_count,
                    avg(abs(predicted - reference)) AS mean_absolute_error,
                    quantile_cont(
                        abs(predicted - reference) / NULLIF(abs(reference), 0),
                        0.5
                    ) AS median_absolute_relative_error,
                    avg(CASE
                        WHEN abs(predicted - reference)
                            <= {within_tolerance_fraction} * abs(reference)
                            THEN 1.0
                        ELSE 0.0
                    END) AS share_within_tolerance
                FROM _validation_values
                WHERE predicted IS NOT NULL
                GROUP BY method, variable, natural_cell_size_m, density_class
                ORDER BY method, variable, natural_cell_size_m, density_class
                """
            )
            .to_arrow_table()
            .to_pylist()
        )

        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_1km_predictions AS
            SELECT 'CRS3035RES{eurostat_resolution_m}mN'
                    || CAST(CAST(floor(northing_m / {eurostat_resolution_m})
                        * {eurostat_resolution_m} AS BIGINT) AS VARCHAR)
                    || 'E' || CAST(CAST(floor(
                        easting_m / {eurostat_resolution_m}
                    ) * {eurostat_resolution_m} AS BIGINT) AS VARCHAR) AS grid_id,
                sum(ind) AS individuals
            FROM _validation_downscaled
            GROUP BY grid_id
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_1km AS
            SELECT e.GRD_ID, e.population, e.density_class,
                coalesce(p.individuals, 0.0) AS predicted_individuals
            FROM _validation_eurostat e
            LEFT JOIN _validation_1km_predictions p ON p.grid_id = e.GRD_ID
            CROSS JOIN department_boundary b
            WHERE regexp_matches(
                e.GRD_ID,
                '^CRS3035RES{eurostat_resolution_m}mN[0-9]+E[0-9]+$'
            )
                AND ST_Covers(b.geom, ST_MakeEnvelope(
                TRY_CAST(regexp_extract(
                    e.GRD_ID, 'E([0-9]+)$', 1
                ) AS BIGINT),
                TRY_CAST(regexp_extract(
                    e.GRD_ID, 'mN([0-9]+)E', 1
                ) AS BIGINT),
                TRY_CAST(regexp_extract(
                    e.GRD_ID, 'E([0-9]+)$', 1
                ) AS BIGINT)
                    + {eurostat_resolution_m},
                TRY_CAST(regexp_extract(
                    e.GRD_ID, 'mN([0-9]+)E', 1
                ) AS BIGINT)
                    + {eurostat_resolution_m}
            ))
            """
        )
        metrics_1km = (
            connection.execute(
                f"""
                SELECT density_class, count(*) AS cell_count,
                    sum(predicted_individuals) AS downscaled_individuals,
                    sum(population) AS eurostat_individuals,
                    sum(CASE WHEN population > 0 THEN 1 ELSE 0 END)
                        AS positive_reference_count,
                    quantile_cont(
                        abs(predicted_individuals - population)
                            / NULLIF(abs(population), 0),
                        0.5
                    ) AS median_absolute_relative_error
                FROM _validation_1km
                GROUP BY density_class
                ORDER BY CASE density_class
                    WHEN '{first_density_label}' THEN 0
                    WHEN '{second_density_label}' THEN 1
                    ELSE 2
                END
                """
            )
            .to_arrow_table()
            .to_pylist()
        )
        if not metrics_200m or not metrics_1km:
            raise ValueError("section-6.5 validation scope is empty")
        return metrics_200m, metrics_1km
    finally:
        for name in registered:
            connection.unregister(name)


def _format_count(value: int, threshold: int) -> str:
    """Render a report count with small-count suppression."""
    return f"<{threshold}" if int(value) < threshold else str(int(value))


def _format_total(value: float, threshold: int) -> str:
    """Render a population total with small-count suppression."""
    return f"<{threshold}" if abs(float(value)) < threshold else f"{value:.1f}"


def render_validation_report(
    year: int,
    department: str,
    metrics_200m: list[dict[str, Any]],
    metrics_1km: list[dict[str, Any]],
    count_suppression_threshold: int,
    within_tolerance_fraction: float,
) -> str:
    """Render aggregate error statistics and totals, never cell-level rows."""
    lines = [
        f"# Section 6.5 validation — Filosofi {year}",
        "",
        f"Department: {department}. All counts below "
        f"{count_suppression_threshold} are suppressed.",
        "",
        "## INSEE 200 m cells published without imputation",
        "",
        "The median absolute relative error excludes zero-reference cells; "
        f"the ±{within_tolerance_fraction:.0%} share includes them and counts "
        "an exact zero prediction "
        "as within range. Density uses Eurostat population divided by land "
        "surface (km²).",
        "",
        "| Method | Variable | Natural cell (m) | Density | Cells | "
        "Positive reference | Mean absolute error | Median absolute "
        f"relative error | Within ±{within_tolerance_fraction:.0%} |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in metrics_200m:
        median = row["median_absolute_relative_error"]
        lines.append(
            "| {method} | {variable} | {size} | {density} | {cells} | "
            "{positive} | {mae:.3f} | {median} | {share:.1%} |".format(
                method=row["method"],
                variable=row["variable"],
                size=row["natural_cell_size_m"],
                density=row["density_class"],
                cells=_format_count(row["cell_count"], count_suppression_threshold),
                positive=_format_count(
                    row["positive_reference_count"], count_suppression_threshold
                ),
                mae=row["mean_absolute_error"],
                median=(
                    "NA"
                    if median is None
                    else f"{100 * float(median):.1f}%"
                ),
                share=row["share_within_tolerance"],
            )
        )
    lines.extend(
        [
            "",
            "## Eurostat 1 km cells wholly inside the department",
            "",
            "| Density | Cells | Downscaled individuals | Eurostat individuals | "
            "Positive reference | Median absolute relative error |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in metrics_1km:
        median = row["median_absolute_relative_error"]
        lines.append(
            "| {density} | {cells} | {downscaled} | {eurostat} | "
            "{positive} | {median} |".format(
                density=row["density_class"],
                cells=_format_count(row["cell_count"], count_suppression_threshold),
                downscaled=_format_total(
                    row["downscaled_individuals"], count_suppression_threshold
                ),
                eurostat=_format_total(
                    row["eurostat_individuals"], count_suppression_threshold
                ),
                positive=_format_count(
                    row["positive_reference_count"], count_suppression_threshold
                ),
                median=(
                    "NA"
                    if median is None
                    else f"{100 * float(median):.1f}%"
                ),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _extract_filosofi_200m(archive: Path, directory: Path) -> Path:
    """Extract the metropolitan 200 m CSV for section 6.5."""
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
            raise FileNotFoundError(
                f"metropolitan 200 m CSV is missing from {archive}"
            )
        target = directory / "filosofi_200m.csv"
        with zipped.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return target


def build_validation_report(
    *,
    config_path: str | Path = "config/origins.yaml",
    pilot_config_path: str | Path = "config/pilot.yaml",
) -> Path:
    """Write aggregate section-6.5 validation under the configured interim path."""
    config = load_origins_config(config_path)
    validation = config.validation
    downscale = config.downscale
    report = config.report
    output_directory = Path(report.output_directory)
    downscaled_path = output_directory / downscale.output_pattern.format(
        year=downscale.output_year
    )
    ff_cells_path = output_directory / report.ff_cells_pattern.format(
        vintage=downscale.ff_vintage
    )
    ff_metadata_path = output_directory / report.metadata_pattern.format(
        vintage=downscale.ff_vintage
    )
    for path in (downscaled_path, ff_cells_path, ff_metadata_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    metadata = json.loads(ff_metadata_path.read_text(encoding="utf-8"))
    if metadata.get("second_home_source") != "hybrid_2024":
        raise ValueError("validation requires adopted hybrid Fichiers fonciers")
    eurostat_path = Path(validation.eurostat_grid)
    if not eurostat_path.is_file():
        raise FileNotFoundError(eurostat_path)
    department = _pilot_department(pilot_config_path)
    report_path = output_directory / validation.report_pattern.format(
        year=downscale.output_year
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    connection = open_connection()
    try:
        _load_department_boundary(
            connection, Path(report.contours_2021), department
        )
        with tempfile.TemporaryDirectory(
            prefix="filosofi_validation_"
        ) as directory:
            insee_path = _extract_filosofi_200m(
                Path(config.filosofi_200m_archive), Path(directory)
            )
            metrics_200m, metrics_1km = calculate_validation_metrics(
                connection,
                downscaled_path,
                insee_path,
                ff_cells_path,
                eurostat_path,
                department=department,
                cell_resolution_m=downscale.cell_resolution_m,
                eurostat_resolution_m=validation.eurostat_resolution_m,
                density_thresholds_population_km2=(
                    validation.density_thresholds_population_km2
                ),
                within_tolerance_fraction=validation.within_tolerance_fraction,
            )
    finally:
        connection.close()

    content = render_validation_report(
        downscale.output_year,
        department,
        metrics_200m,
        metrics_1km,
        report.count_suppression_threshold,
        validation.within_tolerance_fraction,
    )
    temporary = report_path.with_suffix(".tmp.md")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(report_path)
    LOGGER.info("Wrote aggregate-only report to %s", report_path)
    return report_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run section-6.5 validation from configured interim products."""
    parser = argparse.ArgumentParser(
        description="Validate 2021 origins downscaling against INSEE and Eurostat"
    )
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    report_path = build_validation_report(
        config_path=args.config,
        pilot_config_path=args.pilot_config,
    )
    print(json.dumps({"report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
