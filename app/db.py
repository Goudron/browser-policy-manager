# app/db.py
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text
from sqlalchemy.engine import Connection as SyncConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Project settings and ORM base
from .core.config import get_settings
from .models.policy import Base

_engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
_initialized: bool = False


def _database_url() -> str:
    """
    Resolve database URL from settings or fallback to local SQLite.
    """
    settings = get_settings()
    url = getattr(settings, "DATABASE_URL", None) or getattr(
        settings, "database_url", None
    )
    if not url:
        # Dev-friendly default
        url = "sqlite+aiosqlite:///./bpm.db"
    return url


async def _create_engine() -> None:
    global _engine, SessionLocal
    if _engine is None:
        _engine = create_async_engine(
            _database_url(),
            echo=False,
            future=True,
        )
        SessionLocal = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def _create_schema() -> None:
    """
    Create tables if they do not exist (async wrapper around metadata.create_all).
    """
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _has_deleted_at(sync_conn: SyncConnection) -> bool:
    """
    Inspect 'policies' columns in a synchronous context and check 'deleted_at'.
    Works across SQLite/PostgreSQL backends via SQLAlchemy inspector.
    """
    insp = sa_inspect(sync_conn)
    try:
        cols = insp.get_columns("policies")
    except Exception:
        # Table may not exist yet
        return False
    for c in cols:
        if c.get("name") == "deleted_at":
            return True
    return False


async def _apply_minimal_migrations() -> None:
    """
    Minimal dev/CI migrations to keep schema in sync without Alembic:
    - Add 'deleted_at' to 'policies' if missing.
    """
    assert _engine is not None
    async with _engine.begin() as conn:
        has_col = await conn.run_sync(_has_deleted_at)
        if not has_col:
            # Portable-ish SQL: SQLAlchemy will adapt types for the dialect.
            # For SQLite: TIMESTAMP is acceptable, timezone info is not enforced.
            await conn.execute(
                text("ALTER TABLE policies ADD COLUMN deleted_at TIMESTAMP NULL")
            )


async def init_db() -> None:
    """
    Initialize engine, create schema, and apply minimal migrations.
    Intended for app startup and test bootstrap.
    """
    await _create_engine()
    await _create_schema()
    await _apply_minimal_migrations()


async def _ensure_initialized() -> None:
    global _initialized
    if not _initialized:
        await init_db()
        _initialized = True


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async SQLAlchemy session.
    """
    await _ensure_initialized()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        yield session


def init_db_sync() -> None:  # pragma: no cover
    """Helper to run initialization from a synchronous context (CLI, etc.)."""
    asyncio.run(init_db())
