from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import web_evidence_consent as consent

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-web-evidence-opt-in-consent-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m9_02_pins_provider_privacy_retention_and_threat_boundaries() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M9-02"
    assert contract["status"] == "implemented-memory-only-no-http-route-ui-or-network"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["configuration"] == {
        "enabled_environment_variable": "BPM_WEB_EVIDENCE_ENABLED",
        "enabled_by_default": False,
        "credential_environment_variable": "BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN",
        "credential_model": "Administrator-provided BYOK token in server configuration only; BPM ships no shared credential.",
        "missing_credential": "normal local-only state",
        "credential_in_browser_or_logs": False,
        "network_calls_added": 0,
    }


def test_m9_02_freezes_exact_disclosure_one_time_consent_and_no_network_boundary() -> None:
    contract = _contract()

    disclosure = contract["disclosure"]
    assert disclosure["exact_outgoing_question"] is True
    assert disclosure["provider"] == consent.BRAVE_PROVIDER_NAME
    assert disclosure["recipient"] == consent.BRAVE_RECIPIENT
    assert disclosure["query_log_retention_warning"] == consent.BRAVE_QUERY_LOG_RETENTION_WARNING
    consent_policy = contract["consent"]
    assert consent_policy["storage"] == "process memory only"
    assert consent_policy["question_storage"].startswith("per-process HMAC digest only")
    assert consent_policy["ttl_seconds"] == consent.CONSENT_TTL_SECONDS
    assert consent_policy["pending_records_max"] == consent.MAX_PENDING_CONSENTS
    assert consent_policy["one_time_use"] is True
    assert consent_policy["query_limits"] == {
        "characters_max": consent.WEB_QUERY_CHARACTERS_MAX,
        "words_max": consent.WEB_QUERY_WORDS_MAX,
    }
    assert consent_policy["six_locale_search_language"] == {
        "en": "en",
        "ru": "ru",
        "de": "de",
        "zh-CN": "zh-hans",
        "fr": "fr",
        "es-ES": "es",
    }
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "browser_storage": False,
        "database": False,
        "disk": False,
        "telemetry": False,
        "provider_request": False,
        "ordinary_search_calls": 0,
        "cross_locale_consent": False,
        "silent_web_promotion": False,
    }
