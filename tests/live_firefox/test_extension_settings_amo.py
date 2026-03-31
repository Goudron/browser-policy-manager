from __future__ import annotations

import pytest

from tests.live_firefox.helpers import (
    assert_no_policy_errors,
    assert_policy_active,
    wait_for_addon_install,
)

pytestmark = [pytest.mark.firefox_live, pytest.mark.firefox_live_amo]

UBLOCK_ADDON_ID = "uBlock0@raymondhill.net"
UBLOCK_INSTALL_URL = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
UBLOCK_NAME = "uBlock Origin"


def _ublock_extension_settings_policy() -> dict[str, object]:
    return {
        "ExtensionSettings": {
            "*": {
                "installation_mode": "blocked",
            },
            UBLOCK_ADDON_ID: {
                "installation_mode": "force_installed",
                "install_url": UBLOCK_INSTALL_URL,
            },
        }
    }


def test_extension_settings_amo_policy_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run(
        _ublock_extension_settings_policy()
    )

    assert document == {"policies": _ublock_extension_settings_policy()}
    assert_policy_active(driver, "ExtensionSettings")
    assert_no_policy_errors(driver, ["ExtensionSettings"])


def test_extension_settings_force_installs_ublock_origin_from_amo(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        _ublock_extension_settings_policy()
    )

    assert_policy_active(driver, "ExtensionSettings")
    addon = wait_for_addon_install(driver, UBLOCK_ADDON_ID, timeout_seconds=60.0)

    assert addon["name"] == UBLOCK_NAME
    assert addon["isActive"] is True
    assert addon["type"] == "extension"
    assert addon["isBuiltin"] is False
    assert addon["sourceURI"] == UBLOCK_INSTALL_URL
