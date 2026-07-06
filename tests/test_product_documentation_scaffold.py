from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
LOCALES = {"en", "ru", "de", "zh-CN", "fr", "es-ES"}


def _relative_directories(path: Path) -> set[str]:
    return {
        child.relative_to(DOCUMENTATION_ROOT).as_posix()
        for child in path.iterdir()
        if child.is_dir()
        and not child.name.startswith(".")
        and child.name not in {"build", "dist", "reports"}
    }


def _is_git_ignored(relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", f"documentation/{relative_path}"],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


def test_product_documentation_scaffold_has_owned_source_tool_and_test_boundaries():
    expected_directories = {
        "assets",
        "config",
        "fixtures",
        "runbooks",
        "src",
        "tests",
        "tools",
    }
    assert _relative_directories(DOCUMENTATION_ROOT) == expected_directories

    for path in (
        "README.md",
        ".gitignore",
        "config/README.md",
        "fixtures/README.md",
        "runbooks/README.md",
        "src/README.md",
        "src/generated/README.md",
        "src/shared/README.md",
        "assets/screenshots/README.md",
        "tools/README.md",
        "tests/README.md",
    ):
        assert (DOCUMENTATION_ROOT / path).is_file()


def test_product_documentation_scaffold_has_exact_locale_source_and_screenshot_trees():
    dita_root = DOCUMENTATION_ROOT / "src" / "dita"
    screenshots_root = DOCUMENTATION_ROOT / "assets" / "screenshots"

    assert {path.name for path in dita_root.iterdir() if path.is_dir()} == LOCALES
    assert {path.name for path in screenshots_root.iterdir() if path.is_dir()} == LOCALES
    for locale in LOCALES:
        assert (dita_root / locale / ".gitkeep").is_file()
        assert (screenshots_root / locale / ".gitkeep").is_file()


def test_product_documentation_scaffold_separates_hand_authored_and_generated_content():
    readme = (DOCUMENTATION_ROOT / "README.md").read_text(encoding="utf-8")
    generated_readme = (DOCUMENTATION_ROOT / "src" / "generated" / "README.md").read_text(
        encoding="utf-8"
    )
    shared_readme = (DOCUMENTATION_ROOT / "src" / "shared" / "README.md").read_text(
        encoding="utf-8"
    )

    for classification in (
        "Hand-authored build and information-architecture configuration",
        "Hand-authored source-locale DITA",
        "Hand-authored localized DITA",
        "Generator-owned DITA facts/skeletons",
        "Reviewed publishable source assets",
        "Generated local/CI state",
    ):
        assert classification in readme
    assert "must never be hand-edited" in generated_readme
    assert "ignored by default" in generated_readme
    assert "may not conceal an English fallback" in shared_readme
    assert "no silent English fallback, compact summaries, or unreviewed machine output" in readme


def test_product_documentation_scaffold_ignores_generated_dependencies_and_caches():
    for ignored_path in (
        "build/probe.html",
        "dist/bpm-documentation-0.9.0.tar.gz",
        "reports/probe.json",
        ".cache/toolchain/dita/probe.jar",
        ".toolchain/probe",
        ".venv/probe",
        "node_modules/probe.js",
        "vendor/probe.jar",
        "tools/.venv/probe",
        "tools/node_modules/probe.js",
        "tools/vendor/probe.jar",
        "tests/unit/__pycache__/probe.pyc",
        "src/generated/probe.dita",
    ):
        assert _is_git_ignored(ignored_path), ignored_path

    for maintained_source in (
        "README.md",
        "config/probe.json",
        "src/dita/en/probe.dita",
        "src/shared/probe.dita",
        "assets/screenshots/en/probe.webp",
        "fixtures/probe.json",
        "tools/probe.py",
        "tests/contract/probe.py",
    ):
        assert not _is_git_ignored(maintained_source), maintained_source

    if (DOCUMENTATION_ROOT / "build").exists():
        assert _is_git_ignored("build")
    if (DOCUMENTATION_ROOT / "dist").exists():
        assert _is_git_ignored("dist")
    if (DOCUMENTATION_ROOT / "reports").exists():
        assert _is_git_ignored("reports")
    if (DOCUMENTATION_ROOT / ".cache").exists():
        assert _is_git_ignored(".cache")


def test_product_documentation_scaffold_has_isolated_test_groups_and_focused_runner():
    test_root = DOCUMENTATION_ROOT / "tests"

    assert {path.name for path in test_root.iterdir() if path.is_dir()} == {
        "unit",
        "contract",
        "browser",
    }
    readme = " ".join((test_root / "README.md").read_text(encoding="utf-8").split())
    assert "does not require the general BPM test tree" in readme
    assert "immediate sandbox escalation" in readme
    assert "documentation/.cache/toolchain/python-venv/bin/pytest" in readme
    assert "Use the focused documentation test commands before broader repository or release gates" in readme


def test_product_documentation_scaffold_stays_out_of_runtime_package_discovery():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = " ".join((DOCUMENTATION_ROOT / "README.md").read_text(encoding="utf-8").split())

    assert 'include = ["app*"]' in pyproject
    assert "BPM runtime code must not import `documentation.tools`" in readme
    assert "`make docs-install-dev` may install a local build" in readme
