from app.web.firefox_preferences import _build_known_preferences, get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog


def test_wizard_settings_catalog_is_single_source_of_truth():
    catalog = get_wizard_settings_catalog()
    preferences_catalog = get_wizard_preferences_catalog(catalog)

    assert [section["id"] for section in catalog["sections"]] == ["general", "home", "search", "privacy", "sync"]
    assert set(catalog["sections_by_id"]) == {"general", "home", "search", "privacy", "sync"}
    assert catalog["sections_by_id"]["general"]["ui_maps"]["policy"][0]["label_key"] == "profiles.wizard_settings_general_startup"
    assert catalog["sections_by_id"]["general"]["ui_controls"]["policy"][0]["target"] == "field:wizard-homepage-start-page"
    assert catalog["sections_by_id"]["privacy"]["ui_maps"]["lockdown"][0]["fallback"] == "HTTPS-Only Mode"
    assert catalog["sections_by_id"]["privacy"]["preferences"]["controls"][0]["target"] == "preference-preset:privacy_tracking"
    assert catalog["sections_by_id"]["sync"]["preferences"]["gui_groups"][0]["id"] == "account"
    assert preferences_catalog["sections"][0]["id"] == catalog["sections"][0]["preferences"]["id"]
    assert preferences_catalog["known_preferences"]


def test_wizard_preferences_catalog_matches_gui_sections():
    catalog = get_wizard_preferences_catalog()

    section_ids = [section["id"] for section in catalog["sections"]]
    assert section_ids == ["general", "home", "search", "privacy", "sync"]

    sections = {section["id"]: section for section in catalog["sections"]}

    assert {group["id"] for group in sections["general"]["gui_groups"]} >= {
        "startup",
        "tabs",
        "downloads",
        "language",
        "updates",
    }
    assert {group["id"] for group in sections["privacy"]["gui_groups"]} >= {
        "tracking",
        "permissions",
        "https_only",
        "dns_over_https",
    }
    assert {group["id"] for group in sections["sync"]["gui_groups"]} >= {
        "account",
        "data_types",
    }

    general_presets = {preset["id"] for preset in sections["general"]["presets"]}
    privacy_presets = {preset["id"] for preset in sections["privacy"]["presets"]}
    sync_presets = {preset["id"] for preset in sections["sync"]["presets"]}

    assert {"open_homepage", "download_prompt", "spellcheck_multiline"} <= general_presets
    assert {"privacy_https_only", "privacy_doh_default", "privacy_geo_block"} <= privacy_presets
    assert {"sync_bookmarks", "sync_tabs", "sync_passwords_off"} <= sync_presets
    assert {bundle["id"] for bundle in sections["home"]["bundles"]} >= {
        "home_focus_mode",
        "home_dense_topsites",
    }
    assert {bundle["id"] for bundle in sections["privacy"]["bundles"]} >= {
        "privacy_site_permissions_lockdown",
        "privacy_doh_hardened",
    }

    assert "network.trr." in sections["privacy"]["prefixes"]
    assert "permissions.default." in sections["privacy"]["prefixes"]
    assert "services.sync." in sections["sync"]["prefixes"]

    known_by_pref = {item["pref"]: item for item in catalog["known_preferences"]}
    assert known_by_pref["browser.tabs.warnOnClose"]["can_autofill"] is True
    assert known_by_pref["browser.tabs.warnOnClose"]["type"] == "boolean"
    assert known_by_pref["browser.tabs.warnOnClose"]["status"] == "default"
    assert known_by_pref["browser.startup.homepage"]["can_autofill"] is False
    assert known_by_pref["browser.startup.homepage"]["type"] == "string"
    assert known_by_pref["browser.startup.homepage"]["fallback"] == "Homepage URL"
    assert known_by_pref["browser.startup.page"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["browser.startup.page"]["value_options"]] == [0, 1, 3]
    assert known_by_pref["browser.download.useDownloadDir"]["can_autofill"] is False
    assert known_by_pref["browser.download.useDownloadDir"]["type"] == "boolean"
    assert known_by_pref["browser.download.useDownloadDir"]["status"] == "locked"
    assert known_by_pref["browser.download.useDownloadDir"]["preset_count"] == 2
    assert known_by_pref["browser.download.folderList"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["browser.download.folderList"]["value_options"]] == [0, 1, 2]
    assert known_by_pref["media.autoplay.default"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["media.autoplay.default"]["value_options"]] == [0, 1, 5]
    assert known_by_pref["browser.newtabpage.activity-stream.topSitesRows"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["browser.newtabpage.activity-stream.topSitesRows"]["value_options"]] == [1, 2, 3, 4]
    assert known_by_pref["browser.contentblocking.category"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["browser.contentblocking.category"]["value_options"]] == ["standard", "strict", "custom"]
    assert known_by_pref["network.cookie.cookieBehavior"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["network.cookie.cookieBehavior"]["value_options"]] == [0, 1, 4, 5]
    assert known_by_pref["network.trr.mode"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["network.trr.mode"]["value_options"]] == [0, 2, 3, 5]
    assert known_by_pref["permissions.default.geo"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["permissions.default.geo"]["value_options"]] == [0, 1, 2]
    assert known_by_pref["permissions.default.camera"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["permissions.default.camera"]["value_options"]] == [0, 1, 2]
    assert known_by_pref["permissions.default.microphone"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["permissions.default.microphone"]["value_options"]] == [0, 1, 2]
    assert known_by_pref["permissions.default.desktop-notification"]["value_control"] == "select"
    assert [option["value"] for option in known_by_pref["permissions.default.desktop-notification"]["value_options"]] == [0, 1, 2]
    assert known_by_pref["privacy.resistFingerprinting"]["section_id"] == "privacy"
    assert known_by_pref["browser.urlbar.trimURLs"]["section_id"] == "search"
    assert known_by_pref["services.sync.engine.addons"]["section_id"] == "sync"
    assert len(next(bundle for bundle in sections["privacy"]["bundles"] if bundle["id"] == "privacy_site_permissions_lockdown")["items"]) == 4
    assert [item["pref"] for item in next(bundle for bundle in sections["privacy"]["bundles"] if bundle["id"] == "privacy_doh_hardened")["items"]] == [
        "network.trr.mode",
        "security.enterprise_roots.enabled",
    ]


def test_build_known_preferences_respects_explicit_metadata_and_values():
    known_preferences = _build_known_preferences(
        "privacy",
        presets=[],
        explicit_known_preferences=[
            {
                "pref": "browser.test.pref",
                "label_key": "profiles.pref.label",
                "fallback": "Browser Test Pref",
                "description_key": "profiles.pref.description",
                "description_fallback": "Helpful description",
                "value_control": "select",
                "value_options": [{"value": "strict", "fallback": "Strict"}],
                "status": "locked",
                "type": "string",
                "value": "strict",
            }
        ],
    )

    assert known_preferences == [
        {
            "pref": "browser.test.pref",
            "section_id": "privacy",
            "preset_ids": [],
            "preset_count": 0,
            "label_key": "profiles.pref.label",
            "fallback": "Browser Test Pref",
            "description_key": "profiles.pref.description",
            "description_fallback": "Helpful description",
            "value_control": "select",
            "value_options": [{"value": "strict", "fallback": "Strict"}],
            "status": "locked",
            "type": "string",
            "value": "strict",
            "can_autofill": True,
        }
    ]


def test_build_known_preferences_keeps_defaults_when_optional_metadata_is_missing():
    known_preferences = _build_known_preferences(
        "privacy",
        presets=[],
        explicit_known_preferences=[
            {
                "pref": "browser.test.defaulted",
                "label_key": "profiles.pref.defaulted",
            }
        ],
    )

    assert known_preferences == [
        {
            "pref": "browser.test.defaulted",
            "section_id": "privacy",
            "preset_ids": [],
            "preset_count": 0,
            "label_key": "profiles.pref.defaulted",
            "fallback": "browser.test.defaulted",
            "description_key": "",
            "description_fallback": "",
            "value_control": "",
            "value_options": [],
            "status": "",
            "type": "",
            "value": None,
            "can_autofill": False,
        }
    ]
