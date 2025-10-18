from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/profiles", response_class=HTMLResponse)
def profiles_index() -> str:
    """
    Простая UI-страница раздела профилей.
    Здесь намеренно нет работы с БД/шаблонами, чтобы избежать mypy-проблем
    и сложных зависимостей. Страница служит навигационной точкой.
    """
    return (
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
        "<p>Это демонстрационная страница UI. "
        "Для CRUD используйте JSON-API или будущий полноценный редактор.</p>"
        "<ul>"
        '<li><a href="/docs">OpenAPI Docs</a></li>'
        "<li>Создать профиль (API): <code>POST /api/policies</code></li>"
        "<li>Список схем: <code>GET /api/v1/schemas</code></li>"
        "<li>Валидация профиля: <code>POST /api/v1/policies/validate</code></li>"
        "</ul>"
        '<p><a href="/">← На главную</a></p>'
        "</main></body></html>"
    )
