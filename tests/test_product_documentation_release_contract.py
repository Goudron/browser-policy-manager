from __future__ import annotations

from tests.docs_index import doc_path_from_index


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
