#!/usr/bin/env python3
"""Generate Firefox policy DITA skeletons from the maintained documentation inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DEFAULT_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
)
DEFAULT_MODEL = DOCUMENTATION_ROOT / "config/firefox-policy-topic-model-0.9.0.json"
DEFAULT_OUTPUT = DOCUMENTATION_ROOT / "src/generated/firefox"
DEFAULT_SCHEMA_ROOT = REPOSITORY_ROOT / "app/schemas/policies"
POLICIES_DIRNAME = "policies"
MAP_FILENAME = "firefox-policy-skeletons.ditamap"
INDEX_FILENAME = "firefox-policy-skeletons-0.9.0.json"
CHANNEL_DIFFERENCES_FILENAME = "firefox-policy-channel-differences-0.9.0.json"
PROVENANCE_REVIEW_FILENAME = "firefox-policy-provenance-review-0.9.0.json"
GENERATOR_NAME = "documentation/tools/generate_firefox_policy_skeletons.py"
HAND_REGION_PATTERN = re.compile(
    r"(<!-- BPM-HAND-REGION-START (?P<name>[a-z0-9-]+) -->\n)"
    r"(?P<body>.*?)"
    r"(\n\s*<!-- BPM-HAND-REGION-END (?P=name) -->)",
    re.DOTALL,
)


@dataclass(frozen=True)
class GeneratedFile:
    path: Path
    content: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _json_block(payload: object) -> str:
    return _escape(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _policy_sort_key(policy: dict[str, Any]) -> tuple[str, str]:
    policy_id = policy["policy_id"]
    return (policy_id.casefold(), policy_id)


def _existing_regions(existing_text: str | None) -> dict[str, str]:
    if not existing_text:
        return {}
    return {
        match.group("name"): match.group("body")
        for match in HAND_REGION_PATTERN.finditer(existing_text)
    }


def _default_region(region: str, policy_id: str) -> str:
    defaults = {
        "purpose": (
            f"      <p><codeph>{_escape(policy_id)}</codeph> has a generated schema skeleton. "
            "Reviewed runtime guidance is added in the authored Firefox Policy Guide tasks.</p>"
        ),
        "reviewed-examples": (
            "      <p>Reviewed example guidance can add practical notes without changing the "
            "schema-valid generated examples above.</p>"
        ),
        "validation": (
            f"      <p>BPM validates this policy at <codeph>policies.{_escape(policy_id)}</codeph> "
            "against the selected Firefox schema channel. Reviewed validation guidance is pending.</p>"
        ),
        "caveats": (
            "      <p>Reviewed deployment, schema, unsupported-channel, and raw fallback caveats are pending.</p>"
        ),
        "interactions": (
            "      <p>Reviewed related-policy, managed-preference, conflict, and override guidance is pending.</p>"
        ),
        "cis-links": (
            "      <p>No reviewed CIS recommendation links are assigned in this skeleton.</p>"
        ),
    }
    return defaults[region]


def _region(name: str, policy_id: str, existing: dict[str, str]) -> str:
    body = existing.get(name, _default_region(name, policy_id))
    if (
        name == "reviewed-examples"
        and "no-schema-valid-example" in body
        and "policy example task after the schema-grounded skeleton is approved" in body
    ):
        body = _default_region(name, policy_id)
    return (
        f"    <!-- BPM-HAND-REGION-START {name} -->\n"
        f"{body}\n"
        f"    <!-- BPM-HAND-REGION-END {name} -->"
    )


def _channel_props(policy: dict[str, Any]) -> str:
    channels = policy["channels"]
    props = []
    if any(channel_id.startswith("release-") for channel_id in channels):
        props.append("firefox-release")
    if any(channel_id.startswith("esr-") for channel_id in channels):
        props.append("firefox-esr")
    if not props:
        raise ValueError(f"policy {policy['policy_id']} has no supported channel")
    return " ".join(props)


def _channel_display_name(channel_id: str) -> str:
    if channel_id.startswith("release-"):
        return f"Firefox Release {channel_id.removeprefix('release-')}"
    if channel_id.startswith("esr-"):
        return f"Firefox ESR {channel_id.removeprefix('esr-')}"
    return channel_id


def _channel_sort_key(channel_id: str) -> tuple[int, str]:
    if channel_id.startswith("release-"):
        return (0, channel_id)
    if channel_id.startswith("esr-"):
        return (1, channel_id)
    return (2, channel_id)


def _source_metadata(source: str) -> dict[str, str]:
    version = source.removeprefix("mozilla-policy-templates-")
    return {
        "source_locator": f"https://github.com/mozilla/policy-templates/releases/tag/{version}",
        "source_version_or_revision": source,
        "source_retrieved_on": "2026-07-22" if version == "v8.0" else "2026-03-24",
    }


def _channel_support(policy: dict[str, Any]) -> dict[str, Any]:
    channels = sorted(policy["channels"], key=_channel_sort_key)
    return {
        "scope": policy["channel_scope"],
        "supported_channels": channels,
        "release_supported": any(channel_id.startswith("release-") for channel_id in channels),
        "esr_supported": any(channel_id.startswith("esr-") for channel_id in channels),
        "definition_changed_across_channels": policy["definition_changed_across_channels"],
    }


def _support_badge_text(policy: dict[str, Any], all_channels: dict[str, Any]) -> str:
    support = _channel_support(policy)
    supported = ", ".join(
        _channel_display_name(channel_id) for channel_id in support["supported_channels"]
    )
    absent = [
        _channel_display_name(channel_id)
        for channel_id in sorted(all_channels, key=_channel_sort_key)
        if channel_id not in support["supported_channels"]
    ]
    if not absent:
        return f"Supported in {supported}."
    return f"Supported in {supported}; absent from {', '.join(absent)}."


def _example_string(schema: dict[str, Any]) -> str:
    pattern = schema.get("pattern", "")
    if "{searchTerms}" in pattern or "\\{searchTerms\\}" in pattern:
        return "https://search.example.invalid/?q={searchTerms}"
    if "%s" in pattern:
        return "https://handler.example.invalid/?value=%s"
    if pattern.startswith("^https?://") or pattern.startswith("^https://"):
        return "https://example.invalid/"
    if schema.get("format") in {"uri", "url"}:
        return "https://example.invalid/"
    return "example"


def _example_value(schema: dict[str, Any], depth: int = 0) -> Any:
    if "default" in schema:
        return schema["default"]
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    if "oneOf" in schema:
        return _example_value(schema["oneOf"][0], depth + 1)
    if "anyOf" in schema:
        return _example_value(schema["anyOf"][0], depth + 1)

    value_type = schema.get("type")
    if isinstance(value_type, list):
        value_type = next((item for item in value_type if item != "null"), value_type[0])

    if value_type == "boolean":
        return True
    if value_type == "integer":
        return schema.get("minimum", 1)
    if value_type == "number":
        return schema.get("minimum", 1)
    if value_type == "string":
        return _example_string(schema)
    if value_type == "array":
        return [_example_value(schema.get("items", {}), depth + 1)]
    if value_type == "object" or "properties" in schema:
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        keys = required or list(properties)[:1]
        return {
            key: _example_value(properties[key], depth + 1) for key in keys if key in properties
        }

    return True


def _schema_path(channel_id: str, inventory: dict[str, Any]) -> Path:
    return DEFAULT_SCHEMA_ROOT / inventory["channels"][channel_id]["filename"]


def _policy_examples(
    policy: dict[str, Any],
    inventory: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    examples = []
    for channel_id in sorted(policy["channels"]):
        policy_schema = schemas[channel_id]["properties"][policy["policy_id"]]
        document = {"policies": {policy["policy_id"]: _example_value(policy_schema)}}
        examples.append(
            {
                "id": f"{policy['doc_id']}-{channel_id}",
                "channel": channel_id,
                "document": document,
                "validates": True,
                "purpose": "Minimal schema-valid Firefox boundary document.",
                "notes": [
                    "Synthetic documentation fixture; replace example.invalid values before deployment.",
                    f"Schema source: {inventory['channels'][channel_id]['schema_source']}.",
                ],
            }
        )
    return examples


def _examples_dita(examples: list[dict[str, Any]]) -> str:
    entries = []
    for example in examples:
        entries.append(
            '      <sectiondiv outputclass="schema-valid-example">'
            f"<p><codeph>{_escape(example['channel'])}</codeph> schema-valid example "
            f"<codeph>{_escape(example['id'])}</codeph>:</p>"
            f'<codeblock outputclass="language-json">{_json_block(example["document"])}</codeblock>'
            "</sectiondiv>"
        )
    return "\n".join(entries)


def _channel_summary(policy: dict[str, Any], channels: dict[str, Any]) -> str:
    items = []
    for channel_id, channel in channels.items():
        channel_meta = channel["ui"]
        items.append(
            "        <li>"
            f"<codeph>{_escape(channel_id)}</codeph>: type <codeph>{_escape(channel['value_type'])}</codeph>, "
            f"min <codeph>{_escape(channel['min_version'])}</codeph>, "
            f"max <codeph>{_escape(channel['max_version'] or 'none')}</codeph>, "
            f"deprecated <codeph>{str(channel['deprecated']).lower()}</codeph>, "
            f"UI <codeph>{_escape(channel_meta['section'])}/{_escape(channel_meta['subsection'])}</codeph> "
            f"as <codeph>{_escape(channel_meta['support_level'])}</codeph> "
            f"with <codeph>{_escape(channel_meta['widget'])}</codeph>."
            "</li>"
        )
    if policy["channel_scope"] in {"partial", "release-only", "esr-only"}:
        items.append(
            '        <li outputclass="channel-absence-note">This policy is not available on every '
            "supported BPM Firefox schema channel and must retain its channel-specific availability.</li>"
        )
    if policy["definition_changed_across_channels"]:
        items.append("        <li>The schema definition changes across supported channels.</li>")
    return "\n".join(items)


def _channel_conditional_notes(policy: dict[str, Any], all_channels: dict[str, Any]) -> str:
    notes = []
    supported = set(policy["channels"])
    for channel_id in sorted(all_channels, key=_channel_sort_key):
        props = "firefox-release" if channel_id.startswith("release-") else "firefox-esr"
        state = (
            "supports this policy"
            if channel_id in supported
            else "does not include this policy in the bundled schema"
        )
        notes.append(f'      <p props="{props}">{_channel_display_name(channel_id)} {state}.</p>')
    return "\n".join(notes)


def _value_shape(policy: dict[str, Any], channels: dict[str, Any]) -> str:
    value_types = sorted({channel["value_type"] for channel in channels.values()})
    preserve_unknown = any(
        channel["ui"]["preserve_unknown_fields"] for channel in channels.values()
    )
    return (
        f"      <p>Schema value type: <codeph>{_escape(', '.join(value_types))}</codeph>. "
        f"Unknown nested fields preserved by BPM UI metadata: "
        f"<codeph>{str(preserve_unknown).lower()}</codeph>.</p>"
    )


def _bpm_location(channels: dict[str, Any]) -> str:
    entries = []
    for channel_id, channel in channels.items():
        ui = channel["ui"]
        entries.append(
            "        <dlentry>"
            f"<dt><codeph>{_escape(channel_id)}</codeph></dt>"
            f"<dd>Section <codeph>{_escape(ui['section'])}</codeph>, subsection "
            f"<codeph>{_escape(ui['subsection'])}</codeph>, support "
            f"<codeph>{_escape(ui['support_level'])}</codeph>, widget "
            f"<codeph>{_escape(ui['widget'])}</codeph>, complexity "
            f"<codeph>{_escape(ui['complexity'])}</codeph>.</dd>"
            "</dlentry>"
        )
    return "\n".join(entries)


def _provenance(policy: dict[str, Any], inventory: dict[str, Any]) -> str:
    lines = [
        "        <li>Source family: <codeph>mozilla-policy-schema-facts</codeph>.</li>",
        "        <li>Reuse mode: <codeph>generated-facts</codeph> with BPM-authored guidance regions.</li>",
        "        <li>License: <codeph>MPL-2.0</codeph>.</li>",
        "        <li>BPM is not affiliated with or endorsed by Mozilla.</li>",
        f"        <li>Inventory backlog item: <codeph>{_escape(inventory['backlog_item'])}</codeph>.</li>",
        f"        <li>Generated for BPM: <codeph>{_escape(inventory['generated_for_bpm'])}</codeph>.</li>",
    ]
    source_records = {
        inventory["channels"][channel_id]["schema_source"] for channel_id in policy["channels"]
    }
    for source in sorted(source_records):
        metadata = _source_metadata(source)
        lines.append(
            "        <li>Mozilla source locator: "
            f"<codeph>{_escape(metadata['source_locator'])}</codeph>; source retrieved on "
            f"<codeph>{_escape(metadata['source_retrieved_on'])}</codeph>.</li>"
        )
    for channel_id, channel in policy["channels"].items():
        channel_meta = inventory["channels"][channel_id]
        lines.append(
            "        <li>"
            f"<codeph>{_escape(channel_id)}</codeph>: Mozilla version "
            f"<codeph>{_escape(channel_meta['mozilla_version'])}</codeph>, schema source "
            f"<codeph>{_escape(channel_meta['schema_source'])}</codeph>, schema SHA-256 "
            f"<codeph>{_escape(channel['schema_sha256'])}</codeph>."
            "</li>"
        )
    return "\n".join(lines)


def _topic_content(
    policy: dict[str, Any],
    inventory: dict[str, Any],
    model: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    existing_text: str | None,
) -> str:
    policy_id = policy["policy_id"]
    doc_id = policy["doc_id"]
    channels = {
        channel_id: policy["channels"][channel_id]
        for channel_id in model["channel_support_model"]["supported_channels"]
        if channel_id in policy["channels"]
    }
    regions = _existing_regions(existing_text)
    section_titles = {section["id"]: section["title"] for section in model["required_sections"]}
    examples = _policy_examples(policy, inventory, schemas)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="{_escape(doc_id)}" audience="user" product="bpm-0-9-0" platform="web" props="{_channel_props(policy)}" otherprops="policy({_escape(policy_id)})">
  <title>{_escape(policy_id)}</title>
  <shortdesc>Schema-grounded skeleton for the Firefox <codeph>{_escape(policy_id)}</codeph> policy.</shortdesc>
  <refbody>
    <section id="a-purpose">
      <title>{_escape(section_titles["a-purpose"])}</title>
{_region("purpose", policy_id, regions)}
    </section>
    <section id="a-bpm-location">
      <title>{_escape(section_titles["a-bpm-location"])}</title>
      <p>UI target: <codeph>{_escape(policy["ui_target"])}</codeph>.</p>
      <dl>
{_bpm_location(channels)}
      </dl>
    </section>
    <section id="a-value-shape">
      <title>{_escape(section_titles["a-value-shape"])}</title>
{_value_shape(policy, channels)}
    </section>
    <section id="a-channel-support">
      <title>{_escape(section_titles["a-channel-support"])}</title>
      <p outputclass="channel-support-badge channel-scope-{_escape(policy["channel_scope"])}">{_escape(_support_badge_text(policy, inventory["channels"]))}</p>
      <p>Channel scope: <codeph>{_escape(policy["channel_scope"])}</codeph>.</p>
{_channel_conditional_notes(policy, inventory["channels"])}
      <ul>
{_channel_summary(policy, channels)}
      </ul>
    </section>
    <section id="a-examples">
      <title>{_escape(section_titles["a-examples"])}</title>
{_examples_dita(examples)}
{_region("reviewed-examples", policy_id, regions)}
    </section>
    <section id="a-validation">
      <title>{_escape(section_titles["a-validation"])}</title>
{_region("validation", policy_id, regions)}
    </section>
    <section id="a-caveats">
      <title>{_escape(section_titles["a-caveats"])}</title>
{_region("caveats", policy_id, regions)}
    </section>
    <section id="a-interactions">
      <title>{_escape(section_titles["a-interactions"])}</title>
{_region("interactions", policy_id, regions)}
    </section>
    <section id="a-cis-links">
      <title>{_escape(section_titles["a-cis-links"])}</title>
{_region("cis-links", policy_id, regions)}
    </section>
    <section id="a-provenance">
      <title>{_escape(section_titles["a-provenance"])}</title>
      <ul>
{_provenance(policy, inventory)}
      </ul>
    </section>
  </refbody>
  <related-links>
    <link keyref="topic.ug-task-choose-firefox-schema"/>
    <link keyref="topic.ug-task-use-all-settings"/>
    <link keyref="topic.ug-task-export-policies-json"/>
  </related-links>
</reference>
"""


def _map_content(policies: list[dict[str, Any]]) -> str:
    topicrefs = "\n".join(
        f'  <topicref keys="topic.{_escape(policy["doc_id"])}" '
        f'href="{POLICIES_DIRNAME}/{_escape(policy["doc_id"])}.dita"/>'
        for policy in policies
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="map-generated-firefox-policy-skeletons">
  <title>Generated Firefox policy skeletons</title>
{topicrefs}
</map>
"""


def _index_content(
    policies: list[dict[str, Any]],
    inventory: dict[str, Any],
    inventory_path: Path,
    model_path: Path,
    output_root: Path,
    schemas: dict[str, dict[str, Any]],
) -> str:
    payload = {
        "schema_version": 1,
        "backlog_item": "BPM090-M5-02",
        "example_backlog_item": "BPM090-M5-04",
        "channel_differences_backlog_item": "BPM090-M5-05",
        "schema_refresh_runbook_backlog_item": "BPM090-M5-08",
        "provenance_review_backlog_item": "BPM090-M5-09",
        "target_bpm_version": "0.9.0",
        "generated_by": GENERATOR_NAME,
        "source_inventory": str(inventory_path.relative_to(REPOSITORY_ROOT)),
        "source_inventory_sha256": _sha256(inventory_path),
        "source_model": str(model_path.relative_to(REPOSITORY_ROOT)),
        "source_model_sha256": _sha256(model_path),
        "map": _display_path(output_root / MAP_FILENAME),
        "policy_count": len(policies),
        "example_count": sum(len(policy["channels"]) for policy in policies),
        "policies": [
            {
                "policy_id": policy["policy_id"],
                "doc_id": policy["doc_id"],
                "channel_scope": policy["channel_scope"],
                "channel_support": _channel_support(policy),
                "examples": _policy_examples(policy, inventory, schemas),
                "path": _display_path(output_root / POLICIES_DIRNAME / f"{policy['doc_id']}.dita"),
            }
            for policy in policies
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _channel_differences_content(
    policies: list[dict[str, Any]],
    inventory: dict[str, Any],
    inventory_path: Path,
    output_root: Path,
) -> str:
    release_only = [
        policy["policy_id"] for policy in policies if policy["channel_scope"] == "release-only"
    ]
    esr_only = [policy["policy_id"] for policy in policies if policy["channel_scope"] == "esr-only"]
    both = [policy["policy_id"] for policy in policies if policy["channel_scope"] == "both"]
    partial = [policy["policy_id"] for policy in policies if policy["channel_scope"] == "partial"]
    changed = [
        policy["policy_id"] for policy in policies if policy["definition_changed_across_channels"]
    ]
    payload = {
        "schema_version": 1,
        "backlog_item": "BPM090-M5-05",
        "schema_refresh_runbook_backlog_item": "BPM090-M5-08",
        "provenance_review_backlog_item": "BPM090-M5-09",
        "target_bpm_version": "0.9.0",
        "generated_by": GENERATOR_NAME,
        "source_inventory": str(inventory_path.relative_to(REPOSITORY_ROOT)),
        "source_inventory_sha256": _sha256(inventory_path),
        "channels": inventory["channels"],
        "summary": {
            "both_channels": len(both),
            "release_only": len(release_only),
            "esr_only": len(esr_only),
            "partial": len(partial),
            "changed_definitions": len(changed),
        },
        "policy_ids": {
            "both_channels": both,
            "release_only": release_only,
            "esr_only": esr_only,
            "partial": partial,
            "changed_definitions": changed,
        },
        "search_and_navigation_contract": {
            "filter_fields": [
                "channel_support.scope",
                "channel_support.release_supported",
                "channel_support.esr_supported",
                "channel_support.supported_channels",
            ],
            "display_badge_outputclass": "channel-support-badge",
            "generated_topic_section": "a-channel-support",
        },
        "path": _display_path(output_root / CHANNEL_DIFFERENCES_FILENAME),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _provenance_review_content(
    policies: list[dict[str, Any]],
    inventory: dict[str, Any],
    inventory_path: Path,
    model_path: Path,
    output_root: Path,
    schemas: dict[str, dict[str, Any]],
) -> str:
    policy_records = []
    for policy in policies:
        channels = []
        for channel_id in sorted(policy["channels"]):
            channel_meta = inventory["channels"][channel_id]
            channels.append(
                {
                    "channel": channel_id,
                    "schema_file": f"app/schemas/policies/{channel_meta['filename']}",
                    "schema_source": channel_meta["schema_source"],
                    "mozilla_version": channel_meta["mozilla_version"],
                    "schema_version": channel_meta["schema_version"],
                    "schema_sha256": policy["channels"][channel_id]["schema_sha256"],
                    "topic_section_id": "a-provenance",
                    **_source_metadata(channel_meta["schema_source"]),
                }
            )
        source_records = {
            channel["source_version_or_revision"]: {
                key: channel[key]
                for key in ("source_locator", "source_version_or_revision", "source_retrieved_on")
            }
            for channel in channels
        }
        policy_records.append(
            {
                "policy_id": policy["policy_id"],
                "doc_id": policy["doc_id"],
                "topic_path": _display_path(
                    output_root / POLICIES_DIRNAME / f"{policy['doc_id']}.dita"
                ),
                "source_family_id": "mozilla-policy-schema-facts",
                "source_records": list(source_records.values()),
                "source_content_sha256_when_snapshotted": {
                    channel_id: policy["channels"][channel_id]["schema_sha256"]
                    for channel_id in sorted(policy["channels"])
                },
                "license_id": "MPL-2.0",
                "reuse_mode": "generated-facts",
                "authoring_owner": "BPM Firefox schema maintainer",
                "reviewed_by": [
                    "BPM documentation maintainer",
                    "BPM localization maintainer",
                ],
                "rights_approval_id_when_required": None,
                "localized_from_topic_id_when_not_en": None,
                "no_affiliation_notice": "BPM is not affiliated with or endorsed by Mozilla.",
                "copied_mozilla_prose": False,
                "live_browser_verification_claim": False,
                "channel_support": _channel_support(policy),
                "supported_channels": sorted(policy["channels"]),
                "channels": channels,
                "example_ids": [
                    example["id"] for example in _policy_examples(policy, inventory, schemas)
                ],
            }
        )

    payload = {
        "schema_version": 1,
        "backlog_item": "BPM090-M5-09",
        "target_bpm_version": "0.9.0",
        "generated_by": GENERATOR_NAME,
        "source_inventory": str(inventory_path.relative_to(REPOSITORY_ROOT)),
        "source_inventory_sha256": _sha256(inventory_path),
        "source_model": str(model_path.relative_to(REPOSITORY_ROOT)),
        "source_model_sha256": _sha256(model_path),
        "source_matrix": "docs/architecture/product-documentation-provenance-matrix-0.9.0.json",
        "source_family_id": "mozilla-policy-schema-facts",
        "source_records": sorted(
            {
                channel["schema_source"]: _source_metadata(channel["schema_source"])
                for channel in inventory["channels"].values()
            }.values(),
            key=lambda record: record["source_version_or_revision"],
        ),
        "license_id": "MPL-2.0",
        "reuse_mode": "generated-facts",
        "allowed_publication_policy": "allow-with-notice",
        "required_notice": [
            "Mozilla policy-templates repository and exact release tag.",
            "MPL-2.0 notice and retained source/version/hash metadata.",
            "BPM is not affiliated with or endorsed by Mozilla.",
        ],
        "forbidden_claims": [
            "copied-mozilla-prose-without-explicit-source-region",
            "live-browser-verification",
            "stale-channel-support",
            "missing-schema-fingerprint",
            "mozilla-affiliation-or-endorsement",
        ],
        "summary": {
            "policy_count": len(policies),
            "example_count": sum(len(policy["channels"]) for policy in policies),
            "release_only": len(
                [policy for policy in policies if policy["channel_scope"] == "release-only"]
            ),
            "both_channels": len(
                [policy for policy in policies if policy["channel_scope"] == "both"]
            ),
            "esr_only": len(
                [policy for policy in policies if policy["channel_scope"] == "esr-only"]
            ),
            "partial": len([policy for policy in policies if policy["channel_scope"] == "partial"]),
            "changed_definitions": len(
                [policy for policy in policies if policy["definition_changed_across_channels"]]
            ),
        },
        "policies": policy_records,
        "path": _display_path(output_root / PROVENANCE_REVIEW_FILENAME),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_generated_files(
    inventory_path: Path = DEFAULT_INVENTORY,
    model_path: Path = DEFAULT_MODEL,
    output_root: Path = DEFAULT_OUTPUT,
) -> list[GeneratedFile]:
    inventory = _load_json(inventory_path)
    model = _load_json(model_path)
    schemas = {
        channel_id: _load_json(_schema_path(channel_id, inventory))
        for channel_id in model["channel_support_model"]["supported_channels"]
    }
    policies = sorted(inventory["policies"], key=_policy_sort_key)
    files: list[GeneratedFile] = []
    for policy in policies:
        path = output_root / POLICIES_DIRNAME / f"{policy['doc_id']}.dita"
        existing_text = path.read_text(encoding="utf-8") if path.is_file() else None
        files.append(
            GeneratedFile(path, _topic_content(policy, inventory, model, schemas, existing_text))
        )
    files.append(GeneratedFile(output_root / MAP_FILENAME, _map_content(policies)))
    files.append(
        GeneratedFile(
            output_root / CHANNEL_DIFFERENCES_FILENAME,
            _channel_differences_content(policies, inventory, inventory_path, output_root),
        )
    )
    files.append(
        GeneratedFile(
            output_root / INDEX_FILENAME,
            _index_content(policies, inventory, inventory_path, model_path, output_root, schemas),
        )
    )
    files.append(
        GeneratedFile(
            output_root / PROVENANCE_REVIEW_FILENAME,
            _provenance_review_content(
                policies, inventory, inventory_path, model_path, output_root, schemas
            ),
        )
    )
    return files


def generate(
    inventory_path: Path = DEFAULT_INVENTORY,
    model_path: Path = DEFAULT_MODEL,
    output_root: Path = DEFAULT_OUTPUT,
) -> list[Path]:
    files = build_generated_files(inventory_path, model_path, output_root)
    expected = {generated.path for generated in files}
    policies_root = output_root / POLICIES_DIRNAME
    policies_root.mkdir(parents=True, exist_ok=True)
    for stale in (
        sorted(output_root.glob("*.ditamap"))
        + sorted(output_root.glob("*.json"))
        + sorted(policies_root.glob("*.dita"))
    ):
        if stale not in expected:
            stale.unlink()
    written = []
    for generated in files:
        generated.path.parent.mkdir(parents=True, exist_ok=True)
        generated.path.write_text(generated.content, encoding="utf-8")
        written.append(generated.path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    written = generate(args.inventory.resolve(), args.model.resolve(), args.output.resolve())
    print(
        f"Generated {len(written)} Firefox policy skeleton artifact(s) in {args.output}", flush=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
