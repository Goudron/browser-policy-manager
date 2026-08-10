#!/usr/bin/env python3
"""Generate CIS recommendation DITA skeletons from the maintained documentation inventory."""

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
DEFAULT_INVENTORY = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
DEFAULT_MODEL = DOCUMENTATION_ROOT / "config/cis-settings-topic-model-0.9.0.json"
DEFAULT_OUTPUT = DOCUMENTATION_ROOT / "src/generated/cis"
RECOMMENDATIONS_DIRNAME = "recommendations"
MAP_FILENAME = "cis-recommendation-skeletons.ditamap"
INDEX_FILENAME = "cis-recommendation-skeletons-0.9.0.json"
PROVENANCE_REVIEW_FILENAME = "cis-provenance-review-0.9.0.json"
GENERATOR_NAME = "documentation/tools/generate_cis_recommendation_skeletons.py"
CIS_DRIFT_GATE_RUNBOOK = (
    "documentation/runbooks/inventory-refresh.md#cis-benchmark-and-mapping-drift-gate"
)
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


def _json_inline(payload: object) -> str:
    return _escape(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _recommendation_sort_key(recommendation: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(part) for part in recommendation["recommendation_id"].split("."))


def _planned(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        recommendation
        for recommendation in recommendations
        if recommendation["publication_disposition"] == "planned-dita-topic"
    ]


def _provenance_only(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        recommendation
        for recommendation in recommendations
        if recommendation["publication_disposition"] == "provenance-only-non-publishable"
    ]


def _existing_regions(existing_text: str | None) -> dict[str, str]:
    if not existing_text:
        return {}
    return {
        match.group("name"): match.group("body")
        for match in HAND_REGION_PATTERN.finditer(existing_text)
    }


def _default_region(region: str, recommendation_id: str) -> str:
    defaults = {
        "bpm-authored-summary": (
            f"      <p>Reviewed BPM-authored rationale for CIS recommendation "
            f"<codeph>{_escape(recommendation_id)}</codeph> is pending. Keep this prose independent "
            "from the official benchmark expression.</p>"
        ),
        "conflicts": (
            "      <p>Reviewed conflict and exception guidance is pending. Use BPM source attribution "
            "and manual-review state before deciding whether to keep, replace, or document a value.</p>"
        ),
        "verification": (
            "      <p>Reviewed verification guidance is pending. Validate the selected Firefox schema "
            "channel, inspect exported paths, and perform independent runtime review outside BPM.</p>"
        ),
        "limitations": (
            "      <p>Reviewed limitation notes are pending. BPM records mappings and review states but "
            "does not provide a separate persisted CIS exception or waiver model in 0.9.0.</p>"
        ),
    }
    return defaults[region]


def _region(name: str, recommendation_id: str, existing: dict[str, str]) -> str:
    body = existing.get(name, _default_region(name, recommendation_id))
    return (
        f"    <!-- BPM-HAND-REGION-START {name} -->\n"
        f"{body}\n"
        f"    <!-- BPM-HAND-REGION-END {name} -->"
    )


def _props(recommendation: dict[str, Any], model: dict[str, Any]) -> str:
    if recommendation["level"] == 1:
        return model["topic"]["conditional_props"]["level_1"]
    if recommendation["level"] == 2:
        return model["topic"]["conditional_props"]["level_2"]
    raise ValueError(f"unsupported CIS level: {recommendation['level']}")


def _manual_review_path_ids(inventory: dict[str, Any]) -> set[str]:
    return {entry["path_id"] for entry in inventory["manual_review_paths"]}


def _target_path_id(target: dict[str, Any]) -> str:
    return ".".join(str(part) for part in target["path"])


def _target_layer_path(target: dict[str, Any]) -> list[str]:
    if target["kind"] == "preference":
        return ["Preferences", *target["path"]]
    return list(target["path"])


def _nested_value(document: dict[str, Any], path: list[str]) -> Any:
    current: Any = document["policies"]
    for part in path:
        current = current[part]
    return current


def _target_example(target: dict[str, Any]) -> dict[str, Any]:
    if target["kind"] == "preference":
        return {"policies": {"Preferences": {target["target_id"]: target["value"]}}}
    current: Any = target["value"]
    for part in reversed(target["path"][1:]):
        current = {part: current}
    return {"policies": {target["path"][0]: current}}


def _value_type(target: dict[str, Any]) -> str:
    value = target["value"]
    if target["kind"] == "preference" and isinstance(value, dict) and "Type" in value:
        return str(value["Type"])
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _lock_state(target: dict[str, Any]) -> str:
    value = target["value"]
    if target["kind"] == "preference" and isinstance(value, dict):
        return str(value.get("Status", "unknown"))
    if target["path"][-1] == "Locked":
        return "policy-locked" if value is True else "policy-unlocked"
    if isinstance(value, dict) and value.get("Locked") is True:
        return "policy-locked"
    return "not-a-lock-field"


def _firefox_topic_cell(target: dict[str, Any]) -> str:
    target_doc_id = _escape(target["target_doc_id"])
    if target["kind"] == "policy":
        return f'<xref keyref="topic.{target_doc_id}"><codeph>{target_doc_id}</codeph></xref>'
    return f"<codeph>{target_doc_id}</codeph>"


def _layer_checks(
    recommendation: dict[str, Any],
    inventory: dict[str, Any],
    target: dict[str, Any],
) -> list[dict[str, Any]]:
    layers = {layer["layer_id"]: layer for layer in inventory["generated_layers"]}
    checks: list[dict[str, Any]] = []
    for layer_id in recommendation["generated_layers"]:
        layer = layers[layer_id]
        layer_document = _load_json(REPOSITORY_ROOT / layer["file"])
        layer_value = _nested_value(layer_document, _target_layer_path(target))
        checks.append(
            {
                "layer_id": layer_id,
                "file": layer["file"],
                "schema_channel": layer["schema_channel"],
                "value_matches": layer_value == target["value"],
                "layer_value": layer_value,
            }
        )
    return checks


def _mapping_rows(
    recommendation: dict[str, Any], inventory: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "kind": target["kind"],
            "target_id": target["target_id"],
            "target_doc_id": target["target_doc_id"],
            "firefox_topic_key": f"topic.{target['target_doc_id']}",
            "ui_target": target["ui_target"],
            "path": target["path"],
            "path_id": _target_path_id(target),
            "value": target["value"],
            "value_type": _value_type(target),
            "lock_state": _lock_state(target),
            "schema_channels": target["schema_channels"],
            "merge_rule": target["merge_rule"],
            "layer_checks": _layer_checks(recommendation, inventory, target),
            "example_document": _target_example(target),
        }
        for target in recommendation["targets"]
    ]


def _mapping_table_dita(recommendation: dict[str, Any], inventory: dict[str, Any]) -> str:
    rows = _mapping_rows(recommendation, inventory)
    if not rows:
        return "      <p>No publishable BPM target is available for this recommendation.</p>"
    row_text = []
    for row in rows:
        channels = ", ".join(
            f"{channel}: {status}" for channel, status in sorted(row["schema_channels"].items())
        )
        layer_summary = ", ".join(
            f"{check['layer_id']}={str(check['value_matches']).lower()}"
            for check in row["layer_checks"]
        )
        row_text.append(
            f'        <strow outputclass="cis-mapping-row {row["kind"]}">'
            f"<stentry><codeph>{_escape(row['kind'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(row['target_id'])}</codeph></stentry>"
            f"<stentry>{_firefox_topic_cell(row)}</stentry>"
            f"<stentry><codeph>{_escape(row['ui_target'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(row['path_id'])}</codeph></stentry>"
            f"<stentry><codeph>{_json_inline(row['value'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(row['value_type'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(row['lock_state'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(channels)}</codeph></stentry>"
            f"<stentry><codeph>{_escape(row['merge_rule'])}</codeph></stentry>"
            f"<stentry><codeph>{_escape(layer_summary)}</codeph></stentry>"
            "</strow>"
        )
    return (
        '      <simpletable outputclass="cis-mapping-table">\n'
        "        <sthead>"
        "<stentry>Kind</stentry>"
        "<stentry>Target</stentry>"
        "<stentry>Firefox topic</stentry>"
        "<stentry>UI target</stentry>"
        "<stentry>Path</stentry>"
        "<stentry>Value</stentry>"
        "<stentry>Value type</stentry>"
        "<stentry>Lock state</stentry>"
        "<stentry>Channels</stentry>"
        "<stentry>Merge rule</stentry>"
        "<stentry>Layer checks</stentry>"
        "</sthead>\n" + "\n".join(row_text) + "\n      </simpletable>"
    )


def _mapping_examples_dita(recommendation: dict[str, Any], inventory: dict[str, Any]) -> str:
    rows = _mapping_rows(recommendation, inventory)
    examples = []
    for row in rows:
        examples.append(
            '      <sectiondiv outputclass="cis-mapping-example">'
            f"<p>Minimal BPM-owned boundary fragment for <codeph>{_escape(row['path_id'])}</codeph>:</p>"
            f'<codeblock outputclass="language-json">{_json_inline(row["example_document"])}</codeblock>'
            "</sectiondiv>"
        )
    return "\n".join(examples)


def _targets_dita(recommendation: dict[str, Any], inventory: dict[str, Any]) -> str:
    targets = recommendation["targets"]
    if not targets:
        return "      <p>No publishable BPM target is available for this recommendation.</p>"
    return (
        "      <p>The table lists BPM-owned mapping facts derived from shipped CIS layers, "
        "not text copied from the official benchmark.</p>\n"
        f"{_mapping_table_dita(recommendation, inventory)}\n"
        f"{_mapping_examples_dita(recommendation, inventory)}"
    )


def _manual_state_dita(recommendation: dict[str, Any], inventory: dict[str, Any]) -> str:
    review_paths = _manual_review_path_ids(inventory)
    matched_paths = [
        _target_path_id(target)
        for target in recommendation["targets"]
        if _target_path_id(target) in review_paths
    ]
    matched_text = ", ".join(matched_paths) if matched_paths else "none for this recommendation"
    return (
        f"      <p>Assessment: <codeph>{_escape(recommendation['assessment'])}</codeph>. "
        f"Generated layers: <codeph>{_json_inline(recommendation['generated_layers'])}</codeph>. "
        f"Manual-review paths matched by this skeleton: <codeph>{_escape(matched_text)}</codeph>.</p>\n"
        f"      <p>Global manual-review path count: <codeph>{len(inventory['manual_review_paths'])}</codeph>. "
        "BPM records review requirements and merge decisions. BPM has no separate persisted CIS exception or waiver model in 0.9.0.</p>"
    )


def _benchmark_dita(inventory: dict[str, Any]) -> str:
    benchmark = inventory["benchmark"]
    return (
        f"      <p>Benchmark ID <codeph>{_escape(benchmark['id'])}</codeph>; upstream name "
        f"<codeph>{_escape(benchmark['upstream_name'])}</codeph>; version "
        f"<codeph>{_escape(benchmark['upstream_version'])}</codeph>; release date "
        f"<codeph>{_escape(benchmark['exact_release_date'])}</codeph>; tested by CIS against "
        f"<codeph>{_escape(benchmark['tested_by_cis_against'])}</codeph>; source license "
        f"<codeph>{_escape(benchmark['source_license'])}</codeph>; official source required "
        f"<codeph>{str(benchmark['official_source_required']).lower()}</codeph>.</p>"
    )


def _provenance_dita(recommendation: dict[str, Any], inventory: dict[str, Any]) -> str:
    benchmark = inventory["benchmark"]
    return (
        "      <ul>\n"
        "        <li>Publishable source family: <codeph>bpm-cis-mapping-implementation</codeph>.</li>\n"
        "        <li>Restricted benchmark source family: <codeph>cis-benchmark-pdf</codeph>.</li>\n"
        f"        <li>Source license: <codeph>{_escape(benchmark['source_license'])}</codeph>; publication policy: <codeph>approval-required for benchmark expression</codeph>.</li>\n"
        f"        <li>Recommendation source hash: <codeph>{_escape(recommendation['source_title_sha256'])}</codeph>.</li>\n"
        f"        <li>Provenance record: <codeph>{_escape(recommendation['provenance_id'])}</codeph>.</li>\n"
        "        <li>The official CIS PDF and source expression are not copied, translated, indexed, or packaged by this skeleton.</li>\n"
        "        <li>BPM is an independent implementation and is not authorized, sponsored, endorsed, certified, or approved by CIS.</li>\n"
        "      </ul>"
    )


def _topic_content(
    recommendation: dict[str, Any],
    inventory: dict[str, Any],
    model: dict[str, Any],
    existing_text: str | None,
) -> str:
    recommendation_id = recommendation["recommendation_id"]
    doc_id = recommendation["doc_id"]
    regions = _existing_regions(existing_text)
    section_titles = {section["id"]: section["title"] for section in model["required_sections"]}
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="{_escape(doc_id)}" audience="user security-reviewer" product="bpm-0-9-0" platform="web" props="{_escape(_props(recommendation, model))}" otherprops="cis({_escape(recommendation_id)})">
  <title>CIS recommendation {_escape(recommendation_id)}</title>
  <shortdesc>BPM-generated skeleton for CIS recommendation <codeph>{_escape(recommendation_id)}</codeph>, containing BPM-owned mapping facts and reviewed-prose regions.</shortdesc>
  <refbody>
    <section id="a-disclaimer" outputclass="cis-disclaimer">
      <title>{_escape(section_titles["a-disclaimer"])}</title>
      <p>BPM is an independent implementation and is not authorized, sponsored, endorsed, certified, or approved by CIS. BPM documentation is not a substitute for the official CIS benchmark. BPM output does not prove CIS compliance.</p>
      <p>The official CIS PDF and source expression are not copied, translated, indexed, or packaged. BPM documents its own mappings, generated layers, merge behavior, manual-review states, and limitations in original prose.</p>
    </section>
    <section id="a-benchmark">
      <title>{_escape(section_titles["a-benchmark"])}</title>
{_benchmark_dita(inventory)}
    </section>
    <section id="a-recommendation-identity">
      <title>{_escape(section_titles["a-recommendation-identity"])}</title>
      <p>Recommendation ID <codeph>{_escape(recommendation_id)}</codeph>; level <codeph>{_escape(recommendation["level"])}</codeph>; scored <codeph>{str(recommendation["scored"]).lower()}</codeph>; source section <codeph>{_escape(recommendation["source_section"])}</codeph>; source title SHA-256 <codeph>{_escape(recommendation["source_title_sha256"])}</codeph>; publication disposition <codeph>{_escape(recommendation["publication_disposition"])}</codeph>; provenance ID <codeph>{_escape(recommendation["provenance_id"])}</codeph>.</p>
    </section>
    <section id="a-bpm-authored-summary">
      <title>{_escape(section_titles["a-bpm-authored-summary"])}</title>
      <p>Category <codeph>{_escape(recommendation["category"])}</codeph>; assessment <codeph>{_escape(recommendation["assessment"])}</codeph>; confidence <codeph>{_escape(recommendation["confidence"])}</codeph>; mapping status <codeph>{_escape(recommendation["mapping_status"])}</codeph>; mapping reason available <codeph>{str(recommendation["has_mapping_reason"]).lower()}</codeph>; review note available <codeph>{str(recommendation["has_review_note"]).lower()}</codeph>; non-publishable reason <codeph>{_escape(recommendation["non_publishable_reason"] or "none")}</codeph>.</p>
{_region("bpm-authored-summary", recommendation_id, regions)}
    </section>
    <section id="a-bpm-mapping">
      <title>{_escape(section_titles["a-bpm-mapping"])}</title>
{_targets_dita(recommendation, inventory)}
    </section>
    <section id="a-automation-state">
      <title>{_escape(section_titles["a-automation-state"])}</title>
{_manual_state_dita(recommendation, inventory)}
    </section>
    <section id="a-conflicts">
      <title>{_escape(section_titles["a-conflicts"])}</title>
{_region("conflicts", recommendation_id, regions)}
{_region("limitations", recommendation_id, regions)}
    </section>
    <section id="a-verification">
      <title>{_escape(section_titles["a-verification"])}</title>
{_region("verification", recommendation_id, regions)}
    </section>
    <section id="a-provenance" outputclass="cis-disclaimer">
      <title>{_escape(section_titles["a-provenance"])}</title>
{_provenance_dita(recommendation, inventory)}
    </section>
  </refbody>
  <related-links>
    <link keyref="topic.cis-concept-orientation"/>
    <link keyref="topic.cis-concept-levels-channels-layers"/>
    <link keyref="topic.cis-task-select-cis-baseline"/>
    <link keyref="topic.ug-task-resolve-cis-manual-review"/>
  </related-links>
</reference>
"""


def _map_content(recommendations: list[dict[str, Any]]) -> str:
    topicrefs = "\n".join(
        f'  <topicref keys="topic.{_escape(recommendation["doc_id"])}" '
        f'href="{RECOMMENDATIONS_DIRNAME}/{_escape(recommendation["doc_id"])}.dita"/>'
        for recommendation in recommendations
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="map-generated-cis-recommendation-skeletons">
  <title>Generated CIS recommendation skeletons</title>
{topicrefs}
</map>
"""


def _index_content(
    recommendations: list[dict[str, Any]],
    inventory: dict[str, Any],
    inventory_path: Path,
    model_path: Path,
    output_root: Path,
) -> str:
    planned = _planned(recommendations)
    provenance_only = _provenance_only(recommendations)
    payload = {
        "schema_version": 1,
        "backlog_item": "BPM090-M6-03",
        "mapping_backlog_item": "BPM090-M6-04",
        "refresh_runbook_backlog_item": "BPM090-M6-08",
        "refresh_runbook": CIS_DRIFT_GATE_RUNBOOK,
        "provenance_review_backlog_item": "BPM090-M6-09",
        "provenance_review": _display_path(output_root / PROVENANCE_REVIEW_FILENAME),
        "target_bpm_version": "0.9.0",
        "generated_by": GENERATOR_NAME,
        "source_inventory": str(inventory_path.relative_to(REPOSITORY_ROOT)),
        "source_inventory_sha256": _sha256(inventory_path),
        "source_model": str(model_path.relative_to(REPOSITORY_ROOT)),
        "source_model_sha256": _sha256(model_path),
        "map": _display_path(output_root / MAP_FILENAME),
        "recommendation_count": len(recommendations),
        "topic_count": len(planned),
        "provenance_only_count": len(provenance_only),
        "mapping_table_count": len(planned),
        "mapping_row_count": sum(len(recommendation["targets"]) for recommendation in planned),
        "mapping_example_count": sum(len(recommendation["targets"]) for recommendation in planned),
        "source_boundary": {
            "publishable_source_family_id": "bpm-cis-mapping-implementation",
            "restricted_source_family_id": "cis-benchmark-pdf",
            "source_expression_copied": False,
            "source_expression_indexed": False,
            "certification_claimed": False,
        },
        "topics": [
            {
                "recommendation_id": recommendation["recommendation_id"],
                "doc_id": recommendation["doc_id"],
                "path": _display_path(
                    output_root / RECOMMENDATIONS_DIRNAME / f"{recommendation['doc_id']}.dita"
                ),
                "level": recommendation["level"],
                "mapping_status": recommendation["mapping_status"],
                "target_count": len(recommendation["targets"]),
                "target_doc_ids": [target["target_doc_id"] for target in recommendation["targets"]],
                "mapping_table_rows": _mapping_rows(recommendation, inventory),
                "generated_layers": recommendation["generated_layers"],
                "source_title_sha256": recommendation["source_title_sha256"],
                "provenance_id": recommendation["provenance_id"],
            }
            for recommendation in planned
        ],
        "provenance_only_records": [
            {
                "recommendation_id": recommendation["recommendation_id"],
                "doc_id": recommendation["doc_id"],
                "publication_disposition": recommendation["publication_disposition"],
                "mapping_status": recommendation["mapping_status"],
                "non_publishable_reason": recommendation["non_publishable_reason"],
                "source_title_sha256": recommendation["source_title_sha256"],
                "provenance_id": recommendation["provenance_id"],
                "topic_path": None,
            }
            for recommendation in provenance_only
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _review_record(
    recommendation: dict[str, Any],
    inventory: dict[str, Any],
    model: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    manual_review_paths = _manual_review_path_ids(inventory)
    matched_manual_review_paths = [
        _target_path_id(target)
        for target in recommendation["targets"]
        if _target_path_id(target) in manual_review_paths
    ]
    planned = recommendation["publication_disposition"] == "planned-dita-topic"
    topic_path = (
        _display_path(output_root / RECOMMENDATIONS_DIRNAME / f"{recommendation['doc_id']}.dita")
        if planned
        else None
    )
    return {
        "recommendation_id": recommendation["recommendation_id"],
        "doc_id": recommendation["doc_id"],
        "topic_path": topic_path,
        "publication_disposition": recommendation["publication_disposition"],
        "non_publishable_reason": recommendation["non_publishable_reason"],
        "level": recommendation["level"],
        "expected_topic_props": _props(recommendation, model) if planned else None,
        "assessment": recommendation["assessment"],
        "mapping_status": recommendation["mapping_status"],
        "source_section": recommendation["source_section"],
        "source_title_sha256": recommendation["source_title_sha256"],
        "provenance_id": recommendation["provenance_id"],
        "target_count": len(recommendation["targets"]),
        "target_doc_ids": [target["target_doc_id"] for target in recommendation["targets"]],
        "target_paths": [_target_path_id(target) for target in recommendation["targets"]],
        "generated_layers": recommendation["generated_layers"],
        "manual_review_paths": matched_manual_review_paths,
        "source_family_id": "bpm-cis-mapping-implementation",
        "restricted_source_family_id": "cis-benchmark-pdf",
        "reuse_mode": "generated-facts-and-bpm-authored-prose",
        "rights_approval_id_when_required": None,
        "source_expression_published": False,
        "source_expression_indexed": False,
        "source_title_published": False,
        "benchmark_prose_published": False,
        "topic_section_ids": (
            [section["id"] for section in model["required_sections"]] if planned else []
        ),
        "accuracy_basis": [
            "docs/architecture/cis-documentation-inventory-0.9.0.json",
            "app/compliance/firefox/cis/generated/*.json",
            "documentation/config/cis-settings-topic-model-0.9.0.json",
        ],
    }


def _provenance_review_content(
    recommendations: list[dict[str, Any]],
    inventory: dict[str, Any],
    model: dict[str, Any],
    inventory_path: Path,
    model_path: Path,
    output_root: Path,
) -> str:
    benchmark = inventory["benchmark"]
    planned = _planned(recommendations)
    provenance_only = _provenance_only(recommendations)
    payload = {
        "schema_version": 1,
        "backlog_item": "BPM090-M6-09",
        "target_bpm_version": "0.9.0",
        "generated_by": GENERATOR_NAME,
        "source_inventory": str(inventory_path.relative_to(REPOSITORY_ROOT)),
        "source_inventory_sha256": _sha256(inventory_path),
        "source_model": str(model_path.relative_to(REPOSITORY_ROOT)),
        "source_model_sha256": _sha256(model_path),
        "source_matrix": model["source_matrix"],
        "source_family_ids": {
            "publishable_mapping": "bpm-cis-mapping-implementation",
            "restricted_benchmark": "cis-benchmark-pdf",
            "trademark_policy": "cis-trademarks-and-certification-marks",
        },
        "benchmark": {
            "id": benchmark["id"],
            "upstream_name": benchmark["upstream_name"],
            "upstream_version": benchmark["upstream_version"],
            "exact_release_date": benchmark["exact_release_date"],
            "tested_by_cis_against": benchmark["tested_by_cis_against"],
            "source_license": benchmark["source_license"],
            "source_license_url": benchmark["source_license_url"],
            "source_terms_url": benchmark["source_terms_url"],
            "official_source_required": benchmark["official_source_required"],
            "source_content_redistribution_reviewed": benchmark[
                "source_content_redistribution_reviewed"
            ],
        },
        "source_boundary": {
            "publishable_source_family_id": "bpm-cis-mapping-implementation",
            "restricted_source_family_id": "cis-benchmark-pdf",
            "allowed_publication_policy": "approval-required for benchmark expression",
            "source_expression_copied": False,
            "source_expression_indexed": False,
            "official_pdf_committed": False,
            "official_pdf_packaged": False,
            "source_titles_published": False,
            "benchmark_prose_published": False,
            "rights_approval_id_when_required": None,
            "certification_claimed": False,
            "conformance_claimed": False,
            "compliance_guaranteed": False,
        },
        "forbidden_claims": [
            *model["disclaimer_contract"]["forbidden_claims"],
            "copied-cis-benchmark-prose",
            "published-cis-recommendation-title",
            "published-cis-audit-or-remediation-prose",
            "missing-source-title-hash",
            "missing-provenance-id",
            "missing-manual-review-boundary",
        ],
        "accuracy_checks": {
            "benchmark_version_metadata_complete": True,
            "level_metadata_complete": True,
            "mapping_metadata_complete": True,
            "manual_review_metadata_complete": True,
            "source_metadata_complete": True,
            "provenance_only_records_closed": True,
            "layer_checked_examples_required": True,
            "generated_topics_require_source_boundary": True,
            "authored_topics_require_non_certification_boundary": True,
        },
        "summary": {
            "recommendation_count": len(recommendations),
            "planned_topic_count": len(planned),
            "provenance_only_count": len(provenance_only),
            "target_count": sum(
                len(recommendation["targets"]) for recommendation in recommendations
            ),
            "manual_review_path_count": len(inventory["manual_review_paths"]),
            "level_counts": inventory["summary"]["level_counts"],
            "mapping_status_counts": inventory["summary"]["mapping_status_counts"],
            "publication_disposition_counts": inventory["summary"][
                "publication_disposition_counts"
            ],
            "merge_decision_types": inventory["merge_contract"]["decision_types"],
            "persisted_exception_model": inventory["exception_contract"][
                "persisted_exception_model"
            ],
        },
        "manual_review_paths": inventory["manual_review_paths"],
        "records": [
            _review_record(recommendation, inventory, model, output_root)
            for recommendation in recommendations
        ],
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
    recommendations = sorted(inventory["recommendations"], key=_recommendation_sort_key)
    planned = _planned(recommendations)
    files: list[GeneratedFile] = []
    for recommendation in planned:
        path = output_root / RECOMMENDATIONS_DIRNAME / f"{recommendation['doc_id']}.dita"
        existing_text = path.read_text(encoding="utf-8") if path.is_file() else None
        files.append(
            GeneratedFile(path, _topic_content(recommendation, inventory, model, existing_text))
        )
    files.append(GeneratedFile(output_root / MAP_FILENAME, _map_content(planned)))
    files.append(
        GeneratedFile(
            output_root / INDEX_FILENAME,
            _index_content(recommendations, inventory, inventory_path, model_path, output_root),
        )
    )
    files.append(
        GeneratedFile(
            output_root / PROVENANCE_REVIEW_FILENAME,
            _provenance_review_content(
                recommendations,
                inventory,
                model,
                inventory_path,
                model_path,
                output_root,
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
    recommendations_root = output_root / RECOMMENDATIONS_DIRNAME
    recommendations_root.mkdir(parents=True, exist_ok=True)
    for stale in (
        sorted(output_root.glob("*.ditamap"))
        + sorted(output_root.glob("*.json"))
        + sorted(recommendations_root.glob("*.dita"))
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
        f"Generated {len(written)} CIS recommendation skeleton artifact(s) in {args.output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
