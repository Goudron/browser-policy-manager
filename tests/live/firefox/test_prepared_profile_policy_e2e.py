"""Pinned-Firefox evidence for BPM096 created and duplicated policy profiles.

The scenario deliberately uses only the BPM public API and local loopback
fixtures. ExtensionSettings remains a complete manual-policy test: it proves
Firefox accepts the managed-extension rule without depending on AMO or an
external XPI download.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
import requests
from selenium.common.exceptions import WebDriverException

from app.core.policy_validation import load_policy_schema_for_channel
from tests.live.firefox.helpers import (
    assert_no_policy_errors,
    assert_policy_active,
    get_string_pref,
)
from tests.support import run_test_app_server

pytestmark = pytest.mark.firefox_live

CHANNEL_SCHEMA_ARTIFACTS = {
    "release": "release-153",
    "esr153": "esr-153.0",
    "esr140": "esr-140.13",
    "esr115": "esr-115.39",
}


def _schema_artifact_id() -> str:
    channel = os.getenv("BPM_FIREFOX_CHANNEL", "release")
    artifact_id = os.getenv("BPM_FIREFOX_LIVE_SCHEMA_ARTIFACT")
    assert artifact_id == CHANNEL_SCHEMA_ARTIFACTS[channel]
    return artifact_id


def _request_json(response: requests.Response, expected_status: int) -> dict[str, Any]:
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def _manual_policy_flags(
    *, homepage_url: str, ca_certificate_path: str, include_website_filter: bool
) -> dict[str, Any]:
    """Return the common supported manual policy subset for every active schema."""

    flags: dict[str, Any] = {
        "ExtensionSettings": {
            "*": {"installation_mode": "blocked"},
            "manual-policy@example.invalid": {"installation_mode": "allowed"},
        },
        "Homepage": {"URL": homepage_url, "Locked": True, "StartPage": "homepage"},
        "Certificates": {"Install": [ca_certificate_path]},
    }
    if include_website_filter:
        flags["WebsiteFilter"] = {"Block": ["<all_urls>"]}
    return flags


def _create_edit_duplicate_and_export(
    *, base_url: str, schema_artifact_id: str, flags: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """Create atomically, add manual M7--M9 policies, duplicate, then export bytes."""

    source = _request_json(
        requests.post(
            f"{base_url}/api/profiles/prepare/new",
            json={
                "name": f"Pinned Firefox source {schema_artifact_id} {uuid.uuid4().hex}",
                "target_schema_id": schema_artifact_id,
                "starter_id": "blank",
                "cis_baseline_id": "none",
                "preparation_idempotency_key": uuid.uuid4().hex,
            },
            timeout=10,
        ),
        201,
    )
    assert source["schema_version"] == schema_artifact_id

    edited = _request_json(
        requests.patch(
            f"{base_url}/api/profiles/{source['id']}",
            json={"flags": flags, "expected_revision": source["revision"]},
            timeout=10,
        ),
        200,
    )
    assert edited["flags"] == flags

    duplicate = _request_json(
        requests.post(
            f"{base_url}/api/profiles/prepare/duplicate",
            json={
                "name": f"Pinned Firefox duplicate {schema_artifact_id} {uuid.uuid4().hex}",
                "target_schema_id": schema_artifact_id,
                "starter_id": "keep_current",
                "cis_baseline_id": "none",
                "source_id": edited["id"],
                "expected_source_revision": edited["revision"],
                "preparation_idempotency_key": uuid.uuid4().hex,
            },
            timeout=10,
        ),
        201,
    )
    assert duplicate["id"] != edited["id"]
    assert duplicate["schema_version"] == schema_artifact_id
    assert duplicate["flags"] == flags

    source_after = _request_json(
        requests.get(f"{base_url}/api/profiles/{edited['id']}", timeout=10), 200
    )
    assert source_after == edited

    source_export = requests.get(
        f"{base_url}/api/export/profiles/{edited['id']}/firefox/policies.json?indent=2",
        timeout=10,
    )
    duplicate_export = requests.get(
        f"{base_url}/api/export/profiles/{duplicate['id']}/firefox/policies.json?indent=2",
        timeout=10,
    )
    assert source_export.status_code == 200, source_export.text
    assert duplicate_export.status_code == 200, duplicate_export.text
    assert source_export.json() == {"policies": flags}
    assert duplicate_export.json() == {"policies": flags}
    return edited, duplicate, duplicate_export.content


def test_created_and_duplicated_profile_exports_and_applies_manual_policy_in_firefox(
    firefox_run_exported_document,
    static_site,
    https_cert_site,
) -> None:
    """Prove an active schema's source and duplicate reach its pinned Firefox runtime."""

    schema_artifact_id = _schema_artifact_id()
    homepage_url = static_site.url("/homepage.html")
    blocked_url = static_site.url("/blocked.html")
    site_flags = _manual_policy_flags(
        homepage_url=homepage_url,
        ca_certificate_path=str(https_cert_site.ca_cert_path),
        include_website_filter=True,
    )
    trust_flags = _manual_policy_flags(
        homepage_url=homepage_url,
        ca_certificate_path=str(https_cert_site.ca_cert_path),
        include_website_filter=False,
    )

    with run_test_app_server() as base_url:
        site_source, site_duplicate, site_exported_bytes = _create_edit_duplicate_and_export(
            base_url=base_url,
            schema_artifact_id=schema_artifact_id,
            flags=site_flags,
        )
        trust_source, trust_duplicate, trust_exported_bytes = _create_edit_duplicate_and_export(
            base_url=base_url,
            schema_artifact_id=schema_artifact_id,
            flags=trust_flags,
        )

    site_driver, site_document, site_policy_path, _firefox_dir, _profile_dir = (
        firefox_run_exported_document(
            site_exported_bytes,
            accept_insecure_certs=False,
        )
    )
    assert site_policy_path.read_bytes() == site_exported_bytes
    assert site_document == {"policies": site_flags}
    assert site_source["flags"] == site_duplicate["flags"] == site_flags

    site_policy_names = ["ExtensionSettings", "Homepage", "WebsiteFilter", "Certificates"]
    for policy_name in site_policy_names:
        assert_policy_active(site_driver, policy_name)
    assert_no_policy_errors(site_driver, site_policy_names)
    assert get_string_pref(site_driver, "browser.startup.homepage") == homepage_url

    with pytest.raises(WebDriverException) as excinfo:
        site_driver.get(blocked_url)
    assert "blockedByPolicy" in str(excinfo.value) or "blocked access" in str(excinfo.value)

    trust_driver, trust_document, trust_policy_path, _firefox_dir, _profile_dir = (
        firefox_run_exported_document(
            trust_exported_bytes,
            accept_insecure_certs=False,
        )
    )
    assert trust_policy_path.read_bytes() == trust_exported_bytes
    assert trust_document == {"policies": trust_flags}
    assert trust_source["flags"] == trust_duplicate["flags"] == trust_flags

    trust_policy_names = ["ExtensionSettings", "Homepage", "Certificates"]
    for policy_name in trust_policy_names:
        assert_policy_active(trust_driver, policy_name)
    assert_no_policy_errors(trust_driver, trust_policy_names)
    assert get_string_pref(trust_driver, "browser.startup.homepage") == homepage_url
    trust_driver.get(https_cert_site.url("/index.html"))
    assert "HTTPS_CERT_OK" in trust_driver.page_source


def test_channel_records_microsoft_entra_sso_schema_disposition() -> None:
    """Make the one active-artifact unsupported policy explicit, never silently omitted."""

    schema_artifact_id = _schema_artifact_id()
    properties = load_policy_schema_for_channel(schema_artifact_id).get("properties", {})
    assert isinstance(properties, dict)
    if schema_artifact_id == "esr-115.39":
        assert "MicrosoftEntraSSO" not in properties
    else:
        assert "MicrosoftEntraSSO" in properties
