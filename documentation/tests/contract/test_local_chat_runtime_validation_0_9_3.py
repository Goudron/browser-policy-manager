from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/local-chat-runtime-validation-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m6_07_keeps_locale_context_output_and_fallback_claims_bounded() -> None:
    contract = _contract()

    cases = contract["runtime_cases"]
    assert "Jinja template" in cases["accepted_template"]
    assert "UTF-8" in cases["unicode_and_locale"]
    assert "does not translate, merge, or fall back" in cases["unicode_and_locale"]
    assert "no <think> tag" in cases["bounded_output"]
    assert "seed 0" in cases["determinism"]
    assert "2,048-token budget" in cases["context"]
    assert "never silently truncated" in cases["context"]
    assert "cancellation" in cases["lifecycle"]

    fallback = contract["fallback"]
    assert fallback["states"] == [
        "disabled",
        "not-installed",
        "incompatible",
        "cancelled",
        "crashed",
    ]
    assert "assistant_ready false" in fallback["rule"]
    assert "lexical_search_ready true" in fallback["rule"]
    assert "core /health/ready" in fallback["rule"]

    real_probe = contract["real_probe"]
    assert real_probe["runner"] == "documentation/tools/run_local_chat_worker_validation_0_9_3.py"
    assert "flushed stdout progress" in real_probe["output"]
    assert "No network request" in real_probe["network"]
