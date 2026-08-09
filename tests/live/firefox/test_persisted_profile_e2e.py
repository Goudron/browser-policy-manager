from __future__ import annotations

import json
from typing import Any

import pytest
import requests

from tests.live.firefox.helpers import (
    assert_no_policy_errors,
    assert_policy_active,
    get_bool_pref,
    get_int_pref,
    get_requested_locales,
    get_string_pref,
    is_pref_locked,
)
from tests.support import run_test_app_server

pytestmark = pytest.mark.firefox_live

REQUESTED_LOCALES = ["fr", "de", "en-US"]


def _complex_profile_payload(proxy_address: str) -> dict[str, Any]:
    """Return the persisted policy payload for the public BPM API only."""

    proxy_host, proxy_port = proxy_address.rsplit(":", 1)
    return {
        "name": "Firefox persisted complex profile E2E",
        "description": "Public BPM persistence/export to Firefox runtime proof",
        "schema_version": "release-153",
        "flags": {
            "Proxy": {
                "Mode": "manual",
                "Locked": True,
                "HTTPProxy": proxy_address,
                "UseHTTPProxyForAllProtocols": True,
                "Passthrough": "localhost, 127.0.0.1",
            },
            "Preferences": {
                "browser.download.useDownloadDir": {
                    "Value": False,
                    "Status": "locked",
                    "Type": "boolean",
                },
                "network.trr.mode": {
                    "Value": 5,
                    "Status": "locked",
                    "Type": "number",
                },
                "browser.startup.homepage": {
                    "Value": "about:blank",
                    "Status": "locked",
                    "Type": "string",
                },
            },
            "RequestedLocales": REQUESTED_LOCALES,
        },
        "_runtime_expectation": {
            "proxy_host": proxy_host,
            "proxy_port": int(proxy_port),
        },
    }


def _create_read_and_export_persisted_profile(
    *,
    base_url: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], requests.Response]:
    """Use only BPM's public HTTP surface before Firefox receives a document."""

    flags = payload["flags"]
    create_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
    created = requests.post(f"{base_url}/api/profiles", json=create_payload, timeout=10)
    assert created.status_code == 201, created.text
    profile_id = created.json()["id"]

    reloaded = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
    assert reloaded.status_code == 200, reloaded.text
    persisted_profile = reloaded.json()
    assert persisted_profile["id"] == profile_id
    assert persisted_profile["flags"] == flags

    exported = requests.get(
        f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json?indent=2",
        timeout=10,
    )
    assert exported.status_code == 200, exported.text
    assert exported.json() == {"policies": flags}
    return persisted_profile, exported


def test_persisted_complex_profile_exports_exact_document_and_applies_in_firefox(
    firefox_run_exported_document,
    http_proxy_site,
):
    """Prove BPM persistence/export rather than a fixture-to-render shortcut."""

    payload = _complex_profile_payload(http_proxy_site.proxy_address)
    expected_flags = payload["flags"]
    runtime = payload["_runtime_expectation"]

    with run_test_app_server() as base_url:
        persisted_profile, exported = _create_read_and_export_persisted_profile(
            base_url=base_url,
            payload=payload,
        )

    driver, exported_document, policy_path, _firefox_dir, _profile_dir = (
        firefox_run_exported_document(
            exported.content,
        )
    )

    # The installed artifact is a byte-for-byte copy of BPM's response, and
    # both its parsed document and the profile readback preserve nested input.
    assert policy_path.read_bytes() == exported.content
    assert json.loads(policy_path.read_text(encoding="utf-8")) == exported_document
    assert exported_document == {"policies": expected_flags}
    assert persisted_profile["flags"] == expected_flags

    for policy_name in ("Proxy", "Preferences", "RequestedLocales"):
        assert_policy_active(driver, policy_name)
    assert_no_policy_errors(driver, ["Proxy", "Preferences", "RequestedLocales"])

    assert get_int_pref(driver, "network.proxy.type") == 1
    assert get_string_pref(driver, "network.proxy.http") == runtime["proxy_host"]
    assert get_int_pref(driver, "network.proxy.http_port") == runtime["proxy_port"]
    assert is_pref_locked(driver, "network.proxy.type") is True

    assert get_bool_pref(driver, "browser.download.useDownloadDir") is False
    assert is_pref_locked(driver, "browser.download.useDownloadDir") is True
    assert get_int_pref(driver, "network.trr.mode") == 5
    assert is_pref_locked(driver, "network.trr.mode") is True
    assert get_string_pref(driver, "browser.startup.homepage") == "about:blank"
    assert is_pref_locked(driver, "browser.startup.homepage") is True

    assert get_string_pref(driver, "intl.locale.requested") == ",".join(REQUESTED_LOCALES)
    assert get_requested_locales(driver) == REQUESTED_LOCALES

    target_url = http_proxy_site.url("/persisted-profile-e2e")
    driver.get(target_url)
    assert "PROXY_OK" in driver.page_source
    assert target_url in driver.page_source
    assert any(request == target_url for request in http_proxy_site.requests)
