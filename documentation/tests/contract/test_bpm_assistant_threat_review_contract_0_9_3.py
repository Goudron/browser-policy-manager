from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-assistant-threat-review-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


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
        threat for threats in contract["release_blocker_owners"].values() for threat in threats
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
