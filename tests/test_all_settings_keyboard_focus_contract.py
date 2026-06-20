from pathlib import Path

from tests.web_profiles_page_helpers import static_source, template_source

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_all_settings_keyboard_focus_contract_is_wired_for_heavy_review_surface():
    settings_template = template_source("_page_settings_workspace.html")
    search_source = static_source("profiles_settings_search.js")
    list_source = static_source("profiles_all_settings_list.js")
    detail_source = static_source("profiles_all_settings_detail.js")
    css_source = static_source("profiles_css/20-editor-wizard.css")

    for snippet in (
        'class="all-settings-mode-bar surface-soft-box"',
        'role="group"',
        'type="button"',
        'data-settings-mode="{{ mode_id }}"',
        'aria-pressed="{{ \'true\' if mode_id == \'review\' else \'false\' }}"',
        'id="wizard-settings-search-input"',
        'id="wizard-settings-search-results"',
        'role="toolbar"',
        'data-settings-search-scope="{{ scope_id }}"',
        'id="all-settings-list-budget"',
        'id="all-settings-detail-panel"',
    ):
        assert snippet in settings_template

    for snippet in (
        "button.type = \"button\";",
        "button.dataset.settingsSearchTarget = entry.target;",
        "button.setAttribute(\n                \"aria-label\",",
        "function firstResultButton()",
        "function activateSearchResult(button)",
        "if (event.key === \"Enter\")",
        "activateSearchResult(firstResultButton())",
        "if (event.key === \"ArrowDown\")",
        "firstResult.focus?.();",
        "focusTarget?.focus?.({ preventScroll: true });",
        "allSettingsRouteState?.setFocusedTarget(normalizedTarget);",
    ):
        assert snippet in search_source

    for snippet in (
        'type="button"',
        "class=\"all-settings-list-row${selected ? \" is-selected\" : \"\"}\"",
        'aria-current="${selected ? "true" : "false"}"',
        "routeState.setSelectedEntryKey(",
        'entryRow.setAttribute("aria-current", isSelected ? "true" : "false");',
        "row?.scrollIntoView?.({ block: \"nearest\", inline: \"nearest\" });",
        'data-settings-list-budget-action="prev"',
        'data-settings-list-budget-action="next"',
        'data-settings-list-budget-action="${listWindow.expanded ? "collapse" : "expand"}"',
        "data-settings-list-budget-expanded",
    ):
        assert snippet in list_source

    for snippet in (
        "all-settings-detail-actions",
        "button-base ghost-button",
        "data-settings-detail-reset",
        "button-base danger-button",
        "data-settings-detail-remove",
        "data-settings-detail-primary-focus",
    ):
        assert snippet in detail_source

    for snippet in (
        ".wizard-settings-search-result",
        ".all-settings-domain-card:focus-visible",
        ".all-settings-review-card:focus-visible",
        ".all-settings-list-row:focus-visible",
    ):
        assert snippet in css_source
