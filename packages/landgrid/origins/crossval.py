"""Grouped cross-validation for experimental 2021 origins downscaling."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
from common.duckdb_io import write_parquet

from landgrid.origins.composition import (
    AGE_VARIABLES,
    COVARIATES,
    DIRECT_WEIGHTS,
    apply_direct_weights,
    apply_regression_weights,
    balance_age_groups,
    fit_poisson,
    fit_within_poisson,
)
from landgrid.origins.downscale import (
    _extract_archive_member,
    _relation,
)
from landgrid.origins.fichiers_fonciers import (
    _file_signature,
    _pilot_department,
    _quoted_identifier,
    load_origins_config,
)
from landgrid.origins.job import logged_job, open_restricted_connection
from landgrid.origins.validation import (
    _extract_filosofi_200m,
    _format_count,
    _source_relation,
    choose_methods,
    grouped_folds,
    pooled_method_medians,
)

LOGGER = logging.getLogger(__name__)
METHODS = ("proportional", "composition", "within")
HOUSEHOLD_VARIABLES = ("men_1ind", "men_5ind", "men_fmp", "men_pauv")


@dataclass(frozen=True)
class FoldPartition:
    """Natural-level cell groups assigned to one training/holdout fold."""

    fold: int
    training_groups: tuple[str, ...]
    held_out_groups: tuple[str, ...]


def grouped_fold_partitions(
    natural_cell_ids: npt.NDArray,
    *,
    folds: int,
    seed: int,
) -> tuple[FoldPartition, ...]:
    """Partition natural-level ids without splitting a group (section 6.5)."""
    if natural_cell_ids.ndim != 1:
        raise ValueError("natural cell ids must be a one-dimensional array")
    unique = np.unique(natural_cell_ids.astype(str))
    assignments = grouped_folds(unique, folds=folds, seed=seed)
    return tuple(
        FoldPartition(
            fold=fold,
            training_groups=tuple(unique[assignments != fold].tolist()),
            held_out_groups=tuple(unique[assignments == fold].tolist()),
        )
        for fold in range(folds)
    )


def build_choice_payload(
    *,
    year: int,
    folds: int,
    seed: int,
    tie_tolerance: float,
    medians: dict[str, dict[str, float | None]],
    within_diagnostics: dict[str, object],
    signature: str | None = None,
) -> dict[str, object]:
    """Build the aggregate method-choice JSON payload."""
    payload: dict[str, object] = {
        "year": year,
        "folds": folds,
        "seed": seed,
        "tie_tolerance": tie_tolerance,
        "pooled_median_absolute_relative_error": medians,
        "chosen_methods": choose_methods(medians, tolerance=tie_tolerance),
        "within_model_diagnostics": within_diagnostics,
    }
    if signature is not None:
        payload["input_signature"] = signature
    return payload


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _required_columns(
    connection: duckdb.DuckDBPyConnection,
    relation: str,
    required: set[str],
    description: str,
) -> None:
    columns = {
        str(row[0])
        for row in connection.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    }
    missing = required - columns
    if missing:
        raise ValueError(
            f"{description} lacks required columns: " + ", ".join(sorted(missing))
        )


def _float_column(table: pa.Table, name: str) -> npt.NDArray[np.float64]:
    return np.asarray(
        table[name].cast(pa.float64()).to_numpy(zero_copy_only=False),
        dtype=np.float64,
    )


def _feature_matrix(table: pa.Table, names: tuple[str, ...]) -> npt.NDArray[np.float64]:
    return np.column_stack([_float_column(table, name) for name in names])


def _create_input_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    baseline: Path,
    natural: Path,
    ff_natural: Path,
    ff_cells: Path,
    insee_200m: Path,
    eurostat: Path,
    resolution_m: int,
    eurostat_resolution_m: int,
    density_thresholds: tuple[int, int],
    department: str,
) -> tuple[str, ...]:
    baseline_relation, _ = _relation(connection, "_crossval_baseline", baseline)
    natural_relation, _ = _relation(connection, "_crossval_natural_input", natural)
    ff_natural_relation, _ = _relation(
        connection, "_crossval_ff_natural_input", ff_natural
    )
    ff_cells_relation, _ = _relation(connection, "_crossval_ff_cells_input", ff_cells)
    insee_relation, _ = _source_relation(
        connection, "_crossval_insee_input", insee_200m
    )
    eurostat_relation, _ = _source_relation(
        connection, "_crossval_eurostat_input", eurostat
    )
    natural_columns = {
        str(row[0])
        for row in connection.execute(
            f"DESCRIBE SELECT * FROM {natural_relation}"
        ).fetchall()
    }
    age_variables = tuple(name for name in AGE_VARIABLES if name in natural_columns)
    if age_variables not in (AGE_VARIABLES, AGE_VARIABLES[:-1]):
        raise ValueError("Filosofi age groups are incomplete")
    model_variables = ("ind", *age_variables, *HOUSEHOLD_VARIABLES, "ind_snv")
    _required_columns(
        connection,
        baseline_relation,
        {"cell_id", "natural_cell_id", "natural_cell_size_m", *model_variables},
        "proportional origins",
    )
    _required_columns(
        connection,
        natural_relation,
        {"idcar_nat", "tmaille", "men", *model_variables},
        "Filosofi natural-level input",
    )
    _required_columns(
        connection,
        ff_natural_relation,
        {"natural_cell_id", *COVARIATES},
        "natural-level Fichiers fonciers",
    )
    _required_columns(
        connection,
        ff_cells_relation,
        {"cell_id", *COVARIATES, *DIRECT_WEIGHTS.values()},
        "200 m Fichiers fonciers",
    )
    _required_columns(
        connection,
        insee_relation,
        {
            "idcar_200m",
            "idcar_1km",
            "i_est_200",
            *model_variables,
            "lcog_geo",
        },
        "INSEE 200 m reference",
    )
    _required_columns(
        connection,
        eurostat_relation,
        {"GRD_ID", "T", "LAND_SURFACE"},
        "Eurostat density reference",
    )

    covariate_sql = ", ".join(
        f"CAST(f.{_quoted_identifier(name)} AS DOUBLE) AS {_quoted_identifier(name)}"
        for name in COVARIATES
    )
    northing = f"CAST(floor(b.cell_id / 100000) AS BIGINT) * {resolution_m}"
    easting = f"(b.cell_id % 100000) * {resolution_m}"
    cell_code = (
        f"'CRS3035RES{resolution_m}mN' || CAST({northing} AS VARCHAR) "
        f"|| 'E' || CAST({easting} AS VARCHAR)"
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE _cv_base AS
        SELECT b.*, {cell_code} AS cell_code, {covariate_sql}
        FROM {baseline_relation} b
        LEFT JOIN {ff_cells_relation} f USING (cell_id)
        """
    )
    _required_columns(
        connection, "_cv_base", set(COVARIATES), "baseline with FF covariates"
    )
    duplicate_base = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT cell_id FROM _cv_base GROUP BY cell_id HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_base:
        raise ValueError("proportional origins contain duplicate cell ids")

    natural_values = ", ".join(
        f"CAST(n.{_quoted_identifier(name)} AS DOUBLE) AS {_quoted_identifier(name)}"
        for name in ("men", *model_variables)
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE _cv_natural AS
        SELECT n.idcar_nat AS natural_cell_id,
            CAST(n.tmaille AS INTEGER) AS natural_cell_size_m,
            {natural_values}, {
            ", ".join(
                f"CAST(f.{_quoted_identifier(name)} AS DOUBLE) "
                f"AS {_quoted_identifier(name)}"
                for name in COVARIATES
            )
        }
        FROM {natural_relation} n
        JOIN (SELECT DISTINCT natural_cell_id FROM _cv_base) scope
          ON scope.natural_cell_id = n.idcar_nat
        LEFT JOIN {ff_natural_relation} f
          ON f.natural_cell_id = n.idcar_nat
        """
    )
    duplicate_natural = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT natural_cell_id FROM _cv_natural
            GROUP BY natural_cell_id HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_natural:
        raise ValueError("Filosofi natural input contains duplicate cell ids")

    density_labels = (
        f"<{density_thresholds[0]}",
        f"{density_thresholds[0]}-<{density_thresholds[1]}",
        f">={density_thresholds[1]}",
    )
    density_expression = f"""
        CASE
            WHEN T IS NULL OR T < 0 THEN 'population unavailable'
            WHEN CAST(T AS DOUBLE) / CASE
                WHEN LAND_SURFACE > 0 THEN LAND_SURFACE
                ELSE pow({eurostat_resolution_m} / 1000.0, 2)
            END < {density_thresholds[0]} THEN '{density_labels[0]}'
            WHEN CAST(T AS DOUBLE) / CASE
                WHEN LAND_SURFACE > 0 THEN LAND_SURFACE
                ELSE pow({eurostat_resolution_m} / 1000.0, 2)
            END < {density_thresholds[1]} THEN '{density_labels[1]}'
            ELSE '{density_labels[2]}'
        END
    """
    eurostat_duplicates = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT GRD_ID FROM {eurostat_relation}
            GROUP BY GRD_ID HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if eurostat_duplicates:
        raise ValueError("Eurostat grid contains duplicate GRD_ID values")
    connection.execute(
        f"""
        CREATE TEMP TABLE _cv_eurostat_density AS
        SELECT GRD_ID, {density_expression} AS density_class
        FROM {eurostat_relation}
        """
    )
    reference_values = ", ".join(
        f"CAST(i.{_quoted_identifier(name)} AS DOUBLE) "
        f"AS {_quoted_identifier('ref_' + name)}"
        for name in ("men", *model_variables)
    )
    base_covariate_sql = ", ".join(
        f"b.{_quoted_identifier(name)}" for name in COVARIATES
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE _cv_reference AS
        SELECT b.cell_id, b.natural_cell_id, b.natural_cell_size_m,
            i.i_est_200, i.idcar_1km, b.cell_code,
            coalesce(e.density_class, 'unmatched') AS density_class,
            EXISTS (
                SELECT 1
                FROM UNNEST(string_split(
                    CAST(i.lcog_geo AS VARCHAR), ','
                )) AS commune(code)
                WHERE left(trim(commune.code), length(?)) = ?
            ) AS in_validation_department,
            {reference_values},
            {base_covariate_sql}
        FROM {insee_relation} i
        JOIN _cv_base b ON b.cell_code = i.idcar_200m
        LEFT JOIN _cv_eurostat_density e ON e.GRD_ID = i.idcar_1km
        """,
        [department, department],
    )
    duplicate_reference = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT cell_id FROM _cv_reference
            GROUP BY cell_id HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_reference:
        raise ValueError("INSEE 200 m reference contains duplicate matched cells")
    if connection.execute("SELECT count(*) FROM _cv_reference").fetchone()[0] == 0:
        raise ValueError("INSEE 200 m reference has no cells in the origins scope")
    return age_variables


def _training_natural_table(
    connection: duckdb.DuckDBPyConnection,
) -> pa.Table:
    columns = (
        "natural_cell_id",
        "men",
        "ind",
        *AGE_VARIABLES,
        *HOUSEHOLD_VARIABLES,
        "ind_snv",
        *COVARIATES,
    )
    available = {
        str(row[0])
        for row in connection.execute(
            "DESCRIBE SELECT * FROM _cv_fold_train_natural"
        ).fetchall()
    }
    selected = tuple(name for name in columns if name in available)
    return connection.execute(
        f"SELECT {', '.join(_quoted_identifier(name) for name in selected)} "
        "FROM _cv_fold_train_natural ORDER BY natural_cell_id"
    ).to_arrow_table()


def _fit_natural_models(
    connection: duckdb.DuckDBPyConnection,
    *,
    age_variables: tuple[str, ...],
    downscale: Any,
) -> dict[str, Any | None]:
    training = _training_natural_table(connection)
    if training.num_rows == 0:
        raise ValueError("cross-validation fold has no natural-level training cells")
    x = _feature_matrix(training, COVARIATES)
    households = _float_column(training, "men")
    individuals = _float_column(training, "ind")
    variables = ("ind", *age_variables, *HOUSEHOLD_VARIABLES, "ind_snv")
    models: dict[str, Any | None] = {}
    for variable in variables:
        y = _float_column(training, variable)
        denominator = (
            "ind" if variable in age_variables or variable == "ind_snv" else "men"
        )
        exposure = individuals if denominator == "ind" else households
        valid = (households > 0) & (exposure > 0)
        if not np.any(y[valid] > 0):
            heldout_maximum = connection.execute(
                f"""
                SELECT max(n.{_quoted_identifier(variable)})
                FROM _cv_natural n
                JOIN _cv_fold_heldout_groups h USING (natural_cell_id)
                """
            ).fetchone()[0]
            if heldout_maximum is not None and heldout_maximum > 0:
                raise ValueError(
                    f"no positive natural-level training values for {variable}"
                )
            models[variable] = None
            continue
        model = fit_poisson(
            x[valid],
            y[valid],
            exposure[valid],
            households[valid],
            COVARIATES,
            folds=downscale.poisson_folds,
            seed=downscale.poisson_seed,
            tolerance=downscale.poisson_tolerance,
            max_iterations=downscale.poisson_max_iterations,
        )
        models[variable] = model
    return models


def _fit_within_models(
    connection: duckdb.DuckDBPyConnection,
    *,
    age_variables: tuple[str, ...],
    downscale: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, float | int]]]:
    variables = ("ind", *age_variables, *HOUSEHOLD_VARIABLES, "ind_snv")
    models: dict[str, Any] = {}
    diagnostics: dict[str, dict[str, float | int]] = {}
    for variable in variables:
        denominator = (
            "ind" if variable in age_variables or variable == "ind_snv" else "men"
        )
        training = connection.execute(
            f"""
            SELECT natural_cell_id,
                {_quoted_identifier("ref_" + variable)} AS target,
                {_quoted_identifier("ref_" + denominator)} AS exposure,
                {_quoted_identifier("ref_men")} AS standardization_weight,
                {", ".join(_quoted_identifier(name) for name in COVARIATES)}
            FROM _cv_fold_train_reference
            WHERE i_est_200 = 0
            ORDER BY natural_cell_id, cell_id
            """
        ).to_arrow_table()
        groups = training["natural_cell_id"].to_numpy(zero_copy_only=False)
        try:
            model = fit_within_poisson(
                _feature_matrix(training, COVARIATES),
                _float_column(training, "target"),
                _float_column(training, "exposure"),
                groups,
                COVARIATES,
                standardization_weights=_float_column(
                    training, "standardization_weight"
                ),
                tolerance=downscale.poisson_tolerance,
                max_iterations=downscale.poisson_max_iterations,
            )
        except RuntimeError as error:
            raise RuntimeError(f"within-cell model for {variable}: {error}") from error
        models[variable] = model
        diagnostics[variable] = {
            "dispersion": model.dispersion,
            "zero_offset_training_cells_excluded": model.zero_offset_count,
        }
    return models, diagnostics


def _score_expressions(
    age_variables: tuple[str, ...],
) -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    scores = {
        variable: ((variable,), (f"ref_{variable}",))
        for variable in ("ind", *age_variables, *HOUSEHOLD_VARIABLES, "ind_snv")
    }
    scores["under_18"] = (
        ("ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17"),
        ("ref_ind_0_3", "ref_ind_4_5", "ref_ind_6_10", "ref_ind_11_17"),
    )
    scores["age_65_plus"] = (
        ("ind_65_79", "ind_80p"),
        ("ref_ind_65_79", "ref_ind_80p"),
    )
    return scores


def _save_fold_observations(
    connection: duckdb.DuckDBPyConnection,
    *,
    method: str,
    age_variables: tuple[str, ...],
    resolution_m: int,
) -> None:
    score_expressions = _score_expressions(age_variables)
    selects = []
    for variable, (prediction_columns, reference_columns) in score_expressions.items():
        prediction = " + ".join(
            f"o.{_quoted_identifier(name)}" for name in prediction_columns
        )
        reference = " + ".join(
            f"r.{_quoted_identifier(name)}" for name in reference_columns
        )
        selects.append(
            f"""
            SELECT o.cell_id, '{method}' AS method, '{variable}' AS variable,
                o.natural_cell_size_m, r.density_class,
                CAST({prediction} AS DOUBLE) AS predicted,
                CAST({reference} AS DOUBLE) AS reference
            FROM _composition_origins o
            JOIN _cv_reference r USING (cell_id)
            JOIN _cv_fold_heldout_groups h
              ON h.natural_cell_id = o.natural_cell_id
            WHERE r.i_est_200 = 0
                AND r.in_validation_department
                AND o.natural_cell_size_m > {resolution_m}
            """
        )
    query = "\nUNION ALL\n".join(selects)
    if method == METHODS[0]:
        connection.execute(f"CREATE TEMP TABLE _cv_fold_observations AS {query}")
    else:
        connection.execute(f"INSERT INTO _cv_fold_observations {query}")


def _run_fold(
    connection: duckdb.DuckDBPyConnection,
    *,
    partition: FoldPartition,
    age_variables: tuple[str, ...],
    ff_cells: Path,
    downscale: Any,
) -> tuple[dict[str, dict[str, float | int]], int]:
    training_groups = pa.table({"natural_cell_id": list(partition.training_groups)})
    heldout_groups = pa.table({"natural_cell_id": list(partition.held_out_groups)})
    connection.register("_cv_training_group_input", training_groups)
    connection.register("_cv_heldout_group_input", heldout_groups)
    try:
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _cv_fold_training_groups AS
            SELECT * FROM _cv_training_group_input
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _cv_fold_heldout_groups AS
            SELECT * FROM _cv_heldout_group_input
            """
        )
    finally:
        connection.unregister("_cv_training_group_input")
        connection.unregister("_cv_heldout_group_input")
    overlap = connection.execute(
        """
        SELECT count(*) FROM _cv_fold_training_groups t
        JOIN _cv_fold_heldout_groups h USING (natural_cell_id)
        """
    ).fetchone()[0]
    if overlap:
        raise RuntimeError("natural-level cells leak across a cross-validation fold")
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE _cv_fold_train_natural AS
        SELECT n.* FROM _cv_natural n
        JOIN _cv_fold_training_groups g USING (natural_cell_id)
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE _cv_fold_train_reference AS
        SELECT r.* FROM _cv_reference r
        JOIN _cv_fold_training_groups g USING (natural_cell_id)
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE _cv_heldout_base AS
        SELECT b.* FROM _cv_base b
        JOIN _cv_fold_heldout_groups g USING (natural_cell_id)
        """
    )
    heldout_features_table = connection.execute(
        f"SELECT cell_id, {', '.join(_quoted_identifier(name) for name in COVARIATES)} "
        "FROM _cv_heldout_base ORDER BY cell_id"
    ).to_arrow_table()
    heldout_cell_ids = heldout_features_table["cell_id"]
    heldout_features = _feature_matrix(heldout_features_table, COVARIATES)
    natural_models = _fit_natural_models(
        connection,
        age_variables=age_variables,
        downscale=downscale,
    )
    within_models, diagnostics = _fit_within_models(
        connection, age_variables=age_variables, downscale=downscale
    )

    connection.execute("DROP TABLE IF EXISTS _cv_fold_observations")
    for method in METHODS:
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _composition_origins AS
            SELECT * FROM _cv_heldout_base
            """
        )
        apply_direct_weights(connection, ff_cells, downscale.cell_resolution_m)
        if method != "proportional":
            models = natural_models if method == "composition" else within_models
            for variable, model in models.items():
                denominator = (
                    "ind"
                    if variable in age_variables or variable == "ind_snv"
                    else "men"
                )
                if model is None:
                    rates = np.ones(len(heldout_cell_ids), dtype=np.float64)
                else:
                    rates = model.predict_rate(heldout_features)
                apply_regression_weights(
                    connection,
                    pa.table({"cell_id": heldout_cell_ids, "rate": rates}),
                    variable,
                    denominator,
                    downscale.cell_resolution_m,
                )
        failures = balance_age_groups(
            connection,
            age_variables,
            tolerance=downscale.ipf_tolerance,
            max_iterations=downscale.ipf_max_iterations,
        )
        if failures:
            raise RuntimeError(
                f"age IPF failed for {len(failures)} held-out cells in "
                f"{method} fold {partition.fold}"
            )
        _save_fold_observations(
            connection,
            method=method,
            age_variables=age_variables,
            resolution_m=downscale.cell_resolution_m,
        )
    scored_cells = int(
        connection.execute(
            """
        SELECT count(DISTINCT cell_id) FROM _cv_fold_observations
        WHERE method = 'proportional' AND variable = 'ind'
        """
        ).fetchone()[0]
    )
    if scored_cells == 0:
        raise ValueError(f"fold {partition.fold} has no eligible held-out cells")
    return diagnostics, scored_cells


def _suppressed_count(value: int, threshold: int) -> str | int:
    return f"<{threshold}" if value < threshold else value


def _summarize_within_diagnostics(
    fold_diagnostics: dict[int, dict[str, dict[str, float | int]]],
    threshold: int,
) -> dict[str, object]:
    variables = sorted(next(iter(fold_diagnostics.values())))
    result: dict[str, object] = {}
    for variable in variables:
        rows = [
            (fold, diagnostics[variable])
            for fold, diagnostics in sorted(fold_diagnostics.items())
        ]
        zero_offsets = [
            int(row["zero_offset_training_cells_excluded"]) for _, row in rows
        ]
        dispersions = [float(row["dispersion"]) for _, row in rows]
        result[variable] = {
            "mean_dispersion": float(np.mean(dispersions)),
            "dispersion_by_fold": {
                str(fold): float(row["dispersion"]) for fold, row in rows
            },
            "zero_offset_training_cells_excluded": _suppressed_count(
                sum(zero_offsets), threshold
            ),
            "zero_offset_training_cells_excluded_by_fold": {
                str(fold): _suppressed_count(
                    int(row["zero_offset_training_cells_excluded"]), threshold
                )
                for fold, row in rows
            },
        }
    return result


def _render_crossval_report(
    *,
    year: int,
    department: str,
    pooled_rows: list[dict[str, Any]],
    stratum_rows: list[dict[str, Any]],
    choices: dict[str, str],
    count_threshold: int,
    tolerance_fraction: float,
) -> str:
    lines = [
        f"# Origins cross-validation — Filosofi {year}",
        "",
        f"Department: {department}. Five grouped natural-cell folds. "
        f"Counts below {count_threshold} "
        "are suppressed. All methods use the same held-out INSEE 200 m cells "
        "with `i_est_200 = 0` and natural-cell size above 200 m. Median "
        "absolute relative errors exclude zero-reference cells; the tolerance "
        "share includes them and counts an exact zero prediction as within range.",
        "",
        "## Pooled held-out errors",
        "",
        "| Variable | Method | Cells | Positive reference | Mean absolute error | "
        "Median absolute relative error | Chosen |",
        "|---|---|---:|---:|---:|---:|:---:|",
    ]
    for row in pooled_rows:
        median = row["median_absolute_relative_error"]
        lines.append(
            "| {variable} | {method} | {cells} | {positive} | {mae:.3f} | "
            "{median} | {chosen} |".format(
                variable=row["variable"],
                method=row["method"],
                cells=_format_count(row["cell_count"], count_threshold),
                positive=_format_count(
                    row["positive_reference_count"], count_threshold
                ),
                mae=row["mean_absolute_error"],
                median="NA" if median is None else f"{100 * median:.1f}%",
                chosen="yes" if choices[row["variable"]] == row["method"] else "",
            )
        )
    lines.extend(
        [
            "",
            "## Breakdown by natural-cell size and density",
            "",
            f"Within tolerance means an absolute error no greater than "
            f"{tolerance_fraction:.0%} of the reference.",
            "",
            "| Method | Variable | Natural cell (m) | Density | Cells | "
            "Positive reference | Mean absolute error | Median absolute "
            f"relative error | Within ±{tolerance_fraction:.0%} |",
            "|---|---|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in stratum_rows:
        median = row["median_absolute_relative_error"]
        lines.append(
            "| {method} | {variable} | {size} | {density} | {cells} | "
            "{positive} | {mae:.3f} | {median} | {share:.1%} |".format(
                method=row["method"],
                variable=row["variable"],
                size=row["natural_cell_size_m"],
                density=row["density_class"],
                cells=_format_count(row["cell_count"], count_threshold),
                positive=_format_count(
                    row["positive_reference_count"], count_threshold
                ),
                mae=row["mean_absolute_error"],
                median="NA" if median is None else f"{100 * median:.1f}%",
                share=row["share_within_tolerance"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _aggregate_observations(
    connection: duckdb.DuckDBPyConnection,
    *,
    fold_paths: Sequence[Path],
    tolerance_fraction: float,
) -> tuple[
    dict[str, dict[str, float | None]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    paths = (
        "[" + ", ".join(_sql_string(str(path.resolve())) for path in fold_paths) + "]"
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW _cv_all_observations AS
        SELECT * FROM read_parquet({paths})
        """
    )
    medians = pooled_method_medians(connection, "_cv_all_observations")
    pooled_rows = (
        connection.execute(
            """
        SELECT variable, method, count(*) AS cell_count,
            count(*) FILTER (WHERE reference > 0) AS positive_reference_count,
            avg(abs(predicted - reference)) AS mean_absolute_error,
            quantile_cont(
                abs(predicted - reference) / NULLIF(abs(reference), 0), 0.5
            ) AS median_absolute_relative_error
        FROM _cv_all_observations
        GROUP BY variable, method
        ORDER BY variable, CASE method
            WHEN 'proportional' THEN 0
            WHEN 'composition' THEN 1 ELSE 2 END
        """
        )
        .to_arrow_table()
        .to_pylist()
    )
    stratum_rows = (
        connection.execute(
            f"""
        SELECT method, variable, natural_cell_size_m, density_class,
            count(*) AS cell_count,
            count(*) FILTER (WHERE reference > 0) AS positive_reference_count,
            avg(abs(predicted - reference)) AS mean_absolute_error,
            quantile_cont(
                abs(predicted - reference) / NULLIF(abs(reference), 0), 0.5
            ) AS median_absolute_relative_error,
            avg(CASE
                WHEN abs(predicted - reference)
                    <= {tolerance_fraction} * abs(reference) THEN 1.0
                ELSE 0.0
            END) AS share_within_tolerance
        FROM _cv_all_observations
        GROUP BY method, variable, natural_cell_size_m, density_class
        ORDER BY method, variable, natural_cell_size_m, density_class
        """
        )
        .to_arrow_table()
        .to_pylist()
    )
    return medians, pooled_rows, stratum_rows


def build_cross_validation(
    *,
    config_path: str | Path = "config/origins.yaml",
    pilot_config_path: str | Path = "config/pilot.yaml",
) -> dict[str, object]:
    """Run and checkpoint grouped cross-validation under interim."""
    config = load_origins_config(config_path)
    options = config.downscale
    report = config.report
    output = Path(report.output_directory)
    interim_root = Path(report.interim_directory).resolve()
    output_resolved = output.resolve()
    if not output_resolved.is_relative_to(interim_root):
        raise ValueError("cross-validation outputs must stay under data/interim")
    output.mkdir(parents=True, exist_ok=True)

    year = options.output_year
    baseline = output / options.output_pattern.format(year=year)
    ff_cells = output / report.ff_cells_pattern.format(vintage=options.ff_vintage)
    ff_natural = output / report.ff_natural_pattern.format(vintage=options.ff_vintage)
    ff_metadata = output / report.metadata_pattern.format(vintage=options.ff_vintage)
    inputs = (
        Path(config_path),
        Path(pilot_config_path),
        Path(config.filosofi_natural_archive),
        Path(config.filosofi_200m_archive),
        Path(config.validation.eurostat_grid),
        baseline,
        ff_cells,
        ff_natural,
        ff_metadata,
    )
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
    ff_info = json.loads(ff_metadata.read_text(encoding="utf-8"))
    if ff_info.get("second_home_source") != "hybrid_2024" or not ff_info.get(
        "signature"
    ):
        raise ValueError("cross-validation requires signed hybrid Fichiers fonciers")
    signature = hashlib.sha256(
        json.dumps(
            {
                "version": 1,
                "inputs": [_file_signature(path) for path in inputs],
                "folds": options.crossval_folds,
                "seed": options.crossval_seed,
                "tie_tolerance": options.crossval_tie_tolerance,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    choice_path = output / options.crossval_choice_pattern.format(year=year)
    report_path = output / options.crossval_report_pattern.format(year=year)
    checkpoint_dir = output / options.crossval_checkpoint_pattern.format(year=year)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    fold_paths = [
        checkpoint_dir / options.crossval_fold_checkpoint_pattern.format(fold=fold)
        for fold in range(options.crossval_folds)
    ]
    checkpoint_metadata_paths = [path.with_suffix(".json") for path in fold_paths]
    department = _pilot_department(pilot_config_path)
    connection, spill = open_restricted_connection(output)
    try:
        with tempfile.TemporaryDirectory(
            prefix="filosofi_crossval_", dir=output
        ) as directory:
            natural_csv = _extract_archive_member(
                Path(config.filosofi_natural_archive),
                "carreaux_nivNaturel_met.csv",
                Path(directory),
            )
            insee_csv = _extract_filosofi_200m(
                Path(config.filosofi_200m_archive), Path(directory)
            )
            age_variables = _create_input_tables(
                connection,
                baseline=baseline,
                natural=natural_csv,
                ff_natural=ff_natural,
                ff_cells=ff_cells,
                insee_200m=insee_csv,
                eurostat=Path(config.validation.eurostat_grid),
                resolution_m=options.cell_resolution_m,
                eurostat_resolution_m=config.validation.eurostat_resolution_m,
                density_thresholds=(
                    config.validation.density_thresholds_population_km2
                ),
                department=department,
            )
            natural_ids_table = connection.execute(
                """
                SELECT natural_cell_id FROM _cv_base
                GROUP BY natural_cell_id ORDER BY natural_cell_id
                """
            ).to_arrow_table()
            partitions = grouped_fold_partitions(
                natural_ids_table["natural_cell_id"].to_numpy(zero_copy_only=False),
                folds=options.crossval_folds,
                seed=options.crossval_seed,
            )
            fold_diagnostics: dict[int, dict[str, dict[str, float | int]]] = {}
            scored_cell_total = 0
            for partition, fold_path, metadata_path in zip(
                partitions, fold_paths, checkpoint_metadata_paths, strict=True
            ):
                metadata = (
                    json.loads(metadata_path.read_text(encoding="utf-8"))
                    if metadata_path.is_file()
                    else {}
                )
                if (
                    metadata.get("signature") == signature
                    and metadata.get("fold") == partition.fold
                    and fold_path.is_file()
                ):
                    fold_diagnostics[partition.fold] = metadata["diagnostics"]
                    scored_cell_total += int(metadata["scored_cells"])
                    LOGGER.info("Reused cross-validation fold %s", partition.fold)
                    continue
                LOGGER.info("Running cross-validation fold %s", partition.fold)
                diagnostics, scored_cells = _run_fold(
                    connection,
                    partition=partition,
                    age_variables=age_variables,
                    ff_cells=ff_cells,
                    downscale=options,
                )
                temporary = fold_path.with_suffix(".tmp.parquet")
                write_parquet(
                    connection,
                    "SELECT * FROM _cv_fold_observations",
                    temporary,
                )
                temporary.replace(fold_path)
                _write_json(
                    metadata_path,
                    {
                        "signature": signature,
                        "fold": partition.fold,
                        "diagnostics": diagnostics,
                        "scored_cells": scored_cells,
                    },
                )
                fold_diagnostics[partition.fold] = diagnostics
                scored_cell_total += scored_cells
            medians, pooled_rows, stratum_rows = _aggregate_observations(
                connection,
                fold_paths=fold_paths,
                tolerance_fraction=config.validation.within_tolerance_fraction,
            )
            choices = choose_methods(medians, tolerance=options.crossval_tie_tolerance)
            threshold = report.count_suppression_threshold
            diagnostics = _summarize_within_diagnostics(fold_diagnostics, threshold)
            payload = build_choice_payload(
                year=year,
                folds=options.crossval_folds,
                seed=options.crossval_seed,
                tie_tolerance=options.crossval_tie_tolerance,
                medians=medians,
                within_diagnostics=diagnostics,
                signature=signature,
            )
            report_text = _render_crossval_report(
                year=year,
                department=department,
                pooled_rows=pooled_rows,
                stratum_rows=stratum_rows,
                choices=choices,
                count_threshold=threshold,
                tolerance_fraction=config.validation.within_tolerance_fraction,
            )
            _write_json(choice_path, payload)
            temporary_report = report_path.with_suffix(".tmp.md")
            temporary_report.write_text(report_text, encoding="utf-8")
            temporary_report.replace(report_path)
            natural_cell_count = len(natural_ids_table["natural_cell_id"])
            return {
                "choice_file": str(choice_path),
                "report": str(report_path),
                "natural_cells": natural_cell_count,
                "scored_cells": scored_cell_total,
            }
    finally:
        connection.close()
        spill.cleanup()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the section-6.5 grouped origins experiment."""
    parser = argparse.ArgumentParser(
        description="Cross-validate 2021 origins downscaling methods"
    )
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    config = load_origins_config(args.config)
    options = config.downscale
    report = config.report
    year = options.output_year
    with logged_job(
        Path(config.jobs.log_directory),
        config.jobs.crossval_task,
        [
            config.filosofi_natural_archive,
            config.filosofi_200m_archive,
            str(args.pilot_config),
            config.validation.eurostat_grid,
            str(
                Path(report.output_directory) / options.output_pattern.format(year=year)
            ),
            str(
                Path(report.output_directory)
                / report.ff_cells_pattern.format(vintage=options.ff_vintage)
            ),
            str(
                Path(report.output_directory)
                / report.ff_natural_pattern.format(vintage=options.ff_vintage)
            ),
        ],
        report.count_suppression_threshold,
    ) as job:
        result = build_cross_validation(
            config_path=args.config, pilot_config_path=args.pilot_config
        )
        job.outputs.extend((str(result["choice_file"]), str(result["report"])))
        for key in ("natural_cells", "scored_cells"):
            job.counts[key] = int(result[key])
    for key in ("natural_cells", "scored_cells"):
        result[key] = _suppressed_count(
            int(result[key]), report.count_suppression_threshold
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
