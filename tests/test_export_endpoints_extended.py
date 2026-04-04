from __future__ import annotations

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk_profile_body():
    return build_profile_payload(
        name_prefix="Exp",
        description="Export profile",
        flags={"DisableTelemetry": True, "DisablePrivateBrowsing": True},
    )


def test_export_yaml_and_json_and_404():
    client = make_test_client(app)

    # Create
    r = client.post("/api/profiles", json=_mk_profile_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Export YAML
    ry = client.get(f"/api/export/profiles/{pid}.yaml")
    assert ry.status_code == 200
    assert "DisableTelemetry" in ry.text
    # Content-Type may be application/x-yaml or text/plain depending on impl
    assert any(
        ry.headers["content-type"].startswith(t) for t in ("application/x-yaml", "text/plain")
    )

    # Export JSON
    rj = client.get(f"/api/export/profiles/{pid}.json")
    assert rj.status_code == 200
    # Do not rely on top-level shape; ensure key is present somewhere
    assert '"DisableTelemetry"' in rj.text or "DisableTelemetry" in rj.text

    # Unknown id should return the explicit not-found response.
    r404 = client.get("/api/export/profiles/999999.json")
    assert r404.status_code == 404


def test_export_lifecycle_matches_review_finish_line_states():
    client = make_test_client(app)

    create_response = client.post("/api/profiles", json=_mk_profile_body())
    assert create_response.status_code == 201, create_response.text
    profile_id = create_response.json()["id"]

    ready_json = client.get(f"/api/export/profiles/{profile_id}.json")
    ready_yaml = client.get(f"/api/export/profiles/{profile_id}.yaml")
    ready_firefox = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert ready_json.status_code == 200, ready_json.text
    assert ready_yaml.status_code == 200, ready_yaml.text
    assert ready_firefox.status_code == 200, ready_firefox.text

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    archived_suffix_json = client.get(f"/api/export/profiles/{profile_id}.json")
    archived_suffix_yaml = client.get(f"/api/export/profiles/{profile_id}.yaml")
    archived_query_json = client.get(f"/api/export/profiles/{profile_id}?fmt=json")
    archived_query_yaml = client.get(f"/api/export/profiles/{profile_id}?fmt=yaml")
    archived_firefox = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert archived_suffix_json.status_code == 200, archived_suffix_json.text
    assert archived_suffix_yaml.status_code == 200, archived_suffix_yaml.text
    assert archived_query_json.status_code == 404
    assert archived_query_yaml.status_code == 404
    assert archived_firefox.status_code == 404

    archived_json_with_deleted = client.get(
        f"/api/export/profiles/{profile_id}?fmt=json&include_deleted=true"
    )
    archived_yaml_with_deleted = client.get(
        f"/api/export/profiles/{profile_id}?fmt=yaml&include_deleted=true"
    )
    archived_firefox_with_deleted = client.get(
        f"/api/export/profiles/{profile_id}/firefox/policies.json?include_deleted=true"
    )
    assert archived_json_with_deleted.status_code == 200, archived_json_with_deleted.text
    assert archived_yaml_with_deleted.status_code == 200, archived_yaml_with_deleted.text
    assert archived_firefox_with_deleted.status_code == 200, archived_firefox_with_deleted.text

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200, restore_response.text

    restored_json = client.get(f"/api/export/profiles/{profile_id}.json")
    restored_firefox = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert restored_json.status_code == 200, restored_json.text
    assert restored_firefox.status_code == 200, restored_firefox.text
