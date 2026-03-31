# app/services/profile_service.py
from __future__ import annotations

import builtins

from sqlalchemy import asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

SortField = str  # "created_at" | "updated_at" | "name" | "id"
SortOrder = str  # "asc" | "desc"


class ProfileService:
    """Business logic for profile CRUD, with soft delete and filtering."""

    # --- helpers ---

    @staticmethod
    def _sort_clause(field: SortField, order: SortOrder) -> ColumnElement:
        field_map = {
            "created_at": Profile.created_at,
            "updated_at": Profile.updated_at,
            "name": Profile.name,
            "id": Profile.id,
        }
        col = field_map.get(field, Profile.updated_at)
        return asc(col) if order == "asc" else desc(col)

    # --- CRUD ---

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        q: str | None = None,
        owner: str | None = None,
        schema_version: str | None = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
    ) -> builtins.list[ProfileRead]:
        stmt = select(Profile)

        if not include_deleted:
            stmt = stmt.where(Profile.deleted_at.is_(None))

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where((Profile.name.ilike(like)) | (Profile.description.ilike(like)))

        if owner:
            stmt = stmt.where(Profile.owner == owner)

        if schema_version:
            stmt = stmt.where(Profile.schema_version == schema_version)

        stmt = stmt.order_by(ProfileService._sort_clause(sort, order)).limit(limit).offset(offset)
        res = await session.scalars(stmt)
        items = list(res)
        return [ProfileRead.model_validate(x) for x in items]

    @staticmethod
    async def get(
        session: AsyncSession, profile_id: int, include_deleted: bool = False
    ) -> ProfileRead | None:
        stmt = select(Profile).where(Profile.id == profile_id)
        if not include_deleted:
            stmt = stmt.where(Profile.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        return ProfileRead.model_validate(entity) if entity else None

    @staticmethod
    async def count(
        session: AsyncSession,
        *,
        q: str | None = None,
        owner: str | None = None,
        schema_version: str | None = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(Profile)

        if not include_deleted:
            stmt = stmt.where(Profile.deleted_at.is_(None))

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where((Profile.name.ilike(like)) | (Profile.description.ilike(like)))

        if owner:
            stmt = stmt.where(Profile.owner == owner)

        if schema_version:
            stmt = stmt.where(Profile.schema_version == schema_version)

        return int(await session.scalar(stmt) or 0)

    @staticmethod
    async def create(session: AsyncSession, data: ProfileCreate) -> ProfileRead:
        entity = Profile(
            name=data.name,
            description=data.description,
            schema_version=data.schema_version,
            flags=data.flags,
            owner=data.owner,
        )
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return ProfileRead.model_validate(entity)

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
        if "owner" in fields_to_update:
            entity.owner = data.owner

        await session.flush()
        await session.refresh(entity)
        return ProfileRead.model_validate(entity)

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
        return ProfileRead.model_validate(entity)

    @staticmethod
    async def hard_delete(session: AsyncSession, profile_id: int) -> bool:
        stmt = delete(Profile).where(Profile.id == profile_id)
        result = await session.execute(stmt)
        await session.flush()
        return bool(result.rowcount)

    @staticmethod
    async def hard_delete_all(session: AsyncSession) -> int:
        result = await session.execute(delete(Profile))
        await session.flush()
        return int(result.rowcount or 0)
