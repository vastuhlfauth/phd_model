"""Experimental section-6.3 composition weights."""

from pathlib import Path

import duckdb
import pyarrow as pa

from landgrid.origins.downscale import _relation
from landgrid.origins.fichiers_fonciers import _quoted_identifier

DIRECT_WEIGHTS = {
    "men_prop": "owner_occupied_main_residences",
    "men_mais": "main_residence_houses",
    "men_coll": "main_residence_flats",
    "log_soc": "social_housing_main_residences",
    "log_av45": "construction_av45",
    "log_45_70": "construction_45_70",
    "log_70_90": "construction_70_90",
    "log_ap90": "construction_ap90",
    "log_inc": "construction_inc",
}


def apply_direct_weights(
    connection: duckdb.DuckDBPyConnection,
    ff_cells: pa.Table | Path,
    resolution_m: int,
) -> dict[str, int]:
    """Redistribute matched counts by FF counterparts, preserving zone totals."""
    if resolution_m <= 0:
        raise ValueError("cell resolution must be positive")
    relation, registered = _relation(connection, "_composition_ff_input", ff_cells)
    try:
        counts = ", ".join(
            f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
            for name in DIRECT_WEIGHTS.values()
        )
        connection.execute(
            f"CREATE OR REPLACE TEMP TABLE _composition_ff AS "
            f"SELECT cell_id, {counts} FROM {relation} GROUP BY cell_id"
        )
        fallbacks: dict[str, int] = {}
        for variable, counterpart in DIRECT_WEIGHTS.items():
            column = _quoted_identifier(variable)
            weight = _quoted_identifier(counterpart)
            connection.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE _composition_direct AS
                WITH cells AS (
                    SELECT d.cell_id, d.natural_cell_id, d.natural_cell_size_m,
                        d.men, d.{column} AS original,
                        coalesce(f.{weight}, 0) AS weight
                    FROM _composition_origins d
                    LEFT JOIN _composition_ff f USING (cell_id)
                )
                SELECT *,
                    sum(original) OVER (PARTITION BY natural_cell_id) AS control,
                    sum(weight) OVER (PARTITION BY natural_cell_id) AS weight_sum,
                    sum(men) OVER (PARTITION BY natural_cell_id) AS household_sum
                FROM cells
                """
            )
            invalid = connection.execute(
                """
                SELECT count(*) FROM _composition_direct
                WHERE weight < 0 OR men < 0 OR original < 0
                    OR NOT isfinite(weight) OR NOT isfinite(men)
                    OR NOT isfinite(original)
                    OR (weight_sum = 0 AND household_sum = 0 AND control > 0)
                """
            ).fetchone()[0]
            if invalid:
                raise ValueError(f"invalid or zero direct weights for {variable}")
            fallbacks[variable] = int(connection.execute(
                """
                SELECT count(DISTINCT natural_cell_id) FROM _composition_direct
                WHERE natural_cell_size_m > ? AND weight_sum = 0
                """,
                [resolution_m],
            ).fetchone()[0])
            connection.execute(
                f"""
                UPDATE _composition_origins AS dest SET {column} = CASE
                    WHEN source.natural_cell_size_m = ? THEN source.original
                    WHEN source.weight_sum > 0
                        THEN source.control * source.weight / source.weight_sum
                    WHEN source.household_sum > 0
                        THEN source.control * source.men / source.household_sum
                    ELSE 0.0 END
                FROM _composition_direct AS source
                WHERE dest.cell_id = source.cell_id
                """,
                [resolution_m],
            )
        return fallbacks
    finally:
        if registered:
            connection.unregister("_composition_ff_input")
