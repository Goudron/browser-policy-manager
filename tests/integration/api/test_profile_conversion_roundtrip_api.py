from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup
from fastapi import status

from app.core.schema_channels import build_schema_channels_catalog
from tests.support import make_test_client


def _apply_payload(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "profile-conversion-apply-request",
        "contract_version": 1,
        "profile_id": preview["profile"]["id"],
        "expected_revision": preview["profile"]["revision"],
        "source": {
            "line_id": preview["source"]["artifact"]["line_id"],
            "artifact_id": preview["source"]["artifact"]["artifact_id"],
        },
        "target": {
            "line_id": preview["target"]["artifact"]["line_id"],
            "artifact_id": preview["target"]["artifact"]["artifact_id"],
        },
        "target_artifact_id": preview["target"]["artifact"]["artifact_id"],
        "plan_digest": preview["plan_digest"],
        "source_document_digest": preview["source"]["document_digest"],
        "source_compliance_digest": preview["source"]["compliance_digest"],
        "source_metadata_digest": preview["profile"]["metadata_digest"],
        "source_validation_schema_sha256": preview["source"]["artifact"][
            "validation_schema_sha256"
        ],
        "target_validation_schema_sha256": preview["target"]["artifact"][
            "validation_schema_sha256"
        ],
        "recipe_registry_version": preview["recipe_registry"]["registry_version"],
        "recipe_registry_digest": preview["recipe_registry"]["registry_digest"],
    }


def _embedded_json(response, element_id: str) -> dict[str, Any]:
    element = BeautifulSoup(response.text, "html.parser").find(id=element_id)
    assert element is not None
    return json.loads(element.get_text())


def _apply(client, profile_id: int, target: str) -> tuple[dict[str, Any], dict[str, Any]]:
    preview_response = client.post(
        f"/api/profiles/{profile_id}/conversion-preview",
        json={"target_artifact_id": target},
    )
    assert preview_response.status_code == status.HTTP_200_OK, preview_response.text
    preview = preview_response.json()
    assert preview["compatibility"]["applicable"] is True
    assert preview["target_validation"]["status"] == "valid"
    apply_response = client.post(
        f"/api/profiles/{profile_id}/conversion-apply",
        json=_apply_payload(preview),
    )
    assert apply_response.status_code == status.HTTP_200_OK, apply_response.text
    return preview, apply_response.json()


def _shell_policy_ids(shell_catalog: dict[str, Any], channel: str) -> set[str]:
    return {
        item["id"]
        for step in shell_catalog["channels"][channel]["steps"].values()
        for bucket in ("recommended", "additional", "raw_fallback")
        for item in step[bucket]
    }


def test_conversion_apply_roundtrip_retains_target_state_across_profile_surfaces_and_exchange():
    source_flags = {
        "DisableTelemetry": True,
        "EnableTrackingProtection": {
            "Value": True,
            "EmailTracking": True,
            "Exceptions": ["https://intranet.example", "https://support.example"],
        },
        "FirefoxHome": {"TopSites": False, "SponsoredTopSites": False},
        "ExtensionSettings": {
            "{dynamic-addon-id}": {
                "installation_mode": "allowed",
                "allowed_types": ["extension", "theme"],
                "install_sources": ["https://addons.example/*"],
            }
        },
        "Preferences": {
            "browser.tabs.warnOnClose": {"Value": True, "Status": "locked", "Type": "boolean"},
            "network.trr.mode": {"Value": 3, "Status": "locked", "Type": "number"},
        },
    }
    source_compliance = {
        "framework": "external-review",
        "nested": {"reason": "retain-through-conversion", "atoms": [0, False, "exact"]},
    }

    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": "M4-05 persisted roundtrip",
                "schema_version": "esr-115.39",
                "flags": source_flags,
                "compliance": source_compliance,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        created = created_response.json()

        preview, applied = _apply(client, created["id"], "esr-153.0")
        persisted = client.get(f"/api/profiles/{created['id']}").json()
        assert persisted["schema_version"] == "esr-153.0"
        assert persisted["flags"] == source_flags
        assert applied["compliance"] == preview["compliance"]
        assert persisted["compliance"]["status"] == "invalidated"
        assert persisted["compliance"]["preserved_source"] == source_compliance

        # Every read surface receives the persisted exact target profile and
        # the single catalog is the authority for its label.
        library = client.get("/profiles")
        compare = client.get("/profiles/compare")
        guided = client.get(f"/profiles/{created['id']}/edit")
        settings = client.get(f"/profiles/{created['id']}/settings")
        json_editor = client.get(f"/profiles/{created['id']}/json")
        for response in (library, compare, guided, settings, json_editor):
            assert response.status_code == status.HTTP_200_OK
            catalog = _embedded_json(response, "schema-channels-catalog")
            assert catalog == build_schema_channels_catalog()
            assert catalog["labels"]["esr-153.0"] == "ESR 153.0"

        for response in (guided, settings, json_editor):
            initial = _embedded_json(response, "profiles-initial-profile")
            assert initial["schema_version"] == "esr-153.0"
            assert initial["flags"] == source_flags
            assert initial["compliance"] == persisted["compliance"]
            soup = BeautifulSoup(response.text, "html.parser")
            schema_fact = soup.find(id="profile-schema-fact")
            assert schema_fact is not None
            assert schema_fact["data-saved-profile-schema"] == "esr-153.0"
            assert soup.find(id="profile-type") is None

        # A normal editor PATCH cannot name a new channel and preserves the
        # apply-owned compliance evidence as well as all untouched atoms.
        edited_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "description": "edited after conversion",
                "flags": {**source_flags, "BlockAboutConfig": True},
                "compliance": persisted["compliance"],
                "expected_revision": persisted["revision"],
            },
        )
        assert edited_response.status_code == status.HTTP_200_OK, edited_response.text
        edited = edited_response.json()
        assert edited["schema_version"] == "esr-153.0"
        assert edited["compliance"] == persisted["compliance"]
        assert edited["flags"] == {**source_flags, "BlockAboutConfig": True}

        export_one = client.get(f"/api/export/profiles/{created['id']}/firefox/policies.json")
        export_two = client.get(f"/api/export/profiles/{created['id']}/firefox/policies.json")
        assert export_one.status_code == status.HTTP_200_OK
        assert export_one.content == export_two.content
        exported_document = export_one.json()
        assert exported_document == {"policies": edited["flags"]}
        assert set(exported_document) == {"policies"}
        assert "compliance" not in export_one.text
        assert "invalidated" not in export_one.text

        imported_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": "M4-05 target re-import",
                "schema_version": "esr-153.0",
                "document": exported_document,
                "compliance": edited["compliance"],
            },
        )
        assert imported_response.status_code == status.HTTP_201_CREATED, imported_response.text
        imported = imported_response.json()
        assert imported["schema_version"] == "esr-153.0"
        assert imported["flags"] == edited["flags"]
        assert imported["compliance"] == edited["compliance"]
        reexported = client.get(f"/api/export/profiles/{imported['id']}/firefox/policies.json")
        assert reexported.status_code == status.HTTP_200_OK
        assert reexported.content == export_one.content


def test_target_shell_hides_source_only_controls_and_blocked_source_policy_never_converts():
    with make_test_client() as client:
        compatible = client.post(
            "/api/profiles",
            json={
                "name": "M4-05 source-only shell",
                "schema_version": "esr-153.0",
                "flags": {"DisableTelemetry": True},
            },
        ).json()
        _preview, _applied = _apply(client, compatible["id"], "esr-115.39")
        target = client.get(f"/api/profiles/{compatible['id']}").json()
        assert target["schema_version"] == "esr-115.39"

        guided = client.get(f"/profiles/{compatible['id']}/edit")
        assert guided.status_code == status.HTTP_200_OK
        shell_catalog = _embedded_json(guided, "wizard-schema-shell-catalog")
        assert "AIControls" not in _shell_policy_ids(shell_catalog, "esr-115.39")
        assert "AIControls" in _shell_policy_ids(shell_catalog, "esr-153.0")

        blocked_response = client.post(
            "/api/profiles",
            json={
                "name": "M4-05 blocked source-only",
                "schema_version": "esr-153.0",
                "flags": {
                    "DisableTelemetry": True,
                    "AIControls": {"Default": {"Value": "blocked", "Locked": True}},
                },
            },
        )
        assert blocked_response.status_code == status.HTTP_201_CREATED, blocked_response.text
        blocked = blocked_response.json()
        before = client.get(f"/api/profiles/{blocked['id']}").json()
        preview_response = client.post(
            f"/api/profiles/{blocked['id']}/conversion-preview",
            json={"target_artifact_id": "esr-115.39"},
        )
        assert preview_response.status_code == status.HTTP_200_OK, preview_response.text
        preview = preview_response.json()
        assert preview["compatibility"]["applicable"] is False
        assert any(entry["policy_id"] == "AIControls" for entry in preview["entries"])
        apply_response = client.post(
            f"/api/profiles/{blocked['id']}/conversion-apply",
            json=_apply_payload(preview),
        )
        assert apply_response.status_code == status.HTTP_409_CONFLICT
        assert apply_response.json()["detail"]["code"] == "conversion_plan_blocked"
        after = client.get(f"/api/profiles/{blocked['id']}").json()
        assert after == before
