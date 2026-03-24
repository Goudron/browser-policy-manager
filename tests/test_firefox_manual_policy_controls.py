from __future__ import annotations

from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog


def test_manual_policy_controls_catalog_exposes_quick_policy_keys_and_groups():
    catalog = get_manual_policy_controls_catalog()

    assert "HttpsOnlyMode" in catalog["quick_policy_keys"]
    assert "DisableFirefoxAccounts" in catalog["quick_policy_keys"]
    assert "privacy_lockdown" in catalog["groups_by_id"]


def test_manual_policy_controls_catalog_uses_schema_enum_for_https_only_mode():
    catalog = get_manual_policy_controls_catalog("release-148")
    lockdown_items = catalog["groups_by_id"]["privacy_lockdown"]["items"]
    https_only = next(item for item in lockdown_items if item["policy_id"] == "HttpsOnlyMode")

    assert https_only["control_kind"] == "enum-select"
    assert https_only["enum_values"] == ["allowed", "disallowed", "enabled", "force_enabled"]
    assert https_only["target"] == "policy:HttpsOnlyMode"
