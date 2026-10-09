"""JSON API discovery clients for section 5."""

import os
from typing import Any
from urllib.parse import quote

import httpx


def _request_json(
    url: str,
    *,
    params: dict[str, str] | None = None,
    api_key_env: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    headers: dict[str, str] = {}
    if api_key_env is not None:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(
                f"required API key environment variable is unset: {api_key_env}"
            )
        headers["Authorization"] = f"Bearer {api_key}"
    owns_client = client is None
    active_client = client or httpx.Client(follow_redirects=True)
    try:
        response = active_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            active_client.close()
    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object")
    return payload


def list_data_gouv_datasets(
    api_url: str,
    *,
    params: dict[str, str] | None = None,
    api_key_env: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch a data.gouv.fr dataset listing from a configured API URL."""
    return _request_json(
        api_url,
        params=params,
        api_key_env=api_key_env,
        client=client,
    )


def get_data_gouv_dataset(
    api_url: str,
    dataset_id: str,
    *,
    api_key_env: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch one data.gouv.fr dataset using its configured API base URL."""
    return _request_json(
        f"{api_url.rstrip('/')}/{quote(dataset_id, safe='')}",
        api_key_env=api_key_env,
        client=client,
    )


def list_transport_datasets(
    api_url: str,
    *,
    params: dict[str, str] | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch transport.data.gouv.fr datasets from the configured endpoint."""
    return _request_json(api_url, params=params, client=client)


def get_transport_dataset(
    api_url: str,
    dataset_id: str,
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch one transport.data.gouv.fr dataset from its configured API URL."""
    return _request_json(
        f"{api_url.rstrip('/')}/{quote(dataset_id, safe='')}",
        client=client,
    )
