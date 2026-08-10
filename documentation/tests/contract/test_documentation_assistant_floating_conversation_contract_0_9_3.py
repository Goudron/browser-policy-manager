from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"

pytestmark = pytest.mark.docs_contract


def test_m12b_03_limits_persistence_to_locale_private_text_only_session_state() -> None:
    source = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-conversation.js").read_text(
        encoding="utf-8"
    )
    builder = (DOCUMENTATION_ROOT / "buildlib/portal.py").read_text(encoding="utf-8")

    for required in (
        'STORAGE_PREFIX = "bpm.documentation-assistant.floating.v1."',
        "const MAX_TURNS = 8",
        '"tab_id"',
        '"web_enabled"',
        "window.crypto.getRandomValues",
        "window.sessionStorage.getItem",
        "window.sessionStorage.setItem",
        "validTurn",
        "document.createElement",
        "message.textContent = value",
        "recordCompletedTurn",
        "setWebEnabled",
        "webState",
        "data-assistant-clear",
        "ASSISTANT_CONVERSATION_SCRIPT",
    ):
        assert required in source or required in builder
    for forbidden in (
        "fetch(",
        "EventSource",
        "localStorage",
        "IndexedDB",
        "document.cookie",
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "telemetry",
        "documentation-assistant/chat",
    ):
        assert forbidden not in source


def test_m12b_03_has_short_locale_owned_ready_and_clear_labels() -> None:
    from documentation.tools import build_docs

    expected = {
        "en": ("Ready", "Clear"),
        "ru": ("Готов", "Очистить"),
        "de": ("Bereit", "Löschen"),
        "zh-CN": ("就绪", "清除"),
        "fr": ("Prêt", "Effacer"),
        "es-ES": ("Listo", "Limpiar"),
    }

    for locale, (ready, clear) in expected.items():
        copy = build_docs._assistant_copy_payload(locale)["messages"]["shell"]
        assert copy["assistant_ready"] == ready
        assert copy["assistant_clear_short"] == clear


def test_m13_04_keeps_eight_completed_pairs_and_a_tab_private_clear_boundary() -> None:
    conversation = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-conversation.js"
    ).read_text(encoding="utf-8")
    transport = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js").read_text(
        encoding="utf-8"
    )

    assert "const MAX_TURNS = 8" in conversation
    assert ".slice(-MAX_TURNS)" in conversation
    assert 'state === "cancelled" || state === "error"' in transport
    assert "function recoverableFailure(context)" in transport
    assert 'setVisualState(context, "error")' in transport
    assert (
        "conversation?locale=${encodeURIComponent(context.locale)}&tab_id=${encodeURIComponent(context.tabId)}"
        in transport
    )


def test_m13_05_keeps_the_advisory_preview_out_of_persisted_dialogue() -> None:
    conversation = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-conversation.js"
    ).read_text(encoding="utf-8")

    assert "const pendingTurns = new WeakMap()" in conversation
    assert "function showPendingTurn(widget, turn)" in conversation
    assert "function replacePendingTurn(widget, assistant)" in conversation
    assert "pendingTurns.delete(widget);" in conversation
    assert "window.sessionStorage.setItem" in conversation
