from __future__ import annotations

from typing import Any

ALLOWED_TOP = {"policies"}


def normalize_policies(data: Any) -> tuple[dict[str, Any], list[str]]:
    """Нормализуем входной JSON Firefox policies."""
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {}, ["Input JSON must be an object (dict)"]

    if "policies" in data and isinstance(data["policies"], dict):
        policies = data["policies"]
    else:
        policies = data
        if not isinstance(policies, dict):
            return {}, ["JSON root is not a dict"]

    if not policies:
        warnings.append("Policies object is empty")

    return policies, warnings
