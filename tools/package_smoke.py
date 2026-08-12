#!/usr/bin/env python3
"""Build and exercise BPM distribution artifacts in clean virtual environments.

The release-boundary checker owns source classification.  This companion gate
owns the actual deliverables: it builds both PEP 517 artifacts from a clean
source copy, verifies their metadata and file boundaries, and installs the
base, PostgreSQL, AI, and combined optional-extra contours independently.
Nothing from this check is retained in the repository.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile
from collections.abc import Iterable
from email.parser import BytesParser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_TOML = REPO_ROOT / "pyproject.toml"
PROJECT_NAME = "browser-policy-manager"
PROJECT_VERSION = "0.9.5"
LICENSE_EXPRESSION = "MPL-2.0"
BUILD_REQUIREMENT = "build==1.5.0"
NATIVE_AI_DISTRIBUTIONS = frozenset({"numpy", "onnxruntime", "tokenizers"})
POSTGRES_DISTRIBUTIONS = frozenset({"asyncpg", "psycopg"})
REQUIRED_ARTIFACT_FILES = frozenset(
    {
        "app/main.py",
        "app/api/health.py",
        "app/services/firefox_policy_export.py",
        "app/schemas/policies/firefox-release-153.json",
        "app/i18n/en.json",
        "app/static/profiles_bootstrap.js",
        "app/templates/profiles.html",
    }
)
FORBIDDEN_ARTIFACT_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "artifacts",
        "build",
        "data",
        "dist",
        "docs",
        "documentation",
        "node_modules",
        "tests",
        "tools",
    }
)
FORBIDDEN_ARTIFACT_NAMES = frozenset({".env", ".coverage", "coverage.xml"})


def _canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names(requirements: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for requirement in requirements:
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
        if match is None:
            raise AssertionError(f"Unsupported requirement declaration: {requirement!r}")
        names.add(_canonicalize(match.group(1)))
    return names


def validate_declared_packaging() -> None:
    """Check the project declarations before paying for clean installations."""
    project = tomllib.loads(PROJECT_TOML.read_text(encoding="utf-8"))["project"]
    assert project["name"] == PROJECT_NAME
    assert project["version"] == PROJECT_VERSION
    assert project["license"] == LICENSE_EXPRESSION
    assert project["requires-python"] == ">=3.14"

    optional = project["optional-dependencies"]
    assert set(optional) == {"ai", "dev", "postgres"}
    assert _requirement_names(optional["ai"]) == NATIVE_AI_DISTRIBUTIONS
    assert _requirement_names(optional["postgres"]) == POSTGRES_DISTRIBUTIONS
    assert BUILD_REQUIREMENT in optional["dev"]
    assert not (_requirement_names(project["dependencies"]) & NATIVE_AI_DISTRIBUTIONS)


def _run(command: list[str], *, cwd: Path, stage: str) -> None:
    print(f"[package-smoke] {stage}: {shlex.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _copy_clean_source(destination: Path) -> None:
    """Copy only the distributable source surface, excluding local artifacts."""
    for filename in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(REPO_ROOT / filename, destination / filename)
    shutil.copytree(
        REPO_ROOT / "app",
        destination / "app",
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".coverage",
            "*.db",
            "*.sqlite*",
        ),
    )
    # Sentinels prove that setuptools package discovery does not accidentally
    # publish a broad repository tree when an excluded top-level path exists.
    for relative in ("tests/sentinel.py", "tools/sentinel.py", "data/sentinel.db", ".env"):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("must not be packaged\n", encoding="utf-8")


def _build_artifacts(workspace: Path) -> tuple[Path, Path]:
    source = workspace / "source"
    source.mkdir()
    _copy_clean_source(source)
    dist = workspace / "dist"
    dist.mkdir()
    _run(
        [
            sys.executable,
            "-I",
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--outdir",
            str(dist),
            str(source),
        ],
        cwd=workspace,
        stage="build clean sdist and wheel",
    )
    wheels = tuple(dist.glob("browser_policy_manager-*.whl"))
    sdists = tuple(dist.glob("browser_policy_manager-*.tar.gz"))
    assert len(wheels) == 1, wheels
    assert len(sdists) == 1, sdists
    return sdists[0], wheels[0]


def _metadata_from_wheel(wheel: Path) -> tuple[Any, set[str]]:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        return BytesParser().parsebytes(archive.read(metadata_name)), names


def _metadata_from_sdist(sdist: Path) -> tuple[Any, set[str]]:
    with tarfile.open(sdist) as archive:
        names = {member.name for member in archive.getmembers() if member.isfile()}
        metadata_name = next(name for name in names if name.endswith("/PKG-INFO"))
        handle = archive.extractfile(metadata_name)
        assert handle is not None
        return BytesParser().parsebytes(handle.read()), names


def _relative_artifact_paths(paths: Iterable[str]) -> set[str]:
    normalized: set[str] = set()
    for path in paths:
        parts = Path(path).parts
        relative = parts[1:] if parts and parts[0].startswith("browser_policy_manager-") else parts
        normalized.add("/".join(relative))
    return normalized


def _validate_artifact_paths(paths: Iterable[str]) -> None:
    relative_paths = _relative_artifact_paths(paths)
    assert REQUIRED_ARTIFACT_FILES <= relative_paths
    for relative in relative_paths:
        parts = Path(relative).parts
        forbidden_parts = set(parts) & FORBIDDEN_ARTIFACT_PARTS
        # ``app.documentation`` is runtime code behind a product route, not
        # the repository's documentation source tree.
        if parts[:2] == ("app", "documentation"):
            forbidden_parts.discard("documentation")
        assert not forbidden_parts, relative
        assert not (set(parts) & FORBIDDEN_ARTIFACT_NAMES), relative
        assert "__pycache__" not in parts, relative
        assert not relative.endswith((".pyc", ".pyo", ".db", ".sqlite", ".sqlite3")), relative


def _validate_metadata(metadata: Any) -> None:
    assert metadata["Name"] == PROJECT_NAME
    assert metadata["Version"] == PROJECT_VERSION
    assert metadata["License-Expression"] == LICENSE_EXPRESSION
    assert metadata["Requires-Python"] == ">=3.14"
    assert set(metadata.get_all("Provides-Extra", [])) == {"ai", "dev", "postgres"}

    requirements = metadata.get_all("Requires-Dist", [])
    base_names = _requirement_names(
        requirement.split(";", 1)[0]
        for requirement in requirements
        if "extra ==" not in requirement
    )
    assert not (base_names & NATIVE_AI_DISTRIBUTIONS)
    for extra, expected in (("ai", NATIVE_AI_DISTRIBUTIONS), ("postgres", POSTGRES_DISTRIBUTIONS)):
        names = _requirement_names(
            requirement.split(";", 1)[0]
            for requirement in requirements
            if f'extra == "{extra}"' in requirement
        )
        assert names == expected


def validate_artifacts(sdist: Path, wheel: Path) -> None:
    for artifact, reader in ((sdist, _metadata_from_sdist), (wheel, _metadata_from_wheel)):
        metadata, names = reader(artifact)
        _validate_metadata(metadata)
        _validate_artifact_paths(names)
        print(
            f"[package-smoke] verified {artifact.name}: {len(names)} files, "
            f"{artifact.stat().st_size} bytes",
            flush=True,
        )


def _create_venv(path: Path, *, stage: str) -> Path:
    print(f"[package-smoke] {stage}: create clean venv", flush=True)
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return path / "bin" / "python"


def _install_spec(artifact: Path, extra: str | None) -> str:
    if extra is None:
        return str(artifact)
    return f"{PROJECT_NAME}[{extra}] @ {artifact.as_uri()}"


def _probe_base(python: Path, *, cwd: Path) -> dict[str, Any]:
    probe = f"""
import asyncio
import importlib.metadata
import importlib.util
import json

import httpx
import app.main
from app.schemas.profile import ProfileCreate
from app.services.firefox_policy_export import render_firefox_policies_document

assert importlib.metadata.version({PROJECT_NAME!r}) == {PROJECT_VERSION!r}
assert all(importlib.util.find_spec(name) is None for name in {sorted(NATIVE_AI_DISTRIBUTIONS)!r})
profile = ProfileCreate(name="package-smoke", flags={{"policies": {{"Homepage": {{"URL": "https://example.invalid"}}}}}})
assert render_firefox_policies_document(profile.flags) == profile.flags

async def verify():
    transport = httpx.ASGITransport(app=app.main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        root = await client.get("/")
        health = await client.get("/health")
    assert root.status_code == 200 and root.json()["version"] == {PROJECT_VERSION!r}
    assert health.status_code == 200 and health.json() == {{"status": "ok"}}
    return {{"root": root.json()["status"], "health": health.json()["status"], "profile": profile.name}}

print(json.dumps(asyncio.run(verify()), sort_keys=True))
"""
    completed = subprocess.run(
        [str(python), "-I", "-c", probe],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def _probe_extra(python: Path, *, extra: str, cwd: Path) -> None:
    if extra == "postgres":
        probe = "import asyncpg, psycopg; print(asyncpg.__version__, psycopg.__version__)"
    elif extra == "ai":
        probe = (
            "import numpy, onnxruntime, tokenizers; import app.ai.e5_runtime; "
            "print(numpy.__version__, onnxruntime.__version__, tokenizers.__version__)"
        )
    elif extra == "postgres,ai":
        probe = (
            "import asyncpg, psycopg, numpy, onnxruntime, tokenizers; "
            "import app.ai.e5_runtime; print('combined-extras-ok')"
        )
    else:  # pragma: no cover - protected by the static scenario list.
        raise ValueError(extra)
    _run([str(python), "-I", "-c", probe], cwd=cwd, stage=f"probe {extra} extra")


def run_install_smokes(sdist: Path, wheel: Path, workspace: Path) -> dict[str, Any]:
    scenarios = (
        ("base", sdist, None),
        ("postgres", wheel, "postgres"),
        ("ai", wheel, "ai"),
        ("combined", wheel, "postgres,ai"),
    )
    report: dict[str, Any] = {}
    for name, artifact, extra in scenarios:
        environment = workspace / f"{name}-venv"
        python = _create_venv(environment, stage=name)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                _install_spec(artifact, extra),
            ],
            cwd=workspace,
            stage=f"install {name} artifact",
        )
        _run([str(python), "-m", "pip", "check"], cwd=workspace, stage=f"pip check {name}")
        if extra is None:
            report[name] = _probe_base(python, cwd=workspace)
            print(
                f"[package-smoke] probe base app.main:app: {json.dumps(report[name])}", flush=True
            )
        else:
            _probe_extra(python, extra=extra, cwd=workspace)
            report[name] = {"extra": extra, "pip_check": "ok"}
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-install-smokes",
        action="store_true",
        help="Build and inspect artifacts only; intended for focused tool tests.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    validate_declared_packaging()
    with tempfile.TemporaryDirectory(prefix="bpm-package-smoke-") as temporary:
        workspace = Path(temporary)
        print(f"[package-smoke] isolated workspace: {workspace}", flush=True)
        sdist, wheel = _build_artifacts(workspace)
        validate_artifacts(sdist, wheel)
        report = {} if args.skip_install_smokes else run_install_smokes(sdist, wheel, workspace)
    print(f"package delivery smoke: OK {json.dumps(report, sort_keys=True)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
