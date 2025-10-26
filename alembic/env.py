from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Если у вас есть declarative Base в проекте, можно импортировать metadata:
# from app.db_models import Base
# target_metadata = Base.metadata
target_metadata = None  # мы не используем автогенерацию в этом проекте

# Конфигурация Alembic
config = context.config

# Логирование из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Берём URL ТОЛЬКО из alembic.ini / переданного Config (тест вписывает его через set_main_option)
def get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        # последний шанс — переменная окружения (на локалке)
        url = os.environ.get("ALEMBIC_SQLALCHEMY_URL", "")
    if not url:
        raise RuntimeError("SQLAlchemy URL is not configured for Alembic")
    return url


def run_migrations_offline() -> None:
    """Запуск в offline-режиме (генерация SQL без подключения)."""
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
    """Общий запуск миграций при активном соединении."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online_sync() -> None:
    """Синхронный движок (sqlite+pysqlite и т.п.)."""
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


async def run_migrations_online_async() -> None:
    """Асинхронный движок (sqlite+aiosqlite, postgresql+asyncpg и т.п.)."""
    url = get_url()
    connectable: AsyncEngine = create_async_engine(url, poolclass=pool.NullPool, future=True)
    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Выбираем sync/async по схеме URL."""
    url = get_url()
    if "+aiosqlite" in url or "+asyncpg" in url or url.startswith("postgresql+"):
        # грубая эвристика: если драйвер асинхронный — идём через async
        asyncio.run(run_migrations_online_async())
    else:
        run_migrations_online_sync()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
