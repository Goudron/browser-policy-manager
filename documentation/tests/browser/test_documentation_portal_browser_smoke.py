from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from app.core.config import get_settings
from tests.support import run_test_app_server
from tests.test_documentation_runtime_route import _write_packaged_site
from tests.test_ui_browser_tabs import (
    _assert_document_fits,
    _body_text,
    _build_chromium_driver,
    _click_and_switch_to_new_tab,
    _close_chromium_driver,
    _create_profile,
    _load_locale_catalog,
    _set_locale,
)

pytestmark = [pytest.mark.browser_ui, pytest.mark.slow]

DOCUMENTATION_LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def _augment_packaged_site_for_browser_smoke(root: Path) -> None:
    for locale in DOCUMENTATION_LOCALES:
        locale_root = root / locale
        asset_dir = locale_root / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / "docs-smoke-screenshot.svg").write_text(
            (
                "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"180\" "
                "viewBox=\"0 0 320 180\" role=\"img\" aria-label=\"Documentation smoke asset\">"
                "<rect width=\"320\" height=\"180\" fill=\"#0f172a\"/>"
                "<text x=\"24\" y=\"96\" fill=\"#e2e8f0\" font-size=\"24\">BPM docs smoke</text>"
                "</svg>"
            ),
            encoding="utf-8",
        )
        index_path = locale_root / "index.html"
        index_html = index_path.read_text(encoding="utf-8")
        index_path.write_text(
            index_html.replace(
                "</main>",
                (
                    "<form role=\"search\" aria-label=\"Documentation search\">"
                    "<label>Search documentation"
                    "<input type=\"search\" name=\"q\" value=\"profile\"></label>"
                    "</form>"
                    "<img class=\"docs-smoke-screenshot\" src=\"assets/docs-smoke-screenshot.svg\" "
                    f"alt=\"Documentation smoke asset {locale}\">"
                    "</main>"
                ),
            ),
            encoding="utf-8",
        )

        search_dir = root / "search" / locale
        search_dir.mkdir(parents=True, exist_ok=True)
        (search_dir / "index.json").write_text(
            json.dumps(
                {
                    "locale": locale,
                    "documents": [
                        {
                            "title": f"Profile Library {locale}",
                            "url": f"/help/{locale}/user/ug-task-use-profile-library.html",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


@contextmanager
def _documentation_test_server(site_root: Path) -> Iterator[str]:
    previous_site_dir = os.environ.get("BPM_DOCUMENTATION_SITE_DIR")
    os.environ["BPM_DOCUMENTATION_SITE_DIR"] = str(site_root)
    get_settings.cache_clear()
    try:
        with run_test_app_server() as base_url:
            yield base_url
    finally:
        if previous_site_dir is None:
            os.environ.pop("BPM_DOCUMENTATION_SITE_DIR", None)
        else:
            os.environ["BPM_DOCUMENTATION_SITE_DIR"] = previous_site_dir
        get_settings.cache_clear()


def _fetch_statuses(driver, urls: list[str]) -> list[dict[str, str | int]]:
    driver.set_script_timeout(20)
    return driver.execute_async_script(
        """
        const urls = arguments[0];
        const done = arguments[arguments.length - 1];
        Promise.all(urls.map(async (url) => {
          const response = await fetch(url, { cache: "no-store" });
          return {
            url,
            status: response.status,
            contentType: response.headers.get("content-type") || "",
          };
        })).then(done).catch((error) => done([{ error: String(error) }]));
        """,
        urls,
    )


def _close_current_tab_and_return(driver, handle: str) -> None:
    driver.close()
    driver.switch_to.window(handle)


def test_documentation_header_link_opens_packaged_portal_for_all_locales(tmp_path: Path) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale_catalogs = {locale: _load_locale_catalog(locale) for locale in DOCUMENTATION_LOCALES}
    _write_packaged_site(tmp_path)
    _augment_packaged_site_for_browser_smoke(tmp_path)

    with _documentation_test_server(tmp_path) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            main_handle = driver.current_window_handle

            for locale in DOCUMENTATION_LOCALES:
                catalog = locale_catalogs[locale]
                _set_locale(driver, wait, ui, locale=locale, expected_text=catalog["profiles.locale_hint"])
                docs_link = wait.until(
                    ec.element_to_be_clickable((by.By.CSS_SELECTOR, ".compact-toolbar-docs-link"))
                )
                assert docs_link.get_attribute("href") == f"{base_url}/help/{locale}/index.html"

                _click_and_switch_to_new_tab(driver, wait, docs_link)
                wait.until(
                    lambda current_driver, expected_locale=locale: current_driver.current_url.endswith(
                        f"/help/{expected_locale}/index.html"
                    )
                )
                wait.until(
                    lambda current_driver, expected_locale=locale: current_driver.execute_script(
                        "return document.documentElement.lang;"
                    )
                    == expected_locale
                )
                assert f"Docs {locale}" in _body_text(driver)
                assert driver.find_element(by.By.CSS_SELECTOR, "form[role='search'] input[type='search']")
                assert driver.find_element(by.By.CSS_SELECTOR, "img.docs-smoke-screenshot")

                statuses = _fetch_statuses(
                    driver,
                    [
                        f"{base_url}/help/{locale}/assets/bpm-docs.css",
                        f"{base_url}/help/{locale}/assets/docs-smoke-screenshot.svg",
                        f"{base_url}/help/search/{locale}/index.json",
                    ],
                )
                assert statuses == [
                    {
                        "url": f"{base_url}/help/{locale}/assets/bpm-docs.css",
                        "status": 200,
                        "contentType": "text/css; charset=utf-8",
                    },
                    {
                        "url": f"{base_url}/help/{locale}/assets/docs-smoke-screenshot.svg",
                        "status": 200,
                        "contentType": "image/svg+xml",
                    },
                    {
                        "url": f"{base_url}/help/search/{locale}/index.json",
                        "status": 200,
                        "contentType": "application/json; charset=utf-8",
                    },
                ]

                driver.set_window_size(390, 900)
                _assert_document_fits(driver)
                driver.set_window_size(1366, 1200)
                _close_current_tab_and_return(driver, main_handle)
        finally:
            _close_chromium_driver(driver)


def test_documentation_contextual_links_deep_links_and_openapi_docs_survive_browser_flow(
    tmp_path: Path,
) -> None:
    action_chains = pytest.importorskip("selenium.webdriver.common.action_chains")
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    ru = _load_locale_catalog("ru")
    _write_packaged_site(tmp_path)
    _augment_packaged_site_for_browser_smoke(tmp_path)

    with _documentation_test_server(tmp_path) as base_url:
        profile_id = _create_profile(base_url, name="Documentation Browser Smoke")
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        main_handle = ""
        try:
            contextual_routes = {
                "/profiles": ("library", "ug-task-use-profile-library"),
                "/profiles/compare": ("compare", "ug-task-compare-profiles"),
                "/profiles/new": ("guided", "ug-task-use-guided-editor"),
                f"/profiles/{profile_id}/settings": ("settings", "ug-task-use-all-settings"),
                f"/profiles/{profile_id}/json": ("json", "ug-task-use-json-editor"),
            }

            for route, (surface, topic_id) in contextual_routes.items():
                driver.get(f"{base_url}{route}")
                wait.until(ec.presence_of_element_located((by.By.ID, "lang")))
                _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_hint"])
                main_handle = driver.current_window_handle
                link = wait.until(
                    ec.element_to_be_clickable(
                        (
                            by.By.CSS_SELECTOR,
                            f".context-help-link[data-context-help-surface='{surface}']",
                        )
                    )
                )
                assert link.get_attribute("href") == f"{base_url}/help/ru/user/{topic_id}.html"
                assert link.get_attribute("target") == "_blank"
                _click_and_switch_to_new_tab(driver, wait, link)
                wait.until(
                    lambda current_driver, expected_topic_id=topic_id: current_driver.current_url.endswith(
                        f"/{expected_topic_id}.html"
                    )
                )
                assert topic_id in _body_text(driver)
                _close_current_tab_and_return(driver, main_handle)

            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "lang")))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_hint"])
            main_handle = driver.current_window_handle
            icon_link = wait.until(
                ec.element_to_be_clickable(
                    (
                        by.By.CSS_SELECTOR,
                        ".context-help-icon-link[data-context-help-target='import-firefox-policies']",
                    )
                )
            )
            action_chains.ActionChains(driver).move_to_element(icon_link).perform()
            assert icon_link.text.strip() == "i"
            assert icon_link.get_attribute("title")
            assert icon_link.get_attribute("href").endswith(
                "/help/ru/user/ug-task-import-policies-json.html"
            )
            _click_and_switch_to_new_tab(driver, wait, icon_link)
            wait.until(
                lambda current_driver: "ug-task-import-policies-json.html"
                in current_driver.current_url
            )
            _close_current_tab_and_return(driver, main_handle)

            driver.get(f"{base_url}/docs")
            wait.until(
                lambda current_driver: "Swagger UI"
                in current_driver.execute_script("return document.title || '';")
            )
            assert driver.current_url.endswith("/docs")
        finally:
            _close_chromium_driver(driver)
