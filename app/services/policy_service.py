# app/services/policy_service.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate


class PolicyService:
    """Business logic for Policy CRUD."""

    @staticmethod
    async def list_all(session: AsyncSession) -> List[PolicyRead]:
        result = await session.execute(select(Policy).order_by(Policy.id.asc()))
        items = result.scalars().all()
        return [PolicyRead.model_validate(x) for x in items]

    @staticmethod
    async def get(session: AsyncSession, policy_id: int) -> Optional[Policy]:
        result = await session.execute(select(Policy).where(Policy.id == policy_id).limit(1))
        return result.scalar_one_or_none()

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
        try:
            await session.flush()
        except IntegrityError as e:
            await session.rollback()
            raise e
        await session.refresh(entity)
        return PolicyRead.model_validate(entity)

    @staticmethod
    async def update(
        session: AsyncSession, policy_id: int, data: PolicyUpdate
    ) -> Optional[PolicyRead]:
        entity = await PolicyService.get(session, policy_id)
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
    async def delete(session: AsyncSession, policy_id: int) -> bool:
        entity = await PolicyService.get(session, policy_id)
        if not entity:
            return False
        await session.delete(entity)
        return True
