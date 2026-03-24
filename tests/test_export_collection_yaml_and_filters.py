from __future__ import annotations

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk_body(name_prefix: str, owner: str, schema: str):
    return build_profile_payload(
        name_prefix=name_prefix,
        owner=owner,
        schema_version=schema,
        description="Collection export",
    )


def test_export_collection_yaml_with_filters_and_sorting():
    """Covers /api/export/profiles with fmt=yaml + filters + sorting + pagination."""
    client = make_test_client(app)

    # Seed a few diverse items
    seeds = [
        _mk_body("ColA", "ops@example.org", "esr-140"),
        _mk_body("ColB", "sec@example.org", "esr-140"),
        _mk_body("ColC", "ops@example.org", "esr-140"),
    ]
    for body in seeds:
        r = client.post("/api/profiles", json=body)
        assert r.status_code == 201, r.text

    # YAML export with owner/schema filters, search query, sorting and pagination
    params = {
        "fmt": "yaml",
        "owner": "ops@example.org",
        "schema_version": "esr-140",
        "q": "Col",  # substring match in name
        "include_deleted": "false",
        "limit": 2,
        "offset": 0,
        "sort": "name",
        "order": "asc",
    }
    r = client.get("/api/export/profiles", params=params)
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
        assert "profiles.yaml" in cd.lower()
