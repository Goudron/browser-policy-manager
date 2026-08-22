#!/usr/bin/env python3
"""Fail-closed dependency audits and transient CycloneDX release evidence.

The repository deliberately has no Python lockfile.  Instead, every run creates
two clean, fully resolved environments: the shippable base and the complete
development/optional-extra contour.  Their audit reports and SBOMs are evidence
for the current run only, so the output directory is ignored by Git.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "artifacts" / "dependency-audit"
DEFAULT_SUPPRESSIONS = REPO_ROOT / "tools" / "dependency_audit_suppressions.json"
# Do not resolve the interpreter symlink: a venv's ``python`` points to the
# system binary while its sibling console scripts live in the venv's own bin/.
TOOL_BIN_DIR = Path(sys.executable).parent
PIP_AUDIT = TOOL_BIN_DIR / "pip-audit"
CYCLONEDX_PY = TOOL_BIN_DIR / "cyclonedx-py"
PIP_BOOTSTRAP_VERSION = "26.2.1"


class SuppressionError(ValueError):
    """Raised when a proposed advisory exception is incomplete or expired."""


@dataclass(frozen=True)
class Suppression:
    advisory: str
    rationale: str
    owner: str
    expires_on: date


def load_suppressions(path: Path) -> tuple[Suppression, ...]:
    """Load explicit Python advisory exceptions and reject unsafe metadata."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("version") != 1:
        raise SuppressionError(f"{path} must be a version 1 object")

    allowed_keys = {"version", "python", "npm"}
    unknown = set(document) - allowed_keys
    if unknown:
        raise SuppressionError(f"{path} has unsupported keys: {sorted(unknown)}")

    python_entries = document.get("python", [])
    npm_entries = document.get("npm", [])
    if not isinstance(python_entries, list) or not isinstance(npm_entries, list):
        raise SuppressionError(f"{path} python and npm entries must be lists")
    if npm_entries:
        raise SuppressionError(
            "npm audit has no safe per-advisory suppression interface; resolve npm advisories instead"
        )

    today = datetime.now(UTC).date()
    suppressions: list[Suppression] = []
    for index, entry in enumerate(python_entries):
        if not isinstance(entry, dict):
            raise SuppressionError(f"python suppression #{index} must be an object")
        required = {"advisory", "rationale", "owner", "expires_on"}
        if set(entry) != required or not all(
            isinstance(entry[key], str) and entry[key].strip() for key in required
        ):
            raise SuppressionError(
                f"python suppression #{index} needs only non-empty {sorted(required)}"
            )
        try:
            expires_on = date.fromisoformat(entry["expires_on"])
        except ValueError as error:
            raise SuppressionError(f"python suppression #{index} has invalid expires_on") from error
        if expires_on < today:
            raise SuppressionError(f"python suppression #{index} expired on {expires_on}")
        suppressions.append(
            Suppression(
                advisory=entry["advisory"],
                rationale=entry["rationale"],
                owner=entry["owner"],
                expires_on=expires_on,
            )
        )
    return tuple(suppressions)


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print(f"$ {shlex.join(command)}", flush=True)
    subprocess.run(command, check=True, cwd=REPO_ROOT, env=env)


def _resolved_requirements(python: Path, output_path: Path) -> None:
    """Record exact installed third-party versions for a non-mutating audit."""
    result = subprocess.run(
        [str(python), "-m", "pip", "list", "--format=json"],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    packages = json.loads(result.stdout)
    if not isinstance(packages, list):
        raise RuntimeError("pip did not return a package list")
    requirements = sorted(
        f"{package['name']}=={package['version']}"
        for package in packages
        if isinstance(package, dict)
        and package.get("name", "").lower() != "browser-policy-manager"
        and isinstance(package.get("name"), str)
        and isinstance(package.get("version"), str)
    )
    output_path.write_text("\n".join(requirements) + "\n", encoding="utf-8")


def _build_environment(root: Path, name: str, install_spec: str) -> Path:
    environment = root / name
    _run([sys.executable, "-m", "venv", str(environment)])
    python = environment / "bin" / "python"
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--quiet",
            "--upgrade",
            f"pip=={PIP_BOOTSTRAP_VERSION}",
        ]
    )
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--quiet",
            install_spec,
        ]
    )
    _run([str(python), "-m", "pip", "check"])
    return python


def _python_evidence(
    *,
    name: str,
    python: Path,
    artifact_dir: Path,
    suppressions: tuple[Suppression, ...],
) -> None:
    audit_path = artifact_dir / f"python-{name}-pip-audit.json"
    sbom_path = artifact_dir / f"python-{name}.cdx.json"
    requirements_path = artifact_dir / f"python-{name}-resolved-requirements.txt"
    _resolved_requirements(python, requirements_path)
    audit_command = [
        str(PIP_AUDIT),
        "--requirement",
        str(requirements_path),
        "--no-deps",
        "--strict",
        "--format",
        "json",
        "--output",
        str(audit_path),
    ]
    for suppression in suppressions:
        audit_command.extend(["--ignore-vuln", suppression.advisory])
    _run(audit_command)
    _run(
        [
            str(CYCLONEDX_PY),
            "environment",
            str(python),
            "--pyproject",
            str(REPO_ROOT / "pyproject.toml"),
            "--mc-type",
            "application",
            "--output-reproducible",
            "--of",
            "JSON",
            "--output-file",
            str(sbom_path),
        ]
    )
    components = len(json.loads(sbom_path.read_text(encoding="utf-8")).get("components", []))
    print(f"Python {name}: {components} SBOM components; audit passed", flush=True)


def _npm_evidence(artifact_dir: Path) -> None:
    audit_path = artifact_dir / "npm-audit.json"
    sbom_path = artifact_dir / "npm.cdx.json"
    environment = dict(os.environ)
    environment.pop("NODE_ENV", None)
    # Capture audit JSON without shell redirection so command failures remain fail-closed.
    audit_command = ["npm", "audit", "--package-lock-only", "--json"]
    print(f"$ {shlex.join(audit_command)}", flush=True)
    result = subprocess.run(
        audit_command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )
    audit_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="", flush=True)
        raise subprocess.CalledProcessError(result.returncode, result.args)

    _run(
        [
            "node_modules/.bin/cyclonedx-npm",
            "--package-lock-only",
            "--mc-type",
            "application",
            "--output-reproducible",
            "--of",
            "JSON",
            "--output-file",
            str(sbom_path),
            "package.json",
        ],
        env=environment,
    )
    components = len(json.loads(sbom_path.read_text(encoding="utf-8")).get("components", []))
    print(f"npm: {components} SBOM components; audit passed", flush=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--suppressions", type=Path, default=DEFAULT_SUPPRESSIONS)
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-npm", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    suppressions = load_suppressions(args.suppressions)
    print(f"Dependency audit evidence: {artifact_dir}", flush=True)
    total_components = (0 if args.skip_python else 2) + (0 if args.skip_npm else 1)
    completed_components = 0

    if not args.skip_python:
        with tempfile.TemporaryDirectory(prefix="bpm-dependency-audit-") as temporary:
            root = Path(temporary)
            print(
                f"Dependency audit: component {completed_components + 1}/{total_components} — Python base",
                flush=True,
            )
            base_python = _build_environment(root, "base", ".")
            _python_evidence(
                name="base",
                python=base_python,
                artifact_dir=artifact_dir,
                suppressions=suppressions,
            )
            completed_components += 1
            print(
                f"Dependency audit: completed {completed_components}/{total_components} — Python base",
                flush=True,
            )
            print(
                f"Dependency audit: component {completed_components + 1}/{total_components} — Python all extras",
                flush=True,
            )
            all_extras_python = _build_environment(root, "all-extras", ".[dev,postgres,ai]")
            _python_evidence(
                name="all-extras",
                python=all_extras_python,
                artifact_dir=artifact_dir,
                suppressions=suppressions,
            )
            completed_components += 1
            print(
                f"Dependency audit: completed {completed_components}/{total_components} — Python all extras",
                flush=True,
            )

    if not args.skip_npm:
        binary = REPO_ROOT / "node_modules" / ".bin" / "cyclonedx-npm"
        if not binary.is_file():
            raise RuntimeError(
                "npm dependencies are absent; run `npm ci` before `make dependency-audit`"
            )
        print(
            f"Dependency audit: component {completed_components + 1}/{total_components} — npm lock and SBOM",
            flush=True,
        )
        _npm_evidence(artifact_dir)
        completed_components += 1
        print(
            f"Dependency audit: completed {completed_components}/{total_components} — npm lock and SBOM",
            flush=True,
        )

    print(
        f"Dependency audits and CycloneDX SBOM generation passed ({completed_components}/{total_components})",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
