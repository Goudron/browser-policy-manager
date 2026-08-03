from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import web_evidence

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-web-evidence-security-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m9_05_pins_prior_web_boundaries_and_closes_the_two_historical_m9_findings() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M9-05"
    assert contract["status"] == "implemented-adversarial-security-suite-no-route-or-live-network"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    closure = contract["m8_release_blocker_closure"]
    assert closure["closed_findings"] == ["AI093-T02", "AI093-T13"]
    assert "immutable pre-M9 snapshot" in closure["historical_record"]


def test_m9_05_freezes_cancellation_rate_privacy_and_no_route_boundaries() -> None:
    contract = _contract()

    assert contract["admission"]["required_order"] == [
        "request_web",
        "cancellation check",
        "deterministic BPM scope allow",
        "available disabled-by-default BYOK configuration",
        "cancellation check",
        "M9-02 exact one-use authorization validation",
        "process-lifetime rate-limit reservation",
        "cancellation check",
        "M9-02 exact one-use consent consumption",
        "one fixed provider POST",
    ]
    rate_limit = contract["rate_limit"]
    assert rate_limit["window_seconds"] == web_evidence.WEB_EVIDENCE_RATE_LIMIT_WINDOW_SECONDS
    assert rate_limit["requests_per_session_max"] == web_evidence.WEB_EVIDENCE_MAX_REQUESTS_PER_SESSION
    assert rate_limit["requests_global_max"] == web_evidence.WEB_EVIDENCE_MAX_REQUESTS_GLOBAL
    assert rate_limit["tracked_sessions_max"] == web_evidence.WEB_EVIDENCE_MAX_TRACKED_SESSIONS
    assert contract["privacy_and_failure_isolation"]["offline_test_policy"].startswith("all security tests")
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "worker_invocation": False,
        "live_network": False,
        "ordinary_documentation_search_changed": False,
        "cross_locale_chat": False,
        "direct_result_fetch": False,
    }
