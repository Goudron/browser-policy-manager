# app/api/policies.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/api", tags=["policies"])


@router.post("/policies", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    try:
        created = await PolicyService.create(session, payload)
        await session.commit()  # <-- make visible for next requests
        return created
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Policy with this name already exists"
        )


@router.get("/policies", response_model=List[PolicyRead])
async def list_policies(session: AsyncSession = Depends(get_session)) -> List[PolicyRead]:
    return await PolicyService.list_all(session)


@router.get("/policies/{policy_id}", response_model=PolicyRead)
async def get_policy(policy_id: int, session: AsyncSession = Depends(get_session)) -> PolicyRead:
    entity = await PolicyService.get(session, policy_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return PolicyRead.model_validate(entity)


@router.patch("/policies/{policy_id}", response_model=PolicyRead)
async def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    updated = await PolicyService.update(session, policy_id, payload)
    if not updated:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()  # <-- persist changes
    return updated


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await PolicyService.delete(session, policy_id)
    if not ok:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()  # <-- persist deletion
    return
