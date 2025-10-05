from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from app.models.db import init_db
from app.api import policies, exports, health

app = FastAPI(title="Browser Policy Manager")
init_db()

# UI (простой заглушкой пока)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"message": "It works!"})

# REST
app.include_router(health.router)
app.include_router(policies.router)
app.include_router(exports.router)
