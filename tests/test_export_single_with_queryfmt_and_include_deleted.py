from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_body(name_prefix: str = "XDel", owner: str | None = None):
    """Build a policy body used across export tests."""
    u = uuid.uuid4().hex[:6]
    body = {
        "name": f"{name_prefix}-{u}",
        "description": "Marked for deletion",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisableFirefoxAccounts": True},
    }
    if owner is not None:
        body["owner"] = owner
    return body


def test_export_single_with_query_format_and_include_deleted():
    """Covers /api/export/policies/{id}?fmt={json|yaml}&include_deleted=true."""
    client = TestClient(app)

    # Create a policy
    r = client.post("/api/policies", json=_mk_body(owner="ops@example.org"))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Soft delete it so default lookups would hide it
    rdel = client.delete(f"/api/policies/{pid}")
    assert rdel.status_code in (204, 200)

    # Export with include_deleted=true and fmt=yaml (query-param format)
    ry = client.get(f"/api/export/policies/{pid}?fmt=yaml&include_deleted=true")
    assert ry.status_code == 200
    assert "DisableTelemetry" in ry.text
    # YAML content type variations allowed
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/plain", "text/yaml")
    )
    # Content-Disposition should name a YAML file (if header is present)
    cd = ry.headers.get("content-disposition", "")
    if cd:
        assert cd.lower().startswith("attachment;")
        assert cd.lower().endswith('.yaml"') or ".yaml" in cd.lower()

    # Export same item as JSON using query fmt
    rj = client.get(f"/api/export/policies/{pid}?fmt=json&include_deleted=true")
    assert rj.status_code == 200
    assert '"DisableTelemetry"' in rj.text
    assert rj.headers.get("content-type", "").startswith("application/json")
    cdj = rj.headers.get("content-disposition", "")
    if cdj:
        assert ".json" in cdj.lower()
