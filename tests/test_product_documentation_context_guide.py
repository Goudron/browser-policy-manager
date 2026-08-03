from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_documentation_context_guide_starts_from_local_snapshot_and_bounded_sources():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    assert "refine the repository-root `AGENTS.md`" in guide
    assert "1. `documentation/PROJECT_SNAPSHOT.md`" in guide
    assert "2. `documentation/README.md`" in guide
    assert "The relevant `documentation/runbooks/` workflow" in guide
    assert "The one approved task row and execution-progress section" in guide
    assert "Do not begin a documentation-only task from the repository-wide generated snapshot" in guide
    assert "Before editing, state the minimal files" in guide
    for excluded in (
        "`documentation/build/`",
        "`documentation/dist/`",
        "`documentation/reports/`",
        "`documentation/.cache/`",
        "dependency/toolchain/vendor/virtual-environment folders",
        "all six locale trees",
        "ignored CIS PDFs",
        "a full Firefox schema",
    ):
        assert excluded in guide


def test_documentation_context_guide_routes_common_work_to_small_contexts():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    for work in (
        "One topic",
        "Locale parity",
        "Firefox policy topic",
        "CIS topic/workflow",
        "API topic/example",
        "DITA build/config",
        "Manifest/targets",
        "Search",
        "Screenshot",
        "`/help/` serving",
        "BPM help link",
    ):
        assert f"| {work} |" in guide
    assert "If a focused failure points outside this boundary" in guide


def test_documentation_context_guide_protects_dita_locales_generated_and_external_material():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    for rule in (
        "Product source is English.",
        "Published locales are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`",
        "separate optional chat feature, not a",
        "AI-assisted drafting or localization is permitted only before that review",
        "Publishable product content is DITA 1.3.",
        "Do not add product-guide Markdown, hand-authored HTML",
        "Preserve immutable topic IDs, keys, anchors, target IDs",
        "must never be imported by `app/`",
        "unregistered or unclear sources are blocked",
        "CIS source expression/PDF content remains blocked",
        "Never patch `build/`, reports, search indexes, manifests, or packaged artifacts by hand.",
    ):
        assert rule in guide


def test_documentation_context_guide_distinguishes_available_and_planned_commands():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")
    snapshot = _normalized(DOCUMENTATION_ROOT / "PROJECT_SNAPSHOT.md")
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    for command in (
        "./.venv/bin/pytest -q tests/test_product_documentation_scaffold.py",
        "./.venv/bin/pytest -q -m docs_contract",
        "./.venv/bin/ruff check <changed_python_files>",
        "git diff --check -- <changed_files>",
    ):
        assert command in guide
        assert command in snapshot

    for target in (
        "setup-docs-toolchain",
        "test-docs",
        "test-docs-contract",
        "test-docs-ui",
        "test-docs-ui-contract",
        "test-docs-browser",
        "docs-snapshot",
        "docs-fast-check",
        "docs-coverage",
        "docs-release-check",
        "docs-validate",
        "docs-build",
        "docs-install-dev",
        "docs-reproducibility-check",
        "docs-package",
        "docs-package-verify",
    ):
        assert f"make {target}" in guide
        assert f"make {target}" in snapshot
        assert f"{target}:" in makefile

    for target in ("docs-screenshots-check",):
        assert f"make {target}" in guide
        assert f"{target}:" not in makefile
    assert "Planned commands are **not available yet**" in guide
    assert "make test-docs" in snapshot
    assert "make test-docs-contract" in snapshot
    assert "make test-docs-ui" in snapshot


def test_documentation_context_guide_requires_browser_escalation_and_snapshot_updates():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    assert "require immediate sandbox escalation" in guide
    assert "Do not first attempt them inside the sandbox." in guide
    assert "keep progress or periodic status visible" in guide
    assert "Update `documentation/PROJECT_SNAPSHOT.md` in the same change" in guide
    assert "Do not update it with planned behavior presented as implemented." in guide
    assert "show exactly one next task with ID, essence, acceptance, and minimal reasoning" in guide


def test_documentation_snapshot_is_compact_current_and_points_to_existing_contracts():
    snapshot_path = DOCUMENTATION_ROOT / "PROJECT_SNAPSHOT.md"
    snapshot = _normalized(snapshot_path)

    assert snapshot_path.read_text(encoding="utf-8").count("\n") < 180
    assert "Current completed backlog item: `BPM091-M13-10`" in snapshot
    assert "Next backlog item: `BPM091-M13-11`" in snapshot
    assert "five manifest-backed contextual help links" in snapshot
    assert "localized unavailable/stale/incomplete documentation states" in snapshot
    assert "focused `/help/` accessibility/responsive/CSP/theme integration contracts" in snapshot
    assert "isolated documentation test suite boundaries" in snapshot
    assert "focused documentation make targets" in snapshot
    assert "documentation-only source fast loop" in snapshot
    assert "isolated documentation coverage reporting" in snapshot
    assert "compact deterministic fixture catalog" in snapshot
    assert "browser-verified accessible return-safe hierarchical duplicate-free static portal shell/theme" in snapshot
    assert "frozen capture-state contract" in snapshot
    assert "36 normalized PNG source assets" in snapshot
    assert "capture_user_guide_screenshots.py" in snapshot
    assert "ignored failure diagnostics" in snapshot
    assert "generated subsystem snapshot" in snapshot
    assert "release-blocking documentation gate" in snapshot
    assert "browser-backed documentation portal smoke" in snapshot
    assert "final content coverage audit" in snapshot
    assert "refreshed implemented-product README" in snapshot
    assert "documentation-only debugging protocol" in snapshot
    assert "Administrator/DevOps Guide map/key/root contract" in snapshot
    assert "API/integration re-home audit" in snapshot
    assert "DevOps configuration/storage/logs/backups/CORS/security limits" in snapshot
    assert "update-from-source evidence/migrations/docs rebuild/rollback-stop runbooks" in snapshot
    assert "migrated API integration corpus" in snapshot
    assert "DevOps integration runbooks for external control products" in snapshot
    assert "reusable DevOps environment templates/curl/Python/multipart examples" in snapshot
    assert "failed startup/probe/schema/API/import/export/storage/WSL/dependency/documentation-portal diagnostics" in snapshot
    assert "single-node source readiness" in snapshot
    assert "network exposure/proxy-readiness questions" in snapshot
    assert "HA/deferred production boundary records" in snapshot
    assert "compact validation fixtures for stale command/API/env/path/locale/deferred-claim drift" in snapshot
    assert "final no-fallback/no-short-summary locale parity review" in snapshot
    assert "`administrator-guide`" in snapshot
    assert "`make dev` refreshes the current local documentation build" in snapshot
    assert "maintainer manual review acceptance" in snapshot
    assert "`runtime_ready=false` blockers" in snapshot
    assert "Not implemented yet:" in snapshot
    assert "No `make docs-screenshots-check` target exists yet." in snapshot

    for entry_point in (
        "docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md",
        "docs/architecture/product-documentation-ownership-boundary-0.9.0.md",
        "docs/architecture/dita-publishing-toolchain-decision-0.9.0.md",
        "docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md",
        "docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md",
        "docs/architecture/product-documentation-provenance-review-0.9.0.md",
        "docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md",
        "docs/architecture/product-documentation-visual-theme-contract-0.9.1.md",
        "docs/architecture/bpm-documentation-theme-token-audit-0.9.1.md",
        "documentation/config/documentation-sufficiency-review-protocol-0.9.1.json",
        "docs/architecture/product-user-capability-inventory-0.9.0.md",
        "documentation/config/user-guide-map-0.9.0.json",
        "documentation/config/user-guide-screenshot-matrix-0.9.1.json",
        "documentation/config/search-corpus-and-results-0.9.0.json",
        "documentation/config/search-facets-filters-0.9.0.json",
        "documentation/config/search-ui-filter-contract-0.9.1.json",
        "documentation/config/navigation-tree-contract-0.9.1.json",
        "documentation/config/all-settings-row-help-link-contract-0.9.1.json",
        "documentation/config/documentation-polish-guardrails-0.9.1.json",
        "documentation/config/search-quality-performance-0.9.0.json",
        "documentation/config/search-integrity-drift-0.9.0.json",
        "documentation/config/coverage-policy-0.9.0.json",
        "documentation/config/diagnostics-policy-0.9.0.json",
        "documentation/fixtures/fixture-catalog-0.9.0.json",
        "documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json",
        "docs/architecture/linux-distribution-selection-0.9.1.md",
        "documentation/PROJECT_SNAPSHOT.generated.md",
        "documentation/tests/suite-boundaries-0.9.0.json",
        "documentation/tests/contract/test_documentation_release_gate.py",
        "documentation/tests/browser/test_documentation_portal_browser_smoke.py",
        "documentation/runbooks/debugging-protocol.md",
        "documentation/tests/contract/test_administrator_guide_scope.py",
        "documentation/tests/contract/test_administrator_devops_operational_boundaries.py",
        "documentation/tests/contract/test_administrator_linux_deployment_topics.py",
        "documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py",
        "documentation/tests/contract/test_administrator_update_from_source_topics.py",
        "documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py",
        "documentation/tests/contract/test_administrator_production_readiness_boundaries.py",
        "documentation/tests/contract/test_administrator_guide_validation_fixtures.py",
        "documentation/tests/contract/test_api_integration_topics.py",
        "documentation/tests/contract/test_api_locale_parity.py",
        "documentation/tests/contract/test_api_openapi_drift.py",
        "documentation/tests/contract/test_api_rehome_audit.py",
        "documentation/tests/contract/test_api_devops_integration_runbooks.py",
        "docs/architecture/api-integration-rehome-audit-0.9.0.json",
        "docs/architecture/api-integration-rehome-audit-0.9.0.md",
        "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json",
        "docs/architecture/cis-documentation-inventory-0.9.0.json",
        "docs/architecture/api-documentation-inventory-0.9.0.md",
        "documentation/runbooks/README.md",
    ):
        assert f"`{entry_point}`" in snapshot
        assert (REPO_ROOT / entry_point).is_file()
