from __future__ import annotations

import json
import re
from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "docs/architecture/amo-privacy-security-contract-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-amo-privacy-security-contract-v1 -->"


def _fixture() -> dict[str, object]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "AMO privacy/security fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_amo_contract_is_active_planning_only_and_backlog_linked() -> None:
    assert (
        doc_path_from_index("architecture/amo-privacy-security-contract-0.9.6.md", status="active")
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-08`" in source
    assert "adds no amo client, api route, browser request" in source
    assert "does not alter bpm's current csp" in source

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M2-08 — AMO privacy and security contract" in backlog
    assert "amo-privacy-security-contract-0.9.6.md" in backlog


def test_only_fixed_public_search_request_and_six_locale_map_are_permitted() -> None:
    contract = _fixture()
    assert contract["contract_id"] == "bpm096-amo-privacy-security"
    assert contract["contract_version"] == 1
    assert contract["status"] == "planning-only-no-runtime-change"
    assert contract["future_owner"] == "BPM096-M7-extensions-and-amo"
    assert contract["upstream"] == {
        "origin": "https://addons.mozilla.org",
        "path": "/api/v5/addons/search/",
        "method": "GET",
        "query": {
            "fixed": {
                "app": "firefox",
                "type": "extension",
                "page": "1",
                "page_size": "10",
                "sort": "relevance",
            },
            "user_value": "q",
            "locale_value": "lang",
            "allowed_locale_map": {
                "en": "en-US",
                "ru": "ru",
                "de": "de",
                "es-ES": "es-ES",
                "fr": "fr",
                "zh-CN": "zh-CN",
            },
            "q_minimum_characters": 1,
            "q_maximum_characters": 100,
            "q_control_characters": "forbidden",
            "empty_query_request": "forbidden",
        },
    }


def test_transport_prevents_ssrf_redirect_proxy_and_credential_paths() -> None:
    transport = _fixture()["transport"]
    assert transport == {
        "tls_verify": True,
        "follow_redirects": False,
        "trust_env": False,
        "timeout_seconds": 5,
        "retry_attempts": 0,
        "max_response_bytes": 131072,
        "accepted_status": 200,
        "accepted_content_type": "application/json",
        "accepted_content_encoding": ["absent", "identity"],
        "forward_browser_or_profile_headers": False,
        "fixed_request_headers": {
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
        "forbidden_request_headers": [
            "Authorization",
            "Cookie",
            "Referer",
            "Origin",
            "X-Forwarded-For",
            "X-Real-IP",
        ],
    }


def test_response_is_bounded_text_projection_without_remote_or_active_content() -> None:
    response = _fixture()["response"]
    assert response["root_required"] == ["results"]
    assert response["results_maximum"] == 10
    assert response["local_projection"] == ["guid", "name", "version"]
    assert response["consumed_paths"] == [
        "results[].guid",
        "results[].name",
        "results[].current_version.version",
    ]
    assert response["localized_name"] == (
        "requested-locale-nonempty-text-or-requested-null-plus-_default-fallback-text"
    )
    assert response["maximum_guid_utf8_bytes"] == 255
    assert response["maximum_name_utf8_bytes"] == 512
    assert response["maximum_version_utf8_bytes"] == 255
    assert "current_version.file" in response["discarded_upstream_fields"]
    assert response["consumed_schema_drift"] == "discard-complete-result-to-manual-entry"
    assert response["pagination_or_result_urls_followed"] is False

    browser_security = _fixture()["browser_security"]
    assert browser_security == {
        "amo_direct_browser_request": False,
        "csp_connect_src": "'self'",
        "amo_host_allowed_by_any_csp_directive": False,
        "remote_asset_or_xpi_request": False,
        "provider_rendering": "text-only-no-html-markdown-url-or-active-content",
    }


def test_privacy_rate_cache_logging_and_manual_save_boundaries_fail_closed() -> None:
    contract = _fixture()
    assert contract["rate_limit"] == {
        "window_seconds": 60,
        "per_session_requests": 5,
        "global_requests": 20,
        "max_tracked_sessions": 32,
    }
    assert contract["cache"] == {
        "scope": "per-browser-session-memory-only",
        "key": "session-secret-sha256(normalized-query,amo-locale)",
        "ttl_seconds": 300,
        "max_entries_per_session": 10,
        "cross_session_sharing": False,
        "persistence": "forbidden",
        "stale_response": "forbidden",
    }
    data = contract["data_and_logging"]
    assert data["profile_data_disclosure"] == "forbidden"
    assert data["query_or_response_persistence"] == "forbidden"
    assert data["allowed_log_fields"] == [
        "outcome-code",
        "cache-hit",
        "coarse-elapsed-time-bucket",
    ]
    assert set(data["forbidden_log_fields"]) == {
        "query",
        "locale",
        "result-count",
        "result-values",
        "urls",
        "headers",
        "client-address",
        "cookies",
        "credentials",
        "profile-data",
    }

    manual = contract["manual_and_save_boundary"]
    assert manual == {
        "manual_entry_always_available": True,
        "manual_fields": ["extension-guid", "validated-install-url"],
        "selected_result_can_copy": ["guid"],
        "amo_result_install_url": "forbidden",
        "bpm_xpi_fetch": "forbidden",
        "save_or_validation_calls_amo": False,
        "result_provenance_persisted": False,
        "amo_availability_blocks_profile_operation": False,
    }

    failure = contract["failure"]
    assert failure["state"] == "manual-entry"
    assert failure["automatic_retry"] is False
    assert set(failure["reasons"]) == {
        "not-requested",
        "query-invalid",
        "locale-unsupported",
        "rate-limited",
        "cancelled",
        "timeout",
        "network",
        "tls",
        "redirect",
        "http-status",
        "content-type",
        "content-encoding",
        "response-too-large",
        "response-malformed",
        "response-schema-drift",
        "unexpected",
    }
    assert failure["all_failures"] == (
        "closed-to-localized-manual-entry-with-optional-explicit-retry"
    )
