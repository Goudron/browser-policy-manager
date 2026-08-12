#!/usr/bin/env python3
"""Plan a Firefox schema lifecycle change without changing a database.

The command consumes two explicit lifecycle catalog snapshots.  It never
defaults to the runtime catalog: a reviewer must be able to identify both sides
of a proposed bump.  Its optional database observation is deliberately narrow:
it returns aggregate counts only after the caller names a disposable or
verified-backup database and it issues read-only SQL only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.lifecycle_transition_plan import (
    LifecycleTransitionPlan,
    LifecycleTransitionPlanError,
    RetirementSuccessorMapping,
    build_lifecycle_transition_plan,
)
from app.core.profile_conversion_json import canonical_json
from app.core.retirement_convertibility_preflight import (
    RetirementConvertibilityPreflightError,
    SchemaArtifactBinding,
    load_exact_schema_containment_evidence,
    prove_retirement_total_convertibility,
)
from app.core.schema_channels import SchemaChannel, SchemaChannelSource
from migration_support.retirement_revision_materializer_v1 import (
    ALEMBIC_SOURCE_REVISION,
    ALEMBIC_TARGET_REVISION,
    materialize_exact_esr140_retirement_revision,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_VERSION = 1
_CATALOG_DOMAIN = b"bpm-schema-lifecycle-dry-run-catalog:v1\n"
_REPORT_DOMAIN = b"bpm-schema-lifecycle-dry-run-report:v1\n"
_SHA256_LENGTH = 64
_DATABASE_SCOPES = frozenset({"disposable", "verified-backup"})


class SchemaLifecycleDryRunError(RuntimeError):
    """The read-only lifecycle review could not be completed safely."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True, slots=True)
class DatabaseSelection:
    """Explicit aggregate-count target; its URL is never included in output."""

    url: str
    scope: str
    backup_evidence: Mapping[str, Any] | None


def _emit_default(message: str) -> None:
    print(message, flush=True)


def _progress(
    emit: Callable[[str], None],
    *,
    phase: str,
    channel: str,
    completed: int,
    total: int,
    detail: str,
) -> None:
    emit(f"phase={phase} channel={channel} [{completed}/{total}] {detail}")


def _read_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SchemaLifecycleDryRunError(code, path.name) from error
    if not isinstance(value, dict):
        raise SchemaLifecycleDryRunError(code, path.name)
    return value


def _require_string(value: Any, *, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaLifecycleDryRunError(code)
    return value


def _require_bool(value: Any, *, code: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaLifecycleDryRunError(code)
    return value


def _source_from_row(row: Mapping[str, Any]) -> SchemaChannelSource:
    source = row.get("source")
    if not isinstance(source, Mapping):
        raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
    documentation = source.get("documentation_input")
    linux = source.get("linux_policies_input")
    if not isinstance(documentation, Mapping) or not isinstance(linux, Mapping):
        raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
    output_path = _require_string(
        source.get("output_path"), code="lifecycle_catalog_manifest_malformed"
    )
    filename = _require_string(source.get("filename"), code="lifecycle_catalog_manifest_malformed")
    if Path(output_path).name != filename:
        raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
    return SchemaChannelSource(
        source_tag=_require_string(
            source.get("source_tag"), code="lifecycle_catalog_manifest_malformed"
        ),
        upstream_tag=_require_string(
            source.get("upstream_tag"), code="lifecycle_catalog_manifest_malformed"
        ),
        documentation_input_path=_require_string(
            documentation.get("local_path"), code="lifecycle_catalog_manifest_malformed"
        ),
        documentation_input_url=_require_string(
            documentation.get("url"), code="lifecycle_catalog_manifest_malformed"
        ),
        documentation_input_sha256=_require_string(
            documentation.get("sha256"), code="lifecycle_catalog_manifest_malformed"
        ),
        linux_policies_input_path=_require_string(
            linux.get("local_path"), code="lifecycle_catalog_manifest_malformed"
        ),
        linux_policies_input_url=_require_string(
            linux.get("url"), code="lifecycle_catalog_manifest_malformed"
        ),
        linux_policies_input_sha256=_require_string(
            linux.get("sha256"), code="lifecycle_catalog_manifest_malformed"
        ),
        output_path=output_path,
        filename=filename,
    )


def load_catalog(path: Path) -> tuple[tuple[SchemaChannel, ...], frozenset[str], str]:
    """Load one reviewed catalog-contract snapshot, not the runtime catalog."""
    document = _read_json(path, code="lifecycle_catalog_manifest_unreadable")
    rows = document.get("channels")
    implementation = document.get("implementation")
    if not isinstance(rows, list) or not isinstance(implementation, Mapping):
        raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
    bundled = implementation.get("generated_artifact_ids")
    if not isinstance(bundled, list) or not all(
        isinstance(value, str) and value for value in bundled
    ):
        raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
    channels: list[SchemaChannel] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
        support = row.get("support")
        roles = row.get("roles")
        if not isinstance(support, Mapping) or not isinstance(roles, Mapping):
            raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
        line_number = row.get("line_number")
        if isinstance(line_number, bool) or not isinstance(line_number, int):
            raise SchemaLifecycleDryRunError("lifecycle_catalog_manifest_malformed")
        channels.append(
            SchemaChannel(
                line_id=_require_string(
                    row.get("line_id"), code="lifecycle_catalog_manifest_malformed"
                ),
                artifact_id=_require_string(
                    row.get("artifact_id"), code="lifecycle_catalog_manifest_malformed"
                ),
                channel_id=_require_string(
                    row.get("channel_id"), code="lifecycle_catalog_manifest_malformed"
                ),
                family=_require_string(
                    row.get("family"), code="lifecycle_catalog_manifest_malformed"
                ),
                line_number=line_number,
                artifact_version=_require_string(
                    row.get("artifact_version"), code="lifecycle_catalog_manifest_malformed"
                ),
                label=_require_string(
                    row.get("label"), code="lifecycle_catalog_manifest_malformed"
                ),
                i18n_key=_require_string(
                    row.get("i18n_key"), code="lifecycle_catalog_manifest_malformed"
                ),
                support_state=_require_string(
                    support.get("state"), code="lifecycle_catalog_manifest_malformed"
                ),
                selectable=_require_bool(
                    row.get("selectable"), code="lifecycle_catalog_manifest_malformed"
                ),
                is_latest_esr=_require_bool(
                    roles.get("latest_esr"), code="lifecycle_catalog_manifest_malformed"
                ),
                is_product_default=_require_bool(
                    roles.get("product_default"), code="lifecycle_catalog_manifest_malformed"
                ),
                is_default_release=_require_bool(
                    roles.get("default_release"), code="lifecycle_catalog_manifest_malformed"
                ),
                recommendation_target_line_id=row.get("recommendation_target_line_id"),
                retirement_successor_line_id=row.get("retirement_successor_line_id"),
                source=_source_from_row(row),
            )
        )
    digest = hashlib.sha256(_CATALOG_DOMAIN + canonical_json(document)).hexdigest()
    return tuple(channels), frozenset(bundled), digest


def _sha256(value: Any, *, domain: bytes) -> str:
    return hashlib.sha256(domain + canonical_json(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _mapping_key(mapping: RetirementSuccessorMapping) -> tuple[str, str, str, str]:
    return (
        mapping.source.line_id,
        mapping.source.artifact_id,
        mapping.target.line_id,
        mapping.target.artifact_id,
    )


def _proof_readiness(
    plan: LifecycleTransitionPlan,
    candidate: tuple[SchemaChannel, ...],
    proof_path: Path | None,
) -> tuple[dict[str, object], tuple[str, ...]]:
    mappings = plan.retirement_successor_mappings
    if not mappings:
        return ({"status": "not-required", "checked_mappings": []}, ())
    if proof_path is None:
        return (
            {"status": "missing", "checked_mappings": [mapping.as_dict() for mapping in mappings]},
            ("retirement_total_convertibility_unproven",),
        )
    if len(mappings) != 1:
        return (
            {
                "status": "stale",
                "checked_mappings": [mapping.as_dict() for mapping in mappings],
            },
            ("retirement_total_convertibility_unproven",),
        )
    channels_by_line = {channel.line_id: channel for channel in candidate}
    mapping = mappings[0]
    try:
        source = SchemaArtifactBinding.from_channel(channels_by_line[mapping.source.line_id])
        target = SchemaArtifactBinding.from_channel(channels_by_line[mapping.target.line_id])
        evidence = load_exact_schema_containment_evidence(proof_path, source=source, target=target)
        total_report = prove_retirement_total_convertibility(
            plan,
            artifacts={source.artifact_id: source, target.artifact_id: target},
            containment_evidence=evidence,
        )
    except (
        KeyError,
        OSError,
        RetirementConvertibilityPreflightError,
        ValueError,
    ):
        return (
            {"status": "stale", "checked_mappings": [mapping.as_dict()]},
            ("retirement_total_convertibility_unproven",),
        )
    if not total_report.promotable:
        return (
            {"status": "unproven", "checked_mappings": [mapping.as_dict()]},
            ("retirement_total_convertibility_unproven",),
        )
    return (
        {
            "status": "complete",
            "checked_mappings": [mapping.as_dict()],
            "proof_artifact_digest": total_report.results[0].proof_artifact_digest,
            "report_digest": total_report.report_digest,
        },
        (),
    )


def _materializer_readiness(
    mappings: tuple[RetirementSuccessorMapping, ...],
    *,
    previous_catalog_path: Path,
    candidate_catalog_path: Path,
    proof_path: Path | None,
    proof_ready: bool,
) -> tuple[dict[str, object], tuple[str, ...]]:
    if not mappings:
        return ({"status": "not-applicable-no-retirement"}, ())
    if not proof_ready or proof_path is None:
        return (
            {"status": "blocked-proof-not-ready"},
            ("retirement_total_convertibility_unproven",),
        )
    if len(mappings) != 1 or _mapping_key(mappings[0]) != (
        "esr-140",
        "esr-140.13",
        "esr-153",
        "esr-153.0",
    ):
        return (
            {"status": "no-owned-materializer-for-transition"},
            ("retirement_materializer_missing",),
        )
    try:
        artifact = materialize_exact_esr140_retirement_revision(
            previous_catalog_path=previous_catalog_path,
            candidate_catalog_path=candidate_catalog_path,
            proof_path=proof_path,
            source_revision=ALEMBIC_SOURCE_REVISION,
            target_revision=ALEMBIC_TARGET_REVISION,
        )
    except Exception as error:  # Fail closed; exact owner codes are intentionally retained.
        code = getattr(error, "code", "retirement_materializer_unready")
        return ({"status": "blocked", "code": code}, (str(code),))
    return (
        {
            "status": "candidate-only-ready",
            "revision": artifact.revision,
            "source_sha256": artifact.source_sha256,
        },
        (),
    )


def _validate_backup_evidence(value: Mapping[str, Any] | None) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise SchemaLifecycleDryRunError("retirement_backup_evidence_missing")
    required = {
        "engine",
        "backup_sha256",
        "restore_identity_digest",
        "source_stamp",
        "restored_stamp",
        "source_profile_count",
        "restored_profile_count",
        "status",
        "integrity",
    }
    if (
        set(value) != required
        or not _is_sha256(value.get("backup_sha256"))
        or not _is_sha256(value.get("restore_identity_digest"))
    ):
        raise SchemaLifecycleDryRunError("retirement_backup_evidence_invalid")
    if value.get("status") != "verified-native-restore" or value.get("integrity") != "pass":
        raise SchemaLifecycleDryRunError("retirement_backup_evidence_invalid")
    return {
        "status": "declared-verified-backup",
        "execution_preflight": "required-before-activation",
    }


def _validate_database_selection(selection: DatabaseSelection | None) -> None:
    if selection is None:
        return
    if selection.scope not in _DATABASE_SCOPES:
        raise SchemaLifecycleDryRunError("retirement_database_scope_unsafe")
    parsed = urlparse(selection.url)
    if parsed.scheme not in {"sqlite", "postgresql", "postgresql+psycopg"}:
        raise SchemaLifecycleDryRunError("retirement_database_url_unsafe")
    if parsed.scheme == "sqlite":
        query = parse_qs(parsed.query)
        if query.get("mode") != ["ro"] or query.get("uri") != ["true"]:
            raise SchemaLifecycleDryRunError("retirement_database_sqlite_not_readonly")
    if selection.scope == "verified-backup":
        _validate_backup_evidence(selection.backup_evidence)


def _database_counts(
    selection: DatabaseSelection,
    mappings: tuple[RetirementSuccessorMapping, ...],
) -> dict[str, object]:
    """Return aggregate counts through a transaction declared read-only.

    This intentionally uses no ORM, metadata reflection, migration command, or
    DML.  A missing table is an observation failure, not a request to initialize
    the selected database.
    """
    engine = sa.create_engine(selection.url, future=True)
    try:
        with engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                connection.execute(sa.text("SET TRANSACTION READ ONLY"))
            profile_count = int(
                connection.execute(sa.text("SELECT count(*) FROM profiles")).scalar_one()
            )
            affected = [
                {
                    "source": {
                        "line_id": mapping.source.line_id,
                        "artifact_id": mapping.source.artifact_id,
                    },
                    "target": {
                        "line_id": mapping.target.line_id,
                        "artifact_id": mapping.target.artifact_id,
                    },
                    "affected_profile_count": int(
                        connection.execute(
                            sa.text(
                                "SELECT count(*) FROM profiles WHERE schema_version = :schema_version"
                            ),
                            {"schema_version": mapping.source.artifact_id},
                        ).scalar_one()
                    ),
                }
                for mapping in mappings
            ]
    except SQLAlchemyError as error:
        raise SchemaLifecycleDryRunError("retirement_database_observation_failed") from error
    finally:
        engine.dispose()
    backup = (
        _validate_backup_evidence(selection.backup_evidence)
        if selection.scope == "verified-backup"
        else {
            "status": "not-required-disposable",
            "execution_preflight": "required-before-activation",
        }
    )
    return {
        "status": "complete-read-only",
        "scope": selection.scope,
        "engine": engine.dialect.name,
        "profile_count": profile_count,
        "affected_profiles": affected,
        "backup": backup,
    }


def _safe_error_report(error: Exception) -> dict[str, object]:
    code = getattr(error, "code", "schema_lifecycle_dry_run_failed")
    return {
        "report_version": REPORT_VERSION,
        "status": "blocked",
        "blockers": [str(code)],
        "cache": {"state": "not-written"},
        "database": {"status": "not-accessed"},
        "mutation": "none",
    }


def run_dry_run(
    *,
    previous_catalog_path: Path,
    candidate_catalog_path: Path,
    proof_path: Path | None = None,
    database: DatabaseSelection | None = None,
    emit: Callable[[str], None] = _emit_default,
) -> dict[str, object]:
    """Build one deterministic candidate report and emit flushed real phases."""
    total = 5 + (1 if database is not None else 0)
    _progress(
        emit,
        phase="catalog-load",
        channel="previous",
        completed=0,
        total=total,
        detail="status=started",
    )
    previous, _previous_bundled, previous_digest = load_catalog(previous_catalog_path)
    _progress(
        emit,
        phase="catalog-load",
        channel="previous",
        completed=1,
        total=total,
        detail="status=complete",
    )
    candidate, bundled, candidate_digest = load_catalog(candidate_catalog_path)
    _progress(
        emit,
        phase="catalog-load",
        channel="candidate",
        completed=2,
        total=total,
        detail="status=complete",
    )
    plan = build_lifecycle_transition_plan(previous, candidate, bundled_artifact_ids=bundled)
    _progress(
        emit,
        phase="lifecycle-plan",
        channel="matrix",
        completed=3,
        total=total,
        detail="status=complete",
    )
    proof, proof_blockers = _proof_readiness(plan, candidate, proof_path)
    _progress(
        emit,
        phase="retirement-proof",
        channel="matrix",
        completed=4,
        total=total,
        detail=f"status={proof['status']}",
    )
    materializer, materializer_blockers = _materializer_readiness(
        plan.retirement_successor_mappings,
        previous_catalog_path=previous_catalog_path,
        candidate_catalog_path=candidate_catalog_path,
        proof_path=proof_path,
        proof_ready=proof["status"] == "complete",
    )
    _progress(
        emit,
        phase="candidate-materializer",
        channel="matrix",
        completed=5,
        total=total,
        detail=f"status={materializer['status']}",
    )
    _validate_database_selection(database)
    database_report: dict[str, object]
    if database is None:
        database_report = {
            "status": "not-requested",
            "affected_profiles": [],
            "backup": (
                {
                    "status": "not-checked",
                    "execution_preflight": "required-before-activation",
                }
                if plan.retirement_successor_mappings
                else {"status": "not-required-no-retirement"}
            ),
        }
    else:
        database_report = _database_counts(database, plan.retirement_successor_mappings)
        _progress(
            emit,
            phase="database-count",
            channel="selected",
            completed=6,
            total=total,
            detail="status=complete-read-only",
        )
    blockers = tuple(sorted(set((*proof_blockers, *materializer_blockers))))
    report_without_digest: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "status": "blocked" if blockers else "complete",
        "mutation": "none",
        "cache": {"state": "not-used-not-written"},
        "previous_catalog_digest": previous_digest,
        "candidate_catalog_digest": candidate_digest,
        "plan": plan.as_dict(),
        "retirement_proof": proof,
        "candidate_materializer": materializer,
        "database": database_report,
        "blockers": list(blockers),
    }
    report = {
        **report_without_digest,
        "report_digest": _sha256(report_without_digest, domain=_REPORT_DOMAIN),
    }
    completed = total if database is not None else 5
    _progress(
        emit,
        phase="complete",
        channel="matrix",
        completed=completed,
        total=total,
        detail=f"status={report['status']}",
    )
    return report


def _write_report(path: Path, report: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _text_report(report: Mapping[str, object]) -> str:
    plan = report.get("plan", {})
    if not isinstance(plan, Mapping):
        return json.dumps(report, ensure_ascii=True, sort_keys=True)
    blockers_value = report.get("blockers")
    blockers = (
        [blocker for blocker in blockers_value if isinstance(blocker, str)]
        if isinstance(blockers_value, list)
        else []
    )
    lines = [
        f"status={report['status']} mutation={report['mutation']} cache={report['cache']}",
        f"blockers={','.join(blockers) if blockers else 'none'}",
    ]
    for name in ("added_lines", "retained_lines", "refreshed_lines", "retired_lines"):
        entries = plan.get(name, [])
        lines.append(f"{name}={len(entries) if isinstance(entries, list) else 0}")
    for mapping in plan.get("retirement_successor_mappings", []):
        if isinstance(mapping, Mapping):
            source = mapping.get("source", {})
            target = mapping.get("target", {})
            if isinstance(source, Mapping) and isinstance(target, Mapping):
                lines.append(f"mapping={source.get('artifact_id')}->{target.get('artifact_id')}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-catalog", type=Path, required=True)
    parser.add_argument("--candidate-catalog", type=Path, required=True)
    parser.add_argument("--total-proof", type=Path)
    parser.add_argument("--database-url")
    parser.add_argument("--database-scope", choices=sorted(_DATABASE_SCOPES))
    parser.add_argument("--backup-evidence", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--report", type=Path, help="Explicit optional JSON evidence output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.database_url) != bool(args.database_scope):
        error = SchemaLifecycleDryRunError("retirement_database_selection_incomplete")
        print(
            "terminal-report="
            + json.dumps(_safe_error_report(error), ensure_ascii=True, sort_keys=True),
            flush=True,
        )
        return 1
    if args.backup_evidence is not None and args.database_scope != "verified-backup":
        error = SchemaLifecycleDryRunError("retirement_backup_evidence_scope_unsafe")
        print(
            "terminal-report="
            + json.dumps(_safe_error_report(error), ensure_ascii=True, sort_keys=True),
            flush=True,
        )
        return 1
    database = None
    try:
        backup_evidence = (
            _read_json(args.backup_evidence, code="retirement_backup_evidence_unreadable")
            if args.backup_evidence
            else None
        )
        if args.database_url:
            database = DatabaseSelection(args.database_url, args.database_scope, backup_evidence)
        report = run_dry_run(
            previous_catalog_path=args.previous_catalog,
            candidate_catalog_path=args.candidate_catalog,
            proof_path=args.total_proof,
            database=database,
        )
    except (SchemaLifecycleDryRunError, LifecycleTransitionPlanError, OSError, ValueError) as error:
        report = _safe_error_report(error)
    if args.report is not None:
        _write_report(args.report, report)
    rendered = (
        json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        if args.format == "json"
        else _text_report(report)
    )
    print(rendered, flush=True)
    print(
        "terminal-report="
        + json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
