from __future__ import annotations

import uuid

import pytest

from app.db import get_session, init_db
from app.schemas.policy import PolicyCreate, PolicyUpdate
from app.services.policy_service import PolicyService


def _mk_create_payload() -> PolicyCreate:
    u = uuid.uuid4().hex[:6]
    return PolicyCreate(
        name=f"UPD-{u}",
        description="Original description",
        schema_version="firefox-ESR",
        flags={"DisableTelemetry": True},
        owner="ops@example.org",
    )


@pytest.mark.anyio
async def test_update_all_mutable_fields_and_read_back():
    """Hit all field assignments in PolicyService.update (desc/schema/flags/owner)."""
    await init_db()

    # Create initial entity
    async for session in get_session():
        created = await PolicyService.create(session, _mk_create_payload())
        await session.commit()
        pid = created.id
        break

    # Update with all fields set
    patch = PolicyUpdate(
        description="Changed description",
        schema_version="release-144",
        flags={"DisableTelemetry": False, "DisablePocket": True},
        owner="sec@example.org",
    )

    async for session in get_session():
        updated = await PolicyService.update(session, pid, patch)
        await session.commit()
        assert updated is not None
        assert updated.description == "Changed description"
        assert updated.schema_version == "release-144"
        assert updated.flags.get("DisableTelemetry") is False
        assert updated.flags.get("DisablePocket") is True
        assert updated.owner == "sec@example.org"
        break

    # Update non-existent id → None branch in update()
    async for session in get_session():
        missing = await PolicyService.update(session, 9_999_999, patch)
        assert missing is None
        break

    # Soft-delete and verify get(include_deleted=False) hides it, True returns it
    async for session in get_session():
        ok = await PolicyService.soft_delete(session, pid)
        await session.commit()
        assert ok is True
        break

    async for session in get_session():
        hidden = await PolicyService.get(session, pid, include_deleted=False)
        shown = await PolicyService.get(session, pid, include_deleted=True)
        assert hidden is None and shown is not None
        break

    # Restore should succeed once, then second restore returns None branch
    async for session in get_session():
        restored = await PolicyService.restore(session, pid)
        await session.commit()
        assert restored is not None
        break

    async for session in get_session():
        restored_again = await PolicyService.restore(session, pid)
        assert restored_again is None
        break
