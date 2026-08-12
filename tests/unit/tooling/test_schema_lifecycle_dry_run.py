from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from tools.schema_lifecycle_dry_run import (
    DatabaseSelection,
    SchemaLifecycleDryRunError,
    _text_report,
    run_dry_run,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
PROOF = (
    REPO_ROOT
    / "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)


def _candidate_catalog(tmp_path: Path) -> Path:
    candidate = json.loads(CATALOG.read_text(encoding="utf-8"))
    for row in candidate["channels"]:
        if row["line_id"] == "esr-140":
            row["support"]["state"] = "retired"
            row["selectable"] = False
        if row["line_id"] == "esr-115":
            row["retirement_successor_line_id"] = "esr-153"
    path = tmp_path / "candidate-catalog.json"
    path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    return path


def test_default_run_never_constructs_database_engine_and_is_deterministic() -> None:
    messages: list[str] = []
    with patch("tools.schema_lifecycle_dry_run.sa.create_engine") as create_engine:
        first = run_dry_run(
            previous_catalog_path=CATALOG,
            candidate_catalog_path=CATALOG,
            emit=messages.append,
        )
        second = run_dry_run(
            previous_catalog_path=CATALOG,
            candidate_catalog_path=CATALOG,
            emit=lambda _message: None,
        )

    assert create_engine.call_count == 0
    assert first == second
    assert first["status"] == "complete"
    assert first["mutation"] == "none"
    assert first["database"] == {
        "status": "not-requested",
        "affected_profiles": [],
        "backup": {"status": "not-required-no-retirement"},
    }
    assert messages[-1] == "phase=complete channel=matrix [5/5] status=complete"
    assert _text_report(first) == _text_report(second)
    assert json.dumps(first, ensure_ascii=True, sort_keys=True) == json.dumps(
        second, ensure_ascii=True, sort_keys=True
    )


def test_current_supported_catalog_reports_no_retirement_activation() -> None:
    report = run_dry_run(
        previous_catalog_path=CATALOG, candidate_catalog_path=CATALOG, emit=lambda _: None
    )

    assert report["retirement_proof"] == {"status": "not-required", "checked_mappings": []}
    assert report["candidate_materializer"] == {"status": "not-applicable-no-retirement"}
    assert report["blockers"] == []


def test_candidate_esr140_to_esr153_reports_complete_proof_and_candidate_materializer(
    tmp_path: Path,
) -> None:
    report = run_dry_run(
        previous_catalog_path=CATALOG,
        candidate_catalog_path=_candidate_catalog(tmp_path),
        proof_path=PROOF,
        emit=lambda _: None,
    )

    assert report["status"] == "complete"
    assert report["retirement_proof"]["status"] == "complete"
    assert report["candidate_materializer"]["status"] == "candidate-only-ready"
    assert report["database"]["backup"] == {
        "status": "not-checked",
        "execution_preflight": "required-before-activation",
    }
    assert report["candidate_materializer"]["revision"] == "20260812_retire_esr140_13_to_esr153_0"
    assert report["plan"]["retirement_successor_mappings"] == [
        {
            "source": {
                "line_id": "esr-140",
                "artifact_id": "esr-140.13",
                "channel_id": "esr-140.13",
                "family": "esr",
                "line_number": 140,
                "artifact_version": "140.13",
                "support_state": "retired",
                "selectable": False,
            },
            "target": {
                "line_id": "esr-153",
                "artifact_id": "esr-153.0",
                "channel_id": "esr-153.0",
                "family": "esr",
                "line_number": 153,
                "artifact_version": "153.0",
                "support_state": "supported",
                "selectable": True,
            },
            "declared_successor_line_id": "esr-153",
        }
    ]


@pytest.mark.parametrize("proof_kind", ("missing", "stale"))
def test_candidate_rejects_missing_or_stale_total_proof(tmp_path: Path, proof_kind: str) -> None:
    proof_path = None
    if proof_kind == "stale":
        stale = copy.deepcopy(json.loads(PROOF.read_text(encoding="utf-8")))
        stale["target"]["artifact_id"] = "esr-153.1"
        proof_path = tmp_path / "stale-proof.json"
        proof_path.write_text(json.dumps(stale), encoding="utf-8")

    report = run_dry_run(
        previous_catalog_path=CATALOG,
        candidate_catalog_path=_candidate_catalog(tmp_path),
        proof_path=proof_path,
        emit=lambda _: None,
    )

    assert report["status"] == "blocked"
    assert report["retirement_proof"]["status"] == proof_kind
    assert report["candidate_materializer"]["status"] == "blocked-proof-not-ready"
    assert report["blockers"] == ["retirement_total_convertibility_unproven"]


@pytest.mark.parametrize(
    "selection, code",
    [
        (
            DatabaseSelection("sqlite:////tmp/disposable.db", "disposable", None),
            "retirement_database_sqlite_not_readonly",
        ),
        (
            DatabaseSelection("mysql://unsafe.invalid/bpm", "disposable", None),
            "retirement_database_url_unsafe",
        ),
        (
            DatabaseSelection("sqlite:///file:/tmp/disposable.db?mode=ro&uri=true", "unsafe", None),
            "retirement_database_scope_unsafe",
        ),
        (
            DatabaseSelection(
                "sqlite:///file:/tmp/verified.db?mode=ro&uri=true", "verified-backup", None
            ),
            "retirement_backup_evidence_missing",
        ),
    ],
)
def test_unsafe_database_selection_is_rejected_before_database_access(
    selection: DatabaseSelection, code: str
) -> None:
    with patch("tools.schema_lifecycle_dry_run.sa.create_engine") as create_engine:
        with pytest.raises(SchemaLifecycleDryRunError, match=code):
            run_dry_run(
                previous_catalog_path=CATALOG,
                candidate_catalog_path=CATALOG,
                database=selection,
                emit=lambda _: None,
            )
    assert create_engine.call_count == 0


def test_explicit_disposable_database_count_executes_selects_only_and_hides_url(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "disposable.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE profiles (schema_version TEXT NOT NULL)")
        connection.execute("INSERT INTO profiles (schema_version) VALUES ('esr-153.0')")

    observed: list[str] = []
    original_create_engine = sa.create_engine

    def recording_create_engine(*args, **kwargs):
        engine = original_create_engine(*args, **kwargs)
        sa.event.listen(engine, "before_cursor_execute", lambda *event: observed.append(event[2]))
        return engine

    selection = DatabaseSelection(
        f"sqlite:///file:{database_path}?mode=ro&uri=true",
        "disposable",
        None,
    )
    with patch("tools.schema_lifecycle_dry_run.sa.create_engine", recording_create_engine):
        report = run_dry_run(
            previous_catalog_path=CATALOG,
            candidate_catalog_path=CATALOG,
            database=selection,
            emit=lambda _: None,
        )

    assert report["database"] == {
        "status": "complete-read-only",
        "scope": "disposable",
        "engine": "sqlite",
        "profile_count": 1,
        "affected_profiles": [],
        "backup": {
            "status": "not-required-disposable",
            "execution_preflight": "required-before-activation",
        },
    }
    assert observed and all(
        statement.lstrip().upper().startswith("SELECT") for statement in observed
    )
    assert str(database_path) not in json.dumps(report, sort_keys=True)
