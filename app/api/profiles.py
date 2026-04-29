from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.core.schema_channels import DEFAULT_SCHEMA_CHANNEL
from app.db import get_session
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.firefox_policy_import import (
    FirefoxPoliciesDocumentValidationError,
    FirefoxPoliciesImportError,
    validate_firefox_policies_document,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE: dict[str, Any] = {
    "name": "Workstation baseline",
    "description": "Imported from Firefox policies.json",
    "schema_version": DEFAULT_SCHEMA_CHANNEL,
    "document": {
        "policies": {
            "DisableTelemetry": True,
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": True,
                    "Status": "locked",
                }
            },
        }
    },
}


class FirefoxPoliciesJsonImportRequest(BaseModel):
    """Create a profile from a Firefox Enterprise policies.json document."""

    name: str = Field(..., max_length=255, description="Library profile name to create.")
    description: str | None = Field(
        default=None,
        description="Optional library profile description.",
    )
    schema_version: str = Field(
        default=DEFAULT_SCHEMA_CHANNEL,
        max_length=50,
        description="Firefox policy schema channel used to validate the imported document.",
    )
    document: Any = Field(
        ...,
        description=(
            "Full Firefox Enterprise policies.json document. "
            "The value must be an object with a top-level policies object."
        ),
    )
    compliance: dict[str, Any] | None = Field(
        default=None,
        description="Optional internal compliance metadata to attach to the created profile.",
    )
    owner: str | None = Field(
        default=None,
        max_length=255,
        description="Optional profile owner metadata.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE
        }
    )


def _decode_json_document(raw: bytes | str, *, source: str) -> Any:
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Invalid JSON in {source}",
                "error": str(exc),
            },
        ) from exc


def _validate_import_request_payload(data: dict[str, Any]) -> FirefoxPoliciesJsonImportRequest:
    try:
        return FirefoxPoliciesJsonImportRequest.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(),
        ) from exc


async def _read_firefox_policies_import_request(
    request: Request,
) -> FirefoxPoliciesJsonImportRequest:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file") or form.get("document")
        if upload is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Firefox policies.json import failed",
                    "error": "Multipart import requires a file field",
                },
            )

        if hasattr(upload, "read"):
            raw_document = await upload.read()
        elif isinstance(upload, str):
            raw_document = upload
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Firefox policies.json import failed",
                    "error": "Unsupported multipart document field",
                },
            )

        compliance: dict[str, Any] | None = None
        raw_compliance = form.get("compliance")
        if isinstance(raw_compliance, str) and raw_compliance.strip():
            parsed_compliance = _decode_json_document(raw_compliance, source="compliance")
            if not isinstance(parsed_compliance, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Firefox policies.json import failed",
                        "error": "Multipart compliance field must be a JSON object",
                    },
                )
            compliance = parsed_compliance

        name = form.get("name")
        if not isinstance(name, str) or not name.strip():
            filename = getattr(upload, "filename", "") or ""
            name = filename.removesuffix(".json").strip() or "Imported policies.json"

        return _validate_import_request_payload(
            {
                "name": name,
                "description": form.get("description") or None,
                "schema_version": form.get("schema_version") or DEFAULT_SCHEMA_CHANNEL,
                "document": _decode_json_document(raw_document, source="policies.json"),
                "compliance": compliance,
                "owner": form.get("owner") or None,
            }
        )

    if content_type.startswith("application/json"):
        try:
            data = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid JSON in request body",
                    "error": str(exc),
                },
            ) from exc
        return _validate_import_request_payload(data)

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail={
            "message": "Unsupported import content type",
            "error": "Use application/json or multipart/form-data",
        },
    )


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
    expected_revision = payload_data.pop("expected_revision", None)
    if expected_revision is not None and expected_revision != current.revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Profile has been modified since it was loaded",
                "profile_id": profile_id,
                "current_revision": current.revision,
                "expected_revision": expected_revision,
            },
        )
    normalized_payload_data = dict(payload_data)
    if "flags" in payload_data and payload_data["flags"] is not None:
        normalized_payload_data["flags"] = {**current.flags, **payload_data["flags"]}
    if "compliance" in payload_data:
        normalized_payload_data["compliance"] = payload_data["compliance"]
    normalized_payload = ProfileUpdate.model_validate(normalized_payload_data)

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


@router.post(
    "/import/firefox/policies.json",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import Firefox policies.json",
    description=(
        "Create a library profile from a full Firefox Enterprise policies.json document. "
        "The document is validated before the profile is created. Accepts either an "
        "application/json body or multipart/form-data with a file field."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name", "document"],
                        "properties": {
                            "name": {"type": "string", "maxLength": 255},
                            "description": {"type": "string", "nullable": True},
                            "schema_version": {"type": "string", "default": DEFAULT_SCHEMA_CHANNEL},
                            "document": {
                                "type": "object",
                                "description": "Full Firefox policies.json document.",
                                "properties": {
                                    "policies": {"type": "object"},
                                },
                                "required": ["policies"],
                            },
                            "compliance": {"type": "object", "nullable": True},
                            "owner": {"type": "string", "nullable": True, "maxLength": 255},
                        },
                        "example": FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE,
                    },
                },
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "Firefox policies.json file.",
                            },
                            "name": {"type": "string", "maxLength": 255},
                            "schema_version": {"type": "string", "default": DEFAULT_SCHEMA_CHANNEL},
                            "description": {"type": "string"},
                            "owner": {"type": "string", "maxLength": 255},
                            "compliance": {
                                "type": "string",
                                "description": "Optional JSON object with compliance metadata.",
                            },
                        },
                    }
                },
            },
            "required": True,
        }
    },
)
async def import_firefox_policies_json(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    """Create a profile from a canonical Firefox enterprise policies.json payload."""
    payload = await _read_firefox_policies_import_request(request)
    try:
        flags = validate_firefox_policies_document(
            payload.document,
            payload.schema_version,
        )
    except FirefoxPoliciesImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Firefox policies.json import failed",
                "issues": [
                    {
                        "policy": None,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except FirefoxPoliciesDocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Policy validation failed",
                "issues": [
                    {
                        "policy": issue.policy,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Profile validation failed",
                "error": str(exc),
            },
        ) from exc

    return await _create_profile_core(
        ProfileCreate(
            name=payload.name,
            description=payload.description,
            schema_version=payload.schema_version,
            flags=flags,
            compliance=payload.compliance,
            owner=payload.owner,
        ),
        session,
        validate_policies=False,
        conflict_detail="Profile with this name already exists",
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
