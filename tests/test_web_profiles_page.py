from app.main import app
from tests.support import TestClient


def test_profiles_page_renders_html_and_security_headers():
    client = TestClient(app)

    response = client.get("/profiles")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Profiles Editor" in response.text
    assert "/api/profiles" in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers


def test_i18n_and_static_assets_are_served():
    client = TestClient(app)

    locale_response = client.get("/i18n/en.json")
    assert locale_response.status_code == 200
    assert locale_response.headers["content-type"].startswith("application/json")
    assert locale_response.json()["profiles.title"] == "Profiles Editor"

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
