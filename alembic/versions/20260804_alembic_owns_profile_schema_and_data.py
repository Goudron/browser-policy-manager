"""make Alembic the sole owner of profile schema and channel upgrades

Revision ID: 20260804_alembic_owns_profile_schema_and_data
Revises: 20260721_upgrade_profiles_to_firefox153_dual_esr
Create Date: 2026-08-04 00:00:00.000000

The historical revisions are intentionally immutable.  This revision repairs
the only retained root-alias path that their original order could not carry:
the ``5cb73fdb68ed`` database reaches this point with an empty ``profiles``
table and its original rows still in ``policies``.  Any other mixed-table
state is treated as a failed/unsupported prior upgrade and is rejected.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260804_alembic_owns_profile_schema_and_data"
down_revision = "20260721_upgrade_profiles_to_firefox153_dual_esr"
branch_labels = None
depends_on = None

PROFILE_TABLE = "profiles"
LEGACY_TABLE = "policies"
REQUIRED_PRE_COMPLIANCE_COLUMNS = {
    "id",
    "name",
    "description",
    "schema_version",
    "flags",
    "revision",
    "created_at",
    "updated_at",
    "deleted_at",
}
REQUIRED_LEGACY_ROOT_COLUMNS = {
    "id",
    "name",
    "description",
    "schema_version",
    "flags",
    "owner",
    "created_at",
    "updated_at",
}
REQUIRED_HEAD_COLUMNS = REQUIRED_PRE_COMPLIANCE_COLUMNS | {"compliance"}
HEAD_INDEXES: dict[str, tuple[list[str], bool]] = {
    "ix_profiles_name": (["name"], True),
    "ix_profiles_schema_version": (["schema_version"], False),
    "ix_profiles_created_at": (["created_at"], False),
    "ix_profiles_updated_at": (["updated_at"], False),
    "ix_profiles_deleted_at": (["deleted_at"], False),
}


def _bind() -> sa.Connection:
    return op.get_bind()


def _tables() -> set[str]:
    return set(sa.inspect(_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(_bind()).get_columns(table)}


def _index_names(table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(_bind()).get_indexes(table)}


def _require_columns(table: str, required: set[str]) -> None:
    missing = sorted(required - _columns(table))
    if missing:
        raise RuntimeError(
            f"Unsupported {table!r} shape for {revision}: missing {', '.join(missing)}"
        )


def _profile_count() -> int:
    return int(_bind().execute(sa.text("SELECT COUNT(*) FROM profiles")).scalar_one())


def _add_compliance_column() -> None:
    if "compliance" in _columns(PROFILE_TABLE):
        return
    with op.batch_alter_table(PROFILE_TABLE) as batch_op:
        batch_op.add_column(sa.Column("compliance", sa.JSON(), nullable=True))


def _repair_known_root_alias_path() -> None:
    """Copy only the known root-alias payload into its empty historical table."""
    tables = _tables()
    if LEGACY_TABLE not in tables:
        return
    if PROFILE_TABLE not in tables:
        raise RuntimeError(
            "Unsupported upgrade state: policies exists without profiles; restore and preflight "
            "the retained source instead of guessing a revision"
        )

    _require_columns(LEGACY_TABLE, REQUIRED_LEGACY_ROOT_COLUMNS)
    _require_columns(PROFILE_TABLE, REQUIRED_HEAD_COLUMNS)
    if _profile_count():
        raise RuntimeError(
            "Unsupported mixed profile tables: policies can be repaired only when the "
            "historically-created profiles table is empty"
        )

    legacy_columns = _columns(LEGACY_TABLE)
    deleted_at = "deleted_at" if "deleted_at" in legacy_columns else "NULL"
    compliance = "compliance" if "compliance" in legacy_columns else "NULL"
    revision_value = "revision" if "revision" in legacy_columns else "1"
    op.execute(
        sa.text(f"""
            INSERT INTO {PROFILE_TABLE} (
                id, name, description, schema_version, flags, compliance, revision,
                created_at, updated_at, deleted_at
            )
            SELECT
                id, name, description, schema_version, flags, {compliance}, {revision_value},
                created_at, updated_at, {deleted_at}
            FROM {LEGACY_TABLE}
            """)
    )
    op.drop_table(LEGACY_TABLE)


def _converge_known_schema_channels() -> None:
    """Apply only retained same-family channel transitions; preserve all other strings."""
    op.execute(
        sa.text("""
            UPDATE profiles
            SET schema_version = CASE
                WHEN schema_version IN (
                    'release-148', 'release-149', 'release-150', 'release-151', 'release-152'
                ) THEN 'release-153'
                WHEN schema_version IN (
                    'esr-140', 'esr-140.8', 'esr-140.9', 'esr-140.10',
                    'esr-140.11', 'esr-140.12'
                ) THEN 'esr-140.13'
                ELSE schema_version
            END
            """)
    )


def _ensure_head_indexes() -> None:
    existing = _index_names(PROFILE_TABLE)
    for name, (columns, unique) in HEAD_INDEXES.items():
        if name not in existing:
            op.create_index(name, PROFILE_TABLE, columns, unique=unique)


def _sync_postgresql_identity_sequence() -> None:
    """Advance the explicit-id sequence after the root-alias row copy."""
    bind = _bind()
    if bind.dialect.name != "postgresql":
        return
    bind.execute(
        sa.text("""
            SELECT setval(
                pg_get_serial_sequence('profiles', 'id'),
                COALESCE((SELECT MAX(id) FROM profiles), 1),
                true
            )
            """)
    )


def _assert_head_shape() -> None:
    tables = _tables()
    if PROFILE_TABLE not in tables or LEGACY_TABLE in tables:
        raise RuntimeError("Alembic did not produce the required single profiles table")
    _require_columns(PROFILE_TABLE, REQUIRED_HEAD_COLUMNS)
    if "owner" in _columns(PROFILE_TABLE):
        raise RuntimeError("Alembic head must not retain the discarded profiles.owner column")
    missing_indexes = sorted(set(HEAD_INDEXES) - _index_names(PROFILE_TABLE))
    if missing_indexes:
        raise RuntimeError(
            "Alembic head is missing required profiles indexes: " + ", ".join(missing_indexes)
        )


def upgrade() -> None:
    if PROFILE_TABLE not in _tables():
        raise RuntimeError("Alembic history did not produce profiles before the M4 repair revision")
    _require_columns(PROFILE_TABLE, REQUIRED_PRE_COMPLIANCE_COLUMNS)
    _add_compliance_column()
    _repair_known_root_alias_path()
    _converge_known_schema_channels()
    _ensure_head_indexes()
    _sync_postgresql_identity_sequence()
    _assert_head_shape()


def downgrade() -> None:
    raise NotImplementedError(
        "BPM 0.9.4 database downgrade is intentionally unsupported; restore a verified backup "
        "instead of attempting to reconstruct discarded owner data or the repaired root alias."
    )
