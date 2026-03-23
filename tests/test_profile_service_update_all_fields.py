from __future__ import annotations

import uuid

import pytest

from app.db import get_session, init_db
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services.profile_service import ProfileService


def _mk_create_payload() -> ProfileCreate:
    u = uuid.uuid4().hex[:6]
    return ProfileCreate(
        name=f"UPD-{u}",
        description="Original description",
        schema_version="esr-140",
        flags={"DisableTelemetry": True},
        owner="ops@example.org",
    )


@pytest.mark.anyio
async def test_update_all_mutable_fields_and_read_back():
    """Hit all field assignments in ProfileService.update (desc/schema/flags/owner)."""
    await init_db()

    # Create initial entity
    async for session in get_session():
        created = await ProfileService.create(session, _mk_create_payload())
        await session.commit()
        profile_id = created.id
        break

    # Update with all fields set
    patch = ProfileUpdate(
        description="Changed description",
        schema_version="release-145",
        flags={"DisableTelemetry": False, "DisablePrivateBrowsing": True},
        owner="sec@example.org",
    )

    async for session in get_session():
        updated = await ProfileService.update(session, profile_id, patch)
        await session.commit()
        assert updated is not None
        assert updated.description == "Changed description"
        assert updated.schema_version == "release-145"
        assert updated.flags.get("DisableTelemetry") is False
        assert updated.flags.get("DisablePrivateBrowsing") is True
        assert updated.owner == "sec@example.org"
        break

    # Update non-existent id → None branch in update()
    async for session in get_session():
        missing = await ProfileService.update(session, 9_999_999, patch)
        assert missing is None
        break

    # Soft-delete and verify get(include_deleted=False) hides it, True returns it
    async for session in get_session():
        ok = await ProfileService.soft_delete(session, profile_id)
        await session.commit()
        assert ok is True
        break

    async for session in get_session():
        hidden = await ProfileService.get(session, profile_id, include_deleted=False)
        shown = await ProfileService.get(session, profile_id, include_deleted=True)
        assert hidden is None and shown is not None
        break

    # Restore should succeed once, then second restore returns None branch
    async for session in get_session():
        restored = await ProfileService.restore(session, profile_id)
        await session.commit()
        assert restored is not None
        break

    async for session in get_session():
        restored_again = await ProfileService.restore(session, profile_id)
        assert restored_again is None
        break
