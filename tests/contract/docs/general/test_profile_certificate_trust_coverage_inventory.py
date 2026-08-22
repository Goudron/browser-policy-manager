"""Executable scope guard for BPM096-M9-01 certificate/trust coverage."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.firefox_starter_catalog import STARTER_PRESETS
from app.core.schema_channels import SCHEMA_FILENAMES, SUPPORTED_SCHEMA_CHANNELS
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_wizard_shell.catalog import get_wizard_schema_shell_catalog
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
INVENTORY_PATH = (
    REPO_ROOT / "docs/architecture/profile-certificate-trust-coverage-inventory-0.9.6.md"
)
FIXTURE_MARKER = "<!-- bpm096-profile-certificate-trust-coverage-inventory-v1 -->"
GENERAL_TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_general.html"


def _inventory() -> dict[str, Any]:
    source = INVENTORY_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "certificate/trust coverage fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _schema(channel: str) -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "app/schemas/policies" / SCHEMA_FILENAMES[channel]).read_text(encoding="utf-8")
    )


def test_inventory_is_indexed_and_records_the_m9_01_boundary() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-certificate-trust-coverage-inventory-0.9.6.md", status="active"
        )
        == INVENTORY_PATH
    )
    inventory = _inventory()
    assert inventory["inventory_id"] == "bpm096-profile-certificate-trust-coverage"
    assert inventory["inventory_version"] == 1
    assert inventory["backlog_item"] == "BPM096-M9-01"
    assert inventory["guided_owner"] == {"step": 4, "id": "certificates-trust"}
    assert inventory["supported_schema_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M9-01 — Certificate and trust coverage inventoried" in backlog
    assert INVENTORY_PATH.name in backlog


def test_supported_certificate_paths_schema_difference_and_neighbour_boundaries() -> None:
    inventory = _inventory()
    coverage = inventory["policy_coverage"]
    assert set(coverage) == {
        "Certificates",
        "Authentication",
        "SecurityDevices",
        "WindowsSSO",
        "MicrosoftEntraSSO",
        "DisableSecurityBypass",
    }
    for policy_id in set(coverage) - {"MicrosoftEntraSSO"}:
        assert all(
            policy_id in _schema(channel)["properties"] for channel in SUPPORTED_SCHEMA_CHANNELS
        )
    assert coverage["MicrosoftEntraSSO"]["channels"] == [
        "release-153",
        "esr-153.0",
        "esr-140.13",
    ]
    assert "MicrosoftEntraSSO" not in _schema("esr-115.39")["properties"]
    for policy_id in {"Certificates", "Authentication", "WindowsSSO", "MicrosoftEntraSSO"}:
        assert coverage[policy_id]["disposition"] == "certificates-step-control"
        assert coverage[policy_id]["paths"]
    assert coverage["SecurityDevices"]["disposition"] == "certificates-step-raw-preserving-control"
    assert coverage["DisableSecurityBypass"] == {
        "disposition": "certificates-step-control",
        "delivery": "BPM096-M9-02",
        "paths": ["InvalidCertificate"],
        "excluded_paths": ["SafeBrowsing"],
    }

    fields = inventory["schema_fields"]
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        schema = _schema(channel)["properties"]
        for policy_id, expected_fields in fields["all_channels"].items():
            assert list(schema[policy_id].get("properties", {})) == expected_fields
        assert list(schema["DisableSecurityBypass"]["properties"]) == [
            "InvalidCertificate",
            "SafeBrowsing",
        ]
    assert fields["153_only"] == {"MicrosoftEntraSSO": []}

    shell_channels = get_wizard_schema_shell_catalog()["channels"]
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        expected = [
            policy_id
            for policy_id in (
                "Certificates",
                "DisableSecurityBypass",
                "WindowsSSO",
                "MicrosoftEntraSSO",
            )
            if policy_id in _schema(channel)["properties"]
        ]
        assert shell_channels[channel]["certificate_trust_posture"]["policy_ids"] == expected

    privacy = next(
        section
        for section in get_wizard_settings_catalog()["sections"]
        if section["id"] == "privacy"
    )
    assert "security.enterprise_roots.enabled" in {
        item["pref"] for item in privacy["preferences"]["known_preferences"]
    }
    assert inventory["preference_coverage"] == {
        "privacy:security.enterprise_roots.enabled": {
            "disposition": "certificates-step-control",
            "delivery": "BPM096-M9-02",
            "paths": ["<boolean>"],
            "relationship": "distinct-from-Certificates.ImportEnterpriseRoots; do not merge or duplicate",
        },
        "unregistered-client-certificate-selection": {
            "disposition": "all-settings-only",
            "reason": "no supported Firefox policy or registered Guided preference exposes client-certificate selection",
        },
    }


def test_preset_cis_raw_and_legacy_rehome_dispositions_are_explicit() -> None:
    inventory = _inventory()
    expected_presets = {
        "blank": [],
        "keep_current": [],
        "basic_corporate": ["Certificates.ImportEnterpriseRoots=true"],
        "classroom_kiosk": [],
        "soc_hard": ["Certificates.ImportEnterpriseRoots=true"],
    }
    assert inventory["starter_presets"] == expected_presets
    for preset_id, expected in expected_presets.items():
        actual = [
            "Certificates.ImportEnterpriseRoots=true"
            for values in STARTER_PRESETS[preset_id]["policy_values"].values()
            if values.get("Certificates", {}).get("ImportEnterpriseRoots") is True
        ]
        assert actual == expected

    assert inventory["cis"] == {
        "all_layers_all_channels": ["Authentication.NTLM=[]"],
        "unconstrained": [
            "Certificates",
            "SecurityDevices",
            "WindowsSSO",
            "MicrosoftEntraSSO",
            "DisableSecurityBypass",
        ],
        "rule": "M9 displays attribution and conflicts without changing benchmark provenance",
    }
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        for layer in ("cis_l1", "cis_l2"):
            policies = json.loads(
                (
                    REPO_ROOT / "app/compliance/firefox/cis/generated" / f"{layer}.{channel}.json"
                ).read_text(encoding="utf-8")
            )["policies"]
            assert policies["Authentication"] == {"NTLM": []}
            assert not (set(inventory["cis"]["unconstrained"]) & set(policies))

    assert inventory["raw_fallback"] == {
        "typed_certificate_or_authentication_value": {
            "owner": "certificates-trust",
            "step": 4,
            "rule": "preserve exact imported schema value and expose a raw fallback when it cannot be safely structured",
        },
        "security_devices": {
            "owner": "certificates-trust",
            "step": 4,
            "rule": "preserve Add and Delete shapes, device names, and platform paths without reading certificate or module contents",
        },
        "unknown_policy_or_unregistered_preference": {
            "owner": "all-settings-only",
            "rule": "preserve without inferred certificate, trust, host, or path ownership; report from Review only",
        },
    }
    source = GENERAL_TEMPLATE.read_text(encoding="utf-8")
    posture_source = (
        REPO_ROOT / "app" / "templates" / "profiles" / "_page_wizard_step_certificates.html"
    ).read_text(encoding="utf-8")
    dispositions = inventory["legacy_control_dispositions"]
    assert set(dispositions) == {
        "wizard-step-2-trust",
        "wizard-network-enterprise-presets",
        "wizard-windows-sso-card",
        "wizard-authentication-card",
        "wizard-certificates-card",
        "wizard-network-enterprise-fine-tuning-panel",
        "wizard-network-summary-authentication",
        "wizard-network-summary-certificates",
        "wizard-network-summary-windows-sso",
    }
    removed_in_m9_02 = {
        "wizard-step-2-trust",
        "wizard-network-enterprise-presets",
        "wizard-windows-sso-card",
        "wizard-authentication-card",
        "wizard-certificates-card",
        "wizard-network-enterprise-fine-tuning-panel",
    }
    removed_in_m9_04 = {
        "wizard-network-summary-authentication",
        "wizard-network-summary-certificates",
        "wizard-network-summary-windows-sso",
    }
    for control, disposition in dispositions.items():
        if control in removed_in_m9_02 | removed_in_m9_04:
            assert control not in source
            assert disposition["historical_outer_host_step"] == 1
        else:
            assert control in source
            assert disposition["current_outer_host_step"] == 1
        assert disposition["required_owner_step"] == 4
        assert disposition["disposition"]
    for control in (
        "wizard-certificate-system-trust",
        "wizard-certificate-enterprise-roots",
        "wizard-certificate-error-bypass",
        "wizard-certificate-windows-sso",
        "wizard-certificate-entra-sso",
        "wizard-step-4-attribution",
        "wizard-certificate-provenance-status",
        "wizard-certificate-cis-status",
    ):
        assert control in posture_source
