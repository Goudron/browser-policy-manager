.PHONY: run dev ai-model-install-dev ai-runtime-install-dev ai-rag-install-dev ai-web-sources-check-dev test test-fast test-unit-pilot test-unit-xdist test-contract test-ui test-live test-release test-firefox-live test-firefox-live-amo test-locale-contract test-firefox-schema-contract setup-firefox-live-browsers setup-docs-toolchain test-docs test-docs-contract test-docs-ui test-docs-ui-contract test-docs-browser docs-snapshot docs-fast-check docs-coverage docs-release-check docs-validate docs-build docs-install-dev docs-reproducibility-check docs-package docs-package-verify docs-pdf-build docs-pdf-verify docs-pdf-reproducibility docs-pdf-deliver docs-pdf-delivery-verify coverage fmt lint typecheck quality repo-health locale-inventory locale-quality build-locale-catalogs check-locale-catalogs build-profiles-css verify-frontend-vendor rebuild-frontend-vendor backfill-profile-schema-versions local-chromium-ui-audit clean-local-artifacts

PYTEST ?= $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
MYPY ?= $(if $(wildcard .venv/bin/mypy),.venv/bin/mypy,mypy)
RUFF ?= $(if $(wildcard .venv/bin/ruff),.venv/bin/ruff,ruff)
FIREFOX_CHANNEL ?= release
DOCS_TOOLCHAIN_OFFLINE ?= 0
AI_MODEL_LOCALE ?= en
AI_RUNTIME_DEV_ARCHIVE ?= documentation/.cache/bpm093-m6-03/runtime/llama-b9637-bin-ubuntu-x64.tar.gz
XDIST_WORKERS ?= auto
TEST_FAST_MARKERS := not slow and not browser_ui and not firefox_live and not firefox_live_amo
TEST_UNIT_PILOT_MARKERS := unit and not api and not contract and not docs_contract and not ui_contract and not slow and not browser_ui and not firefox_live and not firefox_live_amo
TEST_CONTRACT_MARKERS := contract and not browser_ui and not firefox_live and not firefox_live_amo
TEST_UI_MARKERS := ui_contract or browser_ui
TEST_LIVE_MARKERS := firefox_live or firefox_live_amo
TEST_RELEASE_MARKERS := not firefox_live and not firefox_live_amo
DOCS_UNIT_PATHS := documentation/tests/unit
DOCS_CONTRACT_PATHS := documentation/tests/contract
DOCS_UI_CONTRACT_PATHS := documentation/tests/contract/test_portal_shell_theme.py documentation/tests/contract/test_manifest_generation.py
DOCS_BROWSER_PATHS := documentation/tests/browser
DOCS_RELEASE_GATE_PATHS := documentation/tests/contract
DOCS_CHANGED ?=
DOCS_COVERAGE_MODULES := documentation/tools/validate_metadata.py
DOCS_COVERAGE_SOURCE := validate_metadata
DOCS_COVERAGE_TESTS := documentation/tests/unit/test_validate_metadata.py
DOCS_COVERAGE_REPORT_DIR := documentation/reports/coverage
LOCAL_ARTIFACT_DIRS := \
	.bpm-test-browsers \
	.cache \
	.mypy_cache \
	.pytest_cache \
	.ruff_cache \
	app/documentation/site \
	artifacts \
	browser_policy_manager.egg-info \
	docs/screenshots \
	htmlcov \
	tmp_screens
LOCAL_ARTIFACT_FILES := \
	.coverage \
	coverage.xml \
	app/documentation/.site-dev-install.json \
	tmp-bootstrap.db

run:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000

dev: docs-install-dev ai-model-install-dev ai-runtime-install-dev ai-rag-install-dev ai-web-sources-check-dev
	BPM_AI_LOCAL_CHAT_ENABLED=true $(PYTHON) -m uvicorn app.main:app --reload --port 8000

ai-model-install-dev:
	@echo "Ensuring the explicitly approved local chat model for development:"
	$(PYTHON) -m app.ai.model_installation install --locale $(AI_MODEL_LOCALE) --confirm

ai-runtime-install-dev:
	@echo "Ensuring the checksum-pinned local llama.cpp runtime archive for development:"
	$(PYTHON) -m app.ai.runtime_installation install-local --archive $(AI_RUNTIME_DEV_ARCHIVE) --confirm

ai-rag-install-dev:
	@echo "Ensuring persistent E5-base and the active six-locale RAG generation for development:"
	$(PYTHON) -m app.ai.rag_bootstrap provision

ai-web-sources-check-dev:
	@echo "Checking optional external-sources configuration for development:"
	$(PYTHON) -m app.documentation.web_evidence_dev_config

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

test-release: docs-release-check
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

setup-docs-toolchain:
	$(PYTHON) documentation/tools/bootstrap_toolchain.py $(if $(filter 1,$(DOCS_TOOLCHAIN_OFFLINE)),--offline,)

test-docs:
	@echo "Running documentation unit and contract suites only:"
	@echo "  $(DOCS_UNIT_PATHS) $(DOCS_CONTRACT_PATHS)"
	$(PYTEST) -o addopts= -q $(DOCS_UNIT_PATHS) $(DOCS_CONTRACT_PATHS)

test-docs-contract:
	@echo "Running documentation contract suite only:"
	@echo "  $(DOCS_CONTRACT_PATHS)"
	$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_CONTRACT_PATHS)

test-docs-ui: test-docs-ui-contract test-docs-browser

test-docs-ui-contract:
	@echo "Running documentation portal/UI non-browser contracts only:"
	@echo "  $(DOCS_UI_CONTRACT_PATHS)"
	$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_UI_CONTRACT_PATHS)

test-docs-browser:
	@echo "Running browser-backed documentation portal smoke:"
	@echo "  $(DOCS_BROWSER_PATHS)"
	@echo "Requires immediate sandbox escalation because it launches Chromium/Selenium."
	mkdir -p .cache
	$(PYTEST) -o addopts= -q -m browser_ui $(DOCS_BROWSER_PATHS) --basetemp=.cache/pytest-docs-browser

docs-snapshot:
	$(PYTHON) documentation/tools/generate_subsystem_snapshot.py

docs-fast-check:
	@echo "Running documentation-only fast check:"
	@echo "  DOCS_CHANGED=$(DOCS_CHANGED)"
	$(PYTHON) documentation/tools/build_docs.py fast-check $(DOCS_CHANGED)

docs-coverage:
	@echo "Running isolated documentation coverage:"
	@echo "  modules: $(DOCS_COVERAGE_MODULES)"
	@echo "  tests:   $(DOCS_COVERAGE_TESTS)"
	mkdir -p $(DOCS_COVERAGE_REPORT_DIR)
	$(PYTEST) -o addopts= -q $(DOCS_COVERAGE_TESTS) --cov=$(DOCS_COVERAGE_SOURCE) --cov-branch --cov-report=term-missing --cov-report=xml:$(DOCS_COVERAGE_REPORT_DIR)/docs-coverage.xml --cov-report=html:$(DOCS_COVERAGE_REPORT_DIR)/html --cov-fail-under=100
	@echo "Documentation coverage policy: documentation/config/coverage-policy-0.9.0.json"

docs-release-check:
	@echo "Running documentation release gate: full DITA validation"
	$(PYTHON) documentation/tools/build_docs.py validate
	@echo "Running documentation release gate: editorial locale sign-off"
	$(PYTHON) documentation/tools/validate_editorial_release_gate.py
	@echo "Running documentation release gate: six-locale parity, content, manifest, search, API examples, and non-browser portal contracts"
	$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_RELEASE_GATE_PATHS)

docs-validate:
	$(PYTHON) documentation/tools/build_docs.py validate

docs-build:
	$(PYTHON) documentation/tools/build_docs.py build

docs-install-dev:
	$(PYTHON) documentation/tools/build_docs.py install-dev

docs-reproducibility-check:
	$(PYTHON) documentation/tools/build_docs.py reproducibility

docs-package:
	$(PYTHON) documentation/tools/build_docs.py package

docs-package-verify:
	$(PYTHON) documentation/tools/build_docs.py package-verify

docs-pdf-build:
	$(PYTHON) documentation/tools/build_docs.py pdf-build

docs-pdf-verify:
	$(PYTHON) documentation/tools/build_docs.py pdf-verify

docs-pdf-reproducibility:
	$(PYTHON) documentation/tools/build_docs.py pdf-reproducibility

docs-pdf-deliver:
	$(PYTHON) documentation/tools/deliver_pdfs.py promote

docs-pdf-delivery-verify:
	$(PYTHON) documentation/tools/deliver_pdfs.py verify

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
	@printf '  %s\n' $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES) "data/* (except data/ai)"
	rm -rf $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES) *.db *.sqlite *.sqlite3 *.db-shm *.db-wal *.sqlite-shm *.sqlite-wal *.zip *.tar.gz
	@if [ -d data ]; then find data -mindepth 1 -maxdepth 1 ! -name ai -exec rm -rf -- {} +; fi
	@echo "Preserved installed local AI artifacts under data/ai; remove them only by explicit maintainer instruction."
