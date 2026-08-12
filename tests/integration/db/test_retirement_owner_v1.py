from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.lifecycle_transition_plan import build_lifecycle_transition_plan
from app.core.profile_conversion_json import canonical_json
from app.core.retirement_convertibility_preflight import (
    SchemaArtifactBinding,
    load_exact_schema_containment_evidence,
    prove_retirement_total_convertibility,
)
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG
from migration_support.retirement_owner_v1 import (
    BackupEvidence,
    ConvertedProfile,
    RetirementMigrationError,
    apply_retirement_profiles_in_alembic_transaction,
    authorize_production_retirement,
    authorize_synthetic_contract_fixture,
    build_database_preflight,
    execute_synthetic_contract_transaction,
    reject_retirement_downgrade,
)

_MANIFEST_DOMAIN = b"bpm-retired-esr-transition-manifest:v1\n"
_TOTAL_REPORT_DOMAIN = b"bpm-retired-esr-total-preflight:v1\n"
_REGISTRY_DIGEST = "7" * 64
_SOURCE_REVISION = "fixture_before_esr115_retirement"
_TARGET_REVISION = "fixture_retire_esr115_to_esr140"
_TEMPORARY_POSTGRES_DATABASE = re.compile(r"^bpm_(?:m4_05|m6_04)(?:_[a-z0-9]+)*$")
_ESR140_TO_ESR153_PROOF = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)


@dataclass(frozen=True)
class _RetirementDatabaseTarget:
    """A disposable engine only; this suite must never touch customer data."""

    name: str
    sync_url: str
    database_name: str | None = None
    admin_url: str | None = None

    def create(self) -> None:
        if self.name == "sqlite":
            self.reset()
            return

        self._drop_postgres_database()
        assert self.admin_url is not None
        assert self.database_name is not None
        engine = create_engine(self.admin_url, isolation_level="AUTOCOMMIT", future=True)
        try:
            with engine.connect() as connection:
                connection.execute(sa.text(f'CREATE DATABASE "{self.database_name}"'))
        finally:
            engine.dispose()

    def reset(self) -> None:
        if self.name == "sqlite":
            Path(self.sync_url.removeprefix("sqlite:///")).unlink(missing_ok=True)
            return

        database_name = urlparse(self.sync_url).path.removeprefix("/")
        if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
            raise RuntimeError(
                "Refusing to reset PostgreSQL database outside the disposable retirement "
                f"test naming contract: {database_name!r}"
            )
        engine = create_engine(self.sync_url, isolation_level="AUTOCOMMIT", future=True)
        try:
            with engine.connect() as connection:
                connection.execute(sa.text("DROP SCHEMA public CASCADE"))
                connection.execute(sa.text("CREATE SCHEMA public"))
        finally:
            engine.dispose()

    def cleanup(self) -> None:
        if self.name == "sqlite":
            self.reset()
            return
        self._drop_postgres_database()

    def _drop_postgres_database(self) -> None:
        assert self.admin_url is not None
        assert self.database_name is not None
        engine = create_engine(self.admin_url, isolation_level="AUTOCOMMIT", future=True)
        try:
            with engine.connect() as connection:
                connection.execute(
                    sa.text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = :database AND pid <> pg_backend_pid()"
                    ),
                    {"database": self.database_name},
                )
                connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{self.database_name}"'))
        finally:
            engine.dispose()


def _postgres_sync_url(async_url: str) -> str:
    return async_url.replace("+asyncpg", "+psycopg").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _postgres_retirement_target() -> _RetirementDatabaseTarget | None:
    async_url = os.environ.get("BPM_POSTGRES_TEST_URL")
    if not async_url:
        if os.environ.get("BPM_REQUIRE_POSTGRES") == "1":
            pytest.fail(
                "BPM_REQUIRE_POSTGRES=1 requires BPM_POSTGRES_TEST_URL for the real "
                "PostgreSQL retirement matrix"
            )
        return None
    if "+asyncpg" not in async_url or not async_url.startswith("postgresql+"):
        pytest.fail("BPM_POSTGRES_TEST_URL must use the real postgresql+asyncpg driver")
    base = make_url(async_url)
    database_name = base.database or ""
    if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
        pytest.fail(
            "BPM_POSTGRES_TEST_URL must target only a disposable bpm_m4_05* or bpm_m6_04* "
            f"database, got {database_name!r}"
        )
    retirement_database = f"{database_name}_retirement"
    return _RetirementDatabaseTarget(
        name="postgresql",
        sync_url=base.set(
            drivername="postgresql+psycopg", database=retirement_database
        ).render_as_string(hide_password=False),
        database_name=retirement_database,
        admin_url=base.set(drivername="postgresql+psycopg", database="postgres").render_as_string(
            hide_password=False
        ),
    )


@pytest.fixture(params=("sqlite", "postgresql"), ids=("sqlite", "postgresql"))
def retirement_database_target(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> _RetirementDatabaseTarget:
    if request.param == "sqlite":
        target = _RetirementDatabaseTarget(
            name="sqlite", sync_url=f"sqlite:///{tmp_path / 'm6-04.sqlite'}"
        )
    else:
        target = _postgres_retirement_target()
        if target is None:
            pytest.skip("set BPM_POSTGRES_TEST_URL to run the real PostgreSQL retirement matrix")
    target.create()
    try:
        yield target
    finally:
        target.cleanup()


class _SyntheticIdentityConverter:
    registry_digest = _REGISTRY_DIGEST

    def source_valid(self, flags: dict[str, Any]) -> bool:
        return isinstance(flags.get("Enabled", False), bool)

    def target_valid(self, flags: dict[str, Any]) -> bool:
        return self.source_valid(flags)

    def convert(
        self,
        flags: dict[str, Any],
        compliance: dict[str, Any] | None,
    ) -> ConvertedProfile:
        return ConvertedProfile(
            flags=copy.deepcopy(flags),
            compliance=copy.deepcopy(compliance),
            compliance_disposition="absent" if compliance is None else "preserved-verified",
        )


def _digest(domain: bytes, value: dict[str, Any]) -> str:
    return hashlib.sha256(domain + canonical_json(value)).hexdigest()


def _complete_report() -> dict[str, Any]:
    result = {
        "source": {
            "line_id": "esr-115",
            "artifact_id": "esr-115.38",
            "schema_bundle_sha256": "3" * 64,
            "validation_schema_sha256": "4" * 64,
        },
        "target": {
            "line_id": "esr-140",
            "artifact_id": "esr-140.13",
            "schema_bundle_sha256": "5" * 64,
            "validation_schema_sha256": "6" * 64,
        },
        "successor_line_id": "esr-140",
        "recipe_registry": {
            "registry_id": "firefox-profile-conversion",
            "registry_version": 1,
            "recipes": [],
            "registry_digest": _REGISTRY_DIGEST,
        },
        "status": "complete",
        "method": "schema-containment",
        "uncovered_schema_locations": [],
        "proof_artifact_digest": "8" * 64,
        "blockers": [],
        "mutation": "none",
        "result_digest": "9" * 64,
    }
    projection = {
        "kind": "retirement-total-convertibility-report",
        "contract_version": 1,
        "results": [result],
    }
    return {
        **projection,
        "status": "complete",
        "report_digest": _digest(_TOTAL_REPORT_DOMAIN, projection),
    }


def _manifest(
    report: dict[str, Any],
    *,
    evidence_scope: str,
    source_revision: str = _SOURCE_REVISION,
    target_revision: str | None = _TARGET_REVISION,
) -> dict[str, Any]:
    result = report["results"][0]
    source = result["source"]
    target = result["target"]
    projection = {
        "kind": "retired-esr-transition-manifest",
        "contract_version": 1,
        "transition_id": "fixture-retire-esr115-to-esr140",
        "evidence_scope": evidence_scope,
        "previous_catalog_digest": "1" * 64,
        "candidate_catalog_digest": "2" * 64,
        "source": {
            "family": "esr",
            "line_id": source["line_id"],
            "line_number": 115 if source["line_id"] == "esr-115" else 140,
            **source,
        },
        "target": {
            "family": "esr",
            "line_id": target["line_id"],
            "line_number": 140 if target["line_id"] == "esr-140" else 153,
            **target,
        },
        "candidate_supported_esr_lines": [
            {
                "line_id": target["line_id"],
                "line_number": 140 if target["line_id"] == "esr-140" else 153,
                "artifact_id": target["artifact_id"],
            }
        ],
        "declared_successor_line_id": target["line_id"],
        "conversion_contract_version": 1,
        "recipe_registry_version": 1,
        "recipe_registry_digest": result["recipe_registry"]["registry_digest"],
        "total_proof_artifact_digest": result["proof_artifact_digest"],
        "alembic_source_revision": source_revision,
        "alembic_target_revision": target_revision,
    }
    return {**projection, "manifest_digest": _digest(_MANIFEST_DOMAIN, projection)}


def _synthetic_authorization():
    report = _complete_report()
    return authorize_synthetic_contract_fixture(
        _manifest(report, evidence_scope="synthetic-contract-only"), report
    )


def _production_shaped_fixture_authorization():
    report = _complete_report()
    return authorize_production_retirement(
        _manifest(report, evidence_scope="production-exact-artifacts"), report
    )


def _schema() -> tuple[sa.MetaData, sa.Table, sa.Table]:
    metadata = sa.MetaData()
    profiles = sa.Table(
        "profiles",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_casefold", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("schema_version", sa.String(50), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
        sa.Column("compliance", sa.JSON()),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    version = sa.Table(
        "alembic_version",
        metadata,
        sa.Column("version_num", sa.String(128), nullable=False),
    )
    return metadata, profiles, version


def _prepare_database(target: _RetirementDatabaseTarget) -> tuple[sa.Engine, sa.Table]:
    target.reset()
    engine = create_engine(target.sync_url, future=True)
    metadata, profiles, version = _schema()
    metadata.create_all(engine)
    created = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    updated = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    archived = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    with engine.begin() as connection:
        connection.execute(version.insert().values(version_num=_SOURCE_REVISION))
        connection.execute(
            profiles.insert(),
            [
                {
                    "id": 1,
                    "name": "active-source",
                    "name_casefold": "active-source",
                    "description": "preserve",
                    "schema_version": "esr-115.38",
                    "flags": {"Enabled": True, "Nested": {"items": [1, 2]}},
                    "compliance": None,
                    "revision": 3,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": None,
                },
                {
                    "id": 2,
                    "name": "archived-source",
                    "name_casefold": "archived-source",
                    "description": None,
                    "schema_version": "esr-115.38",
                    "flags": {"Enabled": False},
                    "compliance": {"benchmark": "synthetic", "status": "verified"},
                    "revision": 8,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": archived,
                },
                {
                    "id": 3,
                    "name": "already-target",
                    "name_casefold": "already-target",
                    "description": None,
                    "schema_version": "esr-140.13",
                    "flags": {"Enabled": True},
                    "compliance": None,
                    "revision": 5,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": None,
                },
                {
                    "id": 4,
                    "name": "latest-esr",
                    "name_casefold": "latest-esr",
                    "description": "latest remains retained",
                    "schema_version": "esr-153.0",
                    "flags": {"Enabled": True, "Object": {"nested": []}},
                    "compliance": {"benchmark": "synthetic", "status": "latest"},
                    "revision": 6,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": None,
                },
                {
                    "id": 5,
                    "name": "release",
                    "name_casefold": "release",
                    "description": None,
                    "schema_version": "release-153",
                    "flags": {},
                    "compliance": None,
                    "revision": 2,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": None,
                },
                {
                    "id": 6,
                    "name": "active-empty-source",
                    "name_casefold": "active-empty-source",
                    "description": "empty valid document",
                    "schema_version": "esr-115.38",
                    "flags": {},
                    "compliance": {
                        "benchmark": "synthetic",
                        "evidence": {"empty": [], "valid": True},
                    },
                    "revision": 11,
                    "created_at": created,
                    "updated_at": updated,
                    "deleted_at": None,
                },
            ],
        )
    return engine, profiles


def _backup(*, engine: str = "sqlite", profile_count: int = 6) -> BackupEvidence:
    return BackupEvidence(
        engine=engine,
        backup_sha256="a" * 64,
        restore_identity_digest="b" * 64,
        source_stamp=_SOURCE_REVISION,
        restored_stamp=_SOURCE_REVISION,
        source_profile_count=profile_count,
        restored_profile_count=profile_count,
    )


def _preflight(engine, authorization=None, progress=None):
    with engine.connect() as connection:
        evidence = build_database_preflight(
            connection,
            authorization or _synthetic_authorization(),
            _SyntheticIdentityConverter(),
            _backup(engine=connection.dialect.name),
            no_active_writers=True,
            progress=progress,
        )
        connection.rollback()
    return evidence


def _rows(engine, profiles) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(sa.select(profiles).order_by(profiles.c.id)).mappings()
        ]


def _stamp(engine) -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
        )


def _rows_by_id(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result = {row["id"]: row for row in rows}
    assert len(result) == len(rows)
    return result


def _assert_synthetic_retirement_contract(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> None:
    """Assert the complete permitted-field and lifecycle contract per fixture row."""
    assert len(after) == len(before) == 6
    before_by_id = _rows_by_id(before)
    after_by_id = _rows_by_id(after)
    affected_ids = {1, 2, 6}
    retained_ids = {3, 4, 5}
    preserved_fields = {
        "id",
        "name",
        "name_casefold",
        "description",
        "created_at",
        "deleted_at",
    }
    allowed_changed_fields = {
        "schema_version",
        "flags",
        "compliance",
        "revision",
        "updated_at",
    }

    affected_timestamps = {after_by_id[profile_id]["updated_at"] for profile_id in affected_ids}
    assert len(affected_timestamps) == 1
    for profile_id in affected_ids:
        source = before_by_id[profile_id]
        converted = after_by_id[profile_id]
        changed_fields = {key for key in source if source[key] != converted[key]}
        assert changed_fields <= allowed_changed_fields
        assert converted["schema_version"] == "esr-140.13"
        assert converted["revision"] == source["revision"] + 1
        assert converted["flags"] == source["flags"]
        assert converted["compliance"] == source["compliance"]
        assert converted["updated_at"] != source["updated_at"]
        for field in preserved_fields:
            assert converted[field] == source[field]

    # Archive state is part of the lifecycle contract: both active and archived
    # source rows migrate, while their `deleted_at` value remains exact.
    assert before_by_id[1]["deleted_at"] is None
    assert after_by_id[1]["deleted_at"] is None
    assert before_by_id[2]["deleted_at"] is not None
    assert after_by_id[2]["deleted_at"] == before_by_id[2]["deleted_at"]
    assert before_by_id[6]["flags"] == after_by_id[6]["flags"] == {}

    # Exact target, latest supported ESR, and Release rows are retained byte/value-wise.
    for profile_id in retained_ids:
        assert after_by_id[profile_id] == before_by_id[profile_id]


def test_current_real_proof_does_not_authorize_the_still_supported_runtime_catalog() -> None:
    """A complete proof alone cannot name or activate a retirement revision."""
    candidate = tuple(
        replace(channel, support_state="retired", selectable=False)
        if channel.line_id == "esr-140"
        else replace(channel, retirement_successor_line_id="esr-153")
        if channel.line_id == "esr-115"
        else channel
        for channel in SCHEMA_CHANNEL_CATALOG
    )
    plan = build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        candidate,
        bundled_artifact_ids={channel.artifact_id for channel in candidate},
    )
    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    source = SchemaArtifactBinding.from_channel(channels["esr-140"])
    target = SchemaArtifactBinding.from_channel(channels["esr-153"])
    evidence = load_exact_schema_containment_evidence(
        _ESR140_TO_ESR153_PROOF,
        source=source,
        target=target,
    )
    proof = prove_retirement_total_convertibility(
        plan,
        artifacts={source.artifact_id: source, target.artifact_id: target},
        containment_evidence=evidence,
    )
    report = proof.as_dict()
    manifest = _manifest(
        report,
        evidence_scope="production-exact-artifacts",
        source_revision="20260804_add_profile_name_casefold",
        target_revision=None,
    )

    with pytest.raises(
        RetirementMigrationError, match="retirement_manifest_identity_mismatch"
    ) as error:
        authorize_production_retirement(manifest, report)

    assert error.value.code == "retirement_manifest_identity_mismatch"
    assert report["status"] == "complete"
    assert report["results"][0]["proof_artifact_digest"] == (
        "3d04890c00a89534526fea7456e89250c36ba3617fa0d10949c8e51d98bcc2bb"
    )
    assert manifest["alembic_target_revision"] is None
    assert manifest["source"]["artifact_id"] == "esr-140.13"
    assert manifest["target"]["artifact_id"] == "esr-153.0"


def test_unproven_or_stale_static_evidence_cannot_reach_database_preflight() -> None:
    """Authorizing a retirement is static and fails before any connection exists."""
    complete_report = _complete_report()
    valid_manifest = _manifest(complete_report, evidence_scope="production-exact-artifacts")

    stale_manifest = copy.deepcopy(valid_manifest)
    stale_manifest["manifest_digest"] = "0" * 64
    with pytest.raises(RetirementMigrationError, match="retirement_manifest_stale") as stale:
        authorize_production_retirement(stale_manifest, complete_report)
    assert stale.value.code == "retirement_manifest_stale"

    unproven_report = copy.deepcopy(complete_report)
    unproven_report["status"] = "rejected"
    unproven_report["results"][0]["status"] = "rejected"
    unproven_report["results"][0]["proof_artifact_digest"] = None
    with pytest.raises(
        RetirementMigrationError, match="retirement_total_convertibility_unproven"
    ) as unproven:
        authorize_production_retirement(valid_manifest, unproven_report)
    assert unproven.value.code == "retirement_total_convertibility_unproven"


def test_same_line_patch_refresh_is_plan_only_and_retains_every_profile(
    retirement_database_target: _RetirementDatabaseTarget,
) -> None:
    """A patch refresh has no retirement mapping and must not write stored rows."""
    engine, profiles = _prepare_database(retirement_database_target)
    before = _rows(engine, profiles)
    try:
        candidate = tuple(
            replace(
                channel,
                artifact_id="esr-140.14",
                channel_id="esr-140.14",
                artifact_version="140.14",
            )
            if channel.line_id == "esr-140"
            else channel
            for channel in SCHEMA_CHANNEL_CATALOG
        )
        plan = build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            tuple(reversed(candidate)),
            bundled_artifact_ids={channel.artifact_id for channel in candidate},
        )

        assert [
            (refresh.line_id, refresh.previous.artifact_id, refresh.candidate.artifact_id)
            for refresh in plan.same_line_patch_refreshes
        ] == [("esr-140", "esr-140.13", "esr-140.14")]
        assert [line.line_id for line in plan.retained_lines] == [
            "esr-115",
            "esr-153",
            "release-153",
        ]
        assert plan.retirement_successor_mappings == ()
        assert _rows(engine, profiles) == before
        assert _stamp(engine) == _SOURCE_REVISION
    finally:
        engine.dispose()


def test_synthetic_retirement_is_atomic_preserves_full_contract_and_is_idempotent(
    retirement_database_target: _RetirementDatabaseTarget,
) -> None:
    engine, profiles = _prepare_database(retirement_database_target)
    before = _rows(engine, profiles)
    events: list[dict[str, object]] = []
    preflight = _preflight(engine, progress=lambda event: events.append(dict(event)))
    try:
        with engine.connect() as connection:
            outcome = execute_synthetic_contract_transaction(
                connection,
                preflight,
                _SyntheticIdentityConverter(),
                progress=lambda event: events.append(dict(event)),
            )
        after = _rows(engine, profiles)
        assert outcome.code == "retirement_applied"
        assert outcome.engine == retirement_database_target.name
        assert outcome.affected_count == 3
        assert [row["schema_version"] for row in after] == [
            "esr-140.13",
            "esr-140.13",
            "esr-140.13",
            "esr-153.0",
            "release-153",
            "esr-140.13",
        ]
        assert [row["revision"] for row in after] == [4, 9, 5, 6, 2, 12]
        _assert_synthetic_retirement_contract(before, after)
        assert _stamp(engine) == _TARGET_REVISION
        assert events[0]["phase"] == "preflight"
        assert events[0]["transaction_result"] == "not-started"
        assert events[0]["counts"] == {
            "profile_count": 6,
            "affected_source_count": 3,
            "already_target_count": 1,
            "transformed_count": 0,
            "unchanged_count": 6,
            "processed_in_open_transaction": 0,
        }
        committed = next(event for event in events if event["status"] == "committed")
        assert committed["transaction_result"] == "committed"
        assert committed["counts"] == {
            "profile_count": 6,
            "affected_source_count": 3,
            "already_target_count": 1,
            "transformed_count": 3,
            "unchanged_count": 3,
            "processed_in_open_transaction": 3,
        }
        in_flight = [event for event in events if event["transaction_result"] == "in-progress"]
        assert in_flight
        assert all(event["counts"]["transformed_count"] is None for event in in_flight)
        assert all(event["counts"]["unchanged_count"] is None for event in in_flight)

        with engine.connect() as connection:
            second = execute_synthetic_contract_transaction(
                connection,
                preflight,
                _SyntheticIdentityConverter(),
                progress=lambda event: events.append(dict(event)),
            )
        assert second.code == "retirement_already_applied"
        assert _rows(engine, profiles) == after
        assert events[-1]["status"] == "already-applied"
        assert all(
            not any(
                forbidden in key
                for forbidden in ("profile_id", "name", "description", "flags", "compliance")
            )
            for event in events
            for key in event
        )
        rendered = json.dumps(events, sort_keys=True)
        assert all(
            forbidden not in rendered
            for forbidden in (
                "active-source",
                "archived-source",
                "Enabled",
                "Nested",
                "synthetic",
                "sqlite:///",
                "database_snapshot_digest",
                "preflight_digest",
            )
        )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("failure_phase", "exception_type"),
    [
        ("before-first-write", RuntimeError),
        ("after-affected-row", RuntimeError),
        ("before-stamp", RuntimeError),
        ("before-commit", ConnectionError),
    ],
    ids=("before-first-write", "after-first-row", "before-stamp", "connection-interruption"),
)
def test_injected_failure_rolls_back_all_rows_timestamps_and_stamp(
    retirement_database_target: _RetirementDatabaseTarget,
    failure_phase: str,
    exception_type: type[BaseException],
) -> None:
    """Every interruption boundary rolls back the full synthetic 115 -> 140 set."""
    engine, profiles = _prepare_database(retirement_database_target)
    before = _rows(engine, profiles)
    preflight = _preflight(engine)
    events: list[dict[str, object]] = []

    def interrupt(phase: str, completed: int, total: int) -> None:
        if phase != failure_phase:
            return
        if phase == "after-affected-row":
            assert completed == 1
            assert total == 3
        raise exception_type(f"controlled {failure_phase}")

    try:
        with engine.connect() as connection:
            with pytest.raises(
                RetirementMigrationError, match="retirement_transaction_failed"
            ) as error:
                execute_synthetic_contract_transaction(
                    connection,
                    preflight,
                    _SyntheticIdentityConverter(),
                    progress=lambda event: events.append(dict(event)),
                    failure_injector=interrupt,
                )
        assert error.value.code == "retirement_transaction_failed"
        assert _rows(engine, profiles) == before
        assert _stamp(engine) == _SOURCE_REVISION
        assert events[-1]["status"] == "rolled-back"
        assert events[-1]["transaction_result"] == "rolled-back"
        assert events[-1]["counts"]["transformed_count"] == 0
        assert events[-1]["counts"]["unchanged_count"] == 6
        assert events[-1]["failure_boundary"] == failure_phase
        assert events[-1]["recovery_direction"] == (
            "restore-verified-backup-to-new-clean-candidate"
        )
    finally:
        engine.dispose()


def test_changed_profile_after_preflight_is_stale_and_performs_no_retirement_write(
    retirement_database_target: _RetirementDatabaseTarget,
) -> None:
    engine, profiles = _prepare_database(retirement_database_target)
    preflight = _preflight(engine)
    try:
        with engine.begin() as connection:
            changed = connection.execute(
                sa.update(profiles)
                .where(profiles.c.id == 1)
                .values(description="changed by external writer after read-only preflight")
            )
            assert changed.rowcount == 1
        changed_state = _rows(engine, profiles)

        events: list[dict[str, object]] = []
        with engine.connect() as connection:
            with pytest.raises(
                RetirementMigrationError, match="retirement_preflight_stale"
            ) as error:
                execute_synthetic_contract_transaction(
                    connection,
                    preflight,
                    _SyntheticIdentityConverter(),
                    progress=lambda event: events.append(dict(event)),
                )
        assert error.value.code == "retirement_preflight_stale"
        assert _rows(engine, profiles) == changed_state
        assert _stamp(engine) == _SOURCE_REVISION
        assert events[-1]["status"] == "rolled-back"
        assert events[-1]["failure_boundary"] == "lock-and-preflight-recheck"
    finally:
        engine.dispose()


def test_production_adapter_leaves_stamp_and_commit_to_outer_alembic_transaction(
    retirement_database_target: _RetirementDatabaseTarget,
) -> None:
    engine, profiles = _prepare_database(retirement_database_target)
    before = _rows(engine, profiles)
    authorization = _production_shaped_fixture_authorization()
    preflight = _preflight(engine, authorization)
    events: list[dict[str, object]] = []
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            outcome = apply_retirement_profiles_in_alembic_transaction(
                connection,
                preflight,
                _SyntheticIdentityConverter(),
                progress=lambda event: events.append(dict(event)),
            )
            # This statement represents Alembic's own revision-stamp update.
            stamp = connection.execute(
                sa.text(
                    "UPDATE alembic_version SET version_num = :target WHERE version_num = :source"
                ),
                {"source": _SOURCE_REVISION, "target": _TARGET_REVISION},
            )
            assert stamp.rowcount == 1
            transaction.commit()
        assert outcome.code == "retirement_profiles_applied"
        assert outcome.engine == retirement_database_target.name
        assert events[-1]["status"] == "profiles-applied-awaiting-alembic-stamp"
        assert events[-1]["transaction_result"] == "pending-alembic-stamp"
        assert events[-1]["counts"]["transformed_count"] is None
        assert events[-1]["counts"]["unchanged_count"] is None
        after = _rows(engine, profiles)
        _assert_synthetic_retirement_contract(before, after)
        assert _stamp(engine) == _TARGET_REVISION
    finally:
        engine.dispose()


def test_backup_converter_and_downgrade_gates_fail_without_profile_mutation(
    retirement_database_target: _RetirementDatabaseTarget,
) -> None:
    engine, profiles = _prepare_database(retirement_database_target)
    before = _rows(engine, profiles)
    invalid_backup = replace(
        _backup(engine=retirement_database_target.name), restored_profile_count=5
    )
    try:
        with engine.connect() as connection:
            with pytest.raises(RetirementMigrationError, match="retirement_backup_unverified"):
                build_database_preflight(
                    connection,
                    _synthetic_authorization(),
                    _SyntheticIdentityConverter(),
                    invalid_backup,
                    no_active_writers=True,
                )
            connection.rollback()
        stale_converter = _SyntheticIdentityConverter()
        stale_converter.registry_digest = "0" * 64
        with engine.connect() as connection:
            with pytest.raises(RetirementMigrationError, match="conversion_recipe_registry_stale"):
                build_database_preflight(
                    connection,
                    _synthetic_authorization(),
                    stale_converter,
                    _backup(engine=retirement_database_target.name),
                    no_active_writers=True,
                )
        with pytest.raises(RetirementMigrationError, match="retirement_downgrade_unsupported"):
            reject_retirement_downgrade()
        assert _rows(engine, profiles) == before
        assert _stamp(engine) == _SOURCE_REVISION
    finally:
        engine.dispose()


def test_production_authorizer_rejects_synthetic_scope_even_with_complete_proof() -> None:
    report = _complete_report()
    manifest = _manifest(report, evidence_scope="synthetic-contract-only")

    with pytest.raises(RetirementMigrationError, match="retirement_manifest_identity_mismatch"):
        authorize_production_retirement(manifest, report)

    preflight_engine = create_engine("sqlite:///:memory:", future=True)
    try:
        # The production executor is a second boundary: even a fully formed
        # disposable fixture cannot be routed through the release entrypoint.
        metadata, _profiles, _version = _schema()
        metadata.create_all(preflight_engine)
        with preflight_engine.begin() as connection:
            connection.execute(
                sa.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": _SOURCE_REVISION},
            )
        backup = replace(_backup(), source_profile_count=0, restored_profile_count=0)
        with preflight_engine.connect() as connection:
            preflight = build_database_preflight(
                connection,
                _synthetic_authorization(),
                _SyntheticIdentityConverter(),
                backup,
                no_active_writers=True,
            )
            connection.rollback()
        with preflight_engine.connect() as connection:
            with pytest.raises(
                RetirementMigrationError, match="retirement_manifest_identity_mismatch"
            ):
                apply_retirement_profiles_in_alembic_transaction(
                    connection,
                    preflight,
                    _SyntheticIdentityConverter(),
                    progress=lambda _event: None,
                )
    finally:
        preflight_engine.dispose()
