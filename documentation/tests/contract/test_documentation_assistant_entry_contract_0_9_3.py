from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/documentation-assistant-entry-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m10_01_pins_the_existing_safe_assistant_boundaries() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M10-01"
    assert contract["status"] == "implemented-static-entry-no-assistant-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["portal_entry"]["initial_state"] == "unavailable"
    assert contract["portal_entry"]["interactive_controls"] is False
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]


def test_m10_01_historical_static_entry_does_not_change_search_or_enable_transport() -> None:
    contract = _contract()
    shell = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")
    print_theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-print.css").read_text(
        encoding="utf-8"
    )
    script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js").read_text(encoding="utf-8")

    assert "bpm-docs-discovery-tools" in shell
    assert shell.index("{discovery_shell}") < shell.index("{assistant_shell}")
    assert 'data-assistant-state="unavailable"' in shell
    assert "documentation-assistant/status" not in shell
    assert "documentation-assistant" not in script
    assert ".bpm-docs-assistant-widget" in theme
    assert "grid-template-columns: minmax(0, 1fr)" in theme
    assert ".bpm-docs-assistant-widget" in print_theme
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
        "reason": "AI093-T05 remains a release blocker. M10-01 therefore adds no assistant request surface before body, schema, same-origin and CSRF controls are composed and tested.",
    }
