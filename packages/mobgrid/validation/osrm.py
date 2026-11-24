"""Serial, resumable OSRM route queries for section 13 validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pyarrow.parquet as pq
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mobgrid.validation.osrm_calibration import CalibrationSettings
from mobgrid.validation.osrm_sample import SampleSettings

Mode = Literal["car", "bike", "foot"]


class QueryError(RuntimeError):
    """The OSRM query run cannot safely continue."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


urlopen = build_opener(_NoRedirect()).open


class CarProfileNotes(BaseModel):
    """Published upstream profile values, not verified deployed-server settings."""

    model_config = ConfigDict(extra="forbid")
    source_url: str = Field(min_length=1)
    unclassified_kmh: float = Field(gt=0, allow_inf_nan=False)
    residential_kmh: float = Field(gt=0, allow_inf_nan=False)
    tertiary_kmh: float = Field(gt=0, allow_inf_nan=False)
    primary_kmh: float = Field(gt=0, allow_inf_nan=False)
    maxspeed_factor: float = Field(gt=0, allow_inf_nan=False)
    turn_penalty_s: float = Field(ge=0, allow_inf_nan=False)
    signal_penalty_s: float = Field(ge=0, allow_inf_nan=False)


class QuerySettings(BaseModel):
    """HTTP policy and paths for a serial section 13 OSRM query run."""

    model_config = ConfigDict(extra="forbid")

    base_url_env: str = Field(min_length=1)
    profile: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    prefixes: dict[Mode, str]
    user_agent: str = Field(min_length=1)
    interval_s: float = Field(gt=0, allow_inf_nan=False)
    policy_minimum_interval_s: float = Field(gt=0, allow_inf_nan=False)
    retry_backoff_s: float = Field(gt=0, allow_inf_nan=False)
    max_attempts: int = Field(ge=1)
    timeout_s: float = Field(gt=0, allow_inf_nan=False)
    max_snap_distance_m: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    sample_path: Path
    response_directory: Path
    log_directory: Path
    sampling: SampleSettings | None = None
    report_path: Path | None = None
    route_checkpoint_directory: Path | None = None
    calibration_checkpoint_directory: Path | None = None
    metric_tolerances_min: tuple[float, float] | None = None
    car_profile_notes: CarProfileNotes | None = None
    calibration: CalibrationSettings | None = None

    @model_validator(mode="after")
    def check_policy(self) -> QuerySettings:
        if self.interval_s < self.policy_minimum_interval_s:
            raise ValueError("interval_s must respect the configured server policy")
        if set(self.prefixes) != {"car", "bike", "foot"}:
            raise ValueError("prefixes must include car, bike and foot")
        if self.metric_tolerances_min is not None and not (
            0 < self.metric_tolerances_min[0] < self.metric_tolerances_min[1]
            and all(math.isfinite(value) for value in self.metric_tolerances_min)
        ):
            raise ValueError(
                "metric tolerances must be finite, positive and increasing"
            )
        if any(
            not value
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in value)
            for value in self.prefixes.values()
        ):
            raise ValueError("invalid mode prefix")
        return self


def load_query_settings(path: Path) -> QuerySettings:
    """Read the configured query settings."""
    with path.open(encoding="utf-8") as stream:
        return QuerySettings.model_validate(yaml.safe_load(stream))


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Release the OS lock on process exit, including an interrupted run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            if not stream.read(1):
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise QueryError("another OSRM query run is active") from exc
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise QueryError("another OSRM query run is active") from exc
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def _base_url(settings: QuerySettings) -> str:
    value = os.environ.get(settings.base_url_env)
    if not value:
        raise QueryError(f"set the {settings.base_url_env} environment variable")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise QueryError("OSRM base URL must be an HTTP(S) URL without credentials")
    return value.rstrip("/")


def _request_url(pair: dict, settings: QuerySettings, base: str) -> str:
    try:
        mode = pair["mode"]
        coordinates = [
            float(pair[name])
            for name in (
                "origin_lon",
                "origin_lat",
                "destination_lon",
                "destination_lat",
            )
        ]
        if (
            mode not in settings.prefixes
            or not isinstance(pair["pair_id"], str)
            or not pair["pair_id"].strip()
        ):
            raise ValueError("invalid pair mode or id")
        if any(not math.isfinite(x) for x in coordinates):
            raise ValueError("coordinates must be finite")
        lon1, lat1, lon2, lat2 = coordinates
        if abs(lon1) > 180 or abs(lon2) > 180 or abs(lat1) > 90 or abs(lat2) > 90:
            raise ValueError("coordinates are outside WGS84 bounds")
    except (KeyError, TypeError, ValueError) as exc:
        raise QueryError(f"invalid sample pair: {exc}") from exc
    return (
        f"{base}/{settings.prefixes[mode]}/route/v1/{settings.profile}/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=false"
    )


def _key(pair: dict, url: str) -> str:
    identity = json.dumps([str(pair["pair_id"]), url], separators=(",", ":"))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _valid_response(payload: object) -> bool:
    if not isinstance(payload, dict) or payload.get("code") != "Ok":
        return False
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        return False
    for name in ("duration", "distance"):
        value = routes[0].get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value) or value <= 0:
            return False
    return True


def _unreachable_response(status: int | None, payload: object) -> bool:
    return (
        status in (200, 400)
        and isinstance(payload, dict)
        and payload.get("code") in ("NoRoute", "NoSegment")
    )


def _snap_distances(payload: dict) -> tuple[float, float]:
    waypoints = payload.get("waypoints")
    if not isinstance(waypoints, list) or len(waypoints) != 2:
        raise ValueError("OSRM response must contain two waypoint snapping distances")
    distances = []
    for waypoint in waypoints:
        value = waypoint.get("distance") if isinstance(waypoint, dict) else None
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                "OSRM waypoint snapping distance must be finite and nonnegative"
            )
        distances.append(float(value))
    return distances[0], distances[1]


def _successful_records(directory: Path) -> set[str]:
    completed = set()
    for path in directory.glob("*/*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            record.get("http_status") == 200 and _valid_response(record.get("response"))
        ) or _unreachable_response(record.get("http_status"), record.get("response")):
            completed.add(record["request_key"])
    return completed


def query_pairs(
    pairs: list[dict],
    settings: QuerySettings,
    now: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, int]:
    """Query sampled WGS84 pairs serially, recording each raw response and UTC date."""
    base = _base_url(settings)
    requests = [(pair, _request_url(pair, settings, base)) for pair in pairs]
    keys = [_key(pair, url) for pair, url in requests]
    ids = [str(pair["pair_id"]) for pair in pairs]
    if len(set(ids)) != len(ids):
        raise QueryError("sample contains duplicate pair IDs")
    root = settings.response_directory
    root.mkdir(parents=True, exist_ok=True)
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    start = _utc(now())
    log_path = settings.log_directory / f"{start[:10]}_osrm.log"
    summary_path = settings.log_directory / f"{start[:10]}_osrm_summary.md"
    started = time.perf_counter()
    sent = skipped = 0
    unreachable = 0
    error = ""
    try:
        with _exclusive_lock(root / ".query.lock"):
            completed = _successful_records(root)
            throttle = root / ".last_request.json"
            last_request = None
            if throttle.exists():
                last_request = float(
                    json.loads(throttle.read_text(encoding="utf-8"))["time"]
                )
            for (pair, url), key in zip(requests, keys, strict=True):
                if key in completed:
                    skipped += 1
                    continue
                for attempt in range(settings.max_attempts):
                    if last_request is not None:
                        wait = settings.interval_s - (now() - last_request)
                        if wait > 0:
                            sleep(wait)
                    last_request = now()
                    _write_json(throttle, {"time": last_request})
                    request = Request(url, headers={"User-Agent": settings.user_agent})
                    status = None
                    body = ""
                    network_error = None
                    try:
                        with urlopen(request, timeout=settings.timeout_s) as response:
                            status = response.status
                            body = response.read().decode("utf-8", errors="replace")
                    except HTTPError as exc:
                        status = exc.code
                        body = exc.read().decode("utf-8", errors="replace")
                    except (URLError, TimeoutError, OSError) as exc:
                        network_error = str(exc)
                    sent += 1
                    try:
                        payload = json.loads(body)
                    except json.JSONDecodeError:
                        payload = None
                    response_date = _utc(now())
                    record = {
                        "request_key": key,
                        "pair_id": str(pair["pair_id"]),
                        "mode": pair["mode"],
                        "url": url,
                        "request_date": _utc(last_request),
                        "response_date": response_date,
                        "http_status": status,
                        "raw_body": body,
                        "response": payload,
                        "network_error": network_error,
                    }
                    _write_json(
                        root / response_date[:10] / f"{key}_{uuid.uuid4().hex}.json",
                        record,
                    )
                    if status == 200 and _valid_response(payload):
                        completed.add(key)
                        break
                    if status == 429:
                        raise QueryError("OSRM returned HTTP 429; stopping immediately")
                    if _unreachable_response(status, payload):
                        completed.add(key)
                        unreachable += 1
                        with log_path.open("a", encoding="utf-8") as log:
                            log.write(
                                f"{response_date}: pair={pair['pair_id']}, "
                                f"mode={pair['mode']}, outcome={payload['code']}\n"
                            )
                        break
                    retry = network_error is not None or (
                        status is not None and 500 <= status < 600
                    )
                    if not retry or attempt + 1 == settings.max_attempts:
                        raise QueryError(
                            f"OSRM request failed: HTTP {status}, "
                            f"response {payload}, network error {network_error}; "
                            "expected valid routes with positive duration and distance"
                        )
                    sleep(settings.retry_backoff_s * 2**attempt)
    except (QueryError, OSError, ValueError) as exc:
        error = str(exc)
        raise
    finally:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(
                f"{start}: sent={sent}, resumed={skipped}, error={error or 'none'}\n"
            )
        summary_path.write_text(
            "# OSRM queries\n\n"
            f"- Started (UTC): {start}\n"
            f"- Sample: {settings.sample_path}\n"
            f"- Requests: {sent}; cached pairs: {skipped}\n"
            f"- New unreachable outcomes: {unreachable}\n"
            f"- Seconds: {time.perf_counter() - started:.3f}\n"
            f"- Responses: {root}\n"
            f"- Warnings/errors: {error or 'none'}\n",
            encoding="utf-8",
        )
    return sent, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sample", "queries", "report"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    settings = load_query_settings(args.config)
    if args.command == "sample":
        if settings.sampling is None:
            raise ValueError("sampling configuration is required")
        from mobgrid.validation.osrm_sample import generate_sample

        generate_sample(
            settings.sampling,
            settings.sample_path,
            settings.log_directory,
            _utc(time.time())[:10],
        )
        return
    if args.command == "report":
        from mobgrid.validation.osrm_report import generate_report

        generate_report(settings, _utc(time.time())[:10])
        return
    pairs = pq.read_table(settings.sample_path).to_pylist()
    sent, skipped = query_pairs(pairs, settings)
    print(f"OSRM requests: {sent}; cached pairs: {skipped}")


if __name__ == "__main__":
    main()
