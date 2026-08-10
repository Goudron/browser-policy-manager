from __future__ import annotations

import importlib.util
from pathlib import Path

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = DOCUMENTATION_ROOT / "tools/generate_subsystem_snapshot.py"
SPEC = importlib.util.spec_from_file_location("generate_subsystem_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
generate_subsystem_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_subsystem_snapshot)


def test_generated_documentation_subsystem_snapshot_is_bounded_and_reproducible() -> None:
    first = generate_subsystem_snapshot.generate_snapshot()
    second = generate_subsystem_snapshot.generate_snapshot()

    assert first == second
    assert "Declared source digest:" in first
    assert "Generated only by `make docs-snapshot`" in first
    assert "Declared Source Owners" in first
    assert "Runtime `/help/` bridge" in first
    assert "`make docs-snapshot`" in first
    assert "`documentation/AGENTS.md`" in first


def test_generated_documentation_subsystem_snapshot_excludes_heavy_and_unrelated_surfaces() -> None:
    snapshot = generate_subsystem_snapshot.generate_snapshot()

    for excluded in (
        "documentation/build/",
        "documentation/dist/",
        "documentation/reports/",
        "documentation/.cache/",
        "documentation/.toolchain/",
        "documentation/src/generated/",
        "search/en/index.json",
        "app/api/",
        "app/services/",
        "app/static/",
    ):
        assert excluded not in snapshot
    assert "Environment And Report Evidence Excluded From This Snapshot" in snapshot
    assert "Git state, local-machine paths" in snapshot


def test_snapshot_generator_uses_only_explicit_file_inputs() -> None:
    paths = generate_subsystem_snapshot._declared_paths()

    assert paths
    assert all(path.is_file() for path in paths)
    assert all(path.is_relative_to(DOCUMENTATION_ROOT.parent) for path in paths)
    assert all("build" not in path.parts for path in paths)
    assert all("reports" not in path.parts for path in paths)
    assert all("vendor" not in path.parts for path in paths)
    assert (
        DOCUMENTATION_ROOT / "src/dita/en/user/ug-concept-browser-policy-manager-overview.dita"
    ) not in paths
