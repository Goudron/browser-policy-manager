# app/services/profile_service.py
from __future__ import annotations

import builtins
import hashlib
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import and_, asc, case, delete, desc, func, select, true, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.compliance.firefox.profile_duplicate_composition import (
    DuplicatePlanningResult,
    DuplicatePlanningSource,
    plan_profile_duplicate,
)
from app.compliance.firefox.profile_initialization_composition import (
    InitializationCompositionResult,
    compose_profile_initialization,
)
from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.core.profile_baseline_provenance import (
    downgrade_verified_cis_to_manual_review,
    firefox_import_baseline_provenance,
    generic_create_baseline_provenance,
)
from app.core.profile_certificate_provenance import (
    converted_certificate_provenance,
    imported_certificate_provenance,
    manual_certificate_provenance,
    reconcile_certificate_provenance,
)
from app.core.profile_conversion_json import canonical_json, strict_json_copy
from app.core.profile_conversion_planner import (
    ComplianceReplanner,
    ConversionPlanningContext,
    ConversionPlanningError,
    plan_profile_conversion,
)
from app.core.profile_extension_provenance import (
    converted_extension_provenance,
    imported_extension_provenance,
    manual_extension_provenance,
    reconcile_extension_provenance,
)
from app.core.profile_recommendation import profile_conversion_recommendation
from app.core.schema_channels import require_supported_schema_channel
from app.models.profile import Profile
from app.schemas.profile import (
    ConversionApplyRequest,
    DuplicateProfilePreparationRequest,
    NewProfilePreparationRequest,
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


class NewProfilePreparationFailure(ValueError):
    """A stable, value-free terminal failure for M3-04 preparation."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class DuplicateProfilePreparationFailure(ValueError):
    """A stable, value-free terminal failure for M3-05 preparation."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


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
        # SQLAlchemy Python-side defaults are populated on INSERT, while a
        # focused read model can also be built from a pre-flush legacy object.
        # Treat a missing record as historical imported value attribution; do
        # not inspect flags to invent starter/CIS baseline provenance.
        if not isinstance(profile.extension_provenance, dict):
            profile.extension_provenance = imported_extension_provenance(profile.flags)
        if not isinstance(profile.certificate_provenance, dict):
            profile.certificate_provenance = imported_certificate_provenance(profile.flags)
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
    async def plan_duplicate(
        session: AsyncSession,
        profile_id: int,
        *,
        expected_source_revision: int,
        target_schema_id: str,
        preset_id: str,
        cis_baseline_id: str,
    ) -> DuplicatePlanningResult | None:
        """Read and plan one duplicate without assigning, flushing, or writing.

        This is intentionally an internal M3-03 service boundary, not a
        preparation API.  It takes only server-loaded source fields, copies
        them into the pure planner, and uses ``no_autoflush`` so a future
        caller's pending state cannot turn this read into a write boundary.
        M3-05 must re-read/replan inside its own transaction before inserting.
        """

        with session.no_autoflush:
            result = await session.scalars(select(Profile).where(Profile.id == profile_id))
            profile = result.first()
        if profile is None:
            return None

        source = ProfileService._duplicate_planning_source(profile)
        return plan_profile_duplicate(
            source,
            expected_source_revision=expected_source_revision,
            target_schema_id=target_schema_id,
            preset_id=preset_id,
            cis_baseline_id=cis_baseline_id,
        )

    @staticmethod
    def _duplicate_planning_source(profile: Profile) -> DuplicatePlanningSource:
        """Copy the complete persisted source facts for the pure planner."""

        return DuplicatePlanningSource(
            profile_id=profile.id,
            revision=profile.revision,
            lifecycle_state="active" if profile.deleted_at is None else "deleted",
            schema_artifact_id=profile.schema_version,
            flags=profile.flags,
            compliance=profile.compliance,
            baseline_provenance=profile.baseline_provenance,
            extension_provenance=profile.extension_provenance,
            certificate_provenance=profile.certificate_provenance,
            metadata={
                "name": profile.name,
                "description": profile.description,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "deleted_at": (
                    profile.deleted_at.isoformat() if profile.deleted_at is not None else None
                ),
            },
        )

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
        candidate_extension_provenance = converted_extension_provenance(candidate_policies)
        candidate_certificate_provenance = converted_certificate_provenance(candidate_policies)

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
                extension_provenance=candidate_extension_provenance,
                certificate_provenance=candidate_certificate_provenance,
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
        """Create a generic caller-composed profile with non-inferential provenance."""
        return await ProfileService._create_with_baseline(
            session,
            data,
            baseline_provenance=generic_create_baseline_provenance(),
        )

    @staticmethod
    async def create_prepared_new_profile(
        session: AsyncSession,
        request: NewProfilePreparationRequest,
    ) -> ProfileRead:
        """Insert one fully server-derived new profile without committing.

        The API owns the transaction so it can roll back a catalog/composition,
        database, or serialization failure as one operation.  This method
        accepts catalog identities only and deliberately does not delegate to
        generic ``create``.
        """

        fingerprint = ProfileService._new_preparation_fingerprint(request)
        existing = await ProfileService._prepared_new_replay(
            session,
            idempotency_key=request.preparation_idempotency_key,
            fingerprint=fingerprint,
        )
        if existing is not None:
            return existing

        composition = compose_profile_initialization(
            schema_id=request.target_schema_id,
            preset_id=request.starter_id,
            cis_baseline_id=request.cis_baseline_id,
        )
        if not composition.is_valid:
            raise NewProfilePreparationFailure(
                ProfileService._new_profile_preparation_failure_code(composition)
            )

        document = composition.document
        compliance = composition.compliance
        provenance = composition.baseline_provenance
        extension_provenance = composition.extension_provenance
        certificate_provenance = composition.certificate_provenance
        if (
            not isinstance(document, dict)
            or (compliance is not None and not isinstance(compliance, dict))
            or not isinstance(provenance, dict)
            or not isinstance(extension_provenance, dict)
            or not isinstance(certificate_provenance, dict)
        ):
            # A valid composer result is a persistence invariant.  Treat a
            # violation as a terminal candidate failure before adding a row.
            raise NewProfilePreparationFailure("preparation_candidate_invalid")

        entity = Profile(
            name=request.name,
            schema_version=request.target_schema_id,
            flags=document,
            compliance=compliance,
            baseline_provenance=provenance,
            extension_provenance=extension_provenance,
            certificate_provenance=certificate_provenance,
            preparation_idempotency_key=request.preparation_idempotency_key,
            preparation_request_fingerprint=fingerprint,
        )
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return ProfileService._as_read_model(entity)

    @staticmethod
    async def reconcile_prepared_new_profile(
        session: AsyncSession,
        request: NewProfilePreparationRequest,
    ) -> ProfileRead | None:
        """Return a committed exact replay after a key-uniqueness race."""

        return await ProfileService._prepared_new_replay(
            session,
            idempotency_key=request.preparation_idempotency_key,
            fingerprint=ProfileService._new_preparation_fingerprint(request),
        )

    @staticmethod
    async def create_prepared_duplicate_profile(
        session: AsyncSession,
        request: DuplicateProfilePreparationRequest,
    ) -> ProfileRead:
        """Create or reconcile one duplicate within the caller's transaction.

        A successful first attempt locks the source where the engine supports
        row locks, copies its current database facts into the pure duplicate
        planner, and inserts only the fully rederived candidate.  No source
        attribute is assigned anywhere in this command.  A replay identified
        by the opaque key is deliberately resolved before source validation:
        this is how a client reconciles a response lost after commit without
        turning a later source edit into a second duplicate attempt.
        """

        fingerprint = ProfileService._duplicate_preparation_fingerprint(request)
        existing = await ProfileService._prepared_duplicate_replay(
            session,
            idempotency_key=request.preparation_idempotency_key,
            fingerprint=fingerprint,
        )
        if existing is not None:
            return existing

        source_query = select(Profile).where(Profile.id == request.source_id)
        if session.get_bind().dialect.name != "sqlite":
            source_query = source_query.with_for_update()
        source_result = await session.scalars(source_query)
        source = source_result.one_or_none()
        if source is None:
            raise DuplicateProfilePreparationFailure("preparation_duplicate_source_not_found")

        duplicate_plan = plan_profile_duplicate(
            ProfileService._duplicate_planning_source(source),
            expected_source_revision=request.expected_source_revision,
            target_schema_id=request.target_schema_id,
            preset_id=request.starter_id,
            cis_baseline_id=request.cis_baseline_id,
        )
        if not duplicate_plan.is_valid:
            raise DuplicateProfilePreparationFailure(
                ProfileService._duplicate_preparation_failure_code(duplicate_plan)
            )

        document = duplicate_plan.candidate_document
        compliance = duplicate_plan.candidate_compliance
        provenance = duplicate_plan.candidate_baseline_provenance
        extension_provenance = duplicate_plan.candidate_extension_provenance
        certificate_provenance = duplicate_plan.candidate_certificate_provenance
        target_artifact_id = ProfileService._duplicate_target_artifact_id(
            duplicate_plan,
            request=request,
        )
        if (
            not isinstance(document, dict)
            or (compliance is not None and not isinstance(compliance, dict))
            or not isinstance(provenance, dict)
            or not isinstance(extension_provenance, dict)
            or not isinstance(certificate_provenance, dict)
            or target_artifact_id is None
        ):
            raise DuplicateProfilePreparationFailure("preparation_candidate_invalid")
        if not ProfileService._duplicate_result_matches_rederived_digest(
            duplicate_plan,
            document=document,
            compliance=compliance,
            provenance=provenance,
            extension_provenance=extension_provenance,
            certificate_provenance=certificate_provenance,
        ):
            raise DuplicateProfilePreparationFailure("preparation_candidate_invalid")

        entity = Profile(
            name=request.name,
            schema_version=target_artifact_id,
            flags=document,
            compliance=compliance,
            baseline_provenance=provenance,
            extension_provenance=extension_provenance,
            certificate_provenance=certificate_provenance,
            preparation_idempotency_key=request.preparation_idempotency_key,
            preparation_request_fingerprint=fingerprint,
        )
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return ProfileService._as_read_model(entity)

    @staticmethod
    async def reconcile_prepared_duplicate_profile(
        session: AsyncSession,
        request: DuplicateProfilePreparationRequest,
    ) -> ProfileRead | None:
        """Return a committed exact replay after a key-uniqueness race."""

        return await ProfileService._prepared_duplicate_replay(
            session,
            idempotency_key=request.preparation_idempotency_key,
            fingerprint=ProfileService._duplicate_preparation_fingerprint(request),
        )

    @staticmethod
    async def _prepared_duplicate_replay(
        session: AsyncSession,
        *,
        idempotency_key: str,
        fingerprint: str,
    ) -> ProfileRead | None:
        existing_result = await session.scalars(
            select(Profile).where(Profile.preparation_idempotency_key == idempotency_key)
        )
        existing = existing_result.one_or_none()
        if existing is None:
            return None
        if existing.preparation_request_fingerprint != fingerprint:
            raise DuplicateProfilePreparationFailure("preparation_idempotency_key_reused")
        return ProfileService._as_read_model(existing)

    @staticmethod
    async def _prepared_new_replay(
        session: AsyncSession,
        *,
        idempotency_key: str,
        fingerprint: str,
    ) -> ProfileRead | None:
        """Reconcile one successful new-profile preparation without recomposing it."""

        existing_result = await session.scalars(
            select(Profile).where(Profile.preparation_idempotency_key == idempotency_key)
        )
        existing = existing_result.one_or_none()
        if existing is None:
            return None
        if existing.preparation_request_fingerprint != fingerprint:
            raise NewProfilePreparationFailure("preparation_idempotency_key_reused")
        return ProfileService._as_read_model(existing)

    @staticmethod
    def _new_preparation_fingerprint(request: NewProfilePreparationRequest) -> str:
        """Bind one new-profile retry to its exact value-safe command identity."""

        request_identity = {
            "mode": "create",
            "name": request.name,
            "target_schema_id": request.target_schema_id,
            "starter_id": request.starter_id,
            "cis_baseline_id": request.cis_baseline_id,
        }
        return hashlib.sha256(
            b"bpm096-profile-new-preparation-request:v1\n"
            + canonical_json(strict_json_copy(request_identity))
        ).hexdigest()

    @staticmethod
    def _duplicate_preparation_fingerprint(
        request: DuplicateProfilePreparationRequest,
    ) -> str:
        """Hash the complete caller command without accepting any policy values."""

        request_identity = {
            "mode": "duplicate",
            "name": request.name,
            "target_schema_id": request.target_schema_id,
            "starter_id": request.starter_id,
            "cis_baseline_id": request.cis_baseline_id,
            "source_id": request.source_id,
            "expected_source_revision": request.expected_source_revision,
        }
        return hashlib.sha256(
            b"bpm096-profile-duplicate-preparation-request:v1\n"
            + canonical_json(strict_json_copy(request_identity))
        ).hexdigest()

    @staticmethod
    def _duplicate_target_artifact_id(
        duplicate_plan: DuplicatePlanningResult,
        *,
        request: DuplicateProfilePreparationRequest,
    ) -> str | None:
        """Reject any planner result whose target identity drifted before insert."""

        plan = duplicate_plan.plan
        source = plan.get("source")
        target = plan.get("target")
        result = plan.get("result")
        if (
            not isinstance(source, dict)
            or not isinstance(target, dict)
            or not isinstance(result, dict)
        ):
            return None
        if source.get("profile_id") != request.source_id:
            return None
        if source.get("revision") != request.expected_source_revision:
            return None
        artifact = target.get("artifact")
        artifact_id = artifact.get("artifact_id") if isinstance(artifact, dict) else None
        if artifact_id != request.target_schema_id or not isinstance(artifact_id, str):
            return None
        if not isinstance(result.get("result_digest"), str):
            return None
        return artifact_id

    @staticmethod
    def _duplicate_result_matches_rederived_digest(
        duplicate_plan: DuplicatePlanningResult,
        *,
        document: dict[str, Any],
        compliance: dict[str, Any] | None,
        provenance: dict[str, Any],
        extension_provenance: dict[str, Any],
        certificate_provenance: dict[str, Any],
    ) -> bool:
        """Verify the candidate remains bound to the planner's result digest."""

        plan = duplicate_plan.plan
        result = plan.get("result")
        validation = plan.get("validation")
        if not isinstance(result, dict) or not isinstance(validation, dict):
            return False
        planned_digest = result.get("result_digest")
        if not isinstance(planned_digest, str):
            return False
        try:
            rederived_digest = hashlib.sha256(
                b"bpm096-profile-duplicate-result:v1\n"
                + canonical_json(
                    strict_json_copy(
                        {
                            "document": document,
                            "compliance": compliance,
                            "baseline_provenance": provenance,
                            "extension_provenance": extension_provenance,
                            "certificate_provenance": certificate_provenance,
                            "validation": validation,
                        }
                    )
                )
            ).hexdigest()
        except TypeError, ValueError:
            return False
        return rederived_digest == planned_digest

    @staticmethod
    def _duplicate_preparation_failure_code(duplicate_plan: DuplicatePlanningResult) -> str:
        """Map private planner reasons to the M2-03 terminal preparation vocabulary."""

        reason = duplicate_plan.reason_code or ""
        if reason == "duplicate_source_stale":
            return "preparation_source_stale"
        if reason == "duplicate_source_not_active":
            return "preparation_duplicate_source_not_eligible"
        if reason in {
            "duplicate_source_schema_unavailable",
            "duplicate_target_schema_unavailable",
        }:
            return "preparation_schema_unavailable"
        if reason == "duplicate_preset_unavailable":
            return "preparation_starter_unavailable"
        if reason == "duplicate_cis_unavailable":
            return "preparation_cis_unavailable"
        if reason.startswith("duplicate_conversion"):
            return "preparation_conversion_blocked"
        return "preparation_composition_blocked"

    @staticmethod
    def _new_profile_preparation_failure_code(
        composition: InitializationCompositionResult,
    ) -> str:
        """Collapse catalog internals to the M2-03 public terminal codes."""

        reason = composition.reason_code or ""
        if reason.startswith("initialization_schema_"):
            return "preparation_schema_unavailable"
        if reason.startswith("initialization_preset_"):
            return "preparation_starter_unavailable"
        if reason.startswith("initialization_cis_") or reason.startswith("cis_"):
            return "preparation_cis_unavailable"
        return "preparation_candidate_invalid"

    @staticmethod
    async def create_firefox_import(
        session: AsyncSession,
        data: ProfileCreate,
    ) -> ProfileRead:
        """Create a Firefox import without treating supplied compliance as CIS proof."""
        return await ProfileService._create_with_baseline(
            session,
            data,
            baseline_provenance=firefox_import_baseline_provenance(),
            extension_provenance=imported_extension_provenance(data.flags),
            certificate_provenance=imported_certificate_provenance(data.flags),
        )

    @staticmethod
    async def _create_with_baseline(
        session: AsyncSession,
        data: ProfileCreate,
        *,
        baseline_provenance: dict[str, Any],
        extension_provenance: dict[str, Any] | None = None,
        certificate_provenance: dict[str, Any] | None = None,
    ) -> ProfileRead:
        require_supported_schema_channel(data.schema_version)
        entity = Profile(
            name=data.name,
            description=data.description,
            schema_version=data.schema_version,
            flags=data.flags,
            compliance=data.compliance,
            baseline_provenance=baseline_provenance,
            extension_provenance=(
                extension_provenance
                if extension_provenance is not None
                else manual_extension_provenance(data.flags)
            ),
            certificate_provenance=(
                certificate_provenance
                if certificate_provenance is not None
                else manual_certificate_provenance(data.flags)
            ),
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
            entity.extension_provenance = reconcile_extension_provenance(
                entity.flags,
                entity.extension_provenance,
                data.flags,
                data.extension_provenance,
            )
            entity.certificate_provenance = reconcile_certificate_provenance(
                entity.flags,
                entity.certificate_provenance,
                data.flags,
                data.certificate_provenance,
            )
            entity.flags = data.flags
        if "compliance" in fields_to_update:
            entity.compliance = data.compliance

        if {"flags", "compliance"} & fields_to_update:
            downgraded = downgrade_verified_cis_to_manual_review(entity.baseline_provenance)
            if downgraded is not None:
                entity.baseline_provenance = downgraded

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
