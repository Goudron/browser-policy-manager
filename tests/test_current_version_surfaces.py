from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    assert isinstance(version, str)
    return version


def test_current_version_surfaces_follow_pyproject():
    version = _project_version()

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    docs_index = (REPO_ROOT / "docs" / "docs-index.md").read_text(encoding="utf-8")
    system_map = (REPO_ROOT / "docs" / "architecture" / "current-system-map.md").read_text(
        encoding="utf-8"
    )

    assert f"**Version:** `{version}`" in readme
    assert f"## What's Included In {version}" in readme
    assert f"BPM {version} keeps a six-locale UI matrix:" in readme
    assert re.search(r"^## (?P<version>[^\n]+)$", changelog, re.MULTILINE).group(
        "version"
    ) == version
    assert docs_index.startswith(f"# BPM {version} Documentation Index\n")
    assert f"first orientation point for BPM {version} work" in system_map
