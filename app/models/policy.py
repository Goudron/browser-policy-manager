# app/models/policy.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 2.x Declarative base for ORM models."""

    pass


class Policy(Base):
    """
    Enterprise browser policy profile.

    Soft-delete is implemented via `deleted_at`:
      - Active records: deleted_at IS NULL
      - Deleted records: deleted_at IS NOT NULL
    """

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, unique=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sprint F scope: ESR-140 and Release-144. Value is a free string to avoid hard-coupling here.
    schema_version: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default="esr-140"
    )

    # Arbitrary flags / raw policy blob (JSON)
    flags: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    owner: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

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

    __table_args__ = (UniqueConstraint("name", name="uq_policies_name"),)

    @property
    def is_deleted(self) -> bool:
        """Convenience property for Pydantic models."""
        return self.deleted_at is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Policy id={self.id} name={self.name!r} deleted={self.is_deleted}>"
