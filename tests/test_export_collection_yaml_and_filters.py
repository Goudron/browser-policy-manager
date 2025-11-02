from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_body(name_prefix: str, owner: str, schema: str):
    """Build a policy with specific owner / schema to exercise filters."""
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{name_prefix}-{u}",
        "description": "Collection export",
        "schema_version": schema,
        "flags": {"DisableTelemetry": True},
        "owner": owner,
    }


def test_export_collection_yaml_with_filters_and_sorting():
    """Covers /api/export/policies with fmt=yaml + filters + sorting + pagination."""
    client = TestClient(app)

    # Seed a few diverse items
    seeds = [
        _mk_body("ColA", "ops@example.org", "firefox-ESR"),
        _mk_body("ColB", "sec@example.org", "firefox-ESR"),
        _mk_body("ColC", "ops@example.org", "firefox-ESR"),
    ]
    for body in seeds:
        r = client.post("/api/policies", json=body)
        assert r.status_code == 201, r.text

    # YAML export with owner/schema filters, search query, sorting and pagination
    params = {
        "fmt": "yaml",
        "owner": "ops@example.org",
        "schema_version": "firefox-ESR",
        "q": "Col",  # substring match in name
        "include_deleted": "false",
        "limit": 2,
        "offset": 0,
        "sort": "name",
        "order": "asc",
    }
    r = client.get("/api/export/policies", params=params)
    assert r.status_code == 200
    txt = r.text
    # Ensure YAML envelope keys are present
    assert "items:" in txt and "limit:" in txt and "offset:" in txt and "count:" in txt
    # Ensure at least one of the seeded names/owner shows up
    assert "ops@example.org" in txt
    assert "Col" in txt
    # Attachment name (if present) should be for YAML list
    cd = r.headers.get("content-disposition", "")
    if cd:
        assert "policies.yaml" in cd.lower()
