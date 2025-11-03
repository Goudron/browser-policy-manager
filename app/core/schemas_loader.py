# app/core/schemas_loader.py
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

# Map profiles to file names on disk
_PROFILE_MAP: dict[str, Path] = {
    "esr-140": SCHEMAS_DIR / "firefox-esr140.json",
    "release-144": SCHEMAS_DIR / "firefox-release.json",
}


class UnsupportedProfileError(Exception):
    pass


class SchemaNotFoundError(Exception):
    pass


def available_profiles() -> dict[str, str]:
    """
    Return a dict mapping profile key -> filename (string), for tests.

    Tests expect a dict (not dict_keys), so we expose a simple mapping.
    """
    return {k: v.name for k, v in _PROFILE_MAP.items()}


@lru_cache(maxsize=16)
def load_schema(profile: str) -> dict[str, Any]:
    """
    Load JSON schema by profile key strictly from local files.

    Offline-by-default for tests: we DO NOT try to fetch from network here.
    """
    if profile not in _PROFILE_MAP:
        raise UnsupportedProfileError(
            f"Unsupported profile '{profile}'. Supported: {', '.join(_PROFILE_MAP)}"
        )

    path = _PROFILE_MAP[profile]
    if not path.exists():
        raise SchemaNotFoundError(f"Schema file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
