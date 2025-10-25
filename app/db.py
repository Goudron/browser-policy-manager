# app/db.py
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .core.config import get_settings
from .models.policy import Base

settings = get_settings()

# --- Берём URL базы из Settings ---
db_url: str = settings.DATABASE_URL

# --- Создание асинхронного движка ---
engine: AsyncEngine = create_async_engine(
    db_url,
    echo=settings.ECHO_SQL,
    future=True,
)

# --- Фабрика сессий ---
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

_initialized: bool = False


async def init_db() -> None:
    """Создаёт таблицы, если их ещё нет."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _ensure_initialized() -> None:
    """Гарантирует, что init_db() вызван один раз."""
    global _initialized
    if not _initialized:
        await init_db()
        _initialized = True


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI — возвращает готовую асинхронную сессию."""
    await _ensure_initialized()
    async with SessionLocal() as session:
        yield session


def init_db_sync() -> None:  # pragma: no cover
    """Утилита для ручного вызова в консоли."""
    asyncio.run(init_db())
