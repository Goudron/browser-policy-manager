from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CLOSURE = ROOT / "docs/architecture/documentation-sufficiency-closure-0.9.1.json"
RELEASE_CONTRACT = ROOT / "docs/architecture/product-documentation-release-contract-0.9.1.md"
MATRIX = ROOT / "documentation/config/user-guide-screenshot-matrix-0.9.1.json"
VISUAL_QA = ROOT / "documentation/config/user-guide-screenshot-visual-qa-0.9.1.json"
TARGET_AUDIT = ROOT / "documentation/config/all-settings-documentation-target-audit-0.9.1.json"
TARGET_MAP = ROOT / "documentation/config/all-settings-help-target-map-0.9.1.json"
LIVE_CLOSURE = (
    ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-14-evidence-closure-20260715/closure.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _outcomes() -> dict[str, dict]:
    return {item["id"]: item for item in _json(CLOSURE)["outcomes"]}


def test_closure_reconciles_every_requested_documentation_outcome() -> None:
    closure = _json(CLOSURE)

    assert closure["schema_version"] == 1
    assert closure["closure_id"] == "bpm-0.9.1-documentation-sufficiency-closure"
    assert closure["backlog_item"] == "BPM091-M12-05"
    assert closure["target_bpm_version"] == "0.9.1"
    assert closure["status"] == "accepted"
    assert closure["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert closure["guide_families"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]
    assert set(_outcomes()) == {
        "minimal-localized-user-guide-screenshots",
        "application-and-documentation-themes",
        "compact-localized-documentation-search",
        "single-hierarchical-navigation",
        "four-guide-consolidation",
        "locale-terminology-and-visible-prose",
        "all-settings-contextual-help",
        "five-linux-source-install-procedures",
        "windows-wsl-conditional-validation",
        "maintained-drift-gates",
    }
    assert closure["release_blockers"] == []


def test_guide_reviews_are_accepted_without_hidden_blockers() -> None:
    closure = _json(CLOSURE)

    for record in closure["guide_reviews"]:
        review = _json(ROOT / record["review"])
        assert record["status"] == review["status"] == "accepted"
        assert record["release_blockers"] == []
        assert review.get("release_blockers", review["summary"].get("release_blockers")) == []

    administrator = _json(
        ROOT / "docs/architecture/administrator-devops-guide-sufficiency-review-0.9.1.json"
    )
    sections = {item["section_id"]: item for item in administrator["section_reviews"]}
    wsl = sections["windows-wsl-source-deployment"]
    assert wsl["review_disposition"] == "deferred-non-goal"
    assert wsl["blocking_finding_ids"] == []
    assert "unverified-no-actual-host-supplied" in wsl["expected_result"]


def test_every_closure_evidence_and_focused_check_is_retained() -> None:
    closure = _json(CLOSURE)

    references = [record["review"] for record in closure["guide_reviews"]]
    references.extend(
        evidence for outcome in closure["outcomes"] for evidence in outcome["evidence"]
    )
    references.extend(closure["retained_linux_transcripts"])
    references.extend(closure["environment_handoff"].values())
    references.extend(closure["focused_checks"])
    for reference in references:
        if not isinstance(reference, str):
            continue
        assert (ROOT / reference).exists(), reference


def test_screenshot_all_settings_and_navigation_claims_match_accepted_sources() -> None:
    matrix = _json(MATRIX)
    visual = _json(VISUAL_QA)
    audit = _json(TARGET_AUDIT)
    target_map = _json(TARGET_MAP)
    outcomes = _outcomes()

    assert len(matrix["matrix"]) == visual["coverage"]["rows_reviewed"] == 36
    assert visual["status"] == "accepted"
    assert visual["release_ready"] is True
    assert audit["status"] == target_map["status"] == "accepted"
    assert audit["summary"]["policy_linked_count"] == 120
    assert audit["summary"]["known_preference_linked_count"] == 62
    assert target_map["policy_targets"]["target_pattern"] == "policy:{exact_policy_id}"
    assert target_map["known_preference_targets"]["target_pattern"] == (
        "known-preference:{exact.preference.id}"
    )
    assert "independent sidebar scrolling" in outcomes["single-hierarchical-navigation"][
        "result"
    ]


def test_live_evidence_keeps_linux_passes_and_conditional_wsl_non_claims() -> None:
    closure = _json(CLOSURE)
    live = _json(LIVE_CLOSURE)
    outcomes = _outcomes()

    assert live["status"] == "accepted"
    assert live["decision"]["mandatory_linux_pass_count"] == 5
    assert len(closure["retained_linux_transcripts"]) == 5
    assert all(
        target["result_evidence"]["completion"] == "complete"
        for target in live["linux_targets"]
    )
    assert outcomes["windows-wsl-conditional-validation"]["disposition"] == "deferred-non-goal"
    assert all(
        outcome["status"] == "unverified-no-actual-host-supplied"
        and outcome["validation_claimed"] is False
        and outcome["release_blocking"] is False
        for outcome in live["conditional_wsl_outcomes"]
    )
    assert closure["environment_handoff"] == {
        "manifest": "documentation/evidence/live-source-install/0.9.1/m11-13-validation-environment-handoff-20260715/run-manifest.json",
        "inventory": "documentation/evidence/live-source-install/0.9.1/m11-13-validation-environment-handoff-20260715/retained-inventory.json",
        "docker_engine_retained": True,
        "clean_images_retained": 5,
        "stopped_containers_retained": 13,
        "network_retained": 1,
        "deletion_performed": False,
    }


def test_release_contract_closes_outcomes_but_not_remaining_release_work() -> None:
    closure = _json(CLOSURE)
    contract = RELEASE_CONTRACT.read_text(encoding="utf-8")
    gate_rows = {
        line.split("|")[1].strip(" `"): line
        for line in contract.splitlines()
        if line.startswith("| `DOC091-G")
    }

    for number in range(4, 13):
        assert gate_rows[f"DOC091-G{number:02d}"].rstrip().endswith("| Closed |")
    assert gate_rows["DOC091-G13"].rstrip().endswith("| Closed |")
    assert gate_rows["DOC091-G14"].rstrip().endswith("| Open |")
    assert closure["release_readiness"]["documentation_outcomes_ready"] is True
    assert closure["release_readiness"][
        "implementation_and_maintained_documentation_milestones_verified"
    ] is True
    assert closure["release_readiness"]["overall_bpm_0_9_1_release_ready_claimed"] is False
    assert closure["release_readiness"]["remaining_required_work"] == [
        "BPM091-M13-10 reviewed commit and M13-11 maintainer-run push handoff",
    ]
    assert closure["verification"]["m13_07_milestone_handoff"] == "pass-45"
    assert closure["verification"]["m13_09_release_procedures"] == (
        "pass-754-with-4-deselected"
    )


def test_release_contract_links_completed_m10_m11_and_m12_evidence() -> None:
    contract = RELEASE_CONTRACT.read_text(encoding="utf-8")
    references = (
        "../../documentation/config/documentation-navigation-locale-completion-audit-0.9.1.json",
        "api-integration-rehome-audit-0.9.0.json",
        "linux-source-install-validation-0.9.1.json",
        "../../documentation/evidence/live-source-install/0.9.1/m11-14-evidence-closure-20260715/closure.json",
        "../../documentation/evidence/live-source-install/0.9.1/m11-13-validation-environment-handoff-20260715/retained-inventory.json",
        "../../documentation/evidence/live-source-install/0.9.1/m11-11-windows10-wsl-20260715/run-manifest.json",
        "../../documentation/evidence/live-source-install/0.9.1/m11-12-windows11-wsl-20260715/run-manifest.json",
        "../../README.md",
        "../../documentation/runbooks/README.md",
        "../docs-index.md",
        "documentation-sufficiency-closure-0.9.1.json",
    )

    assert "## M13-07 Maintained Milestone Handoff" in contract
    for milestone in ("M10", "M11", "M12"):
        assert f"| `{milestone}` |" in contract
    for reference in references:
        assert f"]({reference})" in contract
        assert (RELEASE_CONTRACT.parent / reference).resolve().is_file(), reference
    assert "Closed within recorded Linux-userspace and conditional-WSL boundaries" in contract
    assert "M13-10 and M13-11 remain required" in contract


def test_remaining_non_goals_preserve_product_and_platform_boundaries() -> None:
    text = " ".join(_json(CLOSURE)["remaining_non_goals"])

    for required in (
        "minimal User Guide matrix",
        "actual host",
        "Native-host Linux",
        "production hardening",
        "AI-assisted runtime documentation search",
    ):
        assert required in text
