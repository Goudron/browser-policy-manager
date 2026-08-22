from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def _pre_commit_config() -> dict[str, object]:
    document = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _hook(config: dict[str, object], hook_id: str) -> dict[str, object]:
    repositories = config.get("repos")
    assert isinstance(repositories, list)
    for repository in repositories:
        assert isinstance(repository, dict)
        hooks = repository.get("hooks", [])
        assert isinstance(hooks, list)
        for hook in hooks:
            assert isinstance(hook, dict)
            if hook.get("id") == hook_id:
                return hook
    raise AssertionError(f"missing pre-commit hook: {hook_id}")


def test_pre_commit_pins_the_reviewed_python_toolchain() -> None:
    config = _pre_commit_config()
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["minimum_pre_commit_version"] == "4.6.2"
    assert config["default_language_version"] == {"python": "python3.14"}
    assert _hook(config, "ruff")
    assert _hook(config, "ruff-format")
    assert _hook(config, "mypy")

    repositories = config["repos"]
    assert isinstance(repositories, list)
    revisions: dict[str, str] = {}
    for repository in repositories:
        assert isinstance(repository, dict)
        repository_url = repository.get("repo")
        revision = repository.get("rev")
        if isinstance(repository_url, str) and isinstance(revision, str):
            revisions[repository_url] = revision
    assert revisions == {
        "https://github.com/astral-sh/ruff-pre-commit": "v0.16.3",
        "https://github.com/pre-commit/mirrors-mypy": "v2.3.1",
    }
    assert "pre-commit==4.6.2" in pyproject["project"]["optional-dependencies"]["dev"]
    assert "black>=26.5.1" not in pyproject["project"]["optional-dependencies"]["dev"]
    assert "isort>=8.0.1" not in pyproject["project"]["optional-dependencies"]["dev"]


def test_pre_commit_uses_bounded_architecture_contract_not_default_pytest() -> None:
    config = _pre_commit_config()
    hook = _hook(config, "layered-fast-architecture")

    assert hook["entry"] == "make pre-commit-check"
    assert hook["language"] == "system"
    assert hook["pass_filenames"] is False
    assert hook["always_run"] is True
    repositories = config["repos"]
    assert isinstance(repositories, list)
    hook_ids: set[str] = set()
    for repository in repositories:
        assert isinstance(repository, dict)
        hooks = repository.get("hooks", [])
        assert isinstance(hooks, list)
        for configured_hook in hooks:
            assert isinstance(configured_hook, dict)
            hook_id = configured_hook.get("id")
            if isinstance(hook_id, str):
                hook_ids.add(hook_id)
    assert "pytest" not in hook_ids
    assert "black" not in hook_ids

    source = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    start = source.index("pre-commit-check:")
    body = source[start : source.index("\nrelease-boundary:", start)]
    assert "pre-commit-check: architecture" in source
    assert "$(PRE_COMMIT_TEST_PATHS)" in body
    assert "not the full test suite" in body
    assert "$(PYTEST) -o addopts= -q" in body
    assert "$(TEST_FAST_MARKERS)" not in body
    assert "tests/unit/tooling/test_pre_commit_contract.py" in source


def test_pre_commit_full_release_commands_remain_explicit() -> None:
    source = (REPO_ROOT / "docs" / "architecture" / "ci-layer-graph-0.9.4.md").read_text(
        encoding="utf-8"
    )

    for command in (
        "make test-unit",
        "make test-integration",
        "make test-postgres-integration",
        "make test-contract",
        "make docs-release-check",
        "make test-frontend-coverage",
        "make test-browser",
        "make test-docs-browser",
    ):
        assert command in source
    assert "never a\nrelease or full-suite success signal" in source
