from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

from tests.support import build_profile_payload, pick_free_port, run_test_app_server

pytestmark = pytest.mark.browser_ui


SMOKE_LOCALES = ("ru", "zh-CN")


def _load_locale_catalog(locale: str) -> dict[str, str]:
    catalog_path = Path(__file__).resolve().parents[1] / "app" / "i18n" / f"{locale}.json"
    return json.loads(catalog_path.read_text(encoding="utf-8"))


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

    width = 1366
    height = 1200
    debug_port = pick_free_port()
    profile_dir = Path(tempfile.mkdtemp(prefix=f"bpm-browser-smoke-{debug_port}-"))
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
        pytest.skip(f"Chromium UI smoke could not start in this environment: {exc}")
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


def _body_text(driver) -> str:
    return driver.execute_script("return document.body ? document.body.innerText : '';")


def _set_locale(driver, wait, ui, *, locale: str, expected_text: str) -> None:
    select = ui.Select(wait.until(lambda current_driver: current_driver.find_element("id", "lang")))
    select.select_by_value(locale)
    wait.until(lambda current_driver: current_driver.execute_script("return document.documentElement.lang;") == locale)
    wait.until(lambda current_driver: expected_text in _body_text(current_driver))


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


def _create_profile(base_url: str, *, name: str) -> int:
    response = requests.post(
        f"{base_url}/api/profiles",
        json=build_profile_payload(
            name=name,
            description="Chromium smoke profile",
            owner="browser-smoke@example.org",
            schema_version="release-151",
            flags={
                "DisableTelemetry": True,
                "Homepage": {"URL": "https://portal.example.local/", "Locked": True},
            },
        ),
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


def _import_profile_through_picker(driver, wait, by, profile_name: str) -> int:
    policy_document = {"policies": {"DisableTelemetry": True}}
    driver.execute_script(
        """
        const input = document.getElementById('import-firefox-policies-file');
        const payload = JSON.stringify(arguments[0]);
        const file = new File([payload], `${arguments[1]}.json`, { type: 'application/json' });
        const transfer = new DataTransfer();
        transfer.items.add(file);
        input.files = transfer.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        policy_document,
        profile_name,
    )
    wait.until(lambda current_driver: profile_name in current_driver.find_element(by.By.ID, "status").text)
    profile_link = wait.until(lambda current_driver: current_driver.find_element(by.By.LINK_TEXT, profile_name))
    return int(urlparse(profile_link.get_attribute("href")).path.strip("/").split("/")[1])


def test_browser_smoke_imports_firefox_policies_json_in_russian_library():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    ru = _load_locale_catalog("ru")

    with run_test_app_server() as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "import-firefox-policies-file")))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_hint"])
            assert ru["profiles.import_firefox_policies_json"] in _body_text(driver)

            profile_id = _import_profile_through_picker(driver, wait, by, "smoke-import-ru")
            export_response = requests.get(
                f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json",
                timeout=10,
            )
            assert export_response.status_code == 200, export_response.text
            assert export_response.json()["policies"]["DisableTelemetry"] is True
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_primary_routes_render_in_ru_and_zh_cn():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale_catalogs = {locale: _load_locale_catalog(locale) for locale in SMOKE_LOCALES}

    route_expectations = (
        ("library", "/profiles", "#list", ("profiles.title", "profiles.nav_library")),
        ("guided", "/profiles/{profile_id}/edit", "#wizard-panel", ("profiles.workspace_scope_guided",)),
        ("settings", "/profiles/{profile_id}/settings", "#settings-panel", ("profiles.editor_chrome_settings_link",)),
        (
            "json",
            "/profiles/{profile_id}/json",
            "#editor-panel",
            ("profiles.editor_chrome_json_link", "profiles.editor_title_section"),
        ),
    )

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Primary Routes Browser Smoke")
        for locale in SMOKE_LOCALES:
            driver = _build_chromium_driver()
            wait = ui.WebDriverWait(driver, 20)
            catalog = locale_catalogs[locale]
            try:
                driver.get(f"{base_url}/profiles")
                wait.until(ec.presence_of_element_located((by.By.ID, "list")))
                _set_locale(driver, wait, ui, locale=locale, expected_text=catalog["profiles.locale_hint"])

                for _route_name, route_template, ready_selector, keys in route_expectations:
                    driver.get(f"{base_url}{route_template.format(profile_id=profile_id)}")
                    wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))
                    wait.until(
                        lambda current_driver, expected_locale=locale: current_driver.execute_script(
                            "return document.documentElement.lang;"
                        ) == expected_locale
                    )
                    body_text = _body_text(driver)
                    for key in keys:
                        assert catalog[key].casefold() in body_text.casefold()
                    _assert_document_fits(driver)
            finally:
                _close_chromium_driver(driver)


def test_browser_smoke_editor_mode_links_preserve_route_context():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Mode Link Browser Smoke")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(
                f"{base_url}/profiles/{profile_id}/settings"
                f"?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
            )
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            json_href = wait.until(
                ec.presence_of_element_located((by.By.ID, "editor-mode-json"))
            ).get_attribute("href")

            assert f"/profiles/{profile_id}/json" in json_href
            assert f"return=/profiles/{profile_id}/settings" in json_href
            assert "focus=policy%3ADisableTelemetry" in json_href

            driver.get(f"{base_url}/profiles/{profile_id}/json?focus=raw")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            settings_href = wait.until(
                ec.presence_of_element_located((by.By.ID, "editor-mode-settings"))
            ).get_attribute("href")

            assert f"/profiles/{profile_id}/settings" in settings_href
            assert f"return=/profiles/{profile_id}/json" in settings_href
            assert "focus=settings-schema-shell-step-8" in settings_href
        finally:
            _close_chromium_driver(driver)
