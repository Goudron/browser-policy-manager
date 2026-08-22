from __future__ import annotations

import copy
import json
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.models.profile import Base, Profile
from app.services.profile_service import ProfileService
from tests.sync_session_adapter import SyncSessionAdapter


class _ReadOnlySyncSession(SyncSessionAdapter):
    @property
    def no_autoflush(self):
        return self._session.no_autoflush


@pytest.fixture
def service_session() -> _ReadOnlySyncSession:
    engine = create_engine("sqlite:///:memory:", future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session: Session = session_factory()
    try:
        yield _ReadOnlySyncSession(session)
    finally:
        session.close()
        engine.dispose()


def _stored_snapshot(session: _ReadOnlySyncSession, profile_id: int) -> dict:
    profile = session._session.scalars(select(Profile).where(Profile.id == profile_id)).one()
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "schema_version": profile.schema_version,
        "flags": copy.deepcopy(profile.flags),
        "compliance": copy.deepcopy(profile.compliance),
        "baseline_provenance": copy.deepcopy(profile.baseline_provenance),
        "extension_provenance": copy.deepcopy(profile.extension_provenance),
        "revision": profile.revision,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "deleted_at": profile.deleted_at,
    }


@pytest.mark.anyio
async def test_duplicate_planning_is_a_read_only_database_operation(service_session) -> None:
    initialized = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="none",
    )
    assert initialized.is_valid
    assert initialized.document is not None
    assert initialized.baseline_provenance is not None
    assert initialized.extension_provenance is not None
    profile = Profile(
        name=f"duplicate-source-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags=initialized.document,
        compliance=initialized.compliance,
        baseline_provenance=initialized.baseline_provenance,
        extension_provenance=initialized.extension_provenance,
    )
    service_session.add(profile)
    await service_session.commit()
    before = _stored_snapshot(service_session, profile.id)

    result = await ProfileService.plan_duplicate(
        service_session,
        profile.id,
        expected_source_revision=profile.revision,
        target_schema_id="release-153",
        preset_id="keep_current",
        cis_baseline_id="none",
    )
    after = _stored_snapshot(service_session, profile.id)

    assert result is not None and result.is_valid
    assert result.plan["source"]["revision"] == before["revision"]
    assert result.plan["source"]["artifact"]["artifact_id"] == before["schema_version"]
    assert result.plan["validation"]["status"] == "valid"
    assert result.plan["result"]["result_digest"]
    assert not service_session._session.new
    assert not service_session._session.dirty
    assert before == after


@pytest.mark.anyio
async def test_cross_schema_read_only_planning_keeps_source_bytes_and_values_unchanged(
    service_session,
) -> None:
    profile = Profile(
        name=f"cross-duplicate-source-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"HttpAllowlist": ["https://private.example.invalid/source-only"]},
        compliance={"operator_note": "source-only compliance"},
    )
    service_session.add(profile)
    await service_session.commit()
    before = _stored_snapshot(service_session, profile.id)

    result = await ProfileService.plan_duplicate(
        service_session,
        profile.id,
        expected_source_revision=profile.revision,
        target_schema_id="esr-153.0",
        preset_id="keep_current",
        cis_baseline_id="none",
    )
    after = _stored_snapshot(service_session, profile.id)

    assert result is not None and result.is_valid
    assert result.plan["conversion"]["kind"] == "cross-schema"
    assert result.plan["conversion"]["compatibility"]["applicable"] is True
    assert result.plan["source"]["document_digest"]
    assert result.plan["target"]["artifact"]["artifact_id"] == "esr-153.0"
    assert "private.example.invalid" not in json.dumps(result.plan, sort_keys=True)
    assert "source-only compliance" not in json.dumps(result.plan, sort_keys=True)
    assert before == after


@pytest.mark.anyio
async def test_stale_or_missing_source_planning_writes_no_rows(service_session) -> None:
    profile = Profile(
        name=f"stale-duplicate-source-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"DisableTelemetry": True},
    )
    service_session.add(profile)
    await service_session.commit()
    before = _stored_snapshot(service_session, profile.id)

    stale = await ProfileService.plan_duplicate(
        service_session,
        profile.id,
        expected_source_revision=profile.revision + 1,
        target_schema_id="release-153",
        preset_id="keep_current",
        cis_baseline_id="none",
    )
    missing = await ProfileService.plan_duplicate(
        service_session,
        999_999,
        expected_source_revision=1,
        target_schema_id="release-153",
        preset_id="keep_current",
        cis_baseline_id="none",
    )
    after = _stored_snapshot(service_session, profile.id)

    assert stale is not None
    assert stale.reason_code == "duplicate_source_stale"
    assert stale.candidate_document is None
    assert missing is None
    assert before == after
