from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
REVIEW = REPOSITORY_ROOT / "docs/architecture/firefox-cis-guide-sufficiency-review-0.9.1.json"
PROTOCOL = DOCUMENTATION_ROOT / "config/documentation-sufficiency-review-protocol-0.9.1.json"
FIREFOX_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
)
CIS_INVENTORY = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
FIREFOX_INDEX = DOCUMENTATION_ROOT / "src/generated/firefox/firefox-policy-skeletons-0.9.0.json"
CIS_INDEX = DOCUMENTATION_ROOT / "src/generated/cis/cis-recommendation-skeletons-0.9.0.json"
CIS_PROVENANCE = DOCUMENTATION_ROOT / "src/generated/cis/cis-provenance-review-0.9.0.json"
TEST_NODE_RE = re.compile(r"(?P<path>[A-Za-z0-9_./-]+\.py)::(?P<test>test_[A-Za-z0-9_]+)")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _items() -> dict[str, dict]:
    return {item["review_id"]: item for item in _json(REVIEW)["review_items"]}


def test_review_declares_m6_02_scope_counts_and_accepted_result() -> None:
    review = _json(REVIEW)

    assert review["schema_version"] == 1
    assert review["review_id"] == "bpm-0.9.1-firefox-cis-guide-sufficiency-review"
    assert review["target_bpm_version"] == "0.9.1"
    assert review["backlog_item"] == "BPM091-M6-02"
    assert review["guide_ids"] == ["firefox-policy-guide", "cis-settings-guide"]
    assert review["status"] == "accepted"
    assert review["scope"]["locale_scope"] == "source-locale-plus-parity"
    assert review["scope"]["parity_locales"] == ["ru", "de", "zh-CN", "fr", "es-ES"]
    assert review["summary"]["review_item_count"] == 8
    assert review["summary"]["pass_count"] == 8
    assert review["summary"]["blocked_count"] == 0
    assert review["summary"]["release_blockers"] == []


def test_each_review_item_resolves_every_protocol_field_and_evidence_path() -> None:
    review = _json(REVIEW)
    protocol = _json(PROTOCOL)
    required = set(protocol["review_item_template"]["required_fields"])
    allowed_guides = {"firefox-policy-guide", "cis-settings-guide"}
    allowed_evidence = set(protocol["evidence_types"])

    assert len(review["review_items"]) == 8
    for item in review["review_items"]:
        assert required <= set(item), item["review_id"]
        assert item["guide_id"] in allowed_guides
        assert item["locale_scope"] == review["scope"]["locale_scope"]
        assert item["review_disposition"] == "pass"
        assert set(item["evidence_type"]) <= allowed_evidence
        assert "static_source_simulation" in item["evidence_type"]
        for field in required - {
            "review_id",
            "guide_id",
            "topic_id",
            "locale_scope",
            "review_disposition",
        }:
            assert item[field], (item["review_id"], field)
        for artifact in item["evidence_artifact"]:
            assert (REPOSITORY_ROOT / artifact).is_file(), artifact
        for command in item["focused_verification"]:
            for node in TEST_NODE_RE.finditer(command):
                path = REPOSITORY_ROOT / node["path"]
                assert path.is_file(), node.group(0)
                assert f"def {node['test']}(" in path.read_text(encoding="utf-8")


def test_firefox_baseline_and_representative_policy_facts_match_generated_sources() -> None:
    review = _json(REVIEW)
    baseline = review["inventory_baseline"]["firefox"]
    inventory = _json(FIREFOX_INVENTORY)
    index = _json(FIREFOX_INDEX)
    by_id = {policy["policy_id"]: policy for policy in inventory["policies"]}

    assert baseline == {
        "channels": ["esr-140.13", "esr-153.0", "release-153"],
        "policy_count": inventory["summary"]["policy_union_count"],
        "all_channels_count": inventory["summary"]["policy_scope_counts"]["both"],
        "partial_channels_count": inventory["summary"]["policy_scope_counts"]["partial"],
        "managed_preference_count": inventory["summary"]["managed_preference_count"],
        "schema_valid_example_count": index["example_count"],
    }
    assert by_id["DisableTelemetry"]["channel_scope"] == "both"
    assert {entry["value_type"] for entry in by_id["DisableTelemetry"]["channels"].values()} == {
        "boolean"
    }
    assert by_id["Homepage"]["channel_scope"] == "both"
    assert {entry["value_type"] for entry in by_id["Homepage"]["channels"].values()} == {"object"}
    assert by_id["Preferences"]["channels"]["release-153"]["ui"]["preserve_unknown_fields"] is True
    for policy_id in ("AIControls", "VisualSearchEnabled"):
        assert by_id[policy_id]["channel_scope"] == "partial"
        assert set(by_id[policy_id]["channels"]) == {"esr-153.0", "release-153"}


def test_managed_preference_sample_and_cis_l2_mapping_agree() -> None:
    firefox_inventory = _json(FIREFOX_INVENTORY)
    cis_inventory = _json(CIS_INVENTORY)
    preference = next(
        item
        for item in firefox_inventory["managed_preferences"]
        if item["preference_id"] == "network.IDN_show_punycode"
    )
    recommendation = next(
        item for item in cis_inventory["recommendations"] if item["recommendation_id"] == "1.1.18.9"
    )
    target = recommendation["targets"][0]

    assert preference["status"] == "locked"
    assert preference["type"] == "boolean"
    assert target["kind"] == "preference"
    assert target["target_id"] == preference["preference_id"]
    assert target["value"] == {"Status": "locked", "Type": "boolean", "Value": True}
    assert recommendation["level"] == 2
    assert recommendation["generated_layers"] == [
        "cis-l2.esr-140.13",
        "cis-l2.esr-153.0",
        "cis-l2.release-153",
    ]


def test_cis_counts_manual_review_and_provenance_only_states_match_sources() -> None:
    review_baseline = _json(REVIEW)["inventory_baseline"]["cis"]
    inventory = _json(CIS_INVENTORY)
    provenance = _json(CIS_PROVENANCE)
    index = _json(CIS_INDEX)
    summary = inventory["summary"]

    assert review_baseline == {
        "recommendation_count": summary["recommendation_count"],
        "published_topic_count": index["topic_count"],
        "provenance_only_count": index["provenance_only_count"],
        "level_1_count": summary["level_counts"]["L1"],
        "level_2_count": summary["level_counts"]["L2"],
        "policy_mapping_count": summary["target_kind_counts"]["policy"],
        "preference_mapping_count": summary["target_kind_counts"]["preference"],
        "manual_review_path_count": provenance["summary"]["manual_review_path_count"],
        "mapping_example_count": index["mapping_example_count"],
    }
    assert {record["path_id"] for record in provenance["manual_review_paths"]} >= {
        "SanitizeOnShutdown.Sessions",
        "Proxy.Mode",
        "AppAutoUpdate",
    }
    provenance_only = {
        item["recommendation_id"]: item["mapping_status"]
        for item in inventory["recommendations"]
        if item["publication_disposition"] == "provenance-only-non-publishable"
    }
    assert provenance_only == {
        "1.1.5.3": "needs_research",
        "1.1.12.1": "deprecated_or_removed",
    }


def test_cis_mapping_links_and_examples_resolve_to_current_firefox_references() -> None:
    cis_index = _json(CIS_INDEX)
    firefox_policy_ids = {item["policy_id"] for item in _json(FIREFOX_INDEX)["policies"]}

    assert len(cis_index["topics"]) == 53
    for topic in cis_index["topics"]:
        source = (REPOSITORY_ROOT / topic["path"]).read_text(encoding="utf-8")
        root = ET.fromstring(source)
        rows = root.findall("./refbody/section[@id='a-bpm-mapping']/simpletable/strow")
        examples = root.findall("./refbody/section[@id='a-bpm-mapping']/sectiondiv/codeblock")
        assert len(rows) == len(topic["mapping_table_rows"]) == 1
        assert len(examples) == 1
        json.loads("".join(examples[0].itertext()))
        for row in topic["mapping_table_rows"]:
            assert all(check["value_matches"] for check in row["layer_checks"])
            if row["kind"] == "policy":
                assert row["target_id"] in firefox_policy_ids
                assert f'keyref="{row["firefox_topic_key"]}"' in source


def test_review_records_honest_runtime_certification_and_exception_boundaries() -> None:
    review = _json(REVIEW)
    provenance = _json(CIS_PROVENANCE)
    boundaries = " ".join(review["unverified_boundaries"])

    assert "live Firefox deployment" in boundaries
    assert "does not certify" in boundaries
    assert "does not persist" in boundaries
    assert provenance["source_boundary"]["certification_claimed"] is False
    assert provenance["source_boundary"]["compliance_guaranteed"] is False
    assert provenance["summary"]["persisted_exception_model"] is False


def test_representative_items_cover_required_decision_classes() -> None:
    items = _items()

    assert set(items) == {
        "FX-SUFF-SIMPLE",
        "FX-SUFF-COMPLEX",
        "FX-SUFF-PREFERENCES",
        "FX-SUFF-CHANNEL",
        "CIS-SUFF-L1-POLICY",
        "CIS-SUFF-L2-PREFERENCE",
        "CIS-SUFF-MANUAL",
        "CIS-SUFF-PROVENANCE",
    }
    assert {item["guide_id"] for item in items.values()} == {
        "firefox-policy-guide",
        "cis-settings-guide",
    }
