import json
from pathlib import Path

import yaml
from fastapi import APIRouter, Body, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from app.exporters.firefox import build_form_payload_from_policies, build_policies
from app.routes.utils import group_by_ui_group

router = APIRouter(prefix="/firefox", tags=["firefox"])

SCHEMA_PATH = Path("app/schemas/firefox.yaml")
PRESETS_DIR = Path("app/presets")
templates = Jinja2Templates(directory="app/templates")


def _load_schema():
    if not SCHEMA_PATH.exists():
        raise HTTPException(500, detail="Schema file not found: app/schemas/firefox.yaml")
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


@router.get("/schema")
def get_schema():
    return _load_schema()


@router.get("/form")
def render_form(request: Request):
    data = _load_schema()
    grouped = group_by_ui_group(data["policies"])
    return templates.TemplateResponse(
        "policies_form.html.j2", {"request": request, "grouped_policies": grouped}
    )


@router.post("/export")
def export_policies(form_payload: dict = Body(...)):
    """
    Принимает payload вида:
    {
      "disable_app_update": true,
      "extensions": "https://...\nfile:///...",
      "homepage": "{\"URL\":\"https://intranet\",\"Locked\":true}"
    }
    Возвращает JSON вида {"policies": {...}}
    """
    try:
        schema = _load_schema()
        result = build_policies(form_payload, schema)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/download", response_class=PlainTextResponse)
def export_download(form_payload: dict = Body(...)):
    """
    Возвращает policies.json как attachment (text/plain c заголовком).
    """
    schema = _load_schema()
    result = build_policies(form_payload, schema)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    headers = {"Content-Disposition": 'attachment; filename="policies.json"'}
    return PlainTextResponse(text, headers=headers)


@router.get("/presets/{name}")
def get_preset(name: str):
    """
    Загружает YAML пресета и возвращает form payload (по id), уже готовый для заполнения формы.
    """
    file = PRESETS_DIR / f"{name}.yaml"
    if not file.exists():
        raise HTTPException(404, detail=f"Preset '{name}' not found")
    preset = yaml.safe_load(file.read_text(encoding="utf-8"))
    # preset ожидаем в виде:
    # { vendor: firefox, include: { <policy_id or camelKey?>: ... } }
    # Поддержим оба варианта: id и ключ. Преобразуем через схему.
    schema = _load_schema()
    by_id = {p["id"]: p for p in schema["policies"]}
    by_key = {p["key"]: p for p in schema["policies"]}

    include = preset.get("include", {}) or {}
    # если в пресете ключи выглядят как ключи policies.json (CamelCase),
    # преобразуем их в id
    form_payload = {}
    for k, v in include.items():
        if k in by_id:
            form_payload[k] = (
                v
                if not isinstance(v, (dict, list))
                else json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            )
        elif k in by_key:
            pid = by_key[k]["id"]
            form_payload[pid] = (
                v
                if not isinstance(v, (dict, list))
                else json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            )
        else:
            # неизвестный ключ — пропустим
            continue
        # массив -> textarea
        if isinstance(include[k], list):
            form_payload[list(form_payload.keys())[-1]] = "\n".join(str(x) for x in include[k])
    return JSONResponse({"payload": form_payload})


@router.post("/import")
async def import_policies(file: UploadFile = File(...)):
    """
    Принимает policies.json (формата Firefox Enterprise Policies),
    возвращает form payload для заполнения формы.
    """
    if not file.filename:
        raise HTTPException(400, detail="No file provided")
    try:
        raw = await file.read()
        data = json.loads(raw.decode("utf-8"))
        schema = _load_schema()
        payload = build_form_payload_from_policies(data, schema)
        return JSONResponse({"payload": payload})
    except Exception as e:
        raise HTTPException(400, detail=f"Import failed: {e}")
