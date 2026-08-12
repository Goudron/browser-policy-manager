"""Privacy-safe, deterministic evidence for offline ESR retirement work.

This module is intentionally migration-only.  It does not connect to a
database, inspect profile documents, or import ``app``.  The versioned
retirement owner supplies aggregate facts already derived under its safety
boundary; this module makes the externally observable projection explicit.

In particular, an in-flight update is *not* a successful partial migration.
Only a committed transaction reports transformed and unchanged totals.  A
rollback reports zero transformed rows and directs the operator to restore the
verified backup into a new clean candidate.
"""

from __future__ import annotations

from typing import Any, Protocol


class _Authorization(Protocol):
    @property
    def source_line_id(self) -> str: ...

    @property
    def source_artifact_id(self) -> str: ...

    @property
    def target_line_id(self) -> str: ...

    @property
    def target_artifact_id(self) -> str: ...


class _Backup(Protocol):
    @property
    def status(self) -> str: ...

    @property
    def backup_sha256(self) -> str: ...

    @property
    def restore_identity_digest(self) -> str: ...

    @property
    def integrity(self) -> str: ...


class _Preflight(Protocol):
    @property
    def authorization(self) -> _Authorization: ...

    @property
    def engine(self) -> str: ...

    @property
    def profile_count(self) -> int: ...

    @property
    def affected_source_count(self) -> int: ...

    @property
    def already_target_count(self) -> int: ...

    @property
    def backup(self) -> _Backup: ...


_RECOVER_FROM_VERIFIED_BACKUP = "restore-verified-backup-to-new-clean-candidate"
_NO_RECOVERY_REQUIRED = "none"
_STATIC_PROOF_RECOVERY = "complete-schema-wide-proof-before-retirement"


def build_static_gate_block_evidence(
    report: Any,
) -> dict[str, object]:
    """Project an unpromotable total-proof report without opening a database.

    The proof report itself may contain schema pointers for maintainer review.
    Those pointers are deliberately excluded from the operator event: this
    evidence says only which exact artifacts were blocked and the safe code.
    """
    results = getattr(report, "results", ())
    if getattr(report, "promotable", False) or not results:
        raise ValueError("static block evidence requires an unpromotable retirement report")

    source_target = tuple(
        sorted(
            (
                _source_target_from_result(result)
                for result in results
                if not bool(getattr(result, "promotable", False))
            ),
            key=lambda item: (item["source"]["artifact_id"], item["target"]["artifact_id"]),
        )
    )
    if not source_target:
        raise ValueError("static block evidence requires a blocked retirement mapping")

    # One transition revision has exactly one source/target mapping.  Keeping a
    # deterministic aggregate list here lets a future multi-edge review remain
    # observable without hiding a blocker or leaking its proof locations.
    blocker_codes = tuple(
        sorted(
            {
                code
                for result in results
                if not bool(getattr(result, "promotable", False))
                for code in tuple(getattr(result, "blockers", ()))
                if isinstance(code, str)
            }
        )
    )
    return {
        "event_version": 1,
        "phase": "static-gate",
        "status": "blocked",
        "engine": None,
        "mappings": list(source_target),
        "counts": _counts(
            profile_count=0,
            affected_source_count=0,
            already_target_count=0,
            transformed_count=0,
            unchanged_count=0,
            processed_in_open_transaction=0,
        ),
        "transaction_result": "not-started",
        "backup": _backup_not_required(),
        "failure_boundary": "static-gate",
        "failure_code": blocker_codes[0]
        if blocker_codes
        else "retirement_total_convertibility_unproven",
        "blocker_codes": list(blocker_codes),
        "recovery_direction": _STATIC_PROOF_RECOVERY,
    }


def build_preflight_evidence(preflight: _Preflight) -> dict[str, object]:
    """Return the successful read-only preflight observation."""
    return _event(
        phase="preflight",
        status="complete",
        preflight=preflight,
        transaction_result="not-started",
        transformed_count=0,
        unchanged_count=preflight.profile_count,
        processed_in_open_transaction=0,
        failure_boundary=None,
        failure_code=None,
        recovery_direction=_NO_RECOVERY_REQUIRED,
    )


def build_execution_evidence(
    *,
    phase: str,
    status: str,
    preflight: _Preflight,
    transaction_result: str,
    processed_in_open_transaction: int | None = None,
    failure_boundary: str | None = None,
    failure_code: str | None = None,
    recovery_direction: str = _NO_RECOVERY_REQUIRED,
) -> dict[str, object]:
    """Build one safe transaction event from aggregate migration facts.

    ``committed`` is the only terminal success.  While the transaction is
    open, processing progress is exposed separately and successful totals stay
    unknown.  This prevents consumers from mistaking an eventual rollback for
    partial success.
    """
    if transaction_result == "committed":
        transformed_count: int | None = preflight.affected_source_count
        unchanged_count: int | None = preflight.profile_count - preflight.affected_source_count
    elif transaction_result in {"rolled-back", "not-started", "no-op"}:
        transformed_count = 0
        unchanged_count = preflight.profile_count
    else:
        transformed_count = None
        unchanged_count = None
    return _event(
        phase=phase,
        status=status,
        preflight=preflight,
        transaction_result=transaction_result,
        transformed_count=transformed_count,
        unchanged_count=unchanged_count,
        processed_in_open_transaction=processed_in_open_transaction,
        failure_boundary=failure_boundary,
        failure_code=failure_code,
        recovery_direction=recovery_direction,
    )


def _event(
    *,
    phase: str,
    status: str,
    preflight: _Preflight,
    transaction_result: str,
    transformed_count: int | None,
    unchanged_count: int | None,
    processed_in_open_transaction: int | None,
    failure_boundary: str | None,
    failure_code: str | None,
    recovery_direction: str,
) -> dict[str, object]:
    authorization = preflight.authorization
    return {
        "event_version": 1,
        "phase": phase,
        "status": status,
        "engine": preflight.engine,
        "source": {
            "line_id": authorization.source_line_id,
            "artifact_id": authorization.source_artifact_id,
        },
        "target": {
            "line_id": authorization.target_line_id,
            "artifact_id": authorization.target_artifact_id,
        },
        "counts": _counts(
            profile_count=preflight.profile_count,
            affected_source_count=preflight.affected_source_count,
            already_target_count=preflight.already_target_count,
            transformed_count=transformed_count,
            unchanged_count=unchanged_count,
            processed_in_open_transaction=processed_in_open_transaction,
        ),
        "transaction_result": transaction_result,
        "backup": {
            "status": preflight.backup.status,
            "backup_sha256": preflight.backup.backup_sha256,
            "restore_identity_digest": preflight.backup.restore_identity_digest,
            "integrity": preflight.backup.integrity,
        },
        "failure_boundary": failure_boundary,
        "failure_code": failure_code,
        "recovery_direction": recovery_direction,
    }


def _string_attribute(value: object, name: str) -> str:
    attribute = getattr(value, name, None)
    if not isinstance(attribute, str) or not attribute:
        raise ValueError("retirement result has no safe source/target identity")
    return attribute


def _source_target_from_result(result: object) -> dict[str, dict[str, str]]:
    source = getattr(result, "source", None)
    target = getattr(result, "target", None)
    source_line = _string_attribute(source, "line_id")
    source_artifact = _string_attribute(source, "artifact_id")
    target_line = _string_attribute(target, "line_id")
    target_artifact = _string_attribute(target, "artifact_id")
    return {
        "source": {"line_id": source_line, "artifact_id": source_artifact},
        "target": {"line_id": target_line, "artifact_id": target_artifact},
    }


def _counts(
    *,
    profile_count: int,
    affected_source_count: int,
    already_target_count: int,
    transformed_count: int | None,
    unchanged_count: int | None,
    processed_in_open_transaction: int | None,
) -> dict[str, int | None]:
    return {
        "profile_count": profile_count,
        "affected_source_count": affected_source_count,
        "already_target_count": already_target_count,
        "transformed_count": transformed_count,
        "unchanged_count": unchanged_count,
        "processed_in_open_transaction": processed_in_open_transaction,
    }


def _backup_not_required() -> dict[str, str | None]:
    return {
        "status": "not-required-static-gate-blocked",
        "backup_sha256": None,
        "restore_identity_digest": None,
        "integrity": "not-run",
    }
