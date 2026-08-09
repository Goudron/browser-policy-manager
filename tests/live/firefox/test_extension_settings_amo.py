from __future__ import annotations

import pytest

from tests.live.firefox.helpers import (
    assert_no_policy_errors,
    assert_policy_active,
    wait_for_addon_install,
)

pytestmark = [pytest.mark.firefox_live, pytest.mark.firefox_live_amo]

UBLOCK_ADDON_ID = "uBlock0@raymondhill.net"
UBLOCK_INSTALL_URL = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
UBLOCK_NAME = "uBlock Origin"


class AMOCanaryExternalFailure(AssertionError):
    """The AMO provider or its network path failed after policy activation.

    This is intentionally distinct from a product assertion: deterministic
    policy coverage has already established the local Firefox/BPM path.  The
    separate canary must leave an actionable, non-green signal when AMO is
    unavailable without making that external dependency a release gate.
    """


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


def test_extension_settings_force_installs_ublock_origin_from_amo_in_one_browser_session(
    firefox_run,
):
    """Canary the real AMO download after proving Firefox accepted the policy.

    A timeout here is an external provider/network failure: policy document,
    activation, and Firefox policy-error checks have already succeeded.  Those
    product assertions intentionally remain outside the conversion below.
    """
    driver, document, _firefox_dir, _profile_dir = firefox_run(_ublock_extension_settings_policy())

    assert document == {"policies": _ublock_extension_settings_policy()}
    assert_policy_active(driver, "ExtensionSettings")
    assert_no_policy_errors(driver, ["ExtensionSettings"])
    try:
        addon = wait_for_addon_install(driver, UBLOCK_ADDON_ID, timeout_seconds=60.0)
    except AssertionError as error:
        raise AMOCanaryExternalFailure(
            "AMO_CANARY_EXTERNAL_FAILURE[provider-or-network]: Firefox accepted "
            f"ExtensionSettings for {UBLOCK_INSTALL_URL}, but AMO did not supply "
            f"{UBLOCK_ADDON_ID!r}: {error}"
        ) from error

    assert addon["name"] == UBLOCK_NAME
    assert addon["isActive"] is True
    assert addon["type"] == "extension"
    assert addon["isBuiltin"] is False
    assert addon["sourceURI"] == UBLOCK_INSTALL_URL
