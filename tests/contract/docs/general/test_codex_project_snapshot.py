from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SNAPSHOT = REPO_ROOT / "docs/codex/PROJECT_SNAPSHOT.md"
GENERATOR = REPO_ROOT / "docs/codex/generate_project_snapshot.py"
SPEC = importlib.util.spec_from_file_location("generate_codex_snapshot", GENERATOR)
assert SPEC and SPEC.loader
generate_codex_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_codex_snapshot)


def test_codex_project_snapshot_is_current_compact_and_reproducible() -> None:
    snapshot = SNAPSHOT.read_text(encoding="utf-8")

    assert snapshot == generate_codex_snapshot.generate_snapshot()
    assert f"Target BPM version: `{generate_codex_snapshot._version()}`" in snapshot
    assert "Declared-source digest:" in snapshot
    assert "Generated only by `make codex-snapshot`" in snapshot
    assert "Declared Source Owners" in snapshot
    assert "Dirty files:" not in snapshot
    assert "documentation freeze" not in snapshot.lower()
    assert snapshot.count("\n") < 70


def test_codex_project_snapshot_uses_only_declared_existing_entrypoints() -> None:
    paths = generate_codex_snapshot._paths()

    assert paths
    assert all(path.is_file() for path in paths)
    assert all("vendor" not in path.parts for path in paths)
    assert all("reports" not in path.parts for path in paths)
    assert (
        REPO_ROOT / "documentation/src/dita/en/user/ug-concept-browser-policy-manager-overview.dita"
    ) not in paths
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "codex-snapshot:" in makefile
    assert "$(PYTHON) docs/codex/generate_project_snapshot.py" in makefile
