from __future__ import annotations

import json

import pytest
from fastapi import HTTPException, status

from app.api.profiles import (
    _read_firefox_policies_import_request,
    _validate_import_request_payload,
)
from tests.support import make_test_client


def _import_payload(name: str = "Imported Firefox") -> dict:
    return {
        "name": name,
        "description": "Imported from Firefox policies.json",
        "schema_version": "release-151",
        "document": {
            "policies": {
                "DisableTelemetry": True,
                "BlockAboutConfig": True,
            }
        },
    }


def test_import_firefox_policies_json_creates_profile_and_round_trips_export():
    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json=_import_payload(),
        )

        assert response.status_code == status.HTTP_201_CREATED, response.text
        profile = response.json()
        assert profile["name"] == "Imported Firefox"
        assert profile["schema_version"] == "release-151"
        assert profile["flags"] == {
            "DisableTelemetry": True,
            "BlockAboutConfig": True,
        }

        export_response = client.get(
            f"/api/export/profiles/{profile['id']}/firefox/policies.json"
        )

    assert export_response.status_code == status.HTTP_200_OK
    assert export_response.json() == {
        "policies": {
            "DisableTelemetry": True,
            "BlockAboutConfig": True,
        }
    }


def test_import_firefox_policies_json_accepts_multipart_file_upload():
    document = {
        "policies": {
            "DisableTelemetry": True,
            "BlockAboutConfig": True,
        }
    }

    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": "Multipart Firefox",
                "schema_version": "release-151",
                "description": "Uploaded policies.json",
                "owner": "Endpoint tests",
            },
            files={
                "file": (
                    "policies.json",
                    json.dumps(document),
                    "application/json",
                )
            },
        )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    profile = response.json()
    assert profile["name"] == "Multipart Firefox"
    assert profile["description"] == "Uploaded policies.json"
    assert profile["owner"] == "Endpoint tests"
    assert profile["schema_version"] == "release-151"
    assert profile["flags"] == document["policies"]


def test_import_firefox_policies_json_accepts_multipart_document_field_and_compliance():
    document = {"policies": {"DisableTelemetry": True}}

    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "schema_version": "release-151",
                "compliance": json.dumps({"framework": "cis", "layer": "cis_l1"}),
            },
            files={"document": (None, json.dumps(document))},
        )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    profile = response.json()
    assert profile["name"] == "Imported policies.json"
    assert profile["compliance"] == {"framework": "cis", "layer": "cis_l1"}
    assert profile["flags"] == document["policies"]


def test_import_firefox_policies_json_uses_uploaded_filename_as_default_name():
    document = {"policies": {"DisableTelemetry": True}}

    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={"schema_version": "release-151"},
            files={"file": ("workstation-baseline.json", json.dumps(document), "application/json")},
        )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["name"] == "workstation-baseline"


def test_import_firefox_policies_json_rejects_bad_multipart_compliance_shape():
    document = {"policies": {"DisableTelemetry": True}}

    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": "Bad Compliance",
                "schema_version": "release-151",
                "compliance": json.dumps(["cis"]),
            },
            files={"file": ("policies.json", json.dumps(document), "application/json")},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["error"] == "Multipart compliance field must be a JSON object"


def test_import_firefox_policies_json_rejects_multipart_without_file_or_document():
    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={"name": "Missing File"},
            files={"other": (None, "ignored")},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["error"] == "Multipart import requires a file field"


def test_import_firefox_policies_json_rejects_invalid_json_request_body():
    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            content='{"name":',
            headers={"content-type": "application/json"},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["message"] == "Invalid JSON in request body"


def test_import_firefox_policies_json_rejects_unsupported_content_type():
    with make_test_client() as client:
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            content="not json",
            headers={"content-type": "text/plain"},
        )

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json()["detail"]["message"] == "Unsupported import content type"


def test_import_payload_validation_errors_are_reported_as_422():
    with pytest.raises(HTTPException) as excinfo:
        _validate_import_request_payload({})

    assert excinfo.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.anyio
async def test_multipart_import_rejects_unsupported_document_field_type():
    class FakeForm(dict):
        pass

    class FakeRequest:
        headers = {"content-type": "multipart/form-data; boundary=test"}

        async def form(self):
            return FakeForm({"file": object()})

    with pytest.raises(HTTPException) as excinfo:
        await _read_firefox_policies_import_request(FakeRequest())

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert excinfo.value.detail["error"] == "Unsupported multipart document field"


def test_import_firefox_policies_json_rejects_invalid_multipart_json_without_creating_profile():
    with make_test_client() as client:
        before = client.get("/api/profiles").json()
        response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": "Invalid Multipart JSON",
                "schema_version": "release-151",
            },
            files={
                "file": (
                    "policies.json",
                    '{"policies":',
                    "application/json",
                )
            },
        )
        after = client.get("/api/profiles").json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert detail["message"] == "Invalid JSON in policies.json"
    assert after == before


def test_import_firefox_policies_json_rejects_internal_flags_shape():
    payload = {
        "name": "Wrong Shape",
        "schema_version": "release-151",
        "document": {
            "flags": {
                "DisableTelemetry": True,
            }
        },
    }

    with make_test_client() as client:
        response = client.post("/api/profiles/import/firefox/policies.json", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert detail["message"] == "Firefox policies.json import failed"
    assert any(issue["path"] == ["policies"] for issue in detail["issues"])
    assert any(issue["path"] == ["flags"] for issue in detail["issues"])


def test_import_firefox_policies_json_rejects_schema_validation_errors_with_external_path():
    payload = {
        "name": "Invalid Imported Policy",
        "schema_version": "release-151",
        "document": {
            "policies": {
                "Proxy": {
                    "Mode": "bogus",
                }
            }
        },
    }

    with make_test_client() as client:
        response = client.post("/api/profiles/import/firefox/policies.json", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = response.json()["detail"]
    assert detail["message"] == "Policy validation failed"
    assert detail["issues"][0]["policy"] == "Proxy"
    assert detail["issues"][0]["path"] == ["policies", "Proxy", "Mode"]


def test_import_firefox_policies_json_rejects_duplicate_profile_name():
    payload = _import_payload(name="Duplicate Firefox Import")

    with make_test_client() as client:
        first = client.post("/api/profiles/import/firefox/policies.json", json=payload)
        second = client.post("/api/profiles/import/firefox/policies.json", json=payload)

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["detail"] == "Profile with this name already exists"


def test_import_firefox_policies_json_rejects_unknown_schema_channel():
    payload = _import_payload(name="Unknown Schema")
    payload["schema_version"] = "beta-999"

    with make_test_client() as client:
        response = client.post("/api/profiles/import/firefox/policies.json", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert detail["message"] == "Profile validation failed"
    assert "Unsupported channel" in detail["error"]
