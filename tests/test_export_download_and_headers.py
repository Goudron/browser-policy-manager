from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_profile_body():
    """Generate a unique policy profile for export tests."""
    unique = uuid.uuid4().hex[:8]
    return {
        "name": f"Dl-{unique}",
        "description": "Export with download",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisableFirefoxAccounts": True},
    }


def test_export_with_download_headers_and_content_type():
    """Covers YAML/JSON export with ?download=1 and Content-Type variations."""
    client = TestClient(app)

    # Create a policy profile
    r = client.post("/api/policies", json=_mk_profile_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # JSON export with download=1
    rj = client.get(f"/api/export/{pid}/policies.json?download=1")
    assert rj.status_code == 200
    cd = rj.headers.get("content-disposition", "")
    if cd:
        assert "attachment" in cd.lower()
        assert ".json" in cd.lower()
    assert '"DisableTelemetry"' in rj.text

    # YAML export with download=1
    ry = client.get(f"/api/export/{pid}/policies.yaml?download=1")
    assert ry.status_code == 200
    cd2 = ry.headers.get("content-disposition", "")
    if cd2:
        assert "attachment" in cd2.lower()
        assert ".yaml" in cd2.lower()
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/plain", "text/yaml")
    )
    assert "DisableTelemetry" in ry.text
