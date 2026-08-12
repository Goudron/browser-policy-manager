from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlparse

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.engine import make_url

from alembic import command
from migration_support.retirement_owner_v1 import RetirementMigrationError
from migration_support.retirement_revision_materializer_v1 import (
    TOTAL_PROOF_ARTIFACT_DIGEST,
    materialize_exact_esr140_retirement_revision,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
PROOF = (
    REPO_ROOT
    / "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)
SOURCE_REVISION = "20260804_add_profile_name_casefold"
TARGET_REVISION = "20260812_retire_esr140_13_to_esr153_0"
_TEMPORARY_POSTGRES_DATABASE = re.compile(r"^bpm_m4_05(?:_[a-z0-9]+)*$")


@dataclass(frozen=True)
class _CandidateDatabaseTarget:
    """A disposable engine for the temporary candidate Alembic graph only."""

    name: str
    url: str
    database_name: str | None = None
    admin_url: str | None = None

    def create(self) -> None:
        if self.name == "sqlite":
            self.reset()
            return

        self._drop_postgres_database()
        assert self.admin_url is not None
        assert self.database_name is not None
        engine = sa.create_engine(self.admin_url, isolation_level="AUTOCOMMIT", future=True)
        try:
            with engine.connect() as connection:
                connection.execute(sa.text(f'CREATE DATABASE "{self.database_name}"'))
        finally:
            engine.dispose()

    def reset(self) -> None:
        if self.name == "sqlite":
            Path(self.url.removeprefix("sqlite:///")).unlink(missing_ok=True)
            return

        database_name = urlparse(self.url).path.removeprefix("/")
        if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
            raise RuntimeError(
                "Refusing to reset PostgreSQL database outside the disposable M4-05 "
                f"naming contract: {database_name!r}"
            )
        engine = sa.create_engine(self.url, isolation_level="AUTOCOMMIT", future=True)
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
        engine = sa.create_engine(self.admin_url, isolation_level="AUTOCOMMIT", future=True)
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


def _postgres_candidate_target() -> _CandidateDatabaseTarget | None:
    async_url = os.environ.get("BPM_POSTGRES_TEST_URL")
    if not async_url:
        if os.environ.get("BPM_REQUIRE_POSTGRES") == "1":
            pytest.fail(
                "BPM_REQUIRE_POSTGRES=1 requires BPM_POSTGRES_TEST_URL for the real "
                "PostgreSQL candidate-retirement graph"
            )
        return None
    if not async_url.startswith("postgresql+") or "+asyncpg" not in async_url:
        pytest.fail("BPM_POSTGRES_TEST_URL must use the real postgresql+asyncpg driver")
    base = make_url(async_url)
    database_name = base.database or ""
    if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
        pytest.fail(
            "BPM_POSTGRES_TEST_URL must target only a disposable bpm_m4_05* database, "
            f"got {database_name!r}"
        )
    candidate_database = f"{database_name}_candidate"
    return _CandidateDatabaseTarget(
        name="postgresql",
        url=base.set(drivername="postgresql+psycopg", database=candidate_database).render_as_string(
            hide_password=False
        ),
        database_name=candidate_database,
        admin_url=base.set(drivername="postgresql+psycopg", database="postgres").render_as_string(
            hide_password=False
        ),
    )


@pytest.fixture(params=("sqlite", "postgresql"), ids=("sqlite", "postgresql"))
def candidate_database_target(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> _CandidateDatabaseTarget:
    if request.param == "sqlite":
        target = _CandidateDatabaseTarget(
            name="sqlite", url=f"sqlite:///{tmp_path / 'candidate.sqlite'}"
        )
    else:
        target = _postgres_candidate_target()
        if target is None:
            pytest.skip("set BPM_POSTGRES_TEST_URL to run the real PostgreSQL candidate graph")
    target.create()
    try:
        yield target
    finally:
        target.cleanup()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_catalog(tmp_path: Path) -> Path:
    candidate = copy.deepcopy(_load_json(CATALOG))
    candidate["status"] = "candidate-retire-esr140-not-active"
    for row in candidate["channels"]:
        if row["line_id"] == "esr-140":
            row["support"] = {
                **row["support"],
                "state": "retired",
                "end": {"kind": "date", "value": "2026-09-01"},
            }
            row["selectable"] = False
            row["roles"] = {
                "latest_esr": False,
                "product_default": False,
                "default_release": False,
            }
        if row["line_id"] == "esr-115":
            row["retirement_successor_line_id"] = "esr-153"
    output = tmp_path / "candidate-catalog.json"
    output.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    return output


def _materialize(tmp_path: Path):
    return materialize_exact_esr140_retirement_revision(
        previous_catalog_path=CATALOG,
        candidate_catalog_path=_candidate_catalog(tmp_path),
        proof_path=PROOF,
        source_revision=SOURCE_REVISION,
        target_revision=TARGET_REVISION,
    )


def _config(url: str, *, script_location: Path | None = None) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(script_location or REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def _native_sqlite_backup(source: Path, backup: Path, restore: Path) -> tuple[str, str]:
    with sqlite3.connect(source) as source_connection, sqlite3.connect(backup) as backup_connection:
        source_connection.backup(backup_connection)
    shutil.copyfile(backup, restore)
    with sqlite3.connect(restore) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("SELECT COUNT(*) FROM profiles").fetchone() == (4,)
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            SOURCE_REVISION,
        )
    return (
        hashlib.sha256(backup.read_bytes()).hexdigest(),
        hashlib.sha256(restore.read_bytes()).hexdigest(),
    )


def _load_revision(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("candidate_retirement_revision", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_supported_catalog_cannot_materialize_retirement_revision(tmp_path: Path) -> None:
    with pytest.raises(RetirementMigrationError, match="retirement_catalog_not_retired"):
        materialize_exact_esr140_retirement_revision(
            previous_catalog_path=CATALOG,
            candidate_catalog_path=CATALOG,
            proof_path=PROOF,
            source_revision=SOURCE_REVISION,
            target_revision=TARGET_REVISION,
        )
    assert list(tmp_path.iterdir()) == []


def test_candidate_materialization_binds_exact_catalog_proof_manifest_and_graph(
    tmp_path: Path,
) -> None:
    artifact = _materialize(tmp_path)

    assert artifact.revision == TARGET_REVISION
    assert artifact.down_revision == SOURCE_REVISION
    assert artifact.manifest["total_proof_artifact_digest"] == TOTAL_PROOF_ARTIFACT_DIGEST
    assert artifact.manifest["candidate_catalog_digest"] == artifact.candidate_catalog_digest
    assert artifact.manifest["candidate_supported_esr_lines"] == [
        {"line_id": "esr-115", "line_number": 115, "artifact_id": "esr-115.38"},
        {"line_id": "esr-153", "line_number": 153, "artifact_id": "esr-153.0"},
    ]
    assert hashlib.sha256(artifact.source.encode()).hexdigest() == artifact.source_sha256
    compile(artifact.source, "candidate-retirement-revision.py", "exec")
    assert "from app" not in artifact.source
    assert "retirement_backup_evidence" in artifact.source
    assert "reject_retirement_downgrade" in artifact.source


@pytest.mark.parametrize("stale_input", ["proof", "candidate"])
def test_stale_static_input_fails_before_revision_output(tmp_path: Path, stale_input: str) -> None:
    candidate = _candidate_catalog(tmp_path)
    proof = PROOF
    if stale_input == "proof":
        value = _load_json(PROOF)
        value["proof_artifact_digest"] = "0" * 64
        proof = tmp_path / "stale-proof.json"
        proof.write_text(json.dumps(value), encoding="utf-8")
    else:
        value = _load_json(candidate)
        source = next(row for row in value["channels"] if row["line_id"] == "esr-140")
        source["artifact_id"] = "esr-140.12"
        candidate.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(RetirementMigrationError):
        materialize_exact_esr140_retirement_revision(
            previous_catalog_path=CATALOG,
            candidate_catalog_path=candidate,
            proof_path=proof,
            source_revision=SOURCE_REVISION,
            target_revision=TARGET_REVISION,
        )


def test_materialized_candidate_runs_real_alembic_upgrade_atomically(
    tmp_path: Path,
    candidate_database_target: _CandidateDatabaseTarget,
) -> None:
    artifact = _materialize(tmp_path)
    candidate_database_target.reset()
    url = candidate_database_target.url
    command.upgrade(_config(url), SOURCE_REVISION)
    created = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    updated = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    archived = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    engine = sa.create_engine(url, future=True)
    metadata = sa.MetaData()
    profiles = sa.Table("profiles", metadata, autoload_with=engine)
    rows = [
        {
            "id": 1,
            "name": "active-source",
            "name_casefold": "active-source",
            "description": "preserved active",
            "schema_version": "esr-140.13",
            "flags": {"DisableTelemetry": True},
            "compliance": None,
            "revision": 4,
            "created_at": created,
            "updated_at": updated,
            "deleted_at": None,
        },
        {
            "id": 2,
            "name": "archived-source",
            "name_casefold": "archived-source",
            "description": "preserved archived",
            "schema_version": "esr-140.13",
            "flags": {},
            "compliance": {"status": "current", "claim": "must-not-stay-current"},
            "revision": 8,
            "created_at": created,
            "updated_at": updated,
            "deleted_at": archived,
        },
        {
            "id": 3,
            "name": "target",
            "name_casefold": "target",
            "description": None,
            "schema_version": "esr-153.0",
            "flags": {"DisableTelemetry": False},
            "compliance": None,
            "revision": 2,
            "created_at": created,
            "updated_at": updated,
            "deleted_at": None,
        },
        {
            "id": 4,
            "name": "release",
            "name_casefold": "release",
            "description": None,
            "schema_version": "release-153",
            "flags": {},
            "compliance": None,
            "revision": 3,
            "created_at": created,
            "updated_at": updated,
            "deleted_at": None,
        },
    ]
    with engine.begin() as connection:
        connection.execute(profiles.insert(), rows)
    with engine.connect() as connection:
        before = {
            row["id"]: dict(row)
            for row in connection.execute(sa.select(profiles).order_by(profiles.c.id)).mappings()
        }
    engine.dispose()

    if candidate_database_target.name == "sqlite":
        database = Path(url.removeprefix("sqlite:///"))
        backup_path = tmp_path / "candidate.backup.sqlite"
        restore_path = tmp_path / "candidate.restore.sqlite"
        backup_sha256, restore_digest = _native_sqlite_backup(database, backup_path, restore_path)
    else:
        # The real PostgreSQL native backup/restore check is owned by
        # test_database_recovery.py.  This temporary-graph test proves that a
        # separately verified, opaque backup attestation unblocks the exact
        # candidate revision on the PostgreSQL transaction engine.
        backup_sha256 = hashlib.sha256(b"bpm-m6-r3-postgresql-candidate-native-backup").hexdigest()
        restore_digest = hashlib.sha256(
            b"bpm-m6-r3-postgresql-candidate-native-restore"
        ).hexdigest()
    candidate = _candidate_catalog(tmp_path)
    candidate_scripts = tmp_path / "candidate-alembic"
    shutil.copytree(REPO_ROOT / "alembic", candidate_scripts)
    revision_path = candidate_scripts / "versions" / f"{TARGET_REVISION}.py"
    revision_path.write_text(artifact.source, encoding="utf-8")

    config = _config(url, script_location=candidate_scripts)
    config.attributes.update(
        {
            "retirement_repository_root": REPO_ROOT,
            "retirement_candidate_catalog_path": candidate,
            "retirement_proof_path": PROOF,
            "retirement_no_active_writers": True,
            "retirement_backup_evidence": {
                "engine": candidate_database_target.name,
                "backup_sha256": backup_sha256,
                "restore_identity_digest": restore_digest,
                "source_stamp": SOURCE_REVISION,
                "restored_stamp": SOURCE_REVISION,
                "source_profile_count": 4,
                "restored_profile_count": 4,
                "status": "verified-native-restore",
                "integrity": "pass",
            },
        }
    )
    command.upgrade(config, TARGET_REVISION)

    engine = sa.create_engine(url, future=True)
    try:
        with engine.connect() as connection:
            after = {
                row["id"]: dict(row)
                for row in connection.execute(
                    sa.select(profiles).order_by(profiles.c.id)
                ).mappings()
            }
            stamp = connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert stamp == TARGET_REVISION
        assert after[1]["schema_version"] == after[2]["schema_version"] == "esr-153.0"
        assert after[1]["flags"] == rows[0]["flags"]
        assert after[2]["flags"] == rows[1]["flags"]
        assert after[1]["revision"] == 5
        assert after[2]["revision"] == 9
        assert after[1]["updated_at"] == after[2]["updated_at"]
        assert after[1]["updated_at"] != updated
        assert after[2]["deleted_at"] == before[2]["deleted_at"]
        assert after[2]["compliance"] == {
            "schema_version": 1,
            "status": "invalidated",
            "reason_code": "compliance_target_proof_unavailable",
            "source_artifact_id": "esr-140.13",
            "target_artifact_id": "esr-153.0",
            "source_compliance_digest": after[2]["compliance"]["source_compliance_digest"],
            "current_claims": False,
            "preserved_source": rows[1]["compliance"],
        }
        for profile_id in (3, 4):
            assert after[profile_id] == before[profile_id]

        module = _load_revision(revision_path)
        with pytest.raises(RetirementMigrationError, match="retirement_downgrade_unsupported"):
            module.downgrade()
    finally:
        engine.dispose()
