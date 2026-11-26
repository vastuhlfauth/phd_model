"""Experimental section-6.3 composition weights."""

from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa

from landgrid.origins.downscale import _relation
from landgrid.origins.fichiers_fonciers import DownscaleConfig, _quoted_identifier

DIRECT_WEIGHTS = {
    "men_prop": "owner_occupied_main_residences",
    "men_mais": "main_residence_houses",
    "men_coll": "main_residence_flats",
    "log_soc": "social_housing_main_residences",
    "log_av45": "construction_av45",
    "log_45_70": "construction_45_70",
    "log_70_90": "construction_70_90",
    "log_ap90": "construction_ap90",
    "log_inc": "construction_inc",
}
AGE_VARIABLES = (
    "ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17", "ind_18_24",
    "ind_25_39", "ind_40_54", "ind_55_64", "ind_65_79", "ind_80p", "ind_inc",
)
COVARIATES = (
    "owner_share", "second_home_share", "social_share",
    "npiece_i_mean", "npiece_i_std", "dnbniv_mean", "dnbniv_std",
    "stoth_median", "stoth_std", "jannath_median", "jannath_std",
    "house_share", "main_residences_per_200m",
    "construction_av45_share", "construction_45_70_share",
    "construction_70_90_share", "construction_ap90_share",
    "construction_inc_share",
)

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class PoissonModel:
    """Standardised Poisson rate model for section 6.3."""

    input_names: tuple[str, ...]
    means: FloatArray
    scales: FloatArray
    selected: tuple[int, ...]
    feature_names: tuple[str, ...]
    coefficients: FloatArray
    standard_errors: FloatArray
    deviance_explained: float
    cross_validation_errors: tuple[float, ...]
    missing_counts: dict[str, int]

    def predict_rate(self, covariates: FloatArray) -> FloatArray:
        """Predict dimensionless category rates for each cell."""
        matrix = _design_matrix(covariates, self.means, self.scales)
        linear = matrix[:, self.selected] @ self.coefficients
        if not np.isfinite(linear).all():
            raise ValueError("non-finite Poisson linear predictor")
        with np.errstate(over="raise", invalid="raise"):
            return np.exp(linear)


def _design_matrix(x: FloatArray, means: FloatArray, scales: FloatArray) -> FloatArray:
    """Impute training means and add missing-value indicators."""
    missing = np.isnan(x)
    if np.isinf(x).any():
        raise ValueError("covariates contain infinite values")
    filled = np.where(missing, means, x)
    return np.column_stack(
        (np.ones(x.shape[0]), (filled - means) / scales, missing.astype(float))
    )


def _poisson_deviance(y: FloatArray, mu: FloatArray, weights: FloatArray) -> float:
    positive = y > 0
    terms = mu - y
    terms[positive] += y[positive] * np.log(y[positive] / mu[positive])
    return float(2 * np.sum(weights * terms))


def _fit_poisson_once(
    x: FloatArray,
    y: FloatArray,
    exposure: FloatArray,
    weights: FloatArray,
    names: tuple[str, ...],
    tolerance: float,
    max_iterations: int,
) -> PoissonModel:
    valid = ~np.isnan(x)
    valid_weights = valid * weights[:, None]
    weight_sums = valid_weights.sum(axis=0)
    if np.any(weight_sums == 0):
        raise ValueError("a covariate has no observed training values")
    means = np.nansum(x * weights[:, None], axis=0) / weight_sums
    variance = np.nansum(
        np.square(x - means) * weights[:, None], axis=0
    ) / weight_sums
    scales = np.sqrt(variance)
    scales[scales == 0] = 1
    matrix = _design_matrix(x, means, scales)
    all_names = ("intercept", *names, *(f"{name}_missing" for name in names))
    selected = [0]
    rank = 1
    for index in range(1, matrix.shape[1]):
        candidate = matrix[:, [*selected, index]]
        candidate_rank = np.linalg.matrix_rank(candidate)
        if candidate_rank > rank:
            selected.append(index)
            rank = candidate_rank
    design = matrix[:, selected]
    coefficients = np.zeros(design.shape[1])
    coefficients[0] = np.log(np.sum(weights * y) / np.sum(weights * exposure))
    offset = np.log(exposure)
    converged = False
    for _ in range(max_iterations):
        with np.errstate(over="raise", invalid="raise"):
            mu = np.exp(offset + design @ coefficients)
        information = design.T @ ((weights * mu)[:, None] * design)
        gradient = design.T @ (weights * (y - mu))
        step = np.linalg.solve(information, gradient)
        current_deviance = _poisson_deviance(y, mu, weights)
        fraction = 1.0
        while fraction > tolerance:
            candidate = coefficients + fraction * step
            with np.errstate(over="ignore", invalid="ignore"):
                new_mu = np.exp(offset + design @ candidate)
            if (
                np.isfinite(new_mu).all()
                and np.all(new_mu > 0)
                and _poisson_deviance(y, new_mu, weights)
                <= current_deviance + tolerance
            ):
                break
            fraction /= 2
        else:
            raise RuntimeError("Poisson fitting could not find a valid improving step")
        coefficients = candidate
        if np.max(np.abs(fraction * step)) <= tolerance:
            converged = True
            break
    if not converged:
        raise RuntimeError("Poisson fitting did not converge")
    mu = np.exp(offset + design @ coefficients)
    information = design.T @ ((weights * mu)[:, None] * design)
    errors = np.sqrt(np.diag(np.linalg.inv(information)))
    baseline = exposure * np.sum(weights * y) / np.sum(weights * exposure)
    null_deviance = _poisson_deviance(y, baseline, weights)
    deviance = _poisson_deviance(y, mu, weights)
    explained = 1.0 - deviance / null_deviance if null_deviance > 0 else 0.0
    return PoissonModel(
        input_names=names,
        means=means,
        scales=scales,
        selected=tuple(selected),
        feature_names=tuple(all_names[index] for index in selected),
        coefficients=coefficients,
        standard_errors=errors,
        deviance_explained=explained,
        cross_validation_errors=(),
        missing_counts={
            name: int(count) for name, count in zip(names, (~valid).sum(axis=0))
        },
    )


def fit_poisson(
    x: FloatArray,
    y: FloatArray,
    exposure: FloatArray,
    weights: FloatArray,
    names: tuple[str, ...],
    *,
    folds: int,
    seed: int,
    tolerance: float,
    max_iterations: int,
) -> PoissonModel:
    """Fit household-weighted Poisson counts with log exposure (section 6.3)."""
    from dataclasses import replace

    if (
        x.ndim != 2 or x.shape != (len(y), len(names))
        or exposure.shape != y.shape or weights.shape != y.shape
        or len(y) < folds or folds < 2 or tolerance <= 0 or max_iterations <= 0
        or not np.isfinite(y).all() or not np.isfinite(exposure).all()
        or not np.isfinite(weights).all() or np.any(y < 0)
        or np.any(exposure <= 0) or np.any(weights <= 0) or np.sum(y) == 0
    ):
        raise ValueError("invalid Poisson fitting inputs")
    assignments = np.random.default_rng(seed).permutation(len(y)) % folds
    errors = []
    for fold in range(folds):
        train = assignments != fold
        test = ~train
        fitted = _fit_poisson_once(
            x[train], y[train], exposure[train], weights[train], names,
            tolerance, max_iterations,
        )
        predicted = exposure[test] * fitted.predict_rate(x[test])
        errors.append(
            float(np.average(np.abs(predicted - y[test]), weights=weights[test]))
        )
    model = _fit_poisson_once(
        x, y, exposure, weights, names, tolerance, max_iterations
    )
    return replace(model, cross_validation_errors=tuple(errors))


def apply_regression_weights(
    connection: duckdb.DuckDBPyConnection,
    rates: pa.Table,
    variable: str,
    denominator: str,
    resolution_m: int,
) -> None:
    """Scale predicted rates within natural cells to Filosofi totals."""
    column = _quoted_identifier(variable)
    exposure = _quoted_identifier(denominator)
    connection.register("_composition_rates", rates)
    try:
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _composition_regression AS
            WITH cells AS (
                SELECT d.cell_id, d.natural_cell_id, d.natural_cell_size_m,
                    d.{column} AS original, d.{exposure} AS denominator, r.rate
                FROM _composition_origins d
                LEFT JOIN _composition_rates r USING (cell_id)
            ),
            weighted AS (
                SELECT *, denominator * rate AS weight FROM cells
            )
            SELECT *, sum(original) OVER (PARTITION BY natural_cell_id) AS control,
                sum(weight) OVER (PARTITION BY natural_cell_id) AS weight_sum
            FROM weighted
            """
        )
        invalid = connection.execute(
            """
            SELECT count(*) FROM _composition_regression
            WHERE rate IS NULL OR NOT isfinite(rate) OR rate <= 0
                OR denominator IS NULL OR NOT isfinite(denominator) OR denominator < 0
                OR original IS NULL OR NOT isfinite(original) OR original < 0
                OR (weight_sum <= 0 AND control > 0)
            """
        ).fetchone()[0]
        if invalid:
            raise ValueError(f"invalid or zero regression weights for {variable}")
        connection.execute(
            f"""
            UPDATE _composition_origins AS dest SET {column} = CASE
                WHEN source.natural_cell_size_m = ? THEN source.original
                WHEN source.weight_sum > 0
                    THEN source.control * source.weight / source.weight_sum
                ELSE 0.0 END
            FROM _composition_regression AS source
            WHERE dest.cell_id = source.cell_id
            """,
            [resolution_m],
        )
    finally:
        connection.unregister("_composition_rates")


def apply_models(
    connection: duckdb.DuckDBPyConnection,
    natural: pa.Table | Path,
    ff_natural: pa.Table | Path,
    ff_cells: pa.Table | Path,
    config: DownscaleConfig,
) -> dict[str, dict[str, object]]:
    """Fit natural-cell models and apply them to 200 m cells (section 6.3)."""
    sources = []
    registered = []
    for name, value in (
        ("natural", natural), ("ff_natural", ff_natural), ("ff_cells", ff_cells)
    ):
        relation, is_registered = _relation(connection, f"_model_{name}", value)
        sources.append(relation)
        if is_registered:
            registered.append(f"_model_{name}")
    natural_relation, ff_natural_relation, ff_cells_relation = sources
    try:
        natural_columns = {
            row[0] for row in connection.execute(
                f"DESCRIBE SELECT * FROM {natural_relation}"
            ).fetchall()
        }
        age_variables = tuple(
            name for name in AGE_VARIABLES if name in natural_columns
        )
        if age_variables != AGE_VARIABLES and age_variables != AGE_VARIABLES[:-1]:
            raise ValueError("Filosofi age groups are incomplete")
        variables = (
            "ind", *age_variables, "men_1ind", "men_5ind", "men_fmp",
            "men_pauv", "ind_snv",
        )
        features = ", ".join(f"f.{_quoted_identifier(name)}" for name in COVARIATES)
        controls = ", ".join(
            f"n.{_quoted_identifier(name)}" for name in ("men", *variables)
        )
        train = connection.execute(
            f"""
            SELECT {controls}, {features}
            FROM {natural_relation} n
            JOIN {ff_natural_relation} f ON n.idcar_nat = f.natural_cell_id
            ORDER BY n.idcar_nat
            """
        ).to_arrow_table()
        predictions = connection.execute(
            f"""
            SELECT d.cell_id, {features}
            FROM _composition_origins d
            LEFT JOIN {ff_cells_relation} f USING (cell_id)
            ORDER BY d.cell_id
            """
        ).to_arrow_table()
        if train.num_rows == 0:
            raise ValueError("no natural-level cells have FF model covariates")
        train_x = np.column_stack([
            train[name].to_numpy(zero_copy_only=False) for name in COVARIATES
        ]).astype(float)
        prediction_x = np.column_stack([
            predictions[name].to_numpy(zero_copy_only=False) for name in COVARIATES
        ]).astype(float)
        households = np.asarray(train["men"].to_numpy(), dtype=float)
        individuals = np.asarray(train["ind"].to_numpy(), dtype=float)
        reports: dict[str, dict[str, object]] = {}
        for variable in variables:
            y = np.asarray(train[variable].to_numpy(zero_copy_only=False), dtype=float)
            denominator = "ind" if variable in (*age_variables, "ind_snv") else "men"
            exposure = individuals if denominator == "ind" else households
            if (
                not np.isfinite(y).all() or not np.isfinite(exposure).all()
                or not np.isfinite(households).all() or np.any(y < 0)
                or np.any(exposure < 0) or np.any(households < 0)
                or np.any((exposure == 0) & (y > 0))
            ):
                raise ValueError(f"invalid natural-cell controls for {variable}")
            valid = (households > 0) & (exposure > 0)
            if not np.any(y[valid] > 0):
                maximum = connection.execute(
                    f"SELECT max({_quoted_identifier(variable)}) "
                    "FROM _composition_origins"
                ).fetchone()[0]
                if maximum and maximum > 0:
                    raise ValueError(
                        f"no positive training observations for {variable}"
                    )
                reports[variable] = {"status": "all training and output controls zero"}
                continue
            model = fit_poisson(
                train_x[valid], y[valid], exposure[valid], households[valid],
                COVARIATES, folds=config.poisson_folds, seed=config.poisson_seed,
                tolerance=config.poisson_tolerance,
                max_iterations=config.poisson_max_iterations,
            )
            rate_table = pa.table({
                "cell_id": predictions["cell_id"],
                "rate": model.predict_rate(prediction_x),
            })
            apply_regression_weights(
                connection, rate_table, variable, denominator, config.cell_resolution_m
            )
            reports[variable] = {
                "feature_names": list(model.feature_names),
                "input_names": list(model.input_names),
                "means": model.means.tolist(),
                "scales": model.scales.tolist(),
                "selected_indices": list(model.selected),
                "coefficients": model.coefficients.tolist(),
                "standard_errors": model.standard_errors.tolist(),
                "deviance_explained": model.deviance_explained,
                "cross_validation_weighted_mae": list(model.cross_validation_errors),
                "training_missing_counts": model.missing_counts,
                "prediction_missing_counts": {
                    name: int(count)
                    for name, count in zip(
                        COVARIATES, np.isnan(prediction_x).sum(axis=0), strict=True
                    )
                },
                "training_cell_count": int(valid.sum()),
            }
        return reports
    finally:
        for name in registered:
            connection.unregister(name)


def balance_age_groups(
    connection: duckdb.DuckDBPyConnection,
    age_variables: tuple[str, ...],
    *,
    tolerance: float,
    max_iterations: int,
) -> dict[str, str]:
    """Balance 200 m individual and natural age totals using IPF (section 6.3)."""
    if not age_variables or tolerance <= 0 or max_iterations <= 0:
        raise ValueError("invalid age IPF parameters")
    columns = ", ".join(_quoted_identifier(name) for name in age_variables)
    cells = connection.execute(
        f"SELECT cell_id, natural_cell_id, ind, {columns} FROM _composition_origins "
        "ORDER BY natural_cell_id, cell_id"
    ).to_arrow_table()
    if cells.num_rows == 0:
        raise ValueError("age IPF requires at least one cell")
    ids, groups = np.unique(
        np.asarray(cells["natural_cell_id"].to_pylist()), return_inverse=True
    )
    individuals = np.asarray(cells["ind"].to_numpy(), dtype=float)
    matrix = np.column_stack([
        cells[name].to_numpy(zero_copy_only=False) for name in age_variables
    ]).astype(float)
    if (
        not np.isfinite(individuals).all() or not np.isfinite(matrix).all()
        or np.any(individuals < 0) or np.any(matrix < 0)
    ):
        raise ValueError("invalid age IPF inputs")
    original = matrix.copy()
    group_count = len(ids)

    def totals(values: FloatArray) -> FloatArray:
        return np.column_stack([
            np.bincount(groups, weights=values[:, col], minlength=group_count)
            for col in range(values.shape[1])
        ])

    age_totals = totals(matrix)
    individual_totals = np.bincount(
        groups, weights=individuals, minlength=group_count
    )
    mismatch = np.abs(age_totals.sum(axis=1) - individual_totals) > (
        tolerance * np.maximum(1, individual_totals)
    )
    unsupported_rows = (individuals > 0) & (matrix.sum(axis=1) == 0)
    unsupported = np.bincount(
        groups, weights=unsupported_rows.astype(float), minlength=group_count
    ) > 0
    active = ~(mismatch | unsupported)
    active_rows = active[groups]
    converged = ~active
    for _ in range(max_iterations):
        row_sum = matrix.sum(axis=1)
        row_factors = np.ones(len(individuals))
        np.divide(
            individuals, row_sum, out=row_factors,
            where=active_rows & (row_sum > 0),
        )
        matrix *= row_factors[:, None]
        current_totals = totals(matrix)
        column_factors = np.ones_like(age_totals)
        np.divide(
            age_totals, current_totals, out=column_factors,
            where=active[:, None] & (current_totals > 0),
        )
        matrix *= column_factors[groups]
        row_error = np.abs(matrix.sum(axis=1) - individuals) / np.maximum(
            1, individuals
        )
        group_row_error = np.zeros(group_count)
        np.maximum.at(group_row_error, groups, row_error)
        group_column_error = np.max(
            np.abs(totals(matrix) - age_totals) / np.maximum(1, age_totals), axis=1
        )
        converged = (~active) | (
            (group_row_error <= tolerance) & (group_column_error <= tolerance)
        )
        if converged.all():
            break
    failed = ~converged
    matrix[(mismatch | unsupported | failed)[groups]] = original[
        (mismatch | unsupported | failed)[groups]
    ]
    reasons = {
        str(ids[index]): (
            "inconsistent age and individual totals" if mismatch[index]
            else "no age support for a populated cell" if unsupported[index]
            else "IPF did not converge"
        )
        for index in np.flatnonzero(mismatch | unsupported | failed)
    }
    balanced = pa.table({
        "cell_id": cells["cell_id"],
        **{name: matrix[:, index] for index, name in enumerate(age_variables)},
    })
    connection.register("_composition_balanced_ages", balanced)
    try:
        assignments = ", ".join(
            f"{_quoted_identifier(name)} = src.{_quoted_identifier(name)}"
            for name in age_variables
        )
        connection.execute(
            f"UPDATE _composition_origins AS dst SET {assignments} "
            "FROM _composition_balanced_ages src WHERE dst.cell_id = src.cell_id"
        )
    finally:
        connection.unregister("_composition_balanced_ages")
    return reasons


def apply_direct_weights(
    connection: duckdb.DuckDBPyConnection,
    ff_cells: pa.Table | Path,
    resolution_m: int,
) -> dict[str, int]:
    """Redistribute matched counts by FF counterparts, preserving zone totals."""
    if resolution_m <= 0:
        raise ValueError("cell resolution must be positive")
    relation, registered = _relation(connection, "_composition_ff_input", ff_cells)
    try:
        counts = ", ".join(
            f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
            for name in DIRECT_WEIGHTS.values()
        )
        connection.execute(
            f"CREATE OR REPLACE TEMP TABLE _composition_ff AS "
            f"SELECT cell_id, {counts} FROM {relation} GROUP BY cell_id"
        )
        fallbacks: dict[str, int] = {}
        for variable, counterpart in DIRECT_WEIGHTS.items():
            column = _quoted_identifier(variable)
            weight = _quoted_identifier(counterpart)
            connection.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE _composition_direct AS
                WITH cells AS (
                    SELECT d.cell_id, d.natural_cell_id, d.natural_cell_size_m,
                        d.men, d.{column} AS original,
                        coalesce(f.{weight}, 0) AS weight
                    FROM _composition_origins d
                    LEFT JOIN _composition_ff f USING (cell_id)
                )
                SELECT *,
                    sum(original) OVER (PARTITION BY natural_cell_id) AS control,
                    sum(weight) OVER (PARTITION BY natural_cell_id) AS weight_sum,
                    sum(men) OVER (PARTITION BY natural_cell_id) AS household_sum
                FROM cells
                """
            )
            invalid = connection.execute(
                """
                SELECT count(*) FROM _composition_direct
                WHERE weight < 0 OR men < 0 OR original < 0
                    OR NOT isfinite(weight) OR NOT isfinite(men)
                    OR NOT isfinite(original)
                    OR (weight_sum = 0 AND household_sum = 0 AND control > 0)
                """
            ).fetchone()[0]
            if invalid:
                raise ValueError(f"invalid or zero direct weights for {variable}")
            fallbacks[variable] = int(connection.execute(
                """
                SELECT count(DISTINCT natural_cell_id) FROM _composition_direct
                WHERE natural_cell_size_m > ? AND weight_sum = 0
                """,
                [resolution_m],
            ).fetchone()[0])
            connection.execute(
                f"""
                UPDATE _composition_origins AS dest SET {column} = CASE
                    WHEN source.natural_cell_size_m = ? THEN source.original
                    WHEN source.weight_sum > 0
                        THEN source.control * source.weight / source.weight_sum
                    WHEN source.household_sum > 0
                        THEN source.control * source.men / source.household_sum
                    ELSE 0.0 END
                FROM _composition_direct AS source
                WHERE dest.cell_id = source.cell_id
                """,
                [resolution_m],
            )
        return fallbacks
    finally:
        if registered:
            connection.unregister("_composition_ff_input")
