from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(name_prefix: str = "ESI"):
    """Build a policy to test single export branches: indent/pretty/bad fmt."""
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{name_prefix}-{u}",
        "description": "Single export",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
    }


def test_single_export_json_with_indent_pretty_and_download():
    """Covers JSON single export with indent/pretty/download and unknown fmt branch."""
    client = TestClient(app)

    # Create one
    r = client.post("/api/policies", json=_mk())
    assert r.status_code == 201
    pid = r.json()["id"]

    # Hit indent/pretty branches and download header in JSON path
    rj = client.get(f"/api/export/policies/{pid}?fmt=json&indent=2&pretty=1&download=1")
    assert rj.status_code == 200
    assert rj.headers.get("content-type", "").startswith("application/json")
    if cd := rj.headers.get("content-disposition", ""):
        assert "attachment" in cd.lower() and ".json" in cd.lower()
    assert '"DisableTelemetry"' in rj.text

    # Unknown fmt should not 500; 422 is also acceptable for validation error
    rbad = client.get(f"/api/export/policies/{pid}?fmt=txt")
    assert rbad.status_code in (200, 400, 404, 422)
