# app/core/schemas_loader.py
"""
Schema loader for Firefox Enterprise policies.

- Discovers JSON Schemas under app/schemas/.
- Provides explicit mapping for supported profiles:
  * "esr-140"      -> firefox-esr140.json
  * "release-144"  -> firefox-release.json

No Beta, ESR 115 or ESR 128 are supported in Sprint F.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

# Explicit mapping for Sprint F scope.
PROFILE_TO_SCHEMA_FILE: Dict[str, str] = {
    "esr-140": "firefox-esr140.json",
    "release-144": "firefox-release.json",
}


class SchemaNotFoundError(FileNotFoundError):
    """Raised when a requested schema file cannot be found."""


class UnsupportedProfileError(ValueError):
    """Raised when an unsupported profile key was requested."""


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=16)
def load_schema(profile: str) -> Dict[str, Any]:
    """
    Load a JSON Schema for a given profile key.

    Parameters
    ----------
    profile : str
        One of: "esr-140", "release-144".

    Returns
    -------
    Dict[str, Any]
        Parsed JSON Schema.

    Raises
    ------
    UnsupportedProfileError
        If profile is not known in current sprint scope.
    SchemaNotFoundError
        If schema file is missing on disk.
    """
    if profile not in PROFILE_TO_SCHEMA_FILE:
        raise UnsupportedProfileError(
            f"Unsupported profile '{profile}'. Supported: {', '.join(PROFILE_TO_SCHEMA_FILE)}"
        )

    schema_file = SCHEMAS_DIR / PROFILE_TO_SCHEMA_FILE[profile]
    if not schema_file.exists():
        raise SchemaNotFoundError(f"Schema file not found: {schema_file}")

    return _read_json(schema_file)


def available_profiles() -> Dict[str, str]:
    """
    Return mapping of supported profiles to their schema filenames.

    Notes
    -----
    This reflects Sprint F policy: ESR 140 and Release 144 only.
    """
    return dict(PROFILE_TO_SCHEMA_FILE)
