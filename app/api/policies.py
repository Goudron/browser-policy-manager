# app/api/policies.py
# Policies CRUD API with soft delete, filtering, sorting, and OpenAPI examples.

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/api", tags=["policies"])

SortField = Literal["created_at", "updated_at", "name", "id"]
SortOrder = Literal["asc", "desc"]


@router.get(
    "/policies",
    response_model=List[PolicyRead],
    summary="List policies",
    description=(
        "List policies with filters, soft-delete visibility and sorting.\n\n"
        "- By default, soft-deleted items are hidden (`include_deleted=false`).\n"
        "- Sorting supports: `created_at`, `updated_at`, `name`, `id`.\n"
    ),
    responses={
        200: {
            "description": "Array of policies",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Default",
                            "description": "Base profile",
                            "schema_version": "esr-140",
                            "flags": {"DisableTelemetry": True},
                            "owner": "admin@example.org",
                            "created_at": "2025-10-01T12:30:00+00:00",
                            "updated_at": "2025-10-02T08:00:00+00:00",
                            "deleted_at": None,
                            "is_deleted": False,
                        }
                    ]
                }
            },
        }
    },
)
async def list_policies(
    q: Optional[str] = Query(None, description="Search by name/description (ILIKE)"),
    owner: Optional[str] = Query(None),
    schema_version: Optional[str] = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: SortField = Query("updated_at"),
    order: SortOrder = Query("desc"),
    session: AsyncSession = Depends(get_session),
) -> List[PolicyRead]:
    return await PolicyService.list(
        session,
        q=q,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyRead,
    summary="Get policy by ID",
    responses={
        200: {"description": "Policy found"},
        404: {"description": "Not found"},
    },
)
async def get_policy(
    policy_id: int,
    include_deleted: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    item = await PolicyService.get(session, policy_id, include_deleted=include_deleted)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.post(
    "/policies",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create policy",
    responses={
        201: {
            "description": "Created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "New Profile",
                        "description": "Created via UI",
                        "schema_version": "release-144",
                        "flags": {},
                        "owner": "admin@example.org",
                        "created_at": "2025-10-21T10:00:00+00:00",
                        "updated_at": "2025-10-21T10:00:00+00:00",
                        "deleted_at": None,
                        "is_deleted": False,
                    }
                }
            },
        },
        409: {"description": "Name already exists"},
    },
)
async def create_policy(
    data: PolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    try:
        created = await PolicyService.create(session, data)
        await session.commit()
        return created
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Name already exists")


@router.patch(
    "/policies/{policy_id}",
    response_model=PolicyRead,
    summary="Update policy",
    responses={
        200: {"description": "Updated"},
        404: {"description": "Not found"},
    },
)
async def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    updated = await PolicyService.update(session, policy_id, data)
    if not updated:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()
    return updated


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete policy",
    responses={
        204: {"description": "Soft-deleted"},
        404: {"description": "Not found"},
    },
)
async def delete_policy(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await PolicyService.soft_delete(session, policy_id)
    if not ok:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.commit()
    return


@router.post(
    "/policies/{policy_id}/restore",
    response_model=PolicyRead,
    summary="Restore soft-deleted policy",
    responses={
        200: {"description": "Restored"},
        404: {"description": "Not found or not deleted"},
    },
)
async def restore_policy(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    item = await PolicyService.restore(session, policy_id)
    if not item:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found or not deleted"
        )
    await session.commit()
    return item
