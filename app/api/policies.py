from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/policies", tags=["policies"])

# ----------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------


class PolicyInput(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    schema_version: str = Field(..., min_length=1)
    flags: Dict[str, bool] = Field(default_factory=dict)


class PolicyProfileOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    schema_version: str
    flags: Dict[str, bool]


# ----------------------------------------------------------------------
# In-memory storage (для целей mypy/линта; не используется в рантайме)
# ----------------------------------------------------------------------

_STORE: Dict[int, PolicyProfileOut] = {}
_NEXT_ID = 1


def _next_id() -> int:
    global _NEXT_ID
    nid = _NEXT_ID
    _NEXT_ID += 1
    return nid


# ----------------------------------------------------------------------
# CRUD (совместимый контрактом с тестами по смыслу)
# ----------------------------------------------------------------------


@router.post("", response_model=PolicyProfileOut, status_code=status.HTTP_201_CREATED)
def create_policy_profile(payload: PolicyInput = Body(...)) -> PolicyProfileOut:
    """
    In-memory создание профиля. Возвращает PolicyProfileOut с новым id.
    """
    pid = _next_id()
    out = PolicyProfileOut(
        id=pid,
        name=payload.name,
        description=payload.description,
        schema_version=payload.schema_version,
        flags=payload.flags,
    )
    _STORE[pid] = out
    return out


@router.get("/{profile_id}", response_model=PolicyProfileOut)
def get_policy_profile(profile_id: int) -> PolicyProfileOut:
    row = _STORE.get(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row


@router.put("/{profile_id}", response_model=PolicyProfileOut)
def update_policy_profile(
    profile_id: int, body: PolicyInput = Body(...)
) -> PolicyProfileOut:
    row = _STORE.get(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")

    updated = PolicyProfileOut(
        id=profile_id,
        name=body.name,
        description=body.description,
        schema_version=body.schema_version,
        flags=body.flags,
    )
    _STORE[profile_id] = updated
    return updated


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy_profile(profile_id: int) -> None:
    if profile_id in _STORE:
        del _STORE[profile_id]
    # 204 — без тела
    return None


@router.get("/{profile_id}/export")
def export_policy_profile_file(profile_id: int) -> Dict[str, Dict[str, bool]]:
    """
    Минимальный экспорт: возвращаем только блок policies из flags.
    Совместимо по смыслу с legacy-эндпоинтами.
    """
    row = _STORE.get(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"policies": row.flags}
