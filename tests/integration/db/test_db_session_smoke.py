from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DatabaseRuntime


@pytest.mark.anyio
async def test_db_session_context_manager_smoke(tmp_path):
    runtime = DatabaseRuntime(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'smoke.db'}",
        echo=False,
    )
    try:
        await runtime.init()
        async with runtime.session() as session:
            assert isinstance(session, AsyncSession)
    finally:
        await runtime.dispose()
