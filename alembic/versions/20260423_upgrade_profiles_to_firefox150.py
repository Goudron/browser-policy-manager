"""upgrade profile schema channels to firefox 150 / esr 140.10

Revision ID: 20260423_upgrade_profiles_to_firefox150
Revises: 20260330_upgrade_profiles_to_firefox149
Create Date: 2026-04-23 20:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260423_upgrade_profiles_to_firefox150"
down_revision = "20260330_upgrade_profiles_to_firefox149"
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
                WHEN schema_version IN ('release-149', 'release-150') THEN 'release-150'
                WHEN schema_version IN ('esr-140.9', 'esr-140.10') THEN 'esr-140.10'
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
                WHEN schema_version = 'release-150' THEN 'release-149'
                WHEN schema_version = 'esr-140.10' THEN 'esr-140.9'
                ELSE schema_version
            END
            """
        )
    )
