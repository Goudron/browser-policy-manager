"""Ownership and path guard for the future BPM documentation delivery tree."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/future-distribution-documentation-layout-0.9.3.json"
DELIVERY_ROOT = ROOT / "distributions/documentation"

pytestmark = pytest.mark.docs_contract


def test_m14_07_layout_keeps_the_pdf_delivery_scope_safe_after_promotion() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["backlog_item"] == "BPM093-M14-07"
    assert contract["target_bpm_version"] == "0.9.5"
    assert contract["status"] == "implemented-and-delivered"
    assert contract["delivery_root"] == "distributions/documentation"
    assert contract["release_directory"] == "{bpm_version}"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert [guide["id"] for guide in contract["guides"]] == [
        "user-guide",
        "administrator-guide",
    ]
    assert len(contract["release_contents"]) == 5
    assert set(contract["forbidden_content"]) >= {
        "local-models",
        "embeddings",
        "rag-indexes",
        "caches",
        "logs",
        "reports",
        "credentials",
        "secrets",
        "source-dita",
        "html-site",
    }
    assert "atomically" in contract["ownership"]["promotion"]
    assert "temporary" in contract["integrity"]["rebuild"]

    assert DELIVERY_ROOT.is_dir()
    assert (ROOT / "distributions/README.md").is_file()
    assert (DELIVERY_ROOT / "README.md").is_file()
    version_directories = [
        path for path in DELIVERY_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")
    ]
    # The current handoff output is intentionally ignored: CI proves the
    # generator and atomic-delivery behaviour using its compact fixtures, not
    # an incidental local PDF handoff left in a maintainer worktree. Only
    # release directories deliberately retained in Git belong to this tree;
    # the active handoff target may also be present locally.
    version_names = {path.name for path in version_directories}
    assert set(contract["tracked_release_versions"]) <= version_names
    assert contract["preserved_handoff_versions"] == ["0.9.4"]
    assert contract["handoff_target_version"] == contract["target_bpm_version"]
    assert contract["target_bpm_version"] not in contract["tracked_release_versions"]
    assert version_names - set(contract["tracked_release_versions"]) <= {
        *contract["preserved_handoff_versions"],
        contract["handoff_target_version"],
    }
