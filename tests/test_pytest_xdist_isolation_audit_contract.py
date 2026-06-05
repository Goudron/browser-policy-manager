from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "architecture" / "pytest-xdist-isolation-audit.md"
READINESS_PATH = REPO_ROOT / "docs" / "architecture" / "pytest-xdist-readiness.md"
BACKLOG_PATH = REPO_ROOT / "docs" / "bpm_0_8_5_refactoring_backlog_2026-06-01.md"
DOCS_INDEX_PATH = REPO_ROOT / "docs" / "docs-index.md"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_xdist_audit_records_m8_01_scope_and_decision():
    audit = _read(AUDIT_PATH)

    required_phrases = {
        "Backlog item: `BPM085-M8-01`",
        "Do not enable `pytest-xdist` for mandatory BPM 0.8.5 CI.",
        "database and session isolation",
        "FastAPI app and dependency override isolation",
        "process-local caches and mutable module state",
        "temporary files, ports, browser profiles, screenshots, and local artifacts",
    }
    for phrase in required_phrases:
        assert phrase in audit


def test_xdist_audit_maps_required_blocker_categories():
    audit = _read(AUDIT_PATH)

    required_rows = {
        "| Dependency availability |",
        "| DB engine lifecycle |",
        "| DB URL handling |",
        "| FastAPI app state |",
        "| Async client fixture |",
        "| Settings and schema caches |",
        "| Mutable module state |",
        "| Ordered tests |",
        "| Temporary files |",
        "| Local ports |",
        "| Firefox live runtime |",
        "| Artifacts/screenshots |",
    }
    for row in required_rows:
        assert row in audit

    assert "Extra high" in audit
    assert "write `distribution/policies.json` into the shared Firefox install root" in audit


def test_xdist_audit_limits_first_pilot_to_pure_unit_tool_scope():
    audit = _read(AUDIT_PATH)

    assert (
        'pytest -q -m "unit and not api and not contract and not docs_contract and not '
        'ui_contract and not slow and not browser_ui and not firefox_live and not '
        'firefox_live_amo" -n auto'
    ) in audit

    excluded_markers = {
        "`api`",
        "`contract`",
        "`docs_contract`",
        "`ui_contract`",
        "`slow`",
        "`browser_ui`",
        "`firefox_live`",
        "`firefox_live_amo`",
    }
    for marker in excluded_markers:
        assert marker in audit


def test_xdist_audit_records_m8_02_database_harness_result():
    audit = _read(AUDIT_PATH)

    required_phrases = {
        "## M8-02 Implementation Result",
        "`tests/db_harness.py`",
        "`PYTEST_XDIST_WORKER`",
        "guards against `./data/bpm.db`",
        "`tests/test_db_harness_unit.py`",
        "`tests/test_pytest_db_isolation_contract.py`",
        "At that",
        "`BPM085-M8-03`",
    }
    for phrase in required_phrases:
        assert phrase in audit


def test_xdist_audit_records_m8_03_app_and_cache_harness_result():
    audit = _read(AUDIT_PATH)

    required_phrases = {
        "## M8-03 Implementation Result",
        "`tests/app_harness.py`",
        "fresh test app instances for new tests",
        "explicit legacy/custom apps",
        "`tests/cache_harness.py`",
        "`tests/test_app_harness_unit.py`",
        "`tests/test_cache_harness_unit.py`",
        "`tests/test_pytest_app_state_isolation_contract.py`",
        "does not approve API, contract, docs, UI, browser, or live Firefox tests",
    }
    for phrase in required_phrases:
        assert phrase in audit


def test_xdist_readiness_and_docs_index_point_to_audit():
    readiness = _read(READINESS_PATH)
    docs_index = _read(DOCS_INDEX_PATH)

    assert "docs/architecture/pytest-xdist-isolation-audit.md" in readiness
    assert "architecture/pytest-xdist-isolation-audit.md" in docs_index
    assert "Current pytest-xdist isolation blocker map for BPM 0.8.5." in docs_index


def test_m8_backlog_reflects_xdist_audit_corrections():
    backlog = _read(BACKLOG_PATH)

    expected_updates = {
        "per-test or per-worker `BPM_DATABASE_URL`",
        "workers never touch `./data/bpm.db`",
        "fresh app factories, dependency-override cleanup, and a cache-reset registry",
        "excluding `api`, `contract`, `docs_contract`, `ui_contract`, `slow`, browser, and live Firefox markers",
        "keep the xdist pilot opt-in for BPM 0.8.5",
    }
    for update in expected_updates:
        assert update in backlog


def test_xdist_is_available_only_for_opt_in_pilot():
    pyproject = _read(PYPROJECT_PATH)
    readiness = _read(READINESS_PATH)
    audit = _read(AUDIT_PATH)

    assert '"pytest-xdist>=3.8.0"' in pyproject
    assert "make test-unit-pilot" in readiness
    assert "make test-unit-xdist" in readiness
    assert "## M8-04 Implementation Result" in audit
    assert "manual `.github/workflows/xdist-pilot.yml` workflow" in audit
    assert "221 passed, 528 deselected" in readiness
    assert "49.71s" in audit
    assert "42.74s" in audit


def test_m8_05_records_final_opt_in_decision():
    readiness = _read(READINESS_PATH)
    audit = _read(AUDIT_PATH)
    backlog = _read(BACKLOG_PATH)

    assert "Status: final BPM 0.8.5 decision from `BPM085-M8-05`." in readiness
    assert "## M8-05 Decision Rationale" in readiness
    assert "## M8-05 Decision Result" in audit
    assert "No mandatory xdist job is" in audit
    assert "No default `-n auto` configuration is introduced." in audit
    assert "keep it opt-in for 0.8.5" in backlog
