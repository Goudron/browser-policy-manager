from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    # Include the expected text and a link to /profiles for the smoke test.
    return """<!doctype html>
<html>
  <head><title>BPM</title></head>
  <body>
    <h1>BPM</h1>
    <p>Valery Ledovskoy</p>
    <p><a href="/profiles">Profiles</a></p>
  </body>
</html>"""
