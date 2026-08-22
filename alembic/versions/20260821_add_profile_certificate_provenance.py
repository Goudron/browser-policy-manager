"""store durable certificate/trust value source attribution

Revision ID: 20260821_add_profile_certificate_provenance
Revises: 20260821_add_profile_extension_provenance
Create Date: 2026-08-21 00:00:00.000000

This ledger deliberately records only RFC 6901 paths and source labels.  It
does not read certificate/module files and it does not mutate M3 baseline/CIS
provenance. Existing values become historical ``imported`` values rather than
receiving an inferred starter or CIS origin.
"""

from __future__ import annotations

from collections.abc import Mapping

import sqlalchemy as sa

from alembic import op

revision = "20260821_add_profile_certificate_provenance"
down_revision = "20260821_add_profile_extension_provenance"
branch_labels = None
depends_on = None

_CONTRACT_ID = "bpm096-profile-certificate-provenance"
_CERTIFICATE_POLICIES = {
    "Authentication",
    "Certificates",
    "DisableSecurityBypass",
    "MicrosoftEntraSSO",
    "SecurityDevices",
    "WindowsSSO",
}
_ENTERPRISE_ROOTS_PREFERENCE = "security.enterprise_roots.enabled"
_PRESENCE_CONSTRAINT = "ck_profiles_certificate_provenance_present"


def upgrade() -> None:
    """Add and backfill the independent certificate source ledger."""

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "certificate_provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            )
        )
        batch_op.create_check_constraint(
            _PRESENCE_CONSTRAINT,
            "certificate_provenance IS NOT NULL",
        )

    bind = op.get_bind()
    profiles = sa.table(
        "profiles",
        sa.column("id", sa.Integer()),
        sa.column("flags", sa.JSON()),
        sa.column("certificate_provenance", sa.JSON()),
    )
    rows = bind.execute(sa.select(profiles.c.id, profiles.c.flags)).mappings()
    for row in rows:
        bind.execute(
            sa.update(profiles)
            .where(profiles.c.id == row["id"])
            .values(certificate_provenance=_historical_imported_record(row["flags"]))
        )

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column("certificate_provenance", server_default=None)


def downgrade() -> None:
    """Return to the prior physical shape without rewriting policy values."""

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_constraint(_PRESENCE_CONSTRAINT, type_="check")
        batch_op.drop_column("certificate_provenance")


def _historical_imported_record(flags: object) -> dict[str, object]:
    paths: dict[str, str] = {}
    if isinstance(flags, Mapping):
        for policy in sorted(_CERTIFICATE_POLICIES):
            if policy in flags:
                paths.update(_leaf_paths(flags[policy], (policy,)))
        preferences = flags.get("Preferences")
        if isinstance(preferences, Mapping) and _ENTERPRISE_ROOTS_PREFERENCE in preferences:
            paths.update(
                _leaf_paths(
                    preferences[_ENTERPRISE_ROOTS_PREFERENCE],
                    ("Preferences", _ENTERPRISE_ROOTS_PREFERENCE),
                )
            )
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
