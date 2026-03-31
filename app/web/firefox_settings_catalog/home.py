from __future__ import annotations

from typing import Any

from .builders import (
    bundle_item,
    chip,
    doc_target,
    known_pref,
    pref_bundle,
    pref_doc,
    preset,
    value_option,
)


def get_home_section() -> dict[str, Any]:
    return {
        "id": "home",
        "ui_maps": {
            "homepage": [
                chip("homepage", "profiles.wizard_settings_home_homepage", "Homepage"),
                chip("startup", "profiles.wizard_settings_general_startup", "Startup"),
            ],
            "new_tab": [
                chip("new_windows", "profiles.wizard_settings_home_new_windows", "New windows and tabs"),
                chip("startup", "profiles.wizard_settings_general_startup", "Startup"),
            ],
            "firefox_home": [
                chip("firefox_home", "profiles.wizard_settings_home_firefox_home", "Firefox Home"),
                chip("new_windows", "profiles.wizard_settings_home_new_windows", "New windows and tabs"),
            ],
        },
        "ui_docs": {
            "homepage": [
                doc_target("homepage", "field:wizard-homepage-url", "profiles.wizard_homepage_url_label", "Primary homepage URL"),
                doc_target("homepage", "field:wizard-homepage-additional", "profiles.wizard_homepage_additional_label", "Additional homepage tabs"),
                doc_target("homepage", "field:wizard-homepage-locked", "profiles.wizard_homepage_locked_label", "Lock homepage settings"),
                doc_target("startup", "field:wizard-homepage-start-page", "profiles.wizard_homepage_start_label", "Startup behavior"),
            ],
            "new_tab": [
                doc_target("new_windows", "field:wizard-new-tab-page", "profiles.wizard_newtab_page_label", "New tab page"),
                doc_target("new_windows", "field:wizard-override-first-run", "profiles.wizard_override_first_run_label", "First-run page override"),
                doc_target("new_windows", "field:wizard-override-post-update", "profiles.wizard_override_post_update_label", "Post-update page override"),
                doc_target("startup", "field:wizard-homepage-start-page", "profiles.wizard_homepage_start_label", "Startup behavior"),
            ],
            "firefox_home": [
                doc_target("firefox_home", "field:firefox-home-search", "profiles.wizard_firefox_home_search_label", "Search"),
                doc_target("firefox_home", "field:firefox-home-top-sites", "profiles.wizard_firefox_home_top_sites_label", "Top sites"),
                doc_target("firefox_home", "field:firefox-home-pocket", "profiles.wizard_firefox_home_pocket_label", "Pocket"),
                doc_target("firefox_home", "policy:DisablePocket", "profiles.policy_disable_pocket", "Disable Pocket"),
            ],
        },
        "preferences": {
            "id": "home",
            "title_key": "profiles.wizard_preferences_home_title",
            "body_key": "profiles.wizard_preferences_home_body",
            "gui_groups": [
                chip("homepage", "profiles.wizard_preferences_group_home_homepage", "Homepage"),
                chip("new_tabs", "profiles.wizard_preferences_group_home_new_tabs", "New windows and tabs"),
                chip("firefox_home", "profiles.wizard_preferences_group_home_firefox_home", "Firefox Home"),
            ],
            "docs": [
                pref_doc("new_tabs", "home_new_tab", "profiles.wizard_preferences_preset_home_new_tab_title", "Enable Firefox Home on new tabs"),
                pref_doc("firefox_home", "home_topsites", "profiles.wizard_preferences_preset_home_topsites_title", "Show top sites"),
                pref_doc("firefox_home", "home_highlights", "profiles.wizard_preferences_preset_home_highlights_title", "Show highlights"),
                pref_doc("firefox_home", "home_stories", "profiles.wizard_preferences_preset_home_stories_title", "Hide recommended stories"),
                pref_doc("firefox_home", "home_sponsored", "profiles.wizard_preferences_preset_home_sponsored_title", "Hide sponsored top sites"),
                pref_doc("firefox_home", "home_snippets", "profiles.wizard_preferences_preset_home_snippets_title", "Hide snippets"),
            ],
            "prefixes": [
                "browser.newtabpage.",
                "browser.startup.homepage",
                "browser.startup.homepage_override.",
            ],
            "presets": [
                preset("home_new_tab", "browser.newtabpage.enabled", True, "default", "boolean", "profiles.wizard_preferences_preset_home_new_tab_title", "profiles.wizard_preferences_preset_home_new_tab_copy"),
                preset("home_topsites", "browser.newtabpage.activity-stream.feeds.topsites", True, "default", "boolean", "profiles.wizard_preferences_preset_home_topsites_title", "profiles.wizard_preferences_preset_home_topsites_copy"),
                preset("home_highlights", "browser.newtabpage.activity-stream.feeds.section.highlights", True, "default", "boolean", "profiles.wizard_preferences_preset_home_highlights_title", "profiles.wizard_preferences_preset_home_highlights_copy"),
                preset("home_stories", "browser.newtabpage.activity-stream.feeds.system.topstories", False, "default", "boolean", "profiles.wizard_preferences_preset_home_stories_title", "profiles.wizard_preferences_preset_home_stories_copy"),
                preset("home_sponsored", "browser.newtabpage.activity-stream.showSponsoredTopSites", False, "default", "boolean", "profiles.wizard_preferences_preset_home_sponsored_title", "profiles.wizard_preferences_preset_home_sponsored_copy"),
                preset("home_snippets", "browser.newtabpage.activity-stream.feeds.snippets", False, "default", "boolean", "profiles.wizard_preferences_preset_home_snippets_title", "profiles.wizard_preferences_preset_home_snippets_copy"),
            ],
            "bundles": [
                pref_bundle(
                    "home_focus_mode",
                    "firefox_home",
                    "profiles.wizard_preferences_bundle_home_focus_title",
                    "profiles.wizard_preferences_bundle_home_focus_copy",
                    [
                        bundle_item("browser.newtabpage.enabled", True, "default", "boolean"),
                        bundle_item("browser.newtabpage.activity-stream.showSearch", True, "default", "boolean"),
                        bundle_item("browser.newtabpage.activity-stream.feeds.system.topstories", False, "default", "boolean"),
                        bundle_item("browser.newtabpage.activity-stream.showSponsoredTopSites", False, "default", "boolean"),
                        bundle_item("browser.newtabpage.activity-stream.feeds.snippets", False, "default", "boolean"),
                    ],
                ),
                pref_bundle(
                    "home_dense_topsites",
                    "firefox_home",
                    "profiles.wizard_preferences_bundle_home_dense_title",
                    "profiles.wizard_preferences_bundle_home_dense_copy",
                    [
                        bundle_item("browser.newtabpage.activity-stream.feeds.topsites", True, "default", "boolean"),
                        bundle_item("browser.newtabpage.activity-stream.topSitesRows", 2, "default", "number"),
                        bundle_item("browser.newtabpage.activity-stream.showSponsoredTopSites", False, "default", "boolean"),
                    ],
                ),
            ],
            "known_preferences": [
                known_pref(
                    "browser.newtabpage.enabled",
                    "Enable new tab page",
                    "Controls whether Firefox shows the built-in new tab page at all.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.feeds.topsites",
                    "Show top sites feed",
                    "Shows or hides the Top Sites feed on Firefox Home.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.feeds.section.highlights",
                    "Show highlights feed",
                    "Shows or hides Highlights cards on Firefox Home.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.feeds.system.topstories",
                    "Show recommended stories",
                    "Controls whether Firefox Home shows Pocket and recommended stories.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.showSponsoredTopSites",
                    "Show sponsored top sites",
                    "Controls whether sponsored tiles may appear in the Top Sites area.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.feeds.snippets",
                    "Show snippets",
                    "Shows or hides small promotional snippets on Firefox Home surfaces.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.showSearch",
                    "Show search on new tab",
                    "Shows or hides the search box on Firefox Home and the new tab page.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "browser.newtabpage.activity-stream.topSitesRows",
                    "Top sites rows",
                    "Controls how many rows of top sites Firefox Home shows.",
                    value_type="number",
                    status="default",
                    value_control="select",
                    value_options=[
                        value_option(1, "1 row"),
                        value_option(2, "2 rows"),
                        value_option(3, "3 rows"),
                        value_option(4, "4 rows"),
                    ],
                ),
            ],
        },
    }
