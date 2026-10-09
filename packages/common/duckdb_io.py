"""DuckDB and Arrow I/O helpers for sections 14.2 and 14.5."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import duckdb
import pyarrow as pa


def open_connection(
    database: str | Path = ":memory:", *, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection for table work (section 14.2)."""
    return duckdb.connect(str(database), read_only=read_only)


def register_arrow(
    connection: duckdb.DuckDBPyConnection,
    name: str,
    table: pa.Table | pa.RecordBatchReader,
) -> None:
    """Register an Arrow object as a queryable DuckDB view."""
    connection.register(name, table)


def unregister_arrow(connection: duckdb.DuckDBPyConnection, name: str) -> None:
    """Remove an Arrow object previously registered on a connection."""
    connection.unregister(name)


def query_arrow(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: Sequence[object] | Mapping[str, object] | None = None,
) -> pa.Table:
    """Execute SQL and return its result as an Arrow table."""
    return connection.execute(query, parameters).to_arrow_table()


def read_parquet(
    connection: duckdb.DuckDBPyConnection, path: str | Path
) -> duckdb.DuckDBPyRelation:
    """Create a lazy DuckDB relation over a Parquet file or partition directory."""
    path_text = str(path)
    parquet_path = Path(path_text)
    source = (
        str(parquet_path / "**" / "*.parquet")
        if "://" not in path_text and parquet_path.is_dir()
        else path_text
    )
    return connection.read_parquet(source, hive_partitioning=True)


def write_parquet(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    path: str | Path,
    *,
    partition_by: str | Sequence[str] | None = None,
) -> None:
    """Write a SQL result to Parquet, optionally partitioned by columns."""
    relation = connection.sql(query)
    partitions = (
        [partition_by]
        if isinstance(partition_by, str)
        else list(partition_by) if partition_by is not None else None
    )
    relation.write_parquet(str(path), partition_by=partitions)
