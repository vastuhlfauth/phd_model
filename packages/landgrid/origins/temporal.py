"""Temporal census growth helpers for the approved section-6.3 exception."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import duckdb

from landgrid.origins.fichiers_fonciers import _quoted_identifier


def projected_growth_factor(
    start_value: float,
    end_value: float,
    *,
    observed_years: float,
    projected_years: float,
) -> float:
    """Project a census growth factor across years using geometric growth."""
    values = (start_value, end_value, observed_years, projected_years)
    if (
        not all(math.isfinite(value) for value in values)
        or start_value <= 0
        or end_value < 0
        or observed_years <= 0
        or projected_years <= 0
    ):
        raise ValueError("invalid growth inputs")
    if end_value == 0:
        return 0.0
    exponent = projected_years / observed_years
    factor = math.exp((math.log(end_value) - math.log(start_value)) * exponent)
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("projected growth factor is not finite and positive")
    return factor


def rescale_age_margins(
    age_margins: Mapping[str, float],
    *,
    individual_total: float,
) -> tuple[dict[str, float], float]:
    """Rescale census age margins to grown individuals before age IPF (6.3)."""
    if (
        not math.isfinite(individual_total)
        or individual_total < 0
        or not age_margins
        or any(
            not name or not math.isfinite(value) or value < 0
            for name, value in age_margins.items()
        )
    ):
        raise ValueError("invalid age margin inputs")
    age_total = math.fsum(age_margins.values())
    if age_total == 0:
        if individual_total == 0:
            return dict(age_margins), 1.0
        raise ValueError("positive individuals have no age margin support")
    adjustment = individual_total / age_total
    return (
        {name: value * adjustment for name, value in age_margins.items()},
        adjustment,
    )


def allocate_commune_controls(
    connection: duckdb.DuckDBPyConnection,
    *,
    base_relation: str,
    growth_relation: str,
    weights_relation: str,
    variables: Sequence[str],
    age_variables: Sequence[str],
    individual_variable: str = "ind",
) -> dict[str, int | float]:
    """Grow commune controls and split them to target cells, preserving margins."""
    variables = tuple(variables)
    age_variables = tuple(age_variables)
    if (
        not variables
        or len(variables) != len(set(variables))
        or len(age_variables) != len(set(age_variables))
        or set(age_variables) - set(variables)
        or individual_variable not in variables
    ):
        raise ValueError("invalid temporal allocation variables")
    base = _quoted_identifier(base_relation)
    growth = _quoted_identifier(growth_relation)
    weights = _quoted_identifier(weights_relation)
    for relation, keys in (
        (base, ("commune_code", *variables)),
        (growth, ("commune_code", *variables)),
        (weights, ("cell_id", "commune_code", *variables)),
    ):
        columns = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {relation}"
            ).fetchall()
        }
        missing = set(keys) - columns
        if missing:
            raise ValueError(
                f"temporal input {relation} lacks columns: {', '.join(sorted(missing))}"
            )
    duplicate_queries = (
        (
            base,
            "commune_code",
            "duplicate base commune controls",
        ),
        (
            growth,
            "commune_code",
            "duplicate commune growth factors",
        ),
        (
            weights,
            "cell_id, commune_code",
            "duplicate target cell-commune weights",
        ),
    )
    for relation, keys, message in duplicate_queries:
        duplicate_count = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT {keys} FROM {relation}
                GROUP BY {keys} HAVING count(*) > 1
            )
            """
        ).fetchone()[0]
        if duplicate_count:
            raise ValueError(message)
    for relation in (base, growth, weights):
        fields = (
            ("commune_code",) if relation != weights
            else ("cell_id", "commune_code")
        )
        key_checks = [
            f"{_quoted_identifier(name)} IS NULL" for name in fields
        ]
        key_checks.append(
            "trim(CAST(commune_code AS VARCHAR)) = ''"
        )
        values = " OR ".join(
            f"{_quoted_identifier(name)} IS NULL "
            f"OR NOT isfinite(try_cast({_quoted_identifier(name)} AS DOUBLE)) "
            f"OR try_cast({_quoted_identifier(name)} AS DOUBLE) < 0"
            for name in variables
        )
        invalid_count = connection.execute(
            f"SELECT count(*) FROM {relation} WHERE "
            f"{' OR '.join(key_checks)} "
            f"OR {values}"
        ).fetchone()[0]
        if invalid_count:
            raise ValueError(f"invalid numeric values in temporal input {relation}")

    grown = ",\n".join(
        f"CAST(b.{_quoted_identifier(name)} AS DOUBLE) "
        f"* CAST(g.{_quoted_identifier(name)} AS DOUBLE) "
        f"AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_controls_raw AS
        SELECT b.commune_code, {grown}
        FROM {base} b JOIN {growth} g USING (commune_code)
        """
    )
    overflow_checks = " OR ".join(
        f"NOT isfinite({_quoted_identifier(name)}) "
        f"OR {_quoted_identifier(name)} < 0"
        for name in variables
    )
    if connection.execute(
        f"SELECT count(*) FROM _temporal_controls_raw WHERE {overflow_checks}"
    ).fetchone()[0]:
        raise ValueError("grown commune controls are not finite")
    unmatched_base = int(connection.execute(
        f"""
        SELECT count(*) FROM {base} b
        LEFT JOIN {growth} g USING (commune_code)
        LEFT JOIN (
            SELECT DISTINCT commune_code FROM {weights}
        ) w USING (commune_code)
        WHERE g.commune_code IS NULL OR w.commune_code IS NULL
        """
    ).fetchone()[0])
    unmatched_target = int(connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT DISTINCT w.commune_code
            FROM {weights} w
            LEFT JOIN _temporal_controls_raw c USING (commune_code)
            WHERE c.commune_code IS NULL
        )
        """
    ).fetchone()[0])

    if age_variables:
        age_sum = " + ".join(
            _quoted_identifier(name) for name in age_variables
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _temporal_controls AS
            WITH totals AS (
                SELECT *, ({age_sum}) AS _age_total
                FROM _temporal_controls_raw
            )
            SELECT commune_code,
                {", ".join(
                    f"CASE WHEN _age_total > 0 "
                    f"THEN {_quoted_identifier(name)} * "
                    f"{_quoted_identifier(individual_variable)} / _age_total "
                    f"ELSE 0.0 END AS {_quoted_identifier(name)}"
                    if name in age_variables
                    else _quoted_identifier(name)
                    for name in variables
                )},
                CASE WHEN _age_total > 0
                    THEN {_quoted_identifier(individual_variable)} / _age_total
                    WHEN {_quoted_identifier(individual_variable)} = 0 THEN 1.0
                    ELSE NULL END AS _age_adjustment
            FROM totals
            """
        )
        unsupported = int(connection.execute(
            f"""
            SELECT count(*) FROM _temporal_controls_raw
            WHERE ({age_sum}) = 0
                AND {_quoted_identifier(individual_variable)} > 0
            """
        ).fetchone()[0])
        if unsupported:
            raise ValueError("positive individuals have no age margin support")
    else:
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _temporal_controls AS
            SELECT *, 1.0 AS _age_adjustment
            FROM _temporal_controls_raw
            """
        )

    weight_sums = ",\n".join(
        f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_weight_sums AS
        SELECT commune_code, {weight_sums}
        FROM {weights}
        GROUP BY commune_code
        """
    )
    for name in variables:
        unsupported = int(connection.execute(
            f"""
            SELECT count(*) FROM _temporal_controls c
            LEFT JOIN _temporal_weight_sums s USING (commune_code)
            WHERE c.{_quoted_identifier(name)} > 0
                AND coalesce(s.{_quoted_identifier(name)}, 0) <= 0
            """
        ).fetchone()[0])
        if unsupported:
            raise ValueError(
                f"positive {name} controls have zero target weights"
            )
    allocated = ",\n".join(
        f"CASE WHEN s.{_quoted_identifier(name)} > 0 "
        f"THEN c.{_quoted_identifier(name)} * w.{_quoted_identifier(name)} "
        f"/ s.{_quoted_identifier(name)} ELSE 0.0 END "
        f"AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_allocated AS
        SELECT w.cell_id, w.commune_code, {allocated}
        FROM {weights} w
        JOIN _temporal_controls c USING (commune_code)
        JOIN _temporal_weight_sums s USING (commune_code)
        """
    )
    cell_totals = ",\n".join(
        f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_target_cells AS
        SELECT cell_id, {cell_totals}
        FROM _temporal_allocated
        GROUP BY cell_id
        ORDER BY cell_id
        """
    )
    for name in variables:
        mismatches = int(connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT c.commune_code, c.{_quoted_identifier(name)} AS control,
                    coalesce(sum(a.{_quoted_identifier(name)}), 0) AS allocated
                FROM _temporal_controls c
                LEFT JOIN _temporal_allocated a USING (commune_code)
                GROUP BY c.commune_code, c.{_quoted_identifier(name)}
                HAVING abs(control - allocated) >
                    1e-9 * greatest(1.0, abs(control))
            )
            """
        ).fetchone()[0])
        if mismatches:
            raise RuntimeError(f"temporal allocation did not preserve {name} totals")

    age_adjustments = connection.execute(
        """
        SELECT count(*) FILTER (WHERE abs(_age_adjustment - 1.0) > 1e-12),
            min(_age_adjustment), max(_age_adjustment)
        FROM _temporal_controls
        """
    ).fetchone()
    return {
        "matched_communes": int(connection.execute(
            "SELECT count(*) FROM _temporal_controls"
        ).fetchone()[0]),
        "unmatched_base_communes": unmatched_base,
        "unmatched_target_communes": unmatched_target,
        "age_adjusted_communes": int(age_adjustments[0] or 0),
        "age_adjustment_min": float(age_adjustments[1] or 1.0),
        "age_adjustment_max": float(age_adjustments[2] or 1.0),
    }
