"""Candidate-only materializer for the exact ESR 140.13 retirement revision.

This module is release tooling, not application runtime and not an active
Alembic revision.  It can render an Alembic-compatible revision only from a
candidate lifecycle catalog in which ESR 140.13 is actually retired.  The
current BPM 0.9.5 catalog therefore fails closed and the active Alembic graph
is unchanged.

The rendered revision embeds the reviewed transition manifest and complete
M6-02 report.  At execution it reopens the promoted candidate catalog, exact
proof and bundled schemas, verifies every immutable digest, requires explicit
native-backup evidence and delegates the locked transaction to the versioned
M6-03 owner.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pprint
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from jsonschema import Draft202012Validator
from sqlalchemy.engine import Connection

from migration_support.retirement_owner_v1 import (
    BackupEvidence,
    ConvertedProfile,
    RetirementDatabasePreflight,
    RetirementMigrationError,
    RetirementTransactionOutcome,
    apply_retirement_profiles_in_alembic_transaction,
    authorize_production_retirement,
    build_database_preflight,
    reject_retirement_downgrade,
)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type ProgressSink = Callable[[Mapping[str, object]], None]


class _SupportedEsrLine(TypedDict):
    line_id: str
    line_number: int
    artifact_id: str


_MANIFEST_DOMAIN = b"bpm-retired-esr-transition-manifest:v1\n"
_PROOF_DOMAIN = b"bpm-retired-esr-exact-proof-artifact:v1\n"
_COMPLIANCE_DOMAIN = b"bpm-profile-compliance:v1\n"
_REVISION_ID = re.compile(r"^[a-zA-Z0-9_]+$")

SOURCE_LINE_ID = "esr-140"
SOURCE_ARTIFACT_ID = "esr-140.13"
TARGET_LINE_ID = "esr-153"
TARGET_ARTIFACT_ID = "esr-153.0"
SOURCE_SCHEMA_RELATIVE_PATH = Path("app/schemas/policies/firefox-esr-140.13.json")
TARGET_SCHEMA_RELATIVE_PATH = Path("app/schemas/policies/firefox-esr-153.0.json")
DEFAULT_CANDIDATE_CATALOG_RELATIVE_PATH = Path(
    "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
)
DEFAULT_PROOF_RELATIVE_PATH = Path(
    "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)

PREVIOUS_CATALOG_DIGEST = "d34ab9a1142f5f0838a9ea8ed9e5de5798853a2ac6c7483b9625e9d937361812"
SOURCE_SCHEMA_BUNDLE_SHA256 = "9dd77157022cf463b2c0cce2a168527b2809e9647ada369583b9e459732c26d4"
SOURCE_VALIDATION_SCHEMA_SHA256 = "930803d175d7f4942d7101812a9cece1325026d0787760676c8dda8ada07f6cd"
TARGET_SCHEMA_BUNDLE_SHA256 = "160d2ae865a2a0fd06df4c95c947babe429e63fd48029cf2d2c121c5f37f946d"
TARGET_VALIDATION_SCHEMA_SHA256 = "1ca36d178cc5a80a3b16a26a98a9941e8575bb30dfb064c5167dfed853d94260"
RECIPE_REGISTRY_DIGEST = "1d4b572f358a7ff9f7e23beb5a2a27104cec4c2d3451ad8a49099cf8665113a6"
TOTAL_PROOF_ARTIFACT_DIGEST = "9de84bde21e11d161d48297d19cc2447c36ac052d6cef8aed7727b8fa29746ef"
ALEMBIC_SOURCE_REVISION = "20260804_add_profile_name_casefold"
ALEMBIC_TARGET_REVISION = "20260812_retire_esr140_13_to_esr153_0"

FROZEN_TOTAL_REPORT: dict[str, JsonValue] = {
    "kind": "retirement-total-convertibility-report",
    "contract_version": 1,
    "status": "complete",
    "results": [
        {
            "source": {
                "line_id": SOURCE_LINE_ID,
                "artifact_id": SOURCE_ARTIFACT_ID,
                "schema_bundle_sha256": SOURCE_SCHEMA_BUNDLE_SHA256,
                "validation_schema_sha256": SOURCE_VALIDATION_SCHEMA_SHA256,
            },
            "target": {
                "line_id": TARGET_LINE_ID,
                "artifact_id": TARGET_ARTIFACT_ID,
                "schema_bundle_sha256": TARGET_SCHEMA_BUNDLE_SHA256,
                "validation_schema_sha256": TARGET_VALIDATION_SCHEMA_SHA256,
            },
            "successor_line_id": TARGET_LINE_ID,
            "recipe_registry": {
                "registry_id": "firefox-profile-conversion",
                "registry_version": 1,
                "recipes": [],
                "registry_digest": RECIPE_REGISTRY_DIGEST,
            },
            "status": "complete",
            "method": "schema-containment",
            "uncovered_schema_locations": [],
            "proof_artifact_digest": TOTAL_PROOF_ARTIFACT_DIGEST,
            "blockers": [],
            "mutation": "none",
            "result_digest": ("775ef3690ab57d85abe137c70c8c8595f8d26d434592852f71d96164c13956b8"),
        }
    ],
    "report_digest": "f1c6ff2bf8818ff00f3d25ef1dea3f82a64dc56a5d3a49df1e666f8c36716ec9",
}


@dataclass(frozen=True, slots=True)
class MaterializedRetirementRevision:
    """Deterministic candidate artifact; it is not installed in the active graph."""

    revision: str
    down_revision: str
    manifest: dict[str, JsonValue]
    candidate_catalog_digest: str
    source: str
    source_sha256: str


class ExactIdentityConverter:
    """Migration-owned exact-schema validator and identity policy converter."""

    registry_digest = RECIPE_REGISTRY_DIGEST

    def __init__(self, repository_root: Path) -> None:
        source = _load_bound_schema(
            repository_root / SOURCE_SCHEMA_RELATIVE_PATH,
            raw_digest=SOURCE_SCHEMA_BUNDLE_SHA256,
            normalized_digest=SOURCE_VALIDATION_SCHEMA_SHA256,
        )
        target = _load_bound_schema(
            repository_root / TARGET_SCHEMA_RELATIVE_PATH,
            raw_digest=TARGET_SCHEMA_BUNDLE_SHA256,
            normalized_digest=TARGET_VALIDATION_SCHEMA_SHA256,
        )
        self._source_validator = Draft202012Validator(source)
        self._target_validator = Draft202012Validator(target)

    def source_valid(self, flags: dict[str, JsonValue]) -> bool:
        return self._source_validator.is_valid(flags)

    def target_valid(self, flags: dict[str, JsonValue]) -> bool:
        return self._target_validator.is_valid(flags)

    def convert(
        self,
        flags: dict[str, JsonValue],
        compliance: dict[str, JsonValue] | None,
    ) -> ConvertedProfile:
        target_flags = copy.deepcopy(flags)
        if compliance is None:
            return ConvertedProfile(
                flags=target_flags,
                compliance=None,
                compliance_disposition="absent",
            )
        source_compliance = copy.deepcopy(compliance)
        invalidated: dict[str, JsonValue] = {
            "schema_version": 1,
            "status": "invalidated",
            "reason_code": "compliance_target_proof_unavailable",
            "source_artifact_id": SOURCE_ARTIFACT_ID,
            "target_artifact_id": TARGET_ARTIFACT_ID,
            "source_compliance_digest": hashlib.sha256(
                _COMPLIANCE_DOMAIN + _canonical_json(source_compliance)
            ).hexdigest(),
            "current_claims": False,
            "preserved_source": source_compliance,
        }
        return ConvertedProfile(
            flags=target_flags,
            compliance=invalidated,
            compliance_disposition="invalidated-preserved",
        )


def materialize_exact_esr140_retirement_revision(
    *,
    previous_catalog_path: Path,
    candidate_catalog_path: Path,
    proof_path: Path,
    source_revision: str,
    target_revision: str,
) -> MaterializedRetirementRevision:
    """Render a candidate revision after every static binding succeeds.

    The function returns text and never writes it into ``alembic/versions``.
    Release activation must deliberately install the reviewed artifact later.
    """
    _validate_revision_pair(source_revision, target_revision)
    previous = _load_object(previous_catalog_path, "retirement_catalog_identity_mismatch")
    candidate = _load_object(candidate_catalog_path, "retirement_catalog_identity_mismatch")
    previous_digest = _digest(previous)
    candidate_digest = _digest(candidate)
    if previous_digest != PREVIOUS_CATALOG_DIGEST:
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")

    supported = _validate_exact_catalog_transition(previous, candidate)
    _validate_proof_artifact(proof_path)
    repository_root = previous_catalog_path.resolve().parents[2]
    _validate_active_graph(repository_root, source_revision, target_revision)
    ExactIdentityConverter(repository_root)

    manifest_projection: dict[str, JsonValue] = {
        "kind": "retired-esr-transition-manifest",
        "contract_version": 1,
        "transition_id": "retire-esr140.13-to-esr153.0-v1",
        "evidence_scope": "production-exact-artifacts",
        "previous_catalog_digest": previous_digest,
        "candidate_catalog_digest": candidate_digest,
        "source": {
            "family": "esr",
            "line_id": SOURCE_LINE_ID,
            "line_number": 140,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "schema_bundle_sha256": SOURCE_SCHEMA_BUNDLE_SHA256,
            "validation_schema_sha256": SOURCE_VALIDATION_SCHEMA_SHA256,
        },
        "target": {
            "family": "esr",
            "line_id": TARGET_LINE_ID,
            "line_number": 153,
            "artifact_id": TARGET_ARTIFACT_ID,
            "schema_bundle_sha256": TARGET_SCHEMA_BUNDLE_SHA256,
            "validation_schema_sha256": TARGET_VALIDATION_SCHEMA_SHA256,
        },
        "candidate_supported_esr_lines": _json_lines(supported),
        "declared_successor_line_id": TARGET_LINE_ID,
        "conversion_contract_version": 1,
        "recipe_registry_version": 1,
        "recipe_registry_digest": RECIPE_REGISTRY_DIGEST,
        "total_proof_artifact_digest": TOTAL_PROOF_ARTIFACT_DIGEST,
        "alembic_source_revision": source_revision,
        "alembic_target_revision": target_revision,
    }
    manifest = {
        **manifest_projection,
        "manifest_digest": hashlib.sha256(
            _MANIFEST_DOMAIN + _canonical_json(manifest_projection)
        ).hexdigest(),
    }
    authorize_production_retirement(manifest, FROZEN_TOTAL_REPORT)
    source = _render_revision(
        revision=target_revision,
        down_revision=source_revision,
        manifest=manifest,
        candidate_catalog_digest=candidate_digest,
    )
    return MaterializedRetirementRevision(
        revision=target_revision,
        down_revision=source_revision,
        manifest=manifest,
        candidate_catalog_digest=candidate_digest,
        source=source,
        source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
    )


def execute_materialized_revision(
    connection: Connection,
    *,
    manifest: Mapping[str, Any],
    total_report: Mapping[str, Any],
    candidate_catalog_path: Path,
    proof_path: Path,
    repository_root: Path,
    backup: BackupEvidence,
    no_active_writers: bool,
    progress: ProgressSink | None = None,
) -> tuple[RetirementDatabasePreflight, RetirementTransactionOutcome]:
    """Execute one already-materialized revision inside Alembic's transaction."""
    sink = progress or _print_progress
    authorization = authorize_production_retirement(manifest, total_report)
    candidate = _load_object(candidate_catalog_path, "retirement_catalog_identity_mismatch")
    if _digest(candidate) != authorization.manifest.get("candidate_catalog_digest"):
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")
    _validate_candidate_manifest_binding(candidate, authorization.manifest)
    _validate_proof_artifact(proof_path)
    converter = ExactIdentityConverter(repository_root)
    preflight = build_database_preflight(
        connection,
        authorization,
        converter,
        backup,
        no_active_writers=no_active_writers,
        progress=sink,
    )
    outcome = apply_retirement_profiles_in_alembic_transaction(
        connection,
        preflight,
        converter,
        progress=sink,
    )
    return preflight, outcome


def backup_evidence_from_mapping(value: Any) -> BackupEvidence:
    """Parse only the explicit, value-free Alembic Config backup attribute."""
    if not isinstance(value, Mapping):
        raise RetirementMigrationError("retirement_backup_unverified")
    expected = {
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
    if set(value) != expected:
        raise RetirementMigrationError("retirement_backup_unverified")
    text_keys = expected - {"source_profile_count", "restored_profile_count"}
    if any(not isinstance(value[key], str) for key in text_keys):
        raise RetirementMigrationError("retirement_backup_unverified")
    for key in ("source_profile_count", "restored_profile_count"):
        count = value[key]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RetirementMigrationError("retirement_backup_unverified")
    try:
        return BackupEvidence(**{key: value[key] for key in expected})
    except TypeError as exc:
        raise RetirementMigrationError("retirement_backup_unverified") from exc


def _render_revision(
    *,
    revision: str,
    down_revision: str,
    manifest: Mapping[str, Any],
    candidate_catalog_digest: str,
) -> str:
    manifest_literal = pprint.pformat(dict(manifest), sort_dicts=False, width=100)
    report_literal = pprint.pformat(FROZEN_TOTAL_REPORT, sort_dicts=False, width=100)
    return f'''"""retire exact Firefox ESR 140.13 profiles to ESR 153.0

Candidate-only artifact generated by retirement_revision_materializer_v1.
It is inert until deliberately installed in the reviewed Alembic graph.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from migration_support.retirement_revision_materializer_v1 import (
    DEFAULT_CANDIDATE_CATALOG_RELATIVE_PATH,
    DEFAULT_PROOF_RELATIVE_PATH,
    backup_evidence_from_mapping,
    execute_materialized_revision,
)
from migration_support.retirement_owner_v1 import reject_retirement_downgrade

revision = {revision!r}
down_revision = {down_revision!r}
branch_labels = None
depends_on = None

CANDIDATE_CATALOG_DIGEST = {candidate_catalog_digest!r}
MANIFEST = {manifest_literal}
TOTAL_REPORT = {report_literal}


def upgrade() -> None:
    context = op.get_context()
    attributes = context.config.attributes
    repository_root = Path(attributes.get("retirement_repository_root", Path(__file__).resolve().parents[2]))
    candidate_catalog_path = Path(
        attributes.get(
            "retirement_candidate_catalog_path",
            repository_root / DEFAULT_CANDIDATE_CATALOG_RELATIVE_PATH,
        )
    )
    proof_path = Path(
        attributes.get(
            "retirement_proof_path",
            repository_root / DEFAULT_PROOF_RELATIVE_PATH,
        )
    )
    backup = backup_evidence_from_mapping(attributes.get("retirement_backup_evidence"))
    execute_materialized_revision(
        op.get_bind(),
        manifest=MANIFEST,
        total_report=TOTAL_REPORT,
        candidate_catalog_path=candidate_catalog_path,
        proof_path=proof_path,
        repository_root=repository_root,
        backup=backup,
        no_active_writers=attributes.get("retirement_no_active_writers") is True,
    )


def downgrade() -> None:
    reject_retirement_downgrade()
'''


def _validate_exact_catalog_transition(
    previous: Mapping[str, Any], candidate: Mapping[str, Any]
) -> list[_SupportedEsrLine]:
    previous_rows = _catalog_rows(previous)
    candidate_rows = _catalog_rows(candidate)
    source_before = previous_rows.get(SOURCE_LINE_ID)
    source_after = candidate_rows.get(SOURCE_LINE_ID)
    target_before = previous_rows.get(TARGET_LINE_ID)
    target_after = candidate_rows.get(TARGET_LINE_ID)
    older_supported = candidate_rows.get("esr-115")
    if not all(
        isinstance(row, Mapping)
        for row in (source_before, source_after, target_before, target_after)
    ):
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")
    assert isinstance(source_before, Mapping)
    assert isinstance(source_after, Mapping)
    assert isinstance(target_before, Mapping)
    assert isinstance(target_after, Mapping)
    if (
        source_before.get("artifact_id") != SOURCE_ARTIFACT_ID
        or _support_state(source_before) != "supported"
        or source_before.get("retirement_successor_line_id") != TARGET_LINE_ID
        or source_after.get("artifact_id") != SOURCE_ARTIFACT_ID
        or _support_state(source_after) != "retired"
        or source_after.get("selectable") is not False
        or target_before.get("artifact_id") != TARGET_ARTIFACT_ID
        or target_after.get("artifact_id") != TARGET_ARTIFACT_ID
        or _support_state(target_after) != "supported"
        or target_after.get("selectable") is not True
        or not isinstance(older_supported, Mapping)
        or older_supported.get("retirement_successor_line_id") != TARGET_LINE_ID
    ):
        raise RetirementMigrationError("retirement_catalog_not_retired")
    supported = _supported_esr_projection(candidate)
    if not any(row["line_id"] == TARGET_LINE_ID for row in supported):
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")
    if any(140 < row["line_number"] < 153 for row in supported):
        raise RetirementMigrationError("retirement_successor_skips_supported_intermediate")
    return supported


def _validate_candidate_manifest_binding(
    candidate: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    rows = _catalog_rows(candidate)
    source = rows.get(SOURCE_LINE_ID)
    target = rows.get(TARGET_LINE_ID)
    older_supported = rows.get("esr-115")
    if (
        not isinstance(source, Mapping)
        or not isinstance(target, Mapping)
        or source.get("artifact_id") != SOURCE_ARTIFACT_ID
        or _support_state(source) != "retired"
        or source.get("selectable") is not False
        or source.get("retirement_successor_line_id") != TARGET_LINE_ID
        or target.get("artifact_id") != TARGET_ARTIFACT_ID
        or _support_state(target) != "supported"
        or not isinstance(older_supported, Mapping)
        or older_supported.get("retirement_successor_line_id") != TARGET_LINE_ID
        or _json_lines(_supported_esr_projection(candidate))
        != manifest.get("candidate_supported_esr_lines")
    ):
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")


def _json_lines(lines: list[_SupportedEsrLine]) -> list[JsonValue]:
    projection: list[JsonValue] = []
    for line in lines:
        projection.append(
            {
                "line_id": line["line_id"],
                "line_number": line["line_number"],
                "artifact_id": line["artifact_id"],
            }
        )
    return projection


def _supported_esr_projection(catalog: Mapping[str, Any]) -> list[_SupportedEsrLine]:
    result: list[_SupportedEsrLine] = []
    for row in _catalog_rows(catalog).values():
        if row.get("family") == "esr" and _support_state(row) == "supported":
            line_number = row.get("line_number")
            line_id = row.get("line_id")
            artifact_id = row.get("artifact_id")
            if (
                isinstance(line_number, bool)
                or not isinstance(line_number, int)
                or not isinstance(line_id, str)
                or not isinstance(artifact_id, str)
            ):
                raise RetirementMigrationError("retirement_catalog_identity_mismatch")
            result.append(
                {
                    "line_id": line_id,
                    "line_number": line_number,
                    "artifact_id": artifact_id,
                }
            )
    return sorted(result, key=lambda row: (row["line_number"], row["line_id"]))


def _catalog_rows(catalog: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    values = catalog.get("channels")
    if not isinstance(values, list):
        raise RetirementMigrationError("retirement_catalog_identity_mismatch")
    result: dict[str, Mapping[str, Any]] = {}
    for row in values:
        if not isinstance(row, Mapping) or not isinstance(row.get("line_id"), str):
            raise RetirementMigrationError("retirement_catalog_identity_mismatch")
        line_id = str(row["line_id"])
        if line_id in result:
            raise RetirementMigrationError("retirement_catalog_identity_mismatch")
        result[line_id] = row
    return result


def _support_state(row: Mapping[str, Any]) -> Any:
    support = row.get("support")
    return support.get("state") if isinstance(support, Mapping) else row.get("support_state")


def _validate_revision_pair(source_revision: str, target_revision: str) -> None:
    if (
        not _REVISION_ID.fullmatch(source_revision)
        or not _REVISION_ID.fullmatch(target_revision)
        or source_revision == target_revision
        or len(source_revision) > 128
        or len(target_revision) > 128
        or source_revision != ALEMBIC_SOURCE_REVISION
        or target_revision != ALEMBIC_TARGET_REVISION
    ):
        raise RetirementMigrationError("retirement_manifest_identity_mismatch")


def _validate_active_graph(
    repository_root: Path, source_revision: str, target_revision: str
) -> None:
    config = Config(str(repository_root / "alembic.ini"))
    config.set_main_option("script_location", str(repository_root / "alembic"))
    try:
        scripts = ScriptDirectory.from_config(config)
        heads = scripts.get_heads()
        known_revisions = {item.revision for item in scripts.walk_revisions()}
    except (CommandError, OSError, RuntimeError) as exc:
        raise RetirementMigrationError("retirement_alembic_graph_stale") from exc
    if heads != [source_revision] or target_revision in known_revisions:
        raise RetirementMigrationError("retirement_alembic_graph_stale")


def _validate_proof_artifact(path: Path) -> None:
    proof = _load_object(path, "retirement_proof_artifact_identity_mismatch")
    claimed = proof.get("proof_artifact_digest")
    projection = dict(proof)
    projection.pop("proof_artifact_digest", None)
    actual = hashlib.sha256(_PROOF_DOMAIN + _canonical_json(projection)).hexdigest()
    source = proof.get("source")
    target = proof.get("target")
    registry = proof.get("recipe_registry")
    if (
        claimed != TOTAL_PROOF_ARTIFACT_DIGEST
        or actual != TOTAL_PROOF_ARTIFACT_DIGEST
        or not isinstance(source, Mapping)
        or not isinstance(target, Mapping)
        or not isinstance(registry, Mapping)
        or source.get("artifact_id") != SOURCE_ARTIFACT_ID
        or source.get("schema_bundle_sha256") != SOURCE_SCHEMA_BUNDLE_SHA256
        or source.get("validation_schema_sha256") != SOURCE_VALIDATION_SCHEMA_SHA256
        or target.get("artifact_id") != TARGET_ARTIFACT_ID
        or target.get("schema_bundle_sha256") != TARGET_SCHEMA_BUNDLE_SHA256
        or target.get("validation_schema_sha256") != TARGET_VALIDATION_SCHEMA_SHA256
        or registry.get("registry_digest") != RECIPE_REGISTRY_DIGEST
    ):
        raise RetirementMigrationError("retirement_proof_artifact_identity_mismatch")


def _load_bound_schema(path: Path, *, raw_digest: str, normalized_digest: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetirementMigrationError("retirement_schema_artifact_identity_mismatch") from exc
    if not isinstance(value, dict) or hashlib.sha256(raw).hexdigest() != raw_digest:
        raise RetirementMigrationError("retirement_schema_artifact_identity_mismatch")
    normalized = _normalize_schema(value)
    if hashlib.sha256(_canonical_json(normalized)).hexdigest() != normalized_digest:
        raise RetirementMigrationError("retirement_schema_artifact_identity_mismatch")
    Draft202012Validator.check_schema(normalized)
    return normalized


def _normalize_schema(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized = {key: _normalize_schema(item) for key, item in value.items()}
    if normalized.get("type") == "array" and "enum" in normalized:
        items = normalized.get("items")
        if isinstance(items, dict) and "enum" not in items:
            normalized["items"] = dict(items)
            normalized["items"]["enum"] = normalized.pop("enum")
    return normalized


def _load_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetirementMigrationError(code) from exc
    if not isinstance(value, dict):
        raise RetirementMigrationError(code)
    return value


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(value))).hexdigest()


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RetirementMigrationError("retirement_manifest_identity_mismatch") from exc


def _print_progress(event: Mapping[str, object]) -> None:
    ordered = " ".join(f"{key}={event[key]}" for key in sorted(event))
    print(f"[retired-esr] {ordered}", flush=True)


__all__ = [
    "DEFAULT_CANDIDATE_CATALOG_RELATIVE_PATH",
    "DEFAULT_PROOF_RELATIVE_PATH",
    "FROZEN_TOTAL_REPORT",
    "MaterializedRetirementRevision",
    "TOTAL_PROOF_ARTIFACT_DIGEST",
    "backup_evidence_from_mapping",
    "execute_materialized_revision",
    "materialize_exact_esr140_retirement_revision",
    "reject_retirement_downgrade",
]
