from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas.policy import PolicyCreate, PolicyOut, PolicyUpdate
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate, session: AsyncSession = Depends(get_session)
) -> PolicyOut:
    """
    Create a policy. Returns 201 on success.
    If name is not unique, return 409 Conflict.
    """
    try:
        entity = await PolicyService.create(session, payload)
        await session.commit()
        return PolicyOut.model_validate(entity)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy with the same name already exists",
        )


@router.get("", response_model=List[PolicyOut])
async def list_policies(session: AsyncSession = Depends(get_session)) -> List[PolicyOut]:
    items = await PolicyService.list(session)
    return [PolicyOut.model_validate(i) for i in items]


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(policy_id: int, session: AsyncSession = Depends(get_session)) -> PolicyOut:
    entity = await PolicyService.get(session, policy_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return PolicyOut.model_validate(entity)


@router.patch("/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: int, payload: PolicyUpdate, session: AsyncSession = Depends(get_session)
) -> PolicyOut:
    entity = await PolicyService.update(session, policy_id, payload)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()
    return PolicyOut.model_validate(entity)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: int, session: AsyncSession = Depends(get_session)) -> None:
    ok = await PolicyService.delete(session, policy_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()
    return None
