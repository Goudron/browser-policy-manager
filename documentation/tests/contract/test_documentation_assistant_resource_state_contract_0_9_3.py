from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = (
    DOCUMENTATION_ROOT / "config/documentation-assistant-resource-state-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m10_05_renders_only_reviewed_resource_states_without_enabling_chat() -> None:
    contract = _contract()
    state_machine = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-state-machine.js"
    ).read_text(encoding="utf-8")
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")

    assert contract["backlog_item"] == "BPM093-M10-05"
    assert contract["status"] == "implemented-transport-free-resource-state-renderer"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["input_boundary"]["exact_snapshot_fields"] == [
        "api_version", "locale", "state", "state_epoch"
    ]
    assert contract["boundaries"] == {
        "page_load": "The script only registers a future-callable function. It performs no fetch, model inspection, status poll, retrieval, worker start, timeout, retry, unload, request or DOM update on page load.",
        "assistant_http_route": False,
        "chat_controls_enabled": False,
        "ordinary_search_changed": False,
        "web_request": False,
    }
    for required in (
        "exactKeys(snapshot, [\"api_version\", \"locale\", \"state\", \"state_epoch\"])",
        "snapshot.state_epoch <= previousEpoch",
        "stateEpochs = new WeakMap()",
        "data-assistant-recovery",
        "BPMDocumentationAssistantStateMachine",
        "recoverySearch.hidden = false",
    ):
        assert required in state_machine
    for forbidden in (
        "fetch(",
        "EventSource",
        "setTimeout(",
        "setInterval(",
        ".disabled = false",
        "documentation-assistant/chat",
        "innerHTML",
    ):
        assert forbidden not in state_machine
    assert "ASSISTANT_STATE_MACHINE_SCRIPT" in builder
    assert "data-assistant-recovery-search" not in builder


def test_m10_05_resource_messages_are_reviewed_in_every_locale() -> None:
    catalog = json.loads(
        (DOCUMENTATION_ROOT / "config/documentation-assistant-copy-0.9.3.json").read_text(
            encoding="utf-8"
        )
    )
    required = {
        "queued",
        "timeout",
        "unloading",
        "unloaded",
        "search_only",
        "duplicate",
        "resource_limit",
    }

    for locale in catalog["locales"]:
        messages = catalog["catalog"][locale]["resource_states"]
        assert set(messages) == required
        assert all(messages[key].strip() for key in required)
