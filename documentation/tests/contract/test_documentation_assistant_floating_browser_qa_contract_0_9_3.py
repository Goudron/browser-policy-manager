from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = (
    DOCUMENTATION_ROOT
    / "config/documentation-assistant-floating-browser-qa-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m12b_07_freezes_the_six_locale_browser_release_matrix() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M12B-07"
    assert contract["status"] == "implemented-browser-release-qa"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["browser_evidence"]["runner"] == "pytest -m browser_ui"
    assert contract["viewport_and_theme_matrix"]["themes"] == ["light", "dark"]
    assert contract["state_matrix"]["all_locales"] == [
        "collapsed", "ready", "external switch off"
    ]
    assert contract["safety_and_independence"]["ordinary_search_changed"] is False
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]


def test_m12b_07_browser_evidence_covers_persistence_failures_and_safe_boundaries() -> None:
    source = (
        DOCUMENTATION_ROOT / "tests/browser/test_documentation_portal_browser_smoke.py"
    ).read_text(encoding="utf-8")

    for required in (
        "test_documentation_floating_assistant_release_qa_matrix_for_all_locales",
        "test_documentation_floating_assistant_install_failure_stays_locale_safe",
        "DOCUMENTATION_LOCALES",
        "assistant_external_sources",
        "Grounded en BPM answer.",
        "Long answer 7:",
        "artifact_hash_mismatch",
        "Content Security Policy",
        "__assistantQaRejectChat",
        "__assistantQaFailureCalls",
    ):
        assert required in source

    for forbidden in ("brave.com", "https://api.search.brave.com", "localStorage", "innerHTML"):
        assert forbidden not in source
