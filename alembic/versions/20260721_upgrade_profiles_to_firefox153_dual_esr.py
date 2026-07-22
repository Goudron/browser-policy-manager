"""upgrade profile schema channels to Firefox 153 with dual ESR support

Revision ID: 20260721_upgrade_profiles_to_firefox153_dual_esr
Revises: 20260620_upgrade_profiles_to_firefox152
Create Date: 2026-07-21 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260721_upgrade_profiles_to_firefox153_dual_esr"
down_revision = "20260620_upgrade_profiles_to_firefox152"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    """Keep each persisted profile on its existing Firefox release family."""
    if not _table_exists("profiles"):
        return

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET schema_version = CASE
                WHEN schema_version IN ('release-149', 'release-150', 'release-151', 'release-152')
                    THEN 'release-153'
                WHEN schema_version IN ('esr-140.9', 'esr-140.10', 'esr-140.11', 'esr-140.12')
                    THEN 'esr-140.13'
                ELSE schema_version
            END
            """
        )
    )


def downgrade() -> None:
    """Return only upgraded lines to their immediate pre-153 channel."""
    if not _table_exists("profiles"):
        return

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET schema_version = CASE
                WHEN schema_version = 'release-153' THEN 'release-152'
                WHEN schema_version = 'esr-140.13' THEN 'esr-140.12'
                ELSE schema_version
            END
            """
        )
    )
