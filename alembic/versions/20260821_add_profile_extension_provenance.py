"""store durable extension value source attribution

Revision ID: 20260821_add_profile_extension_provenance
Revises: 20260820_add_profile_baseline_provenance
Create Date: 2026-08-21 00:00:00.000000

The new field deliberately does not alter M3 baseline provenance or raw CIS
compliance. Existing persisted extension values are truthfully labelled as
imported historical values instead of guessing whether a past Guided preset,
CIS layer, manual editor, or external AMO search created them.
"""

from __future__ import annotations

from collections.abc import Mapping

import sqlalchemy as sa

from alembic import op

revision = "20260821_add_profile_extension_provenance"
down_revision = "20260820_add_profile_baseline_provenance"
branch_labels = None
depends_on = None

_CONTRACT_ID = "bpm096-profile-extension-provenance"
_EMPTY = {"contract_id": _CONTRACT_ID, "contract_version": 1, "paths": {}}
_EXTENSION_POLICIES = {
    "ExtensionSettings",
    "ExtensionUpdate",
    "Extensions",
    "InstallAddonsPermission",
}
_PRESENCE_CONSTRAINT = "ck_profiles_extension_provenance_present"


def upgrade() -> None:
    """Add one non-null record and attribute retained historical values."""

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "extension_provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            )
        )
        batch_op.create_check_constraint(
            _PRESENCE_CONSTRAINT,
            "extension_provenance IS NOT NULL",
        )

    bind = op.get_bind()
    profiles = sa.table(
        "profiles",
        sa.column("id", sa.Integer()),
        sa.column("flags", sa.JSON()),
        sa.column("extension_provenance", sa.JSON()),
    )
    rows = bind.execute(sa.select(profiles.c.id, profiles.c.flags)).mappings()
    for row in rows:
        bind.execute(
            sa.update(profiles)
            .where(profiles.c.id == row["id"])
            .values(extension_provenance=_historical_imported_record(row["flags"]))
        )

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column("extension_provenance", server_default=None)


def downgrade() -> None:
    """Return to the prior physical shape without rewriting policy values."""

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_constraint(_PRESENCE_CONSTRAINT, type_="check")
        batch_op.drop_column("extension_provenance")


def _historical_imported_record(flags: object) -> dict[str, object]:
    paths: dict[str, str] = {}
    if isinstance(flags, Mapping):
        for policy in sorted(_EXTENSION_POLICIES):
            if policy in flags:
                paths.update(_leaf_paths(flags[policy], (policy,)))
    return {"contract_id": _CONTRACT_ID, "contract_version": 1, "paths": paths}


def _leaf_paths(value: object, path: tuple[str | int, ...]) -> dict[str, str]:
    if isinstance(value, Mapping):
        if not value:
            return {_pointer(path): "imported"}
        result: dict[str, str] = {}
        for key in sorted(value, key=str):
            result.update(_leaf_paths(value[key], (*path, str(key))))
        return result
    if isinstance(value, list):
        if not value:
            return {_pointer(path): "imported"}
        result = {}
        for index, item in enumerate(value):
            result.update(_leaf_paths(item, (*path, index)))
        return result
    return {_pointer(path): "imported"}


def _pointer(parts: tuple[str | int, ...]) -> str:
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)
