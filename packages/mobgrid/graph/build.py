"""Build per-mode OSM CSR graphs and their degree-2 contractions."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
from common.config import load_pilot_config

from mobgrid.energy.rates import activity_rate_kj_per_min, load_energy_config
from mobgrid.graph.csr import (
    MODES,
    CSRGraph,
    build_csr_graph,
    graph_memory_bytes,
    legacy_graph_memory_bytes,
    save_graph,
    validate_edge_cost_join,
)
from mobgrid.graph.simplify import (
    contract_degree_two,
    largest_strong_component,
    weak_node_degrees,
)
from mobgrid.osm.config import Mode


@dataclass(frozen=True)
class ModeGraphBuild:
    """Counts, memory and per-stage durations for one mode graph."""

    mode: Mode
    nodes_before_contraction: int
    edges_before_contraction: int
    nodes_after_contraction: int
    edges_after_contraction: int
    memory_before_bytes: int
    memory_after_bytes: int
    legacy_contracted_memory_bytes: int
    output_path: Path
    stage_seconds: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class GraphBuildResult:
    """Outputs and timing for a complete set of mode graphs."""

    validation_seconds: float
    modes: tuple[ModeGraphBuild, ...]


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _kept_node_mask(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    nodes_path: str | Path,
    mode: Mode,
    graph: CSRGraph,
) -> npt.NDArray[np.bool_]:
    """Flag signals, OSM junctions, mixed road classes and graph junctions."""
    edges_source = _sql_path(edges_path)
    nodes_source = _sql_path(nodes_path)
    flagged = connection.execute(f"""
        WITH edge_ends AS (
            SELECT from_node_id AS node_id, way_id, highway
            FROM read_parquet('{edges_source}')
            WHERE mode = '{mode}'
            UNION ALL
            SELECT to_node_id AS node_id, way_id, highway
            FROM read_parquet('{edges_source}')
            WHERE mode = '{mode}'
        ),
        structural_nodes AS (
            SELECT node_id
            FROM edge_ends
            GROUP BY node_id
            HAVING count(DISTINCT way_id) > 1
                OR count(DISTINCT highway) > 1
        ),
        tagged_nodes AS (
            SELECT node_id
            FROM read_parquet('{nodes_source}')
            WHERE lower(coalesce(tags['highway'], '')) = 'traffic_signals'
               OR (lower(coalesce(tags['highway'], '')) = 'crossing'
                   AND lower(coalesce(tags['crossing'], '')) = 'traffic_signals')
               OR nullif(tags['junction'], '') IS NOT NULL
        )
        SELECT node_id FROM structural_nodes
        UNION
        SELECT node_id FROM tagged_nodes
    """).to_arrow_table()
    flagged_ids = np.asarray(
        flagged.column("node_id").to_numpy(zero_copy_only=False),
        dtype=np.int64,
    )
    kept = np.isin(graph.node_ids, flagged_ids)
    kept |= weak_node_degrees(graph) > 2
    return kept


def build_graphs(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    edge_costs_path: str | Path,
    nodes_path: str | Path,
    output_directory: str | Path,
    *,
    reference_mass_kg: float,
    bike_mass_kg: float,
    car_energy_kj_per_s: float,
) -> GraphBuildResult:
    """Build and atomically write SCC-filtered, contracted graphs for all modes."""
    started = time.perf_counter()
    validate_edge_cost_join(connection, edges_path, edge_costs_path)
    validation_seconds = time.perf_counter() - started
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    summaries = []

    for mode in MODES:
        stages: list[tuple[str, float]] = []
        stage_started = time.perf_counter()
        graph = build_csr_graph(
            connection,
            edges_path,
            edge_costs_path,
            mode,
            reference_mass_kg=reference_mass_kg,
            bike_mass_kg=bike_mass_kg,
            car_energy_kj_per_s=car_energy_kj_per_s,
        )
        stages.append(("join and CSR", time.perf_counter() - stage_started))

        stage_started = time.perf_counter()
        component = largest_strong_component(graph)
        stages.append(("largest SCC", time.perf_counter() - stage_started))
        nodes_before = len(component.node_ids)
        edges_before = len(component.indices)

        stage_started = time.perf_counter()
        kept_nodes = _kept_node_mask(
            connection,
            edges_path,
            nodes_path,
            mode,
            component,
        )
        stages.append(("kept-node flags", time.perf_counter() - stage_started))

        stage_started = time.perf_counter()
        contracted = contract_degree_two(component, kept_nodes)
        stages.append(("contraction", time.perf_counter() - stage_started))

        output_path = destination / f"{mode}.npz"
        stage_started = time.perf_counter()
        save_graph(contracted, output_path)
        stages.append(("write", time.perf_counter() - stage_started))
        summaries.append(
            ModeGraphBuild(
                mode=mode,
                nodes_before_contraction=nodes_before,
                edges_before_contraction=edges_before,
                nodes_after_contraction=len(contracted.node_ids),
                edges_after_contraction=len(contracted.indices),
                memory_before_bytes=graph_memory_bytes(component),
                memory_after_bytes=graph_memory_bytes(contracted),
                legacy_contracted_memory_bytes=legacy_graph_memory_bytes(contracted),
                output_path=output_path,
                stage_seconds=tuple(stages),
            )
        )

    return GraphBuildResult(validation_seconds, tuple(summaries))


def _memory_mib(byte_count: int) -> str:
    return f"{byte_count / (1024 * 1024):.1f}"


def _graph_report_section(
    result: GraphBuildResult,
    *,
    state: int,
    area: str,
) -> str:
    lines = [
        "## Graph build",
        "",
        f"- State / area: {state} / {area}",
        f"- One-to-one edge-cost validation: {result.validation_seconds:.2f} s",
        "- Memory counts include forward and transposed CSR arrays.",
        "- Legacy memory is estimated for the new contracted topology, without "
        "the new membership map; it is not a measurement of the old pilot graph.",
        "",
        "| Mode | Nodes before contraction | Edges before contraction | "
        "Nodes after contraction | Edges after contraction | "
        "Memory before (MiB) | Memory after (MiB) | Legacy estimate (MiB) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in result.modes:
        lines.append(
            f"| {summary.mode} | {summary.nodes_before_contraction:,} | "
            f"{summary.edges_before_contraction:,} | "
            f"{summary.nodes_after_contraction:,} | "
            f"{summary.edges_after_contraction:,} | "
            f"{_memory_mib(summary.memory_before_bytes)} | "
            f"{_memory_mib(summary.memory_after_bytes)} | "
            f"{_memory_mib(summary.legacy_contracted_memory_bytes)} |"
        )
    lines.extend(
        [
            "",
            "| Mode | Join and CSR (s) | Largest SCC (s) | Kept-node flags (s) | "
            "Contraction (s) | Write (s) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for summary in result.modes:
        timings = dict(summary.stage_seconds)
        lines.append(
            f"| {summary.mode} | {timings['join and CSR']:.2f} | "
            f"{timings['largest SCC']:.2f} | "
            f"{timings['kept-node flags']:.2f} | "
            f"{timings['contraction']:.2f} | {timings['write']:.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_graph_report(
    report_path: str | Path,
    result: GraphBuildResult,
    *,
    state: int,
    area: str,
) -> None:
    """Idempotently replace the graph-build section in the step 6 report."""
    report = Path(report_path)
    if not report.is_file():
        raise FileNotFoundError(f"build the step 6 report first: {report}")
    old = report.read_text(encoding="utf-8")
    marker = "\n## Graph build\n"
    if marker in old:
        start = old.index(marker)
        end = old.find("\n## ", start + len(marker))
        old = old[:start] + (old[end:] if end != -1 else "")
    section = _graph_report_section(result, state=state, area=area)
    temporary = report.with_suffix(".tmp.md")
    try:
        temporary.write_text(
            old.rstrip() + "\n\n" + section,
            encoding="utf-8",
        )
        temporary.replace(report)
    finally:
        temporary.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument(
        "--energy-config", type=Path, default=Path("config/energy.yaml")
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build all mode graphs and update the step 6 report."""
    args = _parser().parse_args(argv)
    pilot = load_pilot_config(args.pilot_config)
    energy = load_energy_config(args.energy_config)
    if args.state not in pilot.years:
        raise ValueError(f"unsupported state {args.state}; configured: {pilot.years}")

    root = args.pilot_config.resolve().parent.parent
    base = root / pilot.paths["base"] / "network" / str(args.state) / args.area
    edges_path = base / "edges.parquet"
    costs_path = base / "edge_costs.parquet"
    nodes_path = base / "nodes.parquet"
    output_directory = base / "graph"
    default_report = (
        root / "docs" / "data" / "step06_osm_pilot.md"
        if args.area == "pilot" and args.state == pilot.years[0]
        else root / "docs" / "data" / f"step06_osm_{args.area}_{args.state}.md"
    )
    report_path = args.report or default_report
    for path in (edges_path, costs_path, nodes_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not report_path.is_file():
        raise FileNotFoundError(f"build the step 6 report first: {report_path}")

    car_rate = activity_rate_kj_per_min(
        energy.activity_rates["driving_free_flow"],
        energy.rate_set,
        energy.reference_mass_kg,
    )
    connection = duckdb.connect()
    try:
        result = build_graphs(
            connection,
            edges_path,
            costs_path,
            nodes_path,
            output_directory,
            reference_mass_kg=energy.reference_mass_kg,
            bike_mass_kg=energy.bike.bike_mass_kg,
            car_energy_kj_per_s=car_rate / 60.0,
        )
    finally:
        connection.close()
    write_graph_report(
        report_path,
        result,
        state=args.state,
        area=args.area,
    )
    print(_graph_report_section(result, state=args.state, area=args.area))
    for summary in result.modes:
        print(f"Wrote {summary.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
