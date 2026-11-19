import duckdb
from common.grid import cell_id
from mobgrid.osm.config import load_network_config
from mobgrid.osm.edges import (
    build_directed_edges,
    connectivity_summaries,
    write_step06_report,
)


def _raw_tables(tmp_path):
    connection = duckdb.connect()
    ways_path = tmp_path / "ways.parquet"
    nodes_path = tmp_path / "nodes.parquet"
    connection.execute("""
        CREATE TABLE ways (
            way_id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            refs BIGINT[]
        )
    """)
    connection.execute("""
        INSERT INTO ways VALUES
            (1, map {'highway':'residential', 'oneway':'yes',
                     'maxspeed':'FR:urban'}, [1, 2, 3]),
            (2, map {'highway':'residential', 'oneway':'-1',
                     'maxspeed':'80 mph'}, [2, 4]),
            (3, map {'highway':'residential', 'oneway':'yes',
                     'oneway:bicycle':'no'}, [5, 6]),
            (4, map {'highway':'footway', 'access':'no', 'foot':'yes'}, [7, 8]),
            (5, map {'highway':'motorway'}, [9, 10]),
            (6, map {'highway':'trunk', 'motorroad':'yes'}, [11, 12]),
            (7, map {'highway':'residential', 'oneway':'yes',
                     'cycleway':'opposite_lane'}, [13, 14]),
            (8, map {'highway':'residential', 'junction':'roundabout'}, [15, 16]),
            (9, map {'highway':'residential', 'maxspeed':'walk'}, [17, 18]),
            (10, map {'highway':'residential', 'maxspeed':'none'}, [19, 20]),
            (11, map {'highway':'residential', 'maxspeed':'unknown'}, [21, 22]),
            (12, map {'highway':'residential', 'maxspeed':'30 km/h'}, [23, 24]),
            (13, map {'highway':'service', 'access':'no',
                      'motor_vehicle':'yes', 'motorcar':'no'}, [25, 26]),
            (14, map {'highway':'footway', 'access':'no',
                      'bicycle':'yes'}, [27, 28]),
            (15, map {'highway':'residential', 'access':'no',
                      'motor_vehicle':'yes'}, [29, 30]),
            (16, map {'highway':'residential', 'oneway':'yes',
                      'cycleway:right:oneway':'-1'}, [31, 32]),
            (17, map {'highway':'residential', 'oneway':'yes',
                      'cycleway:oneway':'no'}, [33, 34]),
            (18, map {'highway':'residential', 'oneway':'yes',
                      'oneway:bicycle':'yes',
                      'cycleway':'opposite_lane'}, [35, 36]),
            (19, map {'highway':'residential',
                      'cycleway:right':'track'}, [37, 38]),
            (20, map {'highway':'residential',
                      'cycleway:left':'lane'}, [39, 40])
    """)
    connection.execute("""
        CREATE TABLE nodes (
            node_id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            lat DOUBLE,
            lon DOUBLE
        )
    """)
    node_rows = []
    for node_id in range(1, 41):
        tags = (
            "map {'highway':'traffic_signals'}"
            if node_id == 3
            else "map {'highway':'stop'}"
            if node_id == 2
            else "map()::MAP(VARCHAR, VARCHAR)"
        )
        node_rows.append(
            f"({node_id}, {tags}, 44.0, {0.01 + node_id * 0.001})"
        )
    connection.execute(
        "INSERT INTO nodes VALUES " + ", ".join(node_rows)
    )
    connection.execute(
        "COPY ways TO ? (FORMAT PARQUET)", [str(ways_path)]
    )
    connection.execute(
        "COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)]
    )
    return connection, ways_path, nodes_path


def _build(tmp_path):
    connection, ways_path, nodes_path = _raw_tables(tmp_path)
    result = build_directed_edges(
        connection,
        ways_path,
        nodes_path,
        tmp_path / "base",
        config=load_network_config("config/network.yaml"),
    )
    return connection, result


def test_splits_ways_at_shared_graph_nodes_and_reverses_node_order(tmp_path) -> None:
    connection, result = _build(tmp_path)

    segments = connection.execute(
        """
        SELECT is_forward, node_ids
        FROM read_parquet(?)
        WHERE way_id = 1 AND mode = 'foot'
        ORDER BY is_forward DESC, from_node_id
        """,
        [result.edges_path],
    ).fetchall()
    assert segments == [
        (True, [1, 2]),
        (True, [2, 3]),
        (False, [2, 1]),
        (False, [3, 2]),
    ]
    endpoint = connection.execute(
        """
        SELECT signal_count, junction_count, length_m, geometry_wkb
        FROM read_parquet(?)
        WHERE way_id = 1 AND mode = 'foot' AND is_forward
          AND from_node_id = 2 AND to_node_id = 3
        """,
        [result.edges_path],
    ).fetchone()
    assert endpoint is not None
    assert endpoint[0:2] == (1, 0)
    assert endpoint[2] > 0
    assert endpoint[3] is not None
    grid_ids = connection.execute(
        """
        SELECT cell_1km_id, tile_id,
               ST_X(ST_Centroid(ST_GeomFromWKB(geometry_wkb))) AS easting_m,
               ST_Y(ST_Centroid(ST_GeomFromWKB(geometry_wkb))) AS northing_m
        FROM read_parquet(?)
        WHERE way_id = 1 AND mode = 'foot' AND is_forward
          AND from_node_id = 2 AND to_node_id = 3
        """,
        [result.edges_path],
    ).fetchone()
    assert grid_ids[0] == cell_id(grid_ids[3], grid_ids[2], 1000)
    assert grid_ids[1] == cell_id(grid_ids[3], grid_ids[2], 50_000)

    shared = connection.execute(
        "SELECT graph_node FROM read_parquet(?) WHERE node_id = 2",
        [result.nodes_path],
    ).fetchone()
    assert shared == (True,)


def test_oneway_variants_are_applied_per_mode(tmp_path) -> None:
    connection, result = _build(tmp_path)
    rows = connection.execute(
        """
        SELECT DISTINCT way_id, mode, is_forward
        FROM read_parquet(?)
        WHERE way_id IN (1, 2, 3, 7, 8, 16, 17, 18)
        ORDER BY way_id, mode, is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    directions = {}
    for way_id, mode, forward in rows:
        directions.setdefault((way_id, mode), []).append(forward)

    assert directions[(1, "car")] == [True]
    assert directions[(1, "bike")] == [True]
    assert directions[(1, "foot")] == [True, False]
    assert directions[(2, "car")] == [False]
    assert directions[(2, "bike")] == [False]
    assert directions[(2, "foot")] == [True, False]
    assert directions[(3, "car")] == [True]
    assert directions[(3, "bike")] == [True, False]
    assert directions[(7, "bike")] == [True, False]
    assert directions[(8, "car")] == [True]
    assert directions[(8, "bike")] == [True]
    assert directions[(16, "bike")] == [True, False]
    assert directions[(17, "bike")] == [True, False]
    assert directions[(18, "bike")] == [True]

    infrastructure = connection.execute(
        """
        SELECT way_id, mode, is_forward, bike_infra
        FROM read_parquet(?)
        WHERE way_id IN (19, 20) AND mode = 'bike'
        ORDER BY way_id, is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    assert infrastructure == [
        (19, "bike", True, "separated_track_path"),
        (19, "bike", False, "mixed_traffic"),
        (20, "bike", True, "mixed_traffic"),
        (20, "bike", False, "painted_lane"),
    ]


def test_access_exclusions_and_maxspeed_parsing(tmp_path) -> None:
    connection, result = _build(tmp_path)
    access = connection.execute(
        """
        SELECT way_id, mode
        FROM read_parquet(?)
        WHERE way_id IN (4, 5, 6, 13, 14, 15)
        GROUP BY way_id, mode
        ORDER BY way_id, mode
        """,
        [result.edges_path],
    ).fetchall()
    assert access == [
        (4, "foot"),
        (5, "car"),
        (6, "car"),
        (14, "bike"),
        (15, "car"),
    ]

    speeds = connection.execute(
        """
        SELECT DISTINCT way_id, maxspeed_kmh
        FROM read_parquet(?)
        WHERE way_id IN (1, 2, 9, 10, 11, 12)
          AND mode = 'car'
        ORDER BY way_id
        """,
        [result.edges_path],
    ).fetchall()
    assert speeds == [
        (1, 50.0),
        (2, 128.74752),
        (9, 5.0),
        (10, None),
        (11, None),
        (12, 30.0),
    ]


def test_pilot_report_contains_connectivity_and_edge_checks(tmp_path) -> None:
    connection, result = _build(tmp_path)
    report = tmp_path / "step06_osm_pilot.md"

    write_step06_report(
        connection,
        result.edges_path,
        report,
        state=2021,
        area="pilot",
    )

    text = report.read_text(encoding="utf-8")
    assert "Edges and length by highway class and mode" in text
    assert "Largest strongly connected component" in text
    assert "| car |" in text
    assert "| bike |" in text
    assert "| foot |" in text
    assert "Zero-length directed edges" in text
    assert "Maxspeed coverage by class and mode" in text
    assert "Bike infrastructure length" in text


def test_largest_strong_component_counts_nodes_and_directed_length(tmp_path) -> None:
    connection = duckdb.connect()
    edges = tmp_path / "scc_edges.parquet"
    connection.execute("""
        COPY (
            SELECT * FROM (VALUES
                ('car', 1::BIGINT, 2::BIGINT, 1.0::DOUBLE),
                ('car', 2::BIGINT, 1::BIGINT, 2.0::DOUBLE),
                ('car', 2::BIGINT, 3::BIGINT, 1.0::DOUBLE),
                ('car', 3::BIGINT, 4::BIGINT, 2.0::DOUBLE)
            ) AS e(mode, from_node_id, to_node_id, length_m)
        ) TO ? (FORMAT PARQUET)
    """, [str(edges)])

    summaries = {
        summary.mode: summary
        for summary in connectivity_summaries(connection, edges)
    }

    assert summaries["car"].node_count == 4
    assert summaries["car"].largest_component_nodes == 2
    assert summaries["car"].largest_component_length_share == 0.5
    assert summaries["bike"].node_count == 0
