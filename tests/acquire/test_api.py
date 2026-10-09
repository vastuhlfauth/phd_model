"""Tests for acquire.api."""

import httpx
import pytest
from acquire.api import get_data_gouv_dataset, list_transport_datasets


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


def test_configured_api_key_must_exist(monkeypatch) -> None:
    monkeypatch.delenv("MISSING_ACQUIRE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="environment variable is unset"):
        get_data_gouv_dataset(
            "https://data.example.test/api/datasets",
            "sample-id",
            api_key_env="MISSING_ACQUIRE_API_KEY",
        )
