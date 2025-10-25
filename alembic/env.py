# alembic/env.py
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from typing import Any, Optional

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Project imports
from app.models.policy import Base

try:
    from app.core.config import get_settings  # our pydantic settings factory
except Exception:
    get_settings = None  # fallback if import fails

# Alembic Config
config = context.config

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def _pick_database_url() -> str:
    """
    Try to resolve an async DB URL from settings/env with several common names.
    Fallback to sqlite+aiosqlite:///bpm.db.
    """
    # 1) environment overrides (useful for CI/containers)
    env_candidates = [
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URL",
        "DB_URL",
    ]
    for key in env_candidates:
        val = os.getenv(key)
        if val:
            return _ensure_async_sqlite(val)

    # 2) settings object (pydantic)
    settings_obj: Optional[Any] = None
    if get_settings is not None:
        try:
            settings_obj = get_settings()
        except Exception:
            settings_obj = None

    if settings_obj is not None:
        attr_candidates = [
            "database_url",
            "DATABASE_URL",
            "db_url",
            "SQLALCHEMY_DATABASE_URL",
            "sqlalchemy_database_uri",
        ]
        for attr in attr_candidates:
            if hasattr(settings_obj, attr):
                val = getattr(settings_obj, attr)
                if isinstance(val, str) and val:
                    return _ensure_async_sqlite(val)

    # 3) alembic.ini default (may be sync, we’ll convert if needed)
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return _ensure_async_sqlite(ini_url)

    # 4) final fallback
    return "sqlite+aiosqlite:///bpm.db"


def _ensure_async_sqlite(url: str) -> str:
    """
    If URL is SQLite but not async, convert to sqlite+aiosqlite.
    Otherwise return as is.
    """
    # Normalize common sync DSNs:
    if url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
        return "sqlite+aiosqlite://" + url[len("sqlite://") :]
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        # cover sqlite:///:memory: etc.
        return "sqlite+aiosqlite" + url[len("sqlite") :]
    return url


# Resolve and inject URL into alembic config
DATABASE_URL = _pick_database_url()
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations_sync(connection: Connection) -> None:
    """Synchronous body executed within an async connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using AsyncEngine."""
    connectable: AsyncEngine = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        future=True,
    )
    async with connectable.connect() as async_conn:
        await async_conn.run_sync(_run_migrations_sync)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
