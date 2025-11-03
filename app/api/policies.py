"""
Policies API router.

FastAPI-specific patterns (Query/Depends/Body) are intentionally kept in function
signatures; Ruff B008 is suppressed for app/api/*.py in pyproject.toml.

This version aligns imports with the current repository layout:
- app/db.py                       → get_session
- app/services/policy_service.py  → PolicyService
- app/schemas/policy.py           → Pydantic models (PolicyCreate/Update/Read)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.policy import (
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
async def list_policies(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # Use string params with regex validation instead of missing enums (SortField/SortOrder).
    sort: str = Query("updated_at", pattern="^(created_at|updated_at|name|id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
) -> list[PolicyRead]:
    """List policies with pagination and sorting."""
    return await PolicyService.list(
        session=session,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@router.get("/{policy_id}", response_model=PolicyRead)
async def get_policy(
    policy_id: int,
    include_deleted: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    """Retrieve a single policy by id."""
    item = await PolicyService.get(session, policy_id, include_deleted=include_deleted)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    """Create a new policy."""
    try:
        created = await PolicyService.create(session, data)
        return created
    except IntegrityError as err:
        await session.rollback()
        # Chain the original DB error to keep the traceback informative (Ruff B904).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Name already exists",
        ) from err


@router.put("/{policy_id}", response_model=PolicyRead)
async def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    """Update an existing policy by id."""
    updated = await PolicyService.update(session, policy_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return updated


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Soft-delete a policy by id."""
    ok = await PolicyService.soft_delete(session, policy_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/{policy_id}/restore", response_model=PolicyRead)
async def restore_policy(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    """Restore a soft-deleted policy by id."""
    item = await PolicyService.restore(session, policy_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item
