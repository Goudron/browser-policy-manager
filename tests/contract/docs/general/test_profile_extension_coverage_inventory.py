"""Executable scope guard for BPM096-M7-01's extension coverage inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.firefox_starter_catalog import STARTER_PRESETS
from app.core.schema_channels import SCHEMA_FILENAMES, SUPPORTED_SCHEMA_CHANNELS
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
INVENTORY_PATH = REPO_ROOT / "docs/architecture/profile-extension-coverage-inventory-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-profile-extension-coverage-inventory-v1 -->"
SYNC_TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_sync.html"


def _inventory() -> dict[str, Any]:
    source = INVENTORY_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "extension coverage fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _schema(channel: str) -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "app/schemas/policies" / SCHEMA_FILENAMES[channel]).read_text(encoding="utf-8")
    )


def test_inventory_is_indexed_and_records_the_m7_01_boundary() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-extension-coverage-inventory-0.9.6.md", status="active"
        )
        == INVENTORY_PATH
    )
    inventory = _inventory()
    assert inventory["inventory_id"] == "bpm096-profile-extension-coverage"
    assert inventory["inventory_version"] == 1
    assert inventory["backlog_item"] == "BPM096-M7-01"
    assert inventory["guided_owner"] == {"step": 6, "id": "extensions"}
    assert inventory["supported_schema_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M7-01 — Extension policy coverage inventoried" in backlog
    assert INVENTORY_PATH.name in backlog


def test_every_supported_extension_policy_path_has_one_recorded_disposition() -> None:
    inventory = _inventory()
    coverage = inventory["policy_coverage"]
    expected_policy_ids = {
        "ExtensionSettings",
        "Extensions",
        "ExtensionUpdate",
        "InstallAddonsPermission",
        "3rdparty",
    }
    assert set(coverage) == expected_policy_ids
    assert {
        policy_id
        for channel in SUPPORTED_SCHEMA_CHANNELS
        for policy_id in _schema(channel)["properties"]
        if policy_id in expected_policy_ids
    } == expected_policy_ids

    for policy_id, entry in coverage.items():
        assert entry["paths"], policy_id
        assert entry["disposition"] in {"extensions-step-control", "all-settings-only"}
        if entry["disposition"] == "extensions-step-control":
            assert entry["delivery"] == "BPM096-M7-05"
        else:
            assert entry["reason"] == (
                "opaque add-on-defined Extensions.<guid>.adminSettings payload; "
                "Firefox supplies no stable field contract"
            )

    assert coverage["3rdparty"]["disposition"] == "all-settings-only"
    assert inventory["raw_fallback"]["typed_extension_policy_values"]["owner"] == "extensions"
    assert inventory["raw_fallback"]["typed_extension_policy_values"]["step"] == 6
    assert inventory["raw_fallback"]["thirdparty_admin_settings"]["owner"] == "all-settings-only"


def test_schema_difference_preset_and_cis_inputs_are_explicit() -> None:
    inventory = _inventory()
    baseline = set(inventory["schema_fields"]["baseline"])
    release_extra = set(inventory["schema_fields"]["153_extra"])
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        fields = set(
            _schema(channel)["properties"]["ExtensionSettings"]["additionalProperties"][
                "properties"
            ]
        )
        if channel in {"release-153", "esr-153.0"}:
            assert fields == baseline | release_extra
        else:
            assert fields == baseline

    expected_preset_policy_ids = {
        "blank": set(),
        "keep_current": set(),
        "basic_corporate": {"ExtensionSettings"},
        "classroom_kiosk": {"ExtensionSettings", "InstallAddonsPermission"},
        "soc_hard": {"ExtensionSettings", "InstallAddonsPermission"},
    }
    assert set(inventory["starter_presets"]) == set(expected_preset_policy_ids)
    for preset_id, expected_ids in expected_preset_policy_ids.items():
        values = STARTER_PRESETS[preset_id]["policy_values"]
        actual_ids = {
            policy_id
            for group in values.values()
            for policy_id in group
            if policy_id in {"ExtensionSettings", "InstallAddonsPermission"}
        }
        assert actual_ids == expected_ids

    assert inventory["cis"]["all_layers_all_channels"] == [
        "ExtensionUpdate=true",
        "InstallAddonsPermission.Default=false",
    ]
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        for layer in ("cis_l1", "cis_l2"):
            values = json.loads(
                (
                    REPO_ROOT / "app/compliance/firefox/cis/generated" / f"{layer}.{channel}.json"
                ).read_text(encoding="utf-8")
            )["policies"]
            assert values["ExtensionUpdate"] is True
            assert values["InstallAddonsPermission"]["Default"] is False


def test_legacy_controls_and_curated_guid_assumptions_have_removal_dispositions() -> None:
    inventory = _inventory()
    source = SYNC_TEMPLATE.read_text(encoding="utf-8")
    dispositions = inventory["legacy_control_dispositions"]
    expected_controls = {
        "wizard-extension-default-mode",
        "wizard-extension-install",
        "wizard-extension-locked",
        "wizard-extension-uninstall",
        "policy:InstallAddonsPermission",
        "policy:ExtensionSettings",
    }
    assert set(dispositions) == expected_controls
    assert dispositions["wizard-extension-default-mode"] == {
        "previous_host_step": 5,
        "disposition": "removed-in-M7-05",
    }
    for control, entry in dispositions.items():
        assert control not in source
        if control == "wizard-extension-default-mode":
            continue
        assert entry == {
            "previous_host_step": 5,
            "current_host_step": 6,
            "disposition": "rehome-once-to-step-6-in-M7-05",
        }

    curated = inventory["obsolete_curated_assumptions"]
    assert set(curated) == {
        "uBlock0@raymondhill.net",
        "adguardadblocker@adguard.com",
        "https-everywhere@eff.org",
    }
    for extension_id, disposition in curated.items():
        assert disposition == "removed-static-card-in-M7-05"
        assert extension_id not in source
