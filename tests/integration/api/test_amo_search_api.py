from __future__ import annotations

import time
from dataclasses import dataclass, field

import pytest

from app.api.profiles import _run_amo_search
from app.services.amo_search import (
    AMO_FIXED_HEADERS,
    AmoHttpResponse,
    AmoSearchAdapter,
    AmoSearchRateLimiter,
    AmoSearchResult,
)

_SEARCH_PATH = "/api/profiles/extensions/amo-search"
_SAME_ORIGIN_HEADERS = {"Sec-Fetch-Site": "same-origin"}


@dataclass
class _Transport:
    response: AmoHttpResponse
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def get(self, *, url: str, headers: dict[str, str]) -> AmoHttpResponse:
        self.calls.append((url, dict(headers)))
        return self.response


class _DisconnectedRequest:
    async def is_disconnected(self) -> bool:
        return True


@dataclass
class _SlowTransport:
    """Deterministic in-flight request double for the disconnect watcher."""

    response: AmoHttpResponse
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def get(self, *, url: str, headers: dict[str, str]) -> AmoHttpResponse:
        self.calls.append((url, dict(headers)))
        time.sleep(0.1)
        return self.response


class _DisconnectDuringLookupRequest:
    """Remain connected for dispatch, then disconnect while transport is working."""

    def __init__(self) -> None:
        self._started_at = time.monotonic()

    async def is_disconnected(self) -> bool:
        return time.monotonic() - self._started_at >= 0.04


class _UnavailableAdapter(AmoSearchAdapter):
    """Adapter-shaped route double; it cannot expose provider values."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        self.calls: list[dict[str, object]] = []

    def search(self, **kwargs: object) -> AmoSearchResult:
        self.calls.append(kwargs)
        return AmoSearchResult(
            availability="unavailable",
            reason_code=self.reason_code,  # type: ignore[arg-type] - test fixture enumerates contract codes.
        )


def _response(payload: bytes) -> AmoHttpResponse:
    return AmoHttpResponse(
        status_code=200,
        content_type="application/json; charset=utf-8",
        content_encoding="identity",
        body=payload,
    )


def _adapter(transport: _Transport) -> AmoSearchAdapter:
    return AmoSearchAdapter(
        transport=transport,
        rate_limiter=AmoSearchRateLimiter(
            max_requests_per_session=10,
            max_requests_global=20,
        ),
    )


@pytest.mark.anyio
async def test_amo_search_api_uses_only_the_fixed_adapter_projection_and_private_session_cache(
    client, test_app
):
    transport = _Transport(
        _response(
            b'{"results":[{"guid":"uBlock0@raymondhill.net",'
            b'"name":{"en-US":"uBlock Origin","_default":"ignored"},'
            b'"current_version":{"version":"1.2.3","file":{"url":"https://evil.invalid"}},'
            b'"url":"https://addons.mozilla.org/evil","description":"<img>"}]}'
        )
    )
    test_app.state.amo_search_adapter = _adapter(transport)

    first = await client.get(
        _SEARCH_PATH,
        params={"q": "  uBlock Origin  ", "locale": "en"},
        headers=_SAME_ORIGIN_HEADERS,
    )
    second = await client.get(
        _SEARCH_PATH,
        params={"q": "uBlock Origin", "locale": "en"},
        headers=_SAME_ORIGIN_HEADERS,
    )

    assert first.status_code == 200
    assert "connect-src 'self'" in first.headers["content-security-policy"]
    assert first.headers["cache-control"] == "no-store, max-age=0"
    assert first.headers["pragma"] == "no-cache"
    assert "HttpOnly" in first.headers["set-cookie"]
    assert "SameSite=strict" in first.headers["set-cookie"]
    assert f"Path={_SEARCH_PATH}" in first.headers["set-cookie"]
    assert first.json() == {
        "availability": "available",
        "reason_code": "available",
        "results": [
            {"guid": "uBlock0@raymondhill.net", "name": "uBlock Origin", "version": "1.2.3"}
        ],
        "cache_hit": False,
    }
    assert second.json()["cache_hit"] is True
    assert len(transport.calls) == 1
    assert transport.calls[0][1] == AMO_FIXED_HEADERS
    assert "url=" not in transport.calls[0][0]
    assert "profile" not in transport.calls[0][0]


@pytest.mark.anyio
async def test_amo_search_api_rejects_cross_site_and_unbounded_inputs_without_outbound_request(
    client, test_app
):
    transport = _Transport(_response(b'{"results":[]}'))
    test_app.state.amo_search_adapter = _adapter(transport)

    cross_site = await client.get(
        _SEARCH_PATH,
        params={"q": "extension", "locale": "en"},
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    duplicate = await client.get(
        f"{_SEARCH_PATH}?q=extension&q=second&locale=en",
        headers=_SAME_ORIGIN_HEADERS,
    )
    hostile = await client.get(
        _SEARCH_PATH,
        params={"q": "x" * 101, "locale": "en", "url": "https://example.invalid"},
        headers=_SAME_ORIGIN_HEADERS,
    )
    write_attempt = await client.post(
        _SEARCH_PATH,
        headers=_SAME_ORIGIN_HEADERS,
    )

    assert cross_site.status_code == 403
    assert cross_site.json()["reason_code"] == "unexpected"
    assert duplicate.status_code == 200
    assert duplicate.json() == {
        "availability": "unavailable",
        "reason_code": "query-invalid",
        "results": [],
        "cache_hit": False,
    }
    assert hostile.status_code == 200
    assert hostile.json()["reason_code"] == "query-invalid"
    assert write_attempt.status_code == 405
    assert transport.calls == []


@pytest.mark.anyio
async def test_amo_search_api_maps_adapter_failure_without_provider_or_query_detail(
    client, test_app
):
    transport = _Transport(
        AmoHttpResponse(status_code=503, content_type=None, content_encoding=None, body=b"")
    )
    test_app.state.amo_search_adapter = _adapter(transport)

    response = await client.get(
        _SEARCH_PATH,
        params={"q": "private query", "locale": "ru"},
        headers=_SAME_ORIGIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "availability": "unavailable",
        "reason_code": "http-status",
        "results": [],
        "cache_hit": False,
    }
    assert "private query" not in response.text
    assert "ru" not in response.text
    assert len(transport.calls) == 1


@pytest.mark.anyio
async def test_amo_search_api_stops_before_transport_when_client_already_disconnected():
    transport = _Transport(_response(b'{"results":[]}'))
    adapter = _adapter(transport)

    result = await _run_amo_search(
        _DisconnectedRequest(),  # type: ignore[arg-type] - focused disconnect boundary double.
        adapter=adapter,
        query="extension",
        locale="en",
        session_secret="a-browser-session-secret",
    )

    assert result.availability == "unavailable"
    assert result.reason_code == "cancelled"
    assert transport.calls == []


@pytest.mark.anyio
async def test_amo_search_api_cancels_an_in_flight_lookup_without_returning_provider_data():
    transport = _SlowTransport(_response(b'{"results":[]}'))
    adapter = AmoSearchAdapter(
        transport=transport,
        rate_limiter=AmoSearchRateLimiter(max_requests_per_session=10, max_requests_global=20),
    )

    result = await _run_amo_search(
        _DisconnectDuringLookupRequest(),  # type: ignore[arg-type] - focused disconnect boundary double.
        adapter=adapter,
        query="extension",
        locale="en",
        session_secret="a-browser-session-secret",
    )

    assert result == AmoSearchResult(
        availability="unavailable",
        reason_code="cancelled",
    )
    assert len(transport.calls) == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "reason_code",
    (
        "query-invalid",
        "locale-unsupported",
        "rate-limited",
        "cancelled",
        "timeout",
        "network",
        "tls",
        "redirect",
        "http-status",
        "content-type",
        "content-encoding",
        "response-too-large",
        "response-malformed",
        "response-schema-drift",
        "unexpected",
    ),
)
async def test_amo_search_api_projects_each_adapter_unavailable_state_without_values(
    client, test_app, reason_code: str
):
    adapter = _UnavailableAdapter(reason_code)
    test_app.state.amo_search_adapter = adapter

    response = await client.get(
        _SEARCH_PATH,
        params={"q": "private extension name", "locale": "en"},
        headers=_SAME_ORIGIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "availability": "unavailable",
        "reason_code": reason_code,
        "results": [],
        "cache_hit": False,
    }
    assert "private extension name" not in response.text
    assert len(adapter.calls) == 1
