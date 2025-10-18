from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..services.policy_service import PolicyService

router = APIRouter(tags=["export"])


@router.get("/api/export/{policy_id}/policies.json")
async def export_policies_json(
    policy_id: int, session: AsyncSession = Depends(get_session)
):
    """
    Minimal export endpoint returning {"policies": <flags>} for a stored policy.
    Satisfies tests expecting JSON export at /api/export/{id}/policies.json
    """
    entity = await PolicyService.get(session, policy_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return {"policies": entity.flags or {}}
