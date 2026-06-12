# app/models/profile.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.schema_channels import DEFAULT_SCHEMA_CHANNEL


class Base(DeclarativeBase):
    """SQLAlchemy 2.x Declarative base for ORM models."""

    pass


class Profile(Base):
    """
    Stored browser profile entity.

    Soft-delete is implemented via `deleted_at`:
      - Active records: deleted_at IS NULL
      - Deleted records: deleted_at IS NOT NULL
    """

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Schema version stays free-form here; business rules live in validation code.
    schema_version: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default=DEFAULT_SCHEMA_CHANNEL
    )

    # Raw Firefox policy payload stored as JSON on the profile entity.
    flags: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Optional compliance metadata (e.g., CIS overlay decisions).
    compliance: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Optimistic concurrency token for safe multi-tab editing.
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    # Soft delete marker
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    @property
    def is_deleted(self) -> bool:
        """Convenience property for Pydantic models."""
        return self.deleted_at is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Profile id={self.id} name={self.name!r} deleted={self.is_deleted}>"
