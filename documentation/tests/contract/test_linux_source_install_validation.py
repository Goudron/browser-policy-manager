from __future__ import annotations

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


def test_validation_report_records_m6_06_scope_and_honest_release_result() -> None:
    report = _json(REPORT)
    contract = _json(CONTRACT)

    assert report["backlog_item"] == "BPM091-M6-06"
    assert report["target_bpm_version"] == "0.9.1"
    assert report["status"] == "accepted-with-release-blocker"
    assert report["validation_date"] == "2026-07-11"
    assert contract["status"] == "authored-validation-attempted"
    assert contract["validation_report"] == "docs/architecture/linux-source-install-validation-0.9.1.json"
    assert report["summary"] == {
        "target_count": 5,
        "partial_hands_on_count": 1,
        "simulation_only_count": 4,
        "syntax_pass_count": 5,
        "clean_target_pass_count": 0,
        "release_ready": False,
        "result": (
            "No command defect was found. Ubuntu runtime behavior and shared CPython integrity "
            "passed, but clean-target execution evidence remains insufficient for release."
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
        assert item["shell"] == "bash"
        assert item["evidence_type"]
        assert item["disposition"]
        if item["target_id"] != "ubuntu-26-04":
            assert item["official_evidence"]
            assert item["simulation"]
            assert item["unverified"]


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


def test_observed_ubuntu_and_python_integrity_evidence_is_complete() -> None:
    report = _json(REPORT)
    ubuntu = report["targets"][0]
    observed = ubuntu["observed"]

    assert ubuntu["target_id"] == "ubuntu-26-04"
    assert ubuntu["disposition"] == "partial-hands-on-pass-not-clean-host"
    for field in (
        "release_assertion",
        "python",
        "editable_install",
        "migration",
        "documentation",
        "startup_log",
        "health",
        "readiness",
        "profiles",
        "stop",
    ):
        assert observed[field].startswith("pass:"), field
    assert report["shared_evidence"]["observed_sha256_result"] == "pass"
    assert report["shared_evidence"]["documented_sha256"] == _json(CONTRACT)["python_source"]["sha256"]
    assert len(ubuntu["skipped"]) == 3


def test_unavailable_isolation_and_clean_target_blocker_cannot_be_hidden() -> None:
    report = _json(REPORT)
    isolation = report["method"]["isolation_probe"]
    blocker = report["release_blocker"]

    assert all(isolation[name] == "unavailable" for name in ("docker", "podman", "distrobox", "proot"))
    assert "unshare" in isolation["user_namespace"]
    assert blocker["severity"] == "release-blocker"
    assert blocker["affected_targets"] == [item["id"] for item in _json(CONTRACT)["targets"]]
    assert report["summary"]["release_ready"] is False


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
