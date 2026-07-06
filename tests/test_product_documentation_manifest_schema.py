from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from tests.docs_index import doc_path_from_index

LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDE_ROOTS = {
    "user-guide": "user",
    "firefox-policy-guide": "firefox",
    "cis-settings-guide": "cis",
    "api-integration-guide": "api",
    "administrator-guide": "admin",
}


def _indexed_json(path: str) -> dict[str, Any]:
    return _load_strict(doc_path_from_index(path, status="active"))


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_strict(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )
    assert isinstance(value, dict)
    return value


def _inventory_contracts() -> dict[str, tuple[str, set[str]]]:
    architecture = Path("docs/architecture")
    firefox = json.loads(
        (architecture / "firefox-policy-documentation-inventory-0.9.0.json").read_text(
            encoding="utf-8"
        )
    )
    cis = json.loads(
        (architecture / "cis-documentation-inventory-0.9.0.json").read_text(encoding="utf-8")
    )
    api = (architecture / "api-documentation-inventory-0.9.0.md").read_text(encoding="utf-8")
    capabilities = (architecture / "product-user-capability-inventory-0.9.0.md").read_text(
        encoding="utf-8"
    )
    return {
        "policy": (
            "firefox-policy-documentation-inventory-0.9.0.json",
            {item["policy_id"] for item in firefox["policies"]},
        ),
        "known-preference": (
            "firefox-policy-documentation-inventory-0.9.0.json",
            {item["preference_id"] for item in firefox["managed_preferences"]},
        ),
        "cis": (
            "cis-documentation-inventory-0.9.0.json",
            {item["recommendation_id"] for item in cis["recommendations"]},
        ),
        "api-operation": (
            "api-documentation-inventory-0.9.0.md",
            set(re.findall(r"\| `(API-[A-Z0-9-]+)` \|", api)),
        ),
        "capability": (
            "product-user-capability-inventory-0.9.0.md",
            set(re.findall(r"\| `(CAP-[A-Z0-9-]+)` \|", capabilities)),
        ),
    }


def _validate_semantics(manifest: dict[str, Any], target_map: dict[str, Any]) -> None:
    if tuple(manifest["locales"]) != LOCALES or tuple(target_map["locales"]) != LOCALES:
        raise ValueError("locale matrix mismatch")
    if manifest["artifact"]["bpm_version"] != target_map["bpm_version"]:
        raise ValueError("BPM version mismatch")
    if manifest["ui_target_map"]["schema_version"] != target_map["schema_version"]:
        raise ValueError("target-map schema mismatch")
    if target_map["manifest_schema_version"] != manifest["schema_version"]:
        raise ValueError("manifest schema mismatch")

    guides = manifest["guides"]
    topics = manifest["topics"]
    canonical_paths: dict[str, str] = {}
    source_slugs: dict[str, str] = {}

    for guide_id, expected_root in GUIDE_ROOTS.items():
        if guides[guide_id]["url_root"] != expected_root:
            raise ValueError(f"wrong URL root for {guide_id}")
        home_topic_id = guides[guide_id]["home_topic_id"]
        if home_topic_id not in topics or topics[home_topic_id]["guide_id"] != guide_id:
            raise ValueError(f"broken home topic for {guide_id}")

    for topic_id, topic in topics.items():
        guide_id = topic["guide_id"]
        if guide_id not in guides:
            raise ValueError(f"unknown guide for {topic_id}")
        if topic["dita_key"] != f"topic.{topic_id}":
            raise ValueError(f"wrong DITA key for {topic_id}")

        source_slug_key = topic["source_slug"].casefold()
        if source_slug_key in source_slugs:
            raise ValueError(f"duplicate source slug for {topic_id}")
        source_slugs[source_slug_key] = topic_id

        canonical_path = f"{guides[guide_id]['url_root']}/{topic['url_path']}"
        canonical_key = canonical_path.casefold()
        if canonical_key in canonical_paths:
            raise ValueError(f"duplicate canonical URL for {topic_id}")
        canonical_paths[canonical_key] = topic_id

        canonical_anchors = set(topic["anchors"])
        anchor_aliases = [
            alias
            for anchor in topic["anchors"].values()
            for alias in anchor["aliases"]
        ]
        if len(anchor_aliases) != len(set(anchor_aliases)):
            raise ValueError(f"duplicate anchor alias for {topic_id}")
        if canonical_anchors & set(anchor_aliases):
            raise ValueError(f"anchor alias shadows canonical anchor for {topic_id}")

    for asset_id, asset in manifest["assets"].items():
        for topic_id in asset["topic_ids"]:
            if topic_id not in topics:
                raise ValueError(f"broken asset topic for {asset_id}")
        if asset["localization"] == "shared-approved" and not asset["reuse_approved"]:
            raise ValueError(f"unapproved shared asset {asset_id}")
        if asset["localization"] == "per-locale":
            paths = []
            for locale, variant in asset["variants"].items():
                path = variant["path"]
                if f"/{locale}/" not in path:
                    raise ValueError(f"wrong locale path for {asset_id}:{locale}")
                paths.append(path.casefold())
            if len(paths) != len(set(paths)):
                raise ValueError(f"duplicate localized asset path for {asset_id}")

    for locale, search in manifest["search"].items():
        if search["document_count"] != len(topics):
            raise ValueError(f"search topic count mismatch for {locale}")

    for alias_path, alias in manifest["aliases"].items():
        topic_id = alias["topic_id"]
        if topic_id not in topics:
            raise ValueError(f"broken alias topic for {alias_path}")
        topic = topics[topic_id]
        expected_path = f"{guides[topic['guide_id']]['url_root']}/{topic['url_path']}"
        if alias["canonical_url_path"] != expected_path:
            raise ValueError(f"broken alias destination for {alias_path}")
        if alias_path.casefold() in canonical_paths:
            raise ValueError(f"alias shadows canonical URL {alias_path}")
        anchor_id = alias.get("anchor_id")
        if anchor_id is not None and anchor_id not in topic["anchors"]:
            raise ValueError(f"broken alias anchor for {alias_path}")

    inventory_contracts = _inventory_contracts()
    for target_id, target in target_map["targets"].items():
        if target_id != f"{target['kind']}:{target['source_id']}":
            raise ValueError(f"target identity mismatch for {target_id}")
        if target["kind"] == "topic":
            if target["source_id"] not in topics:
                raise ValueError(f"unknown inventory target for {target_id}")
        else:
            inventory_name, known_source_ids = inventory_contracts[target["kind"]]
            if target["source_inventory"] != inventory_name:
                raise ValueError(f"target inventory mismatch for {target_id}")
            if target["source_id"] not in known_source_ids:
                raise ValueError(f"unknown inventory target for {target_id}")
        topic_id = target["topic_id"]
        if topic_id not in topics:
            raise ValueError(f"broken target topic for {target_id}")
        anchor_id = target.get("anchor_id")
        if anchor_id is not None and anchor_id not in topics[topic_id]["anchors"]:
            raise ValueError(f"broken target anchor for {target_id}")


def _contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest_schema = _indexed_json(
        "architecture/schemas/product-documentation-manifest-v1.schema.json"
    )
    target_schema = _indexed_json(
        "architecture/schemas/product-documentation-ui-target-map-v1.schema.json"
    )
    manifest = _indexed_json(
        "architecture/examples/product-documentation-manifest-v1.example.json"
    )
    target_map = _indexed_json(
        "architecture/examples/product-documentation-ui-target-map-v1.example.json"
    )
    return manifest_schema, target_schema, manifest, target_map


def test_documentation_manifest_schemas_are_valid_draft_2020_12():
    manifest_schema, target_schema, _, _ = _contracts()

    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator.check_schema(target_schema)
    assert manifest_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert target_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_documentation_manifest_examples_pass_structural_and_semantic_validation():
    manifest_schema, target_schema, manifest, target_map = _contracts()

    Draft202012Validator(manifest_schema).validate(manifest)
    Draft202012Validator(target_schema).validate(target_map)
    _validate_semantics(manifest, target_map)

    assert tuple(manifest["locales"]) == LOCALES
    assert set(manifest["guides"]) == set(GUIDE_ROOTS)
    assert {target["kind"] for target in target_map["targets"].values()} == {
        "topic",
        "policy",
        "known-preference",
        "cis",
        "api-operation",
        "capability",
    }


def test_documentation_manifest_schema_rejects_missing_locale_and_required_fields():
    manifest_schema, _, manifest, _ = _contracts()
    invalid = copy.deepcopy(manifest)
    del invalid["topics"]["ug-task-create-first-profile"]["title"]["fr"]

    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(invalid)

    del invalid["artifact"]["build_id"]
    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(invalid)


def test_documentation_manifest_contract_rejects_duplicate_ids_and_urls():
    with pytest.raises(ValueError, match="duplicate JSON key: fx-policy-AIControls"):
        json.loads(
            '{"topics":{"fx-policy-AIControls":{},"fx-policy-AIControls":{}}}',
            object_pairs_hook=_reject_duplicate_pairs,
        )

    _, _, manifest, target_map = _contracts()
    invalid = copy.deepcopy(manifest)
    invalid["topics"]["fx-pref-browser-download-dir"]["url_path"] = "policies/ai-controls"
    with pytest.raises(ValueError, match="duplicate canonical URL"):
        _validate_semantics(invalid, target_map)


def test_documentation_manifest_contract_rejects_broken_targets_anchors_and_assets():
    _, _, manifest, target_map = _contracts()

    broken_topic = copy.deepcopy(target_map)
    broken_topic["targets"]["policy:AIControls"]["topic_id"] = "fx-policy-missing"
    with pytest.raises(ValueError, match="broken target topic"):
        _validate_semantics(manifest, broken_topic)

    broken_anchor = copy.deepcopy(target_map)
    broken_anchor["targets"]["policy:AIControls"]["anchor_id"] = "a-missing"
    with pytest.raises(ValueError, match="broken target anchor"):
        _validate_semantics(manifest, broken_anchor)

    unknown_policy = copy.deepcopy(target_map)
    target = unknown_policy["targets"].pop("policy:AIControls")
    target["source_id"] = "NotShipped"
    unknown_policy["targets"]["policy:NotShipped"] = target
    with pytest.raises(ValueError, match="unknown inventory target"):
        _validate_semantics(manifest, unknown_policy)

    broken_asset = copy.deepcopy(manifest)
    asset = broken_asset["assets"]["shot-ug-task-create-first-profile-library-empty"]
    asset["topic_ids"] = ["ug-task-missing"]
    with pytest.raises(ValueError, match="broken asset topic"):
        _validate_semantics(broken_asset, target_map)


def test_documentation_target_example_uses_current_inventory_identities():
    _, _, _, target_map = _contracts()
    architecture = Path("docs/architecture")
    firefox = json.loads(
        (architecture / "firefox-policy-documentation-inventory-0.9.0.json").read_text(
            encoding="utf-8"
        )
    )
    cis = json.loads(
        (architecture / "cis-documentation-inventory-0.9.0.json").read_text(encoding="utf-8")
    )
    api = (architecture / "api-documentation-inventory-0.9.0.md").read_text(encoding="utf-8")
    capabilities = (architecture / "product-user-capability-inventory-0.9.0.md").read_text(
        encoding="utf-8"
    )

    assert "AIControls" in {item["policy_id"] for item in firefox["policies"]}
    assert "browser.download.dir" in {
        item["preference_id"] for item in firefox["managed_preferences"]
    }
    assert "1.1.1.1" in {item["recommendation_id"] for item in cis["recommendations"]}
    assert "`API-PROFILE-005`" in api
    assert "`CAP-LIB-001`" in capabilities
    assert set(target_map["targets"]) >= {
        "policy:AIControls",
        "known-preference:browser.download.dir",
        "cis:1.1.1.1",
        "api-operation:API-PROFILE-005",
        "capability:CAP-LIB-001",
    }
