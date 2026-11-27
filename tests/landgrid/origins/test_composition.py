"""Synthetic acceptance tests for experimental composition downscaling."""

import csv
import io
import json
import zipfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from landgrid.origins.composition import PoissonModel


def test_direct_weights_preserve_controls_and_count_household_fallbacks() -> None:
    from landgrid.origins.composition import apply_direct_weights

    controls = {
        "men_prop": 12.0, "men_mais": 9.0, "men_coll": 6.0,
        "log_soc": 3.0, "log_av45": 2.0, "log_45_70": 4.0,
        "log_70_90": 6.0, "log_ap90": 8.0, "log_inc": 10.0,
    }
    rows = [
        {"cell_id": 1, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "men": 2.0, **{key: value * 0.25 for key, value in controls.items()}},
        {"cell_id": 2, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "men": 6.0, **{key: value * 0.75 for key, value in controls.items()}},
    ]
    ff = pa.Table.from_pylist([
        {
            "cell_id": cell_id,
            "owner_occupied_main_residences": owner,
            "main_residence_houses": houses,
            "main_residence_flats": flats,
            "social_housing_main_residences": 0,
            "construction_av45": 0,
            "construction_45_70": 0,
            "construction_70_90": 0,
            "construction_ap90": 0,
            "construction_inc": 0,
        }
        for cell_id, owner, houses, flats in ((1, 3, 0, 1), (2, 1, 2, 1))
    ])
    with duckdb.connect() as connection:
        connection.register("benchmark", pa.Table.from_pylist(rows))
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM benchmark"
        )
        fallbacks = apply_direct_weights(connection, ff, 200)
        actual = connection.execute(
            "SELECT * FROM _composition_origins ORDER BY cell_id"
        ).to_arrow_table().to_pylist()
    assert actual[0]["men_prop"] == pytest.approx(9)
    assert actual[0]["men_mais"] == 0
    assert actual[0]["men_coll"] == pytest.approx(3)
    assert actual[0]["log_soc"] == pytest.approx(0.75)
    for key, total in controls.items():
        assert sum(row[key] for row in actual) == pytest.approx(total, rel=1e-9)
    assert fallbacks["log_soc"] == 1
    assert fallbacks["men_prop"] == 0


def test_weighted_poisson_fits_rates_and_reports_cross_validation() -> None:
    from landgrid.origins.composition import fit_poisson

    x = np.arange(20, dtype=float).reshape(-1, 1)
    households = np.linspace(2, 10, 20)
    y = households * np.exp(0.2 + 0.05 * x[:, 0])
    model = fit_poisson(
        x, y, households, households, ("density",), folds=5, seed=17,
        tolerance=1e-10, max_iterations=100,
    )
    assert model.predict_rate(x) == pytest.approx(
        np.exp(0.2 + 0.05 * x[:, 0]), rel=1e-6
    )
    assert model.deviance_explained == pytest.approx(1.0, abs=1e-8)
    assert len(model.cross_validation_errors) == 5
    assert max(model.cross_validation_errors) < 1e-6
    assert all(value >= 0 for value in model.standard_errors)


def test_poisson_imputes_missing_covariates_with_indicator() -> None:
    from landgrid.origins.composition import fit_poisson

    x = np.arange(20, dtype=float).reshape(-1, 1)
    x[0, 0] = np.nan
    y = np.linspace(5, 15, 20)
    model = fit_poisson(
        x, y, np.ones(20), np.ones(20), ("surface_median",), folds=5, seed=3,
        tolerance=1e-10, max_iterations=100,
    )
    assert model.missing_counts == {"surface_median": 1}
    assert "surface_median_missing" in model.feature_names
    assert np.isfinite(model.predict_rate(x)).all()


def test_within_poisson_recovers_split_despite_group_intercepts() -> None:
    from landgrid.origins.composition import fit_within_poisson

    x = np.tile(np.array([0.0, 1.0, 2.0]), 8)[:, None]
    exposure = np.tile(np.array([2.0, 4.0, 3.0]), 8)
    groups = np.repeat(np.arange(8), 3)
    intercepts = np.repeat(np.linspace(-1, 2, 8), 3)
    y = exposure * np.exp(intercepts + 0.6 * x[:, 0])
    model = fit_within_poisson(
        x, y, exposure, groups, ("x",), standardization_weights=exposure,
        tolerance=1e-10, max_iterations=100,
    )
    rates = model.predict_rate(x)
    assert rates[2] / rates[0] == pytest.approx(np.exp(1.2), rel=1e-7)
    assert model.dispersion == pytest.approx(0, abs=1e-12)
    assert np.isfinite(model.standard_errors).all()


def test_within_poisson_excludes_zero_offsets_and_reports_dispersion() -> None:
    from landgrid.origins.composition import fit_within_poisson

    x = np.tile(np.array([0.0, 1.0, 2.0]), 10)[:, None]
    groups = np.repeat(np.arange(10), 3)
    exposure = np.ones(30)
    exposure[0] = 0
    y = np.tile(np.array([1.0, 10.0, 3.0]), 10)
    model = fit_within_poisson(
        x, y, exposure, groups, ("x",), standardization_weights=exposure,
        tolerance=1e-10, max_iterations=100,
    )
    assert model.zero_offset_count == 1
    assert model.dispersion > 1
    assert np.all(model.standard_errors > 0)


def test_within_poisson_standardizes_using_household_weights() -> None:
    from landgrid.origins.composition import fit_within_poisson

    x = np.tile(np.array([0.0, 1.0, 2.0]), 8)[:, None]
    groups = np.repeat(np.arange(8), 3)
    households = np.tile(np.array([1.0, 2.0, 5.0]), 8)
    individuals = np.ones(24)
    model = fit_within_poisson(
        x, individuals * np.exp(0.3 * x[:, 0]), individuals, groups, ("x",),
        standardization_weights=households, tolerance=1e-10, max_iterations=100,
    )
    assert model.means[0] == pytest.approx(1.5)


def test_within_poisson_records_covariates_without_within_group_variation() -> None:
    from landgrid.origins.composition import fit_within_poisson

    groups = np.repeat(np.arange(8), 3)
    x = np.column_stack((np.tile([0.0, 1.0, 2.0], 8), groups, np.full(24, np.nan)))
    exposure = np.ones(len(groups))
    model = fit_within_poisson(
        x, exposure * np.exp(0.3 * x[:, 0]), exposure, groups,
        ("x", "group", "absent"),
        standardization_weights=exposure, tolerance=1e-10, max_iterations=100,
    )
    assert "x" in model.feature_names
    assert set(model.dropped_features) == {
        "group", "absent", "x_missing", "group_missing", "absent_missing"
    }


def test_method_choices_config_override_and_missing_file_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    from landgrid.origins.composition import load_method_choices
    from landgrid.origins.fichiers_fonciers import load_origins_config

    config = replace(
        load_origins_config().downscale,
        fixed_methods={"ind": "proportional", "ind_inc": "proportional"},
    )
    path = tmp_path / "choices.json"
    path.write_text(json.dumps({
        "year": config.output_year,
        "chosen_methods": {"ind": "within", "men_1ind": "within"},
    }))
    choices = load_method_choices(path, config)
    assert choices["ind"] == "proportional"
    assert choices["men_1ind"] == "within"
    assert choices["men_5ind"] == config.default_method
    path.unlink()
    choices = load_method_choices(path, config)
    assert choices["men_1ind"] == config.default_method
    assert "warning" in caplog.text.lower() or "missing" in caplog.text.lower()


def test_within_poisson_converges_with_weak_within_group_variation() -> None:
    """Section 6.3 experiment: convergence depends on conditional splits."""
    from landgrid.origins.composition import fit_within_poisson

    rng = np.random.default_rng(17)
    groups = np.repeat(np.arange(40), 4)
    exposure = rng.uniform(1, 30, len(groups))
    within = np.tile(np.array([-1.5, -0.5, 0.5, 1.5]), 40)
    x = (np.repeat(np.linspace(-2, 2, 40), 4) + 1e-6 * within)[:, None]
    y = exposure * np.exp(
        0.6 * within + np.repeat(np.linspace(-1, 1, 40), 4)
    )
    model = fit_within_poisson(
        x, y, exposure, groups, ("x",), standardization_weights=exposure,
        tolerance=1e-8, max_iterations=100,
    )
    centered = (x.reshape(-1, 4) - x.reshape(-1, 4).mean(axis=1)[:, None])
    rates = np.exp(centered * model.coefficients[0] / model.scales[0])
    weights = exposure.reshape(-1, 4) * rates
    predicted = (
        y.reshape(-1, 4).sum(axis=1)[:, None]
        * weights / weights.sum(axis=1)[:, None]
    )
    assert predicted == pytest.approx(y.reshape(-1, 4), rel=1e-8)
    assert np.isfinite(model.standard_errors).all()


def test_within_poisson_does_not_accept_separated_counts() -> None:
    """Section 6.3 experiment: a divergent fit must remain an error."""
    from landgrid.origins.composition import fit_within_poisson

    x = np.tile(np.array([0.0, 1.0, 2.0]), 8)[:, None]
    exposure = np.ones(len(x))
    y = np.tile(np.array([0.0, 0.0, 10.0]), 8)
    with pytest.raises(RuntimeError, match="within-cell Poisson did not converge"):
        fit_within_poisson(
            x, y, exposure, np.repeat(np.arange(8), 3), ("x",),
            standardization_weights=exposure, tolerance=1e-8, max_iterations=20,
        )


def test_within_poisson_line_search_is_stable_when_counts_are_rescaled() -> None:
    """Section 6.3 experiment: count scaling must not reject an improving fit."""
    from landgrid.origins.composition import fit_within_poisson

    rng = np.random.default_rng(2)
    groups = np.repeat(np.arange(80), 5)
    base = rng.normal(size=len(groups))
    x = np.column_stack((base, base + 1e-4 * rng.normal(size=len(groups))))
    exposure = rng.uniform(1, 30, len(groups))
    y = rng.poisson(exposure * np.exp(0.3 * base)).astype(float)
    models = [
        fit_within_poisson(
            x, y * multiplier, exposure, groups, ("a", "b"),
            standardization_weights=exposure, tolerance=1e-8, max_iterations=100,
        )
        for multiplier in (1.0, 1e6)
    ]
    assert models[1].predict_rate(x) == pytest.approx(
        models[0].predict_rate(x), rel=1e-7
    )
    assert np.isfinite(models[1].standard_errors).all()


@pytest.fixture
def guard_model() -> PoissonModel:
    return PoissonModel(
        input_names=("density",), means=np.zeros(1), scales=np.ones(1),
        selected=(0, 1), feature_names=("intercept", "density"),
        coefficients=np.array([12.0, 10.0]), standard_errors=np.zeros(2),
        deviance_explained=0.0, cross_validation_errors=(), missing_counts={},
    )


@pytest.mark.parametrize(
    "failure", ["nonconvergence", "singular", "bound", "uninformative"],
)
def test_regression_guard_reports_proportional_fallback(
    failure: str, caplog: pytest.LogCaptureFixture, guard_model: PoissonModel,
) -> None:
    """Section 6.3 experiment: unusable fits must explicitly use proportional."""
    from landgrid.origins.composition import guarded_regression_fit

    def fit() -> PoissonModel:
        if failure == "nonconvergence":
            raise RuntimeError("Poisson fitting did not converge")
        if failure == "singular":
            raise np.linalg.LinAlgError("Singular matrix")
        if failure == "uninformative":
            raise ValueError("no informative natural cells for within-cell Poisson")
        return replace(guard_model, coefficients=np.array([12.0, 10.01]))

    model, reason = guarded_regression_fit(
        fit, variable="ind", method="composition", coefficient_bound=10,
    )
    assert model is None
    assert reason
    assert "ind" in caplog.text
    assert "proportional" in caplog.text


def test_regression_guard_does_not_hide_invalid_inputs() -> None:
    from landgrid.origins.composition import guarded_regression_fit

    def fit() -> PoissonModel:
        raise ValueError("invalid Poisson fitting inputs")

    with pytest.raises(ValueError, match="invalid Poisson fitting inputs"):
        guarded_regression_fit(
            fit, variable="ind", method="composition", coefficient_bound=10,
        )


def test_regression_guard_accepts_bound_and_does_not_bound_intercept(
    guard_model: PoissonModel,
) -> None:
    from landgrid.origins.composition import guarded_regression_fit

    model, reason = guarded_regression_fit(
        lambda: guard_model, variable="ind_snv", method="composition",
        coefficient_bound=10,
    )
    assert model is guard_model
    assert reason is None


def test_regression_weights_use_the_specified_denominator_and_preserve_total() -> None:
    from landgrid.origins.composition import apply_regression_weights

    cells = pa.Table.from_pylist([
        {"cell_id": 1, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "ind": 8.0, "men": 1.0, "ind_0_3": 3.0},
        {"cell_id": 2, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "ind": 2.0, "men": 4.0, "ind_0_3": 7.0},
    ])
    rates = pa.Table.from_pylist([
        {"cell_id": 1, "rate": 1.0}, {"cell_id": 2, "rate": 2.0}
    ])
    with duckdb.connect() as connection:
        connection.register("cells", cells)
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM cells"
        )
        apply_regression_weights(connection, rates, "ind_0_3", "ind", 200)
        values = connection.execute(
            "SELECT ind_0_3 FROM _composition_origins ORDER BY cell_id"
        ).fetchall()
    assert values[0][0] == pytest.approx(20 / 3)
    assert values[1][0] == pytest.approx(10 / 3)


def test_fit_and_apply_composition_models_individuals_before_ages() -> None:
    from landgrid.origins.composition import (
        AGE_VARIABLES,
        COVARIATES,
        apply_models,
    )
    from landgrid.origins.fichiers_fonciers import load_origins_config

    natural, ff_natural, cells, ff_cells = [], [], [], []
    for i in range(12):
        zone = f"zone-{i}"
        x = i / 10
        men = 20.0
        ind = men * np.exp(0.1 + 0.1 * x)
        controls = {
            "ind": ind, "men": men, "men_1ind": men * 0.2,
            "men_5ind": men * 0.1, "men_fmp": men * 0.05,
            "men_pauv": men * 0.15, "ind_snv": ind * 100,
            **{name: ind / len(AGE_VARIABLES) for name in AGE_VARIABLES},
        }
        natural.append({"idcar_nat": zone, **controls})
        features = dict.fromkeys(COVARIATES, 1.0)
        features["main_residences_per_200m"] = x
        ff_natural.append({"natural_cell_id": zone, **features})
        for j in range(2):
            cell_id = i * 2 + j
            cells.append({
                "cell_id": cell_id, "natural_cell_id": zone,
                "natural_cell_size_m": 1000,
                **{name: value / 2 for name, value in controls.items()},
            })
            ff_cells.append({
                "cell_id": cell_id,
                **features,
                "main_residences_per_200m": x + j,
            })
    ff_natural.pop()
    natural.append({**natural[0], "idcar_nat": "outside-scope", "ind": 100000.0})
    ff_natural.append({**ff_natural[0], "natural_cell_id": "outside-scope"})
    with duckdb.connect() as connection:
        connection.register("cells", pa.Table.from_pylist(cells))
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM cells"
        )
        reports = apply_models(
            connection, pa.Table.from_pylist(natural),
            pa.Table.from_pylist(ff_natural), pa.Table.from_pylist(ff_cells),
            load_origins_config().downscale,
        )
        result = connection.execute(
            "SELECT * FROM _composition_origins ORDER BY cell_id"
        ).to_arrow_table().to_pylist()
    assert result[1]["ind"] > result[0]["ind"]
    assert result[1]["ind_0_3"] > result[0]["ind_0_3"]
    assert reports["ind"]["training_cell_count"] == 12
    assert reports["ind"]["training_missing_counts"]["owner_share"] == 1
    assert reports["ind_inc"]["method"] == "proportional"
    assert "coefficients" not in reports["ind_inc"]
    for row in result:
        assert row["ind_inc"] == pytest.approx(row["ind"] / len(AGE_VARIABLES))
    assert sum(row["ind"] for row in result[:2]) == pytest.approx(natural[0]["ind"])
    assert sum(row["ind_0_3"] for row in result[:2]) == pytest.approx(
        natural[0]["ind_0_3"]
    )
    assert set(reports) == {
        "ind", "men_1ind", "men_5ind", "men_fmp", "men_pauv", "ind_snv",
        *AGE_VARIABLES,
    }


def test_ipf_balances_both_margins_and_reports_infeasible_cells() -> None:
    from landgrid.origins.composition import balance_age_groups

    cells = pa.Table.from_pylist([
        {"cell_id": 1, "natural_cell_id": "valid", "ind": 8.0,
         "ind_0_3": 3.0, "ind_inc": 1.0},
        {"cell_id": 2, "natural_cell_id": "valid", "ind": 2.0,
         "ind_0_3": 3.0, "ind_inc": 3.0},
        {"cell_id": 3, "natural_cell_id": "invalid", "ind": 10.0,
         "ind_0_3": 6.0, "ind_inc": 1.0},
    ])
    with duckdb.connect() as connection:
        connection.register("cells", cells)
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM cells"
        )
        failures = balance_age_groups(
            connection, ("ind_0_3", "ind_inc"), tolerance=1e-10,
            max_iterations=1000,
        )
        rows = connection.execute(
            "SELECT * FROM _composition_origins ORDER BY cell_id"
        ).to_arrow_table().to_pylist()
    assert failures == {"invalid": "inconsistent age and individual totals"}
    assert rows[0]["ind_0_3"] + rows[0]["ind_inc"] == pytest.approx(8)
    assert rows[1]["ind_0_3"] + rows[1]["ind_inc"] == pytest.approx(2)
    assert rows[0]["ind_0_3"] + rows[1]["ind_0_3"] == pytest.approx(6)
    assert rows[0]["ind_inc"] + rows[1]["ind_inc"] == pytest.approx(4)
    assert rows[2]["ind_0_3"] == 6


def test_ipf_reports_nonconvergence_without_replacing_input() -> None:
    from landgrid.origins.composition import balance_age_groups

    cells = pa.Table.from_pylist([
        {"cell_id": 1, "natural_cell_id": "a", "ind": 8.0,
         "ind_0_3": 3.0, "ind_inc": 1.0},
        {"cell_id": 2, "natural_cell_id": "a", "ind": 2.0,
         "ind_0_3": 3.0, "ind_inc": 3.0},
    ])
    with duckdb.connect() as connection:
        connection.register("cells", cells)
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM cells"
        )
        failures = balance_age_groups(
            connection, ("ind_0_3", "ind_inc"), tolerance=1e-12, max_iterations=1
        )
        result = connection.execute(
            "SELECT ind_0_3 FROM _composition_origins ORDER BY cell_id"
        ).fetchall()
    assert failures == {"a": "IPF did not converge"}
    assert result == [(3.0,), (3.0,)]


@pytest.mark.parametrize(("year", "vintage"), [(None, 2022), (2019, 2021)])
def test_composition_build_writes_separate_output_and_reuses_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    year: int | None,
    vintage: int,
) -> None:
    import landgrid.origins.composition as composition
    from landgrid.origins.composition import AGE_VARIABLES, COVARIATES
    from landgrid.origins.fichiers_fonciers import DownscaleConfig

    natural, ff_natural, cells, ff_cells, reference = [], [], [], [], []
    direct = {
        "men_prop": 10.0, "men_mais": 10.0, "men_coll": 10.0,
        "log_soc": 2.0, "log_av45": 2.0, "log_45_70": 3.0,
        "log_70_90": 4.0, "log_ap90": 5.0, "log_inc": 6.0,
    }
    for i in range(12):
        zone = f"zone-{i}"
        x = i / 10
        ind = 20 * np.exp(0.1 + 0.1 * x)
        controls = {
            "ind": ind, "men": 20.0, "men_1ind": 4.0, "men_5ind": 2.0,
            "men_fmp": 1.0, "men_pauv": 3.0, "ind_snv": ind * 100,
            **direct, **{name: ind / len(AGE_VARIABLES) for name in AGE_VARIABLES},
        }
        natural.append({"idcar_nat": zone, **controls})
        features = dict.fromkeys(COVARIATES, 1.0)
        features["main_residences_per_200m"] = x
        ff_natural.append({"natural_cell_id": zone, **features})
        for j in range(2):
            cell_id = i * 2 + j
            cells.append({
                "cell_id": cell_id, "natural_cell_id": zone,
                "natural_cell_size_m": 1000,
                **{name: value / 2 for name, value in controls.items()},
            })
            ff_cells.append({
                "cell_id": cell_id, **features,
                "main_residences_per_200m": x + j,
                "owner_occupied_main_residences": 1, "main_residence_houses": 1,
                "main_residence_flats": 1, "social_housing_main_residences": 1,
                "construction_av45": 1, "construction_45_70": 1,
                "construction_70_90": 1, "construction_ap90": 1,
                "construction_inc": 1,
            })
            reference.append({
                "idcar_200m": f"CRS3035RES200mN0E{cell_id * 200}",
                "idcar_nat": zone, "ind": ind / 2,
                "i_est_200": 0, "men": 10.0,
                "men_1ind": 2.0 * np.exp(0.3 * j),
            })
    reference[0]["i_est_200"] = 1
    output_year = year or 2021
    output = tmp_path / "interim"
    output.mkdir()
    benchmark = output / f"origins_{output_year}_200m.parquet"
    pq.write_table(pa.Table.from_pylist(cells), benchmark)
    pq.write_table(
        pa.Table.from_pylist(ff_cells), output / f"ff_cells_{vintage}.parquet"
    )
    pq.write_table(
        pa.Table.from_pylist(ff_natural), output / f"ff_natural_{vintage}.parquet"
    )
    (output / f"ff_cells_{vintage}.json").write_text(
        json.dumps({
            "signature": "synthetic", "second_home_source": "hybrid_2024",
            "grid_year": output_year,
        })
    )
    (output / f"origins_{output_year}_200m.json").write_text(
        json.dumps({
            "ff_signature": "synthetic",
            "pilot_signature": composition._file_signature(Path("config/pilot.yaml")),
        })
    )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(natural[0]))
    writer.writeheader()
    writer.writerows(natural)
    archive = tmp_path / "natural.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("carreaux_nivNaturel_met.csv", buffer.getvalue())
    (tmp_path / "carreaux_nivNaturel_met.csv").write_text(
        buffer.getvalue(), encoding="utf-8", newline=""
    )
    reference_archive = tmp_path / "reference.zip"
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(reference[0]))
    writer.writeheader()
    writer.writerows(reference)
    with zipfile.ZipFile(reference_archive, "w") as zipped:
        zipped.writestr("carreaux_200m_met.csv", buffer.getvalue())
    (tmp_path / "carreaux_200m_met.csv").write_text(
        buffer.getvalue(), encoding="utf-8", newline=""
    )
    raw = yaml.safe_load(Path("config/origins.yaml").read_text(encoding="utf-8"))
    raw["report"]["interim_directory"] = str(output)
    raw["report"]["output_directory"] = str(output)
    raw["filosofi"]["natural_archive"] = str(archive)
    raw["filosofi"]["200m_archive"] = str(reference_archive)
    raw["filosofi"]["temporal_2019"]["natural_destination"] = str(tmp_path)
    raw["filosofi"]["temporal_2019"]["200m_destination"] = str(tmp_path)
    raw["downscale"]["fixed_methods"]["men_5ind"] = "proportional"
    choice_path = output / "composition_method_choice_2021.json"
    choice_path.write_text(json.dumps({
        "year": 2021, "chosen_methods": {"men_1ind": "within", "men_5ind": "within"}
    }))
    config = tmp_path / "origins.yaml"
    config.write_text(yaml.safe_dump(raw), encoding="utf-8")
    baseline = benchmark.read_bytes()

    original = composition.apply_models

    def interrupt(
        connection: duckdb.DuckDBPyConnection,
        natural_input: pa.Table | Path,
        ff_natural_input: pa.Table | Path,
        ff_cells_input: pa.Table | Path,
        model_config: DownscaleConfig,
        *,
        methods: dict[str, str] | None = None,
        reference_200m: pa.Table | Path | None = None,
        completed: dict[str, dict[str, object]] | None = None,
        checkpoint: Callable[[dict[str, dict[str, object]]], None] | None = None,
        cross_validate: bool = True,
    ) -> dict[str, dict[str, object]]:
        assert checkpoint is not None

        def interrupted_checkpoint(reports: dict[str, dict[str, object]]) -> None:
            assert checkpoint is not None
            checkpoint(reports)
            raise RuntimeError("simulated interruption")

        return original(
            connection, natural_input, ff_natural_input, ff_cells_input, model_config,
            methods=methods, reference_200m=reference_200m,
            completed=completed, checkpoint=interrupted_checkpoint,
            cross_validate=cross_validate,
        )

    monkeypatch.setattr(composition, "apply_models", interrupt)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        composition.build_composition(config_path=config, year=year)
    state = json.loads(
        (output / f"composition_{output_year}_checkpoint" / "state.json").read_text()
    )
    assert list(state["reports"]) == ["ind"]
    monkeypatch.setattr(composition, "apply_models", original)
    result = composition.build_composition(config_path=config, year=year)
    assert Path(result["output"]).is_file()
    assert benchmark.read_bytes() == baseline
    result_again = composition.build_composition(config_path=config, year=year)
    assert result_again["cached"] is True
    built = pq.read_table(result["output"]).to_pylist()
    reports = json.loads(
        (output / f"origins_{output_year}_composition_models.json").read_text()
    )
    assert reports["men_1ind"]["method"] == "within"
    assert reports["men_1ind"]["training_cell_count"] == 22
    assert reports["men_5ind"]["method"] == "proportional"
    assert len(reports["ind"]["cross_validation_weighted_mae"]) == (
        0 if year == 2019 else 5
    )
    assert built[1]["men_1ind"] > built[0]["men_1ind"]
    assert sum(row["men_1ind"] for row in built[:2]) == pytest.approx(4.0)
    text = (output / f"origins_{output_year}_composition_report.md").read_text()
    assert "Dispersion:" in text and "Dropped features:" in text
    assert built[0]["ind"] != built[1]["ind"]
    assert sum(built[0][name] for name in AGE_VARIABLES) == pytest.approx(
        built[0]["ind"], rel=1e-8
    )
    choice_path.write_text(json.dumps({
        "year": 2021, "chosen_methods": {"men_1ind": "proportional"}
    }))
    rebuilt = composition.build_composition(config_path=config, year=year)
    assert rebuilt["cached"] is False
    rebuilt_reports = json.loads(
        (output / f"origins_{output_year}_composition_models.json").read_text()
    )
    assert rebuilt_reports["men_1ind"]["method"] == "proportional"
    if year == 2019:
        choice_path.unlink()
        with pytest.raises(FileNotFoundError):
            composition.build_composition(config_path=config, year=year)
