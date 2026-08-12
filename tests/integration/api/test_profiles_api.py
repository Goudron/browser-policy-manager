from __future__ import annotations

from fastapi import status

from tests.support import make_test_client


def test_guided_compliance_catalog_is_constrained_and_selection_scoped():
    with make_test_client() as client:
        response = client.get(
            "/profiles/guided-compliance",
            params={
                "starter_key": "basic_corporate",
                "schema_version": "release-153",
                "layer_key": "cis_l2",
            },
        )
        rejected = client.get(
            "/profiles/guided-compliance",
            params={
                "starter_key": "not-a-starter",
                "schema_version": "release-153",
                "layer_key": "cis_l2",
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["cache-control"] == "private, max-age=300"
    payload = response.json()
    assert payload["policy_values"]["DisableTelemetry"] is True
    assert payload["summary"]["added_from_cis"] >= 1
    assert payload["decisions"]
    assert rejected.status_code == status.HTTP_404_NOT_FOUND


def test_create_profile_invalid_policies_returns_422():
    """
    If flags contain invalid policy values, the /api/profiles endpoint
    must fail with 422 and expose policy validation issues.
    """
    payload = {
        "name": "Invalid profile",
        "schema_version": "release-153",
        "flags": {
            # HttpAllowlist currently accepts arbitrary strings, so we use an
            # invalid item type that still reaches schema validation.
            "HttpAllowlist": [42],
        },
    }

    with make_test_client() as client:
        response = client.post("/api/profiles", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    body = response.json()
    assert body["detail"]["message"] == "Policy validation failed"
    issues = body["detail"]["issues"]

    # There must be at least one issue attached to HttpAllowlist.
    assert any(issue["policy"] == "HttpAllowlist" for issue in issues)
    assert any("is not of type 'string'" in issue["message"] for issue in issues)


def test_create_profile_unknown_schema_version_returns_lifecycle_422():
    """
    If schema_version (channel) is not supported by internal policy schemas,
    the endpoint must fail closed with the catalog's HTTP 422 error code.
    """
    payload = {
        "name": "Unknown channel profile",
        "schema_version": "beta-999",  # intentionally unsupported channel
        "flags": {
            "DisableAppUpdate": True,
        },
    }

    with make_test_client() as client:
        response = client.post("/api/profiles", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    body = response.json()
    assert body["detail"] == {
        "message": "Schema channel is not available",
        "code": "schema_channel_unknown",
    }


def test_create_profile_without_schema_channel_uses_latest_esr_default():
    with make_test_client() as client:
        response = client.post("/api/profiles", json={"name": "Latest ESR default", "flags": {}})

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["schema_version"] == "esr-153.0"


def test_profile_recommendation_is_value_free_and_preserved_by_list_pagination_and_filters():
    with make_test_client() as client:
        older = client.post(
            "/api/profiles",
            json={"name": "Older ESR", "schema_version": "esr-115.38", "flags": {}},
        )
        latest = client.post(
            "/api/profiles",
            json={"name": "Latest ESR", "schema_version": "esr-153.0", "flags": {}},
        )
        page = client.get(
            "/api/profiles", params={"limit": 1, "offset": 0, "sort": "id", "order": "asc"}
        )
        filtered = client.get("/api/profiles", params={"schema_version": "esr-115.38"})

    assert older.status_code == status.HTTP_201_CREATED
    recommendation = older.json()["recommendation"]
    assert recommendation["source"] == {"line_id": "esr-115", "artifact_id": "esr-115.38"}
    assert recommendation["target"]["artifact_id"] == "esr-153.0"
    assert recommendation["target"]["i18n_key"] == "profiles.firefox_schema_esr_153_0"
    assert recommendation["profile_revision"] == older.json()["revision"]
    assert recommendation["action"] == {
        "action_id": "conversion-preview",
        "preview_target_artifact_id": "esr-153.0",
    }
    assert "flags" not in recommendation and "policies" not in recommendation
    assert latest.status_code == status.HTTP_201_CREATED
    assert latest.json()["recommendation"] is None
    assert page.status_code == status.HTTP_200_OK
    assert page.json()[0]["recommendation"] == recommendation
    assert filtered.status_code == status.HTTP_200_OK
    assert filtered.json()[0]["recommendation"] == recommendation


def test_profiles_openapi_exposes_read_only_recommendation_metadata():
    with make_test_client() as client:
        response = client.get("/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    schemas = response.json()["components"]["schemas"]
    recommendation = schemas["ProfileRead"]["properties"]["recommendation"]
    assert {item.get("$ref") for item in recommendation["anyOf"]} == {
        "#/components/schemas/ProfileRecommendation",
        None,
    }
    properties = schemas["ProfileRecommendation"]["properties"]
    assert set(properties) == {
        "recommendation_id",
        "reason_code",
        "profile_revision",
        "source",
        "target",
        "action",
    }
    assert properties["recommendation_id"]["const"] == "schema-conversion.older-esr-recommendation"
    assert properties["reason_code"]["const"] == "supported_older_esr_to_latest_esr"
