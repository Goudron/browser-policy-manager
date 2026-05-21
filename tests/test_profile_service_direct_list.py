from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import AsyncSessionAdapter
from app.models.profile import Base
from app.schemas.profile import ProfileCreate
from app.services.profile_service import ProfileService


def _mk(owner: str, schema: str, name_prefix: str = "SRV", flags: dict | None = None):
    u = uuid.uuid4().hex[:6]
    return ProfileCreate(
        name=f"{name_prefix}-{u}",
        description="Service list",
        schema_version=schema,
        flags=flags or {"DisableTelemetry": True},
        owner=owner,
    )


@pytest.fixture
def service_session() -> AsyncSessionAdapter:
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    try:
        yield AsyncSessionAdapter(session)
    finally:
        session.close()
        engine.dispose()


@pytest.mark.anyio
async def test_service_list_filters_sort_and_pagination_direct(service_session: AsyncSessionAdapter):
    """Exercise ProfileService.list directly (owner/schema_version/sort/limit/offset and q branch)."""
    for owner in ("ops@example.org", "sec@example.org"):
        for i in range(2):
            await ProfileService.create(
                service_session, _mk(owner, "esr-140.11", name_prefix=f"SVC-{i}")
            )
    await service_session.commit()

    items = await ProfileService.list(
        service_session,
        q=None,
        owner="ops@example.org",
        schema_version="esr-140.11",
        sort="name",
        order="asc",
        limit=2,
        offset=0,
    )
    assert isinstance(items, list)
    assert len(items) >= 1

    items2 = await ProfileService.list(
        service_session,
        q=None,
        owner=None,
        schema_version="esr-140.11",
        sort="updated_at",
        order="desc",
        limit=1,
        offset=1,
    )
    assert isinstance(items2, list)

    items3 = await ProfileService.list(
        service_session,
        q="SVC-",
        owner=None,
        schema_version=None,
        sort="unknown_field",
        order="desc",
        limit=1,
        offset=0,
    )
    assert isinstance(items3, list)

    filtered_count = await ProfileService.count(
        service_session,
        owner="ops@example.org",
        schema_version="esr-140.11",
    )
    assert filtered_count == 2


@pytest.mark.anyio
async def test_service_list_name_query_is_case_insensitive_for_cyrillic(service_session: AsyncSessionAdapter):
    created = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Корпоративный Профиль",
            description="Unicode search",
            schema_version="esr-140.11",
            flags={"DisableTelemetry": True},
            owner="ops@example.org",
        ),
    )
    await service_session.commit()

    lower = await ProfileService.list(service_session, q="базовый", limit=50, offset=0)
    upper = await ProfileService.list(service_session, q="БАЗОВЫЙ", limit=50, offset=0)
    mixed = await ProfileService.list(service_session, q="кОрПоРаТиВнЫй", limit=50, offset=0)
    count = await ProfileService.count(service_session, q="ПРОФИЛЬ")

    assert created.id in {item.id for item in lower}
    assert created.id in {item.id for item in upper}
    assert created.id in {item.id for item in mixed}
    assert count >= 1


@pytest.mark.anyio
async def test_service_list_name_query_treats_empty_and_whitespace_as_no_filter(
    service_session: AsyncSessionAdapter,
):
    created = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Корпоративный Профиль",
            description="Whitespace query",
            schema_version="esr-140.11",
            flags={"DisableTelemetry": True},
            owner="ops@example.org",
        ),
    )
    await service_session.commit()

    empty_query = await ProfileService.list(service_session, q="", limit=50, offset=0)
    whitespace_query = await ProfileService.list(service_session, q="   ", limit=50, offset=0)

    ids_empty = {item.id for item in empty_query}
    ids_whitespace = {item.id for item in whitespace_query}

    assert created.id in ids_empty
    assert created.id in ids_whitespace


def test_matches_name_query_returns_true_for_missing_query() -> None:
    assert ProfileService._matches_name_query("Any profile", None) is True
    assert ProfileService._matches_name_query("Any profile", "") is True
