"""Synthetic acceptance tests for experimental composition downscaling."""

import duckdb
import pyarrow as pa
import pytest


def test_direct_weights_preserve_controls_and_count_household_fallbacks() -> None:
    from landgrid.origins.composition import apply_direct_weights

    controls = {
        "men_prop": 12.0, "men_mais": 9.0, "men_coll": 6.0,
        "log_soc": 3.0, "log_av45": 2.0, "log_45_70": 4.0,
        "log_70_90": 6.0, "log_ap90": 8.0, "log_inc": 10.0,
    }
    rows = [
        {"cell_id": 1, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "men": 2.0, **{key: value * 0.25 for key, value in controls.items()}},
        {"cell_id": 2, "natural_cell_id": "a", "natural_cell_size_m": 1000,
         "men": 6.0, **{key: value * 0.75 for key, value in controls.items()}},
    ]
    ff = pa.Table.from_pylist([
        {
            "cell_id": cell_id,
            "owner_occupied_main_residences": owner,
            "main_residence_houses": houses,
            "main_residence_flats": flats,
            "social_housing_main_residences": 0,
            "construction_av45": 0,
            "construction_45_70": 0,
            "construction_70_90": 0,
            "construction_ap90": 0,
            "construction_inc": 0,
        }
        for cell_id, owner, houses, flats in ((1, 3, 0, 1), (2, 1, 2, 1))
    ])
    with duckdb.connect() as connection:
        connection.register("benchmark", pa.Table.from_pylist(rows))
        connection.execute(
            "CREATE TEMP TABLE _composition_origins AS SELECT * FROM benchmark"
        )
        fallbacks = apply_direct_weights(connection, ff, 200)
        actual = connection.execute(
            "SELECT * FROM _composition_origins ORDER BY cell_id"
        ).to_arrow_table().to_pylist()
    assert actual[0]["men_prop"] == pytest.approx(9)
    assert actual[0]["men_mais"] == 0
    assert actual[0]["men_coll"] == pytest.approx(3)
    assert actual[0]["log_soc"] == pytest.approx(0.75)
    for key, total in controls.items():
        assert sum(row[key] for row in actual) == pytest.approx(total, rel=1e-9)
    assert fallbacks["log_soc"] == 1
    assert fallbacks["men_prop"] == 0
