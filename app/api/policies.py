from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas.policy import PolicyCreate, PolicyOut, PolicyUpdate
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=List[PolicyOut])
async def list_policies(session: AsyncSession = Depends(get_session)):
    items = await PolicyService.list(session)
    return [PolicyOut.model_validate(i) for i in items]


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(policy_id: int, session: AsyncSession = Depends(get_session)):
    entity = await PolicyService.get(session, policy_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return PolicyOut.model_validate(entity)


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreate, session: AsyncSession = Depends(get_session)
):
    entity = await PolicyService.create(session, data)
    await session.commit()
    return PolicyOut.model_validate(entity)


@router.patch("/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: int, data: PolicyUpdate, session: AsyncSession = Depends(get_session)
):
    entity = await PolicyService.update(session, policy_id, data)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    await session.commit()
    return PolicyOut.model_validate(entity)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: int, session: AsyncSession = Depends(get_session)):
    ok = await PolicyService.delete(session, policy_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    await session.commit()
    return None
