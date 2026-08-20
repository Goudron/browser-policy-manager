from __future__ import annotations

import hashlib
from itertools import permutations
from typing import Any

import pytest
from fastapi import status

from app.compliance.firefox.cis.generation import build_cis_layer
from app.compliance.firefox.cis.merge import merge_base_with_cis_layer
from app.core.profile_conversion_json import canonical_json
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.main import app, create_app
from app.services import profile_service
from tests.support import make_test_client


def _create_profile(
    client,
    *,
    name: str,
    schema_version: str,
    flags: dict[str, Any] | None = None,
    compliance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/profiles",
        json={
            "name": name,
            "schema_version": schema_version,
            "flags": flags or {},
            "compliance": compliance,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _preview(client, profile_id: int, target_artifact_id: str) -> dict[str, Any]:
    response = client.post(
        f"/api/profiles/{profile_id}/conversion-preview",
        json={"target_artifact_id": target_artifact_id},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


def _apply_payload(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "profile-conversion-apply-request",
        "contract_version": 1,
        "profile_id": preview["profile"]["id"],
        "expected_revision": preview["profile"]["revision"],
        "source": {
            "line_id": preview["source"]["artifact"]["line_id"],
            "artifact_id": preview["source"]["artifact"]["artifact_id"],
        },
        "target": {
            "line_id": preview["target"]["artifact"]["line_id"],
            "artifact_id": preview["target"]["artifact"]["artifact_id"],
        },
        "target_artifact_id": preview["target"]["artifact"]["artifact_id"],
        "plan_digest": preview["plan_digest"],
        "source_document_digest": preview["source"]["document_digest"],
        "source_compliance_digest": preview["source"]["compliance_digest"],
        "source_metadata_digest": preview["profile"]["metadata_digest"],
        "source_validation_schema_sha256": preview["source"]["artifact"][
            "validation_schema_sha256"
        ],
        "target_validation_schema_sha256": preview["target"]["artifact"][
            "validation_schema_sha256"
        ],
        "recipe_registry_version": preview["recipe_registry"]["registry_version"],
        "recipe_registry_digest": preview["recipe_registry"]["registry_digest"],
    }


def _assert_error(response, *, status_code: int, code: str, retry_preview_required: bool = False):
    assert response.status_code == status_code, response.text
    detail = response.json()["detail"]
    assert detail["kind"] == "profile-conversion-error"
    assert detail["contract_version"] == 1
    assert detail["code"] == code
    assert detail["http_status"] == status_code
    assert detail["mutation"] == "none"
    assert detail["retry_preview_required"] is retry_preview_required
    return detail


def test_conversion_apply_rederives_current_plan_and_updates_only_owned_fields():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply exact current",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True, "Proxy": {"Mode": "none"}},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        preview = _preview(client, profile["id"], "esr-153.0")
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_200_OK, response.text
    result = response.json()
    assert result["status"] == "applied"
    assert result["profile_id"] == profile["id"]
    assert result["source_revision"] == before["revision"]
    assert result["result_revision"] == before["revision"] + 1
    assert result["source"] == {"line_id": "esr-140", "artifact_id": "esr-140.13"}
    assert result["target"] == {"line_id": "esr-153", "artifact_id": "esr-153.0"}
    assert result["plan_digest"] == preview["plan_digest"]
    assert result["target_validation"]["status"] == "valid"
    assert result["compliance"]["disposition"] == "absent"
    assert after["schema_version"] == "esr-153.0"
    assert after["flags"] == before["flags"]
    assert after["compliance"] is None
    assert after["revision"] == before["revision"] + 1
    assert result["field_accounting"]["updated_at_changed"] is (
        after["updated_at"] != before["updated_at"]
    )
    for field in ("id", "name", "description", "created_at", "deleted_at"):
        assert after[field] == before[field]


def test_conversion_apply_rejects_stale_retry_and_never_accepts_client_candidates():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply stale retry",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        preview = _preview(client, profile["id"], "esr-153.0")
        payload = _apply_payload(preview)
        applied = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
        after_success = client.get(f"/api/profiles/{profile['id']}").json()
        replay = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
        after_replay = client.get(f"/api/profiles/{profile['id']}").json()
        invalid = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json={**payload, "flags": {"SecretPolicy": "must-not-echo"}},
        )

    assert applied.status_code == status.HTTP_200_OK, applied.text
    detail = _assert_error(
        replay,
        status_code=409,
        code="conversion_revision_stale",
        retry_preview_required=True,
    )
    assert detail["expected_revision"] == payload["expected_revision"]
    assert detail["current_revision"] == payload["expected_revision"] + 1
    assert after_replay == after_success
    _assert_error(invalid, status_code=422, code="conversion_apply_request_invalid")
    assert "must-not-echo" not in invalid.text


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda payload: payload.__setitem__("plan_digest", "f" * 64), "conversion_plan_stale"),
        (
            lambda payload: payload["target"].__setitem__("line_id", "esr-140"),
            "conversion_schema_identity_stale",
        ),
        (
            lambda payload: payload["source"].__setitem__("artifact_id", "esr-115.39"),
            "conversion_schema_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("target_artifact_id", "release-153"),
            "conversion_schema_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("recipe_registry_digest", "e" * 64),
            "conversion_recipe_registry_stale",
        ),
        (
            lambda payload: payload.__setitem__("source_document_digest", "d" * 64),
            "conversion_source_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("source_compliance_digest", "c" * 64),
            "conversion_source_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("source_metadata_digest", "b" * 64),
            "conversion_source_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("source_validation_schema_sha256", "a" * 64),
            "conversion_schema_identity_stale",
        ),
        (
            lambda payload: payload.__setitem__("target_validation_schema_sha256", "9" * 64),
            "conversion_schema_identity_stale",
        ),
    ],
)
def test_conversion_apply_rejects_each_preview_identity_mismatch_without_writing(mutate, code):
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name=f"Apply identity {code}",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        payload = _apply_payload(_preview(client, profile["id"], "esr-153.0"))
        mutate(payload)
        response = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _assert_error(response, status_code=409, code=code, retry_preview_required=True)
    assert after == before


def test_conversion_apply_blocks_target_invalid_plan_and_preserves_full_row():
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply blocked",
            schema_version="esr-153.0",
            flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        preview = _preview(client, profile["id"], "esr-115.39")
        assert preview["compatibility"]["applicable"] is False
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _assert_error(response, status_code=409, code="conversion_plan_blocked")
    assert after == before


@pytest.mark.parametrize(
    ("target", "line_id", "code"),
    [
        ("esr-140.13", "esr-140", "conversion_target_identical"),
        ("esr-154.0", "esr-154", "schema_channel_unknown"),
    ],
)
def test_conversion_apply_rejects_current_target_preconditions_without_writing(
    target,
    line_id,
    code,
):
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name=f"Apply target precondition {code}",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        payload = _apply_payload(_preview(client, profile["id"], "esr-153.0"))
        payload["target"] = {"line_id": line_id, "artifact_id": target}
        payload["target_artifact_id"] = target
        response = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _assert_error(response, status_code=422, code=code)
    assert after == before


def test_conversion_apply_invalidates_opaque_compliance_but_preserves_it_as_evidence():
    opaque = {"operator_note": "retain opaque evidence", "nested": {"answer": 42}}
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply opaque compliance",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
            compliance=opaque,
        )
        preview = _preview(client, profile["id"], "esr-153.0")
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        stored = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["compliance"]["disposition"] == "invalidated-preserved"
    assert stored["compliance"]["status"] == "invalidated"
    assert stored["compliance"]["current_claims"] is False
    assert stored["compliance"]["preserved_source"] == opaque


def _cis_envelope(
    *, artifact_id: str, base_policies: dict[str, Any], level: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    layer = build_cis_layer(level, artifact_id)
    merge = merge_base_with_cis_layer(base_policies, layer)
    decisions = []
    for decision in merge.decisions:
        decisions.append(
            {
                "path": list(decision.path),
                "decision": decision.decision,
                "selected_source": decision.selected_source,
                "recommendation_ids": list(decision.recommendation_ids),
                "review_required": decision.review_required,
                "reason": decision.reason,
            }
        )
    decisions[0]["exception_note"] = "preserve reviewed exception note"
    return (
        merge.effective_policies,
        {
            "schema_version": 1,
            "status": "current",
            "framework": "cis",
            "benchmark_id": layer.benchmark_id,
            "benchmark_version": layer.upstream_version,
            "layer": f"cis_l{level}",
            "artifact_id": artifact_id,
            "cis_artifact_digest": hashlib.sha256(canonical_json(layer.to_document())).hexdigest(),
            "base_policies": base_policies,
            "summary": merge.summary,
            "decisions": decisions,
            "current_claims": True,
        },
    )


def test_conversion_apply_recomputes_only_complete_pinned_cis_envelope():
    flags, compliance = _cis_envelope(
        artifact_id="esr-140.13",
        base_policies={"DisableTelemetry": True},
        level=1,
    )
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply pinned CIS evidence",
            schema_version="esr-140.13",
            flags=flags,
            compliance=compliance,
        )
        preview = _preview(client, profile["id"], "esr-153.0")
        assert preview["compliance"]["disposition"] == "recomputed"
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        stored = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_200_OK, response.text
    result = response.json()
    assert result["compliance"]["disposition"] == "recomputed"
    assert result["compliance"]["target_claims_current"] is True
    assert (
        result["compliance"]["target_cis_artifact_digest"]
        == stored["compliance"]["cis_artifact_digest"]
    )
    assert stored["compliance"]["artifact_id"] == "esr-153.0"
    assert (
        stored["compliance"]["decisions"][0]["exception_note"] == "preserve reviewed exception note"
    )


@pytest.mark.parametrize("source,target", tuple(permutations(SUPPORTED_SCHEMA_CHANNELS, 2)))
def test_conversion_apply_handles_every_current_non_self_pair_for_empty_profiles(source, target):
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name=f"Apply pair {source} to {target}",
            schema_version=source,
        )
        preview = _preview(client, profile["id"], target)
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["result_revision"] == profile["revision"] + 1
    assert after["schema_version"] == target
    assert after["flags"] == {}


def test_conversion_apply_rolls_back_an_injected_post_write_failure(monkeypatch):
    original_apply = profile_service.ProfileService.apply_conversion

    async def fail_after_write(session, profile_id, request, *, compliance_replanner=None):
        await original_apply(
            session,
            profile_id,
            request,
            compliance_replanner=compliance_replanner,
        )
        raise RuntimeError("injected conversion write failure")

    monkeypatch.setattr(profile_service.ProfileService, "apply_conversion", fail_after_write)
    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply rollback injected",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = client.get(f"/api/profiles/{profile['id']}").json()
        response = client.post(
            f"/api/profiles/{profile['id']}/conversion-apply",
            json=_apply_payload(_preview(client, profile["id"], "esr-153.0")),
        )
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _assert_error(response, status_code=500, code="conversion_apply_failed")
    assert after == before


def test_conversion_apply_rolls_back_an_unexpected_planner_exception(monkeypatch):
    def raise_unexpected(*args, **kwargs):
        raise ValueError("injected planner failure")

    with make_test_client(app) as client:
        profile = _create_profile(
            client,
            name="Apply planner exception",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        payload = _apply_payload(_preview(client, profile["id"], "esr-153.0"))
        before = client.get(f"/api/profiles/{profile['id']}").json()
        monkeypatch.setattr(profile_service, "plan_profile_conversion", raise_unexpected)
        response = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
        after = client.get(f"/api/profiles/{profile['id']}").json()

    _assert_error(response, status_code=500, code="conversion_apply_failed")
    assert after == before


def test_conversion_apply_openapi_and_security_keep_the_value_free_boundary():
    operation = create_app().openapi()["paths"]["/api/profiles/{profile_id}/conversion-apply"][
        "post"
    ]
    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]

    assert operation["summary"] == "Apply Firefox schema conversion"
    assert set(operation["responses"]) == {"200", "404", "409", "422", "500", "503"}
    assert request_schema["additionalProperties"] is False
    assert "flags" not in request_schema["properties"]
    assert "compliance" not in request_schema["properties"]
    assert "target_artifact_id" in request_schema["required"]

    with make_test_client(app) as client:
        response = client.post("/api/profiles/999999/conversion-apply", json={"secret": "no echo"})

    _assert_error(response, status_code=422, code="conversion_apply_request_invalid")
    assert "no echo" not in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
