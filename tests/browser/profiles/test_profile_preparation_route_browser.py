"""Chromium outcome guards for the M4 create/duplicate preparation surface."""

from __future__ import annotations

import copy
import uuid
from typing import Any
from urllib.parse import urlparse

import pytest
import requests

from tests.browser.harness import assert_document_fits as _assert_document_fits
from tests.browser.harness import build_chromium_driver as _build_chromium_driver
from tests.browser.profiles.pages import load_locale_catalog
from tests.support import build_profile_payload

PREPARE_NEW_PATH = "/api/profiles/prepare/new"


def _progress(scenario: str, completed: int) -> None:
    print(f"BPM096 M4-06 Chromium {completed}/4: {scenario}", flush=True)


def _new_payload(name: str) -> dict[str, object]:
    return {
        "name": name,
        "target_schema_id": "release-153",
        "starter_id": "blank",
        "cis_baseline_id": "none",
        "preparation_idempotency_key": uuid.uuid4().hex,
    }


def _prepare_source(base_url: str, name: str) -> dict[str, Any]:
    response = requests.post(f"{base_url}{PREPARE_NEW_PATH}", json=_new_payload(name), timeout=15)
    assert response.status_code == 201, response.text
    return response.json()


def _profiles(base_url: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{base_url}/api/profiles",
        params={"lifecycle": "all", "sort": "id", "order": "asc"},
        timeout=15,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _profile(base_url: str, profile_id: int) -> dict[str, Any]:
    response = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=15)
    assert response.status_code == 200, response.text
    return response.json()


def _write_name(driver: Any, by: Any, name: str) -> None:
    field = driver.find_element(by.By.ID, "profile-preparation-name")
    field.clear()
    field.send_keys(name)


def _wait_for_edit_destination(wait: Any, driver: Any) -> int:
    def destination_id(current_driver: Any) -> int | bool:
        path = urlparse(current_driver.current_url).path
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "profiles" or parts[2] != "edit":
            return False
        return int(parts[1]) if parts[1].isdigit() and int(parts[1]) > 0 else False

    return int(wait.until(destination_id))


def _wait_for_form(wait: Any, driver: Any, by: Any) -> Any:
    return wait.until(
        lambda current_driver: current_driver.find_element(by.By.ID, "profile-preparation-form")
    )


def _set_select_value(driver: Any, ui: Any, by: Any, identifier: str, value: str) -> None:
    select = ui.Select(driver.find_element(by.By.ID, identifier))
    select.select_by_value(value)


def test_browser_create_preparation_is_exactly_once_and_back_or_reload_do_not_write(
    browser_test_context: Any,
    browser_product_server: str,
) -> None:
    _progress("create success, double activation, reload, and Back", 1)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    driver = _build_chromium_driver()
    wait = ui.WebDriverWait(driver, 20)
    name = f"M4 route create {uuid.uuid4().hex}"

    driver.get(f"{browser_product_server}/profiles/new")
    _wait_for_form(wait, driver, by)
    assert _profiles(browser_product_server) == []
    _write_name(driver, by, name)

    driver.execute_script(
        """
        const form = document.getElementById('profile-preparation-form');
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        """
    )
    created_id = _wait_for_edit_destination(wait, driver)
    created = _profile(browser_product_server, created_id)
    assert created["name"] == name
    assert created["schema_version"] == "release-153"
    assert created["baseline_provenance"]["lineage"]["kind"] == "prepared"
    assert [profile["id"] for profile in _profiles(browser_product_server)] == [created_id]

    driver.back()
    _wait_for_form(wait, driver, by)
    assert urlparse(driver.current_url).path == "/profiles/new"
    assert [profile["id"] for profile in _profiles(browser_product_server)] == [created_id]
    driver.refresh()
    _wait_for_form(wait, driver, by)
    assert [profile["id"] for profile in _profiles(browser_product_server)] == [created_id]
    _assert_document_fits(driver)


def test_browser_duplicate_preparation_preserves_source_and_replaces_its_own_tab(
    browser_test_context: Any,
    browser_product_server: str,
) -> None:
    _progress("duplicate success, source preservation, reload, and Back", 2)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    driver = _build_chromium_driver()
    wait = ui.WebDriverWait(driver, 20)
    source = _prepare_source(browser_product_server, f"M4 route source {uuid.uuid4().hex}")
    source_before = copy.deepcopy(source)
    target_name = f"M4 route duplicate {uuid.uuid4().hex}"

    driver.get(f"{browser_product_server}/profiles/new?clone_from={source['id']}")
    _wait_for_form(wait, driver, by)
    action = wait.until(ec.element_to_be_clickable((by.By.ID, "profile-preparation-submit")))
    _write_name(driver, by, target_name)
    action.click()
    target_id = _wait_for_edit_destination(wait, driver)

    target = _profile(browser_product_server, target_id)
    assert target["name"] == target_name
    assert target["id"] != source["id"]
    assert target["baseline_provenance"]["lineage"]["kind"] == "duplicate"
    assert _profile(browser_product_server, int(source["id"])) == source_before
    assert {profile["id"] for profile in _profiles(browser_product_server)} == {
        source["id"],
        target_id,
    }

    driver.back()
    _wait_for_form(wait, driver, by)
    driver.refresh()
    _wait_for_form(wait, driver, by)
    assert {profile["id"] for profile in _profiles(browser_product_server)} == {
        source["id"],
        target_id,
    }
    _assert_document_fits(driver)


def test_browser_terminal_failures_keep_form_input_and_create_no_target(
    browser_test_context: Any,
    browser_product_server: str,
) -> None:
    _progress("name conflict, stale source, conversion block, and unavailable CIS", 3)
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    driver = _build_chromium_driver()
    wait = ui.WebDriverWait(driver, 20)

    conflict_name = f"M4 route conflict {uuid.uuid4().hex}"
    conflict = _prepare_source(browser_product_server, conflict_name)
    driver.get(f"{browser_product_server}/profiles/new")
    _wait_for_form(wait, driver, by)
    _write_name(driver, by, conflict_name)
    driver.find_element(by.By.ID, "profile-preparation-submit").click()
    conflict_error = wait.until(
        lambda current_driver: (
            current_driver.find_element(by.By.ID, "profile-preparation-name-error")
            if not current_driver.find_element(
                by.By.ID, "profile-preparation-name-error"
            ).get_attribute("hidden")
            else False
        )
    )
    assert (
        driver.find_element(by.By.ID, "profile-preparation-name").get_attribute("value")
        == conflict_name
    )
    assert driver.execute_script("return document.activeElement.id") == "profile-preparation-name"
    assert conflict_error.text
    assert [profile["id"] for profile in _profiles(browser_product_server)] == [conflict["id"]]

    source = _prepare_source(browser_product_server, f"M4 stale source {uuid.uuid4().hex}")
    driver.get(f"{browser_product_server}/profiles/new?clone_from={source['id']}")
    _wait_for_form(wait, driver, by)
    wait.until(ec.element_to_be_clickable((by.By.ID, "profile-preparation-submit")))
    _write_name(driver, by, f"M4 stale target {uuid.uuid4().hex}")
    update = requests.patch(
        f"{browser_product_server}/api/profiles/{source['id']}",
        json={"description": "revision changed", "expected_revision": source["revision"]},
        timeout=15,
    )
    assert update.status_code == 200, update.text
    source_after_update = update.json()
    driver.find_element(by.By.ID, "profile-preparation-submit").click()
    stale_error = wait.until(
        lambda current_driver: (
            current_driver.find_element(by.By.ID, "profile-preparation-action-error")
            if not current_driver.find_element(
                by.By.ID, "profile-preparation-action-error"
            ).get_attribute("hidden")
            else False
        )
    )
    assert stale_error.text
    assert driver.find_element(by.By.ID, "profile-preparation-submit").is_enabled() is False
    assert _profile(browser_product_server, int(source["id"])) == source_after_update
    assert {profile["id"] for profile in _profiles(browser_product_server)} == {
        conflict["id"],
        source["id"],
    }

    blocked_response = requests.post(
        f"{browser_product_server}/api/profiles",
        json=build_profile_payload(
            name=f"M4 blocked source {uuid.uuid4().hex}",
            schema_version="esr-153.0",
            flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
        ),
        timeout=15,
    )
    assert blocked_response.status_code == 201, blocked_response.text
    blocked_source = blocked_response.json()
    blocked_before = copy.deepcopy(blocked_source)
    driver.get(f"{browser_product_server}/profiles/new?clone_from={blocked_source['id']}")
    _wait_for_form(wait, driver, by)
    _set_select_value(driver, ui, by, "profile-preparation-schema", "esr-115.39")
    blocked_error = wait.until(
        lambda current_driver: (
            current_driver.find_element(by.By.ID, "profile-preparation-action-error")
            if not current_driver.find_element(
                by.By.ID, "profile-preparation-action-error"
            ).get_attribute("hidden")
            else False
        )
    )
    assert blocked_error.text
    assert driver.find_element(by.By.ID, "profile-preparation-submit").is_enabled() is False
    assert _profile(browser_product_server, int(blocked_source["id"])) == blocked_before

    driver.get(f"{browser_product_server}/profiles/new")
    _wait_for_form(wait, driver, by)
    unavailable = driver.execute_script(
        """
        const schema = document.getElementById('profile-preparation-schema');
        const cis = document.getElementById('profile-preparation-cis');
        const option = new Option('Unavailable test baseline', 'm4-unavailable-cis');
        option.dataset.availableSchemaVersions = 'unsupported-test-schema';
        cis.append(option);
        cis.value = option.value;
        schema.dispatchEvent(new Event('change', { bubbles: true }));
        return cis.selectedOptions[0].disabled;
        """
    )
    assert unavailable is True
    _write_name(driver, by, f"M4 unavailable cis {uuid.uuid4().hex}")
    driver.find_element(by.By.ID, "profile-preparation-submit").click()
    cis_error = wait.until(
        lambda current_driver: (
            current_driver.find_element(by.By.ID, "profile-preparation-cis-error")
            if not current_driver.find_element(
                by.By.ID, "profile-preparation-cis-error"
            ).get_attribute("hidden")
            else False
        )
    )
    assert cis_error.text
    assert driver.execute_script("return document.activeElement.id") == "profile-preparation-cis"
    assert _profile(browser_product_server, int(blocked_source["id"])) == blocked_before
    assert len(_profiles(browser_product_server)) == 3


def test_browser_preparation_locales_keyboard_accessibility_and_narrow_long_labels(
    browser_test_context: Any,
    browser_product_server: str,
) -> None:
    _progress("six locales, keyboard order, narrow viewport, and long source label", 4)
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    driver = _build_chromium_driver()
    wait = ui.WebDriverWait(driver, 20)
    long_source = _prepare_source(browser_product_server, "M4" + "x" * 250)
    user_agent = driver.execute_script("return navigator.userAgent")

    duplicate_url = f"{browser_product_server}/profiles/new?clone_from={long_source['id']}"
    driver.get(duplicate_url)
    form = _wait_for_form(wait, driver, by)
    assert [
        element.get_attribute("id")
        for element in form.find_elements(by.By.CSS_SELECTOR, "input, select, button")
    ] == [
        "profile-preparation-name",
        "profile-preparation-schema",
        "profile-preparation-starter",
        "profile-preparation-cis",
        "profile-preparation-submit",
    ]
    name = driver.find_element(by.By.ID, "profile-preparation-name")
    name.click()
    name.send_keys(keys.Keys.TAB)
    assert (
        wait.until(
            lambda current_driver: current_driver.execute_script("return document.activeElement.id")
        )
        == "profile-preparation-schema"
    )
    driver.switch_to.active_element.send_keys(keys.Keys.TAB)
    assert (
        wait.until(
            lambda current_driver: current_driver.execute_script("return document.activeElement.id")
        )
        == "profile-preparation-starter"
    )
    driver.switch_to.active_element.send_keys(keys.Keys.TAB)
    assert (
        wait.until(
            lambda current_driver: current_driver.execute_script("return document.activeElement.id")
        )
        == "profile-preparation-cis"
    )
    driver.switch_to.active_element.send_keys(keys.Keys.TAB)
    assert (
        wait.until(
            lambda current_driver: current_driver.execute_script("return document.activeElement.id")
        )
        == "profile-preparation-submit"
    )

    for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN"):
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": user_agent, "acceptLanguage": locale, "platform": "Linux"},
        )
        driver.get(duplicate_url)
        _wait_for_form(wait, driver, by)
        wait.until(
            lambda current_driver, expected_locale=locale: (
                current_driver.execute_script("return document.documentElement.lang")
                == expected_locale
            )
        )
        catalog = load_locale_catalog(locale)
        assert (
            driver.find_element(by.By.ID, "profile-preparation-submit")
            .get_attribute("textContent")
            .strip()
            == catalog["profiles.preparation_duplicate_action"]
        )
        assert (
            driver.find_element(by.By.CSS_SELECTOR, 'label[for="profile-preparation-cis"]')
            .get_attribute("textContent")
            .strip()
            == catalog["profiles.preparation_cis_label"]
        )

    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": user_agent, "acceptLanguage": "de", "platform": "Linux"},
    )
    driver.get(duplicate_url)
    _wait_for_form(wait, driver, by)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 320, "height": 900, "deviceScaleFactor": 1, "mobile": False},
    )
    try:
        viewport_width = wait.until(
            lambda current_driver: current_driver.execute_script("return window.innerWidth")
        )
        assert viewport_width == 320
        _assert_document_fits(driver)
        assert (
            driver.find_element(by.By.ID, "profile-preparation-submit").rect["width"]
            <= viewport_width - 32
        )
    finally:
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
