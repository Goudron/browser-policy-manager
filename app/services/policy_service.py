import json
from typing import Any

ALLOWED_FLAGS = {
    "DisableTelemetry",
    "DisablePocket",
    "DisableFirefoxStudies",
    "DisableFirefoxAccounts",
    "DontCheckDefaultBrowser",
    "OfferToSaveLoginsDefault",
    "PasswordManagerEnabled",
}


def _safe_load_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


class PolicyService:
    @staticmethod
    def build_payload(data: dict[str, Any]) -> dict[str, Any]:
        """
        Собирает итоговый объект policies.json из структур формы.
        Ожидаемые ключи в data:
          - flags: Dict[str, bool]
          - doh: Dict[str, Any]  -> {"Enabled": bool, "ProviderURL": str, "Locked": bool}
          - preferences_json: str (JSON)
          - extension_settings_json: str (JSON)
          - advanced_json: str (JSON)  -> «поверх» всего, последний перезаписывает ключи
        """
        policies: dict[str, Any] = {}

        # 1) Флаги
        flags = data.get("flags") or {}
        for k, v in flags.items():
            if k in ALLOWED_FLAGS and isinstance(v, bool):
                policies[k] = v

        # 2) DoH
        doh = data.get("doh")
        if isinstance(doh, dict):
            # фильтруем только поддерживаемые поля
            doh_out: dict[str, Any] = {}
            if isinstance(doh.get("Enabled"), bool):
                doh_out["Enabled"] = doh["Enabled"]
            if isinstance(doh.get("ProviderURL"), str) and doh["ProviderURL"].strip():
                doh_out["ProviderURL"] = doh["ProviderURL"].strip()
            if isinstance(doh.get("Locked"), bool):
                doh_out["Locked"] = doh["Locked"]
            if doh_out:
                policies["DNSOverHTTPS"] = doh_out

        # 3) Preferences
        prefs_obj = _safe_load_json(data.get("preferences_json"))
        if isinstance(prefs_obj, dict) and prefs_obj:
            policies["Preferences"] = prefs_obj

        # 4) ExtensionSettings
        ext_obj = _safe_load_json(data.get("extension_settings_json"))
        if isinstance(ext_obj, dict) and ext_obj:
            policies["ExtensionSettings"] = ext_obj

        # 5) Advanced (поверх всего)
        adv_obj = _safe_load_json(data.get("advanced_json"))
        if isinstance(adv_obj, dict) and adv_obj:
            # внимание: перезапишет существующие ключи policies
            policies.update(adv_obj)

        return {"policies": policies}
