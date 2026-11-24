"""Section 13 baseline graph-routing metrics against dated OSRM responses."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

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
    from mobgrid.validation.osrm import _base_url, _key, _request_url, _valid_response

    base = _base_url(settings)
    expected = {_key(pair, _request_url(pair, settings, base)): pair for pair in pairs}
    records: dict[str, dict] = {}
    for path in settings.response_directory.glob("*/*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        key = record.get("request_key")
        if key not in expected or record.get("http_status") != 200:
            continue
        if not _valid_response(record.get("response")):
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


def _render(rows: list[dict], settings: QuerySettings) -> str:
    if settings.metric_tolerances_min is None:
        raise ValueError("metric tolerances are required")
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
        "Routes not reached within the configured Dial cutoff are counted and "
        "excluded from metric denominators.",
        "",
        "| Mode | Band (km) | Context | Matched | Cutoff | Bias (min) | "
        f"Median abs (min) | Within {tolerances[0]:g} min | "
        f"Within {tolerances[1]:g} min | Relative error | "
        "Distance bias (m) | Median abs distance (m) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (mode, lower, upper, context), values in sorted(groups.items()):
        reached = [row for row in values if row["model_time_s"] is not None]
        prefix = (
            f"| {mode} | {lower / 1000:g}-{upper / 1000:g} | {context} | "
            f"{len(reached)} | {len(values) - len(reached)} | "
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
            "## Car calibration",
            "",
            "Pending: fitted values and holdout comparison have not been computed.",
            "",
            f"Sample: {settings.sample_path}.",
            f"Responses: {settings.response_directory}.",
        ]
    )
    return "\n".join(lines) + "\n"


def generate_report(settings: QuerySettings, date: str) -> None:
    """Write baseline metrics and dated logs; reuse matching mode-route checkpoints."""
    from mobgrid.validation.osrm import _write_json

    if (
        settings.sampling is None
        or settings.report_path is None
        or settings.route_checkpoint_directory is None
        or settings.metric_tolerances_min is None
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
                rows.append(
                    {
                        **pair,
                        **route_by_id[pair["pair_id"]],
                        "osrm_time_s": response["routes"][0]["duration"],
                        "osrm_distance_m": response["routes"][0]["distance"],
                        "response_date": record["response_date"],
                        "data_version": response.get("data_version"),
                    }
                )
        text = _render(rows, settings)
        settings.report_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = settings.report_path.with_suffix(".tmp.md")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(settings.report_path)
    except (ValueError, OSError, RuntimeError) as exc:
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
            f"- Error: {error or 'none'}",
        ]
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n".join(lines[2:]) + "\n")
