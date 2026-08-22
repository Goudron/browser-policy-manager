"""Chromium acceptance for the M6-06 Guided topology accessibility matrix."""

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


def _create_profile(base_url: str) -> int:
    response = requests.post(
        f"{base_url}/api/profiles/prepare/new",
        json={
            "name": f"M6-06 topology accessibility {uuid.uuid4().hex * 2}",
            "target_schema_id": "release-153",
            "starter_id": "basic_corporate",
            "cis_baseline_id": "cis_l2",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


def _assert_document_fits(driver) -> None:
    metrics = driver.execute_script(
        """
        return {
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
        };
        """
    )
    assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics


def test_guided_eight_step_topology_is_keyboard_operable_responsive_and_motion_safe():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    select_module = pytest.importorskip("selenium.webdriver.support.select")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    german = load_locale_catalog("de")

    with scoped_test_app_server() as base_url:
        profile_id = _create_profile(base_url)
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            # Tablet width intentionally exercises the horizontally scrollable stepper.
            driver.set_window_size(1180, 900)
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            stepper = driver.find_element(by.By.ID, "wizard-stepper")
            overflow = driver.execute_script(
                """
                const stepper = arguments[0];
                return {
                  tag: stepper.tagName.toLowerCase(),
                  name: stepper.getAttribute("aria-label"),
                  scrollWidth: stepper.scrollWidth,
                  clientWidth: stepper.clientWidth,
                  steps: Array.from(stepper.querySelectorAll(".wizard-step")).map((button) => ({
                    step: button.dataset.step,
                    id: button.dataset.stepId,
                    visible: Boolean(button.offsetWidth && button.offsetHeight),
                    ariaControls: button.getAttribute("aria-controls"),
                  })),
                };
                """,
                stepper,
            )
            assert overflow["tag"] == "nav"
            assert overflow["name"]
            assert overflow["scrollWidth"] > overflow["clientWidth"]
            assert [(item["step"], item["id"]) for item in overflow["steps"]] == [
                ("1", "browser_network_search"),
                ("2", "urls_sites_navigation"),
                ("3", "security_privacy"),
                ("4", "certificates_trust"),
                ("5", "users_language_sync"),
                ("6", "extensions"),
                ("7", "ai"),
                ("8", "review_export"),
            ]
            assert all(item["visible"] and item["ariaControls"] for item in overflow["steps"])
            assert "step 6 of 6" not in driver.find_element(by.By.TAG_NAME, "body").text.lower()

            # Arrow/Home/End move the roving focus only; Enter activates the focused step.
            first_step = driver.find_element(by.By.CSS_SELECTOR, '.wizard-step[data-step="1"]')
            driver.execute_script("arguments[0].focus();", first_step)
            first_step.send_keys(keys.Keys.END)
            wait.until(
                lambda current_driver: (
                    current_driver.switch_to.active_element.get_attribute("data-step") == "8"
                )
            )
            assert (
                driver.find_element(
                    by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                ).get_attribute("data-step")
                == "1"
            )
            driver.switch_to.active_element.send_keys(keys.Keys.ENTER)
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step")
                    == "8"
                )
            )
            wait.until(
                lambda current_driver: (
                    current_driver.switch_to.active_element.get_attribute("id") == "wizard-step-8"
                )
            )
            driver.execute_async_script("window.setTimeout(arguments[0], 750);")
            active_step_metrics = driver.execute_script(
                """
                const stepper = document.getElementById("wizard-stepper");
                const active = stepper.querySelector(".wizard-step[aria-current=step]");
                const outer = stepper.getBoundingClientRect();
                const inner = active.getBoundingClientRect();
                return {
                  visible: inner.left >= outer.left - 1 && inner.right <= outer.right + 1,
                  scrollLeft: stepper.scrollLeft,
                  scrollWidth: stepper.scrollWidth,
                  clientWidth: stepper.clientWidth,
                  outer: { left: outer.left, right: outer.right },
                  inner: { left: inner.left, right: inner.right },
                };
                """
            )
            assert active_step_metrics["visible"] is True, active_step_metrics

            # A no-op selection must not enqueue a stale panel focus restoration.
            eighth_step = driver.find_element(by.By.CSS_SELECTOR, '.wizard-step[data-step="8"]')
            driver.execute_script("arguments[0].focus(); arguments[0].click();", eighth_step)
            wait.until(
                lambda current_driver: (
                    current_driver.switch_to.active_element.get_attribute("data-step") == "8"
                )
            )

            # Search uses its owning step and restores focus inside that active panel.
            search = driver.find_element(by.By.ID, "wizard-settings-search-input")
            search.clear()
            search.send_keys("AIControls")
            result = wait.until(
                lambda current_driver: next(
                    (
                        candidate
                        for candidate in current_driver.find_elements(
                            by.By.CSS_SELECTOR,
                            "#wizard-settings-search-results [data-settings-search-target]",
                        )
                        if "STEP 7" in candidate.text.upper()
                    ),
                    False,
                )
            )
            result_target = result.get_attribute("data-settings-search-target")
            assert result_target
            # Chromium's native click auto-scroll can target a stale horizontal-strip
            # coordinate after End. Invoke the same delegated click handler directly.
            driver.execute_script("arguments[0].click();", result)
            ui.WebDriverWait(driver, 5).until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "ai"
                ),
                result_target,
            )
            ui.WebDriverWait(driver, 5).until(
                lambda current_driver: current_driver.execute_script(
                    "return Boolean(document.activeElement.closest('.wizard-panel.is-active'));"
                ),
                "search result did not restore focus in the active guided panel",
            )

            # Both navigation and search must ask for instant scrolling when the user prefers less motion.
            driver.execute_cdp_cmd(
                "Emulation.setEmulatedMedia",
                {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
            )
            driver.execute_script(
                """
                window.__m606ScrollBehaviors = [];
                window.__m606OriginalScrollIntoView = HTMLElement.prototype.scrollIntoView;
                HTMLElement.prototype.scrollIntoView = function(options) {
                  window.__m606ScrollBehaviors.push(options?.behavior || "");
                };
                """
            )
            # Keep the deterministic reduced-motion assertion independent of
            # Chromium's native pointer coordinate after the preceding
            # horizontally-scrolled search-result activation.
            driver.execute_script(
                "arguments[0].click();", driver.find_element(by.By.ID, "wizard-next")
            )
            ui.WebDriverWait(driver, 5).until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step")
                    == "8"
                ),
                "next did not activate the review step",
            )
            ui.WebDriverWait(driver, 5).until(
                lambda current_driver: (
                    "auto" in current_driver.execute_script("return window.__m606ScrollBehaviors;")
                ),
                "reduced-motion navigation did not request instant scrolling",
            )
            assert set(driver.execute_script("return window.__m606ScrollBehaviors;")) == {"auto"}
            driver.execute_script(
                """
                if (window.__m606OriginalScrollIntoView) {
                  HTMLElement.prototype.scrollIntoView = window.__m606OriginalScrollIntoView;
                }
                """
            )
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})

            # The two-column phone stepper keeps all eight long German labels operable without page overflow.
            driver.set_window_size(320, 900)
            set_locale(
                driver,
                wait,
                ui,
                locale="de",
                expected_text=german["profiles.locale_label"],
            )
            mobile = driver.execute_script(
                """
                const stepper = document.getElementById("wizard-stepper");
                const outer = stepper.getBoundingClientRect();
                return {
                  scrollWidth: stepper.scrollWidth,
                  clientWidth: stepper.clientWidth,
                  buttons: Array.from(stepper.querySelectorAll(".wizard-step")).map((button) => {
                    const rect = button.getBoundingClientRect();
                    return {
                      text: button.innerText.trim(),
                      visible: Boolean(button.offsetWidth && button.offsetHeight),
                      withinStepper: rect.left >= outer.left - 1 && rect.right <= outer.right + 1,
                    };
                  }),
                  forbidden: document.querySelectorAll(
                    "#profile-type, #wizard-schema, [data-starter-key], [data-cis-layer-key], "
                    + "#wizard-stepper .wizard-step[data-step='9']"
                  ).length,
                };
                """
            )
            assert mobile["scrollWidth"] <= mobile["clientWidth"] + 1
            assert len(mobile["buttons"]) == 8
            assert all(
                button["visible"] and button["withinStepper"] for button in mobile["buttons"]
            )
            assert all(
                german[f"profiles.wizard_step_{word}"] in mobile["buttons"][index]["text"]
                for index, word in enumerate(
                    ("one", "two", "three", "four", "five", "six", "seven", "eight")
                )
            )
            assert mobile["forbidden"] == 0
            _assert_document_fits(driver)

            for theme in ("light", "dark"):
                select_module.Select(driver.find_element(by.By.ID, "theme")).select_by_value(theme)
                wait.until(
                    lambda current_driver, expected=theme: (
                        current_driver.execute_script(
                            "return document.documentElement.dataset.themeMode;"
                        )
                        == expected
                    )
                )
                _assert_document_fits(driver)
        finally:
            driver.execute_script(
                """
                if (window.__m606OriginalScrollIntoView) {
                  HTMLElement.prototype.scrollIntoView = window.__m606OriginalScrollIntoView;
                }
                """
            )
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})
            close_chromium_driver(driver)
