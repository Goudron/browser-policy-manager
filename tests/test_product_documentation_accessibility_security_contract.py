from __future__ import annotations

import re

from tests.docs_index import doc_path_from_index

CONTRACT_PATH = "architecture/product-documentation-accessibility-security-contract-0.9.0.md"


def _contract() -> str:
    path = doc_path_from_index(CONTRACT_PATH, status="active")
    return " ".join(path.read_text(encoding="utf-8").split())


def _csp_block() -> str:
    path = doc_path_from_index(CONTRACT_PATH, status="active")
    contract = path.read_text(encoding="utf-8")
    match = re.search(
        r"implementation target:\n\n```text\n(?P<csp>.*?)\n```",
        contract,
        flags=re.DOTALL,
    )
    assert match is not None
    return " ".join(match.group("csp").split())


def test_documentation_accessibility_security_contract_sets_scope_and_wcag_target():
    contract = _contract()

    assert "Status: **Accepted for BPM 0.9.0**" in contract
    assert "Backlog item: `BPM090-M2-10`" in contract
    assert "**WCAG 2.2 Level AA**" in contract
    assert "not a claim that one automated scan proves conformance" in contract
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in contract
    for state in ("guide homes", "topics", "search states", "aliases", "tombstones", "unavailable/error pages"):
        assert state in contract


def test_accessibility_contract_defines_semantics_keyboard_and_focus():
    contract = _contract()

    for requirement in (
        "exactly one visible primary `<h1>`",
        "`<main id=\"main-content\">`",
        "`<html lang>` is exactly the route locale",
        "visible-on-focus skip link to `#main-content`",
        "There is no keyboard trap",
        "Focus order follows reading and task order.",
        "is not fully obscured",
        "at least 3:1 contrast",
        "`aria-expanded` and `aria-controls`",
        "normally at least 24 by 24 CSS pixels",
        "not an ARIA `application`",
    ):
        assert requirement in contract


def test_accessibility_contract_defines_visual_reflow_media_and_content_rules():
    contract = _contract()

    for requirement in (
        "Normal text meets 4.5:1 contrast",
        "Text resizes to 200%",
        "400% zoom / a 320 CSS-pixel content width",
        "light, dark, forced-colors/high-contrast",
        "`prefers-reduced-motion`",
        "Every informative image has concise localized alt text",
        "Complex diagrams have a nearby structured text equivalent.",
        "Data tables have a localized caption",
        "Layout tables are forbidden.",
        "Code is emitted as escaped text inside `pre`/`code`",
        "Destructive commands",
    ):
        assert requirement in contract


def test_accessibility_contract_covers_navigation_search_and_error_states():
    contract = _contract()

    for requirement in (
        "Repeated “click here/read more” links",
        "do not open a new tab by default",
        "`rel=\"noopener noreferrer\"`",
        "Search has a programmatic and visible localized label",
        "does not move focus on every keystroke",
        "`role=\"status\"`/`aria-live=\"polite\"`",
        "no-results, malformed-index, and unavailable states",
        "Documentation unavailable, invalid manifest, unsupported version, 404",
        "without exposing filesystem paths, hashes, stack traces",
    ):
        assert requirement in contract


def test_security_contract_rejects_active_html_and_unsafe_dom_sinks():
    contract = _contract()

    for requirement in (
        "network and external-entity resolution disabled",
        "Raw HTML passthrough and active-content constructs are forbidden.",
        "`script`, inline event handlers, `iframe`, `frame`, `object`, `embed`, `applet`, `form`, active SVG",
        "reviewed first-party search script",
        "Inline scripts, remote scripts, module imports",
        "never concatenated as markup",
        "only the approved element and attribute set is present",
        "This allowlist validation is not presented as a general HTML sanitizer.",
        "parsed as data; `eval`, `Function`",
        "limited to 256 Unicode scalar values",
        "maximum 50 visible results per query",
        "inserted with `textContent`",
        "`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`",
        "index content never controls element names or attributes",
        "locale-scoped browser `localStorage`",
        "not persisted in cookies, logs, the BPM profile database, or any server-side state",
    ):
        assert requirement in contract


def test_security_contract_defines_strict_help_csp_without_unsafe_sources():
    csp = _csp_block()

    for directive in (
        "default-src 'none'",
        "script-src 'self'",
        "script-src-attr 'none'",
        "style-src 'self'",
        "style-src-attr 'none'",
        "img-src 'self'",
        "font-src 'self'",
        "connect-src 'self'",
        "worker-src 'none'",
        "frame-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "frame-ancestors 'none'",
    ):
        assert f"{directive};" in csp or csp.endswith(directive)
    for unsafe_source in ("'unsafe-inline'", "'unsafe-eval'", "data:", "https:", "http:", "*"):
        assert unsafe_source not in csp


def test_security_contract_defines_path_assets_examples_and_privacy_boundaries():
    contract = _contract()

    for requirement in (
        "regular non-symlink file below the activated artifact root",
        "matches its SHA-256",
        "absolute paths, `..`, encoded separators, backslashes, NUL/control bytes",
        "serves only `GET` and `HEAD`",
        "Remote scripts, styles, fonts, images, iframes, embeds, CDN resources",
        "HTML/SVG supplied as downloadable examples is forbidden",
        "`https://example.invalid`",
        "do not use `curl | sh`",
        "most recent query may be persisted only",
        "not persisted in cookies, logs, the BPM profile database, or any server-side state",
        "not a service worker",
    ):
        assert requirement in contract


def test_security_contract_defines_headers_caching_and_hsts_boundary():
    contract = _contract()

    for header in (
        "`Content-Security-Policy`",
        "`X-Content-Type-Options`",
        "`Referrer-Policy`",
        "`X-Frame-Options`",
        "`X-XSS-Protection`",
        "`Permissions-Policy`",
        "`Cross-Origin-Resource-Policy`",
        "`Cross-Origin-Opener-Policy`",
        "`Content-Type`",
        "`Cache-Control`",
    ):
        assert f"| {header} |" in contract
    for value in (
        "`nosniff`",
        "`no-referrer`",
        "`DENY`",
        "`same-origin`",
        "`geolocation=(), microphone=(), camera=()`",
    ):
        assert value in contract
    assert "HSTS is deployment-specific and is not enabled by this documentation architecture task." in contract


def test_contract_defines_layered_verification_and_release_blockers():
    contract = _contract()

    for layer in (
        "DITA authoring",
        "Static HTML contract",
        "CSS/static audit",
        "Keyboard browser smoke",
        "Automated accessibility scan",
        "Manual accessibility review",
        "Security static contract",
        "HTTP/browser security",
    ):
        assert f"| {layer} |" in contract
    for requirement in (
        "Zero serious/critical violations",
        "all six locales",
        "Browser and screenshot checks run with immediate sandbox escalation",
        "no accessibility/security exception is a blanket suppression",
        "## Blocking Acceptance Checklist",
    ):
        assert requirement in contract
