"""Browser proof that retained Guided controls follow the M6 topology."""

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


def test_guided_non_domain_controls_keep_their_semantic_step_and_search_owner():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M6-03 non-domain {uuid.uuid4().hex}",
                "target_schema_id": "release-153",
                "starter_id": "basic_corporate",
                "cis_baseline_id": "cis_l2",
                "preparation_idempotency_key": uuid.uuid4().hex,
            },
            timeout=10,
        )
        assert created.status_code == 201, created.text
        profile_id = created.json()["id"]

        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))

            expected_targets = {
                "browser_network_search": "wizard-search-default-engine",
                "security_privacy": "wizard-permissions-card",
                "users_language_sync": "wizard-requested-locales-card",
                "ai": "wizard-ai-controls-card",
                "review_export": "wizard-export-ready-card",
            }
            for step_id, target_id in expected_targets.items():
                step_button = driver.find_element(
                    by.By.CSS_SELECTOR, f'.wizard-step[data-step-id="{step_id}"]'
                )
                driver.execute_script("arguments[0].click();", step_button)
                wait.until(
                    lambda current_driver, expected_step=step_id: (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                        ).get_attribute("data-step-id")
                        == expected_step
                    )
                )
                target = driver.find_element(by.By.ID, target_id)
                assert (
                    target.find_element(
                        by.By.XPATH, "ancestor::section[contains(@class, 'wizard-panel')]"
                    ).get_attribute("data-wizard-step-id")
                    == step_id
                )

            search_input = driver.find_element(by.By.ID, "wizard-settings-search-input")
            search_input.clear()
            search_input.send_keys("default search engine")
            target_selector = '[data-settings-search-target="field:wizard-search-default-engine"]'
            wait.until(
                lambda current_driver: current_driver.find_elements(
                    by.By.CSS_SELECTOR, target_selector
                )
            )
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(by.By.CSS_SELECTOR, target_selector),
            )
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "browser_network_search"
                )
            )
            assert (
                driver.find_element(by.By.ID, "wizard-search-default-engine")
                .find_element(by.By.XPATH, "ancestor::section[contains(@class, 'wizard-panel')]")
                .get_attribute("data-wizard-step-id")
                == "browser_network_search"
            )
        finally:
            close_chromium_driver(driver)
