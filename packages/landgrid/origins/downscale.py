"""Proportional Filosofi household and count downscaling for section 6.3."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
from common.duckdb_io import write_parquet

from landgrid.origins.fichiers_fonciers import (
    DownscaleConfig,
    _file_signature,
    _pilot_department,
    _quoted_identifier,
    load_origins_config,
)
from landgrid.origins.job import open_restricted_connection

_NUMERIC_TYPES = {
    "BIGINT",
    "BIGNUM",
    "DECIMAL",
    "DOUBLE",
    "FLOAT",
    "HUGEINT",
    "INTEGER",
    "REAL",
    "SMALLINT",
    "TINYINT",
    "UBIGINT",
    "UINTEGER",
    "USMALLINT",
    "UTINYINT",
}


def _sql_string(value: str) -> str:
    """Escape a filesystem path for a DuckDB relation expression."""
    return "'" + value.replace("'", "''") + "'"


def _relation(
    connection: duckdb.DuckDBPyConnection,
    name: str,
    source: pa.Table | Path,
) -> tuple[str, bool]:
    """Register an Arrow input or return a lazy DuckDB reader expression."""
    if isinstance(source, pa.Table):
        connection.register(name, source)
        return name, True
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(path)
    reader = "read_parquet" if path.suffix.casefold() == ".parquet" else "read_csv_auto"
    return f"{reader}({_sql_string(str(path.resolve()))})", False


def downscale_natural_cells(
    connection: duckdb.DuckDBPyConnection,
    natural: pa.Table | Path,
    ff_cells: pa.Table | Path,
    filosofi_200m: pa.Table | Path,
    natural_cell_ids: Sequence[str],
    resolution_m: int,
) -> dict[str, dict[str, int | float]]:
    """Apply section 6.3 weights, preserving each natural-cell control total."""
    if resolution_m <= 0:
        raise ValueError("cell resolution must be positive")
    if not natural_cell_ids:
        raise ValueError("at least one natural-level cell is required")
    if len(natural_cell_ids) != len(set(natural_cell_ids)):
        raise ValueError("natural-level scope contains duplicate cells")

    natural_relation, natural_registered = _relation(
        connection, "_downscale_natural_input", natural
    )
    ff_relation, ff_registered = _relation(
        connection, "_downscale_ff_input", ff_cells
    )
    filosofi_relation, filosofi_registered = _relation(
        connection, "_downscale_filosofi_200m_input", filosofi_200m
    )
    registered = [
        (name, flag)
        for name, flag in (
            ("_downscale_natural_input", natural_registered),
            ("_downscale_ff_input", ff_registered),
            ("_downscale_filosofi_200m_input", filosofi_registered),
        )
        if flag
    ]
    scope_table = pa.Table.from_pydict(
        {"natural_cell_id": list(natural_cell_ids)}
    )
    connection.register("_downscale_scope_input", scope_table)
    registered.append(("_downscale_scope_input", True))
    try:
        natural_columns = {
            str(row[0]): str(row[1]).upper().split("(", 1)[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {natural_relation}"
            ).fetchall()
        }
        required_natural = {"idcar_nat", "tmaille"}
        if not required_natural.issubset(natural_columns):
            raise ValueError("Filosofi natural file lacks idcar_nat or tmaille")
        variables = [
            name for name in natural_columns if name not in required_natural
        ]
        if not variables or "men" not in variables:
            raise ValueError("Filosofi natural file has no count variables or men")
        non_numeric = [
            name for name in variables if natural_columns[name] not in _NUMERIC_TYPES
        ]
        if non_numeric:
            raise ValueError(
                "Filosofi natural variables must all be numeric: "
                + ", ".join(sorted(non_numeric))
            )
        ff_columns = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {ff_relation}"
            ).fetchall()
        }
        if not {"cell_id", "main_residences", "dwellings"}.issubset(ff_columns):
            raise ValueError(
                "Fichiers fonciers cell file lacks cell_id, main_residences, "
                "or dwellings"
            )
        filosofi_columns = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {filosofi_relation}"
            ).fetchall()
        }
        if not {"idcar_200m", "men"}.issubset(filosofi_columns):
            raise ValueError("Filosofi 200 m file lacks idcar_200m or men")

        duplicates = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT idcar_nat
                FROM {natural_relation}
                GROUP BY idcar_nat
                HAVING count(*) > 1
            )
            """
        ).fetchone()[0]
        if duplicates:
            raise ValueError("Filosofi natural file has duplicate cell ids")
        duplicates = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT idcar_200m
                FROM {filosofi_relation}
                GROUP BY idcar_200m
                HAVING count(*) > 1
            )
            """
        ).fetchone()[0]
        if duplicates:
            raise ValueError("Filosofi 200 m file has duplicate cell ids")
        unknown_cells = connection.execute(
            f"""
            SELECT count(*)
            FROM _downscale_scope_input s
            LEFT JOIN {natural_relation} n
              ON n.idcar_nat = s.natural_cell_id
            WHERE n.idcar_nat IS NULL
            """
        ).fetchone()[0]
        if unknown_cells:
            raise ValueError("natural-level scope contains unknown Filosofi cells")
        missing_controls = " OR ".join(
            f"n.{_quoted_identifier(name)} IS NULL" for name in variables
        )
        invalid_controls = connection.execute(
            f"""
            SELECT count(*) FROM {natural_relation} n
            JOIN _downscale_scope_input s ON s.natural_cell_id = n.idcar_nat
            WHERE n.tmaille < {resolution_m}
                OR n.tmaille % {resolution_m} <> 0
                OR CAST(regexp_extract(
                    n.idcar_nat, 'RES([0-9]+)mN', 1
                ) AS BIGINT) <> n.tmaille
                OR n.idcar_nat IS NULL
                OR {missing_controls}
            """
        ).fetchone()[0]
        if invalid_controls:
            raise ValueError("Filosofi natural controls are invalid or incomplete")

        variable_fields = ",\n".join(
            f"CAST(n.{_quoted_identifier(name)} AS DOUBLE) "
            f"AS {_quoted_identifier(name)}"
            for name in variables
        )
        output_variables = ",\n".join(
            (
                f"CASE WHEN natural_cell_size_m = {resolution_m} "
                f"THEN {_quoted_identifier(name)} "
                f"WHEN weight_sum > 0 THEN {_quoted_identifier(name)} "
                f"* selected_weight / weight_sum ELSE 0.0 END "
                f"AS {_quoted_identifier(name)}"
            )
            for name in variables
        )
        control_checks = " OR ".join(
            f"abs(sum(d.{_quoted_identifier(name)}) - "
            f"max(n.{_quoted_identifier(name)})) > "
            f"1e-9 * greatest(1.0, abs(max(n.{_quoted_identifier(name)})))"
            for name in variables
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _downscale_weighted AS
            WITH natural_scope AS (
                SELECT n.idcar_nat AS natural_cell_id,
                    CAST(n.tmaille AS BIGINT) AS natural_cell_size_m,
                    CAST(regexp_extract(
                        n.idcar_nat, 'mN([0-9]+)E', 1
                    ) AS BIGINT) AS base_northing_m,
                    CAST(regexp_extract(
                        n.idcar_nat, 'E([0-9]+)$', 1
                    ) AS BIGINT) AS base_easting_m,
                    {variable_fields}
                FROM {natural_relation} n
                JOIN _downscale_scope_input s
                  ON s.natural_cell_id = n.idcar_nat
            ),
            grid_cells AS (
                SELECT n.*,
                    n.base_northing_m + CAST(north.offset_n AS BIGINT)
                        AS northing_m,
                    n.base_easting_m + CAST(east.offset_e AS BIGINT)
                        AS easting_m
                FROM natural_scope n
                CROSS JOIN LATERAL range(
                    0, n.natural_cell_size_m, {resolution_m}
                ) AS north(offset_n)
                CROSS JOIN LATERAL range(
                    0, n.natural_cell_size_m, {resolution_m}
                ) AS east(offset_e)
            ),
            identified_cells AS (
                SELECT *,
                    CAST(floor(northing_m / {resolution_m}) * 100000
                        + floor(easting_m / {resolution_m}) AS BIGINT)
                        AS cell_id,
                    'CRS3035RES{resolution_m}mN'
                        || CAST(northing_m AS VARCHAR)
                        || 'E' || CAST(easting_m AS VARCHAR) AS cell_code
                FROM grid_cells
            ),
            ff_weights AS (
                SELECT cell_id, sum(main_residences) AS main_weight,
                    sum(dwellings) AS dwelling_weight
                FROM {ff_relation}
                GROUP BY cell_id
            ),
            filosofi_weights AS (
                SELECT idcar_200m, sum(men) AS household_weight
                FROM {filosofi_relation}
                GROUP BY idcar_200m
            ),
            cell_weights AS (
                SELECT g.*,
                    coalesce(ff.main_weight, 0) AS main_weight,
                    coalesce(ff.dwelling_weight, 0) AS dwelling_weight,
                    coalesce(f.household_weight, 0) AS household_weight
                FROM identified_cells g
                LEFT JOIN ff_weights ff USING (cell_id)
                LEFT JOIN filosofi_weights f
                  ON f.idcar_200m = g.cell_code
            ),
            natural_weights AS (
                SELECT *,
                    sum(main_weight) OVER (
                        PARTITION BY natural_cell_id
                    ) AS main_weight_sum,
                    sum(dwelling_weight) OVER (
                        PARTITION BY natural_cell_id
                    ) AS dwelling_weight_sum,
                    sum(household_weight) OVER (
                        PARTITION BY natural_cell_id
                    ) AS household_weight_sum
                FROM cell_weights
            ),
            selected_weights AS (
                SELECT *,
                    CASE
                        WHEN natural_cell_size_m = {resolution_m}
                            THEN 'natural_200m'
                        WHEN main_weight_sum > 0 THEN 'main_residences'
                        WHEN dwelling_weight_sum > 0 THEN 'dwellings'
                        ELSE 'filosofi_households'
                    END AS fallback_used,
                    CASE
                        WHEN main_weight_sum > 0 THEN main_weight
                        WHEN dwelling_weight_sum > 0 THEN dwelling_weight
                        ELSE household_weight
                    END AS selected_weight
                FROM natural_weights
            ),
            normalized_weights AS (
                SELECT *,
                    sum(selected_weight) OVER (
                        PARTITION BY natural_cell_id
                    ) AS weight_sum
                FROM selected_weights
            )
            SELECT * FROM normalized_weights
            """
        )

        empty_weights = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT natural_cell_id
                FROM _downscale_weighted
                WHERE natural_cell_size_m > {resolution_m}
                GROUP BY natural_cell_id
                HAVING max(weight_sum) = 0
                    AND ({" OR ".join(
                        f"max(abs({_quoted_identifier(name)})) > 0"
                        for name in variables
                    )})
            )
            """
        ).fetchone()[0]
        if empty_weights:
            raise ValueError(
                "non-zero Filosofi controls have no positive fallback weights"
            )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _downscaled_origins AS
            SELECT cell_id, natural_cell_id, natural_cell_size_m,
                {output_variables},
                fallback_used
            FROM _downscale_weighted
            """
        )
        mismatched_totals = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT d.natural_cell_id
                FROM _downscaled_origins d
                JOIN {natural_relation} n
                  ON n.idcar_nat = d.natural_cell_id
                GROUP BY d.natural_cell_id
                HAVING {control_checks}
            )
            """
        ).fetchone()[0]
        if mismatched_totals:
            raise RuntimeError(
                "downscaled Filosofi totals do not match natural-cell controls"
            )
        return {
            str(row[0]): {
                "cells": int(row[1]),
                "households": float(row[2] or 0.0),
            }
            for row in connection.execute(
                """
                SELECT fallback_used, count(*), sum(men)
                FROM _downscaled_origins
                GROUP BY fallback_used
                ORDER BY fallback_used
                """
            ).fetchall()
        }
    finally:
        for name, was_registered in reversed(registered):
            if was_registered:
                connection.unregister(name)


def _extract_archive_member(
    archive_path: Path,
    suffix: str,
    directory: Path,
) -> Path:
    """Stream one configured Filosofi CSV member into a temporary directory."""
    with zipfile.ZipFile(archive_path) as archive:
        member = next(
            (name for name in archive.namelist() if name.endswith(suffix)),
            None,
        )
        if member is None:
            raise FileNotFoundError(f"{suffix} is missing from {archive_path}")
        target = directory / Path(suffix).name
        with archive.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return target


def build_origins_2021_200m(
    *,
    config_path: str | Path = "config/origins.yaml",
    pilot_config_path: str | Path = "config/pilot.yaml",
    output_directory: str | Path | None = None,
) -> dict[str, Any]:
    """Build 2021 origins from Filosofi 2021 and hybrid FF 2022 in interim."""
    config = load_origins_config(config_path)
    downscale: DownscaleConfig = config.downscale
    output_dir = Path(output_directory or config.report.output_directory)
    ff_cells_path = output_dir / config.report.ff_cells_pattern.format(
        vintage=downscale.ff_vintage
    )
    ff_metadata_path = output_dir / config.report.metadata_pattern.format(
        vintage=downscale.ff_vintage
    )
    if not ff_cells_path.is_file() or not ff_metadata_path.is_file():
        raise FileNotFoundError(
            f"missing FF {downscale.ff_vintage} hybrid build under {output_dir}"
        )
    metadata = json.loads(ff_metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or metadata.get(
        "second_home_source"
    ) != "hybrid_2024":
        raise ValueError(
            f"FF {downscale.ff_vintage} inputs must use the adopted hybrid rule"
        )
    natural_archive = Path(config.filosofi_natural_archive)
    households_archive = Path(config.filosofi_200m_archive)
    if not natural_archive.is_file():
        raise FileNotFoundError(natural_archive)
    if not households_archive.is_file():
        raise FileNotFoundError(households_archive)
    output_path = output_dir / downscale.output_pattern.format(
        year=downscale.output_year
    )
    metadata_path = output_dir / downscale.metadata_pattern.format(
        year=downscale.output_year
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path.unlink(missing_ok=True)

    connection, spill = open_restricted_connection(output_dir)
    try:
        with tempfile.TemporaryDirectory(
            prefix="filosofi_downscale_", dir=output_dir
        ) as folder:
            directory = Path(folder)
            natural_csv = _extract_archive_member(
                natural_archive, "carreaux_nivNaturel_met.csv", directory
            )
            filosofi_200m_csv = _extract_archive_member(
                households_archive, "carreaux_200m_met.csv", directory
            )
            pilot_department = _pilot_department(pilot_config_path)
            natural_cell_ids = [
                str(row[0])
                for row in connection.execute(
                    """
                    SELECT DISTINCT idcar_nat
                    FROM read_csv_auto(?, header=true)
                    WHERE idcar_nat IS NOT NULL AND EXISTS (
                        SELECT 1
                        FROM UNNEST(string_split(
                            CAST(lcog_geo AS VARCHAR), ','
                        )) AS commune(code)
                        WHERE left(trim(commune.code), length(?)) = ?
                    )
                    ORDER BY idcar_nat
                    """,
                    [str(filosofi_200m_csv), pilot_department, pilot_department],
                ).fetchall()
            ]
            if not natural_cell_ids:
                raise ValueError(
                    f"Filosofi 200 m grid does not reach department "
                    f"{pilot_department}"
                )
            fallback_summary = downscale_natural_cells(
                connection,
                natural_csv,
                ff_cells_path,
                filosofi_200m_csv,
                natural_cell_ids,
                downscale.cell_resolution_m,
            )
            temporary = output_path.with_suffix(".tmp.parquet")
            write_parquet(
                connection, "SELECT * FROM _downscaled_origins", temporary
            )
            temporary.replace(output_path)
        metadata_path.with_suffix(".tmp.json").write_text(
            json.dumps(
                {
                    "output_year": downscale.output_year,
                    "fichiers_fonciers_vintage": downscale.ff_vintage,
                    "second_home_source": metadata["second_home_source"],
                    "ff_signature": metadata["signature"],
                    "pilot_signature": _file_signature(Path(pilot_config_path)),
                    "natural_cell_count": len(natural_cell_ids),
                    "fallback_summary": fallback_summary,
                    "output": str(output_path),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        metadata_path.with_suffix(".tmp.json").replace(metadata_path)
        return {
            "output": str(output_path),
            "metadata": str(metadata_path),
            "natural_cell_count": len(natural_cell_ids),
            "fallback_summary": fallback_summary,
        }
    finally:
        connection.close()
        spill.cleanup()


def _suppressed_summary(
    summary: dict[str, dict[str, int | float]],
    threshold: int,
) -> dict[str, dict[str, int | float | str]]:
    """Suppress fallback cell and household counts below the configured limit."""
    return {
        method: {
            metric: (
                f"<{threshold}"
                if abs(float(value)) < threshold
                else value
            )
            for metric, value in counts.items()
        }
        for method, counts in summary.items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run section-6.3 2021 household downscaling."""
    parser = argparse.ArgumentParser(
        description="Downscale 2021 Filosofi counts to 200 m cells"
    )
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = build_origins_2021_200m(
        config_path=args.config,
        pilot_config_path=args.pilot_config,
        output_directory=args.output,
    )
    threshold = load_origins_config(args.config).report.count_suppression_threshold
    result["fallback_summary"] = _suppressed_summary(
        result["fallback_summary"], threshold
    )
    if result["natural_cell_count"] < threshold:
        result["natural_cell_count"] = f"<{threshold}"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
