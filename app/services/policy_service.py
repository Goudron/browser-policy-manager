# app/services/policy_service.py
from __future__ import annotations

import builtins

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate

SortField = str  # "created_at" | "updated_at" | "name" | "id"
SortOrder = str  # "asc" | "desc"


class PolicyService:
    """Business logic for Policy CRUD, with soft delete and filtering."""

    # --- helpers ---

    @staticmethod
    def _sort_clause(field: SortField, order: SortOrder) -> ColumnElement:
        field_map = {
            "created_at": Policy.created_at,
            "updated_at": Policy.updated_at,
            "name": Policy.name,
            "id": Policy.id,
        }
        col = field_map.get(field, Policy.updated_at)
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
    ) -> builtins.list[PolicyRead]:
        stmt = select(Policy)

        if not include_deleted:
            stmt = stmt.where(Policy.deleted_at.is_(None))

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                (Policy.name.ilike(like)) | (Policy.description.ilike(like))
            )

        if owner:
            stmt = stmt.where(Policy.owner == owner)

        if schema_version:
            stmt = stmt.where(Policy.schema_version == schema_version)

        stmt = (
            stmt.order_by(PolicyService._sort_clause(sort, order))
            .limit(limit)
            .offset(offset)
        )
        res = await session.scalars(stmt)
        items = list(res)
        return [PolicyRead.model_validate(x) for x in items]

    @staticmethod
    async def get(
        session: AsyncSession, policy_id: int, include_deleted: bool = False
    ) -> PolicyRead | None:
        stmt = select(Policy).where(Policy.id == policy_id)
        if not include_deleted:
            stmt = stmt.where(Policy.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        return PolicyRead.model_validate(entity) if entity else None

    @staticmethod
    async def create(session: AsyncSession, data: PolicyCreate) -> PolicyRead:
        entity = Policy(
            name=data.name,
            description=data.description,
            schema_version=data.schema_version,
            flags=data.flags,
            owner=data.owner,
        )
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return PolicyRead.model_validate(entity)

    @staticmethod
    async def update(
        session: AsyncSession, policy_id: int, data: PolicyUpdate
    ) -> PolicyRead | None:
        stmt = select(Policy).where(Policy.id == policy_id, Policy.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return None

        if data.description is not None:
            entity.description = data.description
        if data.schema_version is not None:
            entity.schema_version = data.schema_version
        if data.flags is not None:
            entity.flags = data.flags
        if data.owner is not None:
            entity.owner = data.owner

        await session.flush()
        await session.refresh(entity)
        return PolicyRead.model_validate(entity)

    @staticmethod
    async def soft_delete(session: AsyncSession, policy_id: int) -> bool:
        stmt = select(Policy).where(Policy.id == policy_id, Policy.deleted_at.is_(None))
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return False
        from sqlalchemy import func as sa_func

        entity.deleted_at = sa_func.now()
        await session.flush()
        return True

    @staticmethod
    async def restore(session: AsyncSession, policy_id: int) -> PolicyRead | None:
        stmt = select(Policy).where(
            Policy.id == policy_id, Policy.deleted_at.is_not(None)
        )
        res = await session.scalars(stmt)
        entity = res.first()
        if not entity:
            return None
        entity.deleted_at = None
        await session.flush()
        await session.refresh(entity)
        return PolicyRead.model_validate(entity)
