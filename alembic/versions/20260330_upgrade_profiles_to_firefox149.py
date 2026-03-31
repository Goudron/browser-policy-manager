"""upgrade profile schema channels to firefox 149 / esr 140.9

Revision ID: 20260330_upgrade_profiles_to_firefox149
Revises: 20260323_normalize_profiles
Create Date: 2026-03-30 23:45:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260330_upgrade_profiles_to_firefox149"
down_revision = "20260323_normalize_profiles"
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
                WHEN schema_version IN ('release-148', 'release-149') THEN 'release-149'
                WHEN schema_version IN ('esr-140', 'esr-140.8', 'esr-140.9') THEN 'esr-140.9'
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
                WHEN schema_version = 'release-149' THEN 'release-148'
                WHEN schema_version = 'esr-140.9' THEN 'esr-140.8'
                ELSE schema_version
            END
            """
        )
    )
