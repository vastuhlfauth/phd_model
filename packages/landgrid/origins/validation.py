"""Section 6.5 validation for the 2021 Filosofi downscaling."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import shutil
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa

from landgrid.origins.fichiers_fonciers import (
    _file_signature,
    _pilot_department,
    load_origins_config,
)
from landgrid.origins.job import open_restricted_connection
from landgrid.origins.report import _load_department_boundary

LOGGER = logging.getLogger(__name__)

COMPOSITION_VALIDATION_VARIABLES = (
    "men_1ind", "men_5ind", "men_prop", "men_mais", "log_soc", "ind_snv",
)


def grouped_folds(
    groups: npt.NDArray, *, folds: int, seed: int
) -> npt.NDArray[np.int64]:
    """Assign each natural cell to one reproducible validation fold (6.5)."""
    if groups.ndim != 1 or folds < 2:
        raise ValueError("invalid natural cells or number of folds")
    unique, inverse = np.unique(groups, return_inverse=True)
    if len(unique) < folds:
        raise ValueError("not enough natural cells for grouped folds")
    assignment = np.empty(len(unique), dtype=np.int64)
    assignment[np.random.default_rng(seed).permutation(len(unique))] = (
        np.arange(len(unique)) % folds
    )
    return assignment[inverse]


def choose_methods(
    medians: dict[str, dict[str, float | None]], *, tolerance: float
) -> dict[str, str]:
    """Choose from pooled relative-error medians using a fraction tolerance (6.5)."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("invalid median tolerance")
    priority = ("proportional", "composition", "within")
    choices = {}
    for variable, scores in medians.items():
        if set(scores) != set(priority) or any(
            value is None or not math.isfinite(value) or value < 0
            for value in scores.values()
        ):
            raise ValueError(f"invalid or unavailable median for {variable}")
        best = min(float(value) for value in scores.values() if value is not None)
        choices[variable] = next(
            method for method in priority
            if float(scores[method]) - best <= tolerance
            or math.isclose(float(scores[method]) - best, tolerance, abs_tol=1e-12)
        )
    return choices


def pooled_method_medians(
    connection: duckdb.DuckDBPyConnection, observations: pa.Table | Path | str
) -> dict[str, dict[str, float | None]]:
    """Pool held-out 200 m relative errors across folds and strata (6.5)."""
    if isinstance(observations, str):
        if not observations.isascii() or not observations.isidentifier():
            raise ValueError("invalid DuckDB observations relation")
        relation, registered = (
            '"' + observations.replace('"', '""') + '"',
            False,
        )
    else:
        relation, registered = _source_relation(
            connection, "_pooled_observations_input", observations
        )
    try:
        invalid = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT variable, cell_id
                FROM {relation}
                GROUP BY variable, cell_id
                HAVING count(*) != 3 OR count(DISTINCT method) != 3
                    OR count(*) FILTER (
                        WHERE method NOT IN ('proportional', 'composition', 'within')
                            OR method IS NULL OR predicted IS NULL
                            OR NOT isfinite(predicted) OR predicted < 0
                            OR reference IS NULL OR NOT isfinite(reference)
                            OR reference < 0
                    ) > 0
                    OR min(reference) != max(reference)
                    OR variable IS NULL OR cell_id IS NULL
            )
            """
        ).fetchone()[0]
        empty = connection.execute(
            f"SELECT count(*) FROM {relation}"
        ).fetchone()[0] == 0
        if invalid or empty:
            raise ValueError("methods must score the same valid held-out observations")
        rows = connection.execute(
            f"""
            SELECT variable, method,
                quantile_cont(abs(predicted - reference) / NULLIF(reference, 0), 0.5)
            FROM {relation}
            GROUP BY variable, method
            ORDER BY variable, method
            """
        ).fetchall()
        result: dict[str, dict[str, float | None]] = {}
        for variable, method, median in rows:
            result.setdefault(variable, {})[method] = median
        return result
    finally:
        if registered:
            connection.unregister("_pooled_observations_input")


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
    composition: pa.Table | Path | None = None,
    department: str,
    cell_resolution_m: int,
    eurostat_resolution_m: int,
    density_thresholds_population_km2: tuple[int, int],
    within_tolerance_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
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
        composition_relation = None
        if composition is not None:
            composition_relation, was_registered = _source_relation(
                connection, "_validation_composition_input", composition
            )
            if was_registered:
                registered.append("_validation_composition_input")
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

        if composition_relation is not None:
            additional = set(COMPOSITION_VALIDATION_VARIABLES)
            for relation in (downscaled_relation, insee_relation, composition_relation):
                missing = additional - _columns(connection, relation)
                if missing:
                    raise ValueError(
                        "composition validation input lacks columns: "
                        + ", ".join(sorted(missing))
                    )
            missing_eurostat = {"Y_LT15", "Y_GE65"} - _columns(
                connection, eurostat_relation
            )
            if missing_eurostat:
                raise ValueError(
                    "Eurostat input lacks age columns: "
                    + ", ".join(sorted(missing_eurostat))
                )
            mismatch = connection.execute(
                f"""
                SELECT count(*) FROM {downscaled_relation} d
                FULL JOIN {composition_relation} c USING (cell_id)
                WHERE d.cell_id IS NULL OR c.cell_id IS NULL
                    OR d.natural_cell_id IS DISTINCT FROM c.natural_cell_id
                    OR d.natural_cell_size_m IS DISTINCT FROM c.natural_cell_size_m
                """
            ).fetchone()[0]
            if mismatch:
                raise ValueError("composition and benchmark cell scopes differ")
            for relation in (downscaled_relation, composition_relation):
                duplicates = connection.execute(
                    f"SELECT count(*) FROM (SELECT cell_id FROM {relation} "
                    "GROUP BY cell_id HAVING count(*) > 1)"
                ).fetchone()[0]
                if duplicates:
                    raise ValueError("composition validation has duplicate cell ids")

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
                WHEN T IS NULL OR T < 0 THEN 'population unavailable'
                WHEN CAST(T AS DOUBLE) / CASE
                    WHEN LAND_SURFACE > 0 THEN LAND_SURFACE
                    ELSE pow({eurostat_resolution_m} / 1000.0, 2)
                END
                    < {density_thresholds_population_km2[0]}
                    THEN '{first_density_label}'
                WHEN CAST(T AS DOUBLE) / CASE
                    WHEN LAND_SURFACE > 0 THEN LAND_SURFACE
                    ELSE pow({eurostat_resolution_m} / 1000.0, 2)
                END
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
                {("CAST(Y_LT15 AS DOUBLE) AS under_15, "
                  "CAST(Y_GE65 AS DOUBLE) AS age_65_plus,")
                 if composition_relation is not None else ""}
                {density_expression} AS density_class
            FROM {eurostat_relation}
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
        extra_natural = "".join(
            f", sum({name}) AS {name}" for name in COMPOSITION_VALIDATION_VARIABLES
        ) if composition_relation is not None else ""
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_natural_totals AS
            SELECT natural_cell_id,
                sum(ind) AS individuals,
                sum(men) AS households,
                sum(ind_0_3 + ind_4_5 + ind_6_10) AS under_11,
                sum(ind_0_3 + ind_4_5 + ind_6_10 + ind_11_17) AS under_18,
                sum(ind_65_79 + ind_80p) AS age_65_plus {extra_natural}
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
        extra_select = ""
        composition_join = ""
        if composition_relation is not None:
            extra_select = ", " + ", ".join(
                f"d.{name} AS predicted_{name}, i.{name} AS reference_{name}, "
                f"n.{name} AS natural_{name}, c.{name} AS composition_{name}"
                for name in COMPOSITION_VALIDATION_VARIABLES
            )
            extra_select += (
                ", c.ind AS composition_individuals, "
                "c.men AS composition_households, "
                "c.ind_0_3 + c.ind_4_5 + c.ind_6_10 + c.ind_11_17 "
                "AS composition_under_18, "
                "c.ind_65_79 + c.ind_80p AS composition_age_65_plus"
            )
            composition_join = (
                f"JOIN {composition_relation} c ON c.cell_id = d.cell_id"
            )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _validation_200m AS
            SELECT i.idcar_200m, d.natural_cell_id,
                d.natural_cell_size_m,
                coalesce(e.density_class, 'unmatched') AS density_class,
                e.GRD_ID AS eurostat_grid_id, e.population, e.land_surface,
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
                m.occupied_cell_count {extra_select}
            FROM {insee_relation} i
            JOIN _validation_downscaled d
              ON d.cell_code = i.idcar_200m
            LEFT JOIN _validation_eurostat e ON e.GRD_ID = i.idcar_1km
            JOIN _validation_natural_totals n
              ON n.natural_cell_id = d.natural_cell_id
            JOIN _validation_main_cells m
              ON m.natural_cell_id = d.natural_cell_id
            {composition_join}
            LEFT JOIN _validation_ff f ON f.cell_id = d.cell_id
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
        reason_row = connection.execute(
            """
            SELECT
                count(*) FILTER (WHERE eurostat_grid_id IS NULL),
                count(*) FILTER (
                    WHERE eurostat_grid_id IS NOT NULL
                    AND (population IS NULL OR population < 0)
                ),
                count(*) FILTER (
                    WHERE eurostat_grid_id IS NOT NULL AND land_surface IS NULL
                ),
                count(*) FILTER (
                    WHERE eurostat_grid_id IS NOT NULL AND land_surface = 0
                ),
                count(*) FILTER (
                    WHERE eurostat_grid_id IS NOT NULL AND land_surface < 0
                )
            FROM _validation_200m
            """
        ).fetchone()
        reasons = dict(zip(
            (
                "no_match",
                "population_unavailable",
                "land_surface_null",
                "land_surface_zero",
                "land_surface_negative",
            ),
            reason_row,
            strict=True,
        ))

        value_rows = []
        variable_fields = [
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
        ]
        if composition_relation is not None:
            variable_fields.extend(
                (name, f"predicted_{name}", f"reference_{name}", f"natural_{name}")
                for name in COMPOSITION_VALIDATION_VARIABLES
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
            if composition_relation is not None:
                value_rows.append(
                    f"""SELECT 'composition' AS method, '{variable}' AS variable,
                        natural_cell_size_m, density_class,
                        composition_{variable} AS predicted,
                        {reference} AS reference
                    FROM _validation_200m"""
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
                    count(*) FILTER (WHERE reference > 0)
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
            WHERE e.population >= 0
                AND regexp_matches(
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
                    count(*) FILTER (WHERE population > 0)
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
        if composition_relation is not None:
            metrics_1km = _composition_eurostat_metrics(
                connection, composition_relation, eurostat_resolution_m
            )
        if not metrics_200m:
            raise ValueError("section-6.5 INSEE validation scope is empty")
        return metrics_200m, metrics_1km, reasons
    finally:
        for name in registered:
            connection.unregister(name)


def _composition_eurostat_metrics(
    connection: duckdb.DuckDBPyConnection,
    composition_relation: str,
    resolution_m: int,
) -> list[dict[str, Any]]:
    """Compare complete 1 km cells with Eurostat population and age totals."""
    grid_id = (
        f"'CRS3035RES{resolution_m}mN' || "
        f"CAST(CAST(floor(d.northing_m / {resolution_m}) * {resolution_m} "
        f"AS BIGINT) AS VARCHAR) || 'E' || "
        f"CAST(CAST(floor(d.easting_m / {resolution_m}) * {resolution_m} "
        f"AS BIGINT) AS VARCHAR)"
    )
    expressions = {
        "individuals": "ind",
        "under_11_ratio": "ind_0_3 + {alias}.ind_4_5 + {alias}.ind_6_10",
        "under_18_ratio": (
            "ind_0_3 + {alias}.ind_4_5 + {alias}.ind_6_10 + {alias}.ind_11_17"
        ),
        "age_65_plus": "ind_65_79 + {alias}.ind_80p",
    }
    natural_names = {
        "individuals": "individuals",
        "under_11_ratio": "under_11",
        "under_18_ratio": "under_18",
        "age_65_plus": "age_65_plus",
    }
    queries = []
    for method, alias in (("proportional", "d"), ("composition", "c")):
        fields = ", ".join(
            f"sum({alias}.{expression.format(alias=alias)}) AS {name}"
            for name, expression in expressions.items()
        )
        queries.append(
            f"""
            SELECT '{method}' AS method, {grid_id} AS grid_id, {fields}
            FROM _validation_downscaled d
            JOIN {composition_relation} c USING (cell_id)
            GROUP BY grid_id
            """
        )
    equal_fields = ", ".join(
        "sum(CASE WHEN coalesce(f.main_residences, 0) > 0 "
        f"AND m.occupied_cell_count > 0 THEN n.{natural_name} "
        f"/ m.occupied_cell_count ELSE 0.0 END) AS {name}"
        for name, natural_name in natural_names.items()
    )
    queries.append(
        f"""
        SELECT 'equal_split' AS method, {grid_id} AS grid_id, {equal_fields}
        FROM _validation_downscaled d
        LEFT JOIN _validation_ff f USING (cell_id)
        JOIN _validation_natural_totals n USING (natural_cell_id)
        JOIN _validation_main_cells m USING (natural_cell_id)
        GROUP BY grid_id
        """
    )
    union = "\nUNION ALL\n".join(queries)
    return connection.execute(
        f"""
        WITH predictions AS ({union}),
        values_by_variable AS (
            SELECT methods.method, e.density_class, v.variable, v.predicted, v.reference
            FROM _validation_1km valid
            JOIN _validation_eurostat e ON e.GRD_ID = valid.GRD_ID
            CROSS JOIN (
                SELECT 'proportional' AS method UNION ALL
                SELECT 'composition' UNION ALL SELECT 'equal_split'
            ) methods
            LEFT JOIN predictions p
              ON p.grid_id = e.GRD_ID AND p.method = methods.method
            CROSS JOIN LATERAL (VALUES
                ('individuals', coalesce(p.individuals, 0), e.population),
                ('age_65_plus', coalesce(p.age_65_plus, 0), e.age_65_plus),
                ('under_11_ratio', coalesce(p.under_11_ratio, 0), e.under_15),
                ('under_18_ratio', coalesce(p.under_18_ratio, 0), e.under_15)
            ) AS v(variable, predicted, reference)
            WHERE v.reference IS NOT NULL AND v.reference >= 0
        )
        SELECT method, variable, density_class, count(*) AS cell_count,
            sum(predicted) AS downscaled_total, sum(reference) AS reference_total,
            count(*) FILTER (WHERE reference > 0) AS positive_reference_count,
            sum(predicted) / nullif(sum(reference), 0) AS ratio,
            CASE WHEN variable LIKE '%_ratio' THEN NULL ELSE
                quantile_cont(abs(predicted - reference) / nullif(reference, 0), 0.5)
            END AS median_absolute_relative_error
        FROM values_by_variable
        GROUP BY method, variable, density_class
        ORDER BY method, variable, density_class
        """
    ).to_arrow_table().to_pylist()


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
    eurostat_reasons: dict[str, int],
    count_suppression_threshold: int,
    within_tolerance_fraction: float,
    *,
    methods: dict[str, str] | None = None,
    crossval_report: str = "",
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
        "as within range. Density uses Eurostat population divided by "
        "LAND_SURFACE when positive, otherwise 1 km². A missing Eurostat row "
        "is unmatched; a null or negative population is population unavailable.",
        "Within-model INSEE rows are in-sample; held-out errors are in "
        f"[{crossval_report}]({crossval_report})." if crossval_report else "",
        "",
        "Eurostat input issues among the 200 m validation cells "
        "(reasons can overlap; unmatched cells are not counted as null fields):",
        "",
        "| Reason | 200 m cells |",
        "|---|---:|",
        *[
            f"| {reason} | {_format_count(count, count_suppression_threshold)} |"
            for reason, count in eurostat_reasons.items()
        ],
        "",
        "| Method | Variable | Natural cell (m) | Density | Cells | "
        "Positive reference | Mean absolute error | Median absolute "
        f"relative error | Within ±{within_tolerance_fraction:.0%} |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in metrics_200m:
        median = row["median_absolute_relative_error"]
        method = row["method"]
        if method == "composition" and methods is not None:
            components = {
                "individuals": ("ind",),
                "under_18": ("ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17"),
                "age_65_plus": ("ind_65_79", "ind_80p"),
            }.get(row["variable"], (row["variable"],))
            selected = {methods[name] for name in components if name in methods}
            age_variables = {
                "ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17", "ind_18_24",
                "ind_25_39", "ind_40_54", "ind_55_64", "ind_65_79", "ind_80p",
                "ind_inc",
            }
            if age_variables.intersection(components) and any(
                methods.get(name) == "within" for name in (*age_variables, "ind")
            ):
                selected.add("within")
            if selected == {"within"}:
                method = "within (in-sample)"
            elif "within" in selected:
                method = "mixed (includes within; in-sample)"
            elif len(selected) == 1:
                method = next(iter(selected))
        lines.append(
            "| {method} | {variable} | {size} | {density} | {cells} | "
            "{positive} | {mae:.3f} | {median} | {share:.1%} |".format(
                method=method,
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
    if metrics_1km and "method" in metrics_1km[0]:
        lines.extend([
            "",
            "## Eurostat 1 km cells wholly inside the department",
            "",
            "Eurostat comparisons are independent. Age 65 and over is compared "
            "directly. Under-11 "
            "(ind_0_3 + ind_4_5 + ind_6_10) and under-18 "
            "(those groups plus ind_11_17) divided by Eurostat under-15 "
            "are information only, not errors.",
            "",
            "| Method | Variable | Density | Cells | Prediction | Reference | "
            "Ratio | Median absolute relative error |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ])
        for row in metrics_1km:
            median = row["median_absolute_relative_error"]
            ratio = row["ratio"]
            lines.append(
                "| {method} | {variable} | {density} | {cells} | {predicted} | "
                "{reference} | {ratio} | {median} |".format(
                    method=row["method"], variable=row["variable"],
                    density=row["density_class"],
                    cells=_format_count(row["cell_count"], count_suppression_threshold),
                    predicted=_format_total(
                        row["downscaled_total"], count_suppression_threshold
                    ),
                    reference=_format_total(
                        row["reference_total"], count_suppression_threshold
                    ),
                    ratio="NA" if ratio is None else f"{ratio:.3f}",
                    median="NA" if median is None else f"{100 * float(median):.1f}%",
                )
            )
        lines.append("")
        return "\n".join(lines)
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
    if not metrics_1km:
        lines.append(
            "| No Eurostat cells with valid population in the department "
            "| — | — | — | — | — |"
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
    composition_path = output_directory / downscale.composition_output_pattern.format(
        year=downscale.output_year
    )
    composition_metadata_path = output_directory / (
        downscale.composition_metadata_pattern.format(year=downscale.output_year)
    )
    composition_model_path = output_directory / (
        downscale.composition_model_pattern.format(year=downscale.output_year)
    )
    ff_cells_path = output_directory / report.ff_cells_pattern.format(
        vintage=downscale.ff_vintage
    )
    ff_natural_path = output_directory / report.ff_natural_pattern.format(
        vintage=downscale.ff_vintage
    )
    ff_metadata_path = output_directory / report.metadata_pattern.format(
        vintage=downscale.ff_vintage
    )
    for path in (
        downscaled_path, composition_path, composition_metadata_path,
        composition_model_path,
        ff_cells_path, ff_natural_path, ff_metadata_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    metadata = json.loads(ff_metadata_path.read_text(encoding="utf-8"))
    if metadata.get("second_home_source") != "hybrid_2024":
        raise ValueError("validation requires adopted hybrid Fichiers fonciers")
    composition_metadata = json.loads(
        composition_metadata_path.read_text(encoding="utf-8")
    )
    from landgrid.origins.composition import (
        composition_input_signature,
        load_method_choices,
    )

    choice_path = output_directory / downscale.crossval_choice_pattern.format(
        year=downscale.output_year
    )
    choices = load_method_choices(choice_path, downscale)
    reference_archive = (
        Path(config.filosofi_200m_archive) if "within" in choices.values() else None
    )

    expected_signature = composition_input_signature((
        Path(config_path), Path(pilot_config_path),
        Path(config.filosofi_natural_archive),
        ff_cells_path, ff_natural_path, ff_metadata_path, downscaled_path,
    ), choice_path=choice_path, reference_archive=reference_archive)
    if (
        not composition_metadata.get("completed")
        or composition_metadata.get("ff_signature") != metadata.get("signature")
        or composition_metadata.get("signature") != expected_signature
    ):
        raise ValueError("composition output is incomplete or stale")
    eurostat_path = Path(validation.eurostat_grid)
    if not eurostat_path.is_file():
        raise FileNotFoundError(eurostat_path)
    department = _pilot_department(pilot_config_path)
    report_path = output_directory / validation.report_pattern.format(
        year=downscale.output_year
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_directory / validation.checkpoint_pattern.format(
        year=downscale.output_year
    )
    signature = hashlib.sha256(json.dumps({
        "version": 1,
        "inputs": [
            _file_signature(path) for path in (
                Path(config_path), Path(pilot_config_path), downscaled_path,
                composition_path, composition_metadata_path, ff_cells_path,
                ff_metadata_path, eurostat_path, Path(config.filosofi_200m_archive),
                Path(report.contours_2021),
            )
        ],
    }, sort_keys=True).encode("utf-8")).hexdigest()
    checkpoint = {}
    if checkpoint_path.is_file():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("signature") == signature:
        metrics_200m = checkpoint["metrics_200m"]
        metrics_1km = checkpoint["metrics_1km"]
        eurostat_reasons = checkpoint["eurostat_reasons"]
    else:
        connection, spill = open_restricted_connection(output_directory)
        try:
            _load_department_boundary(
                connection, Path(report.contours_2021), department
            )
            with tempfile.TemporaryDirectory(
                prefix="filosofi_validation_", dir=output_directory
            ) as directory:
                insee_path = _extract_filosofi_200m(
                    Path(config.filosofi_200m_archive), Path(directory)
                )
                metrics_200m, metrics_1km, eurostat_reasons = (
                    calculate_validation_metrics(
                        connection,
                        downscaled_path,
                        insee_path,
                        ff_cells_path,
                        eurostat_path,
                        composition=composition_path,
                        department=department,
                        cell_resolution_m=downscale.cell_resolution_m,
                        eurostat_resolution_m=validation.eurostat_resolution_m,
                        density_thresholds_population_km2=(
                            validation.density_thresholds_population_km2
                        ),
                        within_tolerance_fraction=validation.within_tolerance_fraction,
                    )
                )
        finally:
            connection.close()
            spill.cleanup()
        temporary_checkpoint = checkpoint_path.with_suffix(".tmp.json")
        temporary_checkpoint.write_text(json.dumps({
            "signature": signature, "metrics_200m": metrics_200m,
            "metrics_1km": metrics_1km, "eurostat_reasons": eurostat_reasons,
        }, indent=2, sort_keys=True), encoding="utf-8")
        temporary_checkpoint.replace(checkpoint_path)

    content = render_validation_report(
        downscale.output_year,
        department,
        metrics_200m,
        metrics_1km,
        eurostat_reasons,
        report.count_suppression_threshold,
        validation.within_tolerance_fraction,
        methods={
            name: details["method"]
            for name, details in json.loads(
                composition_model_path.read_text(encoding="utf-8")
            ).items()
        },
        crossval_report=downscale.crossval_report_pattern.format(
            year=downscale.output_year
        ),
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
    from landgrid.origins.job import logged_job

    config = load_origins_config(args.config)
    with logged_job(
        Path(config.jobs.log_directory), config.jobs.validation_task,
        [
            config.filosofi_200m_archive, config.validation.eurostat_grid,
            config.report.output_directory,
        ],
        config.report.count_suppression_threshold,
    ) as job:
        report_path = build_validation_report(
            config_path=args.config,
            pilot_config_path=args.pilot_config,
        )
        job.outputs.append(str(report_path))
    print(json.dumps({"report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
