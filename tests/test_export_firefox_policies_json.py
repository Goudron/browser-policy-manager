from __future__ import annotations

import json

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk_profile_body():
    return build_profile_payload(
        name_prefix="FxPol",
        description="Firefox policies export",
        flags={
            "BlockAboutConfig": True,
            "WebsiteFilter": {"Block": ["http://example.org/*"]},
        },
    )


def test_export_firefox_policies_json_returns_canonical_document():
    client = make_test_client(app)

    create_response = client.post("/api/profiles", json=_mk_profile_body())
    assert create_response.status_code == 201, create_response.text
    profile_id = create_response.json()["id"]

    response = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()
    assert payload == {
        "policies": {
            "BlockAboutConfig": True,
            "WebsiteFilter": {"Block": ["http://example.org/*"]},
        }
    }


def test_export_firefox_policies_json_supports_download_pretty_and_include_deleted():
    client = make_test_client(app)

    create_response = client.post("/api/profiles", json=_mk_profile_body())
    assert create_response.status_code == 201, create_response.text
    profile_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_response = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert hidden_response.status_code == 404

    response = client.get(
        f"/api/export/profiles/{profile_id}/firefox/policies.json"
        "?include_deleted=true&download=1&pretty=1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    content_disposition = response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition.lower()
    assert "policies.json" in content_disposition.lower()

    assert "\n  \"policies\"" in response.text
    assert json.loads(response.text)["policies"]["BlockAboutConfig"] is True


def test_export_firefox_policies_json_returns_404_for_missing_profile():
    client = make_test_client(app)

    response = client.get("/api/export/profiles/999999/firefox/policies.json")
    assert response.status_code == 404
