from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.core.schema_channels import (
    DEFAULT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_SCHEMA_CHANNEL,
    LATEST_ESR_SCHEMA_CHANNEL,
    SCHEMA_CHANNELS,
)
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "docs" / "architecture" / "firefox-policy-documentation-inventory-0.9.0.json"
SUMMARY_PATH = ROOT / "docs" / "architecture" / "firefox-policy-documentation-inventory-0.9.0.md"


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
            "artifact_id": channel.artifact_id,
            "family": channel.family,
            "filename": channel.filename,
            # Keep the original field for inventory consumers, but derive it
            # from the explicit product-default role rather than a removed
            # singular/default compatibility attribute.
            "is_default": channel.value == DEFAULT_SCHEMA_CHANNEL,
            "is_default_release": channel.value == DEFAULT_RELEASE_SCHEMA_CHANNEL,
            "is_latest_esr": channel.value == LATEST_ESR_SCHEMA_CHANNEL,
            "is_product_default": channel.is_product_default,
            "label": channel.label,
            "line_id": channel.line_id,
            "line_number": channel.line_number,
            "mozilla_version": channel.mozilla_version,
            "policy_count": len(schema.policies),
            "schema_source": schema.source,
            "schema_version": schema.version,
            "selectable": channel.selectable,
            "support_state": channel.support_state,
            "recommendation_target_line_id": channel.recommendation_target_line_id,
            "retirement_successor_line_id": channel.retirement_successor_line_id,
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
        "backlog_item": "BPM095-M8-04",
        "channels": channel_metadata,
        "generated_for_bpm": "0.9.5",
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


def render_summary(inventory: dict[str, Any]) -> str:
    """Render the reader-facing inventory summary from the same data as JSON."""
    channels = inventory["channels"]
    summary = inventory["summary"]
    rows = "\n".join(
        "| `{channel_id}` | `{mozilla_version}` | {policy_count} | {support_state} | {role} |".format(
            channel_id=channel_id,
            mozilla_version=channel["mozilla_version"],
            policy_count=channel["policy_count"],
            support_state=channel["support_state"],
            role=(
                "product default and latest ESR"
                if channel["is_product_default"]
                else "default Release"
                if channel["is_default_release"]
                else "supported older ESR"
            ),
        )
        for channel_id, channel in channels.items()
    )
    by_id = {policy["policy_id"]: policy for policy in inventory["policies"]}
    esr_115 = set(by_id) & {
        policy_id for policy_id, policy in by_id.items() if "esr-115.38" in policy["channels"]
    }
    esr_140 = {
        policy_id for policy_id, policy in by_id.items() if "esr-140.13" in policy["channels"]
    }
    release = {
        policy_id for policy_id, policy in by_id.items() if "release-153" in policy["channels"]
    }
    return f"""# Firefox Policy Documentation Inventory (BPM 0.9.5)

Generated by `tools/build_firefox_policy_documentation_inventory.py`; do not edit manually.

Backlog item: `BPM095-M8-04`

Machine-readable inventory:
`docs/architecture/firefox-policy-documentation-inventory-0.9.0.json`

Regeneration command:

```bash
./.venv/bin/python tools/build_firefox_policy_documentation_inventory.py
```

Drift-check command:

```bash
./.venv/bin/python tools/build_firefox_policy_documentation_inventory.py --check
```

## Scope And Sources

This inventory derives only from the active lifecycle catalog in
`app/core/schema_channels.py`, its four bundled schemas, normalized
`PolicyDefinition` objects, UI registry metadata, and the known managed-preference
catalog. It records an exact artifact as supported only when the catalog marks it
selectable; a policy channel badge never infers support from a label or version.

## Channel Coverage

| Channel | Mozilla version | Policies | Support state | Lifecycle role |
| --- | --- | ---: | --- | --- |
{rows}

The policy union contains {summary["policy_union_count"]} stable IDs. {len(esr_115)} policies occur in all four
artifacts. {len(esr_140 - esr_115)} policies remain available in ESR 140.13 and the
153 artifacts but not ESR 115.38; {len(release - esr_140)} policies are available only
in the 153 artifacts. {summary["definition_changed_across_channels_count"]} common policies have
different definitions across the supported artifacts. The latest ESR and product
default are the explicit `esr-153.0` catalog roles; ESR 115.38 and ESR 140.13 remain
supported older ESR choices and are not automatically moved by documentation, UI, or
this inventory.

## Stable Documentation Contract

Each policy entry records its case-sensitive `policy_id`, stable `fx-policy-*`
document ID, `policy:*` UI target, exact available artifact channels, value shape,
schema fingerprint, UI support metadata, and unknown-field preservation rule. The
generated Firefox skeletons, All Settings targets, navigation, manifest, and locale
search indexes consume these identities through their owner commands; no generated
site, manifest, target map, or search artifact is edited by hand.

## Managed Preferences And Raw Behavior

The inventory also records {summary["managed_preference_count"]} known managed preferences with their exact
`known-preference:*` targets. Schema-known fallback policies remain supported and
linked; keys absent from the selected schema and unknown preferences remain raw or
imported attention items and do not gain a supported-policy claim.

## Audit Result

- Four current policy/channel badges derive from one lifecycle catalog.
- The product-default/latest-ESR and default-Release roles are explicit and unique.
- Generated policy skeletons receive one schema-valid example for every available
  exact artifact channel.
- The builder checks both the JSON inventory and this reader-facing summary, so a
  schema or lifecycle drift fails before documentation publication.
"""


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
    inventory = build_inventory()
    rendered = json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    summary = render_summary(inventory)
    total = len(inventory["channels"]) + 2
    print(f"firefox-policy-inventory: phase=channels; completed=0/{total}", flush=True)
    for position, channel_id in enumerate(inventory["channels"], start=1):
        print(
            f"firefox-policy-inventory: channel={channel_id}; completed={position}/{total}",
            flush=True,
        )

    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        current_summary = SUMMARY_PATH.read_text(encoding="utf-8") if SUMMARY_PATH.exists() else ""
        if current != rendered or current_summary != summary:
            print("Firefox policy documentation inventory is stale")
            return 1
        print(f"firefox-policy-inventory: artifact=json; completed={total - 1}/{total}", flush=True)
        print(f"firefox-policy-inventory: artifact=summary; completed={total}/{total}", flush=True)
        print("Firefox policy documentation inventory is current")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"firefox-policy-inventory: artifact=json; completed={total - 1}/{total}", flush=True)
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    print(f"firefox-policy-inventory: artifact=summary; completed={total}/{total}", flush=True)
    print("Firefox policy documentation inventory regenerated", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
