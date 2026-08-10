from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
SNAPSHOT = DOCUMENTATION_ROOT / "PROJECT_SNAPSHOT.generated.md"
GENERATOR = DOCUMENTATION_ROOT / "tools/generate_subsystem_snapshot.py"
SPEC = importlib.util.spec_from_file_location("generate_subsystem_snapshot", GENERATOR)
assert SPEC and SPEC.loader
generate_subsystem_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_subsystem_snapshot)

CODEX_GENERATOR = REPOSITORY_ROOT / "docs/codex/generate_project_snapshot.py"
CODEX_SPEC = importlib.util.spec_from_file_location("generate_codex_snapshot", CODEX_GENERATOR)
assert CODEX_SPEC and CODEX_SPEC.loader
generate_codex_snapshot = importlib.util.module_from_spec(CODEX_SPEC)
CODEX_SPEC.loader.exec_module(generate_codex_snapshot)

pytestmark = pytest.mark.docs_contract


def test_generated_documentation_subsystem_snapshot_is_current_and_reproducible() -> None:
    assert SNAPSHOT.is_file()
    assert SNAPSHOT.read_text(encoding="utf-8") == generate_subsystem_snapshot.generate_snapshot()


def test_generated_documentation_subsystem_snapshot_is_compact_and_bounded() -> None:
    snapshot = SNAPSHOT.read_text(encoding="utf-8")

    assert "BPM Documentation Subsystem Snapshot" in snapshot
    assert f"Target BPM version: `{generate_subsystem_snapshot._product_version()}`" in snapshot
    assert "Declared source digest:" in snapshot
    assert "Generated only by `make docs-snapshot`" in snapshot
    assert "Declared Source Owners" in snapshot
    assert "Runtime `/help/` bridge" in snapshot
    assert "`make docs-snapshot`" in snapshot
    assert snapshot.count("\n") < 90
    for excluded in (
        "documentation/build/",
        "documentation/dist/",
        "documentation/reports/",
        "documentation/.cache/",
        "documentation/.toolchain/",
        "documentation/src/generated/",
        "__pycache__",
        ".pyc",
        "app/api/",
        "app/services/",
        "app/static/",
    ):
        assert excluded not in snapshot
    assert "Environment And Report Evidence Excluded From This Snapshot" in snapshot
    assert "A declared source change invalidates this documentation snapshot only." in snapshot


def test_documentation_subsystem_snapshot_command_is_registered() -> None:
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "docs-snapshot:" in makefile
    assert "$(PYTHON) documentation/tools/generate_subsystem_snapshot.py" in makefile


def test_snapshot_source_owners_do_not_overlap() -> None:
    documentation_paths = set(generate_subsystem_snapshot._declared_paths())
    codex_paths = set(generate_codex_snapshot._paths())

    assert documentation_paths.isdisjoint(codex_paths)
