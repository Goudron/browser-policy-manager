from __future__ import annotations

from app.web.firefox_all_settings_categories import get_all_settings_category_catalog


def test_all_settings_category_catalog_is_domain_first():
    catalog = get_all_settings_category_catalog()
    categories = catalog["categories"]

    assert [category["id"] for category in categories] == [
        "browser-access",
        "home-startup",
        "search-navigation",
        "privacy-security",
        "users-addons-sites",
        "ai-smart-features",
        "raw-unmapped",
    ]
    assert [category["policy_section_ids"] for category in categories] == [
        ["browser_behavior", "network_access"],
        ["home_startup"],
        ["search"],
        ["privacy_security"],
        ["extensions_integrations"],
        ["ai_smart"],
        ["advanced"],
    ]
    assert all("step" not in key for category in categories for key in category)


def test_all_settings_category_catalog_maps_existing_sections_without_guided_steps():
    catalog = get_all_settings_category_catalog()

    assert catalog["settings_section_to_category_id"] == {
        "general": "browser-access",
        "home": "home-startup",
        "search": "search-navigation",
        "privacy": "privacy-security",
        "sync": "users-addons-sites",
    }
    assert catalog["preference_section_to_category_id"] == {
        "general": "browser-access",
        "home": "home-startup",
        "search": "search-navigation",
        "privacy": "privacy-security",
        "sync": "users-addons-sites",
    }
    assert catalog["schema_shell_steps_by_category_id"]["browser-access"] == [2]
    assert catalog["schema_shell_steps_by_category_id"]["raw-unmapped"] == [8]
