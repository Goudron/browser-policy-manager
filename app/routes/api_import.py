from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Body, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, List
import json

from app.services.importer import normalize_policies

router = APIRouter(prefix="/api", tags=["import"])

class ImportResponse(BaseModel):
    policies: Dict[str, Any]
    warnings: List[str] = []

@router.post("/import-policies", response_model=ImportResponse)
async def import_policies(
    request: Request,
    file: UploadFile | None = File(default=None),
    data: Any | None = Body(default=None),
):
    payload: Any | None = None

    # 1) multipart файл
    if file is not None:
        try:
            text = (await file.read()).decode("utf-8")
            payload = json.loads(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid file: {e}")

    # 2) обычное JSON-тело (dict ИЛИ строка JSON)
    if payload is None and data is not None:
        if isinstance(data, str):
            try:
                payload = json.loads(data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON string: {e}")
        else:
            payload = data

    # 3) абсолютный fallback: попробуем прочитать тело сами
    if payload is None:
        try:
            raw = await request.body()
            if raw:
                try:
                    # если это строка в JSON, то сначала распарсим в строку, а потом ещё раз
                    obj = json.loads(raw.decode("utf-8"))
                    payload = json.loads(obj) if isinstance(obj, str) else obj
                except Exception:
                    pass
        except Exception:
            pass

    if payload is None:
        raise HTTPException(status_code=400, detail="No input provided")

    policies, warnings = normalize_policies(payload)
    return ImportResponse(policies=policies, warnings=warnings)
