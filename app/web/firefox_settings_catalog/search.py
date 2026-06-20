from __future__ import annotations

from typing import Any

from .builders import chip, control_target, known_pref, pref_control, preset


def get_search_section() -> dict[str, Any]:
    return {
        "id": "search",
        "ui_maps": {
            "search": [
                chip("default_engine", "profiles.wizard_settings_search_default_engine", "Default search engine"),
                chip("suggestions", "profiles.wizard_settings_search_suggestions", "Search suggestions"),
                chip("address_bar", "profiles.wizard_settings_search_address_bar", "Address bar"),
            ],
            "suggest": [
                chip("address_bar", "profiles.wizard_settings_search_address_bar", "Address bar"),
                chip("suggestions", "profiles.wizard_settings_search_suggestions", "Search suggestions"),
            ],
        },
        "ui_controls": {
            "search": [
                control_target("default_engine", "field:wizard-search-default-engine", "profiles.wizard_search_default_engine_label", "Default search engine"),
                control_target("default_engine", "field:wizard-search-prevent-installs", "profiles.wizard_search_prevent_installs_label", "Engine installs from web pages"),
                control_target("default_engine", "field:wizard-search-remove", "profiles.wizard_search_remove_label", "Hide built-in search engines"),
                control_target("address_bar", "field:wizard-search-bar", "profiles.wizard_search_bar_label", "Search bar layout"),
                control_target("suggestions", "field:wizard-search-suggest", "profiles.wizard_search_suggest_label", "Search suggestions"),
            ],
            "suggest": [
                control_target("address_bar", "field:firefox-suggest-web", "profiles.wizard_firefox_suggest_web_label", "Web suggestions"),
                control_target("suggestions", "field:firefox-suggest-sponsored", "profiles.wizard_firefox_suggest_sponsored_label", "Sponsored suggestions"),
                control_target("suggestions", "field:firefox-suggest-improve", "profiles.wizard_firefox_suggest_improve_label", "Improve Suggest"),
                control_target("suggestions", "field:firefox-suggest-locked", "profiles.wizard_firefox_suggest_locked_label", "Lock Firefox Suggest"),
            ],
        },
        "preferences": {
            "id": "search",
            "title_key": "profiles.wizard_preferences_search_title",
            "body_key": "profiles.wizard_preferences_search_body",
            "gui_groups": [
                chip("engine", "profiles.wizard_preferences_group_search_engine", "Default search engine"),
                chip("suggestions", "profiles.wizard_preferences_group_search_suggestions", "Search suggestions"),
                chip("address_bar", "profiles.wizard_preferences_group_search_address_bar", "Address bar"),
                chip("shortcuts", "profiles.wizard_preferences_group_search_shortcuts", "Search shortcuts"),
            ],
            "controls": [
                pref_control("suggestions", "search_suggest", "profiles.wizard_preferences_preset_search_suggest_title", "Enable search suggestions"),
                pref_control("address_bar", "search_bookmarks", "profiles.wizard_preferences_preset_search_bookmarks_title", "Suggest bookmarks in address bar"),
                pref_control("address_bar", "search_history", "profiles.wizard_preferences_preset_search_history_title", "Suggest history in address bar"),
                pref_control("address_bar", "search_open_tabs", "profiles.wizard_preferences_preset_search_open_tabs_title", "Suggest open tabs in address bar"),
                pref_control("address_bar", "search_topsites", "profiles.wizard_preferences_preset_search_topsites_title", "Suggest top sites in address bar"),
                pref_control("shortcuts", "search_keywords", "profiles.wizard_preferences_preset_search_keywords_title", "Enable keyword search"),
            ],
            "prefixes": [
                "browser.search.",
                "browser.urlbar.",
                "keyword.enabled",
            ],
            "presets": [
                preset("search_suggest", "browser.search.suggest.enabled", True, "default", "boolean", "profiles.wizard_preferences_preset_search_suggest_title", "profiles.wizard_preferences_preset_search_suggest_copy"),
                preset("search_bookmarks", "browser.urlbar.suggest.bookmark", True, "default", "boolean", "profiles.wizard_preferences_preset_search_bookmarks_title", "profiles.wizard_preferences_preset_search_bookmarks_copy"),
                preset("search_history", "browser.urlbar.suggest.history", True, "default", "boolean", "profiles.wizard_preferences_preset_search_history_title", "profiles.wizard_preferences_preset_search_history_copy"),
                preset("search_open_tabs", "browser.urlbar.suggest.openpage", True, "default", "boolean", "profiles.wizard_preferences_preset_search_open_tabs_title", "profiles.wizard_preferences_preset_search_open_tabs_copy"),
                preset("search_topsites", "browser.urlbar.suggest.topsites", True, "default", "boolean", "profiles.wizard_preferences_preset_search_topsites_title", "profiles.wizard_preferences_preset_search_topsites_copy"),
                preset("search_keywords", "keyword.enabled", True, "default", "boolean", "profiles.wizard_preferences_preset_search_keywords_title", "profiles.wizard_preferences_preset_search_keywords_copy"),
            ],
            "known_preferences": [
                known_pref(
                    "browser.urlbar.suggest.searches",
                    "Searches in address bar",
                    "Controls whether the address bar shows provider-backed search suggestions.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.urlbar.showSearchSuggestionsFirst",
                    "Search suggestions first",
                    "Moves search suggestions ahead of history and bookmark matches in the address bar.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.urlbar.trimURLs",
                    "Trim URLs",
                    "Hides the protocol and trailing slash in the address bar display.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.urlbar.suggest.quickactions",
                    "Quick actions in address bar",
                    "Shows Firefox quick actions such as clear history or open downloads while typing.",
                    value_type="boolean",
                    status="default",
                    label_key="profiles.wizard_preferences_known_search_quick_actions_title",
                    description_key="profiles.wizard_preferences_known_search_quick_actions_copy",
                ),
                known_pref(
                    "browser.search.update",
                    "Search engine updates",
                    "Controls whether Firefox keeps built-in search engine definitions updated.",
                    value_type="boolean",
                    status="locked",
                ),
            ],
        },
    }
