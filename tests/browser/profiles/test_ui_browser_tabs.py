from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlparse

import pytest
import requests

from tests.browser.harness import (
    assert_document_fits as _assert_document_fits,
)
from tests.browser.harness import (
    body_text as _body_text,
)
from tests.browser.harness import (
    build_chromium_driver as _build_chromium_driver,
)
from tests.browser.harness import (
    click_and_switch_to_new_tab as _click_and_switch_to_new_tab,
)
from tests.browser.harness import (
    click_element as _click_element,
)
from tests.browser.harness import (
    close_chromium_driver as _close_chromium_driver,
)
from tests.browser.harness import (
    scoped_test_app_server as run_test_app_server,
)
from tests.browser.profiles.pages import create_profile as _create_profile
from tests.browser.profiles.pages import load_locale_catalog as _load_locale_catalog
from tests.browser.profiles.pages import set_locale as _set_locale
from tests.support import (
    build_corporate_cis_l2_profile_fixture,
)

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]


SMOKE_LOCALES = ("ru", "zh-CN")
COMPACT_HEADER_LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def _click_css_when_ready(driver, wait, by, selector: str) -> None:
    def attempt(current_driver):
        try:
            element = current_driver.find_element(by.By.CSS_SELECTOR, selector)
            if not element.is_displayed() or not element.is_enabled():
                return False
            _click_element(current_driver, element)
            return True
        except Exception as exc:
            if exc.__class__.__name__ in {
                "ElementClickInterceptedException",
                "NoSuchElementException",
                "StaleElementReferenceException",
            }:
                return False
            raise

    wait.until(attempt)


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
    wait.until(
        lambda current_driver: profile_name in current_driver.find_element(by.By.ID, "status").text
    )
    profile_link = wait.until(
        lambda current_driver: current_driver.find_element(by.By.LINK_TEXT, profile_name)
    )
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
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])
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
        ("library", "/profiles", "#list", ("profiles.nav_library",)),
        (
            "guided",
            "/profiles/{profile_id}/edit",
            "#wizard-panel",
            ("profiles.workspace_scope_guided",),
        ),
        (
            "settings",
            "/profiles/{profile_id}/settings",
            "#settings-panel",
            ("profiles.editor_chrome_settings_link",),
        ),
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
                _set_locale(
                    driver, wait, ui, locale=locale, expected_text=catalog["profiles.locale_label"]
                )

                for _route_name, route_template, ready_selector, keys in route_expectations:
                    driver.get(f"{base_url}{route_template.format(profile_id=profile_id)}")
                    wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))
                    wait.until(
                        lambda current_driver, expected_locale=locale: (
                            current_driver.execute_script("return document.documentElement.lang;")
                            == expected_locale
                        )
                    )
                    body_text = _body_text(driver)
                    for key in keys:
                        assert catalog[key].casefold() in body_text.casefold()
                    _assert_document_fits(driver)
            finally:
                _close_chromium_driver(driver)


def test_browser_guided_schema_selector_offers_and_switches_three_channels():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    select_module = pytest.importorskip("selenium.webdriver.support.select")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    expected_channels = (
        ("esr-140.13", "ESR 140.13"),
        ("esr-153.0", "ESR 153.0"),
        ("release-153", "Release 153"),
    )

    with run_test_app_server() as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/new")
            schema_select = wait.until(ec.presence_of_element_located((by.By.ID, "profile-type")))
            selector = select_module.Select(schema_select)

            assert [
                (option.get_attribute("value"), option.text) for option in selector.options
            ] == list(expected_channels)
            for channel, label in expected_channels:
                selector.select_by_value(channel)
                wait.until(
                    lambda current_driver, expected_channel=channel: (
                        current_driver.find_element(by.By.ID, "profile-type").get_attribute("value")
                        == expected_channel
                    )
                )
                assert (
                    select_module.Select(
                        driver.find_element(by.By.ID, "profile-type")
                    ).first_selected_option.text
                    == label
                )
        finally:
            _close_chromium_driver(driver)


def test_browser_compact_header_is_usable_across_routes_locales_themes_and_zoom():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale_catalogs = {locale: _load_locale_catalog(locale) for locale in COMPACT_HEADER_LOCALES}
    route_expectations = (
        ("/profiles", "#list"),
        ("/profiles/{profile_id}/edit", "#wizard-panel"),
        ("/profiles/{profile_id}/settings", "#settings-panel"),
        ("/profiles/{profile_id}/json", "#editor-panel"),
        ("/profiles/compare", "#compare-page"),
    )

    def assert_header_state(driver, catalog: dict[str, str]) -> None:
        metrics = driver.execute_script("""
            const header = document.querySelector('[data-bpm-header]');
            const docs = header?.querySelector('[data-documentation-link]');
            const locale = header?.querySelector('#lang');
            const theme = header?.querySelector('#theme');
            const labelFor = (control) => control?.closest('label')?.innerText?.trim() || '';
            const rect = (node) => {
              const value = node?.getBoundingClientRect();
              return value ? { width: value.width, height: value.height } : null;
            };
            return {
              headerPresent: Boolean(header),
              brandPresent: Boolean(header?.querySelector('[data-bpm-header-brand]')),
              preferencesPresent: Boolean(header?.querySelector('[data-bpm-header-preferences]')),
              workspacePresent: Boolean(header?.querySelector('[data-bpm-header-workspace]')),
              documentationText: docs?.innerText?.trim() || '',
              localeLabel: labelFor(locale),
              themeLabel: labelFor(theme),
              localeRect: rect(locale),
              themeRect: rect(theme),
              headerScrollWidth: header?.scrollWidth || 0,
              headerClientWidth: header?.clientWidth || 0,
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: window.innerWidth,
            };
            """)
        assert metrics["headerPresent"] is True
        assert metrics["brandPresent"] is True
        assert metrics["preferencesPresent"] is True
        assert metrics["workspacePresent"] is True
        assert metrics["documentationText"]
        assert catalog["profiles.locale_label"].casefold() in metrics["localeLabel"].casefold()
        assert catalog["profiles.theme_label"].casefold() in metrics["themeLabel"].casefold()
        # Browser layout uses floating-point CSS pixels.  Preserve the 44 px
        # touch-target requirement while ignoring sub-millipixel rounding noise
        # such as Chromium's 43.99999237060547 for a computed 44 px control.
        assert round(metrics["localeRect"]["height"], 3) >= 44, metrics
        assert round(metrics["themeRect"]["height"], 3) >= 44, metrics
        assert metrics["headerScrollWidth"] <= metrics["headerClientWidth"] + 1, metrics
        assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Compact Header Browser Smoke")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))

            for locale in COMPACT_HEADER_LOCALES:
                catalog = locale_catalogs[locale]
                _set_locale(
                    driver,
                    wait,
                    ui,
                    locale=locale,
                    expected_text=catalog["profiles.locale_label"],
                )
                for route_template, ready_selector in route_expectations:
                    driver.get(f"{base_url}{route_template.format(profile_id=profile_id)}")
                    wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))
                    wait.until(
                        lambda current_driver, expected_locale=locale: (
                            current_driver.execute_script("return document.documentElement.lang;")
                            == expected_locale
                        )
                    )
                    assert_header_state(driver, catalog)

            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            catalog = locale_catalogs[COMPACT_HEADER_LOCALES[-1]]
            for theme_mode in ("system", "light", "dark"):
                ui.Select(driver.find_element(by.By.ID, "theme")).select_by_value(theme_mode)
                wait.until(
                    lambda current_driver, expected_mode=theme_mode: (
                        current_driver.execute_script(
                            "return document.documentElement.dataset.themeMode;"
                        )
                        == expected_mode
                    )
                )
                assert_header_state(driver, catalog)

            documentation_link = driver.find_element(
                by.By.CSS_SELECTOR, "[data-documentation-link]"
            )
            driver.execute_script("arguments[0].focus();", documentation_link)
            assert driver.switch_to.active_element == documentation_link
            documentation_link.send_keys(keys.Keys.TAB)
            assert driver.switch_to.active_element.get_attribute("id") == "lang"
            driver.switch_to.active_element.send_keys(keys.Keys.TAB)
            assert driver.switch_to.active_element.get_attribute("id") == "theme"

            driver.set_window_size(390, 900)
            driver.execute_script("document.documentElement.style.fontSize = '200%';")
            assert_header_state(driver, catalog)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_guided_disclosure_labels_follow_active_locale():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale_catalogs = {locale: _load_locale_catalog(locale) for locale in SMOKE_LOCALES}

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Disclosure Locale Browser Smoke")
        for locale in SMOKE_LOCALES:
            driver = _build_chromium_driver()
            wait = ui.WebDriverWait(driver, 20)
            catalog = locale_catalogs[locale]
            try:
                driver.get(f"{base_url}/profiles/{profile_id}/edit")
                wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
                _set_locale(
                    driver,
                    wait,
                    ui,
                    locale=locale,
                    expected_text=catalog["profiles.locale_label"],
                )
                disclosure = wait.until(
                    ec.presence_of_element_located(
                        (
                            by.By.CSS_SELECTOR,
                            '[data-wizard-disclosure-toggle][aria-controls="wizard-baseline-override-panel"]',
                        )
                    )
                )
                wait.until(
                    lambda _driver, button=disclosure, expected=catalog["profiles.wizard_disclosure_show"]: (
                        button.text.strip() == expected
                    )
                )
                driver.execute_script("arguments[0].click();", disclosure)
                wait.until(
                    lambda _driver, button=disclosure, expected=catalog["profiles.wizard_disclosure_hide"]: (
                        button.text.strip() == expected
                    )
                )
            finally:
                _close_chromium_driver(driver)


def test_browser_guided_choice_cards_stay_compact_and_keep_selected_state():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Compact Guided Choice Cards")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))

            scenario = driver.find_element(
                by.By.CSS_SELECTOR, '[data-scenario-key="shared_devices"]'
            )
            _click_element(driver, scenario)
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, '[data-scenario-key="shared_devices"]'
                    ).get_attribute("aria-pressed")
                    == "true"
                )
            )
            scenario_state = driver.execute_script("""
                const card = document.querySelector('[data-scenario-key="shared_devices"]');
                return {
                  active: card?.classList.contains('wizard-starter-card--active'),
                  explanatoryNodes: card?.querySelectorAll(
                    '.wizard-starter-copy, .wizard-starter-note, .wizard-toggle-copy'
                  ).length,
                };
                """)
            assert scenario_state == {"active": True, "explanatoryNodes": 0}

            _click_css_when_ready(driver, wait, by, '[data-step="2"]')
            wait.until(
                lambda current_driver: (
                    "is-active"
                    in current_driver.find_element(by.By.ID, "wizard-step-2")
                    .get_attribute("class")
                    .split()
                )
            )
            updates = driver.find_element(
                by.By.CSS_SELECTOR, '[data-general-policy-preset="updates"]'
            )
            _click_element(driver, updates)
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, '[data-general-policy-preset="updates"]'
                    ).get_attribute("aria-pressed")
                    == "true"
                )
            )
            preset_state = driver.execute_script("""
                const card = document.querySelector('[data-general-policy-preset="updates"]');
                return {
                  applied: card?.classList.contains('wizard-search-engine-preset--applied'),
                  explanatoryNodes: card?.querySelectorAll(
                    '.wizard-search-engine-preset-copy'
                  ).length,
                };
                """)
            assert preset_state == {"applied": True, "explanatoryNodes": 0}
        finally:
            _close_chromium_driver(driver)


def test_browser_guided_sections_use_flat_layout_without_losing_responsive_flow():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Flat Guided Sections")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            _click_css_when_ready(driver, wait, by, '[data-step="2"]')
            wait.until(
                lambda current_driver: (
                    "is-active"
                    in current_driver.find_element(by.By.ID, "wizard-step-2")
                    .get_attribute("class")
                    .split()
                )
            )

            layout = driver.execute_script("""
                const styles = (selector) => {
                  const element = document.querySelector(selector);
                  const computed = element ? getComputedStyle(element) : null;
                  return computed && {
                    borderTopWidth: computed.borderTopWidth,
                    paddingTop: computed.paddingTop,
                    paddingRight: computed.paddingRight,
                    backgroundColor: computed.backgroundColor,
                  };
                };
                return {
                  panel: styles('#wizard-step-2'),
                  presets: styles('#wizard-general-policy-presets'),
                  status: styles('#wizard-general-policy-section-status'),
                  duplicateKickers: document.querySelectorAll(
                    '[data-i18n="profiles.wizard_main_choice_label"], ' +
                    '[data-i18n="profiles.wizard_fine_tuning_label"]'
                  ).length,
                };
                """)
            assert layout["panel"]["borderTopWidth"] == "0px"
            assert layout["panel"]["paddingTop"] == "0px"
            assert layout["presets"]["borderTopWidth"] == "0px"
            assert layout["presets"]["paddingTop"] == "0px"
            assert layout["status"]["borderTopWidth"] != "0px"
            assert layout["duplicateKickers"] == 0

            driver.set_window_size(390, 900)
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_guided_cis_help_icon_is_keyboard_focusable():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Guided Context Help")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit")
            cis_help = wait.until(
                ec.element_to_be_clickable(
                    (
                        by.By.CSS_SELECTOR,
                        '[data-context-help-target="cis-baseline-selection"]',
                    )
                )
            )
            assert cis_help.get_attribute("target") == "_blank"
            assert cis_help.get_attribute("rel") == "noopener noreferrer"
            assert cis_help.get_attribute("aria-label")
            assert cis_help.get_attribute("href").startswith(f"{base_url}/help/")

            driver.execute_script("arguments[0].focus();", cis_help)
            assert driver.switch_to.active_element == cis_help
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_library_permanent_delete_handles_active_archived_and_failure():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with run_test_app_server() as base_url:
        active_id = _create_profile(base_url, name="Permanent Delete Active")
        archived_id = _create_profile(base_url, name="Permanent Delete Archived")
        failure_id = _create_profile(base_url, name="Permanent Delete Failure")
        archive_response = requests.delete(f"{base_url}/api/profiles/{archived_id}", timeout=10)
        assert archive_response.status_code == 204, archive_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            driver.execute_script("""
                const lifecycle = document.getElementById('library-lifecycle-filter');
                lifecycle.value = 'all';
                lifecycle.dispatchEvent(new Event('change', { bubbles: true }));
                window.__BPM_CONFIRM_MESSAGES__ = [];
                window.confirm = (message) => {
                  window.__BPM_CONFIRM_MESSAGES__.push(String(message));
                  return true;
                };
                """)

            def delete_button(profile_id: int):
                return (
                    by.By.CSS_SELECTOR,
                    f'[data-library-lifecycle-action="hard-delete"]'
                    f'[data-library-profile-id="{profile_id}"]',
                )

            for profile_id in (active_id, archived_id):
                target = delete_button(profile_id)
                selector = target[1]
                wait.until(
                    lambda current_driver, current_selector=selector: current_driver.execute_script(
                        "return document.querySelector(arguments[0])?.classList.contains('danger-button') || false;",
                        current_selector,
                    )
                )
                _click_css_when_ready(driver, wait, by, selector)
                wait.until(
                    lambda current_driver, selector=target: (
                        not current_driver.find_elements(*selector)
                    )
                )
                get_response = requests.get(
                    f"{base_url}/api/profiles/{profile_id}?include_deleted=true",
                    timeout=10,
                )
                assert get_response.status_code == 404, get_response.text

            confirmation_messages = driver.execute_script(
                "return window.__BPM_CONFIRM_MESSAGES__.slice();"
            )
            assert len(confirmation_messages) == 2
            assert all(
                "archive" in message and "cannot be restored" in message
                for message in confirmation_messages
            )

            driver.execute_script(
                """
                const originalFetch = window.fetch.bind(window);
                const failedUrl = `/api/profiles/${arguments[0]}/hard`;
                window.fetch = (input, init = {}) => {
                  if (String(input).endsWith(failedUrl) && init.method === 'DELETE') {
                    return Promise.resolve(new Response(
                      JSON.stringify({ detail: 'forced hard-delete failure' }),
                      { status: 500, headers: { 'Content-Type': 'application/json' } },
                    ));
                  }
                  return originalFetch(input, init);
                };
                """,
                failure_id,
            )
            failure_button = wait.until(ec.element_to_be_clickable(delete_button(failure_id)))
            driver.execute_script("arguments[0].click();", failure_button)
            wait.until(
                lambda current_driver: (
                    "forced hard-delete failure"
                    in current_driver.find_element(by.By.ID, "status").text
                )
            )
            assert driver.find_elements(*delete_button(failure_id))
            assert (
                requests.get(f"{base_url}/api/profiles/{failure_id}", timeout=10).status_code == 200
            )
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_all_settings_counts_hydrated_corporate_cis_profile():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    fixture = build_corporate_cis_l2_profile_fixture(name="All Settings Counts Browser Smoke")

    with run_test_app_server() as base_url:
        payload = deepcopy(fixture.payload)
        payload["flags"]["GenerativeAI"] = {"Enabled": False, "Locked": True}
        payload["flags"]["VisualSearchEnabled"] = False
        response = requests.post(f"{base_url}/api/profiles", json=payload, timeout=10)
        assert response.status_code == 201, response.text
        profile_id = int(response.json()["id"])
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/settings?settingsMode=configured")
            wait.until(ec.presence_of_element_located((by.By.ID, "settings-panel")))
            wait.until(
                lambda current_driver: current_driver.execute_script("""
                    const summary = document.getElementById('all-settings-list-summary')?.textContent || '';
                    const sourceCounts = Array.from(
                      document.querySelectorAll('[data-settings-source-filter-count]')
                    ).map((el) => Number(el.textContent || '0'));
                    return /configured|настроено/.test(summary)
                      && /configured|настроено/.test(summary)
                      && sourceCounts.some((count) => count > 0);
                    """)
            )
            counts = driver.execute_script("""
                const summary = document.getElementById('all-settings-list-summary')?.textContent || '';
                const configuredMatch = summary.match(/настроено:?\\s*(\\d+)/i)
                  || summary.match(/(\\d+)\\s+configured/i);
                const visibleMatch = summary.match(/Показано:?\\s*(\\d+)\\s+из\\s+(\\d+)/i)
                  || summary.match(/(\\d+)\\s+shown\\s+of\\s+(\\d+)/i);
                const sourceCounts = Object.fromEntries(
                  Array.from(document.querySelectorAll('[data-settings-source-filter]')).map((button) => [
                    button.dataset.settingsSourceFilter,
                    Number(button.querySelector('[data-settings-source-filter-count]')?.textContent || '0'),
                  ])
                );
                const listFilters = Object.fromEntries(
                  Array.from(document.querySelectorAll('[data-settings-list-filter]')).map((button) => [
                    button.dataset.settingsListFilter,
                    {
                      hidden: button.hidden,
                      count: Number(button.querySelector('[data-settings-list-filter-count]')?.textContent || '0'),
                    },
                  ])
                );
                const unknownReviewCount = Number(
                  document
                    .querySelector('[data-settings-review-filter="unknown"] [data-settings-review-count]')
                    ?.textContent || '0'
                );
                return {
                  summary,
                  configured: configuredMatch ? Number(configuredMatch[1]) : 0,
                  visible: visibleMatch ? Number(visibleMatch[1]) : 0,
                  total: visibleMatch ? Number(visibleMatch[2]) : 0,
                  sourceCounts,
                  listFilters,
                  unknownReviewCount,
                };
                """)

            assert counts["configured"] > 0, counts
            assert 0 < counts["visible"] < counts["total"], counts
            assert counts["visible"] == counts["configured"], counts
            assert counts["listFilters"]["configured"]["hidden"] is True, counts
            assert counts["listFilters"]["available"]["hidden"] is True, counts
            assert counts["listFilters"]["all"]["hidden"] is False, counts
            assert counts["listFilters"]["all"]["count"] == counts["visible"], counts
            assert counts["sourceCounts"]["source:cis"] > 0, counts
            assert counts["sourceCounts"]["source:baseline"] > 0, counts
            assert counts["unknownReviewCount"] == 0, counts

            driver.execute_script("""
                document
                  .querySelector('[data-settings-list-budget-action="expand"]')
                  ?.click();
                """)
            wait.until(
                lambda current_driver: current_driver.execute_script("""
                    return Boolean(
                      document.querySelector('[data-settings-list-budget-action="next"]')
                    );
                    """)
            )
            driver.execute_script("""
                document
                  .querySelector('[data-settings-list-budget-action="next"]')
                  ?.click();
                """)
            wait.until(
                lambda current_driver: current_driver.execute_script("""
                    return Boolean(
                      document.querySelector('[data-settings-entry-id="VisualSearchEnabled"]')
                    );
                    """)
            )
            after_selection = driver.execute_script("""
                document
                  .querySelector('[data-settings-entry-id="VisualSearchEnabled"]')
                  ?.click();
                const summary = document.getElementById('all-settings-list-summary')?.textContent || '';
                const configuredMatch = summary.match(/настроено:?\\s*(\\d+)/i)
                  || summary.match(/(\\d+)\\s+configured/i);
                const visibleMatch = summary.match(/Показано:?\\s*(\\d+)\\s+из\\s+(\\d+)/i)
                  || summary.match(/(\\d+)\\s+shown\\s+of\\s+(\\d+)/i);
                const allFilterCount = Number(
                  document
                    .querySelector('[data-settings-list-filter="all"] [data-settings-list-filter-count]')
                    ?.textContent || '0'
                );
                const selected = document.querySelector('.all-settings-list-row.is-selected');
                return {
                  summary,
                  configured: configuredMatch ? Number(configuredMatch[1]) : 0,
                  visible: visibleMatch ? Number(visibleMatch[1]) : 0,
                  total: visibleMatch ? Number(visibleMatch[2]) : 0,
                  allFilterCount,
                  selectedId: selected?.dataset.settingsEntryId || '',
                };
                """)
            assert after_selection["selectedId"] == "VisualSearchEnabled", after_selection
            assert after_selection["visible"] == after_selection["configured"], after_selection
            assert after_selection["allFilterCount"] == after_selection["configured"], (
                after_selection
            )
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
            json_mode_link = wait.until(
                ec.presence_of_element_located((by.By.ID, "editor-mode-json"))
            )
            json_href = json_mode_link.get_attribute("href")
            settings_mode_link = driver.find_element(by.By.ID, "editor-mode-settings")

            assert f"/profiles/{profile_id}/json" in json_href
            assert f"return=/profiles/{profile_id}/settings" in json_href
            assert "focus=policy%3ADisableTelemetry" in json_href
            assert settings_mode_link.get_attribute("aria-current") == "page"
            assert json_mode_link.get_attribute("aria-current") is None

            driver.get(f"{base_url}/profiles/{profile_id}/json?focus=raw")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            settings_mode_link = wait.until(
                ec.presence_of_element_located((by.By.ID, "editor-mode-settings"))
            )
            settings_href = settings_mode_link.get_attribute("href")
            json_mode_link = driver.find_element(by.By.ID, "editor-mode-json")

            assert f"/profiles/{profile_id}/settings" in settings_href
            assert f"return=/profiles/{profile_id}/json" in settings_href
            assert "focus=settings-schema-shell-step-8" in settings_href
            assert settings_mode_link.get_attribute("aria-current") is None
            assert json_mode_link.get_attribute("aria-current") == "page"
        finally:
            _close_chromium_driver(driver)


def test_browser_shared_editor_chrome_keeps_live_state_once_across_transitions():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    en = _load_locale_catalog("en")

    def chrome_state(driver) -> dict[str, str | bool]:
        return driver.execute_script("""
            const text = (id) => document.getElementById(id)?.textContent?.trim() || '';
            const clone = document.getElementById('profile-derived-note');
            return {
              state: text('profile-state-badge'),
              workspace: text('workspace-signal'),
              validation: text('validation-preview'),
              meta: text('current-meta'),
              clone: text('profile-derived-note'),
              cloneVisible: Boolean(clone && !clone.hidden),
            };
            """)

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name="Live Chrome State Profile")
        archived_id = _create_profile(base_url, name="Archived Chrome State Profile")
        archive_response = requests.delete(f"{base_url}/api/profiles/{archived_id}", timeout=10)
        assert archive_response.status_code == 204, archive_response.text

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            for route, ready_selector in (
                (f"/profiles/{profile_id}/edit", "#wizard-panel"),
                (f"/profiles/{profile_id}/settings", "#settings-panel"),
                (f"/profiles/{profile_id}/json?focus=raw", "#editor-panel"),
            ):
                driver.get(f"{base_url}{route}")
                wait.until(ec.presence_of_element_located((by.By.CSS_SELECTOR, ready_selector)))
                wait.until(
                    lambda current_driver: (
                        chrome_state(current_driver)["workspace"] == en["profiles.signal_saved"]
                    )
                )
                state = chrome_state(driver)
                assert state["state"] == en["profiles.badge_active"], state
                assert state["meta"] == f"#{profile_id}", state
                assert state["validation"], state

            assert driver.find_element(by.By.ID, "format").is_displayed()
            editor_language = driver.execute_script(
                "return window.monaco?.editor?.getModels?.()[0]?.getLanguageId?.();"
            )
            assert editor_language == "json"
            _click_element(driver, driver.find_element(by.By.ID, "validate"))
            wait.until(
                lambda current_driver: (
                    chrome_state(current_driver)["validation"] == en["profiles.validation_ok"]
                )
            )
            driver.execute_script("""
                const model = window.monaco?.editor?.getModels?.()[0];
                if (!model) return false;
                model.setValue('{"DisableTelemetry":true}');
                return true;
                """)
            wait.until(
                lambda current_driver: (
                    chrome_state(current_driver)["workspace"] == en["profiles.signal_dirty"]
                )
            )
            _click_element(driver, driver.find_element(by.By.ID, "format"))
            _click_element(driver, driver.find_element(by.By.ID, "save"))
            wait.until(
                lambda current_driver: (
                    chrome_state(current_driver)["workspace"] == en["profiles.signal_saved"]
                )
            )

            driver.execute_script("""
                const model = window.monaco?.editor?.getModels?.()[0];
                if (!model) return false;
                model.setValue('{');
                return true;
                """)
            wait.until(
                lambda current_driver: (
                    chrome_state(current_driver)["workspace"] == en["profiles.signal_invalid"]
                )
            )
            assert not driver.find_element(by.By.ID, "validate").is_enabled()

            driver.get(f"{base_url}/profiles/new?clone_from={profile_id}")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(lambda current_driver: chrome_state(current_driver)["cloneVisible"] is True)
            clone_state = chrome_state(driver)
            assert clone_state["state"] == en["profiles.badge_draft"], clone_state
            assert "Live Chrome State Profile" in clone_state["clone"], clone_state
            assert clone_state["meta"] == "", clone_state

            driver.get(f"{base_url}/profiles/{archived_id}/edit?include_deleted=true")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            wait.until(
                lambda current_driver: (
                    chrome_state(current_driver)["state"] == en["profiles.badge_deleted"]
                )
            )
            archived_state = chrome_state(driver)
            assert archived_state["meta"] == f"#{archived_id}", archived_state
            assert "include_deleted=true" in driver.find_element(
                by.By.ID, "editor-mode-settings"
            ).get_attribute("href")
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_json_editor_loads_corporate_cis_known_preferences():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    fixture = build_corporate_cis_l2_profile_fixture(name="JSON CIS Preferences Browser Smoke")

    with run_test_app_server() as base_url:
        response = requests.post(f"{base_url}/api/profiles", json=fixture.payload, timeout=10)
        assert response.status_code == 201, response.text
        profile_id = int(response.json()["id"])
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/json?focus=raw")
            wait.until(ec.presence_of_element_located((by.By.ID, "editor-panel")))
            wait.until(
                lambda current_driver: current_driver.execute_script("""
                    const value = window.monaco?.editor?.getModels?.()[0]?.getValue?.() || '';
                    return value.includes('browser.safebrowsing.malware.enabled');
                    """)
            )
            status = driver.execute_script("""
                const status = document.getElementById('status');
                return {
                  text: status?.textContent?.trim() || '',
                  isError: status?.classList?.contains('status-banner--error') || false,
                };
                """)

            assert status["isError"] is False, status
            assert "knownPreference" not in status["text"], status
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_library_compare_preserves_locale_in_new_tab_and_selects_two_profiles():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    ru = _load_locale_catalog("ru")

    left_name = "Compare Browser Smoke Alpha"
    right_name = "Compare Browser Smoke Beta"

    with run_test_app_server() as base_url:
        left_id = _create_profile(
            base_url,
            name=left_name,
            flags={
                "DisableTelemetry": True,
                "Homepage": {"URL": "https://alpha.example.local/", "Locked": True},
            },
        )
        right_id = _create_profile(
            base_url,
            name=right_name,
            flags={
                "DisableTelemetry": False,
                "Homepage": {"URL": "https://beta.example.local/", "Locked": True},
            },
        )
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            wait.until(lambda current_driver: left_name in _body_text(current_driver))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])
            assert ru["profiles.compare_action"] in _body_text(driver)

            compare_link = wait.until(
                ec.element_to_be_clickable((by.By.ID, "compare-profiles-link"))
            )
            assert compare_link.get_attribute("target") == "_blank"
            assert compare_link.get_attribute("rel") == "noopener"

            _click_and_switch_to_new_tab(driver, wait, compare_link)
            wait.until(ec.presence_of_element_located((by.By.ID, "compare-page")))
            assert urlparse(driver.current_url).path == "/profiles/compare"
            wait.until(
                lambda current_driver: (
                    current_driver.execute_script("return document.documentElement.lang;") == "ru"
                )
            )
            wait.until(
                lambda current_driver: (
                    ru["profiles.compare_route_title"] in _body_text(current_driver)
                )
            )
            compare_lang = wait.until(ec.presence_of_element_located((by.By.ID, "lang")))
            assert compare_lang.get_attribute("value") == "ru"
            assert not driver.find_elements(
                by.By.CSS_SELECTOR,
                '[data-i18n="profiles.compare_route_eyebrow"], '
                '[data-i18n="profiles.compare_selection_title"], '
                '[data-i18n="profiles.compare_settings_title"]',
            )
            assert not driver.find_elements(
                by.By.CSS_SELECTOR,
                '#compare-page a[href="/profiles"]',
            )
            compare_heading = driver.find_element(by.By.CSS_SELECTOR, ".compare-route-heading")
            assert len(compare_heading.find_elements(by.By.XPATH, "./*")) == 1

            for side, profile_id, profile_name in (
                ("left", left_id, left_name),
                ("right", right_id, right_name),
            ):
                search = wait.until(
                    ec.presence_of_element_located((by.By.ID, f"compare-{side}-search"))
                )
                search.clear()
                search.send_keys(profile_name)
                selector = (
                    f'[data-compare-result-side="{side}"][data-compare-profile-id="{profile_id}"]'
                )

                def select_current_option(
                    current_driver,
                    current_side=side,
                    expected_name=profile_name,
                    current_selector=selector,
                ):
                    if (
                        expected_name
                        in current_driver.find_element(
                            by.By.ID, f"compare-{current_side}-profile"
                        ).text
                    ):
                        return True
                    try:
                        _click_element(
                            current_driver,
                            current_driver.find_element(by.By.CSS_SELECTOR, current_selector),
                        )
                    except Exception as exc:
                        if exc.__class__.__name__ not in {
                            "ElementClickInterceptedException",
                            "NoSuchElementException",
                            "StaleElementReferenceException",
                        }:
                            raise
                    return False

                wait.until(select_current_option)

            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "#compare-settings-rows tr[data-compare-row-id]"
                        )
                    )
                    >= 1
                )
            )
            left_cells = driver.find_elements(
                by.By.CSS_SELECTOR,
                '#compare-settings-rows td[data-compare-column="left"]',
            )
            right_cells = driver.find_elements(
                by.By.CSS_SELECTOR,
                '#compare-settings-rows td[data-compare-column="right"]',
            )
            assert left_cells
            assert len(left_cells) == len(right_cells)
            assert driver.find_elements(
                by.By.CSS_SELECTOR,
                '#compare-settings-rows tr[data-compare-row-changed="true"]',
            )
            assert (
                "DisableTelemetry" in driver.find_element(by.By.ID, "compare-settings-table").text
            )
            assert not driver.find_elements(by.By.ID, "list")
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-clone-profile-id]")
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_compare_selector_scrolls_large_profile_lists_and_selects_profiles():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    bulk_prefix = "Compare Selector Large List"
    right_name = "Compare Selector Right Target"

    with run_test_app_server() as base_url:
        for index in range(50):
            _create_profile(
                base_url,
                name=f"{bulk_prefix} {index:02d}",
                flags={
                    "DisableTelemetry": index % 2 == 0,
                    "Homepage": {
                        "URL": f"https://bulk-{index:02d}.example.local/",
                        "Locked": True,
                    },
                },
            )
        right_id = _create_profile(
            base_url,
            name=right_name,
            flags={
                "DisableTelemetry": False,
                "Homepage": {"URL": "https://right-target.example.local/", "Locked": True},
            },
        )

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/compare")
            wait.until(ec.presence_of_element_located((by.By.ID, "compare-page")))

            left_search = wait.until(
                ec.presence_of_element_located((by.By.ID, "compare-left-search"))
            )
            left_search.clear()
            left_search.send_keys(bulk_prefix)
            wait.until(ec.presence_of_element_located((by.By.ID, "compare-left-results")))
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR,
                            '#compare-left-results [data-compare-profile-option="true"]',
                        )
                    )
                    >= 12
                )
            )
            left_options = driver.find_elements(
                by.By.CSS_SELECTOR,
                '#compare-left-results [data-compare-profile-option="true"]',
            )
            list_metrics = wait.until(
                lambda current_driver: current_driver.execute_script("""
                    const list = document.querySelector("#compare-left-results");
                    const metrics = {
                      clientHeight: list.clientHeight,
                      scrollHeight: list.scrollHeight,
                      overflowY: window.getComputedStyle(list).overflowY,
                      renderedCount: Number(list.dataset.compareResultsCount || 0),
                    };
                    return metrics.scrollHeight > metrics.clientHeight ? metrics : null;
                    """)
            )
            assert 12 <= len(left_options) <= 40
            assert list_metrics["renderedCount"] == len(left_options)
            assert list_metrics["overflowY"] == "auto"
            assert list_metrics["scrollHeight"] > list_metrics["clientHeight"]

            selection = driver.execute_script("""
                const list = document.querySelector("#compare-left-results");
                const previousScrollBehavior = list.style.scrollBehavior;
                list.style.scrollBehavior = "auto";
                list.scrollTop = list.scrollHeight;
                const options = list.querySelectorAll('[data-compare-profile-option="true"]');
                const option = options[options.length - 1];
                const name = option.querySelector("[data-compare-profile-name]").textContent.trim();
                option.click();
                const scrollTop = list.scrollTop;
                list.style.scrollBehavior = previousScrollBehavior;
                return { name, scrollTop };
                """)
            assert selection["scrollTop"] > 0
            selected_left_name = selection["name"]
            wait.until(
                lambda current_driver: (
                    selected_left_name
                    in current_driver.find_element(by.By.ID, "compare-left-profile").text
                )
            )

            right_search = wait.until(
                ec.presence_of_element_located((by.By.ID, "compare-right-search"))
            )
            right_search.clear()
            right_search.send_keys(right_name)
            _click_css_when_ready(
                driver,
                wait,
                by,
                (f'[data-compare-result-side="right"][data-compare-profile-id="{right_id}"]'),
            )
            wait.until(
                lambda current_driver: (
                    right_name
                    in current_driver.find_element(by.By.ID, "compare-right-profile").text
                )
            )
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "#compare-settings-rows tr[data-compare-row-id]"
                        )
                    )
                    >= 1
                )
            )
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_compare_table_setting_cells_do_not_duplicate_identifiers():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    left_name = "Compare Labels Browser Smoke Left"
    right_name = "Compare Labels Browser Smoke Right"
    preference_name = "browser.startup.homepage"

    with run_test_app_server() as base_url:
        left_id = _create_profile(
            base_url,
            name=left_name,
            flags={
                "DisableTelemetry": True,
                "Homepage": {"URL": "https://labels-left.example.local/", "Locked": True},
                "Preferences": {
                    preference_name: {
                        "Status": "locked",
                        "Value": "https://labels-left.example.local/",
                    },
                },
            },
        )
        right_id = _create_profile(
            base_url,
            name=right_name,
            flags={
                "DisableTelemetry": False,
                "Homepage": {"URL": "https://labels-right.example.local/", "Locked": True},
                "Preferences": {
                    preference_name: {
                        "Status": "locked",
                        "Value": "https://labels-right.example.local/",
                    },
                },
            },
        )

        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/compare?left={left_id}&right={right_id}")
            wait.until(ec.presence_of_element_located((by.By.ID, "compare-page")))
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "#compare-settings-rows tr[data-compare-row-id]"
                        )
                    )
                    >= 3
                )
            )

            setting_cells = driver.find_elements(by.By.CSS_SELECTOR, ".compare-setting-cell")
            assert setting_cells
            rendered_rows = {
                cell.find_element(by.By.CSS_SELECTOR, "[data-compare-setting-label]").text: {
                    "text": cell.text,
                    "keys": [
                        element.text
                        for element in cell.find_elements(
                            by.By.CSS_SELECTOR,
                            "[data-compare-setting-key]",
                        )
                    ],
                }
                for cell in setting_cells
            }

            assert "DisableTelemetry" in rendered_rows
            assert rendered_rows["DisableTelemetry"]["keys"] == []
            assert rendered_rows["DisableTelemetry"]["text"].split().count("DisableTelemetry") == 1

            preference_rows = [
                row
                for label, row in rendered_rows.items()
                if preference_name in label or preference_name in " ".join(row["keys"])
            ]
            assert len(preference_rows) == 1
            preference_row = preference_rows[0]
            assert preference_row["keys"] == [f"Preferences.{preference_name}"]
            assert preference_row["text"].split().count(preference_name) <= 1
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_library_clone_name_actions_stay_inside_panel_in_russian():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    ru = _load_locale_catalog("ru")

    source_name = "Clone Layout Browser Smoke Source"

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name=source_name)
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.set_window_size(920, 1100)
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            wait.until(lambda current_driver: source_name in _body_text(current_driver))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])

            _click_css_when_ready(
                driver,
                wait,
                by,
                f'[data-clone-profile-id="{profile_id}"]',
            )
            clone_panel = wait.until(
                ec.visibility_of_element_located(
                    (by.By.ID, f"library-clone-name-panel-{profile_id}")
                )
            )
            wait.until(lambda _driver: ru["profiles.clone_name_confirm"] in clone_panel.text)

            layout_metrics = driver.execute_script(
                """
                const panel = arguments[0];
                const actions = panel.querySelector('.library-clone-name-actions');
                const buttons = [
                  panel.querySelector('[data-clone-name-confirm]'),
                  panel.querySelector('[data-clone-name-cancel]'),
                ].filter(Boolean);
                const panelRect = panel.getBoundingClientRect();
                const actionRect = actions.getBoundingClientRect();
                return {
                  panelClientWidth: panel.clientWidth,
                  panelScrollWidth: panel.scrollWidth,
                  actionsClientWidth: actions.clientWidth,
                  actionsScrollWidth: actions.scrollWidth,
                  actionWithinPanel:
                    actionRect.left >= panelRect.left - 1 &&
                    actionRect.right <= panelRect.right + 1,
                  buttonMetrics: buttons.map((button) => {
                    const rect = button.getBoundingClientRect();
                    const styles = window.getComputedStyle(button);
                    return {
                      text: button.innerText.trim(),
                      left: rect.left,
                      right: rect.right,
                      width: rect.width,
                      whiteSpace: styles.whiteSpace,
                      withinPanel:
                        rect.left >= panelRect.left - 1 &&
                        rect.right <= panelRect.right + 1,
                    };
                  }),
                };
                """,
                clone_panel,
            )

            assert layout_metrics["panelScrollWidth"] <= layout_metrics["panelClientWidth"] + 1
            assert layout_metrics["actionsScrollWidth"] <= layout_metrics["actionsClientWidth"] + 1
            assert layout_metrics["actionWithinPanel"] is True
            assert [item["text"] for item in layout_metrics["buttonMetrics"]] == [
                ru["profiles.clone_name_confirm"],
                ru["profiles.clone_name_cancel"],
            ]
            assert all(item["withinPanel"] for item in layout_metrics["buttonMetrics"])
            assert all(item["whiteSpace"] == "normal" for item in layout_metrics["buttonMetrics"])
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)


def test_browser_smoke_library_edit_and_named_clone_draft_open_new_tabs():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    source_name = "Clone Browser Smoke Source"
    clone_name = "Clone Browser Smoke Custom Name"

    with run_test_app_server() as base_url:
        profile_id = _create_profile(base_url, name=source_name)
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            library_handle = driver.current_window_handle
            profile_link = wait.until(ec.element_to_be_clickable((by.By.LINK_TEXT, source_name)))
            assert profile_link.get_attribute("target") == "_blank"
            assert profile_link.get_attribute("rel") == "noopener"

            edit_handle = _click_and_switch_to_new_tab(driver, wait, profile_link)
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            assert urlparse(driver.current_url).path == f"/profiles/{profile_id}/edit"
            assert (
                driver.find_element(by.By.ID, "profile-name").get_attribute("value") == source_name
            )
            driver.close()
            driver.switch_to.window(library_handle)
            wait.until(lambda current_driver: edit_handle not in current_driver.window_handles)

            clone_button = wait.until(
                ec.element_to_be_clickable(
                    (by.By.CSS_SELECTOR, f'[data-clone-profile-id="{profile_id}"]')
                )
            )
            _click_element(driver, clone_button)
            clone_panel = wait.until(
                ec.visibility_of_element_located(
                    (by.By.ID, f"library-clone-name-panel-{profile_id}")
                )
            )
            clone_input = clone_panel.find_element(by.By.CSS_SELECTOR, "[data-clone-name-input]")
            clone_input.clear()
            clone_input.send_keys(clone_name)
            confirm = clone_panel.find_element(by.By.CSS_SELECTOR, "[data-clone-name-confirm]")
            wait.until(lambda _driver: confirm.get_attribute("aria-disabled") == "false")
            assert confirm.get_attribute("target") == "_blank"
            assert confirm.get_attribute("rel") == "noopener"

            _click_and_switch_to_new_tab(driver, wait, confirm)
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-panel")))
            assert urlparse(driver.current_url).path == "/profiles/new"
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(by.By.ID, "profile-name").get_attribute("value")
                    == clone_name
                )
            )
            assert driver.find_element(by.By.TAG_NAME, "body").get_attribute(
                "data-clone-source-id"
            ) == str(profile_id)
            _assert_document_fits(driver)
        finally:
            _close_chromium_driver(driver)
