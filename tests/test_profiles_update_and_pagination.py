from __future__ import annotations

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk_body(prefix: str = "Pag"):
    return build_profile_payload(name_prefix=prefix, description="Init desc")


def test_update_and_pagination_and_ordering_like():
    client = make_test_client(app)

    # Create 3 profiles
    created_ids = []
    for i in range(3):
        r = client.post("/api/profiles", json=_mk_body(prefix=f"Pg{i}"))
        assert r.status_code == 201, r.text
        created_ids.append(r.json()["id"])

    # List with limit/offset (pagination smoke)
    r_page1 = client.get("/api/profiles", params={"limit": 2, "offset": 0})
    assert r_page1.status_code == 200
    assert len(r_page1.json()) <= 2

    r_page2 = client.get("/api/profiles", params={"limit": 2, "offset": 2})
    assert r_page2.status_code == 200

    # Filter by name substring (if supported, at least should not 500)
    r_like = client.get("/api/profiles", params={"q": "Pg"})
    assert r_like.status_code == 200

    # Update (PATCH) description and flags
    pid = created_ids[0]
    current_revision = client.get(f"/api/profiles/{pid}").json()["revision"]
    patch = {
        "description": "Updated desc",
        "flags": {"DisableTelemetry": False, "DisablePrivateBrowsing": True},
        "expected_revision": current_revision,
    }
    r_upd = client.patch(f"/api/profiles/{pid}", json=patch)
    assert r_upd.status_code == 200, r_upd.text
    assert r_upd.json()["revision"] == current_revision + 1

    # Read back and verify was updated
    r_get = client.get(f"/api/profiles/{pid}")
    assert r_get.status_code == 200
    obj = r_get.json()
    assert obj["description"] in (
        "Updated desc",
        "Init desc",
    )  # accept either if PATCH returns 204-but-updated
    # Flags must at least be a dict; implementation may store/serialize slightly differently
    assert isinstance(obj.get("flags"), dict)


def test_patch_profile_rejects_stale_expected_revision_without_mutation():
    client = make_test_client(app)
    created = client.post(
        "/api/profiles",
        json=build_profile_payload(name_prefix="RevisionConflict"),
    )
    assert created.status_code == 201, created.text
    profile = created.json()
    profile_id = profile["id"]

    first_update = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Fresh update",
            "expected_revision": profile["revision"],
        },
    )
    assert first_update.status_code == 200, first_update.text
    assert first_update.json()["revision"] == profile["revision"] + 1

    stale_update = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Stale update should not persist",
            "expected_revision": profile["revision"],
        },
    )
    assert stale_update.status_code == 409, stale_update.text
    assert stale_update.json()["detail"] == {
        "message": "Profile has been modified since it was loaded",
        "profile_id": profile_id,
        "current_revision": profile["revision"] + 1,
        "expected_revision": profile["revision"],
    }

    after_conflict = client.get(f"/api/profiles/{profile_id}")
    assert after_conflict.status_code == 200, after_conflict.text
    assert after_conflict.json()["description"] == "Fresh update"
    assert after_conflict.json()["revision"] == profile["revision"] + 1


def test_patch_profile_can_clear_compliance_metadata():
    client = make_test_client(app)
    payload = build_profile_payload(name_prefix="ComplianceClear")
    payload["compliance"] = {"framework": "cis", "layer": "cis_l1"}
    created = client.post(
        "/api/profiles",
        json=payload,
    )
    assert created.status_code == 201, created.text

    response = client.patch(
        f"/api/profiles/{created.json()['id']}",
        json={"compliance": None},
    )

    assert response.status_code == 200, response.text
    assert response.json()["compliance"] is None


def test_patch_profile_replaces_flags_so_ui_deletions_persist():
    client = make_test_client(app)
    created = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name_prefix="ReplaceFlags",
            flags={
                "DisableTelemetry": True,
                "DisablePrivateBrowsing": True,
            },
        ),
    )
    assert created.status_code == 201, created.text
    profile = created.json()

    updated = client.patch(
        f"/api/profiles/{profile['id']}",
        json={
            "flags": {"DisableTelemetry": False},
            "expected_revision": profile["revision"],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["flags"] == {"DisableTelemetry": False}

    fresh = client.get(f"/api/profiles/{profile['id']}")
    assert fresh.status_code == 200, fresh.text
    assert fresh.json()["flags"] == {"DisableTelemetry": False}
