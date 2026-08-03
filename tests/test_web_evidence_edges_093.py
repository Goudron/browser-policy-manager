from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
import pytest

from app.documentation import web_evidence
from app.documentation.conversation import ConversationRequest, ScopeDecision
from app.documentation.web_evidence import (
    BRAVE_LLM_CONTEXT_ENDPOINT,
    MAX_EXTERNAL_SNIPPETS_PER_URL,
    MAX_PROVIDER_RESPONSE_BYTES,
    BraveContextTransport,
    HttpxBraveContextTransport,
    ProviderHttpResponse,
    ScopedWebEvidenceRetriever,
    WebEvidenceRateLimiter,
    WebEvidenceTransportError,
)
from app.documentation.web_evidence_consent import (
    WebEvidenceAuthorization,
    WebEvidenceConfiguration,
    WebEvidenceConsentStore,
)


@dataclass
class _Transport(BraveContextTransport):
    response: ProviderHttpResponse
    calls: list[dict[str, object]] = field(default_factory=list)

    def post(
        self, *, url: str, headers: Mapping[str, str], payload: Mapping[str, object]
    ) -> ProviderHttpResponse:
        self.calls.append({"url": url, "headers": dict(headers), "payload": dict(payload)})
        return self.response


class _FalseConsumeStore:
    def is_consumable(self, **_: object) -> bool:
        return True

    def consume(self, **_: object) -> bool:
        return False


def _provider_payload() -> dict[str, object]:
    url = "https://mozilla.github.io/policy-templates/README.md"
    return {
        "grounding": {
            "generic": [
                {
                    "url": url,
                    "title": "Mozilla policy templates",
                    "snippets": ["Firefox Enterprise Policies define managed settings."],
                }
            ]
        },
        "sources": {
            url: {
                "title": "Mozilla policy templates",
                "hostname": "mozilla.github.io",
                "age": ["2026-07-29"],
            }
        },
    }


def _response(payload: object) -> ProviderHttpResponse:
    return ProviderHttpResponse(200, "application/json", "identity", json.dumps(payload).encode())


def _authorized() -> tuple[
    WebEvidenceConfiguration,
    WebEvidenceConsentStore,
    ConversationRequest,
    WebEvidenceAuthorization,
]:
    configuration = WebEvidenceConfiguration(True, "server-only-token")
    store = WebEvidenceConsentStore(configuration=configuration)
    request = ConversationRequest(
        "en",
        "How do I configure Firefox policies in BPM?",
        web_mode="request_web",
        session_id="browser-session",
    )
    disclosed = store.disclose(
        session_id="browser-session", locale="en", question=request.question
    )
    assert disclosed.disclosure is not None
    approved = store.approve(
        session_id="browser-session", consent_id=disclosed.disclosure.consent_id
    )
    assert approved.authorization is not None
    return configuration, store, request, approved.authorization


def _retriever(
    *,
    configuration: WebEvidenceConfiguration,
    store: object,
    transport: BraveContextTransport,
    scope_gate: object = None,
    limiter: WebEvidenceRateLimiter | None = None,
) -> ScopedWebEvidenceRetriever:
    return ScopedWebEvidenceRetriever(
        configuration=configuration,
        consent_store=store,  # type: ignore[arg-type]
        scope_gate=scope_gate or (lambda _: ScopeDecision("allow", "scope_allowed")),  # type: ignore[arg-type]
        rate_limiter=limiter or WebEvidenceRateLimiter(),
        transport=transport,
        retrieved_at=lambda: datetime(2026, 7, 30, tzinfo=UTC),
    )


def test_rate_limiter_bounds_sessions_expiry_and_process_clear() -> None:
    with pytest.raises(ValueError, match="rate-limit"):
        WebEvidenceRateLimiter(window_seconds=0)

    now = [0.0]
    limiter = WebEvidenceRateLimiter(
        window_seconds=5,
        max_requests_per_session=2,
        max_requests_global=3,
        max_tracked_sessions=1,
        clock=lambda: now[0],
    )
    assert limiter.reserve("first") is True
    assert limiter.reserve("second") is False
    assert limiter.clear_session("first") == 1
    assert limiter.clear_session("first") == 0
    assert limiter.reserve("first") is True
    now[0] = 5
    assert limiter.clear_expired() == 2
    assert limiter.reserve("first") is True
    assert limiter.clear_all() == 1
    assert limiter.clear_all() == 0


def test_http_transport_and_bounded_body_reject_redirect_type_and_transport_errors() -> None:
    with pytest.raises(ValueError, match="timeout"):
        HttpxBraveContextTransport(timeout_seconds=0)

    class _Response:
        def __init__(self, status_code: int, headers: dict[str, str]) -> None:
            self.status_code = status_code
            self.headers = headers

        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def iter_bytes(self, *, chunk_size: int) -> list[bytes]:
            assert chunk_size
            return [b"{}"]

    class _Client:
        def __init__(self, response: _Response | None = None, failure: Exception | None = None) -> None:
            self.response = response
            self.failure = failure
            self.closed = False

        def stream(self, *args: object, **kwargs: object) -> _Response:
            del args, kwargs
            if self.failure is not None:
                raise self.failure
            assert self.response is not None
            return self.response

        def close(self) -> None:
            self.closed = True

    redirect_client = _Client(_Response(302, {"content-type": "application/json"}))
    wrong_type_client = _Client(_Response(200, {"content-type": "text/plain"}))
    failing_client = _Client(failure=httpx.ReadError("offline"))
    for client in (redirect_client, wrong_type_client, failing_client):
        with pytest.raises(WebEvidenceTransportError):
            HttpxBraveContextTransport(client_factory=lambda client=client: client).post(
                url=BRAVE_LLM_CONTEXT_ENDPOINT, headers={}, payload={}
            )
        assert client.closed is True

    response = httpx.Response(200, content=b"x" * (MAX_PROVIDER_RESPONSE_BYTES + 1))
    with pytest.raises(WebEvidenceTransportError, match="too large"):
        web_evidence._bounded_response_body(response)


def test_retriever_short_circuits_all_pre_network_boundaries_and_faulty_cancellation() -> None:
    configuration, store, request, authorization = _authorized()
    transport = _Transport(_response(_provider_payload()))
    retriever = _retriever(configuration=configuration, store=store, transport=transport)

    assert retriever.retrieve(
        ConversationRequest("en", "BPM", web_mode="local_only", session_id="browser-session"),
        authorization=None,
    ).reason_code == "assistant_web_not_requested"
    assert _retriever(
        configuration=configuration,
        store=store,
        transport=transport,
        scope_gate=lambda _: (_ for _ in ()).throw(RuntimeError()),
    ).retrieve(request, authorization=authorization).reason_code == "assistant_web_scope_unavailable"
    assert retriever.retrieve(
        ConversationRequest("en", "BPM", web_mode="request_web"), authorization=None
    ).reason_code == "assistant_web_mode_unavailable"
    assert _retriever(
        configuration=WebEvidenceConfiguration(), store=store, transport=transport
    ).retrieve(request, authorization=authorization).reason_code == "assistant_web_disabled"
    assert retriever.retrieve(
        ConversationRequest(
            "en", "x" * 401, web_mode="request_web", session_id="browser-session"
        ),
        authorization=None,
    ).reason_code == "assistant_web_query_too_large"
    assert retriever._cancelled(lambda: (_ for _ in ()).throw(RuntimeError())) is True
    assert transport.calls == []


def test_retriever_handles_cancellation_consumption_failure_and_empty_provider_evidence() -> None:
    configuration, store, request, authorization = _authorized()
    transport = _Transport(_response(_provider_payload()))
    second_check = [0]

    def cancel_after_scope() -> bool:
        second_check[0] += 1
        return second_check[0] == 2

    assert _retriever(configuration=configuration, store=store, transport=transport).retrieve(
        request, authorization=authorization, cancellation_check=cancel_after_scope
    ).reason_code == "assistant_cancelled"

    configuration, store, request, authorization = _authorized()
    transport = _Transport(_response(_provider_payload()))
    third_check = [0]

    def cancel_after_reservation() -> bool:
        third_check[0] += 1
        return third_check[0] == 3

    assert _retriever(configuration=configuration, store=store, transport=transport).retrieve(
        request, authorization=authorization, cancellation_check=cancel_after_reservation
    ).reason_code == "assistant_cancelled"
    assert transport.calls == []

    configuration = WebEvidenceConfiguration(True, "server-only-token")
    failed_transport = _Transport(_response(_provider_payload()))
    false_store = _FalseConsumeStore()
    assert _retriever(
        configuration=configuration, store=false_store, transport=failed_transport
    ).retrieve(
        ConversationRequest("en", "BPM", web_mode="request_web", session_id="session"),
        authorization=WebEvidenceAuthorization("consent", "en"),
    ).reason_code == "assistant_web_consent_unavailable"
    assert failed_transport.calls == []

    configuration, store, request, authorization = _authorized()
    empty = _response({"grounding": {"generic": []}, "sources": {}})
    assert _retriever(
        configuration=configuration, store=store, transport=_Transport(empty)
    ).retrieve(request, authorization=authorization).reason_code == "assistant_web_no_evidence"


def test_retriever_internal_headers_payload_and_response_schema_fail_closed() -> None:
    configuration = WebEvidenceConfiguration(True)
    retriever = _retriever(
        configuration=configuration,
        store=_FalseConsumeStore(),
        transport=_Transport(_response(_provider_payload())),
    )
    with pytest.raises(WebEvidenceTransportError, match="token"):
        retriever._headers()
    with pytest.raises(ValueError, match="unsupported"):
        retriever._payload("BPM", "unsupported")
    with pytest.raises(ValueError, match="exactly one"):
        ScopedWebEvidenceRetriever(
            configuration=configuration,
            scope_gate=lambda _: ScopeDecision("allow", "scope_allowed"),
            rate_limiter=WebEvidenceRateLimiter(),
            transport=_Transport(_response(_provider_payload())),
        )

    invalid_payloads = []
    invalid_payloads.append([])
    invalid_payloads.append({"grounding": [], "sources": {}})
    invalid_payloads.append({"grounding": {"unexpected": []}, "sources": {}})
    invalid_payloads.append({"grounding": {"generic": [], "poi": []}, "sources": {}})
    invalid_payloads.append({"grounding": {"generic": [], "map": [{}]}, "sources": {}})
    invalid_payloads.append({"grounding": {"generic": "bad"}, "sources": {}})
    invalid_payloads.append({"grounding": {"generic": ["bad"]}, "sources": {}})
    bad_sources = _provider_payload()
    bad_sources["sources"] = {}
    invalid_payloads.append(bad_sources)
    for payload in invalid_payloads:
        with pytest.raises(ValueError):
            retriever._sanitize_response(_response(payload), "en")


def test_response_item_url_text_and_metadata_guards_reject_every_unsafe_shape() -> None:
    configuration = WebEvidenceConfiguration(True, "server-only-token")
    retriever = _retriever(
        configuration=configuration,
        store=_FalseConsumeStore(),
        transport=_Transport(_response(_provider_payload())),
    )
    url = "https://mozilla.github.io/policy-templates/README.md"
    payload = _provider_payload()
    payload["grounding"] = {"generic": [{"url": url}]}
    with pytest.raises(ValueError):
        retriever._sanitize_response(_response(payload), "en")

    payload = _provider_payload()
    payload["grounding"]["generic"][0]["snippets"] = []  # type: ignore[index]
    with pytest.raises(ValueError):
        retriever._sanitize_response(_response(payload), "en")

    payload = _provider_payload()
    payload["grounding"]["generic"][0]["snippets"] = ["safe"] * (  # type: ignore[index]
        MAX_EXTERNAL_SNIPPETS_PER_URL + 1
    )
    with pytest.raises(ValueError):
        retriever._sanitize_response(_response(payload), "en")

    multi = {"grounding": {"generic": []}, "sources": {}}
    for index in range(3):
        item_url = f"https://mozilla.github.io/policy-templates/{index}.md"
        multi["grounding"]["generic"].append(  # type: ignore[index]
            {
                "url": item_url,
                "title": "Mozilla policy templates",
                "snippets": ["safe"] * 4,
            }
        )
        multi["sources"][item_url] = {  # type: ignore[index]
            "title": "Mozilla policy templates",
            "hostname": "mozilla.github.io",
            "age": ["2026-07-29"],
        }
    with pytest.raises(ValueError, match="snippet limit"):
        retriever._sanitize_response(_response(multi), "en")

    assert web_evidence._approved_source_url("https://mozilla.github.io:bad/policy-templates/x") is None
    assert web_evidence._approved_source_url("https://mozilla.github.io/policy-templates/../x") is None
    assert web_evidence._sanitize_bounded_text("x" * 513, 512) is None
    with pytest.raises(ValueError):
        web_evidence._source_age({}, url)
    with pytest.raises(ValueError):
        web_evidence._source_age({"title": "safe", "hostname": "wrong", "age": []}, url)
    assert web_evidence._source_age(
        {"title": "safe", "hostname": "mozilla.github.io", "age": None}, url
    ) == ()
    with pytest.raises(ValueError):
        web_evidence._source_age({"title": "safe", "hostname": "mozilla.github.io", "age": []}, url)
    with pytest.raises(ValueError):
        web_evidence._source_age(
            {
                "title": "safe",
                "hostname": "mozilla.github.io",
                "age": ["<script>bad</script>"],
            },
            url,
        )
