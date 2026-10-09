"""Tests for acquire.api."""

import httpx
import pytest
from acquire.api import get_data_gouv_dataset, list_transport_datasets
from acquire.manifest import SourceFile, save_manifest


def test_transport_api_uses_configured_url_and_query() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": []})

    client = httpx.Client(transport=httpx.MockTransport(respond))

    payload = list_transport_datasets(
        "https://transport.example.test/api/datasets",
        params={"q": "Gironde"},
        client=client,
    )

    assert payload == {"data": []}
    assert str(requests[0].url) == (
        "https://transport.example.test/api/datasets?q=Gironde"
    )
    client.close()


def test_api_key_is_read_from_environment(monkeypatch) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "example"})

    monkeypatch.setenv("TEST_ACQUIRE_API_KEY", "test-secret")
    client = httpx.Client(transport=httpx.MockTransport(respond))

    result = get_data_gouv_dataset(
        "https://data.example.test/api/datasets",
        "sample-id",
        api_key_env="TEST_ACQUIRE_API_KEY",
        client=client,
    )

    assert result["id"] == "example"
    assert requests[0].headers["Authorization"] == "Bearer test-secret"
    client.close()


def test_api_key_header_and_scheme_are_configurable(monkeypatch) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "example"})

    monkeypatch.setenv("TEST_ACQUIRE_API_KEY", "raw-key-value")
    client = httpx.Client(transport=httpx.MockTransport(respond))

    get_data_gouv_dataset(
        "https://data.example.test/api/datasets",
        "sample-id",
        api_key_env="TEST_ACQUIRE_API_KEY",
        api_key_header="X-Api-Key",
        api_key_scheme=None,
        client=client,
    )

    assert requests[0].headers["X-Api-Key"] == "raw-key-value"
    assert "Authorization" not in requests[0].headers
    client.close()


def test_configured_api_key_must_exist(monkeypatch) -> None:
    monkeypatch.delenv("MISSING_ACQUIRE_API_KEY", raising=False)

    with pytest.raises(
        ValueError, match="environment variable is unset: MISSING_ACQUIRE_API_KEY"
    ):
        get_data_gouv_dataset(
            "https://data.example.test/api/datasets",
            "sample-id",
            api_key_env="MISSING_ACQUIRE_API_KEY",
        )


def test_api_key_never_leaks_into_manifest_or_logs(
    monkeypatch, tmp_path, caplog
) -> None:
    secret = "do-not-leak-this-value"
    monkeypatch.setenv("TEST_ACQUIRE_API_KEY", secret)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"id": "example"})
        )
    )

    source = SourceFile(
        id="example-2026",
        source="example",
        provider="Example",
        vintage="2026",
        url="https://data.example.test/api/datasets",
        local_path="data/raw/example/file.json",
        access="api",
        api_key_env="TEST_ACQUIRE_API_KEY",
    )

    with caplog.at_level("DEBUG"):
        get_data_gouv_dataset(
            source.url,
            "sample-id",
            api_key_env=source.api_key_env,
            api_key_header=source.api_key_header,
            api_key_scheme=source.api_key_scheme,
            client=client,
        )
    client.close()

    assert secret not in caplog.text
    manifest_path = tmp_path / "sources.yaml"
    save_manifest(manifest_path, [source])
    assert secret not in manifest_path.read_text(encoding="utf-8")
