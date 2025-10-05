from typing import Dict, Any

ALLOWED_FLAGS = {
    "DisableTelemetry", "DisablePocket", "DisableFirefoxStudies",
    "DisableFirefoxAccounts", "DontCheckDefaultBrowser",
    "OfferToSaveLoginsDefault", "PasswordManagerEnabled",
}

class PolicyService:
    @staticmethod
    def build_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        policies: Dict[str, Any] = {}

        flags = data.get("flags") or {}
        for k, v in flags.items():
            if k in ALLOWED_FLAGS and isinstance(v, bool):
                policies[k] = v

        if data.get("dns_over_https"):
            policies["DNSOverHTTPS"] = data["dns_over_https"]

        if data.get("preferences"):
            policies["Preferences"] = data["preferences"]

        if data.get("extension_settings"):
            policies["ExtensionSettings"] = data["extension_settings"]

        if data.get("extra"):
            # осторожно: extra перезаписывает ключи
            policies.update(data["extra"])

        return {"policies": policies}
