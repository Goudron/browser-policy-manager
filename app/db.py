from __future__ import annotations

import importlib
import importlib.util
from collections.abc import AsyncIterator
from typing import cast

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# Cached metadata instance
_metadata: MetaData | None = None


def _resolve_metadata() -> MetaData:
    """
    Resolve project's central SQLAlchemy MetaData dynamically.

    Order:
      1) Try importing `app.models` (look for `metadata` or `Base.metadata`)
      2) Try importing `app.models.base` (look for `Base.metadata`)
      3) Fallback: create a local Base (for testing or empty setups)
    """
    # 1) app.models
    try:
        models = importlib.import_module("app.models")
        md = getattr(models, "metadata", None)
        if isinstance(md, MetaData):
            return md
        base = getattr(models, "Base", None)
        if base is not None and hasattr(base, "metadata"):
            return cast(MetaData, base.metadata)
    except Exception:
        pass

    # 2) app.models.base
    try:
        if importlib.util.find_spec("app.models.base") is not None:
            mod_base = importlib.import_module("app.models.base")
            base = getattr(mod_base, "Base", None)
            if base is not None and hasattr(base, "metadata"):
                return cast(MetaData, base.metadata)
    except Exception:
        pass

    # 3) Fallback - local Base
    from sqlalchemy.orm import declarative_base

    LocalBase = declarative_base()
    return LocalBase.metadata


def get_metadata() -> MetaData:
    """Return cached MetaData, resolving it on first use."""
    global _metadata
    if _metadata is None:
        _metadata = _resolve_metadata()
    return _metadata


# Settings
_settings = get_settings()
_DATABASE_URL: str = cast(str, getattr(_settings, "database_url", "sqlite+aiosqlite:///./bpm.db"))
_DATABASE_ECHO: bool = cast(bool, getattr(_settings, "database_echo", False))

# Engine / Session
engine: AsyncEngine = create_async_engine(_DATABASE_URL, echo=_DATABASE_ECHO)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create tables if they do not exist (idempotent)."""
    async with engine.begin() as conn:

        def _create_all(sync_conn: Connection) -> None:
            get_metadata().create_all(bind=sync_conn)

        await conn.run_sync(_create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an AsyncSession."""
    async with SessionLocal() as session:
        yield session
