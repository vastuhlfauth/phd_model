"""Section 13 baseline graph-routing metrics against dated OSRM responses."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
import numpy as np
import pyarrow.parquet as pq

from mobgrid.graph.config import load_search_config
from mobgrid.graph.csr import MODES, CSRGraph, load_graph
from mobgrid.graph.dijkstra import SearchWorkspace, search

if TYPE_CHECKING:
    from mobgrid.validation.osrm import QuerySettings


def calculate_metrics(
    rows: list[dict], tolerances_min: tuple[float, float]
) -> dict[str, float | int]:
    """Return signed model-minus-OSRM errors in minutes, metres and ratios."""
    if not rows:
        raise ValueError("metrics require at least one matched route")
    if not (
        len(tolerances_min) == 2
        and all(np.isfinite(value) for value in tolerances_min)
        and 0 < tolerances_min[0] < tolerances_min[1]
    ):
        raise ValueError("metric tolerances must be finite, positive and increasing")
    model_time = np.asarray([row["model_time_s"] for row in rows], dtype=float)
    osrm_time = np.asarray([row["osrm_time_s"] for row in rows], dtype=float)
    model_distance = np.asarray([row["model_distance_m"] for row in rows], dtype=float)
    osrm_distance = np.asarray([row["osrm_distance_m"] for row in rows], dtype=float)
    if (
        not all(
            np.isfinite(array).all()
            for array in (model_time, osrm_time, model_distance, osrm_distance)
        )
        or np.any(osrm_time <= 0)
        or np.any(osrm_distance <= 0)
        or np.any(model_time < 0)
        or np.any(model_distance < 0)
    ):
        raise ValueError("routing metrics require finite positive OSRM costs")
    time_error = model_time - osrm_time
    distance_error = model_distance - osrm_distance
    return {
        "count": len(rows),
        "bias_min": float(np.mean(time_error) / 60),
        "median_absolute_error_min": float(np.median(np.abs(time_error)) / 60),
        "within_first": float(np.mean(np.abs(time_error) <= tolerances_min[0] * 60)),
        "within_second": float(np.mean(np.abs(time_error) <= tolerances_min[1] * 60)),
        "relative_error": float(np.mean(time_error / osrm_time)),
        "distance_bias_m": float(np.mean(distance_error)),
        "distance_median_absolute_error_m": float(np.median(np.abs(distance_error))),
    }


def route_pairs(
    graph: CSRGraph, pairs: list[dict], cutoff_s: float, resolution_s: float
) -> list[dict]:
    """Search directed node pairs by Dial; distances are metres, times seconds."""
    if cutoff_s <= 0 or resolution_s <= 0:
        raise ValueError("Dial cutoff and resolution must be positive")
    if len(graph.node_ids) and np.any(np.diff(graph.node_ids) <= 0):
        raise ValueError("graph node IDs must be strictly increasing")
    workspace = SearchWorkspace(
        graph, ("distance_m",), max_dial_ticks=int(np.ceil(cutoff_s / resolution_s))
    )
    results = []
    for pair in pairs:
        ids = np.asarray(
            [pair["origin_node_id"], pair["destination_node_id"]], dtype=np.int64
        )
        indices = np.searchsorted(graph.node_ids, ids)
        if np.any(indices >= len(graph.node_ids)) or not np.array_equal(
            graph.node_ids[indices], ids
        ):
            raise ValueError(f"{graph.mode}: sample node is absent from graph")
        origin, destination = indices
        result = search(
            graph,
            workspace,
            np.asarray([origin], dtype=np.int64),
            np.asarray([0.0]),
            cutoff_s,
            queue="dial",
            resolution_s=resolution_s,
        )
        reached = workspace.settled_stamps[destination] == result.generation
        results.append(
            {
                "pair_id": pair["pair_id"],
                "model_time_s": (
                    float(workspace.times[destination] * result.scale)
                    if reached
                    else None
                ),
                "model_distance_m": (
                    float(workspace.secondary[destination, 0]) if reached else None
                ),
            }
        )
    return results


def _checkpoint_key(
    sample_path: Path, graph_path: Path, mode: str, cutoff: float, resolution: float
) -> str:
    inputs = []
    for path in (sample_path, graph_path):
        stat = path.stat()
        inputs.append([str(path.resolve()), stat.st_size, stat.st_mtime_ns])
    value = [1, inputs, mode, cutoff, resolution]
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def _responses(settings: QuerySettings, pairs: list[dict]) -> dict[str, dict]:
    from mobgrid.validation.osrm import (
        _base_url,
        _key,
        _request_url,
        _unreachable_response,
        _valid_response,
    )

    base = _base_url(settings)
    expected = {_key(pair, _request_url(pair, settings, base)): pair for pair in pairs}
    records: dict[str, dict] = {}
    for path in settings.response_directory.glob("*/*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        key = record.get("request_key")
        if key not in expected:
            continue
        if not (
            record.get("http_status") == 200 and _valid_response(record.get("response"))
        ) and not _unreachable_response(
            record.get("http_status"), record.get("response")
        ):
            continue
        if not isinstance(record.get("response_date"), str):
            raise ValueError(f"OSRM response has no date: {path}")
        if (
            key not in records
            or record["response_date"] > records[key]["response_date"]
        ):
            records[key] = record
    missing = len(expected) - len(records)
    if missing:
        raise ValueError(f"missing valid OSRM responses for {missing} sample pairs")
    return {str(expected[key]["pair_id"]): record for key, record in records.items()}


def _render(
    rows: list[dict], settings: QuerySettings, calibration_section: str | None = None
) -> str:
    if settings.metric_tolerances_min is None or settings.max_snap_distance_m is None:
        raise ValueError("metric tolerances and snapping limit are required")
    tolerances = settings.metric_tolerances_min
    groups: dict[tuple, list[dict]] = defaultdict(list)
    origin_methods = {}
    for row in rows:
        groups[
            (row["mode"], row["band_min_m"], row["band_max_m"], row["context"])
        ].append(row)
        origin_methods[(row["mode"], row["origin_node_id"])] = row["context_method"]
    dates = sorted(row["response_date"] for row in rows)
    versions = sorted(
        {
            str(row["data_version"])
            for row in rows
            if row.get("data_version") is not None
        }
    )
    lines = [
        "# Step 6: OSRM routing check",
        "",
        "OSRM responses use current server data; the model graphs are from 2021.",
        f"Response dates (UTC): {dates[0]} to {dates[-1]}.",
        f"Server data versions: {', '.join(versions) if versions else 'not provided'}.",
        "This is the full-network baseline, not the grid-variant or accessibility "
        "rank-correlation validation.",
        "",
        "Errors are model minus OSRM; relative error is the mean signed time "
        "difference divided by OSRM time. Time shares include the stated boundary.",
        "NoRoute, NoSegment and pairs snapped beyond the configured limit are "
        "excluded from metrics and calibration. Eligible routes not reached within "
        "the Dial cutoff are excluded from metrics.",
        "",
        "| Mode | Band (km) | Context | Matched | Cutoff | NoRoute | NoSegment | "
        "Over snap limit | Bias (min) | "
        f"Median abs (min) | Within {tolerances[0]:g} min | "
        f"Within {tolerances[1]:g} min | Relative error | "
        "Distance bias (m) | Median abs distance (m) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (mode, lower, upper, context), values in sorted(groups.items()):
        eligible = [row for row in values if row["eligible"]]
        reached = [row for row in eligible if row["model_time_s"] is not None]
        prefix = (
            f"| {mode} | {lower / 1000:g}-{upper / 1000:g} | {context} | "
            f"{len(reached)} | {len(eligible) - len(reached)} | "
            f"{sum(row['outcome'] == 'NoRoute' for row in values)} | "
            f"{sum(row['outcome'] == 'NoSegment' for row in values)} | "
            f"{sum(row['over_snap'] for row in values)} | "
        )
        if not reached:
            lines.append(prefix + "— | — | — | — | — | — | — |")
            continue
        m = calculate_metrics(reached, tolerances)
        lines.append(
            prefix
            + f"{m['bias_min']:.2f} | {m['median_absolute_error_min']:.2f} | "
            + f"{m['within_first']:.1%} | {m['within_second']:.1%} | "
            + f"{m['relative_error']:.1%} | {m['distance_bias_m']:.0f} | "
            + f"{m['distance_median_absolute_error_m']:.0f} |"
        )
    lines.extend(
        [
            "",
            "## OSRM unreachable pairs",
            "",
            "Our route time is in seconds; not reached means outside the Dial cutoff.",
            "",
            "| Pair ID | Mode | Band (km) | Context | Outcome | Origin (lon, lat) | "
            "Destination (lon, lat) | Our time (s) |",
            "|---|---|---|---|---|---|---|---:|",
        ]
    )
    for row in rows:
        if row["outcome"] not in ("NoRoute", "NoSegment"):
            continue
        route_time = (
            f"{row['model_time_s']:.1f}"
            if row["model_time_s"] is not None
            else "not reached"
        )
        lines.append(
            f"| {row['pair_id']} | {row['mode']} | "
            f"{row['band_min_m'] / 1000:g}-{row['band_max_m'] / 1000:g} | "
            f"{row['context']} | {row['outcome']} | "
            f"{row['origin_lon']}, {row['origin_lat']} | "
            f"{row['destination_lon']}, {row['destination_lat']} | {route_time} |"
        )
    lines.extend(
        [
            "",
            "## OSRM snapping distances",
            "",
            f"Limit: {settings.max_snap_distance_m:g} m at either endpoint. "
            "Distribution pools both endpoints of all successful routes, "
            "including over-limit pairs.",
            "",
            "| Mode | Successful pairs | Over limit | Endpoint distances | "
            "Minimum (m) | Median (m) | P90 (m) | Maximum (m) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for mode in MODES:
        successful = [
            row for row in rows if row["mode"] == mode and row["outcome"] == "Ok"
        ]
        if not successful:
            lines.append(f"| {mode} | 0 | 0 | 0 | — | — | — | — |")
            continue
        distances = [
            distance for row in successful for distance in row["snap_distances_m"]
        ]
        minimum, median, p90, maximum = np.percentile(distances, [0, 50, 90, 100])
        over_limit = sum(row["over_snap"] for row in successful)
        lines.append(
            f"| {mode} | {len(successful)} | {over_limit} | {len(distances)} | "
            f"{minimum:.2f} | {median:.2f} | {p90:.2f} | {maximum:.2f} |"
        )
    lines.extend(["", "## Origin context provenance", ""])
    for mode in MODES:
        values = [value for (m, _), value in origin_methods.items() if m == mode]
        if values:
            shares = ", ".join(
                f"{method}: {values.count(method) / len(values):.1%}"
                for method in ("tagged", "density", "beyond")
            )
            lines.append(f"- {mode}: {len(values)} distinct origins; {shares}.")
    lines.extend(
        [
            "",
            calibration_section
            or "## Car calibration\n\nPending: fitted values have not been computed.",
            "",
            f"Sample: {settings.sample_path}.",
            f"Responses: {settings.response_directory}.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_calibration(
    result: dict,
    names: list[str],
    lower: np.ndarray,
    upper: np.ndarray,
    rows: list[dict],
    settings: QuerySettings,
) -> str:
    """Render two fits, uncertainty, correlations and stratified holdout metrics."""
    if settings.calibration is None or settings.metric_tolerances_min is None:
        raise ValueError("calibration settings and metric tolerances are required")
    config = settings.calibration
    holdout = result["holdout"]
    lines = [
        "## Car calibration",
        "",
        f"Training pairs: {result['training_count']}; holdout pairs: {len(holdout)}.",
        "Changed paths among all pairs after first fit: "
        f"{result['changed_share']:.1%}.",
        "The first fit uses provisional paths. Both sets are rerouted once, then "
        "refit paths remain fixed for the final holdout metrics.",
        "The fit uses unrounded arc components; reported path times use Dial rounding.",
        "No network configuration was modified; fitted values require approval.",
        "Standard errors and correlations use the linearized log-ratio least-squares "
        "Jacobian; uncertainties at active bounds are approximate.",
        "Unidentifiable parameters or those with standard error over "
        f"{config.uncertainty_fraction:.0%} of their bound range were fixed "
        "at their provisional value.",
        f"Unfitted road classes (factor 1): {', '.join(config.fixed_highways)}.",
    ]
    for label, key in (("First fit", "first_fit"), ("Refit", "refit")):
        fit = result[key]
        lines.extend(
            [
                "",
                f"### {label}: parameters",
                "",
                "| Parameter | Value | Standard error | Bounds | Status |",
                "|---|---:|---:|---|---|",
            ]
        )
        for index, name in enumerate(names):
            if fit.fixed[index]:
                reason = (
                    "unidentifiable"
                    if np.isinf(fit.fixed_standard_errors[index])
                    else f"SE {fit.fixed_standard_errors[index]:.4g} > configured limit"
                )
                status = f"fixed at provisional ({reason})"
                error = "—"
            else:
                status = "fitted"
                error = f"{fit.standard_errors[index]:.4g}"
            lines.append(
                f"| {name} | {fit.values[index]:.4g} | {error} | "
                f"{lower[index]:g}–{upper[index]:g} | {status} |"
            )
        lines.extend(
            [
                "",
                f"### {label}: parameter correlations",
                "",
                "| Parameter | " + " | ".join(names) + " |",
                "|---|" + "---:|" * len(names),
            ]
        )
        for index, name in enumerate(names):
            values = [
                f"{value:.3f}" if np.isfinite(value) else "—"
                for value in fit.correlations[index]
            ]
            lines.append(f"| {name} | " + " | ".join(values) + " |")
    by_id = {row["pair_id"]: row for row in rows}
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for route in holdout:
        original = by_id[route["pair_id"]]
        combined = {**original, **route}
        groups[("all", 0.0, 0.0)].append(combined)
        groups[
            (original["context"], original["band_min_m"], original["band_max_m"])
        ].append(combined)
    tolerances = settings.metric_tolerances_min
    lines.extend(
        [
            "",
            "### Holdout metrics",
            "",
            "| Stage | Band (km) | Context | Pairs | Bias (min) | Median abs (min) | "
            f"Within {tolerances[0]:g} min | Within {tolerances[1]:g} min | "
            "Relative error | Distance bias (m) | Median abs distance (m) |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for stage, prefix in (
        ("Provisional", "provisional"),
        ("First fit", "first"),
        ("Refit", "refit"),
    ):
        for (context, lower_band, upper_band), values in sorted(groups.items()):
            comparisons = [
                {
                    "model_time_s": row[f"{prefix}_time_s"],
                    "model_distance_m": row[f"{prefix}_distance_m"],
                    "osrm_time_s": row["osrm_time_s"],
                    "osrm_distance_m": row["osrm_distance_m"],
                }
                for row in values
            ]
            metric = calculate_metrics(comparisons, tolerances)
            band = (
                "all"
                if context == "all"
                else f"{lower_band / 1000:g}–{upper_band / 1000:g}"
            )
            lines.append(
                f"| {stage} | {band} | {context} | {metric['count']} | "
                f"{metric['bias_min']:.2f} | "
                f"{metric['median_absolute_error_min']:.2f} | "
                f"{metric['within_first']:.1%} | {metric['within_second']:.1%} | "
                f"{metric['relative_error']:.1%} | {metric['distance_bias_m']:.0f} | "
                f"{metric['distance_median_absolute_error_m']:.0f} |"
            )
    return "\n".join(lines)


def _calibration_cache_key(
    settings: QuerySettings, cutoff: float, resolution: float, pair_ids: list[str]
) -> str:
    if settings.sampling is None or settings.calibration is None:
        raise ValueError("calibration and sampling settings are required")
    sampling, calibration = settings.sampling, settings.calibration
    paths = (
        settings.sample_path,
        sampling.graph_directory / "car.npz",
        sampling.edges_path,
        sampling.edge_costs_path,
        sampling.search_config,
        calibration.network_config,
    )
    inputs = []
    for path in paths:
        stat = path.stat()
        inputs.append([str(path.resolve()), stat.st_size, stat.st_mtime_ns])
    value = [
        2,
        inputs,
        calibration.model_dump(mode="json"),
        cutoff,
        resolution,
        pair_ids,
    ]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _car_calibration(rows: list[dict], settings: QuerySettings) -> str:
    from mobgrid.validation.osrm_calibration import arc_features, calibrate_car

    if (
        settings.sampling is None
        or settings.calibration is None
        or settings.calibration_checkpoint_directory is None
    ):
        raise ValueError("calibration settings and checkpoint directory are required")
    sampling = settings.sampling
    search_settings = load_search_config(sampling.search_config)
    cutoff = search_settings.cutoff_s_by_mode["car"]
    if cutoff is None:
        raise ValueError("car search cutoff is not configured")
    graph = load_graph(sampling.graph_directory / "car.npz")
    features, initial, lower, upper, names = arc_features(
        graph, sampling.edges_path, sampling.edge_costs_path, settings.calibration
    )
    car_rows = [row for row in rows if row["mode"] == "car" and row["eligible"]]
    result = calibrate_car(
        graph,
        features,
        car_rows,
        np.asarray([row["osrm_time_s"] for row in car_rows], dtype=np.float64),
        initial,
        lower,
        upper,
        settings.calibration,
        cutoff_s=cutoff,
        resolution_s=search_settings.dial_resolution_s,
        checkpoint_directory=settings.calibration_checkpoint_directory,
        checkpoint_key=_calibration_cache_key(
            settings,
            cutoff,
            search_settings.dial_resolution_s,
            [row["pair_id"] for row in car_rows],
        ),
    )
    return render_calibration(result, names, lower, upper, car_rows, settings)


def _write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.md")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def generate_report(settings: QuerySettings, date: str) -> None:
    """Write baseline metrics and dated logs; reuse matching mode-route checkpoints."""
    from mobgrid.validation.osrm import _snap_distances, _write_json

    if (
        settings.sampling is None
        or settings.report_path is None
        or settings.route_checkpoint_directory is None
        or settings.metric_tolerances_min is None
        or settings.max_snap_distance_m is None
    ):
        raise ValueError("sampling, report path and route checkpoint path are required")
    sampling = settings.sampling
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    settings.route_checkpoint_directory.mkdir(parents=True, exist_ok=True)
    log_path = settings.log_directory / f"{date}_osrm_report.log"
    summary_path = settings.log_directory / f"{date}_osrm_report_summary.md"
    started = time.perf_counter()
    error = ""
    rows: list[dict] = []
    try:
        pairs = pq.read_table(settings.sample_path).to_pylist()
        if len({pair["pair_id"] for pair in pairs}) != len(pairs):
            raise ValueError("sample contains duplicate pair IDs")
        if any(
            sum(pair["mode"] == mode for pair in pairs) != sampling.count_by_mode[mode]
            for mode in MODES
        ) or len(pairs) != sum(sampling.count_by_mode.values()):
            raise ValueError("sample mode counts differ from the configured sizes")
        responses = _responses(settings, pairs)
        search_settings = load_search_config(sampling.search_config)
        for mode in MODES:
            cutoff = search_settings.cutoff_s_by_mode[mode]
            if cutoff is None:
                raise ValueError(f"{mode} search cutoff is not configured")
            graph_path = sampling.graph_directory / f"{mode}.npz"
            key = _checkpoint_key(
                settings.sample_path,
                graph_path,
                mode,
                cutoff,
                search_settings.dial_resolution_s,
            )
            checkpoint = settings.route_checkpoint_directory / f"{mode}_{key}.json"
            mode_pairs = [pair for pair in pairs if pair["mode"] == mode]
            if checkpoint.exists():
                routed = json.loads(checkpoint.read_text(encoding="utf-8"))
            else:
                graph = load_graph(graph_path)
                if graph.mode != mode:
                    raise ValueError(f"unexpected mode in {mode} graph")
                routed = route_pairs(
                    graph, mode_pairs, cutoff, search_settings.dial_resolution_s
                )
                _write_json(checkpoint, routed)
            route_by_id = {row["pair_id"]: row for row in routed}
            if set(route_by_id) != {pair["pair_id"] for pair in mode_pairs}:
                raise ValueError(f"invalid {mode} routing checkpoint")
            for pair in mode_pairs:
                record = responses[pair["pair_id"]]
                response = record["response"]
                outcome = response["code"]
                distances = _snap_distances(response) if outcome == "Ok" else None
                over_snap = (
                    any(
                        distance > settings.max_snap_distance_m
                        for distance in distances
                    )
                    if distances is not None
                    else False
                )
                rows.append(
                    {
                        **pair,
                        **route_by_id[pair["pair_id"]],
                        "outcome": outcome,
                        "snap_distances_m": distances,
                        "over_snap": over_snap,
                        "eligible": outcome == "Ok" and not over_snap,
                        "osrm_time_s": response["routes"][0]["duration"]
                        if outcome == "Ok"
                        else None,
                        "osrm_distance_m": response["routes"][0]["distance"]
                        if outcome == "Ok"
                        else None,
                        "response_date": record["response_date"],
                        "data_version": response.get("data_version"),
                    }
                )
        calibration_section = None
        if settings.calibration is not None:
            try:
                calibration_section = _car_calibration(rows, settings)
            except (
                ValueError,
                OSError,
                RuntimeError,
                duckdb.Error,
                np.linalg.LinAlgError,
            ) as exc:
                _write_report(
                    settings.report_path,
                    _render(rows, settings, f"## Car calibration\n\nFailed: {exc}"),
                )
                raise
        _write_report(
            settings.report_path, _render(rows, settings, calibration_section)
        )
    except (
        ValueError,
        OSError,
        RuntimeError,
        duckdb.Error,
        np.linalg.LinAlgError,
    ) as exc:
        error = str(exc)
        raise
    finally:
        lines = [
            "# OSRM routing report",
            "",
            f"- Sample: {settings.sample_path}",
            f"- Responses: {settings.response_directory}",
            f"- Pairs processed: {len(rows)}",
            f"- Seconds: {time.perf_counter() - started:.3f}",
            f"- Report: {settings.report_path}",
            f"- Outside cutoff: {sum(row['model_time_s'] is None for row in rows)}",
            f"- NoRoute/NoSegment: {sum(row['outcome'] != 'Ok' for row in rows)}",
            f"- Over snap limit: {sum(row['over_snap'] for row in rows)}",
            f"- Warnings/errors: {error or 'none'}",
        ]
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n".join(lines[2:]) + "\n")
