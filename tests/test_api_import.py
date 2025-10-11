import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_import_from_body_dict():
    payload = {"policies": {"DisableTelemetry": True}}
    r = client.post("/api/import-policies", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["policies"] == {"DisableTelemetry": True}


def test_api_import_from_json_string():
    payload = {"DisableTelemetry": True}
    r = client.post("/api/import-policies", json=json.dumps(payload))
    assert r.status_code == 200, r.text
    assert r.json()["policies"] == {"DisableTelemetry": True}
