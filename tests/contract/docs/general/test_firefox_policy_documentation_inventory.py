from __future__ import annotations

import json
import subprocess
import sys

from app.core.schema_channels import (
    CURRENT_RELEASE_SCHEMA_CHANNEL,
    SUPPORTED_SCHEMA_CHANNELS,
)
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog
from tests.docs_index import doc_path_from_index
from tools.build_firefox_policy_documentation_inventory import build_inventory

PARTIAL_POLICIES = {
    "AIControls",
    "BrowserDataBackup",
    "DisableRemoteImprovements",
    "DisableRemoteSettingsAndAcceptSecurityConsequences",
    "GenerativeAI",
    "IPProtectionAvailable",
    "LocalNetworkAccess",
    "SitePolicies",
    "VisualSearchEnabled",
    "XSLTEnabled",
}
ALL_CHANNEL_PARTIAL_POLICIES = (PARTIAL_POLICIES - {"SitePolicies"}) | {
    "AllowFileSelectionDialogs",
    "AutofillAddressEnabled",
    "AutofillCreditCardEnabled",
    "ContentAnalysis",
    "DefaultSerialGuardSetting",
    "DisableEncryptedClientHello",
    "FirefoxSuggest",
    "HttpAllowlist",
    "HttpsOnlyMode",
    "MicrosoftEntraSSO",
    "PostQuantumKeyAgreementEnabled",
    "PrintingEnabled",
    "PrivateBrowsingModeAvailability",
    "SkipTermsOfUse",
    "TranslateEnabled",
}
CHANGED_ACROSS_ALL_CHANNELS = {
    "Cookies",
    "EnableTrackingProtection",
    "ExtensionSettings",
    "FirefoxHome",
    "Homepage",
    "Permissions",
    "SanitizeOnShutdown",
    "UserMessaging",
}
ESR_140_DOCUMENTATION_BASELINE = "esr-140.13"


def _maintained_inventory() -> dict[str, object]:
    path = doc_path_from_index(
        "architecture/firefox-policy-documentation-inventory-0.9.0.json",
        status="active",
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_firefox_policy_documentation_inventory_is_current_and_complete():
    inventory = _maintained_inventory()

    assert inventory == build_inventory()
    assert inventory["schema_version"] == 1
    assert inventory["backlog_item"] == "BPM095-M8-04"
    assert inventory["generated_for_bpm"] == "0.9.6"

    policies = inventory["policies"]
    assert isinstance(policies, list)
    assert len(policies) == 123
    assert len({entry["policy_id"] for entry in policies}) == 123
    assert len({entry["doc_id"] for entry in policies}) == 123
    assert all(entry["doc_id"] == f"fx-policy-{entry['policy_id']}" for entry in policies)
    assert all(entry["ui_target"] == f"policy:{entry['policy_id']}" for entry in policies)

    channels = inventory["channels"]
    assert {channel for channel, record in channels.items() if record["is_default"]} == {
        "esr-153.0"
    }
    assert {channel for channel, record in channels.items() if record["is_product_default"]} == {
        "esr-153.0"
    }
    assert {channel for channel, record in channels.items() if record["is_latest_esr"]} == {
        "esr-153.0"
    }
    assert {channel for channel, record in channels.items() if record["is_default_release"]} == {
        "release-153"
    }


def test_firefox_policy_documentation_inventory_records_channel_differences():
    inventory = _maintained_inventory()
    policies = inventory["policies"]
    by_id = {entry["policy_id"]: entry for entry in policies}
    schema_ids = {
        channel: set(load_policy_schema(channel).policies) for channel in SUPPORTED_SCHEMA_CHANNELS
    }
    esr_ids = schema_ids[ESR_140_DOCUMENTATION_BASELINE]
    release_ids = schema_ids[CURRENT_RELEASE_SCHEMA_CHANNEL]

    assert release_ids - esr_ids == PARTIAL_POLICIES
    assert esr_ids - release_ids == set()
    assert set(by_id) == set().union(*schema_ids.values())
    assert {
        policy_id for policy_id, entry in by_id.items() if entry["channel_scope"] == "partial"
    } == ALL_CHANNEL_PARTIAL_POLICIES
    assert {
        entry["policy_id"] for entry in policies if entry["definition_changed_across_channels"]
    } == CHANGED_ACROSS_ALL_CHANNELS
    assert inventory["summary"]["policy_scope_counts"] == {
        "both": 97,
        "partial": 24,
        "esr-only": 1,
        "release-only": 1,
    }

    for policy_id, entry in by_id.items():
        expected_channels = {
            channel for channel, policy_ids in schema_ids.items() if policy_id in policy_ids
        }
        assert set(entry["channels"]) == expected_channels
        for channel_record in entry["channels"].values():
            assert channel_record["value_type"] in {
                "boolean",
                "integer",
                "number",
                "string",
                "array",
                "object",
            }
            assert len(channel_record["schema_sha256"]) == 64
            assert channel_record["description_key"]
            assert channel_record["ui"]["support_level"] in {"mapped", "fallback"}


def test_firefox_policy_documentation_inventory_covers_known_preferences():
    inventory = _maintained_inventory()
    preferences = inventory["managed_preferences"]
    catalog_preferences = get_wizard_preferences_catalog()["known_preferences"]

    assert len(preferences) == 62
    assert {entry["preference_id"] for entry in preferences} == {
        entry["pref"] for entry in catalog_preferences
    }
    assert len({entry["doc_id"] for entry in preferences}) == 62
    assert all(
        entry["ui_target"] == f"known-preference:{entry['preference_id']}" for entry in preferences
    )
    assert inventory["summary"]["managed_preference_section_counts"] == {
        "general": 11,
        "home": 8,
        "privacy": 24,
        "search": 11,
        "sync": 8,
    }


def test_firefox_policy_documentation_inventory_summary_is_active():
    summary = doc_path_from_index(
        "architecture/firefox-policy-documentation-inventory-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")

    for required in (
        "Four current policy/channel badges derive from one lifecycle catalog",
        "ESR 115.39 and ESR 140.13 remain",
        "97 policies occur in all four",
        "62 known managed preferences",
        "do not edit manually",
        "--check",
    ):
        assert required in summary


def test_inventory_owner_check_reports_four_channel_and_artifact_progress() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/build_firefox_policy_documentation_inventory.py", "--check"],
        cwd=doc_path_from_index(
            "architecture/firefox-policy-documentation-inventory-0.9.0.json"
        ).parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "phase=channels; completed=0/6" in completed.stdout
    for channel in ("release-153", "esr-153.0", "esr-140.13", "esr-115.39"):
        assert f"channel={channel}" in completed.stdout
    assert "artifact=summary; completed=6/6" in completed.stdout
