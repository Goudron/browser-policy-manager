import json
import re
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[4]
I18N_DIR = REPO_ROOT / "app" / "i18n"
DATA_SOURCE = REPO_ROOT / "app" / "static" / "profiles_data.js"


def _read_locale(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def test_profile_data_api_error_keys_exist_in_all_active_catalogs():
    source = DATA_SOURCE.read_text(encoding="utf-8")
    keys = set(re.findall(r'"(profiles\.error_(?:api|expected)_[A-Za-z0-9_]+)"', source))

    assert keys
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = _read_locale(locale)
        missing = sorted(keys - set(catalog))
        assert missing == []


def test_profile_data_error_pipeline_does_not_surface_raw_unknown_payloads():
    source = DATA_SOURCE.read_text(encoding="utf-8")

    assert "return { message: raw," not in source
    assert 'translateDataMessage("profiles.error_api_unknown"' in source
    assert "API_ERROR_MESSAGE_KEYS" in source
