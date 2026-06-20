from app.main import make_app
from tests.support import TestClient, make_test_client


def _make_client() -> TestClient:
    return make_test_client(make_app())


def test_validate_rejects_non_object_release152():
    client = _make_client()

    payload = {"document": 123}
    response = client.post("/api/validate/release-152", json=payload)

    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_validate_profile_ok_and_fail():
    client = _make_client()

    good = {"document": {"DisableTelemetry": True}}
    bad = {"document": 123}

    for profile in ("esr-140.12", "release-152"):
        ok_response = client.post(f"/api/validate/{profile}", json=good)
        assert ok_response.status_code == 200, ok_response.text
        assert ok_response.json() == {"ok": True, "profile": profile}

        bad_response = client.post(f"/api/validate/{profile}", json=bad)
        assert bad_response.status_code == 200
        bad_body = bad_response.json()
        assert bad_body["ok"] is False
        assert bad_body["profile"] == profile


def test_validate_accepts_search_bar_enum_values():
    client = _make_client()

    for profile in ("esr-140.12", "release-152"):
        for value in ("unified", "separate"):
            response = client.post(f"/api/validate/{profile}", json={"document": {"SearchBar": value}})

            assert response.status_code == 200, response.text
            assert response.json() == {"ok": True, "profile": profile}


def test_validate_accepts_search_engines_add_payload():
    client = _make_client()
    document = {
        "SearchEngines": {
            "Add": [
                {
                    "Name": "Example Search",
                    "URLTemplate": "https://www.example.org/search?q={searchTerms}",
                    "Method": "GET",
                    "Alias": "example",
                    "SuggestURLTemplate": "https://www.example.org/suggest?q={searchTerms}",
                }
            ]
        }
    }

    for profile in ("esr-140.12", "release-152"):
        response = client.post(f"/api/validate/{profile}", json={"document": document})

        assert response.status_code == 200, response.text
        assert response.json() == {"ok": True, "profile": profile}


def test_validate_accepts_preferences_payload():
    client = _make_client()
    document = {
        "Preferences": {
            "browser.tabs.warnOnClose": {
                "Value": True,
                "Status": "locked",
                "Type": "boolean",
            }
        }
    }

    for profile in ("esr-140.12", "release-152"):
        response = client.post(f"/api/validate/{profile}", json={"document": document})

        assert response.status_code == 200, response.text
        assert response.json() == {"ok": True, "profile": profile}


def test_validate_rejects_invalid_nested_enum_values():
    client = _make_client()

    response = client.post(
        "/api/validate/release-152",
        json={
            "document": {
                "Proxy": {
                    "Mode": "bogus",
                }
            }
        },
    )

    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["message"] == "Policy validation failed"
    assert detail["issues"][0]["path"] == ["Proxy", "Mode"]


def test_validate_rejects_preferences_type_mismatch():
    client = _make_client()

    response = client.post(
        "/api/validate/release-152",
        json={
            "document": {
                "Preferences": {
                    "browser.tabs.warnOnClose": {
                        "Value": "false",
                        "Status": "locked",
                        "Type": "boolean",
                    }
                }
            }
        },
    )

    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["message"] == "Policy validation failed"
    assert detail["issues"][0]["path"] == ["Preferences", "browser.tabs.warnOnClose", "Value"]
