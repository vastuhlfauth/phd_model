"""Unit tests for the shared trip-leg energy computation
(``mobgrid.budget.trip_legs``), survey-agnostic: section 9.9's density
proxy (the urban-unit-status x residence-size table of "Change between
2008 and 2019").
"""

from __future__ import annotations

import duckdb
import pytest
from mobgrid.budget import trip_legs


@pytest.mark.parametrize(
    ("uu_status", "tuu_res", "expected"),
    [
        # City centre (C): sparse / intermediate / dense, by residence size.
        ("C", "0", "sparse"), ("C", "3", "sparse"),
        ("C", "4", "intermediate"), ("C", "6", "intermediate"),
        ("C", "7", "dense"), ("C", "8", "dense"),
        # Suburb (B): sparse / intermediate / intermediate.
        ("B", "0", "sparse"), ("B", "3", "sparse"),
        ("B", "4", "intermediate"), ("B", "6", "intermediate"),
        ("B", "7", "intermediate"), ("B", "8", "intermediate"),
        # Isolated town (I): always sparse.
        ("I", "0", "sparse"), ("I", "4", "sparse"), ("I", "8", "sparse"),
        # Rural, outside urban units (R): always very_sparse.
        ("R", "0", "very_sparse"), ("R", "4", "very_sparse"),
        ("R", "8", "very_sparse"),
        # Unmapped/missing status or size: the grid's own stray-code
        # fallback, 'intermediate'.
        (None, "7", "intermediate"), ("C", None, "intermediate"),
        ("H", "7", "intermediate"),
    ],
)
def test_density_proxy_table_matches_section_9_9(
    uu_status: str | None, tuu_res: str | None, expected: str
) -> None:
    def _sql_literal(value: str | None) -> str:
        return "NULL::VARCHAR" if value is None else f"{value!r}::VARCHAR"

    con = duckdb.connect()
    case_sql = trip_legs.density_proxy_case_sql("uu_status", "tuu_res")
    row = con.sql(f"""
        SELECT ({case_sql}) FROM (
            SELECT {_sql_literal(uu_status)} AS uu_status,
                {_sql_literal(tuu_res)} AS tuu_res
        )
    """).fetchone()
    assert row[0] == expected
