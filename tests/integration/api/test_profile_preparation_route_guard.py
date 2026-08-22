"""M4 route-facing guards for preparation failures that have no successful handoff."""

from __future__ import annotations

import copy
import uuid
from dataclasses import replace

from fastapi import status

from app.compliance.firefox.profile_duplicate_composition import (
    DuplicatePlanningSource,
    plan_profile_duplicate,
)
from app.services import profile_service
from tests.support import make_test_client

PREPARE_NEW_PATH = "/api/profiles/prepare/new"
PREPARE_DUPLICATE_PATH = "/api/profiles/prepare/duplicate"


def _new_payload(**overrides: object) -> dict[str, object]:
    return {
        "name": f"M4 guard source {uuid.uuid4().hex}",
        "target_schema_id": "release-153",
        "starter_id": "blank",
        "cis_baseline_id": "none",
        "preparation_idempotency_key": uuid.uuid4().hex,
        **overrides,
    }


def _duplicate_payload(source: dict[str, object], **overrides: object) -> dict[str, object]:
    return {
        "name": f"M4 guard target {uuid.uuid4().hex}",
        "target_schema_id": "release-153",
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "preparation_idempotency_key": uuid.uuid4().hex,
        **overrides,
    }


def _assert_terminal_failure(response, code: str) -> None:
    assert response.status_code == status.HTTP_409_CONFLICT, response.text
    assert response.json()["detail"] == {
        "kind": "profile-preparation-error",
        "contract_version": 1,
        "code": code,
        "i18n_key": f"profiles.preparation_error_{code}",
        "http_status": status.HTTP_409_CONFLICT,
        "mutation": "none",
        "parameters": {},
    }


def _planning_source(profile: dict[str, object]) -> DuplicatePlanningSource:
    return DuplicatePlanningSource(
        profile_id=profile["id"],
        revision=profile["revision"],
        lifecycle_state="active",
        schema_artifact_id=profile["schema_version"],
        flags=profile["flags"],
        compliance=profile["compliance"],
        baseline_provenance=profile["baseline_provenance"],
        metadata={
            key: profile[key]
            for key in ("name", "description", "created_at", "updated_at", "deleted_at")
        },
    )


def test_duplicate_ineligible_source_leaves_only_the_archived_source_row() -> None:
    with make_test_client() as client:
        source_response = client.post(PREPARE_NEW_PATH, json=_new_payload())
        assert source_response.status_code == status.HTTP_201_CREATED, source_response.text
        source = source_response.json()
        assert (
            client.delete(f"/api/profiles/{source['id']}").status_code == status.HTTP_204_NO_CONTENT
        )

        response = client.post(PREPARE_DUPLICATE_PATH, json=_duplicate_payload(source))
        archived = client.get(f"/api/profiles/{source['id']}?include_deleted=true")
        profiles = client.get("/api/profiles?lifecycle=all&sort=id&order=asc")

    _assert_terminal_failure(response, "preparation_duplicate_source_not_eligible")
    assert archived.status_code == status.HTTP_200_OK, archived.text
    assert archived.json()["is_deleted"] is True
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]


def test_duplicate_composition_blocker_keeps_the_source_and_creates_no_navigation_target(
    monkeypatch,
) -> None:
    with make_test_client() as client:
        source_response = client.post(PREPARE_NEW_PATH, json=_new_payload())
        assert source_response.status_code == status.HTTP_201_CREATED, source_response.text
        source = source_response.json()
        source_before = copy.deepcopy(source)
        payload = _duplicate_payload(source)
        valid_plan = plan_profile_duplicate(
            _planning_source(source),
            expected_source_revision=payload["expected_source_revision"],
            target_schema_id=payload["target_schema_id"],
            preset_id=payload["starter_id"],
            cis_baseline_id=payload["cis_baseline_id"],
        )
        assert valid_plan.is_valid
        monkeypatch.setattr(
            profile_service,
            "plan_profile_duplicate",
            lambda *_args, **_kwargs: replace(
                valid_plan,
                status="blocked",
                reason_code="duplicate_preset_composition_blocked",
            ),
        )
        response = client.post(PREPARE_DUPLICATE_PATH, json=payload)
        source_after = client.get(f"/api/profiles/{source['id']}")
        profiles = client.get("/api/profiles?lifecycle=all&sort=id&order=asc")

    _assert_terminal_failure(response, "preparation_composition_blocked")
    assert source_after.json() == source_before
    assert [profile["id"] for profile in profiles.json()] == [source["id"]]
