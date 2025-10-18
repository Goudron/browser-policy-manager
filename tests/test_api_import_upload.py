import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_import_policies_via_file_multipart_ok():
    sample = {
        "policies": {
            "DisableTelemetry": True,
            "Preferences": {"browser.startup.homepage": "https://example.org"},
        }
    }
    import json

    payload = json.dumps(sample).encode("utf-8")

    files = {"file": ("policies.json", io.BytesIO(payload), "application/json")}
    r = client.post("/api/import-policies", files=files)
    assert r.status_code == 200, r.text

    data = r.json()
    assert "policies" in data
    assert data["policies"]["DisableTelemetry"] is True
    assert (
        data["policies"]["Preferences"]["browser.startup.homepage"]
        == "https://example.org"
    )
    # допускаем пустые warnings на корректном json
    assert isinstance(data.get("warnings", []), list)


def test_import_policies_via_file_multipart_bad_json():
    bad_payload = b"{ not-a-json ]"
    files = {"file": ("policies.json", io.BytesIO(bad_payload), "application/json")}
    r = client.post("/api/import-policies", files=files)
    assert r.status_code == 400
    # сервер должен вернуть detail с описанием ошибки
    resp = r.json()
    assert "detail" in resp
