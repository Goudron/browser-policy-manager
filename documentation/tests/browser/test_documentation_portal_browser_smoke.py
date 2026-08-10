from __future__ import annotations

import html
import importlib.util
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from app.core.config import get_settings
from app.models.profile import Profile
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
    configured_environment,
)
from tests.browser.profiles.pages import create_profile as _create_profile
from tests.browser.profiles.pages import load_locale_catalog as _load_locale_catalog
from tests.browser.profiles.pages import set_locale as _set_locale
from tests.contract.docs.general.test_documentation_runtime_route import _write_packaged_site
from tests.support import run_test_app_server, run_test_app_server_handle

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.slow,
    pytest.mark.usefixtures("browser_test_context"),
]

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
BUILD_DOCS_SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS_PATH)
assert BUILD_DOCS_SPEC and BUILD_DOCS_SPEC.loader
build_docs = importlib.util.module_from_spec(BUILD_DOCS_SPEC)
BUILD_DOCS_SPEC.loader.exec_module(build_docs)

DOCUMENTATION_LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LANGUAGE_BROWSER_QA = json.loads(
    (
        DOCUMENTATION_ROOT / "config/documentation-navigation-language-browser-qa-0.9.1.json"
    ).read_text(encoding="utf-8")
)


def _augment_packaged_site_for_browser_smoke(root: Path) -> None:
    for locale in DOCUMENTATION_LOCALES:
        locale_root = root / locale
        asset_dir = locale_root / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / "docs-smoke-screenshot.svg").write_text(
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" '
                'viewBox="0 0 320 180" role="img" aria-label="Documentation smoke asset">'
                '<rect width="320" height="180" fill="#0f172a"/>'
                '<text x="24" y="96" fill="#e2e8f0" font-size="24">BPM docs smoke</text>'
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
                    '<form role="search" aria-label="Documentation search">'
                    "<label>Search documentation"
                    '<input type="search" name="q" value="profile"></label>'
                    "</form>"
                    '<img class="docs-smoke-screenshot" src="assets/docs-smoke-screenshot.svg" '
                    f'alt="Documentation smoke asset {locale}">'
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
    with configured_environment({"BPM_DOCUMENTATION_SITE_DIR": site_root}):
        get_settings.cache_clear()
        try:
            with run_test_app_server() as base_url:
                yield base_url
        finally:
            get_settings.cache_clear()


@contextmanager
def _documentation_test_server_handle(site_root: Path) -> Iterator[Any]:
    with configured_environment({"BPM_DOCUMENTATION_SITE_DIR": site_root}):
        get_settings.cache_clear()
        try:
            with run_test_app_server_handle() as handle:
                yield handle
        finally:
            get_settings.cache_clear()


def _write_generated_theme_smoke_site(root: Path) -> None:
    _write_packaged_site(root)
    language_sample = LANGUAGE_BROWSER_QA["language_sample"]
    localized_keydefs = {
        locale: build_docs._localized_map_keydefs(locale) for locale in DOCUMENTATION_LOCALES
    }
    search_facets = build_docs._search_facets_filters()
    first_user_topic_id = build_docs._navigation_topic_order("user-guide.ditamap")[0]
    for locale in DOCUMENTATION_LOCALES:
        locale_root = root / locale
        guide_anchors = "".join(
            f'<section id="{anchor}"><h2>{build_docs._map_title(locale, filename)}</h2></section>'
            for _guide_id, filename, anchor, _url_root in build_docs.GUIDE_MAPS
        )
        body = (
            f"<h1>Theme smoke {locale}</h1>"
            "<p>Generated portal shell theme verification covers search, navigation, "
            "tables, code, notes, and responsive controls.</p>"
            '<pre><code>{"policy": true}</code></pre>'
            '<table><caption>Theme data</caption><tr><th scope="col">Name</th>'
            "<td>Browser Policy Manager</td></tr></table>"
            '<div class="note">Theme smoke note</div>'
            f"{guide_anchors}"
        )
        (locale_root / "index.html").write_text(
            f'<!doctype html><html lang="{locale}"><head><title>{locale}</title></head>'
            f"<body>{body}</body></html>",
            encoding="utf-8",
        )
        for _guide_id, filename, _anchor, _url_root in build_docs.GUIDE_MAPS:
            for keyref in build_docs._guide_topic_keyrefs("en", filename):
                topic_id = keyref.removeprefix("topic.")
                topic_path = localized_keydefs[locale][keyref]
                output = locale_root / topic_path.parent.name / f"{topic_id}.html"
                output.parent.mkdir(parents=True, exist_ok=True)
                if topic_id == language_sample["topic_id"]:
                    sample = language_sample["locales"][locale]
                    title = html.escape(sample["title"])
                    topic_body = (
                        f"<h1>{title}</h1>"
                        f'<p class="shortdesc">{html.escape(sample["shortdesc"])}</p>'
                        f"<p>{html.escape(sample['first_paragraph'])}</p>"
                    )
                else:
                    title = html.escape(topic_id)
                    topic_body = f"<h1>{title}</h1><p>{title} {html.escape(locale)}</p>"
                output.write_text(
                    f'<!doctype html><html lang="{locale}"><head><title>{title}</title></head>'
                    f"<body>{topic_body}</body></html>",
                    encoding="utf-8",
                )

        search_dir = root / "search" / locale
        search_dir.mkdir(parents=True, exist_ok=True)
        localized_facets = build_docs._localized_search_facet_fields(locale, search_facets)
        (search_dir / "index.json").write_text(
            json.dumps(
                {
                    "locale": locale,
                    "documents": [
                        {
                            "title": f"Theme smoke {locale}",
                            "url": f"/help/{locale}/user/{first_user_topic_id}.html",
                            "guide_id": "user-guide",
                            "topic_kind": "task",
                            "searchable": {
                                "title": f"Theme smoke {locale}",
                                "identifiers": [first_user_topic_id, "user-guide"],
                                "body": "theme search navigation responsive",
                            },
                            "filter_facets": {
                                "guide_id": ["user-guide"],
                                "topic_kind": ["task"],
                                "firefox_channel": ["release-152"],
                                "api_area": ["validation"],
                            },
                        }
                    ],
                    "filtering": {
                        "facet_fields": localized_facets,
                        "url_state": search_facets["url_state"],
                    },
                    "facet_counts": {
                        "guide_id": {"user-guide": 1},
                        "topic_kind": {"task": 1},
                        "firefox_channel": {"release-152": 1},
                        "api_area": {"validation": 1},
                    },
                }
            ),
            encoding="utf-8",
        )

    build_docs.apply_portal_shell(root)


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


def _theme_metrics(driver) -> dict[str, object]:
    return driver.execute_script("""
        const selectors = [
          ".bpm-docs-header",
          ".bpm-docs-sidebar",
          ".bpm-docs-main",
          ".bpm-docs-search",
          ".bpm-docs-search-input",
          ".bpm-docs-theme-control select",
        ];
        const backgrounds = selectors.map((selector) => {
          const node = document.querySelector(selector);
          return node ? getComputedStyle(node).backgroundColor : "";
        });
        const controls = Array.from(document.querySelectorAll(
          ".bpm-docs-header-actions, .bpm-docs-locale-control, .bpm-docs-theme-control, .bpm-docs-search-row"
        )).map((node) => {
          const rect = node.getBoundingClientRect();
          return {
            selector: node.className,
            left: rect.left,
            right: rect.right,
            width: rect.width,
            scrollWidth: node.scrollWidth,
            clientWidth: node.clientWidth,
          };
        });
        return {
          lang: document.documentElement.lang,
          themeMode: document.documentElement.dataset.themeMode,
          theme: document.documentElement.dataset.theme,
          metaThemeColor: document.querySelector('meta[name="theme-color"]')?.content || "",
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
          backgrounds,
          controls,
        };
        """)


def _assert_theme_metrics_fit(metrics: dict[str, object]) -> None:
    assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics
    for control in metrics["controls"]:
        assert control["scrollWidth"] <= control["clientWidth"] + 1, (metrics, control)
        assert control["left"] >= -1, (metrics, control)
        assert control["right"] <= metrics["viewportWidth"] + 1, (metrics, control)


def _install_assistant_ready_browser_mock(driver, locale: str) -> None:
    driver.execute_script(
        """
        const locale = arguments[0];
        const api = '/api/documentation-assistant';
        window.__assistantQaCalls = [];
        window.__assistantQaRejectChat = false;
        window.__assistantQaEmitFinal = null;
        const response = (payload, status = 200) => new Response(JSON.stringify(payload), {
          status, headers: { 'Content-Type': 'application/json' },
        });
        window.fetch = async (input, init = {}) => {
          const path = String(input);
          window.__assistantQaCalls.push({ path, method: init.method || 'GET', body: init.body || '' });
          if (path === `${api}/status?locale=${encodeURIComponent(locale)}`) {
            return response({
              api_version: 1, state: 'ready', assistant_ready: true,
              lexical_search_ready: true, locale, message_key: 'assistant_ready',
              action_key: 'assistant_chat_send', reason_code: 'assistant_ready', state_epoch: 1,
            });
          }
          if (path === `${api}/chat`) {
            if (window.__assistantQaRejectChat) {
              return new Response(null, { status: 503 });
            }
            return response({
              api_version: 1, request_id: 'req_qa_example', state: 'accepted', state_epoch: 2,
              stream_path: `${api}/chat/req_qa_example/stream`,
              time_preview: { minimum_seconds: 5, maximum_seconds: 15 },
            }, 202);
          }
          if (path === `${api}/conversation`) {
            return new Response(null, { status: 204 });
          }
          return new Response(null, { status: 404 });
        };
        window.EventSource = class {
          constructor(url) {
            this.url = url;
            this.listeners = new Map();
            window.__assistantQaEmitFinal = () => {
              const final = this.listeners.get('final');
              if (final) {
                final({ data: JSON.stringify({
                  api_version: 1, request_id: 'req_qa_example', state: 'answer', state_epoch: 3,
                  reason_code: 'assistant_citations_validated', message_key: 'assistant_chat_answer',
                  action_key: '', disposition: 'answer', text: `Grounded ${locale} BPM answer.`, citations: [],
                }) });
              }
            };
          }
          addEventListener(name, listener) { this.listeners.set(name, listener); }
          close() {}
        };
        """,
        locale,
    )


def _install_assistant_failure_browser_mock(driver, locale: str) -> None:
    driver.execute_script(
        """
        const locale = arguments[0];
        const api = '/api/documentation-assistant';
        const modelApi = '/api/local-model';
        const csrf = 'c'.repeat(24);
        window.__assistantQaFailureCalls = [];
        const response = (payload, status = 200) => new Response(JSON.stringify(payload), {
          status, headers: { 'Content-Type': 'application/json' },
        });
        const operation = (state) => state === 'idle' ? { state } : {
          cancellable: false, downloaded_bytes: 0, kind: 'install',
          operation_id: 'operation_qa_failure', phase: state === 'failed' ? 'failed' : 'downloading',
          progress_percent: 0, reason_code: state === 'failed' ? 'artifact_hash_mismatch' : '',
          state, total_bytes: 0,
        };
        const modelStatus = () => ({
          api_version: 1, csrf_token: csrf, disclosure: {}, lexical_search_ready: true,
          verification: { state: 'not-installed', verified: false, reason_code: 'artifact_missing' },
          operation: operation('failed'),
        });
        window.fetch = async (input, init = {}) => {
          const path = String(input);
          window.__assistantQaFailureCalls.push({ path, method: init.method || 'GET', body: init.body || '' });
          if (path === `${api}/status?locale=${encodeURIComponent(locale)}`) {
            return response({
              api_version: 1, state: 'not-installed', assistant_ready: false,
              lexical_search_ready: true, locale, message_key: 'assistant_not_installed',
              action_key: 'assistant_manage_model', reason_code: 'assistant_unavailable', state_epoch: 1,
            });
          }
          if (path === `${modelApi}?locale=${encodeURIComponent(locale)}`) {
            return response(modelStatus());
          }
          if (path === `${modelApi}/install`) {
            return response({
              api_version: 1, csrf_token: csrf, accepted: true, operation: operation('running'),
            });
          }
          return new Response(null, { status: 404 });
        };
        """,
        locale,
    )


def _compact_search_metrics(driver) -> dict[str, object]:
    return driver.execute_script("""
        const row = document.querySelector(".bpm-docs-search-row");
        const panel = document.querySelector("[data-search-advanced-panel]");
        const toggle = document.querySelector("[data-search-advanced-toggle]");
        const input = document.querySelector("#bpm-docs-search-query");
        const activeFilters = document.querySelector("[data-search-active-filters]");
        const activeFiltersSummary = document.querySelector("[data-search-active-filters-summary]");
        const rowRect = row.getBoundingClientRect();
        return {
          panelHidden: panel.hidden,
          expanded: toggle.getAttribute("aria-expanded"),
          query: input.value,
          activeFiltersHidden: activeFilters.hidden,
          activeFiltersSummary: activeFiltersSummary.textContent,
          rowScrollWidth: row.scrollWidth,
          rowClientWidth: row.clientWidth,
          rowLeft: rowRect.left,
          rowRight: rowRect.right,
          viewportWidth: window.innerWidth,
        };
        """)


def _assert_compact_search_row_fits(metrics: dict[str, object]) -> None:
    assert metrics["rowScrollWidth"] <= metrics["rowClientWidth"] + 1, metrics
    assert metrics["rowLeft"] >= -1, metrics
    assert metrics["rowRight"] <= metrics["viewportWidth"] + 1, metrics


def _tree_state(driver) -> dict[str, object]:
    return driver.execute_script("""
        const current = document.querySelector("[data-docs-tree] [aria-current='page']");
        const active = document.activeElement;
        const guides = Array.from(document.querySelectorAll(
          "[data-docs-tree] [aria-level='2']"
        )).map((node) => ({
          node: node.dataset.treeNode,
          anchor: node.dataset.treeAnchor || "",
          expanded: node.getAttribute("aria-expanded"),
          hidden: document.getElementById(node.getAttribute("aria-controls"))?.hidden ?? null,
          text: node.textContent.trim(),
        }));
        const sections = Array.from(document.querySelectorAll(
          "[data-docs-tree] [data-section-label-key]"
        )).map((node) => ({
          node: node.dataset.treeNode,
          parent: node.dataset.treeParent,
          labelKey: node.dataset.sectionLabelKey,
          expanded: node.getAttribute("aria-expanded"),
          hidden: document.getElementById(node.getAttribute("aria-controls"))?.hidden ?? null,
          text: node.textContent.trim(),
        }));
        return {
          currentNode: current?.dataset.treeNode || "",
          currentText: current?.textContent.trim() || "",
          activeNode: active?.dataset?.treeNode || "",
          rootText: document.querySelector("[data-tree-node='documentation-root']")?.textContent.trim() || "",
          guideCount: guides.length,
          guides,
          sections,
          tabStops: Array.from(document.querySelectorAll(
            "[data-docs-tree] [role='treeitem'][tabindex='0']"
          )).map((node) => node.dataset.treeNode),
          breadcrumbs: Array.from(document.querySelectorAll(
            ".bpm-docs-breadcrumbs li"
          )).map((node) => node.textContent.trim()),
        };
        """)


def _sidebar_scroll_state(driver) -> dict[str, object]:
    return driver.execute_script("""
        const sidebar = document.querySelector('.bpm-docs-sidebar');
        const active = document.activeElement;
        const sidebarRect = sidebar.getBoundingClientRect();
        const activeRect = active?.getBoundingClientRect();
        return {
          clientHeight: sidebar.clientHeight,
          scrollHeight: sidebar.scrollHeight,
          clientWidth: sidebar.clientWidth,
          scrollWidth: sidebar.scrollWidth,
          scrollTop: sidebar.scrollTop,
          overflowY: getComputedStyle(sidebar).overflowY,
          overflowX: getComputedStyle(sidebar).overflowX,
          maxBlockSize: getComputedStyle(sidebar).maxBlockSize,
          position: getComputedStyle(sidebar).position,
          windowScrollY: window.scrollY,
          activeNode: active?.dataset?.treeNode || '',
          activeTop: activeRect?.top ?? null,
          activeBottom: activeRect?.bottom ?? null,
          sidebarTop: sidebarRect.top,
          sidebarBottom: sidebarRect.bottom,
        };
        """)


def _tree_collection_node(state: dict[str, Any], collection: str, node_id: str) -> dict[str, Any]:
    return next(node for node in state[collection] if node["node"] == node_id)


@pytest.fixture(scope="session")
def generated_theme_smoke_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("generated-theme-smoke-site")
    _write_generated_theme_smoke_site(root)
    return root


def test_documentation_generated_theme_modes_render_for_all_locales_and_viewports(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        driver.set_window_size(1366, 1000)
        try:
            for locale in DOCUMENTATION_LOCALES:
                driver.get(f"{base_url}/help/{locale}/index.html")
                theme_select = ui.Select(
                    driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                )
                assert [option.get_attribute("value") for option in theme_select.options] == [
                    "system",
                    "light",
                    "dark",
                ]
                compact_metrics = _compact_search_metrics(driver)
                assert compact_metrics["panelHidden"] is True
                assert compact_metrics["expanded"] == "false"
                _assert_compact_search_row_fits(compact_metrics)

                search_input = driver.find_element(by.By.CSS_SELECTOR, "#bpm-docs-search-query")
                search_input.clear()
                search_input.send_keys("theme")
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-advanced-toggle]"),
                )
                expanded_metrics = _compact_search_metrics(driver)
                assert expanded_metrics["panelHidden"] is False
                assert expanded_metrics["expanded"] == "true"
                assert expanded_metrics["query"] == "theme"
                first_filter = driver.find_element(by.By.CSS_SELECTOR, "[data-search-filter]")
                first_filter.send_keys(keys.Keys.ESCAPE)
                escaped_metrics = _compact_search_metrics(driver)
                assert escaped_metrics["panelHidden"] is True
                assert escaped_metrics["expanded"] == "false"
                assert escaped_metrics["query"] == "theme"
                assert (
                    driver.switch_to.active_element.get_attribute("data-search-advanced-toggle")
                    == ""
                )
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-advanced-toggle]"),
                )
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-advanced-toggle]"),
                )
                collapsed_metrics = _compact_search_metrics(driver)
                assert collapsed_metrics["panelHidden"] is True
                assert collapsed_metrics["expanded"] == "false"
                assert collapsed_metrics["query"] == "theme"
                search_input.send_keys(keys.Keys.ENTER)
                entered_metrics = _compact_search_metrics(driver)
                assert entered_metrics["panelHidden"] is True
                assert entered_metrics["expanded"] == "false"
                assert entered_metrics["query"] == "theme"
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-submit]"),
                )
                submitted_metrics = _compact_search_metrics(driver)
                assert submitted_metrics["panelHidden"] is True
                assert submitted_metrics["expanded"] == "false"
                assert submitted_metrics["query"] == "theme"
                driver.execute_script("document.querySelector('[data-search-filter]')?.click();")
                filtered_metrics = _compact_search_metrics(driver)
                assert filtered_metrics["panelHidden"] is True
                assert filtered_metrics["expanded"] == "false"
                assert filtered_metrics["activeFiltersHidden"] is False
                assert filtered_metrics["activeFiltersSummary"]
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-clear-filters]"),
                )
                cleared_filters_metrics = _compact_search_metrics(driver)
                assert cleared_filters_metrics["panelHidden"] is True
                assert cleared_filters_metrics["activeFiltersHidden"] is True
                assert cleared_filters_metrics["query"] == "theme"
                driver.refresh()
                ui.WebDriverWait(driver, 10).until(
                    lambda current_driver: (
                        _compact_search_metrics(current_driver)["query"] == "theme"
                    )
                )
                restored_metrics = _compact_search_metrics(driver)
                assert restored_metrics["panelHidden"] is True
                assert restored_metrics["expanded"] == "false"
                assert restored_metrics["query"] == "theme"
                driver.get(f"{base_url}/help/{locale}/index.html?guide=user-guide")
                ui.WebDriverWait(driver, 10).until(
                    lambda current_driver: current_driver.find_elements(
                        by.By.CSS_SELECTOR, "[data-search-filter]:checked"
                    )
                )
                hydrated_metrics = _compact_search_metrics(driver)
                assert hydrated_metrics["panelHidden"] is True
                assert hydrated_metrics["expanded"] == "false"
                assert hydrated_metrics["activeFiltersHidden"] is False
                assert hydrated_metrics["activeFiltersSummary"]
                driver.execute_script(
                    "window.history.pushState(null, '', '?q=theme&guide=user-guide');"
                    "window.dispatchEvent(new PopStateEvent('popstate'));"
                )
                ui.WebDriverWait(driver, 10).until(
                    lambda current_driver: (
                        _compact_search_metrics(current_driver)["query"] == "theme"
                        and bool(
                            current_driver.find_elements(
                                by.By.CSS_SELECTOR, "[data-search-filter]:checked"
                            )
                        )
                    )
                )
                popstate_metrics = _compact_search_metrics(driver)
                assert popstate_metrics["panelHidden"] is True
                assert popstate_metrics["expanded"] == "false"
                assert popstate_metrics["activeFiltersHidden"] is False

                for width, height in ((1366, 1000), (390, 900)):
                    driver.set_window_size(width, height)
                    for mode in ("light", "dark"):
                        theme_select = ui.Select(
                            driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                        )
                        theme_select.select_by_value(mode)
                        metrics = _theme_metrics(driver)
                        assert metrics["lang"] == locale
                        assert metrics["themeMode"] == mode
                        assert metrics["theme"] == mode
                        assert metrics["metaThemeColor"] == (
                            "#07111a" if mode == "dark" else "#edf2f7"
                        )
                        _assert_theme_metrics_fit(metrics)
                        if mode == "light":
                            assert "rgb(255, 255, 255)" not in metrics["backgrounds"], metrics

                    driver.execute_cdp_cmd(
                        "Emulation.setEmulatedMedia",
                        {"features": [{"name": "prefers-color-scheme", "value": "dark"}]},
                    )
                    theme_select = ui.Select(
                        driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                    )
                    theme_select.select_by_value("system")
                    dark_system = _theme_metrics(driver)
                    assert dark_system["themeMode"] == "system"
                    assert dark_system["theme"] == "dark"
                    _assert_theme_metrics_fit(dark_system)

                    driver.execute_cdp_cmd(
                        "Emulation.setEmulatedMedia",
                        {"features": [{"name": "prefers-color-scheme", "value": "light"}]},
                    )
                    theme_select = ui.Select(
                        driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                    )
                    theme_select.select_by_value("dark")
                    theme_select.select_by_value("system")
                    light_system = _theme_metrics(driver)
                    assert light_system["themeMode"] == "system"
                    assert light_system["theme"] == "light"
                    assert "rgb(255, 255, 255)" not in light_system["backgrounds"], light_system
                    _assert_theme_metrics_fit(light_system)
                    driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})
        finally:
            _close_chromium_driver(driver)


def test_documentation_floating_assistant_shell_is_bounded_and_keyboard_operable(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    def metrics(current_driver) -> dict[str, object]:
        return current_driver.execute_script("""
            const widget = document.querySelector('[data-documentation-assistant-widget]');
            const panel = document.querySelector('[data-assistant-panel]');
            const toggle = document.querySelector('[data-assistant-toggle]');
            const panelRect = panel.getBoundingClientRect();
            return {
              expanded: widget.dataset.assistantExpanded,
              panelHidden: panel.hidden,
              ariaExpanded: toggle.getAttribute('aria-expanded'),
              viewportWidth: window.innerWidth,
              viewportHeight: window.innerHeight,
              panelWidth: panelRect.width,
              panelHeight: panelRect.height,
              panelRight: panelRect.right,
              panelBottom: panelRect.bottom,
              transcriptOverflow: getComputedStyle(document.querySelector('[data-assistant-transcript]')).overflowY,
              panelBackground: getComputedStyle(panel).backgroundColor,
            };
            """)

    def assistant_requests(current_driver) -> list[str]:
        return current_driver.execute_script("""
            return performance.getEntriesByType('resource')
              .map((entry) => entry.name)
              .filter((name) => name.includes('/api/documentation-assistant'));
            """)

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 10)
        try:
            for width, height, locale, title in (
                (1366, 1000, "ru", "ИИ-помощник BPM"),
                (390, 900, "en", "BPM AI Assistant"),
            ):
                driver.set_window_size(width, height)
                driver.get(f"{base_url}/help/{locale}/index.html")
                toggle = wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.CSS_SELECTOR, "[data-assistant-toggle]"
                    )
                )
                assert toggle.text == title
                initial = metrics(driver)
                assert initial["panelHidden"] is True
                assert initial["expanded"] == "false"
                assert initial["ariaExpanded"] == "false"
                assert assistant_requests(driver) == []

                toggle.click()
                wait.until(lambda current_driver: metrics(current_driver)["panelHidden"] is False)
                wait.until(
                    lambda current_driver, expected_locale=locale: any(
                        name.endswith(
                            f"/api/documentation-assistant/status?locale={expected_locale}"
                        )
                        for name in assistant_requests(current_driver)
                    )
                )
                assert all(
                    "/api/documentation-assistant/status?locale=" in name
                    for name in assistant_requests(driver)
                )
                expanded = metrics(driver)
                assert expanded["expanded"] == "true"
                assert expanded["ariaExpanded"] == "true"
                if width >= 768:
                    assert expanded["panelHeight"] >= expanded["viewportHeight"] * 0.9 - 2
                    assert expanded["panelHeight"] <= expanded["viewportHeight"] * 0.9 + 2
                else:
                    assert expanded["panelHeight"] <= expanded["viewportHeight"] * 0.5 + 2
                assert expanded["panelRight"] <= expanded["viewportWidth"] + 1
                assert expanded["panelBottom"] <= expanded["viewportHeight"] + 1
                assert expanded["transcriptOverflow"] == "auto"
                if width >= 768:
                    assert expanded["panelWidth"] >= expanded["viewportWidth"] * 0.5 - 2
                    assert expanded["panelWidth"] <= expanded["viewportWidth"] * 0.5 + 2
                else:
                    assert expanded["panelWidth"] >= expanded["viewportWidth"] - 34

                if locale == "ru":
                    persisted = driver.execute_script(
                        """
                        const widget = document.querySelector('[data-documentation-assistant-widget]');
                        return window.BPMDocumentationAssistantConversation.recordCompletedTurn(widget, arguments[0]);
                        """,
                        {
                            "user": "Покажите <img> безопасно",
                            "assistant": "Текст без HTML <script>.",
                        },
                    )
                    assert persisted is True
                    driver.refresh()
                    wait.until(
                        lambda current_driver: metrics(current_driver)["panelHidden"] is False
                    )
                    assert assistant_requests(driver) == []
                    restored = driver.execute_script("""
                        const transcript = document.querySelector('[data-assistant-transcript]');
                        return {
                          text: transcript.textContent,
                          messages: transcript.querySelectorAll('[data-assistant-message-role]').length,
                          unsafeNodes: transcript.querySelectorAll('img, script').length,
                        };
                        """)
                    assert restored == {
                        "text": "Покажите <img> безопасноТекст без HTML <script>.",
                        "messages": 2,
                        "unsafeNodes": 0,
                    }
                    first_user_topic = build_docs._navigation_topic_order("user-guide.ditamap")[0]
                    driver.get(f"{base_url}/help/{locale}/user/{first_user_topic}.html")
                    wait.until(
                        lambda current_driver: metrics(current_driver)["panelHidden"] is False
                    )
                    assert (
                        driver.execute_script(
                            "return document.querySelector('[data-assistant-transcript]').textContent;"
                        )
                        == "Покажите <img> безопасноТекст без HTML <script>."
                    )
                    assert (
                        driver.execute_script("""
                        return window.BPMDocumentationAssistantConversation.setReady(
                          document.querySelector('[data-documentation-assistant-widget]'), true
                        );
                        """)
                        is True
                    )
                    clear = driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-clear]")
                    assert clear.is_displayed()
                    clear.click()
                    wait.until(
                        lambda current_driver: (
                            current_driver.execute_script(
                                "return document.querySelectorAll('[data-assistant-message-role]').length;"
                            )
                            == 0
                        )
                    )

                driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").send_keys(
                    keys.Keys.ESCAPE
                )
                wait.until(lambda current_driver: metrics(current_driver)["panelHidden"] is True)
                assert driver.switch_to.active_element.get_attribute("data-assistant-toggle") == ""

            driver.set_window_size(1366, 1000)
            driver.get(f"{base_url}/help/en/index.html")
            driver.execute_script("""
                window.__assistantTransportCalls = [];
                window.fetch = async (input, init = {}) => {
                  const path = String(input);
                  window.__assistantTransportCalls.push({ path, method: init.method || 'GET', body: init.body || '' });
                  if (path === '/api/documentation-assistant/status?locale=en') {
                    return new Response(JSON.stringify({
                      api_version: 1, state: 'ready', assistant_ready: true,
                      lexical_search_ready: true, locale: 'en', message_key: 'assistant_ready',
                      action_key: 'assistant_chat_send', reason_code: 'assistant_ready', state_epoch: 1,
                    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                  }
                  if (path === '/api/documentation-assistant/chat') {
                    return new Response(JSON.stringify({
                      api_version: 1, request_id: 'req_example', state: 'accepted', state_epoch: 1,
                      stream_path: '/api/documentation-assistant/chat/req_example/stream',
                      time_preview: { minimum_seconds: 5, maximum_seconds: 15 },
                    }), { status: 202, headers: { 'Content-Type': 'application/json' } });
                  }
                  if (path === '/api/documentation-assistant/chat/req_example/sources/src_example') {
                    return new Response(JSON.stringify({
                      api_version: 1, source_id: 'src_example', title: 'BPM overview',
                      published_url: '/help/en/user/overview.html', locale: 'en', excerpt: 'Approved excerpt.',
                    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                  }
                  if (path.startsWith('/api/documentation-assistant/conversation?locale=en&tab_id=')) {
                    return new Response(null, { status: 204 });
                  }
                  return new Response(null, { status: 404 });
                };
                window.EventSource = class {
                  constructor(url) { this.url = url; this.listeners = new Map(); }
                  addEventListener(name, listener) {
                    this.listeners.set(name, listener);
                    if (name === 'final') {
                      queueMicrotask(() => listener({ data: JSON.stringify({
                        api_version: 1, request_id: 'req_example', state: 'answer', state_epoch: 2,
                            reason_code: 'assistant_citations_validated', message_key: 'assistant_chat_answer',
                            action_key: '', disposition: 'answer', text: 'Grounded BPM answer.', citations: ['src_example'],
                          }) }));
                    }
                  }
                  close() {}
                };
                """)
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-toggle]").click()
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, "[data-assistant-send]"
                ).is_displayed()
            )
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-toggle]")
            question = driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-question]")
            question.send_keys("How do I configure BPM?")
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-send]").click()
            wait.until(
                lambda current_driver: (
                    "Grounded BPM answer."
                    in current_driver.execute_script(
                        "return document.querySelector('[data-assistant-transcript]').textContent;"
                    )
                )
            )
            driver.find_element(
                by.By.CSS_SELECTOR,
                ".bpm-docs-assistant-message--assistant summary",
            ).click()
            source = driver.find_element(
                by.By.CSS_SELECTOR,
                ".bpm-docs-assistant-message--assistant a",
            )
            assert source.text == "BPM overview"
            assert source.get_attribute("href").endswith("/help/en/user/overview.html")
            assert not driver.find_elements(
                by.By.CSS_SELECTOR, ".bpm-docs-assistant-external-claims"
            )
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-clear]").click()
            wait.until(
                lambda current_driver: (
                    current_driver.execute_script(
                        "return document.querySelectorAll('[data-assistant-message-role]').length;"
                    )
                    == 0
                )
            )
            calls = driver.execute_script("return window.__assistantTransportCalls;")
            assert any(
                call["path"] == "/api/documentation-assistant/chat" and call["method"] == "POST"
                for call in calls
            )
            assert any(call["path"].endswith("/sources/src_example") for call in calls)
            assert all("/web-mode" not in call["path"] for call in calls)
            assert all("request_web" not in call["body"] for call in calls)
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").click()
            wait.until(lambda current_driver: metrics(current_driver)["panelHidden"] is True)

            driver.set_window_size(1366, 1000)
            driver.get(f"{base_url}/help/en/index.html")
            theme_select = ui.Select(
                driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
            )
            backgrounds = []
            for mode in ("light", "dark"):
                theme_select.select_by_value(mode)
                driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-toggle]").click()
                backgrounds.append(metrics(driver)["panelBackground"])
                driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").click()
            assert backgrounds[0] != backgrounds[1]

            driver.execute_cdp_cmd(
                "Emulation.setEmulatedMedia",
                {
                    "features": [
                        {"name": "prefers-reduced-motion", "value": "reduce"},
                        {"name": "forced-colors", "value": "active"},
                    ]
                },
            )
            driver.refresh()
            toggle = wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, "[data-assistant-toggle]"
                )
            )
            accessibility_mode = driver.execute_script("""
                return {
                  reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
                  forcedColors: matchMedia('(forced-colors: active)').matches,
                };
                """)
            assert accessibility_mode["reducedMotion"] is True
            assert accessibility_mode["forcedColors"] is True
            toggle.click()
            assert metrics(driver)["panelHidden"] is False
        finally:
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})
            _close_chromium_driver(driver)


def test_documentation_floating_assistant_uses_m13_10_desktop_geometry_in_all_locales(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    def panel_metrics(current_driver) -> dict[str, float | bool]:
        return current_driver.execute_script("""
            const panel = document.querySelector('[data-assistant-panel]');
            const transcript = document.querySelector('[data-assistant-transcript]');
            const rect = panel.getBoundingClientRect();
            return {
              hidden: panel.hidden,
              width: rect.width,
              height: rect.height,
              top: rect.top,
              right: rect.right,
              bottom: rect.bottom,
              viewportWidth: window.innerWidth,
              viewportHeight: window.innerHeight,
              transcriptOverflow: getComputedStyle(transcript).overflowY,
            };
            """)

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 10)
        try:
            for locale in DOCUMENTATION_LOCALES:
                driver.set_window_size(1366, 1000)
                driver.get(f"{base_url}/help/{locale}/index.html")
                toggle = wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.CSS_SELECTOR, "[data-assistant-toggle]"
                    )
                )
                assert toggle.text == build_docs.SHELL_LABELS[locale]["assistant"]
                toggle.click()
                wait.until(lambda current_driver: panel_metrics(current_driver)["hidden"] is False)
                panel = panel_metrics(driver)
                assert panel["width"] == pytest.approx(panel["viewportWidth"] * 0.5, abs=2)
                assert panel["height"] == pytest.approx(panel["viewportHeight"] * 0.9, abs=2)
                assert panel["top"] >= 0
                assert panel["right"] <= panel["viewportWidth"] + 1
                assert panel["bottom"] <= panel["viewportHeight"] + 1
                assert panel["transcriptOverflow"] == "auto"

            driver.set_window_size(390, 900)
            driver.get(f"{base_url}/help/ru/index.html")
            wait.until(lambda current_driver: panel_metrics(current_driver)["hidden"] is False)
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").click()
            wait.until(lambda current_driver: panel_metrics(current_driver)["hidden"] is True)
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.CSS_SELECTOR, "[data-assistant-toggle]"
                )
            ).click()
            wait.until(lambda current_driver: panel_metrics(current_driver)["hidden"] is False)
            panel = panel_metrics(driver)
            assert panel["width"] >= panel["viewportWidth"] - 34
            assert panel["height"] <= panel["viewportHeight"] * 0.5 + 2
        finally:
            _close_chromium_driver(driver)


def test_documentation_floating_assistant_ships_local_only_without_external_sources_control(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 10)
        try:
            driver.get(f"{base_url}/help/en/index.html")
            _install_assistant_ready_browser_mock(driver, "en")
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-toggle]").click()
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-status]").text
                    == build_docs.SHELL_LABELS["en"]["assistant_ready"]
                )
            )
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-control]")
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-toggle]")

            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-question]").send_keys(
                "How do I configure BPM?"
            )
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-send]").click()
            wait.until(
                lambda current_driver: any(
                    call["path"] == "/api/documentation-assistant/chat"
                    for call in current_driver.execute_script("return window.__assistantQaCalls;")
                )
            )
            calls = driver.execute_script("return window.__assistantQaCalls;")
            assert all("/web-mode" not in call["path"] for call in calls)
            assert any('"web_mode":"local_only"' in call["body"] for call in calls)
        finally:
            _close_chromium_driver(driver)


def test_documentation_floating_assistant_release_qa_matrix_for_all_locales(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    def panel_state(current_driver) -> dict[str, object]:
        return current_driver.execute_script("""
            const panel = document.querySelector('[data-assistant-panel]');
            const transcript = document.querySelector('[data-assistant-transcript]');
            const header = document.querySelector('.bpm-docs-header');
            const panelRect = panel.getBoundingClientRect();
            const headerRect = header.getBoundingClientRect();
            return {
              panelHidden: panel.hidden,
              panelWidth: panelRect.width,
              panelHeight: panelRect.height,
              panelTop: panelRect.top,
              headerBottom: headerRect.bottom,
              viewportWidth: window.innerWidth,
              viewportHeight: window.innerHeight,
              transcriptClientHeight: transcript.clientHeight,
              transcriptScrollHeight: transcript.scrollHeight,
              inlineScripts: document.querySelectorAll('script:not([src])').length,
            };
            """)

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 10)
        try:
            for index, locale in enumerate(DOCUMENTATION_LOCALES):
                width, height = (1366, 1000) if index % 2 == 0 else (390, 900)
                labels = build_docs.SHELL_LABELS[locale]
                driver.set_window_size(width, height)
                driver.get(f"{base_url}/help/{locale}/index.html")
                toggle = wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.CSS_SELECTOR, "[data-assistant-toggle]"
                    )
                )
                assert toggle.text == labels["assistant"]
                assert (
                    driver.execute_script(
                        "return performance.getEntriesByType('resource').filter((entry) => "
                        "entry.name.includes('/api/documentation-assistant')).length;"
                    )
                    == 0
                )
                _install_assistant_ready_browser_mock(driver, locale)

                toggle.click()
                wait.until(
                    lambda current_driver, ready=labels["assistant_ready"]: (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, "[data-assistant-status]"
                        ).text
                        == ready
                    )
                )
                panel = panel_state(driver)
                assert panel["panelHidden"] is False
                if width >= 768:
                    assert panel["panelHeight"] >= panel["viewportHeight"] * 0.9 - 2
                    assert panel["panelHeight"] <= panel["viewportHeight"] * 0.9 + 2
                else:
                    assert panel["panelHeight"] <= panel["viewportHeight"] * 0.5 + 2
                if width >= 768:
                    assert panel["panelTop"] >= 0
                    assert panel["panelWidth"] >= panel["viewportWidth"] * 0.5 - 2
                    assert panel["panelWidth"] <= panel["viewportWidth"] * 0.5 + 2
                else:
                    assert panel["panelTop"] >= panel["headerBottom"] - 1
                    assert panel["panelWidth"] >= panel["viewportWidth"] - 34
                assert panel["inlineScripts"] == 0
                _assert_theme_metrics_fit(_theme_metrics(driver))

                theme_select = ui.Select(
                    driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                )
                theme_select.select_by_value("light")
                light_background = driver.execute_script(
                    "return getComputedStyle(document.querySelector('[data-assistant-panel]')).backgroundColor;"
                )
                theme_select.select_by_value("dark")
                dark_background = driver.execute_script(
                    "return getComputedStyle(document.querySelector('[data-assistant-panel]')).backgroundColor;"
                )
                assert light_background != dark_background

                assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-control]")
                assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-toggle]")
                assert driver.find_element(
                    by.By.CSS_SELECTOR, "[data-assistant-question]"
                ).is_enabled()
                assert driver.find_element(
                    by.By.CSS_SELECTOR, "[data-assistant-clear]"
                ).is_displayed()

                if locale == "en":
                    question = driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-question]")
                    question.send_keys("How do I configure BPM?")
                    driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-send]").click()
                    wait.until(
                        lambda current_driver: (
                            current_driver.find_element(
                                by.By.CSS_SELECTOR, "[data-documentation-assistant-widget]"
                            ).get_attribute("data-assistant-state")
                            == "busy"
                        )
                    )
                    assert (
                        driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-status]").text
                        == labels["assistant_busy_short"]
                    )
                    driver.execute_script("window.__assistantQaEmitFinal();")
                    wait.until(
                        lambda current_driver: (
                            "Grounded en BPM answer."
                            in current_driver.execute_script(
                                "return document.querySelector('[data-assistant-transcript]').textContent;"
                            )
                        )
                    )
                    assert any(
                        '"web_mode":"local_only"' in call["body"]
                        for call in driver.execute_script("return window.__assistantQaCalls;")
                    )
                    for turn in range(8):
                        assert (
                            driver.execute_script(
                                """
                            return window.BPMDocumentationAssistantConversation.recordCompletedTurn(
                              document.querySelector('[data-documentation-assistant-widget]'), arguments[0]
                            );
                            """,
                                {
                                    "user": f"Long question {turn}: " + ("q" * 320),
                                    "assistant": f"Long answer {turn}: " + ("a" * 640),
                                },
                            )
                            is True
                        )
                    transcript_state = panel_state(driver)
                    assert (
                        transcript_state["transcriptScrollHeight"]
                        > transcript_state["transcriptClientHeight"]
                    )
                    driver.refresh()
                    wait.until(
                        lambda current_driver: panel_state(current_driver)["panelHidden"] is False
                    )
                    restored = driver.execute_script("""
                        const transcript = document.querySelector('[data-assistant-transcript]');
                        return {
                          messageCount: transcript.querySelectorAll('[data-assistant-message-role]').length,
                          unsafeNodes: transcript.querySelectorAll('img, script').length,
                          text: transcript.textContent,
                        };
                        """)
                    assert restored["messageCount"] == 16
                    assert restored["unsafeNodes"] == 0
                    assert "Long answer 7:" in restored["text"]
                    assert (
                        driver.execute_script(
                            "return performance.getEntriesByType('resource').filter((entry) => "
                            "entry.name.includes('/api/documentation-assistant')).length;"
                        )
                        == 0
                    )
                    continue

                if locale == "ru":
                    first_topic = build_docs._navigation_topic_order("user-guide.ditamap")[0]
                    driver.get(f"{base_url}/help/{locale}/user/{first_topic}.html")
                    _install_assistant_ready_browser_mock(driver, locale)
                    wait.until(
                        lambda current_driver: panel_state(current_driver)["panelHidden"] is False
                    )
                    driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").click()
                    wait.until(
                        lambda current_driver: panel_state(current_driver)["panelHidden"] is True
                    )
                    driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-toggle]").click()
                    wait.until(
                        lambda current_driver: panel_state(current_driver)["panelHidden"] is False
                    )
                    calls = driver.execute_script("return window.__assistantQaCalls;")
                    assert all("/web-mode" not in call["path"] for call in calls)

                if locale == "es-ES":
                    driver.execute_script("window.__assistantQaRejectChat = true;")
                    question = driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-question]")
                    question.send_keys("¿Cómo configuro BPM?")
                    driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-send]").click()
                    wait.until(
                        lambda current_driver, expected=labels["assistant_unavailable_short"]: (
                            current_driver.find_element(
                                by.By.CSS_SELECTOR, "[data-assistant-status]"
                            ).text
                            == expected
                        )
                    )
                    assert (
                        driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-status]").text
                        == labels["assistant_unavailable_short"]
                    )

                calls = driver.execute_script("return window.__assistantQaCalls;")
                assert calls
                assert all(
                    call["path"].startswith("/api/documentation-assistant/") for call in calls
                )
                assert all(
                    "search" not in call["path"] and "brave" not in call["path"] for call in calls
                )
                driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-collapse]").send_keys(
                    keys.Keys.ESCAPE
                )
                wait.until(
                    lambda current_driver: panel_state(current_driver)["panelHidden"] is True
                )
                assert driver.switch_to.active_element.get_attribute("data-assistant-toggle") == ""

            csp_messages = [
                entry["message"]
                for entry in driver.get_log("browser")
                if "Content Security Policy" in entry["message"]
            ]
            assert not csp_messages
        finally:
            _close_chromium_driver(driver)


def test_documentation_floating_assistant_install_failure_stays_locale_safe(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    locale = "de"
    labels = build_docs.SHELL_LABELS[locale]

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 10)
        try:
            driver.get(f"{base_url}/help/{locale}/index.html")
            _install_assistant_failure_browser_mock(driver, locale)
            driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-toggle]").click()
            install = wait.until(
                lambda current_driver: (
                    element
                    if (
                        element := current_driver.find_element(
                            by.By.CSS_SELECTOR, "[data-assistant-install]"
                        )
                    ).is_displayed()
                    and element.is_enabled()
                    else False
                )
            )
            install.click()
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, "[data-documentation-assistant-widget]"
                    ).get_attribute("data-assistant-state")
                    == "model-failed"
                )
            )
            status = driver.find_element(by.By.CSS_SELECTOR, "[data-assistant-status]").text
            assert status == labels["assistant_install_failed"]
            assert "artifact_hash_mismatch" not in status
            assert not driver.find_element(
                by.By.CSS_SELECTOR, "[data-assistant-question]"
            ).is_enabled()
            assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-assistant-web-control]")
            calls = driver.execute_script("return window.__assistantQaFailureCalls;")
            assistant_status_path = f"/api/documentation-assistant/status?locale={locale}"
            model_status_path = f"/api/local-model?locale={locale}"
            install_path = "/api/local-model/install"
            portal_index_call = {
                "method": "GET",
                "path": f"../search/{locale}/index.json",
                "body": "",
            }
            non_assistant_calls = [call for call in calls if not call["path"].startswith("/api/")]
            # The portal search script can complete its already-started local index load after the
            # mock is installed.  It is not assistant traffic, so permit only this exact static
            # same-locale resource (and never a search or external assistant endpoint).
            assert all(call == portal_index_call for call in non_assistant_calls)
            assert len(non_assistant_calls) <= 1
            assistant_calls = [call for call in calls if call["path"].startswith("/api/")]
            assert assistant_calls == [
                {"method": "GET", "path": assistant_status_path, "body": ""},
                {"method": "GET", "path": model_status_path, "body": ""},
                {
                    "method": "POST",
                    "path": install_path,
                    "body": json.dumps(
                        {
                            "api_version": 1,
                            "locale": locale,
                            "csrf_token": "c" * 24,
                            "confirm_install": True,
                        },
                        separators=(",", ":"),
                    ),
                },
                {"method": "GET", "path": model_status_path, "body": ""},
            ]
        finally:
            _close_chromium_driver(driver)


def test_all_settings_row_help_links_cover_modes_locales_search_and_keyboard(
    tmp_path: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    _write_packaged_site(tmp_path)
    long_unknown_preference = "unternehmen.sehr.langer.verwalteter.parametername"

    with _documentation_test_server_handle(tmp_path) as server:
        base_url = server.base_url
        profile_id = _create_profile(
            base_url,
            name="All Settings row help browser smoke",
            flags={"VisualSearchEnabled": False},
        )
        session = server.session_factory()
        try:
            profile = session.get(Profile, profile_id)
            assert profile is not None
            profile.flags = {
                "VisualSearchEnabled": False,
                "CustomEnterprisePolicy": {"Enabled": True},
                "Preferences": {
                    "browser.download.dir": {
                        "Status": "locked",
                        "Value": "/srv/downloads",
                    },
                    long_unknown_preference: {
                        "Status": "default",
                        "Value": True,
                    },
                },
            }
            session.commit()
        finally:
            session.close()
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/settings?settingsMode=configured")
            wait.until(
                lambda current: current.find_elements(by.By.CSS_SELECTOR, "[data-settings-mode]")
            )

            def switch_mode(mode: str) -> None:
                button = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f"[data-settings-mode='{mode}']",
                )
                driver.execute_script("arguments[0].click();", button)
                wait.until(
                    lambda current: (
                        current.find_element(
                            by.By.CSS_SELECTOR,
                            f"[data-settings-mode='{mode}']",
                        ).get_attribute("aria-pressed")
                        == "true"
                    )
                )

            def row_help(entry_id: str):
                return wait.until(
                    lambda current: next(
                        (
                            element
                            for element in current.find_elements(
                                by.By.CSS_SELECTOR,
                                ".all-settings-list-row-shell "
                                f".all-settings-row-help-link[data-settings-entry-id='{entry_id}']",
                            )
                            if element.is_displayed()
                        ),
                        False,
                    )
                )

            def search_help(entry_id: str):
                search = driver.find_element(by.By.ID, "wizard-settings-search-input")
                search.clear()
                search.send_keys(entry_id)
                return wait.until(
                    lambda current: next(
                        (
                            element
                            for element in current.find_elements(
                                by.By.CSS_SELECTOR,
                                "[data-all-settings-help-location='search']"
                                f"[data-settings-entry-id='{entry_id}']",
                            )
                            if element.is_displayed()
                        ),
                        False,
                    )
                )

            ru = _load_locale_catalog("ru")
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])

            switch_mode("configured")
            policy_link = row_help("VisualSearchEnabled")
            preference_link = row_help("browser.download.dir")
            unknown_indicator = row_help("CustomEnterprisePolicy")
            assert policy_link.tag_name == "a"
            assert policy_link.get_attribute("data-settings-entry-help-disposition") == "linked"
            assert preference_link.tag_name == "a"
            assert preference_link.get_attribute("href").endswith(
                "/help/ru/firefox/fx-reference-managed-preference-locking.html#a-safe-review"
            )
            assert unknown_indicator.tag_name == "span"
            assert unknown_indicator.get_attribute("href") is None
            assert unknown_indicator.get_attribute("aria-disabled") == "true"
            assert unknown_indicator.get_attribute("data-settings-entry-help-disposition") == (
                "unsupported_unknown"
            )

            switch_mode("review")
            review_unknown = row_help("CustomEnterprisePolicy")
            assert review_unknown.get_attribute("data-settings-entry-help-disposition") == (
                "unsupported_unknown"
            )
            assert review_unknown.get_attribute("href") is None

            switch_mode("catalog")
            raw_filter = driver.find_element(
                by.By.CSS_SELECTOR,
                "[data-settings-list-filter='raw']",
            )
            driver.execute_script("arguments[0].click();", raw_filter)
            raw_row = wait.until(
                lambda current: next(
                    (
                        element
                        for element in current.find_elements(
                            by.By.CSS_SELECTOR,
                            ".all-settings-list-row[data-settings-entry-raw='true']",
                        )
                        if element.is_displayed()
                    ),
                    False,
                )
            )
            raw_help = raw_row.find_element(
                by.By.XPATH,
                "following-sibling::*[contains(@class, 'all-settings-row-help-link')]",
            )
            assert raw_help.get_attribute("href") is None
            assert raw_help.get_attribute("data-settings-entry-help-disposition") == (
                "missing_documentation"
            )

            searched_preference = search_help("browser.download.dir")
            expected_ru_label = ru["profiles.all_settings.row_help.open"].replace(
                "{setting}", "browser.download.dir"
            )
            assert searched_preference.tag_name == "a"
            assert searched_preference.get_attribute("aria-label") == expected_ru_label
            assert searched_preference.get_attribute("target") == "_blank"
            assert searched_preference.get_attribute("rel") == "noopener noreferrer"

            de = _load_locale_catalog("de")
            _set_locale(driver, wait, ui, locale="de", expected_text=de["profiles.locale_label"])
            long_unknown = search_help(long_unknown_preference)
            expected_de_label = de["profiles.all_settings.row_help.unknown_not_supported"].replace(
                "{setting}", long_unknown_preference
            )
            assert long_unknown.tag_name == "span"
            assert long_unknown.get_attribute("aria-label") == expected_de_label
            assert long_unknown.get_attribute("href") is None
            search_shell_metrics = driver.execute_script(
                """
                const help = arguments[0];
                const shell = help.closest('.wizard-settings-search-result-shell');
                const button = shell.querySelector('[data-settings-search-target]');
                const shellRect = shell.getBoundingClientRect();
                const buttonRect = button.getBoundingClientRect();
                const helpRect = help.getBoundingClientRect();
                return {
                  shellRight: shellRect.right,
                  buttonRight: buttonRect.right,
                  helpLeft: helpRect.left,
                  helpRight: helpRect.right,
                };
                """,
                long_unknown,
            )
            assert search_shell_metrics["buttonRight"] <= search_shell_metrics["helpLeft"] + 1
            assert search_shell_metrics["helpRight"] <= search_shell_metrics["shellRight"] + 1
            _assert_document_fits(driver)

            switch_mode("configured")
            policy_link = row_help("VisualSearchEnabled")
            row_button = policy_link.find_element(
                by.By.XPATH,
                "preceding-sibling::*[@data-settings-entry-select]",
            )
            driver.execute_script("arguments[0].focus();", row_button)
            row_button.send_keys(keys.Keys.TAB)
            wait.until(lambda current: current.switch_to.active_element == policy_link)
            assert policy_link.get_attribute("href").endswith(
                "/help/de/firefox/fx-concept-complex-policy-families.html#a-privacy-ai"
            )
            main_handle = driver.current_window_handle
            previous_handles = set(driver.window_handles)
            policy_link.send_keys(keys.Keys.ENTER)
            wait.until(lambda current: len(set(current.window_handles) - previous_handles) == 1)
            new_handle = (set(driver.window_handles) - previous_handles).pop()
            driver.switch_to.window(new_handle)
            wait.until(
                lambda current: current.current_url.endswith(
                    "/help/de/firefox/fx-concept-complex-policy-families.html#a-privacy-ai"
                )
            )
            assert "fx-concept-complex-policy-families" in _body_text(driver)
            _close_current_tab_and_return(driver, main_handle)
        finally:
            _close_chromium_driver(driver)


def test_documentation_navigation_tree_browser_smoke_for_all_locales(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    first_user_topic_id = build_docs._navigation_topic_order("user-guide.ditamap")[0]
    first_admin_topic_id = build_docs._navigation_topic_order("administrator-guide.ditamap")[0]
    first_firefox_topic_id = build_docs._navigation_topic_order("firefox-policy-guide.ditamap")[0]
    sections_by_guide = build_docs._navigation_model(generated_theme_smoke_site)["sections"]
    first_user_section = sections_by_guide["user-guide"][0]
    first_admin_section = sections_by_guide["administrator-guide"][0]
    facets = build_docs._search_facets_filters()
    language_sample = LANGUAGE_BROWSER_QA["language_sample"]
    loaded_main_metrics: dict[str, dict[str, float]] = {}

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        driver.set_page_load_timeout(60)
        wait = ui.WebDriverWait(driver, 20)
        try:
            for locale in DOCUMENTATION_LOCALES:
                expected_root = build_docs.SHELL_LABELS[locale]["navigation_root"]
                expected_guide_label = build_docs._map_title(locale, "user-guide.ditamap")
                expected_user_section_label = first_user_section["labels"][locale]
                expected_admin_section_label = first_admin_section["labels"][locale]
                expected_filters = build_docs._localized_search_facet_fields(locale, facets)

                driver.set_window_size(1366, 1000)
                driver.get(f"{base_url}/help/{locale}/index.html")
                wait.until(
                    lambda current_driver: current_driver.find_element(
                        by.By.CSS_SELECTOR, "[data-docs-tree]"
                    )
                )
                host = driver.find_element(by.By.CSS_SELECTOR, "[data-docs-tree-host]")
                assert host.get_attribute("aria-busy") == "false"
                navigation_resources = driver.execute_script("""
                    return performance.getEntriesByType('resource')
                      .filter((entry) => entry.name.endsWith('/navigation.json'))
                      .map((entry) => entry.name);
                    """)
                assert navigation_resources == [f"{base_url}/help/{locale}/navigation.json"]
                root_state = _tree_state(driver)
                assert root_state["rootText"] == expected_root
                assert root_state["currentNode"] == "documentation-root"
                assert root_state["activeNode"] == "documentation-root"
                assert root_state["tabStops"] == ["documentation-root"]
                assert root_state["guideCount"] == len(build_docs.GUIDE_MAPS)
                assert [guide["node"] for guide in root_state["guides"]] == (
                    LANGUAGE_BROWSER_QA["expected_guide_node_ids"]
                )
                for forbidden_guide_node_id in LANGUAGE_BROWSER_QA["forbidden_guide_node_ids"]:
                    assert not driver.find_elements(
                        by.By.CSS_SELECTOR,
                        f"[data-tree-node='{forbidden_guide_node_id}']",
                    )
                assert [guide["hidden"] for guide in root_state["guides"]] == [True] * len(
                    build_docs.GUIDE_MAPS
                )
                assert root_state["breadcrumbs"] == [expected_root]
                _assert_document_fits(driver)
                loaded_main_metrics[locale] = driver.execute_script("""
                    const rect = document.querySelector('.bpm-docs-main').getBoundingClientRect();
                    return { left: rect.left, width: rect.width };
                    """)

                driver.get(f"{base_url}/help/{locale}/index.html#a-user-guide")
                wait.until(
                    lambda current_driver: (
                        _tree_state(current_driver)["currentNode"] == "user-guide"
                    )
                )
                guide_state = _tree_state(driver)
                assert guide_state["activeNode"] == "user-guide"
                assert guide_state["currentText"] == expected_guide_label
                assert (
                    next(guide for guide in guide_state["guides"] if guide["node"] == "user-guide")[
                        "hidden"
                    ]
                    is False
                )
                user_section_state = _tree_collection_node(
                    guide_state, "sections", first_user_section["node_id"]
                )
                assert user_section_state["text"] == expected_user_section_label
                assert user_section_state["expanded"] == "false"
                assert user_section_state["hidden"] is True
                assert driver.current_url.endswith("#a-user-guide")

                user_guide_node = driver.find_element(
                    by.By.CSS_SELECTOR, "[data-tree-node='user-guide']"
                )
                user_guide_node.send_keys(keys.Keys.ARROW_RIGHT)
                assert _tree_state(driver)["activeNode"] == first_user_section["node_id"]
                user_section_node = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f"[data-tree-node='{first_user_section['node_id']}']",
                )
                user_section_node.send_keys(keys.Keys.ARROW_RIGHT)
                assert (
                    _tree_collection_node(
                        _tree_state(driver), "sections", first_user_section["node_id"]
                    )["hidden"]
                    is False
                )
                user_section_node.send_keys(keys.Keys.ARROW_RIGHT)
                assert _tree_state(driver)["activeNode"] == first_user_topic_id
                driver.find_element(
                    by.By.CSS_SELECTOR, f"[data-tree-node='{first_user_topic_id}']"
                ).send_keys(keys.Keys.ARROW_LEFT)
                assert _tree_state(driver)["activeNode"] == first_user_section["node_id"]
                user_section_node.send_keys(keys.Keys.SPACE)
                assert (
                    _tree_collection_node(
                        _tree_state(driver), "sections", first_user_section["node_id"]
                    )["hidden"]
                    is True
                )
                user_section_node.send_keys(keys.Keys.ENTER)
                assert (
                    _tree_collection_node(
                        _tree_state(driver), "sections", first_user_section["node_id"]
                    )["hidden"]
                    is False
                )
                user_section_node.click()
                clicked_section_state = _tree_collection_node(
                    _tree_state(driver), "sections", first_user_section["node_id"]
                )
                assert clicked_section_state["hidden"] is True
                assert _tree_state(driver)["activeNode"] == first_user_section["node_id"]
                user_section_node.click()

                user_guide_node.send_keys(keys.Keys.SPACE)
                collapsed_state = _tree_state(driver)
                assert (
                    next(
                        guide
                        for guide in collapsed_state["guides"]
                        if guide["node"] == "user-guide"
                    )["hidden"]
                    is True
                )
                user_guide_node.send_keys(keys.Keys.SPACE)
                expanded_state = _tree_state(driver)
                assert (
                    next(
                        guide for guide in expanded_state["guides"] if guide["node"] == "user-guide"
                    )["hidden"]
                    is False
                )

                driver.find_element(by.By.CSS_SELECTOR, "[data-tree-node='user-guide']").send_keys(
                    keys.Keys.HOME
                )
                assert _tree_state(driver)["activeNode"] == "documentation-root"
                driver.find_element(
                    by.By.CSS_SELECTOR, "[data-tree-node='documentation-root']"
                ).send_keys(keys.Keys.ARROW_DOWN)
                assert _tree_state(driver)["activeNode"] == "user-guide"

                topic_url = f"{base_url}/help/{locale}/user/{first_user_topic_id}.html"
                driver.get(topic_url)
                wait.until(
                    lambda current_driver: (
                        _tree_state(current_driver)["currentNode"] == first_user_topic_id
                    )
                )
                topic_state = _tree_state(driver)
                assert topic_state["activeNode"] == first_user_topic_id
                assert topic_state["tabStops"] == [first_user_topic_id]
                assert topic_state["breadcrumbs"][:2] == [expected_root, expected_guide_label]
                assert topic_state["breadcrumbs"][-1]
                assert (
                    next(guide for guide in topic_state["guides"] if guide["node"] == "user-guide")[
                        "hidden"
                    ]
                    is False
                )
                current_section_state = _tree_collection_node(
                    topic_state, "sections", first_user_section["node_id"]
                )
                assert current_section_state["text"] == expected_user_section_label
                assert current_section_state["hidden"] is False
                assert current_section_state["expanded"] == "true"
                current_section_node = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f"[data-tree-node='{first_user_section['node_id']}']",
                )
                current_section_node.send_keys(keys.Keys.SPACE)
                assert (
                    _tree_collection_node(
                        _tree_state(driver), "sections", first_user_section["node_id"]
                    )["hidden"]
                    is False
                )
                driver.set_window_size(390, 900)
                _assert_document_fits(driver)
                driver.set_window_size(1366, 1000)

                driver.find_element(by.By.CSS_SELECTOR, "[data-tree-node='user-guide']").click()
                wait.until(
                    lambda current_driver: (
                        current_driver.current_url.endswith("#a-user-guide")
                        and _tree_state(current_driver)["currentNode"] == "user-guide"
                    )
                )
                driver.find_element(
                    by.By.CSS_SELECTOR, "[data-tree-node='documentation-root']"
                ).click()
                wait.until(
                    lambda current_driver, expected_locale=locale: (
                        current_driver.current_url.endswith(f"/help/{expected_locale}/index.html")
                        and _tree_state(current_driver)["currentNode"] == "documentation-root"
                    )
                )
                driver.back()
                wait.until(
                    lambda current_driver: (
                        current_driver.current_url.endswith("#a-user-guide")
                        and _tree_state(current_driver)["currentNode"] == "user-guide"
                    )
                )
                driver.forward()
                wait.until(
                    lambda current_driver, expected_locale=locale: (
                        current_driver.current_url.endswith(f"/help/{expected_locale}/index.html")
                        and _tree_state(current_driver)["currentNode"] == "documentation-root"
                    )
                )

                admin_topic_url = f"{base_url}/help/{locale}/admin/{first_admin_topic_id}.html"
                driver.get(admin_topic_url)
                wait.until(
                    lambda current_driver: (
                        _tree_state(current_driver)["currentNode"] == first_admin_topic_id
                    )
                )
                admin_section_state = _tree_collection_node(
                    _tree_state(driver), "sections", first_admin_section["node_id"]
                )
                assert admin_section_state["text"] == expected_admin_section_label
                assert admin_section_state["hidden"] is False
                assert admin_section_state["expanded"] == "true"

                firefox_topic_url = (
                    f"{base_url}/help/{locale}/firefox/{first_firefox_topic_id}.html"
                )
                driver.get(firefox_topic_url)
                wait.until(
                    lambda current_driver: (
                        _tree_state(current_driver)["currentNode"] == first_firefox_topic_id
                    )
                )
                firefox_topic_node = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f"[data-tree-node='{first_firefox_topic_id}']",
                )
                assert firefox_topic_node.get_attribute("aria-level") == "3"
                assert firefox_topic_node.get_attribute("data-tree-parent") == (
                    "firefox-policy-guide"
                )
                assert not driver.find_elements(
                    by.By.CSS_SELECTOR,
                    "[data-tree-node^='section:firefox-policy-guide:']",
                )

                sample = language_sample["locales"][locale]
                sample_topic_id = language_sample["topic_id"]
                driver.get(f"{base_url}/help/{locale}/user/{sample_topic_id}.html")
                wait.until(
                    lambda current_driver, expected_topic_id=sample_topic_id: (
                        _tree_state(current_driver)["currentNode"] == expected_topic_id
                    )
                )
                sample_state = _tree_state(driver)
                assert sample_state["activeNode"] == sample_topic_id
                sample_body = _body_text(driver)
                for expected_fragment in (
                    sample["interface_name"],
                    sample["title"],
                    sample["shortdesc"],
                    sample["first_paragraph"],
                ):
                    assert expected_fragment in sample_body
                for forbidden_fragment in sample["forbidden_english_fragments"]:
                    assert forbidden_fragment not in sample_body
                for viewport in LANGUAGE_BROWSER_QA["viewports"].values():
                    driver.set_window_size(viewport["width"], viewport["height"])
                    _assert_document_fits(driver)

                driver.get(f"{base_url}/help/{locale}/index.html")

                search_input = driver.find_element(by.By.CSS_SELECTOR, "#bpm-docs-search-query")
                search_input.clear()
                search_input.send_keys("theme")
                _click_element(
                    driver,
                    driver.find_element(by.By.CSS_SELECTOR, "[data-search-advanced-toggle]"),
                )
                wait.until(
                    lambda current_driver: current_driver.find_elements(
                        by.By.CSS_SELECTOR, ".bpm-docs-search-filter-grid legend"
                    )
                )
                legends = [
                    element.text
                    for element in driver.find_elements(
                        by.By.CSS_SELECTOR, ".bpm-docs-search-filter-grid legend"
                    )
                ]
                assert expected_filters["guide_id"]["label"] in legends
                assert expected_filters["topic_kind"]["label"] in legends
                assert expected_filters["guide_id"]["value_labels"]["user-guide"] in _body_text(
                    driver
                )
                assert expected_filters["topic_kind"]["value_labels"]["task"] in _body_text(driver)

                for width, height in ((1366, 1000), (390, 900)):
                    driver.set_window_size(width, height)
                    _assert_document_fits(driver)
                    _assert_theme_metrics_fit(_theme_metrics(driver))
                    _assert_compact_search_row_fits(_compact_search_metrics(driver))

            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            try:
                for locale in DOCUMENTATION_LOCALES:
                    navigation_path = generated_theme_smoke_site / f"{locale}/navigation.json"
                    navigation_backup = navigation_path.read_bytes()
                    navigation_path.unlink()
                    try:
                        driver.set_window_size(1366, 1000)
                        driver.get(f"{base_url}/help/{locale}/index.html")
                        unavailable = wait.until(
                            lambda current: current.find_element(
                                by.By.CSS_SELECTOR,
                                ".bpm-docs-tree-status--unavailable",
                            )
                        )
                        assert (
                            build_docs.SHELL_LABELS[locale]["navigation_unavailable"]
                            in unavailable.text
                        )
                        fallback = unavailable.find_element(by.By.CSS_SELECTOR, "a")
                        assert fallback.get_attribute("href") == (
                            f"{base_url}/help/{locale}/index.html"
                        )
                        assert not driver.find_elements(by.By.CSS_SELECTOR, "[data-docs-tree]")
                        unavailable_main_metrics = driver.execute_script("""
                            const rect = document.querySelector('.bpm-docs-main').getBoundingClientRect();
                            return { left: rect.left, width: rect.width };
                            """)
                        assert unavailable_main_metrics == loaded_main_metrics[locale]
                        _assert_document_fits(driver)
                    finally:
                        navigation_path.write_bytes(navigation_backup)
            finally:
                driver.execute_cdp_cmd(
                    "Network.setCacheDisabled",
                    {"cacheDisabled": False},
                )
        finally:
            _close_chromium_driver(driver)


def test_documentation_sidebar_scroll_is_independent_and_reveals_deep_topic(
    generated_theme_smoke_site: Path,
) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    action_chains = pytest.importorskip("selenium.webdriver.common.action_chains")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    wheel_input = pytest.importorskip("selenium.webdriver.common.actions.wheel_input")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    topic_id = build_docs._navigation_topic_order("user-guide.ditamap")[-1]
    model = build_docs._navigation_model(generated_theme_smoke_site)

    with _documentation_test_server(generated_theme_smoke_site) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            cases = [
                (locale, viewport["width"], viewport["height"])
                for locale in DOCUMENTATION_LOCALES
                for viewport in LANGUAGE_BROWSER_QA["viewports"].values()
            ]
            for locale, width, height in cases:
                output = model["topics"][topic_id]["output"][locale]
                driver.set_window_size(width, height)
                driver.get(f"{base_url}/help/{output}")
                wait.until(lambda current: _tree_state(current)["currentNode"] == topic_id)
                initial = _sidebar_scroll_state(driver)
                assert initial["overflowY"] == "auto"
                assert initial["overflowX"] == "hidden"
                assert initial["maxBlockSize"] != "none"
                assert initial["scrollHeight"] > initial["clientHeight"]
                assert initial["scrollTop"] > 0
                assert initial["windowScrollY"] == 0
                assert initial["activeNode"] == topic_id
                assert initial["activeTop"] >= initial["sidebarTop"] - 1
                assert initial["activeBottom"] <= initial["sidebarBottom"] + 1
                assert initial["scrollWidth"] <= initial["clientWidth"] + 1
                assert initial["position"] == ("sticky" if width == 1366 else "static")

                sidebar = driver.find_element(by.By.CSS_SELECTOR, ".bpm-docs-sidebar")
                driver.execute_script("arguments[0].scrollTop = 0;", sidebar)
                origin = wheel_input.ScrollOrigin.from_element(sidebar)
                action_chains.ActionChains(driver).scroll_from_origin(origin, 0, 600).perform()
                wait.until(
                    lambda current, current_sidebar=sidebar: (
                        current.execute_script("return arguments[0].scrollTop;", current_sidebar)
                        > 0
                    )
                )
                wheel_state = _sidebar_scroll_state(driver)
                assert wheel_state["scrollTop"] > 0
                assert wheel_state["windowScrollY"] == 0

                independent = driver.execute_script("""
                    const sidebar = document.querySelector('.bpm-docs-sidebar');
                    const beforeWindow = window.scrollY;
                    sidebar.scrollTop = 0;
                    const atStart = sidebar.scrollTop;
                    sidebar.scrollTop = sidebar.scrollHeight;
                    return {
                      beforeWindow,
                      afterWindow: window.scrollY,
                      atStart,
                      atEnd: sidebar.scrollTop,
                    };
                    """)
                assert independent["beforeWindow"] == independent["afterWindow"] == 0
                assert independent["atStart"] == 0
                assert independent["atEnd"] > 0

                current = driver.find_element(
                    by.By.CSS_SELECTOR,
                    f"[data-tree-node='{topic_id}']",
                )
                current.send_keys(keys.Keys.END)
                focused = _sidebar_scroll_state(driver)
                assert focused["activeNode"] != topic_id
                assert focused["activeTop"] >= focused["sidebarTop"] - 1
                assert focused["activeBottom"] <= focused["sidebarBottom"] + 1
                assert focused["windowScrollY"] == 0
                assert focused["scrollWidth"] <= focused["clientWidth"] + 1
        finally:
            _close_chromium_driver(driver)


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
                _set_locale(
                    driver, wait, ui, locale=locale, expected_text=catalog["profiles.locale_label"]
                )
                docs_link = wait.until(
                    ec.element_to_be_clickable((by.By.CSS_SELECTOR, ".compact-toolbar-docs-link"))
                )
                assert docs_link.get_attribute("href") == f"{base_url}/help/{locale}/index.html"

                _click_and_switch_to_new_tab(driver, wait, docs_link)
                wait.until(
                    lambda current_driver, expected_locale=locale: (
                        current_driver.current_url.endswith(f"/help/{expected_locale}/index.html")
                    )
                )
                wait.until(
                    lambda current_driver, expected_locale=locale: (
                        current_driver.execute_script("return document.documentElement.lang;")
                        == expected_locale
                    )
                )
                assert f"Docs {locale}" in _body_text(driver)
                assert driver.find_element(
                    by.By.CSS_SELECTOR, "form[role='search'] input[type='search']"
                )
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


def test_documentation_header_preferences_persist_between_bpm_and_portal(tmp_path: Path) -> None:
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")
    ru = _load_locale_catalog("ru")
    _write_generated_theme_smoke_site(tmp_path)

    with _documentation_test_server(tmp_path) as base_url:
        driver = _build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])
            ui.Select(driver.find_element(by.By.ID, "theme")).select_by_value("dark")
            wait.until(
                lambda current_driver: (
                    current_driver.execute_script("return document.documentElement.dataset.theme;")
                    == "dark"
                )
            )
            wait.until(
                lambda current_driver: (
                    current_driver.execute_script(
                        "return window.localStorage.getItem('bpm-theme-mode');"
                    )
                    == "dark"
                )
            )

            docs_link = wait.until(
                ec.element_to_be_clickable((by.By.CSS_SELECTOR, ".compact-toolbar-docs-link"))
            )
            _click_and_switch_to_new_tab(driver, wait, docs_link)
            wait.until(
                lambda current_driver: current_driver.current_url.endswith("/help/ru/index.html")
            )
            assert (
                ui.Select(
                    driver.find_element(by.By.CSS_SELECTOR, "[data-docs-locale-select]")
                ).first_selected_option.get_attribute("value")
                == "ru"
            )
            assert (
                ui.Select(
                    driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
                ).first_selected_option.get_attribute("value")
                == "dark"
            )

            ui.Select(
                driver.find_element(by.By.CSS_SELECTOR, "[data-docs-locale-select]")
            ).select_by_value("de")
            wait.until(
                lambda current_driver: current_driver.current_url.endswith("/help/de/index.html")
            )
            ui.Select(
                driver.find_element(by.By.CSS_SELECTOR, "[data-docs-theme-select]")
            ).select_by_value("light")

            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "list")))
            wait.until(
                lambda current_driver: (
                    current_driver.execute_script("return document.documentElement.lang;") == "de"
                )
            )
            assert (
                ui.Select(
                    driver.find_element(by.By.ID, "lang")
                ).first_selected_option.get_attribute("value")
                == "de"
            )
            assert (
                ui.Select(
                    driver.find_element(by.By.ID, "theme")
                ).first_selected_option.get_attribute("value")
                == "light"
            )
            assert (
                driver.execute_script("return document.documentElement.dataset.theme;") == "light"
            )
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
        driver.set_page_load_timeout(60)
        wait = ui.WebDriverWait(driver, 20)
        main_handle = ""
        try:
            contextual_routes = {
                "/profiles/compare": ("compare", "ug-task-compare-profiles"),
                "/profiles/new": ("guided", "ug-task-use-guided-editor"),
                f"/profiles/{profile_id}/settings": ("settings", "ug-task-use-all-settings"),
                f"/profiles/{profile_id}/json": ("json", "ug-task-use-json-editor"),
            }

            for route, (surface, topic_id) in contextual_routes.items():
                driver.get(f"{base_url}{route}")
                wait.until(ec.presence_of_element_located((by.By.ID, "lang")))
                _set_locale(
                    driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"]
                )
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
                    lambda current_driver, expected_topic_id=topic_id: (
                        current_driver.current_url.endswith(f"/{expected_topic_id}.html")
                    )
                )
                assert topic_id in _body_text(driver)
                _close_current_tab_and_return(driver, main_handle)

            driver.get(f"{base_url}/profiles")
            wait.until(ec.presence_of_element_located((by.By.ID, "lang")))
            _set_locale(driver, wait, ui, locale="ru", expected_text=ru["profiles.locale_label"])
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
                lambda current_driver: (
                    "ug-task-import-policies-json.html" in current_driver.current_url
                )
            )
            _close_current_tab_and_return(driver, main_handle)

            driver.get(f"{base_url}/docs")
            wait.until(
                lambda current_driver: (
                    "Swagger UI" in current_driver.execute_script("return document.title || '';")
                )
            )
            assert driver.current_url.endswith("/docs")
        finally:
            _close_chromium_driver(driver)
