from __future__ import annotations

from typing import Any

from .builders import chip, control_target, known_pref, pref_control, preset, value_option


def get_general_section() -> dict[str, Any]:
    return {
        "id": "general",
        "ui_maps": {
            "policy": [
                chip("startup", "profiles.wizard_settings_general_startup", "Startup"),
                chip("default_browser", "profiles.wizard_settings_general_default_browser", "Default browser"),
                chip("downloads", "profiles.wizard_settings_general_downloads", "Downloads"),
                chip("updates", "profiles.wizard_settings_general_updates", "Updates"),
            ],
            "proxy": [
                chip("network", "profiles.wizard_settings_general_network", "Network Settings"),
            ],
        },
        "ui_controls": {
            "policy": [
                control_target("startup", "field:wizard-homepage-start-page", "profiles.wizard_homepage_start_label", "Startup behavior"),
                control_target("default_browser", "policy:DontCheckDefaultBrowser", "profiles.policy_default_browser", "Skip default browser checks"),
                control_target("downloads", "policy:PromptForDownloadLocation", "profiles.policy_prompt_downloads", "Always ask for download location"),
                control_target("updates", "policy:DisableAppUpdate", "profiles.policy_disable_app_update", "Disable app update"),
                control_target("updates", "policy:DisableSystemAddonUpdate", "profiles.policy_disable_system_addon_update", "Disable system add-on updates"),
                control_target("updates", "policy:AppAutoUpdate", "profiles.policy_app_auto_update", "Enable app auto update"),
            ],
            "proxy": [
                control_target("network", "field:wizard-proxy-mode", "profiles.wizard_proxy_mode_label", "Proxy mode"),
                control_target("network", "field:wizard-proxy-auto-config-url", "profiles.wizard_proxy_auto_config_label", "Auto-config URL"),
                control_target("network", "field:wizard-proxy-http", "profiles.wizard_proxy_http_label", "HTTP proxy"),
                control_target("network", "field:wizard-proxy-passthrough", "profiles.wizard_proxy_passthrough_label", "Bypass proxy for"),
                control_target("network", "field:wizard-proxy-locked", "profiles.wizard_proxy_locked_label", "Lock proxy settings"),
            ],
        },
        "preferences": {
            "id": "general",
            "title_key": "profiles.wizard_preferences_general_title",
            "body_key": "profiles.wizard_preferences_general_body",
            "gui_groups": [
                chip("startup", "profiles.wizard_preferences_group_general_startup", "Startup"),
                chip("tabs", "profiles.wizard_preferences_group_general_tabs", "Tabs"),
                chip("downloads", "profiles.wizard_preferences_group_general_downloads", "Downloads"),
                chip("language", "profiles.wizard_preferences_group_general_language", "Language"),
                chip("applications", "profiles.wizard_preferences_group_general_applications", "Applications"),
                chip("network", "profiles.wizard_preferences_group_general_network", "Network Settings"),
                chip("updates", "profiles.wizard_preferences_group_general_updates", "Updates"),
            ],
            "controls": [
                pref_control("startup", "restore_session", "profiles.wizard_preferences_preset_restore_session_title", "Restore previous session"),
                pref_control("startup", "open_homepage", "profiles.wizard_preferences_preset_open_homepage_title", "Open homepage on startup"),
                pref_control("tabs", "warn_on_close", "profiles.wizard_preferences_preset_warn_on_close_title", "Warn before closing many tabs"),
                pref_control("tabs", "last_tab_stays_open", "profiles.wizard_preferences_preset_last_tab_stays_open_title", "Keep window open after the last tab"),
                pref_control("downloads", "download_dir", "profiles.wizard_preferences_preset_download_dir_title", "Use default download folder"),
                pref_control("downloads", "download_prompt", "profiles.wizard_preferences_preset_download_prompt_title", "Always ask where to save files"),
                pref_control("applications", "smooth_scroll", "profiles.wizard_preferences_preset_smooth_scroll_title", "Smooth scrolling"),
                pref_control("language", "spellcheck_multiline", "profiles.wizard_preferences_preset_spellcheck_multiline_title", "Spellcheck multiline fields"),
            ],
            "prefixes": [
                "accessibility.",
                "app.update.",
                "browser.download.",
                "browser.link.",
                "browser.sessionstore.",
                "browser.shell.",
                "browser.startup.page",
                "browser.tabs.",
                "browser.warnOnQuit",
                "general.autoScroll",
                "general.smoothScroll",
                "intl.",
                "layout.spellcheckDefault",
                "media.",
                "network.proxy.",
                "widget.",
            ],
            "presets": [
                preset("restore_session", "browser.startup.page", 3, "default", "number", "profiles.wizard_preferences_preset_restore_session_title", "profiles.wizard_preferences_preset_restore_session_copy"),
                preset("open_homepage", "browser.startup.page", 1, "default", "number", "profiles.wizard_preferences_preset_open_homepage_title", "profiles.wizard_preferences_preset_open_homepage_copy"),
                preset("warn_on_close", "browser.tabs.warnOnClose", True, "default", "boolean", "profiles.wizard_preferences_preset_warn_on_close_title", "profiles.wizard_preferences_preset_warn_on_close_copy"),
                preset("last_tab_stays_open", "browser.tabs.closeWindowWithLastTab", False, "default", "boolean", "profiles.wizard_preferences_preset_last_tab_stays_open_title", "profiles.wizard_preferences_preset_last_tab_stays_open_copy"),
                preset("download_dir", "browser.download.useDownloadDir", True, "locked", "boolean", "profiles.wizard_preferences_preset_download_dir_title", "profiles.wizard_preferences_preset_download_dir_copy"),
                preset("download_prompt", "browser.download.useDownloadDir", False, "locked", "boolean", "profiles.wizard_preferences_preset_download_prompt_title", "profiles.wizard_preferences_preset_download_prompt_copy"),
                preset("smooth_scroll", "general.smoothScroll", True, "default", "boolean", "profiles.wizard_preferences_preset_smooth_scroll_title", "profiles.wizard_preferences_preset_smooth_scroll_copy"),
                preset("spellcheck_multiline", "layout.spellcheckDefault", 2, "default", "number", "profiles.wizard_preferences_preset_spellcheck_multiline_title", "profiles.wizard_preferences_preset_spellcheck_multiline_copy"),
            ],
            "known_preferences": [
                known_pref(
                    "browser.startup.page",
                    "Startup page mode",
                    "Chooses whether Firefox opens a blank page, homepage, or restores the previous session at launch.",
                    value_type="number",
                    status="default",
                    value_control="select",
                    value_options=[
                        value_option(0, "Blank page"),
                        value_option(1, "Homepage"),
                        value_option(3, "Restore previous session"),
                    ],
                ),
                known_pref(
                    "browser.startup.homepage",
                    "Homepage URL",
                    "Sets the startup homepage directly through Preferences.",
                    value_type="string",
                    status="default",
                ),
                known_pref(
                    "browser.download.dir",
                    "Default download directory",
                    "Points managed downloads to a specific filesystem path.",
                    value_type="string",
                    status="default",
                ),
                known_pref(
                    "browser.download.folderList",
                    "Download folder source",
                    "Chooses whether Firefox uses desktop, downloads, or a custom folder.",
                    value_type="number",
                    status="default",
                    value_control="select",
                    value_options=[
                        value_option(0, "Desktop"),
                        value_option(1, "Downloads"),
                        value_option(2, "Custom path"),
                    ],
                ),
                known_pref(
                    "general.autoScroll",
                    "Middle-click autoscroll",
                    "Toggles autoscroll when the user presses the middle mouse button.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "media.autoplay.default",
                    "Autoplay policy",
                    "Controls whether websites may autoplay audio and video.",
                    value_type="number",
                    status="default",
                    value_control="select",
                    value_options=[
                        value_option(0, "Allow autoplay"),
                        value_option(1, "Block audible autoplay"),
                        value_option(5, "Block all autoplay"),
                    ],
                ),
            ],
        },
    }
