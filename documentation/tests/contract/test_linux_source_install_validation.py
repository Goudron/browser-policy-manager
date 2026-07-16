from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "documentation"
CONTRACT = DOCS / "config/linux-source-install-command-contract-0.9.1.json"
REPORT = ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
DITA = DOCS / "src/dita/en/admin"

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source(topic_id: str) -> str:
    return (DITA / f"{topic_id}.dita").read_text(encoding="utf-8")


def test_validation_report_records_m11_09_scope_and_honest_release_result() -> None:
    report = _json(REPORT)
    contract = _json(CONTRACT)

    assert report["schema_version"] == 2
    assert report["backlog_item"] == "BPM091-M11-09"
    assert report["target_bpm_version"] == "0.9.1"
    assert report["validation_ref"] == "ff8271e577169c9063291087fb5f244b9fdb9139"
    assert report["status"] == "accepted-with-oci-boundary"
    assert report["validation_date"] == "2026-07-15"
    assert contract["status"] == "authored-validation-attempted"
    assert contract["validation_report"] == "docs/architecture/linux-source-install-validation-0.9.1.json"
    assert report["summary"] == {
        "target_count": 5,
        "clean_userspace_container_pass_count": 5,
        "simulation_only_count": 0,
        "documented_command_correction_count": 1,
        "changed_command_clean_rerun_count": 1,
        "linux_userspace_release_ready": True,
        "native_clean_host_claimed": False,
        "result": (
            "All five documented Linux userspace source-install sequences passed in retained "
            "clean containers. This closes the Linux userspace evidence blocker without "
            "promoting OCI evidence to native clean-host evidence."
        ),
    }


def test_report_covers_every_frozen_target_once_with_required_evidence_fields() -> None:
    report = _json(REPORT)
    expected = [item["id"] for item in _json(CONTRACT)["targets"]]
    records = report["targets"]

    assert [item["target_id"] for item in records] == expected
    assert len(records) == len({item["target_id"] for item in records}) == 5
    for item in records:
        assert item["release"]
        assert item["disposition"].startswith("clean-userspace-container-pass")
        manifest_path = ROOT / item["manifest"]
        manifest = _json(manifest_path)
        attempt = next(
            attempt
            for attempt in manifest["attempts"]
            if attempt["attempt"] == item["accepted_attempt"]
        )
        assert manifest["status"] == "accepted"
        assert attempt["accepted_disposition"] == "accepted-clean-source-install-pass"
        assert attempt["transcript_sha256"]["events.jsonl"] == item["accepted_events_sha256"]
        assert item["accepted_transcript_artifact"].endswith(
            f"[attempt={item['accepted_attempt']}].transcript_sha256.events.jsonl"
        )
        assert item["validated_source_sha256"] == manifest["target"]["source_sha256"]
        assert item["reconciled_source_sha256"] == hashlib.sha256(
            _source(next(
                target["topic_id"]
                for target in _json(CONTRACT)["targets"]
                if target["id"] == item["target_id"]
            )).encode("utf-8")
        ).hexdigest()


def test_every_english_command_block_is_bash_syntax_valid() -> None:
    for target in _json(CONTRACT)["targets"]:
        root = ET.fromstring(_source(target["topic_id"]))
        blocks = ["".join(node.itertext()) for node in root.findall(".//codeblock")]
        assert len(blocks) >= 6
        for index, block in enumerate(blocks):
            result = subprocess.run(
                ["bash", "-n"],
                input=block,
                text=True,
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, (target["id"], index, result.stderr)


def test_required_install_stages_remain_in_executable_order() -> None:
    ordered_tokens = (
        "git clone",
        "git checkout --detach",
        "-m venv .venv",
        'pip install -e ".[dev]"',
        "alembic upgrade head",
        "make setup-docs-toolchain",
        "make docs-validate",
        "make docs-build",
        "make dev",
        "/health",
        "/health/ready",
        "/profiles",
    )
    for target in _json(CONTRACT)["targets"]:
        source = _source(target["topic_id"])
        positions = [source.index(token) for token in ordered_tokens]
        assert positions == sorted(positions), target["id"]


def test_historical_m6_06_blocker_is_preserved_but_superseded() -> None:
    report = _json(REPORT)
    baseline = report["historical_baseline"]

    assert baseline["backlog_item"] == "BPM091-M6-06"
    assert baseline["status"] == "accepted-with-release-blocker"
    assert baseline["partial_hands_on_count"] == 1
    assert baseline["simulation_only_count"] == 4
    assert baseline["clean_target_pass_count"] == 0
    assert "superseded" in baseline["note"]


def test_only_documented_command_correction_links_failure_and_clean_rerun() -> None:
    report = _json(REPORT)
    corrected = [target for target in report["targets"] if target["procedure_corrections"]]

    assert [target["target_id"] for target in corrected] == ["manjaro-stable-2026-06-26"]
    manjaro = corrected[0]
    assert "--noconfirm" in manjaro["procedure_corrections"][0]["command"]
    assert manjaro["diagnostic_transcript_artifact"].endswith(
        "[attempt=1].transcript_sha256.events.jsonl"
    )
    assert manjaro["diagnostic_events_sha256"] == (
        "7a57b529f47985e0a247f9736a19760f4e6890bd3f68540319166fe1609d5eaa"
    )
    assert manjaro["procedure_corrections"][0]["clean_rerun"] == (
        "attempt 2 passed all 37 documented commands"
    )
    assert report["closed_release_blocker"]["closed_by"] == "BPM091-M11-09"
    parity = report["locale_parity_reconciliation"]
    assert parity["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert parity["standalone_command_source_locale"] == "ru"
    assert "line-for-line identical" in parity["rerun_disposition"]


def test_clean_container_evidence_is_not_promoted_to_native_host_evidence() -> None:
    report = _json(REPORT)
    boundaries = " ".join(report["remaining_boundaries"]).casefold()

    assert report["summary"]["native_clean_host_claimed"] is False
    assert "share the host kernel" in boundaries
    assert "native boot" in boundaries
    assert "actual windows hosts" in boundaries
    assert "not clean native-host evidence" in report["method"]["evidence_rule"]


def test_validation_keeps_production_claims_out_of_install_topics_and_report() -> None:
    forbidden = (
        "production-ready",
        "systemd service is provided",
        "reverse proxy is supported",
        "HA is supported",
        "managed backups are provided",
    )
    corpus = REPORT.read_text(encoding="utf-8") + "\n" + "\n".join(
        _source(item["topic_id"]) for item in _json(CONTRACT)["targets"]
    )
    folded = corpus.casefold()
    assert all(claim.casefold() not in folded for claim in forbidden)
