from __future__ import annotations

import json

from app.core.schema_channels import (
    CURRENT_ESR_SCHEMA_CHANNEL,
    CURRENT_RELEASE_SCHEMA_CHANNEL,
)
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog
from tests.docs_index import doc_path_from_index
from tools.build_firefox_policy_documentation_inventory import build_inventory

RELEASE_ONLY_POLICIES = {
    "AIControls",
    "BrowserDataBackup",
    "DisableRemoteImprovements",
    "GenerativeAI",
    "IPProtectionAvailable",
    "LocalNetworkAccess",
    "VisualSearchEnabled",
    "XSLTEnabled",
}


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
    assert inventory["backlog_item"] == "BPM090-M2-03"
    assert inventory["generated_for_bpm"] == "0.9.0"

    policies = inventory["policies"]
    assert isinstance(policies, list)
    assert len(policies) == 120
    assert len({entry["policy_id"] for entry in policies}) == 120
    assert len({entry["doc_id"] for entry in policies}) == 120
    assert all(entry["doc_id"] == f"fx-policy-{entry['policy_id']}" for entry in policies)
    assert all(entry["ui_target"] == f"policy:{entry['policy_id']}" for entry in policies)


def test_firefox_policy_documentation_inventory_records_channel_differences():
    inventory = _maintained_inventory()
    policies = inventory["policies"]
    by_id = {entry["policy_id"]: entry for entry in policies}
    esr_ids = set(load_policy_schema(CURRENT_ESR_SCHEMA_CHANNEL).policies)
    release_ids = set(load_policy_schema(CURRENT_RELEASE_SCHEMA_CHANNEL).policies)

    assert release_ids - esr_ids == RELEASE_ONLY_POLICIES
    assert esr_ids - release_ids == set()
    assert set(by_id) == esr_ids | release_ids
    assert {
        policy_id for policy_id, entry in by_id.items() if entry["channel_scope"] == "release-only"
    } == RELEASE_ONLY_POLICIES
    assert not any(entry["definition_changed_across_channels"] for entry in policies)
    assert inventory["summary"]["policy_scope_counts"] == {
        "both": 112,
        "release-only": 8,
    }

    for policy_id, entry in by_id.items():
        expected_channels = {
            channel
            for channel, schema_ids in (
                (CURRENT_ESR_SCHEMA_CHANNEL, esr_ids),
                (CURRENT_RELEASE_SCHEMA_CHANNEL, release_ids),
            )
            if policy_id in schema_ids
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
        entry["ui_target"] == f"known-preference:{entry['preference_id']}"
        for entry in preferences
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
        "112 ESR policies",
        "Eight policies are Release-only",
        "no changed definitions among the 112 common policies",
        "62 managed preferences",
        "`ui.support_level=fallback`",
        "BPM090-M2-07",
        "--check",
    ):
        assert required in summary
