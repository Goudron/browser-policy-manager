# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_guided_wizard_step_catalog_uses_eight_step_model():
    wizard_steps = get_wizard_steps()

    assert [(step["step"], step["id"]) for step in wizard_steps] == [
        (1, "browser_network_search"),
        (2, "urls_sites_navigation"),
        (3, "security_privacy"),
        (4, "certificates_trust"),
        (5, "users_language_sync"),
        (6, "extensions"),
        (7, "ai"),
        (8, "review_export"),
    ]
    assert [step["label_fallback"] for step in wizard_steps] == [
        "Browser, network & search",
        "URLs, sites & navigation",
        "Security & privacy",
        "Certificates & trust",
        "Users, language & sync",
        "Extensions",
        "AI",
        "Review & export",
    ]
    assert wizard_steps[-1]["progress_fallback"] == "Step 8 of 8: Review & export"


def test_guided_wizard_stepper_renders_eight_navigation_steps_and_starts_at_browser():
    response = _profiles_page_response()

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    soup = BeautifulSoup(response.text, "html.parser")
    step_buttons = soup.select("#wizard-stepper .wizard-step")

    assert [(button.get("data-step"), button.get("data-step-id")) for button in step_buttons] == [
        ("1", "browser_network_search"),
        ("2", "urls_sites_navigation"),
        ("3", "security_privacy"),
        ("4", "certificates_trust"),
        ("5", "users_language_sync"),
        ("6", "extensions"),
        ("7", "ai"),
        ("8", "review_export"),
    ]
    assert soup.select_one('#wizard-stepper .wizard-step[data-step="1"]')["aria-current"] == "step"
    assert soup.select_one('#wizard-step-1[data-wizard-step-id="browser_network_search"]')
    assert soup.select_one('#wizard-step-8[data-wizard-step-id="review_export"]')


def test_guided_stepper_is_a_named_navigation_landmark_with_overflow_safe_labels():
    response = _profiles_page_response()
    css = css_source()
    flow = static_source("profiles_wizard_flow.js")

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    stepper = soup.select_one("nav#wizard-stepper")
    assert stepper is not None
    assert stepper.get("aria-label")
    assert len(stepper.select(".wizard-step")) == 8
    assert ".wizard-step-label {" in css
    assert "overflow-wrap: anywhere;" in css
    assert "hyphens: auto;" in css
    assert "overscroll-behavior-inline: contain;" in css
    assert "scrollbar-gutter: stable;" in css
    assert 'const stepperEl = activeStepButton?.closest?.(".wizard-stepper");' in flow
    assert "stepperEl.scrollWidth > stepperEl.clientWidth" in flow
    assert "stepperEl.scrollTo({" in flow
    assert "left: Math.max(0, Math.min(targetLeft, maxScrollLeft))," in flow


def test_profiles_page_locale_picker_displays_target_locale_metadata():
    response = _profiles_page_response()
    soup = BeautifulSoup(response.text, "html.parser")
    lang_select = soup.find(id="lang")
    options = {option.get("value"): option for option in lang_select.find_all("option")}

    assert list(options) == ["system", "en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert options["en"].get_text(strip=True) == "English"
    assert options["ru"].get_text(strip=True) == "Русский"
    assert options["de"].get_text(strip=True) == "Deutsch"
    assert options["zh-CN"].get_text(strip=True) == "简体中文"
    assert options["fr"].get_text(strip=True) == "Français"
    assert options["es-ES"].get_text(strip=True) == "Español"
    assert options["zh-CN"]["data-locale-bcp47"] == "zh-CN"
    assert options["es-ES"]["data-locale-code"] == "es-ES"

    assert options["en"]["data-locale-has-catalog"] == "true"
    assert options["ru"]["data-locale-has-catalog"] == "true"
    assert options["de"]["data-locale-has-catalog"] == "true"
    assert options["zh-CN"]["data-locale-has-catalog"] == "true"
    assert options["fr"]["data-locale-has-catalog"] == "true"
    assert options["es-ES"]["data-locale-has-catalog"] == "true"
    assert not options["de"].has_attr("disabled")
    assert not options["zh-CN"].has_attr("disabled")
    assert not options["fr"].has_attr("disabled")
    assert not options["es-ES"].has_attr("disabled")


def test_theme_safe_surface_cards_and_dark_white_override_contract():
    css = Path("app/static/profiles.css").read_text(encoding="utf-8")
    editor_template = Path("app/templates/profiles/_page_editor_chrome.html").read_text(
        encoding="utf-8"
    )
    settings_template = Path("app/templates/profiles/_page_settings_workspace.html").read_text(
        encoding="utf-8"
    )

    assert ".theme-subcard {" in css
    assert 'html[data-theme="dark"] .theme-subcard,' in css
    assert ".editor-chrome-panel {" in css
    assert 'html[data-theme="dark"] [class~="bg-white/80"]' in css
    assert 'html[data-theme="dark"] [class~="border-white/70"]' in css
    assert 'html[data-theme="dark"] [class~="border-slate-200"]' in css
    assert 'html[data-theme="dark"] [class~="decoration-slate-300"]' in css
    assert 'html[data-theme="dark"] [class~="hover:text-slate-900"]:hover' in css
    assert ".wizard-search-engine-preset:hover {" in css
    assert "background: var(--control-hover-bg);" in css
    assert "background: rgba(255, 255, 255, 0.86);" not in css
    assert "appearance: none;" in css
    assert "color-scheme: light;" in css
    assert "color-scheme: dark;" in css
    assert 'url("data:image/svg+xml,' in css
    assert "editor-chrome-status-item" not in editor_template
    assert 'id="profile-schema-fact"' in editor_template
    assert 'id="profile-type"' not in editor_template
    assert "theme-subcard" not in settings_template
    assert "data-settings-preferences-compat" in settings_template


def test_profiles_page_renders_editor_shell():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'data-profiles-route-mode="edit"' in response.text
    assert 'data-profiles-template-kind="editor"' in response.text
    assert_contains_all(
        response.text,
        (
            "Browser Policy Manager",
            "Guided editor",
            "All settings",
            "JSON editor",
            'id="overview-panel"',
            'id="wizard-panel"',
            'id="profile-name"',
            'id="profile-schema-fact"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="download-json"' not in response.text
    assert 'id="download-yaml"' not in response.text
    assert 'id="wizard-export-json"' not in response.text
    assert 'id="wizard-export-yaml"' not in response.text


def test_firefox_policies_import_and_final_export_ui_contract():
    client = make_test_client(app)
    library_response = client.get("/profiles")
    editor_response = _profiles_page_response()

    assert library_response.status_code == 200
    assert editor_response.status_code == 200
    assert 'id="import-firefox-policies"' in library_response.text
    assert 'id="import-firefox-policies-file"' in library_response.text
    assert 'accept=".json,application/json"' in library_response.text
    assert 'id="wizard-export-firefox-policies"' in editor_response.text

    removed_export_controls = (
        'id="download-json"',
        'id="download-yaml"',
        'id="wizard-export-json"',
        'id="wizard-export-yaml"',
        "Download JSON",
        "Download YAML",
        "Download files",
        "Скачать файлы",
    )
    for token in removed_export_controls:
        assert token not in library_response.text
        assert token not in editor_response.text

    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()
    assert en_catalog["profiles.wizard_export_ready_title"] == "Download policies.json"
    assert en_catalog["profiles.wizard_export_ready_saved"] == (
        "This saved version is ready for Firefox policies.json download."
    )
    assert ru_catalog["profiles.wizard_export_ready_title"] == "Скачать policies.json"
    assert ru_catalog["profiles.wizard_export_ready_saved"] == (
        "Эта сохранённая версия готова к скачиванию Firefox policies.json."
    )


def test_ai_wizard_presets_update_managed_policy_values():
    source = (REPO_ROOT / "app" / "static" / "profiles_extensions.js").read_text(encoding="utf-8")

    assert "function applyAiPosturePreset(presetKey)" in source
    assert "function isAiWizardAvailable()" in source
    assert "function hasUsableAiPolicyCard(policyCardEl)" in source
    assert 'setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"))' in source
    assert "normalized.AIControls = buildAiControlsValue(presetKey);" in source
    assert 'Value: "blocked"' in source
    assert 'Value: "available"' in source
    assert "SidebarChatbot" in source
    assert "SmartWindow" in source
    assert "normalized.VisualSearchEnabled = false" in source
    assert "profiles.wizard_ai_controls_active" in source
    assert "applyAiPosturePreset(presetKey);" in source


def test_ai_wizard_exposes_current_firefox_150_controls_in_standard_step():
    template = (
        REPO_ROOT / "app" / "templates" / "profiles" / "_page_wizard_step_ai.html"
    ).read_text(encoding="utf-8")

    assert 'id="wizard-ai-release-content" hidden' in template
    assert 'id="wizard-ai-policy-controls"' in template
    assert 'id="wizard-ai-esr-empty-state"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_title"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_body"' in template
    assert 'id="wizard-ai-map-title"' in template
    assert 'href="#wizard-step-7-posture"' in template
    assert 'href="#wizard-step-7-availability"' in template
    assert 'href="#wizard-step-7-surfaces"' in template
    assert 'id="wizard-ai-posture-presets"' in template
    assert 'id="wizard-ai-controls-card"' in template
    assert 'data-settings-target="policy:AIControls"' in template
    assert 'id="wizard-generative-ai-card"' in template
    assert 'data-settings-target="policy:GenerativeAI"' in template
    assert 'id="wizard-visual-search-enabled-card"' in template
    assert 'data-settings-target="policy:VisualSearchEnabled"' in template
    assert 'data-ai-outcome-group="feature-controls"' in template
    assert 'data-ai-outcome-group="generative-controls"' in template
    assert 'data-ai-outcome-group="surface-controls"' in template
    assert 'data-ai-posture-preset="providers"' not in template
    assert 'id="wizard-ai-fine-tuning-panel"' not in template


def test_final_step_renders_compact_cis_summary_without_full_decision_list():
    root = REPO_ROOT
    template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    source = (root / "app" / "static" / "profiles_review.js").read_text(encoding="utf-8")

    assert 'id="wizard-cis-final-summary"' in template
    assert "function renderCisFinalSummary(complianceInfo)" in source
    assert '["added_from_cis", "cis_replaced_base"]' in source
    assert '"already_satisfied"' in source
    assert '["kept_base_stricter", "kept_base_only"]' in source
    assert '"review_required"' in source
    assert "renderCisExceptionNotes(manualCisDecisions);" in source
    assert "renderCisExceptionNotes(complianceDecisions);" not in source


def test_profiles_page_renders_review_sections():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_REVIEW_TOKENS)


def test_profiles_page_renders_schema_export_footer_and_headers():
    current_year = datetime.now(UTC).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"

    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_SCHEMA_EXPORT_TOKENS)
    assert_contains_all(response.text, PROFILES_PAGE_FOOTER_TOKENS)
    assert footer_year_range in response.text
    assert 'data-i18n="profiles.footer_label"' not in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers


def test_default_wizard_path_does_not_render_guided_coverage_blocks():
    root = REPO_ROOT
    macro_source = (root / "app" / "templates" / "profiles" / "_wizard_macros.html").read_text(
        encoding="utf-8"
    )
    shell_source = (root / "app" / "static" / "profiles_schema_shell_sections.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")
    response = _profiles_page_response()

    assert response.status_code == 200
    assert 'id="wizard-guided-coverage-step-' not in response.text
    assert 'data-guided-coverage-open-step="' not in response.text
    assert 'class="wizard-guided-coverage surface-soft-box"' not in macro_source
    assert "renderWizardGuidedCoverage(" not in shell_source
    assert "data-guided-coverage-open-step" not in runtime_source
    assert "wizard-guided-coverage-step" not in dom_source
    assert ".wizard-guided-coverage" not in css_source
    assert 'id="wizard-schema-shell-step-2"' not in response.text
    assert 'id="wizard-schema-shell-step-8"' in response.text


def test_default_wizard_path_does_not_render_settings_map_blocks():
    root = REPO_ROOT
    response = _profiles_page_response()
    macro_source = (root / "app" / "templates" / "profiles" / "_wizard_macros.html").read_text(
        encoding="utf-8"
    )
    template_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            (root / "app" / "templates" / "profiles").glob("_page_wizard_step_*.html")
        )
    )
    settings_search_source = (root / "app" / "static" / "profiles_settings_search.js").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    assert 'id="wizard-settings-search-input"' in response.text
    assert 'id="wizard-settings-search-results"' in response.text
    assert 'id="wizard-settings-catalog"' in response.text
    assert 'data-settings-target="policy:DisableTelemetry"' in response.text
    assert 'data-settings-target="field:wizard-proxy-mode"' in response.text
    assert 'data-settings-target="search-engine-preset:duckduckgo"' in response.text

    removed_tokens = (
        'id="wizard-settings-map-',
        'id="wizard-settings-controls-',
        'id="wizard-preferences-general-groups"',
        'id="wizard-preferences-home-groups"',
        'id="wizard-preferences-search-groups"',
        'id="wizard-preferences-privacy-groups"',
        'id="wizard-preferences-sync-groups"',
        'id="wizard-preferences-general-controls"',
        'id="wizard-preferences-home-controls"',
        'id="wizard-preferences-search-controls"',
        'id="wizard-preferences-privacy-controls"',
        'id="wizard-preferences-sync-controls"',
        "data-settings-nav",
        "data-settings-jump-target",
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_settings_reference" not in macro_source
    assert "render_settings_reference(" not in template_sources
    assert "function renderResults()" in settings_search_source
    assert "function findTarget(targetKey)" in settings_search_source
    assert "button.dataset.settingsSearchTarget = entry.target;" in settings_search_source
    assert (
        'documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`)'
        in settings_search_source
    )
    assert (
        'documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`)'
        in settings_search_source
    )


def test_setup_step_has_no_editor_baseline_selection_state():
    root = REPO_ROOT
    response = _profiles_page_response()
    setup_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_setup.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(encoding="utf-8")

    assert response.status_code == 200
    assert 'id="wizard-step-1"' in response.text
    assert 'id="wizard-step-2"' in response.text
    assert (
        setup_template.strip()
        == '<section class="wizard-panel is-active" id="wizard-step-1">\n</section>'
    )

    removed_html_tokens = (
        'id="wizard-name"',
        'id="wizard-schema"',
        'id="wizard-mode"',
        "data-scenario-key",
        "data-starter-key",
        "data-cis-layer-key",
        "wizard-scenario-summary",
        "wizard-baseline-summary",
        "wizard-export-baseline",
        "wizard-summary-starter",
        "wizard-summary-cis",
    )
    for token in removed_html_tokens:
        assert token not in response.text
    for token in ("applyStarterPreset", "getWizardComplianceMergeInfo"):
        assert token not in flow_source


def test_step_one_preserves_actionable_browser_network_and_search_basics():
    root = REPO_ROOT
    response = _profiles_page_response()
    general_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_general.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(encoding="utf-8")
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-1-basics"',
        'id="wizard-general-policy-presets"',
        'data-general-policy-preset="updates"',
        'data-general-policy-preset="downloads"',
        'id="wizard-proxy-presets"',
        'data-proxy-preset="system"',
        'data-proxy-preset="autoConfig"',
        'data-settings-target="field:wizard-proxy-mode"',
        'id="wizard-dns-over-https-card"',
    )
    for token in core_tokens:
        assert token in response.text

    added_tokens = (
        'id="wizard-browser-defaults-map-title"',
        'href="#wizard-step-1-basics"',
        'href="#wizard-home-surface-startup"',
        'href="#wizard-step-1-default-search"',
        'href="#wizard-step-1-review"',
        'id="wizard-home-summary-homepage"',
        'id="wizard-search-summary-defaults"',
        'id="wizard-step-4-trust-posture"',
        'id="wizard-step-4-attribution"',
        'id="wizard-certificate-provenance-status"',
        'id="wizard-certificate-cis-status"',
        'id="wizard-certificate-system-trust"',
        'id="wizard-certificate-enterprise-roots"',
        'id="wizard-certificate-error-bypass"',
        'id="wizard-certificate-windows-sso"',
        'id="wizard-certificate-entra-sso"',
        'id="wizard-certificate-install-form"',
        'id="wizard-certificate-install-reference"',
        'id="wizard-certificate-authentication-form"',
        'id="wizard-certificate-authentication-field"',
        'id="wizard-certificate-authentication-locked"',
        'id="wizard-security-device-add-form"',
        'id="wizard-security-device-delete-form"',
        'id="wizard-security-devices-raw"',
    )
    for token in added_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-2"',
        'id="wizard-upkeep-governance-copy"',
        'id="wizard-trust-auth-workflow-copy"',
        'id="wizard-step-2-advanced-preferences"',
        'id="wizard-preferences-general-handoff-panel"',
        'data-general-preferences-focus="downloads"',
        'id="wizard-network-enterprise-presets"',
        'data-network-enterprise-preset="sso"',
        'data-network-enterprise-preset="roots"',
        'id="wizard-windows-sso-card"',
        'id="wizard-authentication-card"',
        'id="wizard-certificates-card"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(2)" not in general_template
    assert "wizardUpkeepGovernance" not in dom_source
    assert "wizardTrustAuthWorkflow" not in dom_source
    assert "renderUpkeepGovernanceWorkflow" not in network_source
    assert "renderTrustAuthWorkflow" not in network_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_two_contains_actionable_home_and_startup_sections():
    root = REPO_ROOT
    response = _profiles_page_response()
    home_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_home.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(encoding="utf-8")
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(encoding="utf-8")

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    core_tokens = (
        'id="wizard-home-surface-startup"',
        'id="wizard-homepage-presets"',
        'data-homepage-preset="portal"',
        'data-homepage-shared-preset="portal_locked"',
        'id="wizard-homepage-url"',
        'id="wizard-homepage-start-page"',
        'id="wizard-home-surface-new-tab"',
        'id="wizard-home-overrides-presets"',
        'id="wizard-new-tab-page"',
        'id="wizard-override-first-run"',
        'id="wizard-home-surface-firefox-home"',
        'id="wizard-firefox-home-presets"',
        'data-firefox-home-key="Search"',
        'data-firefox-home-key="TopSites"',
        'id="wizard-firefox-home-fine-tuning-toggle"',
        'id="wizard-firefox-home-fine-tuning-panel"',
    )
    for token in core_tokens:
        assert token in response.text

    for control_id in (
        "wizard-homepage-url",
        "wizard-homepage-additional",
        "wizard-homepage-start-page",
        "wizard-homepage-locked",
        "wizard-new-tab-page",
        "wizard-override-first-run",
        "wizard-override-post-update",
    ):
        control = soup.find(id=control_id)
        assert control is not None
        assert control.find_parent("section", {"data-wizard-step-id": "urls_sites_navigation"})
        assert not control.find_parent("section", {"data-wizard-step-id": "browser_network_search"})

    for selector in ('[data-firefox-home-key="Search"]', '[data-firefox-home-key="TopSites"]'):
        control = soup.select_one(selector)
        assert control is not None
        assert control.find_parent("section", {"data-wizard-step-id": "urls_sites_navigation"})

    removed_tokens = (
        'id="wizard-schema-shell-step-3"',
        'class="wizard-home-step-summary"',
        'id="wizard-home-surfaces-workflow-copy"',
        'id="wizard-home-summary-user-messaging"',
        'id="wizard-preferences-home-add"',
        'id="wizard-preferences-home-bundles"',
        'id="wizard-preferences-home-known"',
        'data-settings-target="pref-section:home"',
        'data-preference-section="home"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(3)" not in home_template
    assert "wizardHomeSurfacesWorkflow" not in dom_source
    assert "renderHomeSurfacesWorkflow" not in network_source
    assert (
        'renderPresetButtonState(homepagePresetButtons, resolveHomepagePreset(parsed), "homepagePreset");'
        in network_source
    )
    assert (
        'renderPresetButtonState(homeOverridesPresetButtons, resolveHomeOverridesPreset(parsed), "homeOverridesPreset");'
        in network_source
    )
    assert (
        'renderPresetButtonState(firefoxHomePresetButtons, resolveFirefoxHomePreset(parsed), "firefoxHomePreset");'
        in network_source
    )


def test_step_two_hosts_the_single_structured_website_filter_manager():
    root = REPO_ROOT
    response = _profiles_page_response()
    soup = BeautifulSoup(response.text, "html.parser")
    urls_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_urls.html"
    ).read_text(encoding="utf-8")
    sync_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_sync.html"
    ).read_text(encoding="utf-8")
    shell_source = (root / "app" / "static" / "profiles_schema_shell_sections.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(encoding="utf-8")

    assert response.status_code == 200
    for policy_id, holder_id in (
        ("WebsiteFilter", "wizard-website-filter-card"),
        ("AllowedDomainsForApps", "wizard-allowed-domains-for-apps-card"),
        ("HttpAllowlist", "wizard-http-allowlist-card"),
        ("LocalFileLinks", "wizard-local-file-links-card"),
    ):
        holder = soup.find(id=holder_id)
        assert holder is not None
        assert holder["data-settings-target"] == f"policy:{policy_id}"
        assert holder.find_parent("section", {"data-wizard-step-id": "urls_sites_navigation"})
        assert not holder.find_parent("section", {"data-wizard-step-id": "users_language_sync"})

    assert 'href="#wizard-site-access"' in urls_template
    assert 'data-settings-target="policy:WebsiteFilter"' not in sync_template
    assert "data-website-access-posture" not in sync_template
    for token in (
        'from "./profiles_modules/website_filter.mjs"',
        "function renderWebsiteFilterManager",
        "function appendWebsiteFilterRow",
        "function removeWebsiteFilterRow",
        "function moveWebsiteFilterRow",
        "function applyWebsiteFilterPostureFromCard",
        "data-website-filter-raw-fallback",
        'policyId: "WebsiteFilter", step: 2',
        'policyId: "AllowedDomainsForApps", step: 2',
        'policyId: "HttpAllowlist", step: 2',
        'policyId: "LocalFileLinks", step: 2',
    ):
        assert token in shell_source
    for token in (
        "[data-website-filter-pattern]",
        "[data-website-filter-add]",
        "[data-website-filter-remove]",
        "[data-website-filter-move]",
        "[data-website-filter-posture]",
    ):
        assert token in runtime_source


def test_url_navigation_inputs_use_one_lossless_validator_and_safe_external_link_boundary():
    root = REPO_ROOT
    validator_source = (
        root / "app" / "static" / "profiles_modules" / "navigation_url.mjs"
    ).read_text(encoding="utf-8")
    website_filter_source = (
        root / "app" / "static" / "profiles_modules" / "website_filter.mjs"
    ).read_text(encoding="utf-8")
    shell_source = (root / "app" / "static" / "profiles_schema_shell_sections.js").read_text(
        encoding="utf-8"
    )
    value_io_source = (root / "app" / "static" / "profiles_schema_shell_value_io.js").read_text(
        encoding="utf-8"
    )
    actions_source = (root / "app" / "static" / "profiles_schema_shell_actions.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(encoding="utf-8")

    for token in (
        "validateNavigationValue",
        "validateWebsiteFilterPattern",
        "getNavigationInputKind",
        "getSafeExternalLink",
        "retainsImportedRawNavigationValue",
        "DIRECTIONAL_OR_INVISIBLE_CHARACTER",
        'rel: "noopener noreferrer"',
        'referrerPolicy: "no-referrer"',
    ):
        assert token in validator_source
    assert 'from "./navigation_url.mjs"' in website_filter_source
    for source in (shell_source, value_io_source, actions_source, network_source):
        assert 'from "./profiles_modules/navigation_url.mjs"' in source
    for token in (
        "data-navigation-url-kind",
        "data-navigation-url-original",
        "data-navigation-url-raw-fallback",
        'target="${link.target}"',
        'rel="${link.rel}"',
        'referrerpolicy="${link.referrerPolicy}"',
    ):
        assert token in shell_source
    assert "readNavigationLines" in network_source
    assert "allowPipeList: true" in network_source


def test_step_one_preserves_actionable_search_sections():
    root = REPO_ROOT
    response = _profiles_page_response()
    search_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_search.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(encoding="utf-8")
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-1-default-search"',
        'id="wizard-search-defaults-presets"',
        'data-search-defaults-preset="managed_default"',
        'id="wizard-search-default-engine"',
        'id="wizard-search-defaults-section-status"',
        'id="wizard-step-1-managed-engines"',
        'id="wizard-search-engine-add"',
        'id="wizard-search-engine-list"',
        'data-search-engine-preset="duckduckgo"',
        'data-search-engine-field="Name"',
        'data-search-engine-field="URLTemplate"',
        'data-search-engine-field="Alias"',
        "data-search-engine-advanced",
        'data-search-engine-field="Method"',
        'data-search-engine-field="PostData"',
        'id="wizard-step-1-suggestions"',
        'id="wizard-firefox-suggest-presets"',
        'data-firefox-suggest-preset="private"',
        'data-firefox-suggest-key="WebSuggestions"',
        'id="wizard-firefox-suggest-section-status"',
        'id="wizard-search-suggest-fine-tuning-toggle"',
        'id="wizard-search-suggest-fine-tuning-panel"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-4"',
        'href="#wizard-step-4-default-search"',
        'id="wizard-step-4-review"',
        'id="wizard-search-surfaces-workflow-copy"',
        'id="wizard-step-4-advanced-preferences"',
        'id="wizard-preferences-search-handoff-panel"',
        'id="wizard-preferences-search-add"',
        'id="wizard-preferences-search-bundles"',
        'id="wizard-preferences-search-known"',
        'data-settings-target="pref-section:search"',
        'data-preference-section="search"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(4)" not in search_template
    assert "wizardSearchSurfacesWorkflow" not in dom_source
    assert "renderSearchSurfacesWorkflow" not in network_source
    assert (
        'renderPresetButtonState(searchDefaultsPresetButtons, resolveSearchDefaultsPreset(parsed), "searchDefaultsPreset");'
        in network_source
    )
    assert (
        'renderPresetButtonState(firefoxSuggestPresetButtons, resolveFirefoxSuggestPreset(parsed), "firefoxSuggestPreset");'
        in network_source
    )
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_three_default_path_is_actionable_privacy_and_protection():
    root = REPO_ROOT
    response = _profiles_page_response()
    privacy_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_privacy.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(encoding="utf-8")
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-hardening-presets"',
        'id="wizard-security-map-title"',
        'href="#wizard-step-3-posture"',
        'href="#wizard-step-3-cleanup"',
        'href="#wizard-step-3-site-data"',
        'href="#wizard-step-3-vpn"',
        'href="#wizard-step-3-review"',
        'data-hardening-preset="balanced"',
        'data-hardening-preset="strict"',
        'id="wizard-hardening-section-status"',
        'id="wizard-privacy-user-data-section-status"',
        'id="wizard-lockdown-section-status"',
        "data-hardening-cleanup-subchoice",
        'id="wizard-cleanup-presets"',
        'data-cleanup-preset="shared"',
        'data-cleanup-preset="strict"',
        'id="wizard-cleanup-section-status"',
        'id="wizard-privacy-site-section-status"',
        'id="wizard-site-data-presets"',
        'data-site-data-preset="balanced"',
        'data-site-data-preset="strict"',
        'id="wizard-site-data-fine-tuning-toggle"',
        'id="wizard-site-data-fine-tuning-panel"',
        'id="wizard-permissions-card"',
        'id="wizard-cookies-card"',
        'id="wizard-privacy-vpn-section-status"',
        'id="wizard-ip-protection-available-card"',
        'data-privacy-outcome-group="cookies-permissions"',
        'id="wizard-privacy-summary-user-data"',
        'id="wizard-privacy-summary-cleanup"',
        'id="wizard-privacy-summary-permissions"',
        'id="wizard-privacy-summary-cookies"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-5"',
        "data-hardening-impact-summary",
        'id="wizard-hardening-governance-workflow"',
        'id="wizard-hardening-governance-list"',
        'id="wizard-hardening-next-posture"',
        'data-hardening-subposture-menu="privacy"',
        'data-hardening-subposture-menu="lockdown"',
        'data-hardening-subposture-menu="site-data"',
        'id="wizard-privacy-user-data-presets"',
        'id="wizard-privacy-fine-tuning-panel"',
        'id="wizard-lockdown-presets"',
        'id="wizard-lockdown-fine-tuning-panel"',
        'data-privacy-outcome-group="telemetry"',
        'data-privacy-outcome-group="passwords-private-browsing"',
        'data-privacy-outcome-group="lockdown"',
        'id="wizard-preferences-privacy-add"',
        'id="wizard-preferences-privacy-bundles"',
        'id="wizard-preferences-privacy-known"',
        'data-settings-target="pref-section:privacy"',
        'data-preference-section="privacy"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(5)" not in privacy_template
    assert "render_outcome_policy_group" not in privacy_template
    assert "renderHardeningGovernanceWorkflow" not in flow_source
    assert "openHardeningGovernanceAdvanced" not in flow_source
    assert "wizard-hardening-next-posture" not in runtime_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_two_owns_managed_navigation_and_step_five_keeps_users_language_sync_only():
    root = REPO_ROOT
    response = _profiles_page_response()
    sync_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_sync.html"
    ).read_text(encoding="utf-8")
    urls_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_urls.html"
    ).read_text(encoding="utf-8")
    extensions_source = (root / "app" / "static" / "profiles_extensions.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-user-environment-map-title"',
        'href="#wizard-step-5-accounts"',
        'href="#wizard-step-5-language"',
        'id="wizard-step-5-accounts"',
        'id="wizard-sync-focus-presets"',
        'data-sync-focus-preset="accounts"',
        'id="wizard-sync-section-status"',
        'id="wizard-sync-fine-tuning-toggle"',
        'id="wizard-user-messaging-card"',
        'id="wizard-step-5-language"',
        'id="wizard-language-presets"',
        'data-language-preset="translation_off"',
        'id="wizard-requested-locales-card"',
        'id="wizard-translate-enabled-card"',
        'id="wizard-language-section-status"',
        'id="wizard-language-ai-handoff"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-language-governance-copy"',
        'id="wizard-language-governance-list"',
        'id="wizard-step-4-extensions"',
        'id="wizard-extension-governance-workflow"',
        'id="wizard-extension-governance-copy"',
        'id="wizard-extension-governance-list"',
        'id="wizard-extension-governance-open-settings"',
        'id="wizard-extension-summary-curated"',
        'id="wizard-bookmark-summary-links"',
        'id="wizard-website-access-summary-blocked"',
        'id="wizard-website-governance-workflow"',
        'id="wizard-website-governance-copy"',
        'id="wizard-website-governance-list"',
        'id="wizard-website-governance-open-settings"',
        'id="wizard-website-next-filter"',
        'id="wizard-website-next-handlers"',
    )
    for token in removed_tokens:
        assert token not in response.text

    for token in (
        'href="#wizard-site-access"',
        'id="wizard-site-access"',
        'id="wizard-website-filter-card"',
        'id="wizard-allowed-domains-for-apps-card"',
        'id="wizard-http-allowlist-card"',
        'id="wizard-local-file-links-card"',
        'href="#wizard-managed-navigation"',
        'id="wizard-managed-navigation"',
        'id="wizard-managed-navigation-toggle"',
        'id="wizard-managed-navigation-panel"',
        'id="wizard-handlers-card"',
        'id="wizard-auto-launch-protocols-card"',
        'id="wizard-intranet-navigation-card"',
        'id="wizard-bookmarks-card"',
        'id="wizard-managed-bookmarks-card"',
        'id="wizard-no-default-bookmarks-card"',
    ):
        assert token in urls_template
        assert token in response.text
    for token in (
        "wizard-step-4-bookmarks",
        "wizard-step-4-websites",
        "data-bookmarks-handoff",
        "wizard-website-access-handlers",
        "wizard-website-fine-tuning-toggle",
        'data-settings-target="policy:Handlers"',
    ):
        assert token not in sync_template

    assert "render_wizard_schema_shell(6)" not in sync_template
    assert "renderLanguageGovernanceWorkflow" not in extensions_source
    assert "renderExtensionGovernanceWorkflow" not in extensions_source
    assert "renderWebsiteGovernanceWorkflow" not in extensions_source
    assert "openWebsiteGovernanceAdvanced" not in extensions_source
    assert "openExtensionGovernanceAdvanced" not in extensions_source
    for stale_step_five_token in (
        "wizard-bookmarks-open-settings",
        "wizard-website-fine-tuning-toggle",
        "data-website-access-handlers",
        "shell-policy:5:Bookmarks",
        "shell-policy:5:ManagedBookmarks",
    ):
        assert stale_step_five_token not in extensions_source
    assert (
        '["wizard-managed-navigation-panel", "wizard-managed-navigation-toggle"]' in runtime_source
    )
    assert 'documentRef.getElementById("wizard-managed-navigation-toggle")' in runtime_source
    for policy_id in (
        "Handlers",
        "AutoLaunchProtocolsFromOrigins",
        "GoToIntranetSiteForSingleWordEntryInAddressBar",
        "Bookmarks",
        "ManagedBookmarks",
        "NoDefaultBookmarks",
    ):
        assert f'"{policy_id}",' in flow_source.split("3: [", 1)[0]


def test_step_six_is_the_single_guided_owner_for_extension_rules():
    root = REPO_ROOT
    response = _profiles_page_response()
    sync_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_sync.html"
    ).read_text(encoding="utf-8")
    extension_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_extensions.html"
    ).read_text(encoding="utf-8")

    assert response.status_code == 200
    for token in (
        'id="wizard-extension-rule-add-form"',
        'id="wizard-extension-rules"',
        'id="wizard-extension-raw-rules"',
        'id="wizard-extension-update"',
        'id="wizard-extension-install-default"',
        'id="wizard-extension-install-allow"',
        'id="wizard-extension-install"',
        'id="wizard-extension-locked"',
        'id="wizard-extension-uninstall"',
    ):
        assert token in extension_template
        assert token in response.text

    assert extension_template.count('data-wizard-step-id="extensions"') == 1
    assert "wizard-step-4-extensions" not in sync_template
    assert "wizard-extension-governance-presets" not in response.text
    assert "wizard-extension-default-mode" not in response.text


def test_profiles_page_preserves_final_guided_ux_contract():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_GUIDED_UX_REGRESSION_TOKENS)
    for retired_step_copy in (
        "Task-first setup",
        "Full visual catalog",
        "Raw policies.json editing",
    ):
        assert retired_step_copy not in response.text
