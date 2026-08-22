"""Chromium proof that AMO failures never block manual extension administration."""

from __future__ import annotations

import uuid

import pytest
import requests

from tests.browser.harness import (
    build_chromium_driver,
    close_chromium_driver,
    scoped_test_app_server,
)

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]


def test_amo_5xx_fallback_focuses_manual_entry_and_manual_rule_saves_and_reopens():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    guid = "manual-fallback@example.test"
    install_url = "https://example.test/manual-fallback.xpi"
    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M7-06 manual {uuid.uuid4().hex}",
                "target_schema_id": "release-153",
                "starter_id": "basic_corporate",
                "cis_baseline_id": "none",
                "preparation_idempotency_key": uuid.uuid4().hex,
            },
            timeout=10,
        )
        assert created.status_code == 201, created.text
        profile_id = created.json()["id"]

        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=extensions")
            wait.until(
                ec.presence_of_element_located((by.By.ID, "wizard-extension-amo-search-form"))
            )
            driver.execute_script(
                """
                window.__amoFallbackCalls = [];
                const realFetch = window.fetch.bind(window);
                window.fetch = (url, options) => {
                  if (!String(url).includes("/api/profiles/extensions/amo-search")) {
                    return realFetch(url, options);
                  }
                  window.__amoFallbackCalls.push(String(url));
                  return Promise.resolve(new Response("provider outage", {
                    status: 503,
                    headers: {"Content-Type": "text/plain"}
                  }));
                };
                """
            )

            driver.find_element(by.By.ID, "wizard-extension-amo-query").send_keys("unavailable")
            driver.find_element(by.By.ID, "wizard-extension-amo-search-submit").click()
            recovery = wait.until(
                ec.visibility_of_element_located((by.By.ID, "wizard-extension-amo-manual-focus"))
            )
            assert (
                "unavailable"
                in driver.find_element(by.By.ID, "wizard-extension-amo-search-status").text.lower()
            )
            driver.execute_script("arguments[0].click();", recovery)
            wait.until(
                lambda current_driver: (
                    current_driver.switch_to.active_element.get_attribute("id")
                    == "wizard-extension-rule-guid"
                )
            )

            manual_guid = driver.find_element(by.By.ID, "wizard-extension-rule-guid")
            manual_url = driver.find_element(by.By.ID, "wizard-extension-rule-install-url")
            manual_guid.send_keys(guid)
            manual_url.send_keys(install_url)
            # The long editor shell keeps its fixed action dock over this
            # button in headless Chromium. The focused DOM contract covers
            # native semantics; invoke the same listener directly here.
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(by.By.ID, "wizard-extension-rule-add"),
            )
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'[data-extension-rule="{guid}"]')
                )
            )
            assert (
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    f'[data-extension-rule="{guid}"] [data-extension-rule-field="install_url"]',
                ).get_attribute("value")
                == install_url
            )
            wait.until(
                lambda current_driver: (
                    "signal-chip--dirty"
                    in current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                        "class"
                    )
                )
            )

            driver.execute_script("arguments[0].click();", driver.find_element(by.By.ID, "save"))
            wait.until(
                lambda current_driver: (
                    "signal-chip--saved"
                    in current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                        "class"
                    )
                )
            )
            saved = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
            assert saved.status_code == 200, saved.text
            assert saved.json()["flags"]["ExtensionSettings"][guid]["install_url"] == install_url

            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=extensions")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'[data-extension-rule="{guid}"]')
                )
            )
            assert (
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    f'[data-extension-rule="{guid}"] [data-extension-rule-field="install_url"]',
                ).get_attribute("value")
                == install_url
            )
            assert driver.execute_script("return window.__amoFallbackCalls || []") == []
        finally:
            close_chromium_driver(driver)
