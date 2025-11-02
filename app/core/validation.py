# app/core/validation.py
"""
Unified validation for Firefox Enterprise policies.

- Builds jsonschema validators per supported profile.
- Validates arbitrary policy documents against correct schema.
- Enforces object type at the top-level to satisfy enterprise policy expectations
  and test suite requirements even if a schema does not explicitly declare it.
"""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError  # keep test expectation

from .schemas_loader import available_profiles, load_schema


class PolicySchemaValidator:
    """
    Policy validator that uses Sprint F schema scope:
      - "esr-140"
      - "release-144"
    """

    def __init__(self, profile: str) -> None:
        self.profile = profile
        schema: dict[str, Any] = load_schema(profile)
        # Build validator once for performance
        self._validator = Draft202012Validator(schema)

    @property
    def supported(self) -> dict[str, str]:
        """Return supported profile -> file mapping."""
        return available_profiles()

    def validate(self, data: Any) -> None:
        """
        Validate given document in-place.

        Parameters
        ----------
        data : Any
            Policy document (expected to be a JSON-like mapping/object).

        Raises
        ------
        ValidationError
            If document does not conform to the profile schema or is not an object.
        """
        # Enforce object top-level independently of schema looseness.
        if not isinstance(data, dict):
            raise ValidationError("Top-level policy must be a JSON object")

        # Delegate to jsonschema validator.
        self._validator.validate(data)
