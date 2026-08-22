# app/models/profile.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, Integer, String, Text, event, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.profile_baseline_provenance import (
    baseline_display,
    generic_create_baseline_provenance,
)
from app.core.profile_certificate_provenance import empty_certificate_provenance
from app.core.profile_extension_provenance import empty_extension_provenance
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
    __table_args__ = (
        CheckConstraint(
            "(preparation_idempotency_key IS NULL "
            "AND preparation_request_fingerprint IS NULL) "
            "OR (preparation_idempotency_key IS NOT NULL "
            "AND preparation_request_fingerprint IS NOT NULL)",
            name="ck_profiles_preparation_idempotency_pair",
        ),
        Index(
            "uq_profiles_preparation_idempotency_key",
            "preparation_idempotency_key",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    # Persist the exact Unicode casefold value used by profile-library search.
    # Neither SQLite LOWER() nor a PostgreSQL database locale implements
    # Python's Unicode casefold semantics consistently.
    name_casefold: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Schema version stays free-form here; business rules live in validation code.
    schema_version: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default=DEFAULT_SCHEMA_CHANNEL
    )

    # Raw Firefox policy payload stored as JSON on the profile entity.
    flags: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Optional compliance metadata (e.g., CIS overlay decisions).
    compliance: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # The only durable starter/CIS origin record.  Policy flags and raw
    # compliance data are deliberately not used to infer or repair it.
    baseline_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=generic_create_baseline_provenance,
    )

    # Value-level extension origin is intentionally separate from the
    # starter/CIS baseline envelope.  It records UI/review attribution only;
    # it cannot assert or repair a benchmark claim.
    extension_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=empty_extension_provenance,
    )

    # Certificate/trust source attribution is deliberately a separate
    # value-free review ledger.  It never changes the selected baseline/CIS
    # proof and never stores certificate or device contents outside flags.
    certificate_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=empty_certificate_provenance,
    )

    # A preparation command records its opaque retry key and canonical request
    # fingerprint only on a successful target.  They are not part of a source
    # snapshot and are never exposed through the generic profile read model.
    preparation_idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preparation_request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)

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

    @property
    def baseline_display(self) -> dict[str, Any]:
        """Return the server-only value-free projection for read models."""
        return baseline_display(self.baseline_provenance)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Profile id={self.id} name={self.name!r} deleted={self.is_deleted}>"


def _synchronize_name_casefold(_: object, __: object, target: Profile) -> None:
    """Keep direct ORM writes aligned with the portable search contract."""
    target.name_casefold = target.name.casefold()


event.listen(Profile, "before_insert", _synchronize_name_casefold)
event.listen(Profile, "before_update", _synchronize_name_casefold)
