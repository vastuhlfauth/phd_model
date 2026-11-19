import duckdb
from common.grid import cell_id
from mobgrid.osm.config import load_network_config
from mobgrid.osm.edges import (
    _build_graph_nodes,
    _build_points_sql,
    _build_segments_sql,
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
                      'cycleway:left':'lane'}, [39, 40]),
            (21, map {'highway':'construction', 'access':'yes'}, [41, 42]),
            (22, map {'highway':'proposed', 'access':'yes'}, [43, 44]),
            (23, map {'highway':'abandoned', 'access':'yes'}, [45, 46]),
            (24, map {'highway':'razed', 'access':'yes'}, [47, 48]),
            (25, map {'highway':'disused', 'access':'yes'}, [49, 50]),
            (26, map {'highway':'raceway', 'access':'yes'}, [51, 52]),
            (27, map {'highway':'bus_guideway', 'access':'yes'}, [53, 54]),
            (28, map {'highway':'escape', 'access':'yes'}, [55, 56]),
            (29, map {'highway':'elevator', 'access':'yes'}, [57, 58]),
            (30, map {'highway':'platform', 'access':'yes'}, [59, 60]),
            (31, map {'highway':'busway', 'access':'yes'}, [61, 62]),
            (32, map {'highway':'track', 'access':'yes'}, [63, 64]),
            (33, map {'highway':'residential',
                      'access':'no;private'}, [65, 66]),
            (34, map {'highway':'residential',
                      'access':'no;yes'}, [67, 68]),
            (35, map {'highway':'pedestrian'}, [69, 70]),
            (36, map {'highway':'residential',
                      'junction':'circular'}, [71, 72]),
            (37, map {'highway':'residential'}, [73, 74, 75]),
            (38, map {'highway':'residential'}, [76, 77, 78]),
            (39, map {'highway':'residential'}, [79, 80, 81]),
            (40, map {'highway':'residential'}, [82, 83, 84]),
            (41, map {'highway':'footway', 'access':'yes'}, [85, 86]),
            (42, map {'highway':'footway', 'motorcar':'yes'}, [87, 88]),
            (43, map {'highway':'path', 'access':'yes'}, [89, 90]),
            (44, map {'highway':'path', 'motor_vehicle':'yes'}, [91, 92]),
            (45, map {'highway':'pedestrian', 'access':'yes'}, [93, 94]),
            (46, map {'highway':'pedestrian', 'motorcar':'designated'}, [95, 96]),
            (47, map {'highway':'cycleway', 'access':'yes'}, [97, 98]),
            (48, map {'highway':'cycleway', 'motor_vehicle':'customers'}, [99, 100]),
            (49, map {'highway':'bridleway', 'access':'yes'}, [101, 102]),
            (50, map {'highway':'bridleway', 'motorcar':'permissive'}, [103, 104]),
            (51, map {'highway':'steps', 'access':'yes'}, [105, 106]),
            (52, map {'highway':'steps', 'motor_vehicle':'yes'}, [107, 108]),
            (53, map {'highway':'corridor', 'access':'yes'}, [109, 110]),
            (54, map {'highway':'corridor', 'motor_vehicle':'yes'}, [111, 112]),
            (55, map {'highway':'bus_stop', 'access':'yes'}, [113, 114]),
            (56, map {'highway':'bus_stop', 'motor_vehicle':'yes'}, [115, 116]),
            (57, map {'highway':'platform', 'access':'yes'}, [117, 118]),
            (58, map {'highway':'platform', 'motor_vehicle':'yes'}, [119, 120]),
            (59, map {'highway':'elevator', 'access':'yes'}, [121, 122]),
            (60, map {'highway':'elevator', 'motor_vehicle':'yes'}, [123, 124]),
            (61, map {'highway':'footway', 'access':'yes'}, [125, 126]),
            (62, map {'highway':'footway', 'bicycle':'yes'}, [127, 128]),
            (63, map {'highway':'steps', 'access':'yes'}, [129, 130]),
            (64, map {'highway':'steps', 'bicycle':'yes'}, [131, 132]),
            (65, map {'highway':'pedestrian', 'access':'yes'}, [133, 134]),
            (66, map {'highway':'pedestrian', 'bicycle':'yes'}, [135, 136]),
            (67, map {'highway':'residential',
                      'zone:traffic':'FR:urban'}, [137, 138]),
            (68, map {'highway':'residential',
                      'source:maxspeed':'FR:rural'}, [139, 140]),
            (69, map {'highway':'residential',
                      'maxspeed:type':'FR:zone30'}, [141, 142]),
            (70, map {'highway':'residential',
                      'zone:maxspeed':'FR:motorway'}, [143, 144])
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
    for node_id in range(1, 145):
        tags = (
            "map {'highway':'traffic_signals'}"
            if node_id == 3
            else "map {'highway':'stop'}"
            if node_id == 2
            else "map {'highway':'traffic_signals', "
            "'traffic_signals:direction':'forward'}"
            if node_id == 74
            else "map {'highway':'crossing', 'direction':'both'}"
            if node_id == 77
            else "map {'highway':'give_way', 'direction':'backward'}"
            if node_id == 80
            else "map {'highway':'mini_roundabout', 'direction':'both'}"
            if node_id == 83
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
        SELECT signal_count, stop_count, crossing_count,
               mini_roundabout_count, length_m, geometry_wkb
        FROM read_parquet(?)
        WHERE way_id = 1 AND mode = 'foot' AND is_forward
          AND from_node_id = 2 AND to_node_id = 3
        """,
        [result.edges_path],
    ).fetchone()
    assert endpoint is not None
    assert endpoint[0:4] == (1, 0, 0, 0)
    assert endpoint[4] > 0
    assert endpoint[5] is not None
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
        WHERE way_id IN (1, 2, 3, 7, 8, 16, 17, 18, 36)
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
    assert directions[(36, "car")] == [True]
    assert directions[(36, "bike")] == [True]
    assert directions[(36, "foot")] == [True, False]

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


def test_speed_context_uses_all_kept_hint_tags(tmp_path) -> None:
    connection, result = _build(tmp_path)
    contexts = connection.execute(
        """
        SELECT DISTINCT way_id, speed_context
        FROM read_parquet(?)
        WHERE way_id BETWEEN 67 AND 70 AND mode = 'car'
        ORDER BY way_id
        """,
        [result.edges_path],
    ).fetchall()
    assert contexts == [
        (67, "urban"),
        (68, "rural"),
        (69, "zone30"),
        (70, "motorway"),
    ]


def test_unusable_highways_access_lists_and_pedestrian_bike_access(
    tmp_path,
) -> None:
    connection, result = _build(tmp_path)
    common_exclusions = connection.execute(
        """
        SELECT DISTINCT way_id, mode
        FROM read_parquet(?)
        WHERE way_id BETWEEN 21 AND 29
        """,
        [result.edges_path],
    ).fetchall()
    assert common_exclusions == []
    car_exclusions = connection.execute(
        """
        SELECT DISTINCT way_id
        FROM read_parquet(?)
        WHERE way_id IN (30, 31) AND mode = 'car'
        """,
        [result.edges_path],
    ).fetchall()
    assert car_exclusions == []
    allowed_track = connection.execute(
        """
        SELECT count(*) FROM read_parquet(?)
        WHERE way_id = 32 AND mode = 'car'
        """,
        [result.edges_path],
    ).fetchone()[0]
    assert allowed_track == 2
    access_modes = connection.execute(
        """
        SELECT way_id, mode
        FROM read_parquet(?)
        WHERE way_id IN (33, 34, 35)
        GROUP BY way_id, mode
        ORDER BY way_id, mode
        """,
        [result.edges_path],
    ).fetchall()
    assert access_modes == [
        (34, "bike"),
        (34, "car"),
        (34, "foot"),
        (35, "bike"),
        (35, "foot"),
    ]


def test_nonroad_access_requires_mode_specific_tags(tmp_path) -> None:
    connection, result = _build(tmp_path)
    car_ways = connection.execute(
        """
        SELECT DISTINCT way_id
        FROM read_parquet(?)
        WHERE mode = 'car' AND way_id BETWEEN 41 AND 60
        ORDER BY way_id
        """,
        [result.edges_path],
    ).fetchall()
    assert car_ways == [(42,), (44,), (46,), (48,), (50,)]

    bike_ways = connection.execute(
        """
        SELECT DISTINCT way_id
        FROM read_parquet(?)
        WHERE mode = 'bike' AND way_id BETWEEN 61 AND 66
        ORDER BY way_id
        """,
        [result.edges_path],
    ).fetchall()
    assert bike_ways == [(62,), (64,), (65,), (66,)]


def test_directional_control_counts_and_to_degree(tmp_path) -> None:
    connection, result = _build(tmp_path)
    signal_counts = connection.execute(
        """
        SELECT is_forward, signal_count
        FROM read_parquet(?)
        WHERE way_id = 37 AND mode = 'foot'
        ORDER BY is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    assert signal_counts == [(True, 1), (False, 0)]

    crossing_counts = connection.execute(
        """
        SELECT is_forward, stop_count, crossing_count, mini_roundabout_count
        FROM read_parquet(?)
        WHERE way_id = 38 AND mode = 'foot'
        ORDER BY is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    assert crossing_counts == [(True, 0, 1, 0), (False, 0, 1, 0)]

    stop_counts = connection.execute(
        """
        SELECT is_forward, stop_count
        FROM read_parquet(?)
        WHERE way_id = 39 AND mode = 'foot'
        ORDER BY is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    assert stop_counts == [(True, 0), (False, 1)]

    mini_roundabout_counts = connection.execute(
        """
        SELECT is_forward, mini_roundabout_count
        FROM read_parquet(?)
        WHERE way_id = 40 AND mode = 'foot'
        ORDER BY is_forward DESC
        """,
        [result.edges_path],
    ).fetchall()
    assert mini_roundabout_counts == [(True, 1), (False, 1)]

    degree = connection.execute(
        """
        SELECT DISTINCT to_degree
        FROM read_parquet(?)
        WHERE mode = 'foot' AND to_node_id = 2
        """,
        [result.edges_path],
    ).fetchall()
    assert degree == [(3,)]


def test_edge_length_uses_ellipsoidal_node_coordinates(tmp_path) -> None:
    connection = duckdb.connect()
    ways_path = tmp_path / "ways.parquet"
    nodes_path = tmp_path / "nodes.parquet"
    connection.execute("""
        CREATE TABLE ways (
            way_id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            refs BIGINT[]
        );
        INSERT INTO ways VALUES
            (1, map {'highway':'residential'}, [1, 2]);
        CREATE TABLE nodes (
            node_id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            lat DOUBLE,
            lon DOUBLE
        );
        INSERT INTO nodes VALUES
            (1, map(), 0, 0),
            (2, map(), 0, 1);
    """)
    connection.execute("COPY ways TO ? (FORMAT PARQUET)", [str(ways_path)])
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])

    connection.execute("LOAD spatial")
    connection.execute(
        _build_points_sql(
            str(ways_path).replace("\\", "/"),
            str(nodes_path).replace("\\", "/"),
        )
    )
    _build_graph_nodes(connection)
    connection.execute(_build_segments_sql())
    lengths = connection.execute(
        """
        SELECT length_m, geom IS NOT NULL
        FROM _osm_way_segments
        WHERE way_id = 1
        """,
    ).fetchall()
    assert lengths == [(111_319.49079327357, True)]


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
