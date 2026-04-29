from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.profile import ProfileRead
from app.services.firefox_policy_export import render_firefox_policies_document
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/export", tags=["export"])


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
    "/profiles/{profile_id}/firefox/policies.json",
    summary="Export Firefox policies.json",
    description=(
        "Export a single profile as the canonical user-facing Firefox Enterprise "
        "policies.json document for deployment."
    ),
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
