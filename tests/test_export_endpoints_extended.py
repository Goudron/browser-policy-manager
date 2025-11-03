from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_profile_body():
    unique = uuid.uuid4().hex[:8]
    return {
        "name": f"Exp-{unique}",
        "description": "Export profile",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
    }


def test_export_yaml_and_json_and_404():
    client = TestClient(app)

    # Create
    r = client.post("/api/policies", json=_mk_profile_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Export YAML
    ry = client.get(f"/api/export/{pid}/policies.yaml")
    assert ry.status_code == 200
    assert "DisableTelemetry" in ry.text
    # Content-Type may be application/x-yaml or text/plain depending on impl
    assert any(
        ry.headers["content-type"].startswith(t) for t in ("application/x-yaml", "text/plain")
    )

    # Export JSON
    rj = client.get(f"/api/export/{pid}/policies.json")
    assert rj.status_code == 200
    # Do not rely on top-level shape; ensure key is present somewhere
    assert '"DisableTelemetry"' in rj.text or "DisableTelemetry" in rj.text

    # Unknown id -> 404/400 depending on implementation detail
    r404 = client.get("/api/export/999999/policies.json")
    assert r404.status_code in (404, 400)
