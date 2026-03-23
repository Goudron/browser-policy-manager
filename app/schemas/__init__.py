"""
Schemas package.

This package exposes the SchemaManager API at the app.schemas top-level
so that tests and application code can import it as:

    from app.schemas import SchemaManager, SchemaVersion

It also exports typed exceptions for convenience.
"""

from __future__ import annotations

from .profile import ProfileCreate, ProfileRead, ProfileUpdate
from .schema_manager import (
    SchemaDownloadError,
    SchemaManager,
    SchemaManagerError,
    SchemaNotFoundError,
    SchemaVersion,
    normalize_schema_for_internal_use,
)

__all__ = [
    "SchemaManager",
    "SchemaVersion",
    "SchemaManagerError",
    "SchemaDownloadError",
    "SchemaNotFoundError",
    "normalize_schema_for_internal_use",
    "ProfileCreate",
    "ProfileRead",
    "ProfileUpdate",
]
