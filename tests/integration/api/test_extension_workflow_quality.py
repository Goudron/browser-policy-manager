"""BPM096-M7-08 API matrix for extension editing without a live AMO dependency."""

from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi import status

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from tests.support import make_test_client

_MANUAL_GUID = "manual-matrix@example.test"
_AMO_ASSISTED_GUID = "amo-assisted-matrix@example.test"


def _common_extension_document() -> dict[str, object]:
    """Return only fields supported by every active Firefox artifact."""

    return {
        "ExtensionSettings": {
            _MANUAL_GUID: {"installation_mode": "allowed"},
        },
        "ExtensionUpdate": True,
        "Extensions": {"Locked": [_MANUAL_GUID]},
        "InstallAddonsPermission": {"Default": False},
    }


@pytest.mark.parametrize("schema_version", SUPPORTED_SCHEMA_CHANNELS)
def test_extension_rule_save_reopen_and_export_round_trip_in_every_active_schema(
    schema_version: str,
) -> None:
    """Manual and AMO-assisted metadata must not alter a valid policy round trip."""

    original_flags = _common_extension_document()
    updated_flags = deepcopy(original_flags)
    updated_flags["ExtensionSettings"] = {
        **original_flags["ExtensionSettings"],
        _AMO_ASSISTED_GUID: {"installation_mode": "blocked"},
    }

    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M7 extension matrix {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "flags": original_flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        created = created_response.json()

        saved_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "flags": updated_flags,
                "extension_provenance": {
                    "contract_id": "bpm096-profile-extension-provenance",
                    "contract_version": 1,
                    "paths": {
                        # An unchanged manual value cannot be relabelled by a
                        # client claim, while a real newly added AMO selection
                        # retains the local interaction fact.
                        f"/ExtensionSettings/{_MANUAL_GUID}/installation_mode": (
                            "amo-assisted-manual"
                        ),
                        f"/ExtensionSettings/{_AMO_ASSISTED_GUID}/installation_mode": (
                            "amo-assisted-manual"
                        ),
                    },
                },
            },
        )
        assert saved_response.status_code == status.HTTP_200_OK, saved_response.text
        saved = saved_response.json()
        reopened_response = client.get(f"/api/profiles/{created['id']}")
        exported_response = client.get(
            f"/api/export/profiles/{created['id']}/firefox/policies.json"
        )

    assert saved["schema_version"] == schema_version
    assert saved["flags"] == updated_flags
    assert (
        saved["extension_provenance"]["paths"][
            f"/ExtensionSettings/{_MANUAL_GUID}/installation_mode"
        ]
        == "manual"
    )
    assert (
        saved["extension_provenance"]["paths"][
            f"/ExtensionSettings/{_AMO_ASSISTED_GUID}/installation_mode"
        ]
        == "amo-assisted-manual"
    )
    assert reopened_response.status_code == status.HTTP_200_OK, reopened_response.text
    assert reopened_response.json()["flags"] == updated_flags
    assert reopened_response.json()["extension_provenance"] == saved["extension_provenance"]
    assert exported_response.status_code == status.HTTP_200_OK, exported_response.text
    assert exported_response.json() == {"policies": updated_flags}
    assert "extension_provenance" not in exported_response.text
