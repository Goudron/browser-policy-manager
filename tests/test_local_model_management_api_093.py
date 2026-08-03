from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import local_model
from app.main import create_app
from tests.support import make_test_client


class _Controller:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def status(self, *, locale: str, session_id: str) -> dict[str, Any]:
        self.calls.append(("status", locale, session_id))
        return {
            "api_version": 1,
            "disclosure": {
                "model_id": "qwen3-0.6b-q8_0-official-gguf",
                "upstream": "Qwen",
                "license": "Apache-2.0",
                "byte_count": 639446688,
                "sha256": "a" * 64,
                "source_revision": "f" * 40,
            },
            "verification": {
                "state": "not-installed",
                "verified": False,
                "reason_code": "artifact_missing",
            },
            "operation": {"state": "idle"},
            "lexical_search_ready": True,
        }

    def start_install(
        self,
        *,
        locale: str,
        session_id: str,
        after_install: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(("install", locale, session_id))
        assert after_install is not None and after_install() is True
        return {"accepted": True, "operation": {"operation_id": "i" * 24, "state": "running"}}

    def start_verify(self, *, locale: str, session_id: str) -> dict[str, Any]:
        self.calls.append(("verify", locale, session_id))
        return {"accepted": True, "operation": {"operation_id": "v" * 24, "state": "running"}}

    def start_remove(self, *, locale: str, session_id: str) -> dict[str, Any]:
        self.calls.append(("remove", locale, session_id))
        return {"accepted": True, "operation": {"operation_id": "r" * 24, "state": "running"}}

    def cancel(self, *, session_id: str, operation_id: str) -> dict[str, Any]:
        self.calls.append(("cancel", "", session_id))
        return {"accepted": True, "reason_code": "model_cancellation_requested"}


@dataclass
class _BodyRequest:
    headers: dict[str, str]
    chunks: tuple[bytes, ...]

    async def stream(self):
        for chunk in self.chunks:
            yield chunk


@pytest.fixture
def model_controller(monkeypatch: pytest.MonkeyPatch) -> _Controller:
    controller = _Controller()
    monkeypatch.setattr(local_model, "_controller", controller)
    monkeypatch.setattr(local_model, "_sessions", local_model._SessionCsrfStore())
    return controller


def _session_headers(response: Any) -> tuple[dict[str, str], str]:
    session_id = response.cookies.get(local_model.SESSION_COOKIE)
    assert session_id
    token = response.json()["csrf_token"]
    return (
        {
            "Cookie": f"{local_model.SESSION_COOKIE}={session_id}",
            "Origin": "http://testserver",
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/json",
        },
        token,
    )


def test_status_only_inspects_and_discloses_the_pinned_artifact(
    model_controller: _Controller,
) -> None:
    with make_test_client(create_app()) as client:
        response = client.get("/api/local-model?locale=ru")

    assert response.status_code == 200
    payload = response.json()
    assert payload["disclosure"]["model_id"] == "qwen3-0.6b-q8_0-official-gguf"
    assert payload["disclosure"]["license"] == "Apache-2.0"
    assert payload["lexical_search_ready"] is True
    assert "path" not in payload["disclosure"]
    assert model_controller.calls and all(call[0] == "status" for call in model_controller.calls)


def test_state_changes_need_same_origin_rotating_csrf_and_explicit_confirmation(
    model_controller: _Controller,
) -> None:
    with make_test_client(create_app()) as client:
        initial = client.get("/api/local-model?locale=en")
        headers, token = _session_headers(initial)

        missing_origin = client.post(
            "/api/local-model/install",
            json={"api_version": 1, "locale": "en", "csrf_token": token, "confirm_install": True},
        )
        assert missing_origin.status_code == 403

        unconfirmed = client.post(
            "/api/local-model/install",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": token},
        )
        assert unconfirmed.status_code == 400

        install = client.post(
            "/api/local-model/install",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": token, "confirm_install": True},
        )
        assert install.status_code == 200
        next_token = install.json()["csrf_token"]
        assert next_token != token

        replay = client.post(
            "/api/local-model/install",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": token, "confirm_install": True},
        )
        assert replay.status_code == 403

        remove_without_remove_confirmation = client.post(
            "/api/local-model/remove",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": next_token, "confirm_install": True},
        )
        assert remove_without_remove_confirmation.status_code == 400

        remove = client.post(
            "/api/local-model/remove",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": next_token, "confirm_remove": True},
        )
        assert remove.status_code == 200

    assert [call[0] for call in model_controller.calls] == ["status", "install", "remove"]


def test_request_schema_and_actual_body_size_are_bounded_before_an_operation_starts(
    model_controller: _Controller,
) -> None:
    with make_test_client(create_app()) as client:
        initial = client.get("/api/local-model?locale=en")
        headers, token = _session_headers(initial)
        oversized = client.post(
            "/api/local-model/install",
            headers=headers,
            content=b"{" + b'"x":"' + b"x" * local_model.MAX_REQUEST_BYTES + b'"}',
        )
        assert oversized.status_code == 413

        unknown = client.post(
            "/api/local-model/install",
            headers=headers,
            json={
                "api_version": 1,
                "locale": "en",
                "csrf_token": token,
                "confirm_install": True,
                "artifact_path": "/private/model.gguf",
            },
        )
        assert unknown.status_code == 400

    assert [call[0] for call in model_controller.calls] == ["status"]


def test_session_store_reuses_rotates_prunes_and_bounds_csrf_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [0.0]
    store = local_model._SessionCsrfStore(clock=lambda: now[0])
    session_id, token, created = store.issue(None)
    reused_id, reused_token, reused = store.issue(session_id)

    assert created is True
    assert (reused_id, reused_token, reused) == (session_id, token, False)
    assert store.consume_and_rotate(None, token) is None
    assert store.consume_and_rotate(session_id, "wrong") is None
    replacement = store.consume_and_rotate(session_id, token)
    assert replacement and replacement != token

    now[0] += local_model.SESSION_TTL_SECONDS + 1
    store.issue(None)
    assert session_id not in store._records

    monkeypatch.setattr(local_model, "MAX_SESSIONS", 1)
    bounded = local_model._SessionCsrfStore(clock=lambda: now[0])
    first, _, _ = bounded.issue(None)
    second, _, _ = bounded.issue(None)
    assert first not in bounded._records
    assert second in bounded._records


def test_model_json_and_action_guards_reject_malformed_input_before_controller_work() -> None:
    cases = (
        ({"content-length": str(local_model.MAX_REQUEST_BYTES + 1)}, (b"{}",), "model_request_too_large"),
        ({"content-length": "bad"}, (b"{}",), "model_invalid_content_length"),
        ({}, (b"x" * (local_model.MAX_REQUEST_BYTES + 1),), "model_request_too_large"),
        ({}, (b"[]",), "model_invalid_request"),
        ({}, (b"{",), "model_invalid_request"),
    )
    for headers, chunks, reason_code in cases:
        with pytest.raises(HTTPException) as raised:
            asyncio.run(local_model._read_bounded_json(_BodyRequest(headers, chunks)))  # type: ignore[arg-type]
        assert raised.value.detail["reason_code"] == reason_code

    with pytest.raises(HTTPException) as missing_host:
        asyncio.run(
            local_model._validated_action(SimpleNamespace(headers={}), local_model._ActionRequest)  # type: ignore[arg-type]
        )
    assert missing_host.value.detail["reason_code"] == "model_invalid_host"


def test_verify_cancel_and_status_error_paths_are_exposed_without_extra_authority(
    model_controller: _Controller,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_test_client(create_app()) as client:
        initial = client.get("/api/local-model?locale=en")
        headers, token = _session_headers(initial)
        verified = client.post(
            "/api/local-model/verify",
            headers=headers,
            json={"api_version": 1, "locale": "en", "csrf_token": token},
        )
        assert verified.status_code == 200
        cancelled = client.post(
            "/api/local-model/cancel",
            headers=headers,
            json={
                "api_version": 1,
                "locale": "en",
                "csrf_token": verified.json()["csrf_token"],
                "operation_id": "o" * 24,
            },
        )
        assert cancelled.status_code == 200

    class _FailingController:
        def status(self, *, locale: str, session_id: str) -> dict[str, Any]:
            raise RuntimeError(f"unsupported: {locale}: {session_id}")

    monkeypatch.setattr(local_model, "_controller", _FailingController())
    with make_test_client(create_app()) as client:
        assert client.get("/api/local-model?locale=unsupported").status_code == 400

    assert [call[0] for call in model_controller.calls] == ["status", "verify", "cancel"]
