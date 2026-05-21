from __future__ import annotations

from typing import Any

_ALL_SETTINGS_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "id": "browser-access",
        "title_key": "profiles.settings_category_browser_access_title",
        "fallback": "Browser behavior & access",
        "body_key": "profiles.settings_category_browser_access_body",
        "body_fallback": "Core browser behavior, downloads, updates, proxy, authentication, and enterprise access.",
        "settings_section_ids": ["general"],
        "preference_section_ids": ["general"],
        "policy_section_ids": ["browser_behavior", "network_access"],
    },
    {
        "id": "home-startup",
        "title_key": "profiles.settings_category_home_startup_title",
        "fallback": "Home & startup",
        "body_key": "profiles.settings_category_home_startup_body",
        "body_fallback": "Homepage, new-tab behavior, startup pages, and Firefox Home surfaces.",
        "settings_section_ids": ["home"],
        "preference_section_ids": ["home"],
        "policy_section_ids": ["home_startup"],
    },
    {
        "id": "search-navigation",
        "title_key": "profiles.settings_category_search_navigation_title",
        "fallback": "Search & navigation",
        "body_key": "profiles.settings_category_search_navigation_body",
        "body_fallback": "Default engines, managed search, suggestions, and address-bar behavior.",
        "settings_section_ids": ["search"],
        "preference_section_ids": ["search"],
        "policy_section_ids": ["search"],
    },
    {
        "id": "privacy-security",
        "title_key": "profiles.settings_category_privacy_security_title",
        "fallback": "Security & privacy",
        "body_key": "profiles.settings_category_privacy_security_body",
        "body_fallback": "Telemetry, permissions, cookies, site data, hardening, and cleanup controls.",
        "settings_section_ids": ["privacy"],
        "preference_section_ids": ["privacy"],
        "policy_section_ids": ["privacy_security"],
    },
    {
        "id": "users-addons-sites",
        "title_key": "profiles.settings_category_users_addons_sites_title",
        "fallback": "Users, add-ons & sites",
        "body_key": "profiles.settings_category_users_addons_sites_body",
        "body_fallback": "Mozilla accounts, language, add-ons, bookmarks, handlers, and website controls.",
        "settings_section_ids": ["sync"],
        "preference_section_ids": ["sync"],
        "policy_section_ids": ["extensions_integrations"],
    },
    {
        "id": "ai-smart-features",
        "title_key": "profiles.settings_category_ai_smart_features_title",
        "fallback": "AI & smart features",
        "body_key": "profiles.settings_category_ai_smart_features_body",
        "body_fallback": "AI controls, generative features, visual search, and related smart surfaces.",
        "settings_section_ids": [],
        "preference_section_ids": [],
        "policy_section_ids": ["ai_smart"],
    },
    {
        "id": "raw-unmapped",
        "title_key": "profiles.settings_category_raw_unmapped_title",
        "fallback": "Raw & unmapped",
        "body_key": "profiles.settings_category_raw_unmapped_body",
        "body_fallback": "Schema-backed items that stay outside the guided surfaces or need raw review.",
        "settings_section_ids": [],
        "preference_section_ids": [],
        "policy_section_ids": ["advanced"],
    },
)

_SCHEMA_SHELL_STEP_BY_POLICY_SECTION = {
    "browser_behavior": 2,
    "network_access": 2,
    "home_startup": 3,
    "search": 4,
    "privacy_security": 5,
    "extensions_integrations": 6,
    "ai_smart": 7,
    "advanced": 8,
}


def get_all_settings_category_catalog() -> dict[str, Any]:
    """Return the domain-first category model used by the All settings route."""

    categories = [
        {
            **category,
            "settings_section_ids": list(category["settings_section_ids"]),
            "preference_section_ids": list(category["preference_section_ids"]),
            "policy_section_ids": list(category["policy_section_ids"]),
        }
        for category in _ALL_SETTINGS_CATEGORIES
    ]

    return {
        "categories": categories,
        "categories_by_id": {category["id"]: category for category in categories},
        "settings_section_to_category_id": {
            section_id: category["id"]
            for category in categories
            for section_id in category["settings_section_ids"]
        },
        "preference_section_to_category_id": {
            section_id: category["id"]
            for category in categories
            for section_id in category["preference_section_ids"]
        },
        "policy_section_to_category_id": {
            section_id: category["id"]
            for category in categories
            for section_id in category["policy_section_ids"]
        },
        "schema_shell_steps_by_category_id": {
            category["id"]: sorted(
                {
                    _SCHEMA_SHELL_STEP_BY_POLICY_SECTION[section_id]
                    for section_id in category["policy_section_ids"]
                    if section_id in _SCHEMA_SHELL_STEP_BY_POLICY_SECTION
                }
            )
            for category in categories
        },
    }
