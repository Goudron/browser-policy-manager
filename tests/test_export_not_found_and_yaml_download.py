from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(prefix: str = "EXY"):
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "YAML download path",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
    }


def test_single_export_not_found_json_and_yaml():
    """Covers 404 branch for single export (json/yaml)."""
    client = TestClient(app)
    # use a very large/non-existent id
    bad_id = 9_999_999

    rj = client.get(f"/api/export/{bad_id}/policies.json")
    assert rj.status_code in (404, 400)

    ry = client.get(f"/api/export/{bad_id}/policies.yaml")
    assert ry.status_code in (404, 400)


def test_single_export_yaml_suffix_with_download_headers():
    """Covers YAML suffix route + download header branch."""
    client = TestClient(app)

    # Create
    r = client.post("/api/policies", json=_mk())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # YAML by suffix with ?download=1
    ry = client.get(f"/api/export/{pid}/policies.yaml?download=1")
    assert ry.status_code == 200
    # content-type variations allowed
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    # if Content-Disposition present, it should indicate YAML
    cd = ry.headers.get("content-disposition", "")
    if cd:
        assert "attachment" in cd.lower() and ".yaml" in cd.lower()
    assert "DisableTelemetry" in ry.text
