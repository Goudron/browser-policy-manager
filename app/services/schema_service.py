# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
"""
Schema validation service for Browser Policy Manager.

Loads JSON schemas from app/schemas/ (e.g. firefox_esr_115.json, firefox_release.json)
and validates incoming policy documents against the correct schema.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple

from importlib import resources

# NOTE:
# jsonschema often lacks bundled type stubs; VS Code may show a type-stub warning.
# The pyright directive at the top suppresses that benign warning.
try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "The 'jsonschema' package is required. Install it with:\n\n"
        "    pip install 'jsonschema>=4.23'\n"
    ) from exc


# Key for the schema index: (channel, version or None)
SchemaKey = Tuple[str, Optional[str]]

# Internal schema registry
_INDEX: Dict[SchemaKey, dict] = {}

# Expected filenames in app/schemas/:
#   firefox_release.json
#   firefox_esr_115.json
#   firefox_esr_128.json
_FILE_RE = re.compile(
    r"firefox_(?P<channel>esr|release)(?:_(?P<version>\d+))?\.json$",
    re.IGNORECASE,
)


def _scan_schemas() -> None:
    """Scan app/schemas for JSON schema files and build an in-memory index."""
    global _INDEX
    _INDEX.clear()

    pkg = "app.schemas"
    try:
        # Cast to Any to silence strict type checkers complaining about Traversable
        folder: Any = resources.files(pkg)  # type: ignore[attr-defined]
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Cannot access schemas package '{pkg}': {e}") from e

    for entry in folder.iterdir():
        name = str(entry.name).lower()
        if not name.endswith(".json"):
            continue

        match = _FILE_RE.match(name)
        if not match:
            # Skip unexpected filenames to avoid accidental misloads
            continue

        channel = match.group("channel").lower()
        version = match.group("version") if channel == "esr" else None

        with entry.open("r", encoding="utf-8") as f:
            schema = json.load(f)

        _INDEX[(channel, version)] = schema


def available() -> Dict[SchemaKey, str]:
    """Return a dict of available schemas: {(ch, ver): 'ch:ver|stable'}."""
    if not _INDEX:
        _scan_schemas()

    return {k: f"{k[0]}:{k[1] or 'stable'}" for k in _INDEX}


def validate_policy(
    doc: dict,
    *,
    channel: Optional[str] = None,
    version: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate a policy document against the appropriate schema.

    Priority of schema selection:
      1. Explicit parameters channel/version (if provided)
      2. Fields in the document: doc['channel'], doc['version']
      3. Fallback: ("release", None)

    Returns:
        (ok: bool, error_message: str | None)
    """
    if not _INDEX:
        _scan_schemas()

    ch = (channel or str(doc.get("channel") or "release")).lower()
    ver = (
        version
        if version is not None
        else (str(doc.get("version")) if doc.get("version") is not None else None)
    )

    # For release channel version is ignored (always stable)
    key: SchemaKey = (ch, ver if ch == "esr" else None)

    if key not in _INDEX:
        avail = ", ".join(sorted(available().values()))
        return (
            False,
            f"Schema not found for channel={ch}, version={ver or 'stable'}. "
            f"Available: {avail}",
        )

    schema = _INDEX[key]
    try:
        Draft202012Validator(schema).validate(doc)
        return True, None
    except ValidationError as e:
        path = "/".join(map(str, e.path)) or "#"
        return False, f"{e.message} @ {path}"
