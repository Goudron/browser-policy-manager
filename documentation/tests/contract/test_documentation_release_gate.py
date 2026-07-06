from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MAKEFILE = REPOSITORY_ROOT / "Makefile"
RELEASE_CONTRACT = (
    REPOSITORY_ROOT
    / "docs/architecture/product-documentation-release-contract-0.9.0.md"
)

pytestmark = pytest.mark.docs_contract


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


def test_release_tests_depend_on_documentation_release_gate() -> None:
    source = _makefile_source()

    assert "docs-release-check" in source.splitlines()[0]
    assert "test-release: docs-release-check" in source

    release_body = _target_body(source, "test-release")
    assert "$(PYTEST) -o addopts= -q -m \"$(TEST_RELEASE_MARKERS)\"" in release_body


def test_documentation_release_gate_runs_full_validation_and_contracts() -> None:
    source = _makefile_source()
    body = _target_body(source, "docs-release-check")

    assert "DOCS_RELEASE_GATE_PATHS := documentation/tests/contract" in source
    assert "$(PYTHON) documentation/tools/build_docs.py validate" in body
    assert "-m docs_contract" in body
    assert "$(DOCS_RELEASE_GATE_PATHS)" in body
    assert "six-locale parity, content, manifest, search, API examples" in body
    assert "non-browser portal contracts" in body


def test_release_contract_names_documentation_release_gate() -> None:
    contract = RELEASE_CONTRACT.read_text(encoding="utf-8")

    assert "`make docs-release-check`" in contract
    assert "make test-release" in contract
