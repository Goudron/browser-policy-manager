# app/services/profile_service.py
from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import and_, asc, case, delete, desc, func, select, true, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.core.profile_conversion_planner import (
    ComplianceReplanner,
    ConversionPlanningContext,
    ConversionPlanningError,
    plan_profile_conversion,
)
from app.core.profile_recommendation import profile_conversion_recommendation
from app.core.schema_channels import require_supported_schema_channel
from app.models.profile import Profile
from app.schemas.profile import (
    ConversionApplyRequest,
    ProfileCreate,
    ProfileRead,
    ProfileRecommendation,
    ProfileUpdate,
)

SortField = str  # "created_at" | "updated_at" | "name" | "schema_version" | "id"
SortOrder = str  # "asc" | "desc"


def _profile_recommendation_read_model(profile: Profile) -> ProfileRecommendation | None:
    """Validate the pure catalog projection before exposing the API DTO."""

    recommendation = profile_conversion_recommendation(
        schema_version=profile.schema_version,
        revision=profile.revision,
        is_active=profile.deleted_at is None,
    )
    return ProfileRecommendation.model_validate(recommendation) if recommendation else None


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


class ConversionApplyFailure(ValueError):
    """A value-free apply failure that the HTTP boundary maps to M2-04."""

    def __init__(
        self,
        code: str,
        *,
        current_revision: int | None = None,
        source_artifact_id: str | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.current_revision = current_revision
        self.source_artifact_id = source_artifact_id


class ProfileSchemaChangeRequiresConversion(ValueError):
    """Raised when a generic profile write attempts to change its schema channel."""


@dataclass(frozen=True, slots=True)
class ConversionApplyOutcome:
    """Server-derived evidence for one uncommitted conversion write."""

    plan: dict[str, Any]
    source_revision: int
    result_revision: int
    updated_at_changed: bool


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
                ),
                "recommendation": _profile_recommendation_read_model(profile),
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
    async def get_conversion_preview_source(
        session: AsyncSession,
        profile_id: int,
    ) -> Profile | None:
        """Load one stored profile for M4 conversion planning without a write boundary.

        The preview route deliberately receives the ORM object only through this
        narrow service read.  ``no_autoflush`` prevents a future caller's
        pending state from turning the planning SELECT into an accidental
        persistence boundary; this method itself performs no assignment,
        flush, refresh, commit, or rollback.
        """
        with session.no_autoflush:
            result = await session.scalars(select(Profile).where(Profile.id == profile_id))
            return result.first()

    @staticmethod
    def conversion_planning_context(
        profile: Profile,
        *,
        compliance_replanner: ComplianceReplanner | None = None,
    ) -> ConversionPlanningContext:
        """Build the one digest-bearing context from persisted profile fields.

        Preview and apply must use this exact projection.  In particular,
        ``updated_at`` is included because a normal profile write invalidates a
        preview even if its policy document happens to be unchanged.
        """
        return ConversionPlanningContext(
            profile_id=profile.id,
            revision=profile.revision,
            lifecycle_state="active" if profile.deleted_at is None else "deleted",
            metadata={
                "name": profile.name,
                "description": profile.description,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "deleted_at": (
                    profile.deleted_at.isoformat() if profile.deleted_at is not None else None
                ),
            },
            compliance=profile.compliance,
            compliance_replanner=compliance_replanner,
        )

    @staticmethod
    async def apply_conversion(
        session: AsyncSession,
        profile_id: int,
        request: ConversionApplyRequest,
        *,
        compliance_replanner: ComplianceReplanner | None = None,
    ) -> ConversionApplyOutcome:
        """Replan and conditionally write one current conversion without committing.

        The caller owns the surrounding transaction.  ``FOR UPDATE`` protects
        PostgreSQL's read/replan/write sequence; SQLite deliberately ignores
        that clause, so the API starts its transaction with ``BEGIN IMMEDIATE``
        and this conditional write remains the final cross-dialect guard.
        """
        with session.no_autoflush:
            result = await session.scalars(
                select(Profile).where(Profile.id == profile_id).with_for_update()
            )
            profile = result.first()

        if profile is None:
            raise ConversionApplyFailure("conversion_profile_not_found")
        if request.profile_id != profile_id:
            raise ConversionApplyFailure(
                "conversion_source_identity_stale",
                current_revision=profile.revision,
            )
        if profile.deleted_at is not None:
            raise ConversionApplyFailure(
                "conversion_source_not_active",
                current_revision=profile.revision,
            )
        if profile.revision != request.expected_revision:
            raise ConversionApplyFailure(
                "conversion_revision_stale",
                current_revision=profile.revision,
            )

        try:
            planning = plan_profile_conversion(
                {"policies": profile.flags},
                source_artifact_id=profile.schema_version,
                target_artifact_id=request.target_artifact_id,
                context=ProfileService.conversion_planning_context(
                    profile,
                    compliance_replanner=compliance_replanner,
                ),
            )
        except ConversionPlanningError as exc:
            raise ConversionApplyFailure(
                exc.code,
                current_revision=profile.revision,
                source_artifact_id=profile.schema_version,
            ) from exc

        plan = planning.plan
        ProfileService._assert_conversion_apply_identities(request, plan)

        compatibility = plan["compatibility"]
        target_validation = plan["target_validation"]
        if (
            not isinstance(compatibility, dict)
            or compatibility.get("applicable") is not True
            or not isinstance(target_validation, dict)
            or target_validation.get("status") != "valid"
        ):
            raise ConversionApplyFailure(
                "conversion_plan_blocked",
                current_revision=profile.revision,
            )

        candidate_document = planning.candidate_document
        candidate_policies = candidate_document.get("policies")
        candidate_compliance = planning.candidate_compliance
        if not isinstance(candidate_policies, dict) or (
            candidate_compliance is not None and not isinstance(candidate_compliance, dict)
        ):
            # The pure planner promises this shape for a valid target.  An
            # internal violation must never be converted into a partial write.
            raise RuntimeError("conversion planner returned an invalid persistence candidate")

        before_updated_at = profile.updated_at
        write = (
            update(Profile)
            .where(
                Profile.id == profile_id,
                Profile.revision == request.expected_revision,
                Profile.deleted_at.is_(None),
            )
            .values(
                schema_version=request.target_artifact_id,
                flags=candidate_policies,
                compliance=candidate_compliance,
                revision=request.expected_revision + 1,
            )
            .returning(Profile.revision, Profile.updated_at)
        )
        written = (await session.execute(write)).one_or_none()
        if written is None:
            # A conditional write is required even with a PostgreSQL row lock:
            # it is the portable final proof that no concurrent apply can win
            # twice.  The API transaction rolls this failure back unchanged.
            raise ConversionApplyFailure("conversion_revision_stale")

        result_revision, updated_at = written
        if result_revision != request.expected_revision + 1:
            raise RuntimeError("conversion write did not advance exactly one revision")
        return ConversionApplyOutcome(
            plan=plan,
            source_revision=request.expected_revision,
            result_revision=result_revision,
            updated_at_changed=updated_at != before_updated_at,
        )

    @staticmethod
    def _assert_conversion_apply_identities(
        request: ConversionApplyRequest,
        plan: dict[str, Any],
    ) -> None:
        """Fail closed unless the current plan is the exact confirmed preview."""
        profile = plan.get("profile")
        source = plan.get("source")
        target = plan.get("target")
        registry = plan.get("recipe_registry")
        if not all(isinstance(value, dict) for value in (profile, source, target, registry)):
            raise RuntimeError("conversion planner returned an invalid identity projection")
        assert isinstance(profile, dict)
        assert isinstance(source, dict)
        assert isinstance(target, dict)
        assert isinstance(registry, dict)

        source_artifact = source.get("artifact")
        target_artifact = target.get("artifact")
        if not isinstance(source_artifact, dict) or not isinstance(target_artifact, dict):
            raise RuntimeError("conversion planner returned an invalid artifact identity")

        if (
            request.source.line_id != source_artifact.get("line_id")
            or request.source.artifact_id != source_artifact.get("artifact_id")
            or request.target.line_id != target_artifact.get("line_id")
            or request.target.artifact_id != target_artifact.get("artifact_id")
            or request.target_artifact_id != request.target.artifact_id
            or request.source_validation_schema_sha256
            != source_artifact.get("validation_schema_sha256")
            or request.target_validation_schema_sha256
            != target_artifact.get("validation_schema_sha256")
        ):
            raise ConversionApplyFailure("conversion_schema_identity_stale")

        if (
            request.source_document_digest != source.get("document_digest")
            or request.source_compliance_digest != source.get("compliance_digest")
            or request.source_metadata_digest != profile.get("metadata_digest")
        ):
            raise ConversionApplyFailure("conversion_source_identity_stale")

        if request.recipe_registry_version != registry.get(
            "registry_version"
        ) or request.recipe_registry_digest != registry.get("registry_digest"):
            raise ConversionApplyFailure("conversion_recipe_registry_stale")
        if request.plan_digest != plan.get("plan_digest"):
            raise ConversionApplyFailure("conversion_plan_stale")

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
        require_supported_schema_channel(data.schema_version)
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
            require_supported_schema_channel(data.schema_version)
            if data.schema_version != entity.schema_version:
                raise ProfileSchemaChangeRequiresConversion("profile_schema_conversion_required")
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
