"""BPM096-M3-07 real-engine atomic preparation and recovery proof."""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest
from alembic.config import Config
from fastapi import status
from sqlalchemy import create_engine, text

from alembic import command
from app.api.profiles import _create_prepared_duplicate_profile_in_transaction
from app.db import DatabaseRuntime
from app.main import create_app
from app.schemas.profile import DuplicateProfilePreparationRequest
from app.services.profile_service import ProfileService

REPO_ROOT = Path(__file__).resolve().parents[3]
_DISPOSABLE_POSTGRES_DATABASE = re.compile(r"^bpm_(?:m3_07|m4_05)(?:_[a-z0-9]+)*$")
PREPARE_NEW_PATH = "/api/profiles/prepare/new"
PREPARE_DUPLICATE_PATH = "/api/profiles/prepare/duplicate"
PREVIEW_DUPLICATE_PATH = "/api/profiles/prepare/duplicate/preview"


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
        """Reset only the selected disposable test target."""

        if self.name == "sqlite":
            Path(self.alembic_url.removeprefix("sqlite:///")).unlink(missing_ok=True)
            return

        database_name = urlparse(self.alembic_url).path.removeprefix("/")
        if not _DISPOSABLE_POSTGRES_DATABASE.fullmatch(database_name):
            raise RuntimeError(
                "Refusing to reset PostgreSQL database outside the disposable BPM test naming "
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
            pytest.fail("BPM_REQUIRE_POSTGRES=1 requires BPM_POSTGRES_TEST_URL")
        return None
    if not url.startswith("postgresql+") or "+asyncpg" not in url:
        pytest.fail("BPM_POSTGRES_TEST_URL must use postgresql+asyncpg")
    database_name = urlparse(url).path.removeprefix("/")
    if not _DISPOSABLE_POSTGRES_DATABASE.fullmatch(database_name):
        pytest.fail(
            "BPM_POSTGRES_TEST_URL must use a disposable bpm_m3_07* or bpm_m4_05* database, "
            f"got {database_name!r}"
        )
    return DatabaseTarget(name="postgresql", alembic_url=url, runtime_url=url)


@pytest.fixture(params=("sqlite", "postgresql"), ids=("sqlite", "postgresql"))
def database_target(request: pytest.FixtureRequest, tmp_path: Path) -> DatabaseTarget:
    if request.param == "sqlite":
        path = tmp_path / "m3-07.sqlite"
        return DatabaseTarget(
            name="sqlite",
            alembic_url=f"sqlite:///{path}",
            runtime_url=f"sqlite+aiosqlite:///{path}",
        )
    target = _postgres_target()
    if target is None:
        pytest.skip("set BPM_POSTGRES_TEST_URL to run the PostgreSQL M3-07 proof")
    return target


def _upgrade(target: DatabaseTarget) -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", target.alembic_url)
    command.upgrade(config, "head")


@asynccontextmanager
async def _prepared_client(target: DatabaseTarget):
    target.reset()
    await asyncio.to_thread(_upgrade, target)
    runtime = DatabaseRuntime(database_url=target.runtime_url, echo=False)
    app = create_app(database_runtime=runtime)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, runtime


def _new_payload(name: str, *, key: str | None = None) -> dict[str, object]:
    return {
        "name": name,
        "target_schema_id": "release-153",
        "starter_id": "blank",
        "cis_baseline_id": "none",
        "preparation_idempotency_key": key or uuid.uuid4().hex,
    }


def _duplicate_payload(
    source: dict[str, object], name: str, *, key: str | None = None
) -> dict[str, object]:
    return {
        "name": name,
        "target_schema_id": "release-153",
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "preparation_idempotency_key": key or uuid.uuid4().hex,
    }


def _duplicate_preview_payload(
    source: dict[str, object], *, target_schema_id: str
) -> dict[str, object]:
    return {
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "target_schema_id": target_schema_id,
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
    }


async def _create_source(client: httpx.AsyncClient, name: str) -> dict[str, object]:
    response = await client.post(PREPARE_NEW_PATH, json=_new_payload(name))
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _assert_preparation_error(response: httpx.Response, code: str) -> None:
    assert response.status_code == status.HTTP_409_CONFLICT, response.text
    assert response.json()["detail"] == {
        "kind": "profile-preparation-error",
        "contract_version": 1,
        "code": code,
        "i18n_key": f"profiles.preparation_error_{code}",
        "http_status": status.HTTP_409_CONFLICT,
        "mutation": "none",
        "parameters": {},
    }


async def _all_profiles(client: httpx.AsyncClient) -> list[dict[str, object]]:
    response = await client.get(
        "/api/profiles",
        params={"lifecycle": "all", "sort": "id", "order": "asc"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


def _persisted_source_snapshot(target: DatabaseTarget, profile_id: int) -> dict[str, object]:
    """Read every profile-owned source field without using the public projection."""

    engine = create_engine(target.sync_url, future=True)
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT id, name, name_casefold, description, schema_version, flags, "
                        "compliance, baseline_provenance, extension_provenance, "
                        "preparation_idempotency_key, "
                        "preparation_request_fingerprint, revision, created_at, updated_at, "
                        "deleted_at FROM profiles WHERE id = :profile_id"
                    ),
                    {"profile_id": profile_id},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    snapshot = dict(row)
    for field in ("flags", "compliance", "baseline_provenance", "extension_provenance"):
        if isinstance(snapshot[field], str):
            snapshot[field] = json.loads(snapshot[field])
    return snapshot


@pytest.mark.anyio
async def test_simultaneous_new_names_and_retries_have_one_deterministic_outcome_per_engine(
    database_target: DatabaseTarget,
) -> None:
    async with _prepared_client(database_target) as (client, _runtime):
        shared_name = f"M3-07 same name {uuid.uuid4().hex}"
        first_payload = _new_payload(shared_name)
        second_payload = _new_payload(shared_name)
        first, second = await asyncio.wait_for(
            asyncio.gather(
                client.post(PREPARE_NEW_PATH, json=first_payload),
                client.post(PREPARE_NEW_PATH, json=second_payload),
            ),
            timeout=20,
        )
        assert sorted((first.status_code, second.status_code)) == [
            status.HTTP_201_CREATED,
            status.HTTP_409_CONFLICT,
        ]
        conflict = first if first.status_code == status.HTTP_409_CONFLICT else second
        _assert_preparation_error(conflict, "preparation_name_conflict")

        retry_payload = _new_payload(f"M3-07 retry {uuid.uuid4().hex}")
        retry_one, retry_two = await asyncio.wait_for(
            asyncio.gather(
                client.post(PREPARE_NEW_PATH, json=retry_payload),
                client.post(PREPARE_NEW_PATH, json=retry_payload),
            ),
            timeout=20,
        )
        assert retry_one.status_code == retry_two.status_code == status.HTTP_201_CREATED
        assert retry_one.json() == retry_two.json()
        mismatch = await client.post(
            PREPARE_NEW_PATH,
            json={**retry_payload, "name": f"M3-07 key misuse {uuid.uuid4().hex}"},
        )
        _assert_preparation_error(mismatch, "preparation_idempotency_key_reused")

        rows = await _all_profiles(client)

    assert [row["name"] for row in rows].count(shared_name) == 1
    assert [row["name"] for row in rows].count(retry_payload["name"]) == 1
    assert len(rows) == 2


@pytest.mark.anyio
async def test_duplicate_preview_is_read_only_for_all_supported_target_schemas(
    database_target: DatabaseTarget,
) -> None:
    target_schema_ids = ("release-153", "esr-153.0", "esr-140.13", "esr-115.39")
    async with _prepared_client(database_target) as (client, _runtime):
        source = await _create_source(client, f"M4-04 preview source {uuid.uuid4().hex}")
        source_before = (await client.get(f"/api/profiles/{source['id']}")).json()
        persisted_source_before = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )
        previews = [
            await client.post(
                PREVIEW_DUPLICATE_PATH,
                json=_duplicate_preview_payload(source, target_schema_id=target_schema_id),
            )
            for target_schema_id in target_schema_ids
        ]
        source_after = await client.get(f"/api/profiles/{source['id']}")
        persisted_source_after = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )
        rows = await _all_profiles(client)

    for preview in previews:
        assert preview.status_code == status.HTTP_200_OK, preview.text
        assert preview.json()["status"] == "valid"
        assert preview.json()["reason_code"] is None
        assert len(preview.json()["plan_digest"]) == 64
    assert source_after.json() == source_before
    assert persisted_source_after == persisted_source_before
    assert [row["id"] for row in rows] == [source["id"]]


@pytest.mark.anyio
async def test_duplicate_retries_and_lost_response_reconcile_without_source_mutation(
    database_target: DatabaseTarget,
) -> None:
    async with _prepared_client(database_target) as (client, runtime):
        source = await _create_source(client, f"M3-07 source {uuid.uuid4().hex}")
        source_before = (await client.get(f"/api/profiles/{source['id']}")).json()
        persisted_source_before = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )

        retry_payload = _duplicate_payload(source, f"M3-07 duplicate {uuid.uuid4().hex}")
        retry_one, retry_two = await asyncio.wait_for(
            asyncio.gather(
                client.post(PREPARE_DUPLICATE_PATH, json=retry_payload),
                client.post(PREPARE_DUPLICATE_PATH, json=retry_payload),
            ),
            timeout=20,
        )
        assert retry_one.status_code == retry_two.status_code == status.HTTP_201_CREATED
        assert retry_one.json() == retry_two.json()

        lost_payload = _duplicate_payload(source, f"M3-07 lost response {uuid.uuid4().hex}")
        async with runtime.session() as session:
            # Commit succeeds but the returned value is deliberately discarded,
            # modelling a response loss after commit rather than a terminal failure.
            committed = await _create_prepared_duplicate_profile_in_transaction(
                session,
                DuplicateProfilePreparationRequest.model_validate(lost_payload),
            )
        reconciled = await client.post(PREPARE_DUPLICATE_PATH, json=lost_payload)
        source_after = await client.get(f"/api/profiles/{source['id']}")
        persisted_source_after = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )
        rows = await _all_profiles(client)

    assert reconciled.status_code == status.HTTP_201_CREATED, reconciled.text
    assert reconciled.json()["id"] == committed.id
    assert source_after.json() == source_before
    assert persisted_source_after == persisted_source_before
    assert {row["id"] for row in rows} == {
        source["id"],
        retry_one.json()["id"],
        committed.id,
    }


@pytest.mark.anyio
async def test_stale_and_archived_duplicate_sources_are_deterministic_and_write_no_target(
    database_target: DatabaseTarget,
) -> None:
    async with _prepared_client(database_target) as (client, _runtime):
        stale_source = await _create_source(client, f"M3-07 stale source {uuid.uuid4().hex}")
        stale_payload = _duplicate_payload(stale_source, f"M3-07 stale target {uuid.uuid4().hex}")
        updated = await client.patch(
            f"/api/profiles/{stale_source['id']}",
            json={"description": "revision changed", "expected_revision": stale_source["revision"]},
        )
        assert updated.status_code == status.HTTP_200_OK, updated.text
        source_after_update = updated.json()
        persisted_stale_after_update = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(stale_source["id"]),
        )
        stale_one = await client.post(PREPARE_DUPLICATE_PATH, json=stale_payload)
        stale_two = await client.post(PREPARE_DUPLICATE_PATH, json=stale_payload)
        _assert_preparation_error(stale_one, "preparation_source_stale")
        _assert_preparation_error(stale_two, "preparation_source_stale")

        archived_source = await _create_source(client, f"M3-07 archived source {uuid.uuid4().hex}")
        archived = await client.delete(f"/api/profiles/{archived_source['id']}")
        assert archived.status_code == status.HTTP_204_NO_CONTENT, archived.text
        archived_before = (
            await client.get(
                f"/api/profiles/{archived_source['id']}", params={"include_deleted": "true"}
            )
        ).json()
        persisted_archived_before = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(archived_source["id"]),
        )
        archived_payload = _duplicate_payload(
            archived_before,
            f"M3-07 archived target {uuid.uuid4().hex}",
        )
        archived_one = await client.post(PREPARE_DUPLICATE_PATH, json=archived_payload)
        archived_two = await client.post(PREPARE_DUPLICATE_PATH, json=archived_payload)
        _assert_preparation_error(archived_one, "preparation_duplicate_source_not_eligible")
        _assert_preparation_error(archived_two, "preparation_duplicate_source_not_eligible")
        stale_after = await client.get(f"/api/profiles/{stale_source['id']}")
        archived_after = await client.get(
            f"/api/profiles/{archived_source['id']}", params={"include_deleted": "true"}
        )
        persisted_stale_after = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(stale_source["id"]),
        )
        persisted_archived_after = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(archived_source["id"]),
        )
        rows = await _all_profiles(client)

    assert stale_after.json() == source_after_update
    assert archived_after.json() == archived_before
    assert persisted_stale_after == persisted_stale_after_update
    assert persisted_archived_after == persisted_archived_before
    assert {row["id"] for row in rows} == {stale_source["id"], archived_source["id"]}


@pytest.mark.anyio
async def test_duplicate_interruption_rolls_back_target_and_preserves_source(
    database_target: DatabaseTarget,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _prepared_client(database_target) as (client, _runtime):
        source = await _create_source(client, f"M3-07 rollback source {uuid.uuid4().hex}")
        source_before = (await client.get(f"/api/profiles/{source['id']}")).json()
        persisted_source_before = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )
        payload = _duplicate_payload(source, f"M3-07 rollback target {uuid.uuid4().hex}")

        def interrupt_after_insert(*_args, **_kwargs):
            raise RuntimeError("BPM096-M3-07 controlled interruption before commit")

        with monkeypatch.context() as patch:
            patch.setattr(
                ProfileService,
                "_as_read_model",
                staticmethod(interrupt_after_insert),
            )
            interrupted = await client.post(PREPARE_DUPLICATE_PATH, json=payload)

        source_after = await client.get(f"/api/profiles/{source['id']}")
        persisted_source_after = await asyncio.to_thread(
            _persisted_source_snapshot,
            database_target,
            int(source["id"]),
        )
        rows = await _all_profiles(client)

    assert interrupted.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, interrupted.text
    assert interrupted.json()["detail"]["code"] == "preparation_transaction_failed"
    assert source_after.json() == source_before
    assert persisted_source_after == persisted_source_before
    assert [row["id"] for row in rows] == [source["id"]]
