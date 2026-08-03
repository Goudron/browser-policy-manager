from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/documentation-assistant-surface-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m10_02_pins_the_inert_surface_to_existing_security_boundaries() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M10-02"
    assert contract["status"] == "implemented-inert-accessible-surface-no-assistant-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["surface"]["controls"]["initially_disabled"] is True
    assert contract["security_and_resource_boundaries"] == {
        "assistant_http_route": False,
        "status_poll": False,
        "worker_start": False,
        "model_or_runtime_verification": False,
        "retrieval": False,
        "network_calls": 0,
        "web_evidence": False,
        "conversation_content": False,
        "ordinary_search_changed": False,
        "reason": "AI093-T05, AI093-T06 and AI093-T07 remain M10 release blockers. This task adds only inert semantic markup and CSS; it makes no request, no browser-side rendering sink and no worker allocation.",
    }


def test_m10_02_historical_inert_structure_still_has_no_request_path() -> None:
    contract = _contract()
    shell = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js").read_text(encoding="utf-8")

    for required in (
        "data-documentation-assistant-widget",
        'data-assistant-expanded="false"',
        "data-assistant-toggle",
        "data-assistant-panel hidden",
        'role="log"',
        'data-assistant-message-roles="user assistant system"',
        "data-assistant-question",
        "data-assistant-install",
        'maxlength="4000"',
        "disabled aria-disabled=\"true\"",
    ):
        assert required in shell
    assert "documentation-assistant/status" not in shell
    assert "documentation-assistant/chat" not in shell
    assert "documentation-assistant" not in script
    assert "fetch(" not in shell
    assert "<form" not in shell

    for required in (
        ".bpm-docs-assistant-surface",
        ".bpm-docs-assistant-widget",
        ".bpm-docs-assistant-panel",
        ".bpm-docs-assistant-transcript",
        "max-block-size: min(40dvh, 20rem)",
        "max-block-size: none",
        "overscroll-behavior: contain",
        ".bpm-docs-assistant-controls textarea",
        ".bpm-docs-assistant-actions button:disabled",
        "@media (prefers-reduced-motion: reduce)",
        "@media (forced-colors: active)",
    ):
        assert required in theme
    assert contract["surface"]["answer_modes"] == ["answer", "clarify", "abstain", "refuse"]
