# app/core/db.py
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

    Resolution order:

      1) Import `app.models` and use:
         * `metadata` attribute if present, or
         * `Base.metadata` if `Base` is exported.

      2) Import `app.models.policy` (current single-model layout) and use
         its `Base.metadata`.

      3) Import `app.models.base` and use its `Base.metadata` if present.

      4) Fallback: create a local declarative base. This is only used as a
         last resort (e.g. in very minimal test setups).

    Service-layer tests call `init_db()` directly and then use
    `PolicyService` on the resulting schema, so it is important that this
    function returns metadata that actually contains the ORM tables.
    """
    # 1) app.models package
    try:
        models = importlib.import_module("app.models")
        md = getattr(models, "metadata", None)
        if isinstance(md, MetaData):
            return md

        base = getattr(models, "Base", None)
        if base is not None and hasattr(base, "metadata"):
            return cast(MetaData, base.metadata)
    except Exception:
        # Best-effort; fall through to the next strategy.
        pass

    # 2) app.models.policy module (current single-model layout)
    try:
        mod_policy = importlib.import_module("app.models.policy")
        base = getattr(mod_policy, "Base", None)
        if base is not None and hasattr(base, "metadata"):
            return cast(MetaData, base.metadata)
    except Exception:
        # If this fails, we try the optional base module next.
        pass

    # 3) app.models.base module (optional)
    try:
        if importlib.util.find_spec("app.models.base") is not None:
            mod_base = importlib.import_module("app.models.base")
            base = getattr(mod_base, "Base", None)
            if base is not None and hasattr(base, "metadata"):
                return cast(MetaData, base.metadata)
    except Exception:
        # Final fallback below.
        pass

    # 4) Fallback - local Base
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
_DATABASE_URL: str = cast(
    str,
    getattr(_settings, "database_url", "sqlite+aiosqlite:///./bpm.db"),
)
_DATABASE_ECHO: bool = cast(
    bool,
    getattr(_settings, "database_echo", False),
)

# Engine / Session
engine: AsyncEngine = create_async_engine(
    _DATABASE_URL,
    echo=_DATABASE_ECHO,
)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


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
