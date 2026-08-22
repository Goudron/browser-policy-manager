"""Executable scope guard for BPM096-M8-01's navigation/site coverage inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.firefox_starter_catalog import STARTER_PRESETS
from app.core.schema_channels import SCHEMA_FILENAMES, SUPPORTED_SCHEMA_CHANNELS
from app.web.firefox_preferences import get_wizard_preferences_catalog
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
INVENTORY_PATH = REPO_ROOT / "docs/architecture/profile-navigation-site-coverage-inventory-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-profile-navigation-site-coverage-inventory-v1 -->"


def _inventory() -> dict[str, Any]:
    source = INVENTORY_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "navigation/site coverage fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _schema(channel: str) -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "app/schemas/policies" / SCHEMA_FILENAMES[channel]).read_text(encoding="utf-8")
    )


def test_inventory_is_indexed_and_records_the_m8_01_boundary() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-navigation-site-coverage-inventory-0.9.6.md", status="active"
        )
        == INVENTORY_PATH
    )
    inventory = _inventory()
    assert inventory["inventory_id"] == "bpm096-profile-navigation-site-coverage"
    assert inventory["inventory_version"] == 1
    assert inventory["backlog_item"] == "BPM096-M8-01"
    assert inventory["guided_owner"] == {"step": 2, "id": "urls-sites-navigation"}
    assert inventory["supported_schema_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M8-01 — Navigation and site-access ownership inventoried" in backlog
    assert INVENTORY_PATH.name in backlog


def test_every_navigation_or_site_access_policy_has_exactly_one_step_two_disposition() -> None:
    inventory = _inventory()
    coverage = inventory["policy_coverage"]
    expected = {
        "Homepage",
        "FirefoxHome",
        "DisablePocket",
        "NewTabPage",
        "OverrideFirstRunPage",
        "OverridePostUpdatePage",
        "WebsiteFilter",
        "AllowedDomainsForApps",
        "HttpAllowlist",
        "LocalFileLinks",
        "AutoLaunchProtocolsFromOrigins",
        "GoToIntranetSiteForSingleWordEntryInAddressBar",
        "Handlers",
        "Bookmarks",
        "ManagedBookmarks",
        "NoDefaultBookmarks",
    }
    assert set(coverage) == expected

    for policy_id, entry in coverage.items():
        channels = entry.get("channels", list(SUPPORTED_SCHEMA_CHANNELS))
        assert entry["disposition"] == "urls-step-control"
        assert entry["delivery"] in {"BPM096-M8-02", "BPM096-M8-03", "BPM096-M8-04"}
        assert entry["paths"], policy_id
        assert channels == [
            channel
            for channel in SUPPORTED_SCHEMA_CHANNELS
            if policy_id in _schema(channel)["properties"]
        ]

    assert coverage["HttpAllowlist"]["channels"] == [
        "release-153",
        "esr-153.0",
        "esr-140.13",
    ]


def test_home_preferences_presets_and_cis_inputs_are_explicit() -> None:
    inventory = _inventory()
    preference_coverage = inventory["preference_coverage"]
    catalog_sections = {
        section["id"]: {item["pref"] for item in section["known_preferences"]}
        for section in get_wizard_preferences_catalog()["sections"]
    }
    assert preference_coverage["general"]["preferences"] == [
        "browser.startup.homepage",
        "browser.startup.page",
    ]
    assert set(preference_coverage["general"]["preferences"]) <= catalog_sections["general"]
    assert set(preference_coverage["home"]["preferences"]) == catalog_sections["home"]

    expected_presets = {
        "blank": set(),
        "keep_current": set(),
        "basic_corporate": {"Homepage", "FirefoxHome"},
        "classroom_kiosk": {"Homepage", "FirefoxHome", "WebsiteFilter"},
        "soc_hard": {"FirefoxHome"},
    }
    assert set(inventory["starter_presets"]) == set(expected_presets)
    for preset_id, expected_policy_ids in expected_presets.items():
        actual_policy_ids = {
            policy_id
            for group in STARTER_PRESETS[preset_id]["policy_values"].values()
            for policy_id in group
            if policy_id in {"Homepage", "FirefoxHome", "WebsiteFilter"}
        }
        if STARTER_PRESETS[preset_id]["homepage"]:
            actual_policy_ids.add("Homepage")
        assert actual_policy_ids == expected_policy_ids

    assert inventory["cis"] == {
        "cis_l1": [],
        "cis_l2": ["NewTabPage=false"],
        "rule": "M8 must expose provenance and review state without altering CIS baseline semantics",
    }
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        l1 = json.loads(
            (
                REPO_ROOT / "app/compliance/firefox/cis/generated" / f"cis_l1.{channel}.json"
            ).read_text(encoding="utf-8")
        )["policies"]
        l2 = json.loads(
            (
                REPO_ROOT / "app/compliance/firefox/cis/generated" / f"cis_l2.{channel}.json"
            ).read_text(encoding="utf-8")
        )["policies"]
        assert "NewTabPage" not in l1
        assert l2["NewTabPage"] is False


def test_url_lookalikes_have_an_explicit_non_url_step_disposition() -> None:
    inventory = _inventory()
    exclusions = inventory["non_url_step_exclusions"]
    assert set(exclusions) == {
        "browser-network-search",
        "extensions",
        "certificates-trust",
        "users-language-sync",
        "all-settings-only",
    }
    assert "Proxy.AutoConfigURL and proxy endpoints" in exclusions["browser-network-search"]
    assert "ExtensionSettings.<guid>.install_url" in exclusions["extensions"]
    assert "Certificates.Install[]" in exclusions["certificates-trust"]
    assert exclusions["users-language-sync"] == ["UserMessaging"]
    assert exclusions["all-settings-only"] == [
        "SitePolicies",
        "unknown policy or unregistered managed preference",
    ]

    raw_fallback = inventory["raw_fallback"]
    assert raw_fallback["typed_navigation_or_site_value"]["owner"] == "urls-sites-navigation"
    assert raw_fallback["typed_navigation_or_site_value"]["step"] == 2
    assert raw_fallback["unknown_or_opaque_value"]["owner"] == "all-settings-only"


def test_temporary_hosts_are_single_rehomes_not_second_owners() -> None:
    inventory = _inventory()
    dispositions = inventory["temporary_host_dispositions"]
    assert dispositions == {
        "home_surfaces_and_home_preferences": {
            "previous_host_step": 1,
            "required_owner_step": 2,
            "delivery": "BPM096-M8-02",
            "sources": [
                "_page_wizard_step_general.html",
                "_page_wizard_step_home.html",
                "profiles_catalogs.js",
                "profiles_settings_search.js",
            ],
        },
        "website_filter_and_site_access": {
            "previous_host_step": 5,
            "required_owner_step": 2,
            "delivery": "BPM096-M8-03",
            "sources": [
                "_page_wizard_step_sync.html",
                "profiles_review.js",
                "profiles_schema_shell_sections.js",
            ],
        },
        "handlers_and_managed_navigation": {
            "previous_host_step": 5,
            "required_owner_step": 2,
            "delivery": "BPM096-M8-04",
            "sources": [
                "_page_wizard_step_sync.html",
                "profiles_review.js",
                "profiles_schema_shell_sections.js",
            ],
        },
    }
