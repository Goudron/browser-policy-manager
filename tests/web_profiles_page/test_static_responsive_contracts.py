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
    assert_source_contains_all(
        css_source(),
        (
            "@media (max-width: 560px)",
            ".library-panel-toolbar #create-profile-link",
            ".library-panel-toolbar #import-firefox-policies",
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
        template_source("_page_library_workspace.html"),
        (
            'id="search"',
            'id="create-profile-link"',
            'id="import-firefox-policies"',
            'id="import-firefox-policies-status"',
            'class="library-import-feedback"',
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


def test_compact_toolbar_narrow_viewport_contract():
    assert '<header class="compact-toolbar surface-panel fade-up mb-4">' in template_source(
        "_page_header.html"
    )
    assert_source_contains_all(
        css_source(),
        (
            ".compact-toolbar {",
            "max-inline-size: 100%;",
            "overflow-x: clip;",
            ".compact-toolbar-title {",
            "overflow-wrap: anywhere;",
            "font-size: 2.45rem;",
            "font-size: 1.9rem;",
            "font-size: 1.62rem;",
            ".compact-toolbar-control select.soft-input",
            "max-width: 100%;",
            "@media (max-width: 820px)",
            ".app-shell",
            "padding-inline: 12px;",
            "@media (max-width: 560px)",
            "padding-inline: 10px;",
        ),
    )


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
    declared_tokens = set(
        re.findall(r"^\s*(--[a-zA-Z0-9_-]+)\s*:", source, flags=re.MULTILINE)
    )

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
            'data-settings-category-link="{{ category.id }}"',
            'id="all-settings-list-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'id="all-settings-add-preference"',
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
    assert_source_contains_all(
        template_source("_page_route_assets.html"),
        ('"/static/profiles_all_settings_list.js"', '"/static/profiles_all_settings_detail.js"'),
    )
    assert_source_contains_all(
        static_source("profiles_settings_search.js"),
        (
            "buildAllSettingsInventoryEntries",
            "all-settings-entry:${entry.kind}:${entry.id}",
            "findAllSettingsEntryTarget?.(normalizedTarget)",
            'entry.rawFallback ? t("profiles.settings_filter_raw")',
        ),
    )
    assert_source_contains_all(
        static_source("profiles_all_settings_list.js"),
        ("getSearchEntries", "findTarget", "data-settings-entry-raw"),
    )
    assert_source_contains_all(
        static_source("profiles_all_settings_detail.js"),
        (
            "const sourceState = readWizardSchemaSource();",
            'documentRef.getElementById("mode")?.value || "json"',
            "onDocumentChange(normalized);",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_bootstrap_core.js"),
        (
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
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            'const editHref = `/profiles/${profile.id}/edit`;',
            '<a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">',
            '<a class="button-base library-row-open-button ${selected ? "library-row-open-button--selected" : ""}" href="${editHref}" target="_blank" rel="noopener">',
        ),
    )
    assert_source_excludes_all(static_source("profiles_workspace.js"), ("loadProfile(profile.id)",))


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
        ('id="workspace-scope-guided"', 'id="workspace-scope-settings"', 'id="workspace-scope-summary"'),
    )
    assert_source_excludes_all(runtime_source, ("bpm-workspace-scope", "applyWorkspaceScope("))
    assert 'body[data-profiles-template-kind="editor"] [data-workspace-scope-panel="settings"]' in source
    assert_source_excludes_all(
        source,
        ('body[data-profiles-template-kind="settings"] [data-workspace-scope-panel="guided"]',),
    )


def test_guided_route_uses_headless_editor_contract_without_monaco_surface():
    assert "function createHeadlessEditorAdapter(initialValue = \"{}\")" in static_source(
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


def test_settings_route_uses_visible_catalog_sections_without_hidden_wizard_backing():
    settings_shell = template_source("_settings_shell.html")
    settings_workspace = template_source("_page_settings_workspace.html")

    assert '_page_settings_preference_support.html' in settings_shell
    assert_source_excludes_all(settings_shell, ("_page_settings_wizard_backing.html",))
    assert_source_contains_all(
        settings_workspace,
        (
            "data-settings-nav",
            'data-settings-jump-target="{{ control.target }}"',
            'data-settings-target="pref-section:{{ preference_section.id }}"',
            'id="wizard-preferences-{{ preference_section.id }}-presets"',
        ),
    )
    assert "settingsTargetAliases" in static_source("profiles_catalogs.js")
    assert_source_contains_all(
        static_source("profiles_settings_search.js"),
        (
            "function resolveTargetAlias(target)",
            "shellPolicyTargetByAlias[normalizedTarget]",
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
            "window.BPMProfilesWorkspaceState = {",
            "normalizeCompareBaseSnapshot",
            "getWorkflowLifecycleState",
            "buildCreatePayload",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_workspace.js"),
        (
            "const workspaceState = windowRef.BPMProfilesWorkspaceState || {};",
            "return workspaceState.normalizeCompareBaseSnapshot(snapshot, fallbackProfile, defaultSchemaVersion);",
            "return workspaceState.buildCreatePayload(form, parsedFlags, compliancePayload, options);",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_review_state.js"),
        (
            "window.BPMProfilesReviewState = {",
            "function hasMeaningfulValue(value)",
            "function countConfiguredObjectEntries(value)",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_review.js"),
        (
            "const reviewState = window.BPMProfilesReviewState || {};",
            "return reviewState.countConfiguredObjectEntries(value);",
        ),
    )
    assert_source_contains_all(
        static_source("profiles_bootstrap_core.js"),
        (
            "editorModeGuidedEl,",
            "editorModeSettingsEl,",
            "editorModeJsonEl,",
            "editorModeLinksHintEl,",
            "jsonReviewStripEl,",
            "jsonReviewSaveStateEl,",
            "jsonReviewValidationStateEl,",
            "jsonReviewDownloadStateEl,",
        ),
    )


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
    assert "<title>New profile draft — Guided editor — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Finance Laptop Baseline — Guided editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert "<title>Finance Laptop Baseline — JSON editor — Browser Policy Manager</title>" in json_response.text
