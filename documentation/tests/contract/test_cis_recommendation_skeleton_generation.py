from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
MODEL_PATH = DOCUMENTATION_ROOT / "config/cis-settings-topic-model-0.9.0.json"
GENERATED_ROOT = DOCUMENTATION_ROOT / "src/generated/cis"
RECOMMENDATIONS_ROOT = GENERATED_ROOT / "recommendations"
INDEX_PATH = GENERATED_ROOT / "cis-recommendation-skeletons-0.9.0.json"
PROVENANCE_REVIEW_PATH = GENERATED_ROOT / "cis-provenance-review-0.9.0.json"
MAP_PATH = GENERATED_ROOT / "cis-recommendation-skeletons.ditamap"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/generate_cis_recommendation_skeletons.py"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SPEC = importlib.util.spec_from_file_location("generate_cis_recommendation_skeletons", MODULE_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)

pytestmark = pytest.mark.docs_contract


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _index() -> dict[str, object]:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _provenance_review() -> dict[str, object]:
    return json.loads(PROVENANCE_REVIEW_PATH.read_text(encoding="utf-8"))


def _layer_value(layer_document: dict[str, object], row: dict[str, object]) -> object:
    path = ["Preferences", *row["path"]] if row["kind"] == "preference" else row["path"]
    current: object = layer_document["policies"]
    for part in path:
        current = current[part]
    return current


def _planned_recommendations() -> list[dict[str, object]]:
    return [
        recommendation
        for recommendation in _inventory()["recommendations"]
        if recommendation["publication_disposition"] == "planned-dita-topic"
    ]


def _provenance_only_recommendations() -> list[dict[str, object]]:
    return [
        recommendation
        for recommendation in _inventory()["recommendations"]
        if recommendation["publication_disposition"] == "provenance-only-non-publishable"
    ]


def test_generated_cis_index_covers_planned_and_provenance_only_records() -> None:
    inventory = _inventory()
    index = _index()
    planned = _planned_recommendations()
    provenance_only = _provenance_only_recommendations()

    assert index["schema_version"] == 1
    assert index["backlog_item"] == "BPM090-M6-03"
    assert index["target_bpm_version"] == "0.9.0"
    assert index["generated_by"] == "documentation/tools/generate_cis_recommendation_skeletons.py"
    assert index["mapping_backlog_item"] == "BPM090-M6-04"
    assert index["refresh_runbook_backlog_item"] == "BPM090-M6-08"
    assert (
        index["refresh_runbook"]
        == "documentation/runbooks/inventory-refresh.md#cis-benchmark-and-mapping-drift-gate"
    )
    assert index["provenance_review_backlog_item"] == "BPM090-M6-09"
    assert index["provenance_review"] == (
        "documentation/src/generated/cis/cis-provenance-review-0.9.0.json"
    )
    assert index["recommendation_count"] == inventory["summary"]["recommendation_count"] == 55
    assert index["topic_count"] == len(planned) == 53
    assert index["provenance_only_count"] == len(provenance_only) == 2
    assert index["mapping_table_count"] == len(planned)
    assert index["mapping_row_count"] == sum(len(recommendation["targets"]) for recommendation in planned)
    assert index["mapping_example_count"] == sum(
        len(recommendation["targets"]) for recommendation in planned
    )
    assert index["source_boundary"] == {
        "certification_claimed": False,
        "publishable_source_family_id": "bpm-cis-mapping-implementation",
        "restricted_source_family_id": "cis-benchmark-pdf",
        "source_expression_copied": False,
        "source_expression_indexed": False,
    }

    generated_topics = index["topics"]
    assert {entry["recommendation_id"] for entry in generated_topics} == {
        recommendation["recommendation_id"] for recommendation in planned
    }
    assert len({entry["doc_id"] for entry in generated_topics}) == len(planned)
    assert len({entry["path"] for entry in generated_topics}) == len(planned)
    for entry in generated_topics:
        recommendation = next(
            item for item in planned if item["recommendation_id"] == entry["recommendation_id"]
        )
        assert entry["doc_id"] == recommendation["doc_id"]
        assert entry["target_count"] == len(recommendation["targets"])
        assert entry["target_doc_ids"] == [target["target_doc_id"] for target in recommendation["targets"]]
        assert len(entry["mapping_table_rows"]) == len(recommendation["targets"])
        assert len(entry["mapping_table_rows"]) == entry["target_count"]
        assert entry["source_title_sha256"] == recommendation["source_title_sha256"]
        assert (REPOSITORY_ROOT / entry["path"]).is_file()

    assert index["provenance_only_records"] == [
        {
            "doc_id": recommendation["doc_id"],
            "mapping_status": recommendation["mapping_status"],
            "non_publishable_reason": recommendation["non_publishable_reason"],
            "provenance_id": recommendation["provenance_id"],
            "publication_disposition": recommendation["publication_disposition"],
            "recommendation_id": recommendation["recommendation_id"],
            "source_title_sha256": recommendation["source_title_sha256"],
            "topic_path": None,
        }
        for recommendation in provenance_only
    ]


def test_generated_cis_map_is_stable_keyed_and_excludes_provenance_only_records() -> None:
    root = ET.parse(MAP_PATH).getroot()
    topicrefs = root.findall("topicref")
    planned = _planned_recommendations()
    provenance_only = _provenance_only_recommendations()

    assert root.tag == "map"
    assert root.attrib == {"id": "map-generated-cis-recommendation-skeletons"}
    assert root.findtext("title") == "Generated CIS recommendation skeletons"
    assert len(topicrefs) == len(planned)
    assert [topicref.attrib["href"] for topicref in topicrefs] == [
        f"recommendations/{recommendation['doc_id']}.dita"
        for recommendation in planned
    ]
    assert all(
        topicref.attrib["keys"] == f"topic.{Path(topicref.attrib['href']).stem}"
        for topicref in topicrefs
    )
    for recommendation in provenance_only:
        assert recommendation["doc_id"] is None
        assert not (RECOMMENDATIONS_ROOT / f"cis-rec-{recommendation['recommendation_id']}.dita").exists()


def test_each_generated_cis_topic_matches_model_sections_metadata_and_mapping_facts() -> None:
    model = _model()
    required_sections = [section["id"] for section in model["required_sections"]]
    conditional_props = model["topic"]["conditional_props"]

    for recommendation in _planned_recommendations():
        path = RECOMMENDATIONS_ROOT / f"{recommendation['doc_id']}.dita"
        topic_text = path.read_text(encoding="utf-8")
        root = ET.fromstring(topic_text)
        expected_props = (
            conditional_props["level_1"]
            if recommendation["level"] == 1
            else conditional_props["level_2"]
        )

        assert root.tag == "reference"
        assert root.attrib == {
            "id": recommendation["doc_id"],
            "audience": "user security-reviewer",
            "product": "bpm-0-9-0",
            "platform": "web",
            "props": expected_props,
            "otherprops": f"cis({recommendation['recommendation_id']})",
        }
        assert XML_LANG not in root.attrib
        assert root.findtext("title") == f"CIS recommendation {recommendation['recommendation_id']}"
        sections = root.findall("./refbody/section")
        assert [section.attrib["id"] for section in sections] == required_sections
        assert all(section.findtext("title") for section in sections)
        assert "BPM-HAND-REGION-START bpm-authored-summary" in topic_text
        assert "BPM-HAND-REGION-START conflicts" in topic_text
        assert "BPM-HAND-REGION-START verification" in topic_text
        mapping_section = root.find("./refbody/section[@id='a-bpm-mapping']")
        assert mapping_section is not None
        mapping_table = mapping_section.find("simpletable[@outputclass='cis-mapping-table']")
        assert mapping_table is not None
        rows = mapping_table.findall("strow")
        assert len(rows) == len(recommendation["targets"])
        assert len(mapping_section.findall("sectiondiv[@outputclass='cis-mapping-example']")) == len(
            recommendation["targets"]
        )
        for target in recommendation["targets"]:
            assert target["target_id"] in topic_text
            assert target["target_doc_id"] in topic_text
            assert target["merge_rule"] in topic_text
            assert json.dumps(target["value"], ensure_ascii=False, sort_keys=True) in topic_text.replace(
                "&quot;",
                '"',
            )
        assert recommendation["source_title_sha256"] in topic_text
        assert recommendation["provenance_id"] in topic_text


def test_generated_mapping_tables_and_examples_match_current_cis_layers() -> None:
    inventory_by_id = {
        recommendation["recommendation_id"]: recommendation
        for recommendation in _planned_recommendations()
    }

    for topic in _index()["topics"]:
        recommendation = inventory_by_id[topic["recommendation_id"]]
        rows = topic["mapping_table_rows"]
        assert rows
        assert len(rows) == len(recommendation["targets"])

        for row, target in zip(rows, recommendation["targets"], strict=True):
            assert row["kind"] == target["kind"]
            assert row["target_id"] == target["target_id"]
            assert row["target_doc_id"] == target["target_doc_id"]
            assert row["firefox_topic_key"] == f"topic.{target['target_doc_id']}"
            assert row["ui_target"] == target["ui_target"]
            assert row["path"] == target["path"]
            assert row["path_id"] == ".".join(target["path"])
            assert row["value"] == target["value"]
            assert row["schema_channels"] == target["schema_channels"]
            assert row["merge_rule"] == target["merge_rule"]
            assert row["layer_checks"]
            assert {check["layer_id"] for check in row["layer_checks"]} == set(
                recommendation["generated_layers"]
            )

            if target["kind"] == "preference":
                assert row["lock_state"] == target["value"]["Status"] == "locked"
                assert row["example_document"] == {
                    "policies": {"Preferences": {target["target_id"]: target["value"]}}
                }
            else:
                assert row["value_type"] in {"boolean", "integer", "string", "array", "object"}
                assert target["path"][0] in row["example_document"]["policies"]

            for check in row["layer_checks"]:
                layer_document = json.loads(
                    (REPOSITORY_ROOT / check["file"]).read_text(encoding="utf-8")
                )
                assert check["value_matches"] is True
                assert check["layer_value"] == _layer_value(layer_document, row) == target["value"]


def test_generated_cis_topics_preserve_source_boundary_and_non_certification_contract() -> None:
    forbidden_claims = set(_model()["disclaimer_contract"]["forbidden_claims"])

    for topic_path in sorted(RECOMMENDATIONS_ROOT.glob("*.dita")):
        text = topic_path.read_text(encoding="utf-8")
        assert "bpm-cis-mapping-implementation" in text
        assert "cis-benchmark-pdf" in text
        assert "source expression are not copied, translated, indexed, or packaged" in text
        assert "not authorized, sponsored, endorsed, certified, or approved by CIS" in text
        assert "not a substitute for the official CIS benchmark" in text
        assert "does not prove CIS compliance" in text
        for forbidden_claim in forbidden_claims:
            assert forbidden_claim not in text


def test_cis_provenance_review_records_accuracy_sources_boundaries_and_forbidden_claims() -> None:
    review = _provenance_review()
    inventory = _inventory()
    model = _model()
    matrix = json.loads(
        (REPOSITORY_ROOT / "docs/architecture/product-documentation-provenance-matrix-0.9.0.json")
        .read_text(encoding="utf-8")
    )
    source_families = {family["id"]: family for family in matrix["source_families"]}
    restricted_family = source_families["cis-benchmark-pdf"]

    assert review["schema_version"] == 1
    assert review["backlog_item"] == "BPM090-M6-09"
    assert review["target_bpm_version"] == "0.9.0"
    assert review["generated_by"] == "documentation/tools/generate_cis_recommendation_skeletons.py"
    assert review["source_matrix"] == model["source_matrix"]
    assert review["source_family_ids"] == {
        "publishable_mapping": "bpm-cis-mapping-implementation",
        "restricted_benchmark": "cis-benchmark-pdf",
        "trademark_policy": "cis-trademarks-and-certification-marks",
    }
    assert review["benchmark"] == {
        "id": inventory["benchmark"]["id"],
        "upstream_name": inventory["benchmark"]["upstream_name"],
        "upstream_version": inventory["benchmark"]["upstream_version"],
        "exact_release_date": inventory["benchmark"]["exact_release_date"],
        "tested_by_cis_against": inventory["benchmark"]["tested_by_cis_against"],
        "source_license": restricted_family["license_id"],
        "source_license_url": inventory["benchmark"]["source_license_url"],
        "source_terms_url": inventory["benchmark"]["source_terms_url"],
        "official_source_required": True,
        "source_content_redistribution_reviewed": False,
    }
    assert review["source_boundary"] == {
        "allowed_publication_policy": "approval-required for benchmark expression",
        "benchmark_prose_published": False,
        "certification_claimed": False,
        "compliance_guaranteed": False,
        "conformance_claimed": False,
        "official_pdf_committed": False,
        "official_pdf_packaged": False,
        "publishable_source_family_id": "bpm-cis-mapping-implementation",
        "restricted_source_family_id": restricted_family["id"],
        "rights_approval_id_when_required": None,
        "source_expression_copied": False,
        "source_expression_indexed": False,
        "source_titles_published": False,
    }
    assert set(model["disclaimer_contract"]["forbidden_claims"]) <= set(review["forbidden_claims"])
    assert {
        "copied-cis-benchmark-prose",
        "published-cis-recommendation-title",
        "published-cis-audit-or-remediation-prose",
        "missing-source-title-hash",
        "missing-provenance-id",
        "missing-manual-review-boundary",
    } <= set(review["forbidden_claims"])
    assert review["accuracy_checks"] == {
        "authored_topics_require_non_certification_boundary": True,
        "benchmark_version_metadata_complete": True,
        "generated_topics_require_source_boundary": True,
        "layer_checked_examples_required": True,
        "level_metadata_complete": True,
        "manual_review_metadata_complete": True,
        "mapping_metadata_complete": True,
        "provenance_only_records_closed": True,
        "source_metadata_complete": True,
    }

    records = {record["recommendation_id"]: record for record in review["records"]}
    assert set(records) == {recommendation["recommendation_id"] for recommendation in inventory["recommendations"]}
    assert review["summary"] == {
        "level_counts": inventory["summary"]["level_counts"],
        "manual_review_path_count": len(inventory["manual_review_paths"]),
        "mapping_status_counts": inventory["summary"]["mapping_status_counts"],
        "merge_decision_types": inventory["merge_contract"]["decision_types"],
        "persisted_exception_model": inventory["exception_contract"]["persisted_exception_model"],
        "planned_topic_count": 53,
        "provenance_only_count": 2,
        "publication_disposition_counts": inventory["summary"]["publication_disposition_counts"],
        "recommendation_count": 55,
        "target_count": 53,
    }

    manual_review_path_ids = {path["path_id"] for path in inventory["manual_review_paths"]}
    for recommendation in inventory["recommendations"]:
        record = records[recommendation["recommendation_id"]]
        expected_manual_review = [
            ".".join(target["path"])
            for target in recommendation["targets"]
            if ".".join(target["path"]) in manual_review_path_ids
        ]
        assert record["source_section"] == recommendation["source_section"]
        assert record["source_title_sha256"] == recommendation["source_title_sha256"]
        assert len(record["source_title_sha256"]) == 64
        assert record["provenance_id"] == recommendation["provenance_id"]
        assert record["level"] == recommendation["level"]
        assert record["mapping_status"] == recommendation["mapping_status"]
        assert record["publication_disposition"] == recommendation["publication_disposition"]
        assert record["manual_review_paths"] == expected_manual_review
        assert record["source_expression_published"] is False
        assert record["source_expression_indexed"] is False
        assert record["source_title_published"] is False
        assert record["benchmark_prose_published"] is False
        if recommendation["publication_disposition"] == "planned-dita-topic":
            assert record["doc_id"] == recommendation["doc_id"]
            assert record["topic_path"] == (
                f"documentation/src/generated/cis/recommendations/{recommendation['doc_id']}.dita"
            )
            assert (REPOSITORY_ROOT / record["topic_path"]).is_file()
            assert record["expected_topic_props"] in {"cis-level-1", "cis-level-2"}
            assert record["topic_section_ids"] == [section["id"] for section in model["required_sections"]]
            assert record["target_count"] == len(recommendation["targets"]) > 0
        else:
            assert record["doc_id"] is None
            assert record["topic_path"] is None
            assert record["expected_topic_props"] is None
            assert record["target_count"] == 0
            assert record["non_publishable_reason"]


def test_generated_cis_topics_carry_reviewed_version_level_mapping_manual_and_source_metadata() -> None:
    inventory = _inventory()
    recommendations = {
        recommendation["recommendation_id"]: recommendation
        for recommendation in inventory["recommendations"]
    }

    for record in _provenance_review()["records"]:
        if record["publication_disposition"] != "planned-dita-topic":
            continue

        recommendation = recommendations[record["recommendation_id"]]
        topic_text = (REPOSITORY_ROOT / record["topic_path"]).read_text(encoding="utf-8")
        root = ET.fromstring(topic_text)
        sections = {section.attrib["id"]: " ".join(section.itertext()) for section in root.findall("./refbody/section")}

        assert root.attrib["props"] == record["expected_topic_props"]
        assert root.attrib["otherprops"] == f"cis({record['recommendation_id']})"
        for required in (
            inventory["benchmark"]["id"],
            inventory["benchmark"]["upstream_name"],
            inventory["benchmark"]["upstream_version"],
            inventory["benchmark"]["exact_release_date"],
            inventory["benchmark"]["tested_by_cis_against"],
            inventory["benchmark"]["source_license"],
            record["recommendation_id"],
            str(record["level"]),
            record["source_section"],
            record["source_title_sha256"],
            record["provenance_id"],
            recommendation["publication_disposition"],
            recommendation["mapping_status"],
            "bpm-cis-mapping-implementation",
            "cis-benchmark-pdf",
            "CC-BY-NC-SA-4.0",
            "not copied, translated, indexed, or packaged",
            "not authorized, sponsored, endorsed, certified, or approved by CIS",
        ):
            assert required in topic_text

        assert "BPM has no separate persisted CIS exception or waiver model in 0.9.0" in topic_text
        for layer_id in recommendation["generated_layers"]:
            assert layer_id in sections["a-automation-state"]
        for target in recommendation["targets"]:
            assert target["target_id"] in sections["a-bpm-mapping"]
            assert target["target_doc_id"] in sections["a-bpm-mapping"]
            assert target["ui_target"] in sections["a-bpm-mapping"]
            assert ".".join(target["path"]) in sections["a-bpm-mapping"]


def test_all_shipped_cis_guidance_rejects_restricted_source_prose_and_unsupported_claims() -> None:
    forbidden_claim_patterns = tuple(_model()["disclaimer_contract"]["forbidden_claims"]) + (
        "copied from CIS",
        "verbatim CIS",
        "CIS-BENCHMARK-PROSE-REGION",
        "CIS source expression copied",
        "CIS audit procedure",
        "CIS remediation procedure",
    )
    shipped_cis_topics = [
        *sorted(RECOMMENDATIONS_ROOT.glob("*.dita")),
        *sorted((DOCUMENTATION_ROOT / "src/dita").glob("*/cis/*.dita")),
    ]

    assert shipped_cis_topics
    for path in shipped_cis_topics:
        topic_text = path.read_text(encoding="utf-8")
        assert "source expression are not copied" in topic_text or "CIS" in topic_text
        for forbidden in forbidden_claim_patterns:
            assert forbidden.casefold() not in topic_text.casefold()


def test_cis_generator_preserves_existing_reviewed_hand_regions(tmp_path: Path) -> None:
    output_root = tmp_path / "generated-cis"
    existing_topic = output_root / "recommendations/cis-rec-1-1-1-1.dita"
    existing_topic.parent.mkdir(parents=True)
    custom_region = (
        "<!-- BPM-HAND-REGION-START verification -->\n"
        "      <p>Custom reviewed verification survives regeneration.</p>\n"
        "    <!-- BPM-HAND-REGION-END verification -->"
    )
    existing_topic.write_text(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<reference>\n"
        f"    {custom_region}\n"
        "</reference>\n",
        encoding="utf-8",
    )

    files = generator.build_generated_files(INVENTORY_PATH, MODEL_PATH, output_root)
    regenerated = next(file for file in files if file.path == existing_topic).content

    assert "Custom reviewed verification survives regeneration." in regenerated
    assert "BPM-HAND-REGION-START bpm-authored-summary" in regenerated
