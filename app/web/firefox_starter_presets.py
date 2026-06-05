from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.compliance.firefox.cis.generation import build_cis_layer
from app.compliance.firefox.cis.merge import merge_base_with_cis_layer
from app.compliance.firefox.cis.validation import BASE_DIR as CIS_BASE_DIR
from app.compliance.firefox.cis.validation import load_yaml_file
from app.core.schema_channels import CURRENT_RELEASE_SCHEMA_CHANNEL, SUPPORTED_SCHEMA_CHANNELS
from app.services.policy_schema_service import get_policy_definition

SUPPORTED_POLICY_CHANNELS = SUPPORTED_SCHEMA_CHANNELS
SCHEMA_ENABLED = "__SCHEMA_ENABLED__"

CIS_LAYER_NONE = "none"
CIS_LAYER_LEVEL_1 = "cis_l1"
CIS_LAYER_LEVEL_2 = "cis_l2"
CIS_LAYER_OPTIONS: dict[str, dict[str, Any]] = {
    CIS_LAYER_NONE: {
        "level": None,
        "label_key": "profiles.wizard_cis_none_title",
        "summary_key": "profiles.wizard_cis_none_summary",
    },
    CIS_LAYER_LEVEL_1: {
        "level": 1,
        "label_key": "profiles.wizard_cis_l1_title",
        "summary_key": "profiles.wizard_cis_l1_summary",
    },
    CIS_LAYER_LEVEL_2: {
        "level": 2,
        "label_key": "profiles.wizard_cis_l2_title",
        "summary_key": "profiles.wizard_cis_l2_summary",
    },
}

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

_CLASSROOM_KIOSK_EXTENSIONS: dict[str, Any] = {
    **_BLOCK_ALL_EXTENSIONS,
    "uBlock0@raymondhill.net": {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
    },
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
                "https://kb.example.local/",
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
                "ExtensionSettings": _CLASSROOM_KIOSK_EXTENSIONS,
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
    for schema_version in SUPPORTED_POLICY_CHANNELS:
        for level in (1, 2):
            keys.update(build_cis_layer(level, schema_version).policies.keys())
    keys.update({"Homepage", "Proxy"})
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
                    CURRENT_RELEASE_SCHEMA_CHANNEL,
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

    compliance_presets = _build_compliance_presets()
    quick_policy_enabled_values = {
        "DisablePocket": {
            schema_version: _resolve_schema_enabled_value("DisablePocket", schema_version)
            for schema_version in SUPPORTED_POLICY_CHANNELS
        }
    }

    return {
        "managed_policy_keys": _collect_managed_policy_keys(),
        "presets": resolved_presets,
        "compliance_layers": deepcopy(CIS_LAYER_OPTIONS),
        "compliance_merged_presets": compliance_presets,
        "compliance_metadata": _load_cis_benchmark_metadata(),
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


def _build_compliance_presets() -> dict[str, dict[str, dict[str, Any]]]:
    presets: dict[str, dict[str, dict[str, Any]]] = {}
    cis_layers = {
        (schema_version, level): build_cis_layer(level, schema_version)
        for schema_version in SUPPORTED_POLICY_CHANNELS
        for level in (1, 2)
    }

    for starter_key in _STARTER_PRESETS:
        layer_variants: dict[str, dict[str, Any]] = {}
        for layer_key, layer_config in CIS_LAYER_OPTIONS.items():
            schema_variants: dict[str, Any] = {}
            for schema_version in SUPPORTED_POLICY_CHANNELS:
                base_document = build_wizard_starter_document(starter_key, schema_version)
                if layer_key == CIS_LAYER_NONE or starter_key == "keep_current":
                    schema_variants[schema_version] = {
                        "policy_values": deepcopy(base_document),
                        "summary": {},
                        "review_required": 0,
                    }
                    continue

                cis_layer = cis_layers[(schema_version, int(layer_config["level"]))]
                merge_result = merge_base_with_cis_layer(
                    base_document,
                    cis_layer,
                    base_label=starter_key,
                    cis_label=layer_key,
                )
                schema_variants[schema_version] = {
                    "policy_values": merge_result.effective_policies,
                    "summary": merge_result.summary,
                    "decisions": [
                        {
                            "path": decision.to_dict()["path"],
                            "decision": decision.decision,
                            "selected_source": decision.selected_source,
                            "recommendation_ids": list(decision.recommendation_ids),
                            "review_required": decision.review_required,
                            "reason": decision.reason,
                        }
                        for decision in merge_result.decisions
                    ],
                    "review_required": merge_result.summary.get("review_required", 0),
                }
            layer_variants[layer_key] = schema_variants
        presets[starter_key] = layer_variants

    return presets


def _load_cis_benchmark_metadata() -> dict[str, Any]:
    sources = load_yaml_file(CIS_BASE_DIR / "sources.yaml")
    benchmarks = sources.get("benchmarks", [])
    if not isinstance(benchmarks, list) or not benchmarks:
        return {}
    benchmark = benchmarks[0] if isinstance(benchmarks[0], dict) else {}
    return {
        "benchmark_id": benchmark.get("id"),
        "upstream_name": benchmark.get("upstream_name"),
        "upstream_version": benchmark.get("upstream_version"),
        "exact_release_date": benchmark.get("exact_release_date"),
        "source_license": benchmark.get("source_license"),
        "source_terms_url": benchmark.get("source_terms_url"),
    }
