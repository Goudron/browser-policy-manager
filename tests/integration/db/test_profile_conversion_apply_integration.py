from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, select, text

from alembic import command
from app.api.profiles import _conversion_apply_in_transaction
from app.core.profile_conversion_planner import plan_profile_conversion
from app.db import DatabaseRuntime
from app.models.profile import Profile
from app.schemas.profile import ConversionApplyRequest, ProfileCreate
from app.services.profile_service import ConversionApplyFailure, ProfileService

REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPORARY_POSTGRES_DATABASE = re.compile(r"^bpm_m4_05(?:_[a-z0-9]+)*$")


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
        if self.name == "sqlite":
            Path(self.alembic_url.removeprefix("sqlite:///")).unlink(missing_ok=True)
            return
        database_name = urlparse(self.alembic_url).path.removeprefix("/")
        if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
            raise RuntimeError(
                f"refusing to reset non-disposable PostgreSQL database {database_name!r}"
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
            pytest.fail("BPM_REQUIRE_POSTGRES=1 requires BPM_POSTGRES_TEST_URL")
        return None
    if "+asyncpg" not in url or not url.startswith("postgresql+"):
        pytest.fail("BPM_POSTGRES_TEST_URL must use a real postgresql+asyncpg URL")
    database_name = urlparse(url).path.removeprefix("/")
    if not _TEMPORARY_POSTGRES_DATABASE.fullmatch(database_name):
        pytest.fail("BPM_POSTGRES_TEST_URL must name only a bpm_m4_05* disposable database")
    return DatabaseTarget("postgresql", url, url)


@pytest.fixture(params=("sqlite", "postgresql"), ids=("sqlite", "postgresql"))
def conversion_database_target(request: pytest.FixtureRequest, tmp_path: Path) -> DatabaseTarget:
    if request.param == "sqlite":
        path = tmp_path / "m4-04-conversion.sqlite"
        return DatabaseTarget("sqlite", f"sqlite:///{path}", f"sqlite+aiosqlite:///{path}")
    target = _postgres_target()
    if target is None:
        pytest.skip("set BPM_POSTGRES_TEST_URL to run PostgreSQL conversion integration cases")
    return target


def _upgrade(target: DatabaseTarget) -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", target.alembic_url)
    command.upgrade(config, "head")


async def _runtime(target: DatabaseTarget) -> DatabaseRuntime:
    target.reset()
    await asyncio.to_thread(_upgrade, target)
    runtime = DatabaseRuntime(database_url=target.runtime_url, echo=False)
    await runtime.init()
    return runtime


async def _create_profile(runtime: DatabaseRuntime, *, schema_version: str, flags: dict) -> int:
    async with runtime.session() as session:
        created = await ProfileService.create(
            session,
            ProfileCreate(
                name=f"m4-04-{schema_version}-{len(flags)}-{id(session)}",
                description="real engine conversion fixture",
                schema_version=schema_version,
                flags=flags,
            ),
        )
        await session.commit()
        return created.id


async def _snapshot(runtime: DatabaseRuntime, profile_id: int) -> dict:
    async with runtime.session() as session:
        profile = await session.scalar(select(Profile).where(Profile.id == profile_id))
        assert profile is not None
        return {
            "id": profile.id,
            "name": profile.name,
            "name_casefold": profile.name_casefold,
            "description": profile.description,
            "schema_version": profile.schema_version,
            "flags": profile.flags,
            "compliance": profile.compliance,
            "revision": profile.revision,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "deleted_at": profile.deleted_at,
        }


async def _apply_request(
    runtime: DatabaseRuntime,
    *,
    profile_id: int,
    target_artifact_id: str,
) -> ConversionApplyRequest:
    async with runtime.session() as session:
        profile = await ProfileService.get_conversion_preview_source(session, profile_id)
        assert profile is not None
        plan = plan_profile_conversion(
            {"policies": profile.flags},
            source_artifact_id=profile.schema_version,
            target_artifact_id=target_artifact_id,
            context=ProfileService.conversion_planning_context(profile),
        ).plan
    return ConversionApplyRequest.model_validate(
        {
            "kind": "profile-conversion-apply-request",
            "contract_version": 1,
            "profile_id": profile_id,
            "expected_revision": plan["profile"]["revision"],
            "source": {
                "line_id": plan["source"]["artifact"]["line_id"],
                "artifact_id": plan["source"]["artifact"]["artifact_id"],
            },
            "target": {
                "line_id": plan["target"]["artifact"]["line_id"],
                "artifact_id": plan["target"]["artifact"]["artifact_id"],
            },
            "target_artifact_id": target_artifact_id,
            "plan_digest": plan["plan_digest"],
            "source_document_digest": plan["source"]["document_digest"],
            "source_compliance_digest": plan["source"]["compliance_digest"],
            "source_metadata_digest": plan["profile"]["metadata_digest"],
            "source_validation_schema_sha256": plan["source"]["artifact"][
                "validation_schema_sha256"
            ],
            "target_validation_schema_sha256": plan["target"]["artifact"][
                "validation_schema_sha256"
            ],
            "recipe_registry_version": plan["recipe_registry"]["registry_version"],
            "recipe_registry_digest": plan["recipe_registry"]["registry_digest"],
        }
    )


async def _apply(runtime: DatabaseRuntime, profile_id: int, request: ConversionApplyRequest):
    async with runtime.session() as session:
        return await _conversion_apply_in_transaction(
            session,
            profile_id=profile_id,
            payload=request,
        )


@pytest.mark.anyio
async def test_real_engine_apply_success_stale_retry_and_race_are_atomic(
    conversion_database_target: DatabaseTarget,
) -> None:
    runtime = await _runtime(conversion_database_target)
    worker_runtime = DatabaseRuntime(
        database_url=conversion_database_target.runtime_url, echo=False
    )
    await worker_runtime.init()
    try:
        profile_id = await _create_profile(
            runtime,
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True, "Proxy": {"Mode": "none"}},
        )
        before = await _snapshot(runtime, profile_id)
        request = await _apply_request(
            runtime,
            profile_id=profile_id,
            target_artifact_id="esr-153.0",
        )
        outcomes = await asyncio.gather(
            _apply(runtime, profile_id, request),
            _apply(worker_runtime, profile_id, request),
            return_exceptions=True,
        )
        after = await _snapshot(runtime, profile_id)

        successes = [outcome for outcome in outcomes if not isinstance(outcome, BaseException)]
        failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
        assert len(successes) == 1
        assert len(failures) == 1
        assert isinstance(failures[0], ConversionApplyFailure)
        assert failures[0].code == "conversion_revision_stale"
        assert after["schema_version"] == "esr-153.0"
        assert after["flags"] == before["flags"]
        assert after["compliance"] == before["compliance"]
        assert after["revision"] == before["revision"] + 1
        assert after["updated_at"] >= before["updated_at"]
        assert successes[0].updated_at_changed is (after["updated_at"] != before["updated_at"])
        for field in ("id", "name", "name_casefold", "description", "created_at", "deleted_at"):
            assert after[field] == before[field]

        with pytest.raises(ConversionApplyFailure, match="conversion_revision_stale"):
            await _apply(runtime, profile_id, request)
        assert await _snapshot(runtime, profile_id) == after
    finally:
        await runtime.dispose()
        await worker_runtime.dispose()


@pytest.mark.anyio
async def test_real_engine_blocked_and_stale_identity_requests_do_not_mutate(
    conversion_database_target: DatabaseTarget,
) -> None:
    runtime = await _runtime(conversion_database_target)
    try:
        profile_id = await _create_profile(
            runtime,
            schema_version="esr-153.0",
            flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
        )
        before = await _snapshot(runtime, profile_id)
        blocked = await _apply_request(
            runtime,
            profile_id=profile_id,
            target_artifact_id="esr-115.38",
        )
        with pytest.raises(ConversionApplyFailure, match="conversion_plan_blocked"):
            await _apply(runtime, profile_id, blocked)
        assert await _snapshot(runtime, profile_id) == before

        valid = await _apply_request(
            runtime,
            profile_id=profile_id,
            target_artifact_id="esr-140.13",
        )
        stale = valid.model_copy(update={"plan_digest": "f" * 64})
        with pytest.raises(ConversionApplyFailure, match="conversion_plan_stale"):
            await _apply(runtime, profile_id, stale)
        assert await _snapshot(runtime, profile_id) == before
    finally:
        await runtime.dispose()


@pytest.mark.anyio
async def test_real_engine_rollback_after_service_write_restores_every_field(
    conversion_database_target: DatabaseTarget,
) -> None:
    runtime = await _runtime(conversion_database_target)
    try:
        profile_id = await _create_profile(
            runtime,
            schema_version="esr-140.13",
            flags={"DisableTelemetry": True},
        )
        before = await _snapshot(runtime, profile_id)
        request = await _apply_request(
            runtime,
            profile_id=profile_id,
            target_artifact_id="esr-153.0",
        )
        async with runtime.session() as session:
            if conversion_database_target.name == "sqlite":
                await session.execute(text("BEGIN IMMEDIATE"))
            else:
                await session.begin()
            try:
                await ProfileService.apply_conversion(session, profile_id, request)
                raise RuntimeError("injected post-write failure")
            except RuntimeError:
                await session.rollback()
        assert await _snapshot(runtime, profile_id) == before
    finally:
        await runtime.dispose()
