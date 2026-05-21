from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from tests.support import (
    build_profile_payload,
    pick_free_port,
    run_test_app_server,
    run_test_app_server_handle,
)

pytestmark = pytest.mark.browser_ui


def _build_chromium_driver():
    webdriver = pytest.importorskip("selenium.webdriver")
    exceptions = pytest.importorskip("selenium.common.exceptions")
    chrome_options = webdriver.ChromeOptions
    chrome_service = pytest.importorskip("selenium.webdriver.chrome.service")

    chromium_binary = Path("/snap/bin/chromium")
    chromedriver_binary = Path("/snap/bin/chromium.chromedriver")
    snap_binary = Path("/usr/bin/snap")
    if not chromium_binary.exists():
        pytest.skip(f"Chromium binary is not available at {chromium_binary}")
    if not chromedriver_binary.exists():
        pytest.skip(f"ChromeDriver binary is not available at {chromedriver_binary}")
    if not snap_binary.exists():
        pytest.skip(f"Snap launcher is not available at {snap_binary}")

    width = 1440
    height = 1600
    debug_port = pick_free_port()
    profile_dir = Path(tempfile.mkdtemp(prefix=f"bpm-browser-tabs-{debug_port}-"))
    browser_log_path = profile_dir / "chromium.log"
    chromedriver_log_path = profile_dir / "chromedriver.log"
    browser_log = browser_log_path.open("w", encoding="utf-8")
    browser_process = subprocess.Popen(
        [
            str(snap_binary),
            "run",
            "chromium",
            "--headless=new",
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={debug_port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-popup-blocking",
            "--lang=en-US",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile_dir}",
            f"--window-size={width},{height}",
            "about:blank",
        ],
        stdout=browser_log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    debugger_url = f"http://127.0.0.1:{debug_port}/json/version"
    deadline = time.time() + 20
    last_error = ""
    debugger_ready = False
    while time.time() < deadline:
        if browser_process.poll() is not None:
            last_error = browser_log_path.read_text(encoding="utf-8", errors="ignore")
            break
        try:
            response = requests.get(debugger_url, timeout=2)
            if response.status_code == 200:
                debugger_ready = True
                break
            last_error = f"debugger probe returned {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.25)
    else:
        last_error = f"Timed out waiting for Chromium debugger at {debugger_url}"

    if not debugger_ready:
        browser_log.close()
        browser_process.terminate()
        browser_process.wait(timeout=10)
        shutil.rmtree(profile_dir, ignore_errors=True)
        pytest.skip(f"Chromium debugger did not become ready: {last_error}")

    options = chrome_options()
    options.debugger_address = f"127.0.0.1:{debug_port}"
    service = chrome_service.Service(
        executable_path=str(chromedriver_binary),
        log_output=str(chromedriver_log_path),
    )
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except exceptions.WebDriverException as exc:
        browser_log.close()
        if browser_process.poll() is None:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                browser_process.kill()
        shutil.rmtree(profile_dir, ignore_errors=True)
        pytest.skip(f"Chromium UI regression could not start in this environment: {exc}")
    driver.set_window_size(width, height)
    driver.set_page_load_timeout(20)
    driver._bpm_browser_process = browser_process
    driver._bpm_browser_profile_dir = profile_dir
    driver._bpm_browser_log = browser_log
    return driver


def _close_chromium_driver(driver) -> None:
    browser_process = getattr(driver, "_bpm_browser_process", None)
    profile_dir = getattr(driver, "_bpm_browser_profile_dir", None)
    browser_log = getattr(driver, "_bpm_browser_log", None)
    try:
        driver.quit()
    finally:
        if browser_process is not None and browser_process.poll() is None:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                browser_process.kill()
        if browser_log is not None:
            browser_log.close()
        if profile_dir is not None:
            shutil.rmtree(profile_dir, ignore_errors=True)


def _switch_to_new_window(driver, wait, previous_handles: set[str]) -> str:
    wait.until(lambda current_driver: len(current_driver.window_handles) == len(previous_handles) + 1)
    new_handles = set(driver.window_handles) - previous_handles
    assert len(new_handles) == 1
    new_handle = next(iter(new_handles))
    driver.switch_to.window(new_handle)
    return new_handle


def _safe_click(driver, element) -> None:
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        element,
    )
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def _click_selector(driver, wait, selector: str) -> None:
    selenium_by = pytest.importorskip("selenium.webdriver.common.by").By
    stale_exception = pytest.importorskip("selenium.common.exceptions").StaleElementReferenceException

    for _ in range(3):
        element = wait.until(
            lambda current_driver: current_driver.find_element(selenium_by.CSS_SELECTOR, selector)
        )
        try:
            _safe_click(driver, element)
            return
        except stale_exception:
            continue

    pytest.fail(f"Could not click selector {selector} without hitting a stale element")


def _select_library_compare_pair(driver, wait, by, ec, first_id: int, second_id: int) -> None:
    first_selector = f'[data-compare-profile-id="{first_id}"]'
    second_selector = f'[data-compare-profile-id="{second_id}"]'
    stale_exception = pytest.importorskip("selenium.common.exceptions").StaleElementReferenceException

    first_button = wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, first_selector)))
    _safe_click(driver, first_button)

    def button_text_is(selector: str, expected: str) -> bool:
        try:
            return driver.find_element(by.By.CSS_SELECTOR, selector).text.strip() == expected
        except stale_exception:
            return False

    wait.until(
        lambda current_driver: button_text_is(second_selector, "Select second")
    )
    second_button = wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, second_selector)))
    _safe_click(driver, second_button)


def _selector_is_visible(driver, selector: str) -> bool:
    return bool(
        driver.execute_script(
            """
            const el = document.querySelector(arguments[0]);
            if (!el) return false;
            if (el.hidden) return false;
            const hiddenAncestor = el.closest("[hidden], .wizard-panel[aria-hidden='true']");
            if (hiddenAncestor) return false;
            const style = window.getComputedStyle(el);
            if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") {
                return false;
            }
            return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            """,
            selector,
        )
    )


def _wait_for_selector_visibility(wait, driver, selector: str, visible: bool = True, message: str = "") -> None:
    wait.until(
        lambda current_driver: _selector_is_visible(current_driver, selector) is visible,
        message=message or f"Selector {selector} did not reach visible={visible}",
    )


def _selector_is_disabled(driver, selector: str) -> bool:
    return bool(
        driver.execute_script(
            """
            const el = document.querySelector(arguments[0]);
            if (!el) return false;
            return !!el.disabled || el.getAttribute("aria-disabled") === "true";
            """,
            selector,
        )
    )


def _wait_for_selector_disabled(wait, driver, selector: str, disabled: bool = True, message: str = "") -> None:
    wait.until(
        lambda current_driver: _selector_is_disabled(current_driver, selector) is disabled,
        message=message or f"Selector {selector} did not reach disabled={disabled}",
    )


def _open_wizard_step(driver, wait, by, step_number: int) -> None:
    button = wait.until(
        lambda current_driver: current_driver.find_element(
            by.By.CSS_SELECTOR, f'.wizard-step[data-step="{step_number}"]'
        )
    )
    _safe_click(driver, button)
    wait.until(
        lambda current_driver: current_driver.find_element(
            by.By.CSS_SELECTOR, f'.wizard-step[data-step="{step_number}"]'
        ).get_attribute("aria-current")
        == "step"
    )
    wait.until(
        lambda current_driver: current_driver.find_element(
            by.By.ID, f"wizard-step-{step_number}"
        ).get_attribute("aria-hidden")
        != "true"
    )


def _assert_step_scope(driver, wait, *, step_number: int, visible_selectors: tuple[str, ...], hidden_selectors: tuple[str, ...]) -> None:
    _open_wizard_step(driver, wait, pytest.importorskip("selenium.webdriver.common.by"), step_number)
    _wait_for_selector_visibility(
        wait,
        driver,
        f"#wizard-step-{step_number}",
        True,
        message=f"wizard step {step_number} did not become visible",
    )
    for selector in visible_selectors:
        _wait_for_selector_visibility(
            wait,
            driver,
            selector,
            True,
            message=f"{selector} should be visible on step {step_number}",
        )
    for selector in hidden_selectors:
        _wait_for_selector_visibility(
            wait,
            driver,
            selector,
            False,
            message=f"{selector} should stay hidden on step {step_number}",
        )


def _toggle_panel(driver, wait, *, toggle_selector: str, panel_selector: str) -> None:
    selenium_by = pytest.importorskip("selenium.webdriver.common.by").By
    timeout_exception = pytest.importorskip("selenium.common.exceptions").TimeoutException

    def panel_is_expanded(current_driver) -> bool:
        toggle_el = current_driver.find_element(selenium_by.CSS_SELECTOR, toggle_selector)
        return toggle_el.get_attribute("aria-expanded") == "true" or _selector_is_visible(
            current_driver,
            panel_selector,
        )

    toggle = wait.until(
        lambda current_driver: current_driver.find_element(
            selenium_by.CSS_SELECTOR,
            toggle_selector,
        )
    )
    if panel_is_expanded(driver):
        _wait_for_selector_visibility(wait, driver, panel_selector, True)
        return

    for _ in range(3):
        _safe_click(driver, toggle)
        try:
            wait.until(panel_is_expanded)
            _wait_for_selector_visibility(wait, driver, panel_selector, True)
            return
        except timeout_exception:
            toggle = wait.until(
                lambda current_driver: current_driver.find_element(
                    selenium_by.CSS_SELECTOR,
                    toggle_selector,
                )
            )

    pytest.fail(f"Could not expand panel {panel_selector} via toggle {toggle_selector}")


def _set_locale(driver, wait, ui, *, locale: str, expected_text: str) -> None:
    select = ui.Select(wait.until(lambda current_driver: current_driver.find_element("id", "lang")))
    select.select_by_value(locale)
    wait.until(lambda current_driver: expected_text in current_driver.find_element("tag name", "body").text)


def _parse_grid_template_columns(template_value: str) -> list[float]:
    values: list[float] = []
    for part in str(template_value or "").split():
        normalized = part.strip()
        if normalized.endswith("px"):
            try:
                values.append(float(normalized[:-2]))
            except ValueError:
                continue
    return values

def _set_theme(driver, wait, ui, *, theme: str) -> None:
    select = ui.Select(wait.until(lambda current_driver: current_driver.find_element("id", "theme")))
    select.select_by_value(theme)
    wait.until(
        lambda current_driver: current_driver.execute_script(
            "return document.documentElement.dataset.theme || 'system';"
        )
        == theme
    )


def _parse_css_rgba(value: str) -> tuple[int, int, int, float]:
    match = re.match(r"rgba?\(([^)]+)\)", str(value).strip())
    if not match:
        raise AssertionError(f"Unsupported CSS color value: {value!r}")
    parts = [part.strip() for part in match.group(1).split(",")]
    if len(parts) < 3:
        raise AssertionError(f"Unexpected CSS color value: {value!r}")
    red = int(float(parts[0]))
    green = int(float(parts[1]))
    blue = int(float(parts[2]))
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    return red, green, blue, alpha


def _surface_luma(driver, selector: str) -> float:
    color = driver.execute_script(
        """
        const el = document.querySelector(arguments[0]);
        if (!el) return null;
        return window.getComputedStyle(el).backgroundColor;
        """,
        selector,
    )
    if not color:
        raise AssertionError(f"Could not read background color for {selector}")
    red, green, blue, _alpha = _parse_css_rgba(color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def test_opening_modes_in_new_tabs_preserves_source_context():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Browser Tab Contract Profile",
        description="Created by the browser regression path",
        owner="tabs@example.org",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            library_search = wait.until(ec.presence_of_element_located((by.By.ID, "search")))
            library_counter = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-profile-count")))
            library_counter_shell = wait.until(
                ec.presence_of_element_located((by.By.CSS_SELECTOR, ".compact-counter"))
            )
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )
            wait.until(lambda current_driver: library_counter.text.strip() == "1")
            wait.until(lambda current_driver: "compact-counter--pending" not in library_counter_shell.get_attribute("class"))
            assert library_counter.is_displayed()

            library_search.clear()
            library_search.send_keys(payload["name"])
            library_handle = driver.current_window_handle
            library_handles = set(driver.window_handles)
            _click_selector(
                driver,
                wait,
                f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]',
            )

            assert driver.current_window_handle == library_handle
            assert urlparse(driver.current_url).path == "/profiles"
            assert library_search.get_attribute("value") == payload["name"]

            edit_handle = _switch_to_new_window(driver, wait, library_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(lambda current_driver: urlparse(current_driver.current_url).path == f"/profiles/{profile_id}/edit")
            _wait_for_selector_disabled(wait, driver, "#save", True)

            step_three_button = wait.until(
                ec.element_to_be_clickable((by.By.CSS_SELECTOR, '.wizard-step[data-step="3"]'))
            )
            _safe_click(driver, step_three_button)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, '.wizard-step[data-step="3"]'
                ).get_attribute("aria-current") == "step"
            )
            edit_source_url = driver.current_url
            edit_handle = driver.current_window_handle
            edit_handles = set(driver.window_handles)
            _safe_click(driver, driver.find_element(by.By.ID, "editor-mode-settings"))

            assert driver.current_window_handle == edit_handle
            assert driver.current_url == edit_source_url
            assert driver.find_element(
                by.By.CSS_SELECTOR, '.wizard-step[data-step="3"]'
            ).get_attribute("aria-current") == "step"

            settings_handle = _switch_to_new_window(driver, wait, edit_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: urlparse(current_driver.current_url).path
                == f"/profiles/{profile_id}/settings"
            )

            settings_search = wait.until(
                ec.presence_of_element_located((by.By.ID, "wizard-settings-search-input"))
            )
            settings_search.clear()
            settings_search.send_keys("Telemetry")
            settings_source_url = driver.current_url
            settings_handles = set(driver.window_handles)
            _safe_click(driver, driver.find_element(by.By.ID, "editor-mode-json"))

            assert driver.current_window_handle == settings_handle
            assert driver.current_url == settings_source_url
            assert driver.find_element(by.By.ID, "wizard-settings-search-input").get_attribute("value") == "Telemetry"

            _switch_to_new_window(driver, wait, settings_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            wait.until(ec.presence_of_element_located((by.By.ID, "download-firefox-policies")))
            json_url = urlparse(driver.current_url)
            json_query = parse_qs(json_url.query)
            assert json_url.path == f"/profiles/{profile_id}/json"
            assert json_query.get("return") == [f"/profiles/{profile_id}/settings"]
            assert json_query.get("focus") == ["editor"]

            driver.switch_to.window(library_handle)
            assert urlparse(driver.current_url).path == "/profiles"
            assert driver.find_element(by.By.ID, "search").get_attribute("value") == payload["name"]
        finally:
            _close_chromium_driver(driver)


def test_json_editor_browser_regression_saves_validates_and_exports_full_document():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="JSON Editor Browser Profile",
        description="JSON editor browser regression",
        owner="json-editor@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        },
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile = create_response.json()
        profile_id = profile["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles/{profile_id}/json?return=/profiles/{profile_id}/settings&focus=editor")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            wait.until(ec.presence_of_element_located((by.By.ID, "editor")))
            wait.until(ec.presence_of_element_located((by.By.ID, "download-firefox-policies")))
            wait.until(
                lambda current_driver: current_driver.execute_script(
                    "return Boolean(window.monaco?.editor?.getModels?.().length);"
                )
            )
            assert driver.find_element(by.By.ID, "advanced-return-link").text.strip() == "Back to previous mode"
            download_link = driver.find_element(by.By.ID, "download-firefox-policies")
            assert download_link.get_attribute("rel") == "noopener"
            assert download_link.get_attribute("href").endswith(
                f"/api/export/profiles/{profile_id}/firefox/policies.json"
            )
            _wait_for_selector_disabled(wait, driver, "#save", True)

            next_document = {
                "policies": {
                    "DisableTelemetry": False,
                    "DisableFirefoxStudies": True,
                }
            }
            driver.execute_script(
                """
                const model = window.monaco.editor.getModels()[0];
                model.setValue(JSON.stringify(arguments[0], null, 2));
                """,
                next_document,
            )
            _wait_for_selector_disabled(wait, driver, "#save", False)
            _click_selector(driver, wait, "#validate")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "validation-preview",
                ).text.strip() != "Validation results will appear here."
            )
            validation_preview_text = driver.find_element(by.By.ID, "validation-preview").text.strip()
            assert "passed" in validation_preview_text.lower(), validation_preview_text
            _click_selector(driver, wait, "#save")
            _wait_for_selector_disabled(wait, driver, "#save", True)

            saved_response = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
            assert saved_response.status_code == 200, saved_response.text
            saved_flags = saved_response.json()["flags"]
            assert saved_flags == {
                "DisableTelemetry": False,
                "DisableFirefoxStudies": True,
            }

            export_response = requests.get(
                f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json",
                timeout=10,
            )
            assert export_response.status_code == 200, export_response.text
            assert export_response.json() == next_document
        finally:
            _close_chromium_driver(driver)


def test_theme_toggle_browser_regression_keeps_surface_cards_consistent_across_light_and_dark():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Theme Surface Contract Profile",
        description="Created by the theme browser regression path",
        owner="theme@example.org",
        schema_version="release-150",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles/{profile_id}/settings")
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, "#overview-panel .editor-chrome-status-item")))
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, "#wizard-preferences-general-presets .wizard-search-engine-preset")
                )
            )
            _click_selector(driver, wait, "#wizard-preferences-general-add")
            _wait_for_selector_visibility(
                wait,
                driver,
                "#wizard-preferences-general-list .wizard-search-engine-card",
                True,
                message="manual preference row did not render",
            )

            _set_theme(driver, wait, ui, theme="light")
            light_overview = _surface_luma(driver, "#overview-panel .editor-chrome-status-item")
            light_preferences = _surface_luma(driver, "#settings-preferences-general .theme-subcard")

            assert light_overview > 170
            assert light_preferences > 170
            light_controls = driver.execute_script(
                """
                return [
                  "#profile-type",
                  "#wizard-preferences-general-presets .wizard-search-engine-preset",
                ].map((selector) => {
                  const el = document.querySelector(selector);
                  const style = window.getComputedStyle(el);
                    return {
                      selector,
                      appearance: style.appearance,
                      colorScheme: style.colorScheme,
                      inlineStyle: el.getAttribute("style") || "",
                    };
                  });
                """
            )
            for control in light_controls:
                assert control["appearance"] == "none"
                assert control["colorScheme"] == "light"
            light_select = driver.execute_script(
                """
                const el = document.querySelector("#profile-type");
                const style = window.getComputedStyle(el);
                return {
                  inlineStyle: el.getAttribute("style") || "",
                  bgRepeat: style.backgroundRepeat,
                  bgSize: style.backgroundSize,
                };
                """
            )
            assert "%235d6b7f" in light_select["inlineStyle"]
            assert light_select["bgRepeat"] == "no-repeat"
            assert "16px" in light_select["bgSize"]

            _set_theme(driver, wait, ui, theme="dark")
            dark_overview = _surface_luma(driver, "#overview-panel .editor-chrome-status-item")
            dark_preferences = _surface_luma(driver, "#settings-preferences-general .theme-subcard")

            assert dark_overview < 90
            assert dark_preferences < 90
            dark_controls = driver.execute_script(
                """
                return [
                  "#profile-type",
                  "#wizard-preferences-general-presets .wizard-search-engine-preset",
                ].map((selector) => {
                  const el = document.querySelector(selector);
                  const style = window.getComputedStyle(el);
                    return {
                      selector,
                      appearance: style.appearance,
                      colorScheme: style.colorScheme,
                      inlineStyle: el.getAttribute("style") || "",
                    };
                  });
                """
            )
            for control in dark_controls:
                assert control["appearance"] == "none"
                assert control["colorScheme"] == "dark"
            dark_select = driver.execute_script(
                """
                const el = document.querySelector("#profile-type");
                const style = window.getComputedStyle(el);
                return {
                  inlineStyle: el.getAttribute("style") || "",
                  bgRepeat: style.backgroundRepeat,
                  bgSize: style.backgroundSize,
                };
                """
            )
            assert "%23cbd5e1" in dark_select["inlineStyle"]
            assert dark_select["bgRepeat"] == "no-repeat"
            assert "16px" in dark_select["bgSize"]

            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "refresh")))
            _set_theme(driver, wait, ui, theme="light")
            light_toolbar = driver.execute_script(
                """
                const selectors = ["#refresh", "#import-firefox-policies"];
                return selectors.map((selector) => {
                  const el = document.querySelector(selector);
                  const style = window.getComputedStyle(el);
                    return {
                      selector,
                      appearance: style.appearance,
                      colorScheme: style.colorScheme,
                      inlineStyle: el.getAttribute("style") || "",
                    };
                  });
                """
            )
            for control in light_toolbar:
                assert control["appearance"] == "none"
                assert control["colorScheme"] == "light"
                assert "248, 250, 252, 0.78" in control["inlineStyle"]
                assert "18, 32, 51" in control["inlineStyle"]

            _set_theme(driver, wait, ui, theme="dark")
            dark_toolbar = driver.execute_script(
                """
                const selectors = ["#refresh", "#import-firefox-policies"];
                return selectors.map((selector) => {
                  const el = document.querySelector(selector);
                  const style = window.getComputedStyle(el);
                    return {
                      selector,
                      appearance: style.appearance,
                      colorScheme: style.colorScheme,
                      inlineStyle: el.getAttribute("style") || "",
                    };
                  });
                """
            )
            for control in dark_toolbar:
                assert control["appearance"] == "none"
                assert control["colorScheme"] == "dark"
                assert "15, 23, 42, 0.86" in control["inlineStyle"]
                assert "226, 232, 240" in control["inlineStyle"]

            driver.get(f"{base_url}/profiles/{profile_id}/json")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            _set_theme(driver, wait, ui, theme="light")
            json_light = driver.execute_script(
                """
                const editorFrame = document.querySelector("#editor");
                const footerLink = document.querySelector(".compact-footer-license-link");
                const editorStyle = window.getComputedStyle(editorFrame);
                const footerStyle = window.getComputedStyle(footerLink);
                return {
                  frameBorder: editorStyle.borderTopColor,
                  footerColor: footerStyle.color,
                  footerDecoration: footerStyle.textDecorationColor,
                };
                """
            )
            assert "148, 163, 184" in json_light["frameBorder"]
            assert "51, 65, 85" in json_light["footerColor"]

            _set_theme(driver, wait, ui, theme="dark")
            json_dark = driver.execute_script(
                """
                const editorFrame = document.querySelector("#editor");
                const footerLink = document.querySelector(".compact-footer-license-link");
                const editorStyle = window.getComputedStyle(editorFrame);
                const footerStyle = window.getComputedStyle(footerLink);
                return {
                  frameBorder: editorStyle.borderTopColor,
                  footerColor: footerStyle.color,
                  footerDecoration: footerStyle.textDecorationColor,
                };
                """
            )
            assert "148, 163, 184" in json_dark["frameBorder"]
            assert "203, 213, 225" in json_dark["footerColor"]
            assert "148, 163, 184" in json_dark["footerDecoration"]
        finally:
            _close_chromium_driver(driver)


def test_all_settings_manager_browser_regression_persists_policy_preference_and_removal():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    from app.models.profile import Profile

    payload = build_profile_payload(
        name="All Settings Manager Browser Profile",
        description="All settings browser regression",
        owner="all-settings@example.org",
        schema_version="release-150",
        flags={"DisableTelemetry": True},
    )

    with run_test_app_server_handle() as server:
        base_url = server.base_url
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        with server.session_factory() as session:
            profile = session.get(Profile, profile_id)
            assert profile is not None
            profile.flags = {
                **(profile.flags or {}),
                "FuturePolicy": {"Enabled": True},
            }
            session.commit()

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles/{profile_id}/settings")
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(ec.presence_of_element_located((by.By.ID, "all-settings-list")))
            wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '#all-settings-list [data-settings-entry-id="NewTabPage"]',
                ))
            )

            _click_selector(driver, wait, '#all-settings-list [data-settings-entry-id="NewTabPage"]')
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "NewTabPage"
            )
            new_tab_page_select = wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '#all-settings-detail-panel [data-schema-policy-field="__value__"]',
                ))
            )
            ui.Select(new_tab_page_select).select_by_value("true")
            _wait_for_selector_disabled(wait, driver, "#save", False)

            _safe_click(driver, driver.find_element(by.By.ID, "all-settings-add-preference"))
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "__new_preference__"
            )
            new_pref_name = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-name]",
            )
            new_pref_name.clear()
            new_pref_name.send_keys("browser.test.allSettingsSaved")
            new_pref_type = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-type]",
            )
            ui.Select(new_pref_type).select_by_value("boolean")
            new_pref_value = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-value-select]",
            )
            ui.Select(new_pref_value).select_by_value("true")
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#all-settings-detail-panel [data-settings-detail-apply-preference]",
                ),
            )
            wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '[data-settings-entry-id="browser.test.allSettingsSaved"]',
                ))
            )

            settings_search = wait.until(
                ec.presence_of_element_located((by.By.ID, "wizard-settings-search-input"))
            )
            settings_search.clear()
            settings_search.send_keys("allSettingsSaved")
            search_result_selector = (
                '#wizard-settings-search-results '
                '[data-settings-search-target="all-settings-entry:preference:browser.test.allSettingsSaved"]'
            )
            wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, search_result_selector)))
            _click_selector(driver, wait, search_result_selector)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "browser.test.allSettingsSaved"
            )

            unknown_review_button = wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '[data-settings-review-filter="unknown"]',
                ))
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-review-filter="unknown"]',
                ).get_attribute("data-settings-review-count")
                == "1"
            )
            _safe_click(driver, unknown_review_button)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "FuturePolicy"
            )
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#all-settings-detail-panel [data-settings-detail-remove]",
                ),
            )
            wait.until(
                lambda current_driver: len(current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    '[data-settings-entry-id="FuturePolicy"]',
                )) == 0
            )

            _wait_for_selector_disabled(wait, driver, "#validate", False)
            _click_selector(driver, wait, "#validate")
            _wait_for_selector_disabled(wait, driver, "#save", False)
            _click_selector(driver, wait, "#save")
            _wait_for_selector_disabled(wait, driver, "#save", True)

            saved_profile_response = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
            assert saved_profile_response.status_code == 200, saved_profile_response.text
            saved_flags = saved_profile_response.json()["flags"]
            assert saved_flags["NewTabPage"] is True
            assert saved_flags["Preferences"]["browser.test.allSettingsSaved"] == {
                "Status": "default",
                "Value": True,
                "Type": "boolean",
            }
            assert "FuturePolicy" not in saved_flags
        finally:
            _close_chromium_driver(driver)


def test_compact_toolbar_browser_regression_stays_inside_narrow_viewport():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Narrow Header Contract Profile",
        description="Created by the narrow header browser regression path",
        owner="narrow-header@example.org",
        schema_version="release-150",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        driver.set_window_size(390, 1200)

        try:
            for path, ready_selector in [
                ("/profiles", "#library-panel"),
                (f"/profiles/{profile_id}/edit", "#wizard-panel"),
                (f"/profiles/{profile_id}/settings", "#settings-panel"),
                (f"/profiles/{profile_id}/json", "#editor-panel"),
            ]:
                driver.get(f"{base_url}{path}")
                wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".compact-toolbar")))
                wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))

                metrics = driver.execute_script(
                    """
                    const viewportWidth = document.documentElement.clientWidth;
                    const selectors = [
                      ".compact-toolbar",
                      ".compact-toolbar-main",
                      ".compact-toolbar-side",
                      ".compact-toolbar-actions",
                      ".compact-toolbar-control",
                      ".compact-counter",
                    ];
                    const offenders = [];
                    for (const selector of selectors) {
                      for (const el of document.querySelectorAll(selector)) {
                        const rect = el.getBoundingClientRect();
                        if (rect.left < -1 || rect.right > viewportWidth + 1) {
                          offenders.push({
                            selector,
                            left: Math.round(rect.left),
                            right: Math.round(rect.right),
                            viewportWidth,
                            text: (el.textContent || "").trim().replace(/\\s+/g, " ").slice(0, 80),
                          });
                        }
                      }
                    }
                    const toolbar = document.querySelector(".compact-toolbar");
                    return {
                      viewportWidth,
                      toolbarScrollWidth: toolbar.scrollWidth,
                      toolbarClientWidth: toolbar.clientWidth,
                      offenders,
                    };
                    """
                )

                assert metrics["toolbarScrollWidth"] <= metrics["toolbarClientWidth"] + 1, metrics
                assert metrics["offenders"] == [], metrics
        finally:
            _close_chromium_driver(driver)


def test_library_summary_browser_regression_covers_zero_many_filter_and_ru_label():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload_alpha = build_profile_payload(
        name="Library Alpha Profile",
        description="Alpha profile for library summary checks",
        owner="alpha@example.org",
    )
    payload_beta = build_profile_payload(
        name="Library Beta Profile",
        description="Beta profile for library summary checks",
        owner="beta@example.org",
    )

    with run_test_app_server() as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            library_counter = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-profile-count")))
            library_counter_label = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-profile-label")))
            library_counter_shell = wait.until(
                ec.presence_of_element_located((by.By.CSS_SELECTOR, ".compact-counter"))
            )
            list_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-summary")))
            list_total_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-total-summary")))
            library_search = wait.until(ec.presence_of_element_located((by.By.ID, "search")))
            schema_filter = wait.until(ec.presence_of_element_located((by.By.ID, "library-schema-filter")))
            lifecycle_filter = wait.until(ec.presence_of_element_located((by.By.ID, "library-lifecycle-filter")))
            validation_filter = wait.until(ec.presence_of_element_located((by.By.ID, "library-validation-filter")))
            sort_select = wait.until(ec.presence_of_element_located((by.By.ID, "sort")))
            order_select = wait.until(ec.presence_of_element_located((by.By.ID, "order")))
            refresh_button = wait.until(ec.element_to_be_clickable((by.By.ID, "refresh")))

            wait.until(lambda current_driver: library_counter.text.strip() == "0")
            wait.until(lambda current_driver: list_summary.text.strip() == "0")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "0")
            wait.until(lambda current_driver: "compact-counter--pending" not in library_counter_shell.get_attribute("class"))
            wait.until(lambda current_driver: "No profiles to show" in current_driver.find_element(by.By.TAG_NAME, "body").text)
            assert library_counter.is_displayed()
            assert library_counter_label.text.strip() == "Profiles in library"
            assert schema_filter.is_displayed()
            assert lifecycle_filter.is_displayed()
            assert validation_filter.is_displayed()
            assert sort_select.is_displayed()
            assert order_select.is_displayed()

            create_alpha = requests.post(f"{base_url}/api/profiles", json=payload_alpha, timeout=10)
            assert create_alpha.status_code == 201, create_alpha.text
            alpha_id = create_alpha.json()["id"]
            create_beta = requests.post(f"{base_url}/api/profiles", json=payload_beta, timeout=10)
            assert create_beta.status_code == 201, create_beta.text
            beta_id = create_beta.json()["id"]

            _safe_click(driver, refresh_button)
            wait.until(lambda current_driver: library_counter.text.strip() == "2")
            wait.until(lambda current_driver: list_summary.text.strip() == "2")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{alpha_id}/edit"]')
                )
            )
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{beta_id}/edit"]')
                )
            )
            assert library_counter_label.text.strip() == "Profiles in library"

            driver.execute_script(
                """
                const sort = document.getElementById('sort');
                sort.value = 'name';
                sort.dispatchEvent(new Event('change', { bubbles: true }));
                const order = document.getElementById('order');
                order.value = 'asc';
                order.dispatchEvent(new Event('change', { bubbles: true }));
                """
            )
            wait.until(
                lambda current_driver: current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    ".library-row-title-button",
                )[0].text.strip() == "Library Alpha Profile"
            )
            driver.execute_script(
                """
                const order = document.getElementById('order');
                order.value = 'desc';
                order.dispatchEvent(new Event('change', { bubbles: true }));
                """
            )
            wait.until(
                lambda current_driver: current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    ".library-row-title-button",
                )[0].text.strip() == "Library Beta Profile"
            )

            library_search.clear()
            library_search.send_keys("Alpha")
            wait.until(lambda current_driver: list_summary.text.strip() == "1")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{alpha_id}/edit"]')
                )
            )
            wait.until(
                lambda current_driver: not current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{beta_id}/edit"]',
                )
            )

            library_search.clear()
            library_search.send_keys("No such profile")
            wait.until(lambda current_driver: list_summary.text.strip() == "0")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                lambda current_driver: "No profiles to show" in current_driver.find_element(by.By.TAG_NAME, "body").text
            )

            _set_locale(driver, wait, ui, locale="ru", expected_text="МЕНЕДЖЕР ПРОФИЛЕЙ БРАУЗЕРА")
            wait.until(lambda current_driver: library_counter.text.strip() == "2")
            wait.until(lambda current_driver: list_summary.text.strip() == "0")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                lambda current_driver: "Профилей для показа нет"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            assert library_counter_label.text.strip() == "Профиля в библиотеке"
        finally:
            _close_chromium_driver(driver)


def test_library_validation_browser_regression_surfaces_not_validated_profiles():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    validated_payload = build_profile_payload(
        name="Validated library profile",
        description="Profile with managed rules",
    )
    not_validated_payload = build_profile_payload(
        name="Empty library profile",
        description="Profile without managed rules",
    )
    not_validated_payload["flags"] = {}

    with run_test_app_server() as base_url:
        validated_response = requests.post(f"{base_url}/api/profiles", json=validated_payload, timeout=10)
        not_validated_response = requests.post(
            f"{base_url}/api/profiles",
            json=not_validated_payload,
            timeout=10,
        )
        assert validated_response.status_code == 201, validated_response.text
        assert not_validated_response.status_code == 201, not_validated_response.text
        validated_id = validated_response.json()["id"]
        not_validated_id = not_validated_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{not_validated_id}/edit"]')
                )
            )
            wait.until(
                lambda current_driver: "Not validated" in current_driver.find_element(
                    by.By.XPATH,
                    f'//a[@href="/profiles/{not_validated_id}/edit"]/ancestor::div[contains(@class,"library-row-grid")]',
                ).text
            )
            not_validated_row = driver.find_element(
                by.By.XPATH,
                f'//a[@href="/profiles/{not_validated_id}/edit"]/ancestor::div[contains(@class,"library-row-grid")]',
            )
            assert "Not validated" in not_validated_row.text
            assert not_validated_row.find_element(
                by.By.CSS_SELECTOR,
                ".profile-list-status--not-validated",
            )

            validation_filter = driver.find_element(by.By.ID, "library-validation-filter")
            driver.execute_script(
                """
                const select = arguments[0];
                select.value = 'not_validated';
                select.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                validation_filter,
            )
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{not_validated_id}/edit"]')
                )
            )
            wait.until(
                lambda current_driver: not current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{validated_id}/edit"]',
                )
            )
        finally:
            _close_chromium_driver(driver)


def test_library_layout_browser_regression_keeps_actions_visible_in_ru_with_long_names():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Очень длинный корпоративный профиль для проверки ширины библиотеки и кнопки открытия",
        description="Long-name library layout regression",
        owner="layout@example.org",
        schema_version="release-150",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )
            _set_locale(driver, wait, ui, locale="ru", expected_text="МЕНЕДЖЕР ПРОФИЛЕЙ БРАУЗЕРА")

            table_shell = wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".library-table-shell")))
            table_head = wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".library-table-head")))
            row_grid = wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".library-row-grid")))
            row_context = wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".library-row-context")))
            open_button = wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )

            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]',
                ).text.strip() == "Открыть профиль"
            )
            open_button = wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )
            row_context = wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ".library-row-context")))

            layout_probe = driver.execute_script(
                """
                const shell = document.querySelector('.library-table-shell');
                const head = document.querySelector('.library-table-head');
                const row = document.querySelector('.library-row-grid');
                const button = arguments[0];
                const shellRect = shell.getBoundingClientRect();
                const buttonRect = button.getBoundingClientRect();
                return {
                  shellClientWidth: shell.clientWidth,
                  shellScrollWidth: shell.scrollWidth,
                  headColumns: window.getComputedStyle(head).gridTemplateColumns,
                  rowColumns: window.getComputedStyle(row).gridTemplateColumns,
                  buttonFitsHorizontally: buttonRect.right <= shellRect.right + 1 && buttonRect.left >= shellRect.left - 1,
                  buttonVisibleWidth: buttonRect.width,
                };
                """,
                open_button,
            )

            assert layout_probe["shellScrollWidth"] <= layout_probe["shellClientWidth"] + 8
            head_columns = _parse_grid_template_columns(layout_probe["headColumns"])
            row_columns = _parse_grid_template_columns(layout_probe["rowColumns"])
            assert len(head_columns) == len(row_columns) == 6
            assert all(abs(head - row) <= 1.0 for head, row in zip(head_columns, row_columns, strict=True))
            assert layout_probe["buttonFitsHorizontally"] is True
            assert layout_probe["buttonVisibleWidth"] > 120
            table_shell = driver.find_element(by.By.CSS_SELECTOR, ".library-table-shell")
            table_head = driver.find_element(by.By.CSS_SELECTOR, ".library-table-head")
            row_grid = driver.find_element(by.By.CSS_SELECTOR, ".library-row-grid")
            assert table_shell.is_displayed()
            assert table_head.is_displayed()
            assert row_grid.is_displayed()
            assert row_context.text.splitlines() == ["layout@example.org", "Long-name library layout regression"]
            assert open_button.is_displayed()
        finally:
            _close_chromium_driver(driver)


def test_library_mobile_cards_browser_regression_show_key_metadata_without_overflow():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Mobile library profile with a readable working title",
        description="Mobile card note",
        owner="mobile-library@example.org",
        schema_version="release-150",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        driver.set_window_size(390, 1200)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )

            metrics = driver.execute_script(
                """
                const viewportWidth = document.documentElement.clientWidth;
                const row = document.querySelector('.library-row-grid');
                const facts = document.querySelector('.library-row-facts');
                const head = document.querySelector('.library-table-head');
                const rowStyle = window.getComputedStyle(row);
                const factsStyle = window.getComputedStyle(facts);
                return {
                  documentWidth: document.documentElement.scrollWidth,
                  viewportWidth,
                  rowAreas: rowStyle.gridTemplateAreas,
                  factsDisplay: factsStyle.display,
                  factsColumns: factsStyle.gridTemplateColumns,
                  headDisplay: window.getComputedStyle(head).display,
                };
                """
            )

            body_text = driver.find_element(by.By.TAG_NAME, "body").text
            assert "Mobile library profile with a readable working title" in body_text
            assert "mobile-library@example.org" in body_text
            assert "Mobile card note" in body_text
            assert "Release 150" in body_text
            assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1
            assert metrics["headDisplay"] == "none"
            assert metrics["rowAreas"] == '"primary" "context" "facts" "actions"'
            assert metrics["factsDisplay"] == "grid"
            assert len(_parse_grid_template_columns(metrics["factsColumns"])) == 2
        finally:
            _close_chromium_driver(driver)


def test_library_row_action_set_browser_regression_exposes_direct_workflows():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    active_payload = build_profile_payload(
        name="Action Set Active Profile",
        description="Active action set profile",
        owner="actions-active@example.org",
    )
    archived_payload = build_profile_payload(
        name="Action Set Archived Profile",
        description="Archived action set profile",
        owner="actions-archived@example.org",
    )

    with run_test_app_server() as base_url:
        active_response = requests.post(f"{base_url}/api/profiles", json=active_payload, timeout=10)
        archived_response = requests.post(f"{base_url}/api/profiles", json=archived_payload, timeout=10)
        assert active_response.status_code == 201, active_response.text
        assert archived_response.status_code == 201, archived_response.text
        active_id = active_response.json()["id"]
        archived_id = archived_response.json()["id"]
        deleted_response = requests.delete(f"{base_url}/api/profiles/{archived_id}", timeout=10)
        assert deleted_response.status_code == 204, deleted_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{active_id}/edit"]')
                )
            )
            active_row = driver.find_element(
                by.By.XPATH,
                f'//a[@href="/profiles/{active_id}/edit"]/ancestor::div[contains(@class,"library-row-grid")]',
            )
            assert active_row.find_element(by.By.LINK_TEXT, "All settings").get_attribute("href").endswith(
                f"/profiles/{active_id}/settings"
            )
            assert active_row.find_element(by.By.LINK_TEXT, "JSON").get_attribute("href").endswith(
                f"/profiles/{active_id}/json"
            )
            duplicate_href = active_row.find_element(by.By.LINK_TEXT, "Duplicate").get_attribute("href")
            assert duplicate_href.endswith(
                f"/profiles/new?clone_from={active_id}"
            )
            assert active_row.find_element(by.By.LINK_TEXT, "Export").get_attribute("href").endswith(
                f"/api/export/profiles/{active_id}/firefox/policies.json?download=1"
            )
            assert active_row.find_element(by.By.LINK_TEXT, "Export").get_attribute("download") == ""

            driver.get(duplicate_href)
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip() == "DRAFT"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "current-name").text.strip().endswith("(copy)")
            )

            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{active_id}/edit"]')
                )
            )
            active_row = driver.find_element(
                by.By.XPATH,
                f'//a[@href="/profiles/{active_id}/edit"]/ancestor::div[contains(@class,"library-row-grid")]',
            )
            archive_button = active_row.find_element(by.By.XPATH, './/button[normalize-space()="Archive profile"]')

            driver.execute_script("window.confirm = () => true;")
            _safe_click(driver, archive_button)
            wait.until(
                lambda current_driver: "Profile Action Set Active Profile archived."
                in current_driver.find_element(by.By.ID, "status").text
            )
            wait.until(
                lambda current_driver: not current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{active_id}/edit"]',
                )
            )

            lifecycle_filter = driver.find_element(by.By.ID, "library-lifecycle-filter")
            driver.execute_script(
                """
                const select = arguments[0];
                select.value = 'archived';
                select.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                lifecycle_filter,
            )
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{archived_id}/edit"]')
                )
            )
            archived_row = driver.find_element(
                by.By.XPATH,
                f'//a[@href="/profiles/{archived_id}/edit"]/ancestor::div[contains(@class,"library-row-grid")]',
            )
            assert archived_row.find_element(by.By.XPATH, './/button[normalize-space()="Restore profile"]')
            assert archived_row.find_element(
                by.By.XPATH,
                './/*[contains(@class,"library-row-secondary-action--disabled") and normalize-space()="Export"]',
            ).get_attribute("aria-disabled") == "true"

            restore_button = archived_row.find_element(by.By.XPATH, './/button[normalize-space()="Restore profile"]')
            _safe_click(driver, restore_button)
            wait.until(
                lambda current_driver: "Profile Action Set Archived Profile restored."
                in current_driver.find_element(by.By.ID, "status").text
            )
            wait.until(
                lambda current_driver: not current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{archived_id}/edit"]',
                )
            )

        finally:
            _close_chromium_driver(driver)


def test_library_import_browser_regression_shows_visible_feedback_and_creates_profile():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            status = wait.until(ec.visibility_of_element_located((by.By.ID, "import-firefox-policies-status")))
            assert "Import creates a new profile" in status.text

            driver.execute_script(
                """
                const input = document.getElementById('import-firefox-policies-file');
                const payload = JSON.stringify({ policies: { DisableTelemetry: true } });
                const file = new File([payload], 'workstation-baseline.json', { type: 'application/json' });
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
                """
            )

            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "import-firefox-policies-status",
                ).text.strip() == "Imported new profile workstation-baseline. Schema: ESR 140.10. Validation: Passed."
            )
            assert driver.find_element(by.By.ID, "status").text.strip() == (
                "Imported new profile workstation-baseline. Schema: ESR 140.10. Validation: Passed."
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "import-firefox-policies",
                ).get_attribute("aria-busy") == "false"
            )
            assert driver.find_element(by.By.LINK_TEXT, "workstation-baseline")

            driver.execute_script(
                """
                const input = document.getElementById('import-firefox-policies-file');
                const file = new File(['{"policies":'], 'broken.json', { type: 'application/json' });
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
                """
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "import-firefox-policies-status",
                ).text.startswith("Import error: Invalid JSON:")
            )
            assert driver.find_element(by.By.ID, "import-firefox-policies").is_enabled()
        finally:
            _close_chromium_driver(driver)


def test_library_compare_browser_regression_selects_two_profiles_directly():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    base_payload = build_profile_payload(
        name="Compare Baseline Profile",
        description="Baseline profile for library compare regression",
        owner="compare-a@example.org",
    )
    other_payload = build_profile_payload(
        name="Compare Other Profile",
        description="Other profile for library compare regression",
        owner="compare-b@example.org",
    )
    other_payload["flags"]["DisableTelemetry"] = True

    with run_test_app_server() as base_url:
        base_response = requests.post(f"{base_url}/api/profiles", json=base_payload, timeout=10)
        assert base_response.status_code == 201, base_response.text
        base_profile_id = base_response.json()["id"]

        other_response = requests.post(f"{base_url}/api/profiles", json=other_payload, timeout=10)
        assert other_response.status_code == 201, other_response.text
        other_profile_id = other_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{base_profile_id}/edit"]')
                )
            )
            assert driver.find_element(
                by.By.CSS_SELECTOR,
                f'[data-compare-profile-id="{base_profile_id}"]',
            ).text.strip() == "Select first"
            assert driver.find_element(
                by.By.CSS_SELECTOR,
                f'[data-compare-profile-id="{other_profile_id}"]',
            ).text.strip() == "Select first"

            baseline_compare_button = wait.until(
                ec.element_to_be_clickable(
                    (by.By.CSS_SELECTOR, f'[data-compare-profile-id="{base_profile_id}"]')
                )
            )
            _safe_click(driver, baseline_compare_button)

            stale_exception = pytest.importorskip("selenium.common.exceptions").StaleElementReferenceException

            def compare_button_text_is(selector: str, expected: str) -> bool:
                try:
                    return driver.find_element(by.By.CSS_SELECTOR, selector).text.strip() == expected
                except stale_exception:
                    return False

            wait.until(
                lambda current_driver: compare_button_text_is(
                    f'[data-compare-profile-id="{base_profile_id}"]',
                    "First selected",
                )
            )
            wait.until(
                lambda current_driver: compare_button_text_is(
                    f'[data-compare-profile-id="{other_profile_id}"]',
                    "Select second",
                )
            )
            assert "First profile selected" in driver.find_element(by.By.ID, "compare-empty-copy").text

            compare_button = wait.until(
                ec.element_to_be_clickable(
                    (by.By.CSS_SELECTOR, f'[data-compare-profile-id="{other_profile_id}"]')
                )
            )
            _safe_click(driver, compare_button)

            wait.until(lambda current_driver: _selector_is_visible(current_driver, "#compare-active"))
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-current-name").text.strip()
                == base_payload["name"]
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-other-name").text.strip()
                == other_payload["name"]
            )
            assert driver.find_element(by.By.ID, "compare-clear").is_displayed()
            assert "Release" not in driver.find_element(by.By.ID, "compare-current-copy").text
            assert driver.find_element(by.By.ID, "compare-policy-count").text.strip().isdigit()
        finally:
            _close_chromium_driver(driver)


def test_primary_modes_browser_regression_stay_russian_and_fit_viewport_in_ru():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Профиль для полного русского QA-прохода",
        description="Russian primary modes QA",
        owner="ru-qa@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )
    forbidden_fragments = (
        "Browser Profile Manager",
        "Profile library",
        "Guided editor",
        "All settings catalog",
        "Search all controls",
        "Firefox Account",
        "Advanced settings",
    )

    def assert_ru_surface_is_clean(driver, expected_fragments: tuple[str, ...]) -> None:
        body_text = driver.find_element(by.By.TAG_NAME, "body").text
        for fragment in expected_fragments:
            assert fragment in body_text
        for fragment in forbidden_fragments:
            assert fragment not in body_text
        layout_probe = driver.execute_script(
            """
            return {
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: window.innerWidth,
            };
            """
        )
        assert layout_probe["documentWidth"] <= layout_probe["viewportWidth"] + 1

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]')
                )
            )
            _set_locale(driver, wait, ui, locale="ru", expected_text="МЕНЕДЖЕР ПРОФИЛЕЙ БРАУЗЕРА")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]',
                ).text.strip() == "Открыть профиль"
            )
            assert_ru_surface_is_clean(
                driver,
                ("Профиль для полного русского QA-прохода", "Открыть профиль"),
            )

            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(
                lambda current_driver: "Пошаговый редактор"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            assert_ru_surface_is_clean(
                driver,
                ("Пошаговый редактор", "Пользователи, дополнения и сайты"),
            )

            driver.get(f"{base_url}/profiles/{profile_id}/settings")
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: "Каталог всех настроек"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            assert_ru_surface_is_clean(
                driver,
                ("Каталог всех настроек", "Аккаунт Mozilla"),
            )

            driver.get(f"{base_url}/profiles/{profile_id}/json")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            wait.until(
                lambda current_driver: "JSON-редактор"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            assert_ru_surface_is_clean(
                driver,
                ("JSON-редактор", "Скачать Firefox policies.json"),
            )
        finally:
            _close_chromium_driver(driver)


def test_responsive_ui_acceptance_covers_ru_library_actions_and_ai_schema_split():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    release_payload = build_profile_payload(
        name="RU Responsive Release Profile",
        description="Release profile for responsive acceptance",
        owner="responsive-release@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "AIControls": {
                "Default": {
                    "Value": "blocked",
                    "Locked": True,
                }
            },
            "VisualSearchEnabled": False,
        },
    )
    esr_payload = build_profile_payload(
        name="RU Responsive ESR Profile",
        description="ESR profile for responsive acceptance",
        owner="responsive-esr@example.org",
        schema_version="esr-140.10",
        flags={"DisableTelemetry": True},
    )

    def assert_document_fits_viewport(driver) -> None:
        metrics = driver.execute_script(
            """
            return {
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: window.innerWidth,
            };
            """
        )
        assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics

    def assert_library_action_buttons_fit(driver) -> None:
        offenders = driver.execute_script(
            """
            return Array.from(document.querySelectorAll(".library-row-actions .button-base"))
              .map((el) => {
                const rect = el.getBoundingClientRect();
                return {
                  text: (el.textContent || "").trim().replace(/\\s+/g, " "),
                  width: rect.width,
                  scrollWidth: el.scrollWidth,
                  height: rect.height,
                  scrollHeight: el.scrollHeight,
                };
              })
              .filter((entry) => (
                entry.scrollWidth > Math.ceil(entry.width) + 1
                || entry.scrollHeight > Math.ceil(entry.height) + 1
              ));
            """
        )
        assert offenders == []

    with run_test_app_server() as base_url:
        release_response = requests.post(f"{base_url}/api/profiles", json=release_payload, timeout=10)
        assert release_response.status_code == 201, release_response.text
        release_profile_id = release_response.json()["id"]
        esr_response = requests.post(f"{base_url}/api/profiles", json=esr_payload, timeout=10)
        assert esr_response.status_code == 201, esr_response.text
        esr_profile_id = esr_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.set_window_size(1440, 1500)
            driver.get(f"{base_url}/profiles")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{release_profile_id}/edit"]')
                )
            )
            _set_locale(driver, wait, ui, locale="ru", expected_text="МЕНЕДЖЕР ПРОФИЛЕЙ БРАУЗЕРА")
            wait.until(
                lambda current_driver: "Все настройки"
                in current_driver.find_element(by.By.ID, "list").text
            )
            assert_document_fits_viewport(driver)
            assert_library_action_buttons_fit(driver)

            driver.set_window_size(390, 1200)
            wait.until(lambda current_driver: current_driver.execute_script("return window.innerWidth") <= 390)
            assert_document_fits_viewport(driver)
            assert_library_action_buttons_fit(driver)

            for route, ready_selector in (
                (f"/profiles/{release_profile_id}/edit", "#wizard-panel"),
                (f"/profiles/{release_profile_id}/settings", "#settings-panel"),
                (f"/profiles/{release_profile_id}/json", "#editor-panel"),
            ):
                driver.get(f"{base_url}{route}")
                wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))
                assert_document_fits_viewport(driver)

            driver.set_window_size(1440, 1500)
            driver.get(f"{base_url}/profiles/{release_profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            _open_wizard_step(driver, wait, by, 5)
            _wait_for_selector_visibility(wait, driver, "#wizard-ai-release-content", True)
            _wait_for_selector_visibility(wait, driver, "#wizard-ai-esr-empty-state", False)
            _wait_for_selector_visibility(wait, driver, "#wizard-ai-policy-controls", True)
            release_ai_text = driver.find_element(by.By.ID, "wizard-step-5").text
            assert "Политики ИИ Firefox 150" in release_ai_text
            assert "Настройки генеративного ИИ" in release_ai_text
            assert "GenerativeAI" not in release_ai_text
            assert "AIControls" not in release_ai_text
            assert "Enabled" not in release_ai_text
            assert "Chatbot" not in release_ai_text
            assert "LinkPreviews" not in release_ai_text
            assert "TabGroups" not in release_ai_text
            assert "Устарев" not in release_ai_text
            assert "поставщик" not in release_ai_text.lower()
            assert "поставщиков" not in release_ai_text.lower()
            assert "нет полей" not in release_ai_text.lower()
            assert not driver.find_elements(by.By.ID, "wizard-ai-providers-handoff")

            driver.get(f"{base_url}/profiles/{esr_profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            _open_wizard_step(driver, wait, by, 5)
            _wait_for_selector_visibility(wait, driver, "#wizard-ai-esr-empty-state", True)
            _wait_for_selector_visibility(wait, driver, "#wizard-ai-release-content", False)
            esr_ai_text = driver.find_element(by.By.ID, "wizard-step-5").text
            assert "Эта схема не поддерживает настройки ИИ" in esr_ai_text
            assert "Политики ИИ Firefox 150" not in esr_ai_text
            assert "Настройки генеративного ИИ" not in esr_ai_text
        finally:
            _close_chromium_driver(driver)


def test_library_compare_browser_regression_reports_expected_counts_and_guided_areas():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    shared_owner = "compare-shared@example.org"
    shared_description = "Profiles used for compare diff verification"
    base_payload = build_profile_payload(
        name="Compare Diff Baseline",
        description=shared_description,
        owner=shared_owner,
        flags={
            "DisableTelemetry": True,
            "Preferences": {
                "browser.search.suggest.enabled": {
                    "Value": False,
                    "Status": "locked",
                    "Type": "boolean",
                }
            },
        },
    )
    other_payload = build_profile_payload(
        name="Compare Diff Other",
        description=shared_description,
        owner=shared_owner,
        flags={
            "DisableTelemetry": False,
        },
    )

    with run_test_app_server() as base_url:
        base_response = requests.post(f"{base_url}/api/profiles", json=base_payload, timeout=10)
        assert base_response.status_code == 201, base_response.text
        base_profile_id = base_response.json()["id"]

        other_response = requests.post(f"{base_url}/api/profiles", json=other_payload, timeout=10)
        assert other_response.status_code == 201, other_response.text
        other_profile_id = other_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            _select_library_compare_pair(driver, wait, by, ec, base_profile_id, other_profile_id)

            wait.until(lambda current_driver: _selector_is_visible(current_driver, "#compare-active"))
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-current-name").text.strip()
                == base_payload["name"]
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-other-name").text.strip()
                == other_payload["name"]
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-metadata-count").text.strip() == "1"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-policy-count").text.strip() == "1"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-preference-count").text.strip() == "1"
            )

            compare_changes_text = driver.find_element(by.By.ID, "compare-changes-list").text
            assert "Profile name" in compare_changes_text
            assert "DisableTelemetry" in compare_changes_text
            assert "browser.search.suggest.enabled" in compare_changes_text

            guided_areas_text = driver.find_element(by.By.ID, "compare-guided-areas-list").text
            assert "Browser access and defaults" in guided_areas_text
            assert "Security and privacy" in guided_areas_text
            assert "browser.search.suggest.enabled" in guided_areas_text
            assert "DisableTelemetry" in guided_areas_text

            assert "Schema: ESR 140.10." in driver.find_element(by.By.ID, "compare-current-copy").text
            assert "Schema: ESR 140.10." in driver.find_element(by.By.ID, "compare-other-copy").text

        finally:
            _close_chromium_driver(driver)


def test_library_compare_browser_regression_keeps_metadata_only_diffs_free_of_policy_noise():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    shared_owner = "compare-metadata@example.org"
    shared_description = "Profiles used for metadata-only compare verification"
    shared_flags = {
        "DisableTelemetry": True,
        "Preferences": {
            "browser.search.suggest.enabled": {
                "Value": False,
                "Status": "locked",
                "Type": "boolean",
            }
        },
    }
    base_payload = build_profile_payload(
        name="Compare Metadata Baseline",
        description=shared_description,
        owner=shared_owner,
        flags=shared_flags,
    )
    other_payload = build_profile_payload(
        name="Compare Metadata Other",
        description=shared_description,
        owner=shared_owner,
        flags=shared_flags,
    )

    with run_test_app_server() as base_url:
        base_response = requests.post(f"{base_url}/api/profiles", json=base_payload, timeout=10)
        assert base_response.status_code == 201, base_response.text
        base_profile_id = base_response.json()["id"]

        other_response = requests.post(f"{base_url}/api/profiles", json=other_payload, timeout=10)
        assert other_response.status_code == 201, other_response.text
        other_profile_id = other_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            _select_library_compare_pair(driver, wait, by, ec, base_profile_id, other_profile_id)

            wait.until(lambda current_driver: _selector_is_visible(current_driver, "#compare-active"))
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-metadata-count").text.strip() == "1"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-policy-count").text.strip() == "0"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(by.By.ID, "compare-preference-count").text.strip() == "0"
            )

            compare_changes_text = driver.find_element(by.By.ID, "compare-changes-list").text
            assert "Profile name" in compare_changes_text
            assert "DisableTelemetry" not in compare_changes_text
            assert "browser.search.suggest.enabled" not in compare_changes_text

            guided_areas_text = driver.find_element(by.By.ID, "compare-guided-areas-list").text
            assert "Profile and baseline" in guided_areas_text
            assert "Browser access and defaults" not in guided_areas_text
            assert "Security and privacy" not in guided_areas_text

        finally:
            _close_chromium_driver(driver)


def test_release_150_profile_browser_regression_loads_cleanly_in_guided_and_json_modes():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Corporate 150 Browser Regression",
        description="Release 150 profile should load cleanly in guided and json modes",
        schema_version="release-150",
        flags={
            "AppAutoUpdate": False,
            "DisableAppUpdate": True,
            "DisableSystemAddonUpdate": True,
            "DisableTelemetry": True,
            "DisableFirefoxAccounts": True,
            "DisablePocket": True,
            "BlockAboutConfig": True,
            "BlockAboutProfiles": True,
            "DisableFirefoxStudies": True,
            "DisableProfileImport": True,
            "DisableProfileRefresh": True,
            "PasswordManagerEnabled": False,
            "OfferToSaveLogins": False,
            "Certificates": {"ImportEnterpriseRoots": True},
            "DNSOverHTTPS": {"Enabled": False, "Locked": True},
            "EnableTrackingProtection": {
                "Value": True,
                "Locked": True,
                "Cryptomining": True,
                "Fingerprinting": True,
                "EmailTracking": True,
                "SuspectedFingerprinting": True,
                "Category": "strict",
                "BaselineExceptions": False,
                "ConvenienceExceptions": False,
            },
            "ExtensionSettings": {
                "*": {
                    "installation_mode": "blocked",
                }
            },
            "FirefoxHome": {
                "Search": True,
                "TopSites": False,
                "SponsoredTopSites": False,
                "Highlights": False,
                "Pocket": False,
                "SponsoredPocket": False,
                "Snippets": False,
                "Stories": False,
                "SponsoredStories": False,
                "Locked": True,
            },
            "FirefoxSuggest": {
                "WebSuggestions": False,
                "SponsoredSuggestions": False,
                "ImproveSuggest": False,
                "Locked": True,
            },
            "UserMessaging": {
                "ExtensionRecommendations": False,
                "FeatureRecommendations": False,
                "UrlbarInterventions": False,
                "SkipOnboarding": True,
                "MoreFromMozilla": False,
                "FirefoxLabs": False,
                "Locked": True,
            },
            "PopupBlocking": {
                "Default": True,
                "Locked": True,
            },
            "Homepage": {
                "URL": "https://intranet.example.local/",
                "Additional": [
                    "https://helpdesk.example.local/",
                    "https://kb.example.local/",
                ],
                "Locked": True,
                "StartPage": "homepage-locked",
            },
            "Proxy": {
                "Mode": "system",
                "Locked": True,
            },
        },
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            workspace_signal = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-signal")))
            status_banner = wait.until(ec.presence_of_element_located((by.By.ID, "status")))
            wait.until(
                lambda current_driver: "signal-chip--invalid"
                not in current_driver.find_element(by.By.ID, "workspace-signal").get_attribute("class")
            )

            assert "signal-chip--invalid" not in workspace_signal.get_attribute("class")
            assert "error" not in status_banner.get_attribute("class")
            assert "Document loading error" not in status_banner.text
            assert "Ошибка загрузки документа" not in status_banner.text

            driver.get(f"{base_url}/profiles/{profile_id}/json")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            json_status_banner = wait.until(ec.presence_of_element_located((by.By.ID, "status")))
            wait.until(lambda current_driver: "error" not in json_status_banner.get_attribute("class"))
            wait.until(lambda current_driver: current_driver.execute_script(
                """
                const tokens = Array.from(document.querySelectorAll('#editor .view-lines span[class*="mtk"]'));
                const uniqueColors = [...new Set(tokens.map((el) => getComputedStyle(el).color).filter(Boolean))];
                return uniqueColors.length;
                """
            ) >= 3)

            editor_value = driver.execute_script(
                """
                const monaco = window.monaco;
                if (monaco?.editor?.getModels) {
                    const models = monaco.editor.getModels();
                    if (models.length) {
                        return models[0].getValue();
                    }
                }
                const lines = document.querySelector('#editor .view-lines');
                return lines ? lines.innerText : '';
                """
            )
            assert isinstance(editor_value, str)
            assert "DisableTelemetry" in editor_value
            assert "DisableProfileRefresh" in editor_value
            assert "Homepage" in editor_value
            assert '"policies": {}' not in editor_value
            assert "Profile list updated" not in json_status_banner.text
            assert "Список профилей обновлён" not in json_status_banner.text
            assert "Document loading error" not in json_status_banner.text
            assert "Ошибка загрузки документа" not in json_status_banner.text

            editor_ui = driver.execute_script(
                """
                const monaco = window.monaco;
                const editors = monaco?.editor?.getEditors?.() || [];
                const editor = editors[0] || null;
                if (editor && monaco?.Range) {
                    editor.setPosition({ lineNumber: 9, column: 3 });
                    editor.focus();
                    editor.executeEdits("bpm-json-editor-check", [
                        { range: new monaco.Range(9, 3, 9, 3), text: " " },
                    ]);
                    editor.trigger("bpm-json-editor-check", "undo", null);
                }

                const editorFrame = document.querySelector('#editor');
                const editorRect = editorFrame?.getBoundingClientRect() || { left: 0 };
                const tokenEls = Array.from(document.querySelectorAll('#editor .view-lines span[class*="mtk"]'));
                const uniqueTokenColors = [...new Set(tokenEls.map((el) => getComputedStyle(el).color).filter(Boolean))];
                const visibleLineNumbers = Array.from(
                    document.querySelectorAll('#editor .margin-view-overlays .line-numbers')
                )
                    .map((el) => ({
                        text: el.textContent.trim(),
                        color: getComputedStyle(el).color,
                        opacity: getComputedStyle(el).opacity,
                        paddingLeft: getComputedStyle(el).paddingLeft,
                    }))
                    .filter((entry) => entry.text);
                const scrollbarSlider = document.querySelector(
                    '#editor .monaco-scrollable-element > .scrollbar.vertical > .slider'
                );
                const sliderStyle = scrollbarSlider ? getComputedStyle(scrollbarSlider) : null;

                return {
                    uniqueTokenColors,
                    visibleLineNumbers,
                    scrollbarBackground: sliderStyle ? sliderStyle.backgroundColor : "",
                    scrollbarWidth: scrollbarSlider ? scrollbarSlider.getBoundingClientRect().width : 0,
                };
                """
            )
            assert len(editor_ui["uniqueTokenColors"]) >= 3
            assert any(entry["text"] == "8" for entry in editor_ui["visibleLineNumbers"])
            assert any(entry["text"] == "9" for entry in editor_ui["visibleLineNumbers"])
            assert any(entry["text"] == "10" for entry in editor_ui["visibleLineNumbers"])
            assert any(float(entry["paddingLeft"].replace("px", "") or 0) >= 8 for entry in editor_ui["visibleLineNumbers"])
            assert editor_ui["scrollbarBackground"] not in {"", "rgba(0, 0, 0, 0)", "transparent"}
            assert editor_ui["scrollbarWidth"] >= 8
        finally:
            _close_chromium_driver(driver)


def test_library_counter_browser_regression_covers_plural_forms_and_delete_restore():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            library_counter = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-profile-count")))
            list_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-summary")))
            list_total_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-total-summary")))
            refresh_button = wait.until(ec.element_to_be_clickable((by.By.ID, "refresh")))

            created_ids = []

            def create_profiles(total: int, *, prefix: str) -> None:
                start_index = len(created_ids) + 1
                for index in range(start_index, start_index + total):
                    payload = build_profile_payload(
                        name=f"{prefix} {index:02d}",
                        description=f"Library counter profile {index}",
                        owner=f"counter-{index}@example.org",
                    )
                    response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
                    assert response.status_code == 201, response.text
                    created_ids.append(response.json()["id"])

            def assert_counter_state(total: int, label_en: str, label_ru: str) -> None:
                _safe_click(driver, refresh_button)
                wait.until(lambda current_driver: library_counter.text.strip() == str(total))
                wait.until(lambda current_driver: list_summary.text.strip() == str(total))
                wait.until(lambda current_driver: list_total_summary.text.strip() == str(total))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID,
                        "workspace-profile-label",
                    ).text.strip() == label_en
                )
                _set_locale(driver, wait, ui, locale="ru", expected_text="МЕНЕДЖЕР ПРОФИЛЕЙ БРАУЗЕРА")
                wait.until(lambda current_driver: library_counter.text.strip() == str(total))
                wait.until(lambda current_driver: list_summary.text.strip() == str(total))
                wait.until(lambda current_driver: list_total_summary.text.strip() == str(total))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID,
                        "workspace-profile-label",
                    ).text.strip() == label_ru
                )
                _set_locale(driver, wait, ui, locale="en", expected_text="BROWSER PROFILE MANAGER")
                wait.until(lambda current_driver: library_counter.text.strip() == str(total))

            create_profiles(1, prefix="Counter One")
            assert_counter_state(1, "Profile in library", "Профиль в библиотеке")

            create_profiles(4, prefix="Counter Five")
            assert_counter_state(5, "Profiles in library", "Профилей в библиотеке")

            create_profiles(16, prefix="Counter Twenty One")
            assert_counter_state(21, "Profiles in library", "Профиль в библиотеке")

            deleted_id = created_ids[-1]
            deleted_response = requests.delete(f"{base_url}/api/profiles/{deleted_id}", timeout=10)
            assert deleted_response.status_code == 204, deleted_response.text
            assert_counter_state(20, "Profiles in library", "Профилей в библиотеке")

            restored_response = requests.post(f"{base_url}/api/profiles/{deleted_id}/restore", timeout=10)
            assert restored_response.status_code == 200, restored_response.text
            assert_counter_state(21, "Profiles in library", "Профиль в библиотеке")
        finally:
            _close_chromium_driver(driver)


def test_library_counter_browser_regression_covers_include_deleted_mode():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload_active = build_profile_payload(
        name="Include Deleted Active Profile",
        description="Active profile for include-deleted coverage",
        owner="active@example.org",
    )
    payload_deleted = build_profile_payload(
        name="Include Deleted Removed Profile",
        description="Deleted profile for include-deleted coverage",
        owner="deleted@example.org",
    )

    with run_test_app_server() as base_url:
        create_active = requests.post(f"{base_url}/api/profiles", json=payload_active, timeout=10)
        create_deleted = requests.post(f"{base_url}/api/profiles", json=payload_deleted, timeout=10)
        assert create_active.status_code == 201, create_active.text
        assert create_deleted.status_code == 201, create_deleted.text
        active_id = create_active.json()["id"]
        deleted_id = create_deleted.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            library_counter = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-profile-count")))
            list_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-summary")))
            list_total_summary = wait.until(ec.presence_of_element_located((by.By.ID, "list-total-summary")))
            refresh_button = wait.until(ec.element_to_be_clickable((by.By.ID, "refresh")))
            search_input = wait.until(ec.presence_of_element_located((by.By.ID, "search")))

            wait.until(lambda current_driver: library_counter.text.strip() == "2")
            wait.until(lambda current_driver: list_summary.text.strip() == "2")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")

            deleted_response = requests.delete(f"{base_url}/api/profiles/{deleted_id}", timeout=10)
            assert deleted_response.status_code == 204, deleted_response.text

            _safe_click(driver, refresh_button)
            wait.until(lambda current_driver: library_counter.text.strip() == "1")
            wait.until(lambda current_driver: list_summary.text.strip() == "1")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "1")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{active_id}/edit"]')
                )
            )
            wait.until(
                lambda current_driver: not current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    f'a.library-row-open-button[href="/profiles/{deleted_id}/edit"]',
                )
            )

            driver.execute_script(
                """
                const checkbox = document.getElementById('include-deleted');
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                """,
            )
            wait.until(lambda current_driver: library_counter.text.strip() == "2")
            wait.until(lambda current_driver: list_summary.text.strip() == "2")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                lambda current_driver: "Include Deleted Removed Profile"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            wait.until(
                lambda current_driver: "Deleted" in current_driver.find_element(by.By.TAG_NAME, "body").text
            )

            search_input.clear()
            search_input.send_keys("Removed")
            wait.until(lambda current_driver: list_summary.text.strip() == "1")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "2")
            wait.until(
                ec.presence_of_element_located(
                    (by.By.CSS_SELECTOR, f'a.library-row-open-button[href="/profiles/{deleted_id}/edit"]')
                )
            )

            driver.execute_script(
                """
                const checkbox = document.getElementById('include-deleted');
                checkbox.checked = false;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                """,
            )
            wait.until(lambda current_driver: list_summary.text.strip() == "0")
            wait.until(lambda current_driver: list_total_summary.text.strip() == "1")
            wait.until(
                lambda current_driver: "No profiles to show"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
        finally:
            _close_chromium_driver(driver)


def test_shared_editor_chrome_browser_regression_across_modes():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    payload = build_profile_payload(
        name="Shared Editor Chrome Browser Profile",
        description="Shared editor chrome browser regression",
        owner="chrome@example.org",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            mode_expectations = (
                ("guided", f"{base_url}/profiles/{profile_id}/edit", (by.By.ID, "wizard-panel")),
                ("settings", f"{base_url}/profiles/{profile_id}/settings", (by.By.ID, "settings-panel")),
                ("json", f"{base_url}/profiles/{profile_id}/json", (by.By.ID, "editor-panel")),
            )

            for mode_name, mode_url, unique_locator in mode_expectations:
                driver.get(mode_url)
                wait.until(ec.presence_of_element_located(unique_locator))
                current_name = wait.until(ec.presence_of_element_located((by.By.ID, "current-name")))
                workspace_signal = wait.until(ec.presence_of_element_located((by.By.ID, "workspace-signal")))
                validation_preview = wait.until(ec.presence_of_element_located((by.By.ID, "validation-preview")))
                save_button = wait.until(ec.presence_of_element_located((by.By.ID, "save")))
                validate_button = wait.until(ec.presence_of_element_located((by.By.ID, "validate")))
                profile_name_input = wait.until(ec.presence_of_element_located((by.By.ID, "profile-name")))
                editor_profile_id = wait.until(ec.presence_of_element_located((by.By.ID, "editor-profile-id")))
                overview_schema = wait.until(ec.presence_of_element_located((by.By.ID, "overview-schema")))
                overview_context = wait.until(ec.presence_of_element_located((by.By.ID, "overview-context")))
                guided_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-guided")))
                settings_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-settings")))
                json_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-json")))

                wait.until(lambda current_driver, signal=workspace_signal: signal.text.strip() != "")
                wait.until(
                    lambda current_driver, preview=validation_preview: (
                        preview.get_attribute("aria-live") == "polite"
                    )
                )
                wait.until(
                    lambda current_driver, name=current_name: name.text.strip() == payload["name"]
                )
                wait.until(
                    lambda current_driver, name_input=profile_name_input: (
                        name_input.get_attribute("value").strip() == payload["name"]
                    )
                )

                assert current_name.text.strip() == payload["name"]
                assert profile_name_input.is_displayed()
                assert profile_name_input.get_attribute("value").strip() == payload["name"]
                assert editor_profile_id.text.strip() == f"#{profile_id}"
                assert overview_schema.text.strip() != ""
                assert overview_context.text.strip() != ""
                assert save_button.text.strip() == "Save"
                assert "Validate" in validate_button.text.strip()
                assert "Save new profile" not in driver.find_element(by.By.TAG_NAME, "body").text
                assert "Choose a profile" not in current_name.text
                assert guided_link.get_attribute("href").endswith(f"/profiles/{profile_id}/edit")
                assert f"/profiles/{profile_id}/settings" in settings_link.get_attribute("href")
                assert f"/profiles/{profile_id}/json" in json_link.get_attribute("href")
                assert workspace_signal.get_attribute("data-i18n") == "profiles.signal_saved"
                assert mode_name in ("guided", "settings", "json")
        finally:
            _close_chromium_driver(driver)


def test_archived_profile_chrome_browser_regression_keeps_deleted_and_restored_state():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    payload = build_profile_payload(
        name="Archived Chrome Browser Profile",
        description="Archived editor chrome browser regression",
        owner="archived@example.org",
        schema_version="release-150",
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]
        delete_response = requests.delete(f"{base_url}/api/profiles/{profile_id}", timeout=10)
        assert delete_response.status_code == 204, delete_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            def open_with_retry(url: str) -> None:
                for attempt in range(3):
                    try:
                        driver.get(url)
                        return
                    except (
                        selenium_exceptions.TimeoutException,
                        selenium_exceptions.WebDriverException,
                    ) as exc:
                        if (
                            not isinstance(exc, selenium_exceptions.TimeoutException)
                            and "Timed out receiving message from renderer" not in str(exc)
                        ):
                            raise
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        if driver.current_url == url:
                            return
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        if driver.current_url == url:
                            return
                        if attempt == 2:
                            raise

            open_with_retry(f"{base_url}/profiles/{profile_id}/edit?include_deleted=true")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))

            current_name = wait.until(ec.presence_of_element_located((by.By.ID, "current-name")))
            state_badge = wait.until(ec.presence_of_element_located((by.By.ID, "profile-state-badge")))
            overview_context = wait.until(ec.presence_of_element_located((by.By.ID, "overview-context")))
            editor_profile_id = wait.until(ec.presence_of_element_located((by.By.ID, "editor-profile-id")))
            save_button = wait.until(ec.presence_of_element_located((by.By.ID, "save")))
            settings_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-settings")))
            json_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-json")))

            wait.until(lambda current_driver: current_name.text.strip() == payload["name"])
            wait.until(lambda current_driver: state_badge.text.strip().lower() == "deleted")

            assert current_name.text.strip() == payload["name"]
            assert state_badge.text.strip().lower() == "deleted"
            assert overview_context.text.strip() == "Archived profile"
            assert editor_profile_id.text.strip() == f"#{profile_id}"
            assert save_button.text.strip() == "Save"
            assert "include_deleted=true" in settings_link.get_attribute("href")
            assert "include_deleted=true" in json_link.get_attribute("href")
            assert current_name.text.strip() != "Choose a profile"
            assert save_button.text.strip() != "Save new profile"

            guided_handle = driver.current_window_handle
            guided_handles = set(driver.window_handles)
            _safe_click(driver, settings_link)
            settings_handle = _switch_to_new_window(driver, wait, guided_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted")
            settings_json_link = wait.until(ec.presence_of_element_located((by.By.ID, "editor-mode-json")))

            assert "include_deleted=true" in driver.current_url
            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]
            assert f"return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue" in settings_json_link.get_attribute("href")
            assert "include_deleted=true" in settings_json_link.get_attribute("href")

            settings_handles = set(driver.window_handles)
            _safe_click(driver, settings_json_link)
            _switch_to_new_window(driver, wait, settings_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted")
            json_return_link = wait.until(ec.presence_of_element_located((by.By.ID, "advanced-return-link")))

            assert "include_deleted=true" in driver.current_url
            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]
            assert json_return_link.get_attribute("href").endswith(
                f"/profiles/{profile_id}/settings?include_deleted=true"
            )

            open_with_retry(json_return_link.get_attribute("href"))
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted")
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"])
            assert driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted"
            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]

            driver.switch_to.window(settings_handle)
            open_with_retry(f"{base_url}/profiles/{profile_id}/edit?include_deleted=true")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted")
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"])
            assert driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted"
            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]

            driver.switch_to.window(guided_handle)
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted")
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"])
            assert driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "deleted"
            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]

            restore_response = requests.post(f"{base_url}/api/profiles/{profile_id}/restore", timeout=10)
            assert restore_response.status_code == 200, restore_response.text

            open_with_retry(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(lambda current_driver: current_driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "active")

            assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]
            assert driver.find_element(by.By.ID, "profile-state-badge").text.strip().lower() == "active"
            assert driver.find_element(by.By.ID, "overview-context").text.strip() == "Saved profile"
            assert driver.find_element(by.By.ID, "current-name").text.strip() != "Choose a profile"
            assert driver.find_element(by.By.ID, "save").text.strip() != "Save new profile"
        finally:
            _close_chromium_driver(driver)


def test_archived_profile_semantic_focus_browser_regression_preserves_route_aware_context():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    payload = build_profile_payload(
        name="Archived Semantic Focus Browser Profile",
        description="Archived semantic focus browser regression",
        owner="archived-focus@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]
        delete_response = requests.delete(f"{base_url}/api/profiles/{profile_id}", timeout=10)
        assert delete_response.status_code == 204, delete_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            def open_with_retry(url: str) -> None:
                for attempt in range(3):
                    try:
                        driver.get(url)
                        return
                    except (
                        selenium_exceptions.TimeoutException,
                        selenium_exceptions.WebDriverException,
                    ) as exc:
                        if (
                            not isinstance(exc, selenium_exceptions.TimeoutException)
                            and "Timed out receiving message from renderer" not in str(exc)
                        ):
                            raise
                        if attempt == 2:
                            raise

            settings_url = (
                f"{base_url}/profiles/{profile_id}/settings"
                f"?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue"
                f"&focus=policy:DisableTelemetry"
            )
            open_with_retry(settings_url)
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "profile-state-badge"
                ).text.strip().lower()
                == "deleted"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "current-name"
                ).text.strip()
                == payload["name"]
            )

            settings_json_link = wait.until(
                ec.presence_of_element_located((by.By.ID, "editor-mode-json"))
            )
            assert "include_deleted=true" in driver.current_url
            assert "focus=policy:DisableTelemetry" in driver.current_url
            assert f"return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue" in (
                settings_json_link.get_attribute("href") or ""
            )

            semantic_json_cases = (
                ("raw", ""),
                ("deprecated:LegacyPolicy", "deprecated:LegacyPolicy"),
                ("unknown:FuturePolicy", "unknown:FuturePolicy"),
            )

            for focus_value, expected_focus in semantic_json_cases:
                open_with_retry(
                    f"{base_url}/profiles/{profile_id}/json"
                    f"?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue"
                    f"&focus={focus_value}"
                )
                wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "deleted"
                )
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "current-name"
                    ).text.strip()
                    == payload["name"]
                )

                json_return_link = wait.until(
                    ec.presence_of_element_located((by.By.ID, "advanced-return-link"))
                )
                settings_link = wait.until(
                    ec.presence_of_element_located((by.By.ID, "editor-mode-settings"))
                )

                assert "include_deleted=true" in driver.current_url
                if expected_focus:
                    assert expected_focus in driver.current_url
                else:
                    assert "focus=raw" in driver.current_url
                assert json_return_link.get_attribute("href").endswith(
                    f"/profiles/{profile_id}/settings?include_deleted=true"
                )
                settings_href = settings_link.get_attribute("href") or ""
                assert "include_deleted=true" in settings_href
                assert "focus=settings-schema-shell-step-8" in settings_href
                assert f"return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue" in settings_href

                open_with_retry(json_return_link.get_attribute("href"))
                wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "deleted"
                )
                assert driver.find_element(by.By.ID, "current-name").text.strip() == payload["name"]
        finally:
            _close_chromium_driver(driver)


def test_archived_profile_semantic_focus_browser_regression_reveals_expected_surfaces():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    payload = build_profile_payload(
        name="Archived Semantic Surface Browser Profile",
        description="Archived semantic surface browser regression",
        owner="archived-surface@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]
        delete_response = requests.delete(f"{base_url}/api/profiles/{profile_id}", timeout=10)
        assert delete_response.status_code == 204, delete_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            def open_with_retry(url: str) -> None:
                for attempt in range(3):
                    try:
                        driver.get(url)
                        return
                    except (
                        selenium_exceptions.TimeoutException,
                        selenium_exceptions.WebDriverException,
                    ) as exc:
                        if (
                            not isinstance(exc, selenium_exceptions.TimeoutException)
                            and "Timed out receiving message from renderer" not in str(exc)
                        ):
                            raise
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        if driver.current_url == url:
                            return
                        if attempt == 2:
                            raise

            open_with_retry(
                f"{base_url}/profiles/{profile_id}/settings"
                f"?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue"
                f"&focus=policy:DisableTelemetry"
            )
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "profile-state-badge"
                ).text.strip().lower()
                == "deleted"
            )
            _wait_for_selector_visibility(
                wait,
                driver,
                "#settings-schema-shell-step-5-details",
                True,
                message="step 5 settings shell should open for archived policy focus",
            )
            _wait_for_selector_visibility(
                wait,
                driver,
                '[data-settings-target="shell-policy:5:DisableTelemetry"]',
                True,
                message="DisableTelemetry settings target should be visible for archived policy focus",
            )

            for focus_value in ("raw", "deprecated:LegacyPolicy", "unknown:FuturePolicy"):
                open_with_retry(
                    f"{base_url}/profiles/{profile_id}/json"
                    f"?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue"
                    f"&focus={focus_value}"
                )
                wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "deleted"
                )
                settings_link = wait.until(
                    ec.presence_of_element_located((by.By.ID, "editor-mode-settings"))
                )
                assert "focus=settings-schema-shell-step-8" in (settings_link.get_attribute("href") or "")

                open_with_retry(settings_link.get_attribute("href"))
                wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "deleted"
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#settings-schema-shell-step-8",
                    True,
                    message=f"settings step 8 should be visible after archived {focus_value} return",
                )
        finally:
            _close_chromium_driver(driver)


def test_active_profile_semantic_focus_browser_regression_reveals_expected_surfaces():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    payload = build_profile_payload(
        name="Active Semantic Surface Browser Profile",
        description="Active semantic surface browser regression",
        owner="active-surface@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )

    with run_test_app_server() as base_url:
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            def open_with_retry(url: str) -> None:
                for attempt in range(3):
                    try:
                        driver.get(url)
                        return
                    except (
                        selenium_exceptions.TimeoutException,
                        selenium_exceptions.WebDriverException,
                    ) as exc:
                        if (
                            not isinstance(exc, selenium_exceptions.TimeoutException)
                            and "Timed out receiving message from renderer" not in str(exc)
                        ):
                            raise
                        try:
                            driver.execute_script("window.stop();")
                        except Exception:
                            pass
                        if driver.current_url == url:
                            return
                        if attempt == 2:
                            raise

            open_with_retry(
                f"{base_url}/profiles/{profile_id}/settings"
                f"?return=/profiles/{profile_id}/edit"
                f"&focus=policy:DisableTelemetry"
            )
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "profile-state-badge"
                ).text.strip().lower()
                == "active"
            )
            _wait_for_selector_visibility(
                wait,
                driver,
                "#settings-schema-shell-step-5-details",
                True,
                message="step 5 settings shell should open for active policy focus",
            )
            _wait_for_selector_visibility(
                wait,
                driver,
                '[data-settings-target="shell-policy:5:DisableTelemetry"]',
                True,
                message="DisableTelemetry settings target should be visible for active policy focus",
            )

            for focus_value in ("raw", "deprecated:LegacyPolicy", "unknown:FuturePolicy"):
                open_with_retry(
                    f"{base_url}/profiles/{profile_id}/json"
                    f"?return=/profiles/{profile_id}/settings"
                    f"&focus={focus_value}"
                )
                wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "active"
                )
                settings_link = wait.until(
                    ec.presence_of_element_located((by.By.ID, "editor-mode-settings"))
                )
                assert "focus=settings-schema-shell-step-8" in (settings_link.get_attribute("href") or "")

                open_with_retry(settings_link.get_attribute("href"))
                wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == "active"
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#settings-schema-shell-step-8",
                    True,
                    message=f"settings step 8 should be visible after active {focus_value} return",
                )
        finally:
            _close_chromium_driver(driver)


def test_export_review_jumps_browser_regression_open_expected_surfaces_for_active_and_archived_profiles():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    def open_with_retry(driver, url: str) -> None:
        for attempt in range(3):
            try:
                driver.get(url)
                return
            except (
                selenium_exceptions.TimeoutException,
                selenium_exceptions.WebDriverException,
            ) as exc:
                if (
                    not isinstance(exc, selenium_exceptions.TimeoutException)
                    and "Timed out receiving message from renderer" not in str(exc)
                ):
                    raise
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
                if driver.current_url == url:
                    return
                if attempt == 2:
                    raise

    def open_wizard_step_with_retry(driver, wait, step_number: int) -> None:
        for attempt in range(3):
            try:
                _open_wizard_step(driver, wait, by, step_number)
                return
            except selenium_exceptions.TimeoutException:
                if attempt == 2:
                    raise
                _click_selector(driver, wait, f'.wizard-step[data-step="{step_number}"]')

    payload = build_profile_payload(
        name="Review Jump Browser Profile",
        description="Review jump browser regression",
        owner="review-jumps@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "DisableProfileRefresh": True,
            "GenerativeAI": {"Enabled": False},
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )

    with run_test_app_server() as base_url:
        active_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert active_response.status_code == 201, active_response.text
        active_profile_id = active_response.json()["id"]

        archived_response = requests.post(
            f"{base_url}/api/profiles",
            json={**payload, "name": "Review Jump Archived Browser Profile"},
            timeout=10,
        )
        assert archived_response.status_code == 201, archived_response.text
        archived_profile_id = archived_response.json()["id"]
        delete_response = requests.delete(f"{base_url}/api/profiles/{archived_profile_id}", timeout=10)
        assert delete_response.status_code == 204, delete_response.text

        for profile_id, include_deleted, expected_state in (
            (active_profile_id, False, "active"),
            (archived_profile_id, True, "deleted"),
        ):
            driver = _build_chromium_driver()
            wait = ui.WebDriverWait(driver, 20)

            try:
                edit_url = f"{base_url}/profiles/{profile_id}/edit"
                if include_deleted:
                    edit_url = f"{edit_url}?include_deleted=true"
                open_with_retry(driver, edit_url)

                wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
                wait.until(
                    lambda current_driver, state=expected_state: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == state
                )

                open_wizard_step_with_retry(driver, wait, 6)
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "wizard-export-next-steps"
                    ).text.strip()
                    != ""
                )
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "wizard-export-deprecated-count"
                    ).text.strip()
                    == "0"
                )
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "wizard-export-unknown-count"
                    ).text.strip()
                    == "0"
                )
                _wait_for_selector_disabled(
                    wait,
                    driver,
                    "#wizard-export-deprecated-jump",
                    True,
                    message="Deprecated export jump should be disabled when there are no deprecated policies",
                )
                _wait_for_selector_disabled(
                    wait,
                    driver,
                    "#wizard-export-unknown-jump",
                    True,
                    message="Unknown export jump should be disabled when there are no unknown keys",
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#wizard-export-deprecated-summary-jump",
                    False,
                    message="Deprecated summary alert should stay hidden when there are no deprecated policies",
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#wizard-export-unknown-summary-jump",
                    False,
                    message="Unknown summary alert should stay hidden when there are no unknown keys",
                )
                wait.until(ec.element_to_be_clickable((by.By.ID, "wizard-export-summary-ai-jump")))
                _click_selector(driver, wait, "#wizard-export-summary-ai-jump")
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.CSS_SELECTOR, '.wizard-step[data-step="5"]'
                    ).get_attribute("aria-current")
                    == "step"
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#wizard-ai-policy-controls",
                    True,
                    message="AI review jump should reveal the guided AI controls",
                )

                open_wizard_step_with_retry(driver, wait, 6)
                wait.until(ec.element_to_be_clickable((by.By.ID, "wizard-export-raw-jump")))
                previous_handles = set(driver.window_handles)
                _click_selector(driver, wait, "#wizard-export-raw-jump")
                _switch_to_new_window(driver, wait, previous_handles)
                jumped_url = driver.current_url
                assert f"/profiles/{profile_id}/settings" in jumped_url
                driver.close()
                driver.switch_to.window(next(iter(previous_handles)))
                jump_driver = _build_chromium_driver()
                jump_wait = ui.WebDriverWait(jump_driver, 20)
                try:
                    try:
                        jump_driver.get(jumped_url)
                    except selenium_exceptions.TimeoutException:
                        pass
                    jump_wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
                    jump_wait.until(
                        lambda current_driver, state=expected_state: current_driver.find_element(
                            by.By.ID, "profile-state-badge"
                        ).text.strip().lower()
                        == state
                    )
                    _wait_for_selector_visibility(
                        jump_wait,
                        jump_driver,
                        "#settings-schema-shell-step-8-details",
                        True,
                        message="Raw export jump should open the advanced step 8 shell",
                    )
                    _wait_for_selector_visibility(
                        jump_wait,
                        jump_driver,
                        '[data-settings-target="shell-policy:8:DisableProfileRefresh"]',
                        True,
                        message="Raw export jump should reveal the focused raw-fallback policy",
                    )
                finally:
                    _close_chromium_driver(jump_driver)
                assert f"/profiles/{profile_id}/settings" in jumped_url
                if include_deleted:
                    assert "include_deleted=true" in jumped_url
            finally:
                _close_chromium_driver(driver)


def test_export_review_unknown_jump_browser_regression_opens_json_for_active_and_archived_profiles():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    selenium_exceptions = pytest.importorskip("selenium.common.exceptions")

    from app.models.profile import Profile

    def open_with_retry(driver, url: str) -> None:
        for attempt in range(3):
            try:
                driver.get(url)
                return
            except (
                selenium_exceptions.TimeoutException,
                selenium_exceptions.WebDriverException,
            ) as exc:
                if (
                    not isinstance(exc, selenium_exceptions.TimeoutException)
                    and "Timed out receiving message from renderer" not in str(exc)
                ):
                    raise
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
                if driver.current_url == url:
                    return
                if attempt == 2:
                    raise

    def open_wizard_step_with_retry(driver, wait, step_number: int) -> None:
        for attempt in range(3):
            try:
                _open_wizard_step(driver, wait, by, step_number)
                return
            except selenium_exceptions.TimeoutException:
                if attempt == 2:
                    raise
                _click_selector(driver, wait, f'.wizard-step[data-step="{step_number}"]')

    payload = build_profile_payload(
        name="Unknown Jump Browser Profile",
        description="Unknown jump browser regression",
        owner="unknown-jumps@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "GenerativeAI": {"Enabled": False},
        },
    )

    with run_test_app_server_handle() as server:
        base_url = server.base_url
        active_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert active_response.status_code == 201, active_response.text
        active_profile_id = active_response.json()["id"]

        archived_response = requests.post(
            f"{base_url}/api/profiles",
            json={**payload, "name": "Unknown Jump Archived Browser Profile"},
            timeout=10,
        )
        assert archived_response.status_code == 201, archived_response.text
        archived_profile_id = archived_response.json()["id"]
        delete_response = requests.delete(f"{base_url}/api/profiles/{archived_profile_id}", timeout=10)
        assert delete_response.status_code == 204, delete_response.text

        with server.session_factory() as session:
            for profile_id in (active_profile_id, archived_profile_id):
                profile = session.get(Profile, profile_id)
                assert profile is not None
                profile.flags = {
                    **(profile.flags or {}),
                    "FuturePolicy": True,
                }
            session.commit()

        for profile_id, include_deleted, expected_state in (
            (active_profile_id, False, "active"),
            (archived_profile_id, True, "deleted"),
        ):
            driver = _build_chromium_driver()
            wait = ui.WebDriverWait(driver, 20)

            try:
                edit_url = f"{base_url}/profiles/{profile_id}/edit"
                if include_deleted:
                    edit_url = f"{edit_url}?include_deleted=true"
                open_with_retry(driver, edit_url)

                wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
                wait.until(
                    lambda current_driver, state=expected_state: current_driver.find_element(
                        by.By.ID, "profile-state-badge"
                    ).text.strip().lower()
                    == state
                )

                open_wizard_step_with_retry(driver, wait, 6)
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "wizard-export-next-steps"
                    ).text.strip()
                    != ""
                )
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.ID, "wizard-export-unknown-count"
                    ).text.strip()
                    == "1"
                )
                _wait_for_selector_disabled(
                    wait,
                    driver,
                    "#wizard-export-unknown-jump",
                    False,
                    message="Unknown export jump should be enabled when an unknown policy is present",
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    "#wizard-export-unknown-summary-jump",
                    True,
                    message="Unknown summary alert should be visible when an unknown policy is present",
                )
                _wait_for_selector_visibility(
                    wait,
                    driver,
                    '[data-final-review-jump="unknown"][data-final-review-key="FuturePolicy"]',
                    True,
                    message="Unknown drilldown jump should be visible when an unknown policy is present",
                )
                previous_handles = set(driver.window_handles)
                _click_selector(driver, wait, '[data-final-review-jump="unknown"][data-final-review-key="FuturePolicy"]')
                _switch_to_new_window(driver, wait, previous_handles)
                jumped_url = driver.current_url
                parsed = urlparse(jumped_url)
                query = parse_qs(parsed.query)
                assert parsed.path == f"/profiles/{profile_id}/json"
                assert query.get("focus") == ["unknown:FuturePolicy"]
                if include_deleted:
                    assert query.get("include_deleted") == ["true"]
                driver.close()
                driver.switch_to.window(next(iter(previous_handles)))

                jump_driver = _build_chromium_driver()
                jump_wait = ui.WebDriverWait(jump_driver, 20)
                try:
                    open_with_retry(jump_driver, jumped_url)
                    jump_wait.until(ec.presence_of_element_located((by.By.ID, "editor")))
                    jump_wait.until(
                        lambda current_driver, state=expected_state: current_driver.find_element(
                            by.By.ID, "profile-state-badge"
                        ).text.strip().lower()
                        == state
                    )
                    jump_wait.until(
                        lambda current_driver: current_driver.execute_script(
                            "return document.body.dataset.profilesRouteMode;"
                        ) == "json"
                    )
                    jump_wait.until(
                        lambda current_driver: current_driver.execute_script(
                            "return document.body.dataset.advancedFocusTarget || '';"
                        ) == "unknown:FuturePolicy"
                    )
                finally:
                    _close_chromium_driver(jump_driver)
            finally:
                _close_chromium_driver(driver)


def test_guided_profile_workflow_browser_regression_covers_step_scope_buttons_and_ru_settings():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    from app.models.profile import Profile

    payload = build_profile_payload(
        name="Guided Workflow Browser Profile",
        description="Chromium guided workflow regression",
        owner="workflow@example.org",
        schema_version="release-150",
        flags={
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    )

    step_expectations = {
        1: {
            "visible": (
                "#wizard-name",
                "#wizard-schema",
                "#wizard-starter-grid",
                '[data-scenario-key="corporate_default"]',
                '[data-cis-layer-key="cis_l1"]',
            ),
            "hidden": (
                "#wizard-general-policy-presets",
                "#wizard-homepage-url",
                "#wizard-search-default-engine",
                "#wizard-hardening-presets",
                "#wizard-sync-focus-presets",
                "#wizard-ai-posture-presets",
                "#wizard-export-ready-card",
            ),
        },
        2: {
            "visible": (
                "#wizard-general-policy-presets",
                "#wizard-proxy-presets",
                "#wizard-network-enterprise-presets",
                "#wizard-home-surface-startup",
                "#wizard-search-defaults-presets",
            ),
            "hidden": (
                "#wizard-starter-grid",
                "#wizard-hardening-presets",
                "#wizard-sync-focus-presets",
                "#wizard-ai-posture-presets",
                "#wizard-export-ready-card",
            ),
        },
        3: {
            "visible": (
                "#wizard-hardening-presets",
                "#wizard-cleanup-presets",
                "#wizard-site-data-presets",
            ),
            "hidden": (
                "#wizard-proxy-presets",
                "#wizard-sync-focus-presets",
                "#wizard-ai-posture-presets",
                "#wizard-export-ready-card",
            ),
        },
        4: {
            "visible": (
                "#wizard-sync-focus-presets",
                "#wizard-language-presets",
                "#wizard-extension-governance-presets",
                "#wizard-bookmarks-open-advanced",
                "#wizard-website-access-posture",
            ),
            "hidden": (
                "#wizard-homepage-url",
                "#wizard-hardening-presets",
                "#wizard-ai-posture-presets",
                "#wizard-export-ready-card",
            ),
        },
        5: {
            "visible": (
                "#wizard-ai-posture-presets",
                "#wizard-ai-policy-controls",
                "#wizard-visual-search-enabled-card",
            ),
            "hidden": (
                "#wizard-sync-focus-presets",
                "#wizard-bookmarks-open-advanced",
                "#wizard-website-access-posture",
                "#wizard-export-ready-card",
                "#wizard-homepage-url",
                "#wizard-hardening-presets",
            ),
        },
        6: {
            "visible": (
                "#wizard-export-ready-card",
                "#wizard-export-save-action",
                "#wizard-export-validate-action",
                "#wizard-export-next-steps",
            ),
            "hidden": (
                "#wizard-hardening-presets",
                "#wizard-ai-posture-presets",
                "#wizard-sync-focus-presets",
                "#wizard-homepage-url",
            ),
        },
    }

    with run_test_app_server_handle() as server:
        base_url = server.base_url
        create_response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert create_response.status_code == 201, create_response.text
        profile_id = create_response.json()["id"]
        with server.session_factory() as session:
            profile = session.get(Profile, profile_id)
            assert profile is not None
            profile.flags = {
                **(profile.flags or {}),
                "FuturePolicy": {"Enabled": True},
            }
            session.commit()

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)

        try:
            driver.get(f"{base_url}/profiles")
            library_search = wait.until(ec.presence_of_element_located((by.By.ID, "search")))
            library_search.clear()
            library_search.send_keys(payload["name"])
            library_handles = set(driver.window_handles)
            open_button_selector = f'a.library-row-open-button[href="/profiles/{profile_id}/edit"]'
            wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, open_button_selector)))
            _click_selector(driver, wait, open_button_selector)
            _switch_to_new_window(driver, wait, library_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(
                lambda current_driver: urlparse(current_driver.current_url).path
                == f"/profiles/{profile_id}/edit"
            )
            wait.until(
                ec.presence_of_element_located((by.By.CSS_SELECTOR, "[data-wizard-review-filters]"))
            )
            wait.until(
                lambda current_driver: current_driver.execute_script(
                    "return document.body.dataset.wizardNavigationReady === 'true';"
                )
            )

            for step_number, expectations in step_expectations.items():
                _assert_step_scope(
                    driver,
                    wait,
                    step_number=step_number,
                    visible_selectors=expectations["visible"],
                    hidden_selectors=expectations["hidden"],
                )

            _open_wizard_step(driver, wait, by, 1)
            wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-scenario-key="shared_devices"]')))
            _click_selector(driver, wait, '[data-scenario-key="shared_devices"]')
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, '[data-scenario-key="shared_devices"]'
                ).get_attribute("aria-pressed")
                == "true"
            )

            _open_wizard_step(driver, wait, by, 2)
            wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-proxy-preset="manual"]')))
            _click_selector(driver, wait, '[data-proxy-preset="manual"]')
            _wait_for_selector_visibility(wait, driver, "#wizard-proxy-http", True)
            _toggle_panel(
                driver,
                wait,
                toggle_selector="#wizard-network-enterprise-fine-tuning-toggle",
                panel_selector="#wizard-network-enterprise-fine-tuning-panel",
            )
            wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-home-surface-toggle="firefox_home"]')))
            _click_selector(driver, wait, '[data-home-surface-toggle="firefox_home"]')
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, '[data-home-surface-toggle="firefox_home"]'
                ).get_attribute("aria-expanded")
                == "true"
            )
            _wait_for_selector_visibility(wait, driver, "#wizard-firefox-home-presets", True)
            _toggle_panel(
                driver,
                wait,
                toggle_selector="#wizard-search-defaults-fine-tuning-toggle",
                panel_selector="#wizard-search-defaults-fine-tuning-panel",
            )

            _open_wizard_step(driver, wait, by, 3)
            _toggle_panel(
                driver,
                wait,
                toggle_selector="#wizard-site-data-fine-tuning-toggle",
                panel_selector="#wizard-site-data-fine-tuning-panel",
            )

            _open_wizard_step(driver, wait, by, 4)
            _toggle_panel(
                driver,
                wait,
                toggle_selector="#wizard-extension-fine-tuning-toggle",
                panel_selector="#wizard-extension-fine-tuning-panel",
            )
            _toggle_panel(
                driver,
                wait,
                toggle_selector="#wizard-extension-curated-toggle",
                panel_selector="#wizard-extension-curated-panel",
            )
            wait.until(
                ec.element_to_be_clickable(
                    (by.By.CSS_SELECTOR, '[data-extension-profile-toggle="uBlock0@raymondhill.net"]')
                )
            )
            _click_selector(driver, wait, '[data-extension-profile-toggle="uBlock0@raymondhill.net"]')
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, '[data-extension-profile-toggle="uBlock0@raymondhill.net"]'
                ).get_attribute("aria-expanded")
                == "true"
            )
            _wait_for_selector_visibility(wait, driver, "#wizard-extension-profile-details-ublock", True)

            _open_wizard_step(driver, wait, by, 5)
            wait.until(ec.element_to_be_clickable((by.By.CSS_SELECTOR, '[data-ai-posture-preset="disable"]')))
            _click_selector(driver, wait, '[data-ai-posture-preset="disable"]')
            wait.until(
                lambda current_driver: _selector_is_visible(current_driver, "#wizard-ai-policy-controls")
            )
            wait.until(
                lambda current_driver: _selector_is_visible(
                    current_driver,
                    "#wizard-visual-search-enabled-card",
                )
            )
            assert not driver.find_elements(by.By.ID, "wizard-ai-providers-open-advanced")

            _open_wizard_step(driver, wait, by, 6)
            wait.until(ec.element_to_be_clickable((by.By.ID, "wizard-export-validate-action")))
            _click_selector(driver, wait, "#wizard-export-validate-action")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "wizard-export-next-steps"
                ).text.strip()
                != ""
            )
            firefox_policies_link = wait.until(ec.presence_of_element_located((by.By.ID, "wizard-export-firefox-policies")))
            assert firefox_policies_link.get_attribute("href")
            wait.until(ec.element_to_be_clickable((by.By.ID, "wizard-export-summary-network-jump")))
            _click_selector(driver, wait, "#wizard-export-summary-network-jump")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, '.wizard-step[data-step="2"]'
                ).get_attribute("aria-current")
                == "step"
            )
            _wait_for_selector_visibility(wait, driver, "#wizard-general-policy-presets", True)
            _open_wizard_step(driver, wait, by, 6)

            _set_locale(driver, wait, ui, locale="ru", expected_text="Пошаговый редактор")
            wait.until(
                lambda current_driver: "Пользователи, дополнения и сайты"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            assert "Firefox Account" not in driver.find_element(by.By.TAG_NAME, "body").text

            edit_handle = driver.current_window_handle
            edit_handles = set(driver.window_handles)
            wait.until(ec.element_to_be_clickable((by.By.ID, "editor-mode-settings")))
            _click_selector(driver, wait, "#editor-mode-settings")

            assert driver.current_window_handle == edit_handle
            settings_handle = _switch_to_new_window(driver, wait, edit_handles)
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: "Каталог всех настроек"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )
            wait.until(
                lambda current_driver: "Аккаунт Mozilla"
                in current_driver.find_element(by.By.TAG_NAME, "body").text
            )

            settings_body_text = driver.find_element(by.By.TAG_NAME, "body").text
            settings_search_label = wait.until(
                ec.presence_of_element_located((by.By.CSS_SELECTOR, '[data-i18n="profiles.settings_search_label"]'))
            )
            settings_list = wait.until(ec.presence_of_element_located((by.By.ID, "all-settings-list")))
            wait.until(
                lambda current_driver: len(
                    current_driver.find_elements(
                        by.By.CSS_SELECTOR,
                        '#all-settings-list [data-settings-entry-kind="policy"]',
                    )
                ) > 0
            )
            disable_telemetry_row = settings_list.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="DisableTelemetry"]',
            )
            startup_preference_row = settings_list.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="browser.startup.page"]',
            )
            assert "Каталог всех настроек" in settings_body_text
            assert settings_search_label.text.strip().lower() == "поиск по всем настройкам"
            assert "Аккаунт Mozilla" in settings_body_text
            assert "All settings catalog" not in settings_body_text
            assert "Search all controls" not in settings_body_text
            assert "Firefox Account" not in settings_body_text
            assert disable_telemetry_row.get_attribute("data-settings-entry-state") == "configured"
            assert startup_preference_row.get_attribute("data-settings-entry-kind") == "preference"
            assert driver.find_element(by.By.ID, "all-settings-list-summary").text.strip()
            review_actions = wait.until(ec.presence_of_element_located((by.By.ID, "all-settings-review-actions")))
            unknown_review_button = review_actions.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-review-filter="unknown"]',
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-review-filter="unknown"]',
                ).get_attribute("data-settings-review-count")
                == "1"
            )
            assert "Импортированные неизвестные ключи" in driver.find_element(by.By.TAG_NAME, "body").text
            _safe_click(driver, unknown_review_button)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-list-filter="unknown"]',
                ).get_attribute("aria-pressed")
                == "true"
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "FuturePolicy"
            )
            future_policy_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="FuturePolicy"]',
            )
            assert future_policy_row.get_attribute("data-settings-entry-unknown") == "true"
            assert future_policy_row.get_attribute("data-settings-entry-state") == "configured"
            _safe_click(driver, driver.find_element(by.By.CSS_SELECTOR, '[data-settings-list-filter="all"]'))
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-list-filter="all"]',
                ).get_attribute("aria-pressed")
                == "true"
            )

            new_tab_page_row = settings_list.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="NewTabPage"]',
            )
            _safe_click(driver, new_tab_page_row)
            detail_panel = wait.until(
                ec.presence_of_element_located((by.By.ID, "all-settings-detail-panel"))
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "NewTabPage"
            )
            new_tab_page_select = detail_panel.find_element(
                by.By.CSS_SELECTOR,
                '[data-schema-policy-field="__value__"]',
            )
            assert new_tab_page_select.get_attribute("value") == ""
            ui.Select(new_tab_page_select).select_by_value("true")
            wait.until(
                lambda current_driver: "true"
                in current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).text
            )

            search_suggest_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="SearchSuggestEnabled"]',
            )
            _safe_click(driver, search_suggest_row)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "SearchSuggestEnabled"
            )
            assert driver.find_element(
                by.By.CSS_SELECTOR,
                '#all-settings-detail-panel [data-schema-policy-kind="boolean-select"]',
            ).is_displayed()

            startup_preference_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="browser.startup.page"]',
            )
            _safe_click(driver, startup_preference_row)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "browser.startup.page"
            )
            assert driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-apply-preference]",
            ).is_displayed()

            add_preference_button = driver.find_element(by.By.ID, "all-settings-add-preference")
            _safe_click(driver, add_preference_button)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "__new_preference__"
            )
            new_pref_name = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-name]",
            )
            new_pref_name.clear()
            new_pref_name.send_keys("browser.test.allSettingsAdded")
            new_pref_type = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-type]",
            )
            ui.Select(new_pref_type).select_by_value("boolean")
            new_pref_value = driver.find_element(
                by.By.CSS_SELECTOR,
                "#all-settings-detail-panel [data-settings-detail-pref-value-select]",
            )
            ui.Select(new_pref_value).select_by_value("true")
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#all-settings-detail-panel [data-settings-detail-apply-preference]",
                ),
            )
            wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '[data-settings-entry-id="browser.test.allSettingsAdded"]',
                ))
            )
            added_preference_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="browser.test.allSettingsAdded"]',
            )
            assert added_preference_row.get_attribute("data-settings-entry-kind") == "preference"
            assert added_preference_row.get_attribute("data-settings-entry-state") == "configured"
            _safe_click(driver, added_preference_row)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "browser.test.allSettingsAdded"
            )
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#all-settings-detail-panel [data-settings-detail-remove]",
                ),
            )
            wait.until(
                lambda current_driver: len(current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    '[data-settings-entry-id="browser.test.allSettingsAdded"]',
                )) == 0
            )

            configured_filter = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-list-filter="configured"]',
            )
            available_filter = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-list-filter="available"]',
            )
            _safe_click(driver, configured_filter)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-list-filter="configured"]',
                ).get_attribute("aria-pressed")
                == "true"
            )
            configured_disable_telemetry_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="DisableTelemetry"]',
            )
            configured_startup_preference_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="browser.startup.page"]',
            )
            assert not configured_disable_telemetry_row.get_attribute("hidden")
            assert configured_startup_preference_row.get_attribute("hidden")

            _safe_click(driver, available_filter)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR,
                    '[data-settings-list-filter="available"]',
                ).get_attribute("aria-pressed")
                == "true"
            )
            available_disable_telemetry_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="DisableTelemetry"]',
            )
            available_startup_preference_row = driver.find_element(
                by.By.CSS_SELECTOR,
                '[data-settings-entry-id="browser.startup.page"]',
            )
            assert available_disable_telemetry_row.get_attribute("hidden")
            assert not available_startup_preference_row.get_attribute("hidden")
            assert "Показано:" in driver.find_element(by.By.ID, "all-settings-list-summary").text

            settings_search = wait.until(
                ec.presence_of_element_located((by.By.ID, "wizard-settings-search-input"))
            )
            settings_search.clear()
            settings_search.send_keys("FuturePolicy")
            wait.until(
                ec.presence_of_element_located((
                    by.By.CSS_SELECTOR,
                    '#wizard-settings-search-results [data-settings-search-target="all-settings-entry:policy:FuturePolicy"]',
                ))
            )
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    '#wizard-settings-search-results [data-settings-search-target="all-settings-entry:policy:FuturePolicy"]',
                ),
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID,
                    "all-settings-detail-panel",
                ).get_attribute("data-settings-detail-id")
                == "FuturePolicy"
            )
            _safe_click(
                driver,
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#all-settings-detail-panel [data-settings-detail-remove]",
                ),
            )
            wait.until(
                lambda current_driver: len(current_driver.find_elements(
                    by.By.CSS_SELECTOR,
                    '[data-settings-entry-id="FuturePolicy"]',
                )) == 0
            )
            _wait_for_selector_disabled(wait, driver, "#validate", False)
            _click_selector(driver, wait, "#validate")
            _wait_for_selector_disabled(wait, driver, "#save", False)
            _click_selector(driver, wait, "#save")
            _wait_for_selector_disabled(wait, driver, "#save", True)
            saved_profile_response = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
            assert saved_profile_response.status_code == 200, saved_profile_response.text
            saved_flags = saved_profile_response.json()["flags"]
            assert saved_flags["NewTabPage"] is True
            assert "FuturePolicy" not in saved_flags
            clear_search_button = wait.until(ec.presence_of_element_located((by.By.ID, "wizard-settings-search-clear")))
            _safe_click(driver, clear_search_button)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "wizard-settings-search-input"
                ).get_attribute("value")
                == ""
            )
            settings_search.send_keys("mozilla")
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "wizard-settings-search-input"
                ).get_attribute("value")
                == "mozilla"
            )
            clear_button = wait.until(ec.presence_of_element_located((by.By.ID, "wizard-settings-search-clear")))
            assert clear_button.get_attribute("data-i18n") == "profiles.wizard_settings_search_clear"

            driver.switch_to.window(settings_handle)
            assert urlparse(driver.current_url).path == f"/profiles/{profile_id}/settings"
        finally:
            _close_chromium_driver(driver)
