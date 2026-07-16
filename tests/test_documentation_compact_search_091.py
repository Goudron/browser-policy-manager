from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
BUILD_DOCS = DOCUMENTATION_ROOT / "tools/build_docs.py"
THEME_CSS = DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"

SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_documentation_search_shell_defaults_to_one_line_compact_controls() -> None:
    source = _source(BUILD_DOCS)

    for required in (
        'class="bpm-docs-visually-hidden">{_escape(labels["search"])}</h2>',
        'class="bpm-docs-visually-hidden" for="bpm-docs-search-query"',
        'class="bpm-docs-search-row"',
        'data-search-submit>{_escape(labels["search_submit"])}</button>',
        'data-search-clear>{_escape(labels["search_clear"])}</button>',
        'class="bpm-docs-search-advanced-toggle"',
        'aria-expanded="false"',
        'aria-controls="bpm-docs-search-advanced-panel"',
        "data-search-advanced-toggle",
    ):
        assert required in source


def test_documentation_search_help_filters_and_results_are_in_hidden_panel() -> None:
    source = _source(BUILD_DOCS)

    panel_start = source.index('id="bpm-docs-search-advanced-panel"')
    panel = source[panel_start : source.index("</div>\n            </section>", panel_start)]

    assert "data-search-advanced-panel hidden" in panel
    assert "bpm-docs-search-help" in panel
    assert "bpm-docs-search-filters" in panel
    assert "data-search-status" in panel
    assert "bpm-docs-search-results" in panel
    assert "<details" not in panel


def test_documentation_search_css_hides_panel_without_removing_compact_row() -> None:
    theme = _source(THEME_CSS)

    for required in (
        ".bpm-docs-visually-hidden",
        ".bpm-docs-search-advanced-panel[hidden]",
        "display: none;",
        ".bpm-docs-search .bpm-docs-search-advanced-toggle",
        '.bpm-docs-search .bpm-docs-search-advanced-toggle[aria-expanded="true"]',
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
        "setSearchExpanded(root, true);",
        "runSearch(root, index);",
        "input.focus();",
    ):
        assert required in script

    assert "input.value = \"\";" in script
    assert "setSearchExpanded(root, false)" not in script
