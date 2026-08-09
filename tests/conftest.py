# ruff: noqa: E402
import asyncio
import os
import sys
from pathlib import Path

pytest_plugins = ("tests.browser.harness",)

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.db_harness import WorkerDatabaseContext, configure_worker_database

TEST_DATABASE_CONTEXT = configure_worker_database()

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_session
from app.main import app as default_app
from app.models.profile import Base
from tests.app_harness import (
    fresh_test_app,
    restore_dependency_overrides,
    snapshot_dependency_overrides,
)
from tests.cache_harness import reset_app_caches as reset_registered_app_caches
from tests.marker_policy import (
    AI_INCUBATION_TEST_FILES,
    OwnershipPolicyError,
    markers_for_path,
    primary_markers,
)


def pytest_addoption(parser):
    parser.addoption(
        "--run-ai-incubation",
        action="store_true",
        default=False,
        help="collect the optional local model/inference/RAG test contour",
    )


def pytest_ignore_collect(collection_path, config):
    try:
        relative = Path(str(collection_path)).resolve().relative_to(Path(str(config.rootpath)))
    except ValueError:
        return None
    normalized = relative.as_posix()
    if normalized in AI_INCUBATION_TEST_FILES:
        return None if config.getoption("--run-ai-incubation") else True
    if (
        config.getoption("--run-ai-incubation")
        and relative.suffix == ".py"
        and relative.name.startswith("test_")
        and relative.parts[:1] == ("tests",)
    ):
        return True
    return None


def pytest_collection_modifyitems(config, items):
    root = Path(str(config.rootpath))
    for item in items:
        try:
            path = Path(str(item.fspath)).resolve().relative_to(root)
        except ValueError:
            path = Path(str(item.fspath))
        try:
            markers = markers_for_path(path)
        except OwnershipPolicyError as error:
            raise pytest.UsageError(str(error)) from error
        for marker in sorted(markers):
            item.add_marker(marker)
        layers = primary_markers(marker.name for marker in item.iter_markers())
        if len(layers) != 1:
            raise pytest.UsageError(
                f"{item.nodeid} must have exactly one primary test layer; found {sorted(layers)}"
            )


def pytest_unconfigure(config):
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
    worker_database_context.cleanup()


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
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    testing_session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    try:
        async with testing_session_factory() as session:
            yield session
    finally:
        await engine.dispose()


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
