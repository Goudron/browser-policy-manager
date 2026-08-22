"""Deterministic BPM096-M8-06 Chromium proof for the Guided URL workflow."""

from __future__ import annotations

import uuid

import pytest
import requests

from tests.browser.harness import (
    build_chromium_driver,
    close_chromium_driver,
    scoped_test_app_server,
)
from tests.browser.profiles.pages import load_locale_catalog, set_locale

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]


_ACTIVE_SCHEMAS = ("release-153", "esr-153.0", "esr-140.13", "esr-115.39")


def _url_flags() -> dict[str, object]:
    return {
        "Homepage": {
            "URL": "https://portal.example.test/",
            "Additional": ["https://help.example.test/"],
            "StartPage": "homepage",
            "Locked": True,
        },
        "WebsiteFilter": {
            "Block": ["https://blocked.example.test/*"],
            "Exceptions": ["https://allowed.example.test/*"],
        },
        "Handlers": {
            "schemes": {
                "mailto": {
                    "action": "useHelperApp",
                    "ask": False,
                    "handlers": [
                        {
                            "name": "M8 mail",
                            "uriTemplate": "https://mail.example.test/compose?to=%s",
                        }
                    ],
                }
            }
        },
        "Bookmarks": [
            {
                "Title": "M8 bookmark",
                "URL": "https://bookmark.example.test/",
                "Placement": "toolbar",
            }
        ],
        "ManagedBookmarks": [
            {
                "toplevel_name": "M8 managed",
                "children": [{"name": "M8 link", "url": "https://managed.example.test/"}],
            }
        ],
    }


def _prepare_profile(base_url: str, schema_id: str) -> dict[str, object]:
    created = requests.post(
        f"{base_url}/api/profiles/prepare/new",
        json={
            "name": f"M8-06 URL workflow {schema_id} {uuid.uuid4().hex}",
            "target_schema_id": schema_id,
            "starter_id": "blank",
            "cis_baseline_id": "none",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
        timeout=10,
    )
    assert created.status_code == 201, created.text
    profile = created.json()
    saved = requests.patch(
        f"{base_url}/api/profiles/{profile['id']}",
        json={"flags": _url_flags(), "expected_revision": profile["revision"]},
        timeout=10,
    )
    assert saved.status_code == 200, saved.text
    return saved.json()


def _assert_no_horizontal_overflow(driver) -> None:
    metrics = driver.execute_script(
        """
        return {
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
        };
        """
    )
    assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics


def test_url_step_edits_reviews_and_round_trips_in_every_active_schema():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            for schema_id in _ACTIVE_SCHEMAS:
                profile = _prepare_profile(base_url, schema_id)
                profile_id = profile["id"]
                driver.set_window_size(1280, 1000)
                driver.get(f"{base_url}/profiles/{profile_id}/edit?step=urls_sites_navigation")
                wait.until(ec.presence_of_element_located((by.By.ID, "wizard-homepage-url")))
                wait.until(
                    lambda current_driver: (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                        ).get_attribute("data-step-id")
                        == "urls_sites_navigation"
                    )
                )

                homepage = driver.find_element(by.By.ID, "wizard-homepage-url")
                assert homepage.get_attribute("value") == "https://portal.example.test/"
                website_filter = driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-schema-policy-card][data-schema-policy-id="WebsiteFilter"]',
                )
                assert website_filter.get_attribute("data-schema-policy-kind") == "website-filter"
                assert (
                    len(
                        website_filter.find_elements(
                            by.By.CSS_SELECTOR, "[data-website-filter-row]"
                        )
                    )
                    == 2
                )
                for field in ("Block", "Exceptions"):
                    assert website_filter.find_element(
                        by.By.CSS_SELECTOR, f'[data-website-filter-list="{field}"]'
                    )

                # The progressive managed-navigation group contains the live,
                # schema-specific handler and bookmark editors on the same
                # step, not a copied legacy step-five handoff.
                driver.execute_script(
                    "arguments[0].click();",
                    driver.find_element(by.By.ID, "wizard-managed-navigation-toggle"),
                )
                wait.until(
                    ec.presence_of_element_located(
                        (by.By.CSS_SELECTOR, '[data-schema-policy-id="Handlers"]')
                    )
                )
                for policy_id in ("Handlers", "Bookmarks", "ManagedBookmarks"):
                    card = driver.find_element(
                        by.By.CSS_SELECTOR, f'[data-schema-policy-id="{policy_id}"]'
                    )
                    assert (
                        card.find_element(
                            by.By.XPATH,
                            "ancestor::section[contains(@class, 'wizard-panel')]",
                        ).get_attribute("data-wizard-step-id")
                        == "urls_sites_navigation"
                    )

                stale_counts = driver.execute_script(
                    """
                    return {
                      oldHomepage: document.querySelectorAll(
                        '[data-wizard-step-id="browser_network_search"] #wizard-homepage-url'
                      ).length,
                      oldNavigation: document.querySelectorAll(
                        '[data-wizard-step-id="users_language_sync"] '
                        + '[data-settings-target="policy:Handlers"], '
                        + '[data-wizard-step-id="users_language_sync"] '
                        + '[data-settings-target="policy:Bookmarks"], '
                        + '[data-wizard-step-id="users_language_sync"] '
                        + '[data-settings-target="policy:ManagedBookmarks"]'
                      ).length,
                    };
                    """
                )
                assert stale_counts == {"oldHomepage": 0, "oldNavigation": 0}

                # Real typed UI editing must persist an exact new allow entry.
                driver.execute_script(
                    "arguments[0].click();",
                    website_filter.find_element(
                        by.By.CSS_SELECTOR, '[data-website-filter-add="Exceptions"]'
                    ),
                )
                new_allow = website_filter.find_elements(
                    by.By.CSS_SELECTOR,
                    '[data-website-filter-rows="Exceptions"] [data-website-filter-pattern]',
                )[-1]
                new_allow.send_keys("https://new-allowed.example.test/*", keys.Keys.TAB)
                driver.execute_script(
                    "arguments[0].click();", driver.find_element(by.By.ID, "save")
                )
                wait.until(
                    lambda current_driver: (
                        "signal-chip--saved"
                        in current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                            "class"
                        )
                    )
                )
                saved = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
                exported = requests.get(
                    f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json",
                    timeout=10,
                )
                assert saved.status_code == exported.status_code == 200
                assert saved.json()["flags"]["WebsiteFilter"]["Exceptions"] == [
                    "https://allowed.example.test/*",
                    "https://new-allowed.example.test/*",
                ]
                assert exported.json() == {"policies": saved.json()["flags"]}

                # Final review's URLs jump returns to the one real owner.
                driver.get(f"{base_url}/profiles/{profile_id}/edit?step=review_export")
                wait.until(ec.presence_of_element_located((by.By.ID, "wizard-export-ready-card")))
                urls_jump = driver.find_element(by.By.ID, "wizard-export-summary-urls-jump")
                assert urls_jump.is_enabled()
                driver.execute_script("arguments[0].click();", urls_jump)
                wait.until(
                    lambda current_driver: (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                        ).get_attribute("data-step-id")
                        == "urls_sites_navigation"
                    )
                )
                assert driver.find_element(by.By.ID, "wizard-homepage-url")

            # The narrow surface must remain usable with localized copy.  A
            # full locale matrix is deliberately independent of schema choice.
            driver.set_window_size(320, 860)
            for locale in ("ru", "de", "zh-CN", "fr", "es-ES", "en"):
                catalog = load_locale_catalog(locale)
                set_locale(
                    driver,
                    wait,
                    ui,
                    locale=locale,
                    expected_text=catalog["profiles.wizard_step_two"],
                )
                active = driver.find_element(by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]")
                assert active.get_attribute("data-step-id") == "urls_sites_navigation"
                assert driver.find_element(by.By.ID, "wizard-website-filter-card")
                _assert_no_horizontal_overflow(driver)
        finally:
            close_chromium_driver(driver)


def test_imported_raw_website_filter_pattern_is_visible_and_never_coerced_by_the_url_step():
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    raw_filter = {"Block": ["javascript:alert(1)"], "Exceptions": []}
    with scoped_test_app_server() as base_url:
        imported = requests.post(
            f"{base_url}/api/profiles/import/firefox/policies.json",
            json={
                "name": f"M8-06 raw URL import {uuid.uuid4().hex}",
                "schema_version": "release-153",
                "document": {"policies": {"WebsiteFilter": raw_filter}},
            },
            timeout=10,
        )
        assert imported.status_code == 201, imported.text
        profile_id = imported.json()["id"]

        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        window.__m8RawUrlAlerts = 0;
                        window.alert = () => { window.__m8RawUrlAlerts += 1; };
                    """
                },
            )
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=urls_sites_navigation")
            raw_pattern = wait.until(
                lambda current_driver: current_driver.execute_script(
                    """
                    const row = document.querySelector('.wizard-website-filter-row--raw');
                    const input = row?.querySelector('[data-website-filter-pattern]');
                    const message = row?.querySelector('[data-website-filter-row-message]');
                    return input?.value === 'javascript:alert(1)'
                      ? { value: input.value, message: message?.textContent?.trim() || '' }
                      : null;
                    """
                )
            )
            assert raw_pattern["value"] == "javascript:alert(1)"
            assert raw_pattern["message"]
            assert driver.execute_script("return window.__m8RawUrlAlerts") == 0

            exported = requests.get(
                f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json",
                timeout=10,
            )
            assert exported.status_code == 200, exported.text
            assert exported.json() == {"policies": {"WebsiteFilter": raw_filter}}
        finally:
            close_chromium_driver(driver)
