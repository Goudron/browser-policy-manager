#!/usr/bin/env python3
"""Provision checksum-pinned Mozilla inputs for offline schema conversion tests.

The converter's source cache deliberately remains outside Git.  This command
downloads only the immutable tag files declared in its manifest, verifies each
payload before atomically publishing it to that cache, and re-verifies cached
files on every later run.  The schema conversion itself remains offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "tools" / "firefox_schema_inputs_manifest_0_9_4.json"
DEFAULT_DESTINATION = REPO_ROOT / "data" / "upstream" / "policy-templates"
CHUNK_SIZE = 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class ProvisioningError(RuntimeError):
    """The source manifest, download, or cached input was invalid."""


@dataclass(frozen=True)
class InputFile:
    name: str
    url: str
    sha256: str


@dataclass(frozen=True)
class InputSet:
    source_tag: str
    upstream_tag: str
    files: tuple[InputFile, ...]


def _required_string(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ProvisioningError(f"{context} requires a non-empty string {key!r}")
    return value


def load_manifest(path: Path = DEFAULT_MANIFEST) -> tuple[InputSet, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProvisioningError(f"Cannot read schema-input manifest {path}: {error}") from error
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "inputs"}:
        raise ProvisioningError("Schema-input manifest requires only schema_version and inputs")
    if payload["schema_version"] != 1 or not isinstance(payload["inputs"], list):
        raise ProvisioningError(
            "Schema-input manifest requires schema_version 1 and an inputs list"
        )

    sets: list[InputSet] = []
    for index, item in enumerate(payload["inputs"]):
        context = f"inputs[{index}]"
        if not isinstance(item, dict) or set(item) != {"source_tag", "upstream_tag", "files"}:
            raise ProvisioningError(f"{context} has invalid fields")
        files_payload = item["files"]
        if not isinstance(files_payload, list) or not files_payload:
            raise ProvisioningError(f"{context}.files must be a non-empty list")
        files: list[InputFile] = []
        for file_index, file_payload in enumerate(files_payload):
            file_context = f"{context}.files[{file_index}]"
            if not isinstance(file_payload, dict) or set(file_payload) != {"name", "url", "sha256"}:
                raise ProvisioningError(f"{file_context} has invalid fields")
            digest = _required_string(file_payload, "sha256", file_context)
            if not SHA256_RE.fullmatch(digest):
                raise ProvisioningError(f"{file_context}.sha256 must be a lowercase SHA-256 digest")
            name = _required_string(file_payload, "name", file_context)
            if Path(name).name != name:
                raise ProvisioningError(f"{file_context}.name must be a file name, not a path")
            files.append(
                InputFile(
                    name=name,
                    url=_required_string(file_payload, "url", file_context),
                    sha256=digest,
                )
            )
        if {file.name for file in files} != {"policy-templates.md", "linux-policies.json"}:
            raise ProvisioningError(
                f"{context}.files must declare the two converter inputs exactly"
            )
        sets.append(
            InputSet(
                source_tag=_required_string(item, "source_tag", context),
                upstream_tag=_required_string(item, "upstream_tag", context),
                files=tuple(files),
            )
        )
    if not sets or len({item.upstream_tag for item in sets}) != len(sets):
        raise ProvisioningError("Schema-input manifest requires unique upstream tags")
    return tuple(sets)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(path: Path, expected: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ProvisioningError(f"Checksum mismatch for {path}: expected {expected}, got {actual}")


def _download_verified(spec: InputFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", suffix=".part", delete=False
    ) as stream:
        temporary = Path(stream.name)
        print(f"Downloading {spec.url}", flush=True)
        try:
            with urlopen(spec.url, timeout=120) as response:  # nosec B310: manifest-pinned URL
                while chunk := response.read(CHUNK_SIZE):
                    stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())
            _verify(temporary, spec.sha256)
            os.replace(temporary, destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    print(f"Verified {destination}: {spec.sha256}", flush=True)


def provision(input_sets: tuple[InputSet, ...], destination_root: Path) -> None:
    for input_set in input_sets:
        print(
            f"Preparing Mozilla policy-templates {input_set.upstream_tag} ({input_set.source_tag})",
            flush=True,
        )
        for spec in input_set.files:
            destination = destination_root / input_set.upstream_tag / spec.name
            if destination.is_file():
                _verify(destination, spec.sha256)
                print(f"Reusing checksum-verified {destination}", flush=True)
            else:
                _download_verified(spec, destination)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--verify", action="store_true", help="Require already provisioned inputs")
    args = parser.parse_args(argv)
    try:
        input_sets = load_manifest(args.manifest)
        if args.verify:
            for input_set in input_sets:
                for spec in input_set.files:
                    _verify(args.destination / input_set.upstream_tag / spec.name, spec.sha256)
            print("Firefox schema inputs are checksum-verified", flush=True)
        else:
            provision(input_sets, args.destination)
    except (OSError, ProvisioningError) as error:
        print(f"Firefox schema-input provisioning failed: {error}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
