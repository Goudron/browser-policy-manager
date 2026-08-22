from __future__ import annotations

import copy
import hashlib
import uuid
from dataclasses import replace

from fastapi import status

from app.compliance.firefox.profile_duplicate_composition import (
    DuplicatePlanningSource,
    plan_profile_duplicate,
)
from app.core.profile_conversion_json import canonical_json
from app.services import profile_service
from tests.support import build_profile_payload, make_test_client

PREPARE_NEW_PATH = "/api/profiles/prepare/new"
PREPARE_DUPLICATE_PATH = "/api/profiles/prepare/duplicate"
PREVIEW_DUPLICATE_PATH = "/api/profiles/prepare/duplicate/preview"


def _new_payload(**overrides: object) -> dict[str, object]:
    return {
        "name": f"Duplicate source {uuid.uuid4().hex}",
        "target_schema_id": "release-153",
        "starter_id": "blank",
        "cis_baseline_id": "none",
        "preparation_idempotency_key": uuid.uuid4().hex,
        **overrides,
    }


def _duplicate_payload(source: dict[str, object], **overrides: object) -> dict[str, object]:
    return {
        "name": f"Duplicate target {uuid.uuid4().hex}",
        "target_schema_id": "release-153",
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "preparation_idempotency_key": uuid.uuid4().hex,
        **overrides,
    }


def _preview_payload(source: dict[str, object], **overrides: object) -> dict[str, object]:
    return {
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "target_schema_id": "release-153",
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
        **overrides,
    }


def _assert_preparation_error(response, *, status_code: int, code: str) -> None:
    assert response.status_code == status_code, response.text
    assert response.json() == {
        "detail": {
            "kind": "profile-preparation-error",
            "contract_version": 1,
            "code": code,
            "i18n_key": f"profiles.preparation_error_{code}",
            "http_status": status_code,
            "mutation": "none",
            "parameters": {},
        }
    }


def _rederive(source: dict[str, object], payload: dict[str, object]):
    return plan_profile_duplicate(
        DuplicatePlanningSource(
            profile_id=source["id"],
            revision=source["revision"],
            lifecycle_state="active",
            schema_artifact_id=source["schema_version"],
            flags=source["flags"],
            compliance=source["compliance"],
            baseline_provenance=source["baseline_provenance"],
            extension_provenance=source["extension_provenance"],
            certificate_provenance=source["certificate_provenance"],
            metadata={
                "name": source["name"],
                "description": source["description"],
                "created_at": source["created_at"],
                "updated_at": source["updated_at"],
                "deleted_at": source["deleted_at"],
            },
        ),
        expected_source_revision=payload["expected_source_revision"],
        target_schema_id=payload["target_schema_id"],
        preset_id=payload["starter_id"],
        cis_baseline_id=payload["cis_baseline_id"],
    )


def _result_digest(profile: dict[str, object], plan: dict[str, object]) -> str:
    return hashlib.sha256(
        b"bpm096-profile-duplicate-result:v1\n"
        + canonical_json(
            {
                "document": profile["flags"],
                "compliance": profile["compliance"],
                "baseline_provenance": profile["baseline_provenance"],
                "extension_provenance": profile["extension_provenance"],
                "certificate_provenance": profile["certificate_provenance"],
                "validation": plan["validation"],
            }
        )
    ).hexdigest()


def _create_source(client, **overrides: object) -> dict[str, object]:
    response = client.post(PREPARE_NEW_PATH, json=_new_payload(**overrides))
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _create_manual_extension_source(client, flags: dict[str, object]) -> dict[str, object]:
    response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name=f"Manual extension source {uuid.uuid4().hex}",
            schema_version="release-153",
            flags=flags,
        ),
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def test_prepare_duplicate_rederives_same_schema_result_and_preserves_source() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        before = copy.deepcopy(source)
        payload = _duplicate_payload(source)
        expected = _rederive(source, payload)
        response = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    assert expected.is_valid
    assert response.status_code == status.HTTP_201_CREATED, response.text
    created = response.json()
    assert created["id"] != source["id"]
    assert created["schema_version"] == payload["target_schema_id"]
    assert created["flags"] == expected.candidate_document
    assert created["compliance"] == expected.candidate_compliance
    assert created["baseline_provenance"] == expected.candidate_baseline_provenance
    assert created["extension_provenance"] == expected.candidate_extension_provenance
    assert created["certificate_provenance"] == expected.candidate_certificate_provenance
    assert _result_digest(created, expected.plan) == expected.plan["result"]["result_digest"]
    assert created["baseline_provenance"]["lineage"]["kind"] == "duplicate"
    assert created["baseline_display"]["starter"] == {
        "identity_state": "catalog",
        "catalog_id": "firefox-guided-starter-presets",
        "catalog_version": "1",
        "preset_id": "blank",
        "disposition": "preserved",
        "availability": "unavailable",
    }
    assert after.json() == before
    assert {profile["id"] for profile in profiles.json()} == {source["id"], created["id"]}


def test_duplicate_preview_is_read_only_for_every_supported_target_schema() -> None:
    supported_schema_ids = ("release-153", "esr-153.0", "esr-140.13", "esr-115.39")
    with make_test_client() as client:
        source = _create_source(client)
        before = copy.deepcopy(source)
        responses = [
            client.post(
                PREVIEW_DUPLICATE_PATH,
                json=_preview_payload(source, target_schema_id=schema_id),
            )
            for schema_id in supported_schema_ids
        ]
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    for response in responses:
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "kind": "profile-duplicate-plan",
            "contract_version": 1,
            "status": "valid",
            "reason_code": None,
            "plan_digest": response.json()["plan_digest"],
        }
        assert len(response.json()["plan_digest"]) == 64
    assert after.json() == before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_duplicate_preview_reports_a_stale_source_without_creating_or_changing_a_profile() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        before = copy.deepcopy(source)
        response = client.post(
            PREVIEW_DUPLICATE_PATH,
            json=_preview_payload(
                source,
                expected_source_revision=source["revision"] + 1,
            ),
        )
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["status"] == "blocked"
    assert response.json()["reason_code"] == "duplicate_source_stale"
    assert after.json() == before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_prepare_duplicate_rederives_cross_schema_result_without_converting_source() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        before = copy.deepcopy(source)
        payload = _duplicate_payload(source, target_schema_id="esr-153.0")
        expected = _rederive(source, payload)
        response = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        after = client.get(f"/api/profiles/{source['id']}")

    assert expected.is_valid
    assert response.status_code == status.HTTP_201_CREATED, response.text
    created = response.json()
    assert created["schema_version"] == "esr-153.0"
    assert created["flags"] == expected.candidate_document
    assert created["compliance"] == expected.candidate_compliance
    assert created["baseline_provenance"] == expected.candidate_baseline_provenance
    assert created["extension_provenance"] == expected.candidate_extension_provenance
    assert created["certificate_provenance"] == expected.candidate_certificate_provenance
    assert _result_digest(created, expected.plan) == expected.plan["result"]["result_digest"]
    assert after.json() == before


def test_cross_schema_duplicate_marks_supported_extension_values_converted() -> None:
    flags = {
        "ExtensionSettings": {
            "addon@example.test": {"installation_mode": "allowed"},
        },
    }
    with make_test_client() as client:
        source = _create_manual_extension_source(client, flags)
        before = copy.deepcopy(source)
        response = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, target_schema_id="esr-153.0"),
        )
        after = client.get(f"/api/profiles/{source['id']}")

    assert response.status_code == status.HTTP_201_CREATED, response.text
    created = response.json()
    assert created["flags"] == flags
    assert set(created["extension_provenance"]["paths"].values()) == {"converted"}
    assert after.json() == before


def test_cross_schema_duplicate_blocks_unsupported_extension_values_without_writing() -> None:
    flags = {
        "ExtensionSettings": {
            "addon@example.test": {"allowed_permissions": ["tabs"]},
        },
    }
    with make_test_client() as client:
        source = _create_manual_extension_source(client, flags)
        before = copy.deepcopy(source)
        response = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, target_schema_id="esr-115.39"),
        )
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_conversion_blocked",
    )
    assert after.json() == before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_cross_schema_duplicate_blocks_unsupported_certificate_values_without_writing() -> None:
    flags = {"MicrosoftEntraSSO": True}
    with make_test_client() as client:
        source = _create_manual_extension_source(client, flags)
        before = copy.deepcopy(source)
        response = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, target_schema_id="esr-115.39"),
        )
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_conversion_blocked",
    )
    assert after.json() == before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_prepare_duplicate_same_key_replays_one_accepted_result_and_rejects_reuse() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        payload = _duplicate_payload(source)
        first = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        replay = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        reused = client.post(
            PREPARE_DUPLICATE_PATH,
            json={**payload, "name": f"different duplicate {uuid.uuid4().hex}"},
        )
        profiles = client.get("/api/profiles")

    assert first.status_code == status.HTTP_201_CREATED, first.text
    assert replay.status_code == status.HTTP_201_CREATED, replay.text
    assert replay.json() == first.json()
    _assert_preparation_error(
        reused,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_idempotency_key_reused",
    )
    assert {profile["id"] for profile in profiles.json()} == {source["id"], first.json()["id"]}


def test_prepare_duplicate_stale_blocked_and_name_conflict_create_no_target() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        source_before = copy.deepcopy(source)
        blocked_source_response = client.post(
            "/api/profiles",
            json={
                "name": f"Blocked duplicate source {uuid.uuid4().hex}",
                "schema_version": "esr-153.0",
                "flags": {"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
            },
        )
        assert blocked_source_response.status_code == status.HTTP_201_CREATED
        blocked_source = blocked_source_response.json()
        blocked_source_before = copy.deepcopy(blocked_source)

        stale = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(
                source,
                expected_source_revision=source["revision"] + 1,
            ),
        )
        blocked = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(blocked_source, target_schema_id="esr-115.39"),
        )
        successful_payload = _duplicate_payload(source)
        successful = client.post(PREPARE_DUPLICATE_PATH, json=successful_payload)
        conflict = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, name=successful_payload["name"]),
        )
        source_after = client.get(f"/api/profiles/{source['id']}")
        blocked_source_after = client.get(f"/api/profiles/{blocked_source['id']}")
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        stale,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_source_stale",
    )
    _assert_preparation_error(
        blocked,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_conversion_blocked",
    )
    assert successful.status_code == status.HTTP_201_CREATED, successful.text
    _assert_preparation_error(
        conflict,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_name_conflict",
    )
    assert source_after.json() == source_before
    assert blocked_source_after.json() == blocked_source_before
    assert {profile["id"] for profile in profiles.json()} == {
        source["id"],
        blocked_source["id"],
        successful.json()["id"],
    }


def test_prepare_duplicate_rolls_back_target_if_read_model_fails(monkeypatch) -> None:
    with make_test_client() as client:
        source = _create_source(client)
        before = copy.deepcopy(source)
        payload = _duplicate_payload(source)

        def fail_read_model(*_args, **_kwargs):
            raise RuntimeError("test duplicate post-insert failure")

        monkeypatch.setattr(
            profile_service.ProfileService,
            "_as_read_model",
            staticmethod(fail_read_model),
        )
        response = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        monkeypatch.undo()
        after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="preparation_transaction_failed",
    )
    assert after.json() == before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_prepare_duplicate_rejects_client_composed_fields_without_writing() -> None:
    with make_test_client() as client:
        source = _create_source(client)
        response = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, flags={"DisableTelemetry": False}),
        )
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="preparation_request_invalid",
    )
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_prepare_duplicate_missing_source_is_404_and_conversion_diagnostic_is_value_safe(
    monkeypatch,
) -> None:
    secret_value = "sensitive-conversion-value-must-not-leak"
    with make_test_client() as client:
        source_response = client.post(
            "/api/profiles",
            json={
                "name": f"Blocked diagnostic source {uuid.uuid4().hex}",
                "schema_version": "esr-153.0",
                "flags": {"HttpAllowlist": [secret_value]},
            },
        )
        assert source_response.status_code == status.HTTP_201_CREATED, source_response.text
        source = source_response.json()
        blocked_payload = _duplicate_payload(source)
        valid_plan = _rederive(source, blocked_payload)
        assert valid_plan.is_valid
        monkeypatch.setattr(
            profile_service,
            "plan_profile_duplicate",
            lambda *_args, **_kwargs: replace(
                valid_plan,
                status="blocked",
                reason_code="duplicate_conversion_blocked",
            ),
        )
        blocked = client.post(
            PREPARE_DUPLICATE_PATH,
            json=blocked_payload,
        )
        monkeypatch.undo()
        missing = client.post(
            PREPARE_DUPLICATE_PATH,
            json=_duplicate_payload(source, source_id=source["id"] + 100_000),
        )
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        blocked,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_conversion_blocked",
    )
    _assert_preparation_error(
        missing,
        status_code=status.HTTP_404_NOT_FOUND,
        code="preparation_duplicate_source_not_found",
    )
    assert secret_value not in blocked.text
    assert secret_value not in missing.text
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]
