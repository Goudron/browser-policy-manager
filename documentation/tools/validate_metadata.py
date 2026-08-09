#!/usr/bin/env python3
"""Validate BPM documentation conditional metadata against its maintained vocabulary."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VOCABULARY = REPOSITORY_ROOT / "documentation/config/metadata-vocabulary.json"
DEFAULT_SOURCES = (
    REPOSITORY_ROOT / "documentation/src/dita",
    REPOSITORY_ROOT / "documentation/src/shared",
    REPOSITORY_ROOT / "documentation/src/generated/firefox",
)
GROUP_PATTERN = re.compile(r"([a-z][a-z0-9-]*)\(([^()]*)\)")


class MetadataError(RuntimeError):
    """Invalid metadata configuration or source."""


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise MetadataError(f"duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise MetadataError(f"cannot read metadata vocabulary {path}: {exc}") from exc


def _registry_values(spec: dict[str, Any]) -> set[str]:
    source = REPOSITORY_ROOT / spec["source"]
    if source.suffix == ".json":
        document = load_json(source)
        try:
            return {item[spec["identity_field"]] for item in document[spec["collection"]]}
        except (KeyError, TypeError) as exc:
            raise MetadataError(f"invalid registry contract in {source}") from exc
    if source.suffix == ".md":
        pattern = re.compile(rf"^\| `({spec['table_identity_pattern']})` \|", re.MULTILINE)
        values = set(pattern.findall(source.read_text(encoding="utf-8")))
        if not values:
            raise MetadataError(f"no registry identities found in {source}")
        return values
    raise MetadataError(f"unsupported registry source: {source}")


def load_vocabulary(path: Path = DEFAULT_VOCABULARY) -> dict[str, Any]:
    vocabulary = load_json(path)
    if vocabulary.get("schema_version") != 1 or vocabulary.get("dita_version") != "1.3":
        raise MetadataError("unsupported metadata vocabulary schema or DITA version")
    vocabulary["registry_values"] = {
        group: _registry_values(spec) for group, spec in vocabulary["otherprops_groups"].items()
    }
    return vocabulary


def _context(element: ET.Element) -> str:
    identity = element.attrib.get("id")
    return f"<{element.tag}{f' id={identity!r}' if identity else ''}>"


def _validate_otherprops(value: str, vocabulary: dict[str, Any], context: str) -> list[str]:
    errors: list[str] = []
    matches = list(GROUP_PATTERN.finditer(value))
    residue = GROUP_PATTERN.sub("", value)
    if residue.strip() or not matches:
        return [f"{context}: otherprops must use group(value) syntax"]
    registries = vocabulary["registry_values"]
    for match in matches:
        group, raw_values = match.groups()
        if group not in registries:
            errors.append(f"{context}: unknown otherprops group {group!r}")
            continue
        values = raw_values.split()
        if not values:
            errors.append(f"{context}: empty otherprops group {group!r}")
            continue
        unknown = sorted(set(values) - registries[group])
        if unknown:
            errors.append(f"{context}: unknown {group} value(s): {', '.join(unknown)}")
    return errors


def validate_xml(path: Path, vocabulary: dict[str, Any]) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"{path}: invalid XML: {exc}"]
    errors: list[str] = []
    fixed = {name: set(values) for name, values in vocabulary["attributes"].items()}
    for element in root.iter():
        context = f"{path}:{_context(element)}"
        for attribute, allowed in fixed.items():
            if attribute not in element.attrib:
                continue
            values = element.attrib[attribute].split()
            unknown = sorted(set(values) - allowed)
            if unknown:
                errors.append(f"{context}: unknown {attribute} value(s): {', '.join(unknown)}")
        if "otherprops" in element.attrib:
            errors.extend(_validate_otherprops(element.attrib["otherprops"], vocabulary, context))
    return errors


def source_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if candidate.suffix in {".dita", ".ditamap"}
            )
        elif path.suffix in {".dita", ".ditamap"}:
            files.append(path)
        else:
            raise MetadataError(f"not a DITA source or directory: {path}")
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=list(DEFAULT_SOURCES))
    parser.add_argument("--vocabulary", type=Path, default=DEFAULT_VOCABULARY)
    args = parser.parse_args()
    try:
        vocabulary = load_vocabulary(args.vocabulary.resolve())
        files = source_files([path.resolve() for path in args.paths])
    except MetadataError as exc:
        print(f"metadata validation failed: {exc}", file=sys.stderr)
        return 2
    errors = [error for path in files for error in validate_xml(path, vocabulary)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated conditional metadata in {len(files)} DITA source files.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
