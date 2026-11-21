import numpy as np
import pytest
from mobgrid.osm.elevation import edge_elevation_profile, sample_elevations


def _grid(path, x_corner, rows):
    path.write_text(
        "ncols 2\nnrows 2\n"
        f"xllcorner {x_corner}\nyllcorner 0\ncellsize 25\n"
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
