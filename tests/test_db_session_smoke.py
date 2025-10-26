from __future__ import annotations

import pytest

from app.db import get_session, init_db


@pytest.mark.anyio
async def test_db_session_context_manager_smoke():
    # Ensure DB is initialized (idempotent)
    await init_db()

    # Use the dependency to open/close a session; do simple no-op
    async for session in get_session():
        # session is an AsyncSession; perform a trivial SQL round-trip if needed
        # Avoid engine-specific raw SQL; just ensure object exists
        assert session is not None
        break  # one iteration is enough
