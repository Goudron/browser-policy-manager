from __future__ import annotations

import importlib.util
from pathlib import Path

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def test_portal_shell_has_localized_chrome_for_every_published_locale() -> None:
    assert set(build_docs.SHELL_LABELS) == set(build_docs.LOCALES)
    for locale, labels in build_docs.SHELL_LABELS.items():
        for key in (
            "skip",
            "guides",
            "locales",
            "breadcrumbs",
            "home",
            "status",
            "theme",
            "theme_system",
            "theme_light",
            "theme_dark",
            "navigation_root",
            "navigation_tree_label",
            "navigation_loading",
            "navigation_unavailable",
            "search",
            "search_query",
            "search_placeholder",
            "search_submit",
            "search_clear",
            "search_clear_filters",
            "search_active_filters",
            "search_help",
            "search_filters",
            "search_results",
            "search_loading",
            "search_ready",
            "search_no_results",
            "search_unavailable",
            "assistant",
            "assistant_description",
            "assistant_unavailable",
            "assistant_transcript",
            "assistant_question",
            "assistant_question_placeholder",
            "assistant_controls_unavailable",
            "assistant_send",
            "assistant_stop",
            "assistant_clear",
            "assistant_answer_mode",
            "assistant_sources",
            "assistant_unavailable_short",
            "assistant_install_model",
            "assistant_ready",
            "assistant_clear_short",
        ):
            assert labels[key].strip(), (locale, key)
        assert labels["skip"] != build_docs.SHELL_LABELS["en"]["skip"] or locale == "en"
        assert labels["theme_system"].strip().lower() != "system" or locale in {"en", "de"}


def test_portal_theme_covers_responsive_dark_light_focus_code_tables_notes_and_print() -> None:
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    print_theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-print.css").read_text(
        encoding="utf-8"
    )

    for required in (
        "color-scheme: light dark",
        "@media (prefers-color-scheme: dark)",
        "@media (max-width: 48rem)",
        "@media (max-width: 320px)",
        "@media (prefers-reduced-motion: reduce)",
        "@media (forced-colors: active)",
        ":focus-visible",
        ".bpm-docs-main pre",
        ".bpm-docs-main table",
        ".bpm-docs-main figure",
        ".bpm-docs-main img",
        ".bpm-docs-main figcaption",
        ".bpm-docs-main .note",
        ".bpm-docs-search",
        ".bpm-docs-discovery-tools",
        ".bpm-docs-assistant-widget",
        ".bpm-docs-assistant-toggle",
        ".bpm-docs-assistant-panel",
        ".bpm-docs-assistant-clear",
        ".bpm-docs-assistant-send",
        ".bpm-docs-assistant-stop",
        ".bpm-docs-assistant-message",
        ".bpm-docs-assistant-surface",
        ".bpm-docs-assistant-transcript",
        ".bpm-docs-assistant-recovery",
        ".bpm-docs-assistant-web-mode",
        ".bpm-docs-assistant-controls textarea",
        ".bpm-docs-assistant-actions",
        ".bpm-docs-search-input",
        ".bpm-docs-search-result-list",
        ".bpm-docs-search mark",
        'html[data-theme="light"]',
        'html[data-theme="dark"]',
        ".bpm-docs-theme-control",
        ".bpm-docs-tree-host",
        ".bpm-docs-tree-status--unavailable",
    ):
        assert required in theme
    assert "@media print" in print_theme
    assert ".bpm-docs-header-actions" in print_theme
    assert ".bpm-docs-search" in print_theme
    assert ".bpm-docs-assistant-widget" in print_theme


def test_portal_current_navigation_uses_primary_ui_selected_surfaces() -> None:
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    product_theme = (
        REPOSITORY_ROOT / "app/static/profiles_css/00-foundation.css"
    ).read_text(encoding="utf-8")
    product_editor = (
        REPOSITORY_ROOT / "app/static/profiles_css/20-editor-wizard.css"
    ).read_text(encoding="utf-8")

    for token in (
        "--bpm-docs-selected-bg: rgba(20, 184, 166, 0.12)",
        "--bpm-docs-selected-border: rgba(15, 118, 110, 0.32)",
        "--bpm-docs-selected-text: rgb(15 118 110)",
        "--bpm-docs-selected-bg: rgba(6, 78, 59, 0.42)",
        "--bpm-docs-selected-border: rgba(34, 197, 94, 0.22)",
        "--bpm-docs-selected-text: #e2e8f0",
    ):
        assert token in theme

    assert "background: rgba(20, 184, 166, 0.12)" in product_editor
    assert "border-color: rgba(15, 118, 110, 0.32)" in product_editor
    assert "background: rgba(6, 78, 59, 0.42)" in product_editor
    assert "border-color: rgba(34, 197, 94, 0.22)" in product_editor
    assert "--ink: #e2e8f0" in product_theme

    current_rule = theme.split('.bpm-docs-guide-list a[aria-current="page"]', 1)[1].split("}", 1)[0]
    assert "background: var(--bpm-docs-selected-bg)" in current_rule
    assert "border-color: var(--bpm-docs-selected-border)" in current_rule
    assert "color: var(--bpm-docs-selected-text)" in current_rule
    assert "#ffffff" not in current_rule


def test_portal_sidebar_has_independent_desktop_and_narrow_scroll_contract() -> None:
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js").read_text(
        encoding="utf-8"
    )

    sidebar_rule = theme.split(".bpm-docs-sidebar {", 1)[1].split("}", 1)[0]
    assert "max-block-size: calc(100dvh - 2rem)" in sidebar_rule
    assert "overflow-x: hidden" in sidebar_rule
    assert "overflow-y: auto" in sidebar_rule
    assert "overscroll-behavior: contain" in sidebar_rule
    assert "scrollbar-gutter: stable" in sidebar_rule
    narrow = theme.split("@media (max-width: 48rem)", 1)[1]
    narrow_sidebar = narrow.split(".bpm-docs-sidebar {", 1)[1].split("}", 1)[0]
    assert "max-block-size: min(70dvh, 32rem)" in narrow_sidebar
    assert "position: static" in narrow_sidebar
    assert "overflow-wrap: anywhere" in theme
    assert "scrollTreeItemIntoView" in script
    assert "item.focus({ preventScroll: true })" in script
    assert "container.scrollTop +=" in script


def test_portal_shell_keeps_csp_friendly_static_boundaries() -> None:
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    print_theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-print.css").read_text(
        encoding="utf-8"
    )
    source = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")
    search_script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js").read_text(
        encoding="utf-8"
    )

    assert '<script src="' in source
    assert "<script>" not in source
    assert "onload=" not in source
    assert "style=" not in source
    assert "http://" not in theme
    assert "https://" not in theme
    assert "url(" not in theme
    assert "url(" not in print_theme
    for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert forbidden not in search_script
    assert "fetch(" in search_script
    assert "setupNavigationHost" in search_script
    assert "resolved.origin !== window.location.origin" in search_script
    assert "treeItem.textContent = node.label" in search_script
    assert "navigation source identity mismatch" in search_script
    assert "localStorage" in search_script
    assert "bpm-theme-mode" in search_script
    assert "dataset.themeMode" in search_script
    assert "dataset.theme" in search_script
    assert 'matchMedia("(prefers-color-scheme: dark)")' in search_script
    assert "MAX_RESULTS = 50" in search_script
