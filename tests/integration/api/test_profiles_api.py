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


def test_create_profile_invalid_schema_version_returns_400():
    """
    If schema_version (channel) is not supported by internal policy schemas,
    the endpoint must fail with HTTP 400 and a clear error message.
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
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    body = response.json()
    assert body["detail"]["message"] == "Profile validation failed"
    assert "Unsupported channel" in body["detail"]["error"]
