from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["api"])

# Простая in-memory "БД" для профилей политик (достаточно для тестов)
_POLICIES_DB: dict[str, dict[str, Any]] = {}


def _ensure_profile_exists(pid: str) -> dict[str, Any]:
    if pid not in _POLICIES_DB:
        raise HTTPException(status_code=404, detail="Policy profile not found")
    return _POLICIES_DB[pid]


@router.post("/policies", status_code=201)
def create_policy_profile(payload: dict[str, Any] = Body(...)) -> JSONResponse:
    """
    Ожидается тело:
    {
      "name": "Default",
      "description": "Base profile",
      "schema_version": "firefox-ESR",
      "flags": {"DisableTelemetry": true, "DisablePocket": true}
    }
    """
    pid = str(uuid.uuid4())
    record = {
        "id": pid,
        "name": payload.get("name") or "",
        "description": payload.get("description") or "",
        "schema_version": payload.get("schema_version") or "firefox",
        "flags": payload.get("flags") or {},
    }
    _POLICIES_DB[pid] = record
    return JSONResponse(record, status_code=201)


@router.get("/policies")
def list_policy_profiles() -> list[dict[str, Any]]:
    return list(_POLICIES_DB.values())


@router.get("/policies/{pid}")
def get_policy_profile(pid: str) -> dict[str, Any]:
    return _ensure_profile_exists(pid)


@router.put("/policies/{pid}")
def update_policy_profile(pid: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    rec = _ensure_profile_exists(pid)
    for k in ("name", "description", "schema_version", "flags"):
        if k in payload:
            rec[k] = payload[k]
    return rec


@router.delete("/policies/{pid}", status_code=204)
def delete_policy_profile(pid: str):
    _ensure_profile_exists(pid)
    _POLICIES_DB.pop(pid, None)
    return JSONResponse(status_code=204, content=None)


# Старый экспорт (оставляем совместимостью)
@router.get("/policies/{pid}/export")
def export_policy_profile(pid: str) -> dict[str, Any]:
    rec = _ensure_profile_exists(pid)
    flags = rec.get("flags") or {}
    if not isinstance(flags, dict):
        raise HTTPException(400, detail="Invalid flags format")
    return {"policies": flags}


# НОВЫЙ маршрут под тест: GET /api/export/{pid}/policies.json
@router.get("/export/{pid}/policies.json")
def export_policy_profile_file(pid: str) -> JSONResponse:
    rec = _ensure_profile_exists(pid)
    flags = rec.get("flags") or {}
    if not isinstance(flags, dict):
        raise HTTPException(400, detail="Invalid flags format")
    return JSONResponse({"policies": flags})
