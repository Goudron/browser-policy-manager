from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    ROOT
    / "documentation/config/documentation-assistant-external-evidence-release-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m12a_04_freezes_local_precedence_safe_fallback_and_no_call_events() -> None:
    contract = _contract()

    assert (
        "current same-locale answer-ready local BPM evidence" in contract["admission"]["required"]
    )
    assert contract["admission"]["provider_calls_per_question_max"] == 1
    assert contract["evidence_and_answer"]["conflict"].startswith("abstain")
    assert contract["fallback"]["ordinary_search_changed"] is False
    assert contract["fallback"]["unexpected_network_fallback"] is False
    assert "web-mode toggle" in contract["no_call_events"]
    assert "off-topic question" in contract["no_call_events"]

    conversation = (ROOT / "app/documentation/conversation.py").read_text(encoding="utf-8")
    service = (ROOT / "app/documentation/assistant_service.py").read_text(encoding="utf-8")
    runtime = (ROOT / "app/documentation/local_assistant_runtime.py").read_text(encoding="utf-8")
    assert "_generate_with_optional_web" in conversation
    assert "external_claims" in conversation
    assert "effective_web_mode" in service
    assert "ScopedWebEvidenceRetriever" in runtime
    assert "ConservativeEvidenceMerger" in runtime
