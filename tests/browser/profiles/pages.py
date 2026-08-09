"""Semantic page operations shared by profile and documentation browser flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from tests.browser.harness import BrowserPage
from tests.support import build_profile_payload

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ProfilesPage(BrowserPage):
    @staticmethod
    def load_locale_catalog(locale: str) -> dict[str, str]:
        catalog_path = PROJECT_ROOT / "app" / "i18n" / f"{locale}.json"
        return json.loads(catalog_path.read_text(encoding="utf-8"))

    @staticmethod
    def create_profile(base_url: str, *, name: str, flags: dict[str, Any] | None = None) -> int:
        response = requests.post(
            f"{base_url}/api/profiles",
            json=build_profile_payload(
                name=name,
                description="Chromium smoke profile",
                schema_version="release-153",
                flags=flags
                or {
                    "DisableTelemetry": True,
                    "Homepage": {
                        "URL": "https://portal.example.local/",
                        "Locked": True,
                    },
                },
            ),
            timeout=10,
        )
        assert response.status_code == 201, response.text
        return int(response.json()["id"])

    def set_locale(self, wait: Any, ui: Any, *, locale: str, expected_text: str) -> None:
        select = ui.Select(
            wait.until(lambda current_driver: current_driver.find_element("id", "lang"))
        )
        select.select_by_value(locale)
        wait.until(
            lambda current_driver: (
                current_driver.execute_script("return document.documentElement.lang;") == locale
            )
        )
        wait.until(lambda _current_driver: expected_text in self.body_text())


load_locale_catalog = ProfilesPage.load_locale_catalog
create_profile = ProfilesPage.create_profile


def set_locale(driver: Any, wait: Any, ui: Any, *, locale: str, expected_text: str) -> None:
    ProfilesPage(driver).set_locale(wait, ui, locale=locale, expected_text=expected_text)
