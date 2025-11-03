# app/db.py
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Import models to ensure metadata is populated
from app.models.policy import Policy  # noqa: F401


DB_PATH = Path("./data/bpm.db")
SQLITE_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_initialized = False


class Base(DeclarativeBase):
    """Base for ORM models."""
    pass


async def _create_schema() -> None:
    """Create folders and tables if not exist."""
    # Ensure ./data exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    assert _engine is not None

    # Import metadata from DeclarativeBase via any mapped model import above
    from app.models.base import metadata  # if you keep central metadata
    # Fallback to Base.metadata if you don’t have a custom metadata
    meta = getattr(metadata, "tables", None)
    target_metadata = getattr(Policy, "metadata", None) or Base.metadata

    async with _engine.begin() as conn:
        await conn.run_sync(target_metadata.create_all)


async def init_db() -> None:
    """Initialize engine/session and create schema."""
    global _engine, _session_factory, _initialized

    if _initialized:
        return

    _engine = create_async_engine(
        SQLITE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    await _create_schema()
    _initialized = True


async def _ensure_initialized() -> None:
    if not _initialized:
        await init_db()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for DB session."""
    await _ensure_initialized()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
