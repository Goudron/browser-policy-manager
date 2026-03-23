from app.main import make_app
from tests.support import TestClient


def _make_client() -> TestClient:
    return TestClient(make_app())


def test_validate_rejects_non_object_release145():
    client = _make_client()

    payload = {"document": 123}
    response = client.post("/api/validate/release-145", json=payload)

    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_validate_profile_ok_and_fail():
    client = _make_client()

    good = {"document": {"DisableTelemetry": True}}
    bad = {"document": 123}

    for profile in ("esr-140", "release-145"):
        ok_response = client.post(f"/api/validate/{profile}", json=good)
        assert ok_response.status_code == 200, ok_response.text
        assert ok_response.json() == {"ok": True, "profile": profile}

        bad_response = client.post(f"/api/validate/{profile}", json=bad)
        assert bad_response.status_code == 200
        bad_body = bad_response.json()
        assert bad_body["ok"] is False
        assert bad_body["profile"] == profile
