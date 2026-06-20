from __future__ import annotations

import pytest

from app.core.schema_channels import CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL
from tests.support import (
    build_all_settings_inventory_counts,
    build_corporate_cis_l2_profile_fixture,
)


@pytest.mark.parametrize("schema_version", (CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL))
def test_all_settings_inventory_counts_cover_supported_channel_catalogs(schema_version):
    counts = build_all_settings_inventory_counts(schema_version=schema_version, flags={})

    assert counts.schema_version == schema_version
    assert counts.policy_entries >= 100
    assert counts.preference_entries >= 45
    assert counts.total_entries >= 145
    assert counts.guided_policy_entries >= 25
    assert counts.raw_fallback_policy_entries >= 60
    assert counts.configured_entries == 0
    assert counts.unknown_policy_entries == 0
    assert counts.imported_preference_entries == 0


def test_release_inventory_does_not_drop_below_current_esr_surface():
    esr_counts = build_all_settings_inventory_counts(
        schema_version=CURRENT_ESR_SCHEMA_CHANNEL,
        flags={},
    )
    release_counts = build_all_settings_inventory_counts(
        schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL,
        flags={},
    )

    assert release_counts.policy_entries >= esr_counts.policy_entries
    assert release_counts.total_entries >= esr_counts.total_entries
    assert release_counts.raw_fallback_policy_entries >= esr_counts.raw_fallback_policy_entries


@pytest.mark.parametrize("schema_version", (CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL))
def test_all_settings_inventory_counts_heavy_corporate_cis_profile(schema_version):
    fixture = build_corporate_cis_l2_profile_fixture(schema_version=schema_version)
    counts = build_all_settings_inventory_counts(
        schema_version=schema_version,
        flags=fixture.flags,
    )

    assert counts.configured_policy_entries == fixture.configured_policy_count
    assert counts.configured_preference_entries == fixture.configured_preference_count
    assert counts.configured_entries >= 50
    assert counts.imported_preference_entries == 0
    assert counts.unknown_policy_entries == 0


def test_all_settings_inventory_counts_track_imported_or_unknown_settings():
    counts = build_all_settings_inventory_counts(
        schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL,
        flags={
            "DisableTelemetry": True,
            "CustomEnterprisePolicy": {"enabled": True},
            "Preferences": {
                "browser.newtabpage.enabled": {
                    "Value": True,
                    "Status": "default",
                    "Type": "boolean",
                },
                "company.managed.preference": {
                    "Value": "strict",
                    "Status": "locked",
                    "Type": "string",
                },
            },
        },
    )

    assert counts.configured_policy_entries == 2
    assert counts.configured_preference_entries == 2
    assert counts.unknown_policy_entries == 1
    assert counts.imported_preference_entries == 1
    assert counts.configured_entries == 4
    assert counts.as_dict()["schema_version"] == CURRENT_RELEASE_SCHEMA_CHANNEL
