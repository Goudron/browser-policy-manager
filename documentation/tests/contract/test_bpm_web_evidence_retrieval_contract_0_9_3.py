from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import web_evidence

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-web-evidence-retrieval-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m9_03_pins_consent_security_and_one_fixed_no_proxy_no_redirect_post() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M9-03"
    assert contract["status"] == "implemented-fixed-provider-adapter-no-route-ui-or-live-smoke"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["admission"]["required_order"] == [
        "request_web",
        "deterministic BPM scope allow",
        "M9-02 exact one-use consent",
        "one fixed provider POST",
    ]
    network = contract["network"]
    assert network["endpoint"] == web_evidence.BRAVE_LLM_CONTEXT_ENDPOINT
    assert network["destinations"] == ["api.search.brave.com:443"]
    assert network["proxy_environment_inheritance"] is False
    assert network["follow_redirects"] is False
    assert network["automatic_retries"] == network["result_url_connections"] == 0
    assert network["location_headers"] is False
    assert network["live_smoke_test"] is False


def test_m9_03_freezes_request_response_filter_sanitization_and_local_only_fallback() -> None:
    contract = _contract()

    request = contract["request"]
    assert request["body_fields"] == {
        "q": "exact consented question",
        "search_lang": {
            "en": "en",
            "ru": "ru",
            "de": "de",
            "zh-CN": "zh-hans",
            "fr": "fr",
            "es-ES": "es",
        },
        "count": 10,
        "spellcheck": False,
        "maximum_number_of_urls": web_evidence.MAX_EXTERNAL_URLS,
        "maximum_number_of_tokens": 2048,
        "maximum_number_of_snippets": web_evidence.MAX_EXTERNAL_SNIPPETS,
        "maximum_number_of_tokens_per_url": 1024,
        "maximum_number_of_snippets_per_url": web_evidence.MAX_EXTERNAL_SNIPPETS_PER_URL,
        "context_threshold_mode": "strict",
        "enable_local": False,
        "goggles": web_evidence.INLINE_MOZILLA_GOGGLE,
    }
    response = contract["response"]
    assert response["bytes_max"] == web_evidence.MAX_PROVIDER_RESPONSE_BYTES
    assert response["content_encodings"] == ["identity", "gzip"]
    assert response["accepted_grounding"].startswith("grounding.generic only")
    source_policy = contract["source_post_filter"]
    assert source_policy["source_filter_alone_is_sufficient"] is False
    assert source_policy["result_url_fetching"] is False
    assert source_policy["allowed_hosts_and_paths"] == {
        host: list(prefixes) for host, prefixes in web_evidence._SOURCE_PATH_PREFIXES.items()
    }
    assert contract["sanitization_and_retention"]["persistence"] is False
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "browser_storage": False,
        "database": False,
        "disk": False,
        "telemetry": False,
        "ordinary_search_changed": False,
        "external_evidence_to_inference": False,
        "hosted_answers": False,
        "direct_result_fetch": False,
    }
