from __future__ import annotations

from tests.docs_index import doc_path_from_index

AUDIT_PATH = "architecture/bpm-documentation-theme-token-audit-0.9.1.md"


def _audit() -> str:
    return " ".join(doc_path_from_index(AUDIT_PATH, status="audit").read_text().split())


def test_theme_token_audit_is_scoped_to_091_and_excludes_generated_vendor_output():
    audit = _audit()

    assert "Status: audit for `BPM091-M3-01`" in audit
    assert "Target BPM version: `0.9.1`" in audit
    assert "it does not implement the darker light theme" in audit

    for included in (
        "app/static/profiles_css/00-foundation.css",
        "app/static/profiles_css/10-library.css",
        "app/static/profiles_css/20-shell.css",
        "app/static/profiles_css/21-settings.css",
        "app/static/profiles_css/22-guided-wizard.css",
        "app/static/profiles_css/23-workspace-editor.css",
        "app/static/profiles_css/24-theme-overrides.css",
        "app/static/profiles_css/30-responsive.css",
        "app/static/profiles_css/40-compact-shell.css",
        "documentation/assets/theme/bpm-docs.css",
        "documentation/assets/theme/bpm-docs-print.css",
    ):
        assert included in audit

    for excluded in (
        "app/static/vendor/",
        "app/documentation/site/",
        "documentation/build/",
        "documentation/dist/",
        "documentation/reports/",
        "documentation/.cache/",
        "docs/screenshots/",
    ):
        assert excluded in audit


def test_theme_token_audit_names_product_tokens_and_selectors_needing_work():
    audit = _audit()

    for token in (
        "`--bg-top: #f6efe4`, `--bg-mid: #f8f7f1`, `--bg-bottom: #e8f2f0`",
        "`--panel: rgba(255, 255, 255, 0.82)`",
        "`--panel-strong: rgba(255, 255, 255, 0.92)`",
        "`--list-button-bg`, `--list-button-hover-bg`, `--list-button-border`",
        "`.hero-shell`",
        "`.soft-input`, `.soft-input:hover`, `.soft-input:focus`",
        "`.theme-subcard`",
        "`.editor-frame`",
    ):
        assert token in audit

    for selector in (
        "`.library-row-meta-primary`",
        '`[class~="bg-white"]`, `[class~="bg-white/80"]`, `[class~="bg-white/70"]`',
        "`.compare-target-name`, `.compare-summary-value`, `.compare-changes-copy`, `.compare-changes-item`",
        "`.all-settings-domain-card`, `.all-settings-domain-card:disabled:hover`, `.all-settings-review-card`, `.all-settings-review-card:disabled:hover`",
        "`.wizard-step--active`",
        "`.wizard-search-engine-preset`, `.wizard-search-engine-preset:hover`, `.wizard-search-engine-card`",
        '`html[data-theme="light"] .soft-input`, `html[data-theme="light"] .soft-input:hover`, `html[data-theme="light"] .soft-input:focus`',
        "`.compact-toolbar-docs-link`, `.context-help-link`, `.context-help-icon-link`",
    ):
        assert selector in audit


def test_theme_token_audit_names_documentation_tokens_and_system_theme_gap():
    audit = _audit()

    for finding in (
        "Header comment `BPM 0.9.0 documentation portal theme`",
        "`:root { color-scheme: light dark; }`",
        "`--bpm-docs-surface: #ffffff`",
        "`--bpm-docs-bg`, `--bpm-docs-surface-muted`, `--bpm-docs-border`, `--bpm-docs-accent`, `--bpm-docs-focus`",
        "`@media (prefers-color-scheme: dark) :root`",
        "`.bpm-docs-header`, `.bpm-docs-sidebar`, `.bpm-docs-main`",
        "`.bpm-docs-search`, `.bpm-docs-search-input`, `.bpm-docs-search-result-list li`",
        "`.bpm-docs-main :not(pre) > code`, `.bpm-docs-main th`, `.bpm-docs-main .note*`",
    ):
        assert finding in audit

    assert "white paper and black text for print output" in audit
    assert "not a light-theme product surface blocker" in audit
    assert (
        'lacks explicit `html[data-theme="light"]`, `html[data-theme="dark"]`, and `html[data-theme="system"]` behavior'
        in audit
    )


def test_theme_token_audit_routes_findings_to_follow_up_tasks():
    audit = _audit()

    for task_id in ("BPM091-M3-02", "BPM091-M3-03", "BPM091-M3-04", "BPM091-M3-05"):
        assert f"`{task_id}`" in audit

    for risk in (
        "Pure-white and translucent-white values are duplicated instead of centralized",
        "Product and documentation themes use different token namespaces and accent families",
        "hardcode text colors instead of using `--ink`, `--muted`, or docs equivalents",
        "No generated documentation output, installed `/help/` site, vendor files",
    ):
        assert risk in audit
