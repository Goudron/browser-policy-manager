from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import NoReturn

import httpx
import pytest

from app.services.amo_search import (
    AMO_CACHE_MAX_ENTRIES_PER_SESSION,
    AMO_FIXED_HEADERS,
    AMO_MAX_RESPONSE_BYTES,
    AMO_SEARCH_ENDPOINT,
    AmoHttpResponse,
    AmoSearchAdapter,
    AmoSearchRateLimiter,
    AmoTransportError,
    HttpxAmoSearchTransport,
    is_verified_extension_guid,
)


@dataclass
class _Clock:
    value: float = 0.0

    def __call__(self) -> float:
        return self.value


@dataclass
class _Transport:
    response: AmoHttpResponse | None = None
    error: Exception | None = None
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def get(self, *, url: str, headers: Mapping[str, str]) -> AmoHttpResponse:
        self.calls.append((url, dict(headers)))
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("test transport needs a response")
        return self.response


def _upstream_result(
    *,
    guid: str = "uBlock0@raymondhill.net",
    name: object | None = None,
    version: object | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "guid": guid,
        "name": name if name is not None else {"en-US": "uBlock Origin"},
        "current_version": version if version is not None else {"version": "1.2.3"},
    }
    if extra is not None:
        item.update(extra)
    return item


def _response(
    payload: object, *, status: int = 200, headers: dict[str, str] | None = None
) -> AmoHttpResponse:
    response_headers = {"content-type": "application/json"}
    if headers is not None:
        response_headers.update(headers)
    return AmoHttpResponse(
        status_code=status,
        content_type=response_headers.get("content-type"),
        content_encoding=response_headers.get("content-encoding"),
        body=json.dumps(payload).encode("utf-8"),
    )


def _adapter(
    transport: _Transport,
    *,
    clock: _Clock | None = None,
    limiter: AmoSearchRateLimiter | None = None,
) -> AmoSearchAdapter:
    active_clock = clock or _Clock()
    return AmoSearchAdapter(
        transport=transport,
        rate_limiter=limiter or AmoSearchRateLimiter(clock=active_clock),
        clock=active_clock,
    )


@pytest.mark.unit
def test_search_forwards_only_normalized_query_exact_locale_and_fixed_request_shape() -> None:
    transport = _Transport(
        _response(
            {
                "results": [
                    _upstream_result(
                        extra={
                            "url": "https://attacker.invalid/extension",
                            "icons": {"64": "https://attacker.invalid/icon.svg"},
                            "description": "<img src=x onerror=alert(1)>",
                            "current_version": {  # type: ignore[dict-item]
                                "version": "1.2.3",
                                "file": {"url": "https://attacker.invalid/file.xpi"},
                            },
                        }
                    )
                ],
                "next": "https://attacker.invalid/next",
            }
        )
    )

    result = _adapter(transport).search(
        query="  uBlock Origin  ", locale="en", session_secret="opaque-session-secret"
    )

    assert result.availability == "available"
    assert result.reason_code == "available"
    assert result.cache_hit is False
    assert result.results[0].guid == "uBlock0@raymondhill.net"
    assert result.results[0].name == "uBlock Origin"
    assert result.results[0].version == "1.2.3"
    assert not hasattr(result.results[0], "url")
    assert transport.calls == [
        (
            "https://addons.mozilla.org/api/v5/addons/search/"
            "?app=firefox&type=extension&page=1&page_size=10&sort=relevance"
            "&q=uBlock+Origin&lang=en-US",
            AMO_FIXED_HEADERS,
        )
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("locale", "amo_locale"),
    (
        ("en", "en-US"),
        ("ru", "ru"),
        ("de", "de"),
        ("es-ES", "es-ES"),
        ("fr", "fr"),
        ("zh-CN", "zh-CN"),
    ),
)
def test_each_authored_locale_maps_to_its_fixed_amo_locale(locale: str, amo_locale: str) -> None:
    transport = _Transport(_response({"results": []}))

    result = _adapter(transport).search(query="extension", locale=locale, session_secret="session")

    assert result.availability == "available"
    assert transport.calls[0][0].endswith(f"&q=extension&lang={amo_locale}")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("", "query-invalid"),
        (" \t ", "query-invalid"),
        ("a" * 101, "query-invalid"),
        ("valid\x00term", "query-invalid"),
        ("valid\x85term", "query-invalid"),
        (object(), "query-invalid"),
    ],
)
def test_invalid_query_never_reaches_amo(query: object, reason: str) -> None:
    transport = _Transport(_response({"results": []}))

    result = _adapter(transport).search(query=query, locale="en", session_secret="session")

    assert result.availability == "unavailable"
    assert result.reason_code == reason
    assert not transport.calls


@pytest.mark.unit
@pytest.mark.parametrize("locale", ("en-US", "pt-BR", "EN", None, object()))
def test_unsupported_locale_never_reaches_amo(locale: object) -> None:
    transport = _Transport(_response({"results": []}))

    result = _adapter(transport).search(query="extension", locale=locale, session_secret="session")

    assert result.availability == "unavailable"
    assert result.reason_code == "locale-unsupported"
    assert not transport.calls


@pytest.mark.unit
def test_cache_is_session_private_hashed_and_expires_without_stale_result() -> None:
    clock = _Clock()
    transport = _Transport(_response({"results": [_upstream_result()]}))
    adapter = _adapter(transport, clock=clock)

    first = adapter.search(query="uBlock", locale="en", session_secret="first-session")
    cached = adapter.search(query="uBlock", locale="en", session_secret="first-session")
    other_session = adapter.search(query="uBlock", locale="en", session_secret="second-session")
    clock.value = 301
    expired = adapter.search(query="uBlock", locale="en", session_secret="first-session")

    assert first.cache_hit is False
    assert cached.cache_hit is True
    assert other_session.cache_hit is False
    assert expired.cache_hit is False
    assert len(transport.calls) == 3
    # Results may contain provider text, but cache keys must never retain a
    # query or session secret in process-memory key material.
    assert "first-session" not in repr(tuple(adapter._cache))  # noqa: SLF001
    assert "uBlock" not in repr(tuple(adapter._cache))  # noqa: SLF001
    assert all("uBlock" not in repr(tuple(entries)) for entries in adapter._cache.values())  # noqa: SLF001


@pytest.mark.unit
def test_cache_has_ten_entry_bound_per_session() -> None:
    clock = _Clock()
    transport = _Transport(_response({"results": []}))
    limiter = AmoSearchRateLimiter(
        max_requests_per_session=AMO_CACHE_MAX_ENTRIES_PER_SESSION + 1,
        max_requests_global=AMO_CACHE_MAX_ENTRIES_PER_SESSION + 1,
        clock=clock,
    )
    adapter = _adapter(transport, clock=clock, limiter=limiter)

    for index in range(AMO_CACHE_MAX_ENTRIES_PER_SESSION + 1):
        result = adapter.search(query=f"extension {index}", locale="en", session_secret="session")
        assert result.availability == "available"

    session_entries = next(iter(adapter._cache.values()))  # noqa: SLF001 - bound proof.
    assert len(session_entries) == AMO_CACHE_MAX_ENTRIES_PER_SESSION
    assert len(transport.calls) == AMO_CACHE_MAX_ENTRIES_PER_SESSION + 1


@pytest.mark.unit
def test_rate_limits_reject_without_transport_and_are_scoped_to_hashed_session() -> None:
    clock = _Clock()
    transport = _Transport(_response({"results": []}))
    limiter = AmoSearchRateLimiter(
        max_requests_per_session=2,
        max_requests_global=3,
        clock=clock,
    )
    adapter = _adapter(transport, clock=clock, limiter=limiter)

    assert (
        adapter.search(query="one", locale="en", session_secret="first").availability == "available"
    )
    assert (
        adapter.search(query="two", locale="en", session_secret="first").availability == "available"
    )
    limited_session = adapter.search(query="three", locale="en", session_secret="first")
    assert (
        adapter.search(query="one", locale="en", session_secret="second").availability
        == "available"
    )
    limited_global = adapter.search(query="two", locale="en", session_secret="second")

    assert limited_session.reason_code == "rate-limited"
    assert limited_global.reason_code == "rate-limited"
    assert len(transport.calls) == 3
    clock.value = 61
    assert (
        adapter.search(query="three", locale="en", session_secret="first").availability
        == "available"
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (_response({"results": []}, status=503), "http-status"),
        (_response({"results": []}, status=302), "redirect"),
        (_response({"results": []}, headers={"content-type": "text/html"}), "content-type"),
        (_response({"results": []}, headers={"content-encoding": "gzip"}), "content-encoding"),
        (
            AmoHttpResponse(200, "application/json", None, b"x" * (AMO_MAX_RESPONSE_BYTES + 1)),
            "response-too-large",
        ),
        (AmoHttpResponse(200, "application/json", None, b"not-json"), "response-malformed"),
        (_response({"unexpected": []}), "response-schema-drift"),
    ],
)
def test_bad_upstream_envelopes_always_fail_closed(response: AmoHttpResponse, reason: str) -> None:
    result = _adapter(_Transport(response)).search(
        query="extension", locale="en", session_secret="session"
    )

    assert result.availability == "unavailable"
    assert result.reason_code == reason
    assert result.results == ()


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {"results": [{}]},
        {"results": [_upstream_result(guid="*")]},
        {"results": [_upstream_result(name={"en-US": None})]},
        {"results": [_upstream_result(version={"version": ""})]},
        {"results": [_upstream_result(), _upstream_result()]},
        {"results": [_upstream_result()] * 11},
    ],
)
def test_schema_drift_or_unverified_guid_discards_the_complete_response(payload: object) -> None:
    result = _adapter(_Transport(_response(payload))).search(
        query="extension", locale="en", session_secret="session"
    )

    assert result.availability == "unavailable"
    assert result.reason_code == "response-schema-drift"
    assert result.results == ()


@pytest.mark.unit
def test_requested_null_name_uses_only_bounded_default_fallback() -> None:
    payload = {
        "results": [
            _upstream_result(name={"en-US": None, "_default": "Fallback extension"}),
        ]
    }

    result = _adapter(_Transport(_response(payload))).search(
        query="extension", locale="en", session_secret="session"
    )

    assert result.availability == "available"
    assert result.results[0].name == "Fallback extension"


@pytest.mark.unit
@pytest.mark.parametrize(
    "guid",
    (
        "uBlock0@raymondhill.net",
        "jid1-MnnxcxisBPnSXQ@jetpack",
        "{d10d0bf8-f5b5-c8b4-87d1-0a20d5e5c1b2}",
    ),
)
def test_verifies_supported_firefox_extension_guid_forms(guid: str) -> None:
    assert is_verified_extension_guid(guid)


@pytest.mark.unit
@pytest.mark.parametrize(
    "guid",
    ("*", "not-an-extension", "bad @example.com", "https://addons.mozilla.org/x", "bad\x00@id"),
)
def test_rejects_non_guid_or_url_provider_values(guid: str) -> None:
    assert not is_verified_extension_guid(guid)


@pytest.mark.unit
def test_cancellation_and_transport_failures_are_stable_unavailable_without_retry() -> None:
    cancelled_transport = _Transport(_response({"results": []}))
    cancelled = _adapter(cancelled_transport).search(
        query="extension",
        locale="en",
        session_secret="session",
        cancellation_check=lambda: True,
    )
    timeout = _adapter(_Transport(error=AmoTransportError("timeout"))).search(
        query="extension", locale="en", session_secret="session"
    )
    tls = _adapter(_Transport(error=AmoTransportError("tls"))).search(
        query="extension", locale="en", session_secret="session"
    )
    network = _adapter(_Transport(error=AmoTransportError("network"))).search(
        query="extension", locale="en", session_secret="session"
    )
    unexpected = _adapter(_Transport(error=RuntimeError("internal"))).search(
        query="extension", locale="en", session_secret="session"
    )

    assert cancelled.reason_code == "cancelled"
    assert not cancelled_transport.calls
    assert timeout.reason_code == "timeout"
    assert tls.reason_code == "tls"
    assert network.reason_code == "network"
    assert unexpected.reason_code == "unexpected"


@pytest.mark.unit
def test_httpx_transport_has_no_arbitrary_proxy_path_or_headers() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200, headers={"content-type": "application/json"}, json={"results": []}
        )

    transport = HttpxAmoSearchTransport(
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )
    response = transport.get(
        url=f"{AMO_SEARCH_ENDPOINT}?app=firefox&type=extension&page=1&page_size=10&sort=relevance&q=x&lang=en-US",
        headers=AMO_FIXED_HEADERS,
    )
    with pytest.raises(AmoTransportError) as rejected_url:
        transport.get(url="https://example.invalid/anything", headers=AMO_FIXED_HEADERS)
    with pytest.raises(AmoTransportError) as rejected_headers:
        transport.get(
            url=f"{AMO_SEARCH_ENDPOINT}?app=firefox&type=extension&page=1&page_size=10&sort=relevance&q=x&lang=en-US",
            headers=AMO_FIXED_HEADERS | {"Authorization": "secret"},
        )

    assert response.status_code == 200
    assert rejected_url.value.reason_code == "network"
    assert rejected_headers.value.reason_code == "network"
    assert len(calls) == 1
    assert calls[0].url.host == "addons.mozilla.org"
    assert dict(calls[0].headers)["accept"] == "application/json"
    assert dict(calls[0].headers)["accept-encoding"] == "identity"
    assert "authorization" not in dict(calls[0].headers)


@pytest.mark.unit
def test_httpx_transport_rejects_redirect_and_size_before_projection() -> None:
    redirect_transport = HttpxAmoSearchTransport(
        client_factory=lambda: httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(302, headers={"location": "https://example.invalid"})
            )
        )
    )
    oversize_transport = HttpxAmoSearchTransport(
        client_factory=lambda: httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    headers={"content-type": "application/json"},
                    content=b"x" * (AMO_MAX_RESPONSE_BYTES + 1),
                )
            )
        )
    )
    url = (
        f"{AMO_SEARCH_ENDPOINT}?app=firefox&type=extension&page=1&page_size=10&sort=relevance"
        "&q=x&lang=en-US"
    )

    with pytest.raises(AmoTransportError) as redirect:
        redirect_transport.get(url=url, headers=AMO_FIXED_HEADERS)
    with pytest.raises(AmoTransportError) as oversize:
        oversize_transport.get(url=url, headers=AMO_FIXED_HEADERS)

    assert redirect.value.reason_code == "redirect"
    assert oversize.value.reason_code == "response-too-large"


@pytest.mark.unit
def test_httpx_transport_default_client_disables_redirects_and_environment_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _Client:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def stream(self, *args: object, **kwargs: object) -> NoReturn:
            raise AssertionError("transport must not start for a rejected URL")

        def close(self) -> None:
            return None

    monkeypatch.setattr("app.services.amo_search.httpx.Client", _Client)

    with pytest.raises(AmoTransportError):
        HttpxAmoSearchTransport().get(url="https://example.invalid", headers=AMO_FIXED_HEADERS)
    # A valid URL reaches construction, and the fake stream only confirms the
    # no-proxy configuration before any response can be interpreted.
    with pytest.raises(AssertionError):
        HttpxAmoSearchTransport().get(
            url=(
                f"{AMO_SEARCH_ENDPOINT}?app=firefox&type=extension&page=1&page_size=10"
                "&sort=relevance&q=x&lang=en-US"
            ),
            headers=AMO_FIXED_HEADERS,
        )

    assert captured["follow_redirects"] is False
    assert captured["trust_env"] is False
    assert captured["verify"] is True
