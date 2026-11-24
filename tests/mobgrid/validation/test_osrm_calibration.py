from dataclasses import replace
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.graph.csr import csr_from_indexed_edges
from mobgrid.validation.osrm import load_query_settings
from mobgrid.validation.osrm_calibration import (
    CalibrationFit,
    adjusted_weights,
    arc_features,
    calibrate_car,
    factor_highways,
    fit_log_time_ratios,
    trace_routes,
)


def test_configured_calibration_bounds_cover_each_requested_class():
    settings = load_query_settings(
        Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
    ).calibration
    assert settings is not None
    assert settings.road_groups["motorway_trunk"].bounds == (0.8, 1.15)
    assert settings.road_groups["primary_tertiary"].bounds == (0.6, 1.15)
    assert settings.road_groups["local"].bounds == (0.4, 1.15)
    assert settings.control_bounds_s == {
        "signal_s": (0, 30),
        "stop_s": (0, 15),
        "give_way_s": (0, 10),
        "mini_roundabout_s": (0, 15),
        "at_to_node_s": (0, 10),
        "crossing_s": (0, 5),
    }
    assert len(factor_highways(settings)) == 13
    assert settings.uncertainty_fraction == 0.5


def test_log_ratio_fit_recovers_speed_factors_and_control_delays():
    rng = np.random.default_rng(42)
    cruise = rng.uniform(10, 300, size=(160, 3))
    controls = rng.integers(0, 10, size=(160, 6)).astype(float)
    fixed = rng.uniform(20, 200, size=160)
    expected = np.array([0.91, 0.83, 0.68, 16, 6, 3, 5, 2, 1], dtype=float)
    observed = fixed + (cruise / expected[:3]).sum(axis=1) + controls @ expected[3:]
    lower = np.array([0.8, 0.6, 0.4, 0, 0, 0, 0, 0, 0], dtype=float)
    upper = np.array([1.15, 1.15, 1.15, 30, 15, 10, 15, 10, 5], dtype=float)
    provisional = np.array([1, 1, 1, 15, 5, 2, 3, 2, 0], dtype=float)
    fit = fit_log_time_ratios(
        cruise,
        controls,
        fixed,
        observed,
        lower,
        upper,
        provisional,
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
    )
    np.testing.assert_allclose(fit.values, expected, rtol=2e-5, atol=2e-5)
    assert not fit.fixed.any()
    assert np.isfinite(fit.standard_errors).all()


def test_unidentifiable_parameter_is_fixed_at_provisional_value():
    rng = np.random.default_rng(5)
    cruise = rng.uniform(10, 100, size=(120, 1))
    first = rng.integers(1, 6, size=120).astype(float)
    controls = np.column_stack((first, first))
    fixed = np.full(120, 20.0)
    observed = fixed + cruise[:, 0] / 0.9 + first * 9
    result = fit_log_time_ratios(
        cruise,
        controls,
        fixed,
        observed,
        lower=np.array([0.8, 0, 0.0]),
        upper=np.array([1.15, 30, 15.0]),
        provisional=np.array([1.0, 5, 4]),
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
    )
    assert result.fixed[1:].sum() == 1
    np.testing.assert_array_equal(result.values[result.fixed], np.array([5.0]))
    assert np.isinf(result.fixed_standard_errors[result.fixed]).all()
    assert np.isnan(result.correlations[result.fixed]).all()


def test_imprecise_parameter_is_fixed_when_error_exceeds_half_range():
    rng = np.random.default_rng(16)
    cruise = rng.uniform(50, 200, size=(100, 1))
    controls = rng.uniform(0, 0.0001, size=(100, 1))
    fixed = np.full(100, 50.0)
    observed = (fixed + cruise[:, 0]) * np.exp(rng.normal(0, 0.1, size=100))
    result = fit_log_time_ratios(
        cruise,
        controls,
        fixed,
        observed,
        lower=np.array([0.8, 0]),
        upper=np.array([1.15, 30]),
        provisional=np.array([1.0, 15]),
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
    )
    assert result.fixed[1]
    assert result.values[1] == 15
    assert result.fixed_standard_errors[1] > 15


def test_refit_keeps_previously_fixed_parameters_at_provisional_values():
    cruise = np.linspace(20, 200, 80).reshape(-1, 1)
    observed = cruise[:, 0] / 0.9
    result = fit_log_time_ratios(
        cruise,
        np.empty((80, 0)),
        np.zeros(80),
        observed,
        lower=np.array([0.8]),
        upper=np.array([1.15]),
        provisional=np.array([1.0]),
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
        fixed_at_provisional=np.array([True]),
        fixed_standard_errors=np.array([np.inf]),
    )
    assert result.fixed[0]
    assert result.values[0] == 1
    assert np.isinf(result.fixed_standard_errors[0])


def test_speed_factor_respects_active_bound():
    cruise = np.linspace(20, 200, 80).reshape(-1, 1)
    observed = cruise[:, 0] / 0.6
    result = fit_log_time_ratios(
        cruise,
        np.empty((80, 0)),
        np.zeros(80),
        observed,
        lower=np.array([0.8]),
        upper=np.array([1.15]),
        provisional=np.array([1.0]),
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
    )
    assert result.values[0] == pytest.approx(0.8)
    assert not result.fixed[0]


def test_full_class_fit_converges_with_noise_and_bounded_controls():
    rng = np.random.default_rng(59)
    cruise = rng.uniform(10, 100, size=(300, 13))
    controls = rng.integers(0, 20, size=(300, 6)).astype(float)
    fixed = rng.uniform(10, 100, size=300)
    expected = np.array([0.95] * 13 + [16, 6, 3, 5, 2, 1])
    observed = (
        fixed + (cruise / expected[:13]).sum(axis=1) + controls @ expected[13:]
    ) * np.exp(rng.normal(0, 0.002, size=300))
    lower = np.array([0.8] * 13 + [0] * 6)
    upper = np.array([1.15] * 13 + [30, 15, 10, 15, 10, 5])
    provisional = np.array([1.0] * 13 + [15, 5, 2, 3, 2, 0])
    result = fit_log_time_ratios(
        cruise,
        controls,
        fixed,
        observed,
        lower,
        upper,
        provisional,
        uncertainty_fraction=0.5,
        max_iterations=200,
        tolerance=1e-8,
        max_backtracks=30,
    )
    predicted = (
        fixed
        + (cruise / result.values[:13]).sum(axis=1)
        + controls @ result.values[13:]
    )
    assert np.sqrt(np.mean(np.log(predicted / observed) ** 2)) < 0.003
    assert np.all(result.values >= lower)
    assert np.all(result.values <= upper)


def test_invalid_bounds_fail_explicitly():
    with pytest.raises(ValueError):
        fit_log_time_ratios(
            np.ones((3, 1)),
            np.ones((3, 1)),
            np.ones(3),
            np.ones(3),
            np.array([0, 0]),
            np.array([1, 1]),
            np.array([0.5, 0]),
            uncertainty_fraction=0.5,
            max_iterations=20,
            tolerance=1e-8,
            max_backtracks=10,
        )


def test_car_arc_features_follow_original_members_and_reject_stale_graph(tmp_path):
    settings = load_query_settings(
        Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
    ).calibration
    assert settings is not None
    graph = csr_from_indexed_edges(
        "car",
        np.array([10, 30, 40], dtype=np.int64),
        np.array([0, 1]),
        np.array([1, 2]),
        {
            "time_s": np.array([40, 35], dtype=np.float32),
            "distance_m": np.array([100, 100], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
        member_offsets=np.array([0, 2, 3], dtype=np.int64),
        member_edge_rows=np.array([0, 1, 2], dtype=np.int64),
    )
    pq.write_table(
        pa.table(
            {
                "edge_key": ["a", "b", "c"],
                "from_node_id": [10, 20, 30],
                "to_node_id": [20, 30, 40],
                "highway": ["primary", "primary", "residential"],
                "mode": ["car"] * 3,
                "signal_count": [1, 0, 0],
                "stop_count": [0, 0, 1],
                "give_way_count": [0, 0, 0],
                "mini_roundabout_count": [0, 0, 0],
                "crossing_count": [0, 0, 0],
                "to_degree": [2, 2, 2],
            }
        ),
        tmp_path / "edges.parquet",
    )
    pq.write_table(
        pa.table({"edge_key": ["a", "b", "c"], "car_time_s": [20.0, 20.0, 35.0]}),
        tmp_path / "costs.parquet",
    )
    features, values, _, _, names = arc_features(
        graph, tmp_path / "edges.parquet", tmp_path / "costs.parquet", settings
    )
    np.testing.assert_allclose(
        adjusted_weights(features, values, len(factor_highways(settings))), [40, 35]
    )
    assert features[0, 1 + names.index("primary")] == 25
    assert features[1, 1 + names.index("residential")] == 30
    pair = [{"pair_id": "p", "origin_node_id": 10, "destination_node_id": 40}]
    routes = trace_routes(graph, features, pair, cutoff_s=100, resolution_s=0.1)
    np.testing.assert_array_equal(routes[0]["path"], [0, 1])
    assert routes[0]["time_s"] == pytest.approx(75)
    np.testing.assert_allclose(routes[0]["features"], features.sum(axis=0))
    stale = replace(
        graph, weights={**graph.weights, "time_s": np.array([41, 35], dtype=np.float32)}
    )
    with pytest.raises(ValueError, match="graph"):
        arc_features(
            stale, tmp_path / "edges.parquet", tmp_path / "costs.parquet", settings
        )


def test_calibration_reroutes_once_then_refits_on_the_new_paths(tmp_path, monkeypatch):
    settings = load_query_settings(
        Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
    ).calibration
    assert settings is not None
    graph = csr_from_indexed_edges(
        "car",
        np.array([10, 20, 30, 40], dtype=np.int64),
        np.array([0, 0, 1, 2]),
        np.array([1, 2, 3, 3]),
        {
            "time_s": np.array([40, 50, 40, 50], dtype=np.float32),
            "distance_m": np.array([10, 20, 10, 20], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    count = len(factor_highways(settings))
    features = np.zeros((4, 1 + count + 6))
    features[[0, 2], 1] = 40
    features[[1, 3], 2] = 50
    initial = np.array([*np.ones(count), 15, 5, 2, 3, 2, 0])
    lower = np.array([0.8] * count + [0] * 6, dtype=float)
    upper = np.array([1.15] * count + [30, 15, 10, 15, 10, 5], dtype=float)
    first_values = initial.copy()
    first_values[:2] = [0.8, 1.15]
    refit_values = initial.copy()
    refit_values[:2] = [0.8, 1.0]
    values = [first_values, refit_values]
    feature_inputs = []
    fit_options = []

    def fake_fit(cruise, *args, **kwargs):
        feature_inputs.append(cruise.copy())
        fit_options.append(kwargs)
        chosen = values[(len(feature_inputs) - 1) % 2]
        fixed = np.zeros(len(chosen), dtype=bool)
        fixed[-1] = True
        errors = np.full(len(chosen), np.nan)
        errors[-1] = np.inf
        return CalibrationFit(
            chosen,
            np.zeros(len(chosen)),
            np.eye(len(chosen)),
            fixed,
            errors,
        )

    monkeypatch.setattr(
        "mobgrid.validation.osrm_calibration.fit_log_time_ratios", fake_fit
    )
    pairs = [
        {"pair_id": f"p{i}", "origin_node_id": 10, "destination_node_id": 40}
        for i in range(4)
    ]
    result = calibrate_car(
        graph,
        features,
        pairs,
        np.full(4, 90.0),
        initial,
        lower,
        upper,
        settings,
        cutoff_s=300,
        resolution_s=0.1,
        checkpoint_directory=tmp_path,
        checkpoint_key="abc",
    )
    assert len(feature_inputs) == 2
    assert fit_options[0]["fixed_at_provisional"] is None
    np.testing.assert_array_equal(
        fit_options[1]["fixed_at_provisional"], result["first_fit"].fixed
    )
    np.testing.assert_array_equal(
        fit_options[1]["fixed_standard_errors"],
        result["first_fit"].fixed_standard_errors,
    )
    np.testing.assert_array_equal(feature_inputs[0][:, :2], [[80, 0], [80, 0]])
    np.testing.assert_array_equal(feature_inputs[1][:, :2], [[0, 100], [0, 100]])
    assert result["changed_share"] == 1
    assert len(result["holdout"]) == 2
    assert all(row["provisional_time_s"] == 80 for row in result["holdout"])
    assert all(row["refit_time_s"] == pytest.approx(100) for row in result["holdout"])
    monkeypatch.setattr(
        "mobgrid.validation.osrm_calibration.trace_routes",
        lambda *args, **kwargs: pytest.fail("paths were not resumed"),
    )
    resumed = calibrate_car(
        graph,
        features,
        pairs,
        np.full(4, 90.0),
        initial,
        lower,
        upper,
        settings,
        cutoff_s=300,
        resolution_s=0.1,
        checkpoint_directory=tmp_path,
        checkpoint_key="abc",
    )
    assert resumed["changed_share"] == 1
