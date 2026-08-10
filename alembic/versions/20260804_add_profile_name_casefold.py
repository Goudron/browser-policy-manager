"""store a portable Unicode search key for profile names

Revision ID: 20260804_add_profile_name_casefold
Revises: 20260804_alembic_owns_profile_schema_and_data
Create Date: 2026-08-04 00:00:00.000000

SQLite's LOWER() is ASCII-oriented by default and PostgreSQL's result depends
on the cluster locale.  BPM's established search contract is Python Unicode
casefold(), so the key is materialised once and queried portably.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260804_add_profile_name_casefold"
down_revision = "20260804_alembic_owns_profile_schema_and_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A temporary default permits the added NOT NULL column on retained data;
    # every row is immediately backfilled with the exact historic predicate.
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column("name_casefold", sa.Text(), nullable=False, server_default=sa.text("''"))
        )

    bind = op.get_bind()
    profiles = sa.table(
        "profiles",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.Text()),
        sa.column("name_casefold", sa.Text()),
    )
    rows = bind.execute(sa.select(profiles.c.id, profiles.c.name)).mappings()
    for row in rows:
        bind.execute(
            sa.update(profiles)
            .where(profiles.c.id == row["id"])
            .values(name_casefold=str(row["name"]).casefold())
        )

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column("name_casefold", server_default=None)
        batch_op.create_index("ix_profiles_name_casefold", ["name_casefold"], unique=False)


def downgrade() -> None:
    raise NotImplementedError(
        "BPM 0.9.4 database downgrade is intentionally unsupported; restore a verified backup."
    )
