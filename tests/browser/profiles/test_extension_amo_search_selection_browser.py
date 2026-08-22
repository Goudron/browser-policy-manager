"""Chromium acceptance for BPM096-M7-04's explicit inert AMO search handoff."""

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


def test_extension_amo_search_needs_submit_and_selection_creates_an_inert_guid_rule():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M7-04 AMO {uuid.uuid4().hex}",
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
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "extensions"
                )
            )
            driver.execute_script(
                """
                window.__amoSearchCalls = [];
                window.fetch = (url) => {
                  window.__amoSearchCalls.push(String(url));
                  return Promise.resolve(new Response(JSON.stringify({
                    availability: "available",
                    reason_code: "available",
                    results: [{
                      guid: "uBlock0@raymondhill.net",
                      name: "<img src=x onerror=alert(1)> uBlock",
                      version: "1.2.3"
                    }],
                    cache_hit: false
                  }), {status: 200, headers: {"Content-Type": "application/json"}}));
                };
                """
            )

            query = driver.find_element(by.By.ID, "wizard-extension-amo-query")
            query.send_keys("uBlock")
            assert driver.execute_script("return window.__amoSearchCalls.length") == 0

            driver.find_element(by.By.ID, "wizard-extension-amo-search-submit").click()
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, "#wizard-extension-amo-search-results [role=listitem]")
                )
            )
            result = driver.find_element(
                by.By.CSS_SELECTOR, "#wizard-extension-amo-search-results [role=listitem]"
            )
            assert "<img src=x onerror=alert(1)> uBlock" in result.text
            assert not result.find_elements(by.By.CSS_SELECTOR, "img, a")
            assert driver.execute_script("return window.__amoSearchCalls") == [
                "/api/profiles/extensions/amo-search?q=uBlock&locale=en"
            ]

            select_action = result.find_element(by.By.TAG_NAME, "button")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_action)
            # The long editor shell keeps its action dock above this result in
            # headless Chromium. Invoke the native button handler directly;
            # its keyboard/native semantics are asserted by the focused DOM
            # contract and this probe verifies the state handoff itself.
            driver.execute_script("arguments[0].click();", select_action)
            wait.until(
                ec.presence_of_element_located(
                    (
                        by.By.CSS_SELECTOR,
                        '[data-extension-amo-rule="uBlock0@raymondhill.net"] '
                        'select[data-extension-amo-rule-mode="uBlock0@raymondhill.net"]',
                    )
                )
            )
            selected = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-extension-amo-rule="uBlock0@raymondhill.net"]',
            )
            assert "uBlock0@raymondhill.net" in selected.text
            assert not selected.find_elements(by.By.CSS_SELECTOR, "a, img")

        finally:
            close_chromium_driver(driver)
