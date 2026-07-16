from __future__ import annotations

from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
RUNBOOK_ROOT = DOCUMENTATION_ROOT / "runbooks"

pytestmark = pytest.mark.docs_contract


def _text(path: str) -> str:
    return " ".join((RUNBOOK_ROOT / path).read_text(encoding="utf-8").split())


def _repository_text(path: str) -> str:
    return " ".join((REPOSITORY_ROOT / path).read_text(encoding="utf-8").split())


def test_authoring_runbooks_cover_required_maintainer_workflows() -> None:
    expected = {
        "README.md",
        "add-or-update-topic.md",
        "localization-and-screenshots.md",
        "inventory-refresh.md",
        "links-manifest-and-publishing.md",
        "debugging-protocol.md",
    }
    assert {path.name for path in RUNBOOK_ROOT.iterdir() if path.is_file()} == expected

    combined = " ".join(_text(path) for path in sorted(expected))
    for required in (
        "topic creation",
        "reuse",
        "localization",
        "screenshots",
        "Firefox",
        "CIS",
        "API",
        "link",
        "manifest",
        "debugging",
        "review",
        "publishing",
    ):
        assert required in combined


def test_one_topic_runbook_keeps_changes_small_and_dita_only() -> None:
    runbook = _text("add-or-update-topic.md")

    for required in (
        "English DITA first",
        "DITA 1.3",
        "keyref",
        "a-{semantic-kebab-slug}",
        "Do not add Markdown",
        "make docs-validate",
        "git diff --check",
    ):
        assert required in runbook


def test_localization_and_inventory_runbooks_preserve_no_ai_and_provenance_boundaries() -> None:
    localization = _text("localization-and-screenshots.md")
    inventory = _text("inventory-refresh.md")

    assert "AI-assisted translation is allowed during development" in localization
    assert "shipped localized topics must still be reviewed" in localization
    assert "documentation/assets/screenshots/{locale}/" in localization
    assert "documentation/reports/" in localization
    assert "Do not read ignored CIS PDFs" in inventory
    assert "Do not claim CIS certification" in inventory
    assert "Mozilla MPL attribution" in inventory
    assert "$BPM_BASE_URL" in inventory


def test_localization_runbook_defines_dita_translation_workflow() -> None:
    localization = _text("localization-and-screenshots.md")
    readme = _text("README.md")

    for required in (
        "English source ownership",
        "source-reviewed",
        "localization-needed",
        "localized-draft",
        "localized-reviewed",
        "blocked-source",
        "Structure gate",
        "Terminology gate",
        "Placeholder gate",
        "Provenance gate",
        "Example gate",
        "Screenshot gate",
        "Search gate",
        "Allowed technical English",
        "DITA element names",
        "$BPM_BASE_URL",
        "OpenAPI operation IDs",
        "Firefox policy IDs",
        "CIS recommendation IDs",
        "Update propagation workflow",
        "topic body, title, map label, key, metadata, code/example",
        "search alias",
        "Do not close the implementation task with compact localized peers",
        "ru`, `de`, `zh-CN`, `fr`, and `es-ES",
        "not in warnings, recovery paths, examples, caveats, or supported/unsupported claims",
    ):
        assert required in localization

    assert "unreviewed machine output as documentation functionality" in readme
    assert "AI-assisted drafting or localization is allowed during development" in readme


def test_localization_runbook_defines_terminology_and_screenshot_drift_gates() -> None:
    localization = _text("localization-and-screenshots.md")

    for required in (
        "runtime UI catalog as the authority",
        "app/i18n_src/",
        "Mozilla Pontoon first",
        "Mozilla SUMO second",
        "brand, abbreviation, identifier, command/path/API value, or placeholder",
        "Never convert known translation debt into an allowlist entry",
        "exact term and occurrence",
        "test_locale_anti_anglicism_guard.py",
        "test_visible_english_prose_review.py",
        "six approved User Guide scenarios in all six published locales (36 rows)",
        "capture_user_guide_screenshots.py",
        "caption key, and alt-text key",
        "Do not add Administrator Guide, DevOps Guide, API, or decorative captures",
        "test_user_guide_screenshot_matrix.py",
        "test_user_guide_screenshot_visual_qa.py",
        "exactly one matrix row",
    ):
        assert required in localization


def test_firefox_schema_refresh_runbook_blocks_policy_documentation_drift() -> None:
    runbook = _text("inventory-refresh.md")

    for required in (
        "Firefox Release/ESR schema bump drift gate",
        "documentation/tools/generate_firefox_policy_skeletons.py",
        "added policies",
        "removed policies",
        "changed common definitions",
        "schema-valid examples",
        "alias or tombstone decision",
        "manifest and search parity",
        "ui-target-map.json",
        "policy targets",
        "locales and screenshots where relevant",
        "content-equivalent",
        "AI/RAG/embeddings/generative search",
        "test_firefox_policy_skeleton_generation.py",
        "test_manifest_generation.py",
    ):
        assert required in runbook


def test_cis_refresh_runbook_blocks_mapping_provenance_locale_and_artifact_drift() -> None:
    runbook = _text("inventory-refresh.md")

    for required in (
        "CIS benchmark and mapping drift gate",
        "tests/test_cis_documentation_inventory.py",
        "documentation/tools/generate_cis_recommendation_skeletons.py",
        "test_cis_recommendation_skeleton_generation.py",
        "recommendation topics",
        "mappings",
        "provenance",
        "locales",
        "examples",
        "search",
        "screenshots",
        "provenance-only records",
        "generated layers",
        "starter presets",
        "manual-review paths",
        "exception-contract",
        "remove stale topics",
        "preserve reviewed hand regions",
        "mapping tables",
        "layer-checked JSON examples",
        "exactly one stable `cis-rec-*` topic",
        "Firefox policy/preference topic route",
        "source hash",
        "bpm-cis-mapping-implementation",
        "cis-benchmark-pdf",
        "no copied or indexed CIS source expression",
        "certification, endorsement, conformance, or compliance guarantee",
        "content-equivalent",
        "Localized topics may not fall back to compact summaries",
        "manifest.json",
        "ui-target-map.json",
        "every locale search index",
        "AI/RAG/embeddings",
        "documentation/assets/screenshots/{locale}/",
        "reproducibility and package verification",
    ):
        assert required in runbook


def test_links_manifest_publishing_runbook_forbids_patching_generated_artifacts() -> None:
    runbook = _text("links-manifest-and-publishing.md")

    for required in (
        "Do not hand-edit generated manifest",
        "make docs-reproducibility-check",
        "make docs-package",
        "make docs-package-verify",
        "Search files are deterministic locale-owned release artifacts",
        "Release readiness remains false",
    ):
        assert required in runbook


def test_inventory_and_publishing_runbooks_define_completion_drift_gates() -> None:
    inventory = _text("inventory-refresh.md")
    publishing = _text("links-manifest-and-publishing.md")

    for required in (
        "live_source_install_harness.py",
        "retained clean target image",
        "never edit an accepted transcript in place",
        "unverified-no-actual-host-supplied",
        "actual Windows host",
        "Administrator API ownership",
        "test_live_source_install_evidence_closure.py",
    ):
        assert required in inventory

    for required in (
        "Search files are deterministic locale-owned release artifacts",
        "navigation.json",
        "Release drift revalidation",
        "there is no `make docs-screenshots-check` target",
        "occurrence-owned allowlists",
        "independently scrolling direct-topic reveal/root return",
        "retained clean Linux image",
        "test_documentation_polish_regression_gates.py",
    ):
        assert required in publishing


def test_administrator_devops_drift_gate_points_to_executable_contracts() -> None:
    inventory = _text("inventory-refresh.md")
    contract_paths = (
        "documentation/tests/contract/test_administrator_guide_scope.py",
        "documentation/tests/contract/test_administrator_linux_deployment_topics.py",
        "documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py",
        "documentation/tests/contract/test_administrator_devops_operational_boundaries.py",
        "documentation/tests/contract/test_administrator_update_from_source_topics.py",
        "documentation/tests/contract/test_api_openapi_drift.py",
        "documentation/tests/contract/test_api_devops_integration_runbooks.py",
        "documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py",
        "documentation/tests/contract/test_administrator_production_readiness_boundaries.py",
    )

    for path in contract_paths:
        assert path in inventory
        assert (REPOSITORY_ROOT / path).is_file(), path
    assert "test_administrator_linux_deployment.py" not in inventory
    assert "test_administrator_windows_wsl_deployment.py" not in inventory
    for required in (
        "retained clean target image",
        "new attempt-isolated transcript and manifest",
        "never edit an accepted transcript in place",
        "generated navigation/search",
        "independently scrolling hierarchy",
        "theme/search/help labels must stay localized from runtime UI catalogs",
        "API procedure ownership stays in the Administrator/DevOps Guide",
    ):
        assert required in inventory


def test_schema_cis_and_locale_update_runbooks_revalidate_documentation_polish() -> None:
    firefox = _repository_text("docs/firefox-schema-update-runbook.md")
    cis = _repository_text("docs/cis_firefox_update_runbook_2026-04-13.md")
    locale = _repository_text("docs/locale_update_runbook_2026-06-01.md")

    for required in (
        "all-settings-help-target-map-0.9.1.json",
        "navigation.json",
        "Direct links must expand the Documents/guide/section/topic tree",
        "six approved User Guide screenshot scenarios",
        "test_all_settings_help_target_map.py",
    ):
        assert required in firefox

    for required in (
        "reveal the active topic in the hierarchy",
        "never revive the retired standalone API guide",
        "Runtime UI catalog terms are authoritative",
        "36-row matrix",
        "test_locale_anti_anglicism_guard.py",
    ):
        assert required in cis

    for required in (
        "Product documentation navigation, theme, or contextual help change",
        "exact runtime value under `app/i18n_src/<locale>/` is the authority",
        "36-row minimal User Guide screenshot matrix",
        "direct-topic links reveal the active tree node",
        "test_documentation_polish_regression_gates.py",
    ):
        assert required in locale
