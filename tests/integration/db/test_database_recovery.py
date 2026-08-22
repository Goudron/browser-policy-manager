from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

import app.core.schema_channels as schema_channels
from alembic import command
from app.core.profile_baseline_provenance import (
    generic_create_baseline_provenance,
    legacy_migration_baseline_provenance,
)
from app.core.profile_certificate_provenance import (
    empty_certificate_provenance,
    imported_certificate_provenance,
)
from app.core.profile_extension_provenance import (
    empty_extension_provenance,
    imported_extension_provenance,
)
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG
from app.db import EXPECTED_DATABASE_REVISION, DatabaseReadinessError, DatabaseRuntime
from app.main import create_app
from tools.database_upgrade_recovery import (
    RecoveryBoundaryError,
    retry_sqlite_upgrade,
    verify_sqlite_backup,
)

PRE_M4_HEAD = "20260721_upgrade_profiles_to_firefox153_dual_esr"


def _historical_m3_legacy_baseline_provenance() -> dict[str, object]:
    result = legacy_migration_baseline_provenance()
    result["starter"].pop("preset_id")
    return result


def _config(path: Path) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return config


def _prepare_retained_source(path: Path) -> None:
    command.upgrade(_config(path), PRE_M4_HEAD)
    engine = create_engine(f"sqlite:///{path}", future=True)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO profiles (name, description, schema_version, flags) "
                    "VALUES ('m4-06-retained', 'recovery proof', 'release-152', :flags)"
                ),
                {"flags": json.dumps({"Proxy": {"Mode": "none"}}, sort_keys=True)},
            )
    finally:
        engine.dispose()


def _native_sqlite_backup(source: Path, backup: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    backup_connection = sqlite3.connect(backup)
    try:
        source_connection.backup(backup_connection)
    finally:
        backup_connection.close()
        source_connection.close()
    backup.chmod(0o444)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _profile_snapshot(path: Path) -> tuple[tuple[object, ...], str]:
    engine = create_engine(f"sqlite:///{path}", future=True)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT name, name_casefold, description, schema_version, flags, compliance, "
                    "baseline_provenance, extension_provenance, certificate_provenance, "
                    "revision, created_at, updated_at, deleted_at FROM profiles "
                    "ORDER BY id"
                )
            ).one()
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            return row, revision
    finally:
        engine.dispose()


def _insert_head_profile(path: Path, *, schema_version: str) -> None:
    engine = create_engine(f"sqlite:///{path}", future=True)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO profiles (name, name_casefold, description, schema_version, flags, "
                    "compliance, baseline_provenance, extension_provenance, certificate_provenance, revision) VALUES "
                    "(:name, :name_casefold, :description, :schema_version, :flags, :compliance, "
                    ":baseline_provenance, :extension_provenance, :certificate_provenance, :revision)"
                ),
                {
                    "name": "m6-readiness-profile",
                    "name_casefold": "m6-readiness-profile",
                    "description": "M6 runtime ownership fixture",
                    "schema_version": schema_version,
                    "flags": "{}",
                    "compliance": None,
                    "baseline_provenance": json.dumps(generic_create_baseline_provenance()),
                    "extension_provenance": json.dumps(empty_extension_provenance()),
                    "certificate_provenance": json.dumps(empty_certificate_provenance()),
                    "revision": 7,
                },
            )
    finally:
        engine.dispose()


async def _assert_app_refuses(path: Path, match: str) -> None:
    runtime = DatabaseRuntime(database_url=f"sqlite+aiosqlite:///{path}", echo=False)
    app = create_app(database_runtime=runtime)
    with pytest.raises(DatabaseReadinessError, match=match):
        async with app.router.lifespan_context(app):
            raise AssertionError("incompatible database must never enter the ready lifespan")
    assert runtime.initialized is False
    assert runtime.schema_ready is False
    assert runtime.engine is None


def test_application_refuses_empty_and_head_stamped_partial_databases(tmp_path: Path):
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    asyncio.run(_assert_app_refuses(empty, "not Alembic-managed"))

    partial = tmp_path / "partial.db"
    connection = sqlite3.connect(partial)
    try:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL)")
        connection.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (EXPECTED_DATABASE_REVISION,),
        )
        connection.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.commit()
    finally:
        connection.close()
    asyncio.run(_assert_app_refuses(partial, "partial/incompatible"))


def test_startup_is_read_only_and_retired_rows_require_the_offline_alembic_upgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    path = tmp_path / "retired-channel-unupgraded.db"
    command.upgrade(_config(path), "head")
    _insert_head_profile(path, schema_version="esr-140.13")
    before = _profile_snapshot(path)

    async def verify_current_head_without_mutation() -> None:
        runtime = DatabaseRuntime(database_url=f"sqlite+aiosqlite:///{path}", echo=False)
        try:
            await runtime.init()
            await runtime.verify_release_schema()
            assert runtime.schema_ready is True
        finally:
            await runtime.dispose()

    asyncio.run(verify_current_head_without_mutation())
    assert _profile_snapshot(path) == before

    source = next(
        channel for channel in SCHEMA_CHANNEL_CATALOG if channel.artifact_id == "esr-140.13"
    )
    retired = replace(source, support_state="retired", selectable=False)
    monkeypatch.setattr(
        schema_channels,
        "SCHEMA_CHANNEL_CATALOG",
        tuple(
            retired if channel.artifact_id == retired.artifact_id else channel
            for channel in SCHEMA_CHANNEL_CATALOG
        ),
    )
    asyncio.run(_assert_app_refuses(path, "schema_channel_retired_requires_migration"))
    assert _profile_snapshot(path) == before


def test_failed_upgrade_keeps_backup_and_retry_starts_from_clean_candidate(tmp_path: Path):
    source = tmp_path / "source.db"
    backup = tmp_path / "source.verified.db"
    manifest = tmp_path / "source.verified.json"
    failed_candidate = tmp_path / "candidate-failed.db"
    retry_candidate = tmp_path / "candidate-retry.db"
    _prepare_retained_source(source)
    source_digest = _sha256(source)
    _native_sqlite_backup(source, backup)

    evidence = verify_sqlite_backup(backup, manifest)
    backup_digest = evidence["backup_sha256"]
    assert backup_digest == _sha256(backup)
    assert evidence["database_summary"]["alembic_revisions"] == [PRE_M4_HEAD]

    from tools.database_upgrade_recovery import restore_sqlite_candidate

    restore_sqlite_candidate(backup, manifest, failed_candidate)
    failure_seen: list[str] = []

    def interrupt_after_baseline_copy(
        connection,
        cursor,
        statement: str,
        parameters,
        context,
        executemany: bool,
    ) -> None:
        del cursor, parameters, context, executemany
        if (
            Path(str(connection.engine.url.database)).resolve() == failed_candidate.resolve()
            and "INSERT INTO _alembic_tmp_profiles" in statement
            and "baseline_provenance" in statement
        ):
            failure_seen.append(statement)
            raise RuntimeError("BPM096-M3-01 interruption after baseline copy boundary")

    event.listen(Engine, "before_cursor_execute", interrupt_after_baseline_copy)
    try:
        with pytest.raises(RuntimeError, match="baseline copy boundary"):
            command.upgrade(_config(failed_candidate), "head")
    finally:
        event.remove(Engine, "before_cursor_execute", interrupt_after_baseline_copy)

    assert failure_seen
    assert _sha256(source) == source_digest
    assert _sha256(backup) == backup_digest
    assert manifest.is_file()
    asyncio.run(_assert_app_refuses(failed_candidate, "revision is not"))

    retry_sqlite_upgrade(backup, manifest, retry_candidate)
    engine = create_engine(f"sqlite:///{retry_candidate}", future=True)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == EXPECTED_DATABASE_REVISION
            )
            row = connection.execute(
                text(
                    "SELECT name, schema_version, flags, baseline_provenance, "
                    "extension_provenance, certificate_provenance FROM profiles"
                )
            ).one()
            assert row == (
                "m4-06-retained",
                "release-153",
                json.dumps({"Proxy": {"Mode": "none"}}, sort_keys=True),
                json.dumps(
                    _historical_m3_legacy_baseline_provenance(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                json.dumps(imported_extension_provenance({"Proxy": {"Mode": "none"}})),
                json.dumps(imported_certificate_provenance({"Proxy": {"Mode": "none"}})),
            )
        assert "compliance" in {
            column["name"] for column in inspect(engine).get_columns("profiles")
        }
    finally:
        engine.dispose()

    async def assert_retry_ready() -> None:
        runtime = DatabaseRuntime(
            database_url=f"sqlite+aiosqlite:///{retry_candidate}",
            echo=False,
        )
        app = create_app(database_runtime=runtime)
        async with app.router.lifespan_context(app):
            assert runtime.schema_ready is True
        assert runtime.engine is None

    asyncio.run(assert_retry_ready())
    assert failed_candidate.is_file()
    assert source.is_file()
    assert backup.is_file()


def test_recovery_boundary_rejects_overwrite_and_manifest_mismatch(tmp_path: Path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    manifest = tmp_path / "backup.json"
    _prepare_retained_source(source)
    _native_sqlite_backup(source, backup)
    verify_sqlite_backup(backup, manifest)

    occupied = tmp_path / "occupied.db"
    occupied.write_text("retain", encoding="utf-8")
    with pytest.raises(RecoveryBoundaryError, match="overwrite"):
        retry_sqlite_upgrade(backup, manifest, occupied)
    assert occupied.read_text(encoding="utf-8") == "retain"

    second_backup = tmp_path / "second.db"
    _native_sqlite_backup(source, second_backup)
    with pytest.raises(RecoveryBoundaryError, match="different backup path"):
        retry_sqlite_upgrade(second_backup, manifest, tmp_path / "never-created.db")
    assert not (tmp_path / "never-created.db").exists()


def _postgres_client_command(tool: str, args: list[str], tmp_path: Path) -> None:
    image = os.environ.get("BPM_POSTGRES_CLIENT_DOCKER_IMAGE")
    executable = shutil.which(tool)
    if image:
        if shutil.which("docker") is None:
            pytest.fail(
                f"PostgreSQL recovery proof requires {tool} or BPM_POSTGRES_CLIENT_DOCKER_IMAGE"
            )
        command_line = [
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--volume",
            f"{tmp_path}:{tmp_path}",
            image,
            tool,
            *args,
        ]
    elif executable is not None:
        command_line = [executable, *args]
    else:
        pytest.fail(
            f"PostgreSQL recovery proof requires {tool} or BPM_POSTGRES_CLIENT_DOCKER_IMAGE"
        )
    subprocess.run(command_line, check=True, capture_output=True, text=True)


def _postgres_database_url(base_url: str, database: str, *, async_driver: bool) -> str:
    url = make_url(base_url).set(
        drivername="postgresql+asyncpg" if async_driver else "postgresql+psycopg",
        database=database,
    )
    return url.render_as_string(hide_password=False)


def _postgres_cli_url(url: str) -> str:
    return make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)


def _postgres_admin(base_url: str, statement: str) -> None:
    engine = create_engine(
        _postgres_database_url(base_url, "postgres", async_driver=False),
        isolation_level="AUTOCOMMIT",
        future=True,
    )
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(statement)
    finally:
        engine.dispose()


def _postgres_drop(base_url: str, database: str) -> None:
    _postgres_admin(
        base_url,
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{database}' AND pid <> pg_backend_pid()",
    )
    _postgres_admin(base_url, f'DROP DATABASE IF EXISTS "{database}"')


def _postgres_create(base_url: str, database: str) -> None:
    _postgres_drop(base_url, database)
    _postgres_admin(base_url, f'CREATE DATABASE "{database}"')


def _postgres_snapshot(
    url: str,
    *,
    include_baseline_provenance: bool = False,
    include_extension_provenance: bool = False,
    include_certificate_provenance: bool = False,
) -> tuple[str, tuple[object, ...]]:
    engine = create_engine(url, future=True)
    try:
        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            columns = "name, schema_version, flags"
            if include_baseline_provenance:
                columns += ", baseline_provenance"
            if include_extension_provenance:
                columns += ", extension_provenance"
            if include_certificate_provenance:
                columns += ", certificate_provenance"
            row = connection.execute(text(f"SELECT {columns} FROM profiles")).one()
        return str(revision), row
    finally:
        engine.dispose()


def test_postgresql_native_backup_interruption_and_clean_retry(tmp_path: Path):
    base_url = os.environ.get("BPM_POSTGRES_TEST_URL")
    if not base_url:
        if os.environ.get("BPM_REQUIRE_POSTGRES_RECOVERY") == "1":
            pytest.fail("BPM_REQUIRE_POSTGRES_RECOVERY=1 requires BPM_POSTGRES_TEST_URL")
        pytest.skip("set BPM_POSTGRES_TEST_URL for real PostgreSQL recovery proof")

    suffix = str(os.getpid())
    databases = {
        stage: f"bpm_m4_06_{stage}_{suffix}"
        for stage in ("source", "restore_check", "failed", "retry")
    }
    backup = tmp_path / "postgres-recovery.dump"
    sync_urls = {
        stage: _postgres_database_url(base_url, database, async_driver=False)
        for stage, database in databases.items()
    }
    async_urls = {
        stage: _postgres_database_url(base_url, database, async_driver=True)
        for stage, database in databases.items()
    }

    try:
        for database in databases.values():
            _postgres_create(base_url, database)
        command.upgrade(_config_url(sync_urls["source"]), PRE_M4_HEAD)
        source_engine = create_engine(sync_urls["source"], future=True)
        try:
            with source_engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO profiles (name, description, schema_version, flags) "
                        "VALUES ('m4-06-postgres', 'native recovery proof', "
                        "'release-152', CAST(:flags AS JSON))"
                    ),
                    {"flags": json.dumps({"Proxy": {"Mode": "none"}}, sort_keys=True)},
                )
        finally:
            source_engine.dispose()

        _postgres_client_command(
            "pg_dump",
            [
                "--format=custom",
                "--serializable-deferrable",
                f"--file={backup}",
                _postgres_cli_url(sync_urls["source"]),
            ],
            tmp_path,
        )
        backup.chmod(0o444)
        backup_digest = _sha256(backup)
        for stage in ("restore_check", "failed"):
            _postgres_client_command(
                "pg_restore",
                [
                    "--exit-on-error",
                    "--single-transaction",
                    "--no-owner",
                    "--no-privileges",
                    f"--dbname={_postgres_cli_url(sync_urls[stage])}",
                    str(backup),
                ],
                tmp_path,
            )
        source_snapshot = _postgres_snapshot(sync_urls["source"])
        assert _postgres_snapshot(sync_urls["restore_check"]) == source_snapshot

        failure_seen: list[str] = []

        def interrupt_postgres_upgrade(
            connection,
            cursor,
            statement: str,
            parameters,
            context,
            executemany: bool,
        ) -> None:
            del cursor, parameters, context, executemany
            if (
                connection.engine.url.database == databases["failed"]
                and "baseline_provenance" in statement
                and "DROP DEFAULT" in statement
            ):
                failure_seen.append(statement)
                raise RuntimeError("BPM096-M3-01 controlled PostgreSQL migration interruption")

        event.listen(Engine, "before_cursor_execute", interrupt_postgres_upgrade)
        try:
            with pytest.raises(RuntimeError, match="controlled PostgreSQL"):
                command.upgrade(_config_url(sync_urls["failed"]), "head")
        finally:
            event.remove(Engine, "before_cursor_execute", interrupt_postgres_upgrade)
        assert failure_seen
        assert _sha256(backup) == backup_digest
        asyncio.run(_assert_app_refuses_url(async_urls["failed"], "revision is not"))

        _postgres_client_command(
            "pg_restore",
            [
                "--exit-on-error",
                "--single-transaction",
                "--no-owner",
                "--no-privileges",
                f"--dbname={_postgres_cli_url(sync_urls['retry'])}",
                str(backup),
            ],
            tmp_path,
        )
        command.upgrade(_config_url(sync_urls["retry"]), "head")
        revision, row = _postgres_snapshot(
            sync_urls["retry"],
            include_baseline_provenance=True,
            include_extension_provenance=True,
            include_certificate_provenance=True,
        )
        assert revision == EXPECTED_DATABASE_REVISION
        assert row[0:2] == ("m4-06-postgres", "release-153")
        assert row[2] == {"Proxy": {"Mode": "none"}}
        assert row[3] == _historical_m3_legacy_baseline_provenance()
        assert row[4] == imported_extension_provenance({"Proxy": {"Mode": "none"}})
        assert row[5] == imported_certificate_provenance({"Proxy": {"Mode": "none"}})
        asyncio.run(_assert_app_accepts_url(async_urls["retry"]))
    finally:
        for database in reversed(tuple(databases.values())):
            _postgres_drop(base_url, database)


def _config_url(url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    return config


async def _assert_app_refuses_url(url: str, match: str) -> None:
    runtime = DatabaseRuntime(database_url=url, echo=False)
    app = create_app(database_runtime=runtime)
    with pytest.raises(DatabaseReadinessError, match=match):
        async with app.router.lifespan_context(app):
            raise AssertionError("failed PostgreSQL candidate must not become ready")
    assert runtime.engine is None


async def _assert_app_accepts_url(url: str) -> None:
    runtime = DatabaseRuntime(database_url=url, echo=False)
    app = create_app(database_runtime=runtime)
    async with app.router.lifespan_context(app):
        assert runtime.schema_ready is True
    assert runtime.engine is None
