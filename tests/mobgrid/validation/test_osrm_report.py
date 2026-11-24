from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.graph.csr import csr_from_indexed_edges, save_graph
from mobgrid.validation import osrm, osrm_report
from mobgrid.validation.osrm_calibration import (
    CONTROL_NAMES,
    CalibrationFit,
    factor_highways,
)
from mobgrid.validation.osrm_report import calculate_metrics, route_pairs
from mobgrid.validation.osrm_sample import SampleSettings


def test_metrics_use_signed_model_minus_osrm_and_inclusive_thresholds():
    rows = [
        {
            "model_time_s": 120,
            "osrm_time_s": 120,
            "model_distance_m": 1200,
            "osrm_distance_m": 1000,
        },
        {
            "model_time_s": 420,
            "osrm_time_s": 300,
            "model_distance_m": 1600,
            "osrm_distance_m": 2000,
        },
        {
            "model_time_s": 600,
            "osrm_time_s": 900,
            "model_distance_m": 2700,
            "osrm_distance_m": 3000,
        },
    ]
    result = calculate_metrics(rows, (2, 5))
    assert result["count"] == 3
    assert result["bias_min"] == pytest.approx(-1)
    assert result["median_absolute_error_min"] == pytest.approx(2)
    assert result["within_first"] == pytest.approx(2 / 3)
    assert result["within_second"] == pytest.approx(1)
    assert result["relative_error"] == pytest.approx((0 + 0.4 - 1 / 3) / 3)
    assert result["distance_bias_m"] == pytest.approx(-500 / 3)
    assert result["distance_median_absolute_error_m"] == pytest.approx(300)


def test_routes_use_dial_distance_and_report_unreached_nodes():
    graph = csr_from_indexed_edges(
        "foot",
        np.array([10, 20, 30], dtype=np.int64),
        np.array([0, 1, 0]),
        np.array([1, 2, 2]),
        {
            "time_s": np.array([10.04, 10.04, 40], dtype=np.float32),
            "distance_m": np.array([100, 200, 80], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    pairs = [
        {"pair_id": "a", "origin_node_id": 10, "destination_node_id": 30},
        {"pair_id": "b", "origin_node_id": 30, "destination_node_id": 10},
    ]
    actual = route_pairs(graph, pairs, cutoff_s=30, resolution_s=0.1)
    assert actual[0]["model_time_s"] == pytest.approx(20)
    assert actual[0]["model_distance_m"] == pytest.approx(300)
    assert actual[1]["model_time_s"] is None
    assert actual[1]["model_distance_m"] is None


def test_missing_nodes_raise_instead_of_silently_excluding():
    graph = csr_from_indexed_edges(
        "foot",
        np.array([10, 20], dtype=np.int64),
        np.array([0]),
        np.array([1]),
        {
            "time_s": np.array([10], dtype=np.float32),
            "distance_m": np.array([1], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    with pytest.raises(ValueError, match="node"):
        route_pairs(
            graph,
            [{"pair_id": "a", "origin_node_id": 10, "destination_node_id": 99}],
            cutoff_s=20,
            resolution_s=0.1,
        )


def test_report_joins_dated_responses_and_resumes_routing(tmp_path, monkeypatch):
    graphs = tmp_path / "graphs"
    graphs.mkdir()
    pairs = []
    for mode in ("car", "bike", "foot"):
        graph = csr_from_indexed_edges(
            mode,
            np.array([10, 20], dtype=np.int64),
            np.array([0, 1]),
            np.array([1, 0]),
            {
                "time_s": np.array([120, 120], dtype=np.float32),
                "distance_m": np.array([1000, 1000], dtype=np.float32),
            },
            reference_mass_kg=74,
            bike_mass_kg=15,
        )
        save_graph(graph, graphs / f"{mode}.npz")
        pairs.append(
            {
                "pair_id": f"{mode}-1",
                "mode": mode,
                "origin_node_id": 10,
                "destination_node_id": 20,
                "origin_lon": 1.0,
                "origin_lat": 45.0,
                "destination_lon": 1.01,
                "destination_lat": 45.01,
                "context": "urban",
                "context_method": "tagged",
                "band_min_m": 0.0,
                "band_max_m": 2000.0,
            }
        )
    pairs.extend({**pairs[0], "pair_id": f"car-{i}"} for i in range(2, 5))
    pq.write_table(
        pa.table(
            {
                "edge_key": ["a", "b"],
                "mode": ["car", "car"],
                "from_node_id": [10, 20],
                "to_node_id": [20, 10],
                "highway": ["primary", "primary"],
                "signal_count": [0, 0],
                "stop_count": [0, 0],
                "give_way_count": [0, 0],
                "mini_roundabout_count": [0, 0],
                "crossing_count": [0, 0],
                "to_degree": [2, 2],
            }
        ),
        tmp_path / "edges.parquet",
    )
    pq.write_table(
        pa.table({"edge_key": ["a", "b"], "car_time_s": [120.0, 120.0]}),
        tmp_path / "costs.parquet",
    )
    sample_path = tmp_path / "pairs.parquet"
    pq.write_table(pa.Table.from_pylist(pairs), sample_path)
    search_path = tmp_path / "search.yaml"
    search_path.write_text(
        "queue: dial\ndial_resolution_s: 0.1\ntime_bin_s: 60\n"
        "distance_bin_m: 250\nenergy_bin_kj: 10\nnearest_extra: 2\n"
        "benchmark_seed: 42\nbenchmark_log_directory: logs\n"
        "cutoff_s_by_mode: {car: 300, bike: 300, foot: 300}\n",
        encoding="utf-8",
    )
    sample = SampleSettings(
        graph_directory=graphs,
        edges_path=tmp_path / "edges.parquet",
        edge_costs_path=tmp_path / "costs.parquet",
        nodes_path=tmp_path / "nodes.parquet",
        area_path=tmp_path / "area.parquet",
        search_config=search_path,
        seed=42,
        count_by_mode={"car": 4, "bike": 1, "foot": 1},
        band_edges_m=[0, 2000, 20000],
        bike_max_m=2000,
        long_car_min_m=20000,
        boundary_margin_m=10000,
        context_radius_m=500,
        attempts_per_stratum=100,
    )
    settings = osrm.QuerySettings(
        base_url_env="OSRM_BASE_URL",
        profile="driving",
        prefixes={"car": "routed-car", "bike": "routed-bike", "foot": "routed-foot"},
        user_agent="phd_model, ENTPE research",
        interval_s=1.1,
        policy_minimum_interval_s=1,
        retry_backoff_s=2,
        max_attempts=3,
        timeout_s=10,
        sample_path=sample_path,
        response_directory=tmp_path / "responses",
        log_directory=tmp_path / "logs",
        sampling=sample,
        report_path=tmp_path / "report.md",
        route_checkpoint_directory=tmp_path / "routing",
        calibration_checkpoint_directory=tmp_path / "calibration",
        metric_tolerances_min=(2, 5),
        calibration=osrm.load_query_settings(
            Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
        ).calibration,
    )
    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")
    for pair in pairs:
        url = osrm._request_url(pair, settings, "https://example.invalid")
        key = osrm._key(pair, url)
        path = settings.response_directory / "2026-01-01" / f"{key}_test.json"
        osrm._write_json(
            path,
            {
                "request_key": key,
                "http_status": 200,
                "response_date": "2026-01-01T00:00:00+00:00",
                "response": {
                    "code": "Ok",
                    "routes": [{"duration": 120, "distance": 900}],
                },
            },
        )
    osrm_report.generate_report(settings, "2026-01-01")
    report = settings.report_path.read_text(encoding="utf-8")
    assert "2026-01-01" in report
    assert all(mode in report for mode in ("car", "bike", "foot"))
    assert "0.00 | 0.00 | 100.0% | 100.0% | 0.0% | 100 | 100" in report
    assert "calibration" in report.lower()
    assert "### Holdout metrics" in report
    assert "First fit: parameter correlations" in report
    assert "Training pairs: 2; holdout pairs: 2" in report
    changed = {**pairs[0], "destination_lon": 2.0}
    with pytest.raises(ValueError, match="missing valid OSRM responses"):
        osrm_report._responses(settings, [changed])
    monkeypatch.setattr(
        osrm_report, "route_pairs", lambda *args, **kwargs: pytest.fail("not resumed")
    )
    monkeypatch.setattr(
        "mobgrid.validation.osrm_calibration.trace_routes",
        lambda *args, **kwargs: pytest.fail("calibration was not resumed"),
    )
    osrm_report.generate_report(settings, "2026-01-01")

    def fail_calibration(*args, **kwargs):
        raise ValueError("synthetic calibration failure")

    monkeypatch.setattr(osrm_report, "_car_calibration", fail_calibration)
    with pytest.raises(ValueError, match="synthetic calibration failure"):
        osrm_report.generate_report(settings, "2026-01-01")
    failure_report = settings.report_path.read_text(encoding="utf-8")
    assert "Failed: synthetic calibration failure" in failure_report
    assert "Within 2 min" in failure_report


def test_car_calibration_report_has_holdout_fits_and_correlations():
    settings = osrm.load_query_settings(
        Path(__file__).resolve().parents[3] / "config" / "osrm.yaml"
    )
    calibration = settings.calibration
    assert calibration is not None
    names = [*factor_highways(calibration), *CONTROL_NAMES]
    count = len(names)
    fixed = np.zeros(count, dtype=bool)
    fixed[1] = True
    fixed_errors = np.full(count, np.nan)
    fixed_errors[1] = np.inf
    fit = CalibrationFit(
        values=np.ones(count),
        standard_errors=np.where(fixed, np.nan, 0.01),
        correlations=np.eye(count),
        fixed=fixed,
        fixed_standard_errors=fixed_errors,
    )
    result = {
        "first_fit": fit,
        "refit": fit,
        "training_count": 2,
        "changed_share": 0.25,
        "holdout": [
            {
                "pair_id": "p",
                "provisional_time_s": 80,
                "provisional_distance_m": 1000,
                "first_time_s": 90,
                "first_distance_m": 900,
                "refit_time_s": 100,
                "refit_distance_m": 900,
                "path_changed": True,
            }
        ],
    }
    rows = [
        {
            "pair_id": "p",
            "context": "urban",
            "band_min_m": 0,
            "band_max_m": 2000,
            "osrm_time_s": 100,
            "osrm_distance_m": 900,
        }
    ]
    text = osrm_report.render_calibration(
        result, names, np.zeros(count), np.ones(count) * 30, rows, settings
    )
    assert "25.0%" in text
    assert "fixed" in text
    assert "unidentifiable" in text
    assert "correlation" in text.lower()
    assert all(stage in text for stage in ("Provisional", "First fit", "Refit"))
