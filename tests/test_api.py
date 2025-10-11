from fastapi.testclient import TestClient

from app.main import app


def test_profiles_crud_and_export():
    c = TestClient(app)
    # create
    body = {
        "name": "Default",
        "description": "Base profile",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
    }
    r = c.post("/api/policies", json=body)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # list
    r = c.get("/api/policies")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    # export
    r = c.get(f"/api/export/{pid}/policies.json")
    assert r.status_code == 200
    data = r.json()
    assert "policies" in data and data["policies"]["DisableTelemetry"] is True
