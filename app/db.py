# app/core/db.py
from __future__ import annotations

import importlib
import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

# Cached metadata instance
_metadata: MetaData | None = None
_LEGACY_PROFILE_TABLE = "policies"
_CURRENT_PROFILE_TABLE = "profiles"
_LEGACY_PROFILE_INDEXES = (
    "ix_policies_created_at",
    "ix_policies_name",
    "ix_policies_updated_at",
    "uq_policies_name",
    "uq_profiles_name",
)
_CURRENT_PROFILE_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS ix_profiles_created_at ON profiles (created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_profiles_name ON profiles (name)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_updated_at ON profiles (updated_at)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_schema_version ON profiles (schema_version)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_owner ON profiles (owner)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_deleted_at ON profiles (deleted_at)",
)


def _resolve_metadata() -> MetaData:
    """
    Resolve project's central SQLAlchemy MetaData dynamically.

    Resolution order:

      1) Import `app.models` and use:
         * `metadata` attribute if present, or
         * `Base.metadata` if `Base` is exported.

      2) Import `app.models.profile` (current single-model layout) and use
         its `Base.metadata`.

      3) Import `app.models.base` and use its `Base.metadata` if present.

      4) Fallback: create a local declarative base. This is only used as a
         last resort (e.g. in very minimal test setups).

    Service-layer tests call `init_db()` directly and then use
    `ProfileService` on the resulting schema, so it is important that this
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

    # 2) app.models.profile module (current single-model layout)
    try:
        mod_profile = importlib.import_module("app.models.profile")
        base = getattr(mod_profile, "Base", None)
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
    _settings.DATABASE_URL,
)
_DATABASE_ECHO: bool = cast(
    bool,
    _settings.DB_ECHO,
)


def _is_sqlite_async_url(url: str) -> bool:
    return url.startswith("sqlite+aiosqlite://")


def _to_sync_sqlite_url(url: str) -> str:
    return url.replace("sqlite+aiosqlite://", "sqlite://", 1)


def _ensure_sqlite_parent_dir(url: str) -> None:
    """
    Create the parent directory for file-based SQLite URLs when needed.

    GitHub Actions runners and fresh local checkouts may not have the relative
    `./data` directory yet. SQLite won't create missing parent directories on
    connect, so we do it proactively during engine setup.
    """
    if ":memory:" in url:
        return

    prefix, _, db_path = url.partition(":///")
    if not db_path or not prefix.startswith("sqlite"):
        return

    path = Path(db_path)
    parent = path.parent
    if str(parent) in ("", "."):
        return
    parent.mkdir(parents=True, exist_ok=True)


class AsyncSessionAdapter:
    """Async-friendly wrapper around a synchronous SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def scalars(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.scalars(*args, **kwargs)

    async def scalar(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.scalar(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.execute(*args, **kwargs)

    async def flush(self) -> None:
        self._session.flush()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()

    async def close(self) -> None:
        self._session.close()

    def add(self, instance: Any) -> None:
        self._session.add(instance)


def _upgrade_legacy_sqlite_schema(sync_engine: Engine) -> None:
    """
    Normalize local SQLite schema to the current `profiles` table layout.

    This keeps `init_db()` usable for local/dev databases that were created
    before the ORM table rename from `policies` to `profiles`.
    """
    inspector = inspect(sync_engine)
    has_profiles = inspector.has_table(_CURRENT_PROFILE_TABLE)
    has_policies = inspector.has_table(_LEGACY_PROFILE_TABLE)

    with sync_engine.begin() as conn:
        if not has_profiles and has_policies:
            conn.exec_driver_sql(
                f"ALTER TABLE {_LEGACY_PROFILE_TABLE} RENAME TO {_CURRENT_PROFILE_TABLE}"
            )

        inspector = inspect(conn)
        if not inspector.has_table(_CURRENT_PROFILE_TABLE):
            return

        columns = {column["name"] for column in inspector.get_columns(_CURRENT_PROFILE_TABLE)}
        if "deleted_at" not in columns:
            conn.exec_driver_sql("ALTER TABLE profiles ADD COLUMN deleted_at DATETIME")

        for index_name in _LEGACY_PROFILE_INDEXES:
            conn.exec_driver_sql(f"DROP INDEX IF EXISTS {index_name}")

        for ddl in _CURRENT_PROFILE_INDEX_DDL:
            conn.exec_driver_sql(ddl)


if _is_sqlite_async_url(_DATABASE_URL):
    _SYNC_DATABASE_URL = _to_sync_sqlite_url(_DATABASE_URL)
    _ensure_sqlite_parent_dir(_SYNC_DATABASE_URL)
    engine: Any = create_engine(
        _SYNC_DATABASE_URL,
        echo=_DATABASE_ECHO,
        future=True,
        poolclass=NullPool,
    )
    SessionLocal: Any = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    _SQLITE_SYNC_MODE = True
else:
    async_engine: AsyncEngine = create_async_engine(
        _DATABASE_URL,
        echo=_DATABASE_ECHO,
    )
    engine = async_engine
    SessionLocal = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
    )
    _SQLITE_SYNC_MODE = False


async def init_db() -> None:
    """Create tables if they do not exist (idempotent)."""
    if _SQLITE_SYNC_MODE:
        _upgrade_legacy_sqlite_schema(engine)
        get_metadata().create_all(bind=engine)
        return

    async with engine.begin() as conn:
        def _create_all(sync_conn: Connection) -> None:
            get_metadata().create_all(bind=sync_conn)

        await conn.run_sync(_create_all)


async def get_session() -> AsyncIterator[AsyncSession | AsyncSessionAdapter]:
    """FastAPI dependency that yields an AsyncSession."""
    await init_db()
    if _SQLITE_SYNC_MODE:
        session = SessionLocal()
        try:
            yield AsyncSessionAdapter(session)
        finally:
            session.close()
        return

    async with SessionLocal() as session:
        yield session
