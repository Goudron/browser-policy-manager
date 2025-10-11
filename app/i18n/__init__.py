from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CATALOG_DIR = Path(__file__).parent
SUPPORTED_LANGS = {"en", "ru"}


def _load(lang: str) -> dict[str, Any]:
    p = CATALOG_DIR / f"{lang}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache
def catalogs() -> dict[str, dict[str, Any]]:
    return {lang: _load(lang) for lang in SUPPORTED_LANGS}


def _get_nested(d: dict[str, Any], key: str) -> str | None:
    cur: Any = d
    for part in key.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur if isinstance(cur, str) else None


def translate(key: str, lang: str = "en", default: str = "") -> str:
    cats = catalogs()
    # 1) выбранный язык
    v = _get_nested(cats.get(lang, {}), key)
    if v:
        return v
    # 2) fallback en
    v = _get_nested(cats.get("en", {}), key)
    if v:
        return v
    # 3) default или сам ключ (для отладки)
    return default or key
