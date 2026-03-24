from __future__ import annotations

import asyncio

from starlette.types import Message

from app import main as main_module
from app.middleware.security import SecurityHeadersMiddleware
from tests.support import make_test_client


def test_resolve_path_preserves_absolute_path(tmp_path):
    absolute = tmp_path / "catalog.json"

    assert main_module._resolve_path(absolute) == absolute


def test_make_app_returns_fastapi_app():
    app = main_module.make_app()

    assert app.title == main_module.settings.APP_NAME


def test_locale_catalog_rejects_unsupported_locale(monkeypatch):
    original_locales = list(main_module.settings.SUPPORTED_LOCALES)
    monkeypatch.setattr(main_module.settings, "SUPPORTED_LOCALES", ["en"])
    client = make_test_client(main_module.create_app())

    response = client.get("/i18n/de.json")

    assert response.status_code == 404
    assert response.json()["detail"] == "Locale not supported"

    monkeypatch.setattr(main_module.settings, "SUPPORTED_LOCALES", original_locales)


def test_locale_catalog_returns_file_not_found_for_missing_catalog(tmp_path, monkeypatch):
    i18n_dir = tmp_path / "i18n"
    i18n_dir.mkdir()
    monkeypatch.setattr(main_module.settings, "SUPPORTED_LOCALES", ["en", "ru"])
    monkeypatch.setattr(main_module.settings, "I18N_DIR", str(i18n_dir))
    client = make_test_client(main_module.create_app())

    response = client.get("/i18n/ru.json")

    assert response.status_code == 404
    assert response.json()["detail"] == "Locale file not found"


def test_security_headers_middleware_passthrough_for_non_http_scope():
    calls = {"app": False, "messages": []}

    async def _fake_app(scope, receive, send):
        calls["app"] = True
        await send({"type": "websocket.accept"})

    async def _receive():
        return {"type": "websocket.connect"}

    async def _send(message: Message):
        calls["messages"].append(message)

    middleware = SecurityHeadersMiddleware(_fake_app)

    asyncio.run(middleware({"type": "websocket"}, _receive, _send))

    assert calls["app"] is True
    assert calls["messages"] == [{"type": "websocket.accept"}]


def test_append_if_missing_keeps_existing_header_value():
    headers = [(b"x-frame-options", b"SAMEORIGIN")]

    SecurityHeadersMiddleware._append_if_missing(headers, b"X-Frame-Options", b"DENY")

    assert headers == [(b"x-frame-options", b"SAMEORIGIN")]


def test_create_app_works_when_cors_disabled(monkeypatch):
    monkeypatch.setattr(main_module.settings, "ENABLE_CORS", False)
    client = make_test_client(main_module.create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
