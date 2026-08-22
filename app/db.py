# app/core/db.py
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from fastapi import Request
from sqlalchemy import bindparam, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core import schema_channels
from app.core.config import Settings, get_settings

EXPECTED_DATABASE_REVISION = "20260821_add_profile_certificate_provenance"
EXPECTED_PROFILE_COLUMNS = {
    "id",
    "name",
    "name_casefold",
    "description",
    "schema_version",
    "flags",
    "compliance",
    "baseline_provenance",
    "extension_provenance",
    "certificate_provenance",
    "preparation_idempotency_key",
    "preparation_request_fingerprint",
    "revision",
    "created_at",
    "updated_at",
    "deleted_at",
}
EXPECTED_PROFILE_INDEXES = {
    "ix_profiles_name",
    "ix_profiles_name_casefold",
    "ix_profiles_schema_version",
    "ix_profiles_created_at",
    "ix_profiles_updated_at",
    "ix_profiles_deleted_at",
    "uq_profiles_preparation_idempotency_key",
}


class DatabaseReadinessError(RuntimeError):
    """The configured database is not an exact, application-readable BPM head."""


def _assert_no_retired_profile_channels(connection: Connection) -> None:
    """Reject an unupgraded retirement before any application route can read it.

    A retirement successor is migration data, not a runtime default. This
    checks only explicitly retired exact artifacts with one ``SELECT``; it
    never assigns an ORM field, normalizes a legacy value, or writes state.
    """
    retired_artifact_ids = schema_channels.retired_schema_channel_artifact_ids()
    if not retired_artifact_ids:
        return
    statement = text(
        "SELECT DISTINCT schema_version FROM profiles WHERE schema_version IN :retired_artifact_ids"
    ).bindparams(bindparam("retired_artifact_ids", expanding=True))
    retired_profile_exists = connection.execute(
        statement,
        {"retired_artifact_ids": retired_artifact_ids},
    ).first()
    if retired_profile_exists is not None:
        raise DatabaseReadinessError(
            "schema_channel_retired_requires_migration: configured database contains profiles "
            "on a retired Firefox schema channel; stop BPM and all other writers, verify a "
            "native backup/restore, then run the approved Alembic upgrade. Runtime startup, "
            "requests, and UI rendering never migrate or remap retired profiles."
        )


def _assert_release_schema_ready(connection: Connection) -> None:
    """Validate the release schema without mutating or attempting to repair it."""
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if "alembic_version" not in tables:
        raise DatabaseReadinessError(
            "Database is not Alembic-managed; restore a verified backup and upgrade a clean "
            "candidate before starting BPM"
        )
    if "profiles" not in tables or "policies" in tables:
        raise DatabaseReadinessError(
            "Database profile tables do not match the BPM 0.9.6 release schema"
        )

    # Prefer retirement-specific guidance over a generic head-stamp error
    # when the minimum safe profile column is present.
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    if "schema_version" in columns:
        _assert_no_retired_profile_channels(connection)

    revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    if revisions != [EXPECTED_DATABASE_REVISION]:
        raise DatabaseReadinessError(
            "Database revision is not the BPM 0.9.6 head; run the documented verified-backup "
            "candidate upgrade before starting BPM"
        )

    if columns != EXPECTED_PROFILE_COLUMNS:
        raise DatabaseReadinessError(
            "Database is stamped at BPM 0.9.6 head but has a partial/incompatible profile shape"
        )
    indexes = {index["name"] for index in inspector.get_indexes("profiles")}
    if not EXPECTED_PROFILE_INDEXES <= indexes:
        raise DatabaseReadinessError(
            "Database is stamped at BPM 0.9.6 head but is missing required profile indexes"
        )


def _normalize_database_url(url: str, *, root_dir: Path | None = None) -> str:
    """
    Resolve some file-based SQLite URLs against the project root.

    Explicit relative paths such as `./data/bpm.db` should remain untouched so
    local bootstrap expectations and tests can observe the configured URL as-is.
    We only normalize bare relative paths that do not already declare their
    filesystem intent.
    """
    if url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    if not url.startswith("sqlite+aiosqlite:///") or ":memory:" in url:
        return url

    prefix, _, raw_path = url.partition(":///")
    if not raw_path:
        return url

    path = Path(raw_path)
    if path.is_absolute() or raw_path.startswith(("./", "../")):
        return url

    resolved_path = ((root_dir or get_settings().ROOT_DIR) / path).resolve()
    return f"{prefix}:///{resolved_path}"


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


class DatabaseRuntime:
    """Own one application's native async database engine and sessions."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        database_url: str | None = None,
        echo: bool | None = None,
    ) -> None:
        configured = settings or get_settings()
        self.database_url = cast(
            str,
            _normalize_database_url(
                database_url or configured.DATABASE_URL,
                root_dir=configured.ROOT_DIR,
            ),
        )
        self.echo = configured.DB_ECHO if echo is None else echo
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._initialized = False
        self._schema_ready = False
        self._lifecycle_lock = asyncio.Lock()

    @property
    def engine(self) -> AsyncEngine | None:
        return self._engine

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def schema_ready(self) -> bool:
        return self._initialized and self._schema_ready

    def _ensure_engine(self) -> AsyncEngine:
        if self._engine is None:
            _ensure_sqlite_parent_dir(self.database_url)
            self._engine = create_async_engine(self.database_url, echo=self.echo)
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
            )
        return self._engine

    async def init(self) -> None:
        """Open one runtime engine; Alembic exclusively owns schema and data upgrades."""
        if self._initialized:
            return
        async with self._lifecycle_lock:
            if self._initialized:
                return
            engine = self._ensure_engine()
            try:
                async with engine.connect() as connection:
                    await connection.exec_driver_sql("SELECT 1")
            except BaseException:
                await engine.dispose()
                self._engine = None
                self._session_factory = None
                raise
            self._initialized = True

    async def verify_release_schema(self) -> None:
        """Fail closed unless this runtime points to the exact release database head."""
        engine = self._engine
        if not self._initialized or engine is None:
            raise RuntimeError("Database runtime must be initialized before readiness verification")
        self._schema_ready = False
        async with engine.connect() as connection:
            await connection.run_sync(_assert_release_schema_ready)
        self._schema_ready = True

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a request-scoped native AsyncSession after lifecycle readiness."""
        session_factory = self._session_factory
        if not self._initialized or session_factory is None:
            raise RuntimeError(
                "Database runtime is not initialized; enter the application lifespan first"
            )
        async with session_factory() as session:
            yield session

    async def dispose(self) -> None:
        """Close all owned connections; the runtime may be initialized again later."""
        async with self._lifecycle_lock:
            engine = self._engine
            self._engine = None
            self._session_factory = None
            self._initialized = False
            self._schema_ready = False
            if engine is not None:
                await engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency backed by the requesting application's runtime."""
    runtime = cast(DatabaseRuntime, request.app.state.database_runtime)
    async with runtime.session() as session:
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise
