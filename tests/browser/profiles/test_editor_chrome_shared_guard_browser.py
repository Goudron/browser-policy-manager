"""Browser proof for the M5-06 shared read-only chrome guard."""

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


def test_browser_shared_chrome_facts_are_identical_read_only_and_fit_at_320px_in_each_theme():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    select_module = pytest.importorskip("selenium.webdriver.support.select")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale = "de"
    catalog = load_locale_catalog(locale)

    with scoped_test_app_server() as base_url:
        created = requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"M5-06 long chrome name {uuid.uuid4().hex * 2}",
                "target_schema_id": "release-153",
                "starter_id": "basic_corporate",
                "cis_baseline_id": "cis_l2",
                "preparation_idempotency_key": uuid.uuid4().hex,
            },
            timeout=10,
        )
        assert created.status_code == 201, created.text
        profile_id = created.json()["id"]
        expected = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10).json()

        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.set_window_size(320, 900)
            snapshots = []
            for suffix, ready_id in (
                ("edit", "wizard-panel"),
                ("settings", "settings-panel"),
                ("json", "editor-panel"),
            ):
                driver.get(f"{base_url}/profiles/{profile_id}/{suffix}")
                wait.until(ec.presence_of_element_located((by.By.ID, ready_id)))
                set_locale(
                    driver, wait, ui, locale=locale, expected_text=catalog["profiles.locale_label"]
                )
                wait.until(ec.presence_of_element_located((by.By.ID, "profile-cis-fact")))
                snapshots.append(
                    driver.execute_script(
                        """
                        const fields = ["profile-schema-fact", "profile-starter-fact", "profile-cis-fact"];
                        const fact = (id) => document.getElementById(id);
                        return {
                          facts: fields.map((id) => ({
                            id,
                            text: fact(id)?.innerText.trim() || "",
                            schema: fact(id)?.dataset.savedProfileSchema || null,
                            starterId: fact(id)?.dataset.savedProfileStarterId || null,
                            cisBaselineId: fact(id)?.dataset.savedProfileCisBaselineId || null,
                            cisStatus: fact(id)?.dataset.savedProfileCisDisplayStatus || null,
                          })),
                          forbidden: document.querySelectorAll(
                            "#overview-panel [contenteditable=true], #profile-type, #wizard-schema, "
                            + "#wizard-starter, #wizard-cis, input[name=schema_version], "
                            + "input[name=target_schema_id], input[name=starter_id], "
                            + "input[name=cis_baseline_id], input[name=baseline_provenance], "
                            + "input[name=baseline_display]"
                          ).length,
                          chromeFits: [document.getElementById("overview-panel"), ...fields.map(fact)]
                            .every((node) => node && node.scrollWidth <= node.clientWidth + 1),
                        };
                        """
                    )
                )
                assert snapshots[-1]["forbidden"] == 0
                assert snapshots[-1]["chromeFits"] is True

            assert snapshots[1:] == [snapshots[0], snapshots[0]]
            facts = {fact["id"]: fact for fact in snapshots[0]["facts"]}
            assert facts["profile-schema-fact"]["schema"] == expected["schema_version"]
            assert (
                facts["profile-starter-fact"]["starterId"]
                == expected["baseline_display"]["starter"]["preset_id"]
            )
            assert (
                facts["profile-cis-fact"]["cisBaselineId"]
                == expected["baseline_display"]["cis"]["baseline_id"]
            )
            assert (
                facts["profile-cis-fact"]["cisStatus"]
                == expected["baseline_display"]["cis"]["display_status"]
            )

            for theme in ("light", "dark"):
                select_module.Select(driver.find_element(by.By.ID, "theme")).select_by_value(theme)
                wait.until(
                    lambda current_driver, expected_theme=theme: (
                        current_driver.execute_script(
                            "return document.documentElement.dataset.themeMode;"
                        )
                        == expected_theme
                    )
                )
                assert (
                    driver.execute_script(
                        """
                    const fields = ["profile-schema-fact", "profile-starter-fact", "profile-cis-fact"];
                    return [document.getElementById("overview-panel"), ...fields.map((id) => document.getElementById(id))]
                      .every((node) => node && node.scrollWidth <= node.clientWidth + 1);
                    """
                    )
                    is True
                )
        finally:
            close_chromium_driver(driver)
