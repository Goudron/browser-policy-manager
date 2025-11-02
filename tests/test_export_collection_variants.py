from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(name_prefix: str, owner: str):
    """Create minimal policy to exercise collection export branches."""
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{name_prefix}-{u}",
        "description": "Collection export",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
        "owner": owner,
    }


def test_export_collection_json_yaml_download_filters_sort_paginate():
    client = TestClient(app)

    # Seed several records
    for prefix, owner in (
        ("EC-A", "ops@example.org"),
        ("EC-B", "sec@example.org"),
        ("EC-C", "ops@example.org"),
    ):
        rr = client.post("/api/policies", json=_mk(prefix, owner))
        assert rr.status_code == 201

    # JSON collection with download and filters (should hit json branch)
    params_json = {
        "fmt": "json",
        "download": "1",
        "owner": "ops@example.org",
        "schema_version": "firefox-ESR",
        "q": "EC-",
        "include_deleted": "false",
        "limit": 2,
        "offset": 0,
        "sort": "name",
        "order": "asc",
    }
    rj = client.get("/api/export/policies", params=params_json)
    assert rj.status_code == 200
    assert rj.headers.get("content-type", "").startswith("application/json")
    if cd := rj.headers.get("content-disposition", ""):
        assert ".json" in cd.lower()
    assert '"items"' in rj.text

    # YAML collection with different sort and pagination (should hit yaml branch)
    params_yaml = {
        "fmt": "yaml",
        "download": "1",
        "owner": "ops@example.org",
        "schema_version": "firefox-ESR",
        "q": "EC-",
        "include_deleted": "false",
        "limit": 1,
        "offset": 1,
        "sort": "updated_at",
        "order": "desc",
    }
    ry = client.get("/api/export/policies", params=params_yaml)
    assert ry.status_code == 200
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    if cd2 := ry.headers.get("content-disposition", ""):
        assert ".yaml" in cd2.lower()
    # YAML envelope keys
    assert (
        "items:" in ry.text
        and "limit:" in ry.text
        and "offset:" in ry.text
        and "count:" in ry.text
    )
