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
    assert "Deterministic input digest:" in first
    assert "Runtime `/help/` bridge" in first
    assert "`make docs-snapshot`" in first
    assert "`documentation/PROJECT_SNAPSHOT.md`" in first


def test_generated_documentation_subsystem_snapshot_excludes_heavy_and_unrelated_surfaces() -> None:
    snapshot = generate_subsystem_snapshot.generate_snapshot()

    for excluded in (
        "documentation/build/",
        "documentation/dist/",
        "documentation/reports/",
        "documentation/.cache/",
        "documentation/.toolchain/",
        "__pycache__",
        ".pyc",
        "search/en/index.json",
        "app/api/",
        "app/services/",
        "app/static/",
    ):
        assert excluded not in snapshot
    assert "app/documentation" not in snapshot
    assert "unrelated application modules outside the documentation runtime bridge" in snapshot


def test_snapshot_generator_includes_only_allowed_files() -> None:
    paths = generate_subsystem_snapshot._files_under(DOCUMENTATION_ROOT / "tests")

    assert paths
    assert all("__pycache__" not in path.parts for path in paths)
    assert all(path.suffix != ".pyc" for path in paths)
