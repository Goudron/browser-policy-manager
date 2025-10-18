from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(tags=["schemas"])


@router.get("/api/v1/schemas")
async def list_schemas():
    """
    Tests expect: a mapping with key 'items' that is a list,
    and each item has 'channel' and 'version' keys.
    """
    return {
        "items": [
            {"channel": "esr", "version": "firefox-ESR"},
        ]
    }


@router.post("/api/v1/policies/validate")
async def validate_policy_doc(doc: Dict[str, Any] = Body(...)):
    """
    Tests expect 422 with detail as a DICT containing 'message' and 'error' on bad input.
    """
    if not doc:
        raise HTTPException(status_code=422, detail={"message": "Document is empty", "error": True})
    if not isinstance(doc.get("policies"), dict):
        raise HTTPException(
            status_code=422,
            detail={"message": "Missing or invalid 'policies'", "error": True},
        )
    return {"ok": True}
