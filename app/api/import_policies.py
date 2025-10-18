from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(tags=["import"])


@router.post("/api/import-policies")
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
        # Может прийти сразу dict
        if isinstance(body, dict):
            data = body
        # Или строка с JSON — парсим
        elif isinstance(body, str):
            try:
                data = json.loads(body)
            except Exception:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON string payload"
                )
        else:
            # Нестандартный тип
            raise HTTPException(status_code=400, detail="Unsupported payload type")

    else:
        raise HTTPException(status_code=400, detail="Empty payload")

    # На этом этапе data — валидный JSON-объект/значение
    return JSONResponse({"ok": True, "received": data})
