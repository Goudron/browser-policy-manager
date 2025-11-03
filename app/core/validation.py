"""
Validation utilities for Browser Policy Manager.

- Wraps JSON Schema validation using fastjsonschema.
- Uses app.core.schemas_loader to obtain upstream Mozilla schemas.
- Exposes a small OO wrapper (PolicySchemaValidator) used by API and tests.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any

import fastjsonschema

from app.core.schemas_loader import (
    SchemaNotFoundError,
    UnsupportedProfileError,
    load_schema,
)
from app.core.schemas_loader import (
    available_profiles as _available_profiles,
)


class ValidationError(Exception):
    """Raised when validation cannot proceed due to environment issues."""


class PolicySchemaValidator:
    """
    Thin validator around a compiled JSON Schema.

    Usage:
        v = PolicySchemaValidator("esr-140")
        ok, errors = v.validate({"some": "doc"})
    """

    def __init__(self, profile: str) -> None:
        try:
            schema: dict[str, Any] = load_schema(profile)
        except (UnsupportedProfileError, SchemaNotFoundError) as err:
            raise ValidationError(str(err)) from err

        # Compile fastjsonschema validator once per instance
        self._validate_fn: Callable[[Any], None] = fastjsonschema.compile(schema)

    def validate(self, document: Any) -> tuple[bool, list[str]]:
        """
        Validate a JSON-like document against the compiled schema.

        Returns:
            (ok, errors)
            ok: True if document is valid.
            errors: list of human-readable messages if not valid.
        """
        try:
            self._validate_fn(document)
            return True, []
        except fastjsonschema.JsonSchemaException as err:
            # Keep a single-line message; tests only check ok/status, but this helps debugging.
            return False, [str(err)]


@lru_cache(maxsize=1)
def supported_profiles() -> list[str]:
    """
    Return the list of supported profile keys (cached).

    We expose list[str] explicitly (not a dict), which aligns with actual usage in tests.
    """
    return list(_available_profiles())
