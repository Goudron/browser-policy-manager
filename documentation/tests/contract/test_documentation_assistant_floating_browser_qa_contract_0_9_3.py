from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = (
    DOCUMENTATION_ROOT / "config/documentation-assistant-floating-browser-qa-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m12b_07_browser_evidence_covers_persistence_failures_and_safe_boundaries() -> None:
    contract = _contract()
    source = (
        DOCUMENTATION_ROOT / "tests/browser/test_documentation_portal_browser_smoke.py"
    ).read_text(encoding="utf-8")

    assert contract["safety_and_independence"]["external_sources_default"] == (
        "off until the reader explicitly changes it"
    )
    for required in (
        "test_documentation_floating_assistant_release_qa_matrix_for_all_locales",
        "test_documentation_floating_assistant_install_failure_stays_locale_safe",
        "test_documentation_floating_assistant_ships_local_only_without_external_sources_control",
        "test_documentation_header_preferences_persist_between_bpm_and_portal",
        "DOCUMENTATION_LOCALES",
        "Grounded en BPM answer.",
        "Long answer 7:",
        "artifact_hash_mismatch",
        "Content Security Policy",
        "__assistantQaRejectChat",
        "__assistantQaFailureCalls",
        "data-assistant-web-control",
        "data-assistant-web-toggle",
        '"web_mode":"local_only"',
    ):
        assert required in source

    persistence_test_name = "test_documentation_header_preferences_persist_between_bpm_and_portal"
    persistence_test = source.split(f"def {persistence_test_name}", maxsplit=1)[1].split(
        "\ndef ", maxsplit=1
    )[0]
    allowed_theme_read = "window.localStorage.getItem('bpm-theme-mode')"
    assert persistence_test.count(allowed_theme_read) == 1

    source_without_allowed_theme_read = source.replace(allowed_theme_read, "")
    for forbidden in ("brave.com", "https://api.search.brave.com", "localStorage", "innerHTML"):
        assert forbidden not in source_without_allowed_theme_read
