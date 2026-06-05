from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"


def _makefile_source() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def _target_body(source: str, target: str) -> str:
    match = re.search(rf"^{re.escape(target)}:\n(?P<body>(?:\t.*\n)+)", source, re.M)
    assert match, f"Missing Makefile target: {target}"
    return match.group("body")


def test_makefile_declares_layered_test_targets():
    source = _makefile_source()

    for target in (
        "test-fast",
        "test-unit-pilot",
        "test-unit-xdist",
        "test-contract",
        "test-ui",
        "test-live",
        "test-release",
        "test-locale-contract",
        "test-firefox-schema-contract",
    ):
        assert target in source.splitlines()[0]
        assert _target_body(source, target)


def test_makefile_test_targets_use_named_marker_expressions():
    source = _makefile_source()

    expected_markers = {
        "TEST_FAST_MARKERS": "not slow and not browser_ui and not firefox_live and not firefox_live_amo",
        "TEST_UNIT_PILOT_MARKERS": "unit and not api and not contract and not docs_contract and not ui_contract and not slow and not browser_ui and not firefox_live and not firefox_live_amo",
        "TEST_CONTRACT_MARKERS": "contract and not browser_ui and not firefox_live and not firefox_live_amo",
        "TEST_UI_MARKERS": "ui_contract or browser_ui",
        "TEST_LIVE_MARKERS": "firefox_live or firefox_live_amo",
        "TEST_RELEASE_MARKERS": "not firefox_live and not firefox_live_amo",
    }
    for name, expression in expected_markers.items():
        assert f"{name} := {expression}" in source

    target_to_variable = {
        "test-fast": "TEST_FAST_MARKERS",
        "test-contract": "TEST_CONTRACT_MARKERS",
        "test-ui": "TEST_UI_MARKERS",
        "test-live": "TEST_LIVE_MARKERS",
        "test-release": "TEST_RELEASE_MARKERS",
    }
    for target, variable in target_to_variable.items():
        body = _target_body(source, target)
        assert "-o addopts= -q" in body
        assert f'$({variable})' in body


def test_makefile_declares_opt_in_xdist_pilot_targets():
    source = _makefile_source()
    serial_body = _target_body(source, "test-unit-pilot")
    xdist_body = _target_body(source, "test-unit-xdist")

    assert "XDIST_WORKERS ?= auto" in source
    assert "$(TEST_UNIT_PILOT_MARKERS)" in serial_body
    assert "$(TEST_UNIT_PILOT_MARKERS)" in xdist_body
    assert " -n " not in serial_body
    assert "-n $(XDIST_WORKERS)" in xdist_body


def test_legacy_firefox_live_target_delegates_to_live_marker_expression():
    body = _target_body(_makefile_source(), "test-firefox-live")

    assert "-o addopts= -q" in body
    assert "tests/live_firefox/test_policy_activation.py" in body
    assert "tests/live_firefox/test_policy_behavior.py" in body
    assert '-m "firefox_live"' in body
    assert "-rs" in body


def test_makefile_declares_firefox_live_amo_canary_target():
    source = _makefile_source()
    body = _target_body(source, "test-firefox-live-amo")

    assert "test-firefox-live-amo" in source.splitlines()[0]
    assert "tests/live_firefox/test_extension_settings_amo.py" in body
    assert '-m "firefox_live_amo"' in body
    assert "-rs" in body


def test_makefile_declares_locale_contract_runbook_target():
    body = _target_body(_makefile_source(), "test-locale-contract")

    expected_tests = {
        "tests/test_locale_catalogs.py",
        "tests/test_locale_visible_english_allowlists.py",
        "tests/test_ui_runtime_i18n_contract.py",
        "tests/test_ui_locale_glossary.py",
        "tests/test_all_settings_search_filter_i18n.py",
        "tests/test_runtime_count_i18n.py",
        "tests/test_chromium_locale_smoke_matrix_contract.py",
        "tests/test_locale_viewport_overflow_contract.py",
        "tests/test_locale_switching_regression_contract.py",
        "tests/test_localized_import_edit_export_workflow_contract.py",
        "tests/test_web_profiles_page.py",
        "tests/test_ui_smoke_profile_workflow.py",
    }
    for path in expected_tests:
        assert path in body


def test_makefile_declares_firefox_schema_contract_runbook_target():
    body = _target_body(_makefile_source(), "test-firefox-schema-contract")

    expected_tests = {
        "tests/test_schema_channels.py",
        "tests/test_schema_validation.py",
        "tests/test_no_legacy_schema_refs.py",
        "tests/test_migrations.py",
        "tests/test_profile_schema_normalization.py",
        "tests/test_firefox_wizard_shell.py",
        "tests/test_web_profiles_page.py",
        "tests/test_locale_catalogs.py",
        "tests/test_ui_runtime_i18n_contract.py",
        "tests/test_locale_visible_english_allowlists.py",
    }
    for path in expected_tests:
        assert path in body


def test_makefile_declares_quality_targets():
    source = _makefile_source()

    assert "typecheck" in source.splitlines()[0]
    assert "quality" in source.splitlines()[0]
    assert "$(MYPY) app" in _target_body(source, "typecheck")
    assert "quality: lint typecheck test-fast" in source


def test_makefile_declares_local_chromium_audit_target():
    source = _makefile_source()
    body = _target_body(source, "local-chromium-ui-audit")

    assert "local-chromium-ui-audit" in source.splitlines()[0]
    assert "$(PYTHON) tools/run_local_chromium_ui_audit.py" in body


def test_makefile_declares_frontend_vendor_verification_target():
    source = _makefile_source()
    body = _target_body(source, "verify-frontend-vendor")

    assert "verify-frontend-vendor" in source.splitlines()[0]
    assert "tools/verify_frontend_vendor.py" in body


def test_makefile_declares_frontend_vendor_rebuild_target():
    source = _makefile_source()
    body = _target_body(source, "rebuild-frontend-vendor")

    assert "rebuild-frontend-vendor" in source.splitlines()[0]
    assert "bash tools/rebuild_frontend_vendor.sh" in body
