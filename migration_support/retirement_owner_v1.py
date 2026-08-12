"""Fail-closed owner for a future, statically approved ESR retirement.

This module is deliberately outside ``app``: request handling and application
startup must never import or invoke it.  A production retirement revision may
use this versioned owner only after M6-02 has emitted a complete exact-artifact
proof and a reviewed transition manifest has been frozen.  Until then,
``authorize_production_retirement`` fails before a database connection is
needed and no Alembic revision may name the transition.

The transaction executor is exercised only with synthetic/disposable database
fixtures in BPM 0.9.5.  It owns the same all-rows-plus-stamp boundary that a
future Alembic retirement revision must embed: SQLite obtains ``BEGIN
IMMEDIATE``; PostgreSQL locks the profiles table; every source row is rederived
and rechecked under that lock; and one commit advances both profiles and the
stamp.  It never imports an application service, runtime schema registry, HTTP
API, or UI path.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from migration_support.retirement_observability_v1 import (
    build_execution_evidence,
    build_preflight_evidence,
)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type ProgressSink = Callable[[Mapping[str, object]], None]
type FailureInjector = Callable[[str, int, int], None]

_MANIFEST_DOMAIN = b"bpm-retired-esr-transition-manifest:v1\n"
_TOTAL_REPORT_DOMAIN = b"bpm-retired-esr-total-preflight:v1\n"
_DATABASE_SNAPSHOT_DOMAIN = b"bpm-retired-esr-database-snapshot:v1\n"
_PREFLIGHT_DOMAIN = b"bpm-retired-esr-preflight-evidence:v1\n"
_SHA256_LENGTH = 64
_SUPPORTED_ENGINES = frozenset({"sqlite", "postgresql"})
_COMPLIANCE_DISPOSITIONS = frozenset(
    {"absent", "preserved-verified", "recomputed", "invalidated-preserved"}
)
_PROFILE_COLUMNS = frozenset(
    {
        "id",
        "name",
        "name_casefold",
        "description",
        "schema_version",
        "flags",
        "compliance",
        "revision",
        "created_at",
        "updated_at",
        "deleted_at",
    }
)


class RetirementMigrationError(RuntimeError):
    """The immutable retirement or database evidence failed closed."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True, slots=True)
class ConvertedProfile:
    """Migration-owned target values for the four permitted profile fields."""

    flags: dict[str, JsonValue]
    compliance: dict[str, JsonValue] | None
    compliance_disposition: str


class FrozenRetirementConverter(Protocol):
    """Interface implemented inside one immutable retirement revision."""

    @property
    def registry_digest(self) -> str: ...

    def convert(
        self,
        flags: dict[str, JsonValue],
        compliance: dict[str, JsonValue] | None,
    ) -> ConvertedProfile: ...

    def source_valid(self, flags: dict[str, JsonValue]) -> bool: ...

    def target_valid(self, flags: dict[str, JsonValue]) -> bool: ...


@dataclass(frozen=True, slots=True)
class AuthorizedRetirement:
    """Exact static evidence admitted before any database preflight."""

    manifest: dict[str, JsonValue]
    manifest_digest: str
    report_digest: str
    evidence_scope: str
    source_line_id: str
    source_artifact_id: str
    target_line_id: str
    target_artifact_id: str
    source_revision: str
    target_revision: str
    recipe_registry_digest: str
    total_proof_artifact_digest: str


@dataclass(frozen=True, slots=True)
class BackupEvidence:
    """Privacy-safe native-backup/restore facts bound to one source database."""

    engine: str
    backup_sha256: str
    restore_identity_digest: str
    source_stamp: str
    restored_stamp: str
    source_profile_count: int
    restored_profile_count: int
    status: str = "verified-native-restore"
    integrity: str = "pass"

    def validate_for(self, authorization: AuthorizedRetirement, profile_count: int) -> None:
        if self.engine not in _SUPPORTED_ENGINES:
            raise RetirementMigrationError("retirement_backup_unverified")
        if self.status != "verified-native-restore" or self.integrity != "pass":
            raise RetirementMigrationError("retirement_backup_unverified")
        if not _is_sha256(self.backup_sha256) or not _is_sha256(self.restore_identity_digest):
            raise RetirementMigrationError("retirement_backup_unverified")
        if (
            self.source_stamp != authorization.source_revision
            or self.restored_stamp != authorization.source_revision
            or self.source_profile_count != profile_count
            or self.restored_profile_count != profile_count
        ):
            raise RetirementMigrationError("retirement_backup_unverified")

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "backup_sha256": self.backup_sha256,
            "restore_identity_digest": self.restore_identity_digest,
            "integrity": self.integrity,
            "source_stamp": self.source_stamp,
            "restored_stamp": self.restored_stamp,
            "source_profile_count": self.source_profile_count,
            "restored_profile_count": self.restored_profile_count,
        }


@dataclass(frozen=True, slots=True)
class _RowPlan:
    profile_id: int
    source_revision: int
    source_flags: dict[str, JsonValue]
    source_compliance: dict[str, JsonValue] | None
    target_flags: dict[str, JsonValue]
    target_compliance: dict[str, JsonValue] | None
    compliance_disposition: str
    row_identity_digest: str


@dataclass(frozen=True, slots=True)
class RetirementDatabasePreflight:
    """Read-only database evidence plus private, in-memory exact row plans."""

    authorization: AuthorizedRetirement
    engine: str
    profile_count: int
    affected_source_count: int
    already_target_count: int
    database_snapshot_digest: str
    backup: BackupEvidence
    preflight_digest: str
    _plans: tuple[_RowPlan, ...]

    def as_dict(self) -> dict[str, JsonValue]:
        status = (
            "complete"
            if self.authorization.evidence_scope == "production-exact-artifacts"
            else "complete-contract-simulation"
        )
        return {
            "status": status,
            "manifest_digest": self.authorization.manifest_digest,
            "engine": self.engine,
            "database_snapshot_digest": self.database_snapshot_digest,
            "source_stamp": self.authorization.source_revision,
            "target_stamp": self.authorization.target_revision,
            "profile_count": self.profile_count,
            "affected_source_count": self.affected_source_count,
            "planned_count": len(self._plans),
            "blocked_count": 0,
            "already_target_count": self.already_target_count,
            "no_active_writers": True,
            "backup": self.backup.as_dict(),
            "preflight_digest": self.preflight_digest,
        }


@dataclass(frozen=True, slots=True)
class RetirementTransactionOutcome:
    code: str
    engine: str
    affected_count: int
    source_artifact_id: str
    target_artifact_id: str


def authorize_production_retirement(
    manifest: Mapping[str, Any],
    total_report: Mapping[str, Any],
) -> AuthorizedRetirement:
    """Admit only a complete production proof; never accepts contract fixtures."""
    return _authorize_retirement(
        manifest,
        total_report,
        required_evidence_scope="production-exact-artifacts",
    )


def authorize_synthetic_contract_fixture(
    manifest: Mapping[str, Any],
    total_report: Mapping[str, Any],
) -> AuthorizedRetirement:
    """Exercise the writer mechanism without granting production promotion."""
    return _authorize_retirement(
        manifest,
        total_report,
        required_evidence_scope="synthetic-contract-only",
    )


def _authorize_retirement(
    manifest_value: Mapping[str, Any],
    total_report_value: Mapping[str, Any],
    *,
    required_evidence_scope: str,
) -> AuthorizedRetirement:
    manifest = _strict_object(manifest_value, "retirement_manifest_identity_mismatch")
    report = _strict_object(total_report_value, "retirement_total_convertibility_unproven")
    if (
        manifest.get("kind") != "retired-esr-transition-manifest"
        or manifest.get("contract_version") != 1
        or manifest.get("evidence_scope") != required_evidence_scope
    ):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")

    manifest_digest = manifest.get("manifest_digest")
    if not isinstance(manifest_digest, str) or not _is_sha256(manifest_digest):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    manifest_projection = copy.deepcopy(manifest)
    del manifest_projection["manifest_digest"]
    if _domain_digest(_MANIFEST_DOMAIN, manifest_projection) != manifest_digest:
        raise RetirementMigrationError("retirement_manifest_stale")

    if report.get("status") != "complete":
        raise RetirementMigrationError("retirement_total_convertibility_unproven")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
        raise RetirementMigrationError("retirement_total_convertibility_unproven")
    result = results[0]
    if result.get("status") != "complete" or result.get("blockers") != []:
        raise RetirementMigrationError("retirement_total_convertibility_unproven")
    if result.get("uncovered_schema_locations") != []:
        raise RetirementMigrationError("retirement_total_convertibility_unproven")

    report_digest = report.get("report_digest")
    if not isinstance(report_digest, str) or not _is_sha256(report_digest):
        raise RetirementMigrationError("retirement_total_convertibility_unproven")
    report_projection = {
        "kind": report.get("kind"),
        "contract_version": report.get("contract_version"),
        "results": copy.deepcopy(results),
    }
    if _domain_digest(_TOTAL_REPORT_DOMAIN, report_projection) != report_digest:
        raise RetirementMigrationError("retirement_total_convertibility_unproven")

    source = _strict_object(manifest.get("source"), "retirement_manifest_identity_mismatch")
    target = _strict_object(manifest.get("target"), "retirement_manifest_identity_mismatch")
    result_source = _strict_object(result.get("source"), "retirement_total_convertibility_unproven")
    result_target = _strict_object(result.get("target"), "retirement_total_convertibility_unproven")
    source_line = _required_text(source, "line_id")
    source_artifact = _required_text(source, "artifact_id")
    target_line = _required_text(target, "line_id")
    target_artifact = _required_text(target, "artifact_id")
    source_line_number = source.get("line_number")
    target_line_number = target.get("line_number")
    if (
        source.get("family") != "esr"
        or target.get("family") != "esr"
        or isinstance(source_line_number, bool)
        or not isinstance(source_line_number, int)
        or isinstance(target_line_number, bool)
        or not isinstance(target_line_number, int)
        or target_line_number <= source_line_number
        or source_line == target_line
        or source_artifact == target_artifact
        or result_source.get("line_id") != source_line
        or result_source.get("artifact_id") != source_artifact
        or result_target.get("line_id") != target_line
        or result_target.get("artifact_id") != target_artifact
        or manifest.get("declared_successor_line_id") != target_line
        or result.get("successor_line_id") != target_line
    ):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    for manifest_end, result_end in ((source, result_source), (target, result_target)):
        for digest_name in ("schema_bundle_sha256", "validation_schema_sha256"):
            digest = manifest_end.get(digest_name)
            if (
                not isinstance(digest, str)
                or not _is_sha256(digest)
                or result_end.get(digest_name) != digest
            ):
                raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    supported_lines = manifest.get("candidate_supported_esr_lines")
    if not isinstance(supported_lines, list) or not supported_lines:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    supported_numbers: list[int] = []
    target_matches = 0
    for row_value in supported_lines:
        row = _strict_object(row_value, "retirement_manifest_identity_mismatch")
        line_number = row.get("line_number")
        if isinstance(line_number, bool) or not isinstance(line_number, int):
            raise RetirementMigrationError("retirement_manifest_identity_mismatch")
        supported_numbers.append(line_number)
        if (
            row.get("line_id") == target_line
            and row.get("artifact_id") == target_artifact
            and line_number == target_line_number
        ):
            target_matches += 1
    if (
        len(supported_numbers) != len(set(supported_numbers))
        or target_matches != 1
        or any(source_line_number < number < target_line_number for number in supported_numbers)
    ):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")

    proof_digest = manifest.get("total_proof_artifact_digest")
    registry_digest = manifest.get("recipe_registry_digest")
    if (
        not isinstance(proof_digest, str)
        or not _is_sha256(proof_digest)
        or result.get("proof_artifact_digest") != proof_digest
        or not isinstance(registry_digest, str)
        or not _is_sha256(registry_digest)
    ):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    registry = result.get("recipe_registry")
    if not isinstance(registry, dict) or registry.get("registry_digest") != registry_digest:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")

    source_revision = _required_text(manifest, "alembic_source_revision")
    target_revision = _required_text(manifest, "alembic_target_revision")
    if source_revision == target_revision:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    return AuthorizedRetirement(
        manifest=manifest,
        manifest_digest=manifest_digest,
        report_digest=report_digest,
        evidence_scope=required_evidence_scope,
        source_line_id=source_line,
        source_artifact_id=source_artifact,
        target_line_id=target_line,
        target_artifact_id=target_artifact,
        source_revision=source_revision,
        target_revision=target_revision,
        recipe_registry_digest=registry_digest,
        total_proof_artifact_digest=proof_digest,
    )


def build_database_preflight(
    connection: Connection,
    authorization: AuthorizedRetirement,
    converter: FrozenRetirementConverter,
    backup: BackupEvidence,
    *,
    no_active_writers: bool,
    progress: ProgressSink | None = None,
) -> RetirementDatabasePreflight:
    """Build read-only, digest-only evidence before the write transaction."""
    if not no_active_writers:
        raise RetirementMigrationError("retirement_preflight_stale", "active writer detected")
    _validate_authorization(authorization)
    engine = connection.dialect.name
    if engine not in _SUPPORTED_ENGINES or backup.engine != engine:
        raise RetirementMigrationError("retirement_backup_unverified")
    _validate_converter(authorization, converter)
    _require_database_shape(connection)
    stamp = _read_stamp(connection)
    if stamp != authorization.source_revision:
        raise RetirementMigrationError("retirement_preflight_stale", "source stamp changed")
    profile_count, already_target_count, plans = _derive_row_plans(
        connection, authorization, converter
    )
    backup.validate_for(authorization, profile_count)
    snapshot_digest = _row_set_digest(plans)
    payload: dict[str, JsonValue] = {
        "status": (
            "complete"
            if authorization.evidence_scope == "production-exact-artifacts"
            else "complete-contract-simulation"
        ),
        "manifest_digest": authorization.manifest_digest,
        "engine": engine,
        "database_snapshot_digest": snapshot_digest,
        "source_stamp": authorization.source_revision,
        "target_stamp": authorization.target_revision,
        "profile_count": profile_count,
        "affected_source_count": len(plans),
        "planned_count": len(plans),
        "blocked_count": 0,
        "already_target_count": already_target_count,
        "no_active_writers": True,
        "backup": backup.as_dict(),
    }
    preflight = RetirementDatabasePreflight(
        authorization=authorization,
        engine=engine,
        profile_count=profile_count,
        affected_source_count=len(plans),
        already_target_count=already_target_count,
        database_snapshot_digest=snapshot_digest,
        backup=backup,
        preflight_digest=_domain_digest(_PREFLIGHT_DOMAIN, payload),
        _plans=plans,
    )
    if progress is not None:
        progress(build_preflight_evidence(preflight))
    return preflight


def apply_retirement_profiles_in_alembic_transaction(
    connection: Connection,
    preflight: RetirementDatabasePreflight,
    converter: FrozenRetirementConverter,
    *,
    progress: ProgressSink | None = None,
    failure_injector: FailureInjector | None = None,
) -> RetirementTransactionOutcome:
    """Apply profiles inside Alembic's transaction; Alembic owns stamp/commit.

    The future immutable revision calls this function from ``upgrade()``.
    PostgreSQL's outer transaction obtains an exclusive table lock here.  On
    SQLite the DBAPI transaction must not have started yet, allowing this
    function to upgrade Alembic's logical transaction to ``BEGIN IMMEDIATE``
    before its first read.  Raising leaves Alembic to roll back the outer
    transaction, including its later revision-stamp write.
    """
    if preflight.authorization.evidence_scope != "production-exact-artifacts":
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    authorization = preflight.authorization
    _validate_authorization(authorization)
    _validate_preflight_identity(preflight)
    engine = connection.dialect.name
    if engine != preflight.engine or engine not in _SUPPORTED_ENGINES:
        raise RetirementMigrationError("retirement_preflight_stale", "database engine changed")
    if not connection.in_transaction():
        raise RetirementMigrationError(
            "retirement_preflight_stale", "Alembic transaction is not active"
        )
    _validate_converter(authorization, converter)
    sink = progress or _print_progress
    inject = failure_injector or (lambda _phase, _completed, _total: None)
    writes_started = False
    failure_boundary = "lock-and-preflight-recheck"

    def mark_failure_boundary(boundary: str) -> None:
        nonlocal failure_boundary
        failure_boundary = boundary

    try:
        if engine == "sqlite":
            driver_connection = connection.connection.driver_connection
            if getattr(driver_connection, "in_transaction", True):
                raise RetirementMigrationError(
                    "retirement_preflight_stale",
                    "SQLite write lock must be acquired before Alembic reads",
                )
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            connection.exec_driver_sql("LOCK TABLE profiles IN EXCLUSIVE MODE")
        plans = _recheck_locked_preflight(connection, preflight, converter)
        mark_failure_boundary("before-first-write")
        inject("before-first-write", 0, len(plans))
        writes_started = bool(plans)
        mark_failure_boundary("profile-apply")
        _apply_locked_profile_rows(
            connection,
            preflight,
            plans,
            sink=sink,
            inject=inject,
            mark_failure_boundary=mark_failure_boundary,
        )
        mark_failure_boundary("before-stamp")
        inject("before-stamp", len(plans), len(plans))
        _emit(
            sink,
            phase="transaction",
            status="profiles-applied-awaiting-alembic-stamp",
            preflight=preflight,
            transaction_result="pending-alembic-stamp",
            processed_in_open_transaction=len(plans),
        )
        return RetirementTransactionOutcome(
            code="retirement_profiles_applied",
            engine=engine,
            affected_count=len(plans),
            source_artifact_id=authorization.source_artifact_id,
            target_artifact_id=authorization.target_artifact_id,
        )
    except BaseException as exc:
        _emit(
            sink,
            phase="transaction",
            status="failed-awaiting-alembic-rollback",
            preflight=preflight,
            transaction_result="rollback-pending-outer-transaction",
            failure_boundary=failure_boundary,
            failure_code=_safe_failure_code(exc),
            recovery_direction="await-outer-rollback-then-restore-verified-backup-to-new-clean-candidate",
        )
        if isinstance(exc, RetirementMigrationError) and not writes_started:
            raise
        raise RetirementMigrationError("retirement_transaction_failed") from exc


def _recheck_locked_preflight(
    connection: Connection,
    preflight: RetirementDatabasePreflight,
    converter: FrozenRetirementConverter,
) -> tuple[_RowPlan, ...]:
    authorization = preflight.authorization
    _require_database_shape(connection)
    if _read_stamp(connection) != authorization.source_revision:
        raise RetirementMigrationError("retirement_preflight_stale", "source stamp changed")
    profile_count, already_target_count, plans = _derive_row_plans(
        connection, authorization, converter
    )
    preflight.backup.validate_for(authorization, profile_count)
    if (
        profile_count != preflight.profile_count
        or already_target_count != preflight.already_target_count
        or len(plans) != preflight.affected_source_count
        or _row_set_digest(plans) != preflight.database_snapshot_digest
        or plans != preflight._plans
    ):
        raise RetirementMigrationError("retirement_preflight_stale", "profile snapshot changed")
    return plans


def _apply_locked_profile_rows(
    connection: Connection,
    preflight: RetirementDatabasePreflight,
    plans: tuple[_RowPlan, ...],
    *,
    sink: ProgressSink,
    inject: FailureInjector,
    mark_failure_boundary: Callable[[str], None],
) -> None:
    authorization = preflight.authorization
    engine = preflight.engine
    mark_failure_boundary("transaction-time")
    transaction_time = connection.execute(sa.text("SELECT CURRENT_TIMESTAMP")).scalar_one()
    if engine == "sqlite" and isinstance(transaction_time, str):
        transaction_time = datetime.fromisoformat(transaction_time)
    profiles = _profiles_table(connection)
    _emit(
        sink,
        phase="transaction",
        status="applying",
        preflight=preflight,
        transaction_result="in-progress",
        processed_in_open_transaction=0,
    )
    for index, plan in enumerate(plans, start=1):
        mark_failure_boundary("affected-row-write")
        result = connection.execute(
            sa.update(profiles)
            .where(
                profiles.c.id == plan.profile_id,
                profiles.c.schema_version == authorization.source_artifact_id,
                profiles.c.revision == plan.source_revision,
            )
            .values(
                schema_version=authorization.target_artifact_id,
                flags=copy.deepcopy(plan.target_flags),
                compliance=copy.deepcopy(plan.target_compliance),
                revision=plan.source_revision + 1,
                updated_at=transaction_time,
            )
        )
        if result.rowcount != 1:
            raise RetirementMigrationError("retirement_preflight_stale")
        mark_failure_boundary("after-affected-row")
        inject("after-affected-row", index, len(plans))
        if index == len(plans) or index % 1000 == 0:
            _emit(
                sink,
                phase="transaction",
                status="progress",
                preflight=preflight,
                transaction_result="in-progress",
                processed_in_open_transaction=index,
            )
    mark_failure_boundary("postcondition-check")
    if _count_channel(connection, authorization.source_artifact_id):
        raise RetirementMigrationError("retirement_transaction_failed")
    _assert_target_postconditions(connection, preflight)


def execute_synthetic_contract_transaction(
    connection: Connection,
    preflight: RetirementDatabasePreflight,
    converter: FrozenRetirementConverter,
    *,
    progress: ProgressSink | None = None,
    failure_injector: FailureInjector | None = None,
) -> RetirementTransactionOutcome:
    """Exercise the DB owner on a disposable contract fixture, never production."""
    if preflight.authorization.evidence_scope != "synthetic-contract-only":
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    return _execute_retirement_transaction(
        connection,
        preflight,
        converter,
        progress=progress,
        failure_injector=failure_injector,
    )


def _execute_retirement_transaction(
    connection: Connection,
    preflight: RetirementDatabasePreflight,
    converter: FrozenRetirementConverter,
    *,
    progress: ProgressSink | None,
    failure_injector: FailureInjector | None,
) -> RetirementTransactionOutcome:
    authorization = preflight.authorization
    _validate_authorization(authorization)
    _validate_preflight_identity(preflight)
    engine = connection.dialect.name
    if engine != preflight.engine or engine not in _SUPPORTED_ENGINES:
        raise RetirementMigrationError("retirement_preflight_stale", "database engine changed")
    if connection.in_transaction():
        raise RetirementMigrationError(
            "retirement_preflight_stale", "retirement requires a fresh connection"
        )
    _validate_converter(authorization, converter)
    sink = progress or _print_progress
    inject = failure_injector or (lambda _phase, _completed, _total: None)
    _emit(
        sink,
        phase="preflight-recheck",
        status="started",
        preflight=preflight,
        transaction_result="not-started",
        processed_in_open_transaction=0,
    )

    transaction: sa.engine.Transaction | None = None
    writes_started = False
    failure_boundary = "lock-and-preflight-recheck"
    try:
        if engine == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            transaction = connection.get_transaction()
            if transaction is None:  # pragma: no cover - SQLAlchemy invariant
                raise RetirementMigrationError("retirement_transaction_failed")
        else:
            transaction = connection.begin()
            connection.exec_driver_sql("LOCK TABLE profiles IN EXCLUSIVE MODE")

        _require_database_shape(connection)
        stamp = _read_stamp(connection)
        if stamp == authorization.target_revision:
            source_count = _count_channel(connection, authorization.source_artifact_id)
            if source_count:
                raise RetirementMigrationError("retirement_partial_state_detected")
            _assert_target_postconditions(connection, preflight)
            transaction.rollback()
            _emit(
                sink,
                phase="transaction",
                status="already-applied",
                preflight=preflight,
                transaction_result="no-op",
                processed_in_open_transaction=0,
            )
            return RetirementTransactionOutcome(
                code="retirement_already_applied",
                engine=engine,
                affected_count=0,
                source_artifact_id=authorization.source_artifact_id,
                target_artifact_id=authorization.target_artifact_id,
            )
        if stamp != authorization.source_revision:
            raise RetirementMigrationError("retirement_preflight_stale", "source stamp changed")

        profile_count, already_target_count, plans = _derive_row_plans(
            connection, authorization, converter
        )
        preflight.backup.validate_for(authorization, profile_count)
        if (
            profile_count != preflight.profile_count
            or already_target_count != preflight.already_target_count
            or len(plans) != preflight.affected_source_count
            or _row_set_digest(plans) != preflight.database_snapshot_digest
            or plans != preflight._plans
        ):
            raise RetirementMigrationError("retirement_preflight_stale", "profile snapshot changed")

        failure_boundary = "before-first-write"
        inject("before-first-write", 0, len(plans))
        transaction_time = connection.execute(sa.text("SELECT CURRENT_TIMESTAMP")).scalar_one()
        if engine == "sqlite" and isinstance(transaction_time, str):
            transaction_time = datetime.fromisoformat(transaction_time)
        profiles = _profiles_table(connection)
        _emit(
            sink,
            phase="transaction",
            status="applying",
            preflight=preflight,
            transaction_result="in-progress",
            processed_in_open_transaction=0,
        )
        for index, plan in enumerate(plans, start=1):
            writes_started = True
            failure_boundary = "affected-row-write"
            result = connection.execute(
                sa.update(profiles)
                .where(
                    profiles.c.id == plan.profile_id,
                    profiles.c.schema_version == authorization.source_artifact_id,
                    profiles.c.revision == plan.source_revision,
                )
                .values(
                    schema_version=authorization.target_artifact_id,
                    flags=copy.deepcopy(plan.target_flags),
                    compliance=copy.deepcopy(plan.target_compliance),
                    revision=plan.source_revision + 1,
                    updated_at=transaction_time,
                )
            )
            if result.rowcount != 1:
                raise RetirementMigrationError("retirement_preflight_stale")
            failure_boundary = "after-affected-row"
            inject("after-affected-row", index, len(plans))
            if index == len(plans) or index % 1000 == 0:
                _emit(
                    sink,
                    phase="transaction",
                    status="progress",
                    preflight=preflight,
                    transaction_result="in-progress",
                    processed_in_open_transaction=index,
                )

        failure_boundary = "postcondition-check"
        if _count_channel(connection, authorization.source_artifact_id):
            raise RetirementMigrationError("retirement_transaction_failed")
        _assert_target_postconditions(connection, preflight)
        failure_boundary = "before-stamp"
        inject("before-stamp", len(plans), len(plans))
        writes_started = True
        stamp_result = connection.execute(
            sa.text("UPDATE alembic_version SET version_num = :target WHERE version_num = :source"),
            {"source": authorization.source_revision, "target": authorization.target_revision},
        )
        if stamp_result.rowcount != 1:
            raise RetirementMigrationError("retirement_preflight_stale")
        failure_boundary = "before-commit"
        inject("before-commit", len(plans), len(plans))
        failure_boundary = "commit"
        transaction.commit()
        _emit(
            sink,
            phase="transaction",
            status="committed",
            preflight=preflight,
            transaction_result="committed",
            processed_in_open_transaction=len(plans),
        )
        return RetirementTransactionOutcome(
            code="retirement_applied",
            engine=engine,
            affected_count=len(plans),
            source_artifact_id=authorization.source_artifact_id,
            target_artifact_id=authorization.target_artifact_id,
        )
    except BaseException as exc:
        if transaction is not None and transaction.is_active:
            transaction.rollback()
        _emit(
            sink,
            phase="transaction",
            status="rolled-back",
            preflight=preflight,
            transaction_result="rolled-back",
            failure_boundary=failure_boundary,
            failure_code=_safe_failure_code(exc),
            recovery_direction="restore-verified-backup-to-new-clean-candidate",
        )
        if isinstance(exc, RetirementMigrationError) and not writes_started:
            raise
        raise RetirementMigrationError("retirement_transaction_failed") from exc


def reject_retirement_downgrade() -> None:
    """A retired source is recovered only by restoring the verified backup."""
    raise RetirementMigrationError("retirement_downgrade_unsupported")


def _derive_row_plans(
    connection: Connection,
    authorization: AuthorizedRetirement,
    converter: FrozenRetirementConverter,
) -> tuple[int, int, tuple[_RowPlan, ...]]:
    profiles = _profiles_table(connection)
    profile_count = int(
        connection.execute(sa.select(sa.func.count()).select_from(profiles)).scalar_one()
    )
    already_target_count = _count_channel(connection, authorization.target_artifact_id)
    rows = (
        connection.execute(
            sa.select(profiles)
            .where(profiles.c.schema_version == authorization.source_artifact_id)
            .order_by(profiles.c.id)
        )
        .mappings()
        .all()
    )
    plans: list[_RowPlan] = []
    for row in rows:
        flags = _strict_object(row["flags"], "conversion_source_invalid")
        compliance_value = row["compliance"]
        compliance = (
            None
            if compliance_value is None
            else _strict_object(compliance_value, "conversion_plan_blocked")
        )
        if not converter.source_valid(copy.deepcopy(flags)):
            raise RetirementMigrationError("conversion_source_invalid")
        converted = converter.convert(copy.deepcopy(flags), copy.deepcopy(compliance))
        if (
            not isinstance(converted, ConvertedProfile)
            or converted.compliance_disposition not in _COMPLIANCE_DISPOSITIONS
        ):
            raise RetirementMigrationError("conversion_plan_blocked")
        target_flags = _strict_object(converted.flags, "conversion_plan_blocked")
        target_compliance = (
            None
            if converted.compliance is None
            else _strict_object(converted.compliance, "conversion_plan_blocked")
        )
        if not converter.target_valid(copy.deepcopy(target_flags)):
            raise RetirementMigrationError("conversion_plan_blocked")
        source_revision = row["revision"]
        profile_id = row["id"]
        if (
            isinstance(source_revision, bool)
            or not isinstance(source_revision, int)
            or source_revision < 1
            or isinstance(profile_id, bool)
            or not isinstance(profile_id, int)
        ):
            raise RetirementMigrationError("retirement_preflight_stale")
        identity: dict[str, JsonValue] = {
            "manifest_digest": authorization.manifest_digest,
            "id": profile_id,
            "name": _json_scalar(row["name"]),
            "name_casefold": _json_scalar(row["name_casefold"]),
            "description": _json_scalar(row["description"]),
            "schema_version": authorization.source_artifact_id,
            "flags": copy.deepcopy(flags),
            "compliance": copy.deepcopy(compliance),
            "revision": source_revision,
            "created_at": _json_scalar(row["created_at"]),
            "updated_at": _json_scalar(row["updated_at"]),
            "deleted_at": _json_scalar(row["deleted_at"]),
            "target_flags": copy.deepcopy(target_flags),
            "target_compliance": copy.deepcopy(target_compliance),
            "compliance_disposition": converted.compliance_disposition,
        }
        plans.append(
            _RowPlan(
                profile_id=profile_id,
                source_revision=source_revision,
                source_flags=flags,
                source_compliance=compliance,
                target_flags=target_flags,
                target_compliance=target_compliance,
                compliance_disposition=converted.compliance_disposition,
                row_identity_digest=_domain_digest(_DATABASE_SNAPSHOT_DOMAIN, identity),
            )
        )
    return profile_count, already_target_count, tuple(plans)


def _row_set_digest(plans: tuple[_RowPlan, ...]) -> str:
    projection: dict[str, JsonValue] = {
        "affected_count": len(plans),
        "row_identity_digests": [plan.row_identity_digest for plan in plans],
    }
    return _domain_digest(_DATABASE_SNAPSHOT_DOMAIN, projection)


def _assert_target_postconditions(
    connection: Connection, preflight: RetirementDatabasePreflight
) -> None:
    profiles = _profiles_table(connection)
    authorization = preflight.authorization
    for plan in preflight._plans:
        row = (
            connection.execute(sa.select(profiles).where(profiles.c.id == plan.profile_id))
            .mappings()
            .one_or_none()
        )
        if (
            row is None
            or row["schema_version"] != authorization.target_artifact_id
            or row["revision"] != plan.source_revision + 1
            or _strict_object(row["flags"], "retirement_partial_state_detected")
            != plan.target_flags
            or (
                None
                if row["compliance"] is None
                else _strict_object(row["compliance"], "retirement_partial_state_detected")
            )
            != plan.target_compliance
        ):
            raise RetirementMigrationError("retirement_partial_state_detected")


def _profiles_table(connection: Connection) -> sa.Table:
    return sa.Table("profiles", sa.MetaData(), autoload_with=connection)


def _require_database_shape(connection: Connection) -> None:
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "profiles" not in tables or "alembic_version" not in tables or "policies" in tables:
        raise RetirementMigrationError("retirement_preflight_stale", "profile table shape")
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    if columns != _PROFILE_COLUMNS:
        raise RetirementMigrationError("retirement_preflight_stale", "profile column shape")


def _read_stamp(connection: Connection) -> str:
    rows = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars().all()
    if len(rows) != 1 or not isinstance(rows[0], str):
        raise RetirementMigrationError("retirement_preflight_stale", "Alembic stamp")
    return rows[0]


def _count_channel(connection: Connection, artifact_id: str) -> int:
    profiles = _profiles_table(connection)
    return int(
        connection.execute(
            sa.select(sa.func.count())
            .select_from(profiles)
            .where(profiles.c.schema_version == artifact_id)
        ).scalar_one()
    )


def _validate_converter(
    authorization: AuthorizedRetirement, converter: FrozenRetirementConverter
) -> None:
    if getattr(converter, "registry_digest", None) != authorization.recipe_registry_digest:
        raise RetirementMigrationError("conversion_recipe_registry_stale")


def _validate_authorization(authorization: AuthorizedRetirement) -> None:
    if not isinstance(authorization, AuthorizedRetirement):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    manifest = _strict_object(authorization.manifest, "retirement_manifest_identity_mismatch")
    digest = manifest.get("manifest_digest")
    if digest != authorization.manifest_digest:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    del manifest["manifest_digest"]
    if _domain_digest(_MANIFEST_DOMAIN, manifest) != authorization.manifest_digest:
        raise RetirementMigrationError("retirement_manifest_stale")


def _validate_preflight_identity(preflight: RetirementDatabasePreflight) -> None:
    payload = preflight.as_dict()
    digest = payload.pop("preflight_digest")
    if (
        digest != preflight.preflight_digest
        or _domain_digest(_PREFLIGHT_DOMAIN, payload) != preflight.preflight_digest
    ):
        raise RetirementMigrationError("retirement_preflight_stale")


def _required_text(value: Mapping[str, JsonValue], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    return item


def _strict_object(value: Any, code: str) -> dict[str, JsonValue]:
    try:
        copied = _strict_json_copy(value)
    except RetirementMigrationError as exc:
        raise RetirementMigrationError(code) from exc
    if not isinstance(copied, dict):
        raise RetirementMigrationError(code)
    return copied


def _strict_json_copy(value: Any, ancestors: set[int] | None = None) -> JsonValue:
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int):
        if not -9_007_199_254_740_991 <= value <= 9_007_199_254_740_991:
            raise RetirementMigrationError("retirement_manifest_identity_mismatch")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RetirementMigrationError("retirement_manifest_identity_mismatch")
        return value
    ancestors = set() if ancestors is None else ancestors
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in ancestors:
            raise RetirementMigrationError("retirement_manifest_identity_mismatch")
        copied: dict[str, JsonValue] = {}
        descendants = {*ancestors, object_id}
        for key, item in value.items():
            if not isinstance(key, str) or key in copied:
                raise RetirementMigrationError("retirement_manifest_identity_mismatch")
            copied[key] = _strict_json_copy(item, descendants)
        return copied
    if isinstance(value, list | tuple):
        object_id = id(value)
        if object_id in ancestors:
            raise RetirementMigrationError("retirement_manifest_identity_mismatch")
        descendants = {*ancestors, object_id}
        return [_strict_json_copy(item, descendants) for item in value]
    raise RetirementMigrationError("retirement_manifest_identity_mismatch")


def _canonical_json(value: JsonValue) -> bytes:
    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if isinstance(value, int):
        return str(value).encode("ascii")
    if isinstance(value, float):
        return _jcs_number(value).encode("ascii")
    if isinstance(value, list):
        return b"[" + b",".join(_canonical_json(item) for item in value) + b"]"
    if isinstance(value, dict):
        ordered = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return (
            b"{"
            + b",".join(
                _canonical_json(key) + b":" + _canonical_json(value[key]) for key in ordered
            )
            + b"}"
        )
    raise RetirementMigrationError("retirement_manifest_identity_mismatch")


def _jcs_number(value: float) -> str:
    if not math.isfinite(value):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")
    if value == 0:
        return "0"
    lexical = repr(value).lower()
    mantissa, separator, exponent_text = lexical.partition("e")
    exponent = int(exponent_text) if separator else 0
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        if separator:
            return _expand_scientific(mantissa, exponent)
        return mantissa[:-2] if mantissa.endswith(".0") else mantissa
    if not separator:
        mantissa, exponent = _scientific_from_fixed(mantissa)
    mantissa = mantissa[:-2] if mantissa.endswith(".0") else mantissa
    sign = "+" if exponent >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exponent)}"


def _expand_scientific(mantissa: str, exponent: int) -> str:
    sign = ""
    if mantissa.startswith("-"):
        sign, mantissa = "-", mantissa[1:]
    whole, _dot, fraction = mantissa.partition(".")
    digits = whole + fraction
    decimal_index = len(whole) + exponent
    if decimal_index <= 0:
        return sign + "0." + ("0" * -decimal_index) + digits
    if decimal_index >= len(digits):
        return sign + digits + ("0" * (decimal_index - len(digits)))
    return sign + digits[:decimal_index] + "." + digits[decimal_index:]


def _scientific_from_fixed(value: str) -> tuple[str, int]:
    sign = ""
    if value.startswith("-"):
        sign, value = "-", value[1:]
    whole, _dot, fraction = value.partition(".")
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return "0", 0
    if whole.lstrip("0"):
        exponent = len(whole.lstrip("0")) - 1
    else:
        exponent = -(len(fraction) - len(fraction.lstrip("0")) + 1)
    remainder = digits[1:].rstrip("0")
    return sign + digits[0] + ("." + remainder if remainder else ""), exponent


def _domain_digest(domain: bytes, value: Mapping[str, Any]) -> str:
    strict = _strict_object(value, "retirement_manifest_identity_mismatch")
    return hashlib.sha256(domain + _canonical_json(strict)).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == _SHA256_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


def _json_scalar(value: Any) -> JsonValue:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if value is None or isinstance(value, str | int | float | bool):
        return _strict_json_copy(value)
    raise RetirementMigrationError("retirement_preflight_stale")


def _emit(
    sink: ProgressSink,
    *,
    phase: str,
    status: str,
    preflight: RetirementDatabasePreflight,
    transaction_result: str,
    processed_in_open_transaction: int | None = None,
    failure_boundary: str | None = None,
    failure_code: str | None = None,
    recovery_direction: str = "none",
) -> None:
    sink(
        build_execution_evidence(
            phase=phase,
            status=status,
            preflight=preflight,
            transaction_result=transaction_result,
            processed_in_open_transaction=processed_in_open_transaction,
            failure_boundary=failure_boundary,
            failure_code=failure_code,
            recovery_direction=recovery_direction,
        )
    )


def _safe_failure_code(exc: BaseException) -> str:
    """Never project an exception message; it may carry a URL or row detail."""
    if isinstance(exc, RetirementMigrationError):
        return exc.code
    return "retirement_transaction_failed"


def _print_progress(event: Mapping[str, object]) -> None:
    ordered = " ".join(f"{key}={event[key]}" for key in sorted(event))
    print(f"[retired-esr] {ordered}", flush=True)
