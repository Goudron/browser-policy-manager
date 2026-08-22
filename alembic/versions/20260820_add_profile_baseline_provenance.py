"""store durable profile starter and CIS baseline provenance

Revision ID: 20260820_add_profile_baseline_provenance
Revises: 20260804_add_profile_name_casefold
Create Date: 2026-08-20 00:00:00.000000

Every retained row, including an archived one, predates durable baseline
provenance.  The migration therefore gives every row the same truthful
``legacy-migration`` / Custom-imported / manual-review envelope.  It does not
inspect flags, raw compliance, schema labels, or historical Guided state, so it
cannot invent a starter preset or a current CIS claim.
"""

from __future__ import annotations

import json

import sqlalchemy as sa

from alembic import op

revision = "20260820_add_profile_baseline_provenance"
down_revision = "20260804_add_profile_name_casefold"
branch_labels = None
depends_on = None

_LEGACY_BASELINE_PROVENANCE = {
    "contract_id": "bpm096-profile-baseline-provenance",
    "contract_version": 1,
    "lineage": {
        "kind": "legacy-migration",
        "source_profile_id": None,
        "source_revision": None,
        "plan_digest": None,
    },
    "starter": {
        "identity_state": "custom-imported",
        "catalog_id": None,
        "catalog_version": None,
        "definition_sha256": None,
        "resolved_schema_artifact_id": None,
        "disposition": "custom-imported",
    },
    "cis": {
        "identity_state": "custom-imported",
        "catalog_id": None,
        "catalog_version": None,
        "baseline_id": None,
        "benchmark_id": None,
        "benchmark_version": None,
        "layer_sha256": None,
        "merge_rules_sha256": None,
        "merge_result_sha256": None,
        "resolved_schema_artifact_id": None,
        "proof_digest": None,
        "display_status": "manual-review",
        "current_claim": False,
        "reason_code": "cis_provenance_unknown",
    },
}
_LEGACY_DEFAULT_JSON = json.dumps(
    _LEGACY_BASELINE_PROVENANCE,
    sort_keys=True,
    separators=(",", ":"),
)
# ``sa.text`` recognizes ``:name`` even inside a quoted SQL literal.  Escape
# JSON's colons before handing it the migration-only server default so SQLite
# and PostgreSQL receive the exact JSON bytes instead of phantom bind tokens.
_LEGACY_DEFAULT_SQL = "'" + _LEGACY_DEFAULT_JSON.replace(":", r"\:") + "'"
_PRESENCE_CONSTRAINT = "ck_profiles_baseline_provenance_present"
_IDEMPOTENCY_PAIR_CONSTRAINT = "ck_profiles_preparation_idempotency_pair"
_IDEMPOTENCY_KEY_INDEX = "uq_profiles_preparation_idempotency_key"


def upgrade() -> None:
    """Add the non-null envelope in one portable Alembic-owned transaction."""

    # The temporary server default is applied to all existing records by both
    # SQLite's batch table rebuild and PostgreSQL's ALTER TABLE path.  It is
    # deliberately independent of archived state and raw profile payloads.
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "baseline_provenance",
                sa.JSON(),
                nullable=False,
                server_default=sa.text(_LEGACY_DEFAULT_SQL),
            )
        )
        batch_op.create_check_constraint(
            _PRESENCE_CONSTRAINT,
            "baseline_provenance IS NOT NULL",
        )
        batch_op.add_column(sa.Column("preparation_idempotency_key", sa.String(length=255)))
        batch_op.add_column(sa.Column("preparation_request_fingerprint", sa.String(length=64)))
        batch_op.create_check_constraint(
            _IDEMPOTENCY_PAIR_CONSTRAINT,
            "(preparation_idempotency_key IS NULL "
            "AND preparation_request_fingerprint IS NULL) "
            "OR (preparation_idempotency_key IS NOT NULL "
            "AND preparation_request_fingerprint IS NOT NULL)",
        )

    # ORM/service creation supplies an explicit truthful origin.  Removing the
    # migration-only default prevents a later raw write from masquerading as a
    # migrated legacy row.
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column("baseline_provenance", server_default=None)
    op.create_index(
        _IDEMPOTENCY_KEY_INDEX,
        "profiles",
        ["preparation_idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Return to the preceding physical shape without rewriting profile data."""

    op.drop_index(_IDEMPOTENCY_KEY_INDEX, table_name="profiles")
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_constraint(_IDEMPOTENCY_PAIR_CONSTRAINT, type_="check")
        batch_op.drop_column("preparation_request_fingerprint")
        batch_op.drop_column("preparation_idempotency_key")
        batch_op.drop_constraint(_PRESENCE_CONSTRAINT, type_="check")
        batch_op.drop_column("baseline_provenance")
