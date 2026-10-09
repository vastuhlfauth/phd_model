"""Metadata-only national source discovery: never GET a data file."""

import csv
import json
import logging
import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import httpx
import yaml
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from acquire.manifest import SourceFile

logger = logging.getLogger(__name__)
ATOM = "{http://www.w3.org/2005/Atom}"
GPF = "{https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd}"


class AcquisitionConfig(BaseModel):
    """Source discovery parameters and request limits for section 5.1."""

    model_config = ConfigDict(extra="forbid")
    transport_api: str
    bdalti_feed: str
    metadata_max_bytes: int = Field(gt=0)
    request_timeout_seconds: float = Field(gt=0)
    ign_interval_seconds: float = Field(ge=1)
    max_retries: int = Field(ge=0, le=5)
    retry_initial_seconds: float = Field(gt=0)
    osm_workers: int = Field(gt=0)
    bdalti_local_path: str
    gtfs_local_path: str
    osm_url: str
    osm_local_path: str
    osm_snapshots: dict[str, str]
    osm_regions: list[str]
    metropolitan_departments: set[str]
    step0_network_patterns: dict[str, str]


def load_acquisition_config(path: Path) -> AcquisitionConfig:
    with path.open(encoding="utf-8") as stream:
        return AcquisitionConfig.model_validate(yaml.safe_load(stream))


def metadata(client: httpx.Client, url: str, settings: AcquisitionConfig) -> bytes:
    """Bound metadata response bytes, including servers without a length."""
    for attempt in range(settings.max_retries + 1):
        if urlsplit(url).hostname == urlsplit(settings.bdalti_feed).hostname:
            time.sleep(settings.ign_interval_seconds)
        chunks: list[bytes] = []
        size = 0
        delay = 0
        with client.stream("GET", url) as response:
            if response.status_code in (429, 503) and attempt < settings.max_retries:
                retry_after = response.headers.get("Retry-After", "")
                delay = settings.retry_initial_seconds * 2**attempt
                if retry_after.isdigit():
                    delay = max(delay, int(retry_after))
                elif retry_after:
                    try:
                        until = parsedate_to_datetime(retry_after)
                        seconds = (until - datetime.now(timezone.utc)).total_seconds()
                        delay = max(delay, seconds)
                    except (TypeError, ValueError) as error:
                        logger.warning("Invalid Retry-After %r: %s", retry_after, error)
                logger.warning(
                    "Metadata HTTP %s; retrying %s in %ss",
                    response.status_code,
                    url,
                    delay,
                )
            else:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > settings.metadata_max_bytes:
                        raise ValueError(f"metadata response exceeds byte limit: {url}")
                    chunks.append(chunk)
                return b"".join(chunks)
        time.sleep(delay)
    raise RuntimeError("metadata retry loop exhausted")


def atom_entries(
    client: httpx.Client,
    url: str,
    settings: AcquisitionConfig,
) -> list[ET.Element]:
    """Follow IGN's pagecount, since this feed has no rel=next links."""
    first = ET.fromstring(metadata(client, url, settings))
    entries = list(first.findall(f"{ATOM}entry"))
    pages = int(first.get(f"{GPF}pagecount", "1"))
    for page in range(2, pages + 1):
        separator = "&" if "?" in url else "?"
        root = ET.fromstring(metadata(client, f"{url}{separator}page={page}", settings))
        if int(root.get(f"{GPF}page", str(page))) != page:
            raise ValueError(f"IGN returned the wrong page for {url}: {page}")
        entries.extend(root.findall(f"{ATOM}entry"))
    return entries


def discover_bdalti(
    client: httpx.Client, settings: AcquisitionConfig
) -> list[SourceFile]:
    """Resolve every metropolitan 25 m archive, without unpacking or fetching it."""
    records: list[SourceFile] = []
    pattern = re.compile(
        r"^BDALTIV2_.*_25M_ASC_LAMB93-[^_]+_D(\d{3}|02[AB])_(\d{4}-\d{2}-\d{2})$"
    )
    for entry in atom_entries(client, settings.bdalti_feed, settings):
        title = entry.findtext(f"{ATOM}title", "")
        match = pattern.fullmatch(title)
        if match is None or match[1] not in settings.metropolitan_departments:
            continue
        page_url = entry.findtext(f"{ATOM}id")
        if not page_url:
            raise ValueError(f"IGN entry has no metadata page: {title}")
        archives = 0
        for file_entry in atom_entries(client, page_url, settings):
            for link in file_entry.findall(f"{ATOM}link"):
                url = link.get("href", "")
                if not urlsplit(url).path.endswith(".7z"):
                    continue
                archives += 1
                filename = PurePosixPath(urlsplit(url).path).name
                size = link.get(f"{GPF}length")
                records.append(
                    SourceFile(
                        id=f"bdalti-{title}-{filename}",
                        source="bdalti",
                        provider="IGN",
                        vintage=match[2],
                        edition_date=date.fromisoformat(match[2]),
                        url=url,
                        local_path=settings.bdalti_local_path.format(filename=filename),
                        expected_size_bytes=int(size) if size else None,
                        notes=f"Departement D{match[1]}; keep the original .7z.",
                    )
                )
        if not archives:
            raise ValueError(f"IGN entry lists no .7z archive: {title}")
    if not records:
        raise ValueError("IGN discovery found no metropolitan 25 m archives")
    found = {
        match[1]
        for record in records
        if (match := re.search(r"_D(\d{3}|02[AB])_", record.id))
    }
    for department in sorted(settings.metropolitan_departments - found):
        logger.warning("BD ALTI missing metropolitan department D%s", department)
    return records


class TransportResource(BaseModel):
    id: int | str
    format: str | None = None
    url: str
    original_url: str | None = None
    is_available: bool | None = None
    community_resource_publisher: str | None = None


class TransportDataset(BaseModel):
    id: str
    slug: str
    title: str
    type: str
    resources: list[TransportResource]
    covered_area: list[dict[str, JsonValue]]
    licence: str | None = None
    community_resources: list[TransportResource] = Field(default_factory=list)


def discover_gtfs(
    client: httpx.Client,
    vintage: str,
    settings: AcquisitionConfig,
) -> list[SourceFile]:
    """Keep all producer GTFS resources, excluding community copies only."""
    datasets = TypeAdapter(list[TransportDataset]).validate_json(
        metadata(client, settings.transport_api, settings)
    )
    records = []
    excluded = 0
    for dataset in datasets:
        if dataset.type != "public-transit":
            continue
        community_ids = {str(resource.id) for resource in dataset.community_resources}
        for resource in dataset.resources:
            if (
                str(resource.id) in community_ids
                or resource.community_resource_publisher is not None
                or "community_resource_publisher" in resource.model_fields_set
            ):
                if resource.format and resource.format.strip().upper() == "GTFS":
                    excluded += 1
                continue
            if resource.format is None:
                logger.warning(
                    "Resource %s in dataset %s has no format; not classified as GTFS",
                    resource.id,
                    dataset.id,
                )
                continue
            if resource.format.strip().upper() != "GTFS":
                continue
            resource_id = str(resource.id)
            records.append(
                SourceFile(
                    id=f"gtfs-{dataset.id}-{resource_id}",
                    source="gtfs",
                    provider="transport.data.gouv.fr",
                    vintage=vintage,
                    url=resource.original_url or resource.url,
                    local_path=settings.gtfs_local_path.format(
                        vintage=vintage,
                        dataset_id=dataset.id,
                        resource_id=resource_id,
                    ),
                    dataset_id=dataset.id,
                    dataset_slug=dataset.slug,
                    dataset_title=dataset.title,
                    resource_id=resource_id,
                    covered_area=dataset.covered_area,
                    license=dataset.licence,
                    available=resource.is_available,
                    availability_note=(
                        "Unavailable according to transport.data.gouv.fr"
                        if resource.is_available is False
                        else None
                    ),
                    checked_date=date.today(),
                )
            )
    if not records:
        raise ValueError("transport discovery found no public-transit GTFS resources")
    logger.info("Excluded %s community GTFS resources", excluded)
    return records


def write_gtfs_inventory(path: Path, records: list[SourceFile]) -> None:
    fields = [
        "dataset_id",
        "dataset_slug",
        "dataset_title",
        "resource_id",
        "url",
        "covered_area",
        "local_path",
        "available",
        "availability_note",
        "checked_date",
        "dataset_gtfs_resource_count",
        "multiple_gtfs_resources",
    ]
    counts = Counter(record.dataset_id for record in records)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {field: getattr(record, field) for field in fields[:-2]}
            row["covered_area"] = json.dumps(record.covered_area, ensure_ascii=False)
            row["dataset_gtfs_resource_count"] = counts[record.dataset_id]
            row["multiple_gtfs_resources"] = counts[record.dataset_id] > 1
            writer.writerow(row)
    temporary.replace(path)
    multiple_path = path.with_name("gtfs_multiple_resources.csv")
    temporary = multiple_path.with_name(multiple_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "dataset_id",
                "dataset_slug",
                "dataset_title",
                "gtfs_resource_count",
                "resource_ids",
            ]
        )
        for dataset_id in sorted(key for key in counts if key is not None):
            if counts[dataset_id] <= 1:
                continue
            group = [record for record in records if record.dataset_id == dataset_id]
            writer.writerow(
                [
                    dataset_id,
                    group[0].dataset_slug,
                    group[0].dataset_title,
                    len(group),
                    ";".join(record.resource_id or "" for record in group),
                ]
            )
    temporary.replace(multiple_path)


def _normalized(text: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(character)
    )


def step0_coverage(
    records: list[SourceFile],
    settings: AcquisitionConfig,
) -> dict[str, list[str]]:
    """Check exact slugs/areas, avoiding STAR Roanne and TCL Limoges."""
    result: dict[str, list[str]] = {}
    for name, pattern in settings.step0_network_patterns.items():
        result[name] = [
            record.id
            for record in records
            if record.available is not False
            and re.search(
                pattern,
                _normalized(
                    f"{record.dataset_slug} {record.dataset_title} "
                    f"{json.dumps(record.covered_area, ensure_ascii=False)}"
                ),
            )
        ]
    return result


def check_url(client: httpx.Client, url: str) -> tuple[bool | None, str]:
    """HEAD only: never fall back to a GET when HEAD is unsupported."""
    try:
        response = client.head(url)
    except httpx.HTTPError as error:
        return None, f"HEAD failed: {type(error).__name__}: {error}"
    if response.status_code in (404, 410):
        return False, f"HEAD HTTP {response.status_code}"
    if not response.is_success:
        return None, f"HEAD HTTP {response.status_code}; existence unconfirmed"
    return True, f"HEAD HTTP {response.status_code}"


def discover_osm(client: httpx.Client, settings: AcquisitionConfig) -> list[SourceFile]:
    records = []
    for stamp, vintage in settings.osm_snapshots.items():
        for region in settings.osm_regions:
            filename = f"{region.rsplit('/', 1)[-1]}-{stamp}.osm.pbf"
            url = settings.osm_url.format(region=region, stamp=stamp)
            records.append(
                SourceFile(
                    id=f"osm-{region.replace('/', '-')}-{stamp}",
                    source="osm",
                    provider="Geofabrik",
                    vintage=vintage,
                    url=url,
                    local_path=settings.osm_local_path.format(
                        stamp=stamp, filename=filename
                    ),
                    md5_url=url + ".md5",
                    license="ODbL-1.0",
                )
            )

    def check(record: SourceFile) -> SourceFile:
        assert record.url is not None and record.md5_url is not None
        file_status, file_note = check_url(client, record.url)
        md5_status, md5_note = check_url(client, record.md5_url)
        return record.model_copy(
            update={
                "available": file_status,
                "md5_available": md5_status,
                "availability_note": f"file: {file_note}; md5: {md5_note}",
                "checked_date": date.today(),
            }
        )

    with ThreadPoolExecutor(max_workers=settings.osm_workers) as executor:
        return list(executor.map(check, records))


def merge_discovered(
    sources: list[SourceFile],
    records: list[SourceFile],
    name: str,
) -> list[SourceFile]:
    """Refresh a snapshot while preserving completed records for unchanged URLs."""
    previous = {record.id: record for record in sources}
    replacements = []
    for record in records:
        old = previous.get(record.id)
        if old and old.url == record.url and old.local_path == record.local_path:
            record = record.model_copy(
                update={
                    field: getattr(old, field)
                    for field in ("size_bytes", "sha256", "download_date", "verified")
                }
            )
        replacements.append(record)
    retained = [
        record
        for record in sources
        if not (
            record.source == name
            and (name != "osm" or record.id in {item.id for item in records})
        )
    ]
    return retained + replacements
