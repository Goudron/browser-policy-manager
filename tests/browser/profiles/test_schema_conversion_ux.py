"""Focused real-browser proof for the catalog-derived schema-conversion UX.

This is deliberately a small complement to the pure-module and API suites.  It
uses the shared Chromium harness so a failed scenario retains only the existing
safe screenshot/context/browser-log artifact set.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from tests.browser.harness import assert_document_fits as _assert_document_fits
from tests.browser.harness import body_text as _body_text
from tests.browser.harness import build_chromium_driver as _build_chromium_driver
from tests.browser.harness import click_element as _click_element
from tests.browser.harness import scoped_test_app_server as run_test_app_server
from tests.browser.profiles.pages import load_locale_catalog as _load_locale_catalog
from tests.browser.profiles.pages import set_locale as _set_locale
from tests.support import build_profile_payload

pytestmark = [
    pytest.mark.browser,
    pytest.mark.browser_ui,
    pytest.mark.ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]

ALL_LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def _progress(scenario: str, completed: int) -> None:
    print(f"BPM095 M5 UX scenario {completed}/3: {scenario}", flush=True)


def _create_profile(
    base_url: str,
    *,
    name: str,
    schema_version: str,
    flags: dict[str, Any],
) -> dict[str, Any]:
    response = requests.post(
        f"{base_url}/api/profiles",
        json=build_profile_payload(name=name, schema_version=schema_version, flags=flags),
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _archive_profile(base_url: str, profile_id: int) -> None:
    response = requests.delete(f"{base_url}/api/profiles/{profile_id}", timeout=10)
    assert response.status_code == 204, response.text


def _profile(base_url: str, profile_id: int) -> dict[str, Any]:
    response = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
    assert response.status_code == 200, response.text
    return response.json()


def _wait_for_review_state(wait: Any, driver: Any, by: Any, state: str) -> Any:
    try:
        return wait.until(
            lambda current_driver: (
                current_driver.find_element(by.By.ID, "schema-conversion-review")
                if current_driver.find_element(by.By.ID, "schema-conversion-review").get_attribute(
                    "data-schema-conversion-state"
                )
                == state
                else False
            )
        )
    except Exception as error:
        diagnostic = driver.execute_script(
            """
            const review = document.getElementById('schema-conversion-review');
            return {
              state: review?.dataset?.schemaConversionState || '',
              title: review?.querySelector('.schema-conversion-review-status strong')?.textContent || '',
              conversionRequests: Array.isArray(window.__bpmM5ConversionRequests)
                ? window.__bpmM5ConversionRequests
                : [],
            };
            """
        )
        raise AssertionError(
            f"schema conversion did not reach {state}; diagnostic={diagnostic}"
        ) from error


def _resource_paths(driver: Any) -> list[str]:
    return driver.execute_script(
        "return performance.getEntriesByType('resource').map((entry) => new URL(entry.name).pathname);"
    )


def _catalog(driver: Any) -> dict[str, Any]:
    return driver.execute_script(
        "return JSON.parse(document.getElementById('schema-channels-catalog').textContent);"
    )


def _record_conversion_transport(driver: Any) -> None:
    """Record only safe request outcome codes while this browser test is active."""

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            (() => {
              const originalFetch = window.fetch.bind(window);
              window.__bpmM5ConversionRequests = [];
              window.fetch = async (input, init = {}) => {
                const response = await originalFetch(input, init);
                const url = typeof input === 'string' ? input : input?.url || '';
                if (!url.includes('/conversion-preview') && !url.includes('/conversion-apply')) {
                  return response;
                }
                const record = {
                  path: new URL(url, window.location.origin).pathname,
                  method: init?.method || 'GET',
                  status: response.status,
                  code: '',
                };
                response.clone().json().then((payload) => {
                  record.code = typeof payload?.detail?.code === 'string'
                    ? payload.detail.code
                    : '';
                }).catch(() => {});
                window.__bpmM5ConversionRequests.push(record);
                return response;
              };
            })();
            """
        },
    )


def _change_select(driver: Any, select: Any, value: str) -> None:
    """Use the browser's native change event after choosing a catalog option."""

    changed = driver.execute_script(
        """
        const select = arguments[0];
        const value = arguments[1];
        select.focus();
        select.value = value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        return select.value;
        """,
        select,
        value,
    )
    assert changed == value


def _confirm_review_checkbox(driver: Any, acknowledgement: Any) -> None:
    """Dispatch the same checked/change pair a keyboard-confirmed checkbox emits."""

    checked = driver.execute_script(
        """
        const acknowledgement = arguments[0];
        acknowledgement.focus();
        acknowledgement.checked = true;
        acknowledgement.dispatchEvent(new Event('input', { bubbles: true }));
        acknowledgement.dispatchEvent(new Event('change', { bubbles: true }));
        return acknowledgement.checked;
        """,
        acknowledgement,
    )
    assert checked is True


def _make_workspace_dirty(wait: Any, driver: Any, by: Any, ec: Any) -> None:
    """Create a real unsaved workspace edit through the guided privacy controls."""

    _click_element(
        driver,
        wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-step="3"]'))),
    )
    _click_element(
        driver,
        wait.until(
            ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-hardening-preset="strict"]'))
        ),
    )


def _wait_for_saved_workspace(wait: Any, driver: Any, by: Any) -> None:
    wait.until(
        lambda current_driver: (
            "signal-chip--saved"
            in (
                current_driver.find_element(by.By.ID, "workspace-signal").get_attribute("class")
                or ""
            )
        )
    )


def test_browser_schema_conversion_library_recommendations_are_catalog_derived_and_localized():
    _progress("Library eligibility, locale, keyboard and responsive recommendation", 1)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        esr_115 = _create_profile(
            base_url,
            name="M5 UX older ESR 115",
            schema_version="esr-115.38",
            flags={"DisableTelemetry": True},
        )
        esr_140 = _create_profile(
            base_url,
            name="M5 UX older ESR 140",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        _create_profile(
            base_url,
            name="M5 UX latest ESR",
            schema_version="esr-153.0",
            flags={"DisableTelemetry": True},
        )
        _create_profile(
            base_url,
            name="M5 UX release channel",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        )
        archived = _create_profile(
            base_url,
            name="M5 UX archived ESR",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        _archive_profile(base_url, int(archived["id"]))

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "[data-schema-conversion-preview-entry]"
                        )
                    )
                    == 2
                )
            )

            catalog = _catalog(driver)
            catalog_targets = {
                option["artifact_id"]: option.get("recommendation_target")
                for option in catalog["options"]
            }
            assert catalog_targets["esr-115.38"] == "esr-153.0"
            assert catalog_targets["esr-140.13"] == "esr-153.0"
            assert catalog_targets["esr-153.0"] is None
            assert catalog_targets["release-153"] is None

            entries = driver.find_elements(
                by.By.CSS_SELECTOR, "[data-schema-conversion-preview-entry]"
            )
            by_profile = {
                int(entry.get_attribute("data-schema-conversion-profile-id")): entry
                for entry in entries
            }
            assert set(by_profile) == {int(esr_115["id"]), int(esr_140["id"])}
            for profile_id, entry in by_profile.items():
                assert (
                    entry.get_attribute("data-schema-conversion-target-artifact-id") == "esr-153.0"
                )
                parsed = urlparse(entry.get_attribute("href"))
                assert parsed.path == f"/profiles/{profile_id}/edit"
                assert parse_qs(parsed.query) == {
                    "schema_conversion": ["preview"],
                    "target_artifact_id": ["esr-153.0"],
                    "recommendation_id": ["schema-conversion.older-esr-recommendation"],
                }
                assert "DisableTelemetry" not in parsed.query
                assert entry.get_attribute("aria-describedby")
                accessible_name = entry.get_attribute("aria-label")
                assert "ESR 140.13" in accessible_name or "ESR 115.38" in accessible_name
                assert "ESR 153.0" in accessible_name

            rendered = _body_text(driver)
            assert "M5 UX latest ESR" in rendered and "M5 UX release channel" in rendered
            select_module = pytest.importorskip("selenium.webdriver.support.select")
            library_lifecycle = select_module.Select(
                driver.find_element(by.By.ID, "library-lifecycle-filter")
            )
            library_lifecycle.select_by_value("all")
            wait.until(lambda current_driver: "M5 UX archived ESR" in _body_text(current_driver))
            archived_row = driver.find_element(
                by.By.XPATH,
                "//li[contains(@class, 'library-table-row') and contains(., 'M5 UX archived ESR')]",
            )
            assert not archived_row.find_elements(
                by.By.CSS_SELECTOR, "[data-schema-conversion-preview-entry]"
            )

            for locale in ALL_LOCALES:
                catalog_locale = _load_locale_catalog(locale)
                _set_locale(
                    driver,
                    wait,
                    ui,
                    locale=locale,
                    expected_text=catalog_locale["profiles.locale_label"],
                )
                entry = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f'[data-schema-conversion-profile-id="{esr_115["id"]}"]',
                )
                assert (
                    catalog_locale["profiles.schema_conversion_recommendation_action"].split(
                        "{target_schema}"
                    )[0]
                    in entry.text
                )
                assert catalog_locale[
                    "profiles.schema_conversion_recommendation_consequence"
                ].split("{source_schema}")[0] in _body_text(driver)

            entry = driver.find_element(
                by.By.CSS_SELECTOR,
                f'[data-schema-conversion-profile-id="{esr_140["id"]}"]',
            )
            driver.execute_script("arguments[0].focus();", entry)
            assert driver.switch_to.active_element == entry
            entry.send_keys(keys.Keys.ENTER)
            wait.until(
                lambda current_driver: (
                    "/profiles/" in current_driver.current_url
                    and "schema_conversion" not in current_driver.current_url
                )
            )
            _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            assert "/conversion-apply" not in _resource_paths(driver)
            driver.set_window_size(390, 900)
            driver.execute_cdp_cmd(
                "Emulation.setEmulatedMedia",
                {"features": [{"name": "forced-colors", "value": "active"}]},
            )
            _assert_document_fits(driver)
        finally:
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})


def test_browser_schema_conversion_blocked_retry_and_unsaved_cancel_are_side_effect_free():
    _progress("Blocked/retry and unsaved cancel", 2)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    select_module = pytest.importorskip("selenium.webdriver.support.select")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        blocked = _create_profile(
            base_url,
            name="M5 UX blocked retry",
            schema_version="release-153",
            flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
        )
        dirty = _create_profile(
            base_url,
            name="M5 UX unsaved cancel",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        saved = _create_profile(
            base_url,
            name="M5 UX unsaved save",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        discarded = _create_profile(
            base_url,
            name="M5 UX unsaved discard",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(
                f"{base_url}/profiles/{blocked['id']}/edit?schema_conversion=preview"
                "&target_artifact_id=esr-153.0"
                "&recommendation_id=schema-conversion.older-esr-recommendation"
            )
            _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            target_select_element = driver.find_element(by.By.ID, "schema-conversion-target-select")
            target_selector = select_module.Select(target_select_element)
            assert [option.get_attribute("value") for option in target_selector.options] == [
                "",
                "esr-153.0",
                "esr-140.13",
                "esr-115.38",
            ]
            _change_select(driver, target_select_element, "esr-115.38")
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.preview-blocked")
            assert "AIControls" not in review.text
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-schema-conversion-apply]")
            wait.until(
                lambda current_driver: (
                    current_driver.switch_to.active_element.get_attribute(
                        "data-schema-conversion-terminal"
                    )
                    is not None
                )
            )
            target_select_element = driver.find_element(by.By.ID, "schema-conversion-target-select")
            _change_select(driver, target_select_element, "esr-153.0")
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            assert review.get_attribute("aria-busy") == "false"
            assert "/conversion-apply" not in _resource_paths(driver)
            assert _profile(base_url, int(blocked["id"]))["schema_version"] == "release-153"

            driver.get(f"{base_url}/profiles/{saved['id']}/edit")
            _wait_for_saved_workspace(wait, driver, by)
            _make_workspace_dirty(wait, driver, by, ec)
            wait.until(
                lambda current_driver: (
                    "signal-chip--dirty"
                    in (
                        current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                            "class"
                        )
                        or ""
                    )
                )
            )
            opener = driver.find_element(by.By.ID, "schema-conversion-review-open")
            _click_element(driver, opener)
            target_selector = wait.until(
                ec.presence_of_element_located((by.By.ID, "schema-conversion-target-select"))
            )
            _change_select(driver, target_selector, "esr-153.0")
            review = _wait_for_review_state(
                wait, driver, by, "schema-conversion.unsaved-work-decision"
            )
            assert "Save" in review.text and "Discard" in review.text and "Cancel" in review.text
            assert "/conversion-apply" not in _resource_paths(driver)
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-save-preview]"),
            )
            _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            saved_after_preview = _profile(base_url, int(saved["id"]))
            assert saved_after_preview["revision"] == saved["revision"] + 1
            assert saved_after_preview["schema_version"] == "esr-140.13"

            driver.get(f"{base_url}/profiles/{discarded['id']}/edit")
            _wait_for_saved_workspace(wait, driver, by)
            _make_workspace_dirty(wait, driver, by, ec)
            wait.until(
                lambda current_driver: (
                    "signal-chip--dirty"
                    in (
                        current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                            "class"
                        )
                        or ""
                    )
                )
            )
            _click_element(driver, driver.find_element(by.By.ID, "schema-conversion-review-open"))
            target_selector = wait.until(
                ec.presence_of_element_located((by.By.ID, "schema-conversion-target-select"))
            )
            _change_select(driver, target_selector, "esr-153.0")
            review = _wait_for_review_state(
                wait, driver, by, "schema-conversion.unsaved-work-decision"
            )
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-discard-preview]"),
            )
            _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            discarded_after_preview = _profile(base_url, int(discarded["id"]))
            assert discarded_after_preview["revision"] == discarded["revision"]
            assert discarded_after_preview["schema_version"] == "esr-140.13"

            driver.get(f"{base_url}/profiles/{dirty['id']}/edit")
            _wait_for_saved_workspace(wait, driver, by)
            _make_workspace_dirty(wait, driver, by, ec)
            wait.until(
                lambda current_driver: (
                    "signal-chip--dirty"
                    in (
                        current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                            "class"
                        )
                        or ""
                    )
                )
            )
            _click_element(driver, driver.find_element(by.By.ID, "schema-conversion-review-open"))
            target_selector = wait.until(
                ec.presence_of_element_located((by.By.ID, "schema-conversion-target-select"))
            )
            _change_select(driver, target_selector, "esr-153.0")
            review = _wait_for_review_state(
                wait, driver, by, "schema-conversion.unsaved-work-decision"
            )
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-cancel]"),
            )
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(by.By.ID, "schema-conversion-review").get_attribute(
                        "hidden"
                    )
                    is not None
                )
            )
            assert (
                driver.switch_to.active_element.get_attribute("id")
                == "schema-conversion-review-open"
            )
            current = _profile(base_url, int(dirty["id"]))
            assert current["schema_version"] == "esr-140.13"
            assert current["revision"] == dirty["revision"]
        finally:
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})


def test_browser_schema_conversion_requires_explicit_confirmation_and_recovers_stale_review():
    _progress("Explicit apply, exact reload and stale recovery", 3)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        successful = _create_profile(
            base_url,
            name="M5 UX explicit conversion",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        stale = _create_profile(
            base_url,
            name="M5 UX stale conversion",
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            _record_conversion_transport(driver)
            driver.get(
                f"{base_url}/profiles/{successful['id']}/edit?schema_conversion=preview"
                "&target_artifact_id=esr-153.0"
                "&recommendation_id=schema-conversion.older-esr-recommendation"
            )
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            assert review.find_element(
                by.By.CSS_SELECTOR, "[data-schema-conversion-confirm]"
            ).is_enabled()
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-schema-conversion-apply]")
            assert "/conversion-apply" not in _resource_paths(driver)
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-confirm]"),
            )
            review = _wait_for_review_state(
                wait, driver, by, "schema-conversion.confirmation-ready"
            )
            apply = review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-apply]")
            assert not apply.is_enabled()
            acknowledgement = review.find_element(
                by.By.CSS_SELECTOR, "[data-schema-conversion-confirm-check]"
            )
            _confirm_review_checkbox(driver, acknowledgement)
            apply = review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-apply]")
            wait.until(lambda _driver: apply.is_enabled())
            assert (
                apply.get_attribute("aria-describedby")
                == "schema-conversion-confirmation-consequence"
            )
            _click_element(driver, apply)
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.apply-success")
            saved = _profile(base_url, int(successful["id"]))
            assert saved["schema_version"] == "esr-153.0"
            assert saved["revision"] == successful["revision"] + 1
            assert str(saved["revision"]) in review.text

            driver.get(
                f"{base_url}/profiles/{stale['id']}/edit?schema_conversion=preview"
                "&target_artifact_id=esr-153.0"
                "&recommendation_id=schema-conversion.older-esr-recommendation"
            )
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.preview-available")
            changed = requests.patch(
                f"{base_url}/api/profiles/{stale['id']}",
                json={
                    "description": "M5 UX external revision change",
                    "revision": stale["revision"],
                },
                timeout=10,
            )
            assert changed.status_code == 200, changed.text
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-confirm]"),
            )
            review = _wait_for_review_state(
                wait, driver, by, "schema-conversion.confirmation-ready"
            )
            _confirm_review_checkbox(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-confirm-check]"),
            )
            _click_element(
                driver,
                review.find_element(by.By.CSS_SELECTOR, "[data-schema-conversion-apply]"),
            )
            review = _wait_for_review_state(wait, driver, by, "schema-conversion.stale-revision")
            assert review.find_elements(by.By.CSS_SELECTOR, "[data-schema-conversion-refresh]")
            stale_after = _profile(base_url, int(stale["id"]))
            assert stale_after["schema_version"] == "esr-140.13"
            assert stale_after["revision"] == stale["revision"] + 1
        finally:
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})
