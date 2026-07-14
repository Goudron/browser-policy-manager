from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
PROTOCOL = DOCUMENTATION_ROOT / "config/documentation-sufficiency-review-protocol-0.9.1.json"

pytestmark = pytest.mark.docs_contract


def _protocol() -> dict[str, object]:
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_sufficiency_protocol_is_scoped_to_091_and_source_backed() -> None:
    protocol = _protocol()

    assert protocol["schema_version"] == 1
    assert protocol["contract_id"] == "bpm-doc-sufficiency-review-protocol-0.9.1"
    assert protocol["backlog_item"] == "BPM091-M2-06"
    assert protocol["target_bpm_version"] == "0.9.1"
    assert protocol["status"] == "accepted"
    assert "complete the documented action and reach the stated result" in protocol["purpose"]
    assert protocol["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert protocol["guide_families"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]

    inherited = set(protocol["inherits_from"])
    assert {
        "documentation/config/user-guide-coverage-closure-0.9.0.json",
        "docs/architecture/product-documentation-content-coverage-audit-0.9.0.md",
        "documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json",
        "documentation/tests/suite-boundaries-0.9.0.json",
    } <= inherited


def test_review_item_template_requires_actionable_sufficiency_fields() -> None:
    protocol = _protocol()
    template = protocol["review_item_template"]

    assert set(template["required_fields"]) >= {
        "review_id",
        "guide_id",
        "topic_id",
        "locale_scope",
        "task_or_claim",
        "prerequisites",
        "exact_steps",
        "expected_result",
        "recovery_path",
        "drift_source",
        "focused_verification",
        "evidence_type",
        "evidence_artifact",
        "review_disposition",
    }
    assert template["locale_scope_values"] == [
        "all-locales",
        "source-locale-plus-parity",
        "single-locale",
    ]
    assert template["review_disposition_values"] == ["pass", "blocked", "deferred-non-goal"]


def test_checklist_covers_prerequisites_steps_result_recovery_drift_and_verification() -> None:
    protocol = _protocol()
    checklist = protocol["checklist"]

    assert set(checklist) == {
        "prerequisites",
        "exact_steps",
        "expected_result",
        "recovery_path",
        "drift_source",
        "focused_verification",
    }
    assert "product version" in checklist["prerequisites"][0]
    assert "commands, clicks, API calls, file paths" in checklist["exact_steps"][0]
    assert "observable successful end state" in checklist["expected_result"][0]
    assert "likely failure mode" in checklist["recovery_path"][0]
    assert "product file, inventory, schema, fixture" in checklist["drift_source"][0]
    assert "narrowest relevant docs contract" in checklist["focused_verification"][0]


def test_evidence_types_include_hands_on_simulation_static_and_waiver_paths() -> None:
    protocol = _protocol()
    evidence = protocol["evidence_types"]

    assert set(evidence) == {
        "hands_on_browser",
        "hands_on_command_transcript",
        "browser_smoke",
        "api_or_unit_test",
        "static_source_simulation",
        "documented_simulation_evidence",
        "explicit_waiver",
    }
    assert "performs the documented UI workflow" in evidence["hands_on_browser"]["description"]
    assert "runs the documented shell/API commands" in evidence["hands_on_command_transcript"]["description"]
    assert "maps every step to deterministic source" in evidence["documented_simulation_evidence"]["description"]
    assert "maintainer-approved non-goal" in evidence["explicit_waiver"]["description"]


def test_each_guide_family_has_minimum_evidence_and_closure_rules() -> None:
    protocol = _protocol()
    rules = protocol["guide_family_rules"]

    assert set(rules) == set(protocol["guide_families"])
    for rule in rules.values():
        assert rule["scope"]
        assert rule["minimum_evidence"]
        assert rule["must_cover"]
        assert rule["closure_rule"]

    assert "hands_on_browser" in rules["user-guide"]["minimum_evidence"]
    assert "documented_simulation_evidence" in rules["user-guide"]["minimum_evidence"]
    assert "cannot close from topic presence or static coverage alone" in rules["user-guide"]["closure_rule"]
    assert "all settings" in rules["user-guide"]["must_cover"]
    assert "JSON editor" in rules["user-guide"]["must_cover"]

    assert "static_source_simulation" in rules["firefox-policy-guide"]["minimum_evidence"]
    assert "schema provenance" in rules["firefox-policy-guide"]["must_cover"]
    assert "source-attribution boundaries" in rules["cis-settings-guide"]["closure_rule"]
    assert "API integration" in rules["administrator-guide"]["scope"]
    assert "hands_on_command_transcript" in rules["administrator-guide"]["minimum_evidence"]
    assert "cannot close from static text checks alone" in rules["administrator-guide"]["closure_rule"]


def test_source_install_rule_requires_hands_on_or_documented_simulation_evidence() -> None:
    protocol = _protocol()
    rule = protocol["source_install_special_rule"]

    assert "future five-distribution Linux source-install topics" in rule["applies_to"]
    assert rule["required_evidence"] == [
        "hands_on_command_transcript",
        "documented_simulation_evidence",
    ]
    assert {
        "exact distribution or OS name and version",
        "shell used",
        "Python version",
        "commands in documented order",
        "exit status or observable result for each verification command",
        "unverified external boundary if simulation was used",
    } <= set(rule["must_include"])
    assert {
        "exact command sequence",
        "health/readiness verification",
        "database migration or explicit no-migration statement",
        "documentation build verification",
        "rollback or stop condition",
    } <= set(rule["blocked_if_missing"])


def test_records_verification_and_non_goals_are_release_ready() -> None:
    protocol = _protocol()

    records = protocol["review_records"]
    assert "documentation/reports/diagnostics/" in records["storage"]
    assert "docs/architecture/" in records["storage"]
    assert records["naming"] == "documentation-sufficiency-{guide_id}-{topic_id}-0.9.1.json"
    assert "secrets" in records["must_not_commit"]
    assert "licensed benchmark source text" in records["must_not_commit"]

    assert protocol["implementation_tasks"] == [
        "BPM091-M6-01",
        "BPM091-M6-02",
        "BPM091-M6-03",
        "BPM091-M6-04",
        "BPM091-M6-05",
        "BPM091-M6-06",
        "BPM091-M6-07",
        "BPM091-M9-05",
    ]
    assert (
        "./.venv/bin/pytest -q documentation/tests/contract/"
        "test_documentation_sufficiency_drift.py"
    ) in protocol["verification"]["focused_contracts"]
    assert "make docs-release-check" in protocol["verification"]["release_gates"]
    assert "User Guide task walkthroughs" in protocol["verification"]["manual_or_simulation_required_for"]
    assert "This protocol does not perform the sufficiency review." in protocol["non_goals"]
