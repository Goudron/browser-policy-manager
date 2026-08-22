"""Deterministic BPM096-M7-08 Chromium coverage for the Extensions step."""

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


_ACTIVE_SCHEMAS = ("release-153", "esr-153.0", "esr-140.13", "esr-115.39")
_FAKE_AMO_GUID = "m7-fake-amo@example.test"


def _prepare_profile(base_url: str, schema_id: str) -> int:
    response = requests.post(
        f"{base_url}/api/profiles/prepare/new",
        json={
            "name": f"M7-08 {schema_id} {uuid.uuid4().hex}",
            "target_schema_id": schema_id,
            "starter_id": "blank",
            "cis_baseline_id": "none",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _install_fake_amo(driver) -> None:
    """Intercept only the same-origin AMO endpoint before each editor loads."""

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                (() => {
                  const realFetch = window.fetch.bind(window);
                  window.__m7AmoSearchCalls = [];
                  window.fetch = (input, options) => {
                    const url = String(typeof input === "string" ? input : input?.url || "");
                    if (!url.includes("/api/profiles/extensions/amo-search")) {
                      return realFetch(input, options);
                    }
                    window.__m7AmoSearchCalls.push(url);
                    return Promise.resolve(new Response(JSON.stringify({
                      availability: "available",
                      reason_code: "available",
                      results: [{
                        guid: "m7-fake-amo@example.test",
                        name: "<img src=x onerror=alert(1)> M7 fake",
                        version: "1.2.3",
                        url: "https://attacker.invalid/never-followed.xpi",
                        description: "<a href=https://attacker.invalid>never rendered</a>"
                      }],
                      cache_hit: false
                    }), { status: 200, headers: { "Content-Type": "application/json" } }));
                  };
                })();
            """,
        },
    )


def test_fake_amo_selection_round_trips_every_active_schema_without_background_lookup():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            _install_fake_amo(driver)
            for schema_id in _ACTIVE_SCHEMAS:
                profile_id = _prepare_profile(base_url, schema_id)
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
                assert driver.execute_script("return window.__m7AmoSearchCalls") == []

                query = driver.find_element(by.By.ID, "wizard-extension-amo-query")
                query.send_keys("M7 fake", keys.Keys.ENTER)
                result = wait.until(
                    ec.presence_of_element_located(
                        (by.By.CSS_SELECTOR, "#wizard-extension-amo-search-results [role=listitem]")
                    )
                )
                assert "<img src=x onerror=alert(1)> M7 fake" in result.text
                assert not result.find_elements(by.By.CSS_SELECTOR, "a, img")
                assert driver.execute_script("return window.__m7AmoSearchCalls") == [
                    "/api/profiles/extensions/amo-search?q=M7%20fake&locale=en"
                ]

                driver.execute_script(
                    "arguments[0].click();", result.find_element(by.By.TAG_NAME, "button")
                )
                wait.until(
                    ec.presence_of_element_located(
                        (by.By.CSS_SELECTOR, f'[data-extension-rule="{_FAKE_AMO_GUID}"]')
                    )
                )
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
                assert driver.execute_script("return window.__m7AmoSearchCalls") == [
                    "/api/profiles/extensions/amo-search?q=M7%20fake&locale=en"
                ]

                saved = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
                exported = requests.get(
                    f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json", timeout=10
                )
                assert saved.status_code == exported.status_code == 200
                assert saved.json()["flags"]["ExtensionSettings"][_FAKE_AMO_GUID] == {
                    "installation_mode": "allowed"
                }
                assert (
                    saved.json()["extension_provenance"]["paths"][
                        f"/ExtensionSettings/{_FAKE_AMO_GUID}/installation_mode"
                    ]
                    == "amo-assisted-manual"
                )
                assert exported.json() == {"policies": saved.json()["flags"]}

                driver.get(f"{base_url}/profiles/{profile_id}/edit?step=extensions")
                wait.until(
                    ec.presence_of_element_located(
                        (by.By.CSS_SELECTOR, f'[data-extension-rule="{_FAKE_AMO_GUID}"]')
                    )
                )
                assert driver.execute_script("return window.__m7AmoSearchCalls") == []
        finally:
            close_chromium_driver(driver)


def test_newer_amo_result_wins_a_cancelled_lookup_race():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        profile_id = _prepare_profile(base_url, "release-153")
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        (() => {
                          const realFetch = window.fetch.bind(window);
                          window.__m7RaceCalls = [];
                          window.__m7ResolveSlow = null;
                          window.fetch = (input, options) => {
                            const url = String(typeof input === "string" ? input : input?.url || "");
                            if (!url.includes("/api/profiles/extensions/amo-search")) {
                              return realFetch(input, options);
                            }
                            window.__m7RaceCalls.push(url);
                            const result = (guid) => new Response(JSON.stringify({
                              availability: "available",
                              reason_code: "available",
                              results: [{ guid, name: guid, version: "1.0" }],
                              cache_hit: false
                            }), { status: 200, headers: { "Content-Type": "application/json" } });
                            if (url.includes("q=slow")) {
                              return new Promise((resolve) => { window.__m7ResolveSlow = () => resolve(result("slow@example.test")); });
                            }
                            return Promise.resolve(result("fresh@example.test"));
                          };
                        })();
                    """,
                },
            )
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=extensions")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-extension-amo-query")))
            query = driver.find_element(by.By.ID, "wizard-extension-amo-query")
            query.send_keys("slow")
            driver.find_element(by.By.ID, "wizard-extension-amo-search-submit").click()
            wait.until(
                lambda current_driver: current_driver.execute_script(
                    "return !!window.__m7ResolveSlow"
                )
            )

            driver.execute_script("arguments[0].value = 'fresh';", query)
            search_submit = driver.find_element(by.By.ID, "wizard-extension-amo-search-submit")
            assert search_submit.is_enabled()
            search_submit.click()
            assert driver.execute_script("return window.__m7RaceCalls") == [
                "/api/profiles/extensions/amo-search?q=slow&locale=en",
                "/api/profiles/extensions/amo-search?q=fresh&locale=en",
            ]
            fresh = wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, "#wizard-extension-amo-search-results [role=listitem]")
                )
            )
            assert "fresh@example.test" in fresh.text
            driver.execute_script("window.__m7ResolveSlow();")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "wizard-extension-amo-search-submit"
                ).is_enabled()
            )
            assert (
                "fresh@example.test"
                in driver.find_element(by.By.ID, "wizard-extension-amo-search-results").text
            )
            assert (
                "slow@example.test"
                not in driver.find_element(by.By.ID, "wizard-extension-amo-search-results").text
            )
            assert driver.execute_script("return window.__m7RaceCalls") == [
                "/api/profiles/extensions/amo-search?q=slow&locale=en",
                "/api/profiles/extensions/amo-search?q=fresh&locale=en",
            ]
        finally:
            close_chromium_driver(driver)
