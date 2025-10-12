from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from app.i18n import translate
from app.middleware.locale import LocaleMiddleware

app = FastAPI(title="Browser Policy Manager", version="0.1.0")
app.add_middleware(LocaleMiddleware)

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@pass_context
def t(ctx, key: str, default: str = "") -> str:
    req = ctx.get("request")
    lang = getattr(req.state, "lang", "en") if req else "en"
    return translate(key, lang=lang, default=default)


# регистрируем t в env
templates.env.globals["t"] = t
# делаем шаблонизатор доступным для других роутеров
app.state.templates = templates

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- favicon в корне ---
@app.get("/favicon.ico")
def favicon() -> FileResponse:
    """
    Отдаём favicon из app/static/favicon.ico по пути /favicon.ico,
    потому что браузеры запрашивают именно корень.
    """
    path = STATIC_DIR / "favicon.ico"
    return FileResponse(path)  # если файла нет, FastAPI вернёт 404 автоматически


# === API ===
try:
    from app.routes import api_import

    app.include_router(api_import.router)
except Exception:
    pass

try:
    from app.routes import policies as policies_router

    app.include_router(policies_router.router)
except Exception:
    pass

# === UI ===
try:
    from app.routes import ui_import

    app.include_router(ui_import.router)
except Exception:
    pass

try:
    from app.routes import ui_profiles
    app.include_router(ui_profiles.router)
except Exception:
    pass

@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    tpl = TEMPLATES_DIR / "index.html"
    if tpl.exists():
        return templates.TemplateResponse(request, "index.html", {})
    return JSONResponse(
        {
            "name": "Browser Policy Manager",
            "message": "UI template not found (app/templates/index.html). API is up.",
        }
    )
