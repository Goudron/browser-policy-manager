from app.core.policy_validation import validate_profile_payload_with_schema
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.models.policy_schema import PolicyDefinition
from app.web import firefox_starter_presets as starter_module
from app.web.firefox_starter_presets import (
    _resolve_schema_enabled_value,
    build_wizard_starter_document,
    get_wizard_starter_catalog,
    get_wizard_starter_compliance_snapshot,
)


def test_wizard_starter_catalog_is_schema_aware():
    catalog = get_wizard_starter_catalog()

    assert {"blank", "keep_current", "basic_corporate", "classroom_kiosk", "soc_hard"} <= set(
        catalog["presets"]
    )
    assert "DisablePocket" in catalog["managed_policy_keys"]
    for schema_version in SUPPORTED_SCHEMA_CHANNELS:
        assert (
            catalog["presets"]["basic_corporate"]["policy_values"][schema_version]["DisablePocket"]
            is True
        )
        assert catalog["quick_policy_enabled_values"]["DisablePocket"][schema_version] is True
    assert "ExtensionSettings" in catalog["managed_policy_keys"]
    assert "WebsiteFilter" in catalog["managed_policy_keys"]
    assert "SanitizeOnShutdown" in catalog["managed_policy_keys"]
    assert catalog["compliance_layers"]["cis_l2"]["level"] == 2
    assert "Homepage" in catalog["managed_policy_keys"]


def test_wizard_starter_catalog_handles_missing_cis_benchmark_metadata(monkeypatch):
    monkeypatch.setattr(starter_module, "load_yaml_file", lambda path: {"benchmarks": []})

    catalog = get_wizard_starter_catalog()

    assert catalog["compliance_metadata"] == {}


def test_wizard_starter_catalog_exposes_cis_merged_variants():
    catalog = get_wizard_starter_catalog()
    for schema_version in SUPPORTED_SCHEMA_CHANNELS:
        merged = catalog["compliance_merged_presets"]["basic_corporate"]["cis_l2"][schema_version]
        policies = merged["policy_values"]

        assert policies["DisableTelemetry"] is True
        assert policies["DisableFirefoxAccounts"] is True
        assert policies["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
        assert (
            policies["Preferences"]["security.mixed_content.block_active_content"]["Value"] is True
        )
        assert policies["Preferences"]["media.peerconnection.enabled"]["Value"] is False
        assert merged["summary"]["added_from_cis"] > 0
        assert any(
            decision["review_required"] and decision["path"] == ["Proxy", "Mode"]
            for decision in merged["decisions"]
        )

        kiosk = catalog["compliance_merged_presets"]["classroom_kiosk"]["cis_l2"][schema_version]
        assert kiosk["policy_values"]["ExtensionSettings"]["uBlock0@raymondhill.net"] == {
            "installation_mode": "force_installed",
            "install_url": (
                "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
            ),
        }

        keep_current = catalog["compliance_merged_presets"]["keep_current"]["cis_l2"][
            schema_version
        ]
        assert keep_current["policy_values"] == {}


def test_cis_catalog_exposes_both_layers_for_every_supported_schema_channel():
    catalog = get_wizard_starter_catalog(include_compliance=False)
    for layer_key in ("cis_l1", "cis_l2"):
        layer = catalog["compliance_layers"][layer_key]
        assert set(layer["available_schema_versions"]) == set(SUPPORTED_SCHEMA_CHANNELS)
        assert layer["unavailable_reason_codes"] == {}
    snapshot = get_wizard_starter_compliance_snapshot("basic_corporate", "esr-115.38", "cis_l2")
    assert snapshot is not None
    assert snapshot["policy_values"]["DisableTelemetry"] is True
    assert snapshot["policy_values"]["DisableFirefoxAccounts"] is True
    assert snapshot["summary"]["added_from_cis"] > 0


def test_wizard_starter_presets_validate_for_all_supported_schema_channels():
    catalog = get_wizard_starter_catalog()

    for schema_version in SUPPORTED_SCHEMA_CHANNELS:
        for starter_key in catalog["presets"]:
            document = build_wizard_starter_document(starter_key, schema_version)
            validate_profile_payload_with_schema(
                {
                    "name": f"{starter_key}-{schema_version}",
                    "channel": schema_version,
                    "policies": document,
                }
            )

    office_esr = build_wizard_starter_document("basic_corporate", "esr-140.13")
    office_esr_153 = build_wizard_starter_document("basic_corporate", "esr-153.0")
    office_release = build_wizard_starter_document("basic_corporate", "release-153")
    soc_esr = build_wizard_starter_document("soc_hard", "esr-140.13")
    soc_esr_153 = build_wizard_starter_document("soc_hard", "esr-153.0")
    soc_release = build_wizard_starter_document("soc_hard", "release-153")

    assert office_esr["DisablePocket"] is True
    assert office_esr_153["DisablePocket"] is True
    assert office_release["DisablePocket"] is True
    assert soc_esr["DisablePocket"] is True
    assert soc_esr_153["DisablePocket"] is True
    assert soc_release["DisablePocket"] is True


def test_esr_115_starter_presets_apply_only_explicitly_reviewed_shapes():
    catalog = get_wizard_starter_catalog()

    for starter_key in catalog["presets"]:
        document = build_wizard_starter_document(starter_key, "esr-115.38")
        validate_profile_payload_with_schema(
            {
                "name": f"{starter_key}-esr-115.38",
                "channel": "esr-115.38",
                "policies": document,
            }
        )

    hardened = build_wizard_starter_document("soc_hard", "esr-115.38")
    assert "HttpsOnlyMode" not in hardened
    assert "FirefoxSuggest" not in hardened
    assert "Category" not in hardened["EnableTrackingProtection"]
    assert "ScreenShare" not in hardened["Permissions"]
    assert "Stories" not in hardened["FirefoxHome"]
    assert "FirefoxLabs" not in hardened["UserMessaging"]


def test_wizard_starter_presets_include_operational_baseline_controls():
    office = build_wizard_starter_document("basic_corporate", "release-153")
    kiosk = build_wizard_starter_document("classroom_kiosk", "release-153")
    soc = build_wizard_starter_document("soc_hard", "release-153")

    assert office["Certificates"]["ImportEnterpriseRoots"] is True
    assert office["DNSOverHTTPS"] == {"Enabled": False, "Locked": True}
    assert office["EnableTrackingProtection"]["Category"] == "strict"
    assert office["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert office["FirefoxHome"]["Locked"] is True
    assert office["FirefoxSuggest"]["WebSuggestions"] is False
    assert office["Homepage"]["Additional"] == [
        "https://helpdesk.example.local/",
        "https://kb.example.local/",
    ]
    assert office["PopupBlocking"]["Locked"] is True
    assert office["Proxy"]["Locked"] is True
    assert office["UserMessaging"]["SkipOnboarding"] is True

    assert kiosk["DisableDeveloperTools"] is True
    assert kiosk["BlockAboutAddons"] is True
    assert kiosk["BlockAboutSupport"] is True
    assert kiosk["InstallAddonsPermission"]["Default"] is False
    assert kiosk["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert kiosk["ExtensionSettings"]["uBlock0@raymondhill.net"] == {
        "installation_mode": "force_installed",
        "install_url": (
            "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
        ),
    }
    assert kiosk["Permissions"]["Camera"]["Allow"] == [
        "https://classroom.example.local",
        "https://lms.example.local",
    ]
    assert kiosk["Permissions"]["Autoplay"]["Default"] == "block-audio-video"
    assert kiosk["WebsiteFilter"]["Block"] == ["<all_urls>"]
    assert kiosk["Homepage"]["StartPage"] == "homepage-locked"

    assert soc["HttpsOnlyMode"] == "force_enabled"
    assert soc["Cookies"]["Behavior"] == "reject-tracker-and-partition-foreign"
    assert soc["DNSOverHTTPS"]["ProviderURL"] == "https://dns.example.secure/dns-query"
    assert soc["Permissions"]["Autoplay"]["Default"] == "block-audio-video"
    assert soc["Proxy"]["Locked"] is True
    assert soc["Proxy"]["Passthrough"] == "localhost, 127.0.0.1"
    assert soc["SanitizeOnShutdown"]["Locked"] is True
    assert soc["UserMessaging"]["FirefoxLabs"] is False


def test_resolve_schema_enabled_value_uses_definition_type(monkeypatch):
    definitions = {
        "Missing": None,
        "ObjectPolicy": PolicyDefinition(id="ObjectPolicy", type="object"),
        "ArrayPolicy": PolicyDefinition(id="ArrayPolicy", type="array"),
        "StringPolicy": PolicyDefinition(id="StringPolicy", type="string"),
        "NumberPolicy": PolicyDefinition(id="NumberPolicy", type="number"),
        "IntegerPolicy": PolicyDefinition(id="IntegerPolicy", type="integer"),
        "BooleanPolicy": PolicyDefinition(id="BooleanPolicy", type="boolean"),
    }
    monkeypatch.setattr(
        starter_module,
        "get_policy_definition",
        lambda schema_version, policy_id: definitions[policy_id],
    )

    assert _resolve_schema_enabled_value("Missing", "release-153") is True
    assert _resolve_schema_enabled_value("ObjectPolicy", "release-153") == {}
    assert _resolve_schema_enabled_value("ArrayPolicy", "release-153") == []
    assert _resolve_schema_enabled_value("StringPolicy", "release-153") == ""
    assert _resolve_schema_enabled_value("NumberPolicy", "release-153") == 1
    assert _resolve_schema_enabled_value("IntegerPolicy", "release-153") == 1
    assert _resolve_schema_enabled_value("BooleanPolicy", "release-153") is True
