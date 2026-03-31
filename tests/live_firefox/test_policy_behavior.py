from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException

from tests.live_firefox.helpers import (
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


def test_block_about_config_changes_browser_behavior(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run({"BlockAboutConfig": True})

    assert_policy_active(driver, "BlockAboutConfig")
    with pytest.raises(WebDriverException) as excinfo:
        driver.get("about:config")

    message = str(excinfo.value)
    assert "blockedByPolicy" in message or "blocked access" in message


def test_website_filter_blocks_matching_page(firefox_run, static_site):
    driver, _document, _firefox_dir, _profile_dir = firefox_run({"WebsiteFilter": {"Block": ["<all_urls>"]}})

    assert_policy_active(driver, "WebsiteFilter")
    with pytest.raises(WebDriverException) as excinfo:
        driver.get(static_site.url("/blocked.html"))

    message = str(excinfo.value)
    assert "blockedByPolicy" in message or "blocked access" in message


def test_homepage_policy_updates_runtime_preferences(firefox_run, static_site):
    homepage_url = static_site.url("/homepage.html")
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {"Homepage": {"URL": homepage_url, "Locked": True, "StartPage": "homepage"}}
    )

    assert_policy_active(driver, "Homepage")
    assert get_string_pref(driver, "browser.startup.homepage") == homepage_url


def test_preferences_policy_updates_runtime_preferences(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {
            "Preferences": {
                "browser.download.useDownloadDir": {
                    "Value": False,
                    "Status": "locked",
                    "Type": "boolean",
                }
            }
        }
    )

    assert_policy_active(driver, "Preferences")
    assert get_bool_pref(driver, "browser.download.useDownloadDir") is False
    assert is_pref_locked(driver, "browser.download.useDownloadDir") is True


def test_disable_private_browsing_blocks_private_browsing_surface(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run({"DisablePrivateBrowsing": True})

    assert_policy_active(driver, "DisablePrivateBrowsing")
    assert is_policy_allowed(driver, "privatebrowsing") is False

    with pytest.raises(WebDriverException) as excinfo:
        driver.get("about:privatebrowsing")

    message = str(excinfo.value)
    assert "blockedByPolicy" in message or "blocked access" in message


def test_requested_locales_updates_runtime_locale_preferences(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {"RequestedLocales": ["fr", "de", "en-US"]}
    )

    assert_policy_active(driver, "RequestedLocales")
    assert get_string_pref(driver, "intl.locale.requested") == "fr,de,en-US"
    assert get_requested_locales(driver) == ["fr", "de", "en-US"]


def test_override_first_run_page_updates_runtime_welcome_preferences(firefox_run, static_site):
    first_run_url = static_site.url("/first-run.html")
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {"OverrideFirstRunPage": first_run_url}
    )

    assert_policy_active(driver, "OverrideFirstRunPage")
    assert get_string_pref(driver, "startup.homepage_welcome_url") == first_run_url
    assert get_bool_pref(driver, "browser.aboutwelcome.enabled") is False


def test_disable_app_update_hides_update_preferences_controls(firefox_run):
    driver, _document, _firefox_dir, _profile_dir = firefox_run({"DisableAppUpdate": True})

    assert_policy_active(driver, "DisableAppUpdate")
    state = get_update_preferences_state(driver)

    assert state["href"] == "about:preferences#general"
    assert state["updateAllowDescription"] is not None
    assert state["updateSettingsContainer"] is not None
    assert state["updateAllowDescription"]["hidden"] is True
    assert state["updateSettingsContainer"]["hidden"] is True


def test_proxy_policy_routes_http_requests_through_managed_proxy(firefox_run, http_proxy_site):
    driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {
            "Proxy": {
                "Mode": "manual",
                "Locked": True,
                "HTTPProxy": http_proxy_site.proxy_address,
                "UseHTTPProxyForAllProtocols": True,
                "Passthrough": "",
            }
        }
    )

    assert_policy_active(driver, "Proxy")
    assert get_int_pref(driver, "network.proxy.type") == 1
    assert get_string_pref(driver, "network.proxy.http") == "127.0.0.1"

    target_url = http_proxy_site.url("/proxy-check")
    driver.get(target_url)

    assert "PROXY_OK" in driver.page_source
    assert target_url in driver.page_source
    assert any(request == target_url for request in http_proxy_site.requests)


def test_certificates_install_trusts_managed_ca_for_local_https_site(firefox_run, https_cert_site):
    strict_driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {},
        accept_insecure_certs=False,
    )
    with pytest.raises(WebDriverException) as excinfo:
        strict_driver.get(https_cert_site.url("/index.html"))
    assert "InsecureCertificateError" in str(excinfo.value)
    assert "certerror" in strict_driver.page_source.lower()

    trusted_driver, _document, _firefox_dir, _profile_dir = firefox_run(
        {"Certificates": {"Install": [str(https_cert_site.ca_cert_path)]}},
        accept_insecure_certs=False,
    )

    assert_policy_active(trusted_driver, "Certificates")
    trusted_driver.get(https_cert_site.url("/index.html"))
    assert "HTTPS_CERT_OK" in trusted_driver.page_source
