from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_documentation_context_guide_starts_from_local_snapshot_and_bounded_sources():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    assert "refine the repository-root `AGENTS.md`" in guide
    assert "1. `documentation/PROJECT_SNAPSHOT.md`" in guide
    assert "2. `documentation/README.md`" in guide
    assert "The relevant `documentation/runbooks/` workflow" in guide
    assert "The one approved task row and execution-progress section" in guide
    assert (
        "Do not begin a documentation-only task from the repository-wide generated snapshot"
        in guide
    )
    assert "Before editing, state the minimal files" in guide
    for excluded in (
        "`documentation/build/`",
        "`documentation/dist/`",
        "`documentation/reports/`",
        "`documentation/.cache/`",
        "dependency/toolchain/vendor/virtual-environment folders",
        "all six locale trees",
        "ignored CIS PDFs",
        "a full Firefox schema",
    ):
        assert excluded in guide


def test_documentation_context_guide_routes_common_work_to_small_contexts():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    for work in (
        "One topic",
        "Locale parity",
        "Firefox policy topic",
        "CIS topic/workflow",
        "API topic/example",
        "DITA build/config",
        "Manifest/targets",
        "Search",
        "Screenshot",
        "`/help/` serving",
        "BPM help link",
    ):
        assert f"| {work} |" in guide
    assert "If a focused failure points outside this boundary" in guide


def test_documentation_context_guide_protects_dita_locales_generated_and_external_material():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    for rule in (
        "Product source is English.",
        "Published locales are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`",
        "separate optional chat feature, not a",
        "AI-assisted drafting or localization is permitted only before that review",
        "Publishable product content is DITA 1.3.",
        "Do not add product-guide Markdown, hand-authored HTML",
        "Preserve immutable topic IDs, keys, anchors, target IDs",
        "must never be imported by `app/`",
        "unregistered or unclear sources are blocked",
        "CIS source expression/PDF content remains blocked",
        "Never patch `build/`, reports, search indexes, manifests, or packaged artifacts by hand.",
    ):
        assert rule in guide


def test_documentation_context_guide_distinguishes_available_and_planned_commands():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")
    snapshot = _normalized(DOCUMENTATION_ROOT / "PROJECT_SNAPSHOT.md")
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    for command in (
        "./.venv/bin/pytest -q tests/contract/docs/general/test_product_documentation_scaffold.py",
        "./.venv/bin/pytest -q -m docs_contract",
        "./.venv/bin/ruff check <changed_python_files>",
        "git diff --check -- <changed_files>",
    ):
        assert command in guide
        assert command in snapshot

    for target in (
        "setup-docs-toolchain",
        "test-docs",
        "test-docs-contract",
        "test-docs-ui",
        "test-docs-ui-contract",
        "test-docs-browser",
        "docs-snapshot",
        "docs-fast-check",
        "docs-coverage",
        "docs-release-check",
        "docs-release-handoff",
        "docs-validate",
        "docs-build",
        "docs-install-dev",
        "docs-reproducibility-check",
        "docs-package",
        "docs-package-verify",
    ):
        assert f"make {target}" in guide
        assert f"make {target}" in snapshot
        assert f"{target}:" in makefile

    for target in ("docs-screenshots-check",):
        assert f"make {target}" in guide
        assert f"{target}:" not in makefile
    assert "Planned commands are **not available yet**" in guide
    assert "make test-docs" in snapshot
    assert "make test-docs-contract" in snapshot
    assert "make test-docs-ui" in snapshot


def test_documentation_context_guide_requires_browser_escalation_and_snapshot_updates():
    guide = _normalized(DOCUMENTATION_ROOT / "AGENTS.md")

    assert "require immediate sandbox escalation" in guide
    assert "Do not first attempt them inside the sandbox." in guide
    assert "keep progress or periodic status visible" in guide
    assert "Update `documentation/PROJECT_SNAPSHOT.md` in the same change" in guide
    assert "Do not update it with planned behavior presented as implemented." in guide
    assert "show exactly one next task with ID, essence, acceptance, and minimal reasoning" in guide
