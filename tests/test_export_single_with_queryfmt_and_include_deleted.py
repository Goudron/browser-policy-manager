from __future__ import annotations

from app.main import app
from tests.support import TestClient, build_profile_payload


def _mk_body(name_prefix: str = "XDel", owner: str | None = None):
    return build_profile_payload(
        name_prefix=name_prefix,
        owner=owner,
        description="Marked for deletion",
        flags={"DisableTelemetry": True, "DisableFirefoxAccounts": True},
    )


def test_export_single_with_query_format_and_include_deleted():
    """Covers /api/export/profiles/{id}?fmt={json|yaml}&include_deleted=true."""
    client = TestClient(app)

    # Create a profile
    r = client.post("/api/profiles", json=_mk_body(owner="ops@example.org"))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Soft delete it so default lookups would hide it
    rdel = client.delete(f"/api/profiles/{pid}")
    assert rdel.status_code in (204, 200)

    # Export with include_deleted=true and fmt=yaml (query-param format)
    ry = client.get(f"/api/export/profiles/{pid}?fmt=yaml&include_deleted=true")
    assert ry.status_code == 200
    assert "DisableTelemetry" in ry.text
    # YAML content type variations allowed
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/plain", "text/yaml")
    )
    # Content-Disposition should name a YAML file (if header is present)
    cd = ry.headers.get("content-disposition", "")
    if cd:
        assert cd.lower().startswith("attachment;")
        assert cd.lower().endswith('.yaml"') or ".yaml" in cd.lower()

    # Export same item as JSON using query fmt
    rj = client.get(f"/api/export/profiles/{pid}?fmt=json&include_deleted=true")
    assert rj.status_code == 200
    assert '"DisableTelemetry"' in rj.text
    assert rj.headers.get("content-type", "").startswith("application/json")
    cdj = rj.headers.get("content-disposition", "")
    if cdj:
        assert ".json" in cdj.lower()
