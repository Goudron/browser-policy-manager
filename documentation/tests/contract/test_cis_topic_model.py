from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
MODEL_PATH = DOCUMENTATION_ROOT / "config/cis-settings-topic-model-0.9.0.json"
INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
PROVENANCE_MATRIX_PATH = (
    REPOSITORY_ROOT / "docs/architecture/product-documentation-provenance-matrix-0.9.0.json"
)
TEMPLATE_PATH = DOCUMENTATION_ROOT / "src/shared/templates/cis-recommendation-reference-topic.dita"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

pytestmark = pytest.mark.docs_contract


def _model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _provenance_matrix() -> dict[str, object]:
    return json.loads(PROVENANCE_MATRIX_PATH.read_text(encoding="utf-8"))


def _recommendation(recommendation_id: str) -> dict[str, object]:
    recommendations = _inventory()["recommendations"]
    return next(
        recommendation
        for recommendation in recommendations
        if recommendation["recommendation_id"] == recommendation_id
    )


def _slug(recommendation_id: str) -> str:
    return re.sub(r"[^0-9]+", "-", recommendation_id).strip("-")


def test_cis_topic_model_declares_stable_topic_identity_sections_and_metadata() -> None:
    model = _model()

    assert model["schema_version"] == 1
    assert model["target_bpm_version"] == "0.9.0"
    assert model["guide_id"] == "cis-settings-guide"
    assert model["backlog_item"] == "BPM090-M6-01"
    assert model["status"] == "defined"
    assert model["source_inventory"] == "docs/architecture/cis-documentation-inventory-0.9.0.json"
    assert (
        model["source_matrix"]
        == "docs/architecture/product-documentation-provenance-matrix-0.9.0.json"
    )
    assert (
        model["template_source"]
        == "documentation/src/shared/templates/cis-recommendation-reference-topic.dita"
    )

    topic = model["topic"]
    assert topic["dita_type"] == "reference"
    assert topic["topic_id_pattern"] == "cis-rec-{recommendation_id_slug}"
    assert topic["key_pattern"] == "topic.cis-rec-{recommendation_id_slug}"
    assert topic["filename_pattern"] == "cis-rec-{recommendation_id_slug}.dita"
    assert topic["otherprops_cis"] == "cis({recommendation_id})"
    assert topic["conditional_props"] == {"level_1": "cis-level-1", "level_2": "cis-level-2"}

    assert [section["id"] for section in model["required_sections"]] == [
        "a-disclaimer",
        "a-benchmark",
        "a-recommendation-identity",
        "a-bpm-authored-summary",
        "a-bpm-mapping",
        "a-automation-state",
        "a-conflicts",
        "a-verification",
        "a-provenance",
    ]
    for section in model["required_sections"]:
        assert section["title"]
        assert section["required_fields"]


def test_disclaimer_and_source_boundary_match_registered_cis_source_families() -> None:
    model = _model()
    matrix = _provenance_matrix()
    families = {family["id"]: family for family in matrix["source_families"]}

    disclaimer = model["disclaimer_contract"]
    assert disclaimer["required_outputclass"] == "cis-disclaimer"
    assert disclaimer["must_appear_in_sections"] == ["a-disclaimer", "a-provenance"]
    required = " ".join(disclaimer["required_statements"])
    assert "independent implementation" in required
    assert "not authorized, sponsored, endorsed, certified, or approved by CIS" in required
    assert "not a substitute for the official CIS benchmark" in required
    assert "does not prove CIS compliance" in required
    assert "not copied, translated, indexed, or packaged" in required
    assert "no separate persisted CIS exception or waiver model" in required
    assert {"CIS certified", "guarantees CIS compliance", "official CIS guidance"} <= set(
        disclaimer["forbidden_claims"]
    )

    source_boundary = model["source_boundary"]
    publishable_ids = set(source_boundary["publishable_source_family_ids"])
    restricted_ids = set(source_boundary["restricted_source_family_ids"])
    assert publishable_ids == {
        "bpm-cis-mapping-implementation",
        "cis-trademarks-and-certification-marks",
    }
    assert restricted_ids == {"cis-benchmark-pdf"}
    assert source_boundary["source_expression_blocked_by_default"] is True
    assert source_boundary["rights_approval_id_required_for_benchmark_expression"] is True
    assert "recommendation_id" in source_boundary["allowed_without_rights_approval"]
    assert "benchmark rationale prose" in source_boundary["blocked_without_rights_approval"]

    benchmark_family = families["cis-benchmark-pdf"]
    assert (
        benchmark_family["publication_policy"]
        == source_boundary["benchmark_source_publication_policy"]
    )
    assert benchmark_family["may_publish_without_rights_approval"] is False
    assert "restricted-external-benchmark-content" == benchmark_family["classification"]

    mapping_family = families["bpm-cis-mapping-implementation"]
    assert mapping_family["may_publish_without_rights_approval"] is True
    assert "BPM-authored mapping facts" in source_boundary["allowed_without_rights_approval"]
    assert "cis-settings-guide" in mapping_family["guide_families"]


def test_recommendation_contract_matches_cis_inventory_counts_and_edge_cases() -> None:
    model = _model()
    inventory = _inventory()
    recommendation_model = model["recommendation_model"]
    automation_model = model["automation_model"]
    fixtures = model["fixture_recommendation_ids"]

    assert (
        recommendation_model["recommendation_count"] == inventory["summary"]["recommendation_count"]
    )
    assert (
        recommendation_model["planned_topic_count"]
        == inventory["summary"]["publication_disposition_counts"]["planned-dita-topic"]
    )
    assert (
        recommendation_model["provenance_only_count"]
        == inventory["summary"]["publication_disposition_counts"]["provenance-only-non-publishable"]
    )
    assert recommendation_model["allowed_publication_dispositions"] == [
        "planned-dita-topic",
        "provenance-only-non-publishable",
    ]
    assert recommendation_model["planned_topics_require_targets"] is True
    assert recommendation_model["provenance_only_must_not_publish_topic"] is True

    assert automation_model["supported_schema_channels"] == [
        "esr-115.39",
        "esr-140.13",
        "esr-153.0",
        "release-153",
    ]
    assert sorted({layer["schema_channel"] for layer in inventory["generated_layers"]}) == [
        "esr-115.39",
        "esr-140.13",
        "esr-153.0",
        "release-153",
    ]
    assert sorted({layer["level"] for layer in inventory["generated_layers"]}) == [1, 2]
    assert automation_model["manual_review_path_count"] == len(inventory["manual_review_paths"])
    assert automation_model["exception_contract"]["persisted_exception_model"] is False
    assert inventory["exception_contract"]["persisted_exception_model"] is False

    policy = _recommendation(fixtures["automated_policy"])
    assert policy["doc_id"] == model["topic"]["topic_id_pattern"].format(
        recommendation_id_slug=_slug(policy["recommendation_id"])
    )
    assert policy["publication_disposition"] == "planned-dita-topic"
    assert policy["mapping_status"] == "mapped"
    assert policy["targets"][0]["kind"] == "policy"
    assert policy["targets"][0]["ui_target"].startswith("policy:")

    manual_review_policy = _recommendation(fixtures["manual_review_path_policy"])
    manual_review_paths = {path["path_id"] for path in inventory["manual_review_paths"]}
    assert ".".join(manual_review_policy["targets"][0]["path"]) in manual_review_paths

    preference = _recommendation(fixtures["automated_preference"])
    assert preference["mapping_status"] == "preference_mapped"
    assert preference["targets"][0]["kind"] == "preference"
    assert preference["targets"][0]["ui_target"].startswith("known-preference:")

    for fixture_name in (
        "provenance_only_needs_research",
        "provenance_only_deprecated_or_removed",
    ):
        recommendation = _recommendation(fixtures[fixture_name])
        assert recommendation["publication_disposition"] == "provenance-only-non-publishable"
        assert recommendation["doc_id"] is None
        assert recommendation["targets"] == []
        assert recommendation["non_publishable_reason"]


def test_cis_template_matches_model_sections_and_disclaimer_boundary() -> None:
    model = _model()
    root = ET.fromstring(TEMPLATE_PATH.read_text(encoding="utf-8"))

    assert root.tag == "reference"
    assert root.attrib == {
        "id": "cis-recommendation-reference-topic-template",
        XML_LANG: "en",
        "audience": "user security-reviewer",
        "product": "bpm-0-9-0",
        "platform": "web",
        "props": "cis-level-1",
        "otherprops": "cis(1.1.1.1)",
    }
    assert root.find("title") is not None
    assert root.find("shortdesc") is not None

    sections = root.findall("./refbody/section")
    assert [section.attrib["id"] for section in sections] == [
        section["id"] for section in model["required_sections"]
    ]
    for section in sections:
        assert section.findtext("title")
        assert "".join(section.itertext()).strip()

    disclaimer_sections = {
        section.attrib["id"]: section
        for section in sections
        if section.attrib.get("outputclass") == "cis-disclaimer"
    }
    assert set(disclaimer_sections) == {"a-disclaimer", "a-provenance"}

    template_text = " ".join(root.itertext())
    for statement in model["disclaimer_contract"]["required_statements"][:4]:
        assert statement in template_text
    for forbidden_claim in model["disclaimer_contract"]["forbidden_claims"]:
        assert forbidden_claim not in template_text
