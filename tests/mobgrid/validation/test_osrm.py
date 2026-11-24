import io
import json
from urllib.error import HTTPError

import pytest
from mobgrid.validation import osrm


class Clock:
    def __init__(self):
        self.value = 1_767_225_600.0
        self.sleeps = []

    def time(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


class Response:
    status = 200

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.value).encode()


def settings(tmp_path):
    return osrm.QuerySettings(
        base_url_env="OSRM_BASE_URL",
        profile="driving",
        prefixes={"car": "routed-car", "bike": "routed-bike", "foot": "routed-foot"},
        user_agent="phd_model, ENTPE research",
        interval_s=1.1,
        policy_minimum_interval_s=1,
        retry_backoff_s=2,
        max_attempts=3,
        timeout_s=10,
        sample_path=tmp_path / "pairs.parquet",
        response_directory=tmp_path / "responses",
        log_directory=tmp_path / "logs",
    )


def pair(pair_id, mode="car"):
    return {
        "pair_id": pair_id,
        "mode": mode,
        "origin_lon": -0.5,
        "origin_lat": 44.8,
        "destination_lon": -0.4,
        "destination_lat": 44.9,
    }


def success(request, timeout):
    return Response({"code": "Ok", "routes": [{"duration": 120, "distance": 900}]})


def test_serial_queries_resume_with_dated_raw_responses(tmp_path, monkeypatch):
    clock = Clock()
    requests = []

    def request(req, timeout):
        requests.append((req.full_url, req.get_header("User-agent"), clock.time()))
        return success(req, timeout)

    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")
    monkeypatch.setattr(osrm, "urlopen", request)
    sample = [pair("one"), pair("two", "bike")]
    config = settings(tmp_path)
    assert osrm.query_pairs(sample, config, clock.time, clock.sleep) == (2, 0)
    assert requests[0][0] == (
        "https://example.invalid/routed-car/route/v1/driving/"
        "-0.5,44.8;-0.4,44.9?overview=false"
    )
    assert "/routed-bike/route/v1/driving/" in requests[1][0]
    assert requests[0][1] == "phd_model, ENTPE research"
    assert requests[1][2] - requests[0][2] == pytest.approx(1.1, abs=1e-6)
    records = list(config.response_directory.glob("*/*.json"))
    assert len(records) == 2
    saved = json.loads(records[0].read_text(encoding="utf-8"))
    assert saved["response"]["code"] == "Ok"
    assert saved["response_date"].startswith("2026-01-01")
    assert osrm.query_pairs(sample, config, clock.time, clock.sleep) == (0, 2)
    assert len(requests) == 2


def test_429_stops_immediately_and_5xx_is_bounded(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")
    calls = []

    def fail(status):
        def request(req, timeout):
            calls.append(status)
            raise HTTPError(req.full_url, status, "error", {}, io.BytesIO(b"failure"))

        return request

    monkeypatch.setattr(osrm, "urlopen", fail(429))
    with pytest.raises(osrm.QueryError, match="429"):
        osrm.query_pairs([pair("one")], settings(tmp_path), clock.time, clock.sleep)
    assert calls == [429]
    monkeypatch.setattr(osrm, "urlopen", fail(503))
    with pytest.raises(osrm.QueryError, match="503"):
        osrm.query_pairs([pair("one")], settings(tmp_path), clock.time, clock.sleep)
    assert calls == [429, 503, 503, 503]
    assert clock.sleeps[-2:] == [2, 4]


def test_invalid_response_not_cached_and_invalid_interval_rejected(
    tmp_path, monkeypatch
):
    clock = Clock()
    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")
    monkeypatch.setattr(
        osrm, "urlopen", lambda req, timeout: Response({"code": "NoRoute"})
    )
    config = settings(tmp_path)
    with pytest.raises(osrm.QueryError, match="NoRoute"):
        osrm.query_pairs([pair("one")], config, clock.time, clock.sleep)
    assert (
        json.loads(
            next(config.response_directory.glob("*/*.json")).read_text(encoding="utf-8")
        )["response"]["code"]
        == "NoRoute"
    )
    with pytest.raises(ValueError):
        osrm.QuerySettings.model_validate(
            {**settings(tmp_path).model_dump(), "interval_s": 0.5}
        )


def test_invalid_ok_response_is_not_cached_on_resume(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")
    monkeypatch.setattr(osrm, "urlopen", lambda req, timeout: Response({"code": "Ok"}))
    config = settings(tmp_path)
    with pytest.raises(osrm.QueryError, match="routes"):
        osrm.query_pairs([pair("one")], config, clock.time, clock.sleep)
    monkeypatch.setattr(osrm, "urlopen", success)
    assert osrm.query_pairs([pair("one")], config, clock.time, clock.sleep) == (1, 0)
    assert clock.sleeps[-1] == pytest.approx(1.1, abs=1e-6)


def test_non_json_error_is_not_cached_on_resume(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setenv("OSRM_BASE_URL", "https://example.invalid")

    def fail(req, timeout):
        raise HTTPError(req.full_url, 500, "error", {}, io.BytesIO(b"failure"))

    monkeypatch.setattr(osrm, "urlopen", fail)
    config = settings(tmp_path)
    with pytest.raises(osrm.QueryError):
        osrm.query_pairs([pair("one")], config, clock.time, clock.sleep)
    monkeypatch.setattr(osrm, "urlopen", success)
    assert osrm.query_pairs([pair("one")], config, clock.time, clock.sleep) == (1, 0)
