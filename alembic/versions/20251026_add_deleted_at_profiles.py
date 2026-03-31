"""add deleted_at to profiles

Revision ID: 20251026_add_deleted_at_profiles
Revises: 20251022_init_profiles
Create Date: 2025-10-26 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251026_add_deleted_at_profiles"
down_revision = "20251022_init_profiles"
branch_labels = None
depends_on = None


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_column(table: str, column: str) -> bool:
    cols = {c["name"] for c in _insp().get_columns(table)} if _has_table(table) else set()
    return column in cols


def upgrade() -> None:
    insp = _insp()
    # 1) If the profiles table does not exist, create a minimal schema.
    if not insp.has_table("profiles"):
        op.create_table(
            "profiles",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=255), nullable=False, unique=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column(
                "schema_version",
                sa.String(length=50),
                nullable=False,
                server_default="esr-140.9",
            ),
            # Store flags as TEXT (JSON is serialized by the application).
            sa.Column("flags", sa.Text, nullable=False, server_default="{}"),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_profiles_created_at", "profiles", ["created_at"], unique=False)
        op.create_index("ix_profiles_name", "profiles", ["name"], unique=True)
        op.create_index("ix_profiles_updated_at", "profiles", ["updated_at"], unique=False)
        op.create_index("ix_profiles_schema_version", "profiles", ["schema_version"], unique=False)
        op.create_index("ix_profiles_owner", "profiles", ["owner"], unique=False)
        op.create_index("ix_profiles_deleted_at", "profiles", ["deleted_at"], unique=False)
        # Remove server defaults if they are not needed at runtime.
        with op.batch_alter_table("profiles") as batch_op:
            batch_op.alter_column("schema_version", server_default=None)
            batch_op.alter_column("flags", server_default=None)
            batch_op.alter_column("created_at", server_default=None)
            batch_op.alter_column("updated_at", server_default=None)
        return  # The table already includes deleted_at; nothing else to do.

    # 2) If the table exists, add the column only when it is missing.
    if not _has_column("profiles", "deleted_at"):
        with op.batch_alter_table("profiles") as batch_op:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    if "ix_profiles_deleted_at" not in {idx["name"] for idx in insp.get_indexes("profiles")}:
        op.create_index("ix_profiles_deleted_at", "profiles", ["deleted_at"], unique=False)


def downgrade() -> None:
    # Do not drop the table, only remove the column if it exists.
    if _has_table("profiles"):
        if "ix_profiles_deleted_at" in {idx["name"] for idx in _insp().get_indexes("profiles")}:
            op.drop_index("ix_profiles_deleted_at", table_name="profiles")
    if _has_table("profiles") and _has_column("profiles", "deleted_at"):
        with op.batch_alter_table("profiles") as batch_op:
            batch_op.drop_column("deleted_at")
