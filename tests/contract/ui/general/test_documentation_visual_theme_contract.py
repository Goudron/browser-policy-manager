from __future__ import annotations

from tests.docs_index import doc_path_from_index

CONTRACT_PATH = "architecture/product-documentation-visual-theme-contract-0.9.1.md"


def _contract() -> str:
    return " ".join(doc_path_from_index(CONTRACT_PATH, status="active").read_text().split())


def test_documentation_visual_theme_contract_is_active_and_scoped_to_091():
    contract = _contract()

    assert "Backlog item: `BPM091-M2-03`" in contract
    assert "not evidence that the current `bpm-docs.css` already satisfies every rule" in contract
    assert (
        "Generated HTML, installed `app/documentation/site/` files, and search indexes must not be hand-edited"
        in contract
    )

    for source in (
        "app/static/profiles_css/00-foundation.css",
        "documentation/assets/theme/bpm-docs.css",
        "documentation/assets/theme/bpm-docs-print.css",
        "documentation/tools/build_docs.py",
        "documentation/assets/theme/bpm-docs-search.js",
        "product-documentation-accessibility-security-contract-0.9.0.md",
        "documentation-portal-blocker-audit-0.9.1.md",
    ):
        assert source in contract


def test_documentation_visual_theme_contract_defines_modes_and_light_surface_rule():
    contract = _contract()

    for requirement in (
        "`light`: explicit light mode using comfortable light-gray primary surfaces.",
        "`dark`: explicit dark mode using the main BPM dark-mode direction.",
        "`system`: follows `prefers-color-scheme` until the user chooses an explicit mode.",
        "`html[data-theme]`",
        "explicit light and dark modes must not depend on operating-system preference",
        "Light theme must not use pure white as a primary surface.",
        "`#ffffff`, `white`, or equivalent pure-white primary backgrounds",
        "Page background, shell header, sidebar, main content surface, search surface",
    ):
        assert requirement in contract


def test_documentation_visual_theme_contract_covers_surface_accessibility_and_media():
    contract = _contract()

    for requirement in (
        "header, sidebar/tree, search, main topic body, footer, callouts, tables, result rows",
        "inputs, selects if introduced, buttons, links, disclosure controls, search filters, and tree controls",
        "Code blocks",
        "Tables",
        "Notes and warnings",
        "Screenshots",
        "WCAG 2.2 AA",
        "at least 3:1",
        "`prefers-reduced-motion`",
        "`forced-colors: active`",
        "Print output",
        "320 CSS pixels",
        "must not read as a single hue family",
    ):
        assert requirement in contract


def test_documentation_visual_theme_contract_routes_verification_to_backlog_tasks():
    contract = _contract()

    for task_id in (
        "BPM091-M3-01",
        "BPM091-M3-02",
        "BPM091-M3-03",
        "BPM091-M3-04",
        "BPM091-M3-05",
    ):
        assert f"`{task_id}`" in contract

    for command in (
        "make test-docs-contract",
        "make test-docs-ui",
        "make test-docs-browser",
        "make test-ui",
        "make test-release",
    ):
        assert f"`{command}`" in contract
