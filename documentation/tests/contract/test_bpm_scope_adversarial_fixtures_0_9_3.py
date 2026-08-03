from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-scope-adversarial-fixtures-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_03_pins_scope_authority_and_fixed_six_locale_escape_cases() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M8-03"
    assert contract["status"] == "implemented-fixed-adversarial-fixtures"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    expected_categories = {
        "jailbreak",
        "role_change",
        "translation_trick",
        "encoded_request",
        "prompt_extraction",
        "fictional_framing",
        "long_padding",
        "context_off_topic",
    }
    assert set(contract["required_categories"]) == expected_categories
    assert set(contract["locale_cases"]) == set(contract["locales"])
    assert all(set(cases) == expected_categories for cases in contract["locale_cases"].values())
    assert {case["category"] for case in contract["code_switched_cases"]} == {
        "mixed_script",
        "percent_encoded",
        "unicode_escape",
        "base64_prefixed",
    }


def test_m8_03_locks_fail_closed_downstream_and_product_boundaries() -> None:
    contract = _contract()

    assert contract["acceptance"] == {
        "expected_disposition": "refuse",
        "expected_reason_code": "scope_off_topic_or_forbidden",
        "retrieval_calls_max": 0,
        "inference_worker_calls_max": 0,
        "network_calls": 0,
        "ordinary_search_import": False,
    }
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "locales_are_independent": True,
        "code_switching_is_not_a_retrieval_fallback": True,
        "fixture_execution_loads_no_model": True,
    }
