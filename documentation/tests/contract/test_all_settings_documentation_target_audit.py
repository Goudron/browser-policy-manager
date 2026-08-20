from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
AUDIT = DOCUMENTATION_ROOT / "config/all-settings-documentation-target-audit-0.9.1.json"
INVENTORY = REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
POLICY_INDEX = DOCUMENTATION_ROOT / "src/generated/firefox/firefox-policy-skeletons-0.9.0.json"
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
INVENTORY_SOURCE = REPOSITORY_ROOT / "app/static/profiles_settings_inventory.js"

SPEC = importlib.util.spec_from_file_location("build_docs_m9_01", BUILD_DOCS_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _generated_target_map() -> dict:
    guide_topics = {
        build_docs._guide_topic_id(guide_id): {}
        for guide_id, _filename, _anchor, _url_root in build_docs.GUIDE_MAPS
    }
    guide_topics.update(
        {topic_id: {} for topic_id in build_docs._api_operation_topic_ids().values()}
    )
    return build_docs._build_target_map(guide_topics)


def test_audit_declares_m9_01_scope_status_and_sources() -> None:
    audit = _json(AUDIT)

    assert audit["schema_version"] == 1
    assert audit["audit_id"] == "bpm-all-settings-documentation-target-audit-0.9.1"
    assert audit["backlog_item"] == "BPM091-M9-01"
    assert audit["target_bpm_version"] == "0.9.5.1"
    assert audit["status"] == "accepted"
    for source in audit["audited_sources"].values():
        path = source.split("::", 1)[0]
        assert (REPOSITORY_ROOT / path).exists(), source


def test_all_policy_inventory_entries_have_exact_generated_targets() -> None:
    audit = _json(AUDIT)
    inventory = _json(INVENTORY)
    policy_index = _json(POLICY_INDEX)
    targets = _generated_target_map()["targets"]
    policy_ids = {policy["policy_id"] for policy in inventory["policies"]}
    indexed_policy_ids = {policy["policy_id"] for policy in policy_index["policies"]}
    generated_policy_ids = {
        target_id.removeprefix("policy:")
        for target_id in targets
        if target_id.startswith("policy:")
    }

    assert policy_ids == indexed_policy_ids == generated_policy_ids
    assert len(policy_ids) == audit["coverage"]["firefox_policies"]["inventory_count"] == 123
    assert inventory["summary"]["policy_scope_counts"] == {
        "both": audit["coverage"]["firefox_policies"]["both_channel_count"],
        "partial": audit["coverage"]["firefox_policies"]["partial_channel_count"],
        "release-only": audit["coverage"]["firefox_policies"]["release_only_policy_count"],
        "esr-only": audit["coverage"]["firefox_policies"]["esr_only_policy_count"],
    }
    assert all(targets[f"policy:{policy_id}"]["source_id"] == policy_id for policy_id in policy_ids)


def test_known_preferences_are_completely_classified_and_m9_02_closes_target_gap() -> None:
    audit = _json(AUDIT)
    inventory = _json(INVENTORY)
    targets = _generated_target_map()["targets"]
    preferences = inventory["managed_preferences"]
    preference_ids = {item["preference_id"] for item in preferences}
    declared_targets = {item["ui_target"] for item in preferences}
    generated_targets = {
        target_id for target_id in targets if target_id.startswith("known-preference:")
    }

    assert len(preference_ids) == len(declared_targets) == 62
    assert declared_targets == {f"known-preference:{item}" for item in preference_ids}
    assert generated_targets == declared_targets
    coverage = audit["coverage"]["known_managed_preferences"]
    assert coverage["inventory_count"] == coverage["declared_inventory_target_count"] == 62
    assert coverage["observed_at_m9_01_generated_target_count"] == 0
    assert coverage["generated_target_count"] == 62
    assert coverage["current_disposition"] == "linked"
    assert coverage["linked_disposition_owner"] == "BPM091-M9-02"


def test_every_runtime_row_class_has_target_fallback_or_no_link_disposition() -> None:
    audit = _json(AUDIT)
    rows = {row["row_class"]: row for row in audit["row_classes"]}

    assert set(rows) == {
        "schema_known_policy",
        "schema_known_raw_fallback_policy",
        "known_managed_preference",
        "unknown_imported_policy",
        "unknown_imported_preference",
        "invalid_known_entry",
        "deprecated_known_entry",
        "generated_inventory_entry",
    }
    assert rows["schema_known_policy"]["documentation_target"] == "policy:{exact_policy_id}"
    assert rows["schema_known_raw_fallback_policy"]["disposition"] == "linked"
    assert rows["known_managed_preference"]["disposition"] == "linked"
    for row_class in ("unknown_imported_policy", "unknown_imported_preference"):
        assert rows[row_class]["documentation_target"] is None
        assert rows[row_class]["disposition"] == "unsupported_unknown"
        assert rows[row_class]["editor_navigation_target"]
    assert "translated label" in rows["generated_inventory_entry"]["disposition"]


def test_runtime_inventory_keeps_editor_and_documentation_identities_distinguishable() -> None:
    source = INVENTORY_SOURCE.read_text(encoding="utf-8")

    assert "target: item.target || `policy:${item.id}`" in source
    assert "target: `known-preference:${item.pref}`" in source
    assert 'target: "settings-schema-shell-step-8"' in source
    assert "target: sectionId ? `pref-section:${sectionId}`" in source
    assert "Current entry.target values for unknown rows" in _json(AUDIT)["findings"][1]["finding"]


def test_audit_summary_and_closed_findings_match_implemented_guards() -> None:
    audit = _json(AUDIT)

    assert audit["summary"] == {
        "policy_inventory_count": 123,
        "policy_linked_count": 123,
        "known_preference_inventory_count": 62,
        "known_preference_linked_count": 62,
        "known_preference_missing_documentation_count": 0,
        "explicit_no_link_row_class_count": 2,
        "open_finding_count": 0,
        "closed_finding_count": 2,
    }
    findings = {item["finding_id"]: item for item in audit["findings"]}
    assert findings["ASDOC091-MISSING-KNOWN-PREFERENCE-TARGETS"]["affected_entry_count"] == 62
    assert findings["ASDOC091-MISSING-KNOWN-PREFERENCE-TARGETS"]["closure_task"] == "BPM091-M9-02"
    assert findings["ASDOC091-MISSING-KNOWN-PREFERENCE-TARGETS"]["status"] == "closed"
    editor_target_finding = findings["ASDOC091-EDITOR-TARGET-NOT-DOCUMENTATION-TARGET"]
    assert editor_target_finding["status"] == "closed"
    assert "emits no href" in editor_target_finding["closure_evidence"]
    assert findings["ASDOC091-EDITOR-TARGET-NOT-DOCUMENTATION-TARGET"]["closure_tasks"] == [
        "BPM091-M9-02",
        "BPM091-M9-03",
        "BPM091-M9-05",
    ]
