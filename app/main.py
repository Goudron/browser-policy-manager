from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from app.models.db import init_db
from app.api import policies, exports, health
from app.api.schemas import router as schemas_router
from app.web.routes import router as web_router

app = FastAPI(title="Browser Policy Manager")
init_db()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"message": "It works!"})

# REST + WEB
app.include_router(health.router)
app.include_router(policies.router)
app.include_router(exports.router)
app.include_router(schemas_router)  # ← новый API
app.include_router(web_router)
# ============================================================
