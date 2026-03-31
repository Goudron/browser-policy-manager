from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# If your project has a declarative Base, you can import its metadata here:
# from app.db_models import Base
# target_metadata = Base.metadata
target_metadata = None  # We do not use autogeneration in this project.

# Alembic configuration
config = context.config

# Logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


LEGACY_REVISION_ALIASES = {
    "5cb73fdb68ed": "20251022_init_profiles",
    "20251026_add_deleted_at": "20251026_add_deleted_at_profiles",
    "20260323_rename_profiles": "20260323_normalize_profiles",
}


# Read the URL ONLY from alembic.ini / injected Config
# (tests set it via set_main_option).
def get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        # Last resort: environment variable for local runs.
        url = os.environ.get("ALEMBIC_SQLALCHEMY_URL", "")
    if not url:
        raise RuntimeError("SQLAlchemy URL is not configured for Alembic")
    return url


def run_migrations_offline() -> None:
    """Run migrations in offline mode (generate SQL without connecting)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Shared migration runner for an active connection."""
    _rewrite_legacy_alembic_versions(connection)
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _rewrite_legacy_alembic_versions(connection: Connection) -> None:
    """
    Rewrite old local revision ids to the current canonical names.

    This keeps existing development databases upgradeable after we cleaned up
    the revision constants to profile-oriented names.
    """
    inspector = connection.dialect.has_table(connection, "alembic_version")
    if not inspector:
        return

    rows = connection.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    if not rows:
        return

    for (version_num,) in rows:
        target = LEGACY_REVISION_ALIASES.get(version_num)
        if target is None:
            continue
        connection.execute(
            text(
                """
                UPDATE alembic_version
                SET version_num = :target
                WHERE version_num = :current
                """
            ),
            {"target": target, "current": version_num},
        )


def run_migrations_online_sync() -> None:
    """Synchronous engine path (sqlite+pysqlite, etc.)."""
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        do_run_migrations(connection)
        if connection.in_transaction():
            connection.commit()
    connectable.dispose()


async def run_migrations_online_async() -> None:
    """Asynchronous engine path (sqlite+aiosqlite, postgresql+asyncpg, etc.)."""
    url = get_url()
    connectable: AsyncEngine = create_async_engine(url, poolclass=pool.NullPool, future=True)
    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)
        if async_connection.in_transaction():
            await async_connection.commit()
    await connectable.dispose()


def run_migrations_online() -> None:
    """Choose sync or async mode based on the URL scheme."""
    url = get_url()
    if "+aiosqlite" in url or "+asyncpg" in url or url.startswith("postgresql+"):
        # Rough heuristic: use async path when the driver is async.
        asyncio.run(run_migrations_online_async())
    else:
        run_migrations_online_sync()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
