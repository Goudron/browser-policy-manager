# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_library_table_resets_list_spacing_contract():
    library_table_block = css_block(".library-table")

    assert_source_contains_all(
        library_table_block,
        (
            "display: grid;",
            "gap: 10px;",
            "margin: 0;",
            "padding: 0;",
        ),
    )


def test_library_table_head_and_rows_share_column_contract():
    source = css_source()

    assert_source_contains_all(
        source,
        (
            "--library-table-columns:",
            "minmax(320px, 1.12fr)",
            "--library-table-columns-compact:",
            "grid-template-columns: var(--library-table-columns);",
            "grid-template-columns: var(--library-table-columns-compact);",
        ),
    )


def test_library_title_button_uses_wrapping_width_contract():
    block = css_block(".library-row-title-button")

    assert_source_contains_all(block, ("width: 100%;", "max-width: 100%;", "min-width: 0;"))
    assert_source_excludes_all(block, ("width: fit-content;",))


def test_library_row_button_uses_border_box_contract():
    block = css_block(".profile-list-button")

    assert_source_contains_all(block, ("box-sizing: border-box;", "width: 100%;"))


def test_library_action_buttons_use_border_box_contract():
    block = css_block(".library-row-actions .button-base")

    assert_source_contains_all(block, ("box-sizing: border-box;", "width: 100%;"))


def test_library_action_buttons_do_not_break_russian_words():
    button_block = css_block(".library-row-actions .button-base")
    grid_block = css_block(".library-row-action-grid")

    assert_source_excludes_all(button_block, ("overflow-wrap: anywhere;",))
    assert_source_contains_all(button_block, ("overflow-wrap: normal;", "word-break: normal;"))
    assert_source_contains_all(grid_block, ("repeat(2, minmax(148px, 1fr))", "gap: 8px;"))


def test_library_bootstrap_does_not_keep_profile_comparison_state_or_actions():
    source = static_source("profiles_library_bootstrap.js")
    css = css_source()

    assert_source_excludes_all(
        source,
        (
            "windowRef.BPMProfilesCompareState",
            "let compareFirstProfileState = null;",
            "let compareSecondProfileState = null;",
            "function buildCompareState(profile)",
            "function renderComparePanel()",
            "async function selectProfileForComparison(id)",
            "data-compare-profile-id",
            "profile-compare-button",
            "profile-list-button--selected",
            "library-row-open-button--selected",
            't("profiles.library_compare_select_first")',
            't("profiles.library_compare_select_second")',
            't("profiles.library_compare_use_as_second")',
            't("profiles.library_status_compare_first_selected")',
            't("profiles.library_status_compare_ready")',
        ),
    )
    assert "windowRef.__BPM_LIBRARY_ITEMS__ = Array.isArray(items) ? items : [];" in source
    assert_source_excludes_all(
        css,
        (
            ".profile-list-button--selected",
            ".library-row-open-button--selected",
            ".profile-compare-button",
            ".profile-compare-button--active",
        ),
    )


def test_library_static_contract_exposes_compare_navigation_only():
    template = template_source("_page_library_workspace.html")
    source = static_source("profiles_library_bootstrap.js")
    locale_sources = tuple(
        (REPO_ROOT / "app" / "i18n_src" / locale / "library.json").read_text(encoding="utf-8")
        for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN")
    )

    assert_source_contains_all(
        template,
        (
            'id="compare-profiles-link"',
            'href="/profiles/compare"',
            'target="_blank"',
            'rel="noopener"',
            'data-i18n-title="profiles.compare_action"',
            'data-i18n="profiles.compare_action"',
        ),
    )
    assert_source_excludes_all(
        template,
        (
            'id="compare-panel"',
            'id="compare-clear"',
            'id="compare-empty"',
            'id="compare-active"',
            "data-compare-profile-id",
            "profiles.library_compare_",
        ),
    )
    assert_source_excludes_all(
        source,
        (
            "data-compare-profile-id",
            "selectProfileForComparison",
            "renderComparePanel",
            "profiles.library_compare_",
            "profiles.library_status_compare_",
        ),
    )
    for locale_source in locale_sources:
        assert "profiles.library_compare_" not in locale_source
        assert "profiles.library_status_compare_" not in locale_source


def test_compare_diff_recurses_inside_compare_only_state_contract():
    compare_source = static_source("profiles_compare_state.js")
    workspace_source = static_source("profiles_workspace.js")
    workspace_state_source = static_source("profiles_workspace_state.js")

    assert_source_contains_all(
        compare_source,
        (
            "if (isPlainObject(normalizedBase) || isPlainObject(normalizedOther)) {",
            "const baseObject = isPlainObject(normalizedBase) ? normalizedBase : {};",
            "const otherObject = isPlainObject(normalizedOther) ? normalizedOther : {};",
            "collectDiffPaths(baseObject[key], otherObject[key], [...path, key], changes);",
        ),
    )
    assert_source_excludes_all(
        workspace_state_source,
        (
            "window.BPMProfilesCompareState",
            "collectDiffPaths",
            "normalizeCompareBaseSnapshot",
            "normalizeCompareBaseProfile",
        ),
    )
    assert_source_excludes_all(
        workspace_source,
        (
            "function buildCompareDiff(",
            "return workspaceState.collectDiffPaths(baseValue, otherValue, path, changes);",
            "data-clone-handoff-compare",
        ),
    )


def test_compare_value_states_have_visible_text_and_not_color_only_contract():
    css = css_source()
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            "resolveValueStateLabel(leftState, options)",
            "resolveValueStateLabel(rightState, options)",
            "compare-value-state",
            "compare-value-code",
            "stateLabel",
        ),
    )
    assert_source_contains_all(
        css,
        (
            ".compare-value-cell {",
            ".compare-value-state {",
            ".compare-value-cell--equal .compare-value-state {",
            ".compare-value-cell--different .compare-value-state {",
            ".compare-value-cell--missing .compare-value-state {",
            ".compare-value-code {",
            "text-transform: uppercase;",
            "white-space: pre-wrap;",
        ),
    )


def test_compare_route_entrypoint_keeps_selection_and_table_anchors_contract():
    source = static_source("profiles_compare.js")

    assert_source_contains_all(
        source,
        (
            'const sideKeys = ["left", "right"];',
            "const elements = Object.fromEntries(sideKeys.map((side) => [",
            "search: documentRef.getElementById(`compare-${side}-search`),",
            "results: documentRef.getElementById(`compare-${side}-results`),",
            "selected: documentRef.getElementById(`compare-${side}-profile`),",
            "data-compare-results-state=\"loading\"",
            "data-compare-results-state=\"error\"",
            "data-compare-results-state=\"empty\"",
            "button.dataset.compareResultSide = side;",
            "button.dataset.compareProfileId = String(profile.id);",
            "row.dataset.compareRowId = compareRow.id;",
            "row.dataset.compareRowKind = compareRow.kind;",
            "row.dataset.compareRowChanged = compareRow.changed ? \"true\" : \"false\";",
            'data-compare-column="left"',
            'data-compare-column="right"',
            "data-compare-value-state=\"${compareRow.left.state}\"",
            "data-compare-value-state=\"${compareRow.right.state}\"",
            "profiles.compare_table_empty",
            "profiles.compare_table_no_settings",
        ),
    )
    assert_source_excludes_all(
        source,
        (
            "profile-list-button",
            "profile-compare-button",
            "data-clone-profile-id",
            "profile-clone-handoff",
            "profiles.library_compare_",
            "profiles.library_status_compare_",
            "profile-owner",
        ),
    )


def test_profile_runtime_and_wizard_bootstrap_guard_optional_inputs_contract():
    runtime_source = static_source("profiles_runtime.js")
    shared_source = static_source("profiles_shared.js")
    network_source = static_source("profiles_network.js")
    extension_source = static_source("profiles_extensions.js")
    wizard_source = static_source("profiles_wizard_flow.js")

    assert 'nameInput?.addEventListener("input", () => {' in runtime_source
    assert "ownerInput" not in runtime_source
    assert 'descriptionInput?.addEventListener("input", () => {' in runtime_source
    assert 'profileTypeEl?.addEventListener("change", () => {' in runtime_source
    assert "if (nameInput) {" in runtime_source
    assert "if (profileTypeEl) {" in runtime_source

    assert "if (!input) return;" in shared_source
    assert "if (!input) return;" in network_source
    assert "!wizardHomepageUrlEl" in network_source
    assert "!wizardProxyUseDnsEl" in network_source
    assert "managedExtensionFields.filter(Boolean).forEach((input) => {" in extension_source
    assert "].filter(Boolean).forEach((input) => {" in extension_source
    assert "if (wizardNameEl && nameInput) {" in wizard_source
    assert "profile-owner" not in wizard_source
    assert "const profileTypeInput = documentRef.getElementById(\"profile-type\");" in wizard_source
