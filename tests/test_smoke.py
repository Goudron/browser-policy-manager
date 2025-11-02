# tests/test_smoke.py
from fastapi.testclient import TestClient

from app.main import app


def test_root_contains_author_name():
    """Проверяем, что главная страница открывается и содержит имя автора."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Valery Ledovskoy" in response.text
