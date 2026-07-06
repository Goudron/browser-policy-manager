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

pytestmark = pytest.mark.docs_contract


def test_generated_documentation_subsystem_snapshot_is_current_and_reproducible() -> None:
    assert SNAPSHOT.is_file()
    assert SNAPSHOT.read_text(encoding="utf-8") == generate_subsystem_snapshot.generate_snapshot()


def test_generated_documentation_subsystem_snapshot_is_compact_and_bounded() -> None:
    snapshot = SNAPSHOT.read_text(encoding="utf-8")

    assert "BPM Documentation Subsystem Snapshot" in snapshot
    assert "Deterministic input digest:" in snapshot
    assert "Documentation tools" in snapshot
    assert "Documentation tests" in snapshot
    assert "Runtime `/help/` bridge" in snapshot
    assert "`make docs-snapshot`" in snapshot
    assert snapshot.count("\n") < 90
    for excluded in (
        "documentation/build/",
        "documentation/dist/",
        "documentation/reports/",
        "documentation/.cache/",
        "documentation/.toolchain/",
        "__pycache__",
        ".pyc",
        "app/api/",
        "app/services/",
        "app/static/",
    ):
        assert excluded not in snapshot


def test_documentation_subsystem_snapshot_command_is_registered() -> None:
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "docs-snapshot:" in makefile
    assert "$(PYTHON) documentation/tools/generate_subsystem_snapshot.py" in makefile
