from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.schema_service import available

client = TestClient(app)


def test_schema_service_available_not_empty():
    # Сервис должен вернуть хотя бы одну доступную схему
    avail = available()
    assert isinstance(avail, dict)
    assert len(avail) >= 1


def test_validate_rejects_invalid_doc():
    # Заведомо некорректный документ (почти пустой) должен быть отклонён
    r = client.post("/api/v1/policies/validate", json={})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data
    # Наш эндпоинт возвращает структуру с message/error
    detail = data["detail"]
    assert isinstance(detail, dict)
    assert "message" in detail
    assert "error" in detail
