"""Synthetic acceptance tests for grouped origins cross-validation."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import pytest


def test_fold_partitions_keep_natural_cells_exclusive() -> None:
    from landgrid.origins.crossval import grouped_fold_partitions

    natural_cells = np.repeat(np.array([f"natural-{index}" for index in range(10)]), 3)
    partitions = grouped_fold_partitions(natural_cells, folds=5, seed=17)

    for partition in partitions:
        assert set(partition.training_groups).isdisjoint(partition.held_out_groups)
        assert set(partition.training_groups) | set(partition.held_out_groups) == set(
            natural_cells
        )


def test_choice_json_has_one_method_per_variable() -> None:
    from landgrid.origins.crossval import build_choice_payload

    medians = {
        variable: {
            "proportional": 0.12,
            "composition": 0.10,
            "within": 0.10,
        }
        for variable in ("ind", "ind_0_3", "men_1ind")
    }
    payload = build_choice_payload(
        year=2021,
        folds=5,
        seed=17,
        tie_tolerance=0.005,
        medians=medians,
        within_diagnostics={},
    )

    decoded = json.loads(json.dumps(payload))
    choices = decoded["chosen_methods"]
    assert set(choices) == set(medians)
    assert all(
        method in {"proportional", "composition", "within"}
        for method in choices.values()
    )


def test_synthetic_fold_scores_identical_non_imputed_holdouts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import landgrid.origins.crossval as crossval
    from landgrid.origins.composition import AGE_VARIABLES, COVARIATES, DIRECT_WEIGHTS
    from landgrid.origins.fichiers_fonciers import load_origins_config

    natural_rows = []
    natural_features = []
    baseline_rows = []
    ff_cell_rows = []
    reference_rows = []
    eurostat_rows = []
    cell_weights = (0.2, 0.3, 0.5)
    for group_index in range(10):
        northing = 2_400_000 + group_index * 2_000
        easting = 4_000_000
        natural_id = f"CRS3035RES1000mN{northing}E{easting}"
        individuals = 100.0 + 3 * group_index
        households = 30.0 + group_index
        controls = {
            "ind": individuals,
            "men_1ind": households * 0.2,
            "men_5ind": households * 0.1,
            "men_fmp": households * 0.05,
            "men_pauv": households * 0.25,
            "ind_snv": individuals * 10,
            **{name: individuals / len(AGE_VARIABLES) for name in AGE_VARIABLES},
        }
        direct_controls = {
            name: households * (0.1 + 0.01 * index)
            for index, name in enumerate(DIRECT_WEIGHTS)
        }
        natural_rows.append(
            {
                "idcar_nat": natural_id,
                "tmaille": 1000,
                "men": households,
                **controls,
            }
        )
        natural_features.append(
            {
                "natural_cell_id": natural_id,
                **dict.fromkeys(COVARIATES, 1.0),
            }
        )
        eurostat_rows.append(
            {
                "GRD_ID": natural_id,
                "T": 500.0,
                "LAND_SURFACE": 1.0,
            }
        )
        for cell_index, share in enumerate(cell_weights):
            cell_easting = easting + cell_index * 200
            cell_id = (northing // 200) * 100_000 + cell_easting // 200
            cell_code = f"CRS3035RES200mN{northing}E{cell_easting}"
            cell_counts = {name: value * share for name, value in controls.items()}
            direct_counts = {
                name: value * share for name, value in direct_controls.items()
            }
            baseline_rows.append(
                {
                    "cell_id": cell_id,
                    "natural_cell_id": natural_id,
                    "natural_cell_size_m": 1000,
                    "men": households * share,
                    **cell_counts,
                    **direct_counts,
                }
            )
            ff_cell_rows.append(
                {
                    "cell_id": cell_id,
                    **dict.fromkeys(COVARIATES, 1.0),
                    **{
                        weight: households * share for weight in DIRECT_WEIGHTS.values()
                    },
                }
            )
            reference_rows.append(
                {
                    "idcar_200m": cell_code,
                    "idcar_1km": natural_id,
                    "i_est_200": 0,
                    "lcog_geo": "33001",
                    "men": households * share,
                    **cell_counts,
                }
            )

    baseline_path = tmp_path / "baseline.parquet"
    ff_cells_path = tmp_path / "ff_cells.parquet"
    ff_natural_path = tmp_path / "ff_natural.parquet"
    natural_path = tmp_path / "natural.csv"
    reference_path = tmp_path / "reference.csv"
    eurostat_path = tmp_path / "eurostat.parquet"
    pq.write_table(pa.Table.from_pylist(baseline_rows), baseline_path)
    pq.write_table(pa.Table.from_pylist(ff_cell_rows), ff_cells_path)
    pq.write_table(pa.Table.from_pylist(natural_features), ff_natural_path)
    pq.write_table(pa.Table.from_pylist(eurostat_rows), eurostat_path)
    pacsv.write_csv(pa.Table.from_pylist(natural_rows), natural_path)
    pacsv.write_csv(pa.Table.from_pylist(reference_rows), reference_path)

    class ConstantRate:
        dispersion = 1.25
        zero_offset_count = 2

        @staticmethod
        def predict_rate(values: np.ndarray) -> np.ndarray:
            return np.ones(len(values), dtype=np.float64)

    monkeypatch.setattr(
        crossval,
        "fit_poisson",
        lambda *args, **kwargs: ConstantRate(),
    )
    monkeypatch.setattr(
        crossval,
        "fit_within_poisson",
        lambda *args, **kwargs: ConstantRate(),
    )
    options = load_origins_config().downscale

    with duckdb.connect() as connection:
        age_variables = crossval._create_input_tables(
            connection,
            baseline=baseline_path,
            natural=natural_path,
            ff_natural=ff_natural_path,
            ff_cells=ff_cells_path,
            insee_200m=reference_path,
            eurostat=eurostat_path,
            resolution_m=200,
            eurostat_resolution_m=1000,
            density_thresholds=(300, 1500),
            department="33",
        )
        natural_ids = np.array(
            [
                row[0]
                for row in connection.execute(
                    "SELECT natural_cell_id FROM _cv_base GROUP BY natural_cell_id"
                ).fetchall()
            ]
        )
        partition = crossval.grouped_fold_partitions(natural_ids, folds=5, seed=17)[0]
        diagnostics, scored_cells = crossval._run_fold(
            connection,
            partition=partition,
            age_variables=age_variables,
            ff_cells=ff_cells_path,
            downscale=options,
        )
        method_cells = connection.execute(
            """
            SELECT method, count(DISTINCT cell_id)
            FROM _cv_fold_observations
            WHERE variable = 'ind'
            GROUP BY method
            """
        ).fetchall()
        scored_groups = {
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT b.natural_cell_id
                FROM _cv_fold_observations o
                JOIN _cv_base b USING (cell_id)
                """
            ).fetchall()
        }
        fold_path = tmp_path / "fold_observations.parquet"
        pq.write_table(
            connection.execute("SELECT * FROM _cv_fold_observations").to_arrow_table(),
            fold_path,
        )
        medians, pooled_rows, stratum_rows = crossval._aggregate_observations(
            connection,
            fold_paths=[fold_path],
            tolerance_fraction=0.2,
        )
        choices = crossval.choose_methods(medians, tolerance=0.005)
        report = crossval._render_crossval_report(
            year=2021,
            department="33",
            pooled_rows=pooled_rows,
            stratum_rows=stratum_rows,
            choices=choices,
            count_threshold=50,
            tolerance_fraction=0.2,
        )
        summarized = crossval._summarize_within_diagnostics(
            {partition.fold: diagnostics}, threshold=50
        )

    assert scored_cells == 6
    assert dict(method_cells) == {
        "proportional": 6,
        "composition": 6,
        "within": 6,
    }
    assert scored_groups.issubset(partition.held_out_groups)
    assert scored_groups.isdisjoint(partition.training_groups)
    assert diagnostics["ind"]["dispersion"] == 1.25
    assert set(choices) == set(medians)
    assert "<50" in report
    assert "cell_id" not in report
    assert summarized["ind"]["zero_offset_training_cells_excluded"] == "<50"
