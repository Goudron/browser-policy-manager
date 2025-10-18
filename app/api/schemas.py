from __future__ import annotations

from fastapi import APIRouter

from app.services.schema_service import available

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.get("")
def list_schemas():
    items = []
    for (channel, version), label in available().items():
        items.append(
            {"channel": channel, "version": version or "stable", "label": label}
        )
    return {"items": sorted(items, key=lambda x: (x["channel"], x["version"]))}
