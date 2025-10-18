from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.policy import Policy
from ..schemas.policy import PolicyCreate, PolicyUpdate


class PolicyService:
    """Business logic for policy CRUD operations."""

    @staticmethod
    async def list(session: AsyncSession) -> List[Policy]:
        res = await session.execute(select(Policy).order_by(Policy.id))
        return list(res.scalars())

    @staticmethod
    async def get(session: AsyncSession, policy_id: int) -> Optional[Policy]:
        return await session.get(Policy, policy_id)

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[Policy]:
        res = await session.execute(select(Policy).where(Policy.name == name))
        return res.scalars().first()

    @staticmethod
    async def create(session: AsyncSession, data: PolicyCreate) -> Policy:
        """
        Create a policy; уникальность имени обеспечивает БД.
        IntegrityError пробрасываем наверх (API вернёт 409).
        """
        entity = Policy(**data.model_dump())
        session.add(entity)
        try:
            await session.flush()
            await session.refresh(entity)
            return entity
        except IntegrityError:
            await session.rollback()
            raise

    @staticmethod
    async def update(session: AsyncSession, policy_id: int, data: PolicyUpdate) -> Optional[Policy]:
        entity = await session.get(Policy, policy_id)
        if not entity:
            return None
        payload = data.model_dump(exclude_unset=True)
        if "description" in payload:
            entity.description = payload["description"]
        if "schema_version" in payload and payload["schema_version"] is not None:
            entity.schema_version = payload["schema_version"]
        if "flags" in payload and payload["flags"] is not None:
            entity.flags = payload["flags"]
        entity.touch()
        await session.flush()
        await session.refresh(entity)
        return entity

    @staticmethod
    async def delete(session: AsyncSession, policy_id: int) -> bool:
        """Удаление через ORM (типобезопасно для mypy)."""
        entity = await session.get(Policy, policy_id)
        if entity is None:
            return False
        await session.delete(entity)
        return True
