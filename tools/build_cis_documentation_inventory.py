from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.compliance.firefox.cis.generation import build_all_cis_layers
from app.compliance.firefox.cis.validation import (
    BASE_DIR,
    load_yaml_file,
    validate_sources,
)
from app.core.schema_channels import SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "docs" / "architecture" / "cis-documentation-inventory-0.9.0.json"
PUBLISHABLE_MAPPING_STATUSES = {"mapped", "preference_mapped"}
PROVENANCE_ONLY_REASONS = {
    "needs_research": "No supported target is approved while mapping research remains unresolved.",
    "deprecated_or_removed": "No modern supported Firefox target exists; retain provenance only.",
}
STARTER_SOURCE_FILES = {
    "basic_corporate": "app/presets/basic_corporate.yaml",
    "classroom_kiosk": "app/presets/classroom_kiosk.yaml",
    "soc_hard": "app/presets/soc_hard.yaml",
}


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _recommendation_doc_id(recommendation_id: str) -> str:
    return f"cis-rec-{recommendation_id.replace('.', '-')}"


def _preference_doc_id(preference_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", preference_id.lower()).strip("-")
    return f"fx-pref-{slug}"


def _target_record(
    target: dict[str, Any],
    *,
    policy_doc_ids: dict[str, str],
    preference_doc_ids: dict[str, str],
) -> dict[str, Any]:
    kind = str(target["kind"])
    path = [str(part) for part in target.get("path") or []]
    target_id = path[0]
    if kind == "policy":
        target_doc_id = policy_doc_ids[target_id]
        ui_target = f"policy:{target_id}"
    elif kind == "preference":
        target_doc_id = preference_doc_ids[target_id]
        ui_target = f"known-preference:{target_id}"
    else:
        raise ValueError(f"Unsupported CIS documentation target kind: {kind!r}")

    return {
        "kind": kind,
        "merge_rule": target.get("merge_rule"),
        "path": path,
        "schema_channels": dict(sorted((target.get("schema_channels") or {}).items())),
        "target_doc_id": target_doc_id,
        "target_id": target_id,
        "ui_target": ui_target,
        "value": target.get("value"),
    }


def _starter_inventory(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    starters = []
    for starter_id in sorted(catalog["compliance_merged_presets"]):
        variants = []
        for layer_id, channels in sorted(catalog["compliance_merged_presets"][starter_id].items()):
            for schema_channel, variant in sorted(channels.items()):
                variants.append(
                    {
                        "decision_count": len(variant.get("decisions") or []),
                        "layer_id": layer_id,
                        "policy_top_level_count": len(variant.get("policy_values") or {}),
                        "review_required": int(variant.get("review_required") or 0),
                        "schema_channel": schema_channel,
                        "summary": dict(sorted((variant.get("summary") or {}).items())),
                    }
                )
        starters.append(
            {
                "source_file": STARTER_SOURCE_FILES.get(starter_id),
                "starter_id": starter_id,
                "variants": variants,
            }
        )
    return starters


def build_inventory() -> dict[str, Any]:
    validation = validate_sources()
    if not validation.ok or validation.warnings:
        raise ValueError(
            "CIS source validation must be clean before building documentation inventory: "
            f"errors={validation.errors!r}, warnings={validation.warnings!r}"
        )

    sources = load_yaml_file(BASE_DIR / "sources.yaml")
    benchmark_registry = sources["benchmarks"]
    if len(benchmark_registry) != 1:
        raise ValueError("BPM 0.9.0 CIS documentation inventory expects one registered benchmark")
    source_entry = benchmark_registry[0]
    source_document = load_yaml_file(BASE_DIR / source_entry["source_file"])
    mappings_document = load_yaml_file(BASE_DIR / source_entry["mapping_file"])
    merge_rules_document = load_yaml_file(BASE_DIR / "merge_rules.yaml")
    recommendations = source_document["recommendations"]
    mappings = mappings_document["mappings"]
    mappings_by_id = {entry["recommendation_id"]: entry for entry in mappings}

    policy_ids = set().union(
        *(set(load_policy_schema(channel.value).policies) for channel in SCHEMA_CHANNELS)
    )
    policy_doc_ids = {policy_id: f"fx-policy-{policy_id}" for policy_id in policy_ids}
    preferences_catalog = get_wizard_preferences_catalog()
    preference_doc_ids = {
        entry["pref"]: _preference_doc_id(entry["pref"])
        for entry in preferences_catalog["known_preferences"]
    }

    generated_layers = build_all_cis_layers()
    membership: dict[str, list[str]] = {}
    layer_records = []
    for layer in generated_layers:
        layer_id = f"cis-l{layer.level}.{layer.schema_channel}"
        for recommendation_id in layer.recommendation_ids:
            membership.setdefault(recommendation_id, []).append(layer_id)
        layer_document = layer.to_document()
        layer_records.append(
            {
                "document_sha256": _sha256_json(layer_document),
                "file": f"app/compliance/firefox/cis/generated/cis_l{layer.level}.{layer.schema_channel}.json",
                "layer_id": layer_id,
                "level": layer.level,
                "policy_top_level_count": len(layer.policies),
                "recommendation_count": len(layer.recommendation_ids),
                "schema_channel": layer.schema_channel,
            }
        )

    recommendation_records = []
    for recommendation in recommendations:
        recommendation_id = str(recommendation["id"])
        mapping = mappings_by_id[recommendation_id]
        mapping_status = str(mapping["status"])
        publishable = mapping_status in PUBLISHABLE_MAPPING_STATUSES
        targets = [
            _target_record(
                target,
                policy_doc_ids=policy_doc_ids,
                preference_doc_ids=preference_doc_ids,
            )
            for target in mapping.get("targets") or []
        ]
        recommendation_records.append(
            {
                "assessment": recommendation["assessment"],
                "category": recommendation["category"],
                "confidence": mapping["confidence"],
                "doc_id": _recommendation_doc_id(recommendation_id) if publishable else None,
                "generated_layers": sorted(membership.get(recommendation_id, [])),
                "has_mapping_reason": bool((mapping.get("notes") or {}).get("mapping_reason")),
                "has_review_note": bool((mapping.get("notes") or {}).get("review_note")),
                "level": recommendation["level"],
                "mapping_status": mapping_status,
                "non_publishable_reason": (
                    None if publishable else PROVENANCE_ONLY_REASONS[mapping_status]
                ),
                "publication_disposition": (
                    "planned-dita-topic" if publishable else "provenance-only-non-publishable"
                ),
                "provenance_id": f"cis-source-{recommendation_id}",
                "recommendation_id": recommendation_id,
                "scored": bool(recommendation.get("scored")),
                "source_section": recommendation["source_section"],
                "source_title_sha256": _sha256_text(str(recommendation["title"])),
                "targets": targets,
            }
        )

    doc_ids = [entry["doc_id"] for entry in recommendation_records if entry["doc_id"]]
    provenance_ids = [entry["provenance_id"] for entry in recommendation_records]
    if len(doc_ids) != len(set(doc_ids)):
        raise ValueError("CIS recommendation documentation IDs are not unique")
    if len(provenance_ids) != len(set(provenance_ids)):
        raise ValueError("CIS recommendation provenance IDs are not unique")

    targets = [target for entry in recommendation_records for target in entry["targets"]]
    mapping_status_counts = Counter(entry["mapping_status"] for entry in recommendation_records)
    level_counts = Counter(f"L{entry['level']}" for entry in recommendation_records)
    target_kind_counts = Counter(target["kind"] for target in targets)
    publication_counts = Counter(
        entry["publication_disposition"] for entry in recommendation_records
    )
    confidence_counts = Counter(entry["confidence"] for entry in recommendation_records)
    category_counts = Counter(entry["category"] for entry in recommendation_records)
    merge_rule_counts = Counter(target["merge_rule"] for target in targets)

    manual_review_paths = [
        {
            "path": dotted_path.split("."),
            "path_id": dotted_path,
            "reason": (
                rule.get("reason") if isinstance(rule, dict) else str(rule)
            ),
        }
        for dotted_path, rule in sorted(
            (merge_rules_document.get("manual_review_paths") or {}).items()
        )
    ]

    source_pdf = BASE_DIR / source_entry["official_source_pdf"]
    benchmark = {
        key: source_entry.get(key)
        for key in (
            "id",
            "upstream_name",
            "upstream_version",
            "product",
            "product_family",
            "release_window",
            "exact_release_date",
            "exact_release_date_status",
            "official_source_required",
            "official_source_status",
            "source_license",
            "source_terms_url",
            "source_license_url",
            "source_file",
            "mapping_file",
            "official_source_pdf",
            "source_pdf_pages",
            "tested_by_cis_against",
        )
    }
    benchmark["official_source_pdf_present"] = source_pdf.is_file()
    benchmark["source_content_redistribution_reviewed"] = False

    starter_catalog = get_wizard_starter_catalog()
    compliance_layers = [
        {
            "label_key": config["label_key"],
            "layer_id": layer_id,
            "level": config["level"],
            "summary_key": config["summary_key"],
        }
        for layer_id, config in sorted(starter_catalog["compliance_layers"].items())
    ]

    return {
        "backlog_item": "BPM090-M2-04",
        "benchmark": benchmark,
        "compliance_layer_options": compliance_layers,
        "exception_contract": {
            "persisted_exception_model": False,
            "statement": (
                "BPM records merge decisions and manual-review requirements but has no separate "
                "persisted CIS exception/waiver model."
            ),
        },
        "generated_for_bpm": "0.9.0",
        "generated_layers": sorted(layer_records, key=lambda entry: entry["layer_id"]),
        "manual_review_paths": manual_review_paths,
        "merge_contract": {
            "decision_types": [
                "added_from_cis",
                "already_satisfied",
                "cis_replaced_base",
                "kept_base_only",
                "kept_base_stricter",
                "manual_review_kept_base",
            ],
            "merge_rule_counts": dict(sorted(merge_rule_counts.items())),
        },
        "recommendations": recommendation_records,
        "schema_version": 1,
        "starter_presets": _starter_inventory(starter_catalog),
        "summary": {
            "category_counts": dict(sorted(category_counts.items())),
            "confidence_counts": dict(sorted(confidence_counts.items())),
            "level_counts": dict(sorted(level_counts.items())),
            "mapping_status_counts": dict(sorted(mapping_status_counts.items())),
            "publication_disposition_counts": dict(sorted(publication_counts.items())),
            "recommendation_count": len(recommendation_records),
            "target_count": len(targets),
            "target_kind_counts": dict(sorted(target_kind_counts.items())),
        },
    }


def render_inventory() -> str:
    return json.dumps(build_inventory(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the BPM 0.9.0 CIS documentation inventory."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the maintained inventory differs from current CIS sources and product data.",
    )
    args = parser.parse_args()
    rendered = render_inventory()

    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print(f"CIS documentation inventory is stale: {OUTPUT_PATH}")
            return 1
        print(f"CIS documentation inventory is current: {OUTPUT_PATH}")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote CIS documentation inventory: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
