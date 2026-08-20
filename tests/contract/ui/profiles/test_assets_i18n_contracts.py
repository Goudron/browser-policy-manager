# ruff: noqa: F403,F405
import json
import re

from tests.contract.docs.general.test_documentation_runtime_route import _write_packaged_site
from tests.web_profiles_page_helpers import *


def test_profiles_header_shows_supported_firefox_channels_on_a_separate_explanatory_line():
    response = _profiles_page_response()
    soup = BeautifulSoup(response.text, "html.parser")

    versions = soup.select_one("[data-supported-firefox-versions]")
    counter = soup.select_one("[data-bpm-header-workspace]")

    assert versions is not None
    assert versions.name == "p"
    assert not versions.find_parent("h1")
    assert [item.get_text(strip=True) for item in versions.find_all("span", recursive=False)] == [
        "Supported Firefox schemas:",
        "Release 153,",
        "ESR 153.0,",
        "ESR 140.13,",
        "ESR 115.39",
    ]
    assert counter is not None
    assert counter.find("strong", id="workspace-profile-count", recursive=False) is not None
    assert counter.find("span", id="workspace-profile-label", recursive=False) is not None
    assert counter.select_one(".compact-counter-meta") is None
    assert "profiles.nav_library" not in str(counter)


def test_profiles_header_uses_the_approved_russian_three_schema_wording():
    client = make_test_client(app)
    response = client.get("/profiles", headers={"accept-language": "ru"})
    soup = BeautifulSoup(response.text, "html.parser")

    versions = soup.select_one("[data-supported-firefox-versions]")

    assert versions is not None
    assert versions.get_text(" ", strip=True).replace(" ,", ",") == (
        "Поддерживаемые схемы Firefox: релиз 153, ESR 153.0, ESR 140.13, ESR 115.39"
    )


def test_profiles_header_uses_comma_separated_schema_lists_without_css_separators():
    css = (REPO_ROOT / "app" / "static" / "profiles.css").read_text(encoding="utf-8")
    template = (REPO_ROOT / "app" / "templates" / "profiles" / "_page_header.html").read_text(
        encoding="utf-8"
    )

    assert 'content: "·"' not in css
    assert "{% if not loop.last %}, {% endif %}" in template
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        catalog = json.loads(
            (REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        expected = " ".join(
            (
                catalog["profiles.supported_firefox_versions"],
                ", ".join(
                    catalog[key]
                    for key in (
                        "profiles.firefox_schema_release_153",
                        "profiles.firefox_schema_esr_153_0",
                        "profiles.firefox_schema_esr_140_13",
                        "profiles.firefox_schema_esr_115_39",
                    )
                ),
            )
        )

        assert expected.count(",") == 3


def test_profiles_theme_color_matches_the_product_light_surface():
    response = _profiles_page_response()
    head_bootstrap = (REPO_ROOT / "app" / "static" / "profiles_head_bootstrap.js").read_text(
        encoding="utf-8"
    )
    platform = (REPO_ROOT / "app" / "static" / "profiles_platform.js").read_text(encoding="utf-8")

    assert '<meta name="theme-color" content="#edf2f7"' in response.text
    assert 'resolvedTheme === "dark" ? "#07111a" : "#edf2f7"' in head_bootstrap
    assert 'resolvedTheme === "dark" ? "#07111a" : "#edf2f7"' in platform


def test_schema_conversion_surfaces_have_owned_responsive_focus_and_theme_styles():
    css = (REPO_ROOT / "app" / "static" / "profiles.css").read_text(encoding="utf-8")

    for selector in (
        ".library-conversion-recommendation",
        ".library-conversion-recommendation-action:focus-visible",
        ".schema-conversion-review-summary",
        '.schema-conversion-review-status[role="alert"]',
        'html[data-theme="dark"] .schema-conversion-review-status',
        "@media (forced-colors: active)",
        "@media (max-width: 820px)",
    ):
        assert selector in css


def test_json_profile_route_uses_local_monaco_assets():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Monaco Asset Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get("/profiles/new")
    response = client.get(f"/profiles/{profile_id}/json")

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' in response.text
    assert (
        '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v='
        not in guided_response.text
    )
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in guided_response.text
    assert '<script src="/static/vendor/monaco/vs/loader.js"></script>' not in response.text
    assert "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs" not in response.text


def test_profiles_page_uses_local_tailwind_stylesheet():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/vendor/profiles_tailwind.css?v=' in response.text
    assert "https://cdn.tailwindcss.com" not in response.text
    assert "tailwind.config =" not in response.text


def test_profiles_page_uses_local_bootstrap_assets_without_inline_scripts():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-guided.js?v=' in response.text
    )
    assert '<script id="profiles-initial-locale" type="application/json">' in response.text
    assert "<script>" not in response.text
    assert "window.__BPM_INITIAL_LANG__ =" not in response.text
    assert "window.__BPM_INITIAL_LOCALE__ =" not in response.text


def test_existing_profile_routes_embed_initial_profile_payload():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name="Initial Profile Embed Contract",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        ),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")

    assert response.status_code == 200
    assert '<script id="profiles-initial-profile" type="application/json">' in response.text
    assert '"name": "Initial Profile Embed Contract"' in response.text
    assert '"schema_version": "release-153"' in response.text
    assert '"DisableTelemetry": true' in response.text

    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find(id="current-name").get_text(strip=True) == "Initial Profile Embed Contract"
    assert soup.find(id="save").get_text(strip=True) == "Save"
    assert soup.find(id="profile-name").get("value") == "Initial Profile Embed Contract"
    assert soup.find(id="current-meta").get_text(strip=True).startswith("#")


def test_esr_115_profile_is_selectable_and_schema_scoped_across_editor_surfaces():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name="ESR 115 editor surface contract",
            schema_version="esr-115.39",
            flags={"DisableTelemetry": True},
        ),
    )
    profile_id = create_response.json()["id"]

    library = client.get("/profiles")
    compare = client.get("/profiles/compare")
    guided = client.get(f"/profiles/{profile_id}/edit")
    settings = client.get(f"/profiles/{profile_id}/settings")
    json_editor = client.get(f"/profiles/{profile_id}/json")

    for response in (library, compare, guided, settings, json_editor):
        assert response.status_code == 200
        assert 'data-firefox-channel="esr-115.39"' in response.text
        assert "ESR 115.39" in response.text

    assert '<option value="esr-115.39"' in library.text
    assert 'id="schema-channels-catalog"' in compare.text
    assert '"schema_version": "esr-115.39"' in guided.text
    shell_catalog = json.loads(
        BeautifulSoup(guided.text, "html.parser").find(id="wizard-schema-shell-catalog").get_text()
    )
    esr_115_policy_ids = {
        item["id"]
        for step in shell_catalog["channels"]["esr-115.39"]["steps"].values()
        for bucket in ("recommended", "additional", "raw_fallback")
        for item in step[bucket]
    }
    assert len(esr_115_policy_ids) == 97
    assert "HttpsOnlyMode" not in esr_115_policy_ids
    assert 'id="settings-schema-shell-step-2"' in settings.text
    assert 'id="editor"' in json_editor.text


def test_profiles_library_page_uses_library_only_assets():
    client = make_test_client(app)

    response = client.get("/profiles")

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-library.js?v=' in response.text
    )
    assert 'id="schema-channels-catalog"' in response.text
    assert 'id="compare-profiles-link"' in response.text
    assert 'href="/profiles/compare"' in response.text
    assert 'target="_blank"' in response.text
    assert 'rel="noopener"' in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in response.text
    assert '<script src="/static/profiles_compare_state.js?v=' not in response.text
    assert '<script src="/static/profiles_compare.js?v=' not in response.text
    assert '<script src="/static/profiles_catalogs.js?v=' not in response.text
    assert '<script src="/static/profiles_page_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_runtime.js?v=' not in response.text
    assert '<script src="/static/profiles_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_guided.js?v=' not in response.text
    assert '<script src="/static/profiles_settings.js?v=' not in response.text
    assert '<script src="/static/profiles.js?v=' not in response.text
    assert 'id="wizard-starter-catalog"' not in response.text
    assert 'id="wizard-settings-catalog"' not in response.text
    assert 'id="wizard-preferences-catalog"' not in response.text
    assert 'id="wizard-manual-policy-controls"' not in response.text
    assert 'id="wizard-schema-shell-catalog"' not in response.text


def test_profiles_compare_page_uses_compare_only_assets():
    client = make_test_client(app)

    response = client.get("/profiles/compare")

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-compare.js?v=' in response.text
    )
    assert '<script id="compare-preferences-catalog" type="application/json">' in response.text
    assert 'id="schema-channels-catalog"' in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in response.text
    assert '<script src="/static/profiles_library_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_library.js?v=' not in response.text
    assert '<script src="/static/profiles_catalogs.js?v=' not in response.text
    assert '<script src="/static/profiles_workspace_state.js?v=' not in response.text
    assert '<script src="/static/profiles_workspace.js?v=' not in response.text
    assert '<script src="/static/profiles_runtime.js?v=' not in response.text
    assert '<script src="/static/profiles_guided.js?v=' not in response.text
    assert '<script src="/static/profiles_settings.js?v=' not in response.text
    assert '<script src="/static/profiles_json.js?v=' not in response.text


def test_profiles_compare_entrypoint_wires_route_locale_switching_contract():
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            'import * as platform from "./profiles_platform.js";',
            "const { resolveBrowserLanguage } = platform;",
            'const langStorageKey = "bpm-lang-mode";',
            'const langSelectEl = documentRef.getElementById("lang");',
            "function applyLocaleText(nextLocale)",
            'documentRef.querySelectorAll("[data-i18n]")',
            'documentRef.querySelectorAll("[data-i18n-placeholder]")',
            'documentRef.querySelectorAll("[data-i18n-title]")',
            'documentRef.querySelectorAll("[data-i18n-aria-label]")',
            "const res = await windowRef.fetch(`/i18n/${lang}.json`);",
            "windowRef.__BPM_INITIAL_LANG__ = lang;",
            "windowRef.__BPM_INITIAL_LOCALE__ = nextLocale;",
            "updateDocumentationLinks?.(documentRef, lang);",
            "async function applyLanguageMode(mode, persist = true)",
            "resolveBrowserLanguage(windowRef.navigator, enabledLanguageModes)",
            "windowRef.localStorage.setItem(langStorageKey, normalizedMode);",
            'langSelectEl?.addEventListener("change", async (event) => {',
            "await applyLanguageMode(event.target.value);",
        ),
    )


def test_profiles_compare_entrypoint_wires_route_theme_switching_contract():
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            "const { resolveTheme, updateThemeColorMeta, syncThemeSensitiveControls } = platform;",
            'const themeStorageKey = "bpm-theme-mode";',
            'const themeSelectEl = documentRef.getElementById("theme");',
            "function applyThemeMode(mode, persist = true)",
            'const normalizedMode = ["system", "light", "dark"].includes(mode) ? mode : "system";',
            "const resolvedTheme = resolveTheme(",
            "documentRef.documentElement.dataset.themeMode = normalizedMode;",
            "documentRef.documentElement.dataset.theme = resolvedTheme;",
            "updateThemeColorMeta(documentRef, resolvedTheme);",
            "syncThemeSensitiveControls?.(documentRef, resolvedTheme);",
            "windowRef.localStorage.setItem(themeStorageKey, normalizedMode);",
            'themeSelectEl?.addEventListener("change", (event) => {',
            "applyThemeMode(event.target.value);",
            'const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";',
            "themeSelectEl.value = savedThemeMode;",
            "applyThemeMode(savedThemeMode, false);",
        ),
    )


def test_profiles_compare_preserves_library_language_and_theme_modes_contract():
    source = static_source("profiles_compare.js")
    library_source = static_source("profiles_library_bootstrap.js")
    client = make_test_client(app)
    response = client.get("/profiles")

    assert 'id="compare-profiles-link"' in response.text
    assert 'href="/profiles/compare"' in response.text
    assert 'target="_blank"' in response.text
    assert 'const langStorageKey = "bpm-lang-mode";' in library_source
    assert 'const langStorageKey = "bpm-lang-mode";' in source
    assert 'const themeStorageKey = "bpm-theme-mode";' in library_source
    assert 'const themeStorageKey = "bpm-theme-mode";' in source
    assert 'windowRef.localStorage.getItem(langStorageKey) || "system"' in source
    assert 'windowRef.localStorage.getItem(themeStorageKey) || "system"' in source
    assert "langSelectEl.value = savedLangMode;" in source
    assert "themeSelectEl.value = savedThemeMode;" in source
    assert "await applyLanguageMode(savedLangMode, false);" in source
    assert "applyThemeMode(savedThemeMode, false);" in source
    assert "renderCompareTable();" in source


def test_profiles_compare_persists_language_and_theme_for_library_return_contract():
    source = static_source("profiles_compare.js")
    library_source = static_source("profiles_library_bootstrap.js")

    assert_source_contains_all(
        source,
        (
            'langSelectEl?.addEventListener("change", async (event) => {',
            "await applyLanguageMode(event.target.value);",
            'themeSelectEl?.addEventListener("change", (event) => {',
            "applyThemeMode(event.target.value);",
            "async function applyLanguageMode(mode, persist = true)",
            "function applyThemeMode(mode, persist = true)",
            "windowRef.localStorage.setItem(langStorageKey, normalizedMode);",
            "windowRef.localStorage.setItem(themeStorageKey, normalizedMode);",
            'const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || "system";',
            'const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";',
        ),
    )
    assert_source_contains_all(
        library_source,
        (
            'const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || "system";',
            'const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";',
            "await applyLanguageMode(savedLangMode, false);",
            "applyThemeMode(savedThemeMode, false);",
        ),
    )


def test_profiles_compare_selector_options_split_name_schema_and_timestamp_contract():
    source = static_source("profiles_compare.js")
    css = css_source()
    template = template_source("_page_compare_workspace.html")

    assert_source_contains_all(
        source,
        (
            "function renderProfileOption(profile, sideState, side)",
            'button.className = "compare-profile-option',
            'button.setAttribute("data-compare-profile-option", "true");',
            'nameEl.setAttribute("data-compare-profile-name", "");',
            'schemaEl.setAttribute("data-compare-profile-schema", "");',
            'updatedEl.setAttribute("data-compare-profile-updated", "");',
            "formatProfileSchema(profile, utils.formatSchemaLabel)",
            "formatProfileUpdatedAt(profile)",
            "button.append(",
            "compare-selected-profile--active",
            "compare-selected-profile__name",
            "compare-selected-profile__meta",
        ),
    )
    assert_source_contains_all(
        css,
        (
            ".compare-profile-option {",
            ".compare-profile-option__name {",
            ".compare-profile-option__meta {",
            ".compare-profile-option__schema {",
            ".compare-profile-option__updated {",
            ".compare-selected-profile {",
            ".compare-selected-profile__name {",
            ".compare-selected-profile__meta",
            ".compare-selected-profile__empty {",
            "column-gap:",
        ),
    )
    assert 'class="compare-selected-profile mt-3"' in template
    assert 'class="mt-3 compact-counter"' not in template


def test_compare_schema_labels_use_the_read_only_catalog_and_active_locale_contract():
    compare_shell = template_source("_compare_shell.html")
    utils_source = static_source("profiles_utils.js")

    assert 'id="schema-channels-catalog"' in compare_shell
    assert "catalog.options.find((option) => option?.value === value)" in utils_source
    assert "window.__BPM_INITIAL_LOCALE__" in utils_source


def test_profiles_compare_selector_results_are_bounded_scroll_containers_contract():
    template = template_source("_page_compare_workspace.html")
    source = static_source("profiles_compare.js")
    css = css_source()

    assert_source_contains_all(
        template,
        (
            'id="compare-left-results"',
            'id="compare-right-results"',
            'class="compare-profile-results',
            'data-compare-results-list="left"',
            'data-compare-results-list="right"',
        ),
    )
    assert_source_contains_all(
        source,
        (
            "resultsEl.dataset.compareResultsCount = String(sideState.items.length);",
            'resultsEl.classList.toggle("compare-profile-results--overflow", sideState.items.length >',
            "sideState.items.slice(0,",
            "button.classList.add",
            '"compare-profile-option"',
            "compareProfileResultsLimit",
            "limit: compareProfileResultsLimit",
        ),
    )
    assert (
        'if (resolvedFilters.limit) url.searchParams.set("limit", String(resolvedFilters.limit));'
        in static_source("profiles_data.js")
    )
    assert_source_contains_all(
        css,
        (
            ".compare-profile-results {",
            "max-height:",
            "overflow-y: auto;",
            "overscroll-behavior: contain;",
            ".compare-profile-results--overflow {",
            ".compare-profile-option {",
            "min-height:",
        ),
    )


def test_profiles_compare_table_setting_identity_avoids_duplicate_key_contract():
    source = static_source("profiles_compare.js")
    css = css_source()

    assert_source_contains_all(
        source,
        (
            "function renderSettingIdentity(compareRow)",
            "data-compare-setting-label",
            "data-compare-setting-key",
            "if (compareRow.settingKey && compareRow.settingKey !== compareRow.label)",
            "renderSettingIdentity(compareRow)",
        ),
    )
    assert_source_contains_all(
        css,
        (
            ".compare-setting-cell__kind {",
            ".compare-setting-cell__label {",
            ".compare-setting-cell__meta {",
        ),
    )


def test_profiles_compare_entrypoint_wires_profile_search_and_selection_contract():
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            "buildProfileSearchFilters(sideState.query)",
            'lifecycle: "active"',
            "data.listProfiles(",
            "data.getProfile(profileId, windowRef.fetch, false)",
            "documentRef.getElementById(`compare-${side}-search`)",
            "documentRef.getElementById(`compare-${side}-results`)",
            "documentRef.getElementById(`compare-${side}-profile`)",
            'data-compare-results-state="loading"',
            'data-compare-results-state="error"',
            'data-compare-results-state="empty"',
            "button.dataset.compareProfileId = String(profile.id);",
            'button.setAttribute("role", "option");',
            'button.setAttribute("aria-selected", selected ? "true" : "false");',
            'elements[side]?.search?.addEventListener("input", () => scheduleLoad(side));',
            'elements[side]?.results?.addEventListener("click", (event) => {',
            "selectProfileForSide(side, profileId);",
            "loadProfilesForSide(side);",
            "resolvePreselectedProfileIds(windowRef.location)",
            "preselectProfileForSide(side, preselectedIds[side]);",
            "function buildCompareRows(leftProfile, rightProfile, compareStateAdapter = compareState",
            "compareStateAdapter.collectProfileSettingKeys(leftFlags, rightFlags)",
            "compareStateAdapter.readSettingValue(leftFlags, rowKey)",
            "renderCompareTable();",
            "row.dataset.compareRowId = compareRow.id;",
            'data-compare-column="left"',
            'data-compare-column="right"',
            'const preferencesCatalog = readEmbeddedJson(documentRef, "compare-preferences-catalog");',
            "buildPreferenceLabelLookup(preferencesCatalog, locale)",
            "resolveSettingPresentation(rowKey, options)",
            'data-compare-setting-kind="${escapeHtml(compareRow.kind)}"',
            'preferenceKindLabel: t("profiles.compare_kind_preference")',
            'policyKindLabel: t("profiles.compare_kind_policy")',
            "stateLabels: {",
            'class="compare-value-cell compare-value-cell--${compareRow.left.state}',
            'data-compare-value-state-label="${compareRow.left.state}"',
            "${escapeHtml(compareRow.left.stateLabel)}",
            'class="compare-value-code"',
        ),
    )


def test_profiles_compare_route_reuses_existing_profile_api_contract():
    source = static_source("profiles_compare.js")
    api_source = (REPO_ROOT / "app" / "api" / "profiles.py").read_text(encoding="utf-8")

    assert 'new URL("/api/profiles", locationRef.origin)' in static_source("profiles_data.js")
    assert "fetchImpl(`/api/profiles/${id}${suffix}`)" in static_source("profiles_data.js")
    assert "/api/profiles/compare" not in source
    assert "/api/profiles/compare" not in api_source
    assert 'router = APIRouter(prefix="/api/profiles", tags=["profiles"])' in api_source


def test_profiles_editor_modes_use_mode_specific_entrypoints():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Mode Entrypoint Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get("/profiles/new")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    assert guided_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-guided.js?v='
        in guided_response.text
    )
    assert "profile-settings.js?v=" not in guided_response.text
    assert (
        '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v='
        not in guided_response.text
    )
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in guided_response.text
    assert "profile-library.js?v=" not in guided_response.text
    assert '<script src="/static/profiles_compare_state.js?v=' not in guided_response.text
    assert '<script src="/static/profiles.js?v=' not in guided_response.text
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-settings.js?v='
        in settings_response.text
    )
    assert "profile-guided.js?v=" not in settings_response.text
    assert (
        '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v='
        not in settings_response.text
    )
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in settings_response.text
    assert '<script src="/static/profiles_compare_state.js?v=' not in settings_response.text
    assert (
        '<script type="module" src="/static/profiles_bundles/profile-json.js?v='
        in json_response.text
    )
    assert "profile-guided.js?v=" not in json_response.text
    assert "profile-settings.js?v=" not in json_response.text
    assert "profile-library.js?v=" not in json_response.text
    assert '<script src="/static/profiles_compare_state.js?v=' not in json_response.text
    assert '<script src="/static/profiles.js?v=' not in json_response.text


def test_profiles_editor_modes_do_not_load_compare_entrypoints_or_hidden_compare_assets():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Editor Compare Asset Boundary Profile"),
    )
    profile_id = create_response.json()["id"]

    responses = (
        client.get("/profiles/new"),
        client.get(f"/profiles/{profile_id}/edit"),
        client.get(f"/profiles/{profile_id}/settings"),
        client.get(f"/profiles/{profile_id}/json"),
    )

    forbidden = (
        "profile-compare.js?v=",
        '<script id="compare-preferences-catalog" type="application/json">',
        'data-profiles-route-mode="compare"',
        'data-profiles-template-kind="compare"',
        'id="compare-page"',
        'id="compare-settings-table"',
        'id="compare-left-search"',
        'id="compare-right-search"',
    )
    for response in responses:
        assert response.status_code == 200
        assert_source_excludes_all(response.text, forbidden)


def test_profiles_page_uses_request_locale_for_initial_render():
    client = make_test_client(app)

    response = client.get(
        "/profiles",
        headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
    )

    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    assert "Библиотека" in response.text
    assert "Browser Policy Manager" in response.text
    assert "Поиск по имени профиля" in response.text
    assert "Сравнение двух профилей" not in response.text
    assert "Пошаговый мастер" not in response.text
    assert "Search engine" not in response.text
    assert "Engine name" not in response.text
    assert "Search URL template" not in response.text
    assert "Required for a valid engine" not in response.text
    assert "Privacy and user data" not in response.text
    assert "Sync and Firefox Accounts" not in response.text
    assert "Homepage and startup" not in response.text
    assert "Controls in this area" not in response.text
    assert "Top-level policies" not in response.text
    assert "Control Room" not in response.text


def test_profiles_header_documentation_link_is_six_locale_and_runtime_locale_aware(
    tmp_path,
    monkeypatch,
):
    _write_packaged_site(tmp_path)
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = make_test_client(app)
    expected_labels = {
        "en": "Open product documentation",
        "ru": "Открыть документацию",
        "de": "Produktdokumentation öffnen",
        "zh-CN": "打开产品文档",
        "fr": "Ouvrir la documentation produit",
        "es-ES": "Abrir documentación del producto",
    }

    for locale, label in expected_labels.items():
        locale_json = client.get(f"/i18n/{locale}.json").json()
        assert locale_json["profiles.documentation_link"] == label
        for key in (
            "profiles.help_policy_ai_controls",
            "profiles.help_policy_visual_search_enabled",
            "profiles.help_cis_baseline_selection",
            "profiles.help_validation",
            "profiles.help_import_firefox_policies",
            "profiles.help_export_firefox_policies",
        ):
            assert locale_json[key]
            assert locale_json[key] != locale_json["profiles.context_help_action"]

    response = client.get(
        "/profiles",
        headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
    )
    header_template = template_source("_page_header.html")
    platform_source = static_source("profiles_platform.js")
    library_source = static_source("profiles_library_bootstrap.js")
    runtime_source = static_source("profiles_runtime.js")
    compare_source = static_source("profiles_compare.js")

    try:
        assert response.status_code == 200
        assert 'href="/help/ru/index.html"' in response.text
        assert '"/help/en/index.html"' in response.text
        assert '"/help/de/index.html"' in response.text
        assert 'target="_blank"' in response.text
        assert 'rel="noopener noreferrer"' in response.text
    finally:
        get_settings.cache_clear()

    assert_source_contains_all(
        header_template,
        (
            "{% if documentation_home_href %}",
            'href="{{ documentation_home_href }}"',
            'target="_blank"',
            'rel="noopener noreferrer"',
            'data-i18n="profiles.documentation_link"',
            "data-documentation-links",
            "data-documentation-link",
        ),
    )
    assert_source_contains_all(
        platform_source,
        (
            "function updateDocumentationLinks(documentRef, lang)",
            'documentRef.querySelectorAll("[data-documentation-link]")',
            'JSON.parse(linkEl.dataset.documentationLinks || "{}")',
            'linkEl.setAttribute("href", href);',
        ),
    )
    for source in (library_source, runtime_source, compare_source):
        assert "updateDocumentationLinks?.(documentRef, lang);" in source


def test_profiles_documentation_links_remain_visible_for_stale_dev_artifact(
    tmp_path,
    monkeypatch,
):
    _write_packaged_site(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact"]["bpm_version"] = "0.8.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = make_test_client(app)

    try:
        response = client.get(
            "/profiles",
            headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    header_link = soup.find("a", {"class": "compact-toolbar-docs-link"})
    import_link = soup.find("a", {"data-context-help-target": "import-firefox-policies"})

    assert header_link is not None
    assert import_link is not None
    assert header_link["href"] == "/help/?locale=ru"
    assert import_link["href"] == "/help/?locale=ru"
    assert '"/help/?locale=en"' in header_link["data-documentation-links"]
    assert '"/help/?locale=zh-CN"' in import_link["data-documentation-links"]


def test_profiles_contextual_help_links_resolve_from_manifest_for_five_surfaces(
    tmp_path,
    monkeypatch,
):
    _write_packaged_site(tmp_path)
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = make_test_client(app)
    profile_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Contextual Help Target Profile"),
    )
    profile_id = profile_response.json()["id"]
    routes = {
        "/profiles/compare": ("compare", "ug-task-compare-profiles"),
        "/profiles/new": ("guided", "ug-task-use-guided-editor"),
        f"/profiles/{profile_id}/settings": ("settings", "ug-task-use-all-settings"),
        f"/profiles/{profile_id}/json": ("json", "ug-task-use-json-editor"),
    }

    try:
        for route, (surface, topic_id) in routes.items():
            response = client.get(route)
            assert response.status_code == 200
            assert f'data-context-help-surface="{surface}"' in response.text
            assert f'href="/help/en/user/{topic_id}.html"' in response.text
            assert 'data-i18n="profiles.context_help_action"' in response.text
            assert "data-documentation-link" in response.text
            assert 'target="_blank"' in response.text
            assert 'rel="noopener noreferrer"' in response.text
    finally:
        get_settings.cache_clear()


def test_profiles_deep_help_icon_links_resolve_from_manifest_targets(
    tmp_path,
    monkeypatch,
):
    _write_packaged_site(tmp_path)
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = make_test_client(app)
    profile_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Deep Help Target Profile"),
    )
    profile_id = profile_response.json()["id"]
    routes = {
        "/profiles": {
            "import-firefox-policies": (
                "/help/en/user/ug-task-import-policies-json.html",
                "Open help for importing Firefox policies.json",
            ),
        },
        "/profiles/new": {
            "policy-ai-controls": (
                "/help/en/firefox/fx-concept-complex-policy-families.html#a-privacy-ai",
                "Open help for Firefox AI policy controls",
            ),
            "policy-visual-search-enabled": (
                "/help/en/firefox/fx-concept-complex-policy-families.html#a-privacy-ai",
                "Open help for the VisualSearchEnabled policy",
            ),
            "cis-baseline-selection": (
                "/help/en/cis/cis-settings-guide.html#a-cis-settings-guide",
                "Open help for selecting CIS baselines",
            ),
            "validation": (
                "/help/en/user/ug-task-validate-profile.html",
                "Open help for profile validation",
            ),
            "export-firefox-policies": (
                "/help/en/user/ug-task-export-policies-json.html",
                "Open help for exporting Firefox policies.json",
            ),
        },
        f"/profiles/{profile_id}/json": {
            "validation": (
                "/help/en/user/ug-task-validate-profile.html",
                "Open help for profile validation",
            ),
            "export-firefox-policies": (
                "/help/en/user/ug-task-export-policies-json.html",
                "Open help for exporting Firefox policies.json",
            ),
        },
    }

    try:
        for route, expected_links in routes.items():
            response = client.get(route)
            assert response.status_code == 200
            soup = BeautifulSoup(response.text, "html.parser")
            for target_id, (href, title) in expected_links.items():
                link = soup.find(
                    "a",
                    {
                        "class": "context-help-icon-link",
                        "data-context-help-target": target_id,
                    },
                )
                assert link is not None, f"{target_id} not rendered on {route}"
                assert link.get_text(strip=True) == "i"
                assert link["href"] == href
                assert link["target"] == "_blank"
                assert link["rel"] == ["noopener", "noreferrer"]
                assert link["title"] == title
                assert link["aria-label"] == title
                assert link["data-documentation-link"] == ""
                assert '"/help/ru/' in link["data-documentation-links"]
    finally:
        get_settings.cache_clear()


def test_all_settings_route_embeds_manifest_resolved_row_help_links(tmp_path, monkeypatch):
    _write_packaged_site(tmp_path)
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        with make_test_client(app) as client:
            profile_response = client.post(
                "/api/profiles",
                json=build_profile_payload(name="All Settings Row Help Profile"),
            )
            profile_id = profile_response.json()["id"]
            response = client.get(f"/profiles/{profile_id}/settings")
            library = client.get("/profiles")
            assert response.status_code == 200
            soup = BeautifulSoup(response.text, "html.parser")
            payload = json.loads(soup.find(id="all-settings-row-help-links").get_text())
            status = json.loads(soup.find(id="all-settings-row-help-status").get_text())
            assert set(payload) == {
                "policy:AIControls",
                "policy:VisualSearchEnabled",
                "known-preference:browser.download.dir",
            }
            assert payload["known-preference:browser.download.dir"]["ru"].endswith(
                "/firefox/fx-reference-managed-preference-locking.html#a-safe-review"
            )
            assert status == "available"
            assert 'id="all-settings-row-help-links"' not in library.text
    finally:
        get_settings.cache_clear()


def test_all_settings_route_embeds_unavailable_status_without_links(tmp_path, monkeypatch):
    missing_site = tmp_path / "missing-docs"
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(missing_site))
    get_settings.cache_clear()

    try:
        with make_test_client(app) as client:
            profile_response = client.post(
                "/api/profiles",
                json=build_profile_payload(name="Unavailable Row Help Profile"),
            )
            response = client.get(f"/profiles/{profile_response.json()['id']}/settings")
        soup = BeautifulSoup(response.text, "html.parser")
        assert json.loads(soup.find(id="all-settings-row-help-links").get_text()) == {}
        assert json.loads(soup.find(id="all-settings-row-help-status").get_text()) == (
            "artifact_unavailable"
        )
    finally:
        get_settings.cache_clear()


def test_library_compare_copy_keys_are_removed_from_runtime_catalogs():
    for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN"):
        locale_json = json.loads(
            (REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )

        assert all(not key.startswith("profiles.library_compare_") for key in locale_json)
        assert "profiles.library_status_compare_first_selected" not in locale_json
        assert "profiles.library_status_compare_ready" not in locale_json


def test_resolve_request_locale_skips_unsupported_languages_and_bad_weights():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"pt-BR;q=1, ;q=0.9, ru;q=oops, en;q=0.5")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_uses_matrix_backed_regional_fallbacks(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            SUPPORTED_LOCALES=("en", "ru", "de", "zh-CN", "fr", "es-ES"),
            DEFAULT_LOCALE="en",
        ),
    )

    cases = (
        (b"de-AT,de;q=0.9,en;q=0.1", "de"),
        (b"fr-CA,fr;q=0.9,en;q=0.1", "fr"),
        (b"es-MX,es;q=0.9,en;q=0.1", "es-ES"),
        (b"zh-Hans-CN,zh;q=0.9,en;q=0.1", "zh-CN"),
    )
    for header, expected_locale in cases:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/profiles",
                "headers": [(b"accept-language", header)],
                "query_string": b"",
            }
        )
        assert reloaded._resolve_request_locale(request) == expected_locale


def test_resolve_request_locale_falls_back_to_active_catalog_for_target_only_locales(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_prefers_next_active_catalog_before_default_fallback(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,ru-RU;q=0.8,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "ru"


def test_load_locale_catalog_returns_empty_mapping_for_missing_locale(
    tmp_path,
    monkeypatch,
    reset_app_caches,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    reset_app_caches("locale_catalogs")
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            ROOT_DIR=tmp_path,
            I18N_DIR="i18n",
            SUPPORTED_LOCALES=("en", "ru"),
            TEMPLATES_DIR=web_profiles.settings.TEMPLATES_DIR,
        ),
    )

    assert reloaded._load_locale_catalog("de") == {}


def test_en_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/en.json")
    assert locale_response.status_code == 200
    assert locale_response.headers["content-type"].startswith("application/json")
    _assert_en_locale_catalog(locale_response.json())


def test_ru_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/ru.json")
    assert locale_response.status_code == 200
    _assert_ru_locale_catalog(locale_response.json())


def test_profiles_js_has_no_inline_english_fallback_copy():
    static_dir = REPO_ROOT / "app" / "static"
    fallback_pattern = re.compile(r'\bt\(\s*"profiles\.[^"]+"\s*,\s*"[^"]+"\s*\)')
    raw_status_pattern = re.compile(r"\b(?:setStatus|setDraftState|setValidationPreview)\(\s*[\"`]")
    confirm_fallback_pattern = re.compile(r'windowRef\.confirm\(\s*t\(\s*"profiles\.[^"]+"\s*,')

    fallback_hits: list[str] = []
    raw_status_hits: list[str] = []
    confirm_hits: list[str] = []

    for path in sorted(static_dir.glob("profiles*.js")):
        text = path.read_text(encoding="utf-8")
        if fallback_pattern.search(text):
            fallback_hits.append(path.name)
        if raw_status_pattern.search(text):
            raw_status_hits.append(path.name)
        if confirm_fallback_pattern.search(text):
            confirm_hits.append(path.name)

    assert not fallback_hits, f"inline translation fallbacks remain in: {fallback_hits}"
    assert not raw_status_hits, f"raw status strings remain in: {raw_status_hits}"
    assert not confirm_hits, f"confirm fallbacks remain in: {confirm_hits}"


def test_static_assets_are_served():
    client = make_test_client(app)
    settings = get_settings()

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"].startswith("image/x-icon")
    assert favicon_response.content == (settings.STATIC_DIR / "favicon.ico").read_bytes()


def test_static_vendor_monaco_assets_exist():
    vendor_root = REPO_ROOT / "app" / "static" / "vendor"
    bundle_path = vendor_root / "profiles_monaco.js"
    bundle_css_path = vendor_root / "profiles_monaco.css"
    editor_worker_path = vendor_root / "monaco-editor.worker.js"
    json_worker_path = vendor_root / "monaco-json.worker.js"
    codicon_font_path = vendor_root / "vendor" / "monaco-assets" / "codicon-KP4OV2OO.ttf"
    license_path = vendor_root / "monaco.LICENSE"

    assert bundle_path.is_file()
    assert bundle_css_path.is_file()
    assert editor_worker_path.is_file()
    assert json_worker_path.is_file()
    assert codicon_font_path.is_file()
    assert license_path.is_file()
    bundle_source = bundle_path.read_text(encoding="utf-8")
    assert "eval(" not in bundle_source
    assert re.search(r"\bnew\s+Function\s*\(", bundle_source) is None
    assert "/static/vendor/monaco-assets/codicon-KP4OV2OO.ttf" in bundle_css_path.read_text(
        encoding="utf-8"
    )
    assert "Microsoft Corporation" in license_path.read_text(encoding="utf-8")


def test_json_editor_runtime_uses_profile_loaded_status_and_custom_monaco_theme_contract():
    root = REPO_ROOT
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(encoding="utf-8")
    json_editor_source = (root / "app" / "static" / "profiles_runtime_json_editor.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")

    assert "function getMonacoThemeName(resolvedTheme)" in json_editor_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-light"' in json_editor_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-dark"' in json_editor_source
    assert (
        "windowRef.monaco.editor.setTheme(jsonEditorRuntime.getMonacoThemeName(resolvedTheme));"
        in runtime_source
    )
    assert "lineNumbersMinChars: 4" in runtime_source
    assert "lineDecorationsWidth: 18" in runtime_source
    assert 'vertical: "visible"' in runtime_source
    assert 'horizontal: "auto"' in runtime_source
    assert (
        'fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"'
        in runtime_source
    )
    assert (
        "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });"
        in runtime_source
    )
    assert (
        'setStatus(t("profiles.status_profile_loaded").replace("{name}", hydratedProfile.name), "success");'
        in runtime_source
    )
    assert "const { announceStatus = hasLibrarySurface } = options;" in workspace_source
    assert "syncLibrary = hasLibrarySurface" in workspace_source
    assert "announceLoaded = true" in workspace_source
    assert ".editor-frame .monaco-editor .margin-view-overlays .line-numbers {" in css_source
    assert ".editor-frame .monaco-scrollable-element > .scrollbar.vertical {" in css_source
    assert ".editor-frame .monaco-scrollable-element > .scrollbar > .slider {" in css_source


def test_static_vendor_tailwind_replacement_asset_exists():
    asset_path = REPO_ROOT / "app" / "static" / "vendor" / "profiles_tailwind.css"
    asset_text = asset_path.read_text(encoding="utf-8")

    assert asset_path.is_file()
    assert ".min-h-screen" in asset_text
    assert ".shadow-soft" in asset_text
    assert ".hover\\:bg-slate-50:hover" in asset_text


def test_static_profiles_bootstrap_assets_exist():
    static_root = REPO_ROOT / "app" / "static"
    head_bootstrap = static_root / "profiles_head_bootstrap.js"
    page_bootstrap = static_root / "profiles_page_bootstrap.js"
    compare_state = static_root / "profiles_compare_state.js"
    compare_entry = static_root / "profiles_compare.js"
    library_bootstrap = static_root / "profiles_library_bootstrap.js"
    route_entries = REPO_ROOT / "app" / "static_src" / "profile_bundle_entries"
    json_editor_runtime = static_root / "profiles_runtime_json_editor.js"
    dirty_guard_runtime = static_root / "profiles_runtime_dirty_guard.js"
    workspace_state = static_root / "profiles_workspace_state.js"
    review_state = static_root / "profiles_review_state.js"
    css_layer_root = static_root / "profiles_css"

    assert head_bootstrap.is_file()
    assert page_bootstrap.is_file()
    assert compare_state.is_file()
    assert compare_entry.is_file()
    assert library_bootstrap.is_file()
    assert {path.name for path in route_entries.glob("*.js")} == {
        "compare.js",
        "guided.js",
        "json.js",
        "library.js",
        "settings.js",
    }
    assert json_editor_runtime.is_file()
    assert dirty_guard_runtime.is_file()
    assert workspace_state.is_file()
    assert review_state.is_file()
    assert (css_layer_root / "00-foundation.css").is_file()
    assert (css_layer_root / "10-library.css").is_file()
    assert (css_layer_root / "20-shell.css").is_file()
    assert (css_layer_root / "21-settings.css").is_file()
    assert (css_layer_root / "22-guided-wizard.css").is_file()
    assert (css_layer_root / "23-workspace-editor.css").is_file()
    assert (css_layer_root / "24-theme-overrides.css").is_file()
    assert (css_layer_root / "30-responsive.css").is_file()
    assert (css_layer_root / "40-compact-shell.css").is_file()
    assert "window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);" in page_bootstrap.read_text(
        encoding="utf-8"
    )


def test_profiles_css_bundle_matches_source_layers():
    root = REPO_ROOT
    bundle_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")
    readme_source = (root / "app" / "static" / "profiles_css" / "README.md").read_text(
        encoding="utf-8"
    )

    assert bundle_source == build_profiles_css.build_css()
    assert "Generated by tools/build_profiles_css.py" in bundle_source
    assert "00-foundation.css" in readme_source
    assert "24-theme-overrides.css" in readme_source
    assert "40-compact-shell.css" in readme_source


def test_profiles_page_assets_are_declared_through_route_manifest():
    templates_root = REPO_ROOT / "app" / "templates" / "profiles"
    document_template = (templates_root / "_page_document.html").read_text(encoding="utf-8")
    manifest_template = (templates_root / "_page_route_assets.html").read_text(encoding="utf-8")

    assert '{% include "profiles/_page_route_assets.html" %}' in document_template
    assert document_template.count('{% include "profiles/_page_route_assets.html" %}') == 2
    assert (
        "{% set route_assets = profiles_frontend_assets.routes[profiles_route_mode] %}"
        in manifest_template
    )
    assert "profiles_frontend_assets.head_script" in manifest_template
    assert 'type="module"' in manifest_template
    assert "route_assets.scripts" in manifest_template
    assert "/static/profiles_" not in manifest_template
    assert "/static/profiles_bundles/" not in manifest_template
    assert (
        '<script src="/static/profiles_guided.js?v={{ asset_version }}"></script>'
        not in document_template
    )
    assert (
        '<script src="/static/profiles_settings.js?v={{ asset_version }}"></script>'
        not in document_template
    )
    assert (
        '<script src="/static/profiles_json.js?v={{ asset_version }}"></script>'
        not in document_template
    )


def test_web_profiles_module_wires_templates_and_route():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    profile_route_paths = {
        route.path for route in reloaded.router.routes if route.path.startswith("/profiles")
    }

    assert reloaded.templates.env.loader.searchpath == [str(reloaded.settings.TEMPLATES_DIR)]
    assert profile_route_paths == {
        "/profiles",
        "/profiles/compare",
        "/profiles/guided-compliance",
        "/profiles/new",
        "/profiles/{profile_id}/edit",
        "/profiles/{profile_id}/settings",
        "/profiles/{profile_id}/json",
    }
