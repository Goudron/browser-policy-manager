from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.profile_baseline_provenance import CONTRACT_ID, CONTRACT_VERSION
from app.models.profile import Base, Profile
from app.schemas.profile import ProfileUpdate
from app.services.profile_service import ProfileService
from tests.support import make_test_client
from tests.sync_session_adapter import SyncSessionAdapter


def _digest(character: str) -> str:
    return character * 64


def _verified_catalog_envelope() -> dict:
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "lineage": {
            "kind": "prepared",
            "source_profile_id": None,
            "source_revision": None,
            "plan_digest": None,
        },
        "starter": {
            "identity_state": "catalog",
            "catalog_id": "starter-security",
            "catalog_version": "1",
            "preset_id": "basic_corporate",
            "definition_sha256": _digest("a"),
            "resolved_schema_artifact_id": "release-153",
            "disposition": "created",
        },
        "cis": {
            "identity_state": "catalog",
            "catalog_id": "cis-firefox",
            "catalog_version": "1",
            "baseline_id": "cis-l1",
            "benchmark_id": "cis-firefox-benchmark",
            "benchmark_version": "1.0",
            "layer_sha256": _digest("b"),
            "merge_rules_sha256": _digest("c"),
            "merge_result_sha256": _digest("d"),
            "resolved_schema_artifact_id": "release-153",
            "proof_digest": _digest("e"),
            "display_status": "verified",
            "current_claim": True,
            "reason_code": None,
        },
    }


@pytest.fixture
def service_session() -> SyncSessionAdapter:
    engine = create_engine("sqlite:///:memory:", future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session: Session = session_factory()
    try:
        yield SyncSessionAdapter(session)
    finally:
        session.close()
        engine.dispose()


def _assert_custom_imported_manual_review(provenance: dict, *, lineage_kind: str) -> None:
    assert provenance["lineage"]["kind"] == lineage_kind
    assert provenance["starter"] == {
        "identity_state": "custom-imported",
        "catalog_id": None,
        "catalog_version": None,
        "preset_id": None,
        "definition_sha256": None,
        "resolved_schema_artifact_id": None,
        "disposition": "custom-imported",
    }
    assert provenance["cis"]["identity_state"] == "custom-imported"
    assert provenance["cis"]["display_status"] == "manual-review"
    assert provenance["cis"]["current_claim"] is False
    assert provenance["cis"]["reason_code"] == "cis_provenance_unknown"


def test_generic_create_and_firefox_import_do_not_accept_caller_provenance_authority():
    generic_name = f"generic-provenance-{uuid.uuid4().hex}"
    import_name = f"import-provenance-{uuid.uuid4().hex}"
    supplied = _verified_catalog_envelope()

    with make_test_client() as client:
        generic = client.post(
            "/api/profiles",
            json={
                "name": generic_name,
                "schema_version": "release-153",
                "flags": {"DisableTelemetry": True},
                "compliance": {"claim": "untrusted"},
                "baseline_provenance": supplied,
                "baseline_display": {"cis": {"display_status": "verified"}},
            },
        )
        assert generic.status_code == 201, generic.text
        generic_payload = generic.json()

        imported = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": import_name,
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
                "compliance": {"claim": "also-untrusted"},
                "baseline_provenance": supplied,
            },
        )
        assert imported.status_code == 201, imported.text
        import_payload = imported.json()

    _assert_custom_imported_manual_review(
        generic_payload["baseline_provenance"],
        lineage_kind="generic-create",
    )
    _assert_custom_imported_manual_review(
        import_payload["baseline_provenance"],
        lineage_kind="firefox-import",
    )
    assert generic_payload["baseline_display"] == {
        "starter": {"identity_state": "custom-imported", "availability": "not-applicable"},
        "cis": {
            "identity_state": "custom-imported",
            "display_status": "manual-review",
            "current_claim": False,
            "reason_code": "cis_provenance_unknown",
        },
    }


@pytest.mark.anyio
async def test_generic_policy_or_compliance_edit_demotes_verified_cis_without_inference(
    service_session: SyncSessionAdapter,
):
    profile = Profile(
        name=f"verified-provenance-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"DisableTelemetry": True},
        baseline_provenance=_verified_catalog_envelope(),
    )
    service_session.add(profile)
    await service_session.commit()

    updated = await ProfileService.update(
        service_session,
        profile.id,
        ProfileUpdate(compliance={"operator_note": "manual edit"}),
    )
    assert updated is not None
    cis = updated.baseline_provenance["cis"]
    assert cis["identity_state"] == "catalog"
    assert cis["baseline_id"] == "cis-l1"
    assert cis["display_status"] == "manual-review"
    assert cis["current_claim"] is False
    assert cis["reason_code"] == "profile_payload_modified"


def test_malformed_stored_envelope_fails_closed_without_inspecting_profile_flags():
    engine = create_engine("sqlite:///:memory:", future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    profile = Profile(
        name=f"malformed-provenance-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"DisableTelemetry": True},
        compliance={"benchmark": "recognizable-but-not-proof"},
        baseline_provenance={"starter": {"identity_state": "catalog"}},
    )
    session: Session = session_factory()
    try:
        session.add(profile)
        session.flush()
        read = ProfileService._as_read_model(profile)
        assert read.baseline_display == {
            "starter": {"identity_state": "unavailable", "availability": "unavailable"},
            "cis": {
                "identity_state": "unavailable",
                "display_status": "manual-review",
                "current_claim": False,
                "reason_code": "baseline_provenance_unavailable",
            },
        }
    finally:
        session.close()
        engine.dispose()


def test_catalog_preset_identity_and_preserved_disposition_serialize_without_flag_inference():
    envelope = _verified_catalog_envelope()
    envelope["starter"]["disposition"] = "preserved"
    profile = Profile(
        name=f"stored-preset-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"DisableTelemetry": False},
        baseline_provenance=envelope,
    )
    profile.id = 1
    profile.revision = 1
    profile.created_at = datetime.now(UTC)
    profile.updated_at = profile.created_at

    read = ProfileService._as_read_model(profile)

    assert read.baseline_display["starter"] == {
        "identity_state": "catalog",
        "catalog_id": "starter-security",
        "catalog_version": "1",
        "preset_id": "basic_corporate",
        "disposition": "preserved",
        "availability": "unavailable",
    }


def test_legacy_catalog_envelope_without_preset_id_remains_noninferential():
    envelope = _verified_catalog_envelope()
    del envelope["starter"]["preset_id"]
    profile = Profile(
        name=f"legacy-preset-{uuid.uuid4().hex}",
        schema_version="release-153",
        flags={"DisableTelemetry": True},
        baseline_provenance=envelope,
    )
    profile.id = 1
    profile.revision = 1
    profile.created_at = datetime.now(UTC)
    profile.updated_at = profile.created_at

    read = ProfileService._as_read_model(profile)

    assert read.baseline_display["starter"] == {
        "identity_state": "catalog",
        "catalog_id": "starter-security",
        "catalog_version": "1",
        "availability": "unavailable",
        "disposition": "created",
        "reason_code": "starter_preset_identity_unavailable",
    }
