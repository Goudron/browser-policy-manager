from __future__ import annotations
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["policies"])

# --- Модели ---
class PolicyIn(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    schema_version: str = "firefox-ESR"
    flags: Dict[str, Any] = Field(default_factory=dict)

class PolicyOut(PolicyIn):
    id: str  # для тестов id обязателен; берём равным name


# --- Память в процессе (для dev/тестов) ---
_STORE: Dict[str, PolicyOut] = {}  # key = id


@router.post("/policies", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(body: PolicyIn):
    pid = body.name  # простое правило: id == name
    if pid in _STORE:
        raise HTTPException(status_code=409, detail="Policy already exists")
    obj = PolicyOut(id=pid, **body.model_dump())
    _STORE[pid] = obj
    return obj


@router.get("/policies", response_model=List[PolicyOut])
def list_policies():
    return list(_STORE.values())


@router.get("/policies/{pid}", response_model=PolicyOut)
def get_policy(pid: str):
    p = _STORE.get(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not Found")
    return p


@router.delete("/policies/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(pid: str):
    if pid not in _STORE:
        raise HTTPException(status_code=404, detail="Not Found")
    del _STORE[pid]
    return None


@router.get("/policies/{pid}/export")
def export_policy(pid: str):
    """
    Минимальный экспорт в формате:
      {"policies": { ...flags... }}
    """
    p = _STORE.get(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not Found")
    return {"policies": p.flags}


@router.get("/export/{pid}/policies.json")
def export_policy_alias(pid: str):
    """
    Алиас под тест: /api/export/{pid}/policies.json
    Возвращаем тот же JSON, media_type = application/json.
    """
    p = _STORE.get(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not Found")

    payload = {"policies": p.flags}
    return JSONResponse(content=payload, media_type="application/json")
