from __future__ import annotations

from typing import Any


FALLBACK_SECTION_MAPPINGS: dict[str, dict[str, tuple[str, list[str]]]] = {
    "browser_behavior": {
        "AllowFileSelectionDialogs": ("files", ["files"]),
        "BrowserDataBackup": ("downloads", ["backup"]),
        "DisableProfileImport": ("startup", ["profiles"]),
        "DisplayBookmarksToolbar": ("appearance", ["bookmarks", "ui"]),
        "DisplayMenuBar": ("appearance", ["ui"]),
        "DownloadDirectory": ("downloads", ["downloads"]),
        "HardwareAcceleration": ("performance", ["performance"]),
        "OverrideFirstRunPage": ("startup", ["startup"]),
        "OverridePostUpdatePage": ("startup", ["startup", "updates"]),
        "ShowHomeButton": ("appearance", ["ui", "home"]),
    },
    "home_startup": {
        "NewTabPage": ("new_tab", ["new-tab"]),
        "NoDefaultBookmarks": ("homepage", ["bookmarks", "startup"]),
    },
    "search": {
        "DisableFirefoxScreenshots": ("search_ui", ["screenshots"]),
    },
    "network_access": {
        "AutoLaunchProtocolsFromOrigins": ("protocol_handlers", ["protocols"]),
        "CaptivePortal": ("network", ["network"]),
        "HttpAllowlist": ("network", ["network"]),
        "NetworkPrediction": ("network", ["network", "privacy"]),
        "SecurityDevices": ("certificates", ["pkcs11", "security"]),
        "SSLVersionMax": ("tls", ["tls"]),
        "SSLVersionMin": ("tls", ["tls"]),
        "SupportMenu": ("support", ["support"]),
    },
    "privacy_security": {
        "AutofillAddressEnabled": ("forms", ["autofill"]),
        "AutofillCreditCardEnabled": ("forms", ["autofill"]),
        "BlockAboutAddons": ("lockdown", ["about-pages"]),
        "BlockAboutConfig": ("lockdown", ["about-pages"]),
        "BlockAboutProfiles": ("lockdown", ["about-pages"]),
        "BlockAboutSupport": ("lockdown", ["about-pages"]),
        "BlockMultipleContentProcesses": ("lockdown", ["processes"]),
        "Cookies": ("cookies", ["cookies"]),
        "DisableFeedbackCommands": ("lockdown", ["feedback"]),
        "DisableForgetButton": ("history", ["history"]),
        "DisableFormHistory": ("forms", ["history", "forms"]),
        "DisableMasterPasswordCreation": ("passwords", ["passwords"]),
        "DisablePasswordReveal": ("passwords", ["passwords"]),
        "EnableTrackingProtection": ("tracking", ["tracking"]),
        "EncryptedMediaExtensions": ("security", ["drm"]),
        "ExemptDomainFileTypePairsFromFileTypeDownloadWarnings": ("downloads", ["downloads", "warnings"]),
        "PDFjs": ("security", ["pdf"]),
        "PictureInPicture": ("surfaces", ["video"]),
        "PostQuantumKeyAgreementEnabled": ("security", ["tls"]),
        "PrimaryPassword": ("passwords", ["passwords"]),
    },
    "extensions_integrations": {
        "Containers": ("containers", ["containers"]),
        "ContentAnalysis": ("content_analysis", ["content-analysis"]),
        "DisabledCiphers": ("security", ["tls", "ciphers"]),
        "Handlers": ("protocol_handlers", ["handlers"]),
        "LegacyProfiles": ("profiles", ["profiles"]),
        "LocalFileLinks": ("content_filtering", ["links"]),
        "OfferToSaveLoginsDefault": ("passwords", ["passwords"]),
        "PasswordManagerExceptions": ("passwords", ["passwords"]),
    },
}


def infer_widget(policy_type: str, schema_node: dict[str, Any] | None) -> str:
    node = schema_node or {}

    if isinstance(node.get("oneOf"), list):
        return "branch"

    if policy_type == "boolean":
        return "toggle"
    if policy_type in {"integer", "number"}:
        return "number"
    if policy_type == "string":
        return "enum-select" if isinstance(node.get("enum"), list) else "text"
    if policy_type == "array":
        items = node.get("items") if isinstance(node.get("items"), dict) else {}
        if isinstance(items.get("properties"), dict):
            return "array-of-objects"
        return "list"
    if policy_type == "object":
        properties = node.get("properties")
        additional_properties = node.get("additionalProperties")
        if isinstance(additional_properties, dict):
            return "dictionary"
        if isinstance(properties, dict) and properties:
            return "object-card"
        return "dictionary"
    return "raw-json"


def preserve_unknown_fields(schema_node: dict[str, Any] | None) -> bool:
    node = schema_node or {}
    additional_properties = node.get("additionalProperties")
    return isinstance(additional_properties, dict) or additional_properties is True


def infer_section(policy_id: str) -> tuple[str, str, list[str]]:
    for section_id, mapping in FALLBACK_SECTION_MAPPINGS.items():
        if policy_id in mapping:
            subsection, tags = mapping[policy_id]
            return section_id, subsection, tags

    return "advanced", "unmapped", ["fallback"]
