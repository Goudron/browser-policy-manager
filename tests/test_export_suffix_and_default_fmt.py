from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_body(prefix: str = "SFX"):
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "Suffix export",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
    }


def test_single_export_suffix_json_and_yaml_and_download_headers():
    """Hit suffix routes: /api/export/{id}/policies.json and .yaml with/without download."""
    client = TestClient(app)

    # Create a policy
    r = client.post("/api/policies", json=_mk_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # JSON by suffix
    rj = client.get(f"/api/export/{pid}/policies.json?download=1&indent=2&pretty=1")
    assert rj.status_code == 200
    assert rj.headers.get("content-type", "").startswith("application/json")
    cd = rj.headers.get("content-disposition", "")
    if cd:
        assert "attachment" in cd.lower() and ".json" in cd.lower()
    assert '"DisableTelemetry"' in rj.text

    # YAML by suffix
    ry = client.get(f"/api/export/{pid}/policies.yaml")
    assert ry.status_code == 200
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    # Content-Disposition may or may not be present; if present, should be .yaml
    cdy = ry.headers.get("content-disposition", "")
    if cdy:
        assert ".yaml" in cdy.lower()
    assert "DisableTelemetry" in ry.text


def test_export_collection_default_fmt_json_with_indent_pretty_download():
    """Call /api/export/policies WITHOUT fmt (default JSON), with indent/pretty/download."""
    client = TestClient(app)

    # Seed a couple records so the list is non-empty
    for _ in range(2):
        rr = client.post("/api/policies", json=_mk_body(prefix="DFLT"))
        assert rr.status_code == 201

    r = client.get("/api/export/policies?download=1&indent=2&pretty=1&limit=1&offset=0")
    assert r.status_code == 200
    # Default branch should be JSON
    assert r.headers.get("content-type", "").startswith("application/json")
    if cd := r.headers.get("content-disposition", ""):
        assert ".json" in cd.lower()
    # Envelope
    assert (
        '"items"' in r.text
        and '"limit"' in r.text
        and '"offset"' in r.text
        and '"count"' in r.text
    )
