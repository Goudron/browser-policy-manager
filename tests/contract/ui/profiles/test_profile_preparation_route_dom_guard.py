"""Rendered DOM and locale guard for the M4 preparation route."""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.main import app
from tests.support import make_test_client

ALL_LOCALES = ("en", "ru", "de", "es-ES", "fr", "zh-CN")
FIELDS = (
    ("profile-preparation-name", "profiles.preparation_name_label"),
    ("profile-preparation-schema", "profiles.preparation_schema_label"),
    ("profile-preparation-starter", "profiles.preparation_starter_label"),
    ("profile-preparation-cis", "profiles.preparation_cis_label"),
)


def test_preparation_form_uses_one_keyboard_native_error_association_in_every_locale() -> None:
    client = make_test_client(app)

    for locale in ALL_LOCALES:
        response = client.get("/profiles/new", headers={"Accept-Language": locale})
        catalog = client.get(f"/i18n/{locale}.json").json()
        assert response.status_code == 200, response.text
        soup = BeautifulSoup(response.text, "html.parser")

        assert soup.html is not None
        assert soup.html.get("lang") == locale
        main = soup.find("main", id="profile-preparation")
        assert main is not None
        assert main.get("aria-labelledby") == "profile-preparation-title"

        form = soup.find("form", id="profile-preparation-form")
        assert form is not None
        assert form.get("data-preparation-form-state") == "ready"
        assert [element.get("id") for element in form.select("input, select, button")] == [
            *[field_id for field_id, _key in FIELDS],
            "profile-preparation-submit",
        ]

        for field_id, label_key in FIELDS:
            control = form.find(id=field_id)
            label = form.find("label", attrs={"for": field_id})
            error = form.find(id=f"{field_id}-error")
            assert control is not None
            assert label is not None
            assert error is not None
            assert label.get_text(strip=True) == catalog[label_key]
            assert control.get("aria-errormessage") == error.get("id")
            assert error.get("role") == "alert"
            assert error.has_attr("hidden")
            assert error.get("id") in (control.get("aria-describedby") or "").split()

        state = form.find(id="profile-preparation-state")
        action = form.find(id="profile-preparation-submit")
        action_error = form.find(id="profile-preparation-action-error")
        assert state is not None
        assert state.get("role") == "status"
        assert state.get("aria-live") == "polite"
        assert state.get("aria-atomic") == "true"
        assert action is not None
        assert action.get_text(strip=True) == catalog["profiles.preparation_create_action"]
        assert action_error is not None
        assert action_error.get("role") == "alert"
        assert action_error.has_attr("hidden")
        assert action_error.get("id") in (action.get("aria-describedby") or "").split()
