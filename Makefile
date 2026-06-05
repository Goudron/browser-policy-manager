.PHONY: run dev test test-fast test-unit-pilot test-unit-xdist test-contract test-ui test-live test-release test-firefox-live test-firefox-live-amo test-locale-contract test-firefox-schema-contract setup-firefox-live-browsers coverage fmt lint typecheck quality repo-health locale-inventory locale-quality build-locale-catalogs check-locale-catalogs build-profiles-css verify-frontend-vendor rebuild-frontend-vendor backfill-profile-schema-versions local-chromium-ui-audit clean-local-artifacts

PYTEST ?= $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
MYPY ?= $(if $(wildcard .venv/bin/mypy),.venv/bin/mypy,mypy)
RUFF ?= $(if $(wildcard .venv/bin/ruff),.venv/bin/ruff,ruff)
FIREFOX_CHANNEL ?= release
XDIST_WORKERS ?= auto
TEST_FAST_MARKERS := not slow and not browser_ui and not firefox_live and not firefox_live_amo
TEST_UNIT_PILOT_MARKERS := unit and not api and not contract and not docs_contract and not ui_contract and not slow and not browser_ui and not firefox_live and not firefox_live_amo
TEST_CONTRACT_MARKERS := contract and not browser_ui and not firefox_live and not firefox_live_amo
TEST_UI_MARKERS := ui_contract or browser_ui
TEST_LIVE_MARKERS := firefox_live or firefox_live_amo
TEST_RELEASE_MARKERS := not firefox_live and not firefox_live_amo
LOCAL_ARTIFACT_DIRS := \
	.bpm-test-browsers \
	.cache \
	.mypy_cache \
	.pytest_cache \
	.ruff_cache \
	artifacts \
	browser_policy_manager.egg-info \
	data \
	docs/screenshots \
	htmlcov \
	tmp_screens
LOCAL_ARTIFACT_FILES := \
	.coverage \
	coverage.xml \
	tmp-bootstrap.db

run:
	uvicorn app.main:app --reload --port 8000

dev:
	uvicorn app.main:app --reload --port 8000

test:
	$(PYTEST)

test-fast:
	$(PYTEST) -o addopts= -q -m "$(TEST_FAST_MARKERS)"

test-unit-pilot:
	$(PYTEST) -o addopts= -q -m "$(TEST_UNIT_PILOT_MARKERS)"

test-unit-xdist:
	$(PYTEST) -o addopts= -q -m "$(TEST_UNIT_PILOT_MARKERS)" -n $(XDIST_WORKERS)

test-contract:
	$(PYTEST) -o addopts= -q -m "$(TEST_CONTRACT_MARKERS)"

test-ui:
	$(PYTEST) -o addopts= -q -m "$(TEST_UI_MARKERS)"

test-live:
	$(PYTEST) -o addopts= -q -m "$(TEST_LIVE_MARKERS)"

test-release:
	$(PYTEST) -o addopts= -q -m "$(TEST_RELEASE_MARKERS)"

test-firefox-live:
	$(PYTEST) -o addopts= -q tests/live_firefox/test_policy_activation.py tests/live_firefox/test_policy_behavior.py -m "firefox_live" -rs

test-firefox-live-amo:
	$(PYTEST) -o addopts= -q tests/live_firefox/test_extension_settings_amo.py -m "firefox_live_amo" -rs

test-locale-contract:
	$(PYTEST) -o addopts= -q tests/test_locale_catalogs.py tests/test_locale_visible_english_allowlists.py tests/test_ui_runtime_i18n_contract.py tests/test_ui_locale_glossary.py tests/test_all_settings_search_filter_i18n.py tests/test_runtime_count_i18n.py tests/test_chromium_locale_smoke_matrix_contract.py tests/test_locale_viewport_overflow_contract.py tests/test_locale_switching_regression_contract.py tests/test_localized_import_edit_export_workflow_contract.py tests/test_web_profiles_page.py tests/test_ui_smoke_profile_workflow.py

test-firefox-schema-contract:
	$(PYTEST) -o addopts= -q tests/test_schema_channels.py tests/test_schema_validation.py tests/test_no_legacy_schema_refs.py tests/test_migrations.py tests/test_profile_schema_normalization.py tests/test_firefox_wizard_shell.py tests/test_web_profiles_page.py tests/test_locale_catalogs.py tests/test_ui_runtime_i18n_contract.py tests/test_locale_visible_english_allowlists.py

setup-firefox-live-browsers:
	bash tools/setup_firefox_live_browsers.sh $(FIREFOX_CHANNEL)

coverage:
	$(PYTEST) --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html
	@echo "HTML coverage report: file://$$(pwd)/htmlcov/index.html"

fmt:
	$(RUFF) check --select I --fix .
	$(RUFF) format .

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) app

quality: lint typecheck test-fast

repo-health:
	$(PYTHON) tools/repo_health_report.py

locale-inventory:
	$(PYTHON) tools/locale_inventory.py

locale-quality:
	$(PYTHON) tools/locale_policy_label_quality.py

build-locale-catalogs:
	$(PYTHON) tools/build_locale_catalogs.py

check-locale-catalogs:
	$(PYTHON) tools/build_locale_catalogs.py --check

build-profiles-css:
	$(PYTHON) tools/build_profiles_css.py

verify-frontend-vendor:
	$(PYTHON) tools/verify_frontend_vendor.py

rebuild-frontend-vendor:
	bash tools/rebuild_frontend_vendor.sh

backfill-profile-schema-versions:
	$(PYTHON) tools/backfill_profile_schema_versions.py

local-chromium-ui-audit:
	$(PYTHON) tools/run_local_chromium_ui_audit.py

clean-local-artifacts:
	@echo "Removing ignored local artifacts:"
	@printf '  %s\n' $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES)
	rm -rf $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES) *.db *.sqlite *.sqlite3 *.db-shm *.db-wal *.sqlite-shm *.sqlite-wal *.zip *.tar.gz
