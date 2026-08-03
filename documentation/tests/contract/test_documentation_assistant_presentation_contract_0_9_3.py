from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = DOCUMENTATION_ROOT / "config/documentation-assistant-presentation-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m10_04_uses_only_validated_final_payloads_without_enabling_chat() -> None:
    contract = _contract()
    renderer = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-renderer.js").read_text(
        encoding="utf-8"
    )
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")

    assert contract["backlog_item"] == "BPM093-M10-04"
    assert contract["status"] == "implemented-validated-final-renderer-without-chat-enable"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["input_boundary"]["exact_payload_fields"] == [
        "api_version", "locale", "bpm_version", "disposition", "text", "sources"
    ]
    assert contract["boundaries"] == {
        "page_load": "The renderer only registers a future-callable function. It makes no fetch, model check, retrieval, worker start, request, poll or DOM update on page load.",
        "assistant_http_route": False,
        "chat_controls_enabled": False,
        "ordinary_search_changed": False,
        "web_request": False,
    }
    for required in (
        "validPayload(payload)",
        "payload.disposition === \"answer\"",
        "payload.sources.some((source) => source.provenance === \"local\")",
        "Object.keys(source).length !== 9",
        'document.createElement("details")',
        "createElement",
        "textContent",
        "noopener noreferrer",
        "window.BPMDocumentationAssistantRenderer",
    ):
        assert required in renderer
    for forbidden in (
        "fetch(",
        "EventSource",
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "documentation-assistant/chat",
    ):
        assert forbidden not in renderer
    assert "ASSISTANT_RENDERER_SCRIPT" in builder
    for required in (
        ".bpm-docs-assistant-answer-mode",
        ".bpm-docs-assistant-sources",
        ".bpm-docs-assistant-sources a",
    ):
        assert required in theme


def test_m10_04_copy_uses_locale_owned_mode_and_source_metadata_labels() -> None:
    catalog = json.loads(
        (DOCUMENTATION_ROOT / "config/documentation-assistant-copy-0.9.3.json").read_text(
            encoding="utf-8"
        )
    )
    required = {"source_guide", "source_topic", "source_anchor", "source_version", "source_excerpt"}

    for locale in catalog["locales"]:
        dialogue = catalog["catalog"][locale]["dialogue"]
        assert required <= set(dialogue)
        assert all(dialogue[key].strip() for key in required)
        assert "{guide}" in dialogue["source_guide"]
        assert "{topic}" in dialogue["source_topic"]
        assert "{anchor}" in dialogue["source_anchor"]
        assert "{version}" in dialogue["source_version"]
