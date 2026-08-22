"""BPM096-M8-06 matrix for Guided URLs, sites, and navigation."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from bs4 import BeautifulSoup
from fastapi import status

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from tests.support import make_test_client

_URL_OWNER_POLICY_IDS = frozenset(
    {
        "Homepage",
        "WebsiteFilter",
        "AllowedDomainsForApps",
        "HttpAllowlist",
        "LocalFileLinks",
        "Handlers",
        "AutoLaunchProtocolsFromOrigins",
        "GoToIntranetSiteForSingleWordEntryInAddressBar",
        "Bookmarks",
        "ManagedBookmarks",
        "NoDefaultBookmarks",
    }
)


def _common_url_flags() -> dict[str, object]:
    """Return navigation values supported by each active Firefox channel."""

    return {
        "Homepage": {
            "URL": "https://portal.example.test/",
            "Additional": ["https://help.example.test/"],
            "StartPage": "homepage",
            "Locked": True,
        },
        "WebsiteFilter": {
            "Block": ["https://blocked.example.test/*"],
            "Exceptions": ["https://allowed.example.test/*"],
        },
        "AllowedDomainsForApps": "portal.example.test,docs.example.test",
        "LocalFileLinks": ["https://files.example.test/"],
        "Handlers": {
            "schemes": {
                "mailto": {
                    "action": "useHelperApp",
                    "ask": False,
                    "handlers": [
                        {
                            "name": "M8 mail",
                            "uriTemplate": "https://mail.example.test/compose?to=%s",
                        }
                    ],
                }
            }
        },
        "Bookmarks": [
            {
                "Title": "M8 bookmark",
                "URL": "https://bookmark.example.test/",
                "Placement": "toolbar",
            }
        ],
        "ManagedBookmarks": [
            {
                "toplevel_name": "M8 managed",
                "children": [{"name": "M8 link", "url": "https://managed.example.test/"}],
            }
        ],
        "NoDefaultBookmarks": True,
    }


def _embedded_json(response: Any, element_id: str) -> dict[str, Any]:
    element = BeautifulSoup(response.text, "html.parser").find(id=element_id)
    assert element is not None
    return json.loads(element.get_text())


def _step_policy_items(shell_catalog: dict[str, Any], schema_version: str) -> list[dict[str, Any]]:
    step = shell_catalog["channels"][schema_version]["steps"]["2"]
    return [
        item for bucket in ("recommended", "additional", "raw_fallback") for item in step[bucket]
    ]


def _conversion_apply_payload(preview: dict[str, Any]) -> dict[str, Any]:
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


@pytest.mark.parametrize("schema_version", SUPPORTED_SCHEMA_CHANNELS)
def test_url_owner_catalog_and_import_export_round_trip_every_active_schema(
    schema_version: str,
) -> None:
    """All typed URL families have one step-two catalog owner and survive exchange."""

    flags = _common_url_flags()
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M8 URLs matrix {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "flags": flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        created = created_response.json()

        # A normal saved-editor write must retain every URL atom exactly.
        saved_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "flags": deepcopy(flags),
                "expected_revision": created["revision"],
            },
        )
        assert saved_response.status_code == status.HTTP_200_OK, saved_response.text
        saved = saved_response.json()
        assert saved["flags"] == flags

        guided_response = client.get(f"/profiles/{created['id']}/edit?step=urls_sites_navigation")
        assert guided_response.status_code == status.HTTP_200_OK
        initial = _embedded_json(guided_response, "profiles-initial-profile")
        shell_catalog = _embedded_json(guided_response, "wizard-schema-shell-catalog")
        assert initial["schema_version"] == schema_version
        assert initial["flags"] == flags

        step_two_items = _step_policy_items(shell_catalog, schema_version)
        for policy_id in _URL_OWNER_POLICY_IDS:
            owners = [item for item in step_two_items if item["id"] == policy_id]
            owners_elsewhere = [
                item
                for step, buckets in shell_catalog["channels"][schema_version]["steps"].items()
                if step != "2"
                for bucket in ("recommended", "additional", "raw_fallback")
                for item in buckets[bucket]
                if item["id"] == policy_id
            ]
            # HttpAllowlist was introduced after ESR 115. Every other M8
            # policy is present in all four active channel schemas.
            if policy_id == "HttpAllowlist" and schema_version == "esr-115.39":
                assert owners == []
            else:
                assert len(owners) == 1
                assert owners[0]["section_id"] == "urls_sites_navigation"
                assert owners[0]["target"] == f"shell-policy:2:{policy_id}"
            assert owners_elsewhere == []

        soup = BeautifulSoup(guided_response.text, "html.parser")
        owner_selectors = {
            "Homepage": "#wizard-homepage-url",
            **{
                policy_id: f'[data-settings-target="policy:{policy_id}"]'
                for policy_id in _URL_OWNER_POLICY_IDS - {"Homepage"}
            },
        }
        for policy_id in _URL_OWNER_POLICY_IDS:
            holders = soup.select(owner_selectors[policy_id])
            assert len(holders) == 1
            assert holders[0].find_parent(
                "section", {"data-wizard-step-id": "urls_sites_navigation"}
            )

        reopened_response = client.get(f"/api/profiles/{created['id']}")
        exported_response = client.get(
            f"/api/export/profiles/{created['id']}/firefox/policies.json"
        )
        assert reopened_response.status_code == status.HTTP_200_OK, reopened_response.text
        assert reopened_response.json()["flags"] == flags
        assert exported_response.status_code == status.HTTP_200_OK, exported_response.text
        assert exported_response.json() == {"policies": flags}

        imported_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": f"M8 URLs re-import {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "document": exported_response.json(),
            },
        )
        assert imported_response.status_code == status.HTTP_201_CREATED, imported_response.text
        imported = imported_response.json()
        assert imported["flags"] == flags
        reexported_response = client.get(
            f"/api/export/profiles/{imported['id']}/firefox/policies.json"
        )
        assert reexported_response.status_code == status.HTTP_200_OK, reexported_response.text
        assert reexported_response.content == exported_response.content


@pytest.mark.parametrize(
    ("source_schema", "target_schema"),
    (
        ("release-153", "esr-153.0"),
        ("esr-153.0", "esr-140.13"),
        ("esr-140.13", "esr-115.39"),
        ("esr-115.39", "release-153"),
    ),
)
def test_url_navigation_conversion_cycle_preserves_common_navigation_atoms(
    source_schema: str,
    target_schema: str,
) -> None:
    """A conversion must retain URL policy spelling, order, and ownership data."""

    flags = _common_url_flags()
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M8 URLs conversion {source_schema} {target_schema} {uuid4().hex}",
                "schema_version": source_schema,
                "flags": flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        profile_id = created_response.json()["id"]

        preview_response = client.post(
            f"/api/profiles/{profile_id}/conversion-preview",
            json={"target_artifact_id": target_schema},
        )
        assert preview_response.status_code == status.HTTP_200_OK, preview_response.text
        preview = preview_response.json()
        assert preview["compatibility"]["applicable"] is True
        assert preview["target_validation"]["status"] == "valid"

        apply_response = client.post(
            f"/api/profiles/{profile_id}/conversion-apply",
            json=_conversion_apply_payload(preview),
        )
        assert apply_response.status_code == status.HTTP_200_OK, apply_response.text
        assert apply_response.json()["status"] == "applied"

        converted_response = client.get(f"/api/profiles/{profile_id}")
        assert converted_response.status_code == status.HTTP_200_OK, converted_response.text
        converted = converted_response.json()
        assert converted["schema_version"] == target_schema
        assert converted["flags"] == flags
