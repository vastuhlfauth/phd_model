"""Resumable directed-edge costs and diagnostics for section 8.1."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

import duckdb
from common.config import load_pilot_config
from common.duckdb_io import open_connection, write_parquet

from mobgrid.energy.rates import load_energy_config
from mobgrid.osm import active_costs, elevation, speeds
from mobgrid.osm.active_costs import enrich_active_edge_costs
from mobgrid.osm.config import load_network_config

logger = logging.getLogger(__name__)
_BUILD_VERSION = 3
_CAR_BUILD_VERSION = 2
_REPORT_HEADING = "## Edge costs"


def _file_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def _checkpoint_matches(checkpoint: Path, signature: dict, output: Path) -> bool:
    if not checkpoint.is_file() or not output.is_file():
        return False
    metadata = json.loads(checkpoint.read_text(encoding="utf-8"))
    return metadata == {"signature": signature, "output": _file_signature(output)}


def _save_checkpoint(checkpoint: Path, signature: dict, output: Path) -> None:
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    temporary = checkpoint.with_suffix(".tmp.json")
    try:
        temporary.write_text(
            json.dumps(
                {
                    "signature": signature,
                    "output": _file_signature(output),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary.replace(checkpoint)
    finally:
        temporary.unlink(missing_ok=True)


def _write_costs(
    connection: duckdb.DuckDBPyConnection,
    edges: Path,
    car: Path,
    active: Path,
    output: Path,
) -> None:
    """Join one cost row per directed edge; units are seconds, metres and kJ (8.1)."""
    sources = {"edges": edges, "car": car, "active": active}
    for name, path in sources.items():
        invalid = connection.execute(f"""
            SELECT count(*) - count(DISTINCT edge_key)
            FROM read_parquet('{_sql_path(path)}')
        """).fetchone()[0]
        if invalid:
            raise ValueError(f"{name} contains {invalid} null or duplicate edge keys")
    edge_source, car_source, active_source = (
        _sql_path(path) for path in (edges, car, active)
    )
    invalid = connection.execute(f"""
        SELECT count(*) FROM (
            SELECT edge_key, mode FROM read_parquet('{edge_source}')
            EXCEPT
            SELECT edge_key, 'car' FROM read_parquet('{car_source}')
            EXCEPT
            SELECT a.edge_key, e.mode FROM read_parquet('{active_source}') a
            JOIN read_parquet('{edge_source}') e USING (edge_key)
            WHERE e.mode IN ('foot', 'bike')
        )
    """).fetchone()[0]
    extra = connection.execute(f"""
        SELECT count(*) FROM (
            SELECT edge_key FROM read_parquet('{car_source}')
            EXCEPT SELECT edge_key FROM read_parquet('{edge_source}') WHERE mode = 'car'
            UNION ALL
            (SELECT edge_key FROM read_parquet('{active_source}')
             EXCEPT SELECT edge_key FROM read_parquet('{edge_source}')
                    WHERE mode IN ('foot', 'bike'))
        )
    """).fetchone()[0]
    if invalid or extra:
        raise ValueError(
            f"cost keys do not match edges: {invalid} missing, {extra} extra"
        )
    temporary = output.with_name(output.stem + ".tmp.parquet")
    try:
        write_parquet(
            connection,
            f"""
            SELECT e.edge_key, CAST(e.length_m AS FLOAT) AS length_m,
                   CAST(c.time_s AS FLOAT) AS car_time_s,
                   CAST(a.walk_time_s AS FLOAT) AS walk_time_s,
                   CAST(a.walk_energy_kj AS FLOAT) AS walk_energy_kj,
                   CAST(a.bike_time_s AS FLOAT) AS bike_time_s,
                   CAST(a.bike_energy_kj AS FLOAT) AS bike_energy_kj,
                   CAST(a.bike_energy_per_kg_kj_per_kg AS FLOAT)
                       AS bike_energy_per_kg_kj_per_kg,
                   CAST(a.bike_energy_drag_kj AS FLOAT) AS bike_energy_drag_kj,
                   CAST(a.bike_pedalling_energy_kj AS FLOAT)
                       AS bike_pedalling_energy_kj,
                   CAST(a.climb_m AS FLOAT) AS climb_m,
                   CAST(a.separated_length_m AS FLOAT) AS separated_length_m,
                   a.bike_zero_speed_segments,
                   c.is_urban, c.speed_limit_bucket
            FROM read_parquet('{edge_source}') e
            LEFT JOIN read_parquet('{car_source}') c USING (edge_key)
            LEFT JOIN read_parquet('{active_source}') a USING (edge_key)
        """,
            temporary,
        )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def _write_report(
    connection: duckdb.DuckDBPyConnection, edges: Path, costs: Path, report: Path
) -> None:
    """Update the step 6 report with directed-edge cost diagnostics (8.1)."""
    if not report.is_file():
        raise FileNotFoundError(f"build the step 6 report first: {report}")
    edge_source, cost_source = _sql_path(edges), _sql_path(costs)
    total, missing = connection.execute(f"""
        SELECT count(*), count(*) FILTER (WHERE climb_m IS NULL)
        FROM read_parquet('{edge_source}')
    """).fetchone()
    zero_speed = connection.execute(f"""
        SELECT coalesce(sum(bike_zero_speed_segments), 0)
        FROM read_parquet('{cost_source}')
    """).fetchone()[0]
    rows = connection.execute(f"""
        SELECT coalesce(e.highway, '(no highway)') AS class,
               3.6 * sum(e.length_m) FILTER (WHERE c.car_time_s > 0)
                   / nullif(sum(c.car_time_s) FILTER (WHERE c.car_time_s > 0), 0),
               3.6 * sum(e.length_m) FILTER (WHERE c.walk_time_s > 0)
                   / nullif(sum(c.walk_time_s) FILTER (WHERE c.walk_time_s > 0), 0),
               3.6 * sum(e.length_m) FILTER (WHERE c.bike_time_s > 0)
                   / nullif(sum(c.bike_time_s) FILTER (WHERE c.bike_time_s > 0), 0),
               sum(e.length_m) FILTER (WHERE e.mode = 'car' AND c.is_urban)
                   / nullif(sum(e.length_m) FILTER (WHERE e.mode = 'car'), 0)
        FROM read_parquet('{edge_source}') e
        JOIN read_parquet('{cost_source}') c USING (edge_key)
        GROUP BY class ORDER BY class
    """).fetchall()
    lines = [
        _REPORT_HEADING,
        "",
        f"- Directed edges with null elevation profiles: {missing:,} of {total:,}",
        f"- Zero-speed bike segments (errors): {zero_speed:,}; "
        "see `active_costs.grades.md` "
        "for highway, bike class, surface, grade and cap.",
        "- Mean speeds are total directed length divided by total time, "
        "including delays.",
        "- Urban length share uses directed car edges.",
        "",
        "| Highway class | Car (km/h) | Walk (km/h) | Bike (km/h) | "
        "Urban length share |",
        "|---|---:|---:|---:|---:|",
    ]
    for road_class, car_speed, walk_speed, bike_speed, urban in rows:
        values = [
            "n/a" if value is None else f"{value:.2f}"
            for value in (car_speed, walk_speed, bike_speed)
        ]
        share = "n/a" if urban is None else f"{urban:.1%}"
        lines.append(f"| {road_class} | {' | '.join(values)} | {share} |")
    old = report.read_text(encoding="utf-8")
    marker = "\n" + _REPORT_HEADING + "\n"
    if marker in old:
        start = old.index(marker)
        end = old.find("\n## ", start + len(marker))
        old = old[:start] + (old[end:] if end != -1 else "")
    temporary = report.with_suffix(".tmp.md")
    try:
        temporary.write_text(
            old.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8"
        )
        temporary.replace(report)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    """Run elevation and B1 costs, with resumable outputs and timing (8.1)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument(
        "--network-config", type=Path, default=Path("config/network.yaml")
    )
    parser.add_argument(
        "--energy-config", type=Path, default=Path("config/energy.yaml")
    )
    parser.add_argument("--pilot-config", type=Path, default=Path("config/pilot.yaml"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    network = load_network_config(args.network_config)
    energy = load_energy_config(args.energy_config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in network.states:
        raise ValueError(f"unsupported state {args.state}")
    root = args.pilot_config.resolve().parent.parent
    base = root / pilot.paths["base"] / "network" / str(args.state) / args.area
    cache = (
        root / pilot.paths["interim"] / "osm" / str(args.state) / args.area / "costs"
    )
    edges, nodes = base / "edges.parquet", base / "nodes.parquet"
    output, car, active = (
        base / "edge_costs.parquet",
        base / "car_costs.parquet",
        base / "active_costs.parquet",
    )
    report = args.report or root / "docs" / "data" / (
        "step06_osm_pilot.md"
        if args.state == 2021 and args.area == "pilot"
        else f"step06_osm_{args.area}_{args.state}.md"
    )
    task = f"osm_costs_{args.state}_{args.area}"
    log = args.log or root / "logs" / f"{date.today().isoformat()}_{task}.log"
    summary = (
        args.summary or root / "logs" / f"{date.today().isoformat()}_{task}_summary.md"
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log, encoding="utf-8")
    terminal = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    terminal.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    for target in (logger, speeds.logger, active_costs.logger):
        target.addHandler(handler)
        target.addHandler(terminal)
        target.setLevel(logging.INFO)
    started = time.perf_counter()
    timings: dict[str, float] = {}
    try:
        if not report.is_file():
            raise FileNotFoundError(f"build the step 6 report first: {report}")
        stage = time.perf_counter()
        elevation.main(
            [
                "--state",
                str(args.state),
                "--area",
                args.area,
                "--pilot-config",
                str(args.pilot_config),
                "--network-config",
                str(args.network_config),
                "--energy-config",
                str(args.energy_config),
            ]
        )
        timings["elevation"] = time.perf_counter() - stage
        logger.info("elevation completed in %.2f s", timings["elevation"])
        signature = {
            "version": _BUILD_VERSION,
            "edges": _file_signature(edges),
            "nodes": _file_signature(nodes),
            "network": network.model_dump(mode="json"),
            "energy": energy.model_dump(mode="json"),
        }
        checkpoint = cache / "completed.json"
        reused = _checkpoint_matches(checkpoint, signature, output)
        connection = open_connection()
        try:
            if reused:
                logger.info("reusing completed edge costs %s", output)
                for name in ("car", "active", "join"):
                    timings[name] = 0.0
                    logger.info("%s reused in %.2f s", name, timings[name])
            else:
                stage = time.perf_counter()
                car_signature = {
                    "version": _CAR_BUILD_VERSION,
                    "edges": _file_signature(edges),
                    "config": network.car_speed.model_dump(mode="json"),
                }
                car_checkpoint = cache / "car.json"
                if _checkpoint_matches(car_checkpoint, car_signature, car):
                    logger.info("reusing car costs %s", car)
                else:
                    speeds.build_car_costs(
                        connection,
                        edges,
                        car,
                        config=network,
                        cache_directory=cache.parent / "speeds",
                    )
                    _save_checkpoint(car_checkpoint, car_signature, car)
                timings["car"] = time.perf_counter() - stage
                logger.info("car completed in %.2f s", timings["car"])
                stage = time.perf_counter()
                active_signature = {
                    "version": _BUILD_VERSION,
                    "edges": _file_signature(edges),
                    "nodes": _file_signature(nodes),
                    "bike_speed_table": network.bike_speed_table.model_dump(
                        mode="json"
                    ),
                    "bike_edge_costs": network.bike_edge_costs.model_dump(mode="json"),
                    "energy": energy.model_dump(mode="json"),
                }
                active_checkpoint = cache / "active.json"
                if active.with_suffix(".grades.md").is_file() and _checkpoint_matches(
                    active_checkpoint, active_signature, active
                ):
                    logger.info("reusing walk and bike costs %s", active)
                else:
                    active_summary = enrich_active_edge_costs(
                        connection, edges, nodes, active, energy=energy, network=network
                    )
                    logger.info(
                        "%s incomplete profiles, %s unknown surfaces, "
                        "%s zero-speed bike segments",
                        active_summary.incomplete_profile_count,
                        active_summary.unknown_surface_count,
                        active_summary.zero_speed_segment_count,
                    )
                    if active_summary.zero_speed_segment_count:
                        logger.error(
                            "%s zero-speed bike segments have null costs; see %s",
                            active_summary.zero_speed_segment_count,
                            active.with_suffix(".grades.md"),
                        )
                    _save_checkpoint(active_checkpoint, active_signature, active)
                timings["active"] = time.perf_counter() - stage
                logger.info("walk and bike completed in %.2f s", timings["active"])
                stage = time.perf_counter()
                _write_costs(connection, edges, car, active, output)
                timings["join"] = time.perf_counter() - stage
                logger.info("cost join completed in %.2f s", timings["join"])
                _save_checkpoint(checkpoint, signature, output)
            stage = time.perf_counter()
            _write_report(connection, edges, output, report)
            edge_count, incomplete = connection.execute(
                f"SELECT count(*), count(*) FILTER (WHERE climb_m IS NULL) "
                f"FROM read_parquet('{_sql_path(edges)}')"
            ).fetchone()
            timings["report"] = time.perf_counter() - stage
            logger.info("report completed in %.2f s", timings["report"])
        finally:
            connection.close()
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            "# OSM edge costs run summary\n\n"
            f"- Inputs: `{edges}`, `{nodes}` and elevation grids/ways.\n"
            f"- Outputs: `{output}`, `{report}`.\n"
            f"- Status: {'reused' if reused else 'built'}.\n"
            f"- Directed edges: {edge_count:,}; incomplete elevation: {incomplete:,}.\n"
            f"- Warnings: {incomplete:,} incomplete profiles; "
            f"see `{log}` for other warnings.\n"
            + "".join(
                f"- {name}: {elapsed:.2f} s\n" for name, elapsed in timings.items()
            )
            + f"- Total: {time.perf_counter() - started:.2f} s\n",
            encoding="utf-8",
        )
        return 0
    finally:
        if sys.exc_info()[0] is not None:
            logger.error("edge cost job failed", exc_info=True)
            summary.parent.mkdir(parents=True, exist_ok=True)
            summary.write_text(
                "# OSM edge costs run summary\n\n"
                f"- Status: failed; see `{log}` for the error.\n"
                f"- Inputs: `{edges}`, `{nodes}`.\n"
                f"- Expected outputs: `{output}`, `{report}`.\n"
                f"- Elapsed: {time.perf_counter() - started:.2f} s\n",
                encoding="utf-8",
            )
        for target in (logger, speeds.logger, active_costs.logger):
            target.removeHandler(handler)
            target.removeHandler(terminal)
        handler.close()
        terminal.close()


if __name__ == "__main__":
    raise SystemExit(main())
