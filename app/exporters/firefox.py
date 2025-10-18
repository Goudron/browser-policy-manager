from __future__ import annotations

import json
from typing import Any


def _lines_to_list(value: str) -> list[str]:
    return [ln.strip() for ln in (value or "").splitlines() if ln.strip()]


def build_policies(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """
    payload: { policy_id: value_from_form, ... }
    schema:  parsed YAML (app/schemas/firefox.yaml)
    Returns: dict suitable for policies.json -> { "policies": { ... } }
    """
    policies: dict[str, Any] = {}
    index = {p["id"]: p for p in schema.get("policies", [])}

    for pid, val in payload.items():
        spec = index.get(pid)
        if not spec:
            continue
        key = spec["key"]
        t = spec["type"]

        if t == "boolean":
            policies[key] = bool(val)
        elif t in ("string", "integer", "number", "enum"):
            policies[key] = val
        elif t == "array":
            if isinstance(val, str):
                policies[key] = _lines_to_list(val)
            else:
                policies[key] = val or []
        elif t == "object":
            if isinstance(val, str) and val.strip():
                try:
                    policies[key] = json.loads(val)
                except Exception:
                    # ignore invalid JSON (best-effort)
                    continue
            elif isinstance(val, dict):
                policies[key] = val
        else:
            policies[key] = val

    return {"policies": policies}


def build_form_payload_from_policies(
    policies_json: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    """
    Обратное преобразование: { "policies": { Key: Value, ... } } -> form payload по id.
    Возвращает { policy_id: value_for_form }, где массивы превращаем в многострочный текст,
    объекты — в компактный JSON.
    """
    result: dict[str, Any] = {}
    index_by_key = {p["key"]: p for p in schema.get("policies", [])}
    pol = (policies_json or {}).get("policies", {})

    for key, value in pol.items():
        spec = index_by_key.get(key)
        if not spec:
            continue
        pid = spec["id"]
        t = spec["type"]
        if t == "boolean":
            result[pid] = bool(value)
        elif t in ("string", "integer", "number", "enum"):
            result[pid] = value
        elif t == "array":
            # многострочный textarea
            if isinstance(value, list):
                result[pid] = "\n".join(str(x) for x in value)
            else:
                result[pid] = str(value)
        elif t == "object":
            try:
                result[pid] = json.dumps(
                    value, ensure_ascii=False, separators=(",", ":")
                )
            except Exception:
                result[pid] = "{}"
        else:
            result[pid] = value
    return result
