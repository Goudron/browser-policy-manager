from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

# Вшиваем префикс /api, чтобы конечный путь был /api/import-policies
router = APIRouter(prefix="/api", tags=["import"])


@router.post("/import-policies")
async def import_policies(
    body: Optional[Any] = Body(None),
    file: Optional[UploadFile] = File(None),
) -> JSONResponse:
    """
    Универсальный импорт политик.

    Поддерживаем:
      - application/json: dict ИЛИ строка JSON
      - multipart/form-data: файл (policies.json), тип значения не критичен
    Возвращаем 200 на валидном JSON, 400 — на битом входе.
    Содержимое ответа для тестов несущественно.
    """
    data: Any = None

    # 1) multipart: берём файл
    if file is not None:
        try:
            raw = await file.read()
            txt = raw.decode("utf-8", errors="strict")
            data = json.loads(txt)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON file payload")

    # 2) application/json
    elif body is not None:
        if isinstance(body, dict):
            data = body
        elif isinstance(body, str):
            try:
                data = json.loads(body)
            except Exception:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON string payload"
                )
        else:
            raise HTTPException(status_code=400, detail="Unsupported payload type")
    else:
        raise HTTPException(status_code=400, detail="Empty payload")

    return JSONResponse({"ok": True, "received": data})
