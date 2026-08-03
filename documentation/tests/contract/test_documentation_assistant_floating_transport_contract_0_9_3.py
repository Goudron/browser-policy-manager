from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"

pytestmark = pytest.mark.docs_contract


def test_m12b_04_binds_only_reviewed_same_origin_transport_after_user_activation() -> None:
    source = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js"
    ).read_text(encoding="utf-8")
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")

    for required in (
        'const API_ROOT = "/api/documentation-assistant"',
        '"bpm-documentation-assistant-toggle"',
        'event.detail && event.detail.expanded',
        'web_mode: "local_only"',
        "tab_id: context.tabId",
        "new EventSource(streamPath)",
        "/chat/${encodeURIComponent(requestId)}/cancel",
        'method: "DELETE"',
        "conversation?locale=${encodeURIComponent(context.locale)}&tab_id=${encodeURIComponent(context.tabId)}",
        "sourcesFor",
        "validSource",
        "validCancellation",
        "recordCompletedTurn",
        "appendExternalClaims",
        "approvedExternalUrl",
        "ASSISTANT_TRANSPORT_SCRIPT",
    ):
        assert required in source or required in builder
    assert "webModePath(context)" not in source
    assert "requestWebMode(context, enabled)" not in source
    for forbidden in (
        "brave.com",
        "http://",
        "https://",
        "localStorage",
        "IndexedDB",
        "document.cookie",
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "setInterval(",
    ):
        assert forbidden not in source


def test_m12b_04_keeps_status_and_sources_bounded_to_the_current_locale() -> None:
    source = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js"
    ).read_text(encoding="utf-8")

    for required in (
        "validStatus(status, context.locale)",
        "validSource(source, sourceId, context.locale)",
        "sameOriginPath(value.published_url, `/help/${locale}/`)",
        "value.request_id !== requestId",
        "event.state_epoch < context.epoch",
        "sources.length !== event.citations.length",
        "closeStream(context)",
    ):
        assert required in source
    assert "const claims = event.disposition === \"answer\" && Array.isArray(event.external_claims)" in source
    assert "      : [];\n    const externalSourceIds" in source


def test_m13_05_renders_a_locale_owned_seconds_range_then_replaces_the_pending_turn() -> None:
    source = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js"
    ).read_text(encoding="utf-8")

    for required in (
        "validTimePreview",
        '\"minimum_seconds\"',
        '\"maximum_seconds\"',
        "function durationText(locale, totalSeconds)",
        "russianDurationUnit",
        "assistantLabelTimePreview",
        "assistantLabelAnswerFailed",
        "showPendingTurn",
        "replacePendingTurn",
        "await cancel(context)",
    ):
        assert required in source
    assert "hardware identifier" not in source
