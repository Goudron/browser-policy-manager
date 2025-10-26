# app/api/export.py
# Export API for enterprise browser policies.
# Features:
# - Export a single policy by id in JSON or YAML.
# - Export a collection with filters, pagination, include_deleted flag.
# - Proper Content-Type and Content-Disposition headers.
# Notes:
# - Supported formats: json | yaml
# - Soft-deleted records are excluded by default (include_deleted=false).

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas.policy import PolicyRead
from ..services.policy_service import PolicyService
from ..utils.yaml_io import to_yaml

router = APIRouter(prefix="/api/export", tags=["export"])

ExportFormat = Literal["json", "yaml"]


def _filename_single(policy: PolicyRead, fmt: ExportFormat) -> str:
    base = f"policy-{policy.id}-{policy.name}".replace(" ", "_")
    return f"{base}.{fmt}"


def _filename_list(fmt: ExportFormat) -> str:
    return f"policies.{fmt}"


# ---- Single item export (query-param format) ---------------------------------


@router.get(
    "/policies/{policy_id}",
    summary="Export a single policy",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
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
                },
                "application/x-yaml": {
                    "example": (
                        "id: 1\n"
                        "name: Default\n"
                        "description: Base profile\n"
                        "schema_version: esr-140\n"
                        "flags:\n"
                        "  DisableTelemetry: true\n"
                        "owner: admin@example.org\n"
                        "created_at: '2025-10-01T12:30:00+00:00'\n"
                        "updated_at: '2025-10-02T08:00:00+00:00'\n"
                        "deleted_at: null\n"
                        "is_deleted: false\n"
                    )
                },
            }
        },
        404: {"description": "Policy not found"},
    },
)
async def export_policy(
    policy_id: int,
    fmt: ExportFormat = Query(
        "json",
        description="Export format: json | yaml",
    ),
    include_deleted: bool = Query(False, description="Include soft-deleted item if true"),
    session: AsyncSession = Depends(get_session),
):
    item = await PolicyService.get(session, policy_id, include_deleted=include_deleted)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    filename = _filename_single(item, fmt)
    if fmt == "json":
        # mode="json" converts datetimes to ISO strings
        return JSONResponse(
            content=item.model_dump(mode="json"),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        payload = to_yaml(item.model_dump(mode="json"))
        return PlainTextResponse(
            content=payload,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


# ---- Backward compatibility: extension-based routes --------------------------


@router.get(
    "/{policy_id}/policies.json",
    summary="[Compat] Export a single policy as JSON",
)
async def export_policy_json_compat(
    policy_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted item if true"),
    session: AsyncSession = Depends(get_session),
):
    item = await PolicyService.get(session, policy_id, include_deleted=include_deleted)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    filename = _filename_single(item, "json")
    return JSONResponse(
        content=item.model_dump(mode="json"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{policy_id}/policies.yaml",
    summary="[Compat] Export a single policy as YAML",
)
async def export_policy_yaml_compat(
    policy_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted item if true"),
    session: AsyncSession = Depends(get_session),
):
    item = await PolicyService.get(session, policy_id, include_deleted=include_deleted)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    filename = _filename_single(item, "yaml")
    payload = to_yaml(item.model_dump(mode="json"))
    return PlainTextResponse(
        content=payload,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---- Collection export -------------------------------------------------------


@router.get(
    "/policies",
    summary="Export policies collection",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "name": "Default",
                                "schema_version": "esr-140",
                                "flags": {"DisableTelemetry": True},
                                "is_deleted": False,
                            }
                        ],
                        "limit": 50,
                        "offset": 0,
                        "count": 1,
                    }
                },
                "application/x-yaml": {
                    "example": (
                        "items:\n"
                        "  - id: 1\n"
                        "    name: Default\n"
                        "    schema_version: esr-140\n"
                        "    flags:\n"
                        "      DisableTelemetry: true\n"
                        "    is_deleted: false\n"
                        "limit: 50\n"
                        "offset: 0\n"
                        "count: 1\n"
                    )
                },
            }
        }
    },
)
async def export_policies(
    fmt: ExportFormat = Query(
        "json",
        description="Export format: json | yaml",
    ),
    include_deleted: bool = Query(False, description="Include soft-deleted items"),
    q: Optional[str] = Query(None, description="Search by name/description (ILIKE)"),
    owner: Optional[str] = Query(None),
    schema_version: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    sort: str = Query("updated_at", pattern="^(created_at|updated_at|name|id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
):
    items: List[PolicyRead] = await PolicyService.list(
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

    payload = {
        "items": [it.model_dump(mode="json") for it in items],
        "limit": limit,
        "offset": offset,
        "count": len(items),
    }

    filename = _filename_list(fmt)
    if fmt == "json":
        return JSONResponse(
            content=payload,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        text = to_yaml(payload)
        return PlainTextResponse(
            content=text,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
