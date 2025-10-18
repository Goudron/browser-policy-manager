from __future__ import annotations

import json
from typing import Any, Dict, cast

from fastapi import APIRouter, HTTPException, Request, UploadFile
from starlette.datastructures import FormData
from starlette.datastructures import UploadFile as StarletteUploadFile

router = APIRouter(tags=["import"])


def _unwrap_policies(obj: Any) -> Dict[str, Any]:
    """
    Accept either {"policies": {...}} or a plain dict and return {"policies": {...}}.
    Raise HTTP 400 if shape is invalid.
    """
    if isinstance(obj, dict):
        if "policies" in obj and isinstance(obj["policies"], dict):
            return {"policies": obj["policies"]}
        # Treat as direct policies dictionary
        return {"policies": obj}
    raise HTTPException(status_code=400, detail="Missing or invalid 'policies' key")


@router.post("/api/import-policies")
async def import_policies(request: Request):
    """
    Universal import endpoint compatible with tests:

    Accepts:
      - application/json:
          * {"policies": {...}} -> OK
          * JSON string of dict (e.g., '{"DisableTelemetry": true}') -> OK (wrap as policies)
          * plain dict like {"DisableTelemetry": true} -> OK (wrap as policies)
      - multipart/form-data:
          * file field containing a JSON document:
              - {"policies": {...}} -> OK
              - or a plain dict -> wrap as policies
    """
    ctype = (request.headers.get("content-type") or "").lower()

    # Multipart branch (file upload). Detect by content type.
    if ctype.startswith("multipart/form-data"):
        form: FormData = await request.form()

        # Prefer common keys first
        candidate = form.get("file")
        if candidate is None:
            # Fallback: try to find the first file-like object among all fields
            for _k, v in form.multi_items():
                if isinstance(v, (UploadFile, StarletteUploadFile)):
                    candidate = v
                    break

        if candidate is None:
            raise HTTPException(status_code=400, detail="Missing file field")

        # Ensure UploadFile
        if not isinstance(candidate, (UploadFile, StarletteUploadFile)):
            raise HTTPException(status_code=400, detail="Missing file field")

        upload: StarletteUploadFile = cast(StarletteUploadFile, candidate)
        try:
            raw = await upload.read()
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON file")

        return _unwrap_policies(data)

    # JSON branch (read raw body and parse ourselves)
    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="Missing body")

    try:
        payload: Any = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        # body may be a JSON string quoted twice or invalid
        raise HTTPException(status_code=400, detail="Invalid JSON string")

    if isinstance(payload, dict):
        return _unwrap_policies(payload)

    if isinstance(payload, str):
        # If JSON contains a JSON-encoded string
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON string")
        return _unwrap_policies(parsed)

    raise HTTPException(status_code=400, detail="Unsupported payload type")
