from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.db import get_session
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def _validate_profile_policies_or_422(
    *,
    name: str,
    schema_version: str,
    flags: dict[str, Any] | None,
) -> None:
    """
    Validate profile policies (flags) against internal Firefox schemas.

    `schema_version` corresponds to the channel ("esr‑140", "release‑145"),
    `flags` is interpreted as a dict policy_id -> value.
    """
    if not flags:
        return

    payload = {
        "name": name,
        "channel": schema_version,
        "policies": flags,
    }

    try:
        validate_profile_payload_with_schema(payload)
    except PolicyValidationError as exc:
        issues_payload = [
            {
                "policy": issue.policy,
                "path": issue.path,
                "message": issue.message,
            }
            for issue in exc.issues
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Policy validation failed",
                "issues": issues_payload,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Profile validation failed",
                "error": str(exc),
            },
        ) from exc


@router.get("", response_model=list[PolicyRead])
async def list_profiles(
    session: AsyncSession = Depends(get_session),
    q: str | None = Query(None, description="Substring filter for profile name/description"),
    owner: str | None = Query(None, description="Filter by owner"),
    schema_version: str | None = Query(None, description="Filter by schema_version (channel)"),
    include_deleted: bool = Query(False, description="Include soft‑deleted profiles"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("updated_at", description="Sort field: created_at/updated_at/name/id"),
    order: str = Query("desc", description="Sort order: asc/desc"),
) -> list[PolicyRead]:
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


@router.get("/{profile_id}", response_model=PolicyRead)
async def get_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    profile = await PolicyService.get(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: PolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    _validate_profile_policies_or_422(
        name=payload.name,
        schema_version=payload.schema_version,
        flags=payload.flags,
    )

    profile = await PolicyService.create(session, payload)
    await session.commit()
    return profile


@router.patch("/{profile_id}", response_model=PolicyRead)
async def update_profile(
    profile_id: int,
    payload: PolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    current = await PolicyService.get(session, profile_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    new_schema_version = payload.schema_version or current.schema_version
    new_flags = payload.flags if payload.flags is not None else current.flags

    _validate_profile_policies_or_422(
        name=current.name,
        schema_version=new_schema_version,
        flags=new_flags,
    )

    updated = await PolicyService.update(session, profile_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    await session.commit()
    return updated


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await PolicyService.soft_delete(session, profile_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    await session.commit()
    return None


@router.post("/{profile_id}/restore", response_model=PolicyRead)
async def restore_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> PolicyRead:
    restored = await PolicyService.restore(session, profile_id)
    if restored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    await session.commit()
    return restored
