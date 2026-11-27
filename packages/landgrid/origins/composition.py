"""Experimental section-6.3 composition weights."""

import argparse
import hashlib
import json
import logging
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
from common.duckdb_io import write_parquet

from landgrid.origins.downscale import (
    _extract_archive_member,
    _relation,
    build_origins_2021_200m,
)
from landgrid.origins.fichiers_fonciers import (
    DownscaleConfig,
    _file_signature,
    _quoted_identifier,
    load_origins_config,
)
from landgrid.origins.job import open_restricted_connection

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
REGRESSION_VARIABLES = (
    "ind", *AGE_VARIABLES, "men_1ind", "men_5ind", "men_fmp", "men_pauv",
    "ind_snv",
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
LOGGER = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class WithinPoissonModel:
    """Conditional Poisson split model with natural-cell fixed effects (6.3)."""

    means: FloatArray
    scales: FloatArray
    selected: tuple[int, ...]
    feature_names: tuple[str, ...]
    dropped_features: tuple[str, ...]
    coefficients: FloatArray
    standard_errors: FloatArray
    dispersion: float
    zero_offset_count: int
    training_cell_count: int
    training_group_count: int

    def predict_rate(self, covariates: FloatArray) -> FloatArray:
        """Return relative, dimensionless cell rates without fixed effects."""
        matrix = _design_matrix(covariates, self.means, self.scales)
        linear = matrix[:, self.selected] @ self.coefficients
        if not np.isfinite(linear).all():
            raise ValueError("non-finite within-cell Poisson predictor")
        with np.errstate(over="raise", invalid="raise"):
            return np.exp(linear)


RegressionModel = TypeVar("RegressionModel", PoissonModel, WithinPoissonModel)


def _check_coefficient_bound(
    model: PoissonModel | WithinPoissonModel, bound: float,
) -> None:
    coefficients = np.asarray([
        coefficient for name, coefficient in zip(
            model.feature_names, model.coefficients, strict=True
        ) if name != "intercept"
    ])
    if not np.isfinite(coefficients).all():
        raise RuntimeError("non-finite regression coefficients")
    maximum = float(np.max(np.abs(coefficients))) if coefficients.size else 0.0
    if maximum > bound:
        raise RuntimeError(
            f"non-intercept coefficient {maximum:.6g} exceeds "
            f"configured bound {bound:g}"
        )


def guarded_regression_fit(
    fit: Callable[[], RegressionModel], *,
    variable: str, method: str, coefficient_bound: float,
) -> tuple[RegressionModel | None, str | None]:
    """Use explicit proportional fallback for unusable section-6.3 rate fits."""
    try:
        model = fit()
        _check_coefficient_bound(model, coefficient_bound)
    except (
        RuntimeError, np.linalg.LinAlgError, FloatingPointError, ValueError,
    ) as error:
        if (
            isinstance(error, ValueError)
            and not isinstance(error, np.linalg.LinAlgError)
            and str(error) not in {
                "no informative natural cells for within-cell Poisson",
                "insufficient residual degrees of freedom for dispersion",
            }
        ):
            raise
        reason = f"{type(error).__name__}: {error}"
        LOGGER.warning(
            "%s model for %s: falling back to proportional (%s)",
            method, variable, reason,
        )
        return None, reason
    return model, None


def fit_within_poisson(
    x: FloatArray,
    y: FloatArray,
    exposure: FloatArray,
    groups: npt.NDArray,
    names: tuple[str, ...],
    *,
    standardization_weights: FloatArray,
    tolerance: float,
    max_iterations: int,
) -> WithinPoissonModel:
    """Fit 200 m counts using observed exposures and natural-cell effects (6.3)."""
    if (
        x.ndim != 2 or x.shape != (len(y), len(names))
        or exposure.shape != y.shape or groups.shape != y.shape
        or standardization_weights.shape != y.shape
        or not np.isfinite(y).all() or np.any(y < 0)
        or not np.isfinite(exposure).all() or np.any(exposure < 0)
        or not np.isfinite(standardization_weights).all()
        or np.any(standardization_weights < 0)
        or np.isinf(x).any() or tolerance <= 0 or max_iterations <= 0
    ):
        raise ValueError("invalid within-cell Poisson fitting inputs")
    zero_offset_count = int(np.count_nonzero(exposure == 0))
    eligible = exposure > 0
    x, y, exposure, groups = (
        x[eligible], y[eligible], exposure[eligible], groups[eligible]
    )
    standardization_weights = standardization_weights[eligible]
    _, group_index, group_counts = np.unique(
        groups, return_inverse=True, return_counts=True
    )
    group_totals = np.bincount(group_index, weights=y)
    eligible = (group_counts[group_index] >= 2) & (group_totals[group_index] > 0)
    x, y, exposure, groups = (
        x[eligible], y[eligible], exposure[eligible], groups[eligible]
    )
    standardization_weights = standardization_weights[eligible]
    _, group_index, group_counts = np.unique(
        groups, return_inverse=True, return_counts=True
    )
    n_groups = len(group_counts)
    if n_groups == 0:
        raise ValueError("no informative natural cells for within-cell Poisson")
    observed = ~np.isnan(x)
    sums = (observed * standardization_weights[:, None]).sum(axis=0)
    means = np.divide(
        np.nansum(x * standardization_weights[:, None], axis=0), sums,
        out=np.zeros(len(names)), where=sums > 0,
    )
    scales = np.sqrt(np.divide(
        np.nansum((x - means) ** 2 * standardization_weights[:, None], axis=0),
        sums, out=np.zeros(len(names)), where=sums > 0,
    ))
    scales[scales == 0] = 1
    matrix = _design_matrix(x, means, scales)
    all_names = ("intercept", *names, *(f"{name}_missing" for name in names))
    centered = matrix.copy()
    for column in range(matrix.shape[1]):
        centered[:, column] -= (
            np.bincount(group_index, weights=matrix[:, column]) / group_counts
        )[group_index]
    selected: list[int] = []
    rank = 0
    for index in range(1, matrix.shape[1]):
        minima = np.full(n_groups, np.inf)
        maxima = np.full(n_groups, -np.inf)
        np.minimum.at(minima, group_index, matrix[:, index])
        np.maximum.at(maxima, group_index, matrix[:, index])
        if np.array_equal(minima, maxima):
            continue
        candidate = centered[:, [*selected, index]]
        candidate_rank = np.linalg.matrix_rank(candidate)
        if candidate_rank > rank:
            selected.append(index)
            rank = candidate_rank
    dropped_features = tuple(
        all_names[index] for index in range(1, len(all_names))
        if index not in selected
    )
    LOGGER.info("Within-cell Poisson dropped features: %s", ", ".join(dropped_features))
    # Group constants cancel from the conditional likelihood.
    design = centered[:, selected]
    if len(y) <= n_groups + rank:
        raise ValueError("insufficient residual degrees of freedom for dispersion")
    totals = np.bincount(group_index, weights=y)

    def evaluate(beta: FloatArray) -> FloatArray:
        linear = np.log(exposure) + design @ beta
        maxima = np.full(n_groups, -np.inf)
        np.maximum.at(maxima, group_index, linear)
        relative = np.exp(linear - maxima[group_index])
        sums_by_group = np.bincount(group_index, weights=relative)
        return totals[group_index] * relative / sums_by_group[group_index]

    beta = np.zeros(rank)
    converged = rank == 0
    for _ in range(max_iterations if rank else 0):
        mu = evaluate(beta)
        group_mean = np.vstack([
            np.bincount(group_index, weights=mu * design[:, column])
            / totals
            for column in range(rank)
        ]).T
        within = design - group_mean[group_index]
        information = within.T @ (mu[:, None] * within)
        step = np.linalg.solve(information, design.T @ (y - mu))
        conditional_change = float(np.max(np.abs(design @ step)))
        if conditional_change <= tolerance:
            converged = True
            break
        direction = within @ step
        fraction = 1.0
        while fraction > tolerance:
            candidate = beta + fraction * step
            delta = fraction * direction
            mean_delta = np.bincount(group_index, weights=mu * delta) / totals
            # Compare likelihoods through their increment, not large totals.
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                remainder = np.bincount(
                    group_index, weights=mu * (np.expm1(delta) - delta)
                ) / totals
                improvement = float(
                    np.dot(y - mu, delta)
                    + np.dot(totals, mean_delta - np.log1p(mean_delta + remainder))
                )
            if np.isfinite(improvement) and improvement >= -tolerance:
                break
            fraction /= 2
        else:
            raise RuntimeError(
                "within-cell Poisson could not find an improving step "
                f"(conditional predictor step {conditional_change:.6g}, "
                f"likelihood increment {improvement:.6g}, "
                f"tolerance {tolerance:.6g})"
            )
        beta = candidate
    if not converged:
        raise RuntimeError(
            f"within-cell Poisson did not converge after {max_iterations} iterations "
            f"(conditional predictor step {conditional_change:.6g}, "
            f"tolerance {tolerance:.6g})"
        )
    mu = evaluate(beta)
    dispersion = float(np.sum((y - mu) ** 2 / mu) / (len(y) - n_groups - rank))
    if rank:
        group_mean = np.vstack([
            np.bincount(group_index, weights=mu * design[:, column]) / totals
            for column in range(rank)
        ]).T
        within = design - group_mean[group_index]
        information = within.T @ (mu[:, None] * within)
        errors = np.sqrt(np.diag(np.linalg.inv(information)) * dispersion)
    else:
        errors = np.empty(0)
    return WithinPoissonModel(
        means=means, scales=scales, selected=tuple(selected),
        feature_names=tuple(all_names[index] for index in selected),
        dropped_features=dropped_features,
        coefficients=beta, standard_errors=errors, dispersion=dispersion,
        zero_offset_count=zero_offset_count, training_cell_count=len(y),
        training_group_count=n_groups,
    )


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
    coefficient_bound: float | None = None,
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
        if coefficient_bound is not None:
            _check_coefficient_bound(fitted, coefficient_bound)
        predicted = exposure[test] * fitted.predict_rate(x[test])
        errors.append(
            float(np.average(np.abs(predicted - y[test]), weights=weights[test]))
        )
    model = _fit_poisson_once(
        x, y, exposure, weights, names, tolerance, max_iterations
    )
    if coefficient_bound is not None:
        _check_coefficient_bound(model, coefficient_bound)
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
    *,
    methods: dict[str, str] | None = None,
    reference_200m: pa.Table | Path | None = None,
    completed: dict[str, dict[str, object]] | None = None,
    checkpoint: Callable[[dict[str, dict[str, object]]], None] | None = None,
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
        chosen = {
            name: config.fixed_methods.get(name, config.default_method)
            for name in variables
        }
        if methods is not None:
            chosen.update(methods)
        reference_relation = None
        if any(chosen[name] == "within" for name in variables):
            if reference_200m is None:
                raise ValueError("within models require INSEE 200 m reference")
            reference_relation, is_registered = _relation(
                connection, "_composition_reference", reference_200m
            )
            if is_registered:
                registered.append("_composition_reference")
        features = ", ".join(f"f.{_quoted_identifier(name)}" for name in COVARIATES)
        controls = ", ".join(
            f"n.{_quoted_identifier(name)}" for name in ("men", *variables)
        )
        train = connection.execute(
            f"""
            SELECT {controls}, {features}
            FROM {natural_relation} n
            JOIN (SELECT DISTINCT natural_cell_id FROM _composition_origins) scope
              ON n.idcar_nat = scope.natural_cell_id
            LEFT JOIN {ff_natural_relation} f ON n.idcar_nat = f.natural_cell_id
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
        if reference_relation is not None:
            resolution = config.cell_resolution_m
            northing = f"CAST(floor(d.cell_id / 100000) AS BIGINT) * {resolution}"
            easting = f"(d.cell_id % 100000) * {resolution}"
            code = (
                f"'CRS3035RES{resolution}mN' || CAST({northing} AS VARCHAR) "
                f"|| 'E' || CAST({easting} AS VARCHAR)"
            )
            target_names = {"men", "ind"} | {
                name for name in variables if chosen[name] == "within"
            }
            target_sql = ", ".join(
                f"i.{_quoted_identifier(name)} AS {_quoted_identifier('ref_' + name)}"
                for name in sorted(target_names)
            )
            connection.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE _within_training AS
                SELECT d.cell_id, d.natural_cell_id, i.idcar_nat AS reference_group,
                    {target_sql}, {features}
                FROM _composition_origins d
                JOIN {reference_relation} i ON i.idcar_200m = {code}
                LEFT JOIN {ff_cells_relation} f USING (cell_id)
                WHERE i.i_est_200 = 0
                """
            )
            invalid = connection.execute(
                """
                SELECT count(*) FROM (
                    SELECT cell_id FROM _within_training
                    GROUP BY cell_id
                    HAVING count(*) != 1
                        OR count(*) FILTER (
                            WHERE reference_group IS DISTINCT FROM natural_cell_id
                        ) > 0
                )
                """
            ).fetchone()[0]
            if invalid:
                raise ValueError("duplicate or mismatched INSEE 200 m training cells")
        train_x = np.column_stack([
            train[name].to_numpy(zero_copy_only=False) for name in COVARIATES
        ]).astype(float)
        prediction_x = np.column_stack([
            predictions[name].to_numpy(zero_copy_only=False) for name in COVARIATES
        ]).astype(float)
        households = np.asarray(train["men"].to_numpy(), dtype=float)
        individuals = np.asarray(train["ind"].to_numpy(), dtype=float)
        reports: dict[str, dict[str, object]] = dict(completed or {})
        for variable in variables:
            if variable in reports:
                LOGGER.info("Reused composition model %s", variable)
                continue
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
            method = chosen[variable]
            if method == "proportional":
                LOGGER.info("Applying configured proportional method for %s", variable)
                apply_regression_weights(
                    connection,
                    pa.table({
                        "cell_id": predictions["cell_id"],
                        "rate": np.ones(predictions.num_rows),
                    }),
                    variable, denominator, config.cell_resolution_m,
                )
                reports[variable] = {
                    "status": f"configured proportional to {denominator}",
                    "method": "proportional",
                }
                if checkpoint is not None:
                    checkpoint(reports)
                continue
            if not np.any(y[valid] > 0):
                maximum = connection.execute(
                    f"SELECT max({_quoted_identifier(variable)}) "
                    "FROM _composition_origins"
                ).fetchone()[0]
                if maximum and maximum > 0:
                    raise ValueError(
                        f"no positive training observations for {variable}"
                    )
                reports[variable] = {
                    "status": "all training and output controls zero", "method": method,
                }
                if checkpoint is not None:
                    checkpoint(reports)
                continue
            LOGGER.info("Fitting composition model %s", variable)
            if method == "within":
                training = connection.execute(
                    f"""
                    SELECT natural_cell_id,
                        {_quoted_identifier('ref_' + variable)} AS target,
                        {_quoted_identifier('ref_' + denominator)} AS exposure,
                        ref_men AS households,
                        {", ".join(_quoted_identifier(name) for name in COVARIATES)}
                    FROM _within_training
                    ORDER BY natural_cell_id, cell_id
                    """
                ).to_arrow_table()
                within_x = np.column_stack([
                    training[name].to_numpy(zero_copy_only=False) for name in COVARIATES
                ]).astype(float)
                model, reason = guarded_regression_fit(
                    lambda: fit_within_poisson(
                        within_x,
                        np.asarray(training["target"].to_numpy(), dtype=float),
                        np.asarray(training["exposure"].to_numpy(), dtype=float),
                        training["natural_cell_id"].to_numpy(zero_copy_only=False),
                        COVARIATES,
                        standardization_weights=np.asarray(
                            training["households"].to_numpy(), dtype=float
                        ),
                        tolerance=config.poisson_tolerance,
                        max_iterations=config.poisson_max_iterations,
                    ),
                    variable=variable, method=method,
                    coefficient_bound=config.poisson_coefficient_bound,
                )
            else:
                model, reason = guarded_regression_fit(
                    lambda: fit_poisson(
                        train_x[valid], y[valid], exposure[valid], households[valid],
                        COVARIATES, folds=config.poisson_folds,
                        seed=config.poisson_seed,
                        tolerance=config.poisson_tolerance,
                        max_iterations=config.poisson_max_iterations,
                        coefficient_bound=config.poisson_coefficient_bound,
                    ),
                    variable=variable, method=method,
                    coefficient_bound=config.poisson_coefficient_bound,
                )
            rate_table = pa.table({
                "cell_id": predictions["cell_id"],
                "rate": (
                    np.ones(predictions.num_rows) if model is None
                    else model.predict_rate(prediction_x)
                ),
            })
            apply_regression_weights(
                connection, rate_table, variable, denominator, config.cell_resolution_m
            )
            if model is None:
                reports[variable] = {
                    "status": f"proportional fallback: {reason}",
                    "method": "proportional", "fallback_reason": reason,
                }
                if checkpoint is not None:
                    checkpoint(reports)
                continue
            if isinstance(model, WithinPoissonModel):
                reports[variable] = {
                    "method": method,
                    "feature_names": list(model.feature_names),
                    "dropped_features": list(model.dropped_features),
                    "coefficients": model.coefficients.tolist(),
                    "standard_errors": model.standard_errors.tolist(),
                    "dispersion": model.dispersion,
                    "training_cell_count": model.training_cell_count,
                    "training_group_count": model.training_group_count,
                    "zero_offset_count": model.zero_offset_count,
                }
                if checkpoint is not None:
                    checkpoint(reports)
                continue
            reports[variable] = {
                "method": method,
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
            if checkpoint is not None:
                checkpoint(reports)
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
        cells["natural_cell_id"].to_numpy(zero_copy_only=False), return_inverse=True
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


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def load_method_choices(path: Path, config: DownscaleConfig) -> dict[str, str]:
    """Resolve per-variable experimental methods, giving configuration precedence."""
    choices: dict[str, str] = {}
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("year") != config.output_year or not isinstance(
            payload.get("chosen_methods"), dict
        ):
            raise ValueError("invalid composition method-choice file")
        for name, method in payload["chosen_methods"].items():
            if name in REGRESSION_VARIABLES:
                if not isinstance(method, str) or method not in {
                    "proportional", "composition", "within"
                }:
                    raise ValueError(f"invalid method choice for {name}")
                choices[name] = method
    else:
        LOGGER.warning("Method-choice file missing: %s; using config default", path)
    return {
        name: config.fixed_methods.get(name, choices.get(name, config.default_method))
        for name in REGRESSION_VARIABLES
    }


def composition_input_signature(
    inputs: Sequence[Path], *, choice_path: Path | None = None,
    reference_archive: Path | None = None,
) -> str:
    """Fingerprint composition inputs to reject stale checkpoints and outputs."""
    return hashlib.sha256(json.dumps(
        {
            "version": 2, "inputs": [_file_signature(path) for path in inputs],
            "choice": (
                _file_signature(choice_path) if choice_path and choice_path.is_file()
                else None
            ),
            "reference": (
                _file_signature(reference_archive) if reference_archive else None
            ),
        },
        sort_keys=True,
    ).encode("utf-8")).hexdigest()


def _render_composition_report(
    reports: dict[str, dict[str, object]],
    fallbacks: dict[str, int],
    failures: dict[str, str],
    threshold: int,
) -> str:
    def count(value: int) -> str:
        return f"<{threshold}" if value < threshold else str(value)

    lines = [
        "# Experimental composition models",
        "",
        "Natural-cell and within-cell Poisson covariates use household-weighted "
        "standardisation and mean imputation with missing indicators.",
        "",
        "## Direct-weight household fallbacks",
        "",
        "| Variable | Natural cells |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {count(value)} |" for name, value in fallbacks.items())
    lines.extend([
        "",
        f"Age IPF failures: {count(len(failures))}. Cell identifiers and reasons "
        "are in the restricted interim failure Parquet.",
    ])
    for variable, report in reports.items():
        lines.extend(["", f"## {variable}", ""])
        lines.append(f"Method: {report['method']}")
        if "status" in report:
            lines.append(str(report["status"]))
            continue
        lines.append(f"Training cells: {count(int(report['training_cell_count']))}")
        if report["method"] == "within":
            lines.append(f"Dispersion: {float(report['dispersion']):.6g}")
            lines.append(
                "Dropped features: " + (
                    ", ".join(report["dropped_features"]) or "none"
                )
            )
            lines.append("Standard errors are dispersion-corrected.")
            lines.extend(
                ["", "| Feature | Coefficient | Standard error |", "|---|---:|---:|"]
            )
            for name, coefficient, error in zip(
                report["feature_names"], report["coefficients"],
                report["standard_errors"], strict=True,
            ):
                lines.append(
                    f"| {name} | {float(coefficient):.6g} | {float(error):.6g} |"
                )
            continue
        lines.append(f"Deviance explained: {float(report['deviance_explained']):.6g}")
        lines.append(
            "Cross-validation weighted MAE by fold: "
            + ", ".join(f"{float(value):.6g}" for value in report[
                "cross_validation_weighted_mae"
            ])
        )
        lines.extend(
            ["", "| Feature | Coefficient | Standard error |", "|---|---:|---:|"]
        )
        for name, coefficient, error in zip(
            report["feature_names"], report["coefficients"], report["standard_errors"],
            strict=True,
        ):
            lines.append(f"| {name} | {float(coefficient):.6g} | {float(error):.6g} |")
        for key in ("training_missing_counts", "prediction_missing_counts"):
            lines.extend(["", f"Missing values ({key}):", ""])
            lines.extend(
                f"- {name}: {count(int(value))}"
                for name, value in report[key].items()
            )
    return "\n".join([*lines, ""])


def _check_composition_totals(
    connection: duckdb.DuckDBPyConnection, benchmark: Path, tolerance: float
) -> None:
    columns = [
        str(row[0]) for row in connection.execute(
            "DESCRIBE SELECT * FROM _composition_origins"
        ).fetchall()
        if str(row[1]).upper() in {
            "DOUBLE", "FLOAT", "DECIMAL", "REAL", "BIGINT", "INTEGER", "HUGEINT"
        } and row[0] not in {"cell_id", "natural_cell_size_m"}
    ]
    checks = " OR ".join(
        f"abs(sum(d.{_quoted_identifier(name)}) - sum(b.{_quoted_identifier(name)})) "
        f"> {tolerance} * greatest(1.0, abs(sum(b.{_quoted_identifier(name)})))"
        for name in columns
    )
    mismatch = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT d.natural_cell_id FROM _composition_origins d
            JOIN read_parquet(?) b USING (cell_id)
            GROUP BY d.natural_cell_id HAVING {checks}
        )
        """,
        [str(benchmark)],
    ).fetchone()[0]
    if mismatch:
        raise RuntimeError("composition does not preserve benchmark natural totals")


def build_composition(
    *,
    config_path: str | Path = "config/origins.yaml",
    pilot_config_path: str | Path = "config/pilot.yaml",
) -> dict[str, object]:
    """Build the experimental 200 m composition product under interim."""
    config = load_origins_config(config_path)
    options = config.downscale
    output = Path(config.report.output_directory)
    if not output.resolve().is_relative_to(
        Path(config.report.interim_directory).resolve()
    ):
        raise ValueError("composition outputs must stay under data/interim")
    output.mkdir(parents=True, exist_ok=True)
    year = options.output_year
    vintage = options.ff_vintage
    ff_cells = output / config.report.ff_cells_pattern.format(vintage=vintage)
    ff_natural = output / config.report.ff_natural_pattern.format(vintage=vintage)
    ff_metadata = output / config.report.metadata_pattern.format(vintage=vintage)
    for path in (ff_cells, ff_natural, ff_metadata):
        if not path.is_file():
            raise FileNotFoundError(path)
    ff_info = json.loads(ff_metadata.read_text(encoding="utf-8"))
    if (
        ff_info.get("second_home_source") != "hybrid_2024"
        or not ff_info.get("signature")
    ):
        raise ValueError("composition requires a signed hybrid FF build")
    benchmark = output / options.output_pattern.format(year=year)
    benchmark_metadata = output / options.metadata_pattern.format(year=year)
    pilot_signature = _file_signature(Path(pilot_config_path))
    benchmark_info = (
        json.loads(benchmark_metadata.read_text(encoding="utf-8"))
        if benchmark_metadata.is_file() else {}
    )
    if (
        not benchmark.is_file()
        or benchmark_info.get("ff_signature") != ff_info["signature"]
        or benchmark_info.get("pilot_signature") != pilot_signature
    ):
        build_origins_2021_200m(
            config_path=config_path, pilot_config_path=pilot_config_path
        )
    archive = Path(config.filosofi_natural_archive)
    inputs = (
        Path(config_path), Path(pilot_config_path), archive, ff_cells,
        ff_natural, ff_metadata, benchmark,
    )
    choice_path = output / options.crossval_choice_pattern.format(year=year)
    methods = load_method_choices(choice_path, options)
    reference_archive = (
        Path(config.filosofi_200m_archive) if "within" in methods.values() else None
    )
    signature = composition_input_signature(
        inputs, choice_path=choice_path, reference_archive=reference_archive
    )
    result_path = output / options.composition_output_pattern.format(year=year)
    report_path = output / options.composition_report_pattern.format(year=year)
    model_path = output / options.composition_model_pattern.format(year=year)
    metadata_path = output / options.composition_metadata_pattern.format(year=year)
    failure_path = output / options.composition_failures_pattern.format(year=year)
    checkpoint_dir = output / options.composition_checkpoint_pattern.format(year=year)
    state_path = checkpoint_dir / options.composition_checkpoint_state
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("signature") == signature and metadata.get("completed")
            and all(path.is_file() for path in (result_path, report_path, model_path))
        ):
            return {
                "output": str(result_path), "report": str(report_path), "cached": True,
                "natural_cells": metadata["natural_cells"], "ipf_failures": 0,
            }
    _write_json(metadata_path, {
        "signature": signature, "ff_signature": ff_info["signature"], "completed": False
    })
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, object] = {}
    if state_path.is_file():
        previous = json.loads(state_path.read_text(encoding="utf-8"))
        if previous.get("signature") == signature:
            state = previous
    connection, spill = open_restricted_connection(output)
    try:
        reports = dict(state.get("reports", {}))
        fallbacks = dict(state.get("fallbacks", {}))
        stage = checkpoint_dir / options.composition_stage_pattern.format(
            index=len(reports)
        )
        if state and stage.is_file():
            connection.execute(
                "CREATE TEMP TABLE _composition_origins AS "
                "SELECT * FROM read_parquet(?)",
                [str(stage)],
            )
        else:
            reports = {}
            connection.execute(
                "CREATE TEMP TABLE _composition_origins AS "
                "SELECT * FROM read_parquet(?)",
                [str(benchmark)],
            )
            fallbacks = apply_direct_weights(
                connection, ff_cells, options.cell_resolution_m
            )

        def checkpoint(current: dict[str, dict[str, object]]) -> None:
            stage_path = checkpoint_dir / options.composition_stage_pattern.format(
                index=len(current)
            )
            temporary = stage_path.with_suffix(".tmp.parquet")
            write_parquet(connection, "SELECT * FROM _composition_origins", temporary)
            temporary.replace(stage_path)
            _write_json(state_path, {
                "signature": signature, "reports": current, "fallbacks": fallbacks
            })
            if current:
                previous_stage = checkpoint_dir / (
                    options.composition_stage_pattern.format(index=len(current) - 1)
                )
                previous_stage.unlink(missing_ok=True)

        if not state or not stage.is_file():
            checkpoint(reports)
        with tempfile.TemporaryDirectory(
            prefix="filosofi_composition_", dir=output
        ) as directory:
            natural_csv = _extract_archive_member(
                archive, "carreaux_nivNaturel_met.csv", Path(directory)
            )
            reference_csv = None
            if reference_archive is not None:
                from landgrid.origins.validation import _extract_filosofi_200m

                reference_csv = _extract_filosofi_200m(
                    reference_archive, Path(directory)
                )
            reports = apply_models(
                connection, natural_csv, ff_natural, ff_cells, options,
                methods=methods, reference_200m=reference_csv,
                completed=reports, checkpoint=checkpoint,
            )
        output_columns = {
            row[0] for row in connection.execute(
                "DESCRIBE SELECT * FROM _composition_origins"
            ).fetchall()
        }
        age_variables = tuple(name for name in AGE_VARIABLES if name in output_columns)
        failures = balance_age_groups(
            connection, age_variables, tolerance=options.ipf_tolerance,
            max_iterations=options.ipf_max_iterations,
        )
        failure_table = pa.Table.from_pylist(
            [{"natural_cell_id": name, "reason": reason}
             for name, reason in failures.items()],
            schema=pa.schema([
                ("natural_cell_id", pa.string()), ("reason", pa.string())
            ]),
        )
        connection.register("_composition_failures", failure_table)
        try:
            temporary = failure_path.with_suffix(".tmp.parquet")
            write_parquet(connection, "SELECT * FROM _composition_failures", temporary)
            temporary.replace(failure_path)
        finally:
            connection.unregister("_composition_failures")
        report_path.write_text(_render_composition_report(
            reports, fallbacks, failures, config.report.count_suppression_threshold
        ), encoding="utf-8")
        _write_json(model_path, reports)
        if failures:
            raise RuntimeError(f"age consistency failed; see {failure_path}")
        _check_composition_totals(connection, benchmark, options.ipf_tolerance)
        natural_cell_count = int(connection.execute(
            "SELECT count(DISTINCT natural_cell_id) FROM _composition_origins"
        ).fetchone()[0])
        temporary = result_path.with_suffix(".tmp.parquet")
        write_parquet(connection, "SELECT * FROM _composition_origins", temporary)
        temporary.replace(result_path)
        _write_json(metadata_path, {
            "signature": signature, "ff_signature": ff_info["signature"],
            "completed": True, "natural_cells": natural_cell_count,
        })
        return {
            "output": str(result_path), "report": str(report_path), "cached": False,
            "natural_cells": natural_cell_count, "ipf_failures": 0,
        }
    finally:
        connection.close()
        spill.cleanup()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the experimental section-6.3 composition build."""
    parser = argparse.ArgumentParser(description="Build composition origins")
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    args = parser.parse_args(argv)
    from landgrid.origins.job import logged_job

    logging.basicConfig(level=logging.INFO)
    config = load_origins_config(args.config)
    with logged_job(
        Path(config.jobs.log_directory), config.jobs.composition_task,
        [config.filosofi_natural_archive, config.report.output_directory],
        config.report.count_suppression_threshold,
    ) as job:
        result = build_composition(
            config_path=args.config, pilot_config_path=args.pilot_config
        )
        job.outputs.extend((str(result["output"]), str(result["report"])))
        for key in ("natural_cells", "ipf_failures"):
            job.counts[key] = int(result[key])
    for key in ("natural_cells", "ipf_failures"):
        if int(result[key]) < config.report.count_suppression_threshold:
            result[key] = f"<{config.report.count_suppression_threshold}"
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
