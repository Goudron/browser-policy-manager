from __future__ import annotations

import asyncio
import contextlib
import socket
import tempfile
import threading
import time
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import requests
import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import AsyncSessionAdapter, get_session
from app.models.profile import Base


class TestClient:
    """Sync-friendly test client backed by httpx ASGITransport."""

    __test__ = False

    def __init__(
        self,
        app: FastAPI,
        base_url: str = "http://testserver",
        on_close: Any | None = None,
        **kwargs: Any,
    ):
        self.app = app
        self.base_url = base_url
        self._on_close = on_close
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
        if self._on_close is not None:
            self._on_close()
            self._on_close = None
        self._runner.close()
        self._closed = True

    def __del__(self):
        try:
            if self._closed:
                return
            self.close()
        except Exception:
            pass


def build_profile_payload(
    *,
    name_prefix: str = "Profile",
    description: str = "Test profile",
    schema_version: str = "esr-140.10",
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

    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    testing_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = testing_session_factory()
    previous_override = app.dependency_overrides.get(get_session)

    async def override_get_session():
        yield AsyncSessionAdapter(session)

    app.dependency_overrides[get_session] = override_get_session

    def _cleanup() -> None:
        if previous_override is None:
            app.dependency_overrides.pop(get_session, None)
        else:
            app.dependency_overrides[get_session] = previous_override
        session.close()
        engine.dispose()

    return TestClient(app, on_close=_cleanup, **kwargs)


def assert_contains_all(text: str, snippets: Iterable[str]) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"Missing expected snippets: {missing[:10]}"


def assert_has_keys(mapping: Mapping[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in mapping]
    assert not missing, f"Missing expected keys: {missing[:10]}"


def pick_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


@dataclass
class TestAppServerHandle:
    base_url: str
    session_factory: Any


@contextlib.contextmanager
def run_test_app_server_handle(
    *,
    host: str = "127.0.0.1",
    log_level: str = "warning",
    startup_timeout: float = 20.0,
):
    """
    Run a fresh app instance behind a local uvicorn server for browser tests.

    This variant also exposes the sync SQLAlchemy session factory so tests can
    seed legacy or otherwise non-API-representable data directly into the
    temporary browser-test database.
    """

    from app.main import create_app

    app = create_app()
    with tempfile.TemporaryDirectory(prefix="bpm-ui-server-") as tmp_dir:
        db_path = Path(tmp_dir) / "bpm-ui.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        testing_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)

        async def override_get_session():
            session = testing_session_factory()
            try:
                yield AsyncSessionAdapter(session)
            finally:
                session.close()

        app.dependency_overrides[get_session] = override_get_session
        port = pick_free_port(host)
        config = uvicorn.Config(app=app, host=host, port=port, log_level=log_level)
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        base_url = f"http://{host}:{port}"
        deadline = time.time() + startup_timeout
        last_error: str | None = None

        try:
            while time.time() < deadline:
                try:
                    response = requests.get(f"{base_url}/i18n/en.json", timeout=2)
                    if response.status_code == 200:
                        break
                    last_error = f"probe returned {response.status_code}"
                except requests.RequestException as exc:
                    last_error = str(exc)
                time.sleep(0.2)
            else:
                raise RuntimeError(f"Timed out waiting for test app server at {base_url}: {last_error}")

            yield TestAppServerHandle(
                base_url=base_url,
                session_factory=testing_session_factory,
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            app.dependency_overrides.pop(get_session, None)
            engine.dispose()


@contextlib.contextmanager
def run_test_app_server(
    *,
    host: str = "127.0.0.1",
    log_level: str = "warning",
    startup_timeout: float = 20.0,
):
    """
    Run a fresh app instance behind a local uvicorn server for browser tests.

    The server uses a temporary SQLite database and request-scoped sessions so
    multi-tab browser regressions can exercise the real HTTP surface safely.
    """

    with run_test_app_server_handle(
        host=host,
        log_level=log_level,
        startup_timeout=startup_timeout,
    ) as handle:
        yield handle.base_url
