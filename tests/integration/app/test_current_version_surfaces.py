from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]


def _project_version() -> str:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    assert isinstance(version, str)
    return version


def _distribution_metadata_version(metadata: bytes) -> str | None:
    return BytesParser().parsebytes(metadata).get("Version")


def _distribution_requirements(metadata: bytes) -> tuple[Requirement, ...]:
    values = BytesParser().parsebytes(metadata).get_all("Requires-Dist", [])
    return tuple(Requirement(value) for value in values)


def _build_release_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    source_root = tmp_path / "source"
    source_root.mkdir()
    for filename in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(REPO_ROOT / filename, source_root / filename)
    shutil.copytree(
        REPO_ROOT / "app",
        source_root / "app",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--outdir",
            str(artifacts_dir),
            ".",
        ],
        cwd=source_root,
        check=True,
    )

    (sdist,) = artifacts_dir.glob("*.tar.gz")
    (wheel,) = artifacts_dir.glob("*.whl")
    return sdist, wheel


def test_current_version_metadata_is_single_source_of_truth():
    version = _project_version()

    assert Settings().APP_VERSION == version
    assert (REPO_ROOT / "README.md").is_file()
    assert (
        (REPO_ROOT / "docs" / "docs-index.md")
        .read_text(encoding="utf-8")
        .startswith(f"# BPM {version} Documentation Index\n")
    )
    system_map = (REPO_ROOT / "docs" / "architecture" / "current-system-map.md").read_text(
        encoding="utf-8"
    )
    assert f"first orientation point for BPM {version} work" in system_map
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.splitlines()[2] == f"## {version}"


def test_release_artifacts_and_installed_runtime_match_project_metadata(tmp_path: Path):
    version = _project_version()
    sdist, wheel = _build_release_artifacts(tmp_path)

    with tarfile.open(sdist) as archive:
        pkg_info = next(
            member for member in archive.getmembers() if member.name.endswith("/PKG-INFO")
        )
        metadata = archive.extractfile(pkg_info)
        assert metadata is not None
        assert _distribution_metadata_version(metadata.read()) == version

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name)
        assert _distribution_metadata_version(metadata) == version
        requirements = _distribution_requirements(metadata)
        for distribution in ("numpy", "onnxruntime", "tokenizers"):
            matching = [
                requirement
                for requirement in requirements
                if canonicalize_name(requirement.name) == distribution
            ]
            assert len(matching) == 1
            assert matching[0].marker is not None
            assert matching[0].marker.evaluate({"extra": "ai"})
            assert not matching[0].marker.evaluate({"extra": ""})
        packaged_names = archive.namelist()
        for required in (
            "app/i18n/en.json",
            "app/static/favicon.ico",
            "app/static/profiles.css",
            "app/static/vendor/profiles_monaco.js",
            "app/templates/profiles.html",
            "app/templates/profiles/_page_document.html",
            "app/schemas/policies/firefox-release-153.json",
            "app/compliance/firefox/cis/sources.yaml",
        ):
            assert required in packaged_names
        assert not any("/data/ai/" in name or name.endswith(".onnx") for name in packaged_names)

    installed_root = tmp_path / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(installed_root),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    runtime = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.metadata, json; from app.core.config import Settings; "
            "print(json.dumps({'metadata': importlib.metadata.version('browser-policy-manager'), "
            "'runtime': Settings().APP_VERSION}))",
        ],
        cwd=tmp_path,
        env={"PATH": os.environ["PATH"], "PYTHONPATH": str(installed_root)},
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(runtime.stdout) == {"metadata": version, "runtime": version}


def test_release_metadata_excludes_tracked_generated_metadata():
    tracked_egg_info = subprocess.run(
        ["git", "ls-files", "--", "*egg-info*"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert not tracked_egg_info.stdout.strip()
    assert "*.egg-info/" in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
