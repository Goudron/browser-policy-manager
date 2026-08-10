from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RECONCILIATION = (
    ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)
COMMAND_CONTRACT = ROOT / "documentation/config/linux-source-install-command-contract-0.9.1.json"
HISTORICAL_REPORT = ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
CLOSURE = (
    ROOT / "documentation/evidence/live-source-install/0.9.1/"
    "m11-14-evidence-closure-20260715/closure.json"
)
DITA_ROOT = ROOT / "documentation/src/dita/en/admin"

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_editorial_reconciliation_keeps_historical_091_evidence_immutable() -> None:
    reconciliation = _json(RECONCILIATION)
    evidence = reconciliation["historical_evidence"]

    assert reconciliation["schema_version"] == 1
    assert reconciliation["backlog_item"] == "BPM092-M11-08"
    assert reconciliation["target_bpm_version"] == "0.9.2"
    assert reconciliation["status"] == "accepted-editorial-boundary"
    assert evidence["command_contract"] == COMMAND_CONTRACT.relative_to(ROOT).as_posix()
    assert evidence["validation_report"] == HISTORICAL_REPORT.relative_to(ROOT).as_posix()
    assert evidence["evidence_closure"] == CLOSURE.relative_to(ROOT).as_posix()
    assert evidence["immutable"] is True
    assert _json(HISTORICAL_REPORT)["target_bpm_version"] == evidence["target_bpm_version"]
    assert _json(CLOSURE)["target_bpm_version"] == evidence["target_bpm_version"]


def test_current_compact_topics_keep_the_user_facing_source_install_path() -> None:
    reconciliation = _json(RECONCILIATION)
    current = reconciliation["current_source_contract"]
    historical_targets = {
        target["id"]: target["topic_id"] for target in _json(COMMAND_CONTRACT)["targets"]
    }

    assert reconciliation["editorial_policy"]["audit"].endswith(
        "documentation-audience-status-leakage-audit-0.9.2.md"
    )
    assert reconciliation["editorial_policy"]["findings"] == [
        "A07",
        "A08",
        "A09",
        "A10",
        "A11",
        "A12",
        "A15",
    ]
    assert [target["id"] for target in current["targets"]] == list(historical_targets)

    for target in current["targets"]:
        assert target["topic_id"] == historical_targets[target["id"]]
        source = (DITA_ROOT / f"{target['topic_id']}.dita").read_text(encoding="utf-8")
        root = ET.fromstring(source)
        blocks = root.findall(".//codeblock")

        assert len(blocks) == target["expected_codeblock_count"]
        assert all(token in source for token in current["required_tokens"])
        assert all(command not in source for command in current["removed_maintainer_commands"])
        assert root.find("./taskbody/result") is not None
        assert root.find("./taskbody/postreq") is not None
