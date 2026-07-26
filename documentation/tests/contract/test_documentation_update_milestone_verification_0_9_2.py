from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "docs/architecture/documentation-update-milestone-verification-0.9.2.md"
RELEASE_CONTRACT = ROOT / "docs/architecture/product-documentation-release-contract-0.9.2.md"
DRIFT_PROCEDURES = ROOT / "docs/architecture/maintained-drift-procedures-verification-0.9.2.md"

pytestmark = pytest.mark.docs_contract


def test_documentation_update_record_links_m11_m12_evidence_and_commands() -> None:
    record = RECORD.read_text(encoding="utf-8")

    for item in (
        "BPM092-M11-01",
        "BPM092-M11-02",
        "BPM092-M11-03",
        "BPM092-M11-04",
        "BPM092-M11-05",
        "BPM092-M11-06",
        "BPM092-M11-07",
        "BPM092-M11-08",
        "BPM092-M11-09",
        "BPM092-M12-05",
        "BPM092-M12-06",
    ):
        assert f"`{item}`" in record

    for path in (
        "compact-ui-user-documentation-review-0.9.2.md",
        "context-help-gap-review-0.9.2.md",
        "compact-ui-screenshot-refresh-0.9.2.md",
        "firefox-153-dual-esr-schema-contract-0.9.2.md",
    ):
        assert path in record

    for command in ("make docs-release-check", "make docs-install-dev", "make test-docs-browser"):
        assert f"`{command}`" in record


def test_release_contract_closes_documentation_gate_with_the_verification_record() -> None:
    contract = RELEASE_CONTRACT.read_text(encoding="utf-8")
    gate = next(line for line in contract.splitlines() if line.startswith("| `BPM092-G10`"))

    assert "documentation-update-milestone-verification-0.9.2.md" in gate
    assert gate.rstrip().endswith("| Closed |")


def test_drift_procedures_cover_092_change_families_and_release_handoff() -> None:
    record = DRIFT_PROCEDURES.read_text(encoding="utf-8")
    contract = RELEASE_CONTRACT.read_text(encoding="utf-8")

    for procedure in (
        "Firefox schema update runbook",
        "CIS Firefox update runbook",
        "Locale update runbook",
        "Links, manifest, review, and publishing",
        "Administrator/DevOps",
        "Release contract",
    ):
        assert procedure in record
    for requirement in (
        "Firefox Release 153",
        "Firefox ESR 153.0",
        "Firefox ESR 140.13",
        "make docs-install-dev",
        "make dev",
    ):
        assert requirement in record
    assert "maintained-drift-procedures-verification-0.9.2.md" in contract
