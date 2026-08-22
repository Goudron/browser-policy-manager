from __future__ import annotations

import uuid
from dataclasses import replace

from fastapi import status

from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.services import profile_service
from tests.support import make_test_client

PREPARE_NEW_PATH = "/api/profiles/prepare/new"


def _payload(**overrides: object) -> dict[str, object]:
    return {
        "name": "Prepared workstations",
        "target_schema_id": "release-153",
        "starter_id": "basic_corporate",
        "cis_baseline_id": "cis_l1",
        "preparation_idempotency_key": uuid.uuid4().hex,
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


def test_prepare_new_profile_creates_one_server_composed_profile_with_provenance() -> None:
    expected = compose_profile_initialization(
        schema_id="release-153",
        preset_id="basic_corporate",
        cis_baseline_id="cis_l1",
    )
    assert expected.is_valid

    with make_test_client() as client:
        response = client.post(PREPARE_NEW_PATH, json=_payload())
        profiles = client.get("/api/profiles")

    assert response.status_code == status.HTTP_201_CREATED, response.text
    created = response.json()
    assert len(profiles.json()) == 1
    assert created["name"] == "Prepared workstations"
    assert created["schema_version"] == "release-153"
    assert created["flags"] == expected.document
    assert created["compliance"] == expected.compliance
    assert created["baseline_provenance"] == expected.baseline_provenance
    assert created["extension_provenance"] == expected.extension_provenance
    assert created["baseline_provenance"]["lineage"]["kind"] == "prepared"
    assert created["baseline_display"]["starter"] == {
        "identity_state": "catalog",
        "catalog_id": "firefox-guided-starter-presets",
        "catalog_version": "1",
        "preset_id": "basic_corporate",
        "disposition": "created",
        "availability": "unavailable",
    }
    assert created["revision"] == 1


def test_prepare_new_profile_rejects_client_composed_fields_without_writing() -> None:
    with make_test_client() as client:
        response = client.post(
            PREPARE_NEW_PATH,
            json=_payload(flags={"DisableTelemetry": False}),
        )
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="preparation_request_invalid",
    )
    assert profiles.json() == []
    assert "DisableTelemetry" not in response.text


def test_prepare_new_profile_rejects_invalid_name_and_catalog_identities_without_writing() -> None:
    cases = (
        (_payload(name="   "), "preparation_request_invalid"),
        (_payload(target_schema_id="unknown-schema"), "preparation_schema_unavailable"),
        (_payload(starter_id="unknown-preset"), "preparation_starter_unavailable"),
        (_payload(cis_baseline_id="unknown-cis"), "preparation_cis_unavailable"),
    )

    with make_test_client() as client:
        for payload, code in cases:
            response = client.post(PREPARE_NEW_PATH, json=payload)
            _assert_preparation_error(
                response,
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code=code,
            )
            assert client.get("/api/profiles").json() == []


def test_prepare_new_profile_rejects_an_invalid_generated_candidate_without_writing(
    monkeypatch,
) -> None:
    valid = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="none",
    )
    assert valid.is_valid
    monkeypatch.setattr(
        profile_service,
        "compose_profile_initialization",
        lambda **_: replace(valid, document=None),
    )

    with make_test_client() as client:
        response = client.post(
            PREPARE_NEW_PATH,
            json=_payload(starter_id="blank", cis_baseline_id="none"),
        )
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="preparation_candidate_invalid",
    )
    assert profiles.json() == []


def test_prepare_new_profile_name_conflict_writes_no_second_row() -> None:
    with make_test_client() as client:
        first = client.post(PREPARE_NEW_PATH, json=_payload())
        duplicate = client.post(PREPARE_NEW_PATH, json=_payload())
        profiles = client.get("/api/profiles")

    assert first.status_code == status.HTTP_201_CREATED, first.text
    _assert_preparation_error(
        duplicate,
        status_code=status.HTTP_409_CONFLICT,
        code="preparation_name_conflict",
    )
    assert [profile["id"] for profile in profiles.json()] == [first.json()["id"]]


def test_prepare_new_profile_same_key_replays_one_result_and_rejects_reuse() -> None:
    with make_test_client() as client:
        payload = _payload()
        first = client.post(PREPARE_NEW_PATH, json=payload)
        replay = client.post(PREPARE_NEW_PATH, json=payload)
        reused = client.post(
            PREPARE_NEW_PATH,
            json={**payload, "name": "Different prepared workstations"},
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
    assert [profile["id"] for profile in profiles.json()] == [first.json()["id"]]


def test_prepare_new_profile_rolls_back_if_a_post_insert_operation_fails(monkeypatch) -> None:
    def fail_read_model(*_args, **_kwargs):
        raise RuntimeError("test post-insert failure")

    monkeypatch.setattr(
        profile_service.ProfileService,
        "_as_read_model",
        staticmethod(fail_read_model),
    )
    with make_test_client() as client:
        response = client.post(PREPARE_NEW_PATH, json=_payload())
        monkeypatch.undo()
        profiles = client.get("/api/profiles")

    _assert_preparation_error(
        response,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="preparation_transaction_failed",
    )
    assert profiles.json() == []
