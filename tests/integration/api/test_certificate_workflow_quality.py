"""BPM096-M9-05 matrix for certificates and trust workflow quality."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from bs4 import BeautifulSoup
from fastapi import status

from app.core.profile_certificate_provenance import certificate_value_paths
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from tests.support import make_test_client

_SUPPORTED_ENTRA_SCHEMAS = frozenset(SUPPORTED_SCHEMA_CHANNELS) - {"esr-115.39"}
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CERTIFICATE_I18N_SOURCES = (
    _REPO_ROOT / "app/templates/profiles/_page_wizard_step_certificates.html",
    _REPO_ROOT / "app/static/profiles_certificate_trust.js",
    _REPO_ROOT / "app/static/profiles_review.js",
    _REPO_ROOT / "app/static/profiles_schema_shell_review.js",
)


def _certificate_flags() -> dict[str, object]:
    """Return every certificate/trust shape common to all active schemas."""

    return {
        "Certificates": {
            "Install": ["/etc/firefox/company-root.pem", "C:\\Corp\\client-chain.der"],
            "ImportEnterpriseRoots": True,
        },
        "Authentication": {
            "SPNEGO": ["intranet.example"],
            "Delegated": ["delegate.example"],
            "NTLM": ["ntlm.example"],
            "AllowNonFQDN": {"fileserver": True},
            "AllowProxies": {"proxy.example": True},
            "Locked": True,
            "PrivateBrowsing": False,
        },
        "SecurityDevices": {
            "Add": {"Corporate token": "/usr/lib/pkcs11/corporate.so"},
            "Delete": ["Legacy token"],
        },
        "DisableSecurityBypass": {"InvalidCertificate": False},
        "WindowsSSO": True,
        "Preferences": {
            "security.enterprise_roots.enabled": {
                "Status": "locked",
                "Type": "boolean",
                "Value": True,
            }
        },
    }


def _embedded_json(response: Any, element_id: str) -> dict[str, Any]:
    element = BeautifulSoup(response.text, "html.parser").find(id=element_id)
    assert element is not None
    payload = json.loads(element.get_text())
    assert isinstance(payload, dict)
    return payload


def _conversion_apply_payload(preview: dict[str, Any]) -> dict[str, object]:
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


def _duplicate_payload(source: dict[str, Any], *, target_schema_id: str) -> dict[str, object]:
    return {
        "name": f"M9 certificate duplicate {target_schema_id} {uuid4().hex}",
        "target_schema_id": target_schema_id,
        "starter_id": "keep_current",
        "cis_baseline_id": "none",
        "source_id": source["id"],
        "expected_source_revision": source["revision"],
        "preparation_idempotency_key": uuid4().hex,
    }


@pytest.mark.parametrize("schema_version", SUPPORTED_SCHEMA_CHANNELS)
def test_certificate_trust_owner_and_exchange_round_trip_every_active_schema(
    schema_version: str,
) -> None:
    """Every typed certificate atom has step-four ownership and exact exchange semantics."""

    flags = _certificate_flags()
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M9 certificate matrix {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "flags": flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        created = created_response.json()

        # Unchanged certificate values must not accept a client-side source
        # relabelling.  Generic CRUD creation truthfully records them as
        # imported, and the server ledger remains authoritative.
        saved_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "flags": deepcopy(flags),
                "expected_revision": created["revision"],
                "certificate_provenance": {
                    "contract_id": "bpm096-profile-certificate-provenance",
                    "contract_version": 1,
                    "paths": {
                        "/Certificates/Install/0": "imported",
                        "/Authentication/NTLM/0": "cis",
                        "/SecurityDevices/Add/Corporate token": "converted",
                    },
                },
            },
        )
        assert saved_response.status_code == status.HTTP_200_OK, saved_response.text
        saved = saved_response.json()
        assert saved["flags"] == flags
        assert set(saved["certificate_provenance"]["paths"]) == set(certificate_value_paths(flags))
        assert set(saved["certificate_provenance"]["paths"].values()) == {"imported"}

        guided_response = client.get(f"/profiles/{created['id']}/edit?step=certificates_trust")
        assert guided_response.status_code == status.HTTP_200_OK, guided_response.text
        initial = _embedded_json(guided_response, "profiles-initial-profile")
        shell_catalog = _embedded_json(guided_response, "wizard-schema-shell-catalog")
        assert initial["schema_version"] == schema_version
        assert initial["flags"] == flags

        soup = BeautifulSoup(guided_response.text, "html.parser")
        certificates_step = soup.select_one('section[data-wizard-step-id="certificates_trust"]')
        assert certificates_step is not None
        assert not certificates_step.select('input[type="file"]')
        for control_id in (
            "wizard-certificate-system-trust",
            "wizard-certificate-enterprise-roots",
            "wizard-certificate-error-bypass",
            "wizard-certificate-windows-sso",
            "wizard-certificate-install-reference",
            "wizard-certificate-authentication-field",
            "wizard-certificate-authentication-host",
            "wizard-certificate-authentication-locked",
            "wizard-certificate-authentication-private-browsing",
            "wizard-security-device-name",
            "wizard-security-device-path",
            "wizard-security-device-delete-name",
        ):
            control = soup.find(id=control_id)
            assert control is not None
            assert control.find_parent("section", {"data-wizard-step-id": "certificates_trust"})
            assert control.find_parent("label") is not None
        for status_id in (
            "wizard-certificate-trust-schema-status",
            "wizard-certificate-provenance-status",
            "wizard-certificate-cis-status",
        ):
            status_node = soup.find(id=status_id)
            assert status_node is not None
            assert status_node.get("role") == "status"
            assert status_node.get("aria-live") == "polite"
        assert not soup.select(
            '[data-wizard-step-id="browser_network_search"] '
            "#wizard-certificate-system-trust, "
            '[data-wizard-step-id="browser_network_search"] '
            "#wizard-certificate-enterprise-roots, "
            '[data-wizard-step-id="browser_network_search"] '
            "#wizard-certificate-windows-sso"
        )
        # Step 8 includes a technical shell.  The certificate owner must be
        # absent from every generic shell bucket so that it cannot become a
        # second editor now or in a future template rearrangement.
        shell_policy_ids = {
            item["id"]
            for channel in shell_catalog["channels"].values()
            for step in channel["steps"].values()
            for bucket in ("recommended", "additional", "raw_fallback")
            for item in step[bucket]
        }
        for policy_id in (
            "Certificates",
            "Authentication",
            "SecurityDevices",
            "DisableSecurityBypass",
            "WindowsSSO",
            "MicrosoftEntraSSO",
        ):
            assert policy_id not in shell_policy_ids
            assert not soup.select(
                f'[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                f'[data-schema-policy-id="{policy_id}"]'
            )

        reopened_response = client.get(f"/api/profiles/{created['id']}")
        exported_response = client.get(
            f"/api/export/profiles/{created['id']}/firefox/policies.json"
        )
        assert reopened_response.status_code == status.HTTP_200_OK, reopened_response.text
        assert reopened_response.json()["flags"] == flags
        assert reopened_response.json()["certificate_provenance"] == saved["certificate_provenance"]
        assert exported_response.status_code == status.HTTP_200_OK, exported_response.text
        assert exported_response.json() == {"policies": flags}
        assert "certificate_provenance" not in exported_response.text

        imported_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": f"M9 certificate re-import {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "document": exported_response.json(),
            },
        )
        assert imported_response.status_code == status.HTTP_201_CREATED, imported_response.text
        imported = imported_response.json()
        assert imported["flags"] == flags
        assert set(imported["certificate_provenance"]["paths"]) == set(
            certificate_value_paths(flags)
        )
        assert set(imported["certificate_provenance"]["paths"].values()) == {"imported"}
        reexported_response = client.get(
            f"/api/export/profiles/{imported['id']}/firefox/policies.json"
        )
        assert reexported_response.status_code == status.HTTP_200_OK, reexported_response.text
        assert reexported_response.content == exported_response.content


@pytest.mark.parametrize("schema_version", SUPPORTED_SCHEMA_CHANNELS)
def test_prepared_cis_certificate_sources_remain_truthful_in_every_active_schema(
    schema_version: str,
) -> None:
    """Starter and CIS sources stay separate from a client-submitted certificate ledger."""

    with make_test_client() as client:
        response = client.post(
            "/api/profiles/prepare/new",
            json={
                "name": f"M9 certificate CIS {schema_version} {uuid4().hex}",
                "target_schema_id": schema_version,
                "starter_id": "basic_corporate",
                "cis_baseline_id": "cis_l1",
                "preparation_idempotency_key": uuid4().hex,
            },
        )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    profile = response.json()
    assert profile["flags"]["Certificates"]["ImportEnterpriseRoots"] is True
    assert profile["flags"]["Authentication"]["NTLM"] == []
    assert profile["certificate_provenance"]["paths"] == {
        "/Authentication/NTLM": "cis",
        "/Certificates/ImportEnterpriseRoots": "baseline",
    }
    assert profile["baseline_provenance"]["cis"]["baseline_id"] == "cis_l1"


@pytest.mark.parametrize(
    ("source_schema", "target_schema"),
    (
        ("release-153", "esr-153.0"),
        ("esr-153.0", "esr-140.13"),
        ("esr-140.13", "esr-115.39"),
        ("esr-115.39", "release-153"),
    ),
)
def test_common_certificate_document_converts_without_provenance_or_policy_loss(
    source_schema: str, target_schema: str
) -> None:
    """Every common trust shape survives a real cross-schema conversion cycle."""

    flags = _certificate_flags()
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M9 certificate conversion {source_schema} {target_schema} {uuid4().hex}",
                "schema_version": source_schema,
                "flags": flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        before = created_response.json()
        preview_response = client.post(
            f"/api/profiles/{before['id']}/conversion-preview",
            json={"target_artifact_id": target_schema},
        )
        assert preview_response.status_code == status.HTTP_200_OK, preview_response.text
        preview = preview_response.json()
        assert preview["compatibility"]["applicable"] is True
        assert preview["target_validation"]["status"] == "valid"
        applied_response = client.post(
            f"/api/profiles/{before['id']}/conversion-apply",
            json=_conversion_apply_payload(preview),
        )
        assert applied_response.status_code == status.HTTP_200_OK, applied_response.text
        after_response = client.get(f"/api/profiles/{before['id']}")

    assert after_response.status_code == status.HTTP_200_OK, after_response.text
    after = after_response.json()
    assert after["schema_version"] == target_schema
    assert after["flags"] == flags
    assert after["baseline_provenance"] == before["baseline_provenance"]
    assert set(after["certificate_provenance"]["paths"]) == set(certificate_value_paths(flags))
    assert set(after["certificate_provenance"]["paths"].values()) == {"converted"}


def test_common_certificate_document_duplicate_preserves_or_converts_its_ledger() -> None:
    """Duplicate keeps same-schema sources and marks cross-schema values converted."""

    flags = _certificate_flags()
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json={
                "name": f"M9 certificate duplicate source {uuid4().hex}",
                "schema_version": "release-153",
                "flags": flags,
            },
        )
        assert created_response.status_code == status.HTTP_201_CREATED, created_response.text
        source = created_response.json()
        same_response = client.post(
            "/api/profiles/prepare/duplicate",
            json=_duplicate_payload(source, target_schema_id="release-153"),
        )
        cross_response = client.post(
            "/api/profiles/prepare/duplicate",
            json=_duplicate_payload(source, target_schema_id="esr-115.39"),
        )
        reread_source_response = client.get(f"/api/profiles/{source['id']}")

    assert same_response.status_code == status.HTTP_201_CREATED, same_response.text
    assert cross_response.status_code == status.HTTP_201_CREATED, cross_response.text
    same = same_response.json()
    cross = cross_response.json()
    assert same["flags"] == cross["flags"] == flags
    assert same["schema_version"] == "release-153"
    assert cross["schema_version"] == "esr-115.39"
    assert set(same["certificate_provenance"]["paths"].values()) == {"imported"}
    assert set(cross["certificate_provenance"]["paths"].values()) == {"converted"}
    assert reread_source_response.status_code == status.HTTP_200_OK
    assert reread_source_response.json() == source


def test_every_certificate_i18n_key_is_available_in_source_and_generated_catalogs() -> None:
    """All dynamic and template certificate UI text resolves in six shipped locales."""

    keys = {
        key
        for path in _CERTIFICATE_I18N_SOURCES
        for key in re.findall(
            r"profiles\.wizard_certificates?_[a-z0-9_]+", path.read_text(encoding="utf-8")
        )
    }
    assert len(keys) >= 50
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        source_catalog = json.loads(
            (_REPO_ROOT / "app/i18n_src" / locale / "wizard.json").read_text(encoding="utf-8")
        )
        generated_catalog = json.loads(
            (_REPO_ROOT / "app/i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        for key in keys:
            assert isinstance(source_catalog.get(key), str) and source_catalog[key]
            assert generated_catalog.get(key) == source_catalog[key]


@pytest.mark.parametrize("schema_version", SUPPORTED_SCHEMA_CHANNELS)
def test_entra_sso_schema_boundary_is_exact_and_does_not_create_invalid_profiles(
    schema_version: str,
) -> None:
    """The 153-only certificate SSO shape is accepted only by its three schemas."""

    with make_test_client() as client:
        response = client.post(
            "/api/profiles",
            json={
                "name": f"M9 Entra boundary {schema_version} {uuid4().hex}",
                "schema_version": schema_version,
                "flags": {"MicrosoftEntraSSO": True},
            },
        )
        profiles = client.get("/api/profiles")

    if schema_version in _SUPPORTED_ENTRA_SCHEMAS:
        assert response.status_code == status.HTTP_201_CREATED, response.text
        assert response.json()["flags"] == {"MicrosoftEntraSSO": True}
        assert response.json()["certificate_provenance"]["paths"] == {
            "/MicrosoftEntraSSO": "manual"
        }
        assert any(profile["id"] == response.json()["id"] for profile in profiles.json())
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert all("M9 Entra boundary" not in profile["name"] for profile in profiles.json())
