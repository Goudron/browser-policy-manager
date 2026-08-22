from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONTRACT = DOCUMENTATION_ROOT / "config/all-settings-help-target-map-0.9.1.json"
INVENTORY = REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
TARGET_SCHEMA = (
    REPOSITORY_ROOT / "docs/architecture/schemas/product-documentation-ui-target-map-v1.schema.json"
)
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"

SPEC = importlib.util.spec_from_file_location("build_docs_m9_02", BUILD_DOCS_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_map() -> dict:
    guide_topics = {
        build_docs._guide_topic_id(guide_id): {}
        for guide_id, _filename, _anchor, _url_root in build_docs.GUIDE_MAPS
    }
    guide_topics.update(
        {topic_id: {} for topic_id in build_docs._api_operation_topic_ids().values()}
    )
    return build_docs._build_target_map(guide_topics)


def test_contract_declares_exact_manifest_backed_identity_rules() -> None:
    contract = _json(CONTRACT)

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-all-settings-help-target-map-0.9.1"
    assert contract["backlog_item"] == "BPM096-M10-04"
    assert contract["target_bpm_version"] == "0.9.6"
    assert contract["status"] == "accepted"
    assert contract["known_preference_targets"] == {
        "target_pattern": "known-preference:{exact.preference.id}",
        "topic_id": "fx-reference-managed-preference-locking",
        "anchor_id": "a-safe-review",
        "coverage": (
            "Exact set of known managed preference IDs in the Firefox documentation inventory."
        ),
        "identity_rule": (
            "Preference IDs are case-sensitive and must not be lowercased, translated, slugified, or derived from visible labels."
        ),
    }
    assert contract["alias_policy"]["generated_alias_target_ids"] == []
    assert "canonical policy or preference identity" in contract["alias_policy"]["rule"]


def test_target_map_covers_exact_release_esr_policy_union_and_known_preferences() -> None:
    inventory = _json(INVENTORY)
    targets = _target_map()["targets"]
    policy_ids = {item["policy_id"] for item in inventory["policies"]}
    preference_ids = {item["preference_id"] for item in inventory["managed_preferences"]}

    assert inventory["summary"]["policy_scope_counts"] == {
        "both": 97,
        "partial": 24,
        "release-only": 1,
        "esr-only": 1,
    }
    assert {
        key.removeprefix("policy:") for key in targets if key.startswith("policy:")
    } == policy_ids
    assert {
        key.removeprefix("known-preference:")
        for key in targets
        if key.startswith("known-preference:")
    } == preference_ids


def test_known_preference_targets_preserve_case_and_use_local_reference_anchor() -> None:
    target_map = _target_map()
    targets = target_map["targets"]
    preference_targets = {
        key: target for key, target in targets.items() if key.startswith("known-preference:")
    }

    assert len(preference_targets) == 62
    assert "known-preference:network.IDN_show_punycode" in preference_targets
    assert "known-preference:network.idn_show_punycode" not in preference_targets
    for target_id, target in preference_targets.items():
        assert target == {
            "kind": "known-preference",
            "source_id": target_id.removeprefix("known-preference:"),
            "source_inventory": (
                "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
            ),
            "topic_id": "fx-reference-managed-preference-locking",
            "anchor_id": "a-safe-review",
        }
    Draft202012Validator(_json(TARGET_SCHEMA)).validate(target_map)


def test_known_preference_reference_anchor_exists_in_every_locale() -> None:
    for locale in build_docs.LOCALES:
        path = (
            DOCUMENTATION_ROOT
            / "src/dita"
            / locale
            / "firefox/fx-reference-managed-preference-locking.dita"
        )
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        assert root.attrib["id"] == "fx-reference-managed-preference-locking"
        assert root.find("./refbody/section[@id='a-safe-review']") is not None


def test_target_coverage_validation_fails_for_missing_removed_and_case_changed_ids() -> None:
    targets = _target_map()["targets"]

    missing = dict(targets)
    missing.pop("known-preference:browser.download.dir")
    with pytest.raises(build_docs.BuildError, match="missing known preference targets"):
        build_docs._validate_all_settings_help_target_coverage(missing)

    extra = dict(targets)
    extra["policy:RemovedPolicy"] = dict(targets["policy:AIControls"])
    with pytest.raises(build_docs.BuildError, match="unknown policy targets"):
        build_docs._validate_all_settings_help_target_coverage(extra)

    changed_case = dict(targets)
    changed_case["known-preference:network.idn_show_punycode"] = changed_case.pop(
        "known-preference:network.IDN_show_punycode"
    )
    with pytest.raises(build_docs.BuildError, match="missing known preference targets"):
        build_docs._validate_all_settings_help_target_coverage(changed_case)


def test_target_map_rejects_unknown_contract_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        build_docs,
        "_read_json_file",
        lambda path: (
            {"schema_version": 2}
            if path == build_docs.ALL_SETTINGS_HELP_TARGET_MAP
            else _json(path)
        ),
    )

    with pytest.raises(build_docs.BuildError, match="unsupported All Settings help target"):
        build_docs._all_settings_help_target_contract()
