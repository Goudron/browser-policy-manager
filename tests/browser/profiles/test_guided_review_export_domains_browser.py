"""Browser acceptance for the M6 eight-domain final review."""

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


def test_final_review_exposes_eight_domains_and_jumps_to_their_current_owner():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M6-05 review {uuid.uuid4().hex}",
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
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=review_export")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-export-ready-card")))
            assert (
                driver.find_element(
                    by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                ).get_attribute("data-step-id")
                == "review_export"
            )
            for domain in (
                "browser",
                "urls",
                "privacy",
                "certificates",
                "users",
                "extensions",
                "ai",
                "review",
            ):
                assert driver.find_element(by.By.ID, f"wizard-export-guided-group-{domain}")
                assert (
                    driver.find_element(by.By.ID, f"wizard-export-summary-{domain}")
                    .get_attribute("textContent")
                    .strip()
                )
                assert driver.find_element(
                    by.By.ID, f"wizard-export-summary-{domain}-jump"
                ).is_enabled()

            facts = driver.execute_script(
                """
                return {
                  schema: document.getElementById("profile-schema-fact")?.textContent.trim(),
                  starter: document.getElementById("profile-starter-fact")?.textContent.trim(),
                  cis: document.getElementById("profile-cis-fact")?.textContent.trim(),
                  selectors: document.querySelectorAll(
                    '#profile-type, #wizard-schema, [data-starter-key], [data-cis-layer-key]'
                  ).length,
                  exportHref: document.getElementById("wizard-export-firefox-policies")?.getAttribute("href"),
                };
                """
            )
            assert facts["schema"]
            assert facts["starter"]
            assert facts["cis"]
            assert facts["selectors"] == 0
            assert facts["exportHref"] == f"/api/export/profiles/{profile_id}/firefox/policies.json"
        finally:
            close_chromium_driver(driver)
