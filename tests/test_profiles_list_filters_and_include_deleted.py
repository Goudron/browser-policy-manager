from __future__ import annotations

from app.main import app
from app.models.profile import Profile
from app.services.profile_service import ProfileService
from tests.support import build_profile_payload, make_test_client


def _mk(name_prefix: str, schema: str, flags: dict | None = None):
    return build_profile_payload(
        name_prefix=name_prefix,
        schema_version=schema,
        description="List filters",
        flags=flags or {"DisableTelemetry": True},
    )


def test_list_filters_include_deleted_sort_and_pagination():
    client = make_test_client(app)

    # Seed multiple records; delete one.
    r1 = client.post("/api/profiles", json=_mk("LF-A", "esr-140.12"))
    r2 = client.post("/api/profiles", json=_mk("LF-B", "esr-140.12"))
    r3 = client.post("/api/profiles", json=_mk("LF-C", "esr-140.12"))
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

    # Lifecycle filters let the library distinguish active from archived profiles.
    r_archived = client.get("/api/profiles", params={"lifecycle": "archived"})
    assert r_archived.status_code == 200
    archived_items = r_archived.json()
    assert pid_deleted in {p["id"] for p in archived_items}
    assert all(p["is_deleted"] for p in archived_items)

    r_all = client.get("/api/profiles", params={"lifecycle": "all"})
    assert r_all.status_code == 200
    assert pid_deleted in {p["id"] for p in r_all.json()}

    # schema_version + q filters combined
    r_f = client.get(
        "/api/profiles",
        params={
            "schema_version": "esr-140.12",
            "q": "LF-",
        },
    )
    assert r_f.status_code == 200
    assert len(r_f.json()) >= 1
    assert all(p["validation_state"] == "valid" for p in r_f.json())

    r_valid = client.get("/api/profiles", params={"validation_state": "valid"})
    assert r_valid.status_code == 200
    assert len(r_valid.json()) >= 1
    assert all(p["validation_state"] == "valid" for p in r_valid.json())

    empty_payload = build_profile_payload(
        name_prefix="LF-EMPTY",
        description="No managed rules yet",
    )
    empty_payload["flags"] = {}
    r_empty = client.post("/api/profiles", json=empty_payload)
    assert r_empty.status_code == 201
    assert r_empty.json()["validation_state"] == "not_validated"

    r_not_validated = client.get(
        "/api/profiles",
        params={"validation_state": "not_validated"},
    )
    assert r_not_validated.status_code == 200
    assert r_empty.json()["id"] in {p["id"] for p in r_not_validated.json()}
    assert all(p["validation_state"] == "not_validated" for p in r_not_validated.json())

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

    r_schema_sort = client.get(
        "/api/profiles",
        params={"sort": "schema_version", "order": "asc"},
    )
    assert r_schema_sort.status_code == 200


def test_profile_validation_state_reports_invalid_payload():
    profile = Profile(
        name="Invalid profile",
        schema_version="unknown-channel",
        flags={"DisableTelemetry": True},
    )

    assert ProfileService._validation_state(profile) == "invalid"
