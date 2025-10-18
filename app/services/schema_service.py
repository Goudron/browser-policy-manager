from __future__ import annotations

from typing import Any, Dict, List, Tuple, TypedDict

from jsonschema import Draft202012Validator, ValidationError


class SchemaInfo(TypedDict):
    channel: str
    version: str


# Minimal schema registry used by tests and /api/v1 endpoints.
# We expose one ESR-like schema version.
_SCHEMAS_LIST: List[SchemaInfo] = [{"channel": "esr", "version": "firefox-ESR"}]

_SCHEMAS_MAP: Dict[str, Dict[str, Any]] = {
    "firefox-ESR": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "policies": {
                "type": "object",
                "additionalProperties": True,
            }
        },
        "required": ["policies"],
        "additionalProperties": True,
    }
}


def available() -> Dict[str, List[SchemaInfo]]:
    """
    Public API expected by tests:
    return a dict with key 'items' that is a list of {channel, version}.
    """
    return {"items": list(_SCHEMAS_LIST)}


def available_list() -> List[SchemaInfo]:
    """
    Internal helper for code paths that want just the list.
    """
    return list(_SCHEMAS_LIST)


def _find_schema(version: str) -> Dict[str, Any]:
    schema = _SCHEMAS_MAP.get(version)
    if schema is None:
        # fallback to the first known schema
        schema = _SCHEMAS_MAP[_SCHEMAS_LIST[0]["version"]]
    return schema


def validate_doc(doc: Dict[str, Any], *, version: str = "firefox-ESR") -> Tuple[bool, List[str]]:
    """Validate given document against known schema."""
    schema = _find_schema(version)
    validator = Draft202012Validator(schema)
    errors: List[str] = []
    for err in validator.iter_errors(doc):
        if isinstance(err, ValidationError):
            errors.append(err.message)
        else:
            errors.append(str(err))
    return (len(errors) == 0, errors)


# -------------------------------------------------------------------------
# Backward-compatible alias for old API usage
# -------------------------------------------------------------------------
validate_policy = validate_doc
