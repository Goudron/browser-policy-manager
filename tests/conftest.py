# ruff: noqa: E402
import asyncio
import gc
import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import AsyncSessionAdapter, get_session
from app.main import app
from app.models.profile import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def cleanup_global_sqlite_engine():
    yield
    try:
        from app import db as db_module

        db_module.engine.dispose()
    except Exception:
        pass
    gc.collect()


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
async def client(test_session):
    # Override FastAPI dependency to use in-memory session for tests
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
