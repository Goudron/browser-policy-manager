from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterable, Mapping
from typing import Any

import httpx
from fastapi import FastAPI


class TestClient:
    """Sync-friendly test client backed by httpx ASGITransport."""

    __test__ = False

    def __init__(self, app: FastAPI, base_url: str = "http://testserver", **kwargs: Any):
        self.app = app
        self.base_url = base_url
        self._client_kwargs = kwargs
        self._runner = asyncio.Runner()
        self._closed = False

    async def _request_async(self, method: str, url: str, **kwargs: Any):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url=self.base_url,
            **self._client_kwargs,
        ) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any):
        return self._runner.run(self._request_async(method, url, **kwargs))

    def get(self, url: str, **kwargs: Any):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any):
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs: Any):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any):
        return self.request("DELETE", url, **kwargs)

    def put(self, url: str, **kwargs: Any):
        return self.request("PUT", url, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return None

    def close(self):
        if self._closed:
            return
        self._runner.close()
        self._closed = True

    def __del__(self):
        try:
            if self._closed:
                return
            loop = getattr(self._runner, "_loop", None)
            if loop is not None and not loop.is_closed():
                loop.close()
            self._closed = True
        except Exception:
            pass


def build_profile_payload(
    *,
    name_prefix: str = "Profile",
    description: str = "Test profile",
    schema_version: str = "esr-140",
    flags: dict[str, Any] | None = None,
    owner: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name or f"{name_prefix}-{uuid.uuid4().hex[:6]}",
        "description": description,
        "schema_version": schema_version,
        "flags": flags or {"DisableTelemetry": True},
    }
    if owner is not None:
        payload["owner"] = owner
    return payload


def make_test_client(app: FastAPI | None = None, **kwargs: Any) -> TestClient:
    """
    Build a sync-friendly ASGI test client.

    When no application is supplied, create a fresh app instance so tests do
    not share router-level state through a module-global client.
    """

    if app is None:
        from app.main import create_app

        app = create_app()

    return TestClient(app, **kwargs)


def assert_contains_all(text: str, snippets: Iterable[str]) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"Missing expected snippets: {missing[:10]}"


def assert_has_keys(mapping: Mapping[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in mapping]
    assert not missing, f"Missing expected keys: {missing[:10]}"
