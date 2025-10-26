# tests/test_validation_api.py
"""
Smoke tests for validation API.

These tests do not assume specific app/main.py contents.
They use FastAPI TestClient by importing the router directly and mounting
on a temporary FastAPI instance.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.validation import router as validation_router


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(validation_router)
    return app


def test_validate_ok_minimal_object_esr140():
    app = make_app()
    client = TestClient(app)

    # Minimal object; schema likely requires object type,
    # we don't assert full shape as real schema may be complex.
    payload = {"document": {}}
    r = client.post("/api/validate/esr-140", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Either ok or not ok depending on strictness of the schema.
    # We only assert response shape here to avoid schema-coupling.
    assert "ok" in data and "profile" in data


def test_validate_rejects_non_object_release144():
    app = make_app()
    client = TestClient(app)

    payload = {"document": 123}
    r = client.post("/api/validate/release-144", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["profile"] == "release-144"
    assert data["ok"] is False
    assert isinstance(data.get("detail"), str)
