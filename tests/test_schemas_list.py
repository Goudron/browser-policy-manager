from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_schemas_endpoint_ok():
    r = client.get("/api/v1/schemas")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    # Должна быть хотя бы одна схема (release или esr)
    assert len(data["items"]) >= 1
    # Каждый элемент должен иметь channel и version
    for item in data["items"]:
        assert "channel" in item
        assert "version" in item
