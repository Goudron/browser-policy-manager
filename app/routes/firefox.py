from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(tags=["firefox"])

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schemas" / "firefox.yaml"
PRESETS_DIR = BASE_DIR / "schemas" / "presets"


def _load_yaml_file(path: Path) -> Any:
    try:
        import importlib

        yaml = importlib.import_module("yaml")
        text = path.read_text(encoding="utf-8")
        return yaml.safe_load(text)
    except Exception as exc:
        raise HTTPException(500, detail=f"YAML load failed: {exc}") from exc


def _load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise HTTPException(500, detail="Schema file not found: app/schemas/firefox.yaml")
    data = _load_yaml_file(SCHEMA_PATH)
    if not isinstance(data, dict):
        raise HTTPException(500, detail="Invalid YAML schema format")
    return data


@router.get("/api/firefox/schema")
def get_schema() -> JSONResponse:
    schema = _load_schema()
    return JSONResponse(schema)


@router.get("/api/firefox/preset/{name}")
def get_preset(name: str) -> JSONResponse:
    """
    Загружает YAML пресета и возвращает form payload (по id), уже готовый для заполнения формы.
    """
    file = PRESETS_DIR / f"{name}.yaml"
    if not file.exists():
        raise HTTPException(404, detail=f"Preset not found: {name}")
    data = _load_yaml_file(file)
    if not isinstance(data, dict):
        raise HTTPException(500, detail="Invalid preset YAML")
    include = data.get("include", [])
    if not isinstance(include, list):
        include = []
    form_payload: dict[str, Any] = {}
    for k in include:
        form_payload[k] = ""
    return JSONResponse({"payload": form_payload})


@router.post("/api/firefox/preset/apply")
def apply_preset(payload: dict) -> JSONResponse:
    """
    Принимает payload с ключом 'include' (список id) и формирует form payload.
    """
    include = payload.get("include", [])
    if not isinstance(include, list):
        include = []
    form_payload: dict[str, Any] = {}
    for k in include:
        form_payload[k] = ""
        if isinstance(include, list):
            try:
                form_payload[list(form_payload.keys())[-1]] = "\n".join(str(x) for x in include)
            except Exception:
                pass
    return JSONResponse({"payload": form_payload})


@router.get("/api/firefox/export")
def export_policies(flags: dict) -> JSONResponse:
    """
    Преобразование form payload -> {"policies": {...}}.
    """
    policies: dict[str, Any] = {}
    for pid, value in flags.items():
        if isinstance(value, str) and "\n" in value:
            arr = [x.strip() for x in value.splitlines() if x.strip()]
            policies[pid] = arr
        elif isinstance(value, str):
            policies[pid] = value
        elif isinstance(value, (int, float, bool)):
            policies[pid] = value
        elif isinstance(value, dict):
            try:
                policies[pid] = json.loads(json.dumps(value, ensure_ascii=False))
            except Exception:
                policies[pid] = {}
        else:
            policies[pid] = value
    return JSONResponse({"policies": policies})


@router.get("/api/firefox/ping")
def ping() -> PlainTextResponse:
    return PlainTextResponse("ok")
