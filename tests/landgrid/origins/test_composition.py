"""Synthetic acceptance tests for experimental composition downscaling."""

import csv
import io
import json
import zipfile
from collections.abc import Callable
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml


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


def test_composition_build_writes_separate_output_and_reuses_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import landgrid.origins.composition as composition
    from landgrid.origins.composition import AGE_VARIABLES, COVARIATES
    from landgrid.origins.fichiers_fonciers import DownscaleConfig

    natural, ff_natural, cells, ff_cells = [], [], [], []
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
    output = tmp_path / "interim"
    output.mkdir()
    pq.write_table(pa.Table.from_pylist(cells), output / "origins_2021_200m.parquet")
    pq.write_table(pa.Table.from_pylist(ff_cells), output / "ff_cells_2022.parquet")
    pq.write_table(pa.Table.from_pylist(ff_natural), output / "ff_natural_2022.parquet")
    (output / "ff_cells_2022.json").write_text(
        json.dumps({"signature": "synthetic", "second_home_source": "hybrid_2024"})
    )
    (output / "origins_2021_200m.json").write_text(
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
    raw = yaml.safe_load(Path("config/origins.yaml").read_text(encoding="utf-8"))
    raw["report"]["output_directory"] = str(output)
    raw["filosofi"]["natural_archive"] = str(archive)
    config = tmp_path / "origins.yaml"
    config.write_text(yaml.safe_dump(raw), encoding="utf-8")
    baseline = (output / "origins_2021_200m.parquet").read_bytes()

    original = composition.apply_models

    def interrupt(
        connection: duckdb.DuckDBPyConnection,
        natural_input: pa.Table | Path,
        ff_natural_input: pa.Table | Path,
        ff_cells_input: pa.Table | Path,
        model_config: DownscaleConfig,
        *,
        completed: dict[str, dict[str, object]] | None = None,
        checkpoint: Callable[[dict[str, dict[str, object]]], None] | None = None,
    ) -> dict[str, dict[str, object]]:
        assert checkpoint is not None

        def interrupted_checkpoint(reports: dict[str, dict[str, object]]) -> None:
            assert checkpoint is not None
            checkpoint(reports)
            raise RuntimeError("simulated interruption")

        return original(
            connection, natural_input, ff_natural_input, ff_cells_input, model_config,
            completed=completed, checkpoint=interrupted_checkpoint,
        )

    monkeypatch.setattr(composition, "apply_models", interrupt)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        composition.build_composition(config_path=config)
    state = json.loads(
        (output / "composition_2021_checkpoint" / "state.json").read_text()
    )
    assert list(state["reports"]) == ["ind"]
    monkeypatch.setattr(composition, "apply_models", original)
    result = composition.build_composition(config_path=config)
    assert Path(result["output"]).is_file()
    assert (output / "origins_2021_200m.parquet").read_bytes() == baseline
    result_again = composition.build_composition(config_path=config)
    assert result_again["cached"] is True
    built = pq.read_table(result["output"]).to_pylist()
    assert built[0]["ind"] != built[1]["ind"]
    assert sum(built[0][name] for name in AGE_VARIABLES) == pytest.approx(
        built[0]["ind"], rel=1e-8
    )
