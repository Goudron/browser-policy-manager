from fastapi.testclient import TestClient

from app.main import app


def test_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    # Новые проверки под актуальный index.html:
    assert "Valery Ledovskoy" in r.text
    assert '/profiles' in r.text  # ссылка на раздел профилей
