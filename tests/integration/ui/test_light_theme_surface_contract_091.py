from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CSS_ROOT = REPO_ROOT / "app/static/profiles_css"
LAYER_PATHS = [
    CSS_ROOT / "00-foundation.css",
    CSS_ROOT / "10-library.css",
    CSS_ROOT / "20-shell.css",
    CSS_ROOT / "21-settings.css",
    CSS_ROOT / "22-guided-wizard.css",
    CSS_ROOT / "23-workspace-editor.css",
    CSS_ROOT / "24-theme-overrides.css",
    CSS_ROOT / "40-compact-shell.css",
]


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _block(source: str, selector: str) -> str:
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def test_main_light_theme_tokens_use_gray_surfaces_instead_of_white_panels() -> None:
    foundation = _source(CSS_ROOT / "00-foundation.css")
    light_tokens = foundation.split('html[data-theme="dark"] {', 1)[0]

    for declaration in (
        "--bg-top: #edf2f7;",
        "--bg-mid: #e7edf4;",
        "--bg-bottom: #dfeae8;",
        "--panel: rgba(235, 240, 246, 0.9);",
        "--panel-strong: rgba(226, 232, 240, 0.94);",
        "--list-button-bg: rgba(229, 236, 243, 0.88);",
        "--list-button-hover-bg: rgba(220, 228, 237, 0.96);",
        "--surface-soft-bg: rgba(226, 232, 240, 0.72);",
        "--control-bg: rgba(226, 232, 240, 0.86);",
        "--control-hover-bg: rgba(218, 226, 236, 0.94);",
        "--control-focus-bg: rgba(211, 222, 233, 0.98);",
        "--raised-surface-bg: rgba(232, 238, 245, 0.84);",
        "--raised-surface-strong-bg: rgba(224, 232, 241, 0.92);",
        "--hero-panel-start: rgba(230, 237, 245, 0.92);",
        "--hero-panel-end: rgba(217, 226, 236, 0.82);",
    ):
        assert declaration in light_tokens

    for old_white_panel in (
        "--panel: rgba(255, 255, 255",
        "--panel-strong: rgba(255, 255, 255",
        "--list-button-bg: rgba(255, 255, 255",
        "--list-button-hover-bg: rgba(255, 255, 255",
    ):
        assert old_white_panel not in light_tokens


def test_main_light_theme_primary_backgrounds_do_not_use_white_declarations() -> None:
    forbidden = (
        "background: rgba(255, 255, 255",
        "background-color: rgba(255, 255, 255",
        "linear-gradient(135deg, rgba(255, 255, 255",
        "linear-gradient(180deg, rgba(255, 255, 255",
    )

    for path in LAYER_PATHS:
        source = _source(path)
        for snippet in forbidden:
            assert snippet not in source, f"{path.relative_to(REPO_ROOT)} still has {snippet}"


def test_main_light_theme_primary_surface_selectors_are_tokenized() -> None:
    foundation = _source(CSS_ROOT / "00-foundation.css")
    library = _source(CSS_ROOT / "10-library.css")
    wizard = "".join(_source(path) for path in LAYER_PATHS[2:7])
    compact = _source(CSS_ROOT / "40-compact-shell.css")

    expected_blocks = {
        ".hero-shell {": "var(--hero-panel-start)",
        ".soft-input {": "var(--control-bg)",
        ".theme-subcard {": "var(--raised-surface-bg)",
        ".editor-frame {": "var(--raised-surface-strong-bg)",
        ".library-row-meta-primary {": "var(--neutral-surface-bg)",
        ".all-settings-domain-card {": "var(--raised-surface-bg)",
        ".all-settings-review-card {": "var(--raised-surface-bg)",
        ".wizard-search-engine-preset {": "var(--raised-surface-bg)",
        'html[data-theme="light"] .soft-input {': "var(--control-bg)",
        ".compact-toolbar-control {": "var(--raised-surface-strong-bg)",
    }
    sources = foundation + library + wizard + compact
    for selector, expected_token in expected_blocks.items():
        assert expected_token in _block(sources, selector)


def test_focus_status_disabled_and_destructive_states_remain_explicit() -> None:
    foundation = _source(CSS_ROOT / "00-foundation.css")
    wizard = "".join(_source(path) for path in LAYER_PATHS[2:7])
    compact = _source(CSS_ROOT / "40-compact-shell.css")
    source = foundation + wizard + compact

    for required in (
        ".soft-input:focus {",
        "box-shadow: 0 0 0 4px color-mix(in srgb, var(--focus-ring-color), transparent 76%);",
        ".soft-input.input-invalid {",
        "border-color: var(--status-warn-border);",
        ".status-banner--warn {",
        ".status-banner--error {",
        ".all-settings-domain-card:disabled {",
        ".all-settings-review-card:disabled {",
        ".danger-button {",
        ".danger-button:hover {",
        '.context-help-icon-link[aria-disabled="true"] {',
    ):
        assert required in source
