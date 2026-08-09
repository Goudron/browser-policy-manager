from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.profile import Base
from app.schemas.profile import ProfileCreate
from app.services.profile_service import ProfileQuery, ProfileService
from tests.sync_session_adapter import SyncSessionAdapter


def _mk(schema: str, name_prefix: str = "SRV", flags: dict | None = None):
    u = uuid.uuid4().hex[:6]
    return ProfileCreate(
        name=f"{name_prefix}-{u}",
        description="Service list",
        schema_version=schema,
        flags=flags or {"DisableTelemetry": True},
    )


@pytest.fixture
def service_session() -> SyncSessionAdapter:
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    try:
        yield SyncSessionAdapter(session)
    finally:
        session.close()
        engine.dispose()


@pytest.mark.anyio
async def test_service_list_filters_sort_and_pagination_direct(service_session: SyncSessionAdapter):
    """Exercise ProfileService.list directly (schema_version/sort/limit/offset and q branch)."""
    for i in range(4):
        await ProfileService.create(service_session, _mk("esr-140.12", name_prefix=f"SVC-{i}"))
    await service_session.commit()

    items = await ProfileService.list(
        service_session,
        q=None,
        schema_version="esr-140.12",
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
        schema_version="esr-140.12",
        sort="updated_at",
        order="desc",
        limit=1,
        offset=1,
    )
    assert isinstance(items2, list)

    items3 = await ProfileService.list(
        service_session,
        q="SVC-",
        schema_version=None,
        sort="unknown_field",
        order="desc",
        limit=1,
        offset=0,
    )
    assert isinstance(items3, list)

    filtered_count = await ProfileService.count(
        service_session,
        schema_version="esr-140.12",
    )
    assert filtered_count == 4


@pytest.mark.anyio
async def test_service_list_name_query_is_case_insensitive_for_cyrillic(
    service_session: SyncSessionAdapter,
):
    created = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Корпоративный Профиль",
            description="Unicode search",
            schema_version="esr-140.12",
            flags={"DisableTelemetry": True},
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
    service_session: SyncSessionAdapter,
):
    created = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Корпоративный Профиль",
            description="Whitespace query",
            schema_version="esr-140.12",
            flags={"DisableTelemetry": True},
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


def test_profile_query_filters_keep_sql_filtering_in_one_helper() -> None:
    active = ProfileQuery(schema_version="esr-140.12")
    archived = ProfileQuery(lifecycle="archived")
    all_profiles = ProfileQuery(lifecycle="all")

    assert len(ProfileService._query_filters(active)) == 2
    assert len(ProfileService._query_filters(archived)) == 1
    assert ProfileService._query_filters(all_profiles) == []


def test_profile_query_post_filter_matches_name_and_validation_state(monkeypatch) -> None:
    class FakeProfile:
        name = "Базовый корпоративный профиль"
        flags = {"DisableTelemetry": True}

    monkeypatch.setattr(ProfileService, "_validation_state", lambda profile: "valid")

    assert ProfileService._matches_query(FakeProfile(), ProfileQuery(q="КОРПОРАТИВНЫЙ"))
    assert ProfileService._matches_query(
        FakeProfile(),
        ProfileQuery(q="базовый", validation_state="valid"),
    )
    assert not ProfileService._matches_query(FakeProfile(), ProfileQuery(q="missing"))
    assert not ProfileService._matches_query(
        FakeProfile(),
        ProfileQuery(validation_state="invalid"),
    )


class _CountingSession(SyncSessionAdapter):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.scalars_calls = 0

    async def scalars(self, *args, **kwargs):
        self.scalars_calls += 1
        return await super().scalars(*args, **kwargs)


@pytest.mark.anyio
async def test_service_page_derives_list_counts_lifecycle_and_pagination_from_one_read():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    raw_session = sessionmaker(bind=engine, expire_on_commit=False)()
    session = _CountingSession(raw_session)
    try:
        active = await ProfileService.create(session, _mk("release-153", "PAGE-Alpha"))
        archived = await ProfileService.create(session, _mk("release-153", "PAGE-Beta"))
        await session.commit()
        assert await ProfileService.soft_delete(session, archived.id)
        await session.commit()

        session.scalars_calls = 0
        result = await ProfileService.page(
            session,
            q="page",
            lifecycle="all",
            sort="name",
            order="asc",
            limit=1,
            offset=1,
        )

        assert session.scalars_calls == 1
        assert result.query_metadata.scalar_selects == 1
        assert result.query_metadata.aggregate_selects == 2
        assert result.query_metadata.candidate_rows == 1
        assert result.query_metadata.post_filtering is False
        assert result.query_metadata.page_is_bounded is True
        assert result.filtered == 2
        assert result.total == 2
        assert result.lifecycle.active == 1
        assert result.lifecycle.archived == 1
        assert result.pagination.returned == 1
        assert result.pagination.has_next is False
        assert result.items[0].id in {active.id, archived.id}

        empty_page = await ProfileService.page(session, q="missing", offset=10)
        assert empty_page.items == ()
        assert empty_page.filtered == 0
        assert empty_page.pagination.returned == 0
        assert empty_page.pagination.has_next is False
    finally:
        raw_session.close()
        engine.dispose()


@pytest.mark.anyio
async def test_service_page_pushes_unicode_name_filter_and_page_boundaries_into_sql(
    service_session: SyncSessionAdapter,
):
    first = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Профиль",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        ),
    )
    second = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="Базовый Второй",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        ),
    )
    await service_session.commit()

    result = await ProfileService.page(
        service_session,
        q="БАЗОВЫЙ",
        sort="schema_version",
        order="asc",
        limit=1,
        offset=0,
    )

    assert result.filtered == 2
    assert result.pagination.returned == 1
    assert result.pagination.has_next is True
    assert result.query_metadata.page_is_bounded is True
    assert result.query_metadata.candidate_rows == 1
    assert result.items[0].id == min(first.id, second.id)


@pytest.mark.anyio
async def test_service_name_search_treats_sql_wildcards_as_literal_characters(
    service_session: SyncSessionAdapter,
):
    literal = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="100%_coverage",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        ),
    )
    other = await ProfileService.create(
        service_session,
        ProfileCreate(
            name="100Xcoverage",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
        ),
    )
    await service_session.commit()

    result = await ProfileService.page(service_session, q="%_", limit=50)

    assert [profile.id for profile in result.items] == [literal.id]
    assert other.id not in {profile.id for profile in result.items}


@pytest.mark.anyio
async def test_validation_state_keeps_explicit_full_read_fallback(
    service_session: SyncSessionAdapter,
):
    await ProfileService.create(service_session, _mk("release-153", "VALIDATION"))
    await service_session.commit()

    result = await ProfileService.page(service_session, validation_state="valid", limit=1)

    assert result.query_metadata.post_filtering is True
    assert result.query_metadata.page_is_bounded is False
    assert result.query_metadata.aggregate_selects == 1


@pytest.mark.anyio
async def test_validation_state_filter_validates_each_candidate_once_and_carries_the_result(
    service_session: SyncSessionAdapter,
    monkeypatch,
):
    import app.services.profile_service as profile_service_module

    await ProfileService.create(service_session, _mk("release-153", "VALID-ONE"))
    await ProfileService.create(
        service_session,
        _mk("release-153", "INVALID-ONE", flags={"DisableTelemetry": "bad"}),
    )
    await ProfileService.create(
        service_session,
        ProfileCreate(
            name="EMPTY-ONE",
            schema_version="release-153",
            flags={},
        ),
    )
    await ProfileService.create(
        service_session,
        _mk("unknown-channel", "UNKNOWN-ONE", flags={"DisableTelemetry": True}),
    )
    await service_session.commit()

    actual_validator = profile_service_module.validate_profile_payload_with_schema
    validation_calls = 0

    def counted_validator(payload):
        nonlocal validation_calls
        validation_calls += 1
        return actual_validator(payload)

    monkeypatch.setattr(
        profile_service_module,
        "validate_profile_payload_with_schema",
        counted_validator,
    )

    result = await ProfileService.page(
        service_session,
        validation_state="valid",
        limit=50,
    )

    assert len(result.items) == 1
    assert result.items[0].name.startswith("VALID-ONE-")
    assert validation_calls == 3
    assert result.query_metadata.validation_calls == 3
    assert result.filtered == 1
    assert result.pagination.returned == 1


@pytest.mark.anyio
async def test_count_uses_page_summary_without_validating_unrequested_read_models(
    service_session: SyncSessionAdapter,
    monkeypatch,
):
    import app.services.profile_service as profile_service_module

    await ProfileService.create(service_session, _mk("release-153", "COUNT-ONE"))
    await service_session.commit()

    validation_calls = 0
    actual_validator = profile_service_module.validate_profile_payload_with_schema

    def counted_validator(payload):
        nonlocal validation_calls
        validation_calls += 1
        return actual_validator(payload)

    monkeypatch.setattr(
        profile_service_module,
        "validate_profile_payload_with_schema",
        counted_validator,
    )

    assert await ProfileService.count(service_session, schema_version="release-153") == 1
    assert validation_calls == 0


@pytest.mark.anyio
async def test_stats_adapter_filters_with_one_validation_per_candidate(
    service_session: SyncSessionAdapter,
    monkeypatch,
):
    import app.services.profile_service as profile_service_module
    from app.api import profiles as profiles_api

    await ProfileService.create(service_session, _mk("release-153", "STATS-VALID"))
    await ProfileService.create(
        service_session,
        _mk("release-153", "STATS-INVALID", flags={"DisableTelemetry": "bad"}),
    )
    await service_session.commit()

    validation_calls = 0
    actual_validator = profile_service_module.validate_profile_payload_with_schema

    def counted_validator(payload):
        nonlocal validation_calls
        validation_calls += 1
        return actual_validator(payload)

    monkeypatch.setattr(
        profile_service_module,
        "validate_profile_payload_with_schema",
        counted_validator,
    )

    stats = await profiles_api._profile_library_stats_core(
        service_session,
        schema_version="release-153",
        validation_state="valid",
    )

    assert stats == {"filtered": 1, "total": 2}
    assert validation_calls == 2
