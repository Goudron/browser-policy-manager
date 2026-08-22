"""Browser proof for the M6-01 eight-step Guided topology."""

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


def test_guided_eight_step_topology_starts_at_browser_and_finishes_at_review():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M6-01 topology {uuid.uuid4().hex}",
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

            initial = driver.execute_script(
                """
                const active = document.querySelector(".wizard-step[aria-current=step]");
                return {
                  buttons: Array.from(document.querySelectorAll("#wizard-stepper .wizard-step"))
                    .map((button) => [button.dataset.step, button.dataset.stepId]),
                  activeStep: active?.dataset.step,
                  activePanel: document.querySelector(".wizard-panel.is-active")?.id,
                  progress: document.getElementById("wizard-progress-text")?.textContent.trim(),
                  previousDisabled: document.getElementById("wizard-prev")?.disabled,
                };
                """
            )
            assert initial["buttons"] == [
                ["1", "browser_network_search"],
                ["2", "urls_sites_navigation"],
                ["3", "security_privacy"],
                ["4", "certificates_trust"],
                ["5", "users_language_sync"],
                ["6", "extensions"],
                ["7", "ai"],
                ["8", "review_export"],
            ]
            assert initial["activeStep"] == "1"
            assert initial["activePanel"] == "wizard-step-1"
            assert "1" in initial["progress"] and "8" in initial["progress"]
            assert initial["previousDisabled"] is True

            first_step_button = driver.find_element(
                by.By.CSS_SELECTOR, '.wizard-step[data-step="1"]'
            )
            first_step_button.click()
            first_step_button.send_keys(keys.Keys.END)
            assert driver.switch_to.active_element.get_attribute("data-step") == "8"
            driver.switch_to.active_element.send_keys(keys.Keys.HOME)
            assert driver.switch_to.active_element.get_attribute("data-step") == "1"

            next_button = driver.find_element(by.By.ID, "wizard-next")
            for expected_step in range(2, 8):
                driver.execute_script("arguments[0].click();", next_button)
                wait.until(
                    lambda current_driver, expected=str(expected_step): (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                        ).get_attribute("data-step")
                        == expected
                    )
                )

            driver.execute_script("document.getElementById('wizard-finish').click();")
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step")
                    == "8"
                )
            )
            final = driver.execute_script(
                """
                return {
                  activePanel: document.querySelector(".wizard-panel.is-active")?.id,
                  progress: document.getElementById("wizard-progress-text")?.textContent.trim(),
                  nextDisabled: document.getElementById("wizard-next")?.disabled,
                  previousDisabled: document.getElementById("wizard-prev")?.disabled,
                };
                """
            )
            assert final["activePanel"] == "wizard-step-8"
            assert "8" in final["progress"]
            assert final["nextDisabled"] is True
            assert final["previousDisabled"] is False

            driver.execute_script(
                "arguments[0].click();", driver.find_element(by.By.ID, "wizard-prev")
            )
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step")
                    == "7"
                )
            )
        finally:
            close_chromium_driver(driver)


def test_guided_step_deep_links_use_semantic_history_and_explicit_legacy_mapping():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M6-02 navigation {uuid.uuid4().hex}",
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
            driver.get(f"{base_url}/profiles/{profile_id}/edit?legacy_step=5")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "ai"
                )
            )
            assert "step=ai" in driver.current_url
            assert "legacy_step" not in driver.current_url

            driver.execute_script(
                "arguments[0].click();", driver.find_element(by.By.ID, "wizard-next")
            )
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "review_export"
                )
            )
            assert "step=review_export" in driver.current_url

            driver.back()
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "ai"
                )
            )
            assert "step=ai" in driver.current_url
        finally:
            close_chromium_driver(driver)
