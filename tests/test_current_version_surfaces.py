from __future__ import annotations

import re
import tomllib
from pathlib import Path

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_TARGET_VERSION = "0.9.3"


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
    docs_index = (REPO_ROOT / "docs" / "docs-index.md").read_text(encoding="utf-8")
    system_map = (REPO_ROOT / "docs" / "architecture" / "current-system-map.md").read_text(
        encoding="utf-8"
    )

    assert f"**Version:** `{version}`" not in readme
    assert f"## What's Included In {version}" not in readme
    assert f"BPM {version}" not in readme
    assert f"planned for {version}" not in readme
    assert f"target version {version}" not in readme
    assert f"active target {version}" not in readme
    assert "active target version" not in readme
    assert "target-version anchor" not in readme
    assert "completion placeholder" not in readme
    assert "Documentation portal status" not in readme
    normalized_readme = " ".join(readme.split())
    assert "BPM serves an installed static documentation artifact under `/help/`" in normalized_readme
    assert "keeps FastAPI `/docs` for OpenAPI" in normalized_readme
    assert "The portal contains four guide families in all six active locales:" in readme
    assert "API Integration Guide" not in readme
    assert "light, dark, and system themes" in normalized_readme
    assert "light-gray primary surfaces instead of a pure-white page" in normalized_readme
    assert "same BPM product header and visual language as the application" in normalized_readme
    assert "single BPM version derived from product metadata" in normalized_readme
    assert "Search starts as a compact one-line control" in normalized_readme
    assert "Advanced filters are hidden by default" in normalized_readme
    assert "change only through their explicit toggle" in normalized_readme
    assert "search, URL/history hydration, results, and clear preserve that choice" in normalized_readme
    assert "one generated source per locale" in normalized_readme
    assert "independently scrollable sidebar" in normalized_readme
    assert "guide, section, and topic hierarchy" in normalized_readme
    assert "reviewed minimal set of locale-specific screenshots" in normalized_readme
    for distribution in (
        "Ubuntu 26.04 LTS",
        "Debian 13.5",
        "Fedora Linux 44",
        "Linux Mint 22.3",
        "Manjaro stable branch",
    ):
        assert distribution in normalized_readme
    assert "actual Windows-host validation is not claimed" in normalized_readme
    assert "every supported policy or known managed preference" in normalized_readme
    assert "localized non-link states instead of broken documentation URLs" in normalized_readme
    assert "deterministic, local, offline-capable, and non-AI" in readme
    assert "`make docs-screenshots-check` is not implemented yet" not in readme
    assert "planned for 0.9.0 and not yet shipped" not in readme
    assert "this status note will be replaced" not in readme
    assert "BPM 0.9.0" not in readme
    assert "0.8.8" not in readme
    assert "0.8.7.1" not in readme
    assert "BPM keeps a six-locale UI matrix:" in readme
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(r"^## (?P<version>[^\n]+)$", changelog, re.MULTILINE).group(
        "version"
    ) == version
    current_changelog_entry = changelog.split("## 0.8.8", 1)[0]
    assert "Completed full default pytest" in current_changelog_entry
    assert "Maintainer manual documentation QA found issues accepted for deferral" in current_changelog_entry
    assert docs_index.startswith(f"# BPM {version} Documentation Index\n")
    assert f"first orientation point for BPM {version} work" in system_map


def test_current_release_naming_audit_bounds_091_updates():
    audit = (
        REPO_ROOT / "docs" / "architecture" / "release-naming-audit-0.9.1.md"
    ).read_text(encoding="utf-8")
    docs_index = (REPO_ROOT / "docs" / "docs-index.md").read_text(encoding="utf-8")

    assert "BPM 0.9.1 Release Naming Audit" in audit
    assert "## Bounded Update List" in audit
    assert "## Historical And Provenance Exclusions" in audit
    assert "No broad repository-wide replacement of `0.9.0` is approved" in audit

    for active_follow_up in (
        "documentation/PROJECT_SNAPSHOT.md",
        "documentation/config/artifact-policy.json",
        "documentation/config/toolchain-lock.json",
        "documentation/config/requirements.lock",
        "app/documentation/site/manifest.json",
        "app/documentation/site/ui-target-map.json",
    ):
        assert active_follow_up in audit

    for excluded_reference in (
        "CHANGELOG.md",
        "docs/archive/",
        "docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md",
        "documentation/config/firefox-policy-context-targets-0.9.0.json",
    ):
        assert excluded_reference in audit

    assert "release-naming-audit-0.9.1.md" in docs_index


def test_current_changelog_finalizes_091_documentation_release_scope():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    current_entry = changelog.split("## 0.9.1", 1)[1].split("## 0.9.0", 1)[0]
    normalized_entry = " ".join(current_entry.split())

    assert "Status: **In progress.**" not in current_entry
    assert "### Planned" not in current_entry
    for heading in ("### Added", "### Changed", "### Quality", "### Known boundaries"):
        assert heading in current_entry
    for expected in (
        "six workflow screenshots",
        "light, dark, and system theme",
        "Collapsed documentation search to one line",
        "Documents/guide/section/topic tree",
        "obsolete standalone API Integration Guide",
        "Pontoon/SUMO terminology review",
        "Ubuntu 26.04 LTS",
        "Debian 13.5",
        "Fedora Linux 44",
        "Linux Mint 22.3",
        "Manjaro stable",
        "all 120 supported Firefox policy rows",
        "all 62 known managed-preference rows",
        "TOTAL 100%",
        "Windows 10 and Windows 11 WSL behavior remains unverified",
    ):
        assert expected in normalized_entry


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
        "Release 153, ESR 153.0, and ESR 140.13",
        "coverage remains at `100%`",
    ):
        assert expected in current_entry
