from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-assistant-threat-review-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_07_pins_reviewed_boundaries_and_classifies_every_m2_threat() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M8-07"
    assert contract["status"] == "completed-current-surface-with-explicit-release-blockers"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    dispositions = {item["id"]: item["disposition"] for item in contract["threat_dispositions"]}
    assert set(dispositions) == {f"AI093-T{number:02d}" for number in range(1, 15)}
    assert {item for item, status in dispositions.items() if status == "closed"} == {
        "AI093-T01",
        "AI093-T03",
        "AI093-T04",
        "AI093-T08",
        "AI093-T09",
        "AI093-T12",
    }
    assert set(dispositions.values()) == {"closed", "release-blocker"}


def test_m8_07_has_no_security_or_nondeterminism_exception_and_owns_every_blocker() -> None:
    contract = _contract()

    summary = contract["summary"]
    assert summary == {
        "threats_total": 14,
        "closed": 6,
        "release_blockers": 8,
        "accepted_with_compensating_controls": 0,
        "model_nondeterminism_exceptions": 0,
        "m8_current_surface_exit_allowed": True,
        "product_release_allowed": False,
    }
    owned = {
        threat
        for threats in contract["release_blocker_owners"].values()
        for threat in threats
    }
    blockers = {
        item["id"]
        for item in contract["threat_dispositions"]
        if item["disposition"] == "release-blocker"
    }
    assert owned == blockers
    assert set(contract["release_blocker_owners"]) == {"M9", "M10", "M11", "M13"}
    assert all((ROOT / path).is_file() for path in contract["regression_suite"])
    assert {finding["id"] for finding in contract["closed_findings"]} == {
        "M8R-01",
        "M8R-02",
    }
