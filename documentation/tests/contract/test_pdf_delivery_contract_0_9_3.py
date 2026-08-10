"""Contract guard for the BPM 0.9.4 PDF delivery promotion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "documentation/config/pdf-delivery-contract-0.9.3.json"
DELIVERY_TOOL = ROOT / "documentation/tools/deliver_pdfs.py"
MAKEFILE = ROOT / "Makefile"

pytestmark = pytest.mark.docs_contract


def test_m14_09_contract_requires_a_versioned_atomic_pdf_delivery() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["contract_id"] == "bpm-pdf-delivery-0.9.4"
    assert contract["backlog_item"] == "BPM094-M11-05"
    assert contract["target_bpm_version"] == "0.9.4"
    assert contract["candidate_root"] == "documentation/build/pdf"
    assert contract["delivery_root"] == "distributions/documentation"
    assert contract["delivery_directory"] == "{bpm_version}"
    assert len(contract["delivery_paths"]) == 5
    assert "PDF SHA-256" in contract["integrity"]["candidate_provenance"]
    assert "never contains a self-checksum" in contract["integrity"]["checksums"]
    assert "another version" in contract["promotion"]["scope"]
    assert contract["operator_commands"]["promote"] == "make docs-pdf-deliver"
    assert contract["operator_commands"]["verify_delivery"] == "make docs-pdf-delivery-verify"


def test_delivery_tool_and_makefile_expose_only_explicit_promotion_operations() -> None:
    tool = DELIVERY_TOOL.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert "def promote_delivery" in tool
    assert "def validate_delivery_tree" in tool
    assert "atomically promote verified release directory" in tool
    assert "docs-pdf-deliver:" in makefile
    assert "docs-pdf-delivery-verify:" in makefile
