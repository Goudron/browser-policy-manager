from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.db import get_session
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.profile_service import ProfileService

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
    `flags` is interpreted as a mapping of Firefox policy_id -> value.
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


async def _list_profiles_core(
    session: AsyncSession,
    *,
    q: str | None = None,
    owner: str | None = None,
    schema_version: str | None = None,
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
    sort: str = "updated_at",
    order: str = "desc",
    ) -> list[ProfileRead]:
    return await ProfileService.list(
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


async def _profile_library_stats_core(
    session: AsyncSession,
    *,
    q: str | None = None,
    owner: str | None = None,
    schema_version: str | None = None,
    include_deleted: bool = False,
) -> dict[str, int]:
    filtered = await ProfileService.count(
        session,
        q=q,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
    )
    total = await ProfileService.count(
        session,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
    )
    return {
        "filtered": filtered,
        "total": total,
    }


async def _get_profile_or_404_core(
    profile_id: int,
    session: AsyncSession,
    *,
    include_deleted: bool = False,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    return profile


async def _create_profile_core(
    payload: ProfileCreate,
    session: AsyncSession,
    *,
    validate_policies: bool = True,
    conflict_detail: str = "Profile with this name already exists",
) -> ProfileRead:
    if validate_policies:
        _validate_profile_policies_or_422(
            name=payload.name,
            schema_version=payload.schema_version,
            flags=payload.flags,
        )

    try:
        profile = await ProfileService.create(session, payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        ) from exc

    return profile


async def _update_profile_core(
    profile_id: int,
    payload: ProfileUpdate,
    session: AsyncSession,
    *,
    validate_policies: bool = True,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    current = await _get_profile_or_404_core(
        profile_id,
        session,
        not_found_detail=not_found_detail,
    )
    payload_data = payload.model_dump(exclude_unset=True)
    normalized_payload = payload
    if "flags" in payload_data and payload_data["flags"] is not None:
        normalized_payload = ProfileUpdate(
            description=payload.description,
            schema_version=payload.schema_version,
            flags={**current.flags, **payload_data["flags"]},
            owner=payload.owner,
        )

    if validate_policies:
        new_schema_version = normalized_payload.schema_version or current.schema_version
        new_flags = normalized_payload.flags if normalized_payload.flags is not None else current.flags

        _validate_profile_policies_or_422(
            name=current.name,
            schema_version=new_schema_version,
            flags=new_flags,
        )

    updated = await ProfileService.update(session, profile_id, normalized_payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()
    return updated


async def _delete_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> None:
    ok = await ProfileService.soft_delete(session, profile_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()


async def _restore_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    restored = await ProfileService.restore(session, profile_id)
    if restored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()
    return restored


async def _hard_delete_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> None:
    ok = await ProfileService.hard_delete(session, profile_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()


async def _reset_profiles_library_core(session: AsyncSession) -> dict[str, int]:
    deleted = await ProfileService.hard_delete_all(session)
    await session.commit()
    return {"deleted": deleted}


@router.get("", response_model=list[ProfileRead], summary="List profiles")
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
) -> list[ProfileRead]:
    return await _list_profiles_core(
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


@router.get("/stats", summary="Get profile library stats")
async def profile_library_stats(
    session: AsyncSession = Depends(get_session),
    q: str | None = Query(None, description="Substring filter for profile name/description"),
    owner: str | None = Query(None, description="Filter by owner"),
    schema_version: str | None = Query(None, description="Filter by schema_version (channel)"),
    include_deleted: bool = Query(False, description="Include soft-deleted profiles"),
) -> dict[str, int]:
    return await _profile_library_stats_core(
        session,
        q=q,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
    )


@router.delete("/reset", summary="Hard-delete all profiles from the library")
async def reset_profiles_library(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await _reset_profiles_library_core(session)


@router.get("/{profile_id}", response_model=ProfileRead, summary="Get profile")
async def get_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _get_profile_or_404_core(profile_id, session)


@router.post(
    "",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create profile",
)
async def create_profile(
    payload: ProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _create_profile_core(
        payload,
        session,
        validate_policies=True,
    )


@router.patch("/{profile_id}", response_model=ProfileRead, summary="Update profile")
async def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _update_profile_core(
        profile_id,
        payload,
        session,
        validate_policies=True,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete profile")
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _delete_profile_core(profile_id, session)
    return None


@router.delete(
    "/{profile_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard-delete profile",
)
async def hard_delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _hard_delete_profile_core(profile_id, session)
    return None


@router.post("/{profile_id}/restore", response_model=ProfileRead, summary="Restore profile")
async def restore_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _restore_profile_core(profile_id, session)
