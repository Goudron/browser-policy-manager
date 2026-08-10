#!/usr/bin/env python3
"""Install the locked BPM documentation toolchain into a repository-local cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import posixpath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = REPOSITORY_ROOT / "documentation/config/toolchain-lock.json"


class BootstrapError(RuntimeError):
    """A fail-closed toolchain bootstrap error."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def platform_id() -> str:
    machines = {"x86_64": "x86_64", "amd64": "x86_64"}
    systems = {"linux": "linux"}
    system = systems.get(platform.system().lower())
    machine = machines.get(platform.machine().lower())
    if not system or not machine:
        raise BootstrapError(
            f"unsupported documentation toolchain platform: {platform.system()}/{platform.machine()}"
        )
    return f"{system}-{machine}"


def load_lock(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BootstrapError(f"duplicate JSON key in lock: {key}")
            result[key] = value
        return result

    try:
        lock = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read toolchain lock {path}: {exc}") from exc
    if lock.get("schema_version") != 1:
        raise BootstrapError("unsupported toolchain lock schema")
    return lock


def _safe_member(name: str, expected_root: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise BootstrapError(f"unsafe archive member: {name}")
    if path.parts[0] != expected_root:
        raise BootstrapError(f"archive member is outside expected root {expected_root}: {name}")
    return path


def _safe_link(member_name: str, link_name: str, expected_root: str) -> None:
    member = PurePosixPath(member_name)
    if PurePosixPath(link_name).is_absolute():
        raise BootstrapError(f"absolute archive link is forbidden: {member_name}")
    resolved = PurePosixPath(posixpath.normpath(str(member.parent / link_name)))
    if not resolved.parts or resolved.parts[0] != expected_root or ".." in resolved.parts:
        raise BootstrapError(f"archive link escapes expected root: {member_name}")


def extract_archive(archive: Path, destination: Path, archive_format: str, root: str) -> None:
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=parent) as temp_name:
        temp = Path(temp_name)
        if archive_format == "zip":
            with zipfile.ZipFile(archive) as bundle:
                for item in bundle.infolist():
                    _safe_member(item.filename, root)
                    if (item.external_attr >> 16) & 0o170000 == 0o120000:
                        raise BootstrapError(f"symbolic link is forbidden in zip: {item.filename}")
                bundle.extractall(temp)
                for item in bundle.infolist():
                    mode = (item.external_attr >> 16) & 0o777
                    extracted_item = temp / item.filename
                    if mode and extracted_item.exists():
                        extracted_item.chmod(mode)
        elif archive_format == "tar.gz":
            with tarfile.open(archive, "r:gz") as bundle:
                for item in bundle.getmembers():
                    _safe_member(item.name, root)
                    if item.issym() or item.islnk():
                        _safe_link(item.name, item.linkname, root)
                    if item.isdev():
                        raise BootstrapError(f"special archive member is forbidden: {item.name}")
                bundle.extractall(temp, filter="data")
        else:
            raise BootstrapError(f"unsupported archive format: {archive_format}")
        extracted = temp / root
        if not extracted.is_dir():
            raise BootstrapError(f"archive does not contain expected root: {root}")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(extracted, destination)


def ensure_archive(spec: dict[str, str], archive_dir: Path, offline: bool) -> Path:
    filename = Path(urllib.parse.urlparse(spec["url"]).path).name
    target = archive_dir / f"{spec['sha256']}-{filename}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    if target.exists() and sha256(target) == spec["sha256"]:
        return target
    target.unlink(missing_ok=True)
    if offline:
        raise BootstrapError(f"locked archive is absent from offline cache: {filename}")
    temporary = target.with_suffix(target.suffix + ".part")
    temporary.unlink(missing_ok=True)
    print(f"Downloading {spec['url']}", flush=True)
    try:
        with (
            urllib.request.urlopen(spec["url"], timeout=120) as response,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
        actual = sha256(temporary)
        if actual != spec["sha256"]:
            raise BootstrapError(f"SHA-256 mismatch for {filename}: {actual}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def install_component(name: str, spec: dict[str, Any], cache: Path, offline: bool) -> Path:
    archive_spec = spec["archive"]
    archive = ensure_archive(archive_spec, cache / "archives", offline)
    destination = cache / "installs" / f"{name}-{spec['version']}"
    marker = destination / ".bpm-toolchain.json"
    expected = {"version": spec["version"], "sha256": archive_spec["sha256"]}
    if marker.is_file():
        try:
            executable = destination / spec["executable"]
            if json.loads(marker.read_text(encoding="utf-8")) == expected and os.access(
                executable, os.X_OK
            ):
                return destination
        except json.JSONDecodeError:
            pass
    extract_archive(archive, destination, archive_spec["format"], archive_spec["root"])
    if not os.access(destination / spec["executable"], os.X_OK):
        raise BootstrapError(f"archive did not provide executable {spec['executable']}")
    marker.write_text(json.dumps(expected, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def run_checked(command: list[str], *, env: dict[str, str] | None = None) -> str:
    try:
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    except OSError as exc:
        raise BootstrapError(f"cannot run {' '.join(command)}: {exc}") from exc
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    if completed.returncode:
        raise BootstrapError(f"command failed ({' '.join(command)}):\n{output}")
    return output


def install_python(lock: dict[str, Any], cache: Path, offline: bool) -> Path:
    if sys.version_info[:2] != (3, 14):
        raise BootstrapError(
            f"documentation tests require Python >=3.14,<3.15; got {platform.python_version()}"
        )
    requirements = REPOSITORY_ROOT / lock["python"]["requirements_lock"]
    wheelhouse = cache / "python-wheelhouse"
    environment = cache / "python-venv"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    if not offline:
        run_checked(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--dest",
                str(wheelhouse),
                "-r",
                str(requirements),
            ]
        )
    if environment.exists():
        shutil.rmtree(environment)
    run_checked([sys.executable, "-m", "venv", str(environment)])
    python = environment / "bin/python"
    run_checked(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "-r",
            str(requirements),
        ]
    )
    return python


def smoke_build(
    dita_home: Path,
    java_home: Path,
    cache: Path,
    *,
    expected_java_version: str,
    expected_dita_version: str,
) -> None:
    dita = dita_home / "bin/dita"
    java = java_home / "bin/java"
    if not dita.is_file() or not java.is_file():
        raise BootstrapError("locked DITA-OT or Java executable is missing")
    env = os.environ.copy()
    env.update({"JAVA_HOME": str(java_home), "PATH": f"{java_home / 'bin'}:{env.get('PATH', '')}"})
    if expected_java_version not in run_checked([str(java), "-version"], env=env):
        raise BootstrapError("installed Java version does not match lock")
    if expected_dita_version not in run_checked([str(dita), "--version"], env=env):
        raise BootstrapError("installed DITA-OT version does not match lock")
    with tempfile.TemporaryDirectory(prefix="smoke-", dir=cache) as temp_name:
        temp = Path(temp_name)
        (temp / "topic.dita").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">\n'
            '<topic id="smoke" xml:lang="en"><title>Offline smoke</title>'
            "<body><p>Locked toolchain.</p></body></topic>\n",
            encoding="utf-8",
        )
        (temp / "map.ditamap").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">\n'
            '<map xml:lang="en"><title>Smoke</title><topicref href="topic.dita"/></map>\n',
            encoding="utf-8",
        )
        run_checked(
            [
                str(dita),
                "--input",
                str(temp / "map.ditamap"),
                "--format",
                "html5",
                "--output",
                str(temp / "out"),
            ],
            env=env,
        )
        if not (temp / "out/topic.html").is_file():
            raise BootstrapError("DITA-OT smoke build produced no HTML topic")


def bootstrap(lock_path: Path, offline: bool, skip_python: bool) -> None:
    lock = load_lock(lock_path)
    current_platform = platform_id()
    if current_platform not in lock["supported_platforms"]:
        raise BootstrapError(f"platform is not present in lock: {current_platform}")
    cache = REPOSITORY_ROOT / lock["cache_directory"]
    cache.mkdir(parents=True, exist_ok=True)
    java_spec = lock["components"]["java"]
    platform_spec = java_spec["platforms"][current_platform]
    java_home = install_component(
        "temurin-jre",
        {"version": java_spec["version"], **platform_spec},
        cache,
        offline,
    )
    dita_spec = lock["components"]["dita_ot"]
    dita_home = install_component("dita-ot", dita_spec, cache, offline)
    smoke_build(
        dita_home,
        java_home,
        cache,
        expected_java_version=java_spec["version"].split("+", 1)[0],
        expected_dita_version=dita_spec["version"],
    )
    if not skip_python:
        install_python(lock, cache, offline)
    print(f"Documentation toolchain ready in {cache.relative_to(REPOSITORY_ROOT)}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--offline", action="store_true", help="reuse cache without network access")
    parser.add_argument("--skip-python", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        bootstrap(args.lock.resolve(), args.offline, args.skip_python)
    except BootstrapError as exc:
        print(f"documentation toolchain bootstrap failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
