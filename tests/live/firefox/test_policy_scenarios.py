from __future__ import annotations

from typing import Any

import pytest
from selenium.common.exceptions import WebDriverException

from tests.live.firefox.helpers import (
    assert_no_policy_errors,
    assert_policy_active,
    get_bool_pref,
    get_int_pref,
    get_requested_locales,
    get_string_pref,
    get_update_preferences_state,
    is_policy_allowed,
    is_pref_locked,
)

pytestmark = pytest.mark.firefox_live


def _assert_exact_active_policy(
    driver: Any,
    document: dict[str, object],
    flags: dict[str, object],
    policy_name: str,
) -> None:
    """Prove the exact input document activates without Firefox policy errors."""

    assert document == {"policies": flags}
    assert_policy_active(driver, policy_name)
    assert_no_policy_errors(driver, [policy_name])


def _assert_policy_blocked(excinfo: pytest.ExceptionInfo[WebDriverException]) -> None:
    message = str(excinfo.value)
    assert "blockedByPolicy" in message or "blocked access" in message


def test_block_about_config_is_active_and_blocks_the_browser(firefox_run):
    flags = {"BlockAboutConfig": True}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "BlockAboutConfig")
    with pytest.raises(WebDriverException) as excinfo:
        driver.get("about:config")
    _assert_policy_blocked(excinfo)


def test_website_filter_is_active_and_blocks_matching_page(firefox_run, static_site):
    flags = {"WebsiteFilter": {"Block": ["<all_urls>"]}}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "WebsiteFilter")
    with pytest.raises(WebDriverException) as excinfo:
        driver.get(static_site.url("/blocked.html"))
    _assert_policy_blocked(excinfo)


def test_homepage_is_active_and_updates_runtime_preferences(firefox_run, static_site):
    homepage_url = static_site.url("/homepage.html")
    flags = {"Homepage": {"URL": homepage_url, "Locked": True, "StartPage": "homepage"}}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "Homepage")
    assert get_string_pref(driver, "browser.startup.homepage") == homepage_url


def test_preferences_are_active_and_lock_runtime_value(firefox_run):
    flags = {
        "Preferences": {
            "browser.download.useDownloadDir": {
                "Value": False,
                "Status": "locked",
                "Type": "boolean",
            }
        }
    }
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "Preferences")
    assert get_bool_pref(driver, "browser.download.useDownloadDir") is False
    assert is_pref_locked(driver, "browser.download.useDownloadDir") is True


def test_disable_private_browsing_is_active_and_blocks_its_surface(firefox_run):
    flags = {"DisablePrivateBrowsing": True}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "DisablePrivateBrowsing")
    assert is_policy_allowed(driver, "privatebrowsing") is False
    with pytest.raises(WebDriverException) as excinfo:
        driver.get("about:privatebrowsing")
    _assert_policy_blocked(excinfo)


def test_requested_locales_are_active_and_update_runtime_locale_preferences(firefox_run):
    flags = {"RequestedLocales": ["fr", "de", "en-US"]}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "RequestedLocales")
    assert get_string_pref(driver, "intl.locale.requested") == "fr,de,en-US"
    assert get_requested_locales(driver) == ["fr", "de", "en-US"]


def test_override_first_run_page_is_active_and_updates_welcome_preferences(
    firefox_run, static_site
):
    first_run_url = static_site.url("/first-run.html")
    flags = {"OverrideFirstRunPage": first_run_url}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "OverrideFirstRunPage")
    assert get_string_pref(driver, "startup.homepage_welcome_url") == first_run_url
    assert get_bool_pref(driver, "browser.aboutwelcome.enabled") is False


def test_disable_app_update_is_active_and_disables_update_permission(firefox_run):
    flags = {"DisableAppUpdate": True}
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "DisableAppUpdate")
    state = get_update_preferences_state(driver)
    assert state["href"] == "about:preferences#general"
    assert state["appUpdateAllowed"] is False


def test_proxy_is_active_and_routes_http_requests_through_managed_proxy(
    firefox_run, http_proxy_site
):
    flags = {
        "Proxy": {
            "Mode": "manual",
            "Locked": True,
            "HTTPProxy": http_proxy_site.proxy_address,
            "UseHTTPProxyForAllProtocols": True,
            "Passthrough": "",
        }
    }
    driver, document, _firefox_dir, _profile_dir = firefox_run(flags)

    _assert_exact_active_policy(driver, document, flags, "Proxy")
    assert get_int_pref(driver, "network.proxy.type") == 1
    assert get_string_pref(driver, "network.proxy.http") == "127.0.0.1"

    target_url = http_proxy_site.url("/proxy-check")
    driver.get(target_url)

    assert "PROXY_OK" in driver.page_source
    assert target_url in driver.page_source
    assert any(request == target_url for request in http_proxy_site.requests)


def test_certificates_keep_strict_baseline_and_trust_managed_ca(firefox_run, https_cert_site):
    # This negative baseline must remain a separate Firefox launch/profile: a
    # previous managed CA would invalidate the assertion.
    strict_driver, strict_document, _firefox_dir, _profile_dir = firefox_run(
        {},
        accept_insecure_certs=False,
    )
    assert strict_document == {"policies": {}}
    with pytest.raises(WebDriverException) as excinfo:
        strict_driver.get(https_cert_site.url("/index.html"))
    assert "InsecureCertificateError" in str(excinfo.value)
    assert "certerror" in strict_driver.page_source.lower()

    flags = {"Certificates": {"Install": [str(https_cert_site.ca_cert_path)]}}
    trusted_driver, document, _firefox_dir, _profile_dir = firefox_run(
        flags,
        accept_insecure_certs=False,
    )

    _assert_exact_active_policy(trusted_driver, document, flags, "Certificates")
    trusted_driver.get(https_cert_site.url("/index.html"))
    assert "HTTPS_CERT_OK" in trusted_driver.page_source
