from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
from alembic.config import Config
from sqlalchemy import MetaData, Table, create_engine, event, inspect, select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.core.profile_baseline_provenance import legacy_migration_baseline_provenance
from app.core.profile_certificate_provenance import imported_certificate_provenance
from app.core.profile_extension_provenance import imported_extension_provenance
from app.db import DatabaseRuntime
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate
from app.services.firefox_policy_export import render_firefox_policies_document
from app.services.profile_service import ProfileService

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO_ROOT / "docs" / "architecture" / "database-upgrade-matrix-0.9.5.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "database_upgrade" / "golden_profiles_0_9_5.json"
HEAD_REVISION = "20260821_add_profile_certificate_provenance"
_TEMPORARY_POSTGRES_DATABASE = re.compile(r"^bpm_m4_05(?:_[a-z0-9]+)*$")


def _historical_m3_legacy_baseline_provenance() -> dict[str, Any]:
    """The M3 migration predates the additive `preset_id` catalog field."""

    result = legacy_migration_baseline_provenance()
    result["starter"].pop("preset_id")
    return result


def _expected_baseline_provenance(source: dict[str, Any]) -> dict[str, Any]:
    """Respect the exact physical source shape used by the matrix fixture."""

    shape = _matrix()["schema_shapes"][source["shape"]]
    if "baseline_provenance" in shape["required_columns"]:
        return legacy_migration_baseline_provenance()
    return _historical_m3_legacy_baseline_provenance()


@dataclass(frozen=True)
class DatabaseTarget:
    name: str
    alembic_url: str
    runtime_url: str

    @property
    def sync_url(self) -> str:
        return (
            self.alembic_url.replace("+aiosqlite", "")
            .replace("+asyncpg", "+psycopg")
            .replace("postgresql://", "postgresql+psycopg://")
        )

    def reset(self) -> None:
        """Reset only the disposable target selected by this focused suite."""
        if self.name == "sqlite":
            Path(self.alembic_url.removeprefix("sqlite:///")).unlink(missing_ok=True)
            return

        database_name = urlparse(self.alembic_url).path.removeprefix("/")
        if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
            raise RuntimeError(
                "Refusing to reset PostgreSQL database outside the M4-05 disposable naming "
                f"contract: {database_name!r}"
            )
        engine = create_engine(self.sync_url, isolation_level="AUTOCOMMIT", future=True)
        try:
            with engine.connect() as connection:
                connection.execute(text("DROP SCHEMA public CASCADE"))
                connection.execute(text("CREATE SCHEMA public"))
        finally:
            engine.dispose()


def _postgres_target() -> DatabaseTarget | None:
    url = os.environ.get("BPM_POSTGRES_TEST_URL")
    if not url:
        if os.environ.get("BPM_REQUIRE_POSTGRES") == "1":
            pytest.fail(
                "BPM_REQUIRE_POSTGRES=1 requires BPM_POSTGRES_TEST_URL for the real PostgreSQL "
                "integration suite"
            )
        return None
    if "+asyncpg" not in url or not url.startswith("postgresql+"):
        pytest.fail("BPM_POSTGRES_TEST_URL must use the real postgresql+asyncpg driver")
    database_name = urlparse(url).path.removeprefix("/")
    if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
        pytest.fail(
            "BPM_POSTGRES_TEST_URL must target only a disposable bpm_m4_05* database, "
            f"got {database_name!r}"
        )
    return DatabaseTarget(name="postgresql", alembic_url=url, runtime_url=url)


@pytest.fixture(params=("sqlite", "postgresql"), ids=("sqlite", "postgresql"))
def database_target(request: pytest.FixtureRequest, tmp_path: Path) -> DatabaseTarget:
    if request.param == "sqlite":
        path = tmp_path / "m4-05.sqlite"
        return DatabaseTarget(
            name="sqlite",
            alembic_url=f"sqlite:///{path}",
            runtime_url=f"sqlite+aiosqlite:///{path}",
        )
    target = _postgres_target()
    if target is None:
        pytest.skip("set BPM_POSTGRES_TEST_URL to run the real PostgreSQL integration cases")
    return target


def _alembic_config(url: str) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def _upgrade(target: DatabaseTarget, revision: str = "head") -> None:
    command.upgrade(_alembic_config(target.alembic_url), revision)


def _matrix() -> dict[str, Any]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def _golden_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _scenario_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = {item["id"]: item for item in _golden_fixture()["scenarios"]}
    return [dict(case["source"]) for case in scenarios[source["fixture_scenario"]]["cases"]]


def _coerce_source_value(column: str, value: Any) -> Any:
    if column in {"created_at", "updated_at", "deleted_at"} and isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def _prepare_supported_source(target: DatabaseTarget, source: dict[str, Any]) -> None:
    """Create exactly one M4-01 source from fixtures, never production data."""
    target.reset()
    if source["kind"] == "fresh_install":
        return

    canonical_revision = source["canonical_revision"]
    assert isinstance(canonical_revision, str)
    _upgrade(target, canonical_revision)

    engine = create_engine(target.sync_url, future=True)
    try:
        with engine.begin() as connection:
            if source["kind"] == "legacy_alias":
                if source["shape"].startswith("legacy-policies"):
                    connection.execute(text("ALTER TABLE profiles RENAME TO policies"))
                    for index in inspect(connection).get_indexes("policies"):
                        connection.execute(text(f'DROP INDEX "{index["name"]}"'))
                connection.execute(
                    text("UPDATE alembic_version SET version_num = :revision"),
                    {"revision": source["stamp"]},
                )

            table_name = _matrix()["schema_shapes"][source["shape"]]["table"]
            assert isinstance(table_name, str)
            inspector = inspect(connection)
            if any("compliance" in row for row in _scenario_rows(source)) and "compliance" not in {
                column["name"] for column in inspector.get_columns(table_name)
            }:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN compliance JSON"))

            table = Table(table_name, MetaData(), autoload_with=connection)
            for source_row in _scenario_rows(source):
                values = {
                    column.name: _coerce_source_value(column.name, source_row[column.name])
                    for column in table.columns
                    if column.name in source_row
                }
                if "name_casefold" in table.c and "name_casefold" not in values:
                    values["name_casefold"] = str(source_row["name"]).casefold()
                if "baseline_provenance" in table.c and "baseline_provenance" not in values:
                    values["baseline_provenance"] = legacy_migration_baseline_provenance()
                if "extension_provenance" in table.c and "extension_provenance" not in values:
                    values["extension_provenance"] = imported_extension_provenance(
                        source_row["flags"]
                    )
                if "certificate_provenance" in table.c and "certificate_provenance" not in values:
                    values["certificate_provenance"] = imported_certificate_provenance(
                        source_row["flags"]
                    )
                connection.execute(table.insert().values(**values))
    finally:
        engine.dispose()


def _assert_head_schema(target: DatabaseTarget) -> None:
    engine = create_engine(target.sync_url, future=True)
    try:
        inspector = inspect(engine)
        assert "profiles" in inspector.get_table_names()
        assert "policies" not in inspector.get_table_names()
        assert {column["name"] for column in inspector.get_columns("profiles")} == {
            "id",
            "name",
            "name_casefold",
            "description",
            "schema_version",
            "flags",
            "compliance",
            "baseline_provenance",
            "extension_provenance",
            "certificate_provenance",
            "preparation_idempotency_key",
            "preparation_request_fingerprint",
            "revision",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert {index["name"] for index in inspector.get_indexes("profiles")} >= {
            "ix_profiles_name",
            "ix_profiles_name_casefold",
            "ix_profiles_schema_version",
            "ix_profiles_created_at",
            "ix_profiles_updated_at",
            "ix_profiles_deleted_at",
            "uq_profiles_preparation_idempotency_key",
        }
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == (HEAD_REVISION)
    finally:
        engine.dispose()


def _expected_channel(value: str) -> str:
    if value.startswith("release-") and value != "release-153":
        return "release-153"
    if value.startswith("esr-140"):
        return "esr-140.13"
    return value


def _json_semantic_value(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def _assert_golden_rows(target: DatabaseTarget, source: dict[str, Any]) -> None:
    source_rows = _scenario_rows(source)
    if not source_rows:
        return
    engine = create_engine(target.sync_url, future=True)
    try:
        with engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        "SELECT id, name, name_casefold, description, schema_version, flags, compliance, "
                        "baseline_provenance, extension_provenance, certificate_provenance, revision, deleted_at "
                        "FROM profiles ORDER BY id"
                    )
                )
                .mappings()
                .all()
            )
    finally:
        engine.dispose()

    assert len(rows) == len(source_rows)
    for stored, source_row in zip(rows, source_rows, strict=True):
        assert stored["id"] == source_row["id"]
        assert stored["name"] == source_row["name"]
        assert stored["name_casefold"] == source_row["name"].casefold()
        assert stored["description"] == source_row["description"]
        assert stored["schema_version"] == _expected_channel(source_row["schema_version"])
        assert _json_semantic_value(stored["flags"]) == source_row["flags"]
        assert _json_semantic_value(stored["compliance"]) == source_row.get("compliance")
        assert _json_semantic_value(stored["baseline_provenance"]) == (
            _expected_baseline_provenance(source)
        )
        assert _json_semantic_value(stored["extension_provenance"]) == (
            imported_extension_provenance(source_row["flags"])
        )
        assert _json_semantic_value(stored["certificate_provenance"]) == (
            imported_certificate_provenance(source_row["flags"])
        )
        assert stored["revision"] == source_row.get("revision", 1)
        assert (stored["deleted_at"] is None) is (source_row.get("deleted_at") is None)


def test_supported_upgrade_matrix_reaches_head_on_each_real_engine(
    database_target: DatabaseTarget,
) -> None:
    """Materialize every M4-01 source and migrate it through the real engine."""
    if database_target.name == "postgresql":
        engine = create_engine(database_target.sync_url, future=True)
        try:
            with engine.connect() as connection:
                assert "PostgreSQL" in str(
                    connection.execute(text("SELECT version()")).scalar_one()
                )
        finally:
            engine.dispose()

    for source in _matrix()["supported_sources"]:
        _prepare_supported_source(database_target, source)
        _upgrade(database_target)
        _assert_head_schema(database_target)
        _assert_golden_rows(database_target, source)


async def _create_and_commit(runtime: DatabaseRuntime, name: str) -> None:
    async with runtime.session() as session:
        await ProfileService.create(
            session,
            ProfileCreate(
                name=name,
                description="M4-05 real engine contract",
                schema_version="esr-140.13",
                flags={"DisableTelemetry": True, "Proxy": {"Mode": "none"}},
            ),
        )
        await session.commit()


@pytest.mark.anyio
async def test_common_crud_transaction_and_export_contract_on_each_real_engine(
    database_target: DatabaseTarget,
) -> None:
    database_target.reset()
    await asyncio.to_thread(_upgrade, database_target)
    runtime = DatabaseRuntime(database_url=database_target.runtime_url, echo=False)
    await runtime.init()
    worker_runtime = DatabaseRuntime(database_url=database_target.runtime_url, echo=False)
    await worker_runtime.init()
    try:
        assert runtime.engine is not worker_runtime.engine
        async with runtime.session() as session:
            created = await ProfileService.create(
                session,
                ProfileCreate(
                    name="m4-05-active",
                    description="Portable CRUD fixture",
                    schema_version="esr-140.13",
                    flags={"DisableTelemetry": True, "Proxy": {"Mode": "none"}},
                ),
            )
            await session.commit()

        async with runtime.session() as session:
            with pytest.raises(IntegrityError):
                await ProfileService.create(
                    session,
                    ProfileCreate(
                        name="m4-05-active",
                        schema_version="esr-140.13",
                        flags={"DisableTelemetry": True},
                    ),
                )
            await session.rollback()

        async with runtime.session() as session:
            listed = await ProfileService.list(session, q="M4-05", sort="name", order="asc")
            assert [item.id for item in listed] == [created.id]
            assert await ProfileService.soft_delete(session, created.id) is True
            await session.commit()

        async with runtime.session() as session:
            assert await ProfileService.get(session, created.id) is None
            archived = await ProfileService.list(session, lifecycle="archived")
            assert [item.id for item in archived] == [created.id]
            restored = await ProfileService.restore(session, created.id)
            assert restored is not None
            assert render_firefox_policies_document(restored.flags) == {
                "policies": {"DisableTelemetry": True, "Proxy": {"Mode": "none"}}
            }
            await session.commit()

        async with runtime.session() as session:
            session.add(
                Profile(
                    name="m4-05-rolled-back",
                    schema_version="esr-140.13",
                    flags={"DisableTelemetry": True},
                )
            )
            await session.flush()
            await session.rollback()

        async with runtime.session() as session:
            assert (
                await session.scalar(select(Profile.id).where(Profile.name == "m4-05-rolled-back"))
                is None
            )

        await _create_and_commit(runtime, "m4-05-worker-a")
        await _create_and_commit(worker_runtime, "m4-05-worker-b")
        async with runtime.session() as session:
            worker_names = set(
                await session.scalars(
                    select(Profile.name).where(Profile.name.like("m4-05-worker-%"))
                )
            )
            assert worker_names == {"m4-05-worker-a", "m4-05-worker-b"}
    finally:
        await runtime.dispose()
        await worker_runtime.dispose()

    assert runtime.engine is None
    assert runtime.initialized is False
    assert worker_runtime.engine is None
    assert worker_runtime.initialized is False


@pytest.mark.anyio
async def test_profile_page_query_is_unicode_exact_stable_and_bounded_on_each_real_engine(
    database_target: DatabaseTarget,
) -> None:
    """Prove SQL filtering/page limits without relying on either engine's LOWER()."""
    database_target.reset()
    await asyncio.to_thread(_upgrade, database_target)
    runtime = DatabaseRuntime(database_url=database_target.runtime_url, echo=False)
    await runtime.init()
    statements: list[str] = []

    def record_statement(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: object,
    ) -> None:
        if "FROM profiles" in statement:
            statements.append(statement)

    assert runtime.engine is not None
    event.listen(runtime.engine.sync_engine, "before_cursor_execute", record_statement)
    try:
        async with runtime.session() as session:
            created = []
            for name in ("Базовый A", "Базовый B", "Базовый C"):
                created.append(
                    await ProfileService.create(
                        session,
                        ProfileCreate(
                            name=name,
                            schema_version="release-153",
                            flags={"DisableTelemetry": True},
                        ),
                    )
                )
            await session.commit()

        async with runtime.session() as session:
            first_page = await ProfileService.page(
                session,
                q="БАЗОВЫЙ",
                sort="schema_version",
                order="asc",
                limit=2,
                offset=0,
            )
            second_page = await ProfileService.page(
                session,
                q="базовый",
                sort="schema_version",
                order="asc",
                limit=2,
                offset=2,
            )

        expected_ids = sorted(profile.id for profile in created)
        assert [profile.id for profile in (*first_page.items, *second_page.items)] == expected_ids
        assert first_page.filtered == second_page.filtered == 3
        assert first_page.query_metadata.candidate_rows == 2
        assert second_page.query_metadata.candidate_rows == 1
        assert first_page.query_metadata.page_is_bounded is True
        bounded_statements = [
            statement
            for statement in statements
            if "name_casefold" in statement and "LIMIT" in statement
        ]
        assert len(bounded_statements) >= 2
        assert all(
            "ORDER BY" in statement and "profiles.id" in statement
            for statement in bounded_statements
        )
    finally:
        event.remove(runtime.engine.sync_engine, "before_cursor_execute", record_statement)
        await runtime.dispose()
