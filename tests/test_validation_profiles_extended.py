from fastapi.testclient import TestClient

from app.main import make_app


def test_validate_profile_ok_and_fail():
    app = make_app()  # создаем экземпляр приложения
    client = TestClient(app)

    good = {"document": {"DisableTelemetry": True}}
    bad = {"document": 123}  # should produce ok=False

    # ESR 140
    r1 = client.post("/api/validate/esr-140", json=good)
    assert r1.status_code == 200, r1.text
    assert r1.json()["ok"] is True

    r2 = client.post("/api/validate/esr-140", json=bad)
    assert r2.status_code == 200
    assert r2.json()["ok"] is False

    # Release 145
    r3 = client.post("/api/validate/release-145", json=good)
    assert r3.status_code == 200
    assert r3.json()["ok"] is True

    r4 = client.post("/api/validate/release-145", json=bad)
    assert r4.status_code == 200
    assert r4.json()["ok"] is False
