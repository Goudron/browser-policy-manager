from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import AsyncSessionAdapter
from app.models.profile import Base
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services.profile_service import ProfileService


def _mk_create_payload() -> ProfileCreate:
    u = uuid.uuid4().hex[:6]
    return ProfileCreate(
        name=f"UPD-{u}",
        description="Original description",
        schema_version="esr-140.9",
        flags={"DisableTelemetry": True},
        owner="ops@example.org",
    )


@pytest.fixture
def service_session() -> AsyncSessionAdapter:
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    try:
        yield AsyncSessionAdapter(session)
    finally:
        session.close()
        engine.dispose()


@pytest.mark.anyio
async def test_update_all_mutable_fields_and_read_back(service_session: AsyncSessionAdapter):
    """Hit all field assignments in ProfileService.update (desc/schema/flags/owner)."""
    created = await ProfileService.create(service_session, _mk_create_payload())
    await service_session.commit()
    profile_id = created.id

    patch = ProfileUpdate(
        description="Changed description",
        schema_version="release-149",
        flags={"DisableTelemetry": False, "DisablePrivateBrowsing": True},
        owner="sec@example.org",
    )

    updated = await ProfileService.update(service_session, profile_id, patch)
    await service_session.commit()
    assert updated is not None
    assert updated.description == "Changed description"
    assert updated.schema_version == "release-149"
    assert updated.flags.get("DisableTelemetry") is False
    assert updated.flags.get("DisablePrivateBrowsing") is True
    assert updated.owner == "sec@example.org"

    cleared = await ProfileService.update(
        service_session,
        profile_id,
        ProfileUpdate(description=None, owner=None),
    )
    await service_session.commit()
    assert cleared is not None
    assert cleared.description is None
    assert cleared.owner is None

    missing = await ProfileService.update(service_session, 9_999_999, patch)
    assert missing is None

    ok = await ProfileService.soft_delete(service_session, profile_id)
    await service_session.commit()
    assert ok is True

    hidden = await ProfileService.get(service_session, profile_id, include_deleted=False)
    shown = await ProfileService.get(service_session, profile_id, include_deleted=True)
    assert hidden is None and shown is not None

    restored = await ProfileService.restore(service_session, profile_id)
    await service_session.commit()
    assert restored is not None

    restored_again = await ProfileService.restore(service_session, profile_id)
    assert restored_again is None

    deleted = await ProfileService.hard_delete(service_session, profile_id)
    await service_session.commit()
    assert deleted is True

    missing = await ProfileService.get(service_session, profile_id, include_deleted=True)
    deleted_again = await ProfileService.hard_delete(service_session, profile_id)
    assert missing is None
    assert deleted_again is False


@pytest.mark.anyio
async def test_hard_delete_all_profiles_resets_library(service_session: AsyncSessionAdapter):
    await ProfileService.create(service_session, _mk_create_payload())
    await ProfileService.create(service_session, _mk_create_payload())
    await service_session.commit()

    deleted = await ProfileService.hard_delete_all(service_session)
    await service_session.commit()
    assert deleted >= 2

    items = await ProfileService.list(service_session, include_deleted=True, limit=500)
    assert items == []
