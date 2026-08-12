from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from app.core.config import Settings
from tests.docs_index import docs_index_rows, docs_manifest

REPO_ROOT = Path(__file__).resolve().parents[4]
OWNERSHIP_PATH = REPO_ROOT / "tests/fixtures/current_artifact_owners_0_9_4.json"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.-]+)?$")


def _owners() -> dict[str, Any]:
    value = json.loads(OWNERSHIP_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _project_version() -> str:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    assert isinstance(version, str)
    return version


def test_current_artifact_owners_are_complete_existing_and_nonoverlapping() -> None:
    ownership = _owners()
    assert ownership["schema_version"] == 1
    assert ownership["history_rule"].startswith("Historical documents are indexed")

    owner_paths: dict[str, set[str]] = {}
    historical_paths: set[str] = set()
    for fact, owner in ownership["facts"].items():
        assert set(owner) == {"authoritative_paths", "historical_paths"}
        authoritative = set(owner["authoritative_paths"])
        historical = set(owner["historical_paths"])
        assert authoritative
        assert authoritative.isdisjoint(historical)
        assert all((REPO_ROOT / path).exists() for path in authoritative)
        assert all((REPO_ROOT / path).exists() for path in historical)
        owner_paths[fact] = authoritative
        historical_paths.update(historical)

    assert owner_paths["documentation_history"] == {"docs/docs-index.md", "docs/docs-manifest.json"}
    assert owner_paths["release"].isdisjoint(historical_paths)
    assert "documentation/buildlib/" in owner_paths["documentation_build"]
    assert owner_paths["schema_lifecycle"] == {
        "app/core/schema_channels.py",
        "app/core/lifecycle_transition_plan.py",
        "app/core/retirement_convertibility_preflight.py",
        "app/core/profile_conversion_planner.py",
        "migration_support/retirement_owner_v1.py",
        "tools/schema_lifecycle_dry_run.py",
        "docs/architecture/schema-channel-surface-inventory-0.9.5.md",
    }


def test_current_release_and_documentation_artifacts_derive_one_version() -> None:
    version = _project_version()
    assert SEMVER_RE.fullmatch(version)
    assert Settings().APP_VERSION == version

    artifact_policy = json.loads(
        (REPO_ROOT / "documentation/config/artifact-policy.json").read_text(encoding="utf-8")
    )
    pdf_contract = json.loads(
        (REPO_ROOT / "documentation/config/pdf-generation-contract-0.9.3.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact_policy["target_bpm_version"] == version
    assert pdf_contract["target_bpm_version"] == version
    changelog_headings = (
        line
        for line in (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    )
    assert next(changelog_headings) == f"## {version}"


def test_history_is_indexed_without_becoming_a_current_implementation_owner() -> None:
    index_paths = {row["path"] for row in docs_index_rows()}
    manifest = docs_manifest()

    for item in manifest["finished_backlog_items"]:
        assert item["source_doc"] in index_paths
        assert item["status"] == "done"

    ownership = _owners()
    for path in ownership["facts"]["documentation_history"]["historical_paths"]:
        if path.endswith("/"):
            assert any(indexed.startswith(path.removeprefix("docs/")) for indexed in index_paths)
        else:
            assert path.removeprefix("docs/") in index_paths
