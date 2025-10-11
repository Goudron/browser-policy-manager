import json
from pathlib import Path

import pytest

I18N_DIR = Path(__file__).resolve().parents[1] / "app" / "i18n"


@pytest.mark.parametrize("lang", ["en", "ru"])
def test_i18n_catalog_parses_and_contains_ui_header_title(lang):
    path = I18N_DIR / f"{lang}.json"
    assert path.exists(), f"Missing {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        pytest.fail(f"{path.name} is not valid JSON: {e}")

    # traverse nested dict safely
    ui = data.get("ui") or {}
    header = ui.get("header") or {}
    title = header.get("title")

    assert isinstance(title, str) and title.strip(), f"Missing or empty title in {lang}.json"
    print(f"{lang}.json: title = {title!r}")
