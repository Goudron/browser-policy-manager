from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""

    pass


class Policy(Base):
    """Policy profile entity persisted to the database."""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(50), default="firefox-ESR")
    flags: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Use UTC timestamps; updated_at is maintained by application (on update).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    def touch(self) -> None:
        """Update the 'updated_at' field to current UTC time in Python side."""
        self.updated_at = datetime.now(timezone.utc)
