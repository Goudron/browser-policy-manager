# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_documentation_placeholders_are_removed_from_ui():
    response = _profiles_page_response()
    client = make_test_client(app)
    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()
    sources = (
        template_source("_wizard_macros.html"),
        template_source("_page_wizard_step_export.html"),
        css_source(),
        response.text,
        json.dumps(en_catalog, ensure_ascii=False),
        json.dumps(ru_catalog, ensure_ascii=False),
    )

    assert_sources_exclude_all(
        sources,
        (
            "docs_placeholder",
            "wizard-doc-placeholder",
            "data-doc-placeholder",
            "render_doc_placeholder",
            "docs-guided-schema-shell",
            "docs-policy-boundaries",
            "Future docs",
            "Будущая документация",
        ),
    )


def test_wizard_disclosure_toggle_keeps_runtime_i18n_key_in_sync():
    macros = template_source("_wizard_macros.html")
    bootstrap = static_source("profiles_bootstrap.js")
    runtime = static_source("profiles_runtime.js")

    assert (
        "data-i18n=\"{{ 'profiles.wizard_disclosure_hide' if default_open else 'profiles.wizard_disclosure_show' }}\""
        in macros
    )
    assert 'button.setAttribute(\n                "data-i18n",' in bootstrap
    assert "button.dataset.wizardDisclosureHideKey" in bootstrap
    assert "button.dataset.wizardDisclosureShowKey" in bootstrap
    assert 'toggleEl.setAttribute("data-i18n", key);' in runtime


def test_wizard_step_navigation_scrolls_only_for_normal_navigation():
    runtime_source = static_source("profiles_runtime.js")
    settings_search_source = static_source("profiles_settings_search.js")

    assert_source_contains_all(
        runtime_source,
        (
            "function scrollWizardStepToTop(stepNumber)",
            'targetEl.scrollIntoView({ behavior: "smooth", block: "start" });',
            "function navigateWizardStep(nextStep)",
            'button.addEventListener("click", () => navigateWizardStep(button.dataset.step));',
            'wizardPrevEl?.addEventListener("click", () => navigateWizardStep(getWizardStep() - 1));',
            "navigateWizardStep(getWizardStep() + 1);",
        ),
    )
    assert_source_contains_all(
        settings_search_source,
        (
            "setWizardStep(nextStep);",
            'targetEl.scrollIntoView({ behavior: "smooth", block: "center" });',
        ),
    )
    assert_source_excludes_all(settings_search_source, ("navigateWizardStep(",))


def test_profile_library_narrow_viewport_contract():
    template = template_source("_page_library_workspace.html")

    assert_source_contains_all(
        css_source(),
        (
            "@media (max-width: 560px)",
            ".library-action-grid {",
            ".library-action-grid .button-base",
            "grid-template-columns: repeat(4, minmax(0, 1fr));",
            "grid-template-columns: repeat(2, minmax(0, 1fr));",
            ".library-table-shell",
            "overflow-x: hidden;",
            ".library-row-facts",
            "grid-template-areas:",
            ".library-row-meta::before",
            "content: attr(data-label);",
            ".library-row-updated::before",
            ".library-row-status-wrap::before",
            ".library-row-actions .button-base",
            ".library-import-feedback",
        ),
    )
    assert_source_contains_all(
        template,
        (
            'id="search"',
            'id="create-profile-link"',
            'id="import-firefox-policies"',
            'id="import-firefox-policies-status"',
            'class="library-import-feedback"',
        ),
    )
    assert (
        template.index('class="library-action-grid"')
        < template.index('class="library-filter-bar"')
        < template.index('class="library-table-shell"')
    )
    assert template.index('id="search"') > template.index('class="library-filter-bar"')


def test_profile_compare_table_responsive_layout_contract():
    css = css_source()
    template = template_source("_page_compare_workspace.html")
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        template,
        (
            'class="compare-table-shell"',
            'id="compare-settings-table"',
            'class="compare-settings-table text-left text-sm"',
            'class="compare-setting-column"',
            'class="compare-value-column"',
        ),
    )
    assert_source_contains_all(
        source,
        (
            'class="compare-setting-cell px-3 py-3 align-top"',
            'data-label="${escapeHtml(settingColumnLabel)}"',
            'data-label="${escapeHtml(leftColumnLabel)}"',
            'data-label="${escapeHtml(rightColumnLabel)}"',
        ),
    )
    assert_source_contains_all(
        css,
        (
            "#compare-page {",
            "overflow-x: clip;",
            ".compare-table-shell {",
            "overflow-x: auto;",
            ".compare-settings-table {",
            "table-layout: fixed;",
            "min-width: 760px;",
            ".compare-setting-column {",
            "width: 34%;",
            ".compare-value-column {",
            "width: 33%;",
            "@media (max-width: 820px)",
            ".compare-table-shell",
            "overflow-x: hidden;",
            ".compare-settings-table colgroup,",
            ".compare-settings-table thead",
            "display: none;",
            ".compare-settings-table tr",
            "grid-template-columns: 1fr;",
            ".compare-setting-cell::before,",
            ".compare-value-cell::before",
            "content: attr(data-label);",
        ),
    )


def test_profile_compare_table_omits_duplicate_heading_and_stale_value_state_legend_contract():
    css = css_source()
    template = template_source("_page_compare_workspace.html")

    assert "compare-settings-heading" not in template
    assert ".compare-settings-heading" not in css
    assert 'class="compare-state-legend"' not in template
    assert 'class="status-pill compare-state-legend__item"' not in template
    assert ".compare-state-legend" not in css
    assert ".compare-state-legend__item" not in css


def test_profile_compare_table_long_setting_names_and_values_stay_wrapped_contract():
    css = css_source()
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            'class="compare-setting-cell px-3 py-3 align-top"',
            'class="compare-value-cell compare-value-cell--${compareRow.left.state}',
            'class="compare-value-code"',
            "renderSettingIdentity(compareRow)",
            "compare-setting-cell__label",
            "compare-setting-cell__meta",
        ),
    )
    assert_source_contains_all(
        css,
        (
            ".compare-setting-cell,",
            ".compare-value-cell {",
            "max-width: 100%;",
            "overflow: hidden;",
            ".compare-setting-cell__label {",
            "word-break: break-word;",
            ".compare-setting-cell__meta {",
            "word-break: break-word;",
            ".compare-value-state {",
            "white-space: normal;",
            ".compare-value-code {",
            "max-inline-size: 100%;",
            "white-space: pre-wrap;",
            "overflow-wrap: anywhere;",
            "word-break: break-word;",
        ),
    )


def test_visual_editor_narrow_viewport_contract():
    workspace_template = template_source("_page_workspace.html")

    assert_source_contains_all(
        css_source(),
        (
            "@media (max-width: 560px)",
            ".wizard-header",
            ".wizard-settings-search-row",
            ".wizard-layout",
            ".wizard-stepper",
            "grid-auto-columns: minmax(142px, 76vw);",
            ".wizard-panel",
            "overflow-wrap: anywhere;",
            ".wizard-nav-actions",
        ),
    )
    assert_source_excludes_all(
        workspace_template,
        ('id="editor-mode-settings"', 'id="workspace-scope-panel"'),
    )


def test_guided_editor_content_uses_shared_panel_inset_after_stepper():
    editor_styles = static_source("profiles_css/22-guided-wizard.css")
    responsive_styles = static_source("profiles_css/30-responsive.css")
    wizard_template = template_source("_page_wizard.html")

    assert (
        ".wizard-content {\n            display: grid;\n            gap: 12px;\n            min-width: 0;\n            padding-inline-start: var(--compact-space-3);"
        in editor_styles
    )
    assert (
        ".wizard-panel {\n            display: none;\n            gap: 12px;\n            padding: 0;\n            padding-inline: var(--compact-space-4);"
        in editor_styles
    )
    assert "@media (max-width: 1200px)" in responsive_styles
    assert (
        ".wizard-content {\n                padding-inline-start: var(--compact-space-3);"
        in responsive_styles
    )
    assert wizard_template.index('class="wizard-stepper"') < wizard_template.index(
        'class="wizard-content"'
    )


def test_compact_toolbar_narrow_viewport_contract():
    header_template = template_source("_page_header.html")

    assert (
        '<header class="compact-toolbar surface-panel fade-up mb-4" data-bpm-header>'
        in header_template
    )
    assert_source_contains_all(
        header_template,
        (
            'class="compact-toolbar-docs-link"',
            "{% if documentation_home_href %}",
            'href="{{ documentation_home_href }}"',
            'target="_blank"',
            'rel="noopener noreferrer"',
            "data-documentation-links",
            "data-documentation-link",
            'class="compact-toolbar-firefox-versions"',
            'data-i18n="profiles.supported_firefox_versions"',
            "header_schema_options",
            'data-firefox-channel="{{ option.value }}"',
            'id="workspace-profile-count"',
            'id="workspace-profile-label"',
        ),
    )
    assert 'data-i18n="profiles.nav_library"' not in header_template


def test_shared_editor_mode_switch_uses_compact_links_with_programmatic_current_state():
    template = template_source("_page_editor_chrome.html")
    workspace_source = static_source("profiles_workspace.js")
    editor_styles = static_source("profiles_css/23-workspace-editor.css")

    assert_source_contains_all(
        template,
        (
            'class="editor-mode-grid" role="group"',
            "profiles.editor_chrome_modes_title",
            'id="editor-mode-guided"',
            'id="editor-mode-settings"',
            'id="editor-mode-json"',
            'class="editor-mode-option-title"',
            "data-editor-mode-save-required",
        ),
    )
    assert_source_excludes_all(
        template,
        (
            "editor-chrome-mode-copy",
            "editor-mode-option-copy",
            "editor-mode-option-body",
            "profiles.editor_chrome_modes_body",
            "profiles.editor_chrome_guided_body",
            "profiles.editor_chrome_settings_body",
            "profiles.editor_chrome_json_body",
            "editor-mode-links-hint",
        ),
    )
    assert_source_contains_all(
        workspace_source,
        (
            "function refreshEditorModeLinks()",
            'el.setAttribute("aria-current", "page");',
            'el.removeAttribute("aria-current");',
            'const saveRequiredEl = el.querySelector("[data-editor-mode-save-required]");',
            "saveRequiredEl.hidden = available;",
        ),
    )
    assert_source_contains_all(
        editor_styles,
        (
            ".editor-mode-grid {",
            ".editor-mode-option {",
            "min-height: var(--compact-control-target);",
            ".editor-mode-option-state {",
        ),
    )


def test_shared_editor_chrome_keeps_each_lifecycle_fact_in_one_location():
    template = template_source("_page_editor_chrome.html")
    workspace_source = static_source("profiles_workspace.js")

    assert_source_contains_all(
        template,
        (
            'id="profile-state-badge"',
            'id="workspace-signal"',
            'id="validation-preview"',
            'id="profile-derived-note"',
            'id="profile-lifecycle-list"',
            'id="profile-compliance-list"',
        ),
    )
    assert_source_excludes_all(
        template,
        (
            "profile-lifecycle-copy",
            "profile-compliance-copy",
            "profiles.lifecycle_review_body",
            "profiles.compliance_summary_body",
        ),
    )
    assert_source_excludes_all(
        workspace_source,
        (
            "profileLifecycleCopyEl",
            "profileComplianceCopyEl",
            "profiles.lifecycle_review_active",
            "profiles.lifecycle_review_body",
            "profiles.compliance_summary_body",
            "profiles.clone_meta",
            't("profiles.meta_updated")',
            'title: t("profiles.lifecycle_item_state")',
            'title: t("profiles.lifecycle_item_origin")',
        ),
    )
    assert_source_contains_all(
        workspace_source,
        (
            "function renderCloneContext()",
            "function renderLifecycleReview()",
            "function renderProfileComplianceSummary(profile)",
            "currentMetaEl.textContent = `#${profile.id}`;",
        ),
    )


def test_guided_editor_removes_route_step_and_section_narration_before_choice_controls():
    template_sources = "\n".join(
        template_source(filename)
        for filename in (
            "_page_wizard.html",
            "_page_wizard_step_setup.html",
            "_page_wizard_step_general.html",
            "_page_wizard_step_home.html",
            "_page_wizard_step_privacy.html",
            "_page_wizard_step_search.html",
            "_page_wizard_step_sync.html",
            "_page_wizard_step_ai.html",
        )
    )

    assert_source_contains_all(
        template_source("_page_wizard.html"),
        (
            'id="wizard-panel"',
            'id="wizard-stepper"',
            'id="wizard-settings-search-meta" class="wizard-input-hint" aria-live="polite"',
            'class="wizard-step-label"',
        ),
    )
    assert_source_excludes_all(
        template_sources,
        (
            "profiles.wizard_body",
            "profiles.wizard_context_new",
            "profiles.wizard_profile_identity_body",
            "profiles.wizard_starter_body",
            "profiles.wizard_scenarios_body",
            "profiles.wizard_ai_body",
            "profiles.wizard_ai_map_body",
            "profiles.wizard_browser_defaults_map_body",
            "profiles.wizard_general_policy_body",
            "profiles.wizard_proxy_body",
            "profiles.wizard_network_enterprise_body",
            "profiles.wizard_homepage_body",
            "profiles.wizard_newtab_body",
            "profiles.wizard_firefox_home_body",
            "profiles.wizard_security_map_body",
            "profiles.wizard_hardening_body",
            "profiles.wizard_privacy_site_controls_body",
            "profiles.wizard_privacy_vpn_body",
            "profiles.wizard_privacy_review_body",
            "profiles.wizard_search_body",
            "profiles.wizard_search_add_body",
            "profiles.wizard_firefox_suggest_body",
            "profiles.wizard_user_environment_map_body",
            "profiles.wizard_sync_body",
            "profiles.wizard_language_translation_body",
            "profiles.wizard_extensions_body",
            "profiles.wizard_bookmarks_focus_body",
            "profiles.wizard_website_behavior_body",
            "profiles.wizard_website_access_decision_body",
            "profiles.wizard_extensions_advanced_body",
            "wizard-step-copy",
            "wizard-context-copy",
        ),
    )


def test_guided_choice_cards_keep_labels_and_state_without_explanatory_copy():
    template_sources = "\n".join(
        template_source(filename)
        for filename in (
            "_page_wizard_step_setup.html",
            "_page_wizard_step_general.html",
            "_page_wizard_step_home.html",
            "_page_wizard_step_privacy.html",
            "_page_wizard_step_search.html",
            "_page_wizard_step_sync.html",
            "_page_wizard_step_ai.html",
            "_wizard_macros.html",
        )
    )

    assert not re.search(
        r'<(?:span|div) class="wizard-(?:starter-copy|starter-note|toggle-copy)"', template_sources
    )
    assert not re.search(r'<span class="wizard-search-engine-preset-copy"', template_sources)
    assert not re.search(r'aria-label="[^"\n]*(?:_copy|_body)', template_sources)
    assert_source_contains_all(
        template_sources,
        (
            'aria-pressed="true"',
            'aria-pressed="false"',
            'id="wizard-general-policy-section-status" class="wizard-search-engine-preset-copy wizard-search-engine-preset-status wizard-stage-status"',
            'id="wizard-ai-section-status" class="wizard-search-engine-preset-copy wizard-search-engine-preset-status wizard-stage-status"',
        ),
    )
    assert_source_contains_all(
        static_source("profiles_wizard_flow.js"),
        (
            'button.classList.toggle("wizard-starter-card--active", isActive);',
            'button.classList.toggle("wizard-search-engine-preset--applied", isActive);',
            'button.setAttribute("aria-pressed", isActive ? "true" : "false");',
        ),
    )
    assert_source_contains_all(
        css_source(),
        (
            ".wizard-starter-card {",
            "gap: 6px;",
            "min-height: 0;",
            "padding: 12px 14px;",
            ".wizard-search-engine-preset {",
            "min-height: 56px;",
            ".wizard-starter-card--active {",
            ".wizard-search-engine-preset--applied {",
            "overflow-wrap: anywhere;",
        ),
    )
    assert_source_excludes_all(
        static_source("profiles_wizard_flow.js"),
        (
            "wizardContextCopyEl",
            "function updateWizardContext()",
        ),
    )
    settings_search_source = static_source("profiles_settings_search.js")
    assert 't("profiles.settings_search_hint")' not in settings_search_source
    assert 't("profiles.wizard_settings_search_match_count")' in settings_search_source


def test_guided_sections_flatten_decorative_nesting_and_duplicate_kickers():
    template_sources = "\n".join(
        template_source(filename)
        for filename in (
            "_page_wizard_step_general.html",
            "_page_wizard_step_home.html",
            "_page_wizard_step_privacy.html",
            "_page_wizard_step_search.html",
            "_page_wizard_step_sync.html",
        )
    )
    editor_styles = static_source("profiles_css/22-guided-wizard.css")

    assert_source_excludes_all(
        template_sources,
        (
            "profiles.wizard_main_choice_label",
            "profiles.wizard_fine_tuning_label",
        ),
    )
    assert_source_contains_all(
        template_sources,
        (
            'class="wizard-search-engine-preset-copy wizard-search-engine-preset-status wizard-stage-status"',
            'data-i18n="profiles.wizard_fine_tuning_show"',
        ),
    )
    assert_source_contains_all(
        editor_styles,
        (
            ".wizard-panel {\n            display: none;\n            gap: 12px;\n            padding: 0;",
            ".wizard-stage-panel {\n            align-content: start;\n            gap: 12px;\n            padding: 0;",
            ".wizard-fine-tuning-panel {\n            align-content: start;\n            gap: 12px;\n            padding: 10px 0 0;\n            border-top:",
            ".wizard-subsection-card {\n            display: grid;\n            gap: 10px;\n            padding: 0;",
            ".wizard-disclosure {\n            display: grid;\n            gap: 8px;",
        ),
    )
    assert "border-radius" not in css_block(".wizard-panel")
    assert "background" not in css_block(".wizard-panel")
    assert "border-radius" not in css_block(".wizard-stage-panel")
    assert "background" not in css_block(".wizard-stage-panel")


def test_compact_density_tokens_cover_controls_focus_and_reduced_motion_contract():
    foundation = static_source("profiles_css/00-foundation.css")
    compact_shell = static_source("profiles_css/40-compact-shell.css")
    editor_styles = static_source("profiles_css/23-workspace-editor.css")

    assert_source_contains_all(
        foundation,
        (
            "--compact-space-1: 0.35rem;",
            "--compact-space-2: 0.5rem;",
            "--compact-space-3: 0.75rem;",
            "--compact-space-4: 1rem;",
            "--compact-radius: 0.8rem;",
            "--compact-control-target: 2.75rem;",
            "--focus-ring-width: 3px;",
            "--focus-ring-color:",
            "@media (prefers-reduced-motion: reduce)",
            "animation-duration: 0.01ms !important;",
        ),
    )
    assert_source_contains_all(
        compact_shell,
        (
            "min-height: var(--compact-control-target);",
            "outline: var(--focus-ring-width) solid var(--focus-ring-color);",
            "inline-size: var(--compact-control-target);",
            "gap: var(--compact-space-2);",
        ),
    )
    assert_source_contains_all(
        editor_styles,
        (
            ".editor-chrome-actions .button-base {",
            ".editor-chrome-fields .soft-input {",
            "min-height: var(--compact-control-target);",
            ".editor-chrome-panel {",
            ".editor-chrome-heading {",
        ),
    )
    assert_source_excludes_all(
        template_source("_page_editor_chrome.html"),
        (
            "editor-chrome-workbar",
            "editor-chrome-status",
            "editor-profile-id",
        ),
    )
    assert_source_contains_all(
        css_source(),
        (
            ".compact-toolbar {",
            "max-inline-size: 100%;",
            "overflow-x: clip;",
            ".compact-toolbar-title {",
            "overflow-wrap: anywhere;",
            "font-size: 1.45rem;",
            "font-size: 1.3rem;",
            "font-size: 1.15rem;",
            ".compact-toolbar-firefox-versions {",
            "font-size: 0.95rem;",
            ".compact-toolbar-firefox-versions-label {",
            "overflow-wrap: anywhere;",
            ".compact-toolbar-docs-link {",
            "box-sizing: border-box;",
            ".compact-toolbar-control select.soft-input",
            "max-width: 100%;",
            "@media (max-width: 820px)",
            ".app-shell",
            "padding-inline: 12px;",
            "@media (max-width: 560px)",
            "padding-inline: 10px;",
        ),
    )


def test_contextual_help_links_are_manifest_backed_and_responsive_contract():
    partial = template_source("_context_help_link.html")
    templates = {
        "compare": template_source("_page_compare_workspace.html"),
        "guided": template_source("_page_wizard.html"),
        "settings": template_source("_page_settings_workspace.html"),
        "json": template_source("_page_json_workspace.html"),
    }

    assert_source_contains_all(
        partial,
        (
            "documentation_context_help_links.get(context_help_surface",
            'class="context-help-link"',
            'target="_blank"',
            'rel="noopener noreferrer"',
            'data-i18n="profiles.context_help_action"',
            "data-documentation-links",
            "data-context-help-surface",
        ),
    )
    assert 'context_help_surface = "library"' not in template_source("_page_library_workspace.html")
    for surface, template in templates.items():
        assert f'{{% set context_help_surface = "{surface}" %}}' in template
        assert '{% include "profiles/_context_help_link.html" %}' in template
    assert_source_contains_all(
        css_source(),
        (
            ".context-help-link {",
            ".context-help-link::after",
            ".context-help-link:hover",
            ".context-help-link:focus-visible",
            'html[data-theme="dark"] .context-help-link',
        ),
    )


def test_deep_help_icon_links_are_manifest_backed_and_responsive_contract():
    partial = template_source("_context_help_icon.html")
    template_sources = "\n".join(
        (
            template_source("_page_library_workspace.html"),
            template_source("_page_wizard_step_setup.html"),
            template_source("_page_wizard_step_ai.html"),
            template_source("_page_editor_chrome.html"),
            template_source("_page_json_workspace.html"),
            template_source("_page_wizard_step_export.html"),
        )
    )

    assert_source_contains_all(
        partial,
        (
            "documentation_deep_help_links.get(context_help_icon_target",
            'class="context-help-icon-link"',
            'target="_blank"',
            'rel="noopener noreferrer"',
            'title="{{ tr(context_help_icon_label_key) }}"',
            'aria-label="{{ tr(context_help_icon_label_key) }}"',
            "data-i18n-title",
            "data-i18n-aria-label",
            "data-documentation-links",
            "data-context-help-target",
            '<span aria-hidden="true">i</span>',
        ),
    )
    for target in (
        "policy-ai-controls",
        "policy-visual-search-enabled",
        "cis-baseline-selection",
        "validation",
        "import-firefox-policies",
        "export-firefox-policies",
    ):
        assert f'{{% set context_help_icon_target = "{target}" %}}' in template_sources
    assert_source_contains_all(
        css_source(),
        (
            ".inline-help-label {",
            ".context-help-icon-link {",
            "inline-size: var(--compact-control-target);",
            "border-radius: 999px;",
            ".context-help-icon-link:hover",
            ".context-help-icon-link:focus-visible",
            'html[data-theme="dark"] .context-help-icon-link',
        ),
    )


def test_guided_help_icons_are_limited_to_residual_choice_ambiguities():
    setup_template = template_source("_page_wizard_step_setup.html")
    ai_template = template_source("_page_wizard_step_ai.html")
    other_guided_templates = "\n".join(
        template_source(filename)
        for filename in (
            "_page_wizard_step_general.html",
            "_page_wizard_step_home.html",
            "_page_wizard_step_privacy.html",
            "_page_wizard_step_search.html",
            "_page_wizard_step_sync.html",
        )
    )
    manifest_source = source_text("app/documentation/manifest.py")
    client = make_test_client(app)

    assert setup_template.count("context_help_icon_target") == 1
    assert ai_template.count("context_help_icon_target") == 2
    assert "context_help_icon_target" not in other_guided_templates
    assert_source_contains_all(
        setup_template,
        (
            'context_help_icon_target = "cis-baseline-selection"',
            'context_help_icon_label_key = "profiles.help_cis_baseline_selection"',
        ),
    )
    assert_source_contains_all(
        ai_template,
        (
            'context_help_icon_target = "policy-ai-controls"',
            'context_help_icon_label_key = "profiles.help_policy_ai_controls"',
            'context_help_icon_target = "policy-visual-search-enabled"',
            'context_help_icon_label_key = "profiles.help_policy_visual_search_enabled"',
        ),
    )
    assert_source_contains_all(
        manifest_source,
        (
            '"policy-ai-controls": "policy:AIControls"',
            '"policy-visual-search-enabled": "policy:VisualSearchEnabled"',
            '"cis-baseline-selection": "cis:1.1.1.1"',
        ),
    )
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        catalog = client.get(f"/i18n/{locale}.json").json()
        for key in (
            "profiles.help_policy_ai_controls",
            "profiles.help_policy_visual_search_enabled",
            "profiles.help_cis_baseline_selection",
        ):
            assert isinstance(catalog.get(key), str) and catalog[key]


def test_profile_ui_decorative_density_contract():
    source = css_source()
    template_sources = "\n".join(
        template_source(filename)
        for filename in (
            "_page_library_workspace.html",
            "_page_settings_workspace.html",
            "_page_json_workspace.html",
            "_page_footer.html",
        )
    )

    assert_source_excludes_all(
        template_sources,
        (
            "rounded-[30px]",
            "rounded-[28px]",
            "rounded-[26px]",
            "rounded-[22px]",
            "shadow-soft",
            "shadow-inner",
        ),
    )
    assert_source_contains_all(
        source,
        (
            "box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);",
            "backdrop-filter: blur(8px);",
            "border-radius: 16px;",
            ".panel-card {",
            ".button-base:hover {\n            border-color: rgba(15, 118, 110, 0.28);",
            'html[data-theme="dark"] .workspace-scope-mode-card--active',
            "box-shadow: none;",
        ),
    )


def test_profiles_css_custom_properties_are_declared():
    source = css_source()

    used_tokens = set(re.findall(r"var\((--[a-zA-Z0-9_-]+)", source))
    declared_tokens = set(re.findall(r"^\s*(--[a-zA-Z0-9_-]+)\s*:", source, flags=re.MULTILINE))

    assert used_tokens <= declared_tokens
    assert "--ink-muted" in declared_tokens
    assert "--ink-soft" in declared_tokens
    assert "--line-soft" in declared_tokens


def test_settings_workspace_hides_guided_step_numbers_and_centers_mapped_controls():
    settings_workspace = template_source("_page_settings_workspace.html")

    assert_source_excludes_all(
        settings_workspace,
        (
            '<div class="section-kicker">{{ step.step }}</div>',
            "guided_source_section_ids",
            "guided_source_shell_steps",
            "{% for step in wizard_steps if step.step > 1 %}",
        ),
    )
    assert_source_contains_all(
        settings_workspace,
        (
            "{% for category in all_settings_categories %}",
            'id="settings-category-{{ category.id }}"',
            'id="all-settings-catalog-advanced"',
            "data-settings-catalog-advanced",
            "{% if not settings_shell_step_to_open %}hidden{% endif %}",
            'id="all-settings-list-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'id="all-settings-add-preference"',
            "data-settings-advanced-schema-shell",
            "profiles.settings_advanced_schema_title",
            "profiles.settings_advanced_schema_body",
            '("all", "profiles.settings_filter_all")',
            '("configured", "profiles.settings_filter_configured")',
            '("available", "profiles.settings_filter_available")',
            '("guided-covered", "profiles.settings_filter_guided_covered")',
            '("all-settings-only", "profiles.settings_filter_all_settings_only")',
            '("invalid", "profiles.settings_filter_invalid")',
            '("deprecated", "profiles.settings_filter_deprecated")',
            '("raw", "profiles.settings_filter_raw")',
            '("unknown", "profiles.settings_filter_unknown")',
        ),
    )
    assert 'id="all-settings-category-summary"' not in settings_workspace
    assert (
        'class="all-settings-domain-summary all-settings-state-summary"' not in settings_workspace
    )
    route_assets = template_source("_page_route_assets.html")
    assert "profiles_frontend_assets.routes[profiles_route_mode]" in route_assets
    assert "route_assets.scripts" in route_assets
    assert_source_contains_all(
        static_source("profiles_settings_search.js"),
        (
            "buildAllSettingsInventoryEntries",
            "all-settings-entry:${entry.kind}:${entry.id}",
            "findAllSettingsEntryTarget?.(entryTarget)",
            'entry.rawFallback ? t("profiles.settings_filter_raw")',
        ),
    )
    assert_source_contains_all(
        static_source("profiles_all_settings_list.js"),
        (
            "settingsInventory",
            "settingsInventory?.collect?.(sourceData)",
            "allSettingsRouteState",
            "routeState.updateEntries",
            "getSearchEntries",
            "findTarget",
            "data-settings-entry-raw",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_all_settings_state.js"),
        (
            "function create(initialState = {})",
            "activeCategory",
            "activeFilter",
            "searchQuery",
            "selectedEntryKey",
            "focusedTarget",
            "expandedGroups",
            "function updateEntries(entries = [], options = {})",
            "function buildCounts(entries, modeEntries, visibleEntries, filterValues, matchesFilter)",
            "export { create };",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_all_settings_detail.js"),
        (
            "settingsInventory = null",
            "settingsInventory?.getKnownPreference?.(prefName)",
            "const sourceState = readWizardSchemaSource();",
            'documentRef.getElementById("mode")?.value || "json"',
            "onDocumentChange(normalized);",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_bootstrap_core.js"),
        (
            "createAllSettingsRouteState,",
            "const allSettingsRouteState = createAllSettingsRouteState({",
            "activeMode: readAllSettingsModeFromUrl(),",
            "createSettingsInventory,",
            "const settingsInventory = createSettingsInventory({",
            "allSettingsRouteState,",
            "settingsInventory,",
            "getAllSettingsSearchEntries: () => allSettingsList.getSearchEntries()",
            "handleAllSettingsDocumentChange = () =>",
            "settingsSearch.buildIndex();",
            "workspace.updateActionState();",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_runtime.js"),
        ("buildWizardSettingsSearchIndex();", "renderWizardSettingsSearchResults();"),
    )
    assert_source_contains_all(
        css_source(),
        (
            ".wizard-search-engine-preset {",
            ".button-base.wizard-search-engine-preset {",
            "display: flex;",
            "flex-direction: column;",
            "align-items: flex-start;",
            "justify-content: center;",
        ),
    )


def test_profile_library_actions_use_editor_route_links():
    assert_source_contains_all(
        template_source("_page_library_workspace.html"),
        ('id="create-profile-link"', 'href="/profiles/new"', 'target="_blank"', 'rel="noopener"'),
    )
    library_source = static_source("profiles_library_bootstrap.js")
    assert_source_contains_all(
        library_source,
        (
            "const editHref = `/profiles/${profile.id}/edit`;",
            '<a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">',
            '<a class="button-base ghost-button library-row-secondary-action" href="${settingsHref}" target="_blank" rel="noopener">',
            '<a class="button-base ghost-button library-row-secondary-action" href="${jsonHref}" target="_blank" rel="noopener">',
            'data-clone-profile-id="${profile.id}"',
            "data-clone-name-input",
            'target="_blank"',
            'rel="noopener"',
            "data-clone-name-confirm",
            'data-library-lifecycle-action="${profile.is_deleted ? "restore" : "archive"}"',
        ),
    )
    assert_source_excludes_all(
        library_source,
        (
            "data-compare-profile-id",
            "profile-compare-button",
            'const openLabel = t("profiles.list_open");',
            'library-row-open-button" href="${editHref}"',
            "library-row-open-button--selected",
            "loadProfile(profile.id)",
        ),
    )


def test_all_settings_desktop_layout_gives_heavy_lists_full_width():
    css = css_source()
    manager_grid_rule = css.split(".all-settings-manager-grid {", 1)[1].split("}", 1)[0]
    detail_rule = css.split(".all-settings-detail {", 1)[1].split("}", 1)[0]

    assert "grid-template-columns: minmax(0, 1fr);" in manager_grid_rule
    assert "minmax(320px" not in manager_grid_rule
    assert "width: 100%;" in detail_rule
    assert "max-width: 1040px;" in detail_rule


def test_all_settings_mobile_layout_stacks_heavy_controls_and_detail():
    css = css_source()
    responsive_css = css.split("/* profiles_css/30-responsive.css */", 1)[1]
    mobile_rule = responsive_css.split("@media (max-width: 820px) {", 1)[1].split("@media", 1)[0]

    for snippet in (
        ".wizard-settings-search-scope,",
        ".all-settings-filter-bar,",
        ".all-settings-source-filter-bar",
        "grid-template-columns: 1fr;",
        ".all-settings-list-budget {",
        ".all-settings-list-budget-actions {",
        ".all-settings-detail {",
        "max-width: none;",
        ".all-settings-detail-meta > div {",
        ".all-settings-detail-actions {",
        ".all-settings-list-heading #all-settings-add-preference {",
    ):
        assert snippet in mobile_rule


def test_all_settings_long_label_contract_targets_live_heavy_ui_elements():
    settings_template = template_source("_page_settings_workspace.html")
    list_source = static_source("profiles_all_settings_list.js")
    detail_source = static_source("profiles_all_settings_detail.js")

    assert_source_contains_all(
        settings_template,
        (
            "all-settings-mode-bar",
            "all-settings-mode-button",
            "all-settings-mode-title",
            "all-settings-source-filter-bar",
            "all-settings-source-filter-button",
            "all-settings-list-budget",
            "all-settings-detail-panel",
        ),
    )
    assert_source_contains_all(
        list_source,
        (
            "all-settings-domain-card",
            "all-settings-domain-card-title",
            "all-settings-domain-card-body",
            "all-settings-domain-card-counts",
            "all-settings-domain-card-coverage",
            "all-settings-list-budget-count",
            "all-settings-list-budget-actions",
            "all-settings-list-budget-toggle",
            'data-settings-list-budget-action="prev"',
            'data-settings-list-budget-action="next"',
            'data-settings-list-budget-action="${listWindow.expanded ? "collapse" : "expand"}"',
            "all-settings-list-row",
            "all-settings-list-cell all-settings-list-cell--setting",
            "all-settings-list-cell all-settings-list-cell--value",
            "data-label=",
            "all-settings-list-badge",
            "data-settings-entry-source",
            "data-settings-entry-category-badge",
        ),
    )
    assert_source_contains_all(
        detail_source,
        (
            "all-settings-detail-actions",
            "button-base ghost-button",
            "button-base danger-button",
            "data-settings-detail-reset",
            "data-settings-detail-remove",
        ),
    )


def test_visual_editor_save_uses_revision_token_contract():
    workspace_source = static_source("profiles_workspace.js")

    assert_source_contains_all(
        workspace_source,
        (
            "function buildExpectedRevisionPayload()",
            "const revision = Number(getCurrentProfile()?.revision);",
            "return { expected_revision: revision };",
            "function buildUpdatePayload(form, parsedFlags, compliancePayload, options = {})",
            "includeExpectedRevision ? buildExpectedRevisionPayload() : {}",
            "function isRevisionConflictError(error)",
            "return Number(error?.status) === 409;",
            't("profiles.status_revision_conflict")',
            'setValidationPreview(message, "error");',
        ),
    )
    assert_source_contains_all(
        static_source("profiles_workspace_state.js"),
        (
            "function buildUpdatePayload(form, parsedFlags, compliancePayload, expectedRevisionPayload = {})",
            "...expectedRevisionPayload",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_data.js"),
        (
            "error.status = res.status;",
            "error.detail = payload.detail;",
            "if (!res.ok) throw await profileRequestError(res);",
        ),
    )


def test_json_editor_save_uses_revision_token_contract():
    assert_source_contains_all(
        static_source("profiles_runtime.js"),
        (
            '(routeMode === "edit" || routeMode === "settings" || routeMode === "json") && editingProfileId',
            "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });",
            "setJsonHandoffContext(null);",
            "applyJsonFocusTarget(focusTarget);",
            'saveButtonEl.addEventListener("click", saveCurrent);',
            "saveCurrent();",
        ),
    )
    assert "setSaveCurrent(workspace.saveCurrent);" in static_source("profiles_bootstrap_core.js")
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            "const revision = Number(getCurrentProfile()?.revision);",
            "includeExpectedRevision ? buildExpectedRevisionPayload() : {}",
            "if (isRevisionConflictError(e))",
        ),
    )


def test_guided_route_no_longer_exposes_workspace_scope_switch_contract():
    runtime_source = static_source("profiles_runtime.js")
    workspace_template = template_source("_page_workspace.html")
    source = css_source()

    assert_source_excludes_all(
        workspace_template,
        (
            'id="workspace-scope-guided"',
            'id="workspace-scope-settings"',
            'id="workspace-scope-summary"',
        ),
    )
    assert_source_excludes_all(runtime_source, ("bpm-workspace-scope", "applyWorkspaceScope("))
    assert (
        'body[data-profiles-template-kind="editor"] [data-workspace-scope-panel="settings"]'
        in source
    )
    assert_source_excludes_all(
        source,
        ('body[data-profiles-template-kind="settings"] [data-workspace-scope-panel="guided"]',),
    )


def test_guided_route_uses_headless_editor_contract_without_monaco_surface():
    assert 'function createHeadlessEditorAdapter(initialValue = "{}")' in static_source(
        "profiles_runtime_json_editor.js"
    )
    assert_source_contains_all(
        static_source("profiles_runtime.js"),
        (
            'const needsEditorRuntime = templateKind === "editor" || templateKind === "settings" || templateKind === "json";',
            "if (!editorEl && !needsEditorRuntime) {",
            ': jsonEditorRuntime.createHeadlessEditorAdapter("{}");',
        ),
    )
    assert "{% if profiles_template_kind == 'editor' %}" in template_source("_page_workspace.html")


def test_settings_route_rehomes_preference_sections_into_hidden_compat_bridge():
    settings_shell = template_source("_settings_shell.html")
    settings_workspace = template_source("_page_settings_workspace.html")

    assert "_page_settings_preference_support.html" in settings_shell
    assert_source_excludes_all(settings_shell, ("_page_settings_wizard_backing.html",))
    assert_source_contains_all(
        settings_workspace,
        (
            "data-settings-nav",
            'data-settings-jump-target="{{ control.target }}"',
            "data-settings-preferences-compat",
            'data-settings-target="pref-section:{{ preference_section.id }}"',
            'id="wizard-preferences-{{ preference_section.id }}-presets"',
        ),
    )
    assert_source_excludes_all(
        settings_workspace,
        (
            'class="mt-4 surface-soft-box rounded-[14px] p-4"',
            "profiles.settings_preferences_presets",
            "profiles.settings_preferences_bundles",
            "profiles.settings_preferences_known",
            "profiles.settings_preferences_manual",
            'class="theme-subcard rounded-[12px] px-4 py-4"',
        ),
    )
    assert "settingsTargetAliases" in static_source("profiles_catalogs.js")
    assert_source_contains_all(
        static_source("profiles_settings_search.js"),
        (
            "function resolveTargetAlias(target)",
            "shellPolicyTargetByAlias[normalizedTarget]",
            "target: resolveTargetAlias(`pref-section:${preferenceSection.id}`)",
            'normalizedTarget.startsWith("pref-section:")',
            "item?.editor?.preferenceSectionId",
            'documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`)',
        ),
    )
    assert 'wizardSearchEngineAddButtonEl?.addEventListener("click"' in static_source(
        "profiles_runtime.js"
    )
    assert_source_contains_all(
        static_source("profiles_wizard_flow.js"),
        (
            "if (!hasWizardUi) {",
            'wizardSummaryNameEl && (wizardSummaryNameEl.textContent = form.name || "—");',
        ),
    )


def test_shared_save_conflict_ui_contract():
    assert_source_contains_all(
        template_source("_page_command_deck.html"),
        (
            'id="save-conflict-panel"',
            'role="alert"',
            'id="save-conflict-reload"',
            'id="save-conflict-save-copy"',
            'id="save-conflict-overwrite"',
            'data-i18n="profiles.conflict_overwrite"',
        ),
    )
    assert 'saveConflictPanelEl: byId("save-conflict-panel")' in static_source("profiles_dom.js")
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            "let saveConflictState = null;",
            "function showSaveConflictState(error)",
            'saveConflictReloadEl?.addEventListener("click"',
            'saveConflictSaveCopyEl?.addEventListener("click"',
            'saveConflictOverwriteEl?.addEventListener("click"',
            "await saveCurrent({ overwriteRevision: true });",
            "buildUpdatePayload(form, parsedFlags, compliancePayload",
        ),
    )


def test_json_editor_chrome_exposes_format_action_without_command_deck():
    assert_source_contains_all(
        template_source("_page_editor_chrome.html"),
        ('{% if profiles_route_mode == "json" %}', 'id="format"'),
    )
    assert_source_excludes_all(template_source("_page_command_deck.html"), ('id="command-deck"',))
    assert_source_contains_all(
        static_source("profiles_runtime.js"),
        (
            'formatButtonEl?.addEventListener("click", () => {',
            'softDeleteButtonEl?.addEventListener("click", doSoftDelete);',
            'hardDeleteButtonEl?.addEventListener("click", doHardDelete);',
            'restoreButtonEl?.addEventListener("click", doRestore);',
            'resetLibraryButtonEl?.addEventListener("click", doResetLibrary);',
        ),
    )


def test_profile_review_and_workspace_state_helpers_are_split_from_dom_adapters():
    assert_source_contains_all(
        static_source("profiles_workspace_state.js"),
        (
            "export {",
            "function snapshotToString(snapshot)",
            "getWorkflowLifecycleState",
            "buildCreatePayload",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            "workspaceState = {},",
            "return workspaceState.buildCreatePayload(form, parsedFlags, compliancePayload, options);",
        ),
    )
    assert_source_excludes_all(
        static_source("profiles_workspace.js"),
        (
            "normalizeCompareBaseSnapshot",
            "compareBaseStorageKey",
            "buildCompareDiff",
            "compareWithProfile",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_review_state.js"),
        (
            "export {",
            "function hasMeaningfulValue(value)",
            "function countConfiguredObjectEntries(value)",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_review.js"),
        (
            "reviewState = {},",
            "return reviewState.countConfiguredObjectEntries(value);",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_bootstrap_core.js"),
        (
            "editorModeGuidedEl,",
            "editorModeSettingsEl,",
            "editorModeJsonEl,",
            "jsonReviewStripEl,",
            "jsonReviewSaveStateEl,",
            "jsonReviewValidationStateEl,",
            "jsonReviewDownloadStateEl,",
        ),
    )


def test_editor_workspace_static_boundary_has_no_profile_comparison_flow():
    sources = (
        static_source("profiles_workspace.js"),
        static_source("profiles_workspace_state.js"),
        static_source("profiles_dom.js"),
        static_source("profiles_runtime.js"),
        static_source("profiles_bootstrap_core.js"),
    )
    forbidden = (
        "BPMProfilesCompareState",
        "profiles_compare_state.js",
        "profiles_compare.js",
        "compareProfileState",
        "compareBaseStorageKey",
        "normalizeCompareBaseSnapshot",
        "normalizeCompareBaseProfile",
        "readStoredCompareBase",
        "writeStoredCompareBase",
        "persistCompareBaseProfile",
        "getComparableBaseState",
        "getComparableBaseId",
        "hasComparableBase",
        "buildCompareDiff",
        "renderComparePanel",
        "clearCompareProfile",
        "compareWithProfile",
        "compareClearEl",
        "compareEmptyEl",
        "compareActiveEl",
        "compareCurrentNameEl",
        "compareOtherNameEl",
        "compareMetadataCountEl",
        "comparePolicyCountEl",
        "comparePreferenceCountEl",
        "compareChangesListEl",
        "compareGuidedAreasListEl",
        "profileCloneHandoffPanelEl",
        "profileCloneHandoffCopyEl",
        "profileCloneHandoffListEl",
        "data-clone-handoff-compare",
        "profile-compare-button",
        "data-compare-profile-id",
        'id("compare-panel")',
        'byId("compare-panel")',
        'byId("profile-clone-handoff-panel")',
    )

    assert_sources_exclude_all(sources, forbidden)


def test_conflict_save_as_copy_creates_new_profile_contract():
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            "async function saveConflictAsCopy()",
            "const copyName = buildConflictCopyName(form);",
            "function buildCreatePayload(form, parsedFlags, compliancePayload, options = {})",
            "buildCreatePayload(form, parsedFlags, compliancePayload, { name: copyName })",
            "const created = await createProfile(",
            "await loadProfile(created.id, { skipConfirm: true });",
            't("profiles.conflict_copy_created").replace("{name}", created.name)',
            'saveConflictSaveCopyEl?.addEventListener("click", async () =>',
            "await saveConflictAsCopy();",
        ),
    )
    assert (
        "function buildCreatePayload(form, parsedFlags, compliancePayload, options = {})"
        in static_source("profiles_workspace_state.js")
    )


def test_profile_routes_use_specific_page_titles():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Finance Laptop Baseline"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    json_response = client.get(f"/profiles/{profile_id}/json")

    assert "<title>Library — Browser Policy Manager</title>" in library_response.text
    assert (
        "<title>New profile draft — Guided editor — Browser Policy Manager</title>"
        in new_response.text
    )
    assert (
        "<title>Finance Laptop Baseline — Guided editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        "<title>Finance Laptop Baseline — JSON editor — Browser Policy Manager</title>"
        in json_response.text
    )
