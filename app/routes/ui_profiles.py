from __future__ import annotations

import types
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

# Пытаемся подключить in-memory STORE из API-модуля (dev-режим).
# Если модуля нет — просто покажем пустой список.
policies_api: Optional[types.ModuleType]
try:
    from app.api import policies as _policies_api  # импорт успешен → модуль

    policies_api = _policies_api
except Exception:  # pragma: no cover
    policies_api = None


def _collect_profiles() -> List[Dict[str, Any]]:
    """
    Собирает список профилей из in-memory STORE (если он есть).
    Возвращает list[dict] с полями id/name/description/schema_version.
    """
    result: List[Dict[str, Any]] = []
    store: Optional[Dict[int, Any]] = None

    if policies_api is not None and hasattr(policies_api, "_STORE"):
        maybe_store = getattr(policies_api, "_STORE")
        if isinstance(maybe_store, dict):
            store = maybe_store

    if store:
        for item in store.values():
            # Поддержим Pydantic-модель, dict и “простой объект”
            if hasattr(item, "model_dump"):
                data_fn = getattr(item, "model_dump", None)
                if callable(data_fn):
                    try:
                        data = data_fn()
                    except Exception:
                        data = {}
                else:
                    data = {}
            elif isinstance(item, dict):
                data = item
            else:
                data = {
                    "id": getattr(item, "id", None),
                    "name": getattr(item, "name", ""),
                    "description": getattr(item, "description", None),
                    "schema_version": getattr(item, "schema_version", ""),
                }

            raw_id: Any = data.get("id") if isinstance(data, dict) else None
            try:
                pid = int(raw_id) if raw_id is not None else -1
            except Exception:
                pid = -1

            result.append(
                {
                    "id": pid,
                    "name": (str(data.get("name") or "") if isinstance(data, dict) else ""),
                    "description": (data.get("description") if isinstance(data, dict) else None),
                    "schema_version": (
                        str(data.get("schema_version") or "") if isinstance(data, dict) else ""
                    ),
                }
            )
    return result


@router.get("/profiles", response_class=HTMLResponse)
def profiles_page() -> str:
    """
    Небольшая HTML-страница со списком профилей.
    Без Jinja2/БД, чтобы не плодить зависимостей и сохранять простоту типизации.
    """
    profiles = _collect_profiles()

    def _li() -> Iterable[str]:
        if not profiles:
            yield "<li><em>No profiles yet. Use POST /api/policies to create one.</em></li>"
            return
        for p in profiles:
            pid = p["id"]
            name = p["name"] or f"Profile #{pid}"
            desc = f" — {p['description']}" if p.get("description") else ""
            ver = p.get("schema_version") or ""
            yield (
                f'<li><a href="/api/policies/{pid}">{name}</a>{desc} <small>({ver})</small></li>'
            )

    html = (
        "<!doctype html><html><head>"
        "<meta charset='utf-8'><title>Profiles — Browser Policy Manager</title>"
        "<style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial}"
        "main{max-width:760px;margin:40px auto;padding:0 16px}"
        "ul{line-height:1.8}"
        "code{background:#f4f4f4;padding:2px 4px;border-radius:4px}"
        "</style>"
        "</head><body><main>"
        "<h1>Policy Profiles</h1>"
        "<p>Навигация по профилям. Создание/редактирование через JSON-API.</p>"
        "<ul>"
        f"{''.join(_li())}"
        "</ul>"
        "<hr>"
        '<p><a href="/">← На главную</a></p>'
        '<p><a href="/docs">OpenAPI Docs</a> · '
        "<code>POST /api/policies</code> · "
        "<code>GET /api/v1/schemas</code> · "
        "<code>POST /api/v1/policies/validate</code>"
        "</p>"
        "</main></body></html>"
    )
    return html
