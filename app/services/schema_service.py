from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")


@lru_cache(maxsize=32)
def list_schemas() -> list[str]:
    """Return available schema basenames without extension (sorted)."""
    files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
    return sorted(os.path.splitext(f)[0] for f in files)


@lru_cache(maxsize=32)
def get_schema(version: str) -> dict[str, Any]:
    """Load one schema by version name (basename without .json)."""
    path = os.path.join(SCHEMAS_DIR, f"{version}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema not found: {version}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_boolean_policy_keys(version: str) -> list[str]:
    """
    Convenience: return list of boolean policies for quick flag UI.
    """
    schema = get_schema(version)
    policies = schema.get("policies", {})
    return [k for k, v in policies.items() if (isinstance(v, dict) and v.get("type") == "boolean")]
