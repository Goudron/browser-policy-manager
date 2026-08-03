from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import conversation_diagnostics as diagnostics

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-diagnostics-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_06_pins_safe_diagnostics_without_an_http_or_runtime_side_effect() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M7-06"
    assert contract["status"] == "implemented-memory-only-no-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "network_calls": 0,
        "worker_start": False,
        "retrieval": False,
        "persistence": False,
        "telemetry": False,
        "conversation_content": False,
    }
    source = (ROOT / "app/documentation/conversation_diagnostics.py").read_text(encoding="utf-8")
    assert "from fastapi" not in source
    assert "generate(" not in source


def test_m7_06_freezes_diagnostic_categories_and_content_free_shape() -> None:
    contract = _contract()

    assert contract["diagnostic_shape"]["fields"] == [
        "state",
        "assistant_ready",
        "lexical_search_ready",
        "configuration_compatible",
        "model_compatible",
        "index_compatible",
        "load_state",
        "queue_depth_class",
        "last_local_error_class",
        "web_availability",
    ]
    assert contract["diagnostic_shape"]["queue_depth_classes"] == ["idle", "active", "queued"]
    assert contract["diagnostic_shape"]["local_error_classes"] == [
        "none",
        "setup",
        "index",
        "model",
        "runtime",
    ]
    assert diagnostics.AssistantDiagnostics.__annotations__.keys() == set(
        contract["diagnostic_shape"]["fields"]
    )
    truthfulness = " ".join(contract["truthfulness"])
    assert "lexical_search_ready is always true" in truthfulness
    assert "never retains exception text" in truthfulness
