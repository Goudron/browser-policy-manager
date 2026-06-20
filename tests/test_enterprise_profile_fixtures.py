from __future__ import annotations

import pytest

from app.core.policy_validation import validate_profile_payload_with_schema
from app.core.schema_channels import CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL
from app.main import app
from tests.support import (
    build_corporate_cis_l2_profile_fixture,
    build_corporate_cis_l2_profile_fixtures,
    make_test_client,
)


@pytest.mark.parametrize("schema_version", (CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL))
def test_corporate_cis_l2_fixture_builds_heavy_profile_for_supported_channels(schema_version):
    fixture = build_corporate_cis_l2_profile_fixture(schema_version=schema_version)

    assert fixture.schema_version == schema_version
    assert fixture.starter_key == "basic_corporate"
    assert fixture.compliance_layer == "cis_l2"
    assert fixture.payload["schema_version"] == schema_version
    assert fixture.payload["flags"] == fixture.flags
    assert fixture.payload["compliance"] == fixture.compliance
    assert fixture.compliance["framework"] == "cis"
    assert fixture.compliance["layer"] == "cis_l2"
    assert fixture.compliance["summary"] == fixture.summary
    assert fixture.compliance["decisions"] == fixture.decisions
    assert fixture.configured_policy_count >= 35
    assert fixture.configured_preference_count >= 8
    assert fixture.manual_review_count >= 4
    assert fixture.summary["added_from_cis"] > 0
    assert fixture.summary["review_required"] == fixture.manual_review_count
    assert fixture.flags["DisableTelemetry"] is True
    assert fixture.flags["DisableFirefoxAccounts"] is True
    assert fixture.flags["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert fixture.flags["Preferences"]["security.mixed_content.block_active_content"]["Value"] is True
    assert fixture.flags["Preferences"]["media.peerconnection.enabled"]["Value"] is False
    assert any(
        decision["review_required"] and decision["path"] == ["Proxy", "Mode"]
        for decision in fixture.decisions
    )

    validate_profile_payload_with_schema(
        {
            "name": fixture.name,
            "channel": fixture.schema_version,
            "policies": fixture.flags,
        }
    )


def test_corporate_cis_l2_fixture_collection_covers_esr_and_release():
    fixtures = build_corporate_cis_l2_profile_fixtures()

    assert [fixture.schema_version for fixture in fixtures] == [
        CURRENT_ESR_SCHEMA_CHANNEL,
        CURRENT_RELEASE_SCHEMA_CHANNEL,
    ]
    assert all(fixture.compliance["layer"] == "cis_l2" for fixture in fixtures)


def test_corporate_cis_l2_fixture_can_seed_profile_api_for_future_ui_tests():
    fixture = build_corporate_cis_l2_profile_fixture(schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL)
    client = make_test_client(app)

    create_response = client.post("/api/profiles", json=fixture.payload)

    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["name"] == fixture.name
    assert created["schema_version"] == CURRENT_RELEASE_SCHEMA_CHANNEL
    assert created["flags"] == fixture.flags
    assert created["compliance"]["framework"] == "cis"
    assert created["compliance"]["layer"] == "cis_l2"
    assert created["compliance"]["summary"] == fixture.summary
    assert created["compliance"]["decisions"] == fixture.decisions
