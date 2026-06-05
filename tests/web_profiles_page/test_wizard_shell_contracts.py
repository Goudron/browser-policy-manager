# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_guided_wizard_step_catalog_uses_six_step_model():
    wizard_steps = get_wizard_steps()

    assert [(step["step"], step["id"]) for step in wizard_steps] == [
        (1, "start"),
        (2, "browser_defaults"),
        (3, "privacy"),
        (4, "users_features"),
        (5, "ai"),
        (6, "review"),
    ]
    assert [step["label_fallback"] for step in wizard_steps] == [
        "Profile & baseline",
        "Browser access & defaults",
        "Security & privacy",
        "Users, add-ons & sites",
        "AI & smart features",
        "Review & export",
    ]
    assert wizard_steps[-1]["progress_fallback"] == "Step 6 of 6: Review & export"


def test_guided_wizard_stepper_renders_six_navigation_steps():
    client = make_test_client(app)
    response = client.get("/profiles/new")

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    step_buttons = soup.select("#wizard-stepper .wizard-step")

    assert [button.get("data-step") for button in step_buttons] == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ]
    assert soup.select_one('#wizard-stepper .wizard-step[data-step="7"]') is None
    assert soup.select_one('#wizard-stepper .wizard-step[data-step="8"]') is None


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
    editor_template = Path("app/templates/profiles/_page_editor_chrome.html").read_text(encoding="utf-8")
    settings_template = Path("app/templates/profiles/_page_settings_workspace.html").read_text(encoding="utf-8")

    assert ".theme-subcard {" in css
    assert 'html[data-theme="dark"] .theme-subcard,' in css
    assert ".editor-chrome-status-item {" in css
    assert 'html[data-theme="dark"] .editor-chrome-status-item,' in css
    assert 'html[data-theme="dark"] [class~="bg-white/80"]' in css
    assert 'html[data-theme="dark"] [class~="border-white/70"]' in css
    assert 'html[data-theme="dark"] [class~="border-slate-200"]' in css
    assert 'html[data-theme="dark"] [class~="decoration-slate-300"]' in css
    assert 'html[data-theme="dark"] [class~="hover:text-slate-900"]:hover' in css
    assert ".wizard-search-engine-preset:hover {" in css
    assert "background: rgba(255, 255, 255, 0.86);" in css
    assert "appearance: none;" in css
    assert "color-scheme: light;" in css
    assert "color-scheme: dark;" in css
    assert 'url("data:image/svg+xml,' in css
    assert editor_template.count("editor-chrome-status-item") >= 4
    assert settings_template.count("theme-subcard") >= 4


def test_profiles_page_renders_editor_shell():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'data-profiles-route-mode="new"' in response.text
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
            'id="profile-type"',
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
    source = (
        REPO_ROOT / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")

    assert "function applyAiPosturePreset(presetKey)" in source
    assert "function isAiWizardAvailable()" in source
    assert "function hasUsableAiPolicyCard(policyCardEl)" in source
    assert 'setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"))' in source
    assert 'normalized.AIControls = buildAiControlsValue(presetKey);' in source
    assert 'Value: "blocked"' in source
    assert 'Value: "available"' in source
    assert "SidebarChatbot" in source
    assert "SmartWindow" in source
    assert "normalized.VisualSearchEnabled = false" in source
    assert "profiles.wizard_ai_controls_active" in source
    assert "applyAiPosturePreset(presetKey);" in source


def test_ai_wizard_exposes_current_firefox_150_controls_in_standard_step():
    template = (
        REPO_ROOT
        / "app"
        / "templates"
        / "profiles"
        / "_page_wizard_step_ai.html"
    ).read_text(encoding="utf-8")

    assert 'id="wizard-ai-release-content" hidden' in template
    assert 'id="wizard-ai-policy-controls"' in template
    assert 'id="wizard-ai-esr-empty-state"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_title"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_body"' in template
    assert 'id="wizard-ai-map-title"' in template
    assert 'href="#wizard-step-5-posture"' in template
    assert 'href="#wizard-step-5-availability"' in template
    assert 'href="#wizard-step-5-surfaces"' in template
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
    source = (root / "app" / "static" / "profiles_review.js").read_text(
        encoding="utf-8"
    )

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
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    shell_source = (
        root / "app" / "static" / "profiles_schema_shell_sections.js"
    ).read_text(encoding="utf-8")
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
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
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    template_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "app" / "templates" / "profiles").glob("_page_wizard_step_*.html"))
    )
    settings_search_source = (
        root / "app" / "static" / "profiles_settings_search.js"
    ).read_text(encoding="utf-8")

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
        'data-settings-nav',
        'data-settings-jump-target',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_settings_reference" not in macro_source
    assert "render_settings_reference(" not in template_sources
    assert "function renderResults()" in settings_search_source
    assert "function findTarget(targetKey)" in settings_search_source
    assert "button.dataset.settingsSearchTarget = entry.target;" in settings_search_source
    assert 'documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`)' in settings_search_source
    assert 'documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`)' in settings_search_source


def test_setup_step_defaults_to_corporate_baseline_and_active_preset_states():
    root = REPO_ROOT
    response = _profiles_page_response()
    setup_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_setup.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    assert 'data-i18n="profiles.wizard_profile_identity_title"' in response.text
    assert 'id="wizard-name"' in response.text
    assert 'id="wizard-schema"' in response.text
    assert 'data-scenario-key="corporate_default" aria-pressed="true"' in response.text
    assert 'data-scenario-key="targeted_edits" aria-pressed="false"' in response.text
    assert 'data-starter-key="basic_corporate" aria-pressed="true"' in response.text
    assert 'data-starter-key="blank" aria-pressed="false"' in response.text
    assert 'data-cis-layer-key="cis_l2" aria-pressed="false"' in response.text
    assert 'id="wizard-baseline-override-panel" hidden' in response.text

    assert 'id="wizard-scenario-summary-copy"' in response.text
    assert 'id="wizard-scenario-summary-list"' in response.text
    assert 'id="wizard-baseline-summary-copy"' in response.text
    assert 'id="wizard-baseline-summary-list"' in response.text
    assert 'class="wizard-impact-panel' not in response.text
    assert 'id="wizard-shared-device-workflow-copy"' not in response.text
    assert 'id="wizard-baseline-preview-copy"' not in response.text

    assert 'let wizardScenario = "corporate_default";' in flow_source
    assert 'let wizardStarter = "basic_corporate";' in flow_source
    assert 'button.classList.toggle("wizard-starter-card--active", isActive);' in flow_source
    assert 'button.setAttribute("aria-pressed", isActive ? "true" : "false");' in flow_source
    assert 'box-shadow:\n                inset 4px 0 0 rgba(15, 118, 110, 0.82)' in css_source

    identity_index = setup_template.index("profiles.wizard_profile_identity_title")
    scenario_summary_index = setup_template.index('"wizard-scenario-summary-copy"')
    baseline_summary_index = setup_template.index('"wizard-baseline-summary-copy"')
    baseline_override_index = setup_template.index('"wizard-baseline-override-panel"')
    secondary_index = setup_template.index('wizard-starter-grid--secondary')
    cis_index = setup_template.index('data-cis-layer-key="cis_l2"')
    assert identity_index < scenario_summary_index < baseline_summary_index < baseline_override_index < secondary_index < cis_index


def test_step_two_default_path_is_actionable_network_basics():
    root = REPO_ROOT
    response = _profiles_page_response()
    general_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_general.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-2-basics"',
        'id="wizard-general-policy-presets"',
        'data-general-policy-preset="updates"',
        'data-general-policy-preset="downloads"',
        'id="wizard-proxy-presets"',
        'data-proxy-preset="system"',
        'data-proxy-preset="autoConfig"',
        'data-settings-target="field:wizard-proxy-mode"',
        'id="wizard-network-enterprise-presets"',
        'data-network-enterprise-preset="sso"',
        'data-network-enterprise-preset="roots"',
        'id="wizard-dns-over-https-card"',
        'id="wizard-windows-sso-card"',
        'id="wizard-authentication-card"',
        'id="wizard-certificates-card"',
        'id="wizard-network-summary-authentication"',
        'id="wizard-network-summary-certificates"',
    )
    for token in core_tokens:
        assert token in response.text

    added_tokens = (
        'id="wizard-browser-defaults-map-title"',
        'href="#wizard-step-2-basics"',
        'href="#wizard-home-surface-startup"',
        'href="#wizard-step-2-default-search"',
        'href="#wizard-step-2-review"',
        'id="wizard-home-summary-homepage"',
        'id="wizard-search-summary-defaults"',
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
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
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
    assert 'renderPresetButtonState(homepagePresetButtons, resolveHomepagePreset(parsed), "homepagePreset");' in network_source
    assert 'renderPresetButtonState(homeOverridesPresetButtons, resolveHomeOverridesPreset(parsed), "homeOverridesPreset");' in network_source
    assert 'renderPresetButtonState(firefoxHomePresetButtons, resolveFirefoxHomePreset(parsed), "firefoxHomePreset");' in network_source


def test_step_two_contains_actionable_search_and_navigation_sections():
    root = REPO_ROOT
    response = _profiles_page_response()
    search_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_search.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-2-default-search"',
        'id="wizard-search-defaults-presets"',
        'data-search-defaults-preset="managed_default"',
        'id="wizard-search-default-engine"',
        'id="wizard-search-defaults-section-status"',
        'id="wizard-step-2-managed-engines"',
        'id="wizard-search-engine-add"',
        'id="wizard-search-engine-list"',
        'data-search-engine-preset="duckduckgo"',
        'data-search-engine-field="Name"',
        'data-search-engine-field="URLTemplate"',
        'data-search-engine-field="Alias"',
        'data-search-engine-advanced',
        'data-search-engine-field="Method"',
        'data-search-engine-field="PostData"',
        'id="wizard-step-2-suggestions"',
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
    assert 'renderPresetButtonState(searchDefaultsPresetButtons, resolveSearchDefaultsPreset(parsed), "searchDefaultsPreset");' in network_source
    assert 'renderPresetButtonState(firefoxSuggestPresetButtons, resolveFirefoxSuggestPreset(parsed), "firefoxSuggestPreset");' in network_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_three_default_path_is_actionable_privacy_and_protection():
    root = REPO_ROOT
    response = _profiles_page_response()
    privacy_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_privacy.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

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
        'data-hardening-cleanup-subchoice',
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
        'data-hardening-impact-summary',
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


def test_step_four_default_path_is_compact_accounts_extensions_and_sites():
    root = REPO_ROOT
    response = _profiles_page_response()
    sync_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_sync.html"
    ).read_text(encoding="utf-8")
    extensions_source = (
        root / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-user-environment-map-title"',
        'href="#wizard-step-4-accounts"',
        'href="#wizard-step-4-language"',
        'href="#wizard-step-4-extensions"',
        'href="#wizard-step-4-bookmarks"',
        'href="#wizard-step-4-websites"',
        'id="wizard-step-4-accounts"',
        'id="wizard-sync-focus-presets"',
        'data-sync-focus-preset="accounts"',
        'id="wizard-sync-section-status"',
        'id="wizard-sync-fine-tuning-toggle"',
        'id="wizard-user-messaging-card"',
        'id="wizard-step-4-language"',
        'id="wizard-language-presets"',
        'data-language-preset="translation_off"',
        'id="wizard-requested-locales-card"',
        'id="wizard-translate-enabled-card"',
        'id="wizard-language-section-status"',
        'id="wizard-language-ai-handoff"',
        'id="wizard-step-4-extensions"',
        'id="wizard-extension-governance-presets"',
        'data-extension-governance-preset="managed"',
        'id="wizard-extension-default-mode"',
        'id="wizard-extension-section-status"',
        'id="wizard-extension-fine-tuning-toggle"',
        'id="wizard-extension-curated-section"',
        'id="wizard-step-4-bookmarks"',
        'data-bookmarks-handoff',
        'id="wizard-bookmarks-open-settings"',
        'id="wizard-bookmarks-section-status"',
        'id="wizard-step-4-websites"',
        'id="wizard-website-access-decision"',
        'id="wizard-website-access-posture"',
        'data-website-access-posture="allow_only"',
        'id="wizard-website-access-handlers"',
        'id="wizard-website-filter-card"',
        'id="wizard-website-fine-tuning-toggle"',
        'id="wizard-handlers-card"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-language-governance-copy"',
        'id="wizard-language-governance-list"',
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

    assert "render_wizard_schema_shell(6)" not in sync_template
    assert "renderLanguageGovernanceWorkflow" not in extensions_source
    assert "renderExtensionGovernanceWorkflow" not in extensions_source
    assert "renderWebsiteGovernanceWorkflow" not in extensions_source
    assert "openWebsiteGovernanceAdvanced" not in extensions_source
    assert "openExtensionGovernanceAdvanced" not in extensions_source


def test_profiles_page_preserves_final_guided_ux_contract():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_GUIDED_UX_REGRESSION_TOKENS)
