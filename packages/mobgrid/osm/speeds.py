"""Free-flow car speeds and edge delays for sections 8.1 and 8.4."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
from common.config import load_pilot_config
from common.duckdb_io import open_connection, write_parquet

from mobgrid.osm.config import CarSpeedConfig, NetworkConfig, load_network_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CarCostSummary:
    """Fitted density threshold and length-weighted urban shares."""

    edge_count: int
    density_radius_m: float
    density_threshold_km: float
    density_agreement: float | None
    urban_length_share_by_class: tuple[tuple[str, float], ...]
    output_path: str


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _default_speed_expression(config: CarSpeedConfig) -> str:
    context_cases = []
    for context, default_speed in config.defaults_kmh_by_context.items():
        class_cases = " ".join(
            f"WHEN {_sql_text(highway)} THEN {speed!r}"
            for highway, speed in config.class_overrides_kmh_by_context.get(
                context, {}
            ).items()
        )
        class_default = (
            f"CASE lower(coalesce(highway, 'default')) {class_cases} "
            f"ELSE {default_speed!r} END"
            if class_cases
            else repr(default_speed)
        )
        context_cases.append(
            f"WHEN resolved_context = {_sql_text(context)} "
            f"THEN ({class_default})"
        )
    base = "CASE " + " ".join(context_cases) + " END"
    oneway_cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {speed!r}"
        for highway, speed in config.rural_oneway_speed_kmh_by_highway.items()
    )
    base = (
        "CASE WHEN resolved_context = 'rural' AND lower(trim(oneway)) = 'yes' "
        f"THEN coalesce(CASE lower(highway) {oneway_cases} END, ({base})) "
        f"ELSE ({base}) END"
    )
    cap_cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {speed!r}"
        for highway, speed in config.default_caps_kmh_by_highway.items()
    )
    return (
        f"least(({base}), coalesce(CASE lower(highway) {cap_cases} END, "
        f"({base})))"
    )


def _realism_factor_expression(config: CarSpeedConfig) -> str:
    cases = " ".join(
        f"WHEN {_sql_text(highway)} THEN {factor!r}"
        for highway, factor in config.realism_factor_by_highway.items()
        if highway != "default"
    )
    return (
        f"CASE lower(coalesce(highway, 'default')) {cases} "
        f"ELSE {config.realism_factor_by_highway['default']!r} END"
    )


def _bucket_expression(
    config: CarSpeedConfig, speed_expression: str
) -> str:
    bounds = config.speed_limit_bucket_upper_bounds_kmh
    cases = []
    for index, upper_bound in enumerate(bounds):
        label = f"le_{upper_bound:g}" if index == 0 else (
            f"gt_{bounds[index - 1]:g}_le_{upper_bound:g}"
        )
        cases.append(
            f"WHEN {speed_expression} <= {upper_bound!r} "
            f"THEN {_sql_text(label)}"
        )
    return (
        "CASE " + " ".join(cases) + " ELSE "
        + _sql_text(f"gt_{bounds[-1]:g}") + " END"
    )


def _fit_density_threshold(
    connection: duckdb.DuckDBPyConnection,
    config: CarSpeedConfig,
) -> tuple[float, float | None]:
    """Fit the length-weighted urban/rural separator on tagged edges."""
    urban_length, rural_length = connection.execute("""
        SELECT sum(length_m) FILTER (WHERE speed_context = 'urban'),
               sum(length_m) FILTER (WHERE speed_context = 'rural')
        FROM _car_edges
    """).fetchone()
    if not urban_length or not rural_length:
        return config.urban_density.fallback_threshold_km, None

    threshold, agreement = connection.execute("""
        WITH density_groups AS (
            SELECT d.road_density_km,
                   sum(e.length_m) FILTER (
                       WHERE e.speed_context = 'urban'
                   ) AS urban_length_m,
                   sum(e.length_m) FILTER (
                       WHERE e.speed_context = 'rural'
                   ) AS rural_length_m
            FROM _car_edges e
            JOIN _car_edge_densities d USING (edge_key)
            WHERE e.speed_context IN ('urban', 'rural')
            GROUP BY d.road_density_km
        ),
        totals AS (
            SELECT sum(urban_length_m) AS urban_total_m,
                   sum(rural_length_m) AS rural_total_m,
                   sum(
                       coalesce(urban_length_m, 0)
                       + coalesce(rural_length_m, 0)
                   ) AS labelled_total_m,
                   max(road_density_km) AS maximum_density_km
            FROM density_groups
        ),
        running AS (
            SELECT *,
                   coalesce(
                       sum(urban_length_m) OVER (
                           ORDER BY road_density_km
                           ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                       ),
                       0
                   ) AS urban_below_m,
                   coalesce(
                       sum(rural_length_m) OVER (
                           ORDER BY road_density_km
                           ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                       ),
                       0
                   ) AS rural_below_m
            FROM density_groups
        ),
        candidates AS (
            SELECT road_density_km AS threshold_km,
                   urban_total_m - urban_below_m + rural_below_m
                       AS correctly_classified_m,
                   labelled_total_m
            FROM running
            CROSS JOIN totals
            UNION ALL
            SELECT maximum_density_km
                       + greatest(abs(maximum_density_km), 1) * 1e-12,
                   rural_total_m,
                   labelled_total_m
            FROM totals
        )
        SELECT threshold_km,
               max(correctly_classified_m / labelled_total_m) AS agreement
        FROM candidates
        GROUP BY threshold_km
        ORDER BY agreement DESC, threshold_km
        LIMIT 1
    """).fetchone()
    return float(threshold), float(agreement)


def _check_car_classes(
    connection: duckdb.DuckDBPyConnection,
    edges_path: Path,
    config: CarSpeedConfig,
) -> None:
    configured = set(config.realism_factor_by_highway)
    classes = {
        row[0]
        for row in connection.execute(
            f"""
            SELECT DISTINCT lower(highway)
            FROM read_parquet('{_sql_path(edges_path)}')
            WHERE mode = 'car' AND highway IS NOT NULL
            """
        ).fetchall()
    }
    missing = sorted(classes - configured)
    if missing:
        raise ValueError(
            "car highway classes lack realism factors in config/network.yaml: "
            + ", ".join(missing)
        )
    invalid_limits = connection.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{_sql_path(edges_path)}')
        WHERE mode = 'car' AND maxspeed_kmh <= 0
        """
    ).fetchone()[0]
    if invalid_limits:
        raise ValueError(
            f"{invalid_limits} car edges have a non-positive maxspeed_kmh"
        )


def build_car_costs(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    output_path: str | Path,
    *,
    config: NetworkConfig,
) -> CarCostSummary:
    """Write per-directed-edge free-flow times and speed metadata (8.1, 8.4)."""
    edges = Path(edges_path)
    output = Path(output_path)
    if not edges.is_file():
        raise FileNotFoundError(edges)
    _check_car_classes(connection, edges, config.car_speed)
    output.parent.mkdir(parents=True, exist_ok=True)
    connection.execute("LOAD spatial")
    edge_source = _sql_path(edges)
    radius = config.car_speed.urban_density.radius_m
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _car_edges AS
        WITH geometries AS (
            SELECT edge_key, highway, maxspeed_kmh, speed_context, length_m, oneway,
                   signal_count, stop_count, give_way_count, crossing_count,
                   mini_roundabout_count, to_degree,
                   ST_GeomFromWKB(geometry_wkb) AS geom
            FROM read_parquet('{edge_source}')
            WHERE mode = 'car'
        )
        SELECT *, ST_Centroid(geom) AS edge_center
        FROM geometries
    """)
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _car_edge_densities AS
        SELECT target.edge_key,
               coalesce(
                   sum(
                       ST_Length(ST_Intersection(
                           neighbor.geom,
                           ST_Buffer(target.edge_center, {radius!r})
                       ))
                   ),
                   0
               ) / 1000 AS road_density_km
        FROM _car_edges target
        LEFT JOIN _car_edges neighbor
          ON ST_DWithin(target.edge_center, neighbor.geom, {radius!r})
        GROUP BY target.edge_key
    """)
    threshold, agreement = _fit_density_threshold(
        connection, config.car_speed
    )
    density_flag = f"d.road_density_km >= {threshold!r}"
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _car_edge_costs AS
        WITH classified AS (
            SELECT e.*, d.road_density_km,
                   CASE
                     WHEN e.speed_context = 'urban' THEN TRUE
                     WHEN e.speed_context = 'rural' THEN FALSE
                     ELSE {density_flag}
                   END AS is_urban,
                   CASE
                     WHEN e.speed_context IN (
                         'urban', 'rural', 'zone30', 'motorway'
                     ) THEN e.speed_context
                     WHEN {density_flag} THEN 'urban'
                     ELSE 'rural'
                   END AS resolved_context
            FROM _car_edges e
            JOIN _car_edge_densities d USING (edge_key)
        ),
        limits AS (
            SELECT *,
                   coalesce(
                       maxspeed_kmh,
                       {_default_speed_expression(config.car_speed)}
                   ) AS speed_limit_kmh,
                   {_realism_factor_expression(config.car_speed)}
                       AS realism_factor
            FROM classified
        ),
        timed AS (
            SELECT *,
                   speed_limit_kmh * realism_factor AS effective_speed_kmh,
                   length_m * 3.6
                       / (speed_limit_kmh * realism_factor)
                   + coalesce(signal_count, 0) * {config.car_speed.delays.signal_s!r}
                   + coalesce(stop_count, 0) * {config.car_speed.delays.stop_s!r}
                   + coalesce(give_way_count, 0)
                       * {config.car_speed.delays.give_way_s!r}
                   + coalesce(crossing_count, 0)
                       * {config.car_speed.delays.crossing_s!r}
                   + coalesce(mini_roundabout_count, 0)
                       * {config.car_speed.delays.mini_roundabout_s!r}
                   + CASE
                       WHEN to_degree >=
                            {config.car_speed.delays.degree_threshold}
                       THEN {config.car_speed.delays.at_to_node_s!r}
                       ELSE 0
                     END AS time_s
            FROM limits
        )
        SELECT edge_key, time_s, is_urban, highway AS road_class,
               {_bucket_expression(config.car_speed, "speed_limit_kmh")}
                   AS speed_limit_bucket
        FROM timed
    """)

    temporary = output.with_name(output.stem + ".tmp.parquet")
    try:
        write_parquet(
            connection,
            "SELECT edge_key, time_s, is_urban, road_class, "
            "speed_limit_bucket FROM _car_edge_costs",
            temporary,
        )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    edge_count = int(
        connection.execute("SELECT count(*) FROM _car_edge_costs").fetchone()[0]
    )
    class_shares = connection.execute("""
        SELECT coalesce(costs.road_class, '(no highway)') AS road_class,
               coalesce(
                   sum(edges.length_m) FILTER (WHERE costs.is_urban)
                       / nullif(sum(edges.length_m), 0),
                   0
               )
                   AS urban_length_share
        FROM _car_edge_costs costs
        JOIN _car_edges edges USING (edge_key)
        GROUP BY road_class
        ORDER BY road_class
    """).fetchall()
    return CarCostSummary(
        edge_count=edge_count,
        density_radius_m=radius,
        density_threshold_km=threshold,
        density_agreement=agreement,
        urban_length_share_by_class=tuple(
            (str(road_class), float(share))
            for road_class, share in class_shares
        ),
        output_path=str(output),
    )


def write_car_speed_report(
    summary: CarCostSummary,
    path: str | Path,
    *,
    state: int,
    area: str,
) -> None:
    """Report the fitted urban-density rule and urban length by class (8.4)."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    agreement = (
        "not estimable"
        if summary.density_agreement is None
        else f"{summary.density_agreement:.1%}"
    )
    lines = [
        f"# Car free-flow costs ({state}, {area})",
        "",
        f"- Directed car edges: {summary.edge_count:,}",
        "- Density metric: car-edge length clipped to the configured radius "
        "around each edge centroid.",
        f"- Density radius: {summary.density_radius_m:g} m",
        f"- {'Fitted' if summary.density_agreement is not None else 'Fallback'} "
        f"urban threshold: {summary.density_threshold_km:.6g} km of car edges",
        f"- Length-weighted urban/rural label agreement: {agreement}",
        "- Speed-limit bucket is based on the configured limit before realism "
        "factors.",
        "",
        "## Urban share of directed car length by road class",
        "",
        "| Road class | Urban length share |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {road_class} | {share:.1%} |"
        for road_class, share in summary.urban_length_share_by_class
    )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.speeds")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--area", choices=("pilot", "national"), default="pilot")
    parser.add_argument(
        "--network-config", type=Path, default=Path("config/network.yaml")
    )
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build the car free-flow cost table and its diagnostic report."""
    args = _parser().parse_args(argv)
    config = load_network_config(args.network_config)
    pilot = load_pilot_config(args.pilot_config)
    if args.state not in config.states:
        raise ValueError(f"unsupported state {args.state}")
    root = args.pilot_config.resolve().parent.parent
    network_directory = (
        root / pilot.paths["base"] / "network" / str(args.state) / args.area
    )
    edges_path = network_directory / "edges.parquet"
    output_path = network_directory / "car_costs.parquet"
    report_path = args.report or Path(
        f"docs/data/step06_car_speeds_{args.area}_{args.state}.md"
    )
    connection = open_connection()
    try:
        summary = build_car_costs(
            connection, edges_path, output_path, config=config
        )
    finally:
        connection.close()
    write_car_speed_report(
        summary, report_path, state=args.state, area=args.area
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.info(
        "wrote %s directed car costs to %s; density threshold %.6g km",
        summary.edge_count,
        output_path,
        summary.density_threshold_km,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
