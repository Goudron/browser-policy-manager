from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MAKEFILE = REPO_ROOT / "Makefile"


def _makefile_source() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def _target_body(source: str, target: str) -> str:
    match = re.search(
        rf"^{re.escape(target)}:(?:[^\n]*)\n(?P<body>(?:\t.*\n)+)",
        source,
        re.M,
    )
    assert match, f"Missing Makefile target: {target}"
    return match.group("body")


def test_makefile_declares_layered_test_targets():
    source = _makefile_source()

    for target in (
        "test-fast",
        "test-ai-incubation",
        "test-unit",
        "test-integration",
        "test-unit-pilot",
        "test-unit-xdist",
        "test-contract",
        "test-browser",
        "test-ui",
        "test-live",
        "test-release",
        "test-locale-contract",
        "test-firefox-schema-contract",
        "test-firefox-schema-workflow",
    ):
        assert target in source.splitlines()[0]
        assert _target_body(source, target)


def test_makefile_test_targets_use_named_marker_expressions():
    source = _makefile_source()

    expected_markers = {
        "TEST_FAST_MARKERS": "not ai_incubation and not slow and not browser and not live",
        "TEST_UNIT_MARKERS": "unit and not ai_incubation",
        "TEST_INTEGRATION_MARKERS": "integration and not db and not ai_incubation",
        "TEST_CONTRACT_MARKERS": "contract and not ai_incubation",
        "TEST_BROWSER_MARKERS": "browser",
        "TEST_UI_MARKERS": "ui or browser_ui",
        "TEST_LIVE_MARKERS": "live",
        "TEST_RELEASE_MARKERS": "not ai_incubation and not browser and not live",
    }
    for name, expression in expected_markers.items():
        assert f"{name} := {expression}" in source

    target_to_variable = {
        "test-fast": "TEST_FAST_MARKERS",
        "test-unit": "TEST_UNIT_MARKERS",
        "test-integration": "TEST_INTEGRATION_MARKERS",
        "test-contract": "TEST_CONTRACT_MARKERS",
        "test-browser": "TEST_BROWSER_MARKERS",
        "test-ui": "TEST_UI_MARKERS",
        "test-live": "TEST_LIVE_MARKERS",
        "test-release": "TEST_RELEASE_MARKERS",
    }
    for target, variable in target_to_variable.items():
        body = _target_body(source, target)
        assert "-o addopts= -q" in body
        assert f"$({variable})" in body

    assert "test-release: docs-release-check" in source


def test_makefile_declares_explicit_ai_incubation_contour() -> None:
    source = _makefile_source()

    assert "ai-extra-check" in source.splitlines()[0]
    assert "test-ai-incubation" in source.splitlines()[0]
    assert "tools/check_ai_extra.py" in _target_body(source, "ai-extra-check")
    body = _target_body(source, "test-ai-incubation")
    assert "ai-extra-check" in source[source.index("test-ai-incubation:") :].splitlines()[0]
    assert "$(PYTEST_COVERAGE_ARGS)" in body
    assert "--run-ai-incubation" in body
    assert '-m "ai_incubation"' in body


def test_makefile_declares_opt_in_xdist_pilot_targets():
    source = _makefile_source()
    serial_body = _target_body(source, "test-unit-pilot")
    xdist_body = _target_body(source, "test-unit-xdist")

    assert "XDIST_WORKERS ?= auto" in source
    assert "$(TEST_UNIT_MARKERS)" in serial_body
    assert "$(TEST_UNIT_MARKERS)" in xdist_body
    assert " -n " not in serial_body
    assert "-n $(XDIST_WORKERS)" in xdist_body


def test_firefox_live_target_delegates_to_live_marker_expression():
    body = _target_body(_makefile_source(), "test-firefox-live")

    assert "-o addopts= -q" in body
    assert "tests/live/firefox/test_policy_scenarios.py" in body
    assert "test_policy_activation.py" not in body
    assert "test_policy_behavior.py" not in body
    assert '-m "firefox_live"' in body
    assert "-rs" in body


def test_makefile_declares_four_channel_firefox_live_owner_target():
    source = _makefile_source()
    body = _target_body(source, "firefox-live-four-channel-workflow")

    assert "firefox-live-four-channel-workflow" in source.splitlines()[0]
    assert "tools/provision_firefox_live_browsers.py all" in body
    assert "tools/run_firefox_live_workflow.py all" in body
    assert "$(FIREFOX_LIVE_FOUR_CHANNEL_ARTIFACT_DIR)" in body


def test_makefile_declares_firefox_live_amo_canary_target():
    source = _makefile_source()
    body = _target_body(source, "test-firefox-live-amo")

    assert "test-firefox-live-amo" in source.splitlines()[0]
    assert "tests/live/firefox/test_extension_settings_amo.py" in body
    assert '-m "firefox_live_amo"' in body
    assert "-rs" in body
    assert "BPM_FIREFOX_LIVE_ARTIFACT_DIR=$(FIREFOX_LIVE_AMO_ARTIFACT_DIR)" in body
    assert "firefox-live-amo-work/$(FIREFOX_CHANNEL)" in body
    assert 'mkdir -p "$(CURDIR)/artifacts/firefox-live-amo-work"' in body


def test_makefile_declares_locale_contract_runbook_target():
    body = _target_body(_makefile_source(), "test-locale-contract")

    expected_tests = {
        "tests/integration/locale/test_locale_catalogs.py",
        "tests/integration/locale/test_locale_visible_english_allowlists.py",
        "tests/contract/ui/localization/test_ui_runtime_i18n_contract.py",
        "tests/contract/ui/localization/test_ui_locale_glossary.py",
        "tests/contract/ui/localization/test_all_settings_search_filter_i18n.py",
        "tests/contract/ui/localization/test_runtime_count_i18n.py",
        "tests/contract/ui/localization/test_chromium_locale_smoke_matrix_contract.py",
        "tests/contract/ui/localization/test_locale_viewport_overflow_contract.py",
        "tests/contract/ui/localization/test_locale_switching_regression_contract.py",
        "tests/contract/ui/localization/test_localized_import_edit_export_workflow_contract.py",
        "tests/contract/ui/localization/test_web_profiles_page.py",
        "tests/contract/ui/smoke/test_ui_smoke_profile_workflow.py",
    }
    for path in expected_tests:
        assert path in body


def test_makefile_declares_firefox_schema_contract_runbook_target():
    body = _target_body(_makefile_source(), "test-firefox-schema-contract")

    expected_tests = {
        "tests/unit/schema/contracts/test_schema_channels.py",
        "tests/integration/schema/test_schema_validation.py",
        "tests/integration/schema/test_firefox_schema_workflow_offline.py",
        "tests/integration/db/test_migrations.py",
        "tests/integration/firefox/test_firefox_wizard_shell.py",
        "tests/contract/ui/localization/test_web_profiles_page.py",
        "tests/integration/locale/test_locale_catalogs.py",
        "tests/contract/ui/localization/test_ui_runtime_i18n_contract.py",
        "tests/integration/locale/test_locale_visible_english_allowlists.py",
    }
    for path in expected_tests:
        assert path in body


def test_makefile_declares_offline_firefox_schema_workflow_target():
    body = _target_body(_makefile_source(), "test-firefox-schema-workflow")

    assert "tests/integration/schema/test_firefox_schema_workflow_offline.py" in body


def test_makefile_declares_four_channel_schema_release_gate():
    body = _target_body(_makefile_source(), "verify-firefox-schema-matrix")

    assert "verify-firefox-schema-matrix" in _makefile_source().splitlines()[0]
    assert "tools/verify_firefox_schema_matrix.py" in body


def test_makefile_declares_directed_firefox_conversion_matrix_gate():
    body = _target_body(_makefile_source(), "verify-firefox-conversion-matrix")

    assert "verify-firefox-conversion-matrix" in _makefile_source().splitlines()[0]
    assert "tools/verify_firefox_conversion_matrix.py" in body


def test_makefile_declares_quality_targets():
    source = _makefile_source()

    assert "typecheck" in source.splitlines()[0]
    assert "quality" in source.splitlines()[0]
    assert "$(MYPY) --explicit-package-bases $(TYPECHECK_PATHS)" in _target_body(
        source, "typecheck"
    )
    assert "quality: lint typecheck architecture test-fast" in source


def test_makefile_declares_local_chromium_audit_target():
    source = _makefile_source()
    body = _target_body(source, "local-chromium-ui-audit")

    assert "local-chromium-ui-audit" in source.splitlines()[0]
    assert "$(PYTHON) tools/run_local_chromium_ui_audit.py" in body


def test_browser_targets_share_the_failure_artifact_boundary():
    source = _makefile_source()

    assert "BROWSER_ARTIFACT_DIR ?= artifacts/browser-failures" in source
    for target in ("test-browser", "test-docs-browser"):
        body = _target_body(source, target)
        assert "BPM_BROWSER_ARTIFACT_DIR=$(BROWSER_ARTIFACT_DIR)" in body


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


def test_makefile_declares_native_frontend_test_and_coverage_targets():
    source = _makefile_source()

    for target, command in (
        ("test-frontend", "npm run test:frontend"),
        ("test-frontend-coverage", "npm run test:frontend:coverage"),
    ):
        assert target in source.splitlines()[0]
        assert command in _target_body(source, target)

    frontend_coverage = _target_body(source, "test-frontend-coverage")
    assert "FRONTEND_COVERAGE_REPORT_DIR" in frontend_coverage
    assert "coverage.txt" in frontend_coverage
    assert "pipefail" in frontend_coverage

    pure_modules = _target_body(source, "test-profile-pure-modules")
    assert "node --test" in pure_modules
    assert "tests/javascript/integration/profiles/profile_pure_modules.test.js" in pure_modules
    assert "pytest" not in pure_modules.lower()

    fixture_check = _target_body(source, "check-frontend-test-fixtures")
    assert "generate_frontend_fixtures.py --check" in fixture_check


def test_mandatory_ci_layer_targets_can_emit_coverage_without_changing_ownership() -> None:
    source = _makefile_source()

    assert "PYTEST_COVERAGE_ARGS ?=" in source
    assert "COVERAGE_FAIL_UNDER ?= 100" in source
    for target in (
        "test-ai-incubation",
        "test-unit",
        "test-integration",
        "test-contract",
        "test-browser",
    ):
        assert "$(PYTEST_COVERAGE_ARGS)" in _target_body(source, target)

    database = _target_body(source, "test-postgres-integration")
    assert "$(PYTEST_COVERAGE_ARGS)" in database
    assert "tests/integration/db" in database
    assert "test_database_integration.py" not in database

    evidence = _target_body(source, "postgres-ci-evidence")
    assert "BPM_REQUIRE_POSTGRES=1" in evidence
    assert "tools/report_postgres_ci_evidence.py" in evidence

    coverage = _target_body(source, "coverage")
    assert "surface 1/2" in coverage
    assert "surface 2/2" in coverage
    assert "completed 1/2 surfaces" in coverage
    assert "completed 2/2 surfaces" in coverage
    assert "coverage-release-implementation" in coverage
    assert "test-ai-incubation-coverage" in coverage
    assert "coverage combine $(COVERAGE_REPORT_DIR)" in coverage
    assert "--cov=app" not in coverage

    report = _target_body(source, "coverage-report")
    assert "coverage combine $(COVERAGE_DATA_DIR)" in report
    assert "coverage report --show-missing --fail-under=$(COVERAGE_FAIL_UNDER)" in report
    assert "COVERAGE_FILE=$(COVERAGE_DATA_FILE)" in report
    assert "coverage xml -o $(COVERAGE_XML)" in report
    assert "coverage html -d $(COVERAGE_HTML)" in report


def test_documentation_coverage_and_remaining_suite_form_one_non_browser_owner() -> None:
    source = _makefile_source()

    assert "DOCS_COVERAGE_TESTS := $(DOCS_COVERAGE_REQUIRED_CASES)" in source
    assert "DOCS_COVERAGE_REQUIRED_CASES :=" in source
    assert "test_pdf_topic_html_waits_for_delayed_map_output" in source
    coverage = _target_body(source, "docs-coverage")
    assert "$(DOCS_COVERAGE_TESTS)" in coverage
    assert "--cov-fail-under=100" in coverage

    remaining = _target_body(source, "test-docs")
    assert "$(DOCS_COVERAGE_IGNORE_ARGS)" in remaining
    assert "$(DOCS_COVERAGE_DESELECT_ARGS)" in remaining
