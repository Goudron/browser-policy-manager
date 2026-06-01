import json
import re
import subprocess
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[1]
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


def test_profile_data_common_api_errors_are_locale_backed(tmp_path):
    source = DATA_SOURCE.read_text(encoding="utf-8")
    ru_catalog = _read_locale("ru")
    script = f"""
const vm = require("node:vm");
const source = {json.dumps(source)};
const context = {{
  window: {{
    __BPM_INITIAL_LOCALE__: {json.dumps(ru_catalog, ensure_ascii=False)},
  }},
}};
vm.createContext(context);
vm.runInContext(source, context);
const data = context.window.BPMProfilesData;

try {{
  data.fromEditorValue("[]", "json");
  throw new Error("array root did not fail");
}} catch (error) {{
  if (!String(error.message).includes("Ожидался корневой объект policies.json")) {{
    throw error;
  }}
}}

(async () => {{
  const conflictMessage = await data.readError({{
    text: async () => JSON.stringify({{ detail: "Profile with this name already exists" }}),
  }});
  if (conflictMessage !== "Профиль с таким именем уже существует.") {{
    throw new Error(`unexpected conflict message: ${{conflictMessage}}`);
  }}

  const schemaMessage = await data.readError({{
    text: async () => JSON.stringify({{ detail: "Schema for profile 'release-999' is not available" }}),
  }});
  if (schemaMessage !== "Схема для профиля release-999 недоступна.") {{
    throw new Error(`unexpected schema message: ${{schemaMessage}}`);
  }}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""

    script_path = tmp_path / "profile_data_error_i18n.js"
    script_path.write_text(script, encoding="utf-8")

    subprocess.run(
        ["node", str(script_path)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_profile_data_error_pipeline_does_not_surface_raw_unknown_payloads():
    source = DATA_SOURCE.read_text(encoding="utf-8")

    assert 'return { message: raw,' not in source
    assert 'translateDataMessage("profiles.error_api_unknown"' in source
    assert "API_ERROR_MESSAGE_KEYS" in source
