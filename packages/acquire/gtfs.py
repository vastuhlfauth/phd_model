"""Offline GTFS inventory checks for sections 5.1 and 5.6."""

import logging
import shutil
import zlib
from datetime import date
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import duckdb
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)
REQUIRED_FILES = (
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
)
WEEKDAYS = (
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
)


class GtfsCheck(BaseModel):
    """Local feed facts; coordinates are WGS84 degrees, dates are service dates."""

    model_config = ConfigDict(extra="forbid")
    valid_zip: bool = False
    is_gtfs: bool = False
    missing_files: list[str] = Field(default_factory=list)
    present_files: list[str] = Field(default_factory=list)
    has_locations_geojson: bool = False
    has_booking_rules: bool = False
    first_service_date: date | None = None
    last_service_date: date | None = None
    expired: bool | None = None
    stop_count: int | None = None
    trip_count: int | None = None
    agency_names: list[str] = Field(default_factory=list)
    bbox: tuple[float, float, float, float] | None = None
    checked_date: date
    error: str | None = None


def _load_table(connection: duckdb.DuckDBPyConnection, name: str, path: Path) -> None:
    """Read extracted CSVs lazily with DuckDB, retaining ids as strings."""
    connection.read_csv(
        str(path), header=True, all_varchar=True, delimiter=","
    ).create_view(name)


def _service_dates(
    connection: duckdb.DuckDBPyConnection, present: set[str]
) -> tuple[date | None, date | None]:
    """Compute effective service bounds, including additions/removals (5.6)."""
    connection.execute(
        "CREATE TEMP VIEW services AS SELECT DISTINCT service_id FROM trips"
    )
    if "calendar_dates.txt" in present:
        connection.execute("""
            CREATE TEMP VIEW exceptions AS
            SELECT service_id, CAST(strptime(date, '%Y%m%d') AS DATE) AS day,
                   CAST(exception_type AS INTEGER) AS exception_type
            FROM calendar_dates JOIN services USING (service_id)
        """)
    else:
        connection.execute("""
            CREATE TEMP VIEW exceptions AS
            SELECT NULL::VARCHAR AS service_id, NULL::DATE AS day,
                   NULL::INTEGER AS exception_type WHERE false
        """)
    if "calendar.txt" in present:
        weekday_cases = " ".join(
            f"WHEN {index} THEN c.{name}" for index, name in enumerate(WEEKDAYS)
        )
        connection.execute(f"""
            CREATE TEMP VIEW regular AS
            SELECT c.service_id, CAST(d.day AS DATE) AS day
            FROM calendar c JOIN services USING (service_id),
                 LATERAL generate_series(
                     strptime(c.start_date, '%Y%m%d'),
                     strptime(c.end_date, '%Y%m%d'),
                     INTERVAL 1 DAY
                 ) d(day)
            WHERE CASE dayofweek(d.day) {weekday_cases} END = '1'
              AND NOT EXISTS (
                  SELECT 1 FROM exceptions e
                  WHERE e.service_id = c.service_id
                    AND e.day = CAST(d.day AS DATE) AND e.exception_type = 2
              )
        """)
    else:
        connection.execute(
            "CREATE TEMP VIEW regular AS SELECT NULL::DATE AS day WHERE false"
        )
    return connection.execute("""
        SELECT min(day), max(day) FROM (
            SELECT day FROM regular
            UNION ALL SELECT day FROM exceptions WHERE exception_type = 1
        )
    """).fetchone()


def _inspect_tables(
    archive: ZipFile, members: dict[str, str], check: GtfsCheck
) -> None:
    """Extract only small metadata tables to scratch space, never under raw."""
    with TemporaryDirectory(prefix="gtfs-check-") as directory:
        scratch = Path(directory)
        with duckdb.connect() as connection:
            for name in (
                "agency.txt",
                "stops.txt",
                "trips.txt",
                "calendar.txt",
                "calendar_dates.txt",
            ):
                if name not in members:
                    continue
                path = scratch / name
                with archive.open(members[name]) as source, path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                _load_table(connection, name.removesuffix(".txt"), path)
            check.stop_count = connection.execute(
                "SELECT count(*) FROM stops"
            ).fetchone()[0]
            check.trip_count = connection.execute(
                "SELECT count(*) FROM trips"
            ).fetchone()[0]
            check.agency_names = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT agency_name FROM agency "
                    "WHERE agency_name IS NOT NULL ORDER BY agency_name"
                ).fetchall()
            ]
            bbox = connection.execute("""
                SELECT min(CAST(stop_lon AS DOUBLE)), min(CAST(stop_lat AS DOUBLE)),
                       max(CAST(stop_lon AS DOUBLE)), max(CAST(stop_lat AS DOUBLE))
                FROM stops
            """).fetchone()
            if all(value is not None for value in bbox):
                if not (
                    -180 <= bbox[0] <= bbox[2] <= 180
                    and -90 <= bbox[1] <= bbox[3] <= 90
                ):
                    raise ValueError("stop coordinates outside WGS84 bounds")
                check.bbox = bbox
            first, last = _service_dates(connection, set(members))
            check.first_service_date = first
            check.last_service_date = last
            check.expired = last < check.checked_date if last else None
            if last is None:
                raise ValueError("feed has no active service dates for its trips")


def inspect_gtfs(path: Path, as_of: date) -> GtfsCheck:
    """Inspect ZIP CRCs, tables, effective service and WGS84 extent, offline."""
    check = GtfsCheck(checked_date=as_of)
    if not path.is_file():
        check.error = "not downloaded"
        return check
    try:
        with ZipFile(path) as archive:
            corrupt = archive.testzip()
            if corrupt:
                raise BadZipFile(f"CRC failure in {corrupt}")
            check.valid_zip = True
            members: dict[str, str] = {}
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = PurePosixPath(info.filename).name
                if name in members:
                    raise ValueError(f"duplicate GTFS filename: {name}")
                members[name] = info.filename
            check.present_files = sorted(members)
            check.has_locations_geojson = "locations.geojson" in members
            check.has_booking_rules = "booking_rules.txt" in members
            check.missing_files = [
                name for name in REQUIRED_FILES if name not in members
            ]
            if not {"calendar.txt", "calendar_dates.txt"} & members.keys():
                check.missing_files.append("calendar.txt or calendar_dates.txt")
            if check.missing_files:
                check.error = "missing required GTFS files"
            else:
                _inspect_tables(archive, members, check)
                check.is_gtfs = True
    except (
        BadZipFile,
        OSError,
        ValueError,
        UnicodeError,
        RuntimeError,
        NotImplementedError,
        EOFError,
        zlib.error,
        duckdb.Error,
    ) as error:
        check.error = str(error)
    if check.error:
        logger.warning("GTFS check %s: %s", path, check.error)
    return check
