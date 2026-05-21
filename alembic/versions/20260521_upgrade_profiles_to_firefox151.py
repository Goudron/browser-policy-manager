"""upgrade profile schema channels to firefox 151 / esr 140.11

Revision ID: 20260521_upgrade_profiles_to_firefox151
Revises: 20260423_upgrade_profiles_to_firefox150
Create Date: 2026-05-21 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260521_upgrade_profiles_to_firefox151"
down_revision = "20260423_upgrade_profiles_to_firefox150"
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
                WHEN schema_version IN ('release-150', 'release-151') THEN 'release-151'
                WHEN schema_version IN ('esr-140.10', 'esr-140.11') THEN 'esr-140.11'
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
                WHEN schema_version = 'release-151' THEN 'release-150'
                WHEN schema_version = 'esr-140.11' THEN 'esr-140.10'
                ELSE schema_version
            END
            """
        )
    )
