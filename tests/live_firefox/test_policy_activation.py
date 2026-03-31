from __future__ import annotations

import pytest

from tests.live_firefox.helpers import assert_no_policy_errors, assert_policy_active

pytestmark = pytest.mark.firefox_live


def test_block_about_config_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run({"BlockAboutConfig": True})

    assert document == {"policies": {"BlockAboutConfig": True}}
    assert_policy_active(driver, "BlockAboutConfig")
    assert_no_policy_errors(driver, ["BlockAboutConfig"])


def test_website_filter_is_loaded_by_firefox(firefox_run, static_site):
    driver, document, _firefox_dir, _profile_dir = firefox_run({"WebsiteFilter": {"Block": ["<all_urls>"]}})

    assert document == {"policies": {"WebsiteFilter": {"Block": ["<all_urls>"]}}}
    assert_policy_active(driver, "WebsiteFilter")
    assert_no_policy_errors(driver, ["WebsiteFilter"])


def test_homepage_policy_is_loaded_by_firefox(firefox_run, static_site):
    homepage_url = static_site.url("/homepage.html")
    driver, document, _firefox_dir, _profile_dir = firefox_run(
        {"Homepage": {"URL": homepage_url, "Locked": True, "StartPage": "homepage"}}
    )

    assert document == {
        "policies": {
            "Homepage": {
                "URL": homepage_url,
                "Locked": True,
                "StartPage": "homepage",
            }
        }
    }
    assert_policy_active(driver, "Homepage")
    assert_no_policy_errors(driver, ["Homepage"])


def test_preferences_policy_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run(
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

    assert document == {
        "policies": {
            "Preferences": {
                "browser.download.useDownloadDir": {
                    "Value": False,
                    "Status": "locked",
                    "Type": "boolean",
                }
            }
        }
    }
    assert_policy_active(driver, "Preferences")
    assert_no_policy_errors(driver, ["Preferences"])


def test_disable_private_browsing_policy_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run({"DisablePrivateBrowsing": True})

    assert document == {"policies": {"DisablePrivateBrowsing": True}}
    assert_policy_active(driver, "DisablePrivateBrowsing")
    assert_no_policy_errors(driver, ["DisablePrivateBrowsing"])


def test_requested_locales_policy_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run(
        {"RequestedLocales": ["fr", "de", "en-US"]}
    )

    assert document == {"policies": {"RequestedLocales": ["fr", "de", "en-US"]}}
    assert_policy_active(driver, "RequestedLocales")
    assert_no_policy_errors(driver, ["RequestedLocales"])


def test_override_first_run_page_policy_is_loaded_by_firefox(firefox_run, static_site):
    first_run_url = static_site.url("/first-run.html")
    driver, document, _firefox_dir, _profile_dir = firefox_run(
        {"OverrideFirstRunPage": first_run_url}
    )

    assert document == {"policies": {"OverrideFirstRunPage": first_run_url}}
    assert_policy_active(driver, "OverrideFirstRunPage")
    assert_no_policy_errors(driver, ["OverrideFirstRunPage"])


def test_disable_app_update_policy_is_loaded_by_firefox(firefox_run):
    driver, document, _firefox_dir, _profile_dir = firefox_run({"DisableAppUpdate": True})

    assert document == {"policies": {"DisableAppUpdate": True}}
    assert_policy_active(driver, "DisableAppUpdate")
    assert_no_policy_errors(driver, ["DisableAppUpdate"])


def test_proxy_policy_is_loaded_by_firefox(firefox_run, http_proxy_site):
    driver, document, _firefox_dir, _profile_dir = firefox_run(
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

    assert document == {
        "policies": {
            "Proxy": {
                "Mode": "manual",
                "Locked": True,
                "HTTPProxy": http_proxy_site.proxy_address,
                "UseHTTPProxyForAllProtocols": True,
                "Passthrough": "",
            }
        }
    }
    assert_policy_active(driver, "Proxy")
    assert_no_policy_errors(driver, ["Proxy"])


def test_certificates_install_policy_is_loaded_by_firefox(firefox_run, https_cert_site):
    driver, document, _firefox_dir, _profile_dir = firefox_run(
        {"Certificates": {"Install": [str(https_cert_site.ca_cert_path)]}},
        accept_insecure_certs=False,
    )

    assert document == {
        "policies": {
            "Certificates": {
                "Install": [str(https_cert_site.ca_cert_path)],
            }
        }
    }
    assert_policy_active(driver, "Certificates")
    assert_no_policy_errors(driver, ["Certificates"])
