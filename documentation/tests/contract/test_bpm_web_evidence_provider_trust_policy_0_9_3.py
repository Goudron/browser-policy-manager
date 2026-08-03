from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-web-evidence-provider-trust-policy-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m9_01_selects_one_fixed_brave_context_endpoint_and_pins_prior_security() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M9-01"
    assert contract["status"] == "brave-llm-context-selected-contract-only-no-network"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    decision = contract["provider_decision"]
    assert decision["product"] == "Brave Search API"
    assert decision["service"] == "LLM Context"
    assert decision["endpoint"] == "https://api.search.brave.com/res/v1/llm/context"
    assert decision["method"] == "POST"
    assert decision["hosted_answers_allowed"] is False
    assert decision["direct_result_url_fetching_allowed"] is False


def test_m9_01_freezes_six_locale_privacy_request_and_source_boundaries() -> None:
    contract = _contract()

    assert contract["locale_mapping"] == {
        "en": "en",
        "ru": "ru",
        "de": "de",
        "zh-CN": "zh-hans",
        "fr": "fr",
        "es-ES": "es",
    }
    request = contract["request_policy"]
    assert request["query_characters_max"] == 400
    assert request["query_words_max"] == 50
    assert request["provider_calls_per_consented_query_max"] == 1
    assert request["automatic_retries"] == request["redirects"] == 0
    assert request["enable_local"] is False
    assert request["location_headers"] is False
    assert request["provider_answer_generation"] is False
    sources = contract["source_policy"]
    assert sources["inline_goggle"].startswith("$discard\n")
    assert sources["provider_filter_is_sufficient_alone"] is False
    assert sources["local_post_filter_required"] is True
    assert {item["host"] for item in sources["allowed_sources"]} == {
        "mozilla.github.io",
        "support.mozilla.org",
        "firefox-source-docs.mozilla.org",
        "www.mozilla.org",
    }
    assert all(item["scheme"] == "https" for item in sources["allowed_sources"])
    assert contract["response_and_network_policy"]["result_url_connections"] == 0


def test_m9_01_records_terms_privacy_alternatives_and_no_runtime_change() -> None:
    contract = _contract()

    facts = contract["provider_facts_reviewed"]
    assert facts["standard_query_log_retention_days_max"] == 90
    assert facts["payment_information_required"] is True
    assert facts["observed_search_price_usd_per_1000_requests"] == 5.0
    alternatives = {item["candidate"]: item["status"] for item in contract["alternatives"]}
    assert alternatives == {
        "Google Custom Search JSON API": "rejected",
        "Microsoft Bing Search APIs": "rejected",
        "self-hosted or public SearXNG": "rejected-as-default-provider",
        "Brave Search API Answers": "rejected",
    }
    assert all("train" not in item.casefold() or "do not train" in item.casefold() for item in contract["terms_and_rights_policy"]["required_restrictions"])
    assert contract["acceptance"] == {
        "provider_selected": True,
        "contract_only": True,
        "network_calls_added": 0,
        "credentials_created_or_changed": False,
        "http_route_added": False,
        "browser_ui_added": False,
        "local_mode_default": True,
        "ordinary_search_changed": False,
        "m9_02_required_before_any_call": True,
        "m9_03_required_before_any_provider_content_reaches_inference": True,
        "m9_05_required_before_release": True,
    }
