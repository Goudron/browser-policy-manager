from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GATE_PATH = ROOT / "documentation/config/documentation-editorial-release-gate-0.9.2.json"
SCRIPT_PATH = ROOT / "documentation/tools/validate_editorial_release_gate.py"
MAKEFILE = ROOT / "Makefile"
REQUIRED_LOCALES = {"en", "ru", "de", "zh-CN", "fr", "es-ES"}

pytestmark = pytest.mark.docs_contract


def _load_script_module():
    spec = importlib.util.spec_from_file_location("editorial_release_gate", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gate() -> dict[str, object]:
    return json.loads(GATE_PATH.read_text(encoding="utf-8"))


def test_editorial_release_gate_is_release_blocking_and_covers_all_locales() -> None:
    gate = _gate()

    assert gate["gate_id"] == "bpm-0.9.2-documentation-editorial-release-gate"
    assert gate["target_bpm_version"] == "0.9.2"
    assert gate["backlog_item"] == "BPM092-M10-11"
    assert gate["release_blocking"] is True
    assert gate["release_command"] == "make docs-release-check"
    assert set(gate["locales"]) == REQUIRED_LOCALES


def test_editorial_release_gate_records_existing_review_evidence_and_drift_contracts() -> None:
    gate = _gate()

    assert gate["automated_regression_contracts"] == [
        "documentation/tests/contract/test_public_audience_language.py",
        "documentation/tests/contract/test_locale_anti_anglicism_guard.py",
        "documentation/tests/contract/test_localized_heading_style.py",
    ]
    for contract_path in gate["automated_regression_contracts"]:
        assert (ROOT / contract_path).is_file()
    for locale, record in gate["locales"].items():
        assert record["review_state"] == "accepted", locale
        review = ROOT / record["review_record"]
        assert review.is_file(), locale
        assert record["record_acceptance_marker"] in review.read_text(encoding="utf-8"), locale


def test_accepted_manual_reviews_clear_the_release_gate() -> None:
    gate = _gate()
    module = _load_script_module()

    blockers = module.release_blockers(gate)

    assert blockers == []


def test_release_command_runs_editorial_gate_before_contract_suite() -> None:
    source = MAKEFILE.read_text(encoding="utf-8")
    target = source.split("docs-release-check:\n", 1)[1].split("\ndocs-validate:", 1)[0]

    assert target.index("validate_editorial_release_gate.py") < target.index("-m docs_contract")
