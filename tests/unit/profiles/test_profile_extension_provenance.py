"""Focused BPM096-M7-07 proof for durable extension value attribution."""

from __future__ import annotations

from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.core.profile_extension_provenance import (
    converted_extension_provenance,
    duplicate_extension_provenance,
    extension_value_paths,
    imported_extension_provenance,
    is_valid_extension_provenance,
    reconcile_extension_provenance,
)


def test_prepared_starter_and_cis_extension_values_are_attributed_from_server_ledgers() -> None:
    result = compose_profile_initialization(
        schema_id="release-153",
        preset_id="basic_corporate",
        cis_baseline_id="cis_l1",
    )

    assert result.status == "valid"
    assert result.document is not None
    assert result.extension_provenance is not None
    paths = result.extension_provenance["paths"]
    assert paths["/ExtensionSettings/*/installation_mode"] == "preset"
    assert paths["/ExtensionUpdate"] == "cis"
    assert paths["/InstallAddonsPermission/Default"] == "cis"
    assert set(paths) == set(extension_value_paths(result.document))
    assert is_valid_extension_provenance(result.extension_provenance)


def test_duplicate_preserves_same_schema_sources_and_marks_only_supported_cross_schema_values_converted() -> (
    None
):
    source = {
        "ExtensionSettings": {
            "addon@example.test": {"installation_mode": "allowed"},
        },
        "Extensions": {"Locked": ["addon@example.test"]},
    }
    source_provenance = imported_extension_provenance(source)
    same_schema = duplicate_extension_provenance(
        source,
        source_provenance,
        source,
        cross_schema=False,
    )
    converted = duplicate_extension_provenance(
        source,
        source_provenance,
        source,
        cross_schema=True,
    )

    assert set(same_schema["paths"].values()) == {"imported"}
    assert set(converted["paths"].values()) == {"converted"}
    assert converted == converted_extension_provenance(source)


def test_update_keeps_unchanged_starter_value_and_accepts_amo_marker_only_for_changed_value() -> (
    None
):
    before = {
        "ExtensionSettings": {
            "addon@example.test": {
                "installation_mode": "blocked",
                "updates_disabled": True,
            },
        },
    }
    previous = {
        "contract_id": "bpm096-profile-extension-provenance",
        "contract_version": 1,
        "paths": {
            "/ExtensionSettings/addon@example.test/installation_mode": "preset",
            "/ExtensionSettings/addon@example.test/updates_disabled": "cis",
        },
    }
    after = {
        "ExtensionSettings": {
            "addon@example.test": {
                "installation_mode": "allowed",
                "updates_disabled": True,
            },
        },
    }
    submitted = {
        "contract_id": "bpm096-profile-extension-provenance",
        "contract_version": 1,
        "paths": {
            "/ExtensionSettings/addon@example.test/installation_mode": "amo-assisted-manual",
            "/ExtensionSettings/addon@example.test/updates_disabled": "amo-assisted-manual",
        },
    }

    result = reconcile_extension_provenance(before, previous, after, submitted)

    assert result["paths"] == {
        "/ExtensionSettings/addon@example.test/installation_mode": "amo-assisted-manual",
        "/ExtensionSettings/addon@example.test/updates_disabled": "cis",
    }


def test_update_keeps_raw_attribution_only_for_a_real_raw_editor_change() -> None:
    before = {"ExtensionUpdate": {"Enabled": True}}
    after = {"ExtensionUpdate": {"Enabled": False}}

    result = reconcile_extension_provenance(
        before,
        imported_extension_provenance(before),
        after,
        {
            "contract_id": "bpm096-profile-extension-provenance",
            "contract_version": 1,
            "paths": {"/ExtensionUpdate/Enabled": "raw"},
        },
    )

    assert result["paths"] == {"/ExtensionUpdate/Enabled": "raw"}
