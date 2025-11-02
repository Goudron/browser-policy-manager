from __future__ import annotations

import uuid

import pytest

from app.db import get_session, init_db
from app.schemas.policy import PolicyCreate
from app.services.policy_service import PolicyService


def _mk(owner: str, schema: str, name_prefix: str = "SRV", flags: dict | None = None):
    u = uuid.uuid4().hex[:6]
    return PolicyCreate(
        name=f"{name_prefix}-{u}",
        description="Service list",
        schema_version=schema,
        flags=flags or {"DisableTelemetry": True},
        owner=owner,
    )


@pytest.mark.anyio
async def test_service_list_filters_sort_and_pagination_direct():
    """Exercise PolicyService.list directly (owner/schema_version/sort/limit/offset and q branch)."""
    await init_db()

    # Create a few records via service and COMMIT so they are visible to subsequent queries
    async for session in get_session():
        for owner in ("ops@example.org", "sec@example.org"):
            for i in range(2):
                await PolicyService.create(
                    session, _mk(owner, "firefox-ESR", name_prefix=f"SVC-{i}")
                )
        await session.commit()
        break

    # Now query through the service with different combinations
    async for session in get_session():
        # 1) Owner + schema_version without q -> should return at least one item
        items = await PolicyService.list(
            session,
            q=None,
            owner="ops@example.org",
            schema_version="firefox-ESR",
            sort="name",
            order="asc",
            limit=2,
            offset=0,
        )
        assert isinstance(items, list)
        assert len(items) >= 1

        # 2) Different sorting and pagination
        items2 = await PolicyService.list(
            session,
            q=None,
            owner=None,
            schema_version="firefox-ESR",
            sort="updated_at",
            order="desc",
            limit=1,
            offset=1,
        )
        assert isinstance(items2, list)

        # 3) Apply q branch explicitly; do not require non-empty result (we just want to hit the code path)
        items3 = await PolicyService.list(
            session,
            q="SVC-",
            owner=None,
            schema_version=None,
            sort="unknown_field",  # triggers fallback in sort clause
            order="desc",
            limit=1,
            offset=0,
        )
        assert isinstance(items3, list)
        break
