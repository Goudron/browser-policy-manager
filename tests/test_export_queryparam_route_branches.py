from __future__ import annotations

import uuid

from app.main import app
from tests.support import make_test_client


def _mk(prefix: str = "QP"):
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "Query-param export path",
        "schema_version": "esr-140.9",
        "flags": {"DisableTelemetry": True, "DisablePrivateBrowsing": True},
    }


def test_single_export_queryparam_yaml_and_404_and_include_deleted():
    """Covers /api/export/profiles/{id}?fmt=... with YAML branch, 404 branch, and include_deleted=True."""
    client = make_test_client(app)

    # Create a profile
    r = client.post("/api/profiles", json=_mk())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Export via query-param route in YAML (hits the fmt == "yaml" branch)
    ry = client.get(f"/api/export/profiles/{pid}?fmt=yaml")
    assert ry.status_code == 200
    # YAML content type may vary slightly; allow common variants
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    # Filename header is set by implementation; if present it should end with .yaml
    cdy = ry.headers.get("content-disposition", "")
    if cdy:
        assert (
            "attachment" in cdy.lower() and cdy.lower().endswith('.yaml"') or ".yaml" in cdy.lower()
        )
    assert "DisableTelemetry" in ry.text

    # Soft-delete item to make the default include_deleted=False return 404
    rdel = client.delete(f"/api/profiles/{pid}")
    assert rdel.status_code == 204

    # Now same query-param route WITHOUT include_deleted should return 404 (Not found branch)
    r404 = client.get(f"/api/export/profiles/{pid}?fmt=json")
    assert r404.status_code == 404

    # And WITH include_deleted=true should return 200 and JSON payload (fmt == "json" branch)
    rj = client.get(f"/api/export/profiles/{pid}?fmt=json&include_deleted=true")
    assert rj.status_code == 200
    assert rj.headers.get("content-type", "").startswith("application/json")
    cdj = rj.headers.get("content-disposition", "")
    if cdj:
        assert "attachment" in cdj.lower() and ".json" in cdj.lower()
    assert '"DisableTelemetry"' in rj.text


def test_collection_yaml_queryparam_with_include_deleted_and_filters_for_envelope():
    """Covers collection export YAML branch with include_deleted=True and filters; verifies YAML envelope."""
    client = make_test_client(app)

    # Seed and delete one record so include_deleted=True makes a difference
    r = client.post("/api/profiles", json=_mk(prefix="QPC"))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    rdel = client.delete(f"/api/profiles/{pid}")
    assert rdel.status_code == 204

    # Export collection in YAML with include_deleted=true and some filters/pagination
    params = {
        "fmt": "yaml",
        "include_deleted": "true",
        "q": "QPC-",  # substring in name
        "schema_version": "esr-140.9",
        "limit": 5,
        "offset": 0,
        "sort": "updated_at",
        "order": "desc",
    }
    ry = client.get("/api/export/profiles", params=params)
    assert ry.status_code == 200
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    txt = ry.text
    # Verify the standard YAML envelope keys are present
    assert "items:" in txt and "limit:" in txt and "offset:" in txt and "count:" in txt
