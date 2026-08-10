from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
THEME_CSS = DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_documentation_search_css_hides_panel_without_removing_compact_row() -> None:
    theme = _source(THEME_CSS)

    for required in (
        ".bpm-docs-visually-hidden",
        ".bpm-docs-search-advanced-panel[hidden]",
        "display: none;",
        ".bpm-docs-search .bpm-docs-search-advanced-toggle",
        '.bpm-docs-search .bpm-docs-search-advanced-toggle[aria-expanded="true"]',
        ".bpm-docs-search-active-filters",
        ".bpm-docs-search-clear-filters",
    ):
        assert required in theme


def test_documentation_search_runtime_toggles_advanced_panel_and_preserves_query_state() -> None:
    script = _source(SEARCH_SCRIPT)

    for required in (
        "const setSearchExpanded = (root, expanded) => {",
        'root.querySelector("[data-search-advanced-panel]")',
        'root.querySelector("[data-search-advanced-toggle]")',
        "panel.hidden = !expanded;",
        'toggle.setAttribute("aria-expanded", expanded ? "true" : "false");',
        'root.querySelector("[data-search-advanced-toggle]")?.addEventListener("click"',
        "setSearchExpanded(root, !expanded);",
        "runSearch(root, index);",
        "input.focus();",
    ):
        assert required in script

    assert 'input.value = "";' in script
    assert "setSearchExpanded(root, false)" in script
    assert "setSearchExpanded(root, true)" not in script


def test_documentation_search_runtime_exposes_and_clears_hidden_active_filters() -> None:
    script = _source(SEARCH_SCRIPT)

    for required in (
        "function updateActiveFilterSummary(root, filters = selectedFilters(root))",
        'root.querySelector("[data-search-active-filters]")',
        'root.querySelector("[data-search-active-filters-summary]")',
        "state.hidden = !count || !panelIsCollapsed;",
        'root.dataset.labelActiveFilters || "Active filters: {count}"',
        'const clearFilters = root.querySelector("[data-search-clear-filters]");',
        'clearFilters.addEventListener("click", () => {',
        'root.querySelector("[data-search-advanced-toggle]")?.focus();',
    ):
        assert required in script
