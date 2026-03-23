"""normalize profiles schema

Revision ID: 20260323_normalize_profiles
Revises: 20251026_add_deleted_at_profiles
Create Date: 2026-03-23 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260323_normalize_profiles"
down_revision = "20251026_add_deleted_at_profiles"
branch_labels = None
depends_on = None

OLD_TABLE = "policies"
NEW_TABLE = "profiles"
LEGACY_INDEXES = (
    "ix_policies_created_at",
    "ix_policies_name",
    "ix_policies_updated_at",
    "uq_policies_name",
)
CURRENT_INDEXES: dict[str, tuple[list[str], bool]] = {
    "ix_profiles_created_at": (["created_at"], False),
    "ix_profiles_name": (["name"], True),
    "ix_profiles_updated_at": (["updated_at"], False),
    "ix_profiles_schema_version": (["schema_version"], False),
    "ix_profiles_owner": (["owner"], False),
    "ix_profiles_deleted_at": (["deleted_at"], False),
}
SQLITE_CURRENT_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS ix_profiles_created_at ON profiles (created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_profiles_name ON profiles (name)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_updated_at ON profiles (updated_at)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_schema_version ON profiles (schema_version)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_owner ON profiles (owner)",
    "CREATE INDEX IF NOT EXISTS ix_profiles_deleted_at ON profiles (deleted_at)",
)


def _bind() -> Connection:
    return op.get_bind()


def _insp():
    return sa.inspect(_bind())


def _has_table(table: str) -> bool:
    bind = _bind()
    if bind.dialect.name == "sqlite":
        row = bind.execute(
            sa.text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = :table
                """
            ),
            {"table": table},
        ).first()
        return row is not None
    return _insp().has_table(table)


def _has_column(table: str, column: str) -> bool:
    bind = _bind()
    if not _has_table(table):
        return False
    if bind.dialect.name == "sqlite":
        rows = bind.execute(sa.text(f"PRAGMA table_info({table})")).mappings().all()
        cols = {row["name"] for row in rows}
    else:
        cols = {c["name"] for c in _insp().get_columns(table)}
    return column in cols


def _index_names(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    bind = _bind()
    if bind.dialect.name == "sqlite":
        rows = bind.execute(sa.text(f"PRAGMA index_list({table})")).mappings().all()
        return {row["name"] for row in rows}
    return {idx["name"] for idx in _insp().get_indexes(table)}


def _ensure_current_indexes(table: str) -> None:
    existing = _index_names(table)
    for name, (columns, unique) in CURRENT_INDEXES.items():
        if name not in existing:
            op.create_index(name, table, columns, unique=unique)


def _run_sqlite_ddl(bind: Connection, ddl: str) -> None:
    try:
        bind.execute(sa.text(ddl))
    except Exception:
        # The normalize migration is intentionally idempotent for local/dev SQLite
        # databases that may already be partially migrated.
        pass


def upgrade() -> None:
    """Normalize legacy `policies` tables to the canonical `profiles` schema."""
    bind = _bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if is_sqlite:
        _run_sqlite_ddl(bind, "ALTER TABLE policies ADD COLUMN deleted_at DATETIME")
        _run_sqlite_ddl(bind, "ALTER TABLE policies RENAME TO profiles")
        _run_sqlite_ddl(bind, "ALTER TABLE profiles ADD COLUMN deleted_at DATETIME")
        for index_name in LEGACY_INDEXES:
            _run_sqlite_ddl(bind, f"DROP INDEX IF EXISTS {index_name}")
        for ddl in SQLITE_CURRENT_INDEX_DDL:
            _run_sqlite_ddl(bind, ddl)
        return

    if _has_table(OLD_TABLE) and not _has_table(NEW_TABLE):
        if not _has_column(OLD_TABLE, "deleted_at"):
            with op.batch_alter_table(OLD_TABLE) as batch_op:
                batch_op.add_column(
                    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
                )

        op.rename_table(OLD_TABLE, NEW_TABLE)

    if not _has_table(NEW_TABLE):
        return

    if not _has_column(NEW_TABLE, "deleted_at"):
        with op.batch_alter_table(NEW_TABLE) as batch_op:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    for index_name in LEGACY_INDEXES:
        if index_name in _index_names(NEW_TABLE):
            op.drop_index(index_name, table_name=NEW_TABLE)

    _ensure_current_indexes(NEW_TABLE)


def downgrade() -> None:
    """Reconstruct the legacy `policies` table/index names if needed."""
    if not _has_table(NEW_TABLE):
        return

    for index_name in CURRENT_INDEXES:
        if index_name in _index_names(NEW_TABLE):
            op.drop_index(index_name, table_name=NEW_TABLE)

    op.rename_table(NEW_TABLE, OLD_TABLE)

    existing = _index_names(OLD_TABLE)
    if "ix_policies_created_at" not in existing:
        op.create_index("ix_policies_created_at", OLD_TABLE, ["created_at"], unique=False)
    if "ix_policies_name" not in existing:
        op.create_index("ix_policies_name", OLD_TABLE, ["name"], unique=True)
    if "ix_policies_updated_at" not in existing:
        op.create_index("ix_policies_updated_at", OLD_TABLE, ["updated_at"], unique=False)
