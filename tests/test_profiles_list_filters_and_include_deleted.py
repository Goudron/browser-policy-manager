from __future__ import annotations

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk(name_prefix: str, owner: str, schema: str, flags: dict | None = None):
    return build_profile_payload(
        name_prefix=name_prefix,
        owner=owner,
        schema_version=schema,
        description="List filters",
        flags=flags or {"DisableTelemetry": True},
    )


def test_list_filters_include_deleted_sort_and_pagination():
    client = make_test_client(app)

    # Seed multiple records with different owners/schemas; delete one
    r1 = client.post("/api/profiles", json=_mk("LF-A", "ops@example.org", "esr-140.10"))
    r2 = client.post("/api/profiles", json=_mk("LF-B", "sec@example.org", "esr-140.10"))
    r3 = client.post("/api/profiles", json=_mk("LF-C", "ops@example.org", "esr-140.10"))
    assert r1.status_code == r2.status_code == r3.status_code == 201
    pid_deleted = r2.json()["id"]
    rdel = client.delete(f"/api/profiles/{pid_deleted}")
    assert rdel.status_code == 204

    # Default list hides deleted
    r = client.get("/api/profiles")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert pid_deleted not in ids

    # include_deleted=true shows the record
    r_inc = client.get("/api/profiles", params={"include_deleted": "true"})
    assert r_inc.status_code == 200
    ids_inc = {p["id"] for p in r_inc.json()}
    assert pid_deleted in ids_inc

    # Owner + schema_version + q filters combined
    r_f = client.get(
        "/api/profiles",
        params={
            "owner": "ops@example.org",
            "schema_version": "esr-140.10",
            "q": "LF-",
        },
    )
    assert r_f.status_code == 200
    assert len(r_f.json()) >= 1

    # Sorting and pagination branches
    r_page1 = client.get(
        "/api/profiles",
        params={"order_by": "name", "order": "asc", "limit": 1, "offset": 0},
    )
    r_page2 = client.get(
        "/api/profiles",
        params={"order_by": "updated_at", "order": "desc", "limit": 1, "offset": 1},
    )
    assert r_page1.status_code == r_page2.status_code == 200
