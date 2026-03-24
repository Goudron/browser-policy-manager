from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.policy_schema_service import get_policy_definition


_MANUAL_POLICY_GROUPS: list[dict[str, Any]] = [
    {
        "id": "general_browser_behavior",
        "items": [
            {
                "policy_id": "DontCheckDefaultBrowser",
                "label_key": "profiles.policy_default_browser",
                "copy_key": "profiles.policy_default_browser_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisableAppUpdate",
                "label_key": "profiles.policy_disable_app_update",
                "copy_key": "profiles.policy_disable_app_update_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisableSystemAddonUpdate",
                "label_key": "profiles.policy_disable_system_addon_update",
                "copy_key": "profiles.policy_disable_system_addon_update_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "AppAutoUpdate",
                "label_key": "profiles.policy_app_auto_update",
                "copy_key": "profiles.policy_app_auto_update_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "PromptForDownloadLocation",
                "label_key": "profiles.policy_prompt_downloads",
                "copy_key": "profiles.policy_prompt_downloads_copy",
                "control_kind": "toggle",
            },
        ],
    },
    {
        "id": "home_surfaces",
        "items": [
            {
                "policy_id": "DisablePocket",
                "label_key": "profiles.policy_disable_pocket",
                "copy_key": "profiles.policy_disable_pocket_copy",
                "control_kind": "toggle",
            }
        ],
    },
    {
        "id": "privacy_user_data",
        "items": [
            {
                "policy_id": "DisableTelemetry",
                "label_key": "profiles.policy_disable_telemetry",
                "copy_key": "profiles.policy_disable_telemetry_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisableFirefoxStudies",
                "label_key": "profiles.policy_disable_studies",
                "copy_key": "profiles.policy_disable_studies_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisablePrivateBrowsing",
                "label_key": "profiles.policy_disable_private_browsing",
                "copy_key": "profiles.policy_disable_private_browsing_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "OfferToSaveLogins",
                "label_key": "profiles.policy_save_logins",
                "copy_key": "profiles.policy_save_logins_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "PasswordManagerEnabled",
                "label_key": "profiles.policy_password_manager",
                "copy_key": "profiles.policy_password_manager_copy",
                "control_kind": "toggle",
            },
        ],
    },
    {
        "id": "privacy_lockdown",
        "items": [
            {
                "policy_id": "BlockAboutConfig",
                "label_key": "profiles.policy_block_about_config",
                "copy_key": "profiles.policy_block_about_config_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "BlockAboutProfiles",
                "label_key": "profiles.policy_block_about_profiles",
                "copy_key": "profiles.policy_block_about_profiles_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisableDeveloperTools",
                "label_key": "profiles.policy_disable_devtools",
                "copy_key": "profiles.policy_disable_devtools_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "DisableBuiltinPDFViewer",
                "label_key": "profiles.policy_disable_pdf_viewer",
                "copy_key": "profiles.policy_disable_pdf_viewer_copy",
                "control_kind": "toggle",
            },
            {
                "policy_id": "HttpsOnlyMode",
                "label_key": "profiles.policy_https_only",
                "copy_key": "profiles.policy_https_only_copy",
                "control_kind": "enum-select",
            },
        ],
    },
    {
        "id": "sync_accounts",
        "items": [
            {
                "policy_id": "DisableFirefoxAccounts",
                "label_key": "profiles.policy_disable_accounts",
                "copy_key": "profiles.policy_disable_accounts_copy",
                "control_kind": "toggle",
            }
        ],
    },
]


def get_manual_policy_controls_catalog(schema_version: str = "release-148") -> dict[str, Any]:
    """Return the curated manual policy controls backed by the active schema."""

    groups = []
    quick_policy_keys = []

    for group in _MANUAL_POLICY_GROUPS:
        items = [_resolve_control_item(item, schema_version) for item in group["items"]]
        groups.append({"id": group["id"], "items": items})
        quick_policy_keys.extend(item["policy_id"] for item in items)

    return {
        "schema_version": schema_version,
        "quick_policy_keys": quick_policy_keys,
        "groups": groups,
        "groups_by_id": {group["id"]: group for group in groups},
    }


def _resolve_control_item(item: dict[str, Any], schema_version: str) -> dict[str, Any]:
    definition = get_policy_definition(schema_version, item["policy_id"])
    resolved = deepcopy(item)
    resolved["target"] = f"policy:{item['policy_id']}"
    resolved["enum_values"] = list(definition.enum or []) if definition is not None and item["control_kind"] == "enum-select" else []
    return resolved
