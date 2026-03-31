from __future__ import annotations

from typing import Any

from jsonschema import FormatChecker
from jsonschema.validators import validator_for

from app.core.schemas_loader import load_schema


class PolicySchemaValidator:
    """
    Thin wrapper around jsonschema validator with project-specific schema loading.
    We intentionally re-export and raise jsonschema.exceptions.ValidationError
    so tests can assert on that exact type.
    """

    def __init__(self, profile: str) -> None:
        schema: dict[str, Any] = load_schema(profile)
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        self._validator = validator_class(schema, format_checker=FormatChecker())

    def validate(self, document: Any) -> None:
        """
        Validate a single policy document against the JSON schema.

        Raises:
            ValidationError (from jsonschema): if validation fails.
        """
        # Let jsonschema raise its own ValidationError directly.
        self._validator.validate(document)
