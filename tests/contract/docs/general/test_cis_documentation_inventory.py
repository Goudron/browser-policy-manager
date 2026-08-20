from __future__ import annotations

import json

from app.compliance.firefox.cis.generation import build_all_cis_layers
from app.compliance.firefox.cis.validation import BASE_DIR, load_yaml_file
from tests.docs_index import doc_path_from_index
from tools.build_cis_documentation_inventory import build_inventory


def _maintained_inventory() -> dict[str, object]:
    path = doc_path_from_index(
        "architecture/cis-documentation-inventory-0.9.0.json",
        status="active",
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_cis_documentation_inventory_is_current_and_complete():
    inventory = _maintained_inventory()
    source = load_yaml_file(BASE_DIR / "firefox_esr_gpo_1_0_0.yaml")

    assert inventory == build_inventory()
    assert inventory["schema_version"] == 1

    recommendations = inventory["recommendations"]
    assert isinstance(recommendations, list)
    assert len(recommendations) == 55
    assert {entry["recommendation_id"] for entry in recommendations} == {
        entry["id"] for entry in source["recommendations"]
    }
    assert len({entry["provenance_id"] for entry in recommendations}) == 55


def test_cis_documentation_inventory_closes_publication_dispositions():
    recommendations = _maintained_inventory()["recommendations"]
    planned = [
        entry
        for entry in recommendations
        if entry["publication_disposition"] == "planned-dita-topic"
    ]
    provenance_only = [
        entry
        for entry in recommendations
        if entry["publication_disposition"] == "provenance-only-non-publishable"
    ]

    assert len(planned) == 53
    assert len({entry["doc_id"] for entry in planned}) == 53
    assert all(entry["doc_id"].startswith("cis-rec-") for entry in planned)
    assert all(entry["non_publishable_reason"] is None for entry in planned)
    assert {(entry["recommendation_id"], entry["mapping_status"]) for entry in provenance_only} == {
        ("1.1.5.3", "needs_research"),
        ("1.1.12.1", "deprecated_or_removed"),
    }
    assert all(entry["doc_id"] is None for entry in provenance_only)
    assert all(entry["non_publishable_reason"] for entry in provenance_only)


def test_cis_documentation_inventory_targets_firefox_documentation_ids():
    inventory = _maintained_inventory()
    targets = [target for entry in inventory["recommendations"] for target in entry["targets"]]

    assert len(targets) == 53
    assert sum(target["kind"] == "policy" for target in targets) == 43
    assert sum(target["kind"] == "preference" for target in targets) == 10
    assert all(
        target["target_doc_id"].startswith("fx-policy-")
        for target in targets
        if target["kind"] == "policy"
    )
    assert all(
        target["target_doc_id"].startswith("fx-pref-")
        for target in targets
        if target["kind"] == "preference"
    )
    assert all(
        target["schema_channels"]
        == {
            "esr-115.39": "valid",
            "esr-140.13": "valid",
            "esr-153.0": "valid",
            "release-153": "valid",
        }
        for target in targets
    )


def test_cis_documentation_inventory_covers_layers_presets_and_merge_contract():
    inventory = _maintained_inventory()
    layers = inventory["generated_layers"]
    expected_layers = build_all_cis_layers()

    assert len(layers) == 8
    assert {(entry["level"], entry["schema_channel"]) for entry in layers} == {
        (layer.level, layer.schema_channel) for layer in expected_layers
    }
    assert sorted(entry["recommendation_count"] for entry in layers) == [
        49,
        49,
        49,
        49,
        53,
        53,
        53,
        53,
    ]
    assert sorted(entry["policy_top_level_count"] for entry in layers) == [
        30,
        30,
        30,
        30,
        33,
        33,
        33,
        33,
    ]
    assert {entry["starter_id"] for entry in inventory["starter_presets"]} == {
        "blank",
        "keep_current",
        "basic_corporate",
        "classroom_kiosk",
        "soc_hard",
    }
    assert all(len(entry["variants"]) == 12 for entry in inventory["starter_presets"])
    assert len(inventory["manual_review_paths"]) == 9
    assert len(inventory["merge_contract"]["decision_types"]) == 6
    assert inventory["exception_contract"]["persisted_exception_model"] is False


def test_cis_documentation_inventory_summary_is_active():
    summary = doc_path_from_index(
        "architecture/cis-documentation-inventory-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")
    normalized_summary = " ".join(summary.split())

    for required in (
        "55 scored, automated recommendation records",
        "53 planned DITA topics",
        "2 provenance-only non-publishable records",
        "Nine explicit paths require manual review",
        "no separate persisted CIS exception or waiver model",
        "does not read, hash, copy, or republish its contents",
        "--check",
    ):
        assert required in normalized_summary
