"""Round-trip tests for DuckDB and Arrow helpers."""

from unittest.mock import Mock

import pyarrow as pa
from common.duckdb_io import (
    open_connection,
    query_arrow,
    read_parquet,
    register_arrow,
    unregister_arrow,
    write_parquet,
)


def test_read_parquet_preserves_remote_url() -> None:
    connection = Mock()
    source = "s3://example-bucket/table.parquet"

    read_parquet(connection, source)

    connection.read_parquet.assert_called_once_with(
        source,
        hive_partitioning=True,
    )


def test_arrow_registration_query_and_parquet_round_trip(tmp_path) -> None:
    source = pa.table(
        {
            "scenario": ["baseline", "baseline"],
            "mode": ["walk", "walk"],
            "tile": pa.array([1, 1], type=pa.int32()),
            "cell_id": pa.array([12_000_400_000, 12_000_400_001], type=pa.int64()),
            "value": pa.array([1.25, 2.5], type=pa.float32()),
        }
    )
    destination = tmp_path / "partitioned"
    connection = open_connection()
    try:
        register_arrow(connection, "input_cells", source)
        queried = query_arrow(connection, "SELECT * FROM input_cells ORDER BY cell_id")
        assert queried.equals(source)

        write_parquet(
            connection,
            "SELECT * FROM input_cells",
            destination,
            partition_by=("scenario", "mode", "tile"),
        )
        restored = read_parquet(connection, destination).project(
            "scenario, mode, CAST(tile AS INTEGER) AS tile, cell_id, value"
        ).to_arrow_table()
        assert restored.sort_by("cell_id").equals(source)
    finally:
        unregister_arrow(connection, "input_cells")
        connection.close()
