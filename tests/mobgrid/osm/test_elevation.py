import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.osm.elevation import (
    ElevationSummary,
    edge_elevation_profile,
    enrich_edges_with_elevation,
    sample_elevations,
    write_elevation_report,
)


def _grid(path, x_corner, rows, y_corner=0):
    path.write_text(
        f"ncols {len(rows[0])}\nnrows {len(rows)}\n"
        f"xllcorner {x_corner}\nyllcorner {y_corner}\ncellsize 25\n"
        "NODATA_value -9999\n"
        + "\n".join(" ".join(str(value) for value in row) for row in rows)
        + "\n",
        encoding="ascii",
    )


def test_bilinear_interpolation_across_tiles_and_nodata(tmp_path):
    west = tmp_path / "west.asc"
    east = tmp_path / "east.asc"
    _grid(west, 0, [[10, 20], [0, 10]])
    _grid(east, 50, [[30, -9999], [20, 30]])

    elevations = sample_elevations(
        [west, east],
        np.array([25.0, 50.0, 62.5, 75.0, -100.0]),
        np.array([25.0, 25.0, 37.5, 37.5, 25.0]),
    )
    assert elevations[:3] == pytest.approx([10.0, 20.0, 30.0])
    assert np.isnan(elevations[3:]).all()


def test_directional_elevation_profile_and_missing_nodes():
    forward = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([10.0, 15.0, 12.0])
    )
    reverse = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([12.0, 15.0, 10.0])
    )
    assert forward.climb_m == pytest.approx(5.0)
    assert forward.descent_m == pytest.approx(3.0)
    assert reverse.climb_m == pytest.approx(forward.descent_m)
    assert reverse.descent_m == pytest.approx(forward.climb_m)
    assert forward.mean_grade == pytest.approx(0.01)
    assert reverse.mean_grade == pytest.approx(-0.01)
    missing = edge_elevation_profile(
        np.array([100.0, 100.0]), np.array([10.0, np.nan, 12.0])
    )
    assert missing.climb_m is None
    assert missing.mean_grade is None


def test_unaligned_grids_are_rejected(tmp_path):
    west = tmp_path / "west.asc"
    east = tmp_path / "east.asc"
    _grid(west, 0, [[10, 20], [0, 10]])
    _grid(east, 51, [[30, 40], [20, 30]])
    with pytest.raises(ValueError, match="unaligned ASCII grid"):
        sample_elevations([west, east], np.array([25.0]), np.array([25.0]))


def test_edge_elevation_profiles_keep_direction_and_report_uncovered_nodes(
    tmp_path,
):
    import duckdb

    grid = tmp_path / "tile.asc"
    _grid(grid, 700000, [[10, 15, 12], [10, 15, 12]], y_corner=6600000)
    edges = tmp_path / "edges.parquet"
    nodes = tmp_path / "nodes.parquet"
    ways = tmp_path / "ways.parquet"
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    connection.register(
        "_test_lambert93",
        pa.table(
            {
                "x": [700012.5, 700037.5, 700062.5, 701000.0],
                "y": [6600012.5] * 4,
            }
        ),
    )
    coordinates = connection.execute("""
        SELECT ST_X(ST_Transform(
                   ST_Point(x, y), 'EPSG:2154', 'EPSG:3035', true
               )) AS x,
               ST_Y(ST_Transform(
                   ST_Point(x, y), 'EPSG:2154', 'EPSG:3035', true
               )) AS y
        FROM _test_lambert93
    """).fetchall()
    pq.write_table(
        pa.table(
            {
                "edge_key": ["10:0:foot:f", "10:0:foot:r", "11:0:foot:f"],
                "way_id": [10, 10, 11],
                "is_forward": [True, False, True],
                "node_ids": pa.array(
                    [[1, 2, 3], [3, 2, 1], [3, 4]],
                    type=pa.list_(pa.int64()),
                ),
                "length_m": [50.0, 50.0, 25.0],
            }
        ),
        edges,
    )
    pq.write_table(
        pa.table(
            {
                "node_id": [1, 2, 3, 4],
                "x": [row[0] for row in coordinates],
                "y": [row[1] for row in coordinates],
                "graph_node": [True, False, True, True],
            }
        ),
        nodes,
    )
    pq.write_table(pa.table({
        "way_id": [10, 11],
        "refs": [[1, 2, 3], [3, 4]],
        "tags": pa.array([{}, {}], type=pa.map_(pa.string(), pa.string())),
    }), ways)

    try:
        summary = enrich_edges_with_elevation(
            connection, edges, nodes, [grid], ways_path=ways,
            way_elevations_path=tmp_path / "way_elevations.parquet",
        )
        profiles = {
            row[0]: row[1:]
            for row in connection.execute(
                f"SELECT edge_key, climb_m, descent_m, mean_grade "
                f"FROM read_parquet('{edges.as_posix()}')"
            ).fetchall()
        }
        node_elevations = connection.execute(
            f"SELECT node_id, elevation_m FROM read_parquet('{nodes.as_posix()}') "
            "ORDER BY node_id"
        ).fetchall()
    finally:
        connection.close()

    assert profiles["10:0:foot:f"][:2] == pytest.approx((5.0, 3.0))
    assert profiles["10:0:foot:f"][2] == pytest.approx(0.04, abs=1e-4)
    assert profiles["10:0:foot:r"][:2] == pytest.approx((3.0, 5.0))
    assert profiles["10:0:foot:r"][2] == pytest.approx(-0.04, abs=1e-4)
    assert profiles["11:0:foot:f"] == (None, None, None)
    assert summary.nodes_without_elevation == 1
    assert summary.nodes_without_tile == 1
    assert [row[1] for row in node_elevations[:3]] == pytest.approx(
        [10.0, 15.0, 12.0]
    )
    assert node_elevations[3][1] is None


def test_elevation_report_distinguishes_uncovered_nodes_from_missing_samples(
    tmp_path,
):
    report = tmp_path / "elevation.md"

    write_elevation_report(
        ElevationSummary(3, 2, 1, 1),
        report,
        state=2021,
        area="pilot",
        tile_count=2,
    )

    contents = report.read_text(encoding="utf-8")
    assert "Nodes with no covering tile: 1" in contents
    assert "Nodes with no valid elevation sample: 2" in contents


@pytest.mark.parametrize("structure", ["bridge", "tunnel"])
def test_structure_profile_interpolates_between_portals_per_way(tmp_path, structure):
    import duckdb

    grid = tmp_path / "tile.asc"
    _grid(grid, 700000, [[10, -20, 12], [10, -20, 12]], y_corner=6600000)
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    coordinates = connection.execute("""
        SELECT ST_X(p), ST_Y(p)
        FROM (
            SELECT ST_Transform(
                ST_Point(x, 6600012.5), 'EPSG:2154', 'EPSG:3035', true
            ) AS p
            FROM unnest([700012.5, 700037.5, 700062.5]) AS points(x)
        )
    """).fetchall()
    nodes = tmp_path / "nodes.parquet"
    ways = tmp_path / "ways.parquet"
    edges = tmp_path / "edges.parquet"
    profiles = tmp_path / "way_elevations.parquet"
    pq.write_table(pa.table({
        "node_id": [1, 2, 3],
        "x": [point[0] for point in coordinates],
        "y": [point[1] for point in coordinates],
        "graph_node": [True, True, True],
    }), nodes)
    pq.write_table(pa.table({
        "way_id": [10, 11],
        "refs": [[1, 2, 3], [1, 2, 3]],
        "tags": pa.array(
            [{structure: "yes"}, {structure: "no"}],
            type=pa.map_(pa.string(), pa.string()),
        ),
    }), ways)
    pq.write_table(pa.table({
        "edge_key": [
            "10:0:foot:f", "10:0:foot:r", "10:1:foot:f", "11:0:foot:f"
        ],
        "way_id": [10, 10, 10, 11],
        "is_forward": [True, False, True, True],
        "node_ids": [[1, 2], [2, 1], [2, 3], [1, 2]],
        "length_m": [25.0, 25.0, 25.0, 25.0],
    }), edges)
    try:
        summary = enrich_edges_with_elevation(
            connection, edges, nodes, [grid], ways_path=ways,
            way_elevations_path=profiles,
        )
        values = connection.execute(
            "SELECT way_id, node_id, elevation_m FROM read_parquet(?) "
            "ORDER BY way_id, node_sequence", [str(profiles)]
        ).fetchall()
        edge_profiles = connection.execute(
            "SELECT edge_key, node_elevations_m FROM read_parquet(?) "
            "ORDER BY edge_key", [str(edges)]
        ).fetchall()
    finally:
        connection.close()

    assert [row[2] for row in values[:3]] == pytest.approx([10, 11, 12], abs=1e-3)
    assert values[4][2] == pytest.approx(-20, abs=1e-3)
    assert edge_profiles[0][1] == pytest.approx([10, 11], abs=1e-3)
    assert edge_profiles[1][1] == pytest.approx([11, 10], abs=1e-3)
    assert edge_profiles[3][1] == pytest.approx([10, -20], abs=1e-3)
    assert getattr(summary, f"{structure}_length_m") == pytest.approx(50, abs=0.1)
    other = "tunnel" if structure == "bridge" else "bridge"
    assert getattr(summary, f"{other}_length_m") == 0
