from fastapi.testclient import TestClient

from app.main import app


def test_app_starts_and_root_responds_ok():
    """
    Smoke test to ensure the FastAPI application starts correctly
    and the root endpoint returns a valid JSON payload.
    """
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200, "Root endpoint must return HTTP 200"

    data = response.json()
    assert isinstance(data, dict), "Response must be a JSON object"
    assert data.get("status") == "ok", "Root response must include status=ok"
    assert "app" in data, "Root response must include the app name"
    assert isinstance(data["app"], str) and data["app"], "App name must be a non-empty string"
