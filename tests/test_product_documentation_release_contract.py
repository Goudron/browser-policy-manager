from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from tests.docs_index import doc_path_from_index

ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = ROOT / "documentation" / "tools"
RESOURCE_TOOL_PATH = TOOLS_ROOT / "run_search_resource_benchmark_0_9_3.py"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
RESOURCE_TOOL_SPEC = importlib.util.spec_from_file_location("search_resource_benchmark", RESOURCE_TOOL_PATH)
assert RESOURCE_TOOL_SPEC and RESOURCE_TOOL_SPEC.loader
resource_benchmark = importlib.util.module_from_spec(RESOURCE_TOOL_SPEC)
sys.modules[RESOURCE_TOOL_SPEC.name] = resource_benchmark
RESOURCE_TOOL_SPEC.loader.exec_module(resource_benchmark)


def test_product_documentation_release_contract_is_active_and_complete():
    contract = doc_path_from_index(
        "architecture/product-documentation-release-contract-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM090-M1-05`" in contract
    assert "Every gate below is release-blocking." in contract
    assert "A missing planned command is a failed release gate" in contract

    gate_rows = [line for line in contract.splitlines() if line.startswith("| `DOC090-G")]
    assert len(gate_rows) == 14
    assert len({row.split("|")[1].strip() for row in gate_rows}) == 14
    assert all("Project maintainer" in row for row in gate_rows)
    assert all("`make " in row or "`pytest " in row for row in gate_rows)

    for required_scope in (
        "case-oriented User Guide",
        "Firefox Policy Guide",
        "CIS Settings Guide",
        "API Integration Guide",
        "locale-specific screenshot",
        "OpenAPI `/docs`",
        "Offline deterministic smart search",
        "100% documentation-code coverage",
        "LLMs, embeddings, vector databases, RAG",
        "administrator guide",
    ):
        assert required_scope in contract


def test_product_documentation_release_contract_names_quality_commands():
    contract = doc_path_from_index(
        "architecture/product-documentation-release-contract-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")

    for command in (
        "make docs-build",
        "make docs-release-check",
        "make test-docs",
        "make test-docs-contract",
        "make docs-screenshots-check",
        "make test-docs-ui",
        "make typecheck",
        "make lint",
        "pytest -q",
        "make coverage",
        "make test-ui",
        "make test-release",
    ):
        assert f"`{command}`" in contract


def test_product_documentation_release_contract_091_is_active_and_complete():
    contract = doc_path_from_index(
        "architecture/product-documentation-release-contract-0.9.1.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM091-M1-06`" in contract
    assert "Every gate below is release-blocking." in contract
    assert "README is not a version surface." in contract

    gate_rows = [line for line in contract.splitlines() if line.startswith("| `DOC091-G")]
    assert len(gate_rows) == 14
    assert len({row.split("|")[1].strip() for row in gate_rows}) == 14
    assert all("Project maintainer" in row for row in gate_rows)
    assert all("`make " in row or "`pytest " in row for row in gate_rows)

    for required_scope in (
        "minimal User Guide screenshot matrix",
        "light, dark, and system theme modes",
        "comfortable light-gray primary surfaces",
        "compact one-line control",
        "hierarchical tree",
        "Documentation sufficiency review",
        "five selected worldwide-popular distributions",
        "Mozilla Pontoon and SUMO terminology",
        "circled-info documentation links",
        "no README version anchor",
        "LLMs, embeddings, vector databases, RAG",
    ):
        assert required_scope in contract


def test_product_documentation_release_contract_091_names_quality_commands():
    contract = doc_path_from_index(
        "architecture/product-documentation-release-contract-0.9.1.md",
        status="active",
    ).read_text(encoding="utf-8")

    for command in (
        "documentation/tests/contract/test_user_guide_screenshot_matrix.py",
        "documentation/tests/contract/test_user_guide_screenshot_visual_qa.py",
        "make docs-release-check",
        "make test-docs",
        "make test-docs-contract",
        "make test-docs-ui",
        "make test-docs-browser",
        "make test-locale-contract",
        "make typecheck",
        "make lint",
        "pytest -q",
        "make coverage",
        "make test-ui",
        "make test-release",
    ):
        assert command in contract

    assert "make docs-screenshots-check" not in contract
    assert "unverified-no-actual-host-supplied" in contract
    assert "retained clean image" in contract
    assert "navigation.json" in contract


def test_product_documentation_release_contract_093_is_active_and_complete():
    contract = doc_path_from_index(
        "architecture/product-documentation-release-contract-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M1-06`" in contract
    assert "Every gate below is release-blocking." in contract
    assert "README remains durable current-state product documentation." in contract

    gate_rows = [line for line in contract.splitlines() if line.startswith("| `BPM093-G")]
    assert len(gate_rows) == 16
    assert len({row.split("|")[1].strip() for row in gate_rows}) == 16
    assert all("Project maintainer" in row for row in gate_rows)
    assert all("`make " in row or "pytest " in row for row in gate_rows)

    for required_scope in (
        "six locales",
        "i5-7200U, 7.1 GiB, CPU-only baseline",
        "at most 2.5 GiB",
        "at most 3.5 GiB",
        "Recall@5 at least 98%",
        "pre-generation multilingual scope gate",
        "no network request after explicit model installation",
        "Optional web evidence",
        "No qualifying provider blocks release",
        "immediate sandbox escalation",
    ):
        assert required_scope in contract


def test_active_version_and_ai_boundary_audit_093_is_indexed_and_complete():
    audit = doc_path_from_index(
        "architecture/active-version-and-ai-boundary-audit-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M1-07`" in audit
    assert "No `0.9.2` reference exists in runtime source" in audit
    assert "56 `0.9.2` path hits" in audit
    assert "37\nAI/RAG-boundary path hits" in audit
    for disposition in ("**Retain", "**Replace", "**Narrow"):
        assert disposition in audit
    for required_owner in ("M2/M4", "M12-01", "M12-05", "M12-06", "M12-07", "M13"):
        assert required_owner in audit


def test_current_documentation_search_inventory_093_is_indexed_and_complete():
    inventory = doc_path_from_index(
        "architecture/current-documentation-search-inventory-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-01`" in inventory
    assert "Full generated indexes were not read" in inventory
    assert "six `search/{locale}/index.json` records" in inventory
    assert "build-time ranking" in inventory
    assert "browser scorer is simpler" in inventory
    assert "source fingerprint does not include the search JSON contracts" in inventory
    for disposition in ("**Preserve", "**Replace", "**Adapt", "**Retire"):
        assert disposition in inventory


def test_search_selection_criteria_and_shortlist_093_is_indexed_without_a_premature_choice():
    record = doc_path_from_index(
        "architecture/search-selection-criteria-and-shortlist-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M3-01`" in record
    assert "no engine is selected or installed" in record
    assert "there are no hidden selection vetoes" in record
    for weight in ("35%", "20%", "15%", "10%"):
        assert weight in record
    for candidate in ("Current BPM static search", "Pagefind `1.5.2`", "Meilisearch Community Edition `1.45.1`"):
        assert candidate in record
    assert "browser never reaches daemon" in record
    assert "No other candidate is admitted" in record


def test_search_candidate_adapter_prototypes_093_are_indexed_and_non_production():
    record = doc_path_from_index(
        "architecture/search-candidate-adapter-prototypes-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M3-02`" in record
    assert "no vendor engine is installed, started, or benchmarked" in record
    assert "24 compact plain-text documents" in record
    assert "browser-to-daemon transport is forbidden" in record
    assert "must not be reported as Pagefind or Meilisearch relevance" in record


def test_six_locale_search_relevance_benchmark_093_is_indexed_without_a_selection_claim():
    record = doc_path_from_index(
        "architecture/six-locale-search-relevance-benchmark-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M3-03`" in record
    assert "Measured; no engine is selected" in record
    assert "732 records" in record
    assert "Pagefind `1.5.2`" in record
    assert "Meilisearch CE `1.45.1`" in record
    assert "not collapsed into a macro average" in record
    assert "No external candidate is more relevant than the current control in all six locales" in record


def test_search_resource_operability_benchmark_093_is_indexed_and_measured_without_a_selection():
    record = doc_path_from_index(
        "architecture/search-resource-operability-integration-benchmark-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M3-04`" in record
    assert "Measured; no engine is selected" in record
    assert "54,400 KiB RSS" in record
    assert "P95 4.80 ms" in record
    assert "240 documents" in record
    assert "4.28 ms P95" in record
    assert "make test-docs-browser` passed" in record
    assert "no engine is selected" in record


def test_search_resource_benchmark_growth_fixture_and_atomic_rollback_are_deterministic(tmp_path: Path):
    growth = resource_benchmark.build_growth_documents()

    assert len(growth) == 240
    assert len({document["document_id"] for document in growth}) == 240
    assert all("-growth-" in document["topic_id"] for document in growth)

    baseline_site = tmp_path / "baseline"
    growth_site = tmp_path / "growth"
    baseline_site.mkdir()
    growth_site.mkdir()
    (baseline_site / "index.html").write_text("baseline", encoding="utf-8")
    (growth_site / "index.html").write_text("growth", encoding="utf-8")

    result = resource_benchmark.atomic_install_update_rollback(
        baseline_site, growth_site, tmp_path / "installed"
    )

    assert result == {"clean_install": True, "atomic_update": True, "rollback": True}


def test_search_engine_adr_093_selects_the_bpm_owned_static_control():
    adr = doc_path_from_index(
        "architecture/search-engine-adr-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M3-05`" in adr
    assert "Accepted own-engine decision; no external replacement is selected" in adr
    assert "BPM093-G05` is closed" in adr
    assert "not an invented absolute relevance floor" in adr
    assert "Current BPM static control" in adr
    assert "Select as BPM's own engine and improve it in M4" in adr
    assert "Pagefind `1.5.2`" in adr
    assert "Meilisearch Community Edition `1.45.1`" in adr
    assert "M4 must improve the selected own implementation" in adr


def test_bpm093_backlog_authorizes_task_scoped_permission_requests_only_after_approval():
    backlog = (ROOT / "docs/bpm_0_9_3_documentation_search_local_rag_backlog_2026-07-28.md").read_text(
        encoding="utf-8"
    )

    assert "An approval automatically authorizes the agent to request and use every task-scoped execution" in backlog
    assert "immediate sandbox\nescalation for browser/Selenium commands" in backlog
    assert "must not make a restricted trial first" in backlog
    assert "does not cover external account creation" in backlog


def test_old_laptop_benchmark_protocol_093_is_indexed_and_reproducible():
    protocol = doc_path_from_index(
        "architecture/old-laptop-benchmark-protocol-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-02`" in protocol
    for required_scope in (
        "Intel Core i5-7200U, two physical cores/four logical threads, 7.1 GiB RAM, CPU-only",
        "at least 40 search or retrieval queries and at least 24 answer/dialogue cases",
        "five unreported warm-up attempts followed by 30 measured attempts",
        "rank 29 after ascending sort",
        "VmRSS",
        "Every 100 ms",
        "process-cold",
        "no-network benchmark runner",
        "zero network requests after explicit installation",
    ):
        assert required_scope in protocol


def test_six_locale_evaluation_corpus_093_records_maintainer_accepted_locale_review():
    record = doc_path_from_index(
        "architecture/six-locale-evaluation-corpus-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-03`" in record
    assert "maintainer-confirmed locale review is recorded" in record
    for locale in ("`en`", "`ru`", "`de`", "`zh-CN`", "`fr`", "`es-ES`"):
        assert locale in record
    assert "| `en` | 40 | 24 |" in record
    assert "eligible for future M3/M5/M7/M8 evaluation runners" in record


def test_rag_knowledge_update_contract_093_is_indexed_and_keeps_reindexing_distinct_from_training():
    contract = doc_path_from_index(
        "architecture/rag-knowledge-and-update-contract-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-04`" in contract
    assert "no RAG runtime, model, embeddings, chunks, or index is implemented" in contract
    assert "ragc-v1:{locale}:{topic_id}:{anchor_id_or_root}:{ordinal}" in contract
    assert "fail closed to lexical search" in contract
    assert "does not modify base-model weights" in contract
    for locale in ("`en`", "`ru`", "`de`", "`zh-CN`", "`fr`", "`es-ES`"):
        assert locale in contract


def test_local_ai_security_privacy_architecture_093_is_indexed_and_release_blocking():
    contract = doc_path_from_index(
        "architecture/local-ai-security-privacy-architecture-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-05`" in contract
    assert "local AI remains unimplemented and disabled" in contract
    assert "must not inherit that policy" in contract
    assert "pre-inference multilingual scope gate" in contract
    assert "no AI listener" in contract
    assert "Local mode performs zero network requests" in contract
    threat_rows = [line for line in contract.splitlines() if line.startswith("| `AI093-T")]
    assert len(threat_rows) == 14
    assert all("M" in row for row in threat_rows)
    assert "Every register row is release-blocking" in contract


def test_local_ai_availability_fallback_contract_093_is_indexed_and_preserves_search():
    contract = doc_path_from_index(
        "architecture/local-ai-availability-fallback-contract-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-06`" in contract
    assert "no assistant endpoint, worker, artifact lifecycle, or UI is implemented" in contract
    assert "`/health/ready` continues to report only core BPM readiness" in contract
    assert "`lexical_search_ready` remains true" in contract
    state_rows = [line for line in contract.splitlines() if line.startswith("| `")]
    assert len(state_rows) == 12
    for state in (
        "disabled",
        "not-installed",
        "downloading",
        "indexing",
        "loading",
        "ready",
        "busy",
        "cancelled",
        "degraded",
        "incompatible",
        "crashed",
        "web-offline",
    ):
        assert f"`{state}`" in contract
    assert "English visible fallback is forbidden" in contract
    assert "Partial, stale, unverified" in contract


def test_local_ai_preimplementation_guards_093_are_indexed_and_cover_failure_cases():
    contract = doc_path_from_index(
        "architecture/local-ai-preimplementation-guards-0.9.3.md",
        status="active",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM093-M2-07`" in contract
    assert "do not implement an AI runtime" in contract
    for guard in (
        "Chunk identity",
        "Locale evidence",
        "Artifact ownership",
        "Resources",
        "Startup/network",
        "Assistant capability",
        "Grounding",
        "Availability",
    ):
        assert guard in contract
    assert "raises\n`GuardViolation`" in contract
    assert "do not start a model" in contract
