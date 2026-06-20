"""upgrade profile schema channels to firefox 152 / esr 140.12

Revision ID: 20260620_upgrade_profiles_to_firefox152
Revises: 20260606_drop_profile_owner
Create Date: 2026-06-20 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260620_upgrade_profiles_to_firefox152"
down_revision = "20260606_drop_profile_owner"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("profiles"):
        return

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET schema_version = CASE
                WHEN schema_version IN ('release-151', 'release-152') THEN 'release-152'
                WHEN schema_version IN ('esr-140.11', 'esr-140.12') THEN 'esr-140.12'
                ELSE schema_version
            END
            """
        )
    )


def downgrade() -> None:
    if not _table_exists("profiles"):
        return

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET schema_version = CASE
                WHEN schema_version = 'release-152' THEN 'release-151'
                WHEN schema_version = 'esr-140.12' THEN 'esr-140.11'
                ELSE schema_version
            END
            """
        )
    )
