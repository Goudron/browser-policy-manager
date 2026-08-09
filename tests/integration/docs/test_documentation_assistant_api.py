from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import documentation_assistant as assistant_api
from app.api.documentation_assistant import (
    AssistantSource,
    AssistantStatus,
    AssistantWebModeStatus,
    _event_payload,
)
from app.documentation.conversation import ConversationRequest
from app.documentation.conversation_stream import (
    ConversationAdmission,
    ConversationStreamEvent,
    ConversationStreamExternalClaim,
)
from app.documentation.training_notice import training_notice
from app.main import create_app
from tests.support import make_test_client

TAB_ID = "tab_0123456789abcdef0123456789abcdef"


@dataclass
class _AssistantService:
    requests: list[ConversationRequest] = field(default_factory=list)
    sessions: list[str] = field(default_factory=list)
    web_mode_enabled: bool = False
    clear_calls: list[tuple[str, str | None, str | None]] = field(default_factory=list)

    def status(self, *, locale: str, session_id: str) -> AssistantStatus:
        self.sessions.append(session_id)
        return AssistantStatus(
            "ready",
            True,
            True,
            locale,
            "assistant_ready",
            "assistant_chat_send",
            "assistant_ready",
            3,
        )

    def ask(self, *, request: ConversationRequest, session_id: str) -> ConversationAdmission:
        self.requests.append(request)
        self.sessions.append(session_id)
        return ConversationAdmission("req_example", "accepted", "assistant_accepted", 1)

    def web_mode_status(
        self, *, locale: str, session_id: str, tab_id: str | None = None
    ) -> AssistantWebModeStatus:
        assert tab_id == TAB_ID
        self.sessions.append(session_id)
        return AssistantWebModeStatus(
            self.web_mode_enabled,
            True,
            locale,
            (
                "assistant_web_enabled"
                if self.web_mode_enabled
                else "assistant_web_disabled_by_reader"
            ),
            int(self.web_mode_enabled),
        )

    def set_web_mode(
        self, *, locale: str, session_id: str, enabled: bool, tab_id: str | None = None
    ) -> AssistantWebModeStatus:
        self.web_mode_enabled = enabled
        return self.web_mode_status(locale=locale, session_id=session_id, tab_id=tab_id)

    def events(
        self, *, request_id: str, session_id: str
    ) -> tuple[ConversationStreamEvent, ...] | None:
        if request_id != "req_example" or session_id not in self.sessions:
            return None
        return (
            ConversationStreamEvent(
                "accepted",
                request_id,
                "accepted",
                1,
                "assistant_accepted",
                "assistant_chat_accepted",
                "assistant_chat_cancel",
            ),
            ConversationStreamEvent(
                "final",
                request_id,
                "answer",
                2,
                "assistant_citations_validated",
                "assistant_chat_answer",
                "",
                "answer",
                "Grounded BPM answer.",
                ("src_example",),
            ),
        )

    def cancel(self, *, request_id: str, session_id: str) -> bool | None:
        return request_id == "req_example" and session_id in self.sessions

    def clear(
        self, *, session_id: str, locale: str | None = None, tab_id: str | None = None
    ) -> bool:
        self.clear_calls.append((session_id, locale, tab_id))
        return session_id in self.sessions

    def source(self, *, request_id: str, source_id: str, session_id: str) -> AssistantSource | None:
        if request_id != "req_example" or session_id not in self.sessions:
            return None
        if source_id == "src_web":
            return AssistantSource(
                source_id,
                "Mozilla policy templates",
                "https://mozilla.github.io/policy-templates/README.md",
                "en",
                "",
                "external_untrusted",
                "brave-search-llm-context",
            )
        if source_id != "src_example":
            return None
        return AssistantSource(
            source_id,
            "BPM overview",
            "/help/en/user/overview.html",
            "en",
            "Approved BPM documentation excerpt.",
        )


@dataclass
class _BodyRequest:
    headers: dict[str, str]
    chunks: tuple[bytes, ...]

    async def stream(self):
        for chunk in self.chunks:
            yield chunk


class _EmptyStream:
    def __aiter__(self) -> _EmptyStream:
        return self

    async def __anext__(self) -> bytes:
        raise StopAsyncIteration


@dataclass
class _NoBodyRequest:
    headers: dict[str, str]

    def stream(self) -> _EmptyStream:
        return _EmptyStream()


def _headers(session_cookie: str | None = None) -> dict[str, str]:
    headers = {
        "Origin": "http://testserver",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/json",
    }
    if session_cookie is not None:
        headers["Cookie"] = session_cookie
    return headers


def test_release_assistant_returns_the_localized_training_notice_without_worker_startup() -> None:
    with make_test_client(create_app()) as client:
        session_cookie = ""
        for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
            status_response = client.get(f"/api/documentation-assistant/status?locale={locale}")
            assert status_response.status_code == 200
            assert status_response.json() == {
                "api_version": 1,
                "state": "ready",
                "assistant_ready": True,
                "lexical_search_ready": True,
                "locale": locale,
                "message_key": "assistant_training_notice",
                "action_key": "assistant_chat_send",
                "reason_code": "assistant_training_notice",
                "state_epoch": 1,
            }
            if not session_cookie:
                session_cookie = status_response.headers["set-cookie"].split(";", 1)[0]
            admitted = client.post(
                "/api/documentation-assistant/chat",
                headers=_headers(session_cookie),
                json={
                    "api_version": 1,
                    "locale": locale,
                    "question": "Any permitted question",
                    "tab_id": TAB_ID,
                },
            )
            assert admitted.status_code == 202
            assert admitted.json()["time_preview"] == {
                "minimum_seconds": 1,
                "maximum_seconds": 1,
            }
            stream = client.get(admitted.json()["stream_path"], headers={"Cookie": session_cookie})
            assert stream.status_code == 200
            assert training_notice(locale) in stream.text
            assert '"citations": []' in stream.text


def test_same_origin_assistant_api_exposes_only_safe_status_chat_events_and_sources() -> None:
    app = create_app()
    service = _AssistantService()
    app.state.documentation_assistant_service = service

    with make_test_client(app) as client:
        status_response = client.get("/api/documentation-assistant/status?locale=en")
        assert status_response.status_code == 200
        assert status_response.json()["assistant_ready"] is True
        session_cookie = status_response.headers["set-cookie"].split(";", 1)[0]

        missing_tab = client.get(
            "/api/documentation-assistant/web-mode?locale=en",
            headers={"Cookie": session_cookie},
        )
        assert missing_tab.status_code == 400

        web_status = client.get(
            f"/api/documentation-assistant/web-mode?locale=en&tab_id={TAB_ID}",
            headers={"Cookie": session_cookie},
        )
        assert web_status.json() == {
            "api_version": 1,
            "enabled": False,
            "available": True,
            "locale": "en",
            "reason_code": "assistant_web_disabled_by_reader",
            "state_epoch": 0,
        }
        enabled = client.post(
            "/api/documentation-assistant/web-mode",
            headers=_headers(session_cookie),
            json={"api_version": 1, "locale": "en", "enabled": True, "tab_id": TAB_ID},
        )
        assert enabled.status_code == 200
        assert enabled.json()["enabled"] is True

        cross_origin_mode = client.post(
            "/api/documentation-assistant/web-mode",
            json={"api_version": 1, "locale": "en", "enabled": False, "tab_id": TAB_ID},
        )
        assert cross_origin_mode.status_code == 403

        rejected = client.post(
            "/api/documentation-assistant/chat",
            json={"api_version": 1, "locale": "en", "question": "BPM"},
        )
        assert rejected.status_code == 403

        admitted = client.post(
            "/api/documentation-assistant/chat",
            headers=_headers(session_cookie),
            json={
                "api_version": 1,
                "locale": "en",
                "question": "How do I configure BPM?",
                "web_mode": "local_only",
                "tab_id": TAB_ID,
            },
        )
        assert admitted.status_code == 202
        assert admitted.json()["stream_path"].endswith("/req_example/stream")
        assert admitted.json()["time_preview"] == {
            "minimum_seconds": 60,
            "maximum_seconds": 900,
        }

        unsupported_version = client.post(
            "/api/documentation-assistant/chat",
            headers=_headers(session_cookie),
            json={"api_version": 2, "locale": "en", "question": "BPM"},
        )
        assert unsupported_version.status_code == 400
        assert (
            unsupported_version.json()["detail"]["reason_code"]
            == "assistant_api_version_unsupported"
        )

        stream = client.get(
            "/api/documentation-assistant/chat/req_example/stream",
            headers={"Cookie": session_cookie},
        )
        assert stream.status_code == 200
        assert "event: final" in stream.text
        assert "Grounded BPM answer." in stream.text
        assert "src_example" in stream.text
        assert "prompt" not in stream.text

        source = client.get(
            "/api/documentation-assistant/chat/req_example/sources/src_example",
            headers={"Cookie": session_cookie},
        )
        assert source.status_code == 200
        assert source.json() == {
            "api_version": 1,
            "source_id": "src_example",
            "title": "BPM overview",
            "published_url": "/help/en/user/overview.html",
            "locale": "en",
            "excerpt": "Approved BPM documentation excerpt.",
        }

        external_source = client.get(
            "/api/documentation-assistant/chat/req_example/sources/src_web",
            headers={"Cookie": session_cookie},
        )
        assert external_source.json() == {
            "api_version": 1,
            "source_id": "src_web",
            "title": "Mozilla policy templates",
            "published_url": "https://mozilla.github.io/policy-templates/README.md",
            "locale": "en",
            "excerpt": "",
            "source_kind": "external_untrusted",
            "provider_id": "brave-search-llm-context",
        }

        cancelled = client.post(
            "/api/documentation-assistant/chat/req_example/cancel",
            headers=_headers(session_cookie),
            json={"api_version": 1},
        )
        assert cancelled.status_code == 202
        assert (
            client.delete(
                f"/api/documentation-assistant/conversation?locale=en&tab_id={TAB_ID}",
                headers={"Cookie": session_cookie},
            ).status_code
            == 204
        )

    assert service.clear_calls[-1][1:] == ("en", TAB_ID)

    assert service.requests == [
        ConversationRequest(
            locale="en",
            question="How do I configure BPM?",
            web_mode="local_only",
            session_id=service.sessions[-1],
            web_tab_id=TAB_ID,
        )
    ]


def test_external_claims_are_a_separate_optional_final_event_region() -> None:
    event = ConversationStreamEvent(
        "final",
        "req_example",
        "answer",
        4,
        "assistant_merged_answer_validated",
        "assistant_chat_answer",
        "",
        "answer",
        "Local BPM answer.",
        ("src_local",),
        external_claims=(ConversationStreamExternalClaim("External Firefox note.", ("src_web",)),),
    )

    assert _event_payload(event) == {
        "api_version": 1,
        "request_id": "req_example",
        "state": "answer",
        "state_epoch": 4,
        "reason_code": "assistant_merged_answer_validated",
        "message_key": "assistant_chat_answer",
        "action_key": "",
        "disposition": "answer",
        "text": "Local BPM answer.",
        "citations": ["src_local"],
        "external_claims": [{"text": "External Firefox note.", "citations": ["src_web"]}],
    }


def test_unavailable_service_and_event_payload_keep_all_terminal_paths_safe() -> None:
    service = assistant_api.UnavailableDocumentationAssistantService()
    request = ConversationRequest("en", "How do I configure BPM?")

    assert service.status(locale="en", session_id="session").state == "not-installed"
    assert service.ask(request=request, session_id="session").request_id is None
    assert service.web_mode_status(locale="en", session_id="session").available is False
    assert (
        service.set_web_mode(locale="en", session_id="session", enabled=True, tab_id=TAB_ID).enabled
        is False
    )
    assert service.events(request_id="request", session_id="session") is None
    assert service.cancel(request_id="request", session_id="session") is None
    assert service.clear(session_id="session") is True
    assert service.source(request_id="request", source_id="source", session_id="session") is None

    incomplete = ConversationStreamEvent(
        "accepted",
        "req_example",
        "accepted",
        1,
        "assistant_accepted",
        "assistant_chat_accepted",
        "assistant_chat_cancel",
        incomplete=True,
    )
    assert _event_payload(incomplete)["incomplete"] is True


def test_json_body_guard_handles_declared_and_streamed_invalid_payloads() -> None:
    cases = (
        (
            {"content-length": str(assistant_api.ASSISTANT_MAX_REQUEST_BYTES + 1)},
            (b"{}",),
            "assistant_request_too_large",
        ),
        ({"content-length": "not-a-number"}, (b"{}",), "assistant_invalid_request"),
        (
            {},
            (b"x" * (assistant_api.ASSISTANT_MAX_REQUEST_BYTES + 1),),
            "assistant_request_too_large",
        ),
        ({}, (), "assistant_invalid_request"),
        ({}, (b"[]",), "assistant_invalid_request"),
        ({}, (b"{",), "assistant_invalid_request"),
        ({}, (b'{"api_version":true}',), "assistant_api_version_unsupported"),
    )

    for headers, chunks, reason_code in cases:
        with pytest.raises(HTTPException) as raised:
            asyncio.run(
                assistant_api._json_body(_BodyRequest(headers, chunks), assistant_api._AskPayload)  # type: ignore[arg-type]
            )
        assert raised.value.detail["reason_code"] == reason_code

    with pytest.raises(HTTPException) as empty_body:
        asyncio.run(
            assistant_api._json_body(_NoBodyRequest({}), assistant_api._AskPayload)  # type: ignore[arg-type]
        )
    assert empty_body.value.detail["reason_code"] == "assistant_invalid_request"

    with pytest.raises(HTTPException) as missing_host:
        assistant_api._require_same_origin_json(SimpleNamespace(headers={}))
    assert missing_host.value.detail["reason_code"] == "assistant_invalid_request"
    assert len(assistant_api._session(SimpleNamespace(cookies={}))) >= 20


def test_api_missing_resource_invalid_locale_and_clear_paths_fail_closed() -> None:
    app = create_app()
    service = _AssistantService()
    service.cancel = lambda **_: None  # type: ignore[method-assign]
    app.state.documentation_assistant_service = service

    with make_test_client(app) as client:
        status_response = client.get("/api/documentation-assistant/status?locale=en")
        session_cookie = status_response.headers["set-cookie"].split(";", 1)[0]
        assert client.get("/api/documentation-assistant/status?locale=ja").status_code == 400
        service.ask = lambda **_: ConversationAdmission(  # type: ignore[method-assign]
            None, "error", "assistant_unavailable", 7
        )
        assert (
            client.post(
                "/api/documentation-assistant/chat",
                headers=_headers(session_cookie),
                json={"api_version": 1, "locale": "en", "question": "BPM", "tab_id": TAB_ID},
            ).status_code
            == 503
        )
        assert (
            client.get(
                "/api/documentation-assistant/chat/missing/stream",
                headers={"Cookie": session_cookie},
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/api/documentation-assistant/chat/missing/cancel",
                headers=_headers(session_cookie),
                json={"api_version": 1},
            ).status_code
            == 404
        )
        assert (
            client.get(
                "/api/documentation-assistant/chat/req_example/sources/missing",
                headers={"Cookie": session_cookie},
            ).status_code
            == 404
        )
        assert (
            client.delete(
                "/api/documentation-assistant/conversation?locale=en",
                headers={"Cookie": session_cookie},
            ).status_code
            == 400
        )
        assert (
            client.delete(
                "/api/documentation-assistant/conversation",
                headers={"Cookie": session_cookie},
            ).status_code
            == 204
        )

    assert service.clear_calls[-1][1:] == (None, None)
