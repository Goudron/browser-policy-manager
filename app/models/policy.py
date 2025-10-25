# app/models/policy.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 2.x Declarative base for ORM models."""

    pass


class Policy(Base):
    """DB entity for browser policy profile."""

    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("name", name="uq_policies_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Human-friendly unique name of profile
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Optional description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Which schema (channel) is used, e.g., "firefox-ESR"
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False, default="firefox-ESR")

    # The actual policy flags document (JSON)
    flags: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Optional owner (who created/owns the profile)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Policy id={self.id} name={self.name!r}>"
