"""Same-origin, session-bound release UI API for explicit local-model lifecycle actions."""

from __future__ import annotations

import json
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.ai.least_privilege import (
    ASSISTANT_MAX_REQUEST_BYTES,
    AssistantRequestGuard,
    AssistantRequestMetadata,
    LeastPrivilegeViolation,
)
from app.ai.model_management import ModelManagementController

router = APIRouter(prefix="/api/local-model", include_in_schema=False)

API_VERSION = 1
MAX_REQUEST_BYTES = min(1024, ASSISTANT_MAX_REQUEST_BYTES)
SESSION_COOKIE = "bpm_local_model_session"
SESSION_TTL_SECONDS = 30 * 60
MAX_SESSIONS = 128


@dataclass
class _SessionRecord:
    csrf_token: str
    expires_at: float


class _SessionCsrfStore:
    def __init__(self, *, clock: Any = time.monotonic) -> None:
        self._clock = clock
        self._records: OrderedDict[str, _SessionRecord] = OrderedDict()
        self._lock = threading.RLock()

    def issue(self, presented: str | None) -> tuple[str, str, bool]:
        with self._lock:
            self._prune_locked()
            if presented is not None and presented in self._records:
                record = self._records.pop(presented)
                record.expires_at = self._clock() + SESSION_TTL_SECONDS
                self._records[presented] = record
                return presented, record.csrf_token, False
            session_id = secrets.token_urlsafe(24)
            token = secrets.token_urlsafe(32)
            self._records[session_id] = _SessionRecord(
                csrf_token=token, expires_at=self._clock() + SESSION_TTL_SECONDS
            )
            self._trim_locked()
            return session_id, token, True

    def consume_and_rotate(self, session_id: str | None, csrf_token: str) -> str | None:
        with self._lock:
            self._prune_locked()
            if session_id is None:
                return None
            record = self._records.get(session_id)
            if record is None or not secrets.compare_digest(record.csrf_token, csrf_token):
                return None
            replacement = secrets.token_urlsafe(32)
            record.csrf_token = replacement
            record.expires_at = self._clock() + SESSION_TTL_SECONDS
            self._records.move_to_end(session_id)
            return replacement

    def _prune_locked(self) -> None:
        now = self._clock()
        for session_id in [
            key for key, record in self._records.items() if record.expires_at <= now
        ]:
            del self._records[session_id]

    def _trim_locked(self) -> None:
        while len(self._records) > MAX_SESSIONS:
            self._records.popitem(last=False)


class _ActionRequest(BaseModel):
    api_version: Literal[1]
    locale: str = Field(min_length=2, max_length=16)
    csrf_token: str = Field(min_length=20, max_length=128)

    model_config = ConfigDict(extra="forbid", strict=True)


class _InstallRequest(_ActionRequest):
    confirm_install: Literal[True]


class _RemoveRequest(_ActionRequest):
    confirm_remove: Literal[True]


class _CancelRequest(_ActionRequest):
    operation_id: str = Field(min_length=20, max_length=128)


_sessions = _SessionCsrfStore()
_controller = ModelManagementController.from_settings()


def _response(
    payload: dict[str, Any], *, request: Request, session_id: str, set_cookie: bool
) -> JSONResponse:
    response = JSONResponse(payload)
    if set_cookie:
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            httponly=True,
            samesite="strict",
            secure=request.url.scheme == "https",
            max_age=SESSION_TTL_SECONDS,
            path="/api/local-model",
        )
    return response


def _error(status_code: int, reason_code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code, detail={"api_version": API_VERSION, "reason_code": reason_code}
    )


async def _read_bounded_json(request: Request) -> dict[str, Any]:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "model_request_too_large")
        except ValueError as exc:
            raise _error(status.HTTP_400_BAD_REQUEST, "model_invalid_content_length") from exc
    body = bytearray()
    stream = request.stream()
    while True:
        try:
            chunk = await anext(stream)
        except StopAsyncIteration:
            break
        body.extend(chunk)
        if len(body) > MAX_REQUEST_BYTES:
            raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "model_request_too_large")
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(status.HTTP_400_BAD_REQUEST, "model_invalid_request") from exc
    if not isinstance(decoded, dict):
        raise _error(status.HTTP_400_BAD_REQUEST, "model_invalid_request")
    return decoded


async def _validated_action(
    request: Request, model: type[_ActionRequest]
) -> tuple[_ActionRequest, str, str]:
    host = request.headers.get("host")
    if not host:
        raise _error(status.HTTP_400_BAD_REQUEST, "model_invalid_host")
    try:
        guard = AssistantRequestGuard(
            f"{request.url.scheme}://{host}", maximum_bytes=MAX_REQUEST_BYTES
        )
        guard.require_same_origin_json(
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
        if exc.code == "assistant_request_too_large":
            raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "model_request_too_large") from exc
        raise _error(status.HTTP_403_FORBIDDEN, "model_request_rejected") from exc
    raw = await _read_bounded_json(request)
    try:
        parsed = model.model_validate(raw)
    except ValidationError as exc:
        raise _error(status.HTTP_400_BAD_REQUEST, "model_invalid_request") from exc
    session_id = request.cookies.get(SESSION_COOKIE)
    next_token = _sessions.consume_and_rotate(session_id, parsed.csrf_token)
    if session_id is None or next_token is None:
        raise _error(status.HTTP_403_FORBIDDEN, "model_csrf_rejected")
    return parsed, session_id, next_token


@router.get("")
async def local_model_status(request: Request, locale: str = "en") -> JSONResponse:
    session_id, csrf_token, set_cookie = _sessions.issue(request.cookies.get(SESSION_COOKIE))
    try:
        payload = _controller.status(locale=locale, session_id=session_id)
    except Exception:
        raise _error(status.HTTP_400_BAD_REQUEST, "model_unsupported_locale") from None
    payload["csrf_token"] = csrf_token
    return _response(payload, request=request, session_id=session_id, set_cookie=set_cookie)


@router.post("/install")
async def local_model_install(request: Request) -> JSONResponse:
    payload, session_id, csrf_token = await _validated_action(request, _InstallRequest)
    activation_callback = getattr(request.app.state, "documentation_assistant_activation", None)

    def activate_assistant() -> bool:
        return True if activation_callback is None else bool(activation_callback())

    result = _controller.start_install(
        locale=payload.locale,
        session_id=session_id,
        after_install=activate_assistant,
    )
    return _response(
        {"api_version": API_VERSION, "csrf_token": csrf_token, **result},
        request=request,
        session_id=session_id,
        set_cookie=False,
    )


@router.post("/verify")
async def local_model_verify(request: Request) -> JSONResponse:
    payload, session_id, csrf_token = await _validated_action(request, _ActionRequest)
    result = _controller.start_verify(locale=payload.locale, session_id=session_id)
    return _response(
        {"api_version": API_VERSION, "csrf_token": csrf_token, **result},
        request=request,
        session_id=session_id,
        set_cookie=False,
    )


@router.post("/remove")
async def local_model_remove(request: Request) -> JSONResponse:
    payload, session_id, csrf_token = await _validated_action(request, _RemoveRequest)
    result = _controller.start_remove(locale=payload.locale, session_id=session_id)
    return _response(
        {"api_version": API_VERSION, "csrf_token": csrf_token, **result},
        request=request,
        session_id=session_id,
        set_cookie=False,
    )


@router.post("/cancel")
async def local_model_cancel(request: Request) -> JSONResponse:
    payload, session_id, csrf_token = await _validated_action(request, _CancelRequest)
    assert isinstance(payload, _CancelRequest)
    result = _controller.cancel(session_id=session_id, operation_id=payload.operation_id)
    return _response(
        {"api_version": API_VERSION, "csrf_token": csrf_token, **result},
        request=request,
        session_id=session_id,
        set_cookie=False,
    )
