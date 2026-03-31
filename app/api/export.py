from __future__ import annotations

import json
from typing import Any, Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.profile import ProfileRead
from app.services.firefox_policy_export import render_firefox_policies_document
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/export", tags=["export"])


def _serialize(profile: ProfileRead) -> dict[str, Any]:
    """Serialize an internal profile model to the public export shape."""
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "schema_version": profile.schema_version,
        "flags": profile.flags,
        "owner": profile.owner,
        "is_deleted": profile.is_deleted,
    }


def _build_envelope(
    items: list[ProfileRead],
    limit: int,
    offset: int,
    total: int,
) -> dict[str, Any]:
    """
    Build a collection envelope.

    Tests expect an object with at least "items", "limit", "offset" and "count"
    for collection exports.
    """
    return {
        "items": [_serialize(p) for p in items],
        "limit": limit,
        "offset": offset,
        "count": total,
    }


def _to_yaml(data: Any) -> str:
    """Serialize data to YAML in a readable form."""
    return yaml.safe_dump(data, sort_keys=False)


def _build_firefox_policies_json_response(
    profile: ProfileRead,
    *,
    profile_id: int,
    download: int = 0,
    indent: int | None = None,
    pretty: int = 0,
) -> Response:
    """Serialize one profile as a Firefox enterprise policies.json payload."""
    if indent is None and pretty:
        indent = 2

    body_json = json.dumps(render_firefox_policies_document(profile.flags), indent=indent)
    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = (
            f'attachment; filename="profile-{profile_id}-policies.json"'
        )
    return Response(content=body_json, media_type="application/json", headers=headers)


@router.get(
    "/profiles",
    summary="Export profiles collection",
    description="Export a filtered collection of profiles as JSON or YAML.",
)
async def export_collection(
    session: AsyncSession = Depends(get_session),
    fmt: Literal["json", "yaml"] = Query("json"),
    download: int = Query(0, ge=0, le=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_deleted: bool = Query(False),
    q: str | None = Query(None),
    owner: str | None = Query(None),
    schema_version: str | None = Query(None),
    order_by: str | None = Query(None),
    sort: str | None = Query(None),
    order: str = Query("asc"),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """Export a collection of profiles."""
    effective_sort = sort or order_by or "id"
    items = await ProfileService.list(
        session,
        q=q,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
        sort=effective_sort,
        order=order,
    )
    total = await ProfileService.count(
        session,
        q=q,
        owner=owner,
        schema_version=schema_version,
        include_deleted=include_deleted,
    )
    envelope = _build_envelope(items, limit=limit, offset=offset, total=total)

    headers: dict[str, str] = {}

    if fmt == "yaml":
        if download:
            headers["Content-Disposition"] = 'attachment; filename="profiles.yaml"'
        body = _to_yaml(envelope)
        return Response(content=body, media_type="application/x-yaml", headers=headers)

    # Default JSON
    if indent is None and pretty:
        indent = 2
    body_json = json.dumps(envelope, indent=indent)
    if download:
        headers["Content-Disposition"] = 'attachment; filename="profiles.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)


@router.get(
    "/profiles/{profile_id}.json",
    summary="Export profile as JSON",
    description="Export a single profile as JSON via a suffix route.",
)
async def export_single_json_suffix(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
    download: int = Query(0, ge=0, le=1),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """Export one profile as JSON."""
    profile = await ProfileService.get(session, profile_id, include_deleted=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    if indent is None and pretty:
        indent = 2

    body_json = json.dumps(_serialize(profile), indent=indent)
    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="profile-{profile_id}.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)


@router.get(
    "/profiles/{profile_id}.yaml",
    summary="Export profile as YAML",
    description="Export a single profile as YAML via a suffix route.",
)
async def export_single_yaml_suffix(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
    download: int = Query(0, ge=0, le=1),
) -> Response:
    """Export one profile as YAML."""
    profile = await ProfileService.get(session, profile_id, include_deleted=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    body = _to_yaml(_serialize(profile))
    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="profile-{profile_id}.yaml"'
    return Response(content=body, media_type="application/x-yaml", headers=headers)


@router.get(
    "/profiles/{profile_id}/firefox/policies.json",
    summary="Export Firefox policies.json",
    description="Export a single profile as a ready-to-use Firefox enterprise policies.json document.",
)
async def export_single_firefox_policies_json(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
    include_deleted: bool = Query(False),
    download: int = Query(0, ge=0, le=1),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """Export one profile as a canonical Firefox enterprise policies.json payload."""
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return _build_firefox_policies_json_response(
        profile,
        profile_id=profile_id,
        download=download,
        indent=indent,
        pretty=pretty,
    )


@router.get(
    "/profiles/{profile_id}",
    summary="Export single profile",
    description="Export a single profile as JSON or YAML using the fmt query parameter.",
)
async def export_single_queryparam(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
    fmt: Literal["json", "yaml"] = Query("json"),
    include_deleted: bool = Query(False),
    download: int = Query(0, ge=0, le=1),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """Export one profile using the fmt query parameter route."""
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    headers: dict[str, str] = {}

    if fmt == "yaml":
        body = _to_yaml(_serialize(profile))
        if download:
            headers["Content-Disposition"] = f'attachment; filename="profile-{profile_id}.yaml"'
        return Response(content=body, media_type="application/x-yaml", headers=headers)

    # Default JSON
    if indent is None and pretty:
        indent = 2
    body_json = json.dumps(_serialize(profile), indent=indent)
    if download:
        headers["Content-Disposition"] = f'attachment; filename="profile-{profile_id}.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)
