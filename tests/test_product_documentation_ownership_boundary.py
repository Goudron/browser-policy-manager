from __future__ import annotations

from tests.docs_index import doc_path_from_index


def _decision() -> str:
    decision = doc_path_from_index(
        "architecture/product-documentation-ownership-boundary-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")
    return " ".join(decision.split())


def test_product_documentation_boundary_assigns_all_required_owners():
    decision = _decision()

    assert "Status: **Accepted for BPM 0.9.0**" in decision
    assert "Backlog item: `BPM090-M2-05`" in decision
    for owned_area in (
        "English product content",
        "Localized product content",
        "Generated DITA facts/skeletons",
        "Shared DITA metadata",
        "Localized screenshots",
        "Build and search tooling",
        "Documentation fixtures",
        "Focused documentation tests",
        "Local build/debug output",
        "Release documentation artifact",
        "Runtime manifest/router",
        "BPM entry/deep links",
    ):
        assert f"| {owned_area} |" in decision


def test_product_documentation_boundary_defines_source_artifact_and_runtime_flow():
    decision = _decision()

    for path in (
        "documentation/src/dita/en/",
        "documentation/src/dita/{locale}/",
        "documentation/src/generated/",
        "documentation/src/shared/",
        "documentation/assets/screenshots/{locale}/",
        "documentation/fixtures/",
        "documentation/tools/",
        "documentation/tests/",
        "documentation/build/",
        "app/documentation/",
    ):
        assert f"`{path}`" in decision

    for contract_phrase in (
        "Only this artifact crosses into runtime ownership.",
        "`app/` runtime code must not import from `documentation/`",
        "bridge reads only the artifact manifest and files",
        "Generated pages and browser search make no runtime database/API calls.",
        "Search is deterministic, static, local, and offline-capable.",
        "The route is `/help/`, not `/docs`",
        "reject path traversal",
    ):
        assert contract_phrase in decision


def test_product_documentation_boundary_preserves_six_locales_and_non_ai_scope():
    decision = _decision()

    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in decision
    assert "may not silently fall back to English" in decision
    assert "Visible UI screenshots are locale-specific source assets." in decision
    assert "No LLM, embedding model, vector database, RAG" in decision
    assert "Licensed source PDFs" in decision


def test_product_documentation_boundary_isolates_test_and_debug_context():
    decision = _decision()

    for work_type in (
        "Edit one topic",
        "Fix DITA build",
        "Fix localization parity",
        "Fix deterministic search",
        "Fix screenshot capture",
        "Fix `/help/` serving",
        "Fix Library/help navigation",
        "Final release validation",
    ):
        assert f"| {work_type} |" in decision

    for command in (
        "make test-docs",
        "make test-docs-contract",
        "make test-docs-ui",
        "make docs-build",
        "make docs-screenshots-check",
        "make test-release",
    ):
        assert f"`{command}`" in decision

    assert "prohibit recursive reads of generated pages" in decision
    assert "Normal documentation implementation must not modify profile persistence" in decision
    assert "this decision alone creates no `documentation/` directory" in decision
