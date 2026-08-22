from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"

pytestmark = pytest.mark.docs_contract


def _ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", path],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    return completed.returncode == 0


def test_artifact_policy_separates_committed_generated_built_and_shipped_material() -> None:
    policy = json.loads(
        (DOCUMENTATION_ROOT / "config/artifact-policy.json").read_text(encoding="utf-8")
    )

    assert policy["target_bpm_version"] == "0.9.6"
    assert policy["commit_policy"] == {
        "reviewed_sources": "commit",
        "localized_screenshots": "commit-after-review",
        "generated_dita": "ignore-and-regenerate",
        "local_build_output": "ignore-and-regenerate",
        "release_archives": "ignore-and-build-in-ci",
    }
    assert policy["current_runtime_contract"]["runtime_ready"] is False
    assert policy["current_runtime_contract"]["required_before_shipping"] == [
        "release extraction policy from the verified documentation package into the runtime site",
        "localized screenshot capture and review",
        "final manual QA and defect disposition for the installed documentation flow",
    ]
    assert policy["current_runtime_contract"]["runtime_source"] == (
        "make dev refreshes the ignored runtime copy through make docs-install-dev "
        "for maintainer dev review; release still requires verified package extraction"
    )


def test_generated_build_and_distribution_paths_are_ignored_but_sources_are_not() -> None:
    for ignored in (
        "src/generated/probe.dita",
        "build/site/en/index.html",
        "dist/bpm-documentation-0.9.6.tar.gz",
        "dist/bpm-documentation-0.9.6.tar.gz.sha256",
    ):
        assert _ignored(f"documentation/{ignored}"), ignored
    assert _ignored("app/documentation/site/")
    assert _ignored("app/documentation/.site-dev-install.json")
    for maintained in (
        "src/generated/README.md",
        "src/generated/cis/cis-recommendation-skeletons-0.9.0.json",
        "src/generated/cis/recommendations/cis-rec-1-1-1-1.dita",
        "config/artifact-policy.json",
        "tools/build_docs.py",
        "tests/contract/test_artifact_policy.py",
    ):
        assert not _ignored(f"documentation/{maintained}"), maintained


def test_runtime_package_discovery_still_excludes_documentation_sources_and_build_tools() -> None:
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'include = ["app*"]' in pyproject
    assert "documentation*" not in pyproject
