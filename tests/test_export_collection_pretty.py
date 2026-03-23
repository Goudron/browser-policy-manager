from __future__ import annotations

from app.main import app
from tests.support import TestClient, build_profile_payload


def test_collection_export_pretty_defaults_to_indented_json():
    client = TestClient(app)
    create = client.post(
        "/api/profiles",
        json=build_profile_payload(name_prefix="Pretty", description="Pretty export"),
    )
    assert create.status_code == 201, create.text

    response = client.get("/api/export/profiles", params={"pretty": 1})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert '\n  "items"' in response.text
