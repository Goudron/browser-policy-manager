# app/db.py
from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import Base so we can create all tables on startup
from app.models.policy import Base  # noqa: F401

# --- Configuration ----------------------------------------------------------
# Use env var if provided, otherwise local sqlite file in project root.
DATABASE_URL = os.getenv("BPM_DATABASE_URL", "sqlite+aiosqlite:///./bpm.db")

# Create async engine (aiosqlite driver for SQLite)
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- FastAPI dependency -----------------------------------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession per-request. Closes automatically."""
    async with AsyncSessionLocal() as session:
        yield session


# --- App startup helper -----------------------------------------------------
async def init_db() -> None:
    """
    Create DB schema if it doesn't exist (useful for dev/test).
    In production, prefer Alembic migrations.
    """
    # Import here to ensure models are registered on Base.metadata
    from app.models import policy as _  # noqa: F401

    async with engine.begin() as conn:
        # Run sync DDL in async context
        await conn.run_sync(Base.metadata.create_all)
