"""Authoritative, schema-neutral Firefox starter catalog definitions.

The Guided web surface and server-side profile preparation both resolve this
catalog.  Keeping immutable definitions below the web/service boundary means a
future preparation command can rederive a selected starter without trusting a
browser-composed policy document.
"""

from __future__ import annotations

from typing import Any

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

ESR_115_PRESET_POLICY_EXCLUSIONS = frozenset({"FirefoxSuggest", "HttpsOnlyMode"})
ESR_115_PRESET_NESTED_EXCLUSIONS: dict[str, frozenset[str]] = {
    "EnableTrackingProtection": frozenset(
        {"BaselineExceptions", "Category", "ConvenienceExceptions", "SuspectedFingerprinting"}
    ),
    "FirefoxHome": frozenset({"SponsoredStories", "Stories"}),
    "Permissions": frozenset({"ScreenShare", "VirtualReality"}),
    "UserMessaging": frozenset({"FirefoxLabs"}),
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
        "install_url": (
            "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
        ),
    },
}

_LOCKED_POPUP_BLOCKING: dict[str, Any] = {
    "Default": True,
    "Locked": True,
}


STARTER_PRESETS: dict[str, dict[str, Any]] = {
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
