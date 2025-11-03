from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(name_prefix: str, owner: str, schema: str, flags: dict | None = None):
    """Build a policy body with specific attributes to exercise list filters."""
    if flags is None:
        flags = {"DisableTelemetry": True}
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{name_prefix}-{u}",
        "description": "List filters",
        "schema_version": schema,
        "flags": flags,
        "owner": owner,
    }


def test_list_filters_include_deleted_sort_and_pagination():
    client = TestClient(app)

    # Seed multiple records with different owners/schemas; delete one
    r1 = client.post("/api/policies", json=_mk("LF-A", "ops@example.org", "firefox-ESR"))
    r2 = client.post("/api/policies", json=_mk("LF-B", "sec@example.org", "firefox-ESR"))
    r3 = client.post("/api/policies", json=_mk("LF-C", "ops@example.org", "firefox-ESR"))
    assert r1.status_code == r2.status_code == r3.status_code == 201
    pid_deleted = r2.json()["id"]
    rdel = client.delete(f"/api/policies/{pid_deleted}")
    assert rdel.status_code in (200, 204)

    # Default list hides deleted
    r = client.get("/api/policies")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert pid_deleted not in ids

    # include_deleted=true shows the record
    r_inc = client.get("/api/policies", params={"include_deleted": "true"})
    assert r_inc.status_code == 200
    ids_inc = {p["id"] for p in r_inc.json()}
    assert pid_deleted in ids_inc

    # Owner + schema_version + q filters combined
    r_f = client.get(
        "/api/policies",
        params={
            "owner": "ops@example.org",
            "schema_version": "firefox-ESR",
            "q": "LF-",
        },
    )
    assert r_f.status_code == 200
    assert len(r_f.json()) >= 1

    # Sorting and pagination branches
    r_page1 = client.get(
        "/api/policies",
        params={"order_by": "name", "order": "asc", "limit": 1, "offset": 0},
    )
    r_page2 = client.get(
        "/api/policies",
        params={"order_by": "updated_at", "order": "desc", "limit": 1, "offset": 1},
    )
    assert r_page1.status_code == r_page2.status_code == 200
