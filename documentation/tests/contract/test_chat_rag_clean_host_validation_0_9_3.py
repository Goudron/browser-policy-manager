from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
VALIDATION_PATH = ROOT / "documentation/config/chat-rag-clean-host-validation-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _validation() -> dict:
    return json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))


def test_clean_host_attempt_truthfully_records_the_failed_no_swap_gate() -> None:
    validation = _validation()

    assert validation["backlog_item"] == "BPM093-M5-03D"
    assert validation["status"] == "failed-before-quality-measurement"
    contract = ROOT / validation["input_contract"]["path"]
    assert (
        validation["input_contract"]["sha256"] == hashlib.sha256(contract.read_bytes()).hexdigest()
    )
    assert validation["candidate"]["id"] == "multilingual-e5-base-onnx-o4"
    assert validation["swap_validation"]["changed"] is True
    assert (
        validation["swap_validation"]["before_bytes"]
        != validation["swap_validation"]["observed_after_bytes"]
    )
    assert validation["disposition"]["measurement_completed"] is False


def test_failed_clean_host_attempt_is_historical_diagnostic_and_keeps_m4_unchanged() -> None:
    validation = _validation()

    effect = validation["disposition"]["release_effect"]
    assert "Historical diagnostic only" in effect
    assert "M4 ordinary search remains unchanged" in effect
    assert "do not use it to reject E5-base" in validation["disposition"]["next_attempt"]
