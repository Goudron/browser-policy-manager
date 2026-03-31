from __future__ import annotations

import pytest

from app.core.policy_validation import (
    PolicyValidationError,
    PolicyValidationIssue,
    load_policy_schema_for_channel,
    validate_profile_payload_with_schema,
    validate_profile_policies_or_raise,
)


def _schema(channel: str = "release-149"):
    return load_policy_schema_for_channel(channel)


def _issues_for(
    policies: dict[str, object],
    *,
    channel: str = "release-149",
) -> list[PolicyValidationIssue]:
    with pytest.raises(PolicyValidationError) as excinfo:
        validate_profile_policies_or_raise(policies, _schema(channel))
    return excinfo.value.issues


def _issue_paths(issues: list[PolicyValidationIssue]) -> set[tuple[object, ...]]:
    return {tuple(issue.path) for issue in issues}


def test_release_schema_accepts_valid_profile_with_arrays_and_objects():
    policies = {
        "HttpAllowlist": ["http://example.org"],
        "DisableAppUpdate": True,
        "Extensions": {
            "Install": [
                "https://addons.mozilla.org/firefox/downloads/somefile.xpi",
            ],
            "Uninstall": ["bad_addon_id@mozilla.org"],
            "Locked": ["addon_id@mozilla.org"],
        },
    }

    validate_profile_policies_or_raise(policies, _schema())


def test_validate_profile_payload_helper_accepts_channel_and_policies():
    payload = {
        "channel": "release-149",
        "name": "Test profile",
        "policies": {
            "DisableAppUpdate": True,
            "HttpAllowlist": ["http://example.org"],
        },
    }

    validate_profile_payload_with_schema(payload)


def test_validate_profile_payload_helper_rejects_invalid_policies():
    payload = {
        "channel": "release-149",
        "name": "Test profile",
        "policies": {
            "Proxy": {
                "Mode": "bogus",
            },
        },
    }

    with pytest.raises(PolicyValidationError):
        validate_profile_payload_with_schema(payload)


def test_release_148_schema_includes_newer_mozilla_policies():
    schema = _schema("release-149")

    assert "BrowserDataBackup" in schema["properties"]
    assert "DisableRemoteImprovements" in schema["properties"]


def test_esr_140_schema_excludes_policies_added_after_esr_140():
    schema = _schema("esr-140.9")

    assert "BrowserDataBackup" not in schema.get("properties", {})
    assert "DisableRemoteImprovements" not in schema.get("properties", {})


def test_disable_pocket_is_boolean_in_current_snapshot():
    schema = _schema()

    assert schema["properties"]["DisablePocket"]["type"] == "boolean"


def test_requested_locales_rejects_invalid_top_level_type():
    issues = _issues_for({"RequestedLocales": 42})

    assert issues
    assert any(issue.policy == "RequestedLocales" for issue in issues)
    assert any("is not valid under any of the given schemas" in issue.message for issue in issues)


@pytest.mark.parametrize(
    "value",
    [
        "de,en-US",
        ["fr", "ru", "en-US"],
    ],
)
def test_requested_locales_accepts_supported_forms(value: object):
    validate_profile_policies_or_raise({"RequestedLocales": value}, _schema())


def test_http_allowlist_rejects_non_string_items():
    issues = _issues_for({"HttpAllowlist": [42]})

    assert issues
    assert any("is not of type 'string'" in issue.message for issue in issues)


def test_unknown_top_level_policy_is_reported():
    issues = _issues_for({"NoSuchPolicy": True})

    assert any("unexpected" in issue.message for issue in issues)


def test_extensions_rejects_unknown_nested_property():
    issues = _issues_for({"Extensions": {"Foo": []}})

    assert any(issue.path == ["Extensions", "Foo"] for issue in issues)


def test_proxy_mode_enum_is_enforced():
    issues = _issues_for({"Proxy": {"Mode": "bogus"}})

    assert any(issue.path == ["Proxy", "Mode"] for issue in issues)
    assert any("is not one of" in issue.message for issue in issues)


def test_bookmarks_rejects_invalid_item_shape():
    issues = _issues_for(
        {
            "Bookmarks": [
                {
                    "Title": "Docs",
                    "Placement": "sidebar",
                }
            ]
        }
    )

    assert any(issue.path == ["Bookmarks", 0, "Placement"] for issue in issues)


def test_bookmarks_require_title_and_url():
    issues = _issues_for({"Bookmarks": [{"Placement": "toolbar"}]})

    paths = _issue_paths(issues)
    assert ("Bookmarks", 0, "Title") in paths
    assert ("Bookmarks", 0, "URL") in paths


def test_preferences_value_type_is_controlled_by_declared_type():
    issues = _issues_for(
        {
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": "true",
                    "Status": "locked",
                    "Type": "boolean",
                }
            }
        }
    )

    assert any(
        issue.path == ["Preferences", "browser.tabs.warnOnClose", "Value"]
        for issue in issues
    )


def test_preferences_status_and_type_enums_are_enforced():
    issues = _issues_for(
        {
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": 1,
                    "Status": "bogus",
                    "Type": "integer",
                }
            }
        }
    )

    paths = _issue_paths(issues)
    assert ("Preferences", "browser.tabs.warnOnClose", "Status") in paths
    assert ("Preferences", "browser.tabs.warnOnClose", "Type") in paths


def test_search_engines_add_requires_name_and_url_template():
    issues = _issues_for(
        {
            "SearchEngines": {
                "Add": [
                    {
                        "Method": "GET",
                    }
                ]
            }
        }
    )

    paths = _issue_paths(issues)
    assert ("SearchEngines", "Add", 0, "Name") in paths
    assert ("SearchEngines", "Add", 0, "URLTemplate") in paths


def test_search_engines_url_template_must_include_search_terms():
    issues = _issues_for(
        {
            "SearchEngines": {
                "Add": [
                    {
                        "Name": "Example Search",
                        "URLTemplate": "https://www.example.org/search",
                    }
                ]
            }
        }
    )

    assert any(issue.path == ["SearchEngines", "Add", 0, "URLTemplate"] for issue in issues)


def test_cookies_allow_entries_must_include_scheme():
    issues = _issues_for({"Cookies": {"Allow": ["example.org"]}})

    assert any(issue.path == ["Cookies", "Allow", 0] for issue in issues)


def test_handlers_uri_template_must_be_https_with_substitution():
    issues = _issues_for(
        {
            "Handlers": {
                "schemes": {
                    "mailto": {
                        "action": "openElsewhere",
                        "handlers": [
                            {
                                "name": "Bad Handler",
                                "uriTemplate": "http://mail.example.com/",
                            }
                        ],
                    }
                }
            }
        }
    )

    paths = _issue_paths(issues)
    assert ("Handlers", "schemes", "mailto", "action") in paths
    assert ("Handlers", "schemes", "mailto", "handlers", 0, "uriTemplate") in paths


def test_content_analysis_numeric_enum_is_enforced():
    issues = _issues_for({"ContentAnalysis": {"DefaultResult": 3}})

    assert any(issue.path == ["ContentAnalysis", "DefaultResult"] for issue in issues)


@pytest.mark.parametrize(
    "value",
    [
        True,
        {
            "Cache": True,
            "Locked": True,
        },
    ],
)
def test_sanitize_on_shutdown_accepts_boolean_and_object_forms(value: object):
    validate_profile_policies_or_raise({"SanitizeOnShutdown": value}, _schema())


def test_extension_settings_property_table_enums_are_enforced():
    issues = _issues_for(
        {
            "ExtensionSettings": {
                "*": {
                    "installation_mode": "side_loaded",
                    "allowed_types": ["extension", "plugin"],
                    "default_area": "sidebar",
                }
            }
        }
    )

    paths = _issue_paths(issues)
    assert ("ExtensionSettings", "*", "installation_mode") in paths
    assert ("ExtensionSettings", "*", "allowed_types", 1) in paths
    assert ("ExtensionSettings", "*", "default_area") in paths


def test_enable_tracking_protection_does_not_require_convenience_exceptions():
    validate_profile_policies_or_raise(
        {
            "EnableTrackingProtection": {
                "Category": "strict",
                "Locked": True,
            }
        },
        _schema(),
    )
