"""
Schema validation service for Browser Policy Manager.

Scans app/schemas/ for JSON or YAML schemas and validates policy documents.
Supported file extensions: .json, .yaml, .yml
Filename patterns:
  - *release*.json|yaml|yml      -> (channel="release", version=None)
  - *esr_<digits>*.json|yaml|yml -> (channel="esr",    version="<digits>")
"""

from __future__ import annotations

import json
import re
from importlib import resources
from typing import Any, Dict, Optional, Tuple

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

# PyYAML подгружаем динамически в _load_yaml


SchemaKey = Tuple[str, Optional[str]]  # (channel, version|None)
_INDEX: Dict[SchemaKey, dict] = {}

_RE_ESR = re.compile(r"\besr[_-]?(?P<ver>\d+)\b", re.IGNORECASE)
_RE_REL = re.compile(r"\brelease\b", re.IGNORECASE)
_ALLOWED_EXT = (".json", ".yaml", ".yml")


def _load_yaml(text: str) -> Optional[dict]:
    """Lazy-load PyYAML and parse mapping; return None if not a mapping."""
    try:
        import importlib

        yaml = importlib.import_module("yaml")
        data = yaml.safe_load(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_mapping(entry: Any) -> Optional[dict]:
    """Load schema file as dict (JSON or YAML)."""
    name = str(entry.name).lower()
    text = entry.read_text(encoding="utf-8")
    if name.endswith(".json"):
        try:
            mapping = json.loads(text)
        except Exception:
            return None
        return mapping if isinstance(mapping, dict) else None
    if name.endswith((".yaml", ".yml")):
        return _load_yaml(text)
    return None


def _classify(name: str) -> Optional[SchemaKey]:
    """Infer (channel, version) from filename."""
    if _RE_REL.search(name):
        return ("release", None)
    m = _RE_ESR.search(name)
    if m:
        return ("esr", m.group("ver"))
    return None


def _scan_schemas() -> None:
    """Scan app/schemas and build the in-memory index."""
    global _INDEX
    _INDEX.clear()

    pkg = "app.schemas"
    folder: Any = resources.files(pkg)

    for entry in folder.iterdir():
        name = str(entry.name).lower()
        if not name.endswith(_ALLOWED_EXT):
            continue

        key = _classify(name) or ("release", None)
        mapping = _load_mapping(entry)
        if not isinstance(mapping, dict):
            continue

        _INDEX[key] = mapping


def available() -> Dict[SchemaKey, str]:
    """Return {(ch, ver): 'ch:ver|stable'}."""
    if not _INDEX:
        _scan_schemas()
    return {k: f"{k[0]}:{k[1] or 'stable'}" for k in _INDEX}


def validate_policy(
    doc: dict,
    *,
    channel: Optional[str] = None,
    version: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Validate the document against the selected schema."""
    if not _INDEX:
        _scan_schemas()

    ch = (channel or str(doc.get("channel") or "release")).lower()
    ver = (
        version
        if version is not None
        else (str(doc.get("version")) if doc.get("version") is not None else None)
    )
    key: SchemaKey = (ch, ver if ch == "esr" else None)

    if key not in _INDEX:
        labels = ", ".join(sorted(available().values()))
        return (
            False,
            f"Schema not found for channel={ch}, version={ver or 'stable'}. "
            f"Available: {labels}",
        )

    schema = _INDEX[key]
    try:
        Draft202012Validator(schema).validate(doc)
        return True, None
    except ValidationError as e:
        path = "/".join(map(str, e.path)) or "#"
        return False, f"{e.message} @ {path}"

    # Страховочный возврат для mypy (логически сюда не дойдём)
    return False, "Validation failed (unexpected path)"
