from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"

pytestmark = pytest.mark.docs_contract


def test_m12b_02_renders_the_title_only_floating_shell_without_transport() -> None:
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")
    shell = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-shell.js").read_text(
        encoding="utf-8"
    )

    for required in (
        "data-documentation-assistant-widget",
        'data-assistant-expanded=\"false\"',
        "data-assistant-toggle",
        "data-assistant-panel hidden",
        "data-assistant-collapse",
        "data-assistant-transcript",
        "data-assistant-question",
        "data-assistant-install",
        "ASSISTANT_SHELL_SCRIPT",
    ):
        assert required in builder
    for forbidden in ("fetch(", "EventSource", "sessionStorage", "localStorage", "innerHTML"):
        assert forbidden not in shell
    assert "setExpanded" in shell
    assert 'event.key === "Escape"' in shell


def test_m12b_02_uses_viewport_bounded_overlay_geometry_and_portal_tokens() -> None:
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    print_theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-print.css").read_text(
        encoding="utf-8"
    )

    for required in (
        ".bpm-docs-assistant-widget",
        "position: fixed",
        "inset-inline-end: max(1rem, env(safe-area-inset-right))",
        "block-size: 90dvh",
        "inline-size: 50vw",
        "grid-template-rows: auto minmax(0, 1fr) auto auto",
        ".bpm-docs-assistant-widget .bpm-docs-assistant-transcript",
        "max-block-size: none",
        "@media (max-width: 48rem)",
        "inline-size: calc(100vw - 2rem)",
        "@media (prefers-reduced-motion: reduce)",
        "@media (forced-colors: active)",
    ):
        assert required in theme
    assert ".bpm-docs-assistant-widget" in print_theme


def test_m12b_02_has_the_approved_six_locale_collapsed_titles() -> None:
    from documentation.tools import build_docs

    expected = {
        "en": "BPM AI Assistant",
        "ru": "ИИ-помощник BPM",
        "de": "BPM-KI-Assistent",
        "zh-CN": "BPM AI 助手",
        "fr": "Assistant IA BPM",
        "es-ES": "Asistente de IA de BPM",
    }

    assert {locale: build_docs.SHELL_LABELS[locale]["assistant"] for locale in expected} == expected


def test_m13_05_has_a_seconds_precision_preview_template_in_all_six_locales() -> None:
    from documentation.tools import build_docs

    for locale in build_docs.LOCALES:
        template = build_docs.SHELL_LABELS[locale]["assistant_time_preview"]
        assert "{minimum}" in template and "{maximum}" in template
        shell = build_docs._assistant_copy_payload(locale)["messages"]["shell"]
        assert shell["assistant_time_preview"] == template
        assert shell["assistant_answer_failed"]
