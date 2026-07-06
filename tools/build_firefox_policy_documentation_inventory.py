from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.core.schema_channels import SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = (
    ROOT / "docs" / "architecture" / "firefox-policy-documentation-inventory-0.9.0.json"
)


def _schema_path(filename: str) -> Path:
    return ROOT / "app" / "schemas" / "policies" / filename


def _fingerprint(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _preference_doc_id(preference_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", preference_id.lower()).strip("-")
    return f"fx-pref-{slug}"


def _policy_channel_record(policy: Any, raw_node: dict[str, Any]) -> dict[str, Any]:
    ui = policy.ui
    return {
        "categories": list(policy.categories),
        "deprecated": policy.deprecated,
        "description_key": policy.description_key,
        "max_version": policy.max_version,
        "min_version": policy.min_version,
        "schema_sha256": _fingerprint(raw_node),
        "ui": {
            "complexity": ui.complexity,
            "preserve_unknown_fields": ui.preserve_unknown_fields,
            "section": ui.section,
            "subsection": ui.subsection,
            "support_level": ui.support_level,
            "widget": ui.widget,
        },
        "value_type": policy.type,
    }


def build_inventory() -> dict[str, Any]:
    raw_schemas: dict[str, dict[str, Any]] = {}
    schemas = {}
    channel_metadata: dict[str, dict[str, Any]] = {}

    for channel in SCHEMA_CHANNELS:
        raw_schema = json.loads(_schema_path(channel.filename).read_text(encoding="utf-8"))
        schema = load_policy_schema(channel.value)
        raw_schemas[channel.value] = raw_schema
        schemas[channel.value] = schema
        support_counts = Counter(policy.ui.support_level for policy in schema.policies.values())
        type_counts = Counter(policy.type for policy in schema.policies.values())
        channel_metadata[channel.value] = {
            "family": channel.family,
            "filename": channel.filename,
            "is_default": channel.is_default,
            "mozilla_version": channel.mozilla_version,
            "policy_count": len(schema.policies),
            "schema_source": schema.source,
            "schema_version": schema.version,
            "type_counts": dict(sorted(type_counts.items())),
            "ui_support_counts": dict(sorted(support_counts.items())),
        }

    policy_ids = sorted(
        set().union(*(set(schema.policies) for schema in schemas.values())),
        key=str.casefold,
    )
    policies: list[dict[str, Any]] = []
    for policy_id in policy_ids:
        channels: dict[str, dict[str, Any]] = {}
        fingerprints: set[str] = set()
        for channel in SCHEMA_CHANNELS:
            policy = schemas[channel.value].policies.get(policy_id)
            raw_node = raw_schemas[channel.value].get("properties", {}).get(policy_id)
            if policy is None or not isinstance(raw_node, dict):
                continue
            record = _policy_channel_record(policy, raw_node)
            channels[channel.value] = record
            fingerprints.add(record["schema_sha256"])

        families = {channel.family for channel in SCHEMA_CHANNELS if channel.value in channels}
        if len(channels) == len(SCHEMA_CHANNELS):
            channel_scope = "both"
        elif families == {"release"}:
            channel_scope = "release-only"
        elif families == {"esr"}:
            channel_scope = "esr-only"
        else:
            channel_scope = "partial"

        policies.append(
            {
                "channel_scope": channel_scope,
                "channels": channels,
                "definition_changed_across_channels": len(fingerprints) > 1,
                "doc_id": f"fx-policy-{policy_id}",
                "policy_id": policy_id,
                "ui_target": f"policy:{policy_id}",
            }
        )

    preferences_catalog = get_wizard_preferences_catalog()
    managed_preferences = [
        {
            "can_autofill": preference["can_autofill"],
            "description_key": preference["description_key"],
            "doc_id": _preference_doc_id(preference["pref"]),
            "label_key": preference["label_key"],
            "preference_id": preference["pref"],
            "preset_ids": list(preference["preset_ids"]),
            "section_id": preference["section_id"],
            "status": preference["status"],
            "type": preference["type"],
            "ui_target": f"known-preference:{preference['pref']}",
            "value_control": preference["value_control"],
        }
        for preference in preferences_catalog["known_preferences"]
    ]

    policy_doc_ids = [entry["doc_id"] for entry in policies]
    preference_doc_ids = [entry["doc_id"] for entry in managed_preferences]
    if len(policy_doc_ids) != len(set(policy_doc_ids)):
        raise ValueError("Policy documentation IDs are not unique")
    if len(preference_doc_ids) != len(set(preference_doc_ids)):
        raise ValueError("Managed-preference documentation IDs are not unique")

    scope_counts = Counter(entry["channel_scope"] for entry in policies)
    changed_count = sum(entry["definition_changed_across_channels"] for entry in policies)
    preference_section_counts = Counter(entry["section_id"] for entry in managed_preferences)

    return {
        "backlog_item": "BPM090-M2-03",
        "channels": channel_metadata,
        "generated_for_bpm": "0.9.0",
        "managed_preferences": managed_preferences,
        "policies": policies,
        "raw_and_fallback_contract": {
            "fallback_support_level": (
                "Policies with ui.support_level=fallback use inferred schema-backed presentation "
                "and require explicit documentation review before publishing examples."
            ),
            "preserve_unknown_fields": (
                "Per-policy channel metadata records whether unknown nested fields must be "
                "preserved by editors."
            ),
            "unknown_managed_preference": (
                "Preferences outside managed_preferences remain editable as raw imported/unknown "
                "settings but do not receive a generated known-preference reference topic."
            ),
            "unknown_policy": (
                "Policy keys outside the selected bundled schema remain raw imported/unknown "
                "settings and must not be presented as supported policy topics."
            ),
        },
        "schema_version": 1,
        "summary": {
            "definition_changed_across_channels_count": changed_count,
            "managed_preference_count": len(managed_preferences),
            "managed_preference_section_counts": dict(sorted(preference_section_counts.items())),
            "policy_scope_counts": dict(sorted(scope_counts.items())),
            "policy_union_count": len(policies),
        },
    }


def render_inventory() -> str:
    return json.dumps(build_inventory(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the BPM 0.9.0 Firefox policy documentation inventory."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the maintained inventory differs from current schemas/catalogs.",
    )
    args = parser.parse_args()
    rendered = render_inventory()

    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print(f"Firefox policy documentation inventory is stale: {OUTPUT_PATH}")
            return 1
        print(f"Firefox policy documentation inventory is current: {OUTPUT_PATH}")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote Firefox policy documentation inventory: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
