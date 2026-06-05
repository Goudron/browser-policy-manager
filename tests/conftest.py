# ruff: noqa: E402
import asyncio
import gc
import os
import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.db_harness import WorkerDatabaseContext, configure_worker_database

TEST_DATABASE_CONTEXT = configure_worker_database()

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import AsyncSessionAdapter, get_session
from app.main import app as default_app
from app.models.profile import Base
from tests.app_harness import (
    fresh_test_app,
    restore_dependency_overrides,
    snapshot_dependency_overrides,
)
from tests.cache_harness import reset_app_caches as reset_registered_app_caches
from tests.marker_policy import markers_for_path


def _dispose_global_database_engine() -> None:
    try:
        from app import db as db_module

        db_module.engine.dispose()
    except Exception:
        pass


def pytest_collection_modifyitems(config, items):
    root = Path(str(config.rootpath))
    for item in items:
        try:
            path = Path(str(item.fspath)).resolve().relative_to(root)
        except ValueError:
            path = Path(str(item.fspath))
        for marker in sorted(markers_for_path(path)):
            item.add_marker(marker)


def pytest_unconfigure(config):
    _dispose_global_database_engine()
    TEST_DATABASE_CONTEXT.cleanup()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def worker_database_context() -> WorkerDatabaseContext:
    return TEST_DATABASE_CONTEXT


@pytest.fixture(scope="session", autouse=True)
def guard_worker_database(worker_database_context: WorkerDatabaseContext):
    project_database_path = (PROJECT_ROOT / "data" / "bpm.db").resolve()

    assert worker_database_context.database_path.resolve() != project_database_path
    assert os.environ["BPM_DATABASE_URL"] == worker_database_context.database_url
    yield
    _dispose_global_database_engine()
    worker_database_context.cleanup()


@pytest.fixture(autouse=True)
def cleanup_global_sqlite_engine():
    yield
    _dispose_global_database_engine()
    gc.collect()


@pytest.fixture(autouse=True)
def guard_default_app_dependency_overrides():
    default_app.dependency_overrides.clear()
    yield
    default_app.dependency_overrides.clear()


@pytest.fixture
def app_factory():
    return fresh_test_app


@pytest.fixture
def test_app(app_factory):
    return app_factory()


@pytest.fixture
def reset_app_caches():
    reset_registered_app_caches()
    yield reset_registered_app_caches
    reset_registered_app_caches()


@pytest.fixture
async def test_session():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    testing_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = testing_session_factory()
    try:
        yield AsyncSessionAdapter(session)
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
async def client(test_app, test_session):
    # Override FastAPI dependency to use in-memory session for tests
    async def override_get_session():
        yield test_session

    override_snapshot = snapshot_dependency_overrides(test_app)
    test_app.dependency_overrides[get_session] = override_get_session

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    restore_dependency_overrides(test_app, override_snapshot)
