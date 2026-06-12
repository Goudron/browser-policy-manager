"""drop profile owner storage

Revision ID: 20260606_drop_profile_owner
Revises: 20260521_upgrade_profiles_to_firefox151
Create Date: 2026-06-06 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260606_drop_profile_owner"
down_revision = "20260521_upgrade_profiles_to_firefox151"
branch_labels = None
depends_on = None

TABLE_NAME = "profiles"
OWNER_COLUMN = "owner"
OWNER_INDEX = "ix_profiles_owner"


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {item["name"] for item in _insp().get_columns(table)}


def _index_names(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {item["name"] for item in _insp().get_indexes(table)}


def upgrade() -> None:
    if not _has_table(TABLE_NAME):
        return

    if OWNER_INDEX in _index_names(TABLE_NAME):
        op.drop_index(OWNER_INDEX, table_name=TABLE_NAME)

    if _has_column(TABLE_NAME, OWNER_COLUMN):
        with op.batch_alter_table(TABLE_NAME) as batch_op:
            batch_op.drop_column(OWNER_COLUMN)


def downgrade() -> None:
    if not _has_table(TABLE_NAME):
        return

    if not _has_column(TABLE_NAME, OWNER_COLUMN):
        with op.batch_alter_table(TABLE_NAME) as batch_op:
            batch_op.add_column(sa.Column(OWNER_COLUMN, sa.String(length=255), nullable=True))

    if _has_column(TABLE_NAME, OWNER_COLUMN) and OWNER_INDEX not in _index_names(TABLE_NAME):
        op.create_index(OWNER_INDEX, TABLE_NAME, [OWNER_COLUMN], unique=False)
