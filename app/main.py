from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles

from app.routes.firefox import router as firefox_router
from app.routes.api import router as api_router

app = FastAPI(
    title="Browser Policy Manager",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Static files ---
STATIC_DIR = Path("app/static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

FAVICON_PATH = STATIC_DIR / "favicon.ico"


@app.get("/favicon.ico")
def favicon():
    if FAVICON_PATH.exists():
        return FileResponse(str(FAVICON_PATH), media_type="image/x-icon")
    # если файла нет — не спамим 404, отдадим пустой ответ
    return Response(status_code=204)


# --- Routers ---
app.include_router(firefox_router)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse, tags=["meta"])
def index() -> str:
    return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Browser Policy Manager</title>
    <link rel="icon" href="/favicon.ico">
    <link rel="shortcut icon" href="/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;margin:20px}
      .links a{margin-right:10px}
    </style>
  </head>
  <body>
    <h1>Browser Policy Manager</h1>
    <p>Maintainer: <strong>Valery Ledovskoy</strong></p>
    <p class="links">
      <a href="/profiles">Profiles</a>
      <a href="/firefox/form">Open Firefox Policies form</a>
      <a href="/docs">/docs</a>
    </p>
  </body>
</html>"""


@app.get("/profiles", response_class=HTMLResponse, tags=["meta"])
def profiles_page() -> str:
    return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Profiles — Browser Policy Manager</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="icon" href="/favicon.ico">
    <link rel="shortcut icon" href="/favicon.ico">
    <style>
      body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;margin:20px}
      .card{border:1px solid #ddd;border-radius:10px;padding:12px;margin:8px 0}
      .muted{color:#666}
      code{background:#f6f6f6;padding:2px 4px;border-radius:4px}
    </style>
  </head>
  <body>
    <h1>Profiles</h1>
    <div id="list"></div>
    <p><a href="/">⬅ Back</a></p>
    <script>
      fetch('/api/policies')
        .then(r => r.json())
        .then(items => {
          const root = document.getElementById('list');
          if (!Array.isArray(items) || !items.length) {
            root.innerHTML = '<p class="muted">No profiles yet.</p>';
            return;
          }
          root.innerHTML = items.map(p => `
            <div class="card">
              <div><strong>${p.name || '(no name)'} </strong>
                <span class="muted">${p.id}</span>
              </div>
              <div class="muted">${p.description || ''}</div>
              <div>Schema: <code>${p.schema_version || ''}</code></div>
              <div style="margin-top:6px">
                <a href="/api/export/${p.id}/policies.json" target="_blank">Export policies.json</a>
              </div>
            </div>
          `).join('');
        })
        .catch(() => {
          document.getElementById('list').innerHTML = '<p class="muted">Failed to load.</p>';
        });
    </script>
  </body>
</html>"""


@app.get("/healthz", tags=["meta"])
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})
