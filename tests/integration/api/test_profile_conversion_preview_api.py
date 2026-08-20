from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi import status

import app.core.schema_channels as schema_channels
from app.api import profiles as profiles_api
from app.core.profile_conversion_planner import ConversionPlanningError
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG, SUPPORTED_SCHEMA_CHANNELS
from app.main import app, create_app
from tests.support import make_test_client


def _create_profile(client, *, name: str, schema_version: str, flags=None, compliance=None):
    payload = {"name": name, "schema_version": schema_version, "flags": flags or {}}
    if compliance is not None:
        payload["compliance"] = compliance
    response = client.post("/api/profiles", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _error(response, *, status_code: int, code: str):
    assert response.status_code == status_code, response.text
    assert response.json()["detail"] == {
        "kind": "profile-conversion-error",
        "contract_version": 1,
        "code": code,
        "http_status": status_code,
        "profile_id": response.json()["detail"]["profile_id"],
        "expected_revision": None,
        "current_revision": response.json()["detail"]["current_revision"],
        "plan_digest": None,
        "retry_preview_required": False,
        "mutation": "none",
        "parameters": response.json()["detail"]["parameters"],
    }


def test_conversion_preview_is_repeatable_value_free_and_does_not_write_profile():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Preview opaque compliance",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
            compliance={"operator_note": "do-not-disclose"},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()

        first = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        second = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert first.status_code == status.HTTP_200_OK, first.text
    assert second.status_code == status.HTTP_200_OK, second.text
    preview = first.json()
    assert preview == second.json()
    assert preview["available"] is True
    assert preview["profile"]["id"] == profile["id"]
    assert preview["profile"]["revision"] == before["revision"]
    assert preview["source"]["artifact"] == {
        key: preview["source"]["artifact"][key]
        for key in (
            "line_id",
            "artifact_id",
            "channel_id",
            "artifact_version",
            "source_tag",
            "schema_bundle_sha256",
            "validation_schema_sha256",
        )
    }
    assert preview["source"]["artifact"]["artifact_id"] == "esr-140.13"
    assert preview["target"]["artifact"]["artifact_id"] == "esr-153.0"
    assert preview["compatibility"]["applicable"] is True
    assert preview["target_validation"]["status"] == "valid"
    assert preview["compliance"]["disposition"] == "invalidated-preserved"
    assert preview["recipe_registry"]["recipes"] == []
    assert "do-not-disclose" not in first.text
    assert "DisableTelemetry" in {entry["policy_id"] for entry in preview["entries"]}
    assert before == after


@pytest.mark.parametrize("source", SUPPORTED_SCHEMA_CHANNELS)
def test_conversion_preview_plans_every_current_non_self_target_from_server_profile(source):
    with make_test_client(app) as client:
        for target in SUPPORTED_SCHEMA_CHANNELS:
            if target == source:
                continue
            profile = _create_profile(
                client,
                name=f"Preview {source} to {target}",
                schema_version=source,
            )
            response = client.post(
                f"/api/profiles/{profile['id']}/conversion-preview",
                json={"target_artifact_id": target},
            )

            assert response.status_code == status.HTTP_200_OK, response.text
            body = response.json()
            assert body["available"] is True
            assert body["profile"]["revision"] == profile["revision"]
            assert body["source"]["artifact"]["artifact_id"] == source
            assert body["target"]["artifact"]["artifact_id"] == target
            assert body["compatibility"]["applicable"] is True
            assert body["target_validation"] == {
                "status": "valid",
                "validated_document_digest": body["target"]["candidate_document_digest"],
                "validation_schema_sha256": body["target"]["artifact"]["validation_schema_sha256"],
                "issues": [],
            }


def test_conversion_preview_returns_blocked_plan_with_target_validation_without_writing():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Preview blocked",
            schema_version="esr-153.0",
            flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-115.39"},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_200_OK, response.text
    body = response.json()
    assert body["available"] is True
    assert body["compatibility"]["status"] == "blocked"
    assert body["compatibility"]["applicable"] is False
    assert body["compatibility"]["counts"]["blocked"] > 0
    assert body["target_validation"]["status"] == "invalid"
    assert body["target_validation"]["issues"]
    assert body["blockers"]
    assert any(entry["classification"] == "blocked" for entry in body["entries"])
    assert before == after


def test_conversion_preview_errors_are_nonmutating_and_do_not_echo_untrusted_values():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Preview errors",
            schema_version="esr-140.13",
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()

        missing = client.post(
            "/api/profiles/999999/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        unknown = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "not-a-channel"},
        )
        identical = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-140.13"},
        )
        invalid_request = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={
                "target_artifact_id": "esr-153.0",
                "document": {"policies": {"SecretPolicy": "do-not-disclose"}},
            },
        )
        after_preview_errors = client.get(f"/api/profiles/{profile['id']}").json()
        client.delete(f"/api/profiles/{profile['id']}")
        archived_before = client.get(
            f"/api/profiles/{profile['id']}", params={"include_deleted": True}
        ).json()
        inactive = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        archived_after = client.get(
            f"/api/profiles/{profile['id']}", params={"include_deleted": True}
        ).json()

    _error(missing, status_code=404, code="conversion_profile_not_found")
    _error(unknown, status_code=422, code="schema_channel_unknown")
    _error(identical, status_code=422, code="conversion_target_identical")
    _error(invalid_request, status_code=422, code="conversion_preview_request_invalid")
    _error(inactive, status_code=409, code="conversion_source_not_active")
    assert "do-not-disclose" not in invalid_request.text
    assert before == after_preview_errors
    assert archived_before == archived_after


def test_retired_profile_preview_requires_alembic_migration_without_remapping(monkeypatch):
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Preview retired source",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        source = next(
            channel for channel in SCHEMA_CHANNEL_CATALOG if channel.artifact_id == "esr-140.13"
        )
        retired = replace(source, support_state="retired", selectable=False)
        monkeypatch.setattr(
            schema_channels,
            "SCHEMA_CHANNEL_CATALOG",
            tuple(
                retired if channel.artifact_id == retired.artifact_id else channel
                for channel in SCHEMA_CHANNEL_CATALOG
            ),
        )
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _error(
        response,
        status_code=status.HTTP_409_CONFLICT,
        code="schema_channel_retired_requires_migration",
    )
    assert after["schema_version"] == before["schema_version"] == "esr-140.13"
    assert after["flags"] == before["flags"]
    assert after["compliance"] == before["compliance"]
    assert after["revision"] == before["revision"]
    assert after["updated_at"] == before["updated_at"]


def test_existing_profile_schema_patch_requires_conversion_preview_and_does_not_write():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Schema patch requires preview",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        response = client.patch(
            f"/api/profiles/{profile['id']}",
            json={"schema_version": "esr-153.0", "expected_revision": profile["revision"]},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == {
        "message": "Schema conversion preview is required for channel changes",
        "code": "profile_schema_conversion_required",
    }
    assert before == after


def test_empty_profile_schema_patch_requires_conversion_preview_and_does_not_write():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Empty schema patch requires preview",
            schema_version="esr-140.13",
            flags={},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        response = client.patch(
            f"/api/profiles/{profile['id']}",
            json={"schema_version": "esr-153.0", "expected_revision": profile["revision"]},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["code"] == "profile_schema_conversion_required"
    assert before == after


@pytest.mark.parametrize(
    ("planner_code", "expected_status"),
    [
        ("conversion_source_invalid", 422),
        ("conversion_source_schema_missing", 503),
        ("conversion_target_schema_missing", 503),
    ],
)
def test_conversion_preview_maps_planner_preconditions_without_mutation(
    monkeypatch,
    planner_code,
    expected_status,
):
    def fail_planning(*args, **kwargs):
        raise ConversionPlanningError(planner_code)

    monkeypatch.setattr(profiles_api, "plan_profile_conversion", fail_planning)
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name=f"Preview {planner_code}",
            schema_version="esr-140.13",
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-preview",
            json={"target_artifact_id": "esr-153.0"},
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _error(response, status_code=expected_status, code=planner_code)
    assert before == after


@pytest.mark.parametrize(
    ("planner_code", "source_artifact_id", "expected_status"),
    [
        ("schema_channel_unknown", "unknown-stored-artifact", 409),
        ("schema_channel_unknown", "esr-140.13", 422),
        ("schema_channel_retired", "esr-140.13", 422),
        ("schema_channel_retired_requires_migration", "esr-140.13", 409),
        ("conversion_target_unsupported", "esr-140.13", 422),
        ("conversion_target_identical", "esr-140.13", 422),
    ],
)
def test_conversion_preview_status_mapping_covers_lifecycle_and_target_preconditions(
    planner_code,
    source_artifact_id,
    expected_status,
):
    assert (
        profiles_api._conversion_preview_status(
            planner_code,
            source_artifact_id=source_artifact_id,
        )
        == expected_status
    )


def test_conversion_preview_openapi_declares_target_only_body_and_error_envelopes():
    operation = create_app().openapi()["paths"]["/api/profiles/{profile_id}/conversion-preview"][
        "post"
    ]

    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert request_schema["required"] == ["target_artifact_id"]
    assert set(request_schema["properties"]) == {"target_artifact_id"}
    assert request_schema["additionalProperties"] is False
    assert operation["summary"] == "Preview Firefox schema conversion"
    assert set(operation["responses"]) == {"200", "404", "409", "422", "503"}
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ConversionPreviewResponse"
    }
    profile_update = create_app().openapi()["components"]["schemas"]["ProfileUpdate"]
    assert profile_update["properties"]["schema_version"]["deprecated"] is True
    for error_status in ("404", "409", "422", "503"):
        assert operation["responses"][error_status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ConversionPreviewErrorEnvelope"
        }
