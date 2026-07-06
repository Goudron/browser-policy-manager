from __future__ import annotations

import re
import tomllib
from pathlib import Path

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_TARGET_VERSION = "0.9.0"


def _project_version() -> str:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    assert isinstance(version, str)
    return version


def test_current_version_surfaces_follow_pyproject():
    version = _project_version()

    assert version == CURRENT_TARGET_VERSION
    assert Settings().APP_VERSION == version

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    docs_index = (REPO_ROOT / "docs" / "docs-index.md").read_text(encoding="utf-8")
    system_map = (REPO_ROOT / "docs" / "architecture" / "current-system-map.md").read_text(
        encoding="utf-8"
    )

    assert f"**Version:** `{version}`" not in readme
    assert f"## What's Included In {version}" not in readme
    assert "Documentation portal status" not in readme
    normalized_readme = " ".join(readme.split())
    assert "BPM serves an installed static documentation artifact under `/help/`" in normalized_readme
    assert "keeps FastAPI `/docs` for OpenAPI" in normalized_readme
    assert "Release package extraction, localized screenshot capture/review" in normalized_readme
    assert "The portal contains five guide families in all six active locales:" in readme
    assert "deterministic, local, offline-capable, and non-AI" in readme
    assert "make docs-install-dev" in readme
    assert "make docs-release-check" in readme
    assert "`make docs-screenshots-check` is not implemented yet" in readme
    assert "planned for 0.9.0 and not yet shipped" not in readme
    assert "this status note will be replaced" not in readme
    assert "BPM 0.9.0" not in readme
    assert "0.8.8" not in readme
    assert "0.8.7.1" not in readme
    assert "BPM keeps a six-locale UI matrix:" in readme
    assert re.search(r"^## (?P<version>[^\n]+)$", changelog, re.MULTILINE).group(
        "version"
    ) == version
    assert "Status: **In progress.**" in changelog.split("## 0.8.8", 1)[0]
    assert "records only completed and verified 0.9.0 work" in changelog
    assert docs_index.startswith(f"# BPM {version} Documentation Index\n")
    assert f"first orientation point for BPM {version} work" in system_map


def test_current_changelog_summarizes_completed_088_release_scope():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    current_entry = " ".join(changelog.split("## 0.8.7.1", 1)[0].split())

    for expected in (
        "Review, Configured, and Catalog modes",
        "source attribution",
        "grouped, scope-aware settings search",
        "primary detail editor",
        "bounded visible lists",
        "permanent-delete action",
        "redundant return-to-Library action",
        "all six active locale catalogs",
        "Firefox Release 152 and ESR 140.12 schemas",
        "coverage remains at `100%`",
    ):
        assert expected in current_entry
