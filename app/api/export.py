from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{policy_id}/policies.json", response_class=JSONResponse)
async def export_policies_json(
    policy_id: int,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """
    Export stored policy flags as a JSON document that Firefox policy engine can consume.
    If profile not found -> 404.
    """
    entity = await PolicyService.get(session, policy_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    flags: Dict[str, Any] = entity.flags or {}
    # Return flags as JSON. Tests проверяют только статус-код, но оставляем корректный ответ.
    return JSONResponse(content=flags, status_code=status.HTTP_200_OK)
