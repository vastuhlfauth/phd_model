"""Time bounded searches on configured pilot graphs (section 14.7)."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import date as current_date
from pathlib import Path
from typing import Literal, Mapping

import numpy as np
from common.config import load_pilot_config

from mobgrid.graph.config import load_search_config
from mobgrid.graph.csr import MODES, load_graph
from mobgrid.graph.dijkstra import SearchWorkspace, search
from mobgrid.osm.config import Mode


@dataclass(frozen=True)
class BenchmarkResult:
    """Completed search count, summed seconds and settled nodes."""

    mode: Mode
    queue: Literal["heap", "dial"]
    searches: int
    seconds: float
    settled: int


def _checkpoint(
    directory: Path,
    graph_path: Path,
    mode: Mode,
    queue: str,
    cutoff: float,
    resolution: float,
    searches: int,
    seed: int,
) -> tuple[Path, list[dict], bool]:
    stat = graph_path.stat()
    signature = {
        "version": 1,
        "graph": str(graph_path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "mode": mode,
        "queue": queue,
        "cutoff_s": cutoff,
        "resolution_s": resolution,
        "searches": searches,
        "seed": seed,
    }
    key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    path = directory / f"{mode}_{queue}_{key}.jsonl"
    if not path.exists():
        return path, [], False
    content = path.read_bytes()
    recovered = bool(content) and not content.endswith(b"\n")
    if recovered:
        end = content.rfind(b"\n") + 1
        if not end:
            raise ValueError(f"benchmark checkpoint has no complete header: {path}")
        with path.open("r+b") as stream:
            stream.truncate(end)
        content = content[:end]
    rows = [json.loads(line) for line in content.splitlines()]
    if not rows or rows[0] != signature or len(rows) - 1 > searches:
        raise ValueError(f"invalid benchmark checkpoint: {path}")
    return path, rows[1:], recovered


def run_benchmark(
    graph_paths: Mapping[Mode, Path],
    cutoffs_s: Mapping[Mode, float],
    resolution_s: float,
    searches: int,
    seed: int,
    checkpoint_dir: Path,
    log_dir: Path,
    date: str,
) -> tuple[BenchmarkResult, ...]:
    """Run or resume timed searches; output times are seconds."""
    if searches <= 0 or resolution_s <= 0 or not np.isfinite(resolution_s):
        raise ValueError("search count and resolution must be positive")
    if any(not np.isfinite(cutoffs_s[m]) or cutoffs_s[m] <= 0 for m in MODES):
        raise ValueError("all mode cutoffs must be finite and positive")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{date}_graph_search_benchmark.log"
    summary_path = log_dir / f"{date}_graph_search_benchmark_summary.md"
    results: list[BenchmarkResult] = []
    warnings: list[str] = []
    started = time.perf_counter()
    try:
        with log_path.open("a", encoding="utf-8") as log:
            for mode_index, mode in enumerate(MODES):
                graph_path = graph_paths[mode]
                graph = load_graph(graph_path)
                if graph.mode != mode or not len(graph.node_ids):
                    raise ValueError(f"invalid or empty {mode} graph: {graph_path}")
                cutoff = cutoffs_s[mode]
                max_ticks = int(np.ceil(cutoff / resolution_s))
                workspace = SearchWorkspace(
                    graph, ("distance_m", "energy_kj"), max_dial_ticks=max_ticks
                )
                origins = np.random.default_rng(seed + mode_index).integers(
                    0, len(graph.node_ids), size=searches
                )
                offset = np.zeros(1, dtype=np.float64)
                for queue in ("heap", "dial"):
                    checkpoint, rows, recovered = _checkpoint(
                        checkpoint_dir,
                        graph_path,
                        mode,
                        queue,
                        cutoff,
                        resolution_s,
                        searches,
                        seed,
                    )
                    if recovered:
                        warning = f"removed incomplete checkpoint line: {checkpoint}"
                        warnings.append(warning)
                        log.write(f"WARNING: {warning}\n")
                    for index, row in enumerate(rows):
                        if (
                            row["origin"] != int(origins[index])
                            or not np.isfinite(row["seconds"])
                            or row["seconds"] < 0
                            or not 0 <= row["settled"] <= len(graph.node_ids)
                        ):
                            raise ValueError(f"invalid benchmark row in {checkpoint}")
                    if not checkpoint.exists():
                        stat = graph_path.stat()
                        signature = {
                            "version": 1,
                            "graph": str(graph_path.resolve()),
                            "size": stat.st_size,
                            "mtime_ns": stat.st_mtime_ns,
                            "mode": mode,
                            "queue": queue,
                            "cutoff_s": cutoff,
                            "resolution_s": resolution_s,
                            "searches": searches,
                            "seed": seed,
                        }
                        checkpoint.write_text(
                            json.dumps(signature, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    if len(rows) < searches:
                        search(
                            graph,
                            workspace,
                            origins[:1],
                            offset,
                            cutoff,
                            queue=queue,
                            resolution_s=resolution_s,
                        )
                    with checkpoint.open("a", encoding="utf-8") as output:
                        for index in range(len(rows), searches):
                            origin = origins[index : index + 1]
                            timer = time.perf_counter()
                            result = search(
                                graph,
                                workspace,
                                origin,
                                offset,
                                cutoff,
                                queue=queue,
                                resolution_s=resolution_s,
                            )
                            row = {
                                "origin": int(origin[0]),
                                "seconds": time.perf_counter() - timer,
                                "settled": result.count,
                            }
                            output.write(json.dumps(row) + "\n")
                            output.flush()
                            rows.append(row)
                    result = BenchmarkResult(
                        mode,
                        queue,
                        len(rows),
                        sum(row["seconds"] for row in rows),
                        sum(row["settled"] for row in rows),
                    )
                    results.append(result)
                    log.write(
                        f"{mode} {queue}: {result.searches} searches, "
                        f"{result.seconds:.6f} s, {result.settled} settled\n"
                    )
                    log.flush()
    except Exception as exc:
        warnings.append(f"{type(exc).__name__}: {exc}")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"ERROR: {warnings[-1]}\n")
        raise
    finally:
        lines = [
            "# Graph search benchmark",
            "",
            f"- Inputs: {dict(graph_paths)}",
            f"- Cutoffs (s): {dict(cutoffs_s)}; Dial resolution (s): {resolution_s}",
            f"- Search count per mode and queue: {searches}; seed: {seed}",
            f"- Total wall seconds: {time.perf_counter() - started:.3f}",
            f"- Checkpoints: {checkpoint_dir}",
            f"- Log: {log_path}",
            f"- Warnings: {warnings if warnings else 'none'}",
            "",
            "| Mode | Queue | Searches | Seconds | Settled | Settled/s |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for result in results:
            rate = result.settled / result.seconds if result.seconds else 0
            lines.append(
                f"| {result.mode} | {result.queue} | {result.searches} | "
                f"{result.seconds:.6f} | {result.settled} | {rate:.0f} |"
            )
        for mode in MODES:
            pair = [item for item in results if item.mode == mode]
            if len(pair) == 2:
                faster = min(pair, key=lambda item: item.seconds)
                lines.append(f"- {mode}: faster queue is {faster.queue}.")
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tuple(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--searches", type=int, required=True)
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument(
        "--search-config", type=Path, default=Path("config/search.yaml")
    )
    args = parser.parse_args(argv)
    pilot = load_pilot_config(args.pilot_config)
    config = load_search_config(args.search_config)
    if args.state not in pilot.years:
        raise ValueError(f"unsupported state {args.state}")
    cutoffs = config.cutoff_s_by_mode
    if any(cutoffs[mode] is None for mode in MODES):
        raise ValueError("set cutoff_s_by_mode for car, bike and foot in search config")
    root = args.pilot_config.resolve().parent.parent
    base = root / pilot.paths["base"] / "network" / str(args.state) / "pilot" / "graph"
    graphs = {mode: base / f"{mode}.npz" for mode in MODES}
    complete_cutoffs = {mode: float(cutoffs[mode]) for mode in MODES}
    results = run_benchmark(
        graphs,
        complete_cutoffs,
        config.dial_resolution_s,
        args.searches,
        config.benchmark_seed,
        root / pilot.paths["interim"] / "graph_benchmark",
        root / config.benchmark_log_directory,
        current_date.today().isoformat(),
    )
    for result in results:
        print(
            f"{result.mode} {result.queue}: {result.searches} searches, "
            f"{result.seconds:.3f} s, {result.settled} settled"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
