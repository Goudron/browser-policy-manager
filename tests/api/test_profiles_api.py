from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app

# Use the real application factory to ensure all routers are included.
app = create_app()
client = TestClient(app)


def test_create_profile_invalid_policies_returns_422():
    """
    If flags contain invalid policy values, the /api/profiles endpoint
    must fail with 422 and expose policy validation issues.
    """
    payload = {
        "name": "Invalid profile",
        "schema_version": "release-145",
        "flags": {
            # HttpAllowlist in our generated schemas has an enum of allowed URLs;
            # "http://evil.example" is intentionally not part of it.
            "HttpAllowlist": ["http://evil.example"],
        },
    }

    response = client.post("/api/profiles", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    body = response.json()
    assert body["detail"]["message"] == "Policy validation failed"
    issues = body["detail"]["issues"]

    # There must be at least one issue attached to HttpAllowlist.
    assert any(issue["policy"] == "HttpAllowlist" for issue in issues)
    assert any("not allowed" in issue["message"] for issue in issues)


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

    response = client.post("/api/profiles", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    body = response.json()
    assert body["detail"]["message"] == "Profile validation failed"
    # The exact wording comes from load_policy_schema_for_channel(...)
    # which raises ValueError("Unsupported channel '<channel>'").
    assert "Unsupported channel" in body["detail"]["error"]
