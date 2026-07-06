from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
MODEL_PATH = DOCUMENTATION_ROOT / "config/firefox-policy-topic-model-0.9.0.json"
INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
TEMPLATE_PATH = DOCUMENTATION_ROOT / "src/shared/templates/firefox-policy-reference-topic.dita"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

pytestmark = pytest.mark.docs_contract


def _model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _policy(policy_id: str) -> dict[str, object]:
    policies = _inventory()["policies"]
    return next(policy for policy in policies if policy["policy_id"] == policy_id)


def _slug_preference(preference_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", preference_id.lower()).strip("-")


def test_firefox_policy_topic_model_declares_stable_topic_identity_and_sections() -> None:
    model = _model()

    assert model["schema_version"] == 1
    assert model["target_bpm_version"] == "0.9.0"
    assert model["guide_id"] == "firefox-policy-guide"
    assert model["backlog_item"] == "BPM090-M5-01"
    assert model["status"] == "defined"
    assert model["source_inventory"] == "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
    assert model["template_source"] == "documentation/src/shared/templates/firefox-policy-reference-topic.dita"

    topic = model["topic"]
    assert topic["dita_type"] == "reference"
    assert topic["topic_id_pattern"] == "fx-policy-{policy_id}"
    assert topic["managed_preference_topic_id_pattern"] == "fx-pref-{preference_id_slug}"
    assert topic["key_pattern"] == "topic.fx-policy-{policy_id}"
    assert topic["otherprops_policy"] == "policy({policy_id})"
    assert topic["conditional_props"] == {"release": "firefox-release", "esr": "firefox-esr"}

    sections = model["required_sections"]
    assert [section["id"] for section in sections] == [
        "a-purpose",
        "a-bpm-location",
        "a-value-shape",
        "a-channel-support",
        "a-examples",
        "a-validation",
        "a-caveats",
        "a-interactions",
        "a-cis-links",
        "a-provenance",
    ]
    for section in sections:
        assert section["title"]
        assert section["required_fields"]


def test_model_covers_supported_channels_simple_complex_and_release_only_policy_shapes() -> None:
    model = _model()
    inventory = _inventory()
    fixture_policy_ids = model["fixture_policy_ids"]
    channel_model = model["channel_support_model"]
    value_model = model["value_shape_model"]

    assert channel_model["supported_channels"] == list(inventory["channels"])
    assert channel_model["channel_scope_values"] == ["both", "release-only", "esr-only"]
    assert value_model["value_types"] == ["boolean", "string", "integer", "array", "object"]
    assert value_model["simple_policy_types"] == ["boolean", "string", "integer"]
    assert value_model["complex_policy_types"] == ["array", "object"]

    simple = _policy(fixture_policy_ids["simple_boolean_both_channels"])
    complex_object = _policy(fixture_policy_ids["complex_object_both_channels"])
    preserve_unknown = _policy(fixture_policy_ids["advanced_dictionary_preserve_unknown"])
    release_object = _policy(fixture_policy_ids["release_only_object"])
    release_boolean = _policy(fixture_policy_ids["release_only_boolean"])

    assert simple["channel_scope"] == "both"
    assert {entry["value_type"] for entry in simple["channels"].values()} == {"boolean"}
    assert complex_object["channel_scope"] == "both"
    assert {entry["value_type"] for entry in complex_object["channels"].values()} == {"object"}
    assert preserve_unknown["channels"]["esr-140.12"]["ui"]["preserve_unknown_fields"] is True
    assert release_object["channel_scope"] == "release-only"
    assert set(release_object["channels"]) == {"release-152"}
    assert release_object["channels"]["release-152"]["value_type"] == "object"
    assert release_boolean["channel_scope"] == "release-only"
    assert release_boolean["channels"]["release-152"]["value_type"] == "boolean"

    for policy in (simple, complex_object, preserve_unknown, release_object, release_boolean):
        assert policy["doc_id"] == model["topic"]["topic_id_pattern"].format(
            policy_id=policy["policy_id"]
        )
        assert policy["ui_target"] == f"policy:{policy['policy_id']}"
        for channel in policy["channels"].values():
            for field in channel_model["per_channel_required_fields"]:
                assert field in channel


def test_model_includes_examples_relationships_managed_preferences_and_generation_contract() -> None:
    model = _model()
    inventory = _inventory()

    example_model = model["example_model"]
    assert example_model["required"] is True
    assert example_model["document_shape"] == "Firefox boundary document with top-level policies object"
    assert set(example_model["example_fields"]) == {
        "id",
        "channel",
        "document",
        "validates",
        "purpose",
        "notes",
    }

    relationship_model = model["relationship_model"]
    assert "policy:{policy_id}" in relationship_model["ui_targets"]
    assert "known-preference:{preference_id}" in relationship_model["ui_targets"]
    assert "ug-task-use-all-settings" in relationship_model["user_guide_links"]
    assert relationship_model["cis_link_format"] == "cis({recommendation_id})"
    assert relationship_model["api_operation_links"] == ["API-VAL-001", "API-EXP-001", "API-IMP-001"]

    managed_shape = model["value_shape_model"]["managed_preference_shape"]
    assert managed_shape["container_policy"] == "Preferences"
    assert managed_shape["topic_id_pattern"] == "fx-pref-{preference_id_slug}"
    preference = inventory["managed_preferences"][0]
    expected_pref_id = managed_shape["topic_id_pattern"].format(
        preference_id_slug=_slug_preference(preference["preference_id"])
    )
    assert preference["doc_id"] == expected_pref_id
    for field in managed_shape["required_fields"]:
        assert field in preference

    generator_contract = model["generator_contract"]
    assert generator_contract["skeleton_owner"] == "documentation/src/generated"
    assert generator_contract["reviewed_topic_owner"] == "documentation/src/dita/{locale}/firefox"
    assert {"purpose", "caveats", "interactions", "cis-links", "reviewed-examples"} <= set(
        generator_contract["hand_authored_regions"]
    )
    assert {"policy-id", "bpm-location", "value-shape", "channel-support", "provenance"} <= set(
        generator_contract["generated_regions"]
    )
    assert "preserve hand-authored regions byte-for-byte" in generator_contract["regeneration_rule"]


def test_dita_reference_template_matches_model_sections_and_registered_metadata() -> None:
    model = _model()
    root = ET.fromstring(TEMPLATE_PATH.read_text(encoding="utf-8"))

    assert root.tag == "reference"
    assert root.attrib == {
        "id": "fx-policy-reference-topic-template",
        XML_LANG: "en",
        "audience": "user",
        "product": "bpm-0-9-0",
        "platform": "web",
        "props": "firefox-release",
        "otherprops": "policy(AIControls)",
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
