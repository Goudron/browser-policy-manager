from __future__ import annotations

from pathlib import Path
from typing import Annotated

import httpx
import pytest
from alembic.config import Config
from fastapi import Depends, HTTPException
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from alembic import command
from app import db as db_module
from app.db import get_session
from app.main import create_app
from app.models.profile import Profile


def test_normalize_database_url_keeps_empty_sqlite_path():
    assert db_module._normalize_database_url("sqlite+aiosqlite:///") == ("sqlite+aiosqlite:///")


def test_normalize_database_url_converts_sync_sqlite_and_resolves_bare_path(
    tmp_path: Path,
):
    normalized = db_module._normalize_database_url(
        "sqlite:///data/app.db",
        root_dir=tmp_path,
    )

    assert normalized == f"sqlite+aiosqlite:///{(tmp_path / 'data' / 'app.db').resolve()}"


def test_ensure_sqlite_parent_dir_skips_memory_and_non_sqlite_urls(tmp_path: Path):
    memory_target = tmp_path / "memory-parent"
    nonsqlite_target = tmp_path / "postgres-parent"

    db_module._ensure_sqlite_parent_dir(f"sqlite+aiosqlite:///{memory_target}/:memory:")
    db_module._ensure_sqlite_parent_dir(f"postgresql+asyncpg:///{nonsqlite_target}/db")

    assert not memory_target.exists()
    assert not nonsqlite_target.exists()


def test_ensure_sqlite_parent_dir_creates_missing_parent(tmp_path: Path):
    target_dir = tmp_path / "nested" / "sqlite"
    db_url = f"sqlite+aiosqlite:///{target_dir / 'app.db'}"

    db_module._ensure_sqlite_parent_dir(db_url)

    assert target_dir.is_dir()


@pytest.mark.anyio
async def test_database_runtime_init_performs_no_schema_ddl(tmp_path: Path):
    db_path = tmp_path / "runtime-does-not-bootstrap.db"
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    try:
        await runtime.init()
    finally:
        await runtime.dispose()

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        assert inspect(engine).get_table_names() == []
    finally:
        engine.dispose()


def _create_test_profile_schema(path: Path) -> None:
    """Fixture-only bootstrap; production schema ownership belongs to Alembic."""
    engine = create_engine(f"sqlite:///{path}", future=True)
    try:
        Profile.metadata.create_all(engine)
    finally:
        engine.dispose()


def _upgrade_test_database(path: Path) -> None:
    """Create a true disposable Alembic head for application-lifespan tests."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(config, "head")


@pytest.mark.anyio
async def test_database_runtime_is_lazy_native_async_and_disposable(tmp_path: Path):
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'runtime.db'}",
        echo=False,
    )

    assert runtime.engine is None
    assert runtime.initialized is False

    await runtime.init()
    assert isinstance(runtime.engine, AsyncEngine)
    assert runtime.initialized is True
    async with runtime.session() as session:
        assert isinstance(session, AsyncSession)

    await runtime.dispose()
    assert runtime.engine is None
    assert runtime.initialized is False


@pytest.mark.anyio
async def test_database_runtime_rolls_back_without_leaking_transaction_state(tmp_path: Path):
    db_path = tmp_path / "rollback.db"
    _create_test_profile_schema(db_path)
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    try:
        await runtime.init()
        async with runtime.session() as session:
            session.add(
                Profile(
                    name="rolled-back",
                    schema_version="release-153",
                    flags={"DisableTelemetry": True},
                )
            )
            await session.flush()
            await session.rollback()

        async with runtime.session() as session:
            assert await session.scalar(select(func.count()).select_from(Profile)) == 0
    finally:
        await runtime.dispose()


@pytest.mark.anyio
async def test_database_runtimes_isolate_independent_app_state(tmp_path: Path):
    first_path = tmp_path / "first.db"
    second_path = tmp_path / "second.db"
    _create_test_profile_schema(first_path)
    _create_test_profile_schema(second_path)
    first = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{first_path}",
        echo=False,
    )
    second = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{second_path}",
        echo=False,
    )
    try:
        await first.init()
        await second.init()
        async with first.session() as session:
            session.add(
                Profile(
                    name="first-only",
                    schema_version="release-153",
                    flags={"DisableTelemetry": True},
                )
            )
            await session.commit()

        async with second.session() as session:
            assert await session.scalar(select(func.count()).select_from(Profile)) == 0
    finally:
        await first.dispose()
        await second.dispose()


@pytest.mark.anyio
async def test_application_lifespan_initializes_and_disposes_injected_runtime(tmp_path: Path):
    db_path = tmp_path / "lifespan.db"
    _upgrade_test_database(db_path)
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    app = create_app(database_runtime=runtime)

    assert app.state.database_runtime is runtime
    assert runtime.engine is None
    async with app.router.lifespan_context(app):
        assert runtime.initialized is True
        assert runtime.engine is not None

    assert runtime.initialized is False
    assert runtime.engine is None


@pytest.mark.anyio
async def test_request_dependency_rolls_back_failed_transaction(tmp_path: Path):
    db_path = tmp_path / "request-rollback.db"
    _upgrade_test_database(db_path)
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    app = create_app(database_runtime=runtime)

    @app.post("/_runtime-test/rollback")
    async def rollback_route(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> None:
        session.add(
            Profile(
                name="dependency-rollback",
                schema_version="release-153",
                flags={"DisableTelemetry": True},
            )
        )
        await session.flush()
        raise HTTPException(status_code=409, detail="rollback")

    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://runtime-test",
            ) as client:
                response = await client.post("/_runtime-test/rollback")
            assert response.status_code == 409
            async with runtime.session() as session:
                assert await session.scalar(select(func.count()).select_from(Profile)) == 0
    finally:
        await runtime.dispose()


@pytest.mark.anyio
async def test_application_lifespan_initializes_once_and_requests_do_not_reinitialize(
    tmp_path: Path,
):
    class CountingRuntime(db_module.DatabaseRuntime):
        def __init__(self) -> None:
            super().__init__(
                database_url=f"sqlite+aiosqlite:///{tmp_path / 'counting-lifespan.db'}",
                echo=False,
            )
            self.init_calls = 0
            self.dispose_calls = 0

        async def init(self) -> None:
            self.init_calls += 1
            await super().init()

        async def dispose(self) -> None:
            self.dispose_calls += 1
            await super().dispose()

    runtime = CountingRuntime()
    _upgrade_test_database(tmp_path / "counting-lifespan.db")
    app = create_app(database_runtime=runtime)

    async with app.router.lifespan_context(app):
        assert runtime.init_calls == 1
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://runtime-test",
        ) as client:
            assert (await client.get("/profiles")).status_code == 200
            assert (await client.get("/api/profiles")).status_code == 200
        assert runtime.init_calls == 1

    assert runtime.dispose_calls == 1


@pytest.mark.anyio
async def test_library_page_has_no_database_dependency_after_startup(tmp_path: Path):
    db_path = tmp_path / "library-page.db"
    _upgrade_test_database(db_path)
    runtime = db_module.DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    app = create_app(database_runtime=runtime)

    async def fail_if_resolved():
        raise AssertionError("library page must not resolve a database session")
        yield

    async with app.router.lifespan_context(app):
        app.dependency_overrides[get_session] = fail_if_resolved
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://runtime-test",
            ) as client:
                response = await client.get("/profiles")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_session, None)


@pytest.mark.anyio
async def test_runtime_session_requires_explicit_lifecycle_readiness():
    runtime = db_module.DatabaseRuntime(
        database_url="sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    try:
        with pytest.raises(RuntimeError, match="application lifespan"):
            async with runtime.session():
                pass
    finally:
        await runtime.dispose()
