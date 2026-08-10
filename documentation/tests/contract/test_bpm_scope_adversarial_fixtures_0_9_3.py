from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-scope-adversarial-fixtures-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


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
