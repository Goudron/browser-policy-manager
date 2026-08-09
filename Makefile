.PHONY: run dev ai-extra-check ai-model-install-dev ai-rag-install-dev ai-runtime-install-dev ai-web-sources-check-dev dependency-audit package-smoke test test-ai-incubation test-ai-incubation-coverage coverage-release-implementation test-browser test-contract test-fast test-frontend test-frontend-coverage test-integration test-live test-profile-pure-modules test-release test-ui test-unit test-unit-pilot test-unit-xdist test-firefox-live firefox-live-workflow test-firefox-live-amo test-locale-contract test-firefox-schema-contract test-firefox-schema-workflow test-db-integration test-db-recovery test-postgres-integration postgres-ci-evidence setup-firefox-live-browsers verify-firefox-live-browsers setup-docs-toolchain test-docs test-docs-contract test-docs-ui test-docs-ui-contract test-docs-browser codex-snapshot docs-snapshot docs-fast-check docs-coverage docs-release-check docs-release-handoff docs-validate docs-build docs-install-dev docs-reproducibility-check docs-package docs-package-verify docs-pdf-build docs-pdf-verify docs-pdf-deliver docs-pdf-delivery-verify coverage coverage-report fmt lint typecheck architecture pre-commit-check release-boundary quality repo-health profile-performance profile-performance-gate profile-performance-release-gate locale-inventory locale-quality build-locale-catalogs check-locale-catalogs build-profiles-css build-profile-frontend-bundles verify-profile-frontend-vendor verify-frontend-vendor rebuild-frontend-vendor local-chromium-ui-audit clean-local-artifacts

PYTEST ?= $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
MYPY ?= $(if $(wildcard .venv/bin/mypy),.venv/bin/mypy,mypy)
RUFF ?= $(if $(wildcard .venv/bin/ruff),.venv/bin/ruff,ruff)
IMPORT_LINTER ?= $(if $(wildcard .venv/bin/lint-imports),.venv/bin/lint-imports,lint-imports)
FIREFOX_CHANNEL ?= release
FIREFOX_LIVE_TIMEOUT_SECONDS ?= 1200
FIREFOX_LIVE_ARTIFACT_DIR ?= artifacts/firefox-live/$(FIREFOX_CHANNEL)
FIREFOX_LIVE_AMO_ARTIFACT_DIR ?= artifacts/firefox-live-amo/$(FIREFOX_CHANNEL)
DOCS_TOOLCHAIN_OFFLINE ?= 0
AI_MODEL_LOCALE ?= en
AI_RUNTIME_DEV_ARCHIVE ?= documentation/.cache/bpm093-m6-03/runtime/llama-b9637-bin-ubuntu-x64.tar.gz
XDIST_WORKERS ?= auto
PYTEST_COVERAGE_ARGS ?=
COVERAGE_DATA_DIR ?= coverage-data
COVERAGE_REPORT_DIR ?= artifacts/coverage/python
COVERAGE_DATA_FILE := $(COVERAGE_REPORT_DIR)/.coverage
COVERAGE_XML := $(COVERAGE_REPORT_DIR)/coverage.xml
COVERAGE_HTML := $(COVERAGE_REPORT_DIR)/html
COVERAGE_FAIL_UNDER ?= 100
FRONTEND_COVERAGE_REPORT_DIR ?= artifacts/coverage/frontend
RELEASE_IMPLEMENTATION_COVERAGE_TARGETS := \
	--cov=app.ai.least_privilege \
	--cov=app.ai.model_management \
	--cov=app.documentation.training_notice
AI_INCUBATION_COVERAGE_TARGETS := \
	--cov=app.ai.e5_runtime \
	--cov=app.ai.local_inference_worker \
	--cov=app.ai.rag_bootstrap \
	--cov=app.documentation.answer_validation \
	--cov=app.documentation.assistant_capabilities \
	--cov=app.documentation.conversation \
	--cov=app.documentation.conversation_context \
	--cov=app.documentation.conversation_diagnostics \
	--cov=app.documentation.conversation_stream \
	--cov=app.documentation.evidence \
	--cov=app.documentation.evidence_relevance \
	--cov=app.documentation.local_assistant_runtime \
	--cov=app.documentation.response_timing \
	--cov=app.documentation.retrieval \
	--cov=app.documentation.topic_scope \
	--cov=app.documentation.web_evidence \
	--cov=app.documentation.web_evidence_consent \
	--cov=app.documentation.web_evidence_merge
TEST_FAST_MARKERS := not ai_incubation and not slow and not browser and not live
TEST_UNIT_MARKERS := unit and not ai_incubation
# Database-marked integration tests have one CI owner: the real PostgreSQL job.
TEST_INTEGRATION_MARKERS := integration and not db and not ai_incubation
TEST_CONTRACT_MARKERS := contract and not ai_incubation
TEST_BROWSER_MARKERS := browser
TEST_UI_MARKERS := ui
TEST_LIVE_MARKERS := live
TEST_RELEASE_MARKERS := not ai_incubation and not browser and not live
PRE_COMMIT_TEST_PATHS := \
	tests/unit/tooling/test_makefile_test_targets.py \
	tests/unit/tooling/test_ci_workflow_layers.py \
	tests/unit/tooling/test_pre_commit_contract.py
DOCS_UNIT_PATHS := documentation/tests/unit
DOCS_CONTRACT_PATHS := documentation/tests/contract
DOCS_UI_CONTRACT_PATHS := documentation/tests/contract/test_portal_shell_theme.py documentation/tests/contract/test_manifest_generation.py
DOCS_BROWSER_PATHS := documentation/tests/browser
DOCS_RELEASE_GATE_PATHS := documentation/tests/contract
DOCS_CHANGED ?=
DOCS_FAST_BUDGET_SECONDS ?= 30
DOCS_COVERAGE_MODULES := documentation/buildlib/{artifacts,catalog,lifecycle,portal,shared,sources,validation}.py documentation/tools/validate_metadata.py
DOCS_COVERAGE_TARGETS := --cov=documentation.buildlib.artifacts --cov=documentation.buildlib.catalog --cov=documentation.buildlib.lifecycle --cov=documentation.buildlib.portal --cov=documentation.buildlib.shared --cov=documentation.buildlib.sources --cov=documentation.buildlib.validation --cov=validate_metadata
DOCS_COVERAGE_FILE_CASES := \
	documentation/tests/unit/test_build_docs_structure.py \
	documentation/tests/unit/test_buildlib_artifacts.py \
	documentation/tests/unit/test_buildlib_catalog.py \
	documentation/tests/unit/test_buildlib_portal.py \
	documentation/tests/unit/test_buildlib_shared.py \
	documentation/tests/unit/test_buildlib_sources.py \
	documentation/tests/unit/test_build_lifecycle.py \
	documentation/tests/unit/test_validate_metadata.py
DOCS_COVERAGE_FUNCTION_CASES := \
	documentation/tests/unit/test_build_docs.py::test_manifest_generation_lists_guides_locales_search_and_target_map \
	documentation/tests/unit/test_build_docs.py::test_search_indexes_are_reproducible_for_clean_publish_trees \
	documentation/tests/unit/test_build_docs.py::test_staged_search_validation_rejects_each_semantic_failure_class \
	documentation/tests/unit/test_build_docs.py::test_manifest_validation_stages_preserve_stable_diagnostics \
	documentation/tests/unit/test_build_docs.py::test_validation_reporter_exposes_typed_stage_without_changing_diagnostic \
	documentation/tests/unit/test_build_docs.py::test_validation_reporter_preserves_success_and_reclassifies_legacy_failures \
	documentation/tests/unit/test_build_docs.py::test_package_keeps_last_verified_outputs_when_source_validation_fails \
	documentation/tests/unit/test_build_docs.py::test_pdf_candidate_build_writes_every_locale_guide_and_normalizes_metadata \
	documentation/tests/unit/test_build_docs.py::test_canonicalize_pdf_replaces_qpdf_trailer_id_after_the_rewrite \
	documentation/tests/unit/test_build_docs.py::test_pdf_article_drops_temporary_local_file_links_but_keeps_external_links \
	documentation/tests/unit/test_build_docs.py::test_pdf_topic_html_waits_for_delayed_map_output
DOCS_COVERAGE_REQUIRED_CASES := $(DOCS_COVERAGE_FILE_CASES) $(DOCS_COVERAGE_FUNCTION_CASES)
DOCS_COVERAGE_IGNORE_ARGS := $(addprefix --ignore=,$(DOCS_COVERAGE_FILE_CASES))
DOCS_COVERAGE_DESELECT_ARGS := $(addprefix --deselect=,$(DOCS_COVERAGE_FUNCTION_CASES))
# The documentation CI owner runs both commands. They form a disjoint
# non-browser partition: focused coverage-policy witnesses run under coverage,
# while every remaining documentation unit/contract test runs without it.
DOCS_COVERAGE_TESTS := $(DOCS_COVERAGE_REQUIRED_CASES)
DOCS_COVERAGE_REPORT_DIR := documentation/reports/coverage
DOCS_COVERAGE_DATA_FILE := $(DOCS_COVERAGE_REPORT_DIR)/.coverage-docs
BROWSER_ARTIFACT_DIR ?= artifacts/browser-failures
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

ai-extra-check:
	$(PYTHON) tools/check_ai_extra.py

ai-model-install-dev: ai-extra-check
	@echo "Ensuring the explicitly approved local chat model for development:"
	$(PYTHON) -m app.ai.model_installation install --locale $(AI_MODEL_LOCALE) --confirm

ai-runtime-install-dev: ai-extra-check
	@echo "Ensuring the checksum-pinned local llama.cpp runtime archive for development:"
	$(PYTHON) -m app.ai.runtime_installation install-local --archive $(AI_RUNTIME_DEV_ARCHIVE) --confirm

ai-rag-install-dev: ai-extra-check
	@echo "Ensuring persistent E5-base and the active six-locale RAG generation for development:"
	$(PYTHON) -m app.ai.rag_bootstrap provision

ai-web-sources-check-dev: ai-extra-check
	@echo "Checking optional external-sources configuration for development:"
	$(PYTHON) -m app.documentation.web_evidence_dev_config

dependency-audit:
	$(PYTHON) tools/dependency_audit.py

package-smoke:
	$(PYTHON) tools/package_smoke.py

test:
	$(PYTEST)

test-ai-incubation: ai-extra-check
	$(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) --run-ai-incubation -m "ai_incubation"

# Strict coverage is deliberately limited to the implementation inventory in
# tests/coverage-ownership-0.9.4.json.  Adapters retain their semantic owners
# in the normal unit/integration/contract/browser layers; no `coverage omit`
# rule hides them from this declaration.
test-ai-incubation-coverage: ai-extra-check
	$(PYTEST) -o addopts= -q --run-ai-incubation -m "ai_incubation" $(AI_INCUBATION_COVERAGE_TARGETS) --cov-branch --cov-report=term-missing --cov-fail-under=$(COVERAGE_FAIL_UNDER)

coverage-release-implementation:
	$(PYTEST) -o addopts= -q \
		tests/integration/ai/core/test_ai_least_privilege.py \
		tests/integration/ai/core/test_model_management.py \
		tests/integration/ai/core/test_training_notice.py \
		$(RELEASE_IMPLEMENTATION_COVERAGE_TARGETS) --cov-branch --cov-report=term-missing --cov-fail-under=$(COVERAGE_FAIL_UNDER)

test-fast:
	$(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) -m "$(TEST_FAST_MARKERS)"

test-unit:
	$(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) -m "$(TEST_UNIT_MARKERS)"

test-integration:
	$(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) -m "$(TEST_INTEGRATION_MARKERS)"

test-unit-pilot:
	$(PYTEST) -o addopts= -q -m "$(TEST_UNIT_MARKERS)"

test-unit-xdist:
	$(PYTEST) -o addopts= -q -m "$(TEST_UNIT_MARKERS)" -n $(XDIST_WORKERS)

test-contract:
	$(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) -m "$(TEST_CONTRACT_MARKERS)"

test-browser:
	BPM_BROWSER_ARTIFACT_DIR=$(BROWSER_ARTIFACT_DIR) $(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) -m "$(TEST_BROWSER_MARKERS)"

test-ui:
	$(PYTEST) -o addopts= -q -m "$(TEST_UI_MARKERS)"

test-live:
	$(PYTEST) -o addopts= -q -m "$(TEST_LIVE_MARKERS)"

test-frontend:
	npm run test:frontend

test-frontend-coverage:
	@mkdir -p "$(FRONTEND_COVERAGE_REPORT_DIR)"
	@bash -o pipefail -c 'npm run test:frontend:coverage 2>&1 | tee "$$1/coverage.txt"' -- "$(FRONTEND_COVERAGE_REPORT_DIR)"

test-release: docs-release-check
	$(PYTEST) -o addopts= -q -m "$(TEST_RELEASE_MARKERS)"

test-firefox-live:
	BPM_FIREFOX_CHANNEL=$(FIREFOX_CHANNEL) $(PYTEST) -o addopts= -q tests/live/firefox/test_policy_scenarios.py tests/live/firefox/test_persisted_profile_e2e.py -m "firefox_live" -rs --basetemp "$(CURDIR)/artifacts/firefox-live-work/$(FIREFOX_CHANNEL)"

firefox-live-workflow:
	$(PYTHON) tools/run_firefox_live_workflow.py $(FIREFOX_CHANNEL) --artifact-dir "$(FIREFOX_LIVE_ARTIFACT_DIR)" --timeout-seconds $(FIREFOX_LIVE_TIMEOUT_SECONDS)

test-firefox-live-amo:
	@mkdir -p "$(CURDIR)/artifacts/firefox-live-amo-work"
	BPM_FIREFOX_CHANNEL=$(FIREFOX_CHANNEL) BPM_FIREFOX_LIVE_ARTIFACT_DIR=$(FIREFOX_LIVE_AMO_ARTIFACT_DIR) $(PYTEST) -o addopts= -q tests/live/firefox/test_extension_settings_amo.py -m "firefox_live_amo" -rs --basetemp "$(CURDIR)/artifacts/firefox-live-amo-work/$(FIREFOX_CHANNEL)"

test-locale-contract:
	$(PYTEST) -o addopts= -q tests/integration/locale/test_locale_catalogs.py tests/integration/locale/test_locale_visible_english_allowlists.py tests/contract/ui/localization/test_ui_runtime_i18n_contract.py tests/contract/ui/localization/test_ui_locale_glossary.py tests/contract/ui/localization/test_all_settings_search_filter_i18n.py tests/contract/ui/localization/test_runtime_count_i18n.py tests/contract/ui/localization/test_chromium_locale_smoke_matrix_contract.py tests/contract/ui/localization/test_locale_viewport_overflow_contract.py tests/contract/ui/localization/test_locale_switching_regression_contract.py tests/contract/ui/localization/test_localized_import_edit_export_workflow_contract.py tests/contract/ui/localization/test_web_profiles_page.py tests/contract/ui/smoke/test_ui_smoke_profile_workflow.py

test-firefox-schema-contract:
	$(PYTEST) -o addopts= -q tests/unit/schema/contracts/test_schema_channels.py tests/integration/schema/test_schema_validation.py tests/integration/schema/test_firefox_schema_workflow_offline.py tests/integration/db/test_migrations.py tests/integration/firefox/test_firefox_wizard_shell.py tests/contract/ui/localization/test_web_profiles_page.py tests/integration/locale/test_locale_catalogs.py tests/contract/ui/localization/test_ui_runtime_i18n_contract.py tests/integration/locale/test_locale_visible_english_allowlists.py

test-firefox-schema-workflow:
	$(PYTEST) -o addopts= -q tests/integration/schema/test_firefox_schema_workflow_offline.py

test-db-integration:
	$(PYTEST) -o addopts= -q tests/integration/db/test_database_integration.py

test-db-recovery:
	$(PYTEST) -o addopts= -q tests/integration/db/test_database_recovery.py

test-postgres-integration:
	BPM_REQUIRE_POSTGRES=1 BPM_REQUIRE_POSTGRES_RECOVERY=1 $(PYTEST) -o addopts= -q $(PYTEST_COVERAGE_ARGS) tests/integration/db

postgres-ci-evidence:
	BPM_REQUIRE_POSTGRES=1 $(PYTHON) tools/report_postgres_ci_evidence.py

setup-firefox-live-browsers:
	$(PYTHON) tools/provision_firefox_live_browsers.py $(FIREFOX_CHANNEL)

verify-firefox-live-browsers:
	$(PYTHON) tools/provision_firefox_live_browsers.py $(FIREFOX_CHANNEL) --verify

setup-docs-toolchain:
	$(PYTHON) documentation/tools/bootstrap_toolchain.py $(if $(filter 1,$(DOCS_TOOLCHAIN_OFFLINE)),--offline,)

test-docs:
	@echo "Running the non-coverage documentation unit and contract partition:"
	@echo "  $(DOCS_UNIT_PATHS) $(DOCS_CONTRACT_PATHS), excluding coverage witnesses"
	$(PYTEST) -o addopts= -q $(DOCS_UNIT_PATHS) $(DOCS_CONTRACT_PATHS) $(DOCS_COVERAGE_IGNORE_ARGS) $(DOCS_COVERAGE_DESELECT_ARGS)

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
	BPM_BROWSER_ARTIFACT_DIR=$(BROWSER_ARTIFACT_DIR) $(PYTEST) -o addopts= -q -m browser_ui $(DOCS_BROWSER_PATHS) --basetemp=.cache/pytest-docs-browser

docs-snapshot:
	$(PYTHON) documentation/tools/generate_subsystem_snapshot.py

codex-snapshot:
	$(PYTHON) docs/codex/generate_project_snapshot.py

docs-fast-check:
	@echo "Running bounded documentation authoring check (budget: $(DOCS_FAST_BUDGET_SECONDS)s; not a release gate):"
	@echo "  DOCS_CHANGED=$(DOCS_CHANGED)"
	$(PYTHON) documentation/tools/build_docs.py fast-check $(DOCS_CHANGED)

docs-coverage:
	@echo "Running isolated documentation coverage:"
	@echo "  modules: $(DOCS_COVERAGE_MODULES)"
	@echo "  tests:   $(DOCS_COVERAGE_TESTS)"
	mkdir -p $(DOCS_COVERAGE_REPORT_DIR)
	COVERAGE_FILE=$(DOCS_COVERAGE_DATA_FILE) $(PYTEST) -o addopts= -q $(DOCS_COVERAGE_TESTS) $(DOCS_COVERAGE_TARGETS) --cov-branch --cov-report=term-missing --cov-report=xml:$(DOCS_COVERAGE_REPORT_DIR)/docs-coverage.xml --cov-report=html:$(DOCS_COVERAGE_REPORT_DIR)/html --cov-fail-under=100
	@echo "Documentation coverage policy: documentation/config/coverage-policy-0.9.4.json"

docs-release-check:
	@echo "Running documentation release gate: full DITA validation"
	$(PYTHON) documentation/tools/build_docs.py validate
	@echo "Running documentation release gate: editorial locale sign-off"
	$(PYTHON) documentation/tools/validate_editorial_release_gate.py
	@echo "Running documentation release gate: six-locale parity, content, manifest, search, API examples, and non-browser portal contracts"
	$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_RELEASE_GATE_PATHS)

docs-release-handoff:
	@echo "Running authoritative documentation release handoff for en, ru, de, zh-CN, fr, es-ES:"
	@echo "  Includes six-locale validation, contracts, binary PDFs, delivery, reproducibility, package, snapshot, and local install proof."
	@echo "  No release-only checks are skipped. This command is not the fast authoring check."
	$(MAKE) docs-snapshot
	$(MAKE) docs-release-check
	$(MAKE) docs-pdf-build
	$(MAKE) docs-pdf-verify
	$(MAKE) docs-pdf-deliver
	$(MAKE) docs-pdf-delivery-verify
	$(MAKE) docs-reproducibility-check
	$(MAKE) docs-package
	$(MAKE) docs-package-verify
	$(MAKE) docs-install-dev
	@echo "Authoritative documentation release handoff passed; use make test-release for the general BPM release suite."

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
	@mkdir -p "$(COVERAGE_REPORT_DIR)"
	COVERAGE_FILE=$(COVERAGE_DATA_FILE) $(PYTEST) --cov=app --cov-branch --cov-report=term-missing --cov-report=xml:$(COVERAGE_XML) --cov-report=html:$(COVERAGE_HTML) --cov-fail-under=$(COVERAGE_FAIL_UNDER)
	@echo "HTML coverage report: file://$$(pwd)/$(COVERAGE_HTML)/index.html"

coverage-report:
	@mkdir -p "$(COVERAGE_REPORT_DIR)"
	COVERAGE_FILE=$(COVERAGE_DATA_FILE) $(PYTHON) -m coverage combine $(COVERAGE_DATA_DIR)
	COVERAGE_FILE=$(COVERAGE_DATA_FILE) $(PYTHON) -m coverage report --show-missing --fail-under=$(COVERAGE_FAIL_UNDER)
	COVERAGE_FILE=$(COVERAGE_DATA_FILE) $(PYTHON) -m coverage xml -o $(COVERAGE_XML)
	COVERAGE_FILE=$(COVERAGE_DATA_FILE) $(PYTHON) -m coverage html -d $(COVERAGE_HTML)
	@echo "HTML coverage report: file://$$(pwd)/$(COVERAGE_HTML)/index.html"

fmt:
	$(RUFF) check --select I --fix .
	$(RUFF) format .

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) app

architecture:
	$(IMPORT_LINTER) --config pyproject.toml --no-cache

# Bounded local hook: validates the release-gate map and import architecture,
# but never implies that product, documentation, browser, database, or live
# test owners have run.  Those commands remain explicit below and in CI.
pre-commit-check: architecture
	@echo "Running bounded pre-commit contracts (not the full test suite):"
	$(PYTEST) -o addopts= -q $(PRE_COMMIT_TEST_PATHS)
	@echo "Full gates: make test-unit test-integration test-postgres-integration test-contract docs-release-check test-frontend-coverage test-browser test-docs-browser"

release-boundary:
	$(PYTHON) tools/release_boundary_contract.py

quality: lint typecheck architecture test-fast

repo-health:
	$(PYTHON) tools/repo_health_report.py

profile-performance:
	$(PYTHON) tools/profile_performance_harness.py

profile-performance-gate:
	$(PYTHON) tools/profile_performance_budgets.py

profile-performance-release-gate:
	$(PYTHON) tools/profile_performance_budgets.py --enforce-release-targets

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

build-profile-frontend-bundles:
	$(PYTHON) tools/build_profile_frontend_bundles.py

verify-profile-frontend-bundles:
	$(PYTHON) tools/verify_profile_frontend_bundles.py

check-profile-frontend-bundles: verify-profile-frontend-bundles
	$(PYTHON) tools/build_profile_frontend_bundles.py --check

frontend-profile-graph:
	$(PYTHON) tools/check_frontend_profile_graph.py

test-profile-pure-modules:
	node --test --test-timeout=10000 --experimental-test-isolation=process tests/javascript/integration/profiles/profile_pure_modules.test.js

check-frontend-test-fixtures:
	$(PYTHON) tests/javascript/fixtures/generate_frontend_fixtures.py --check

verify-frontend-vendor:
	$(PYTHON) tools/verify_frontend_vendor.py

rebuild-frontend-vendor:
	bash tools/rebuild_frontend_vendor.sh

local-chromium-ui-audit:
	$(PYTHON) tools/run_local_chromium_ui_audit.py

clean-local-artifacts:
	@echo "Removing ignored local artifacts:"
	@printf '  %s\n' $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES) "data/* (except data/ai)"
	rm -rf $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES) *.db *.sqlite *.sqlite3 *.db-shm *.db-wal *.sqlite-shm *.sqlite-wal *.zip *.tar.gz
	@if [ -d data ]; then find data -mindepth 1 -maxdepth 1 ! -name ai -exec rm -rf -- {} +; fi
	@echo "Preserved installed local AI artifacts under data/ai; remove them only by explicit maintainer instruction."
