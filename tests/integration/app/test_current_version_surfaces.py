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
from app.documentation import manifest as documentation_manifest
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
TARGET_VERSION = "0.9.6"


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

    assert version == TARGET_VERSION
    assert Settings().APP_VERSION == version
    app = create_app()
    assert app.version == version
    assert app.openapi()["info"]["version"] == version
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


def test_active_release_boundary_declarations_match_product_version() -> None:
    version = _project_version()
    release_boundary = json.loads(
        (REPO_ROOT / "tools" / "release_boundary_manifest_0_9_5.json").read_text(encoding="utf-8")
    )
    documentation_policy = json.loads(
        (REPO_ROOT / "documentation" / "config" / "artifact-policy.json").read_text(
            encoding="utf-8"
        )
    )

    assert version == TARGET_VERSION
    assert release_boundary["target_version"] == version
    assert documentation_policy["target_bpm_version"] == version
    assert documentation_policy["archive"]["root"] == f"bpm-documentation-{version}"
    assert documentation_policy["paths"]["release_archive"] == (
        f"documentation/dist/bpm-documentation-{version}.tar.gz"
    )
    assert documentation_policy["paths"]["release_checksum"] == (
        f"documentation/dist/bpm-documentation-{version}.tar.gz.sha256"
    )

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "BPM 0." not in readme
    assert "## Release" not in readme


def test_served_documentation_rejects_a_stale_product_version(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"artifact": {"bpm_version": "0.9.5.1"}}),
        encoding="utf-8",
    )

    assert documentation_manifest.documentation_artifact_problem(tmp_path) == "stale"


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
        assert any(member.name.endswith(f"-{version}/PKG-INFO") for member in archive.getmembers())

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name)
        assert _distribution_metadata_version(metadata) == version
        assert f"browser_policy_manager-{version}.dist-info/METADATA" == metadata_name
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
