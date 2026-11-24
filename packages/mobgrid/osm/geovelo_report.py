"""Géovélo validation section for the step 6 OSM report (section 8.1)."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import duckdb
import numpy as np
import shapely
from acquire.manifest import load_manifest
from common.config import load_pilot_config
from shapely import STRtree

from mobgrid.osm.bike_infra import maxspeed_sql
from mobgrid.osm.config import (
    BikeReportFamily,
    NetworkConfig,
    load_network_config,
)
from mobgrid.pt.osm_route_extraction import configure_extraction_connection

_GÉOVÉLO_HEADING = "## Géovélo comparison"


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _configured_cycleway_case(
    value_expression: str,
    config: NetworkConfig,
) -> str:
    cases = [
        f"WHEN lower(trim({value_expression})) = {_sql_text(value)} "
        f"THEN {_sql_text(family)}"
        for value, family in sorted(
            config.geovelo_report.osm_cycleway_families.items()
        )
    ]
    return "CASE " + " ".join(cases) + " ELSE NULL END"


def _generic_side_count(
    value_expression: str,
    config: NetworkConfig,
) -> str:
    """Build the configured generic-way side count for section 8.1."""
    cases = [
        f"WHEN lower(trim({value_expression})) = {_sql_text(value)} "
        f"THEN {count}"
        for value, count in sorted(
            config.geovelo_report.osm_generic_cycleway_side_counts.items()
        )
    ]
    return "CASE " + " ".join(cases) + " ELSE 1 END"


def _low_speed_rule_sql(
    rule: str,
    tags_expression: str,
    config: NetworkConfig,
) -> str:
    if rule.startswith("maxspeed<="):
        limit = float(rule.split("<=", 1)[1])
        return f"({maxspeed_sql(tags_expression, config)} <= {limit})"
    conditions = []
    for condition in rule.split("+"):
        tag, value = condition.split("=", 1)
        conditions.append(
            f"lower({tags_expression}[{_sql_text(tag)}]) "
            f"= {_sql_text(value.casefold())}"
        )
    return "(" + " AND ".join(conditions) + ")"


def _create_osm_facilities(
    connection: duckdb.DuckDBPyConnection,
    *,
    ways_path: str | Path,
    nodes_path: str | Path,
    edges_path: str | Path,
    config: NetworkConfig,
) -> None:
    ways = _sql_path(ways_path)
    nodes = _sql_path(nodes_path)
    edges = _sql_path(edges_path)
    busway_values = ", ".join(
        _sql_text(value.casefold()) for value in config.busway_values
    )
    cycleway_case = _configured_cycleway_case("side_value", config)
    generic_side_count = _generic_side_count("side_value", config)
    low_speed_rules = " OR ".join(
        _low_speed_rule_sql(rule, "tags", config)
        for rule in (
            *config.bike_classes["low_speed"],
            *config.geovelo_report.osm_unmarked_contraflow_rules,
        )
    )
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_osm_ways AS
        WITH bike_ways AS (
            SELECT way_id, bool_or(car_access) AS car_access
            FROM read_parquet('{edges}')
            WHERE mode = 'bike' AND bike_access
            GROUP BY way_id
        ),
        points AS (
            SELECT w.way_id, w.tags, b.car_access,
                   r.ordinality AS node_order,
                   n.lat, n.lon
            FROM read_parquet('{ways}') w
            JOIN bike_ways b USING (way_id)
            CROSS JOIN UNNEST(w.refs) WITH ORDINALITY AS r(node_id, ordinality)
            JOIN read_parquet('{nodes}') n ON n.node_id = r.node_id
        ),
        full_ways AS (
            SELECT way_id, first(tags) AS tags, first(car_access) AS car_access,
                   ST_Transform(
                       ST_MakeLine(list(ST_Point(lon, lat) ORDER BY node_order)),
                       'EPSG:4326', 'EPSG:3035'
                   ) AS geom
            FROM points
            GROUP BY way_id
            HAVING count(*) >= 2
        )
        SELECT w.way_id, w.tags, w.car_access,
               ST_Intersection(w.geom, d.geom) AS geom
        FROM full_ways w
        CROSS JOIN _geovelo_report_department d
        WHERE ST_Intersects(w.geom, d.geom)
    """)

    left_cycleway = (
        "coalesce(nullif(trim(tags['cycleway:left']), ''), "
        "nullif(trim(tags['cycleway:both']), ''))"
    )
    right_cycleway = (
        "coalesce(nullif(trim(tags['cycleway:right']), ''), "
        "nullif(trim(tags['cycleway:both']), ''))"
    )
    left_busway = (
        f"CASE WHEN lower(trim(tags['busway:left'])) IN ({busway_values}) "
        "THEN 'share_busway' "
        f"WHEN lower(trim(tags['busway:both'])) IN ({busway_values}) "
        "THEN 'share_busway' END"
    )
    right_busway = (
        f"CASE WHEN lower(trim(tags['busway:right'])) IN ({busway_values}) "
        "THEN 'share_busway' "
        f"WHEN lower(trim(tags['busway:both'])) IN ({busway_values}) "
        "THEN 'share_busway' END"
    )
    no_directional_cycleway = (
        "nullif(trim(tags['cycleway:left']), '') IS NULL "
        "AND nullif(trim(tags['cycleway:right']), '') IS NULL "
        "AND nullif(trim(tags['cycleway:both']), '') IS NULL "
    )
    no_directional_busway = (
        "nullif(trim(tags['busway:left']), '') IS NULL "
        "AND nullif(trim(tags['busway:right']), '') IS NULL "
        "AND nullif(trim(tags['busway:both']), '') IS NULL "
    )
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_osm_facilities AS
        WITH separate_ways AS (
            SELECT way_id, 'separated_track_path' AS family, geom,
                   1::BIGINT AS side_count
            FROM _geovelo_report_osm_ways
            WHERE lower(tags['highway']) = 'cycleway'
               OR (
                   lower(tags['highway']) IN ('path', 'footway')
                   AND lower(tags['bicycle']) = 'designated'
               )
        ),
        side_values AS (
            SELECT way_id, tags, geom,
                   coalesce({left_cycleway}, {left_busway}) AS side_value
            FROM _geovelo_report_osm_ways
            WHERE lower(coalesce(tags['highway'], '')) != 'cycleway'
              AND NOT (
                  lower(tags['highway']) IN ('path', 'footway')
                  AND lower(tags['bicycle']) = 'designated'
              )
            UNION ALL
            SELECT way_id, tags, geom,
                   coalesce({right_cycleway}, {right_busway}) AS side_value
            FROM _geovelo_report_osm_ways
            WHERE lower(coalesce(tags['highway'], '')) != 'cycleway'
              AND NOT (
                  lower(tags['highway']) IN ('path', 'footway')
                  AND lower(tags['bicycle']) = 'designated'
              )
        ),
        classified_sides AS (
            SELECT way_id, geom, {cycleway_case} AS family
            FROM (
                SELECT way_id, geom, side_value
                FROM side_values
                WHERE side_value IS NOT NULL
            )
        ),
        side_facilities AS (
            SELECT way_id, family, first(geom) AS geom,
                   count(*)::BIGINT AS side_count
            FROM classified_sides
            WHERE family IS NOT NULL
            GROUP BY way_id, family
        ),
        generic_values AS (
            SELECT way_id, geom,
                   coalesce(
                       nullif(trim(tags['cycleway']), ''),
                       CASE WHEN lower(trim(tags['busway'])) IN ({busway_values})
                            THEN 'share_busway' END
                   ) AS side_value
            FROM _geovelo_report_osm_ways
            WHERE {no_directional_cycleway}
              AND {no_directional_busway}
              AND lower(coalesce(tags['highway'], '')) != 'cycleway'
              AND NOT (
                  lower(tags['highway']) IN ('path', 'footway')
                  AND lower(tags['bicycle']) = 'designated'
              )
        ),
        generic_facilities AS (
            SELECT way_id, {cycleway_case} AS family, first(geom) AS geom,
                   max({generic_side_count})::BIGINT AS side_count
            FROM generic_values
            WHERE side_value IS NOT NULL
            GROUP BY way_id, side_value
            HAVING {cycleway_case} IS NOT NULL
        ),
        low_speed_facilities AS (
            SELECT way_id, 'low_speed' AS family, geom,
                   1::BIGINT AS side_count
            FROM _geovelo_report_osm_ways
            WHERE {no_directional_cycleway}
              AND nullif(trim(tags['cycleway']), '') IS NULL
              AND {no_directional_busway}
              AND nullif(trim(tags['busway']), '') IS NULL
              AND lower(coalesce(tags['highway'], ''))
                  NOT IN ('cycleway', 'path', 'footway', 'pedestrian')
              AND ({low_speed_rules})
        ),
        other_car_free_paths AS (
            SELECT way_id, 'other_car_free_paths' AS family, geom,
                   1::BIGINT AS side_count
            FROM _geovelo_report_osm_ways
            WHERE lower(tags['highway']) IN ('path', 'footway', 'pedestrian')
              AND {no_directional_cycleway}
              AND nullif(trim(tags['cycleway']), '') IS NULL
              AND {no_directional_busway}
              AND nullif(trim(tags['busway']), '') IS NULL
              AND NOT (
                  lower(tags['highway']) IN ('path', 'footway')
                  AND lower(tags['bicycle']) = 'designated'
              )
              AND NOT car_access
        )
        SELECT * FROM separate_ways
        UNION ALL SELECT * FROM side_facilities
        UNION ALL SELECT * FROM generic_facilities
        UNION ALL SELECT * FROM low_speed_facilities
        UNION ALL SELECT * FROM other_car_free_paths
    """)


def _geovelo_family_case(
    value_expression: str,
    mappings: dict[str, BikeReportFamily | None],
) -> str:
    cases = [
        f"WHEN upper(trim({value_expression})) = {_sql_text(value.upper())} "
        f"THEN {_sql_text(family)}"
        for value, family in sorted(mappings.items())
        if family is not None
    ]
    return "CASE " + " ".join(cases) + " ELSE NULL END"


def _format_length(value: float | None) -> str:
    return "0.0" if value is None else f"{value:,.1f}"


def _match_geovelo_lengths(
    connection: duckdb.DuckDBPyConnection,
    config: NetworkConfig,
) -> dict[str, tuple[float, float]]:
    """Match 5 m length-weighted samples to same-family lines, in metres (8.1)."""
    geovelo_rows = connection.execute("""
        SELECT family, side_count, ST_AsWKB(geom)
        FROM _geovelo_report_facilities
    """).fetchall()
    osm_rows = connection.execute("""
        SELECT family, ST_AsWKB(geom)
        FROM _geovelo_report_osm_facilities
        WHERE family != 'other_car_free_paths'
    """).fetchall()
    geovelo_by_family: dict[str, list[tuple[bytes, int]]] = defaultdict(list)
    osm_by_family: dict[str, list[bytes]] = defaultdict(list)
    for family, side_count, geometry_wkb in geovelo_rows:
        geovelo_by_family[family].append((bytes(geometry_wkb), side_count))
    for family, geometry_wkb in osm_rows:
        osm_by_family[family].append(bytes(geometry_wkb))

    matches: dict[str, tuple[float, float]] = {}
    for family, facilities in geovelo_by_family.items():
        geometries = shapely.from_wkb([item[0] for item in facilities])
        side_counts = np.asarray([item[1] for item in facilities], dtype=np.int64)
        parts, parent_indices = shapely.get_parts(
            geometries, return_index=True
        )
        line_mask = shapely.get_type_id(parts) == 1
        parts = parts[line_mask]
        parent_indices = parent_indices[line_mask]
        lengths = np.asarray(shapely.length(parts), dtype=np.float64)
        positive = lengths > 0
        parts = parts[positive]
        parent_indices = parent_indices[positive]
        lengths = lengths[positive]
        total_length = float(
            np.sum(lengths * side_counts[parent_indices], dtype=np.float64)
        )
        if not len(parts):
            matches[family] = (total_length, 0.0)
            continue

        sample_counts = np.maximum(
            1,
            np.ceil(
                lengths / config.geovelo_report.match_sample_spacing_m
            ).astype(np.int64),
        )
        sampled_line_indices = np.repeat(
            np.arange(len(parts), dtype=np.int64), sample_counts
        )
        sample_starts = np.repeat(
            np.cumsum(sample_counts) - sample_counts, sample_counts
        )
        fractions = (
            np.arange(len(sampled_line_indices)) - sample_starts + 0.5
        ) / sample_counts[sampled_line_indices]
        points = shapely.line_interpolate_point(
            parts[sampled_line_indices], fractions, normalized=True
        )
        weights = (
            lengths[sampled_line_indices]
            / sample_counts[sampled_line_indices]
            * side_counts[parent_indices[sampled_line_indices]]
        )

        osm_geometries = osm_by_family.get(family, [])
        if not osm_geometries:
            matches[family] = (total_length, 0.0)
            continue
        tree = STRtree(shapely.from_wkb(osm_geometries))
        nearest = tree.query_nearest(
            points,
            max_distance=config.geovelo_report.match_tolerance_m,
            all_matches=False,
        )
        matched_length = float(weights[nearest[0]].sum())
        matches[family] = (total_length, matched_length)
    return matches


def _append_section(report_path: Path, lines: list[str]) -> None:
    if not report_path.is_file():
        raise FileNotFoundError(f"build the step 6 report first: {report_path}")
    existing_lines = report_path.read_text(encoding="utf-8").splitlines()
    section_start = next(
        (
            index
            for index, line in enumerate(existing_lines)
            if line == _GÉOVÉLO_HEADING
        ),
        None,
    )
    if section_start is None:
        prefix = "\n".join(existing_lines).rstrip()
        suffix = ""
    else:
        section_end = next(
            (
                index
                for index in range(section_start + 1, len(existing_lines))
                if existing_lines[index].startswith("## ")
            ),
            len(existing_lines),
        )
        prefix = "\n".join(existing_lines[:section_start]).rstrip()
        suffix = "\n".join(existing_lines[section_end:]).lstrip()
    section = "\n".join(lines)
    report_path.write_text(
        prefix
        + "\n\n"
        + section
        + (("\n\n" + suffix) if suffix else "")
        + "\n",
        encoding="utf-8",
    )


def write_geovelo_report_section(
    connection: duckdb.DuckDBPyConnection,
    report_path: str | Path,
    *,
    ways_path: str | Path,
    nodes_path: str | Path,
    edges_path: str | Path,
    geovelo_path: str | Path,
    contours_path: str | Path,
    department: str,
    source_id: str,
    config: NetworkConfig,
) -> None:
    """Append department-only section 8.1 lengths and matching to step 6."""
    geovelo = _sql_path(geovelo_path)
    contours = _sql_path(contours_path)
    department_sql = _sql_text(department)
    for path in (geovelo_path, contours_path, ways_path, nodes_path, edges_path):
        if not Path(path).is_file():
            raise FileNotFoundError(f"report input does not exist: {path}")
    connection.execute("LOAD spatial")
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_communes AS
        SELECT code, nom, geom AS geom_wgs84,
               ST_Transform(geom, 'EPSG:4326', 'EPSG:3035') AS geom
        FROM ST_Read('{contours}')
        WHERE departement = {department_sql}
    """)
    commune_count = connection.execute(
        "SELECT count(*) FROM _geovelo_report_communes"
    ).fetchone()[0]
    if not commune_count:
        raise ValueError(
            f"no commune contours found for department {department!r}"
        )
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_department AS
        SELECT ST_Union_Agg(geom) AS geom
        FROM _geovelo_report_communes
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_bbox AS
        SELECT ST_Envelope(ST_Union_Agg(geom_wgs84)) AS geom
        FROM _geovelo_report_communes
    """)
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_features AS
        SELECT g.OGC_FID AS feature_id, g.ame_d, g.ame_g,
               ST_Intersection(
                   ST_Transform(g.geom, 'EPSG:4326', 'EPSG:3035'),
                   d.geom
               ) AS geom
        FROM ST_Read('{geovelo}') g
        CROSS JOIN _geovelo_report_bbox b
        CROSS JOIN _geovelo_report_department d
        WHERE ST_Intersects(g.geom, b.geom)
          AND ST_Intersects(
              ST_Transform(g.geom, 'EPSG:4326', 'EPSG:3035'), d.geom
          )
    """)
    family_case_d = _geovelo_family_case(
        "amenagement", config.geovelo_report.amenagement_families
    )
    connection.execute(f"""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_sides AS
        SELECT feature_id, geom, 'ame_d' AS source_field,
               nullif(trim(ame_d), '') AS amenagement,
               {family_case_d} AS family
        FROM _geovelo_report_features
        UNION ALL
        SELECT feature_id, geom, 'ame_g' AS source_field,
               nullif(trim(ame_g), '') AS amenagement,
               {family_case_d} AS family
        FROM _geovelo_report_features
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_facilities AS
        SELECT feature_id, family, first(geom) AS geom,
               CASE WHEN family = 'separated_track_path' THEN 1
                    ELSE count(*) END::BIGINT AS side_count
        FROM _geovelo_report_sides
        WHERE family IS NOT NULL
        GROUP BY feature_id, family
    """)
    _create_osm_facilities(
        connection,
        ways_path=ways_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        config=config,
    )
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_osm_commune_lengths AS
        SELECT c.code, c.nom, f.family,
               sum(ST_Length(ST_Intersection(f.geom, c.geom))
                   * f.side_count) AS length_m
        FROM _geovelo_report_osm_facilities f
        JOIN _geovelo_report_communes c ON ST_Intersects(f.geom, c.geom)
        GROUP BY c.code, c.nom, f.family
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _geovelo_report_geo_commune_lengths AS
        SELECT c.code, c.nom, f.family,
               sum(ST_Length(ST_Intersection(f.geom, c.geom))
                   * f.side_count) AS length_m
        FROM _geovelo_report_facilities f
        JOIN _geovelo_report_communes c ON ST_Intersects(f.geom, c.geom)
        GROUP BY c.code, c.nom, f.family
    """)
    length_rows = connection.execute("""
        SELECT coalesce(o.code, g.code) AS code,
               coalesce(o.nom, g.nom) AS commune,
               coalesce(o.family, g.family) AS family,
               o.length_m AS osm_length_m,
               g.length_m AS geovelo_length_m
        FROM _geovelo_report_osm_commune_lengths o
        FULL OUTER JOIN _geovelo_report_geo_commune_lengths g
            USING (code, family)
        WHERE coalesce(o.family, g.family) != 'other_car_free_paths'
        ORDER BY code, family
    """).fetchall()
    match_rows = sorted(_match_geovelo_lengths(connection, config).items())
    other_path_rows = connection.execute("""
        SELECT c.code, c.nom,
               sum(ST_Length(ST_Intersection(f.geom, c.geom))
                   * f.side_count) AS length_m
        FROM _geovelo_report_osm_facilities f
        JOIN _geovelo_report_communes c ON ST_Intersects(f.geom, c.geom)
        WHERE f.family = 'other_car_free_paths'
        GROUP BY c.code, c.nom
        ORDER BY c.code
    """).fetchall()
    distinct_rows = connection.execute("""
        SELECT source_field, coalesce(amenagement, '(blank)') AS value,
               count(*) AS feature_count
        FROM _geovelo_report_sides
        GROUP BY source_field, value
        ORDER BY source_field, value
    """).fetchall()
    excluded_rows = connection.execute("""
        SELECT source_field, amenagement, count(*) AS side_count,
               sum(ST_Length(geom)) AS length_m
        FROM _geovelo_report_sides
        WHERE amenagement IS NOT NULL AND family IS NULL
        GROUP BY source_field, amenagement
        ORDER BY source_field, amenagement
    """).fetchall()

    lines = [
        _GÉOVÉLO_HEADING,
        "",
        f"- Géovélo source: `{source_id}`.",
        f"- Scope: department `{department}` only; geometries are clipped to "
        "configured commune contours in EPSG:3035.",
        "- OSM lengths use each tagged way geometry once per facility side, "
        "not directed-edge lengths. Designated separate facilities count once "
        "regardless of direction; generic `cycleway=lane` counts on both "
        "sides. Géovélo amenagement sides each count once except a separated "
        "facility shared by both fields.",
        f"- Matching threshold: {config.geovelo_report.match_tolerance_m:g} m; "
        f"same-family OSM nearest-line matching uses points spaced at most "
        f"{config.geovelo_report.match_sample_spacing_m:g} m apart, weighted "
        "by represented length.",
        "- Géovélo's dataset is built from OpenStreetMap; this checks our "
        "classification against Géovélo's, not OSM's completeness.",
        "",
        "### Distinct Géovélo amenagement values",
        "",
        "| Field | Value | Features |",
        "|---|---|---:|",
    ]
    lines.extend(
        f"| {source_field} | {value} | {count:,} |"
        for source_field, value, count in distinct_rows
    )
    lines.extend([
        "",
        "### Length by commune and family",
        "",
        "| Commune code | Commune | Family | OSM (m) | Géovélo (m) |",
        "|---|---|---|---:|---:|",
    ])
    lines.extend(
        f"| {code} | {commune} | {family} | "
        f"{_format_length(osm_length)} | {_format_length(geovelo_length)} |"
        for code, commune, family, osm_length, geovelo_length in length_rows
    )
    lines.extend([
        "",
        "### Géovélo length matched to the nearest same-family OSM line",
        "",
        "| Family | Géovélo length (m) | Matched (m) | Share |",
        "|---|---:|---:|---:|",
    ])
    for family, (total, matched) in match_rows:
        share = matched / total if total else None
        lines.append(
            f"| {family} | {_format_length(total)} | "
            f"{_format_length(matched)} | "
            f"{'n/a' if share is None else f'{share:.1%}'} |"
        )
    lines.extend([
        "",
        "### Other car-free paths open to bikes (reported separately)",
        "",
        "| Commune code | Commune | OSM length (m) |",
        "|---|---|---:|",
    ])
    lines.extend(
        f"| {code} | {commune} | {_format_length(length)} |"
        for code, commune, length in other_path_rows
    )
    lines.extend([
        "",
        "### Excluded and counted Géovélo values",
        "",
        "| Field | Value | Sides | Length (m) |",
        "|---|---|---:|---:|",
    ])
    lines.extend(
        f"| {source_field} | {value} | {count:,} | "
        f"{_format_length(length)} |"
        for source_field, value, count, length in excluded_rows
    )
    lines.extend([
        "",
        "Unmapped non-empty values and values mapped to `null` in "
        "`config/network.yaml` are excluded from family totals and listed "
        "above. Blank values are shown in the distinct-value table but are "
        "not counted as facilities.",
    ])
    _append_section(Path(report_path), lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.geovelo_report")
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pilot-config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Write the standalone department-only Géovélo section for a pilot report."""
    args = _parser().parse_args(argv)
    config = load_network_config(args.config)
    source_id = config.geovelo_report.source_ids_by_state.get(args.state)
    if source_id is None:
        raise ValueError(f"no Géovélo source configured for state {args.state}")
    pilot = load_pilot_config(args.pilot_config)
    sources = {source.id: source for source in load_manifest(args.manifest)}
    geovelo_source = sources.get(source_id)
    contour_source = sources.get(config.contour_source_id)
    if geovelo_source is None:
        raise ValueError(f"Géovélo source {source_id!r} is not in the manifest")
    if contour_source is None:
        raise ValueError(
            f"contour source {config.contour_source_id!r} is not in the manifest"
        )

    input_directory = (
        Path(pilot.paths["interim"]) / "osm" / str(args.state) / "pilot"
    )
    output_directory = (
        Path(pilot.paths["base"]) / "network" / str(args.state) / "pilot"
    )
    report_path = args.report
    connection = duckdb.connect()
    try:
        configure_extraction_connection(connection, pilot.paths["interim"])
        write_geovelo_report_section(
            connection,
            report_path,
            ways_path=input_directory / "ways.parquet",
            nodes_path=input_directory / "nodes.parquet",
            edges_path=output_directory / "edges.parquet",
            geovelo_path=geovelo_source.local_path,
            contours_path=contour_source.local_path,
            department=pilot.department,
            source_id=source_id,
            config=config,
        )
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
