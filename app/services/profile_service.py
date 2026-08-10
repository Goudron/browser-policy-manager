# app/services/profile_service.py
from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import and_, asc, case, delete, desc, func, select, true
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

SortField = str  # "created_at" | "updated_at" | "name" | "schema_version" | "id"
SortOrder = str  # "asc" | "desc"


@dataclass(frozen=True, slots=True)
class ProfileQuery:
    q: str | None = None
    schema_version: str | None = None
    validation_state: str | None = None
    lifecycle: str = "active"
    include_deleted: bool = False
    limit: int = 50
    offset: int = 0
    sort: SortField = "updated_at"
    order: SortOrder = "desc"


@dataclass(frozen=True, slots=True)
class ProfilePagination:
    """Pagination facts derived from one profile-library read."""

    limit: int
    offset: int
    returned: int
    filtered: int
    has_next: bool


@dataclass(frozen=True, slots=True)
class ProfileLifecycleStats:
    """Lifecycle counts for the schema-scoped candidates of a page operation."""

    active: int
    archived: int
    all: int


@dataclass(frozen=True, slots=True)
class ProfileQueryMetadata:
    """Measured work performed by the service-owned page operation."""

    scalar_selects: int
    aggregate_selects: int
    candidate_rows: int
    validation_calls: int
    post_filtering: bool
    page_is_bounded: bool


@dataclass(frozen=True, slots=True)
class ProfilePageResult:
    """Canonical result for one profile library read.

    HTTP adapters deliberately expose only the characterized list or stats
    projection. Keeping the complete result here prevents callers which need
    both projections from repeating the same database read.
    """

    items: tuple[ProfileRead, ...]
    filtered: int
    total: int
    lifecycle: ProfileLifecycleStats
    pagination: ProfilePagination
    query_metadata: ProfileQueryMetadata


class ProfileService:
    """Business logic for profile CRUD, with soft delete and filtering."""

    # --- helpers ---

    @staticmethod
    def _matches_name_query(name: str | None, query: str | None) -> bool:
        if not query:
            return True
        candidate = (name or "").casefold()
        needle = query.strip().casefold()
        if not needle:
            return True
        return needle in candidate

    @staticmethod
    def _sort_clause(field: SortField, order: SortOrder) -> ColumnElement:
        field_map = {
            "created_at": Profile.created_at,
            "updated_at": Profile.updated_at,
            "name": Profile.name,
            "schema_version": Profile.schema_version,
            "id": Profile.id,
        }
        col = field_map.get(field, Profile.updated_at)
        return asc(col) if order == "asc" else desc(col)

    @staticmethod
    def _sort_clauses(field: SortField, order: SortOrder) -> tuple[ColumnElement, ...]:
        """Return a deterministic order, including a stable page tie-breaker."""
        primary = ProfileService._sort_clause(field, order)
        if field == "id":
            return (primary,)
        return (primary, asc(Profile.id) if order == "asc" else desc(Profile.id))

    @staticmethod
    def _name_query_value(query: str | None) -> str | None:
        if not query:
            return None
        value = query.strip().casefold()
        return value or None

    @staticmethod
    def _query_filters(
        query: ProfileQuery,
        *,
        include_lifecycle: bool = True,
        include_name: bool = True,
    ) -> builtins.list[ColumnElement[bool]]:
        filters: builtins.list[ColumnElement[bool]] = []

        if include_lifecycle:
            if query.lifecycle == "archived":
                filters.append(Profile.deleted_at.is_not(None))
            elif query.lifecycle != "all" and not query.include_deleted:
                filters.append(Profile.deleted_at.is_(None))

        if query.schema_version:
            filters.append(Profile.schema_version == query.schema_version)

        name_query = ProfileService._name_query_value(query.q)
        if include_name and name_query is not None:
            # contains(autoescape=True) keeps '%' and '_' literal, exactly as
            # Python's old substring check did, on both supported engines.
            filters.append(Profile.name_casefold.contains(name_query, autoescape=True))

        return filters

    @staticmethod
    def _apply_query_filters(stmt, query: ProfileQuery):
        filters = ProfileService._query_filters(query)
        return stmt.where(*filters) if filters else stmt

    @staticmethod
    def _lifecycle_count_value(
        query: ProfileQuery,
        *,
        active: int,
        archived: int,
        all_profiles: int,
    ) -> int:
        if query.lifecycle == "archived":
            return archived
        if query.lifecycle == "all" or query.include_deleted:
            return all_profiles
        return active

    @staticmethod
    def _matches_lifecycle(profile: Profile, query: ProfileQuery) -> bool:
        if query.lifecycle == "archived":
            return profile.deleted_at is not None
        if query.lifecycle == "all" or query.include_deleted:
            return True
        return profile.deleted_at is None

    @staticmethod
    def _matches_query(
        profile: Profile,
        query: ProfileQuery,
        *,
        validation_state: str | None = None,
    ) -> bool:
        if not ProfileService._matches_name_query(profile.name, query.q):
            return False
        if query.validation_state and (
            (
                validation_state
                if validation_state is not None
                else ProfileService._validation_state(profile)
            )
            != query.validation_state
        ):
            return False
        return True

    @staticmethod
    def _validation_state(profile: Profile) -> str:
        if not profile.flags:
            return "not_validated"
        try:
            validate_profile_payload_with_schema(
                {
                    "channel": profile.schema_version,
                    "policies": profile.flags,
                }
            )
        except PolicyValidationError:
            return "invalid"
        except ValueError:
            return "invalid"
        return "valid"

    @staticmethod
    def _as_read_model(
        profile: Profile,
        *,
        validation_state: str | None = None,
    ) -> ProfileRead:
        return ProfileRead.model_validate(profile).model_copy(
            update={
                "validation_state": (
                    validation_state
                    if validation_state is not None
                    else ProfileService._validation_state(profile)
                )
            }
        )

    # --- CRUD ---

    @staticmethod
    async def page(
        session: AsyncSession,
        *,
        q: str | None = None,
        schema_version: str | None = None,
        validation_state: str | None = None,
        lifecycle: str = "active",
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
        include_items: bool = True,
    ) -> ProfilePageResult:
        """Read one profile-library page and all projections from one select.

        SQL owns ordinary name filtering, ordering and page boundaries.  The
        only intentionally non-SQL filter is ``validation_state``: evaluation
        runs the canonical schema validator once per candidate and carries its
        result into the read model.  It retains the characterized full-read
        fallback, without duplicate validation of returned profiles.
        """
        query = ProfileQuery(
            q=q,
            schema_version=schema_version,
            validation_state=validation_state,
            lifecycle=lifecycle,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
        )
        candidate_filters = ProfileService._query_filters(
            query,
            include_lifecycle=False,
            include_name=False,
        )
        page_filters = ProfileService._query_filters(query)
        candidate_predicate = and_(*candidate_filters) if candidate_filters else true()
        page_predicate = and_(*page_filters) if page_filters else true()

        aggregate_stmt = select(
            func.count(Profile.id).label("all"),
            func.coalesce(func.sum(case((Profile.deleted_at.is_(None), 1), else_=0)), 0).label(
                "active"
            ),
        ).where(candidate_predicate)
        aggregate = (await session.execute(aggregate_stmt)).mappings().one()
        all_profiles = int(aggregate["all"])
        active = int(aggregate["active"])
        archived = all_profiles - active
        total = ProfileService._lifecycle_count_value(
            query,
            active=active,
            archived=archived,
            all_profiles=all_profiles,
        )

        if query.validation_state is not None:
            # Do not pretend a schema-validation filter is SQL-pushdown.  The
            # authoritative validator remains the only correct implementation.
            stmt = (
                select(Profile)
                .where(page_predicate)
                .order_by(*ProfileService._sort_clauses(query.sort, query.order))
            )
            candidates = list(await session.scalars(stmt))
            validated_candidates = [
                (profile, ProfileService._validation_state(profile)) for profile in candidates
            ]
            filtered_items = [
                (profile, state)
                for profile, state in validated_candidates
                if ProfileService._matches_query(profile, query, validation_state=state)
            ]
            filtered = len(filtered_items)
            page_items = (
                filtered_items[query.offset : query.offset + query.limit] if include_items else []
            )
            candidate_rows = len(candidates)
            validation_calls = sum(1 for profile in candidates if profile.flags)
            page_is_bounded = False
        else:
            filtered = int(
                (
                    await session.execute(select(func.count(Profile.id)).where(page_predicate))
                ).scalar_one()
            )
            if include_items:
                stmt = (
                    select(Profile)
                    .where(page_predicate)
                    .order_by(*ProfileService._sort_clauses(query.sort, query.order))
                    .limit(query.limit)
                    .offset(query.offset)
                )
                page_profiles = list(await session.scalars(stmt))
                page_items = [
                    (profile, ProfileService._validation_state(profile))
                    for profile in page_profiles
                ]
                candidate_rows = len(page_profiles)
                validation_calls = sum(1 for profile in page_profiles if profile.flags)
            else:
                page_items = []
                candidate_rows = 0
                validation_calls = 0
            page_is_bounded = True

        read_items = tuple(
            ProfileService._as_read_model(profile, validation_state=validation_state)
            for profile, validation_state in page_items
        )
        return ProfilePageResult(
            items=read_items,
            filtered=filtered,
            total=total,
            lifecycle=ProfileLifecycleStats(
                active=active,
                archived=archived,
                all=all_profiles,
            ),
            pagination=ProfilePagination(
                limit=query.limit,
                offset=query.offset,
                returned=len(read_items),
                filtered=filtered,
                has_next=query.offset + len(read_items) < filtered,
            ),
            query_metadata=ProfileQueryMetadata(
                scalar_selects=1 if include_items else 0,
                aggregate_selects=1 if query.validation_state is not None else 2,
                candidate_rows=candidate_rows,
                validation_calls=validation_calls,
                post_filtering=query.validation_state is not None,
                page_is_bounded=page_is_bounded,
            ),
        )

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        q: str | None = None,
        schema_version: str | None = None,
        validation_state: str | None = None,
        lifecycle: str = "active",
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
    ) -> builtins.list[ProfileRead]:
        result = await ProfileService.page(
            session,
            q=q,
            schema_version=schema_version,
            validation_state=validation_state,
            lifecycle=lifecycle,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
        )
        return list(result.items)

    @staticmethod
    async def get(
        session: AsyncSession, profile_id: int, include_deleted: bool = False
    ) -> ProfileRead | None:
        stmt = select(Profile).where(Profile.id == profile_id)
        if not include_deleted:
            stmt = stmt.where(Profile.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        return ProfileService._as_read_model(entity) if entity else None

    @staticmethod
    async def count(
        session: AsyncSession,
        *,
        q: str | None = None,
        schema_version: str | None = None,
        validation_state: str | None = None,
        lifecycle: str = "active",
        include_deleted: bool = False,
    ) -> int:
        result = await ProfileService.page(
            session,
            q=q,
            schema_version=schema_version,
            validation_state=validation_state,
            lifecycle=lifecycle,
            include_deleted=include_deleted,
            include_items=False,
        )
        return result.filtered

    @staticmethod
    async def create(session: AsyncSession, data: ProfileCreate) -> ProfileRead:
        entity = Profile(
            name=data.name,
            description=data.description,
            schema_version=data.schema_version,
            flags=data.flags,
            compliance=data.compliance,
        )
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return ProfileService._as_read_model(entity)

    @staticmethod
    async def update(
        session: AsyncSession, profile_id: int, data: ProfileUpdate
    ) -> ProfileRead | None:
        stmt = select(Profile).where(Profile.id == profile_id, Profile.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return None

        fields_to_update = data.model_fields_set

        if "description" in fields_to_update:
            entity.description = data.description
        if "schema_version" in fields_to_update and data.schema_version is not None:
            entity.schema_version = data.schema_version
        if "flags" in fields_to_update and data.flags is not None:
            entity.flags = data.flags
        if "compliance" in fields_to_update:
            entity.compliance = data.compliance

        entity.revision += 1
        await session.flush()
        await session.refresh(entity)
        return ProfileService._as_read_model(entity)

    @staticmethod
    async def soft_delete(session: AsyncSession, profile_id: int) -> bool:
        stmt = select(Profile).where(Profile.id == profile_id, Profile.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return False
        from sqlalchemy import func as sa_func

        entity.deleted_at = sa_func.now()
        await session.flush()
        return True

    @staticmethod
    async def restore(session: AsyncSession, profile_id: int) -> ProfileRead | None:
        stmt = select(Profile).where(Profile.id == profile_id, Profile.deleted_at.is_not(None))
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return None
        entity.deleted_at = None
        await session.flush()
        await session.refresh(entity)
        return ProfileService._as_read_model(entity)

    @staticmethod
    async def hard_delete(session: AsyncSession, profile_id: int) -> bool:
        stmt = delete(Profile).where(Profile.id == profile_id)
        result = await session.execute(stmt)
        await session.flush()
        delete_result = cast(CursorResult[Any], result)
        return bool(delete_result.rowcount)

    @staticmethod
    async def hard_delete_all(session: AsyncSession) -> int:
        result = await session.execute(delete(Profile))
        await session.flush()
        delete_result = cast(CursorResult[Any], result)
        return int(delete_result.rowcount or 0)
