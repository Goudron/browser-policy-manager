from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.policy_schema_service import get_policy_definition

SUPPORTED_POLICY_CHANNELS = ("esr-140", "release-148")
SCHEMA_ENABLED = "__SCHEMA_ENABLED__"

_LOCKED_ENTERPRISE_HOME: dict[str, Any] = {
    "Search": True,
    "TopSites": False,
    "SponsoredTopSites": False,
    "Highlights": False,
    "Pocket": False,
    "SponsoredPocket": False,
    "Snippets": False,
    "Stories": False,
    "SponsoredStories": False,
    "Locked": True,
}

_LOCKED_NO_SUGGEST: dict[str, Any] = {
    "WebSuggestions": False,
    "SponsoredSuggestions": False,
    "ImproveSuggest": False,
    "Locked": True,
}

_LOCKED_NO_USER_MESSAGING: dict[str, Any] = {
    "ExtensionRecommendations": False,
    "FeatureRecommendations": False,
    "UrlbarInterventions": False,
    "SkipOnboarding": True,
    "MoreFromMozilla": False,
    "FirefoxLabs": False,
    "Locked": True,
}

_STRICT_TRACKING_PROTECTION: dict[str, Any] = {
    "Value": True,
    "Locked": True,
    "Cryptomining": True,
    "Fingerprinting": True,
    "EmailTracking": True,
    "SuspectedFingerprinting": True,
    "Category": "strict",
    "BaselineExceptions": False,
    "ConvenienceExceptions": False,
}

_BLOCK_ALL_EXTENSIONS: dict[str, Any] = {
    "*": {
        "installation_mode": "blocked",
    }
}

_LOCKED_POPUP_BLOCKING: dict[str, Any] = {
    "Default": True,
    "Locked": True,
}


_STARTER_PRESETS: dict[str, dict[str, Any]] = {
    "blank": {
        "policy_values": {},
        "homepage": {},
        "proxy": {},
    },
    "keep_current": {
        "policy_values": {},
        "homepage": {},
        "proxy": {},
    },
    "basic_corporate": {
        "policy_values": {
            "default": {
                "AppAutoUpdate": False,
                "DisableAppUpdate": True,
                "DisableSystemAddonUpdate": True,
                "DisableTelemetry": True,
                "DisableFirefoxAccounts": True,
                "DisablePocket": SCHEMA_ENABLED,
                "BlockAboutConfig": True,
                "BlockAboutProfiles": True,
                "DisableFirefoxStudies": True,
                "DisableProfileImport": True,
                "DisableProfileRefresh": True,
                "PasswordManagerEnabled": False,
                "OfferToSaveLogins": False,
                "Certificates": {
                    "ImportEnterpriseRoots": True,
                },
                "DNSOverHTTPS": {
                    "Enabled": False,
                    "Locked": True,
                },
                "EnableTrackingProtection": _STRICT_TRACKING_PROTECTION,
                "ExtensionSettings": _BLOCK_ALL_EXTENSIONS,
                "FirefoxHome": _LOCKED_ENTERPRISE_HOME,
                "FirefoxSuggest": _LOCKED_NO_SUGGEST,
                "UserMessaging": _LOCKED_NO_USER_MESSAGING,
                "PopupBlocking": _LOCKED_POPUP_BLOCKING,
            },
        },
        "homepage": {
            "URL": "https://intranet.example.local/",
            "Additional": [
                "https://helpdesk.example.local/",
                "https://docs.example.local/",
            ],
            "Locked": True,
            "StartPage": "homepage-locked",
        },
        "proxy": {
            "Mode": "system",
            "Locked": True,
        },
    },
    "classroom_kiosk": {
        "policy_values": {
            "default": {
                "DisablePrivateBrowsing": True,
                "DisableDeveloperTools": True,
                "DisableFirefoxAccounts": True,
                "DisablePocket": SCHEMA_ENABLED,
                "BlockAboutConfig": True,
                "BlockAboutAddons": True,
                "BlockAboutProfiles": True,
                "BlockAboutSupport": True,
                "DisableFirefoxStudies": True,
                "DisableProfileImport": True,
                "DisableProfileRefresh": True,
                "PromptForDownloadLocation": True,
                "ExtensionSettings": _BLOCK_ALL_EXTENSIONS,
                "FirefoxHome": _LOCKED_ENTERPRISE_HOME,
                "FirefoxSuggest": _LOCKED_NO_SUGGEST,
                "UserMessaging": _LOCKED_NO_USER_MESSAGING,
                "InstallAddonsPermission": {
                    "Default": False,
                },
                "Permissions": {
                    "Camera": {
                        "Allow": [
                            "https://classroom.example.local",
                            "https://lms.example.local",
                        ],
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Microphone": {
                        "Allow": [
                            "https://classroom.example.local",
                            "https://lms.example.local",
                        ],
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Location": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Notifications": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "ScreenShare": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "VirtualReality": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Autoplay": {
                        "Default": "block-audio-video",
                        "Locked": True,
                    },
                },
                "PopupBlocking": _LOCKED_POPUP_BLOCKING,
                "WebsiteFilter": {
                    "Block": ["<all_urls>"],
                    "Exceptions": [
                        "https://start.school.local/*",
                        "https://classroom.example.local/*",
                        "https://lms.example.local/*",
                    ],
                },
            },
        },
        "homepage": {
            "URL": "https://start.school.local/",
            "Additional": [
                "https://classroom.example.local/",
                "https://lms.example.local/",
            ],
            "Locked": True,
            "StartPage": "homepage-locked",
        },
        "proxy": {
            "Mode": "system",
            "Locked": True,
        },
    },
    "soc_hard": {
        "policy_values": {
            "default": {
                "AppAutoUpdate": False,
                "DisableAppUpdate": True,
                "DisableSystemAddonUpdate": True,
                "BlockAboutConfig": True,
                "BlockAboutAddons": True,
                "BlockAboutProfiles": True,
                "BlockAboutSupport": True,
                "DisableDeveloperTools": True,
                "DisableFirefoxAccounts": True,
                "DisablePocket": SCHEMA_ENABLED,
                "DisableFirefoxStudies": True,
                "DisablePrivateBrowsing": True,
                "DisableProfileImport": True,
                "DisableProfileRefresh": True,
                "Certificates": {
                    "ImportEnterpriseRoots": True,
                },
                "Cookies": {
                    "Behavior": "reject-tracker-and-partition-foreign",
                    "BehaviorPrivateBrowsing": "reject-tracker-and-partition-foreign",
                    "Locked": True,
                },
                "DNSOverHTTPS": {
                    "Enabled": True,
                    "ProviderURL": "https://dns.example.secure/dns-query",
                    "Fallback": False,
                    "Locked": True,
                },
                "EnableTrackingProtection": _STRICT_TRACKING_PROTECTION,
                "ExtensionSettings": _BLOCK_ALL_EXTENSIONS,
                "FirefoxHome": _LOCKED_ENTERPRISE_HOME,
                "FirefoxSuggest": _LOCKED_NO_SUGGEST,
                "HttpsOnlyMode": "force_enabled",
                "InstallAddonsPermission": {
                    "Default": False,
                },
                "Permissions": {
                    "Camera": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Microphone": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Location": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Notifications": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "ScreenShare": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "VirtualReality": {
                        "BlockNewRequests": True,
                        "Locked": True,
                    },
                    "Autoplay": {
                        "Default": "block-audio-video",
                        "Locked": True,
                    },
                },
                "PopupBlocking": _LOCKED_POPUP_BLOCKING,
                "SanitizeOnShutdown": {
                    "Cache": True,
                    "Cookies": True,
                    "FormData": True,
                    "History": True,
                    "Sessions": True,
                    "SiteSettings": True,
                    "Locked": True,
                },
                "UserMessaging": _LOCKED_NO_USER_MESSAGING,
            },
        },
        "homepage": {},
        "proxy": {
            "Mode": "manual",
            "HTTPProxy": "proxy.sec.local:3128",
            "SSLProxy": "proxy.sec.local:3128",
            "UseHTTPProxyForAllProtocols": True,
            "Passthrough": "localhost, 127.0.0.1",
            "Locked": True,
        },
    },
}


def _collect_managed_policy_keys() -> list[str]:
    keys: set[str] = set()
    for preset in _STARTER_PRESETS.values():
        for policy_values in preset.get("policy_values", {}).values():
            keys.update(policy_values.keys())
    return sorted(keys)


def _resolve_schema_enabled_value(policy_id: str, schema_version: str) -> Any:
    definition = get_policy_definition(schema_version, policy_id)
    if definition is None:
        return True
    if definition.type == "object":
        return {}
    if definition.type == "array":
        return []
    if definition.type == "string":
        return ""
    if definition.type in {"integer", "number"}:
        return 1
    return True


def _resolve_policy_values_for_channel(
    policy_values: dict[str, Any],
    schema_version: str,
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for policy_id, value in policy_values.items():
        if value == SCHEMA_ENABLED:
            resolved[policy_id] = _resolve_schema_enabled_value(policy_id, schema_version)
        else:
            resolved[policy_id] = deepcopy(value)
    return resolved


def get_wizard_starter_catalog() -> dict[str, Any]:
    resolved_presets: dict[str, dict[str, Any]] = {}
    for preset_key, preset in _STARTER_PRESETS.items():
        resolved_preset = {
            "policy_values": {
                "default": _resolve_policy_values_for_channel(
                    preset.get("policy_values", {}).get("default", {}),
                    "release-148",
                ),
            },
            "homepage": deepcopy(preset.get("homepage", {})),
            "proxy": deepcopy(preset.get("proxy", {})),
        }
        for schema_version in SUPPORTED_POLICY_CHANNELS:
            resolved_preset["policy_values"][schema_version] = _resolve_policy_values_for_channel(
                preset.get("policy_values", {}).get("default", {}),
                schema_version,
            )
            resolved_preset["policy_values"][schema_version].update(
                _resolve_policy_values_for_channel(
                    preset.get("policy_values", {}).get(schema_version, {}),
                    schema_version,
                )
            )
        resolved_presets[preset_key] = resolved_preset

    quick_policy_enabled_values = {
        "DisablePocket": {
            schema_version: _resolve_schema_enabled_value("DisablePocket", schema_version)
            for schema_version in SUPPORTED_POLICY_CHANNELS
        }
    }

    return {
        "managed_policy_keys": _collect_managed_policy_keys(),
        "presets": resolved_presets,
        "quick_policy_enabled_values": quick_policy_enabled_values,
    }


def resolve_wizard_starter_policy_values(
    starter_key: str,
    schema_version: str,
) -> dict[str, Any]:
    preset = _STARTER_PRESETS.get(starter_key, {})
    policy_values = preset.get("policy_values", {})
    resolved = _resolve_policy_values_for_channel(policy_values.get("default", {}), schema_version)
    resolved.update(_resolve_policy_values_for_channel(policy_values.get(schema_version, {}), schema_version))
    return resolved


def build_wizard_starter_document(
    starter_key: str,
    schema_version: str,
) -> dict[str, Any]:
    preset = _STARTER_PRESETS.get(starter_key, {})
    document = resolve_wizard_starter_policy_values(starter_key, schema_version)

    homepage = deepcopy(preset.get("homepage", {}))
    proxy = deepcopy(preset.get("proxy", {}))

    if homepage:
        document["Homepage"] = homepage
    if proxy:
        document["Proxy"] = proxy

    return document
