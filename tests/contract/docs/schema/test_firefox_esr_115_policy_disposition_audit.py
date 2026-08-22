from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from app.compliance.firefox.cis.generation import build_cis_layer
from app.compliance.firefox.cis.validation import BASE_DIR as CIS_BASE_DIR
from app.compliance.firefox.cis.validation import load_yaml_file
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from app.web.firefox_wizard_shell.catalog import CERTIFICATE_TRUST_GUIDED_POLICY_IDS

REPO_ROOT = Path(__file__).resolve().parents[4]
AUDIT_PATH = REPO_ROOT / "docs/architecture/firefox-esr-115-policy-disposition-audit-0.9.5.json"
SCHEMA_PATH = (
    REPO_ROOT / "docs/architecture/schemas/firefox-esr-115-policy-disposition-audit-v1.schema.json"
)
DOCS_INDEX_PATH = REPO_ROOT / "docs/docs-index.md"
SCHEMAS_DIR = REPO_ROOT / "app/schemas/policies"
SOURCE = "esr-115.39"
TARGETS = ("esr-140.13", "esr-153.0", "release-153")


def _audit() -> dict[str, Any]:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def _shape(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    shaped: dict[str, Any] = {}
    for key in (
        "type",
        "enum",
        "minimum",
        "maximum",
        "pattern",
        "additionalProperties",
        "required",
        "oneOf",
    ):
        if key in value:
            shaped[key] = value[key]
    if isinstance(value.get("properties"), dict):
        shaped["properties"] = {key: _shape(child) for key, child in value["properties"].items()}
    if isinstance(value.get("items"), dict):
        shaped["items"] = _shape(value["items"])
    if isinstance(value.get("additionalProperties"), dict):
        shaped["additionalProperties"] = _shape(value["additionalProperties"])
    if isinstance(value.get("oneOf"), list):
        shaped["oneOf"] = [_shape(child) for child in value["oneOf"]]
    return shaped


def _changed_paths(source: Any, target: Any, path: str = "") -> set[str]:
    if source == target:
        return set()
    if isinstance(source, dict) and isinstance(target, dict):
        return {
            changed
            for key in source.keys() | target.keys()
            for changed in _changed_paths(
                source.get(key, "__missing__"), target.get(key, "__missing__"), f"{path}/{key}"
            )
        }
    return {path}


def _expected(target: str) -> tuple[set[str], set[str]]:
    source = json.loads((SCHEMAS_DIR / f"firefox-{SOURCE}.json").read_text())["properties"]
    target_policies = json.loads((SCHEMAS_DIR / f"firefox-{target}.json").read_text())["properties"]
    added = {f"/{policy}" for policy in target_policies.keys() - source.keys()}
    changed = {
        path
        for policy in source.keys() & target_policies.keys()
        for path in _changed_paths(
            _shape(source[policy]), _shape(target_policies[policy]), f"/{policy}"
        )
    }
    return added, changed


def _recorded(comparison: dict[str, Any]) -> tuple[set[str], set[str], dict[str, str]]:
    added: set[str] = set()
    changed: set[str] = set()
    owners: dict[str, str] = {}
    for group in comparison["groups"]:
        for member in group["members"]:
            identity = f"{group['stable_identity_prefix']}{member}"
            assert identity.count(":") >= 4
            assert member not in owners
            owners[member] = group["owner"]
            (added if group["kind"] == "target_only_policy" else changed).add(member)
    return added, changed, owners


def test_esr_115_disposition_audit_is_schema_valid_and_exhaustive() -> None:
    audit = _audit()
    jsonschema.Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate(audit)
    assert audit["source_channel"] == SOURCE
    assert {item["target_channel"] for item in audit["comparisons"]} == set(TARGETS)
    for channel, digest in audit["artifacts"].items():
        assert (
            hashlib.sha256((SCHEMAS_DIR / f"firefox-{channel}.json").read_bytes()).hexdigest()
            == digest
        )
    for comparison in audit["comparisons"]:
        added, changed = _expected(comparison["target_channel"])
        recorded_added, recorded_changed, owners = _recorded(comparison)
        assert recorded_added == added
        assert recorded_changed == changed
        assert set(owners.values()) <= {"guided", "raw_fallback"}
    index = DOCS_INDEX_PATH.read_text(encoding="utf-8")
    assert "firefox-esr-115-policy-disposition-audit-0.9.5.json" in index
    assert "firefox-esr-115-policy-disposition-audit-0.9.5.md" in index


def test_esr_115_disposition_audit_rejects_an_unclassified_difference() -> None:
    mutated = copy.deepcopy(_audit())
    mutated["comparisons"][0]["groups"][0]["members"].pop()
    expected_added, _ = _expected(mutated["comparisons"][0]["target_channel"])
    recorded_added, _, _ = _recorded(mutated["comparisons"][0])
    assert recorded_added != expected_added


def test_cis_evidence_and_layers_cover_all_four_schema_channels() -> None:
    audit = _audit()
    cis_evidence = audit["cis_evidence"]
    sources = load_yaml_file(CIS_BASE_DIR / "sources.yaml")
    mappings = load_yaml_file(CIS_BASE_DIR / "mappings.yaml")["mappings"]

    assert sources["benchmarks"][0]["tested_by_cis_against"] == (
        "Mozilla Firefox 115.10 ESR on Windows 11 Release 23H2"
    )
    assert set(cis_evidence["available_channels"]) == set(SUPPORTED_SCHEMA_CHANNELS)
    assert cis_evidence["unavailable_channels"] == {}
    assert cis_evidence["mapping_target_count_per_channel"] == 53
    assert cis_evidence["validated_levels"] == [1, 2]

    targets = [target for mapping in mappings for target in mapping.get("targets") or []]
    assert len(targets) == 53
    assert all(
        target["schema_channels"] == {channel: "valid" for channel in target["schema_channels"]}
        and set(target["schema_channels"]) == set(SUPPORTED_SCHEMA_CHANNELS)
        for target in targets
    )
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        assert len(build_cis_layer(1, channel).recommendation_ids) == 49
        assert len(build_cis_layer(2, channel).recommendation_ids) == 53


def test_all_settings_guided_and_raw_are_disjoint_and_complete_for_esr_115() -> None:
    shell = get_wizard_schema_shell_catalog()["channels"][SOURCE]
    buckets = {"recommended": set(), "additional": set(), "raw_fallback": set()}
    for step in shell["steps"].values():
        for bucket, values in buckets.items():
            values.update(item["id"] for item in step[bucket])
    assert not (buckets["recommended"] & buckets["additional"])
    assert not ((buckets["recommended"] | buckets["additional"]) & buckets["raw_fallback"])
    assert len(buckets["recommended"] | buckets["additional"]) == 47
    assert len(buckets["raw_fallback"]) == 45
    assert (
        buckets["recommended"] | buckets["additional"] | buckets["raw_fallback"]
        == set(load_policy_schema(SOURCE).policies) - CERTIFICATE_TRUST_GUIDED_POLICY_IDS
    )
