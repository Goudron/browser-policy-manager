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
    assert "minmax(168px, 1fr)" in grid_block


def test_library_compare_contract_selects_two_profiles_explicitly():
    source = static_source("profiles_library_bootstrap.js")

    assert_source_contains_all(
        source,
        (
            "let compareFirstProfileState = null;",
            "let compareSecondProfileState = null;",
            "function buildCompareState(profile)",
            "function renderComparePanel()",
            "windowRef.__BPM_LIBRARY_ITEMS__ = Array.isArray(items) ? items : [];",
            "async function selectProfileForComparison(id)",
            "await selectProfileForComparison(profile.id);",
            't("profiles.library_compare_select_first")',
            't("profiles.library_compare_select_second")',
            't("profiles.library_compare_use_as_second")',
        ),
    )
    assert_source_excludes_all(
        source,
        (
            'const compareBaseStorageKey = "bpm-library-compare-base";',
            'windowRef.localStorage?.setItem(compareBaseStorageKey, JSON.stringify({',
            'windowRef.addEventListener?.("storage", (event) => {',
            'windowRef.addEventListener?.("focus", refreshCompareBaselineUi);',
        ),
    )


def test_compare_diff_recurses_into_missing_object_branches_contract():
    library_source = static_source("profiles_library_bootstrap.js")
    workspace_source = static_source("profiles_workspace.js")
    workspace_state_source = static_source("profiles_workspace_state.js")

    for source in (library_source, workspace_state_source):
        assert_source_contains_all(
            source,
            (
                "if (isPlainObject(normalizedBase) || isPlainObject(normalizedOther)) {",
                "const baseObject = isPlainObject(normalizedBase) ? normalizedBase : {};",
                "const otherObject = isPlainObject(normalizedOther) ? normalizedOther : {};",
                "collectDiffPaths(baseObject[key], otherObject[key], [...path, key], changes);",
            ),
        )
    assert "return workspaceState.collectDiffPaths(baseValue, otherValue, path, changes);" in workspace_source


def test_profile_runtime_and_wizard_bootstrap_guard_optional_inputs_contract():
    runtime_source = static_source("profiles_runtime.js")
    shared_source = static_source("profiles_shared.js")
    network_source = static_source("profiles_network.js")
    extension_source = static_source("profiles_extensions.js")
    wizard_source = static_source("profiles_wizard_flow.js")

    assert 'nameInput?.addEventListener("input", () => {' in runtime_source
    assert 'ownerInput?.addEventListener("input", () => {' in runtime_source
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
    assert "const profileTypeInput = documentRef.getElementById(\"profile-type\");" in wizard_source
