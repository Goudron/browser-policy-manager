"""Same-origin API transport for the bounded local documentation assistant.

The router deliberately owns only HTTP admission, opaque browser-session cookies and safe response
shapes.  Retrieval, inference and citations remain behind an injected service so a missing model or
RAG generation fails closed instead of being replaced by a mock answer.
"""

from __future__ import annotations

import json
import re
import secrets
from collections.abc import Iterable
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.ai.least_privilege import (
    ASSISTANT_MAX_REQUEST_BYTES,
    AssistantRequestGuard,
    AssistantRequestMetadata,
    LeastPrivilegeViolation,
)
from app.documentation.assistant_contracts import (
    SUPPORTED_LOCALES,
    ConversationAdmission,
    ConversationRequest,
    ConversationStreamEvent,
)
from app.documentation.assistant_service import (
    AssistantSource,
    AssistantStatus,
    AssistantWebModeStatus,
    DocumentationAssistantService,
    TrainingDocumentationAssistantService,
)

router = APIRouter(prefix="/api/documentation-assistant", tags=["documentation-assistant"])

API_VERSION = 1
SESSION_COOKIE = "bpm_documentation_assistant_session"
SESSION_COOKIE_PATH = "/api/documentation-assistant"
MAX_SESSION_ID_LENGTH = 128
MAX_SOURCE_EXCERPT_CHARACTERS = 1_200
WEB_TAB_ID_PATTERN = r"^[A-Za-z0-9_-]{20,64}$"


class _AskPayload(BaseModel):
    api_version: Literal[1]
    locale: str = Field(min_length=2, max_length=16)
    question: str = Field(min_length=1, max_length=4_000)
    web_mode: Literal["local_only", "request_web"] = "local_only"
    tab_id: str | None = Field(default=None, pattern=WEB_TAB_ID_PATTERN)

    model_config = ConfigDict(extra="forbid", strict=True)


class _VersionPayload(BaseModel):
    api_version: Literal[1]

    model_config = ConfigDict(extra="forbid", strict=True)


class _WebModePayload(BaseModel):
    api_version: Literal[1]
    locale: str = Field(min_length=2, max_length=16)
    enabled: bool
    tab_id: str = Field(pattern=WEB_TAB_ID_PATTERN)

    model_config = ConfigDict(extra="forbid", strict=True)


class UnavailableDocumentationAssistantService:
    """Safe production default until M12A-03 supplies verified model/index dependencies."""

    def status(self, *, locale: str, session_id: str) -> AssistantStatus:
        return AssistantStatus(
            state="not-installed",
            assistant_ready=False,
            lexical_search_ready=True,
            locale=locale,
            message_key="assistant_not_installed",
            action_key="assistant_manage_model",
            reason_code="assistant_unavailable",
        )

    def ask(self, *, request: ConversationRequest, session_id: str) -> ConversationAdmission:
        return ConversationAdmission(None, "error", "assistant_unavailable", 0)

    def web_mode_status(
        self, *, locale: str, session_id: str, tab_id: str | None = None
    ) -> AssistantWebModeStatus:
        return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)

    def set_web_mode(
        self,
        *,
        locale: str,
        session_id: str,
        enabled: bool,
        tab_id: str | None = None,
    ) -> AssistantWebModeStatus:
        del session_id, enabled, tab_id
        return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)

    def events(
        self, *, request_id: str, session_id: str
    ) -> Iterable[ConversationStreamEvent] | None:
        return None

    def cancel(self, *, request_id: str, session_id: str) -> bool | None:
        return None

    def clear(
        self, *, session_id: str, locale: str | None = None, tab_id: str | None = None
    ) -> bool:
        return True

    def source(self, *, request_id: str, source_id: str, session_id: str) -> AssistantSource | None:
        return None


_DEFAULT_SERVICE = TrainingDocumentationAssistantService()


def _error(
    status_code: int, reason_code: str, *, state: str = "error", epoch: int = 0
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "api_version": API_VERSION,
            "state": state,
            "state_epoch": epoch,
            "reason_code": reason_code,
            "message_key": reason_code,
            "action_key": "assistant_chat_search",
        },
    )


def _service(request: Request) -> DocumentationAssistantService:
    value = getattr(request.app.state, "documentation_assistant_service", _DEFAULT_SERVICE)
    return value if value is not None else _DEFAULT_SERVICE


def _valid_locale(locale: str) -> str:
    if locale not in SUPPORTED_LOCALES:
        raise _error(status.HTTP_400_BAD_REQUEST, "assistant_unsupported_locale")
    return locale


def _valid_tab_id(tab_id: str) -> str:
    if not re.fullmatch(WEB_TAB_ID_PATTERN, tab_id):
        raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request")
    return tab_id


def _session(request: Request, response: JSONResponse | None = None) -> str:
    presented = request.cookies.get(SESSION_COOKIE)
    if presented is not None and 20 <= len(presented) <= MAX_SESSION_ID_LENGTH:
        return presented
    session_id = secrets.token_urlsafe(24)
    if response is not None:
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            httponly=True,
            samesite="strict",
            secure=request.url.scheme == "https",
            path=SESSION_COOKIE_PATH,
        )
    return session_id


async def _json_body(request: Request, model: type[BaseModel]) -> BaseModel:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > ASSISTANT_MAX_REQUEST_BYTES:
                raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "assistant_request_too_large")
        except ValueError as exc:
            raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request") from exc
    body = bytearray()
    stream = request.stream()
    while True:
        try:
            chunk = await anext(stream)
        except StopAsyncIteration:
            break
        body.extend(chunk)
        if len(body) > ASSISTANT_MAX_REQUEST_BYTES:
            raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "assistant_request_too_large")
    try:
        raw = json.loads(body.decode("utf-8"))
        if not isinstance(raw, dict):
            raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request")
        if type(raw.get("api_version")) is not int or raw["api_version"] != API_VERSION:
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "assistant_api_version_unsupported",
            )
        return model.model_validate(raw)
    except HTTPException:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request") from exc


def _require_same_origin_json(request: Request) -> None:
    host = request.headers.get("host")
    if not host:
        raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request")
    try:
        AssistantRequestGuard(
            f"{request.url.scheme}://{host}", maximum_bytes=ASSISTANT_MAX_REQUEST_BYTES
        ).require_same_origin_json(
            AssistantRequestMetadata(
                method=request.method,
                origin=request.headers.get("origin"),
                host=host,
                content_type=request.headers.get("content-type"),
                sec_fetch_site=request.headers.get("sec-fetch-site"),
                content_length=(
                    int(request.headers["content-length"])
                    if request.headers.get("content-length", "").isdigit()
                    else None
                ),
            )
        )
    except LeastPrivilegeViolation as exc:
        code = (
            "assistant_request_too_large"
            if exc.code == "assistant_request_too_large"
            else "assistant_invalid_request"
        )
        raise _error(
            (
                status.HTTP_413_CONTENT_TOO_LARGE
                if code.endswith("too_large")
                else status.HTTP_403_FORBIDDEN
            ),
            code,
        ) from exc


def _status_payload(value: AssistantStatus) -> dict[str, object]:
    return {"api_version": API_VERSION, **value.__dict__}


def _event_payload(event: ConversationStreamEvent) -> dict[str, object]:
    payload: dict[str, object] = {
        "api_version": API_VERSION,
        "request_id": event.request_id,
        "state": event.state,
        "state_epoch": event.state_epoch,
        "reason_code": event.reason_code,
        "message_key": event.message_key,
        "action_key": event.action_key,
    }
    if event.event_type == "final":
        payload.update(
            {
                "disposition": event.disposition,
                "text": event.text,
                "citations": list(event.source_ids),
            }
        )
        if event.external_claims:
            payload["external_claims"] = [
                {"text": claim.text, "citations": list(claim.source_ids)}
                for claim in event.external_claims
            ]
    if event.incomplete:
        payload["incomplete"] = True
    return payload


@router.get("/status")
async def assistant_status(request: Request, locale: str = "en") -> JSONResponse:
    locale = _valid_locale(locale)
    response = JSONResponse({})
    session_id = _session(request, response)
    payload = _status_payload(_service(request).status(locale=locale, session_id=session_id))
    response.body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    response.headers["content-length"] = str(len(response.body))
    return response


@router.get("/web-mode")
async def assistant_web_mode_status(
    request: Request, locale: str = "en", tab_id: str = ""
) -> JSONResponse:
    locale = _valid_locale(locale)
    tab_id = _valid_tab_id(tab_id)
    response = JSONResponse({})
    session_id = _session(request, response)
    value = _service(request).web_mode_status(locale=locale, session_id=session_id, tab_id=tab_id)
    response.body = json.dumps(
        {"api_version": API_VERSION, **value.__dict__},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    response.headers["content-length"] = str(len(response.body))
    return response


@router.post("/web-mode")
async def assistant_set_web_mode(request: Request) -> JSONResponse:
    _require_same_origin_json(request)
    payload = await _json_body(request, _WebModePayload)
    assert isinstance(payload, _WebModePayload)
    locale = _valid_locale(payload.locale)
    response = JSONResponse({})
    session_id = _session(request, response)
    value = _service(request).set_web_mode(
        locale=locale,
        session_id=session_id,
        enabled=payload.enabled,
        tab_id=payload.tab_id,
    )
    response.body = json.dumps(
        {"api_version": API_VERSION, **value.__dict__},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    response.headers["content-length"] = str(len(response.body))
    return response


@router.post("/chat", status_code=status.HTTP_202_ACCEPTED)
async def assistant_ask(request: Request) -> JSONResponse:
    _require_same_origin_json(request)
    payload = await _json_body(request, _AskPayload)
    assert isinstance(payload, _AskPayload)
    locale = _valid_locale(payload.locale)
    response = JSONResponse({}, status_code=status.HTTP_202_ACCEPTED)
    session_id = _session(request, response)
    admission = _service(request).ask(
        request=ConversationRequest(
            locale=locale,
            question=payload.question,
            web_mode=payload.web_mode,
            session_id=session_id,
            web_tab_id=payload.tab_id,
        ),
        session_id=session_id,
    )
    if admission.request_id is None:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            admission.reason_code,
            state=admission.state,
            epoch=admission.state_epoch,
        )
    response.body = json.dumps(
        {
            "api_version": API_VERSION,
            "request_id": admission.request_id,
            "state": admission.state,
            "state_epoch": admission.state_epoch,
            "stream_path": f"/api/documentation-assistant/chat/{admission.request_id}/stream",
            "time_preview": {
                "minimum_seconds": admission.time_preview.minimum_seconds,
                "maximum_seconds": admission.time_preview.maximum_seconds,
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    response.headers["content-length"] = str(len(response.body))
    return response


@router.get("/chat/{request_id}/stream")
async def assistant_stream(request: Request, request_id: str) -> StreamingResponse:
    session_id = _session(request)
    events = _service(request).events(request_id=request_id, session_id=session_id)
    if events is None:
        raise _error(status.HTTP_404_NOT_FOUND, "assistant_not_found")

    def encoded(values: Iterable[ConversationStreamEvent]) -> Iterable[bytes]:
        for event in values:
            yield f"event: {event.event_type}\ndata: {json.dumps(_event_payload(event), ensure_ascii=False)}\n\n".encode()

    return StreamingResponse(encoded(events), media_type="text/event-stream")


@router.post("/chat/{request_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def assistant_cancel(request: Request, request_id: str) -> JSONResponse:
    _require_same_origin_json(request)
    await _json_body(request, _VersionPayload)
    session_id = _session(request)
    cancelled = _service(request).cancel(request_id=request_id, session_id=session_id)
    if cancelled is None:
        raise _error(status.HTTP_404_NOT_FOUND, "assistant_not_found")
    return JSONResponse(
        {
            "api_version": API_VERSION,
            "request_id": request_id,
            "state": "cancelled",
            "state_epoch": 0,
            "reason_code": "assistant_cancelled",
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.delete("/conversation", status_code=status.HTTP_204_NO_CONTENT)
async def assistant_clear(
    request: Request, locale: str | None = None, tab_id: str | None = None
) -> None:
    session_id = _session(request)
    if (locale is None) != (tab_id is None):
        raise _error(status.HTTP_400_BAD_REQUEST, "assistant_invalid_request")
    if locale is not None and tab_id is not None:
        _service(request).clear(
            session_id=session_id,
            locale=_valid_locale(locale),
            tab_id=_valid_tab_id(tab_id),
        )
        return
    # Legacy callers without a UI tab handle still receive the safe all-context clear.
    _service(request).clear(session_id=session_id)


@router.get("/chat/{request_id}/sources/{source_id}")
async def assistant_source(request: Request, request_id: str, source_id: str) -> JSONResponse:
    session_id = _session(request)
    source = _service(request).source(
        request_id=request_id, source_id=source_id, session_id=session_id
    )
    if source is None:
        raise _error(status.HTTP_404_NOT_FOUND, "assistant_not_found")
    excerpt = source.excerpt[:MAX_SOURCE_EXCERPT_CHARACTERS]
    payload: dict[str, object] = {
        "api_version": API_VERSION,
        "source_id": source.source_id,
        "title": source.title,
        "published_url": source.published_url,
        "locale": source.locale,
        "excerpt": excerpt,
    }
    if source.source_kind != "local":
        payload.update({"source_kind": source.source_kind, "provider_id": source.provider_id})
    return JSONResponse(payload)
