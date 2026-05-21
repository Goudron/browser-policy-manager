from __future__ import annotations

from typing import Any

from .builders import chip, control_target, known_pref, pref_control, preset


def get_sync_section() -> dict[str, Any]:
    return {
        "id": "sync",
        "ui_maps": {
            "policy": [
                chip("account", "profiles.wizard_settings_sync_account", "Firefox Account"),
                chip("data", "profiles.wizard_settings_sync_data", "What to sync"),
            ],
            "extensions": [
                chip("addons_manager", "profiles.wizard_settings_addons_manager", "Add-ons Manager"),
                chip("managed_addons", "profiles.wizard_settings_extensions_policy", "Managed add-ons"),
            ],
        },
        "ui_controls": {
            "policy": [
                control_target("account", "policy:DisableFirefoxAccounts", "profiles.policy_disable_accounts", "Disable Firefox Accounts"),
                control_target("data", "pref-section:sync", "profiles.wizard_preferences_sync_title", "Managed Preferences for Sync"),
            ],
            "extensions": [
                control_target("addons_manager", "field:wizard-extension-default-mode", "profiles.wizard_extensions_mode_label", "Default add-on policy"),
                control_target("managed_addons", "field:wizard-extension-install", "profiles.wizard_extensions_install_label", "Managed install URLs"),
                control_target("managed_addons", "field:wizard-extension-locked", "profiles.wizard_extensions_locked_label", "Locked add-on IDs"),
                control_target("managed_addons", "field:wizard-extension-uninstall", "profiles.wizard_extensions_uninstall_label", "Add-on IDs to uninstall"),
                control_target("managed_addons", "field:extension-profile-ublock", "profiles.wizard_extension_profile_ublock_title", "uBlock Origin"),
            ],
        },
        "preferences": {
            "id": "sync",
            "title_key": "profiles.wizard_preferences_sync_title",
            "body_key": "profiles.wizard_preferences_sync_body",
            "gui_groups": [
                chip("account", "profiles.wizard_preferences_group_sync_account", "Firefox Account"),
                chip("data_types", "profiles.wizard_preferences_group_sync_data_types", "What to sync"),
                chip("device_surfaces", "profiles.wizard_preferences_group_sync_device_surfaces", "Device sync surfaces"),
            ],
            "controls": [
                pref_control("data_types", "sync_bookmarks", "profiles.wizard_preferences_preset_sync_bookmarks_title", "Sync bookmarks"),
                pref_control("data_types", "sync_history", "profiles.wizard_preferences_preset_sync_history_title", "Sync history"),
                pref_control("data_types", "sync_tabs", "profiles.wizard_preferences_preset_sync_tabs_title", "Sync open tabs"),
                pref_control("data_types", "sync_passwords_off", "profiles.wizard_preferences_preset_sync_passwords_off_title", "Do not sync passwords"),
            ],
            "prefixes": [
                "identity.fxaccounts.",
                "services.sync.",
            ],
            "presets": [
                preset("sync_bookmarks", "services.sync.engine.bookmarks", True, "default", "boolean", "profiles.wizard_preferences_preset_sync_bookmarks_title", "profiles.wizard_preferences_preset_sync_bookmarks_copy"),
                preset("sync_history", "services.sync.engine.history", True, "default", "boolean", "profiles.wizard_preferences_preset_sync_history_title", "profiles.wizard_preferences_preset_sync_history_copy"),
                preset("sync_tabs", "services.sync.engine.tabs", True, "default", "boolean", "profiles.wizard_preferences_preset_sync_tabs_title", "profiles.wizard_preferences_preset_sync_tabs_copy"),
                preset("sync_passwords_off", "services.sync.engine.passwords", False, "locked", "boolean", "profiles.wizard_preferences_preset_sync_passwords_off_title", "profiles.wizard_preferences_preset_sync_passwords_off_copy"),
            ],
            "known_preferences": [
                known_pref(
                    "services.sync.engine.addons",
                    "Sync add-ons",
                    "Keeps installed add-ons in sync across signed-in devices.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "services.sync.engine.prefs",
                    "Sync settings",
                    "Lets Firefox synchronize preference changes between devices.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "services.sync.engine.addresses",
                    "Sync addresses",
                    "Keeps saved postal addresses in sync.",
                    value_type="boolean",
                    status="default",
                ),
                known_pref(
                    "services.sync.engine.creditcards",
                    "Sync payment cards",
                    "Keeps saved payment cards synchronized between devices.",
                    value_type="boolean",
                    status="default",
                ),
            ],
        },
    }
