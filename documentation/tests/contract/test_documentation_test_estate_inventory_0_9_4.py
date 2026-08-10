"""Fail closed on complete, non-overlapping BPM094-M11A-01 test-layer ownership."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
INVENTORY_PATH = ROOT / "documentation/config/documentation-test-estate-inventory-0.9.4.json"
LAYERS = {"fast_edit_time", "release_gate", "scheduled_audit", "remove_replace"}
COUPLINGS = {
    "semantic",
    "structural",
    "fixture",
    "literal_text",
    "snapshot",
    "obsolete_evidence",
    "binary_artifact",
    "runtime_boundary",
}

pytestmark = pytest.mark.docs_contract


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _test_files(inventory: dict[str, object]) -> list[str]:
    return sorted(
        path.relative_to(ROOT).as_posix()
        for test_root in inventory["maintained_test_roots"]
        for path in (ROOT / test_root).rglob("test_*.py")
    )


def _matches(path: str, classification: dict[str, object]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in classification["include"]) and not any(
        fnmatch.fnmatch(path, pattern) for pattern in classification["exclude"]
    )


def test_test_estate_inventory_has_complete_owned_non_overlapping_classification() -> None:
    inventory = _inventory()

    assert inventory["schema_version"] == 1
    assert inventory["inventory_id"] == "bpm-0.9.4-documentation-test-estate"
    assert inventory["backlog_item"] == "BPM094-M11A-01"
    assert inventory["target_bpm_version"] == "0.9.4"
    assert inventory["status"] == "accepted-for-layer-rationalization"
    assert set(inventory["layers"]) == LAYERS
    assert set(inventory["coupling_types"]) == COUPLINGS

    classifications = inventory["classifications"]
    assert classifications
    assert len({entry["id"] for entry in classifications}) == len(classifications)
    for entry in classifications:
        assert entry["include"], entry["id"]
        assert entry["owner"], entry["id"]
        assert entry["asserted_risks"], entry["id"]
        assert entry["execution_cost"], entry["id"]
        assert entry["coupling"], entry["id"]
        assert set(entry["coupling"]) <= COUPLINGS, entry["id"]
        assert entry["layer"] in LAYERS, entry["id"]
        assert entry["rationale"], entry["id"]
        if entry["layer"] == "remove_replace":
            assert entry["replacement"], entry["id"]

    files = _test_files(inventory)
    assert files
    unmatched = []
    overlapping = []
    for path in files:
        matches = [entry["id"] for entry in classifications if _matches(path, entry)]
        if not matches:
            unmatched.append(path)
        if len(matches) > 1:
            overlapping.append((path, matches))
    assert unmatched == []
    assert overlapping == []


def test_false_blockers_have_root_cause_and_non_destructive_disposition() -> None:
    inventory = _inventory()
    blockers = inventory["m11_false_blockers"]

    assert {entry["id"] for entry in blockers} == {
        "M11-FB-001",
        "M11-FB-002",
        "M11-FB-003",
        "M11-FB-004",
        "M11-FB-005",
        "M11-FB-006",
    }
    for blocker in blockers:
        assert blocker["source_record"]
        assert blocker["affected_tests"]
        assert blocker["root_cause_class"] in {
            "literal_text",
            "snapshot",
            "fixture_and_obsolete_evidence",
            "obsolete_evidence",
        }
        assert blocker["observed_false_block"]
        assert blocker["disposition"]
        assert blocker["replacement_required"] is True
        assert blocker["authority_record"]
        assert all((ROOT / path).exists() for path in blocker["current_sources"])
        assert blocker["replacement_status"] in {
            "completed",
            "deferred-to-BPM094-M11A-04",
        }
        if blocker["replacement_status"] == "completed":
            assert len(blocker["focused_regressions"]) == 2
        else:
            assert blocker["id"] == "M11-FB-005"
            assert blocker["focused_regressions"] == []

    causes = {entry["root_cause_class"] for entry in blockers}
    assert {
        "literal_text",
        "snapshot",
        "fixture_and_obsolete_evidence",
        "obsolete_evidence",
    } <= causes


def test_critical_risks_remain_in_or_are_covered_by_release_layer() -> None:
    inventory = _inventory()
    classifications = {entry["id"]: entry for entry in inventory["classifications"]}
    guards = inventory["critical_risk_guards"]

    for risk in ("structural", "localization", "pdf", "security", "delivery"):
        guard_ids = [item.strip() for item in guards[risk].split(",")]
        assert guard_ids
        assert all(guard_id in classifications for guard_id in guard_ids)
        assert any(classifications[guard_id]["layer"] == "release_gate" for guard_id in guard_ids)
    assert "may not move a critical check out of release_gate" in guards["rule"]
