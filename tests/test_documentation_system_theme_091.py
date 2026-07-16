from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
THEME_CSS = DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css"
THEME_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"
BUILD_DOCS = DOCUMENTATION_ROOT / "tools/build_docs.py"

SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_documentation_theme_runtime_uses_product_theme_mode_contract() -> None:
    script = _source(THEME_SCRIPT)

    for required in (
        'THEME_STORAGE_KEY = "bpm-theme-mode"',
        'new Set(["system", "light", "dark"])',
        'window.matchMedia("(prefers-color-scheme: dark)")',
        "html.dataset.themeMode = normalizedMode;",
        "html.dataset.theme = resolvedTheme;",
        'themeSelect.addEventListener("change"',
        'mediaQuery.addEventListener("change", handleSystemThemeChange)',
        'mediaQuery.addListener(handleSystemThemeChange)',
        'activeMode === "system"',
        "safeStorageSet(THEME_STORAGE_KEY, normalizedMode);",
    ):
        assert required in script


def test_documentation_css_supports_system_and_explicit_theme_modes() -> None:
    theme = _source(THEME_CSS)

    for required in (
        ":root {\n  color-scheme: light dark;",
        "@media (prefers-color-scheme: dark)",
        'html[data-theme="light"]',
        "color-scheme: light;",
        'html[data-theme="dark"]',
        "color-scheme: dark;",
        "--bpm-docs-bg: #edf2f7;",
        "--bpm-docs-bg: #07111a;",
    ):
        assert required in theme


def test_documentation_shell_exposes_localized_theme_mode_selector() -> None:
    for locale, labels in build_docs.SHELL_LABELS.items():
        for key in ("theme", "theme_system", "theme_light", "theme_dark"):
            assert labels[key].strip(), (locale, key)

    source = _source(BUILD_DOCS)
    for required in (
        '<div class="bpm-docs-theme-control">',
        'data-docs-theme-select',
        '<option value="system">',
        '<option value="light">',
        '<option value="dark">',
        '<meta name="theme-color" content="#edf2f7">',
    ):
        assert required in source
