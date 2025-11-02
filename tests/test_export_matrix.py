from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(name_prefix: str, owner: str = "ops@example.org"):
    """Create a policy payload with predictable fields."""
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{name_prefix}-{u}",
        "description": "Matrix export",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
        "owner": owner,
    }


def _ok_yaml(ct: str) -> bool:
    return any(
        ct.startswith(t) for t in ("application/x-yaml", "text/yaml", "text/plain")
    )


def _status_ok_for_unknown_fmt(code: int) -> bool:
    # FastAPI often returns 422 for invalid enum; other impls may do 400 or 404.
    return code in (200, 400, 404, 422)


def _ensure_created(client: TestClient, n: int, prefix: str) -> list[int]:
    ids: list[int] = []
    for _ in range(n):
        r = client.post("/api/policies", json=_mk(prefix))
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])
    return ids


def test_export_full_matrix_single_and_collection():
    """Systematically cover export branches for single & collection endpoints."""
    client = TestClient(app)

    # Seed items
    ids = _ensure_created(client, 2, "MATRIX")
    pid = ids[0]

    # --- SINGLE EXPORTS ---
    # 1) Suffix routes: /api/export/{id}/policies.(json|yaml)
    for fmt in ("json", "yaml"):
        url = f"/api/export/{pid}/policies.{fmt}"
        # with/without download, with indent/pretty toggles
        for download in ("0", "1"):
            for indent in (None, "2"):
                for pretty in ("0", "1"):
                    qs = []
                    if download == "1":
                        qs.append("download=1")
                    if indent is not None:
                        qs.append(f"indent={indent}")
                    if pretty == "1":
                        qs.append("pretty=1")
                    full = url + (("?" + "&".join(qs)) if qs else "")
                    r = client.get(full)
                    assert r.status_code == 200
                    ct = r.headers.get("content-type", "")
                    if fmt == "json":
                        assert ct.startswith("application/json")
                        assert '"DisableTelemetry"' in r.text
                    else:
                        assert _ok_yaml(ct)
                        assert "DisableTelemetry" in r.text
                    # optional Content-Disposition
                    cd = r.headers.get("content-disposition", "")
                    if cd:
                        assert "attachment" in cd.lower()
                        assert f".{fmt}" in cd.lower()

    # 2) Query-param route: /api/export/policies/{id}?fmt=...
    for fmt in ("json", "yaml"):
        for download in ("0", "1"):
            for indent in (None, "2"):
                for pretty in ("0", "1"):
                    qs = [f"fmt={fmt}"]
                    if download == "1":
                        qs.append("download=1")
                    if indent is not None:
                        qs.append(f"indent={indent}")
                    if pretty == "1":
                        qs.append("pretty=1")
                    r = client.get(f"/api/export/policies/{pid}?" + "&".join(qs))
                    assert r.status_code == 200
                    ct = r.headers.get("content-type", "")
                    if fmt == "json":
                        assert ct.startswith("application/json")
                        assert '"DisableTelemetry"' in r.text
                    else:
                        assert _ok_yaml(ct)
                        assert "DisableTelemetry" in r.text
                    cd = r.headers.get("content-disposition", "")
                    if cd:
                        assert "attachment" in cd.lower()
                        assert f".{fmt}" in cd.lower()

    # 3) Soft-delete the item and exercise include_deleted branches & 404
    rdel = client.delete(f"/api/policies/{pid}")
    assert rdel.status_code in (200, 204)

    # Default (include_deleted=false) should 404
    r404_json = client.get(f"/api/export/policies/{pid}?fmt=json")
    assert r404_json.status_code == 404
    r404_yaml = client.get(f"/api/export/policies/{pid}?fmt=yaml")
    assert r404_yaml.status_code == 404

    # With include_deleted=true should return data
    rj = client.get(f"/api/export/policies/{pid}?fmt=json&include_deleted=true")
    assert rj.status_code == 200 and rj.headers.get("content-type", "").startswith(
        "application/json"
    )
    ry = client.get(f"/api/export/policies/{pid}?fmt=yaml&include_deleted=true")
    assert ry.status_code == 200 and _ok_yaml(ry.headers.get("content-type", ""))

    # 4) Non-existent ID should return 404 for both suffix and query-param routes
    bad_id = 9_999_999
    r_bad_sfx_json = client.get(f"/api/export/{bad_id}/policies.json")
    r_bad_sfx_yaml = client.get(f"/api/export/{bad_id}/policies.yaml")
    assert r_bad_sfx_json.status_code in (404, 400)
    assert r_bad_sfx_yaml.status_code in (404, 400)
    r_bad_qp_json = client.get(f"/api/export/policies/{bad_id}?fmt=json")
    r_bad_qp_yaml = client.get(f"/api/export/policies/{bad_id}?fmt=yaml")
    assert r_bad_qp_json.status_code in (404, 400)
    assert r_bad_qp_yaml.status_code in (404, 400)

    # 5) Unknown fmt (validation may 422)
    r_unknown = client.get(f"/api/export/policies/{pid}?fmt=txt")
    assert _status_ok_for_unknown_fmt(r_unknown.status_code)

    # --- COLLECTION EXPORTS ---
    # Default (no fmt) should be JSON envelope
    r_def = client.get("/api/export/policies?limit=1&offset=0&pretty=1&indent=2")
    assert r_def.status_code == 200
    assert r_def.headers.get("content-type", "").startswith("application/json")
    assert (
        '"items"' in r_def.text
        and '"limit"' in r_def.text
        and '"offset"' in r_def.text
        and '"count"' in r_def.text
    )

    # JSON with filters (owner/schema_version/q), pagination, sorting, download
    r_coll_json = client.get(
        "/api/export/policies",
        params={
            "fmt": "json",
            "download": "1",
            "owner": "ops@example.org",
            "schema_version": "firefox-ESR",
            "q": "MATRIX-",
            "include_deleted": "true",
            "limit": 2,
            "offset": 0,
            "sort": "updated_at",
            "order": "desc",
        },
    )
    assert r_coll_json.status_code == 200
    assert r_coll_json.headers.get("content-type", "").startswith("application/json")
    if cd := r_coll_json.headers.get("content-disposition", ""):
        assert ".json" in cd.lower()
    assert '"items"' in r_coll_json.text

    # YAML with different sort and pagination
    r_coll_yaml = client.get(
        "/api/export/policies",
        params={
            "fmt": "yaml",
            "download": "1",
            "owner": "ops@example.org",
            "schema_version": "firefox-ESR",
            "q": "MATRIX-",
            "include_deleted": "true",
            "limit": 3,
            "offset": 0,
            "sort": "name",
            "order": "asc",
        },
    )
    assert r_coll_yaml.status_code == 200
    assert _ok_yaml(r_coll_yaml.headers.get("content-type", ""))
    if cd2 := r_coll_yaml.headers.get("content-disposition", ""):
        assert ".yaml" in cd2.lower()
    txt = r_coll_yaml.text
    assert "items:" in txt and "limit:" in txt and "offset:" in txt and "count:" in txt

    # Empty set envelope (unmatchable q)
    r_empty_json = client.get("/api/export/policies?q=__NO_MATCH_EXPECTED__")
    assert r_empty_json.status_code == 200
    assert '"items"' in r_empty_json.text

    r_empty_yaml = client.get("/api/export/policies?fmt=yaml&q=__NO_MATCH_EXPECTED__")
    assert r_empty_yaml.status_code == 200
    assert _ok_yaml(r_empty_yaml.headers.get("content-type", ""))
    assert "items:" in r_empty_yaml.text
