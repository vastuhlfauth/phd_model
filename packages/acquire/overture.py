"""Anonymous Overture extraction; invoked only for an actual acquisition."""

from datetime import date
from pathlib import Path

import duckdb

from acquire.checksums import checksum_file
from acquire.download import DownloadResult, _destination
from acquire.manifest import SourceFile


def write_places(
    connection: duckdb.DuckDBPyConnection,
    url: str,
    bbox: tuple[float, float, float, float],
    output: Path,
) -> None:
    west, south, east, north = bbox
    connection.execute(
        """
        COPY (
            SELECT * FROM read_parquet($source_url)
            WHERE bbox.xmin <= $east AND bbox.xmax >= $west
              AND bbox.ymin <= $north AND bbox.ymax >= $south
        ) TO $output (FORMAT PARQUET)
        """,
        {
            "source_url": url,
            "east": east,
            "west": west,
            "north": north,
            "south": south,
            "output": str(output),
        },
    )


def extract_places(source: SourceFile, root: Path) -> DownloadResult:
    """Keep places intersecting the configured box, preserving all columns."""
    if (
        source.access != "s3"
        or source.url is None
        or source.bbox is None
        or source.s3_region is None
    ):
        raise ValueError("expected a configured S3 extraction")
    destination = _destination(root, source.local_path)
    if (
        destination.is_file()
        and source.sha256 is not None
        and checksum_file(destination) == source.sha256
    ):
        return DownloadResult(destination, source, True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    with duckdb.connect() as connection:
        connection.execute("INSTALL httpfs")
        connection.execute("LOAD httpfs")
        connection.execute(f"SET s3_region = '{source.s3_region}'")
        connection.execute(
            "CREATE SECRET overture_anonymous "
            f"(TYPE s3, KEY_ID '', SECRET '', REGION '{source.s3_region}')"
        )
        write_places(connection, source.url, source.bbox, temporary)
    temporary.replace(destination)
    record = source.model_copy(
        update={
            "size_bytes": destination.stat().st_size,
            "sha256": checksum_file(destination),
            "download_date": date.today(),
            "verified": False,
        }
    )
    return DownloadResult(destination, record, False)
