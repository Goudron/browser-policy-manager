from __future__ import annotations

from app.web import profile_navigation
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog


def test_profile_navigation_rejects_unsafe_return_and_focus_values():
    assert profile_navigation.resolve_safe_profiles_return_url(None) is None
    assert profile_navigation.resolve_safe_profiles_return_url("//profiles/8/edit") is None
    assert (
        profile_navigation.resolve_safe_profiles_return_url(
            "/profiles?return=https://evil.test"
        )
        is None
    )
    assert (
        profile_navigation.resolve_safe_profiles_return_url("/profiles/8/edit")
        == "/profiles/8/edit"
    )

    assert profile_navigation.resolve_focus_target("   ") is None
    assert profile_navigation.resolve_focus_target("x" * 161) is None
    assert (
        profile_navigation.resolve_focus_target("  policy:DisableTelemetry  ")
        == "policy:DisableTelemetry"
    )


def test_profile_navigation_maps_settings_and_json_focus_targets():
    assert (
        profile_navigation.resolve_json_focus_target_from_settings_focus(
            "settings-schema-shell-step-8"
        )
        == "raw"
    )
    assert (
        profile_navigation.resolve_json_focus_target_from_settings_focus(
            "policy:DisableTelemetry"
        )
        == "policy:DisableTelemetry"
    )
    assert profile_navigation.resolve_json_focus_target_from_settings_focus("   ") is None
    assert (
        profile_navigation.resolve_json_focus_target_from_settings_focus("custom-target")
        is None
    )

    assert (
        profile_navigation.resolve_settings_focus_target_from_json_focus("raw")
        == "settings-schema-shell-step-8"
    )
    assert (
        profile_navigation.resolve_settings_focus_target_from_json_focus(
            "deprecated:LegacyPolicy"
        )
        == "settings-schema-shell-step-8"
    )
    assert (
        profile_navigation.resolve_settings_focus_target_from_json_focus(
            "policy:DisableTelemetry"
        )
        == "policy:DisableTelemetry"
    )
    assert (
        profile_navigation.resolve_settings_focus_target_from_json_focus("custom-target")
        == "custom-target"
    )


def test_profile_navigation_resolves_settings_shell_focus_step():
    shell_catalog = get_wizard_schema_shell_catalog(
        get_wizard_preferences_catalog(get_wizard_settings_catalog())
    )

    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:DisableTelemetry",
            "release-152",
            shell_catalog,
        )
        == 5
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:LocalNetworkAccess",
            "release-152",
            shell_catalog,
        )
        == 5
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "deprecated:LegacyPolicy",
            "release-152",
            shell_catalog,
        )
        == 8
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "shell-policy:8:DisableProfileRefresh",
            "release-152",
            shell_catalog,
        )
        == 8
    )


def test_profile_navigation_rejects_invalid_settings_shell_focus_step_inputs():
    shell_catalog = get_wizard_schema_shell_catalog(
        get_wizard_preferences_catalog(get_wizard_settings_catalog())
    )

    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "shell-policy:not-a-step:DisableTelemetry",
            "release-152",
            shell_catalog,
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "shell-policy:8",
            "release-152",
            shell_catalog,
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:   ",
            "release-152",
            shell_catalog,
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:DefinitelyNotInTheCatalog",
            "release-152",
            shell_catalog,
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-152",
            {
                "channels": {
                    "release-152": {
                        "steps": {
                            "not-a-step": {
                                "recommended": [{"id": "MatchedPolicy"}],
                            }
                        }
                    }
                }
            },
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-152",
            {"channels": []},
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-152",
            {"channels": {"release-152": []}},
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-152",
            {"channels": {"release-152": {"steps": []}}},
        )
        is None
    )
    assert (
        profile_navigation.resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-152",
            {
                "channels": {
                    "release-152": {
                        "steps": {
                            "5": ["not-a-dict"],
                        }
                    }
                }
            },
        )
        is None
    )


def test_profile_navigation_builds_route_hrefs_with_context():
    assert (
        profile_navigation.build_profile_json_href(
            8,
            focus_target="policy:DisableTelemetry",
        )
        == "/profiles/8/json?focus=policy:DisableTelemetry"
    )
    assert (
        profile_navigation.build_profile_json_href(
            8,
            return_url="/profiles/8/edit",
            focus_target="policy:DisableTelemetry",
        )
        == "/profiles/8/json?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    )
    assert (
        profile_navigation.build_profile_json_href(
            8,
            return_url="/profiles/8/edit?include_deleted=true",
            focus_target="deprecated:LegacyPolicy",
            include_deleted=True,
        )
        == "/profiles/8/json?include_deleted=true&return=/profiles/8/edit%3Finclude_deleted%3Dtrue&focus=deprecated:LegacyPolicy"
    )
    assert (
        profile_navigation.build_profile_settings_href(
            8,
            return_url="/profiles/8/edit",
            focus_target="policy:DisableTelemetry",
        )
        == "/profiles/8/settings?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    )
    assert (
        profile_navigation.build_profile_settings_href(
            8,
            return_url="/profiles/8/json?include_deleted=true",
            focus_target="settings-schema-shell-step-8",
            include_deleted=True,
        )
        == "/profiles/8/settings?include_deleted=true&return=/profiles/8/json%3Finclude_deleted%3Dtrue&focus=settings-schema-shell-step-8"
    )
    assert profile_navigation.build_profile_route_path(8, "settings") == (
        "/profiles/8/settings"
    )
    assert profile_navigation.build_profile_route_path(
        8,
        "settings",
        include_deleted=True,
    ) == "/profiles/8/settings?include_deleted=true"
