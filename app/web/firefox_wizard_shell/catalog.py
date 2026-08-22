from __future__ import annotations

from typing import Any

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS, get_schema_label
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog

from .inline_editors import build_inline_editor
from .serializer import humanize_identifier, serialize_policy

SUPPORTED_POLICY_CHANNELS = SUPPORTED_SCHEMA_CHANNELS

CERTIFICATE_TRUST_POSTURE_POLICY_IDS = (
    "Certificates",
    "DisableSecurityBypass",
    "WindowsSSO",
    "MicrosoftEntraSSO",
)

# These Firefox shapes have a single structured owner: the dedicated
# Certificates & trust component on Guided step 4.  They must never leak back
# into generic schema-shell cards (including the step-8 review shell), where a
# second editor would bypass its raw-preservation and provenance safeguards.
CERTIFICATE_TRUST_GUIDED_POLICY_IDS = frozenset(
    {
        "Authentication",
        "Certificates",
        "DisableSecurityBypass",
        "MicrosoftEntraSSO",
        "SecurityDevices",
        "WindowsSSO",
    }
)

WIZARD_SHELL_STEPS: list[dict[str, Any]] = [
    {
        "step": 1,
        "id": "browser_network_search",
        "title_key": "profiles.wizard_step_one",
        "fallback": "Browser, network & search",
        "policy_sections": ["browser_behavior", "network_access", "search"],
        "preference_sections": ["general", "search"],
    },
    {
        "step": 2,
        "id": "urls_sites_navigation",
        "title_key": "profiles.wizard_step_two",
        "fallback": "URLs, sites & navigation",
        "policy_sections": ["home_startup", "urls_sites_navigation"],
        "preference_sections": ["home"],
    },
    {
        "step": 3,
        "id": "security_privacy",
        "title_key": "profiles.wizard_step_three",
        "fallback": "Security & privacy",
        "policy_sections": ["privacy_security"],
        "preference_sections": ["privacy"],
    },
    {
        "step": 4,
        "id": "certificates_trust",
        "title_key": "profiles.wizard_step_four",
        "fallback": "Certificates & trust",
        "policy_sections": [],
        "preference_sections": [],
    },
    {
        "step": 5,
        "id": "users_language_sync",
        "title_key": "profiles.wizard_step_five",
        "fallback": "Users, language & sync",
        "policy_sections": ["sync_accounts"],
        "preference_sections": ["sync"],
    },
    {
        "step": 6,
        "id": "extensions",
        "title_key": "profiles.wizard_step_six",
        "fallback": "Extensions",
        "policy_sections": [],
        "preference_sections": [],
    },
    {
        "step": 7,
        "id": "ai",
        "title_key": "profiles.wizard_step_seven",
        "fallback": "AI",
        "policy_sections": ["ai_smart"],
        "preference_sections": [],
    },
    {
        "step": 8,
        "id": "review_export",
        "title_key": "profiles.wizard_step_eight",
        "fallback": "Review & export",
        "policy_sections": ["advanced", "extensions_integrations"],
        "preference_sections": [],
    },
]


def get_wizard_schema_shell_catalog(
    preferences_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return schema-driven wizard shell data for all supported channels."""

    resolved_preferences = preferences_catalog or get_wizard_preferences_catalog()
    preferences_by_id = _build_preferences_by_id(resolved_preferences)

    channel_data = {
        channel: {
            "schema_label": _format_schema_label(channel),
            "steps": {
                str(step["step"]): _build_channel_step_shell(
                    load_policy_schema(channel),
                    step,
                    preferences_by_id,
                )
                for step in WIZARD_SHELL_STEPS
            },
            "certificate_trust_posture": {
                "policy_ids": [
                    policy_id
                    for policy_id in CERTIFICATE_TRUST_POSTURE_POLICY_IDS
                    if policy_id in load_policy_schema(channel).policies
                ],
            },
            "certificate_trust": {
                "policy_ids": sorted(
                    CERTIFICATE_TRUST_GUIDED_POLICY_IDS & set(load_policy_schema(channel).policies)
                ),
            },
        }
        for channel in SUPPORTED_POLICY_CHANNELS
    }

    return {
        "steps": [
            {
                "step": step["step"],
                "id": step["id"],
                "title_key": step["title_key"],
                "fallback": step["fallback"],
            }
            for step in WIZARD_SHELL_STEPS
        ],
        "channels": channel_data,
    }


def _build_preferences_by_id(resolved_preferences: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        section["id"]: {
            "id": section["id"],
            "title_key": section["title_key"],
            "fallback": humanize_identifier(section["id"]),
            "body_key": section["body_key"],
            "target": f"pref-section:{section['id']}",
            "prefix_count": len(section.get("prefixes") or []),
            "preset_count": len(section.get("presets") or []),
        }
        for section in resolved_preferences.get("sections", [])
    }


def _build_channel_step_shell(
    schema,
    step_meta: dict[str, Any],
    preferences_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    policies = [
        definition
        for definition in schema.policies.values()
        if definition.ui is not None
        and definition.ui.section in step_meta["policy_sections"]
        and definition.id not in CERTIFICATE_TRUST_GUIDED_POLICY_IDS
    ]

    recommended = sorted(
        (
            serialize_policy(
                definition,
                step_meta["step"],
                inline_editor_builder=build_inline_editor,
            )
            for definition in policies
            if definition.ui.support_level == "mapped" and definition.ui.recommended
        ),
        key=lambda item: item["label"],
    )
    additional = sorted(
        (
            serialize_policy(
                definition,
                step_meta["step"],
                inline_editor_builder=build_inline_editor,
            )
            for definition in policies
            if definition.ui.support_level == "mapped" and not definition.ui.recommended
        ),
        key=lambda item: item["label"],
    )
    raw_fallback = sorted(
        (
            serialize_policy(
                definition,
                step_meta["step"],
                inline_editor_builder=build_inline_editor,
            )
            for definition in policies
            if definition.ui.support_level == "fallback"
        ),
        key=lambda item: item["label"],
    )
    preferences = [
        preferences_by_id[section_id]
        for section_id in step_meta["preference_sections"]
        if section_id in preferences_by_id
    ]

    return {
        "recommended": recommended,
        "additional": additional,
        "raw_fallback": raw_fallback,
        "preferences": preferences,
        "compatibility": {
            "total": len(policies),
            "mapped": len(recommended) + len(additional),
            "recommended": len(recommended),
            "additional": len(additional),
            "raw_fallback": len(raw_fallback),
            "deprecated": sum(1 for definition in policies if definition.deprecated),
        },
    }


def _format_schema_label(channel: str) -> str:
    return get_schema_label(channel)
