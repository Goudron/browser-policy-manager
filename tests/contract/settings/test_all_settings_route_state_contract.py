from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def _static_source(filename: str) -> str:
    return (STATIC_ROOT / filename).read_text(encoding="utf-8")


def test_all_settings_route_state_initializes_navigation_state_contract():
    source = _static_source("profiles_all_settings_state.js")

    for snippet in (
        'const DEFAULT_FILTER = "all";',
        'const DEFAULT_CATEGORY = "all";',
        'const DEFAULT_MODE = "review";',
        'const VALID_MODES = new Set(["review", "configured", "catalog"]);',
        "function normalizeMode(mode)",
        "activeCategory: normalizeText(initialState.activeCategory, DEFAULT_CATEGORY)",
        "activeMode: normalizeMode(initialState.activeMode)",
        "activeFilter: normalizeText(initialState.activeFilter, DEFAULT_FILTER)",
        "searchQuery: normalizeText(initialState.searchQuery)",
        "selectedEntryKey: normalizeText(initialState.selectedEntryKey)",
        "focusedTarget: normalizeText(initialState.focusedTarget)",
        "expandedGroups: new Set(uniqueList(initialState.expandedGroups))",
        "function getSnapshot()",
        "function setActiveMode(mode)",
        "export { create };",
    ):
        assert snippet in source


def test_all_settings_route_state_update_contract_tracks_counts_visibility_and_selection():
    source = _static_source("profiles_all_settings_state.js")

    for snippet in (
        "function updateEntries(entries = [], options = {})",
        'const matchesMode = typeof options.matchesMode === "function"',
        "const nextModeEntries = nextEntries.filter((entry) => matchesMode(entry, state.activeMode));",
        "const nextVisibleEntries = nextCategoryEntries.filter((entry) => matchesFilter(entry, state.activeFilter));",
        "state.modeEntries = nextModeEntries;",
        "state.categoryEntries = nextCategoryEntries;",
        "state.visibleEntries = nextVisibleEntries;",
        "state.counts = buildCounts(",
        "filters[filterValue] = visibleEntries.categoryEntries.filter((entry) => matchesFilter(entry, filterValue)).length;",
        "metadata.updateCategory && metadata.categoryId",
        "fallbackVisible && state.activeCategory !== DEFAULT_CATEGORY",
        "function getCategoryEntries()",
        "function getModeEntries()",
        "function getVisibleEntries()",
        "function getSelectedEntry(entries = state.entries, entryKey = defaultEntryKey)",
    ):
        assert snippet in source


def test_all_settings_list_uses_route_state_instead_of_local_navigation_state():
    source = _static_source("profiles_all_settings_list.js")

    for stale_local_state in ("let activeFilter", "let selectedEntryKey", "let lastEntries"):
        assert stale_local_state not in source

    for snippet in (
        "allSettingsRouteState",
        "components = {}",
        "createAllSettingsRouteState",
        "const routeState = allSettingsRouteState || createAllSettingsRouteState();",
        "onModeChange,",
        "function setActiveMode(mode, options = {})",
        "onModeChange?.(routeState.getSnapshot().activeMode, options);",
        "routeState.updateEntries(entries, {",
        "matchesMode: entryMatchesMode,",
        "routeState.setActiveFilter(",
        'setActiveMode("catalog", { updateUrl: false });',
        "routeState.setSelectedEntryKey(",
        "routeState.setFocusedTarget(normalizedTarget);",
    ):
        assert snippet in source
