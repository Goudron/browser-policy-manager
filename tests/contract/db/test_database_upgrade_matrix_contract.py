from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import Settings
from app.core.policy_validation import validate_profile_policies_for_channel
from app.core.profile_baseline_provenance import legacy_migration_baseline_provenance
from app.core.profile_certificate_provenance import imported_certificate_provenance
from app.core.profile_extension_provenance import imported_extension_provenance
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNEL_SET

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO_ROOT / "docs" / "architecture" / "database-upgrade-matrix-0.9.5.json"
RUNBOOK_PATH = REPO_ROOT / "docs" / "architecture" / "database-upgrade-matrix-0.9.5.md"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "database_upgrade" / "golden_profiles_0_9_5.json"
ALEMBIC_ENV_PATH = REPO_ROOT / "alembic" / "env.py"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_revision_order() -> list[str]:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    scripts = ScriptDirectory.from_config(config)
    assert len(scripts.get_heads()) == 1
    return [revision.revision for revision in reversed(list(scripts.walk_revisions()))]


def _literal_assignment(path: Path, name: str) -> Any:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                return ast.literal_eval(node.value)
    raise AssertionError(f"Missing literal assignment {name} in {path}")


def _sqlite_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _materialize_source_shape(
    shape: dict[str, Any],
    cases: list[dict[str, Any]],
) -> None:
    table = shape["table"]
    if table is None:
        assert not cases
        return

    source_rows = [dict(case["source"]) for case in cases]
    if "name_casefold" in shape["required_columns"]:
        for row in source_rows:
            row.setdefault("name_casefold", str(row["name"]).casefold())
    if "baseline_provenance" in shape["required_columns"]:
        for row in source_rows:
            # Existing head-idempotent fixture rows model old persisted data.
            # The M3 revision's explicit all-row default is their only
            # admissible baseline when a current-head source is materialized.
            row.setdefault("baseline_provenance", legacy_migration_baseline_provenance())
    if "extension_provenance" in shape["required_columns"]:
        for row in source_rows:
            # M7-07 explicitly classifies every pre-attribution extension
            # value as imported; it never reconstructs its source from flags.
            row.setdefault("extension_provenance", imported_extension_provenance(row["flags"]))
    if "certificate_provenance" in shape["required_columns"]:
        for row in source_rows:
            # M9-04 treats historical certificate-related values as imported
            # and deliberately leaves their M3 benchmark envelope untouched.
            row.setdefault("certificate_provenance", imported_certificate_provenance(row["flags"]))
    columns = list(shape["required_columns"])
    columns.extend(
        column
        for column in shape.get("optional_columns", [])
        if any(column in row for row in source_rows)
    )
    allowed_columns = set(shape["required_columns"]) | set(shape.get("optional_columns", []))
    for row in source_rows:
        assert set(row) <= allowed_columns
        assert set(shape["required_columns"]) <= set(row)

    type_by_column = {
        "id": "INTEGER PRIMARY KEY",
        "revision": "INTEGER NOT NULL",
        "flags": "TEXT NOT NULL",
        "compliance": "TEXT",
    }
    column_ddl = ", ".join(f'"{column}" {type_by_column.get(column, "TEXT")}' for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(f'"{column}"' for column in columns)

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(f'CREATE TABLE "{table}" ({column_ddl})')
        for row in source_rows:
            connection.execute(
                f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
                [_sqlite_value(row.get(column)) for column in columns],
            )
        stored_count = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
        assert stored_count == (len(source_rows),)
    finally:
        connection.close()


def test_upgrade_matrix_matches_the_complete_alembic_graph_and_aliases():
    matrix = _load_json(MATRIX_PATH)
    canonical_revisions = _canonical_revision_order()
    actual_aliases = _literal_assignment(ALEMBIC_ENV_PATH, "LEGACY_REVISION_ALIASES")
    sources = matrix["supported_sources"]

    assert matrix["contract_version"] == 2
    assert matrix["product_version"] == Settings().APP_VERSION
    assert matrix["supported_engines"] == ["sqlite", "postgresql"]
    assert matrix["observed_head_revision"] == canonical_revisions[-1]
    assert matrix["retained_window"]["first_canonical_revision"] == canonical_revisions[0]
    assert matrix["retained_window"]["last_source_revision"] == canonical_revisions[-1]
    assert matrix["legacy_revision_aliases"] == actual_aliases

    source_ids = [source["id"] for source in sources]
    assert len(source_ids) == len(set(source_ids))
    assert [source["stamp"] for source in sources if source["kind"] == "canonical_revision"] == (
        canonical_revisions
    )
    assert {
        source["stamp"]: source["canonical_revision"]
        for source in sources
        if source["kind"] == "legacy_alias"
    } == actual_aliases
    assert [source["id"] for source in sources if source["kind"] == "fresh_install"] == [
        "fresh-empty"
    ]

    for source in sources:
        assert source["shape"] in matrix["schema_shapes"]
        assert source["applicability"] == {
            "sqlite": "required",
            "postgresql": "required",
        }


def test_upgrade_matrix_declares_fail_closed_preflight_and_owned_evidence_gaps():
    matrix = _load_json(MATRIX_PATH)
    stop_conditions = set(matrix["preflight_stop_condition_ids"])
    gap_by_id = {gap["id"]: gap for gap in matrix["known_evidence_gaps"]}

    assert {
        "unstamped-nonempty",
        "unknown-or-multiple-stamp",
        "mixed-profile-tables",
        "shape-does-not-match-stamp",
        "backup-not-restorable",
        "partial-or-failed-prior-upgrade",
    } <= stop_conditions
    assert gap_by_id == {}
    recovery = matrix["recovery_evidence"]
    assert recovery["engines"] == ["sqlite", "postgresql"]
    assert recovery["tests"] == "tests/integration/db/test_database_recovery.py"
    assert recovery["ci_gate"] == "make test-postgres-integration"
    assert "explicit maintainer action" in recovery["promotion_boundary"]
    assert "unsupported" in recovery["downgrade_policy"]

    candidate = matrix["candidate_only_retirement"]
    assert candidate == {
        "transition": "esr-140.13-to-esr-153.0",
        "status": "blocked-current-catalog-still-supported",
        "materializer": "migration_support/retirement_revision_materializer_v1.py",
        "active_graph_changed": False,
        "observed_head_revision": matrix["observed_head_revision"],
        "immutable_proof_digest": (
            "9de84bde21e11d161d48297d19cc2447c36ac052d6cef8aed7727b8fa29746ef"
        ),
        "sqlite_evidence": "candidate-artifact-real-alembic-upgrade-pass",
        "postgresql_evidence": "pending-m6-remediation-r3",
        "activation_conditions": [
            "ESR 140.13 is retired in the reviewed candidate lifecycle catalog",
            "the materialized manifest binds the exact previous and candidate catalog digests",
            "the generated revision is deliberately installed and the active graph/matrix owners are updated together",
            "native backup restore evidence and no-active-writer attestation are supplied to Alembic",
            "the real PostgreSQL candidate matrix passes before release promotion",
        ],
    }

    unsupported_ids = {source["id"] for source in matrix["unsupported_sources"]}
    assert {
        "unstamped-nonempty",
        "unknown-or-multiple-stamp",
        "mixed-profile-tables",
        "shape-does-not-match-stamp",
    } == unsupported_ids


def test_golden_scenarios_cover_every_source_and_materialize_in_memory():
    matrix = _load_json(MATRIX_PATH)
    fixture = _load_json(FIXTURE_PATH)
    sources = {source["id"]: source for source in matrix["supported_sources"]}
    scenarios = {scenario["id"]: scenario for scenario in fixture["scenarios"]}

    assert fixture["matrix"] == MATRIX_PATH.relative_to(REPO_ROOT).as_posix()
    # This retained fixture records pre-M3 source values and their historical
    # field-preservation expectations.  The M3 envelope is synthesized for
    # every old row rather than copied from a source value and is proven by the
    # real migration suites below.
    assert set(fixture["head_profile_fields"]) == (
        set(matrix["target_head_invariants"]["profile_columns"])
        - {"name_casefold", "baseline_provenance", "extension_provenance", "certificate_provenance"}
    )
    assert len(scenarios) == len(fixture["scenarios"])

    covered_source_ids: set[str] = set()
    all_case_ids: set[str] = set()
    all_dimensions: set[str] = set()
    for scenario in scenarios.values():
        assert scenario["source_ids"]
        for source_id in scenario["source_ids"]:
            assert source_id in sources
            assert sources[source_id]["fixture_scenario"] == scenario["id"]
            covered_source_ids.add(source_id)
            _materialize_source_shape(
                matrix["schema_shapes"][sources[source_id]["shape"]],
                scenario["cases"],
            )
        for case in scenario["cases"]:
            assert case["id"] not in all_case_ids
            all_case_ids.add(case["id"])
            all_dimensions.update(case["dimensions"])

    assert covered_source_ids == set(sources)
    assert set(fixture["required_dimensions"]) <= all_dimensions


def test_golden_expected_rows_preserve_data_defaults_and_policy_validity():
    matrix = _load_json(MATRIX_PATH)
    fixture = _load_json(FIXTURE_PATH)
    expected_fields = set(matrix["target_head_invariants"]["profile_columns"]) - {
        "name_casefold",
        "baseline_provenance",
        "extension_provenance",
        "certificate_provenance",
    }
    immutable_fields = {
        "id",
        "name",
        "description",
        "flags",
        "created_at",
        "updated_at",
    }

    for scenario in fixture["scenarios"]:
        for case in scenario["cases"]:
            source = case["source"]
            expected = case["expected_head"]

            assert set(expected) == expected_fields
            assert "owner" not in expected
            for field in immutable_fields:
                assert expected[field] == source[field]
            assert expected["compliance"] == source.get("compliance")
            assert expected["revision"] == source.get("revision", 1)
            assert expected["deleted_at"] == source.get("deleted_at")

            source_channel = source["schema_version"]
            expected_channel = expected["schema_version"]
            disposition = case["channel_disposition"]
            if disposition == "migrate-same-family":
                assert source_channel != expected_channel
                assert source_channel.split("-", 1)[0] == expected_channel.split("-", 1)[0]
            elif disposition in {"preserve-supported", "preserve-quarantined"}:
                assert source_channel == expected_channel
            else:  # pragma: no cover - protects fixture vocabulary
                raise AssertionError(f"Unknown channel disposition: {disposition}")

            validity = case["policy_validity"]
            if expected_channel in SUPPORTED_SCHEMA_CHANNEL_SET:
                issues = validate_profile_policies_for_channel(expected["flags"], expected_channel)
                assert (not issues) if validity == "valid" else (validity == "invalid" and issues)
            else:
                assert validity == "uncheckable"
                assert disposition == "preserve-quarantined"


def test_runbook_defines_backup_restore_and_failure_boundaries():
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    for heading in (
        "## Supported source matrix",
        "## Pre-upgrade invariants",
        "## Post-upgrade invariants",
        "## Stop conditions",
        "## SQLite backup and recovery procedure",
        "## PostgreSQL backup and recovery procedure",
        "## Golden fixture semantics",
        "## Interruption and recovery evidence",
    ):
        assert heading in runbook
    assert 'sqlite3 <source.db> ".backup' in runbook
    assert "pg_dump --format=custom --serializable-deferrable" in runbook
    assert "pg_restore --exit-on-error --single-transaction" in runbook
    assert "never treat an Alembic downgrade as recovery" in runbook
    assert "never target\n`data/bpm.db` in tests" in runbook
    assert "tools/database_upgrade_recovery.py verify-sqlite-backup" in runbook
    assert "tools/database_upgrade_recovery.py retry-sqlite-upgrade" in runbook
    assert "make test-postgres-integration" in runbook
