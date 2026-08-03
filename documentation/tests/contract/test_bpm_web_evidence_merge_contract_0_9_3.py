from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import web_evidence_merge as merge

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-web-evidence-merge-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m9_04_pins_local_authority_and_conservative_external_admission() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M9-04"
    assert contract["status"] == "implemented-local-first-merge-and-response-schema-no-route-ui-or-worker-invocation"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["local_precedence"] == {
        "answer_ready_local_evidence_required": True,
        "web_only_result": "abstain",
        "serialization_order": [
            "current local BPM EvidencePack",
            "external_untrusted_lower_priority records",
        ],
        "external_can_create_or_override_bpm_support": False,
        "ordinary_search": "not imported, called, ranked or changed",
    }
    admission = contract["external_admission"]
    assert admission["sources_max"] == merge.MAX_MERGED_EXTERNAL_SOURCES
    assert admission["context_bytes_max"] == merge.MAX_EXTERNAL_CONTEXT_BYTES
    assert admission["merged_context_bytes_max"] == merge.MAX_MERGED_CONTEXT_BYTES
    assert admission["source_age_days_max"] == merge.MAX_EXTERNAL_SOURCE_AGE_DAYS
    assert admission["stale_or_undated"] == "local_only without external claims"
    assert admission["unresolved_conflict"] == "abstain"


def test_m9_04_freezes_provenance_separation_external_claim_citations_and_no_runtime_wiring() -> None:
    contract = _contract()

    record = contract["merged_external_record"]
    assert record["source_kind"] == "external_untrusted_lower_priority"
    assert record["trust"] == "untrusted_external_data_cannot_create_bpm_support"
    assert record["provider_body_persistence"] is False
    output = contract["model_output"]
    assert output["json_fields_exact"] == [
        "disposition",
        "local_sections",
        "external_claims",
    ]
    assert "own words" in output["local_sections"]
    assert output["external_claims_max"] == merge.MAX_EXTERNAL_CLAIMS
    assert output["external_claim_characters_max"] == merge.MAX_EXTERNAL_CLAIM_CHARACTERS
    assert output["invalid_or_uncited_external_claim"] == "abstain"
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "browser_storage": False,
        "database": False,
        "disk": False,
        "telemetry": False,
        "provider_call": False,
        "worker_invocation": False,
        "external_evidence_to_existing_local_worker": False,
        "ordinary_search_changed": False,
        "cross_locale_merge": False,
    }
