from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_THEME = REPO_ROOT / "documentation/assets/theme/bpm-docs.css"


def _theme() -> str:
    return DOCS_THEME.read_text(encoding="utf-8")


def _block(source: str, selector: str) -> str:
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def _light_tokens(source: str) -> str:
    return source.split("@media (prefers-color-scheme: dark)", 1)[0]


def test_documentation_theme_uses_091_product_aligned_tokens() -> None:
    theme = _theme()
    light_tokens = _light_tokens(theme)

    assert "Browser Policy Manager documentation portal theme" in theme
    for declaration in (
        "--bpm-docs-bg: #edf2f7;",
        "--bpm-docs-bg-mid: #e7edf4;",
        "--bpm-docs-bg-end: #dfeae8;",
        "--bpm-docs-surface: rgba(235, 240, 246, 0.9);",
        "--bpm-docs-surface-strong: rgba(226, 232, 240, 0.94);",
        "--bpm-docs-surface-muted: rgba(226, 232, 240, 0.72);",
        "--bpm-docs-control-bg: rgba(226, 232, 240, 0.86);",
        "--bpm-docs-control-hover-bg: rgba(218, 226, 236, 0.94);",
        "--bpm-docs-text: #122033;",
        "--bpm-docs-text-muted: #5d6b7f;",
        "--bpm-docs-accent: #0f766e;",
        "--bpm-docs-accent-strong: #115e59;",
        "--bpm-docs-accent-soft: rgba(15, 118, 110, 0.12);",
    ):
        assert declaration in light_tokens

    for old_value in (
        "BPM 0.9.0 documentation portal theme",
        "--bpm-docs-surface: #ffffff;",
        "--bpm-docs-accent: #174ea6;",
        "--bpm-docs-accent-strong: #0b3478;",
    ):
        assert old_value not in theme


def test_documentation_theme_primary_light_backgrounds_are_not_pure_white() -> None:
    light_tokens = _light_tokens(_theme())

    assert not re.search(
        r"background(?:-color)?:\s*(?:#fff(?:fff)?|white|rgb\(255,\s*255,\s*255\)|"
        r"rgba\(255,\s*255,\s*255)",
        light_tokens,
        flags=re.IGNORECASE,
    )


def test_documentation_shell_search_and_content_surfaces_use_bpm_tokens() -> None:
    theme = _theme()
    expected_blocks = {
        "html {": "linear-gradient(",
        ".bpm-docs-header {": "var(--bpm-docs-surface)",
        ".bpm-docs-header-control select {": "var(--bpm-docs-control-bg)",
        ".bpm-docs-sidebar,\n.bpm-docs-main {": "var(--bpm-docs-surface)",
        ".bpm-docs-search {": "var(--bpm-docs-surface-muted)",
        ".bpm-docs-search-input {": "var(--bpm-docs-control-bg)",
        ".bpm-docs-search .bpm-docs-search-clear {": "var(--bpm-docs-control-bg)",
        ".bpm-docs-search-filter-grid fieldset {": "var(--bpm-docs-surface)",
        ".bpm-docs-search-result-list li {": "var(--bpm-docs-surface-strong)",
        ".bpm-docs-main :not(pre) > code {": "var(--bpm-docs-surface-accent)",
        ".bpm-docs-main th {": "var(--bpm-docs-surface-strong)",
        ".bpm-docs-main .note,": "var(--bpm-docs-warning-bg)",
    }

    for selector, expected_token in expected_blocks.items():
        assert expected_token in _block(theme, selector)


def test_documentation_dark_theme_mirrors_main_bpm_dark_direction() -> None:
    dark_block = _theme().split("@media (prefers-color-scheme: dark)", 1)[1]

    for declaration in (
        "--bpm-docs-bg: #07111a;",
        "--bpm-docs-bg-mid: #0b1724;",
        "--bpm-docs-bg-end: #0b1b20;",
        "--bpm-docs-surface: rgba(10, 18, 31, 0.78);",
        "--bpm-docs-surface-strong: rgba(12, 21, 35, 0.9);",
        "--bpm-docs-control-bg: rgba(15, 23, 42, 0.86);",
        "--bpm-docs-text: #e2e8f0;",
        "--bpm-docs-text-muted: #94a3b8;",
        "--bpm-docs-accent: #22c55e;",
        "--bpm-docs-accent-strong: #86efac;",
    ):
        assert declaration in dark_block


def test_documentation_theme_has_explicit_light_and_dark_mode_selectors() -> None:
    theme = _theme()

    for selector in (
        'html[data-theme="light"]',
        'html[data-theme="dark"]',
    ):
        assert selector in theme

    assert 'html[data-theme="light"] {\n  color-scheme: light;' in theme

    explicit_dark = _block(theme, 'html[data-theme="dark"] {')
    assert "color-scheme: dark;" in explicit_dark
    assert "--bpm-docs-bg: #07111a;" in explicit_dark
    assert "--bpm-docs-accent: #22c55e;" in explicit_dark


def test_documentation_header_matches_the_product_chrome_and_uses_one_version() -> None:
    source = (REPO_ROOT / "documentation/tools/build_docs.py").read_text(encoding="utf-8")
    theme = _theme()

    assert 'class="bpm-docs-header-main"' in source
    assert (
        'class="bpm-docs-header-title">Browser Policy Manager '
        '<span class="bpm-docs-header-version">v{_escape(product_version)}</span>'
        in source
    )
    assert 'class="bpm-docs-header-context"' not in source
    assert 'class="bpm-docs-header-firefox-versions" data-supported-firefox-versions' in source
    assert 'class="bpm-docs-header-firefox-versions-label">{_escape(labels["supported_firefox_versions"])}' in source
    assert "for channel in SCHEMA_CHANNELS" in source
    assert 'class="bpm-docs-header-control bpm-docs-locale-control"' in source
    assert 'class="bpm-docs-header-control bpm-docs-theme-control"' in source
    assert 'data-docs-locale-select' in source
    assert 'labels["version"]' not in source
    assert "Documentation 0.9.1" not in source

    for selector in (
        ".bpm-docs-header-main {",
        ".bpm-docs-header-title {",
        ".bpm-docs-header-version {",
        ".bpm-docs-header-firefox-versions {",
        ".bpm-docs-header-firefox-versions-label {",
        ".bpm-docs-header-side {",
        ".bpm-docs-header-actions {",
        ".bpm-docs-header-control {",
        "html[data-theme=\"dark\"] .bpm-docs-header-control {",
        "@media (min-width: 61.25rem)",
        "@media (max-width: 51.25rem)",
        "@media (max-width: 35rem)",
    ):
        assert selector in theme
